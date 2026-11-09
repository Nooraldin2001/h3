# H2 Auctions Live V4 — Design Sandbox

Independent frontend prototype. **Not** wired to Django.

## Preview

```bash
cd h2_live_v4
python -m http.server 8766
```

Open: http://127.0.0.1:8766/

OBS-sized frame is fixed at **1920×1080** in CSS.

## Scope (this step)

Base screen only:

- H2 AUCTIONS branding
- Studio stage background
- Timer above plate
- UAE Dubai plate (mock AA / 7777)
- Current bid below plate

No character, floating plates, cards, aging, SOLD, beams, or drops.

## Isolation

- Does not import `static/css/live-display-new.css` or `static/js/live-display-new.js`
- Does not modify Django models/views/URLs
- Existing New Style / Classic / TikTok remain untouched
