# services/trade.py
import time
from datetime import datetime, timezone
from decimal import Decimal


def to_float(v) -> float:
    if v is None:
        return 0.0
    return float(v)


def format_trade(r: dict) -> dict:
    created_at = r["created_at"]
    dt = datetime.fromtimestamp(created_at, tz=timezone.utc) if isinstance(created_at, (int, float)) else created_at

    entry  = to_float(r["entry_price"])
    exit_  = to_float(r["exit_price"])
    amount = to_float(r["amount_usd"])

    if entry and exit_:
        pct = (exit_ - entry) / entry if r["action"] == "LONG" else (entry - exit_) / entry
        pnl = round(amount * pct, 4)
    else:
        pnl = 0.0

    return {
        "id":          str(r["id"]),
        "symbol":      r["pair"],
        "side":        "BUY" if r["action"] == "LONG" else "SELL",
        "entry_price": entry,
        "exit_price":  exit_,
        "pnl":         pnl,
        "confidence":  to_float(r["confidence_at_entry"]),
        "decision":    "approved" if r["status"] in ("PENDING", "WIN", "LOSS", "NEUTRAL") else "skipped",
        "timestamp":   dt.isoformat(),
        "hour":        dt.hour,
        "volume":      amount,
    }


async def get_all_trades(status: str = None, pair: str = None, limit: int = 100, db=None) -> list:
    query = """
        SELECT id, pair, action, entry_price, exit_price,
               amount_usd, confidence_at_entry, status, created_at
        FROM trade_outcomes
        WHERE 1=1
    """
    params = []
    i = 1
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
    return [format_trade(dict(r)) for r in rows]


async def get_dashboard_overview(db=None) -> dict:
    rows = await db.fetch("""
        SELECT action, entry_price, exit_price, amount_usd,
               status, confidence_at_entry, sl_price, tp_price, rr_ratio
        FROM trade_outcomes
        ORDER BY created_at ASC
    """)
    rows = [dict(r) for r in rows]

    wins     = sum(1 for r in rows if r["status"] == "WIN")
    losses   = sum(1 for r in rows if r["status"] == "LOSS")
    active   = sum(1 for r in rows if r["status"] == "PENDING")
    resolved = wins + losses
    win_rate = round(wins / resolved * 100, 2) if resolved > 0 else 0.0

    total_pnl = 0.0
    peak      = 0.0
    drawdown  = 0.0
    max_dd    = 0.0
    equity    = 10000.0
    pnl_list  = []
    rr_list   = []

    for r in rows:
        entry  = to_float(r["entry_price"])
        exit_  = to_float(r["exit_price"])
        amount = to_float(r["amount_usd"])

        if entry and exit_ and r["status"] != "PENDING":
            pct = (exit_ - entry) / entry if r["action"] == "LONG" else (entry - exit_) / entry
            pnl       = amount * pct
            total_pnl = round(total_pnl + pnl, 4)
            equity   += pnl
            pnl_list.append(pnl)
            if equity > peak:
                peak = equity
            drawdown = round((peak - equity) / peak * 100, 4) if peak > 0 else 0.0
            if drawdown > max_dd:
                max_dd = drawdown

        if r["rr_ratio"]:
            rr_list.append(to_float(r["rr_ratio"]))

    best_trade  = max(pnl_list) if pnl_list else 0.0
    worst_trade = min(pnl_list) if pnl_list else 0.0
    avg_rr      = round(sum(rr_list) / len(rr_list), 4) if rr_list else 0.0

    # Reputation
    rep_row = await db.fetchrow("SELECT score FROM reputation_history ORDER BY recorded_at DESC LIMIT 1")
    rep_prev = await db.fetchrow("SELECT score FROM reputation_history ORDER BY recorded_at DESC LIMIT 1 OFFSET 1")
    reputation = to_float(rep_row["score"]) if rep_row else 0.0
    if rep_prev:
        prev = to_float(rep_prev["score"])
        rep_trend = "up" if reputation > prev else ("down" if reputation < prev else "flat")
    else:
        rep_trend = "flat"

    # Regimes
    regime_rows = await db.fetch("""
        SELECT DISTINCT ON (symbol) symbol, direction, p_long, p_short, p_neutral
        FROM snapshots
        ORDER BY symbol, created_at DESC
    """)
    regimes = {
        r["symbol"]: {
            "direction": r["direction"],
            "p_long":    to_float(r["p_long"]),
            "p_short":   to_float(r["p_short"]),
            "p_neutral": to_float(r["p_neutral"]),
        }
        for r in regime_rows
    }

    # Recent outcomes
    outcome_rows = await db.fetch("""
        SELECT id, pair, action, entry_price, exit_price,
               amount_usd, confidence_at_entry, status, created_at
        FROM trade_outcomes
        WHERE status IN ('WIN', 'LOSS', 'NEUTRAL')
        ORDER BY created_at DESC LIMIT 5
    """)
    recent_outcomes = [format_trade(dict(r)) for r in outcome_rows]

    # Symbols traded
    sym_rows = await db.fetch("SELECT DISTINCT pair FROM trade_outcomes")
    symbols_traded = [r["pair"] for r in sym_rows]

    return {
        "totalPnl":        round(total_pnl, 4),
        "winRate":         win_rate,
        "currentDrawdown": drawdown,
        "maxDrawdown":     max_dd,
        "activePositions": active,
        "totalEquity":     round(equity, 4),
        "resolvedTrades":  resolved,
        "winCount":        wins,
        "lossCount":       losses,
        "avgRR":           avg_rr,
        "bestTrade":       round(best_trade, 4),
        "worstTrade":      round(worst_trade, 4),
        "reputationScore": reputation,
        "reputationTrend": rep_trend,
        "regimes":         regimes,
        "symbolsTraded":   symbols_traded,
        "recentOutcomes":  recent_outcomes,
    }


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