from pydantic import BaseModel, ConfigDict, EmailStr

class GenerateIn(BaseModel):
    email: EmailStr

