from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Instrument, MarketSnapshot, TechnicalAnalysis
from app.utils.helpers import asset_type

router = APIRouter()


class InstrumentInput(BaseModel):
    symbol: str
    name: str | None = None


@router.get("/instruments")
def instruments(db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": item.id, "symbol": item.symbol, "name": item.name, "asset_type": item.asset_type, "enabled": item.enabled} for item in db.scalars(select(Instrument).order_by(Instrument.symbol))]


@router.post("/instruments", status_code=201)
def add_instrument(payload: InstrumentInput, db: Session = Depends(get_db)) -> dict:
    symbol = payload.symbol.upper().strip()
    if not symbol or len(symbol) > 32: raise HTTPException(400, "Invalid symbol")
    item = db.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if item: item.enabled = True
    else: item = Instrument(symbol=symbol, name=payload.name or symbol, asset_type=asset_type(symbol), enabled=True); db.add(item)
    db.commit(); db.refresh(item)
    return {"symbol": item.symbol, "enabled": item.enabled}


@router.patch("/instruments/{symbol}")
def toggle_instrument(symbol: str, enabled: bool, db: Session = Depends(get_db)) -> dict:
    item = db.scalar(select(Instrument).where(Instrument.symbol == symbol.upper()))
    if not item: raise HTTPException(404, "Instrument not found")
    item.enabled = enabled; db.commit(); return {"symbol": item.symbol, "enabled": item.enabled}


@router.delete("/instruments/{symbol}")
def remove_instrument(symbol: str, db: Session = Depends(get_db)) -> dict:
    item = db.scalar(select(Instrument).where(Instrument.symbol == symbol.upper()))
    if not item: raise HTTPException(404, "Instrument not found")
    db.delete(item); db.commit(); return {"removed": symbol.upper()}


@router.get("/market/{symbol}")
def market(symbol: str, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(select(MarketSnapshot).where(MarketSnapshot.symbol == symbol.upper()).order_by(MarketSnapshot.timestamp.desc()))
    if not row: raise HTTPException(404, "No market snapshot")
    return {key: getattr(row, key) for key in ("symbol", "timestamp", "price", "open", "high", "low", "close", "volume")}


@router.get("/analysis/{symbol}")
def analysis(symbol: str, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(select(TechnicalAnalysis).where(TechnicalAnalysis.symbol == symbol.upper()).order_by(TechnicalAnalysis.timestamp.desc()))
    if not row: raise HTTPException(404, "No analysis")
    return {column.name: getattr(row, column.name) for column in TechnicalAnalysis.__table__.columns}
