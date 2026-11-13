"""E2E QA — plate typography (Oswald, shell bounds) v=20261112type2."""
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
CACHE = "20261112type2"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\plate_typography"
os.makedirs(OUT, exist_ok=True)

CASES = [
    {
        "id": "dubai_A_7777",
        "shot": "dubai_A_7777.png",
        "ptype": "dubai",
        "code": "A",
        "number": "7777",
        "mode": "plate",
    },
    {
        "id": "dubai_B_1234",
        "shot": "dubai_B_1234.png",
        "ptype": "dubai",
        "code": "B",
        "number": "1234",
        "mode": "plate",
    },
    {
        "id": "dubai_C_9",
        "shot": "dubai_C_9.png",
        "ptype": "dubai",
        "code": "C",
        "number": "9",
        "mode": "plate",
    },
    {
        "id": "abudhabi_1_88888",
        "shot": "abudhabi_1_88888.png",
        "ptype": "abudhabi",
        "code": "1",
        "number": "88888",
        "mode": "plate",
    },
    {
        "id": "du_phone",
        "shot": "du_phone.png",
        "ptype": "du",
        "phone": "0501234567",
        "mode": "phone",
    },
]

def typography_js(cache: str) -> str:
    return f"""
const shell = document.getElementById('plate-shell');
const mode = arguments[0];
const ids = mode === 'phone' ? ['plate-phone'] : ['plate-code', 'plate-number'];
const shellR = shell ? shell.getBoundingClientRect() : null;
const bust = {json.dumps(cache)};
const assets = {{
  css: !!Array.from(document.querySelectorAll('link[rel=stylesheet]'))
      .some(l => (l.href || '').includes('plate-system.css') && (l.href || '').includes(bust)),
  cssLink: (() => {{
    const el = Array.from(document.querySelectorAll('link[rel=stylesheet]'))
      .find(l => (l.href || '').includes('plate-system.css'));
    return el ? el.href : null;
  }})(),
  js: Array.from(document.scripts).filter(s => s.src && s.src.includes('plate-system.js') && s.src.includes(bust)).length,
}};
const overlays = ids.map((id) => {{
  const el = document.getElementById(id);
  if (!el) return {{ id, missing: true }};
  const cs = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  const hidden = el.hidden || cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity || '1') < 0.05;
  const ff = (cs.fontFamily || '').toLowerCase();
  let overflow = null;
  if (shellR) {{
    overflow = {{
      left: shellR.left - r.left,
      top: shellR.top - r.top,
      right: r.right - shellR.right,
      bottom: r.bottom - shellR.bottom,
    }};
  }}
  const tol = 2;
  const inShell = shellR && overflow
    ? overflow.left <= tol && overflow.top <= tol && overflow.right <= tol && overflow.bottom <= tol
    : false;
  return {{
    id,
    text: (el.textContent || '').trim(),
    fontFamily: cs.fontFamily,
    oswald: ff.includes('oswald'),
    fontSizePx: parseFloat(cs.fontSize) || 0,
    fontWeight: cs.fontWeight,
    visible: !hidden && r.width > 0 && r.height > 0,
    rect: {{ w: r.width, h: r.height, left: r.left, top: r.top }},
    overflow,
    inShell,
  }};
}});
return {{ mode, assets, overlays, shellClass: shell ? shell.className : null }};
"""


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
            "return !!window.H2V4DjangoBridge && !!window.H2V4State && !!window.H2PlateSystem"
        )
    )
    time.sleep(0.6)


def apply_lot(ctrl, disp, case: dict) -> None:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(case["ptype"])
    if case["mode"] == "phone":
        phone_el = ctrl.find_element(By.ID, "phone")
        phone_el.clear()
        phone_el.send_keys(case["phone"])
        ctrl.find_element(By.ID, "code").clear()
        ctrl.find_element(By.ID, "number").clear()
        expected = case["phone"]
        ctrl.find_element(By.ID, "btn-apply-lot").click()
        WebDriverWait(disp, 12).until(
            lambda x: expected in (x.execute_script(
                "const p=document.getElementById('plate-phone'); return p&&!p.hidden?(p.textContent||'').trim():'';"
            ) or "")
        )
    else:
        ctrl.find_element(By.ID, "code").clear()
        ctrl.find_element(By.ID, "code").send_keys(case["code"])
        ctrl.find_element(By.ID, "number").clear()
        ctrl.find_element(By.ID, "number").send_keys(case["number"])
        code = case["code"]
        number = case["number"]
        ctrl.find_element(By.ID, "btn-apply-lot").click()
        WebDriverWait(disp, 12).until(
            lambda x, c=code, n=number: (
                (x.execute_script(
                    "const el=document.getElementById('plate-code'); return el?(el.textContent||'').trim():'';"
                ) or "").upper() == c.upper()
                and (x.execute_script(
                    "const el=document.getElementById('plate-number'); return el?(el.textContent||'').trim():'';"
                ) or "") == n
            )
        )
    time.sleep(0.5)


def assert_case(metrics: dict) -> tuple[bool, str]:
    assets = metrics.get("assets") or {}
    if assets.get("js", 0) < 1:
        return False, "plate-system.js cache bust missing"
    overlays = metrics.get("overlays") or []
    if not overlays:
        return False, "no overlays probed"
    for ov in overlays:
        if ov.get("missing"):
            return False, f"missing {ov.get('id')}"
        if not ov.get("oswald"):
            return False, f"{ov['id']} font missing Oswald: {ov.get('fontFamily')}"
        if not ov.get("visible"):
            return False, f"{ov['id']} not visible"
        if not ov.get("inShell"):
            return False, f"{ov['id']} overflow outside shell: {ov.get('overflow')}"
    return True, "ok"


def main() -> int:
    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        report = {"ok": False, "error": "no LiveBroadcastSession"}
        with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
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
    case_results: dict[str, dict] = {}

    try:
        disp_url = f"{BASE}/live/display-v4/{token}/{bust}"
        ctrl_url = f"{BASE}/live/control/v4/{bust}"

        hard_refresh(disp, disp_url)
        wait_display_ready(disp)
        login_control(ctrl)
        hard_refresh(ctrl, ctrl_url)
        WebDriverWait(ctrl, 25).until(lambda x: x.execute_script("return !!window.H2V4DjangoBridge"))
        hard_refresh(disp, disp_url)
        wait_display_ready(disp)

        for case in CASES:
            print("CASE", case["id"])
            apply_lot(ctrl, disp, case)
            metrics = disp.execute_script(typography_js(CACHE), case["mode"])
            ok, detail = assert_case(metrics)
            shot_path = os.path.join(OUT, case["shot"])
            shot_cdp(disp, shot_path)
            case_results[case["id"]] = {
                "ok": ok,
                "detail": detail,
                "screenshot": shot_path,
                "metrics": metrics,
            }
            print(("PASS" if ok else "FAIL"), case["id"], detail)

        all_ok = all(r["ok"] for r in case_results.values())
        report = {
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cache_bust": CACHE,
            "display_url": f"{BASE}/live/display-v4/{token}/?v={CACHE}",
            "control_url": f"{BASE}/live/control/v4/?v={CACHE}",
            "credentials": "admin / TempTest123!",
            "cases": case_results,
            "ok": all_ok,
            "typography_notes": {
                "font_stack_expects_oswald": True,
                "sample_font_sizes_px": {
                    k: {
                        ov["id"]: ov.get("fontSizePx")
                        for ov in (v.get("metrics", {}).get("overlays") or [])
                    }
                    for k, v in case_results.items()
                },
            },
        }
        report_path = os.path.join(OUT, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("REPORT", report_path, "OK" if all_ok else "FAIL")
        return 0 if all_ok else 1
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
