from pydantic import BaseModel, ConfigDict, Field, field_validator
import uuid
from datetime import datetime
from typing import Optional

class ItemIn(BaseModel):
    sku: int = Field(ge=100)
    name: str
    initial_stock: int = Field(ge=0)

class ItemOut(BaseModel):
    id: uuid.UUID
    sku: int = Field(ge=100)
    name: str
    current_stock: int = Field(ge=0)
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class ItemUpdate(BaseModel):
    sku: Optional[int] = None
    name: Optional[str] = None
    updating_stock: Optional[int] = None

    @field_validator("name", mode="before")
    @classmethod
    def lowercase_if_present(cls, v:Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return v.lower().strip()
        return v