"""Deterministic risk assessment."""
from app.schemas import RiskResult, TechnicalResult
from app.utils.helpers import clamp


class RiskAgent:
    def analyze(self, technical: TechnicalResult) -> RiskResult:
        values = technical.indicators
        volatility = values.get("volatility") or 25
        atr = values.get("atr") or 0
        ema20 = values.get("ema_20") or 0
        atr_percent = (atr / ema20 * 100) if ema20 else 2.0
        drawdown = abs(min(values.get("drawdown") or 0, 0))
        risk = 2.0 + min(volatility / 20, 3.5) + min(drawdown / 15, 2) + min(atr_percent / 3, 2)
        risks = list(technical.risks)
        if drawdown > 20: risks.append("Deep recent drawdown")
        if atr_percent > 5: risks.append("Wide daily range")
        score = round(clamp(risk), 2)
        level = "EXTREME" if score >= 8.5 else "HIGH" if score >= 6.5 else "MEDIUM" if score >= 3.5 else "LOW"
        return RiskResult(risk_score=score, risk_level=level, risks=list(dict.fromkeys(risks)), suggested_stop_distance_percent=round(max(1.5, min(12, atr_percent * 1.8)), 2))
