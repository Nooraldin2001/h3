"""Capture 1920x1080 floating-plates ON / OFF QA screenshots."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "floating-plates"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def driver_1920():
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


def wait_ready(d, timeout=20):
    WebDriverWait(d, timeout).until(
        lambda drv: drv.execute_script(
            "return !!(window.H2V4State && window.H2V4BgPlatesFx && window.H2PlateSystem);"
        )
    )
    try:
        WebDriverWait(d, 6).until(
            lambda drv: drv.execute_script(
                "const img=document.querySelector('.stage-bg-img');"
                "return !!(img && img.complete && img.naturalWidth>0);"
            )
        )
    except Exception:
        pass
    time.sleep(0.4)


def shot(d, path: Path):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
            "captureBeyondViewport": False,
            "fromSurface": True,
        },
    )
    path.write_bytes(base64.b64decode(data["data"]))


def metrics(d):
    return d.execute_script(
        """
        const ns = H2V4State.getState().new_style || {};
        const sprites = [...document.querySelectorAll('#bg-plates .bg-plate-sprite')];
        const keep = [
          {name:'logo', sel:'.brand'},
          {name:'timer', sel:'.timer'},
          {name:'plate', sel:'#plate, .plate-shell'},
          {name:'bid', sel:'.bid'},
        ];
        function rect(el){
          if(!el) return null;
          const b=el.getBoundingClientRect();
          return {l:b.left,t:b.top,r:b.right,b:b.bottom,w:b.width,h:b.height};
        }
        function overlap(a,b){
          return !(a.r<=b.l || b.r<=a.l || a.b<=b.t || b.b<=a.t);
        }
        const zones = {};
        for (const z of keep){
          zones[z.name] = rect(document.querySelector(z.sel));
        }
        const overlaps = [];
        for (const img of sprites){
          const r = rect(img);
          for (const [name, z] of Object.entries(zones)){
            if (z && overlap(r,z)) overlaps.push({src: img.getAttribute('src'), zone: name});
          }
        }
        const srcs = sprites.map(s => s.getAttribute('src') || '');
        const emirates = [...new Set(srcs.map(s => {
          const m = /pack\\/([^_]+(?:_[^_]+)*)__/.exec(s);
          return m ? m[1] : null;
        }).filter(Boolean))];
        const uniqueSrc = new Set(srcs).size;
        return {
          enabled: !!ns.bg_motion_enabled,
          density: ns.bg_density,
          speed: ns.bg_speed,
          spriteCount: sprites.length,
          uniqueSrc,
          emirates,
          sampleSrc: srcs.slice(0, 6),
          overlapsCentral: overlaps.slice(0, 8),
          overlapCount: overlaps.length,
          hasBlackBgClass: sprites.some(s => getComputedStyle(s).backgroundColor === 'rgb(0, 0, 0)'),
        };
        """
    )


def main():
    d = driver_1920()
    report = {}
    try:
        # OFF (default)
        d.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&v=fp1")
        wait_ready(d)
        # Allow pack load attempt even when off
        time.sleep(0.6)
        off_m = metrics(d)
        shot(d, OUT / "floating-plates-OFF-1920x1080.png")
        report["off"] = off_m

        # ON via query
        d.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&bg=1&v=fp1")
        wait_ready(d)
        # Wait for manifest + sprite build
        WebDriverWait(d, 15).until(
            lambda drv: drv.execute_script(
                "return document.querySelectorAll('#bg-plates .bg-plate-sprite').length >= 8;"
            )
        )
        time.sleep(1.2)
        on_m = metrics(d)
        shot(d, OUT / "floating-plates-ON-1920x1080.png")
        report["on"] = on_m
    finally:
        d.quit()

    for name in ("floating-plates-OFF-1920x1080.png", "floating-plates-ON-1920x1080.png"):
        p = OUT / name
        im = Image.open(p)
        report.setdefault("files", {})[name] = {"size": list(im.size), "bytes": p.stat().st_size}

    (OUT / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
