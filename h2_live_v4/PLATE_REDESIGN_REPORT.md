# H2 Live V4 — UAE Plate Redesign Report

**Date:** 2026-11-10  
**Branch:** `main`  
**Scope:** V4 plate rendering only (`static/live_v4` + sandbox `h2_live_v4`). No Django models/routes, Classic, TikTok, New Style, deploy, or commit.

---

## 1. Root cause of extra white edges

Three stacked causes:

1. **Padded source canvases** — Sharjah (`1413×397`, aspect 3.559) and Dubai Classic (`1290×306`, aspect 4.216) included large near-white margins outside the painted black frame. With `object-fit` filling a mismatched shell aspect, those margins rendered as a white mat around the real plate.
2. **Aspect mismatch** — Shell aspect ratios lagged the artwork (especially Sharjah), so letterboxing/contain behavior exaggerated the white mat.
3. **CSS corner clip** — Soft `border-radius` on `.plate-shell` cut through the painted black stroke and exposed white plate body at the corners. An experimental art overscale also clipped the black frame; both were removed.

**Fix:** Lossless padding trim → update `PLATE_ASPECT` → square shell clip (`border-radius: 0`) → `object-fit: fill` with matched aspect → transparent shell (no white card layer).

---

## 2. Source assets per plate type

| Type | Asset | Notes |
|---|---|---|
| `abudhabi` | `assets/plates/abudhabi.jpg` | New Style master (tight-trimmed) |
| `dubai` | `assets/plates/dubai.jpg` | New Style master (tight-trimmed) |
| `dubai_yellow` | `assets/plates/dubai_classic.jpg` | Trimmed padded Classic yellow blank |
| `sharjah` | `assets/plates/sharjah.jpg` | Trimmed (3.559 → ~4.616 aspect) |
| `ajman` | `assets/plates/ajman.jpg` | Tight-trimmed |
| `rasalkhimma` | `assets/plates/rasalkhimma.jpg` | Already clean |
| `ummalquain` | `assets/plates/ummalquain.jpg` | Tight-trimmed |
| `fujairah` | `assets/plates/fujairah.jpg` | Tight-trimmed |
| `du` | `assets/plates/du.png` | **Classic RGBA** phone frame (replaces Dubai-collision PNG) |
| `etisalat` | `assets/plates/etisalat.png` | **Classic RGBA** phone frame |

No invented official graphics. Emirate artwork remains the verified New Style / Classic masters.

---

## 3. Number font & styling

| Property | Before | After |
|---|---|---|
| Family | generic / inherited | `"Arial Black", "Arial Narrow", Arial, Helvetica, sans-serif` |
| Weight | ~800 | `900` |
| Tracking | loose | `-0.04em` numbers / `-0.02em` codes |
| Rendering | default | `geometricPrecision` + antialiased |
| Shadows / gradients | none (kept) | none — digits stay flat/integrated |
| Size | fixed per type | digit-count scaling (`scaledFont`) for 1–8+ chars |
| Abu Dhabi code | black | white on red panel (preserved) |

Dynamic text overlays retained (not baked into images).

---

## 4. Files modified

**Assets (trimmed / corrected):**
- `static/live_v4/assets/plates/{sharjah,dubai,dubai_classic,abudhabi,ajman,fujairah,ummalquain}.jpg`
- `static/live_v4/assets/plates/{du,etisalat}.png` (+ jpeg copies)
- Mirrored under `h2_live_v4/assets/plates/`

**Code / CSS:**
- `static/live_v4/js/plate-system.js` (+ sandbox mirror)
- `static/live_v4/css/plate-system.css`
- `static/live_v4/css/fx.css` (rim CSS border, radius)
- `static/live_v4/js/character-controller.js` (rim pad 10→4)
- `static/live_v4/js/fx-beam-drop.js` (rim pad 10→4)

**Tools / evidence (untracked helpers):**
- `static/live_v4/tools/trim_plate_padding.py`, `capture_plate_qa.py`, …
- `h2_live_v4/refs/qa/plate-redesign/*` (screenshots + metrics)

---

## 5. Geometry adjustments

- Updated `PLATE_ASPECT` to measured trimmed sizes (e.g. Sharjah **4.616**, Dubai **4.764**, Dubai Yellow **4.395**).
- Remapped Sharjah / Dubai Yellow overlay `%` boxes from New Style coordinates after padding removal.
- Slight Dubai Yellow code-box tweak so dynamic code sits in the yellow well above the CLASSIC watermark.
- Yellow/Red rim `fitRim` pad reduced **10 → 4** so frames hug the physical shell.
- Stamp / aging / drop still keyed off shell + geometry registry (unchanged API).

---

## 6. Visual evidence

Folder: `h2_live_v4/refs/qa/plate-redesign/`

| Shot | Purpose |
|---|---|
| `after-{type}-crop.png` | Close-up per supported type |
| `after-dubai-7-crop.png` / `after-dubai-12345-crop.png` | Short / long digit scaling |
| `after-broadcast-dubai-1920.png` | Full 1920×1080 |
| `after-broadcast-dubai-1280.png` | 1280×720 |
| `geometry-debug-dubai.png` | Shell / code / number / stamp / yellow rim |
| `after-dubai-yellow-rim.png` | Yellow card frame |
| `after-dubai-red-card.png` | Red card (digits hidden) |
| `after-dubai-sold-stamp.png` | SOLD stamp target |
| `plate-metrics-after.json` | Measured aspect / font / art src |

---

## 7. Regression checks

| Check | Result |
|---|---|
| All 8 emirates + du + etisalat render | Pass (12 capture cases) |
| Dynamic code/number/phone update via `H2V4State.patch` | Pass |
| No fake white shell background | Pass (`shellBg: rgba(0,0,0,0)`) |
| Red card hides digits, keeps code + artwork | Pass |
| Yellow rim follows shell | Pass (tighter pad) |
| SOLD stamp uses `getStampTarget` | Pass |
| Broadcast chrome (logo / timer / bid) untouched | Pass |
| Digit-count font scaling | Pass (7→94px, 7777→79px, 12345→71px) |

Number-drop / aging / character not re-animated in every headless pass; geometry inputs they consume (shell bounds + registry) were preserved and rim fit updated.

---

## 8. Missing authentic assets

- No dedicated UAE embossed plate typeface is in-repo (only Poppins / Noto Arabic). Digits use system Arial Black as the best available non-invented stand-in.
- Emirate JPG masters are modest resolution (~1k wide); they are **not** upscaled. Broadcast sharpness is limited by source masters.
- `live_new` mapped `du.png` / `etisalat.png` were Dubai duplicates historically; V4 now uses Classic RGBA frames. New Style production files were **not** modified (per safety rules).

---

## 9. Remaining realism limitations

- Flat 2D artwork — no true emboss / metal BRDF without new photographed masters.
- DUBAI / emirate wordmarks stay as raster in the JPG (soft at 1080p).
- CSS rim is a clean border+glow, not a physical warning sleeve.
- Phone frames are marketing cards, not metal plates (by product design).
- Authentic stamped fonts would require licensed plate typefaces not present in the project.

---

## Definition of Done status

| Criterion | Status |
|---|---|
| No unwanted white padding mat | **Met** (trim + aspect + no white shell; painted frame preserved) |
| Resembles real UAE plate artwork | **Improved** (correct masters + proportions; still 2D) |
| Digits authentic & positioned | **Improved** (weight/tracking/scaling + remapped boxes) |
| All supported types functional | **Met** |
| Plate-relative FX aligned | **Met** (rim pad + registry) |
| Admin→Broadcast sync untouched | **Met** (no sync rewrite) |
| No V4 feature rewrite / no deploy | **Met** |
