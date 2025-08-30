# Quran Chatbot

A sophisticated chatbot for analyzing Quranic text, words, and linguistic features using advanced NLP techniques.

## 🏗️ Project Structure

```
quran_chatbot/
├── api/                          # API package
│   ├── __init__.py              # API package initialization
│   ├── api.py                   # Main FastAPI application
│   ├── config/                  # Configuration package
│   │   ├── __init__.py         # Config package initialization
│   │   ├── config.py            # Configuration management
│   │   └── env.example         # Environment template
│   ├── docs/                    # API documentation
│   │   ├── API_README.md       # Complete API documentation
│   │   └── API_SETUP_SUMMARY.md # Setup summary
│   └── scripts/                 # Utility scripts
│       ├── __init__.py         # Scripts package initialization
│       ├── test_api.py         # API testing script
│       ├── demo_api.py         # Comprehensive demo
│       ├── start_api.sh        # Unix/Mac startup script
│       └── start_api.bat       # Windows startup script
├── pipeline/                     # Core pipeline components
├── services/                     # Service layer
├── data/                        # Data files
├── utils/                       # Utility functions
├── app.py                       # Streamlit web interface
├── main.py                      # Command-line interface
├── run_api.py                   # API entry point
├── start_api.sh                 # Root-level startup script
├── start_api.bat                # Root-level Windows startup
├── test_api.py                  # Root-level test script
├── demo_api.py                  # Root-level demo script
└── requirements.txt              # Dependencies
```

## 🚀 Quick Start

### Web Interface (Streamlit)
```bash
streamlit run app.py
```

### Command Line Interface
```bash
python main.py "ما معنى كلمة غفر؟"
```

### REST API
```bash
# Start the API server
python simple_api.py

# Or use startup scripts
./start_api.sh          # Unix/Mac
start_api.bat           # Windows

# Test the API
python test_api.py

# Run comprehensive demo
python demo_api.py
```

## 🌐 API Access

Once the API server is running:
- **Base URL**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

## 📚 Documentation

- **API Documentation**: `api/docs/API_README.md`
- **Setup Summary**: `api/docs/API_SETUP_SUMMARY.md`
- **Configuration**: `api/config/`

## 🔧 Configuration

1. Copy the environment template:
   ```bash
   cp api/config/env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🧪 Testing

```bash
# Test the API
python test_api.py

# Run comprehensive demo
python demo_api.py

# Manual testing
curl http://localhost:8000/health
```

## 🌟 Features

- **Arabic Word Analysis**: Meanings and explanations of Quranic words
- **Root-based Search**: Information about word roots and occurrences
- **Morphological Analysis**: Word forms and structures
- **Frequency Counting**: Count word/root occurrences
- **Verse Extraction**: Extract verses containing specific words/roots
- **Linguistic Comparison**: Compare different words and meanings
- **REST API**: Full HTTP API for integration
- **Web Interface**: User-friendly Streamlit interface
- **Command Line**: Scriptable command-line interface

## 🔌 API Endpoints

- `GET /health` - Health check
- `POST /ask` - Ask questions to the chatbot
- `POST /ask/stream` - Ask questions with streaming updates
- `GET /capabilities` - Get chatbot capabilities
- `GET /examples` - Get example questions

## 🚀 Production Deployment

For production use:
1. Set `DEBUG=false` in your `.env` file
2. Set `API_RELOAD=false` for production
3. Configure `CORS_ORIGINS` to specific domains
4. Use a reverse proxy (Nginx/Apache)
5. Add process management (systemd/supervisor)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review error messages in responses
3. Check server logs for detailed information
4. Ensure all dependencies and data files are configured 