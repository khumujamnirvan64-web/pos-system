import uuid
from app.schema.transactions import TransactionIn, TransactionType, TransactionOut
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.transactions import Transaction
from app.models.items import Item
from fastapi import HTTPException, status
from collections.abc import Sequence
from app.models.users import User

class TransactionsNotFound(Exception):
    pass
class ItemNotFound(Exception):
    pass
class InsufficientStockInput(Exception):
    pass

def handle_create_transaction(transaction_batch: TransactionIn, db: Session, current_user: User) -> list[Transaction]:
    sorted_items = sorted(transaction_batch.items, key=lambda x: x.sku)
    created_transactions: list[Transaction] = []

    for movement in sorted_items:
        stmt = (
            select(Item)
            .where(Item.sku == movement.sku)
            .with_for_update()
        )

        item = db.execute(stmt).scalar_one_or_none()

        if not item:
            raise ItemNotFound(f"Item with SKU {movement.sku} not found.")

        delta = (
            -movement.quantity
            if movement.transaction_type == TransactionType.sales
            else movement.quantity
        )

        if item.current_stock + delta < 0:
            raise InsufficientStockInput(f"Insufficient stock for SKU {movement.sku}.")

        item.current_stock += delta

        transaction = Transaction(
            sku=movement.sku,
            user_id=current_user.id,
            transaction_type = movement.transaction_type,
            movement=delta
        )

        db.add(transaction)
        db.flush()
        db.refresh(transaction)

        created_transactions.append(transaction)
    db.commit()
    return created_transactions

# Get all transaction of the user
def handle_get_my_transaction(user_id: uuid.UUID, db: Session) -> Sequence[Transaction]:
    stmt = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        )
    )

    transactions_list = db.execute(stmt).scalars().all()

    if not transactions_list:
        return []

    return transactions_list

def handle_get_transaction(user_id: uuid.UUID, transaction_id: uuid.UUID, db: Session) -> Transaction:
    stmt = (
        select(Transaction)
        .where(
                Transaction.user_id == user_id,
                Transaction.id == transaction_id,
                Transaction.is_deleted == False
            )
        .order_by(Transaction.created_at.desc())
    )

    transaction = db.execute(stmt).scalar_one_or_none()

    if not transaction:
        raise TransactionsNotFound

    return transaction

# Admin Functions:
def handle_get_all_transactions(db: Session, limit: int, offset: int) -> Sequence[Transaction]:
    stmt = (
        select(Transaction)
        .where(Transaction.is_deleted == False)
        .limit(limit)
        .offset(offset)
        .order_by(Transaction.created_at.desc())
    )
    transactions = db.execute(stmt).scalars().all()
    
    if not transactions:
        return []

    return transactions

def handle_delete_transaction(transaction_id: uuid.UUID, db: Session) -> None:
    stmt = (
        select(Transaction)
        .where(
            Transaction.id == transaction_id,
            Transaction.is_deleted == False
        )
    )

    transaction = db.execute(stmt).scalar_one_or_none()

    if not transaction:
            raise TransactionsNotFound

    transaction.is_deleted = True
    db.commit()