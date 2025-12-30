from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

# --- Schema for passing data to the LLM ---

class VideoMetadataSchema(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    channel_name: Optional[str] = None
    published_date: Optional[datetime] = None
    comments: Optional[List[str]] = None

class TagsSchema(BaseModel):
    macro: List[str] = Field(default_factory=list)
    topic: List[str] = Field(default_factory=list)
    content: List[str] = Field(default_factory=list)

# --- Schemas for reading/returning data from the API ---

class IngredientSchema(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class RecipeIngredientSchema(BaseModel):
    ingredient: IngredientSchema
    quantity: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class InstructionSchema(BaseModel):
    step_number: int
    section_name: Optional[str] = None
    description: str
    model_config = ConfigDict(from_attributes=True)

class RecipeSchema(BaseModel):
    id: int
    name: str
    source_url: str
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    servings: Optional[str] = None
    category: Optional[str] = None
    cuisine: Optional[str] = None
    calories: Optional[int] = None
    main_image_url: Optional[str] = None # New field for main recipe image
    created_at: datetime
    
    ingredients: List[RecipeIngredientSchema] = []
    instructions: List[InstructionSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class RecipeListResponseSchema(BaseModel):
    recipes: List[RecipeSchema]

# --- Schemas for processing the YouTube URL ---

class YouTubeProcessRequestSchema(BaseModel):
    youtube_url: str

class YouTubeProcessResponseSchema(BaseModel):
    message: str
    recipe_id: int
    recipe_name: Optional[str] = None

class ErrorResponseSchema(BaseModel):
    detail: str

