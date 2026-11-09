# H2 Auctions V4 — Asset Stickers Inventory

**Date:** 2026-11-09  
**Scope:** Read-only inventory of `h2_live_v4/refs/qa/assest_stickers/`  
**Note:** Folder name is spelled `assest_stickers` (as supplied). No assets were modified, renamed, moved, or deleted.

---

## Executive summary

| Finding | Result |
|--------|--------|
| Files in folder | **12** (all under `H2_Character_Starter_Pack/`) |
| Real transparent character WebM videos | **None** (zero `.webm` anywhere under `h2_live_v4/`) |
| Production-ready overlays in this pack | **4 SVGs** (yellow/red cards + yellow/red plate frames) |
| PNG sheets | **3** — all **reference / storyboard collages**, not on-stage sprites |
| Metadata | **4 JSON** stubs with `status: "missing"` for required WebMs |
| V4 character runtime | Already expects `./assets/character/{point,yellow,red,sold_stamp}.webm` — files **absent** |

**Verdict:** This pack is a **starter / briefing kit** (identity refs + storyboards + flat SVG overlays + empty cue metadata). It is **not** a complete character animation delivery. Do not put the PNG collages on the broadcast stage.

---

## 1. Complete file list (format / size / transparency)

### 1.1 Tree

```
assest_stickers/
└── H2_Character_Starter_Pack/
    ├── README.md
    ├── metadata/
    │   ├── point.json
    │   ├── yellow.json
    │   ├── red.json
    │   └── sold_stamp.json
    ├── overlays/
    │   ├── yellow_card.svg
    │   ├── red_card.svg
    │   ├── yellow_frame.svg
    │   └── red_frame.svg
    ├── references/
    │   └── presenter_identity_pose_sheet.png
    └── storyboards/
        ├── entry_yellow_red_sold_reference.png
        └── motion_sequence_reference.png
```

### 1.2 Measured properties

| Relative path | Format | Dimensions | Mode / alpha | Bytes | Notes |
|---|---|---|---|---|---|
| `…/README.md` | Markdown | — | — | 1,710 | Pack rules; correctly marks WebMs as missing |
| `…/metadata/point.json` | JSON | — | — | 544 | `status: missing` → `point.webm` |
| `…/metadata/yellow.json` | JSON | — | — | 546 | `status: missing` → `yellow.webm` |
| `…/metadata/red.json` | JSON | — | — | 540 | `status: missing` → `red.webm` |
| `…/metadata/sold_stamp.json` | JSON | — | — | 554 | `status: missing` → `sold_stamp.webm` |
| `…/overlays/yellow_card.svg` | SVG | 420×600 (`viewBox 0 0 420 600`) | Transparent canvas | 425 | Rounded yellow card + soft highlight |
| `…/overlays/red_card.svg` | SVG | 420×600 | Transparent canvas | 425 | Same geometry as yellow; red fill |
| `…/overlays/yellow_frame.svg` | SVG | 1600×440 | Transparent (stroke-only) | 466 | Glow outline; `fill="none"` |
| `…/overlays/red_frame.svg` | SVG | 1600×440 | Transparent (stroke-only) | 466 | Same geometry as yellow frame; red stroke |
| `…/references/presenter_identity_pose_sheet.png` | **PNG** | **1774×887** | **RGB — no alpha** | 1,578,288 | Near-white opaque sheet; poses look cut-out but file is **not** transparent |
| `…/storyboards/entry_yellow_red_sold_reference.png` | PNG | 1672×941 | RGBA | 2,547,797 | Alpha extrema **149–252** (no true holes); dark gray collage BG |
| `…/storyboards/motion_sequence_reference.png` | PNG | 1672×941 | RGBA | 2,754,535 | Alpha 0–255 but only **~0.24%** fully transparent; labeled collage claiming WebMs |

**SHA1 (first 8) for duplicate spotting**

| File | sha1_8 |
|------|--------|
| yellow_card.svg | `99df798f` |
| red_card.svg | `7508ce29` |
| yellow_frame.svg | `4cced047` |
| red_frame.svg | `3e4764fe` |
| presenter_identity_pose_sheet.png | `0d34e79a` |
| entry_yellow_red_sold_reference.png | `516b1d65` |
| motion_sequence_reference.png | `12b1b093` |

No byte-identical duplicates among these files. Cards/frames are intentional color variants of shared geometry (not accidental copies).

---

## 2. Grouped inventory

### A. Gulf presenter character assets

| Asset | Role | Usable on stage? |
|-------|------|------------------|
| `references/presenter_identity_pose_sheet.png` | Same-person identity + pose collage (front, walk cycles, card/stamp holds, hand close-ups) | **No** — opaque RGB sheet; guidance only |
| Storyboard character strips (both PNGs) | Frame-by-frame *illustrations* of entry / point / cards / sold / exit | **No** — collage references |
| `metadata/*.json` | Declares intended actions + cue schema | Schema useful; values empty |

**Same person across sheets:** Yes — white kandura / ghutra / black agal presenter identity is consistent.

### B. Walking and pose references

| Source | What it shows |
|--------|----------------|
| Pose sheet bottom row | Back-view walk, side-profile walk, 3/4 approach, idle |
| `entry_yellow_red_sold_reference.png` | Numbered entry 01–12 (front), exit strip, point 4-up |
| `motion_sequence_reference.png` | Entry/exit strips + action strips drawn over studio-like floor; **labels claim WebM** that are not in this folder |

These are **static references**. They do **not** constitute walk cycles, sprite atlases, or video.

### C. Yellow and Red Card assets

| Asset | Type | Usable directly? |
|-------|------|------------------|
| `overlays/yellow_card.svg` | Vector flat card | **Yes** (UI / hand-held card graphic) |
| `overlays/red_card.svg` | Vector flat card | **Yes** |
| Cards drawn inside PNG sheets | Embedded in collages | Reference only |
| Hand-holding close-ups on pose sheet | Raster on opaque sheet | Reference only — would need cutout + cleanup if ever used as still props |

### D. SOLD stamps

| Asset | Location | Notes |
|-------|----------|-------|
| Presenter holding stamp | Pose sheet / storyboards | Reference only |
| Isolated wood-handle stamp prop | Pose sheet | Reference only |
| Flat red “SOLD” imprint graphic | Storyboard sheets | Reference art — **not** a separate file in this folder |
| Production imprint already in V4 | `assets/sold/stamp.png` (420×220, RGBA, outside this folder) | Separate pipeline asset; do not confuse with missing `sold_stamp.webm` character clip |

**Missing here:** character performance WebM that ends in a stamp contact; measured `contact_ms` / `stamp_tip` UV.

### E. Plate warning frames

| Asset | Type | Usable directly? |
|-------|------|------------------|
| `overlays/yellow_frame.svg` | 1600×440 glowing rounded rect outline | **Yes, with caution** — conceptual; must be fitted to **actual plate-shell bounds**, not stretched blindly |
| `overlays/red_frame.svg` | Same | **Yes, with caution** |
| Frame thumbnails on storyboards | Collage | Reference only |

Pack README correctly warns: generate glow from exact rendered plate bounds; validate aspect ratio.

### F. Other visual effects

| Item | Status in this folder |
|------|------------------------|
| Fireworks / particle FX | Not present (V4 already has separate sold FX code) |
| Beam / number drop FX | Not present |
| Ambient floating plates | Not in this folder (handled under `assets/bg_plates/`) |
| Transparent WebM character reels | **Not present** |

---

## 3. Duplicates and quality issues

### Duplicates / overlaps (conceptual)

1. **Yellow/red cards** appear as: SVG overlays + collage embeds on both storyboards + pose sheet. Canonical production source for *flat cards* = the **SVGs**.
2. **Yellow/red frames** appear as: SVG overlays + storyboard thumbnails. Canonical = **SVGs**.
3. **Action metadata** mirrored by V4 runtime stubs under `assets/character/meta/{point,yellow,red,sold_stamp}.json` (also `status: missing`). Starter-pack JSON is richer (cue/anchor schema) but still unmeasured.
4. **SOLD imprint** concept appears on storyboards; live V4 already uses `assets/sold/stamp.png`.

### Low-quality / unsuitable for direct broadcast use

| Issue | Files | Why |
|-------|-------|-----|
| No alpha despite “sticker” look | `presenter_identity_pose_sheet.png` | Mode **RGB**; white sheet background baked in |
| Fake / weak alpha | `entry_yellow_red_sold_reference.png` | RGBA but min alpha **149** — cannot key cleanly |
| Marketing collage vs delivery | `motion_sequence_reference.png` | Claims “WEBM Animations (Alpha)” in-panel text, but **no WebM files ship with the pack** |
| Composite density | All three PNGs | Multi-panel sheets; not sliced sprites; labels/UI chrome baked in |
| Unmeasured cues | All four metadata JSON | `duration_ms`, anchors, contact times all `null` |

---

## 4. What can be used directly in V4

| Asset | Direct use | Suggested V4 role |
|-------|------------|-------------------|
| `overlays/yellow_card.svg` | Yes | Plate/character card prop or rim companion |
| `overlays/red_card.svg` | Yes | Same (number-hide language) |
| `overlays/yellow_frame.svg` | Yes* | Yellow warning rim around `#plate-shell` (*fit to bounds) |
| `overlays/red_frame.svg` | Yes* | Red conceal/warning rim (*fit to bounds) |
| `metadata/*.json` | Schema only | Template for measured cue files after WebM land |
| `README.md` | Process rules | Keep as integration contract |
| All PNG sheets | **No on-stage** | Art / motion briefing only |

\* Frame aspect is **1600×440** (~3.64:1). V4 plate shell aspect differs by emirate; always scale to live plate rect, never assume 1:1 with this viewBox.

---

## 5. Static references that require real animation

Must be **produced** as motion media (not CSS-slid stills):

| Intended clip | Declared by metadata | Seen only as | Required for V4 character controller |
|---------------|----------------------|--------------|--------------------------------------|
| Entry from bottom center + approach | Implied by storyboards + README | PNG strips | Yes (shared into action WebMs or separate intro) |
| `point.webm` | `metadata/point.json` | Pose + 4-up strip | Yes — `assets/character/point.webm` |
| `yellow.webm` | `metadata/yellow.json` | Raise-card strip | Yes |
| `red.webm` | `metadata/red.json` | Raise-card strip | Yes |
| `sold_stamp.webm` | `metadata/sold_stamp.json` | Stamp action strip | Yes |
| Exit to bottom center | Storyboards | Exit strip | Yes (end of each clip or shared exit) |
| Walk / 3/4 rear approach | Pose sheet + README | Still frames | Yes — README requires rear/3/4 for podium approach authenticity |

**Do not** treat pose-sheet stills as a walk by translating a PNG.

---

## 6. Transparent WebM audit

| Search | Result |
|--------|--------|
| `assest_stickers/**/*.webm` | **0 files** |
| `h2_live_v4/**/*.webm` | **0 files** |
| Video elsewhere under `h2_live_v4/refs/qa/` | `aging-demo.mp4`, `feature-demo.mp4` only — **not** alpha character reels |
| Runtime paths expected by `js/character-controller.js` | `./assets/character/{action}.webm` — **missing** |

**Conclusion:** No real transparent WebM character videos exist in V4 today. The storyboard that *lists* WebMs is aspirational packaging copy, not a delivery receipt.

---

## 7. Recommended production workflow (missing animations)

### 7.1 Delivery targets (match controller)

Place under `h2_live_v4/assets/character/` (not inside `assest_stickers/`):

| File | Content |
|------|---------|
| `point.webm` | Bottom-center entry → walk/pose → point gesture → hold → exit (or loop-safe end) |
| `yellow.webm` | Entry → raise yellow card → hold for cue → exit |
| `red.webm` | Entry → raise red card → hold for cue → exit |
| `sold_stamp.webm` | Entry → stamp contact on plate plane → release → exit |
| `meta/{action}.json` | Measured `duration_ms`, `fps_nominal`, `gesture_ms` / `contact_ms` / `release_ms`, UV anchors |

Keep starter-pack JSON as the **schema reference**; overwrite/port measured values into `assets/character/meta/` after QA.

### 7.2 Capture / authoring pipeline

1. **Lock identity** from `presenter_identity_pose_sheet.png` (wardrobe, beard, agal, proportions). Same talent/rig for all clips.
2. **Block to storyboards** (`entry_yellow_red_sold_reference.png`, `motion_sequence_reference.png`) for timing language; do not rotoscope the collage as final.
3. **Shoot or render** full performance against a true keyable BG (green) **or** native 3D/AI pipeline with **straight alpha**.
4. **Export VP9/WebM with alpha** (or ProRes 4444 → WebM alpha). Target roughly character layer size used by V4 (`#character` corridor ~420×720 stage CSS px); prefer master ≥1080h then downscale.
5. **Camera / staging rules** (from pack README):
   - Enter / exit **bottom center** (stage X≈960 world).
   - Approach podium with **rear or ¾ back** then settle to interactive front/3/4 as needed.
   - Natural walk — no foot slide.
6. **Measure cues** in an editor (frame → ms): card raise peak, stamp contact, point apex. Write into meta JSON; only then set `status: "measured"`.
7. **Composite QA in V4 sandbox** (`admin.html` Yellow / Red / Point / Sold stamp): confirm alpha edges, no black boxes, cue sync with plate rim / number hide / sold imprint, keep-out vs logo/timer/plate/bid.
8. **Keep character disabled** until WebM + measured meta pass (controller already surfaces incomplete/missing).

### 7.3 Overlay track (can proceed in parallel)

1. Wire SVG cards/frames to plate-shell-local layers (yellow rim / red conceal).
2. Fit frames to live `getBoundingClientRect()` of `#plate-shell` (or geometry helper), preserve stroke width in CSS px.
3. Continue using `assets/sold/stamp.png` for imprint unless a higher-res transparent stamp is supplied later.

### 7.4 Explicitly out of scope for this inventory

- Implementing animations  
- Changing Django / Classic / TikTok / current V4 display  
- Moving or renaming files in `assest_stickers/`

---

## 8. Cross-reference to current V4 wiring

| V4 path | State |
|---------|-------|
| `js/character-controller.js` | Loads `./assets/character/${action}.webm` + meta; marks incomplete when missing |
| `assets/character/meta/*.json` | Present, `status: "missing"` |
| `assets/character/*.webm` | **Absent** |
| `assets/sold/stamp.png` | Present (plate imprint), independent of character WebM |
| Pack README integration rules | Align with controller: disable character until real alpha WebMs exist |

---

## 9. STOP checklist

- [x] Listed all files with format, dimensions, transparency  
- [x] Grouped into character / walk-pose / cards / stamps / frames / other  
- [x] Flagged duplicates and low-quality sheets  
- [x] Marked direct-use vs reference-only  
- [x] Confirmed **no** transparent character WebMs in V4  
- [x] Documented production workflow for missing animations  
- [x] No asset mutations; no V4/Django/Classic/TikTok code changes  

**Inventory complete.**
