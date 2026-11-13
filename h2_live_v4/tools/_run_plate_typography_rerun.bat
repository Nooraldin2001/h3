@echo off
setlocal
cd /d C:\Users\moham\h3
set PY=C:\Users\moham\.conda\envs\greenhouse\python.exe
call C:\Users\moham\h3\h2_live_v4\tools\_probe_and_start_v4.bat
"%PY%" C:\Users\moham\h3\h2_live_v4\tools\qa_plate_typography_rerun.py
exit /b %ERRORLEVEL%
