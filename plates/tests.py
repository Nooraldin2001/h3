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
        self.assertContains(response, "nld-sold-name")
        self.assertContains(response, "nld-gavel-stage")
        self.assertContains(response, "live-display-new.js")

    def test_classic_display_includes_sold_overlay(self):
        url = reverse("live_display", kwargs={"token": self.session.display_token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plates/live_display.html")
        self.assertContains(response, "live-sold-overlay")
        self.assertContains(response, "live-sold-name")
        self.assertContains(response, "triggerSoldCelebration")
        self.assertContains(response, "sold_event_id")
        self.assertContains(response, "live-gavel-stage")

    def test_new_display_invalid_token_returns_404(self):
        url = reverse("live_display_new", kwargs={"token": uuid.uuid4()})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_hub_shows_three_mode_cards(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plates/live_hub.html")
        classic_path = reverse("live_display", kwargs={"token": self.session.display_token})
        new_path = reverse("live_display_new", kwargs={"token": self.session.display_token})
        tiktok_path = reverse("live_display_tiktok", kwargs={"token": self.session.display_token})
        self.assertContains(response, classic_path)
        self.assertContains(response, new_path)
        self.assertContains(response, tiktok_path)
        self.assertContains(response, reverse("live_control_classic"))
        self.assertContains(response, reverse("live_control_new"))
        self.assertContains(response, reverse("live_control_tiktok"))

    def test_control_pages_return_200(self):
        self.client.force_login(self.user)
        for name in ("live_control_classic", "live_control_new", "live_control_tiktok"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertTemplateUsed(response, "plates/live_control_panel.html")
            self.assertContains(response, "sold-name")
            self.assertContains(response, "SOLD")
            self.assertContains(response, "sold-gavel-btn")

    def test_new_control_shows_event_title(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control_new"))
        self.assertContains(response, 'id="event-title"')
        self.assertContains(response, 'id="toggle-header-logo-btn"')
        self.assertNotContains(response, 'id="tiktok-brand-mode"')

    def test_classic_control_hides_header_logo_toggle(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control_classic"))
        self.assertNotContains(response, 'id="toggle-header-logo-btn"')

    def test_superuser_can_hide_header_logo(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"header_logo_visible": False}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertFalse(self.session.header_logo_visible)
        self.assertFalse(response.json()["header_logo_visible"])

    def test_tiktok_control_shows_brand_toggle(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control_tiktok"))
        self.assertContains(response, 'id="event-title"')
        self.assertContains(response, 'id="toggle-tiktok-watermark-btn"')
        self.assertContains(response, 'id="toggle-tiktok-logo-btn"')

    def test_tiktok_display_uses_existing_token(self):
        url = reverse("live_display_tiktok", kwargs={"token": self.session.display_token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plates/live_display_tiktok.html")
        self.assertContains(response, str(self.session.display_token))
        self.assertContains(response, "/live/api/state/")
        self.assertContains(response, "tld-sold-overlay")
        self.assertContains(response, "tld-sold-name")
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

    def test_superuser_can_update_sold_name_and_tiktok_brand(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "sold_name": "أحمد",
                "tiktok_brand_mode": "watermark",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.sold_name, "أحمد")
        self.assertEqual(self.session.tiktok_brand_mode, "watermark")
        self.assertEqual(response.json()["sold_name"], "أحمد")
        self.assertEqual(response.json()["tiktok_brand_mode"], "watermark")

    def test_superuser_can_set_tiktok_brand_empty(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"tiktok_brand_mode": "empty"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.tiktok_brand_mode, "empty")
        self.assertEqual(response.json()["tiktok_brand_mode"], "empty")

    def test_tiktok_control_shows_hide_brand_buttons(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control_tiktok"))
        self.assertContains(response, 'id="toggle-tiktok-watermark-btn"')
        self.assertContains(response, 'id="toggle-tiktok-logo-btn"')
        self.assertNotContains(response, 'id="tiktok-brand-mode"')

    def test_superuser_can_set_tiktok_brand_both(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"tiktok_brand_mode": "both"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.tiktok_brand_mode, "both")
        self.assertEqual(response.json()["tiktok_brand_mode"], "both")

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

    def test_superuser_can_trigger_sold_with_name(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "trigger_sold": True,
                "sold_style": "confetti",
                "sold_name": "محمد علي",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.sold_event_id, 1)
        self.assertEqual(self.session.sold_name, "محمد علي")
        self.assertEqual(response.json()["sold_name"], "محمد علي")

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

    def test_superuser_can_clear_custom_logo(self):
        self.client.force_login(self.user)
        self.session.logo = "live/logos/old.png"
        self.session.save(update_fields=["logo"])

        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"clear_logo": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertFalse(bool(self.session.logo))
        self.assertEqual(response.json()["logo_url"], "")

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
