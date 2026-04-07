import os
import time
import asyncio
import aiohttp
import json
import websockets
from database.connection import get_connection
from logger import get_logger

logger = get_logger(__name__)

BINANCE_BASE    = "https://fapi.binance.com"
BINANCE_WS_BASE = "wss://fstream.binance.com/ws"
LOOP_SLEEP      = int(os.getenv("COLLECT_LOOP_SLEEP", "60"))
BACKFILL_DAYS   = 1
KLINE_LIMIT     = 1500
AGG_TRADE_BATCH = int(os.getenv("AGG_TRADE_BATCH", "100"))


def get_active_symbols():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT symbol, intervals FROM symbols WHERE active = TRUE")
            return cur.fetchall()


async def _get(session, url, params=None):
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as res:
            res.raise_for_status()
            return await res.json()
    except Exception as e:
        logger.error(f"GET {url} {params}: {e}")
        return None


def _save_ohlcv_cvd(symbol, interval, data):
    ohlcv_rows = [
        (symbol, interval, int(c[0]), float(c[1]), float(c[2]), float(c[3]),
         float(c[4]), float(c[5]), float(c[9]), int(c[6]))
        for c in data
    ]
    cvd_rows = []
    cumulative = 0.0
    for c in data:
        buy_vol = float(c[9])
        delta = buy_vol - (float(c[5]) - buy_vol)
        cumulative += delta
        cvd_rows.append((symbol, interval, int(c[0]), round(delta, 4), round(cumulative, 4)))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO market_data (symbol, interval, open_time, open, high, low, close, volume, taker_buy_volume, close_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, interval, open_time) DO NOTHING
            """, ohlcv_rows)
            cur.executemany("""
                INSERT INTO cvd_history (symbol, interval, open_time, delta, cvd)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, interval, open_time) DO NOTHING
            """, cvd_rows)
            conn.commit()


def _save_liquidation(symbol, side, quantity, price, trade_time):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO liquidations (symbol, side, quantity, price, trade_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol, side, quantity, price, trade_time))
            conn.commit()


def _save_agg_trades(rows):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO agg_trades (symbol, trade_id, price, quantity, is_buyer_mm, trade_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, trade_id) DO NOTHING
            """, rows)
            conn.commit()


async def _backfill_ohlcv(session, symbol, interval):
    import time as t
    end_time   = int(t.time() * 1000)
    start_time = end_time - BACKFILL_DAYS * 86400 * 1000

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MIN(open_time) FROM market_data WHERE symbol = %s AND interval = %s",
                (symbol, interval)
            )
            row = cur.fetchone()
            if row and row[0]:
                end_time = int(row[0]) - 1

    total = 0
    while True:
        data = await _get(session, f"{BINANCE_BASE}/fapi/v1/klines", {
            "symbol": symbol, "interval": interval,
            "startTime": start_time, "endTime": end_time,
            "limit": KLINE_LIMIT
        })
        if not data:
            break
        _save_ohlcv_cvd(symbol, interval, data)
        total += len(data)
        logger.info(f"[{symbol}/{interval}] backfill: {total} rows")
        if len(data) < KLINE_LIMIT:
            break
        end_time = int(data[0][0]) - 1
        await asyncio.sleep(0.2)


async def _backfill_funding(session, symbol):
    import time as t
    end_time   = int(t.time() * 1000)
    start_time = end_time - BACKFILL_DAYS * 86400 * 1000
    total      = 0
    while True:
        data = await _get(session, f"{BINANCE_BASE}/fapi/v1/fundingRate", {
            "symbol": symbol, "startTime": start_time, "endTime": end_time, "limit": 1000
        })
        if not data:
            break
        rows = [
            (symbol, int(f["fundingTime"]), float(f["fundingRate"]),
             float(f.get("markPrice", 0) or 0))
            for f in data
        ]
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO funding_rates (symbol, funding_time, funding_rate, mark_price)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (symbol, funding_time) DO NOTHING
                """, rows)
                conn.commit()
        total += len(rows)
        if len(data) < 1000:
            break
        end_time = int(data[0]["fundingTime"]) - 1
        await asyncio.sleep(0.2)
    logger.info(f"[{symbol}] backfill funding: {total} rows")


async def _backfill_oi(session, symbol, period):
    import time as t
    end_time   = int(t.time() * 1000)
    start_time = end_time - BACKFILL_DAYS * 86400 * 1000
    total      = 0
    while True:
        data = await _get(session, f"{BINANCE_BASE}/futures/data/openInterestHist", {
            "symbol": symbol, "period": period,
            "startTime": start_time, "endTime": end_time, "limit": 500
        })
        if not data:
            break
        rows = [
            (symbol, period, int(o["timestamp"]), float(o["sumOpenInterest"]),
             float(o.get("sumOpenInterestValue", 0) or 0))
            for o in data
        ]
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO oi_history (symbol, period, timestamp, open_interest, open_interest_value)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, period, timestamp) DO NOTHING
                """, rows)
                conn.commit()
        total += len(rows)
        if len(data) < 500:
            break
        end_time = int(data[0]["timestamp"]) - 1
        await asyncio.sleep(0.2)
    logger.info(f"[{symbol}] backfill oi/{period}: {total} rows")


async def _live_funding(session, symbol):
    data = await _get(session, f"{BINANCE_BASE}/fapi/v1/fundingRate", {
        "symbol": symbol, "limit": 5
    })
    if not data:
        return
    rows = [
        (symbol, int(f["fundingTime"]), float(f["fundingRate"]),
         float(f.get("markPrice", 0) or 0))
        for f in data
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO funding_rates (symbol, funding_time, funding_rate, mark_price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol, funding_time) DO NOTHING
            """, rows)
            conn.commit()


async def _live_oi(session, symbol, period):
    data = await _get(session, f"{BINANCE_BASE}/futures/data/openInterestHist", {
        "symbol": symbol, "period": period, "limit": 5
    })
    if not data:
        return
    rows = [
        (symbol, period, int(o["timestamp"]), float(o["sumOpenInterest"]),
         float(o.get("sumOpenInterestValue", 0) or 0))
        for o in data
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO oi_history (symbol, period, timestamp, open_interest, open_interest_value)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, period, timestamp) DO NOTHING
            """, rows)
            conn.commit()


async def _ws_klines(symbol, interval):
    stream = f"{symbol.lower()}@kline_{interval}"
    url    = f"{BINANCE_WS_BASE}/{stream}"
    logger.info(f"[ws] klines connecting {stream}")
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                async for raw in ws:
                    msg = json.loads(raw)
                    k   = msg.get("k", {})
                    if not k.get("x"):
                        continue
                    candle = [
                        k["t"], k["o"], k["h"], k["l"], k["c"],
                        k["v"], k["T"], None, None, k["V"]
                    ]
                    _save_ohlcv_cvd(symbol, interval, [candle])
        except Exception as e:
            logger.error(f"[ws] klines {stream} error: {e} — reconnecting in 5s")
            await asyncio.sleep(5)


async def _ws_liquidations(symbol):
    stream = f"{symbol.lower()}@forceOrder"
    url    = f"{BINANCE_WS_BASE}/{stream}"
    logger.info(f"[ws] liquidations connecting {stream}")
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                async for raw in ws:
                    msg   = json.loads(raw)
                    order = msg.get("o", {})
                    _save_liquidation(
                        symbol,
                        order.get("S"),
                        float(order.get("q", 0)),
                        float(order.get("p", 0)),
                        int(order.get("T", 0)),
                    )
        except Exception as e:
            logger.error(f"[ws] liquidations {stream} error: {e} — reconnecting in 5s")
            await asyncio.sleep(5)


async def _ws_agg_trades(symbol):
    stream = f"{symbol.lower()}@aggTrade"
    url    = f"{BINANCE_WS_BASE}/{stream}"
    logger.info(f"[ws] aggTrades connecting {stream}")
    buffer = []
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                async for raw in ws:
                    msg = json.loads(raw)
                    buffer.append((
                        symbol,
                        int(msg["a"]),    # trade_id
                        float(msg["p"]),  # price
                        float(msg["q"]),  # quantity
                        bool(msg["m"]),   # is_buyer_mm: True = sell trade, False = buy trade
                        int(msg["T"]),    # trade_time
                    ))
                    if len(buffer) >= AGG_TRADE_BATCH:
                        _save_agg_trades(buffer)
                        buffer = []
        except Exception as e:
            logger.error(f"[ws] aggTrades {stream} error: {e} — reconnecting in 5s")
            if buffer:
                try:
                    _save_agg_trades(buffer)
                except Exception:
                    pass
                buffer = []
            await asyncio.sleep(5)


async def _rest_loop(symbols_intervals):
    logger.info("REST live loop running (funding + OI)")
    while True:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol, intervals in symbols_intervals:
                for interval in intervals:
                    tasks.append(_live_oi(session, symbol, interval))
                tasks.append(_live_funding(session, symbol))
            await asyncio.gather(*tasks)
        await asyncio.sleep(max(0, LOOP_SLEEP - (time.time() - start)))


async def backfill(symbols_intervals):
    logger.info(f"Backfill starting — {BACKFILL_DAYS} days")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for symbol, intervals in symbols_intervals:
            for interval in intervals:
                tasks.append(_backfill_ohlcv(session, symbol, interval))
                tasks.append(_backfill_oi(session, symbol, interval))
            tasks.append(_backfill_funding(session, symbol))
        await asyncio.gather(*tasks)
    logger.info("Backfill complete")


async def run():
    symbols_intervals = get_active_symbols()
    if not symbols_intervals:
        logger.error("No active symbols in DB")
        return

    logger.info(f"Symbols: {[s for s, _ in symbols_intervals]}")
    await backfill(symbols_intervals)

    tasks = [_rest_loop(symbols_intervals)]
    for symbol, intervals in symbols_intervals:
        for interval in intervals:
            tasks.append(_ws_klines(symbol, interval))
        tasks.append(_ws_liquidations(symbol))
        tasks.append(_ws_agg_trades(symbol))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run())