# H2 Auctions V4 — Character Motion Asset Audit

**Date:** 2026-11-09  
**Scope (read-only):** `h2_live_v4/refs/qa/assest_stickers/H2_Character_Motion_Preview_Pack/`  
**Compared against:** `js/character-controller.js` + `assets/character/meta/*.json`  
**Constraints honored:** No production asset changes, no character activation, no Django/Classic/TikTok/Phase 8 edits, no commit/push/deploy.

---

## Executive verdict

| Question | Answer |
|----------|--------|
| Are these production character WebMs? | **No** |
| Any clip marked `measured`? | **No** — none inspected to a verified gesture/contact frame schedule |
| Transparent alpha usable in practice? | **PNG/GIF frames: yes (hard matte).** **WebM: tagged `alpha_mode=1` but decode → fully opaque RGBA** |
| Ready for V4 controller side-effects? | **No** — missing `red` / `sold_stamp` WebMs; no measured meta; wrong entry perspective |
| Bottom-center rear approach supported? | **No** — entry is **front-facing** walk toward camera |

Pack self-labels correctly: README + `motion_manifest.json` = **unapproved / unmeasured motion previews**.

---

## 1. Inventory

**Total files:** 41 under the preview pack root.

### 1.1 Layout

```
H2_Character_Motion_Preview_Pack/
├── red card.gif                          (loose root)
├── sold.gif                              (loose root)
├── sold man.gif                          (loose root; duplicate of sold.gif)
└── H2_Character_Motion_PREVIEWS/
    ├── README.md
    ├── motion_manifest.json
    ├── entry_FRONT_VIEW_ONLY.webm
    ├── entry_FRONT_VIEW_ONLY_source.gif
    ├── exit_FRONT_VIEW_REVERSED.webm
    ├── exit_FRONT_VIEW_REVERSED_source.gif
    ├── point.webm
    ├── point_source.gif
    ├── yellow.webm
    ├── yellow_source.gif
    └── png_frames/
        ├── entry_FRONT_VIEW_ONLY/0000–0007.png      (8)
        ├── exit_FRONT_VIEW_REVERSED/0000–0007.png   (8)
        ├── point/0000–0003.png                      (4)
        └── yellow/0000–0007.png                     (8)
```

**Absent from this pack:** `red.webm`, `sold_stamp.webm`, measured cue JSON, rear-view entry/exit masters.

### 1.2 Counts by type

| Type | Count | Role |
|------|------:|------|
| `.webm` | 4 | Preview encodes |
| `.gif` | 7 | Sources + loose root previews |
| `.png` | 28 | Per-frame inspection stills |
| `.json` | 1 | Unmeasured manifest |
| `.md` | 1 | Pack disclaimer |

---

## 2. Codec / resolution / fps / duration / alpha

Probed with OpenCV + FFmpeg (`libvpx-vp9` encode tag) and Pillow on GIF/PNG.

### 2.1 WebM

| File | Codec | Pix fmt (ffmpeg) | Alpha metadata | WxH | FPS | Frames | Duration | Bitrate ~ |
|------|-------|------------------|----------------|-----|-----|--------|----------|-----------|
| `entry_FRONT_VIEW_ONLY.webm` | VP9 Profile 0 | `yuv420p` | `alpha_mode: 1` | 443×443 | 5 | 8 | **1.60 s** | ~183 kb/s |
| `exit_FRONT_VIEW_REVERSED.webm` | VP9 Profile 0 | `yuv420p` | `alpha_mode: 1` | 443×443 | 5 | 8 | **1.60 s** | ~192 kb/s |
| `point.webm` | VP9 Profile 0 | `yuv420p` | `alpha_mode: 1` | 440×441 | 5 | **4** | **0.80 s** | ~243 kb/s |
| `yellow.webm` | VP9 Profile 0 | `yuv420p` | `alpha_mode: 1` | 442×441 | 5 | 8 | **1.60 s** | ~207 kb/s |

**Alpha verification (critical):**

- Manifest text claims “VP9 yuva420p”.
- Actual stream is **`yuv420p` + `alpha_mode=1`** on a **single** video stream.
- FFmpeg extract to PNG (`-pix_fmt rgba`) for **all four WebMs** yields **alpha channel constant 255** (0% transparent pixels).
- Conclusion: WebMs are **not verified as usable transparent composites**. Treat alpha as **broken / non-functional for production compositing** until re-encoded from the PNG sequence (which *does* have real alpha).

### 2.2 Source GIFs (PREVIEWS)

| File | Size | Frames | Duration sum | Transparency |
|------|------|--------|--------------|--------------|
| `entry_FRONT_VIEW_ONLY_source.gif` | 443×443 | 8 | 1760 ms | Yes (~89%→75% clear over sequence) |
| `exit_FRONT_VIEW_REVERSED_source.gif` | 443×443 | 8 | 1760 ms | Same bytes as entry source (**duplicate**) |
| `point_source.gif` | 440×441 | **8** | 1440 ms | Yes (~79% clear) |
| `yellow_source.gif` | 442×441 | 8 | 1600 ms | Yes (~55% clear; waist-up fills more) |

### 2.3 Loose root GIFs

| File | Size | Frames | Duration | Notes |
|------|------|--------|----------|-------|
| `red card.gif` | 271×724 | 8 | 1440 ms | Transparent matte; **no matching `.webm`** |
| `sold.gif` | 299×724 | 8 | 1440 ms | Transparent matte; stamp prop visible |
| `sold man.gif` | 299×724 | 8 | 1440 ms | **Byte-identical** to `sold.gif` (`sha1_8=f7e183f7`) |

### 2.4 PNG frame sequences

All inspected PNGs are **RGBA** with true holes (`alpha_min=0`, `alpha_max=255`). Binary matte (semi-transparent % ≈ 0) — hard cutouts, not soft AA mattes. Subject fill grows across entry (transparent area 89% → ~75%), consistent with approach scale change.

| Sequence | Frames | Canvas | Alpha quality |
|----------|--------|--------|---------------|
| `entry_FRONT_VIEW_ONLY` | 8 | 443×443 | Real transparency |
| `exit_FRONT_VIEW_REVERSED` | 8 | 443×443 | Same pixels as entry reversed (see duplicates) |
| `point` | **4** | 440×441 | Real transparency |
| `yellow` | 8 | 442×441 | Real transparency; waist-up |

---

## 3. Available actions vs gaps

| Action | In this pack? | Primary files | Completeness |
|--------|---------------|---------------|--------------|
| **Entry** | Partial | `entry_FRONT_VIEW_ONLY.webm` + gif + 8 png | Front walk only; wrong cinematic approach |
| **Exit** | Fake | `exit_FRONT_VIEW_REVERSED.*` | Time-reversal of entry — **not** authored exit |
| **Point** | Partial | `point.webm` (4f) / `point_source.gif` (8f) / 4 png | WebM **drops half** of GIF frames; short |
| **Yellow** | Partial | `yellow.webm` + gif + 8 png | Waist-up card raise study; not full entry→gesture→exit |
| **Red** | GIF only | `red card.gif` | **No WebM**, no png_frames folder |
| **SOLD / sold_stamp** | GIF only | `sold.gif` / `sold man.gif` | **No WebM**; stamp held while walking — not measured contact |

Manifest `missing_production` list still correct for production names (`red.webm`, `sold_stamp.webm`, proper entry/exit, measured point/yellow).

---

## 4. Artifacts, identity, incomplete motion

### 4.1 Transparency / matte

- **PNG/GIF:** Functional hard-alpha cutouts. Visual review shows occasional **white edge fringe / aliasing** on white ghutra & kandura (typical generative key). Worse on dark studio than numbers alone imply.
- **WebM:** Alpha flag present but **decoded frames are opaque** → risk of **black/colored rectangles** if dropped into `<video>` expecting VP9 alpha.

### 4.2 Character appearance consistency

| Clip family | Framing | Identity notes |
|-------------|---------|----------------|
| Entry / exit / point (full body) | ~443² full figure | Kandura + ghutra + agal; no lapel mic |
| Yellow | Waist-up ~442×441 | Same general talent, but **lapel mic** appears; different crop/scale language |
| Red / sold GIFs | Tall portrait 271–299 × 724 | Different canvas aspect; sold holds oversized stamp prop |

Not one locked hero master. Treat as **research variants**, not one production identity lock.

### 4.3 Incomplete / incorrect motion

1. **Exit = reversed entry** — every exit PNG is a byte-identical reverse of an entry PNG (see §5 duplicates).
2. **`point.webm` = 4 frames** while `point_source.gif` = 8 — incomplete encode.
3. **Yellow** — card appears mid-sequence; no walk-in/out; not a full operator action reel.
4. **Point** sequence mixes walk-like frames with a pointing hold — short, not cue-annotated.
5. **Red / SOLD** — GIF sketches only; README states clean usable animation not delivered.
6. **5 fps / ≤1.6 s** — research cadence, not broadcast motion quality.

**Gesture/contact frames:** Not marked measured. No `gesture_ms` / `contact_ms` derived or approved in this audit (per task rule #8).

---

## 5. Bottom-center entry & studio perspective

**Requirement (V4 + prior starter pack):** enter from **bottom center**, approach podium with **rear / ¾ back** walk, then face audience for gestures.

| Check | Result |
|-------|--------|
| Entry faces camera (front view) | **Yes** — filename and frames |
| Walks *away* from camera toward podium | **No** |
| Perspective foreshortening / floor contact for stage depth | Weak — flat generative full-body; no studio floor contact shadow |
| Exit as turn + walk away | **No** — reversed front walk |
| Suitable as cinematic bottom-center approach | **No** (matches pack README warning) |

Front walk *toward* viewer can still be *hacked* as a UI pop-up, but it **fails** the requested realistic studio approach.

---

## 6. V4 character-controller gap analysis

Controller (`js/character-controller.js`):

- Actions: `point`, `yellow`, `red`, `sold_stamp`
- Loads: `./assets/character/{action}.webm`
- Meta: `./assets/character/meta/{action}.json`
- Side effects (yellow rim / red conceal / sold imprint sync) **only if** `meta.status === "measured"` **and** WebM present

| Controller need | Preview pack | Production tree today |
|-----------------|--------------|------------------------|
| `point.webm` | Preview only (4f, opaque decode) | **Missing** under `assets/character/` |
| `yellow.webm` | Preview only | **Missing** |
| `red.webm` | **Absent** (GIF only) | **Missing** |
| `sold_stamp.webm` | **Absent** (GIF only) | **Missing** |
| Measured meta + cues | Manifest `unmeasured`; cues null | Meta files exist with `status: "missing"` |
| Entry/exit as separate assets | Not in controller API (baked into action clips per design notes) | N/A |

**Do not copy these previews into `assets/character/` as-is.** They would fail alpha compositing expectations and unlock nothing useful until `status` is honestly `measured` after real cue inspection.

---

## 7. Classification

Legend: **PROTOTYPE** = research only · **USABLE FOR TESTING** = offline inspection / layout experiments · **PRODUCTION-READY** = broadcast-safe + measured (none).

| File / group | Class | Rationale |
|--------------|-------|-----------|
| `entry_FRONT_VIEW_ONLY.webm` | **PROTOTYPE** | Wrong perspective; opaque decode; 5 fps / 1.6 s |
| `exit_FRONT_VIEW_REVERSED.webm` | **PROTOTYPE** | Not real exit; reverse of entry |
| `point.webm` | **PROTOTYPE** | Truncated (4f); unmeasured; opaque decode |
| `yellow.webm` | **PROTOTYPE** | Partial gesture study; opaque decode |
| `*_source.gif` (entry/point/yellow) | **USABLE FOR TESTING** | Inspect motion/matte offline; not for OBS stage |
| `exit_*_source.gif` | **PROTOTYPE** | Duplicate of entry source |
| `png_frames/**` | **USABLE FOR TESTING** | Best alpha reference in the pack; still not production masters |
| `red card.gif` | **PROTOTYPE** | No WebM; unmeasured |
| `sold.gif` / `sold man.gif` | **PROTOTYPE** | Duplicates; no WebM; unmeasured contact |
| `motion_manifest.json` / `README.md` | Documentation | Correctly marks unapproved / unmeasured |

**PRODUCTION-READY count: 0**

**Measured count: 0** (explicitly not assigned)

---

## 8. Duplicates detected (SHA-1)

| sha1_8 | Paths |
|--------|-------|
| `b45ba3c1` | `entry_FRONT_VIEW_ONLY_source.gif` ≡ `exit_FRONT_VIEW_REVERSED_source.gif` |
| `f7e183f7` | `sold.gif` ≡ `sold man.gif` |
| Per-frame | `entry/0000..0007.png` ≡ `exit/0007..0000.png` (exact reverse pairs) |

---

## 9. Recommended next production steps (audit only — not executed)

1. Author **new** RGBA image sequences at ≥1080h: rear/¾ **entry**, turn, gesture, turn, **exit** — same locked identity.
2. Export **true** VP9 alpha WebM; verify decode on black **and** gold (alpha not merely tagged).
3. Deliver `point.webm`, `yellow.webm`, `red.webm`, `sold_stamp.webm` into `assets/character/` only after QA.
4. Measure `gesture_ms` / `contact_ms` / UV anchors; set `status: "measured"` only then.
5. Keep this preview pack quarantined under `refs/qa/`; do not activate controller effects on it.

---

## 10. STOP

- Inventory, codec/alpha checks, action map, artifact/perspective review, controller comparison, and classifications complete.
- **No** animation marked measured.
- **No** production files modified; character effects not activated.
