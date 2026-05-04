"""
共通ティッカー設定
config/cik_lookup.csv から動的読み込み
"""

import csv
import os


def _load_from_csv() -> dict:
    search_paths = []

    workspace = os.environ.get("GITHUB_WORKSPACE", "")
    if workspace:
        search_paths.append(os.path.join(workspace, "config", "cik_lookup.csv"))

    try:
        current = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(os.path.dirname(current))
        search_paths.append(os.path.join(repo_root, "config", "cik_lookup.csv"))
    except Exception:
        pass

    for path in search_paths:
        if os.path.exists(path):
            tickers = {}
            with open(path, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    ticker = row.get("ticker", "").strip()
                    if ticker:
                        tickers[ticker] = {
                            "status": "watching",
                            "name": row.get("name", ticker),
                            "cik": row.get("cik", ""),
                        }
            return tickers

    return {}


TICKERS = _load_from_csv()


def get_holdings():
    return [t for t, v in TICKERS.items() if v["status"] == "holding"]


def get_watchlist():
    return [t for t, v in TICKERS.items() if v["status"] == "watching"]


def get_all():
    return list(TICKERS.keys())


def get_ticker_info(ticker: str) -> dict:
    return TICKERS.get(ticker, {"status": "unknown", "name": ticker})
