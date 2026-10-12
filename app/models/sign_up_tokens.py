import uuid
from datetime import datetime
from sqlalchemy import UUID, Text, TIMESTAMP, func, String
from sqlalchemy.orm import mapped_column, Mapped
from app.core.database import Base

class SignUpToken(Base):
    __tablename__ = "sign_up_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    token: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    exp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    