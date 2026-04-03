import os
import torch
from agent.features import build_live_sequence
from contracts.model import load_model
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
        x          = torch.tensor(seq).to(DEVICE)
        confidence = float(model(x).item())

    adjustment      = reputation * REPUTATION_CONFIDENCE_BOOST
    long_threshold  = max(0.50, REGIME_BULL_THRESHOLD - adjustment)
    short_threshold = min(0.50, REGIME_BEAR_THRESHOLD + adjustment)

    if confidence >= long_threshold:
        direction = "long"
    elif confidence <= short_threshold:
        direction = "short"
    else:
        direction = "neutral"

    deviation         = abs(confidence - 0.5) * 2
    volatility_regime = "high" if deviation > 0.6 else "low"
    activity_score    = round(deviation, 4)
    trend_strength    = round(deviation, 4)

    logger.info(
        f"[{symbol}] confidence={confidence:.4f} direction={direction} "
        f"reputation={reputation:.4f} thresholds=({short_threshold:.2f},{long_threshold:.2f})"
    )

    return {
        "symbol":            symbol,
        "confidence":        round(confidence, 4),
        "direction":         direction,
        "volatility_regime": volatility_regime,
        "activity_score":    activity_score,
        "trend_strength":    trend_strength,
        "ready":             True,
    }