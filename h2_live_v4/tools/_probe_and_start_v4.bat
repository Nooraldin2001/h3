@echo off
cd /d C:\Users\moham\h3
curl -s -o NUL -w "%%{http_code}" http://127.0.0.1:8000/live/control/v4/ > "%TEMP%\h2_probe.txt" 2>NUL
set /p CODE=<"%TEMP%\h2_probe.txt"
echo PROBE=%CODE%
if "%CODE%"=="200" goto :alive
if "%CODE%"=="302" goto :alive
if "%CODE%"=="301" goto :alive
echo Starting runserver...
set DEBUG=True
set ALLOWED_HOSTS=127.0.0.1,localhost
start "H2-Django-V4" /MIN cmd /c "cd /d C:\Users\moham\h3 && set DEBUG=True&& set ALLOWED_HOSTS=127.0.0.1,localhost&& python manage.py runserver 127.0.0.1:8000"
timeout /t 4 /nobreak >NUL
curl -s -o NUL -w "%%{http_code}" http://127.0.0.1:8000/live/control/v4/ > "%TEMP%\h2_probe.txt" 2>NUL
set /p CODE2=<"%TEMP%\h2_probe.txt"
echo AFTER=%CODE2%
exit /b 0
:alive
echo ALREADY_RUNNING
exit /b 0
