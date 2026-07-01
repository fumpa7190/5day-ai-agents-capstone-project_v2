@echo off
title PNG Classroom Resource Generator
cd /d "%~dp0"

echo Starting PNG Classroom Resource Generator...
echo A browser window will open automatically once it's ready.
echo Leave this window open while you use the app. Close it to stop the app.
echo.

".venv\Scripts\python.exe" -m streamlit run frontend\app.py

pause
