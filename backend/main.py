import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.security import rate_limit
from database.database import init_pool

from api.auth import router as auth_router
# from api.public import router as public_router
from api.private import router as private_router
from ws.trade import router as trade_router, binance_price_relay

from config import FRONTEND_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    asyncio.create_task(binance_price_relay("btcusdt"))
    yield

app = FastAPI(title="Quasar Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(rate_limit)

app.include_router(auth_router, prefix="/auth")
# app.include_router(public_router, prefix="/api/public")
app.include_router(private_router, prefix="/api")
app.include_router(trade_router, prefix="/ws")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7052, reload=True)