from app.agents.risk_agent import RiskAgent
from app.schemas import TechnicalResult


def test_high_volatility_increases_risk():
    technical = TechnicalResult(score=5, bias="neutral", confidence=.7, indicators={"volatility": 90, "atr": 8, "ema_20": 100, "drawdown": -25}, risks=[])
    result = RiskAgent().analyze(technical)
    assert result.risk_score >= 7
    assert result.risk_level in {"HIGH", "EXTREME"}
    assert result.suggested_stop_distance_percent > 5
