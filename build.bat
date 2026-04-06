@echo off
echo ========================================
echo   Building Imaginaree Desktop App
echo ========================================
echo.

echo [1/4] Building frontend...
cd frontend
call npm run build
cd ..

echo.
echo [2/4] Installing Python dependencies...
cd backend
call venv\Scripts\activate
pip install -r requirements.txt
cd ..

echo.
echo [3/4] Packaging with PyInstaller...
cd backend
call venv\Scripts\activate
cd ..
python -m PyInstaller imaginaree.spec --noconfirm

echo.
echo [4/4] Creating output directories...
if not exist "dist\Imaginaree\outputs\images" mkdir "dist\Imaginaree\outputs\images"
if not exist "dist\Imaginaree\outputs\thumbnails" mkdir "dist\Imaginaree\outputs\thumbnails"
if not exist "dist\Imaginaree\models_cache" mkdir "dist\Imaginaree\models_cache"

echo.
echo ========================================
echo   Build complete!
echo   Run: dist\Imaginaree\Imaginaree.exe
echo ========================================
pause
