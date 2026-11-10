from PIL import Image, ImageEnhance, ImageStat

sj = Image.open(
    r"c:\Users\moham\h3\h2_live_v4\assets\studio\H2_AUCTIONS_Studio_1920x1080.jpg"
).convert("RGB")
w, h = sj.size
# find brightest pixels
bright = []
for y in range(0, h, 4):
    for x in range(0, w, 4):
        r, g, b = sj.getpixel((x, y))
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if lum > 35:
            bright.append((lum, x, y, (r, g, b)))
bright.sort(reverse=True)
print("top bright", bright[:15])
print("count lum>35", len(bright), "of", (w // 4) * (h // 4))
st = ImageStat.Stat(sj)
print("mean", st.mean, "extrema", st.extrema)

# bake a lightly lifted version for broadcast readability
lifted = ImageEnhance.Brightness(sj).enhance(1.55)
lifted = ImageEnhance.Contrast(lifted).enhance(1.2)
lifted = ImageEnhance.Color(lifted).enhance(1.15)
out = r"c:\Users\moham\h3\h2_live_v4\assets\studio\H2_AUCTIONS_Studio_1920x1080.jpg"
lifted.save(out, format="JPEG", quality=93, optimize=True)
print("saved lifted", ImageStat.Stat(lifted).mean)

# also save a preview
lifted.save(
    r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio-layer\studio-lifted-preview.jpg",
    format="JPEG",
    quality=90,
)
