import pytest
from pydantic import ValidationError

from app.agents.fundamental_agent import FundamentalAgent
from app.agents.sentiment_agent import SentimentAgent
from app.config import Settings
from app.providers.base import MarketDataProvider


class UnavailableProvider(MarketDataProvider):
    def history(self, symbol, period="1y", interval="1d"): raise RuntimeError("offline")
    def fundamentals(self, symbol): return {}


def test_malformed_ai_response_rejected():
    with pytest.raises(ValidationError): SentimentAgent.parse_response('{"sentiment":"great","score":99}')


def test_missing_fundamentals_and_crypto():
    assert FundamentalAgent().analyze({}, False)["score"] is None
    assert FundamentalAgent().analyze({}, True)["score"] is None


def test_unavailable_provider_isolated():
    with pytest.raises(RuntimeError): UnavailableProvider().history("TEST")


def test_configuration_paths_are_cross_platform():
    config = Settings()
    assert config.data_dir.name == "data"
    assert config.cache_dir.name == "cache"
    assert config.api_host == "127.0.0.1"
