from PIL import Image
from pathlib import Path
p = Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\plate-redesign\after-dubai-crop.png")
im = Image.open(p).convert("RGB"); w,h=im.size; px=im.load()
def is_dark(x,y,t=40):
    r,g,b=px[x,y]; return r<=t and g<=t and b<=t
def is_white(x,y,t=220):
    r,g,b=px[x,y]; return r>=t and g>=t and b>=t
# find first white row (plate body)
for y in range(h):
    whites=sum(1 for x in range(w) if is_white(x,y))
    if whites>100:
        print("first white-heavy row", y, "whites", whites)
        # find left edge of white on this row
        xs=[x for x in range(w) if is_white(x,y)]
        print(" white x range", min(xs), max(xs))
        # print pixels left of white
        x0=min(xs)
        for x in range(max(0,x0-8), x0+4):
            print(" ", x,y, px[x,y])
        break
# check corners around plate body
# find bbox of white
xs=[]; ys=[]
for y in range(h):
  for x in range(w):
    if is_white(x,y):
      xs.append(x); ys.append(y)
L,R,T,B=min(xs),max(xs),min(ys),max(ys)
print("white bbox", L,T,R,B, "size", R-L+1, B-T+1)
# outside white bbox but non-dark near corners?
for label, pts in {
 'TL':[(L-2,T-2),(L-1,T-1),(L,T),(L+2,T+2)],
 'TR':[(R+2,T-2),(R+1,T-1),(R,T),(R-2,T+2)],
 'BL':[(L-2,B+2),(L-1,B+1),(L,B),(L+2,B-2)],
 'BR':[(R+2,B+2),(R+1,B+1),(R,B),(R-2,B-2)],
}.items():
  print(label, [(pt, px[pt] if 0<=pt[0]<w and 0<=pt[1]<h else None) for pt in pts])
# count white pixels outside black frame: scan from outer plate non-dark bbox
