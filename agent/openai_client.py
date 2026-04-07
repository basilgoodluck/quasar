import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_LEVERAGE, MIN_LEVERAGE, MAX_RISK_PCT, MIN_RISK_PCT, MIN_RR, MAX_RR
from logger import get_logger

logger  = get_logger(__name__)
_client = OpenAI(api_key=OPENAI_API_KEY)

LIMITS = {
    "leverage": {"min": MIN_LEVERAGE, "max": MAX_LEVERAGE},
    "risk_pct": {"min": MIN_RISK_PCT, "max": MAX_RISK_PCT},
    "rr_ratio": {"min": MIN_RR,       "max": MAX_RR},
}

_SYSTEM = """You are a trade sizing optimizer for a crypto futures trading agent called ARC.

You receive a market regime snapshot, a reputation score, and hard limits.
The reputation score is between 0 and 1. It reflects the agent's verified on-chain win rate and decision consistency.

Regime types:
- trending: clean directional move — good conditions, trade with normal sizing
- trending_volatile: strong move with high energy — best conditions, can push sizing
- volatile: explosive but no clear direction — only trade with tight sizing if confidence is high
- ranging: choppy, no edge — you should never receive this, but if so return SKIP

Sizing rules:
- reputation >= 0.7 → you may use up to 100% of the leverage and risk limits
- reputation 0.4–0.7 → use 50–80% of the limits
- reputation < 0.4 → stay close to the minimum limits regardless of confidence
- trending_volatile + high confidence → push toward upper bound
- volatile only → stay at lower bound regardless of confidence
- trending + low confidence → mid range
- RR toward upper bound when regime is strong, lower bound when uncertain

You must decide the trade direction based on regime context:
- If regime is trending or trending_volatile, pick LONG or SHORT based on the confidence and context
- If regime is volatile with low confidence, return SKIP

Also write a 2-3 sentence plain English explanation referencing the regime and reputation level.

Respond ONLY with valid JSON, no markdown, no extra text:
{"action": "LONG"|"SHORT"|"SKIP", "leverage": float, "risk_pct": float, "rr_ratio": float, "explanation": "string"}"""


def _clamp(value: float, key: str) -> float:
    lo      = LIMITS[key]["min"]
    hi      = LIMITS[key]["max"]
    clamped = max(lo, min(hi, value))
    if clamped != value:
        logger.warning(f"[openai] {key}={value} clamped to {clamped}")
    return round(clamped, 4)


def get_trade_params(regime: dict, reputation: float = 0.0) -> dict:
    current_regime = regime.get("regime", "ranging")

    if current_regime == "ranging":
        return {
            "action":      "SKIP",
            "leverage":    MIN_LEVERAGE,
            "risk_pct":    MIN_RISK_PCT,
            "rr_ratio":    MIN_RR,
            "explanation": "Regime is ranging. No trade taken.",
        }

    prompt = (
        f"regime={current_regime} "
        f"confidence={regime['confidence']} "
        f"p_trending={regime['p_trending']} "
        f"p_ranging={regime['p_ranging']} "
        f"p_volatile={regime['p_volatile']} "
        f"reputation={reputation}\n"
        f"limits: leverage {MIN_LEVERAGE}–{MAX_LEVERAGE}x "
        f"risk {MIN_RISK_PCT}–{MAX_RISK_PCT}% "
        f"rr {MIN_RR}–{MAX_RR}"
    )

    try:
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        choice = response.choices[0]
        raw    = choice.message.content.strip()

        if not raw:
            raise ValueError(f"Empty response from OpenAI (finish_reason={choice.finish_reason})")

        if choice.finish_reason == "length":
            raise ValueError("Response truncated by max_tokens")

        raw  = re.sub(r"^```(?:json)?\s*", "", raw)
        raw  = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)

        action = data.get("action", "SKIP").upper()
        if action not in ("LONG", "SHORT", "SKIP"):
            action = "SKIP"

        result = {
            "action":      action,
            "leverage":    _clamp(float(data.get("leverage", MIN_LEVERAGE)), "leverage"),
            "risk_pct":    _clamp(float(data.get("risk_pct", MIN_RISK_PCT)), "risk_pct"),
            "rr_ratio":    _clamp(float(data.get("rr_ratio", MIN_RR)),       "rr_ratio"),
            "explanation": str(data.get("explanation", "")),
        }

        logger.info(
            f"[openai] {result['action']} leverage={result['leverage']}x "
            f"risk={result['risk_pct']}% rr={result['rr_ratio']} reputation={reputation}"
        )
        return result

    except Exception as e:
        logger.error(f"[openai] {e}")
        return {
            "action":      "SKIP",
            "leverage":    MIN_LEVERAGE,
            "risk_pct":    MIN_RISK_PCT,
            "rr_ratio":    MIN_RR,
            "explanation": f"OpenAI call failed: {e}",
        }