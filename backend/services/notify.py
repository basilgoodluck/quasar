import httpx
from config import DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


async def _discord(message: str):
    if not DISCORD_WEBHOOK_URL:
        return
    async with httpx.AsyncClient() as client:
        await client.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=5,
        )


async def _telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"},
            timeout=5,
        )


async def notify(message: str):
    try:
        await _discord(message)
    except Exception:
        pass
    try:
        await _telegram(message)
    except Exception:
        pass


async def notify_trade_open(pair: str, action: str, leverage: float, risk_pct: float, price: float, explanation: str):
    msg = (
        f"🟢 *TRADE OPEN*\n"
        f"Pair: `{pair}` | Action: `{action}`\n"
        f"Price: `{price}` | Leverage: `{leverage}x` | Risk: `{risk_pct}%`\n"
        f"Reason: {explanation}"
    )
    await notify(msg)


async def notify_trade_close(pair: str, action: str, outcome: str, entry: float, exit_price: float, tx: str):
    emoji = "✅" if outcome == "WIN" else "❌" if outcome == "LOSS" else "➖"
    msg = (
        f"{emoji} *TRADE CLOSED — {outcome}*\n"
        f"Pair: `{pair}` | Action: `{action}`\n"
        f"Entry: `{entry}` → Exit: `{exit_price}`\n"
        f"On-chain: `{tx}`"
    )
    await notify(msg)


async def notify_reputation(score: float):
    msg = f"⭐ *REPUTATION UPDATE*\nNew score: `{score}`"
    await notify(msg)


async def notify_retrain(val_loss: float, real_labels: int):
    msg = (
        f"🔁 *MODEL RETRAIN*\n"
        f"Val loss: `{val_loss:.6f}` | Real labels: `{real_labels}`"
    )
    await notify(msg)


async def notify_error(context: str, error: str):
    msg = f"🚨 *AGENT ERROR*\nContext: `{context}`\nError: `{error}`"
    await notify(msg)
