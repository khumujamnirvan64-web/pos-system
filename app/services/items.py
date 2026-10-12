from sqlalchemy import select
from sqlalchemy.orm import Session
from app.schema.items import ItemIn, ItemUpdate
from app.models.items import Item
from collections.abc import Sequence

class ItemAlreadyExists(Exception):
    pass
class ItemNotFound(Exception):
    pass

def handle_create_item(payload: ItemIn, db: Session) -> Item:
    normalized_name = payload.name.lower().strip()

    stmt = (
        select(Item)
        .where(
            Item.name == payload.name,
            Item.sku == payload.sku
        )
    )

    existing = db.execute(stmt).scalar_one_or_none()

    if existing:
        raise ItemAlreadyExists

    new_item = Item(
        sku=payload.sku,
        name=normalized_name,
        current_stock=payload.initial_stock,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item

def handle_get_items(db: Session) -> Sequence[Item]:
    stmt = select(Item).order_by(Item.sku)

    items = db.execute(stmt).scalars().all()

    if not items:
        raise ItemNotFound

    return items

def handle_one_item(sku: int, db: Session) -> Item:
    stmt = select(Item).where(Item.sku == sku)

    item = db.execute(stmt).scalar_one_or_none()

    if not item:
        raise ItemNotFound

    return item

def handle_update_item(item_sku: int, payload: ItemUpdate, db: Session) -> Item:
    stmt =  select(Item).where(Item.sku == item_sku).with_for_update()
    
    item = db.execute(stmt).scalar_one_or_none()

    if item is None:
        raise ItemNotFound

    if payload.name is not None:
        item.name = payload.name
    if payload.current_stock is not None:
        item.current_stock = payload.current_stock

    db.commit()
    db.refresh(item)
    return item

def handle_delete_item(item_sku: int, db: Session) -> None:
    stmt = select(Item).where(Item.sku == item_sku)

    deleting_item = db.execute(stmt).scalar_one_or_none()

    if not deleting_item:
        raise ItemNotFound

    db.delete(deleting_item)
    db.commit()