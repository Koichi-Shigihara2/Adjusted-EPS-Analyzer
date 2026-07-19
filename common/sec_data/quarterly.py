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

from .tag_definitions import TAG_CANDIDATES
from .contracts import validate_fields
from .utils import quarters_in_trailing_window

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
    # SOFI-DATA-1（2026-06-24発見・2026-07-13パイプライン恒久化）:
    # 銀行免許取得後（2022年以降）LongTermDebt/LongTermDebtNoncurrentタグの
    # 申告を停止し、短期+長期合算タグDebtLongtermAndShorttermCombinedAmountに
    # 移行。standard fallbackへの追加はAVGO/VZ等の無関係な既存LTDebtデータにも
    # 波及することを検証で確認したため、SOFI限定のticker_restrictionsとした。
    # FY52WEEK-BS-STI-OVERRIDE-DESIGN-1（2026-07-19）: short_term_investments
    # もBS本体「Investment securities」全体を表すOtherInvestmentsタグに固定。
    # 当初想定していたAvailableForSaleSecuritiesDebtSecuritiesはAFS分類分の
    # サブセット（FY2025時点で95.3%のみ）しか捕捉できず、残差はNote 15
    # （公正価値ヒエラルキー）に含まれる非AFS分類の資産担保証券・残余持分
    # （証券化VIE由来）であることを一次情報で確認済み。OtherInvestmentsは
    # BS「Investment securities」合計と全期間で完全一致する。
    "SOFI": {
        "revenue_concept": "RevenuesNetOfInterestExpense",
        "ltdebt_concept": "DebtLongtermAndShorttermCombinedAmount",
        "sti_concept": "OtherInvestments",
        "note": "フィンテック銀行。Revenuesタグなし。フォールバックが"
                "RevenueFromContract(130M=手数料のみ)とRevenuesNetOfInterest(1100M=全社収益)を"
                "混在させ採用タグが不定になる。revenue_conceptで単一タグに固定が必須。"
                "LTDebtも2022年以降LongTermDebt系タグの申告を停止しており"
                "ltdebt_conceptで単一タグに固定が必須。short_term_investmentsは"
                "非分類BS（流動/非流動を区分しない銀行持株会社）のため"
                "sti_conceptで単一タグ（OtherInvestments、BS合計と完全一致）に固定。",
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
    # FY52WEEK-BS-STI-OVERRIDE-DESIGN-1（2026-07-19）:
    # short_term_investmentsのXBRL_MAPPING標準候補群（Current接尾辞系タグ）は
    # KLAC/TER/Vいずれも数年前に申告停止済みで機能しない。かつ正しいタグが
    # 汎用的な名称（他銘柄でも別の意味で広く使われる）のためグローバル候補
    # リストへは追加せず、ticker限定のsti_conceptで固定する。
    "KLAC": {
        "sti_concept": "AvailableForSaleSecuritiesDebtSecurities",
        "note": "BACKLOG当初想定のAvailableForSaleSecuritiesDebtSecuritiesCurrent"
                "は2021-03-31を最後に申告停止済みの死んだタグ。'Current'接尾辞なしの"
                "AvailableForSaleSecuritiesDebtSecuritiesが現在も継続申告されており、"
                "BS「Marketable securities」の99.0%（FY2025）に一致（残差は"
                "EquitySecuritiesFvNiCost約$22.9Mの株式性有価証券、本タグの対象外）。",
    },
    "TER": {
        "sti_concept": "AvailableForSaleSecuritiesDebtMaturitiesWithinOneYearFairValue",
        "note": "標準候補群（AvailableForSaleSecuritiesCurrent等）は2021年以降"
                "申告停止済み。満期別内訳の「1年以内」タグがBS「Marketable "
                "securities」（FY2025: $28,247K）と完全一致（誤差ゼロ）。",
    },
    "V": {
        "sti_concept": "Investments",
        "note": "標準候補群は2020年以降申告停止済み。'Investments'タグ（'Current'"
                "接尾辞なしの汎用名）がBS流動資産側「Investment securities」"
                "（FY2025: $1,833,000,000）と完全一致。他9銘柄（ADSK/BSY/CEG/"
                "CRWV/DELL/LRCX/LYFT/MO/ONDS）も同タグを別の意味で申告している"
                "ため、V限定オーバーライドとして厳格運用し、グローバル候補"
                "リストには絶対に追加しないこと。",
    },
}

# 会計年度タイプ（将来対応用）
FISCAL_YEAR_TYPE: dict[str, str] = {
    # "AMZN": "53week",  # 53週会計年度（AMZNオンボード時に有効化）
}

# XBRL概念マッピング（field_name → (concept, unit)）
# CapEx・FinanceLeasePmts・SBC・GrossProfit・NetIncome・Cash・RD・Buyback・OCFの
# primaryタグはtag_definitions.pyのTAG_CANDIDATES（各タプルの先頭）から取得する
# （LLY-CAPEX-STALE-1 Phase 2a・quarterly.py/parser.pyのタグリスト統合）。
FIELD_CONCEPTS: dict[str, tuple[str, str]] = {
    "OCF":              (TAG_CANDIDATES["OPERATING_CASH_FLOW"][0], "USD"),
    "ICF":              ("NetCashProvidedByUsedInInvestingActivities", "USD"),
    "CFF":              ("NetCashProvidedByUsedInFinancingActivities", "USD"),
    "CapEx":            (TAG_CANDIDATES["CAPITAL_EXPENDITURE"][0], "USD"),
    "FinanceLeasePmts": (TAG_CANDIDATES["FINANCE_LEASE_PAYMENTS"][0], "USD"),
    "SBC":              (TAG_CANDIDATES["STOCK_BASED_COMPENSATION"][0], "USD"),
    "DA":               ("DepreciationDepletionAndAmortization", "USD"),
    "Revenue":          ("Revenues", "USD"),
    "GrossProfit":      (TAG_CANDIDATES["GROSS_PROFIT"][0], "USD"),
    "OperatingIncome":  ("OperatingIncomeLoss", "USD"),
    "NetIncome":        (TAG_CANDIDATES["NET_INCOME"][0], "USD"),
    "Cash":             (TAG_CANDIDATES["CASH_AND_EQUIVALENTS"][0], "USD"),
    "STDebt":           ("ShortTermBorrowings", "USD"),
    "LTDebt":           ("LongTermDebt", "USD"),
    "DeferredRevenue":  ("DeferredRevenue", "USD"),
    "Equity":           ("StockholdersEquity", "USD"),
    "Assets":           ("Assets", "USD"),
    "SharesBasic":      ("CommonStockSharesOutstanding", "shares"),
    "SharesDiluted":    ("WeightedAverageNumberOfDilutedSharesOutstanding", "shares"),
    # R&D / 販売・マーケティング費（RICE計算用）
    "RD":               (TAG_CANDIDATES["RESEARCH_AND_DEVELOPMENT"][0], "USD"),
    "SM":               ("SellingAndMarketingExpense", "USD"),
    # RPO: 残存履行義務（SaaS/クラウド企業向けストック値）
    "RPO":              ("RevenueRemainingPerformanceObligation", "USD"),
    # GrossProfit逆算用（内部フィールド）
    "_COGS":            ("CostOfRevenue", "USD"),
    # BS流動項目（シガーバット検出用）
    "CurrentAssets":      ("AssetsCurrent", "USD"),
    "CurrentLiabilities": ("LiabilitiesCurrent", "USD"),
    # 自社株買い（キャッシュトラップ検出用）
    "Buyback":            (TAG_CANDIDATES["BUYBACK"][0], "USD"),
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
# CapEx・SBC・GrossProfit・NetIncome・Cash・RDはtag_definitions.pyのTAG_CANDIDATES
# （primary除く残り）から取得する（LLY-CAPEX-STALE-1 Phase 2a）。
# LTDebt・SM・RPOはparser.py側と優先順位・候補集合が構造的に異なるため
# 統合対象外（tag_definitions.pyのdocstring・BACKLOG [TAG-DEFS-UNIFY-1] 参照）。
_FIELD_FALLBACKS: dict[str, tuple[str, ...]] = {
    # AVGO: NetIncomeLossの四半期データが2019以前で途絶えているため ProfitLoss を使用
    # BKNG/AVAV: NetIncomeLoss自体が未申告のため以下をフォールバック
    "NetIncome": TAG_CANDIDATES["NET_INCOME"][1:],
    "CapEx": TAG_CANDIDATES["CAPITAL_EXPENDITURE"][1:],
    "RD": TAG_CANDIDATES["RESEARCH_AND_DEVELOPMENT"][1:],
    "SM": (
        "MarketingAndAdvertisingExpense",
        "MarketingExpense",
        "AdvertisingExpense",
        # SGA全体をフォールバック（SM単独タグ未申告の銘柄向け: JOBY/NVDA/CIX/ELF/KO等）
        "SellingGeneralAndAdministrativeExpense",
        "GeneralAndAdministrativeExpense",
    ),
    # RCAT等: CashAndCashEquivalentsAtCarryingValue が少ない場合
    "Cash": TAG_CANDIDATES["CASH_AND_EQUIVALENTS"][1:],
    # CEG等: ShareBasedCompensation未申告の場合
    "SBC": TAG_CANDIDATES["STOCK_BASED_COMPENSATION"][1:],
    # AMZN等: GrossProfitタグがある場合（normalizer._calc_gross_profitで逆算済みの場合は不要）
    "GrossProfit": TAG_CANDIDATES["GROSS_PROFIT"][1:],
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

# FinanceLeasePmts・Buyback・OCFはprimaryのみ（fallbackなし）だったが、
# parser.py側にFinanceLeasePmtsの追加候補があったため統合する（Phase 2a）。
_FIELD_FALLBACKS["FinanceLeasePmts"] = TAG_CANDIDATES["FINANCE_LEASE_PAYMENTS"][1:]

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
                    # 規約③（出所メタデータ）: ticker_restrictionsによる明示オーバーライドは
                    # 「なぜこの値か」が自明でないため_provenanceに記録する
                    entries = [
                        {**e, "_provenance": {"source_tag": ticker_revenue_concept}}
                        for e in entries
                    ]
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

        if field_name == "LTDebt":
            # 銘柄固有のLTDebt概念が指定されている場合はそれを優先使用
            # SOFI-DATA-1: 銀行免許取得後（2022年以降）LongTermDebt/
            # LongTermDebtNoncurrentの申告自体を停止し、短期+長期合算タグに
            # 移行したケース向け。standard候補群への一般フォールバック追加は
            # AVGO/VZ等の無関係な既存データにも波及するため見送り、
            # ticker_restrictionsによる明示的な銘柄限定オーバーライドとする。
            ticker_ltdebt_concept = restrictions.get("ltdebt_concept")
            if ticker_ltdebt_concept:
                override_entries = _get_field_units(company_facts, ticker_ltdebt_concept, unit)
                if override_entries:
                    entries = _process_entries(override_entries)
                    # 規約③（出所メタデータ）: SOFI-DATA-1のような明示オーバーライドは
                    # 「なぜこの値か」が自明でないため_provenanceに記録する
                    entries = [
                        {**e, "_provenance": {"source_tag": ticker_ltdebt_concept}}
                        for e in entries
                    ]
                    logger.debug("[%s] LTDebt override: %s (%d entries)",
                                 ticker, ticker_ltdebt_concept, len(entries))
                    fields[field_name] = entries
                    continue

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
                processed, _source_tag = _select_best_candidate(
                    company_facts, unit, concept, processed,
                    _FIELD_FALLBACKS[field_name], _FALLBACK_MIN,
                )
                if _source_tag:
                    # 規約③（出所メタデータ）: フォールバック候補が採用された場合のみ
                    # 記録する（primary採用時は想定通りのためnoise回避で付与しない）
                    processed = [
                        {**e, "_provenance": {"source_tag": _source_tag}}
                        for e in processed
                    ]
                logger.debug("[%s] %s fallback evaluated (best candidate selected)", ticker, field_name)

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


def _select_best_candidate(
    company_facts: dict,
    unit: str,
    primary_concept: str,
    primary_processed: list,
    fallback_concepts: tuple[str, ...],
    min_count: int,
) -> tuple[list, str | None]:
    """primary概念＋フォールバック候補群の中から採用する候補を選ぶ。

    LLY-CAPEX-STALE-1 Phase 2a: 「候補タグ群の中で最初に条件（最小件数）を
    満たしたものを採用して打ち切る」方式は、タグがサイレントに切り替わった
    銘柄（旧タグは件数を満たすが更新が止まっている）を検知できない
    （LLYのCapEx: 旧タグPaymentsToAcquireProductiveAssetsは4四半期分あるが
    2022-09-30で申告停止しており、新タグへの切替後データを一切拾えなかった）。

    最小件数(min_count)を満たす候補が複数ある場合、「最初に見つかったもの」
    ではなく「四半期の最新end日が最も新しいもの」を採用する。最小件数を
    満たす候補が皆無の場合のみ、従来どおり最多件数の候補を採用する。
    同着（end日・件数が同一）の場合は優先順位（primary→fallback_concepts順）を維持する。

    戻り値: (選定されたエントリリスト, 採用概念名)。採用概念名はprimary_conceptが
    選ばれた場合はNone（想定通りの経路のためprovenance記録不要）、フォールバック
    概念が選ばれた場合はその概念名（QUALITY-GATES-EPIC-1 Phase 3a: 呼び出し元で
    EntryProvenance.source_tagとして記録するため）。
    """
    def _stats(processed: list) -> tuple[int, str]:
        q_count = sum(1 for e in processed if not e.get("is_annual"))
        latest_end = max((e["end"] for e in processed), default="")
        return q_count, latest_end

    candidates: list[tuple[list, int, str, str]] = []
    q0, end0 = _stats(primary_processed)
    candidates.append((primary_processed, q0, end0, primary_concept))
    for concept in fallback_concepts:
        fb_entries = _get_field_units(company_facts, concept, unit)
        if not fb_entries:
            continue
        fb_processed = _process_entries(fb_entries)
        q, end = _stats(fb_processed)
        candidates.append((fb_processed, q, end, concept))

    qualified = [c for c in candidates if c[1] >= min_count]
    if qualified:
        # 最小件数を満たす候補の中から最新end日優先（同着は優先順位＝リスト順で先勝ち）
        best = max(qualified, key=lambda c: (c[2], -candidates.index(c)))
    else:
        # 最小件数を満たす候補が皆無 → 従来どおり最多件数優先（同点はend日→優先順位）
        best = max(candidates, key=lambda c: (c[1], c[2], -candidates.index(c)))
    winning_concept = best[3]
    source_tag = winning_concept if winning_concept != primary_concept else None
    return best[0], source_tag


def _select_best_filing(filings: list, end_date: str) -> dict | None:
    """同一期間に複数filingがある場合、最新filed優先で選択"""
    candidates = [f for f in filings if f.get("end") == end_date]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x.get("filed", ""))


def _classify_period(start: str, end: str, fp: str, form: str = "") -> dict:
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

    # is_annualはform=10-K/10-K-A限定（PARSER-ENTG-COMPYEAR-1の教訓）:
    # 10-Qには比較用に365日近いdurationのcontextRefが混入することがあり、
    # form制限なしだとそれが「最新filed優先」ロジックで正規の10-K年次値を
    # 上書きしてしまう（ENTG FY2022でQ4合成値が$0になる不具合が発生した）
    #
    # fp=='FY'のみでの判定は不十分（XBRL-TAG-KLAC-1の教訓）:
    # SEC XBRL APIのfpは「filing自体の期間種別」を指すため、10-K内に
    # 埋め込まれた四半期duration（例: period_days=91の比較用開示）にも
    # 一律fp='FY'が付与される。fp=='FY'単独で年次判定すると、KLACの
    # FY2021 10-K内の四半期GrossProfit開示（period_days=89〜91）が
    # 誤って年次データとして扱われ、その後の年度に本来の年次値が
    # 一度も上書きされず4四半期分の古いデータが残存し続けた。
    # fp=='FY'採用時もdays>130（4半期の最短妥当日数）を必須とする。
    is_annual = form in ("10-K", "10-K/A") and ((fp == "FY" and days > 130) or days > 300)
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

    四半期: (start, end) の期間単位でグルーピングし、同一期間内は最新filed優先。
    ※ end日付だけでグルーピングすると、同一end・異なるstart（例: Q3単独 vs
      Q1-Q3累計）の別期間エントリを誤って「重複」扱いし、一方（主にYTD）を
      完全に破棄してしまう（BUG-CON-YTD-1）。YTDは欠落四半期の逆算に使える
      有用な情報のため、start違いは別期間として保持する。
    年次: 直近6年、四半期: 直近5年。
    """
    today = date.today()
    cutoff_q = (today - timedelta(days=_QUARTERLY_YEARS * 365)).isoformat()
    cutoff_a = (today - timedelta(days=_ANNUAL_YEARS * 365)).isoformat()

    # (start, end) → 候補リスト（quarterly）、end → 候補リスト（annual）
    quarterly_by_period: dict[tuple, list] = defaultdict(list)
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

        period_info = _classify_period(start, end, fp, form)

        # 10-Q/10-Q-A由来でduration>300日のエントリは比較用contextRefの混入
        # （PARSER-ENTG-COMPYEAR-1）とみなし、YTD四半期扱いにもせず除外する
        # （実際の10-Q YTDは最大9ヶ月≒270日程度のため、300日超は正規の
        #   四半期・YTD概念に該当しない）
        if form in ("10-Q", "10-Q/A") and period_info["period_days"] > 300:
            continue

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
                quarterly_by_period[(start, end)].append(enriched)

    result: list = []

    # 四半期: 同一(start, end)内は最新filed優先。異なるstartは別期間として全保持。
    for period, candidates in quarterly_by_period.items():
        best = max(candidates, key=lambda x: x["filed"])
        result.append(best)

    # 年次: 最新filed
    for end_date, candidates in annual_by_end.items():
        best = max(candidates, key=lambda x: x["filed"])
        result.append(best)

    result.sort(key=lambda x: x["end"])
    return result


def save_raw_table(ticker: str, raw: dict) -> str:
    """raw tableをJSONファイルに保存し、パスを返す

    QUALITY-GATES-EPIC-1 Phase 3a: json.dump()直前に規約B（標準エントリ形状）を
    検証する。検証結果のオブジェクトは破棄し、保存対象データ自体は変更しない
    （既存のJSON on-disk形式を一切変えないため）。違反時はContractViolation
    （ValueErrorのサブクラス）を送出し、呼び出し元（update.py）の既存の
    per-ticker try/except Exceptionで捕捉・スキップされる。
    """
    validate_fields(raw.get("fields", {}))
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
    # 暦年ラベル(a_end[:4])での四半期グルーピングは非12月決算企業（KLAC/LRCX等）で
    # 誤検知する（CHECK-QREV-FYE-1）。年次end日を起点にtrailing 12ヶ月窓で
    # 該当4四半期を抽出する会計年度ベースのグルーピングに変更した
    # （ARCH-DATA-1残課題①でquarters_in_trailing_window()に一本化）。
    for a_end, a_val in a_only[-3:]:
        try:
            q_in_fy = quarters_in_trailing_window(q_only, a_end)
        except ValueError:
            continue
        if len(q_in_fy) == 4:
            q_total = sum(q_in_fy)
            gap_pct = abs(q_total - a_val) / abs(a_val) * 100 if a_val else 0
            if gap_pct > 5:
                issues.append(
                    f"FY(期末{a_end}) 年次vs四半期合計 乖離{gap_pct:.1f}%: "
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
