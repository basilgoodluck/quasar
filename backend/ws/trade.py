# ws/trade.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import websockets
import httpx
from database.database import pool
from services.trade import get_all_trades, format_trade

router = APIRouter()


# ── Connection Manager ────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# ── GET /api/binance/klines ───────────────────────────────────────────────────

@router.get("/binance/klines")
async def binance_klines(symbol: str, interval: str = "15m", limit: int = 200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


# ── WS /ws/trades ─────────────────────────────────────────────────────────────

@router.websocket("/trades")
async def trade_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        async with pool.acquire() as db:
            initial = await get_all_trades(limit=50, db=db)
        await websocket.send_json({"type": "initial", "data": initial})
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# ── WS /ws/binance-stream ─────────────────────────────────────────────────────

@router.websocket("/binance-stream")
async def binance_stream(websocket: WebSocket, symbol: str = "btcusdt", interval: str = "15m"):
    await websocket.accept()
    binance_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"
    try:
        async with websockets.connect(binance_url) as ws:
            async for raw in ws:
                await websocket.send_text(raw)
    except Exception:
        pass
    finally:
        await websocket.close()


# ── Broadcast helpers ─────────────────────────────────────────────────────────

async def broadcast_new_trade(trade_row: dict):
    await manager.broadcast({"type": "new_trade", "data": format_trade(trade_row)})


async def broadcast_event(event_data: dict):
    await manager.broadcast({"type": "event", "data": event_data})