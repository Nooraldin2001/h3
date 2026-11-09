# H2 Auctions V4 — Gulf Presenter Starter Pack

## Supplied
- `references/presenter_identity_pose_sheet.png`: visual identity/pose reference. **Not a transparent animation or source character rig.**
- `storyboards/*.png`: cinematic entrance/exit and action references, **not video assets**.
- `overlays/yellow_card.svg` / `red_card.svg`: actual transparent vector flat-color card assets.
- `overlays/yellow_frame.svg` / `red_frame.svg`: actual transparent vector warning outlines, conceptual. For final use, the glow should be generated from the exact rendered plate bounds; never stretch across incompatible aspect ratios without validation.
- `metadata/{point,yellow,red,sold_stamp}.json`: unmeasured placeholders, deliberately status `missing`.

## NOT INCLUDED — MUST BE PRODUCED BEFORE CHARACTER FUNCTIONAL QA
- Real alpha-preserving, same-person `point.webm`, `yellow.webm`, `red.webm`, `sold_stamp.webm` with natural walking and card/stamp gestures.
- Motion-specific authored entry/exit from below screen center at X=960. To walk toward the podium the actor initially requires a rear or 3/4 back view and physically appropriate perspective.
- Actual measured cue/contact times, foot/card/stamp anchors, interaction alignment, alpha validation.

## Integration rules
- Treat PNG references as visual guidance only. DO NOT display reference collage as on-stage character.
- Keep character disabled when WebMs are missing. Do not animate a still by CSS translation and claim walking.
- Card frames are plate-shell-local. Red hides actual number glyphs, not blurring plate.
- Character enters from bottom center only upon operator trigger, and exits bottom center.
- No production files were modified.
