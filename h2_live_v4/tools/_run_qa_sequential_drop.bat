@echo off
cd /d C:\Users\moham\h3
"C:\Users\moham\.conda\envs\greenhouse\python.exe" "C:\Users\moham\h3\h2_live_v4\tools\qa_sequential_drop.py" > "%TEMP%\h2_qa_seq_drop.log" 2>&1
exit /b %ERRORLEVEL%
