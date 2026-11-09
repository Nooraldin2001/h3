"""New Style Live V3 state helpers (prefs + one-shot event counters)."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime


BACKGROUND_IDS = (
	"stage_dark_01",
	"stage_dark_02",
	"stage_spotlight",
	"stage_violet",
)

DEFAULT_FRESH_DELAY = 50
DEFAULT_AGING_DURATION = 10

# Letter-only floating background plate codes (A..Z and AA..ZZ). ZERO digits.
LETTER_PLATE_CODES = tuple(
	list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
	+ [ch + ch for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
)

_DENSITY_LABELS = {
	"low": 0.5,
	"med": 1.0,
	"medium": 1.0,
	"high": 1.75,
}


def letter_only_sprite_ok(code: str) -> bool:
	"""Return True when code is a digit-free letter plate sprite allowlist entry."""
	if not isinstance(code, str):
		return False
	normalized = code.strip().upper()
	if not normalized or re.search(r"\d", normalized):
		return False
	return normalized in LETTER_PLATE_CODES


def _events_defaults():
	return {
		"reveal_event_id": 0,
		"hide_event_id": 0,
		"reveal_replay_event_id": 0,
		"beam_event_id": 0,
		"drop_event_id": 0,
		"aging_reset_event_id": 0,
		"aging_replay_event_id": 0,
		# Legacy single-shot walker (maps to char_point when triggered via ns_kandura)
		"kandura_event_id": 0,
		"char_point_event_id": 0,
		"char_yellow_event_id": 0,
		"char_red_event_id": 0,
		"char_sold_stamp_event_id": 0,
	}


def _watermark_defaults(x=0.05, y=0.9):
	return {
		"visible": False,
		"x": x,
		"y": y,
		"scale": 1.0,
	}


def _character_defaults():
	return {
		"entry": "left",
		"speed": 1.0,
	}


def _bg_motion_defaults():
	return {
		# Off until operator enables (M1 layout review must stay clean).
		"bg_motion_enabled": False,
		"bg_speed": 1.0,
		"bg_density": 1.0,
	}


def default_new_style():
	return {
		"background_id": "stage_dark_01",
		"number_visible": True,
		"bg_motion_enabled": False,
		"bg_speed": 1.0,
		"bg_density": 1.0,
		"aging": {
			"fresh_delay_seconds": DEFAULT_FRESH_DELAY,
			"aging_duration_seconds": DEFAULT_AGING_DURATION,
			"started_at": "",
			"paused": False,
			"paused_elapsed_seconds": 0,
		},
		"watermarks": {
			"h2": _watermark_defaults(0.04, 0.88),
		},
		# Legacy prefs kept for backward compat; mirrored into character when present.
		"kandura": {
			"entry": "left",
			"speed": 1.0,
			"point_ms": 1500,
		},
		"character": _character_defaults(),
		"events": _events_defaults(),
	}


def _as_bool(value, default=False):
	if value is None:
		return default
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return default


def _as_int(value, default=0, minimum=None, maximum=None):
	try:
		result = int(value)
	except (TypeError, ValueError):
		result = default
	if minimum is not None:
		result = max(minimum, result)
	if maximum is not None:
		result = min(maximum, result)
	return result


def _as_float(value, default=0.0, minimum=None, maximum=None):
	try:
		result = float(value)
	except (TypeError, ValueError):
		result = default
	if minimum is not None:
		result = max(minimum, result)
	if maximum is not None:
		result = min(maximum, result)
	return result


def _as_density(value, default=1.0):
	if isinstance(value, str):
		mapped = _DENSITY_LABELS.get(value.strip().lower())
		if mapped is not None:
			return mapped
	return _as_float(value, default, minimum=0.25, maximum=2.0)


def deep_merge(base, patch):
	"""Recursively merge dicts; patch wins for non-dict values."""
	if not isinstance(base, dict):
		base = {}
	result = deepcopy(base)
	if not isinstance(patch, dict):
		return result
	for key, value in patch.items():
		if isinstance(value, dict) and isinstance(result.get(key), dict):
			result[key] = deep_merge(result[key], value)
		else:
			result[key] = deepcopy(value)
	return result


def normalize_new_style(raw):
	defaults = default_new_style()
	data = deep_merge(defaults, raw if isinstance(raw, dict) else {})

	bg = str(data.get("background_id") or defaults["background_id"])
	if bg not in BACKGROUND_IDS:
		bg = defaults["background_id"]
	data["background_id"] = bg
	data["number_visible"] = _as_bool(data.get("number_visible"), True)

	data["bg_motion_enabled"] = _as_bool(data.get("bg_motion_enabled"), False)
	data["bg_speed"] = _as_float(data.get("bg_speed"), 1.0, minimum=0.25, maximum=3.0)
	data["bg_density"] = _as_density(data.get("bg_density"), 1.0)

	aging = data.get("aging") if isinstance(data.get("aging"), dict) else {}
	aging = deep_merge(defaults["aging"], aging)
	aging["fresh_delay_seconds"] = _as_int(
		aging.get("fresh_delay_seconds"), DEFAULT_FRESH_DELAY, minimum=0, maximum=3600
	)
	aging["aging_duration_seconds"] = _as_int(
		aging.get("aging_duration_seconds"), DEFAULT_AGING_DURATION, minimum=1, maximum=600
	)
	aging["paused"] = _as_bool(aging.get("paused"), False)
	aging["paused_elapsed_seconds"] = _as_float(
		aging.get("paused_elapsed_seconds"), 0.0, minimum=0.0
	)
	started = aging.get("started_at") or ""
	if started and not isinstance(started, str):
		started = str(started)
	aging["started_at"] = started
	data["aging"] = aging

	watermarks = data.get("watermarks") if isinstance(data.get("watermarks"), dict) else {}
	normalized_marks = {}
	for key, default_mark in defaults["watermarks"].items():
		mark = watermarks.get(key) if isinstance(watermarks.get(key), dict) else {}
		merged = deep_merge(default_mark, mark)
		merged["visible"] = _as_bool(merged.get("visible"), False)
		merged["x"] = _as_float(merged.get("x"), default_mark["x"], minimum=0.0, maximum=1.0)
		merged["y"] = _as_float(merged.get("y"), default_mark["y"], minimum=0.0, maximum=1.0)
		merged["scale"] = _as_float(merged.get("scale"), 1.0, minimum=0.2, maximum=3.0)
		normalized_marks[key] = merged
	data["watermarks"] = normalized_marks

	kandura = data.get("kandura") if isinstance(data.get("kandura"), dict) else {}
	kandura = deep_merge(defaults["kandura"], kandura)
	entry = str(kandura.get("entry") or "left").lower()
	kandura["entry"] = entry if entry in {"left", "right"} else "left"
	kandura["speed"] = _as_float(kandura.get("speed"), 1.0, minimum=0.25, maximum=3.0)
	kandura["point_ms"] = _as_int(kandura.get("point_ms"), 1500, minimum=200, maximum=10000)
	data["kandura"] = kandura

	character = data.get("character") if isinstance(data.get("character"), dict) else {}
	character = deep_merge(defaults["character"], character)
	# Prefer explicit character prefs; otherwise inherit from legacy kandura.
	char_entry = str(character.get("entry") or kandura["entry"] or "left").lower()
	character["entry"] = char_entry if char_entry in {"left", "right"} else "left"
	character["speed"] = _as_float(
		character.get("speed", kandura.get("speed")), 1.0, minimum=0.25, maximum=3.0
	)
	data["character"] = character

	events = data.get("events") if isinstance(data.get("events"), dict) else {}
	normalized_events = {}
	for key, default_value in defaults["events"].items():
		normalized_events[key] = _as_int(events.get(key), default_value, minimum=0)
	data["events"] = normalized_events
	return data


def bump_event(ns, event_key):
	events = ns.setdefault("events", _events_defaults())
	events[event_key] = _as_int(events.get(event_key), 0, minimum=0) + 1
	return events[event_key]


def plate_identity(session):
	return (
		session.plate_type or "",
		(session.code or "").strip(),
		(session.number or "").strip(),
		(session.phone_number or "").strip(),
	)


def plate_has_content(session):
	plate_type = session.plate_type or ""
	if plate_type in {"du", "etisalat"}:
		return bool((session.phone_number or "").strip())
	return bool((session.code or "").strip() or (session.number or "").strip())


def ensure_aging_started(ns, session, force_now=False):
	aging = ns.setdefault("aging", default_new_style()["aging"])
	if force_now or (plate_has_content(session) and not aging.get("started_at")):
		aging["started_at"] = timezone.now().isoformat()
		aging["paused"] = False
		aging["paused_elapsed_seconds"] = 0
	elif not plate_has_content(session):
		aging["started_at"] = ""
		aging["paused"] = False
		aging["paused_elapsed_seconds"] = 0
	return ns


def reset_aging_clock(ns, when=None):
	aging = ns.setdefault("aging", default_new_style()["aging"])
	aging["started_at"] = (when or timezone.now()).isoformat()
	aging["paused"] = False
	aging["paused_elapsed_seconds"] = 0
	return ns


def replay_aging_clock(ns, when=None):
	"""Jump to the start of the deteriorate window."""
	aging = ns.setdefault("aging", default_new_style()["aging"])
	now = when or timezone.now()
	fresh = _as_int(aging.get("fresh_delay_seconds"), DEFAULT_FRESH_DELAY, minimum=0)
	aging["started_at"] = (now - timedelta(seconds=fresh)).isoformat()
	aging["paused"] = False
	aging["paused_elapsed_seconds"] = float(fresh)
	return ns


def _apply_character_prefs(ns, prefs):
	if not isinstance(prefs, dict):
		return
	merged = normalize_new_style(deep_merge(ns, {"character": prefs, "kandura": prefs}))
	ns["character"] = merged["character"]
	# Keep legacy kandura in sync for older clients.
	ns["kandura"]["entry"] = merged["character"]["entry"]
	ns["kandura"]["speed"] = merged["character"]["speed"]
	if "point_ms" in prefs:
		ns["kandura"]["point_ms"] = merged["kandura"]["point_ms"]


def apply_new_style_patch(session, data):
	"""
	Mutate session.new_style from PATCH payload.
	Returns the normalized new_style dict (also assigned to session.new_style).
	"""
	ns = normalize_new_style(session.new_style if isinstance(session.new_style, dict) else {})

	if data.get("new_style_replace") and isinstance(data.get("new_style"), dict):
		ns = normalize_new_style(data["new_style"])
	elif isinstance(data.get("new_style"), dict):
		# Prefer prefs-only merge; strip nested events unless explicitly provided
		patch = deepcopy(data["new_style"])
		incoming_events = patch.pop("events", None)
		ns = normalize_new_style(deep_merge(ns, patch))
		if isinstance(incoming_events, dict):
			# Ignore client-supplied event counters (server owns them)
			pass

	# Direct preference shortcuts
	if "background_id" in data:
		bg = str(data["background_id"])
		if bg in BACKGROUND_IDS:
			ns["background_id"] = bg

	if "bg_motion_enabled" in data:
		ns["bg_motion_enabled"] = _as_bool(data.get("bg_motion_enabled"), False)
	if "bg_speed" in data:
		ns["bg_speed"] = _as_float(data.get("bg_speed"), ns.get("bg_speed", 1.0), minimum=0.25, maximum=3.0)
	if "bg_density" in data:
		ns["bg_density"] = _as_density(data.get("bg_density"), ns.get("bg_density", 1.0))

	if data.get("ns_show_number"):
		ns["number_visible"] = True
		bump_event(ns, "reveal_event_id")
	if data.get("ns_hide_number"):
		ns["number_visible"] = False
		bump_event(ns, "hide_event_id")
	if data.get("ns_replay_reveal"):
		ns["number_visible"] = True
		bump_event(ns, "reveal_replay_event_id")
	if data.get("ns_beam"):
		bump_event(ns, "beam_event_id")
	if data.get("ns_drop"):
		bump_event(ns, "drop_event_id")
	if data.get("ns_aging_reset"):
		reset_aging_clock(ns)
		bump_event(ns, "aging_reset_event_id")
	if data.get("ns_aging_replay"):
		replay_aging_clock(ns)
		bump_event(ns, "aging_replay_event_id")

	# Legacy kandura trigger → char_point (+ keep kandura_event_id for compat)
	if data.get("ns_kandura"):
		prefs = data.get("ns_kandura_prefs") or data.get("ns_character_prefs")
		_apply_character_prefs(ns, prefs)
		bump_event(ns, "kandura_event_id")
		bump_event(ns, "char_point_event_id")

	if data.get("ns_char_point"):
		prefs = data.get("ns_character_prefs") or data.get("ns_kandura_prefs")
		_apply_character_prefs(ns, prefs)
		bump_event(ns, "char_point_event_id")
		bump_event(ns, "kandura_event_id")

	if data.get("ns_char_yellow"):
		prefs = data.get("ns_character_prefs") or data.get("ns_kandura_prefs")
		_apply_character_prefs(ns, prefs)
		bump_event(ns, "char_yellow_event_id")

	if data.get("ns_char_red"):
		prefs = data.get("ns_character_prefs") or data.get("ns_kandura_prefs")
		_apply_character_prefs(ns, prefs)
		ns["number_visible"] = False
		bump_event(ns, "char_red_event_id")

	if data.get("ns_char_sold_stamp"):
		prefs = data.get("ns_character_prefs") or data.get("ns_kandura_prefs")
		_apply_character_prefs(ns, prefs)
		bump_event(ns, "char_sold_stamp_event_id")
		# Coordinate with global sold path when caller did not already trigger sold.
		if not data.get("trigger_sold"):
			session.sold_event_id = (session.sold_event_id or 0) + 1
			session.sold_event_at = timezone.now()
			session.sold_style = "fireworks"

	# Aging preference updates via nested new_style already merged; ensure started_at if content
	ensure_aging_started(ns, session)
	session.new_style = ns
	return ns


def parse_started_at(value):
	if not value:
		return None
	parsed = parse_datetime(str(value))
	if parsed is None:
		return None
	if timezone.is_naive(parsed):
		parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
	return parsed
