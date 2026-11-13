@echo off
cd /d C:\Users\moham\h3
python manage.py test plates.tests.LiveDisplayNewTests.test_studio_theme_patch_persists plates.tests.LiveDisplayNewTests.test_state_api_includes_normalized_new_style -v2
echo EXIT_CODE=%ERRORLEVEL%
