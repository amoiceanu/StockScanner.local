"""End-to-end research pipeline shared by API, CLI and scheduler."""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.agents.bear_agent import BearAgent
from app.agents.bull_agent import BullAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.fundamental_agent import FundamentalAgent
from app.agents.market_regime import MarketRegimeClassifier
from app.agents.news_agent import NewsAgent
from app.agents.risk_agent import RiskAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.technical_agent import TechnicalAgent
from app.collectors.fundamentals_collector import persist_fundamentals
from app.collectors.market_collector import MarketCollector
from app.collectors.news_collector import NewsCollector
from app.config import settings
from app.database import SessionLocal
from app.indicators.technical import calculate_indicators
from app.models import AgentResult, FundamentalAnalysis, Instrument, NewsArticle, Recommendation, RecommendationPerformance, TechnicalAnalysis
from app.notifications.telegram import TelegramNotifier
from app.providers.market_data import YFinanceProvider
from app.scoring.scoring_engine import CandidateFilter
from app.schemas import DebateResult, RiskResult, SentimentResult, TechnicalResult
from app.utils.helpers import asset_type

logger = logging.getLogger(__name__)


def seed_instruments() -> None:
    with SessionLocal() as db:
        for symbol in settings.watchlist:
            if not db.scalar(select(Instrument).where(Instrument.symbol == symbol)):
                db.add(Instrument(symbol=symbol, name=symbol, asset_type=asset_type(symbol), enabled=True))
        db.commit()


class Scanner:
    def __init__(self, provider=None) -> None:
        self.provider = provider or YFinanceProvider()
        self.market = MarketCollector(self.provider)
        self.news_collector = NewsCollector()
        self.candidate_filter = CandidateFilter(settings.candidate_threshold)

    def scan(self, symbol: str, force_ai: bool = False) -> dict:
        started = time.monotonic(); symbol = symbol.upper().strip()
        logger.info("Scan start symbol=%s", symbol)
        with SessionLocal() as db:
            frame = self.market.collect(symbol, db)
            enriched = calculate_indicators(frame)
            technical = TechnicalAgent().analyze(enriched) if settings.enable_technical_agent else TechnicalResult(score=5, bias="neutral", confidence=.1, summary="Technical agent disabled")
            db.add(TechnicalAnalysis(symbol=symbol, technical_score=technical.score, details_json=technical.model_dump_json(), **{key: technical.indicators.get(key) for key in ("rsi", "macd", "macd_signal", "ema_20", "ema_50", "ema_200", "sma_20", "sma_50", "atr", "bollinger_upper", "bollinger_lower", "volume_ratio")}))
            interesting = self.candidate_filter.is_interesting(technical.score, technical.signals, force_ai)
            articles = self.news_collector.collect(symbol, db) if interesting and settings.enable_news_agent else []
            news = NewsAgent().analyze(articles) if settings.enable_news_agent else {"score": 5.0, "confidence": .1, "events": [], "summary": "News agent disabled", "risks": []}
            sentiment = self._sentiment_with_cache(articles, news["score"], db) if interesting and settings.enable_sentiment_agent else SentimentAgent().analyze([], 5)
            fundamental = self._fundamental_with_cache(symbol, db) if interesting and settings.enable_fundamental_agent else FundamentalAgent().analyze({}, symbol.endswith("-USD"))
            risk = RiskAgent().analyze(technical) if settings.enable_risk_agent else RiskResult(risk_score=5, risk_level="MEDIUM", suggested_stop_distance_percent=3, risks=[])
            evidence = {"technical_score": technical.score, "technical_signals": technical.signals, "news_score": news["score"], "fundamental_score": fundamental["score"], "risk_score": risk.risk_score, "risks": risk.risks + news["risks"]}
            # Independent calls consume exactly the same immutable evidence, never each other's output.
            if settings.enable_bull_bear_debate:
                bull, bear = BullAgent().analyze(evidence), BearAgent().analyze(evidence)
            else:
                bull = bear = DebateResult(score=5, confidence=.1, arguments=["Bull/bear debate disabled"], invalidations=[])
            history_rate = self._historical_rate(db, technical.score)
            regime = self._market_regime(symbol, frame)
            price = float(enriched.iloc[-1]["close"])
            decision = DecisionAgent().decide(symbol, price, technical, news, sentiment.score, fundamental["score"], risk, bull, bear, history_rate, regime)
            recommendation = Recommendation(symbol=symbol, price_at_signal=price, technical_score=technical.score, news_score=news["score"], sentiment_score=sentiment.score, fundamental_score=fundamental["score"], risk_score=risk.risk_score, bull_score=bull.score, bear_score=bear.score, final_score=decision.score, confidence=decision.confidence, recommendation=decision.recommendation, entry_min=decision.entry_min, entry_max=decision.entry_max, stop_loss=decision.stop_loss, target_1=decision.target_1, target_2=decision.target_2, risk_reward_ratio=decision.risk_reward_ratio, reasoning=json.dumps(decision.reasoning), risks=json.dumps(decision.risks))
            db.add(recommendation); db.flush(); db.add(RecommendationPerformance(recommendation_id=recommendation.id))
            for name, score, confidence, raw in (("technical", technical.score, technical.confidence, technical.model_dump()), ("news", news["score"], news["confidence"], news), ("sentiment", sentiment.score, sentiment.confidence, sentiment.model_dump()), ("risk", 10-risk.risk_score, technical.confidence, risk.model_dump()), ("bull", bull.score, bull.confidence, bull.model_dump()), ("bear", 10-bear.score, bear.confidence, bear.model_dump())):
                db.add(AgentResult(symbol=symbol, agent_name=name, score=score, confidence=confidence, recommendation=decision.recommendation, reasoning=str(raw.get("summary", "")), raw_json=json.dumps(raw, default=str)))
            db.commit()
            result = decision.model_dump() | {"price": price, "technical": technical.model_dump(), "news": news, "sentiment": sentiment.model_dump(), "fundamental": fundamental, "risk": risk.model_dump(), "market_regime": regime, "interesting_candidate": interesting}
        if abs(decision.score - 5) >= settings.min_notification_score - 5:
            TelegramNotifier().send(result)
        logger.info("Scan finish symbol=%s recommendation=%s score=%.2f runtime=%.2fs", symbol, decision.recommendation, decision.score, time.monotonic()-started)
        return result

    @staticmethod
    def _historical_rate(db, score: float) -> float | None:
        low = int(score); high = min(10, low + 1)
        rows = db.execute(select(Recommendation.final_score, Recommendation.recommendation, RecommendationPerformance.return_5d).join(RecommendationPerformance).where(Recommendation.final_score >= low, Recommendation.final_score < high, RecommendationPerformance.return_5d.is_not(None))).all()
        if len(rows) < 20: return None
        wins = sum((ret > 0) if "BUY" in rec or rec == "WATCH" else (ret < 0) for _, rec, ret in rows)
        return wins / len(rows)

    @staticmethod
    def _sentiment_with_cache(articles: list[dict], rule_score: float, db) -> SentimentResult:
        urls = [article["url"] for article in articles]
        stored = list(db.scalars(select(NewsArticle).where(NewsArticle.url.in_(urls)))) if urls else []
        scored = [article.sentiment_score for article in stored if article.sentiment_score is not None]
        if articles and len(scored) == len(articles):
            score = round(sum(scored) / len(scored), 2)
            return SentimentResult(sentiment="positive" if score >= 6 else "negative" if score < 4 else "neutral", score=score, confidence=0.65, summary="Reused cached article sentiment")
        result = SentimentAgent().analyze(articles, rule_score)
        by_url = {article.url: article for article in stored}
        for url in urls:
            row = by_url.get(url)
            if row:
                row.sentiment = result.sentiment; row.sentiment_score = result.score
        db.flush()
        return result

    def _market_regime(self, symbol: str, current_frame) -> dict:
        benchmark = "BTC-USD" if symbol.endswith("-USD") else "SPY"
        try:
            frame = current_frame if symbol == benchmark else self.provider.history(benchmark, "1y")
            return MarketRegimeClassifier().classify(frame)
        except Exception as exc:
            logger.warning("Market regime unavailable benchmark=%s error=%s", benchmark, type(exc).__name__)
            return {"trend": "SIDEWAYS", "volatility_regime": "NORMAL VOLATILITY", "volatility": 0}

    def _fundamental_with_cache(self, symbol: str, db) -> dict:
        if symbol.endswith("-USD"):
            return FundamentalAgent().analyze({}, True)
        cached = db.scalar(select(FundamentalAnalysis).where(FundamentalAnalysis.symbol == symbol).order_by(FundamentalAnalysis.timestamp.desc()))
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        if cached:
            timestamp = cached.timestamp.replace(tzinfo=timezone.utc) if cached.timestamp.tzinfo is None else cached.timestamp
            if timestamp >= cutoff:
                keys = ("market_cap", "pe_ratio", "forward_pe", "eps", "revenue_growth", "earnings_growth", "debt_to_equity", "free_cash_flow")
                return {"values": {key: getattr(cached, key) for key in keys}, "score": cached.fundamental_score, "summary": "Reused daily fundamental cache"}
        result = FundamentalAgent().analyze(self.provider.fundamentals(symbol), False)
        persist_fundamentals(symbol, result, db)
        return result

    def scan_all(self) -> list[dict]:
        with SessionLocal() as db:
            symbols = list(db.scalars(select(Instrument.symbol).where(Instrument.enabled.is_(True))))
        results = []
        for symbol in symbols:
            try: results.append(self.scan(symbol))
            except Exception as exc: logger.exception("Symbol scan failed symbol=%s error=%s", symbol, type(exc).__name__)
        return results
