"""Compute features from candle history.

Self-contained feature computation (no Velma dependency).
Reimplements the core calculations needed by trading models.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _atr(high, low, close, period=14):
    tr = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period).mean()


def _natr(high, low, close, period=14):
    return _atr(high, low, close, period) / close * 100


def _mfi(high, low, close, volume, period=14):
    tp = (high + low + close) / 3
    mf = tp * volume
    pos = mf.where(tp > tp.shift(), 0).rolling(period).sum()
    neg = mf.where(tp < tp.shift(), 0).rolling(period).sum()
    ratio = pos / neg.replace(0, np.nan)
    return 100 - (100 / (1 + ratio))


def _bb_width(close, period=20, std_mult=2):
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + std_mult * std
    lower = sma - std_mult * std
    return (upper - lower) / sma


def _stoch(high, low, close, period=14, smooth=3):
    lowest_low = low.rolling(period).min()
    highest_high = high.rolling(period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    return k.rolling(smooth).mean()


def _nmacd(close, fast=12, slow=26, signal=9):
    macd = _ema(close, fast) - _ema(close, slow)
    sig = _ema(macd, signal)
    hist = macd - sig
    return macd / close * 100, sig / close * 100, hist / close * 100


def _hh_ratio(high, period):
    return high / high.rolling(period).max()


def _hl_ratio(low, high, period):
    return low / high.rolling(period).max()


def _hh_div(high, rsi, period):
    price_hh = high / high.rolling(period).max()
    rsi_norm = rsi / rsi.rolling(period).max().replace(0, np.nan)
    return price_hh - rsi_norm


def _roc(close, period):
    return close.pct_change(period) * 100


def _sma_ratio(close, period):
    return close / _sma(close, period)


def _ema_ratio(close, period):
    return close / _ema(close, period)


def _funding_features(funding_rates: list[float]) -> dict:
    """Compute funding rate features from the latest funding rates."""
    if not funding_rates:
        return {
            "funding_rate": np.nan,
            "funding_rate_sma_8": np.nan,
            "funding_rate_zscore_30": np.nan,
            "funding_rate_streak": 0,
            "funding_rate_cumsum_7d": np.nan,
        }

    fr = pd.Series(funding_rates)
    latest = fr.iloc[-1]
    sma_8 = fr.tail(8).mean() if len(fr) >= 8 else fr.mean()

    if len(fr) >= 30:
        mean30 = fr.tail(30).mean()
        std30 = fr.tail(30).std()
        zscore = (latest - mean30) / std30 if std30 > 0 else 0
    else:
        zscore = 0

    # Streak
    streak = 0
    for val in reversed(fr.tolist()):
        if val > 0:
            if streak >= 0:
                streak += 1
            else:
                break
        elif val < 0:
            if streak <= 0:
                streak -= 1
            else:
                break
        else:
            break

    cumsum_7d = fr.tail(21).sum() if len(fr) >= 21 else fr.sum()

    return {
        "funding_rate": latest,
        "funding_rate_sma_8": sma_8,
        "funding_rate_zscore_30": zscore,
        "funding_rate_streak": streak,
        "funding_rate_cumsum_7d": cumsum_7d,
    }


def compute_features(
    df: pd.DataFrame, funding_rates: list[float] = None
) -> pd.DataFrame:
    """Compute all features from OHLCV candle DataFrame.

    Returns DataFrame with feature columns appended.
    Expects df sorted by open_time ascending with columns:
    open_time, open, high, low, close, volume
    """
    _o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"]

    # 1h features
    rsi = _rsi(c, 14)
    nmacd, nmacd_sig, nmacd_hist = _nmacd(c)

    feat = pd.DataFrame(index=df.index)
    feat["rsi_14"] = rsi
    feat["natr_14"] = _natr(h, l, c, 14)
    feat["mfi_14"] = _mfi(h, l, c, v, 14)
    feat["bb_width_20"] = _bb_width(c, 20)
    feat["nmacd_signal"] = nmacd_sig
    feat["nmacd_hist"] = nmacd_hist

    for p in [50, 100, 200]:
        feat[f"sma_ratio_{p}"] = _sma_ratio(c, p)
        feat[f"ema_ratio_{p}"] = _ema_ratio(c, p)

    for p in [7, 14, 21]:
        feat[f"hh_ratio_{p}"] = _hh_ratio(h, p)
        feat[f"hl_ratio_{p}"] = _hl_ratio(l, h, p)
        feat[f"hh_div_{p}"] = _hh_div(h, rsi, p)

    feat["roc_21"] = _roc(c, 21)
    feat["stoch_d_14"] = _stoch(h, l, c, 14)

    # 4h features (resample)
    df_ts = df.copy()
    df_ts["open_time"] = pd.to_datetime(df_ts["open_time"], utc=True)
    df4h = (
        df_ts.set_index("open_time")
        .resample("4h")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
    )

    if len(df4h) > 50:
        h4, l4, c4, v4 = df4h["high"], df4h["low"], df4h["close"], df4h["volume"]
        rsi4 = _rsi(c4, 14)
        nmacd4, nmacd_sig4, nmacd_hist4 = _nmacd(c4)

        feat4h = pd.DataFrame(index=df4h.index)
        feat4h["tf4h_natr_14"] = _natr(h4, l4, c4, 14)
        feat4h["tf4h_mfi_14"] = _mfi(h4, l4, c4, v4, 14)
        feat4h["tf4h_bb_width_20"] = _bb_width(c4, 20)
        feat4h["tf4h_nmacd_signal"] = nmacd_sig4
        feat4h["tf4h_nmacd_hist"] = nmacd_hist4
        feat4h["tf4h_stoch_d_14"] = _stoch(h4, l4, c4, 14)
        feat4h["tf4h_roc_21"] = _roc(c4, 21)

        for p in [50, 100, 200]:
            feat4h[f"tf4h_sma_ratio_{p}"] = _sma_ratio(c4, p)
            feat4h[f"tf4h_ema_ratio_{p}"] = _ema_ratio(c4, p)

        for p in [7, 14, 21]:
            feat4h[f"tf4h_hh_ratio_{p}"] = _hh_ratio(h4, p)
            feat4h[f"tf4h_hl_ratio_{p}"] = _hl_ratio(l4, h4, p)
            feat4h[f"tf4h_hh_div_{p}"] = _hh_div(h4, rsi4, p)

        # Merge 4h -> 1h (forward fill)
        feat4h_1h = feat4h.reindex(
            pd.to_datetime(df["open_time"], utc=True), method="ffill"
        )
        feat4h_1h.index = df.index
        feat = pd.concat([feat, feat4h_1h], axis=1)

    # Funding features
    if funding_rates:
        ff = _funding_features(funding_rates)
        for k, val in ff.items():
            feat[k] = val

    return feat
