---
description: Project architecture and structure conventions
---

# Mock Trader — Architecture

> For design decisions and project state, see **SPEC.md** in the project root.

## Overview

Mock Trader is a live mock trading system that simulates BUY/SELL operations
using ML models trained in Velma. It runs 24/7, fetching data from Binance,
computing features, and executing trades based on model predictions.

## Project Type

- **Flat Python project** — single directory, no `src/` package structure.
- **PostgreSQL** for persistence — supports remote DB and multiple clients.
- **Single git repo** at the project root.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| DataFrames | Pandas |
| Database | PostgreSQL (remote-capable) |
| ML Models | XGBoost (loaded via joblib) |
| Exchange API | Binance REST (public, no key needed) |
| Config | python-dotenv (.env) |
| Linting | Ruff (check + format) |

## File Structure

```
mock-trader/
├── main.py              # Entry point: hourly + monitor loops
├── fetcher.py           # Binance API (candles, ticker, funding)
├── features_compute.py  # Self-contained feature computation
├── trader.py            # BaseTrader, XGBoostTrader, RandomTrader
├── monitor.py           # Fast TP/SL checker (every 60s)
├── db.py                # PostgreSQL helpers
├── config.py            # .env loader
├── schema.sql           # Database schema
├── register_trader.py   # CLI: register new traders
├── status.py            # CLI: show trader status
├── SPEC.md              # Project specification
├── .env.example         # Environment template
└── requirements.txt     # Dependencies
```

## Conventions

- Follow all rules defined in `CODE.md`.
- Design decisions are tracked in `SPEC.md` (project root).
- All files are top-level (no package structure needed for this project size).
- Business logic in modules — `main.py` only orchestrates.
- PostgreSQL is the single source of truth for all state.
- System is designed to be stopped and restarted at any time.
