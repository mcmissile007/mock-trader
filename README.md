# Mock Trader

Live mock trading system for ML/AI models — simulates BUY/SELL with real-time TP/SL monitoring.

## Features
- Hourly signal generation (BUY/SELL/HOLD) from trained models
- Real-time TP/SL monitoring every 60 seconds
- Multiple concurrent traders (XGBoost, Random, LLM)
- PostgreSQL storage for web dashboard integration

## Setup

```bash
pip install -r requirements.txt

# Create database
psql -U postgres -c 'CREATE DATABASE mock_trader;'
psql -U postgres -d mock_trader -f schema.sql

# Configure
cp .env.example .env
# Edit .env with your DB credentials

# Register traders
python register_trader.py \
    --name xgboost_v1 \
    --type XGBoost \
    --model-path /path/to/velma/trained_models/label_pct4_hold72/era3_xgb_tuned \
    --tp 0.04 --sl -0.04 --max-hold 72 --min-confidence 0.80

python register_trader.py \
    --name random_baseline \
    --type Random \
    --buy-prob 0.05

# Run
python main.py
```

## Architecture

- **Hourly loop**: Fetch candle → compute features → run models → open/close positions
- **Monitor loop** (every 60s): Check open positions for TP/SL via Binance ticker
- **PostgreSQL**: Stores traders, positions, trades for web dashboard
