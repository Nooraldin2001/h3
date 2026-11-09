# SOLD Fireworks Visibility QA

**Result:** `PASS`

## Root cause
Fireworks previously drew on #plate-fw inside #plate, behind opaque .plate-shell art. Particles existed on the canvas but were visually covered by the white plate and confined under .stack. Fixed by moving to full-stage #stage-fw (1920×1080, z-index 3) above ambient plates and below the auction stack, with rockets exploding in upper L/R studio.

- admin-1920 visible: True gold_delta=96728 fw_peak=390878
- admin-1600 visible: True gold_delta=62462 fw_peak=318798
- direct-1280: {'gold_delta': 159656, 'diff': {'mean_abs_diff': 37.94196662808642, 'changed_px': 523923, 'changed_left': 176704, 'changed_right': 172025, 'changed_upper': 399733, 'changed_frac': 0.2526634837962963}, 'fw_lit_sample': 0, 'visible': True}
