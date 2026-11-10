"""Build manifest.json for the final 12 floating plate assets."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "assets" / "plates" / "floating_final"

# Explicit mapping for the approved final set (filename → emirate, code).
MAPPING = {
    "dubai_A.png": ("dubai", "A"),
    "dubai_B.png": ("dubai", "B"),
    "dubai_C.png": ("dubai", "C"),
    "dubai_classic.png": ("dubai_classic", ""),
    "abudhabi_1.png": ("abudhabi", "1"),
    "sharjah.png": ("sharjah", ""),
    "ajman.png": ("ajman", ""),
    "rasalkhaimah.png": ("rasalkhaimah", ""),
    "ummalquwain.png": ("ummalquwain", ""),
    "fujairah.png": ("fujairah", ""),
    "du.png": ("du", ""),
    "etisalat.png": ("etisalat", ""),
}


def main() -> None:
    assets = []
    missing = []
    for name, (emirate, code) in MAPPING.items():
        path = ROOT / name
        if not path.exists():
            missing.append(name)
            continue
        im = Image.open(path)
        w, h = im.size
        assets.append(
            {
                "file": name,
                "emirate": emirate,
                "code": code,
                "w": w,
                "h": h,
            }
        )

    extras = sorted(
        p.name for p in ROOT.glob("*.png") if p.name not in MAPPING
    )
    if missing:
        raise SystemExit(f"missing approved files: {missing}")
    if extras:
        print("WARNING excluding non-approved extras:", extras)

    manifest = {
        "note": (
            "Final approved floating plates (12). Letter/blank artwork only — "
            "no registration numbers. Source: h2_live_v4/assets/plates/coded/"
        ),
        "count": len(assets),
        "assets": assets,
    }
    out = ROOT / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {out} count={len(assets)}")
    for a in assets:
        print(
            f"  {a['file']:22} emirate={a['emirate']:14} "
            f"code={(a['code'] or '(none)'):6} {a['w']}x{a['h']}"
        )


if __name__ == "__main__":
    main()
