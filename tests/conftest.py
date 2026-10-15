import os

import pytest
from dotenv import load_dotenv
from starlette.testclient import TestClient as TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

load_dotenv(".env.test")

from app.core.database import Base
from app.core.dependencies import get_db, get_current_admin, get_current_user
from app.main import app

from app.models.items import Item
from app.models.users import User
from app.models.transactions import Transaction
from app.models.sign_up_tokens import SignUpToken
from app.models.password_tokens import PasswordToken
from app.models.refresh_tokens import RefreshToken
from app.models.idempotency_keys import IdempotencyRecord

TEST_DB_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DB_URL:
    raise RuntimeError("Test database URL not found from .env.test.")

test_engine = create_engine(TEST_DB_URL)

testing_session = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = testing_session()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def create_test_user(db_session):
    test_user = User(
        id=uuid4(),
        email="user@example.com",
        password="12345678",
        name="user",
        is_admin=False
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    return test_user

@pytest.fixture
def create_admin_test_user(db_session):
    test_user = User(
            id=uuid4(),
            email="admin@example.com",
            password="12345678",
            name="admin",
            is_admin=True
        )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    
    return test_user

# Authenticated Non-Admin Client
@pytest.fixture
def non_admin_client(db_session, create_test_user):
    def overide_get_db():
        yield db_session
    
    def overide_get_current_user():
        return create_test_user

    app.dependency_overrides[get_db] = overide_get_db
    app.dependency_overrides[get_current_user] = overide_get_current_user
    app.dependency_overrides.pop(get_current_admin, None)
    try:
        with TestClient(app) as test_non_admin_client:
                yield test_non_admin_client
    finally:
        app.dependency_overrides.clear()


# Unauthenticated Client
@pytest.fixture
def unauthenticated_client(db_session):

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_admin, None)
    app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app) as test_unauthenticated_client:
            yield test_unauthenticated_client
    finally:
        app.dependency_overrides.clear()


# Admin client
@pytest.fixture
def admin_client(db_session, create_admin_test_user):
    def override_get_db():
        yield db_session

    def override_get_current_admin():
        return create_admin_test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_admin] = override_get_current_admin
    try:
        with TestClient(app) as admin_client:
             yield admin_client
    finally:
        app.dependency_overrides.clear()

@pytest.fixture
def missing_user_client(db_session):
    missing_user_id = uuid4()

    class FakeClient:
        id = missing_user_id
        is_admin = False

    def override_get_db():
        yield db_session
    def override_get_current_user():
        return FakeClient()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        with TestClient(app) as fake_client:
            yield fake_client
    finally:
        app.dependency_overrides.clear()