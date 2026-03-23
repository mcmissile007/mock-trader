"""Mock Trader -- Main entry point.

Runs two loops:
- Hourly: fetch candle, compute features, run all traders
- Monitor: check TP/SL every 60 seconds

Resilient: can be stopped and restarted at any time.
On startup, backfills missing candles and recovers open positions from DB.

Usage:
    python main.py
    python main.py --backfill 500
"""

import argparse
import logging
import signal
import time
from datetime import datetime, timezone

import config
import db
import fetcher
from features import compute_features
from monitor import check_all_positions
from trader import BaseTrader, create_trader

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


def smart_backfill(max_hours: int = 500):
    """Backfill candles intelligently.

    - If DB is empty: fetch last max_hours candles
    - If DB has candles: fetch only the gap since last candle
    """
    candles = db.get_candles(limit=1)

    if not candles:
        logger.info("Empty DB -- backfilling %d hours...", max_hours)
        new_candles = fetcher.backfill_candles(max_hours)
    else:
        last_time = candles[-1]["open_time"]
        if not last_time.tzinfo:
            last_time = last_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        gap_hours = int((now - last_time).total_seconds() / 3600) + 1

        if gap_hours <= 1:
            logger.info("Candles up to date (last: %s)", last_time)
            return 0
        elif gap_hours > max_hours:
            gap_hours = max_hours

        logger.info(
            "Gap detected: last candle %s (%d hours ago). Backfilling...",
            last_time.strftime("%Y-%m-%d %H:%M"),
            gap_hours,
        )
        new_candles = fetcher.backfill_candles(gap_hours)

    count = 0
    for c in new_candles:
        db.upsert_candle(
            c["open_time"],
            c["open"],
            c["high"],
            c["low"],
            c["close"],
            c["volume"],
        )
        count += 1

    logger.info("Backfilled %d candles", count)
    return count


def load_traders() -> dict[int, BaseTrader]:
    rows = db.get_active_traders()
    traders = {}
    for row in rows:
        try:
            trader = create_trader(row)
            traders[trader.id] = trader
            logger.info(
                "Loaded trader: %s (id=%d, type=%s)",
                trader.name,
                trader.id,
                trader.model_type,
            )
        except Exception as e:
            logger.error("Failed to load trader %s: %s", row["name"], e)
    return traders


def recover_state(traders: dict[int, BaseTrader]):
    """Recover open positions and log state after restart."""
    for trader in traders.values():
        open_pos = db.get_open_positions(trader.id)
        summary = db.get_trades_summary(trader.id)
        total = int(summary.get("total", 0) or 0)
        wins = int(summary.get("wins", 0) or 0)
        wr = f"{wins / total:.0%}" if total > 0 else "N/A"

        logger.info(
            "[%s] Recovered: %d open positions, %d completed trades (WR=%s)",
            trader.name,
            len(open_pos),
            total,
            wr,
        )
        for pos in open_pos:
            logger.info(
                "  Open #%d: entry=$%.2f (conf=%.3f) since %s",
                pos["id"],
                float(pos["entry_price"]),
                float(pos["confidence"]),
                pos["entry_time"],
            )


def hourly_tick(traders: dict[int, BaseTrader]):
    """Hourly loop: fetch candle -> compute features -> run traders."""
    candle = fetcher.fetch_latest_candle()
    if candle is None:
        logger.warning("Failed to fetch candle, skipping")
        return

    db.upsert_candle(
        candle["open_time"],
        candle["open"],
        candle["high"],
        candle["low"],
        candle["close"],
        candle["volume"],
    )
    logger.info(
        "Candle %s: O=%.2f H=%.2f L=%.2f C=%.2f V=%.0f",
        candle["open_time"].strftime("%Y-%m-%d %H:%M"),
        candle["open"],
        candle["high"],
        candle["low"],
        candle["close"],
        candle["volume"],
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


def print_summary(traders: dict[int, BaseTrader]):
    """Print periodic summary of all traders."""
    for trader in traders.values():
        summary = db.get_trades_summary(trader.id)
        n_open = len(db.get_open_positions(trader.id))
        total = int(summary.get("total", 0) or 0)
        wins = int(summary.get("wins", 0) or 0)
        wr = f"{wins / total:.0%}" if total > 0 else "N/A"
        pnl = summary.get("total_pnl_usd", 0) or 0
        logger.info(
            "[%s] %d trades, WR=%s, PnL=$%s, open=%d",
            trader.name,
            total,
            wr,
            pnl,
            n_open,
        )


def main():
    parser = argparse.ArgumentParser(description="Mock Trader")
    parser.add_argument(
        "--backfill", type=int, default=500, help="Max hours to backfill"
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Init database
    db.init_db()

    # Smart backfill (fills gaps or full backfill if empty)
    smart_backfill(args.backfill)

    # Load traders
    traders = load_traders()
    if not traders:
        logger.warning("No active traders! Register one with register_trader.py")

    # Recover state (open positions, trade history)
    recover_state(traders)

    logger.info("=" * 60)
    logger.info("Mock Trader started with %d traders", len(traders))
    logger.info("Monitor interval: %ds", config.MONITOR_INTERVAL)
    logger.info("=" * 60)

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
                print_summary(traders)

        # Monitor TP/SL every 60 seconds
        check_all_positions(traders)
        time.sleep(config.MONITOR_INTERVAL)

    # Graceful shutdown
    logger.info("=" * 60)
    logger.info("Shutting down. Final status:")
    print_summary(traders)
    logger.info("Goodbye!")


if __name__ == "__main__":
    main()
