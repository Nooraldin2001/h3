"""QA: live text above timer via separate Admin control page."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

BASE = "http://127.0.0.1:8766"
OUT = Path(__file__).resolve().parents[1] / "refs" / "qa" / "live-text"
OUT.mkdir(parents=True, exist_ok=True)


def shot(d, name, clip=None):
    args = {"format": "png", "fromSurface": True}
    if clip:
        args["clip"] = clip
    else:
        args["clip"] = {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1}
    data = d.execute_cdp_cmd("Page.captureScreenshot", args)
    path = OUT / name
    path.write_bytes(base64.b64decode(data["data"]))
    return path


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
    results = []

    def check(name, ok, detail=""):
        results.append({"name": name, "ok": bool(ok), "detail": detail})
        print(("PASS" if ok else "FAIL"), name, detail)

    try:
        d.get(f"{BASE}/index.html?v=ltfix")
        WebDriverWait(d, 15).until(lambda x: x.execute_script("return !!window.H2V4State"))
        broadcast = d.current_window_handle

        d.switch_to.new_window("window")
        control = d.current_window_handle
        d.get(f"{BASE}/control.html?v=ltfix")
        WebDriverWait(d, 15).until(
            lambda x: x.execute_script("return !!document.getElementById('btn-live-text-1-apply')")
        )

        # Empty → invisible
        d.switch_to.window(broadcast)
        empty = d.execute_script(
            """
            const w = document.getElementById('live-screen-text');
            const l1 = document.getElementById('live-text-line-1');
            const l2 = document.getElementById('live-text-line-2');
            return {
              hasText: w.classList.contains('has-text'),
              display: getComputedStyle(w).display,
              l1hidden: l1.hidden,
              l2hidden: l2.hidden,
              inStack: !!w.closest('.stack'),
              beforeTimer: w.nextElementSibling && w.nextElementSibling.classList.contains('timer'),
            };
            """
        )
        check("empty_invisible", empty["display"] == "none" and empty["l1hidden"] and empty["l2hidden"], json.dumps(empty))
        check("dom_above_timer", empty["inStack"] and empty["beforeTimer"], json.dumps(empty))

        # Apply Arabic L1 + English L2 from Admin
        d.switch_to.window(control)
        d.find_element("id", "live-text-1").clear()
        d.find_element("id", "live-text-1").send_keys("لوحة مميزة")
        d.find_element("id", "btn-live-text-1-apply").click()
        d.find_element("id", "live-text-2").clear()
        d.find_element("id", "live-text-2").send_keys("H2 Auctions Live")
        d.find_element("id", "btn-live-text-2-apply").click()
        time.sleep(0.6)

        d.switch_to.window(broadcast)
        geo = d.execute_script(
            """
            const s = H2V4State.getState();
            const l1 = document.getElementById('live-text-line-1');
            const l2 = document.getElementById('live-text-line-2');
            const w = document.getElementById('live-screen-text');
            const t = document.querySelector('.timer');
            const r1 = l1.getBoundingClientRect();
            const r2 = l2.getBoundingClientRect();
            const rt = t.getBoundingClientRect();
            return {
              state: {l1:s.live_text_line1, l2:s.live_text_line2},
              text: {l1:l1.textContent, l2:l2.textContent, hidden1:l1.hidden, hidden2:l2.hidden},
              hasText: w.classList.contains('has-text'),
              wrapDisplay: getComputedStyle(w).display,
              gapAboveTimer: rt.top - r2.bottom,
              line1AboveLine2: r1.bottom <= r2.top + 1,
              line2AboveTimer: r2.bottom <= rt.top + 1,
              l1vis: getComputedStyle(l1).visibility,
              l1opacity: getComputedStyle(l1).opacity,
              l1h: r1.height,
              l2h: r2.height,
            };
            """
        )
        check(
            "state_received",
            geo["state"]["l1"] == "لوحة مميزة" and geo["state"]["l2"] == "H2 Auctions Live",
            json.dumps(geo["state"], ensure_ascii=False),
        )
        check(
            "visible_above_timer",
            geo["hasText"]
            and geo["wrapDisplay"] != "none"
            and not geo["text"]["hidden1"]
            and not geo["text"]["hidden2"]
            and geo["l1h"] > 10
            and geo["l2h"] > 10
            and geo["line2AboveTimer"]
            and geo["gapAboveTimer"] < 40,
            json.dumps({k: geo[k] for k in ("gapAboveTimer", "line2AboveTimer", "l1h", "l2h", "wrapDisplay")}),
        )
        shot(d, "broadcast-live-text-above-timer.png")
        shot(
            d,
            "live-text-above-timer-crop.png",
            {"x": 560, "y": 180, "width": 800, "height": 280, "scale": 1},
        )

        # Independent clear line 1
        d.switch_to.window(control)
        d.find_element("id", "btn-live-text-1-clear").click()
        time.sleep(0.4)
        d.switch_to.window(broadcast)
        c1 = d.execute_script(
            """
            const s = H2V4State.getState();
            const l1 = document.getElementById('live-text-line-1');
            const l2 = document.getElementById('live-text-line-2');
            return {s1:s.live_text_line1, s2:s.live_text_line2, h1:l1.hidden, h2:l2.hidden, t2:l2.textContent};
            """
        )
        check("clear_line1_keeps_line2", c1["s1"] == "" and c1["h1"] and not c1["h2"] and c1["t2"] == "H2 Auctions Live", json.dumps(c1, ensure_ascii=False))

        # Re-apply L1, clear L2
        d.switch_to.window(control)
        d.find_element("id", "live-text-1").clear()
        d.find_element("id", "live-text-1").send_keys("مزاد مباشر")
        d.find_element("id", "btn-live-text-1-apply").click()
        d.find_element("id", "btn-live-text-2-clear").click()
        time.sleep(0.4)
        d.switch_to.window(broadcast)
        c2 = d.execute_script(
            """
            const s = H2V4State.getState();
            const l1 = document.getElementById('live-text-line-1');
            const l2 = document.getElementById('live-text-line-2');
            return {s1:s.live_text_line1, s2:s.live_text_line2, h1:l1.hidden, h2:l2.hidden, t1:l1.textContent};
            """
        )
        check("clear_line2_keeps_line1", c2["s2"] == "" and c2["h2"] and not c2["h1"] and c2["t1"] == "مزاد مباشر", json.dumps(c2, ensure_ascii=False))

        # Both lines for persistence test
        d.switch_to.window(control)
        d.find_element("id", "live-text-2").clear()
        d.find_element("id", "live-text-2").send_keys("Persist OK")
        d.find_element("id", "btn-live-text-2-apply").click()
        time.sleep(0.4)

        d.switch_to.window(broadcast)
        d.refresh()
        WebDriverWait(d, 15).until(lambda x: x.execute_script("return !!window.H2V4State"))
        time.sleep(0.5)
        pers = d.execute_script(
            """
            const s = H2V4State.getState();
            const l1 = document.getElementById('live-text-line-1');
            const l2 = document.getElementById('live-text-line-2');
            return {
              s1:s.live_text_line1, s2:s.live_text_line2,
              t1:l1.textContent, t2:l2.textContent,
              h1:l1.hidden, h2:l2.hidden,
              hasText: document.getElementById('live-screen-text').classList.contains('has-text'),
            };
            """
        )
        check(
            "persist_after_broadcast_refresh",
            pers["s1"] == "مزاد مباشر"
            and pers["s2"] == "Persist OK"
            and pers["t1"] == "مزاد مباشر"
            and pers["t2"] == "Persist OK"
            and not pers["h1"]
            and not pers["h2"],
            json.dumps(pers, ensure_ascii=False),
        )

        # Smoke: other control still works (bid)
        d.switch_to.window(control)
        price = d.find_element("id", "price")
        price.clear()
        price.send_keys("222000")
        d.find_element("id", "btn-apply-lot").click()
        time.sleep(0.4)
        d.switch_to.window(broadcast)
        bid = d.execute_script("return H2V4State.getState().price")
        check("other_controls_still_work", str(bid) == "222000", f"price={bid}")

    finally:
        d.quit()

    failed = [r for r in results if not r["ok"]]
    print(f"Result: {sum(1 for r in results if r['ok'])}/{len(results)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
