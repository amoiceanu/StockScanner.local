"""News collection with URL-level deduplication."""
from sqlalchemy.orm import Session

from app.models import NewsArticle
from app.providers.news import RSSNewsProvider


class NewsCollector:
    def __init__(self, provider: RSSNewsProvider | None = None) -> None:
        self.provider = provider or RSSNewsProvider()

    def collect(self, symbol: str, db: Session) -> list[dict]:
        articles = self.provider.fetch(symbol)
        for item in articles:
            existing = db.query(NewsArticle.id).filter(NewsArticle.url == item["url"]).first()
            if not existing: db.add(NewsArticle(**item))
        db.flush()
        return articles
