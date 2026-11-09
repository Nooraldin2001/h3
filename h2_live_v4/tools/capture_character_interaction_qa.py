"""Character interaction prototype QA — screenshots + geometry + effect checks."""
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
OUT = ROOT / "refs" / "qa" / "character-interaction"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def driver_at(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.set_script_timeout(60)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script(
            "return !!(window.H2V4State && window.H2V4Character && window.H2V4CharacterPrototypeMedia);"
        )
    )
    for _ in range(40):
        nw = d.execute_script(
            "const i=document.querySelector('.stage-bg-img'); return i?i.naturalWidth:0;"
        )
        if nw and nw >= 1600:
            break
        time.sleep(0.25)
    time.sleep(0.35)


def shot(d, path: Path, w=1920, h=1080):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
            "fromSurface": True,
        },
    )
    path.write_bytes(base64.b64decode(data["data"]))


def geom(d):
    return d.execute_script(
        """
        const G = H2V4Geom;
        const box = (sel) => {
          const el = document.querySelector(sel);
          return el ? G.elementStageBox(el) : null;
        };
        return {
          stageScale: G.getStageScale(),
          brand: box('.brand-mark'),
          timer: box('.timer'),
          plate: box('#plate'),
          shell: box('#plate-shell'),
          code: box('#plate-code'),
          number: box('#plate-number'),
          phone: box('#plate-phone'),
          bid: box('.bid'),
          character: box('#character'),
          sprite: box('#character-sprite'),
          rim: box('#plate-rim'),
          anchors: H2V4Character.getAnchorsLive(),
          hud: H2V4Character.getHud(),
          numberVisible: H2V4State.getState().new_style.number_visible !== false,
          numberText: document.getElementById('plate-number')?.textContent || '',
          numberOpacity: getComputedStyle(document.getElementById('plate-number')).opacity,
          numberVisCss: getComputedStyle(document.getElementById('plate-number')).visibility,
        };
        """
    )


def play(d, action):
    return d.execute_script(
        "return H2V4Character.play(arguments[0], {yellowRim:true, redFx:true, soldStamp:true});",
        action,
    )


def wait_state(d, name, timeout=12):
    WebDriverWait(d, timeout).until(
        lambda x: x.execute_script("return H2V4Character.getState() === arguments[0];", name)
    )


def main():
    report = {"out": str(OUT), "cases": {}}
    d = driver_at(1920, 1080)
    try:
        d.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&debug=1&v=char1")
        wait_ready(d)

        # Initial idle — character invisible
        g0 = geom(d)
        shot(d, OUT / "01-idle-1920x1080.png")
        report["cases"]["idle"] = {
            "hud": g0["hud"],
            "charOpacity": d.execute_script(
                "return getComputedStyle(document.getElementById('character')).opacity;"
            ),
            "ok": g0["hud"]["state"] == "IDLE" and not g0["hud"]["busy"],
        }

        # Yellow card sequence
        play(d, "yellow")
        time.sleep(2.2)
        gY = geom(d)
        shot(d, OUT / "02-yellow-gesture-1920x1080.png")
        time.sleep(2.5)
        wait_state(d, "IDLE", 10)
        shot(d, OUT / "03-yellow-done-1920x1080.png")
        report["cases"]["yellow"] = {
            "mid": gY,
            "digitsStillVisibleMid": gY["numberVisCss"] != "hidden",
            "rimPresent": gY["rim"] is not None,
            "cueStatus": gY["hud"].get("cueStatus"),
            "ok": gY["hud"].get("cueStatus") == "estimated",
        }

        # Red card
        play(d, "red")
        time.sleep(2.4)
        gR = geom(d)
        shot(d, OUT / "04-red-hide-1920x1080.png")
        time.sleep(2.5)
        wait_state(d, "IDLE", 10)
        gR2 = geom(d)
        # Show number restore
        d.execute_script("H2V4State.patch({ns_show_number:true});")
        time.sleep(0.3)
        gShow = geom(d)
        shot(d, OUT / "05-show-number-restore-1920x1080.png")
        report["cases"]["red"] = {
            "hidden": gR["numberVisCss"] == "hidden" or gR["numberOpacity"] == "0",
            "storedNumber": gR["numberText"],
            "restored": gShow["numberVisCss"] != "hidden" and float(gShow["numberOpacity"] or 0) > 0.5,
            "ok": (gR["numberVisCss"] == "hidden" or gR["numberOpacity"] == "0")
            and gShow["numberText"] == "7777",
        }

        # Point
        play(d, "point")
        time.sleep(2.0)
        shot(d, OUT / "06-point-1920x1080.png")
        time.sleep(2.5)
        wait_state(d, "IDLE", 10)

        # SOLD
        play(d, "sold_stamp")
        time.sleep(2.6)
        gS = geom(d)
        shot(d, OUT / "07-sold-1920x1080.png")
        stampVisible = d.execute_script(
            "const s=document.getElementById('plate-sold-stamp'); return !!(s && !s.hidden);"
        )
        time.sleep(2.5)
        wait_state(d, "IDLE", 10)
        report["cases"]["sold"] = {
            "stampVisible": stampVisible,
            "cueStatus": gS["hud"].get("cueStatus"),
            "ok": stampVisible and gS["hud"].get("cueStatus") == "estimated",
        }

        # Busy lock
        play(d, "enter")
        time.sleep(0.2)
        rejected = play(d, "yellow")
        time.sleep(2.0)
        d.execute_script("H2V4Character.play('exit');")
        time.sleep(1.5)
        wait_state(d, "IDLE", 8)
        report["cases"]["busy_lock"] = {
            "rejected": rejected.get("ok") is False,
            "reason": rejected.get("reason"),
            "ok": rejected.get("ok") is False,
        }

        # Reset
        play(d, "enter")
        time.sleep(1.0)
        d.execute_script("H2V4Character.reset();")
        time.sleep(0.3)
        gZ = geom(d)
        shot(d, OUT / "08-reset-1920x1080.png")
        report["cases"]["reset"] = {
            "state": gZ["hud"]["state"],
            "ok": gZ["hud"]["state"] == "IDLE" and not gZ["hud"]["busy"],
        }

        # Geometry snapshot
        report["geometry_1920"] = geom(d)

        # Plate variants quick red-hide
        for ptype, code, number, phone in (
            ("abudhabi", "4", "8010", ""),
            ("fujairah", "A", "1234", ""),
            ("du", "", "", "0501234567"),
            ("etisalat", "", "", "0569876543"),
        ):
            d.execute_script(
                "H2V4State.patch({plate_type:arguments[0], code:arguments[1], number:arguments[2], phone_number:arguments[3]});",
                ptype,
                code,
                number,
                phone,
            )
            time.sleep(0.4)
            play(d, "red")
            time.sleep(2.5)
            wait_state(d, "IDLE", 10)
            hidden = d.execute_script(
                """
                const st = H2V4State.getState();
                const isPhone = H2PlateSystem.isPhone(st.plate_type);
                const el = document.getElementById(isPhone ? 'plate-phone' : 'plate-number');
                const cs = getComputedStyle(el);
                return cs.visibility === 'hidden' || cs.opacity === '0';
                """
            )
            shot(d, OUT / f"09-red-{ptype}-1920x1080.png")
            d.execute_script("H2V4State.patch({ns_show_number:true}); H2V4Character.reset();")
            time.sleep(0.25)
            report["cases"][f"red_{ptype}"] = {"hidden": hidden, "ok": hidden}

    finally:
        d.quit()

    # 1280 preview scale smoke
    d2 = driver_at(1280, 720)
    try:
        d2.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&v=char720")
        wait_ready(d2)
        play(d2, "yellow")
        time.sleep(2.2)
        shot(d2, OUT / "10-yellow-1280x720.png", 1280, 720)
        report["geometry_1280"] = geom(d2)
        wait_state(d2, "IDLE", 10)
    finally:
        d2.quit()

    files = {}
    for p in sorted(OUT.glob("*.png")):
        im = Image.open(p)
        files[p.name] = {"size": list(im.size), "bytes": p.stat().st_size}
    report["files"] = files
    report["all_ok"] = all(c.get("ok") for c in report["cases"].values() if isinstance(c, dict) and "ok" in c)
    report["media_note"] = (
        "Prototype PNG/GIF used. WebM alpha not composited. "
        "Cues status=estimated. Not production-ready."
    )
    (OUT / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
