# New Style Live assets

Expected layout for OBS New Style / TikTok displays:

- `images/h3-logo.jpeg` — default header logo
- `images/watermark.jpeg` — TikTok watermark (optional for New Style)
- `plates/` — emirate and phone plate artwork referenced by `live-display-new.js`
- `kandura/walker.webm` — optional alpha WebM for Kandura Walker (CSS fallback used if missing)
- `aging/` — optional overlay art pack for photoreal aging layers

Until these files are restored, the auction UI still works; plate images and optional video effects may 404.

## OBS Browser Source checklist (New Style V2)

1. Source size: **1920×1080**, URL `/live/display-new/<token>/`
2. Swap background from New control — display updates within ~1s without reload
3. Hide/Show/Replay number — full number appears at once; reload keeps visibility
4. Aging: leave active plate 50s fresh, then 10s continuous deteriorate; freeze after 60s; Reset / Replay / plate change
5. Refresh OBS mid-aging (~55s) — reconstructs continuous progress
6. Light beam, number drop, Kandura walker, H2/Sun Mix watermarks
7. SOLD fireworks — plate/price/timer remain; Classic/TikTok gavel unchanged
8. Missing `kandura/walker.webm` falls back to CSS figure
