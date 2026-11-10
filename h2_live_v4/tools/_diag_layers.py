from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time, json, base64
from pathlib import Path
from PIL import Image
import io

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
time.sleep(2)
info = d.execute_script(
    """
const img=document.getElementById('studio-bg-img');
const layers=[
  'layer-studio','bg-plates','stage-fw','layer-main-plate','character','layer-ui','brand'
].map(id=>{
  const el=document.getElementById(id) || document.querySelector('.'+id);
  if(!el) return {id, missing:true};
  const cs=getComputedStyle(el);
  const r=el.getBoundingClientRect();
  return {
    id,
    z: cs.zIndex,
    opacity: cs.opacity,
    visibility: cs.visibility,
    display: cs.display,
    bg: cs.backgroundColor,
    w: r.width, h: r.height,
    tag: el.tagName,
  };
});
return {
  img: {nw:img.naturalWidth, nh:img.naturalHeight, complete:img.complete, src:img.currentSrc, opacity:getComputedStyle(img).opacity},
  layers
};
"""
)
print(json.dumps(info, indent=2))

# Hide everything except studio and sample
d.execute_script(
    """
['bg-plates','stage-fw','layer-main-plate','character','layer-ui','brand'].forEach(id=>{
  const el=document.getElementById(id);
  if(el) el.style.visibility='hidden';
});
"""
)
time.sleep(0.3)
shot = d.execute_cdp_cmd(
    "Page.captureScreenshot",
    {
        "format": "png",
        "fromSurface": True,
        "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
    },
)
raw = base64.b64decode(shot["data"])
out = Path(r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio-layer\10-studio-only.png")
out.write_bytes(raw)
im = Image.open(io.BytesIO(raw)).convert("RGB")
print("studio-only samples", im.getpixel((960, 80)), im.getpixel((960, 700)), im.getpixel((700, 700)))
d.quit()
