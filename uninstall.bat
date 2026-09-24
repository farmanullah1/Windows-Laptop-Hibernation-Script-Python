@echo off
setlocal enabledelayedexpansion

echo ==============================================================
echo   Windows Laptop Hibernation Utility - Clean Uninstaller
echo ==============================================================
echo.

set /p CONFIRM="Are you sure you want to remove the Hibernate shortcuts? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo [ABORTED] Uninstallation cancelled by user.
    pause
    exit /b 0
)

echo.
echo [1/3] Removing Desktop shortcut...
set "DESKTOP_LNK=%USERPROFILE%\Desktop\Hibernate.lnk"
if exist "%DESKTOP_LNK%" (
    del /f /q "%DESKTOP_LNK%"
    echo       Removed %DESKTOP_LNK%
) else (
    echo       Desktop shortcut not found.
)

echo.
echo [2/3] Removing Start Menu shortcut...
set "START_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Hibernate.lnk"
if exist "%START_LNK%" (
    del /f /q "%START_LNK%"
    echo       Removed %START_LNK%
) else (
    echo       Start Menu shortcut not found.
)

echo.
echo [3/3] Cleanup completed.
echo.
echo ==============================================================
echo   [SUCCESS] Hibernate shortcuts have been cleanly removed!
echo   (Project files remain in this folder. You can safely delete
echo    this folder if you no longer need the utility.)
echo ==============================================================
echo.
pause
