"""Regression QA: control.html drives index.html via SyncBus (same Chrome profile)."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "page-separation"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"
REPORT = OUT / "SEPARATION_REPORT.md"


def shot(driver, name: str, w=1920, h=1080):
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    time.sleep(0.15)
    data = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
            "fromSurface": True,
        },
    )
    path = OUT / name
    path.write_bytes(base64.b64decode(data["data"]))
    return path


def wait_ready(d, timeout=20):
    WebDriverWait(d, timeout).until(
        lambda x: x.execute_script("return !!(window.H2V4State && window.H2PlateSystem);")
    )


def wait_control(d, timeout=20):
    WebDriverWait(d, timeout).until(
        lambda x: x.execute_script("return !!(window.H2V4SyncBus && document.getElementById('btn-apply-lot'));")
    )


def click(d, id_):
    d.find_element(By.ID, id_).click()
    time.sleep(0.35)


def set_input(d, id_, value):
    el = d.find_element(By.ID, id_)
    el.clear()
    el.send_keys(str(value))


def broadcast_state(d):
    return d.execute_script(
        """
        return {
          state: window.H2V4State.getState(),
          aging: window.H2V4AgingFx && window.H2V4AgingFx.getStatus ? window.H2V4AgingFx.getStatus() : null,
          hasControls: !!document.getElementById('btn-sold'),
          fwVisible: (function(){
            const c = document.getElementById('stage-fw');
            if (!c) return false;
            const ctx = c.getContext('2d');
            const data = ctx.getImageData(0,0,c.width,c.height).data;
            let n=0; for (let i=3;i<data.length;i+=16) if (data[i]>8) n++;
            return n > 40;
          })(),
          live1: (document.getElementById('live-text-line-1')||{}).textContent || '',
          live2: (document.getElementById('live-text-line-2')||{}).textContent || '',
          numberHidden: document.getElementById('plate-number')
            ? getComputedStyle(document.getElementById('plate-number')).visibility === 'hidden'
              || document.getElementById('plate-number').classList.contains('is-hidden')
              || document.getElementById('plate').classList.contains('number-hidden')
            : null,
          consoleErrors: window.__h2v4_err || [],
        };
        """
    )


def install_err_hook(d):
    d.execute_script(
        """
        window.__h2v4_err = window.__h2v4_err || [];
        window.addEventListener('error', e => window.__h2v4_err.push(String(e.message||e)));
        window.addEventListener('unhandledrejection', e => window.__h2v4_err.push(String(e.reason||e)));
        """
    )


def pixel_diff(a: Path, b: Path, threshold=12):
    try:
        from PIL import Image
        import numpy as np
    except Exception:
        return {"ok": False, "reason": "PIL/numpy unavailable"}
    ia = np.asarray(Image.open(a).convert("RGB"), dtype=np.int16)
    ib = np.asarray(Image.open(b).convert("RGB"), dtype=np.int16)
    if ia.shape != ib.shape:
        return {"ok": False, "reason": f"shape {ia.shape} vs {ib.shape}"}
    diff = np.abs(ia - ib).max(axis=2)
    changed = int((diff > threshold).sum())
    total = int(diff.size)
    return {
        "ok": True,
        "changed_px": changed,
        "pct": round(100.0 * changed / total, 4),
        "max_delta": int(diff.max()),
    }


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--window-size=1600,1000")
    # Same profile → BroadcastChannel works between windows
    d = webdriver.Chrome(options=opts)
    results = []

    def check(name, ok, detail=""):
        results.append({"name": name, "ok": bool(ok), "detail": detail})
        print(("PASS" if ok else "FAIL"), name, detail)

    try:
        # --- Broadcast window ---
        d.get(f"{BASE}/index.html?v=sepqa1")
        wait_ready(d)
        install_err_hook(d)
        d.execute_script("window.name = 'h2v4_broadcast';")
        broadcast_handle = d.current_window_handle

        # Clean baseline-comparable idle shot (default plate)
        shot(d, "final-broadcast-idle-1920x1080.png")
        baseline = OUT / "baseline-broadcast-1920x1080.png"
        if baseline.exists():
            # Baseline was captured with dubai AA 7777 query — match that
            d.get(f"{BASE}/index.html?plate_type=dubai&code=AA&number=7777&v=sepqa_base")
            wait_ready(d)
            install_err_hook(d)
            time.sleep(0.6)
            final_match = shot(d, "final-broadcast-vs-baseline-1920x1080.png")
            diff = pixel_diff(baseline, final_match)
            check(
                "visual_vs_baseline",
                diff.get("ok") and diff.get("pct", 99) < 0.35,
                json.dumps(diff),
            )
            d.get(f"{BASE}/index.html?v=sepqa2")
            wait_ready(d)
            install_err_hook(d)
            broadcast_handle = d.current_window_handle

        check("broadcast_has_no_admin_buttons", not d.execute_script("return !!document.getElementById('btn-sold');"))

        # --- Control window (same Chrome profile → BroadcastChannel works) ---
        d.switch_to.new_window("window")
        control_handle = d.current_window_handle
        d.get(f"{BASE}/control.html?v=sepqa1")
        wait_control(d)
        install_err_hook(d)
        shot(d, "admin-control-panel.png")

        # Plate / bid
        Select(d.find_element(By.ID, "plate-type")).select_by_value("sharjah")
        set_input(d, "code", "1")
        set_input(d, "number", "5555")
        set_input(d, "price", "999000")
        click(d, "btn-apply-lot")
        time.sleep(0.5)
        d.switch_to.window(broadcast_handle)
        st = broadcast_state(d)
        check(
            "plate_bid_sync",
            st["state"]["plate_type"] == "sharjah"
            and st["state"]["number"] == "5555"
            and str(st["state"]["price"]) in ("999000", "999,000"),
            json.dumps({"plate": st["state"]["plate_type"], "num": st["state"]["number"], "price": st["state"]["price"]}),
        )

        # Live text
        d.switch_to.window(control_handle)
        set_input(d, "live-text-1", "TEST LINE ONE")
        click(d, "btn-live-text-1-apply")
        set_input(d, "live-text-2", "TEST LINE TWO")
        click(d, "btn-live-text-2-apply")
        time.sleep(0.4)
        d.switch_to.window(broadcast_handle)
        st = broadcast_state(d)
        check("live_text_lines", st["live1"] == "TEST LINE ONE" and st["live2"] == "TEST LINE TWO", f"{st['live1']}|{st['live2']}")

        # Timer start/pause/resume
        d.switch_to.window(control_handle)
        set_input(d, "timer-seconds", "45")
        click(d, "btn-timer-start")
        time.sleep(1.2)
        d.switch_to.window(broadcast_handle)
        rem1 = broadcast_state(d)["state"]["timer_remaining_seconds"]
        active1 = broadcast_state(d)["state"]["timer_active"]
        check("timer_start", active1 and rem1 <= 45 and rem1 >= 42, f"rem={rem1} active={active1}")
        ends_at = broadcast_state(d)["state"]["timer_ends_at"]

        d.switch_to.window(control_handle)
        click(d, "btn-timer-pause")
        time.sleep(0.4)
        d.switch_to.window(broadcast_handle)
        st = broadcast_state(d)
        check("timer_pause", not st["state"]["timer_active"] and st["state"]["timer_paused_remaining"] is not None)

        d.switch_to.window(control_handle)
        click(d, "btn-timer-resume")
        time.sleep(0.5)
        d.switch_to.window(broadcast_handle)
        st = broadcast_state(d)
        check("timer_resume", st["state"]["timer_active"] and st["state"]["timer_ends_at"])

        d.switch_to.window(control_handle)
        click(d, "btn-timer-reset")
        time.sleep(0.4)
        d.switch_to.window(broadcast_handle)
        st = broadcast_state(d)
        check("timer_reset", not st["state"]["timer_active"] and st["state"]["timer_remaining_seconds"] == st["state"]["timer_seconds"])

        # Show/Hide
        d.switch_to.window(control_handle)
        click(d, "btn-hide")
        time.sleep(0.5)
        d.switch_to.window(broadcast_handle)
        st = broadcast_state(d)
        check("hide_number", st["state"]["new_style"]["number_visible"] is False)
        d.switch_to.window(control_handle)
        click(d, "btn-show")
        time.sleep(0.5)
        d.switch_to.window(broadcast_handle)
        check("show_number", broadcast_state(d)["state"]["new_style"]["number_visible"] is True)

        # Drop
        d.switch_to.window(control_handle)
        click(d, "btn-drop")
        time.sleep(0.8)
        d.switch_to.window(broadcast_handle)
        drop_id = broadcast_state(d)["state"]["new_style"]["events"]["drop_event_id"]
        check("number_drop", drop_id >= 1, f"drop_event_id={drop_id}")

        # Yellow / Red / Point
        d.switch_to.window(control_handle)
        click(d, "btn-yellow")
        time.sleep(1.0)
        d.switch_to.window(broadcast_handle)
        yid = broadcast_state(d)["state"]["new_style"]["events"]["char_yellow_event_id"]
        check("yellow_card", yid >= 1, f"id={yid}")
        shot(d, "broadcast-yellow-1920x1080.png")

        d.switch_to.window(control_handle)
        click(d, "btn-char-reset")
        time.sleep(0.5)
        click(d, "btn-red")
        time.sleep(1.0)
        d.switch_to.window(broadcast_handle)
        rid = broadcast_state(d)["state"]["new_style"]["events"]["char_red_event_id"]
        check("red_card", rid >= 1 and broadcast_state(d)["state"]["new_style"]["number_visible"] is False, f"id={rid}")
        shot(d, "broadcast-red-1920x1080.png")

        d.switch_to.window(control_handle)
        click(d, "btn-char-reset")
        click(d, "btn-show")
        time.sleep(0.4)
        click(d, "btn-point")
        time.sleep(0.8)
        d.switch_to.window(broadcast_handle)
        pid = broadcast_state(d)["state"]["new_style"]["events"]["char_point_event_id"]
        check("point_character", pid >= 1, f"id={pid}")

        # SOLD fireworks
        d.switch_to.window(control_handle)
        click(d, "btn-char-reset")
        time.sleep(0.3)
        click(d, "btn-sold")
        time.sleep(1.2)
        d.switch_to.window(broadcast_handle)
        st = broadcast_state(d)
        check("sold_event", st["state"]["sold_event_id"] >= 1, f"sold#{st['state']['sold_event_id']}")
        check("sold_fireworks_pixels", st["fwVisible"] is True)
        shot(d, "broadcast-sold-1920x1080.png")
        sold_before = st["state"]["sold_event_id"]

        # Aging
        d.switch_to.window(control_handle)
        Select(d.find_element(By.ID, "aging-enabled")).select_by_value("1")
        time.sleep(0.2)
        click(d, "btn-aging-start")
        time.sleep(1.0)
        d.switch_to.window(broadcast_handle)
        aging = broadcast_state(d)["aging"]
        check("aging_running", aging and aging.get("enabled") and (aging.get("running") or aging.get("elapsed_seconds", 0) > 0), json.dumps(aging))
        rem_timer = broadcast_state(d)["state"]["timer_remaining_seconds"]
        # Aging independent — timer should still be idle after reset earlier
        check("aging_independent_of_timer", broadcast_state(d)["state"]["timer_active"] is False, f"timer_rem={rem_timer}")

        d.switch_to.window(control_handle)
        click(d, "btn-aging-pause")
        time.sleep(0.3)
        click(d, "btn-aging-resume")
        time.sleep(0.3)
        click(d, "btn-aging-reset")
        time.sleep(0.4)
        d.switch_to.window(broadcast_handle)
        aging = broadcast_state(d)["aging"]
        check("aging_reset", aging and aging.get("elapsed_seconds", 1) < 0.5, json.dumps(aging))

        # Ambient floats
        d.switch_to.window(control_handle)
        Select(d.find_element(By.ID, "bg-motion")).select_by_value("1")
        click(d, "btn-bg-start")
        time.sleep(0.6)
        d.switch_to.window(broadcast_handle)
        bg = broadcast_state(d)["state"]["new_style"]
        check("ambient_on", bg.get("bg_motion_enabled") is True and bg.get("bg_motion_playing") is True)
        d.switch_to.window(control_handle)
        click(d, "btn-bg-stop")
        time.sleep(0.4)
        d.switch_to.window(broadcast_handle)
        check("ambient_stop", broadcast_state(d)["state"]["new_style"].get("bg_motion_playing") is False)

        # Display refresh — no sold replay
        d.switch_to.window(broadcast_handle)
        d.refresh()
        wait_ready(d)
        install_err_hook(d)
        time.sleep(0.8)
        st = broadcast_state(d)
        check("refresh_keeps_lot", st["state"]["plate_type"] == "sharjah" and st["state"]["number"] == "5555")
        check("refresh_no_sold_replay", st["state"]["sold_event_id"] == sold_before and st["fwVisible"] is False, f"sold={st['state']['sold_event_id']} fw={st['fwVisible']}")
        check("refresh_keeps_live_text", st["live1"] == "TEST LINE ONE" and st["live2"] == "TEST LINE TWO")

        # Control refresh form hydrate
        d.switch_to.window(control_handle)
        d.refresh()
        wait_control(d)
        time.sleep(0.5)
        code_val = d.find_element(By.ID, "code").get_attribute("value")
        check("control_refresh_hydrate", code_val == "1", f"code={code_val}")

        # 1280x720 broadcast
        d.switch_to.window(broadcast_handle)
        shot(d, "final-broadcast-1280x720.png", 1280, 720)

        # Clean broadcast idle final
        d.switch_to.window(control_handle)
        click(d, "btn-char-reset")
        click(d, "btn-aging-disable")
        Select(d.find_element(By.ID, "bg-motion")).select_by_value("0")
        click(d, "btn-bg-apply")
        click(d, "btn-live-text-1-clear")
        click(d, "btn-live-text-2-clear")
        Select(d.find_element(By.ID, "plate-type")).select_by_value("dubai")
        set_input(d, "code", "AA")
        set_input(d, "number", "7777")
        set_input(d, "price", "1250000")
        click(d, "btn-apply-lot")
        click(d, "btn-show")
        time.sleep(0.6)
        d.switch_to.window(broadcast_handle)
        time.sleep(0.4)
        shot(d, "final-broadcast-clean-1920x1080.png")
        shot(d, "admin-control-final.png")  # will be broadcast — fix below
        d.switch_to.window(control_handle)
        shot(d, "admin-control-final.png")

        errs_b = d.execute_script("return window.__h2v4_err || []") if False else []
        d.switch_to.window(broadcast_handle)
        errs_b = d.execute_script("return window.__h2v4_err || []")
        d.switch_to.window(control_handle)
        errs_c = d.execute_script("return window.__h2v4_err || []")
        check("no_console_errors", len(errs_b) == 0 and len(errs_c) == 0, json.dumps({"b": errs_b, "c": errs_c}))

    finally:
        d.quit()

    passed = sum(1 for r in results if r["ok"])
    failed = [r for r in results if not r["ok"]]
    lines = [
        "# H2 V4 Page Separation — Regression Report",
        "",
        f"- Passed: **{passed}/{len(results)}**",
        f"- Admin URL: `{BASE}/control.html`",
        f"- Broadcast URL: `{BASE}/index.html`",
        f"- Sync: BroadcastChannel `{ 'h2-v4-sandbox-sync' }` + localStorage snapshot",
        "",
        "## OBS limitation",
        "",
        "Sandbox sync (BroadcastChannel + localStorage) only works inside the **same browser profile/origin**.",
        "OBS Browser Source typically uses a separate Chromium process and **will not** receive these messages.",
        "Do not claim production OBS sync from same-browser tab tests. Production path: Django session/API (unchanged).",
        "",
        "## Checklist",
        "",
    ]
    for r in results:
        mark = "PASS" if r["ok"] else "FAIL"
        lines.append(f"- [{mark}] {r['name']}: {r['detail']}")
    lines += [
        "",
        "## Artifacts",
        "",
        "- `baseline-broadcast-1920x1080.png`",
        "- `final-broadcast-vs-baseline-1920x1080.png`",
        "- `final-broadcast-clean-1920x1080.png`",
        "- `admin-control-panel.png`",
        "- `admin-control-final.png`",
        "- `broadcast-sold-1920x1080.png`",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {REPORT}")
    print(f"Result: {passed}/{len(results)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
