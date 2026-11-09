"""Alpha-key H2 Floating Plates Collection into transparent pack assets."""
from __future__ import annotations

import collections
import json
import re
from pathlib import Path

from PIL import Image

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

SRC = Path(r"C:\Users\moham\.cursor\projects\c-Users-moham-h3\assets")
OUT = Path(__file__).resolve().parents[1] / "assets" / "bg_plates" / "pack"

PAT = re.compile(
    r"^(abu_dhabi|ajman|dibba|dubai_white|dubai_yellow|fujairah|"
    r"ras_al_khaimah|sharjah|umm_al_quwain)__([A-Z]{1,2})-([0-9a-f-]{36})\.png$",
    re.I,
)


def key_black(im: Image.Image, thresh: int = 28) -> Image.Image:
    im = im.convert("RGBA")
    if np is not None:
        arr = np.array(im)
        mask = (arr[:, :, 0] <= thresh) & (arr[:, :, 1] <= thresh) & (arr[:, :, 2] <= thresh)
        arr[mask, 3] = 0
        im = Image.fromarray(arr, "RGBA")
    else:
        px = im.load()
        w, h = im.size
        for y in range(h):
            for x in range(w):
                r, g, b, _a = px[x, y]
                if r <= thresh and g <= thresh and b <= thresh:
                    px[x, y] = (0, 0, 0, 0)
    bbox = im.getbbox()
    if not bbox:
        return im
    pad = 4
    w, h = im.size
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(w, bbox[2] + pad)
    bottom = min(h, bbox[3] + pad)
    return im.crop((left, top, right, bottom))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.png"):
        p.unlink()

    candidates: dict[tuple[str, str], list[tuple[str, Path]]] = collections.defaultdict(list)
    for p in SRC.glob("*.png"):
        m = PAT.match(p.name)
        if not m:
            continue
        emirate, code, uid = m.group(1).lower(), m.group(2).upper(), m.group(3).lower()
        candidates[(emirate, code)].append((uid, p))

    manifest = []
    by_emirate: collections.Counter[str] = collections.Counter()
    for (emirate, code), files in sorted(candidates.items()):
        files.sort(key=lambda t: t[0])
        _uid, path = files[-1]
        keyed = key_black(Image.open(path))
        tw = 640
        th = max(1, int(keyed.height * (tw / keyed.width)))
        keyed = keyed.resize((tw, th), Image.Resampling.LANCZOS)
        name = f"{emirate}__{code}.png"
        keyed.save(OUT / name, optimize=True)
        manifest.append({"file": name, "emirate": emirate, "code": code, "w": tw, "h": th})
        by_emirate[emirate] += 1

    note = (
        "Concept artwork — not verified official plate masters. "
        "No registration numbers on floating plates."
    )
    (OUT / "manifest.json").write_text(
        json.dumps({"note": note, "count": len(manifest), "assets": manifest}, indent=2),
        encoding="utf-8",
    )
    (OUT / "MANIFEST.txt").write_text(
        "\n".join(e["file"] for e in manifest) + "\n",
        encoding="utf-8",
    )
    print("unique_pairs", len(manifest))
    print("by_emirate", dict(by_emirate))
    print("out", OUT)


if __name__ == "__main__":
    main()
