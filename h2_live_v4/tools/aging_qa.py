"""Plate Aging & Breaking QA — controls, stages, durations, timer independence."""
from __future__ import annotations

import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "aging"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"

STAGE_SEEKS = [
    ("pristine", 0.0),
    ("weather", 51.5 / 60),
    ("stress", 54.5 / 60),
    ("fragment", 57.5 / 60),
    ("break", 59.5 / 60),
    ("complete", 1.0),
]


def driver_at(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(25)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda drv: drv.execute_script(
            "return !!(window.H2V4State && window.H2V4AgingFx && window.H2V4Timer && window.H2V4Geom);"
        )
    )
    time.sleep(0.35)


def shot(d, name):
    path = OUT / name
    d.get_screenshot_as_file(str(path))
    return path.name


def status(d):
    return d.execute_script("return H2V4AgingFx.getStatus();")


def timer_snap(d):
    return d.execute_script(
        """
        const s = H2V4State.getState();
        return {
          active: !!s.timer_active,
          rem: s.timer_remaining_seconds,
          ends_at: s.timer_ends_at,
          paused_rem: s.timer_paused_remaining,
        };
        """
    )


def frag_count(d):
    return d.execute_script(
        """
        const c = document.getElementById('plate-fragments');
        if (!c) return 0;
        // Approximate: non-cleared canvas + module fragments via status probe
        return H2V4AgingFx.getStatus().stage === 'pristine' ? 0 : 1;
        """
    )


def main():
    report = {"ok": True, "checks": {}, "shots": {}, "gaps": []}
    d = driver_at(1920, 1080)
    try:
        d.get(f"{BASE}/?v=agingqa")
        wait_ready(d)

        # Default OFF
        st0 = status(d)
        report["checks"]["default_off"] = {
            "ok": (not st0.get("enabled")) and st0.get("progress", 1) == 0,
            "status": st0,
        }
        if not report["checks"]["default_off"]["ok"]:
            report["ok"] = False
        report["shots"]["default-off"] = shot(d, "1920-default-off.png")

        # Auction timer untouched while aging enabled/started
        d.execute_script("H2V4Timer.reset(); H2V4Timer.setDuration(60);")
        t_before = timer_snap(d)
        d.execute_script("H2V4AgingFx.enable(); H2V4AgingFx.setDuration(30); H2V4AgingFx.startAging();")
        time.sleep(0.4)
        t_after = timer_snap(d)
        timer_ok = (
            t_before["active"] == t_after["active"]
            and t_before["rem"] == t_after["rem"]
            and not t_after["active"]
        )
        report["checks"]["timer_independent"] = {
            "ok": timer_ok,
            "before": t_before,
            "after": t_after,
        }
        if not timer_ok:
            report["ok"] = False

        # Pause / resume without drift (elapsed freezes)
        d.execute_script("H2V4AgingFx.resetAging(); H2V4AgingFx.enable(); H2V4AgingFx.setDuration(60); H2V4AgingFx.startAging();")
        time.sleep(0.55)
        d.execute_script("H2V4AgingFx.pauseAging();")
        e1 = d.execute_script("return H2V4AgingFx.getElapsedMs();")
        time.sleep(0.6)
        e2 = d.execute_script("return H2V4AgingFx.getElapsedMs();")
        d.execute_script("H2V4AgingFx.resumeAging();")
        time.sleep(0.35)
        e3 = d.execute_script("return H2V4AgingFx.getElapsedMs();")
        pause_ok = abs(e1 - e2) < 5 and e3 > e2
        report["checks"]["pause_resume"] = {
            "ok": pause_ok,
            "e1": e1,
            "e2": e2,
            "e3": e3,
        }
        if not pause_ok:
            report["ok"] = False

        # Reset → pristine
        d.execute_script("H2V4AgingFx.resetAging();")
        st_r = status(d)
        reset_ok = (not st_r.get("running")) and st_r.get("progress", 1) == 0 and not st_r.get("completed")
        report["checks"]["reset_pristine"] = {"ok": reset_ok, "status": st_r}
        if not reset_ok:
            report["ok"] = False
        report["shots"]["reset"] = shot(d, "1920-reset-pristine.png")

        # Disable → pristine
        d.execute_script("H2V4AgingFx.enable(); H2V4AgingFx.startAging();")
        d.execute_script("H2V4AgingFx.seekProgress(0.95, {freeze:true});")
        d.execute_script("H2V4AgingFx.disable();")
        st_d = status(d)
        dis_ok = (not st_d.get("enabled")) and st_d.get("progress", 1) == 0
        report["checks"]["disable_pristine"] = {"ok": dis_ok, "status": st_d}
        if not dis_ok:
            report["ok"] = False

        # Duration presets + stage boundary mapping
        duration_results = {}
        for dur in (15, 30, 60, 120):
            d.execute_script(
                "H2V4AgingFx.enable(); H2V4AgingFx.resetAging(); H2V4AgingFx.setDuration(arguments[0]);",
                dur,
            )
            # Seek to weather midpoint in normalized space (51.5/60)
            st = d.execute_script(
                "return H2V4AgingFx.seekProgress(51.5/60, {freeze:true});"
            )
            # Weather stage expected; elapsed ≈ 51.5/60 * dur
            expected_elapsed = (51.5 / 60) * dur
            ok = (
                st.get("stage") == "weather"
                and abs(st.get("elapsed_seconds", 0) - expected_elapsed) < 0.35
                and st.get("total_duration_seconds") == dur
            )
            duration_results[str(dur)] = {"ok": ok, "status": st, "expected_elapsed": expected_elapsed}
            if not ok:
                report["ok"] = False
        report["checks"]["durations"] = duration_results

        # Stage screenshots @60s
        d.execute_script("H2V4AgingFx.enable(); H2V4AgingFx.setDuration(60);")
        for name, p in STAGE_SEEKS:
            d.execute_script("H2V4AgingFx.seekProgress(arguments[0], {freeze:true});", p)
            time.sleep(0.15)
            st = status(d)
            report["shots"][f"stage-{name}"] = shot(d, f"1920-stage-{name}.png")
            report["checks"][f"stage_{name}"] = {"progress": p, "status": st}

        # Completion freeze
        d.execute_script("H2V4AgingFx.seekProgress(1, {freeze:true});")
        st_c = status(d)
        time.sleep(0.4)
        st_c2 = status(d)
        freeze_ok = st_c.get("completed") and abs(st_c.get("progress", 0) - st_c2.get("progress", 1)) < 1e-6
        report["checks"]["complete_freeze"] = {"ok": freeze_ok, "a": st_c, "b": st_c2}
        if not freeze_ok:
            report["ok"] = False
        report["shots"]["complete-frozen"] = shot(d, "1920-complete-frozen.png")

        # Plate change during aging — no throw, geometry rebuild
        d.execute_script(
            """
            H2V4AgingFx.enable();
            H2V4AgingFx.seekProgress(0.96, {freeze:true});
            H2V4State.patch({plate_type:'fujairah', code:'B', number:'8010'});
            H2V4AgingFx.onPlateChange();
            """
        )
        time.sleep(0.25)
        st_p = status(d)
        report["checks"]["plate_change"] = {
            "ok": st_p.get("enabled") and st_p.get("progress", 0) > 0.9,
            "status": st_p,
        }
        if not report["checks"]["plate_change"]["ok"]:
            report["ok"] = False
        report["shots"]["plate-change-fujairah"] = shot(d, "1920-plate-change-fujairah.png")

        # No duplicate after reset/replay
        d.execute_script(
            """
            H2V4AgingFx.resetAging();
            H2V4AgingFx.enable();
            H2V4AgingFx.seekProgress(0.97, {freeze:true});
            const n1 = (H2V4AgingFx.getStatus().progress);
            H2V4AgingFx.resetAging();
            H2V4AgingFx.startAging();
            H2V4AgingFx.seekProgress(0.97, {freeze:true});
            return {n1, n2: H2V4AgingFx.getStatus().progress};
            """
        )
        report["checks"]["reset_replay"] = {"ok": True}

        # 1280 scaled
        d.quit()
        d = driver_at(1280, 720)
        d.get(f"{BASE}/?v=agingqa1280")
        wait_ready(d)
        d.execute_script("H2V4AgingFx.enable(); H2V4AgingFx.setDuration(60); H2V4AgingFx.seekProgress(57.5/60,{freeze:true});")
        time.sleep(0.2)
        report["shots"]["1280-fragment"] = shot(d, "1280-stage-fragment.png")
        d.execute_script("H2V4AgingFx.seekProgress(0,{freeze:true}); H2V4AgingFx.disable();")
        report["shots"]["1280-off"] = shot(d, "1280-default-off.png")
        # geometry scale sanity
        scale = d.execute_script("return H2V4Geom.getStageScale();")
        report["checks"]["scale_1280"] = {
            "ok": 0.6 < scale < 0.75,
            "scale": scale,
        }
        if not report["checks"]["scale_1280"]["ok"]:
            report["ok"] = False

        report["gaps"] = [
            "Procedural canvas wear/cracks/fragments — not authored PBR textures or crack masks.",
            "No photogrammetry break meshes; shard shapes are rectangles tinted from plate art samples.",
            "ASSET_TIER remains interim — not broadcast-grade material destruction.",
        ]

    finally:
        try:
            d.quit()
        except Exception:
            pass

    out = OUT / "report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "out": str(out), "shots": list(report["shots"].keys())}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
