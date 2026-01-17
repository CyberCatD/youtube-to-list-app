from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from math import ceil
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database import get_db
from src.services import recipe_service, image_service, nutrition_service
from src.schemas import RecipeSchema, RecipeListResponseSchema, PaginatedRecipeListResponseSchema, ErrorResponseSchema, RecipeUpdateSchema
from src.auth import verify_api_key
from src.models import Recipe
from src.logging_config import get_logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)

@router.get("/", response_model=PaginatedRecipeListResponseSchema, responses={500: {"model": ErrorResponseSchema}})
def list_recipes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine"),
    db: Session = Depends(get_db),
):
    """
    Retrieves a paginated list of recipes with optional filtering.
    """
    try:
        query = db.query(Recipe).filter(Recipe.is_deleted == False)
        
        if category:
            query = query.filter(Recipe.category.ilike(f"%{category}%"))
        if cuisine:
            query = query.filter(Recipe.cuisine.ilike(f"%{cuisine}%"))
        
        total = query.count()
        
        offset = (page - 1) * page_size
        recipes = query.order_by(Recipe.created_at.desc()).offset(offset).limit(page_size).all()
        
        total_pages = ceil(total / page_size) if total > 0 else 0
        
        logger.info(f"Retrieved {len(recipes)} recipes (page {page}/{total_pages}, total: {total})")
        return PaginatedRecipeListResponseSchema(
            recipes=recipes,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Error fetching recipes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching recipes: {e}",
        )

@router.get("/search", response_model=PaginatedRecipeListResponseSchema)
def search_recipes(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Search recipes by name, category, or cuisine.
    """
    search_term = f"%{q}%"
    
    query = db.query(Recipe).filter(
        Recipe.is_deleted == False,
        or_(
            Recipe.name.ilike(search_term),
            Recipe.category.ilike(search_term),
            Recipe.cuisine.ilike(search_term)
        )
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    recipes = query.order_by(Recipe.created_at.desc()).offset(offset).limit(page_size).all()
    
    total_pages = ceil(total / page_size) if total > 0 else 0
    
    logger.info(f"Search '{q}': found {total} recipes")
    return PaginatedRecipeListResponseSchema(
        recipes=recipes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/trash/count", response_model=dict)
def get_trash_count(
    db: Session = Depends(get_db),
):
    """
    Returns the count of recipes currently in trash.
    """
    count = recipe_service.get_trash_count(db)
    return {"count": count}

@router.get("/{recipe_id}", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}})
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves a specific recipe by its ID.
    """
    db_recipe = recipe_service.get_recipe_by_id(db, recipe_id)
    if db_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found.",
        )
    return db_recipe

@router.get("/{recipe_id}/nutrition", responses={404: {"model": ErrorResponseSchema}})
def get_recipe_nutrition(
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """
    Calculate and return nutrition information for a recipe.
    Uses USDA FoodData Central API to lookup ingredient nutrition.
    """
    recipe = recipe_service.get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found.",
        )
    
    ingredients = []
    for ing in recipe.ingredients:
        ingredients.append({
            "name": ing.ingredient.name,
            "quantity": ing.quantity,
            "unit": ing.unit,
        })
    
    servings = nutrition_service.parse_servings(recipe.servings)
    nutrition_data = nutrition_service.calculate_recipe_nutrition(ingredients, servings)
    
    nutrition_data["recipe_id"] = recipe_id
    nutrition_data["recipe_name"] = recipe.name
    
    logger.info(f"Calculated nutrition for recipe ID {recipe_id}: {nutrition_data['ingredients_analyzed']} ingredients analyzed")
    return nutrition_data

@router.delete("/{recipe_id}", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def delete_recipe(
    request: Request,
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """
    Soft delete - moves a recipe to trash.
    """
    deleted_recipe = recipe_service.move_to_trash(db, recipe_id)
    if deleted_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found.",
        )
    logger.info(f"Moved recipe ID {recipe_id} to trash")
    return deleted_recipe

@router.post("/trash/restore", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def restore_from_trash(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Restores the most recently deleted recipe from trash.
    """
    restored_recipe = recipe_service.restore_most_recent_from_trash(db)
    if restored_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recipes in trash to restore.",
        )
    logger.info(f"Restored recipe ID {restored_recipe.id} from trash")
    return restored_recipe

@router.delete("/trash/purge", response_model=dict, dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
def purge_trash(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Permanently deletes all recipes in trash.
    """
    count = recipe_service.purge_trash(db)
    logger.info(f"Purged {count} recipes from trash")
    return {"message": f"Purged {count} recipes from trash", "count": count}

@router.patch("/{recipe_id}", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
def update_recipe(
    request: Request,
    recipe_id: int,
    update_data: RecipeUpdateSchema,
    db: Session = Depends(get_db),
):
    """
    Updates a recipe's editable fields (currently: name).
    """
    updated_recipe = recipe_service.update_recipe(db, recipe_id, update_data.model_dump(exclude_unset=True))
    if updated_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found.",
        )
    logger.info(f"Updated recipe ID {recipe_id}")
    return updated_recipe

@router.post("/{recipe_id}/image", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def upload_recipe_image(
    request: Request,
    recipe_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a custom image for a recipe.
    Accepts JPG, PNG, GIF, WEBP files up to 5MB.
    """
    recipe = recipe_service.get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found.",
        )
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPG, PNG, GIF, or WEBP).",
        )
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file must be less than 5MB.",
        )
    
    image_path = image_service.save_uploaded_image(content, file.filename or "image.jpg")
    
    updated_recipe = recipe_service.update_recipe(db, recipe_id, {"main_image_url": image_path})
    logger.info(f"Uploaded image for recipe ID {recipe_id}: {image_path}")
    return updated_recipe

@router.post("/{recipe_id}/fetch-image", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
def fetch_recipe_image(
    request: Request,
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """
    Attempt to fetch/refresh the image for a recipe using Microlink API.
    Useful when the original image URL has expired.
    """
    recipe = recipe_service.get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found.",
        )
    
    new_image_url = image_service.get_best_image_url(recipe.source_url, recipe.main_image_url)
    
    if new_image_url and new_image_url != recipe.main_image_url:
        updated_recipe = recipe_service.update_recipe(db, recipe_id, {"main_image_url": new_image_url})
        logger.info(f"Updated image for recipe ID {recipe_id}")
        return updated_recipe
    
    return recipe
