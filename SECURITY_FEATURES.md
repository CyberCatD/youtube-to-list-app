# Security Features Quick Reference

## ✅ Implemented (Phase 1 - Complete)

### 1. API Rate Limiting
- **Global**: 200 requests/day, 50 requests/hour per IP
- **POST /api/v1/youtube/process-youtube-url**: 10 requests/minute
- **DELETE /api/v1/recipes/{id}**: 10 requests/minute
- **Response**: 429 Too Many Requests when exceeded

### 2. CORS Protection
- **Configured Origins**: Via `ALLOWED_ORIGINS` env var (default: http://localhost:5173)
- **Allowed Methods**: GET, POST, DELETE
- **Credentials**: Enabled
- **Cache**: 1 hour

### 3. YouTube URL Validation
- **Supported Formats**:
  - `https://www.youtube.com/watch?v={video_id}`
  - `https://youtu.be/{video_id}`
  - `https://www.youtube.com/embed/{video_id}`
- **Sanitization**: Removes tracking parameters
- **Response**: 400 Bad Request for invalid URLs

### 4. API Key Authentication (Optional)
- **Status**: Disabled by default (empty API_KEYS)
- **Protected Endpoints**:
  - POST /api/v1/youtube/process-youtube-url
  - DELETE /api/v1/recipes/{id}
- **Public Endpoints**: All GET operations
- **Header**: `X-API-Key: your-key-here`
- **Response**: 401 Unauthorized for invalid/missing keys

### 5. Structured Logging
- **Replaced**: All 27 debug print() statements
- **Format**: `timestamp - module - level - message`
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Configuration**: Via `LOG_LEVEL` env var
- **Security**: No sensitive data in logs

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
GOOGLE_API_KEY=your_google_api_key
YOUTUBE_API_KEY=your_youtube_api_key

# Security (Optional)
API_KEYS=                           # Comma-separated keys, empty = disabled
ALLOWED_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
```

## 📝 Testing

### Test Rate Limiting
```bash
# Make 11 requests in quick succession
for i in {1..11}; do 
  curl -s -w "\nStatus: %{http_code}\n" \
    -X POST http://localhost:8000/api/v1/youtube/process-youtube-url \
    -H "Content-Type: application/json" \
    -d '{"youtube_url": "https://youtube.com/watch?v=test"}'
done
```

### Test URL Validation
```bash
# Should fail (400)
curl -X POST http://localhost:8000/api/v1/youtube/process-youtube-url \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "not-a-youtube-url"}'

# Should pass validation
curl -X POST http://localhost:8000/api/v1/youtube/process-youtube-url \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Test API Key Auth
```bash
# Enable auth: Set API_KEYS=test-key-123 in .env, restart server

# Should fail (401)
curl -X POST http://localhost:8000/api/v1/youtube/process-youtube-url \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://youtube.com/watch?v=test"}'

# Should succeed (or pass validation)
curl -X POST http://localhost:8000/api/v1/youtube/process-youtube-url \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d '{"youtube_url": "https://youtube.com/watch?v=test"}'
```

## 🚀 Running the Server

```bash
cd youtube_to_list
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Modified Files

- `src/main.py` - Added CORS, rate limiting, logging config
- `src/api/v1/endpoints/youtube.py` - Added validation, auth, rate limit
- `src/api/v1/endpoints/recipes.py` - Added auth, rate limit, logging
- `src/services/recipe_service.py` - Replaced prints with logging
- `src/services/youtube_service.py` - Replaced prints with logging
- `src/services/llm_service.py` - Replaced prints with logging
- `src/validators.py` - NEW: URL validation
- `src/auth.py` - NEW: API key authentication
- `requirements.txt` - Added security dependencies

## ⚠️ Known Issues

- **google.generativeai deprecation warning**: Non-breaking, can be addressed later by migrating to `google.genai`

---
**Last Updated**: 2026-01-03
**Phase**: 1 (Security Hardening) - Complete ✓
