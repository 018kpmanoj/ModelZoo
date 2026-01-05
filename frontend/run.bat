@echo off
echo ========================================
echo    ModelZoo Frontend Server
echo ========================================
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo.
echo Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo.

npm start

