import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, Literal

class UserIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str

class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"

    model_config = ConfigDict(
            from_attributes=True
        )

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

    @field_validator("email", "name", mode="before")
    @classmethod
    def lowercase_if_present(cls, v:Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return v.lower().strip()
        return v


class ToggleAdminUpdate(BaseModel):
    toggle: Literal[True, False]