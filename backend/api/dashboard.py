# api/dashboard.py
from fastapi import APIRouter
from database.database import get_db
from services.trade import get_all_trades

router = APIRouter()


@router.get("/dashboard/trades")
async def dashboard_trades(status: str = None, pair: str = None, limit: int = 100):
    db = await get_db()
    return await get_all_trades(status=status, pair=pair, limit=limit, db=db)