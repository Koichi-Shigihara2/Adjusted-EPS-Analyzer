"""
common/sec_data/tickers.py
責務: config/cik_lookup.csv から銘柄リストを取得する共通ユーティリティ
     各サブシステムの --all オプションはこのモジュールを使う
"""

import csv
import os

_DEFAULT_CSV = os.path.join(
    os.path.dirname(__file__),  # common/sec_data/
    "..", "..",                  # リポジトリルート
    "config", "cik_lookup.csv"
)


def _load(csv_path: str | None = None) -> list[dict]:
    path = csv_path or os.path.abspath(_DEFAULT_CSV)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_all_tickers(csv_path: str | None = None) -> list[str]:
    """cik_lookup.csv の全銘柄を返す"""
    return [r["ticker"] for r in _load(csv_path)]


def get_tickers_by_flag(flag: str, csv_path: str | None = None) -> list[str]:
    """
    指定フラグが 'true' の銘柄リストを返す。

    flag: 'hypecore' | 'tanuki' | 'eps' | 'stonks_silo'
    """
    return [
        r["ticker"] for r in _load(csv_path)
        if r.get(flag, "").strip().lower() == "true"
    ]


def get_hypecore_tickers(csv_path: str | None = None) -> list[str]:
    """hypecore=true の銘柄リストを返す"""
    return get_tickers_by_flag("hypecore", csv_path)


def get_tanuki_tickers(csv_path: str | None = None) -> list[str]:
    """tanuki=true の銘柄リストを返す"""
    return get_tickers_by_flag("tanuki", csv_path)


def get_eps_tickers(csv_path: str | None = None) -> list[str]:
    """eps=true の銘柄リストを返す"""
    return get_tickers_by_flag("eps", csv_path)


def get_stonks_silo_tickers(csv_path: str | None = None) -> list[str]:
    """stonks_silo=true の銘柄リストを返す"""
    return get_tickers_by_flag("stonks_silo", csv_path)
