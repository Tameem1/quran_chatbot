@echo off
REM Quran Chatbot API Startup Script for Windows

echo 🚀 Starting Quran Chatbot API...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if requirements are installed
echo 📦 Checking dependencies...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Some dependencies are missing. Installing...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist .env (
    echo ⚠️  No .env file found. Please create one with your OpenAI API key:
    echo    OPENAI_API_KEY=your_api_key_here
    echo    OPENAI_MODEL=gpt-4o-mini-2024-07-18
)

REM Start the API server
echo 🌐 Starting server on http://localhost:8000
echo 📚 API documentation will be available at:
echo    - Swagger UI: http://localhost:8000/docs
echo    - ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

python api.py

pause
