from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time, json
opts=Options(); opts.add_argument("--headless=new"); opts.add_argument("--window-size=1920,1080")
d=webdriver.Chrome(options=opts)
d.get("http://127.0.0.1:8766/assets/studio/H2_AUCTIONS_Studio_1920x1080.jpg")
time.sleep(1)
print("jpg page", d.title, d.execute_script("const i=document.querySelector('img'); return i?{nw:i.naturalWidth,nh:i.naturalHeight,c:i.complete}:'noimg'"))
d.get("http://127.0.0.1:8766/assets/studio/H2_AUCTIONS_Studio_3840x2160.png")
time.sleep(1)
print("png page", d.execute_script("const i=document.querySelector('img'); return i?{nw:i.naturalWidth,nh:i.naturalHeight,c:i.complete,src:i.currentSrc}:location.href"))
# direct img test html
html = "http://127.0.0.1:8766/index.html"
d.get(html)
WebDriverWait(d,10).until(lambda x: x.execute_script("return !!document.getElementById('studio-bg-img')"))
# force jpg
d.execute_script("""
const img=document.getElementById('studio-bg-img');
img.removeAttribute('srcset');
img.src='./assets/studio/H2_AUCTIONS_Studio_1920x1080.jpg';
""")
time.sleep(1)
print(d.execute_script("const i=document.getElementById('studio-bg-img'); return {nw:i.naturalWidth,nh:i.naturalHeight,c:i.complete,src:i.currentSrc,err:i.decode?true:false}"))
d.quit()
