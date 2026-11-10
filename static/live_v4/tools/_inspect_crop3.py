from PIL import Image
from pathlib import Path
p = Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\plate-redesign\after-dubai-crop.png")
im = Image.open(p).convert("RGB"); w,h=im.size; px=im.load()
def is_dark(x,y,t=40):
    r,g,b=px[x,y]; return r<=t and g<=t and b<=t
def is_white(x,y,t=220):
    r,g,b=px[x,y]; return r>=t and g>=t and b>=t
xs=[]; ys=[]
for y in range(h):
  for x in range(w):
    if is_white(x,y):
      xs.append(x); ys.append(y)
L,R,T,B=min(xs),max(xs),min(ys),max(ys)
print("white bbox", L,T,R,B)
print("TL", px[L,T], px[L+1,T+1], px[L+3,T+3])
print("BL", px[L,B], px[L+1,B-1], px[L+3,B-3])
print("TR", px[R,T], px[R-1,T+1])
print("BR", px[R,B], px[R-1,B-1])
# count white pixels that are outer-most on each side (potential halo)
halo=0
for x in range(L,R+1):
  if is_white(x,T) and not is_dark(x,T):
    # if row above is dark stage, this is outer edge
    if T>0 and is_dark(x,T-1):
      # check if black border missing: neighbor inside should be white too
      if is_white(x,T+2): halo+=1
print("top outer white-without-dark-edge count", halo)
