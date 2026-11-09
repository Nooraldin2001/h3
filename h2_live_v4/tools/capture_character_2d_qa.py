"""Temporary 2D character QA — Point / Yellow / Red with visual checks."""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "character-2d"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def driver_at(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.set_script_timeout(90)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script(
            "return !!(window.H2V4Character && window.H2V4CharacterPrototypeMedia && window.H2V4State);"
        )
    )
    for _ in range(40):
        nw = d.execute_script(
            "const i=document.querySelector('.stage-bg-img'); return i?i.naturalWidth:0;"
        )
        if nw and nw >= 1600:
            break
        time.sleep(0.2)
    time.sleep(0.3)


def shot(d, path: Path, w, h):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
            "fromSurface": True,
            "captureBeyondViewport": True,
        },
    )
    # Crop stage
    box = d.execute_script(
        """
        const s=document.getElementById('stage');
        const r=s.getBoundingClientRect();
        return {x:r.left,y:r.top,w:r.width,h:r.height};
        """
    )
    page = Image.open(io.BytesIO(base64.b64decode(data["data"]))).convert("RGB")
    x, y = int(box["x"]), int(box["y"])
    ww, hh = max(1, int(box["w"])), max(1, int(box["h"]))
    crop = page.crop((x, y, x + ww, y + hh)).resize((1920, 1080), Image.Resampling.LANCZOS)
    crop.save(path)
    return crop


def snap(d):
    return d.execute_script(
        """
        const G = H2V4Geom;
        const box = (sel) => {
          const el = document.querySelector(sel);
          return el ? G.elementStageBox(el) : null;
        };
        const num = document.getElementById('plate-number');
        const char = document.getElementById('character');
        const spr = document.getElementById('character-sprite');
        const rim = document.getElementById('plate-rim');
        const plate = document.getElementById('plate');
        return {
          hud: H2V4Character.getHud(),
          anchors: H2V4Character.getAnchorsLive(),
          presence: H2V4Character.getPresence(),
          charBox: box('#character'),
          brand: box('.brand-mark'),
          timer: box('.timer'),
          bid: box('.bid'),
          plate: box('#plate'),
          shell: box('#plate-shell'),
          number: box('#plate-number'),
          numberText: num?.textContent || '',
          numberVisible: getComputedStyle(num).visibility !== 'hidden' && getComputedStyle(num).opacity !== '0',
          numberOpacity: getComputedStyle(num).opacity,
          charOpacity: getComputedStyle(char).opacity,
          charPlaying: char.classList.contains('playing'),
          spriteSrc: spr?.getAttribute('src') || '',
          spriteNatural: spr ? {w: spr.naturalWidth, h: spr.naturalHeight} : null,
          rimYellow: rim?.classList.contains('yellow'),
          rimRed: rim?.classList.contains('red'),
          plateShake: plate?.classList.contains('yellow-card'),
          plateTransform: getComputedStyle(plate).transform,
          price: H2V4State.getState().price,
          timer_remaining: H2V4State.getState().timer_remaining_seconds,
          number_visible_state: H2V4State.getState().new_style.number_visible !== false,
        };
        """
    )


def overlaps(a, b, pad=4):
    if not a or not b:
        return False
    return not (
        a["x"] + a["w"] + pad < b["x"]
        or b["x"] + b["w"] + pad < a["x"]
        or a["y"] + a["h"] + pad < b["y"]
        or b["y"] + b["h"] + pad < a["y"]
    )


def wait_idle(d, timeout=8):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if d.execute_script("return H2V4Character.getState() === 'IDLE' && !H2V4Character.isBusy();"):
            return True
        time.sleep(0.1)
    return False


def run_res(tag, w, h, report):
    d = driver_at(w, h)
    case = {"tag": tag, "page": f"{w}x{h}", "actions": {}}
    try:
        d.get(f"{BASE}/index.html?plate_type=dubai&code=AA&number=7777&price=1250000&v=char2d3")
        wait_ready(d)
        d.execute_script(
            "try{ if(window.H2V4BgPlates?.setDensity) H2V4BgPlates.setDensity(0);}catch(e){}"
        )

        idle0 = snap(d)
        shot(d, OUT / f"{tag}-00-idle.png", w, h)
        case["no_autoload"] = (
            not idle0["charPlaying"]
            and float(idle0["charOpacity"] or 0) < 0.05
            and idle0["hud"]["state"] == "IDLE"
        )
        case["presence"] = idle0["presence"]

        # POINT
        d.execute_script("H2V4Character.play('point');")
        time.sleep(0.95)  # mid hold after enter
        p = snap(d)
        shot(d, OUT / f"{tag}-01-point.png", w, h)
        case["actions"]["point"] = {
            "hud": p["hud"],
            "sprite": p["spriteSrc"],
            "spriteNatural": p["spriteNatural"],
            "charBox": p["charBox"],
            "covers_timer": overlaps(p["charBox"], p["timer"]),
            "covers_brand": overlaps(p["charBox"], p["brand"]),
            "covers_number": overlaps(p["charBox"], p["number"]),
            "price_ok": p["price"] == idle0["price"],
            "timer_ok": p["timer_remaining"] == idle0["timer_remaining"],
            "number_visible": p["numberVisible"],
            "visible": p["charPlaying"] and float(p["charOpacity"] or 0) > 0.5,
        }
        wait_idle(d)
        time.sleep(0.2)

        # YELLOW
        d.execute_script("H2V4Character.play('yellow', {yellowRim:true});")
        time.sleep(1.05)
        y = snap(d)
        shot(d, OUT / f"{tag}-02-yellow.png", w, h)
        case["actions"]["yellow"] = {
            "hud": y["hud"],
            "sprite": y["spriteSrc"],
            "rimYellow": y["rimYellow"],
            "plateShake": y["plateShake"],
            "number_visible": y["numberVisible"],
            "covers_timer": overlaps(y["charBox"], y["timer"]),
            "covers_brand": overlaps(y["charBox"], y["brand"]),
            "visible": y["charPlaying"] and float(y["charOpacity"] or 0) > 0.5,
        }
        wait_idle(d)
        time.sleep(0.25)
        y_after = snap(d)
        case["actions"]["yellow"]["after_transform"] = y_after["plateTransform"]
        case["actions"]["yellow"]["transform_reset"] = y_after["plateTransform"] in (
            "none",
            "matrix(1, 0, 0, 1, 0, 0)",
        )
        case["actions"]["yellow"]["rim_cleared"] = not y_after["rimYellow"]

        # RED
        d.execute_script("H2V4Character.play('red', {redFx:true});")
        time.sleep(1.05)
        r = snap(d)
        shot(d, OUT / f"{tag}-03-red.png", w, h)
        case["actions"]["red"] = {
            "hud": r["hud"],
            "sprite": r["spriteSrc"],
            "rimRed": r["rimRed"],
            "number_visible": r["numberVisible"],
            "number_hidden_ok": (not r["numberVisible"]) and (not r["number_visible_state"]),
            "numberText_preserved": r["numberText"] == "7777",
            "visible": r["charPlaying"] and float(r["charOpacity"] or 0) > 0.5,
        }
        wait_idle(d)
        time.sleep(0.2)

        # Still hidden after exit
        after_red = snap(d)
        shot(d, OUT / f"{tag}-04-red-exit-hidden.png", w, h)
        case["actions"]["red"]["still_hidden_after_exit"] = not after_red["numberVisible"]
        case["actions"]["red"]["char_gone"] = (
            not after_red["charPlaying"] or float(after_red["charOpacity"] or 0) < 0.05
        )

        # Show Number restores
        d.execute_script("H2V4State.patch({ ns_show_number: true });")
        time.sleep(0.25)
        shown = snap(d)
        shot(d, OUT / f"{tag}-05-show-number.png", w, h)
        case["show_number_restores"] = shown["numberVisible"] and shown["numberText"] == "7777"

        # Clean idle
        d.execute_script("H2V4Character.reset();")
        time.sleep(0.2)
        clean = snap(d)
        shot(d, OUT / f"{tag}-06-clean.png", w, h)
        case["clean"] = (
            not clean["charPlaying"]
            and float(clean["charOpacity"] or 0) < 0.05
            and clean["hud"]["state"] == "IDLE"
        )

        # Overlap prevention during busy
        d.execute_script("H2V4Character.play('point');")
        time.sleep(0.2)
        blocked = d.execute_script("return H2V4Character.play('yellow');")
        case["overlap_blocked"] = blocked.get("ok") is False and blocked.get("reason") == "busy"
        wait_idle(d)

        a = case["actions"]
        case["all_ok"] = all(
            [
                case["no_autoload"],
                case["presence"].get("point"),
                case["presence"].get("yellow"),
                case["presence"].get("red"),
                a["point"]["visible"],
                a["point"]["number_visible"],
                a["point"]["price_ok"],
                not a["point"]["covers_timer"],
                not a["point"]["covers_brand"],
                a["yellow"]["visible"],
                a["yellow"]["rimYellow"],
                a["yellow"]["number_visible"],
                a["yellow"]["transform_reset"],
                a["red"]["visible"],
                a["red"]["number_hidden_ok"],
                a["red"]["numberText_preserved"],
                a["red"]["still_hidden_after_exit"],
                a["red"]["char_gone"],
                case["show_number_restores"],
                case["clean"],
                case["overlap_blocked"],
            ]
        )
    finally:
        d.quit()
    report["cases"][tag] = case
    return case


def main():
    report = {
        "out": str(OUT),
        "asset_notes": {
            "point": "assets/character/prototype_2d/point.png from point_source.gif frame 4",
            "yellow": "assets/character/prototype_2d/yellow.png from point_source.gif frame 5 (same identity as point)",
            "red": "assets/character/prototype_2d/red.png from red card.gif frame 5 (only red-card sprite; framing differs)",
            "missing": "No matching full-body red card in the same 440×441 point/yellow capture; no dedicated sold_stamp 2D sprite",
        },
        "cases": {},
    }
    c1 = run_res("fullhd", 1920, 1080, report)
    c2 = run_res("hd720", 1280, 720, report)
    report["all_ok"] = bool(c1.get("all_ok") and c2.get("all_ok"))
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# Temporary 2D Character QA",
        "",
        f"**Result:** `{'PASS' if report['all_ok'] else 'FAIL'}`",
        "",
        "## Assets",
        json.dumps(report["asset_notes"], indent=2),
        "",
        f"- fullhd all_ok: {c1.get('all_ok')}",
        f"- hd720 all_ok: {c2.get('all_ok')}",
        "",
    ]
    (OUT / "CHARACTER_2D_QA.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"all_ok": report["all_ok"], "fullhd": c1.get("all_ok"), "hd720": c2.get("all_ok"), "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
