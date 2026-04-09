import numpy as np
from agent.strategy.base import BaseStrategy
from agent.regime import detect_regime
from agent.strategy.risk import compute_risk
from agent.features import fetch_ohlcv, INTERVAL
from agent.reputation import get_reputation_score
from config import STRUCTURE_LOOKBACK, ARC_FISHER_PERIOD
from logger import get_logger

logger = get_logger(__name__)

TRADEABLE_REGIMES = {"trending", "trending_volatile"}


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

    if direction == "long":
        threshold_price = low + rng * 0.6
        note = (
            f"LONG structure: price=${current:.4f} at {position:.0%} of swing range "
            f"[low=${low:.4f} to high=${high:.4f}]. "
            f"Required: price <= ${threshold_price:.4f} (60% of range). "
            f"Result: {'PASS' if valid else f'FAIL — price ${current:.4f} is above entry ceiling ${threshold_price:.4f}'}"
        )
    else:
        threshold_price = low + rng * 0.4
        note = (
            f"SHORT structure: price=${current:.4f} at {position:.0%} of swing range "
            f"[low=${low:.4f} to high=${high:.4f}]. "
            f"Required: price >= ${threshold_price:.4f} (40% of range). "
            f"Result: {'PASS' if valid else f'FAIL — price ${current:.4f} is below entry floor ${threshold_price:.4f}'}"
        )

    return {
        "valid":    valid,
        "price":    current,
        "high":     high,
        "low":      low,
        "position": round(position, 4),
        "note":     note,
    }


async def _ma_confirmation(symbol: str) -> dict:
    df = await fetch_ohlcv(symbol, INTERVAL, 30)
    if df is None or len(df) < 21:
        return {"above": None, "ma": None, "price": None, "note": "MA skipped — not enough candles"}

    typical = (df["high"] + df["low"] + df["close"]) / 3
    ma      = float(typical.ewm(span=20, adjust=False).mean().iloc[-1])
    current = float(df["close"].iloc[-1])
    above   = current > ma
    diff    = abs(current - ma)
    pct     = (diff / ma) * 100

    note = (
        f"EMA20(typical)=${ma:.4f} | current price=${current:.4f} | "
        f"price is {'ABOVE' if above else 'BELOW'} EMA by ${diff:.4f} ({pct:.2f}%) | "
        f"LONG requires price > EMA, SHORT requires price < EMA"
    )

    return {
        "above": above,
        "ma":    round(ma, 4),
        "price": round(current, 4),
        "note":  note,
    }


async def _fisher_confirmation(symbol: str) -> dict:
    df = await fetch_ohlcv(symbol, INTERVAL, ARC_FISHER_PERIOD + 10)
    if df is None or len(df) < ARC_FISHER_PERIOD:
        return {"fisher": None, "note": "Fisher skipped — not enough candles"}

    period = ARC_FISHER_PERIOD
    high   = df["high"].rolling(period).max()
    low    = df["low"].rolling(period).min()
    rng    = high - low
    value  = 2 * ((df["close"] - low) / (rng + 1e-9)) - 1
    value  = value.clip(-0.999, 0.999)
    fisher = 0.5 * np.log((1 + value) / (1 - value))
    last   = float(fisher.iloc[-1])

    # Trend following signal
    trend_long  = last < 0    # negative = moving down = pullback in uptrend
    trend_short = last > 0    # positive = moving up = bounce in downtrend

    # Pullback/reversal signal (stronger confirmation)
    reversal_long  = last < -1.5
    reversal_short = last > +1.5

    if reversal_long:
        signal = "OVERSOLD REVERSAL — strong LONG signal"
    elif reversal_short:
        signal = "OVERBOUGHT REVERSAL — strong SHORT signal"
    elif trend_long:
        signal = "negative — trend-following LONG signal"
    elif trend_short:
        signal = "positive — trend-following SHORT signal"
    else:
        signal = "neutral"

    note = f"Fisher={last:.4f} ({signal})"

    return {
        "fisher":          round(last, 4),
        "trend_long":      trend_long,
        "trend_short":     trend_short,
        "reversal_long":   reversal_long,
        "reversal_short":  reversal_short,
        "note":            note,
    }


class ARCStrategy(BaseStrategy):

    async def analyze(self, symbol: str) -> dict:
        reputation = await get_reputation_score()
        regime     = await detect_regime(symbol, reputation=reputation)

        if not regime["ready"]:
            return self.skip(
                symbol,
                f"SKIP {symbol}: regime scorer returned no result — insufficient candle history to classify market",
                confidence=0.0, post_on_chain=False,
            )

        current_regime     = regime["regime"]
        confidence         = regime["confidence"]
        p_trending         = regime["p_trending"]
        p_ranging          = regime["p_ranging"]
        p_volatile         = regime["p_volatile"]
        trend_direction    = regime["trend_direction"]
        direction_strength = regime["direction_strength"]

        regime_summary = (
            f"regime={current_regime} confidence={confidence:.4f} "
            f"[p_trending={p_trending:.4f} p_ranging={p_ranging:.4f} p_volatile={p_volatile:.4f}] "
            f"trend_direction={trend_direction}({direction_strength:+.4f})"
        )

        if current_regime not in TRADEABLE_REGIMES:
            reason = {
                "ranging":  "market is ranging — no directional edge",
                "volatile": (
                    f"pure volatile regime — order flow is chaotic, "
                    f"no trend anchor, ARC strategy has no edge here"
                ),
            }.get(current_regime, f"regime '{current_regime}' is not tradeable")

            return self.skip(
                symbol,
                f"SKIP {symbol}: {regime_summary} — {reason}",
                confidence=confidence, post_on_chain=True,
            )

        params = await compute_risk(regime, reputation=reputation)

        if params["action"] == "SKIP":
            return self.skip(
                symbol,
                f"SKIP {symbol}: {regime_summary} — risk check blocked trade: {params['explanation']}",
                confidence=confidence, post_on_chain=True,
            )

        if trend_direction == "bullish":
            allowed_actions = {"LONG"}
        elif trend_direction == "bearish":
            allowed_actions = {"SHORT"}
        else:
            allowed_actions = {"LONG", "SHORT"}

        ma     = await _ma_confirmation(symbol)
        fisher = await _fisher_confirmation(symbol)

        if ma["above"] is None or fisher["fisher"] is None:
            return self.skip(
                symbol,
                f"SKIP {symbol}: {regime_summary} — indicator data unavailable: {ma['note']} | {fisher['note']}",
                confidence=confidence, post_on_chain=True,
            )

        # Determine entry type:
        # Reversal (stronger): Fisher extreme + price on correct side of EMA
        # Trend following: Fisher agrees with direction + price on correct side of EMA
        action    = None
        direction = None
        entry_type = None

        if "LONG" in allowed_actions and ma["above"]:
            if fisher["reversal_long"]:
                action, direction, entry_type = "LONG", "long", "reversal"
            elif fisher["trend_long"]:
                action, direction, entry_type = "LONG", "long", "trend"

        elif "SHORT" in allowed_actions and not ma["above"]:
            if fisher["reversal_short"]:
                action, direction, entry_type = "SHORT", "short", "reversal"
            elif fisher["trend_short"]:
                action, direction, entry_type = "SHORT", "short", "trend"

        if action is None:
            long_blocked  = []
            short_blocked = []

            if "LONG" not in allowed_actions:
                long_blocked.append(f"regime trend is {trend_direction} — LONG not allowed")
            else:
                if not ma["above"]:
                    long_blocked.append(f"price ${ma['price']:.4f} is below EMA20 ${ma['ma']:.4f}")
                if not fisher["trend_long"]:
                    long_blocked.append(f"Fisher={fisher['fisher']:.4f} is positive — not pointing down for pullback")

            if "SHORT" not in allowed_actions:
                short_blocked.append(f"regime trend is {trend_direction} — SHORT not allowed")
            else:
                if ma["above"]:
                    short_blocked.append(f"price ${ma['price']:.4f} is above EMA20 ${ma['ma']:.4f}")
                if not fisher["trend_short"]:
                    short_blocked.append(f"Fisher={fisher['fisher']:.4f} is negative — not pointing up for bounce")

            return self.skip(
                symbol,
                (
                    f"SKIP {symbol}: {regime_summary} — no valid entry. "
                    f"LONG blocked: {'; '.join(long_blocked)}. "
                    f"SHORT blocked: {'; '.join(short_blocked)}."
                ),
                confidence=confidence, post_on_chain=True,
            )

        structure = await _price_structure(symbol, direction)
        if not structure["valid"]:
            return self.skip(
                symbol,
                (
                    f"SKIP {symbol}: {regime_summary} | action={action} entry_type={entry_type} "
                    f"blocked by structure: {structure['note']}"
                ),
                confidence=confidence, post_on_chain=True,
            )

        explanation = (
            f"TRADE {symbol} {action} ({entry_type}): {regime_summary} | "
            f"reputation={reputation:.4f} | "
            f"{params['explanation']} | "
            f"leverage={params['leverage']}x risk={params['risk_pct']:.4f} rr={params['rr_ratio']} "
            f"amount=${params['amount_usd']} | "
            f"{structure['note']} | "
            f"{ma['note']} | "
            f"{fisher['note']}"
        )

        return {
            "symbol":      symbol,
            "action":      action,
            "entry_type":  entry_type,
            "leverage":    params["leverage"],
            "risk_pct":    params["risk_pct"],
            "rr_ratio":    params["rr_ratio"],
            "explanation": explanation,
            "regime":      regime,
            "structure":   structure,
            "reputation":  reputation,
            "ready":       True,
        }