import json
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

You receive a full market regime snapshot and hard limits.
Based on the regime values decide the exact leverage, risk % and RR ratio within those limits.
Also write a 2-3 sentence plain English explanation of the trade: what the market is doing, why this is a valid setup, and what the key risk is.

- High confidence + low volatility → push leverage and risk toward upper bound
- Low confidence + high volatility → pull leverage and risk toward lower bound
- Strong trend → RR toward upper bound
- Weak trend → RR toward lower bound
- neutral direction → action must be SKIP

Respond ONLY with valid JSON, no markdown, no extra text:
{"action": "LONG"|"SHORT"|"SKIP", "leverage": float, "risk_pct": float, "rr_ratio": float, "explanation": "string"}"""


def _clamp(value: float, key: str) -> float:
    lo      = LIMITS[key]["min"]
    hi      = LIMITS[key]["max"]
    clamped = max(lo, min(hi, value))
    if clamped != value:
        logger.warning(f"[openai] {key}={value} clamped to {clamped}")
    return round(clamped, 4)


def get_trade_params(regime: dict) -> dict:
    if regime.get("direction", "neutral") == "neutral":
        return {
            "action":      "SKIP",
            "leverage":    MIN_LEVERAGE,
            "risk_pct":    MIN_RISK_PCT,
            "rr_ratio":    MIN_RR,
            "explanation": "Regime direction is neutral. No trade taken.",
        }

    prompt = (
        f"confidence={regime['confidence']} "
        f"volatility_regime={regime['volatility_regime']} "
        f"activity_score={regime['activity_score']} "
        f"trend_strength={regime['trend_strength']} "
        f"direction={regime['direction']}\n"
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
            max_tokens=300,
        )

        data   = json.loads(response.choices[0].message.content.strip())
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

        logger.info(f"[openai] {result['action']} leverage={result['leverage']}x risk={result['risk_pct']}% rr={result['rr_ratio']}")
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