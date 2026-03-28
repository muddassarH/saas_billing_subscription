from django.urls import include, path
from rest_framework.routers import DefaultRouter

from billing import webhook_views
from billing.views import (
    AdminOrganizationViewSet,
    AdminPlanViewSet,
    AdminUserListView,
    BillingPortalView,
    CreateCheckoutSessionView,
    InvoiceListView,
    LimitedPingView,
    MeView,
    PlanListView,
    SubscriptionDetailView,
    UsageIncrementView,
    UsagePeriodListView,
    UsageSummaryView,
)

router = DefaultRouter()
router.register("admin/plans", AdminPlanViewSet, basename="admin-plans")
router.register("admin/organizations", AdminOrganizationViewSet, basename="admin-orgs")

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plans-list"),
    path("create-checkout-session/", CreateCheckoutSessionView.as_view(), name="checkout"),
    path("billing-portal/", BillingPortalView.as_view(), name="billing-portal"),
    path("me/", MeView.as_view(), name="me"),
    path("usage/", UsageSummaryView.as_view(), name="usage-summary"),
    path("usage/increment/", UsageIncrementView.as_view(), name="usage-increment"),
    path("usage/periods/", UsagePeriodListView.as_view(), name="usage-periods"),
    path("subscription/", SubscriptionDetailView.as_view(), name="subscription"),
    path("invoices/", InvoiceListView.as_view(), name="invoices"),
    path("limited/ping/", LimitedPingView.as_view(), name="limited-ping"),
    path("webhook/stripe/", webhook_views.stripe_webhook, name="stripe-webhook"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("", include(router.urls)),
]
