"""Single-process APScheduler configuration for small servers."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, text

from app.config import settings
from app.database import SessionLocal
from app.models import Recommendation, RecommendationPerformance
from app.providers.market_data import YFinanceProvider
from app.services import Scanner

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="UTC", job_defaults={"coalesce": True, "max_instances": 1})


def scan_job() -> None:
    Scanner().scan_all()


def update_performance() -> None:
    provider = YFinanceProvider()
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        recommendations = list(db.scalars(select(Recommendation).where(Recommendation.timestamp >= now - timedelta(days=30))))
        for rec in recommendations:
            try:
                perf = rec.performance or RecommendationPerformance(recommendation_id=rec.id)
                age = now - rec.timestamp.replace(tzinfo=timezone.utc) if rec.timestamp.tzinfo is None else now - rec.timestamp
                daily = provider.history(rec.symbol, "1mo")
                future = daily[daily.index > rec.timestamp.replace(tzinfo=timezone.utc)]
                for days in (1, 5, 20):
                    if age >= timedelta(days=days) and len(future) >= days:
                        price = float(future.iloc[days-1]["close"]); setattr(perf, f"price_after_{days}d", price); setattr(perf, f"return_{days}d", (price / rec.price_at_signal - 1) * 100)
                if age >= timedelta(hours=1) and perf.price_after_1h is None:
                    intraday = provider.history(rec.symbol, "5d", "1h"); rows = intraday[intraday.index > rec.timestamp.replace(tzinfo=timezone.utc)]
                    if not rows.empty: perf.price_after_1h=float(rows.iloc[0]["close"]); perf.return_1h=(perf.price_after_1h/rec.price_at_signal-1)*100
                if not future.empty:
                    perf.max_drawdown=float((future["low"].min()/rec.price_at_signal-1)*100); perf.max_gain=float((future["high"].max()/rec.price_at_signal-1)*100)
                db.add(perf)
            except Exception as exc: logger.warning("Performance update failed id=%s error=%s", rec.id, type(exc).__name__)
        db.commit()


def database_maintenance() -> None:
    """Lightweight daily SQLite optimization and expired cache cleanup."""
    with SessionLocal() as db:
        db.execute(text("PRAGMA optimize")); db.commit()
    cutoff = time.time() - 45 * 86400
    for path in settings.cache_dir.glob("*.csv"):
        try:
            if path.is_file() and path.stat().st_mtime < cutoff: path.unlink()
        except OSError:
            logger.warning("Could not remove expired cache file=%s", path.name)


def start_scheduler() -> None:
    if scheduler.running: return
    scheduler.add_job(scan_job, "interval", minutes=settings.scan_interval_minutes, id="market_scan", replace_existing=True, next_run_time=datetime.now(timezone.utc)+timedelta(seconds=5))
    scheduler.add_job(update_performance, "interval", hours=1, id="performance", replace_existing=True)
    # Candidate news collection is part of market_scan; fundamental records are
    # reused for 24 hours. This avoids separate duplicate network passes.
    scheduler.add_job(database_maintenance, "interval", days=1, id="maintenance", replace_existing=True)
    scheduler.start(); logger.info("Scheduler started interval=%sm", settings.scan_interval_minutes)


def stop_scheduler() -> None:
    if scheduler.running: scheduler.shutdown(wait=False)
