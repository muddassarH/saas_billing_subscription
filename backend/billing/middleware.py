import logging

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from billing.services.feature_access import FeatureAccessService
from billing.services.usage import UsageService

logger = logging.getLogger(__name__)


class UsageEnforcementMiddleware:
    """
    For configured URL prefixes, block anonymous users and users over usage limits
    for the `api_calls` bucket (example protected API surface).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        prefixes = getattr(settings, "USAGE_ENFORCED_PATH_PREFIXES", ("/api/limited/",))
        self.prefixes = tuple(prefixes)
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        path = request.path
        if not any(path.startswith(p) for p in self.prefixes):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            try:
                auth_result = self.jwt_auth.authenticate(request)
            except AuthenticationFailed:
                auth_result = None
            if auth_result:
                user, _ = auth_result
                request.user = user
        if not user or not user.is_authenticated:
            return JsonResponse({"detail": "Authentication required"}, status=401)

        feats = FeatureAccessService.plan_features(user)
        current = UsageService.get_period_total(user, "api_calls")
        if current >= feats.api_calls_per_month:
            return JsonResponse(
                {
                    "detail": "Monthly API usage limit exceeded for your plan.",
                    "usage_type": "api_calls",
                    "limit": feats.api_calls_per_month,
                    "current": current,
                },
                status=429,
            )

        return self.get_response(request)
