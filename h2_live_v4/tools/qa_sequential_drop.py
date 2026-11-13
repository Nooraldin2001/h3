"""E2E QA — sequential digit-by-digit Number Drop (v=20261113drop1)."""
from __future__ import annotations

import base64
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
from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402

BASE = "http://127.0.0.1:8000"
CACHE = "20261113drop1"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\sequential_drop"
os.makedirs(OUT, exist_ok=True)
RESULTS: dict[str, dict] = {}


def record(name: str, ok: bool, detail: object = "") -> None:
    RESULTS[name] = {"ok": bool(ok), "detail": detail}
    print(("PASS" if ok else "FAIL"), name, detail if detail != "" else "")


def chrome(w: int = 1920, h: int = 1080) -> webdriver.Chrome:
    opts = Options()
    # Foreground window: background tabs throttle drop stagger timers (false simultaneous fall).
    # opts.add_argument("--headless=new")
    opts.add_argument(f"--window-size={w},{h}")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--hide-scrollbars")
    d = webdriver.Chrome(options=opts)
    d.set_window_size(w, h)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def hard_refresh(driver, url: str) -> None:
    driver.get(url)
    WebDriverWait(driver, 25).until(lambda x: x.execute_script("return document.readyState") == "complete")
    driver.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
    time.sleep(0.6)


def shot(driver, path: str, w: int = 1920, h: int = 1080) -> str:
    data = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
        },
    )
    with open(path, "wb") as f:
        f.write(base64.b64decode(data["data"]))
    return path


def login(ctrl) -> None:
    ctrl.get(f"{BASE}/accounts/login/?next=/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "button[type=submit], input[type=submit]").click()
    WebDriverWait(ctrl, 20).until(EC.url_contains("/live/control"))


def set_lot(ctrl, number: str, code: str = "AA") -> None:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value("dubai")
    code_el = ctrl.find_element(By.ID, "code")
    code_el.clear()
    code_el.send_keys(code)
    num_el = ctrl.find_element(By.ID, "number")
    num_el.clear()
    num_el.send_keys(number)
    ctrl.find_element(By.ID, "btn-apply-lot").click()
    time.sleep(0.7)


def click_id(ctrl, eid: str) -> None:
    el = ctrl.find_element(By.ID, eid)
    ctrl.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.15)
    ctrl.execute_script("arguments[0].click();", el)


def probe_drop(disp) -> dict:
    return disp.execute_script(
        """
        const num = document.getElementById('plate-number');
        const st = H2V4State.getState();
        const glyphs = Array.from(num.querySelectorAll(':scope > .plate-num')).map(s => ({
          t: s.textContent,
          vis: getComputedStyle(s).visibility,
          opacity: getComputedStyle(s).opacity,
          left: s.getBoundingClientRect().left,
        }));
        const fallers = Array.from(document.querySelectorAll('.plate-digit-fall')).map(f => ({
          t: f.textContent,
          left: f.getBoundingClientRect().left,
          top: f.getBoundingClientRect().top,
          opacity: getComputedStyle(f).opacity,
        }));
        return {
          busy: !!(window.H2V4BeamDropFx && H2V4BeamDropFx.isDropBusy()),
          number_visible: st.new_style?.number_visible !== false,
          text: (num.textContent || '').trim(),
          aria: num.getAttribute('aria-hidden'),
          opacity: getComputedStyle(num).opacity,
          visibility: getComputedStyle(num).visibility,
          glyphs,
          fallers,
          cacheHit: !!document.querySelector('script[src*="fx-beam-drop.js?v=20261113drop1"]'),
        };
        """
    )


def sample_cascade(disp, duration_s: float = 2.2, every_ms: int = 80) -> list[dict]:
    samples = []
    end = time.time() + duration_s
    while time.time() < end:
        samples.append(probe_drop(disp))
        time.sleep(every_ms / 1000.0)
    return samples


def analyze_stagger(samples: list[dict], expected: str) -> dict:
    """Detect that faller starts appear one-by-one (not all at once)."""
    first_seen: dict[str, float] = {}
    # Track by count of fallers and which glyphs are hidden over time
    hide_events = []
    for i, s in enumerate(samples):
        t = i * 0.08
        hidden_idx = [
            gi
            for gi, g in enumerate(s.get("glyphs") or [])
            if g.get("vis") == "hidden" or float(g.get("opacity") or 1) < 0.05
        ]
        fall_texts = [f.get("t") for f in (s.get("fallers") or [])]
        if hidden_idx:
            hide_events.append({"t": t, "hidden": list(hidden_idx), "fallers": fall_texts})
        for f in s.get("fallers") or []:
            key = f"{f.get('t')}@{round(f.get('left') or 0)}"
            if key not in first_seen:
                first_seen[key] = t

    # Distinct start times of fallers (by left position order)
    starts = sorted(first_seen.values())
    gaps = [starts[i + 1] - starts[i] for i in range(len(starts) - 1)] if len(starts) > 1 else []
    # Hidden-count should grow over time for multi-digit
    max_hidden = 0
    growth_steps = 0
    prev = -1
    for ev in hide_events:
        n = len(ev["hidden"])
        if n > prev:
            growth_steps += 1
            prev = n
        max_hidden = max(max_hidden, n)

    ok_len = len(expected)
    staggered = True
    if ok_len >= 2:
        # Need at least 2 growth steps and average gap >= 0.12s (allowing poll jitter)
        staggered = growth_steps >= min(ok_len, 3) and (
            not gaps or (sum(gaps) / len(gaps) >= 0.12) or growth_steps >= ok_len
        )
        # Fail hard if first sample already has all digits hidden + no fallers progression
        if hide_events and len(hide_events[0]["hidden"]) >= ok_len and growth_steps <= 1:
            staggered = False

    return {
        "expected": expected,
        "faller_starts": starts,
        "gaps": gaps,
        "growth_steps": growth_steps,
        "max_hidden": max_hidden,
        "staggered": staggered,
        "sample_count": len(samples),
        "hide_events_head": hide_events[:8],
    }


def main() -> int:
    # Ensure session exists
    LiveBroadcastSession.objects.filter(pk=1).exists() or LiveBroadcastSession.objects.create(pk=1)

    ctrl = chrome()
    disp = chrome()
    try:
        login(ctrl)
        sess = LiveBroadcastSession.objects.order_by("-id").first()
        token = sess.display_token
        hard_refresh(ctrl, f"{BASE}/live/control/v4/")
        hard_refresh(disp, f"{BASE}/live/display-v4/{token}/")
        time.sleep(0.8)

        cache_ok = disp.execute_script(
            "return !!document.querySelector('script[src*=\"fx-beam-drop.js?v=20261113drop1\"]')"
        )
        record("cache_bust", cache_ok, CACHE)

        # --- Test A: 8258 sequential ---
        set_lot(ctrl, "8258")
        click_id(ctrl, "btn-show")
        time.sleep(0.5)
        before = probe_drop(disp)
        record("A_visible_before", before["text"] == "8258" and before["number_visible"], before)

        click_id(ctrl, "btn-drop")
        samples = sample_cascade(disp, duration_s=2.4, every_ms=70)
        # Mid-cascade screenshot
        mid = next((s for s in samples if 0 < len(s.get("fallers") or []) < 4), None)
        if mid is None:
            mid = next((s for s in samples if s.get("busy")), samples[min(5, len(samples) - 1)])
        # Re-sample a still frame near early cascade
        time.sleep(0.05)
        shot(disp, os.path.join(OUT, "8258_drop_mid.png"))
        analysis = analyze_stagger(samples, "8258")
        record("A_sequential_8258", analysis["staggered"] and analysis["max_hidden"] >= 3, analysis)
        with open(os.path.join(OUT, "8258_cascade.json"), "w", encoding="utf-8") as f:
            json.dump({"analysis": analysis, "samples": samples[::3]}, f, indent=2)

        # Wait for settle
        time.sleep(1.2)
        after = probe_drop(disp)
        hidden_ok = (not after["number_visible"]) and (
            after["visibility"] == "hidden" or float(after["opacity"] or 1) < 0.05 or after["aria"] == "true"
        )
        record("B_hidden_after", hidden_ok and not after["busy"], after)
        shot(disp, os.path.join(OUT, "8258_drop_hidden.png"))

        # Refresh persistence
        hard_refresh(disp, f"{BASE}/live/display-v4/{token}/")
        time.sleep(1.0)
        refreshed = probe_drop(disp)
        persist_ok = refreshed["number_visible"] is False and (
            refreshed["visibility"] == "hidden"
            or float(refreshed["opacity"] or 1) < 0.05
            or refreshed["aria"] == "true"
        )
        record("B_refresh_stays_hidden", persist_ok, refreshed)

        click_id(ctrl, "btn-show")
        time.sleep(0.8)
        shown = probe_drop(disp)
        record("B_show_restores_8258", shown["text"] == "8258" and shown["number_visible"], shown)
        shot(disp, os.path.join(OUT, "8258_show_restore.png"))

        # --- Test C: lengths ---
        for num in ["1", "11", "123", "12345"]:
            set_lot(ctrl, num)
            click_id(ctrl, "btn-show")
            time.sleep(0.4)
            click_id(ctrl, "btn-drop")
            samp = sample_cascade(disp, duration_s=min(2.8, 0.35 * len(num) + 1.0), every_ms=70)
            an = analyze_stagger(samp, num)
            ok = an["staggered"] if len(num) > 1 else an["max_hidden"] >= 1 or any(
                s.get("busy") for s in samp
            )
            record(f"C_len_{num}", ok, an)
            time.sleep(0.9)

        # --- Test D: new number during drop ---
        set_lot(ctrl, "8258")
        click_id(ctrl, "btn-show")
        time.sleep(0.4)
        click_id(ctrl, "btn-drop")
        time.sleep(0.35)
        mid_busy = probe_drop(disp)
        set_lot(ctrl, "7777")
        time.sleep(1.0)
        after_new = probe_drop(disp)
        interrupt_ok = (
            after_new["text"] == "7777"
            and after_new["number_visible"]
            and not after_new["busy"]
            and len(after_new.get("fallers") or []) == 0
        )
        record(
            "D_interrupt_new_lot",
            interrupt_ok,
            {"mid": mid_busy, "after": after_new},
        )
        shot(disp, os.path.join(OUT, "interrupt_7777.png"))

        # --- Test E: light regression sold ---
        click_id(ctrl, "btn-sold")
        time.sleep(1.0)
        sold_on = disp.execute_script(
            """
            const s = document.getElementById('plate-sold-stamp');
            return !!(s && s.classList.contains('imprint') && getComputedStyle(s).opacity !== '0');
            """
        )
        click_id(ctrl, "btn-cancel-sold")
        time.sleep(0.6)
        sold_off = disp.execute_script(
            """
            const s = document.getElementById('plate-sold-stamp');
            return !s || s.hidden || !s.classList.contains('imprint') || getComputedStyle(s).opacity === '0';
            """
        )
        record("E_sold_unsold", sold_on and sold_off, {"sold_on": sold_on, "sold_off": sold_off})

        report = {
            "cache": CACHE,
            "results": RESULTS,
            "pass": all(v["ok"] for v in RESULTS.values()),
        }
        with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("OVERALL", "PASS" if report["pass"] else "FAIL")
        return 0 if report["pass"] else 1
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
