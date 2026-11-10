# H2 Auctions V4 — Django Integration & Production Deployment Readiness Audit

**Audit date:** 2026-11-10  
**Mode:** Read-only (no commits, pushes, deploys, or application code changes)  
**Local HEAD:** `a31ad2d` on branch `main` tracking `origin/main`  
**Remote:** `https://github.com/Nooraldin2001/h3.git`

---

## 1. Executive Verdict

### **NOT READY**

**Evidence-based answer to the acceptance question:**

> If I manually publish the latest project revision using the correct deployment process, will the live Django website load the same approved H2 Auctions V4 functionality and visual assets that currently work locally?

### **NOT YET**

| Scope | Verdict |
|---|---|
| Local Django V4 (runserver / local static) | **YES** — Admin + Broadcast work through Django routes and `/live/api/state/` |
| Publishing **current Git `HEAD` / GitHub `main` as-is** | **NO** — approved V4 code + critical assets are **uncommitted / untracked** |
| Publishing after a complete commit that includes all required files + server `collectstatic` + restart | **LIKELY YES** — architecture is production-compatible, but **not verified on the live Hostinger server** |

### Why NOT READY

1. **Critical visual assets are untracked** (will not exist on the server if you only push what Git currently knows):
   - `static/live_v4/assets/plates/dubai-main-final.png`
   - `static/live_v4/assets/effects/sold-stamp-red.png`
   - `static/live_v4/assets/studio/H2_AUCTIONS_Studio_4K_Vector.svg`
   - Entire `static/live_v4/assets/plates/floating_final/` pack (12 PNGs + manifest)
2. **Approved V4 code changes exist only in the working tree** (modified vs `HEAD`), including Arabic Admin, plate mapping, Red/Yellow glow, SOLD stamp wiring, character depth/size, bid-slot CSS, DjangoBridge live-text race fixes, etc.
3. **`HEAD` still maps Dubai to the old asset** (`dubai.jpg`), not `dubai-main-final.png`.
4. **Live Hostinger production smoke tests were NOT VERIFIED** (no SSH/production access in this audit).
5. Large set of **deleted legacy coded floating images** is also uncommitted — must be intentional and packaged with the new `floating_final` pack.

---

## 2. Django Integration Map

### Routes (`h3auctions/urls.py`)

| Purpose | URL | Name | Lines |
|---|---|---|---|
| V4 Admin Control | `/live/control/v4/` | `live_control_v4` | 24 |
| V4 Broadcast Display | `/live/display-v4/<uuid:token>/` | `live_display_v4` | 28 |
| Shared Live State API | `/live/api/state/` | `live_state_api` | 29 |
| Live Hub | `/live/` | `live_control` | 20 |
| Classic / New / TikTok | `/live/control/classic\|new\|tiktok/` + matching display routes | — | 21–27 |

### Views (`plates/views.py`)

| View | Auth / access | Template | Notes |
|---|---|---|---|
| `live_control_v4` (≈514–527) | `@live_auction_enabled` + `@superuser_required` + CSRF cookie | `plates/live_control_v4.html` | Injects token, display URL, state JSON, state API URL |
| `live_display_v4` (≈531–546) | `@live_auction_enabled`; token lookup; **no login required** for OBS | `plates/live_display_v4.html` | Resolves `LiveBroadcastSession` by `display_token` |
| `live_state_api` (≈551+) | GET: token query; PATCH: **superuser session** | JSON | Source of truth for Admin↔Display sync |
| `_v4_enabled_or_404` (≈506–508) | `settings.LIVE_V4_ENABLED` (default True) | — | Feature flag |

### Sync architecture (production path)

- **Active V4 does NOT depend on opening `h2_live_v4/index.html`.**
- Control + Display load `{% static 'live_v4/...' %}` assets and boot `window.H2V4_DJANGO`.
- `static/live_v4/js/django-bridge.js` is the production adapter:
  - Control **PATCH** → `/live/api/state/` (credentials + CSRF)
  - Display **GET** → `/live/api/state/?token=<display_token>`
  - Optional BroadcastChannel/localStorage pulse is a **speed optimization only**, not the source of truth
- Display token comes from `LiveBroadcastSession.display_token` (same classic token used for V4 URLs in hub).

### Active templates & front-end stack

**Admin:** `templates/plates/live_control_v4.html`  
→ `static/live_v4/css/admin.css`  
→ `static/live_v4/js/django-bridge.js` + `static/live_v4/js/admin.js`

**Broadcast:** `templates/plates/live_display_v4.html`  
→ CSS: `broadcast.css`, `plate-system.css`, `fx.css`  
→ JS: `geometry`, `plate-system`, `state-controller`, `timer-controller`, `fx-sold`, `fx-beam-drop`, `fx-aging`, `fx-bg-plates`, character modules, `broadcast`, `django-bridge`

### Settings relevant to production (`h3auctions/settings.py`)

- `LIVE_V4_ENABLED` env (default True)
- `STATIC_URL=/static/`, `STATICFILES_DIRS=[BASE_DIR/static]`, `STATIC_ROOT=BASE_DIR/staticfiles`
- `STATICFILES_STORAGE = whitenoise.storage.CompressedManifestStaticFilesStorage`
- `DEBUG` / `ALLOWED_HOSTS` from env (production expects `DEBUG=False`)

### Deployment mechanism (from repo docs — not live-verified)

Documented in `DEPLOYMENT.md` + `deploy.sh` for **Hostinger VPS**:

1. Upload / `git pull` into `/var/www/h3auctions` (documented path)
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py collectstatic --noinput`
5. Restart via Supervisor (`sudo supervisorctl restart h3auctions` per `deploy.sh` comments)
6. Nginx reverse proxy

**Production host identity, current server revision, and service health: NOT VERIFIED** (no production SSH in this audit).

---

## 3. Feature Verification Matrix

Evidence sources:
- Code/static inspection of active Django paths under `templates/` + `static/live_v4/`
- Local HTTP asset checks (`127.0.0.1:8000`)
- Prior local Django E2E QA artifacts under `h2_live_v4/refs/qa/` (Admin↔Display same session)
- Fresh `manage.py test plates.tests` (47 OK)

| Feature | Status | Evidence | Key sources | Issues |
|---|---|---|---|---|
| **A. Arabic Admin RTL** | **PASS** (local) | `lang="ar" dir="rtl"`; HOW TO OPERATE removed; full-width cards; E2E `admin_arabic_rtl` 34/34 | `live_control_v4.html`, `admin.css`, `admin.js` | Working-tree only (not in HEAD) |
| **B. SVG Studio** | **PASS** (local) | Template references SVG; HTTP 200 locally; file on disk | `live_display_v4.html` L22–26; `assets/studio/...svg` | **UNTRACKED** — blocker for Git deploy |
| **C. Main plates + final Dubai** | **PASS** (local) | Mapping `dubai → dubai-main-final.png`; aspect 4.734; AA/7777 overlays; E2E 13/13 | `plate-system.js`, asset PNG | Asset **UNTRACKED**; HEAD still `dubai.jpg` |
| **C. dubai_yellow + others** | **PASS** (local) | Mapping intact for other types; yellow classic unchanged in QA | `plate-system.js` | — |
| **D. Floating Plates 15/25/35** | **PASS** (local) | `DENSITY_OPTS=[15,25,35]`; `PACK_DIR=floating_final/`; Admin E2E dens 15/25/35 | `fx-bg-plates.js`, Admin QA | Pack **UNTRACKED**; legacy coded pack deletions uncommitted |
| **E. Character depth/size** | **PASS** (local) | Prototype media scale 1.625; depth entrance; Point/Yellow/Red E2E | `character-prototype-media.js`, `character-controller.js` | Working-tree mods vs HEAD |
| **F. Yellow Card cinematic** | **PASS** (local) | Glow + shake; digits remain; E2E | `fx.css`, `fx-beam-drop.js`, QA yellow/red suites | Working-tree mods |
| **G. Red Card glow + hide** | **PASS** (local) | Cinematic red; digits hidden persist; Show restores; refresh keeps hide | `fx.css`, `fx-beam-drop.js`, `character-controller.js`, `new_style.py` | Working-tree mods |
| **H. SOLD stamp + fireworks** | **PASS** (local) | Red grunge stamp asset + imprint; fireworks play; E2E | `sold-stamp-red.png`, `fx-sold.js`, template img src | Stamp PNG **UNTRACKED** |
| **I. Timer + Live Text** | **PASS** (local) | Timer start/pause/resume; bilingual lines; DjangoBridge patch/poll; Admin E2E | `admin.js`, `django-bridge.js`, `new_style.py` | Working-tree mods |
| **J. Hidden Current Bid** | **PASS** (local) | `.bid { visibility:hidden }`; spacer retained; E2E bid hidden | `broadcast.css`, `live_display_v4.html` | Working-tree mods |
| **K. Number FX / Aging / Beam / Drop** | **PASS** (local) | Controls present + E2E triggered | Admin IDs + handlers | Aging seek remains sandbox-limited in Django mode (pre-existing) |
| **Admin↔Broadcast Django sync** | **PASS** (local) | Same-session Selenium Admin Control + Display-v4 | Prior QA + Admin Arabic suite | Production sync **NOT VERIFIED** |
| **Standalone `h2_live_v4/` required?** | **PASS (not required)** | Django serves templates/static; standalone differs intentionally | Diff hashes: admin/plate/character/fx DIFF; django-bridge SAME | Do not deploy standalone as the live app |
| **Classic / New / TikTok routes** | **PASS** (routing + tests) | URLs present; `plates.tests` 47 OK | `urls.py`, tests | Full visual regression of Classic/TikTok **NOT VERIFIED** beyond automated tests |
| **Production Hostinger live site** | **NOT VERIFIED** | No production credentials/SSH in audit | `DEPLOYMENT.md` only | Must smoke-test after manual deploy |

---

## 4. Static Asset Audit

### Required for approved V4 — **present locally, missing from Git tracking**

Must be included in any manual Git upload / commit before server pull:

```
static/live_v4/assets/plates/dubai-main-final.png
static/live_v4/assets/effects/sold-stamp-red.png
static/live_v4/assets/studio/H2_AUCTIONS_Studio_4K_Vector.svg
static/live_v4/assets/plates/floating_final/abudhabi_1.png
static/live_v4/assets/plates/floating_final/ajman.png
static/live_v4/assets/plates/floating_final/du.png
static/live_v4/assets/plates/floating_final/dubai_A.png
static/live_v4/assets/plates/floating_final/dubai_B.png
static/live_v4/assets/plates/floating_final/dubai_C.png
static/live_v4/assets/plates/floating_final/dubai_classic.png
static/live_v4/assets/plates/floating_final/etisalat.png
static/live_v4/assets/plates/floating_final/fujairah.png
static/live_v4/assets/plates/floating_final/rasalkhaimah.png
static/live_v4/assets/plates/floating_final/sharjah.png
static/live_v4/assets/plates/floating_final/ummalquwain.png
static/live_v4/assets/plates/floating_final/manifest.json
```

Optional / secondary untracked (not required if `floating_final` is the active pack):

- `static/live_v4/assets/plates/dubai-main.png` (superseded by `-final`)
- `static/live_v4/assets/plates/coded/*` newer blank/letter variants

### Tracked character assets (OK)

`static/live_v4/assets/character/prototype_2d/{point,red,yellow}.png` + meta JSON are tracked.

### Modified tracked files that must ship with the release

At minimum (working tree vs `HEAD`):

- `templates/plates/live_control_v4.html`
- `templates/plates/live_display_v4.html`
- `static/live_v4/css/admin.css`
- `static/live_v4/css/broadcast.css`
- `static/live_v4/css/fx.css`
- `static/live_v4/css/plate-system.css`
- `static/live_v4/js/admin.js`
- `static/live_v4/js/django-bridge.js`
- `static/live_v4/js/plate-system.js`
- `static/live_v4/js/fx-beam-drop.js`
- `static/live_v4/js/fx-sold.js`
- `static/live_v4/js/character-controller.js`
- `static/live_v4/js/character-prototype-media.js` (if modified)
- `static/live_v4/js/broadcast.js` / `state-controller.js` / `fx-bg-plates.js` (confirm via `git status`)
- `plates/new_style.py`
- `plates/views.py` (if intentional)

### Deleted tracked legacy floating coded packs

Many `static/live_v4/assets/plates/coded/<legacy>__*.png` show as **deleted** in working tree.  
If you commit those deletions **without** adding `floating_final/`, production Floating Plates will break.

### Path hygiene

- No Windows absolute paths found in V4 template static tags.
- Assets use Django `{% static %}` or relative `./assets/...` resolved under `/static/live_v4/`.
- Local HTTP 200 confirmed for Dubai final, SOLD stamp, studio SVG.
- Source folder `Emirates_plates/` is **not** referenced by the live renderer (correct — copied into `static/live_v4/assets/plates/`).

### Manifest / WhiteNoise note

Production uses `CompressedManifestStaticFilesStorage`. After deploy you **must** run `collectstatic` on the server so hashed filenames exist. Local `staticfiles/` currently contains the critical assets when collected from the working tree.

---

## 5. Regression Test Results

### Django system check

```text
python manage.py check
→ 1 warning (ckeditor.W001) — unrelated to V4
→ exit 0
```

### Migrations (`plates`)

All listed migrations `[X]` applied locally through `0013_livebroadcastsession_new_style_display_token`.  
No pending V4-specific migration identified for the UI asset/JS work.

### Automated tests

```text
python manage.py test plates.tests -v1 --keepdb
→ Ran 47 tests in ~64.5s
→ OK
```

### Local V4 E2E evidence (Django Admin + Display, same session)

| Suite | Result | Location |
|---|---|---|
| Arabic Admin + feature regression | 34/34 PASS | `h2_live_v4/refs/qa/admin_arabic_rtl/` |
| Dubai final plate | 13/13 PASS | `h2_live_v4/refs/qa/dubai_main_final/` |
| Red Card glow | 24/24 PASS (prior) | `h2_live_v4/refs/qa/red_cinematic_glow/` |
| SOLD stamp | 20/20 PASS (prior) | `h2_live_v4/refs/qa/sold_stamp_red/` |
| Yellow glow | prior PASS artifacts | `h2_live_v4/refs/qa/yellow_cinematic_glow/` |

### Standalone vs Django divergence (intentional)

| Pair | Result |
|---|---|
| `h2_live_v4/js/django-bridge.js` ↔ `static/live_v4/js/django-bridge.js` | SAME |
| admin / plate-system / character-controller / fx.css | DIFF |

**Interpretation:** Django `static/live_v4` + templates are the production source of truth. Standalone sandbox may lag or diverge; do not replace Django files blindly from standalone without review.

---

## 6. Deployment Blockers

1. **Untracked critical assets** (Dubai final, SOLD stamp, studio SVG, floating_final pack).
2. **Uncommitted approved code** (Admin Arabic RTL, FX, plate mapping, bridges, bid-slot CSS, etc.).
3. **Publishing GitHub `main` at `a31ad2d` alone would ship pre-approval V4** (old Dubai JPG mapping, old Admin EN/HOW TO OPERATE layout, missing new assets).
4. **Legacy coded float deletions** must be paired with `floating_final` inclusion.
5. **Production server smoke test not performed** — Hostinger paths/services only documented, not observed live.
6. **WhiteNoise ManifestStaticFilesStorage** requires successful `collectstatic` after upload; missing files can hard-fail hashed static resolution.

Non-blockers / warnings:

- CKEditor security warning (pre-existing, unrelated).
- Character Enter/Exit/Reset remain display-local in Django mode (pre-existing design).
- Aging seek is sandbox-limited in Django mode (pre-existing).

---

## 7. Manual Deployment Checklist

> Do **not** invent unconfirmed server details. Follow documented Hostinger flow in `DEPLOYMENT.md` / `deploy.sh`, using your real SSH user/path if they differ.

### A. Local Git actions (you perform — not done by this audit)

1. Review `git status` carefully (include intended adds; avoid unrelated noise if possible).
2. **Add** all required untracked V4 assets listed in §4.
3. **Stage** modified V4 templates/JS/CSS/Python listed in §4.
4. Confirm Floating Plates strategy: keep `floating_final` + accept legacy coded deletions **or** restore legacy if still needed.
5. Create a commit with a clear V4 release message (**you** commit — audit did not).
6. `git push origin main` (or your release branch) when ready.

### B. GitHub

7. Confirm the pushed revision contains the new assets (GitHub file browser / `git ls-tree`).

### C. Server Git update

8. SSH to VPS.
9. `cd` to the documented app root (docs say `/var/www/h3auctions` — confirm on server).
10. `git fetch` + `git checkout`/`git pull` the revision you just pushed.
11. Verify critical files exist on disk:
    - `static/live_v4/assets/plates/dubai-main-final.png`
    - `static/live_v4/assets/effects/sold-stamp-red.png`
    - `static/live_v4/assets/studio/H2_AUCTIONS_Studio_4K_Vector.svg`
    - `static/live_v4/assets/plates/floating_final/`

### D. Python / Django

12. Activate venv.
13. `pip install -r requirements.txt` (if requirements changed; otherwise optional).
14. `python manage.py migrate` (expected no-op for pure UI/asset release, but run).
15. `python manage.py collectstatic --noinput`
16. `python manage.py check`

### E. Process reload

17. Restart app process per your production setup (docs: `sudo supervisorctl restart h3auctions`).
18. Reload Nginx only if config changed (usually not required for static/code pull).

### F. Production smoke tests (mandatory)

19. Open `/live/control/v4/` as superuser (Arabic RTL, no HOW TO OPERATE).
20. Open `/live/display-v4/<token>/` in OBS/browser.
21. Apply Dubai AA/7777 → confirm **final** Dubai art.
22. Live text both lines; timer start/pause.
23. Yellow Card; Red Card hide + Show Number restore.
24. SOLD stamp + fireworks.
25. Floating Plates LOW/MED/HIGH.
26. Confirm bid panel remains hidden.
27. Spot-check Classic / New / TikTok hub links still open.

---

## 8. Rollback Plan

Goal: restore previous production revision **without** deleting the database or unrelated media.

1. On server: note current commit (`git rev-parse HEAD`).
2. `git checkout <previous_known_good_sha>` **or** `git revert` the release commit(s) on a clean pull (prefer revert for shared main).
3. Re-run:
   - `python manage.py migrate` (only if release included migrations; UI-only release should be no-op)
   - `python manage.py collectstatic --noinput`
4. Restart Supervisor app process.
5. Smoke-test Classic + V4 display URLs.
6. Do **not** run destructive DB resets, `git clean -fd`, or delete `media/` / DB dumps as part of rollback.

If static hashed files look stale after rollback, re-run `collectstatic` and hard-refresh OBS Browser Source cache.

---

## Appendix A — Local integration confirmation

- V4 Admin and Broadcast are **Django views**, not the standalone sandbox.
- Sync is **Django `/live/api/state/`** (PATCH + token GET), not localStorage-only.
- `LIVE_V4_ENABLED` gates V4 routes.
- Display is token-based for OBS; Control requires superuser.

## Appendix B — Bottom-line release gate

| Gate | Status |
|---|---|
| Django wiring correct | YES |
| Local feature parity for approved V4 | YES |
| Required files present on disk | YES |
| Required files in Git / pushable revision | **NO** |
| Production deploy verified live | **NO** |

**Final gate decision: NOT READY until the working-tree V4 release (code + untracked assets) is committed, pushed, pulled on the server, collectstatic’d, restarted, and smoke-tested.**

---

*End of audit. No deploy, push, commit, or production changes were performed.*
