import asyncio
import time
import os
from database.connection import get_connection
from contracts.validation import post_outcome_checkpoint
from agent.features import _fetch_ohlcv
from agent.reputation import get_reputation_score, save_reputation_snapshot
from config import OUTCOME_LOOKBACK_CANDLES, TRAIN_INTERVAL, RETRAIN_EVERY_N_TRADES
from logger import get_logger

logger = get_logger(__name__)

TRACKER_SLEEP = int(os.getenv("OUTCOME_TRACKER_SLEEP", "60"))


def _get_pending_trades() -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, intent_hash, pair, action, entry_price,
                       amount_usd, confidence_at_entry, reputation_at_entry,
                       checkpoint_hash, created_at
                FROM trade_outcomes
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
            """)
            return cur.fetchall()


def _get_current_price(pair: str) -> float | None:
    df = _fetch_ohlcv(pair, TRAIN_INTERVAL, 5)
    if df is None or len(df) == 0:
        return None
    return float(df["close"].iloc[-1])


def _candles_since(created_at: int) -> int:
    interval_seconds = {
        "1m": 60, "3m": 180, "5m": 300, "15m": 900,
        "30m": 1800, "1h": 3600, "4h": 14400,
    }
    seconds = interval_seconds.get(TRAIN_INTERVAL, 900)
    elapsed = int(time.time()) - created_at
    return elapsed // seconds


def _label_outcome(action: str, entry_price: float, exit_price: float) -> str:
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


def _mark_outcome(trade_id: int, status: str, exit_price: float, outcome_tx: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE trade_outcomes
                SET status = %s, exit_price = %s, outcome_tx_hash = %s, resolved_at = %s
                WHERE id = %s
            """, (status, exit_price, outcome_tx, int(time.time()), trade_id))
            conn.commit()


def _count_resolved_trades() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM trade_outcomes WHERE status != 'PENDING'")
            return cur.fetchone()[0]


def _trigger_retrain_if_needed():
    resolved = _count_resolved_trades()
    if resolved > 0 and resolved % RETRAIN_EVERY_N_TRADES == 0:
        logger.info(f"[outcome_tracker] {resolved} resolved trades — triggering retrain")
        try:
            import subprocess
            subprocess.Popen(["python", "agent/train.py"])
        except Exception as e:
            logger.error(f"[outcome_tracker] retrain trigger failed: {e}")


def process_pending():
    trades = _get_pending_trades()
    if not trades:
        return

    resolved_this_pass = 0

    for row in trades:
        (trade_id, intent_hash, pair, action, entry_price,
         amount_usd, confidence, reputation, checkpoint_hash, created_at) = row

        candles_elapsed = _candles_since(created_at)
        if candles_elapsed < OUTCOME_LOOKBACK_CANDLES:
            continue

        exit_price = _get_current_price(pair)
        if exit_price is None:
            logger.warning(f"[outcome_tracker] could not get price for {pair}")
            continue

        outcome = _label_outcome(action, entry_price, exit_price)

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
            outcome_tx = ""

        _mark_outcome(trade_id, outcome, exit_price, outcome_tx)
        resolved_this_pass += 1

    if resolved_this_pass > 0:
        score = get_reputation_score()
        save_reputation_snapshot(score)
        logger.info(f"[outcome_tracker] resolved {resolved_this_pass} trades | reputation={score}")
        _trigger_retrain_if_needed()


async def run():
    logger.info("[outcome_tracker] starting")
    while True:
        try:
            process_pending()
        except Exception as e:
            logger.error(f"[outcome_tracker] loop error: {e}")
        await asyncio.sleep(TRACKER_SLEEP)


if __name__ == "__main__":
    asyncio.run(run())