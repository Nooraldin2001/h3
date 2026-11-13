@echo off
cd /d C:\Users\moham\h3
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ar/', timeout=3)" 2>nul
if errorlevel 1 (
  start "" /b cmd /c "set DEBUG=True&& set ALLOWED_HOSTS=127.0.0.1,localhost&& cd /d C:\Users\moham\h3&& python manage.py runserver 127.0.0.1:8000"
  timeout /t 6 /nobreak >nul
)
python h2_live_v4\tools\qa_studio_theme_fx_smoke.py
echo EXIT_CODE=%ERRORLEVEL%
