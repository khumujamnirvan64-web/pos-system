from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.users import User

def count_current_admin(db: Session):
    stmt = (
        select(
            func.count(User.id)
            .filter(User.is_admin == True)
        )
    )

    current_admins = db.execute(stmt).scalar() or 0

    if current_admins <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete the last remaining administrator account."
        )