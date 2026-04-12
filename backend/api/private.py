from fastapi import APIRouter, Depends
from middleware.auth import require_auth
from services.trade import get_all_trades
from middleware.security import require_admin

router = APIRouter()


@router.get("/trades")
def all_trades(
    status: str = None,
    pair: str = None,
    limit: int = 100,
    user=Depends(require_auth),
):
    return {"trades": get_all_trades(status=status, pair=pair, limit=limit)}

# readonly route
@router.get("/status")
async def status(user=Depends(require_auth)):
    ...

# admin only route
@router.post("/config")
async def update_config(user=Depends(require_admin)):
    ...