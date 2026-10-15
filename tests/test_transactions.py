from tests.conftest import non_admin_client, unauthenticated_client, admin_client, missing_user_client, db_session, create_test_user
from app.models.transactions import Transaction
from app.models.items import Item
from app.models.idempotency_keys import IdempotencyRecord
from app.models.users import User
from uuid import uuid4
def create_test_item(db_session):
    item = Item(
        sku=101,
        name="test product",
        current_stock=100
    )
    db_session.add(item)
    db_session.commit()

    db_session.refresh(item)

    return item

# Unauthenticated Tests
def test_unauthenticated_create_transaction(unauthenticated_client):
    response = unauthenticated_client.post("/transaction/v1")
    assert response.status_code == 401

def test_unauthenticated_get_my_transaction(unauthenticated_client):
    response = unauthenticated_client.get("/transaction/v1")
    assert response.status_code == 401

def test_unauthenticated_get_transaction_by_id(unauthenticated_client):
    transaction_id = uuid4()
    response = unauthenticated_client.get(f"/transaction/v1/{transaction_id}")
    assert response.status_code == 401

def test_unauthenticated_get_all_transaction(unauthenticated_client):
    response = unauthenticated_client.get("/admin/v1/transaction")
    assert response.status_code == 401

def test_unauthenticated_delete_transaction(unauthenticated_client):
    transaction_id = uuid4()
    response = unauthenticated_client.delete(f"admin/v1/transaction/{transaction_id}")
    assert response.status_code == 401

# Authenticated Tests
def test_authenticated_create_transaction_stock_out(non_admin_client, db_session):
    key = uuid4()
    create_test_item(db_session)
    payload = {
                "items": [
                    {
                    "sku": 101,
                    "quantity": 50,
                    "transaction_type": "stock out"
                    }
                ]
            }

    response = non_admin_client.post(
        "/transaction/v1",
        json=payload,
        headers={"X-Idempotency-Key": str(key)}
    )

    assert response.status_code == 201
    assert len(response.json()) == 1

def test_authenticated_create_transaction_with_existing_key(
    non_admin_client, db_session
):
    key = str(uuid4())
    item = create_test_item(db_session)
    initial_stock = item.current_stock

    cached_response = [
        {
            "id": str(uuid4()),
            "sku": 101,
            "movement": -50,
            "transaction_type": "stock out",
            "created_at": "2026-01-01T12:00:00+00:00",
        }
    ]

    existing_key = IdempotencyRecord(
        idempotency_key=key,
        response_status_code=201,
        response_body=cached_response,
    )
    db_session.add(existing_key)
    db_session.commit()

    payload = {
        "items": [
            {
                "sku": 101,
                "quantity": 50,
                "transaction_type": "stock out",
            }
        ]
    }

    response = non_admin_client.post(
        "/transaction/v1",
        json=payload,
        headers={"X-Idempotency-Key": key},
    )

    assert response.status_code == 201
    assert response.json() == cached_response

    db_session.refresh(item)
    assert item.current_stock == initial_stock

    transactions = db_session.query(Transaction).filter(
        Transaction.sku == 101
    ).all()
    assert len(transactions) == 0

def test_authenticated_create_transaction_with_non_existent_item(non_admin_client):
    payload = {
                "items": [
                    {
                    "sku": 101,
                    "quantity": 50,
                    "transaction_type": "stock out"
                    }
                ]
            }
    response = non_admin_client.post("/transaction/v1", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "ITEM_NOT_FOUND"

def test_authenticated_create_transaction_of_insufficient_stock(non_admin_client, db_session):
    create_test_item(db_session)
    payload = {
                "items": [
                    {
                    "sku": 101,
                    "quantity": 101,
                    "transaction_type": "stock out"
                    }
                ]
            }

    response = non_admin_client.post("/transaction/v1", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "INSUFFICIENT_STOCK_ERROR"

def test_authenticated_get_my_transactions(non_admin_client, db_session, create_test_user):
    user = create_test_user
    
    create_test_item(db_session)

    transaction = Transaction(
        sku=101,
        user_id=user.id,
        transaction_type="stock out",
        movement=-50,
        is_deleted=False
    )

    db_session.add(transaction)
    db_session.commit()

    response = non_admin_client.get("/transaction/v1")

    assert response.status_code == 200
    assert response.json()[0]["sku"] == 101
    assert response.json()[0]["transaction_type"] == "stock out"
    assert response.json()[0]["movement"] == -50


def test_authenticated_get_empty_transaction(non_admin_client):
    response = non_admin_client.get("/transaction/v1")

    assert response.status_code == 200
    assert response.json() == []

def test_authenticated_get_transaction_by_id(non_admin_client, db_session, create_test_user):
    user = create_test_user
    transaction_id = uuid4()
    create_test_item(db_session)

    transaction = Transaction(
        id=transaction_id,
        sku=101,
        user_id=user.id,
        transaction_type="stock out",
        movement=-50,
        is_deleted=False
    )

    db_session.add(transaction)
    db_session.commit()

    response = non_admin_client.get(f"/transaction/v1/{transaction_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(transaction_id)
    assert response.json()["sku"] == 101
    assert response.json()["transaction_type"] == "stock out"
    assert response.json()["movement"] == -50

def test_authenticated_get_transaction_by_id_error(non_admin_client):
    transaction_id = uuid4()

    response = non_admin_client.get(f"/transaction/v1/{transaction_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "TRANSACTION_NOT_FOUND"

def test_admin_enpoint_with_normal_user(non_admin_client):
    response = non_admin_client.get("/admin/v1/transaction")
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "NOT_ADMIN"

    transaction_id = uuid4()
    response_two = non_admin_client.delete(f"/admin/v1/transaction/{transaction_id}")
    assert response_two.status_code == 403
    assert response_two.json()["detail"]["error"] == "NOT_ADMIN"


# Admin Tests
def test_admin_get_all_transaction(admin_client, db_session, create_admin_test_user):
    user = create_admin_test_user
    transaction_id = uuid4()
    create_test_item(db_session)
    
    transaction = Transaction(
        id=transaction_id,
        sku=101,
        user_id=user.id,
        transaction_type="stock out",
        movement=-50,
        is_deleted=False
    )

    db_session.add(transaction)
    db_session.commit()

    response = admin_client.get("/admin/v1/transaction")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == 101
    assert response.json()[0]["transaction_type"] == "stock out"
    assert response.json()[0]["movement"] == -50

def test_admin_get_all_transaction_error(admin_client):
    response = admin_client.get("/admin/v1/transaction")
    assert response.status_code == 200
    assert response.json() == []

def test_admin_delete_transaction(admin_client, db_session, create_admin_test_user):
    user = create_admin_test_user
    transaction_id = uuid4()
    create_test_item(db_session)
    
    transaction = Transaction(
        id=transaction_id,
        sku=101,
        user_id=user.id,
        transaction_type="stock out",
        movement=-50,
        is_deleted=False
    )

    db_session.add(transaction)
    db_session.commit()

    response = admin_client.delete(f"/admin/v1/transaction/{transaction_id}")

    assert response.status_code == 204

def test_admin_delete_transaction_error(admin_client):
    transaction_id = uuid4()
    
    response = admin_client.delete(f"/admin/v1/transaction/{transaction_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "TRANSACTION_NOT_FOUND"