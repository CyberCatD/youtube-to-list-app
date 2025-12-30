from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.services import recipe_service
from src.schemas import RecipeSchema, RecipeListResponseSchema, ErrorResponseSchema

router = APIRouter()

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
        print(f"--- DEBUG: BACKEND DATA ---")
        print(recipes)
        print(f"--------------------------")
        return RecipeListResponseSchema(recipes=recipes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching recipes: {e}",
        )

@router.delete("/{recipe_id}", response_model=RecipeSchema, responses={404: {"model": ErrorResponseSchema}})
def delete_recipe(
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
    return deleted_recipe
