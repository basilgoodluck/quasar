from fastapi import APIRouter, Depends
from middleware.auth import require_auth
from services.trade import get_all_trades
from services.paper import get_paper_status
from services.symbols import get_all_symbols, set_symbol_active
from services.logs import get_agent_logs, get_collector_logs, get_retrain_log

router = APIRouter()


@router.get("/paper/status")
def paper_status(user=Depends(require_auth)):
    try:
        return get_paper_status()
    except Exception as e:
        return {"error": str(e)}


@router.get("/trades")
def all_trades(
    status: str = None,
    pair: str = None,
    limit: int = 100,
    user=Depends(require_auth),
):
    return {"trades": get_all_trades(status=status, pair=pair, limit=limit)}


@router.get("/retrain/log")
def retrain_log(user=Depends(require_auth)):
    return {"log": get_retrain_log()}


@router.get("/symbols")
def symbols(user=Depends(require_auth)):
    return {"symbols": get_all_symbols()}


@router.put("/symbols/{symbol}")
def update_symbol(symbol: str, active: bool, user=Depends(require_auth)):
    set_symbol_active(symbol, active)
    return {"ok": True}


@router.get("/logs/agent")
def agent_logs(lines: int = 100, user=Depends(require_auth)):
    try:
        return {"logs": get_agent_logs(lines)}
    except Exception as e:
        return {"error": str(e)}


@router.get("/logs/collector")
def collector_logs(lines: int = 100, user=Depends(require_auth)):
    try:
        return {"logs": get_collector_logs(lines)}
    except Exception as e:
        return {"error": str(e)}
