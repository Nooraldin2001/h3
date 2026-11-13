"""E2E QA — V4 studio theme dark/light persistence (control + display)."""
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
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

BASE = "http://127.0.0.1:8000"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\studio_theme"
os.makedirs(OUT, exist_ok=True)
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL"), name, detail if detail else "")


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


def probe_display(driver) -> dict:
    return driver.execute_script(
        """
      const stage = document.getElementById('stage');
      const img = document.getElementById('studio-bg-img');
      const st = window.H2V4State?.getState?.() || {};
      const src = img ? (img.currentSrc || img.src || '') : '';
      return {
        studio_theme_state: st.new_style?.studio_theme,
        stage_theme: stage ? stage.dataset.studioTheme : null,
        studio_src: src,
        is_light_asset: /Light_Studio\\.svg/i.test(src),
        is_dark_asset: /Studio_4K_Vector\\.svg/i.test(src),
      };
    """
    )


def wait_theme(driver, theme: str, timeout: float = 8.0) -> dict | None:
    want = "light" if theme == "light" else "dark"
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        last = probe_display(driver)
        if last and last.get("studio_theme_state") == want and last.get("stage_theme") == want:
            asset_ok = last.get("is_light_asset") if want == "light" else last.get("is_dark_asset")
            if asset_ok:
                return last
        time.sleep(0.2)
    return last


def login_control(ctrl) -> None:
    ctrl.get(f"{BASE}/admin/login/?next=/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "input[type=submit],button[type=submit]").click()
    WebDriverWait(ctrl, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!document.getElementById('btn-studio-dark')")
    )
    time.sleep(0.4)


def patch_studio_theme(theme: str) -> None:
    s = LiveBroadcastSession.objects.order_by("pk").first()
    if not s:
        raise RuntimeError("No LiveBroadcastSession in DB")
    ns = normalize_new_style(s.new_style if isinstance(s.new_style, dict) else {})
    ns["studio_theme"] = "light" if theme == "light" else "dark"
    s.new_style = ns
    s.save(update_fields=["new_style"])


def main() -> int:
    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        check("session_exists", False, "no LiveBroadcastSession")
        return 1
    token = str(session.display_token)

    patch_studio_theme("dark")

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--hide-scrollbars")

    ctrl = webdriver.Chrome(options=opts)
    disp = webdriver.Chrome(options=opts)

    try:
        disp.get(f"{BASE}/live/display-v4/{token}/?_={int(time.time())}")
        WebDriverWait(disp, 25).until(
            lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4State")
        )
        time.sleep(1.0)

        login_control(ctrl)
        ctrl.get(f"{BASE}/live/control/v4/")

        dark = wait_theme(disp, "dark")
        check("dark_mode_applied", dark and dark.get("stage_theme") == "dark", json.dumps(dark))
        dark_path = shot_cdp(disp, os.path.join(OUT, "dark_mode.png"))
        check("dark_screenshot", os.path.isfile(dark_path), dark_path)

        ctrl.find_element(By.ID, "btn-studio-light").click()
        light = wait_theme(disp, "light")
        check("light_mode_via_admin", light and light.get("stage_theme") == "light", json.dumps(light))
        light_path = shot_cdp(disp, os.path.join(OUT, "light_mode.png"))
        check("light_screenshot", os.path.isfile(light_path), light_path)

        disp.refresh()
        WebDriverWait(disp, 25).until(
            lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4State")
        )
        time.sleep(1.0)
        after_refresh = wait_theme(disp, "light")
        check("light_persists_after_refresh", after_refresh and after_refresh.get("stage_theme") == "light", json.dumps(after_refresh))

        ctrl.find_element(By.ID, "btn-studio-dark").click()
        back_dark = wait_theme(disp, "dark")
        check("restore_dark_mode", back_dark and back_dark.get("stage_theme") == "dark", json.dumps(back_dark))

        report = {
            "display_url": f"{BASE}/live/display-v4/{token}/",
            "control_url": f"{BASE}/live/control/v4/",
            "screenshots": {
                "dark_mode": dark_path,
                "light_mode": light_path,
            },
            "results": [{"name": n, "ok": ok, "detail": d} for n, ok, d in RESULTS],
        }
        report_path = os.path.join(OUT, "studio_theme_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("REPORT", report_path)

        failed = [n for n, ok, _ in RESULTS if not ok]
        return 1 if failed else 0
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
