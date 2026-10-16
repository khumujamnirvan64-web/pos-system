from uuid import uuid4
from tests.conftest import unauthenticated_client, db_session, admin_client, non_admin_client
from app.models.users import User
from urllib.parse import urlparse
from app.utils.password_hash import hash_password, verify_password

def test_login(unauthenticated_client, db_session):
    user = User(
        id=uuid4(),
        email="test@example.com",
        password=hash_password("123456789"),
        name="test",
        is_admin=False
    )

    db_session.add(user)
    db_session.commit()

    payload = {
        "username": "test@example.com",
        "password": "123456789"
    }

    response = unauthenticated_client.post("/auth/v1/login", data=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["access_token"]
    assert data["token_type"] == "Bearer"

def test_login_error(unauthenticated_client):
    payload = {
            "username": "test@example.com",
            "password": "123456789"
        }

    response = unauthenticated_client.post(
        "/auth/v1/login",
        data=payload
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["error"] == "INVALID_CREDENTIALS"

def test_login_allow_access_to_protected_endpoint(unauthenticated_client, db_session):
    user = User(
        id=uuid4(),
        email="test@example.com",
        password=hash_password("123456789"),
        name="test",
        is_admin=False
    )

    db_session.add(user)
    db_session.commit()

    payload = {
        "username": "test@example.com",
        "password": "123456789"
    }

    response = unauthenticated_client.post(
        "/auth/v1/login",
        data=payload
    )

    if response.status_code == 200:
        get_user = unauthenticated_client.get(
            "/user/v1/me",
            headers={
                "Authorization": f'Bearer {response.json()["access_token"]}'
            }
        )

        assert get_user.status_code == 200
        assert get_user.json()["email"] == "test@example.com"

def test_invalid_jwt_token(unauthenticated_client, db_session):
    random_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30"

    user = User(
            id=uuid4(),
            email="test@example.com",
            password=hash_password("123456789"),
            name="test",
            is_admin=False
        )

    db_session.add(user)
    db_session.commit()

    payload = {
        "username": "test@example.com",
        "password": "123456789"
    }

    response = unauthenticated_client.post(
        "/auth/v1/login",
        data=payload
    )

    if response.status_code == 200:
        get_user = unauthenticated_client.get(
                    "/user/v1/me",
                    headers={
                        "Authorization": f'Bearer {random_jwt}'
                    }
                )
        assert get_user.status_code == 401

def test_forgot_password(unauthenticated_client):
    payload = {
        "email": "test@example.com"
    }

    response = unauthenticated_client.post("/auth/v1/forget-password", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "If an account with that email exists, a password reset link has been sent."
    assert data["email"] == "test@example.com"

def test_create_signup_token(admin_client):
    payload = {"email": "test@example.com"}
    response = admin_client.post("/admin/v1/token/generate", json=payload)
    assert response.status_code == 200
    assert response.json()["invite_token"]


def test_create_sign_up_token_by_non_admin(non_admin_client):
    payload = {"email": "test@example.com"}
    response = non_admin_client.post("/admin/v1/token/generate", json=payload)

    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["error"] == "NOT_ADMIN"

def test_create_user(unauthenticated_client, admin_client):
    payload = {"email": "test@example.com"}
    response = admin_client.post("/admin/v1/token/generate", json=payload)
    signup_token = response.json()["invite_token"]

    if response.status_code == 200:
        payload = {
            "email": "test@example.com",
            "password": "123456789",
            "name": "test"
        }

        create_user = unauthenticated_client.post(
            f"/auth/v1/signup/{signup_token}",
            json=payload
        )
        assert create_user.status_code == 201
        data = create_user.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "test"

def test_create_user_existing_email(unauthenticated_client, admin_client, db_session):
    payload = {"email": "test@example.com"}
    response = admin_client.post("/admin/v1/token/generate", json=payload)
    signup_token = response.json()["invite_token"]

    existing_user = User(
        email="test@example.com",
        password=hash_password("123456789"),
        name="test"
    )

    db_session.add(existing_user)
    db_session.commit()

    if response.status_code == 200:
        payload = {
            "email": "test@example.com",
            "password": "123456789",
            "name": "test"
        }

        create_user = unauthenticated_client.post(
            f"/auth/v1/signup/{signup_token}",
            json=payload
        )
        assert create_user.status_code == 409
        assert create_user.json()["detail"]["error"] == "USER_ALREADY_EXIST"

def test_create_user_uninvited_email(unauthenticated_client ,admin_client):
    payload = {"email": "test@example.com"}
    response = admin_client.post("/admin/v1/token/generate", json=payload)
    signup_token = response.json()["invite_token"]

    if response.status_code == 200:
        payload = {
            "email": "test2@example.com",
            "password": "123456789",
            "name": "test"
        }

        create_user = unauthenticated_client.post(
            f"/auth/v1/signup/{signup_token}",
            json=payload
        )

        assert create_user.status_code == 403
        assert create_user.json()["detail"]["error"] == "UNINVITED_EMAIL"

def test_create_user_wrong_token(unauthenticated_client):
    payload = {
                "email": "test@example.com",
                "password": "123456789",
                "name": "test"
            }

    response = unauthenticated_client.post(
        "/auth/v1/signup/123",
        json=payload
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "INVALID_SIGNUP_TOKEN"


from urllib.parse import urlparse
from app.utils.password_hash import hash_password, verify_password


def test_password_reset_flow(
    unauthenticated_client,
    create_test_user,
    db_session,
    monkeypatch,
):
    old_password = "OldPassword123!"
    create_test_user.password = hash_password(old_password)
    db_session.commit()

    captured_emails = []

    def fake_send_password_reset_link(email, reset_url):
        captured_emails.append({
            "email": email,
            "reset_url": reset_url,
        })

    monkeypatch.setattr(
        "app.services.auth.send_password_reset_link",
        fake_send_password_reset_link,
    )

    response = unauthenticated_client.post(
        "/auth/v1/forget-password",
        json={"email": create_test_user.email},
    )

    assert response.status_code == 200
    assert len(captured_emails) == 1

    # Step 2: Extract the token from the captured email URL.
    reset_url = captured_emails[0]["reset_url"]
    token = urlparse(reset_url).path.rsplit("/", 1)[-1]

    assert token

    new_password = "NewPassword456!"

    reset_response = unauthenticated_client.post(
        f"/auth/v1/reset-password/{token}",
        json={"new_password": new_password},
    )

    assert reset_response.status_code == 200

    db_session.refresh(create_test_user)

    assert verify_password(create_test_user.password, new_password)
    assert not verify_password(create_test_user.password, old_password)

def test_refresh_token_flow(unauthenticated_client, db_session):
    user = User(
            id=uuid4(),
            email="test@example.com",
            password=hash_password("123456789"),
            name="test",
            is_admin=False
        )
    
    db_session.add(user)
    db_session.commit()

    payload = {
        "username": "test@example.com",
        "password": "123456789"
    }

    response = unauthenticated_client.post("/auth/v1/login", data=payload)

    refresh_token = response.cookies.get("refresh_token")

    refresh_response = unauthenticated_client.post("/auth/v1/refresh", cookies={"refresh_token": refresh_token})

    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]
    assert refresh_response.json()["token_type"] == "Bearer"

def test_refresh_token_error_invalid_token(unauthenticated_client, db_session):
    user = User(
            id=uuid4(),
            email="test@example.com",
            password=hash_password("123456789"),
            name="test",
            is_admin=False
        )
    
    db_session.add(user)
    db_session.commit()

    payload = {
        "username": "test@example.com",
        "password": "123456789"
    }

    unauthenticated_client.post("/auth/v1/login", data=payload)

    refresh_response = unauthenticated_client.post("/auth/v1/refresh", cookies={"refresh_token": "123456789"})
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"]["error"] == "INVALID_REFRESH_TOKEN"


def test_refresh_token_error_missing_token(unauthenticated_client, db_session):
    user = User(
            id=uuid4(),
            email="test@example.com",
            password=hash_password("123456789"),
            name="test",
            is_admin=False
        )
    
    db_session.add(user)
    db_session.commit()

    payload = {
        "username": "test@example.com",
        "password": "123456789"
    }

    unauthenticated_client.post("/auth/v1/login", data=payload)

    refresh_response = unauthenticated_client.post("/auth/v1/refresh")
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"]["error"] == "REFRESH_TOKEN_MISSING"

def test_logout(unauthenticated_client, db_session):
    user = User(
        id=uuid4(),
        email="test@example.com",
        password=hash_password("123456789"),
        name="test",
        is_admin=False
    )

    db_session.add(user)
    db_session.commit()

    payload = {
        "username": "test@example.com",
        "password": "123456789"
    }

    response = unauthenticated_client.post(
        "/auth/v1/login",
        data=payload
    )

    if response.status_code == 200:
        logout_response = unauthenticated_client.post(
            "/auth/v1/logout",
            headers={
                "Authorization": f'Bearer {response.json()["access_token"]}'
            }
        )
        deleted_cookie = logout_response.cookies.get("refresh_token")


        assert logout_response.status_code == 200
        assert logout_response.json()["message"]
        assert not deleted_cookie