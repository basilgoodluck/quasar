import asyncio
from database.connection import get_pool
from agent.strategy.arc import ARCStrategy
from agent.features import fetch_ohlcv
from agent.reputation import get_reputation_score
from agent.monitor import monitor_loop
from config import TRAIN_INTERVAL, COLLECT_LOOP_SLEEP
from logger import get_logger

logger   = get_logger(__name__)
strategy = ARCStrategy()

DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "LTCUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT",
    "OPUSDT", "ARBUSDT", "INJUSDT", "SUIUSDT",
]


async def seed_symbols():
    pool = await get_pool()
    async with pool.acquire() as conn:
        for symbol in DEFAULT_SYMBOLS:
            await conn.execute("""
                INSERT INTO symbols (symbol, active, intervals, asset_class)
                VALUES ($1, TRUE, '{5m,30m}', 'crypto')
                ON CONFLICT (symbol) DO NOTHING
            """, symbol)
    logger.info(f"[main] seeded {len(DEFAULT_SYMBOLS)} symbols")


async def get_active_symbols() -> list[str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT symbol FROM symbols WHERE active = TRUE")
        return [r["symbol"] for r in rows]


async def get_current_price(symbol: str) -> float | None:
    df = await fetch_ohlcv(symbol, TRAIN_INTERVAL, 5)
    if df is None or len(df) == 0:
        return None
    return float(df["close"].iloc[-1])


async def process_symbol(symbol: str, reputation: float):
    try:
        decision = await strategy.analyze(symbol)
        if not decision["ready"]:
            logger.info(f"[{symbol}] SKIP — {decision['explanation']}")
            return

        price = await get_current_price(symbol)
        if price is None:
            logger.warning(f"[{symbol}] could not fetch current price")
            return

        result = await strategy.open_position(decision, price, reputation)
        if result["executed"]:
            logger.info(
                f"[{symbol}] {decision['action']} executed "
                f"leverage={decision['leverage']}x "
                f"risk={decision['risk_pct']}% "
                f"rr={decision['rr_ratio']} "
                f"price={price} "
                f"sl={result['sl_price']} tp={result['tp_price']}"
            )
        else:
            logger.warning(f"[{symbol}] execution failed — {result.get('reason')}")
    except Exception as e:
        logger.error(f"[{symbol}] error: {e}")


async def main():
    logger.info("[main] agent starting")
    await seed_symbols()

    # start monitor as background task
    asyncio.create_task(monitor_loop(strategy))

    while True:
        start      = asyncio.get_event_loop().time()
        symbols    = await get_active_symbols()
        reputation = await get_reputation_score()

        if not symbols:
            logger.warning("[main] no active symbols")
            await asyncio.sleep(COLLECT_LOOP_SLEEP)
            continue

        # process sequentially so open_count check is accurate
        for symbol in symbols:
            await process_symbol(symbol, reputation)

        elapsed = asyncio.get_event_loop().time() - start
        await asyncio.sleep(max(0, COLLECT_LOOP_SLEEP - elapsed))


if __name__ == "__main__":
    asyncio.run(main())