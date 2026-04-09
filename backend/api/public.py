# from fastapi import APIRouter
# from services.trade import get_recent_trades, get_trade_replay, get_pnl_curve, get_checkpoints
# from services.reputation import get_reputation
# from services.regime import get_regime_all
# from config import AGENT_WALLET_ADDRESS, AGENT_ID, AGENT_REGISTRY_ADDRESS, CHAIN_ID

# router = APIRouter()


# @router.get("/reputation")
# def reputation():
#     current, history = get_reputation()
#     return {"current": current, "history": history}


# @router.get("/trades")
# def trades():
#     return {"trades": get_recent_trades()}


# @router.get("/trades/{trade_id}/replay")
# def trade_replay(trade_id: int):
#     trade, candles = get_trade_replay(trade_id)
#     if not trade:
#         return {"error": "not found"}
#     return {"trade": trade, "candles": candles}


# @router.get("/pnl")
# def pnl():
#     curve, total = get_pnl_curve()
#     return {"curve": curve, "total": total}


# @router.get("/checkpoints")
# def checkpoints():
#     return {"checkpoints": get_checkpoints()}


# @router.get("/regime")
# def regime():
#     return {"regime": get_regime_all()}


# @router.get("/agent")
# def agent():
#     return {
#         "name":         "ARC",
#         "version":      "1.0.0",
#         "wallet":       AGENT_WALLET_ADDRESS,
#         "agent_id":     AGENT_ID,
#         "chain":        "Sepolia",
#         "chain_id":     CHAIN_ID,
#         "registry":     AGENT_REGISTRY_ADDRESS,
#         "capabilities": ["LONG", "SHORT", "SKIP", "RISK_MANAGED", "ON_CHAIN_VERIFIED"],
#     }
