# Admin Only Routes
from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_admin
from app.models.users import User
from app.services.dashboard import handle_get_movement_percentage

router = APIRouter(
    prefix="/dashboard/v1",
    tags=["Dashboard"]
)

@router.get("")
def get_movement_percentage(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    return handle_get_movement_percentage(db)