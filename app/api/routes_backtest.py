from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.backtest.engine import BacktestEngine
from app.database import get_db
from app.models import Recommendation, RecommendationPerformance
from app.providers.market_data import YFinanceProvider
from app.schemas import BacktestRequest

router = APIRouter()


@router.post("/backtest")
def backtest(request: BacktestRequest) -> dict:
    return BacktestEngine(YFinanceProvider()).run(request)


@router.get("/performance")
def performance(db: Session = Depends(get_db)) -> dict:
    total = db.scalar(select(func.count(Recommendation.id))) or 0
    returns = list(db.scalars(select(RecommendationPerformance.return_5d).where(RecommendationPerformance.return_5d.is_not(None))))
    return {"total_signals": total, "evaluated_5d": len(returns), "average_5d_return": round(sum(returns)/len(returns), 3) if returns else None}


@router.get("/performance/{symbol}")
def performance_symbol(symbol: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Recommendation, RecommendationPerformance).join(RecommendationPerformance).where(Recommendation.symbol == symbol.upper()).order_by(Recommendation.timestamp.desc())).all()
    return [{"recommendation_id": rec.id, "timestamp": rec.timestamp, "recommendation": rec.recommendation, "return_1h": perf.return_1h, "return_1d": perf.return_1d, "return_5d": perf.return_5d, "return_20d": perf.return_20d, "max_drawdown": perf.max_drawdown, "max_gain": perf.max_gain} for rec, perf in rows]
