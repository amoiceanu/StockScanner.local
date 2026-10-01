"""Fundamental normalization and deterministic scoring."""
from app.utils.helpers import clamp, finite


def normalize_fundamentals(raw: dict) -> dict:
    return {
        "market_cap": finite(raw.get("marketCap")),
        "pe_ratio": finite(raw.get("trailingPE")),
        "forward_pe": finite(raw.get("forwardPE")),
        "eps": finite(raw.get("trailingEps")),
        "revenue_growth": finite(raw.get("revenueGrowth")),
        "earnings_growth": finite(raw.get("earningsGrowth")),
        "debt_to_equity": finite(raw.get("debtToEquity")),
        "free_cash_flow": finite(raw.get("freeCashflow")),
    }


def score_fundamentals(values: dict) -> float | None:
    available = [value for value in values.values() if value is not None]
    if len(available) < 2:
        return None
    score = 5.0
    pe = values.get("forward_pe") or values.get("pe_ratio")
    if pe is not None:
        score += 1 if 0 < pe < 25 else (-1 if pe < 0 or pe > 60 else 0)
    for key in ("revenue_growth", "earnings_growth"):
        growth = values.get(key)
        if growth is not None:
            score += 0.8 if growth > 0.1 else (-0.8 if growth < 0 else 0)
    fcf = values.get("free_cash_flow")
    if fcf is not None:
        score += 0.7 if fcf > 0 else -0.7
    debt = values.get("debt_to_equity")
    if debt is not None:
        score += 0.5 if debt < 100 else (-0.7 if debt > 250 else 0)
    return round(clamp(score), 2)
