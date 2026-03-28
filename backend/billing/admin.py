from django.contrib import admin

from billing.models import (
    InvoiceRecord,
    Organization,
    OrganizationMember,
    Plan,
    Subscription,
    UsageLog,
    UsagePeriod,
    WebhookEvent,
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order", "price_monthly_cents")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "stripe_subscription_id", "current_period_end")
    list_filter = ("status",)
    search_fields = ("stripe_subscription_id", "user__email")


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ("user", "usage_type", "quantity", "created_at")
    list_filter = ("usage_type",)


@admin.register(UsagePeriod)
class UsagePeriodAdmin(admin.ModelAdmin):
    list_display = ("user", "usage_type", "period_start", "total")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("stripe_event_id", "event_type", "processed_at", "created_at")
    readonly_fields = ("stripe_event_id", "event_type", "payload_summary")


@admin.register(InvoiceRecord)
class InvoiceRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "stripe_invoice_id", "amount_paid_cents", "status", "created_at")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ("name", "slug")


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "role")
