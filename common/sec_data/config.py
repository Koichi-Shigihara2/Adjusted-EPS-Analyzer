"""
共通ティッカー設定
config/cik_lookup.csv から動的読み込み
"""

import csv
import os

from . import tickers as _tickers_mod


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

# get_holdings()・get_watchlist()・get_ticker_info()は[[TICKER-LOADING-
# UNIFICATION-1]]（2026-09-05）調査時点でtickers.py側に同等機能が存在せず
# （名前/CIK/status付きの銘柄情報dictという形はtickers.pyにない）、
# 統合対象から外してconfig.py側に残した。なお_load_from_csv()は
# 実際のCSVのstatus列を見ず全行を"watching"固定で読み込むため、
# get_holdings()は常に空リストを返す・get_watchlist()は実質get_all()と
# 同じ全銘柄を返す設計になっている。両関数とも呼び出し元が存在しない
# （リポジトリ内grep確認済み）が、既存動作を変える修正は本タスクの
# スコープ外のためそのまま残す。


def get_holdings():
    return [t for t, v in TICKERS.items() if v["status"] == "holding"]


def get_watchlist():
    return [t for t, v in TICKERS.items() if v["status"] == "watching"]


def get_all():
    """全登録銘柄（status='retired'以外）を返す。

    [[TICKER-LOADING-UNIFICATION-1]]（2026-09-05）により、独自の
    `TICKERS`辞書キー列挙から`tickers.get_registrable_tickers()`
    （flag未指定＝フラグ絞り込みなし）経由に統一した。

    **`get_active_tickers()`ではなく`get_registrable_tickers()`を使う
    理由**: `common/sec_data/update.py`（本関数の主要呼び出し元、SEC
    EDGAR生データ取得のStep 1）は、新規銘柄登録オーケストレーション
    （`common/registration/register_ticker.py`）がStep 1として
    status=provisioningの銘柄のデータ取得を行う際にも使われる。
    `get_active_tickers()`はprovisioningを除外するため、これを使うと
    登録処理中の銘柄がStep 1から漏れて登録フローが壊れる
    （[[REGISTER-FLOW-REDESIGN-1]]方針3）。

    旧実装（`TICKERS`辞書、statusを"watching"に固定して読み込むだけで
    実際のCSV上のstatus列を一切見ていなかった）は事実上フラグ・status
    無条件の全銘柄返却だったため、'retired'銘柄が存在しない現行データ
    では本統一後も結果は完全に一致する（'retired'銘柄が登録された場合、
    今後はSEC生データ取得の対象から正しく除外されるようになる）。
    """
    return _tickers_mod.get_registrable_tickers()


def get_ticker_info(ticker: str) -> dict:
    return TICKERS.get(ticker, {"status": "unknown", "name": ticker})
