@echo off
cd /d C:\Users\moham\h3
set PY=C:\Users\moham\.conda\envs\greenhouse\python.exe
set DEBUG=True
set ALLOWED_HOSTS=127.0.0.1,localhost
echo === Django unit tests ===
"%PY%" manage.py test plates.tests.LiveTimerReliabilityTests -v2 > h2_live_v4\refs\qa\timer_reliability\unit_tests.log 2>&1
echo UNIT_EXIT=%ERRORLEVEL% >> h2_live_v4\refs\qa\timer_reliability\unit_tests.log
call h2_live_v4\tools\_probe_and_start_v4_greenhouse.bat
echo === E2E ===
"%PY%" h2_live_v4\tools\qa_timer_reliability.py > h2_live_v4\refs\qa\timer_reliability\e2e.log 2>&1
echo E2E_EXIT=%ERRORLEVEL% >> h2_live_v4\refs\qa\timer_reliability\e2e.log
exit /b 0
