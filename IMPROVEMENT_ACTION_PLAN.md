# YouTube-to-List App: Improvement Action Plan

**Created:** 2026-01-03  
**Status:** Planning  
**Goal:** Transform MVP into production-ready application

---

## Executive Summary

This action plan addresses critical security, scalability, and reliability gaps in the YouTube-to-List recipe extraction application. Implementation is structured in 9 phases over an estimated timeline, prioritizing security and data integrity first.

**Estimated Total Effort:** 15-20 development days  
**Risk Level:** Medium (breaking changes in database migration)  
**Dependencies:** None (can proceed immediately)

---

## Phase 1: Security Hardening 🔴 CRITICAL
**Priority:** URGENT  
**Effort:** 1-2 days  
**Risk:** Low

### Objectives
Secure the application against common vulnerabilities and implement access controls.

### Tasks

#### 1.1 Add API Rate Limiting
**File:** `youtube_to_list/src/main.py`

```python
# Install dependency
pip install slowapi

# Implementation
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@limiter.limit("10/minute")
@router.post("/process-youtube-url")
def process_youtube_url(...):
    ...
```

**Acceptance Criteria:**
- [ ] Rate limiting active on all POST/DELETE endpoints
- [ ] 429 status code returned when limit exceeded
- [ ] Per-IP tracking working correctly

---

#### 1.2 Add CORS Middleware
**File:** `youtube_to_list/src/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

**Acceptance Criteria:**
- [ ] CORS headers present in responses
- [ ] Frontend can communicate with backend
- [ ] Origins configurable via environment variable

---

#### 1.3 Add YouTube URL Validation
**File:** `youtube_to_list/src/validators.py` (NEW)

```python
import re
from typing import Optional

YOUTUBE_URL_PATTERNS = [
    r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}',
    r'^https?://youtu\.be/[\w-]{11}',
    r'^https?://(?:www\.)?youtube\.com/embed/[\w-]{11}',
]

def validate_youtube_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validates YouTube URL format and extracts video ID.
    Returns (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    for pattern in YOUTUBE_URL_PATTERNS:
        if re.match(pattern, url):
            return True, None
    
    return False, "Invalid YouTube URL format"

def sanitize_url(url: str) -> str:
    """Remove tracking parameters and normalize URL"""
    return url.split('&')[0]  # Remove tracking params
```

**Update:** `youtube_to_list/src/api/v1/endpoints/youtube.py`
```python
from src.validators import validate_youtube_url, sanitize_url

@router.post("/process-youtube-url")
def process_youtube_url(request: YouTubeProcessRequestSchema, ...):
    is_valid, error = validate_youtube_url(request.youtube_url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    sanitized_url = sanitize_url(request.youtube_url)
    # ... proceed with sanitized_url
```

**Acceptance Criteria:**
- [ ] Invalid URLs rejected with 400 error
- [ ] Only YouTube domains accepted
- [ ] URL sanitization removes tracking params

---

#### 1.4 Remove Debug Print Statements
**Files:** All Python files in `src/`

**Search and destroy:**
```bash
grep -r "print(" youtube_to_list/src/
# Replace with proper logging (see Phase 6)
```

**Acceptance Criteria:**
- [ ] No `print()` statements in production code
- [ ] Temporary logging added where needed
- [ ] No sensitive data in logs

---

#### 1.5 Add API Key Authentication
**File:** `youtube_to_list/src/auth.py` (NEW)

```python
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import secrets

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Store in environment variable
VALID_API_KEYS = set(os.getenv("API_KEYS", "").split(","))

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return api_key
```

**Update endpoints:**
```python
from src.auth import verify_api_key

@router.post("/process-youtube-url", dependencies=[Depends(verify_api_key)])
def process_youtube_url(...):
    ...
```

**Acceptance Criteria:**
- [ ] API key required for POST/DELETE operations
- [ ] GET operations remain public
- [ ] 401 returned for invalid keys
- [ ] Keys stored in environment variables

---

## Phase 2: Database Migration 🔴 CRITICAL
**Priority:** HIGH  
**Effort:** 2-3 days  
**Risk:** MEDIUM (requires data migration)

### Objectives
Implement proper database migrations and optimize query performance.

### Tasks

#### 2.1 Install and Configure Alembic
```bash
cd youtube_to_list
pip install alembic
alembic init alembic
```

**File:** `alembic.ini`
```ini
sqlalchemy.url = # Will be set dynamically from config
```

**File:** `alembic/env.py`
```python
from src.database import Base
from src.models import Recipe, Ingredient, RecipeIngredient, Instruction
from src.config import SQLALCHEMY_DATABASE_URL

config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
target_metadata = Base.metadata
```

**Create initial migration:**
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Acceptance Criteria:**
- [ ] Alembic successfully initialized
- [ ] Initial migration captures current schema
- [ ] Can apply/rollback migrations
- [ ] Migration history tracked in `alembic_version` table

---

#### 2.2 Add Database Indexes
**File:** `alembic/versions/XXXXX_add_performance_indexes.py`

```python
def upgrade():
    op.create_index('ix_recipes_category', 'recipes', ['category'])
    op.create_index('ix_recipes_cuisine', 'recipes', ['cuisine'])
    op.create_index('ix_recipes_created_at', 'recipes', ['created_at'])
    op.create_index('ix_ingredients_name_lower', 'ingredients', [sa.text('lower(name)')])

def downgrade():
    op.drop_index('ix_recipes_category')
    op.drop_index('ix_recipes_cuisine')
    op.drop_index('ix_recipes_created_at')
    op.drop_index('ix_ingredients_name_lower')
```

**Update models:**
```python
class Recipe(Base):
    category = Column(String, nullable=True, index=True)
    cuisine = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

**Acceptance Criteria:**
- [ ] Indexes created via migration
- [ ] Query performance improved (benchmark with EXPLAIN)
- [ ] Indexes documented in schema

---

#### 2.3 Prepare PostgreSQL Migration Path
**File:** `youtube_to_list/src/database.py`

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Support both SQLite (dev) and PostgreSQL (prod)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DB_PATH}"
)

connect_args = {}
pool_config = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL connection pooling
    pool_config = {
        "poolclass": QueuePool,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **pool_config
)
```

**Create migration guide:**
**File:** `POSTGRES_MIGRATION.md` (NEW)
```markdown
# PostgreSQL Migration Guide

## Prerequisites
1. PostgreSQL 14+ installed
2. Create database: `createdb youtube_recipes`

## Migration Steps
1. Export SQLite data: `sqlite3 youtube_cards.db .dump > backup.sql`
2. Update DATABASE_URL in .env
3. Run migrations: `alembic upgrade head`
4. Import data (if needed): Use pgloader or custom script
5. Verify data integrity

## Rollback Plan
Keep SQLite backup for 30 days after migration.
```

**Acceptance Criteria:**
- [ ] Code supports both SQLite and PostgreSQL
- [ ] Migration guide documented
- [ ] Connection pooling configured for PostgreSQL
- [ ] Can switch databases via environment variable

---

## Phase 3: Reliability Improvements 🔴 HIGH
**Priority:** HIGH  
**Effort:** 2 days  
**Risk:** LOW

### Objectives
Add retry logic, error recovery, and response validation.

### Tasks

#### 3.1 Add Retry Logic with Tenacity
```bash
pip install tenacity
```

**File:** `youtube_to_list/src/services/youtube_service.py`
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError)),
    reraise=True
)
def get_video_metadata(video_id: str) -> VideoMetadataSchema:
    # Existing implementation
    ...

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def get_video_transcript(video_id: str) -> str:
    # Existing implementation
    ...
```

**File:** `youtube_to_list/src/services/llm_service.py`
```python
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type((genai.types.GenerationError, ConnectionError)),
    reraise=True
)
def generate_content_and_tags(metadata: VideoMetadataSchema, transcript: str) -> Dict[str, Any]:
    # Existing implementation
    ...
```

**Acceptance Criteria:**
- [ ] API calls retry on transient failures
- [ ] Exponential backoff implemented
- [ ] Maximum 3 retry attempts
- [ ] Logs show retry attempts

---

#### 3.2 Add LLM Response Validation
**File:** `youtube_to_list/src/schemas.py`

```python
from pydantic import BaseModel, Field, validator, field_validator
from typing import List, Optional
import re

class LLMRecipeDetailsSchema(BaseModel):
    """Strict schema for LLM-extracted recipe details"""
    name: str = Field(..., min_length=1, max_length=500)
    prep_time: Optional[str] = Field(None, pattern=r'^PT(\d+H)?(\d+M)?$')
    cook_time: Optional[str] = Field(None, pattern=r'^PT(\d+H)?(\d+M)?$')
    total_time: Optional[str] = Field(None, pattern=r'^PT(\d+H)?(\d+M)?$')
    servings: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    cuisine: Optional[str] = Field(None, max_length=100)
    calories: Optional[int] = Field(None, ge=0, le=10000)
    
    @field_validator('prep_time', 'cook_time', 'total_time')
    def validate_iso8601_duration(cls, v):
        if v and not re.match(r'^PT(\d+H)?(\d+M)?$', v):
            return None  # Invalid format, set to None
        return v

class LLMIngredientSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)

class LLMInstructionSchema(BaseModel):
    step_number: int = Field(..., ge=1)
    section_name: Optional[str] = Field(None, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)

class LLMResponseSchema(BaseModel):
    recipe_details: LLMRecipeDetailsSchema
    ingredients: List[LLMIngredientSchema] = Field(..., min_items=1)
    instructions: List[LLMInstructionSchema] = Field(..., min_items=1)
    main_image_url: Optional[str] = Field(None, max_length=2000)
```

**Update:** `youtube_to_list/src/services/llm_service.py`
```python
from src.schemas import LLMResponseSchema
from pydantic import ValidationError

def generate_content_and_tags(metadata, transcript) -> Dict[str, Any]:
    # ... existing API call ...
    
    try:
        # Validate response against strict schema
        validated_response = LLMResponseSchema(**response_data)
        return validated_response.model_dump()
    except ValidationError as e:
        logger.error(f"LLM response validation failed: {e}")
        raise ValueError(f"Invalid LLM response structure: {e}")
```

**Acceptance Criteria:**
- [ ] All LLM responses validated with Pydantic
- [ ] Invalid responses rejected early
- [ ] Validation errors logged with details
- [ ] Fallback behavior for validation failures

---

#### 3.3 Implement Response Caching
```bash
pip install cachetools
```

**File:** `youtube_to_list/src/services/youtube_service.py`
```python
from cachetools import TTLCache, cached
from threading import Lock

# Cache for 1 hour, max 100 entries
metadata_cache = TTLCache(maxsize=100, ttl=3600)
transcript_cache = TTLCache(maxsize=100, ttl=3600)
cache_lock = Lock()

@cached(cache=metadata_cache, lock=cache_lock)
def get_video_metadata(video_id: str) -> VideoMetadataSchema:
    # Existing implementation
    ...

@cached(cache=transcript_cache, lock=cache_lock)
def get_video_transcript(video_id: str) -> str:
    # Existing implementation
    ...
```

**Acceptance Criteria:**
- [ ] Duplicate requests served from cache
- [ ] Cache expires after 1 hour
- [ ] Cache thread-safe
- [ ] Cache hit/miss logged

---

## Phase 4: API Improvements 🟡 MEDIUM
**Priority:** MEDIUM  
**Effort:** 2 days  
**Risk:** LOW

### Objectives
Add pagination, search, filtering, and async processing.

### Tasks

#### 4.1 Add Pagination to Recipe Listing
**File:** `youtube_to_list/src/schemas.py`

```python
class PaginatedRecipeListResponseSchema(BaseModel):
    recipes: List[RecipeSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**File:** `youtube_to_list/src/api/v1/endpoints/recipes.py`

```python
from math import ceil

@router.get("/", response_model=PaginatedRecipeListResponseSchema)
def list_recipes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine"),
    db: Session = Depends(get_db),
):
    query = db.query(Recipe)
    
    # Apply filters
    if category:
        query = query.filter(Recipe.category.ilike(f"%{category}%"))
    if cuisine:
        query = query.filter(Recipe.cuisine.ilike(f"%{cuisine}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    recipes = query.order_by(Recipe.created_at.desc()).offset(offset).limit(page_size).all()
    
    return PaginatedRecipeListResponseSchema(
        recipes=recipes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 0
    )
```

**Acceptance Criteria:**
- [ ] Pagination working with page/page_size params
- [ ] Total count and pages returned
- [ ] Category/cuisine filtering works
- [ ] Performance acceptable with 1000+ recipes

---

#### 4.2 Add Search Endpoint
**File:** `youtube_to_list/src/api/v1/endpoints/recipes.py`

```python
@router.get("/search", response_model=PaginatedRecipeListResponseSchema)
def search_recipes(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    search_term = f"%{q}%"
    
    query = db.query(Recipe).filter(
        or_(
            Recipe.name.ilike(search_term),
            Recipe.category.ilike(search_term),
            Recipe.cuisine.ilike(search_term)
        )
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    recipes = query.offset(offset).limit(page_size).all()
    
    return PaginatedRecipeListResponseSchema(
        recipes=recipes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size)
    )
```

**Acceptance Criteria:**
- [ ] Search across name, category, cuisine
- [ ] Case-insensitive search
- [ ] Pagination applied to search results
- [ ] Empty query handled gracefully

---

#### 4.3 Implement Async Job Processing
**File:** `youtube_to_list/src/schemas.py`

```python
class AsyncJobResponseSchema(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    message: str

class JobStatusResponseSchema(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
```

**File:** `youtube_to_list/src/api/v1/endpoints/youtube.py`

```python
from fastapi import BackgroundTasks
import uuid
from datetime import datetime
from typing import Dict

# In-memory job store (use Redis in production)
job_store: Dict[str, Dict] = {}

def process_recipe_background(job_id: str, youtube_url: str):
    """Background task to process recipe"""
    try:
        job_store[job_id]["status"] = "processing"
        job_store[job_id]["updated_at"] = datetime.utcnow().isoformat()
        
        from src.database import SessionLocal
        db = SessionLocal()
        
        recipe = recipe_service.upsert_recipe_from_youtube_url(db, youtube_url)
        
        job_store[job_id].update({
            "status": "completed",
            "result": {
                "recipe_id": recipe.id,
                "recipe_name": recipe.name
            },
            "updated_at": datetime.utcnow().isoformat()
        })
        
        db.close()
        
    except Exception as e:
        job_store[job_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })

@router.post("/process-youtube-url-async", response_model=AsyncJobResponseSchema)
def process_youtube_url_async(
    request: YouTubeProcessRequestSchema,
    background_tasks: BackgroundTasks,
):
    job_id = str(uuid.uuid4())
    
    job_store[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "youtube_url": request.youtube_url,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    background_tasks.add_task(process_recipe_background, job_id, request.youtube_url)
    
    return AsyncJobResponseSchema(
        job_id=job_id,
        status="pending",
        message="Recipe processing started"
    )

@router.get("/jobs/{job_id}", response_model=JobStatusResponseSchema)
def get_job_status(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponseSchema(**job_store[job_id])
```

**Acceptance Criteria:**
- [ ] Async endpoint returns immediately with job_id
- [ ] Status endpoint shows job progress
- [ ] Background processing doesn't block API
- [ ] Failed jobs tracked with error messages

---

## Phase 5: Frontend Enhancements 🟡 MEDIUM
**Priority:** MEDIUM  
**Effort:** 2 days  
**Risk:** LOW

### Objectives
Improve frontend performance, UX, and error handling.

### Tasks

#### 5.1 Add React Query for Data Fetching
```bash
cd frontend
npm install @tanstack/react-query
```

**File:** `frontend/src/main.tsx`
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

**File:** `frontend/src/components/RecipeGallery.tsx`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const RecipeGallery = () => {
  const queryClient = useQueryClient();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['recipes'],
    queryFn: async () => {
      const res = await axios.get('/api/v1/recipes/');
      return res.data.recipes;
    },
  });

  const mutation = useMutation({
    mutationFn: (url: string) => 
      axios.post('/api/v1/youtube/process-youtube-url', { youtube_url: url }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
    },
    onError: (error) => {
      alert(`Failed to process URL: ${error.message}`);
    },
  });

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const urlInput = event.currentTarget.elements.namedItem('url') as HTMLInputElement;
    mutation.mutate(urlInput.value);
    urlInput.value = '';
  };
  
  // ... rest of component
};
```

**Acceptance Criteria:**
- [ ] Data cached client-side
- [ ] No redundant API calls
- [ ] Optimistic updates working
- [ ] Loading/error states handled

---

#### 5.2 Add Loading Skeletons and Error Boundaries
**File:** `frontend/src/components/ui/skeleton.tsx` (NEW)

```typescript
export const Skeleton = ({ className }: { className?: string }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

export const RecipeCardSkeleton = () => (
  <Card>
    <CardHeader>
      <Skeleton className="h-6 w-3/4 mb-2" />
      <Skeleton className="h-4 w-1/2" />
    </CardHeader>
    <CardContent>
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-2/3" />
    </CardContent>
  </Card>
);
```

**File:** `frontend/src/components/ErrorBoundary.tsx` (NEW)

```typescript
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="text-center p-8">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h1>
          <p className="text-gray-600">{this.state.error?.message}</p>
          <button 
            onClick={() => this.setState({ hasError: false })}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Update:** `frontend/src/App.tsx`
```typescript
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        {/* routes */}
      </BrowserRouter>
    </ErrorBoundary>
  );
}
```

**Acceptance Criteria:**
- [ ] Skeleton shown during loading
- [ ] Error boundary catches React errors
- [ ] User can recover from errors
- [ ] Errors logged for debugging

---

#### 5.3 Implement Image Lazy Loading
**File:** `frontend/src/components/RecipeDetail.tsx`

```typescript
// Add native lazy loading
<img
  src={recipe.main_image_url}
  alt={recipe.name}
  loading="lazy"
  decoding="async"
  className="w-full h-64 object-cover rounded-t-lg mb-6"
  onError={() => {
    console.error(`Failed to load image: ${recipe?.main_image_url}`);
    setImageError(true);
  }}
/>

// Optional: Add blur-up effect
const [imageLoaded, setImageLoaded] = useState(false);

<div className="relative">
  {!imageLoaded && <Skeleton className="absolute inset-0 h-64" />}
  <img
    src={recipe.main_image_url}
    alt={recipe.name}
    loading="lazy"
    onLoad={() => setImageLoaded(true)}
    className={`w-full h-64 object-cover rounded-t-lg mb-6 transition-opacity ${
      imageLoaded ? 'opacity-100' : 'opacity-0'
    }`}
  />
</div>
```

**Acceptance Criteria:**
- [ ] Images load only when visible
- [ ] Smooth loading transitions
- [ ] Fallback for failed images
- [ ] Page load time improved

---

## Phase 6: Observability & Monitoring 🟡 MEDIUM
**Priority:** MEDIUM  
**Effort:** 1-2 days  
**Risk:** LOW

### Objectives
Replace debug statements with structured logging and add metrics.

### Tasks

#### 6.1 Implement Structured Logging
```bash
pip install python-json-logger
```

**File:** `youtube_to_list/src/logging_config.py` (NEW)

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(level=logging.INFO):
    """Configure structured JSON logging"""
    
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        timestamp=True
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Module-level logger
logger = logging.getLogger(__name__)
```

**Update all modules:**
```python
from src.logging_config import logger

# Replace all print() with:
logger.info("Processing recipe", extra={"video_id": video_id})
logger.error("Failed to fetch transcript", extra={"error": str(e)})
logger.debug("LLM response received", extra={"recipe_name": recipe_name})
```

**File:** `youtube_to_list/src/main.py`
```python
from src.logging_config import setup_logging
import logging

# Set log level from environment
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(getattr(logging, log_level))
```

**Acceptance Criteria:**
- [ ] All print() replaced with logger calls
- [ ] JSON-formatted logs
- [ ] Log level configurable via env
- [ ] Contextual information in logs

---

#### 6.2 Add Prometheus Metrics
```bash
pip install prometheus-fastapi-instrumentator
```

**File:** `youtube_to_list/src/main.py`

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Custom metrics
from prometheus_client import Counter, Histogram, Gauge

recipe_processing_time = Histogram(
    'recipe_processing_seconds',
    'Time spent processing recipes',
    ['status']
)

llm_api_calls = Counter(
    'llm_api_calls_total',
    'Total LLM API calls',
    ['model', 'status']
)

active_recipes = Gauge(
    'active_recipes_total',
    'Total number of recipes in database'
)
```

**Update services:**
```python
import time

def upsert_recipe_from_youtube_url(db: Session, youtube_url: str):
    start_time = time.time()
    status = "success"
    
    try:
        # ... existing code ...
        return db_recipe
    except Exception as e:
        status = "failed"
        raise
    finally:
        duration = time.time() - start_time
        recipe_processing_time.labels(status=status).observe(duration)
```

**Acceptance Criteria:**
- [ ] /metrics endpoint available
- [ ] Request metrics tracked
- [ ] Custom business metrics tracked
- [ ] Can be scraped by Prometheus

---

#### 6.3 Implement LLM Cost Tracking
**File:** `youtube_to_list/src/services/llm_metrics.py` (NEW)

```python
from dataclasses import dataclass
from typing import Dict
from datetime import datetime

@dataclass
class LLMUsage:
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float

class LLMMetrics:
    """Track LLM API usage and costs"""
    
    # Gemini pricing (as of 2026)
    PRICING = {
        "gemini-2.5-flash": {
            "input": 0.00001,   # per token
            "output": 0.00003,  # per token
        }
    }
    
    def __init__(self):
        self.usage_history: list[LLMUsage] = []
        self.total_tokens = 0
        self.total_cost_usd = 0.0
    
    def track_call(self, model: str, input_tokens: int, output_tokens: int):
        """Record LLM API call metrics"""
        pricing = self.PRICING.get(model, {"input": 0, "output": 0})
        
        cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
        
        usage = LLMUsage(
            timestamp=datetime.utcnow(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost
        )
        
        self.usage_history.append(usage)
        self.total_tokens += input_tokens + output_tokens
        self.total_cost_usd += cost
        
        logger.info(
            "LLM API call",
            extra={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": f"{cost:.6f}",
                "total_cost_usd": f"{self.total_cost_usd:.6f}"
            }
        )
        
        return usage
    
    def get_summary(self) -> Dict:
        return {
            "total_calls": len(self.usage_history),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "average_cost_per_call": round(
                self.total_cost_usd / len(self.usage_history), 4
            ) if self.usage_history else 0
        }

# Singleton instance
llm_metrics = LLMMetrics()
```

**Update:** `youtube_to_list/src/services/llm_service.py`
```python
from src.services.llm_metrics import llm_metrics

def generate_content_and_tags(metadata, transcript):
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    
    # Track usage (Gemini API provides token counts)
    if hasattr(response, 'usage_metadata'):
        llm_metrics.track_call(
            model=MODEL_NAME,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count
        )
    
    # ... rest of function
```

**Add metrics endpoint:**
```python
@app.get("/admin/llm-metrics", tags=["admin"])
def get_llm_metrics():
    return llm_metrics.get_summary()
```

**Acceptance Criteria:**
- [ ] All LLM calls tracked
- [ ] Token counts recorded
- [ ] Costs calculated accurately
- [ ] Metrics accessible via endpoint

---

## Phase 7: Configuration Management 🟢 LOW
**Priority:** LOW  
**Effort:** 0.5 days  
**Risk:** LOW

### Objectives
Centralize configuration with proper validation.

### Tasks

#### 7.1 Implement Pydantic Settings
```bash
pip install pydantic-settings
```

**File:** `youtube_to_list/src/config.py` (REFACTOR)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Application configuration with validation"""
    
    # API Keys
    google_api_key: str
    youtube_api_key: str
    
    # Database
    database_url: str = "sqlite:///./youtube_cards.db"
    
    # Security
    api_keys: str = ""  # Comma-separated list
    allowed_origins: str = "http://localhost:5173"
    
    # LLM Configuration
    llm_model_name: str = "gemini-2.5-flash"
    llm_max_retries: int = 3
    llm_timeout: int = 60
    
    # Cache Configuration
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    
    # Application
    environment: str = "development"
    debug: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

settings = Settings()

# Backward compatibility
GOOGLE_API_KEY = settings.google_api_key
YOUTUBE_API_KEY = settings.youtube_api_key
SQLALCHEMY_DATABASE_URL = settings.database_url
```

**Update all imports:**
```python
from src.config import settings

# Use settings.google_api_key instead of GOOGLE_API_KEY
```

**Acceptance Criteria:**
- [ ] All config centralized in Settings class
- [ ] Environment variables validated on startup
- [ ] Type checking for config values
- [ ] Helpful error messages for missing config

---

#### 7.2 Create .env.example
**File:** `.env.example` (NEW)

```bash
# Google APIs
GOOGLE_API_KEY=your_google_generative_ai_api_key_here
YOUTUBE_API_KEY=your_youtube_data_api_v3_key_here

# Database
# SQLite (development)
DATABASE_URL=sqlite:///./youtube_cards.db
# PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@localhost:5432/youtube_recipes

# Security
# Comma-separated list of valid API keys
API_KEYS=dev-key-123,prod-key-456
# Comma-separated list of allowed origins for CORS
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com

# LLM Configuration
LLM_MODEL_NAME=gemini-2.5-flash
LLM_MAX_RETRIES=3
LLM_TIMEOUT=60

# Cache
CACHE_TTL=3600
CACHE_MAX_SIZE=100

# Logging
LOG_LEVEL=INFO

# Application
ENVIRONMENT=development
DEBUG=false
```

**File:** `README.md` (UPDATE)

Add section:
```markdown
## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your API keys:
   - Get Google Generative AI key: https://makersuite.google.com/app/apikey
   - Get YouTube Data API key: https://console.cloud.google.com/apis/credentials

3. (Optional) Customize other settings as needed.

See `.env.example` for all available configuration options.
```

**Acceptance Criteria:**
- [ ] .env.example created with all variables
- [ ] .env.example added to git
- [ ] .env in .gitignore
- [ ] README updated with setup instructions

---

## Phase 8: Testing & Quality 🟢 LOW
**Priority:** LOW  
**Effort:** 3 days  
**Risk:** LOW

### Objectives
Increase test coverage and code quality.

### Tasks

#### 8.1 Expand Backend Tests
**File:** `youtube_to_list/tests/conftest.py` (NEW)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.models import Recipe, Ingredient, RecipeIngredient, Instruction

@pytest.fixture
def test_db():
    """Create in-memory database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def sample_recipe(test_db):
    """Create sample recipe for tests"""
    recipe = Recipe(
        name="Test Recipe",
        source_url="https://youtube.com/watch?v=test123",
        category="Dessert",
        cuisine="American",
        prep_time="PT30M",
        cook_time="PT1H"
    )
    test_db.add(recipe)
    test_db.commit()
    test_db.refresh(recipe)
    return recipe
```

**File:** `youtube_to_list/tests/test_recipe_service.py` (NEW)

```python
import pytest
from src.services import recipe_service
from src.models import Recipe

def test_get_recipe_by_id(test_db, sample_recipe):
    recipe = recipe_service.get_recipe_by_id(test_db, sample_recipe.id)
    assert recipe is not None
    assert recipe.name == "Test Recipe"

def test_get_recipe_by_id_not_found(test_db):
    recipe = recipe_service.get_recipe_by_id(test_db, 999)
    assert recipe is None

def test_delete_recipe_by_id(test_db, sample_recipe):
    deleted = recipe_service.delete_recipe_by_id(test_db, sample_recipe.id)
    assert deleted is not None
    assert deleted.id == sample_recipe.id
    
    # Verify deletion
    recipe = recipe_service.get_recipe_by_id(test_db, sample_recipe.id)
    assert recipe is None

# Add more tests...
```

**File:** `youtube_to_list/tests/test_validators.py` (NEW)

```python
from src.validators import validate_youtube_url, sanitize_url

def test_validate_youtube_url_valid():
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
    ]
    
    for url in valid_urls:
        is_valid, error = validate_youtube_url(url)
        assert is_valid is True
        assert error is None

def test_validate_youtube_url_invalid():
    invalid_urls = [
        "https://vimeo.com/123456",
        "not a url",
        "",
        None,
        "https://youtube.com/channel/123",
    ]
    
    for url in invalid_urls:
        is_valid, error = validate_youtube_url(url)
        assert is_valid is False
        assert error is not None

def test_sanitize_url():
    dirty_url = "https://youtube.com/watch?v=test123&feature=share&t=30"
    clean_url = sanitize_url(dirty_url)
    assert clean_url == "https://youtube.com/watch?v=test123"
```

**Update:** `youtube_to_list/requirements.txt`
```
pytest
pytest-cov
pytest-asyncio
```

**Run tests with coverage:**
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

**Acceptance Criteria:**
- [ ] Test coverage > 70%
- [ ] All services have unit tests
- [ ] Validators fully tested
- [ ] Database operations tested with fixtures

---

#### 8.2 Add Frontend Tests
```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**File:** `frontend/vite.config.ts` (UPDATE)

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
```

**File:** `frontend/src/test/setup.ts` (NEW)

```typescript
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

afterEach(() => {
  cleanup();
});
```

**File:** `frontend/src/components/__tests__/RecipeGallery.test.tsx` (NEW)

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import RecipeGallery from '../RecipeGallery';
import axios from 'axios';

vi.mock('axios');

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('RecipeGallery', () => {
  it('renders loading state initially', () => {
    renderWithProviders(<RecipeGallery />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
  
  it('displays recipes after loading', async () => {
    const mockRecipes = [
      { id: 1, name: 'Test Recipe 1', category: 'Dessert' },
      { id: 2, name: 'Test Recipe 2', category: 'Main Course' },
    ];
    
    vi.mocked(axios.get).mockResolvedValueOnce({ data: { recipes: mockRecipes } });
    
    renderWithProviders(<RecipeGallery />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
      expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
    });
  });
  
  // Add more tests...
});
```

**Update:** `frontend/package.json`
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

**Acceptance Criteria:**
- [ ] Component rendering tests pass
- [ ] User interactions tested
- [ ] API mocking works
- [ ] Coverage > 60%

---

#### 8.3 Add Integration Tests
**File:** `youtube_to_list/tests/test_integration.py` (NEW)

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import Base, engine

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_test_db():
    """Setup test database before integration tests"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_recipes_empty(setup_test_db):
    response = client.get("/api/v1/recipes/")
    assert response.status_code == 200
    data = response.json()
    assert "recipes" in data
    assert isinstance(data["recipes"], list)

def test_get_recipe_not_found(setup_test_db):
    response = client.get("/api/v1/recipes/999")
    assert response.status_code == 404

# Add test for full pipeline (requires mocking external APIs)
```

**Acceptance Criteria:**
- [ ] API endpoints tested end-to-end
- [ ] HTTP status codes verified
- [ ] Response schemas validated
- [ ] Error cases covered

---

## Phase 9: Code Quality & Documentation 🟢 LOW
**Priority:** LOW  
**Effort:** 1 day  
**Risk:** NONE

### Objectives
Clean up code, add documentation, extract constants.

### Tasks

#### 9.1 Clean Up Code Issues
**File:** `youtube_to_list/src/services/llm_service.py`

- Remove duplicate `tags` structure (lines 77-81)
- Remove commented code
- Fix inconsistent formatting

**File:** `youtube_to_list/src/constants.py` (NEW)

```python
"""Application constants"""

# Unit conversion factors
UNIT_CONVERSIONS = {
    "metric_to_imperial": {
        "ml": {"threshold": 236, "factor": 236.588, "unit": "cups"},
        "g": {"threshold": 450, "factor": 453.592, "unit": "lbs"},
    },
    "imperial_to_metric": {
        "cup": {"factor": 240, "unit": "ml"},
        "oz": {"factor": 28.35, "unit": "g"},
        "lb": {"factor": 453.592, "unit": "g"},
        "tsp": {"factor": 4.929, "unit": "ml"},
        "tbsp": {"factor": 14.79, "unit": "ml"},
    }
}

# API Timeouts
YOUTUBE_API_TIMEOUT = 30  # seconds
LLM_API_TIMEOUT = 60  # seconds

# Cache Settings
DEFAULT_CACHE_TTL = 3600  # 1 hour
DEFAULT_CACHE_SIZE = 100  # entries

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Rate Limiting
RATE_LIMIT_PER_MINUTE = 10
RATE_LIMIT_PER_DAY = 200
```

**Update:** `frontend/src/components/RecipeDetail.tsx`
```typescript
import { UNIT_CONVERSIONS } from '../constants';

// Use constants instead of magic numbers
```

**Acceptance Criteria:**
- [ ] No duplicate code
- [ ] No commented-out code
- [ ] Magic numbers extracted to constants
- [ ] Imports organized and unused removed

---

#### 9.2 Add Comprehensive Docstrings
**Example:** `youtube_to_list/src/services/recipe_service.py`

```python
def upsert_recipe_from_youtube_url(db: Session, youtube_url: str) -> Recipe:
    """
    Process a YouTube URL and create or update a recipe in the database.
    
    This function orchestrates the entire recipe extraction pipeline:
    1. Validates and extracts the video ID from the URL
    2. Checks transcript availability
    3. Fetches video metadata (title, description, thumbnail, comments)
    4. Retrieves video transcript if available
    5. Sends data to LLM for recipe extraction
    6. Creates or updates the recipe in the database
    
    Args:
        db (Session): SQLAlchemy database session
        youtube_url (str): Valid YouTube video URL
        
    Returns:
        Recipe: The created or updated recipe object with all relationships loaded
        
    Raises:
        ValueError: If the URL is invalid or video is not accessible
        RuntimeError: If LLM processing fails or database operations fail
        
    Examples:
        >>> recipe = upsert_recipe_from_youtube_url(db, "https://youtube.com/watch?v=abc123")
        >>> print(recipe.name)
        "Chocolate Chip Cookies"
        
    Note:
        - Existing recipes are identified by source_url and updated in place
        - All ingredients and instructions are replaced on update
        - Transaction is rolled back on any error
    """
    # ... implementation
```

**Add docstrings to:**
- All public functions
- All API endpoints
- All service methods
- Complex helper functions

**Acceptance Criteria:**
- [ ] All public functions documented
- [ ] Docstrings follow Google/NumPy style
- [ ] Parameters and return types documented
- [ ] Exceptions documented

---

#### 9.3 Update Documentation
**File:** `README.md` (UPDATE)

Add sections:
- Architecture Overview
- API Documentation
- Configuration Guide
- Deployment Guide
- Contributing Guidelines
- Testing Guide

**File:** `ARCHITECTURE.md` (NEW)

Document:
- System architecture diagram
- Data flow
- Component responsibilities
- Technology choices and rationale

**File:** `API.md` (NEW)

Document all endpoints:
- Request/response schemas
- Example curl commands
- Authentication requirements
- Error responses

**Acceptance Criteria:**
- [ ] README comprehensive and up-to-date
- [ ] Architecture documented
- [ ] API documented
- [ ] Setup instructions tested

---

## Implementation Timeline

| Phase | Duration | Dependencies | Start After |
|-------|----------|--------------|-------------|
| Phase 1: Security | 1-2 days | None | Immediately |
| Phase 2: Database | 2-3 days | None | Immediately (parallel) |
| Phase 3: Reliability | 2 days | Phase 1 | Phase 1 complete |
| Phase 4: API Improvements | 2 days | Phase 2 | Phase 2 complete |
| Phase 5: Frontend | 2 days | Phase 4 | Phase 4 complete |
| Phase 6: Observability | 1-2 days | Phase 1 | Phase 1 complete |
| Phase 7: Configuration | 0.5 days | None | Anytime |
| Phase 8: Testing | 3 days | Phases 1-5 | After Phases 1-5 |
| Phase 9: Code Quality | 1 day | None | Anytime |

**Total Estimated Time:** 15-20 development days

---

## Success Metrics

### Security
- [ ] Zero exposed secrets in logs
- [ ] All endpoints rate-limited
- [ ] CORS properly configured
- [ ] Input validation on all user inputs

### Performance
- [ ] API response time < 200ms (cached)
- [ ] Recipe processing < 30s (p95)
- [ ] Database query time < 50ms (with indexes)
- [ ] Frontend initial load < 2s

### Reliability
- [ ] 99% uptime
- [ ] < 1% failed LLM calls (after retries)
- [ ] Zero data loss incidents
- [ ] All errors logged with context

### Code Quality
- [ ] Test coverage > 70%
- [ ] No critical security vulnerabilities
- [ ] All functions documented
- [ ] Code passes linting

### Observability
- [ ] All errors logged with context
- [ ] LLM costs tracked
- [ ] Key metrics exposed
- [ ] Alerts configured

---

## Risk Mitigation

### Database Migration Risk
- **Risk:** Data loss during SQLite → PostgreSQL migration
- **Mitigation:**
  - Test migration on copy of production data
  - Keep SQLite backup for 30 days
  - Implement rollback procedure
  - Schedule migration during low-traffic period

### API Breaking Changes Risk
- **Risk:** Frontend breaks with new pagination API
- **Mitigation:**
  - Version API endpoints (v1, v2)
  - Maintain backward compatibility for 1 release
  - Update frontend and backend simultaneously

### External API Changes Risk
- **Risk:** YouTube or Gemini API changes break functionality
- **Mitigation:**
  - Pin API versions
  - Monitor API deprecation notices
  - Implement comprehensive error handling
  - Add integration tests with real APIs

---

## Post-Implementation Checklist

- [ ] All phases completed
- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Staging environment tested
- [ ] Deployment runbook created
- [ ] Monitoring dashboards configured
- [ ] Incident response plan documented

---

## Future Enhancements (Not in Current Plan)

1. **User Accounts & Multi-tenancy**
   - User authentication and authorization
   - Personal recipe collections
   - Sharing and collaboration features

2. **Advanced Search**
   - Full-text search with Elasticsearch
   - Filter by ingredients, dietary restrictions
   - Semantic search with embeddings

3. **Recipe Scaling**
   - Automatic ingredient scaling for servings
   - Batch cooking calculations
   - Nutritional information scaling

4. **Export Features**
   - PDF export
   - Print-friendly views
   - Recipe book generation

5. **Social Features**
   - Recipe ratings and reviews
   - User comments
   - Recipe collections/boards

6. **Mobile App**
   - React Native mobile app
   - Offline recipe access
   - Shopping list integration

7. **AI Enhancements**
   - Ingredient substitution suggestions
   - Recipe variations
   - Dietary restriction adaptations
   - Cooking tips and techniques

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-03  
**Owner:** Development Team  
**Review Date:** After Phase 8 completion
