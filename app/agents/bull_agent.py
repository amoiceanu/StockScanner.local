"""Independent bull case constructed from the same normalized evidence."""
from app.schemas import DebateResult


class BullAgent:
    def analyze(self, evidence: dict) -> DebateResult:
        arguments = list(evidence.get("technical_signals", []))
        if (evidence.get("fundamental_score") or 0) >= 6: arguments.append("Supportive fundamentals")
        if (evidence.get("news_score") or 0) >= 6: arguments.append("Positive recent news flow")
        base = evidence.get("technical_score", 5) * 0.55 + (evidence.get("news_score") or 5) * 0.2 + (evidence.get("fundamental_score") or 5) * 0.25
        return DebateResult(score=round(base, 2), confidence=min(0.85, 0.4 + len(arguments) * 0.08), arguments=arguments[:5] or ["No strong bullish catalyst"], invalidations=list(evidence.get("risks", []))[:4])
