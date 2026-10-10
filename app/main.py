from fastapi import FastAPI
from app.models.items import Item
from app.models.transactions import Transaction
from app.models.users import User
from app.models.sign_up_tokens import SignUpToken
from app.routers.admin import router as admin_routes
from app.routers.users import router as user_routes

app = FastAPI()

app.include_router(admin_routes)
app.include_router(user_routes)

@app.get("/")
def root():
    return {"status": "running"}