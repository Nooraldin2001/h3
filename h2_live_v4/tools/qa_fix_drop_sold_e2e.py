"""E2E QA — Number Drop persistence, cancel SOLD, new-lot visibility (v=20261112fix1)."""
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
from plates.new_style import normalize_new_style  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402

BASE = "http://127.0.0.1:8000"
CACHE = "20261112fix1"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\fix_drop_sold"
os.makedirs(OUT, exist_ok=True)

LETTER_RESULTS: dict[str, dict] = {}


def record(letter: str, ok: bool, detail: object = "") -> None:
    LETTER_RESULTS[letter] = {"ok": bool(ok), "detail": detail}
    print(("PASS" if ok else "FAIL"), f"Test_{letter}", detail if detail != "" else "")


def chrome(w: int = 1920, h: int = 1080) -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
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
    time.sleep(0.5)


def shot_cdp(driver, path: str) -> str:
    data = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1},
        },
    )
    with open(path, "wb") as f:
        f.write(base64.b64decode(data["data"]))
    return path


def probe_number(disp) -> dict:
    return disp.execute_script(
        """
        const st = H2V4State.getState();
        const num = document.getElementById('plate-number');
        const cs = num ? getComputedStyle(num) : null;
        return {
          number: String(st.number || ''),
          number_visible: st.new_style?.number_visible !== false,
          digitVis: num ? num.style.visibility : null,
          elHidden: num ? (num.classList.contains('is-hidden') || num.style.visibility === 'hidden') : null,
          digitText: num ? (num.textContent || '').trim() : null,
          digitOpacity: cs ? cs.opacity : null,
          dropBusy: !!(window.H2V4BeamDropFx && H2V4BeamDropFx.isDropBusy && H2V4BeamDropFx.isDropBusy()),
        };
        """
    )


def digits_hidden(p: dict | None) -> bool:
    if not p:
        return False
    return p.get("number_visible") is False and (
        p.get("digitVis") == "hidden" or p.get("elHidden") is True
    )


def digits_visible(p: dict | None, number: str) -> bool:
    if not p:
        return False
    return (
        p.get("number_visible") is True
        and p.get("digitVis") != "hidden"
        and p.get("elHidden") is not True
        and number in (p.get("digitText") or p.get("number") or "")
    )


def wait_digits_hidden(disp, timeout: float = 10.0) -> dict | None:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        last = probe_number(disp)
        if digits_hidden(last) and not last.get("dropBusy"):
            return last
        time.sleep(0.12)
    return last


def wait_digits_visible(disp, number: str, timeout: float = 8.0) -> dict | None:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        last = probe_number(disp)
        if digits_visible(last, number) and not last.get("dropBusy"):
            return last
        time.sleep(0.12)
    return last


def probe_sold(disp) -> dict:
    return disp.execute_script(
        """
        const stamp = document.getElementById('plate-sold-stamp');
        const cs = stamp ? getComputedStyle(stamp) : null;
        return {
          imprint: !!(stamp && stamp.classList.contains('imprint')),
          opacity: cs ? parseFloat(cs.opacity) : 0,
          hidden: stamp ? stamp.hidden : null,
          soldPlaying: !!(window.H2V4SoldFx && H2V4SoldFx.isPlaying()),
          stageSold: document.getElementById('stage')?.classList.contains('sold-celebration'),
        };
        """
    )


def sold_clear(s: dict | None) -> bool:
    if not s:
        return False
    return (
        not s.get("imprint")
        and float(s.get("opacity") or 0) < 0.2
        and not s.get("soldPlaying")
        and not s.get("stageSold")
    )


def sold_active(s: dict | None) -> bool:
    if not s:
        return False
    return bool(s.get("imprint")) and float(s.get("opacity") or 0) > 0.35


def apply_lot(ctrl, disp, number: str, code: str = "AA", ptype: str = "dubai") -> dict | None:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(ptype)
    ctrl.find_element(By.ID, "code").clear()
    ctrl.find_element(By.ID, "code").send_keys(code)
    ctrl.find_element(By.ID, "number").clear()
    ctrl.find_element(By.ID, "number").send_keys(number)
    ctrl.find_element(By.ID, "btn-apply-lot").click()
    return wait_digits_visible(disp, number, timeout=10.0)


def login_control(ctrl) -> None:
    ctrl.get(f"{BASE}/admin/login/?next=/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "input[type=submit],button[type=submit]").click()
    WebDriverWait(ctrl, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!document.getElementById('btn-apply-lot')")
    )
    time.sleep(0.4)


def wait_display_ready(disp) -> None:
    WebDriverWait(disp, 25).until(
        lambda x: x.execute_script(
            "return !!window.H2V4DjangoBridge && !!window.H2V4State && !!window.H2V4BeamDropFx"
        )
    )
    time.sleep(0.6)


def test_a_number_drop(ctrl, disp) -> None:
    apply_lot(ctrl, disp, "7777")
    ctrl.find_element(By.ID, "btn-drop").click()
    time.sleep(3.2)
    hidden = probe_number(disp)
    ok_hidden = digits_hidden(hidden)
    if ok_hidden:
        shot_cdp(disp, os.path.join(OUT, "drop_hidden.png"))

    disp.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
    wait_display_ready(disp)
    time.sleep(0.8)
    after_refresh = probe_number(disp)
    ok_persist = digits_hidden(after_refresh)

    ctrl.find_element(By.ID, "btn-show").click()
    shown = wait_digits_visible(disp, "7777")
    record(
        "A",
        ok_hidden and ok_persist and digits_visible(shown, "7777"),
        {"after_drop": hidden, "after_refresh": after_refresh, "after_show": shown},
    )


def test_b_cancel_sold(ctrl, disp) -> None:
    apply_lot(ctrl, disp, "7777")
    ctrl.find_element(By.ID, "btn-sold").click()
    sold = None
    t0 = time.time()
    while time.time() - t0 < 6:
        sold = probe_sold(disp)
        if sold_active(sold):
            break
        time.sleep(0.1)
    ok_sold = sold_active(sold)
    if ok_sold:
        shot_cdp(disp, os.path.join(OUT, "cancel_sold_before.png"))

    ctrl.find_element(By.ID, "btn-cancel-sold").click()
    cleared = None
    t0 = time.time()
    while time.time() - t0 < 5:
        cleared = probe_sold(disp)
        if sold_clear(cleared):
            break
        time.sleep(0.12)
    ok_clear = sold_clear(cleared)

    disp.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
    wait_display_ready(disp)
    time.sleep(0.8)
    after = probe_sold(disp)
    ok_after = sold_clear(after)

    ctrl.find_element(By.ID, "btn-sold").click()
    again = None
    t0 = time.time()
    while time.time() - t0 < 6:
        again = probe_sold(disp)
        if sold_active(again):
            break
        time.sleep(0.1)
    ok_again = sold_active(again)
    if ok_clear:
        shot_cdp(disp, os.path.join(OUT, "cancel_sold.png"))

    record(
        "B",
        ok_sold and ok_clear and ok_after and ok_again,
        {"sold": sold, "cleared": cleared, "after_refresh": after, "sold_again": again},
    )


def test_c_hide_new(ctrl, disp) -> None:
    apply_lot(ctrl, disp, "7777")
    ctrl.find_element(By.ID, "btn-hide").click()
    wait_digits_hidden(disp)
    apply_lot(ctrl, disp, "8888")
    vis = wait_digits_visible(disp, "8888")
    record("C", digits_visible(vis, "8888"), vis)


def test_d_red_new(ctrl, disp) -> None:
    apply_lot(ctrl, disp, "7777")
    ctrl.execute_script("document.getElementById('btn-red').click();")
    red = None
    t0 = time.time()
    while time.time() - t0 < 12:
        red = disp.execute_script(
            """
            const plate = document.getElementById('plate');
            const st = H2V4State.getState();
            const num = document.getElementById('plate-number');
            return {
              red: plate?.classList.contains('red-illuminate'),
              number_visible: st.new_style?.number_visible !== false,
              digitVis: num ? num.style.visibility : null,
            };
            """
        )
        if red and red.get("red") and not red.get("number_visible"):
            break
        time.sleep(0.12)
    time.sleep(0.5)
    apply_lot(ctrl, disp, "8888")
    vis = wait_digits_visible(disp, "8888", timeout=10.0)
    record("D", digits_visible(vis, "8888"), {"red": red, "after_apply": vis})


def test_e_drop_new(ctrl, disp) -> None:
    apply_lot(ctrl, disp, "7777")
    ctrl.find_element(By.ID, "btn-drop").click()
    wait_digits_hidden(disp, timeout=12.0)
    t0 = time.time()
    apply_lot(ctrl, disp, "8888")
    vis = wait_digits_visible(disp, "8888", timeout=6.0)
    fast = (time.time() - t0) < 5.0
    record("E", digits_visible(vis, "8888"), {"immediate": fast, "probe": vis})


def test_f_race(ctrl, disp) -> None:
    apply_lot(ctrl, disp, "7777")
    ctrl.find_element(By.ID, "btn-drop").click()
    # fast lot change within drop window (~400ms)
    time.sleep(0.15)
    ctrl.execute_script(
        """
        const n = document.getElementById('number');
        n.value = '9999';
        n.dispatchEvent(new Event('input', {bubbles: true}));
        document.getElementById('btn-apply-lot').click();
        """
    )
    time.sleep(3.5)
    vis = probe_number(disp)
    ok = digits_visible(vis, "9999")
    record("F", ok, vis)


def test_g_smoke(ctrl, disp) -> None:
    dark = bool(ctrl.find_elements(By.ID, "btn-studio-dark"))
    light = bool(ctrl.find_elements(By.ID, "btn-studio-light"))
    apply_lot(ctrl, disp, "7011")
    ctrl.find_element(By.ID, "btn-yellow").click()
    y = None
    t0 = time.time()
    while time.time() - t0 < 8:
        y = disp.execute_script(
            "return document.getElementById('plate')?.classList.contains('yellow-illuminate');"
        )
        if y:
            break
        time.sleep(0.15)
    record("G", dark and light and y is True, {"studio_buttons": [dark, light], "yellow": y})


def main() -> int:
    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        record("setup", False, "no LiveBroadcastSession")
        return 1

    ns = normalize_new_style(session.new_style if isinstance(session.new_style, dict) else {})
    ns["number_visible"] = True
    ns.setdefault("studio_theme", "dark")
    session.new_style = ns
    session.save(update_fields=["new_style"])
    token = str(session.display_token)
    bust = f"?v={CACHE}&_={int(time.time())}"

    ctrl = chrome()
    disp = chrome()
    try:
        disp_url = f"{BASE}/live/display-v4/{token}/{bust}"
        ctrl_url = f"{BASE}/live/control/v4/{bust}"

        hard_refresh(disp, disp_url)
        wait_display_ready(disp)

        login_control(ctrl)
        hard_refresh(ctrl, ctrl_url)
        WebDriverWait(ctrl, 25).until(
            lambda x: x.execute_script("return !!window.H2V4DjangoBridge")
        )
        hard_refresh(disp, disp_url)
        wait_display_ready(disp)

        test_a_number_drop(ctrl, disp)
        test_b_cancel_sold(ctrl, disp)
        test_c_hide_new(ctrl, disp)
        test_d_red_new(ctrl, disp)
        test_e_drop_new(ctrl, disp)
        test_f_race(ctrl, disp)
        test_g_smoke(ctrl, disp)

        letters = {k: v for k, v in LETTER_RESULTS.items() if len(k) == 1}

        report = {
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cache_bust": CACHE,
            "display_url": f"{BASE}/live/display-v4/{token}/",
            "control_url": f"{BASE}/live/control/v4/",
            "unit_tests_note": "plates fix_drop_sold (4 tests)",
            "screenshots": {
                "drop_hidden": os.path.join(OUT, "drop_hidden.png"),
                "cancel_sold": os.path.join(OUT, "cancel_sold.png"),
            },
            "tests": letters,
            "ok": all(v.get("ok") for v in letters.values()),
        }
        report_path = os.path.join(OUT, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("REPORT", report_path)
        return 0 if report["ok"] else 1
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
