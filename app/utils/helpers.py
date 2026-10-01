"""Small shared helpers."""
from __future__ import annotations

import math
from typing import Any


def finite(value: Any, default: float | None = None) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def asset_type(symbol: str) -> str:
    if symbol.upper().endswith("-USD"):
        return "crypto"
    if symbol.upper() in {"SPY", "QQQ", "DIA", "IWM", "VTI", "VOO"}:
        return "etf"
    return "stock"
