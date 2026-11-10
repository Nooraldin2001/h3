"""Build manifest.json for floating coded plate pack."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "assets" / "plates" / "coded"


def main() -> None:
    assets = []
    for path in sorted(ROOT.glob("*.png")):
        im = Image.open(path)
        w, h = im.size
        stem = path.stem
        if stem.endswith("_blank"):
            emirate = stem[: -len("_blank")]
            code = ""
        else:
            emirate, code = stem.rsplit("_", 1)
        assets.append(
            {
                "file": path.name,
                "emirate": emirate,
                "code": code,
                "w": w,
                "h": h,
            }
        )

    manifest = {
        "note": (
            "Coded floating plates — letter/blank artwork only, "
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
            f"  {a['file']:24} emirate={a['emirate']:16} "
            f"code={(a['code'] or '(blank)'):8} {a['w']}x{a['h']}"
        )


if __name__ == "__main__":
    main()
