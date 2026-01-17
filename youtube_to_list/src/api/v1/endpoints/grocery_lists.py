from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database import get_db
from src.services import grocery_list_service
from src.schemas import (
    GroceryListSchema,
    GroceryListCreateSchema,
    GroceryListAddRecipeSchema,
    GroceryListItemSchema,
    GroceryListItemUpdateSchema,
    ErrorResponseSchema,
)
from src.auth import verify_api_key
from src.logging_config import get_logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.get("/", response_model=List[GroceryListSchema])
def list_grocery_lists(db: Session = Depends(get_db)):
    """Get all grocery lists."""
    lists = grocery_list_service.get_all_grocery_lists(db)
    return lists


@router.post("/", response_model=GroceryListSchema, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
def create_grocery_list(
    request: Request,
    data: GroceryListCreateSchema,
    db: Session = Depends(get_db),
):
    """Create a new grocery list from recipe IDs."""
    try:
        grocery_list = grocery_list_service.create_grocery_list(
            db, data.name or "My Grocery List", data.recipe_ids
        )
        logger.info(f"Created grocery list: {grocery_list.id}")
        return grocery_list
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{list_id}", response_model=GroceryListSchema, responses={404: {"model": ErrorResponseSchema}})
def get_grocery_list(list_id: int, db: Session = Depends(get_db)):
    """Get a specific grocery list by ID."""
    grocery_list = grocery_list_service.get_grocery_list(db, list_id)
    if not grocery_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grocery list with ID {list_id} not found.",
        )
    return grocery_list


@router.post("/{list_id}/recipes", response_model=GroceryListSchema, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
def add_recipe_to_list(
    request: Request,
    list_id: int,
    data: GroceryListAddRecipeSchema,
    db: Session = Depends(get_db),
):
    """Add a recipe to an existing grocery list."""
    grocery_list = grocery_list_service.add_recipe_to_list(db, list_id, data.recipe_id)
    if not grocery_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grocery list or recipe not found.",
        )
    logger.info(f"Added recipe {data.recipe_id} to list {list_id}")
    return grocery_list


@router.delete("/{list_id}/recipes/{recipe_id}", response_model=GroceryListSchema, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
def remove_recipe_from_list(
    request: Request,
    list_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """Remove a recipe from a grocery list."""
    grocery_list = grocery_list_service.remove_recipe_from_list(db, list_id, recipe_id)
    if not grocery_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grocery list not found.",
        )
    logger.info(f"Removed recipe {recipe_id} from list {list_id}")
    return grocery_list


@router.patch("/items/{item_id}/toggle", response_model=GroceryListItemSchema, dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
def toggle_grocery_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
):
    """Toggle the checked state of a grocery list item."""
    item = grocery_list_service.toggle_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found.",
        )
    return item


@router.patch("/items/{item_id}", response_model=GroceryListItemSchema, dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
def update_grocery_item(
    request: Request,
    item_id: int,
    update_data: GroceryListItemUpdateSchema,
    db: Session = Depends(get_db),
):
    """Update a grocery list item."""
    item = grocery_list_service.update_item(db, item_id, update_data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found.",
        )
    return item


@router.delete("/{list_id}", response_model=dict, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def delete_grocery_list(
    request: Request,
    list_id: int,
    db: Session = Depends(get_db),
):
    """Delete a grocery list."""
    success = grocery_list_service.delete_grocery_list(db, list_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grocery list with ID {list_id} not found.",
        )
    return {"message": f"Grocery list {list_id} deleted successfully"}
