import uuid
from datetime import datetime
from app.core.database import Base
from sqlalchemy import Text, String, Boolean, TIMESTAMP, UUID, ForeignKey, func
from sqlalchemy.orm import mapped_column, Mapped

class PasswordToken(Base):
    __tablename__ = "password_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), ForeignKey("users.email", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    exp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())