from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
from app.models.users import User
from app.core.jwt import verify_access_token, InvalidTokenError
from fastapi import HTTPException, status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/v1/login")

def get_db():
    db: Session = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)

):
    try:
        user_id = verify_access_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    stmt = (
        select(User)
        .where(User.id == user_id)
    )

    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

def get_current_admin(
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin access required"
        )
    return current_user