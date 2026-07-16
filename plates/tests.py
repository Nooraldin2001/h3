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

    def test_new_display_includes_sold_overlay(self):
        url = reverse("live_display_new", kwargs={"token": self.session.display_token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nld-sold-overlay")
        self.assertContains(response, "nld-gavel-stage")
        self.assertContains(response, "live-display-new.js")

    def test_classic_display_includes_sold_overlay(self):
        url = reverse("live_display", kwargs={"token": self.session.display_token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plates/live_display.html")
        self.assertContains(response, "live-sold-overlay")
        self.assertContains(response, "triggerSoldCelebration")
        self.assertContains(response, "sold_event_id")
        self.assertContains(response, "live-gavel-stage")

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
        self.assertContains(response, "TikTok display URL")
        tiktok_path = reverse("live_display_tiktok", kwargs={"token": self.session.display_token})
        self.assertContains(response, tiktok_path)
        self.assertContains(response, "SOLD")
        self.assertContains(response, "sold-gavel-btn")
        self.assertContains(response, "SOLD — Gavel")
        self.assertContains(response, "Event title (new style header)")
        self.assertContains(response, 'id="event-title"')

    def test_tiktok_display_uses_existing_token(self):
        url = reverse("live_display_tiktok", kwargs={"token": self.session.display_token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plates/live_display_tiktok.html")
        self.assertContains(response, str(self.session.display_token))
        self.assertContains(response, "/live/api/state/")
        self.assertContains(response, "tld-sold-overlay")
        self.assertContains(response, "live-display-tiktok.js")

    def test_tiktok_display_invalid_token_returns_404(self):
        url = reverse("live_display_tiktok", kwargs={"token": uuid.uuid4()})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_superuser_can_update_event_title(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"event_title": "عنوان المزاد الجديد"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.event_title, "عنوان المزاد الجديد")
        self.assertEqual(response.json()["event_title"], "عنوان المزاد الجديد")

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
        self.assertEqual(self.session.sold_style, "confetti")
        self.assertEqual(response.json()["sold_event_id"], 1)
        self.assertEqual(response.json()["sold_style"], "confetti")

    def test_superuser_can_trigger_gavel_sold_event(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"trigger_sold": True, "sold_style": "gavel"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.sold_event_id, 1)
        self.assertEqual(self.session.sold_style, "gavel")
        self.assertEqual(response.json()["sold_style"], "gavel")

    def test_invalid_sold_style_falls_back_to_confetti(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"trigger_sold": True, "sold_style": "unknown"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.sold_style, "confetti")
        self.assertEqual(response.json()["sold_style"], "confetti")
