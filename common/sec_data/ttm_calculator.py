"""
common/sec_data/ttm_calculator.py
責務: 直近4四半期を合算してTTM値を計算する（Rolling TTM系列）
出力: ttm/{ticker}_ttm_series.json（calc_ttm_series()/save_ttm_series()）

フェーズC（移行実装計画8章）: 入力元をnormalizer.py::normalize()の
戻り値（PascalCase、26フィールド）からlayer3_builder.py::
build_ticker_store()の戻り値（snake_case、Layer3の32フィールド）へ
切替済み。FLOW_FIELDS等の分類定数もsnake_caseへ統一した。
"""

import json
import logging
import os
from datetime import date, datetime

from .contracts import validate_field_classification
from .layer3_builder import load_concept_definitions, get_field_entries
from .q4_implied import build_q4_implied_entries

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
TTM_DIR = os.path.join(BASE_DIR, "ttm")

# フロー系フィールド（4Q合算）。Layer3（config/sec_concept_definitions.json）
# のcategory="flow"に対応するsnake_caseフィールド名（17件）。
FLOW_FIELDS = frozenset([
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
    "capital_expenditure", "finance_lease_payments",
    "stock_based_compensation", "depreciation_and_amortization",
    "revenue", "gross_profit", "operating_income", "net_income",
    "research_and_development", "selling_and_marketing", "buyback",
    "eps_basic", "eps_diluted", "selling_general_and_administrative",
])

# ストック系フィールド（最新Q末の値）。Layer3のcategory="stock"（10件）。
# CurrentAssets/CurrentLiabilities: GATE2-PHASE3B-1②で追加（貸借対照表項目の
# ためフロー〈4Q合算〉ではなくストック〈最新Q末の値〉分類が妥当。抽出はされて
# いたがFLOW/STOCK/SHARESいずれにも属さず消費者ゼロのままTTM出力から漏れて
# いた既知バグの是正）
#
# 【TTM-STOCK-FIELDS-DEAD-1 2026-07-18】この分類自体を実際に処理していた
# calc_ttm()/save_ttm()は本番未到達コードだったため削除した（本番経路は
# FLOW_FIELDSのみを扱うcalc_ttm_series()）。STOCK_FIELDSは以下2点のためだけに
# 残置している:
#   ① 下記validate_field_classification()の引数（Layer3フィールド定義の
#      全キーがFLOW/STOCK/SHARES/EXCLUDEDのいずれかに分類されることを
#      import時に保証する契約チェック。EXCLUDED_FIELDSへ統合すると
#      「意図的除外」の意味が変わってしまうため統合しない）
#   ② long_term_debt/shares_basic_weighted_avg/shares_diluted等は別経路
#      （reader.py・audit.py・quarterly_review_generator.py・
#      tail_dcf_bridge.py・pipeline.pyがnormalized JSONを直接読む）で
#      個別に生存しているため、それらの分類上の位置づけとしても意味を
#      保っている
STOCK_FIELDS = frozenset([
    "cash_and_equivalents", "short_term_debt", "long_term_debt",
    "deferred_revenue", "stockholders_equity", "total_assets",
    "current_assets", "current_liabilities",
    "short_term_investments", "total_liabilities",
])

# 株式数フィールド（最新Q末の値）。Layer3のcategory="shares"（3件）。
# TTM-STOCK-FIELDS-DEAD-1 2026-07-18: STOCK_FIELDSと同じ理由
# （validate_field_classification()契約チェックのための残置）で
# calc_ttm_series()経由では使われない。個別実装（reader.py等）で別途生存。
SHARES_FIELDS = frozenset([
    "shares_diluted", "shares_basic_weighted_avg",
    "shares_outstanding_period_end_sec",
])

# 意図的にTTM出力対象外とするフィールド（GATE2-PHASE3B-1②で新設）。
# Layer3のcategory="excluded"（2件）。FLOW_FIELDS/STOCK_FIELDS/
# SHARES_FIELDSのいずれにも入れず、かつ「分類漏れ」として検知されない
# ようにするための明示的な除外リスト。
EXCLUDED_FIELDS = frozenset([
    # GrossProfit逆算用の内部計算専用フィールド。単独でTTM出力する意味が
    # ないため対象外は意図的。
    "cost_of_revenue",
    # reader.py::get_rpo_series()/get_rpo_context()がnormalized JSONを
    # 直接読む別経路で消費されるため、TTM層での分類は不要（GATE2-PHASE3B-1
    # 事前調査で確認済み。ttm.jsonを経由しないだけで実際には正常に消費されている）。
    "rpo",
])

# GATE2-PHASE3B-1②規約C: Layer3フィールド定義（config/
# sec_concept_definitions.json::fields、32キー）の全キーが上記4分類の
# いずれかに属することをモジュールロード時に検証する。新フィールド追加時に
# 分類を忘れると黙って出力から消える問題（CurrentAssets/CurrentLiabilities
# の実例）を、import時点で即座に検知するため。
_LAYER3_FIELD_DEFS = load_concept_definitions().get("fields", {})
validate_field_classification(_LAYER3_FIELD_DEFS, FLOW_FIELDS, STOCK_FIELDS, SHARES_FIELDS, EXCLUDED_FIELDS)

# Q4 implied生成本体はcommon/sec_data/q4_implied.py::build_q4_implied_entries()
# に集約済み（[[Q4-IMPLIED-CALC-TRIPLICATION-1]]対応、移行実装計画フェーズB）。
# BUG-TTM-Q4DUP-1（既存end日付との重複防止）・RICE-TTM-CAPEX-SUM-SIGN-1
# （field_name=="CapEx"時のabs()適用）は共有関数側に同等の実装として維持。


# ---------------------------------------------------------------------------
# Rolling TTM系列
# ---------------------------------------------------------------------------

def _calc_fcf(
    ocf: float | None,
    capex: float | None,
    fl: float | None,
    da: float | None = None,
) -> float | None:
    """
    FCF計算（parser.pyと同じ計算式）。

    FCF = OCF - (|CapEx| - |FinanceLeasePmts|)
    ファイナンスリースはCapExから除外（AMZN等対応）。

    OCF または CapEx が None の場合は None を返す。
    FinanceLeasePmts が None の場合は 0 として扱う。
    """
    if ocf is None or capex is None:
        return None
    pure_capex = abs(capex) - abs(fl or 0)
    return ocf - max(0, pure_capex)


def _select_anchors(all_end_dates: list[str], n_periods: int) -> list[str]:
    """
    anchor[0] = all_end_dates[0]（最新Q）
    anchor[i] = anchor[i-1] から約365日前に最も近い end_date

    許容差分: 305〜425日（365±60日）
    範囲外の場合はそのanchorをスキップ（n_periodsに満たなくても継続）。
    """
    if not all_end_dates:
        return []

    anchors: list[str] = [all_end_dates[0]]

    for _ in range(n_periods - 1):
        prev = anchors[-1]
        prev_date = date.fromisoformat(prev)

        best: str | None = None
        best_diff: int | None = None

        for d in all_end_dates:
            if d >= prev:
                continue
            gap = (prev_date - date.fromisoformat(d)).days
            if 305 <= gap <= 425:
                diff = abs(gap - 365)
                if best_diff is None or diff < best_diff:
                    best = d
                    best_diff = diff

        if best is None:
            break

        gap_actual = (prev_date - date.fromisoformat(best)).days
        if gap_actual < 305:
            logger.warning(
                "anchor gap too small: %s → %s (%d days)", prev, best, gap_actual
            )

        anchors.append(best)

    return anchors


def calc_ttm_series(
    ticker: str,
    store: dict,
    n_periods: int = 6,
) -> list[dict]:
    """
    Rolling TTM系列を生成する。
    直近Qをanchor[0]とし、約1年(4Q)ずつ遡ってn_periods点を計算。

    n_periods=6 の理由: rice.pyのCF計算が3年分必要（4点）+ FCF用5点 → 安全マージン6点

    storeはlayer3_builder.py::build_ticker_store()の戻り値（インメモリ、
    ファイル経由にしない。フェーズC対応）。フィールド抽出は
    layer3_builder.py::get_field_entries()経由で行う。

    戻り値: ttm_end降順のリスト
    [
      {
        "ttm_end": "2026-01-25",
        "flow": {
          "operating_cash_flow":     {"val": ..., "quarters_used": 4, "missing": 0},
          "capital_expenditure":     {"val": ..., "quarters_used": 4, "missing": 0},
          "finance_lease_payments":  {"val": ..., "quarters_used": 4, "missing": 0},
          "FCF":                     {"val": ...},
          "revenue":                 {"val": ..., "quarters_used": 4, "missing": 0},
          "net_income":              {"val": ..., "quarters_used": 4, "missing": 0},
          "research_and_development":{"val": ..., "quarters_used": 4, "missing": 0},
          "selling_and_marketing":   {"val": ..., "quarters_used": 4, "missing": 2},
        }
      },
      ...
    ]
    """
    ticker = ticker.upper()
    field_names = store.get("fields", {}).keys()

    # 各フィールドを四半期・年次に分離
    quarterly_by_field: dict[str, list] = {}
    annual_by_field: dict[str, list] = {}

    for field_name in field_names:
        entries = get_field_entries(store, field_name)
        quarterly_by_field[field_name] = sorted(
            [e for e in entries if not e.get("is_annual")],
            key=lambda x: x["end"],
            reverse=True,
        )
        annual_by_field[field_name] = sorted(
            [e for e in entries if e.get("is_annual")],
            key=lambda x: x["end"],
            reverse=True,
        )

    # Q4 implied 合成エントリを計算し、quarterly に追加
    # [[LAYER3-TTM-REGRESSION-NEWFIELD-BLINDSPOT-1]]対応（2026-07-29投資調査）:
    # FLOW_FIELDSにはeps_basic/eps_dilutedが含まれるが、両者は比率フィールド
    # （加重平均株式数で変動するため単純合算・差分が数学的に無意味）であり、
    # q4_implied.py::Q4_IMPLIED_FIELDSのガードに含まれないため
    # build_q4_implied_entries()は常に空リストを返す（実害なし、冗長な
    # 呼び出しのみ）。この2フィールドをFLOW_FIELDSから除外する対応は
    # 本ループの外側（validate_field_classification()の分類契約）に影響する
    # ため今回は行わない。short_term_investments/total_liabilitiesは
    # category="stock"のためFLOW_FIELDSに含まれず、本ループに到達しない。
    for field_name in FLOW_FIELDS:
        q4_list = build_q4_implied_entries(
            annual_by_field.get(field_name, []),
            quarterly_by_field.get(field_name, []),
            field_name,
        )
        if q4_list:
            merged = sorted(
                quarterly_by_field.get(field_name, []) + q4_list,
                key=lambda x: x["end"],
                reverse=True,
            )
            quarterly_by_field[field_name] = merged

    # anchor選択: FLOW_FIELDS の全 end_date の union を使用
    all_end_dates: list[str] = sorted(
        {
            e["end"]
            for field_name in FLOW_FIELDS
            for e in quarterly_by_field.get(field_name, [])
        },
        reverse=True,
    )

    anchors = _select_anchors(all_end_dates, n_periods)

    series: list[dict] = []
    for anchor in anchors:
        flow: dict = {}

        for field_name in FLOW_FIELDS:
            q_entries = [
                e for e in quarterly_by_field.get(field_name, [])
                if e["end"] <= anchor
            ]
            last4 = q_entries[:4]
            if not last4:
                continue
            total = sum(e["val"] or 0 for e in last4)
            flow[field_name] = {
                "val": total,
                "quarters_used": len(last4),
                "missing": max(0, 4 - len(last4)),
            }

        # FCF計算（派生値・quarters_used/missingなし）
        ocf_val   = flow.get("operating_cash_flow", {}).get("val")
        capex_val = flow.get("capital_expenditure", {}).get("val")
        fl_val    = flow.get("finance_lease_payments", {}).get("val")
        da_val    = flow.get("depreciation_and_amortization", {}).get("val")  # v8.2: 維持CapEx分離用
        fcf_val = _calc_fcf(ocf_val, capex_val, fl_val, da_val)
        if fcf_val is not None:
            flow["FCF"] = {"val": fcf_val}

        series.append({
            "ttm_end": anchor,
            "flow": flow,
        })

    logger.info("[%s] TTM series calculated: %d periods", ticker, len(series))
    return series


def save_ttm_series(ticker: str, series: list[dict], n_periods: int = 6) -> str:
    """TTM系列をJSONファイルに保存し、パスを返す"""
    os.makedirs(TTM_DIR, exist_ok=True)
    path = os.path.join(TTM_DIR, f"{ticker.upper()}_ttm_series.json")
    data = {
        "ticker": ticker.upper(),
        "generated_at": datetime.now().isoformat(),
        "n_periods": n_periods,
        "series": series,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("[%s] TTM series saved -> %s", ticker, path)
    return path
