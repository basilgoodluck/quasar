import numpy as np
from agent.strategy.base import BaseStrategy
from agent.regime import detect_regime
from agent.openai_client import get_trade_params
from agent.features import _fetch_ohlcv, INTERVAL
from agent.reputation import get_reputation_score
from config import STRUCTURE_LOOKBACK, ARC_FISHER_PERIOD
from logger import get_logger

logger = get_logger(__name__)

# Regimes where ARC will look for trades
TRADEABLE_REGIMES = {"trending", "trending_volatile"}

# Volatile alone — allow trade only if confidence is very high
VOLATILE_MIN_CONFIDENCE = float(0.65)


def _price_structure(symbol: str, direction: str) -> dict:
    df = _fetch_ohlcv(symbol, INTERVAL, STRUCTURE_LOOKBACK + 5)
    if df is None or len(df) < STRUCTURE_LOOKBACK:
        return {"valid": False, "note": "insufficient data"}

    recent  = df.tail(STRUCTURE_LOOKBACK)
    current = float(df["close"].iloc[-1])
    high    = float(recent["high"].max())
    low     = float(recent["low"].min())
    rng     = high - low

    if rng == 0:
        return {"valid": False, "note": "zero range"}

    position = (current - low) / rng
    valid    = position <= 0.6 if direction == "long" else position >= 0.4

    return {
        "valid":    valid,
        "price":    current,
        "high":     high,
        "low":      low,
        "position": round(position, 4),
        "note":     f"price at {position:.0%} of range swing_low={low:.4f} swing_high={high:.4f}",
    }


def _ma_confirmation(symbol: str, direction: str) -> dict:
    df = _fetch_ohlcv(symbol, INTERVAL, 30)
    if df is None or len(df) < 21:
        return {"confirmed": True, "note": "skipped"}

    ma        = float(df["close"].rolling(20).mean().iloc[-1])
    current   = float(df["close"].iloc[-1])
    above     = current > ma
    confirmed = (direction == "long" and above) or (direction == "short" and not above)

    return {
        "confirmed": confirmed,
        "ma":        round(ma, 4),
        "note":      f"price {'above' if above else 'below'} 20MA={ma:.4f}",
    }


def _fisher_confirmation(symbol: str, direction: str) -> dict:
    df = _fetch_ohlcv(symbol, INTERVAL, ARC_FISHER_PERIOD + 10)
    if df is None or len(df) < ARC_FISHER_PERIOD:
        return {"confirmed": True, "note": "skipped"}

    period = ARC_FISHER_PERIOD
    high   = df["high"].rolling(period).max()
    low    = df["low"].rolling(period).min()
    rng    = high - low
    value  = 2 * ((df["close"] - low) / (rng + 1e-9)) - 1
    value  = value.clip(-0.999, 0.999)
    fisher = 0.5 * np.log((1 + value) / (1 - value))
    last   = float(fisher.iloc[-1])

    confirmed = last < -1.5 if direction == "long" else last > 1.5

    return {
        "confirmed": confirmed,
        "fisher":    round(last, 4),
        "note":      f"fisher={last:.4f} {'confirms' if confirmed else 'no signal'} {direction}",
    }


class ARCStrategy(BaseStrategy):

    def analyze(self, symbol: str) -> dict:
        reputation = get_reputation_score()
        regime     = detect_regime(symbol, reputation=reputation)

        if not regime["ready"]:
            return self.skip(
                symbol, "regime model not ready — insufficient data",
                confidence=0.0, post_on_chain=False,
            )

        current_regime = regime["regime"]
        confidence     = regime["confidence"]

        # Ranging — always skip, market is choppy
        if current_regime == "ranging":
            return self.skip(
                symbol, "regime=ranging — choppy market, no edge",
                confidence=confidence, post_on_chain=True,
            )

        # Volatile only (no trend) — skip unless confidence is very high
        if current_regime == "volatile" and confidence < VOLATILE_MIN_CONFIDENCE:
            return self.skip(
                symbol,
                f"regime=volatile confidence={confidence} below threshold={VOLATILE_MIN_CONFIDENCE} — too uncertain",
                confidence=confidence, post_on_chain=True,
            )

        # At this point regime is trending, trending_volatile, or high-confidence volatile
        # Now use OpenAI to determine direction (long/short) and sizing
        params = get_trade_params(regime, reputation=reputation)

        if params["action"] == "SKIP":
            return self.skip(
                symbol, params["explanation"],
                confidence=confidence, post_on_chain=True,
            )

        direction = params["action"].lower()  # "long" or "short"

        # Price structure check
        structure = _price_structure(symbol, direction)
        if not structure["valid"]:
            return self.skip(
                symbol, f"structure invalid: {structure['note']}",
                confidence=confidence, post_on_chain=True,
            )

        # MA and Fisher as informational filters — log but don't hard block
        ma     = _ma_confirmation(symbol, direction)
        fisher = _fisher_confirmation(symbol, direction)

        if not ma["confirmed"]:
            logger.info(f"[{symbol}] MA does not confirm {direction}: {ma['note']}")

        if not fisher["confirmed"]:
            logger.info(f"[{symbol}] Fisher does not confirm {direction}: {fisher['note']}")

        return {
            "symbol":      symbol,
            "action":      params["action"],
            "leverage":    params["leverage"],
            "risk_pct":    params["risk_pct"],
            "rr_ratio":    params["rr_ratio"],
            "explanation": (
                f"regime={current_regime} confidence={confidence} | "
                f"{params['explanation']} | {structure['note']} | "
                f"{ma['note']} | {fisher['note']} | reputation={reputation:.4f}"
            ),
            "regime":     regime,
            "structure":  structure,
            "reputation": reputation,
            "ready":      True,
        }