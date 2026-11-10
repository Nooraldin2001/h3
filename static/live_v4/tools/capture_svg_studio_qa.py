"""Verify Django V4 loads the SVG studio background at 1920×1080."""
from __future__ import annotations

import base64
import json
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[3]
TOKEN = "b747d8ca-8593-4ec0-b095-4d90a95233c4"
URL = f"http://127.0.0.1:8000/live/display-v4/{TOKEN}/"
SVG_URL = "http://127.0.0.1:8000/static/live_v4/assets/studio/H2_AUCTIONS_Studio_4K_Vector.svg"
OUT = ROOT / "h2_live_v4" / "refs" / "qa" / "studio-layer"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    # MIME / body check
    with urllib.request.urlopen(SVG_URL) as resp:
        ctype = resp.headers.get("Content-Type", "")
        body = resp.read(200)
    mime_ok = "svg" in ctype.lower()
    svg_ok = body.lstrip().startswith(b"<svg") or b"<svg" in body[:80]

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
        lambda x: x.execute_script("return !!window.H2V4State && !!document.getElementById('studio-bg-img')")
    )
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script(
            "const i=document.getElementById('studio-bg-img');"
            "return !!(i && i.complete && i.naturalWidth>0);"
        )
    )
    time.sleep(0.5)

    info = d.execute_script(
        """
        const img = document.getElementById('studio-bg-img');
        const cs = getComputedStyle(img);
        return {
          url: location.href,
          studioSrc: img.currentSrc || img.src,
          naturalWidth: img.naturalWidth,
          naturalHeight: img.naturalHeight,
          objectFit: cs.objectFit,
          objectPosition: cs.objectPosition,
          filter: cs.filter,
          isSvg: /\\.svg(\\?|$)/i.test(img.currentSrc || img.src),
          plateExists: !!document.getElementById('plate'),
          plateDisplay: getComputedStyle(document.getElementById('plate')).display,
          brand: !!document.querySelector('.brand'),
          timer: document.getElementById('timer-value')?.textContent,
          bid: document.getElementById('bid-amount')?.textContent,
        };
        """
    )
    info["contentType"] = ctype
    info["mimeOk"] = mime_ok
    info["svgBodyOk"] = svg_ok

    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
        },
    )
    shot = OUT / "django-svg-studio-1920.png"
    shot.write_bytes(base64.b64decode(data["data"]))
    (OUT / "django-svg-studio-metrics.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("OK", shot)
    print(json.dumps(info, indent=2))
    d.quit()

    if not info["isSvg"] or not info["mimeOk"] or not info["svgBodyOk"]:
        raise SystemExit("FAIL: SVG not actively loaded")
    if "studio-stage.jpg" in info["studioSrc"]:
        raise SystemExit("FAIL: old JPG still active")
    if info["plateDisplay"] == "none":
        raise SystemExit("FAIL: plate hidden unexpectedly")


if __name__ == "__main__":
    main()
