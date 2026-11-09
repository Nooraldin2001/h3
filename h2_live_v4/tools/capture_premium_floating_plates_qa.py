"""Premium Ambient Floating Plates QA — OFF / Low / Med / High + motion + scales."""
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
OUT = ROOT / "refs" / "qa" / "floating-plates-premium"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def make_driver(w: int, h: int):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d, timeout=20):
    WebDriverWait(d, timeout).until(
        lambda drv: drv.execute_script(
            "return !!(window.H2V4State && window.H2V4BgPlatesFx && window.H2PlateSystem);"
        )
    )
    # Poll naturalWidth — img.complete can be true while decode is still pending
    nw = 0
    for _ in range(50):
        nw = d.execute_script(
            "const img=document.querySelector('.stage-bg-img');"
            "return img ? img.naturalWidth : 0;"
        )
        if nw and nw >= 1600:
            break
        time.sleep(0.25)
    if not nw or nw < 1600:
        raise RuntimeError("studio-stage.jpg failed to decode in browser")
    d.execute_async_script(
        """
        const done = arguments[0];
        const img = document.querySelector('.stage-bg-img');
        if (!img || !img.decode) { done(true); return; }
        img.decode().then(() => done(true)).catch(() => done(true));
        """
    )
    time.sleep(0.45)


def shot_stage(d, path: Path, w=1920, h=1080):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
            "captureBeyondViewport": False,
            "fromSurface": True,
        },
    )
    path.write_bytes(base64.b64decode(data["data"]))


def patch_bg(d, enabled=True, playing=True, density=16, speed=0.65):
    d.execute_script(
        """
        const [en, play, dens, spd] = arguments;
        H2V4State.patch({
          new_style: {
            bg_motion_enabled: !!en,
            bg_motion_playing: !!play,
            bg_density: dens,
            bg_speed: spd,
          }
        });
        H2V4BgPlatesFx.syncFromState();
        """,
        enabled,
        playing,
        density,
        speed,
    )


def wait_sprites(d, n, timeout=15):
    WebDriverWait(d, timeout).until(
        lambda drv: drv.execute_script(
            "return document.querySelectorAll('#bg-plates .bg-plate-sprite').length >= arguments[0];",
            n,
        )
    )


def metrics(d):
    return d.execute_script(
        """
        const ns = H2V4State.getState().new_style || {};
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
          return {l:b.left,t:b.top,r:b.right,b:b.bottom,w:b.width,h:b.height};
        }
        function overlap(a,b){
          return !(a.r<=b.l || b.r<=a.l || a.b<=b.t || b.b<=a.t);
        }
        const zones = {};
        for (const z of keep){
          zones[z.name] = rect(document.querySelector(z.sel));
        }
        const overlaps = [];
        for (const img of sprites){
          const r = rect(img);
          for (const [name, z] of Object.entries(zones)){
            if (z && overlap(r,z)) overlaps.push({src: img.getAttribute('src'), zone: name});
          }
        }
        const srcs = sprites.map(s => s.getAttribute('src') || '');
        const codes = srcs.map(s => {
          const m = /__([A-Z]+)\\.png$/i.exec(s);
          return m ? m[1] : null;
        }).filter(Boolean);
        const hasDigitInFilename = srcs.some(s => /\\d/.test((s.split('__').pop()||'')));
        return {
          enabled: !!ns.bg_motion_enabled,
          playing: ns.bg_motion_playing !== false,
          density: ns.bg_density,
          speed: ns.bg_speed,
          spriteCount: sprites.length,
          uniqueSrc: new Set(srcs).size,
          sampleSrc: srcs.slice(0, 8),
          codesSample: codes.slice(0, 12),
          hasDigitInFilename,
          overlapsCentral: overlaps.slice(0, 10),
          overlapCount: overlaps.length,
          hasOpaqueBlackBg: sprites.some(s => {
            const bg = getComputedStyle(s).backgroundColor;
            return bg === 'rgb(0, 0, 0)' || bg === '#000' || bg === '#000000';
          }),
          rafRunning: !!(window.__h2BgRafProbe),
        };
        """
    )


def toggle_on_off_leak_test(d):
    """Repeated enable/disable must not leave duplicate sprites or stuck loops."""
    counts = []
    for i in range(4):
        patch_bg(d, enabled=True, playing=True, density=16, speed=0.65)
        wait_sprites(d, 16)
        time.sleep(0.25)
        counts.append(
            d.execute_script(
                "return document.querySelectorAll('#bg-plates .bg-plate-sprite').length;"
            )
        )
        patch_bg(d, enabled=False, playing=False, density=16, speed=0.65)
        time.sleep(0.2)
        counts.append(
            d.execute_script(
                "return document.querySelectorAll('#bg-plates .bg-plate-sprite').length;"
            )
        )
    return {
        "sequence": counts,
        "ok": counts == [16, 0, 16, 0, 16, 0, 16, 0],
    }


def capture_suite(w: int, h: int, report: dict):
    d = make_driver(w, h)
    tag = f"{w}x{h}"
    try:
        d.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&v=prem1")
        wait_ready(d)
        time.sleep(0.5)

        # OFF
        patch_bg(d, enabled=False)
        time.sleep(0.3)
        off_m = metrics(d)
        shot_stage(d, OUT / f"premium-OFF-{tag}.png", w, h)
        report[f"off_{tag}"] = off_m

        dens_map = {"low": 8, "medium": 16, "high": 25}
        for name, dens in dens_map.items():
            patch_bg(d, enabled=True, playing=True, density=dens, speed=0.65)
            wait_sprites(d, dens)
            time.sleep(0.9)
            m = metrics(d)
            shot_stage(d, OUT / f"premium-{name}-{tag}.png", w, h)
            report[f"{name}_{tag}"] = m

            # Second motion position
            time.sleep(1.4)
            shot_stage(d, OUT / f"premium-{name}-motion2-{tag}.png", w, h)

        # Stop freeze check at medium
        patch_bg(d, enabled=True, playing=False, density=16, speed=0.65)
        time.sleep(0.4)
        report[f"stopped_{tag}"] = metrics(d)
        shot_stage(d, OUT / f"premium-stopped-{tag}.png", w, h)

        if tag == "1920x1080":
            report["leak_toggle"] = toggle_on_off_leak_test(d)
    finally:
        d.quit()


def main():
    report = {"out": str(OUT)}
    capture_suite(1920, 1080, report)
    capture_suite(1280, 720, report)

    files = {}
    for p in sorted(OUT.glob("premium-*.png")):
        im = Image.open(p)
        files[p.name] = {"size": list(im.size), "bytes": p.stat().st_size}
    report["files"] = files

    # Soft pass/fail summary
    checks = []
    for key in ("off_1920x1080", "low_1920x1080", "medium_1920x1080", "high_1920x1080"):
        m = report.get(key) or {}
        if key.startswith("off"):
            checks.append({"key": key, "ok": m.get("spriteCount") == 0 and not m.get("enabled")})
        else:
            expected = {"low": 8, "medium": 16, "high": 25}[key.split("_")[0]]
            checks.append(
                {
                    "key": key,
                    "ok": m.get("spriteCount") == expected
                    and not m.get("hasDigitInFilename")
                    and not m.get("hasOpaqueBlackBg")
                    and m.get("overlapCount", 99) == 0,
                    "spriteCount": m.get("spriteCount"),
                    "overlapCount": m.get("overlapCount"),
                }
            )
    if report.get("leak_toggle"):
        checks.append({"key": "leak_toggle", "ok": report["leak_toggle"].get("ok")})
    report["checks"] = checks
    report["all_ok"] = all(c.get("ok") for c in checks)

    (OUT / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
