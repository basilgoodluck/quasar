from db import get_connection


def get_all_symbols():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT symbol, active, intervals FROM symbols")
            return list(cur.fetchall())


def set_symbol_active(symbol: str, active: bool):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE symbols SET active = %s WHERE symbol = %s",
                (active, symbol),
            )
            conn.commit()
