import numpy as np
from agent.strategy.base import BaseStrategy
from agent.regime import detect_regime
from agent.strategy.risk import compute_risk
from agent.features import fetch_ohlcv, INTERVAL
from agent.reputation import get_reputation_score
from agent.ai_advisor import ai_trade_review
from config import STRUCTURE_LOOKBACK, ARC_FISHER_PERIOD
from logger import get_logger

logger = get_logger(__name__)

TRADEABLE_REGIMES = {"trending", "trending_volatile"}

# For reversal confirmation we look back further to verify
# the extreme is genuine and not just noise
REVERSAL_LOOKBACK = 100


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
    # Fetch enough candles for both trend (ARC_FISHER_PERIOD)
    # and reversal confirmation (REVERSAL_LOOKBACK)
    fetch_count = max(ARC_FISHER_PERIOD, REVERSAL_LOOKBACK) + 10
    df = await fetch_ohlcv(symbol, INTERVAL, fetch_count)
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

    # For reversal confirmation: check how extreme this Fisher reading is
    # relative to the last REVERSAL_LOOKBACK candles.
    # If Fisher < -1.5 AND it is at or near the lowest Fisher reading
    # over the lookback, the oversold condition is genuine.
    # Same for overbought.
    fisher_window  = fisher.iloc[-REVERSAL_LOOKBACK:]
    fisher_min     = float(fisher_window.min())
    fisher_max     = float(fisher_window.max())

    # Reversal is confirmed if current Fisher is within 10% of the
    # historical extreme over the lookback window
    reversal_long  = last < -1.5 and last <= fisher_min * 0.9
    reversal_short = last > +1.5 and last >= fisher_max * 0.9

    # Trend following: Fisher just needs to agree with direction
    trend_long  = last < 0
    trend_short = last > 0

    if reversal_long:
        signal = (
            f"OVERSOLD REVERSAL confirmed — Fisher={last:.4f} at/near "
            f"{REVERSAL_LOOKBACK}-candle low of {fisher_min:.4f}"
        )
    elif reversal_short:
        signal = (
            f"OVERBOUGHT REVERSAL confirmed — Fisher={last:.4f} at/near "
            f"{REVERSAL_LOOKBACK}-candle high of {fisher_max:.4f}"
        )
    elif trend_long:
        signal = f"negative ({last:.4f}) — trend-following LONG signal"
    elif trend_short:
        signal = f"positive ({last:.4f}) — trend-following SHORT signal"
    else:
        signal = "neutral"

    note = (
        f"Fisher={last:.4f} ({signal}) | "
        f"{REVERSAL_LOOKBACK}-candle range [{fisher_min:.4f} to {fisher_max:.4f}]"
    )

    return {
        "fisher":         round(last, 4),
        "fisher_min":     round(fisher_min, 4),
        "fisher_max":     round(fisher_max, 4),
        "trend_long":     trend_long,
        "trend_short":    trend_short,
        "reversal_long":  reversal_long,
        "reversal_short": reversal_short,
        "note":           note,
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
                    "pure volatile regime — order flow is chaotic, "
                    "no trend anchor, ARC strategy has no edge here"
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

        ma     = await _ma_confirmation(symbol)
        fisher = await _fisher_confirmation(symbol)

        if ma["above"] is None or fisher["fisher"] is None:
            return self.skip(
                symbol,
                f"SKIP {symbol}: {regime_summary} — indicator data unavailable: {ma['note']} | {fisher['note']}",
                confidence=confidence, post_on_chain=True,
            )

        action     = None
        direction  = None
        entry_type = None

        # --- REVERSAL entries (regime gate lifted) ---
        # Fisher at multi-candle extreme overrides regime direction.
        # Checked first because it is a stronger signal.
        if fisher["reversal_long"] and not ma["above"]:
            action, direction, entry_type = "LONG", "long", "reversal"

        elif fisher["reversal_short"] and ma["above"]:
            action, direction, entry_type = "SHORT", "short", "reversal"

        # --- TREND FOLLOWING entries (regime gates direction) ---
        elif trend_direction == "bullish" and ma["above"] and fisher["trend_long"]:
            action, direction, entry_type = "LONG", "long", "trend"

        elif trend_direction == "bearish" and not ma["above"] and fisher["trend_short"]:
            action, direction, entry_type = "SHORT", "short", "trend"

        if action is None:
            return self.skip(
                symbol,
                (
                    f"SKIP {symbol}: {regime_summary} — no valid entry. "
                    f"{ma['note']} | {fisher['note']}"
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

        # --- AI TRADE REVIEW ---
        # All rule-based gates passed. Ask OpenAI for a second opinion.
        # A veto skips the trade but does NOT post on-chain (no gas wasted).
        # If AI is unavailable, defaults to approve=True with adj=0.0 and
        # a clear error message so the explanation is never misleadingly empty.
        ai_review = await ai_trade_review(
            symbol=symbol,
            action=action,
            entry_type=entry_type,
            regime=regime,
            ma=ma,
            fisher=fisher,
            structure=structure,
            params=params,
            reputation=reputation,
        )

        if not ai_review["approve"]:
            return self.skip(
                symbol,
                (
                    f"SKIP {symbol}: {regime_summary} | action={action} entry_type={entry_type} "
                    f"— AI review vetoed: {ai_review['reason']}"
                ),
                confidence=confidence, post_on_chain=False,
            )

        # Original explanation preserved exactly — AI appended cleanly at the end
        explanation = (
            f"TRADE {symbol} {action} ({entry_type}): {regime_summary} | "
            f"reputation={reputation:.4f} | "
            f"{params['explanation']} | "
            f"leverage={params['leverage']}x risk={params['risk_pct']:.4f} rr={params['rr_ratio']} "
            f"amount=${params['amount_usd']} | "
            f"{structure['note']} | "
            f"{ma['note']} | "
            f"{fisher['note']} | "
            f"ai=approved adj={ai_review['confidence_adjustment']:+.2f} — {ai_review['reason']}"
        )

        return {
            "symbol":      symbol,
            "action":      action,
            "entry_type":  entry_type,
            "leverage":    params["leverage"],
            "risk_pct":    params["risk_pct"],
            "rr_ratio":    params["rr_ratio"],
            "amount_usd":  params["amount_usd"],
            "explanation": explanation,
            "regime":      regime,
            "structure":   structure,
            "reputation":  reputation,
            "ai_review":   ai_review,
            "ready":       True,
        }