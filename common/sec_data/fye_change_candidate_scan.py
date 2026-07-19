"""
common/sec_data/fye_change_candidate_scan.py
責務: 決算期変更（FYE change）の可能性がある銘柄を、決算アンカー日の
クラスタリングで機械的に洗い出す候補抽出ツール（読み取り専用・自動修正なし）。

FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1の設計調査時に、105銘柄全体を
一時的にスキャンして手法として使ったもの（RCAT/ELF/MSCI/NOWの4銘柄を検出）を、
独立ツールとして常設化した。`parser.py::_detect_fiscal_anchor_date()`が
既に使っている`common/sec_data/utils.py::_cluster_fiscal_anchor_candidates()`
（ARCH-DATA-1ステージ2導入、JNJ/TDY型の52/53週対応）をそのまま再利用する。

【重要・本ツールの位置づけ】
本ツールが検出する「クラスタ2つ以上・循環距離30日超」は、あくまで
「決算日の分布がヒストリカルに2箇所に分かれている」という統計的シグナル
であり、実際にデータ品質上の問題（年度バケツ競合等）を引き起こしているか
は別途個別確認が必要。過去の実例では4候補（RCAT/ELF/MSCI/NOW）中、
実際に年度バケツ競合が発生していたのはRCATのみで、ELF/MSCIは決算期
変更はあったが競合なし、NOWは単発の参考開示によるノイズだった
（詳細はBACKLOG_DONE.md [[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]参照）。

そのため本ツールはWARN-24（report_consistency_check.py::CHECK-24、
実際の年度バケツ競合を検知する精密なチェック）の常設発火条件としては
使わない。新規銘柄登録時・定期監査時に手動実行し、決算期変更の可能性が
ある候補を洗い出すための補助ツールという位置づけに留める。

実行方法:
    python -m common.sec_data.fye_change_candidate_scan
    python -m common.sec_data.fye_change_candidate_scan AAPL MSFT  # 銘柄指定
"""

import os
import sys
from datetime import datetime

from .fetcher import load_company_facts
from .parser import SECParser
from .tickers import get_tanuki_tickers
from .utils import _cluster_fiscal_anchor_candidates

# クラスタとして意味を持たせる最小支持度（合計出現回数）。1件のみの孤立点は
# 単発の参考開示等のノイズである可能性が高いため対象外とする（NOW型の除外）。
MIN_CLUSTER_SUPPORT = 2

# クラスタ間の循環距離（日数）がこれを超える場合のみ「実質的に離れた2つの
# 決算期」とみなす（52/53週企業の通常の前後変動と区別するため）。
MIN_CLUSTER_DISTANCE_DAYS = 30


def _build_day_counts(us_gaap: dict, candidate_keys: list) -> dict:
    """
    common/sec_data/utils.py::detect_fiscal_anchor_date()と同一の入力構築
    ロジック（本人10-K annualエントリ・340-380日の真の年次期間のend日）を
    再利用する。parser.py本体を変更せず、ここで独立に再実装する
    （detect_fiscal_anchor_date()自体はクラスタ選定後の代表日1点のみを
    返す設計のため、クラスタ一覧そのものが欲しい本ツールでは低レベルの
    day_counts構築部分だけを共有する）。
    """
    day_counts: dict = {}
    for raw_key in candidate_keys:
        xbrl_key = raw_key[8:] if raw_key.startswith("us-gaap:") else raw_key
        if xbrl_key not in us_gaap:
            continue
        for unit_type in ("USD", "shares", "USD/shares"):
            for entry in us_gaap[xbrl_key].get("units", {}).get(unit_type, []):
                if entry.get("form") not in ("10-K", "10-K/A") or entry.get("fp") != "FY":
                    continue
                start = entry.get("start", "")
                end = entry.get("end", "")
                if not start or not end or len(start) < 10 or len(end) < 10:
                    continue
                try:
                    start_dt = datetime.strptime(start, "%Y-%m-%d")
                    end_dt = datetime.strptime(end, "%Y-%m-%d")
                except ValueError:
                    continue
                days = (end_dt - start_dt).days
                if not (340 <= days <= 380):
                    continue
                key = (end_dt.month, end_dt.day)
                day_counts[key] = day_counts.get(key, 0) + 1
        if day_counts:
            break
    return day_counts


def _circular_distance(doy1: int, doy2: int) -> int:
    d = abs(doy1 - doy2)
    return min(d, 366 - d)


def scan_ticker(parser: SECParser, ticker: str) -> dict | None:
    """
    1銘柄をスキャンし、候補に該当する場合のみ詳細dictを返す
    （非該当の場合はNone）。

    Returns:
        {"ticker": str, "clusters": [(support, [(month,day), ...]), ...],
         "max_distance_days": int} または None
    """
    cf = load_company_facts(ticker, data_dir=parser.data_dir)
    if not cf:
        return None
    us_gaap = cf.get("facts", {}).get("us-gaap", {})
    candidate_keys = parser._fiscal_detection_keys()
    day_counts = _build_day_counts(us_gaap, candidate_keys)
    clusters = _cluster_fiscal_anchor_candidates(day_counts)

    real_clusters = [c for c in clusters if sum(p[3] for p in c) >= MIN_CLUSTER_SUPPORT]
    if len(real_clusters) < 2:
        return None

    # クラスタごとの代表点（最頻出の(月,日)）のday_of_yearで距離を測る
    reps = [max(c, key=lambda p: p[3]) for c in real_clusters]
    max_dist = 0
    for i in range(len(reps)):
        for j in range(i + 1, len(reps)):
            max_dist = max(max_dist, _circular_distance(reps[i][0], reps[j][0]))

    if max_dist <= MIN_CLUSTER_DISTANCE_DAYS:
        return None

    return {
        "ticker": ticker,
        "clusters": [
            (sum(p[3] for p in c), sorted({(m, d) for _, m, d, _ in c}))
            for c in real_clusters
        ],
        "max_distance_days": max_dist,
    }


def main():
    args = sys.argv[1:]
    tickers = args if args else get_tanuki_tickers()
    if not tickers:
        print("対象銘柄が見つかりません。config/cik_lookup.csv を確認してください。")
        sys.exit(1)

    parser = SECParser()

    print("=== 決算期変更（FYE change）候補スキャン ===")
    print(f"対象: {len(tickers)}銘柄 / "
          f"クラスタ最小支持度: {MIN_CLUSTER_SUPPORT} / 最小循環距離: {MIN_CLUSTER_DISTANCE_DAYS}日")
    print("※ これは候補抽出用の統計的シグナルであり誤検知を含みうる")
    print("　（実例: 過去4候補中3件〈ELF/MSCI/NOW〉が実害なしのノイズだった）。")
    print("　実際にデータ品質上の問題を引き起こしているかは個別確認が必要。")
    print()

    candidates = []
    for ticker in tickers:
        result = scan_ticker(parser, ticker)
        if result:
            candidates.append(result)

    for c in candidates:
        cluster_str = " / ".join(
            f"{support}件@{','.join(f'{m}/{d}' for m, d in dates)}"
            for support, dates in c["clusters"]
        )
        print(f"⚠️  {c['ticker']}: クラスタ{len(c['clusters'])}個・最大循環距離{c['max_distance_days']}日")
        print(f"     {cluster_str}")

    print()
    print(f"合計: {len(candidates)}/{len(tickers)}銘柄が決算期変更の候補として該当")


if __name__ == "__main__":
    main()
