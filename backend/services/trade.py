from database.database import get_db
from fastapi import Depends

async def get_recent_trades(limit: int = 50, db=Depends(get_db)):
    rows = await db.fetch("""
        SELECT id, pair, action, entry_price, exit_price,
               amount_usd, confidence_at_entry, reputation_at_entry,
               status, outcome_tx_hash, checkpoint_hash,
               created_at, resolved_at
        FROM trade_outcomes
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


async def get_all_trades(status: str = None, pair: str = None, limit: int = 100, db=Depends(get_db)):
    query  = "SELECT * FROM trade_outcomes WHERE 1=1"
    params = []
    i      = 1
    if status:
        query += f" AND status = ${i}"
        params.append(status)
        i += 1
    if pair:
        query += f" AND pair = ${i}"
        params.append(pair)
        i += 1
    query += f" ORDER BY created_at DESC LIMIT ${i}"
    params.append(limit)
    rows = await db.fetch(query, *params)
    return [dict(r) for r in rows]


async def get_trade_replay(trade_id: int, db=Depends(get_db)):
    trade = await db.fetchrow("""
        SELECT pair, action, entry_price, exit_price,
               created_at, resolved_at, status,
               confidence_at_entry, reputation_at_entry,
               checkpoint_hash, outcome_tx_hash
        FROM trade_outcomes
        WHERE id = $1
    """, trade_id)
    if not trade:
        return None, []

    trade = dict(trade)
    candles = await db.fetch("""
        SELECT open_time, open, high, low, close, volume
        FROM market_data
        WHERE symbol   = $1
          AND interval = '15m'
          AND open_time >= $2 - 96 * 15 * 60 * 1000
          AND open_time <= $2 + 20 * 15 * 60 * 1000
        ORDER BY open_time ASC
    """, trade["pair"], int(trade["created_at"]) * 1000)

    return trade, [dict(c) for c in candles]


async def get_pnl_curve(db=Depends(get_db)):
    rows = await db.fetch("""
        SELECT created_at, resolved_at, action,
               entry_price, exit_price, amount_usd, status
        FROM trade_outcomes
        WHERE status IN ('WIN', 'LOSS', 'NEUTRAL')
        ORDER BY created_at ASC
    """)

    curve      = []
    cumulative = 0.0
    for r in rows:
        r = dict(r)
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


async def get_checkpoints(limit: int = 100, db=Depends(get_db)):
    rows = await db.fetch("""
        SELECT pair, action, checkpoint_hash, outcome_tx_hash,
               status, created_at
        FROM trade_outcomes
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]