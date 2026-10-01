"""Cross-platform command line interface."""
from __future__ import annotations

import argparse
import json

from app.backtest.engine import BacktestEngine
from app.database import init_db
from app.providers.market_data import YFinanceProvider
from app.schemas import BacktestRequest
from app.services import Scanner, seed_instruments
from app.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Intelligence research CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan"); scan.add_argument("symbol")
    sub.add_parser("scan-all")
    backtest = sub.add_parser("backtest"); backtest.add_argument("symbol"); backtest.add_argument("--period", default="5y")
    sub.add_parser("init-db")
    args = parser.parse_args(); configure_logging(); init_db(); seed_instruments()
    if args.command == "scan": result = Scanner().scan(args.symbol, force_ai=True)
    elif args.command == "scan-all": result = Scanner().scan_all()
    elif args.command == "backtest": result = BacktestEngine(YFinanceProvider()).run(BacktestRequest(symbol=args.symbol, period=args.period))
    else: result = {"status": "database initialized"}
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__": main()
