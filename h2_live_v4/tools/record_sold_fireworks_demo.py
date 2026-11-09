"""Short 1920×1080 demo of SOLD cinematic fireworks."""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "sold-fireworks" / "sold-fireworks-demo.mp4"
OUT.parent.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"
FPS = 12


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


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script("return !!(window.H2V4State && window.H2V4SoldFx);")
    )
    for _ in range(40):
        nw = d.execute_script(
            "const i=document.querySelector('.stage-bg-img'); return i?i.naturalWidth:0;"
        )
        if nw and nw >= 1600:
            break
        time.sleep(0.2)
    time.sleep(0.25)


def grab(d) -> np.ndarray:
    png = d.get_screenshot_as_png()
    arr = np.frombuffer(png, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise RuntimeError("decode failed")
    if bgr.shape[1] != 1920 or bgr.shape[0] != 1080:
        bgr = cv2.resize(bgr, (1920, 1080), interpolation=cv2.INTER_AREA)
    return bgr


def label(d, title: str):
    d.execute_script(
        """
        let el = document.getElementById('demo-label');
        if (!el) {
          el = document.createElement('div');
          el.id = 'demo-label';
          el.style.cssText = 'position:absolute;left:28px;bottom:28px;z-index:200;'
            + 'padding:12px 16px;font:700 26px Rajdhani,sans-serif;color:#f3e0a0;'
            + 'background:rgba(0,0,0,0.72);border:1px solid rgba(212,175,55,0.5);'
            + 'border-radius:8px;pointer-events:none;';
          document.getElementById('stage').appendChild(el);
        }
        el.textContent = arguments[0];
        """,
        title,
    )


def main():
    d = make_driver()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(OUT), fourcc, FPS, (1920, 1080))
    try:
        d.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&price=1250000&v=solddemo1")
        wait_ready(d)
        d.execute_script(
            "try{ if(window.H2V4BgPlates?.setDensity) H2V4BgPlates.setDensity(4);}catch(e){}"
        )

        label(d, "BEFORE SOLD")
        for _ in range(int(FPS * 1.2)):
            writer.write(grab(d))
            time.sleep(1 / FPS)

        label(d, "SOLD — FIREWORKS")
        d.execute_script(
            "H2V4State.patch({ trigger_sold: true, sold_style: 'fireworks', sold_name: 'DEMO' });"
        )

        # Capture live celebration through cleanup (~5.5s)
        t0 = time.time()
        while time.time() - t0 < 5.8:
            elapsed = time.time() - t0
            if elapsed < 0.4:
                label(d, "FIREWORKS START")
            elif elapsed < 2.2:
                label(d, "PEAK CELEBRATION")
            elif elapsed < 4.4:
                label(d, "FIREWORKS ENDING")
            else:
                label(d, "CLEAN STUDIO")
            writer.write(grab(d))
            time.sleep(1 / FPS)

        label(d, "FINAL CLEAN")
        for _ in range(int(FPS * 0.8)):
            writer.write(grab(d))
            time.sleep(1 / FPS)
    finally:
        writer.release()
        d.quit()
    print(str(OUT))


if __name__ == "__main__":
    main()
