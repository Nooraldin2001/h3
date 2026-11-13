"""E2E QA — custom plate digit 1 glyphs (cache v=20261112one1)."""
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
CACHE = "20261112one1"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\plate_digit_one"
os.makedirs(OUT, exist_ok=True)

NUMBERS = ["1", "11", "1111", "1825", "7101", "1212"]
PTYPE = "dubai"
CODE = "A"


def digit_one_js(cache: str) -> str:
    return f"""
const expectedNumber = arguments[0];
const bust = {json.dumps(cache)};
const shell = document.getElementById('plate-shell');
const number = document.getElementById('plate-number');
const code = document.getElementById('plate-code');
const assets = {{
  css: !!Array.from(document.querySelectorAll('link[rel=stylesheet]'))
      .some(l => (l.href || '').includes('plate-system.css') && (l.href || '').includes(bust)),
  js: Array.from(document.scripts).filter(s => s.src && s.src.includes('plate-system.js') && s.src.includes(bust)).length,
}};
const hasGlyphs = !!(number && number.classList.contains('has-glyphs'));
const ones = number ? number.querySelectorAll('.plate-num-1').length : 0;
const expectedOnes = (String(expectedNumber).match(/1/g) || []).length;
const spans = number ? Array.from(number.querySelectorAll('.plate-num')) : [];
const nonOneSpans = number ? number.querySelectorAll('.plate-num:not(.plate-num-1)').length : 0;
const expectedNonOne = String(expectedNumber).length - expectedOnes;
const spanClassesOk = spans.length === String(expectedNumber).length && spans.every((s) => {{
  const ch = (s.textContent || '').trim();
  if (ch === '1') return s.classList.contains('plate-num-1');
  return s.classList.contains('plate-num') && !s.classList.contains('plate-num-1');
}});
const codeOneSpans = code ? code.querySelectorAll('.plate-num-1').length : 0;
const codeGlyphSpans = code ? code.querySelectorAll('.plate-num').length : 0;
const codePlain = codeOneSpans === 0 && codeGlyphSpans === 0;
const codeText = code ? (code.textContent || '').trim() : '';
const shellR = shell ? shell.getBoundingClientRect() : null;
const numR = number ? number.getBoundingClientRect() : null;
const tol = 2;
let numberInShell = false;
let overflow = null;
if (shellR && numR) {{
  overflow = {{
    left: shellR.left - numR.left,
    top: shellR.top - numR.top,
    right: numR.right - shellR.right,
    bottom: numR.bottom - shellR.bottom,
  }};
  numberInShell = overflow.left <= tol && overflow.top <= tol
      && overflow.right <= tol && overflow.bottom <= tol;
}}
return {{
  assets,
  hasGlyphs,
  ones,
  expectedOnes,
  nonOneSpans,
  expectedNonOne,
  spanClassesOk,
  codePlain,
  codeText,
  codeOneSpans,
  numberInShell,
  overflow,
  numberText: number ? (number.textContent || '').trim() : '',
}};
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


def shot_cdp(driver, path: str) -> None:
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


def apply_lot(ctrl, disp, number: str) -> None:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(PTYPE)
    ctrl.find_element(By.ID, "code").clear()
    ctrl.find_element(By.ID, "code").send_keys(CODE)
    ctrl.find_element(By.ID, "number").clear()
    ctrl.find_element(By.ID, "number").send_keys(number)
    ctrl.find_element(By.ID, "btn-apply-lot").click()
    WebDriverWait(disp, 12).until(
        lambda x, n=number: (
            x.execute_script(
                "const el=document.getElementById('plate-number');"
                "return el ? el.classList.contains('has-glyphs') : false;"
            )
            and (x.execute_script(
                "const el=document.getElementById('plate-number'); return el?(el.textContent||'').trim():'';"
            ) or "") == n
        )
    )
    time.sleep(0.5)


def assert_case(number: str, metrics: dict) -> tuple[bool, str]:
    assets = metrics.get("assets") or {}
    if assets.get("js", 0) < 1:
        return False, "plate-system.js cache bust missing"
    if not assets.get("css"):
        return False, "plate-system.css cache bust missing"
    if not metrics.get("hasGlyphs"):
        return False, "#plate-number missing has-glyphs"
    if metrics.get("ones") != metrics.get("expectedOnes"):
        return False, f".plate-num-1 count {metrics.get('ones')} != expected {metrics.get('expectedOnes')}"
    if metrics.get("nonOneSpans") != metrics.get("expectedNonOne"):
        return False, (
            f"non-one span count {metrics.get('nonOneSpans')} != expected {metrics.get('expectedNonOne')}"
        )
    if not metrics.get("spanClassesOk"):
        return False, "digit span classes incorrect"
    if not metrics.get("codePlain"):
        return False, f"#plate-code not plain text (plate-num-1={metrics.get('codeOneSpans')})"
    if (metrics.get("codeText") or "").upper() != CODE.upper():
        return False, f"code text mismatch: {metrics.get('codeText')}"
    if metrics.get("numberText") != number:
        return False, f"number text mismatch: {metrics.get('numberText')}"
    if not metrics.get("numberInShell"):
        return False, f"number box outside shell: {metrics.get('overflow')}"
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

        for number in NUMBERS:
            print("CASE", number)
            apply_lot(ctrl, disp, number)
            metrics = disp.execute_script(digit_one_js(CACHE), number)
            ok, detail = assert_case(number, metrics)
            shot_path = os.path.join(OUT, f"{number}.png")
            shot_cdp(disp, shot_path)
            case_results[number] = {
                "ok": ok,
                "detail": detail,
                "screenshot": shot_path,
                "metrics": metrics,
            }
            print(("PASS" if ok else "FAIL"), number, detail)

        all_ok = all(r["ok"] for r in case_results.values())
        report = {
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cache_bust": CACHE,
            "display_url": f"{BASE}/live/display-v4/{token}/?v={CACHE}",
            "control_url": f"{BASE}/live/control/v4/?v={CACHE}",
            "credentials": "admin / TempTest123!",
            "plate_type": PTYPE,
            "code": CODE,
            "numbers": NUMBERS,
            "cases": case_results,
            "ok": all_ok,
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
