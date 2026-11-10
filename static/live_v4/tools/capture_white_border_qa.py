"""Before/after white-border QA on Django V4 display."""
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
OUT = Path(__file__).resolve().parents[3] / "h2_live_v4" / "refs" / "qa" / "plate-white-border"
OUT.mkdir(parents=True, exist_ok=True)

TYPES = [
    ("dubai", "AA", "7777", ""),
    ("abudhabi", "15", "88888", ""),
    ("ajman", "A", "1234", ""),
    ("du", "", "", "0501234567"),
    ("etisalat", "", "", "0569876543"),
]


def shot(d, name, clip=None):
    args = {"format": "png", "fromSurface": True}
    args["clip"] = clip or {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1}
    data = d.execute_cdp_cmd("Page.captureScreenshot", args)
    path = OUT / name
    path.write_bytes(base64.b64decode(data["data"]))
    return path


def main(tag="before"):
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
    d.get(URL + f"?_={int(time.time())}")
    WebDriverWait(d, 15).until(
        lambda x: x.execute_script("return !!window.H2V4State && !!window.H2PlateSystem")
    )
    time.sleep(0.4)

    results = []
    # Pause django poll so local plate patches stick for visual QA
    d.execute_script(
        """
        if (window.H2V4DjangoBridge) {
          const id = setInterval(()=>{}, 1e9);
          for (let i=1;i<id;i++) clearInterval(i);
        }
        """
    )
    for ptype, code, number, phone in TYPES:
        d.execute_script(
            """
            H2V4State.patch({
              plate_type: arguments[0], code: arguments[1], number: arguments[2],
              phone_number: arguments[3],
              new_style: { number_visible: true }
            });
            H2PlateSystem.renderPlate(H2V4State.getState());
            """,
            ptype,
            code,
            number,
            phone,
        )
        time.sleep(0.4)
        info = d.execute_script(
            """
            const plate=document.getElementById('plate');
            const shell=document.getElementById('plate-shell');
            const art=document.getElementById('plate-art');
            const pr=plate.getBoundingClientRect();
            const sr=shell.getBoundingClientRect();
            const ar=art.getBoundingClientRect();
            return {
              type: H2V4State.getState().plate_type,
              plateAspect: getComputedStyle(plate).aspectRatio,
              shellBg: getComputedStyle(shell).backgroundColor,
              shellRadius: getComputedStyle(shell).borderRadius,
              artFit: getComputedStyle(art).objectFit,
              artRadius: getComputedStyle(art).borderRadius,
              artBoxShadow: getComputedStyle(art).boxShadow,
              plateBox:{x:pr.x,y:pr.y,w:pr.width,h:pr.height},
              shellBox:{w:sr.width,h:sr.height},
              artBox:{w:ar.width,h:ar.height},
              src: art.currentSrc||art.src,
            };
            """
        )
        results.append(info)
        pr = info["plateBox"]
        crop = {
            "x": max(0, pr["x"] - 40),
            "y": max(0, pr["y"] - 40),
            "width": min(1920 - max(0, pr["x"] - 40), pr["w"] + 80),
            "height": min(1080 - max(0, pr["y"] - 40), pr["h"] + 80),
            "scale": 1,
        }
        shot(d, f"{tag}-{ptype}-crop.png", crop)

    shot(d, f"{tag}-broadcast-1920.png")
    (OUT / f"{tag}-metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("OK", tag, OUT)
    d.quit()


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "before")
