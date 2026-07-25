"""
common/sec_data/layer3_builder.py
責務: Layer1（company_facts.json）＋Layer2（config/sec_concept_definitions.json）
から Layer3（32フィールド統合ストア）を生成する。

フェーズA（新規構築、既存コード非改変）: 詳細は
docs/architecture/new_data_platform/SEC_EDGAR_LAYER_DESIGN.md 8章を参照。
既存の data/・normalized/・raw/・ttm/ には一切書き込まない。
出力先: common/sec_data/store_v2/{TICKER}.json（新規パス）。

設計上の再利用（意図的）:
XBRLエントリの期間分類（10-Q/10-K・is_annual/is_ytd判定、
common/sec_data/quarterly.py::_classify_period()）と、同一期間内で
複数エントリが競合した場合のfiled日タイブレーク（同::_process_entries()、
内部でcommon/sec_data/fact_selection.py::select_latest_filed()を使用）は、
過去に複数回のバグ修正（PARSER-ENTG-COMPYEAR-1・XBRL-TAG-KLAC-1・
BUG-CON-YTD-1等）を経て確定した実装のため、重複再実装によるバグ再導入
リスクを避け、そのままimportして再利用する。

本モジュールで新規実装する部分（フェーズAの本来の目的）:
- Layer2 candidatesに基づくフィールド抽出（最初に見つかった非空候補を採用）
- sign_normalize（符号正規化、CAPEX-SIGN-UNNORMALIZED-1対応）
- YTD→単四半期差分変換（start/period_daysの再計算込み。
  NORMALIZER-YTD-METADATA-STALE-1のメタデータ不整合を修正）
- Q4逆算ロジックの単一集約実装（Q4-IMPLIED-CALC-TRIPLICATION-1対応の先取り。
  normalizer.py・ttm_calculator.py・financial_trend_calculator.pyの
  3箇所独立実装を、本モジュールでは1箇所に統一する）。適用範囲は
  normalizer.py::Q4_IMPLIED_FIELDSと同一の13フィールド（Q4_IMPLIED_FIELDS
  定数）に限定する。FY年次値からQ1+Q2+Q3を差し引く近似はフロー系
  （累積可能）フィールドでのみ有効であり、shares系（加重平均株式数）や
  stock系（残高スナップショット）に無条件適用すると符号反転等の
  無意味な値を生む（実装時に発見・修正）
- FCF計算の共有関数化（quarterly/annual生成側とTTM集計側の両方から
  呼べる設計。parser.py・ttm_calculator.pyの既存計算式と同一であることを
  確認済み: FCF = OCF - max(0, |CapEx| - |FinanceLeasePmts|)）

未実装（フェーズAのスコープ外、既知の制限。回帰レポートで扱う）:
- normalizer.py::_build_missing_quarter_implied_entries() 相当
  （Q4以外の任意欠落四半期の逆算）
- normalizer.py::_calc_gross_profit() 相当
  （Revenue - cost_of_revenue からのGrossProfit逆算）
- quarterly.py::TICKER_RESTRICTIONS 相当の銘柄別override
  （MSFTのexcludeのみ簡易反映、他8銘柄は未移行）
- quarterly.py::_FALLBACK_MIN/_FALLBACK_MIN_FIELDS 相当の
  「件数が少なければより多いフォールバックを採用」ロジック
  （単純に「最初に見つかった非空候補を採用」のみ）
- quarterly.py::_REVENUE_FALLBACKS のような複数タグ源のマージ
  （Revenueはcandidatesの中で最初に見つかった1タグのみを採用し、
  複数タグを合算しない）
"""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

from .quarterly import _classify_period, _process_entries
from .fact_selection import select_latest_filed  # noqa: F401  (contract of _process_entries)

logger = logging.getLogger(__name__)

# Q4逆算はフロー系（累積・加算可能）フィールドにのみ有効な近似
# （FY年次値 - (Q1+Q2+Q3) = Q4）。stock系（残高スナップショット）・
# shares系（加重平均株式数）に適用すると数学的に無意味な値（符号反転等）
# を生む。normalizer.py::Q4_IMPLIED_FIELDS（13フィールド、RPO等の
# ストック値は明示的に対象外）と同一スコープを踏襲する。
Q4_IMPLIED_FIELDS = frozenset({
    "revenue", "cost_of_revenue",
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
    "capital_expenditure",
    "research_and_development", "selling_and_marketing",
    "stock_based_compensation", "depreciation_and_amortization",
    "net_income", "operating_income", "gross_profit",
})

# LAYER3-FALLBACK-STALE-TAG-PRIORITY-1対応の対象外フィールド。
# rpo: [[LAYER3-RPO-CANDIDATE-ORDER-1]]は別途概念分離（総額系/長期系の
# 分離）で対応する前提のため、本対応では変更しない（該当BACKLOGの
# 着手条件は変更なし）。
# shares_basic_weighted_avg・shares_outstanding_period_end_sec: 加重平均
# （PL項目）と期末残高（BS項目）は異なる会計概念であり、元々別フィールドに
# 分離済み（[[SCHEMA-SHARESBASIC-CONCEPT-MISMATCH-1]]）。統合しない。
NO_CANDIDATE_MERGE_FIELDS = frozenset({
    "rpo",
    "shares_basic_weighted_avg",
    "shares_outstanding_period_end_sec",
})

BASE_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(REPO_ROOT, "config", "sec_concept_definitions.json")
STORE_V2_DIR = os.path.join(BASE_DIR, "store_v2")

_QUARTERLY_YEARS = 5
_ANNUAL_YEARS = 6


# ---------------------------------------------------------------------------
# Layer1 / Layer2 ロード
# ---------------------------------------------------------------------------

def load_company_facts(ticker: str) -> dict | None:
    """Layer1: common/sec_data/data/{TICKER}/company_facts.json を読み込む。"""
    path = os.path.join(DATA_DIR, ticker.upper(), "company_facts.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("[%s] company_facts.json 読み込み失敗: %s", ticker, e)
        return None


def load_concept_definitions() -> dict:
    """Layer2: config/sec_concept_definitions.json を読み込む。"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# フィールド抽出（Layer2 candidatesベースのフォールバック）
# ---------------------------------------------------------------------------

def _get_concept_units(company_facts: dict, concept: str, unit: str) -> list:
    """company_facts.facts.us-gaap.{concept}.units.{unit} を安全に取得する。"""
    try:
        return company_facts["facts"]["us-gaap"][concept]["units"][unit]
    except (KeyError, TypeError):
        return []


def extract_field_raw_entries(
    company_facts: dict, field_def: dict, field_name: str = "",
) -> tuple[list, str | None]:
    """
    Layer2のcandidatesからエントリを抽出する。

    [[LAYER3-FALLBACK-STALE-TAG-PRIORITY-1]]対応: field_nameが
    NO_CANDIDATE_MERGE_FIELDSに含まれない限り、候補タグごとに独立して
    正規化（YTD→単四半期変換）を完了させたうえで、その正規化済み系列を
    end_dateキーで優先順位マージする（_merge_candidate_entries参照）。
    「最初に見つかった非空候補を採用」方式は、直近データを持たない古い
    タグ（例: Revenues）が、より新しく実際に使われているタグより先に
    拾われてしまう問題があった（IONQ等で確認）。

    戻り値の正規化状態が呼び出し元（build_ticker_store）で分岐に使われる:
    NO_CANDIDATE_MERGE_FIELDS対象フィールドは従来通り「最初に見つかった
    非空候補を採用」方式を維持し、_process_entries()止まりの未正規化
    エントリを返す（呼び出し元が_normalize_field_entries()を適用する）。
    候補マージ対象フィールドは、本関数内で正規化まで完了させた結果を
    返す（呼び出し元は再度正規化しない。理由はモジュールdocstring・
    _merge_candidate_entries参照）。

    戻り値: (エントリのリスト, 採用したタグ名（複数採用時は"+"区切り）or None)
    """
    unit = field_def.get("unit", "USD")
    candidates = field_def.get("candidates", [])

    if field_name in NO_CANDIDATE_MERGE_FIELDS:
        for concept in candidates:
            raw_entries = _get_concept_units(company_facts, concept, unit)
            if not raw_entries:
                continue
            processed = _process_entries(raw_entries)
            if processed:
                return processed, concept
        return [], None

    return _merge_candidate_entries(company_facts, candidates, unit)


def _merge_candidate_entries(
    company_facts: dict, candidates: list, unit: str,
) -> tuple[list, str | None]:
    """
    候補タグごとに独立して_process_entries()→_normalize_field_entries()を
    適用し（各タグ内で完結したYTD→単四半期変換を完了させる）、得られた
    正規化済み系列同士をend_date単位で優先順位マージする。優先タグ
    （candidatesの先頭）にその期間のエントリがあれば採用し、なければ
    次候補にフォールバックする（_merge_normalized_by_priority参照）。

    設計変更の経緯: 当初は生エントリを先に統合してから正規化する順序
    だったが、異なるタグ由来のエントリが同一end_dateで競合した際の
    タイブレークが、_normalize_field_entries()内のFYチェーン判定
    （startの完全一致でグルーピング）を破壊し、YTD差分計算が中間四半期を
    1つ読み飛ばして2四半期分を1四半期として誤算出するバグを引き起こした
    （CPRT capital_expenditure・PEP他で実データ確認）。タグごとに
    独立して正規化を完了させてからマージすることで、この
    クロスタグ混入を構造的に防ぐ。
    """
    used_concepts: list = []
    per_tag_normalized: list = []
    for concept in candidates:
        raw_entries = _get_concept_units(company_facts, concept, unit)
        if not raw_entries:
            continue
        processed = _process_entries(raw_entries)
        if not processed:
            continue
        normalized = _normalize_field_entries(processed)
        if normalized:
            used_concepts.append(concept)
            per_tag_normalized.append(normalized)

    if not per_tag_normalized:
        return [], None

    merged = _merge_normalized_by_priority(per_tag_normalized)
    source_tag = "+".join(used_concepts) if len(used_concepts) > 1 else used_concepts[0]
    return merged, source_tag


# [[LAYER3-MISSING-QUARTER-IMPLIED-GAP-1]]対応: 標準的な単四半期として
# 妥当なperiod_daysの範囲。105銘柄×32フィールド全数（is_annual・
# is_implied除外後、約38,000エントリ）のperiod_days分布を確認した結果、
# 正常な単四半期は83〜98日に密集しており、唯一の異常値（RCAT
# stock_based_compensationの優先タグ内欠落による誤合算値）は183日
# だった。75〜100日を範囲とすることで、正常値（83〜98日）には
# 十分な余裕を持たせつつ、183日の異常値は明確に除外できる。
# 27〜55日の少数の短期スタブ期間（IPO直後の端数月次報告等、APGE/CEG/
# FROG/LITE/VZで確認）はこの範囲より短いが正当なデータのため、
# range外と判定された場合でも即座に破棄せず次候補を探索し、
# 全候補が範囲外だった場合は元の優先候補の値を採用する
# （データを失わないためのフォールバック、下記_merge_normalized_by_priority参照）。
_STANDARD_QUARTER_MIN_DAYS = 75
_STANDARD_QUARTER_MAX_DAYS = 100

# [[LAYER3-ANNUAL-QUARTERLY-COLLISION-1]]対応: 標準的な年次として
# 妥当なperiod_daysの範囲。105銘柄×28フィールド全数のis_annual=True
# エントリ（11,517件）のperiod_days分布を確認した結果、95%が
# 363〜365日に、99%が370日以内に収まっていた。一方295日以下にも
# 156件のクラスタ（180〜295日、300日未満）があり、これは
# [[QUARTERLY-CLASSIFY-PERIOD-NO-UPPER-BOUND-1]]（quarterly.py::
# _classify_period()のis_annual判定に上限が無く、中間的な期間長の
# エントリを誤ってis_annual=Trueに分類するバグ）の実例と判明した
# （DELL等）。300日を下限とすることで、この誤分類クラスタと明確に
# 分離できる（_classify_period()自身が持つdays>300の代替分岐と
# 一致させた値）。上限400日は53週決算年度等の変則的な年度長にも
# 余裕を持たせるための保守的な値。
_STANDARD_ANNUAL_MIN_DAYS = 300
_STANDARD_ANNUAL_MAX_DAYS = 400


def _is_plausible_standalone_quarter(e: dict) -> bool:
    """
    標準的な単四半期として妥当なperiod_daysか判定する。
    is_annual・is_implied（Q4逆算等）エントリはチェック対象外（常にTrue）。
    period_days=0（残高スナップショット等のinstant fact）もチェック対象外
    （四半期の「長さ」という概念が存在しないフィールドのため）。
    """
    if e.get("is_annual") or e.get("is_implied"):
        return True
    period_days = e.get("period_days")
    if not period_days:
        return True
    return _STANDARD_QUARTER_MIN_DAYS <= period_days <= _STANDARD_QUARTER_MAX_DAYS


def _is_plausible_annual(e: dict) -> bool:
    """
    標準的な年次として妥当なperiod_daysか判定する
    （[[LAYER3-ANNUAL-QUARTERLY-COLLISION-1]]対応）。
    period_days=0（instant fact）はチェック対象外。
    """
    period_days = e.get("period_days")
    if not period_days:
        return True
    return _STANDARD_ANNUAL_MIN_DAYS <= period_days <= _STANDARD_ANNUAL_MAX_DAYS


def _merge_normalized_by_priority(per_tag_normalized: list) -> list:
    """
    候補タグごとに正規化済みの系列（per_tag_normalizedの並び順＝
    candidatesの優先順位）を、(end_date, is_annual)の複合キー単位で
    優先順位マージする。優先タグ（リスト先頭）にその期間・区分の
    エントリがあれば採用し、なければ次候補にフォールバックする。

    [[LAYER3-ANNUAL-QUARTERLY-COLLISION-1]]対応: end_dateのみをキーに
    すると、カレンダー年決算企業の年次エントリ（is_annual=True、365日
    前後）と「Q4単独開示」エントリ（fp='FY'だが実際は91日程度、
    is_annual=False）が同一end_dateを持つ場合に競合し、一方が黙って
    破棄される問題があった（[[XBRL-TAG-KLAC-1]]と同型のパターン）。
    is_annualをキーに含めることで、年次・四半期を別スロットに分離し、
    両方とも最終出力に残す。

    [[LAYER3-MISSING-QUARTER-IMPLIED-GAP-1]]対応: is_annual=False
    スロット内で優先タグのエントリが標準的な単四半期として妥当な
    period_daysの範囲から外れている場合（優先タグ自体が特定四半期の
    報告を欠落させ、隣接四半期と合算した値を報告しているケース。RCAT
    等で確認）、そのエントリを不採用とし、次候補タグの同一キーの
    エントリを探す。is_annual=Trueスロットについても同様の妥当性判定
    （_is_plausible_annual）を適用する。全候補が範囲外だった場合は、
    データを完全に失わないよう最も優先度の高い候補の値にフォールバック
    する（27〜55日の正当な短期スタブ期間等を誤って欠落させないため）。
    """
    candidates_by_key: dict[tuple, list] = defaultdict(list)
    for normalized in per_tag_normalized:
        for e in normalized:
            candidates_by_key[(e["end"], bool(e.get("is_annual")))].append(e)

    merged: list = []
    for (end, is_annual), entries in candidates_by_key.items():
        plausible_check = _is_plausible_annual if is_annual else _is_plausible_standalone_quarter
        chosen = next((e for e in entries if plausible_check(e)), entries[0])
        merged.append(chosen)

    return sorted(merged, key=lambda x: x["end"])


def _apply_sign_normalize(entries: list, mode: str | None) -> list:
    """sign_normalizeが指定されていれば適用する（現状"abs"のみサポート）。"""
    if mode != "abs":
        return entries
    out = []
    for e in entries:
        e = dict(e)
        if e.get("val") is not None:
            e["val"] = abs(e["val"])
        out.append(e)
    return out


# ---------------------------------------------------------------------------
# YTD→単四半期差分変換（NORMALIZER-YTD-METADATA-STALE-1対応）
# ---------------------------------------------------------------------------

def _ytd_to_quarterly(fy_entries: list) -> tuple[list, list]:
    """
    YTDエントリのリストを受け取り、差分変換した単一四半期エントリを返す。

    normalizer.py::_ytd_to_quarterly() と同一のアルゴリズムだが、差分変換後の
    start/period_days を変換後の期間（前四半期end翌日〜当四半期end）に
    再計算する点が異なる（NORMALIZER-YTD-METADATA-STALE-1のメタデータ
    不整合を修正: 旧実装はvalのみYTD差分にし、start/period_daysをYTD期間
    のまま残していた）。

    戻り値: (converted, unresolved)
    """
    converted: list = []
    unresolved: list = []
    prev_ytd: float = 0
    prev_ytd_known = False
    prev_end: str | None = None

    for entry in fy_entries:
        new_entry = dict(entry)

        if not entry.get("is_ytd"):
            standalone = entry["val"]
            prev_ytd += standalone
            prev_ytd_known = True
            prev_end = entry["end"]
            new_entry["val"] = standalone
            converted.append(new_entry)
            continue

        if not prev_ytd_known:
            unresolved.append(new_entry)
            prev_ytd = entry["val"]
            prev_ytd_known = True
            prev_end = entry["end"]
            continue

        standalone = entry["val"] - prev_ytd
        if prev_ytd > 0 and entry["val"] < prev_ytd:
            new_entry["anomaly"] = True
            logger.warning(
                "YTD reversal for end=%s fp=%s val=%s prev_ytd=%s",
                entry.get("end"), entry.get("fp"), entry["val"], prev_ytd,
            )

        # --- NORMALIZER-YTD-METADATA-STALE-1対応: start/period_daysを
        #     変換後の単四半期期間に再計算する ---
        new_start = prev_end
        try:
            if new_start:
                period_days = (
                    date.fromisoformat(entry["end"]) - date.fromisoformat(new_start)
                ).days
            else:
                period_days = entry.get("period_days")
        except (ValueError, TypeError):
            period_days = entry.get("period_days")

        prev_ytd = entry["val"]
        prev_end = entry["end"]
        new_entry["is_ytd"] = False
        new_entry["val"] = standalone
        if new_start:
            new_entry["start"] = new_start
        if period_days is not None:
            new_entry["period_days"] = period_days
        converted.append(new_entry)

    return converted, unresolved


def _normalize_field_entries(raw_entries: list) -> list:
    """
    1フィールドのエントリ群をYTD→単四半期変換する
    （normalizer.py::_normalize_field()と同型のロジック）。
    """
    if not raw_entries:
        return []

    annual = [e for e in raw_entries if e.get("is_annual")]
    quarterly = [e for e in raw_entries if not e.get("is_annual")]

    sa_entries = [e for e in quarterly if not e.get("is_ytd")]
    ytd_entries = [e for e in quarterly if e.get("is_ytd")]

    if not ytd_entries:
        return sorted(annual + sa_entries, key=lambda x: x["end"])

    ytd_starts = {e["start"] for e in ytd_entries}
    chain_entries = [e for e in quarterly if e["start"] in ytd_starts]
    passthrough_entries = [e for e in quarterly if e["start"] not in ytd_starts]

    by_fy_start: dict[str, list] = defaultdict(list)
    for e in chain_entries:
        by_fy_start[e["start"]].append(e)

    converted: list = []
    unresolved: list = []
    for fy_start, fy_entries in by_fy_start.items():
        sorted_entries = sorted(fy_entries, key=lambda x: x["end"])
        c, u = _ytd_to_quarterly(sorted_entries)
        converted.extend(c)
        unresolved.extend(u)

    by_end: dict[str, list] = defaultdict(list)
    for e in passthrough_entries:
        by_end[e["end"]].append(("passthrough", e))
    for e in converted:
        by_end[e["end"]].append(("converted", e))

    all_quarterly: list = []
    for end_date, candidates in by_end.items():
        raw_sa = [e for kind, e in candidates if kind == "passthrough"]
        pool = raw_sa if raw_sa else [e for kind, e in candidates if kind == "converted"]
        all_quarterly.append(max(pool, key=lambda x: x.get("filed", "")))
    all_quarterly.extend(unresolved)

    all_quarterly.sort(key=lambda x: x["end"])
    return sorted(annual + all_quarterly, key=lambda x: x["end"])


# ---------------------------------------------------------------------------
# Q4逆算（単一集約実装、Q4-IMPLIED-CALC-TRIPLICATION-1対応の先取り）
# ---------------------------------------------------------------------------

def build_q4_implied_entries(entries: list) -> list:
    """
    年次データ（is_annual=True）から Q4 implied エントリを生成する。
    Q4 = FY年次値 - (Q1+Q2+Q3の合計)

    normalizer.py::_build_q4_implied_entries()・
    ttm_calculator.py::_build_q4_quarterly_entries()・
    financial_trend_calculator.py の3箇所独立実装（Q4-IMPLIED-CALC-
    TRIPLICATION-1）を、本モジュールでは1箇所に統一する。
    """
    today = date.today().isoformat()

    annual = [e for e in entries if e.get("is_annual") and e.get("end", "") <= today]
    quarterly = [e for e in entries if not e.get("is_annual") and not e.get("is_ytd")]

    result = []
    for ann in annual:
        fy_end = ann.get("end", "")
        fy_start = ann.get("start", "")
        fy_val = ann.get("val")
        if not fy_end or fy_val is None:
            continue

        fy_qs = [
            e for e in quarterly
            if e.get("end", "") < fy_end and e.get("start", "") >= fy_start
        ]
        top3 = sorted(fy_qs, key=lambda x: x["end"], reverse=True)[:3]
        if len(top3) < 3:
            continue

        q3_end = sorted(top3, key=lambda x: x["end"], reverse=True)[0]["end"]
        q4_val = fy_val - sum(e["val"] for e in top3)

        try:
            period_days = (date.fromisoformat(fy_end) - date.fromisoformat(q3_end)).days
        except (ValueError, TypeError):
            period_days = 90

        result.append({
            "end": fy_end,
            "start": q3_end,
            "val": q4_val,
            "fp": "Q4",
            "fy": ann.get("fy"),
            "form": "10-K",
            "filed": ann.get("filed", ""),
            "accn": ann.get("accn", ""),
            "period_days": period_days,
            "is_ytd": False,
            "is_annual": False,
            "is_implied": True,
        })

    return result


# ---------------------------------------------------------------------------
# FCF共有関数（parser.py・ttm_calculator.pyの既存計算式と同一）
# ---------------------------------------------------------------------------

def calc_fcf(ocf: float | None, capex: float | None, fl: float | None) -> float | None:
    """
    FCF = OCF - max(0, |CapEx| - |FinanceLeasePmts|)

    parser.py（1503-1505行付近）・ttm_calculator.py::_calc_fcf()と
    同一の計算式。quarterly/annual生成側とTTM集計側の両方が本関数を
    呼ぶことで、[[Q4-IMPLIED-CALC-TRIPLICATION-1]]と同種の独立実装リスク
    （FCF計算式の重複実装）を解消する。

    CapExは本モジュールのLayer2定義でsign_normalize="abs"が既に
    適用されている前提のため、ここでも念のためabs()を通す
    （二重abs()は符号に影響しない）。
    """
    if ocf is None or capex is None:
        return None
    pure_capex = abs(capex) - abs(fl or 0)
    return ocf - max(0, pure_capex)


# ---------------------------------------------------------------------------
# 銘柄単位のLayer3構築
# ---------------------------------------------------------------------------

def build_ticker_store(ticker: str) -> dict | None:
    """
    1銘柄分のLayer3データ（32フィールド）を構築する。

    戻り値の構造:
    {
      "ticker": "AAPL",
      "generated_at": "...",
      "layer2_schema_version": "1.0",
      "fields": {
        "operating_cash_flow": {
          "source_tag": "NetCashProvidedByUsedInOperatingActivities",
          "entries": [...]
        },
        ...
      }
    }
    """
    ticker = ticker.upper()
    company_facts = load_company_facts(ticker)
    if company_facts is None:
        return None

    concept_defs = load_concept_definitions()
    fields_def = concept_defs.get("fields", {})

    fields_out: dict[str, dict] = {}

    for field_name, field_def in fields_def.items():
        raw_entries, source_tag = extract_field_raw_entries(company_facts, field_def, field_name)
        if field_name in NO_CANDIDATE_MERGE_FIELDS:
            # NO_CANDIDATE_MERGE_FIELDSはextract_field_raw_entries()が
            # _process_entries()止まりの未正規化エントリを返すため、ここで正規化する。
            normalized_entries = _normalize_field_entries(raw_entries)
        else:
            # 候補マージ対象フィールドはextract_field_raw_entries()内
            # （_merge_candidate_entries）で既に正規化済み。ここで再度
            # _normalize_field_entries()を適用すると、複数タグ由来の
            # エントリが混在した状態で再度FYチェーン判定が走り、
            # クロスタグ混入バグを再発させかねないため適用しない。
            normalized_entries = raw_entries

        if field_name in Q4_IMPLIED_FIELDS:
            q4_list = build_q4_implied_entries(normalized_entries)
            if q4_list:
                existing_ends = {e["end"] for e in normalized_entries if not e.get("is_annual")}
                added = [e for e in q4_list if e["end"] not in existing_ends]
                if added:
                    normalized_entries = sorted(normalized_entries + added, key=lambda x: x["end"])

        # 未解決YTD累計の除外（is_ytd=Trueの残骸を四半期として誤計上しない）
        normalized_entries = [
            e for e in normalized_entries
            if e.get("is_annual") or not e.get("is_ytd")
        ]

        sign_normalize = field_def.get("sign_normalize")
        normalized_entries = _apply_sign_normalize(normalized_entries, sign_normalize)

        fields_out[field_name] = {
            "source_tag": source_tag,
            "category": field_def.get("category"),
            "entries": normalized_entries,
        }

    return {
        "ticker": ticker,
        "generated_at": datetime.now().isoformat(),
        "layer2_schema_version": concept_defs.get("_schema_version"),
        "fields": fields_out,
    }


def save_ticker_store(ticker: str, store: dict) -> str:
    """common/sec_data/store_v2/{TICKER}.json へ保存する（新規パス、既存ファイルは変更しない）。"""
    os.makedirs(STORE_V2_DIR, exist_ok=True)
    path = os.path.join(STORE_V2_DIR, f"{ticker.upper()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    return path


def build_and_save(ticker: str) -> str | None:
    store = build_ticker_store(ticker)
    if store is None:
        return None
    return save_ticker_store(ticker, store)


if __name__ == "__main__":
    import sys

    tickers = sys.argv[1:]
    if not tickers:
        print("使い方: python -m common.sec_data.layer3_builder TICKER [TICKER ...]")
        sys.exit(1)

    for t in tickers:
        path = build_and_save(t)
        if path:
            print(f"[{t}] 生成完了 -> {path}")
        else:
            print(f"[{t}] company_facts.json が見つからずスキップ")
