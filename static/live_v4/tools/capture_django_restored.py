"""Verify restored Django V4 display at 1920×1080."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

TOKEN = "b747d8ca-8593-4ec0-b095-4d90a95233c4"
URL = f"http://127.0.0.1:8000/live/display-v4/{TOKEN}/"
OUT = Path(__file__).resolve().parents[3] / "h2_live_v4" / "refs" / "qa" / "studio-layer"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disk-cache-size=1")
    d = webdriver.Chrome(options=opts)
    try:
        d.execute_cdp_cmd("Network.enable", {})
        d.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
    except Exception:
        pass
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
    )
    d.get(URL + "?_=" + str(int(time.time())))
    WebDriverWait(d, 15).until(
        lambda x: x.execute_script("return !!window.H2V4State && !!window.H2PlateSystem")
    )
    time.sleep(1.0)

    info = d.execute_script(
        """
        const plate = document.getElementById('plate');
        const art = document.getElementById('plate-art');
        const bg = document.querySelector('.stage-bg-img');
        const cs = plate ? getComputedStyle(plate) : null;
        const pr = plate ? plate.getBoundingClientRect() : null;
        return {
          url: location.href,
          hasDisplayConfig: !!window.H2V4DisplayConfig,
          django: !!window.H2V4_DJANGO,
          plateDisplay: cs ? cs.display : null,
          plateVisibility: cs ? cs.visibility : null,
          plateBox: pr ? {w:pr.width,h:pr.height,x:pr.x,y:pr.y} : null,
          code: document.getElementById('plate-code')?.textContent || '',
          number: document.getElementById('plate-number')?.textContent || '',
          numberVisible: (()=>{
            const n=document.getElementById('plate-number');
            if(!n) return false;
            const r=n.getBoundingClientRect();
            return r.width>2 && r.height>2 && getComputedStyle(n).visibility!=='hidden';
          })(),
          studioSrc: bg ? (bg.currentSrc || bg.src) : null,
          studioNW: bg ? bg.naturalWidth : 0,
          artSrc: art ? (art.currentSrc || art.src) : null,
          timer: document.getElementById('timer-value')?.textContent,
          bid: document.getElementById('bid-amount')?.textContent,
          brand: !!document.querySelector('.brand'),
          scripts: [...document.scripts].map(s=>s.src).filter(s=>s.includes('live_v4')),
        };
        """
    )
    (OUT / "django-restored-metrics.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
        },
    )
    path = OUT / "django-display-v4-restored-1920.png"
    path.write_bytes(base64.b64decode(data["data"]))
    print("OK", path)
    print(json.dumps(info, indent=2))
    d.quit()

    # Hard fail if hide flag still active or plate invisible
    if info.get("hasDisplayConfig"):
        raise SystemExit("FAIL: H2V4DisplayConfig still present")
    if info.get("plateDisplay") == "none" or not info.get("numberVisible"):
        raise SystemExit("FAIL: plate not visible: " + json.dumps(info))
    if not info.get("studioSrc") or "studio-stage" not in str(info.get("studioSrc")):
        raise SystemExit("FAIL: original studio-stage not active: " + str(info.get("studioSrc")))


if __name__ == "__main__":
    main()
