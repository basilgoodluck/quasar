# main.py
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from middleware.security import rate_limit
from database.database import init_pool
from api.auth import router as auth_router
from api.dashboard import router as dashboard_router
from ws.trade import router as trade_router
from config import FRONTEND_URL, SECRET_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield


app = FastAPI(title="Quasar Agent API", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit)

# /auth/*
app.include_router(auth_router, prefix="/auth")

# /api/dashboard/trades
# /api/binance/klines
app.include_router(dashboard_router, prefix="/api")
app.include_router(trade_router, prefix="/api")

# /ws/trades
# /ws/binance-stream
app.include_router(trade_router, prefix="/ws")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7052, reload=True)