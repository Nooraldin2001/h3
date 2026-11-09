# H2 V4 Page Separation — Regression Report

- Passed: **26/26**
- Admin URL: `http://127.0.0.1:8766/control.html`
- Broadcast URL: `http://127.0.0.1:8766/index.html`
- Sync: BroadcastChannel `h2-v4-sandbox-sync` + localStorage snapshot

## OBS limitation

Sandbox sync (BroadcastChannel + localStorage) only works inside the **same browser profile/origin**.
OBS Browser Source typically uses a separate Chromium process and **will not** receive these messages.
Do not claim production OBS sync from same-browser tab tests. Production path: Django session/API (unchanged).

## Checklist

- [PASS] visual_vs_baseline: {"ok": true, "changed_px": 0, "pct": 0.0, "max_delta": 3}
- [PASS] broadcast_has_no_admin_buttons: 
- [PASS] plate_bid_sync: {"plate": "sharjah", "num": "5555", "price": "999000"}
- [PASS] live_text_lines: TEST LINE ONE|TEST LINE TWO
- [PASS] timer_start: rem=43 active=True
- [PASS] timer_pause: 
- [PASS] timer_resume: 
- [PASS] timer_reset: 
- [PASS] hide_number: 
- [PASS] show_number: 
- [PASS] number_drop: drop_event_id=1
- [PASS] yellow_card: id=1
- [PASS] red_card: id=1
- [PASS] point_character: id=1
- [PASS] sold_event: sold#1
- [PASS] sold_fireworks_pixels: 
- [PASS] aging_running: {"asset_tier": "interim", "completed": false, "elapsed_ms": 1396, "elapsed_seconds": 1.396, "enabled": true, "paused": false, "progress": 0.023266666666666668, "running": true, "stage": "pristine", "stage_label": "Pristine", "stage_local": 0.02792, "total_duration_seconds": 60}
- [PASS] aging_independent_of_timer: timer_rem=45
- [PASS] aging_reset: {"asset_tier": "interim", "completed": false, "elapsed_ms": 0, "elapsed_seconds": 0, "enabled": true, "paused": false, "progress": 0, "running": false, "stage": "pristine", "stage_label": "Pristine", "stage_local": 0, "total_duration_seconds": 60}
- [PASS] ambient_on: 
- [PASS] ambient_stop: 
- [PASS] refresh_keeps_lot: 
- [PASS] refresh_no_sold_replay: sold=1 fw=False
- [PASS] refresh_keeps_live_text: 
- [PASS] control_refresh_hydrate: code=1
- [PASS] no_console_errors: {"b": [], "c": []}

## Artifacts

- `baseline-broadcast-1920x1080.png`
- `final-broadcast-vs-baseline-1920x1080.png`
- `final-broadcast-clean-1920x1080.png`
- `admin-control-panel.png`
- `admin-control-final.png`
- `broadcast-sold-1920x1080.png`
