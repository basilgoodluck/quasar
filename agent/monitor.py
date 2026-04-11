import asyncio
import time
from agent.features import fetch_ohlcv
from agent.strategy.base import BaseStrategy
from database.connection import get_pool
from config import TRAIN_INTERVAL
from logger import get_logger

logger = get_logger(__name__)

POLL_INTERVAL = 30    # seconds
MAX_TRADE_AGE = 3600  # 1 hour


def _pf_to_symbol(pf_pair: str) -> str:
    """Convert PF_XBTUSD -> BTCUSDT, PF_ETHUSD -> ETHUSDT, etc."""
    base = pf_pair.replace("PF_", "").replace("USD", "")
    base = "BTC" if base == "XBT" else base
    return f"{base}USDT"


async def get_pending_trades() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT intent_hash, pair, action, entry_price, amount_usd,
                   sl_price, tp_price, rr_ratio, created_at
            FROM trade_outcomes
            WHERE status = 'PENDING'
        """)
    return [dict(r) for r in rows]


async def get_current_price(symbol: str) -> float | None:
    df = await fetch_ohlcv(symbol, TRAIN_INTERVAL, 5)
    if df is None or len(df) == 0:
        return None
    return float(df["close"].iloc[-1])


async def monitor_loop(strategy: BaseStrategy):
    logger.info("[monitor] trade monitor started")
    while True:
        try:
            trades = await get_pending_trades()
            if not trades:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            now = int(time.time())

            for trade in trades:
                intent_hash = trade["intent_hash"]
                pf_pair     = trade["pair"]           # e.g. PF_XBTUSD
                symbol      = _pf_to_symbol(pf_pair)  # e.g. BTCUSDT
                action      = trade["action"]
                entry_price = float(trade["entry_price"])
                amount_usd  = float(trade["amount_usd"])
                sl_price    = float(trade["sl_price"]) if trade["sl_price"] else None
                tp_price    = float(trade["tp_price"]) if trade["tp_price"] else None
                created_at  = int(trade["created_at"])
                age         = now - created_at

                current_price = await get_current_price(symbol)
                if current_price is None:
                    logger.warning(f"[monitor] could not fetch price for {symbol}")
                    continue

                contracts    = str(round(amount_usd / entry_price, 4))
                close_reason = None

                if age >= MAX_TRADE_AGE:
                    close_reason = f"timeout — trade open for {age}s (limit {MAX_TRADE_AGE}s)"

                elif action == "LONG":
                    if sl_price and current_price <= sl_price:
                        close_reason = f"SL hit — price={current_price} <= sl={sl_price}"
                    elif tp_price and current_price >= tp_price:
                        close_reason = f"TP hit — price={current_price} >= tp={tp_price}"

                elif action == "SHORT":
                    if sl_price and current_price >= sl_price:
                        close_reason = f"SL hit — price={current_price} >= sl={sl_price}"
                    elif tp_price and current_price <= tp_price:
                        close_reason = f"TP hit — price={current_price} <= tp={tp_price}"

                if close_reason:
                    logger.info(f"[monitor] closing {symbol} ({action}) — {close_reason}")
                    result = await strategy.close_position(
                        symbol=symbol,
                        volume=contracts,
                        intent_hash=intent_hash,
                        exit_price=current_price,
                        reason=close_reason,
                    )
                    if result["closed"]:
                        logger.info(f"[monitor] {symbol} closed — status={result['status']}")
                    else:
                        logger.error(f"[monitor] {symbol} close failed — {result.get('reason')}")
                else:
                    logger.info(
                        f"[monitor] {symbol} ({action}) watching — "
                        f"price={current_price} sl={sl_price} tp={tp_price} age={age}s"
                    )

        except Exception as e:
            logger.error(f"[monitor] error: {e}")

        await asyncio.sleep(POLL_INTERVAL)