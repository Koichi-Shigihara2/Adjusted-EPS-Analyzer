"""
SEC XBRL データパーサー
Company Facts 生データを正規化された年次/四半期データに変換
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from .config import get_ticker_info
from .quarterly import TICKER_RESTRICTIONS
from .tag_definitions import TAG_CANDIDATES
from .utils import determine_fiscal_year


class SECParser:
    """SEC Company Facts データパーサー"""
    
    # タグをまたいでデータをマージするフィールド（早期終了しない）
    # 企業によって年代ごとに異なるXBRLタグを使うフィールドを列挙する
    # 例: GOOGLはFY2022-2024に RevenueFromContractWithCustomerExcludingAssessedTax,
    #         FY2025に Revenues を使用しており、早期終了するとFY2022-2024が欠落する
    MERGE_ALL_TAGS_FIELDS = {"revenue", "selling_and_marketing", "depreciation_and_amortization"}

    # XBRL項目マッピング（優先順位順）
    XBRL_MAPPING = {
        # BS（貸借対照表）
        "total_assets": [
            "Assets",
        ],
        "stockholders_equity": [
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ],
        "total_liabilities": [
            "Liabilities",
            "LiabilitiesAndStockholdersEquity",
        ],

        # BS詳細（ネットキャッシュ計算用）
        # tag_definitions.pyのTAG_CANDIDATESから取得する（LLY-CAPEX-STALE-1 Phase 2a）
        "cash_and_equivalents": list(TAG_CANDIDATES["CASH_AND_EQUIVALENTS"]),
        "short_term_investments": [
            "ShortTermInvestments",
            "MarketableSecuritiesCurrent",
            "AvailableForSaleSecuritiesCurrent",
            "AvailableForSaleSecurities",
        ],
        "long_term_debt": [
            # LongTermDebtNoncurrent を優先する。
            # LongTermDebt は current+non-current の合計値のため、LongTermDebtCurrent と
            # 組み合わせると Total_Debt が二重計上される（BUG-NETDEBT-2）。
            "LongTermDebtNoncurrent",
            "LongTermDebt",
            "LongTermNotesPayable",
            "SeniorNotes",
        ],
        "short_term_debt": [
            "ShortTermBorrowings",
            "NotesPayableCurrent",
            "LongTermDebtCurrent",
            "DebtCurrent",
            "CommercialPaper",
        ],
        # 流動項目（シガーバット検出用）
        "current_assets": [
            "AssetsCurrent",
        ],
        "current_liabilities": [
            "LiabilitiesCurrent",
        ],

        # RPO（残存履行義務）- SaaS企業向け
        "rpo": [
            "RevenueRemainingPerformanceObligation",
            "RemainingPerformanceObligation",
            "ContractWithCustomerLiability",
            "DeferredRevenue",
        ],
        
        # PL（損益計算書）
        "revenue": [
            "Revenues",  # 最優先（最も汎用的）
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",  # SOUN等
            "RevenueFromContractWithCustomer",
            "SalesRevenueNet",
            "TotalRevenue",
            "RevenuesNetOfInterestExpense",  # 銀行向け（SOFI等）
        ],
        # net_income・gross_profitはtag_definitions.pyのTAG_CANDIDATESから取得する
        # （LLY-CAPEX-STALE-1 Phase 2a・quarterly.py/parser.pyのタグリスト統合）
        "net_income": list(TAG_CANDIDATES["NET_INCOME"]),
        "gross_profit": list(TAG_CANDIDATES["GROSS_PROFIT"]),
        "cost_of_revenue": [
            "CostOfRevenue",
            "CostOfGoodsAndServicesSold",
            "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",  # IONQ等
        ],
        # R&D費（RICE計算の投資強度に使用）
        # CapitalizedComputerSoftwareDevelopmentCosts:
        #   費用化されずBSに資産計上されるソフトウェア開発費。
        #   PLに現れないR&D投資を捕捉するためのフォールバック。
        "research_and_development": list(TAG_CANDIDATES["RESEARCH_AND_DEVELOPMENT"]),
        "eps_diluted": [
            "EarningsPerShareDiluted",
        ],
        "eps_basic": [
            "EarningsPerShareBasic",
        ],
        # 販売・マーケティング費（RICE投資強度計算用）
        # 軽資産型企業（CELH等）はR&D/CapExが極小だが
        # マーケティング投資が成長の主な源泉のため投資強度に加算する
        "selling_and_marketing": [
            "MarketingAndAdvertisingExpense",
            "SellingAndMarketingExpense",    # CELH等: FY2022以前の旧タグ
            "MarketingExpense",              # AMZN等: Sales&Marketing費用
            "AdvertisingExpense",
        ],
        # SGA整合性チェック用参照フィールド（取得済みR&D+S&Mとの差分でタグ漏れを検出）
        "selling_general_and_administrative": [
            "SellingGeneralAndAdministrativeExpense",
        ],
        "operating_income": [
            "OperatingIncomeLoss",
        ],

        # CF（キャッシュフロー計算書）
        # operating_cash_flow・capital_expenditure・finance_lease_paymentsは
        # tag_definitions.pyのTAG_CANDIDATESから取得する（LLY-CAPEX-STALE-1 Phase 2a）。
        # capital_expenditureにはLLYが2023年以降申告する新タグ
        # PaymentsToAcquireOtherPropertyPlantAndEquipmentが含まれる
        # （旧タグPaymentsToAcquireProductiveAssetsは2022-09-30で申告停止）。
        "operating_cash_flow": list(TAG_CANDIDATES["OPERATING_CASH_FLOW"]),
        "capital_expenditure": list(TAG_CANDIDATES["CAPITAL_EXPENDITURE"]),
        # ファイナンスリース返済（AMZN等）: FCF計算から除外するために別取得
        "finance_lease_payments": list(TAG_CANDIDATES["FINANCE_LEASE_PAYMENTS"]),
        # 減価償却費（R&D資本化・維持CapEx分離に使用）
        # DepreciationAndAmortization: 最も汎用的なタグ（多くの企業）
        # DepreciationDepletionAndAmortization: 資源系企業等で使用
        # Depreciation: D&Aを分割開示する企業のDepreciation単独タグ
        # AmortizationOfIntangibleAssets: 無形資産償却を別開示する企業のフォールバック
        "depreciation_and_amortization": [
            "DepreciationAndAmortization",
            "DepreciationDepletionAndAmortization",
            "Depreciation",
            "AmortizationOfIntangibleAssets",
        ],
        # stock_based_compensation・buybackはtag_definitions.pyのTAG_CANDIDATESから取得する
        "stock_based_compensation": list(TAG_CANDIDATES["STOCK_BASED_COMPENSATION"]),
        # 自社株買い（キャッシュトラップ検出用）
        "buyback": list(TAG_CANDIDATES["BUYBACK"]),

        # 株式数
        "shares_diluted": [
            "WeightedAverageNumberOfDilutedSharesOutstanding",
            "CommonStockSharesOutstanding",  # フォールバック
        ],
        "shares_basic": [
            "WeightedAverageNumberOfSharesOutstandingBasic",
            "CommonStockSharesOutstanding",
        ],
    }
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = os.path.join(os.path.dirname(__file__), "data")

    def _detect_fiscal_end_month(self, us_gaap: dict) -> int:
        """10-K FYエントリから会計年度末月を検出（最頻月を返す、デフォルト12）"""
        month_counts: Dict[int, int] = {}
        for xbrl_key in self.XBRL_MAPPING.get("net_income", []) + self.XBRL_MAPPING.get("revenue", []):
            if xbrl_key not in us_gaap:
                continue
            for entry in us_gaap[xbrl_key].get("units", {}).get("USD", []):
                if entry.get("form") == "10-K" and entry.get("fp") == "FY":
                    end = entry.get("end", "")
                    if len(end) >= 7:
                        m = int(end[5:7])
                        month_counts[m] = month_counts.get(m, 0) + 1
            if month_counts:
                break
        return max(month_counts, key=month_counts.get) if month_counts else 12

    def parse_company_facts(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Company Facts 生データを読み込んでパース
        
        Returns:
            dict: {
                "ticker": str,
                "cik": str,
                "company_name": str,
                "annual": {2024: {...}, 2023: {...}, ...},
                "quarterly": {"2024Q1": {...}, ...}
            }
        """
        ticker = ticker.upper()
        raw_path = os.path.join(self.data_dir, ticker, "company_facts.json")
        
        if not os.path.exists(raw_path):
            print(f"   [{ticker}] company_facts.json が見つかりません")
            return None
        
        try:
            with open(raw_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"   [{ticker}] ファイル読み込みエラー: {e}")
            return None
        
        return self._parse_raw_data(ticker, raw_data)
    
    def _parse_raw_data(self, ticker: str, raw_data: dict) -> Dict[str, Any]:
        """生データをパース"""
        result = {
            "ticker": ticker,
            "cik": raw_data.get("cik", ""),
            "company_name": raw_data.get("entityName", ""),
            "annual": {},
            "quarterly": {},
            "parsed_at": datetime.now().isoformat(),
        }
        
        facts = raw_data.get("facts", {})
        us_gaap = facts.get("us-gaap", {})

        # 銘柄別 revenue_concept オーバーライド（quarterly.py の TICKER_RESTRICTIONS から参照）
        # 金融系銘柄（SOFI等）は MERGE_ALL_TAGS による先着タグ優先で狭義revenuタグが勝つ問題を回避
        _rev_concept_override = TICKER_RESTRICTIONS.get(ticker, {}).get("revenue_concept")

        # 会計年度末月を検出（非12月決算企業対応・determine_fiscal_year に渡す）
        fiscal_end_month = self._detect_fiscal_end_month(us_gaap)

        # 全項目を抽出
        extracted = {}
        for field_name, xbrl_keys in self.XBRL_MAPPING.items():
            # 株式数は同一期間で最大値を採用（異常値対策）
            use_max = False  # 株式数は優先順位順で取得（最大値ではない）
            # 以前はuse_max=Trueだったが、CommonStockSharesOutstanding（期末発行済）が
            # WeightedAverageNumberOfDilutedSharesOutstanding（加重平均希薄化後）より
            # 大きい場合に誤った値が取得される問題があった
            merge_all = field_name in self.MERGE_ALL_TAGS_FIELDS
            # revenue_concept が指定されている場合はそのタグのみ使用（mergeなし）
            if field_name == "revenue" and _rev_concept_override:
                xbrl_keys = [_rev_concept_override]
                merge_all = False
            extracted[field_name] = self._extract_values(us_gaap, xbrl_keys, use_max=use_max, merge_all_tags=merge_all, fiscal_end_month=fiscal_end_month)
        
        # 年次データを集約
        years = self._get_available_years(extracted)
        for year in years:
            annual_data = self._build_period_data(extracted, year, is_annual=True)
            if annual_data:
                result["annual"][year] = annual_data
        
        # 四半期データを集約
        quarters = self._get_available_quarters(extracted)
        for quarter in quarters:
            quarterly_data = self._build_period_data(extracted, quarter, is_annual=False)
            if quarterly_data:
                result["quarterly"][quarter] = quarterly_data
        
        return result
    
    def _extract_values(self, us_gaap: dict, xbrl_keys: List[str], use_max: bool = False, merge_all_tags: bool = False, fiscal_end_month: int = 12) -> Dict[str, Any]:
        """
        指定されたXBRLキーから値を抽出

        Args:
            us_gaap: SEC XBRL データ
            xbrl_keys: 優先順位順のXBRLキーリスト
            use_max: 同一期間に複数値がある場合、最大値を使用（株式数向け）
                     Trueの場合、全XBRLキーを検索して最大値を採用
            merge_all_tags: 年代ごとにXBRLタグが切り替わる銘柄向け。全キーの値を統合する

        Returns:
            dict: {
                "annual": {2024: value, 2023: value, ...},
                "quarterly": {"2024Q1": value, ...}
            }
        """
        if use_max or merge_all_tags:
            return self._extract_values_merged(us_gaap, xbrl_keys, use_max, fiscal_end_month)
        return self._extract_values_best_candidate(us_gaap, xbrl_keys, fiscal_end_month)

    def _extract_values_merged(self, us_gaap: dict, xbrl_keys: List[str], use_max: bool, fiscal_end_month: int) -> Dict[str, Any]:
        """use_max=True または merge_all_tags=True の場合の抽出（全キーを検索して統合）"""
        result = {"annual": {}, "quarterly": {}}
        # 期末日を記録（同一end_yearで最新のend日付を優先するため）
        annual_end_dates = {}
        quarterly_end_dates = {}
        # fy==end_yearの完全一致フラグ: 非December FY企業でQ1等中間期エントリが
        # 同一end_yearを持ち全年データを上書きするのを防ぐ（INTU等の対策）
        annual_exact_match = {}
        # 期間日数（end-start）を記録。同一end_date・同一exact_matchレベルで
        # 複数タグが競合した場合に365日（正規の年次期間）に近い方を優先するために使う
        # （SEC-TAG-FICO-CPRT-1: 91日間の四半期比較開示がform='10-K'・fp='FY'で
        #  年次候補に混入し、XBRL_MAPPINGの列挙順（先に処理されたタグ）が
        #  実質的に勝ってしまう早い者勝ちバグへの対応。FICO/CPRT/LITEで確認）
        annual_durations = {}

        for key in xbrl_keys:
            if key not in us_gaap:
                continue

            units = us_gaap[key].get("units", {})

            # USD or shares
            for unit_type in ["USD", "shares", "USD/shares"]:
                if unit_type not in units:
                    continue

                for entry in units[unit_type]:
                    form = entry.get("form", "")
                    fy = entry.get("fy")
                    fp = entry.get("fp", "")
                    val = entry.get("val")
                    end_date = entry.get("end", "")

                    if val is None or fy is None:
                        continue

                    # 年次（10-K）- determine_fiscal_year で会計年度キーを統一定義に従って決定
                    if form == "10-K" and fp == "FY":
                        # determine_fiscal_year(期末日, fiscal_end_month) が単一定義
                        # fy==end_yearはFY通年データとして信頼度が高い（exact match）
                        # fy!=end_yearは比較年度エントリ（FCX等）または中間期エントリ（INTU Q1等）
                        if end_date and len(end_date) >= 10:
                            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                            end_year = determine_fiscal_year(end_dt, fiscal_end_month)
                        else:
                            end_year = fy  # end_date 不明時は SEC の fy フィールドを使用
                        exact = (fy == end_year)
                        start_date = entry.get("start", "")
                        days = None
                        if start_date and end_date and len(start_date) >= 10 and len(end_date) >= 10:
                            try:
                                days = (end_dt - datetime.strptime(start_date, '%Y-%m-%d')).days
                            except ValueError:
                                days = None
                        if use_max:
                            # 最大値を採用（株式数の異常値対策）
                            if end_year not in result["annual"] or val > result["annual"][end_year]:
                                result["annual"][end_year] = val
                                annual_end_dates[end_year] = end_date
                        else:
                            if end_year not in result["annual"]:
                                result["annual"][end_year] = val
                                annual_end_dates[end_year] = end_date
                                annual_exact_match[end_year] = exact
                                annual_durations[end_year] = days
                            elif exact and not annual_exact_match.get(end_year, True):
                                # exact matchで上書き: 非December FY企業のQ1等中間期エントリ
                                # (fy=N+1, end_year=N) が全年データ(fy=N, end_year=N)を上書きするのを防ぐ
                                result["annual"][end_year] = val
                                annual_end_dates[end_year] = end_date
                                annual_exact_match[end_year] = True
                                annual_durations[end_year] = days
                            elif exact == annual_exact_match.get(end_year, False):
                                stored_end = annual_end_dates.get(end_year, "")
                                if end_date > stored_end:
                                    # 同じexact_matchレベル: 最新のend_dateを優先
                                    result["annual"][end_year] = val
                                    annual_end_dates[end_year] = end_date
                                    annual_durations[end_year] = days
                                elif end_date == stored_end and days is not None:
                                    # SEC-TAG-FICO-CPRT-1: end_dateも同一の場合、
                                    # 期間日数が365日（正規の年次期間）に近い方を優先する
                                    stored_days = annual_durations.get(end_year)
                                    if stored_days is None or abs(days - 365) < abs(stored_days - 365):
                                        result["annual"][end_year] = val
                                        annual_durations[end_year] = days

                    # 四半期（10-Q）
                    elif form == "10-Q" and fp in ["Q1", "Q2", "Q3"]:
                        quarter_key = f"{fy}{fp}"
                        if use_max:
                            if quarter_key not in result["quarterly"] or val > result["quarterly"][quarter_key]:
                                result["quarterly"][quarter_key] = val
                                quarterly_end_dates[quarter_key] = end_date
                        else:
                            # 同一四半期では最新のend日付を優先
                            if quarter_key not in result["quarterly"]:
                                result["quarterly"][quarter_key] = val
                                quarterly_end_dates[quarter_key] = end_date
                            elif end_date > quarterly_end_dates.get(quarter_key, ""):
                                result["quarterly"][quarter_key] = val
                                quarterly_end_dates[quarter_key] = end_date

                # 最初に見つかったunit_typeのデータを使用
                if result["annual"] or result["quarterly"]:
                    break

            # 全キーを検索（早期終了しない。merge_all_tagsは年代ごとのタグ切替を横断統合するため）

        return result

    def _extract_values_best_candidate(self, us_gaap: dict, xbrl_keys: List[str], fiscal_end_month: int) -> Dict[str, Any]:
        """use_max/merge_all_tagsいずれもFalseの場合の抽出（1つの候補タグを選んで採用する）

        LLY-CAPEX-STALE-1 Phase 2a: 候補キーを優先順位順に「最新期末年が
        取れた最初のキーで打ち切る」方式は、真に最新のデータを持つタグが
        候補リストに含まれていない場合に検知できない（LLYのcapital_expenditure:
        旧候補3タグはいずれも年次(10-K FY)エントリを一度も持たず常に空扱い
        だった）。候補キーをすべて独立に抽出し、annualデータを持つ候補の
        中から最新end_yearが最も新しいものを採用する（quarterly.pyの
        _select_best_candidate と同じ考え方）。annualデータを持つ候補が
        皆無の場合のみ、quarterlyの最新度で採用する。
        """
        candidates: list[tuple[str, Dict[str, Any]]] = []
        for key in xbrl_keys:
            if key not in us_gaap:
                continue
            key_result = self._extract_single_key(us_gaap, key, fiscal_end_month)
            if not key_result["annual"] and not key_result["quarterly"]:
                continue
            candidates.append((key, key_result))

        if not candidates:
            return {"annual": {}, "quarterly": {}}

        def _freshness(idx: int) -> tuple[int, str, int]:
            _, key_result = candidates[idx]
            latest_annual = max(key_result["annual"].keys(), default=0)
            latest_quarter = max(key_result["quarterly"].keys(), default="")
            return latest_annual, latest_quarter, -idx

        qualified = [i for i in range(len(candidates)) if candidates[i][1]["annual"]]
        pool = qualified if qualified else list(range(len(candidates)))
        best_idx = max(pool, key=_freshness)
        return candidates[best_idx][1]

    def _extract_single_key(self, us_gaap: dict, key: str, fiscal_end_month: int) -> Dict[str, Any]:
        """1つのXBRLキーからannual/quarterly値を抽出する（候補選定の評価単位）"""
        result: Dict[str, Any] = {"annual": {}, "quarterly": {}}
        annual_end_dates: Dict[int, str] = {}
        quarterly_end_dates: Dict[str, str] = {}
        annual_exact_match: Dict[int, bool] = {}

        units = us_gaap.get(key, {}).get("units", {})
        for unit_type in ["USD", "shares", "USD/shares"]:
            if unit_type not in units:
                continue

            for entry in units[unit_type]:
                form = entry.get("form", "")
                fy = entry.get("fy")
                fp = entry.get("fp", "")
                val = entry.get("val")
                end_date = entry.get("end", "")

                if val is None or fy is None:
                    continue

                if form == "10-K" and fp == "FY":
                    if end_date and len(end_date) >= 10:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        end_year = determine_fiscal_year(end_dt, fiscal_end_month)
                    else:
                        end_year = fy
                    exact = (fy == end_year)
                    if end_year not in result["annual"]:
                        result["annual"][end_year] = val
                        annual_end_dates[end_year] = end_date
                        annual_exact_match[end_year] = exact
                    elif exact and not annual_exact_match.get(end_year, True):
                        result["annual"][end_year] = val
                        annual_end_dates[end_year] = end_date
                        annual_exact_match[end_year] = True
                    elif exact == annual_exact_match.get(end_year, False):
                        if end_date > annual_end_dates.get(end_year, ""):
                            result["annual"][end_year] = val
                            annual_end_dates[end_year] = end_date

                elif form == "10-Q" and fp in ["Q1", "Q2", "Q3"]:
                    quarter_key = f"{fy}{fp}"
                    if quarter_key not in result["quarterly"]:
                        result["quarterly"][quarter_key] = val
                        quarterly_end_dates[quarter_key] = end_date
                    elif end_date > quarterly_end_dates.get(quarter_key, ""):
                        result["quarterly"][quarter_key] = val
                        quarterly_end_dates[quarter_key] = end_date

            if result["annual"] or result["quarterly"]:
                break

        return result
    
    def _get_available_years(self, extracted: dict) -> List[int]:
        """利用可能な年度を取得"""
        years = set()
        for field_data in extracted.values():
            years.update(field_data.get("annual", {}).keys())
        return sorted(years, reverse=True)
    
    def _get_available_quarters(self, extracted: dict) -> List[str]:
        """利用可能な四半期を取得"""
        quarters = set()
        for field_data in extracted.values():
            quarters.update(field_data.get("quarterly", {}).keys())
        return sorted(quarters, reverse=True)
    
    def _build_period_data(self, extracted: dict, period: Any, is_annual: bool) -> Optional[Dict[str, Any]]:
        """特定期間のデータを構築"""
        period_type = "annual" if is_annual else "quarterly"
        
        data = {
            "period": str(period),
            "bs": {},
            "pl": {},
            "cf": {},
            "shares": {},
            "other": {},
        }
        
        # BS
        for field in ["total_assets", "stockholders_equity", "total_liabilities",
                      "cash_and_equivalents", "short_term_investments",
                      "long_term_debt", "short_term_debt",
                      "current_assets", "current_liabilities"]:
            val = extracted.get(field, {}).get(period_type, {}).get(period)
            if val is not None:
                data["bs"][field] = val
        
        # PL
        for field in ["revenue", "gross_profit", "cost_of_revenue", "net_income", "eps_diluted", "eps_basic",
                      "research_and_development", "selling_and_marketing",
                      "selling_general_and_administrative", "operating_income"]:
            val = extracted.get(field, {}).get(period_type, {}).get(period)
            if val is not None:
                data["pl"][field] = val
        
        # CF
        for field in ["operating_cash_flow", "capital_expenditure", "finance_lease_payments",
                      "depreciation_and_amortization", "stock_based_compensation", "buyback"]:
            val = extracted.get(field, {}).get(period_type, {}).get(period)
            if val is not None:
                data["cf"][field] = val
        
        # FCF計算（ファイナンスリース除外）
        #
        # FCF = OCF - (|CapEx| - |FinanceLeasePmts|)
        # ファイナンスリースはCapExから除外（AMZN等対応）
        ocf   = data["cf"].get("operating_cash_flow", 0)
        capex = data["cf"].get("capital_expenditure", 0)
        fl    = data["cf"].get("finance_lease_payments", 0)

        # CapEx・ファイナンスリースはSECデータで負値の場合があるためabs()
        abs_capex = abs(capex)
        abs_fl    = abs(fl)
        pure_capex = abs_capex - abs_fl  # リース除外後の純CapEx

        if ocf != 0:
            data["cf"]["free_cash_flow"] = ocf - max(0, pure_capex)
            data["cf"]["fcf_method"] = "traditional"
            data["cf"]["finance_lease_payments_applied"] = abs_fl > 0
        
        # Shares
        for field in ["shares_diluted", "shares_basic"]:
            val = extracted.get(field, {}).get(period_type, {}).get(period)
            if val is not None:
                data["shares"][field] = val
        
        # Other (RPO等)
        for field in ["rpo"]:
            val = extracted.get(field, {}).get(period_type, {}).get(period)
            if val is not None:
                data["other"][field] = val

        # SGA整合性チェック:
        # selling_and_marketing が完全に未取得（None）かつ
        # SGA総額が売上比5%超の場合に data_quality 警告を記録する。
        # ※ SGA = Selling + G&A であり G&A は投資強度に含めないため、
        #   (R&D + S&M) vs SGA 差額による比率チェックは常に誤発火する。
        #   S&M が何らかの値で取得できている場合は警告不要。
        sga_total  = data["pl"].get("selling_general_and_administrative")
        sm_missing = data["pl"].get("selling_and_marketing") is None
        revenue    = data["pl"].get("revenue") or 0
        if sm_missing and sga_total and sga_total > 0 and revenue > 0:
            if (sga_total / revenue) > 0.05:
                data["data_quality"] = {
                    "sga_gap_warning": True,
                    "sga_total": sga_total,
                    "sga_captured": 0,
                    "gap_amount": sga_total,
                    "gap_ratio": 1.0,
                    "note": (
                        f"S&M未取得かつSGA総額${sga_total/1e6:.0f}M"
                        f"（売上比{sga_total/revenue*100:.0f}%）。"
                        "企業がSGA内訳を非開示の可能性。投資強度が過小になる場合があります"
                    ),
                }

        # 最低限のデータがあるか確認
        if not any([data["bs"], data["pl"], data["cf"]]):
            return None
        
        return data
    
    def save_parsed_data(self, ticker: str, parsed: dict) -> None:
        """パース済みデータを個別ファイルに保存"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.data_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        
        # 年次データ
        for year, data in parsed.get("annual", {}).items():
            path = os.path.join(ticker_dir, f"annual_{year}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "ticker": ticker,
                    "period": year,
                    "form": "10-K",
                    **data
                }, f, ensure_ascii=False, indent=2)
        
        # 四半期データ
        for quarter, data in parsed.get("quarterly", {}).items():
            path = os.path.join(ticker_dir, f"quarterly_{quarter}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "ticker": ticker,
                    "period": quarter,
                    "form": "10-Q",
                    **data
                }, f, ensure_ascii=False, indent=2)
        
        print(f"   [{ticker}] 保存完了: {len(parsed.get('annual', {}))}年次, {len(parsed.get('quarterly', {}))}四半期")
    
    def parse_and_save(self, ticker: str) -> Optional[Dict[str, Any]]:
        """パースして保存"""
        parsed = self.parse_company_facts(ticker)
        if parsed:
            self.save_parsed_data(ticker, parsed)
        return parsed


if __name__ == "__main__":
    parser = SECParser()
    
    # テスト
    parsed = parser.parse_and_save("TSLA")
    if parsed:
        print(f"\n年次データ: {list(parsed['annual'].keys())}")
        print(f"四半期データ: {list(parsed['quarterly'].keys())[:8]}...")
