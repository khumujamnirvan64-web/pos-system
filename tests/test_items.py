from fastapi import Depends
from tests.conftest import db_session, non_admin_client, unauthenticated_client, admin_client
from app.models.items import Item
from app.models.users import User
from app.core.dependencies import get_current_admin, get_current_user

def create_test_item(db_session):
    item = Item(
        sku=101,
        name="test product",
        current_stock=20
    )

    db_session.add(item)
    db_session.commit()
    

# Authenticated normal user test
def test_get_empty_items(non_admin_client, current_user: User = Depends(get_current_user)):
    response = non_admin_client.get("/item/v1")

    assert response.status_code == 200
    assert response.json() == []

def test_get_saved_items(non_admin_client, db_session):
    create_test_item(db_session)

    response = non_admin_client.get("/item/v1")

    assert response.status_code == 200

    items = response.json()

    assert len(items) == 1
    assert items[0]["sku"] == 101
    assert items[0]["name"] == "test product"
    assert items[0]["current_stock"] == 20

def test_get_one_item_by_sku(non_admin_client, db_session):
    create_test_item(db_session)

    response = non_admin_client.get("/item/v1/101")

    assert response.status_code == 200

    items = response.json()
    
    assert len(items) == 5
    assert items["sku"] == 101
    assert items["name"] == "test product"
    assert items["current_stock"] == 20

def test_non_admin_create_item(non_admin_client):
    item_data = {
        "sku": 101,
        "name": "laptop",
        "initial_stock": 20
    }
    
    response = non_admin_client.post("admin/v1/item", json=item_data)
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "NOT_ADMIN"
    assert response.json()["detail"]["message"] == "Admin access required"

def test_non_admin_updated_item(non_admin_client, db_session):
    create_test_item(db_session)
        
    payload = {
        "name":"updated",
        "current_stock":20
    }

    response = non_admin_client.patch("/admin/v1/item/101", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "NOT_ADMIN"

def test_non_admin_delete_item(non_admin_client, db_session):
    create_test_item(db_session)

    response = non_admin_client.delete("/admin/v1/item/101")

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "NOT_ADMIN"

# ====END===

# Unauthenticated users test
def test_unauthenticate_get_items(unauthenticated_client):
    response = unauthenticated_client.get("/item/v1")

    assert response.status_code == 401
    response_object = response.json()

    assert response_object["detail"] == "Not authenticated"

def test_unauthenticate_get_save_item(unauthenticated_client):

    response = unauthenticated_client.get("/item/v1")

    assert response.status_code == 401
    response_object = response.json()

    assert response_object["detail"] == "Not authenticated"

def test_unauthenticate_get_item_by_sku(unauthenticated_client):
    response = unauthenticated_client.get("/item/v1/101")
    assert response.status_code == 401

def test_unauthenticate_create_item(unauthenticated_client):
    payload = {
        "sku":101,
        "name":"test",
        "initial_stock":20
    }

    response = unauthenticated_client.post("/admin/v1/item", json=payload)
    assert response.status_code == 401

def test_unauthenticated_update_item(unauthenticated_client):
    response = unauthenticated_client.patch("/admin/v1/item/101")

    assert response.status_code == 401

def test_unauthenticated_delete_item(unauthenticated_client):
    response = unauthenticated_client.delete("/admin/v1/item/101")

    assert response.status_code == 401
# ====END===


# Admin test
def test_create_item(admin_client):
    item_data = {
        "sku": 101,
        "name": "laptop",
        "initial_stock": 20
    }
    
    response = admin_client.post("/admin/v1/item", json=item_data)

    assert response.status_code == 201

    item = response.json()

    assert item["sku"] == 101
    assert item["name"] == "laptop"
    assert item["current_stock"] == 20

def test_existing_create_item(admin_client, db_session):
    create_test_item(db_session)

    payload = {
        "sku":101,
        "name":"test",
        "initial_stock":20
    }

    response = admin_client.post("/admin/v1/item", json=payload)

    assert response.status_code == 409

def test_update_item(db_session, admin_client):
    create_test_item(db_session)
    
    payload = {
        "name":"updated",
        "current_stock":20
    }

    response = admin_client.patch("/admin/v1/item/101", json=payload)

    assert response.status_code == 200
    assert response.json()["sku"] == 101
    assert response.json()["name"] == "updated"
    assert response.json()["current_stock"] == 20

def test_update_non_existent_item(admin_client):
    payload = {
            "name":"updated",
            "current_stock":20
        }
    
    response = admin_client.patch("/admin/v1/item/101", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "ITEM_NOT_FOUND"

def test_delete_item(admin_client, db_session):
    create_test_item(db_session)

    response = admin_client.delete("/admin/v1/item/101")

    assert response.status_code == 204

def test_delete_nonexistent_item(admin_client):
    response = admin_client.delete("/admin/v1/item/101")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "ITEM_NOT_FOUND"