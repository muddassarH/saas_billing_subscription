from __future__ import annotations

import logging
import time
from typing import Any

import requests
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


def configure() -> None:
    stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_customer(user) -> str:
    configure()
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.pk)},
    )
    user.stripe_customer_id = customer.id
    user.save(update_fields=["stripe_customer_id"])
    return customer.id


def create_checkout_session(
    *,
    user,
    price_id: str,
    success_url: str,
    cancel_url: str,
    mode: str = "subscription",
    allow_promotion_codes: bool = True,
    client_reference_id: str | None = None,
    subscription_data: dict[str, Any] | None = None,
) -> stripe.checkout.Session:
    configure()
    customer_id = get_or_create_customer(user)
    params: dict[str, Any] = {
        "customer": customer_id,
        "mode": mode,
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "allow_promotion_codes": allow_promotion_codes,
        "client_reference_id": client_reference_id or str(user.pk),
    }
    if subscription_data:
        params["subscription_data"] = subscription_data
    return stripe.checkout.Session.create(**params)


def create_billing_portal_session(*, user, return_url: str) -> stripe.billing_portal.Session:
    configure()
    if not user.stripe_customer_id:
        get_or_create_customer(user)
    return stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=return_url,
    )


def report_usage_for_user(user, usage_type: str, quantity: int) -> None:
    """Report metered usage to Stripe (legacy usage records API; Stripe SDK v15 omits helpers)."""
    from billing.models import Subscription, SubscriptionStatus

    configure()
    sub = (
        Subscription.objects.select_related("plan")
        .filter(
            user=user,
            status__in=(SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING),
        )
        .first()
    )
    if not sub or not sub.stripe_metered_subscription_item_id:
        return
    si = sub.stripe_metered_subscription_item_id
    url = f"https://api.stripe.com/v1/subscription_items/{si}/usage_records"
    try:
        r = requests.post(
            url,
            auth=(settings.STRIPE_SECRET_KEY, ""),
            data={
                "quantity": quantity,
                "action": "increment",
                "timestamp": int(time.time()),
            },
            timeout=30,
        )
        if r.status_code >= 400:
            logger.warning("Stripe usage report failed: %s %s", r.status_code, r.text[:500])
    except requests.RequestException as e:
        logger.warning("Stripe usage report request failed: %s", e)
