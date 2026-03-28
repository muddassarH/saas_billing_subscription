from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import stripe

from accounts.serializers import MeSerializer
from billing.models import InvoiceRecord, Organization, Plan, Subscription
from billing.permissions import IsAdminRole
from billing.serializers import (
    AdminUserSerializer,
    CheckoutSessionSerializer,
    InvoiceSerializer,
    OrganizationSerializer,
    PlanSerializer,
    SubscriptionSerializer,
    UsageIncrementSerializer,
    UsagePeriodSerializer,
)
from billing.services import stripe_service
from billing.services.feature_access import FeatureAccessService
from billing.services.usage import UsageLimitExceeded, UsageService
from django.conf import settings

User = get_user_model()


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = (AllowAny,)


class CreateCheckoutSessionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        ser = CheckoutSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        plan = Plan.objects.filter(slug=ser.validated_data["plan_slug"], is_active=True).first()
        if not plan:
            return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)
        interval = ser.validated_data["billing_interval"]
        price_id = (
            plan.stripe_price_id_monthly if interval == "month" else plan.stripe_price_id_yearly
        )
        if not price_id:
            return Response(
                {"detail": "Plan has no Stripe price configured for this interval."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not price_id.startswith("price_"):
            return Response(
                {"detail": "Plan Stripe price is invalid. Expected a Stripe price ID starting with 'price_'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        success_url = f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.FRONTEND_URL}/pricing"
        try:
            session = stripe_service.create_checkout_session(
                user=request.user,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(request.user.pk),
            )
        except stripe.StripeError as exc:
            return Response(
                {"detail": str(exc.user_message or str(exc))},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"checkout_url": session.url, "session_id": session.id})


class BillingPortalView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        return_url = f"{settings.FRONTEND_URL}/billing"
        portal = stripe_service.create_billing_portal_session(user=request.user, return_url=return_url)
        return Response({"url": portal.url})


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class UsageSummaryView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        feats = FeatureAccessService.plan_features(request.user)
        period_start = UsageService.current_period_start()
        api_calls = UsageService.get_period_total(request.user, "api_calls", period_start)
        credits = UsageService.get_period_total(request.user, "credits", period_start)
        return Response(
            {
                "period_start": period_start.isoformat(),
                "limits": {
                    "api_calls_per_month": feats.api_calls_per_month,
                    "credits": feats.credits,
                },
                "usage": {
                    "api_calls": api_calls,
                    "credits": credits,
                },
                "feature_flags": list(feats.flags),
            }
        )


class UsageIncrementView(APIView):
    """Record usage (metered billing + local limits)."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        ser = UsageIncrementSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ut = ser.validated_data["usage_type"]
        qty = ser.validated_data["quantity"]
        try:
            UsageService.check_within_limit(request.user, ut)
        except UsageLimitExceeded as e:
            return Response(
                {"detail": str(e), "limit": e.limit, "current": e.current},
                status=status.HTTP_403_FORBIDDEN,
            )
        UsageService.increment(request.user, ut, quantity=qty)
        UsageService.report_stripe_meter_if_configured(request.user, ut, qty)
        return Response({"ok": True})


class UsagePeriodListView(generics.ListAPIView):
    serializer_class = UsagePeriodSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.usage_periods.order_by("-period_start")[:24]


class SubscriptionDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        sub = Subscription.objects.filter(user=request.user).select_related("plan").first()
        if not sub:
            plan = FeatureAccessService.get_effective_plan(request.user)
            return Response(
                {
                    "subscription": None,
                    "effective_plan": PlanSerializer(plan).data,
                }
            )
        return Response(
            {
                "subscription": SubscriptionSerializer(sub).data,
                "effective_plan": PlanSerializer(sub.plan).data,
            }
        )


class LimitedPingView(APIView):
    """Example route protected by UsageEnforcementMiddleware (429 when over limit)."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({"ok": True, "message": "Within monthly API limit."})


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return InvoiceRecord.objects.filter(user=self.request.user)


class AdminPlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all().order_by("sort_order", "id")
    serializer_class = PlanSerializer
    permission_classes = (IsAuthenticated, IsAdminRole)


class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = (IsAuthenticated, IsAdminRole)


class AdminOrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all().order_by("name")
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated, IsAdminRole)
