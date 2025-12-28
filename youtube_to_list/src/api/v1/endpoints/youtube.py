from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services import card_service
from src.schemas import YouTubeProcessRequestSchema, YouTubeProcessResponseSchema, ErrorResponseSchema

router = APIRouter()

@router.post("/process-youtube-url", response_model=YouTubeProcessResponseSchema, responses={400: {"model": ErrorResponseSchema}, 500: {"model": ErrorResponseSchema}})
def process_youtube_url(
    request: YouTubeProcessRequestSchema,
    db: Session = Depends(get_db),
):
    """
    Processes a YouTube URL to create a new card.
    """
    try:
        created_card = card_service.create_card_from_youtube_url(db, request.youtube_url)
        return YouTubeProcessResponseSchema(
            message="Card created successfully.",
            card_id=created_card.id,
            video_title=created_card.video_title
        )
    except ValueError as ve:
        # Specific errors like invalid URL, no transcript, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except RuntimeError as re:
        # General processing errors, e.g., LLM failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(re),
        )
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )
