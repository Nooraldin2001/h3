"""Visual QA captures for V4 plate redesign (sandbox http://127.0.0.1:8766)."""
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
URL = "http://127.0.0.1:8766/index.html"


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


def plate_clip(info):
    pr = info["plate"]
    return {
        "x": max(0, pr["x"] - 40),
        "y": max(0, pr["y"] - 40),
        "width": min(1920 - max(0, pr["x"] - 40), pr["w"] + 80),
        "height": min(1080 - max(0, pr["y"] - 40), pr["h"] + 80),
    }


def measure(d):
    return d.execute_script(
        """
        const plate=document.getElementById('plate');
        const shell=document.getElementById('plate-shell');
        const art=document.getElementById('plate-art');
        const num=document.getElementById('plate-number');
        const code=document.getElementById('plate-code');
        const phone=document.getElementById('plate-phone');
        const rim=document.getElementById('plate-rim');
        const pr=plate.getBoundingClientRect();
        const sr=shell.getBoundingClientRect();
        const ar=art.getBoundingClientRect();
        const st=H2V4State.getState();
        return {
          plateType: st.plate_type,
          aspect: getComputedStyle(plate).aspectRatio,
          plate: {w:pr.width,h:pr.height,x:pr.x,y:pr.y},
          shell: {w:sr.width,h:sr.height,x:sr.x,y:sr.y},
          art: {w:ar.width,h:ar.height, src: art.currentSrc || art.getAttribute('src')},
          numberText: num && !num.hidden ? num.textContent : '',
          codeText: code && !code.hidden ? code.textContent : '',
          phoneText: phone && !phone.hidden ? phone.textContent : '',
          numberFont: num ? getComputedStyle(num).fontFamily : '',
          numberSize: num ? getComputedStyle(num).fontSize : '',
          numberWeight: num ? getComputedStyle(num).fontWeight : '',
          shellRadius: getComputedStyle(shell).borderRadius,
          artFit: getComputedStyle(art).objectFit,
          shellBg: getComputedStyle(shell).backgroundColor,
          rimRadius: rim ? getComputedStyle(rim).borderRadius : '',
          aspectMismatch: Math.abs(sr.width/sr.height - (ar.width/ar.height)) < 0.02,
        };
        """
    )


def patch(d, plate_type, code, number, phone):
    d.execute_script(
        """
        const t=arguments[0], c=arguments[1], n=arguments[2], p=arguments[3];
        H2V4State.patch({
          plate_type:t, code:c, number:n, phone_number:p,
          new_style:{number_visible:true}
        });
        """,
        plate_type,
        code,
        number,
        phone,
    )
    time.sleep(0.35)


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
    d.get(URL)
    WebDriverWait(d, 12).until(lambda x: x.execute_script("return !!window.H2V4State && !!window.H2PlateSystem"))

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
        patch(d, plate_type, code, number, phone)
        info = measure(d)
        results.append(info)
        tag = plate_type if number not in ("7", "12345") else f"{plate_type}-{number}"
        shot(d, f"after-{tag}.png")
        shot(d, f"after-{tag}-crop.png", plate_clip(info))

    # Geometry debug overlays
    d.execute_script(
        """
        H2V4State.patch({plate_type:'dubai', code:'AA', number:'7777', new_style:{number_visible:true}});
        const shell=document.getElementById('plate-shell');
        let dbg=document.getElementById('geo-debug');
        if (dbg) dbg.remove();
        dbg=document.createElement('div'); dbg.id='geo-debug'; shell.appendChild(dbg);
        dbg.style.cssText='position:absolute;inset:0;pointer-events:none;z-index:50;border:3px solid #22c55e;box-sizing:border-box;';
        const g=H2PlateSystem.getGeometry('dubai');
        const stamp=H2PlateSystem.getStampTarget('dubai');
        for (const [name,box,col] of [
          ['code', g.codeBox, '#06b6d4'],
          ['number', g.numberBox, '#a855f7'],
        ]) {
          const el=document.createElement('div');
          el.style.cssText=`position:absolute;top:${box.top}%;left:${box.left}%;width:${box.width}%;height:${box.height}%;border:2px solid ${col};box-sizing:border-box;`;
          el.title=name; dbg.appendChild(el);
        }
        const st=document.createElement('div');
        st.style.cssText=`position:absolute;left:${stamp.x*100}%;top:${stamp.y*100}%;width:12px;height:12px;margin:-6px 0 0 -6px;border-radius:50%;background:#f59e0b;border:2px solid #fff;`;
        dbg.appendChild(st);
        H2V4Character?.fitRim?.();
        const rim=document.getElementById('plate-rim');
        rim.classList.add('yellow');
        rim.setAttribute('aria-hidden','false');
        """
    )
    time.sleep(0.4)
    info = measure(d)
    shot(d, "geometry-debug-dubai.png", plate_clip(info))
    shot(d, "after-dubai-yellow-rim.png", plate_clip(info))

    # Red card: digits hidden, rim red
    d.execute_script(
        """
        document.getElementById('geo-debug')?.remove();
        const rim=document.getElementById('plate-rim');
        rim.classList.remove('yellow'); rim.classList.add('red');
        H2V4BeamDropFx?.setRed?.(true);
        """
    )
    time.sleep(0.35)
    info = measure(d)
    shot(d, "after-dubai-red-card.png", plate_clip(info))
    d.execute_script("H2V4BeamDropFx?.setRed?.(false); document.getElementById('plate-rim')?.classList.remove('red');")

    # SOLD stamp alignment
    d.execute_script(
        """
        H2V4State.patch({plate_type:'dubai', code:'AA', number:'7777'});
        const stamp=document.getElementById('plate-sold-stamp');
        if (stamp) {
          stamp.hidden=false; stamp.removeAttribute('hidden');
          stamp.style.opacity='1'; stamp.style.visibility='visible';
          const t=H2PlateSystem.getStampTarget('dubai');
          stamp.style.left=(t.x*100)+'%'; stamp.style.top=(t.y*100)+'%';
          stamp.style.transform='translate(-50%,-50%) rotate(-12deg)';
          stamp.style.position='absolute'; stamp.style.zIndex='20';
          stamp.style.width='42%'; stamp.style.height='auto';
        }
        """
    )
    time.sleep(0.35)
    info = measure(d)
    shot(d, "after-dubai-sold-stamp.png", plate_clip(info))

    # Full broadcast frames
    patch(d, "dubai", "AA", "7777", "")
    d.execute_script("document.getElementById('plate-sold-stamp').hidden=true;")
    shot(d, "after-broadcast-dubai-1920.png")
    d.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1280, "height": 720, "deviceScaleFactor": 1, "mobile": False},
    )
    time.sleep(0.35)
    shot(d, "after-broadcast-dubai-1280.png", {"x": 0, "y": 0, "width": 1280, "height": 720})

    (OUT / "plate-metrics-after.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("OK", OUT)
    print("types", len(results))
    d.quit()


if __name__ == "__main__":
    main()
