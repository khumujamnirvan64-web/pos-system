import uuid
from app.core.database import Base
from datetime import datetime
from sqlalchemy import TIMESTAMP, UUID, String, Integer, func, CheckConstraint, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    sku: Mapped[int] = mapped_column(Integer, ForeignKey("items.sku"),index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(255), nullable=False)
    movement: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("transaction_type IN ('stock in', 'stock out')", name="check_valid_transaction_type"),
    )

    owner: Mapped["User"] = relationship("User", back_populates="transactions")


from app.models.users import User