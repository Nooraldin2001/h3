from pathlib import Path
from PIL import Image

src = Path(
    r"C:\Users\moham\.cursor\projects\c-Users-moham-h3\assets"
    r"\H2_AUCTIONS_Studio_4K_Vector-7758613a-4419-449e-bab4-8a4fa4f2a268.png"
)
studio = Path(r"c:\Users\moham\h3\h2_live_v4\assets\studio")
studio.mkdir(parents=True, exist_ok=True)

im = Image.open(src)
print("src", im.size, im.mode, im.format)
rgba = im.convert("RGBA")
a_min, a_max = rgba.getchannel("A").getextrema()
print("alpha extrema", a_min, a_max)

# Keep alpha if meaningful; otherwise RGB for max decoder compatibility
if a_min >= 250:
    out = rgba.convert("RGB")
else:
    out = rgba

png_path = studio / "H2_AUCTIONS_Studio_3840x2160.png"
out.save(png_path, format="PNG", optimize=True)
print("png", png_path, png_path.stat().st_size, Image.open(png_path).size)

# Broadcast-sized JPEG fallback (same 16:9 pixels upscaled once for OBS sharpness)
jpg = out.convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
jpg_path = studio / "H2_AUCTIONS_Studio_1920x1080.jpg"
jpg.save(jpg_path, format="JPEG", quality=93, optimize=True)
print("jpg", jpg_path, jpg_path.stat().st_size, Image.open(jpg_path).size)

# Native-pixel clean PNG alias
alias = studio / "H2_AUCTIONS_Studio_native.png"
out.save(alias, format="PNG", optimize=True)
print("alias", alias.stat().st_size)
