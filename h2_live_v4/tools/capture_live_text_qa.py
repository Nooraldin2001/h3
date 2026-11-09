"""Live Screen Text QA — admin apply + broadcast display screenshots."""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "live-screen-text"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def driver_at(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_admin(d):
    WebDriverWait(d, 25).until(lambda x: x.find_element(By.ID, "btn-live-text-1-apply"))
    WebDriverWait(d, 25).until(
        lambda x: x.execute_script(
            """
            try {
              const w = document.getElementById('preview').contentWindow;
              return !!(w && w.H2V4State && w.document.getElementById('live-text-line-1'));
            } catch (e) { return false; }
            """
        )
    )
    time.sleep(0.4)


def shot_full(d, path, w, h):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
            "fromSurface": True,
        },
    )
    Path(path).write_bytes(base64.b64decode(data["data"]))


def shot_stage(d, path, page_w, page_h):
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": page_w, "height": page_h, "scale": 1},
            "fromSurface": True,
        },
    )
    page = Image.open(io.BytesIO(base64.b64decode(data["data"]))).convert("RGB")
    box = d.execute_script(
        """
        const iframe = document.getElementById('preview');
        const ir = iframe.getBoundingClientRect();
        const stage = iframe.contentDocument.getElementById('stage');
        const sr = stage.getBoundingClientRect();
        return {x: ir.left + sr.left, y: ir.top + sr.top, w: sr.width, h: sr.height};
        """
    )
    x, y = max(0, int(box["x"])), max(0, int(box["y"]))
    w, h = max(1, int(box["w"])), max(1, int(box["h"]))
    crop = page.crop((x, y, min(page.width, x + w), min(page.height, y + h)))
    crop = crop.resize((1920, 1080), Image.Resampling.LANCZOS)
    crop.save(path)
    return crop


def live_state(d):
    return d.execute_script(
        """
        const w = document.getElementById('preview').contentWindow;
        const s = w.H2V4State.getState();
        const l1 = w.document.getElementById('live-text-line-1');
        const l2 = w.document.getElementById('live-text-line-2');
        const G = w.H2V4Geom;
        const box = (el) => el && !el.hidden ? G.elementStageBox(el) : null;
        return {
          state1: s.live_text_line1,
          state2: s.live_text_line2,
          dom1: l1 ? l1.textContent : null,
          dom2: l2 ? l2.textContent : null,
          hidden1: !l1 || l1.hidden,
          hidden2: !l2 || l2.hidden,
          box1: box(l1),
          box2: box(l2),
          brand: G.elementStageBox(w.document.querySelector('.brand-mark')),
          timer: G.elementStageBox(w.document.querySelector('.timer')),
          plate: G.elementStageBox(w.document.getElementById('plate')),
          price: s.price,
          timer_remaining: s.timer_remaining_seconds,
          number: s.number,
        };
        """
    )


def overlaps(a, b, pad=4):
    if not a or not b:
        return False
    return not (
        a["x"] + a["w"] + pad < b["x"]
        or b["x"] + b["w"] + pad < a["x"]
        or a["y"] + a["h"] + pad < b["y"]
        or b["y"] + b["h"] + pad < a["y"]
    )


def apply_line(d, n, text):
    inp = d.find_element(By.ID, f"live-text-{n}")
    inp.clear()
    inp.send_keys(text)
    d.find_element(By.ID, f"btn-live-text-{n}-apply").click()
    time.sleep(0.25)


def clear_line(d, n):
    d.find_element(By.ID, f"btn-live-text-{n}-clear").click()
    time.sleep(0.25)


def run_admin(tag, page_w, page_h, report):
    d = driver_at(page_w, page_h)
    case = {"tag": tag, "checks": {}}
    try:
        d.get(f"{BASE}/admin.html?v=livetext2")
        wait_admin(d)
        d.execute_script(
            """
            try {
              const w = document.getElementById('preview').contentWindow;
              if (w.H2V4BgPlates?.setDensity) w.H2V4BgPlates.setDensity(0);
              // clear any persisted text for clean start
              w.H2V4State.patch({ live_text_line1: '', live_text_line2: '' });
            } catch (e) {}
            """
        )
        time.sleep(0.2)

        shot_full(d, OUT / f"{tag}-00-admin-empty.png", page_w, page_h)
        shot_stage(d, OUT / f"{tag}-00-stage-empty.png", page_w, page_h)
        empty = live_state(d)
        case["checks"]["empty_hidden"] = empty["hidden1"] and empty["hidden2"]

        # Line 1 Arabic only
        apply_line(d, 1, "لوحة مميزة الليلة")
        shot_stage(d, OUT / f"{tag}-01-line1-ar.png", page_w, page_h)
        s1 = live_state(d)
        case["checks"]["line1_ar"] = (
            s1["state1"] == "لوحة مميزة الليلة"
            and s1["dom1"] == "لوحة مميزة الليلة"
            and not s1["hidden1"]
            and s1["hidden2"]
            and not overlaps(s1["box1"], s1["brand"])
            and not overlaps(s1["box1"], s1["timer"])
            and not overlaps(s1["box1"], s1["plate"])
        )

        # Line 2 English independently
        apply_line(d, 2, "H2 Auctions Live")
        shot_full(d, OUT / f"{tag}-02-admin-both.png", page_w, page_h)
        shot_stage(d, OUT / f"{tag}-02-stage-both.png", page_w, page_h)
        s2 = live_state(d)
        case["checks"]["both"] = (
            s2["state1"] == "لوحة مميزة الليلة"
            and s2["state2"] == "H2 Auctions Live"
            and not s2["hidden1"]
            and not s2["hidden2"]
            and s2["box1"]["y"] < s2["box2"]["y"] < s2["timer"]["y"]
            and s2["box1"]["y"] > s2["brand"]["y"]
        )

        # Mixed
        apply_line(d, 1, "Featured · مميزة")
        apply_line(d, 2, "Bidding now — المزايدة الآن")
        shot_stage(d, OUT / f"{tag}-03-mixed.png", page_w, page_h)
        sm = live_state(d)
        case["checks"]["mixed"] = (
            "Featured" in sm["dom1"] and "مميزة" in sm["dom1"] and not sm["hidden2"]
        )

        # Long text truncated to 100
        long = "A" * 120 + "لوحة"
        apply_line(d, 1, long)
        sl = live_state(d)
        case["checks"]["long_truncated"] = len(sl["state1"]) == 100 and len(sl["dom1"]) == 100

        # Clear line 1 only — line 2 remains
        apply_line(d, 2, "Still here")
        clear_line(d, 1)
        shot_stage(d, OUT / f"{tag}-04-line1-cleared.png", page_w, page_h)
        sc = live_state(d)
        case["checks"]["clear_line1_keeps_line2"] = (
            sc["hidden1"] and not sc["hidden2"] and sc["dom2"] == "Still here"
        )

        # Independence: auction data unchanged
        case["checks"]["auction_untouched"] = (
            sc["price"] == "1250000"
            and sc["number"] == "7777"
            and sc["timer_remaining"] == 60
        )

        # Persist across iframe reload
        apply_line(d, 1, "After refresh")
        apply_line(d, 2, "بعد التحديث")
        d.execute_script(
            """
            const f = document.getElementById('preview');
            f.src = './index.html?embed=1&t=' + Date.now();
            """
        )
        wait_admin(d)
        time.sleep(0.5)
        shot_stage(d, OUT / f"{tag}-05-after-reload.png", page_w, page_h)
        sr = live_state(d)
        case["checks"]["persist_reload"] = (
            sr["state1"] == "After refresh" and sr["state2"] == "بعد التحديث"
        )

        clear_line(d, 1)
        clear_line(d, 2)
        shot_stage(d, OUT / f"{tag}-06-cleared.png", page_w, page_h)

        case["all_ok"] = all(case["checks"].values())
    finally:
        d.quit()
    report["cases"][tag] = case
    return case


def run_direct_1280(report):
    d = driver_at(1280, 720)
    try:
        d.get(f"{BASE}/index.html?plate_type=dubai&code=AA&number=7777&v=livetext2")
        WebDriverWait(d, 20).until(
            lambda x: x.execute_script(
                "return !!(window.H2V4State && document.getElementById('live-text-line-1'));"
            )
        )
        time.sleep(0.4)
        d.execute_script(
            "H2V4State.patch({ live_text_line1: 'English Title', live_text_line2: 'عنوان عربي' });"
        )
        time.sleep(0.3)
        data = d.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "png",
                "clip": {"x": 0, "y": 0, "width": 1280, "height": 720, "scale": 1},
                "fromSurface": True,
            },
        )
        (OUT / "direct-1280-both.png").write_bytes(base64.b64decode(data["data"]))
        ok = d.execute_script(
            """
            const a = document.getElementById('live-text-line-1');
            const b = document.getElementById('live-text-line-2');
            return !a.hidden && !b.hidden && a.textContent === 'English Title'
              && b.textContent === 'عنوان عربي';
            """
        )
        report["cases"]["direct-1280"] = {"visible": bool(ok)}
    finally:
        d.quit()


def main():
    report = {"out": str(OUT), "cases": {}}
    c1 = run_admin("admin-1920", 1920, 1080, report)
    c2 = run_admin("admin-1600", 1600, 900, report)
    run_direct_1280(report)
    report["all_ok"] = bool(
        c1.get("all_ok") and c2.get("all_ok") and report["cases"]["direct-1280"].get("visible")
    )
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# Live Screen Text QA",
        "",
        f"**Result:** `{'PASS' if report['all_ok'] else 'FAIL'}`",
        "",
        f"- admin-1920: {c1.get('all_ok')} {c1.get('checks')}",
        f"- admin-1600: {c2.get('all_ok')} {c2.get('checks')}",
        f"- direct-1280: {report['cases']['direct-1280']}",
        "",
    ]
    (OUT / "LIVE_TEXT_QA.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"all_ok": report["all_ok"], "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
