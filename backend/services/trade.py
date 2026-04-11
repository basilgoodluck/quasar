# services/trade.py
from datetime import datetime, timezone


def format_trade(r: dict) -> dict:
    created_at = r["created_at"]
    dt = datetime.fromtimestamp(created_at, tz=timezone.utc) if isinstance(created_at, (int, float)) else created_at

    entry  = float(r["entry_price"]) if r["entry_price"] else 0.0
    exit_  = float(r["exit_price"])  if r["exit_price"]  else 0.0
    amount = float(r["amount_usd"])  if r["amount_usd"]  else 0.0

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
        "confidence":  float(r["confidence_at_entry"]) if r["confidence_at_entry"] else 0.0,
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