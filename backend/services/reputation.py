from db import get_connection


def get_reputation():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT score, recorded_at
                FROM reputation_history
                ORDER BY recorded_at DESC
                LIMIT 100
            """)
            history = list(cur.fetchall())
    current = float(history[0]["score"]) if history else 0.0
    return current, history
