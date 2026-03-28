from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from billing.models import UsageLog, UsagePeriod
from billing.services.feature_access import FeatureAccessService, UsageLimitExceeded

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


class UsageService:
    @staticmethod
    def current_period_start() -> date:
        today = timezone.localdate()
        return _month_start(today)

    @staticmethod
    def increment(user, usage_type: str, quantity: int = 1, metadata: dict | None = None) -> UsagePeriod:
        """Log usage and bump period aggregate."""
        if quantity < 1:
            raise ValueError("quantity must be >= 1")
        period_start = UsageService.current_period_start()
        with transaction.atomic():
            UsageLog.objects.create(
                user=user,
                usage_type=usage_type,
                quantity=quantity,
                metadata=metadata or {},
            )
            period, _ = UsagePeriod.objects.select_for_update().get_or_create(
                user=user,
                usage_type=usage_type,
                period_start=period_start,
                defaults={"total": 0},
            )
            UsagePeriod.objects.filter(pk=period.pk).update(total=F("total") + quantity)
            period.refresh_from_db()
        return period

    @staticmethod
    def get_period_total(user, usage_type: str, period_start: date | None = None) -> int:
        ps = period_start or UsageService.current_period_start()
        row = UsagePeriod.objects.filter(user=user, usage_type=usage_type, period_start=ps).first()
        return row.total if row else 0

    @staticmethod
    def check_within_limit(user, usage_type: str = "api_calls") -> None:
        """Raise UsageLimitExceeded if user exceeded plan limit for usage_type."""
        feats = FeatureAccessService.plan_features(user)
        limit_map = {
            "api_calls": feats.api_calls_per_month,
            "credits": feats.credits,
        }
        limit = limit_map.get(usage_type)
        if limit is None:
            limit = feats.api_calls_per_month
        current = UsageService.get_period_total(user, usage_type)
        if current >= limit:
            raise UsageLimitExceeded(usage_type, limit, current)

    @staticmethod
    def report_stripe_meter_if_configured(user, usage_type: str, quantity: int) -> None:
        """Send usage record to Stripe when metered item is configured (best-effort)."""
        from billing.services import stripe_service

        stripe_service.report_usage_for_user(user, usage_type, quantity)
