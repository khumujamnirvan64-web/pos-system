import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from app.core.limiter import limiter
from sqlalchemy.orm import Session
from app.services.users import handle_login, handle_create_user, UserAlreadyExist, InvalidCredentials, UninvitedEmailError
from app.services.auth import handle_send_reset_link, handle_reset_password, handle_refresh_token, InvalidRefreshToken, RefreshTokenMissing
from app.schema.auth import ResetPasswordRequest, ForgetPasswordRequest
from app.schema.users import LoginOut, UserIn, UserOut
from app.core.dependencies import get_db, get_current_user
from app.models.users import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth/v1",
    tags=["Auth"]
)

REFRESH_TOKEN_EXPIRE_SECONDS = 7 * 24 * 60 * 60 # 7 days

@router.post("/login", response_model=LoginOut)
@limiter.limit("5/hour")
def login(request: Request, response: Response, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        access_token, refresh_token = handle_login(db, form)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_SECONDS
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email or password."
        )

@router.post("/forget-password")
@limiter.limit("3/5hour")
def forgot_password(request: Request, data: ForgetPasswordRequest, db: Session = Depends(get_db)):
    handle_send_reset_link(data, db)

    return {
        "detail": "If an account with that email exists, a password reset link has been sent.",
        "email": data.email
    }

@router.post("/signup/{token}", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(token: str, data: UserIn, db: Session = Depends(get_db)) -> User:
    try:
        return handle_create_user(token, data, db)
    except UserAlreadyExist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "USER_ALREADY_EXIST",
                "message": "User with this email already exists."
            }
        )
    except UninvitedEmailError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "UNIVITED_EMAIL",
                "message": "Un-invited email was sent to sign-up"
            }
        )

@router.post("/reset-password/{token}")
def reset_password(token: str, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    handle_reset_password(token, data, db)

    return{
        "detail": "Your password has been successfully updated. You can now log in."
    }

@router.post("/refresh")
def refresh_token(
    response: Response,
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    try:
        new_access_token, new_refresh_token = handle_refresh_token(refresh_token, db)
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_SECONDS
        )

        return {
                "access_token": new_access_token,
                "token_type": "Bearer"
            }

    except InvalidRefreshToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_REFRESH_TOKEN",
                "message": e
            }
        )
    except RefreshTokenMissing as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "REFRESH_TOKEN_MISSING",
                "message": e
            }
        )