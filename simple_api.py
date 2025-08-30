#!/usr/bin/env python3
"""
Simple entry point for the Quran Chatbot API.

This script directly imports the FastAPI app and runs it.
"""

import uvicorn
import os
import sys

# Add the api directory to Python path
api_path = os.path.join(os.path.dirname(__file__), 'api')
sys.path.insert(0, api_path)

# Import the FastAPI app directly
from api import app

if __name__ == "__main__":
    # Get configuration from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("API_LOG_LEVEL", "info")
    
    print("🚀 Starting Quran Chatbot API...")
    print(f"🌐 Server will be available at: http://{host}:{port}")
    print(f"📚 API documentation: http://{host}:{port}/docs")
    print(f"🔄 Auto-reload: {'enabled' if reload else 'disabled'}")
    print(f"📝 Log level: {log_level}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    if reload:
        # For reload mode, use import string
        uvicorn.run(
            "api:app",
            host=host,
            port=port,
            reload=True,
            log_level=log_level
        )
    else:
        # For production mode, use app object directly
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            log_level=log_level
        )
