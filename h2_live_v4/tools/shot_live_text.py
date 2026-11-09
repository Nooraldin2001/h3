from __future__ import annotations

import base64
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

BASE = "http://127.0.0.1:8766"
OUT = Path(__file__).resolve().parents[1] / "refs" / "qa" / "live-text"
OUT.mkdir(parents=True, exist_ok=True)


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
        d.get(f"{BASE}/index.html?v=ltshot")
        WebDriverWait(d, 15).until(lambda x: x.execute_script("return !!window.H2V4State"))
        b = d.current_window_handle
        d.switch_to.new_window("window")
        d.get(f"{BASE}/control.html?v=ltshot")
        WebDriverWait(d, 15).until(
            lambda x: x.execute_script("return !!document.getElementById('btn-live-text-1-apply')")
        )
        d.find_element("id", "live-text-1").clear()
        d.find_element("id", "live-text-1").send_keys("لوحة مميزة")
        d.find_element("id", "btn-live-text-1-apply").click()
        d.find_element("id", "live-text-2").clear()
        d.find_element("id", "live-text-2").send_keys("H2 Auctions Live")
        d.find_element("id", "btn-live-text-2-apply").click()
        time.sleep(0.7)
        d.switch_to.window(b)
        time.sleep(0.3)
        data = d.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "png",
                "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
                "fromSurface": True,
            },
        )
        (OUT / "broadcast-with-live-text.png").write_bytes(base64.b64decode(data["data"]))
        # crop top area around text
        data2 = d.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "png",
                "clip": {"x": 560, "y": 40, "width": 800, "height": 280, "scale": 1},
                "fromSurface": True,
            },
        )
        (OUT / "live-text-crop.png").write_bytes(base64.b64decode(data2["data"]))
        print(OUT / "broadcast-with-live-text.png")
        print(OUT / "live-text-crop.png")
    finally:
        d.quit()


if __name__ == "__main__":
    main()
