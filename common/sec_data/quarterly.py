"""
common/sec_data/quarterly.py
責務: company_facts.json から四半期Raw Tableを生成する
出力: raw/{ticker}_quarterly_raw.json
"""

import json
import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, "raw")

# 銘柄別制限（ハードコード）
TICKER_RESTRICTIONS: dict[str, dict] = {
    "MSFT":  {"exclude": ["DA"]},
    "APP":   {"exclude": ["CapEx"]},
    "GOOGL": {
        "approximate": ["DA"],
        "note_discontinuous": ["LTDebt"],
    },
}

# 会計年度タイプ（将来対応用）
FISCAL_YEAR_TYPE: dict[str, str] = {
    # "AMZN": "53week",  # 53週会計年度（AMZNオンボード時に有効化）
}

# XBRL概念マッピング（field_name → (concept, unit)）
FIELD_CONCEPTS: dict[str, tuple[str, str]] = {
    "OCF":              ("NetCashProvidedByUsedInOperatingActivities", "USD"),
    "ICF":              ("NetCashProvidedByUsedInInvestingActivities", "USD"),
    "CFF":              ("NetCashProvidedByUsedInFinancingActivities", "USD"),
    "CapEx":            ("PaymentsToAcquirePropertyPlantAndEquipment", "USD"),
    "FinanceLeasePmts": ("FinanceLeasePrincipalPayments", "USD"),
    "SBC":              ("ShareBasedCompensation", "USD"),
    "DA":               ("DepreciationDepletionAndAmortization", "USD"),
    "Revenue":          ("Revenues", "USD"),
    "GrossProfit":      ("GrossProfit", "USD"),
    "OperatingIncome":  ("OperatingIncomeLoss", "USD"),
    "NetIncome":        ("NetIncomeLoss", "USD"),
    "Cash":             ("CashAndCashEquivalentsAtCarryingValue", "USD"),
    "STDebt":           ("ShortTermBorrowings", "USD"),
    "LTDebt":           ("LongTermDebt", "USD"),
    "DeferredRevenue":  ("DeferredRevenue", "USD"),
    "Equity":           ("StockholdersEquity", "USD"),
    "SharesBasic":      ("CommonStockSharesOutstanding", "shares"),
    "SharesDiluted":    ("WeightedAverageNumberOfDilutedSharesOutstanding", "shares"),
    # R&D / 販売・マーケティング費（RICE計算用）
    "RD":               ("ResearchAndDevelopmentExpense", "USD"),
    "SM":               ("SellingAndMarketingExpense", "USD"),
    # GrossProfit逆算用（内部フィールド）
    "_COGS":            ("CostOfRevenue", "USD"),
}

# Revenue フォールバック概念
_REVENUE_FALLBACKS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
    "TotalRevenue",
)

# RD・SM・CapEx フォールバック概念（primaryと重複しない候補のみ）
_FIELD_FALLBACKS: dict[str, tuple[str, ...]] = {
    "CapEx": (
        # NVDAなど: PP&E以外の生産的資産支出も含む広義CapEx
        "PaymentsToAcquireProductiveAssets",
    ),
    "RD": (
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    ),
    "SM": (
        "MarketingAndAdvertisingExpense",
        "MarketingExpense",
        "AdvertisingExpense",
    ),
}

# 取得期間
_QUARTERLY_YEARS = 5
_ANNUAL_YEARS = 6


def build_raw_table(ticker: str, company_facts: dict) -> dict:
    """
    company_facts から全フィールドの四半期Raw Tableを抽出。

    戻り値構造:
    {
      "ticker": "NVDA",
      "generated_at": "2026-05-07T...",
      "fields": {
        "OCF": [
          {
            "end": "2024-10-27",
            "start": "2024-07-29",
            "val": 7000000000,
            "accn": "0001045810-24-...",
            "fp": "Q3",
            "fy": 2025,
            "form": "10-Q",
            "filed": "2024-11-20",
            "period_days": 90,
            "is_ytd": False,
            "is_annual": False,
          },
          ...
        ],
        "Revenue": [...],
        ...
      }
    }
    """
    ticker = ticker.upper()
    restrictions = TICKER_RESTRICTIONS.get(ticker, {})
    excluded = set(restrictions.get("exclude", []))

    fields: dict[str, list] = {}

    for field_name, (concept, unit) in FIELD_CONCEPTS.items():
        if field_name in excluded:
            fields[field_name] = []
            continue

        entries = _get_field_units(company_facts, concept, unit)

        if field_name == "Revenue" and not entries:
            for fallback_concept in _REVENUE_FALLBACKS:
                entries = _get_field_units(company_facts, fallback_concept, unit)
                if entries:
                    logger.debug("[%s] Revenue fallback: %s", ticker, fallback_concept)
                    break

        processed = _process_entries(entries)

        # Revenue追加フォールバック: 生データはあるが直近カットオフ後に空になった場合
        # （例: METAは2018年以前はRevenues、以降はRevenueFromContractWith...に切り替え）
        if field_name == "Revenue" and not processed:
            for fallback_concept in _REVENUE_FALLBACKS:
                fb_entries = _get_field_units(company_facts, fallback_concept, unit)
                if fb_entries:
                    fb_processed = _process_entries(fb_entries)
                    if fb_processed:
                        processed = fb_processed
                        logger.debug("[%s] Revenue post-cutoff fallback: %s", ticker, fallback_concept)
                        break

        # 汎用フォールバック: タグ欠如 または 有効期間内エントリなしの場合に適用
        if not processed and field_name in _FIELD_FALLBACKS:
            for fallback_concept in _FIELD_FALLBACKS[field_name]:
                fb_entries = _get_field_units(company_facts, fallback_concept, unit)
                if fb_entries:
                    fb_processed = _process_entries(fb_entries)
                    if fb_processed:
                        processed = fb_processed
                        logger.debug("[%s] %s fallback: %s", ticker, field_name, fallback_concept)
                        break

        fields[field_name] = processed

    logger.info("[%s] raw table built: %d fields", ticker, len(fields))
    return {
        "ticker": ticker,
        "generated_at": datetime.now().isoformat(),
        "fields": fields,
    }


def _get_field_units(company_facts: dict, concept: str, unit: str = "USD") -> list:
    """company_facts.facts.us-gaap.{concept}.units.{unit} を安全に取得"""
    try:
        return company_facts["facts"]["us-gaap"][concept]["units"][unit]
    except (KeyError, TypeError):
        return []


def _select_best_filing(filings: list, end_date: str) -> dict | None:
    """同一期間に複数filingがある場合、最新filed優先で選択"""
    candidates = [f for f in filings if f.get("end") == end_date]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x.get("filed", ""))


def _classify_period(start: str, end: str, fp: str) -> dict:
    """
    期間を分類する。

    戻り値: {"period_days": int, "is_ytd": bool, "is_annual": bool}
    """
    try:
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        days = (e - s).days
    except (ValueError, TypeError):
        days = 0

    is_annual = fp == "FY" or days > 300
    # 131-300日 かつ 10-Q → YTD
    is_ytd = (not is_annual) and (days > 130)

    return {
        "period_days": days,
        "is_ytd": is_ytd,
        "is_annual": is_annual,
    }


def _process_entries(raw_entries: list) -> list:
    """
    生エントリをフィルタ・分類・重複排除・ソートして返す。

    同一end_date内: SA（期間短い）優先 > YTD、最新filed優先。
    四半期: 直近5年, 年次: 直近6年。
    """
    today = date.today()
    cutoff_q = (today - timedelta(days=_QUARTERLY_YEARS * 365)).isoformat()
    cutoff_a = (today - timedelta(days=_ANNUAL_YEARS * 365)).isoformat()

    # end_date → 候補リスト（quarterly / annual 別）
    quarterly_by_end: dict[str, list] = defaultdict(list)
    annual_by_end: dict[str, list] = defaultdict(list)

    for entry in raw_entries:
        form = entry.get("form", "")
        if form not in ("10-Q", "10-Q/A", "10-K", "10-K/A"):
            continue

        end = entry.get("end", "")
        start = entry.get("start", "")
        fp = entry.get("fp", "")
        val = entry.get("val")

        if val is None or not end:
            continue

        period_info = _classify_period(start, end, fp)

        enriched = {
            "end": end,
            "start": start,
            "val": val,
            "accn": entry.get("accn", ""),
            "fp": fp,
            "fy": entry.get("fy"),
            "form": form,
            "filed": entry.get("filed", ""),
            "period_days": period_info["period_days"],
            "is_ytd": period_info["is_ytd"],
            "is_annual": period_info["is_annual"],
        }

        if period_info["is_annual"]:
            if end >= cutoff_a:
                annual_by_end[end].append(enriched)
        else:
            if end >= cutoff_q:
                quarterly_by_end[end].append(enriched)

    result: list = []

    # 四半期: SA優先、最新filed
    for end_date, candidates in quarterly_by_end.items():
        sa = [c for c in candidates if not c["is_ytd"]]
        ytd = [c for c in candidates if c["is_ytd"]]
        pool = sa if sa else ytd
        best = max(pool, key=lambda x: x["filed"])
        result.append(best)

    # 年次: 最新filed
    for end_date, candidates in annual_by_end.items():
        best = max(candidates, key=lambda x: x["filed"])
        result.append(best)

    result.sort(key=lambda x: x["end"])
    return result


def save_raw_table(ticker: str, raw: dict) -> str:
    """raw tableをJSONファイルに保存し、パスを返す"""
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, f"{ticker.upper()}_quarterly_raw.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    logger.info("[%s] raw table saved → %s", ticker, path)
    return path
