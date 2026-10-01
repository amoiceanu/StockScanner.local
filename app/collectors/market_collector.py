"""Market data collection and snapshot persistence."""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models import MarketSnapshot
from app.providers.base import MarketDataProvider


class MarketCollector:
    def __init__(self, provider: MarketDataProvider) -> None:
        self.provider = provider

    def collect(self, symbol: str, db: Session, period: str = "1y") -> pd.DataFrame:
        frame = self.provider.history(symbol, period=period)
        row = frame.iloc[-1]
        snapshot = MarketSnapshot(symbol=symbol, timestamp=frame.index[-1].to_pydatetime(), price=float(row["close"]), open=float(row.get("open", row["close"])), high=float(row["high"]), low=float(row["low"]), close=float(row["close"]), volume=float(row["volume"]))
        existing = db.query(MarketSnapshot).filter_by(symbol=symbol, timestamp=snapshot.timestamp).first()
        if not existing:
            db.add(snapshot); db.flush()
        return frame
