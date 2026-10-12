import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schema.users import UserIn, UserUpdate, ToggleAdminUpdate
from app.models.users import User
from app.utils.password_hash import hash_password
from app.utils.signup_token import delete_signup_token, verify_sign_up_token
from app.schema.users import LoginOut
from app.utils.password_hash import verify_password
from app.core.jwt import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from collections.abc import Sequence

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

def handle_login(db: Session, form: OAuth2PasswordRequestForm = Depends()) -> LoginOut:
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
    

    return LoginOut(access_token=token)

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

    updating_user.is_admin = update_data.toggle

    db.commit()
    db.refresh(updating_user)

    return updating_user

def handle_delete_user_by_admin(user_id: uuid.UUID, db: Session) -> None:
    stmt = select(User).where(User.id == user_id)

    deleting_user = db.execute(stmt).scalar_one_or_none()

    if not deleting_user:
        raise UserNotFound

    db.delete(deleting_user)
    db.commit()

def handle_get_all_user(db: Session) -> Sequence[User]:
    stmt = select(User)

    users = db.execute(stmt).scalars().all()

    if not users:
        raise UserNotFound

    return users
