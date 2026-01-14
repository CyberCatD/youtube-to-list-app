from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
from typing import Dict
import uuid
import logging

from src.database import get_db, SessionLocal
from src.services import recipe_service
from src.schemas import (
    YouTubeProcessRequestSchema, 
    YouTubeProcessResponseSchema, 
    WebProcessRequestSchema,
    UniversalProcessRequestSchema,
    ErrorResponseSchema,
    AsyncJobResponseSchema,
    JobStatusResponseSchema
)
from src.validators import validate_youtube_url, sanitize_url
from src.auth import verify_api_key

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

job_store: Dict[str, Dict] = {}

@router.post("/process-youtube-url", response_model=YouTubeProcessResponseSchema, responses={400: {"model": ErrorResponseSchema}, 500: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def process_youtube_url(
    request: Request,
    youtube_request: YouTubeProcessRequestSchema,
    db: Session = Depends(get_db),
):
    """
    Processes a YouTube URL to create a new, structured recipe.
    """
    is_valid, error = validate_youtube_url(youtube_request.youtube_url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    sanitized_url = sanitize_url(youtube_request.youtube_url)
    
    try:
        created_recipe = recipe_service.upsert_recipe_from_youtube_url(db, sanitized_url)
        return YouTubeProcessResponseSchema(
            message="Recipe created successfully.",
            recipe_id=created_recipe.id,
            recipe_name=created_recipe.name,
            source_type="youtube"
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(re),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )

@router.post("/process-web-url", response_model=YouTubeProcessResponseSchema, responses={400: {"model": ErrorResponseSchema}, 500: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def process_web_url(
    request: Request,
    web_request: WebProcessRequestSchema,
    db: Session = Depends(get_db),
):
    """
    Processes a recipe website URL (AllRecipes, NYTimes Cooking, etc.) to create a new recipe.
    """
    sanitized_url = sanitize_url(web_request.url)
    
    try:
        created_recipe = recipe_service.upsert_recipe_from_web_url(db, sanitized_url)
        return YouTubeProcessResponseSchema(
            message="Recipe imported successfully.",
            recipe_id=created_recipe.id,
            recipe_name=created_recipe.name,
            source_type="web"
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(re),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )

@router.post("/process-url", response_model=YouTubeProcessResponseSchema, responses={400: {"model": ErrorResponseSchema}, 500: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def process_any_url(
    request: Request,
    url_request: UniversalProcessRequestSchema,
    db: Session = Depends(get_db),
):
    """
    Universal endpoint that automatically detects URL type (YouTube, recipe website, social media)
    and processes it accordingly.
    """
    sanitized_url = sanitize_url(url_request.url)
    
    try:
        created_recipe = recipe_service.upsert_recipe_from_any_url(db, sanitized_url)
        return YouTubeProcessResponseSchema(
            message="Recipe processed successfully.",
            recipe_id=created_recipe.id,
            recipe_name=created_recipe.name,
            source_type=created_recipe.source_type
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(re),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


def process_url_background(job_id: str, url: str):
    """Background task to process recipe from any URL."""
    db = None
    try:
        job_store[job_id]["status"] = "processing"
        job_store[job_id]["updated_at"] = datetime.utcnow().isoformat()
        
        db = SessionLocal()
        
        recipe = recipe_service.upsert_recipe_from_any_url(db, url)
        
        job_store[job_id].update({
            "status": "completed",
            "result": {
                "recipe_id": recipe.id,
                "recipe_name": recipe.name,
                "source_type": recipe.source_type
            },
            "updated_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Job {job_id} completed: recipe {recipe.id}")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job_store[job_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })
    finally:
        if db:
            db.close()


@router.post("/process-url-async", response_model=AsyncJobResponseSchema, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def process_url_async(
    request: Request,
    url_request: UniversalProcessRequestSchema,
    background_tasks: BackgroundTasks,
):
    """
    Async version of process-url. Returns immediately with a job ID.
    Use GET /jobs/{job_id} to check status.
    """
    sanitized_url = sanitize_url(url_request.url)
    
    job_id = str(uuid.uuid4())
    
    job_store[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "url": sanitized_url,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    background_tasks.add_task(process_url_background, job_id, sanitized_url)
    
    logger.info(f"Created async job {job_id} for URL: {sanitized_url}")
    
    return AsyncJobResponseSchema(
        job_id=job_id,
        status="pending",
        message="Recipe processing started"
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponseSchema)
def get_job_status(job_id: str):
    """
    Check the status of an async job.
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_store[job_id]
    return JobStatusResponseSchema(
        job_id=job["job_id"],
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"]
    )


@router.get("/jobs", response_model=list)
def list_jobs():
    """
    List all jobs (for debugging/admin purposes).
    """
    return [
        {
            "job_id": job["job_id"],
            "status": job["status"],
            "created_at": job["created_at"]
        }
        for job in job_store.values()
    ]
