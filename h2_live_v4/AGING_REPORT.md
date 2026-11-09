# H2 Live V4 — Plate Aging & Breaking Report

Sandbox only (`h2_live_v4/`). No Django / Classic / TikTok / Phase 8 changes. Not committed.

## Files changed

| File | Role |
|------|------|
| `js/fx-aging.js` | Independent elapsed-time aging clock + canvas material FX (wear, branching cracks, gravity fragments) |
| `js/state-controller.js` | Default aging **OFF**; control aliases (`aging_enable/disable/start/pause/resume/reset`, duration) |
| `js/broadcast.js` | Plate-change hook; admin aging status/seek messages; `?aging=1` seeks mid-stage (does not auto-run forever) |
| `js/admin.js` / `admin.html` / `css/admin.css` | Dev Aging Control Panel + live HUD (outside OBS stage) |
| `index.html` | Aging surface canvas (replaces interim SVG crack paths) |
| `css/fx.css` | Surface/fragment layering; bid above falling shards |
| `tools/aging_qa.py` | Automated control + stage QA |
| `tools/record_aging_demo.py` | Stage-seek demo strip / gif-mp4 |
| `refs/qa/aging/*` | Screenshots + `report.json` |

## Control interface

**Location:** `admin.html` → sidebar section **“Plate Aging (dev)”**  
This panel lives beside the preview iframe — **never inside the 1920×1080 `#stage`**, so it cannot appear in OBS.

Also operable from the preview console / patch bus:

- `H2V4State.patch({ aging_enable: true })`
- `H2V4State.patch({ aging_start: true })`
- `H2V4State.patch({ aging_pause: true })` / `{ aging_resume: true }`
- `H2V4State.patch({ aging_reset: true })` / `{ aging_disable: true }`
- `H2V4State.patch({ aging_duration_seconds: 30 })`
- `H2V4AgingFx.seekProgress(0.9, { freeze: true })` (QA)

## How to operate

1. Open `http://127.0.0.1:8766/admin.html` (serve `h2_live_v4/` with `python -m http.server 8766`).
2. Set **Master = ON**, choose duration (15 / 30 / 60 / 120 or custom), **Apply duration**.
3. **Start** — normalized timeline begins at pristine.
4. **Pause** freezes elapsed time + fragments; **Resume** continues without restart.
5. **Reset** → pristine (keeps enabled); **Disable → pristine** turns the effect off.
6. Optional: **Seek stage** for instant QA frames.

Default load state: **Aging OFF**, plate pristine. Auction countdown is untouched.

## Timer behavior

- Single **elapsed-ms** clock (`started_at` + `elapsed_ms` accumulator).
- Pause stores elapsed and clears `started_at` (no drift while paused).
- Progress = `elapsed / total_duration` (frame-rate independent).
- Stages scale with duration using the **60s reference proportions**:
  - 0–50/60 pristine  
  - 50–53/60 weathering  
  - 53–56/60 stress / fine cracks  
  - 56–59/60 crack network / chips  
  - 59–60/60 final break  
  - ≥1.0 frozen complete until reset/disable  
- Idempotent start/pause/resume/reset/disable.
- Plate/lot change rebuilds crack geometry via `onPlateChange()` without forcing a full timeline restart.
- **Not** tied to `H2V4Timer` / `timer_ends_at`.

## Visual improvements

- Plate-local **canvas surface** (clipped in shell): worn paint mottling, gloss loss, scratches, edge oxidation.
- Deterministic **branching crack trees** from stress anchors (gap + edge highlight — not flat black SVG strokes alone).
- **Fragments** spawn at crack anchors, sample plate-art color, use gravity / rotation / acceleration; free layer may leave the shell.
- Subtle shell deform + finale shake; completion freezes final look.
- Still labeled **`ASSET_TIER: interim`** — procedural, not authored production masks.

## QA results

Command: `python tools/aging_qa.py` → `refs/qa/aging/report.json` — **ok: true**

Verified:

- Default OFF  
- Enable + Start; Pause / Resume (elapsed frozen while paused)  
- Reset + Disable → pristine  
- Durations 15 / 30 / 60 / 120 with proportional stage mapping  
- Stage screenshots (pristine → weather → stress → fragment → break → complete)  
- Completion freeze  
- Plate change during aging (Fujairah)  
- Auction timer independence  
- 1920×1080 and scaled 1280×720  

Artifacts: `refs/qa/aging/1920-*.png`, `1280-*.png`, demo strip/frames from `record_aging_demo.py`.

## Remaining gaps vs production-grade destruction

- No authored wear textures, crack masks, or break meshes.
- Shards are tinted rectangles, not photographic plate pieces.
- Multiply canvas veil is an approximation of paint aging, not PBR.
- Lighting/shadow response is illustrative only.
- Do **not** treat this as broadcast-finished material destruction until real assets are supplied.
