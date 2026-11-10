"""Screenshot the ACTIVE Django V4 display URL with main plate hidden."""
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
    # Avoid stale cached static while iterating
    opts.add_argument("--disk-cache-size=1")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Network.setCacheDisabled",
        {"cacheDisabled": True},
    )
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
    )
    d.get(URL + "?show_plate=0&_=" + str(int(time.time())))
    WebDriverWait(d, 15).until(
        lambda x: x.execute_script("return !!window.H2V4DisplayConfig && !!window.H2V4State")
    )
    d.execute_script("H2V4DisplayConfig.applyMainPlateVisibility();")
    time.sleep(0.8)

    info = d.execute_script(
        """
        const plate = document.getElementById('plate');
        const cs = plate ? getComputedStyle(plate) : null;
        const scripts = [...document.scripts].map(s => s.src).filter(Boolean);
        const sheets = [...document.styleSheets].map(s => s.href).filter(Boolean);
        return {
          url: location.href,
          SHOW_MAIN_PLATE: H2V4DisplayConfig.SHOW_MAIN_PLATE,
          plateExists: !!plate,
          plateDisplay: cs ? cs.display : null,
          plateVisibility: cs ? cs.visibility : null,
          plateHiddenAttr: plate ? plate.hidden : null,
          codeText: document.getElementById('plate-code')?.textContent || '',
          numberText: document.getElementById('plate-number')?.textContent || '',
          numberVisible: (()=>{
            const n=document.getElementById('plate-number');
            if(!n) return false;
            const r=n.getBoundingClientRect();
            return r.width>0 && r.height>0 && getComputedStyle(n).visibility!=='hidden' && getComputedStyle(n).display!=='none';
          })(),
          plateVisibleBox: (()=>{
            if(!plate) return null;
            const r=plate.getBoundingClientRect();
            return {w:r.width,h:r.height,x:r.x,y:r.y};
          })(),
          timer: document.getElementById('timer-value')?.textContent,
          bid: document.getElementById('bid-amount')?.textContent,
          brand: !!document.querySelector('.brand'),
          studioSrc: document.querySelector('.stage-bg-img')?.currentSrc || document.querySelector('.stage-bg-img')?.src,
          scripts: scripts.filter(s => s.includes('live_v4')),
          sheets: sheets.filter(s => s && s.includes('live_v4')),
          django: !!window.H2V4_DJANGO,
        };
        """
    )
    (OUT / "django-plate-hidden-metrics.json").write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )

    assert info["SHOW_MAIN_PLATE"] is False, info
    assert info["plateDisplay"] == "none", info
    assert info["numberVisible"] is False, info
    assert (info["plateVisibleBox"] or {}).get("w", 0) == 0, info

    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
        },
    )
    path = OUT / "django-display-v4-plate-hidden-1920.png"
    path.write_bytes(base64.b64decode(data["data"]))
    print("OK", path)
    print(json.dumps(info, indent=2))
    d.quit()


if __name__ == "__main__":
    main()
