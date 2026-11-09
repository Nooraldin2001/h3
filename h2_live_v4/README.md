# H2 Auctions Live V4 — Design Sandbox

Independent frontend prototype. **Not** wired to Django (Phase 8 deferred).

## Preview

```bash
cd h2_live_v4
python -m http.server 8766
```

Open:
- Preview: http://127.0.0.1:8766/
- **Admin / control panel:** http://127.0.0.1:8766/admin.html

OBS-sized frame is fixed at **1920×1080** in CSS (scales down in smaller windows).

## Architecture (Phases 0–7)

| Layer | Files |
|-------|-------|
| Shell | `index.html`, `css/broadcast.css` |
| Plates | `js/plate-system.js`, `css/plate-system.css` |
| State bus | `js/state-controller.js` |
| FX | `js/fx-*.js`, `css/fx.css` |
| Character | `js/character-controller.js` + `assets/character/meta/*.json` |
| Debug | `js/debug-overlay.js` (`?debug=1`) |
| QA | `tools/capture_qa.py`, `refs/qa/`, `PHASE_0_7_REPORT.md` |

## Query helpers

- `?plate_type=dubai|sharjah|du|…`
- `?aging=1` — enable aging and freeze mid-deteriorate (dev QA)
- Aging controls: `admin.html` → **Plate Aging (dev)** (default OFF; independent of auction timer). See `AGING_REPORT.md`.
- `?bg=1` — enable corridor float motion
- `?debug=1` — geometry/safezone overlay

## Isolation

- Does not import production New Style CSS/JS
- Does not modify Django models/views/URLs
- Classic / TikTok / Live Control Panel untouched
