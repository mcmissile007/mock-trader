"""PostgreSQL database helpers."""

import json
import logging
from contextlib import contextmanager
from datetime import datetime

import psycopg2
import psycopg2.extras

import config

logger = logging.getLogger(__name__)


@contextmanager
def get_conn():
    """Get a database connection."""
    conn = psycopg2.connect(config.DB_DSN)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    from pathlib import Path

    schema = (Path(__file__).parent / "schema.sql").read_text()
    with get_conn() as conn:
        conn.cursor().execute(schema)
    logger.info("Database initialized")


# --- Traders ---


def get_active_traders() -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM traders WHERE active = true")
        return [dict(r) for r in cur.fetchall()]


def register_trader(
    name: str,
    model_type: str,
    model_path: str,
    features: list,
    strategy: dict,
) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO traders (name, model_type, model_path, features, strategy)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (name) DO UPDATE SET
                   model_type = EXCLUDED.model_type,
                   model_path = EXCLUDED.model_path,
                   features = EXCLUDED.features,
                   strategy = EXCLUDED.strategy,
                   active = true
               RETURNING id""",
            (name, model_type, model_path, json.dumps(features), json.dumps(strategy)),
        )
        trader_id = cur.fetchone()[0]
    logger.info("Registered trader '%s' (id=%d)", name, trader_id)
    return trader_id


# --- Candles ---


def upsert_candle(open_time: datetime, o, h, l, c, v):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO candles (open_time, open, high, low, close, volume)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (open_time) DO UPDATE SET
                   high = EXCLUDED.high, low = EXCLUDED.low,
                   close = EXCLUDED.close, volume = EXCLUDED.volume""",
            (open_time, o, h, l, c, v),
        )


def get_candles(limit: int = 500) -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM candles ORDER BY open_time DESC LIMIT %s",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()][::-1]  # oldest first


# --- Positions ---


def open_position(
    trader_id: int,
    entry_time: datetime,
    entry_price: float,
    amount_usd: float,
    confidence: float,
) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO positions
               (trader_id, entry_time, entry_price, amount_usd, confidence)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (trader_id, entry_time, entry_price, amount_usd, confidence),
        )
        pos_id = cur.fetchone()[0]
    logger.info(
        "Opened position #%d for trader %d: $%.2f @ $%.2f (conf=%.3f)",
        pos_id,
        trader_id,
        amount_usd,
        entry_price,
        confidence,
    )
    return pos_id


def close_position(
    pos_id: int,
    exit_time: datetime,
    exit_price: float,
    reason: str,
    fee_pct: float = 0.001,
):
    with get_conn() as conn:
        cur = conn.cursor(psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM positions WHERE id = %s", (pos_id,))
        pos = dict(cur.fetchone())

        entry_price = float(pos["entry_price"])
        amount_usd = float(pos["amount_usd"])
        pnl_pct = (exit_price - entry_price) / entry_price - 2 * fee_pct
        pnl_usd = amount_usd * pnl_pct
        hold_hours = (exit_time - pos["entry_time"]).total_seconds() / 3600

        cur = conn.cursor()
        cur.execute(
            """UPDATE positions SET
                   status = 'closed', exit_time = %s, exit_price = %s,
                   exit_reason = %s, pnl_pct = %s, pnl_usd = %s,
                   hold_hours = %s
               WHERE id = %s""",
            (
                exit_time,
                exit_price,
                reason,
                round(pnl_pct, 6),
                round(pnl_usd, 4),
                round(hold_hours, 2),
                pos_id,
            ),
        )
    emoji = {
        "tp": "\U0001f3af",
        "sl": "\U0001f6d1",
        "sell_signal": "\U0001f4c9",
        "timeout": "\u23f0",
    }
    logger.info(
        "%s Closed #%d (%s): entry=$%.2f exit=$%.2f pnl=%+.2f%% ($%+.4f) hold=%.1fh",
        emoji.get(reason, "?"),
        pos_id,
        reason,
        entry_price,
        exit_price,
        pnl_pct * 100,
        pnl_usd,
        hold_hours,
    )


def get_open_positions(trader_id: int = None) -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(psycopg2.extras.RealDictCursor)
        if trader_id:
            cur.execute(
                "SELECT * FROM positions WHERE status = 'open' AND trader_id = %s",
                (trader_id,),
            )
        else:
            cur.execute("SELECT * FROM positions WHERE status = 'open'")
        return [dict(r) for r in cur.fetchall()]


def get_trades_summary(trader_id: int = None) -> dict:
    with get_conn() as conn:
        cur = conn.cursor(psycopg2.extras.RealDictCursor)
        where = "WHERE status = 'closed'"
        params = []
        if trader_id:
            where += " AND trader_id = %s"
            params.append(trader_id)
        cur.execute(
            f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE pnl_pct > 0) as wins,
                ROUND(AVG(pnl_pct)::numeric, 6) as avg_pnl,
                ROUND(SUM(pnl_pct)::numeric, 6) as total_pnl,
                ROUND(SUM(pnl_usd)::numeric, 4) as total_pnl_usd,
                ROUND(AVG(hold_hours)::numeric, 1) as avg_hold,
                ROUND(STDDEV(pnl_pct)::numeric, 6) as std_pnl
            FROM positions {where}
        """,
            params,
        )
        return dict(cur.fetchone())
