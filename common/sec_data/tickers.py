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
    指定フラグが 'true' の銘柄リストを返す（statusは見ない）。

    flag: 'hypecore' | 'tanuki' | 'eps' | 'stonks_silo'
    """
    return [
        r["ticker"] for r in _load(csv_path)
        if r.get(flag, "").strip().lower() == "true"
    ]


# statusのうち、フラグの値に関わらず対象外とすべき値。
# 'retired'（登録抹消済み）のみを除外する。'candidate'（検証中だが
# 各パイプラインには通す運用、WST/CON等）は現状の既存動作を維持するため
# 除外しない（statusによるパイプライン対象外化は現状candidateには
# 適用されていない。フラグ判定基準そのものの厳密化は別タスクとする）。
_INVALID_STATUSES = {"retired"}


def get_active_tickers(flag: str, csv_path: str | None = None) -> list[str]:
    """
    指定フラグが'true'、かつstatusが有効（'retired'でない）銘柄リストを返す。

    銘柄リストを組み立てる全ての消費者はcik_lookup.csv・config.get_all()を
    直接参照するのではなく、本関数を経由することで、フラグ判定ロジックを
    一元化する（tanuki=falseのZSがtickers.json等に混入し続けていた問題の
    再発防止。TICKER-SOURCE-UNIFY-1の延長）。

    flag: 'hypecore' | 'tanuki' | 'eps' | 'stonks_silo'
    """
    return [
        r["ticker"] for r in _load(csv_path)
        if r.get(flag, "").strip().lower() == "true"
        and r.get("status", "").strip().lower() not in _INVALID_STATUSES
    ]


def get_hypecore_tickers(csv_path: str | None = None) -> list[str]:
    """hypecore=true（かつstatus有効）の銘柄リストを返す"""
    return get_active_tickers("hypecore", csv_path)


def get_tanuki_tickers(csv_path: str | None = None) -> list[str]:
    """tanuki=true（かつstatus有効）の銘柄リストを返す"""
    return get_active_tickers("tanuki", csv_path)


def get_eps_tickers(csv_path: str | None = None) -> list[str]:
    """eps=true（かつstatus有効）の銘柄リストを返す"""
    return get_active_tickers("eps", csv_path)


def get_stonks_silo_tickers(csv_path: str | None = None) -> list[str]:
    """stonks_silo=true（かつstatus有効）の銘柄リストを返す"""
    return get_active_tickers("stonks_silo", csv_path)
