from sqlalchemy.orm import Session
from src.models import Card as CardModel
from src.schemas import CardCreateSchema, VideoMetadataSchema, TagsSchema
from src.services import youtube_service, llm_service
from datetime import datetime
from typing import Optional, Dict, Any, List # Import Optional here
import uuid

def create_card_from_youtube_url(db: Session, youtube_url: str) -> CardModel:
    """
    Processes a YouTube URL to create a new Card entry in the database.
    """
    try:
        video_id = youtube_service.extract_video_id(youtube_url)
        
        # 1. Check for transcript availability
        has_transcript = youtube_service.check_transcript_availability(video_id)
        
        # 2. Fetch Video Metadata (including description)
        metadata = youtube_service.get_video_metadata(video_id)
        
        # 3. Fetch Transcript if available
        transcript = ""
        if has_transcript:
            try:
                transcript = youtube_service.get_video_transcript(video_id)
            except ValueError as e:
                # Log this, but don't fail the process
                print(f"Proceeding without transcript for {youtube_url} due to error: {e}")
        
        # 4. Process content with LLM
        llm_output = llm_service.generate_content_and_tags(metadata, transcript)
        
        extracted_content = llm_output.get("extracted_content", {})
        tags = llm_output.get("tags", {})
        action_steps = llm_output.get("action_steps", [])
        card_color = llm_output.get("card_color", "#EAEAEA") # Default to gray
        
        # Ensure tags are in the expected format even if LLM output is slightly off
        tags_schema = TagsSchema(
            macro=tags.get("macro", []),
            topic=tags.get("topic", []),
            content=tags.get("content", [])
        )
        
        # 4. Create Card Object
        card_data = CardCreateSchema(
            video_metadata=metadata,
            extracted_content_type=extracted_content.get("type", "General Information"),
            extracted_content_details=extracted_content.get("details", {}),
            tags=tags_schema
        )
        
        db_card = CardModel(
            video_url=card_data.video_metadata.url,
            video_title=card_data.video_metadata.title,
            thumbnail_url=card_data.video_metadata.thumbnail_url,
            channel_name=card_data.video_metadata.channel_name,
            published_date=card_data.video_metadata.published_date,
            extracted_content_type=card_data.extracted_content_type,
            extracted_content_details=card_data.extracted_content_details,
            tags_macro=card_data.tags.macro,
            tags_topic=card_data.tags.topic,
            tags_content=card_data.tags.content,
            action_steps=action_steps,
            card_color=card_color,
            created_at=datetime.utcnow()
        )

        db.add(db_card)
        db.commit()
        db.refresh(db_card)
        
        return db_card
        
    except ValueError as ve:
        db.rollback() # Rollback any partial changes if a known error occurred early
        print(f"Value Error during card creation for {youtube_url}: {ve}")
        raise ve # Re-raise to be caught by API layer
    except Exception as e:
        db.rollback() # Rollback any partial changes
        print(f"Unexpected error during card creation for {youtube_url}: {e}")
        raise RuntimeError(f"Failed to process YouTube URL: {e}") from e

def get_card_by_id(db: Session, card_id: int) -> Optional[CardModel]:
    return db.query(CardModel).filter(CardModel.id == card_id).first()

def get_all_cards(db: Session) -> list[CardModel]:
    return db.query(CardModel).order_by(CardModel.created_at.desc()).all()

def delete_card_by_id(db: Session, card_id: int) -> Optional[CardModel]:
    """
    Deletes a card from the database by its ID.
    """
    card_to_delete = db.query(CardModel).filter(CardModel.id == card_id).first()
    if card_to_delete:
        db.delete(card_to_delete)
        db.commit()
        return card_to_delete
    return None