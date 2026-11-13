@echo off
cd /d C:\Users\moham\h3
python manage.py test plates.tests.LiveDisplayNewTests.test_clear_sold_bumps_clear_event_without_sold_id plates.tests.LiveV4IntegrationTests.test_v4_control_requires_superuser -v2
echo EXIT_CODE=%ERRORLEVEL%
