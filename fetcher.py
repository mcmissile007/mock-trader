"""Binance data fetcher -- public endpoints, no API key needed."""
import logging
from datetime import datetime, timezone

import requests

import config

logger = logging.getLogger(__name__)


def fetch_latest_candle() -> dict | None:
    """Fetch the last closed 1h candle from Binance."""
    url = f"{config.BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": config.SYMBOL, "interval": "1h", "limit": 2}

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error("Failed to fetch candle: %s", e)
        return None

    if len(data) < 2:
        return None

    candle = data[0]  # last closed
    return {
        "open_time": datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc),
        "open": float(candle[1]),
        "high": float(candle[2]),
        "low": float(candle[3]),
        "close": float(candle[4]),
        "volume": float(candle[5]),
    }


def fetch_ticker_price() -> float | None:
    """Fetch current BTC price from Binance ticker."""
    url = f"{config.BINANCE_BASE_URL}/api/v3/ticker/price"
    params = {"symbol": config.SYMBOL}

    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception as e:
        logger.error("Failed to fetch price: %s", e)
        return None


def fetch_funding_rate() -> float | None:
    """Fetch latest funding rate from Binance Futures."""
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {"symbol": config.SYMBOL, "limit": 1}

    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        return float(data[0]["fundingRate"]) if data else None
    except Exception as e:
        logger.error("Failed to fetch funding rate: %s", e)
        return None


def backfill_candles(hours: int = 500) -> list[dict]:
    """Fetch last N hours of candles for initial feature computation."""
    url = f"{config.BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": config.SYMBOL, "interval": "1h", "limit": hours}

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error("Failed to backfill: %s", e)
        return []

    candles = []
    for c in data[:-1]:  # exclude current incomplete candle
        candles.append({
            "open_time": datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc),
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5]),
        })
    return candles
