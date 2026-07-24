"""
common/sec_data/q4_implied.py
責務: 「FY年次値 - (Q1+Q2+Q3) = Q4」のQ4逆算ロジックの単一集約実装。

[[Q4-IMPLIED-CALC-TRIPLICATION-1]]対応（移行実装計画フェーズB）。
従来normalizer.py::_build_q4_implied_entries()・
ttm_calculator.py::_build_q4_quarterly_entries()・
discover/stonks-silo/src/financial_trend_calculator.py::_build_q4_implied()
の3箇所に独立実装されていたロジックを本モジュールに統一する。

適用範囲のガード（重要）:
この近似（FY年次値からQ1+Q2+Q3を差し引く）はフロー系（累積可能）
フィールドでのみ数学的に有効であり、shares系（加重平均株式数）や
stock系（残高スナップショット）に適用すると符号反転等の無意味な値を
生む（layer3_builder.py実装中〈フェーズA〉にshares_diluted等で実際に
発生・修正したバグ）。このため本モジュールはQ4_IMPLIED_FIELDS
（フロー系フィールドの許可リスト）に含まれるfield_nameでのみ計算を
実行するガードを設ける。

Q4_IMPLIED_FIELDSの構成について:
normalizer.py::Q4_IMPLIED_FIELDS（13フィールド）とttm_calculator.py::
FLOW_FIELDS（14フィールド、Q4逆算にも同じ集合を使用）は、既存実装の
時点で完全には一致していなかった（FinanceLeasePmts・BuybackはttmのFLOW_
FIELDSのみに存在、_COGSはnormalizer側のみに存在）。実データ確認の結果、
FinanceLeasePmts（26銘柄）・Buyback（65銘柄）はttm_calculator.py側の
Q4逆算で実際に非空のimpliedエントリを生成していた（normalizer.py側は
この2フィールドをQ4逆算対象にしないため、ttm側の独自生成が実質的な
唯一の供給源になっている）。フェーズB集約時にこの2フィールドを除外すると
ttm/出力からimpliedエントリが消失し「値を変えない集約」という要件に反する
ため、両モジュールの既存許可フィールドの**和集合**（15フィールド）を
本モジュールのガードとして採用する。いずれも実際に加算可能なフロー系
概念であり、除外対象のshares/stock系フィールドとは性質が異なる。
"""

from __future__ import annotations

from datetime import date

# フロー系（累積・加算可能）フィールドの許可リスト。
# normalizer.py::Q4_IMPLIED_FIELDS ∪ ttm_calculator.py::FLOW_FIELDS。
# 上記docstring参照。
Q4_IMPLIED_FIELDS = frozenset({
    "Revenue", "_COGS",
    "OCF", "ICF", "CFF", "CapEx", "FinanceLeasePmts",
    "RD", "SM", "SBC", "DA",
    "NetIncome", "OperatingIncome", "GrossProfit",
    "Buyback",
})


def build_q4_implied_entries(
    annual_entries: list,
    quarterly_entries: list,
    field_name: str,
) -> list:
    """
    年次エントリ（is_annual=True）とQ1〜Q3の四半期エントリから、
    Q4 implied エントリを生成する。

    Q4 = FY年次値 - (Q1+Q2+Q3の合計)

    - field_nameがQ4_IMPLIED_FIELDSに含まれない場合は空リストを返す
      （shares/stock系フィールドへの誤適用防止ガード）。
    - 同一end日付の四半期エントリが既にquarterly_entries内に存在する
      場合はそのFYをスキップする（重複生成防止、旧ttm_calculator.py
      ::BUG-TTM-Q4DUP-1ガードと同等）。
    - field_name=="CapEx"の場合、算出したq4_valにabs()を適用する
      （[[CAPEX-SIGN-UNNORMALIZED-1]]・[[RICE-TTM-CAPEX-SUM-SIGN-1]]対応。
      normalizer.py側の最終出力時abs()と重複適用されても
      abs(abs(x))==abs(x)のため無害）。
    - 未来のFY（fy_end > 本日）はアナリスト予想化を避けるため対象外。
    """
    if field_name not in Q4_IMPLIED_FIELDS:
        return []

    today = date.today().isoformat()
    existing_ends = {e["end"] for e in quarterly_entries if not e.get("is_annual")}

    result: list = []
    for annual in annual_entries:
        fy_end = annual.get("end", "")
        fy_start = annual.get("start", "")
        fy_val = annual.get("val")

        if not fy_end or fy_val is None:
            continue
        if fy_end > today:
            continue
        if fy_end in existing_ends:
            continue

        fy_qs = [
            e for e in quarterly_entries
            if e.get("end", "") < fy_end
            and e.get("start", "") >= fy_start
            and not e.get("is_annual")
        ]
        top3 = sorted(fy_qs, key=lambda x: x["end"], reverse=True)[:3]
        if len(top3) < 3:
            continue

        q3_end = sorted(top3, key=lambda x: x["end"], reverse=True)[0]["end"]
        q4_val = fy_val - sum(e["val"] or 0 for e in top3)
        if field_name == "CapEx":
            q4_val = abs(q4_val)

        try:
            period_days = (date.fromisoformat(fy_end) - date.fromisoformat(q3_end)).days
        except (ValueError, TypeError):
            period_days = 90

        result.append({
            "end": fy_end,
            "start": q3_end,
            "val": q4_val,
            "fp": "Q4",
            "fy": annual.get("fy"),
            "form": "10-K",
            "filed": annual.get("filed", ""),
            "accn": annual.get("accn", ""),
            "period_days": period_days,
            "is_ytd": False,
            "is_annual": False,
            "is_implied": True,
        })

    return result
