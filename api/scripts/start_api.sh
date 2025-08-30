#!/bin/bash

# Quran Chatbot API Startup Script

echo "🚀 Starting Quran Chatbot API..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn" &> /dev/null; then
    echo "⚠️  Some dependencies are missing. Installing..."
    pip3 install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Please create one with your OpenAI API key:"
    echo "   OPENAI_API_KEY=your_api_key_here"
    echo "   OPENAI_MODEL=gpt-4o-mini-2024-07-18"
fi

# Start the API server
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API documentation will be available at:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 api.py
