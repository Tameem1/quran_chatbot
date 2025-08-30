"""
Configuration file for the Quran Chatbot API.
"""

import os
from typing import Optional

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"
API_LOG_LEVEL = os.getenv("API_LOG_LEVEL", "info")

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# Thread Pool Configuration
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini-2024-07-18")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Development vs Production
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def validate_config():
    """Validate that required configuration is present."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    print(f"✅ Configuration validated:")
    print(f"   - API Host: {API_HOST}")
    print(f"   - API Port: {API_PORT}")
    print(f"   - API Reload: {API_RELOAD}")
    print(f"   - Max Workers: {MAX_WORKERS}")
    print(f"   - OpenAI Model: {OPENAI_MODEL}")
    print(f"   - Debug Mode: {DEBUG}")

if __name__ == "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        exit(1)
