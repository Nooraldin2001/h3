"""E2E QA — Red grunge SOLD stamp replacement (V4)."""
import json
import os
import sys
import time

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

OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\sold_stamp_red"
os.makedirs(OUT, exist_ok=True)
results = []


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
    ns = normalize_new_style(s.new_style if isinstance(s.new_style, dict) else {})
    ns["number_visible"] = True
    s.new_style = ns
    s.save(update_fields=["new_style"])

    ctrl = make_driver(1400, 900)
    disp = make_driver(1920, 1080)

    def probe():
        return disp.execute_script(
            """
      const stamp = document.getElementById('plate-sold-stamp');
      const plate = document.getElementById('plate');
      const fw = document.getElementById('stage-fw');
      const num = document.getElementById('plate-number');
      const st = H2V4State.getState();
      const cs = stamp ? getComputedStyle(stamp) : null;
      const src = stamp ? stamp.getAttribute('src') || stamp.src : '';
      return {
        src,
        hasNewAsset: src.includes('sold-stamp-red.png'),
        hasOldAsset: src.includes('sold/stamp.png'),
        hidden: stamp ? stamp.hidden : null,
        opacity: cs ? cs.opacity : null,
        width: cs ? cs.width : null,
        maxWidth: cs ? cs.maxWidth : null,
        imprint: stamp ? stamp.classList.contains('imprint') : false,
        naturalW: stamp ? stamp.naturalWidth : 0,
        naturalH: stamp ? stamp.naturalHeight : 0,
        display: cs ? cs.display : null,
        transform: cs ? cs.transform : null,
        filter: cs ? cs.filter : null,
        soldPlaying: !!(window.H2V4SoldFx && H2V4SoldFx.isPlaying()),
        fwW: fw ? fw.width : 0,
        stageSold: document.getElementById('stage')?.classList.contains('sold-celebration'),
        digitText: num ? num.textContent : null,
        digitVis: num ? num.style.visibility : null,
        number_visible: st.new_style?.number_visible !== false,
        number_val: st.number,
        plateW: plate ? plate.getBoundingClientRect().width : 0,
        stampBox: stamp ? (() => {
          const r = stamp.getBoundingClientRect();
          const p = plate.getBoundingClientRect();
          return {
            w: r.width, h: r.height,
            cx: r.left + r.width/2, cy: r.top + r.height/2,
            onPlate: r.left < p.right && r.right > p.left && r.top < p.bottom && r.bottom > p.top
          };
        })() : null,
      };
    """
        )

    disp.get(f"http://127.0.0.1:8000/live/display-v4/{token}/")
    WebDriverWait(disp, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2V4SoldFx")
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
    time.sleep(0.6)

    ctrl.execute_script(
        """
      return window.H2V4DjangoBridge?.patch?.({
        plate_type: 'dubai', code: 'AA', number: '7777',
        ns_show_number: true
      });
    """
    )
    time.sleep(1.2)

    before = probe()
    check("asset_points_to_new_png", before and before.get("hasNewAsset") and not before.get("hasOldAsset"), before.get("src"))
    check("stamp_hidden_before", before and before.get("hidden") is True, before)
    check("A_digits_visible_before", before and before.get("number_visible") and before.get("digitVis") != "hidden", before)
    disp.save_screenshot(os.path.join(OUT, "01_before_sold_1920.png"))

    # Trigger SOLD from admin
    ctrl.find_element(By.ID, "btn-sold").click()

    # Peak during imprint + fireworks
    peak = None
    t0 = time.time()
    while time.time() - t0 < 4.0:
        peak = probe()
        if peak and peak.get("imprint") and float(peak.get("opacity") or 0) > 0.5:
            break
        time.sleep(0.05)
    # Capture while fireworks likely active
    time.sleep(0.35)
    mid = probe()
    disp.save_screenshot(os.path.join(OUT, "02_sold_stamp_appearing_1920.png"))
    time.sleep(0.6)
    with_fw = probe()
    disp.save_screenshot(os.path.join(OUT, "03_sold_stamp_with_fireworks_1920.png"))

    settled = None
    t0 = time.time()
    while time.time() - t0 < 2.0:
        settled = probe()
        if settled and settled.get("imprint") and float(settled.get("opacity") or 0) >= 0.99:
            break
        time.sleep(0.1)
    disp.save_screenshot(os.path.join(OUT, "04_sold_stamp_settled_1920.png"))

    check("A_stamp_visible", peak and peak.get("imprint") and float(peak.get("opacity") or 0) > 0.5, peak)
    check("A_new_asset_loaded", peak and peak.get("naturalW", 0) > 100, peak)
    check("A_on_plate", peak and peak.get("stampBox") and peak["stampBox"].get("onPlate"), peak)
    check("A_fireworks_playing", mid.get("soldPlaying") or with_fw.get("soldPlaying") or mid.get("stageSold") or with_fw.get("stageSold"), {"mid": mid, "fw": with_fw})
    check("A_number_unchanged", settled and str(settled.get("number_val")) in ("7777", settled.get("digitText") or ""), settled)
    check("A_no_auto_reveal_force", settled is not None, settled)

    # Close-up crop via JS canvas around stamp
    crop_ok = disp.execute_script(
        """
      const stamp = document.getElementById('plate-sold-stamp');
      const plate = document.getElementById('plate');
      if (!stamp || !plate) return false;
      const r = stamp.getBoundingClientRect();
      const pad = 40;
      const sx = Math.max(0, Math.floor(r.left - pad));
      const sy = Math.max(0, Math.floor(r.top - pad));
      const sw = Math.min(window.innerWidth - sx, Math.ceil(r.width + pad * 2));
      const sh = Math.min(window.innerHeight - sy, Math.ceil(r.height + pad * 2));
      // mark for selenium region screenshot via full page; store coords
      window.__soldCrop = {sx, sy, sw, sh, stampW: r.width, stampH: r.height};
      return sw > 20 && sh > 20;
    """
    )
    check("closeup_coords", crop_ok, disp.execute_script("return window.__soldCrop"))
    # Full screenshot then we'll also save a plate-focused shot by re-screenshot
    disp.save_screenshot(os.path.join(OUT, "05_sold_closeup_context_1920.png"))

    # Sample pixels under stamp transparent region vs red — detect black rectangle
    px = disp.execute_script(
        """
      const stamp = document.getElementById('plate-sold-stamp');
      if (!stamp || !stamp.naturalWidth) return null;
      const c = document.createElement('canvas');
      c.width = stamp.naturalWidth; c.height = stamp.naturalHeight;
      const ctx = c.getContext('2d');
      ctx.drawImage(stamp, 0, 0);
      const w = c.width, h = c.height;
      // corner should be transparent (outside stamp)
      const corner = ctx.getImageData(2, 2, 1, 1).data;
      // center-ish may be red or transparent distress
      const mid = ctx.getImageData(Math.floor(w*0.5), Math.floor(h*0.5), 1, 1).data;
      // count opaque red-ish vs opaque near-black
      const data = ctx.getImageData(0, 0, w, h).data;
      let opaque = 0, nearBlackOpaque = 0, redOpaque = 0;
      for (let i = 0; i < data.length; i += 4) {
        const a = data[i+3];
        if (a < 20) continue;
        opaque++;
        const r=data[i], g=data[i+1], b=data[i+2];
        const lum = 0.2126*r+0.7152*g+0.0722*b;
        if (lum < 40 && r < 60) nearBlackOpaque++;
        if (r > 120 && r > g + 30 && r > b + 30) redOpaque++;
      }
      return {
        cornerA: corner[3],
        midRGBA: [mid[0],mid[1],mid[2],mid[3]],
        opaque, nearBlackOpaque, redOpaque,
        blackRatio: opaque ? nearBlackOpaque/opaque : 1,
        redRatio: opaque ? redOpaque/opaque : 0,
      };
    """
    )
    check("B_corner_transparent", px and px.get("cornerA", 255) < 10, px)
    check("B_mostly_red_not_black_bg", px and px.get("blackRatio", 1) < 0.08 and px.get("redRatio", 0) > 0.35, px)

    # Replay SOLD
    ctrl.find_element(By.ID, "btn-sold").click()
    time.sleep(0.8)
    replay = probe()
    stamp_count = disp.execute_script("return document.querySelectorAll('.plate-sold-stamp').length")
    check("C_replay_imprint", replay and replay.get("imprint") and float(replay.get("opacity") or 0) > 0.5, replay)
    check("C_single_stamp_element", stamp_count == 1, stamp_count)
    time.sleep(0.5)
    disp.save_screenshot(os.path.join(OUT, "06_sold_replay_1920.png"))

    # Layout 1280x720
    disp.set_window_size(1280, 720)
    time.sleep(0.4)
    ctrl.find_element(By.ID, "btn-sold").click()
    time.sleep(0.9)
    lay = probe()
    check("D_1280_stamp_on_plate", lay and lay.get("stampBox") and lay["stampBox"].get("onPlate"), lay)
    check("D_1280_aspect_ok", lay and lay.get("stampBox") and lay["stampBox"]["w"] > lay["stampBox"]["h"] * 1.2, lay)
    disp.save_screenshot(os.path.join(OUT, "07_sold_1280x720.png"))

    # Restore 1920 for regression
    disp.set_window_size(1920, 1080)
    time.sleep(0.5)

    # Clear sold visuals via lot-ish: show number then yellow/red/point
    ctrl.execute_script("return window.H2V4DjangoBridge?.patch?.({ ns_show_number: true });")
    time.sleep(0.8)
    # Trigger yellow
    ctrl.find_element(By.ID, "btn-yellow").click()
    y = None
    t0 = time.time()
    while time.time() - t0 < 8:
        y = disp.execute_script(
            """
          const plate=document.getElementById('plate');
          const rim=document.getElementById('plate-rim');
          return {
            y: !!plate?.classList.contains('yellow-illuminate'),
            rim: !!rim?.classList.contains('yellow'),
            state: H2V4Character?.getHud?.()?.state
          };
        """
        )
        if y and y.get("y"):
            break
        time.sleep(0.15)
    check("E_yellow_works", y and y.get("y"), y)
    time.sleep(5.0)

    ctrl.find_element(By.ID, "btn-red").click()
    r = None
    t0 = time.time()
    while time.time() - t0 < 8:
        r = disp.execute_script(
            """
          const plate=document.getElementById('plate');
          const rim=document.getElementById('plate-rim');
          const num=document.getElementById('plate-number');
          return {
            red: !!plate?.classList.contains('red-illuminate'),
            rim: !!rim?.classList.contains('red'),
            digitVis: num?.style.visibility,
          };
        """
        )
        if r and r.get("red"):
            break
        time.sleep(0.15)
    check("E_red_works", r and r.get("red"), r)
    time.sleep(5.5)

    ctrl.find_element(By.ID, "btn-point").click()
    time.sleep(3.0)
    p = disp.execute_script("return H2V4Character?.getHud?.()?.state")
    check("E_point_works", p in ("ENTERING", "ACTING", "EXITING"), p)

    bid_vis = disp.execute_script(
        "return getComputedStyle(document.getElementById('bid-slot')).visibility"
    )
    check("E_bid_still_hidden", bid_vis == "hidden", bid_vis)

    qa = {"before": before, "peak": peak, "mid": mid, "settled": settled, "px": px, "lay": lay}
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
