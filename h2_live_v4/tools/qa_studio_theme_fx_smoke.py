"""Smoke: Admin FX works in dark + light studio themes; studio SVGs HTTP 200."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

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
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio_theme"
REPORT_MAIN = os.path.join(OUT, "studio_theme_report.json")
REPORT_FX = os.path.join(OUT, "fx_smoke.json")
RESULTS: list[dict] = []

SVG_DARK = f"{BASE}/static/live_v4/assets/studio/H2_AUCTIONS_Studio_4K_Vector.svg"
SVG_LIGHT = f"{BASE}/static/live_v4/assets/studio/H2_AUCTIONS_Light_Studio.svg"


def record(name: str, ok: bool, detail: object = "") -> None:
    row = {"name": name, "ok": bool(ok), "detail": detail}
    RESULTS.append(row)
    print(("PASS" if ok else "FAIL"), name, detail if detail != "" else "")


def http_status(url: str) -> int | None:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        record("http_error", False, {"url": url, "error": str(e)})
        return None


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


def set_theme(ctrl, disp, theme: str) -> bool:
    btn = "btn-studio-light" if theme == "light" else "btn-studio-dark"
    ctrl.execute_script(
        "const el=document.getElementById(arguments[0]); el.scrollIntoView({block:'center'}); el.click();",
        btn,
    )
    want = theme
    t0 = time.time()
    while time.time() - t0 < 10:
        info = disp.execute_script(
            """
          const st = H2V4State.getState();
          const stage = document.getElementById('stage');
          return {theme: st.new_style?.studio_theme, stage: stage?.dataset?.studioTheme};
        """
        )
        if info and info.get("theme") == want and info.get("stage") == want:
            return True
        time.sleep(0.2)
    return False


def apply_lot(ctrl, disp, ptype: str, code: str, number: str, prefix: str) -> bool:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(ptype)
    ctrl.find_element(By.ID, "code").clear()
    ctrl.find_element(By.ID, "code").send_keys(code)
    ctrl.find_element(By.ID, "number").clear()
    ctrl.find_element(By.ID, "number").send_keys(number)
    ctrl.find_element(By.ID, "btn-apply-lot").click()
    ctrl.execute_script(
        """
      return window.H2V4DjangoBridge?.patch?.({
        plate_type: arguments[0], code: arguments[1], number: arguments[2],
        ns_show_number: true
      });
    """,
        ptype,
        code,
        number,
    )
    t0 = time.time()
    while time.time() - t0 < 6:
        st = disp.execute_script(
            "const s=H2V4State.getState(); return {t:s.plate_type,c:s.code,n:s.number,vis:s.new_style?.number_visible!==false};"
        )
        if (
            st
            and st.get("t") == ptype
            and st.get("c") == code
            and str(st.get("n")) == number
            and st.get("vis")
        ):
            record(f"{prefix}_apply_lot", True, st)
            return True
        time.sleep(0.2)
    record(f"{prefix}_apply_lot", False, "timeout")
    return False


def run_theme_block(ctrl, disp, theme: str, ptype: str, code: str, number: str) -> None:
    prefix = theme
    ok_theme = set_theme(ctrl, disp, theme)
    record(f"{prefix}_studio_theme", ok_theme, theme)

    if not apply_lot(ctrl, disp, ptype, code, number, prefix):
        return

    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(0.5)

    ctrl.execute_script("document.getElementById('timer-seconds').value='12';")
    ctrl.find_element(By.ID, "btn-timer-duration").click()
    time.sleep(0.3)
    ctrl.find_element(By.ID, "btn-timer-start").click()
    time.sleep(0.6)
    active = disp.execute_script("return H2V4State.getState().timer_active")
    record(f"{prefix}_timer_start", active is True, active)
    ctrl.find_element(By.ID, "btn-timer-pause").click()
    time.sleep(0.4)
    paused = disp.execute_script("return H2V4State.getState().timer_active")
    record(f"{prefix}_timer_pause", paused is False, paused)
    ctrl.find_element(By.ID, "btn-timer-reset").click()
    time.sleep(0.4)

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
    record(f"{prefix}_yellow_card", y is True, y)
    time.sleep(4.5)

    t0 = time.time()
    while time.time() - t0 < 10:
        ch = disp.execute_script("return window.H2V4Character?.getHud?.()?.state")
        if ch in (None, "IDLE", ""):
            break
        time.sleep(0.2)

    ctrl.execute_script("document.getElementById('btn-red').click();")
    r = None
    t0 = time.time()
    while time.time() - t0 < 10:
        r = disp.execute_script(
            """
          const plate=document.getElementById('plate');
          const rim=document.getElementById('plate-rim');
          const num=document.getElementById('plate-number');
          const st=H2V4State.getState();
          return {
            red: plate?.classList.contains('red-illuminate'),
            rimRed: rim?.classList.contains('red'),
            number_visible: st.new_style?.number_visible !== false,
            digitVis: num ? num.style.visibility : null
          };
        """
        )
        if r and r.get("red") and r.get("number_visible") is False:
            break
        time.sleep(0.1)
    record(
        f"{prefix}_red_card",
        r and r.get("red") and r.get("number_visible") is False,
        r,
    )
    time.sleep(3.0)

    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(0.6)
    ctrl.find_element(By.ID, "btn-sold").click()
    sold = None
    t0 = time.time()
    while time.time() - t0 < 6:
        sold = disp.execute_script(
            """
          const stamp=document.getElementById('plate-sold-stamp');
          return {
            imprint: stamp?.classList.contains('imprint'),
            op: stamp ? getComputedStyle(stamp).opacity : null,
            src: stamp?.src||''
          };
        """
        )
        if sold and sold.get("imprint") and float(sold.get("op") or 0) > 0.3:
            break
        time.sleep(0.15)
    record(f"{prefix}_sold", sold and sold.get("imprint"), sold)


def write_reports(ok_all: bool) -> int:
    os.makedirs(OUT, exist_ok=True)
    payload = {
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ok": ok_all,
        "svg_urls": {
            "dark": {"url": SVG_DARK, "status": http_status(SVG_DARK)},
            "light": {"url": SVG_LIGHT, "status": http_status(SVG_LIGHT)},
        },
        "results": RESULTS,
    }
    with open(REPORT_FX, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    main = {}
    if os.path.isfile(REPORT_MAIN):
        with open(REPORT_MAIN, encoding="utf-8") as f:
            main = json.load(f)
    main["fx_smoke"] = {
        "ok": ok_all,
        "report_file": REPORT_FX,
        "passed": sum(1 for r in RESULTS if r["ok"]),
        "total": len(RESULTS),
        "failed": [r["name"] for r in RESULTS if not r["ok"]],
    }
    with open(REPORT_MAIN, "w", encoding="utf-8") as f:
        json.dump(main, f, indent=2, ensure_ascii=False)
    return 0 if ok_all else 1


def main() -> int:
    for label, url in (("dark_svg", SVG_DARK), ("light_svg", SVG_LIGHT)):
        st = http_status(url)
        record(f"static_{label}_200", st == 200, {"status": st, "url": url})

    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        record("session", False, "no session")
        return write_reports(False)

    ns = normalize_new_style(session.new_style if isinstance(session.new_style, dict) else {})
    ns["studio_theme"] = "dark"
    ns["number_visible"] = True
    session.new_style = ns
    session.save(update_fields=["new_style"])

    token = str(session.display_token)
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--force-device-scale-factor=1")

    ctrl = webdriver.Chrome(options=opts)
    disp = webdriver.Chrome(options=opts)
    try:
        disp.get(f"{BASE}/live/display-v4/{token}/?_={int(time.time())}")
        WebDriverWait(disp, 25).until(
            lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4State")
        )
        time.sleep(0.8)
        login_control(ctrl)
        ctrl.get(f"{BASE}/live/control/v4/")

        run_theme_block(ctrl, disp, "dark", "dubai", "AA", "7011")
        run_theme_block(ctrl, disp, "light", "dubai", "BB", "7022")
    finally:
        ctrl.quit()
        disp.quit()

    failed = [r["name"] for r in RESULTS if not r["ok"]]
    ok_all = not failed
    print("SUMMARY", f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed", "failed:", failed)
    return write_reports(ok_all)


if __name__ == "__main__":
    raise SystemExit(main())
