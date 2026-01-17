from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
import os

from .api.v1.endpoints import youtube, recipes, grocery_lists, admin
from .database import engine, Base
from .scheduler import start_scheduler
from .logging_config import setup_logging, get_logger
from .config import settings

setup_logging()
logger = get_logger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_tables_on_startup():
    """
    Creates database tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="YouTube to Recipe API",
    description="Extract structured recipe data from YouTube videos",
    version="1.0.0"
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["monitoring"])

limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PATCH", "PUT"],
    allow_headers=["*"],
    max_age=3600,
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting YouTube to Recipe API", extra={"version": "1.0.0"})
    create_tables_on_startup()
    start_scheduler()
    logger.info("Application startup complete")

@app.get("/", tags=["root"])
def root(request: Request):
    """Welcome endpoint with API information"""
    api_data = {
        "message": "YouTube to Recipe API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "recipes": {
                "list": "GET /api/v1/recipes/",
                "get": "GET /api/v1/recipes/{recipe_id}",
                "delete": "DELETE /api/v1/recipes/{recipe_id}"
            },
            "youtube": {
                "process": "POST /api/v1/youtube/process-youtube-url"
            }
        },
        "security": {
            "rate_limiting": "200/day, 50/hour (10/min for POST/DELETE)",
            "authentication": "Optional API key via X-API-Key header",
            "cors": "Enabled for configured origins"
        }
    }
    
    # Return HTML for browser requests, JSON for API clients
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>YouTube to Recipe API</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 40px 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    margin-top: 0;
                }
                h2 {
                    color: #34495e;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                .endpoint {
                    background: #f8f9fa;
                    padding: 12px 16px;
                    margin: 8px 0;
                    border-radius: 4px;
                    border-left: 4px solid #3498db;
                }
                .method {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 0.85em;
                    margin-right: 8px;
                }
                .get { background: #61affe; color: white; }
                .post { background: #49cc90; color: white; }
                .delete { background: #f93e3e; color: white; }
                .security-badge {
                    background: #ff9800;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                    display: inline-block;
                    margin: 4px 0;
                    font-size: 0.9em;
                }
                code {
                    background: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Monaco', 'Courier New', monospace;
                }
                a {
                    color: #3498db;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
                .version {
                    color: #7f8c8d;
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🍳 YouTube to Recipe API</h1>
                <p class="version">Version 1.0.0</p>
                
                <h2>📚 Documentation</h2>
                <div class="endpoint">
                    <a href="/docs" target="_blank">📖 Interactive API Docs (Swagger UI)</a>
                </div>
                <div class="endpoint">
                    <a href="/redoc" target="_blank">📄 API Documentation (ReDoc)</a>
                </div>
                
                <h2>🔍 Endpoints</h2>
                
                <h3>Health Check</h3>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <code>/health</code> - Check API status
                </div>
                
                <h3>Recipes</h3>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <code>/api/v1/recipes/</code> - List all recipes
                </div>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <code>/api/v1/recipes/{recipe_id}</code> - Get specific recipe
                </div>
                <div class="endpoint">
                    <span class="method delete">DELETE</span>
                    <code>/api/v1/recipes/{recipe_id}</code> - Delete recipe
                    <span class="security-badge">🔒 Requires API Key</span>
                </div>
                
                <h3>YouTube Processing</h3>
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <code>/api/v1/youtube/process-youtube-url</code> - Extract recipe from YouTube video
                    <span class="security-badge">🔒 Requires API Key</span>
                </div>
                
                <h2>🔐 Security</h2>
                <ul>
                    <li><strong>Rate Limiting:</strong> 200/day, 50/hour (10/min for POST/DELETE)</li>
                    <li><strong>Authentication:</strong> Optional API key via <code>X-API-Key</code> header</li>
                    <li><strong>CORS:</strong> Enabled for configured origins</li>
                </ul>
                
                <h2>🚀 Quick Start</h2>
                <p>For detailed API usage, visit the <a href="/docs">interactive documentation</a>.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    return api_data

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

app.include_router(youtube.router, prefix="/api/v1/youtube", tags=["youtube"])
app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])
app.include_router(grocery_lists.router, prefix="/api/v1/grocery-lists", tags=["grocery-lists"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")