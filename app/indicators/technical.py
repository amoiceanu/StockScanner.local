"""Technical calculations. LLMs are deliberately absent from this module."""
from __future__ import annotations

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands


def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    required = {"high", "low", "close", "volume"}
    if not required.issubset(data.columns):
        raise ValueError(f"Missing OHLCV columns: {sorted(required - set(data.columns))}")
    frame = data.copy().astype({column: "float64" for column in required})
    close, high, low, volume = frame["close"], frame["high"], frame["low"], frame["volume"]
    frame["rsi"] = RSIIndicator(close, window=14).rsi()
    macd = MACD(close)
    frame["macd"] = macd.macd()
    frame["macd_signal"] = macd.macd_signal()
    for window in (20, 50, 200):
        frame[f"ema_{window}"] = EMAIndicator(close, window=window).ema_indicator()
    for window in (20, 50):
        frame[f"sma_{window}"] = SMAIndicator(close, window=window).sma_indicator()
    frame["atr"] = AverageTrueRange(high, low, close, window=14).average_true_range()
    bands = BollingerBands(close, window=20, window_dev=2)
    frame["bollinger_upper"] = bands.bollinger_hband()
    frame["bollinger_lower"] = bands.bollinger_lband()
    frame["volume_average"] = volume.rolling(20).mean()
    frame["volume_ratio"] = volume / frame["volume_average"].replace(0, np.nan)
    frame["high_52w"] = high.rolling(252, min_periods=50).max()
    frame["low_52w"] = low.rolling(252, min_periods=50).min()
    frame["distance_52w_high"] = (close / frame["high_52w"] - 1) * 100
    for days in (1, 5, 20):
        frame[f"momentum_{days}d"] = close.pct_change(days) * 100
    frame["volatility"] = close.pct_change().rolling(20).std() * np.sqrt(252) * 100
    frame["drawdown"] = (close / close.rolling(252, min_periods=20).max() - 1) * 100
    return frame


def latest_values(frame: pd.DataFrame) -> dict[str, float | None]:
    if frame.empty:
        return {}
    row = frame.iloc[-1]
    keys = ["rsi", "macd", "macd_signal", "ema_20", "ema_50", "ema_200", "sma_20", "sma_50", "atr", "bollinger_upper", "bollinger_lower", "volume_average", "volume_ratio", "high_52w", "low_52w", "distance_52w_high", "momentum_1d", "momentum_5d", "momentum_20d", "volatility", "drawdown"]
    return {key: None if key not in row or pd.isna(row[key]) else round(float(row[key]), 6) for key in keys}
