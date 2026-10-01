import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AgentResult, Recommendation
from app.services import Scanner

router = APIRouter()


def _rec(row: Recommendation) -> dict:
    result = {column.name: getattr(row, column.name) for column in Recommendation.__table__.columns}
    for key in ("reasoning", "risks"):
        try: result[key] = json.loads(result[key] or "[]")
        except Exception: result[key] = []
    return result


@router.get("/recommendations")
def recommendations(limit: int = 100, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Recommendation).order_by(Recommendation.timestamp.desc()).limit(min(limit, 500)))
    return [_rec(row) for row in rows]


@router.get("/recommendations/{symbol}")
def recommendations_symbol(symbol: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Recommendation).where(Recommendation.symbol == symbol.upper()).order_by(Recommendation.timestamp.desc()).limit(100))
    return [_rec(row) for row in rows]


@router.get("/agents/{symbol}")
def agents(symbol: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(AgentResult).where(AgentResult.symbol == symbol.upper()).order_by(AgentResult.timestamp.desc()).limit(50))
    return [{column.name: getattr(row, column.name) for column in AgentResult.__table__.columns} for row in rows]


@router.post("/scan")
def scan_all() -> dict:
    results = Scanner().scan_all(); return {"scanned": len(results), "results": results}


@router.post("/scan/{symbol}")
def scan_symbol(symbol: str) -> dict:
    try: return Scanner().scan(symbol, force_ai=True)
    except Exception as exc: raise HTTPException(502, f"Scan failed: {type(exc).__name__}") from exc
