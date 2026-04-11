import time


# ─── Trades ───────────────────────────────────────────────────────────────────

async def get_recent_trades(limit: int = 50, db=None):
    rows = await db.fetch("""
        SELECT id, pair, action, entry_price, exit_price,
               amount_usd, confidence_at_entry, reputation_at_entry,
               status, outcome_tx_hash, checkpoint_hash,
               sl_price, tp_price, rr_ratio,
               created_at, resolved_at
        FROM trade_outcomes
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


async def get_all_trades(status: str = None, pair: str = None, limit: int = 100, db=None):
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


async def get_pnl_curve(db=None):
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


# ─── Dashboard Overview ───────────────────────────────────────────────────────

async def get_dashboard_overview(db=None):
    rows = await db.fetch("""
        SELECT action, entry_price, exit_price, amount_usd,
               status, sl_price, tp_price, rr_ratio,
               confidence_at_entry, reputation_at_entry
        FROM trade_outcomes
        ORDER BY created_at ASC
    """)

    rows     = [dict(r) for r in rows]
    wins     = sum(1 for r in rows if r["status"] == "WIN")
    losses   = sum(1 for r in rows if r["status"] == "LOSS")
    active   = sum(1 for r in rows if r["status"] == "PENDING")
    win_rate = round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else 0.0

    total_pnl = 0.0
    peak      = 0.0
    drawdown  = 0.0
    max_dd    = 0.0
    equity    = 10000.0

    for r in rows:
        if r["exit_price"] and r["entry_price"] and r["status"] != "PENDING":
            pct = (
                (r["exit_price"] - r["entry_price"]) / r["entry_price"]
                if r["action"] == "LONG"
                else (r["entry_price"] - r["exit_price"]) / r["entry_price"]
            )
            pnl       = float(r["amount_usd"]) * pct
            total_pnl = round(total_pnl + pnl, 4)
            equity   += pnl
            if equity > peak:
                peak = equity
            drawdown = round((peak - equity) / peak * 100, 4) if peak > 0 else 0.0
            if drawdown > max_dd:
                max_dd = drawdown

    rep_row = await db.fetchrow("""
        SELECT score FROM reputation_history
        ORDER BY recorded_at DESC LIMIT 1
    """)
    reputation = float(rep_row["score"]) if rep_row else 0.0

    return {
        "totalPnL":        round(total_pnl, 4),
        "winRate":         win_rate,
        "currentDrawdown": drawdown,
        "maxDrawdown":     max_dd,
        "activePositions": active,
        "equity":          round(equity, 4),
        "totalCapital":    10000.0,
        "reputationScore": reputation,
        "totalTrades":     len(rows),
        "wins":            wins,
        "losses":          losses,
    }


# ─── Activity / Events ────────────────────────────────────────────────────────

async def get_activity(limit: int = 50, db=None):
    rows = await db.fetch("""
        SELECT id, type, trade_id, pair, payload, notified, created_at
        FROM events
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


async def create_event(type: str, db=None, pair: str = None, trade_id: int = None, payload: dict = None):
    await db.execute("""
        INSERT INTO events (type, trade_id, pair, payload, created_at)
        VALUES ($1, $2, $3, $4, $5)
    """, type, trade_id, pair, payload, int(time.time()))