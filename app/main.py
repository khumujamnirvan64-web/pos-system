from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.items import Item
from app.models.transactions import Transaction
from app.models.users import User
from app.models.sign_up_tokens import SignUpToken
from app.routers.admin import router as admin_routes
from app.routers.users import router as user_routes
from app.routers.items import router as item_routes
from app.routers.transactions import router as transactions_route
from app.routers.dashboard import router as dashboard_routers

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",  # e.g., React / Vite dev server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_routes)
app.include_router(dashboard_routers)
app.include_router(user_routes)
app.include_router(item_routes)
app.include_router(transactions_route)

@app.get("/")
def root():
    return {"status": "running"}