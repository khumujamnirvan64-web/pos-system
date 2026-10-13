from datetime import datetime
from app.core.database import Base
from sqlalchemy import Text, TIMESTAMP, Integer ,func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    
    idempotency_key: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    response_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())