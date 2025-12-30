from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.services import card_service
from src.schemas import CardDBSchema, CardListResponseSchema, ErrorResponseSchema

router = APIRouter()

@router.get("/{card_id}", response_model=CardDBSchema, responses={404: {"model": ErrorResponseSchema}})
def get_card(
    card_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves a specific card by its ID.
    """
    db_card = card_service.get_card_by_id(db, card_id)
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with ID {card_id} not found.",
        )
    return db_card

@router.get("/", response_model=CardListResponseSchema, responses={500: {"model": ErrorResponseSchema}})
def list_cards(
    db: Session = Depends(get_db),
):
    """
    Retrieves a list of all created cards.
    """
    try:
        cards = card_service.get_all_cards(db)
        return CardListResponseSchema(cards=cards)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching cards: {e}",
        )

@router.delete("/{card_id}", response_model=CardDBSchema, responses={404: {"model": ErrorResponseSchema}})
def delete_card(
    card_id: int,
    db: Session = Depends(get_db),
):
    """
    Deletes a specific card by its ID.
    """
    deleted_card = card_service.delete_card_by_id(db, card_id)
    if deleted_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with ID {card_id} not found.",
        )
    return deleted_card

