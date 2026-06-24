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
    # 金融系: Revenueタグを銀行固有のタグに上書き
    # 【調査済み 2026-05-20】
    # SOFIは "Revenues" タグを申告していない。
    # フォールバックで RevenueFromContractWithCustomerExcludingAssessedTax(~130M, 手数料のみ)と
    # RevenuesNetOfInterestExpense(~1100M, 全社収益)が同一end/start/filedでマージされ、
    # max(filed)が不定になるため採用タグがランダムになる。
    # → revenue_concept で RevenuesNetOfInterestExpense に固定することが必須。
    "SOFI": {
        "revenue_concept": "RevenuesNetOfInterestExpense",
        "note": "フィンテック銀行。Revenuesタグなし。フォールバックが"
                "RevenueFromContract(130M=手数料のみ)とRevenuesNetOfInterest(1100M=全社収益)を"
                "混在させ採用タグが不定になる。revenue_conceptで単一タグに固定が必須。",
    },
    # BUG-REV-SPAC-1 (2026-06-12 修正)
    # IONQの2022年10-KにおいてRevenuesタグが$1,235M (SPAC関連資金調達額) を誤タグして報告している。
    # merge_all_tags=True + 同一end_date (2022-12-31) でRevenuesが先頭タグのため勝ち、
    # 正しい営業収益RevenueFromContractWithCustomer($11.1M)が採用されない。
    # → revenue_conceptで正しいタグに固定。
    "IONQ": {
        "revenue_concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
        "note": "量子コンピューティング企業。2022年10-KのRevenuesタグが"
                "SPAC調達金($1,235M)を誤タグ。正しい営業収益は"
                "RevenueFromContractWithCustomerExcludingAssessedTax($11.1M)。",
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
    "Assets":           ("Assets", "USD"),
    "SharesBasic":      ("CommonStockSharesOutstanding", "shares"),
    "SharesDiluted":    ("WeightedAverageNumberOfDilutedSharesOutstanding", "shares"),
    # R&D / 販売・マーケティング費（RICE計算用）
    "RD":               ("ResearchAndDevelopmentExpense", "USD"),
    "SM":               ("SellingAndMarketingExpense", "USD"),
    # RPO: 残存履行義務（SaaS/クラウド企業向けストック値）
    "RPO":              ("RevenueRemainingPerformanceObligation", "USD"),
    # GrossProfit逆算用（内部フィールド）
    "_COGS":            ("CostOfRevenue", "USD"),
    # BS流動項目（シガーバット検出用）
    "CurrentAssets":      ("AssetsCurrent", "USD"),
    "CurrentLiabilities": ("LiabilitiesCurrent", "USD"),
    # 自社株買い（キャッシュトラップ検出用）
    "Buyback":            ("PaymentsForRepurchaseOfCommonStock", "USD"),
}

# _COGS フォールバック概念（CostOfRevenue未申告の場合）
_COGS_FALLBACKS = (
    "CostOfGoodsAndServicesSold",
    "CostOfGoodsSold",
    "CostOfServices",
    "CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization",
)

# Revenue フォールバック概念（優先順位順・メインタグとマージして最多エントリを採用）
_REVENUE_FALLBACKS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
    "TotalRevenue",
    "RevenuesNetOfInterestExpense",  # 銀行・金融系（SOFI等）
)

# RD・SM・CapEx・SBC フォールバック概念（primaryと重複しない候補のみ）
_FIELD_FALLBACKS: dict[str, tuple[str, ...]] = {
    "NetIncome": (
        # AVGO: NetIncomeLossの四半期データが2019以前で途絶えているため ProfitLoss を使用
        # BKNG/AVAV: NetIncomeLoss自体が未申告のため以下をフォールバック
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
    ),
    "CapEx": (
        # NVDAなど: PP&E以外の生産的資産支出も含む広義CapEx
        "PaymentsToAcquireProductiveAssets",
        "PaymentsForCapitalImprovements",
    ),
    "RD": (
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    ),
    "SM": (
        "MarketingAndAdvertisingExpense",
        "MarketingExpense",
        "AdvertisingExpense",
        # SGA全体をフォールバック（SM単独タグ未申告の銘柄向け: JOBY/NVDA/CIX/ELF/KO等）
        "SellingGeneralAndAdministrativeExpense",
        "GeneralAndAdministrativeExpense",
    ),
    "Cash": (
        # RCAT等: CashAndCashEquivalentsAtCarryingValue が少ない場合
        "CashCashEquivalentsAndShortTermInvestments",
        "Cash",
    ),
    "SBC": (
        # CEG等: ShareBasedCompensation未申告の場合
        "AllocatedShareBasedCompensationExpense",
    ),
    "GrossProfit": (
        # AMZN等: GrossProfitタグがある場合（normalizer._calc_gross_profitで逆算済みの場合は不要）
        "GrossProfitLoss",
    ),
    "LTDebt": (
        # CEG等: 10-QがLongTermDebt(total)を申告せずLongTermDebtNoncurrentのみ申告する場合
        # LongTermDebt(quarterly)が0件でもLongTermDebtNoncurrentで四半期値を取得できる
        "LongTermDebtNoncurrent",
    ),
    "RPO": (
        "RemainingPerformanceObligation",
        "ContractWithCustomerLiabilityNoncurrent",
        "DeferredRevenueNoncurrent",
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

        if field_name == "Revenue":
            # 銘柄固有のRevenue概念が指定されている場合はそれを優先使用
            ticker_revenue_concept = restrictions.get("revenue_concept")
            if ticker_revenue_concept:
                override_entries = _get_field_units(company_facts, ticker_revenue_concept, unit)
                if override_entries:
                    entries = _process_entries(override_entries)
                    logger.debug("[%s] Revenue override: %s (%d entries)",
                                 ticker, ticker_revenue_concept, len(entries))
                    fields[field_name] = entries
                    continue
            # Revenueは企業によってタグが途中で変わる・複数タグ併用のため
            # メインタグ＋全フォールバックをマージして最多エントリを確保する
            # 注意: 同一accn内にYTDとstandalone両方が含まれる場合があるため
            # accnではなく(end, start, val)の組み合わせで重複排除する
            all_entries = list(entries)
            seen_key = {(e.get("end"), e.get("start"), e.get("val")) for e in entries}
            for fallback_concept in _REVENUE_FALLBACKS:
                fb = _get_field_units(company_facts, fallback_concept, unit)
                for e in fb:
                    key = (e.get("end"), e.get("start"), e.get("val"))
                    if key not in seen_key:
                        all_entries.append(e)
                        seen_key.add(key)
            entries = all_entries
            if entries:
                logger.debug("[%s] Revenue merged: %d entries", ticker, len(entries))

        if field_name == "_COGS" and not entries:
            # CostOfRevenue未申告の場合、代替COGSタグを試みる
            for fallback_concept in _COGS_FALLBACKS:
                fb = _get_field_units(company_facts, fallback_concept, unit)
                if fb:
                    entries = fb
                    logger.debug("[%s] _COGS fallback: %s", ticker, fallback_concept)
                    break

        processed = _process_entries(entries)

        # 汎用フォールバック:
        # ① タグ欠如またはエントリなし → 全フィールド対象
        # ② Q件数が少ない（4件未満）場合もフォールバックを試みてより多い方を採用
        #    ※ SMはメインタグで少数取れていてもSGA等に乗り換えると意味が変わるため除外
        _FALLBACK_MIN = 4
        # NetIncome: quarterly数が少ない場合もフォールバックを試みる
        #   AVGO等: NetIncomeLossの四半期データが5年窓外で q_count=0 になる場合に
        #   ProfitLossへのフォールバックが必要（annualはあるため not processed=False）
        _FALLBACK_MIN_FIELDS = {"Cash", "SBC", "CapEx", "GrossProfit", "NetIncome", "LTDebt"}
        if field_name in _FIELD_FALLBACKS:
            q_count = sum(1 for e in processed if not e.get("is_annual"))
            use_min = field_name in _FALLBACK_MIN_FIELDS and q_count < _FALLBACK_MIN
            if not processed or use_min:
                for fallback_concept in _FIELD_FALLBACKS[field_name]:
                    fb_entries = _get_field_units(company_facts, fallback_concept, unit)
                    if fb_entries:
                        fb_processed = _process_entries(fb_entries)
                        fb_q_count = sum(1 for e in fb_processed if not e.get("is_annual"))
                        if fb_q_count > q_count:
                            processed = fb_processed
                            logger.debug("[%s] %s fallback(better): %s (%d Q entries)",
                                         ticker, field_name, fallback_concept, fb_q_count)
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


# ---------------------------------------------------------------------------
# Revenue品質チェック
# ---------------------------------------------------------------------------

def check_revenue_quality(ticker: str, normalized: dict) -> dict:
    """
    normalized JSONのRevenueフィールドに対して品質チェックを行う。

    チェック項目:
      1. 四半期件数が少ない（8件未満）
      2. 最新Q 前Q比の異常値
         - seasonal_q1_jump=True の銘柄はQ1（3月末）の前Q比チェックをスキップ
         - それ以外: |QoQ| > 60% → ISSUE, > 35% → WARN
      3. 最新yoyトレンドの急変（±20pt超）
      4. 四半期合計とFY年次の整合性（乖離 > 5% → ISSUE）
      5. 金融・保険系フラグ（seasonal_q1_jump or revenue_concept上書きあり）
      6. Revenue負値

    戻り値:
    {
      "ticker": str,
      "status": "OK" | "WARN" | "ISSUE",
      "issues": [str, ...],   # 重大問題
      "warnings": [str, ...], # 注意事項
      "latest_rev_yoy": float | None,
      "latest_q_end": str | None,
    }
    """
    ticker = ticker.upper()
    restrictions = TICKER_RESTRICTIONS.get(ticker, {})
    seasonal_q1 = restrictions.get("seasonal_q1_jump", False)

    entries = normalized.get("fields", {}).get("Revenue", [])
    q_only = sorted(
        [(e["end"], e["val"]) for e in entries if not e.get("is_annual")],
        key=lambda x: x[0],
    )
    a_only = sorted(
        [(e["end"], e["val"]) for e in entries if e.get("is_annual")],
        key=lambda x: x[0],
    )

    issues: list[str] = []
    warnings: list[str] = []
    latest_yoy: float | None = None
    latest_q_end: str | None = q_only[-1][0] if q_only else None

    if not q_only:
        issues.append("四半期Revenueエントリなし")
        return _build_result(ticker, issues, warnings, latest_yoy, latest_q_end)

    # --- チェック1: 件数 ---
    if len(q_only) < 8:
        warnings.append(f"四半期データが少ない ({len(q_only)}件 < 8件)")

    # --- チェック2: 最新Q 前Q比 ---
    if len(q_only) >= 2:
        latest_end, latest_val = q_only[-1]
        prev_end, prev_val = q_only[-2]
        qoq = (latest_val - prev_val) / abs(prev_val) * 100
        is_q1 = latest_end[5:7] == "03"  # 3月末 = Q1

        if seasonal_q1 and is_q1:
            # Q1季節性銘柄はQ1ジャンプをスキップし、過去Q1比で異常検出
            q1_entries = [(e, v) for e, v in q_only if e[5:7] == "03"]
            if len(q1_entries) >= 3:
                past_q1_qoqs = []
                for i in range(1, len(q1_entries) - 1):
                    # 直前Q4を探して比較
                    q1_end = q1_entries[i][0]
                    q4_candidates = [(e, v) for e, v in q_only
                                     if e < q1_end and e[5:7] == "12"]
                    if q4_candidates:
                        q4_end, q4_val = q4_candidates[-1]
                        past_q1_qoqs.append(
                            (q1_entries[i][1] - q4_val) / abs(q4_val) * 100
                        )
                if past_q1_qoqs:
                    avg_q1_jump = sum(past_q1_qoqs) / len(past_q1_qoqs)
                    # Q4を探して現在の実績と比較
                    q4_for_latest = [(e, v) for e, v in q_only
                                     if e < latest_end and e[5:7] == "12"]
                    if q4_for_latest:
                        _, q4_val = q4_for_latest[-1]
                        latest_q1_jump = (latest_val - q4_val) / abs(q4_val) * 100
                        diff = latest_q1_jump - avg_q1_jump
                        if diff > 30:
                            warnings.append(
                                f"Q1季節性ジャンプが過去平均を大幅超過: "
                                f"今回{latest_q1_jump:.1f}% vs 過去平均{avg_q1_jump:.1f}% "
                                f"(+{diff:.1f}pt)"
                            )
            # Q1スキップのメモをWARNに残す
            warnings.append(
                f"seasonal_q1_jump: 前Q比{qoq:+.1f}%はQ1季節性として評価スキップ"
            )
        else:
            if abs(qoq) > 60:
                issues.append(
                    f"最新Q 前Q比異常: {qoq:+.1f}% ({prev_end}→{latest_end})"
                )
            elif abs(qoq) > 35:
                warnings.append(
                    f"最新Q 前Q比大きめ: {qoq:+.1f}% ({prev_end}→{latest_end}) 季節性か要確認"
                )

    # --- チェック3: yoyトレンド急変 ---
    if len(q_only) >= 5:
        yoys = []
        for i in range(4, len(q_only)):
            e, v = q_only[i]
            pe, pv = q_only[i - 4]
            yoys.append((e, (v - pv) / abs(pv) * 100))
        latest_yoy = yoys[-1][1]
        if len(yoys) >= 3:
            recent = [y for _, y in yoys[-3:]]
            avg_prev = sum(recent[:-1]) / len(recent[:-1])
            jump = recent[-1] - avg_prev
            if jump > 20:
                warnings.append(
                    f"最新yoy急加速: {avg_prev:.1f}%→{recent[-1]:.1f}% (+{jump:.1f}pt)"
                )
            elif jump < -20:
                warnings.append(
                    f"最新yoy急減速: {avg_prev:.1f}%→{recent[-1]:.1f}% ({jump:.1f}pt)"
                )

    # --- チェック4: 四半期合計 vs FY年次 整合性 ---
    for a_end, a_val in a_only[-3:]:
        year = a_end[:4]
        q_in_year = [v for e, v in q_only if e[:4] == year]
        if q_in_year:
            q_total = sum(q_in_year)
            gap_pct = abs(q_total - a_val) / abs(a_val) * 100
            if gap_pct > 5:
                issues.append(
                    f"FY{year} 年次vs四半期合計 乖離{gap_pct:.1f}%: "
                    f"annual={a_val/1e6:.0f}M, Q合計={q_total/1e6:.0f}M"
                )

    # --- チェック5: 金融・保険系フラグ ---
    if restrictions.get("revenue_concept") or restrictions.get("seasonal_q1_jump"):
        kind = "銀行/フィンテック" if restrictions.get("revenue_concept") else "保険/季節性"
        warnings.append(
            f"特殊銘柄({kind}): TICKER_RESTRICTIONSで管理済み"
        )

    # --- チェック6: Revenue負値 ---
    neg = [(e, v) for e, v in q_only if v < 0]
    if neg:
        issues.append(
            f"Revenue負値: {[(e, round(v/1e6, 1)) for e, v in neg]}"
        )

    return _build_result(ticker, issues, warnings, latest_yoy, latest_q_end)


def _build_result(
    ticker: str,
    issues: list[str],
    warnings: list[str],
    latest_yoy: float | None,
    latest_q_end: str | None,
) -> dict:
    status = "ISSUE" if issues else ("WARN" if warnings else "OK")
    result = {
        "ticker": ticker,
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "latest_rev_yoy": round(latest_yoy, 2) if latest_yoy is not None else None,
        "latest_q_end": latest_q_end,
    }
    logger.info(
        "[%s] revenue quality: %s  issues=%d warnings=%d  yoy=%s",
        ticker,
        status,
        len(issues),
        len(warnings),
        f"{latest_yoy:.1f}%" if latest_yoy is not None else "N/A",
    )
    return result
