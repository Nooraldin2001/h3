"""E2E QA — UNSOLD cancel buttons (v=20261112unsold1)."""
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
CACHE = "20261112unsold1"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\unsold"
os.makedirs(OUT, exist_ok=True)

STEP_RESULTS: dict[str, dict] = {}


def record(step: str, ok: bool, detail: object = "") -> None:
    STEP_RESULTS[step] = {"ok": bool(ok), "detail": detail}
    print(("PASS" if ok else "FAIL"), step, detail if detail != "" else "")


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


def probe_sold(disp) -> dict:
    return disp.execute_script(
        """
        const stamp = document.getElementById('plate-sold-stamp');
        const cs = stamp ? getComputedStyle(stamp) : null;
        const st = window.H2V4State ? H2V4State.getState() : {};
        const fw = document.querySelector('.sold-fireworks, #sold-fireworks, .fx-fireworks');
        const fwVis = fw ? getComputedStyle(fw) : null;
        return {
          imprint: !!(stamp && stamp.classList.contains('imprint')),
          opacity: cs ? parseFloat(cs.opacity) : 0,
          hidden: stamp ? stamp.hidden : null,
          soldPlaying: !!(window.H2V4SoldFx && H2V4SoldFx.isPlaying()),
          stageSold: document.getElementById('stage')?.classList.contains('sold-celebration'),
          sold_imprint_active: !!(st.new_style && st.new_style.sold_imprint_active),
          fireworksVisible: !!(fw && fwVis && parseFloat(fwVis.opacity || '0') > 0.1),
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
        and s.get("sold_imprint_active") is False
        and not s.get("fireworksVisible")
    )


def sold_active(s: dict | None) -> bool:
    if not s:
        return False
    return bool(s.get("imprint")) and float(s.get("opacity") or 0) > 0.35 and s.get("sold_imprint_active") is True


def wait_sold_active(disp, timeout: float = 8.0) -> dict | None:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        last = probe_sold(disp)
        if sold_active(last):
            return last
        time.sleep(0.1)
    return last


def wait_sold_clear(disp, timeout: float = 6.0) -> dict | None:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        last = probe_sold(disp)
        if sold_clear(last):
            return last
        time.sleep(0.12)
    return last


def apply_lot(ctrl, disp, number: str, code: str = "AA", ptype: str = "dubai") -> None:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(ptype)
    ctrl.find_element(By.ID, "code").clear()
    ctrl.find_element(By.ID, "code").send_keys(code)
    ctrl.find_element(By.ID, "number").clear()
    ctrl.find_element(By.ID, "number").send_keys(number)
    ctrl.find_element(By.ID, "btn-apply-lot").click()
    WebDriverWait(disp, 12).until(
        lambda x: number in (x.execute_script(
            "const n=document.getElementById('plate-number'); return n?(n.textContent||'').trim():'';"
        ) or "")
    )


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
            "return !!window.H2V4DjangoBridge && !!window.H2V4State && !!window.H2V4SoldFx"
        )
    )
    time.sleep(0.6)


def check_unsold_buttons(ctrl) -> dict:
    return ctrl.execute_script(
        """
        const b1 = document.getElementById('btn-cancel-sold');
        const b2 = document.getElementById('btn-cancel-sold-char');
        const label = (el) => el ? (el.textContent || '').trim() : '';
        return {
          btn_cancel_sold: !!b1,
          btn_cancel_sold_char: !!b2,
          label_cancel_sold: label(b1),
          label_cancel_sold_char: label(b2),
          cache_scripts: Array.from(document.scripts).filter(s => s.src && s.src.includes('20261112unsold1')).length,
        };
        """
    )


def run_e2e(ctrl, disp) -> None:
    apply_lot(ctrl, disp, "7777")

    ctrl.find_element(By.ID, "btn-sold").click()
    sold = wait_sold_active(disp, 10.0)
    ok_a = sold_active(sold)
    if ok_a:
        shot_cdp(disp, os.path.join(OUT, "sold_on.png"))
    record("a_sold_imprint", ok_a, sold)

    ctrl.find_element(By.ID, "btn-cancel-sold").click()
    cleared = wait_sold_clear(disp, 8.0)
    ok_b = sold_clear(cleared)
    if ok_b:
        shot_cdp(disp, os.path.join(OUT, "unsold_cleared.png"))
    record("b_cancel_sold", ok_b, cleared)

    disp.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
    wait_display_ready(disp)
    time.sleep(0.8)
    after = probe_sold(disp)
    ok_c = sold_clear(after)
    if ok_c:
        shot_cdp(disp, os.path.join(OUT, "unsold_after_refresh.png"))
    record("c_persist_after_refresh", ok_c, after)

    ctrl.find_element(By.ID, "btn-sold").click()
    again = wait_sold_active(disp, 10.0)
    ok_d = sold_active(again)
    record("d_sold_again", ok_d, again)

    ctrl.find_element(By.ID, "btn-cancel-sold-char").click()
    char_cleared = wait_sold_clear(disp, 8.0)
    ok_e = sold_clear(char_cleared)
    record("e_cancel_sold_char", ok_e, char_cleared)


def main() -> int:
    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        record("setup", False, "no LiveBroadcastSession")
        return 1

    ns = normalize_new_style(session.new_style if isinstance(session.new_style, dict) else {})
    ns["number_visible"] = True
    ns["sold_imprint_active"] = False
    ns.setdefault("studio_theme", "dark")
    session.new_style = ns
    session.save(update_fields=["new_style"])
    token = str(session.display_token)
    bust = f"?v={CACHE}&_={int(time.time())}"

    ctrl = chrome()
    disp = chrome()
    unit_exit = None
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

        buttons = check_unsold_buttons(ctrl)
        labels_ok = (
            buttons.get("label_cancel_sold") == "إلغاء البيع (UNSOLD)"
            and buttons.get("label_cancel_sold_char") == "إلغاء البيع (UNSOLD)"
        )
        record(
            "buttons_present",
            buttons.get("btn_cancel_sold")
            and buttons.get("btn_cancel_sold_char")
            and labels_ok,
            buttons,
        )

        hard_refresh(disp, disp_url)
        wait_display_ready(disp)

        run_e2e(ctrl, disp)

        e2e_keys = ["buttons_present", "a_sold_imprint", "b_cancel_sold", "c_persist_after_refresh", "d_sold_again", "e_cancel_sold_char"]
        report = {
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cache_bust": CACHE,
            "display_url": f"{BASE}/live/display-v4/{token}/?v={CACHE}",
            "control_url": f"{BASE}/live/control/v4/?v={CACHE}",
            "unit_tests_exit_code": unit_exit,
            "credentials": "admin / TempTest123!",
            "screenshots": {
                "sold_on": os.path.join(OUT, "sold_on.png"),
                "unsold_cleared": os.path.join(OUT, "unsold_cleared.png"),
                "unsold_after_refresh": os.path.join(OUT, "unsold_after_refresh.png"),
            },
            "steps": {k: STEP_RESULTS.get(k, {"ok": False, "detail": "missing"}) for k in e2e_keys},
            "ok": all(STEP_RESULTS.get(k, {}).get("ok") for k in e2e_keys),
        }
        report_path = os.path.join(OUT, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("REPORT", report_path, "OK" if report["ok"] else "FAIL")
        return 0 if report["ok"] else 1
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
