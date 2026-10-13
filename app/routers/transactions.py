import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schema.transactions import TransactionIn, TransactionOut
from app.models.transactions import Transaction
from app.models.users import User
from app.core.dependencies import get_db, get_current_user
from collections.abc import Sequence
from app.services.transactions import handle_create_transaction, handle_get_my_transaction, handle_get_transaction, TransactionsNotFound, InsufficientStockInput, ItemNotFound

router = APIRouter(
    prefix="/transaction/v1",
    tags=["Transaction"]
)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=list[TransactionOut])
def create_transaction(
    transaction_batch: TransactionIn,
    db: Session = Depends(get_db),
    current_user:User = Depends(get_current_user)
) -> list[Transaction]:

    try:
        return handle_create_transaction(transaction_batch, db, current_user)
    except ItemNotFound as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientStockInput as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("", response_model=list[TransactionOut])
def get_my_transaction(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Sequence[Transaction]:
    
    return handle_get_my_transaction(current_user.id, db)

@router.get("/{id}", response_model=TransactionOut)
def get_transaction(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Transaction:
    try:
        return handle_get_transaction(current_user.id, id, db)
    except TransactionsNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "TRANSACTION_NOT_FOUND",
                "message": "Requested transaction ID doesn't exists"
            }
        )
    