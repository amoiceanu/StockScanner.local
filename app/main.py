"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes_backtest import router as backtest_router
from app.api.routes_market import router as market_router
from app.api.routes_signals import router as signals_router
from app.api.routes_system import router as system_router
from app.config import settings
from app.database import init_db
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.services import seed_instruments
from app.utils.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db(); seed_instruments(); start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Trading Intelligence", version="1.0.0", description="Research-only market analysis. No trade execution endpoints exist.", lifespan=lifespan)
app.include_router(system_router)
app.include_router(market_router)
app.include_router(signals_router)
app.include_router(backtest_router)
app.mount("/static", StaticFiles(directory=settings.base_dir / "app" / "static"), name="static")
templates = Jinja2Templates(directory=settings.base_dir / "app" / "templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"timezone": settings.display_timezone})


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, workers=1)
