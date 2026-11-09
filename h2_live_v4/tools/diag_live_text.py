from __future__ import annotations

import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

BASE = "http://127.0.0.1:8766"


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    d = webdriver.Chrome(options=opts)
    try:
        d.get(f"{BASE}/index.html?v=livetext1")
        WebDriverWait(d, 15).until(lambda x: x.execute_script("return !!window.H2V4State"))
        b = d.current_window_handle
        d.switch_to.new_window("window")
        d.get(f"{BASE}/control.html?v=livetext1")
        WebDriverWait(d, 15).until(
            lambda x: x.execute_script("return !!document.getElementById('btn-live-text-1-apply')")
        )
        d.find_element("id", "live-text-1").clear()
        d.find_element("id", "live-text-1").send_keys("لوحة مميزة")
        d.find_element("id", "btn-live-text-1-apply").click()
        d.find_element("id", "live-text-2").clear()
        d.find_element("id", "live-text-2").send_keys("H2 Auctions Live")
        d.find_element("id", "btn-live-text-2-apply").click()
        time.sleep(0.8)
        d.switch_to.window(b)
        info = d.execute_script(
            """
            const s = H2V4State.getState();
            const l1 = document.getElementById('live-text-line-1');
            const l2 = document.getElementById('live-text-line-2');
            const wrap = document.getElementById('live-screen-text');
            function box(el){
              if(!el) return null;
              const r = el.getBoundingClientRect();
              const cs = getComputedStyle(el);
              return {
                text: el.textContent,
                hidden: el.hidden,
                hasHiddenAttr: el.hasAttribute('hidden'),
                display: cs.display,
                visibility: cs.visibility,
                opacity: cs.opacity,
                color: cs.color,
                zIndex: cs.zIndex,
                fontSize: cs.fontSize,
                rect: {x:r.x,y:r.y,w:r.width,h:r.height},
                parentDisplay: el.parentElement ? getComputedStyle(el.parentElement).display : null,
                parentZ: el.parentElement ? getComputedStyle(el.parentElement).zIndex : null,
                parentRect: el.parentElement ? (()=>{const p=el.parentElement.getBoundingClientRect(); return {x:p.x,y:p.y,w:p.width,h:p.height};})() : null,
              };
            }
            const stage = document.getElementById('stage');
            return {
              state: {l1:s.live_text_line1, l2:s.live_text_line2},
              wrap: box(wrap),
              line1: box(l1),
              line2: box(l2),
              timer: (()=>{const t=document.querySelector('.timer'); const r=t.getBoundingClientRect(); return {y:r.y,h:r.height, top:getComputedStyle(t).top};})(),
              brand: (()=>{const t=document.querySelector('.brand'); const r=t.getBoundingClientRect(); return {y:r.y,h:r.height};})(),
              stack: (()=>{const t=document.querySelector('.stack'); const r=t.getBoundingClientRect(); return {y:r.y,h:r.height,z:getComputedStyle(t).zIndex};})(),
              stageOverflow: stage ? getComputedStyle(stage).overflow : null,
            };
            """
        )
        print(json.dumps(info, ensure_ascii=False, indent=2))
    finally:
        d.quit()


if __name__ == "__main__":
    main()
