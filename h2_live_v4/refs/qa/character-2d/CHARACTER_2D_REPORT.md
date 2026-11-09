# Temporary 2D Character Interaction — Report

## Result
`PASS` at 1920×1080 and 1280×720 (`refs/qa/character-2d/report.json`).

## Assets used (honest)

| Action | File | Source | Notes |
|--------|------|--------|-------|
| POINT | `assets/character/prototype_2d/point.png` | `point_source.gif` frame 4 | Full-body point, transparent PNG |
| YELLOW | `assets/character/prototype_2d/yellow.png` | `point_source.gif` frame 5 | Same identity/framing as POINT |
| RED | `assets/character/prototype_2d/red.png` | `red card.gif` frame 5 | Only available red-card sprite |

### Missing / gaps
- **No matching full-body red card** in the same 440×441 point/yellow capture — red uses a taller 271×724 crop of the same Gulf presenter wardrobe.
- **No dedicated sold-stamp 2D sprite** for this temporary pack (`sold_stamp` remains marked missing).
- Storyboard collages were **not** used as sprites.
- WebMs remain unusable for alpha (unchanged); this pack does **not** overwrite production WebM paths.

## Behavior
- Bottom-center 2D slide enter (~650 ms ease-out) → hold (~1.5 s) → exit (~500 ms).
- Not labeled as a production walk.
- Yellow: plate-shell yellow rim + plate-only shake; number stays visible; transform resets.
- Red: plate-shell red rim; digits hidden only; data preserved; Show Number restores all digits.
- No autoplay on load; overlapping plays blocked while busy.

## Files modified
- `assets/character/prototype_2d/*` (new)
- `js/character-prototype-media.js`
- `js/character-controller.js`
- `css/fx.css` (character layer sizing)
- `tools/capture_character_2d_qa.py`
- `tools/record_character_2d_demo.py`

## Artifacts
- Screenshots: `fullhd-*.png`, `hd720-*.png`
- Demo: `character-2d-demo.mp4`
