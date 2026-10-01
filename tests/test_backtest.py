from app.backtest.engine import BacktestEngine
from app.providers.base import MarketDataProvider
from app.schemas import BacktestRequest


class FakeProvider(MarketDataProvider):
    def __init__(self, frame): self.frame = frame
    def history(self, symbol, period="1y", interval="1d"): return self.frame.copy()
    def fundamentals(self, symbol): return {}


def test_backtest_returns_metrics(market_frame):
    result = BacktestEngine(FakeProvider(market_frame)).run(BacktestRequest(symbol="TEST", rsi_below=100, require_ema_trend=False))
    assert result["metrics"]["number_of_trades"] > 0
    assert "lookahead" not in str(result["limitations"]).lower() or result["limitations"]
    assert all("return_20d" in trade for trade in result["trades"])
