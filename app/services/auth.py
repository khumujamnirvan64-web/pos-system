import logging
from fastapi import HTTPException, status
from app.utils.password_tokens import generate_password_tokens, verify_password_tokens, delete_password_token, ExpiredToken, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.schema.auth import ForgetPasswordRequest, ResetPasswordRequest
from app.models.users import User
from app.utils.send_email import send_password_reset_link
from app.utils.password_hash import hash_password

logger = logging.getLogger(__name__)

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
            detail="Token has expired, generate a new one to try again."
        )
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is invalid."
        )