"""E2E QA — Red Card cinematic glow + persistent number hide (V4)."""
import json
import os
import sys
import time
import urllib.request

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "h3auctions.settings")
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

OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\red_cinematic_glow"
os.makedirs(OUT, exist_ok=True)
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL"), name, detail if detail else "")


def main():
    s = LiveBroadcastSession.objects.get(pk=1)
    token = str(s.display_token)
    ns = normalize_new_style(s.new_style if isinstance(s.new_style, dict) else {})
    ns["number_visible"] = True
    s.new_style = ns
    s.plate_type = s.plate_type or "dubai"
    s.code = s.code or "AA"
    s.number = s.number or "1465"
    s.save()

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--force-device-scale-factor=1")
    ctrl = webdriver.Chrome(options=opts)
    disp = webdriver.Chrome(options=opts)
    disp.set_window_size(1920, 1080)

    def probe():
        return disp.execute_script(
            """
      const num = document.getElementById('plate-number');
      const code = document.getElementById('plate-code');
      const rim = document.getElementById('plate-rim');
      const plate = document.getElementById('plate');
      const cs = rim ? getComputedStyle(rim) : null;
      const after = rim ? getComputedStyle(rim, '::after') : null;
      const st = H2V4State.getState();
      const hud = window.H2V4Character?.getHud?.() || {};
      return {
        digitText: num ? num.textContent : null,
        digitVis: num ? num.style.visibility : null,
        digitOp: num ? getComputedStyle(num).opacity : null,
        digitHidden: num ? num.classList.contains('is-hidden') : null,
        codeText: code ? code.textContent : null,
        codeVis: code ? getComputedStyle(code).visibility : null,
        codeOp: code ? getComputedStyle(code).opacity : null,
        rimRed: rim ? rim.classList.contains('red') : false,
        rimYellow: rim ? rim.classList.contains('yellow') : false,
        illuminate: plate ? plate.classList.contains('red-illuminate') : false,
        yellowIlluminate: plate ? plate.classList.contains('yellow-illuminate') : false,
        redCard: plate ? plate.classList.contains('red-card') : false,
        bgImage: cs ? cs.backgroundImage : null,
        border: after ? after.borderTopWidth + ' ' + after.borderTopStyle : null,
        boxShadow: cs ? cs.boxShadow : null,
        number_visible: st.new_style?.number_visible !== false,
        number_val: st.number,
        charState: hud.state || null,
        action: hud.action || null,
      };
    """
        )

    disp.get(f"http://127.0.0.1:8000/live/display-v4/{token}/")
    WebDriverWait(disp, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4State")
    )
    time.sleep(1.0)

    ctrl.get("http://127.0.0.1:8000/admin/login/?next=/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "input[type=submit],button[type=submit]").click()
    WebDriverWait(ctrl, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge")
    )
    time.sleep(0.5)

    ctrl.execute_script(
        """
      return window.H2V4DjangoBridge?.patch?.({
        plate_type: 'dubai', code: 'AA', number: '1465',
        ns_show_number: true
      });
    """
    )
    time.sleep(1.2)

    before = None
    t0 = time.time()
    while time.time() - t0 < 5:
        before = probe()
        if (
            before
            and before.get("digitVis") != "hidden"
            and float(before.get("digitOp") or 0) > 0.5
            and before.get("number_visible")
        ):
            break
        time.sleep(0.2)

    check(
        "A_before_digits_visible",
        before
        and before.get("number_visible")
        and before.get("digitVis") != "hidden"
        and float(before.get("digitOp") or 0) > 0.5,
        before,
    )
    disp.save_screenshot(os.path.join(OUT, "01_before.png"))

    # --- Test A: Red Card ---
    ctrl.find_element(By.ID, "btn-red").click()

    peak = None
    t0 = time.time()
    while time.time() - t0 < 8.0:
        peak = probe()
        if peak and peak.get("illuminate") and peak.get("rimRed") and peak.get("digitVis") == "hidden":
            break
        time.sleep(0.1)

    check("A_peak_red_illuminate", peak and peak.get("illuminate") is True, peak)
    check("A_peak_rim_red", peak and peak.get("rimRed") is True, peak)
    check(
        "A_peak_no_yellow",
        peak and not peak.get("rimYellow") and not peak.get("yellowIlluminate"),
        peak,
    )
    check(
        "A_peak_digits_hidden",
        peak and (peak.get("digitVis") == "hidden" or float(peak.get("digitOp") or 1) == 0),
        peak,
    )
    check("A_peak_number_state_false", peak and peak.get("number_visible") is False, peak)
    check(
        "A_peak_code_visible",
        peak
        and peak.get("codeText")
        and float(peak.get("codeOp") or 0) > 0.5
        and peak.get("codeVis") != "hidden",
        peak,
    )
    check("A_peak_no_frame_svg", peak and "red_frame" not in (peak.get("bgImage") or ""), peak)
    check(
        "A_peak_no_hard_border",
        peak and ("0px" in (peak.get("border") or "") or "none" in (peak.get("border") or "")),
        peak,
    )
    check("A_peak_number_value_preserved", peak and str(peak.get("number_val")) == "1465", peak)
    disp.save_screenshot(os.path.join(OUT, "02_peak_glow_digits_hidden.png"))

    time.sleep(1.9)
    after_glow = None
    t0 = time.time()
    while time.time() - t0 < 3.0:
        after_glow = probe()
        if after_glow and not after_glow.get("illuminate") and not after_glow.get("rimRed"):
            break
        time.sleep(0.15)

    check(
        "A_after_glow_off",
        after_glow and not after_glow.get("illuminate") and not after_glow.get("rimRed"),
        after_glow,
    )
    check(
        "A_after_digits_still_hidden",
        after_glow
        and (after_glow.get("digitVis") == "hidden" or float(after_glow.get("digitOp") or 1) == 0),
        after_glow,
    )
    check(
        "A_after_number_state_false",
        after_glow and after_glow.get("number_visible") is False,
        after_glow,
    )
    check(
        "A_after_code_still_visible",
        after_glow and after_glow.get("codeText") and float(after_glow.get("codeOp") or 0) > 0.5,
        after_glow,
    )
    disp.save_screenshot(os.path.join(OUT, "03_after_glow_digits_still_hidden.png"))

    t0 = time.time()
    while time.time() - t0 < 6:
        p = probe()
        if p and p.get("charState") in (None, "IDLE", ""):
            break
        time.sleep(0.2)

    # --- Test B: Show Number ---
    ctrl.find_element(By.ID, "btn-show").click()
    restored = None
    t0 = time.time()
    while time.time() - t0 < 5:
        restored = probe()
        if (
            restored
            and restored.get("number_visible")
            and restored.get("digitVis") != "hidden"
            and float(restored.get("digitOp") or 0) > 0.5
        ):
            break
        time.sleep(0.15)

    check(
        "B_show_digits_restored",
        restored
        and restored.get("number_visible")
        and float(restored.get("digitOp") or 0) > 0.5
        and restored.get("digitVis") != "hidden",
        restored,
    )
    check(
        "B_no_red_glow",
        restored and not restored.get("illuminate") and not restored.get("rimRed"),
        restored,
    )
    check(
        "B_number_value",
        restored
        and (restored.get("digitText") == "1465" or str(restored.get("number_val")) == "1465"),
        restored,
    )
    disp.save_screenshot(os.path.join(OUT, "04_after_show_number.png"))

    # --- Test C: Persistence across refresh ---
    ctrl.find_element(By.ID, "btn-red").click()
    t0 = time.time()
    while time.time() - t0 < 8:
        p = probe()
        if p and p.get("number_visible") is False and p.get("illuminate"):
            break
        time.sleep(0.1)
    time.sleep(2.0)
    disp.get(f"http://127.0.0.1:8000/live/display-v4/{token}/")
    WebDriverWait(disp, 20).until(lambda x: x.execute_script("return !!window.H2V4State"))
    time.sleep(1.5)
    persist = probe()
    check(
        "C_refresh_digits_hidden",
        persist
        and persist.get("number_visible") is False
        and (persist.get("digitVis") == "hidden" or float(persist.get("digitOp") or 1) == 0),
        persist,
    )
    check(
        "C_refresh_no_auto_replay_glow",
        persist and not persist.get("illuminate") and not persist.get("rimRed"),
        persist,
    )
    check(
        "C_refresh_no_char_acting",
        persist and persist.get("charState") in (None, "IDLE", ""),
        persist,
    )
    disp.save_screenshot(os.path.join(OUT, "05_refresh_digits_hidden_no_glow.png"))

    # --- Test D: Yellow / Point regression ---
    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(1.0)
    ctrl.find_element(By.ID, "btn-yellow").click()
    ypeak = None
    t0 = time.time()
    while time.time() - t0 < 8:
        ypeak = probe()
        if ypeak and ypeak.get("yellowIlluminate") and ypeak.get("rimYellow"):
            break
        time.sleep(0.1)
    check(
        "D_yellow_illuminate",
        ypeak and ypeak.get("yellowIlluminate") and ypeak.get("rimYellow"),
        ypeak,
    )
    check(
        "D_yellow_not_red",
        ypeak and not ypeak.get("rimRed") and not ypeak.get("illuminate"),
        ypeak,
    )
    time.sleep(5.0)
    ctrl.find_element(By.ID, "btn-point").click()
    time.sleep(3.2)
    pp = probe()
    check("D_point_enters", pp and pp.get("charState") in ("ENTERING", "ACTING", "EXITING"), pp)

    with urllib.request.urlopen(f"http://127.0.0.1:8000/live/api/state/?token={token}") as r:
        api = json.loads(r.read().decode())
    check("api_reachable", "number" in api or "new_style" in api, True)

    qa = {
        "before": before,
        "peak": peak,
        "after_glow": after_glow,
        "restored": restored,
        "persist": persist,
        "yellow": ypeak,
    }
    with open(os.path.join(OUT, "QA.json"), "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2)

    ctrl.quit()
    disp.quit()

    failed = [n for n, ok, _ in results if not ok]
    print("SUMMARY", f"{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED", failed)
        for n, ok, d in results:
            if not ok:
                print(" ", n, d)
        raise SystemExit(1)
    print("OUT", OUT)


if __name__ == "__main__":
    main()
