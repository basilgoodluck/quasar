from db import get_connection


def get_active_symbols():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT symbol FROM symbols WHERE active = TRUE")
            return [r["symbol"] for r in cur.fetchall()]


def get_regime_all():
    symbols = get_active_symbols()
    results = {}
    for symbol in symbols:
        try:
            from agent.regime import detect_regime
            results[symbol] = detect_regime(symbol)
        except Exception as e:
            results[symbol] = {"ready": False, "error": str(e)}
    return results
