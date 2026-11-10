"""Lossless trim of near-white canvas padding from V4 plate JPGs. Writes trimmed copies + report."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "assets" / "plates"
OUT_DIR = ROOT  # overwrite V4 copies only (not live_new)
REPORT = Path(__file__).resolve().parents[1].parent.parent / "h2_live_v4" / "refs" / "qa" / "plate-redesign"
REPORT.mkdir(parents=True, exist_ok=True)

# Also mirror into sandbox
SANDBOX = Path(__file__).resolve().parents[1].parent.parent / "h2_live_v4" / "assets" / "plates"


def content_bbox(im: Image.Image, thr: int = 242, dark_thr: int = 230):
    """Find bounding box of non-near-white content (keeps plate white face + dark border)."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()

    def is_canvas(x, y):
        r, g, b = px[x, y]
        # near-uniform white canvas outside the physical plate
        return r >= thr and g >= thr and b >= thr and abs(r - g) < 8 and abs(g - b) < 8

    # sample density
    step_x = max(1, w // 400)
    step_y = max(1, h // 120)

    top = 0
    while top < h and all(is_canvas(x, top) for x in range(0, w, step_x)):
        top += 1
    bottom = h - 1
    while bottom > top and all(is_canvas(x, bottom) for x in range(0, w, step_x)):
        bottom -= 1
    left = 0
    while left < w and all(is_canvas(left, y) for y in range(top, bottom + 1, step_y)):
        left += 1
    right = w - 1
    while right > left and all(is_canvas(right, y) for y in range(top, bottom + 1, step_y)):
        right -= 1

    # small inset safety — do not eat the real border
    pad = 1
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(w - 1, right + pad)
    bottom = min(h - 1, bottom + pad)
    return left, top, right + 1, bottom + 1


def main():
    results = []
    for src in sorted(OUT_DIR.glob("*")):
        if src.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        # Prefer jpeg phone frames over mislabeled dubai duplicates
        if src.name in {"du.png", "etisalat.png"}:
            continue
        im = Image.open(src)
        box = content_bbox(im)
        l, t, r, b = box
        trimmed = im.crop(box)
        tw, th = trimmed.size
        changed = (l, t, r, b) != (0, 0, im.size[0], im.size[1]) and (t > 2 or b < im.size[1] - 2 or l > 2 or r < im.size[0] - 2)
        info = {
            "file": src.name,
            "before": {"w": im.size[0], "h": im.size[1], "aspect": round(im.size[0] / im.size[1], 3)},
            "crop": {"left": l, "top": t, "right": r, "bottom": b},
            "after": {"w": tw, "h": th, "aspect": round(tw / th, 3)},
            "trimmed": bool(changed and (t > 3 or (im.size[1] - b) > 3)),
        }
        if info["trimmed"] or src.name.endswith(".jpeg"):
            # save trimmed / ensure phone jpegs used
            out_name = src.name
            if out_name.endswith(".jpeg"):
                # keep as jpeg for du/etisalat
                trimmed.convert("RGB").save(OUT_DIR / out_name, quality=95, optimize=True)
            else:
                trimmed.convert("RGB").save(OUT_DIR / out_name, quality=95, optimize=True)
            if SANDBOX.exists():
                trimmed.convert("RGB").save(SANDBOX / out_name, quality=95, optimize=True)
        results.append(info)
        print(json.dumps(info))

    # Copy classic RGBA phone masters into V4 as preferred phone assets
    classic = Path(r"c:\Users\moham\h3\static\plates")
    for name in ("du.png", "etisalat.png"):
        src = classic / name
        if src.exists():
            im = Image.open(src)
            im.save(OUT_DIR / name)
            if SANDBOX.exists():
                im.save(SANDBOX / name)
            results.append({"file": name, "source": "classic_rgba", "w": im.size[0], "h": im.size[1]})
            print("copied", name, im.size, im.mode)

    (REPORT / "plate-trim-report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", REPORT / "plate-trim-report.json")


if __name__ == "__main__":
    main()
