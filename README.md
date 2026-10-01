# Trading Intelligence

A research-only market scanner for US stocks, ETFs and crypto. It combines deterministic technical calculations, selective news/fundamental analysis, optional structured AI sentiment, risk validation, backtesting, performance tracking and Telegram alerts. It contains **no broker integration and no order execution endpoint**.

## Architecture

`market data → indicators → candidate filter → news/fundamentals → optional AI → risk → decision → tracking → notification`

The `MarketDataProvider` interface isolates yfinance so Polygon, Finnhub or another provider can be added without changing analysis logic. Indicators and price levels are computed in Python. Bull and bear evaluations receive the same normalized evidence independently. Missing fundamental data causes weight redistribution; crypto uses adapted weights.

Confidence is deterministic: 35% agent agreement, 25% data completeness, 25% technical confidence and 15% historical calibration (55% prior until at least 20 comparable evaluated signals exist). When calibrated, confidence is capped near the observed win rate.

## Windows 11

Install 64-bit Python 3.12+ and enable **Add Python to PATH**, then:

```powershell
git clone <repository-url> trading-agent
cd trading-agent
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
notepad .env
.\run_windows.ps1
```

Open <http://127.0.0.1:8000>. Swagger API docs are at <http://127.0.0.1:8000/docs>.

For startup, use Windows Task Scheduler: create a task running `powershell.exe` with arguments `-NoProfile -ExecutionPolicy Bypass -File C:\Projects\trading-agent\run_windows.ps1`; set **Start in** to the project directory and run as a normal user.

## Ubuntu / DigitalOcean

On Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
git clone <repository-url> trading-agent
cd trading-agent
chmod +x setup_linux.sh run_linux.sh
./setup_linux.sh
nano .env
./run_linux.sh
```

For systemd, copy the project to `/opt/trading-agent`, create a non-root service account, ensure it owns the project, and edit `User`/`Group` in the example:

```bash
sudo cp trading-agent.service.example /etc/systemd/system/trading-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now trading-agent
sudo journalctl -u trading-agent -f
```

The default API binds only to `127.0.0.1`. Use an authenticated TLS reverse proxy if remote access is required; do not expose Uvicorn directly. The app uses one process, bounded sequential scans, rotating logs and SQLite for small droplets. 512 MB is possible but 1 GB is recommended when pandas compiles/installs or several years of data are scanned.

## Configuration

Copy `.env.example` to `.env`. API keys are optional. With no OpenAI key, rule-based news/technical analysis continues. With no Telegram token/chat ID, notifications are simply skipped. `WATCHLIST` seeds only an empty database; afterward SQLite is the source of truth and the dashboard manages instruments.

Important settings: `SCAN_INTERVAL_MINUTES`, `CANDIDATE_THRESHOLD`, `MAX_AI_CALLS_PER_HOUR`, `MAX_AI_CALLS_PER_DAY`, `MIN_NOTIFICATION_SCORE`, `API_HOST`, `API_PORT`, and `DISPLAY_TIMEZONE`. Internal timestamps are UTC.

## CLI and API

```powershell
.\.venv\Scripts\python.exe -m app.cli scan NVDA
.\.venv\Scripts\python.exe -m app.cli scan-all
.\.venv\Scripts\python.exe -m app.cli backtest NVDA --period 5y
```

Linux uses `.venv/bin/python` with the same module commands. Key APIs include `/health`, `/instruments`, `/market/{symbol}`, `/analysis/{symbol}`, `/recommendations`, `/agents/{symbol}`, `/performance`, `/scan`, `/scan/{symbol}`, and `/backtest`.

## Tests

```bash
python -m pytest -q
```

Tests use synthetic market data/mocks and do not require live APIs.

## Troubleshooting

- **Python/venv missing:** install Python 3.12+ and the Ubuntu `python3-venv` package. On Windows, disable the Microsoft Store Python execution alias if it shadows your install.
- **Permissions:** run as a normal user that can write `data/` and `logs/`; never run the service as root.
- **SQLite locked:** run a single Uvicorn worker. Stop duplicate instances; WAL mode is enabled.
- **yfinance failures:** wait and retry, verify DNS/outbound HTTPS, or remove `data/cache/<symbol>_*.csv` if a cache is corrupt. The provider retries and uses stale cache when safe.
- **Telegram:** message the bot once, verify chat ID/token and outbound HTTPS. Tokens are never logged.
- **OpenAI:** verify key/model/access. Rate limits fall back to deterministic analysis; inspect `logs/errors.log` without sharing secrets.
- **Market hours:** US session state is DST-aware, but exchange holidays are a documented V1 limitation. Crypto scans continuously.

## V1 limitations

Yahoo/yfinance and public RSS availability are best-effort. News sentiment caching uses stored article sentiment fields but richer semantic cache invalidation is intentionally conservative. Backtests use current symbols and therefore cannot fully remove survivorship bias. Earnings-calendar proximity and official exchange holidays require a future dedicated provider. Recommendations are informational and require manual action.
