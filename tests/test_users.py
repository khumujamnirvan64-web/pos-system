from tests.conftest import non_admin_client, unauthenticated_client, admin_client, missing_user_client, db_session
from app.models.users import User
from uuid import uuid4

# Unauthenticate Tests
def test_unauthenticated_get_user(unauthenticated_client):
    response = unauthenticated_client.get("/user/v1/me")
    assert response.status_code == 401

def test_unauthenticated_update_user(unauthenticated_client):
    response = unauthenticated_client.patch("/user/v1")
    assert response.status_code == 401

def test_unauthenticated_delete_user(unauthenticated_client):
    response = unauthenticated_client.delete("/user/v1")
    assert response.status_code == 401

def test_unauthenticated_get_all_user(unauthenticated_client):
    response = unauthenticated_client.get("/admin/v1/user")
    assert response.status_code == 401

def test_unauthenticated_update_user_to_admin(unauthenticated_client):
    response = unauthenticated_client.patch("/admin/v1/user/123")
    assert response.status_code == 401

def test_unauthenticated_delete_user_by_admin(unauthenticated_client):
    response = unauthenticated_client.delete("/admin/v1/user/123")
    assert response.status_code == 401

# Authenticated Tests
def test_authenticated_get_user(non_admin_client):

    response = non_admin_client.get("/user/v1/me")
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert response.json()["email"] == "user@example.com"
    assert response.json()["name"] == "user"
    assert response.json()["is_admin"] == False 

def test_authenticated_user_not_found_error(missing_user_client):
    response = missing_user_client.get("/user/v1/me")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "USER_NOT_FOUND"

def test_authenticated_update_user(non_admin_client):
    payload = {
        "email": "updated@example.com",
        "name": "updated"
    }

    response = non_admin_client.patch("/user/v1", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "updated"
    assert response.json()["email"] == "updated@example.com"

def test_authenticated_update_user_error(non_admin_client, db_session):
    existing_user = User(
        email="existing@example.com",
        password="existing",
        name="existing",
        is_admin=False
    )

    db_session.add(existing_user)
    db_session.commit()

    payload = {
            "email": "existing@example.com",
            "name": "existing"
        }

    response = non_admin_client.patch("/user/v1", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "CONFLICT"

def test_authenticated_delete_user(non_admin_client):
    response = non_admin_client.delete("/user/v1")
    assert response.status_code == 204

def test_authenticated_delete_non_existent_user(missing_user_client):
    response = missing_user_client.delete("/user/v1")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "USER_NOT_FOUND"

# Admin Tests
def test_admin_get_all_user(admin_client):

    response = admin_client.get("/admin/v1/user")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "admin@example.com"
    assert response.json()[0]["name"] == "admin"
    assert response.json()[0]["is_admin"] == True

def test_admin_update_user_to_admin(admin_client, db_session):
    user_id = uuid4()

    existing_user = User(
        id=user_id,
        email="existing@example.com",
        password="existing",
        name="existing",
        is_admin=False
    )

    db_session.add(existing_user)
    db_session.commit()

    payload = {
        "is_admin": True
    }

    response = admin_client.patch(f"/admin/v1/user/{user_id}", json=payload)

    assert response.status_code == 200
    assert response.json()["is_admin"] == True
    assert response.json()["email"] == "existing@example.com"

def test_admin_non_existent_update_user_to_admin(admin_client):
    user_id = uuid4()
    payload = {
            "is_admin": True
        }
    response = admin_client.patch(f"/admin/v1/user/{user_id}", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "USER_NOT_FOUND"

def test_admin_delete_user_by_admin(admin_client, db_session):
    user_id = uuid4()
    
    existing_user = User(
        id=user_id,
        email="existing@example.com",
        password="existing",
        name="existing",
        is_admin=False
    )
    
    db_session.add(existing_user)
    db_session.commit()

    response = admin_client.delete(f"/admin/v1/user/{user_id}")

    assert response.status_code == 204

def test_admin_delete_non_existent_user_by_admin(admin_client):
    user_id = uuid4()
    response = admin_client.delete(f"/admin/v1/user/{user_id}")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "USER_NOT_FOUND"