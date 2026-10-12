from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy.orm import Session
from app.services.items import handle_get_items, handle_one_item, ItemNotFound
from app.schema.items import ItemOut
from app.core.dependencies import get_db, get_current_user
from app.models.users import User
from app.models.items import Item
from collections.abc import Sequence


router = APIRouter(
    prefix="/item/v1",
    tags=["Item"]
)

@router.get("", response_model=list[ItemOut])
def get_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Sequence[Item]:
    try:
        return handle_get_items(db)
    except ItemNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Items not found."
        )

@router.get("/{sku}", response_model=ItemOut)
def one_item(
    sku: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Item:
    try:
        return handle_one_item(sku, db)
    except ItemNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Items not found."
        )