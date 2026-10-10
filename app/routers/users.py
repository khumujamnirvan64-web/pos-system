from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.schema.users import UserIn, UserOut, UserUpdate
from app.models.users import User
from app.services.users import handle_create_user, handle_get_current_user, handle_login, handle_update_user, UserNotFound, UserAlreadyExist, UninvitedEmailError, InvalidCredentials
from app.core.dependencies import get_db, get_current_user
from app.schema.users import LoginOut
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError 

router = APIRouter(
    prefix="/user",
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

@router.post("/login", response_model=LoginOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> LoginOut:
    try:
        return handle_login(db, form)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email or password."
        )

@router.patch("/update", response_model=UserOut)
def update_user(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
    try:
        return handle_update_user(data, db, current_user.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already used."
        )

@router.post("/signup/{token}", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(token: str, data: UserIn, db: Session = Depends(get_db)) -> User:
    try:
        return handle_create_user(token, data, db)
    except UserAlreadyExist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    except UninvitedEmailError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Error! Use the invited email address to sign up."
        )

