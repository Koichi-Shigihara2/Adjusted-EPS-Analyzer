"""
common/macro_data/migrate_bamlh0a0hym2_history.py

【これは通常のfetcher/reader運用とは異なる、一度限りの例外的な過去データ
移行スクリプトです】common/macro_data/の通常運用（`fetcher.py`による
FRED APIからの日次再取得）とは別系統の、単発実行専用ツールです。

【実行理由】
BACKLOG `[[MACRODATA-BAMLH0A0HYM2-HISTORY-EXCEPTION-1]]`参照。
FRED側（データ提供元ICE Data Indices）が2026年4月からBAMLH0A0HYM2の
提供範囲を「直近3年分のみ」に制限したため（`fredapi::get_series_info()`
のnotes欄で確認済み）、`common/macro_data/series/BAMLH0A0HYM2.json`は
FRED APIからの再取得では`2023-08-14`より前のデータを二度と取得できない。
`[[PHASE2-MIGRATION-POLICY-DECIDED-1]]`で確定した移行方針の「例外」規定
（データ提供元が恒久的に提供範囲を制限しており再取得が技術的に不可能な
場合に限り、削除予定の旧保存先データから一度限りの例外的移行を行う）に
基づき、削除予定の旧`docs/market-monitor/macro-pulse/data/05_events.csv`
（`indicator == "HY Spread"`の行）から、まだFRED APIで取得可能だった
期間（`2023-08-14`より前）のデータをこのスクリプトで一度だけ移行する。

【冪等性に関する注意】
このスクリプトは冪等性を保証しません。誤って複数回実行しないでください。
実行前に、移行先ファイルの既存レコードに`source_detail`へ
`migrated_from=05_events.csv`を含むものが既に存在しないかをチェックし、
存在する場合は`--force`を指定しない限り処理を中断します
（二重投入によるレコード汚染を防ぐための安全装置）。

【スクリプト自体の扱い】
使い捨てではありません。監査証跡として削除せず残します（実行は一度限り）。

【移行ロジック】
1. `common/macro_data/series/BAMLH0A0HYM2.json`の既存レコードのうち
   最古の`as_of`を確認する（移行対象の締切日、通常は`2023-08-14`）
2. `05_events.csv`から`indicator == "HY Spread"`の行を抽出し、
   `release_date`列を`as_of`、`actual`列を`value`として変換
3. 締切日より前の日付のみを移行対象とする（締切日以降の既存レコードは
   一切変更しない）
4. 移行レコードにはprovenanceとして`source="FRED"`・`source_detail`に
   例外的移行である旨を明記（ライブ取得分の`source_detail=
   "series=BAMLH0A0HYM2"`と区別可能な文言）・`fallback_used=false`を付与
5. `common/macro_data/fetcher.py`の保存前検証（`_validate_incoming_batch`）
   と同一の検証を移行バッチに対して実行し、結果を
   `macro_data_violations_log.json`のBAMLH0A0HYM2セクションへ記録
   （`fetcher._write_violations_section`を再利用）
6. 既存レコード＋移行レコードを`as_of`昇順にソートして
   `fetcher._atomic_write_json`で保存

使い方:
    python common/macro_data/migrate_bamlh0a0hym2_history.py           # 実行
    python common/macro_data/migrate_bamlh0a0hym2_history.py --dry-run # 確認のみ（書き込みなし）
    python common/macro_data/migrate_bamlh0a0hym2_history.py --force   # 二重実行ガードを無視して強制実行（非推奨）
"""

import argparse
import csv
import os
import sys

# fetcher.pyと同じディレクトリに配置されているため、スクリプト直接実行時
# （`python common/macro_data/migrate_bamlh0a0hym2_history.py`）は
# Pythonがこのファイルのディレクトリを自動的にsys.path[0]へ追加する。
# fetcher.pyの共通ユーティリティ（アトミック書き込み・保存前検証・
# 違反ログ書き込み）を再利用する。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetcher as _fetcher  # noqa: E402

SERIES_ID = "BAMLH0A0HYM2"
MIGRATION_MARKER = "migrated_from=05_events.csv"
SOURCE_DETAIL = (
    f"series={SERIES_ID}; {MIGRATION_MARKER} "
    "(exception, FRED 3yr limit since 2026-04)"
)

MACRO_DATA_DIR = _fetcher.MACRO_DATA_DIR
EVENTS_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "docs", "market-monitor", "macro-pulse", "data", "05_events.csv",
)


def _load_hy_spread_rows(csv_path: str):
    """05_events.csvからindicator == "HY Spread"の行のみ抽出し、
    release_date昇順でas_of/valueの辞書リストを返す。"""
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("indicator") != "HY Spread":
                continue
            as_of = row.get("release_date", "")
            actual = row.get("actual", "")
            if not as_of or not actual:
                continue
            rows.append({"as_of": as_of, "value": float(actual)})
    rows.sort(key=lambda r: r["as_of"])
    return rows


def migrate(base_dir: str = None, dry_run: bool = False, force: bool = False) -> dict:
    base = base_dir if base_dir is not None else MACRO_DATA_DIR
    series_path = _fetcher._series_path(SERIES_ID, base)

    payload = _fetcher._load_json(series_path, default={"series_id": SERIES_ID, "records": []})
    existing_records = payload.get("records", [])
    if not existing_records:
        raise RuntimeError(
            f"{series_path} にレコードが存在しません。"
            "先にcommon/macro_data/fetcher.pyで通常取得を実行してください。"
        )

    already_migrated = [
        r for r in existing_records
        if MIGRATION_MARKER in str(r.get("source_detail", ""))
    ]
    if already_migrated and not force:
        raise RuntimeError(
            f"既に{len(already_migrated)}件の移行済みレコード"
            f"（source_detailに'{MIGRATION_MARKER}'を含む）が存在します。"
            "二重投入を防ぐため処理を中断します。再実行する場合は"
            "--forceを指定してください（非推奨、事前に既存の移行分の"
            "削除要否を確認すること）。"
        )

    existing_map = {r["as_of"]: r for r in existing_records if r.get("as_of")}
    cutoff_date = min(existing_map.keys())

    hy_rows = _load_hy_spread_rows(EVENTS_CSV_PATH)
    incoming = [r for r in hy_rows if r["as_of"] < cutoff_date]

    if not incoming:
        return {
            "cutoff_date": cutoff_date,
            "candidates_total": len(hy_rows),
            "migrated": 0,
            "warnings": [],
            "before_count": len(existing_records),
            "after_count": len(existing_records),
        }

    # 移行対象がcutoff_dateより前であることを再確認し、既存レコードとの
    # 衝突（＝2023-08-14以降のレコードを誤って上書きしてしまう事態）が
    # 絶対に起きないことを保証する。
    collisions = [r["as_of"] for r in incoming if r["as_of"] in existing_map]
    if collisions:
        raise RuntimeError(
            f"移行対象に既存レコードと同一のas_ofが{len(collisions)}件"
            f"検出されました（例: {collisions[:5]}）。既存レコードの上書きを"
            "避けるため処理を中断します。"
        )

    # fetcher.py::_validate_incoming_batch()と同一の保存前検証。
    # 移行バッチより前の既存データは存在しないためprior_last_value=None。
    validation_warnings = _fetcher._validate_incoming_batch(incoming, prior_last_value=None)

    if dry_run:
        return {
            "cutoff_date": cutoff_date,
            "candidates_total": len(hy_rows),
            "migrated": len(incoming),
            "warnings": validation_warnings,
            "before_count": len(existing_records),
            "after_count": len(existing_records) + len(incoming),
            "dry_run": True,
        }

    fetched_at = _fetcher._now_jst_iso()
    for item in incoming:
        existing_map[item["as_of"]] = {
            "value": item["value"],
            "as_of": item["as_of"],
            "fetched_at": fetched_at,
            "source": "FRED",
            "source_detail": SOURCE_DETAIL,
            "fallback_used": False,
        }

    records = sorted(existing_map.values(), key=lambda r: r["as_of"])
    payload["series_id"] = SERIES_ID
    payload["records"] = records
    _fetcher._atomic_write_json(series_path, payload)

    _fetcher._write_violations_section(SERIES_ID, validation_warnings, base)

    return {
        "cutoff_date": cutoff_date,
        "candidates_total": len(hy_rows),
        "migrated": len(incoming),
        "warnings": validation_warnings,
        "before_count": len(existing_records),
        "after_count": len(records),
    }


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="BAMLH0A0HYM2の例外的履歴移行（05_events.csv → "
                     "common/macro_data/series/BAMLH0A0HYM2.json、一度限り）"
    )
    arg_parser.add_argument(
        "--dry-run", action="store_true",
        help="書き込みを行わず、移行対象件数・検証結果のみ表示する",
    )
    arg_parser.add_argument(
        "--force", action="store_true",
        help="既に移行済みレコードが存在する場合でも強制的に再実行する（非推奨）",
    )
    args = arg_parser.parse_args()

    result = migrate(dry_run=args.dry_run, force=args.force)

    print(f"cutoff_date (既存最古as_of): {result['cutoff_date']}")
    print(f"05_events.csv HY Spread候補行数: {result['candidates_total']}")
    print(f"移行対象件数: {result['migrated']}")
    print(f"移行前レコード数: {result['before_count']}")
    print(f"移行後レコード数: {result['after_count']}"
          + (" (dry-run、実際には書き込んでいない)" if args.dry_run else ""))
    if result["warnings"]:
        print(f"保存前検証の警告: {len(result['warnings'])}件")
        for w in result["warnings"]:
            print(f"  - {w}")
    else:
        print("保存前検証の警告: 0件")
