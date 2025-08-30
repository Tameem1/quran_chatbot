# Quran Chatbot API

This document describes how to use the Quran Chatbot through its REST API interface.

## Overview

The Quran Chatbot API provides programmatic access to the Quranic linguistic analysis chatbot. It allows you to ask questions about Arabic words, roots, and linguistic features found in the Quran through HTTP endpoints.

## Features

- **Arabic Word Analysis**: Get meanings and explanations of Quranic words
- **Root-based Search**: Find information about word roots and their occurrences
- **Morphological Analysis**: Analyze word forms and structures
- **Frequency Counting**: Count how often words or roots appear
- **Verse Extraction**: Extract specific verses containing certain words or roots
- **Linguistic Comparison**: Compare different words and their meanings

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python api.py
```

The server will start on `http://localhost:8000`

### 3. Access API Documentation

Open your browser and go to:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Health Check

#### GET `/health`
Check if the API is operational.

**Response:**
```json
{
  "status": "healthy",
  "message": "Quran Chatbot API is operational"
}
```

### Core Functionality

#### POST `/ask`
Ask a question to the chatbot.

**Request Body:**
```json
{
  "question": "ما معنى كلمة غفر؟",
  "verbose": false
}
```

**Response:**
```json
{
  "answer": "كلمة 'غفر' تعني...",
  "question_type": "word_meaning",
  "target_entity": "غفر",
  "surah_filter": null,
  "processing_time": 2.345
}
```

#### POST `/ask/stream`
Ask a question with streaming status updates.

**Request Body:**
```json
{
  "question": "كم مرة ورد جذر سجد في القرآن؟",
  "verbose": false
}
```

**Response:**
```json
{
  "answer": "جذر 'سجد' ورد 15 مرة في القرآن...",
  "status_updates": [
    "[Pipeline] Received question: كم مرة ورد جذر سجد في القرآن؟",
    "[Pipeline] Stage-1 ▶️  Classifying question ...",
    "[Pipeline]         ↳ Detected type  : frequency_word_root"
  ],
  "total_stages": 5
}
```

### Information Endpoints

#### GET `/capabilities`
Get information about what the chatbot can do.

**Response:**
```json
{
  "supported_languages": ["Arabic"],
  "question_types": [
    "word_meaning",
    "frequency_word_root",
    "difference_two_words",
    "root_ayah_extraction",
    "morphology",
    "dictionary_lookup"
  ],
  "features": [
    "Arabic word analysis",
    "Root-based search",
    "Morphological analysis",
    "Frequency counting",
    "Verse extraction",
    "Linguistic comparison"
  ],
  "data_sources": [
    "Quran text",
    "Arabic dictionary",
    "Morphological analysis",
    "Root analysis"
  ]
}
```

#### GET `/examples`
Get example questions that can be asked to the chatbot.

**Response:**
```json
{
  "examples": [
    {
      "arabic": "ما معنى كلمة غفر؟",
      "english": "What is the meaning of the word 'ghafara'?",
      "type": "word_meaning"
    },
    {
      "arabic": "كم مرة ورد جذر سجد في القرآن؟",
      "english": "How many times does the root 'sajada' appear in the Quran?",
      "type": "frequency_word_root"
    }
  ],
  "total": 5,
  "note": "These are example questions in Arabic that demonstrate the chatbot's capabilities."
}
```

## Usage Examples

### Python

```python
import requests

# Ask a question
response = requests.post("http://localhost:8000/ask", json={
    "question": "ما معنى كلمة غفر؟"
})

if response.status_code == 200:
    result = response.json()
    print(f"Answer: {result['answer']}")
    print(f"Processing time: {result['processing_time']}s")
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/ask', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        question: 'ما معنى كلمة غفر؟'
    })
});

const result = await response.json();
console.log(`Answer: ${result.answer}`);
console.log(`Processing time: ${result.processing_time}s`);
```

### cURL

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "ما معنى كلمة غفر؟"}'
```

## Question Types

The chatbot supports several types of questions:

1. **word_meaning**: Ask about the meaning of a specific word
   - Example: "ما معنى كلمة غفر؟"

2. **frequency_word_root**: Ask how often a root appears
   - Example: "كم مرة ورد جذر سجد في القرآن؟"

3. **difference_two_words**: Compare two words
   - Example: "ما الفرق بين كلمة عقل وكلمة فهم؟"

4. **root_ayah_extraction**: Extract verses containing a root
   - Example: "استخرج جميع الآيات التي تحتوي على جذر كتب"

5. **morphology**: Ask about morphological forms
   - Example: "ما هي الصيغ الصرفية لكلمة علم؟"

6. **dictionary_lookup**: Look up dictionary definitions
   - Example: "ما هو تعريف كلمة قرآن؟"

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid input)
- **500**: Internal server error

Error responses include a detail message:

```json
{
  "detail": "Error processing question: Invalid input format"
}
```

## Testing

Run the test script to verify the API is working:

```bash
python test_api.py
```

Make sure the API server is running before executing the tests.

## Configuration

### Environment Variables

The API uses the same environment variables as the main chatbot:

- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: Model to use (defaults to gpt-4o-mini-2024-07-18)

### Server Configuration

The API server runs on:
- **Host**: `0.0.0.0` (accessible from any IP)
- **Port**: `8000`
- **Reload**: Enabled for development

To change these settings, modify the `uvicorn.run()` call in `api.py`.

## Performance

- **Concurrent Requests**: The API can handle multiple concurrent requests using a thread pool
- **Processing Time**: Typical response times range from 1-5 seconds depending on question complexity
- **Memory Usage**: The pipeline is initialized once and reused for all requests

## Security Considerations

- **CORS**: Currently allows all origins (`*`) - configure appropriately for production
- **Input Validation**: All inputs are validated using Pydantic models
- **Error Handling**: Sensitive information is not exposed in error messages

## Production Deployment

For production use, consider:

1. **Reverse Proxy**: Use Nginx or Apache as a reverse proxy
2. **Process Manager**: Use systemd, supervisor, or PM2
3. **Environment**: Set `reload=False` in production
4. **Logging**: Configure proper logging levels and output
5. **Monitoring**: Add health checks and metrics
6. **Rate Limiting**: Implement rate limiting for API endpoints

## Troubleshooting

### Common Issues

1. **Port Already in Use**: Change the port in `api.py` or kill the process using port 8000
2. **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Pipeline Errors**: Check that all data files are present in the `data/` directory
4. **API Key Issues**: Verify your OpenAI API key is set correctly

### Debug Mode

Enable debug logging by modifying the logging level in `api.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review the error messages in the response
3. Check the server logs for detailed error information
4. Ensure all dependencies and data files are properly configured
