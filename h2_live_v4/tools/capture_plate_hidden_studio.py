"""Capture 1920×1080 broadcast with main plate hidden (studio refinement)."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

OUT = Path(__file__).resolve().parents[1] / "refs" / "qa" / "studio-layer"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8766/index.html"


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
    d.get(URL)
    WebDriverWait(d, 12).until(
        lambda x: x.execute_script("return !!window.H2V4DisplayConfig && !!window.H2V4State")
    )
    # Bust cache + ensure studio decode
    d.execute_script(
        """
        const i=document.getElementById('studio-bg-img');
        if (i) {
          const base = './assets/studio/H2_AUCTIONS_Studio_1920x1080.jpg';
          i.src = base + '?t=' + Date.now();
        }
        H2V4DisplayConfig.applyMainPlateVisibility();
        """
    )
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script(
            "const i=document.getElementById('studio-bg-img');"
            "return !!(i && i.complete && i.naturalWidth > 0);"
        )
    )
    time.sleep(0.45)

    info = d.execute_script(
        """
        const layer = document.getElementById('layer-main-plate');
        const img = document.getElementById('studio-bg-img');
        const cs = getComputedStyle(layer);
        return {
          SHOW_MAIN_PLATE: H2V4DisplayConfig.SHOW_MAIN_PLATE,
          layerHidden: layer.hidden,
          layerDisplay: cs.display,
          layerVisibility: cs.visibility,
          studioSrc: img.currentSrc,
          studioNW: img.naturalWidth,
          studioNH: img.naturalHeight,
          studioFit: getComputedStyle(img).objectFit,
          brandVisible: !!document.querySelector('.brand'),
          timerText: document.getElementById('timer-value')?.textContent,
          bidText: document.getElementById('bid-amount')?.textContent,
        };
        """
    )
    (OUT / "plate-hidden-metrics.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
        },
    )
    path = OUT / "studio-plate-hidden-1920.png"
    path.write_bytes(base64.b64decode(data["data"]))
    print("OK", path)
    print(json.dumps(info, indent=2))
    d.quit()


if __name__ == "__main__":
    main()
