# H2 Live V4 — Safe Rollback Report

**Date:** 2026-11-10  
**Working revision restored:** `a31ad2d` (`Wire H2 Live V4 into Django with separate control and display routes.`)  
**Method:** `git checkout HEAD -- <paths>` only (no `reset --hard`, no `clean`)

---

## Root context

Active broadcast is **Django**, not the sandbox:

- URL: `http://127.0.0.1:8000/live/display-v4/<token>/`
- Template: `templates/plates/live_display_v4.html`
- Assets: `static/live_v4/...`

Sandbox-only experiments never affected that path.

---

## Backup before restore

`h2_live_v4/refs/qa/_rollback_backup_2026-11-10/`

- `experiment-changes.patch`
- Snapshots of key HTML/JS/CSS from the experiment tree

---

## Files restored from HEAD

- `templates/plates/live_display_v4.html`
- `static/live_v4/css/{broadcast,fx,plate-system}.css`
- `static/live_v4/js/{broadcast,plate-system,character-controller,fx-beam-drop}.js`
- `static/live_v4/assets/plates/*`
- Matching `h2_live_v4/` CSS/JS/`index.html`/plates (sandbox mirror)

## Removed from active path

- `static/live_v4/js/display-config.js` (untracked hide flag)
- `h2_live_v4/js/display-config.js`

## Intentionally preserved (untracked / unused)

- `h2_live_v4/assets/studio/` (new studio pack — not referenced)
- QA folders / reports / tools under `h2_live_v4/refs/qa/` and `*/tools/`
- `PLATE_REDESIGN_REPORT.md`, `STUDIO_LAYER_REPORT.md`

---

## Verification

Active URL tested:

`http://127.0.0.1:8000/live/display-v4/b747d8ca-8593-4ec0-b095-4d90a95233c4/`

| Check | Result |
|---|---|
| Original `studio-stage.jpg` | Yes (+ brightness 1.4 styling) |
| `H2V4DisplayConfig` absent | Yes |
| Main `#plate` visible | Yes (`display: grid`, ~760×204) |
| Hide flag inactive | Yes |
| Logo / timer / bid | Yes |
| Screenshot | `refs/qa/studio-layer/django-display-v4-restored-1920.png` |

Note: live session currently shows **Etisalat** phone plate (server state). That is expected Admin sync — not a hide failure.

---

## Remaining differences vs pristine HEAD

None in active renderer paths. Untracked experiment artifacts remain on disk but are not loaded.
