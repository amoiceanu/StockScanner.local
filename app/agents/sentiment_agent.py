"""Cost-controlled structured AI sentiment with deterministic fallback."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.config import settings
from app.database import SessionLocal
from app.models import AIUsage
from app.schemas import SentimentResult

logger = logging.getLogger(__name__)


class SentimentAgent:
    def _allowed(self) -> bool:
        if not settings.ai_enabled or not settings.openai_api_key:
            return False
        now = datetime.now(timezone.utc)
        with SessionLocal() as db:
            hour = db.scalar(select(func.count(AIUsage.id)).where(AIUsage.timestamp >= now - timedelta(hours=1))) or 0
            day = db.scalar(select(func.count(AIUsage.id)).where(AIUsage.timestamp >= now - timedelta(days=1))) or 0
        allowed = hour < settings.max_ai_calls_per_hour and day < settings.max_ai_calls_per_day
        if not allowed: logger.info("AI skipped: configured usage limit reached")
        return allowed

    def analyze(self, articles: list[dict], rule_score: float = 5.0) -> SentimentResult:
        fallback = SentimentResult(sentiment="positive" if rule_score >= 6 else "negative" if rule_score < 4 else "neutral", score=rule_score, confidence=0.35 if articles else 0.1, summary="Rule-based fallback", risks=[])
        if not articles or not self._allowed():
            return fallback
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key, timeout=25, max_retries=2)
            compact = [{"title": item.get("title", ""), "published_at": str(item.get("published_at", ""))} for item in articles[:8]]
            logger.info("AI request purpose=news_sentiment model=%s", settings.ai_model)
            with SessionLocal() as db:
                usage_row = AIUsage(model=settings.ai_model, purpose="news_sentiment")
                db.add(usage_row); db.commit(); usage_id = usage_row.id
            response = client.responses.create(
                model=settings.ai_model,
                input=[{"role": "system", "content": "Analyze only supplied market news. Return compact JSON with sentiment, score 0-10, confidence 0-1, important_events, summary, risks."}, {"role": "user", "content": json.dumps(compact)}],
                text={"format": {"type": "json_schema", "name": "sentiment", "strict": True, "schema": SentimentResult.model_json_schema()}},
            )
            result = SentimentResult.model_validate_json(response.output_text)
            usage = getattr(response, "usage", None)
            with SessionLocal() as db:
                row = db.get(AIUsage, usage_id)
                if row:
                    row.prompt_tokens = getattr(usage, "input_tokens", 0) or 0
                    row.completion_tokens = getattr(usage, "output_tokens", 0) or 0
                db.commit()
            logger.info("AI response status=success purpose=news_sentiment")
            return result
        except Exception as exc:
            logger.warning("AI sentiment unavailable error=%s; using deterministic fallback", type(exc).__name__)
            return fallback

    @staticmethod
    def parse_response(raw: str) -> SentimentResult:
        """Explicit parsing seam used by tests and alternate providers."""
        return SentimentResult.model_validate_json(raw)
