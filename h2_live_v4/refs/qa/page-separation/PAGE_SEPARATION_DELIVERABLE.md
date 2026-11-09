# H2 Auctions V4 — Admin / Broadcast Page Separation

**Status:** Complete (sandbox only). No Django / Classic / TikTok / Phase 8 changes. No commit.

## URLs (local preview server)

| Role | URL |
|------|-----|
| **Admin Live Control Panel** | http://127.0.0.1:8766/control.html |
| **H2 Live Broadcast Display** | http://127.0.0.1:8766/index.html |
| Iframe combo (legacy sandbox) | http://127.0.0.1:8766/admin.html |

## Files added or modified

### Added
- `h2_live_v4/control.html` — standalone Admin Control Panel (no iframe, no broadcast chrome)
- `h2_live_v4/js/sync-bus.js` — BroadcastChannel + localStorage snapshot adapter
- `h2_live_v4/_backup_separation_20261109_193721/` — reversible backup of pre-edit files
- `h2_live_v4/tools/capture_separation_baseline.py`
- `h2_live_v4/tools/qa_page_separation.py`
- `h2_live_v4/tools/record_separation_demo.py`
- `h2_live_v4/refs/qa/page-separation/*` — baseline, finals, report, demo

### Modified (minimal)
- `h2_live_v4/index.html` — load `sync-bus.js` (broadcast remains control-free)
- `h2_live_v4/js/broadcast.js` — hydrate snapshot; SyncBus commands when top-level; keep postMessage for iframe
- `h2_live_v4/js/admin.js` — dual mode: iframe `admin.html` vs standalone `control.html`
- `h2_live_v4/js/state-controller.js` — shared live-text persistence; Start+duration order fix
- `h2_live_v4/js/timer-controller.js` — shared timer persistence; keep hydrated ends_at across tabs
- `h2_live_v4/admin.html` — links to separate control/broadcast
- `h2_live_v4/css/admin.css` — standalone layout only (no broadcast visual changes)

## State synchronization mechanism

**Sandbox adapter:** `H2V4SyncBus`

1. **BroadcastChannel** name `h2-v4-sandbox-sync` for live commands (patch, character, agingSeek, getStatus).
2. **localStorage snapshot** `h2v4_sandbox_snap_v1` (+ shared timer / live-text keys) for reopen/restore.
3. **Event counters** restored + `seedFromState()` so refresh does **not** replay SOLD / drop / yellow / red / beam.
4. **Timer** uses authoritative `timer_ends_at` — reload recomputes remaining; does not restart.
5. **Aging** restored independently from snapshot; auction timer remains separate.
6. **Iframe path preserved:** `admin.html` still uses `postMessage` into embedded `index.html` (embedded broadcast ignores SyncBus commands to avoid double-fire).

## Baseline vs final visual comparison

- Baseline: `refs/qa/page-separation/baseline-broadcast-1920x1080.png`
- Final match: `refs/qa/page-separation/final-broadcast-vs-baseline-1920x1080.png`
- Pixel diff: **0 changed px** (max channel delta 3) at threshold 12 — approved studio composition unchanged.

## Regression checklist

Full automated Admin-UI → Broadcast suite: **26/26 PASS**  
See `SEPARATION_REPORT.md`.

Covered: plate/bid, timer start/pause/resume/reset, live text ×2, show/hide, drop, yellow/red/point, SOLD+fireworks, aging independent, ambient on/off, display refresh (no one-shot replay), control refresh hydrate, no console errors, broadcast has no admin buttons, 1920×1080 + 1280×720 captures.

## Screenshots / video

- Admin: `admin-control-panel.png` / `admin-control-final.png`
- Clean Broadcast: `final-broadcast-clean-1920x1080.png`
- Demo: `admin-controls-broadcast-demo.mp4` (when ffmpeg available)

## Missing / incomplete features

None removed. Not invented:
- Authenticated production Django Admin sync (out of scope; must remain Django session/API).
- Cross-device / cross-process networking.

## OBS synchronization limitations

**Verified limitation (sandbox):** BroadcastChannel and localStorage only work within the **same browser profile and origin**.

OBS Browser Source commonly runs in a **separate Chromium process** and **will not** receive sandbox SyncBus messages or share this localStorage.

Same-browser tab tests must **not** be claimed as production OBS synchronization.

**Production path (unchanged):** reuse existing Django session/API infrastructure. This task did not modify Django.
