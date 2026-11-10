from PIL import Image
from pathlib import Path

p = Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio-layer\01-broadcast-normal-1920.png")
im = Image.open(p).convert("RGB")
print("size", im.size)
pts = [(960, 80), (960, 120), (400, 100), (1520, 100), (960, 900), (200, 500), (960, 400)]
for pt in pts:
    print(pt, im.getpixel(pt))

w, h = im.size
gold = 0
dark = 0
for y in range(0, h, 8):
    for x in range(0, w, 8):
        r, g, b = im.getpixel((x, y))
        if r > 40 and g > 25 and b < 40 and r > b + 10:
            gold += 1
        if r < 15 and g < 15 and b < 15:
            dark += 1
print("goldish samples", gold, "near-black", dark)

sj = Image.open(
    r"c:\Users\moham\h3\h2_live_v4\assets\studio\H2_AUCTIONS_Studio_1920x1080.jpg"
).convert("RGB")
print(
    "studio jpg samples",
    sj.getpixel((960, 80)),
    sj.getpixel((960, 900)),
    sj.getpixel((960, 400)),
)

# Also check plate-hidden shot
p2 = Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio-layer\03-plate-hidden-studio-intact-1920.png")
im2 = Image.open(p2).convert("RGB")
print("hidden shot", im2.getpixel((960, 80)), im2.getpixel((960, 900)))
