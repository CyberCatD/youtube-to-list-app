from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from src.database import get_db
from src.services import recipe_service
from src.schemas import RecipeSchema, RecipeListResponseSchema, ErrorResponseSchema
from src.auth import verify_api_key

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

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

@router.get("/", response_model=RecipeListResponseSchema, responses={500: {"model": ErrorResponseSchema}})
def list_recipes(
    db: Session = Depends(get_db),
):
    """
    Retrieves a list of all created recipes.
    """
    try:
        recipes = recipe_service.get_all_recipes(db)
        logger.info(f"Retrieved {len(recipes)} recipes from database")
        return RecipeListResponseSchema(recipes=recipes)
    except Exception as e:
        logger.error(f"Error fetching recipes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching recipes: {e}",
        )

@router.delete("/{recipe_id}", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}}, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def delete_recipe(
    request: Request,
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """
    Deletes a specific recipe by its ID.
    """
    deleted_recipe = recipe_service.delete_recipe_by_id(db, recipe_id)
    if deleted_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found.",
        )
    logger.info(f"Deleted recipe ID: {recipe_id}")
    return deleted_recipe
