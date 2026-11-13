"""Digit 1 stem balance (oneBal) — canvas ink vs ::before, plates 2154/1751/1111/1010/8258."""
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
CSS_BUST = "20261113oneBal"
PLATES = ("2154", "1751", "1111", "1010", "8258")
OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\digit_one_scale"
os.makedirs(OUT, exist_ok=True)

MEASURE_2154_JS = r"""
return (function() {
  function glyphInkMetrics(el, ch) {
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
    const baselineY = pad + asc;
    ctx.fillText(ch, w / 2, baselineY);
    const data = ctx.getImageData(0, 0, w, h).data;
    const dark = (x, y) => {
      const i = (y * w + x) * 4;
      const a = data[i + 3];
      if (a < 16) return false;
      const lum = (data[i] + data[i + 1] + data[i + 2]) / 3;
      return lum < 200;
    };
    let minY = h, maxY = -1;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        if (!dark(x, y)) continue;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
    const inkH = maxY >= 0 ? maxY - minY + 1 : 0;
    let vertStrokeW = 0;
    if (inkH > 0 && ch === '2') {
      const y0 = minY + Math.floor(inkH * 0.22);
      const y1 = minY + Math.floor(inkH * 0.48);
      const colCounts = new Array(w).fill(0);
      for (let y = y0; y <= y1; y++) {
        for (let x = 0; x < w; x++) {
          if (dark(x, y)) colCounts[x]++;
        }
      }
      const thresh = Math.max(2, Math.floor((y1 - y0 + 1) * 0.55));
      let bestLen = 0, run = 0;
      for (let x = 0; x < w; x++) {
        if (colCounts[x] >= thresh) {
          run++;
        } else {
          if (run > bestLen) bestLen = run;
          run = 0;
        }
      }
      if (run > bestLen) bestLen = run;
      vertStrokeW = bestLen;
    }
    return {
      digit: ch,
      inkH_px: Math.round(inkH * 1000) / 1000,
      vertStrokeW_px: vertStrokeW ? Math.round(vertStrokeW * 1000) / 1000 : null,
    };
  }

  function beforeStem(el) {
    const parent = el.getBoundingClientRect();
    const cs = getComputedStyle(el, '::before');
    const top = parseFloat(cs.top) || 0;
    const bottom = parseFloat(cs.bottom) || 0;
    const width = parseFloat(cs.width) || 0;
    const height = parent.height - top - bottom;
    return {
      stemH_px: Math.round(height * 1000) / 1000,
      stemW_px: Math.round(width * 1000) / 1000,
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

  const ones = Array.from(number.querySelectorAll('.plate-num-1'));
  const stem = ones.length ? beforeStem(ones[0]) : { stemH_px: 0, stemW_px: 0 };

  const siblingInk = {};
  const heights = [];
  for (const d of ['2', '5', '4']) {
    const el = byDigit[d];
    if (!el) continue;
    const m = glyphInkMetrics(el, d);
    siblingInk[d] = m;
    if (m.inkH_px) heights.push(m.inkH_px);
  }
  heights.sort((a, b) => a - b);
  const medianInk =
    heights.length === 0
      ? null
      : heights.length % 2
      ? heights[(heights.length - 1) / 2]
      : (heights[heights.length / 2 - 1] + heights[heights.length / 2]) / 2;

  const stemH = stem.stemH_px;
  const ratio = medianInk && stemH ? Math.round((stemH / medianInk) * 10000) / 10000 : null;
  const pctDiff = medianInk && stemH ? Math.round(((stemH - medianInk) / medianInk) * 10000) / 100 : null;
  const passHeight = medianInk != null && Math.abs(pctDiff) <= 6;

  const ink2 = siblingInk['2'] || null;
  const widthRatio =
    ink2 && ink2.vertStrokeW_px && stem.stemW_px
      ? Math.round((stem.stemW_px / ink2.vertStrokeW_px) * 10000) / 10000
      : null;

  return {
    number: (number.textContent || '').trim(),
    stemH_px: stemH,
    stemW_px: stem.stemW_px,
    sibling_ink_heights_px: Object.fromEntries(
      Object.entries(siblingInk).map(([k, v]) => [k, v.inkH_px])
    ),
    median_sibling_inkH_px: medianInk != null ? Math.round(medianInk * 1000) / 1000 : null,
    ratio_stem_over_median_ink: ratio,
    pct_stem_vs_median: pctDiff,
    pass_height_within_6pct: passHeight,
    digit2_vert_strokeW_px: ink2 ? ink2.vertStrokeW_px : null,
    ratio_stemW_over_digit2_vert: widthRatio,
    pass: passHeight,
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


def run_qa(css_bust: str, plates: tuple[str, ...] = PLATES, measure_only_2154: bool = True) -> dict:
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

    cases: dict = {}
    measure_2154 = None
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
            lambda x: x.execute_script("return document.fonts && document.fonts.status === 'loaded'")
        )

        run_plates = ("2154",) if (measure_only_2154 and len(plates) == 1) else plates
        for num in run_plates:
            apply_lot(num)
            shot = os.path.join(OUT, f"{num}_bal.png")
            shot_plate_closeup(shot)
            entry = {"screenshot": f"{num}_bal.png", "plate": f"dubai AA {num}"}
            if num == "2154":
                measure_2154 = disp.execute_script(MEASURE_2154_JS)
                entry.update(measure_2154)
            cases[num] = entry

        tz = timezone(timedelta(hours=4))
        need_tweak = False
        if measure_2154 and measure_2154.get("pct_stem_vs_median") is not None:
            need_tweak = abs(measure_2154["pct_stem_vs_median"]) > 8

        result = {
            "ran_at": datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "qa_type": "digit_one_scale_oneBal",
            "django": "127.0.0.1:8000",
            "login": "admin / TempTest123!",
            "plate": "dubai / AA",
            "cache_bust": {
                "plate-system.css": css_bust,
                "css_loaded": bool(css_info.get("loaded")),
                "css_href": css_info.get("href"),
            },
            "display_url": f"{BASE}/live/display-v4/{token}/",
            "numbers": list(run_plates),
            "measure_2154": measure_2154,
            "pass_criterion": "stemH within ±6% of median sibling ink height (digits 2,5,4 canvas bbox)",
            "cases": cases,
            "need_css_tweak_gt_8pct": need_tweak,
            "verdict": "pass" if measure_2154 and measure_2154.get("pass") and css_info.get("loaded") else "fail",
            "ok": bool(measure_2154 and measure_2154.get("pass") and css_info.get("loaded")),
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
