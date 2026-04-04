import pytest
import os
import psycopg2


def get_test_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def test_postgres_connection():
    conn = get_test_conn()
    assert conn is not None
    conn.close()


def test_required_tables_exist():
    tables = [
        "users", "sessions", "symbols", "agents",
        "market_data", "funding_rates", "oi_history",
        "liquidations", "cvd_history", "snapshots",
        "trades", "signals", "positions", "logs",
        "trade_outcomes", "reputation_history", "retrain_log",
    ]
    conn = get_test_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    existing = {r[0] for r in cur.fetchall()}
    cur.close()
    conn.close()

    for table in tables:
        assert table in existing, f"Missing table: {table}"


def test_symbols_seeded():
    conn = get_test_conn()
    cur  = conn.cursor()
    cur.execute("SELECT symbol FROM symbols WHERE active = TRUE")
    symbols = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    assert "BTCUSDT" in symbols
    assert "ETHUSDT" in symbols
    assert "SOLUSDT" in symbols


def test_trade_outcomes_columns():
    conn = get_test_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'trade_outcomes'
    """)
    cols = {r[0] for r in cur.fetchall()}
    cur.close()
    conn.close()
    expected = {
        "id", "intent_hash", "pair", "action", "entry_price",
        "exit_price", "amount_usd", "confidence_at_entry",
        "reputation_at_entry", "checkpoint_hash", "outcome_tx_hash",
        "status", "created_at", "resolved_at",
    }
    for col in expected:
        assert col in cols, f"Missing column: {col}"


def test_write_and_read_trade_outcome():
    import time
    conn = get_test_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO trade_outcomes
            (intent_hash, pair, action, entry_price, amount_usd,
             confidence_at_entry, reputation_at_entry, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (intent_hash) DO NOTHING
    """, ("0xtest123", "BTCUSDT", "LONG", 65000.0, 100.0, 0.72, 0.5, "PENDING", int(time.time())))
    conn.commit()

    cur.execute("SELECT status FROM trade_outcomes WHERE intent_hash = '0xtest123'")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "PENDING"

    cur.execute("DELETE FROM trade_outcomes WHERE intent_hash = '0xtest123'")
    conn.commit()
    cur.close()
    conn.close()


def test_reputation_history_write():
    import time
    conn = get_test_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO reputation_history (agent_id, score, recorded_at)
        VALUES (%s, %s, %s)
    """, (0, 0.65, int(time.time())))
    conn.commit()

    cur.execute("SELECT score FROM reputation_history WHERE agent_id = 0 ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    assert row is not None
    assert float(row[0]) == 0.65

    cur.execute("DELETE FROM reputation_history WHERE agent_id = 0")
    conn.commit()
    cur.close()
    conn.close()


def test_indexes_exist():
    conn = get_test_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT indexname FROM pg_indexes WHERE schemaname = 'public'
    """)
    indexes = {r[0] for r in cur.fetchall()}
    cur.close()
    conn.close()
    expected = [
        "idx_market_data_symbol_interval",
        "idx_trade_outcomes_status",
        "idx_trade_outcomes_pair",
        "idx_reputation_agent",
    ]
    for idx in expected:
        assert idx in indexes, f"Missing index: {idx}"
