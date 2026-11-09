"""Record real admin SOLD + Fireworks click — stage-visible celebration MP4."""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "sold-fireworks-visibility" / "sold-fireworks-visible-demo.mp4"
OUT.parent.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"
FPS = 12
PAGE_W, PAGE_H = 1920, 1080


def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={PAGE_W},{PAGE_H}")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": PAGE_W, "height": PAGE_H, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_admin(d):
    WebDriverWait(d, 25).until(lambda x: x.find_element(By.ID, "btn-sold"))
    WebDriverWait(d, 25).until(
        lambda x: x.execute_script(
            """
            try {
              const w = document.getElementById('preview').contentWindow;
              return !!(w && w.H2V4SoldFx && w.document.getElementById('stage-fw'));
            } catch (e) { return false; }
            """
        )
    )
    time.sleep(0.5)


def grab_stage(d) -> np.ndarray:
    png = d.get_screenshot_as_png()
    page = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    box = d.execute_script(
        """
        const stage = document.getElementById('preview').contentDocument.getElementById('stage');
        const r = stage.getBoundingClientRect();
        return {x:r.left,y:r.top,w:r.width,h:r.height};
        """
    )
    x, y, w, h = int(box["x"]), int(box["y"]), max(1, int(box["w"])), max(1, int(box["h"]))
    x = max(0, min(x, page.shape[1] - 1))
    y = max(0, min(y, page.shape[0] - 1))
    crop = page[y : y + h, x : x + w]
    return cv2.resize(crop, (1920, 1080), interpolation=cv2.INTER_AREA)


def main():
    d = make_driver()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(OUT), fourcc, FPS, (1920, 1080))
    try:
        d.get(f"{BASE}/admin.html?v=soldvisdemo2")
        wait_admin(d)
        d.execute_script(
            """
            try {
              const w = document.getElementById('preview').contentWindow;
              if (w.H2V4BgPlates?.setDensity) w.H2V4BgPlates.setDensity(4);
            } catch (e) {}
            """
        )
        for _ in range(int(FPS * 1.0)):
            writer.write(grab_stage(d))
            time.sleep(1 / FPS)

        d.find_element(By.ID, "btn-sold").click()
        t0 = time.time()
        while time.time() - t0 < 6.2:
            writer.write(grab_stage(d))
            time.sleep(1 / FPS)

        for _ in range(int(FPS * 0.6)):
            writer.write(grab_stage(d))
            time.sleep(1 / FPS)
    finally:
        writer.release()
        d.quit()
    print(str(OUT))


if __name__ == "__main__":
    main()
