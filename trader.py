"""Trader classes -- model loading and signal generation."""
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import config
import db

logger = logging.getLogger(__name__)


class BaseTrader(ABC):
    """Base class for all traders."""

    def __init__(self, trader_row: dict):
        self.id = trader_row["id"]
        self.name = trader_row["name"]
        self.model_type = trader_row["model_type"]
        self.features = trader_row["features"] or []
        self.strategy = trader_row["strategy"]
        self.tp = self.strategy.get("tp", 0.04)
        self.sl = self.strategy.get("sl", -0.04)
        self.max_hold = self.strategy.get("max_hold", 72)
        self.min_confidence = self.strategy.get("min_confidence", 0.8)
        self.amount_usd = self.strategy.get("amount_usd", config.DEFAULT_AMOUNT_USD)

    @abstractmethod
    def predict(self, features_row: pd.DataFrame) -> tuple[str, float]:
        """Return (signal, confidence). Signal in ['BUY', 'SELL', 'HOLD']."""

    def on_new_candle(self, features_df: pd.DataFrame, current_price: float, now: datetime):
        """Called every hour with computed features."""
        signal, confidence = self.predict(features_df)

        logger.info(
            "[%s] Signal: %s (conf=%.3f) @ $%.2f",
            self.name, signal, confidence, current_price,
        )

        # SELL -> close all open positions
        if signal == "SELL":
            open_positions = db.get_open_positions(self.id)
            for pos in open_positions:
                db.close_position(
                    pos["id"], now, current_price,
                    reason="sell_signal", fee_pct=config.FEE_PCT,
                )

        # BUY -> open new position if confidence is high enough
        if signal == "BUY" and confidence >= self.min_confidence:
            db.open_position(
                trader_id=self.id,
                entry_time=now,
                entry_price=current_price,
                amount_usd=self.amount_usd,
                confidence=confidence,
            )

    def check_positions(self, current_price: float, now: datetime):
        """Check TP/SL/timeout for open positions."""
        open_positions = db.get_open_positions(self.id)
        for pos in open_positions:
            entry_price = float(pos["entry_price"])
            pnl_pct = (current_price - entry_price) / entry_price
            hold_hours = (now - pos["entry_time"]).total_seconds() / 3600

            if pnl_pct <= self.sl:
                exit_price = entry_price * (1 + self.sl)
                db.close_position(
                    pos["id"], now, exit_price,
                    reason="sl", fee_pct=config.FEE_PCT,
                )
            elif pnl_pct >= self.tp:
                exit_price = entry_price * (1 + self.tp)
                db.close_position(
                    pos["id"], now, exit_price,
                    reason="tp", fee_pct=config.FEE_PCT,
                )
            elif hold_hours >= self.max_hold:
                db.close_position(
                    pos["id"], now, current_price,
                    reason="timeout", fee_pct=config.FEE_PCT,
                )


class XGBoostTrader(BaseTrader):
    """Trader using a trained XGBoost model."""

    INV_MAP = {0: -1, 1: 0, 2: 1}
    SIGNAL_NAMES = {-1: "SELL", 0: "HOLD", 1: "BUY"}

    def __init__(self, trader_row: dict):
        super().__init__(trader_row)
        model_path = trader_row.get("model_path", "")
        if model_path:
            model_dir = Path(model_path)
            self.model = joblib.load(model_dir / "model.joblib")
            with open(model_dir / "metadata.json") as f:
                self.meta = json.load(f)
            self.features = self.meta["features"]
            logger.info(
                "[%s] Loaded XGBoost: %d features, test F1=%.4f",
                self.name, len(self.features), self.meta.get("test_f1_macro", 0),
            )
        else:
            raise ValueError(f"No model_path for trader {self.name}")

    def predict(self, features_df: pd.DataFrame) -> tuple[str, float]:
        available = [f for f in self.features if f in features_df.columns]
        X = features_df[available].iloc[[-1]]  # last row
        pred = self.model.predict(X)[0]
        proba = self.model.predict_proba(X)[0]
        signal_code = self.INV_MAP[pred]
        signal = self.SIGNAL_NAMES[signal_code]
        confidence = float(proba.max())
        return signal, confidence


class RandomTrader(BaseTrader):
    """Random buy baseline -- buys randomly, no model."""

    def __init__(self, trader_row: dict):
        super().__init__(trader_row)
        self.buy_probability = self.strategy.get("buy_probability", 0.05)
        self.rng = np.random.RandomState(42)

    def predict(self, features_df: pd.DataFrame) -> tuple[str, float]:
        if self.rng.random() < self.buy_probability:
            return "BUY", 1.0
        return "HOLD", 1.0


def create_trader(trader_row: dict) -> BaseTrader:
    """Factory: create trader by model_type."""
    model_type = trader_row["model_type"]
    if model_type == "XGBoost":
        return XGBoostTrader(trader_row)
    elif model_type == "Random":
        return RandomTrader(trader_row)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
