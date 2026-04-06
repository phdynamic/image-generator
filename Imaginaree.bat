@echo off
title Imaginaree
cd /d "%~dp0"
call backend\venv\Scripts\activate
python run_app.py
if errorlevel 1 (
    echo.
    echo ERROR: Imaginaree failed to start. See above for details.
    pause
)
