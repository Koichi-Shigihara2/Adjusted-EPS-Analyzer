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


def extract_field_raw_entries(company_facts: dict, field_def: dict) -> tuple[list, str | None]:
    """
    Layer2のcandidatesを順に試し、最初に非空のタグが見つかった時点で採用する。

    quarterly.py::_FIELD_FALLBACKS/_REVENUE_FALLBACKSのような複数タグの
    マージ・件数比較によるフォールバック切り替えは行わない（フェーズAの
    意図的な単純化。詳細はモジュールdocstring参照）。

    戻り値: (処理済みエントリのリスト, 採用したタグ名 or None)
    """
    unit = field_def.get("unit", "USD")
    for concept in field_def.get("candidates", []):
        raw_entries = _get_concept_units(company_facts, concept, unit)
        if not raw_entries:
            continue
        processed = _process_entries(raw_entries)
        if processed:
            return processed, concept
    return [], None


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
        raw_entries, source_tag = extract_field_raw_entries(company_facts, field_def)
        normalized_entries = _normalize_field_entries(raw_entries)

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
