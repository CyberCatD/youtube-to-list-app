from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any

# This schema now directly reflects the flat structure of the Card SQLAlchemy model
class CardDBSchema(BaseModel):
    id: int
    video_url: str
    video_title: str
    thumbnail_url: Optional[str] = None
    channel_name: Optional[str] = None
    published_date: Optional[datetime] = None
    extracted_content_type: str
    extracted_content_details: Dict[str, Any]
    tags_macro: List[str] = Field(default_factory=list)
    tags_topic: List[str] = Field(default_factory=list)
    tags_content: List[str] = Field(default_factory=list)
    action_steps: Optional[List[str]] = Field(default_factory=list)
    card_color: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# The response model is updated to use the corrected CardDBSchema
class CardListResponseSchema(BaseModel):
    cards: List[CardDBSchema]

# --- Schemas below are for creating/processing and remain as they were ---

class VideoMetadataSchema(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    channel_name: Optional[str] = None
    published_date: Optional[datetime] = None

class TagsSchema(BaseModel):
    macro: List[str] = Field(default_factory=list)
    topic: List[str] = Field(default_factory=list)
    content: List[str] = Field(default_factory=list)

class CardBaseSchema(BaseModel):
    video_metadata: VideoMetadataSchema
    extracted_content_type: str
    extracted_content_details: Dict[str, Any]
    tags: TagsSchema

class CardCreateSchema(CardBaseSchema):
    pass

class YouTubeProcessRequestSchema(BaseModel):
    youtube_url: str

class YouTubeProcessResponseSchema(BaseModel):
    message: str
    card_id: int
    video_title: Optional[str] = None

class ErrorResponseSchema(BaseModel):
    error: str
