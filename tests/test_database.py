from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Instrument, NewsArticle


def test_database_models_and_news_deduplication(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Instrument(symbol="TEST", name="Test", asset_type="stock")); db.commit()
        assert db.scalar(select(Instrument).where(Instrument.symbol == "TEST")) is not None
        db.add(NewsArticle(symbol="TEST", title="One", url="https://example.test/1")); db.commit()
        assert len(list(db.scalars(select(NewsArticle)))) == 1
