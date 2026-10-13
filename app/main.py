from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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
from app.routers.auth import router as auth_routes
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

app = FastAPI()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded {exc.detail}"}
    )


origins = [
    "http://localhost",
    "http://localhost:3000",  # e.g., React / Vite dev server
    "http://127.0.0.1:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes)
app.include_router(user_routes)
app.include_router(admin_routes)
app.include_router(dashboard_routers)
app.include_router(item_routes)
app.include_router(transactions_route)

@app.get("/")
def root():
    return {"status": "running"}