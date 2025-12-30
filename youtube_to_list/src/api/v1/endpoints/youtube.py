from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services import recipe_service
from src.schemas import YouTubeProcessRequestSchema, YouTubeProcessResponseSchema, ErrorResponseSchema

router = APIRouter()

@router.post("/process-youtube-url", response_model=YouTubeProcessResponseSchema, responses={400: {"model": ErrorResponseSchema}, 500: {"model": ErrorResponseSchema}})
def process_youtube_url(
    request: YouTubeProcessRequestSchema,
    db: Session = Depends(get_db),
):
    """
    Processes a YouTube URL to create a new, structured recipe.
    """
    try:
        created_recipe = recipe_service.upsert_recipe_from_youtube_url(db, request.youtube_url)
        return YouTubeProcessResponseSchema(
            message="Recipe created successfully.",
            recipe_id=created_recipe.id,
            recipe_name=created_recipe.name
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
