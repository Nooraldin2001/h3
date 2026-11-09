"""Record short MP4: Admin control drives Broadcast (same Chrome profile)."""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "page-separation"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES = OUT / "_demo_frames"
BASE = "http://127.0.0.1:8766"


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script("return !!(window.H2V4State && window.H2PlateSystem);")
    )


def wait_control(d):
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script("return !!document.getElementById('btn-sold');")
    )


def click(d, id_):
    d.find_element(By.ID, id_).click()


def main():
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--window-size=1920,1080")
    d = webdriver.Chrome(options=opts)

    frame_i = 0

    def grab():
        nonlocal frame_i
        d.save_screenshot(str(FRAMES / f"f{frame_i:04d}.png"))
        frame_i += 1

    try:
        d.get(f"{BASE}/index.html?v=demo1")
        wait_ready(d)
        broadcast = d.current_window_handle
        d.switch_to.new_window("window")
        control = d.current_window_handle
        d.get(f"{BASE}/control.html?v=demo1")
        wait_control(d)

        # Sequence on control, capture broadcast
        steps = [
            ("lot", None),
            ("text", None),
            ("timer", "btn-timer-start"),
            ("yellow", "btn-yellow"),
            ("reset", "btn-char-reset"),
            ("red", "btn-red"),
            ("reset2", "btn-char-reset"),
            ("show", "btn-show"),
            ("sold", "btn-sold"),
        ]

        d.switch_to.window(control)
        Select(d.find_element(By.ID, "plate-type")).select_by_value("dubai")
        d.find_element(By.ID, "code").clear()
        d.find_element(By.ID, "code").send_keys("AA")
        d.find_element(By.ID, "number").clear()
        d.find_element(By.ID, "number").send_keys("7777")
        click(d, "btn-apply-lot")
        d.find_element(By.ID, "live-text-1").clear()
        d.find_element(By.ID, "live-text-1").send_keys("H2 LIVE CONTROL")
        click(d, "btn-live-text-1-apply")

        for name, btn in steps:
            d.switch_to.window(control)
            if btn:
                click(d, btn)
            # Capture several broadcast frames for motion
            d.switch_to.window(broadcast)
            for _ in range(6):
                grab()
                time.sleep(0.18)
    finally:
        d.quit()

    mp4 = OUT / "admin-controls-broadcast-demo.mp4"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        try:
            import imageio_ffmpeg

            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg = None
    if ffmpeg:
        subprocess.check_call(
            [
                ffmpeg,
                "-y",
                "-framerate",
                "6",
                "-i",
                str(FRAMES / "f%04d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(mp4),
            ]
        )
        print(str(mp4))
    else:
        print("NO_FFMPEG")
        print(f"frames={FRAMES}")


if __name__ == "__main__":
    main()
