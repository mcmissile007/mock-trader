# Mock Trader — Specification

> Living document. Update when design decisions are made.

## Project Overview

Live mock trading system for ML/AI models. Simulates BUY/SELL on BTC/USDT
with real-time TP/SL monitoring. Multiple traders compete in parallel.
Results stored in PostgreSQL for a future web dashboard.

## Pipeline Status

| Phase | Module | Status |
|-------|--------|--------|
| 1. Data fetch | `src/fetcher.py` | ✅ Done |
| 2. Feature compute | `src/features.py` | ✅ Done |
| 3. Trading logic | `src/trader.py` | ✅ Done |
| 4. TP/SL monitor | `src/monitor.py` | ✅ Done |
| 5. DB persistence | `src/db.py` + `src/schema.sql` | ✅ Done |
| 6. Resilient startup | `scripts/main.py` | ✅ Done |
| 7. Web dashboard | (separate project) | ⬚ TODO |

## Architecture

```
scripts/main.py
├── Hourly loop (every hour at :05)
│   ├── fetcher.fetch_latest_candle()
│   ├── db.upsert_candle()
│   ├── features.compute_features()
│   └── trader.on_new_candle() → BUY / SELL
└── Monitor loop (every 60s)
    ├── fetcher.fetch_ticker_price()
    └── trader.check_positions() → TP / SL / timeout
```

## Project Structure

```
mock-trader/
├── pyproject.toml          # project config, deps, tooling
├── src/                    # library modules
│   ├── config.py
│   ├── db.py
│   ├── features.py
│   ├── fetcher.py
│   ├── monitor.py
│   ├── schema.sql
│   └── trader.py
├── scripts/                # CLI entry points
│   ├── main.py
│   ├── register_trader.py
│   └── status.py
├── tests/                  # test suite
│   ├── conftest.py
│   └── test_placeholder.py
├── .env.example
├── README.md
└── SPEC.md
```

## Trading Rules

1. **BUY**: model says BUY with confidence ≥ threshold → open $10 position
2. **Multiple positions**: a second BUY opens a second position
3. **SELL signal**: closes ALL open positions for that trader
4. **TP/SL**: checked every 60s against live Binance price
5. **Timeout**: position closed after max_hold hours
6. **Fees**: 0.1% per side (deducted from P&L)

## Resilient Startup

The system can be stopped and restarted at any time. On startup:
1. **Backfill candles**: fetch last 500h from Binance to fill gaps
2. **Recompute features**: from stored candles in DB
3. **Recover positions**: open positions are loaded from DB
4. **Resume monitoring**: TP/SL checks start immediately

## Trader Types

| Type | Model | Signal source |
|------|-------|---------------|
| `XGBoost` | Velma trained model | `model.predict()` + confidence |
| `Random` | None | Random buy with configurable probability |
| `LLM` | (future) | LLM-generated signals |

## Database Schema

- `traders`: registered strategies (name, type, model_path, features, strategy)
- `positions`: open/closed positions (entry/exit price, P&L, reason)
- `candles`: 1h OHLCV data from Binance
- `features_cache`: precomputed features (optional)

## Design Decisions Log

| ID | Decision | Rationale |
|----|----------|-----------|
| DD-001 | Separate repo from Velma | Different concern (live runtime vs research) |
| DD-002 | PostgreSQL over DuckDB | Multi-trader, future web dashboard, remote access |
| DD-003 | Self-contained features | No Velma dependency — features.py reimplements core calcs |
| DD-004 | 60s monitor interval | Balance between responsiveness and API limits |
| DD-005 | Backfill on startup | Resilience — can recover after hours/days offline |
| DD-006 | Multiple positions per trader | Allows stacking BUY signals for high-conviction moments |
| DD-007 | src/ + scripts/ + tests/ layout | Consistent with velma, clean separation of library vs CLI vs tests |
