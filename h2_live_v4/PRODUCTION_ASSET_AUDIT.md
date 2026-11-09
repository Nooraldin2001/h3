# H2 Auctions — Production Plate Asset Audit

**Date:** 2026-11-09  
**Scope:** Read-only inventory of UAE plate templates, phone frames, and dynamic overlay wiring.  
**Out of scope for this document:** No Django / DB / Live Control Panel changes. No plate-system rebuild. No V4 screen modifications.

---

## 1. Supported plate types (Django)

Source: `plates/models.py` → `LiveBroadcastSession.PLATE_TYPE_CHOICES`

| `plate_type` | Label | Category |
|---|---|---|
| `abudhabi` | Abu Dhabi | Emirate |
| `dubai` | Dubai | Emirate |
| `dubai_yellow` | Dubai Yellow | Emirate (classic yellow blank) |
| `sharjah` | Sharjah | Emirate |
| `ajman` | Ajman | Emirate |
| `rasalkhimma` | Ras Al Khaimah | Emirate |
| `ummalquain` | Umm Al Quwain | Emirate |
| `fujairah` | Fujairah | Emirate |
| `du` | du | Phone frame |
| `etisalat` | Etisalat | Phone frame |

Session fields used for rendering:

- Emirates: `code`, `number`
- Phone types: `phone_number` only

---

## 2. Dynamic rendering maps

### 2.1 New Style Live (`display-new`)

- JS: `static/js/live-display-new.js`
- CSS overlays: `static/css/live-display-new.css`
- Image base: `/static/live_new/plates/`

```js
EMIRATE_TYPES = [abudhabi, dubai, dubai_yellow, rasalkhimma, fujairah, ajman, ummalquain, sharjah]
PHONE_TYPES   = [du, etisalat]
PLATE_IMAGES  = {
  abudhabi: "abudhabi.jpg",
  dubai: "dubai.jpg",
  dubai_yellow: "dubai_classic.jpg",
  rasalkhimma: "rasalkhimma.jpg",
  fujairah: "fujairah.jpg",
  ajman: "ajman.jpg",
  ummalquain: "ummalquain.jpg",
  sharjah: "sharjah.jpg",
  du: "du.png",          // CRITICAL: wrong file (see §5)
  etisalat: "etisalat.png" // CRITICAL: wrong file (see §5)
}
```

TikTok display (`static/js/live-display-tiktok.js`) uses the same plate map / filenames.

### 2.2 Classic Live

- JS: `static/js/live-plate.js`
- Image base: `/static/plates/`

```js
LIVE_PLATE_IMAGES = {
  abudhabi: "Abu_Dhabi.jpg",
  dubai: "dubai.jpg",
  dubai_yellow: "dubai_classic.jpg",
  rasalkhimma: "Ras_Alkhima.jpg",
  fujairah: "Al_fujjairah.jpg",
  ajman: "ajman.jpg",
  ummalquain: "om_qaun.jpg",
  sharjah: "sharjah.jpg",
  du: "du.png",           // correct RGBA phone frame
  etisalat: "etisalat.png" // correct RGBA phone frame
}
```

### 2.3 Overlay mode by type

| Types | Overlay elements | API / session fields |
|---|---|---|
| All 8 emirates | Code + number text overlays | `code`, `number` |
| `du`, `etisalat` | Phone text overlay only | `phone_number` |

All listed types already support dynamic overlays in Classic and New Style JS (text is injected into positioned CSS boxes over blank artwork).

---

## 3. New Style production assets

Folder: `c:\Users\moham\h3\static\live_new\plates\`

| File | Maps to | W×H | Aspect | Format (Pillow) | Bytes | MD5 |
|---|---|---|---|---|---|---|
| `abudhabi.jpg` | `abudhabi` | 1081×223 | 4.848 | JPEG / RGB | 30290 | `1b34d01470f9497271a3c30c2d951192` |
| `dubai.jpg` | `dubai` | 1012×214 | 4.729 | JPEG / RGB | 20967 | `cbe61299d52fa0d6e0c5306c84c4d6ac` |
| `dubai_classic.jpg` | `dubai_yellow` | 1290×306 | 4.216 | JPEG / RGB | 28074 | `aef1f076ed32348d47bdbe7022be0c7e` |
| `rasalkhimma.jpg` | `rasalkhimma` | 1600×339 | 4.720 | JPEG / RGB | 70116 | `88a1385ab471d854ff2e6ab6d08d91f7` |
| `fujairah.jpg` | `fujairah` | 1146×247 | 4.640 | JPEG / RGB | 31967 | `7a9b0825e3c7b7fc1a67569574ec5938` |
| `ajman.jpg` | `ajman` | 1075×214 | 5.023 | JPEG / RGB | 24241 | `1d0299a885c7a170c9d13160ef7ce3f6` |
| `ummalquain.jpg` | `ummalquain` | 1600×319 | 5.016 | JPEG / RGB | 64509 | `d60f26abafecbfdd238721d9d274a274` |
| `sharjah.jpg` | `sharjah` | 1413×397 | 3.559 | JPEG / RGB | 72759 | `c662efb13f4762c94c22d870caa5c21d` |
| `du.png` | `du` (mapped) | 1012×214 | 4.729 | **JPEG / RGB** (mislabeled `.png`) | 20967 | `cbe61299…` **= dubai.jpg** |
| `etisalat.png` | `etisalat` (mapped) | 1012×214 | 4.729 | **JPEG / RGB** (mislabeled `.png`) | 20967 | `cbe61299…` **= dubai.jpg** |
| `du.jpeg` | *(present, NOT mapped)* | 894×204 | 4.382 | JPEG / RGB | 28071 | `a79bb5b95bbad75f98b0218eb1cd2734` |
| `etisalat.jpeg` | *(present, NOT mapped)* | 879×236 | 3.725 | JPEG / RGB | 29509 | `b04280fde8b7381a57af16c73ef89a2f` |

**Rendering use:** Blank plate / phone frame image + CSS %-positioned text overlays (`code`/`number` or `phone_number`).

---

## 4. Classic production assets

Folder: `c:\Users\moham\h3\static\plates\`

### 4.1 Mapped by `LIVE_PLATE_IMAGES`

| File | Maps to | W×H | Format | Bytes | MD5 | Notes |
|---|---|---|---|---|---|---|
| `Abu_Dhabi.jpg` | `abudhabi` | 1081×223 | JPEG / RGB | 30290 | `1b34d014…` | Same pixels as live_new `abudhabi.jpg` |
| `dubai.jpg` | `dubai` | 1012×214 | JPEG / RGB | 20967 | `cbe61299…` | Same as live_new |
| `dubai_classic.jpg` | `dubai_yellow` | 1290×306 | JPEG / RGB | 28074 | `aef1f076…` | Same as live_new |
| `Ras_Alkhima.jpg` | `rasalkhimma` | 1600×339 | JPEG / RGB | 70116 | `88a1385a…` | Same as live_new |
| `Al_fujjairah.jpg` | `fujairah` | 1146×247 | JPEG / RGB | 31967 | `7a9b0825…` | Same as live_new |
| `ajman.jpg` | `ajman` | 1075×214 | JPEG / RGB | 24241 | `1d0299a8…` | Same as live_new |
| `om_qaun.jpg` | `ummalquain` | 1600×319 | JPEG / RGB | 64509 | `d60f26ab…` | Same as live_new |
| `sharjah.jpg` | `sharjah` | 1413×397 | JPEG / RGB | 72759 | `c662efb1…` | Same as live_new |
| `du.png` | `du` | 894×204 | **PNG / RGBA** | 71334 | `8550b1ef8db613b88ef31620f7922e08` | Real phone frame |
| `etisalat.png` | `etisalat` | 879×236 | **PNG / RGBA** | 61312 | `8afc92dbe733e2e36b8b0dbc63f659eb` | Real phone frame |

### 4.2 Present but unused by live plate maps

| File | W×H | Format | Bytes | MD5 | Notes |
|---|---|---|---|---|---|
| `du.jpeg` | 894×204 | JPEG / RGB | 28071 | `a79bb5b9…` | Same art family as Classic `du.png` / live_new `du.jpeg` |
| `etisalat.jpeg` | 879×236 | JPEG / RGB | 29509 | `b04280fd…` | Same art family as Classic `etisalat.png` |
| `Abu_Dhabi.jpeg` | 1080×1350 | JPEG / RGB | 28249 | `238b81a4…` | Portrait; not in live maps |
| `dubai.jpeg` | 1080×1350 | JPEG / RGB | 23399 | `19c44813…` | Portrait; not in live maps |
| `Ras_Alkhima.jpeg` | 1080×1350 | JPEG / RGB | 23298 | `0ffbe2ff…` | Portrait; not in live maps |
| `Al_fujjairah.jpeg` | 1080×1350 | JPEG / RGB | 26092 | `aa8a2cc2…` | Portrait; not in live maps |
| `ajman.jpeg` | 1080×1350 | JPEG / RGB | 24842 | `60048c87…` | Portrait; not in live maps |
| `om_qaun.jpeg` | 1080×1350 | JPEG / RGB | 23609 | `22e5a372…` | Portrait; not in live maps |
| `sharjah.jpeg` | 1080×1350 | JPEG / RGB | 29998 | `74a1cb6d…` | Portrait; not in live maps |

---

## 5. Duplicates, wrong maps, quality issues

### 5.1 Critical wrong mapping (New Style + TikTok)

| Asset | Problem |
|---|---|
| `static/live_new/plates/du.png` | Byte-identical to `dubai.jpg` (MD5 `cbe61299…`). Named `.png` but decoded as JPEG/RGB. |
| `static/live_new/plates/etisalat.png` | Same — byte-identical Dubai placeholder. |

Real phone frames already exist next to them as `du.jpeg` / `etisalat.jpeg`, but **New Style `PLATE_IMAGES` does not point at them**.

Classic is correct: `static/plates/du.png` / `etisalat.png` are genuine RGBA phone frames.

### 5.2 Duplication summary

- Emirate `.jpg` pixels are shared 1:1 between Classic (alternate filenames) and New Style.
- Dubai MD5 `cbe61299…` appears as: Classic `dubai.jpg`, New Style `dubai.jpg`, New Style `du.png`, New Style `etisalat.png`, and V4 copies of those four names.
- Phone JPEG masters (`du.jpeg` / `etisalat.jpeg`) are duplicated across Classic, New Style folders, and V4.

### 5.3 Soft / low-resolution emirates

Emirate blanks are ~1075–1600px wide with heavy JPEG compression (≈21–73 KB). At broadcast plate width (~760px+) they look soft. Design is correct; resolution is insufficient for a premium OBS look.

### 5.4 New Style stage aspect distortion risk

New Style `.nld-plate-stage` uses a **16:9** stage while plate art aspects are ~3.56–5.02. Overlays are %-boxes on the stage, not locked to native plate aspect. This can misalign code/number relative to the blank when the image is `object-fit: contain`.

---

## 6. Overlay CSS (New Style) — reuse candidates

Source: `static/css/live-display-new.css` (approx. lines 988–1102)

| CSS type class | Code box (top / left / w / h) | Number box | Phone box |
|---|---|---|---|
| `abudhabi` | 30% / 2% / 12% / 35% | 25% / 52% / 42% / 45% | — |
| `dubai`, `dubai-yellow` | 50% / 8% / 12% / 38% | 30% / 38% / 52% / 40% | — |
| `rasalkhimma` | 33% / 32% / 14% / 35% | 25% / 52% / 44% / 45% | — |
| `fujairah` | 20% / 3% / 12% / 38% | 23% / 45% / 48% / 45% | — |
| `ajman` | 38% / 7% / 10% / 24% | 32% / 24% / 38% / 36% | — |
| `ummalquain` | 35% / 3% / 14% / 35% | 25% / 48% / 48% / 45% | — |
| `sharjah` | 25% / 20% / 10% / 40% | 36% / 60% / 34% / 20% | — |
| `du`, `etisalat` | — | — | 14% / 3.5% / 70% / 72% |

These %-boxes are the production dynamic overlay contract. Keep them when swapping sharper art of the **same aspect**.

Classic CSS uses equivalent boxes; type class for yellow is `dubai_yellow` (underscore) vs New Style `dubai-yellow` (hyphen).

---

## 7. V4 prototype assets vs production

Folder: `c:\Users\moham\h3\h2_live_v4\assets\plates\`

| V4 file | W×H | Bytes | MD5 | vs `static/live_new/plates/` |
|---|---|---|---|---|
| `abudhabi.jpg` | 1081×223 | 30290 | `1b34d014…` | Identical |
| `dubai.jpg` | 1012×214 | 20967 | `cbe61299…` | Identical |
| `dubai_classic.jpg` | 1290×306 | 28074 | `aef1f076…` | Identical |
| `rasalkhimma.jpg` | 1600×339 | 70116 | `88a1385a…` | Identical |
| `fujairah.jpg` | 1146×247 | 31967 | `7a9b0825…` | Identical |
| `ajman.jpg` | 1075×214 | 24241 | `1d0299a8…` | Identical |
| `ummalquain.jpg` | 1600×319 | 64509 | `d60f26ab…` | Identical |
| `sharjah.jpg` | 1413×397 | 72759 | `c662efb1…` | Identical |
| `du.jpeg` | 894×204 | 28071 | `a79bb5b9…` | Identical (real phone frame) |
| `etisalat.jpeg` | 879×236 | 29509 | `b04280fd…` | Identical (real phone frame) |
| `du.png` | 1012×214 | 20967 | `cbe61299…` | Identical **broken** placeholder |
| `etisalat.png` | 1012×214 | 20967 | `cbe61299…` | Identical **broken** placeholder |

Also: `h2_live_v4/assets/plate-dubai.jpg` matches `dubai.jpg` (MD5 `cbe61299…`).

**Current V4 screen behavior (unchanged by this audit):**

- `h2_live_v4/js/broadcast.js` mocks Dubai only (`AA` / `7777`).
- Base CSS in `h2_live_v4/css/broadcast.css` positions Dubai code/number overlays.
- Full multi-type plate JS map is **not** present as a separate `plate-system.js` in the current tree; the **artwork inventory** for all types already sits under `assets/plates/`.

---

## 8. Type → file → overlay → classification

| plate_type | New Style file | Classic file | V4 file present | Overlay | Classification |
|---|---|---|---|---|---|
| `abudhabi` | `abudhabi.jpg` | `Abu_Dhabi.jpg` | `abudhabi.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `dubai` | `dubai.jpg` | `dubai.jpg` | `dubai.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `dubai_yellow` | `dubai_classic.jpg` | `dubai_classic.jpg` | `dubai_classic.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `rasalkhimma` | `rasalkhimma.jpg` | `Ras_Alkhima.jpg` | `rasalkhimma.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `fujairah` | `fujairah.jpg` | `Al_fujjairah.jpg` | `fujairah.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `ajman` | `ajman.jpg` | `ajman.jpg` | `ajman.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `ummalquain` | `ummalquain.jpg` | `om_qaun.jpg` | `ummalquain.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `sharjah` | `sharjah.jpg` | `sharjah.jpg` | `sharjah.jpg` | code + number | **UPGRADE** (REUSE until sharper master) |
| `du` | **`du.png` WRONG** | `du.png` OK (RGBA) | `du.jpeg` OK + leftover bad `du.png` | phone_number | New Style map target **REPLACE**; Classic PNG **REUSE**; JPEG **REUSE** (or UPGRADE from Classic PNG) |
| `etisalat` | **`etisalat.png` WRONG** | `etisalat.png` OK (RGBA) | `etisalat.jpeg` OK + leftover bad `etisalat.png` | phone_number | Same as `du` |

### System-level classifications

| Item | Class | Why |
|---|---|---|
| Emirate JPG blanks (all paths) | **UPGRADE** | Correct official-style blanks; soft / under-resolved for 1920×1080 OBS |
| New Style / TikTok `du.png` / `etisalat.png` | **REPLACE** | Dubai placeholders; incorrect mapping |
| V4 leftover `du.png` / `etisalat.png` | **REPLACE** | Dead broken copies; do not map |
| `du.jpeg` / `etisalat.jpeg` (live_new + V4) | **REUSE** | Correct phone frames currently available |
| Classic `du.png` / `etisalat.png` | **REUSE** | Best current phone artwork (PNG/RGBA) |
| Classic unused 1080×1350 `*.jpeg` portraits | **REPLACE** / archive | Not used by live plate maps |
| Overlay %-box CSS | **REUSE** | Production dynamic overlay contract |
| New Style 16:9 plate stage wrapping | **UPGRADE** | Prefer native plate aspect for overlay accuracy |

---

## 9. Recommendations (audit only — not implemented here)

1. Prefer Classic RGBA `du.png` / `etisalat.png` as phone masters when remapping New Style / TikTok (out of scope for this audit).
2. Keep using existing emirate JPGs until official ≥~2000px blanks are supplied; do not invent plate designs.
3. V4 already holds byte-identical emirate copies plus usable phone JPEGs; remove or ignore broken V4 `du.png` / `etisalat.png` when wiring multi-type later.
4. Do not rebuild the plate system as part of asset intake.

---

## 10. Audit stop note

This document is the sole deliverable of the Production Asset Audit.  
**No production files, Django models, Control Panel, or V4 screen files were modified.**
