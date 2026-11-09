"""H2 Live V4 — phase screenshot + automated DOM checks (Selenium)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "refs" / "qa" / "phases"
GEOM = ROOT / "refs" / "qa" / "geometry"
QA.mkdir(parents=True, exist_ok=True)
GEOM.mkdir(parents=True, exist_ok=True)

BASE = "http://127.0.0.1:8766"
TYPES = [
    "abudhabi",
    "dubai",
    "dubai_yellow",
    "rasalkhimma",
    "fujairah",
    "ajman",
    "ummalquain",
    "sharjah",
    "du",
    "etisalat",
]


def driver_1920():
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
    return d


def wait_ready(d, timeout=20):
    WebDriverWait(d, timeout).until(
        lambda drv: drv.execute_script(
            "return !!(window.H2V4State && window.H2PlateSystem && window.H2V4Character && window.H2V4CharacterAcceptance);"
        )
    )
    # Soft-wait for studio still (do not fail the suite if slow)
    try:
        WebDriverWait(d, 5).until(
            lambda drv: drv.execute_script(
                "const img=document.querySelector('.stage-bg-img');"
                "return !!(img && (img.complete || img.naturalWidth>0));"
            )
        )
    except Exception:
        pass
    time.sleep(0.25)


def shot(d, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    d.get_screenshot_as_file(str(path))


def run_checks(d) -> dict:
    return d.execute_script(
        """
        const s = H2V4State.getState();
        const stage = document.getElementById('stage').getBoundingClientRect();
        const brand = document.querySelector('.brand').getBoundingClientRect();
        const timer = document.querySelector('.timer').getBoundingClientRect();
        const plate = document.getElementById('plate').getBoundingClientRect();
        const bid = document.querySelector('.bid').getBoundingClientRect();
        const charZ = getComputedStyle(document.getElementById('character')).zIndex;
        const stackZ = getComputedStyle(document.querySelector('.stack')).zIndex;
        const brandZ = getComputedStyle(document.querySelector('.brand')).zIndex;
        const fw = document.getElementById('plate-fw');
        const shell = document.getElementById('plate-shell');
        return {
          stage: {w: stage.width, h: stage.height},
          order: {
            brandAboveTimer: brand.bottom <= timer.top + 2,
            timerAbovePlate: timer.bottom <= plate.top + 8,
            plateAboveBid: plate.bottom <= bid.top + 8,
          },
          z: {character: charZ, stack: stackZ, brand: brandZ},
          zOk: Number(charZ) > Number(stackZ) && Number(brandZ) > Number(charZ),
          plateType: s.plate_type,
          identity: H2V4State.plateIdentity(),
          fwBehindShell: Number(getComputedStyle(fw).zIndex) < Number(getComputedStyle(shell).zIndex),
          characterIncomplete: H2V4Character.ASSET_STATUS,
          agingTier: H2V4AgingFx.ASSET_TIER,
          bgNote: H2V4BgPlatesFx.ASSET_NOTE,
          debugOff: !H2V4Debug.enabled || new URLSearchParams(location.search).get('debug') !== '1',
        };
        """
    )


def main():
    report = {"phases": {}, "geometry": {}, "events": {}, "ok": True}
    d = driver_1920()
    try:
        # Phase 0/1 base
        d.get(f"{BASE}/?v=qa")
        wait_ready(d)
        shot(d, QA / "phase0-base-1920x1080.png")
        checks = run_checks(d)
        report["phases"]["0_1_base"] = checks
        if not checks["order"]["brandAboveTimer"] or not checks["zOk"]:
            report["ok"] = False

        # Geometry matrix
        for t in TYPES:
            phone = "0501234567" if t in ("du", "etisalat") else ""
            url = f"{BASE}/?plate_type={t}&code=AA&number=7777&phone={phone}&v=geom"
            d.get(url)
            wait_ready(d)
            time.sleep(0.35)
            shot(d, GEOM / f"{t}.png")
            info = d.execute_script(
                """
                const s = H2V4State.getState();
                const phone = document.getElementById('plate-phone');
                const code = document.getElementById('plate-code');
                const number = document.getElementById('plate-number');
                const plate = document.getElementById('plate');
                const aspect = getComputedStyle(plate).aspectRatio;
                return {
                  type: s.plate_type,
                  phoneHidden: phone.hidden,
                  codeHidden: code.hidden,
                  numberHidden: number.hidden,
                  aspect,
                  w: plate.getBoundingClientRect().width,
                  h: plate.getBoundingClientRect().height,
                };
                """
            )
            report["geometry"][t] = info
            if t in ("du", "etisalat"):
                if info["phoneHidden"] or not info["codeHidden"]:
                    report["ok"] = False
            else:
                if not info["phoneHidden"] or info["codeHidden"]:
                    report["ok"] = False

        # Phase 2 event seed / no replay
        d.get(f"{BASE}/")
        wait_ready(d)
        d.execute_script(
            """
            window.__replay = [];
            H2V4State.subscribe((k) => window.__replay.push(k));
            // Seeded state with sold_event_id already 3 — refresh simulation
            const st = H2V4State.getState();
            st.sold_event_id = 3;
            st.new_style.events.beam_event_id = 2;
            H2V4State.seedFromState();
            window.__replay = [];
            H2V4State.patch({}); // should not fire sold/beam
            window.__afterSeed = window.__replay.slice();
            H2V4State.patch({ ns_beam: true });
            window.__afterBeam = window.__replay.slice();
            """
        )
        events = d.execute_script(
            "return { afterSeed: window.__afterSeed, afterBeam: window.__afterBeam };"
        )
        report["events"]["seed"] = events
        if "sold" in events["afterSeed"] or "beam" in events["afterSeed"]:
            report["ok"] = False
        if "beam" not in events["afterBeam"]:
            report["ok"] = False

        # Phase 3 FX screenshots
        d.get(f"{BASE}/")
        wait_ready(d)
        d.execute_script("H2V4State.patch({ trigger_sold: true, sold_style: 'fireworks' });")
        time.sleep(0.6)
        shot(d, QA / "phase3-sold-fw.png")

        d.execute_script("H2V4State.patch({ ns_beam: true });")
        time.sleep(0.4)
        shot(d, QA / "phase3-beam.png")

        d.execute_script("H2V4State.patch({ ns_drop: true });")
        time.sleep(0.35)
        shot(d, QA / "phase3-drop.png")

        # Phase 4 aging
        d.get(f"{BASE}/?aging=1")
        wait_ready(d)
        time.sleep(0.5)
        aging = d.execute_script("return H2V4AgingFx.agingProgress();")
        report["phases"]["4_aging_progress"] = aging
        shot(d, QA / "phase4-aging.png")
        if aging <= 0:
            report["ok"] = False

        # Phase 5 bg floats
        d.get(f"{BASE}/?bg=1")
        wait_ready(d)
        time.sleep(0.6)
        bg_count = d.execute_script(
            "return document.querySelectorAll('#bg-plates .bg-plate-sprite').length;"
        )
        report["phases"]["5_bg_count"] = bg_count
        shot(d, QA / "phase5-bg-floats.png")

        # Phase 6 character incomplete path + acceptance suite
        d.get(f"{BASE}/")
        wait_ready(d)
        d.execute_script("return H2V4Character.probeAll();")
        time.sleep(0.4)
        char = d.execute_script(
            """
            const r = H2V4Character.play('sold_stamp', { soldStamp: true });
            const suite = H2V4CharacterAcceptance.runSuite();
            return {
              result: r,
              presence: H2V4Character.getPresence(),
              meta: H2V4Character.getMeta(),
              acceptance: suite,
            };
            """
        )
        report["phases"]["6_character"] = char
        time.sleep(0.5)
        shot(d, QA / "phase6-character-incomplete.png")
        if char["result"].get("measured"):
            report["ok"] = False  # should not be measured without assets
        if char.get("acceptance", {}).get("failed", 0) > 0:
            report["ok"] = False

        # Phase 5 keyed asset presence
        keyed = d.execute_script(
            """
            return fetch('./assets/bg_plates/A.png', {method:'HEAD'}).then(r => r.ok);
            """
        )
        # selenium execute_script won't await promise — use sync XHR check
        keyed = d.execute_script(
            """
            const x = new XMLHttpRequest();
            x.open('HEAD', './assets/bg_plates/A.png', false);
            x.send(null);
            return x.status >= 200 && x.status < 400;
            """
        )
        report["phases"]["5_keyed_A"] = keyed
        if not keyed:
            report["ok"] = False

        # Phase 7 debug overlay
        d.get(f"{BASE}/?debug=1")
        wait_ready(d)
        time.sleep(0.4)
        dbg = d.execute_script(
            "return { enabled: H2V4Debug.enabled, kids: document.getElementById('debug-overlay').children.length };"
        )
        report["phases"]["7_debug"] = dbg
        shot(d, QA / "phase7-debug.png")
        if not dbg["enabled"] or dbg["kids"] < 3:
            report["ok"] = False

        # 1280 preview scale check
        d.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1280, "height": 720, "deviceScaleFactor": 1, "mobile": False},
        )
        d.get(f"{BASE}/")
        wait_ready(d)
        time.sleep(0.3)
        shot(d, QA / "preview-1280x720.png")
        scale = d.execute_script(
            "return document.getElementById('stage').style.transform || 'none';"
        )
        report["phases"]["preview_scale"] = scale

    finally:
        d.quit()

    out = ROOT / "refs" / "qa" / "phase-report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("WROTE", out)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
