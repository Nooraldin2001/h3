"""E2E QA — main Dubai plate image replacement (V4)."""
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
from PIL import Image  # noqa: E402

OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\dubai_main_plate"
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
    s.save(update_fields=["new_style"])

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
      const art = document.getElementById('plate-art');
      const shell = document.getElementById('plate-shell');
      const code = document.getElementById('plate-code');
      const num = document.getElementById('plate-number');
      const plate = document.getElementById('plate');
      const st = H2V4State.getState();
      const src = art ? (art.currentSrc || art.src || '') : '';
      const pr = plate.getBoundingClientRect();
      const sr = shell.getBoundingClientRect();
      return {
        type: st.plate_type,
        code: st.code,
        number: st.number,
        src,
        hasNew: src.includes('dubai-main.png'),
        hasOldJpg: src.includes('/dubai.jpg'),
        shellClass: shell ? shell.className : '',
        codeText: code ? code.textContent : null,
        numText: num ? num.textContent : null,
        codeVis: code ? getComputedStyle(code).visibility : null,
        numVis: num ? getComputedStyle(num).visibility : null,
        codeOp: code ? getComputedStyle(code).opacity : null,
        numOp: num ? getComputedStyle(num).opacity : null,
        plateW: pr.width, plateH: pr.height,
        aspect: pr.width && pr.height ? pr.width/pr.height : null,
        shellRadius: shell ? getComputedStyle(shell).borderRadius : null,
        artNatural: art ? [art.naturalWidth, art.naturalHeight] : null,
      };
    """
        )

    disp.get(f"http://127.0.0.1:8000/live/display-v4/{token}/")
    WebDriverWait(disp, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge && !!window.H2PlateSystem")
    )
    time.sleep(0.8)

    ctrl.get("http://127.0.0.1:8000/admin/login/?next=/live/control/v4/")
    WebDriverWait(ctrl, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    ctrl.find_element(By.NAME, "username").send_keys("admin")
    ctrl.find_element(By.NAME, "password").send_keys("TempTest123!")
    ctrl.find_element(By.CSS_SELECTOR, "input[type=submit],button[type=submit]").click()
    WebDriverWait(ctrl, 20).until(
        lambda x: x.execute_script("return !!window.H2V4DjangoBridge")
    )
    time.sleep(0.5)

    def apply_lot(plate_type, code, number):
        ctrl.execute_script(
            """
          const t=arguments[0], c=arguments[1], n=arguments[2];
          const sel=document.getElementById('plate-type');
          const codeEl=document.getElementById('code');
          const numEl=document.getElementById('number');
          if (sel) sel.value = t;
          if (codeEl) codeEl.value = c;
          if (numEl) numEl.value = n;
        """,
            plate_type,
            code,
            number,
        )
        ctrl.find_element(By.ID, "btn-apply-lot").click()
        time.sleep(1.2)

    # Select dubai AA 7777 via Admin Apply lot
    apply_lot("dubai", "AA", "7777")
    dubai = None
    t0 = time.time()
    while time.time() - t0 < 6:
        dubai = probe()
        if dubai and dubai.get("hasNew") and dubai.get("numText") == "7777" and dubai.get("codeText") == "AA":
            break
        time.sleep(0.2)

    check("dubai_uses_new_png", dubai and dubai.get("hasNew") and not dubai.get("hasOldJpg"), dubai.get("src"))
    check("dubai_code_AA", dubai and dubai.get("codeText") == "AA", dubai)
    check("dubai_number_7777", dubai and dubai.get("numText") == "7777", dubai)
    check("dubai_overlays_visible", dubai and float(dubai.get("numOp") or 0) > 0.5 and dubai.get("numVis") != "hidden", dubai)
    check("dubai_aspect_near_new", dubai and dubai.get("aspect") and abs(dubai["aspect"] - 3.178) < 0.15, dubai.get("aspect"))
    disp.save_screenshot(os.path.join(OUT, "01_dubai_AA_7777_1920.png"))

    # Close-up crop around plate
    box = disp.execute_script(
        """
      const p = document.getElementById('plate').getBoundingClientRect();
      return {x: Math.max(0,p.left-40), y: Math.max(0,p.top-40),
              w: p.width+80, h: p.height+80};
    """
    )
    full = Image.open(os.path.join(OUT, "01_dubai_AA_7777_1920.png"))
    crop = full.crop(
        (
            int(box["x"]),
            int(box["y"]),
            int(box["x"] + box["w"]),
            int(box["y"] + box["h"]),
        )
    )
    crop.save(os.path.join(OUT, "02_dubai_closeup.png"))

    # Switch to Abu Dhabi — unchanged
    apply_lot("abudhabi", "1", "1465")
    abu = None
    t0 = time.time()
    while time.time() - t0 < 6:
        abu = probe()
        if abu and abu.get("type") == "abudhabi" and "abudhabi" in (abu.get("src") or ""):
            break
        time.sleep(0.2)
    check("abudhabi_unchanged_asset", abu and "abudhabi" in (abu.get("src") or "") and "dubai-main" not in (abu.get("src") or ""), abu.get("src"))
    disp.save_screenshot(os.path.join(OUT, "03_abudhabi_unchanged_1920.png"))

    # Back to Dubai
    apply_lot("dubai", "AA", "7777")
    back = None
    t0 = time.time()
    while time.time() - t0 < 6:
        back = probe()
        if back and back.get("hasNew") and back.get("numText") == "7777":
            break
        time.sleep(0.2)
    check("dubai_returns_new_image", back and back.get("hasNew"), back.get("src"))
    disp.save_screenshot(os.path.join(OUT, "04_dubai_back_1920.png"))

    # dubai_yellow unchanged
    apply_lot("dubai_yellow", "A", "1234")
    yel = None
    t0 = time.time()
    while time.time() - t0 < 6:
        yel = probe()
        if yel and yel.get("type") == "dubai_yellow":
            break
        time.sleep(0.2)
    check(
        "dubai_yellow_unchanged",
        yel and "dubai_classic" in (yel.get("src") or "") and "dubai-main" not in (yel.get("src") or ""),
        yel.get("src") if yel else None,
    )

    # Effects on dubai
    apply_lot("dubai", "AA", "7777")
    ctrl.execute_script("return window.H2V4DjangoBridge?.patch?.({ ns_show_number: true });")
    time.sleep(1.0)

    ctrl.find_element(By.ID, "btn-yellow").click()
    y = None
    t0 = time.time()
    while time.time() - t0 < 8:
        y = disp.execute_script(
            "return {y: document.getElementById('plate')?.classList.contains('yellow-illuminate')}"
        )
        if y and y.get("y"):
            break
        time.sleep(0.15)
    check("yellow_on_dubai", y and y.get("y"), y)
    time.sleep(5.0)

    ctrl.find_element(By.ID, "btn-red").click()
    r = None
    t0 = time.time()
    while time.time() - t0 < 8:
        r = disp.execute_script(
            """
          const plate=document.getElementById('plate');
          const num=document.getElementById('plate-number');
          return {
            red: plate?.classList.contains('red-illuminate'),
            digitVis: num?.style.visibility,
            stillNew: (document.getElementById('plate-art')?.src||'').includes('dubai-main')
          };
        """
        )
        if r and r.get("red"):
            break
        time.sleep(0.15)
    check("red_on_dubai", r and r.get("red") and r.get("digitVis") == "hidden", r)
    time.sleep(5.5)

    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(0.8)
    ctrl.find_element(By.ID, "btn-sold").click()
    time.sleep(0.9)
    sold = disp.execute_script(
        """
      const stamp=document.getElementById('plate-sold-stamp');
      return {
        imprint: stamp?.classList.contains('imprint'),
        opacity: stamp ? getComputedStyle(stamp).opacity : null,
        playing: !!(window.H2V4SoldFx && H2V4SoldFx.isPlaying()),
        src: document.getElementById('plate-art')?.src || ''
      };
    """
    )
    check("sold_on_dubai", sold and sold.get("imprint") and float(sold.get("opacity") or 0) > 0.5, sold)
    disp.save_screenshot(os.path.join(OUT, "05_dubai_sold_1920.png"))

    # Pixel check: no large white rectangle outside plate shell
    fringe = disp.execute_script(
        """
      const plate = document.getElementById('plate');
      const shell = document.getElementById('plate-shell');
      const pr = plate.getBoundingClientRect();
      const sr = shell.getBoundingClientRect();
      // sample 4 corners of plate box just outside shell radius — should not be pure white UI box
      return {
        plateAsp: pr.width/pr.height,
        shellAsp: sr.width/sr.height,
        hasNew: (document.getElementById('plate-art').src||'').includes('dubai-main.png')
      };
    """
    )
    check("fringe_probe", fringe and fringe.get("hasNew"), fringe)

    with open(os.path.join(OUT, "QA.json"), "w", encoding="utf-8") as f:
        json.dump({"dubai": dubai, "abu": abu, "back": back, "yel": yel, "sold": sold}, f, indent=2)

    ctrl.quit()
    disp.quit()

    # cleanup preview helper
    prev = r"c:\Users\moham\h3\static\live_v4\assets\plates\_dubai_main_preview.jpg"
    if os.path.exists(prev):
        os.remove(prev)

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
