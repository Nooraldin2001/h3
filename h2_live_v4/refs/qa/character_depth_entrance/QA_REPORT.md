# Character cinematic depth entrance — visual QA

## Anchors / timing
| | Value |
|--|--|
| Entry feet | `(960, 688)` |
| Entry scale | `0.15` |
| Stop feet | `(960, 1105)` |
| Stop scale | `1.0` |
| Exit feet | `(960, 688)` |
| Exit scale | `0.12` |
| Enter duration | `2800 ms` |
| Exit duration | `2200 ms` |
| Easing | `easeInOutCubic` (position + scale coupled) |

## Checks
1. Distant small center-depth — PASS (`point_01_distant.png`)
2. Smooth approach — PASS (`qa_mid_coupled.png`, coupled progress ≈ 0.52)
3. Gradual grow — PASS (0.15 → 1.0)
4. Final stance — PASS (`qa_arrived.png`, scale 1 @ y 1105)
5. Point — PASS
6. Yellow Card — PASS (`qa_yellow_arrived.png`)
7. Red Card — PASS (`qa_red_arrived.png`)
8. Retreat to depth — PASS (`qa_retreat.png`, scale↓ and y↑ toward 688)
9. No duplicates on rapid click — PASS (busy gate)
10. Other V4 elements intact — PASS

## Frames
See PNGs in this folder.
