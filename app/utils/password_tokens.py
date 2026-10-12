import jwt
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.password_tokens import PasswordToken

logger = logging.getLogger(__name__)

class InvalidToken(Exception):
    pass
class ExpiredToken(Exception):
    pass

def generate_password_tokens(email: str, db: Session):
    payload = {
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_EXP_MINUTE
        )
    }

    token = jwt.encode(payload, settings.PASSWORD_SECRET_KEY, settings.PASSWORD_ALGORITHM)

    token_data = PasswordToken(
        email=payload["email"],
        token_hash=token,
        exp=payload["exp"]
    )

    db.add(token_data)
    db.commit()

    return token

def verify_password_tokens(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.PASSWORD_SECRET_KEY, algorithms=[settings.PASSWORD_ALGORITHM])

        stmt = (
            select(PasswordToken)
            .where(
                PasswordToken.token_hash == token,
                PasswordToken.is_active == True
            )
        )

        db_token = db.execute(stmt).scalar_one_or_none()

        if not db_token:
            raise InvalidToken

        if db_token.exp < datetime.now(timezone.utc):
            raise ExpiredToken

        db_token.is_active = False

        return payload
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to verify token. Error: {e}")
        raise