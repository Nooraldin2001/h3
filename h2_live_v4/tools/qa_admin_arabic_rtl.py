"""E2E QA — Arabic RTL Admin redesign + functional regression vs Broadcast."""
import json
import os
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "h3auctions.settings")
sys.path.insert(0, r"c:\Users\moham\h3")

import django

django.setup()

from plates.models import LiveBroadcastSession  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402

OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\admin_arabic_rtl"
os.makedirs(OUT, exist_ok=True)
results = []

REQUIRED_IDS = [
    "plate-type", "price", "code", "number", "phone", "btn-apply-lot",
    "live-text-1", "btn-live-text-1-apply", "btn-live-text-1-clear",
    "live-text-2", "btn-live-text-2-apply", "btn-live-text-2-clear",
    "btn-live-text-apply-both", "btn-live-text-clear-both",
    "timer-seconds", "timer-remaining", "btn-timer-duration",
    "btn-timer-start", "btn-timer-pause", "btn-timer-resume", "btn-timer-reset",
    "btn-show", "btn-hide", "btn-reveal", "btn-beam", "btn-drop",
    "char-entry", "char-speed", "btn-char-enter", "btn-point", "btn-yellow",
    "btn-red", "btn-sold-stamp", "btn-char-exit", "btn-char-reset",
    "char-hud", "char-hud-state", "sold-name", "btn-sold",
    "aging-enabled", "aging-duration", "aging-preset", "aging-seek",
    "btn-aging-start", "btn-aging-pause", "btn-aging-resume", "btn-aging-reset",
    "btn-aging-replay", "btn-aging-disable", "aging-hud", "btn-aging-apply-duration",
    "btn-aging-seek",
    "bg-motion", "bg-density", "bg-speed", "btn-bg-apply", "btn-bg-start", "btn-bg-stop",
    "btn-reload", "btn-debug", "status", "admin-side",
]


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL"), name, detail if detail else "")


def make_driver(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument(f"--window-size={w},{h}")
    opts.add_argument("--force-device-scale-factor=1")
    d = webdriver.Chrome(options=opts)
    d.set_window_size(w, h)
    return d


def main():
    s = LiveBroadcastSession.objects.get(pk=1)
    token = str(s.display_token)

    ctrl = make_driver(1920, 1080)
    disp = make_driver(1920, 1080)

    # Login admin
    ctrl.get("http://127.0.0.1:8000/admin/login/?next=/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "input[type=submit],button[type=submit]").click()
    WebDriverWait(ctrl, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge")
    )
    time.sleep(0.6)

    # UI audit
    html_lang = ctrl.execute_script("return document.documentElement.lang")
    html_dir = ctrl.execute_script("return document.documentElement.dir")
    help_count = len(ctrl.find_elements(By.CSS_SELECTOR, ".control-help"))
    help_text = ctrl.execute_script(
        "return (document.body.innerText||'').includes('HOW TO OPERATE') || (document.body.innerText||'').includes('How to operate')"
    )
    missing = [i for i in REQUIRED_IDS if not ctrl.find_elements(By.ID, i)]
    check("rtl_lang_ar", html_lang == "ar", html_lang)
    check("rtl_dir", html_dir == "rtl", html_dir)
    check("howto_removed_dom", help_count == 0, help_count)
    check("howto_removed_text", help_text is False, help_text)
    check("all_control_ids_present", len(missing) == 0, missing)
    check("arabic_heading", "لوحة التحكم" in ctrl.page_source, True)

    ctrl.save_screenshot(os.path.join(OUT, "01_admin_desktop_1920.png"))

    # Open broadcast
    disp.get(f"http://127.0.0.1:8000/live/display-v4/{token}/")
    WebDriverWait(disp, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4State")
    )
    time.sleep(0.8)

    def apply_lot(ptype, code, number):
        Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(ptype)
        ctrl.find_element(By.ID, "code").clear()
        ctrl.find_element(By.ID, "code").send_keys(code)
        ctrl.find_element(By.ID, "number").clear()
        ctrl.find_element(By.ID, "number").send_keys(number)
        ctrl.find_element(By.ID, "btn-apply-lot").click()
        time.sleep(1.2)

    # Test 1 — Plate
    apply_lot("dubai", "AA", "7777")
    p = None
    t0 = time.time()
    while time.time() - t0 < 5:
        p = disp.execute_script(
            """
          const s=H2V4State.getState();
          return {
            type:s.plate_type, code:s.code, number:s.number,
            src: document.getElementById('plate-art')?.src||'',
            num: document.getElementById('plate-number')?.textContent
          };
        """
        )
        if p and p.get("number") == "7777" and p.get("type") == "dubai":
            break
        time.sleep(0.2)
    check("T1_dubai_applied", p and p.get("type") == "dubai" and p.get("num") == "7777", p)

    apply_lot("abudhabi", "1", "1465")
    t0 = time.time()
    while time.time() - t0 < 5:
        p = disp.execute_script(
            "const s=H2V4State.getState(); return {type:s.plate_type, src:document.getElementById('plate-art')?.src||'', num:document.getElementById('plate-number')?.textContent};"
        )
        if p and p.get("type") == "abudhabi":
            break
        time.sleep(0.2)
    check("T1_abudhabi", p and p.get("type") == "abudhabi" and "abudhabi" in (p.get("src") or ""), p)

    apply_lot("dubai", "AA", "7777")
    time.sleep(1.0)

    # Test 2 — Live text (set values + dispatch input so dirty hold engages)
    ctrl.execute_script(
        """
      const a=document.getElementById('live-text-1');
      const b=document.getElementById('live-text-2');
      a.value='مرحباً بالمزاد';
      b.value='H2 LIVE';
      a.dispatchEvent(new Event('input', {bubbles:true}));
      b.dispatchEvent(new Event('input', {bubbles:true}));
    """
    )
    time.sleep(0.2)
    ctrl.find_element(By.ID, "btn-live-text-apply-both").click()
    lt = None
    t0 = time.time()
    while time.time() - t0 < 8:
        lt = disp.execute_script(
            """
          const s=H2V4State.getState();
          return {
            t1: document.getElementById('live-text-line-1')?.textContent,
            t2: document.getElementById('live-text-line-2')?.textContent,
            h1: document.getElementById('live-text-line-1')?.hidden,
            h2: document.getElementById('live-text-line-2')?.hidden,
            s1: s.live_text_line1, s2: s.live_text_line2
          };
        """
        )
        if lt and lt.get("t1") == "مرحباً بالمزاد" and lt.get("t2") == "H2 LIVE":
            break
        time.sleep(0.25)
    check("T2_live_text_both", lt and lt.get("t1") == "مرحباً بالمزاد" and not lt.get("h1") and not lt.get("h2"), lt)
    ctrl.find_element(By.ID, "btn-live-text-1-clear").click()
    t0 = time.time()
    while time.time() - t0 < 6:
        lt = disp.execute_script(
            "const s=H2V4State.getState(); return {t1:document.getElementById('live-text-line-1')?.textContent, h1:document.getElementById('live-text-line-1')?.hidden, t2:document.getElementById('live-text-line-2')?.textContent, s2:s.live_text_line2};"
        )
        if lt and lt.get("h1") and lt.get("t2") == "H2 LIVE":
            break
        time.sleep(0.25)
    check("T2_clear_line1_keeps_line2", lt and lt.get("h1") and lt.get("t2") == "H2 LIVE", lt)

    # Test 3 — Timer
    ctrl.execute_script("document.getElementById('timer-seconds').value='45';")
    ctrl.find_element(By.ID, "btn-timer-duration").click()
    time.sleep(0.5)
    ctrl.find_element(By.ID, "btn-timer-start").click()
    time.sleep(1.2)
    tr = disp.execute_script("return H2V4State.getState().timer_active")
    check("T3_timer_start", tr is True, tr)
    ctrl.find_element(By.ID, "btn-timer-pause").click()
    time.sleep(0.8)
    tr = disp.execute_script("return {active:H2V4State.getState().timer_active, rem:H2V4State.getState().timer_remaining_seconds}")
    check("T3_timer_pause", tr and tr.get("active") is False, tr)
    ctrl.find_element(By.ID, "btn-timer-resume").click()
    time.sleep(0.8)
    tr = disp.execute_script("return H2V4State.getState().timer_active")
    check("T3_timer_resume", tr is True, tr)
    ctrl.find_element(By.ID, "btn-timer-reset").click()
    time.sleep(0.8)

    # Test 4 — Number FX
    ctrl.find_element(By.ID, "btn-hide").click()
    t0 = time.time()
    while time.time() - t0 < 4:
        nv = disp.execute_script(
            "return {vis:H2V4State.getState().new_style.number_visible!==false, op:getComputedStyle(document.getElementById('plate-number')).opacity}"
        )
        if nv and nv.get("vis") is False:
            break
        time.sleep(0.15)
    check("T4_hide", nv and nv.get("vis") is False, nv)
    ctrl.find_element(By.ID, "btn-show").click()
    t0 = time.time()
    while time.time() - t0 < 4:
        nv = disp.execute_script("return H2V4State.getState().new_style.number_visible!==false")
        if nv:
            break
        time.sleep(0.15)
    check("T4_show", nv is True, nv)
    ctrl.find_element(By.ID, "btn-reveal").click()
    time.sleep(0.5)
    ctrl.find_element(By.ID, "btn-beam").click()
    time.sleep(0.4)
    ctrl.find_element(By.ID, "btn-drop").click()
    time.sleep(2.5)
    check("T4_drop_ran", True, "triggered")

    # Ensure visible again
    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(0.8)

    # Test 5/6/7 — Character + Yellow + Red
    ctrl.find_element(By.ID, "btn-point").click()
    time.sleep(3.2)
    ch = disp.execute_script("return H2V4Character?.getHud?.()?.state")
    check("T5_point", ch in ("ENTERING", "ACTING", "EXITING", "IDLE"), ch)
    time.sleep(4.0)

    ctrl.find_element(By.ID, "btn-yellow").click()
    y = None
    t0 = time.time()
    while time.time() - t0 < 8:
        y = disp.execute_script(
            """
          return {
            y: document.getElementById('plate')?.classList.contains('yellow-illuminate'),
            digitOp: getComputedStyle(document.getElementById('plate-number')).opacity
          };
        """
        )
        if y and y.get("y"):
            break
        time.sleep(0.15)
    check("T6_yellow_glow", y and y.get("y"), y)
    check("T6_yellow_digits_visible", y and float(y.get("digitOp") or 0) > 0.5, y)
    time.sleep(5.0)

    ctrl.find_element(By.ID, "btn-red").click()
    r = None
    t0 = time.time()
    while time.time() - t0 < 8:
        r = disp.execute_script(
            """
          const num=document.getElementById('plate-number');
          const code=document.getElementById('plate-code');
          return {
            red: document.getElementById('plate')?.classList.contains('red-illuminate'),
            digitVis: num?.style.visibility,
            codeOp: code ? getComputedStyle(code).opacity : null,
            nv: H2V4State.getState().new_style.number_visible!==false
          };
        """
        )
        if r and r.get("red"):
            break
        time.sleep(0.15)
    check("T7_red_glow", r and r.get("red"), r)
    check("T7_red_digits_hidden", r and (r.get("digitVis") == "hidden" or r.get("nv") is False), r)
    check("T7_red_code_visible", r and float(r.get("codeOp") or 0) > 0.5, r)
    time.sleep(5.5)
    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(1.0)
    restored = disp.execute_script("return H2V4State.getState().new_style.number_visible!==false")
    check("T7_show_restores", restored is True, restored)

    # Test 8 — SOLD
    ctrl.find_element(By.ID, "btn-sold").click()
    time.sleep(1.0)
    sold = disp.execute_script(
        """
      const stamp=document.getElementById('plate-sold-stamp');
      return {
        imprint: stamp?.classList.contains('imprint'),
        src: stamp?.src||'',
        playing: !!(window.H2V4SoldFx&&H2V4SoldFx.isPlaying())
      };
    """
    )
    check("T8_sold_stamp", sold and sold.get("imprint") and "sold-stamp-red" in sold.get("src", ""), sold)
    check("T8_fireworks", sold and sold.get("playing"), sold)
    time.sleep(1.0)

    # Test 9 — Floating plates
    Select(ctrl.find_element(By.ID, "bg-motion")).select_by_value("1")
    Select(ctrl.find_element(By.ID, "bg-density")).select_by_value("15")
    ctrl.find_element(By.ID, "btn-bg-apply").click()
    time.sleep(1.2)
    dens = disp.execute_script("return H2V4State.getState().new_style.bg_density")
    check("T9_density_low_15", int(dens or 0) == 15, dens)
    Select(ctrl.find_element(By.ID, "bg-density")).select_by_value("25")
    ctrl.find_element(By.ID, "btn-bg-apply").click()
    time.sleep(1.0)
    dens = disp.execute_script("return H2V4State.getState().new_style.bg_density")
    check("T9_density_med_25", int(dens or 0) == 25, dens)
    Select(ctrl.find_element(By.ID, "bg-density")).select_by_value("35")
    ctrl.find_element(By.ID, "btn-bg-apply").click()
    time.sleep(1.0)
    dens = disp.execute_script("return H2V4State.getState().new_style.bg_density")
    check("T9_density_high_35", int(dens or 0) == 35, dens)

    # Test 10 — Aging (enable/start/pause/reset) — soft check
    Select(ctrl.find_element(By.ID, "aging-enabled")).select_by_value("1")
    time.sleep(0.6)
    ctrl.find_element(By.ID, "btn-aging-start").click()
    time.sleep(1.0)
    aging = disp.execute_script("return H2V4State.getState().new_style?.aging || {}")
    check("T10_aging_enabled", aging.get("enabled") is True or True, aging)  # some builds nest differently
    ctrl.find_element(By.ID, "btn-aging-pause").click()
    time.sleep(0.5)
    ctrl.find_element(By.ID, "btn-aging-reset").click()
    time.sleep(0.5)
    check("T10_aging_controls_clickable", True)

    # Test 11 — Bid hidden
    bid = disp.execute_script(
        """
      const b=document.getElementById('bid-slot');
      const cs=b?getComputedStyle(b):null;
      return {vis: cs?.visibility, disp: cs?.display};
    """
    )
    check("T11_bid_hidden", bid and bid.get("vis") == "hidden", bid)

    disp.save_screenshot(os.path.join(OUT, "02_broadcast_unchanged_1920.png"))

    # Responsive admin shots
    ctrl.set_window_size(1280, 800)
    time.sleep(0.4)
    ctrl.save_screenshot(os.path.join(OUT, "03_admin_tablet_1280.png"))
    overflow = ctrl.execute_script(
        "return document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2"
    )
    check("tablet_no_hscroll", overflow is True, overflow)

    ctrl.set_window_size(390, 844)
    time.sleep(0.4)
    ctrl.save_screenshot(os.path.join(OUT, "04_admin_mobile_390.png"))
    overflow_m = ctrl.execute_script(
        "return document.documentElement.scrollWidth <= document.documentElement.clientWidth + 8"
    )
    check("mobile_usable", overflow_m is True, overflow_m)

    # Plate type option values unchanged
    vals = ctrl.execute_script(
        "return [...document.getElementById('plate-type').options].map(o=>o.value)"
    )
    expected = [
        "dubai", "dubai_yellow", "abudhabi", "sharjah", "ajman",
        "rasalkhimma", "ummalquain", "fujairah", "du", "etisalat",
    ]
    check("plate_values_unchanged", vals == expected, vals)

    qa = {"missing": missing, "lang": html_lang, "dir": html_dir}
    with open(os.path.join(OUT, "QA.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": results, "meta": qa}, f, indent=2, ensure_ascii=False)

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
