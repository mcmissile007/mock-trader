"""Fast monitoring loop -- checks TP/SL every minute."""
import logging
from datetime import datetime, timezone

import db
import fetcher
from trader import BaseTrader

logger = logging.getLogger(__name__)


def check_all_positions(traders: dict[int, BaseTrader]):
    """Check TP/SL/timeout for all open positions."""
    price = fetcher.fetch_ticker_price()
    if price is None:
        return

    now = datetime.now(timezone.utc)
    open_positions = db.get_open_positions()

    if not open_positions:
        return

    for pos in open_positions:
        trader = traders.get(pos["trader_id"])
        if trader:
            trader.check_positions(price, now)
