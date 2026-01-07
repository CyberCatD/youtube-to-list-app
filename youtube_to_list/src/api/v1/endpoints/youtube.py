from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database import get_db
from src.services import recipe_service
from src.schemas import (
    YouTubeProcessRequestSchema, 
    YouTubeProcessResponseSchema, 
    WebProcessRequestSchema,
    UniversalProcessRequestSchema,
    ErrorResponseSchema
)
from src.validators import validate_youtube_url, sanitize_url
from src.auth import verify_api_key

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

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
