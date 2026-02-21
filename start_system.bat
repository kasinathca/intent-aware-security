@echo off
title NIC Security Operations Center - System Launcher
cls
echo ===============================================================================
echo      NATIONAL INFORMATICS CENTRE - SECURITY SIMULATION STARTUP
echo ===============================================================================
echo.
echo [1/3] Starting API Gateway and Web Server (app.py)...
start "NIC API GATEWAY" /min cmd /c "python app.py"

echo [2/3] Waiting for server initialization (5 seconds)...
timeout /t 5 /nobreak >nul

echo [3/3] Opening Interfaces in Browser...
timeout /t 2 /nobreak >nul

:: Open System 1: Government Portal
start http://localhost:8000/portal/index.html

:: Open System 2: Hacker Console
start http://localhost:8000/hacker/index.html

:: Open System 3: Security Dashboard (NEW HTML Version)
start http://localhost:8000/dashboard/index.html

echo.
echo ===============================================================================
echo      SYSTEM ONLINE - ALL MODULES ACTIVE
echo ===============================================================================
echo.
echo [INFO] API Gateway Running at http://localhost:8000
echo [INFO] Dashboard Running at http://localhost:8000/dashboard/index.html
echo.
echo Press any key to shutdown the system...
pause >nul

:: Cleanup on exit
taskkill /F /IM python.exe /T >nul
echo System Shutdown Complete.
