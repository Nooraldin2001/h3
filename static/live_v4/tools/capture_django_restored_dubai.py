"""Restored Django V4 shot forced to Dubai for visual confirmation."""
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
    # Local visual confirmation only — does not write Django session
    d.execute_script(
        """
        H2V4State.patch({
          plate_type:'dubai', code:'AA', number:'7777', phone_number:'',
          new_style:{number_visible:true}
        });
        """
    )
    time.sleep(0.6)
    info = d.execute_script(
        """
        const plate=document.getElementById('plate');
        const pr=plate.getBoundingClientRect();
        const bg=document.querySelector('.stage-bg-img');
        return {
          hasDisplayConfig: !!window.H2V4DisplayConfig,
          plateDisplay: getComputedStyle(plate).display,
          plateBox:{w:pr.width,h:pr.height},
          code: document.getElementById('plate-code').textContent,
          number: document.getElementById('plate-number').textContent,
          studioSrc: bg.currentSrc||bg.src,
          studioFilter: getComputedStyle(bg).filter,
        };
        """
    )
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
        },
    )
    path = OUT / "django-display-v4-restored-dubai-1920.png"
    path.write_bytes(base64.b64decode(data["data"]))
    (OUT / "django-restored-dubai-metrics.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("OK", path)
    print(json.dumps(info, indent=2))
    d.quit()
    if info["hasDisplayConfig"] or info["plateDisplay"] == "none" or info["number"] != "7777":
        raise SystemExit("FAIL " + json.dumps(info))
    if "studio-stage.jpg" not in info["studioSrc"]:
        raise SystemExit("FAIL studio " + info["studioSrc"])


if __name__ == "__main__":
    main()
