# PROJECT_STATUS.md — 新一次データベース構築プロジェクト進捗

作成日: 2026-07-23
更新日: 2026-08-05（[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]] Stage 1
完了。`common/sec_data/`一次データ取得層の「フィックス」機構
（`fixed_registry.json`、検証済み銘柄×年度を以後の抽出ロジック変更の
対象外とする仕組み）の運用方針確定・スキーマ設計・実装・検証まで
完了した。taxonomy属性①〜⑧（SPAC上場・決算期変更・M&A直後・非継続
事業・IPO前・業界特有会計慣行・標準タグ外れ・原因不明）非該当26銘柄・
372銘柄×年度エントリを`fixed_by: checkgate_pass`で登録、`parser.py`
（`_apply_fixed_registry_freeze()`、差分適用方式）・`report_
consistency_check.py`（CHECK-31/WARN-31、NG化）を実装。全105銘柄再
パースでフィックス対象含め全出力が無変化であることを確認済み。
機能コミット`7c15b2a75`・BACKLOG更新コミット`ae88715c5`（push済み）。
残タスク: taxonomy属性該当58銘柄のStage 2〜3（段階的フィックス拡大）。
詳細はBACKLOG_DONE.md「2026-08-05（完了）」・BACKLOG.md該当項目参照）

更新日: 2026-08-02（セッション終了処理。common/sec_data/統合フェーズ1の
備考欄に、セッション最終盤で発見した最重要事項を反映: TTM系列生成
パイプライン`layer3_builder.py`が`parser.py`（annual_YYYY.json生成）
とは完全に独立した別実装であり、annual側の修正（`[[PERIOD-LENGTH-
VALIDATION-GAP-1]]`・`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`・
`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`等7件）が構造的に
TTM側へ反映されないという設計上の発見（`[[TTM-DATA-DRIFT-BEHIND-
PIPELINE-1]]`）を登録。影響実測の結果、TANUKI VALUATION・STONKS SILO
への現在進行形の実害はゼロと確定し優先度を高→中に引き下げたが、構造的
脆弱性自体は温存されている旨を申し送り事項として明記。「次セッション
での着手順序」欄を最終整理。詳細はBACKLOG.md/BACKLOG_DONE.md該当項目
参照）

更新日: 2026-08-02（セッション終了処理。common/sec_data/統合フェーズ1の
備考欄を更新。`[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]`が
提起した4種の恒等式違反すべての分類調査が完了し同エントリをクローズ
（TA=TL+SE分は先行実装済み、GP≠Revenue−COGS/OI>GP/NI≠EPS×Sharesの
残る3種も本セッションで分類調査完了）。GOOGL(2012/2013)のGP≠Revenue−
COGSは`[[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]`として実装完了（案A
採用、`_apply_fact_overrides()`実行順序修正、機能コミット`ba8628198`・
データコミット`dd6fba1a1`）。COHR(2009-2011)のNI≠EPS×Sharesは
`[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]`として対応方針確定（
`fact_overrides.json`個別上書き、実装は次回）。同調査から派生した
`[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]`（未文書化tie-break欠陥）は
全母集団シミュレーションで広範な設計変更は危険と判明したため不採用とし
`[[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]`へガード条件付き介入として
統合。「次セッションでの着手順序」欄を最終整理。詳細はBACKLOG.md/
BACKLOG_DONE.md該当項目参照）

更新日: 2026-08-02（セッション終了処理。common/sec_data/抽出アーキテク
チャの俯瞰的脆弱性分析から`docs/architecture/new_data_platform/
EXTRACTION_DESIGN_PRINCIPLES.md`（新規データ層向け抽出設計原則）を新設。
`[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]`（会計恒等式TA=TL+SE
の横断検証レイヤー）を実装完了し、続くHEI・ONDS型許可リスト拡張
（[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]）と合わせてTA=TL+SE違反156件
中139件（89.1%）を解消。残る17件はCOHR2件
（[[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]）・その他15件
（[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]）に分けて継続調査。

更新日: 2026-08-02（セッション終了処理。`[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]`
パターンB実装前シミュレーション→`[[RCAT-TTM-SERIES-CONTINUING-
DISCONTINUED-UNCHECKED-1]]`根本原因調査を実施（いずれも読み取り専用の
調査・BACKLOG登録のみ、実装なし）。

**確定した内容**: RCATの本番FCF計算は`reader.py::get_fcf_5yr_avg()`
（年次ファイルベース）ではなく`data_fetcher.py::_select_fcf_source()`が
優先するTTM系列（`common/sec_data/ttm/RCAT_ttm_series.json`）経由である
ことが判明。年次パーサー側の継続/非継続事業分割タグ問題
（`[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]`）を年次パーサー
のみに実装してもRCATのIV・Classificationは変化しない（ΔIV=$0）ため、
`[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]`の優先度を「高→低」に訂正。

根本原因調査の結果、より深刻で現在進行形の実害を持つ別バグを発見:
`ttm_calculator.py::calc_ttm_series()`が採用四半期の日付連続性を検証せず
「アンカー日以前の直近4件」を単純採用する設計欠陥（ticker非依存の一般的
欠陥）により、RCATでは2023年7〜10月・10月〜2024年1月の四半期が
`ttm_end=2025-03-31`・`2026-03-31`の両方に重複使用され、現在の
`fcf_5yr_avg`（-40,185,008.5）・`fcf_2yr_avg`（-50,540,837.0）が正しい値
（試算：約-53,985,212・約-78,141,244）より34〜55%過小評価と確定。ただし
IVへの影響は現時点でΔIV=$0（revenue floor＋EPSベース推定オーバーライド
が吸収、将来業績改善時に顕在化しうる潜在リスクの留保付き）。他銘柄
（HON/AVAV/TER）への現時点の実害なしと確認。

根本原因（ticker非依存の一般的欠陥）を`[[TTM-CALC-QUARTER-CONTIGUITY-
UNCHECKED-1]]`として新規登録（優先度：中〜高）。

**次回最優先タスク**: `[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]`
〈優先度：中〜高、calc_ttm_series()の日付連続性チェック欠如。まず105銘柄
全体での該当有無の横断スキャンから着手〉。

詳細はBACKLOG.md/BACKLOG_DONE.md該当項目参照）

更新日: 2026-08-02（セッション終了処理。2026-08-01〜02の2日間にわたり
gross_profit調査を発端に波及した一連のデータ品質是正作業の最終サマリを
反映。

**完了・クローズ項目（全16件）**: `[[PERIOD-LENGTH-VALIDATION-GAP-1]]`・
`[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]`・`[[SPAC-STUB-PERIOD-FIELD-
SPLIT-1]]`・`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`段階1・段階2・`[[LAYER3-
GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]`①・`[[STONKS-SILO-FETCHER-
GROSSPROFIT-BACKFILL-DUP-1]]`・`[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-
KULR-1]]`（`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`へ統合）・
`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`（278件是正実装完了）・
`[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]`（解消・実害なし）・
`[[SPAC-STUB-PERIOD-VERIFICATION-1]]`（解消・11銘柄すべて妥当と確認）・
`[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]`一部（MO/PM/
SCCOをgenuine定義差と確定）・`[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`
案b（LRCX(2010)是正実装完了、CRM/JNJ/MRVL/ONDS型は残存）・
`[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]`（案③WARN-28実装完了）・
`[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]`（`[[OPERATING-CASH-FLOW-
CONTINUING-DISCONTINUED-GAP-1]]`へスコープ拡大・統合）。

**次回最優先タスク**: `[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]`〈優先度：高、
現在進行形のDCF計算実害。RCATの`get_fcf_5yr_avg()`が実質2021-2023年の
3年平均になっており、真により大きな悪化を示す2024/2025年〈特に-$89.1M〉
が欠落。`[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]`のRCAT分
〈パターンB、継続+非継続の合算〉解決が前提〉。残る25銘柄中24銘柄は該当
年度が現在の直近5年窓の外にあり実害なしと確定済み。

詳細はBACKLOG.md/BACKLOG_DONE.md該当項目参照）

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
| `common/sec_data/` 統合（raw/normalized/ttm統合含む、`INPUT-A-001〜018`対応） | 構築中（着手日2026-07-24） | `INPUT_DATA_TOBE.md` 2-A参照。統合スコープに`raw/`・`normalized/`・`ttm/`の3系統を含む旨を明記済み。`SEC_EDGAR_LAYER_DESIGN.md`のフェーズA〜C（Layer3スキーマ構築・`layer3_builder.py`実装・`ttm_calculator.py`snake_case統一）が実装済み。2026-07-29、フェーズC移行時の消費者横展開漏れ（`data_fetcher.py`・`audit.py`が旧PascalCaseキー参照のまま取り残されRICEスコア全銘柄停止）を`[[TTM-PASCALCASE-KEY-STALE-1]]`として修正完了（コミット`a7b840c32fde3b6619707f7a7c588baeaed12fd1`、`BACKLOG_DONE.md`参照）。**2026-08-01〜02、一次データ抽出品質の残課題6件が完了**（`[[PERIOD-LENGTH-VALIDATION-GAP-1]]`・`[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]`・`[[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]`・`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`段階1・`[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]`①・`[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]`、詳細はBACKLOG_DONE.md「2026-08-01/02（完了）」参照）。**セッション後半、`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`段階2〈formerNames区間一致によるSPAC合併疑いの機械的検知〉も完了**し同エントリは段階1・段階2とも完了としてBACKLOG_DONE.mdへ全文移動済み。副産物`[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]`〈KULR(2019)個別〉は根本原因調査でXBRL_MAPPING候補タグ設計欠陥と確定・105銘柄中278件へ及ぶ横断課題と判明したためクローズし`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`へ統合。**同エントリは実装完了**（貸借対照表恒等式逆算〈total_assets−stockholders_equity〉によるtotal_liabilitiesバックフィルを実装、278件全件で完全一致を確認、全105銘柄フローズン入力比較で対象外無変化を確認。BACKLOG_DONE.mdへ移動済み）。**`[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]`は解消**（3段階目の決算期変更は存在せず、実害なしと確認）。**`[[SPAC-STUB-PERIOD-VERIFICATION-1]]`は解消**（11銘柄すべて現状の処理が妥当と確認）。**`[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]`はMO/PM/SCCOの3銘柄をgenuine定義差と確定しクローズ**（残り11銘柄は`[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`・`[[LITE-COGS-DA-TAG-UNMERGED-1]]`へ分離登録）。**`[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`は案b（同一accn＋期間一致優先）を実装完了**（LRCX(2010)のcost_of_revenueを是正、全105銘柄フローズン入力比較で対象外無変化を確認。CRM(2013)・JNJ(2017)・MRVL(2017)・ONDS(2017)は案b単独では未解決のまま残存、案a・案cはゲート条件込みの再設計が必要）。**`[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]`は案③（`report_consistency_check.py`へのWARN-28追加）を実装完了**しBACKLOG_DONE.mdへ移動（案①のrelevant_forms修正はコスト過大と判明し見送り確定）。**`[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]`は根本原因調査の結果、105銘柄中25銘柄へ及ぶ横断課題と判明したためクローズし`[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]`へ統合**（実害確認調査で25銘柄中24銘柄は現在の直近5年窓の外にあり実害なしと確定、優先度を高→中に訂正）。**RCAT単独については`[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]`として新規登録**（優先度：高、`get_fcf_5yr_avg()`が実質3年平均になっておりDCFのFCFベース値計算に現在進行形の実害）。**2026-08-02後半、`[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]`パターンB実装前シミュレーションを実施した結果、RCATの本番FCF計算はTTM系列（`common/sec_data/ttm/RCAT_ttm_series.json`）経由でありreader.py::get_fcf_5yr_avg()（年次ファイルベース）は使われていないと判明**（年次パーサー側パターンB実装ではΔIV=$0、優先度を高→低に訂正）。**続く`[[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]`根本原因調査で、当初懸念とは異なりticker非依存の一般的欠陥（`ttm_calculator.py::calc_ttm_series()`が採用四半期の日付連続性を検証しない）を発見。RCATでは2023年7〜10月・10月〜2024年1月の四半期がttm_end=2025-03-31・2026-03-31の両方に重複使用され、fcf_5yr_avg・fcf_2yr_avgが正しい値より34〜55%過小評価と確定したが、IVへの影響は現時点でΔIV=$0（revenue floor＋EPSベース推定オーバーライドが吸収、将来業績改善時に顕在化しうる潜在リスクの留保付き）。根本原因を`[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]`として新規登録（優先度：中〜高）。**2026-08-02セッション後半、common/sec_data/抽出アーキテクチャの俯瞰的
脆弱性分析を実施し、本セッションで発見した5バグ（[[PERIOD-LENGTH-
VALIDATION-GAP-1]]・[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]・
[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]・[[SPAC-SHELL-BS-ENTITY-
MIXING-1]]・[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]）が共通の設計的
欠陥に帰着すると判明**。この教訓を新規データ層向けに一般化した
`docs/architecture/new_data_platform/EXTRACTION_DESIGN_PRINCIPLES.md`
（`common/market_data/`・`common/macro_data/`着手前に確認すべき3原則・
チェックリスト、`MIGRATION_CHECKLIST.md`と同型の独立文書）を新設した。
**`[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]`（会計恒等式
Total_Assets=Total_Liabilities+Stockholders_Equityの横断検証レイヤー）
を実装完了**（機能コミット`bd91000f0`）。OR条件フォールバック方式
（①本体一致→②不一致時のみNCI・一時的持分の許可リストを加算した拡張形）
で実装し、全105銘柄検証でTA=TL+SE違反156件中133件を解消。続けて
[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]のHEI・ONDS型（許可リスト拡張、
機能コミット`a910afef2`）を実装し**156件中139件（89.1%）が解消**。
残る17件のうちCOHR2件は[[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]
（CHECK29のown-accn限定照合という設計方針の緩和検討）へ切り出し、
残り15件（PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW）は個別調査未着手。
**2026-08-02セッション後半（続き）、`[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]`が提起した4種のPL/BS恒等式違反のうち残る3種（GP≠Revenue−COGS・OI>GP・NI≠EPS×Shares）の分類調査が完了**（TA=TL+SE分は上記の通り実装済み）。GOOGL(2012/2013)のGP≠Revenue−COGSは`fact_overrides.json`によるrevenue手動補正が`_backfill_gross_profit_from_revenue_cogs()`より後段で適用されるシーケンシングバグと確定・**`[[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]`として実装完了**（案A採用、`_apply_fact_overrides()`を全逆算バックフィルより前に移動、機能コミット`ba8628198`・データコミット`dd6fba1a1`、GOOGL(2012/2013)のgross_profitを是正、105銘柄フローズン入力比較で対象外無変化を確認）。LMT(18/19年度)のOI>GPは①genuine（設計スコープ外）と確定・対応不要。COHR(2009-2011)のNI≠EPS×SharesはCOHR自身のFY2011 10-Kのshares_diluted/basic単位スケール申告誤り（1/1000）と確定し**`[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]`として新規登録・対応方針確定**（`fact_overrides.json`個別上書き、値も確定済み、実装は次回）。同エントリ調査から派生した`[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]`（本人データ不在時の未文書化tie-break欠陥）は全母集団シミュレーションの結果、広範な設計変更は危険（31銘柄・124件変化、確実な改善はCOHRの2件のみ）と判明したため不採用とし、**ガード条件付き介入として`[[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]`へ統合・実装方式確定**（同符号かつ比が10のべき乗値の場合のみ新filing優先へ切り替え）。`[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]`本体は4種すべて分類調査完了としてBACKLOG_DONE.mdへ移動。

**2026-08-02セッション最終盤、`[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]`実装完了に伴う検証過程で、common/sec_data/統合フェーズ1の設計上の重大な発見があった**: TTM系列（`common/sec_data/ttm/`）を生成する`layer3_builder.py`（＋`quarterly.py`・`fact_selection.py`・`q4_implied.py`）は、annual_YYYY.jsonを生成する`parser.py`とは**完全に独立した別実装のパイプライン**であり、`parser.py`のクラス・関数を一切importせず`fact_overrides.json`も読み込まず、`_resolve_bs_entity_mixing()`等の主要ロジックも実装されていないことを確認した。結果、本セッションのannual側修正の大部分
（`[[PERIOD-LENGTH-VALIDATION-GAP-1]]`・`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`・`[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]`・`[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`・`[[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]`・`[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]`・`[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]`）は、`.github/workflows/SEC_Data_Update.yml`（毎週日曜自動実行、正常稼働中と確認済み）が何度実行されてもTTM系列には反映されないという構造的問題であると判明し、`[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]`として新規登録した（唯一の例外は`[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]`自体、`ttm_calculator.py`への直接実装のため自動反映される）。続く影響実測調査で、TANUKI VALUATION・STONKS SILOいずれも上記7件への現在進行形の実害はゼロと確定した（BS項目・shares系はTTM出力＝`FLOW_FIELDS`17種に構造的に含まれず消費経路も`annual_*.json`を直接参照、その他は対象年度が現在のTTM anchor範囲外、STONKS SILOはTTM/layer3を一切参照しない独立パイプラインと確認）ため優先度を高→中に引き下げたが、**2つの独立パイプラインが同期しない構造的脆弱性自体は温存されている**ため、将来の新規annual側修正では都度TTM側への影響確認が必要である旨を申し送る。

残課題（優先度順、2026-08-02セッション終了時点）: `[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]`〈中、構造的脆弱性は残存・既知7件への実害はゼロ確定〉・`[[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]`〈中〉・`[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]`〈中、残り15件〉・`[[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]`〈中〉・`[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]`〈中〉・`[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]`残存分〈中〜高〉・`[[LITE-COGS-DA-TAG-UNMERGED-1]]`〈低〜中〉・`[[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]`〈低〜中〉・`[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]`〈低、副次的解消見込み〉・`[[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]`〈低〉・`[[ELF-ROE10YR-RECALC-PENDING-1]]`〈中、定期更新で自然解消見込み〉・`[[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]`〈低〜中〉等、`BACKLOG.md`該当項目を参照。**2026-08-05、`[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]` Stage 1完了**（`fixed_registry.json`フィックス機構の運用方針確定・スキーマ設計・実装・検証。taxonomy属性①〜⑧非該当26銘柄・372銘柄×年度エントリを`fixed_by: checkgate_pass`で登録、`parser.py`/`report_consistency_check.py`〈CHECK-31/WARN-31〉実装、全105銘柄再パースで無変化を確認。詳細はBACKLOG_DONE.md「2026-08-05（完了）」参照）。**残タスク: Stage 2〜3**（taxonomy属性該当58銘柄の段階的フィックス拡大、`fixed_by: manual_verification`）は未着手 |
| `common/market_data/` 新設（yfinance統合層、`INPUT-A-019〜023`対応） | 未着手 | `INPUT_DATA_TOBE.md` 2-B参照。日次/週次属性/イベント履歴の3層分離設計。**着手前に`EXTRACTION_DESIGN_PRINCIPLES.md`（common/sec_data/で発見された5バグの教訓を一般化した抽出設計原則）を確認すること（2026-08-02追記）** |
| `common/macro_data/` 新設（FRED統合層、`INPUT-A-024〜047`対応） | 未着手 | `INPUT_DATA_TOBE.md` 2-C参照。系列単位の時系列ストア設計。**着手前に`EXTRACTION_DESIGN_PRINCIPLES.md`（common/sec_data/で発見された5バグの教訓を一般化した抽出設計原則）を確認すること（2026-08-02追記）** |
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
