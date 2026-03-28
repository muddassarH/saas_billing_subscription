from django.conf import settings
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    """Subscription catalog (Free, Pro, Enterprise)."""

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price_monthly_cents = models.PositiveIntegerField(default=0)
    price_yearly_cents = models.PositiveIntegerField(default=0)
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True, default="")
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True, default="")
    # Metered overage (optional) — Stripe metered price for usage billing
    stripe_metered_price_id = models.CharField(max_length=255, blank=True, default="")
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.name


class SubscriptionStatus(models.TextChoices):
    INCOMPLETE = "incomplete", "Incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired", "Incomplete expired"
    TRIALING = "trialing", "Trialing"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELED = "canceled", "Canceled"
    UNPAID = "unpaid", "Unpaid"
    PAUSED = "paused", "Paused"


class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=32,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.INCOMPLETE,
        db_index=True,
    )
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    stripe_metered_subscription_item_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.plan.slug}"


class UsageLog(models.Model):
    """Append-only usage events for audit and aggregation."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_logs")
    usage_type = models.CharField(max_length=64, db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "usage_type", "created_at"]),
        ]


class UsagePeriod(models.Model):
    """Rolled-up usage per user / type / billing month (YYYY-MM-01)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_periods")
    usage_type = models.CharField(max_length=64)
    period_start = models.DateField(db_index=True)
    total = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "usage_type", "period_start")
        indexes = [
            models.Index(fields=["user", "period_start"]),
        ]


class WebhookEvent(models.Model):
    """Stripe event idempotency: one row per delivered event."""

    stripe_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=128)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)
    payload_summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class InvoiceRecord(models.Model):
    """Cached Stripe invoices for history UI."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices")
    stripe_invoice_id = models.CharField(max_length=255, unique=True)
    amount_paid_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="usd")
    status = models.CharField(max_length=32, blank=True)
    hosted_invoice_url = models.URLField(max_length=2048, blank=True)
    invoice_pdf = models.URLField(max_length=2048, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class Organization(models.Model):
    """Optional multi-tenant grouping (bonus)."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    class OrgRole(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MEMBER = "MEMBER", "Member"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="org_memberships")
    role = models.CharField(max_length=16, choices=OrgRole.choices, default=OrgRole.MEMBER)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("organization", "user")
