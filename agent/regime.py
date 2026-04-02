import os
import torch
from agent.features import build_live_sequence
from contracts.model import load_model
from logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "models/regime_lstm.pt")
INTERVAL   = os.getenv("TRAIN_INTERVAL", "15m")
WINDOW     = int(os.getenv("TRAIN_WINDOW", "96"))
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"

_model = None
_input_size = None


def _get_model(input_size):
    global _model, _input_size
    if _model is None or _input_size != input_size:
        _model = load_model(MODEL_PATH, input_size=input_size, device=DEVICE)
        _input_size = input_size
    return _model


def detect_regime(symbol: str) -> dict:
    seq = build_live_sequence(symbol, interval=INTERVAL, window=WINDOW)

    if seq is None:
        logger.warning(f"[{symbol}] not enough data for inference")
        return {
            "symbol":     symbol,
            "confidence": 0.0,
            "ready":      False,
        }

    input_size = seq.shape[2]
    model = _get_model(input_size)

    with torch.no_grad():
        x = torch.tensor(seq).to(DEVICE)
        confidence = float(model(x).item())

    logger.info(f"[{symbol}] confidence={confidence:.4f}")

    return {
        "symbol":     symbol,
        "confidence": round(confidence, 4),
        "ready":      True,
    }