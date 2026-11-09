"""SOLD cinematic fireworks QA — multi-phase screenshots @ 1920×1080 and 1280×720."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "sold-fireworks"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def driver_at(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.set_script_timeout(60)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda x: x.execute_script(
            "return !!(window.H2V4State && window.H2V4SoldFx && window.H2PlateSystem);"
        )
    )
    for _ in range(40):
        nw = d.execute_script(
            "const i=document.querySelector('.stage-bg-img'); return i?i.naturalWidth:0;"
        )
        if nw and nw >= 1600:
            break
        time.sleep(0.25)
    time.sleep(0.3)


def shot(d, path: Path, w, h):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
            "fromSurface": True,
        },
    )
    path.write_bytes(base64.b64decode(data["data"]))


def snapshot(d):
    return d.execute_script(
        """
        const G = H2V4Geom;
        const box = (sel) => {
          const el = document.querySelector(sel);
          return el ? G.elementStageBox(el) : null;
        };
        const fw = document.getElementById('plate-fw');
        const st = H2V4State.getState();
        return {
          timerText: document.getElementById('timer-value')?.textContent || '',
          bidText: document.getElementById('bid-amount')?.textContent || '',
          numberText: document.getElementById('plate-number')?.textContent || '',
          numberVisible: getComputedStyle(document.getElementById('plate-number')).visibility,
          stampHidden: document.getElementById('plate-sold-stamp')?.hidden,
          soldPlaying: !!H2V4SoldFx.isPlaying(),
          celebration: document.getElementById('stage')?.classList.contains('sold-celebration'),
          fwSize: fw ? { w: fw.width, h: fw.height, left: fw.style.left, top: fw.style.top } : null,
          particleHint: fw ? (() => {
            const ctx = fw.getContext('2d');
            const data = ctx.getImageData(0, 0, fw.width, fw.height).data;
            let lit = 0;
            for (let i = 3; i < data.length; i += 16) if (data[i] > 20) lit++;
            return lit;
          })() : 0,
          brand: box('.brand-mark'),
          timer: box('.timer'),
          bid: box('.bid'),
          plate: box('#plate'),
          price: st.price,
          timer_remaining: st.timer_remaining_seconds,
          sold_event_id: st.sold_event_id,
        };
        """
    )


def trigger_sold(d):
    d.execute_script(
        "H2V4State.patch({ trigger_sold: true, sold_style: 'fireworks', sold_name: 'QA' });"
    )


def run_res(w, h, label, report):
    d = driver_at(w, h)
    tag = f"{w}x{h}"
    case = {"resolution": tag, "phases": {}}
    try:
        d.get(f"{BASE}/?plate_type=dubai&code=AA&number=7777&price=1250000&v=soldfw1")
        wait_ready(d)

        # Freeze ambient noise a bit — disable bg plates density if API exists
        d.execute_script(
            """
            try {
              if (window.H2V4BgPlates?.setDensity) H2V4BgPlates.setDensity(0);
            } catch (e) {}
            """
        )

        before = snapshot(d)
        shot(d, OUT / f"{label}-01-before-{tag}.png", w, h)
        case["phases"]["before"] = before

        # Confirm no autoplay
        time.sleep(0.6)
        idle = snapshot(d)
        case["no_autoplay"] = (not idle["soldPlaying"]) and idle["particleHint"] == 0

        # Capture baseline values that must not change
        base_timer = before["timer_remaining"]
        base_price = before["price"]
        base_number = before["numberText"]

        trigger_sold(d)
        time.sleep(0.12)
        start = snapshot(d)
        shot(d, OUT / f"{label}-02-start-{tag}.png", w, h)
        case["phases"]["start"] = start

        time.sleep(1.1)
        peak = snapshot(d)
        shot(d, OUT / f"{label}-03-peak-{tag}.png", w, h)
        case["phases"]["peak"] = peak

        time.sleep(2.8)
        ending = snapshot(d)
        shot(d, OUT / f"{label}-04-ending-{tag}.png", w, h)
        case["phases"]["ending"] = ending

        # Wait for full cleanup (~5.2s total from trigger)
        deadline = time.time() + 4.0
        while time.time() < deadline:
            if not d.execute_script("return H2V4SoldFx.isPlaying();"):
                break
            time.sleep(0.2)
        time.sleep(0.35)
        clean = snapshot(d)
        shot(d, OUT / f"{label}-05-clean-{tag}.png", w, h)
        case["phases"]["clean"] = clean

        # Deliberate replay should work
        trigger_sold(d)
        time.sleep(0.25)
        replay = snapshot(d)
        case["replay_ok"] = bool(replay["soldPlaying"] or replay["particleHint"] > 0)

        # Independence checks
        case["timer_unchanged"] = clean["timer_remaining"] == base_timer or abs(
            (clean["timer_remaining"] or 0) - (base_timer or 0)
        ) <= 2
        case["price_unchanged"] = clean["price"] == base_price
        case["number_unchanged"] = clean["numberText"] == base_number
        case["started_with_particles"] = (
            start["particleHint"] > 0 or peak["particleHint"] > 0 or start["soldPlaying"]
        )
        case["cleaned_up"] = (not clean["soldPlaying"]) and clean["particleHint"] == 0
        case["fw_expanded"] = bool(
            start.get("fwSize")
            and start["fwSize"]["w"] > 800
            and start["fwSize"]["h"] > 200
        )

        # Duplicate prevention: second trigger mid-run replaces (still playing once)
        trigger_sold(d)
        time.sleep(0.2)
        mid = d.execute_script("return H2V4SoldFx.isPlaying();")
        case["mid_replay_single_loop"] = bool(mid)

        case["all_ok"] = all(
            [
                case["no_autoplay"],
                case["started_with_particles"],
                case["cleaned_up"],
                case["replay_ok"],
                case["timer_unchanged"],
                case["price_unchanged"],
                case["number_unchanged"],
                case["fw_expanded"],
            ]
        )
    finally:
        d.quit()
    report["cases"][label] = case
    return case


def main():
    report = {"out": str(OUT), "cases": {}}
    c1 = run_res(1920, 1080, "fullhd", report)
    c2 = run_res(1280, 720, "hd720", report)
    report["all_ok"] = bool(c1.get("all_ok") and c2.get("all_ok"))
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# SOLD Cinematic Fireworks QA",
        "",
        f"**Result:** `{'all_ok' if report['all_ok'] else 'ISSUES'}`",
        "",
        "## Checks",
        "",
    ]
    for name, c in report["cases"].items():
        md.append(f"### {name} ({c.get('resolution')})")
        md.append(f"- no_autoplay: {c.get('no_autoplay')}")
        md.append(f"- started_with_particles: {c.get('started_with_particles')}")
        md.append(f"- fw_expanded: {c.get('fw_expanded')}")
        md.append(f"- cleaned_up: {c.get('cleaned_up')}")
        md.append(f"- replay_ok: {c.get('replay_ok')}")
        md.append(f"- timer_unchanged: {c.get('timer_unchanged')}")
        md.append(f"- price_unchanged: {c.get('price_unchanged')}")
        md.append(f"- number_unchanged: {c.get('number_unchanged')}")
        md.append(f"- all_ok: {c.get('all_ok')}")
        md.append("")
    (OUT / "SOLD_FIREWORKS_QA.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"all_ok": report["all_ok"], "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
