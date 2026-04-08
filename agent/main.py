import time
from database.connection import get_connection
from agent.strategy.arc import ARCStrategy
from agent.features import _fetch_ohlcv
from agent.reputation import get_reputation_score
from config import TRAIN_INTERVAL, COLLECT_LOOP_SLEEP
from logger import get_logger

logger   = get_logger(__name__)
strategy = ARCStrategy()

DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "LTCUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT",
    "OPUSDT", "ARBUSDT", "INJUSDT", "SUIUSDT", "MATICUSDT",
]


def seed_symbols():
    with get_connection() as conn:
        with conn.cursor() as cur:
            for symbol in DEFAULT_SYMBOLS:
                cur.execute("""
                    INSERT INTO symbols (symbol, active, intervals, asset_class)
                    VALUES (%s, TRUE, '{5m,30m}', 'crypto')
                    ON CONFLICT (symbol) DO NOTHING
                """, (symbol,))
            conn.commit()
    logger.info(f"[main] seeded {len(DEFAULT_SYMBOLS)} symbols")


def get_active_symbols() -> list[str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT symbol FROM symbols WHERE active = TRUE")
            return [r[0] for r in cur.fetchall()]


def get_current_price(symbol: str) -> float | None:
    df = _fetch_ohlcv(symbol, TRAIN_INTERVAL, 5)
    if df is None or len(df) == 0:
        return None
    return float(df["close"].iloc[-1])


def main():
    logger.info("[main] agent starting")
    seed_symbols()
    while True:
        start      = time.time()
        symbols    = get_active_symbols()
        reputation = get_reputation_score()

        if not symbols:
            logger.warning("[main] no active symbols")
            time.sleep(COLLECT_LOOP_SLEEP)
            continue

        for symbol in symbols:
            try:
                decision = strategy.analyze(symbol)

                if not decision["ready"]:
                    logger.info(f"[{symbol}] SKIP — {decision['explanation']}")
                    continue

                price = get_current_price(symbol)
                if price is None:
                    logger.warning(f"[{symbol}] could not fetch current price")
                    continue

                result = strategy.open_position(decision, price, reputation)

                if result["executed"]:
                    logger.info(
                        f"[{symbol}] {decision['action']} executed "
                        f"leverage={decision['leverage']}x "
                        f"risk={decision['risk_pct']}% "
                        f"rr={decision['rr_ratio']} "
                        f"price={price}"
                    )
                else:
                    logger.warning(f"[{symbol}] execution failed — {result.get('reason')}")

            except Exception as e:
                logger.error(f"[{symbol}] error: {e}")

        time.sleep(max(0, COLLECT_LOOP_SLEEP - (time.time() - start)))


if __name__ == "__main__":
    main()