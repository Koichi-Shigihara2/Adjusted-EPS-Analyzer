"""
common/sec_data/quality_checker.py
責務: Normalizedデータの品質を量的・質的・整合性の3軸で検証する
"""

import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)

# 銘柄別制限（quarterly.pyと同期）
TICKER_RESTRICTIONS: dict[str, dict] = {
    "MSFT":  {"exclude": ["DA"]},
    "APP":   {"exclude": ["CapEx"]},
    "GOOGL": {
        "approximate": ["DA"],
        "note_discontinuous": ["LTDebt"],
    },
}

CHECKS: dict[str, str] = {
    # 量的チェック（データ量）
    "Q01": "直近8四半期でOCFの欠損が2以下",
    "Q02": "直近8四半期でRevenueの欠損が1以下",
    "Q03": "年次データが最低4期分存在する",
    "Q04": "SharesDilutedが直近4四半期すべて存在する",
    # 質的チェック（値の妥当性）
    "Q05": "Revenue前四半期比 ±80%以内（急変フラグ）",
    "Q06": "OCFが5期連続でRevenueの±200%以内",
    "Q07": "Cash残高が正値",
    "Q08": "FinanceLeasePmtsがCapEx以下（または欠損）",
    # 整合性チェック
    "Q09": "GrossProfit <= Revenue（粗利が売上超過していない）",
    "Q10": "期間の重複・ギャップが2四半期以上ない",
    "Q11": "同一end_dateに複数の非重複エントリがない",
    "Q12": "YTD→Q変換後の差分合計がFY年次値と±5%以内",
    "Q13": "銘柄別制限フィールドが除外されている（MSFT/APP/GOOGL）",
}


def run_checks(ticker: str, normalized: dict, raw: dict) -> dict:
    """
    13項目チェックを実行し、結果を返す。

    戻り値:
    {
      "ticker": "NVDA",
      "checked_at": "...",
      "passed": 12,
      "failed": 1,
      "results": {
        "Q01": {"status": "PASS", "detail": "欠損0件"},
        "Q09": {"status": "FAIL", "detail": "2024-Q3: GrossProfit=12B > Revenue=11.5B"},
        ...
      }
    }
    """
    ticker = ticker.upper()
    fields = normalized.get("fields", {})
    results: dict[str, dict] = {}

    results["Q01"] = _check_q01(fields)
    results["Q02"] = _check_q02(fields)
    results["Q03"] = _check_q03(fields)
    results["Q04"] = _check_q04(fields)
    results["Q05"] = _check_q05(fields)
    results["Q06"] = _check_q06(fields)
    results["Q07"] = _check_q07(fields)
    results["Q08"] = _check_q08(fields)
    results["Q09"] = _check_q09(fields)
    results["Q10"] = _check_q10(fields)
    results["Q11"] = _check_q11(fields)
    results["Q12"] = _check_q12(fields, raw.get("fields", {}))
    results["Q13"] = _check_q13(ticker, fields)

    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    failed = sum(1 for r in results.values() if r["status"] == "FAIL")

    logger.info("[%s] QC: %d/%d PASS", ticker, passed, passed + failed)
    return {
        "ticker": ticker,
        "checked_at": datetime.now().isoformat(),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


# ---------------------------------------------------------------------------
# 量的チェック
# ---------------------------------------------------------------------------

def _check_q01(fields: dict) -> dict:
    """直近8四半期でOCFの欠損が2以下"""
    entries = _get_quarterly(fields, "OCF", limit=8)
    missing = max(0, 8 - len(entries))
    if missing <= 2:
        return _pass(f"欠損{missing}件")
    return _fail(f"欠損{missing}件（8Q中{len(entries)}件のみ）")


def _check_q02(fields: dict) -> dict:
    """直近8四半期でRevenueの欠損が1以下"""
    entries = _get_quarterly(fields, "Revenue", limit=8)
    missing = max(0, 8 - len(entries))
    if missing <= 1:
        return _pass(f"欠損{missing}件")
    return _fail(f"欠損{missing}件（8Q中{len(entries)}件のみ）")


def _check_q03(fields: dict) -> dict:
    """年次データが最低4期分存在する"""
    # OCFまたはRevenueの年次エントリ数で確認
    count = 0
    for field_name in ("OCF", "Revenue", "NetIncome"):
        annual = _get_annual(fields, field_name)
        if len(annual) >= 4:
            return _pass(f"{field_name}の年次{len(annual)}期")
        count = max(count, len(annual))
    return _fail(f"年次データ不足（最大{count}期）")


def _check_q04(fields: dict) -> dict:
    """SharesDilutedが直近4四半期すべて存在する"""
    entries = _get_quarterly(fields, "SharesDiluted", limit=4)
    if len(entries) >= 4:
        return _pass("4Q全揃い")
    return _fail(f"直近4Q中{len(entries)}件のみ")


# ---------------------------------------------------------------------------
# 質的チェック
# ---------------------------------------------------------------------------

def _check_q05(fields: dict) -> dict:
    """Revenue前四半期比 ±80%以内"""
    entries = _get_quarterly(fields, "Revenue", limit=9)
    if len(entries) < 2:
        return _pass("比較データ不足（スキップ）")

    violations: list[str] = []
    for i in range(len(entries) - 1):
        curr = entries[i]
        prev = entries[i + 1]
        prev_val = prev["val"]
        if prev_val == 0:
            continue
        ratio = (curr["val"] - prev_val) / abs(prev_val)
        if abs(ratio) > 0.80:
            violations.append(
                f"{curr['end']}: {ratio:+.1%} vs {prev['end']}"
            )

    if not violations:
        return _pass("急変なし")
    return _fail(f"急変検出: {'; '.join(violations)}")


def _check_q06(fields: dict) -> dict:
    """OCFが5期連続でRevenueの±200%以内"""
    ocf_entries = _get_quarterly(fields, "OCF", limit=5)
    rev_entries = _get_quarterly(fields, "Revenue", limit=5)

    rev_by_end = {e["end"]: e["val"] for e in rev_entries}
    violations: list[str] = []

    for e in ocf_entries:
        rev = rev_by_end.get(e["end"])
        if rev is None or rev == 0:
            continue
        ratio = abs(e["val"]) / abs(rev)
        if ratio > 2.0:
            violations.append(f"{e['end']}: OCF/Rev={ratio:.1f}x")

    if not violations:
        return _pass("OCF/Rev比正常")
    return _fail(f"OCF/Rev超過: {'; '.join(violations)}")


def _check_q07(fields: dict) -> dict:
    """Cash残高が正値"""
    entries = _get_quarterly(fields, "Cash", limit=4)
    if not entries:
        return _pass("Cashデータなし（スキップ）")
    negatives = [e for e in entries if e["val"] < 0]
    if not negatives:
        return _pass("Cash正値確認")
    return _fail(f"Cash負値: {[e['end'] for e in negatives]}")


def _check_q08(fields: dict) -> dict:
    """FinanceLeasePmtsがCapEx以下（または欠損）"""
    flp_entries = _get_quarterly(fields, "FinanceLeasePmts", limit=4)
    if not flp_entries:
        return _pass("FinanceLeasePmtsなし（スキップ）")

    capex_entries = _get_quarterly(fields, "CapEx", limit=4)
    capex_by_end = {e["end"]: abs(e["val"]) for e in capex_entries}

    violations: list[str] = []
    for e in flp_entries:
        capex = capex_by_end.get(e["end"])
        if capex is None:
            continue
        if abs(e["val"]) > capex:
            violations.append(
                f"{e['end']}: FLP={abs(e['val']):.0f} > CapEx={capex:.0f}"
            )

    if not violations:
        return _pass("FLP/CapEx関係正常")
    return _fail(f"FLP>CapEx: {'; '.join(violations)}")


# ---------------------------------------------------------------------------
# 整合性チェック
# ---------------------------------------------------------------------------

def _check_q09(fields: dict) -> dict:
    """GrossProfit <= Revenue"""
    gp_entries = _get_quarterly(fields, "GrossProfit", limit=8)
    rev_entries = _get_quarterly(fields, "Revenue", limit=8)

    rev_by_end = {e["end"]: e["val"] for e in rev_entries}
    violations: list[str] = []

    for e in gp_entries:
        rev = rev_by_end.get(e["end"])
        if rev is None:
            continue
        if e["val"] > rev:
            violations.append(
                f"{e['end']}: GP={e['val']/1e9:.1f}B > Rev={rev/1e9:.1f}B"
            )

    if not violations:
        return _pass("GP<=Revenue 確認")
    return _fail(f"GP超過: {'; '.join(violations)}")


def _check_q10(fields: dict) -> dict:
    """期間の重複・ギャップが2四半期以上ない"""
    # OCF または Revenue の end_date シーケンスで確認
    for field_name in ("OCF", "Revenue"):
        entries = _get_quarterly(fields, field_name, limit=20)
        if len(entries) < 3:
            continue

        ends = sorted(e["end"] for e in entries)
        max_gap_days = 0
        for i in range(len(ends) - 1):
            d1 = date.fromisoformat(ends[i])
            d2 = date.fromisoformat(ends[i + 1])
            gap = (d2 - d1).days
            max_gap_days = max(max_gap_days, gap)

        # 2四半期以上のギャップ = 180日超
        if max_gap_days > 185:
            return _fail(
                f"{field_name}: 最大ギャップ{max_gap_days}日（2Q超）"
            )
        return _pass(f"{field_name}: 最大ギャップ{max_gap_days}日")

    return _pass("比較データ不足（スキップ）")


def _check_q11(fields: dict) -> dict:
    """同一end_dateに複数の非重複エントリがない"""
    for field_name, entries in fields.items():
        if field_name.startswith("_"):
            continue
        q_entries = [e for e in entries if not e.get("is_annual")]
        end_counts: dict[str, int] = {}
        for e in q_entries:
            end_counts[e["end"]] = end_counts.get(e["end"], 0) + 1
        duplicates = {k: v for k, v in end_counts.items() if v > 1}
        if duplicates:
            return _fail(f"{field_name}: 重複end_date={list(duplicates.keys())[:3]}")
    return _pass("重複なし")


def _check_q12(fields: dict, raw_fields: dict) -> dict:
    """
    YTD→Q変換後の差分合計が元のYTD値と一致するか検証（±5%以内）。

    正規化後の Q1+Q2+Q3 の合計 ≈ 元の Q3 YTD raw 値 であるはずなので、
    この照合で変換精度を確認する。
    """
    # raw の最新 Q3 YTD エントリを取得
    raw_ocf = raw_fields.get("OCF", [])
    ytd_q3_entries = [
        e for e in raw_ocf
        if e.get("is_ytd") and e.get("fp") == "Q3"
    ]
    if not ytd_q3_entries:
        return _pass("YTDデータなし（スキップ）")

    latest_ytd_q3 = max(ytd_q3_entries, key=lambda x: x["end"])
    q3_ytd_val = latest_ytd_q3["val"]
    q3_end = latest_ytd_q3["end"]
    fy_start = latest_ytd_q3.get("start", "")

    # 正規化後の同FY内 Q1+Q2+Q3 合計
    # fy_start <= start かつ end <= q3_end の四半期エントリを集計
    norm_ocf = _get_quarterly(fields, "OCF", limit=20)
    fy_qs = [
        e for e in norm_ocf
        if e.get("start", "") >= fy_start and e["end"] <= q3_end
    ]

    if len(fy_qs) < 3:
        return _pass("FY対応Qデータ不足（スキップ）")

    q_sum = sum(e["val"] for e in fy_qs)

    if q3_ytd_val == 0:
        return _pass("YTD値=0（スキップ）")

    diff_ratio = abs(q_sum - q3_ytd_val) / abs(q3_ytd_val)
    if diff_ratio <= 0.05:
        return _pass(f"差分{diff_ratio:.1%}（<=5%）")
    return _fail(
        f"差分{diff_ratio:.1%}（>5%）: "
        f"正規化合計={q_sum:.0f} vs YTD={q3_ytd_val:.0f}"
    )


def _check_q13(ticker: str, fields: dict) -> dict:
    """銘柄別制限フィールドが除外されている"""
    restrictions = TICKER_RESTRICTIONS.get(ticker)
    if not restrictions:
        return _pass("制限なし")

    excluded = restrictions.get("exclude", [])
    violations: list[str] = []
    for field_name in excluded:
        entries = fields.get(field_name, [])
        non_empty = [e for e in entries if e.get("val") is not None]
        if non_empty:
            violations.append(f"{field_name}が除外されていない（{len(non_empty)}件）")

    if not violations:
        return _pass(f"除外フィールド確認: {excluded}")
    return _fail("; ".join(violations))


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def _get_quarterly(fields: dict, field_name: str, limit: int) -> list:
    """フィールドの四半期エントリを新しい順でlimit件返す"""
    entries = fields.get(field_name, [])
    q = [e for e in entries if not e.get("is_annual")]
    return sorted(q, key=lambda x: x["end"], reverse=True)[:limit]


def _get_annual(fields: dict, field_name: str) -> list:
    """フィールドの年次エントリを新しい順で返す"""
    entries = fields.get(field_name, [])
    return sorted(
        [e for e in entries if e.get("is_annual")],
        key=lambda x: x["end"],
        reverse=True,
    )


def _pass(detail: str) -> dict:
    return {"status": "PASS", "detail": detail}


def _fail(detail: str) -> dict:
    return {"status": "FAIL", "detail": detail}
