import asyncio
import time
import os
from database.connection import get_pool
from contracts.validation import post_outcome_checkpoint
from agent.features import fetch_ohlcv
from agent.reputation import get_reputation_score, save_reputation_snapshot
from config import OUTCOME_LOOKBACK_CANDLES, TRAIN_INTERVAL, RETRAIN_EVERY_N_TRADES
from logger import get_logger

logger = get_logger(__name__)

TRACKER_SLEEP = int(os.getenv("OUTCOME_TRACKER_SLEEP", "60"))


async def get_pending_trades() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT id, intent_hash, pair, action, entry_price,
                   amount_usd, confidence_at_entry, reputation_at_entry,
                   checkpoint_hash, created_at
            FROM trade_outcomes
            WHERE status = 'PENDING'
            ORDER BY created_at ASC
        """)


async def get_current_price(pair: str) -> float | None:
    df = await fetch_ohlcv(pair, TRAIN_INTERVAL, 5)
    if df is None or len(df) == 0:
        return None
    return float(df["close"].iloc[-1])


def candles_since(created_at: int) -> int:
    interval_seconds = {
        "1m": 60, "3m": 180, "5m": 300, "15m": 900,
        "30m": 1800, "1h": 3600, "4h": 14400,
    }
    seconds = interval_seconds.get(TRAIN_INTERVAL, 300)
    elapsed = int(time.time()) - created_at
    return elapsed // seconds


def label_outcome(action: str, entry_price: float, exit_price: float) -> str:
    pnl_pct = (
        (exit_price - entry_price) / entry_price
        if action == "LONG"
        else (entry_price - exit_price) / entry_price
    )
    if pnl_pct > 0.003:
        return "WIN"
    if pnl_pct < -0.003:
        return "LOSS"
    return "NEUTRAL"


async def mark_outcome(trade_id: int, status: str, exit_price: float, outcome_tx: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE trade_outcomes
            SET status = $1, exit_price = $2, outcome_tx_hash = $3, resolved_at = $4
            WHERE id = $5
        """, status, exit_price, outcome_tx, int(time.time()), trade_id)


async def count_resolved_trades() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) FROM trade_outcomes WHERE status != 'PENDING'")
        return row["count"]


async def trigger_retrain_if_needed():
    resolved = await count_resolved_trades()
    if resolved > 0 and resolved % RETRAIN_EVERY_N_TRADES == 0:
        logger.info(f"[outcome_tracker] {resolved} resolved trades — triggering retrain")
        try:
            proc = await asyncio.create_subprocess_exec("python", "agent/train.py")
            logger.info(f"[outcome_tracker] retrain process started pid={proc.pid}")
        except Exception as e:
            logger.error(f"[outcome_tracker] retrain trigger failed: {e}")


async def process_pending():
    trades = await get_pending_trades()
    if not trades:
        return

    resolved_this_pass = 0

    for row in trades:
        trade_id     = row["id"]
        intent_hash  = row["intent_hash"]
        pair         = row["pair"]
        action       = row["action"]
        entry_price  = float(row["entry_price"])
        confidence   = float(row["confidence_at_entry"])
        created_at   = row["created_at"]

        if candles_since(created_at) < OUTCOME_LOOKBACK_CANDLES:
            continue

        exit_price = await get_current_price(pair)
        if exit_price is None:
            logger.warning(f"[outcome_tracker] could not get price for {pair}")
            continue

        outcome    = label_outcome(action, entry_price, exit_price)
        outcome_tx = ""

        try:
            result = post_outcome_checkpoint(
                pair=pair,
                action=action,
                outcome=outcome,
                original_intent_hash=intent_hash,
                entry_price=entry_price,
                exit_price=exit_price,
                confidence_at_entry=confidence,
            )
            outcome_tx = result["tx_hash"]
            logger.info(
                f"[outcome_tracker] {pair} {action} {outcome} "
                f"entry={entry_price} exit={exit_price} tx={outcome_tx}"
            )
        except Exception as e:
            logger.error(f"[outcome_tracker] on-chain post failed for {intent_hash}: {e}")

        await mark_outcome(trade_id, outcome, exit_price, outcome_tx)
        resolved_this_pass += 1

    if resolved_this_pass > 0:
        score = await get_reputation_score()
        await save_reputation_snapshot(score)
        logger.info(f"[outcome_tracker] resolved {resolved_this_pass} trades | reputation={score}")
        await trigger_retrain_if_needed()


async def run():
    logger.info("[outcome_tracker] starting")
    while True:
        try:
            await process_pending()
        except Exception as e:
            logger.error(f"[outcome_tracker] loop error: {e}")
        await asyncio.sleep(TRACKER_SLEEP)


if __name__ == "__main__":
    asyncio.run(run())