from PIL import Image
from pathlib import Path
p = Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\plate-redesign\after-dubai-crop.png")
im = Image.open(p).convert("RGB"); w,h=im.size; px=im.load()
def is_dark(x,y,t=45):
    r,g,b=px[x,y]; return r<=t and g<=t and b<=t
def is_white(x,y,t=230):
    r,g,b=px[x,y]; return r>=t and g>=t and b>=t
# find non-dark plate region
pts=[(x,y) for y in range(h) for x in range(w) if not is_dark(x,y)]
xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
L,R,T,B=min(xs),max(xs),min(ys),max(ys)
print("plate bbox", L,T,R,B, R-L+1, B-T+1)
print("edge mid top", px[(L+R)//2, T], px[(L+R)//2, T+1], px[(L+R)//2, T+2], px[(L+R)//2, T+8])
print("edge mid bot", px[(L+R)//2, B], px[(L+R)//2, B-1], px[(L+R)//2, B-8])
print("edge mid left", px[L,(T+B)//2], px[L+1,(T+B)//2], px[L+8,(T+B)//2])
print("TL corner path:")
for i in range(10):
    print(i, px[L+i,T+i])
# also dubai_yellow
p2=Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\plate-redesign\after-dubai_yellow-crop.png")
im2=Image.open(p2).convert("RGB"); w2,h2=im2.size; px2=im2.load()
def dark2(x,y,t=45):
    r,g,b=px2[x,y]; return r<=t and g<=t and b<=t
pts2=[(x,y) for y in range(h2) for x in range(w2) if not dark2(x,y)]
xs2=[p[0] for p in pts2]; ys2=[p[1] for p in pts2]
L2,R2,T2,B2=min(xs2),max(xs2),min(ys2),max(ys2)
print("yellow bbox", L2,T2,R2,B2)
print("yellow top mid", px2[(L2+R2)//2,T2], px2[(L2+R2)//2,T2+3], px2[(L2+R2)//2,T2+10])
