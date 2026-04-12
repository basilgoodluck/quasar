import asyncio
import time
from web3 import Web3
from database.connection import get_pool
from config import (
    REPUTATION_MIN_TRADES,
    AGENT_ID,
    SEPOLIA_RPC_URL,
    REPUTATION_REGISTRY_ADDRESS,
    REPUTATION_REGISTRY_ABI,
    AGENT_WALLET_PRIVATE_KEY,
)
from logger import get_logger

logger    = get_logger(__name__)
_w3       = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
_registry = None
_account  = None


def _get_registry():
    global _registry, _account
    if _registry is None:
        _registry = _w3.eth.contract(
            address=Web3.to_checksum_address(REPUTATION_REGISTRY_ADDRESS),
            abi=REPUTATION_REGISTRY_ABI,
        )
        _account = _w3.eth.account.from_key(AGENT_WALLET_PRIVATE_KEY)
    return _registry, _account


def _submit_on_chain(score: float, outcome_ref: bytes, comment: str):
    registry, account = _get_registry()
    try:
        tx = registry.functions.submitFeedback(
            AGENT_ID,
            int(score * 100),
            outcome_ref,
            comment,
            0,
        ).build_transaction({
            "from":     account.address,
            "nonce":    _w3.eth.get_transaction_count(account.address),
            "gas":      200000,
            "gasPrice": _w3.eth.gas_price,
        })
        signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
        tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        _w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info(f"[reputation] on-chain feedback submitted tx={tx_hash.hex()}")
    except Exception as e:
        logger.error(f"[reputation] on-chain submission failed: {e}")


async def get_reputation_score() -> float:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT status, confidence_at_entry, regime, entry_type, trend_direction
            FROM trade_outcomes
            WHERE status IN ('WIN', 'LOSS', 'NEUTRAL')
            ORDER BY created_at DESC
            LIMIT 100
        """)

    if not rows or len(rows) < REPUTATION_MIN_TRADES:
        logger.info(f"[reputation] not enough trades yet ({len(rows) if rows else 0}/{REPUTATION_MIN_TRADES})")
        return 0.0

    total    = len(rows)
    wins     = sum(1 for r in rows if r["status"] == "WIN")
    win_rate = wins / total

    confident_and_right = sum(1 for r in rows if r["status"] == "WIN"  and r["confidence_at_entry"] >= 0.65)
    confident_and_wrong = sum(1 for r in rows if r["status"] == "LOSS" and r["confidence_at_entry"] >= 0.65)
    consistency         = confident_and_right / (confident_and_right + confident_and_wrong + 1e-9)

    streak = 0
    for r in rows:
        if r["status"] == "WIN":
            streak += 1
        else:
            break
    streak_bonus = min(0.1, streak * 0.01) if streak >= 5 else 0.0

    score = round(min(1.0, max(0.0, (win_rate * 0.6) + (consistency * 0.3) + (streak_bonus * 0.1))), 4)

    logger.info(
        f"[reputation] score={score} win_rate={win_rate:.2f} "
        f"consistency={consistency:.2f} streak={streak} trades={total}"
    )

    # --- AI REPUTATION INSIGHT ---
    # Run in background — never block score return on AI availability.
    # The insight is logged and cached for the strategy to optionally read.
    try:
        trade_rows = [dict(r) for r in rows]
        asyncio.create_task(
            _run_and_cache_insight(score, win_rate, consistency, streak, trade_rows)
        )
    except Exception as e:
        logger.warning(f"[reputation] failed to schedule AI insight: {e}")

    return score


# Module-level cache so arc.py can read the latest insight without waiting
_latest_insight: dict = {"avoid_conditions": [], "prefer_conditions": [], "summary": ""}


async def _run_and_cache_insight(
    score: float,
    win_rate: float,
    consistency: float,
    streak: int,
    trade_rows: list[dict],
):
    global _latest_insight
    from agent.ai_advisor import ai_reputation_insight
    insight = await ai_reputation_insight(
        score=score,
        win_rate=win_rate,
        consistency=consistency,
        streak=streak,
        trade_rows=trade_rows,
    )
    _latest_insight = insight


def get_latest_insight() -> dict:
    """
    Returns the most recently computed AI reputation insight.
    Safe to call from arc.py — returns empty bias if insight not yet computed.
    """
    return _latest_insight


async def save_reputation_snapshot(score: float, outcome_ref: bytes = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO reputation_history (agent_id, score, recorded_at)
            VALUES ($1, $2, $3)
        """, AGENT_ID, score, int(time.time()))

    if outcome_ref is None:
        outcome_ref = bytes(32)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _submit_on_chain, score, outcome_ref, f"score={score}")


async def get_reputation_history(limit: int = 50) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT score, recorded_at
            FROM reputation_history
            WHERE agent_id = $1
            ORDER BY recorded_at DESC
            LIMIT $2
        """, AGENT_ID, limit)