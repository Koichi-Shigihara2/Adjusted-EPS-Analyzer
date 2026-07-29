"""
common/sec_data/newfield_q4_cutoff_check.py
責務: [[LAYER3-TTM-REGRESSION-NEWFIELD-BLINDSPOT-1]]対応の常設チェックツール。

現行のTTM回帰比較（旧ttm/データのキーを起点に新旧を突合する設計）は、
旧パイプラインに存在しなかった新規フィールドを検証対象外にしてしまう
構造的欠陥がある。selling_general_and_administrative・cost_of_revenueの
2フィールドについて、旧データとの突合に代わる個別チェックとして以下を行う:

  ① Q4欠落チェック: 年次エントリのFY窓内にQ1〜Q3の3四半期が揃っている
     にも関わらず、Q4（ネイティブ報告・Q4逆算いずれも含む）が存在しない
     ケースを検出する。[[LAYER3-SGA-Q4-MISSING-1]]（42銘柄・171四半期に
     影響）と同種のバグの再発を検知する。
  ② カットオフチェック: 非12月決算企業について、対象フィールドの単四半期
     エントリのperiod_daysがlayer3_builder.py::_is_plausible_standalone_
     quarter()の妥当範囲（75〜100日）に収まっているかを確認する。

対象フィールドを2件に限定する理由（[[LAYER3-TTM-REGRESSION-NEWFIELD-
BLINDSPOT-1]]対応の投資調査で判定済み・q4_implied.pyのモジュールdocstring
参照）:
  - short_term_investments・total_liabilities（category="stock"）:
    「年次-Q1-Q2-Q3=Q4」という近似自体がSTOCK系（残高スナップショット）
    には数学的に無意味なため対象外。
  - eps_basic・eps_diluted（比率フィールド）: 加重平均株式数の変動により
    単純合算・差分が数学的に意味を持たないため対象外。
これら4フィールド向けの検証（BS恒等式によるクロスフィールド整合性チェック・
source_tag監視・ROEフォールバック発火ログ等）は性質の異なる別種の検証
（report_consistency_check.py側の役割に近い）であり、本ツールのスコープ
には含めない。

実行方法:
    python -m common.sec_data.newfield_q4_cutoff_check
    python -m common.sec_data.newfield_q4_cutoff_check AAPL MSFT  # 銘柄指定

終了コード:
    0 = Q4欠落なし（カットオフ異常のみの場合も0。WARN相当のため非ブロッキング）
    1 = 1件以上のQ4欠落を検出
"""

import sys
from datetime import date

from .layer3_builder import build_ticker_store, _is_plausible_standalone_quarter
from .tickers import get_tanuki_tickers

TARGET_FIELDS = ("selling_general_and_administrative", "cost_of_revenue")


def _detect_non_dec_fye(store: dict) -> bool:
    """
    revenue（常に安定して取得できる基準フィールド）の年次エントリの
    最頻end月から、非12月決算企業かどうかを簡易判定する。
    """
    rev_entries = store.get("fields", {}).get("revenue", {}).get("entries", [])
    months = [
        date.fromisoformat(e["end"]).month
        for e in rev_entries
        if e.get("is_annual") and e.get("end")
    ]
    if not months:
        return False
    most_common = max(set(months), key=months.count)
    return most_common != 12


def _check_q4_completeness(field_name: str, entries: list) -> tuple[list[dict], list[dict]]:
    """
    q4_implied.py::build_q4_implied_entries()と同一の「直近3四半期
    （top3）・source_tag完全一致」判定条件を用いて、Q4が既存entries
    （ネイティブ報告・Q4逆算いずれも含む）に存在しないケースを検出する。

    top3のsource_tagが年次エントリと完全一致しない場合、
    build_q4_implied_entries()自身がQ4逆算を意図的にスキップする
    （[[LAYER3-DA-SBC-CANDIDATE-REGRESSION-1]]の既存ガード）ため、
    これは[[LAYER3-SGA-Q4-MISSING-1]]型のフィールドスコープ漏れバグとは
    区別し、"guarded"（ガードによる正当なスキップ）として別枠で返す。

    戻り値: (missing, guarded) のタプル。missingはフィールドスコープ漏れ等
    本来是正すべきケース、guardedはsource_tag不一致による正当なスキップ
    （情報提供のみ、NG扱いしない）。
    """
    annual = [e for e in entries if e.get("is_annual") and e.get("val") is not None]
    quarterly = [e for e in entries if not e.get("is_annual")]
    existing_ends = {e["end"] for e in quarterly}

    today = date.today().isoformat()
    missing: list[dict] = []
    guarded: list[dict] = []
    for a in annual:
        fy_end = a.get("end", "")
        fy_start = a.get("start", "")
        if not fy_end or fy_end > today:
            continue
        if fy_end in existing_ends:
            continue
        fy_qs = [
            e for e in quarterly
            if e.get("end", "") < fy_end and e.get("start", "") >= fy_start
        ]
        if len(fy_qs) < 3:
            continue
        top3 = sorted(fy_qs, key=lambda x: x["end"], reverse=True)[:3]
        source_tags = {a.get("source_tag")} | {e.get("source_tag") for e in top3}
        entry = {"field": field_name, "fy_end": fy_end, "q_count": len(fy_qs)}
        if len(source_tags) != 1:
            guarded.append({**entry, "source_tags": sorted(str(t) for t in source_tags)})
        else:
            missing.append(entry)
    return missing, guarded


def _check_cutoff(field_name: str, entries: list) -> list[dict]:
    """非12月決算企業向け: 単四半期エントリのperiod_days妥当性を確認する。"""
    anomalies: list[dict] = []
    for e in entries:
        if e.get("is_annual") or e.get("is_implied"):
            continue
        if not _is_plausible_standalone_quarter(e):
            anomalies.append({
                "field": field_name,
                "end": e.get("end"),
                "start": e.get("start"),
                "period_days": e.get("period_days"),
            })
    return anomalies


def check_ticker(ticker: str) -> dict | None:
    """
    1銘柄をチェックし、Q4欠落・カットオフ異常のいずれかが1件でもあれば
    詳細dictを返す（該当なしの場合はNone）。
    """
    store = build_ticker_store(ticker)
    if not store:
        return None

    non_dec_fye = _detect_non_dec_fye(store)
    q4_missing: list[dict] = []
    q4_guarded: list[dict] = []
    cutoff_anomalies: list[dict] = []

    for field_name in TARGET_FIELDS:
        entries = store.get("fields", {}).get(field_name, {}).get("entries", [])
        if not entries:
            continue
        missing, guarded = _check_q4_completeness(field_name, entries)
        q4_missing.extend(missing)
        q4_guarded.extend(guarded)
        if non_dec_fye:
            cutoff_anomalies.extend(_check_cutoff(field_name, entries))

    if not q4_missing and not q4_guarded and not cutoff_anomalies:
        return None
    return {
        "ticker": ticker,
        "non_dec_fye": non_dec_fye,
        "q4_missing": q4_missing,
        "q4_guarded": q4_guarded,
        "cutoff_anomalies": cutoff_anomalies,
    }


def main():
    args = sys.argv[1:]
    tickers = args if args else get_tanuki_tickers()
    if not tickers:
        print("対象銘柄が見つかりません。config/cik_lookup.csv を確認してください。")
        sys.exit(1)

    print("=== 新規フィールド Q4欠落・カットオフチェック"
          f"（対象: {', '.join(TARGET_FIELDS)}） ===")
    print(f"対象: {len(tickers)}銘柄\n")

    ng_results: list[dict] = []
    warn_results: list[dict] = []
    guarded_results: list[dict] = []
    for ticker in tickers:
        result = check_ticker(ticker)
        if result is None:
            continue
        if result["q4_missing"]:
            ng_results.append(result)
        elif result["cutoff_anomalies"]:
            warn_results.append(result)
        elif result["q4_guarded"]:
            guarded_results.append(result)

    for r in ng_results:
        detail = " / ".join(
            f"{m['field']}@FY{m['fy_end']}(Q数={m['q_count']})" for m in r["q4_missing"]
        )
        print(f"NG  {r['ticker']}: Q4欠落 - {detail}")

    for r in warn_results:
        detail = " / ".join(
            f"{a['field']}@{a['end']}(period_days={a['period_days']})"
            for a in r["cutoff_anomalies"]
        )
        print(f"WARN {r['ticker']}: カットオフ異常候補（非12月決算） - {detail}")

    for r in guarded_results:
        detail = " / ".join(
            f"{g['field']}@FY{g['fy_end']}(source_tags={g['source_tags']})"
            for g in r["q4_guarded"]
        )
        print(f"参考 {r['ticker']}: Q4はsource_tag不一致ガードにより正当にスキップ - {detail}")

    print()
    print(f"合計: NG {len(ng_results)}銘柄 / WARN {len(warn_results)}銘柄 / "
          f"参考(ガードスキップ) {len(guarded_results)}銘柄 / 全{len(tickers)}銘柄中")

    if ng_results:
        sys.exit(1)


if __name__ == "__main__":
    main()
