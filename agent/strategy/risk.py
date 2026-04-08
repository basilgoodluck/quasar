from database.connection import get_connection
from contracts.vault import get_available_capital
from logger import get_logger

logger = get_logger(__name__)

MAX_DRAWDOWN        = 0.05
MAX_CONCURRENT      = 3
BASE_CONCURRENT     = 1
MIN_WIN_RATE_SAMPLE = 10
DEFAULT_WIN_RATE    = 0.45
MAX_TRADE_USD       = 500.0
MIN_RISK_PCT        = 0.005
MAX_RISK_PCT        = 0.02
MIN_LEVERAGE        = 2.0
MAX_LEVERAGE        = 5.0
MIN_RR              = 1.5
MAX_RR              = 3.0


def _get_open_positions_count() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM trade_outcomes WHERE status = 'PENDING'")
            return cur.fetchone()[0]


def _get_win_rate() -> tuple[float, int]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'WIN')  AS wins,
                    COUNT(*) FILTER (WHERE status = 'LOSS') AS losses
                FROM trade_outcomes
                WHERE status IN ('WIN', 'LOSS')
            """)
            row = cur.fetchone()
    wins, losses = row
    total = wins + losses
    if total < MIN_WIN_RATE_SAMPLE:
        return DEFAULT_WIN_RATE, total
    return round(wins / total, 4), total


def _get_cumulative_drawdown() -> float:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    SUM(CASE
                        WHEN status = 'LOSS' AND exit_price IS NOT NULL
                        THEN amount_usd
                        ELSE 0
                    END) AS total_lost,
                    SUM(amount_usd) AS total_risked
                FROM trade_outcomes
                WHERE status IN ('WIN', 'LOSS')
            """)
            row = cur.fetchone()
    total_lost, total_risked = row
    if not total_risked or total_risked == 0:
        return 0.0
    return float(total_lost / total_risked)


def _get_allowed_concurrent(reputation: float, win_rate: float) -> int:
    if reputation >= 0.7 and win_rate >= 0.6:
        return MAX_CONCURRENT
    if reputation >= 0.4 and win_rate >= 0.5:
        return 2
    return BASE_CONCURRENT


def _kelly_fraction(win_rate: float, rr: float) -> float:
    kelly = (win_rate * rr - (1 - win_rate)) / rr
    kelly = max(0.0, kelly)
    return round(kelly * 0.25, 4)


def _regime_leverage(regime: str, confidence: float) -> float:
    base = {
        "trending":          3.0,
        "trending_volatile": 4.0,
        "volatile":          2.0,
    }.get(regime, MIN_LEVERAGE)
    scaled = base * confidence
    return round(max(MIN_LEVERAGE, min(MAX_LEVERAGE, scaled)), 2)


def _regime_rr(regime: str, confidence: float) -> float:
    base = {
        "trending":          2.0,
        "trending_volatile": 2.5,
        "volatile":          1.5,
    }.get(regime, MIN_RR)
    scaled = base * confidence
    return round(max(MIN_RR, min(MAX_RR, scaled)), 2)


def compute_risk(regime: dict, reputation: float) -> dict:
    current_regime = regime.get("regime", "ranging")
    confidence     = regime.get("confidence", 0.0)

    drawdown = _get_cumulative_drawdown()
    if drawdown >= MAX_DRAWDOWN:
        logger.warning(f"[risk] cumulative drawdown {drawdown:.2%} hit limit — blocking all trades")
        return {
            "action":      "SKIP",
            "leverage":    MIN_LEVERAGE,
            "risk_pct":    MIN_RISK_PCT,
            "rr_ratio":    MIN_RR,
            "explanation": f"Drawdown limit reached {drawdown:.2%} — no new trades",
        }

    remaining_drawdown = MAX_DRAWDOWN - drawdown

    win_rate, sample_size = _get_win_rate()
    open_count            = _get_open_positions_count()
    allowed_concurrent    = _get_allowed_concurrent(reputation, win_rate)

    if open_count >= allowed_concurrent:
        logger.info(f"[risk] {open_count} open positions — limit is {allowed_concurrent}")
        return {
            "action":      "SKIP",
            "leverage":    MIN_LEVERAGE,
            "risk_pct":    MIN_RISK_PCT,
            "rr_ratio":    MIN_RR,
            "explanation": f"Max concurrent positions reached ({open_count}/{allowed_concurrent})",
        }

    rr       = _regime_rr(regime=current_regime, confidence=confidence)
    kelly    = _kelly_fraction(win_rate=win_rate, rr=rr)
    leverage = _regime_leverage(regime=current_regime, confidence=confidence)

    reputation_scale = 0.2 + (0.8 * reputation)
    raw_risk_pct     = kelly * confidence * reputation_scale
    risk_pct         = round(max(MIN_RISK_PCT, min(MAX_RISK_PCT, raw_risk_pct)), 6)
    risk_pct         = min(risk_pct, remaining_drawdown * 0.5)

    capital    = get_available_capital()
    amount_usd = round(capital * risk_pct * leverage, 2)
    amount_usd = min(amount_usd, MAX_TRADE_USD)

    logger.info(
        f"[risk] regime={current_regime} confidence={confidence} reputation={reputation} "
        f"win_rate={win_rate}(n={sample_size}) kelly={kelly} risk_pct={risk_pct} "
        f"leverage={leverage}x rr={rr} amount_usd=${amount_usd} "
        f"drawdown={drawdown:.2%} open={open_count}/{allowed_concurrent}"
    )

    return {
        "action":      "COMPUTE",
        "leverage":    leverage,
        "risk_pct":    risk_pct,
        "rr_ratio":    rr,
        "amount_usd":  amount_usd,
        "explanation": (
            f"kelly={kelly} win_rate={win_rate}(n={sample_size}) "
            f"risk={risk_pct:.2%} leverage={leverage}x rr={rr} "
            f"drawdown_used={drawdown:.2%} open={open_count}/{allowed_concurrent}"
        ),
    }