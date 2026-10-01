"""Independent bear case; it never consumes the bull conclusion."""
from app.schemas import DebateResult


class BearAgent:
    def analyze(self, evidence: dict) -> DebateResult:
        arguments = list(evidence.get("risks", []))
        risk_score = evidence.get("risk_score", 5)
        bearishness = risk_score * 0.5 + (10 - evidence.get("technical_score", 5)) * 0.35 + (10 - (evidence.get("news_score") or 5)) * 0.15
        return DebateResult(score=round(bearishness, 2), confidence=min(0.85, 0.4 + len(arguments) * 0.08), arguments=arguments[:5] or ["No strong bearish catalyst"], invalidations=list(evidence.get("technical_signals", []))[:4])
