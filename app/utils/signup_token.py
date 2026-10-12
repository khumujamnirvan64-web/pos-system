import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.sign_up_tokens import SignUpToken
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

def create_sign_up_token(email: str, db: Session) -> str:
    payload = {
        "email": str(email),
        "type": "signup_invite",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=settings.SIGNUP_EXP_MINUTE
        )
    }

    signup_token = jwt.encode(payload, settings.SIGN_UP_KEY, settings.SIGN_UP_ALGORITHM)

    db_data = SignUpToken(
        email=payload["email"],
        token=signup_token,
        exp=payload["exp"]
    )

    db.add(db_data)
    db.commit()

    return signup_token

def verify_sign_up_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.SIGN_UP_KEY, algorithms=[settings.SIGN_UP_ALGORITHM])

        stmt = (
            select(SignUpToken)
            .where(SignUpToken.token == token)
        )

        db_token = db.execute(stmt).scalar_one_or_none()

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signup Token"
            )

        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup token has expired. Please request a new one."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signup token"
        )

def delete_signup_token(token, db: Session):
    stmt = (
        select(SignUpToken)
        .where(SignUpToken.token == token)
    )

    db_token = db.execute(stmt).scalar_one_or_none()

    if not db_token:
        logger.warning(f"Attempted to delete non-existent signup token: {token}")
        return

    try:
        db.delete(db_token)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception(f"Database error while deleting signup token {token}: {e}")
        raise
