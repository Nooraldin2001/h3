"""Measure per-digit ink bbox from plate PNG (luma < 80)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


def luma(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def measure_png(path: Path, luma_thresh: float = 80) -> dict:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()

    ink: list[tuple[int, int]] = []
    col_has_ink = [0] * w
    for y in range(h):
        for x in range(w):
            if luma(px[x, y]) < luma_thresh:
                ink.append((x, y))
                col_has_ink[x] = 1

    if not ink:
        return {"path": str(path), "error": "no ink pixels", "size": [w, h]}

    # Column boundaries: gaps where no ink in full height (with small tolerance)
    gaps: list[tuple[int, int]] = []
    in_gap = False
    gap_start = 0
    for x in range(w):
        if col_has_ink[x] == 0:
            if not in_gap:
                in_gap = True
                gap_start = x
        else:
            if in_gap:
                gaps.append((gap_start, x))
                in_gap = False
    if in_gap:
        gaps.append((gap_start, w))

    # Pick the 3 widest internal gaps between digit clusters
    digit_gaps = [g for g in gaps if g[1] - g[0] >= 2]
    if len(digit_gaps) >= 3:
        digit_gaps.sort(key=lambda g: g[1] - g[0], reverse=True)
        use = sorted(digit_gaps[:3], key=lambda g: g[0])
        bounds = [0]
        for a, b in use:
            bounds.append((a + b) // 2)
        bounds.append(w)
    else:
        # Fallback: equal quarters of ink span
        xs = [p[0] for p in ink]
        x0, x1 = min(xs), max(xs)
        span = x1 - x0 + 1
        q = span / 4
        bounds = [int(x0 + i * q) for i in range(5)]
        bounds[0] = x0
        bounds[-1] = x1 + 1

    digits: list[dict] = []
    labels = ["digit0", "digit1", "digit2", "digit3"]
    for i in range(4):
        x_lo, x_hi = bounds[i], bounds[i + 1]
        col_ink = [(x, y) for x, y in ink if x_lo <= x < x_hi]
        if not col_ink:
            digits.append(
                {
                    "index": i,
                    "label": labels[i],
                    "x_range": [x_lo, x_hi],
                    "ink_top": None,
                    "ink_bottom": None,
                    "ink_height_px": 0,
                }
            )
            continue
        ys = [y for _, y in col_ink]
        top, bottom = min(ys), max(ys)
        digits.append(
            {
                "index": i,
                "label": labels[i],
                "x_range": [x_lo, x_hi],
                "ink_top": top,
                "ink_bottom": bottom,
                "ink_height_px": bottom - top + 1,
            }
        )

    d0, d1, d2, d3 = digits
    h1_left = d0["ink_height_px"]
    h7 = d1["ink_height_px"]
    h5 = d2["ink_height_px"]
    h1_right = d3["ink_height_px"]
    ref = max(h7, h5)
    ones = [h1_left, h1_right]
    max_one = max(ones)
    threshold = ref * 1.05 if ref else None
    css_fail = bool(threshold is not None and max_one > threshold)

    return {
        "path": str(path),
        "name": path.name,
        "size_px": [w, h],
        "luma_threshold": luma_thresh,
        "column_bounds_x": bounds,
        "digits": digits,
        "interpretation": {"digit0": "1", "digit1": "7", "digit2": "5", "digit3": "1"},
        "heights": {
            "one_left_px": h1_left,
            "seven_px": h7,
            "five_px": h5,
            "one_right_px": h1_right,
            "max_sibling_7_5_px": ref,
        },
        "comparison": {
            "max_one_height_px": max_one,
            "max_sibling_height_px": ref,
            "fail_threshold_px": round(threshold, 3) if threshold is not None else None,
            "one_over_sibling_ratio": round(max_one / ref, 4) if ref else None,
            "one_taller_than_5pct": css_fail,
            "margin_px": round(max_one - ref, 3) if ref else None,
        },
        "css_fix_failed_visually": css_fail,
        "verdict": "fail" if css_fail else "pass",
    }


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print("usage: script <png> [...]", file=sys.stderr)
        return 2
    out = {"images": [measure_png(p) for p in paths]}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
