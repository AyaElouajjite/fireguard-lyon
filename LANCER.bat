@echo off
title FireGuard Lyon
cd /d "%~dp0"

echo.
echo  ============================================
echo    FireGuard Lyon - Lancement automatique
echo  ============================================
echo.

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" launch.py
) else (
    python launch.py
)

if errorlevel 1 pause
