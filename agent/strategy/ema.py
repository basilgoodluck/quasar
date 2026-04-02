import pandas as pd
from agent.logger import get_logger

logger = get_logger(__name__)

FAST = 9
SLOW = 21


def generate_signal(ohlcv: list, regime: str, prism_signal: dict) -> dict:
    if regime == "volatile":
        return {"signal": "hold", "confidence": 0.0}

    df = pd.DataFrame(ohlcv)
    df["close"] = df["close"].astype(float)
    df["ema_fast"] = df["close"].ewm(span=FAST).mean()
    df["ema_slow"] = df["close"].ewm(span=SLOW).mean()

    pf, ps = df["ema_fast"].iloc[-2], df["ema_slow"].iloc[-2]
    cf, cs = df["ema_fast"].iloc[-1], df["ema_slow"].iloc[-1]

    ema_confidence = round(min(abs(cf - cs) / cs * 100, 1.0), 4)
    prism_action = prism_signal.get("action") if prism_signal else None
    prism_confidence = float(prism_signal.get("confidence", 0)) if prism_signal else 0

    if pf < ps and cf > cs:
        signal = "buy"
    elif pf > ps and cf < cs:
        signal = "sell"
    else:
        signal = "hold"

    if prism_action and prism_action != signal and prism_confidence > 0.7:
        signal = prism_action

    confidence = round((ema_confidence + prism_confidence) / 2, 4)
    logger.info(f"Signal: {signal} | Confidence: {confidence}")

    return {"signal": signal, "confidence": confidence}