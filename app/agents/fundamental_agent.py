"""Fundamental agent facade."""
from app.providers.fundamentals import normalize_fundamentals, score_fundamentals


class FundamentalAgent:
    def analyze(self, raw: dict, is_crypto: bool = False) -> dict:
        if is_crypto:
            return {"values": {}, "score": None, "summary": "Not applicable to crypto"}
        values = normalize_fundamentals(raw)
        score = score_fundamentals(values)
        return {"values": values, "score": score, "summary": "Fundamental data unavailable" if score is None else f"Fundamental score {score}/10"}
