from PIL import Image
from pathlib import Path
import collections

p = Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\plate-redesign\after-dubai-crop.png")
im = Image.open(p).convert("RGB")
w,h = im.size
px = im.load()
# find plate bbox: non-dark pixels
def is_dark(x,y,t=35):
    r,g,b=px[x,y]
    return r<=t and g<=t and b<=t
def is_white(x,y,t=230):
    r,g,b=px[x,y]
    return r>=t and g>=t and b>=t
# scan rows for plate
ys=[y for y in range(h) if sum(1 for x in range(w) if not is_dark(x,y)) > w*0.2]
xs=[x for x in range(w) if sum(1 for y in range(h) if not is_dark(x,y)) > h*0.08]
print("crop", w,h, "plate_y", min(ys), max(ys), "plate_x", min(xs), max(xs))
top,bot,left,right = min(ys), max(ys), min(xs), max(xs)
# inspect top edge strip of plate
print("top edge samples y=top..top+6")
for dy in range(0,8):
    y=top+dy
    whites=sum(1 for x in range(left,right+1) if is_white(x,y))
    darks=sum(1 for x in range(left,right+1) if is_dark(x,y))
    print(f"  y={y} white={whites} dark={darks} mid={px[(left+right)//2,y]}")
# corner zoom top-left
print("TL corner 12x12:")
for y in range(top, top+12):
    row=[]
    for x in range(left, left+12):
        r,g,b=px[x,y]
        row.append("W" if is_white(x,y) else ("D" if is_dark(x,y) else "."))
    print("".join(row))
