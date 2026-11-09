# SOLD Fireworks Visibility Fix

## Result: PASS

Real admin **SOLD + Fireworks** button produces obviously visible golden fireworks in the rendered preview. Automated visibility QA: `all_ok: true`.

## Root cause

Fireworks were drawn on `#plate-fw` **inside** `#plate`, stacked **behind** opaque `.plate-shell` plate artwork (and confined under `.stack`).

- JS particle counts / `getImageData` on that canvas could be > 0.
- On screen, almost all particles were covered by the white plate — effect looked invisible.

Prior QA marked `all_ok` from canvas lit-pixel counts, not from visible stage pixels outside the plate.

## Fix

1. Added full-stage canvas `#stage-fw` (1920×1080) as a direct child of `#stage`.
2. Layer order: studio bg → ambient plates → **fireworks (z=3)** → stack/plate/timer/bid (z=8) → character → brand.
3. Rewrote `js/fx-sold.js`: rockets from podium L/R → bursts in upper-left/right studio; time-based decay + hard cleanup (~5–7s).
4. Removed plate-local `#plate-fw` usage.
5. SOLD path still fires immediately via `trigger_sold` / `btn-sold` (no character wait).

## Files modified

- `index.html` — `#stage-fw`
- `css/fx.css` — `.stage-fw` layering
- `js/fx-sold.js` — stage-space rockets/bursts + cleanup
- `tools/capture_sold_visibility_qa.py` — real button + screenshot zone diffs
- `tools/record_sold_visibility_demo.py` — demo MP4

## Numerical screenshot diffs (automation)

| Case | gold_delta (zones) | changed_left | changed_right | mean_abs_diff |
|------|-------------------:|-------------:|--------------:|--------------:|
| admin-1920 | 96728 | 131163 | 140832 | 45.2 |
| admin-1600 | 62462 | (visible) | (visible) | — |
| direct-1280 | 159656 | 176704 | 172025 | 37.9 |

Browser real button (preview half): gold_delta **30533**, mean_abs_diff **28.8**, changed_px **154684**.

## Artifacts

- Before / peak / clean (automation): `refs/qa/sold-fireworks-visibility/admin-1920-*.png`
- Real browser: `browser-00-before.png`, `browser-25-peak.png`, `browser-60-clean.png`
- Demo MP4: `sold-fireworks-visible-demo.mp4`
- Machine report: `report.json`

## Operator confirmation

Clicking admin **SOLD + Fireworks** (`#btn-sold` → `trigger_sold` postMessage → `sold` event → `H2V4SoldFx.triggerSoldLocal`) starts visible fireworks immediately. Cleanup restores a clean stage (SOLD imprint may remain). Timer / bid / number unchanged.
