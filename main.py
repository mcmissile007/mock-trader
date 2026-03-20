"""Mock Trader -- Main entry point.

Runs two loops:
- Hourly: fetch candle, compute features, run all traders
- Monitor: check TP/SL every 60 seconds

Usage:
    python main.py
    python main.py --backfill 500
"""
import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timezone

import db
import fetcher
import config
from features_compute import compute_features
from monitor import check_all_positions
from trader import create_trader, BaseTrader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

running = True


def handle_signal(sig, frame):
    global running
    logger.info("Shutting down...")
    running = False


def backfill(hours: int):
    """Backfill candles from Binance."""
    logger.info("Backfilling %d hours of candles...", hours)
    candles = fetcher.backfill_candles(hours)
    for c in candles:
        db.upsert_candle(
            c["open_time"], c["open"], c["high"],
            c["low"], c["close"], c["volume"],
        )
    logger.info("Backfilled %d candles", len(candles))
    return len(candles)


def load_traders() -> dict[int, BaseTrader]:
    rows = db.get_active_traders()
    traders = {}
    for row in rows:
        try:
            trader = create_trader(row)
            traders[trader.id] = trader
            logger.info(
                "Loaded trader: %s (id=%d, type=%s)",
                trader.name, trader.id, trader.model_type,
            )
        except Exception as e:
            logger.error("Failed to load trader %s: %s", row["name"], e)
    return traders


def hourly_tick(traders: dict[int, BaseTrader]):
    """Hourly loop: fetch candle -> compute features -> run traders."""
    candle = fetcher.fetch_latest_candle()
    if candle is None:
        logger.warning("Failed to fetch candle, skipping")
        return

    db.upsert_candle(
        candle["open_time"], candle["open"], candle["high"],
        candle["low"], candle["close"], candle["volume"],
    )
    logger.info(
        "Candle %s: O=%.2f H=%.2f L=%.2f C=%.2f",
        candle["open_time"].strftime("%Y-%m-%d %H:%M"),
        candle["open"], candle["high"], candle["low"], candle["close"],
    )

    candles = db.get_candles(limit=500)
    if len(candles) < 200:
        logger.warning(
            "Only %d candles -- need at least 200 for features", len(candles)
        )
        return

    import pandas as pd
    df = pd.DataFrame(candles)

    fr = fetcher.fetch_funding_rate()
    funding_rates = [fr] if fr is not None else None

    features_df = compute_features(df, funding_rates)
    now = datetime.now(timezone.utc)
    current_price = candle["close"]

    for trader in traders.values():
        try:
            trader.on_new_candle(features_df, current_price, now)
        except Exception as e:
            logger.error("Trader %s error: %s", trader.name, e, exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="Mock Trader")
    parser.add_argument(
        "--backfill", type=int, default=500, help="Hours to backfill"
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    db.init_db()

    n_candles = len(db.get_candles(limit=1))
    if n_candles == 0:
        backfill(args.backfill)

    traders = load_traders()
    if not traders:
        logger.warning(
            "No active traders! Register one with register_trader.py"
        )

    logger.info("Starting mock trader with %d traders", len(traders))
    logger.info("Monitor interval: %ds", config.MONITOR_INTERVAL)

    last_hour = -1
    tick_count = 0

    while running:
        now = datetime.now(timezone.utc)

        # Hourly tick at minute :05 of each new hour
        if now.hour != last_hour and now.minute >= 5:
            last_hour = now.hour
            logger.info("=" * 50)
            hourly_tick(traders)

            tick_count += 1
            if tick_count % 6 == 0:
                for trader in traders.values():
                    summary = db.get_trades_summary(trader.id)
                    n_open = len(db.get_open_positions(trader.id))
                    total = int(summary.get("total", 0) or 0)
                    wins = int(summary.get("wins", 0) or 0)
                    wr = f"{wins/total:.0%}" if total > 0 else "N/A"
                    logger.info(
                        "[%s] %d trades, WR=%s, PnL=$%s, open=%d",
                        trader.name, total, wr,
                        summary.get("total_pnl_usd", 0), n_open,
                    )

        # Monitor TP/SL every 60 seconds
        check_all_positions(traders)
        time.sleep(config.MONITOR_INTERVAL)

    logger.info("Goodbye!")


if __name__ == "__main__":
    main()
