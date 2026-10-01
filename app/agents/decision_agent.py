"""Deterministic final decision and price levels."""
from __future__ import annotations

from app.schemas import DebateResult, DecisionResult, RiskResult, TechnicalResult
from app.scoring.scoring_engine import deterministic_confidence, recommendation_level, weighted_score


class DecisionAgent:
    def decide(self, symbol: str, price: float, technical: TechnicalResult, news: dict, sentiment_score: float, fundamental_score: float | None, risk: RiskResult, bull: DebateResult, bear: DebateResult, historical_win_rate: float | None = None, market_regime: dict | None = None) -> DecisionResult:
        debate = (bull.score + (10 - bear.score)) / 2
        values = {"technical": technical.score, "news": news.get("score"), "sentiment": sentiment_score, "fundamental": fundamental_score, "debate": debate, "risk": risk.risk_score}
        score = weighted_score(values, is_crypto=symbol.endswith("-USD"))
        regime_trend = (market_regime or {}).get("trend")
        score = round(max(0, min(10, score + (0.25 if regime_trend == "BULL TREND" else -0.25 if regime_trend == "BEAR TREND" else 0))), 2)
        available = sum(value is not None for value in values.values()) / len(values)
        confidence = deterministic_confidence(list(values.values()), technical.confidence, available, historical_win_rate)
        atr = technical.indicators.get("atr") or price * risk.suggested_stop_distance_percent / 180
        entry_min = max(0.01, price - atr * 0.45)
        entry_max = price + atr * 0.2
        stop_distance = max(atr * 1.5, price * risk.suggested_stop_distance_percent / 100)
        nearby_support = max(
            technical.indicators.get("sma_50") or 0,
            technical.indicators.get("bollinger_lower") or 0,
        )
        # ATR/risk distance is primary; a nearby moving support may tighten, but
        # never widen the stop toward a remote 52-week low.
        stop = max(0.01, price - stop_distance, nearby_support - atr * 0.25)
        stop = min(stop, price - max(atr * 0.5, price * 0.005))
        unit_risk = max(price - stop, atr)
        target_1 = price + unit_risk * 1.5
        target_2 = price + unit_risk * 2.5
        rr = (target_2 - price) / max(price - stop, 0.01)
        reasoning = (technical.signals + list(news.get("events", [])))[:6]
        if not reasoning: reasoning = ["No decisive catalyst; weighted evidence is near neutral"]
        return DecisionResult(symbol=symbol, recommendation=recommendation_level(score), score=score, confidence=confidence, entry_min=round(entry_min, 4), entry_max=round(entry_max, 4), stop_loss=round(stop, 4), target_1=round(target_1, 4), target_2=round(target_2, 4), risk_reward_ratio=round(rr, 2), reasoning=reasoning, risks=list(dict.fromkeys(risk.risks + news.get("risks", [])))[:6], bull_case="; ".join(bull.arguments), bear_case="; ".join(bear.arguments))
