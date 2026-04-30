@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   video-full setup
echo ============================================
echo.

echo [1/3] Initializing git submodules...
git submodule update --init --recursive
if errorlevel 1 (
    echo [ERROR] git submodule failed. Is git installed?
    pause
    exit /b 1
)
echo.

echo [2/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo.

echo [3/3] Running interactive setup wizard...
python "%~dp0video-full.py" setup
echo.

pause
