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
echo [1/2] Invoking Python shortcut uninstaller...
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%~dp0create_desktop_shortcut.py" --remove
)

echo.
echo [2/2] Verifying and cleaning any remaining shortcuts...
if exist "%USERPROFILE%\Desktop\Hibernate.lnk" (
    del /f /q "%USERPROFILE%\Desktop\Hibernate.lnk"
)
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Hibernate.lnk" (
    del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Hibernate.lnk"
)

echo.
echo ==============================================================
echo   [SUCCESS] Hibernate shortcuts have been cleanly removed!
echo   (Project files remain in this folder. You can safely delete
echo    this folder if you no longer need the utility.)
echo ==============================================================
echo.
pause
