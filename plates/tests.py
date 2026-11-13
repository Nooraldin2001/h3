import json
import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import LiveBroadcastSession
from .new_style import (
    letter_only_sprite_ok,
    normalize_new_style,
    replay_aging_clock,
    reset_aging_clock,
)


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
        url = reverse("live_display_new", kwargs={"token": self.session.new_style_display_token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nld-sold-overlay")
        self.assertContains(response, "nld-sold-name")
        self.assertContains(response, "nld-fireworks")
        self.assertContains(response, "live-display-new.js")
        self.assertContains(response, "H2")
        self.assertContains(response, "AUCTIONS")
        self.assertContains(response, "nld-timer-capsule")
        self.assertContains(response, "Current Bid")
        self.assertNotContains(response, "Sun Mix")
        self.assertNotContains(response, "STANDBY")
        self.assertNotContains(response, "CLOSING")

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
        new_path = reverse(
            "live_display_new", kwargs={"token": self.session.new_style_display_token}
        )
        tiktok_path = reverse("live_display_tiktok", kwargs={"token": self.session.display_token})
        self.assertContains(response, classic_path)
        self.assertContains(response, new_path)
        self.assertContains(response, tiktok_path)
        self.assertNotEqual(
            str(self.session.display_token),
            str(self.session.new_style_display_token),
        )
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

    def test_classic_and_tiktok_keep_gavel_button(self):
        self.client.force_login(self.user)
        for name in ("live_control_classic", "live_control_tiktok"):
            response = self.client.get(reverse(name))
            self.assertContains(response, "sold-gavel-btn", msg_prefix=name)

    def test_new_control_hides_gavel_and_shows_v2(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control_new"))
        self.assertNotContains(response, 'id="sold-gavel-btn"')
        self.assertContains(response, 'id="ns-show-number-btn"')
        self.assertContains(response, 'id="ns-aging-reset-btn"')
        self.assertContains(response, 'id="ns-beam-btn"')
        self.assertContains(response, 'id="ns-kandura-btn"')
        self.assertContains(response, 'id="ns-char-point-btn"')
        self.assertContains(response, 'id="ns-char-yellow-btn"')
        self.assertContains(response, 'id="ns-char-red-btn"')
        self.assertContains(response, 'id="ns-char-sold-stamp-btn"')
        self.assertContains(response, 'id="ns-bg-motion-enabled"')
        self.assertContains(response, 'id="ns-background-id"')
        self.assertContains(response, "fireworks")

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
        self.assertNotContains(response, 'id="ns-show-number-btn"')

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
        self.assertNotContains(response, "Red title shown on the display header.")
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

    def test_superuser_can_trigger_fireworks_sold_event(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"trigger_sold": True, "sold_style": "fireworks"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.sold_style, "fireworks")
        self.assertEqual(response.json()["sold_style"], "fireworks")

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

    def test_state_api_includes_normalized_new_style(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_state_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("new_style", payload)
        self.assertIn("server_now", payload)
        ns = payload["new_style"]
        self.assertEqual(ns["aging"]["fresh_delay_seconds"], 50)
        self.assertEqual(ns["aging"]["aging_duration_seconds"], 10)
        self.assertTrue(ns["number_visible"])
        self.assertEqual(ns["background_id"], "stage_dark_01")
        self.assertEqual(ns["studio_theme"], "dark")

    def test_ns_drop_persists_number_hidden(self):
        self.client.force_login(self.user)
        drop = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_drop": True}),
            content_type="application/json",
        )
        self.assertEqual(drop.status_code, 200)
        body = drop.json()
        self.assertFalse(body["new_style"]["number_visible"])
        self.assertEqual(body["new_style"]["events"]["drop_event_id"], 1)
        self.session.refresh_from_db()
        self.assertFalse((self.session.new_style or {}).get("number_visible"))
        again = self.client.get(reverse("live_state_api"))
        self.assertFalse(again.json()["new_style"]["number_visible"])

    def test_clear_sold_bumps_clear_event_without_sold_id(self):
        self.client.force_login(self.user)
        sold = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"trigger_sold": True, "sold_style": "fireworks"}),
            content_type="application/json",
        )
        sold_id = sold.json()["sold_event_id"]
        self.assertTrue(sold.json()["new_style"]["sold_imprint_active"])
        clear = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"clear_sold": True}),
            content_type="application/json",
        )
        self.assertEqual(clear.status_code, 200)
        body = clear.json()
        self.assertEqual(body["sold_event_id"], sold_id)
        self.assertEqual(body["new_style"]["events"]["sold_clear_event_id"], 1)
        self.assertFalse(body["new_style"]["sold_imprint_active"])
        again = self.client.get(reverse("live_state_api"))
        self.assertFalse(again.json()["new_style"]["sold_imprint_active"])

    def test_new_number_forces_visible_after_hide(self):
        self.client.force_login(self.user)
        self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"number": "7777"}),
            content_type="application/json",
        )
        self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_hide_number": True}),
            content_type="application/json",
        )
        hidden = self.client.get(reverse("live_state_api")).json()
        self.assertEqual(hidden["number"], "7777")
        self.assertFalse(hidden["new_style"]["number_visible"])

        shown = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"number": "8888"}),
            content_type="application/json",
        )
        self.assertEqual(shown.status_code, 200)
        body = shown.json()
        self.assertEqual(body["number"], "8888")
        self.assertTrue(body["new_style"]["number_visible"])

        # Same number re-applied must not auto-reveal a deliberate hide
        self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_hide_number": True}),
            content_type="application/json",
        )
        keep = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"number": "8888"}),
            content_type="application/json",
        )
        self.assertFalse(keep.json()["new_style"]["number_visible"])

    def test_studio_theme_patch_persists(self):
        self.client.force_login(self.user)
        light = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"new_style": {"studio_theme": "light"}}),
            content_type="application/json",
        )
        self.assertEqual(light.status_code, 200)
        self.assertEqual(light.json()["new_style"]["studio_theme"], "light")
        self.session.refresh_from_db()
        self.assertEqual(
            (self.session.new_style or {}).get("studio_theme"),
            "light",
        )
        again = self.client.get(reverse("live_state_api"))
        self.assertEqual(again.json()["new_style"]["studio_theme"], "light")

        dark = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"new_style": {"studio_theme": "dark"}}),
            content_type="application/json",
        )
        self.assertEqual(dark.json()["new_style"]["studio_theme"], "dark")

        new_mode = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"new_style": {"studio_theme": "new"}}),
            content_type="application/json",
        )
        self.assertEqual(new_mode.json()["new_style"]["studio_theme"], "new")
        self.session.refresh_from_db()
        self.assertEqual((self.session.new_style or {}).get("studio_theme"), "new")

        bad = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"new_style": {"studio_theme": "neon"}}),
            content_type="application/json",
        )
        self.assertEqual(bad.json()["new_style"]["studio_theme"], "dark")

    def test_token_get_authorized_anonymous(self):
        response = self.client.get(
            reverse("live_state_api"),
            {"token": str(self.session.display_token)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["number"], "5555")

    def test_anonymous_without_token_forbidden(self):
        response = self.client.get(reverse("live_state_api"))
        self.assertEqual(response.status_code, 403)

    def test_non_superuser_patch_forbidden(self):
        User = get_user_model()
        plain = User.objects.create_user(username="plain", password="password")
        self.client.force_login(plain)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"price": "1"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_show_hide_number_events(self):
        self.client.force_login(self.user)
        hide = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_hide_number": True}),
            content_type="application/json",
        )
        self.assertEqual(hide.status_code, 200)
        self.assertFalse(hide.json()["new_style"]["number_visible"])
        self.assertEqual(hide.json()["new_style"]["events"]["hide_event_id"], 1)
        self.assertEqual(hide.json()["number"], "5555")

        show = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_show_number": True}),
            content_type="application/json",
        )
        self.assertTrue(show.json()["new_style"]["number_visible"])
        self.assertEqual(show.json()["new_style"]["events"]["reveal_event_id"], 1)

        replay = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_replay_reveal": True}),
            content_type="application/json",
        )
        self.assertEqual(replay.json()["new_style"]["events"]["reveal_replay_event_id"], 1)

    def test_background_and_beam_and_drop_and_kandura(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "new_style": {"background_id": "stage_spotlight"},
                "ns_beam": True,
                "ns_drop": True,
                "ns_kandura": True,
                "ns_kandura_prefs": {"entry": "right", "speed": 1.5, "point_ms": 2000},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        ns = response.json()["new_style"]
        self.assertEqual(ns["background_id"], "stage_spotlight")
        self.assertEqual(ns["events"]["beam_event_id"], 1)
        self.assertEqual(ns["events"]["drop_event_id"], 1)
        self.assertEqual(ns["events"]["kandura_event_id"], 1)
        self.assertEqual(ns["events"]["char_point_event_id"], 1)
        self.assertEqual(ns["kandura"]["entry"], "right")
        self.assertEqual(ns["kandura"]["point_ms"], 2000)
        self.assertEqual(ns["character"]["entry"], "right")
        self.assertEqual(ns["character"]["speed"], 1.5)

    def test_aging_defaults_and_reset_replay(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "new_style": {
                    "aging": {
                        "fresh_delay_seconds": 50,
                        "aging_duration_seconds": 10,
                    }
                },
                "ns_aging_reset": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        ns = response.json()["new_style"]
        self.assertEqual(ns["aging"]["fresh_delay_seconds"], 50)
        self.assertEqual(ns["aging"]["aging_duration_seconds"], 10)
        self.assertTrue(bool(ns["aging"]["started_at"]))
        self.assertEqual(ns["events"]["aging_reset_event_id"], 1)
        started = ns["aging"]["started_at"]

        replay = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_aging_replay": True}),
            content_type="application/json",
        )
        self.assertEqual(replay.status_code, 200)
        replay_ns = replay.json()["new_style"]
        self.assertEqual(replay_ns["events"]["aging_replay_event_id"], 1)
        self.assertNotEqual(replay_ns["aging"]["started_at"], started)

    def test_plate_identity_change_resets_aging(self):
        self.client.force_login(self.user)
        first = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_aging_reset": True}),
            content_type="application/json",
        )
        started = first.json()["new_style"]["aging"]["started_at"]
        second = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"number": "9999"}),
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 200)
        ns = second.json()["new_style"]
        self.assertNotEqual(ns["aging"]["started_at"], started)
        self.assertGreaterEqual(ns["events"]["aging_reset_event_id"], 1)

    def test_unrelated_patch_does_not_clear_aging_clock(self):
        self.client.force_login(self.user)
        primed = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_aging_reset": True}),
            content_type="application/json",
        )
        started = primed.json()["new_style"]["aging"]["started_at"]
        reset_id = primed.json()["new_style"]["events"]["aging_reset_event_id"]
        follow = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"price": "200000", "message": "same plate"}),
            content_type="application/json",
        )
        self.assertEqual(follow.json()["new_style"]["aging"]["started_at"], started)
        self.assertEqual(follow.json()["new_style"]["events"]["aging_reset_event_id"], reset_id)

    def test_normalize_and_replay_helpers(self):
        ns = normalize_new_style({})
        self.assertEqual(ns["aging"]["fresh_delay_seconds"], 50)
        self.assertEqual(ns["aging"]["aging_duration_seconds"], 10)
        now = timezone.now()
        reset_aging_clock(ns, when=now)
        self.assertEqual(ns["aging"]["started_at"], now.isoformat())
        replay_aging_clock(ns, when=now)
        started = datetime.fromisoformat(ns["aging"]["started_at"])
        if timezone.is_naive(started):
            started = timezone.make_aware(started, timezone.get_current_timezone())
        self.assertAlmostEqual(
            (now - started).total_seconds(),
            50,
            delta=1,
        )
        # Completing lifecycle does not auto-reset in helpers
        ns["aging"]["started_at"] = (now - timedelta(seconds=120)).isoformat()
        before = ns["aging"]["started_at"]
        ns2 = normalize_new_style(ns)
        self.assertEqual(ns2["aging"]["started_at"], before)

    def test_watermark_prefs_merge(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "new_style": {
                    "watermarks": {
                        "h2": {"visible": True, "scale": 1.2},
                        "sun_mix": {"visible": True, "x": 0.9, "y": 0.85},
                    }
                }
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        marks = response.json()["new_style"]["watermarks"]
        self.assertTrue(marks["h2"]["visible"])
        self.assertEqual(marks["h2"]["scale"], 1.2)
        self.assertNotIn("sun_mix", marks)

    def test_new_control_has_no_sun_mix(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control_new"))
        self.assertNotContains(response, "Sun Mix")
        self.assertNotContains(response, "ns-wm-sunmix")
        self.assertContains(response, "H2")

    def test_bg_motion_prefs_patch(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "new_style": {
                    "bg_motion_enabled": False,
                    "bg_speed": 2.5,
                    "bg_density": "high",
                }
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        ns = response.json()["new_style"]
        self.assertFalse(ns["bg_motion_enabled"])
        self.assertEqual(ns["bg_speed"], 2.5)
        self.assertEqual(ns["bg_density"], 1.75)

        clamped = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "bg_motion_enabled": True,
                "bg_speed": 9,
                "bg_density": 0.1,
            }),
            content_type="application/json",
        )
        ns2 = clamped.json()["new_style"]
        self.assertTrue(ns2["bg_motion_enabled"])
        self.assertEqual(ns2["bg_speed"], 3.0)
        self.assertEqual(ns2["bg_density"], 0.25)

    def test_letter_only_sprite_allowlist(self):
        self.assertTrue(letter_only_sprite_ok("A"))
        self.assertTrue(letter_only_sprite_ok("aa"))
        self.assertTrue(letter_only_sprite_ok("ZZ"))
        self.assertFalse(letter_only_sprite_ok("A1"))
        self.assertFalse(letter_only_sprite_ok("12"))
        self.assertFalse(letter_only_sprite_ok(""))
        self.assertFalse(letter_only_sprite_ok("ABC"))

    def test_character_event_triggers(self):
        self.client.force_login(self.user)
        point = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({
                "ns_char_point": True,
                "ns_character_prefs": {"entry": "right", "speed": 1.25},
            }),
            content_type="application/json",
        )
        self.assertEqual(point.status_code, 200)
        ns = point.json()["new_style"]
        self.assertEqual(ns["events"]["char_point_event_id"], 1)
        self.assertEqual(ns["events"]["kandura_event_id"], 1)
        self.assertEqual(ns["character"]["entry"], "right")

        yellow = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_char_yellow": True}),
            content_type="application/json",
        )
        self.assertEqual(yellow.json()["new_style"]["events"]["char_yellow_event_id"], 1)
        self.assertTrue(yellow.json()["new_style"]["number_visible"])

        red = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_char_red": True}),
            content_type="application/json",
        )
        red_ns = red.json()["new_style"]
        self.assertEqual(red_ns["events"]["char_red_event_id"], 1)
        self.assertFalse(red_ns["number_visible"])
        self.assertEqual(red.json()["number"], "5555")

        sold_before = self.session.sold_event_id or 0
        stamp = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"ns_char_sold_stamp": True}),
            content_type="application/json",
        )
        stamp_ns = stamp.json()["new_style"]
        self.assertEqual(stamp_ns["events"]["char_sold_stamp_event_id"], 1)
        self.assertGreater(stamp.json()["sold_event_id"], sold_before)
        self.assertEqual(stamp.json()["sold_style"], "fireworks")

    def test_new_display_has_v3_layers(self):
        url = reverse(
            "live_display_new", kwargs={"token": self.session.new_style_display_token}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="nld-bg-plates-layer"')
        self.assertContains(response, 'id="nld-character-layer"')
        self.assertContains(response, 'id="nld-character-video"')
        self.assertContains(response, 'id="nld-sold-stamp"')
        self.assertContains(response, 'id="nld-plate-fw"')
        self.assertContains(response, "live_new/v3/character/")
        self.assertContains(response, "debugCharacterStub")
        self.assertContains(response, "m1Preview: false")
        self.assertNotContains(response, "nld-m1-preview")

    def test_m1_preview_mode_is_non_destructive(self):
        url = reverse(
            "live_display_new", kwargs={"token": self.session.new_style_display_token}
        )
        response = self.client.get(url, {"m1_preview": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nld-m1-preview")
        self.assertContains(response, "m1Preview: true")
        self.assertContains(response, "nld-stage-stack")
        self.assertContains(response, "nld-studio-hero")
        self.assertContains(response, "live_new/v3/studio/stage-hero.jpg")
        # Session auction fields untouched by preview GET
        self.session.refresh_from_db()
        self.assertEqual(self.session.number, "5555")
        self.assertEqual(self.session.alert_message, "Live alert")

@override_settings(LIVE_AUCTION_ENABLED=True, LIVE_V4_ENABLED=True)
class LiveV4IntegrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="v4-admin",
            email="v4-admin@example.com",
            password="password",
        )
        self.session = LiveBroadcastSession.objects.create(
            user=self.user,
            plate_type="dubai",
            code="AA",
            number="7777",
            price=1250000,
        )

    def test_hub_shows_v4_card(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("live_control"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("live_control_v4"))
        v4_path = reverse("live_display_v4", kwargs={"token": self.session.display_token})
        self.assertContains(response, v4_path)

    def test_v4_display_serves_v4_assets_not_new_style(self):
        url = reverse("live_display_v4", kwargs={"token": self.session.display_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "live_v4/js/broadcast.js")
        self.assertContains(response, "live_v4/js/django-bridge.js")
        self.assertContains(response, "H2V4_DJANGO")
        self.assertContains(response, "H2_AUCTIONS_Studio_4K_Vector.svg")
        self.assertContains(response, "H2_AUCTIONS_Light_Studio.svg")
        self.assertContains(response, "H2_AUCTIONS_Dubai_Studio_4K.svg")
        self.assertContains(response, "data-studio-dark=")
        self.assertContains(response, "data-studio-light=")
        self.assertContains(response, "data-studio-new=")
        self.assertNotContains(response, "live-display-new.js")
        self.assertNotContains(response, "live_new/v3/studio/stage-hero.jpg")

    def test_v4_display_invalid_token_404(self):
        url = reverse("live_display_v4", kwargs={"token": uuid.uuid4()})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_v4_control_requires_superuser(self):
        response = self.client.get(reverse("live_control_v4"))
        self.assertIn(response.status_code, (302, 403))
        self.client.force_login(self.user)
        ok = self.client.get(reverse("live_control_v4"))
        self.assertEqual(ok.status_code, 200)
        self.assertContains(ok, "data-mode=\"django\"")
        self.assertContains(ok, "live_v4/js/admin.js")
        self.assertContains(ok, "خلفية الاستوديو")
        self.assertContains(ok, "btn-studio-dark")
        self.assertContains(ok, "btn-studio-light")
        self.assertContains(ok, "btn-studio-new")
        self.assertContains(ok, "الوضع الجديد")
        self.assertContains(ok, "btn-cancel-sold")
        self.assertContains(ok, "btn-cancel-sold-char")
        self.assertContains(ok, "إلغاء البيع (UNSOLD)")

    def test_live_text_patch_roundtrip(self):
        self.client.force_login(self.user)
        patch = self.client.patch(
            reverse("live_state_api"),
            data=json.dumps({"live_text_line1": "????", "live_text_line2": "Live"}),
            content_type="application/json",
        )
        self.assertEqual(patch.status_code, 200)
        body = patch.json()
        self.assertEqual(body["live_text_line1"], "????")
        self.assertEqual(body["live_text_line2"], "Live")
        # Display token GET sees same values
        got = self.client.get(
            reverse("live_state_api"),
            {"token": str(self.session.display_token)},
        )
        self.assertEqual(got.status_code, 200)
        self.assertEqual(got.json()["live_text_line1"], "????")

    def test_classic_and_new_style_still_work(self):
        classic = reverse("live_display", kwargs={"token": self.session.display_token})
        new = reverse(
            "live_display_new", kwargs={"token": self.session.new_style_display_token}
        )
        self.assertEqual(self.client.get(classic).status_code, 200)
        self.assertEqual(self.client.get(new).status_code, 200)

    @override_settings(LIVE_V4_ENABLED=False)
    def test_v4_disabled_returns_404(self):
        url = reverse("live_display_v4", kwargs={"token": self.session.display_token})
        self.assertEqual(self.client.get(url).status_code, 404)


@override_settings(LIVE_AUCTION_ENABLED=True)
class LiveTimerReliabilityTests(TestCase):
    """Authoritative ends_at timer: start ceil, idle duration, pause/resume, completion."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="timer-admin",
            email="timer-admin@example.com",
            password="password",
        )
        self.session = LiveBroadcastSession.objects.create(
            user=self.user,
            plate_type="dubai",
            code="AA",
            number="8258",
            timer_seconds=60,
        )

    def _patch(self, payload):
        self.client.force_login(self.user)
        return self.client.patch(
            reverse("live_state_api"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_idle_shows_configured_duration_not_zero(self):
        self.client.force_login(self.user)
        body = self.client.get(reverse("live_state_api")).json()
        self.assertFalse(body["timer_active"])
        self.assertEqual(body["timer_seconds"], 60)
        self.assertEqual(body["timer_remaining_seconds"], 60)

    def test_set_duration_does_not_start(self):
        res = self._patch({"timer_seconds": 120})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["timer_seconds"], 120)
        self.assertEqual(body["timer_remaining_seconds"], 120)
        self.assertFalse(body["timer_active"])
        self.assertIsNone(body["timer_ends_at"])

    def test_start_remaining_equals_duration_ceil(self):
        res = self._patch({"timer_seconds": 60, "start_timer": True})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["timer_active"])
        self.assertIsNotNone(body["timer_ends_at"])
        # Must not truncate to 59 via int()/floor immediately after start
        self.assertEqual(body["timer_remaining_seconds"], 60)
        self.assertIn("server_now", body)

    def test_start_durations_matrix(self):
        for dur in (10, 30, 60, 120, 300):
            res = self._patch({"timer_seconds": dur, "start_timer": True})
            self.assertEqual(res.status_code, 200, dur)
            body = res.json()
            self.assertEqual(body["timer_remaining_seconds"], dur, dur)
            self.assertTrue(body["timer_active"], dur)
            self._patch({"reset_timer": True})

    def test_pause_resume_preserves_remaining(self):
        self._patch({"timer_seconds": 60, "start_timer": True})
        # Force ~15s elapsed by rewriting ends_at
        self.session.refresh_from_db()
        self.session.timer_ends_at = timezone.now() + timedelta(seconds=45)
        self.session.save(update_fields=["timer_ends_at"])
        paused = self._patch({"pause_timer": True}).json()
        self.assertFalse(paused["timer_active"])
        self.assertIsNone(paused["timer_ends_at"])
        self.assertEqual(paused["timer_paused_remaining"], 45)
        self.assertEqual(paused["timer_remaining_seconds"], 45)
        resumed = self._patch({"resume_timer": True}).json()
        self.assertTrue(resumed["timer_active"])
        self.assertEqual(resumed["timer_remaining_seconds"], 45)
        self.assertIsNone(resumed["timer_paused_remaining"])

    def test_reset_restores_full_duration(self):
        self._patch({"timer_seconds": 90, "start_timer": True})
        reset = self._patch({"reset_timer": True}).json()
        self.assertFalse(reset["timer_active"])
        self.assertIsNone(reset["timer_ends_at"])
        self.assertIsNone(reset["timer_paused_remaining"])
        self.assertEqual(reset["timer_seconds"], 90)
        self.assertEqual(reset["timer_remaining_seconds"], 90)

    def test_completed_deadline_shows_zero_not_restart(self):
        self._patch({"timer_seconds": 10, "start_timer": True})
        self.session.refresh_from_db()
        self.session.timer_ends_at = timezone.now() - timedelta(seconds=2)
        self.session.save(update_fields=["timer_ends_at"])
        body = self.client.get(reverse("live_state_api")).json()
        self.assertEqual(body["timer_remaining_seconds"], 0)
        self.assertFalse(body["timer_active"])
        # ends_at may remain for audit; must not present as running
        self.assertFalse(body["timer_active"])

    def test_double_start_refreshes_deadline(self):
        first = self._patch({"timer_seconds": 60, "start_timer": True}).json()
        second = self._patch({"timer_seconds": 60, "start_timer": True}).json()
        self.assertTrue(second["timer_active"])
        self.assertEqual(second["timer_remaining_seconds"], 60)
        self.assertNotEqual(first["timer_ends_at"], second["timer_ends_at"])

    def test_display_ceil_helper_near_boundary(self):
        from plates.views import _timer_display_remaining_seconds

        now = timezone.now()
        # Just under 60s left → still display 60 with ceil
        ends = now + timedelta(milliseconds=59950)
        self.assertEqual(_timer_display_remaining_seconds(ends, now=now), 60)
        # Exactly 0
        self.assertEqual(_timer_display_remaining_seconds(now, now=now), 0)
        # Past
        self.assertEqual(
            _timer_display_remaining_seconds(now - timedelta(seconds=1), now=now),
            0,
        )
