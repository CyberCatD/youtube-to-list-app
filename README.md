# YouTube to List App

A modern web application for extracting and managing recipes from YouTube videos and other sources including Instagram, TikTok, Facebook, and web pages. Uses Google's Gemini AI to intelligently parse and structure recipe data.

## Features

- **Multi-Source Recipe Import**: Extract recipes from YouTube, Instagram, TikTok, Facebook, and general web pages
- **AI-Powered Extraction**: Uses Google Gemini to intelligently parse ingredients, instructions, and metadata
- **Nutrition Analysis**: Automatic nutritional information calculation using USDA food database
- **Grocery List Generation**: Create consolidated shopping lists from multiple recipes
- **Dark Mode**: Beautiful dark theme with system preference detection
- **Admin Dashboard**: Monitor LLM usage, costs, and recipe statistics
- **Prometheus Metrics**: Built-in observability with custom business metrics

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **SQLAlchemy** ORM with SQLite (dev) / PostgreSQL (prod) support
- **Pydantic Settings** for configuration management
- **Google Gemini AI** for recipe extraction
- **Prometheus** metrics for monitoring

### Frontend
- **React 19** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **TanStack React Query** for data fetching
- **Recharts** for data visualization

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm (or npm/yarn)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd youtube-to-list-app
```

### 2. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
GOOGLE_API_KEY=your_google_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

**Getting API Keys:**
- **Google Gemini API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **YouTube Data API Key**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (enable YouTube Data API v3)

### 3. Backend Setup

```bash
cd youtube_to_list

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn src.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Run the frontend
pnpm dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Prometheus Metrics: http://localhost:8000/metrics

## Configuration

All configuration is managed via environment variables or `.env` file. See `.env.example` for all available options.

### Required Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google Gemini API key for LLM |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./youtube_cards.db` | Database connection URL |
| `API_KEYS` | (empty) | Comma-separated valid API keys for endpoint security |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS allowed origins |
| `LLM_MODEL_NAME` | `gemini-2.5-flash` | Gemini model to use |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `development` | Environment (development/production/testing) |
| `USDA_API_KEY` | `DEMO_KEY` | USDA Food Database API key |

## API Endpoints

### Recipe Operations
- `POST /api/v1/youtube/import` - Import recipe from YouTube URL
- `POST /api/v1/recipes/import-url` - Import recipe from any URL
- `GET /api/v1/recipes` - List all recipes (with pagination and search)
- `GET /api/v1/recipes/{id}` - Get recipe by ID
- `DELETE /api/v1/recipes/{id}` - Delete recipe (soft delete)

### Grocery Lists
- `POST /api/v1/grocery-lists` - Create grocery list from recipes
- `GET /api/v1/grocery-lists` - List all grocery lists
- `GET /api/v1/grocery-lists/{id}` - Get grocery list details

### Admin
- `GET /api/v1/admin/stats` - Get comprehensive admin statistics
- `GET /api/v1/admin/llm-metrics` - Get LLM usage metrics

### Monitoring
- `GET /metrics` - Prometheus metrics endpoint
- `GET /health` - Health check endpoint

## Development

### Running Tests

```bash
cd youtube_to_list

# Run all tests
TESTING=true python3 -m pytest tests/ -v

# Run with coverage
TESTING=true python3 -m pytest tests/ --cov=src --cov-report=html
```

### Code Style

The project follows Python best practices with type hints throughout. Configuration is centralized using Pydantic Settings for type-safe configuration management.

## Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production` for JSON logging
2. Use PostgreSQL by setting `DATABASE_URL`
3. Configure proper `ALLOWED_ORIGINS` for your domain
4. Set up Prometheus to scrape `/metrics` endpoint
5. Consider setting `API_KEYS` for endpoint security

## License

MIT License
