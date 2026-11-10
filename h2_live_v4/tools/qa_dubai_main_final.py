"""E2E QA — final Dubai main plate image replacement."""
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
from PIL import Image  # noqa: E402

OUT = r"c:\Users\moham\h3\h2_live_v4\refs\qa\dubai_main_final"
os.makedirs(OUT, exist_ok=True)
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL"), name, detail if detail else "")


def main():
    s = LiveBroadcastSession.objects.get(pk=1)
    token = str(s.display_token)

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
      const art=document.getElementById('plate-art');
      const code=document.getElementById('plate-code');
      const num=document.getElementById('plate-number');
      const plate=document.getElementById('plate');
      const st=H2V4State.getState();
      const pr=plate.getBoundingClientRect();
      return {
        type: st.plate_type,
        src: art?.currentSrc||art?.src||'',
        codeText: code?.textContent,
        numText: num?.textContent,
        codeOp: code?getComputedStyle(code).opacity:null,
        numOp: num?getComputedStyle(num).opacity:null,
        digitVis: num?.style.visibility,
        aspect: pr.width/pr.height,
        natural: art?[art.naturalWidth, art.naturalHeight]:null,
        yellow: plate?.classList.contains('yellow-illuminate'),
        red: plate?.classList.contains('red-illuminate'),
        stampSrc: document.getElementById('plate-sold-stamp')?.src||'',
        imprint: document.getElementById('plate-sold-stamp')?.classList.contains('imprint'),
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

    def apply_lot(ptype, code, number):
        Select(ctrl.find_element(By.ID, "plate-type")).select_by_value(ptype)
        ctrl.find_element(By.ID, "code").clear()
        ctrl.find_element(By.ID, "code").send_keys(code)
        ctrl.find_element(By.ID, "number").clear()
        ctrl.find_element(By.ID, "number").send_keys(number)
        ctrl.find_element(By.ID, "btn-apply-lot").click()
        time.sleep(1.2)

    apply_lot("dubai", "AA", "7777")
    dubai = None
    t0 = time.time()
    while time.time() - t0 < 6:
        dubai = probe()
        if dubai and "dubai-main-final" in dubai.get("src", "") and dubai.get("numText") == "7777":
            break
        time.sleep(0.2)

    check("uses_final_png", dubai and "dubai-main-final.png" in dubai.get("src", ""), dubai.get("src") if dubai else None)
    check("not_old_main", dubai and "dubai-main.png" not in dubai.get("src", "").split("dubai-main-final")[0], dubai.get("src"))
    check("code_AA", dubai and dubai.get("codeText") == "AA", dubai)
    check("number_7777", dubai and dubai.get("numText") == "7777", dubai)
    check("overlays_visible", dubai and float(dubai.get("numOp") or 0) > 0.5 and float(dubai.get("codeOp") or 0) > 0.5, dubai)
    check("aspect_near_4734", dubai and abs((dubai.get("aspect") or 0) - 4.734) < 0.12, dubai.get("aspect") if dubai else None)

    disp.save_screenshot(os.path.join(OUT, "01_dubai_final_1920.png"))
    box = disp.execute_script(
        """
      const p=document.getElementById('plate').getBoundingClientRect();
      return {x:Math.max(0,p.left-36), y:Math.max(0,p.top-36), w:p.width+72, h:p.height+72};
    """
    )
    full = Image.open(os.path.join(OUT, "01_dubai_final_1920.png"))
    full.crop((int(box["x"]), int(box["y"]), int(box["x"] + box["w"]), int(box["y"] + box["h"]))).save(
        os.path.join(OUT, "02_dubai_final_closeup.png")
    )

    # Asset alpha corner check
    px = disp.execute_script(
        """
      const art=document.getElementById('plate-art');
      const c=document.createElement('canvas');
      c.width=art.naturalWidth; c.height=art.naturalHeight;
      const ctx=c.getContext('2d'); ctx.drawImage(art,0,0);
      const corner=ctx.getImageData(1,1,1,1).data;
      return {cornerA: corner[3], nw: art.naturalWidth, nh: art.naturalHeight};
    """
    )
    check("transparent_corner", px and px.get("cornerA", 255) < 20, px)

    apply_lot("abudhabi", "1", "1465")
    abu = None
    t0 = time.time()
    while time.time() - t0 < 5:
        abu = probe()
        if abu and abu.get("type") == "abudhabi":
            break
        time.sleep(0.2)
    check("abudhabi_unchanged", abu and "abudhabi" in abu.get("src", "") and "dubai-main-final" not in abu.get("src", ""), abu.get("src"))

    apply_lot("dubai", "AA", "7777")
    back = None
    t0 = time.time()
    while time.time() - t0 < 5:
        back = probe()
        if back and "dubai-main-final" in back.get("src", ""):
            break
        time.sleep(0.2)
    check("dubai_returns", back and "dubai-main-final" in back.get("src", ""), back.get("src") if back else None)

    apply_lot("dubai_yellow", "A", "1234")
    yel = None
    t0 = time.time()
    while time.time() - t0 < 5:
        yel = probe()
        if yel and yel.get("type") == "dubai_yellow":
            break
        time.sleep(0.2)
    check("dubai_yellow_unchanged", yel and "dubai_classic" in (yel.get("src") or ""), yel.get("src") if yel else None)

    apply_lot("dubai", "AA", "7777")
    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(0.8)

    ctrl.find_element(By.ID, "btn-yellow").click()
    y = None
    t0 = time.time()
    while time.time() - t0 < 8:
        y = probe()
        if y and y.get("yellow"):
            break
        time.sleep(0.15)
    check("yellow_works", y and y.get("yellow"), y)
    time.sleep(5.0)

    ctrl.find_element(By.ID, "btn-red").click()
    r = None
    t0 = time.time()
    while time.time() - t0 < 8:
        r = probe()
        if r and r.get("red"):
            break
        time.sleep(0.15)
    check("red_works", r and r.get("red") and r.get("digitVis") == "hidden", r)
    time.sleep(5.5)

    ctrl.find_element(By.ID, "btn-show").click()
    time.sleep(0.8)
    ctrl.find_element(By.ID, "btn-sold").click()
    time.sleep(1.0)
    sold = probe()
    check("sold_works", sold and sold.get("imprint") and "sold-stamp-red" in sold.get("stampSrc", ""), sold)
    disp.save_screenshot(os.path.join(OUT, "03_dubai_final_sold_1920.png"))

    with open(os.path.join(OUT, "QA.json"), "w", encoding="utf-8") as f:
        json.dump({"dubai": dubai, "abu": abu, "back": back, "yel": yel, "px": px}, f, indent=2)

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
