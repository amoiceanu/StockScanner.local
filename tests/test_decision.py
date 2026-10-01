from app.agents.decision_agent import DecisionAgent
from app.schemas import DebateResult, RiskResult, TechnicalResult


def test_price_levels_are_atr_based_and_ordered():
    tech = TechnicalResult(score=7, bias="bullish", confidence=.8, signals=["Trend bullish"], indicators={"atr": 5, "sma_50": 90, "bollinger_lower": 85, "low_52w": 40})
    risk = RiskResult(risk_score=5, risk_level="MEDIUM", suggested_stop_distance_percent=5, risks=[])
    bull = DebateResult(score=7, confidence=.7, arguments=["Momentum"], invalidations=[])
    bear = DebateResult(score=4, confidence=.6, arguments=["Volatility"], invalidations=[])
    result = DecisionAgent().decide("TEST", 100, tech, {"score": 5, "events": [], "risks": []}, 5, None, risk, bull, bear)
    assert 85 < result.stop_loss < result.entry_min < result.entry_max < result.target_1 < result.target_2
    assert result.stop_loss > 40  # remote 52-week low must not drive the stop
