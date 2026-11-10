from PIL import Image
from pathlib import Path

def trim_tight(path, thresh=240):
    im = Image.open(path)
    has_alpha = im.mode in ("RGBA", "LA") or ("transparency" in im.info)
    rgb = im.convert("RGBA" if has_alpha else "RGB")
    w, h = rgb.size
    px = rgb.load()
    def is_pad(x, y):
        c = px[x, y]
        if len(c) == 4:
            r,g,b,a = c
            if a < 8: return True
            return r >= thresh and g >= thresh and b >= thresh and a > 200
        r,g,b = c
        return r >= thresh and g >= thresh and b >= thresh
    top=0
    while top < h and all(is_pad(x, top) for x in range(0, w, max(1, w//160))): top += 1
    bot=h-1
    while bot >= 0 and all(is_pad(x, bot) for x in range(0, w, max(1, w//160))): bot -= 1
    left=0
    while left < w and all(is_pad(left, y) for y in range(0, h, max(1, h//80))): left += 1
    right=w-1
    while right >= 0 and all(is_pad(right, y) for y in range(0, h, max(1, h//80))): right -= 1
    # also nibble 1px if edge is mostly white
    def edge_white_ratio(side):
        if side=='top':
            ys=top; xs=range(left, right+1)
            return sum(1 for x in xs if is_pad(x, ys)) / max(1, right-left+1)
        if side=='bot':
            ys=bot; xs=range(left, right+1)
            return sum(1 for x in xs if is_pad(x, ys)) / max(1, right-left+1)
        if side=='left':
            xs=left; ys=range(top, bot+1)
            return sum(1 for y in ys if is_pad(xs, y)) / max(1, bot-top+1)
        xs=right; ys=range(top, bot+1)
        return sum(1 for y in ys if is_pad(xs, y)) / max(1, bot-top+1)
    while top < bot and edge_white_ratio('top') > 0.55: top += 1
    while bot > top and edge_white_ratio('bot') > 0.55: bot -= 1
    while left < right and edge_white_ratio('left') > 0.55: left += 1
    while right > left and edge_white_ratio('right') > 0.55: right -= 1
    cropped = rgb.crop((left, top, right+1, bot+1))
    before = (w,h)
    after = cropped.size
    if after != before:
        save_kwargs = {}
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            cropped = cropped.convert("RGB")
            save_kwargs = dict(quality=95, optimize=True)
        cropped.save(path, **save_kwargs)
    return before, after, (left, top, w-1-right, h-1-bot)

roots = [
    Path(r"c:\Users\moham\h3\static\live_v4\assets\plates"),
    Path(r"c:\Users\moham\h3\h2_live_v4\assets\plates"),
]
names = ["dubai.jpg","sharjah.jpg","abudhabi.jpg","ajman.jpg","dubai_classic.jpg","fujairah.jpg","rasalkhimma.jpg","ummalquain.jpg"]
for root in roots:
    print("==", root)
    for name in names:
        p = root / name
        b,a,pad = trim_tight(p)
        print(f"  {name}: {b} -> {a} pad={pad} aspect={a[0]/a[1]:.4f}")
