# Geometry & Timer Repair QA

## Timer freeze — root cause

V4 painted `timer_remaining_seconds` **once** from the mock state. There was no `timer_ends_at` clock and no tick loop, so the display stayed at `01:00`.

**Fix:** `js/timer-controller.js` — authoritative `timer_ends_at`, single 200ms interval, Start/Pause/Resume/Reset, sessionStorage restore, independent of aging. Admin controls on `admin.html`.

## Debug overlay mismatch — root cause

Preview `transform: scale(...)` was applied on `#stage`. Debug boxes used viewport `getBoundingClientRect()` deltas as if they were unscaled stage CSS pixels, so overlays drifted when the window was not 1920×1080.

**Fix:**
- Scale `.stage-scaler` instead of `#stage`
- `js/geometry.js` converts viewport → stage-local via `visualWidth / offsetWidth`
- Debug overlay + FX canvases use stage-local / layout sizes

## Results

See `report.json` — suite `"ok": true`.

Screenshots in this folder: 1920/1280 debug, Fujairah, du phone, SOLD, aging.
