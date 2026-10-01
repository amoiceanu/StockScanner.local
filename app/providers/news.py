"""Polite public RSS news collection."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser

logger = logging.getLogger(__name__)


class RSSNewsProvider:
    def fetch(self, symbol: str, limit: int = 15) -> list[dict]:
        url = f"https://news.google.com/rss/search?q={quote_plus(symbol + ' stock OR market')}&hl=en-US&gl=US&ceid=US:en"
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "TradingIntelligence/1.0 research"})
            articles = []
            for entry in feed.entries[:limit]:
                published = None
                if getattr(entry, "published_parsed", None):
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                articles.append({
                    "symbol": symbol,
                    "title": str(getattr(entry, "title", ""))[:500],
                    "source": str(getattr(getattr(entry, "source", None), "title", "Google News"))[:120],
                    "url": str(getattr(entry, "link", ""))[:1000],
                    "published_at": published,
                    "summary": str(getattr(entry, "summary", ""))[:3000],
                })
            return [article for article in articles if article["url"]]
        except Exception as exc:
            logger.warning("News provider error symbol=%s error=%s", symbol, type(exc).__name__)
            return []
