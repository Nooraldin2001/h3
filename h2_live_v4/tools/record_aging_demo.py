"""Short aging demo strip + mp4 (stage seeks, not real-time 60s)."""
from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "aging"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"

# Normalized progress keyframes for a ~6s paced demo
KEYS = [
    0.0,
    50 / 60,
    51.5 / 60,
    53 / 60,
    54.5 / 60,
    56 / 60,
    57.5 / 60,
    59 / 60,
    59.5 / 60,
    1.0,
    1.0,
]


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--window-size=1920,1080")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
    )
    frames = []
    try:
        d.get(f"{BASE}/?v=agingdemo")
        WebDriverWait(d, 20).until(
            lambda drv: drv.execute_script("return !!(window.H2V4AgingFx && window.H2V4State);")
        )
        time.sleep(0.4)
        d.execute_script("H2V4AgingFx.enable(); H2V4AgingFx.setDuration(60);")
        for i, p in enumerate(KEYS):
            d.execute_script("H2V4AgingFx.seekProgress(arguments[0], {freeze:true});", p)
            time.sleep(0.12)
            png = d.get_screenshot_as_png()
            fp = OUT / f"demo-frame-{i:02d}.png"
            fp.write_bytes(png)
            frames.append(fp)
            print("frame", i, p)
    finally:
        d.quit()

    # Build strip + mp4 if pillow/opencv available
    try:
        from PIL import Image

        imgs = [Image.open(f).convert("RGB") for f in frames]
        # contact strip
        tw = sum(im.width // 4 for im in imgs)
        th = imgs[0].height // 4
        strip = Image.new("RGB", (tw, th), (5, 6, 10))
        x = 0
        for im in imgs:
            sm = im.resize((im.width // 4, im.height // 4))
            strip.paste(sm, (x, 0))
            x += sm.width
        strip_path = OUT / "aging-demo-strip.png"
        strip.save(strip_path)
        print("strip", strip_path)

        # gif / mp4 via imageio if present
        try:
            import imageio.v2 as imageio
            import numpy as np

            seq = [np.array(im.resize((960, 540))) for im in imgs]
            mp4 = OUT / "aging-demo.mp4"
            imageio.mimsave(mp4, seq, fps=2)
            print("mp4", mp4)
        except Exception as e:
            # fallback gif
            gif = OUT / "aging-demo.gif"
            imgs[0].resize((960, 540)).save(
                gif,
                save_all=True,
                append_images=[im.resize((960, 540)) for im in imgs[1:]],
                duration=500,
                loop=0,
            )
            print("gif", gif, "(mp4 skipped:", e, ")")
    except Exception as e:
        print("media build skipped:", e)


if __name__ == "__main__":
    main()
