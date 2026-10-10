import uuid
from app.core.database import Base
from datetime import datetime
from sqlalchemy import TIMESTAMP, UUID, String, Boolean, func
from sqlalchemy.orm import mapped_column, Mapped, relationship

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="owner")

from app.models.transactions import Transaction