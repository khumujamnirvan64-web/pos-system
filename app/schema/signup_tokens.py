from pydantic import BaseModel, EmailStr

class GenerateIn(BaseModel):
    email: EmailStr

