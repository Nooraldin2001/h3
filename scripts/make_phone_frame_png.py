from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "number"
OUT_DIRS = [
    ROOT / "static" / "plates",
    ROOT / "static" / "live_new" / "plates",
    SRC_DIR,
]


def make_exterior_transparent(img: Image.Image, threshold: int = 245) -> Image.Image:
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    visited = [[False] * h for _ in range(w)]
    stack = []
    for x in range(w):
        stack.append((x, 0))
        stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y))
        stack.append((w - 1, y))

    def is_bg(x, y):
        r, g, b, a = pixels[x, y]
        return a > 0 and r >= threshold and g >= threshold and b >= threshold

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[x][y]:
            continue
        visited[x][y] = True
        if not is_bg(x, y):
            continue
        pixels[x, y] = (255, 255, 255, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def main():
    for name in ("du", "etisalat"):
        src = SRC_DIR / f"{name}.jpeg"
        img = Image.open(src)
        out = make_exterior_transparent(img)
        for d in OUT_DIRS:
            d.mkdir(parents=True, exist_ok=True)
            out_path = d / f"{name}.png"
            out.save(out_path, "PNG")
            if d != SRC_DIR:
                Image.open(src).convert("RGB").save(d / f"{name}.jpeg", "JPEG", quality=95)
            print("wrote", out_path)
    print("done")


if __name__ == "__main__":
    main()
