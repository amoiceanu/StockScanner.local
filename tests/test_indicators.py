from app.agents.technical_agent import TechnicalAgent
from app.indicators.technical import calculate_indicators


def test_indicators_and_agent(market_frame):
    result = calculate_indicators(market_frame)
    assert result.iloc[-1]["rsi"] > 0
    assert result.iloc[-1]["ema_200"] > 0
    assert result.iloc[-1]["atr"] > 0
    assert "volume_ratio" in result
    analysis = TechnicalAgent().analyze(result)
    assert 0 <= analysis.score <= 10
    assert 0 <= analysis.confidence <= 1


def test_missing_columns_rejected(market_frame):
    try:
        calculate_indicators(market_frame.drop(columns="volume"))
        assert False
    except ValueError as exc:
        assert "volume" in str(exc)
