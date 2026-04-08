import asyncio
from database.connection import get_pool
from contracts.vault import get_available_capital
from logger import get_logger

logger = get_logger(__name__)

MAX_DRAWDOWN       = 0.05
MAX_CONCURRENT     = 3
BASE_CONCURRENT    = 1
MIN_WIN_RATE_SAMPLE = 10
DEFAULT_WIN_RATE   = 0.45
MAX_TRADE_USD      = 1000.0
MIN_RISK_PCT       = 0.005
MAX_RISK_PCT       = 0.02
MIN_LEVERAGE       = 2.0
MAX_LEVERAGE       = 5.0
MIN_RR             = 1.5
MAX_RR             = 3.0


async def get_open_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) FROM trade_outcomes WHERE status = 'PENDING'")
        return row["count"]


async def get_win_rate() -> tuple[float, int]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'WIN')  AS wins,
                COUNT(*) FILTER (WHERE status = 'LOSS') AS losses
            FROM trade_outcomes
            WHERE status IN ('WIN', 'LOSS')
        """)
    wins   = row["wins"]
    losses = row["losses"]
    total  = wins + losses
    if total < MIN_WIN_RATE_SAMPLE:
        return DEFAULT_WIN_RATE, total
    return round(wins / total, 4), total


async def get_drawdown() -> float:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                SUM(CASE WHEN status = 'LOSS' AND exit_price IS NOT NULL THEN amount_usd ELSE 0 END) AS total_lost,
                SUM(amount_usd) AS total_risked
            FROM trade_outcomes
            WHERE status IN ('WIN', 'LOSS')
        """)
    total_lost   = row["total_lost"] or 0
    total_risked = row["total_risked"] or 0
    if total_risked == 0:
        return 0.0
    return float(total_lost / total_risked)


def allowed_concurrent(reputation: float, win_rate: float) -> int:
    if reputation >= 0.7 and win_rate >= 0.6:
        return MAX_CONCURRENT
    if reputation >= 0.4 and win_rate >= 0.5:
        return 2
    return BASE_CONCURRENT


def kelly(win_rate: float, rr: float) -> float:
    k = (win_rate * rr - (1 - win_rate)) / rr
    return round(max(0.0, k) * 0.25, 4)


def regime_leverage(regime: str, confidence: float) -> float:
    base = {"trending": 3.0, "trending_volatile": 4.0, "volatile": 2.0}.get(regime, MIN_LEVERAGE)
    return round(max(MIN_LEVERAGE, min(MAX_LEVERAGE, base * confidence)), 2)


def regime_rr(regime: str, confidence: float) -> float:
    base = {"trending": 2.0, "trending_volatile": 2.5, "volatile": 1.5}.get(regime, MIN_RR)
    return round(max(MIN_RR, min(MAX_RR, base * confidence)), 2)


async def compute_risk(regime: dict, reputation: float) -> dict:
    current_regime = regime.get("regime", "ranging")
    confidence     = regime.get("confidence", 0.0)

    drawdown, win_rate_data, open_count = await asyncio.gather(
        get_drawdown(),
        get_win_rate(),
        get_open_count(),
    )

    win_rate, sample_size = win_rate_data

    if drawdown >= MAX_DRAWDOWN:
        logger.warning(f"[risk] drawdown {drawdown:.2%} hit limit — blocking all trades")
        return {
            "action":      "SKIP",
            "leverage":    MIN_LEVERAGE,
            "risk_pct":    MIN_RISK_PCT,
            "rr_ratio":    MIN_RR,
            "explanation": f"Drawdown limit reached {drawdown:.2%}",
        }

    remaining_drawdown  = MAX_DRAWDOWN - drawdown
    max_concurrent      = allowed_concurrent(reputation, win_rate)

    if open_count >= max_concurrent:
        logger.info(f"[risk] {open_count} open positions — limit is {max_concurrent}")
        return {
            "action":      "SKIP",
            "leverage":    MIN_LEVERAGE,
            "risk_pct":    MIN_RISK_PCT,
            "rr_ratio":    MIN_RR,
            "explanation": f"Max concurrent positions reached ({open_count}/{max_concurrent})",
        }

    rr         = regime_rr(current_regime, confidence)
    k          = kelly(win_rate, rr)
    leverage   = regime_leverage(current_regime, confidence)
    rep_scale  = 0.2 + (0.8 * reputation)
    raw_risk   = k * confidence * rep_scale
    risk_pct   = round(max(MIN_RISK_PCT, min(MAX_RISK_PCT, raw_risk)), 6)
    risk_pct   = min(risk_pct, remaining_drawdown * 0.5)

    capital    = get_available_capital()
    amount_usd = round(min(capital * risk_pct * leverage, MAX_TRADE_USD), 2)

    logger.info(
        f"[risk] regime={current_regime} confidence={confidence} reputation={reputation} "
        f"win_rate={win_rate}(n={sample_size}) kelly={k} risk_pct={risk_pct} "
        f"leverage={leverage}x rr={rr} amount=${amount_usd} "
        f"drawdown={drawdown:.2%} open={open_count}/{max_concurrent}"
    )

    return {
        "action":      "COMPUTE",
        "leverage":    leverage,
        "risk_pct":    risk_pct,
        "rr_ratio":    rr,
        "amount_usd":  amount_usd,
        "explanation": (
            f"kelly={k} win_rate={win_rate}(n={sample_size}) "
            f"risk={risk_pct:.2%} leverage={leverage}x rr={rr} "
            f"drawdown_used={drawdown:.2%} open={open_count}/{max_concurrent}"
        ),
    }