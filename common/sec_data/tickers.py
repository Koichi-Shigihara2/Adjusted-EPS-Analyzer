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
# 'retired'（登録抹消済み）に加え、2026-09-03より'provisioning'
# （登録処理中・Step 8のNG=0確認前）も除外する（[[REGISTER-FLOW-
# REDESIGN-1]]方針2、common/registration/register_ticker.py参照）。
# 'candidate'（検証中だが各パイプラインには通す運用、WST/CON等）は
# 現状の既存動作を維持するため除外しない（statusによるパイプライン
# 対象外化は現状candidateには適用されていない。フラグ判定基準
# そのものの厳密化は別タスクとする）。
_INVALID_STATUSES = {"retired", "provisioning"}


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


def get_registrable_tickers(flag: str, csv_path: str | None = None) -> list[str]:
    """
    指定フラグが'true'、かつstatusが'retired'でない銘柄リストを返す
    （'provisioning'は除外しない、`get_active_tickers()`とはこの点のみ異なる）。

    **用途**: 各パイプラインの「CLI引数でticker明示指定時」の対象妥当性
    検証（ZS-TICKERS-LEAK-1由来の`_filter_*_tickers()`群）専用。
    新規銘柄登録オーケストレーション（[[REGISTER-FLOW-REDESIGN-1]]方針3、
    `common/registration/register_ticker.py`）が、status=provisioning
    のティッカーに対してStep 3（`pipeline.py TICKER`）・Step 5
    （`hypecore.py --batch TICKER`）・Step 5b（EPS Analyzer
    `--ticker TICKER`）を明示的に実行できる必要があるため新設した
    （2026-09-03）。

    **`get_active_tickers()`との使い分け**:
    - デフォルト・バッチ実行（`tickers=None`、`--all`等）の対象選定は
      引き続き`get_active_tickers()`（provisioning除外）を使う——
      registration_validator.pyのStep 8でNG=0が確認され`active`/
      `candidate`へ昇格するまでは、スケジュール実行等の自動対象には
      含めない
    - CLI引数でticker明示指定時の「範囲外ではないか」検証には本関数を
      使う——provisioningは「意図的な対象外」ではなく「登録処理中」
      であり、登録オーケストレーション自身が明示的に指定した場合は
      処理を許可すべきため。'retired'（登録抹消済み）は明示指定でも
      引き続き除外する（意図的な対象外のため、ZS-TICKERS-LEAK-1が
      防いだ種類のリークと同型のリスクを再導入しないため）

    flag: 'hypecore' | 'tanuki' | 'eps' | 'stonks_silo'
    """
    return [
        r["ticker"] for r in _load(csv_path)
        if r.get(flag, "").strip().lower() == "true"
        and r.get("status", "").strip().lower() != "retired"
    ]
