# Mock Trader

Live mock trading system for ML/AI models. Simulates BUY/SELL on BTC/USDT
with real-time TP/SL monitoring. Multiple traders compete in parallel.

## Setup

```bash
# 1. Create virtualenv
python -m venv .venv && source .venv/bin/activate

# 2. Install in editable mode
pip install -e .

# 3. Copy and configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. Initialize database
psql -U postgres -c "CREATE DATABASE mock_trader;"
```

## Usage

```bash
# Register a random baseline trader
python scripts/register_trader.py \
    --name random_baseline --type Random \
    --buy-prob 0.05 --tp 0.04 --sl -0.04 --max-hold 72

# Register an XGBoost trader (from Velma)
python scripts/register_trader.py \
    --name xgboost_v1 --type XGBoost \
    --model-path /path/to/trained_model \
    --tp 0.04 --sl -0.04 --max-hold 72 --min-confidence 0.80

# Start trading
python scripts/main.py

# Check status
python scripts/status.py
```

## Development

```bash
# Lint + format check
ruff check src/ scripts/ tests/ && ruff format --check src/ scripts/ tests/

# Run tests
pytest

# Auto-fix formatting
ruff format src/ scripts/ tests/
```

## Project Structure

```
src/          → library modules (config, db, fetcher, features, trader, monitor)
scripts/      → CLI entry points (main, register_trader, status)
tests/        → test suite
```

See [SPEC.md](SPEC.md) for full architecture and design decisions.
