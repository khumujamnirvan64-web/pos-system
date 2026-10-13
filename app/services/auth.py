import logging
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.schema.auth import ForgetPasswordRequest, ResetPasswordRequest
from app.models.users import User
from app.models.refresh_tokens import RefreshToken
from app.utils.send_email import send_password_reset_link
from app.utils.password_hash import hash_password
from app.utils.refresh_hash import hash_token
from app.utils.password_tokens import generate_password_tokens, verify_password_tokens, ExpiredToken, InvalidToken
from app.utils.refresh_tokens import generate_refresh_token
from app.utils.refresh_hash import hash_token
from app.core.jwt import create_access_token
from app.core.config import settings

logger = logging.getLogger(__name__)

class RefreshTokenMissing(Exception):
    pass
class InvalidRefreshToken(Exception):
    pass

def handle_send_reset_link(
        data: ForgetPasswordRequest,
        db: Session
):
    normalized_email = data.email.lower().strip()
    
    stmt = (
        select(User)
        .where(User.email == normalized_email)
    )

    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        logger.info(f"Password reset requested for non-existent email: {normalized_email}")
        return

    token = generate_password_tokens(normalized_email, db)

    reset_url = f"http://localhost:5173/auth/v1/reset-password/{token}"

    send_password_reset_link(normalized_email, reset_url)

def handle_reset_password(token: str, data: ResetPasswordRequest, db: Session):
    try:
        payload = verify_password_tokens(token, db)

        email = payload.get("email")

        stmt = (
            select(User)
            .where(User.email == email)
        )

        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The password reset link is invalid or has expired."
            )

        new_password = data.new_password
        new_hash_password = hash_password(new_password)
        user.password = new_hash_password

        db.commit()

    except ExpiredToken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "EXPIRED_TOKEN",
                "message": "Token has expired, generate a new one to try again."
            }
        )
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_TOKEN",
                "message": "Token is invalid."
            }
        )

def handle_refresh_token(refresh_token: str, db: Session):
    if not refresh_token:
        raise RefreshTokenMissing("Refresh token missing from cookies.")

    incoming_hash = hash_token(refresh_token)

    stmt = (
        select(RefreshToken)
        .where(
            RefreshToken.token == incoming_hash,
            RefreshToken.is_alive == True,
            RefreshToken.expired_at > datetime.now(timezone.utc)
        )
        .with_for_update()
    )

    db_token = db.execute(stmt).scalar_one_or_none()

    if not db_token:
        raise InvalidRefreshToken("Invalid or expired refresh token.")

    new_access_token = create_access_token(str(db_token.user_id))

    new_refresh_token = generate_refresh_token()
    expired_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXP_DAY
    )

    hash_new_token = hash_token(new_refresh_token)

    new_db_token = RefreshToken(
        user_id=str(db_token.user_id),
        token=hash_new_token,
        expired_at=expired_at
    )

    db.add(new_db_token)
    db.delete(db_token)
    db.commit()

    return new_access_token, new_refresh_token
