"""Enable ambient floats on Django V4 display and capture QA evidence."""
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
OUT = Path(__file__).resolve().parents[3] / "h2_live_v4" / "refs" / "qa" / "floating-coded"
OUT.mkdir(parents=True, exist_ok=True)


def shot(d, name, clip=None):
    args = {"format": "png", "fromSurface": True}
    args["clip"] = clip or {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1}
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
    opts.add_argument("--disk-cache-size=1")
    d = webdriver.Chrome(options=opts)
    try:
        d.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
        d.execute_cdp_cmd("Network.enable", {})
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
    time.sleep(0.4)

    # Pause django poll so local ambient patches stick
    d.execute_script(
        """
        if (window.H2V4DjangoBridge) {
          const id = setInterval(()=>{}, 1e9);
          for (let i=1;i<id;i++) clearInterval(i);
        }
        """
    )

    # Enable floats + play + medium density
    d.execute_script(
        """
        H2V4State.patch({
          new_style: {
            bg_motion_enabled: true,
            bg_motion_playing: true,
            bg_density: 16,
            bg_speed: 'normal',
            number_visible: true
          }
        });
        if (window.H2V4BgPlatesFx) {
          H2V4BgPlatesFx.setEnabled(true);
          H2V4BgPlatesFx.syncFromState();
        }
        """
    )
    time.sleep(1.2)

    info = d.execute_script(
        """
        const layer = document.getElementById('bg-plates');
        const imgs = [...(layer ? layer.querySelectorAll('img.bg-plate-sprite') : [])];
        const state = H2V4State.getState();
        return {
          enabled: !!(state.new_style && state.new_style.bg_motion_enabled),
          playing: state.new_style && state.new_style.bg_motion_playing !== false,
          density: state.new_style && state.new_style.bg_density,
          spriteCount: imgs.length,
          sources: imgs.map(img => img.currentSrc || img.src),
          files: imgs.map(img => (img.currentSrc || img.src).split('/').pop()),
          natural: imgs.map(img => ({w: img.naturalWidth, h: img.naturalHeight, complete: img.complete})),
          packNote: H2V4BgPlatesFx.ASSET_NOTE,
          ariaHidden: layer && layer.getAttribute('aria-hidden'),
        };
        """
    )

    # Collect network responses for plate assets
    logs = []
    try:
        entries = d.execute_cdp_cmd("Network.getResponseBody", {})  # may fail; use performance log instead
    except Exception:
        pass
    perf = d.execute_script(
        """
        return performance.getEntriesByType('resource')
          .filter(e => /plates\\/coded|bg_plates\\/pack|manifest\\.json/.test(e.name))
          .map(e => ({name: e.name, duration: e.duration, transferSize: e.transferSize, type: e.initiatorType}));
        """
    )

    # Toggle OFF then ON to verify control still works
    d.execute_script(
        """
        H2V4BgPlatesFx.setEnabled(false);
        H2V4BgPlatesFx.syncFromState();
        """
    )
    time.sleep(0.35)
    off_count = d.execute_script(
        "return document.querySelectorAll('#bg-plates img.bg-plate-sprite').length"
    )
    shot(d, "floating-OFF-1920.png")

    d.execute_script(
        """
        H2V4BgPlatesFx.setEnabled(true);
        H2V4BgPlatesFx.syncFromState();
        """
    )
    time.sleep(1.0)
    on_count = d.execute_script(
        "return document.querySelectorAll('#bg-plates img.bg-plate-sprite').length"
    )
    shot(d, "floating-ON-1920.png")

    # Probe HTTP status for each unique source
    statuses = d.execute_script(
        """
        const files = arguments[0];
        return Promise.all(files.map(async (file) => {
          const url = './assets/plates/coded/' + file;
          try {
            const res = await fetch(url, {cache: 'no-store'});
            return {file, status: res.status, ok: res.ok, url: res.url};
          } catch (e) {
            return {file, status: 0, ok: false, error: String(e)};
          }
        }));
        """,
        sorted(set(info.get("files") or [])),
    )
    # Also probe manifest + ensure old pack not requested by sprites
    manifest_status = d.execute_script(
        """
        return fetch('./assets/plates/coded/manifest.json', {cache:'no-store'})
          .then(async r => ({status: r.status, ok: r.ok, count: (await r.json()).count}))
          .catch(e => ({status:0, ok:false, error:String(e)}));
        """
    )

    report = {
        "info": info,
        "off_count": off_count,
        "on_count": on_count,
        "perf": perf,
        "statuses": statuses,
        "manifest": manifest_status,
        "old_pack_in_sources": [
            s for s in (info.get("sources") or []) if "bg_plates/pack" in s
        ],
        "new_coded_in_sources": [
            s for s in (info.get("sources") or []) if "plates/coded" in s
        ],
    }
    (OUT / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "sprites": info.get("spriteCount"),
        "files": info.get("files"),
        "off": off_count,
        "on": on_count,
        "manifest": manifest_status,
        "old_pack_refs": len(report["old_pack_in_sources"]),
        "new_refs": len(report["new_coded_in_sources"]),
        "out": str(OUT),
    }, indent=2))
    d.quit()


if __name__ == "__main__":
    main()
