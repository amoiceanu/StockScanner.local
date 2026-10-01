"""Momentum-specific helpers."""
import pandas as pd


def rate_of_change(series: pd.Series, periods: int) -> pd.Series:
    return series.pct_change(periods) * 100
