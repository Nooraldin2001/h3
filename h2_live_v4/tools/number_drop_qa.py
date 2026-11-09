"""Sequential Number Drop QA — start / mid / end frames + show restore."""
from __future__ import annotations

import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "refs" / "qa" / "number-drop"
OUT_DIR.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8766"

# Match fx-beam-drop.js timing
FALL_MS = 720
STAGGER_MS = 200


def driver_at(w=1920, h=1080):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument(f"--window-size={w},{h}")
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(20)
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    return d


def wait_ready(d):
    WebDriverWait(d, 20).until(
        lambda drv: drv.execute_script(
            "return !!(window.H2V4State && window.H2V4Geom && window.H2V4BeamDropFx);"
        )
    )
    time.sleep(0.35)


def shot(d, name: str) -> str:
    path = OUT_DIR / name
    d.get_screenshot_as_file(str(path))
    return path.name


def probe(d):
    return d.execute_script(
        """
        const state = H2V4State.getState();
        const type = state.plate_type;
        const el = H2PlateSystem.isPhone(type)
          ? document.getElementById('plate-phone')
          : document.getElementById('plate-number');
        const digits = el ? el.querySelectorAll('.plate-digit') : [];
        const fallers = document.querySelectorAll('.plate-digit-fall');
        const visibleDigits = [...digits].filter(s => {
          const cs = getComputedStyle(s);
          return cs.visibility !== 'hidden' && cs.opacity !== '0' && s.offsetParent !== null;
        }).map(s => s.textContent);
        return {
          number_visible: state.new_style?.number_visible !== false,
          stored_number: state.number,
          stored_phone: state.phone_number,
          elText: el ? el.textContent : null,
          elHidden: el ? (el.classList.contains('is-hidden') || el.style.visibility === 'hidden') : null,
          elOpacity: el ? el.style.opacity : null,
          digitCount: digits.length,
          visibleDigitChars: visibleDigits,
          fallerCount: fallers.length,
          fallerChars: [...fallers].map(f => f.textContent),
          dropBusy: !!(H2V4BeamDropFx.isDropBusy && H2V4BeamDropFx.isDropBusy()),
          concealActive: (() => {
            const c = document.getElementById('plate-red-conceal');
            if (!c) return false;
            return c.classList.contains('active') || getComputedStyle(c).display !== 'none' && parseFloat(getComputedStyle(c).opacity) > 0.05;
          })(),
        };
        """
    )


def run_case(d, *, label: str, plate_type: str, number: str, phone: str, code: str = "A"):
    case = {"label": label, "ok": True, "checks": {}, "shots": {}}
    d.execute_script(
        """
        const args = arguments;
        H2V4State.patch({
          plate_type: args[0],
          code: args[1],
          number: args[2],
          phone_number: args[3],
          new_style: { number_visible: true },
        });
        """,
        plate_type,
        code,
        number,
        phone,
    )
    time.sleep(0.4)

    before = probe(d)
    case["checks"]["before"] = before
    case["shots"]["start"] = shot(d, f"{label}-start.png")

    # Trigger Number Drop
    d.execute_script("H2V4State.patch({ ns_drop: true });")

    # Mid: after first digit started, before all finished
    text = phone if plate_type in ("du", "etisalat") else number
    glyph_count = max(1, len(text))
    mid_wait = (STAGGER_MS * 1.2 + FALL_MS * 0.35) / 1000.0
    time.sleep(mid_wait)
    mid = probe(d)
    case["checks"]["mid"] = mid
    case["shots"]["mid"] = shot(d, f"{label}-mid.png")

    # Sequential: mid should still have some plate digits OR fallers, not empty wipe of all at once
    mid_ok = (
        mid.get("fallerCount", 0) >= 1
        or (0 < len(mid.get("visibleDigitChars") or []) < glyph_count)
        or mid.get("dropBusy")
    )
    case["checks"]["mid_sequential"] = {"ok": mid_ok, "detail": mid}
    if not mid_ok:
        case["ok"] = False

    # Wait for completion
    total = (STAGGER_MS * max(0, glyph_count - 1) + FALL_MS + 400) / 1000.0
    deadline = time.time() + total + 1.5
    end = mid
    while time.time() < deadline:
        end = probe(d)
        if not end.get("dropBusy") and end.get("fallerCount", 0) == 0:
            break
        time.sleep(0.08)

    case["checks"]["end"] = end
    case["shots"]["end"] = shot(d, f"{label}-end.png")

    end_ok = (
        end.get("elHidden") is True
        and not end.get("number_visible")
        and end.get("fallerCount", 0) == 0
        and not end.get("dropBusy")
        and not end.get("concealActive")
        and (
            (end.get("stored_number") == number)
            if plate_type not in ("du", "etisalat")
            else (end.get("stored_phone") == phone)
        )
    )
    case["checks"]["end_clean_hidden"] = {"ok": end_ok, "detail": end}
    if not end_ok:
        case["ok"] = False

    # Show Number restores full string at once
    d.execute_script("H2V4State.patch({ ns_show_number: true });")
    time.sleep(0.35)
    shown = probe(d)
    case["checks"]["after_show"] = shown
    case["shots"]["show"] = shot(d, f"{label}-show.png")

    expected_text = phone if plate_type in ("du", "etisalat") else number
    show_ok = (
        shown.get("number_visible") is True
        and shown.get("elHidden") is False
        and (shown.get("elText") or "").replace("\xa0", " ") == expected_text
        and shown.get("digitCount", 0) == 0  # plain text, not leftover spans
    )
    case["checks"]["show_restores_full"] = {"ok": show_ok, "expected": expected_text, "detail": shown}
    if not show_ok:
        case["ok"] = False

    return case


def main():
    report = {"ok": True, "cases": []}
    d = driver_at()
    try:
        d.get(f"{BASE}/?v=numberdrop")
        wait_ready(d)

        cases = [
            ("7777", "dubai", "7777", "0501234567"),
            ("8010", "dubai", "8010", "0501234567"),
            ("phone", "du", "7777", "050 123 4567"),
        ]
        for label, ptype, number, phone in cases:
            print(f"case {label}…")
            result = run_case(d, label=label, plate_type=ptype, number=number, phone=phone)
            report["cases"].append(result)
            if not result["ok"]:
                report["ok"] = False
            print(f"  ok={result['ok']} shots={result['shots']}")

    finally:
        d.quit()

    out = OUT_DIR / "report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "out": str(out)}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
