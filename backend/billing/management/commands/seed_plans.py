from django.core.management.base import BaseCommand

from billing.models import Plan


class Command(BaseCommand):
    help = "Seed default Free / Pro / Enterprise plans (replace Stripe price IDs via admin or env)."

    def handle(self, *args, **options):
        defaults = [
            {
                "name": "Free",
                "slug": "free",
                "description": "Get started with core features.",
                "price_monthly_cents": 0,
                "price_yearly_cents": 0,
                "stripe_price_id_monthly": "",
                "stripe_price_id_yearly": "",
                "features": {
                    "limits": {"api_calls_per_month": 100, "credits": 10},
                    "feature_flags": ["basic_dashboard"],
                },
                "sort_order": 0,
            },
            {
                "name": "Pro",
                "slug": "pro",
                "description": "For growing teams.",
                "price_monthly_cents": 2900,
                "price_yearly_cents": 29000,
                "stripe_price_id_monthly": "",
                "stripe_price_id_yearly": "",
                "features": {
                    "limits": {"api_calls_per_month": 10000, "credits": 1000},
                    "feature_flags": ["basic_dashboard", "advanced_analytics", "priority_support"],
                },
                "sort_order": 10,
            },
            {
                "name": "Enterprise",
                "slug": "enterprise",
                "description": "Scale with dedicated support.",
                "price_monthly_cents": 9900,
                "price_yearly_cents": 99000,
                "stripe_price_id_monthly": "",
                "stripe_price_id_yearly": "",
                "features": {
                    "limits": {"api_calls_per_month": 1000000, "credits": 100000},
                    "feature_flags": ["basic_dashboard", "advanced_analytics", "priority_support", "sso"],
                },
                "sort_order": 20,
            },
        ]
        for row in defaults:
            slug = row.pop("slug")
            Plan.objects.update_or_create(slug=slug, defaults=row)
            self.stdout.write(self.style.SUCCESS(f"Upserted plan: {slug}"))
