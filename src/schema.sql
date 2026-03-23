-- Mock Trader Database Schema
-- Run: psql -U postgres -d mock_trader -f schema.sql

CREATE TABLE IF NOT EXISTS traders (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    model_type  TEXT NOT NULL,
    model_path  TEXT,
    features    JSONB,
    strategy    JSONB NOT NULL,
    active      BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS positions (
    id          SERIAL PRIMARY KEY,
    trader_id   INT REFERENCES traders(id),
    entry_time  TIMESTAMPTZ NOT NULL,
    entry_price NUMERIC NOT NULL,
    amount_usd  NUMERIC DEFAULT 10,
    confidence  NUMERIC,
    status      TEXT DEFAULT 'open',
    exit_time   TIMESTAMPTZ,
    exit_price  NUMERIC,
    exit_reason TEXT,
    pnl_pct     NUMERIC,
    pnl_usd     NUMERIC,
    hold_hours  NUMERIC,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS candles (
    open_time   TIMESTAMPTZ PRIMARY KEY,
    open        NUMERIC NOT NULL,
    high        NUMERIC NOT NULL,
    low         NUMERIC NOT NULL,
    close       NUMERIC NOT NULL,
    volume      NUMERIC NOT NULL
);

CREATE TABLE IF NOT EXISTS features_cache (
    open_time   TIMESTAMPTZ PRIMARY KEY,
    features    JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_positions_trader ON positions(trader_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_trader_status ON positions(trader_id, status);
CREATE INDEX IF NOT EXISTS idx_candles_time ON candles(open_time DESC);
