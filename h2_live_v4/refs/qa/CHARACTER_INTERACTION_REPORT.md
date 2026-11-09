# H2 Auctions V4 — Character & Plate Interaction Report

**Date:** 2026-11-09  
**Branch:** `feature/h2-live-v4`  
**Scope:** `h2_live_v4/` only  
**Status:** **Prototype complete for testing — NOT production-ready**

---

## 1. Modified / added files

| File | Change |
|------|--------|
| `js/character-prototype-media.js` | **New** — quarantined PNG/GIF catalog + estimated cues + stage anchors |
| `js/character-controller.js` | Timeline state machine, bottom-center path, frame/GIF player |
| `js/fx-beam-drop.js` | Plate-local rim fit to shell for yellow/red |
| `js/broadcast.js` | Character boot, direct admin messages, lot-change reset |
| `js/admin.js` / `admin.html` | Enter / Exit / Reset + live character HUD (outside OBS) |
| `js/debug-overlay.js` | Anchors, path, rim, shell, sprite boxes |
| `js/character-acceptance.js` | Prototype adapter note; measured paths still SKIP |
| `css/fx.css` | Bottom-center character layer; SVG rim frames; yellow shake |
| `index.html` | `#character-sprite` + prototype media script |
| `tools/capture_character_interaction_qa.py` | **New** automated visual QA |
| `refs/qa/character-interaction/*` | Screenshots + `qa-report.json` |

No Django / Classic / TikTok / Phase 8 / production asset overwrites.

---

## 2. Controller design

```
IDLE → ENTERING → POSITIONING → ACTING → EXITING → IDLE
         └──────── hold (Enter) ────────┘
```

- Single busy lock; conflicting plays return `{ ok:false, reason:"busy" }`.
- `Enter` → walk to stop and **hold**.
- `Point` / `Yellow` / `Red` / `SOLD` → enter (unless holding) → act → exit.
- `Exit` / `Reset` / lot change → cleanup.
- No autoplay on load.

**Media policy:** Prefer PNG sequences / GIF mattes from the preview pack. **WebM not composited** (tagged `alpha_mode` but decode opaque — see `character-asset-audit.md`).

---

## 3. Geometry (stage CSS px @ 1920×1080)

| Anchor | x | y | Notes |
|--------|--:|--:|------|
| Entry feet | 960 | 1200 | Below stage |
| Stop feet | 960 | 1065 | Floor / podium band |
| Exit feet | 960 | 1240 | Below stage |
| Gesture target | 960 | 520 | Plate center (approx) |
| Display box | 400×540 | | Aspect preserved; `object-position: bottom` |

Live boxes for logo / timer / shell / number / bid are measured via `H2V4Geom.elementStageBox` (scale-safe). Rim is fitted to `#plate-shell` on each card cue.

---

## 4. Action timing (all **estimated**)

| Action | Enter | Gesture / contact | Act length | Status |
|--------|------:|------------------:|-----------:|--------|
| Enter | 1600 ms | — | hold | estimated |
| Point | 1600 + 800 | gesture ~400 | exit after | estimated |
| Yellow | 1600 + 1600 | gesture ~700 → rim + plate shake | exit | estimated |
| Red | 1600 + 1440 | gesture ~600 → rim + hide glyphs | exit | estimated |
| SOLD | 1600 + 1440 | contact ~800 → imprint + FW + shake | exit | estimated |

**Never labeled `measured`.**

---

## 5. Media & transparency audit (implementation-time)

| Source | Used? | Alpha |
|--------|-------|-------|
| PNG frames (entry/exit/point/yellow) | **Yes** | True RGBA |
| Root `red card.gif` / `sold.gif` | **Yes** | GIF matte |
| Preview `.webm` | **No** (disabled) | Opaque when decoded |
| Starter SVG yellow/red frames | **Yes** (rim) | Vector |

Perspective caveat: entry footage is **front-facing** — interim approximation only, not a rear podium approach.

---

## 6. Functional vs prototype matrix

| Feature | Status |
|---------|--------|
| Bottom-center entry/exit path | Functional (prototype motion) |
| Point action | Functional (short 4-frame; aim not guaranteed) |
| Yellow rim + **plate-only** shake | Functional |
| Red rim + complete digit hide (no blur/censor) | Functional |
| Show Number restore | Functional |
| SOLD imprint plate-local + fireworks | Functional (estimated contact) |
| Dev HUD outside stage | Functional |
| `?debug=1` anchors/path/rim | Functional |
| Production alpha WebM + measured cues | **Blocked / missing** |
| Genuine rear-view walk | **Blocked / missing** |

---

## 7. QA results

Automated suite: `refs/qa/character-interaction/qa-report.json` → **`all_ok: true`**

Coverage includes:

- Idle invisible
- Yellow gesture / settle
- Red hide + Show Number restore (`7777` preserved)
- Point / SOLD
- Busy rejection
- Reset
- Red hide on abu_dhabi, fujairah, du, etisalat
- 1280×720 smoke

Screenshots: `refs/qa/character-interaction/01-*.png` … `10-*.png`

---

## 8. Outstanding asset blockers

1. True VP9 **alpha** WebMs for `point` / `yellow` / `red` / `sold_stamp`.
2. Authored **rear/¾ entry** and real **exit** (not reversed front walk).
3. Locked identity across walk vs card close-ups.
4. Frame-accurate **measured** `gesture_ms` / `contact_ms` + UV anchors.
5. Higher resolution (≥1080h) masters.

Until then: keep `ASSET_STATUS = prototype_estimated_cues_not_production`.

---

## 9. How to exercise locally

1. Serve `h2_live_v4` (e.g. port 8766).
2. Open `admin.html` (controls stay outside the OBS iframe stage).
3. Use **Enter / Point / Yellow Card / Red Card / SOLD / Exit / Reset**.
4. Optional: `index.html?debug=1` for geometry overlays.

**STOP.** No commit / push / deploy. Not production-ready.
