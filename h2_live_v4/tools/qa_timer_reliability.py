"""E2E QA — Django V4 live timer reliability (cache v=20261113timer1)."""
from __future__ import annotations

import json
import os
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "h3auctions.settings")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ALLOWED_HOSTS", "127.0.0.1,localhost")
sys.path.insert(0, r"c:\Users\moham\h3")

import django

django.setup()

from plates.models import LiveBroadcastSession  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

BASE = "http://127.0.0.1:8000"
CACHE = "20261113timer1"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\timer_reliability"
os.makedirs(OUT, exist_ok=True)
RESULTS: dict[str, dict] = {}


def record(name: str, ok: bool, detail: object = "") -> None:
    RESULTS[name] = {"ok": bool(ok), "detail": detail}
    print(("PASS" if ok else "FAIL"), name, detail if detail != "" else "")


def chrome(w: int = 1280, h: int = 720) -> webdriver.Chrome:
    opts = Options()
    # Headless throttles timers; use headed for accurate countdown samples when possible.
    # Fall back to headless=new if display unavailable.
    # Headless throttles timers; use headed for accurate countdown (see qa_sequential_drop).
    opts.add_argument(f"--window-size={w},{h}")
    opts.add_argument("--force-device-scale-factor=1")
    d = webdriver.Chrome(options=opts)
    d.set_window_size(w, h)
    return d


def hard_refresh(driver, url: str) -> None:
    driver.get(url)
    WebDriverWait(driver, 25).until(lambda x: x.execute_script("return document.readyState") == "complete")
    driver.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
    time.sleep(0.5)


def login(ctrl) -> None:
    ctrl.get(f"{BASE}/live/login/?next=/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "button[type=submit], input[type=submit]").click()
    WebDriverWait(ctrl, 20).until(EC.url_contains("/live/"))
    ctrl.get(f"{BASE}/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.url_contains("/live/control/v4"))


def click_id(ctrl, eid: str) -> None:
    el = ctrl.find_element(By.ID, eid)
    ctrl.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", el)


def set_duration(ctrl, seconds: int) -> None:
    el = ctrl.find_element(By.ID, "timer-seconds")
    el.clear()
    el.send_keys(str(seconds))
    click_id(ctrl, "btn-timer-duration")
    time.sleep(0.4)


def probe_disp(disp) -> dict:
    return disp.execute_script(
        """
        const st = H2V4State.getState();
        const el = document.getElementById('timer-value');
        const rem = H2V4Timer.computeRemaining(st);
        return {
          text: el ? el.textContent : null,
          rem,
          active: !!st.timer_active,
          ends_at: st.timer_ends_at,
          duration: st.timer_seconds,
          paused: st.timer_paused_remaining,
          cache: !!document.querySelector('script[src*="timer-controller.js?v=20261113timer1"]'),
          offset: H2V4State.getClockOffsetMs ? H2V4State.getClockOffsetMs() : null,
        };
        """
    )


def parse_mmss(text: str) -> int:
    parts = str(text or "0:0").split(":")
    return int(parts[0]) * 60 + int(parts[1])


def main() -> int:
    sess = LiveBroadcastSession.objects.order_by("-id").first()
    if not sess:
        record("session", False, "no LiveBroadcastSession")
        return 1
    token = sess.display_token

    ctrl = chrome()
    disp = chrome()
    disp2 = chrome()
    try:
        login(ctrl)
        hard_refresh(ctrl, f"{BASE}/live/control/v4/")
        hard_refresh(disp, f"{BASE}/live/display-v4/{token}/")
        hard_refresh(disp2, f"{BASE}/live/display-v4/{token}/")
        time.sleep(0.8)
        record("cache_bust", probe_disp(disp)["cache"], CACHE)

        # Reset clean
        click_id(ctrl, "btn-timer-reset")
        time.sleep(0.5)

        # --- A: Start accuracy 60s ---
        set_duration(ctrl, 60)
        time.sleep(0.5)
        before = probe_disp(disp)
        before_ok = before["text"] == "01:00" or before["rem"] == 60
        record("A_idle_shows_60", before_ok, before)

        click_id(ctrl, "btn-timer-start")
        # Sample immediately and for ~1.2s
        samples = []
        t0 = time.time()
        while time.time() - t0 < 1.2:
            samples.append(probe_disp(disp))
            time.sleep(0.05)
        first = samples[0]
        # Must not start at 58; allow 60 or 59 within first 50ms only if latency — require max of early samples >= 59 and first sample >= 59
        early_rems = [s["rem"] for s in samples[:6]]
        start_ok = max(early_rems) >= 59 and min(early_rems) >= 58 and early_rems[0] >= 59
        # Prefer exact 60 on first paint
        start_exact = early_rems[0] == 60
        record(
            "A_start_not_stale",
            start_ok,
            {"early": early_rems, "first_text": first["text"], "exact60": start_exact},
        )

        # Real-time rate: after ~3s wall, rem should drop ~3
        time.sleep(3.0)
        mid = probe_disp(disp)
        drop = early_rems[0] - mid["rem"]
        rate_ok = 2 <= drop <= 5
        record("A_realtime_rate", rate_ok, {"drop": drop, "mid": mid})

        # --- B: Pause / Resume ---
        click_id(ctrl, "btn-timer-reset")
        time.sleep(0.3)
        set_duration(ctrl, 60)
        click_id(ctrl, "btn-timer-start")
        time.sleep(2.5)
        click_id(ctrl, "btn-timer-pause")
        time.sleep(0.3)
        p1 = probe_disp(disp)
        time.sleep(1.5)
        p2 = probe_disp(disp)
        pause_ok = p1["rem"] == p2["rem"] and p1["rem"] > 0 and not p2["active"]
        record("B_pause_holds", pause_ok, {"p1": p1, "p2": p2})
        paused_at = p2["rem"]
        click_id(ctrl, "btn-timer-resume")
        time.sleep(0.4)
        r1 = probe_disp(disp)
        time.sleep(1.2)
        r2 = probe_disp(disp)
        resume_ok = r1["active"] and abs(r1["rem"] - paused_at) <= 1 and r2["rem"] < r1["rem"]
        record("B_resume_continues", resume_ok, {"paused_at": paused_at, "r1": r1, "r2": r2})

        # --- C: Refresh while running ---
        click_id(ctrl, "btn-timer-reset")
        set_duration(ctrl, 120)
        click_id(ctrl, "btn-timer-start")
        time.sleep(2.0)
        before_ref = probe_disp(disp)
        hard_refresh(disp, f"{BASE}/live/display-v4/{token}/")
        time.sleep(1.0)
        after_ref = probe_disp(disp)
        # Should still be running near previous remaining (not reset to 120)
        ref_ok = (
            after_ref["active"]
            and after_ref["rem"] <= before_ref["rem"] + 1
            and after_ref["rem"] >= before_ref["rem"] - 5
            and after_ref["rem"] < 120
        )
        record("C_refresh_preserves", ref_ok, {"before": before_ref, "after": after_ref})

        # --- E: Two displays ---
        click_id(ctrl, "btn-timer-reset")
        set_duration(ctrl, 60)
        click_id(ctrl, "btn-timer-start")
        time.sleep(1.0)
        d1 = probe_disp(disp)
        d2 = probe_disp(disp2)
        sync_ok = abs(d1["rem"] - d2["rem"]) <= 1 and d1["active"] and d2["active"]
        record("E_two_displays_sync", sync_ok, {"d1": d1, "d2": d2})

        # --- F: Completion to zero (10s) ---
        click_id(ctrl, "btn-timer-reset")
        set_duration(ctrl, 10)
        click_id(ctrl, "btn-timer-start")
        saw = []
        t0 = time.time()
        while time.time() - t0 < 14:
            saw.append(probe_disp(disp))
            time.sleep(0.25)
        texts = [s["text"] for s in saw]
        rems = [s["rem"] for s in saw]
        hit_zero = any(r == 0 for r in rems) or any(t == "00:00" for t in texts)
        # Must not freeze forever above 0 while claiming active at end
        last = saw[-1]
        stuck_above = last["rem"] > 0 and last["active"] and (time.time() - t0) > 12
        # After zero, stay at zero
        zero_idx = next((i for i, r in enumerate(rems) if r == 0), None)
        stays_zero = True
        if zero_idx is not None:
            stays_zero = all(r == 0 for r in rems[zero_idx:])
        # Never negative
        no_neg = all(r >= 0 for r in rems)
        # Did not freeze at 1/2/3 without completing
        froze_early = (not hit_zero) and any(r in (1, 2, 3) for r in rems[-5:])
        record(
            "F_reaches_zero",
            hit_zero and stays_zero and no_neg and not stuck_above and not froze_early,
            {
                "hit_zero": hit_zero,
                "stays_zero": stays_zero,
                "last": last,
                "min_rem": min(rems),
                "froze_early": froze_early,
            },
        )

        # Refresh after complete must stay 00:00
        hard_refresh(disp, f"{BASE}/live/display-v4/{token}/")
        time.sleep(0.8)
        post = probe_disp(disp)
        record(
            "F_refresh_stays_zero",
            post["rem"] == 0 and post["text"] == "00:00",
            post,
        )

        # Double-start safety
        click_id(ctrl, "btn-timer-reset")
        set_duration(ctrl, 30)
        click_id(ctrl, "btn-timer-start")
        click_id(ctrl, "btn-timer-start")
        time.sleep(0.3)
        ds = probe_disp(disp)
        record("double_start_ok", ds["active"] and 28 <= ds["rem"] <= 30, ds)

        report = {"cache": CACHE, "results": RESULTS, "pass": all(v["ok"] for v in RESULTS.values())}
        with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("OVERALL", "PASS" if report["pass"] else "FAIL")
        return 0 if report["pass"] else 1
    finally:
        ctrl.quit()
        disp.quit()
        disp2.quit()


if __name__ == "__main__":
    raise SystemExit(main())
