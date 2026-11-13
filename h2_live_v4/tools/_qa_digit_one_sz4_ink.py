"""Digit 1 vs sibling INK height (oneSz4) — canvas tight bbox."""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "h3auctions.settings")
sys.path.insert(0, r"c:\Users\moham\h3")

BASE = "http://127.0.0.1:8000"
CSS_BUST = "20261113oneSz4"
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\digit_one_scale"
os.makedirs(OUT, exist_ok=True)

INK_MEASURE_JS = r"""
return (function() {
  function glyphInkHeight(el, ch) {
    const root = el.closest('#plate-number') || el;
    const cs = getComputedStyle(el);
    const rs = getComputedStyle(root);
    const fs = parseFloat(cs.fontSize) || parseFloat(rs.fontSize) || 100;
    const font = `${cs.fontWeight || rs.fontWeight || 700} ${fs}px ${cs.fontFamily || rs.fontFamily || 'Oswald'}`;
    const pad = Math.ceil(fs * 0.15);
    const w = Math.ceil(fs * 1.6) + pad * 2;
    const h = Math.ceil(fs * 1.35) + pad * 2;
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    ctx.font = font;
    ctx.fillStyle = '#0a0a0a';
    ctx.textBaseline = 'alphabetic';
    ctx.textAlign = 'center';
    const m = ctx.measureText(ch);
    const asc = m.actualBoundingBoxAscent || fs * 0.78;
    const desc = m.actualBoundingBoxDescent || fs * 0.22;
    const baselineY = pad + asc;
    ctx.fillText(ch, w / 2, baselineY);
    const data = ctx.getImageData(0, 0, w, h).data;
    let minY = h;
    let maxY = -1;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        const a = data[i + 3];
        if (a < 16) continue;
        const lum = (data[i] + data[i + 1] + data[i + 2]) / 3;
        if (lum < 200) {
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }
    }
  const inkH = maxY >= 0 ? maxY - minY + 1 : 0;
    return {
      inkH_px: Math.round(inkH * 1000) / 1000,
      canvas_h: h,
      font,
      digit: ch,
    };
  }

  function beforeStemHeight(el) {
    const parent = el.getBoundingClientRect();
    const cs = getComputedStyle(el, '::before');
    const top = parseFloat(cs.top) || 0;
    const bottom = parseFloat(cs.bottom) || 0;
    const width = parseFloat(cs.width) || 0;
    const height = parent.height - top - bottom;
    return {
      height,
      width,
      top: parent.top + top,
      bottom: parent.top + top + height,
      parent_h: parent.height,
    };
  }

  const number = document.getElementById('plate-number');
  if (!number) return { error: 'no plate-number' };

  const spans = Array.from(number.querySelectorAll('.plate-num'));
  const byDigit = {};
  for (const s of spans) {
    const d = (s.textContent || '').trim();
    if (d && !byDigit[d]) byDigit[d] = s;
  }

  const el7 = byDigit['7'];
  const el5 = byDigit['5'];
  const ones = Array.from(number.querySelectorAll('.plate-num-1'));
  const stems = ones.map((el) => beforeStemHeight(el));
  const stemH = stems.length ? Math.max(...stems.map((s) => s.height)) : 0;

  const ink7 = el7 ? glyphInkHeight(el7, '7') : null;
  const ink5 = el5 ? glyphInkHeight(el5, '5') : null;
  const inkH7 = ink7 ? ink7.inkH_px : null;
  const inkH5 = ink5 ? ink5.inkH_px : null;

  const ratio = inkH7 && stemH ? Math.round((stemH / inkH7) * 10000) / 10000 : null;
  const pass = inkH7 != null && stemH <= inkH7 * 1.05;

  return {
    number: (number.textContent || '').trim(),
    stemH_px: Math.round(stemH * 1000) / 1000,
    inkH7_px: inkH7,
    inkH5_px: inkH5,
    ratio_stem_over_ink7: ratio,
    pass,
    stems,
    ink7,
    ink5,
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


def run_qa(css_bust: str) -> dict:
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
        return {"ok": False, "error": "no session"}

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

    bust_q = f"?v={css_bust}&_={int(time.time())}"
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
        ctrl.find_element(By.ID, "code").send_keys("AA")
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

    result: dict = {}
    try:
        hard_refresh(disp, disp_url)
        wait_ready(disp)
        css_info = disp.execute_script(CSS_CHECK_JS, css_bust)

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
        WebDriverWait(disp, 15).until(
            lambda x: x.execute_script(
                "return document.fonts && document.fonts.status === 'loaded'"
            )
        )

        apply_lot("1751")
        metrics = disp.execute_script(INK_MEASURE_JS)
        shot_plate_closeup(os.path.join(OUT, "1751_sz4.png"))

        apply_lot("1111")
        shot_plate_closeup(os.path.join(OUT, "1111_sz4.png"))

        tz = timezone(timedelta(hours=4))
        result = {
            "ran_at": datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "qa_type": "digit_one_scale_ink_canvas",
            "django": "127.0.0.1:8000",
            "login": "admin / TempTest123!",
            "plate": "dubai / AA",
            "cache_bust": {
                "plate-system.css": css_bust.replace("20261113", "") if css_bust.startswith("20261113") else css_bust,
                "plate-system.css_full": css_bust,
                "css_loaded": bool(css_info.get("loaded")),
                "css_href": css_info.get("href"),
            },
            "display_url": f"{BASE}/live/display-v4/{token}/",
            "ink_measure_1751": metrics,
            "stemH_px": metrics.get("stemH_px"),
            "inkH7_px": metrics.get("inkH7_px"),
            "inkH5_px": metrics.get("inkH5_px"),
            "ratio_stem_over_ink7": metrics.get("ratio_stem_over_ink7"),
            "pass_criterion": "stemH <= inkH7 * 1.05",
            "pass": bool(metrics.get("pass")) and bool(css_info.get("loaded")),
            "screenshots": ["1751_sz4.png", "1111_sz4.png"],
            "verdict": "pass" if metrics.get("pass") and css_info.get("loaded") else "fail",
            "ok": bool(metrics.get("pass")) and bool(css_info.get("loaded")),
        }
        return result
    finally:
        ctrl.quit()
        disp.quit()


def main() -> int:
    result = run_qa(CSS_BUST)
    report_path = os.path.join(OUT, "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
