from db import get_connection


def get_recent_trades(limit: int = 50):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, pair, action, entry_price, exit_price,
                       amount_usd, confidence_at_entry, reputation_at_entry,
                       status, outcome_tx_hash, checkpoint_hash,
                       created_at, resolved_at
                FROM trade_outcomes
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            return list(cur.fetchall())


def get_all_trades(status: str = None, pair: str = None, limit: int = 100):
    query  = "SELECT * FROM trade_outcomes WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if pair:
        query += " AND pair = %s"
        params.append(pair)
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return list(cur.fetchall())


def get_trade_replay(trade_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pair, action, entry_price, exit_price,
                       created_at, resolved_at, status,
                       confidence_at_entry, reputation_at_entry,
                       checkpoint_hash, outcome_tx_hash
                FROM trade_outcomes
                WHERE id = %s
            """, (trade_id,))
            trade = cur.fetchone()
            if not trade:
                return None, []

            cur.execute("""
                SELECT open_time, open, high, low, close, volume
                FROM market_data
                WHERE symbol   = %s
                  AND interval = '15m'
                  AND open_time >= %s - 96 * 15 * 60 * 1000
                  AND open_time <= %s + 20 * 15 * 60 * 1000
                ORDER BY open_time ASC
            """, (trade["pair"], trade["created_at"] * 1000, trade["created_at"] * 1000))
            candles = list(cur.fetchall())

    return dict(trade), candles


def get_pnl_curve():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_at, resolved_at, action,
                       entry_price, exit_price, amount_usd, status
                FROM trade_outcomes
                WHERE status IN ('WIN', 'LOSS', 'NEUTRAL')
                ORDER BY created_at ASC
            """)
            rows = cur.fetchall()

    curve      = []
    cumulative = 0.0
    for r in rows:
        if r["exit_price"] and r["entry_price"]:
            pct = (
                (r["exit_price"] - r["entry_price"]) / r["entry_price"]
                if r["action"] == "LONG"
                else (r["entry_price"] - r["exit_price"]) / r["entry_price"]
            )
            pnl_usd    = round(float(r["amount_usd"]) * pct, 4)
            cumulative = round(cumulative + pnl_usd, 4)
            curve.append({
                "ts":         r["resolved_at"],
                "pnl":        pnl_usd,
                "cumulative": cumulative,
            })

    return curve, cumulative


def get_checkpoints(limit: int = 100):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pair, action, checkpoint_hash, outcome_tx_hash,
                       status, created_at
                FROM trade_outcomes
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            return list(cur.fetchall())