"""Weighted decision scoring with missing-data redistribution."""
from __future__ import annotations

from app.utils.helpers import clamp

LEVELS = [
    (9.0, "STRONG BUY"), (7.5, "BUY"), (6.0, "WATCH"),
    (4.0, "HOLD"), (2.5, "REDUCE"), (1.0, "SELL"), (0.0, "STRONG SELL"),
]


def recommendation_level(score: float) -> str:
    return next(label for threshold, label in LEVELS if score >= threshold)


class CandidateFilter:
    """Keeps AI costs bounded by selecting only notable deterministic setups."""
    def __init__(self, threshold: float = 6.0) -> None:
        self.threshold = threshold

    def is_interesting(self, technical_score: float, signals: list[str], force: bool = False) -> bool:
        return force or technical_score >= self.threshold or technical_score <= 10 - self.threshold or any("break" in signal.lower() or "cross" in signal.lower() for signal in signals)


def weighted_score(values: dict[str, float | None], is_crypto: bool = False) -> float:
    weights = {"technical": 0.30, "news": 0.15, "sentiment": 0.10, "fundamental": 0.20, "debate": 0.15, "risk": 0.10}
    if is_crypto:
        weights = {"technical": 0.42, "news": 0.18, "sentiment": 0.15, "fundamental": 0.0, "debate": 0.15, "risk": 0.10}
    usable = {key: weight for key, weight in weights.items() if weight > 0 and values.get(key) is not None}
    total = sum(usable.values())
    if total == 0:
        return 5.0
    # Risk is inverted: high risk reduces the bullish score.
    numerator = sum(((10 - values[key]) if key == "risk" else values[key]) * weight for key, weight in usable.items())  # type: ignore[operator]
    return round(clamp(numerator / total), 2)


def deterministic_confidence(scores: list[float | None], technical_confidence: float, data_quality: float, historical_win_rate: float | None = None) -> float:
    """Confidence = agreement 35% + data quality 25% + technical strength 25% + calibration 15%.

    Agent agreement uses inverse normalized standard deviation. If enough historical
    outcomes exist, their win rate caps optimism rather than allowing an LLM to invent it.
    """
    available = [score for score in scores if score is not None]
    if not available:
        return 0.1
    mean = sum(available) / len(available)
    variance = sum((score - mean) ** 2 for score in available) / len(available)
    agreement = max(0, 1 - variance**0.5 / 5)
    calibration = historical_win_rate if historical_win_rate is not None else 0.55
    confidence = agreement * 0.35 + data_quality * 0.25 + technical_confidence * 0.25 + calibration * 0.15
    if historical_win_rate is not None:
        confidence = min(confidence, historical_win_rate + 0.12)
    return round(max(0.1, min(0.95, confidence)), 2)
