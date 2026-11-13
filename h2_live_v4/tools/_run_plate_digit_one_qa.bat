@echo off
setlocal
cd /d C:\Users\moham\h3
set OUT=C:\Users\moham\h3\h2_live_v4\refs\qa\plate_digit_one
if not exist "%OUT%" mkdir "%OUT%"
set PY=C:\Users\moham\.conda\envs\greenhouse\python.exe

call C:\Users\moham\h3\h2_live_v4\tools\_probe_and_start_v4_greenhouse.bat > "%OUT%\_probe.log" 2>&1

"%PY%" C:\Users\moham\h3\h2_live_v4\tools\qa_plate_digit_one.py > "%OUT%\_e2e.log" 2>&1
set E2E_EXIT=%ERRORLEVEL%
echo E2E_EXIT=%E2E_EXIT%>> "%OUT%\_e2e.log"
echo E2E=%E2E_EXIT%
exit /b %E2E_EXIT%
