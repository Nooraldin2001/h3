"""Baseline + after plate screenshots via Django V4 display (token from DB/session mock)."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

OUT = Path(__file__).resolve().parents[2].parent / "h2_live_v4" / "refs" / "qa" / "plate-redesign"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8000"


def shot(d, name, clip=None):
    args = {"format": "png", "fromSurface": True}
    if clip:
        args["clip"] = {**clip, "scale": 1}
    else:
        args["clip"] = {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1}
    data = d.execute_cdp_cmd("Page.captureScreenshot", args)
    path = OUT / name
    path.write_bytes(base64.b64decode(data["data"]))
    return path


def main():
    # Login as superuser if needed — use sandbox static page for visual QA without auth:
    # Prefer V4 static files via Django static serving
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

    # Use sandbox index via static? Better: open h2_live_v4 through file server on 8766 if up,
    # else use Django static preview by injecting plate via local file protocol on live_v4 HTML copy.
    # Simplest reliable path: load sandbox HTTP if available, else write a mini harness.
    url = "http://127.0.0.1:8766/index.html"
    try:
        d.get(url)
        WebDriverWait(d, 3).until(lambda x: x.execute_script("return !!window.H2V4State"))
    except Exception:
        # start using file from static via django? Fallback local file
        harness = Path(__file__).resolve().parents[1] / "_qa_harness.html"
        d.get(harness.as_uri())
        WebDriverWait(d, 10).until(lambda x: x.execute_script("return !!window.H2V4State"))

    types = [
        ("dubai", "AA", "7777", ""),
        ("dubai", "AA", "7", ""),
        ("dubai", "D", "12345", ""),
        ("abudhabi", "15", "88888", ""),
        ("sharjah", "2", "4444", ""),
        ("ajman", "A", "1234", ""),
        ("rasalkhimma", "A", "9999", ""),
        ("fujairah", "A", "5555", ""),
        ("ummalquain", "A", "3333", ""),
        ("dubai_yellow", "AA", "2222", ""),
        ("du", "", "", "0501234567"),
        ("etisalat", "", "", "0569876543"),
    ]

    results = []
    for plate_type, code, number, phone in types:
        d.execute_script(
            """
            const t=arguments[0], c=arguments[1], n=arguments[2], p=arguments[3];
            H2V4State.patch({plate_type:t, code:c, number:n, phone_number:p,
              new_style:{number_visible:true}});
            """,
            plate_type,
            code,
            number,
            phone,
        )
        time.sleep(0.45)
        info = d.execute_script(
            """
            const plate=document.getElementById('plate');
            const shell=document.getElementById('plate-shell');
            const art=document.getElementById('plate-art');
            const num=document.getElementById('plate-number');
            const code=document.getElementById('plate-code');
            const pr=plate.getBoundingClientRect();
            const sr=shell.getBoundingClientRect();
            const ar=art.getBoundingClientRect();
            return {
              plateType: H2V4State.getState().plate_type,
              aspect: getComputedStyle(plate).aspectRatio,
              plate: {w:pr.width,h:pr.height,x:pr.x,y:pr.y},
              shell: {w:sr.width,h:sr.height},
              art: {w:ar.width,h:ar.height, src: art.getAttribute('src')},
              numberText: num ? num.textContent : '',
              codeText: code ? code.textContent : '',
              numberFont: num ? getComputedStyle(num).fontFamily : '',
              numberSize: num ? getComputedStyle(num).fontSize : '',
              shellRadius: getComputedStyle(shell).borderRadius,
              artFit: getComputedStyle(art).objectFit,
            };
            """
        )
        results.append(info)
        shot(d, f"plate-{plate_type}.png")
        # close crop around plate
        pr = info["plate"]
        shot(
            d,
            f"plate-{plate_type}-crop.png",
            {
                "x": max(0, pr["x"] - 40),
                "y": max(0, pr["y"] - 40),
                "width": min(1920, pr["w"] + 80),
                "height": min(1080, pr["h"] + 80),
            },
        )

    # geometry debug for dubai
    d.execute_script(
        """
        H2V4State.patch({plate_type:'dubai', code:'AA', number:'7777'});
        const shell=document.getElementById('plate-shell');
        let dbg=document.getElementById('geo-debug');
        if(!dbg){ dbg=document.createElement('div'); dbg.id='geo-debug'; shell.appendChild(dbg); }
        dbg.style.cssText='position:absolute;inset:0;pointer-events:none;z-index:50;border:2px solid #0f0;box-sizing:border-box;';
        const g=H2PlateSystem.getGeometry('dubai');
        for (const [name,box] of Object.entries({code:g.codeBox, number:g.numberBox})) {
          const el=document.createElement('div');
          el.style.cssText=`position:absolute;top:${box.top}%;left:${box.left}%;width:${box.width}%;height:${box.height}%;border:2px solid ${name==='code'?'#0ff':'#f0f'};box-sizing:border-box;`;
          dbg.appendChild(el);
        }
        """
    )
    time.sleep(0.3)
    info = d.execute_script(
        "const pr=document.getElementById('plate').getBoundingClientRect(); return {x:pr.x,y:pr.y,w:pr.width,h:pr.height};"
    )
    shot(
        d,
        "geometry-debug-dubai.png",
        {
            "x": max(0, info["x"] - 40),
            "y": max(0, info["y"] - 40),
            "width": min(1920, info["w"] + 80),
            "height": min(1080, info["h"] + 80),
        },
    )
    shot(d, "broadcast-dubai-1920.png")
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1280, "height": 720, "deviceScaleFactor": 1, "mobile": False},
    )
    time.sleep(0.3)
    shot(d, "broadcast-dubai-1280.png", {"x": 0, "y": 0, "width": 1280, "height": 720})

    (OUT / "plate-metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("OK", OUT)
    d.quit()


if __name__ == "__main__":
    main()
