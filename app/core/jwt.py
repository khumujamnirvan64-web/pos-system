import uuid
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

class InvalidTokenError(Exception):
    pass

def create_access_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_EXP_MINUTE
        )
    }

    return jwt.encode(payload, settings.ACCESS_TOKEN_KEY, algorithm=settings.ACCESS_TOKEN_ALGORITHM)

def verify_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.ACCESS_TOKEN_KEY, algorithms=[settings.ACCESS_TOKEN_ALGORITHM])

        user_id = payload.get("sub")

        if not user_id:
            raise InvalidTokenError
        return uuid.UUID(user_id)
    except jwt.InvalidTokenError:
        raise InvalidTokenError