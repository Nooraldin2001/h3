"""One-off re-check: digit 1 stem vs siblings (oneSz3)."""
from __future__ import annotations

import base64
import json
import os
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "h3auctions.settings")
sys.path.insert(0, r"c:\Users\moham\h3")

BASE = "http://127.0.0.1:8000"
CSS_BUST = "20261113oneSz3"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\digit_one_scale"
os.makedirs(OUT, exist_ok=True)

STEM_MEASURE_JS = r"""
return (function() {
  const number = document.getElementById('plate-number');
  if (!number) return { error: 'no plate-number' };

  function pseudoBeforeRect(el) {
    const parent = el.getBoundingClientRect();
    const cs = getComputedStyle(el, '::before');
    const top = parseFloat(cs.top) || 0;
    const bottom = parseFloat(cs.bottom) || 0;
    const width = parseFloat(cs.width) || 0;
    const height = parseFloat(cs.height) || (parent.height - top - bottom);
    return {
      height,
      width,
      top: parent.top + top,
      bottom: parent.top + top + height,
    };
  }

  const tol = 2;
  const ones = Array.from(number.querySelectorAll('.plate-num-1'));
  const siblings = Array.from(number.querySelectorAll('.plate-num:not(.plate-num-1)'));
  const stems = ones.map((el) => ({ ...pseudoBeforeRect(el), digit: '1' }));

  const sibRects = siblings.map((el) => {
    const r = el.getBoundingClientRect();
    return {
      digit: (el.textContent || '').trim(),
      height: r.height,
      top: r.top,
      bottom: r.bottom,
    };
  });

  const refSibling = sibRects.length
    ? sibRects.reduce((a, b) => (a.height >= b.height ? a : b))
    : null;

  const pairwise = [];
  let pass = true;
  const maxStem = stems.length ? Math.max(...stems.map((s) => s.height)) : 0;

  if (refSibling && stems.length) {
    for (const stem of stems) {
      const s = refSibling;
      const topOk = stem.top >= s.top - tol;
      const bottomOk = stem.bottom <= s.bottom + tol;
      const heightTarget = s.height * 0.7;
      const heightLo = s.height * 0.65;
      const heightHi = s.height * 0.78;
      const heightOk = stem.height >= heightLo && stem.height <= heightHi;
      const bottomNear = Math.abs(stem.bottom - s.bottom) <= tol + 1;
      const dominates = stem.height > s.height * 0.82 || stem.top < s.top - tol;
      const rowPass = topOk && bottomOk && heightOk && bottomNear && !dominates;
      if (!rowPass) pass = false;
      pairwise.push({
        vs_digit: s.digit,
        stem_h_px: Math.round(stem.height * 100) / 100,
        sibling_h_px: Math.round(s.height * 100) / 100,
        stem_top: Math.round(stem.top * 100) / 100,
        stem_bottom: Math.round(stem.bottom * 100) / 100,
        sib_top: Math.round(s.top * 100) / 100,
        sib_bottom: Math.round(s.bottom * 100) / 100,
        ratio: Math.round((stem.height / s.height) * 1000) / 1000,
        top_ok: topOk,
        bottom_ok: bottomOk,
        height_ok: heightOk,
        bottom_near: bottomNear,
        dominates,
        pass: rowPass,
      });
    }
  } else if (stems.length && !siblings.length) {
    pass = true;
  }

  return {
    maxStem_px: Math.round(maxStem * 100) / 100,
    sibling_digit: refSibling ? refSibling.digit : null,
    sibling_boxH_px: refSibling ? Math.round(refSibling.height * 100) / 100 : null,
    stem_vs_sibling: refSibling ? Math.round((maxStem / refSibling.height) * 1000) / 1000 : null,
    stem_taller_than_siblings: refSibling ? maxStem > refSibling.height * 1.02 : false,
    pairwise,
    pass,
  };
})();
"""

CSS_CHECK_JS = r"""
return (function(bust) {
  const links = Array.from(document.querySelectorAll('link[rel=stylesheet]'));
  const plateCss = links.find(l => (l.href || '').includes('plate-system.css'));
  const href = plateCss ? plateCss.href : null;
  const loaded = !!links.some(l => (l.href || '').includes('plate-system.css') && (l.href || '').includes(bust));
  return { href, loaded, bust };
})(arguments[0]);
"""


def main() -> int:
    import django

    django.setup()
    from plates.models import LiveBroadcastSession  # noqa: E402
    from plates.new_style import normalize_new_style  # noqa: E402
    from selenium import webdriver  # noqa: E402
    from selenium.webdriver.chrome.options import Options  # noqa: E402
    from selenium.webdriver.common.by import By  # noqa: E402
    from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
    from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402

    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        print(json.dumps({"ok": False, "error": "no session"}))
        return 1

    ns = normalize_new_style(session.new_style if isinstance(session.new_style, dict) else {})
    ns["number_visible"] = True
    ns["sold_imprint_active"] = False
    ns.setdefault("studio_theme", "dark")
    session.new_style = ns
    session.save(update_fields=["new_style"])
    token = str(session.display_token)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--hide-scrollbars")
    ctrl = webdriver.Chrome(options=opts)
    disp = webdriver.Chrome(options=opts)
    for d in (ctrl, disp):
        d.set_window_size(1920, 1080)
        d.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
        )

    bust_q = f"?v={CSS_BUST}&_={int(time.time())}"
    disp_url = f"{BASE}/live/display-v4/{token}/{bust_q}"
    ctrl_url = f"{BASE}/live/control/v4/{bust_q}"

    def hard_refresh(driver, url: str) -> None:
        driver.get(url)
        WebDriverWait(driver, 25).until(lambda x: x.execute_script("return document.readyState") == "complete")
        driver.execute_cdp_cmd("Page.reload", {"ignoreCache": True})
        time.sleep(0.6)

    def wait_ready(d):
        WebDriverWait(d, 25).until(
            lambda x: x.execute_script(
                "return !!window.H2V4DjangoBridge && !!window.H2V4State && !!window.H2PlateSystem"
            )
        )
        time.sleep(0.5)

    def apply_lot(number: str) -> None:
        Select(ctrl.find_element(By.ID, "plate-type")).select_by_value("dubai")
        ctrl.find_element(By.ID, "code").clear()
        ctrl.find_element(By.ID, "code").send_keys("A")
        ctrl.find_element(By.ID, "number").clear()
        ctrl.find_element(By.ID, "number").send_keys(number)
        ctrl.find_element(By.ID, "btn-apply-lot").click()
        WebDriverWait(disp, 12).until(
            lambda x: x.execute_script(
                "const el=document.getElementById('plate-number');"
                "const want=arguments[0];"
                "return el && el.classList.contains('has-glyphs') && (el.textContent||'').trim()===want;",
                number,
            )
        )
        time.sleep(0.45)

    def shot_plate_closeup(path: str) -> None:
        clip = disp.execute_script(
            """
            const num = document.getElementById('plate-number');
            const plate = document.getElementById('plate');
            const el = num || plate;
            if (!el) return null;
            const r = el.getBoundingClientRect();
            const pad = 24;
            return {
              x: Math.max(0, r.left - pad),
              y: Math.max(0, r.top - pad),
              width: Math.min(1920 - Math.max(0, r.left - pad), r.width + pad * 2),
              height: Math.min(1080 - Math.max(0, r.top - pad), r.height + pad * 2),
              scale: 1,
            };
            """
        )
        if not clip:
            raise RuntimeError("no clip region")
        data = disp.execute_cdp_cmd(
            "Page.captureScreenshot",
            {"format": "png", "fromSurface": True, "clip": clip},
        )
        with open(path, "wb") as f:
            f.write(base64.b64decode(data["data"]))

    result: dict = {"css_bust": CSS_BUST, "cases": {}}

    try:
        hard_refresh(disp, disp_url)
        wait_ready(disp)
        css_info = disp.execute_script(CSS_CHECK_JS, CSS_BUST)
        result["css"] = css_info

        ctrl.get(f"{BASE}/admin/login/?next=/live/control/v4/")
        WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
        ctrl.find_element(By.NAME, "username").send_keys("admin")
        ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
        ctrl.find_element(By.CSS_SELECTOR, "input[type=submit],button[type=submit]").click()
        WebDriverWait(ctrl, 20).until(
            lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!document.getElementById('btn-apply-lot')")
        )
        hard_refresh(ctrl, ctrl_url)
        hard_refresh(disp, disp_url)
        wait_ready(disp)

        shot_map = (
            ("1751", "1751_sz3.png"),
            ("1111", "1111_sz3.png"),
            ("1010", "1010_sz3.png"),
            ("8258", "8258_sz3.png"),
        )
        for number, shot_name in shot_map:
            apply_lot(number)
            metrics = disp.execute_script(STEM_MEASURE_JS)
            shot_plate_closeup(os.path.join(OUT, shot_name))
            result["cases"][number] = {"metrics": metrics, "screenshot": shot_name}

        css_ok = bool(css_info.get("loaded"))
        m1751 = result["cases"]["1751"]["metrics"]
        pass_1751 = css_ok and bool(m1751.get("pass")) and not m1751.get("stem_taller_than_siblings")
        result["pass"] = pass_1751
        result["verdict"] = "pass" if pass_1751 else "fail"
        result["django"] = "127.0.0.1:8000"
        result["login"] = "admin"
        result["plate"] = "dubai / A"
        result["display_url"] = disp_url.split("?")[0]
        result["ok"] = pass_1751
        report_path = os.path.join(OUT, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result, indent=2))
        return 0 if pass_1751 else 1
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
