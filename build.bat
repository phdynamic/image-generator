@echo off
title Imaginaree Build
echo ========================================
echo   Building Imaginaree Desktop App
echo ========================================
echo.
echo This will take several minutes and create a
echo standalone Imaginaree.exe in the dist folder.
echo.

cd /d "%~dp0"

echo [1/4] Building frontend...
cd frontend
call npm run build
if errorlevel 1 goto error
cd ..

echo.
echo [2/4] Installing Python dependencies (including PyInstaller)...
call backend\venv\Scripts\activate
pip install pyinstaller >nul
if errorlevel 1 goto error

echo.
echo [3/4] Packaging with PyInstaller (this takes a while)...
python -m PyInstaller imaginaree.spec --noconfirm
if errorlevel 1 goto error

echo.
echo [4/4] Creating output directories...
if not exist "dist\Imaginaree\outputs\images" mkdir "dist\Imaginaree\outputs\images"
if not exist "dist\Imaginaree\outputs\thumbnails" mkdir "dist\Imaginaree\outputs\thumbnails"
if not exist "dist\Imaginaree\models_cache" mkdir "dist\Imaginaree\models_cache"

echo.
echo ========================================
echo   Build complete!
echo ========================================
echo.
echo   Your app is at:
echo   dist\Imaginaree\Imaginaree.exe
echo.
echo   You can move the whole dist\Imaginaree
echo   folder anywhere and run the .exe inside.
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo   BUILD FAILED
echo ========================================
echo See error messages above.
pause
exit /b 1
