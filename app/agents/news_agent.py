"""Deterministic news relevance/event pre-analysis."""
from __future__ import annotations

from datetime import datetime, timezone

EVENTS = {"earnings", "guidance", "acquisition", "merger", "lawsuit", "regulatory", "ceo", "contract", "launch", "upgrade", "downgrade", "offering", "buyback", "layoffs", "bankruptcy"}
POSITIVE = {"beat", "growth", "upgrade", "record", "buyback", "wins", "approval", "surge"}
NEGATIVE = {"miss", "downgrade", "lawsuit", "layoffs", "bankruptcy", "fraud", "decline", "offering"}


class NewsAgent:
    def analyze(self, articles: list[dict]) -> dict:
        if not articles:
            return {"score": 5.0, "confidence": 0.1, "events": [], "summary": "No recent news", "risks": []}
        weighted, total, events, risks = 0.0, 0.0, [], []
        now = datetime.now(timezone.utc)
        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            age_days = max(0, (now - (article.get("published_at") or now)).total_seconds() / 86400)
            recency = max(0.2, 1 - age_days / 14)
            delta = sum(word in text for word in POSITIVE) - sum(word in text for word in NEGATIVE)
            weighted += (5 + max(-3, min(3, delta))) * recency
            total += recency
            events.extend(event for event in EVENTS if event in text)
            if any(word in text for word in NEGATIVE): risks.append(article.get("title", "Negative news"))
        score = round(max(0, min(10, weighted / total)), 2) if total else 5.0
        return {"score": score, "confidence": round(min(0.85, 0.2 + len(articles) * 0.06), 2), "events": sorted(set(events)), "summary": f"{len(articles)} recent articles analyzed", "risks": risks[:3]}
