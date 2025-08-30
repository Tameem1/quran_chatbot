"""
Configuration package for the Quran Chatbot API.
"""

from .config import *

__all__ = [
    'API_HOST', 'API_PORT', 'API_RELOAD', 'API_LOG_LEVEL',
    'CORS_ORIGINS', 'CORS_ALLOW_CREDENTIALS', 'MAX_WORKERS',
    'OPENAI_API_KEY', 'OPENAI_MODEL', 'LOG_LEVEL', 'LOG_FORMAT',
    'DEBUG', 'validate_config'
]
