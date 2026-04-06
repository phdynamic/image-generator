@echo off
title Imaginaree
cd /d "%~dp0"
call backend\venv\Scripts\activate
python run_app.py
