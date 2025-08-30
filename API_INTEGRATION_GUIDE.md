# Quran Chatbot API Integration Guide

## 🎯 Quick Reference

**Base URL**: `http://localhost:8000` (dev) or your server URL (prod)  
**Protocol**: HTTP REST API  
**Data Format**: JSON  
**Authentication**: None (public API)  
**Documentation**: `/docs` (Swagger UI) or `/redoc`

## 🔌 Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/health` | GET | Health check | `{"status": "healthy", "message": "..."}` |
| `/capabilities` | GET | Supported features | Features, question types, data sources |
| `/examples` | GET | Sample questions | Arabic questions with English translations |
| `/ask` | POST | Ask a question | Answer with processing time |
| `/ask/stream` | POST | Ask with streaming | Answer + real-time status updates |

## 📋 Question Types

1. **word_meaning** - Word meanings
2. **frequency_word_root** - Count root occurrences  
3. **difference_two_words** - Compare two words
4. **root_ayah_extraction** - Extract verses containing roots
5. **morphology** - Morphological forms
6. **dictionary_lookup** - Dictionary definitions

## 🚀 Integration Examples

### Python - Basic Client
```python
import requests

class QuranChatbotClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def ask_question(self, question, verbose=False):
        payload = {"question": question, "verbose": verbose}
        response = self.session.post(f"{self.base_url}/ask", json=payload)
        response.raise_for_status()
        return response.json()
    
    def health_check(self):
        response = self.session.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = QuranChatbotClient()
result = client.ask_question("ما معنى كلمة غفر؟")
print(f"Answer: {result['answer']}")
print(f"Processing time: {result['processing_time']}s")
```

### JavaScript - Basic Client
```javascript
class QuranChatbotClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async askQuestion(question, verbose = false) {
        const response = await fetch(`${this.baseUrl}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, verbose })
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    }
}

// Usage
const client = new QuranChatbotClient();
client.askQuestion('ما معنى كلمة غفر؟')
    .then(result => console.log('Answer:', result.answer))
    .catch(error => console.error('Error:', error));
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Ask question
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "ما معنى كلمة غفر؟"}'

# Get capabilities
curl http://localhost:8000/capabilities
```

## 🔧 Configuration

### Environment Variables
```bash
export QURAN_API_BASE_URL="http://localhost:8000"
export QURAN_API_TIMEOUT="30"
export QURAN_API_MAX_RETRIES="3"
```

### Request Format
```json
{
  "question": "ما معنى كلمة غفر؟",
  "verbose": false
}
```

### Response Format
```json
{
  "answer": "كلمة 'غفر' تعني...",
  "question_type": "word_meaning",
  "target_entity": "غفر",
  "surah_filter": null,
  "processing_time": 2.345
}
```

## 🚀 Integration Patterns

### Web App (React)
```jsx
const askQuestion = async () => {
    try {
        const response = await fetch('http://localhost:8000/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question.trim() })
        });
        
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        
        const result = await response.json();
        setAnswer(result.answer);
    } catch (err) {
        setError(err.message);
    }
};
```

### Mobile App (React Native)
```jsx
const askQuestion = async () => {
    try {
        const response = await fetch('http://localhost:8000/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question.trim() })
        });

        if (!response.ok) throw new Error(`API Error: ${response.status}`);

        const result = await response.json();
        setAnswer(result.answer);
    } catch (error) {
        Alert.alert('خطأ', error.message);
    }
};
```

### Chatbot (Discord Bot)
```python
async def ask_quran(ctx, *, question):
    async with aiohttp.ClientSession() as session:
        payload = {"question": question}
        async with session.post(
            f"{self.api_base}/ask",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                embed = discord.Embed(
                    title="Quran Chatbot Answer",
                    description=result['answer']
                )
                await ctx.send(embed=embed)
```

## 🔒 Security & Best Practices

### Rate Limiting
```python
class RateLimiter:
    def __init__(self, max_requests=100, time_window=3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]
        user_requests[:] = [req_time for req_time in user_requests if now - req_time < self.time_window]
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        return True
```

### Input Validation
```python
def validate_question(question):
    if not question or not isinstance(question, str):
        raise ValueError("Question must be a non-empty string")
    
    if len(question.strip()) < 3 or len(question.strip()) > 500:
        raise ValueError("Question must be 3-500 characters")
    
    # Check for harmful content
    harmful_patterns = [r'<script.*?>.*?</script>', r'javascript:', r'data:text/html']
    for pattern in harmful_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            raise ValueError("Question contains harmful content")
    
    return question.strip()
```

### Error Handling
```python
def ask_question_with_retry(question, max_retries=3):
    for attempt in range(max_retries):
        try:
            return ask_question(question)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
```

## 📊 Monitoring

### Request Logging
```python
def log_request(question, response_time, success, error=None):
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "response_time": response_time,
        "success": success,
        "error": error
    }
    
    if success:
        logger.info(f"Successful request: {log_data}")
    else:
        logger.error(f"Failed request: {log_data}")
```

### Performance Monitoring
```python
class PerformanceMonitor:
    def __init__(self, max_samples=1000):
        self.response_times = deque(maxlen=max_samples)
        self.error_count = 0
        self.success_count = 0
    
    def record_request(self, response_time, success):
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_stats(self):
        if not self.response_times:
            return {}
        
        return {
            "total_requests": len(self.response_times),
            "success_rate": self.success_count / (self.success_count + self.error_count),
            "avg_response_time": statistics.mean(self.response_times),
        }
```

## 🚀 Production Deployment

### Environment Setup
```bash
export QURAN_API_BASE_URL="https://your-api-domain.com"
export QURAN_API_TIMEOUT="60"
export QURAN_API_MAX_RETRIES="5"
export QURAN_API_RATE_LIMIT="100"
export QURAN_API_RATE_WINDOW="3600"
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "simple_api.py"]
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quran-chatbot-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: quran-chatbot-api
  template:
    spec:
      containers:
      - name: quran-chatbot-api
        image: your-registry/quran-chatbot-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        - name: API_RELOAD
          value: "false"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
```

## 🔍 Testing

### Unit Tests
```python
@patch('requests.Session.post')
def test_ask_question_success(self, mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "answer": "Test answer",
        "processing_time": 1.5
    }
    mock_post.return_value = mock_response
    
    result = self.client.ask_question("Test question")
    self.assertEqual(result["answer"], "Test answer")
```

### Integration Tests
```python
def test_api_health(api_client):
    result = api_client.health_check()
    assert result["status"] == "healthy"

def test_api_ask_question(api_client):
    result = api_client.ask_question("ما معنى كلمة غفر؟")
    assert "answer" in result
    assert "processing_time" in result
```

## 📚 Key Points

1. **Start simple** - Basic integration first, add complexity later
2. **Handle errors gracefully** - Implement retries and user feedback
3. **Validate input** - Check questions before sending to API
4. **Rate limit** - Prevent abuse with request limiting
5. **Monitor performance** - Track success rates and response times
6. **Use HTTPS in production** - Secure all communications
7. **Log everything** - For debugging and monitoring

## 🎯 Ready to Integrate!

The API is production-ready and handles real-world usage. All endpoints are tested and working. Start with the basic examples and build up to advanced features like streaming, batch processing, and monitoring.

**For questions**: Check `/docs` endpoint or project repository.
