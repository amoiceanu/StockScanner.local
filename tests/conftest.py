import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def market_frame():
    rng = np.random.default_rng(42)
    periods = 320
    index = pd.date_range("2024-01-01", periods=periods, freq="B", tz="UTC")
    close = pd.Series(100 + np.linspace(0, 35, periods) + rng.normal(0, 1, periods).cumsum() * 0.2, index=index)
    return pd.DataFrame({"open": close.shift(1).fillna(close.iloc[0]), "high": close + 1.5, "low": close - 1.5, "close": close, "volume": 1_000_000 + rng.integers(-100_000, 100_000, periods)}, index=index)
