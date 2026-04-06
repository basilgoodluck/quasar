from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import websockets
import json
import httpx
from services.trade import get_recent_trades, get_all_trades, get_pnl_curve

router = APIRouter(prefix="/trade", tags=["trade"])


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


# Binance kline proxy (HTTP)
@router.get("/binance-klines")
async def binance_klines(symbol: str, interval: str = "15m", limit: int = 200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


# Binance kline stream proxy (WebSocket)
@router.websocket("/ws/binance-stream")
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


# Existing price relay (unchanged)
async def binance_price_relay(symbol: str = "btcusdt"):
    url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
    while True:
        try:
            async with websockets.connect(url) as ws:
                async for raw in ws:
                    msg = json.loads(raw)
                    price = float(msg["p"])
                    await manager.broadcast({"type": "price", "symbol": symbol.upper(), "price": price})
        except Exception:
            await asyncio.sleep(3)


@router.get("/recent")
async def recent_trades(limit: int = 50):
    return get_recent_trades(limit)


@router.get("/all")
async def all_trades(status: str = None, pair: str = None, limit: int = 100):
    return get_all_trades(status, pair, limit)


@router.get("/pnl-curve")
async def pnl_curve():
    curve, total = get_pnl_curve()
    return {"curve": curve, "total_pnl": total}


@router.websocket("/ws")
async def trade_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        initial = get_recent_trades(limit=30)
        await websocket.send_json({"type": "initial", "data": initial})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def broadcast_new_trade(trade_data: dict):
    await manager.broadcast({"type": "new_trade", "data": trade_data})