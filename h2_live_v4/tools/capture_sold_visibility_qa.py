"""
SOLD fireworks VISIBILITY QA — real admin button + rendered screenshot diffs.

PASS only when peak frames show obvious gold fireworks in stage zones
outside the opaque plate (not merely JS particle counts).
"""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "refs" / "qa" / "sold-fireworks-visibility"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"


def driver_at(w, h):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.set_script_timeout(90)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_admin(d):
    WebDriverWait(d, 25).until(lambda x: x.find_element(By.ID, "btn-sold"))
    WebDriverWait(d, 25).until(
        lambda x: x.execute_script(
            """
            try {
              const w = document.getElementById('preview').contentWindow;
              return !!(w && w.H2V4State && w.H2V4SoldFx
                        && w.document.getElementById('stage-fw'));
            } catch (e) { return false; }
            """
        )
    )
    for _ in range(50):
        nw = d.execute_script(
            """
            try {
              const i = document.getElementById('preview').contentDocument
                .querySelector('.stage-bg-img');
              return i ? i.naturalWidth : 0;
            } catch (e) { return 0; }
            """
        )
        if nw and nw >= 1600:
            break
        time.sleep(0.2)
    time.sleep(0.35)


def stage_rect_in_page(d):
    """Stage box in top-level page coordinates (iframe offset + inner rect)."""
    return d.execute_script(
        """
        const iframe = document.getElementById('preview');
        const ir = iframe.getBoundingClientRect();
        const stage = iframe.contentDocument.getElementById('stage');
        const sr = stage.getBoundingClientRect();
        return {
          x: ir.left + sr.left,
          y: ir.top + sr.top,
          w: sr.width,
          h: sr.height,
        };
        """
    )


def shot_stage(d, path: Path, page_w: int, page_h: int) -> Image.Image:
    """Capture only the stage region (fast clip) — not the full admin chrome."""
    box = stage_rect_in_page(d)
    x = max(0, int(round(box["x"])))
    y = max(0, int(round(box["y"])))
    w = max(64, int(round(box["w"])))
    h = max(64, int(round(box["h"])))
    # Keep clip inside page
    w = min(w, max(64, page_w - x))
    h = min(h, max(64, page_h - y))
    data = d.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "clip": {"x": x, "y": y, "width": w, "height": h, "scale": 1},
            "fromSurface": True,
            "captureBeyondViewport": True,
        },
    )
    crop = Image.open(io.BytesIO(base64.b64decode(data["data"]))).convert("RGB")
    crop = crop.resize((1920, 1080), Image.Resampling.LANCZOS)
    crop.save(path)
    return crop


def fw_canvas_gold(d) -> int:
    """Count non-transparent lit pixels on #stage-fw (fireworks layer only)."""
    b64 = d.execute_script(
        """
        const fw = document.getElementById('preview').contentDocument.getElementById('stage-fw');
        return fw.toDataURL('image/png').split(',')[1];
        """
    )
    im = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
    a = np.asarray(im)
    # lit = alpha > 20 and warm
    r, g, b, al = a[:, :, 0], a[:, :, 1], a[:, :, 2], a[:, :, 3]
    lit = (al > 20) & (r.astype(int) + g.astype(int) > 120)
    return int(lit.sum())


def gold_mask(arr: np.ndarray) -> np.ndarray:
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    bright = (r + g) > 200
    goldish = (r > 130) & (g > 95) & (r >= g - 30) & (r > b + 30) & (g > b + 10)
    white_gold = (r > 200) & (g > 180) & (b > 100) & (b < 215) & ((r + g) > 400)
    return (bright & goldish) | white_gold


def zone_counts(img: Image.Image) -> dict:
    arr = np.asarray(img)
    h, w = arr.shape[:2]
    zones = {
        "upper_left": (0, int(h * 0.05), int(w * 0.38), int(h * 0.45)),
        "upper_right": (int(w * 0.62), int(h * 0.05), w, int(h * 0.45)),
        "mid_left": (0, int(h * 0.28), int(w * 0.30), int(h * 0.65)),
        "mid_right": (int(w * 0.70), int(h * 0.28), w, int(h * 0.65)),
    }
    out = {}
    total = 0
    for name, (x0, y0, x1, y1) in zones.items():
        m = gold_mask(arr[y0:y1, x0:x1])
        c = int(m.sum())
        out[name] = c
        total += c
    out["zones_total"] = total
    out["full_gold"] = int(gold_mask(arr).sum())
    return out


def diff_stats(before: Image.Image, peak: Image.Image) -> dict:
    a = np.asarray(before).astype(np.int16)
    b = np.asarray(peak).astype(np.int16)
    d = np.abs(a - b).sum(axis=2)
    changed = d > 35
    h, w = changed.shape
    return {
        "mean_abs_diff": float(d.mean()),
        "changed_px": int(changed.sum()),
        "changed_left": int(changed[:, : int(w * 0.35)].sum()),
        "changed_right": int(changed[:, int(w * 0.65) :].sum()),
        "changed_upper": int(changed[: int(h * 0.45), :].sum()),
        "changed_frac": float(changed.mean()),
    }


def click_sold(d):
    d.find_element(By.ID, "btn-sold").click()


def wait_until_idle(d, timeout=8.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        playing = d.execute_script(
            "return document.getElementById('preview').contentWindow.H2V4SoldFx.isPlaying();"
        )
        if not playing:
            return True
        time.sleep(0.15)
    return False


def run_admin(label: str, page_w: int, page_h: int, report: dict):
    d = driver_at(page_w, page_h)
    case = {"label": label, "page": f"{page_w}x{page_h}", "phases": {}}
    try:
        d.get(f"{BASE}/admin.html?v=soldvis3")
        wait_admin(d)
        d.execute_script(
            """
            try {
              const w = document.getElementById('preview').contentWindow;
              if (w.H2V4BgPlates?.setDensity) w.H2V4BgPlates.setDensity(0);
            } catch (e) {}
            """
        )
        time.sleep(0.25)

        before = shot_stage(d, OUT / f"{label}-00-before.png", page_w, page_h)
        zb = zone_counts(before)
        fw0 = fw_canvas_gold(d)
        case["phases"]["0.0_before"] = {"gold": zb, "fw_lit": fw0}

        click_sold(d)
        t_click = time.time()

        playing = d.execute_script(
            "return document.getElementById('preview').contentWindow.H2V4SoldFx.isPlaying();"
        )
        stage_fw = d.execute_script(
            """
            const fw = document.getElementById('preview').contentDocument.getElementById('stage-fw');
            const cs = getComputedStyle(fw);
            const stack = getComputedStyle(
              document.getElementById('preview').contentDocument.querySelector('.stack')
            );
            return {
              w: fw.width, h: fw.height, z: cs.zIndex, opacity: cs.opacity,
              display: cs.display, visibility: cs.visibility,
              parent: fw.parentElement && fw.parentElement.id,
              stackZ: stack.zIndex,
            };
            """
        )
        case["pipeline"] = {
            "button": "btn-sold",
            "playing_after_click": bool(playing),
            "stage_fw": stage_fw,
        }

        # Timed captures — grab closest frame after each mark (fast path)
        schedule = [
            (0.35, "05-rockets"),
            (1.2, "15-explosions"),
            (2.2, "25-peak"),
            (4.2, "45-fading"),
        ]
        peak_img = before
        peak_score = -1
        for sec, name in schedule:
            while time.time() - t_click < sec:
                time.sleep(0.01)
            img = shot_stage(d, OUT / f"{label}-{name}.png", page_w, page_h)
            z = zone_counts(img)
            fw = fw_canvas_gold(d)
            case["phases"][f"{sec}_{name}"] = {
                "gold": z,
                "fw_lit": fw,
                "t": time.time() - t_click,
            }
            score = z["zones_total"] + fw * 0.15
            if score > peak_score:
                peak_score = score
                peak_img = img

        # Wait for natural end then clean shot
        idle = wait_until_idle(d, timeout=10.0)
        time.sleep(0.2)
        clean = shot_stage(d, OUT / f"{label}-60-clean.png", page_w, page_h)
        zc = zone_counts(clean)
        fw_clean = fw_canvas_gold(d)
        case["phases"]["clean"] = {"gold": zc, "fw_lit": fw_clean, "idle": idle}

        ds = diff_stats(before, peak_img)
        zg_before = zb["zones_total"]
        zg_peak = zone_counts(peak_img)["zones_total"]
        gold_delta = zg_peak - zg_before
        fw_peak = max(
            (p.get("fw_lit") or 0)
            for k, p in case["phases"].items()
            if k != "0.0_before" and k != "clean"
        )

        case["diff"] = ds
        case["gold_before_zones"] = zg_before
        case["gold_peak_zones"] = zg_peak
        case["gold_delta"] = gold_delta
        case["fw_lit_before"] = fw0
        case["fw_lit_peak"] = fw_peak
        case["fw_lit_clean"] = fw_clean

        visible = (
            gold_delta >= 8000
            and fw_peak >= 5000
            and ds["changed_left"] >= 2000
            and ds["changed_right"] >= 2000
            and ds["mean_abs_diff"] >= 4.0
            and case["pipeline"]["playing_after_click"]
            and stage_fw["w"] == 1920
            and stage_fw["h"] == 1080
            and stage_fw["parent"] == "stage"
            and int(stage_fw["z"]) < int(stage_fw["stackZ"])
        )
        case["visible_fireworks"] = bool(visible)

        indep = d.execute_script(
            """
            const s = document.getElementById('preview').contentWindow.H2V4State.getState();
            return {
              price: s.price,
              number: s.number,
              timer_active: s.timer_active,
              timer_remaining: s.timer_remaining_seconds,
              playing: document.getElementById('preview').contentWindow.H2V4SoldFx.isPlaying(),
            };
            """
        )
        case["independence"] = indep
        case["cleaned"] = bool(idle and fw_clean < 500 and not indep["playing"])

        click_sold(d)
        time.sleep(0.35)
        replay = d.execute_script(
            "return document.getElementById('preview').contentWindow.H2V4SoldFx.isPlaying();"
        )
        fw_replay = fw_canvas_gold(d)
        case["replay_ok"] = bool(replay and fw_replay > 1000)

        case["all_ok"] = bool(
            case["visible_fireworks"] and case["cleaned"] and case["replay_ok"]
        )
    finally:
        d.quit()
    report["cases"][label] = case
    return case


def run_direct_1280(report: dict):
    d = driver_at(1280, 720)
    try:
        d.get(f"{BASE}/index.html?plate_type=dubai&code=AA&number=7777&v=soldvis3")
        WebDriverWait(d, 20).until(
            lambda x: x.execute_script(
                "return !!(window.H2V4SoldFx && document.getElementById('stage-fw'));"
            )
        )
        for _ in range(40):
            nw = d.execute_script(
                "const i=document.querySelector('.stage-bg-img'); return i?i.naturalWidth:0;"
            )
            if nw and nw >= 1600:
                break
            time.sleep(0.2)
        time.sleep(0.3)
        d.execute_script(
            "try{ if(window.H2V4BgPlates?.setDensity) H2V4BgPlates.setDensity(0);}catch(e){}"
        )

        def grab(path):
            data = d.execute_cdp_cmd(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "clip": {"x": 0, "y": 0, "width": 1280, "height": 720, "scale": 1},
                    "fromSurface": True,
                },
            )
            im = Image.open(io.BytesIO(base64.b64decode(data["data"]))).convert("RGB")
            # Stage may be letterboxed/scaled — crop stage element
            box = d.execute_script(
                """
                const s = document.getElementById('stage');
                const r = s.getBoundingClientRect();
                return {x:r.left,y:r.top,w:r.width,h:r.height};
                """
            )
            x, y = int(box["x"]), int(box["y"])
            w, h = max(1, int(box["w"])), max(1, int(box["h"]))
            crop = im.crop((x, y, x + w, y + h)).resize((1920, 1080), Image.Resampling.LANCZOS)
            crop.save(path)
            return crop

        before = grab(OUT / "direct-1280-00-before.png")
        d.execute_script(
            "H2V4State.patch({ trigger_sold: true, sold_style: 'fireworks', sold_name: 'QA' });"
        )
        time.sleep(2.2)
        peak = grab(OUT / "direct-1280-25-peak.png")
        zb = zone_counts(before)["zones_total"]
        zp = zone_counts(peak)["zones_total"]
        ds = diff_stats(before, peak)
        fw = d.execute_script(
            """
            const fw = document.getElementById('stage-fw');
            const c = document.createElement('canvas');
            c.width = fw.width; c.height = fw.height;
            c.getContext('2d').drawImage(fw,0,0);
            const data = c.getContext('2d').getImageData(0,0,c.width,c.height).data;
            let n=0; for (let i=3;i<data.length;i+=16) if (data[i]>20) n++;
            return n;
            """
        )
        visible = (zp - zb) >= 8000 and ds["changed_left"] >= 2000 and ds["changed_right"] >= 2000
        report["cases"]["direct-1280"] = {
            "gold_delta": zp - zb,
            "diff": ds,
            "fw_lit_sample": fw,
            "visible": bool(visible),
        }
    finally:
        d.quit()


def main():
    report = {
        "out": str(OUT),
        "root_cause": (
            "Fireworks previously drew on #plate-fw inside #plate, behind opaque "
            ".plate-shell art. Particles existed on the canvas but were visually "
            "covered by the white plate and confined under .stack. Fixed by moving "
            "to full-stage #stage-fw (1920×1080, z-index 3) above ambient plates "
            "and below the auction stack, with rockets exploding in upper L/R studio."
        ),
        "files_modified": [
            "index.html",
            "css/fx.css",
            "js/fx-sold.js",
            "tools/capture_sold_visibility_qa.py",
            "tools/record_sold_visibility_demo.py",
        ],
        "cases": {},
    }
    c1 = run_admin("admin-1920", 1920, 1080, report)
    c2 = run_admin("admin-1600", 1600, 900, report)
    run_direct_1280(report)

    report["all_ok"] = bool(
        c1.get("all_ok")
        and c2.get("all_ok")
        and report["cases"]["direct-1280"].get("visible")
    )
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# SOLD Fireworks Visibility QA",
        "",
        f"**Result:** `{'PASS' if report['all_ok'] else 'FAIL'}`",
        "",
        "## Root cause",
        report["root_cause"],
        "",
        f"- admin-1920 visible: {c1.get('visible_fireworks')} gold_delta={c1.get('gold_delta')} fw_peak={c1.get('fw_lit_peak')}",
        f"- admin-1600 visible: {c2.get('visible_fireworks')} gold_delta={c2.get('gold_delta')} fw_peak={c2.get('fw_lit_peak')}",
        f"- direct-1280: {report['cases']['direct-1280']}",
        "",
    ]
    (OUT / "VISIBILITY_QA.md").write_text("\n".join(md), encoding="utf-8")
    print(
        json.dumps(
            {
                "all_ok": report["all_ok"],
                "c1": {
                    "ok": c1.get("all_ok"),
                    "visible": c1.get("visible_fireworks"),
                    "gold_delta": c1.get("gold_delta"),
                    "fw_peak": c1.get("fw_lit_peak"),
                    "cleaned": c1.get("cleaned"),
                    "diff": c1.get("diff"),
                },
                "c2": {
                    "ok": c2.get("all_ok"),
                    "visible": c2.get("visible_fireworks"),
                    "gold_delta": c2.get("gold_delta"),
                    "fw_peak": c2.get("fw_lit_peak"),
                    "cleaned": c2.get("cleaned"),
                },
                "direct": report["cases"]["direct-1280"],
                "out": str(OUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
