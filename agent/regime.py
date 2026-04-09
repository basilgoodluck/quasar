import os
import numpy as np
from agent.features import build_live_sequence, INTERVAL, WINDOW
from config import REPUTATION_CONFIDENCE_BOOST
from logger import get_logger

logger = get_logger(__name__)

TRENDING_THRESHOLD = float(os.getenv("TRENDING_THRESHOLD", "0.45"))
VOLATILE_THRESHOLD = float(os.getenv("VOLATILE_THRESHOLD", "0.40"))


def _score_window(seq: np.ndarray) -> tuple[float, float, float, str, float]:
    arr = seq[0]

    log_return      = arr[:, 0]
    hl_range        = arr[:, 1]
    vol_ratio       = arr[:, 2]
    buy_ratio       = arr[:, 3]
    realized_vol    = arr[:, 4]
    cvd_norm        = arr[:, 5]
    delta_norm      = arr[:, 6]
    cvd_accel       = arr[:, 7]
    funding         = arr[:, 8]
    oi_change       = arr[:, 9]
    long_liq_ratio  = arr[:, 10]
    short_liq_ratio = arr[:, 11]
    large_trade     = arr[:, 12]
    buy_aggression  = arr[:, 13]

    n = len(arr)
    x = np.arange(n)

    def slope(series):
        return float(np.polyfit(x, series, 1)[0])

    def consistency(series):
        s = slope(series)
        if abs(s) < 1e-9:
            return 0.0
        residuals = series - (s * x + np.mean(series))
        return float(1.0 - np.clip(np.std(residuals) / (np.std(series) + 1e-9), 0, 1))

    cvd_slope       = slope(cvd_norm)
    cvd_consistency = consistency(cvd_norm)
    oi_slope        = slope(oi_change)
    agg_slope       = slope(buy_aggression)
    ret_slope       = slope(log_return)
    avg_vol         = float(np.mean(realized_vol))
    avg_hl          = float(np.mean(hl_range))
    liq_imbalance   = float(np.mean(np.abs(long_liq_ratio - short_liq_ratio)))
    cvd_flip        = float(np.mean(np.abs(np.diff(np.sign(cvd_norm)))))

    avg_vol_ratio = float(np.mean(vol_ratio))
    avg_buy_ratio = float(np.mean(buy_ratio))
    avg_delta     = float(np.mean(np.abs(delta_norm)))
    avg_accel     = float(np.mean(np.abs(cvd_accel)))
    avg_funding   = float(np.mean(np.abs(funding)))
    avg_large     = float(np.mean(large_trade))

    trending_score = (
        abs(cvd_slope)    * 3.0 +
        cvd_consistency   * 3.0 +
        abs(oi_slope)     * 2.0 +
        abs(agg_slope)    * 2.0 +
        abs(ret_slope)    * 2.0 +
        liq_imbalance     * 1.5 +
        avg_buy_ratio     * 1.5 +
        avg_large         * 1.5 +
        avg_delta         * 1.5 +
        avg_accel         * 1.0
    )

    volatile_score = (
        avg_vol               * 2.5 +
        avg_hl                * 2.0 +
        cvd_flip              * 1.5 +
        (1.0 - liq_imbalance) * 1.0 +
        avg_vol_ratio         * 1.0 +
        avg_funding           * 0.5
    )

    ranging_score = (
        (1.0 - abs(cvd_slope))  * 1.0 +
        (1.0 - abs(ret_slope))  * 1.0 +
        (1.0 - avg_vol)         * 0.5 +
        (1.0 - abs(oi_slope))   * 0.5 +
        (1.0 - avg_vol_ratio)   * 0.5 +
        (1.0 - avg_large)       * 0.5
    )

    total      = trending_score + volatile_score + ranging_score + 1e-9
    p_trending = trending_score / total
    p_volatile = volatile_score / total
    p_ranging  = ranging_score  / total

    # --- Trend direction ---
    # Weighted vote from four signed slope signals.
    # Each signal contributes its sign weighted by its magnitude.
    # cvd_slope is most reliable (order flow), ret_slope is price confirmation,
    # agg_slope is aggression confirmation, oi_slope is positioning.
    direction_score = (
        cvd_slope * 3.0 +
        ret_slope * 2.0 +
        agg_slope * 2.0 +
        oi_slope  * 1.0
    )

    # Also factor in avg buy_ratio: >0.5 = more buying, <0.5 = more selling
    direction_score += (avg_buy_ratio - 0.5) * 2.0

    # Normalise to [-1, 1] for readability
    max_possible = 3.0 + 2.0 + 2.0 + 1.0 + 1.0  # rough upper bound per unit slope
    direction_strength = float(np.clip(direction_score / (abs(direction_score) + 1e-9), -1, 1))

    trend_direction = "bullish" if direction_score > 0 else "bearish"

    return (
        round(float(p_trending), 4),
        round(float(p_ranging),  4),
        round(float(p_volatile), 4),
        trend_direction,
        round(direction_strength, 4),
    )


async def detect_regime(symbol: str, reputation: float = 0.0) -> dict:
    seq = await build_live_sequence(symbol, interval=INTERVAL, window=WINDOW)

    if seq is None:
        logger.warning(f"[{symbol}] not enough data for regime inference")
        return {
            "symbol":           symbol,
            "p_trending":       0.0,
            "p_ranging":        1.0,
            "p_volatile":       0.0,
            "regime":           "ranging",
            "confidence":       0.0,
            "trend_direction":  "unknown",
            "direction_strength": 0.0,
            "ready":            False,
        }

    p_trending, p_ranging, p_volatile, trend_direction, direction_strength = _score_window(seq)

    boost              = reputation * REPUTATION_CONFIDENCE_BOOST
    trending_threshold = max(0.35, TRENDING_THRESHOLD - boost)
    volatile_threshold = max(0.30, VOLATILE_THRESHOLD - boost)

    if p_trending >= trending_threshold and p_trending >= p_ranging:
        if p_volatile >= volatile_threshold:
            regime     = "trending_volatile"
        else:
            regime     = "trending"
        confidence = round(p_trending, 4)
    elif p_volatile >= volatile_threshold and p_trending < trending_threshold:
        regime     = "volatile"
        confidence = round(p_volatile, 4)
    else:
        regime     = "ranging"
        confidence = round(p_ranging, 4)

    logger.info(
        f"[{symbol}] p_trending={p_trending:.4f} p_ranging={p_ranging:.4f} "
        f"p_volatile={p_volatile:.4f} regime={regime} confidence={confidence} "
        f"trend_direction={trend_direction}({direction_strength:+.4f}) reputation={reputation:.4f}"
    )

    return {
        "symbol":             symbol,
        "p_trending":         p_trending,
        "p_ranging":          p_ranging,
        "p_volatile":         p_volatile,
        "regime":             regime,
        "confidence":         confidence,
        "trend_direction":    trend_direction,
        "direction_strength": direction_strength,
        "ready":              True,
    }