import uuid
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_admin
from fastapi import Depends, APIRouter, HTTPException, status, Request
from app.schema.signup_tokens import GenerateIn
from app.utils.signup_token import create_sign_up_token
from app.schema.items import ItemIn, ItemUpdate, ItemOut
from app.schema.users import UserOut, ToggleAdminUpdate
from app.services.items import handle_create_item, handle_delete_item, handle_update_item, ItemNotFound, ItemAlreadyExists
from app.models.users import User
from app.models.items import Item
from sqlalchemy.exc import IntegrityError
from app.services.users import handle_admin_user_update, handle_delete_user_by_admin, handle_get_all_user, UserNotFound
from collections.abc import Sequence
from app.services.transactions import handle_get_all_transactions, handle_delete_transaction, TransactionsNotFound
from app.schema.transactions import TransactionAdminOut
from app.models.transactions import Transaction
from app.core.limiter import limiter

router = APIRouter(
    prefix="/admin/v1",
    tags=["Admin"]
)

@router.post("/token/generate")
@limiter.limit("5/3 hour")
def generate_signup_token(
    request: Request,
    data: GenerateIn,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    normalized_email = data.email.lower().strip()

    singup_token = create_sign_up_token(normalized_email, db)

    return {"invite_token": f"{singup_token}"}

# Item routes
@router.post("/item", status_code=status.HTTP_201_CREATED, response_model=ItemOut)
def create_item(
    payload: ItemIn,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
) -> Item:
    try:
        return handle_create_item(payload, db)
    except ItemAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item with the same name or SKU already exists"
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item with this SKU already exist"
        )

@router.patch("/item/{sku}", response_model=ItemOut)
def update_item(
    sku: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
) -> Item:
    try:
        return handle_update_item(sku, payload, db)
    except ItemNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found."
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item with this SKU already exist"
        )

@router.delete("/item/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    sku: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
) -> None:
    try:
        handle_delete_item(sku, db)
    except ItemNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found."
        )

#User routes
@router.get("/user", response_model=list[UserOut])
def get_all_user(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
) -> Sequence[User]:
    try:
        return handle_get_all_user(db)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

@router.patch("/user/{user_id}", response_model=UserOut)
def update_user_to_admin(
    user_id: uuid.UUID,
    update_data: ToggleAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
) -> User:
    try:
        return handle_admin_user_update(user_id, update_data, db)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_admin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin) 
) -> None:
    try:
        handle_delete_user_by_admin(user_id, db)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

# Transactions
@router.get("/transaction", response_model=list[TransactionAdminOut])
def get_all_transactions(
    limit: int = 25,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
) -> Sequence[Transaction]:
    try:
        return handle_get_all_transactions(db, limit, offset)
    except TransactionsNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found."
        )

@router.delete("/transaction/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Session = Depends(get_current_admin)
) -> None:
    try:
        handle_delete_transaction(transaction_id, db)
    except TransactionsNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found."
        )