"""QA floating plate density levels 15 / 25 / 35 on Django V4 display."""
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
OUT = Path(__file__).resolve().parents[3] / "h2_live_v4" / "refs" / "qa" / "floating-density"
OUT.mkdir(parents=True, exist_ok=True)

LEVELS = [("low", 15), ("medium", 25), ("high", 35)]


def shot(d, name):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
        },
    )
    path = OUT / name
    path.write_bytes(base64.b64decode(data["data"]))
    return path


def pause_bridge(d):
    d.execute_script(
        """
        if (window.H2V4DjangoBridge) {
          const id = setInterval(()=>{}, 1e9);
          for (let i=1;i<id;i++) clearInterval(i);
        }
        """
    )


def set_density(d, density, enabled=True):
    d.execute_script(
        """
        const density = arguments[0];
        const enabled = arguments[1];
        H2V4State.patch({
          new_style: {
            bg_motion_enabled: enabled,
            bg_motion_playing: enabled,
            bg_density: density,
            bg_speed: 'normal',
            number_visible: true
          }
        });
        H2V4BgPlatesFx.syncFromState();
        """,
        density,
        enabled,
    )
    time.sleep(1.0)


def sprite_info(d):
    return d.execute_script(
        """
        const imgs = [...document.querySelectorAll('#bg-plates img.bg-plate-sprite')];
        const files = imgs.map(i => (i.currentSrc || i.src).split('/').pop());
        const adjSame = files.slice(1).filter((f, i) => f === files[i]).length;
        const ns = H2V4State.getState().new_style || {};
        return {
          count: imgs.length,
          densityState: ns.bg_density,
          resolved: H2V4BgPlatesFx.resolveDensity(ns.bg_density),
          enabled: !!ns.bg_motion_enabled,
          files,
          uniqueFiles: [...new Set(files)],
          adjacentSame: adjSame,
          allCoded: files.every(f => !!f && !f.includes('bg_plates')),
          opts: H2V4BgPlatesFx.DENSITY_OPTS,
        };
        """
    )


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
    d.get(URL + f"?_={int(time.time())}")
    WebDriverWait(d, 15).until(
        lambda x: x.execute_script(
            "return !!window.H2V4State && !!window.H2V4BgPlatesFx"
        )
    )
    time.sleep(0.3)
    pause_bridge(d)

    report = {"levels": {}, "off": None, "pass": True}

    for name, dens in LEVELS:
        set_density(d, dens, True)
        info = sprite_info(d)
        shot(d, f"density-{name}-{dens}.png")
        ok = info["count"] == dens and info["resolved"] == dens and info["allCoded"]
        report["levels"][name] = {**info, "expected": dens, "ok": ok}
        if not ok:
            report["pass"] = False
        print(f"{name}: count={info['count']} expected={dens} unique={len(info['uniqueFiles'])} adjSame={info['adjacentSame']} ok={ok}")

    # ON/OFF without auto-enable when off
    set_density(d, 25, False)
    off = sprite_info(d)
    shot(d, "density-OFF.png")
    off_ok = off["count"] == 0 and off["enabled"] is False
    report["off"] = {**off, "ok": off_ok}
    if not off_ok:
        report["pass"] = False
    print(f"off: count={off['count']} enabled={off['enabled']} ok={off_ok}")

    set_density(d, 25, True)
    on = sprite_info(d)
    shot(d, "density-ON-medium.png")
    on_ok = on["count"] == 25
    report["on"] = {**on, "ok": on_ok}
    if not on_ok:
        report["pass"] = False
    print(f"on: count={on['count']} ok={on_ok}")

    (OUT / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PASS" if report["pass"] else "FAIL", OUT)
    d.quit()
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
