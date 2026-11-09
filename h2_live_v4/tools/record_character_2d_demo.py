"""Short demo: Point → Yellow → Red → Show Number → clean."""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "character-2d" / "character-2d-demo.mp4"
OUT.parent.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"
FPS = 10


def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--window-size=1920,1080")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def grab(d):
    png = d.get_screenshot_as_png()
    bgr = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    box = d.execute_script(
        """
        const s=document.getElementById('stage');
        const r=s.getBoundingClientRect();
        return {x:r.left,y:r.top,w:r.width,h:r.height};
        """
    )
    x, y, w, h = int(box["x"]), int(box["y"]), max(1, int(box["w"])), max(1, int(box["h"]))
    crop = bgr[y : y + h, x : x + w]
    return cv2.resize(crop, (1920, 1080), interpolation=cv2.INTER_AREA)


def label(d, text):
    d.execute_script(
        """
        let el=document.getElementById('demo-label');
        if(!el){
          el=document.createElement('div');
          el.id='demo-label';
          el.style.cssText='position:absolute;left:28px;bottom:28px;z-index:200;padding:10px 14px;'
            +'font:700 24px Rajdhani,sans-serif;color:#f3e0a0;background:rgba(0,0,0,.72);'
            +'border:1px solid rgba(212,175,55,.5);border-radius:8px;pointer-events:none;';
          document.getElementById('stage').appendChild(el);
        }
        el.textContent=arguments[0];
        """,
        text,
    )


def hold_rec(d, writer, seconds):
    n = max(1, int(seconds * FPS))
    for _ in range(n):
        writer.write(grab(d))
        time.sleep(1 / FPS)


def main():
    d = make_driver()
    writer = cv2.VideoWriter(str(OUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (1920, 1080))
    try:
        d.get(f"{BASE}/index.html?plate_type=dubai&code=AA&number=7777&v=char2ddemo1")
        WebDriverWait(d, 20).until(
            lambda x: x.execute_script("return !!(window.H2V4Character && window.H2V4State);")
        )
        time.sleep(0.5)
        d.execute_script(
            "try{ if(window.H2V4BgPlates?.setDensity) H2V4BgPlates.setDensity(4);}catch(e){}"
        )

        label(d, "IDLE — no character")
        hold_rec(d, writer, 0.8)

        label(d, "POINT")
        d.execute_script("H2V4Character.play('point');")
        hold_rec(d, writer, 2.6)

        label(d, "YELLOW CARD")
        d.execute_script("H2V4Character.play('yellow', {yellowRim:true});")
        hold_rec(d, writer, 2.8)

        label(d, "RED CARD — hide number")
        d.execute_script("H2V4Character.play('red', {redFx:true});")
        hold_rec(d, writer, 2.8)

        label(d, "Number still hidden")
        hold_rec(d, writer, 0.7)

        label(d, "SHOW NUMBER")
        d.execute_script("H2V4State.patch({ ns_show_number: true });")
        hold_rec(d, writer, 1.0)

        label(d, "CLEAN")
        d.execute_script("H2V4Character.reset();")
        hold_rec(d, writer, 0.8)
    finally:
        writer.release()
        d.quit()
    print(str(OUT))


if __name__ == "__main__":
    main()
