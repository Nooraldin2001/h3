"""E2E QA — SOLD stamp left-bias vs plate number (cache v=20261113soldL2)."""
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
CACHE = "20261113soldL2"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\sold_stamp_left"
os.makedirs(OUT, exist_ok=True)

MEASURE_JS = """
const stamp = document.getElementById('plate-sold-stamp');
const num = document.getElementById('plate-number');
const codeEl = document.getElementById('plate-code');
const plate = document.getElementById('plate');
const codeR = codeEl ? codeEl.getBoundingClientRect() : null;
const cs = stamp ? getComputedStyle(stamp) : null;
const sr = stamp ? stamp.getBoundingClientRect() : null;
const nr = num ? num.getBoundingClientRect() : null;
const digitText = num ? (num.textContent || '').replace(/\\s+/g, '') : '';
const digitCount = digitText.length || 4;
let digitCenters = [];
if (nr && digitCount > 0) {
  for (let i = 0; i < digitCount; i++) {
    const left = nr.left + (nr.width * (i + 0.5) / digitCount);
    digitCenters.push(left);
  }
}
const stampCx = sr ? sr.left + sr.width / 2 : null;
const numCx = nr ? nr.left + nr.width / 2 : null;
const stampRight = sr ? sr.right : null;
const digit3Left = digitCenters.length >= 3 ? nr.left + nr.width * (2 / digitCount) : (nr ? nr.left + nr.width * 0.5 : null);
const stampLeftPct = (sr && plate) ? ((sr.left - plate.getBoundingClientRect().left) / plate.getBoundingClientRect().width * 100) : null;
const numCenterPctPlate = (nr && plate) ? (((nr.left + nr.width/2) - plate.getBoundingClientRect().left) / plate.getBoundingClientRect().width * 100) : null;
const stampCenterPctPlate = (sr && plate) ? (((sr.left + sr.width/2) - plate.getBoundingClientRect().left) / plate.getBoundingClientRect().width * 100) : null;
const stampCoversLeftHalf = sr && nr ? (sr.right < nr.left + nr.width * 0.55) : false;
const lastTwoOutsideStamp = sr && nr && digitCount >= 2
  ? (stampRight < nr.left + nr.width * ((digitCount - 2) / digitCount))
  : false;
const stampClearsCode = sr && codeR ? sr.left > codeR.right - 2 : null;
return {
  imprint: !!(stamp && stamp.classList.contains('imprint')),
  code: codeR ? { left: codeR.left, right: codeR.right, width: codeR.width } : null,
  stampClearsCode,
  opacity: cs ? parseFloat(cs.opacity) : 0,
  digitText,
  digitCount,
  stamp: sr ? { left: sr.left, right: sr.right, top: sr.top, width: sr.width, height: sr.height, centerX: stampCx } : null,
  number: nr ? { left: nr.left, right: nr.right, width: nr.width, height: nr.height, centerX: numCx } : null,
  digitCenters,
  digit3Left,
  stampRightBeforeDigit3: stampRight != null && digit3Left != null ? stampRight < digit3Left : null,
  stampCenterLeftOfNumber: stampCx != null && numCx != null ? stampCx < numCx : null,
  stampCoversLeftHalf,
  lastTwoDigitsOutsideStampRight: lastTwoOutsideStamp,
  stampCenterPctPlate,
  numCenterPctPlate,
  stampLeftPct,
  deltaCenterPx: stampCx != null && numCx != null ? (numCx - stampCx) : null,
};
"""


def closeup_stamp(disp, path: str, vw: int = 1920, vh: int = 1080) -> bool:
    clip = disp.execute_script(
        f"""
        const stamp = document.getElementById('plate-sold-stamp');
        const num = document.getElementById('plate-number');
        if (!stamp || !num) return null;
        const r = stamp.getBoundingClientRect();
        const n = num.getBoundingClientRect();
        const left = Math.min(r.left, n.left);
        const top = Math.min(r.top, n.top);
        const right = Math.max(r.right, n.right);
        const bottom = Math.max(r.bottom, n.bottom);
        const pad = 24;
        const sx = Math.max(0, Math.floor(left - pad));
        const sy = Math.max(0, Math.floor(top - pad));
        const sw = Math.min({vw} - sx, Math.ceil(right - left + pad * 2));
        const sh = Math.min({vh} - sy, Math.ceil(bottom - top + pad * 2));
        return {{x: sx, y: sy, width: sw, height: sh, scale: 1}};
        """
    )
    if clip and clip.get("width", 0) > 10:
        shot_cdp(disp, path, clip)
        return True
    return False


def set_viewport(driver, w: int, h: int) -> None:
    driver.set_window_size(w, h)
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )


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


def shot_cdp(driver, path: str, clip: dict | None = None) -> str:
    args: dict = {"format": "png", "fromSurface": True}
    if clip:
        args["clip"] = clip
    data = driver.execute_cdp_cmd("Page.captureScreenshot", args)
    with open(path, "wb") as f:
        f.write(base64.b64decode(data["data"]))
    return path


def apply_lot(ctrl, disp, number: str, code: str = "AA", ptype: str = "dubai") -> None:
    Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(ptype)
    ctrl.find_element(By.ID, "code").clear()
    ctrl.find_element(By.ID, "code").send_keys(code)
    ctrl.find_element(By.ID, "number").clear()
    ctrl.find_element(By.ID, "number").send_keys(number)
    ctrl.find_element(By.ID, "btn-apply-lot").click()
    WebDriverWait(disp, 12).until(
        lambda x: number in (
            x.execute_script(
                "const n=document.getElementById('plate-number'); return n?(n.textContent||'').trim():'';"
            )
            or ""
        ).replace(" ", "")
    )
    time.sleep(0.4)


def wait_imprint(disp, timeout: float = 10.0) -> dict:
    t0 = time.time()
    last = {}
    while time.time() - t0 < timeout:
        last = disp.execute_script(MEASURE_JS)
        if last.get("imprint") and float(last.get("opacity") or 0) > 0.85:
            return last
        time.sleep(0.08)
    return last


def wait_clear(disp, timeout: float = 8.0) -> dict:
    t0 = time.time()
    last = {}
    while time.time() - t0 < timeout:
        last = disp.execute_script(
            """
            const stamp = document.getElementById('plate-sold-stamp');
            const cs = stamp ? getComputedStyle(stamp) : null;
            return {
              imprint: !!(stamp && stamp.classList.contains('imprint')),
              opacity: cs ? parseFloat(cs.opacity) : 0,
              hidden: stamp ? stamp.hidden : null,
            };
            """
        )
        if not last.get("imprint") and float(last.get("opacity") or 0) < 0.2:
            return last
        time.sleep(0.1)
    return last


def eval_position(m: dict) -> dict:
    checks = {
        "stamp_center_left_of_number": bool(m.get("stampCenterLeftOfNumber")),
        "stamp_right_before_digit3": bool(m.get("stampRightBeforeDigit3")),
        "stamp_covers_left_half": bool(m.get("stampCoversLeftHalf")),
        "last_two_digits_outside_stamp": bool(m.get("lastTwoDigitsOutsideStampRight")),
        "stamp_clears_code_aa": bool(m.get("stampClearsCode")),
    }
    checks["pass"] = all(checks.values())
    return checks


def click_studio_theme(ctrl, disp, theme: str, btn_id: str) -> None:
    ctrl.execute_script(
        "const el=document.getElementById(arguments[0]); el.scrollIntoView({block:'center'}); el.click();",
        btn_id,
    )
    WebDriverWait(disp, 12).until(
        lambda x: x.execute_script(
            f"const st=H2V4State.getState(); return st.new_style && st.new_style.studio_theme==='{theme}';"
        )
    )
    time.sleep(0.6)


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
            "return !!window.H2V4DjangoBridge && !!window.H2V4State && !!window.H2V4SoldFx && !!window.H2PlateSystem"
        )
    )
    time.sleep(0.5)


def cache_on_display(disp) -> dict:
    return disp.execute_script(
        f"""
        const urls = Array.from(document.querySelectorAll('link[rel=stylesheet], script[src]'))
          .map(el => el.href || el.src).filter(Boolean);
        const hits = urls.filter(u => u.includes('{CACHE}')).length;
        const fx = urls.find(u => u.includes('fx-sold.js'));
        return {{ cacheHits: hits, fxSoldSrc: fx || null, totalAssets: urls.length }};
        """
    )


def trigger_sold(ctrl) -> None:
    ctrl.find_element(By.ID, "btn-sold").click()


def main() -> int:
    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        print("FAIL no session")
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
    report: dict = {
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cache_bust": CACHE,
        "credentials": "admin / TempTest123!",
        "scenarios": {},
        "ok": False,
    }

    try:
        disp_url = f"{BASE}/live/display-v4/{token}/{bust}"
        ctrl_url = f"{BASE}/live/control/v4/{bust}"

        hard_refresh(disp, disp_url)
        wait_display_ready(disp)
        cache_info = cache_on_display(disp)
        report["display_cache"] = cache_info

        login_control(ctrl)
        hard_refresh(disp, disp_url)
        wait_display_ready(disp)

        # --- 8258 primary ---
        apply_lot(ctrl, disp, "8258", "AA", "dubai")
        trigger_sold(ctrl)
        m8258 = wait_imprint(disp, 12.0)
        time.sleep(0.35)
        m8258 = disp.execute_script(MEASURE_JS)
        checks8258 = eval_position(m8258)
        shot_cdp(disp, os.path.join(OUT, "8258_sold.png"))
        closeup_stamp(disp, os.path.join(OUT, "8258_sold_closeup.png"))
        report["scenarios"]["8258_sold"] = {"measurements": m8258, "checks": checks8258}

        # UNSOLD
        ctrl.find_element(By.ID, "btn-cancel-sold").click()
        cleared = wait_clear(disp)
        shot_cdp(disp, os.path.join(OUT, "8258_unsold_cleared.png"))
        report["scenarios"]["8258_unsold"] = {"cleared": cleared}

        # SOLD again — compare positioning
        trigger_sold(ctrl)
        m8258b = wait_imprint(disp, 12.0)
        time.sleep(0.25)
        m8258b = disp.execute_script(MEASURE_JS)
        checks8258b = eval_position(m8258b)
        delta_cx = abs((m8258.get("stamp") or {}).get("centerX", 0) - (m8258b.get("stamp") or {}).get("centerX", 0))
        reposition_ok = delta_cx < 3.0 and checks8258b.get("pass")
        report["scenarios"]["8258_sold_repeat"] = {
            "measurements": m8258b,
            "checks": checks8258b,
            "stamp_center_delta_px": delta_cx,
            "same_positioning": reposition_ok,
        }
        shot_cdp(disp, os.path.join(OUT, "8258_sold_repeat.png"))

        apply_lot(ctrl, disp, "1234")
        trigger_sold(ctrl)
        wait_imprint(disp)
        shot_cdp(disp, os.path.join(OUT, "1234_sold.png"))
        m1234 = disp.execute_script(MEASURE_JS)
        report["scenarios"]["1234_sold"] = {
            "measurements": m1234,
            "checks": eval_position(m1234),
        }
        ctrl.find_element(By.ID, "btn-cancel-sold").click()
        wait_clear(disp)

        # Quick 7777
        apply_lot(ctrl, disp, "7777")
        trigger_sold(ctrl)
        wait_imprint(disp)
        shot_cdp(disp, os.path.join(OUT, "7777_sold.png"))
        m7777 = disp.execute_script(MEASURE_JS)
        report["scenarios"]["7777_sold"] = {
            "measurements": m7777,
            "checks": eval_position(m7777),
        }
        ctrl.find_element(By.ID, "btn-cancel-sold").click()
        wait_clear(disp)

        # Quick 12345 (5 digits)
        apply_lot(ctrl, disp, "12345")
        trigger_sold(ctrl)
        wait_imprint(disp)
        shot_cdp(disp, os.path.join(OUT, "12345_sold.png"))
        m12345 = disp.execute_script(MEASURE_JS)
        report["scenarios"]["12345_sold"] = {
            "measurements": m12345,
            "checks": eval_position(m12345),
        }
        ctrl.find_element(By.ID, "btn-cancel-sold").click()
        wait_clear(disp)

        apply_lot(ctrl, disp, "8258", "AA", "dubai")
        studio_results: dict = {}
        for theme, btn in (
            ("dark", "btn-studio-dark"),
            ("light", "btn-studio-light"),
            ("new", "btn-studio-new"),
        ):
            click_studio_theme(ctrl, disp, theme, btn)
            ctrl.find_element(By.ID, "btn-cancel-sold").click()
            wait_clear(disp, 4.0)
            trigger_sold(ctrl)
            wait_imprint(disp)
            m_th = disp.execute_script(MEASURE_JS)
            ch = eval_position(m_th)
            shot_cdp(disp, os.path.join(OUT, f"8258_sold_studio_{theme}.png"))
            studio_results[theme] = {"measurements": m_th, "checks": ch}

        report["scenarios"]["8258_studio_modes"] = studio_results
        studio_placement_ok = all(
            v["checks"].get("stamp_center_left_of_number") and v["checks"].get("stamp_right_before_digit3")
            for v in studio_results.values()
        )

        set_viewport(disp, 1280, 720)
        hard_refresh(disp, disp_url)
        wait_display_ready(disp)
        report["display_cache_720"] = cache_on_display(disp)
        apply_lot(ctrl, disp, "8258", "AA", "dubai")
        trigger_sold(ctrl)
        m720 = wait_imprint(disp, 12.0)
        time.sleep(0.35)
        m720 = disp.execute_script(MEASURE_JS)
        checks720 = eval_position(m720)
        shot_cdp(disp, os.path.join(OUT, "8258_sold_720.png"))
        closeup_stamp(disp, os.path.join(OUT, "8258_sold_720_closeup.png"), 1280, 720)
        report["scenarios"]["8258_sold_720"] = {"measurements": m720, "checks": checks720}

        keys = [
            checks8258.get("pass"),
            cleared and not cleared.get("imprint"),
            reposition_ok,
            checks720.get("pass"),
            (report["scenarios"]["7777_sold"]["checks"] or {}).get("pass"),
            (report["scenarios"]["12345_sold"]["checks"] or {}).get("pass"),
            studio_placement_ok,
            cache_info.get("cacheHits", 0) >= 1,
        ]
        report["ok"] = all(keys)
        def edge_nums(m: dict) -> dict:
            st = (m.get("stamp") or {}).get("right")
            d3 = m.get("digit3Left")
            return {
                "stamp_right": st,
                "digit3_left": d3,
                "gap_px": (d3 - st) if st is not None and d3 is not None else None,
                "stamp_right_before_digit3": bool(m.get("stampRightBeforeDigit3")),
            }

        report["summary"] = {
            "8258_primary_pass": checks8258.get("pass"),
            "8258_1920_edges": edge_nums(m8258),
            "8258_720_edges": edge_nums(m720),
            "stamp_center_pct_plate": m8258.get("stampCenterPctPlate"),
            "number_center_pct_plate": m8258.get("numCenterPctPlate"),
            "stamp_left_pct_plate": m8258.get("stampLeftPct"),
            "delta_center_px": m8258.get("deltaCenterPx"),
            "unsold_cleared": bool(cleared and not cleared.get("imprint")),
            "repeat_same_positioning": reposition_ok,
            "studio_modes_left_bias": studio_placement_ok,
        }
        report_path = os.path.join(OUT, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        status = "PASS" if report["ok"] else "FAIL"
        s = report["summary"]
        e192 = s.get("8258_1920_edges") or {}
        e720 = s.get("8258_720_edges") or {}
        print(status)
        print(
            "8258@1920",
            f"stamp.right={e192.get('stamp_right')}",
            f"digit3Left={e192.get('digit3_left')}",
            f"gap={e192.get('gap_px')}",
        )
        print(
            "8258@720",
            f"stamp.right={e720.get('stamp_right')}",
            f"digit3Left={e720.get('digit3_left')}",
            f"gap={e720.get('gap_px')}",
        )
        print(
            f"stamp_center%={s.get('stamp_center_pct_plate'):.2f}" if s.get("stamp_center_pct_plate") else "stamp_center%=n/a",
            f"delta_center_px={s.get('delta_center_px')}",
        )
        print("REPORT", report_path)
        return 0 if report["ok"] else 1
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
