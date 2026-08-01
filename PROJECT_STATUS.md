# PROJECT_STATUS.md — 新一次データベース構築プロジェクト進捗

作成日: 2026-07-23
更新日: 2026-08-02（セッション終了処理。2026-08-01〜02セッション全体
〈gross_profit調査発端の一連の作業〉のサマリを反映。

**完了・クローズ項目**: `[[PERIOD-LENGTH-VALIDATION-GAP-1]]`・
`[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]`・`[[SPAC-STUB-PERIOD-
FIELD-SPLIT-1]]`・`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`段階1・段階2
（完了）・`[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]`①・
`[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]`（実害解消済み、
コード整理は将来検討）・`[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]`
（`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`へ統合）・
`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`（貸借対照表恒等式
逆算によるtotal_liabilitiesバックフィルを実装、278件是正・全105銘柄
フローズン入力比較で対象外無変化を確認）・`[[RCAT-TRIPLE-FISCAL-
CHANGE-SUSPECTED-1]]`（解消・実害なし、3段階目の決算期変更は存在せず）・
`[[SPAC-STUB-PERIOD-VERIFICATION-1]]`（解消・11銘柄すべて現状の処理が
妥当と確認）・`[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]`
一部（MO/PM/SCCOの3銘柄をgenuine定義差と確定・クローズ）。

**新規発見・残存タスク（次セッションでの着手順序、優先度順）**:
①`[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`〈中〜高、revenue/cost_of_
revenue/gross_profitが異なるaccn・会計年度から独立採用される設計欠陥。
CRM/JNJ/MRVLで確定、残り6銘柄〈AMD/BSY/KO/LRCX/ONDS/RMBS〉は要個別確認〉
②`[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]`〈中、fetcher.pyのrelevant_
formsに10-KT・10-QTが含まれず本人データが採用されない。現在進行形の実害は
解消済みだが将来の再発リスクとして監視対象〉③`[[RCAT-OCF-CONTINUING-
DISCONTINUED-SPLIT-1]]`〈中、RCATのoperating_cash_flow欠落〉
④`[[LITE-COGS-DA-TAG-UNMERGED-1]]`〈低〜中、LITEのCOGS由来償却費タグ
未合算〉⑤`[[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]`〈低〉
⑥`[[ELF-ROE10YR-RECALC-PENDING-1]]`〈中、TANUKI VALUATION定期更新で
自然解消見込み〉⑦`[[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-
MISSING-1]]`〈低〜中〉⑧`[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-
DUP-1]]〈低、クローズ済み・コード整理のみ将来検討〉。

詳細はBACKLOG.md/BACKLOG_DONE.md該当項目参照）

更新日: 2026-08-02（セッション後半。`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`
段階2〈formerNames区間一致によるSPAC合併疑いの機械的検知〉が完了し、
同エントリはBACKLOG_DONE.mdへ全文移動（段階1・段階2とも完了）。副産物
として新規登録した`[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]`
〈KULR(2019)単独〉は、根本原因調査（読み取りのみ）で
`XBRL_MAPPING["total_liabilities"]`の2番目のフォールバック候補
`LiabilitiesAndStockholdersEquity`〈定義上`total_assets`と数学的に一致する
誤った代替タグ〉が原因と確定。予備スキャンで105銘柄中278件（銘柄年度、
AMZN・GOOGL・MSFT・NVDA等の大型株を含む）に及ぶ横断的な候補タグ設計欠陥と
判明したため、KULR単独対応は不要と判断してクローズし、規模の大きい横断課題
`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`〈優先度：高、対応方針
未定・実装未着手〉として新規登録・統合した。downstream影響調査により
Net_Debt/Total_Debt算出への直接汚染はないことを確認済み（診断WARN
メッセージでの消費のみ）。詳細はBACKLOG.md/BACKLOG_DONE.md該当項目参照）

更新日: 2026-08-02（2026-08-01〜02セッションで`common/sec_data/`統合
フェーズ1の一次データ抽出品質に関わる残課題6件が解消。①`[[PERIOD-
LENGTH-VALIDATION-GAP-1]]`〈parser.pyのFLOW型フィールド抽出に期間長検証
340-380日を追加、9銘柄のgross_profit等の四半期→年次誤採用を是正〉、
②`[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]`〈era別fiscal_end_month/
anchor対応、ELFの2015-2018年度データを是正〉、③`[[SPAC-STUB-PERIOD-
FIELD-SPLIT-1]]`〈BBAI/RDW/ELF/KULRのSPAC・predecessor/successor期間
混在を個別調査、対応不要と確認〉、④`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`
段階1〈BS instant factの法的実体混在によるcurrent_assets>total_assets
等の数学的矛盾を7銘柄7年度で解消。段階2〈SPAC合併疑いの機械的検知〉は
未着手で残存〉、⑤`[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]`①
〈gross_profitのrevenue-cost_of_revenue逆算フォールバックを本番
annual_YYYY.jsonへ実装、34銘柄342件を書き戻し〉、⑥`[[STONKS-SILO-
FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]`〈⑤の効果でSTONKS SILO側の重複
補完ロジックが実質デッドコード化、クローズ〉が完了。新規発見の残存事項:
`[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]`〈KULR(2019)、同一filing内
でのcandidate tag誤選択、entity混在ではない別原因と確定〉・
`[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]`〈14銘柄49件へ
対象拡大、会計上の定義差または未解消バグの疑い〉・
`[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]`〈RCAT直近10-Kの決算期変更
再発疑い〉・`[[ELF-ROE10YR-RECALC-PENDING-1]]`〈TANUKI VALUATION定期
更新待ち〉。詳細はBACKLOG.md/BACKLOG_DONE.md該当項目参照）

更新日（2026-07-24分、履歴として保持）: 一次データベース設計の投資調査で
判明した3件の実態を反映。①INPUT-A-016〈セグメント別売上・KPI〉を正式
ASC280セグメントから`tail_kpi_map.json`ベースの銘柄固有カスタムKPI
〈フェーズ1統合スコープ外〉に訂正、②Adjusted EPS算出専用の税務・一過性
項目タグ群52種を`INPUT-A-048`として新規追加、③`common/sec_data/data/
{TICKER}/company_facts.json`〈SEC EDGAR company_facts API生レスポンス
全量、既存〉がLayer1（無加工アーカイブ）の要件を既に満たしていることが
判明し、新規構築不要と判明。分類A件数を47件→48件に更新。詳細は
`INPUT_DATA_TOBE.md`該当箇所・BACKLOG.md
`[[SECDATA-COMPANYFACTS-OVERLOOKED-1]]`参照）
位置づけ: 「新一次データベース構築プロジェクト」（2段階プロジェクトの
第1段階＝一次データ層の構築・過去データ移管、第2段階＝導出データ層
〈`FIELD_DEFINITIONS.md`499項目〉の管理方法検討）の進捗を追跡する。
仕様書本体は`docs/architecture/new_data_platform/`を参照。

2026-07-24より`common/sec_data/` 統合（フェーズ1の一部）が**構築中**。
他コンポーネント（`common/market_data/`・`common/macro_data/`等）は
未着手のまま（設計フェーズは2026-07-22〜23に完了済み）。

## 一次データ層の総数（`INPUT_DATA_TOBE.md`3分類、2026-07-24時点）

| 分類 | 件数 | ID範囲 | フェーズ1・2のスコープ内か |
|---|---|---|---|
| A. 一次データ本体 | 48件 | `INPUT-A-001`〜`048` | **対象**（一次データ層構築の主対象） |
| B. 取得前提条件 | 3件 | `INPUT-B-001`〜`003` | **対象**（SEC EDGAR取得〈`INPUT-B-002`/`003`〉・全体の対象銘柄決定〈`INPUT-B-001`〉の前提として、分類Aの取得と一体で構築する） |
| C. 導出データの入力 | 14件 | `INPUT-C-001`〜`014` | **対象外**（一次データそのものではなく`FIELD_DEFINITIONS.md`導出データ側の入力のため、フェーズ3〈導出データ層の管理方法検討〉で扱う） |
| **合計** | **65件** | — | — |

---

## フェーズ1: 一次データ層の構築（分類A48件＋分類B3件が対象）

| コンポーネント | 状態（未着手/構築中/完成） | 備考 |
|---|---|---|
| `common/sec_data/` 統合（raw/normalized/ttm統合含む、`INPUT-A-001〜018`対応） | 構築中（着手日2026-07-24） | `INPUT_DATA_TOBE.md` 2-A参照。統合スコープに`raw/`・`normalized/`・`ttm/`の3系統を含む旨を明記済み。`SEC_EDGAR_LAYER_DESIGN.md`のフェーズA〜C（Layer3スキーマ構築・`layer3_builder.py`実装・`ttm_calculator.py`snake_case統一）が実装済み。2026-07-29、フェーズC移行時の消費者横展開漏れ（`data_fetcher.py`・`audit.py`が旧PascalCaseキー参照のまま取り残されRICEスコア全銘柄停止）を`[[TTM-PASCALCASE-KEY-STALE-1]]`として修正完了（コミット`a7b840c32fde3b6619707f7a7c588baeaed12fd1`、`BACKLOG_DONE.md`参照）。**2026-08-01〜02、一次データ抽出品質の残課題6件が完了**（`[[PERIOD-LENGTH-VALIDATION-GAP-1]]`・`[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]`・`[[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]`・`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`段階1・`[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]`①・`[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]`、詳細はBACKLOG_DONE.md「2026-08-01/02（完了）」参照）。**セッション後半、`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`段階2〈formerNames区間一致によるSPAC合併疑いの機械的検知〉も完了**し同エントリは段階1・段階2とも完了としてBACKLOG_DONE.mdへ全文移動済み。副産物`[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]`〈KULR(2019)個別〉は根本原因調査でXBRL_MAPPING候補タグ設計欠陥と確定・105銘柄中278件へ及ぶ横断課題と判明したためクローズし`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`へ統合。**同エントリは実装完了**（貸借対照表恒等式逆算〈total_assets−stockholders_equity〉によるtotal_liabilitiesバックフィルを実装、278件全件で完全一致を確認、全105銘柄フローズン入力比較で対象外無変化を確認。BACKLOG_DONE.mdへ移動済み）。**`[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]`は解消**（3段階目の決算期変更は存在せず、実害なしと確認）。**`[[SPAC-STUB-PERIOD-VERIFICATION-1]]`は解消**（11銘柄すべて現状の処理が妥当と確認）。**`[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]`はMO/PM/SCCOの3銘柄をgenuine定義差と確定しクローズ**（残り11銘柄は`[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`・`[[LITE-COGS-DA-TAG-UNMERGED-1]]`へ分離登録）。残課題（優先度順）: `[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`〈中〜高、revenue/cost_of_revenue/gross_profitの複数フィールド間accn・期間不整合、CRM/JNJ/MRVLで確定・残り6銘柄要確認〉・`[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]`〈中、決算期変更移行期報告書の除外バグ〉・`[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]`〈中、RCATのOCF欠落〉・`[[LITE-COGS-DA-TAG-UNMERGED-1]]`〈低〜中〉・`[[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]`〈低〉・`[[ELF-ROE10YR-RECALC-PENDING-1]]`〈中、定期更新で自然解消見込み〉・`[[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]`〈低〜中〉等、`BACKLOG.md`該当項目を参照 |
| `common/market_data/` 新設（yfinance統合層、`INPUT-A-019〜023`対応） | 未着手 | `INPUT_DATA_TOBE.md` 2-B参照。日次/週次属性/イベント履歴の3層分離設計 |
| `common/macro_data/` 新設（FRED統合層、`INPUT-A-024〜047`対応） | 未着手 | `INPUT_DATA_TOBE.md` 2-C参照。系列単位の時系列ストア設計 |
| 取得前提条件の一元管理（`INPUT-B-001〜003`） | 未着手 | `INPUT_DATA_TOBE.md`分類B参照。監視銘柄マスタ・CIKマッピングの管理方法は分類Aの取得と一体で設計する |
| provenanceメタデータ標準化 | 未着手 | `INPUT_DATA_TOBE.md` 2-D参照（`as_of`/`fetched_at`/`source`/`source_detail`/`fallback_used`） |
| fetcher/reader分離アクセス制御 | 未着手 | `INPUT_DATA_TOBE.md` 3-B参照 |

## フェーズ2: 過去データ移管（分類A48件＋分類B3件が対象）

| データソース | 状態 | 対象範囲 |
|---|---|---|
| SEC EDGAR既存データ（`INPUT-A-001〜018`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-A・2-A参照（実測7経路） |
| yfinance既存データ（`INPUT-A-019〜023`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-B・2-B参照（実測11ファイル） |
| FRED既存データ（`INPUT-A-024〜047`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-C・2-C参照（実測2サブシステム） |
| 取得前提条件（`INPUT-B-001〜003`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-D・1-E参照（`monitor_tickers.yaml`・`cik_lookup.csv`／`cik_lookup_result.json`はいずれも現状`config/`配下に存在確認済み） |

**分類Cはフェーズ1・2の対象外**: `config/segment_config.json`等14件
（`INPUT-C-001〜014`）は一次データそのものではなく`FIELD_DEFINITIONS.md`
導出データ側（392件）が消費する入力であるため、一次データ層の構築・
移管スコープには含めない。Portfolio二重保持（`INPUT-C-008`）・
`config/`外配置（`INPUT-C-009`/`010`）等の是正要否は、フェーズ3
（導出データ層の管理方法検討）で扱う。

## フェーズ3: 導出データ層の管理方法検討（分類C14件を含む）

| 項目 | 状態 |
|---|---|
| `FIELD_DEFINITIONS.md` 499項目の新DB参照への切替方針 | 未着手（フェーズ1・2完了後に着手） |
| 分類C14件（`INPUT-C-001〜014`）の管理方法検討（`config/`外配置2件の是正、Portfolio二重保持の是正等） | 未着手（フェーズ1・2完了後に着手） |

---

## 関連BACKLOG項目

`NETCASH-DUAL-CALC-1`・`NETINCOME-DUAL-PIPELINE-1`・
`SECDATA-STORAGE-FRAGMENTATION-1`・`FRED-HYSPREAD-TRIPLE-FETCH-1`・
`SP500-GSPC-MULTI-FETCH-1`・`PORTFOLIO-CONFIG-DUP-1`・
`BETA-FALLBACK-DESIGN-GAPS-1`等、2026-07-22〜23に起票した39件のうち、
新DB構築（本プロジェクト）によって構造的に自動解消されるものと、新DB
構築後も個別対応が必要なもの（例: [[SCENARIO-BEARBULL-SIGN-FLIP-1]]の
ような計算ロジック自体の欠陥は、一次データ層の統合だけでは解消しない）
を区別する必要がある。この整理は本プロジェクトの各コンポーネント着手時に
行う。

## 更新ルール

本ファイルの各ステータスは、該当コンポーネントの実装依頼が完了した都度、
その完了報告に含まれる更新内容を反映して更新する（`CHAT_RULES.md`
「新DB構築プロジェクトの進捗管理」参照）。「未着手」→「構築中」→
「完成」の3段階で管理し、「構築中」に遷移した場合は着手日を、
「完成」に遷移した場合は完了日とコミットハッシュを備考欄に追記する。

分類A/B/Cの件数・IDリストに追加・削除が生じた場合は、本ファイル冒頭の
「一次データ層の総数」表も同時に更新する（`CHAT_RULES.md`
「一次データ層の件数管理」参照）。
