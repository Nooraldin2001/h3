"""QA final 12 floating plate assets on Django V4 display."""
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
OUT = Path(__file__).resolve().parents[3] / "h2_live_v4" / "refs" / "qa" / "floating-final"
OUT.mkdir(parents=True, exist_ok=True)

APPROVED = {
    "dubai_A.png",
    "dubai_B.png",
    "dubai_C.png",
    "dubai_classic.png",
    "abudhabi_1.png",
    "sharjah.png",
    "ajman.png",
    "rasalkhaimah.png",
    "ummalquwain.png",
    "fujairah.png",
    "du.png",
    "etisalat.png",
}
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
    d.execute_script(
        """
        if (window.H2V4DjangoBridge) {
          const id = setInterval(()=>{}, 1e9);
          for (let i=1;i<id;i++) clearInterval(i);
        }
        """
    )

    report = {"levels": {}, "pass": True, "approved": sorted(APPROVED)}

    def apply(density, enabled=True):
        d.execute_script(
            """
            H2V4State.patch({
              new_style: {
                bg_motion_enabled: arguments[1],
                bg_motion_playing: arguments[1],
                bg_density: arguments[0],
                bg_speed: 'normal',
                number_visible: true
              }
            });
            H2V4BgPlatesFx.syncFromState();
            """,
            density,
            enabled,
        )
        time.sleep(1.1)

    def info():
        return d.execute_script(
            """
            const imgs = [...document.querySelectorAll('#bg-plates img.bg-plate-sprite')];
            const sources = imgs.map(i => i.currentSrc || i.src);
            const files = sources.map(s => s.split('/').pop());
            const adj = files.slice(1).filter((f,i)=>f===files[i]).length;
            return {
              count: imgs.length,
              files,
              unique: [...new Set(files)],
              sources,
              adjacentSame: adj,
              packDirOk: sources.every(s => s.includes('/plates/floating_final/')),
              oldPack: sources.filter(s => s.includes('/bg_plates/pack/') || s.includes('/plates/coded/')),
              natural: imgs.map(i => ({w:i.naturalWidth,h:i.naturalHeight,ok:i.complete && i.naturalWidth>0})),
              note: H2V4BgPlatesFx.ASSET_NOTE,
              opts: H2V4BgPlatesFx.DENSITY_OPTS,
            };
            """
        )

    for name, dens in LEVELS:
        apply(dens, True)
        data = info()
        shot(d, f"final-{name}-{dens}.png")
        bad = [f for f in data["files"] if f not in APPROVED]
        ok = (
            data["count"] == dens
            and data["packDirOk"]
            and not data["oldPack"]
            and not bad
            and all(n["ok"] for n in data["natural"])
        )
        report["levels"][name] = {
            **data,
            "expected": dens,
            "unapproved": bad,
            "ok": ok,
        }
        if not ok:
            report["pass"] = False
        print(
            f"{name}: count={data['count']}/{dens} unique={len(data['unique'])} "
            f"adj={data['adjacentSame']} packOk={data['packDirOk']} bad={bad} ok={ok}"
        )

    # HTTP status for all approved
    statuses = d.execute_script(
        """
        const files = arguments[0];
        return Promise.all(files.map(async (file) => {
          const res = await fetch('./assets/plates/floating_final/' + file, {cache:'no-store'});
          return {file, status: res.status, ok: res.ok};
        }));
        """,
        sorted(APPROVED),
    )
    manifest = d.execute_script(
        """
        return fetch('./assets/plates/floating_final/manifest.json', {cache:'no-store'})
          .then(async r => ({status:r.status, ok:r.ok, body: await r.json()}))
          .catch(e => ({ok:false, error:String(e)}));
        """
    )
    report["statuses"] = statuses
    report["manifest"] = {
        "ok": manifest.get("ok"),
        "status": manifest.get("status"),
        "count": (manifest.get("body") or {}).get("count"),
        "files": [a["file"] for a in ((manifest.get("body") or {}).get("assets") or [])],
    }
    if not all(s.get("ok") for s in statuses) or report["manifest"].get("count") != 12:
        report["pass"] = False

    apply(25, False)
    off = info()
    shot(d, "final-OFF.png")
    report["off"] = {"count": off["count"], "ok": off["count"] == 0}
    if off["count"] != 0:
        report["pass"] = False

    apply(25, True)
    on = info()
    shot(d, "final-ON-medium.png")
    report["on"] = {"count": on["count"], "ok": on["count"] == 25}
    if on["count"] != 25:
        report["pass"] = False

    (OUT / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PASS" if report["pass"] else "FAIL", OUT)
    d.quit()
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
