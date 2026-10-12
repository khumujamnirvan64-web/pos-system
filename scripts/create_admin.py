import logging
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.users import User
from app.utils.password_hash import hash_password
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_first_admin(db: Session) -> None:
  normalized_email = settings.FIRST_USER_EMAIL.lower().strip()
  logger.info(f"Checking for admin user: {normalized_email}")

  try:
    stmt = select(User).where(User.email == normalized_email)
    existing = db.execute(stmt).scalar_one_or_none()

    if existing:
      logger.info(f"Admin already exists: {normalized_email}")
      return

    hashed_password = hash_password(settings.FIRST_USER_PASSWORD)
    admin = User(
        email=normalized_email,
        password=hashed_password,
        name=settings.FIRST_USER_NAME.strip(),
        is_admin=True,
    )

    db.add(admin)
    db.commit()
    logger.info("Admin created successfully.")

  except Exception as e:
    db.rollback()
    logger.error(f"Failed to create admin user: {e}", exc_info=True)
    raise e


# --- Standalone Execution Entrypoint ---
def run_init_admin():
  db = SessionLocal()
  try:
    create_first_admin(db)
  finally:
    db.close()


if __name__ == "__main__":
  run_init_admin()