import time
from database.connection import get_connection
from config import REPUTATION_MIN_TRADES, AGENT_ID
from logger import get_logger

logger = get_logger(__name__)


def get_reputation_score() -> float:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT outcome, confidence_at_entry
                FROM trade_outcomes
                WHERE status IN ('WIN', 'LOSS', 'NEUTRAL')
                ORDER BY created_at DESC
                LIMIT 100
            """)
            rows = cur.fetchall()

    if not rows or len(rows) < REPUTATION_MIN_TRADES:
        logger.info(f"[reputation] not enough trades yet ({len(rows) if rows else 0}/{REPUTATION_MIN_TRADES})")
        return 0.0

    total   = len(rows)
    wins    = sum(1 for r in rows if r[0] == "WIN")
    losses  = sum(1 for r in rows if r[0] == "LOSS")

    win_rate = wins / total

    confident_and_right = sum(
        1 for r in rows if r[0] == "WIN" and r[1] >= 0.65
    )
    confident_and_wrong = sum(
        1 for r in rows if r[0] == "LOSS" and r[1] >= 0.65
    )
    consistency = (
        confident_and_right / (confident_and_right + confident_and_wrong + 1e-9)
    )

    streak_bonus = 0.0
    streak       = 0
    for r in rows:
        if r[0] == "WIN":
            streak += 1
        else:
            break
    if streak >= 5:
        streak_bonus = min(0.1, streak * 0.01)

    score = (win_rate * 0.6) + (consistency * 0.3) + (streak_bonus * 0.1)
    score = round(min(1.0, max(0.0, score)), 4)

    logger.info(
        f"[reputation] score={score} win_rate={win_rate:.2f} "
        f"consistency={consistency:.2f} streak={streak} trades={total}"
    )
    return score


def save_reputation_snapshot(score: float):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reputation_history (agent_id, score, recorded_at)
                VALUES (%s, %s, %s)
            """, (AGENT_ID, score, int(time.time())))
            conn.commit()


def get_reputation_history(limit: int = 50) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT score, recorded_at
                FROM reputation_history
                WHERE agent_id = %s
                ORDER BY recorded_at DESC
                LIMIT %s
            """, (AGENT_ID, limit))
            return cur.fetchall()