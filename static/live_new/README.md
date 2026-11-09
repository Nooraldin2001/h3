# New Style Live assets

Expected layout for OBS New Style / TikTok displays:

- `images/h3-logo.jpeg` — default header logo
- `images/watermark.jpeg` — TikTok watermark (optional for New Style)
- `plates/` — emirate and phone plate artwork referenced by `live-display-new.js`
- `v3/bg_plates/` — letter-only floating background sprites (`A.svg`…`Z.svg`, `AA.svg`…`ZZ.svg`). **No digits.**
- `v3/character/` — Gulf character WebM clips (`point`, `yellow`, `red`, `sold_stamp`). Operator-triggered only; missing files report **asset missing** (no CSS mannequin).
- `v3/sold/stamp.png` (+ `stamp.svg`) — plate-local SOLD imprint

Until character WebMs are restored, the auction UI still works; character control shows asset missing and display does not invent a production mannequin.

## OBS Browser Source checklist (New Style V3)

1. Source size: **1920×1080**, URL `/live/display-new/<token>/`
2. Background Motion On/Off + Speed/Density — letter plates drift behind stage
3. Hide/Show/Replay number — full-string cinematic reveal; reload keeps visibility (no re-play)
4. Aging: 50s fresh + 10s continuous deteriorate; freeze final; Reset / Replay / plate change
5. Light beam, number drop (visual-only unless clear checkbox)
6. Character: Point / Yellow / Red / SOLD Stamp — mutual exclusion via `characterBusy`
7. SOLD / SOLD Stamp — plate-local imprint + gold fireworks behind plate; timer/bid intact
8. Branding: H2 watermark only (no Sun Mix)
