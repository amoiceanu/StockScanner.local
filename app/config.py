"""Cross-platform environment configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: str) -> list[str]:
    return [item.strip().upper() for item in os.getenv(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    cache_dir: Path = BASE_DIR / "data" / "cache"
    logs_dir: Path = BASE_DIR / "logs"
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/trading.db"))
    watchlist: list[str] = field(default_factory=lambda: _list("WATCHLIST", "AAPL,MSFT,NVDA,GOOGL,AMZN,META,AMD,AVGO,TSLA,SPY,QQQ,BTC-USD,ETH-USD"))
    scan_interval_minutes: int = field(default_factory=lambda: int(os.getenv("SCAN_INTERVAL_MINUTES", "15")))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    ai_model: str = field(default_factory=lambda: os.getenv("AI_MODEL", "gpt-4.1-mini"))
    ai_enabled: bool = field(default_factory=lambda: _bool("AI_ENABLED", True))
    max_ai_calls_per_hour: int = field(default_factory=lambda: int(os.getenv("MAX_AI_CALLS_PER_HOUR", "30")))
    max_ai_calls_per_day: int = field(default_factory=lambda: int(os.getenv("MAX_AI_CALLS_PER_DAY", "300")))
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    enable_telegram: bool = field(default_factory=lambda: _bool("ENABLE_TELEGRAM", True))
    min_signal_score: float = field(default_factory=lambda: float(os.getenv("MIN_SIGNAL_SCORE", "6.5")))
    min_notification_score: float = field(default_factory=lambda: float(os.getenv("MIN_NOTIFICATION_SCORE", "7.5")))
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    display_timezone: str = field(default_factory=lambda: os.getenv("DISPLAY_TIMEZONE", "Europe/Bucharest"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    candidate_threshold: float = field(default_factory=lambda: float(os.getenv("CANDIDATE_THRESHOLD", "6.0")))
    enable_technical_agent: bool = field(default_factory=lambda: _bool("ENABLE_TECHNICAL_AGENT", True))
    enable_news_agent: bool = field(default_factory=lambda: _bool("ENABLE_NEWS_AGENT", True))
    enable_fundamental_agent: bool = field(default_factory=lambda: _bool("ENABLE_FUNDAMENTAL_AGENT", True))
    enable_sentiment_agent: bool = field(default_factory=lambda: _bool("ENABLE_SENTIMENT_AGENT", True))
    enable_risk_agent: bool = field(default_factory=lambda: _bool("ENABLE_RISK_AGENT", True))
    enable_bull_bear_debate: bool = field(default_factory=lambda: _bool("ENABLE_BULL_BEAR_DEBATE", True))

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.cache_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def timezone(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.display_timezone)
        except Exception:
            return ZoneInfo("UTC")


settings = Settings()
settings.ensure_directories()
