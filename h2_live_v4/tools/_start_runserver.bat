@echo off
cd /d C:\Users\moham\h3
set DEBUG=True
set ALLOWED_HOSTS=127.0.0.1,localhost
python manage.py runserver 127.0.0.1:8000
