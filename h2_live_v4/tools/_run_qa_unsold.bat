@echo off
setlocal
cd /d C:\Users\moham\h3
set LOGDIR=C:\Users\moham\h3\h2_live_v4\refs\qa\unsold
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set PY=C:\Users\moham\.conda\envs\greenhouse\python.exe

call C:\Users\moham\h3\h2_live_v4\tools\_probe_and_start_v4.bat > "%LOGDIR%\_probe.log" 2>&1

"%PY%" manage.py test plates.tests.LiveDisplayNewTests.test_clear_sold_bumps_clear_event_without_sold_id plates.tests.LiveV4IntegrationTests.test_v4_control_requires_superuser -v2 > "%LOGDIR%\_unit_tests.log" 2>&1
set UNIT_EXIT=%ERRORLEVEL%
echo UNIT_EXIT=%UNIT_EXIT%>> "%LOGDIR%\_unit_tests.log"

"%PY%" C:\Users\moham\h3\h2_live_v4\tools\qa_unsold_e2e.py > "%LOGDIR%\_e2e.log" 2>&1
set E2E_EXIT=%ERRORLEVEL%
echo E2E_EXIT=%E2E_EXIT%>> "%LOGDIR%\_e2e.log"

echo UNIT=%UNIT_EXIT% E2E=%E2E_EXIT%
if %UNIT_EXIT% NEQ 0 exit /b %UNIT_EXIT%
exit /b %E2E_EXIT%
