import os
import torch
from agent.features import build_live_sequence, INTERVAL, WINDOW
from agent.model import load_model
from config import REPUTATION_CONFIDENCE_BOOST
from logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "models/regime_lstm.pt")
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"

# Confidence thresholds — how certain the model must be to declare a regime
TRENDING_THRESHOLD = float(os.getenv("TRENDING_THRESHOLD", "0.45"))
VOLATILE_THRESHOLD = float(os.getenv("VOLATILE_THRESHOLD", "0.40"))

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
        logger.warning(f"[{symbol}] not enough data for regime inference")
        return {
            "symbol":      symbol,
            "p_trending":  0.0,
            "p_ranging":   1.0,
            "p_volatile":  0.0,
            "regime":      "ranging",
            "confidence":  0.0,
            "ready":       False,
        }

    input_size = seq.shape[2]
    model      = _get_model(input_size)

    with torch.no_grad():
        x     = torch.tensor(seq).to(DEVICE)
        probs = model(x).squeeze(0).cpu().tolist()  # [p_trending, p_ranging, p_volatile]

    p_trending, p_ranging, p_volatile = probs

    # Reputation boosts confidence threshold slightly — higher rep = easier to trigger a trade
    boost              = reputation * REPUTATION_CONFIDENCE_BOOST
    trending_threshold = max(0.35, TRENDING_THRESHOLD - boost)
    volatile_threshold = max(0.30, VOLATILE_THRESHOLD - boost)

    # Determine regime
    if p_trending >= trending_threshold and p_trending >= p_ranging:
        if p_volatile >= volatile_threshold:
            regime     = "trending_volatile"  # best condition — strong move with energy
        else:
            regime     = "trending"            # clean trend
        confidence = round(p_trending, 4)

    elif p_volatile >= volatile_threshold and p_trending < trending_threshold:
        regime     = "volatile"               # explosive but no clear direction — caution
        confidence = round(p_volatile, 4)

    else:
        regime     = "ranging"                # choppy, stay out
        confidence = round(p_ranging, 4)

    logger.info(
        f"[{symbol}] p_trending={p_trending:.4f} p_ranging={p_ranging:.4f} "
        f"p_volatile={p_volatile:.4f} regime={regime} confidence={confidence} reputation={reputation:.4f}"
    )

    return {
        "symbol":     symbol,
        "p_trending": round(p_trending, 4),
        "p_ranging":  round(p_ranging, 4),
        "p_volatile": round(p_volatile, 4),
        "regime":     regime,
        "confidence": confidence,
        "ready":      True,
    }