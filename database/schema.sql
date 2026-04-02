CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    discord_id TEXT,
    telegram_id TEXT,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT UNIQUE NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    intervals TEXT[] NOT NULL DEFAULT '{15m,1h}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO symbols (symbol, active, intervals) VALUES
    ('BTCUSDT', TRUE, '{15m,1h}'),
    ('ETHUSDT', TRUE, '{15m,1h}'),
    ('SOLUSDT', TRUE, '{15m,1h}');

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT,
    active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES symbols(id) ON DELETE CASCADE,
    UNIQUE (agent_id, symbol_id)
);

CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    confidence NUMERIC,
    chaos NUMERIC,
    trend_direction INT,
    regime_label TEXT,
    price_at_signal NUMERIC,
    features JSONB,
    raw JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    snapshot_id UUID REFERENCES snapshots(id),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    status TEXT DEFAULT 'open',
    tx_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    source TEXT,
    action TEXT NOT NULL,
    confidence NUMERIC,
    raw JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    avg_price NUMERIC NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (agent_id, symbol)
);

CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    open_time BIGINT NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    taker_buy_volume NUMERIC,
    close_time BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, interval, open_time)
);

CREATE TABLE funding_rates (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    funding_time BIGINT NOT NULL,
    funding_rate NUMERIC NOT NULL,
    mark_price NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, funding_time)
);

CREATE TABLE oi_history (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    period TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    open_interest NUMERIC NOT NULL,
    open_interest_value NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, period, timestamp)
);

CREATE TABLE liquidations (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    trade_time BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cvd_history (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    open_time BIGINT NOT NULL,
    delta NUMERIC NOT NULL,
    cvd NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, interval, open_time)
);

CREATE INDEX idx_market_data_symbol_interval ON market_data (symbol, interval, open_time DESC);
CREATE INDEX idx_funding_rates_symbol ON funding_rates (symbol, funding_time DESC);
CREATE INDEX idx_oi_history_symbol ON oi_history (symbol, period, timestamp DESC);
CREATE INDEX idx_liquidations_symbol ON liquidations (symbol, trade_time DESC);
CREATE INDEX idx_cvd_history_symbol ON cvd_history (symbol, interval, open_time DESC);
CREATE INDEX idx_snapshots_agent_symbol ON snapshots (agent_id, symbol, created_at DESC);
CREATE INDEX idx_signals_agent_symbol ON signals (agent_id, symbol, created_at DESC);