from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from django.contrib.auth import get_user_model

from billing.models import Plan, Subscription, SubscriptionStatus

User = get_user_model()


class UsageLimitExceeded(Exception):
    def __init__(self, usage_type: str, limit: int, current: int):
        self.usage_type = usage_type
        self.limit = limit
        self.current = current
        super().__init__(f"Usage limit exceeded for {usage_type}: {current}/{limit}")


@dataclass(frozen=True)
class PlanFeatures:
    api_calls_per_month: int
    credits: int
    flags: frozenset[str]

    @classmethod
    def from_plan(cls, plan: Plan | None) -> PlanFeatures:
        raw = (plan.features or {}) if plan else {}
        limits = raw.get("limits") or {}
        flags = raw.get("feature_flags") or []
        return cls(
            api_calls_per_month=int(limits.get("api_calls_per_month", 100)),
            credits=int(limits.get("credits", 10)),
            flags=frozenset(flags) if isinstance(flags, list) else frozenset(),
        )


class FeatureAccessService:
    """Resolve effective plan from active subscription or default Free plan."""

    @staticmethod
    def get_effective_plan(user) -> Plan:
        sub = (
            Subscription.objects.select_related("plan")
            .filter(
                user=user,
                status__in=(SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING),
            )
            .first()
        )
        if sub:
            return sub.plan
        return (
            Plan.objects.filter(slug="free", is_active=True).first()
            or Plan.objects.filter(is_active=True).order_by("sort_order").first()
        )

    @staticmethod
    def plan_features(user) -> PlanFeatures:
        return PlanFeatures.from_plan(FeatureAccessService.get_effective_plan(user))

    @staticmethod
    def user_has_flag(user, flag: str) -> bool:
        return flag in FeatureAccessService.plan_features(user).flags
