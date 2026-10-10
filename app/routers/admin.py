from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_admin
from fastapi import Depends, APIRouter
from app.schema.signup_tokens import GenerateIn
from app.utils.signup_token import create_sign_up_token

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.post("/token/generate")
def generate_signup_token(
    data: GenerateIn,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    normalized_email = data.email.lower().strip()

    singup_token = create_sign_up_token(normalized_email, db)

    return {"invite_token": f"{singup_token}"}