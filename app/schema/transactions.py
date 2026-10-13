import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.schema.users import UserOut
from enum import Enum
from datetime import datetime

class TransactionType(str, Enum):
    sales = "stock out"
    restock = "stock in"

class StockMovementItem(BaseModel):
    sku: int
    quantity: int = Field(..., gt=0, description="Always postive amount")
    transaction_type: TransactionType

class TransactionIn(BaseModel):
    items: list[StockMovementItem] = Field(..., min_length=1)

class TransactionOut(BaseModel):
    id: uuid.UUID
    sku: int
    movement: int
    transaction_type: TransactionType
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class TransactionAdminOut(BaseModel):
    id: uuid.UUID
    sku: int
    movement: int
    transaction_type: TransactionType
    created_at: datetime
    owner: UserOut

    model_config = ConfigDict(
        from_attributes=True
    )