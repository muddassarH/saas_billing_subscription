from django.contrib.auth import get_user_model
from rest_framework import serializers

from billing.models import InvoiceRecord, Organization, Plan, Subscription, UsagePeriod

User = get_user_model()


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price_monthly_cents",
            "price_yearly_cents",
            "stripe_price_id_monthly",
            "stripe_price_id_yearly",
            "features",
            "is_active",
            "sort_order",
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "plan",
            "stripe_subscription_id",
            "status",
            "current_period_end",
            "cancel_at_period_end",
            "created_at",
        )


class UsagePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsagePeriod
        fields = ("usage_type", "period_start", "total", "updated_at")


class CheckoutSessionSerializer(serializers.Serializer):
    plan_slug = serializers.SlugField()
    billing_interval = serializers.ChoiceField(choices=("month", "year"), default="month")


class BillingPortalSerializer(serializers.Serializer):
    pass


class UsageIncrementSerializer(serializers.Serializer):
    usage_type = serializers.CharField(max_length=64, default="api_calls")
    quantity = serializers.IntegerField(min_value=1, default=1)


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceRecord
        fields = (
            "stripe_invoice_id",
            "amount_paid_cents",
            "currency",
            "status",
            "hosted_invoice_url",
            "invoice_pdf",
            "period_end",
            "created_at",
        )


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "stripe_customer_id", "created_at")


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role", "stripe_customer_id", "is_active", "date_joined")
