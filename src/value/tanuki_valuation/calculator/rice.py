"""
TANUKI VALUATION - RICE Calculator
RICE = Reinvestment & Compounding Efficiency

定義:
    RICE = (G × Q × CF) / WACC

変数:
    G    : TANUKIシナリオ別forward成長率（bear/base/bull）
    Q    : OCF ÷ 純利益（直近3年平均）キャッシュ転換効率
    CF   : 売上成長率 ÷ 投資強度（1年ラグ・直近3年平均）投資再生産効率
           投資強度 = (R&D + CapEx) / Revenue
    WACC : TANUKI VALUATION計算値

設計方針:
    - RICEは「投資効率の純粋な測定指標」として割り切る
    - PERに対する相対評価（RICE/PER）で銘柄間比較に使用
    - 総合的な割高・割安判定はRICEを含む複数指標の組み合わせで将来設計（課題）

データソース:
    - annual_{year}.json の cf.operating_cash_flow / pl.net_income
    - annual_{year}.json の pl.revenue / cf.capital_expenditure
    - pl.research_and_development（R&D費）
    - シナリオ成長率: scenario_valuations（core_calculatorが計算済み）
    - WACC: wacc_result.value（core_calculatorが計算済み）

注意:
    - R&Dが annual_{year}.json に存在しない銘柄は CapEx のみで投資強度を計算
    - OCF/純利益が両方ゼロの年は Q 計算から除外
    - CF計算に必要な最低年数: 4年分（1年ラグ + 3点平均）
"""

import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class RICEScenario:
    """シナリオ別RICE結果"""
    growth_rate: float          # G: forward成長率
    rice: float                 # RICE値
    rice_per_ratio: float       # RICE / PER（PERが利用可能な場合のみ）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "growth_rate": round(self.growth_rate, 4),
            "rice": round(self.rice, 3),
            "rice_per_ratio": round(self.rice_per_ratio, 4),
        }


@dataclass
class RICEResult:
    """RICE計算結果"""
    # 構成要素
    q: float                    # OCF転換効率（直近3年平均）
    cf_conversion: float        # 投資再生産効率（1年ラグ・直近3年平均）
    wacc: float                 # WACC

    # 内訳（デバッグ・表示用）
    q_years: int                # Q計算に使用した年数
    cf_years: int               # CF計算に使用した年数
    avg_intensity: float        # 平均投資強度
    avg_rev_growth: float       # 平均売上成長率（ラグあり）

    # シナリオ別RICE
    bear: Optional[RICEScenario] = None
    base: Optional[RICEScenario] = None
    bull: Optional[RICEScenario] = None

    # メタ
    available: bool = True
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "available": self.available,
            "q": round(self.q, 4),
            "cf_conversion": round(self.cf_conversion, 4),
            "wacc": round(self.wacc, 4),
            "q_years": self.q_years,
            "cf_years": self.cf_years,
            "avg_intensity": round(self.avg_intensity, 4),
            "avg_rev_growth_lagged": round(self.avg_rev_growth, 4),
            "note": self.note,
        }
        if self.bear:
            d["bear"] = self.bear.to_dict()
        if self.base:
            d["base"] = self.base.to_dict()
        if self.bull:
            d["bull"] = self.bull.to_dict()
        return d


def _calc_q(annual_data: List[Dict[str, Any]], years: int = 3) -> Tuple[float, int]:
    """
    Q = OCF ÷ 純利益（直近3年平均）

    Args:
        annual_data: get_annual_range()の返却値（新しい順）
        years: 計算年数

    Returns:
        (Q値, 使用年数)
    """
    q_list = []
    for data in annual_data[:years]:
        ocf = data.get("cf", {}).get("operating_cash_flow")
        ni  = data.get("pl", {}).get("net_income")
        if ocf is not None and ni is not None and ni != 0:
            q_list.append(ocf / ni)

    if not q_list:
        return 0.0, 0

    return sum(q_list) / len(q_list), len(q_list)


def _calc_cf_lagged(annual_data: List[Dict[str, Any]], years: int = 3) -> Tuple[float, int, float, float]:
    """
    CF = 売上成長率(t+1) ÷ 投資強度(t)（1年ラグ・直近N点平均）

    annual_data は新しい順（annual_data[0]が最新）なので
    インデックスの扱いに注意:
        t   = annual_data[i+1]  （古い年）
        t+1 = annual_data[i]    （新しい年）

    Args:
        annual_data: get_annual_range()の返却値（新しい順）
        years: 使用するラグペアの数（最低3点）

    Returns:
        (CF値, 使用年数, 平均投資強度, 平均売上成長率)
    """
    cf_list       = []
    intensity_list = []
    rev_growth_list = []

    # annual_data[0]=最新, annual_data[1]=1年前, ...
    # ペア: (t=data[i+1], t+1=data[i]) で i=0,1,...
    for i in range(min(years, len(annual_data) - 1)):
        newer = annual_data[i]      # t+1年
        older = annual_data[i + 1]  # t年

        # 投資強度(t年) = (R&D + CapEx) / Revenue
        rev_t     = older.get("pl", {}).get("revenue")
        capex_t   = older.get("cf", {}).get("capital_expenditure")
        rd_t      = older.get("pl", {}).get("research_and_development")  # 存在しない場合はNone

        if rev_t is None or rev_t == 0 or capex_t is None:
            continue

        # R&Dがない場合はCapExのみで投資強度を計算
        invest_t = abs(capex_t) + (abs(rd_t) if rd_t is not None else 0.0)
        intensity_t = invest_t / rev_t

        # 売上成長率(t+1年)
        rev_t1 = newer.get("pl", {}).get("revenue")
        if rev_t1 is None or rev_t == 0:
            continue

        rev_growth_t1 = (rev_t1 - rev_t) / abs(rev_t)

        if intensity_t == 0:
            continue

        cf_point = rev_growth_t1 / intensity_t
        cf_list.append(cf_point)
        intensity_list.append(intensity_t)
        rev_growth_list.append(rev_growth_t1)

    if not cf_list:
        return 0.0, 0, 0.0, 0.0

    cf_avg        = sum(cf_list) / len(cf_list)
    intensity_avg = sum(intensity_list) / len(intensity_list)
    rev_growth_avg = sum(rev_growth_list) / len(rev_growth_list)

    return cf_avg, len(cf_list), intensity_avg, rev_growth_avg


def calculate_rice(
    annual_data: List[Dict[str, Any]],
    wacc: float,
    scenario_valuations: Optional[Dict[str, Any]],
    current_per: float = 0.0,
    q_years: int = 3,
    cf_years: int = 3,
) -> RICEResult:
    """
    RICE計算メイン関数

    Args:
        annual_data:          get_annual_range()の返却値（新しい順、最低4年分推奨）
        wacc:                 TANUKI VALUATIONが計算したWACC
        scenario_valuations:  latest.jsonの scenario_valuations（bear/base/bull成長率）
        current_per:          現在のPER（RICE/PER計算用、0の場合は比率計算をスキップ）
        q_years:              Q計算年数（デフォルト3）
        cf_years:             CF計算年数（デフォルト3）

    Returns:
        RICEResult
    """
    # ── データ不足チェック ──
    if len(annual_data) < 2:
        return RICEResult(
            q=0.0, cf_conversion=0.0, wacc=wacc,
            q_years=0, cf_years=0,
            avg_intensity=0.0, avg_rev_growth=0.0,
            available=False,
            note="年次データ不足（最低2年分必要）"
        )

    # ── Q計算 ──
    q, q_used = _calc_q(annual_data, q_years)
    if q_used == 0:
        return RICEResult(
            q=0.0, cf_conversion=0.0, wacc=wacc,
            q_years=0, cf_years=0,
            avg_intensity=0.0, avg_rev_growth=0.0,
            available=False,
            note="Q計算不可（OCF/純利益データなし）"
        )

    # ── CF計算（1年ラグ） ──
    cf, cf_used, avg_intensity, avg_rev_growth = _calc_cf_lagged(annual_data, cf_years)
    if cf_used == 0:
        return RICEResult(
            q=q, cf_conversion=0.0, wacc=wacc,
            q_years=q_used, cf_years=0,
            avg_intensity=0.0, avg_rev_growth=0.0,
            available=False,
            note="CF計算不可（Revenue/CapExデータなし）"
        )

    # ── シナリオ別RICE計算 ──
    scenarios: Dict[str, Optional[RICEScenario]] = {
        "bear": None, "base": None, "bull": None
    }

    if scenario_valuations and wacc > 0:
        for sc_name in ("bear", "base", "bull"):
            sc = scenario_valuations.get(sc_name)
            if sc is None:
                continue
            g = sc.get("growth_rate")
            if g is None:
                continue

            rice_val = (g * q * cf) / wacc
            ratio = rice_val / current_per if current_per > 0 else 0.0
            scenarios[sc_name] = RICEScenario(
                growth_rate=g,
                rice=rice_val,
                rice_per_ratio=ratio,
            )

    # ── ノート生成 ──
    note_parts = []
    if q_used < q_years:
        note_parts.append(f"Q: {q_used}年のみ使用（{q_years}年要求）")
    if cf_used < cf_years:
        note_parts.append(f"CF: {cf_used}点のみ使用（{cf_years}点要求）")
    note = "、".join(note_parts) if note_parts else ""

    return RICEResult(
        q=q,
        cf_conversion=cf,
        wacc=wacc,
        q_years=q_used,
        cf_years=cf_used,
        avg_intensity=avg_intensity,
        avg_rev_growth=avg_rev_growth,
        bear=scenarios["bear"],
        base=scenarios["base"],
        bull=scenarios["bull"],
        available=True,
        note=note,
    )


if __name__ == "__main__":
    # 簡易テスト（annual_dataのモックで動作確認）
    mock_annual = [
        # FY2026（最新）
        {"pl": {"revenue": 215_938_000_000, "net_income": 72_880_000_000, "research_and_development": 12_910_000_000},
         "cf": {"operating_cash_flow": 96_000_000_000, "capital_expenditure": -1_330_000_000}},
        # FY2025
        {"pl": {"revenue": 130_497_000_000, "net_income": 29_760_000_000, "research_and_development": 8_680_000_000},
         "cf": {"operating_cash_flow": 64_090_000_000, "capital_expenditure": -1_070_000_000}},
        # FY2024
        {"pl": {"revenue": 60_922_000_000, "net_income": 4_370_000_000, "research_and_development": 5_870_000_000},
         "cf": {"operating_cash_flow": 28_080_000_000, "capital_expenditure": -700_000_000}},
        # FY2023
        {"pl": {"revenue": 26_974_000_000, "net_income": 4_370_000_000, "research_and_development": 3_970_000_000},
         "cf": {"operating_cash_flow": 5_640_000_000, "capital_expenditure": -600_000_000}},
    ]

    mock_scenarios = {
        "bear": {"growth_rate": 0.227, "intrinsic_value_per_share": 284.21},
        "base": {"growth_rate": 0.325, "intrinsic_value_per_share": 408.67},
        "bull": {"growth_rate": 0.390, "intrinsic_value_per_share": 514.03},
    }

    result = calculate_rice(
        annual_data=mock_annual,
        wacc=0.10285,
        scenario_valuations=mock_scenarios,
        current_per=35.0,
    )

    import json
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
