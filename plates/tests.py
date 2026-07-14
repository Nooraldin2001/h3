import json
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import LiveBroadcastSession


@override_settings(LIVE_AUCTION_ENABLED=True)
class LiveDisplayNewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="live-admin",
            email="live-admin@example.com",
            password="password",
        )
        self.session = LiveBroadcastSession.objects.create(
            user=self.user,
            plate_type="dubai_yellow",
            code="S",
            number="5555",
            price=150000,
            message="Live ticker",
            alert_message="Live alert",
        )

    def test_new_display_uses_existing_token(self):
        url = reverse("live_display_new", kwargs={"token": self.session.display_token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plates/live_display_new.html")
        self.assertContains(response, str(self.session.display_token))
        self.assertContains(response, "/live/api/state/")

    def test_new_display_invalid_token_returns_404(self):
        url = reverse("live_display_new", kwargs={"token": uuid.uuid4()})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_control_panel_shows_classic_and_new_display_urls(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control"))

        self.assertEqual(response.status_code, 200)
        classic_path = reverse("live_display", kwargs={"token": self.session.display_token})
        new_path = reverse("live_display_new", kwargs={"token": self.session.display_token})
        self.assertContains(response, classic_path)
        self.assertContains(response, new_path)
        self.assertContains(response, "Classic display URL")
        self.assertContains(response, "New style display URL")
        self.assertContains(response, "SOLD")

    def test_superuser_can_trigger_sold_event(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"trigger_sold": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.sold_event_id, 1)
        self.assertIsNotNone(self.session.sold_event_at)
        self.assertEqual(response.json()["sold_event_id"], 1)
