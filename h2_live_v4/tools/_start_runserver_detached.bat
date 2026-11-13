@echo off
setlocal
set DEBUG=True
set ALLOWED_HOSTS=127.0.0.1,localhost
cd /d C:\Users\moham\h3
set LOG=C:\Users\moham\h3\h2_live_v4\tools\_runserver.log
echo [%date% %time%] Starting runserver >> "%LOG%"
C:\Users\moham\.conda\envs\greenhouse\python.exe manage.py runserver 127.0.0.1:8000 >> "%LOG%" 2>&1
