@echo off
mkdir "C:\Users\moham\h3\h2_live_v4\refs\qa\sequential_drop" 2>nul
copy /Y "%~1" "C:\Users\moham\h3\h2_live_v4\refs\qa\sequential_drop\%~nx1"
exit /b 0
