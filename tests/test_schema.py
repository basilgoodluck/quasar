import os
import pytest
import asyncpg
import time


async def get_test_conn():
    return await asyncpg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        database=os.environ["POSTGRES_DB"],
    )


@pytest.mark.asyncio
async def test_postgres_connection():
    conn = await get_test_conn()
    assert conn is not None
    await conn.close()


@pytest.mark.asyncio
async def test_required_tables_exist():
    tables = [
        "users", "sessions", "symbols", "agents",
        "market_data", "funding_rates", "oi_history",
        "liquidations", "cvd_history", "snapshots",
        "agg_trades", "trade_outcomes", "reputation_history", "retrain_log",
    ]
    conn     = await get_test_conn()
    rows     = await conn.fetch("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    existing = {r["table_name"] for r in rows}
    await conn.close()
    for table in tables:
        assert table in existing, f"Missing table: {table}"


@pytest.mark.asyncio
async def test_symbols_seeded():
    conn    = await get_test_conn()
    rows    = await conn.fetch("SELECT symbol FROM symbols WHERE active = TRUE")
    symbols = [r["symbol"] for r in rows]
    await conn.close()
    assert "BTCUSDT" in symbols
    assert "ETHUSDT" in symbols
    assert "SOLUSDT" in symbols


@pytest.mark.asyncio
async def test_trade_outcomes_columns():
    conn = await get_test_conn()
    rows = await conn.fetch("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'trade_outcomes'
    """)
    cols = {r["column_name"] for r in rows}
    await conn.close()
    expected = {
        "id", "intent_hash", "pair", "action", "entry_price",
        "exit_price", "amount_usd", "confidence_at_entry",
        "reputation_at_entry", "checkpoint_hash", "outcome_tx_hash",
        "status", "created_at", "resolved_at",
    }
    for col in expected:
        assert col in cols, f"Missing column: {col}"


@pytest.mark.asyncio
async def test_write_and_read_trade_outcome():
    conn = await get_test_conn()
    await conn.execute("""
        INSERT INTO trade_outcomes
            (intent_hash, pair, action, entry_price, amount_usd,
             confidence_at_entry, reputation_at_entry, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (intent_hash) DO NOTHING
    """, "0xtest123", "BTCUSDT", "LONG", 65000.0, 100.0, 0.72, 0.5, "PENDING", int(time.time()))
    row = await conn.fetchrow("SELECT status FROM trade_outcomes WHERE intent_hash = '0xtest123'")
    assert row is not None
    assert row["status"] == "PENDING"
    await conn.execute("DELETE FROM trade_outcomes WHERE intent_hash = '0xtest123'")
    await conn.close()


@pytest.mark.asyncio
async def test_reputation_history_write():
    conn = await get_test_conn()
    await conn.execute("""
        INSERT INTO reputation_history (agent_id, score, recorded_at)
        VALUES ($1, $2, $3)
    """, 0, 0.65, int(time.time()))
    row = await conn.fetchrow("SELECT score FROM reputation_history WHERE agent_id = 0 ORDER BY id DESC LIMIT 1")
    assert row is not None
    assert float(row["score"]) == 0.65
    await conn.execute("DELETE FROM reputation_history WHERE agent_id = 0")
    await conn.close()


@pytest.mark.asyncio
async def test_indexes_exist():
    conn    = await get_test_conn()
    rows    = await conn.fetch("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
    indexes = {r["indexname"] for r in rows}
    await conn.close()
    expected = [
        "idx_market_data_symbol_interval",
        "idx_trade_outcomes_status",
        "idx_trade_outcomes_pair",
        "idx_reputation_agent",
    ]
    for idx in expected:
        assert idx in indexes, f"Missing index: {idx}"