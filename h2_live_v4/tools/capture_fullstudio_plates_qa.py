"""QA: full-studio floating plate distribution (Low / Medium / High)."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "floating-plates-fullstudio"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--window-size=1920,1080")
    d = webdriver.Chrome(options=opts)
    d.set_script_timeout(30)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda drv: drv.execute_script(
            "return !!(window.H2V4State && window.H2V4BgPlatesFx && window.H2PlateSystem);"
        )
    )
    nw = 0
    for attempt in range(2):
        for _ in range(40):
            nw = d.execute_script(
                "const img=document.querySelector('.stage-bg-img');"
                "return img ? img.naturalWidth : 0;"
            )
            if nw and nw >= 1600:
                break
            time.sleep(0.25)
        if nw and nw >= 1600:
            break
        d.execute_script(
            """
            const img=document.querySelector('.stage-bg-img');
            if(!img) return;
            const base=img.getAttribute('src').split('?')[0];
            img.src = base + '?r=' + Date.now();
            """
        )
        time.sleep(0.6)
    if not nw or nw < 1600:
        raise RuntimeError("studio-stage.jpg failed to decode")
    d.execute_async_script(
        "const done=arguments[0];"
        "const img=document.querySelector('.stage-bg-img');"
        "if(!img||!img.decode){done(1);return;}"
        "img.decode().then(()=>done(1)).catch(()=>done(1));"
    )
    time.sleep(0.5)


def shot(d, path: Path):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
            "fromSurface": True,
        },
    )
    path.write_bytes(base64.b64decode(data["data"]))


def patch(d, dens):
    d.execute_script(
        """
        H2V4State.patch({
          new_style: {
            bg_motion_enabled: true,
            bg_motion_playing: true,
            bg_density: arguments[0],
            bg_speed: 0.65,
          }
        });
        H2V4BgPlatesFx.syncFromState();
        """,
        dens,
    )


def wait_sprites(d, n):
    WebDriverWait(d, 15).until(
        lambda drv: drv.execute_script(
            "return document.querySelectorAll('#bg-plates .bg-plate-sprite').length >= arguments[0];",
            n,
        )
    )


def metrics(d):
    return d.execute_script(
        """
        const sprites = [...document.querySelectorAll('#bg-plates .bg-plate-sprite')];
        const keep = [
          {name:'logo', sel:'.brand-mark'},
          {name:'timer', sel:'.timer'},
          {name:'plate', sel:'.plate-shell'},
          {name:'bid', sel:'.bid'},
        ];
        function rect(el){
          if(!el) return null;
          const b=el.getBoundingClientRect();
          return {l:b.left,t:b.top,r:b.right,b:b.bottom,cx:(b.left+b.right)/2,cy:(b.top+b.bottom)/2};
        }
        function overlap(a,b){
          return !(a.r<=b.l || b.r<=a.l || a.b<=b.t || b.b<=a.t);
        }
        const zones = {};
        for (const z of keep) zones[z.name] = rect(document.querySelector(z.sel));
        const overlaps = [];
        const centers = [];
        let leftBand=0, midBand=0, rightBand=0, topBand=0, bottomBand=0, edgeOnly=0, inner=0;
        for (const img of sprites){
          const r = rect(img);
          centers.push({cx:r.cx, cy:r.cy, zone: img.dataset?.zone || null});
          if (r.cx < 520) leftBand++;
          else if (r.cx > 1400) rightBand++;
          else midBand++;
          if (r.cy < 300) topBand++;
          if (r.cy > 780) bottomBand++;
          if (r.cx < 280 || r.cx > 1640) edgeOnly++;
          else inner++;
          for (const [name, z] of Object.entries(zones)){
            if (z && overlap(r,z)) overlaps.push({zone:name, src:img.getAttribute('src')});
          }
        }
        // Attach zone ids from FX sprites if available
        const fx = (window.H2V4BgPlatesFx && [...document.querySelectorAll('#bg-plates .bg-plate-sprite')]) || [];
        const zoneIds = (window.__h2BgZones) || null;
        const ns = H2V4State.getState().new_style || {};
        const total = sprites.length || 1;
        return {
          density: ns.bg_density,
          spriteCount: sprites.length,
          leftBand, midBand, rightBand, topBand, bottomBand, edgeOnly, inner,
          leftPct: leftBand/total,
          midPct: midBand/total,
          rightPct: rightBand/total,
          topPct: topBand/total,
          bottomPct: bottomBand/total,
          innerPct: inner/total,
          overlapCount: overlaps.length,
          overlaps: overlaps.slice(0, 8),
          sampleCenters: centers.slice(0, 14),
          zoneIds,
        };
        """
    )


def main():
    d = make_driver()
    report = {"out": str(OUT)}
    try:
        d.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&v=fullstudio1")
        wait_ready(d)

        dens_map = {"low": 8, "medium": 16, "high": 25}
        for name, dens in dens_map.items():
            patch(d, dens)
            wait_sprites(d, dens)
            time.sleep(1.1)
            m = metrics(d)
            shot(d, OUT / f"fullstudio-{name}-1920x1080.png")
            report[name] = m
            time.sleep(1.2)
            shot(d, OUT / f"fullstudio-{name}-motion2-1920x1080.png")
    finally:
        d.quit()

    files = {}
    for p in sorted(OUT.glob("fullstudio-*.png")):
        im = Image.open(p)
        files[p.name] = {"size": list(im.size), "bytes": p.stat().st_size}
    report["files"] = files

    checks = []
    for name, dens in (("low", 8), ("medium", 16), ("high", 25)):
        m = report.get(name) or {}
        # Full-studio: need mid presence + top/bottom, and not edge-dominated
        side_heavy = m.get("innerPct", 0) < 0.28
        has_top = m.get("topBand", 0) >= 1
        has_bottom = dens < 16 or m.get("bottomBand", 0) >= 1
        has_mid = dens < 16 or m.get("midBand", 0) >= 2
        ok = (
            m.get("spriteCount") == dens
            and m.get("overlapCount", 99) == 0
            and not side_heavy
            and has_top
            and has_bottom
            and has_mid
        )
        checks.append(
            {
                "key": name,
                "ok": ok,
                "spriteCount": m.get("spriteCount"),
                "overlapCount": m.get("overlapCount"),
                "midBand": m.get("midBand"),
                "topBand": m.get("topBand"),
                "bottomBand": m.get("bottomBand"),
                "innerPct": m.get("innerPct"),
                "side_heavy": side_heavy,
            }
        )
    report["checks"] = checks
    report["all_ok"] = all(c["ok"] for c in checks)
    (OUT / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
