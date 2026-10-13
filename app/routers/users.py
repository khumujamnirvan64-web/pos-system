from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.schema.users import UserOut, UserUpdate
from app.models.users import User
from app.services.users import handle_get_current_user, handle_update_user, handle_delete_user, UserNotFound
from app.core.dependencies import get_db, get_current_user
from sqlalchemy.exc import IntegrityError 

router = APIRouter(
    prefix="/user/v1",
    tags=["User"]
)

@router.get("/me", response_model=UserOut)
def get_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
    try:
        return handle_get_current_user(db, current_user.id)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

@router.patch("", response_model=UserOut)
def update_user(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
    try:
        return handle_update_user(data, db, current_user.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already used."
        )

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    try:
        handle_delete_user(current_user.id, db)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )