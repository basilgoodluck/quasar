import json
import asyncio
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from logger import get_logger

logger = get_logger(__name__)

_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
MODEL   = "gpt-4o-mini"   


TRADE_REVIEW_SYSTEM = """
You are a disciplined quantitative trading risk officer reviewing trade signals for a crypto futures bot.
You will receive a structured signal bundle and must decide whether to approve or veto the trade.

Rules:
- Be concise. Your reason must be one sentence max.
- confidence_adjustment is a float between -0.2 and +0.1. Use it to nudge the signal strength.
  Negative = you see weakness. Positive = you see extra confluence.
- Only veto (approve=false) if signals are clearly contradictory or the risk/reward is irrational.
- Do not veto just because the market is uncertain — uncertainty is normal.
- Respond ONLY with valid JSON, no markdown, no explanation outside the JSON.

Response format:
{"approve": true, "reason": "...", "confidence_adjustment": 0.0}
"""

async def ai_trade_review(
    symbol: str,
    action: str,
    entry_type: str,
    regime: dict,
    ma: dict,
    fisher: dict,
    structure: dict,
    params: dict,
    reputation: float,
) -> dict:
    """
    Ask OpenAI to sanity-check the trade signal before execution.
    Returns {"approve": bool, "reason": str, "confidence_adjustment": float}
    Falls back to approve=True on any error so AI never blocks trading due to API issues.
    """
    prompt = f"""
Symbol: {symbol}
Proposed action: {action} ({entry_type})
Reputation score: {reputation:.4f}

--- REGIME ---
regime={regime.get('regime')} confidence={regime.get('confidence'):.4f}
p_trending={regime.get('p_trending'):.4f} p_ranging={regime.get('p_ranging'):.4f} p_volatile={regime.get('p_volatile'):.4f}
trend_direction={regime.get('trend_direction')} strength={regime.get('direction_strength'):+.4f}

--- INDICATORS ---
{ma['note']}
{fisher['note']}

--- STRUCTURE ---
{structure['note']}

--- RISK PARAMS ---
leverage={params['leverage']}x  risk_pct={params['risk_pct']:.4f}  rr_ratio={params['rr_ratio']}  amount_usd=${params['amount_usd']}

Should this trade be approved?
""".strip()

    try:
        response = await _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": TRADE_REVIEW_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,
            max_tokens=120,
        )
        raw  = response.choices[0].message.content.strip()
        data = json.loads(raw)

        approve               = bool(data.get("approve", True))
        reason                = str(data.get("reason", ""))
        confidence_adjustment = float(data.get("confidence_adjustment", 0.0))
        confidence_adjustment = max(-0.2, min(0.1, confidence_adjustment))  # clamp

        logger.info(
            f"[ai_advisor] {symbol} {action} → approve={approve} "
            f"adj={confidence_adjustment:+.2f} reason={reason}"
        )
        return {"approve": approve, "reason": reason, "confidence_adjustment": confidence_adjustment}

    except Exception as e:
        logger.warning(f"[ai_advisor] trade review failed ({e}) — defaulting to approve")
        return {"approve": True, "reason": "AI review unavailable", "confidence_adjustment": 0.0}



REPUTATION_SYSTEM = """
You are a trading performance analyst. You will receive a summary of recent trade outcomes for a crypto futures bot.
Your job is to identify *specific, actionable* patterns in where the bot wins and loses.

Rules:
- Be specific. Generic advice like "be careful" is useless.
- Focus on: regime type, entry_type (trend vs reversal), trend direction, confidence level.
- Output a bias dict the strategy can use to filter or scale future trades.
- avoid_conditions is a list of plain-English strings describing what to avoid.
- Respond ONLY with valid JSON, no markdown.

Response format:
{
  "avoid_conditions": ["bearish reversal entries when confidence < 0.55", "..."],
  "prefer_conditions": ["bullish trend entries with confidence > 0.65", "..."],
  "summary": "one sentence on the core pattern"
}
"""

async def ai_reputation_insight(
    score: float,
    win_rate: float,
    consistency: float,
    streak: int,
    trade_rows: list[dict],
) -> dict:
    """
    Analyse the recent trade history for patterns and return actionable bias hints.
    Falls back to empty bias on any error.
    trade_rows: list of dicts with keys: status, regime, entry_type, trend_direction, confidence_at_entry
    """
    if not trade_rows:
        return {"avoid_conditions": [], "prefer_conditions": [], "summary": "no data"}

    # Summarise trades compactly so we don't blow the token budget
    trade_lines = []
    for r in trade_rows:
        trade_lines.append(
            f"  {r.get('status','?'):4s} | regime={r.get('regime','?'):18s} | "
            f"entry={r.get('entry_type','?'):8s} | dir={r.get('trend_direction','?'):7s} | "
            f"conf={r.get('confidence_at_entry', 0):.2f}"
        )
    trades_block = "\n".join(trade_lines)

    prompt = f"""
Reputation score: {score:.4f}
Win rate: {win_rate:.2%}
Consistency (confident & right): {consistency:.2%}
Current winning streak: {streak}

Recent trades (newest first):
{trades_block}

Identify patterns in wins vs losses and return your bias dict.
""".strip()

    try:
        response = await _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": REPUTATION_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        raw  = response.choices[0].message.content.strip()
        data = json.loads(raw)

        avoid  = data.get("avoid_conditions",  [])
        prefer = data.get("prefer_conditions", [])
        summary = data.get("summary", "")

        logger.info(f"[ai_advisor] reputation insight: {summary}")
        logger.info(f"[ai_advisor] avoid={avoid} | prefer={prefer}")

        return {"avoid_conditions": avoid, "prefer_conditions": prefer, "summary": summary}

    except Exception as e:
        logger.warning(f"[ai_advisor] reputation insight failed ({e}) — returning empty bias")
        return {"avoid_conditions": [], "prefer_conditions": [], "summary": "AI insight unavailable"}