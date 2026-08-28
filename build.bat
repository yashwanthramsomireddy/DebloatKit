@echo off
title DebloatKit -- Build Script
color 0A

echo.
echo  =============================================
echo    DebloatKit v1.0 -- Build Script
echo    TeamExyKings - Yashwanth Ram Somireddy
echo  =============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python 3.11+ from https://python.org
    pause & exit /b 1
)

REM Install dependencies
echo  [1/4] Installing dependencies...
pip install customtkinter pyinstaller --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause & exit /b 1
)
echo        Done.

REM Generate installer assets if not present
if not exist "assets\installer_side_164x314.bmp" (
    echo  [1b]   Generating installer assets...
    python gen_bitmaps.py
)

REM Clean previous build
echo  [2/4] Cleaning previous build...
if exist "dist\DebloatKit.exe" del /f /q "dist\DebloatKit.exe"
if exist "build" rmdir /s /q "build"
if exist "DebloatKit.spec" del /f /q "DebloatKit.spec"
echo        Done.

REM Build exe
echo  [3/4] Building DebloatKit.exe...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "DebloatKit" ^
    --uac-admin ^
    --add-data "data;data" ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL._tkinter_finder ^
    --collect-all customtkinter ^
    DebloatKit.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. Check output above.
    pause & exit /b 1
)

REM Copy assets
echo  [4/4] Copying assets to dist\...
if not exist "dist\backups" mkdir "dist\backups"
if exist "assets" xcopy /e /i /q "assets" "dist\assets" >nul

echo.
echo  =============================================
echo    BUILD SUCCESSFUL!
echo    Output: dist\DebloatKit.exe
echo  =============================================
echo.
echo  Next step: run installer\build_installer.bat
echo  to create the Windows setup .exe
echo.
pause
