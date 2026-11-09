"""Record a 1920x1080 MP4 walking through every H2 Live V4 sandbox feature."""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "feature-demo.mp4"
BASE = "http://127.0.0.1:8766"
FPS = 6


def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--window-size=1920,1080")
    opts.page_load_strategy = "eager"
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(20)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 15).until(
        lambda drv: drv.execute_script("return !!(window.H2V4State && window.H2PlateSystem);")
    )
    time.sleep(0.25)


def set_label(d, title: str, note: str = ""):
    d.execute_script(
        """
        let el = document.getElementById('demo-label');
        if (!el) {
          el = document.createElement('div');
          el.id = 'demo-label';
          el.style.cssText = 'position:absolute;left:24px;bottom:24px;z-index:200;'
            + 'padding:14px 18px;max-width:760px;font:700 28px Rajdhani,sans-serif;'
            + 'color:#f3e0a0;background:rgba(0,0,0,0.75);border:1px solid rgba(212,175,55,0.55);'
            + 'border-radius:10px;pointer-events:none;letter-spacing:0.04em;';
          document.getElementById('stage').appendChild(el);
        }
        el.innerHTML = `<div>${arguments[0]}</div>`
          + (arguments[1] ? `<div style="font:600 16px Cairo,sans-serif;opacity:.85;margin-top:6px">${arguments[1]}</div>` : '');
        """,
        title,
        note,
    )


def grab(d) -> np.ndarray:
    png = d.get_screenshot_as_png()
    arr = np.frombuffer(png, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr.shape[1] != 1920 or bgr.shape[0] != 1080:
        bgr = cv2.resize(bgr, (1920, 1080), interpolation=cv2.INTER_AREA)
    return bgr


def hold(writer, frame: np.ndarray, seconds: float):
    n = max(1, int(round(seconds * FPS)))
    for _ in range(n):
        writer.write(frame)


def burst(d, writer, seconds: float, samples: int = 4):
    """Grab a few live frames while FX plays, stretch to duration."""
    samples = max(1, samples)
    gap = max(0.05, seconds / samples)
    frames = []
    for _ in range(samples):
        frames.append(grab(d))
        time.sleep(gap)
    # write evenly to fill seconds
    total = max(1, int(round(seconds * FPS)))
    for i in range(total):
        writer.write(frames[min(len(frames) - 1, i * len(frames) // total)])


def log(msg: str):
    print(msg, flush=True)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(OUT), fourcc, FPS, (1920, 1080))
    if not writer.isOpened():
        raise RuntimeError("VideoWriter failed")

    d = make_driver()
    strip_frames = []
    try:
        log("open base")
        d.get(f"{BASE}/?v=demo")
        wait_ready(d)
        set_label(d, "1/12  BASE LAYOUT", "Brand · Timer · Plate · Bid · 1920×1080")
        f = grab(d)
        strip_frames.append(f)
        hold(writer, f, 1.6)

        types = [
            ("abudhabi", "AA", "1234", ""),
            ("dubai_yellow", "B", "55", ""),
            ("sharjah", "K", "99999", ""),
            ("ajman", "C", "7", ""),
            ("rasalkhimma", "R", "8888", ""),
            ("fujairah", "F", "4321", ""),
            ("ummalquain", "U", "2468", ""),
            ("du", "", "", "0501234567"),
            ("etisalat", "", "", "0569876543"),
            ("dubai", "AA", "7777", ""),
        ]
        for i, (ptype, code, number, phone) in enumerate(types, start=1):
            log(f"plate {ptype}")
            set_label(d, f"2/12  PLATE  {ptype.upper()}  ({i}/{len(types)})", "Native aspect + overlays")
            d.execute_script(
                "H2V4State.patch({plate_type:arguments[0], code:arguments[1], number:arguments[2], phone_number:arguments[3], new_style:{number_visible:true}});",
                ptype, code, number, phone,
            )
            time.sleep(0.2)
            f = grab(d)
            if i in (1, 8, 10):
                strip_frames.append(f)
            hold(writer, f, 0.85)

        log("hide/reveal")
        set_label(d, "3/12  NUMBER HIDE", "Conceal number region only")
        d.execute_script("H2V4State.patch({ns_hide_number:true});")
        time.sleep(0.15)
        hold(writer, grab(d), 1.1)
        set_label(d, "3/12  NUMBER REVEAL", "Reveal animation on number region")
        d.execute_script("H2V4State.patch({ns_replay_reveal:true});")
        burst(d, writer, 1.4, samples=5)

        log("beam")
        set_label(d, "4/12  LIGHT BEAM", "Plate-local orbit")
        d.execute_script("H2V4State.patch({ns_beam:true});")
        burst(d, writer, 2.0, samples=6)

        log("drop")
        set_label(d, "5/12  NUMBER DROP", "Digits only")
        d.execute_script("H2V4State.patch({ns_drop:true});")
        burst(d, writer, 1.3, samples=4)

        log("yellow")
        set_label(d, "6/12  YELLOW CARD", "Rim + shake (character WebM missing)")
        d.execute_script("H2V4State.patch({ns_char_yellow:true});")
        burst(d, writer, 1.6, samples=4)

        log("red")
        set_label(d, "7/12  RED CARD", "Number conceal; values unchanged")
        d.execute_script("H2V4State.patch({ns_char_red:true});")
        time.sleep(0.2)
        f = grab(d)
        strip_frames.append(f)
        hold(writer, f, 1.4)
        d.execute_script("H2V4State.patch({ns_show_number:true}); H2V4BeamDropFx.clearCardFx();")

        log("sold")
        set_label(d, "8/12  SOLD + FIREWORKS", "Imprint on plate · FW behind art")
        d.execute_script("H2V4State.patch({trigger_sold:true, sold_style:'fireworks'});")
        burst(d, writer, 2.6, samples=8)
        strip_frames.append(grab(d))

        log("aging")
        set_label(d, "9/12  AGING / BREAK", "Independent of timer · interim cracks")
        d.execute_script(
            """
            const fresh=50;
            H2V4State.patch({new_style:{aging:{
              fresh_delay_seconds:fresh, aging_duration_seconds:10,
              started_at:new Date(Date.now()-(fresh+8)*1000).toISOString(),
              paused:false, paused_elapsed_seconds:0
            }}});
            """
        )
        burst(d, writer, 2.2, samples=5)

        d.execute_script(
            "H2V4State.patch({ns_aging_reset:true}); H2V4SoldFx.clearSoldVisuals(); H2V4AgingFx.resetVisual();"
        )

        log("floats")
        set_label(d, "10/12  FLOATING LETTERS", "Corridor-only · alpha-keyed PNGs · motion ON")
        d.execute_script("H2V4State.patch({new_style:{bg_motion_enabled:true}});")
        time.sleep(0.8)  # allow sprites to build
        burst(d, writer, 2.2, samples=5)
        d.execute_script("H2V4State.patch({new_style:{bg_motion_enabled:false}});")

        log("character")
        set_label(d, "11/12  CHARACTER (INCOMPLETE)", "No WebM / measured meta — gated")
        d.execute_script("H2V4Character.play('point');")
        time.sleep(0.25)
        hold(writer, grab(d), 1.5)

        log("debug")
        d.get(f"{BASE}/?debug=1&v=demo")
        wait_ready(d)
        set_label(d, "12/12  DEBUG OVERLAY", "Boxes · stamp target · safezones")
        f = grab(d)
        strip_frames.append(f)
        hold(writer, f, 2.0)

        log("end")
        d.get(f"{BASE}/?v=end")
        wait_ready(d)
        set_label(
            d,
            "FEATURE DEMO COMPLETE",
            "All sandbox FX covered · Character assets still missing · No Phase 8 API",
        )
        hold(writer, grab(d), 2.0)

    finally:
        d.quit()
        writer.release()

    if strip_frames:
        picks = strip_frames[:6]
        while len(picks) < 6:
            picks.append(picks[-1])
        row = np.hstack([cv2.resize(f, (320, 180)) for f in picks])
        cv2.imwrite(str(ROOT / "refs" / "qa" / "feature-demo-strip.png"), row)

    mb = OUT.stat().st_size / (1024 * 1024)
    log(f"WROTE {OUT} ({mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
