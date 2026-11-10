# H2 Live V4 — Studio Background + Independent Plate Layer

**Date:** 2026-11-10  
**Scope:** `h2_live_v4/` only. No Django / Classic / TikTok / commit / deploy.

---

## 1. Files changed

| Path | Change |
|---|---|
| `assets/studio/H2_AUCTIONS_Studio_3840x2160.png` | Imported + clean-reencoded master (native **1024×576**) |
| `assets/studio/H2_AUCTIONS_Studio_1920x1080.jpg` | Broadcast bake (LANCZOS + mild exposure lift) — **in use** |
| `assets/studio/H2_AUCTIONS_Studio_native.png` | Clean master alias |
| `assets/studio/README.md` | Asset inventory |
| `index.html` | Layer stack refactor; new studio img; plate moved out of `.stack` |
| `css/broadcast.css` | Studio layer styles; `.layer-main-plate`; `.plate-slot`; UI stack |
| `css/fx.css` | Character z-index comment |
| `js/plate-system.js` | `syncPlateLayerToSlot()`; slot aspect follows plate type |
| `js/broadcast.js` | Re-sync plate layer after preview scale |
| `tools/capture_studio_layer_qa.py` | Visual QA harness |
| `refs/qa/studio-layer/*` | Screenshots + metrics |
| `STUDIO_LAYER_REPORT.md` | This report |

---

## 2. Studio background integration

- No SVG was delivered (`H2_AUCTIONS_Studio_4K_Vector.svg` missing).
- Provided “4K Vector” PNG is actually **1024×576** RGBA; re-encoded to clean RGB PNG.
- Stage uses **`H2_AUCTIONS_Studio_1920x1080.jpg`** (`object-fit: cover`, centered) so the 1920×1080 stage fills without letterboxing and keeps the podium centered.
- Removed the old `brightness(1.4)` wash on the previous soft still; new art is graded lightly in the JPEG bake so gold rings/spotlights read on air.
- Studio is a pure environment layer: no baked plate, timer, logo, text, or character.

---

## 3. Plate as independent layer

Desired stack (implemented):

1. `#layer-studio` — z0  
2. `#bg-plates` — z2 ambient  
3. `#stage-fw` — z3 fireworks  
4. `#layer-main-plate` — z6 main plate + plate-local FX (rim, stamp, aging, fragments, beam)  
5. `#character` — z7  
6. `#layer-ui` (text / timer / bid) — z8 + `#brand` — z10  

The plate was **removed from** the flex `.stack`. An invisible `#plate-slot` keeps timer↔bid spacing. `H2PlateSystem.syncPlateLayerToSlot()` pins `#layer-main-plate` over that slot (also on resize).

Hiding `.layer-main-plate.is-hidden` leaves the studio + chrome intact (QA shot `03-plate-hidden-studio-intact-1920.png`).

Dynamic emirates / code / number / phone + Admin sync paths were not rebuilt — only rendering host structure changed.

---

## 4. Root cause of the previous white-box look

1. Old soft studio still + heavy CSS brightness made the center feel like a washed card.  
2. Main plate lived inside the same UI stack as timer/bid, so it read as one chrome block.  
3. Opaque rectangular plate JPGs still have white corner pixels outside the painted rounded frame (asset limitation — not a CSS wrapper). Shell background is transparent (`rgba(0,0,0,0)`).

---

## 5. Final rendering asset

**JPEG** `assets/studio/H2_AUCTIONS_Studio_1920x1080.jpg` (from provided PNG master).  
SVG: not available. True 4K: not available (master is 1024×576).

---

## 6. Screenshots

Folder: `refs/qa/studio-layer/`

| File | Check |
|---|---|
| `01-broadcast-normal-1920.png` | New studio + plate + chrome |
| `02-plate-visible-crop.png` | Plate over studio |
| `03-plate-hidden-studio-intact-1920.png` | Studio complete without main plate |
| `04-yellow-card-crop.png` | Yellow rim on plate layer |
| `05-red-card-crop.png` | Red rim + digits hidden |
| `06-sold-crop.png` | SOLD stamp on plate |
| `07-aging-crop.png` | Aging still plate-local |
| `08-broadcast-1920.png` / `09-broadcast-1280.png` | Resolutions |
| `layer-metrics.json` | z-index + slot/plate alignment |

---

## 7. Remaining limitations

- Master studio is not true 4K / not SVG; 1920 JPEG is an upscale bake.  
- Plate JPGs are opaque rectangles — rounded physical silhouette would need alpha-masked masters.  
- Ambient floating plates remain stylized gray cards (unchanged).  
- Plate realism (emboss / metal type) unchanged from prior plate-redesign pass.
