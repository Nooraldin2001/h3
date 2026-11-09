"""Before/after screenshots for ~30% 2D character scale increase."""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "character-2d-scale"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def driver_at(w=1920, h=1080):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script(
            "return !!(window.H2V4Character && window.H2V4CharacterPrototypeMedia);"
        )
    )
    for _ in range(40):
        nw = d.execute_script(
            "const i=document.querySelector('.stage-bg-img'); return i?i.naturalWidth:0;"
        )
        if nw and nw >= 1600:
            break
        time.sleep(0.2)
    time.sleep(0.25)


def shot(d, path: Path, w=1920, h=1080):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
            "fromSurface": True,
        },
    )
    box = d.execute_script(
        """
        const s = document.getElementById('stage');
        const r = s.getBoundingClientRect();
        return {x:r.left, y:r.top, w:r.width, h:r.height};
        """
    )
    page = Image.open(io.BytesIO(base64.b64decode(data["data"]))).convert("RGB")
    x, y = int(box["x"]), int(box["y"])
    ww, hh = max(1, int(box["w"])), max(1, int(box["h"]))
    crop = page.crop((x, y, x + ww, y + hh)).resize((1920, 1080), Image.Resampling.LANCZOS)
    crop.save(path)
    return crop


def metrics(d):
    return d.execute_script(
        """
        const G = H2V4Geom;
        const box = (sel) => {
          const el = document.querySelector(sel);
          return el ? G.elementStageBox(el) : null;
        };
        const a = H2V4Character.getAnchorsLive();
        const char = box('#character');
        const brand = box('.brand-mark');
        const timer = box('.timer');
        const bid = box('.bid');
        const number = box('#plate-number');
        const overlaps = (a,b,pad=2) => {
          if (!a || !b) return false;
          return !(a.x+a.w+pad < b.x || b.x+b.w+pad < a.x || a.y+a.h+pad < b.y || b.y+b.h+pad < a.y);
        };
        // Character is behind stack (z7 < z8); still check geometric intrusion into critical boxes
        return {
          display: a.display,
          stopFeet: a.stopFeet,
          scale: a.display ? (a.display.h / 430) : null,
          charBox: char,
          overlaps_brand: overlaps(char, brand),
          overlaps_timer: overlaps(char, timer),
          overlaps_number: overlaps(char, number),
          overlaps_bid: overlaps(char, bid),
          // head below bid bottom is preferred
          head_y: char ? char.y : null,
          bid_bottom: bid ? bid.y + bid.h : null,
          below_bid: char && bid ? char.y >= (bid.y + bid.h - 8) : null,
          hud: H2V4Character.getHud(),
        };
        """
    )


def wait_idle(d, timeout=8):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if d.execute_script(
            "return H2V4Character.getState()==='IDLE' && !H2V4Character.isBusy();"
        ):
            return True
        time.sleep(0.1)
    return False


def capture_set(prefix: str, tag: str, w: int, h: int):
    d = driver_at(w, h)
    out = {}
    try:
        d.get(f"{BASE}/index.html?plate_type=dubai&code=AA&number=7777&v={prefix}{tag}")
        wait_ready(d)
        d.execute_script(
            "try{ if(window.H2V4BgPlates?.setDensity) H2V4BgPlates.setDensity(0);}catch(e){}"
        )
        for action, wait in (("point", 0.95), ("yellow", 1.05), ("red", 1.05)):
            d.execute_script("H2V4Character.reset();")
            time.sleep(0.12)
            # Freeze on stage after enter so screenshot isn't mid-exit
            d.execute_script(
                "H2V4Character.play(arguments[0], {yellowRim:true, redFx:true, hold:true});",
                action,
            )
            time.sleep(wait)
            m = metrics(d)
            shot(d, OUT / f"{prefix}-{tag}-{action}.png", w, h)
            out[action] = m
            d.execute_script("H2V4Character.reset();")
            time.sleep(0.2)
    finally:
        d.quit()
    return out


def main():
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "after"
    prefix = "before" if mode == "before" else "after"
    report = {"mode": prefix, "cases": {}}
    report["cases"]["1920"] = capture_set(prefix, "1920", 1920, 1080)
    report["cases"]["1280"] = capture_set(prefix, "1280", 1280, 720)
    (OUT / f"{prefix}-metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
