# 2D Character +30% Scale QA

## Change
Shared `CHARACTER_SCALE = 1.3` in `js/character-prototype-media.js`.

| | Before | After |
|--|--:|--:|
| Display box | 300×430 | **390×559** |
| stopFeet.y | 1095 | 1105 |
| Box height ratio | 1.0 | **1.30** |

All Point / Yellow / Red poses use the same `ANCHORS.display` (no per-pose sizes). Aspect ratio preserved via `object-fit: contain`.

## Clearance (1920 hold)
- Logo / timer: no overlap
- Plate number & bid: geometrically near character top, but character `z-index:7` is under `.stack` (`z-index:8`) so digits/bid stay readable
- Yellow rim + Red hide unchanged

## Artifacts
- Before: `before-1920-*.png`, `before-1280-*.png`, `before-metrics.json`
- After: `after-1920-*.png`, `after-1280-*.png`, `after-metrics.json`
