import os
import time
import asyncio
import aiohttp
from database.connection import get_connection
from logger import get_logger

logger = get_logger(__name__)

BINANCE_BASE  = "https://fapi.binance.com"
LOOP_SLEEP    = int(os.getenv("COLLECT_LOOP_SLEEP", "60"))
BACKFILL_DAYS = int(os.getenv("BACKFILL_DAYS", "730"))
KLINE_LIMIT   = 1500


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


async def _backfill_ohlcv(session, symbol, interval):
    import time as t
    end_time = int(t.time() * 1000)
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
    end_time = int(t.time() * 1000)
    start_time = end_time - BACKFILL_DAYS * 86400 * 1000
    total = 0
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
    end_time = int(t.time() * 1000)
    start_time = end_time - BACKFILL_DAYS * 86400 * 1000
    total = 0
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


async def _live_ohlcv(session, symbol, interval):
    data = await _get(session, f"{BINANCE_BASE}/fapi/v1/klines", {
        "symbol": symbol, "interval": interval, "limit": 5
    })
    if data:
        _save_ohlcv_cvd(symbol, interval, data)


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


async def _live_liquidations(session, symbol):
    data = await _get(session, f"{BINANCE_BASE}/fapi/v1/allForceOrders", {
        "symbol": symbol, "limit": 20
    })
    if not data:
        return
    rows = [
        (symbol, order["side"], float(order["origQty"]), float(order["price"]), int(order["time"]))
        for order in data
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO liquidations (symbol, side, quantity, price, trade_time)
                VALUES (%s, %s, %s, %s, %s)
            """, rows)
            conn.commit()


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


async def live(symbols_intervals):
    logger.info("Live collector running")
    while True:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol, intervals in symbols_intervals:
                for interval in intervals:
                    tasks.append(_live_ohlcv(session, symbol, interval))
                    tasks.append(_live_oi(session, symbol, interval))
                tasks.append(_live_funding(session, symbol))
                tasks.append(_live_liquidations(session, symbol))
            await asyncio.gather(*tasks)
        await asyncio.sleep(max(0, LOOP_SLEEP - (time.time() - start)))


async def run():
    symbols_intervals = get_active_symbols()
    if not symbols_intervals:
        logger.error("No active symbols in DB")
        return
    logger.info(f"Symbols: {[s for s, _ in symbols_intervals]}")
    await backfill(symbols_intervals)
    await live(symbols_intervals)


if __name__ == "__main__":
    asyncio.run(run())