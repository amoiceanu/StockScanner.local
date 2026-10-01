"""Fundamental persistence."""
from sqlalchemy.orm import Session

from app.models import FundamentalAnalysis


def persist_fundamentals(symbol: str, analysis: dict, db: Session) -> None:
    values = analysis.get("values", {})
    db.add(FundamentalAnalysis(symbol=symbol, fundamental_score=analysis.get("score"), **values))
