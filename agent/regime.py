import os
import torch
from agent.features import build_live_sequence
from agent.model import load_model
from config import (
    REGIME_BULL_THRESHOLD,
    REGIME_BEAR_THRESHOLD,
    REPUTATION_CONFIDENCE_BOOST,
)
from logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "models/regime_lstm.pt")
INTERVAL   = os.getenv("TRAIN_INTERVAL", "15m")
WINDOW     = int(os.getenv("TRAIN_WINDOW", "96"))
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"

_model      = None
_input_size = None

def _get_model(input_size):
    global _model, _input_size
    if _model is None or _input_size != input_size:
        _model      = load_model(MODEL_PATH, input_size=input_size, device=DEVICE)
        _input_size = input_size
    return _model


def detect_regime(symbol: str, reputation: float = 0.0) -> dict:
    seq = build_live_sequence(symbol, interval=INTERVAL, window=WINDOW)

    if seq is None:
        logger.warning(f"[{symbol}] not enough data for inference")
        return {
            "symbol":            symbol,
            "p_long":            0.0,
            "p_short":           0.0,
            "p_neutral":         1.0,
            "confidence":        0.0,
            "direction":         "neutral",
            "volatility_regime": "low",
            "activity_score":    0.0,
            "trend_strength":    0.0,
            "ready":             False,
        }

    input_size = seq.shape[2]
    model      = _get_model(input_size)

    with torch.no_grad():
        x     = torch.tensor(seq).to(DEVICE)
        probs = model(x).squeeze(0).cpu().tolist()  # [p_long, p_short, p_neutral]

    p_long, p_short, p_neutral = probs

    adjustment     = reputation * REPUTATION_CONFIDENCE_BOOST
    long_threshold = max(0.40, REGIME_BULL_THRESHOLD - adjustment)
    short_threshold = max(0.40, REGIME_BEAR_THRESHOLD - adjustment)

    if p_long >= long_threshold and p_long > p_short:
        direction  = "long"
        confidence = round(p_long, 4)
    elif p_short >= short_threshold and p_short > p_long:
        direction  = "short"
        confidence = round(p_short, 4)
    else:
        direction  = "neutral"
        confidence = round(p_neutral, 4)

    activity_score    = round(1.0 - p_neutral, 4)
    volatility_regime = "high" if activity_score > 0.6 else "low"
    trend_strength    = round(abs(p_long - p_short), 4)

    logger.info(
        f"[{symbol}] p_long={p_long:.4f} p_short={p_short:.4f} p_neutral={p_neutral:.4f} "
        f"direction={direction} reputation={reputation:.4f}"
    )

    return {
        "symbol":            symbol,
        "p_long":            round(p_long, 4),
        "p_short":           round(p_short, 4),
        "p_neutral":         round(p_neutral, 4),
        "confidence":        confidence,
        "direction":         direction,
        "volatility_regime": volatility_regime,
        "activity_score":    activity_score,
        "trend_strength":    trend_strength,
        "ready":             True,
    }