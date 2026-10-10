import uuid
from app.core.database import Base
from datetime import datetime
from sqlalchemy import UUID, TIMESTAMP, String, Integer, CheckConstraint, func
from sqlalchemy.orm import mapped_column, Mapped

class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    sku: Mapped[int] = mapped_column(Integer ,index=True, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="check_current_stock_valid"),
    )
    