"""Volume helpers."""
import pandas as pd


def volume_ratio(volume: pd.Series, window: int = 20) -> pd.Series:
    return volume / volume.rolling(window).mean().replace(0, float("nan"))
