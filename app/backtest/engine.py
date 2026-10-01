"""Vectorized backtest without lookahead signal construction."""
from __future__ import annotations

import pandas as pd

from app.backtest.metrics import calculate_metrics
from app.indicators.technical import calculate_indicators
from app.providers.base import MarketDataProvider
from app.schemas import BacktestRequest


class BacktestEngine:
    def __init__(self, provider: MarketDataProvider) -> None:
        self.provider = provider

    def run(self, request: BacktestRequest) -> dict:
        frame = calculate_indicators(self.provider.history(request.symbol, request.period))
        signal = frame["rsi"] < request.rsi_below
        if request.require_ema_trend: signal &= frame["ema_20"] > frame["ema_50"]
        signal &= frame["volume_ratio"] >= request.min_volume_ratio
        if request.require_macd_cross:
            signal &= (frame["macd"] > frame["macd_signal"]) & (frame["macd"].shift(1) <= frame["macd_signal"].shift(1))
        # Signal uses only data known at close t. Entry is next close t+1; this
        # conservatively avoids future leakage, though close execution is idealized.
        entries = frame.loc[signal].copy()
        entries["entry_price"] = frame["close"].shift(-1).reindex(entries.index)
        for days in (1, 5, 20):
            exits = frame["close"].shift(-(days + 1)).reindex(entries.index)
            entries[f"return_{days}d"] = (exits / entries["entry_price"] - 1) * 100
        trades = entries.dropna(subset=["entry_price", "return_20d"])
        return {"symbol": request.symbol.upper(), "strategy": request.model_dump(), "metrics": calculate_metrics(trades), "trades": [{"signal_date": str(index), "entry_price": round(float(row["entry_price"]), 4), "return_1d": round(float(row["return_1d"]), 3), "return_5d": round(float(row["return_5d"]), 3), "return_20d": round(float(row["return_20d"]), 3)} for index, row in trades.tail(100).iterrows()], "limitations": ["Historical constituents are not modeled; survivorship bias may remain.", "Prices are adjusted daily data and next-close execution is idealized."]}
