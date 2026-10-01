from app.agents.market_regime import MarketRegimeClassifier


def test_market_regime_classification(market_frame):
    regime = MarketRegimeClassifier().classify(market_frame)
    assert regime["trend"] in {"BULL TREND", "BEAR TREND", "SIDEWAYS"}
    assert regime["volatility_regime"] in {"HIGH VOLATILITY", "LOW VOLATILITY", "NORMAL VOLATILITY"}
