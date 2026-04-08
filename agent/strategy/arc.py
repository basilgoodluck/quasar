import numpy as np
from agent.strategy.base import BaseStrategy
from agent.regime import detect_regime
from agent.strategy.risk import compute_risk
from agent.features import fetch_ohlcv, INTERVAL
from agent.reputation import get_reputation_score
from config import STRUCTURE_LOOKBACK, ARC_FISHER_PERIOD
from logger import get_logger

logger = get_logger(__name__)

VOLATILE_MIN_CONFIDENCE = float(0.65)


async def _price_structure(symbol: str, direction: str) -> dict:
    df = await fetch_ohlcv(symbol, INTERVAL, STRUCTURE_LOOKBACK + 5)
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


async def _ma_confirmation(symbol: str) -> dict:
    df = await fetch_ohlcv(symbol, INTERVAL, 30)
    if df is None or len(df) < 21:
        return {"above": None, "ma": None, "note": "skipped"}

    ma      = float(df["close"].rolling(20).mean().iloc[-1])
    current = float(df["close"].iloc[-1])
    above   = current > ma

    return {
        "above": above,
        "ma":    round(ma, 4),
        "note":  f"price {'above' if above else 'below'} 20MA={ma:.4f}",
    }


async def _fisher_confirmation(symbol: str) -> dict:
    df = await fetch_ohlcv(symbol, INTERVAL, ARC_FISHER_PERIOD + 10)
    if df is None or len(df) < ARC_FISHER_PERIOD:
        return {"fisher": None, "note": "skipped"}

    period = ARC_FISHER_PERIOD
    high   = df["high"].rolling(period).max()
    low    = df["low"].rolling(period).min()
    rng    = high - low
    value  = 2 * ((df["close"] - low) / (rng + 1e-9)) - 1
    value  = value.clip(-0.999, 0.999)
    fisher = 0.5 * np.log((1 + value) / (1 - value))
    last   = float(fisher.iloc[-1])

    return {
        "fisher": round(last, 4),
        "note":   f"fisher={last:.4f}",
    }


class ARCStrategy(BaseStrategy):

    async def analyze(self, symbol: str) -> dict:
        reputation = await get_reputation_score()
        regime     = await detect_regime(symbol, reputation=reputation)

        if not regime["ready"]:
            return self.skip(
                symbol, "regime not ready — insufficient data",
                confidence=0.0, post_on_chain=False,
            )

        current_regime = regime["regime"]
        confidence     = regime["confidence"]

        if current_regime == "ranging":
            return self.skip(
                symbol, "regime=ranging — choppy market, no edge",
                confidence=confidence, post_on_chain=True,
            )

        if current_regime == "volatile" and confidence < VOLATILE_MIN_CONFIDENCE:
            return self.skip(
                symbol,
                f"regime=volatile confidence={confidence} below threshold={VOLATILE_MIN_CONFIDENCE}",
                confidence=confidence, post_on_chain=True,
            )

        params = await compute_risk(regime, reputation=reputation)

        if params["action"] == "SKIP":
            return self.skip(
                symbol, params["explanation"],
                confidence=confidence, post_on_chain=True,
            )

        ma     = await _ma_confirmation(symbol)
        fisher = await _fisher_confirmation(symbol)

        if ma["above"] is None or fisher["fisher"] is None:
            return self.skip(
                symbol, "MA or Fisher insufficient data",
                confidence=confidence, post_on_chain=True,
            )

        if ma["above"] and fisher["fisher"] < -1.5:
            direction = "long"
            action    = "LONG"
        elif not ma["above"] and fisher["fisher"] > 1.5:
            direction = "short"
            action    = "SHORT"
        else:
            return self.skip(
                symbol,
                f"no clear direction — {ma['note']} | {fisher['note']}",
                confidence=confidence, post_on_chain=True,
            )

        structure = await _price_structure(symbol, direction)
        if not structure["valid"]:
            return self.skip(
                symbol, f"structure invalid: {structure['note']}",
                confidence=confidence, post_on_chain=True,
            )

        return {
            "symbol":      symbol,
            "action":      action,
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