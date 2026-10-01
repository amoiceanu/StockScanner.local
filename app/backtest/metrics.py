"""Backtest performance metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"number_of_trades": 0, "win_rate": 0.0, "average_return": 0.0, "median_return": 0.0, "profit_factor": 0.0, "max_drawdown": 0.0, "sharpe_ratio": None, "return_1d": 0.0, "return_5d": 0.0, "return_20d": 0.0}
    returns = trades["return_5d"].dropna()
    gains, losses = returns[returns > 0].sum(), abs(returns[returns < 0].sum())
    equity = (1 + returns / 100).cumprod()
    drawdown = (equity / equity.cummax() - 1).min() * 100
    sharpe = None if len(returns) < 10 or returns.std() == 0 else float(returns.mean() / returns.std() * np.sqrt(252 / 5))
    return {"number_of_trades": int(len(trades)), "win_rate": round(float((returns > 0).mean() * 100), 2), "average_return": round(float(returns.mean()), 3), "median_return": round(float(returns.median()), 3), "profit_factor": round(float(gains / losses), 3) if losses else None, "max_drawdown": round(float(drawdown), 3), "sharpe_ratio": None if sharpe is None else round(sharpe, 3), **{f"return_{days}d": round(float(trades[f'return_{days}d'].mean()), 3) for days in (1, 5, 20)}}
