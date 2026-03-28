import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from billing.models import WebhookEvent


@pytest.mark.django_db
def test_webhook_skips_when_already_processed(client):
    WebhookEvent.objects.create(
        stripe_event_id="evt_done",
        event_type="checkout.session.completed",
        processed_at=timezone.now(),
    )
    payload = json.dumps({"id": "evt_done", "type": "ping", "data": {"object": {}}}).encode()
    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = {"id": "evt_done", "type": "ping", "data": {"object": {}}}
        with patch("billing.webhook_views.process_stripe_event.delay") as mock_delay:
            client.post(
                reverse("stripe-webhook"),
                data=payload,
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="sig",
            )
            mock_delay.assert_not_called()


@pytest.mark.django_db
def test_webhook_queues_new_event(client):
    payload = json.dumps({"id": "evt_new", "type": "ping", "data": {"object": {}}}).encode()
    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = {"id": "evt_new", "type": "ping", "data": {"object": {}}}
        with patch("billing.webhook_views.process_stripe_event.delay") as mock_delay:
            client.post(
                reverse("stripe-webhook"),
                data=payload,
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="sig",
            )
            mock_delay.assert_called_once_with("evt_new")
