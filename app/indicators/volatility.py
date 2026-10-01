"""Volatility helpers."""
import numpy as np
import pandas as pd


def annualized_volatility(close: pd.Series, window: int = 20) -> pd.Series:
    return close.pct_change().rolling(window).std() * np.sqrt(252) * 100
