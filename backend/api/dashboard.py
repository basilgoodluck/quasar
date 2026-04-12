# api/dashboard.py
from fastapi import APIRouter, Depends
from database.database import get_db
from services.trade import get_all_trades, get_dashboard_overview, get_symbols

router = APIRouter()


@router.get("/dashboard/overview")
async def dashboard_overview(db=Depends(get_db)):
    return await get_dashboard_overview(db=db)


@router.get("/dashboard/trades")
async def dashboard_trades(status: str = None, pair: str = None, limit: int = 100, db=Depends(get_db)):
    return await get_all_trades(status=status, pair=pair, limit=limit, db=db)


@router.get("/trade/symbols")
async def trade_symbols(db=Depends(get_db)):
    return await get_symbols(db=db)