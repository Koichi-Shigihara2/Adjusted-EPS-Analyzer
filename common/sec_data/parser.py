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
from .utils import determine_fiscal_year, detect_fiscal_end_month, detect_fiscal_anchor_date, _day_of_year
from .fetcher import load_submissions


class SECParser:
    """SEC Company Facts データパーサー"""
    
    # タグをまたいでデータをマージするフィールド（早期終了しない）
    # 企業によって年代ごとに異なるXBRLタグを使うフィールドを列挙する
    # 例: GOOGLはFY2022-2024に RevenueFromContractWithCustomerExcludingAssessedTax,
    #         FY2025に Revenues を使用しており、早期終了するとFY2022-2024が欠落する
    MERGE_ALL_TAGS_FIELDS = {"revenue", "selling_and_marketing", "depreciation_and_amortization"}

    # instant fact（単一時点end_dateのみを持ち、start_dateを持たないXBRL概念）
    # のフィールド。BS9項目 + RPO残高。本人データ判定は_collect_own_data_instant()
    # （start_date不要版）を使う（ARCH-DATA-1残課題④: _collect_own_data_annual()は
    # start_date必須フィルタを持つためinstant factを常に除外していた）
    INSTANT_FACT_FIELDS = {
        "total_assets", "stockholders_equity", "total_liabilities",
        "cash_and_equivalents", "short_term_investments",
        "long_term_debt", "short_term_debt",
        "current_assets", "current_liabilities",
        "rpo",
    }

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
            # FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1（2026-07-19追加）:
            # CASH-TAG-MISSING-1と同型のタグ網羅漏れ。CECL(ASU 2016-13)taxonomy
            # 対応後に多くの企業が移行した"Current"明示タグを追加。10-K原本で
            # BS本体の「Marketable securities/Short-term investments」流動資産行
            # と一致することを個別確認済み（ALAB/BBAI/CRM/DDOG/GTLB/INTU/IOT/KO/
            # NET/NOW/RBRK/RMBS/SITM/VRT/ZS）。KLAC/NVDA/SOFI/TER/Vは合算タグでは
            # 過大/過小評価となるため対象外（[[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]
            # で銘柄別override設計を別途検討）。CAT/LLYはBS本体に科目行自体が
            # 存在しない（footnote専用）ため対象外。
            "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
            "DebtSecuritiesAvailableForSaleExcludingAccruedInterestCurrent",
            "DebtSecuritiesHeldToMaturityAmortizedCostAfterAllowanceForCreditLossCurrent",
            "OtherShortTermInvestments",
        ],
        "long_term_debt": [
            # LongTermDebtNoncurrent を優先する。
            # LongTermDebt は current+non-current の合計値のため、LongTermDebtCurrent と
            # 組み合わせると Total_Debt が二重計上される（BUG-NETDEBT-2）。
            "LongTermDebtNoncurrent",
            "LongTermDebt",
            "LongTermNotesPayable",
            "SeniorNotes",
            # FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1（2026-07-19追加）:
            # AVGO型（VMware買収後にLongTermDebtNoncurrentの申告を停止し
            # LongTermDebtAndCapitalLeaseObligationsへ移行）と同種のタグ切替
            # 欠損。10-K原本で連結BS本体の「Long-term debt」行と一致することを
            # 個別確認済み（AVGO/CDNS/CON/DDOG/HEI/KO/NET/NOW/ONDS/PM/RBRK/
            # RXRX/VZ/XOM/ZS）。SOFIは既存のticker_restrictions
            # （ltdebt_concept=DebtLongtermAndShorttermCombinedAmount、
            # SOFI-DATA-1）で個別対応済みのため、本リストには追加しない
            # （追加するとSOFIのcurrent/noncurrent二重計上リスクがあるため注意）。
            "LongTermDebtAndCapitalLeaseObligations",
            "UnsecuredLongTermDebt",
            "ConvertibleLongTermNotesPayable",
            "ConvertibleDebtNoncurrent",
            "OtherLongTermDebt",
        ],
        "short_term_debt": [
            "ShortTermBorrowings",
            "NotesPayableCurrent",
            "LongTermDebtCurrent",
            "DebtCurrent",
            "CommercialPaper",
            # FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1（2026-07-19追加）:
            # long_term_debtのAndCapitalLeaseObligations系タグのCurrent版・
            # 転換社債Current版。10-K原本で連結BS本体の流動負債区分と一致する
            # ことを個別確認済み（CON/DDOG/ELF/NET/QBTS/RXRX/ZS）。
            # AVAV/ESTC/ZETA/SOFIは該当額が既にlong_term_debt側に正しく
            # 計上済みのため対象外（二重計上防止）。SCCOは最新年度の
            # Current portion of long-term debtが明示的に$0（生涯フェード
            # アウト相当）のため対象外。
            "LongTermDebtAndCapitalLeaseObligationsCurrent",
            "ConvertibleNotesPayableCurrent",
            "ConvertibleDebtCurrent",
            "OtherLongTermDebtCurrent",
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
            # FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1（2026-07-19追加）:
            # 親タグ（流動+非流動合算のContractWithCustomerLiability/
            # DeferredRevenue）を申告せず、Current変種のみ申告する企業向け。
            # 10-K原本でBS本体の該当科目と一致することを個別確認済み
            # （ADSK/ALAB/APP/BBAI/CAKE/CART/CELH/CIX/CPRT/DOCN/ENTG/FLYW/
            # INTU/JOBY/KULR/MRVL/RXRX/TASK/VRT/ZETA）。非SaaS業態の
            # 真のゼロ銘柄（ABBV/JNJ/KO/PEP/PM/XOM/SCCO等）は該当タグが
            # 一切存在しないため引き続きNoneのまま。
            "ContractWithCustomerLiabilityCurrent",
            "DeferredRevenueCurrent",
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

    def _fiscal_detection_keys(self) -> List[str]:
        """会計年度末月・決算アンカー日検出に使うXBRLタグ候補（net_income+revenue）"""
        return self.XBRL_MAPPING.get("net_income", []) + self.XBRL_MAPPING.get("revenue", [])

    def _detect_fiscal_end_month(self, us_gaap: dict) -> int:
        """10-K FYエントリから会計年度末月を検出（最頻月を返す、デフォルト12）

        ARCH-DATA-1ステージ2: 実体はcommon/sec_data/utils.py::detect_fiscal_end_month()
        に統一済み（extract_key_facts.py側の独自実装も同関数を参照する）。
        ここでは本クラスのXBRL_MAPPING候補タグを渡す薄いラッパーとして残す。
        """
        return detect_fiscal_end_month(us_gaap, self._fiscal_detection_keys())

    def _detect_fiscal_anchor_date(self, us_gaap: dict) -> Optional[tuple]:
        """本人10-K annualエントリから決算アンカー日（月+日）を検出する

        ARCH-DATA-1ステージ2: common/sec_data/utils.py::detect_fiscal_anchor_date()
        の薄いラッパー。_detect_fiscal_end_monthと同じ候補タグを使う。
        """
        return detect_fiscal_anchor_date(us_gaap, self._fiscal_detection_keys())

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

        # submissions.json（accn -> reportDate）を読み込む。
        # 存在しない場合は空dictとなり、本人データ判定はスキップされ
        # determine_fiscal_year()フォールバックのみで動作する（後方互換）
        accn_reportdate = load_submissions(ticker, data_dir=self.data_dir)

        return self._parse_raw_data(ticker, raw_data, accn_reportdate=accn_reportdate)

    def _parse_raw_data(self, ticker: str, raw_data: dict, accn_reportdate: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
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
        # 銘柄別 ltdebt_concept オーバーライド（SOFI-DATA-1: 銀行免許取得後にLongTermDebt系
        # タグの申告を停止し代替タグへ移行したケース向け。quarterly.pyと同一の
        # ticker_restrictionsを参照する）
        _ltdebt_concept_override = TICKER_RESTRICTIONS.get(ticker, {}).get("ltdebt_concept")
        # 銘柄別 sti_concept オーバーライド（FY52WEEK-BS-STI-OVERRIDE-DESIGN-1:
        # KLAC/TER/V/SOFIはshort_term_investmentsの標準候補群（XBRL_MAPPING）が
        # 申告停止済み・非分類BS・正しいタグが汎用的すぎるため、ltdebt_conceptと
        # 同型のticker限定オーバーライドとする）
        _sti_concept_override = TICKER_RESTRICTIONS.get(ticker, {}).get("sti_concept")
        # 銘柄別 cross_filing_tags オーバーライド（NVDA-STI-TAG-UNIDENTIFIED-1:
        # ANOMALY-PATTERN-CATALOG-1型C。単一タグでは捕捉できず、複数XBRL概念を
        # 指定end_date・指定form制限で直接検索し合算する必要があるケース向け。
        # sti_concept等と異なり、ticker×period×fieldを明示指定した組み合わせ
        # にのみ適用され、他の全銘柄・全フィールドの既存抽出ロジックには
        # 一切影響しない。_apply_cross_filing_tags()参照）
        _cross_filing_tags = TICKER_RESTRICTIONS.get(ticker, {}).get("cross_filing_tags")

        # 会計年度末月を検出（非12月決算企業対応・determine_fiscal_year に渡す。
        # 本人データが存在しない年度のフォールバック判定にのみ使用する）
        fiscal_end_month = self._detect_fiscal_end_month(us_gaap)
        # 決算アンカー日（月+日）を検出（ARCH-DATA-1ステージ2: アンカー日
        # ウィンドウ方式）。検出不可の場合はNone,Noneとなり、determine_fiscal_year()
        # 側で従来の月のみ比較にフォールバックする
        _anchor = self._detect_fiscal_anchor_date(us_gaap)
        anchor_month, anchor_day = _anchor if _anchor else (None, None)

        # FY52WEEK-BUCKET-MISPLACE-1 根本修正: reportDate==end_dateが成立する
        # 「本人の当期データ」のfyタグを年度キーとしてそのまま採用する。
        # accn_reportdateが空（submissions.json未取得）の場合は全件フォールバックのみで動作する。
        _accn_reportdate = accn_reportdate or {}
        _fy_collisions: List[Dict[str, Any]] = []
        _fy_tag_mismatches: List[Dict[str, Any]] = []
        # FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: 本人データ側と既存（フォールバック）
        # 側の生fyタグが異なるまま同一年度バケツで競合したケースを記録する
        _fye_boundary_collisions: List[Dict[str, Any]] = []

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
            # ltdebt_concept が指定されている場合はそのタグのみ使用
            if field_name == "long_term_debt" and _ltdebt_concept_override:
                xbrl_keys = [_ltdebt_concept_override]
            # sti_concept が指定されている場合はそのタグのみ使用
            if field_name == "short_term_investments" and _sti_concept_override:
                xbrl_keys = [_sti_concept_override]
            extracted[field_name] = self._extract_values(
                us_gaap, xbrl_keys, use_max=use_max, merge_all_tags=merge_all,
                fiscal_end_month=fiscal_end_month, accn_reportdate=_accn_reportdate,
                field_name=field_name, collisions_out=_fy_collisions,
                anchor_month=anchor_month, anchor_day=anchor_day,
                fy_mismatches_out=_fy_tag_mismatches,
                boundary_collisions_out=_fye_boundary_collisions,
            )

        # NVDA-STI-TAG-UNIDENTIFIED-1: cross_filing_tagsに明示登録された
        # ticker×period×fieldの組み合わせについてのみ、複数タグ合算値で
        # extracted[field]の該当バケツを上書きする（型C対応・①案）。
        # 標準抽出ループの後に適用することで、通常経路の結果を出発点として
        # 上書きし、既存の抽出ロジック自体には一切手を加えない。
        if _cross_filing_tags:
            self._apply_cross_filing_tags(us_gaap, extracted, _cross_filing_tags)

        # ARCH-DATA-1ステージ3: fyタグ裏取り不一致を記録（0件でも毎回書き込む。
        # fy_collision_logと同じ化石ファイル対策）
        self._save_fy_tag_mismatch_log(ticker, _fy_tag_mismatches)

        # 衝突0件でも毎回書き込む（IOT/AVGO/MRVLの化石ファイル問題の再発防止。
        # 一度検知された衝突が後日解消された場合に古いログが残り続けることを防ぐ）
        self._save_fy_collision_log(ticker, _fy_collisions)

        # FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: 0件でも毎回書き込む（同上の化石
        # ファイル対策と同じ理由）
        self._save_fye_boundary_collision_log(ticker, _fye_boundary_collisions)

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
    
    def _extract_values(self, us_gaap: dict, xbrl_keys: List[str], use_max: bool = False, merge_all_tags: bool = False,
                         fiscal_end_month: int = 12, accn_reportdate: Optional[Dict[str, str]] = None,
                         field_name: str = "", collisions_out: Optional[List[Dict[str, Any]]] = None,
                         anchor_month: Optional[int] = None, anchor_day: Optional[int] = None,
                         fy_mismatches_out: Optional[List[Dict[str, Any]]] = None,
                         boundary_collisions_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        指定されたXBRLキーから値を抽出

        Args:
            us_gaap: SEC XBRL データ
            xbrl_keys: 優先順位順のXBRLキーリスト
            use_max: 同一期間に複数値がある場合、最大値を使用（株式数向け）
                     Trueの場合、全XBRLキーを検索して最大値を採用
            merge_all_tags: 年代ごとにXBRLタグが切り替わる銘柄向け。全キーの値を統合する
            accn_reportdate: {accn: reportDate} のマッピング（本人データ判定用。
                              FY52WEEK-BUCKET-MISPLACE-1根本修正）
            field_name: ログ記録用のフィールド名（"revenue"等）
            collisions_out: 本人データ同士のfyキー衝突を記録するリスト（呼び出し元で集約）
            anchor_month/anchor_day: 決算アンカー日（ARCH-DATA-1ステージ2）。
                              determine_fiscal_year()にそのまま渡す
            fy_mismatches_out: 採用エントリのfyタグと年度バケツキーの不一致を記録する
                              リスト（ARCH-DATA-1ステージ3: fyタグ裏取り、呼び出し元で集約）
            boundary_collisions_out: 本人データ側と既存（フォールバック）側の生fyタグが
                              異なるまま同一年度バケツで競合したケースを記録するリスト
                              （FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1、呼び出し元で集約）

        Returns:
            dict: {
                "annual": {2024: value, 2023: value, ...},
                "quarterly": {"2024Q1": value, ...}
            }
        """
        if use_max or merge_all_tags:
            return self._extract_values_merged(us_gaap, xbrl_keys, use_max, fiscal_end_month,
                                                accn_reportdate=accn_reportdate, field_name=field_name,
                                                collisions_out=collisions_out,
                                                anchor_month=anchor_month, anchor_day=anchor_day,
                                                fy_mismatches_out=fy_mismatches_out,
                                                boundary_collisions_out=boundary_collisions_out)
        return self._extract_values_best_candidate(us_gaap, xbrl_keys, fiscal_end_month,
                                                    accn_reportdate=accn_reportdate, field_name=field_name,
                                                    collisions_out=collisions_out,
                                                    anchor_month=anchor_month, anchor_day=anchor_day,
                                                    fy_mismatches_out=fy_mismatches_out,
                                                    boundary_collisions_out=boundary_collisions_out)

    def _find_entry_by_end_date(self, us_gaap: dict, tag: str, end_date: str,
                                 forms: tuple) -> Optional[Dict[str, Any]]:
        """指定タグ・指定end_date・指定form群に一致するエントリを1件返す
        （NVDA-STI-TAG-UNIDENTIFIED-1: _apply_cross_filing_tags()専用の
        ピンポイント検索。既存の_collect_own_data_annual/_instantが持つ
        accn_reportdate自己一致チェックを意図的に迂回する唯一の経路のため、
        TICKER_RESTRICTIONSのcross_filing_tagsに明示登録された呼び出し元
        からのみ使用すること）。

        複数ヒットした場合（同一end_dateへの10-K/A訂正申告等）はfiled日が
        最新のものを採用する。

        Returns:
            該当エントリのdict（"val"/"form"/"accn"/"filed"等）、なければNone
        """
        candidates = []
        units = us_gaap.get(tag, {}).get("units", {})
        for entry in units.get("USD", []):
            if entry.get("form") not in forms:
                continue
            if entry.get("end") != end_date:
                continue
            if entry.get("val") is None:
                continue
            candidates.append(entry)
        if not candidates:
            return None
        candidates.sort(key=lambda e: e.get("filed", ""))
        return candidates[-1]

    def _apply_cross_filing_tags(self, us_gaap: dict, extracted: Dict[str, Any],
                                  cross_filing_config: Dict[str, tuple]) -> None:
        """NVDA-STI-TAG-UNIDENTIFIED-1（ANOMALY-PATTERN-CATALOG-1型C: 資産クラス
        変化・当年度未タグ化型）向け。TICKER_RESTRICTIONSのcross_filing_tagsに
        明示登録されたticker×period×fieldの組み合わせについてのみ、複数XBRL
        タグを指定end_date・指定form制限で直接検索し合算した値で
        extracted[field]の該当バケツ（annual/quarterly）を上書きする。

        既存の_collect_own_data_annual/_instantが持つ`form in (10-K, 10-K/A)`
        フィルタ・accn_reportdate自己一致チェックはここでは一切参照しない
        （_find_entry_by_end_date経由の意図的な迂回）。本関数はcross_filing_tags
        に明示登録された組み合わせにのみ発火するため、他の全銘柄・全フィールド・
        当該ticker自身の他フィールドの既存抽出結果には一切影響しない。

        periodがint（年度）の場合はannualバケツ、str（例:"2027Q1"、parser.pyの
        quarter_key形式 f"{fy}{fp}"）の場合はquarterlyバケツを上書きする。
        合算対象タグの一部が指定end_date・form条件で見つからない場合、その
        periodの上書きはスキップする（中途半端な部分合算値を書き込まない）。
        """
        for field_name, period_specs in cross_filing_config.items():
            field_result = extracted.setdefault(field_name, {"annual": {}, "quarterly": {}})
            for spec in period_specs:
                period = spec["period"]
                end_date = spec["end_date"]
                components = spec["components"]

                total = 0.0
                source_tags = []
                found_all = True
                for comp in components:
                    entry = self._find_entry_by_end_date(us_gaap, comp["tag"], end_date, comp["forms"])
                    if entry is None:
                        found_all = False
                        break
                    total += entry["val"]
                    source_tags.append(comp["tag"])
                if not found_all:
                    continue

                bucket = "annual" if isinstance(period, int) else "quarterly"
                field_result[bucket][period] = total

                residual_pct = spec.get("approx_residual_pct")
                if bucket == "annual":
                    prov = field_result.setdefault("_annual_provenance", {})
                    prov[period] = {
                        "is_own_data": True,
                        "is_approximated": residual_pct is not None,
                        "residual_pct": residual_pct,
                        "combined_tags": source_tags,
                    }

    def _collect_own_data_annual(self, us_gaap: dict, xbrl_keys: List[str],
                                  accn_reportdate: Dict[str, str], fiscal_end_month: int, field_name: str,
                                  collisions_out: Optional[List[Dict[str, Any]]],
                                  anchor_month: Optional[int] = None, anchor_day: Optional[int] = None) -> Dict[int, Any]:
        """
        reportDate==end_dateが成立する「本人の当期データ」のみを対象に、
        fyタグを年度キーとして採用した値マップを構築する
        （FY52WEEK-BUCKET-MISPLACE-1根本修正: determine_fiscal_year()の月のみ判定を
        経由せず、企業自身が申告したfyタグを信頼する）。

        fp=="Q4"も候補に含める: DELLの真のFY2019 10-K原本はfp="Q4"でタグ付けされており
        fp=="FY"限定では原本自体が候補から除外されてしまう（本調査で確認済み）。

        form=="10-K/A"（訂正申告）も候補に含める（ARCH-DATA-1ステージ1）:
        10-K/Aで再提出された期間もreportDate==end_dateが成立すれば本人データ
        として扱う。ただし同一タグ内で元の10-Kとその10-K/Aが同一(fy, end_date)を
        報告する場合は下記のfiled日タイブレークで新しい方（通常は10-K/A）を採用する。

        同一fyキーに複数の本人end_dateが競合した場合（CRM/FCX/CAKE/HON/COHR/AVAV/
        FICO/NVDA等で実在確認済みの、filing代行者側のタグ付け起因と推測される矛盾）は
        まずdetermine_fiscal_year()フォールバックで両end_dateが自然に別の年度へ
        分離できないか確認する。分離できる場合（CRM/FCX等の固定月決算企業。
        fyタグだけが誤っており日付ベースの判定自体は曖昧でない）は、共有された
        誤ったfyタグを使わず各自のフォールバック年度をキーとして採用する
        （これを怠ると、fyタグの衝突が全く新しい真値喪失を引き起こす回帰と
        なることを確認済み——CRMの真のFY2025値がFY2026値に上書きされて消失した
        実例で発覚）。フォールバックでも分離できない場合（CAKE。52/53週の
        月またぎとfyタグ誤りが同一年度で重なるケース）のみ、end_dateが
        新しい方を優先するtie-breakを適用する。

        Returns:
            dict: {fy: (val, end_date, accn, filed, raw_fy_tag)}
        """
        # fy -> {end_date: {"val":..., "accn":..., "filed":..., "key":...}}
        # "key"は採用元のXBRLタグ名（xbrl_keysの優先順位を尊重するために保持する）
        by_fy: Dict[int, Dict[str, Dict[str, Any]]] = {}
        for key in xbrl_keys:
            if key not in us_gaap:
                continue
            units = us_gaap[key].get("units", {})
            for unit_type in ["USD", "shares", "USD/shares"]:
                if unit_type not in units:
                    continue
                for entry in units[unit_type]:
                    if entry.get("form") not in ("10-K", "10-K/A") or entry.get("fp") not in ("FY", "Q4"):
                        continue
                    fy = entry.get("fy")
                    val = entry.get("val")
                    end_date = entry.get("end", "")
                    start_date = entry.get("start", "")
                    accn = entry.get("accn")
                    filed = entry.get("filed", "")
                    if val is None or fy is None or not end_date or len(end_date) < 10:
                        continue
                    if not start_date or len(start_date) < 10:
                        continue
                    try:
                        days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
                    except ValueError:
                        continue
                    if not (340 <= days <= 380):
                        # 真の年次期間（約365日）以外は除外する。10-K内に選択四半期データ
                        # （例: JNJの90日間Q4内訳）が form=10-K・fp=FY で同一end_dateとして
                        # 混入し、reportDate一致だけでは年次実績と区別できないため
                        # （JNJ FY2011のQ4内訳$218Mが本人データと誤判定される問題への対応）
                        continue
                    if accn_reportdate.get(accn) != end_date:
                        continue  # 本人データではない（比較年度再掲・IPO前データ等）

                    # 同一(fy, end_date)に複数タグが該当する場合、xbrl_keysの優先順位
                    # （先勝ち）を尊重する。WMTはRevenues（総収益）とSalesRevenueNet
                    # （純売上高）を同一filingで併記しており、後から処理したタグで
                    # 無条件上書きすると優先順位の低いタグが勝ってしまう
                    # （WMT: Revenues $485,651M が優先されるべきところSalesRevenueNet
                    # $482,229M に上書きされる回帰を検出・修正）
                    fy_bucket = by_fy.setdefault(fy, {})
                    existing = fy_bucket.get(end_date)
                    if existing is None:
                        fy_bucket[end_date] = {"val": val, "accn": accn, "filed": filed, "key": key}
                    elif existing["key"] == key:
                        # 同一タグ内で同一(fy, end_date)が複数filingに登場する場合
                        # （元の10-Kとその10-K/A訂正申告等）はfiled日が新しい方を採用する
                        # （ARCH-DATA-1ステージ1: 値の確定）。異なるタグ間の優先順位
                        # （上記WMT対応）はここでは変更しない（先勝ちのまま）。
                        if filed and filed > existing.get("filed", ""):
                            fy_bucket[end_date] = {"val": val, "accn": accn, "filed": filed, "key": key}

        winners: Dict[int, tuple] = {}  # fy -> (val, end_date, accn, filed, raw_fy_tag)
        # raw_fy_tag はこのエントリ群が実際にXBRLで申告していたfyタグ（=外側ループのfy）を
        # そのまま保持する。placementキー（winnersの辞書キー）はフォールバック分離・
        # tie-breakの結果fyと異なる場合があるため、両者を区別してARCH-DATA-1ステージ3
        # （fyタグ裏取り）用に保持する。
        for fy, end_date_vals in by_fy.items():
            if len(end_date_vals) == 1:
                (end_date, info), = end_date_vals.items()
                winners[fy] = (info["val"], end_date, info["accn"], info["filed"], fy)
                continue

            # 同一fyキーに複数の異なる本人end_dateが競合
            fallback_years = {
                end_date: determine_fiscal_year(datetime.strptime(end_date, '%Y-%m-%d'), fiscal_end_month,
                                                 anchor_month, anchor_day)
                for end_date in end_date_vals
            }
            if len(set(fallback_years.values())) == len(end_date_vals):
                # フォールバックが自然に分離できる → 誤ったfyタグではなく
                # 各end_date自身のフォールバック年度をキーにする（CRM/FCX型）
                for end_date, info in end_date_vals.items():
                    winners[fallback_years[end_date]] = (info["val"], end_date, info["accn"], info["filed"], fy)
                if collisions_out is not None:
                    collisions_out.append({
                        "field": field_name, "fy": fy,
                        "end_dates": sorted(end_date_vals.keys()),
                        "resolution": "fyタグ衝突だがフォールバック年度で自然分離",
                    })
            else:
                # フォールバックも同一年度に衝突する（CAKE型・52/53週またぎと
                # fyタグ誤りが同一年度で重複）→ end_dateが新しい方を優先
                newest_end = max(end_date_vals.keys())
                newest_info = end_date_vals[newest_end]
                winners[fy] = (newest_info["val"], newest_end, newest_info["accn"], newest_info["filed"], fy)
                if collisions_out is not None:
                    collisions_out.append({
                        "field": field_name, "fy": fy,
                        "end_dates": sorted(end_date_vals.keys()),
                        "resolution": "end_date新しい方を採用(フォールバックも衝突)",
                    })

        return winners

    def _collect_own_data_instant(self, us_gaap: dict, xbrl_keys: List[str],
                                   accn_reportdate: Dict[str, str], fiscal_end_month: int, field_name: str,
                                   collisions_out: Optional[List[Dict[str, Any]]],
                                   anchor_month: Optional[int] = None, anchor_day: Optional[int] = None) -> Dict[int, Any]:
        """
        instant fact（BS項目・RPO残高等、単一時点のend_dateのみを持ちstart_dateを
        持たないXBRL概念）向けに、reportDate==end_dateが成立する「本人の当期データ」
        を判定する（ARCH-DATA-1残課題④）。

        _collect_own_data_annual()との違いはstart_date・期間長（340-380日）フィルタを
        持たない点のみ。instant factのXBRL instant contextには元々start属性が存在せず、
        _collect_own_data_annual()のstart_date必須フィルタ（duration fact向けに、
        10-K内に混入する90日間の四半期内訳等を除外する目的）はinstant factには
        意味を持たない（そもそも比較対象となる「期間長」自体が存在しない）ため、
        同フィルタを持たない別実装として複製する。

        fyタグ衝突時のフォールバック分離・end_date新しい方優先のtie-breakロジックは
        _collect_own_data_annual()と同一（詳細は同メソッドのdocstring参照）。

        Returns:
            dict: {fy: (val, end_date, accn, filed, raw_fy_tag)}
        """
        by_fy: Dict[int, Dict[str, Dict[str, Any]]] = {}
        for key in xbrl_keys:
            if key not in us_gaap:
                continue
            units = us_gaap[key].get("units", {})
            for unit_type in ["USD", "shares", "USD/shares"]:
                if unit_type not in units:
                    continue
                for entry in units[unit_type]:
                    if entry.get("form") not in ("10-K", "10-K/A") or entry.get("fp") not in ("FY", "Q4"):
                        continue
                    fy = entry.get("fy")
                    val = entry.get("val")
                    end_date = entry.get("end", "")
                    accn = entry.get("accn")
                    filed = entry.get("filed", "")
                    if val is None or fy is None or not end_date or len(end_date) < 10:
                        continue
                    if accn_reportdate.get(accn) != end_date:
                        continue  # 本人データではない（比較年度再掲・IPO前データ等）

                    # 同一(fy, end_date)に複数タグが該当する場合、xbrl_keysの優先順位
                    # （先勝ち）を尊重する（_collect_own_data_annual()と同じ方針）
                    fy_bucket = by_fy.setdefault(fy, {})
                    existing = fy_bucket.get(end_date)
                    if existing is None:
                        fy_bucket[end_date] = {"val": val, "accn": accn, "filed": filed, "key": key}
                    elif existing["key"] == key:
                        if filed and filed > existing.get("filed", ""):
                            fy_bucket[end_date] = {"val": val, "accn": accn, "filed": filed, "key": key}

        winners: Dict[int, tuple] = {}
        for fy, end_date_vals in by_fy.items():
            if len(end_date_vals) == 1:
                (end_date, info), = end_date_vals.items()
                winners[fy] = (info["val"], end_date, info["accn"], info["filed"], fy)
                continue

            # 同一fyキーに複数の異なる本人end_dateが競合
            fallback_years = {
                end_date: determine_fiscal_year(datetime.strptime(end_date, '%Y-%m-%d'), fiscal_end_month,
                                                 anchor_month, anchor_day)
                for end_date in end_date_vals
            }
            if len(set(fallback_years.values())) == len(end_date_vals):
                for end_date, info in end_date_vals.items():
                    winners[fallback_years[end_date]] = (info["val"], end_date, info["accn"], info["filed"], fy)
                if collisions_out is not None:
                    collisions_out.append({
                        "field": field_name, "fy": fy,
                        "end_dates": sorted(end_date_vals.keys()),
                        "resolution": "fyタグ衝突だがフォールバック年度で自然分離",
                    })
            else:
                newest_end = max(end_date_vals.keys())
                newest_info = end_date_vals[newest_end]
                winners[fy] = (newest_info["val"], newest_end, newest_info["accn"], newest_info["filed"], fy)
                if collisions_out is not None:
                    collisions_out.append({
                        "field": field_name, "fy": fy,
                        "end_dates": sorted(end_date_vals.keys()),
                        "resolution": "end_date新しい方を採用(フォールバックも衝突)",
                    })

        return winners

    def _collect_own_data(self, us_gaap: dict, xbrl_keys: List[str],
                           accn_reportdate: Dict[str, str], fiscal_end_month: int, field_name: str,
                           collisions_out: Optional[List[Dict[str, Any]]],
                           anchor_month: Optional[int] = None, anchor_day: Optional[int] = None) -> Dict[int, Any]:
        """duration fact / instant factに応じて_collect_own_data_annual/_instantへ振り分ける
        （ARCH-DATA-1残課題④）。呼び出し元（_extract_values_merged/_extract_values_best_candidate）
        は本メソッド経由で呼び出すことで、フィールド種別を意識せず本人データ判定を利用できる。
        """
        if field_name in self.INSTANT_FACT_FIELDS:
            return self._collect_own_data_instant(us_gaap, xbrl_keys, accn_reportdate, fiscal_end_month, field_name,
                                                    collisions_out, anchor_month, anchor_day)
        return self._collect_own_data_annual(us_gaap, xbrl_keys, accn_reportdate, fiscal_end_month, field_name,
                                              collisions_out, anchor_month, anchor_day)

    # FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: 真の境界衝突（決算期変更）とみなす
    # 最小の(月,日)循環距離。common/sec_data/fye_change_candidate_scan.py の
    # MIN_CLUSTER_DISTANCE_DAYSと同じ値を使い、判定基準を一致させる。
    _BOUNDARY_COLLISION_MIN_ANCHOR_DISTANCE_DAYS = 30

    @staticmethod
    def _fiscal_anchors_far_apart(end_date_a: str, end_date_b: str) -> bool:
        """
        2つのend_dateの(月,日)のみを比較し、暦年をまたぐ循環距離が
        _BOUNDARY_COLLISION_MIN_ANCHOR_DISTANCE_DAYSを超えるか判定する。

        「生fyタグが異なる・end_dateも異なる」だけでは不十分で、ADSK/AVAV/CRM/
        CAKE等の固定決算日企業では「同一の(月,日)・隣接する暦年」の組み合わせが
        頻出する（filer側のfyタグが実際の期間より1年ずれるWARN-23既知パターン。
        例: end=2011-01-31/fy=2010とend=2012-01-31/fy=2011が同一年度バケツで
        競合するが、これは決算期変更ではなく単なるfyタグの年ズレ）。
        本関数は(月,日)のみを見て「そもそも決算日そのものが動いたか」を判定し、
        同一の(月,日)（52/53週の前後変動込み）は除外する。
        """
        try:
            dt_a = datetime.strptime(end_date_a, "%Y-%m-%d")
            dt_b = datetime.strptime(end_date_b, "%Y-%m-%d")
        except ValueError:
            return False
        doy_a = _day_of_year(dt_a.month, dt_a.day)
        doy_b = _day_of_year(dt_b.month, dt_b.day)
        diff = abs(doy_a - doy_b)
        circular_dist = min(diff, 366 - diff)
        return circular_dist > SECParser._BOUNDARY_COLLISION_MIN_ANCHOR_DISTANCE_DAYS

    @classmethod
    def _is_boundary_collision(cls, existing_end: Optional[str], existing_fy_tag: Optional[int],
                                own_end: str, own_fy_tag: Optional[int]) -> bool:
        """
        FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: 既存（フォールバック採用済み）側と
        本人データ候補側が「真の境界衝突」（決算期変更、RCAT型）とみなせるかを
        判定する純関数。`_own_override_is_safe()`自体は変更せず、その呼び出し
        前後で退避した既存側の情報と組み合わせて使う（_extract_values_merged/
        _extract_values_best_candidate内の2箇所から呼び出される）。

        判定条件（すべて満たす場合のみTrue）:
        1. 既存側end_dateが存在する（フォールバックが実際に何かを採用済み）
        2. 既存側fyタグが存在し、本人データ側fyタグと異なる
        3. 既存側end_dateと本人データ側end_dateが異なる
        4. 2つのend_dateの(月,日)が_fiscal_anchors_far_apart()で「十分離れている」
           （ADSK/AVAV/CRM/CAKE等の「同一(月,日)・隣接暦年」パターン＝fyタグの
           年ズレ〈WARN-23既知〉を除外するため）
        """
        if existing_end is None or existing_fy_tag is None:
            return False
        if existing_fy_tag == own_fy_tag:
            return False
        if existing_end == own_end:
            return False
        return cls._fiscal_anchors_far_apart(existing_end, own_end)

    def _own_override_is_safe(self, year: int, own_end_date: str, fiscal_end_month: int,
                               annual_end_dates: Dict[int, str], annual_durations: Dict[int, Any],
                               annual_accn: Dict[int, str], accn_reportdate: Dict[str, str],
                               anchor_month: Optional[int] = None, anchor_day: Optional[int] = None,
                               is_instant: bool = False) -> bool:
        """
        本人データによる上書きが安全か判定する。

        フォールバック（determine_fiscal_year()ベースのtie-break）が既にこの年度キーに
        「別の真の年次期間として自己無矛盾な、正規の年次データ（340-380日）」を
        採用済みの場合は上書きしない。

        WMTの実例で発覚: WMTの真のFY2010データ（$408,214M、end=2010-01-31）が、
        WMT自身のfiling原本内でfy=2009と誤りタグ付けされている（比較年度再掲ではなく
        原本自体の誤り）。この1件だけを見るとDELLのFY2019パターン（本人データの
        fyタグがdetermine_fiscal_year()の計算結果と食い違う正当なケース）と区別が
        つかないが、上書き先のfy=2009キーには既に自己無矛盾な真のFY2009年次データ
        （$404,374M、end=2009-01-31、reportDateとの一致はないがdetermine_fiscal_year()
        computed_year==2009と自己整合）が存在しており、無条件上書きするとこの正しい
        データを破壊してしまう。DELLの場合、上書き前のfallback値は90日間スタブ
        （determine_fiscal_year()の計算結果がキーと一致しない）であり本チェックには
        引っかからず、正しく上書きされる。

        ARCH-DATA-1ステージ2（設計変更）: 旧実装は「月またぎ補正
        (end_date.month > fiscal_end_month による+1)なしで自己整合する場合のみ
        安全とみなす」事前フィルタ（no_crossing_needed = existing_end_dt.month
        <= fiscal_end_month）を持っていたが、これはdetermine_fiscal_year()本体
        と同じ「月のみ比較」欠陥を共有しており、12月決算企業では
        month<=12が恒常的にTrueとなり事前フィルタが機能しない欠陥があった
        （CDNS FY2015のtotal_assets/revenueがFY2014値のまま誤って保持され続ける
        実害を確認済み）。determine_fiscal_year()自体がアンカー日ウィンドウ方式
        に置き換わり、月境界をまたぐか否かに関わらず「end_dateに最も近いアンカー日
        候補年度」を正しく計算できるようになったため、事前フィルタ自体を廃止し、
        統一版determine_fiscal_year()の計算結果とyearの一致判定のみで安全性を
        判定する（IOT型の52/53週誤配置とWMT型の自己整合データの区別は
        アンカー日ウィンドウ方式が両方とも正しく解決するため、月またぎの有無で
        場合分けする必要がなくなった）。

        ARCH-DATA-1残課題④（instant fact対応、VZ型の発覚）: 「existing_end ==
        own_end_date → 同一期間なので上書き安全」という最初のショートカットは
        duration factでは「同一期間を指す2つの候補タグは同じ概念の別名表記
        （WMT Revenues/SalesRevenueNet等）である可能性が高い」という前提の下で
        成立するが、instant fact（BS項目）ではこの前提が成立しない。BS項目は
        同一会計年度内であれば異なるタグ（例: ShortTermBorrowings＝短期借入金と
        LongTermDebtCurrent＝長期債務の流動化部分）でもend_dateが機械的に一致
        するため、このショートカットが「別概念の値」を安全と誤判定してしまう
        （VZの実例: xbrl_keys優先順位1位のShortTermBorrowings本人データ$441M
        が、freshness選定で勝っていたLongTermDebtCurrent本人データ$18,618M
        〈同一end_date〉を誤って上書きし、Net Debtが約$18.6B過小評価される
        回帰を検出）。instant fact向け呼び出し（is_instant=True）ではこの
        ショートカットをスキップし、後続のaccnベースの判定（既に別の本人データ
        が採用済みか）のみで安全性を判定する。
        """
        existing_end = annual_end_dates.get(year)
        if existing_end is None:
            return True  # フォールバックに何もない → 上書きして問題ない
        if not is_instant and existing_end == own_end_date:
            return True  # 同一期間 → 実質的に同じ値のはず（duration factのみ。上記docstring参照）

        existing_accn = annual_accn.get(year)
        if existing_accn is not None and accn_reportdate.get(existing_accn) == existing_end:
            return False  # 既に別の本人データが採用済み → 上書きしない（タグ優先順位を尊重）

        existing_days = annual_durations.get(year)
        if existing_days is not None and 340 <= existing_days <= 380:
            try:
                existing_end_dt = datetime.strptime(existing_end, '%Y-%m-%d')
            except ValueError:
                return True
            if determine_fiscal_year(existing_end_dt, fiscal_end_month, anchor_month, anchor_day) == year:
                return False  # 既存エントリは別の真の年次データとして自己無矛盾に存在する

        return True

    def _extract_values_merged(self, us_gaap: dict, xbrl_keys: List[str], use_max: bool, fiscal_end_month: int,
                                accn_reportdate: Optional[Dict[str, str]] = None, field_name: str = "",
                                collisions_out: Optional[List[Dict[str, Any]]] = None,
                                anchor_month: Optional[int] = None, anchor_day: Optional[int] = None,
                                fy_mismatches_out: Optional[List[Dict[str, Any]]] = None,
                                boundary_collisions_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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
        # 採用accnを記録（本人データ上書き判定用。FY52WEEK-BUCKET-MISPLACE-1根本修正）
        annual_accn: Dict[int, str] = {}
        # 採用filed日・formを記録（ARCH-DATA-1ステージ1: 真に同一期間〈end_date一致〉の
        # 複数バージョンが競合し、かつ一方が10-K/A〈訂正申告〉である場合のみ、
        # filed日が新しい方を優先するタイブレークに使う）
        annual_filed: Dict[int, str] = {}
        annual_form: Dict[int, str] = {}
        # 採用エントリの生XBRL fyタグを記録（ARCH-DATA-1ステージ3: fyタグ裏取り用。
        # end_yearキー〈determine_fiscal_year()の計算結果〉と一致しない場合がある）
        annual_fy_tag: Dict[int, int] = {}

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
                    accn = entry.get("accn")
                    filed = entry.get("filed", "")

                    if val is None or fy is None:
                        continue

                    # 年次（10-K・10-K/A）- determine_fiscal_year で会計年度キーを統一定義に従って決定
                    # 10-K/A（訂正申告）も候補に含める（ARCH-DATA-1ステージ1）
                    if form in ("10-K", "10-K/A") and fp == "FY":
                        # determine_fiscal_year(期末日, fiscal_end_month) が単一定義
                        # fy==end_yearはFY通年データとして信頼度が高い（exact match）
                        # fy!=end_yearは比較年度エントリ（FCX等）または中間期エントリ（INTU Q1等）
                        if end_date and len(end_date) >= 10:
                            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                            end_year = determine_fiscal_year(end_dt, fiscal_end_month, anchor_month, anchor_day)
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
                                annual_accn[end_year] = accn
                                annual_filed[end_year] = filed
                                annual_form[end_year] = form
                                annual_fy_tag[end_year] = fy
                        else:
                            if end_year not in result["annual"]:
                                result["annual"][end_year] = val
                                annual_end_dates[end_year] = end_date
                                annual_exact_match[end_year] = exact
                                annual_durations[end_year] = days
                                annual_accn[end_year] = accn
                                annual_filed[end_year] = filed
                                annual_form[end_year] = form
                                annual_fy_tag[end_year] = fy
                            elif exact and not annual_exact_match.get(end_year, True):
                                # exact matchで上書き: 非December FY企業のQ1等中間期エントリ
                                # (fy=N+1, end_year=N) が全年データ(fy=N, end_year=N)を上書きするのを防ぐ
                                result["annual"][end_year] = val
                                annual_end_dates[end_year] = end_date
                                annual_exact_match[end_year] = True
                                annual_durations[end_year] = days
                                annual_accn[end_year] = accn
                                annual_filed[end_year] = filed
                                annual_form[end_year] = form
                                annual_fy_tag[end_year] = fy
                            elif exact == annual_exact_match.get(end_year, False):
                                stored_end = annual_end_dates.get(end_year, "")
                                if end_date > stored_end:
                                    # 同じexact_matchレベル: 最新のend_dateを優先
                                    result["annual"][end_year] = val
                                    annual_end_dates[end_year] = end_date
                                    annual_durations[end_year] = days
                                    annual_accn[end_year] = accn
                                    annual_filed[end_year] = filed
                                    annual_form[end_year] = form
                                    annual_fy_tag[end_year] = fy
                                elif end_date == stored_end and (form == "10-K/A" or annual_form.get(end_year) == "10-K/A"):
                                    # ARCH-DATA-1ステージ1: end_dateも同一＝真に同一期間の
                                    # 複数バージョンが競合。一方が10-K/A（訂正申告）の場合に
                                    # 限り、filed日が新しい方を優先する（「値の確定」の主軸）。
                                    # 10-K/Aが関与しない場合（通常の比較年度再掲同士の食い違い。
                                    # discontinued operations区分変更等で数字の意味自体が
                                    # 変わりうるため）は下記のSEC-TAG-FICO-CPRT-1タイブレーク
                                    # （期間日数365日近似）のみで判定する従来動作を変更しない。
                                    stored_filed = annual_filed.get(end_year, "")
                                    if filed and filed > stored_filed:
                                        result["annual"][end_year] = val
                                        annual_durations[end_year] = days
                                        annual_accn[end_year] = accn
                                        annual_filed[end_year] = filed
                                        annual_form[end_year] = form
                                        annual_fy_tag[end_year] = fy
                                    elif filed == stored_filed and days is not None:
                                        stored_days = annual_durations.get(end_year)
                                        if stored_days is None or abs(days - 365) < abs(stored_days - 365):
                                            result["annual"][end_year] = val
                                            annual_durations[end_year] = days
                                            annual_accn[end_year] = accn
                                            annual_fy_tag[end_year] = fy
                                elif end_date == stored_end and days is not None:
                                    # SEC-TAG-FICO-CPRT-1: end_dateも同一（10-K/A非関与）の
                                    # 場合、期間日数が365日（正規の年次期間）に近い方を優先する
                                    stored_days = annual_durations.get(end_year)
                                    if stored_days is None or abs(days - 365) < abs(stored_days - 365):
                                        result["annual"][end_year] = val
                                        annual_durations[end_year] = days
                                        annual_accn[end_year] = accn
                                        annual_fy_tag[end_year] = fy

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

        # 出所メタデータのサイドカー（ARCH-DATA-1ステージ1: 「値の確定」）。
        # フォールバック採用分をまず記録し、本人データ上書きが適用された年度は
        # 後段で上書きする。annual_provenance は _build_period_data が
        # {field}_provenance として消費し、既存の bs/pl/cf 等のスキーマは変更しない。
        annual_provenance: Dict[int, Dict[str, Any]] = {}
        for year, accn in annual_accn.items():
            if accn is None:
                continue
            annual_provenance[year] = {
                "accn": accn,
                "filed": annual_filed.get(year, ""),
                "is_own_data": accn_reportdate.get(accn) == annual_end_dates.get(year) if accn_reportdate else False,
                "fy_tag": annual_fy_tag.get(year),
            }

        # FY52WEEK-BUCKET-MISPLACE-1根本修正: フォールバック(上記のdetermine_fiscal_year()
        # ベースのtie-break)が「本人データではない」候補を採用してしまった年度キーのみを
        # 本人データで上書きする。フォールバックが既に本人データを採用済みの年度キーは
        # 一切変更しない（WMTのRevenues/SalesRevenueNet併記のような、複数タグが同時に
        # 本人データとして存在するケースで、xbrl_keysの優先順位に基づく既存のtie-break
        # 判断を上書きの副作用で覆してしまう回帰を防ぐため）。
        if accn_reportdate:
            own_data = self._collect_own_data(us_gaap, xbrl_keys, accn_reportdate, fiscal_end_month, field_name,
                                               collisions_out, anchor_month, anchor_day)
            for year, (val, own_end, own_accn, own_filed, own_fy_tag) in own_data.items():
                # FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: 上書き判定の前に既存
                # （フォールバック採用済み）側のend_date/fyタグを退避しておく。
                # _own_override_is_safe自体はannual_end_dates[year]を書き換えない
                # ため、判定結果に関わらずここで取得した値が「上書き前の既存側」を表す。
                _existing_end = annual_end_dates.get(year)
                _existing_fy_tag = annual_fy_tag.get(year)
                _existing_accn = annual_accn.get(year)
                _override_ok = self._own_override_is_safe(year, own_end, fiscal_end_month, annual_end_dates,
                                                            annual_durations, annual_accn, accn_reportdate,
                                                            anchor_month, anchor_day,
                                                            is_instant=field_name in self.INSTANT_FACT_FIELDS)
                if (boundary_collisions_out is not None
                        and self._is_boundary_collision(_existing_end, _existing_fy_tag, own_end, own_fy_tag)):
                    boundary_collisions_out.append({
                        "field": field_name, "year": year,
                        "own_data_side": {"fy_tag": own_fy_tag, "accn": own_accn, "end_date": own_end},
                        "other_side": {
                            "fy_tag": _existing_fy_tag, "accn": _existing_accn, "end_date": _existing_end,
                            "is_own_data": bool(_existing_accn and accn_reportdate.get(_existing_accn) == _existing_end),
                        },
                        "override_applied": _override_ok,
                    })
                if _override_ok:
                    result["annual"][year] = val
                    annual_end_dates[year] = own_end
                    annual_provenance[year] = {
                        "accn": own_accn, "filed": own_filed, "is_own_data": True,
                        "fy_tag": own_fy_tag,
                    }

        # ARCH-DATA-1ステージ3: fyタグ裏取り。年度バケツキー（determine_fiscal_year()の
        # 計算結果）と採用エントリの生fyタグが食い違う場合を記録する（呼び出し元
        # _parse_raw_data が全フィールド横断で集約し fy_tag_mismatch_log.json に保存）。
        # is_own_data=False（比較年度再掲エントリ等）は対象外とする: fyタグは
        #「その数値がどの10-Kに載っていたか」というfiling側の属性であり、比較年度
        # 再掲エントリでは「載っていた10-Kの年」と「数値が表す期間」が一致しないのが
        # 正常仕様（企業のfyタグ誤りとは無関係）。全105銘柄検証で4,434件・105銘柄
        # というノイズになることが判明したため、is_own_data=True（本人データ自身の
        # fyタグが実際に採用されてしまっているケース）のみを対象にする
        # （2026-07-17設計変更）。
        if fy_mismatches_out is not None:
            for year, prov in annual_provenance.items():
                if not prov.get("is_own_data"):
                    continue
                fy_tag = prov.get("fy_tag")
                if fy_tag is not None and fy_tag != year:
                    fy_mismatches_out.append({
                        "field": field_name,
                        "end_date": annual_end_dates.get(year, ""),
                        "fy_tag": fy_tag,
                        "computed_year": year,
                    })

        result["_annual_provenance"] = annual_provenance
        return result

    def _extract_values_best_candidate(self, us_gaap: dict, xbrl_keys: List[str], fiscal_end_month: int,
                                        accn_reportdate: Optional[Dict[str, str]] = None, field_name: str = "",
                                        collisions_out: Optional[List[Dict[str, Any]]] = None,
                                        anchor_month: Optional[int] = None, anchor_day: Optional[int] = None,
                                        fy_mismatches_out: Optional[List[Dict[str, Any]]] = None,
                                        boundary_collisions_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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
            key_result = self._extract_single_key(us_gaap, key, fiscal_end_month, anchor_month, anchor_day)
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
        result = candidates[best_idx][1]
        winning_end_dates = result.pop("_annual_end_dates", {})
        winning_accns = result.pop("_annual_accn", {})
        winning_durations = result.pop("_annual_durations", {})
        winning_filed = result.pop("_annual_filed", {})
        winning_fy_tags = result.pop("_annual_fy_tag", {})
        for _, key_result in candidates:
            key_result.pop("_annual_end_dates", None)
            key_result.pop("_annual_accn", None)
            key_result.pop("_annual_durations", None)
            key_result.pop("_annual_filed", None)
            key_result.pop("_annual_fy_tag", None)

        # 出所メタデータのサイドカー（ARCH-DATA-1ステージ1: 「値の確定」）。
        # 勝者タグのフォールバック採用分をまず記録し、本人データ上書きが
        # 適用された年度は後段で上書きする。
        annual_provenance: Dict[int, Dict[str, Any]] = {}
        for year, accn in winning_accns.items():
            if accn is None:
                continue
            annual_provenance[year] = {
                "accn": accn,
                "filed": winning_filed.get(year, ""),
                "is_own_data": accn_reportdate.get(accn) == winning_end_dates.get(year) if accn_reportdate else False,
                "fy_tag": winning_fy_tags.get(year),
            }

        # FY52WEEK-BUCKET-MISPLACE-1根本修正: フォールバックが「本人データではない」
        # 候補を採用してしまった年度キーのみを、本人データで上書きする
        # （選ばれたタグ単体に本人データが無い年度でも他の候補タグには存在する場合が
        # あるため、xbrl_keysの優先順位順に全タグを横断して本人データを収集する。
        # JNJのnet_income: NetIncomeLossタグに2011年の本人365日データが無く
        # ProfitLossタグには存在する、という実例で確認済み）。
        # フォールバックが既にそのタグ自身の本人データを採用済みの年度キー、または
        # 別の真の年次データとして自己無矛盾に存在する年度キーは変更しない
        # （WMT型の回帰防止。_own_override_is_safe参照）
        if accn_reportdate:
            combined_own_data: Dict[int, Any] = {}
            for key in xbrl_keys:
                if key not in us_gaap:
                    continue
                key_own_data = self._collect_own_data(us_gaap, [key], accn_reportdate, fiscal_end_month, field_name,
                                                       collisions_out, anchor_month, anchor_day)
                for fy, (val, end_date, own_accn, own_filed, own_fy_tag) in key_own_data.items():
                    if fy not in combined_own_data:
                        combined_own_data[fy] = (val, end_date, own_accn, own_filed, own_fy_tag)
            for year, (val, own_end, own_accn, own_filed, own_fy_tag) in combined_own_data.items():
                # FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: _extract_values_mergedと同一パターン
                _existing_end = winning_end_dates.get(year)
                _existing_fy_tag = winning_fy_tags.get(year)
                _existing_accn = winning_accns.get(year)
                _override_ok = self._own_override_is_safe(year, own_end, fiscal_end_month, winning_end_dates,
                                                            winning_durations, winning_accns, accn_reportdate,
                                                            anchor_month, anchor_day,
                                                            is_instant=field_name in self.INSTANT_FACT_FIELDS)
                if (boundary_collisions_out is not None
                        and self._is_boundary_collision(_existing_end, _existing_fy_tag, own_end, own_fy_tag)):
                    boundary_collisions_out.append({
                        "field": field_name, "year": year,
                        "own_data_side": {"fy_tag": own_fy_tag, "accn": own_accn, "end_date": own_end},
                        "other_side": {
                            "fy_tag": _existing_fy_tag, "accn": _existing_accn, "end_date": _existing_end,
                            "is_own_data": bool(_existing_accn and accn_reportdate.get(_existing_accn) == _existing_end),
                        },
                        "override_applied": _override_ok,
                    })
                if _override_ok:
                    result["annual"][year] = val
                    winning_end_dates[year] = own_end
                    annual_provenance[year] = {
                        "accn": own_accn, "filed": own_filed, "is_own_data": True,
                        "fy_tag": own_fy_tag,
                    }

        # ARCH-DATA-1ステージ3: fyタグ裏取り（_extract_values_mergedと同じロジック。
        # is_own_data=Falseの比較年度再掲エントリは対象外。詳細は_extract_values_merged
        # 側のコメント参照）
        if fy_mismatches_out is not None:
            for year, prov in annual_provenance.items():
                if not prov.get("is_own_data"):
                    continue
                fy_tag = prov.get("fy_tag")
                if fy_tag is not None and fy_tag != year:
                    fy_mismatches_out.append({
                        "field": field_name,
                        "end_date": winning_end_dates.get(year, ""),
                        "fy_tag": fy_tag,
                        "computed_year": year,
                    })

        result["_annual_provenance"] = annual_provenance
        return result

    def _extract_single_key(self, us_gaap: dict, key: str, fiscal_end_month: int,
                             anchor_month: Optional[int] = None, anchor_day: Optional[int] = None) -> Dict[str, Any]:
        """1つのXBRLキーからannual/quarterly値を抽出する（候補選定の評価単位）"""
        result: Dict[str, Any] = {"annual": {}, "quarterly": {}}
        annual_end_dates: Dict[int, str] = {}
        quarterly_end_dates: Dict[str, str] = {}
        annual_exact_match: Dict[int, bool] = {}
        annual_accn: Dict[int, str] = {}
        annual_durations: Dict[int, Any] = {}
        # 採用filed日・formを記録（ARCH-DATA-1ステージ1: 真に同一期間の複数バージョンが
        # 競合し、かつ一方が10-K/A〈訂正申告〉である場合のみ、filed日が新しい方を
        # 優先するタイブレークに使う）
        annual_filed: Dict[int, str] = {}
        annual_form: Dict[int, str] = {}
        # 採用エントリの生XBRL fyタグを記録（ARCH-DATA-1ステージ3: fyタグ裏取り用）
        annual_fy_tag: Dict[int, int] = {}

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
                accn = entry.get("accn")
                filed = entry.get("filed", "")

                if val is None or fy is None:
                    continue

                # 10-K/A（訂正申告）も候補に含める（ARCH-DATA-1ステージ1）
                if form in ("10-K", "10-K/A") and fp == "FY":
                    if end_date and len(end_date) >= 10:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        end_year = determine_fiscal_year(end_dt, fiscal_end_month, anchor_month, anchor_day)
                    else:
                        end_year = fy
                    exact = (fy == end_year)
                    start_date = entry.get("start", "")
                    days = None
                    if start_date and end_date and len(start_date) >= 10 and len(end_date) >= 10:
                        try:
                            days = (end_dt - datetime.strptime(start_date, '%Y-%m-%d')).days
                        except ValueError:
                            days = None
                    if end_year not in result["annual"]:
                        result["annual"][end_year] = val
                        annual_end_dates[end_year] = end_date
                        annual_exact_match[end_year] = exact
                        annual_accn[end_year] = accn
                        annual_durations[end_year] = days
                        annual_filed[end_year] = filed
                        annual_form[end_year] = form
                        annual_fy_tag[end_year] = fy
                    elif exact and not annual_exact_match.get(end_year, True):
                        result["annual"][end_year] = val
                        annual_end_dates[end_year] = end_date
                        annual_exact_match[end_year] = True
                        annual_accn[end_year] = accn
                        annual_durations[end_year] = days
                        annual_filed[end_year] = filed
                        annual_form[end_year] = form
                        annual_fy_tag[end_year] = fy
                    elif exact == annual_exact_match.get(end_year, False):
                        stored_end = annual_end_dates.get(end_year, "")
                        if end_date > stored_end:
                            result["annual"][end_year] = val
                            annual_end_dates[end_year] = end_date
                            annual_accn[end_year] = accn
                            annual_durations[end_year] = days
                            annual_filed[end_year] = filed
                            annual_form[end_year] = form
                            annual_fy_tag[end_year] = fy
                        elif end_date == stored_end and (form == "10-K/A" or annual_form.get(end_year) == "10-K/A"):
                            # ARCH-DATA-1ステージ1: end_dateも同一＝真に同一期間の
                            # 複数バージョンが競合。一方が10-K/A（訂正申告）の場合に限り、
                            # filed日が新しい方を優先する（「値の確定」の主軸）。
                            # 10-K/Aが関与しない場合（通常の比較年度再掲同士の食い違い。
                            # discontinued operations区分変更等で数字の意味自体が変わり
                            # うるため）は従来通り先勝ちのまま変更しない。
                            stored_filed = annual_filed.get(end_year, "")
                            if filed and filed > stored_filed:
                                result["annual"][end_year] = val
                                annual_accn[end_year] = accn
                                annual_durations[end_year] = days
                                annual_filed[end_year] = filed
                                annual_form[end_year] = form
                                annual_fy_tag[end_year] = fy
                            elif filed == stored_filed and days is not None:
                                stored_days = annual_durations.get(end_year)
                                if stored_days is None or abs(days - 365) < abs(stored_days - 365):
                                    result["annual"][end_year] = val
                                    annual_accn[end_year] = accn
                                    annual_fy_tag[end_year] = fy
                                    annual_durations[end_year] = days

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

        # 本人データの上書きは呼び出し元(_extract_values_best_candidate)で
        # タグ横断・優先順位順に一括適用する（このタグ単体では本人データが
        # 存在しない年度でも、他候補タグには存在する場合があるため。
        # JNJのnet_income: NetIncomeLossタグには2011年の本人365日データが
        # 存在しないが、ProfitLossタグには存在する、という実例で確認済み）。
        # フォールバックが既に本人データを採用済みかどうかの判定用に、
        # 採用end_date/accn/duration/filedを"_"接頭辞のメタ情報として同梱する
        result["_annual_end_dates"] = annual_end_dates
        result["_annual_accn"] = annual_accn
        result["_annual_durations"] = annual_durations
        result["_annual_filed"] = annual_filed
        result["_annual_fy_tag"] = annual_fy_tag
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

        # 出所メタデータのサイドカー（ARCH-DATA-1ステージ1: 「値の確定」）。
        # 既存の bs/pl/cf/shares/other スキーマ（フラットな{フィールド名: 値}）は
        # 変更せず、{セクション}_provenance という追加キーとしてのみ付与する
        # （既存消費者は未知キーを無視するため無改修で動作する）。
        # 年次データのみ対象（quarterly側は_annual_provenanceに該当エントリが
        # 存在しないため自然に空のまま）。
        provenance_sections: Dict[str, Dict[str, Any]] = {
            "bs": {}, "pl": {}, "cf": {}, "shares": {}, "other": {},
        }

        def _record(section: str, field: str, val: Any) -> None:
            if val is None:
                return
            data[section][field] = val
            if not is_annual:
                return
            prov = extracted.get(field, {}).get("_annual_provenance", {}).get(period)
            if prov:
                provenance_sections[section][field] = prov

        # BS
        for field in ["total_assets", "stockholders_equity", "total_liabilities",
                      "cash_and_equivalents", "short_term_investments",
                      "long_term_debt", "short_term_debt",
                      "current_assets", "current_liabilities"]:
            _record("bs", field, extracted.get(field, {}).get(period_type, {}).get(period))

        # PL
        for field in ["revenue", "gross_profit", "cost_of_revenue", "net_income", "eps_diluted", "eps_basic",
                      "research_and_development", "selling_and_marketing",
                      "selling_general_and_administrative", "operating_income"]:
            _record("pl", field, extracted.get(field, {}).get(period_type, {}).get(period))

        # CF
        for field in ["operating_cash_flow", "capital_expenditure", "finance_lease_payments",
                      "depreciation_and_amortization", "stock_based_compensation", "buyback"]:
            _record("cf", field, extracted.get(field, {}).get(period_type, {}).get(period))
        
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
            _record("shares", field, extracted.get(field, {}).get(period_type, {}).get(period))

        # Other (RPO等)
        for field in ["rpo"]:
            _record("other", field, extracted.get(field, {}).get(period_type, {}).get(period))

        # 出所メタデータのサイドカーを空でないセクションのみ付与する
        # （既存スキーマへの無用なサイズ増加・省略時の互換性維持のため）
        for section, prov in provenance_sections.items():
            if prov:
                data[f"{section}_provenance"] = prov

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

    def _save_fy_collision_log(self, ticker: str, collisions: List[Dict[str, Any]]) -> None:
        """
        本人データ同士のfyキー衝突（CRM/FCX/CAKE/HON/COHR/AVAV/FICO/NVDA等で
        実在確認済み。filing代行者側のタグ付け起因と推測されるが原因追及は対象外）を
        report_consistency_check.pyから参照できる形で記録する。
        """
        ticker_dir = os.path.join(self.data_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        path = os.path.join(ticker_dir, "fy_collision_log.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ticker": ticker, "collisions": collisions}, f, ensure_ascii=False, indent=2)
        if collisions:
            print(f"   [{ticker}] fyキー競合を検知・記録: {len(collisions)}件 ({path})")

    def _save_fy_tag_mismatch_log(self, ticker: str, mismatches: List[Dict[str, Any]]) -> None:
        """
        ARCH-DATA-1ステージ3（fyタグ裏取り）: 年度バケツキー（determine_fiscal_year()の
        計算結果）と採用エントリの生XBRL fyタグが食い違うケースを
        report_consistency_check.pyから参照できる形で記録する。
        CHECK-22（fy_collision_log.json、同一fyタグへの複数本人end_date競合を検知）
        とは独立した別軸のチェックであり、こちらは「fyタグは単一だが値の年度
        バケツ配置自体がfyタグと異なる」ケース（CDNS型）を対象とする。
        自動修正は行わない（WARN出力のみ）。
        """
        ticker_dir = os.path.join(self.data_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        path = os.path.join(ticker_dir, "fy_tag_mismatch_log.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ticker": ticker, "mismatches": mismatches}, f, ensure_ascii=False, indent=2)
        if mismatches:
            print(f"   [{ticker}] fyタグ裏取り不一致を検知・記録: {len(mismatches)}件 ({path})")

    def _save_fye_boundary_collision_log(self, ticker: str, collisions: List[Dict[str, Any]]) -> None:
        """
        FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: 決算期変更の境界年で「本人データ」
        （is_own_data判定を通過したエントリ）と、翌年10-Kの比較年度再掲データ等
        「生fyタグが異なる別のエントリ」が同一年度バケツ（computed_year）で競合した
        ケースを記録する。CHECK-22（fy_collision_log.json、同一fyタグへの複数
        本人end_date競合）・CHECK-23（fy_tag_mismatch_log.json、勝者自身の
        fyタグと年度バケツの不一致）のいずれとも異なる軸: 本件は競合する2エントリの
        生fyタグが元々異なるため（例: RCAT、本人データ側fy=2024・非本人データ側
        fy=2025）、CHECK-22（同一fyタグ前提）・CHECK-23（勝者自身のfyタグと
        バケツの不一致が対象、敗者側は対象外）のいずれの検知条件にも該当しない。

        `_own_override_is_safe()`自体は変更せず、その呼び出し前後で既存
        （フォールバック採用済み）側と本人データ候補側の生fyタグを比較する形で
        検知する（詳細は_extract_values_merged/_extract_values_best_candidate
        内のboundary_collisions_out追記箇所参照）。自動修正は行わない
        （WARN出力のみ）。0件でも毎回書き込む（fy_collision_log/
        fy_tag_mismatch_logと同じ化石ファイル対策）。
        """
        ticker_dir = os.path.join(self.data_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        path = os.path.join(ticker_dir, "fye_boundary_collision_log.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ticker": ticker, "collisions": collisions}, f, ensure_ascii=False, indent=2)
        if collisions:
            print(f"   [{ticker}] 決算期変更境界の年度バケツ競合を検知・記録: {len(collisions)}件 ({path})")

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
