from PIL import Image
from pathlib import Path

def content_and_frame(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    # near-white outer
    def white(x,y,t=248):
        r,g,b = px[x,y]
        return r>=t and g>=t and b>=t
    def dark(x,y,t=40):
        r,g,b = px[x,y]
        return r<=t and g<=t and b<=t
    # find first non-white from each edge
    top=0
    while top<h and all(white(x,top) for x in range(0,w,max(1,w//120))): top+=1
    bot=h-1
    while bot>=0 and all(white(x,bot) for x in range(0,w,max(1,w//120))): bot-=1
    left=0
    while left<w and all(white(left,y) for y in range(0,h,max(1,h//60))): left+=1
    right=w-1
    while right>=0 and all(white(right,y) for y in range(0,h,max(1,h//60))): right-=1
    # from content edge, find black frame thickness
    # sample mid edges
    def frame_in(side):
        if side=='top':
            y=top
            while y<min(h, top+20) and not any(dark(x,y) for x in range(left, right+1, max(1,(right-left)//40))):
                y+=1
            y2=y
            while y2<min(h, y+20) and any(dark(x,y2) for x in range(left, right+1, max(1,(right-left)//40))):
                y2+=1
            return y-top, y2-y
        if side=='left':
            x=left
            while x<min(w, left+20) and not any(dark(x,y) for y in range(top, bot+1, max(1,(bot-top)//20))):
                x+=1
            x2=x
            while x2<min(w, x+20) and any(dark(x2,y) for y in range(top, bot+1, max(1,(bot-top)//20))):
                x2+=1
            return x-left, x2-x
        return None
    print(f"{Path(path).name:22} {w}x{h} white_pad LTRB=({left},{top},{w-1-right},{h-1-bot}) content={right-left+1}x{bot-top+1} frameTop={frame_in('top')} frameLeft={frame_in('left')}")

base = Path(r"c:\Users\moham\h3\static\live_v4\assets\plates")
for name in ["dubai.jpg","sharjah.jpg","abudhabi.jpg","ajman.jpg","dubai_classic.jpg","fujairah.jpg","rasalkhimma.jpg","ummalquain.jpg","du.png","etisalat.png"]:
    content_and_frame(base/name)
