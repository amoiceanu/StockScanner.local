"""Retrying yfinance implementation behind a replaceable interface."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

from app.config import settings
from app.providers.base import MarketDataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    def __init__(self, cache_dir: Path | None = None, retries: int = 3) -> None:
        self.cache_dir = cache_dir or settings.cache_dir
        self.retries = retries
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, symbol: str, interval: str) -> Path:
        safe = symbol.replace("/", "_").replace("^", "idx_")
        return self.cache_dir / f"{safe}_{interval}.csv"

    def history(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        cache_path = self._cache_path(symbol, interval)
        cached = self._read_cache(cache_path)
        # Daily cache remains fresh until the next UTC day; intraday for 10 minutes.
        max_age = 86400 if interval == "1d" else 600
        if cache_path.exists() and time.time() - cache_path.stat().st_mtime < max_age and not cached.empty:
            return cached
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                data = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False, threads=False, timeout=20)
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                data.columns = [str(column).lower().replace(" ", "_") for column in data.columns]
                data.index = pd.to_datetime(data.index, utc=True)
                data = data[~data.index.duplicated(keep="last")].sort_index()
                if data.empty:
                    raise ValueError(f"No market data returned for {symbol}")
                # Merge protects future incremental provider implementations and avoids duplicate history.
                if not cached.empty:
                    data = pd.concat([cached, data]).loc[lambda frame: ~frame.index.duplicated(keep="last")].sort_index()
                data.to_csv(cache_path)
                return data
            except Exception as exc:
                last_error = exc
                logger.warning("Market provider error symbol=%s attempt=%s error=%s", symbol, attempt + 1, type(exc).__name__)
                if attempt + 1 < self.retries:
                    time.sleep(2**attempt)
        if not cached.empty:
            logger.warning("Using stale cache for %s", symbol)
            return cached
        raise RuntimeError(f"Market data unavailable for {symbol}") from last_error

    @staticmethod
    def _read_cache(path: Path) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()
        try:
            data = pd.read_csv(path, index_col=0, parse_dates=True)
            data.index = pd.to_datetime(data.index, utc=True)
            return data
        except Exception:
            return pd.DataFrame()

    def fundamentals(self, symbol: str) -> dict:
        for attempt in range(self.retries):
            try:
                return dict(yf.Ticker(symbol).info or {})
            except Exception as exc:
                logger.warning("Fundamentals provider error symbol=%s attempt=%s error=%s", symbol, attempt + 1, type(exc).__name__)
                if attempt + 1 < self.retries:
                    time.sleep(2**attempt)
        return {}
