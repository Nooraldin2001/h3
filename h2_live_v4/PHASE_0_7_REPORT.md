# H2 Live V4 — Phases 0–7 Completion Report

**Branch / cwd:** `feature/h2-live-v4` · `c:\Users\moham\h3`  
**Scope:** `h2_live_v4/` only · Phase 8 (Django API) **not** executed · No commit/push/deploy

## Summary

Phases 0–7 are implemented in the V4 sandbox. Automated Selenium QA at 1920×1080 passed (`refs/qa/phase-report.json` → `"ok": true`). Black-and-gold base layout preserved. Missing production assets are gated and reported as incomplete (not fabricated).

## Phase results

| Phase | Status | Evidence |
|-------|--------|----------|
| 0 Restore `index.html` | Done | Preview loads; `refs/qa/phases/phase0-base-1920x1080.png` |
| 1 Plate system (10 types) | Done | Native aspects; geometry stills under `refs/qa/geometry/` |
| 2 Mock state bus | Done | Seed-on-load does not replay sold/beam; new bump fires once |
| 3 Plate-local FX | Done | Sold/FW/beam/drop screenshots in `refs/qa/phases/` |
| 4 Aging | Done | Progress ~0.77 with `?aging=1`; interim crack paths |
| 5 Ambient floats | Done | **339** alpha-keyed PNGs in `assets/bg_plates/`; motion off by default (`?bg=1`) |
| 6 Character | Architecture done / assets incomplete | Meta `status: missing`; CHAR-* suite SKIP until WebMs; z-order PASS |
| 7 Debug + OBS matrix | Done | `?debug=1`; 1280 preview scale ~0.667 |

## Verified layout / stacking

- Stage 1920×1080
- Order: brand → timer → plate → bid
- z-index: character **9** > stack **8**; brand **10** > character
- Fireworks canvas z behind plate-shell
- Preview scale at 1280×720 applied on `#stage`

## Incomplete effects (honest)

1. **Character WebMs** — absent; cue-synced stamp/point/card contact not live until measured meta.
2. **Character meta** — all four JSON files `status: "missing"`.
3. **Aging cracks** — procedural/SVG **interim**, not production masks (`H2V4AgingFx.ASSET_TIER = interim`).
4. **Floating letter plates** — 339 codes alpha-keyed into `assets/bg_plates/` (outer black transparent). Letter coverage still incomplete beyond the staged drop.
5. **Studio / plate fidelity** — soft upscaled studio + marketplace plate JPGs (see `MISSING_ASSETS.md`).
6. **Phase 8** — not in plan todos / not wired to `/live/api/state/`.

## How to preview

```bash
cd h2_live_v4
python -m http.server 8766
```

- Base: http://127.0.0.1:8766/
- Types: `?plate_type=sharjah` · phones: `?plate_type=du&phone=0501234567`
- Aging demo: `?aging=1` · floats: `?bg=1` · debug: `?debug=1`
- QA hotkeys (Alt+): `b` beam, `d` drop, `f` sold, `y` yellow, `e` red, `p` point, `s` sold_stamp

## Screenshot index

- Base: [refs/qa/phases/phase0-base-1920x1080.png](refs/qa/phases/phase0-base-1920x1080.png)
- Sold/FW: [refs/qa/phases/phase3-sold-fw.png](refs/qa/phases/phase3-sold-fw.png)
- Beam / drop / aging / floats / character-incomplete / debug / 1280 preview under `refs/qa/phases/`
- All 10 plate types under `refs/qa/geometry/`
- Machine report: [refs/qa/phase-report.json](refs/qa/phase-report.json)

## Production-readiness

**Not production-ready for OBS final claim.** Architecture and base broadcast layout are in place for continued asset drop-in. Blockers: native studio still, sharp plates, character WebMs + measured cues, alpha-keyed floats, authored crack masks, Stage F API wire.
