from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.core.limiter import limiter
from sqlalchemy.orm import Session
from app.services.users import handle_login, handle_create_user, UserAlreadyExist, InvalidCredentials, UninvitedEmailError
from app.schema.users import LoginOut, UserIn, UserOut
from app.core.dependencies import get_db
from app.models.users import User

router = APIRouter(
    prefix="/auth/v1",
    tags=["Auth"]
)

@router.post("/login", response_model=LoginOut)
@limiter.limit("5/hour")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> LoginOut:
    try:
        return handle_login(db, form)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email or password."
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