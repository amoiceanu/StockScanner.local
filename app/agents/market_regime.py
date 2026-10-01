"""Deterministic market-context classification infrastructure."""
from __future__ import annotations

import pandas as pd

from app.indicators.technical import calculate_indicators


class MarketRegimeClassifier:
    def classify(self, frame: pd.DataFrame) -> dict[str, str | float]:
        enriched = calculate_indicators(frame) if "ema_200" not in frame else frame
        row = enriched.iloc[-1]
        price, ema50, ema200 = float(row["close"]), float(row["ema_50"]), float(row["ema_200"])
        volatility = float(row["volatility"])
        trend = "BULL TREND" if price > ema50 > ema200 else "BEAR TREND" if price < ema50 < ema200 else "SIDEWAYS"
        volatility_regime = "HIGH VOLATILITY" if volatility >= 35 else "LOW VOLATILITY" if volatility <= 15 else "NORMAL VOLATILITY"
        return {"trend": trend, "volatility_regime": volatility_regime, "volatility": round(volatility, 2)}
