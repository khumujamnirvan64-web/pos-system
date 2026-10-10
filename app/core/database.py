from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine, engine
from app.core.config import settings

engine = create_engine(
    settings.DB_URL,
    pool_size=4,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass