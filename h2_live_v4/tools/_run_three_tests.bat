@echo off
cd /d C:\Users\moham\h3
python manage.py test plates.tests.LiveV4IntegrationTests.test_v4_display_serves_v4_assets_not_new_style plates.tests.LiveV4IntegrationTests.test_v4_control_requires_superuser plates.tests.LiveDisplayNewTests.test_studio_theme_patch_persists -v2
echo EXIT_CODE=%ERRORLEVEL%
