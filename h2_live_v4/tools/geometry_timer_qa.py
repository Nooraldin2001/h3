"""Geometry alignment + timer QA for H2 Live V4."""
from __future__ import annotations

import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "refs" / "qa" / "geometry-fix"
OUT_DIR.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"
TOL_PX = 2.0


def driver_at(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(20)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda drv: drv.execute_script(
            "return !!(window.H2V4State && window.H2V4Geom && window.H2V4Timer && window.H2V4Debug);"
        )
    )
    time.sleep(0.3)


def shot(d, name):
    path = OUT_DIR / name
    d.get_screenshot_as_file(str(path))
    return path.name


def alignment(d):
    d.execute_script("H2V4Debug.draw && H2V4Debug.draw();")
    return d.execute_script("return H2V4Debug.measureAlignment();")


def max_error(align):
    errs = [v.get("errorPx") for v in align.values() if v.get("errorPx") is not None]
    return max(errs) if errs else None


def main():
    report = {"ok": True, "timer": {}, "geometry": {}, "cause": None}
    d = driver_at(1920, 1080)
    try:
        # --- Timer cause + functional tests ---
        d.get(f"{BASE}/?v=timerqa")
        wait_ready(d)
        cause = d.execute_script("return H2V4Timer.CAUSE;")
        report["cause"] = cause
        report["geometry"]["before_note"] = (
            "Prior debug overlay used viewport deltas as stage CSS px under scale(transform)."
        )

        d.execute_script("sessionStorage.removeItem(H2V4Timer.STORAGE_KEY); H2V4Timer.reset();")
        d.execute_script("H2V4Timer.setDuration(60); H2V4Timer.start();")
        t0 = d.execute_script("return H2V4Timer.computeRemaining(H2V4State.getState());")
        time.sleep(2.2)
        t1 = d.execute_script("return H2V4Timer.computeRemaining(H2V4State.getState());")
        report["timer"]["start_from_60"] = {"t0": t0, "t1": t1, "ok": t1 < t0 and t1 >= 57}
        if not report["timer"]["start_from_60"]["ok"]:
            report["ok"] = False

        d.execute_script("H2V4Timer.pause();")
        paused = d.execute_script("return H2V4State.getState().timer_paused_remaining;")
        time.sleep(1.0)
        paused2 = d.execute_script("return H2V4Timer.computeRemaining(H2V4State.getState());")
        report["timer"]["pause"] = {
            "paused_remaining": paused,
            "after_1s": paused2,
            "ok": paused == paused2 and paused is not None,
        }
        if not report["timer"]["pause"]["ok"]:
            report["ok"] = False

        d.execute_script("H2V4Timer.resume();")
        time.sleep(1.2)
        resumed = d.execute_script("return H2V4Timer.computeRemaining(H2V4State.getState());")
        report["timer"]["resume"] = {
            "after": resumed,
            "ok": resumed < paused2 and resumed >= 0,
        }
        if not report["timer"]["resume"]["ok"]:
            report["ok"] = False

        d.execute_script("H2V4Timer.reset();")
        reset_v = d.execute_script("return H2V4Timer.computeRemaining(H2V4State.getState());")
        active = d.execute_script("return H2V4State.getState().timer_active;")
        report["timer"]["reset"] = {"remaining": reset_v, "active": active, "ok": reset_v == 60 and not active}
        if not report["timer"]["reset"]["ok"]:
            report["ok"] = False

        # Fast complete to 0
        d.execute_script(
            """
            H2V4Timer.setDuration(2);
            H2V4Timer.start();
            """
        )
        time.sleep(2.6)
        done = d.execute_script(
            "return {rem:H2V4Timer.computeRemaining(H2V4State.getState()), active:H2V4State.getState().timer_active, text:document.getElementById('timer-value').textContent};"
        )
        report["timer"]["complete"] = {
            **done,
            "ok": done["rem"] == 0 and done["text"] == "00:00" and not done["active"],
        }
        if not report["timer"]["complete"]["ok"]:
            report["ok"] = False

        # Aging independence: capture aging before/after timer ops
        d.execute_script(
            """
            const fresh=50;
            H2V4State.patch({new_style:{aging:{
              fresh_delay_seconds:fresh, aging_duration_seconds:10,
              started_at:new Date(Date.now()-(fresh+5)*1000).toISOString(),
              paused:false, paused_elapsed_seconds:0
            }}});
            """
        )
        aging_a = d.execute_script("return H2V4AgingFx.agingProgress();")
        d.execute_script("H2V4Timer.setDuration(60); H2V4Timer.start(); H2V4Timer.pause(); H2V4Timer.reset();")
        aging_b = d.execute_script("return H2V4AgingFx.agingProgress();")
        report["timer"]["aging_independent"] = {
            "before": aging_a,
            "after": aging_b,
            "ok": abs(aging_a - aging_b) < 0.15,  # allow natural aging advance during test
        }

        # Plate switch while timer active
        d.execute_script("H2V4Timer.setDuration(60); H2V4Timer.start();")
        d.execute_script("H2V4State.patch({plate_type:'fujairah', code:'F', number:'4321'});")
        time.sleep(0.3)
        still = d.execute_script(
            "return {type:H2V4State.getState().plate_type, active:H2V4State.getState().timer_active, rem:H2V4Timer.computeRemaining(H2V4State.getState())};"
        )
        report["timer"]["plate_switch"] = {**still, "ok": still["type"] == "fujairah" and still["active"]}
        if not report["timer"]["plate_switch"]["ok"]:
            report["ok"] = False

        shot(d, "timer-running-1920.png")

        # --- Geometry matrix ---
        cases = [
            ("1920x1080-dubai-debug", 1920, 1080, f"{BASE}/?debug=1&plate_type=dubai&code=AA&number=7777"),
            ("1280x720-dubai-debug", 1280, 720, f"{BASE}/?debug=1&plate_type=dubai&code=AA&number=7777"),
            ("1920-fujairah", 1920, 1080, f"{BASE}/?debug=1&plate_type=fujairah&code=F&number=4321"),
            ("1920-du-phone", 1920, 1080, f"{BASE}/?debug=1&plate_type=du&phone=0501234567"),
        ]

        cur_w, cur_h = 1920, 1080
        for name, w, h, url in cases:
            if (w, h) != (cur_w, cur_h):
                d.quit()
                d = driver_at(w, h)
                cur_w, cur_h = w, h
            d.get(url)
            wait_ready(d)
            time.sleep(0.35)
            align = alignment(d)
            err = max_error(align)
            report["geometry"][name] = {
                "maxErrorPx": err,
                "align": align,
                "scale": d.execute_script("return H2V4Geom.getStageScale();"),
                "shot": shot(d, f"{name}.png"),
                "ok": err is not None and err <= TOL_PX,
            }
            if not report["geometry"][name]["ok"]:
                report["ok"] = False

        # SOLD + aging shots at 1920
        if d.execute_script("return window.innerWidth;") != 1920:
            d.quit()
            d = driver_at(1920, 1080)
        d.get(f"{BASE}/?debug=1&plate_type=dubai&code=AA&number=7777")
        wait_ready(d)
        d.execute_script("H2V4State.patch({trigger_sold:true, sold_style:'fireworks'});")
        time.sleep(0.5)
        stamp = d.execute_script(
            """
            const st=document.getElementById('plate-sold-stamp');
            const plate=document.getElementById('plate');
            const shell=document.getElementById('plate-shell');
            const num=document.getElementById('plate-number');
            const sb=H2V4Geom.elementStageBox(st);
            const pb=H2V4Geom.elementStageBox(plate);
            // Rotated stamp AABB may extend past plate; require center on plate surface
            const cx = sb.x + sb.w/2, cy = sb.y + sb.h/2;
            const centerInside = sb && pb
              && cx >= pb.x && cx <= pb.x+pb.w
              && cy >= pb.y && cy <= pb.y+pb.h;
            return {
              visible: !st.hidden,
              numberVisible: num.style.visibility !== 'hidden' && !num.hidden,
              stampInShell: st.parentElement === shell,
              stampCenterOnPlate: !!centerInside,
              fwZ: getComputedStyle(document.getElementById('plate-fw')).zIndex,
              shellZ: getComputedStyle(document.getElementById('plate-shell')).zIndex,
            };
            """
        )
        report["geometry"]["sold"] = {
            **stamp,
            "ok": stamp["visible"] and stamp["numberVisible"] and stamp["stampInShell"]
            and stamp["stampCenterOnPlate"] and int(stamp["fwZ"]) < int(stamp["shellZ"]),
            "shot": shot(d, "sold-1920-debug.png"),
        }
        if not report["geometry"]["sold"]["ok"]:
            report["ok"] = False

        d.execute_script(
            """
            H2V4SoldFx.clearSoldVisuals();
            const fresh=50;
            H2V4State.patch({new_style:{aging:{
              fresh_delay_seconds:fresh, aging_duration_seconds:10,
              started_at:new Date(Date.now()-(fresh+8)*1000).toISOString(),
              paused:false, paused_elapsed_seconds:0
            }}});
            """
        )
        time.sleep(0.4)
        aging = d.execute_script(
            """
            const aging=document.getElementById('plate-aging');
            const shell=document.getElementById('plate-shell');
            return {
              progress: H2V4AgingFx.agingProgress(),
              agingParentIsShell: aging.parentElement === shell,
              opacity: getComputedStyle(aging).opacity,
            };
            """
        )
        report["geometry"]["aging"] = {
            **aging,
            "ok": aging["progress"] > 0 and aging["agingParentIsShell"],
            "shot": shot(d, "aging-1920-debug.png"),
        }
        if not report["geometry"]["aging"]["ok"]:
            report["ok"] = False

        report["geometry"]["debug_overlay"] = {
            "shot": shot(d, "debug-overlay-1920.png"),
            "align": alignment(d),
        }

    finally:
        d.quit()

    out = OUT_DIR / "report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("WROTE", out)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
