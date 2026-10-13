import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schema.users import UserIn, UserUpdate, ToggleAdminUpdate
from app.models.users import User
from app.utils.password_hash import hash_password, verify_password
from app.utils.signup_token import delete_signup_token, verify_sign_up_token
from app.utils.count_admin import count_current_admin
from app.utils.refresh_hash import hash_token
from app.core.jwt import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from collections.abc import Sequence
from app.models.refresh_tokens import RefreshToken
from datetime import datetime, timezone, timedelta
from app.utils.refresh_tokens import generate_refresh_token
from app.core.config import settings

class UserNotFound(Exception):
    pass
class UserAlreadyExist(Exception):
    pass
class UninvitedEmailError(Exception):
    pass
class InvalidCredentials(Exception):
    pass

def handle_create_user(token: str, data: UserIn, db: Session) -> User:
    normalized_email = data.email.lower().strip()
    normalized_name = data.name.lower().strip()
    hash = hash_password(data.password)

    payload = verify_sign_up_token(token, db)

    payload_email = payload.get("email")

    if normalized_email != payload_email:
        raise UninvitedEmailError

    stmt = select(User).where(User.email == normalized_email)
    existing = db.execute(stmt).scalar_one_or_none()

    if existing:
        raise UserAlreadyExist


    new_user = User(
        email=normalized_email,
        name=normalized_name,
        password=hash
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    delete_signup_token(token, db)

    return new_user

def handle_get_current_user(db: Session, user_id: uuid.UUID) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id)
    )

    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise UserNotFound

    return user

def handle_login(db: Session, form: OAuth2PasswordRequestForm):
    normalized_email = form.username.lower().strip()

    stmt = (
        select(User)
        .where(User.email == normalized_email)
    )

    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise InvalidCredentials

    check_password = verify_password(user.password, form.password)

    if check_password == False:
        raise InvalidCredentials

    token = create_access_token(str(user.id))
    generated_refresh_token = generate_refresh_token()
    expired_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXP_DAY
    )

    hash_refresh = hash_token(generated_refresh_token)

    db_data = RefreshToken(
        user_id=str(user.id),
        token=hash_refresh,
        expired_at=expired_at
    )

    db.add(db_data)
    db.commit()

    return token, generated_refresh_token

def handle_update_user(data: UserUpdate, db: Session, user_id: uuid.UUID) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id)
    )

    updating_user = db.execute(stmt).scalar_one_or_none()

    if not updating_user:
        raise UserNotFound

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(updating_user, field, value)

    db.commit()
    db.refresh(updating_user)

    return updating_user

def handle_delete_user(user_id: uuid.UUID, db: Session) -> None:

    stmt = (
        select(User)
        .where(User.id == user_id)
    )

    deleting_user = db.execute(stmt).scalar_one_or_none()

    if not deleting_user:
        raise UserNotFound

    if deleting_user.is_admin:
        count_current_admin(db)

    db.delete(deleting_user)
    db.commit()

# Give admin the privilege to assign normal user as admin or remove
def handle_admin_user_update(user_id: uuid.UUID, update_data: ToggleAdminUpdate, db: Session) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id)
    )

    updating_user = db.execute(stmt).scalar_one_or_none()

    if not updating_user:
        raise UserNotFound

    if updating_user.is_admin:
        count_current_admin(db)

    updating_user.is_admin = update_data.is_admin

    db.commit()
    db.refresh(updating_user)

    return updating_user

def handle_delete_user_by_admin(user_id: uuid.UUID, db: Session) -> None:
    stmt = select(User).where(User.id == user_id)

    deleting_user = db.execute(stmt).scalar_one_or_none()

    if not deleting_user:
        raise UserNotFound
    
    if deleting_user.is_admin:
        count_current_admin(db)

    db.delete(deleting_user)
    db.commit()

def handle_get_all_user(db: Session) -> Sequence[User]:
    stmt = select(User)

    users = db.execute(stmt).scalars().all()

    if not users:
        return []

    return users
