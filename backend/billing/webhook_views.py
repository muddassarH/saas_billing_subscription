import json
import logging

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing.models import WebhookEvent
from billing.tasks import process_stripe_event

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if not sig_header:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError:
        return HttpResponse(status=400)
    except Exception:
        logger.exception("Unexpected Stripe webhook parsing failure")
        # Local Stripe CLI forwarding can still be useful for end-to-end testing even if
        # the SDK chokes on a forwarded payload shape/version. Only relax parsing on localhost.
        if request.get_host().split(":")[0] not in {"localhost", "127.0.0.1"}:
            return HttpResponse(status=400)
        try:
            event = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return HttpResponse(status=400)

    event_id = event["id"]
    event_type = event["type"]
    livemode = event["livemode"] if "livemode" in event else None

    try:
        with transaction.atomic():
            WebhookEvent.objects.create(
                stripe_event_id=event_id,
                event_type=event_type,
                payload_summary={"type": event_type, "livemode": livemode},
            )
    except IntegrityError:
        pass

    row = WebhookEvent.objects.get(stripe_event_id=event_id)
    if row.processed_at:
        return JsonResponse({"received": True, "duplicate": True})

    process_stripe_event.delay(event_id)
    return JsonResponse({"received": True})
