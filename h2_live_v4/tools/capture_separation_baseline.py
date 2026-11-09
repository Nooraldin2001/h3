"""Capture 1920×1080 broadcast baseline before page separation."""
from __future__ import annotations

import base64
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "page-separation"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def main():
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
    try:
        d.get(f"{BASE}/index.html?plate_type=dubai&code=AA&number=7777&v=sepbase1")
        WebDriverWait(d, 20).until(
            lambda x: x.execute_script("return !!(window.H2V4State && window.H2PlateSystem);")
        )
        time.sleep(0.8)
        data = d.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "png",
                "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
                "fromSurface": True,
            },
        )
        (OUT / "baseline-broadcast-1920x1080.png").write_bytes(base64.b64decode(data["data"]))
        print(str(OUT / "baseline-broadcast-1920x1080.png"))
    finally:
        d.quit()


if __name__ == "__main__":
    main()
