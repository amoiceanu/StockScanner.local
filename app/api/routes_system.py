from datetime import datetime, timezone

from fastapi import APIRouter

from app.scheduler.jobs import scheduler
from app.utils.datetime import market_status

router = APIRouter()


@router.get("/health")
def health() -> dict:
    job = scheduler.get_job("market_scan") if scheduler.running else None
    return {"status": "ok", "research_only": True, "market_status": market_status(), "utc_time": datetime.now(timezone.utc), "scheduler_running": scheduler.running, "next_scan": job.next_run_time if job else None}
