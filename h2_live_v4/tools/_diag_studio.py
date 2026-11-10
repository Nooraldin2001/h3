from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time, json

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1920,1080")
d = webdriver.Chrome(options=opts)
d.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride",
    {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
)
d.get("http://127.0.0.1:8766/index.html")
WebDriverWait(d, 12).until(lambda x: x.execute_script("return !!window.H2V4State"))
time.sleep(1.5)
info = d.execute_script(
    """
const img=document.getElementById('studio-bg-img');
const layer=document.getElementById('layer-studio');
return {
  complete: img.complete,
  naturalWidth: img.naturalWidth,
  naturalHeight: img.naturalHeight,
  currentSrc: img.currentSrc,
  display: getComputedStyle(img).display,
  opacity: getComputedStyle(img).opacity,
  visibility: getComputedStyle(img).visibility,
  zIndex: getComputedStyle(layer).zIndex,
  layerDisplay: getComputedStyle(layer).display,
  layerOpacity: getComputedStyle(layer).opacity,
  stageBg: getComputedStyle(document.getElementById('stage')).backgroundColor,
  imgRect: (()=>{const r=img.getBoundingClientRect(); return {w:r.width,h:r.height,x:r.x,y:r.y};})(),
};
"""
)
print(json.dumps(info, indent=2))
px = d.execute_script(
    """
const img=document.getElementById('studio-bg-img');
const c=document.createElement('canvas');
c.width=img.naturalWidth||1; c.height=img.naturalHeight||1;
const ctx=c.getContext('2d');
try { ctx.drawImage(img,0,0); } catch(e) { return {err:String(e)}; }
const p=ctx.getImageData(Math.floor(c.width/2), Math.floor(c.height/2), 1, 1).data;
const p2=ctx.getImageData(Math.floor(c.width/2), 40, 1, 1).data;
const p3=ctx.getImageData(Math.floor(c.width/2), Math.floor(c.height*0.85), 1, 1).data;
return {center:[p[0],p[1],p[2],p[3]], topSpot:[p2[0],p2[1],p2[2],p2[3]], podium:[p3[0],p3[1],p3[2],p3[3]]};
"""
)
print("pixels", px)
# sample actual screenshot center pixel via CDP
shot = d.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"format": "png", "fromSurface": True, "clip": {"x": 900, "y": 100, "width": 120, "height": 80, "scale": 1}},
)
from pathlib import Path
import base64
from PIL import Image
import io

raw = base64.b64decode(shot["data"])
Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio-layer\diag-top.png").write_bytes(raw)
im = Image.open(io.BytesIO(raw)).convert("RGB")
print("diag-top size", im.size, "mid", im.getpixel((60, 40)))
d.quit()
