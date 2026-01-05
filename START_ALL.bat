@echo off
echo ============================================================
echo           ModelZoo - Multi-LLM Chat System
echo ============================================================
echo.
echo Starting Backend and Frontend servers...
echo.

REM Start Backend in a new window
start "ModelZoo Backend" cmd /k "cd /d "%~dp0backend" && run.bat"

REM Wait a moment for backend to start
timeout /t 5 /nobreak > nul

REM Start Frontend in a new window
start "ModelZoo Frontend" cmd /k "cd /d "%~dp0frontend" && run.bat"

echo.
echo ============================================================
echo  Servers are starting in separate windows...
echo.
echo  Backend API:      http://localhost:8000
echo  API Documentation: http://localhost:8000/docs
echo  Frontend UI:      http://localhost:3000
echo.
echo  Press any key to open the application in your browser...
echo ============================================================

pause > nul
start http://localhost:3000

