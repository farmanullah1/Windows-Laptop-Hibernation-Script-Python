@echo off
setlocal enabledelayedexpansion

echo ==============================================================
echo   Windows Laptop Hibernation Utility - One-Click Setup
echo ==============================================================
echo.

:: 1. Verify Python availability
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in system PATH.
    echo Please install Python 3.10+ from https://www.python.org and ensure
    echo "Add python.exe to PATH" is checked during installation.
    pause
    exit /b 1
)

echo [1/3] Python detected:
python --version
echo.

:: 2. Install Python requirements
echo [2/3] Installing dependencies from requirements.txt...
python -m pip install -r "%~dp0requirements.txt" --quiet
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Failed to install pip requirements. Attempting to proceed...
) else (
    echo       Dependencies verified.
)
echo.

:: 3. Generate icon and create desktop shortcut
echo [3/3] Creating Desktop shortcut and setting up Hotkey (Ctrl+Alt+H)...
python "%~dp0create_desktop_shortcut.py"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create desktop shortcut.
    pause
    exit /b 1
)

echo.
echo ==============================================================
echo   [SUCCESS] Setup completed successfully!
echo   - Desktop Icon: "Hibernate" on your Desktop
echo   - Global Hotkey: Ctrl + Alt + H
echo   - Configuration: Edit config.json to customize countdown/hotkey
echo ==============================================================
echo.
pause
