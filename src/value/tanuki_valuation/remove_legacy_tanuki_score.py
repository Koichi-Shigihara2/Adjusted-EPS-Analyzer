"""
TANUKI VALUATION - Remove Legacy tanuki_score Field from history.json

[[HISTORY-JSON-LEGACY-TANUKI-SCORE-1]]対応。

pipeline.py:987-988のDESIGNコメントが明記する通り、history.json（時系列
チャート用の軽量サマリ）は判定ラベル（TANUKI SCORE等）を含めない設計に
なっており、現行コードは`tanuki_score`を一切書き込んでいない。しかし
過去（この方針が確定する前）に書き込まれたレガシーエントリが削除されず
複数銘柄のhistory.jsonに残存していたため、一括削除する。

着手前に消費者ゼロを確認済み（フロントエンド・バックエンドともhistory.json
の`tanuki_score`キーを読む箇所は存在しない）。

実行方法:
    python src/value/tanuki_valuation/remove_legacy_tanuki_score.py         # 実行
    python src/value/tanuki_valuation/remove_legacy_tanuki_score.py --dry-run  # 件数確認のみ
"""

import argparse
import glob
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
DATA_ROOT = os.path.join(REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "data")


def clean_history_file(path: str, dry_run: bool) -> int:
    """1ファイル分のtanuki_scoreエントリを削除する。削除件数を返す。"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        return 0

    removed = 0
    for entry in data:
        if isinstance(entry, dict) and "tanuki_score" in entry:
            entry.pop("tanuki_score")
            removed += 1

    if removed and not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return removed


def main():
    parser = argparse.ArgumentParser(description="Remove legacy tanuki_score field from history.json files")
    parser.add_argument("--dry-run", action="store_true", help="削除は行わず件数のみ表示")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(DATA_ROOT, "*", "history.json")))
    print(f"対象ファイル: {len(paths)}件")

    total_files_affected = 0
    total_entries_removed = 0
    for path in paths:
        ticker = os.path.basename(os.path.dirname(path))
        removed = clean_history_file(path, args.dry_run)
        if removed:
            total_files_affected += 1
            total_entries_removed += removed
            action = "検出" if args.dry_run else "削除"
            print(f"  [{ticker}] {removed}件のtanuki_scoreエントリを{action}")

    mode = "（dry-run、実際の削除は行っていません）" if args.dry_run else ""
    print(f"\n完了{mode}: {total_files_affected}ファイル・計{total_entries_removed}件のtanuki_scoreエントリを{'検出' if args.dry_run else '削除'}")


if __name__ == "__main__":
    main()
