"""Rule-based technical agent."""
from __future__ import annotations

import pandas as pd

from app.indicators.technical import latest_values
from app.schemas import TechnicalResult
from app.utils.helpers import clamp


class TechnicalAgent:
    def analyze(self, frame: pd.DataFrame) -> TechnicalResult:
        if len(frame) < 50:
            return TechnicalResult(score=5, bias="neutral", confidence=0.2, risks=["Insufficient history"], summary="Insufficient data")
        values = latest_values(frame)
        row = frame.iloc[-1]
        previous = frame.iloc[-2]
        score, signals, risks = 5.0, [], []
        rsi = values.get("rsi")
        if rsi is not None:
            if rsi < 30:
                score += 1.2; signals.append("RSI oversold")
            elif rsi > 70:
                score -= 1.2; risks.append("RSI overbought")
            elif 50 < rsi < 65:
                score += 0.4
        if row.get("ema_20", 0) > row.get("ema_50", 0) > row.get("ema_200", float("inf")):
            score += 1.4; signals.append("Trend bullish")
        elif row.get("ema_20", 0) < row.get("ema_50", 0) < row.get("ema_200", -float("inf")):
            score -= 1.4; risks.append("Trend bearish")
        if previous.get("ema_20", 0) <= previous.get("ema_50", 0) and row.get("ema_20", 0) > row.get("ema_50", 0):
            score += 0.8; signals.append("Golden cross EMA20/EMA50")
        if previous.get("ema_20", 0) >= previous.get("ema_50", 0) and row.get("ema_20", 0) < row.get("ema_50", 0):
            score -= 0.8; risks.append("Death cross EMA20/EMA50")
        if row.get("macd", 0) > row.get("macd_signal", 0):
            score += 0.5; signals.append("MACD bullish")
        else:
            score -= 0.5
        prior_high = frame["high"].iloc[-21:-1].max()
        prior_low = frame["low"].iloc[-21:-1].min()
        if row["close"] > prior_high:
            score += 0.9; signals.append("20-day breakout")
        elif row["close"] < prior_low:
            score -= 0.9; risks.append("20-day breakdown")
        if (values.get("volume_ratio") or 0) > 1.5:
            signals.append("Abnormal volume")
            score += 0.3 if (values.get("momentum_1d") or 0) > 0 else -0.3
        volatility = values.get("volatility") or 0
        if volatility > 60:
            risks.append("High volatility")
        score = round(clamp(score), 2)
        bias = "bullish" if score >= 6 else "bearish" if score < 4 else "neutral"
        completeness = sum(value is not None for value in values.values()) / max(len(values), 1)
        strength = min(abs(score - 5) / 5, 1)
        confidence = round(min(0.95, 0.35 + completeness * 0.35 + strength * 0.25), 2)
        return TechnicalResult(score=score, bias=bias, confidence=confidence, signals=signals, risks=risks, summary=f"{bias.title()} technical setup ({score}/10)", indicators=values)
