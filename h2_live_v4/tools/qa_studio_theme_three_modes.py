"""E2E QA — V4 studio theme dark / light / new (cache v=20261112studio3)."""
from __future__ import annotations

import base64
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
CACHE = "20261112studio3"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio_theme_three"
os.makedirs(OUT, exist_ok=True)

SVG_DUBAI = f"{BASE}/static/live_v4/assets/studio/H2_AUCTIONS_Dubai_Studio_4K.svg"

THEME_ASSET = {
    "dark": "Studio_4K_Vector",
    "light": "Light_Studio",
    "new": "Dubai_Studio_4K",
}

RESULTS: list[dict] = []


def record(name: str, ok: bool, detail: object = "") -> None:
    row = {"name": name, "ok": bool(ok), "detail": detail}
    RESULTS.append(row)
    print(("PASS" if ok else "FAIL"), name, detail if detail != "" else "")


def http_status(url: str) -> int | None:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return None


def shot_cdp(driver, path: str, w: int = 1920, h: int = 1080) -> str:
    driver.set_window_size(w, h)
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    time.sleep(0.35)
    data = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
        },
    )
    raw = base64.b64decode(data["data"])
    with open(path, "wb") as f:
        f.write(raw)
    return path


def hard_refresh_display(driver, url: str) -> None:
    driver.get(url)
    WebDriverWait(driver, 25).until(lambda x: x.execute_script("return document.readyState") == "complete")
    driver.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
    WebDriverWait(driver, 25).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4State")
    )
    time.sleep(0.6)


def hard_refresh_control(driver, url: str) -> None:
    driver.get(url)
    WebDriverWait(driver, 25).until(lambda x: x.execute_script("return document.readyState") == "complete")
    driver.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
    WebDriverWait(driver, 25).until(
        lambda x: x.execute_script(
            "return !!window.H2V4DjangoBridge && !!document.getElementById('btn-studio-dark')"
        )
    )
    time.sleep(0.6)


def cache_bust_url(path: str) -> str:
    sep = "&" if "?" in path else "?"
    return f"{BASE}{path}{sep}v={CACHE}&_={int(time.time())}"


def probe_display(driver) -> dict:
    return driver.execute_script(
        """
      const stage = document.getElementById('stage');
      const img = document.getElementById('studio-bg-img');
      const plate = document.getElementById('plate');
      const st = window.H2V4State?.getState?.() || {};
      const src = img ? (img.currentSrc || img.src || '') : '';
      return {
        studio_theme_state: st.new_style?.studio_theme,
        stage_theme: stage ? stage.dataset.studioTheme : null,
        studio_src: src,
        plate_visible: plate ? !plate.hidden && plate.style.display !== 'none' : false,
        plate_type: st.plate_type,
        code: st.code,
        number: st.number,
      };
    """
    )


def wait_theme(driver, theme: str, timeout: float = 12.0) -> dict | None:
    want_asset = THEME_ASSET[theme]
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        last = probe_display(driver)
        if not last:
            time.sleep(0.2)
            continue
        state_ok = last.get("studio_theme_state") == theme and last.get("stage_theme") == theme
        src = str(last.get("studio_src") or "")
        asset_ok = want_asset in src
        if state_ok and asset_ok:
            return last
        time.sleep(0.2)
    return last


def click_theme(ctrl, btn_id: str) -> None:
    ctrl.execute_script(
        "const el=document.getElementById(arguments[0]); el.scrollIntoView({block:'center'}); el.click();",
        btn_id,
    )


def login_admin(ctrl) -> None:
    ctrl.get(cache_bust_url("/admin/login/?next=/live/control/v4/"))
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "input[type=submit],button[type=submit]").click()
    WebDriverWait(ctrl, 25).until(
        lambda x: x.execute_script(
            "return !!window.H2V4DjangoBridge && !!document.getElementById('btn-studio-dark')"
        )
    )
    time.sleep(0.4)


def confirm_studio_buttons(ctrl) -> None:
    mapping = {
        "btn-studio-dark": "الوضع الداكن",
        "btn-studio-light": "الوضع الفاتح",
        "btn-studio-new": "الوضع الجديد",
    }
    found = {}
    for bid, label in mapping.items():
        el = ctrl.find_elements(By.ID, bid)
        ok = bool(el)
        text = el[0].text if el else ""
        ok = ok and label in text
        found[bid] = {"present": bool(el), "text": text, "label_ok": label in text}
        record(f"button_{bid}", ok, found[bid])
    record("studio_buttons_three_modes", all(v["label_ok"] for v in found.values()), found)


def apply_lot_smoke(ctrl, disp) -> bool:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value("dubai")
    ctrl.find_element(By.ID, "code").clear()
    ctrl.find_element(By.ID, "code").send_keys("AA")
    ctrl.find_element(By.ID, "number").clear()
    ctrl.find_element(By.ID, "number").send_keys("7777")
    ctrl.find_element(By.ID, "btn-apply-lot").click()
    ctrl.execute_script(
        """
      return window.H2V4DjangoBridge?.patch?.({
        plate_type: 'dubai', code: 'AA', number: '7777', ns_show_number: true
      });
    """
    )
    ctrl.find_element(By.ID, "btn-show").click()
    t0 = time.time()
    last = None
    while time.time() - t0 < 8:
        last = probe_display(disp)
        theme = last and last.get("studio_theme_state") == "new"
        plate_ok = (
            last
            and last.get("plate_type") == "dubai"
            and last.get("code") == "AA"
            and str(last.get("number")) == "7777"
            and last.get("plate_visible")
        )
        if theme and plate_ok:
            record("lot_aa_7777_plate_visible", True, last)
            return True
        time.sleep(0.2)
    record("lot_aa_7777_plate_visible", False, last)
    return False


def write_report(token: str, screenshots: dict, mapping: dict) -> str:
    report_path = os.path.join(OUT, "report.json")
    payload = {
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ok": all(r["ok"] for r in RESULTS),
        "cache_bust": CACHE,
        "theme_asset_mapping": mapping,
        "urls": {
            "display": f"{BASE}/live/display-v4/{token}/",
            "control": cache_bust_url("/live/control/v4/"),
            "dubai_svg": SVG_DUBAI,
            "dubai_svg_status": http_status(SVG_DUBAI),
        },
        "screenshots": screenshots,
        "results": RESULTS,
        "failed": [r["name"] for r in RESULTS if not r["ok"]],
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("REPORT", report_path)
    return report_path


def main() -> int:
    mapping = {
        "dark": {"theme": "dark", "src_contains": THEME_ASSET["dark"], "button": "btn-studio-dark"},
        "light": {"theme": "light", "src_contains": THEME_ASSET["light"], "button": "btn-studio-light"},
        "new": {"theme": "new", "src_contains": THEME_ASSET["new"], "button": "btn-studio-new"},
    }
    record("mapping_confirmation", True, mapping)

    dubai_st = http_status(SVG_DUBAI)
    record("dubai_svg_static_200", dubai_st == 200, {"url": SVG_DUBAI, "status": dubai_st})

    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        record("session_exists", False, "no LiveBroadcastSession")
        write_report("", {}, mapping)
        return 1

    ns = normalize_new_style(session.new_style if isinstance(session.new_style, dict) else {})
    ns["studio_theme"] = "dark"
    ns["number_visible"] = True
    session.new_style = ns
    session.save(update_fields=["new_style"])

    token = str(session.display_token)
    display_url = cache_bust_url(f"/live/display-v4/{token}/")
    control_url = cache_bust_url("/live/control/v4/")

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--hide-scrollbars")

    ctrl = webdriver.Chrome(options=opts)
    disp = webdriver.Chrome(options=opts)
    screenshots: dict[str, str] = {}

    try:
        hard_refresh_display(disp, display_url)
        login_admin(ctrl)
        hard_refresh_control(ctrl, control_url)
        hard_refresh_display(disp, display_url)

        confirm_studio_buttons(ctrl)

        click_theme(ctrl, "btn-studio-dark")
        dark = wait_theme(disp, "dark")
        record("dark_mode_studio_src", bool(dark and THEME_ASSET["dark"] in str(dark.get("studio_src"))), dark)
        screenshots["dark_mode"] = shot_cdp(disp, os.path.join(OUT, "dark_mode.png"))
        record("dark_screenshot", os.path.isfile(screenshots["dark_mode"]), screenshots["dark_mode"])

        click_theme(ctrl, "btn-studio-light")
        light = wait_theme(disp, "light")
        record("light_mode_studio_src", bool(light and THEME_ASSET["light"] in str(light.get("studio_src"))), light)
        screenshots["light_mode"] = shot_cdp(disp, os.path.join(OUT, "light_mode.png"))
        record("light_screenshot", os.path.isfile(screenshots["light_mode"]), screenshots["light_mode"])

        click_theme(ctrl, "btn-studio-new")
        new_mode = wait_theme(disp, "new")
        record("new_mode_studio_src", bool(new_mode and THEME_ASSET["new"] in str(new_mode.get("studio_src"))), new_mode)
        screenshots["new_mode"] = shot_cdp(disp, os.path.join(OUT, "new_mode.png"))
        record("new_screenshot", os.path.isfile(screenshots["new_mode"]), screenshots["new_mode"])

        apply_lot_smoke(ctrl, disp)

        disp.refresh()
        WebDriverWait(disp, 25).until(
            lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4State")
        )
        time.sleep(1.0)
        after_refresh = wait_theme(disp, "new")
        record(
            "new_persists_after_display_refresh",
            bool(after_refresh and after_refresh.get("stage_theme") == "new"),
            after_refresh,
        )

        click_theme(ctrl, "btn-studio-dark")
        back_dark = wait_theme(disp, "dark")
        record(
            "restore_dark_after_new",
            bool(back_dark and THEME_ASSET["dark"] in str(back_dark.get("studio_src"))),
            back_dark,
        )

        write_report(token, screenshots, mapping)
        failed = [r["name"] for r in RESULTS if not r["ok"]]
        print("SUMMARY", f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed", "failed:", failed)
        return 1 if failed else 0
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
