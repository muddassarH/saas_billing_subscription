from __future__ import annotations

import logging
from datetime import datetime, timezone

import stripe
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone as dj_timezone

from billing.models import (
    InvoiceRecord,
    Plan,
    Subscription,
    SubscriptionStatus,
    WebhookEvent,
)
from billing.services import stripe_service

logger = logging.getLogger(__name__)
User = get_user_model()


def _dt_from_ts(ts: int | None):
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _plan_for_price(price_id: str) -> Plan | None:
    if not price_id:
        return None
    return (
        Plan.objects.filter(stripe_price_id_monthly=price_id).first()
        or Plan.objects.filter(stripe_price_id_yearly=price_id).first()
    )


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def process_stripe_event(self, event_id: str):
    """Process a Stripe webhook event by id (payload loaded from Stripe if needed)."""
    row = WebhookEvent.objects.filter(stripe_event_id=event_id).first()
    if row and row.processed_at:
        return

    stripe_service.configure()
    try:
        event = stripe.Event.retrieve(event_id)
    except stripe.StripeError as exc:
        logger.exception("Failed to retrieve event %s", event_id)
        raise self.retry(exc=exc)

    etype = event["type"]
    data = event["data"]["object"]

    try:
        if etype == "checkout.session.completed":
            _handle_checkout_completed(data)
        elif etype == "invoice.payment_succeeded":
            _handle_invoice_payment_succeeded(data)
        elif etype == "invoice.payment_failed":
            _handle_invoice_payment_failed(data)
        elif etype == "customer.subscription.updated":
            _handle_subscription_updated(data)
        elif etype == "customer.subscription.deleted":
            _handle_subscription_deleted(data)
        else:
            logger.info("Unhandled Stripe event type: %s", etype)

        WebhookEvent.objects.filter(stripe_event_id=event_id).update(
            processed_at=dj_timezone.now(),
            processing_error="",
        )
    except Exception as exc:
        WebhookEvent.objects.filter(stripe_event_id=event_id).update(
            processing_error=str(exc)[:2000],
        )
        logger.exception("Webhook processing failed for %s", event_id)
        raise


def _handle_checkout_completed(session: dict):
    user_id = session.get("client_reference_id")
    if not user_id:
        meta = session.get("metadata") or {}
        user_id = meta.get("user_id")
    if not user_id:
        logger.warning("checkout.session.completed without user reference")
        return
    try:
        user = User.objects.get(pk=int(user_id))
    except (User.DoesNotExist, ValueError, TypeError):
        logger.warning("User not found for checkout session: %s", user_id)
        return

    sub_id = session.get("subscription")
    if not sub_id:
        return

    stripe_sub = stripe.Subscription.retrieve(sub_id, expand=["items.data.price"])
    _upsert_subscription_from_stripe(user, stripe_sub)


def _upsert_subscription_from_stripe(user, stripe_sub: stripe.Subscription):
    price_id = None
    items = getattr(stripe_sub, "items", None)
    if items and items.data:
        first = items.data[0]
        price_id = first.price.id if getattr(first, "price", None) else None
    plan = _plan_for_price(price_id) if price_id else None
    if not plan:
        plan = Plan.objects.filter(slug="pro", is_active=True).first() or Plan.objects.filter(
            is_active=True
        ).first()

    metered_item_id = ""
    if items and items.data:
        for it in items.data:
            pid = it.price.id if getattr(it, "price", None) else None
            p = Plan.objects.filter(stripe_metered_price_id=pid).first() if pid else None
            if p:
                metered_item_id = it.id
                break

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.UNPAID,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        "paused": SubscriptionStatus.PAUSED,
    }
    status = status_map.get(stripe_sub.status, SubscriptionStatus.INCOMPLETE)

    with transaction.atomic():
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "plan": plan,
                "stripe_subscription_id": stripe_sub.id,
                "status": status,
                "current_period_end": _dt_from_ts(stripe_sub.current_period_end),
                "cancel_at_period_end": bool(stripe_sub.cancel_at_period_end),
                "stripe_metered_subscription_item_id": metered_item_id,
            },
        )


def _handle_invoice_payment_succeeded(invoice: dict):
    customer_id = invoice.get("customer")
    user = User.objects.filter(stripe_customer_id=customer_id).first()
    if not user:
        return
    InvoiceRecord.objects.update_or_create(
        stripe_invoice_id=invoice["id"],
        defaults={
            "user": user,
            "amount_paid_cents": invoice.get("amount_paid") or 0,
            "currency": invoice.get("currency") or "usd",
            "status": invoice.get("status") or "",
            "hosted_invoice_url": invoice.get("hosted_invoice_url") or "",
            "invoice_pdf": invoice.get("invoice_pdf") or "",
            "period_end": _dt_from_ts(invoice.get("period_end")),
        },
    )


def _handle_invoice_payment_failed(invoice: dict):
    customer_id = invoice.get("customer")
    user = User.objects.filter(stripe_customer_id=customer_id).first()
    if not user:
        return
    send_billing_notification.delay(
        user.id,
        "payment_failed",
        {"invoice_id": invoice.get("id"), "amount_due": invoice.get("amount_due")},
    )


def _handle_subscription_updated(stripe_sub: dict):
    sub_id = stripe_sub.get("id")
    internal = Subscription.objects.filter(stripe_subscription_id=sub_id).select_related("user").first()
    if not internal:
        customer_id = stripe_sub.get("customer")
        user = User.objects.filter(stripe_customer_id=customer_id).first()
        if not user:
            return
        full = stripe.Subscription.retrieve(sub_id, expand=["items.data.price"])
        _upsert_subscription_from_stripe(user, full)
        return

    full = stripe.Subscription.retrieve(sub_id, expand=["items.data.price"])
    _upsert_subscription_from_stripe(internal.user, full)


def _handle_subscription_deleted(stripe_sub: dict):
    sub_id = stripe_sub.get("id")
    Subscription.objects.filter(stripe_subscription_id=sub_id).update(
        status=SubscriptionStatus.CANCELED,
        cancel_at_period_end=False,
    )


@shared_task
def aggregate_usage_periods():
    """Placeholder for heavy aggregation from UsageLog into UsagePeriod (already incremental)."""
    return True


@shared_task
def send_billing_notification(user_id: int, kind: str, context: dict):
    """Email notifications — uses Django email backend (console in dev)."""
    from django.core.mail import send_mail

    user = User.objects.filter(pk=user_id).first()
    if not user:
        return
    subject_map = {
        "payment_failed": "Payment failed — update your billing method",
    }
    subject = subject_map.get(kind, "Billing notification")
    body = f"Hello,\n\nBilling event: {kind}\nContext: {context}\n"
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else "billing@example.com", [user.email], fail_silently=True)
