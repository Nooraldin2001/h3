"""QA captures for studio background + independent plate layer (sandbox :8766)."""
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


def shot(d, name, clip=None, w=1920, h=1080):
    args = {"format": "png", "fromSurface": True}
    args["clip"] = clip or {"x": 0, "y": 0, "width": w, "height": h, "scale": 1}
    data = d.execute_cdp_cmd("Page.captureScreenshot", args)
    path = OUT / name
    path.write_bytes(base64.b64decode(data["data"]))
    return path


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
        lambda x: x.execute_script("return !!window.H2V4State && !!window.H2PlateSystem")
    )
    # Wait until studio backdrop actually decodes (avoid black stage false negatives)
    WebDriverWait(d, 15).until(
        lambda x: x.execute_script(
            "const i=document.getElementById('studio-bg-img');"
            "return !!(i && i.complete && i.naturalWidth > 0);"
        )
    )
    time.sleep(0.35)
    d.execute_script(
        """
        H2V4State.patch({
          plate_type:'dubai', code:'AA', number:'7777',
          new_style:{number_visible:true, bg_motion_enabled:true, bg_motion_playing:true}
        });
        H2PlateSystem.syncPlateLayerToSlot();
        """
    )
    time.sleep(0.6)

    info = d.execute_script(
        """
        const bg = document.getElementById('studio-bg-img');
        const layer = document.getElementById('layer-main-plate');
        const plate = document.getElementById('plate');
        const slot = document.getElementById('plate-slot');
        const studio = document.getElementById('layer-studio');
        const cs = getComputedStyle(bg);
        return {
          bgSrc: bg ? (bg.currentSrc || bg.src) : null,
          bgFit: cs.objectFit,
          bgFilter: cs.filter,
          studioZ: getComputedStyle(studio).zIndex,
          plateLayerZ: getComputedStyle(layer).zIndex,
          uiZ: getComputedStyle(document.getElementById('layer-ui')).zIndex,
          charZ: getComputedStyle(document.getElementById('character')).zIndex,
          plateBox: H2V4Geom.elementStageBox(plate),
          slotBox: H2V4Geom.elementStageBox(slot),
          layerBox: H2V4Geom.elementStageBox(layer),
          shellBg: getComputedStyle(document.getElementById('plate-shell')).backgroundColor,
        };
        """
    )
    (OUT / "layer-metrics.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    # 1. Clean broadcast normal
    shot(d, "01-broadcast-normal-1920.png")
    # crop plate region
    pb = info["plateBox"]
    crop = {
        "x": max(0, pb["x"] - 60),
        "y": max(0, pb["y"] - 80),
        "width": min(1920, pb["w"] + 120),
        "height": min(1080, pb["h"] + 160),
        "scale": 1,
    }
    shot(d, "02-plate-visible-crop.png", crop)

    # 3. Hide plate layer — studio must remain
    d.execute_script(
        "document.getElementById('layer-main-plate').classList.add('is-hidden');"
    )
    time.sleep(0.25)
    shot(d, "03-plate-hidden-studio-intact-1920.png")
    d.execute_script(
        "document.getElementById('layer-main-plate').classList.remove('is-hidden');"
    )
    time.sleep(0.2)

    # 4. Yellow card
    d.execute_script(
        """
        H2V4Character?.fitRim?.();
        const rim=document.getElementById('plate-rim');
        rim.classList.add('yellow'); rim.classList.remove('red');
        rim.setAttribute('aria-hidden','false');
        document.getElementById('plate')?.classList.add('yellow-card');
        """
    )
    time.sleep(0.3)
    shot(d, "04-yellow-card-crop.png", crop)
    d.execute_script(
        """
        document.getElementById('plate-rim')?.classList.remove('yellow');
        document.getElementById('plate')?.classList.remove('yellow-card');
        """
    )

    # 5. Red card
    d.execute_script(
        """
        H2V4Character?.fitRim?.();
        H2V4BeamDropFx?.setRed?.(true);
        """
    )
    time.sleep(0.35)
    shot(d, "05-red-card-crop.png", crop)
    d.execute_script("H2V4BeamDropFx?.setRed?.(false);")

    # 6. SOLD
    d.execute_script(
        """
        H2V4State.patch({plate_type:'dubai', code:'AA', number:'7777'});
        const stamp=document.getElementById('plate-sold-stamp');
        const t=H2PlateSystem.getStampTarget('dubai');
        stamp.hidden=false; stamp.removeAttribute('hidden');
        stamp.style.opacity='1'; stamp.style.visibility='visible';
        stamp.style.position='absolute'; stamp.style.zIndex='20';
        stamp.style.left=(t.x*100)+'%'; stamp.style.top=(t.y*100)+'%';
        stamp.style.transform='translate(-50%,-50%) rotate(-12deg)';
        stamp.style.width='42%';
        document.getElementById('plate')?.classList.add('sold-illuminate');
        """
    )
    time.sleep(0.35)
    shot(d, "06-sold-crop.png", crop)
    d.execute_script(
        """
        document.getElementById('plate-sold-stamp').hidden=true;
        document.getElementById('plate')?.classList.remove('sold-illuminate');
        """
    )

    # 7. Aging (if available)
    d.execute_script(
        """
        if (window.H2V4AgingFx) {
          H2V4AgingFx.enable?.();
          H2V4AgingFx.setDuration?.(60);
          H2V4AgingFx.seekProgress?.(0.75, {freeze:true});
        }
        """
    )
    time.sleep(0.45)
    shot(d, "07-aging-crop.png", crop)
    d.execute_script("H2V4AgingFx?.resetAging?.();")

    # 8 already 1920; 9 = 1280
    d.execute_script(
        "H2V4State.patch({plate_type:'dubai', code:'AA', number:'7777', new_style:{number_visible:true}});"
    )
    time.sleep(0.3)
    shot(d, "08-broadcast-1920.png")
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1280, "height": 720, "deviceScaleFactor": 1, "mobile": False},
    )
    time.sleep(0.4)
    d.execute_script("H2PlateSystem.syncPlateLayerToSlot();")
    time.sleep(0.2)
    shot(d, "09-broadcast-1280.png", {"x": 0, "y": 0, "width": 1280, "height": 720, "scale": 1})

    print("OK", OUT)
    print(json.dumps(info, indent=2))
    d.quit()


if __name__ == "__main__":
    main()
