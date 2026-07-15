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
from .fetcher import load_submissions


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

        # 会計年度末月を検出（非12月決算企業対応・determine_fiscal_year に渡す。
        # 本人データが存在しない年度のフォールバック判定にのみ使用する）
        fiscal_end_month = self._detect_fiscal_end_month(us_gaap)

        # FY52WEEK-BUCKET-MISPLACE-1 根本修正: reportDate==end_dateが成立する
        # 「本人の当期データ」のfyタグを年度キーとしてそのまま採用する。
        # accn_reportdateが空（submissions.json未取得）の場合は全件フォールバックのみで動作する。
        _accn_reportdate = accn_reportdate or {}
        _fy_collisions: List[Dict[str, Any]] = []

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
            extracted[field_name] = self._extract_values(
                us_gaap, xbrl_keys, use_max=use_max, merge_all_tags=merge_all,
                fiscal_end_month=fiscal_end_month, accn_reportdate=_accn_reportdate,
                field_name=field_name, collisions_out=_fy_collisions,
            )

        # 衝突0件でも毎回書き込む（IOT/AVGO/MRVLの化石ファイル問題の再発防止。
        # 一度検知された衝突が後日解消された場合に古いログが残り続けることを防ぐ）
        self._save_fy_collision_log(ticker, _fy_collisions)

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
                         field_name: str = "", collisions_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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

        Returns:
            dict: {
                "annual": {2024: value, 2023: value, ...},
                "quarterly": {"2024Q1": value, ...}
            }
        """
        if use_max or merge_all_tags:
            return self._extract_values_merged(us_gaap, xbrl_keys, use_max, fiscal_end_month,
                                                accn_reportdate=accn_reportdate, field_name=field_name,
                                                collisions_out=collisions_out)
        return self._extract_values_best_candidate(us_gaap, xbrl_keys, fiscal_end_month,
                                                    accn_reportdate=accn_reportdate, field_name=field_name,
                                                    collisions_out=collisions_out)

    def _collect_own_data_annual(self, us_gaap: dict, xbrl_keys: List[str],
                                  accn_reportdate: Dict[str, str], fiscal_end_month: int, field_name: str,
                                  collisions_out: Optional[List[Dict[str, Any]]]) -> Dict[int, Any]:
        """
        reportDate==end_dateが成立する「本人の当期データ」のみを対象に、
        fyタグを年度キーとして採用した値マップを構築する
        （FY52WEEK-BUCKET-MISPLACE-1根本修正: determine_fiscal_year()の月のみ判定を
        経由せず、企業自身が申告したfyタグを信頼する）。

        fp=="Q4"も候補に含める: DELLの真のFY2019 10-K原本はfp="Q4"でタグ付けされており
        fp=="FY"限定では原本自体が候補から除外されてしまう（本調査で確認済み）。

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
            dict: {fy: (val, end_date)}
        """
        # fy -> {end_date: val}
        by_fy: Dict[int, Dict[str, Any]] = {}
        for key in xbrl_keys:
            if key not in us_gaap:
                continue
            units = us_gaap[key].get("units", {})
            for unit_type in ["USD", "shares", "USD/shares"]:
                if unit_type not in units:
                    continue
                for entry in units[unit_type]:
                    if entry.get("form") != "10-K" or entry.get("fp") not in ("FY", "Q4"):
                        continue
                    fy = entry.get("fy")
                    val = entry.get("val")
                    end_date = entry.get("end", "")
                    start_date = entry.get("start", "")
                    accn = entry.get("accn")
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
                    if end_date not in fy_bucket:
                        fy_bucket[end_date] = val

        winners: Dict[int, tuple] = {}  # fy -> (val, end_date)
        for fy, end_date_vals in by_fy.items():
            if len(end_date_vals) == 1:
                (end_date, val), = end_date_vals.items()
                winners[fy] = (val, end_date)
                continue

            # 同一fyキーに複数の異なる本人end_dateが競合
            fallback_years = {
                end_date: determine_fiscal_year(datetime.strptime(end_date, '%Y-%m-%d'), fiscal_end_month)
                for end_date in end_date_vals
            }
            if len(set(fallback_years.values())) == len(end_date_vals):
                # フォールバックが自然に分離できる → 誤ったfyタグではなく
                # 各end_date自身のフォールバック年度をキーにする（CRM/FCX型）
                for end_date, val in end_date_vals.items():
                    winners[fallback_years[end_date]] = (val, end_date)
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
                winners[fy] = (end_date_vals[newest_end], newest_end)
                if collisions_out is not None:
                    collisions_out.append({
                        "field": field_name, "fy": fy,
                        "end_dates": sorted(end_date_vals.keys()),
                        "resolution": "end_date新しい方を採用(フォールバックも衝突)",
                    })

        return winners

    def _own_override_is_safe(self, year: int, own_end_date: str, fiscal_end_month: int,
                               annual_end_dates: Dict[int, str], annual_durations: Dict[int, Any],
                               annual_accn: Dict[int, str], accn_reportdate: Dict[str, str]) -> bool:
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

        重要な追加条件（IOTで発覚した誤検知の修正）: 既存エントリが「月またぎ補正
        (end_date.month > fiscal_end_month による+1)」を経てこのキーに到達している
        場合は、自己整合していても信頼しない。IOTの真のFY2024（end=2024-02-03）は
        fallback計算で月またぎ補正により自己整合的にbucket 2025へ到達するが、これは
        まさに本修正が正そうとしている52/53週バグそのものであり、WMT型の
        「月またぎ無しで自己整合するデータ」とは区別する必要がある。月またぎ補正
        なし（end_date.month <= fiscal_end_month）で自己整合する場合のみ、
        52/53週の影響を受けない安定した配置とみなして上書きをブロックする。
        """
        existing_end = annual_end_dates.get(year)
        if existing_end is None:
            return True  # フォールバックに何もない → 上書きして問題ない
        if existing_end == own_end_date:
            return True  # 同一期間 → 実質的に同じ値のはず

        existing_accn = annual_accn.get(year)
        if existing_accn is not None and accn_reportdate.get(existing_accn) == existing_end:
            return False  # 既に別の本人データが採用済み → 上書きしない（タグ優先順位を尊重）

        existing_days = annual_durations.get(year)
        if existing_days is not None and 340 <= existing_days <= 380:
            try:
                existing_end_dt = datetime.strptime(existing_end, '%Y-%m-%d')
            except ValueError:
                return True
            no_crossing_needed = existing_end_dt.month <= fiscal_end_month
            if no_crossing_needed and determine_fiscal_year(existing_end_dt, fiscal_end_month) == year:
                return False  # 既存エントリは別の真の年次データとして自己無矛盾に存在する

        return True

    def _extract_values_merged(self, us_gaap: dict, xbrl_keys: List[str], use_max: bool, fiscal_end_month: int,
                                accn_reportdate: Optional[Dict[str, str]] = None, field_name: str = "",
                                collisions_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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
                                annual_accn[end_year] = accn
                        else:
                            if end_year not in result["annual"]:
                                result["annual"][end_year] = val
                                annual_end_dates[end_year] = end_date
                                annual_exact_match[end_year] = exact
                                annual_durations[end_year] = days
                                annual_accn[end_year] = accn
                            elif exact and not annual_exact_match.get(end_year, True):
                                # exact matchで上書き: 非December FY企業のQ1等中間期エントリ
                                # (fy=N+1, end_year=N) が全年データ(fy=N, end_year=N)を上書きするのを防ぐ
                                result["annual"][end_year] = val
                                annual_end_dates[end_year] = end_date
                                annual_exact_match[end_year] = True
                                annual_durations[end_year] = days
                                annual_accn[end_year] = accn
                            elif exact == annual_exact_match.get(end_year, False):
                                stored_end = annual_end_dates.get(end_year, "")
                                if end_date > stored_end:
                                    # 同じexact_matchレベル: 最新のend_dateを優先
                                    result["annual"][end_year] = val
                                    annual_end_dates[end_year] = end_date
                                    annual_durations[end_year] = days
                                    annual_accn[end_year] = accn
                                elif end_date == stored_end and days is not None:
                                    # SEC-TAG-FICO-CPRT-1: end_dateも同一の場合、
                                    # 期間日数が365日（正規の年次期間）に近い方を優先する
                                    stored_days = annual_durations.get(end_year)
                                    if stored_days is None or abs(days - 365) < abs(stored_days - 365):
                                        result["annual"][end_year] = val
                                        annual_durations[end_year] = days
                                        annual_accn[end_year] = accn

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

        # FY52WEEK-BUCKET-MISPLACE-1根本修正: フォールバック(上記のdetermine_fiscal_year()
        # ベースのtie-break)が「本人データではない」候補を採用してしまった年度キーのみを
        # 本人データで上書きする。フォールバックが既に本人データを採用済みの年度キーは
        # 一切変更しない（WMTのRevenues/SalesRevenueNet併記のような、複数タグが同時に
        # 本人データとして存在するケースで、xbrl_keysの優先順位に基づく既存のtie-break
        # 判断を上書きの副作用で覆してしまう回帰を防ぐため）。
        if accn_reportdate:
            own_data = self._collect_own_data_annual(us_gaap, xbrl_keys, accn_reportdate, fiscal_end_month, field_name, collisions_out)
            for year, (val, own_end) in own_data.items():
                if self._own_override_is_safe(year, own_end, fiscal_end_month, annual_end_dates,
                                               annual_durations, annual_accn, accn_reportdate):
                    result["annual"][year] = val

        return result

    def _extract_values_best_candidate(self, us_gaap: dict, xbrl_keys: List[str], fiscal_end_month: int,
                                        accn_reportdate: Optional[Dict[str, str]] = None, field_name: str = "",
                                        collisions_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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
        result = candidates[best_idx][1]
        winning_end_dates = result.pop("_annual_end_dates", {})
        winning_accns = result.pop("_annual_accn", {})
        winning_durations = result.pop("_annual_durations", {})
        for _, key_result in candidates:
            key_result.pop("_annual_end_dates", None)
            key_result.pop("_annual_accn", None)
            key_result.pop("_annual_durations", None)

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
                key_own_data = self._collect_own_data_annual(us_gaap, [key], accn_reportdate, fiscal_end_month, field_name, collisions_out)
                for fy, (val, end_date) in key_own_data.items():
                    if fy not in combined_own_data:
                        combined_own_data[fy] = (val, end_date)
            for year, (val, own_end) in combined_own_data.items():
                if self._own_override_is_safe(year, own_end, fiscal_end_month, winning_end_dates,
                                               winning_durations, winning_accns, accn_reportdate):
                    result["annual"][year] = val

        return result

    def _extract_single_key(self, us_gaap: dict, key: str, fiscal_end_month: int) -> Dict[str, Any]:
        """1つのXBRLキーからannual/quarterly値を抽出する（候補選定の評価単位）"""
        result: Dict[str, Any] = {"annual": {}, "quarterly": {}}
        annual_end_dates: Dict[int, str] = {}
        quarterly_end_dates: Dict[str, str] = {}
        annual_exact_match: Dict[int, bool] = {}
        annual_accn: Dict[int, str] = {}
        annual_durations: Dict[int, Any] = {}

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

                if val is None or fy is None:
                    continue

                if form == "10-K" and fp == "FY":
                    if end_date and len(end_date) >= 10:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        end_year = determine_fiscal_year(end_dt, fiscal_end_month)
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
                    elif exact and not annual_exact_match.get(end_year, True):
                        result["annual"][end_year] = val
                        annual_end_dates[end_year] = end_date
                        annual_exact_match[end_year] = True
                        annual_accn[end_year] = accn
                        annual_durations[end_year] = days
                    elif exact == annual_exact_match.get(end_year, False):
                        if end_date > annual_end_dates.get(end_year, ""):
                            result["annual"][end_year] = val
                            annual_end_dates[end_year] = end_date
                            annual_accn[end_year] = accn
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
        # 採用end_date/accn/durationを"_"接頭辞のメタ情報として同梱する
        result["_annual_end_dates"] = annual_end_dates
        result["_annual_accn"] = annual_accn
        result["_annual_durations"] = annual_durations
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
