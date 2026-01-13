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

class TagSchema(BaseModel):
    id: int
    name: str
    tag_type: str
    model_config = ConfigDict(from_attributes=True)

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
    source_type: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    servings: Optional[str] = None
    category: Optional[str] = None
    cuisine: Optional[str] = None
    calories: Optional[int] = None
    main_image_url: Optional[str] = None
    created_at: datetime
    
    ingredients: List[RecipeIngredientSchema] = []
    instructions: List[InstructionSchema] = []
    tags: List[TagSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class RecipeListResponseSchema(BaseModel):
    recipes: List[RecipeSchema]

class RecipeUpdateSchema(BaseModel):
    name: Optional[str] = None
    main_image_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# --- Schemas for processing URLs ---

class YouTubeProcessRequestSchema(BaseModel):
    youtube_url: str

class WebProcessRequestSchema(BaseModel):
    url: str

class UniversalProcessRequestSchema(BaseModel):
    url: str

class YouTubeProcessResponseSchema(BaseModel):
    message: str
    recipe_id: int
    recipe_name: Optional[str] = None
    source_type: Optional[str] = None

class ErrorResponseSchema(BaseModel):
    detail: str


# --- Schemas for Grocery Lists ---

class GroceryListItemSchema(BaseModel):
    id: int
    ingredient_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    is_checked: bool = False
    recipe_ids: Optional[List[int]] = None
    retail_package: Optional[str] = None
    retail_package_count: Optional[int] = None
    exact_amount: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class GroceryListItemUpdateSchema(BaseModel):
    is_checked: Optional[bool] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None


class RecipeSummarySchema(BaseModel):
    id: int
    name: str
    main_image_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class GroceryListSchema(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    items: List[GroceryListItemSchema] = []
    recipes: List[RecipeSummarySchema] = []
    
    model_config = ConfigDict(from_attributes=True)


class GroceryListCreateSchema(BaseModel):
    name: Optional[str] = "My Grocery List"
    recipe_ids: List[int] = []


class GroceryListAddRecipeSchema(BaseModel):
    recipe_id: int

