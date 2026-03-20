"""Configuration loaded from .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "mock_trader")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DB_DSN = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

# Binance
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")

# Trading
DEFAULT_AMOUNT_USD = float(os.getenv("DEFAULT_AMOUNT_USD", "10"))
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))
FEE_PCT = float(os.getenv("FEE_PCT", "0.001"))

# Paths
MODELS_DIR = Path(os.getenv("MODELS_DIR", "models"))
