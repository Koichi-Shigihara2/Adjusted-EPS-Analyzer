"""
common/sec_data/tag_definitions.py
XBRLタグ候補の共通定義（LLY-CAPEX-STALE-1 Phase 2a・QUALITY-GATES-EPIC-1）

quarterly.py（四半期/TTM側）とparser.py（年次側）が独立にタグ候補リストを
管理しており、片方だけタグを追加すると四半期/年次で扱いが食い違う問題が
LLYのCapExで発生した（旧タグ PaymentsToAcquireProductiveAssets が2022年
Q3以降申告停止、新タグ PaymentsToAcquireOtherPropertyPlantAndEquipment への
切替が quarterly.py 側にしか（それも件数不足時のみ）反映されず、parser.py
側は新タグを一度も試行していなかった）。

このモジュールは、quarterly.py と parser.py 双方のタグ候補リストのうち
「優先順位・候補集合が完全に一致している」または「一方が他方の厳密な
上位集合になっている」フィールドのみを集約する。統合しても既存の
意図的な設計判断を壊さないフィールドに限定している。

【NET_INCOME拡張（EPS-ANALYZER-NORMALIZE-SCOPE-1、2026-07-20）】
src/value/adjusted_eps_analyzer/extract_key_facts.pyが独自に保持していた
NET_INCOME_ANNUAL_TAGS/NET_INCOME_QUARTERLY_TAGS（6タグ）をこのTAG_CANDIDATES
["NET_INCOME"]に統合した。既存3タグ（parser.py/quarterly.py実績検証済み、
順序変更なし）の末尾にEPS Analyzer固有の3タグを追加する方式を採用（全101銘柄
シミュレーションで既存3タグの選定結果より新しいデータを持つ銘柄は0件と確認済み
のため、parser.py/quarterly.py側の挙動への影響はない）。extract_key_facts.py
が内部に持っていた第3の候補リスト（net_income_priority、四半期後段で無条件
上書きする別優先順位）は本タグ集合と矛盾していたため削除し、単一の選定ロジック
（このTAG_CANDIDATES参照＋既存の「最新データを持つタグを採用」アルゴリズム）
に統一した。

【意図的に統合していないフィールド】（優先順位や候補集合が構造的に異なり、
無条件でのマージは既存の修正済みバグ・設計判断を壊すリスクがあるため。
詳細は BACKLOG.md [TAG-DEFS-UNIFY-1] 参照）:
- LTDebt/long_term_debt: 優先タグの順序が quarterly.py と parser.py で逆
  （parser.py は BUG-NETDEBT-2 対策で LongTermDebtNoncurrent を意図的に最優先）
- SM/selling_and_marketing: quarterly.py は SGA 全体への最終フォールバックを
  持つが、parser.py は SGA を sga_gap_warning 専用に意図的に分離している
- DA/depreciation_and_amortization: primary タグの優先順序が逆かつ
  parser.py は merge_all_tags、quarterly.py は単一タグのみで挙動が根本的に異なる
- RPO/rpo: current/noncurrent 区分が異なるタグが混在しており単純な合算は
  概念的に不正確になりうる
- Revenue/revenue: ティッカー別 revenue_concept オーバーライドと
  merge_all_tags の相互作用が複雑なため対象外
"""

TAG_CANDIDATES: dict[str, tuple[str, ...]] = {
    "CAPITAL_EXPENDITURE": (
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",       # NVDA等: 広義CapEx
        "PaymentsForCapitalImprovements",
        # LLY: 2023年以降の新タグ（LLY-CAPEX-STALE-1・旧タグは2022-09-30で申告停止）
        "PaymentsToAcquireOtherPropertyPlantAndEquipment",
    ),
    "FINANCE_LEASE_PAYMENTS": (
        "FinanceLeasePrincipalPayments",
        "PaymentsForFinanceLeases",
        "RepaymentsOfLongTermCapitalLeaseObligations",
    ),
    "STOCK_BASED_COMPENSATION": (
        "ShareBasedCompensation",
        "AllocatedShareBasedCompensationExpense",  # CEG等
    ),
    "GROSS_PROFIT": (
        "GrossProfit",
        "GrossProfitLoss",
    ),
    "NET_INCOME": (
        "NetIncomeLoss",
        "ProfitLoss",                                        # AVGO等
        "NetIncomeLossAvailableToCommonStockholdersBasic",    # BKNG/AVAV等
        # EPS-ANALYZER-NORMALIZE-SCOPE-1（2026-07-20）: 以下3タグは
        # extract_key_facts.py固有だった候補。既存3タグの順序は変えず末尾に追加
        "NetIncomeLossAvailableToCommonStockholders",
        "NetIncomeLossAttributableToParent",
        "IncomeLossFromContinuingOperations",
    ),
    "CASH_AND_EQUIVALENTS": (
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",  # RCAT等
        "Cash",
        # [[CASH-TAG-MISSING-1]]対応（2026-08-30）: ASU 2016-18（制限付き
        # 現金を含むキャッシュフロー期首・期末残高調整表示義務化）対応後に
        # 移行した企業向け。GEV・SITM等、上記3タグのいずれも報告していない
        # 銘柄のcash_and_equivalentsが完全欠落していたことを解消する。
        # 「制限付き現金」を含む定義のため、純粋な現金同等物より広い概念
        # である点に注意。CPRT・HEIは上記CashAndCashEquivalentsAtCarrying
        # Valueが引き続き機能しているにもかかわらず、このタグの方が
        # 直近年度まで新しく報告されているため
        # _extract_values_best_candidate()の「最新annual年が新しい候補が
        # 全期間の採用タグになる」設計により、機能していた期間まで
        # 過大計上（制限付き現金の混入）に置き換わってしまうリスクを
        # 全105銘柄シミュレーションで確認した。両銘柄はquarterly.py::
        # TICKER_RESTRICTIONSのcash_concept上書きで明示的に既存タグへ
        # 固定し、このリスクを回避している。
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ),
    "RESEARCH_AND_DEVELOPMENT": (
        # [[JNJ-RD-TAG-PRIORITY-1]]対応: ExcludingAcquiredInProcessCostを
        # ResearchAndDevelopmentExpenseより優先する。JNJは両タグを2023年以降
        # 並存報告しており、後者はキャッシュフロー計算書の非資金調整項目
        # 「Charge for purchase of in-process research and development assets」
        # （M&A時のIPR&D即時費用化、通常のR&D活動とは無関係の一時的項目）を指す
        # ため、損益計算書本体の主要R&D科目である前者を優先する必要がある
        # （10-K原本R5.htm/R10.htm、FY2023-2025の3期で確認済み）。
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        "ResearchAndDevelopmentExpense",
        "CapitalizedComputerSoftwareDevelopmentCosts",
        "CapitalizedComputerSoftwareAmortization1",  # UNH等
    ),
    "BUYBACK": (
        "PaymentsForRepurchaseOfCommonStock",
    ),
    "OPERATING_CASH_FLOW": (
        "NetCashProvidedByUsedInOperatingActivities",
    ),
}
