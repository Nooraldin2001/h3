"""Partial re-run: dubai A/7777 + abudhabi 1/88888 (v=20261112type2)."""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import qa_plate_typography as qa
from plates.models import LiveBroadcastSession  # noqa: E402 — django.setup via qa import
from selenium.webdriver.support.ui import WebDriverWait

RERUN_IDS = ("dubai_A_7777", "abudhabi_1_88888")
CACHE = "20261112type2"
OUT = qa.OUT
REPORT_PATH = os.path.join(OUT, "report.json")


def main() -> int:
    prior: dict = {}
    if os.path.isfile(REPORT_PATH):
        with open(REPORT_PATH, encoding="utf-8") as f:
            prior = json.load(f)

    cases = [c for c in qa.CASES if c["id"] in RERUN_IDS]
    session = LiveBroadcastSession.objects.order_by("pk").first()
    if not session:
        return 1
    ns = qa.normalize_new_style(session.new_style if isinstance(session.new_style, dict) else {})
    ns["number_visible"] = True
    ns["sold_imprint_active"] = False
    ns.setdefault("studio_theme", "dark")
    session.new_style = ns
    session.save(update_fields=["new_style"])
    token = str(session.display_token)
    bust = f"?v={CACHE}&_={int(time.time())}"

    ctrl = qa.chrome()
    disp = qa.chrome()
    merged_cases: dict = dict(prior.get("cases") or {})
    try:
        disp_url = f"{qa.BASE}/live/display-v4/{token}/{bust}"
        ctrl_url = f"{qa.BASE}/live/control/v4/{bust}"
        qa.hard_refresh(disp, disp_url)
        qa.wait_display_ready(disp)
        qa.login_control(ctrl)
        qa.hard_refresh(ctrl, ctrl_url)
        WebDriverWait(ctrl, 25).until(lambda x: x.execute_script("return !!window.H2V4DjangoBridge"))
        qa.hard_refresh(disp, disp_url)
        qa.wait_display_ready(disp)

        for case in cases:
            print("CASE", case["id"])
            qa.apply_lot(ctrl, disp, case)
            metrics = disp.execute_script(qa.typography_js(CACHE), case["mode"])
            ok, detail = qa.assert_case(metrics)
            shot_path = os.path.join(OUT, case["shot"])
            qa.shot_cdp(disp, shot_path)
            merged_cases[case["id"]] = {
                "ok": ok,
                "detail": detail,
                "screenshot": shot_path,
                "metrics": metrics,
            }
            print(("PASS" if ok else "FAIL"), case["id"], detail)

        rerun_ok = all(merged_cases[i]["ok"] for i in RERUN_IDS if i in merged_cases)
        all_ok = all((merged_cases.get(k) or {}).get("ok") for k in merged_cases)
        report = {
            **prior,
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cache_bust": CACHE,
            "display_url": f"{qa.BASE}/live/display-v4/{token}/?v={CACHE}",
            "control_url": f"{qa.BASE}/live/control/v4/?v={CACHE}",
            "partial_rerun": list(RERUN_IDS),
            "cases": merged_cases,
            "ok": all_ok,
            "typography_notes": {
                "font_stack_expects_oswald": True,
                "sample_font_sizes_px": {
                    k: {
                        ov["id"]: ov.get("fontSizePx")
                        for ov in (v.get("metrics", {}).get("overlays") or [])
                    }
                    for k, v in merged_cases.items()
                },
            },
        }
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("REPORT", REPORT_PATH, "RERUN_OK" if rerun_ok else "RERUN_FAIL")
        return 0 if rerun_ok else 1
    finally:
        ctrl.quit()
        disp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
