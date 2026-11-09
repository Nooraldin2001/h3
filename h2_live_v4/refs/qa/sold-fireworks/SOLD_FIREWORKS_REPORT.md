# SOLD Cinematic Fireworks — Report

## Result
`all_ok` at 1920×1080 and 1280×720.

## Changes
- Rewrote `js/fx-sold.js`: layered golden bursts (fountain / radial / ring / arc), trails, gravity, ~5.2s auto-end, generation-based cancel/replay.
- Expanded `#plate-fw` beyond the plate box so bursts bloom past the shell without clipping.
- Studio gold wash via `#stage.sold-celebration` + plate glow (brief, then clears).
- `broadcast.js`: SOLD always triggers fireworks immediately (no character busy / WebM wait). Optional `delayMs` remains for future measured stamp sync.
- SOLD does not touch timer, bid, number, or aging.

## Artifacts
- Screenshots: `refs/qa/sold-fireworks/fullhd-*.png`, `hd720-*.png`
- Demo: `refs/qa/sold-fireworks/sold-fireworks-demo.mp4`
- Machine QA: `refs/qa/sold-fireworks/SOLD_FIREWORKS_QA.md`
