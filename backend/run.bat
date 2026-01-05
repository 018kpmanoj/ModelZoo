@echo off
echo ========================================
echo    ModelZoo Backend Server
echo ========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Check for .env file
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Creating from template...
    copy env.template .env
    echo Please update .env with your Azure credentials.
    echo.
)

echo.
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

