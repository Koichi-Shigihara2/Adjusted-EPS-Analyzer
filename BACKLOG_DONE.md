# BACKLOG 完了アーカイブ / アクティブな課題は BACKLOG.md を参照

---

## 2026-08-02（完了）

### ✅ [SPAC-SHELL-BS-ENTITY-MIXING-1] SPAC合併銘柄でBS（instant fact）フィールドが合併前シェル会社・合併後本体の異なる法的実体から混在採用され数学的に矛盾する値が本番稼働中（段階1・段階2いずれも完了）
**優先度:** 高（登録時）→中（段階1完了後、実害解消済みのため）
**分類:** バグ / 確定
**登録日:** 2026-08-01
**完了日:** 2026-08-02（段階1・段階2とも）
**発見:** [[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]個別調査（チャット記録）

#### 内容（根本原因）
SPAC合併を経た銘柄で、同一年度のBS（instant fact）フィールドが、異なる
法的実体（合併前のSPACシェル会社 vs 合併後の本体）から混在して採用されて
いた。既存の`_own_override_is_safe()`は「同一フィールド内での年度競合」
のみをチェックし、「同一年度・異なるBSフィールドが異なるaccn（法的実体）
から来ていないか」という横断チェックを持たなかった。

確定した実害（段階1着手時点）: BBAI(2020)・RDW(2020)・RKLB(2020)・
SOFI(2020)・VRT(2019)で`current_assets>total_assets`等の数学的に不可能な
状態が本番稼働中だった。全105銘柄横断スキャンでSPIR(2020)は同一パターン
だが矛盾が未顕在化の"事故的な正しさ"、ONDS(2017)・KULR(2016)は原因は同型
だがSPAC非該当と判明。KULR(2019)のみ原因が別系統（同一filing内でのcandidate
tag誤選択）と確定し[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]として
分離登録（未解決のまま残存）。

#### 段階1実装内容（矛盾トリガー型の単一accn強制）
`SECParser._resolve_bs_entity_mixing()`を新規追加。「①複数accnが混在」
かつ「②本人データ(is_own_data=True)を提供するaccnが単一に定まる」かつ
「③現に数学的矛盾が確認できる」かつ「④アンカーへの統一により実際に矛盾が
解消する」の4条件をすべて満たす年度についてのみ、本人データのaccnを
アンカーとして採用し、アンカー以外のaccnから採用されたBSフィールドを
None化する設計（安全側のNone化）。条件④はKULR(2019)型（矛盾の原因フィールド
が元々同一accn内にあり、accn混在自体は矛盾と無関係）の巻き添えNone化を
防ぐため実装時に追加。

案A（単一accn強制）を無条件で全銘柄に適用する設計は、105銘柄・87件への
オフラインシミュレーションで正常系56件（41銘柄）を新たにNone化する副作用が
判明したため不採用と確定し、「矛盾トリガー型」に限定する設計へ絞り込んだ。

コミット: `80e51d2c2`（機能変更・テスト）・`c5e588474`（データ再生成）

**検証結果**: BBAI(2020)/RDW(2020)/RKLB(2020)/SOFI(2020)/VRT(2019)・
ONDS(2017)・KULR(2016)の7銘柄7年度で数学的矛盾が解消。全105銘柄フローズン
入力比較で対象7件以外に変化なし（矛盾のない56件・KULR(2019)・SPIR(2020)
含む）を確認。pytest 461 passed/2 known failed、report_consistency_check.py
NG=0（WARN=68件、変化なし）。

#### 段階2実装内容（formerNames区間一致によるSPAC合併疑いの機械的検知）
SPIR(2020)型（矛盾が未顕在化の"事故的な正しさ"）を、矛盾の有無に頼らず
事前検知するため、SEC EDGAR submissions APIのformerNames（法人名変更履歴、
[{name, from, to}, ...]）を活用した検知を追加。

- `fetcher.py::_fetch_submissions_for_cik()`で、既に取得済みのレスポンスから
  formerNamesを追加取得・保存するよう変更（**新規APIコールは発生しない**、
  同一レスポンスからの追加抽出のみ）。`load_former_names()`を新設
- `_resolve_bs_entity_mixing()`に新しいトリガー条件③'「矛盾はないが、
  アンカー候補accnのreportDateがformerNames区間[from, to]内にある」を
  追加。既存の条件③（数学的矛盾確認済み）とのOR条件とし、③または③'を
  満たせば段階1と同じ解消処理に進む
- 誤検知防止のため③'は常に条件①（複数accn混在）・②（本人データaccnの
  一意性）とのAND条件でのみ発火する設計。formerNames単独では「単純な
  改名」（例: RKLBの「Rocket Lab USA, Inc.」→「Rocket Lab Corp」2025年
  再法人化、SPAC合併とは無関係）と合併疑いを区別できないため、accn混在
  という構造的シグナルとの組み合わせで誤検知を防いだ
- 検知条件は「reportDateがformerNamesの[from, to]区間に含まれるか」の
  厳密な区間包含チェック（日数閾値は不要）。BBAI/RDW/RKLB/SOFI/VRT/SPIRの
  6銘柄全件で例外なく一致することを実データで確認済み
- 監査証跡として`_save_spac_shell_detection_log()`を新設し、
  `spac_shell_detection_log.json`（既存のfy_collision_log.json等と同一
  パターン、0件でも毎回書き込む）に検知内容を記録

コミット: `1f6e95d92`（機能変更・テスト）・`43470bccf`（データ再生成）

**検証結果**:
1. SPIR(2020)が新規検知・解消されることを確認（long_term_debt
   $26,645,000をNone化、triggered_by="former_names_window"）
2. BBAI/RDW/RKLB/SOFI/VRT（既に段階1で解消済み）が③'条件でも重複検知
   されるが結果は不変（冪等性を確認、triggered_by="math_violation"）
3. 全105銘柄フローズン入力比較で、SPIR(2020)以外に一切変化がないことを
   確認（RKLBの「単純な改名」ケースでの誤検知なしを含む）
4. `spac_shell_detection_log.json`が全105銘柄で正しく生成され、検知6件
   （BBAI/RDW/RKLB/SOFI/VRT・SPIR）が正しく記録されていることを確認
5. pytest 473 passed/2 known failed（既知のMSFT/NVDA、[[TEST-STALE-IV-1]]）、
   report_consistency_check.py NG=0（WARN=68件、変化なし）を確認
6. formerNames取得は6対象銘柄のみforce_refreshで即時反映。残り99銘柄は
   通常の週次自動更新（SEC_Data_Update.yml、24時間キャッシュより長い
   間隔で必ず再取得が発生）で自然にバックフィルされ、特別な一括再取得は
   不要と設計上確認（実行は行わず、次回以降の通常更新サイクルに委ねる）

#### 副産物として新規発見・登録した課題（未実装）
- [[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（KULR(2019)単独、原因は
  同一filing内でのcandidate tag誤選択と確定、entity混在ではない）

---

### ✅ [LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1] GrossProfitバックフィルが本番データパス(annual_YYYY.json)に到達しない構造的欠落（①本番書き戻し完了、②はGROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1へ引き継ぎ）
**優先度:** 中〜高
**分類:** データ品質 / アーキテクチャ欠陥
**登録日:** 2026-07-29
**完了日:** 2026-08-02
**発見:** cost_of_revenue/EPS投資調査（チャット記録）

#### 内容（根本原因）
normalizer.py::_calc_gross_profit()・layer3_builder.py::_backfill_gross_profit()は
中間パイプライン(ttm/{ticker}_ttm_series.json・store_v2)にのみ作用し、TANUKI VALUATION・
STONKS SILOが実際に読むcommon/sec_data/data/{TICKER}/annual_YYYY.jsonには一切書き戻され
ない。加えてこのバックフィルは書き込み専用(一方向)であり、gross_profitが既に存在する
期間ではcost_of_revenueとの突合・検算は一切行われない。CAKE実例ではFY2008-2021の19年間、
cost_of_revenue実額がありながらgross_profitは一貫してNoneだった。

着手条件（[[PERIOD-LENGTH-VALIDATION-GAP-1]]の解消）は2026-07-31に充足。その後
2026-08-02の現状再確認で、gross_profit欠損・乖離状況を全105銘柄で再スキャンし、
①(本番書き戻し)のリスク（既存の正しい値を誤って上書きするリスク）が実質ゼロで
あることを確認した上で①を実装した。

#### 実装内容（①本番書き戻し）
`SECParser._backfill_gross_profit_from_revenue_cogs()`を新規追加。標準タグ
（GrossProfit/GrossProfitLoss）からgross_profitが取得できない年度についてのみ、
revenue - cost_of_revenueで逆算した値を採用し本番annual_YYYY.jsonへ書き戻す。

適用条件（Case Aの定義を厳密に踏襲）:
- gross_profitが標準タグから取得できていない年度のみ（標準タグを常に優先、
  既存の正しい値を上書きする経路は持たない）
- revenue・cost_of_revenueが同一年度で両方present

採用値のprovenance（pl_provenance.gross_profit）には`"derived": True`を付与し、
実タグに基づかない逆算値であることを明示（bs_provenance側のis_approximated規約と
同種）。CLAUDE_CODE_START.mdの「生成パイプラインをバイパスした手動データパッチの
禁止」原則に沿い、生成元コード（parser.py）自体に恒久的なフォールバックロジック
として実装した（後処理パッチではない）。

`_parse_raw_data()`の全フィールド抽出ループ・cross_filing_tags適用後に1回呼び出す。
Predecessor/Successor型（revenue/cost_of_revenue自体もNoneの年度、例: ELF
2014/2019・BBAI/RDW/RKLB/SOFI/VRT 2020/2019）は判定を経由せず自動的に対象外となる。

コミット: `dc0507c27`（機能変更・common/sec_data/parser.py・テスト）

#### 検証結果
1. 対象34銘柄342件（ABBV/AMZN/APP/BROS/CAKE/CAT/COHR/CON/CPRT/CRWV/FCX/FICO/
   GOOGL/HEI/HON/HWM/IONQ/KLAC/LLY/LYFT/META/MSCI/PEP/RMBS/RXRX/SCCO/SOFI/SOUN/
   TASK/TDY/VRT/VZ/WMT/ZETA）でgross_profitがrevenue-cost_of_revenueの値で
   完全一致（許容誤差なし）で埋まることを確認
2. 全105銘柄フローズン入力比較で、対象342件以外（Case B残存49件・既存の正常値
   含む）は変化ゼロを確認
3. 対象342件すべてに`pl_provenance.gross_profit.derived=True`が正しく設定
   されていることを確認
4. STONKS SILO fetcher.py（discover/stonks-silo/src/fetcher.py、gross_profit=None
   時の重複自己修復ロジック）について、STONKS SILO対象25銘柄全体で
   `gross_profit=None かつ revenue/cost_of_revenue両方present`の残存ケースが
   0件になったことを確認した。**[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-
   DUP-1]]の重複ロジックは、少なくとも「revenue/cost_of_revenue両方存在」の
   条件下では発火し得ない（実質デッドコード化）ことを確認**（同エントリの
   クローズ判断材料として報告のみ、同エントリ自体の更新は別タスク）
5. pytest 467 passed/2 known failed（既知のMSFT/NVDA、[[TEST-STALE-IV-1]]）、
   report_consistency_check.py NG=0（WARN=68件、変化なし。pl_provenance/
   gross_profitを参照する既存WARN項目は皆無のため誤作動リスクなしと事前確認
   した上で実施）を確認
6. pytest全件NG=0（上記5と同一）
7. TANUKI VALUATION（growth.py・data_fetcher.py・core_calculator.py等）は
   annual_YYYY.jsonの`pl.gross_profit`を一切参照しないことをコードベース全体で
   確認した（Moat ScoreのGross Margin成分は`docs/common/sec_data/normalized/`
   の別系統・normalizer.py独自の四半期ベース逆算を参照しており、本実装とは
   無関係）。よってgrowth.py::fcf_list[:5]の直近5年窓・IV・Classificationへの
   影響は**ゼロ**と確定

#### データコミット
`65ddd0d6b`（common/sec_data/data/、34銘柄・342ファイル）

#### 副産物として新規発見・登録した課題（未実装）
- [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低。HON(2009)のみ
  期間長是正後も乖離が残存、既知パターンと異なる原因の疑い）
- [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]の対象を14銘柄へ拡大
  訂正（Case B残存49件の全容判明。**本タスクの②〈突合検算ロジック〉はこちらの
  エントリへ実質的に引き継がれた**）

---

### ✅ [STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1] gross_profit=None時のRevenue-cost_of_revenue補完ロジックが3箇所に重複実装（実害解消済み・コード整理は将来検討）
**優先度:** 低
**分類:** アーキテクチャ / 重複実装
**登録日:** 2026-07-31
**完了日:** 2026-08-02
**発見:** [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]調査（チャット記録）

#### 内容（登録時の記録）
discover/stonks-silo/src/fetcher.py(172-174行)が、normalizer.py::
_calc_gross_profit()・layer3_builder.py::_backfill_gross_profit()とは独立に、
gross_profit=None時のRevenue−cost_of_revenue自前補完ロジック
(gross_profit_derived=Trueを付与)を持っている。None時の挙動自体は明示的で
安全(暗黙のゼロ化なし)だが、同じ計算が3箇所に分散している。

#### クローズ判断根拠（2026-08-02）
[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]①実装
（`SECParser._backfill_gross_profit_from_revenue_cogs()`、annual_YYYY.jsonへの
gross_profit書き戻し）の検証過程で、STONKS SILO対象25銘柄全体を走査し、
`gross_profit=None かつ revenue/cost_of_revenue両方present`という
fetcher.py側の重複補完ロジックの発火条件に該当するケースが**0件**に
なったことを確認した。annual_YYYY.json側で先に値が埋まるため、
fetcher.py(172-174行)の当該コードパスは**実質的に発火し得ない状態
（デッドコード化）**になっている。

**「解消」の性質**: 実害（3箇所での計算重複によるメンテナンスコスト・
将来的な計算式乖離リスク）は解消されたが、これはfetcher.py側の**コード
自体を削除・整理した結果ではない**。コードは依然としてdiscover/
stonks-silo/src/fetcher.pyに残存しており、発火条件に該当するデータが
将来再び発生すれば動作する状態を維持している（デッドコードとしての残存、
削除ではない）。

#### 対応方針（クローズ後の扱い）
コード自体の削除・共有アクセサへの一本化は本クローズの対象外とし、
将来のcommon/sec_data統合（フェーズ1、STONKS SILOのreader.py利用まで
進んだ時点）で改めて検討する。実害面では緊急性がなくなったため、
統合作業の一環として着手可能になったタイミングでのクリーンアップを推奨する。

#### 着手条件（コード整理を再検討する場合）
common/sec_data統合(フェーズ1)がSTONKS SILOのreader.py利用まで進んだ時点。

---

## 2026-08-01（完了）

### ✅ [ELF-FISCAL-END-MONTH-MISDETECTION-1] fiscal_end_month/anchor検出が1銘柄単一値のみ対応、実在する決算期変更（ELF/RCAT/AVGO）をera別に扱えない構造的限界（2026-08-01案②完了）
**優先度:** 高
**分類:** バグ / 一次データ抽出ロジック（決算年度判定）
**登録日:** 2026-07-31
**完了日:** 2026-08-01
**発見:** [[PERIOD-LENGTH-VALIDATION-GAP-1]]実装時の全105銘柄フローズン入力
再生成・検証、および[[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]との関係確認調査
（いずれもチャット記録）

#### 内容（根本原因、案①完了時点の記録）
[[PERIOD-LENGTH-VALIDATION-GAP-1]]の期間長フィルタ実装後、全105銘柄で
annual_YYYY.jsonを再生成しフローズン入力比較を行ったところ、ELFのみ
revenue/gross_profit/net_income等が「新年度の値に前年度の値が入り込む」
一連のカスケード的な入れ替わりを起こすことを発見した。根本原因は
`_detect_fiscal_end_month()`/`_detect_fiscal_anchor_date()`が1銘柄につき
単一のfiscal_end_month/anchorしか持てず、実在する決算期変更（ELFは12月
決算→3月決算へ変更）をera別に扱えない構造的限界だった。案①（期間長
フィルタの`_detect_fiscal_end_month()`への追加、コミット`96c42d8f0`）は
必要条件だが不十分と実証され、案②（era別anchor切替）が根治手段として
確定していた。

#### 実装内容（案②）
- `common/sec_data/utils.py`: 新規関数`detect_fiscal_anchor_clusters(us_gaap,
  candidate_keys, min_support=2)`を追加。`_cluster_fiscal_anchor_candidates()`
  が返す全クラスタのうち、主anchor（最大クラスタ）以外でsupport>=2の
  有意なクラスタのアンカー日のみを追加候補として返す。単一クラスタ銘柄
  （105銘柄中100銘柄）は必ず空リストを返す設計。
  `detect_fiscal_anchor_date()`との重複コードを避けるため、day_counts収集
  （`_collect_anchor_day_counts()`）・クラスタ内アンカー日算出
  （`_cluster_anchor_point()`）を共通ヘルパーへ抽出するリファクタリングを
  実施（既存関数の挙動は変更なし、105銘柄全件比較で確認済み）。
- `determine_fiscal_year()`に`extra_anchors: Optional[Sequence[Tuple[int,int]]]
  = None`引数を追加。指定時は主anchor＋extra_anchorsの全候補から、同じ
  365日ウィンドウ探索でグローバルに最小距離の候補年度を採用する。
  extra_anchors省略/空リスト時は主anchor単独の探索のみとなり、追加前と
  数学的に完全同一の計算になる（単一ループ順序が変わらないため）。
- `common/sec_data/parser.py`: `SECParser._parse_raw_data()`冒頭で一度だけ
  `detect_fiscal_anchor_clusters()`を呼び出し、既存の5つの
  `determine_fiscal_year()`呼び出し箇所（`_collect_own_data_annual()`・
  `_collect_own_data_instant()`・`_own_override_is_safe()`・
  `_extract_values_merged()`・`_extract_single_key()`）全てに同じ配線
  パターンで`extra_anchors`を通した（`_collect_own_data()`・
  `_extract_values()`・`_extract_values_best_candidate()`も中継のため
  シグネチャ拡張）。

#### 検証結果
1. 全105銘柄でbucketing結果を新旧比較（git worktreeで変更前コードを
   分離して実行）。**変化があったのはELFのみ**。RCAT/AVGO/MSCI/NOWは
   いずれも2クラスタ検出（RCAT: 主(4,30)+追加(12,31)、AVGO: 主(12,31)+
   追加(10,30)、MSCI: 主(12,31)+追加(11,30)、NOW: 主(12,31)+追加(6,30)）
   だが、実際のend_dateがいずれも主anchor側に十分近く、bucketingへの
   実害はゼロ（era別の構造的な保険が追加されたのみ）。単一クラスタの
   100銘柄は完全不変を確認。
2. ELFのrevenue/gross_profit/cost_of_revenue/net_income/operating_incomeが
   2015-2018年度で真の暦年値に復旧したことを確認（例: revenue
   2015=$191,413,000、2016=$229,567,000、2017=$269,888,000、
   2018=$267,435,000。10-K原本"Selected Financial Data"表の
   Net sales $191,413/$229,567（千ドル）と一致確認済み）。
3. ELFの2014年度・2019年度（移行期）はPL/CF系フィールドがNone化。
   事前チャット確認済みの通り、2014年は本タスク着手前にPredecessor
   （2014-01-01〜01-31、Net sales $9,810K）/Successor（2014-02-01〜
   12-31、333日、Net sales $135,134K）分割による正当な333日Successor値
   と10-K原本で確認済みであり、合算救済は行わず安全側のNone化を採用
   （BS項目=instant factは期間長フィルタの対象外のため両年度とも維持）。
4. 前回除外していたELF分annual_2014-2019.json（6ファイル）を、フローズン
   入力（company_facts.json等は再取得せず）で`SECParser.parse_and_save
   ('ELF')`により再生成し、[[PERIOD-LENGTH-VALIDATION-GAP-1]]コミット
   `d6d404016`時点の除外を解除した。
5. pytest: 447 passed/2 known failed（既知のMSFT/NVDA、[[TEST-STALE-IV-1]]）
   → 453 passed/2 known failed（新規テスト6件追加、既知失敗数に変化なし）。
   `report_consistency_check.py`: NG=0（WARN=68件、変化なし。ELFはWARN-10
   〈yfinance PSステール値、無関係〉のみで新規WARNなし）。
6. TANUKI VALUATIONパイプライン（`pipeline.py ELF --skip-risk`）を試験
   実行し、Intrinsic_Value_BASE/DCF_FCF_PV/DCF_TV_PV/DCF_v0/
   Growth_Rate_Original（いずれも`growth.py::fcf_list[:5]`の直近5年窓
   ベース）が完全無変化であることを確認（最新年度が2026のためウィンドウは
   2022-2026年度相当で2015-2019年度に到達しない）。STONKS SILOはELFが
   `cik_lookup.csv`でstonks_silo=falseのため対象外。
   **一方、`ROE_avg (10yr)`は7.0%→9.6%へ変化することを検知した**
   （10年ROE平均窓が2017-2019年度を含むため、是正された正しい値が反映
   された）。これに連動しAlpha_Premium（HypeCore expectation premium、
   ALPHA-REDESIGN-1後はIntrinsic_Valueに非乗算の参考値）が0.29→0.40へ
   変化するが、TANUKI SCORE分類（WATCH）・Matrix Quadrant/Labelは不変。
   本タスクのスコープ外のため、このTANUKI VALUATION側の再生成・コミットは
   実施していない（試験実行の出力は`git checkout`で破棄済み）。

#### コミット
- コード変更: `7c44ac266`（`common/sec_data/parser.py`・`utils.py`・
  `tests/test_fiscal_year_anchor_window.py`）
- データ再生成: `6d9c18b2f`（`common/sec_data/data/ELF/annual_2014-2019.json`
  6ファイル）
- BACKLOG更新: 本コミット
（ユーザー指示により今回はpushを保留、コミットのみ）

#### 対象銘柄の残課題
- **ELF**: 本タスクで解消。
- **RCAT**: bucketingへの実害は引き続きゼロ（本タスクの案②実装で
  構造的な保険は追加済み）だが、直近10-Kが12月31日・4月30日の両クラスタに
  同時投票しており3段階目の決算期変更が進行中の可能性を[[RCAT-TRIPLE-
  FISCAL-CHANGE-SUSPECTED-1]]として別途登録済み（2026-08-01、優先度：中、
  10-K原本での個別確認が未着手）。
- **AVGO**: bucketingへの実害は引き続きゼロ。真のFYE（10月末）との
  不一致自体は[[PERIOD-LENGTH-VALIDATION-GAP-1]]で背景要因として発見済み
  のまま、個別の10-K確認は未着手。

## 2026-07-31（完了）

### ✅ [PERIOD-LENGTH-VALIDATION-GAP-1] parser.pyのFLOW型フィールド抽出に期間長検証が構造的に欠落（2026-07-31完了）
**優先度:** 高
**分類:** バグ / 一次データ抽出ロジック
**登録日:** 2026-07-31
**完了日:** 2026-07-31
**発見:** GrossProfitバックフィル調査から派生した横断調査（チャット記録）

#### 内容（根本原因）
common/sec_data/parser.pyのFLOW型（duration型）フィールド抽出には2経路あった。
`_extract_values_merged()`（`MERGE_ALL_TAGS_FIELDS` = revenue/selling_and_
marketing/depreciation_and_amortizationの3フィールド限定）は、複数候補タグが
競合した場合のみ期間長(365日近傍)によるtie-breakを行っていた（2026-07-12
[[SEC-TAG-FICO-CPRT-1]]で追加）。一方、それ以外の全FLOW型フィールド
（gross_profit・net_income・operating_income・cost_of_revenue・research_and_
development・selling_general_and_administrative・operating_cash_flow・
capital_expenditure・stock_based_compensation）を処理する
`_extract_values_best_candidate()` → `_extract_single_key()`には、期間長検証が
一切存在せず、候補タグが単一しかない年度では91日程度の四半期エントリが
そのまま年次値として採用されていた。2026-07-12のSEC-TAG-FICO-CPRT-1修正は
同一企業(FICO/CPRT/LITE)のrevenueフィールドのみを対象にスコープを限定して
おり、根本原因（`_extract_single_key()`経路全体の期間長検証欠如）を解消して
いなかったことが判明した。

#### シミュレーション結果（実装前・全母集団オフライン検証）
105銘柄×12フィールドで実コード（`_detect_fiscal_end_month()`・
`_detect_fiscal_anchor_date()`・`determine_fiscal_year()`）を読み取り専用で
使用したオフラインシミュレーションを実施:
- 9フィールド（_extract_single_key()経由）: OK約9,700件・b:改善53件・
  c:新規欠損化138件
- 3フィールド（_extract_values_merged()経由、revenue/S&M/D&A）: OK約3,487件・
  b:改善13件・c:新規欠損化12件
- 新規発見: MRVL(gross_profit)・COHR/INTU(cost_of_revenue、INTUは12年連続)・
  VRT(revenue)・RCAT(depreciation_and_amortization)
- FICO/CPRT/LITE（SEC-TAG-FICO-CPRT-1対応済み）は無条件フィルタ適用後も
  regressionなしを個別確認済み

#### 実装内容
- `_extract_single_key()`: `field_name`引数を追加し、新設の
  `PERIOD_LENGTH_VALIDATED_FIELDS`（9フィールド）に該当する場合、年次候補
  として受理する際に期間長(340-380日)を必須条件とする
  （`_collect_own_data_annual()`の同種フィルタと同一パターン）。
  同じ`_extract_single_key()`を経由する他フィールド（eps_diluted/eps_basic・
  buyback・finance_lease_payments・shares_diluted/shares_basic）は
  シミュレーション未実施のため意図的に対象外のまま据え置いた。
- `_extract_values_merged()`: 候補受理時に、単一候補の場合も含めて無条件で
  340-380日フィルタを適用するよう変更（従来は複数候補競合時のtie-breakのみ）。
- 両者とも候補プールから範囲外エントリを除外する減算的(subtractive)設計とし、
  既存の正しいエントリを再評価・上書きする経路は追加していない。
- コミット: `e3723b3eb`（common/sec_data/parser.py・テスト）

#### 検証結果
1. pytest: 変更前442 passed/2 known failed（MSFT/NVDA、[[TEST-STALE-IV-1]]）→
   変更後446 passed/2 known failed（新規テスト4件追加、既知失敗数に変化なし）
2. 全105銘柄でannual_YYYY.jsonをフローズン入力（company_facts.json等は
   再取得せず既存ファイルのまま）で再パース・再生成し、git diffで新旧比較。
   実際に値が変化したのは28銘柄・194フィールドエントリ
3. b:改善66件（53+13件）はシミュレーション予測とおおむね一致。AVGO
   revenue 2016/2017の是正後値($13,240M/$17,636M)は10-K原本確認済みの
   真の年次値と完全一致。3件（AVGO net_income 2016・AVGO operating_income
   2017・VRT net_income 2016）はシミュレーションスクリプトの簡易tie-break
   近似が実装の詳細なタグ横断選定ロジック（複数バージョン10-Kの併存等）を
   完全に再現していなかったための予測誤差と判明したが、いずれも実装側
   （company_facts.json上の正規の365日前後エントリを採用）が正しい挙動
   であることを個別確認済み
4. c:新規欠損化150件中、実際にNone化されたのは128件（残り22件はELF分、
   下記「発見した別バグ」参照）。想定通りNoneとなることを確認
5. 上記b・c以外のエントリで値の変化がないことを確認（フローズン入力
   比較、git diffで無関係な差分なしを確認）。**例外: ELF(2015-2019、
   revenue/gross_profit/net_income等)で、本タスクとは別系統の既知バグ
   （ELFのfiscal_end_month自動検出が実際の決算月と異なる値を検出し
   年度ラベルが一括でずれる）との相互作用により、既存の正しい値が別年度の
   値に置き換わる「値の入れ替わり」を検知したため、ELF分のみ本コミットから
   除外した**（[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]として別途新規登録）
6. pytest全件・`report_consistency_check.py`ともにNG=0を確認
   （report_consistency_check.py: 変更前WARN=71件〈未確認21件〉→変更後
   WARN=68件〈未確認20件〉。件数減少のみで新規WARNの発生なし。減少分は
   本修正で除外されたエントリに起因するfyタグ裏取り不一致WARN等の解消）
7. STONKS SILOの自己修復ロジック（fetcher.py、gross_profit=None時に
   Revenue-cost_of_revenue逆算）を、HON/ABBV/CAT/KLAC/FICO/HEIの直近5年度で
   個別確認し、全て`gross_profit_derived=True`で正常にフォールバックする
   ことを確認。CPRTのみ2013-2015・2020年以降でフォールバックが発動しない
   ことを発見したが、原因はcost_of_revenue自体が本修正と無関係に
   既に欠損していたため（pre-existing、git HEAD時点で既にNone）と確認済み。
   TANUKI VALUATION側は、b/cの変化がgrowth.py::fcf_list[:5]の直近5年窓に
   該当するケースを確認したところ、RCAT 2024(stock_based_compensation、
   b:改善、$4,103,000→$3,609,000)のみがtanuki=trueの現役銘柄で該当。
   APGE 2022(net_income等、c:新規欠損化)はcik_lookup.csvでtanuki=false・
   status=candidateのため現状無関係。moat_score自体はannual_YYYY.jsonの
   gross_profitを参照しないため無関係。

#### データコミット
`d6d404016`（common/sec_data/data/、28銘柄・125ファイル）

#### 副産物として新規発見・登録した課題（未実装）
- [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]（優先度：高。ELFのfiscal_end_month
  自動検出誤りによる年度ラベル一括ズレ。本タスクの対象銘柄から除外）

## 2026-07-24（完了）

### ✅ [LAYER3-ASTS-DDOG-Q4-RESIDUAL-1] ASTS/revenue・DDOG/net_incomeで単独タグ計算値と旧normalized/の値が不一致
**優先度:** 低
**分類:** データ品質 / 要調査
**完了日:** 2026-07-24
**発見:** q4_implied.py単独タグ完結フォールバック実装時のTTM回帰

#### 内容
ASTS/revenue・DDOG/net_incomeで、新パイプラインの単独タグ計算値と
旧normalized/の値が不一致。DDOGは原因判明済み（ProfitLossタグ単独
では自己完結し45,594,000だが、旧データは断片エントリに起因する
別値119,563,000）。ASTSは未調査（前タスクで単独タグ計算値が旧
データと不一致と判明済みだが、どちらが正しいか未検証）。

#### 対応方針
未定。DDOGは旧データ側の断片エントリ（過去に発見した30日間の異常な
断片エントリ）が原因と推測されるため、新パイプラインの値が正しい
可能性が高い。ASTSは個別調査が必要。

【2026-07-24対応完了（判定のみ、コード変更なし）】両ケースとも
新パイプラインの値が正しいと判断した。

DDOG: 旧データ側の断片エントリに起因する値（119,563,000）であり、
新パイプラインの単独タグ自己完結値（45,594,000）が正しい。

ASTS: 旧normalized/の値（-2,394,000、マイナス売上高という会計的に
ありえない値）は、異なるタグ・異なる時点の値を混ぜ合わせた結果
生じたもの。新パイプラインの値（0）は単一タグ
〈RevenueFromContractWithCustomerIncludingAssessedTax〉が2023年
当初申告から2026年の比較年度再開示まで一貫して報告している値で
あり、内部整合性がある。プレレベニュー期の衛星通信企業という
事業実態とも整合する。SEC提出データ自体に矛盾（同一filing内で
異なるタグが異なる値を報告）が残るが、これは発行体側のタグ付けの
問題であり、パイプライン実装の対応範囲外と判断する。

両ケースとも、新パイプラインの値を正として採用する（追加のコード
修正は不要、既存のロジックが既に正しい値を算出している）。

---

### ✅ [LAYER3-DA-SBC-CANDIDATE-REGRESSION-1] depreciation_and_amortization・stock_based_compensationのTTM系列で一部銘柄がquarters_used減少
**優先度:** 低〜中
**分類:** データ品質 / 要調査
**完了日:** 2026-07-24
**発見:** フェーズC実装、TTM系列全体での105銘柄回帰

#### 内容
depreciation_and_amortization（82件）・stock_based_compensation
（62件）で、TTM系列全体の回帰差異を確認。多くは2022年前後の古い
期間でquarters_usedが増加（1→2、2→3等）する改善方向だが、BSY・PM
等一部銘柄で逆に減少するケースがあり、個別要因は未特定。

【2026-07-24再調査】オリジナル登録時の「quarters_used減少」6件
（DA: IOT・SOUN、SBC: CRM・NVDA・PM）は、その後の一連の実装
（欠落四半期逆算・is_implied優先順位変更）により全て解消済み。

残る37件（DA 28件・SBC 9件、対象: DA=ALAB/BSY/DDOG/ELF/FICO/JOBY/
PEP/SOUN/SPIR、SBC=APGE/BKNG/CART/ESTC/RCAT）は原因を特定できた:
source_tagが複数タグの"+"結合（例:
DepreciationDepletionAndAmortization+
AmortizationOfIntangibleAssets）になっているケースで、
_merge_normalized_by_priority()が四半期スロットと年次スロットを
それぞれ独立に別タグから採用してしまい、q4_implied.py（Q4逆算）が
性質の異なる2つのタグ由来の値を組み合わせて意味のない値を生成する
（BSYで実際にマイナスのQ4逆算値を確認）。今回の一連の実装とは
無関係の、以前から存在する別種の問題と判明。

【2026-07-24原因の再分割】37件は単一原因ではなく2種類に分かれる
ことが判明した。

**クロスタグ混入型（7銘柄: DA=ALAB/BSY/FICO/JOBY/SOUN、
SBC=BKNG/RCAT）**: 優先タグが年次申告のみ・四半期申告のみ停止する
等の理由で、年次キーと四半期キーが異なるタグを採用してしまい、
q4_implied.pyが異なるタグ由来の値を組み合わせて意味のない値を
生成する（BSY実例で確認済み）。パターンは「年次のみ停止」
（BSY型）・「完全逆転」（SOUN型）・「部分混在」（ALAB/JOBY/RCAT型）・
「完全分離」（FICO/BKNG型）等、複数バリエーションが存在する。

**原因未特定型（7銘柄: DA=DDOG/ELF/PEP/SPIR、SBC=APGE/CART/
ESTC）**: 年次・四半期とも一貫して同一タグを使用しており、
クロスタグ混入ではない別原因。未調査。

#### 対応方針
クロスタグ混入型（7銘柄）: q4_implied.pyに「Q4逆算に使う年次
エントリと3四半期エントリが全て同一source_tag由来であること」を
要求するガードを追加し、満たさない場合はQ4逆算をスキップする方針
（実データ確認済み: 7銘柄ともQ4に相当する期間の直接開示・他の
復元経路が存在しないため、ガード追加によりQ4値は「誤った値」から
「値の欠落」に変わる。コア原則〈各データポイントは正しいか、明確に
不正確とフラグされるべき〉に照らし、誤った値より欠落の方が望ましい
と判断）。_merge_normalized_by_priority()自体の作り替え（タグ
一貫性制約の追加）は、[[LAYER3-FALLBACK-STALE-TAG-PRIORITY-1]]が
解決した「優先タグ停止時の確実なフォールバック」を再度損なうリスクが
あるため見送る。

原因未特定型（7銘柄）: 別途投資調査が必要。

【2026-07-24対応完了】コミット5bae1e9f4（q4_implied.pyへの
同一source_tagガード＋単独タグ完結フォールバック追加、コミット
c3eefe31a時点の方針を実装）。当初のDA/SBC 37件のうち、実際の
クロスタグ混入型7銘柄（ALAB/BSY/FICO/JOBY/SOUN/BKNG/RCAT）は
ガードで正しく遮断された上、フォールバックにより多くが正しい値で
復元された。ガード追加の過程で、同一原因が他13フィールド・
43銘柄にも及ぶことが判明し（[[LAYER3-CROSS-TAG-YEARLY-QUARTERLY-
GENERAL-RISK-1]]の実例）、単独タグ完結フォールバックの追加により
88件中88件を復元（旧normalized/値との一致をサンプル5件で確認）。
TTM系列レベルで総不一致は本タスク開始前（426件）比-16件の410件に
正味改善。残る新規差異2件（ASTS/revenue・DDOG/net_income）は原因
特定済みの既知の残差として個別対応を検討する。

---

### ✅ [CAPEX-SIGN-UNNORMALIZED-1] CapEx符号不統一によるFCF過大表示（stock.html CF分析セクション・STONKS SILO表示専用フィールド）
**優先度:** 高
**分類:** バグ / TANUKI VALUATION / STONKS SILO
**完了日:** 2026-07-24
**発見:** `FIELD_DEFINITIONS.md`フェーズ4（AS-IS-071・AS-IS-157）、
2026-07-23登録

#### 背景
SEC XBRLの`CapEx`は報告企業により正負どちらの符号でも報告されうる。正式な
FCF計算（`common/sec_data/parser.py`）は`abs()`で符号を吸収済みだが、
stock.htmlの「キャッシュフロー分析セクション」（`loadCfData()`/
`renderCfCharts()`）はlatest.jsonを使わず`{ticker}_quarterly_normalized.json`
を直接fetchして`FCF = OCF - CapEx`をabs()なしで再計算しており、CapExが
負値の銘柄では実際より高いFCFを表示してしまう問題。同種の符号不統一が
STONKS SILOの表示専用フィールド`capex_annual`（AS-IS-157）、および
`financial_trend_calculator.py`（VECTOR_FIELDS/CapEx、2026-07-23の
フェーズ1調査で追加確認）にも存在していた。

#### 対応内容
根本原因である`normalized/`生成元（`normalizer.py`）でのCapEx符号
未処理を解消する方針で対応。表示側（stock.html/analyzer.py）を
個別に直すのではなく、データ生成元3箇所に符号正規化を実装した:

1. `normalizer.py::normalize()`: Q4逆算処理の後、最終出力直前の
   1箇所でCapExエントリの`val`にabs()を適用
2. `ttm_calculator.py::_build_q4_quarterly_entries()`: field_name
   引数を追加し、CapExのQ4逆算値にも独立にabs()を適用（保険的対応、
   [[RICE-TTM-CAPEX-SUM-SIGN-1]]参照）
3. `discover/stonks-silo/src/fetcher.py::_normalize_record()`:
   capital_expenditure抽出直後にabs()を適用

既存raw/キャッシュ（SEC EDGAR再取得なし）で105銘柄全数を検証した結果、
変更が生じたのはALAB/APGE/INTU/KULR/ONDSの5銘柄（事前調査で特定済みの
混在符号銘柄と完全一致）のみで、他100銘柄・CapEx以外の全フィールドは
完全にidempotent（無変更）であることを確認。TANUKI VALUATION側は
ALAB/INTU/KULR/ONDS（4銘柄、APGEは非対象）をpipeline.py --skip-riskで
再実行し、RICE値の変化（ALAB 5.882→5.861 / INTU 0.796→0.793 /
ONDS -1.362→-1.273、KULRはRICE算出不可のため無変化）とTANUKI SCORE
Classificationが4銘柄とも不変であることを確認済み。STONKS SILOの
実運用25銘柄はいずれも現状abs()適用前後で無変化（HONは非対象のため
`_normalize_record()`への直接呼び出しで動作のみ確認）。
`report_consistency_check.py` NG=0（全5銘柄）、pytest 442 passed
（既知のMSFT/NVDA IV式ミスマッチ2件は無関係）。

#### コミット
- `8843a51f2`（機能修正: normalizer.py/ttm_calculator.py/fetcher.py）
- `12452519e`（データ再生成: ALAB/APGE/INTU/KULR/ONDSのnormalized/ttm/
  latest.json等）

---

### ✅ [RICE-TTM-CAPEX-SUM-SIGN-1] TTM経由CapEx合算値の「合算後abs()」によるRICE投資強度の過小評価リスク
**優先度:** 中
**分類:** バグ / TANUKI VALUATION（RICE計算）
**完了日:** 2026-07-24
**発見:** CapEx符号処理実態調査（フェーズ1、CAPEX-SIGN-UNNORMALIZED-1
対応方針検討の過程）、2026-07-23登録

#### 内容
`ttm_calculator.py::calc_ttm_series()`が4四半期分のCapExを符号処理せず
単純合算してから`ttm/{ticker}_ttm_series.json`に保存し、この合算値が
`data_fetcher.py::build_rice_annual_shape()`（abs()なし）経由で
`rice.py`のRICE投資強度計算（Q値の構成要素）に渡っていた。4四半期の
うち1四半期でも符号が逆転していると、abs(合算値)が各四半期のabs()の
合計と一致せず、投資強度が本来より過小評価される問題。

#### 対応内容
[[CAPEX-SIGN-UNNORMALIZED-1]]の対応（`normalizer.py`側でのCapEx最終
出力時abs()）により、ttm_calculator.pyが受け取る個々の四半期CapEx値が
既に正規化された状態になるため、本問題は根本解消される。加えて保険的
対応として、`ttm_calculator.py::_build_q4_quarterly_entries()`に
field_name引数を追加し、CapExのQ4逆算フォールバック発火時にも独立に
abs()を適用した（normalizer.py側が該当end日付のQ4エントリを未生成の
稀なケースへの保険）。

実データ検証: 該当5銘柄（ALAB/APGE/INTU/KULR/ONDS）のTTM系列で、
CapEx/FCF値が影響を受けていたウィンドウ数はALAB 1・APGE 1・INTU 4・
KULR 1・ONDS 3（合計10ウィンドウ）。修正後は該当ウィンドウ全てで
CapExが正しい単四半期絶対値の合算に是正され、RICE投資強度
（avg_intensity）もそれに応じて是正された（詳細は
[[CAPEX-SIGN-UNNORMALIZED-1]]完了記録参照）。

#### コミット
- `8843a51f2`（機能修正）
- `12452519e`（データ再生成）

---

### ✅ [LAYER3-MISSING-QUARTER-IMPLIED-GAP-1] 優先タグ自体の四半期報告欠落により、より完全な次候補タグより誤った合算値が優先される
**優先度:** 低〜中
**分類:** データ品質 / 既知の制限
**完了日:** 2026-07-24
**発見:** layer3_builder.pyフォールバック方式修正時の回帰検証
（フェーズA、105銘柄×32フィールド全数スキャン）、2026-07-24登録

#### 内容
優先タグ自体が特定の四半期報告を欠落させ、隣接する四半期をまとめて
報告する場合（例: RCATのShareBasedCompensationがQ2を報告せずQ1→Q3に
直接ジャンプ）、次候補タグ（この場合AllocatedShareBasedCompensationExpense、
Q1/Q2/Q3すべて正常報告）がより完全なデータを持っていても、優先タグの
欠落由来の誤った値（Q2+Q3合算値がQ3として誤計上）がそのまま採用される。

これは今回修正した「クロスタグ混入」バグ（[[LAYER3-FALLBACK-STALE-TAG-
PRIORITY-1]]）とは異なる性質の問題で、layer3_builder.pyのモジュール
docstringに元々「未実装（フェーズAのスコープ外、既知の制限）:
normalizer.py::_build_missing_quarter_implied_entries()相当（Q4以外の
任意欠落四半期の逆算）」として明記済みだった。今回の回帰検証
（105銘柄×32フィールド＝3,360件）でRCAT/stock_based_compensationの
1件のみ発生を確認。

#### 対応方針
優先タグ内の完全性チェック（欠落四半期の検知）を追加し、欠落がある
場合は次候補タグの当該期間を採用する設計で対応。

【2026-07-24対応完了】コミットfd7473e57。優先タグから選んだエントリの
period_daysが標準的な四半期範囲（75〜100日、is_annual/is_implied除外）
から外れる場合、次候補タグの同一end_dateエントリにフォールバックする
完全性チェックを追加。正当な短期スタブ期間（APGE/CEG/FROG/LITE/VZ、
5件）は「全候補が範囲外の場合は最優先候補へフォールバック」する設計に
より、誤って除外されず維持されることを105銘柄×32フィールド全数で
確認済み。

---

### ✅ [LAYER3-FALLBACK-STALE-TAG-PRIORITY-1] layer3_builder.pyの「最初に見つかった非空候補採用」方式が古いタグを新しいタグより優先してしまう
**優先度:** 中
**分類:** データ品質 / バグ
**完了日:** 2026-07-24
**発見:** フェーズA（layer3_builder.py）105銘柄回帰レポート、2026-07-24登録

#### 内容
「最初に見つかった非空候補を採用」というフォールバック方式が、
直近データを持たない古いタグ（例: `Revenues`）を、より新しく実際に
使われているタグより先に拾ってしまう。IONQ等6銘柄のrevenueで確認
（既存コードのdocstringに既知の限界として言及はあったが、BACKLOG
未登録だった）。既存parser.py側の[[REVENUE-TAG-PRIORITY-FRAGILE-1]]
（`XBRL_MAPPING["revenue"]`の候補優先順位が脆弱）と同種の「Revenuesタグ
優先」パターンだが、発生箇所は別モジュール（本件はlayer3_builder.py
の新規フォールバック方式、[[REVENUE-TAG-PRIORITY-FRAGILE-1]]は既存
parser.py::`_extract_values_merged()`のtie-break規則）のため区別して
登録する。

#### 影響
候補リストの並び順次第で、実際には報告されなくなった古いタグの値を
誤って採用し続けるリスクがある。revenue以外のフィールドでも理論上
同型の問題が起こりうる。

#### 対応方針
「候補の中で最も直近のfiled日を持つタグを優先する」等、recency
考慮のフォールバック方式への変更が候補。

【2026-07-24対応完了】layer3_builder.pyの候補選択方式を、候補タグ
ごとに独立して正規化した系列を作ってからend_date単位でマージする
方式に変更（コミット925a02733）。IONQ/ASTS/CELH/RCAT/SOUN/WSTの
revenueが正しい現行タグ値に一致することを実データで確認済み。
short_term_debt（VZ・KLAC等）・stockholders_equity（AVAV・CPRT）・
research_and_development（LLY）でも同型の改善を確認。残るrevenue
diff 1件（SOFI）はticker_restrictions未移行という別件の既知事項
であり本タスクの範囲外。

---

### ✅ [LAYER3-ANNUAL-QUARTERLY-COLLISION-1] _merge_normalized_by_priority()がis_annualを区別せずend日付でグルーピングし年次エントリが四半期エントリを黙って上書きする
**優先度:** 高
**分類:** バグ
**完了日:** 2026-07-24
**発見:** eps_basic/eps_diluted unitバグ修正後の105銘柄再検証、
2026-07-24登録

#### 内容
`_merge_normalized_by_priority()`がend日付のみをキーにエントリを
グルーピングしており、`is_annual`（年次/四半期の別）を区別していない。
カレンダー年決算企業では、年次エントリ（is_annual=True、365日）と
「Q4単独開示」エントリ（fp='FY'だが実際は91日程度、is_annual=False）
が同一end日付（例: 2024-12-31）を持つケースがあり
（[[XBRL-TAG-KLAC-1]]と同型のパターン）、両方とも
`_is_plausible_standalone_quarter()`を通過するため、
`next((e for e in entries if ...), entries[0])`が単純にリスト先頭
（年次エントリ）を採用し、四半期エントリを黙って破棄する。

具体例（ABBV eps_basic、2024-12-31期）: 年次エントリval=2.40
（FY全体）が採用され、本来の四半期エントリval=-0.02（91日）が
破棄された。

【2026-07-24 波及範囲調査】105銘柄×28フィールド全数スキャンの
結果、16フィールド・16銘柄（ABBV/BBAI/CWAN/DELL/DOCN/ELF/ENTG/
FROG/HON/HQY/JNJ/LYFT/MSCI/SOUN/SPIR）・計234件で同一end日付の
年次/四半期衝突を確認した。内訳:
- パターンA（68件）: Q4_IMPLIED_FIELDS所属フィールドで、四半期
  エントリ喪失後もbuild_q4_implied_entries()が独立に同じ値を
  再計算し偶然「回復」していた（設計上の安全策ではなく偶然の
  内部整合性による）
- パターンB（156件、真の恒久的データ欠損）: eps_basic/eps_diluted
  全件、およびQ1〜Q3データ自体が欠落気味の銘柄（BBAI・SOUN・FROG・
  MSCI・LYFT等）でQ4逆算が発火せず回復されなかったケース
- パターンC（4件）: DELLのnet_incomeで、逆に四半期エントリが
  衝突に勝ち年次エントリが消失（回復機構なし）

既存の回帰レポート（1〜3回目）は各フィールドの「最新四半期のみ」を
突合対象としていたため、234件中231件（過去の四半期時点で発生）は
検出できていなかった。回帰レポート自体の検証範囲が不十分だった
ことも本件の一部として記録する。

#### 影響
eps_basic/eps_diluted unitバグ修正の再検証で11銘柄・22件
（ABBV/BBAI/DELL/DOCN/ELF/ENTG/HON/JNJ/LYFT/MSCI/SOUN）で発見された。
`_merge_candidate_entries()`を通る全フィールド（RPO・shares系除く）
に理論上該当し得るが、他フィールドでの実際の発生有無は未確認。

#### 対応方針
未定。年次/四半期の別をグルーピングキーに含める、または
`_is_plausible_standalone_quarter()`の判定を強化する等が候補。

【2026-07-24対応完了】コミットee1a5479a。
`_merge_normalized_by_priority()`のグルーピングキーを
end_dateのみから(end_date, is_annual)の複合キーに変更し、年次・
四半期エントリを別スロットに分離、同一end_dateでの競合自体を
解消した。105銘柄回帰で228件（重複排除後）全て解消を確認。
下流のQ4逆算処理も、以前は衝突で失われた四半期値を偶然回復して
いた箇所が、本来の四半期エントリをそのまま保持する形に是正された
ことを確認済み。なお[[QUARTERLY-CLASSIFY-PERIOD-NO-UPPER-BOUND-1]]
（DELL 181日エントリの誤分類自体）は本タスクでは未解消・別タスクの
まま（両エントリが保持されるようになったため実害は解消したが、
分類自体の正しさは別途対応が必要）。

---

### ✅ [LAYER3-Q4-IMPLIED-NOT-MIGRATED-1] layer3_builder.pyのQ4逆算がq4_implied.pyへ未移行のまま独自実装が残存していた
**優先度:** 中
**分類:** データ品質 / 設計不整合
**完了日:** 2026-07-24（本来はフェーズC実装前の現状確認調査時に
登録すべきだったが、登録漏れのまま2026-07-24中に対応完了。今回
BACKLOG_DONE.mdへ遡って直接登録する）
**発見:** フェーズC実装前の現状確認調査

#### 内容
[[Q4-IMPLIED-CALC-TRIPLICATION-1]]対応（フェーズB、コミット
a7678d16c）でnormalizer.py・ttm_calculator.py・
financial_trend_calculator.pyの3箇所をcommon/sec_data/q4_implied.py
へ集約したが、layer3_builder.py（フェーズAの新規コード）は独自の
Q4逆算実装（Q4_IMPLIED_FIELDS定数13フィールド・
build_q4_implied_entries()関数）を持ったままで、q4_implied.pyへの
移行が行われていなかった。両実装は適用フィールド範囲（13
フィールド vs 和集合15フィールド）・None安全性・CapEx符号処理の
扱いが異なっていた。

#### 影響
layer3_builder.pyの出力（store_v2/）は、finance_lease_payments・
buybackについてQ4逆算エントリが生成されておらず、q4_implied.py
経由の他3モジュールと整合しない状態だった。

#### 対応方針・完了記録
【2026-07-24対応完了】コミット76ff0cf1d。q4_implied.pyに
PascalCase/snake_case両対応を追加し、layer3_builder.py独自の
Q4逆算実装（13フィールドスコープ）をq4_implied.py呼び出しに置き換え。
finance_lease_payments（26銘柄）・buyback（65銘柄）で新規にQ4逆算
エントリが生成されることを確認（q4_implied.py側の既存生成数と完全
一致）。既存13フィールドはidempotent、CapEx符号の二重適用
（abs(abs(x))）も数学的に無害と確認済み。新規に発生した差異4件
（finance_lease_payments: APP/CELH/KULR、buyback: PLTR）は全て
比較対象normalized/側の未診断・不完全な状態に起因すると個別に実証
確認済み（KULRは自前逆算で新Q4値と完全一致、PLTRはnormalized/側の
start日付不整合という別の既知の限界が原因）。

---

### ✅ [LAYER3-GROSSPROFIT-BACKFILL-MISSING-1] normalizer.py相当のGrossProfitバックフィル機能がlayer3_builder.pyに未実装
**優先度:** 中
**分類:** 未実装機能 / データ品質
**完了日:** 2026-07-24
**発見:** フェーズC実装、TTM系列全体（複数年）での105銘柄回帰

#### 内容
normalizer.py::_calc_gross_profit()（Revenue−cost_of_revenueから
のGrossProfit逆算バックフィル）がlayer3_builder.pyに未実装
（フェーズA当初からモジュールdocstringに既知の制限として明記済み）。
TTM系列全体（最大6期・約5年分）での回帰確認で135件の差異として
初めて規模が判明した（単一四半期の最新値のみを見る従来の回帰
チェックでは見えなかった）。GrossProfitタグを直接開示しない期を
持つ銘柄（ABBV/HON等）で、古い期間のquarters_usedが減少する。

【2026-07-24実装前調査】store（Layer3）レベルでの欠落は508件・
30銘柄（TTM系列レベルの登録済み128件とは母数が異なる、1欠落四半期が
複数TTM anchorに波及するため単純な倍数関係にはならない）。

このうち11銘柄（BKNG/CDNS/CEG/CPRT/FLYW/INTU/JOBY/VST/VZ/V/XOM）は
revenueは存在するがcost_of_revenue候補タグ自体が1件も存在しない
ため、バックフィル実装後もGrossProfit欠落は解消されない見込み
（normalizer.py側の既存ロジックも同条件でスキップするため、この
制約は本タスク固有ではなく元の設計を踏襲した結果）。

#### 影響
フェーズC（ttm_calculator.py移行）の「値を変えない」という前提を
満たせない規模になっている。

#### 対応方針
_calc_gross_profit()相当のバックフィル機能をlayer3_builder.pyに
実装する。フェーズC完了の前提とするか、既知の制限として許容し
フェーズD以降に持ち越すかの判断が必要。

【2026-07-24対応完了】コミット11dc05627。
_calc_gross_profit()相当のバックフィル機能をlayer3_builder.pyに
移植（全フィールドループ完了後の後処理ステップとして実行、
"backfilled": Trueフラグ付与、既存エントリ非上書き）。508件・
30銘柄を正しくバックフィル、revenue−|cost_of_revenue|の単純差分と
508件全件完全一致。cost_of_revenue候補が存在しない11銘柄
（BKNG/CDNS/CEG/CPRT/FLYW/INTU/JOBY/VST/VZ/V/XOM）は想定通り
未解消のまま。TTM系列レベルの不一致は128件→10件に減少、残る10件は
既知パターン（SOFI: [[SOFI-TICKER-RESTRICTIONS-NOT-MIGRATED-1]]の
下流影響、MSCI: revenue/cost_of_revenue側のタグ陳腐化）で説明可能。
他フィールドへの影響ゼロ件、新規差異ゼロ件。

---

### ✅ [SOFI-TICKER-RESTRICTIONS-NOT-MIGRATED-1] TICKER_RESTRICTIONS（9銘柄）のticker_overrides機構がbuild_ticker_store()に未実装
**優先度:** 低
**分類:** 既知の制限 / 移行未完了
**完了日:** 2026-07-24
**発見:** 残る161件の内訳再確認調査

#### 内容
【2026-07-24調査で判明、範囲を全面訂正】config/
sec_concept_definitions.jsonのticker_overridesは、
build_ticker_store()のどこからも読み込まれておらず、実質的に
機能していない（MSFTのexcludeエントリを含め、config上に存在する
だけで一切適用されない）。

旧quarterly.py::TICKER_RESTRICTIONS（9銘柄: MSFT/APP/GOOGL/SOFI/
IONQ/KLAC/TER/V/NVDA）は、現状のfield/action/note（3キー）形式
では表現しきれない多様なパターンを持つ:
- 単純除外（APP: CapEx除外）
- 概念差し替え1件（IONQ/KLAC/TER/V: revenue_concept等1種類）
- 概念差し替え複数同時（SOFI: revenue・LTDebt・
  short_term_investmentsの3概念を同時差し替え）
- 期間・フォーム種別条件付き複数タグ合算（NVDA:
  cross_filing_tags、field/action/noteの枠組みと構造が根本的に
  異なる）
- 処理に影響しない警告ラベル（GOOGL: approximate/
  note_discontinuous、quarterly.py本体はこれらのキーを一切読んで
  いない）

実データ確認済みの影響（7銘柄）: APP（除外すべき低品質CapExデータが
素通し）・GOOGL（LTDebtが異常な急増パターン）・IONQ（revenue異常値、
[[LAYER3-IONQ-REVENUE-2022Q1-ANOMALY-1]]と同一原因と確認）・KLAC・
V（short_term_investments候補タグ全滅、0件）・TER
（short_term_investments 2021年で更新停止）・NVDA
（short_term_investments直近2期が欠落）。

副次発見: MSFTのconfig側エントリは`field: "revenue"`だが、元の
TICKER_RESTRICTIONSは`exclude: ["DA"]`であり、フィールドが一致
していない（移行時の誤り、意図不明）。

#### 影響
SOFIのrevenue（TTM含む）が正しい概念（金融機関向け
RevenuesNetOfInterestExpense）を使わず、通常のRevenues系タグに
フォールバックした値になる。

#### 対応方針
未定。少なくとも3種類の異なる仕組みが必要: (1)
ticker_overridesを実際に読み込み適用する機構自体の実装、(2)
単純除外・概念差し替え（単一・複数）に対応するスキーマ拡張、(3)
cross_filing_tags（期間・フォーム条件付き複数タグ合算）は既存の
候補タグ探索の枠組みと別構造のため個別設計が必要。approximate/
note_discontinuousは処理に影響しない注記のため、そのまま
コメント欄として引き継ぐのみでよい。

【2026-07-24対応完了】コミット46d05a542。ticker_overrides機構を
実装（extract_field_raw_entries()等にticker引数を追加、単純除外・
概念差し替え〈単一・複数同時〉・cross_filing_tagsの3パターンに
対応）。9銘柄中8銘柄（APP/IONQ/KLAC/V/TER/SOFI/NVDA/MSFT）で意図
通りの解消を確認、96銘柄への影響ゼロ。GOOGLは旧TICKER_RESTRICTIONS
自体がLTDebt向けの概念差し替え設定を持たず（approximate/
note_discontinuousは処理に影響しない注記のみ）、今回のスコープ外と
判断（新規オーバーライドの追加は別途要否を検討）。TTM系列レベルで
438件→426件に減少（IONQ・SOFI由来のrevenue/gross_profit異常値解消
分）、新規差異ゼロ。MSFTのconfig不整合（field: revenue→
depreciation_and_amortization）も本対応で是正済み。

---

### ✅ [LAYER3-IMPLIED-BLOCKS-FALLBACK-1] タグ単位の欠落四半期逆算が優先タグの空スロットを埋め、下位候補への実報告値フォールバックを阻害する
**優先度:** 中〜高
**分類:** バグ
**完了日:** 2026-07-24
**発見:** 欠落四半期逆算（先頭欠落パターン）実装時のTTM全体回帰

#### 内容
タグ単位・マージ前に適用する欠落四半期逆算が、優先タグの本来
空だったスロットに新規の逆算値（is_implied: True）を作り出すことで、
_merge_normalized_by_priority()が下位候補タグの実報告値へフォール
バックする経路を塞いでしまう。

具体例（ONDS selling_and_marketing、2024Q1）: 最優先タグ
MarketingAndAdvertisingExpenseはこの期間の単独値を元々報告して
おらず（移植前は空スロットのため次点SellingAndMarketingExpense
〈正しい報告値1,321,149〉へ自動フォールバックしていた）、移植後は
最優先タグに先頭欠落逆算による誤った派生値26,143（本来と無関係な
狭い"広告費"のみの値）が新規生成され、これがマージで採用されて
しまい、正しい下位候補へのフォールバックが起きなくなった。

#### 影響
対象87件の個別検証では検出されず、105銘柄TTM全体回帰で初めて
表面化した。他に同型の未検出ケースが存在する可能性がある。

#### 対応方針
未定。_merge_normalized_by_priority()の選択順序を「タグ優先順位が
先、is_implied状態は考慮しない」から「is_implied=Falseのエントリを
タグ優先順位に関わらず優先し、全候補がis_implied=Trueの場合のみ
タグ優先順位で選ぶ」という順序に変更する案が有力（実報告データを
派生値より常に優先する原則）。

【2026-07-24対応完了】コミットdb06d4299。
_merge_normalized_by_priority()の選択順序を、候補タグ優先順位より
先に「is_implied=Falseの実報告データを優先し、全候補が
is_implied=Trueの場合のみ派生値を採用する」というルールに変更。
ONDS selling_and_marketing 2024Q1で誤った派生値26,143ではなく正しい
報告値1,321,149が採用されることを確認。105銘柄TTM全体回帰で同型の
新規ケースはゼロ件、既存の関連修正（LAYER3-MISSING-QUARTER-
IMPLIED-GAP-1・LAYER3-ANNUAL-QUARTERLY-COLLISION-1）への影響なし。

---

## 2026-07-22（完了）

### ✅ [REVIEW-1] 外部AIレビュー指摘・要調査案件（2026-06-15 レビュー由来）
**優先度:** 低〜中（調査してから判断）
**分類:** データ品質 / 外部AIレビュー
**完了日:** 2026-06-15〜2026-06-16頃（本文記載の通り全件対応完了。
BACKLOG.mdからBACKLOG_DONE.mdへの記録移動は2026-07-22の棚卸しで実施）

#### 案件一覧（全件✅完了済み）
| 銘柄 | 指摘内容 | 対応状況 |
|------|---------|---------|
| SCCO | EPS quarterly 株数（163.7M）vs 実際（821M）が 5.1x 乖離 | 修正完了: CIK誤登録修正 + ProfitLossフォールバック追加 |
| NOW | adj_eps が SEC XBRL 値と乖離している疑い | 修正完了: 5:1株式分割未対応をBUG-NOW-SPLIT-1として修正 |
| MRVL | EPS 四半期データに異常値の可能性 | 修正完了: DTA認識NIをBUG-LYFT-EPS-1と同類処理で対応 |
| LMT | Q2 2025 EPS異常値、Adjustment_Delta=$0.0000 | 調査完了: プログラム損失はLIMITATION-1として記録、コード修正不要 |

#### 移動の経緯
BACKLOG.md本文に「状態: 全件対応完了・記録としてのみ残置（次回同種
レビュー時の参照用）」「案件一覧（全件✅完了済み）」と自己申告された
まま長期間BACKLOG.mdに残存していた。2026-07-22のBACKLOG.md全アクティブ
項目棚卸しで発見し、既存の完了タスク移動手順に従いBACKLOG_DONE.mdへ
全文移動した。

#### コミット
`6a9bc40d1e3d1068c466ff64d5605ca7a672d80c`

---

### ✅ [FCF-DIVERGENCE-SIGN-GUARD-1] raw_fcf<=0側の対称ケース対応（追補）
**優先度:** 高
**分類:** DCF信頼性判定ロジック / バグ
**完了日:** 2026-07-22

#### 内容
[[FCF-DIVERGENCE-SIGN-GUARD-1]]本体で「raw_fcf>0かつestimated_fcf<0」の
符号反転ガードを追加した際、対称ケース「raw_fcf<=0かつestimated_fcf>0」
（実績FCFが赤字/ゼロにも関わらず推定FCFが黒字）は、divergence_ratioが
raw_fcf<=0で無条件0.0に丸められ閾値判定（>=2.0/>=5.0）を通過できないため
未対応のまま残っていた（追加調査で発見・報告済み、詳細は上記エントリ内
「raw_fcf<=0ケースに関する追加調査」参照）。

追加調査により、raw_fcf<=0は現行のrevenue_floor設計
（`adjust_fcf()`、latest_revenue×8%のフロア）が`latest_revenue>0`の
限り必ず正値化するため、`latest_revenue<=0`（pre-revenue企業）でのみ
発生しうる構造であること、および現行監視銘柄100件（applied=True/False
問わず）中0件が該当することを確認済み。

#### 対応内容
`src/value/tanuki_valuation/calculator/adjustments.py`の
`estimate_fcf_from_eps()`に、前回の符号反転ガードと対称な
`raw_fcf <= 0 and estimated_fcf > 0`条件を独立追加。該当時は
divergence_ratioの値（常に0.0）に関わらず無条件で警告を生成。
メッセージは「実績FCFが赤字/ゼロにも関わらず推定FCFが黒字」とし、
前回の符号反転警告（「符号反転を検出」）と文言で区別できるようにした。
divergence_ratio自体は仕様通りraw_fcf<=0で0.0のまま変更していない。

#### 回帰テスト
`tests/test_divergence_sign_guard.py`に2件追加（計6件）:
- raw_fcf<0・estimated_fcf>0で、divergence_ratio=0.0のままでも
  divergence_warningが生成され「実績FCFが赤字」を含み「符号反転」を
  含まないこと
- raw_fcf=0（境界値）でも同様に警告が生成されること

`python -m pytest tests/ -q`: 442 passed, 2 failed（既知の
[[TEST-STALE-IV-1]] MSFT/NVDA、本修正と無関係）。新規失敗なし。

#### 100銘柄フローズン入力比較
`fcf_estimation`を持つ全100銘柄（applied=True/False問わず）を新旧ロジックに
再投入して比較 → **変化0件**（現行データにraw_fcf<=0が存在しないため
想定通り無影響）。

#### コミット
`99014218b676fa4e36e4babefaf9ce407cac8ba4`

---

### ✅ [FCF-DIVERGENCE-SIGN-GUARD-1] divergence_ratioの符号反転検知漏れ修正
**優先度:** 高
**分類:** DCF信頼性判定ロジック / バグ
**登録日:** 2026-07-21
**完了日:** 2026-07-22

#### 内容
`divergence_ratio`（estimated_fcf/raw_fcf）がraw_fcf>0の場合のみ符号付きで
計算されるため、conversion_rateが負値等の理由でestimated_fcfの符号が
raw_fcfと反転すると、divergence_ratioの絶対値が小さいまま（例: -0.9）
既存の閾値判定（>=2.0/>=5.0）を満たさず、divergence_warningが生成されない
まま素通りする問題があった。FCF-CONVRATE①③調査時のVSTシミュレーションで
発見（divergence_ratio=-0.45が閾値2.0を満たさず無警告になることを確認）。

divergence_warningが空だと、DCF_Reliability Policy Bの`eps_invalid`判定
（`pipeline.py:465`）・stock.html/admin.htmlの警告表示の両方が「無警告＝
正常」として素通りする構造だったため、符号反転時にIVが無警告でマイナス値
になり得るリスクがあった。

#### 対応内容
`src/value/tanuki_valuation/calculator/adjustments.py`の`estimate_fcf_from_eps()`
（divergence_ratio/divergence_warning生成箇所、旧1723-1738行目付近）に、
既存の閾値判定（>=2.0中乖離／>=5.0高乖離）とは独立した条件として、
`raw_fcf > 0 and estimated_fcf < 0`（符号反転）を追加。該当時は
divergence_ratioの絶対値に関わらず無条件で高乖離警告扱いとし、
メッセージに「符号反転を検出」の文言を含めて既存の高乖離警告と区別できる
ようにした。

#### 消費箇所への影響確認
- `pipeline.py:465` `_calc_dcf_reliability_policy_b()`の`eps_invalid = bool(fcf_est.get("divergence_warning"))`:
  符号反転ケースをシミュレーションし、`eps_invalid=True`→Policy B判定
  `LOW`に正しく倒れることを確認済み
- `stock.html:799`/`admin.html:2647`: いずれも`divergence_warning`の
  非空判定（truthy check）のみで、文言をregexで再パースする箇所は
  存在しないことを事前確認済み。新しい警告文言もそのまま黄色バッジ・
  警告リストに反映される

#### 回帰テスト
`tests/test_divergence_sign_guard.py`新規追加（4件）:
- 符号反転時（raw_fcf>0, estimated_fcf<0）にdivergence_ratioの絶対値が
  閾値未満でもdivergence_warningが非空になり「符号反転」を含むこと
- 符号反転なし・閾値未満（従来通り無警告）の回帰確認
- 符号反転なし・中乖離（>=2.0）/高乖離（>=5.0）が従来通り警告し、
  かつ「符号反転」の文言を含まないことの回帰確認

`python -m pytest tests/ -q`: 440 passed, 2 failed（既知の[[TEST-STALE-IV-1]]
MSFT/NVDA、本修正と無関係、修正前から存在）。新規失敗なし。

#### 59銘柄（fcf_estimation.applied=True）フローズン入力比較
既存のlatest.jsonをそのまま新旧ロジックに再投入して比較。59銘柄全件で
`raw_fcf>0 and estimated_fcf<0`に該当する銘柄は0件のため、
divergence_warningの分類（無警告/中乖離/高乖離）は全銘柄で変化なし
（本番のconversion_rate設定に負値が存在しないため、今回のガード追加は
現行データには影響しない設計通りの結果）。

#### raw_fcf<=0ケースに関する追加調査（今回のスコープ外・報告のみ）
`divergence_ratio = estimated_fcf / raw_fcf if raw_fcf > 0 else 0.0`の
`raw_fcf <= 0`分岐（無条件で0.0に丸められ無警告になる別の盲点）は、
今回のガードでは対応していない。現行59銘柄では`raw_fcf<=0`に該当する
ケースは0件（2026-07-22時点）で実害未発現だが、構造的な盲点として
残っている。別タスクとして起票が必要（BACKLOG.md未登録、次回検討）。

#### コミット
`f6201ae04a4e242bbda2014b0f71ca2ef42911b6`

---

## 2026-07-20（完了）

### ✅ [ARCH-DATA-1] SECデータ正規化レイヤーの強化
**優先度:** 最高（2026-07-16、旧「高」からさらに格上げ — 「残課題④」参照）
**分類:** アーキテクチャ / 根本対策
**完了日:** 2026-07-19（RCAT型決算期変更検知の解消をもって全課題完了。BACKLOG.md→BACKLOG_DONE.mdへの記録移動は2026-07-20）

#### 格上げ理由（2026-06-19）
2026年6月の修正ログを通読すると、BUG-NETDEBT-6/PARSER-1/ANNUAL-FY-1/
BUG-EPS-UNIT-1/BUG-FOUR-1等、直近1ヶ月の主要バグの大半が「ロジックミス」
ではなく「想定外のSECデータ形への対応漏れ」だった。このレイヤーが薄いままだと、
新規ティッカー追加・既存ティッカーの決算更新のたびに同種バグが再発し続ける。
個別バグ修正は対症療法であり、ここへの投資が最も複利で効く。

#### 背景
79銘柄以上のXBRLデータ形式が不均一（旧タグ / 金融の狭いrevenue / 非12月決算期 /
上場直後の年次不足 / SPAC / IFRS等）で、計算ロジックの各所でデータの個性を
吸収している。これがエッジケースバグの温床。

#### 着手状況
- **PARSER-1（2026-06-13 完了）が本タスクの第一歩**: 年次キーを fy→end_date年 に変更し
  非12月決算企業の過去データ汚染を根治。exact_match優先ロジックを正規化層に導入済み。
- **BUG-NETDEBT-6（2026-06-13 完了）で同一時点原則を実装**: BS項目を同一filingから
  取得する規則を pipeline に導入済み。
- **ANNUAL-FY-1（2026-06-13 完了）が第三歩**: aggregate_annual の filing_date[:4] →
  fiscal_year フィールドベースに変更。20銘柄のIV誤計算を是正。
  ~~**残課題**: 年度判定が parser.py / extract_key_facts.py / aggregate_annual の
  3箇所に分散。~~ ✅ 2026-06-25完了（ARCH-DATA-1-FY）

#### 残りの方針
計算ロジックに渡す前に、SECの変種を統一フォーマットに均す
正規化レイヤーを厚くする。下流のエッジケースを構造的に減らす。
- BS項目はすべて同一決算期（同一 as-of 日）から取得する統一規則を敷く
  （BUG-NETDEBT-6で同一時点原則を実装済み。残課題は normalized JSON 自体の
   フィールド網羅性向上）
- 旧SECタグ・金融revenueタグ・非12月期等の吸収を正規化層に集約し、
  計算ロジックからデータ個性の処理を排除（PARSER-1で年度キー部分は対応済み）
- ~~normalized JSON に不足フィールド（ShortTermInvestments / 銀行移行後LTDebt 等）を補完~~
  ✅ 2026-07-13再調査で判明・完了。詳細はBACKLOG_DONE.md
  [ARCH-DATA-1-PREP-1] 参照（ShortTermInvestmentsは既に解消済みと確認、
  銀行移行後LTDebtはSOFI-DATA-1として恒久修正）
- ~~**年度判定の3箇所分散を単一関数に統合**~~ ✅ 2026-06-25完了
  （`common/sec_data/utils.py` に `determine_fiscal_year` を追加。parser.py・extract_key_facts.py・aggregate_annual の3箇所を統一）
- ~~**新規スコープ候補（2026-07-09追加）**: バグA・B（_estimate_ttm_operating_income()等の
  フォールバック実装がGrossProfit/RD/SM等複数フィールドの期末日整合性を検証せず
  暗黙に0円扱いしていた）~~ ✅ **既に解消済みと2026-07-13判明**。本追記の33分前、
  同日2026-07-09 19:54のコミット`1a8f5253d`「Moat Scoreフォールバックの2件のバグを
  修正（バグA・B）」で`_estimate_ttm_operating_income()`が`dict.get(end, 0)`の
  暗黙0円フォールバックから、GrossProfit/RD/SM3フィールドの共通end日
  （set intersection・4件未満ならNone）方式に修正済みだった。本追記時点で
  未反映のまま「新規スコープ候補」として残置されていた記録上の陳腐化。
  同種パターンの他箇所残存なし（grep確認済み）。

**年次データ正規化の3段階設計（2026-07-16確定）:**
今回（2026-07-16）のセッションで固まった年次データ正規化の設計方針。
[[FY52WEEK-BS-INSTANT-FACT-1]]事前調査で判明した未解決課題（残課題④
参照）を含め、以下の3段階でARCH-DATA-1本体として実装する。
1. ✅ **値の確定**: タグ＋日付をキーに正規化。同一キーで金額が食い違う
   場合は新しい報告書（filed日）を優先する（2026-07-16完了）
2. ✅ **年度ラベルの計算**: `determine_fiscal_year()`の月比較方式
   （month <= fiscal_end_monthによる片方向の年またぎ補正のみ）を廃し、
   企業ごとの決算アンカー日（月＋日）からの前後日数ウィンドウ判定に
   置き換える。12月決算企業でmonth<=12が恒常的にTrueになり判定が
   無効化する欠陥、および52/53週企業で決算日が前後にずれる際の
   片方向補正の限界を、両方とも解消する設計。（2026-07-17完了。
   詳細は下記「ステージ2完了」参照）
3. ✅ **裏取り**: 上記2で計算した年度と、XBRLの`fy`タグとの突き合わせを
   検証用の副次チェックとして実装（WMT型：企業側のfyタグ自体が誤って
   いるケースの検知用）。2026-07-17完了。詳細は下記「ステージ3完了」参照

**3段階設計は全て完了（2026-07-17）。**

#### 着手条件（成立・2026-07-09）
2026-07-09の新規5銘柄登録（RMBS/ENTG/TER/KLAC/LRCX）で
PARSER-ENTG-COMPYEAR-1・CHECK-QREV-FYE-1・XBRL-TAG-KLAC-1の
3件のデータ形起因バグが同一セッション内で同時発生し、着手条件
「次にデータ形起因バグが発生した時点で着手する」が満たされた。

追記: 2026-07-09同日中に、CHECK-QREV-FYE-1と同型の暦年グルーピング
バグがDILUTION-FYE-1（LRCX希薄化率誤算出）としてもう1件発見された。
report_consistency_check.py・pipeline.py双方の別々の箇所で同種の
「非12月決算企業を暦年ラベルでグルーピングする」実装が独立に存在し、
同じ欠陥を繰り返していたことになる。単発の偶然ではなく、正規化
レイヤーが薄いことに起因する再発パターンであることの裏付けとして記録する。

個別バグの掃討が一段落してから、ではなく、**次にデータ形起因バグが
発生した時点で着手する**（先送りを重ねるほど一本化コストが増えるため）。

**audit.py に追加すべき項目（SECデータ取得層）:**
- ~~yfinance株式数とSEC株式数の乖離が5倍以上の銘柄を WARNING 出力（2026-06-15 実装）~~
  **記録訂正（2026-07-13）**: audit.pyに実装されているのはAUDIT-SHARES-1
  （EPS Analyzer quarterly.json vs latest.json/DCFの希薄化株数比較、5倍閾値）で
  あり、「yfinance株式数 vs SEC株式数」の比較ではなかった。該当する
  yfinance-vs-SEC比較の実装は現状存在しない（本項目は元々の記述が誤りだった）。
- ~~10-Qに株式数タグが存在しない銘柄（UP-C構造等）を一覧表示~~ ✅ 2026-07-13完了。
  詳細はBACKLOG_DONE.md [ARCH-DATA-1-PREP-1] 参照

**着手条件に該当する新規事例（2026-07-10追記）:** [[SEC-TAG-FICO-CPRT-1]]
（完了・BACKLOG_DONE.md参照。FICO・CPRTの2020→2021年次売上高の不自然な
ジャンプ、当初はXBRL-TAG-KLAC-1と同型のタグ取得ミス疑いとして検出したが、
実際の根本原因は`_extract_values_merged()`の早い者勝ちマージだった）を検出。
「次にデータ形起因バグが発生した時点で着手する」という本タスクの着手条件に
該当する事例として記録する。

#### 設計メモ（2026-07-02・検討中）
- PREFLIGHT-CHECK-1とパターン判定ロジックを共有する設計が望ましい。
  「このティッカーはこの変種パターンに該当する」という判定を
  ARCH-DATA-1側で作れば、Step1後の正規化（事後）とStep1前の
  警告（事前）の両方から同じロジックを呼び出せる。別々に作らない。
- 未知パターン（カタログにない初見の異常）への対応として、
  異常検知→AIが仮説生成→一次情報で検証→カタログに追加、という
  学習ループが構想として挙がっている。詳細はPREFLIGHT-CHECK-1参照。

#### 着手前棚卸し・残課題①完了（2026-07-15）
着手前調査で、`contracts.py`（QUALITY-GATES-EPIC-1 Phase 3a）はARCH-DATA-1が
目指す「SEC変種吸収の正規化層への一本化」とは別レイヤー（型による構造検証の
み、変種吸収ロジックは含まない）と確認し、二重実装リスクなしと判断した。
既知SECデータ形バグ（PARSER-1・BUG-NETDEBT-1〜6・XBRL-TAG-KLAC-1系・
CHECK-QREV-FYE-1・DILUTION-FYE-1・LLY-CAPEX-STALE-1・BUG-EPS-ZERO-1/UNIT-1・
BUG-FOUR-1・SPLIT-AUTO-CHECK-1等20件超）を棚卸しし、正規化層（`tag_definitions.py`
等）への集約は部分的に進行済みだが、計算層（`pipeline.py`・`reader.py`）への
重複実装が①暦年グルーピング（trailing 370日窓）②BS項目「同一時点原則」の
2件残存していることを確認した。

上記①②を残課題①として一本化完了（コミット`4e4629a3b`・`60d44b2d8`）:
- ①`common/sec_data/utils.py::quarters_in_trailing_window()`に窓計算部分を
  共有化し、`quarterly.py::check_revenue_quality()`・`pipeline.py`
  （DILUTION-FYE-1）双方から参照する形に統一
- ②`reader.py::get_net_cash()`を正としてBS項目取得ロジックを一本化。
  調査の結果、単なるコード重複ではなくreader.py側だけがInsurance/Fintech
  セクターガードを適用しており、V（Visa）で実際に約$1.56Bの表示乖離
  （report.txt・TANUKI SCORE判定に使う値がDCF計算に使う値とズレていた）が
  発生していたことを実データで確認・是正した。副次的にSOUN（LTDebt=0の
  FY2024 10-K値が旧pipeline.py独自フィルタで誤除外されていたバグ）も是正。
  いずれもIntrinsic_Value自体・TANUKI SCORE分類には影響なし

残課題②（EPS Analyzer経路を正規化統合対象に含めるかのスコープ判断）は
[[EPS-ANALYZER-NORMALIZE-SCOPE-1]]として分離登録。残課題③（パターン判定
ロジックの実装、PREFLIGHT-CHECK-1と共有設計）は依然未着手（設計メモの
段階のまま）。

**軽微な残存（記録漏れの追加登録、2026-07-15）**: 残課題①の「最新
quarterly_*.jsonファイルを探す」処理パターンは、統合前は4箇所
（`reader.py`に2箇所・`pipeline.py`に2箇所）独立実装されていたが、
今回の一本化で`pipeline.py`側の1箇所を解消し3箇所に減った。残る
`pipeline.py`のDuPont分解（ROE = Net Margin × Asset Turnover ×
Financial Leverage）セクション内の1箇所は、Net_Debt算出とは無関係
（別の計算目的）のため今回のスコープ外としたが、将来
`reader.py::get_quarterly_range(ticker, quarters=1)`への統一で
解消可能。優先度は低く、着手条件なし。

#### 残課題③ 対応内容（2026-07-15完了・スコープ縮小）
着手前調査（2026-07-15）で、当初想定していた「PREFLIGHT-CHECK-1と共有する
汎用パターン判定カタログ」構想には2つの問題があると判明した:
1. `_extract_values_merged()`には候補タグ比較・競合検知の仕組みが一切なく、
   カタログの初期エントリとして使えそうな既存の「検知トリガー」も、
   SEC-REV-FINTECH-1/BUG-REV-SPAC-1型（revenue系タグ競合）については
   人間が10-K相当の文脈情報で正誤判断した一回限りの手動オーバーライド
   （`TICKER_RESTRICTIONS`）にすぎず、自動トリガーが存在しなかった
2. PREFLIGHT-CHECK-1が想定する新規登録時点（SEC EDGAR submissions API
   取得直後）の情報だけでは、revenue系タグ競合等の大半は「正誤確定」
   まではできず「リスクフラグ立て」止まりであり、精度未検証のまま
   共有カタログ化するのはリスクが高いと判断した

これを踏まえ、汎用カタログ構想は見送り、**revenue系タグ競合の実データ
検知**（`_extract_values_merged()`が静かに一本化してしまう競合を、
company_facts.json再読込により機械的に可視化する）に最小スコープを
絞って実装した（コミット`f05cae0ba`）:
- `common/sec_data/revenue_tag_conflict_check.py`新設。parser.py本体は
  無変更、`SECParser`の既存メソッド（`_detect_fiscal_end_month`/
  `_extract_single_key`/`_extract_values_merged`）を再利用し候補タグ
  一覧・年度判定ロジックを重複させない設計
- `update.py`のStep1完了直後（`check_revenue_quality()`の直後、4c.相当）
  に配線。新規のStep番号追加は不要だった（既存の4b.と同じ場所に
  差し込むだけで「Step1.5」相当のタイミングを実現できた）
- SOFI（$619.4M vs $3,613.4M、乖離5.8倍）・IONQ（$1,235.0M vs $11.1M、
  乖離111.0倍）の既知ケースを正しく再現することを確認
- 全100銘柄実行の結果、revenue系で14銘柄を検知（詳細は
  [[REVENUE-TAG-CONFLICT-SCAN-1]]参照。新規発見分の対応要否は別途判断）
- 自動修正は一切行わず、WARN出力（候補タグ名・各値・採用値の明示）のみ

残課題③はrevenue系タグ競合検知の実装をもって一区切りとする。パターン
判定ロジックの汎用カタログ化自体は、今回の知見（自動トリガーがほぼ
存在しない・登録時点情報では確定判定できないケースが多い）を踏まえ、
優先度を下げて次回以降に再検討する。

#### 残課題④（2026-07-16新規）
当初[[FY52WEEK-BS-INSTANT-FACT-1]]として個別調査した「BS項目
（instant fact）が52/53週バグの本人データ判定から対象外」問題は、
上記3段階設計で根本解決されるためARCH-DATA-1へ統合する
（[[FY52WEEK-BS-INSTANT-FACT-1]]エントリは削除し本項目への統合注記に置換）。

調査過程で、`_own_override_is_safe`の安全弁条件2
（`existing_end_dt.month <= fiscal_end_month`）が12月決算企業で
恒常的にTrueとなり機能しない欠陥を実データで確認した。実例:
CDNS FY2015のtotal_assets/revenueが、実際にはFY2014の値のまま
誤って保持されている（total_assets: 現状$3,209,556,000〈FY2014値〉、
正しくは$2,351,015,000。revenue: 現状$1,580,932,000〈FY2014値〉、
正しくは$1,702,091,000）。revenueは「完了済み」のFY52WEEK-
BUCKET-MISPLACE-1のスコープ内項目であったにもかかわらず、この
安全弁の欠陥により回帰が未解決のまま本番データに残っていた。
report_consistency_check.pyのCHECK-22（fyタグ衝突検知）はこの
ケースを検知しない（fy_collision_log.jsonにCDNSの記録なし）。

緊急の個別パッチ（安全弁条件2のみの差し替え）は見送り、根本解決
である上記3段階設計の実装をもって解消する方針とする（Koichiさん
判断・2026-07-16）。

また、「bsが空」のみを条件とした従来の対象件数カウント方法
（23件・53件）は、CDNS型（値は存在するが別年度の値が誤って
居座るケース）を検出できないことが判明した。3段階設計の実装後、
「フォールバック値と本人データ値の食い違い」チェックによる
全量再カウントが別途必要になる。

#### ステージ1（値の確定）完了（2026-07-16）
**背景**: `common/sec_data/parser.py`の`form == "10-K"`完全一致フィルタにより、
10-K/A（訂正申告）が全105銘柄中30銘柄で候補プールから完全除外されていた。
また同一(tag, end_date)が複数エントリで競合する場合、filed日を一切参照せず
「配列内で先に処理された方が勝つ」（実質的に古い方が残りやすい）ロジックに
なっていた。

**対応の技術的決定**: `_collect_own_data_annual`・`_extract_values_merged`・
`_extract_single_key`のform判定を`"10-K"`→`("10-K","10-K/A")`に拡張したが、
`_detect_fiscal_end_month`は対象外とした（10-K/Aを含めると最頻会計年度末月の
検出結果が変わりRCATで年度バケツ計算全体に波及する回帰を発見したため、
ステージ2の領域と判断し据え置き）。filed日タイブレークは「競合エントリの
少なくとも一方がform=="10-K/A"」の場合に限定し、10-K/A非関与の通常の比較
年度再掲同士（discontinued operations区分変更等で数字の意味が変わりうる）は
変更しない設計とした（AAPL/HON等の実データ検証で無条件適用の危険性を発見・
対処。実装過程で一度は無条件適用を試み509件の誤った差分を検出→設計を修正し
185件に収束させた）。

10-K/A候補プール化・filed日タイブレーク・出所メタデータサイドカー
（{bs,pl,cf,shares,other}_provenance）を実装（コミット`4587ee09e`）。
全105銘柄再生成（コミット`ba9927676`）し、事前検証の185件・18銘柄
（AAPL/ASTS/CELH/CPRT/DOCN/IONQ/JOBY/LITE/LYFT/QBTS/RDW/RKLB/RMBS/
SOFI/SPIR/TSLA/VRT/WST）と完全一致することを確認した。全件が実際に
公表されているSEC訂正事象（SPACワラント会計是正・QBTSのSR&ED税額
控除誤り・LYFTの再保険会計問題・AAPLのサブスクリプション会計早期
適用等）と整合することを一次情報で確認済み。pytest 309 passed
（既知2件除く）・report_consistency_check NG=0、いずれも変更前と同一。

5年トレーリング指標への影響が見込まれたDOCN/LYFT/QBTS/SPIRを個別
確認した結果、DOCN/LYFT/QBTSはROE平均が変化したもののalpha=0.0000
床打ちにより吸収されIntrinsic_Value・TANUKI SCORE分類とも完全不変。
SPIRのみR&D資本化経路の変化によりIntrinsic_Value_BASEが+7.6%
（$29.44→$31.68）変化したが、分類（PASS）は維持された。

ステージ2（年度ラベル計算のアンカー日ウィンドウ化・RCAT型決算期変更
検知）・ステージ3（fyタグ裏取り強化）は未着手。CDNS FY2015の
total_assets/revenue誤りはステージ1の対象外のため未解消のまま
（想定通り、ステージ2待ち）。

#### ステージ2（年度ラベル計算のアンカー日ウィンドウ化）完了（2026-07-17）

`determine_fiscal_year()`の「month > fiscal_end_month」片方向月比較を、
決算アンカー日（月+日）を中心とした前後日数ウィンドウ判定に置き換えた
（`common/sec_data/utils.py`）。

**実装内容:**
- `detect_fiscal_end_month()`: parser.py・extract_key_facts.pyに分散していた
  会計年度末月検出ロジックを統一（parser.py側の「10-K完全一致・10-K/A除外」を
  正本採用）。extract_key_facts.py側の独自実装（旧`determine_fiscal_year_end()`）
  は削除
- `detect_fiscal_anchor_date()`: 本人10-K annualエントリ（340〜380日）の
  end日から決算アンカー日（月+日）を検出
- `determine_fiscal_year()`: end_date.yearを中心に[year-1,year,year+1]の
  3候補年度でアンカー日との日数差を比較し最小の年度を採用。最小日数差が
  60日を超える場合はWARNログを出力し月のみ比較にフォールバック（安全弁）
- `_own_override_is_safe()`（parser.py）: 条件2の`no_crossing_needed`
  事前フィルタ（月のみ比較で12月決算企業では恒常的にTrueとなり機能しない
  欠陥があった）を廃止し、統一版`determine_fiscal_year()`の1条件に統一
- 呼び出し元8箇所（parser.py 4箇所・extract_key_facts.py 4箇所）に
  anchor_month/anchor_dayを追加

**JNJ/TDY型の追加発見と対応（実装中の検証で判明）:**
`detect_fiscal_anchor_date()`の初版（(月,日)完全一致の最頻値方式）で
105銘柄ネットワーク未使用比較を実施したところ、JNJ・TDY（決算日が
12月末〜1月頭を往復する52/53週企業）で、企業自身のfyタグと矛盾する
誤判定を新たに発見した（例: JNJのend=2013-12-29はJNJ自身がfy=2013と
申告しているが、アンカーが(1,1)と検出されたため2014と誤判定）。
BS項目（instant fact）は本人データ上書きの安全網対象外（残課題④/
FY52WEEK-BS-INSTANT-FACT-1系統、未解消のまま）のため、この誤判定が
そのまま年度ラベルに反映されてしまう。

原因はDec側（複数の微妙に異なる日）とJan側（別の複数の日）に得票が
分散し、たまたまJan側の1点が単独最多になったこと。年境界をまたぐ
循環距離（±7日）でクラスタリングし、最大クラスタの中央値（実在しない
場合はクラスタ内最頻値）を採用する方式に変更して解消した
（`_cluster_fiscal_anchor_candidates()`新設）。この経緯を反映し、
CHAT_RULESの「検証結果が依頼の前提と乖離した場合の一時停止」ルールに
従い一度立ち止まって報告・設計変更の承認を得てから実装した。

**検証結果:**
- 全105銘柄ネットワーク未使用新旧比較: 830件・16銘柄
  （ADBE/AVGO/CAKE/CDNS/CEG/DELL/ELF/IOT/JNJ/KLAC/LITE/MRVL/MSCI/
  RDW/TDY/WST）に差分。CDNS FY2015のtotal_assets $3,209,556,000→
  **$2,351,015,000**・revenue $1,580,932,000→**$1,702,091,000**が
  ステージ1完了時点から引き継いでいた既知の誤りとして正しく是正されたことを
  一次情報（company_facts.json内のown data・reportDate照合）で確認。
  AVGOの真のFY2025値がbucket 2026という存在しない年度に誤配置されていた
  問題も是正（是正に伴い`common/sec_data/data/AVGO/annual_2026.json`が
  化石ファイル化したため削除。`save_parsed_data()`に古い年度ファイルの
  自動削除ロジックがない既知の構造的問題〈IOT/AVGO/MRVLの化石ファイル
  問題と同型〉に起因し、今回もCLAUDE Code側で手動削除が必要だった）
- JNJ/TDYはクラスタリング方式変更後、企業自身のfyタグと一致する年度に
  是正されることを確認（是正範囲は52/53週の年境界越えが実際に発生する
  年度のみに限定され、修正前の(1,1)アンカー版で発生していた「ほぼ全年度が
  1年ずつシフトする」広範な誤判定は解消）
- 影響16銘柄でTANUKI VALUATIONを再生成し、TANUKI SCORE分類
  （BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）は全銘柄で不変を確認。
  Intrinsic_Value_Per_Shareは AVGO +10.6%・JNJ +2.8%・TDY -1.4%
  変化（他13銘柄は不変）
- pytest 325 passed（既知2件除く、新規16件のアンカー日ウィンドウ境界
  テストを`tests/test_fiscal_year_anchor_window.py`に含む）・
  report_consistency_check.py NG=0/WARN=41（変更前と同一）

**未解決のまま残る点（ステージ3以降）:**
- RCAT型決算期変更検知（企業が実際に決算期を変更したケースと、単なる
  52/53週の測定誤差との区別）は本ステージのスコープ外で未着手
- 残課題④のBS項目（instant fact）本人データ判定除外は未解消のまま
  （ステージ3のfyタグ裏取り強化、または別途の安全網設計が必要）

#### ステージ3（fyタグ裏取り）完了（2026-07-17）

ステージ2で計算した年度ラベル（`determine_fiscal_year()`の結果）と、
XBRLの`fy`タグとの突き合わせを検証用の副次チェックとして実装した
（WMT型：企業側のfyタグ自体が誤っているケースの検知用）。

**実装内容:**
- `parser.py`: `{bs,pl,cf,shares,other}_provenance`サイドカーに
  生XBRL `fy`タグ値を`fy_tag`フィールドとして追加（既存の
  accn/filed/is_own_dataに追加するのみ、破壊的変更なし）。
  `_own_override_is_safe`内で`_collect_own_data_annual`の戻り値も
  `(val, end_date, accn, filed, raw_fy_tag)`の5要素に拡張し、
  fyタグ衝突・自然分離ケースでも本来の生タグを正しく追跡できるようにした
- `_extract_values_merged`/`_extract_values_best_candidate`の両方に
  `fy_mismatches_out`引数を追加し、`annual_provenance`構築後に
  `fy_tag != 年度バケツキー`のエントリを検出して集約する仕組みを新設
- `_save_fy_tag_mismatch_log()`（`_save_fy_collision_log`と同パターン）で
  `common/sec_data/data/{ticker}/fy_tag_mismatch_log.json`に記録
- `report_consistency_check.py`にCHECK-23/WARN-23を新設。CHECK-22
  （同一fyタグへの複数本人end_date競合）とは独立した別軸で、
  「fyタグは単一だが値の年度バケツ配置自体がfyタグと異なる」CDNS型を検知する
- `config/warn_acknowledged.json`にWARN-23のNVDA・CAKEを一次情報検証済みとして事前登録

**設計変更の経緯（is_own_data=False側の除外、2026-07-17）:**
初版実装では`is_own_data`の値に関わらず全ての不一致を記録し、
`is_own_data=True`を「要確認」・`is_own_data=False`を「info」として
記録する2段階設計だったが、全105銘柄検証で**4,434件・105/105銘柄**
という実用に耐えないノイズになることが判明した。原因は、
`is_own_data=False`側の大半が比較年度再掲エントリ（例: 2008年の数値が
2011年の10-Kに比較年度として再掲載）由来であり、XBRLの`fy`タグは
「その数値がどの10-Kに載っていたか」というfiling側の属性でしかなく、
比較年度再掲エントリでは載っていた10-Kの年と数値が表す期間が
一致しないのが正常仕様（企業の申告ミスとは無関係）と判明したため。
CHAT_RULESの一時停止ルールに従い報告・設計変更の承認を得た上で、
`is_own_data=True`（本人データ自身のfyタグが実際に採用されてしまって
いるケース）のみを検知対象に限定し、severity区分（要確認/info）自体を
撤去して単一区分に簡素化した。

**検証結果:**
- 全105銘柄ネットワーク未使用検証: `is_own_data=True`限定後は
  **281件・10銘柄**（ADSK/AVAV/CAKE/COHR/CRM/FCX/FICO/HON/NVDA/WMT）
  に集約。281件を(ticker, end_date, fy_tag, computed_year)で重複排除
  すると**16件の distinct イベント**まで縮小し、1イベントあたり平均
  12〜26フィールドに重複計上されていたことを確認（同一10-Kから
  抽出される複数フィールドが同じ期間ズレを共有するため。フィールド
  単位ではなく期間単位で見れば実態はさらに小さい）
- NVDA・CAKEの2件は一次情報（NVIDIA自身の決算発表・Cheesecake Factory
  自身の決算発表）で検証済み: いずれもXBRL `fy`タグ側の誤りで
  computed_year側が正しいことを確認（NVDA: end=2013-01-27の売上$4.28Bは
  NVIDIA自身が「fiscal 2013」と公表・fyタグは2012と誤り。CAKE:
  end=2023-01-03はCheesecake Factory自身が「Fourth Quarter of Fiscal
  2022」と公表・fyタグは2023と誤り）。両者とも`_own_override_is_safe()`
  の安全弁によりcomputed_year経由の正しい値が本番データで既に採用されて
  おり実害なし
- 全105銘柄で新旧比較（annual_*.jsonの値そのもの）: **差分0件**を確認
  （fy_tagサイドカー追加のみで既存の値・TANUKI SCORE分類には一切影響しない）
- pytest 337 passed（既知2件除く、新規12件のfy_tag裏取りテストを含む。
  内訳: `tests/test_fy_tag_provenance.py`〈fy_tagサイドカー記録2件・
  不一致検知4件・CHECK-22非干渉1件〉、`tests/test_report_consistency_check.py`
  〈WARN-23検知4件・独立性確認1件〉）
- report_consistency_check.py: NG=0/WARN=51（stage2完了時点の41件から
  +10、影響10銘柄それぞれにWARN-23が1件ずつ追加。NVDA/CAKEは事前登録済み
  のため確認済み表示、残り8銘柄は🆕未確認として表示される）

**3段階設計（値の確定→年度ラベル計算→裏取り）が全完了。**

**未解決のまま残る点:**
- RCAT型決算期変更検知は引き続き未着手
- 残課題④のBS項目（instant fact）本人データ判定除外は未解消のまま
  （BS項目はstart日を持たないため`_collect_own_data_annual`の対象外
  であり、fy_tagサイドカーはフォールバック経路でのみ記録される。
  ステージ3の裏取りチェック自体はBS項目にも及ぶが、本人データ判定
  自体の拡張は別途必要）
- WARN-23の281件→16件イベントという重複計上は、(ticker, end_date)
  単位での集約表示に改善する余地があるが、今回のスコープ外として
  reportのみに留めた

#### WARN-23残り8銘柄の一次情報検証完了（2026-07-18）

NVDA・CAKE以外の未検証8銘柄（ADSK/AVAV/COHR/CRM/FCX/FICO/HON/WMT）
・計12件を、SEC EDGAR一次情報（10-K本文のカバーページ・自己言及文、
一部銘柄は`dei:DocumentFiscalYearFocus`タグ）で検証した。

**結果:** 12件全てでXBRL `fy`タグ側の誤りでcomputed_year側が正しい
ことを確認（NVDA/CAKEと同型の真陽性）。8銘柄すべて固定暦日決算
（1/31・4/30・6/30・9/30・12/31のいずれか）であり、52/53週型
（JNJ/TDY型の年境界往復）には該当しない別要因と判明。FCX/HONは
同一文書内でカバーページ本文と`dei:DocumentFiscalYearFocus`タグが
直接矛盾しており、filerの更新漏れ（コピペミス）と断定できる明確な
事例。AVAV/COHR/FICOは`dei:DocumentFiscalYearFocus`タグ自体も
fyタグと同じ誤り値で、filer側のXBRL全体が1年ズレていたケース。
全12件で`is_own_data=True`かつaccnが一次情報で特定した正しい10-Kの
accession numberと一致しており、本番データ（annual_*.json）は既に
正しい値を採用済み・実害なしを確認した。

`config/warn_acknowledged.json`に8銘柄分を追加登録し、WARN-23は
**全10銘柄の一次情報検証が完了**した。今後新規に発生するWARN-23
（未登録の新規ティッカー・新規end_date）は都度個別確認が必要。

#### 残課題④ 対応完了（2026-07-18）

BS項目（instant fact）向けの本人データ判定を新設した（コミット後の
`common/sec_data/parser.py`）。

**実装内容:**
- `_collect_own_data_instant()`新設: `_collect_own_data_annual()`から
  start_date必須フィルタ・期間長（340-380日）フィルタを除いた版。
  instant factのXBRL instant contextには元々start属性が存在しないため
- `INSTANT_FACT_FIELDS`（BS9項目: total_assets/stockholders_equity/
  total_liabilities/cash_and_equivalents/short_term_investments/
  long_term_debt/short_term_debt/current_assets/current_liabilities +
  rpo）を新設し、`_collect_own_data()`ディスパッチャで
  duration/instantを振り分け
- `_own_override_is_safe()`に`is_instant`引数を追加

**実装中に発見・修正した設計欠陥（VZ型）:**
`_own_override_is_safe()`の最初のショートカット
（`existing_end == own_end_date: return True`＝同一end_dateなら上書き
安全）は、duration factでは「同一期間を指す2候補タグは同じ概念の別名
表記（WMT Revenues/SalesRevenueNet等）」という前提が成立するが、
instant factではBS項目は同一会計年度内であれば異なる概念のタグ
（ShortTermBorrowings＝短期借入金とLongTermDebtCurrent＝長期債務の
流動化部分等）でもend_dateが機械的に一致するため、この前提が崩れる。
検証で全105銘柄再生成後の影響候補9銘柄をTANUKI VALUATION再生成した際、
VZのshort_term_debtがxbrl_keys優先順位1位のShortTermBorrowings本人データ
$441M（真の値は$18,618M＝LongTermDebtCurrent側）に誤って上書きされ、
Net Debtが約$18.6B過小評価されHOLD→WATCHへ分類が変化する回帰を検出。
`is_instant=True`時は同ショートカットをスキップしaccnベースの判定
（既に別の本人データが採用済みか）のみで安全性判定する修正を実施し解消。
LRCX・XOMでも同型の誤上書き（false positive）を検出・解消した。

**検証結果:**
- 全105銘柄ネットワーク未使用再パース: 修正確定後は
  value_to_value（既存の非NULL値が別の非NULL値に置換）**184件**・
  none_to_value（欠損補完）**262件**・value_to_none（データ消失）**0件**
  （VZ型バグ修正前は273件/89件が誤上書きによる偽陽性だった）
- CDNS FY2015のtotal_assets/revenueは変更前と同一値を維持
- NVDAのtotal_assets等、FY2011-2013が1年ズレた値のまま保持されていた
  同型の未検知事例を新たに発見・是正（生XBRLのaccn/reportDate照合で
  正当性を確認）。WMT/CRM/ADSK/ELF等30銘柄超で同型の是正あり
- pytest 380 passed（既知2件除く、変更前と同一）
- report_consistency_check.py: NG=0/WARN=51（変更前と同一。WARN-22/23
  の内訳件数はBS/rpo項目が衝突・裏取りログに新規参加し増加したが
  ティッカー単位のフラグ集合は完全一致）
- 実際のTANUKI VALUATION計算窓（`stockholders_equity`はROE 10年平均、
  `cash_and_equivalents`等/`rpo`は最新年のみ）と照合し、604件中
  影響候補は9銘柄・18件（ASTS/AVAV/BSY/ELF/KLAC/LRCX/VST/VZ/WST/XOM。
  うちKLAC/rpo系2件はrpo_config.json未登録のため実質対象外）に絞り込み、
  該当9銘柄（ASTS/AVAV/BSY/ELF/LRCX/VST/VZ/WST/XOM）を`pipeline.py
  --skip-risk`で再生成。**Intrinsic_Value_Per_Share・TANUKI SCORE分類
  ともに全9銘柄で完全不変（0.00%）**を確認（VZ型バグ修正前の中間状態では
  LRCX+2.26%・VZ+9.38%〈HOLD→WATCH〉・XOM+0.94%の変化が出ていたが、
  いずれも偽陽性でありバグ修正後は完全に解消）

**残課題④は解消。** ステージ1〜3（値の確定→年度ラベル計算→裏取り）に
続く4段階目としてBS/rpo項目の本人データ判定を実装完了。

**未解決のまま残る点:**
- RCAT型決算期変更検知は引き続き未着手

---

#### クローズ根拠（2026-07-20・BACKLOG_DONE.mdへ移動）

3段階設計（値の確定→年度ラベル計算→裏取り）・残課題①〜④、全て完了済み。
唯一「未解決のまま残る点」として繰り返し記録されていた**RCAT型決算期
変更検知**は、[[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]（2026-07-19完了・
本ファイル参照）としてARCH-DATA-1の枠組みの外に個別タスク化され、
CHECK-24/WARN-24の新設・`_is_boundary_collision()`/
`_fiscal_anchors_far_apart()`の実装をもって解消済みと確認した。
これによりARCH-DATA-1が抱えていた残課題は全て解消し、本エントリを
クローズする。

**※2026-07-31追記**: この完了はWARN-24による検知・ログ記録層のみを指す。
`_detect_fiscal_end_month()`等の抽出ロジック自体のera別対応は含まれておらず、
[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]調査で未解消と再確認した。

---

### ✅ [FY52WEEK-BS-INSTANT-FACT-1] BS項目（instant fact）が52/53週バグの本人データ判定から対象外で値がNoneに変化する
**状態:** [[ARCH-DATA-1]]へ統合済み（2026-07-16）・ARCH-DATA-1自体が2026-07-19完了・本ファイルへ移動（2026-07-20）

2026-07-16の事前調査で、本問題（duration検証を経由しないBS項目が
reportDate==end_date本人データ判定の対象外になり値がNoneに変化する
事象。DELL 2023・AVGO 2024・ADBE 2021・CDNS 2014/2020ほか）は、
[[ARCH-DATA-1]]が計画する年次データ正規化の3段階設計（値の確定→
決算アンカー日ベースの年度ラベル計算→XBRLタグ・reportDateとの
突き合わせ検証）で根本解決される対象と判断し、個別タスクとしては
クローズして[[ARCH-DATA-1]]へ統合した。調査過程で発見した
`_own_override_is_safe`安全弁の未解決の欠陥（CDNSでの実害確認含む）・
「bsが空」のみでは対象を網羅できない問題等の詳細は[[ARCH-DATA-1]]の
「残課題④」参照。

---

### ✅ [FY52WEEK-BS-NULL-SILENT-1] BS項目がNoneの場合`or 0`パターンで静かに$0として計算に組み込まれる
**優先度:** 高
**分類:** アーキテクチャ / データ品質ゲート
**登録日:** 2026-07-15
**完了日:** 2026-07-19（Phase A・Phase B Stage1〜3・Phase Cの全フェーズ完了。BACKLOG.md→BACKLOG_DONE.mdへの記録移動は2026-07-20）
**発見:** FY52WEEK-BUCKET-MISPLACE-1の実装過程

#### 問題
BS項目（total_assets/stockholders_equity/cash_and_equivalents等）が
Noneになった場合、コードベース全体で一貫して`or 0`パターンにより
静かに$0として計算に組み込まれることが判明した。None自体を検知して
警告する仕組みは存在しない。確認済みの該当箇所（最低3件、他に類似
パターンが存在する可能性あり）：

- `common/sec_data/reader.py:382`（Net Debt計算）
  `cash = bs.get("cash_and_equivalents", 0) or 0`
- `common/screening/dcf_validity_checker.py:173-176`（投下資本計算）
  `equity = bs.get("stockholders_equity") or bs.get("total_equity") or 0`
- `common/sec_data/report_consistency_check.py:532-539`（WARN-12
  Cash-STI期ズレ）
  `_ann_cash12 = _ann_bs12.get("cash_and_equivalents") or 0`

複数年度を横断参照する箇所（`reader.py:172` `get_roe_avg_detail()`の
ROE平均計算等）では、該当年度がif文により静かにサンプルから除外
される（クラッシュはしないが、利用者からは「その年のデータが
減った」ことが一切分からない）。

これは「各データポイントは正しいか、明確に信頼できないとフラグ
付けされているか」という本プラットフォームの根本方針に反する、
TRUST-SUMMARY-EPIC-1が対象とする領域の具体的な一事例。
[[ARCH-DATA-1]]（旧[[FY52WEEK-BS-INSTANT-FACT-1]]、2026-07-16に
ARCH-DATA-1へ統合済み）の修正が入るまでの間、及び今後同種の
None化が他の原因で発生した場合全般に関わる、より広い構造的リスク。

#### 対応方針
`or 0`パターンをNone検知＋明示的警告（report_consistency_check.py
のWARN体系への追加、または該当データを「信頼できない」フラグ付きで
返す設計）に置き換える。対象箇所の網羅的な洗い出しが必要（今回発見
した3箇所は氷山の一角の可能性）。

#### 着手条件
なし

ARCH-DATA-1の3段階設計とは独立に着手可能。ただしARCH-DATA-1の
実装後に新たに生まれるNoneパターン（値の確定・年度ラベル計算の
途中で生じうる欠落等）も本タスクの対象に含めて拾えるよう、
ARCH-DATA-1の設計・実装状況を横目に見ながら進めることが望ましい。

#### 網羅調査完了（2026-07-18）

対象箇所の網羅grepを実施した結果、BS9項目+rpoの参照は9ファイルに
限定されることを確認した。`or 0`パターン14件（うち`get_net_cash()`
起点が最重要、`_calc_g_fundamental()`・invested_capital計算〈RICEの
VC_Factor〉が高重要度）・複数年度横断除外パターン4件を一覧化。
全105銘柄の機械集計でNone率を実測し、total_assets/total_liabilities
が0%、stockholders_equity/current_assets/current_liabilitiesが1%、
cash_and_equivalentsが4%、long_term_debt/short_term_debtが36-37%、
short_term_investmentsが65%、rpoが35%（非SaaS銘柄は正常）と判明した。
None率がほぼ0-4%の6フィールド（total_assets/total_liabilities/
stockholders_equity/current_assets/current_liabilities/
cash_and_equivalents）はNoneがほぼ確実にデータ異常のシグナルである
一方、short_term_investments/long_term_debt/short_term_debtは
「真のゼロ」との判別が本質的に困難と判明したため、Phase A（前者6項目）
とPhase B/C（後者+rpo）に分離する方針とした。

#### Phase A完了（2026-07-18）

None率がほぼ0-4%の6フィールドについて、以下3経路の`or 0`パターンを
DuPont分解（`pipeline.py`）と同じ「除外」方針の明示的None検知に置換した:

- `reader.py::get_net_cash()`: `cash_and_equivalents`のNoneを`or 0`で
  ゼロ化せず保持。annual/四半期のいずれからも取得できなかった場合
  `available=False`・新規`cash_missing`フラグをTrueにし、
  `calculate_bs_adjustment()`側の既存フォールバック
  （`available=False`→`net_cash_per_share=0.0`）でBS補正自体を
  安全にスキップする設計とした（`financial_health`辞書にも
  `cash_missing`を伝播）
- `pipeline.py::_calc_g_fundamental()`: `stockholders_equity`/
  `total_equity`がいずれもNone、または`cash_and_equivalents`がNoneの
  場合、関数の既存パターンに倣いNoneを返す（除外）
- `pipeline.py::_calc_roic_wacc_ratio()`（RICEのVC_Factor）: 同様に
  Noneを返す。既存の`invested_capital<=0`→None→`VC_Factor=1.0`
  フォールバック安全弁は維持

`long_term_debt`/`short_term_debt`/`short_term_investments`（Phase B/C
対象）は今回変更していない。副次的伝播箇所（`adjustments.py`::
`calculate_bs_adjustment()`・`pipeline.py`の`financial_health`辞書
構築）は`get_net_cash()`側のavailable/cash_missingが正しく機能すれば
自動的に安全になることを確認済み（`calculate_bs_adjustment()`は
`available`を既に正しく参照していたため無改修）。`pipeline.py:2065-2069`
の`debt_cash_by_year`（死コード、構築後どこからも参照されない）は
今回のスコープ外として変更していない（削除要否は別途DEAD-CODE系で判断）。

`report_consistency_check.py`にCHECK-25/WARN-25を新設し、最新
annual_YYYY.jsonを直接参照して対象6フィールドのNoneを検知するように
した（WARN-24は[[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]向けに予約済み
のため欠番）。

**検証結果:**
- 全105銘柄のSECデータ層（annual_YYYY.json）は無変更（parser.py自体は
  今回改修していないため）
- WARN-25が新規に発生した銘柄: CPRT・GEV・HEI・SITM（いずれも
  cash_and_equivalents欠損、CASH-TAG-MISSING-1の既知欠落銘柄
  CAT/CPRT/ELF/GEV/HEIと符合）・SOFI（current_assets/
  current_liabilities欠損、total_assets/total_liabilities系は
  想定通り0件）・APGE（stockholders_equity欠損だがtanuki=falseで
  pipeline.py対象外のため実害なし）
- 計算経路（`get_net_cash()`・`_calc_g_fundamental()`・
  `_calc_roic_wacc_ratio()`）に実際に影響するのはAPGE除く4銘柄
  （CPRT/GEV/HEI/SITM）のみと機械的に特定し、`pipeline.py --skip-risk`
  で再生成して確認: Intrinsic_Value_Per_Shareは CPRT +2.37%・
  GEV +0.36%・HEI -4.72%・SITM 0.00%変化（TANUKI SCORE分類は
  4銘柄ともWATCHで不変）。HEIは以前`_calc_g_fundamental()`が
  annual cash_and_equivalents=Noneを$0として誤って投下資本計算に
  混入させていた（実際は四半期データで$210M保有）ことが根本原因と
  一次データで確認済み。無関係な制御群（AAPL）で再生成しIV完全不変
  （current_price等の市場変動ノイズのみ）を確認
- pytest 380 passed（既知2件除く、変更前と同一）
- report_consistency_check.py: NG=0/WARN=56（51→+5、上記5銘柄分の
  WARN-25新規発生。既存WARN種別への影響なし）

**Phase B/C（short_term_investments/long_term_debt/short_term_debt/rpo）
は未着手のまま残る。** 本タスクは完了扱いにしない。

#### Phase B Stage1完了（2026-07-19）

全179件のabsent銘柄（4フィールド×約45銘柄平均）をSEC EDGAR 10-K原本で
個別確認した結果、①候補タグ欠落・②生涯フェードアウト・③真の構造的
ゼロの3類型に分解できることが判明。うち①のうち銘柄別override不要で
安全に解消できる57件（41銘柄）について、`parser.py`のXBRL_MAPPINGへ
標準候補タグを追加し解消した。詳細・検証結果はBACKLOG_DONE.md
「[FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1]」参照。

残る2グループを新規BACKLOG登録した：
- [[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]（Stage2・5銘柄・銘柄別override設計要）
  → **2026-07-19: KLAC/TER/V/SOFIの4銘柄完了（BACKLOG_DONE.md参照）。
  NVDAのみ[[NVDA-STI-TAG-UNIDENTIFIED-1]]として分離継続**
- [[FY52WEEK-BS-FADEOUT-FALLBACK-1]]（Stage3・25銘柄・履歴フォールバック設計要）
  → **2026-07-19: 22銘柄分完了（BACKLOG_DONE.md参照）。除外3件（CSGP/
  KULR/RCAT）は[[BS-FIELD-FADEOUT-NONZERO-LAST-VALUE-1]]として分離継続**

Phase C（rpoの非SaaS銘柄True-negative群の扱い）はStage1のrpo分の
タグ追加で実質解消済みと確認。本タスク自体はStage2/3が残るため
引き続き完了扱いにしない。

---

#### クローズ根拠（2026-07-20・BACKLOG_DONE.mdへ移動）

全フェーズが完了済みのため本エントリをクローズする。

- **Phase A**（2026-07-18完了）: None率0-4%の6フィールド（total_assets/total_liabilities/stockholders_equity/current_assets/current_liabilities/cash_and_equivalents）を`or 0`パターンから明示的None検知＋WARN-25新設で解消。詳細は本ファイル上部の同日エントリ参照
- **Phase B Stage1**（2026-07-19完了）: 全179件のabsent銘柄を10-K原本で個別確認し、候補タグ欠落57件（41銘柄）をXBRL_MAPPING追加で解消。詳細は本ファイル「[FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1]」参照
- **Phase B Stage2**（[[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]、2026-07-19完了）: KLAC/TER/V/SOFIの4銘柄をticker別sti_concept overrideで解消。NVDAのみ資産クラス変化・当年度未タグ化という別型と判明し[[NVDA-STI-TAG-UNIDENTIFIED-1]]として分離、これも2026-07-19完了（`cross_filing_tags`機構で実装）
- **Phase B Stage3**（[[FY52WEEK-BS-FADEOUT-FALLBACK-1]]、2026-07-19完了）: 生涯フェードアウト22銘柄を条件ベースの履歴フォールバック（年数閾値なし）で解消。除外3件（CSGP/KULR/RCAT、最後の既知値が非ゼロで単純な$0フォールバック不可）は[[BS-FIELD-FADEOUT-NONZERO-LAST-VALUE-1]]として分離継続（未解決のまま）
- **Phase C**（rpoの非SaaS銘柄True-negative群）: Phase B Stage1のrpoタグ追加で実質解消済みと確認済み（本ファイル上部の同日エントリ参照）

残るのは[[BS-FIELD-FADEOUT-NONZERO-LAST-VALUE-1]]（3銘柄・別ロジック要設計）のみで、これは独立した新規タスクとして分離済みのため本エントリのクローズを妨げない。

---

### ✅ [GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1] HON成長率修正＋14銘柄のgrowth_sanity構造的ミスマッチ可視化
**優先度:** 未定→完了（HON修正は明確なバグ修正、14銘柄可視化はTRUST-SUMMARY-EPIC-1骨子②）
**分類:** データ品質 / TANUKI VALUATION / [[TRUST-SUMMARY-EPIC-1]]骨子①②適用
**登録日:** 2026-07-19
**完了日:** 2026-07-20
**発見:** [[GROWTH-SANITY-CLASS-SYNC-1]]（完了・本ファイル参照）verdict≠PLAUSIBLE
全32銘柄の原因分析

#### 骨子①: HONのバグ切り分け・修正
`segment_config.json`のHONエントリの成長率（加重平均8.5%）は、
2026-05-30の12銘柄一括登録コミット（`352630edce9d`、
`Co-Authored-By: Claude Sonnet 4.6`）でAIが機械生成した値で、以降
一度も見直されていなかった。各セグメント成長率（12%/6%/6%/8%）は
具体的な裏付け（決算資料・アナリスト予想の引用等）がなく、実績Revenue
CAGR（3yr=1.82%/5yr=2.79%）との乖離が業界平均比3.2倍・自社実績比3.1倍
に達していた。裏付けなしのAI生成値と判断し、実績CAGR水準（加重平均
2.6%）へ修正した（Aerospace Technologies 12%→3.5%・Industrial
Automation 6%→2%・Building Automation 6%→2%・Energy & Sustainability
8%→2.5%）。修正根拠をHONエントリの`note`フィールドに記載。

#### 骨子②: 14銘柄の可視化（構造的限界、FCF-CONVRATE②と同型パターン）
残る14銘柄（AMD/NVDA/ONDS/ASTS/BKNG/BROS/ELF/KULR/LLY/TER/XOM/ALAB/
IONQ/RCAT）は、いずれも登録時点からverdict=REVIEWのまま変化なし
（業界平均比2.5〜19.8倍）で、ハイパーグロース事業と成熟業種平均との
構造的ミスマッチと判断した。TERのみ業界平均比ではなく自社の直近実績
成長率比（4.6倍）での警告という別軸のパターンだったため、注記文言を
専用に分岐させた。

`src/value/tanuki_valuation/pipeline.py`にFCF_CYCLICAL_VOLATILITY_TICKERS
と同型の個別ティッカーリスト`GROWTH_STRUCTURAL_MISMATCH_TICKERS`を新設し、
report.txtの[4. 成長率根拠]セクション（signals/warnings表示直後）に
該当ticker限定の注記行を追加。`docs/value-monitor/tanuki_valuation/stock.html`
にも同一内容のJS側`GROWTH_STRUCTURAL_MISMATCH_TICKERS`セットを追加し、
`#growth-sanity-container`のsanityHTML内に条件付きバナーを追加（FCF-CONVRATE②
と同じPython/JS二重定義パターンを踏襲、共有configファイル化は今回のスコープ外）。
Classification（BUY/WATCH等）は一切変更していない。

#### 検証結果
1. HON修正後、growth_sanity.verdictがAGGRESSIVE→**PLAUSIBLE**に改善
   （想定通り）。signals: 「業界平均Diversified(2.7%)の1.0倍以内 ✅」
   「過去実績(3yr:1.8% / 5yr:2.8%)と整合 ✅」、warnings: 0件
2. 14銘柄すべてでreport.txt・stock.htmlに新規注記が正しく表示されることを
   確認（grep実測）。TERのみ「成長率警告は業界平均比ではなく自社の直近
   実績成長率比によるもの」の専用文言、他13件は共通文言
3. 対象外の全銘柄で変化ゼロ件: HON+14銘柄以外はファイル変更なし
   （`git status`で確認）。控えとして再生成したAAPL/MSFT/GOOGLは
   コード変更前後で完全に同一の結果（GOOGLの`tanuki_score`が
   HOLD→TRIMに見えたのは、git stashで本タスクのコード変更を一時的に
   除去した状態で再生成しても同じ結果になることを確認し、本タスクとは
   無関係な既存データ陳腐化〈他タスクでも複数回確認済みの既知パターン〉
   と判明したため実データの反映は行わず、コミット対象からも除外した）
4. Classificationは前後で完全一致（HON: HOLD→HOLD、14銘柄:
   ALAB=WATCH・AMD=WATCH・ASTS=WATCH・BKNG=BUY・BROS=WATCH・ELF=WATCH・
   IONQ=WATCH・KULR=PASS・LLY=WATCH・NVDA=BUY・ONDS=WATCH・RCAT=WATCH・
   TER=TRIM・XOM=WATCHのいずれも変化なし）。growth_sanity.verdictも
   14銘柄全てREVIEWのまま変化なし（純粋な注記追加のみで判定ロジック自体
   には一切影響しないことを確認）
5. pytest 426 passed（既知2件失敗のみ、新規失敗なし）
6. `report_consistency_check.py --fail-on-ng`: NG=0/WARN=69（変更前と不変）

#### TRUST-SUMMARY-EPIC-1への反映
段階1（成長率算出）についても骨子①（バグ切り分け）・骨子②（構造的限界の
可視化）の適用が完了し、段階2（FCF-CONVRATE②）と合わせて両段階で可視化
パターンが確立された。詳細はBACKLOG.md「[TRUST-SUMMARY-EPIC-1]」の
2026-07-20追記を参照。

---

### ✅ [FY-COLLISION-LOG-NONDETERMINISTIC-1] fy_collision_log.jsonの重複エントリを排除（対症療法・対象7銘柄）
**優先度:** 未定→低（対症療法のため実装コスト小・実害は診断ログの信頼性のみ）
**分類:** データ品質 / SECデータ基盤
**登録日:** 2026-07-19
**完了日:** 2026-07-20
**発見:** [[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]（完了・本ファイル参照）
実装前後比較のための全銘柄オフライン再パース実行中の副次発見

#### 調査で判明した訂正: 「非決定的」ではなく決定的なバグだった
登録時点では「複数回実行時に結果が変わりうる非決定的な要因」と推測していたが、
実装前調査（別セッション）でデバッグ計測により根本原因を特定した結果、
**完全に決定的なバグ**であり、同一company_facts.jsonに対して同一コードを
何度実行しても毎回同じ件数だけ重複することを確認した（3回連続実行で
`total collisions=33`が常に一致、増殖しない）。

根本原因: `_extract_values_best_candidate()`（`parser.py`）が、フィールドの
候補XBRLタグ（`xbrl_keys`）ごとに`_collect_own_data()`を独立に呼び出す
ループ（1221-1230行目）を持ち、同一の`collisions_out`リストに全呼び出しの
結果を追記する。複数の候補タグが独立に同一の(fy, end_dates)衝突を検出すると、
その候補タグ数だけ内容が完全同一のエントリが重複する（例: FICOの`rpo`は
候補タグ4個が全て同一のFY2019衝突を検出し4件重複）。値の採用ロジック
（`combined_own_data`の先着優先マージ）自体は正しく機能しており、実データの
正確性には一切影響していない。

実装前調査でAVAV/COHR/FICO/HONに加え、**CAKE/CRM/FCXの3銘柄も同型の
重複が新規に確認**され、対象は計7銘柄に拡大した。

#### 実装内容
根本修正（`_extract_values_best_candidate()`の候補タグループ自体の変更）は
値選択ロジックと密結合しておりリスクが高いため見送り、`_save_fy_collision_log()`
側での重複排除ガード（対症療法）を採用した。(field, fy, tuple(end_dates),
resolution)をキーに重複排除してから書き込むよう変更（既存の衝突検知ロジック・
`_extract_values_best_candidate`の候補タグループには一切手を加えていない）。
0件でも毎回書き込む既存仕様（化石ファイル対策）は維持。

`tests/test_fy_collision_log_dedup.py`を新設（4ケース: 完全同一エントリの
排除・field違いは別扱い・end_dates違いは別扱い・0件時も書き込み継続）。

#### 検証結果
1. FICOのrpo（4件→1件）ほか、事前調査で確認済みの重複ケースが全て
   正しく1件ずつに削減されたことを確認:
   AVAV 27→23件・CAKE 26→21件・COHR 31→25件・CRM 31→27件・FCX 27→22件・
   FICO 33→26件・HON 31→25件（いずれも減少数=重複していた分と正確に一致）
2. FICOで3回連続再パースし、件数が26件で完全に安定（増殖しないことを確認）
3. 全105銘柄（tanuki100+eps101の和集合103＋ENB/ZSの計105）で
   `parse_company_facts()`を再実行し、上記7銘柄以外で新規に件数が変わる
   銘柄がないことを確認（重複ゼロ件）。git stashによる前後比較で、
   7銘柄それぞれのannual/quarterly抽出結果（実データ・値の採用結果）が
   修正前後で完全一致することも確認
4. `report_consistency_check.py`のWARN-22表示件数が上記の正しい件数に
   変化したことを確認（NVDA等、元々重複がなかった銘柄のWARN-22件数
   〈22件〉は不変）。`--fail-on-ng`: NG=0/WARN=69（対象銘柄数・NG判定は
   不変、WARN-22の表示内訳のみが正しい件数に修正された）
5. pytest 426 passed（既知2件失敗のみ、新規失敗なし。新設4件含む）

---

### ✅ [SPLIT-REALTIME-GAP-1] 分割直後〜翌年10-K再掲までの恒久固着ギャップ解消（NVDA+新規発見AVGO/CPRT/WMT/LRCX/CELH/TSLA・KLAC事前登録、RCAT除外）
**優先度:** 低〜中
**分類:** データ品質 / EPS ANALYZER
**登録日:** 2026-07-12
**完了日:** 2026-07-20
**発見:** [[SPLIT-AUTO-CHECK-1]]（完了・本ファイル参照）実装検証時

#### 問題
`extract_key_facts.py`のfact選定ロジックを「filed日が最新のfactを優先」に
統一済み（SPLIT-AUTO-CHECK-1）だが、そもそも分割前後で比較年度として再掲される
機会が一度もない四半期（10-Qは前年同四半期のみ比較掲載するため、分割効力発生日
から1年以上前の四半期は将来も再掲されない）は、この修正でも是正できず、
分割前株数が恒久的に残存する（「先頭ブロックが分割前のまま恒久固着」型）。

#### 実装前調査で確定した方針
- **採用方式**: `split_history.yaml`への個別登録＋既存`apply_split_adjustments()`
  （`pipeline.py:140-205`、post-split四半期平均の1.5倍を閾値として遡及補正する
  既存ロジック）の流用。新規ロジック設計は不要と判明していたため。
- **対象拡大の経緯**: 当初はNVDA単独が対象だったが、実装前調査で全101銘柄
  （EPS ANALYZER対象）をyfinance実分割履歴とローカルキャッシュの
  `diluted_shares_used`時系列で横断スキャンした結果、NVDAと同型の
  「先頭ブロック恒久固着」パターンをAVGO/CPRT/WMT/LRCX/CELHの5銘柄でも
  確認（TSLAも軽微な1四半期分の該当を確認したが、背景説明への言及のみで
  具体的な登録・検証対象からは除外された）。
- **RCAT除外の判断根拠**: SEC XBRL company facts API（74件の
  `WeightedAverageNumberOfDilutedSharesOutstanding`全履歴）を直接確認した結果、
  RCATは分割関連のXBRLタグが一度も存在せず、2019年のRed Cat Holdings逆さ合併
  以降は株式分割を一切実施していないことを確認。往復変動に見えた「同一値が
  7四半期連続で繰り返される」パターンは、[[ASTS-SHARES-OSCILLATION-1]]
  （2026-07-13完了・本ファイル参照）で実装済みの「隣接する実四半期からの
  引き継ぎ」フォールバックが、RCAT自身の2019〜2024年の四半期単位XBRL開示欠落
  （年次のみ開示）を埋めた結果であり、既存ロジックが意図通り動作している
  だけと判明。加えてRCATは2024年に会計年度末を4/30→12/31へ変更
  （8ヶ月移行期をForm 10-KTで申告）しており、これが四半期区切り自体を
  変えていた（[[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]／
  [[FYE-BOUNDARY-COLLISION-UNCONFIRMED-1]]で追跡中の同一の実イベント）。
  split_history.yamlに登録すべき比率が存在しないため、本タスクから除外した。
- **CPRT分割日の一次情報再確認**: 実装前調査時点ではyfinanceの記録
  （2022-11-04・2023-08-22の2回、各2x）をそのまま報告していたが、実装時に
  SEC 8-K（Ex-99.1、CIK0000900075、2023-08-04付プレスリリース）を直接確認した
  結果、**実際の分割は2023-08-22（基準日2023-08-14・引渡2023-08-21）の
  1回のみ**と判明。2022-11-04は株主総会での授権株式数増加（400M→1,600M株、
  分割の前提条件）であり分割そのものではなかった。2022年のCPRT 8-K
  （四半期決算発表）にも分割の言及が一切ないことを確認済み。
- **KLAC事前登録の安全性確認**: KLACは2026-06-12に10-for-1分割済みだが、
  ローカルキャッシュの最新四半期（2026-03-31）はまだ分割前のため、
  post-split四半期データが0件。`apply_split_adjustments()`の既存コードを
  確認した結果、`post_split_shares`が空リストの場合は
  `print(...スキップ...); continue`で安全にno-opとなることを確認済み
  （防御的な分岐の追加は不要と判断）。

#### 実装内容
`config/split_history.yaml`に7銘柄を新規登録（既存NOW登録に追加）。
コード変更は`apply_split_adjustments()`本体には行わず（既存ロジックが
そのまま適用可能なため）、`tests/test_split_history_adjustments.py`を新設
（10ケース: 登録7銘柄それぞれの遡及補正・KLACのno-op・RCAT/未登録銘柄の
無変更を確認）。

#### 検証結果
1. **NVDA/AVGO/CPRT/WMT/LRCX/CELHの新旧比較**（`apply_split_adjustments()`を
   実際のローカルキャッシュデータに適用して確認、さらに全7銘柄についてSEC実
   データで`pipeline.run(ticker_filter=...)`を実行し永続化ファイルも更新）:
   - NVDA: 5四半期補正（2021-10-31/2022-05-01/2022-07-31/2022-10-30/
     2023-04-30、いずれも約2.49-2.54B→約24.9-25.4B）
   - AVGO: 3四半期補正（2022-07-31/2023-01-29/2023-04-30、約427-430M→4.27-4.3B）
   - CPRT: 3四半期補正（2021-10-31/2022-01-31/2022-04-30、約481-482M→約963-965M）
   - WMT: 3四半期補正（2022-04-30/2022-07-31/2022-10-31、約2.71-2.77B→約8.13-8.30B）
   - LRCX: 8四半期補正（2021-03-28〜2023-03-26、約135-145M→約1.35-1.45B）
   - CELH: 3四半期補正（2022-03-31/2022-06-30/2022-09-30、約75.8-78.4M→約227-235M）
   - いずれも補正後は前後の実測値と滑らかに連続する時系列になったことを確認
2. **KLAC**: `apply_split_adjustments()`が`post_split_shares`空リストで
   即座にスキップし、0四半期変更（no-op）であることを確認（永続化データにも
   数値上の変化なし、diffはAI分析コメントの非決定的な再生成分のみ）
3. **RCAT**: split_history.yamlに未登録のため`apply_split_adjustments()`が
   早期returnし、変更0件を確認
4. **対象外の全93銘柄**（EPS ANALYZER対象101銘柄−登録7銘柄、RCAT含む）:
   ローカルキャッシュに対し新旧の`apply_split_adjustments()`出力を全銘柄
   突き合わせ、変化ゼロ件を確認
5. pytest 421 passed（既知2件失敗`test_iv_formula.py`のMSFT/NVDAのみ、
   新規失敗なし。新設10件含む）
6. `tests/test_split_history_adjustments.py`を新設（既存
   `tests/test_extract_key_facts_split.py`はextract_key_facts.py側の
   fact選定ロジック回帰テストのため、pipeline.py側の
   `load_split_history()`/`apply_split_adjustments()`専用に別ファイルとした）

#### 副次発見（新規BACKLOG登録）
実装前調査で全101銘柄を横断スキャンした際、フォワード分割（比率>1のジャンプ）
のみを検知対象としていたため見落としていたが、BACKLOG_DONE.md
「Phase 2b-3完了（2026-07-12）」の記述を再確認した結果、KULR・SPIRの2銘柄が
リバース分割（1-for-8、yfinance確認済み）を経ており、ローカルキャッシュ上で
高い値→低い値への同型の恒久固着ブロックが存在する可能性を確認した（詳細は
[[SPLIT-REALTIME-GAP-REVERSE-1]]として新規登録）。本タスクのスコープ外のため
実装は行っていない。

#### 追記（2026-07-20・TSLA追加登録）
初回の登録依頼書作成時、TSLAがKoichiさん承認済みの対象6銘柄（AVGO/CPRT/WMT/
LRCX/CELH/TSLA）の1つであったにもかかわらず記載漏れとなっていたため、
追加登録した。

`config/split_history.yaml`にTSLA（date="2022-08-25", ratio=3, TSLA 3-for-1
株式分割）を追加。2021-06-30の1四半期（1,119,000,000→3,357,000,000）のみが
恒久固着していたため、この1四半期を遡及補正。

検証結果:
1. TSLAで新旧比較し、2021-06-30の1四半期が正しく補正されることを実データ
   （`apply_split_adjustments()`）およびSEC実データでの`pipeline.run()`実行
   後の永続化ファイルの両方で確認
2. 他の登録済み7銘柄（NVDA/AVGO/CPRT/WMT/LRCX/CELH/KLAC）・対象外銘柄には
   一切影響がないことを確認（`git status`でTSLA関連ファイルとsummary.json
   以外に変更なし）
3. pytest 422 passed（既知2件失敗のみ、新規失敗なし。
   `tests/test_split_history_adjustments.py`にTSLA用テスト1件追加）

---

### ✅ [MRVL-2019-2020-NULL-1] MRVLのannual_2019.json/annual_2020.jsonが両方ともrevenue/net_income=None
**優先度:** 中〜低
**分類:** データ品質 / SECデータ正規化
**登録日:** 2026-07-15
**発見:** [[FY52WEEK-BUCKET-MISPLACE-1]] IOT `_build_period_data`追加調査時の機械スキャン（副次発見）
**完了日:** 2026-07-20（原因調査により実害なしと確認、クローズ）

#### 内容（登録時）
MRVLの`annual_2019.json`・`annual_2020.json`が両方ともrevenue/net_income=None
であることを、隣接年度の完全重複を検出する機械スキャンで発見した。
`git log`で確認したところ、`annual_2019.json`の最終更新は2026-06-13時点
（ARCH-DATA-1-FYコミット`ab792d38b`＝2026-06-25より前）であり、
その時点で既に空だった。したがって[[FY52WEEK-BUCKET-MISPLACE-1]]で
特定した回帰バグ（determine_fiscal_year()導入コミットによる年度キー
シフト）とは無関係の別原因と判断される。

CLAUDE_CODE_START.mdの「調査中に発見した別バグの実装は別途依頼を待つ」
ルールに従い、その場での原因調査・修正は行わず、新規登録のみ実施。

#### 原因調査結果（2026-07-20完了）
**依頼時の前提は誤りだったことをまず記録**: 実ファイルを確認したところ
`annual_2020.json`は revenue/net_income とも正常に値が入っており
None ではなかった（pl/cf/shares すべて充足）。None だったのは
`annual_2019.json` のみ（`pl`/`cf`/`shares`/`other` が全て空、`bs` に
`stockholders_equity` が1件あるのみ）。

**確定した原因**: MRVLが2021年にCIK切替（旧1058057「MARVELL TECHNOLOGY
GROUP LTD」バミューダ籍 → 新1835632「Marvell Technology, Inc.」
デラウェア籍、Inphi買収に伴う持株会社再編）を経ており、`cik_lookup.csv`
は新CIKのみを登録している。新CIKの初回10-K（FY2022、accn
0001835632-22-000016、filed 2022-03-10）の損益計算書比較年度は
FY2020までしか遡らないため、FY2019の revenue/net_income タグは
新CIK配下のXBRL company facts に一切存在しない
（`RevenueFromContractWithCustomerExcludingAssessedTax`・`NetIncomeLoss`
とも end~2019-02-02 のfactが0件と一次情報で確認）。`bs.stockholders_equity`
のみ値が入っているのは、株主資本変動計算書のロールフォワード開始残高
（FY2019期末残高）が副産物的にXBRLへ開示されているため。

経済実体としてのFY2019データは旧CIK（1058057）配下にSEC上実在する
（10-K filed 2019-03-28, accn 0001058057-19-000010, period 2019-02-02、
EDGARで確認済み）が、現行システムは新CIKのみを参照しているため取得できない。

git履歴（初回コミット`09efb2553`時点から既にこの状態）・fy_collision_log.json
/fy_tag_mismatch_log.json（ともに空）から、正規化処理中に消失したのでは
なく初回生成時点からの構造的欠落と確認。マッピング側の候補タグ不足でも
正規化ロジックのバグでもない。

**横展開確認**: 「最古年度がBS項目の一部のみでPL/CFが空」という同型
パターンは86ファイル・ほぼ全銘柄で再現する普遍的な最古10-K比較年度
ウィンドウ境界の特性と判明。MRVLはCIK切替によりこの境界が異例に新しい
2019年に来ているだけ。CEG（2022年Exelonからのスピンオフ）も同型パターン
を示す実例として確認済み。

**結論**: 実害なし・マッピング側の不備でも正規化処理のバグでもないと
確認済みとしてクローズ。

#### 副次発見
CIK断絶による最古年度PL/CF欠落という構造的パターンをBACKLOG.mdに
[[CIK-DISCONTINUITY-OLDEST-YEAR-GAP-1]]として新規分離登録した
（対応方針〈旧CIK補完 or 現状維持〉の確定を含む、優先度：未定）。

---

### ✅ [KO-SPIR-CF-CAUSE-UNCONFIRMED-1] KO・SPIRのFCF乖離原因が一次情報不足で未確定
**優先度:** 未定
**分類:** データ品質 / TANUKI VALUATION / FCF-CONVRATE②派生
**登録日:** 2026-07-18
**発見:** [[TRUST-SUMMARY-EPIC-1]]FCF-CONVRATE②原因ベース分析（12銘柄個別調査）
**完了日:** 2026-07-20（10-K MD&A一次情報で原因確定、可視化注記まで実装完了）

#### 内容（登録時）
KO（Coca-Cola）・SPIR（Spire Global）のFCF乖離原因は、SEC XBRLの
構造化データ（`common/sec_data/data/{KO,SPIR}/annual_YYYY.json`）
からは特定できず、一次情報不足のまま未確定で残っていた。

- **KO**: NIが安定成長する一方（$10.7B→$10.6B→$13.1B）、OCFが2024年に
  -41%急落（$11.6B→$6.8B、2025年も$7.4Bと低水準継続）。SEC XBRLの
  `cf`セクションに税金支払・運転資本の内訳フィールドがなく（`other`
  フィールドも空）、原因を確定できなかった。10-K MD&A本文の直接確認が
  必要
- **SPIR**: 2025年NIが初めて黒字転換（+$51.3M）した一方、OCFは過去最悪
  （-$59.8M）という不整合が見られる。非現金・非経常項目（負債消滅益・
  ワラント再評価等）の可能性があるが、10-K注記での内訳確認が必要。
  同年Revenueも前年比-35%（$110.5M→$71.6M）と大幅減収しており、
  健全な事業サイクルとは言い難い

#### 原因調査結果（2026-07-20完了・10-K MD&A一次情報、確度：高）
- **KO 2024年OCF急落**: IRS移転価格税務訴訟（2007-2009年度分）の追徴
  課税$6.0Bを一括納付（2024年9月、控訴審係属中で還付可能性あり）。
  FY2024 10-K（accn 0000021344-25-000011）Note 12に明記
- **KO 2025年OCF低水準継続**: 2020年fairlife買収の偶発対価（業績連動
  マイルストーン）$6.1Bの最終決済（2025年3月）という、前年とは別の
  一過性項目。FY2025 10-K（accn 0001628280-26-010047）Note 17/18に
  明記。両年度の一過性項目を除いた正常化OCFは$12.8B(2024)/$13.5B(2025)
  相当となり、NIの成長トレンドと整合
- **SPIR NI/OCF乖離**: 2025年4月完了の海事(maritime)事業売却（Kpler
  Holding SAへ約$238.9M）に伴う非現金の売却益$154.3M（投資CF区分計上
  のためOCF算定上はNIから控除）が主因。FY2025 10-K（accn
  0001193125-26-116169）MD&Aに明記
- **SPIR 減収-35%**: 同じ海事事業売却による連結売上ベースの恒久的縮小
  （一過性ではなく構造的変化）

#### 対応（実装完了）
`FCF_TRANSIENT_ITEM_EXPLANATIONS`（KOは年度キー・SPIRはカテゴリキーの
ネスト辞書）を新設し、既存の`FCF_CYCLICAL_VOLATILITY_TICKERS`
（SITM/LITE）と同型の個別ティッカーリスト方式でreport.txt・stock.html
に可視化注記を実装（コミット`18cc4b6b7`）。DCF計算式・FCF算出ロジック
自体は変更なし、Classification判定にも影響しない。

#### 検証
- `report_consistency_check.py --ticker KO,SPIR`: NG=0（SPIRの既存
  WARN-26は[[BS-FIELD-NEWLY-MISSING-2026-1]]で追跡中の別件データ品質
  事象であり、本タスクとは無関係）
- `pytest tests/`: 426 passed / 2 known failed（MSFT/NVDA、
  [[TEST-STALE-IV-1]]既知の無関係な失敗のみ）
- KO/SPIRのlatest.json diffでIV・upside等の数値項目に影響がないこと、
  `FCF_TRANSIENT_ITEM_EXPLANATIONS`の参照箇所がpipeline.py・
  stock.htmlの2ファイル（KO/SPIRの2銘柄のみ）に閉じていることを確認済み

---

### ✅ [JOBY-STATIC-GROWTH-HARDCODE-1] JOBYのsegment_config.jsonにgrowth=0.15の静的値、FLOOR_HIT_REVIEW検知の対象外
**優先度:** 未定
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-19
**発見:** [[GROWTH-SANITY-CLASS-SYNC-1]]（完了・BACKLOG_DONE.md参照）
案B安全性検証の副次発見
**完了日:** 2026-07-20（原因確定・FLOOR_HIT_REVIEW検知拡張まで実装完了）

#### 内容（登録時）
`segment_config.json`を確認したところ、CART・JOBYは「General」100%
セグメントの`growth`値として直接`0.15`が静的に格納されていた
（`{"General": {"weight": 1, "growth": 0.15}}`）。これは
`calculator/growth.py::calculate_fcf_cagr()`のfloorパラメータとは
別の場所に埋め込まれた同一数値。

JOBYは`rev_cagr_3yr`/`5yr`/`g_fundamental`がいずれもNone（算出不能）だが、
`growth_source=="segment_weighted"`のため[[GROWTH-FLOOR-VERDICT-1]]の
FLOOR_HIT_REVIEW検知（`growth_source=="fcf_cagr"`限定）の対象外になっている。
CARTは`rev_cagr_3yr=13.6%`と15%に近い実績値があるため偶然の一致の
可能性があるが、JOBYは実績データが一切ないため、この0.15が実態を
反映した値なのか、過去のfloor/TTM override由来の残存値なのか不明だった。

#### 原因調査結果（2026-07-20完了、確度：高）
`segment_config.json`のgrowth=0.15は、`admin.html::fetchSegmentsForTicker()`
が新規銘柄登録時に機械的に書き込むテンプレートのデフォルト値であり、
JOBY固有の分析結果ではない。同時期に登録された他11銘柄（MRVL/RXRX/ARQQ/
SNDL/CIX/RDW/XNDU/AUR/VWAV/RCAT・CART）も登録コミットで一字一句同一の
値を取得していた（git log -pで確認）。admin.htmlの登録ツールは3箇所すべて
（CIK未設定時・セグメント自動抽出成功時・fetch失敗時）で一律0.15を
ハードコードしている。

JOBYは量産前段階の低ベース効果（revenue: 2023年$1.03M→2024年$0.136M→
2025年$53.4M、rev_yoy=69,873%）によりTTM注入の安全弁
（`_inject_ttm_for_general_segment`の`-50%〜100%`範囲チェック）で
実測値が棄却され、`growth_source=="segment_weighted"`のため既存の
FLOOR_HIT_REVIEW検知（`growth_source=="fcf_cagr"`限定）の対象外となり、
未検証のテンプレート値0.15がそのままDCF成長率として使われ続けていた
（`latest.json`の`components.high_growth_rate_used: 0.15`で確認済み）。
同一0.15テンプレートを保持する27銘柄中、全指標Noneで実効値が素通り
しているのはJOBYのみと横展開確認済み。

#### 対応（実装完了）
FLOOR_HIT_REVIEW検知を「`growth_source=="segment_weighted"`かつ
`rev_cagr_3yr`/`rev_cagr_5yr`/`g_fundamental`が全てNoneかつ
`recommended_g is None`」の条件にも拡張（コミット`ea21545d4`）。
0.15自体の妥当性判断（修正・上書き）は行わず、検知・可視化のみ実装。

全100銘柄シミュレーションで想定外候補CRWVを検出したが（同じく実測系
3指標None・segment_weightedだが、TTM実測値ベースのdecayモデルで
recommended_g=54.3%と正しく上書き成功済み）、`recommended_g is None`を
必須条件に追加して正しく除外し、最終的にJOBYのみが該当することを
確認した。

#### 検証
- JOBY: `verdict PLAUSIBLE→FLOOR_HIT_REVIEW`・`floor_hit false→true`、
  report.txt・stock.htmlに「実測データ不足のためテンプレートのデフォルト
  成長率（15%）が未検証のまま使用中 ⚠️」を表示確認
- CRWV: verdict/warnings/IVとも無変化を確認（除外条件が実データでも
  正しく機能）
- IV等数値項目への影響なし（git diffで確認、変化はgrowth_sanity関連
  フィールドのみ）
- `report_consistency_check.py`（全100銘柄）: NG=0件
- `pytest tests/`: 426 passed / 2 known failed（MSFT/NVDA、
  [[TEST-STALE-IV-1]]既知の無関係な失敗のみ、regressionなし）

#### 副次観察（実装対象外・記録のみ）
`report_consistency_check.py`のWARN 69件中19件が本タスク無関係の
未確認既存事象として残っている。個別の内容確認・要否判断は別途必要
（新規タスク化するかは次回検討）。

---

### ✅ [EPS-ANALYZER-NORMALIZE-SCOPE-1] EPS Analyzer独自SECデータ抽出パイプラインの正規化統合対象化の要否判断
**優先度:** 未定
**分類:** アーキテクチャ / SECデータ取得層
**登録日:** 2026-07-15
**発見:** [[ARCH-DATA-1]]着手前棚卸し調査
**完了日:** 2026-07-20（リスク評価→スコーピング調査→部分統合実装→本番データ再生成まで完了）

#### 内容（登録時）
EPS Analyzer（`src/value/adjusted_eps_analyzer/extract_key_facts.py`）は
ARCH-DATA-1が現在スコープとする`parser.py`/`normalizer.py`/`data_fetcher.py`/
`common/sec_data/`配下とは別の独立SECデータ抽出パイプラインであり、同種の
タグフォールバック・fact選定ロジックを独自実装している（`SPLIT-AUTO-CHECK-1`
完了記録で対象外と明記済み。SEC Company Facts APIを都度ライブ取得し、
ローカルraw JSONキャッシュも持たない。importしているのは
`common.sec_data.utils.determine_fiscal_year`のみ）。

これをARCH-DATA-1の正規化統合対象に含めるか、独立パイプラインとして
維持するかを判断する必要があった。

#### 方針判断
リスク評価・スコーピング調査（一次コード網羅照合）の結果、EPS Analyzer
全体を統一パイプライン配下へ完全統合はせず、以下の部分統合に限定した：
- **net_income候補タグリスト**: 統合する（既存の`tag_definitions.py::
  TAG_CANDIDATES`パターンに合流可能・影響範囲が特定しやすいため）
- **fact選定（filed日最新優先の部分）**: 共通プリミティブとして切り出す
- **revenue系タグ**: 統合しない。`tag_definitions.py`のdocstringで
  既に「統合対象外」（ティッカー別`revenue_concept`オーバーライドとの
  相互作用が複雑）と明記済みの設計判断を維持

#### 実装内容
1. **net_income統合**（コミット`609fbc1ac`）: `common/sec_data/
   tag_definitions.py::TAG_CANDIDATES["NET_INCOME"]`を3タグ→6タグに
   拡張（既存3タグの順序は維持、`extract_key_facts.py`固有だった
   3タグを末尾に追加）。`extract_key_facts.py`の
   `NET_INCOME_ANNUAL_TAGS`/`NET_INCOME_QUARTERLY_TAGS`（独自6タグ・
   独自順序）をこの共有定数の参照に置き換え、内部に存在した矛盾する
   第3の候補リスト（`net_income_priority`、四半期後段で無条件上書き）
   を削除
2. **fact選定共通プリミティブ**: `common/sec_data/fact_selection.py`を
   新設し`select_latest_filed()`を実装。`quarterly.py`
   （`_select_best_filing`・`_process_entries`）と`extract_key_facts.py`
   （希薄化後株式数のQ1-Q3選定）双方から参照するようリファクタ
   （parser.py本体の多段規則は今回対象外）
3. **全101銘柄本番データ再生成**（コミット`ecdb6b805`）:
   `python -m src.value.adjusted_eps_analyzer.pipeline`を
   `get_eps_tickers()`経由の全101銘柄で再実行

#### 重大な副次発見（実装過程で判明）
削除した`net_income_priority`は`'us-gaap:NetIncomeLoss'`を探すが、
そのキーは直前のループで意図的に除外されており`data`辞書に決して
現れないため、`NetIncomeLossAvailableToCommonStockholders`/
`AttributableToParent`を持たない銘柄（`NetIncomeLoss`と`ProfitLoss`を
両方申告する成熟企業に多い）では、常に`ProfitLoss`（非支配持分込みの
連結利益）へ意図せずフォールバックするバグを内包していた。
`NetIncomeLoss`はUS-GAAP XBRLタクソノミ上「親会社帰属利益」を表す
概念であり、EPS分析（1株当たり利益）の目的にはこちらが正しい。

実装前のスコーピング調査時点では「影響0件」と予測していたが、これは
検証方法の誤り（タグの新旧比較のみを見て、`net_income_priority`削除
自体の影響を見落としていた）と判明。実際に全母集団シミュレーション
（キャッシュデータ）で再検証した結果、**40銘柄・434四半期**に実害が
あることが発覚し、本番データでの再検証では**41銘柄**（ABBV/ASTS/
AVAV/BROS/BSY/CAKE/CAT/CDNS/CEG/COHR/CON/CPRT/CWAN/DELL/GEV/GTLB/
HEI/HON/IONQ/IOT/JNJ/KLAC/KO/LITE/MO/ONDS/PAYS/PEP/PLTR/PM/RCAT/RDW/
SCCO/SNPS/SPIR/TDY/TSLA/VST/VZ/WMT/XOM）が該当することを確認した
（キャッシュ時点との差は本番の最新SEC生データ反映によるもの）。
regressionではなく、既存の潜在バグの発見・是正と判断した。

#### 検証
- net_income統合の全母集団シミュレーション（キャッシュデータ）:
  想定外候補として発見された「40銘柄・434四半期」の実害を、
  ABBVの一次データ（`NetIncomeLoss`=$3,179M vs `ProfitLoss`=$3,180M等）
  で根本原因を確認
- fact_selection.py切り出し: `quarterly.py`は全105銘柄でリファクタ
  前後の出力が`generated_at`タイムスタンプ以外完全一致（0差分）。
  `extract_key_facts.py`の希薄化後株式数選定もnet_income変更を分離
  した状態で完全一致を確認
- 本番データ再生成後: `report_consistency_check.py --fail-on-ng`
  NG=0件（対象100銘柄、WARN=69件は既存の無関係事象）
- `pytest tests/`: 429 passed / 2 known failed（MSFT/NVDA、
  [[TEST-STALE-IV-1]]既知の無関係な失敗のみ、regressionなし）。
  回帰テスト`tests/test_extract_key_facts_net_income_selection.py`
  を新規追加（3件）

---

### ✅ [CWAN-SNPS-MA-DISTORTION-1] CWAN・SNPSのFCF乖離は大型M&Aに伴う一過性歪みと判明
**優先度:** 未定
**分類:** データ品質 / TANUKI VALUATION / FCF-CONVRATE②派生
**登録日:** 2026-07-18
**発見:** [[TRUST-SUMMARY-EPIC-1]]FCF-CONVRATE②原因ベース分析（12銘柄個別調査）
**完了日:** 2026-07-20（原因調査→対応方針転換→実装→全母集団シミュレーション
→全100銘柄再生成まで完了）

#### 内容（登録時）
CWAN（Clearwater Analytics）・SNPS（Synopsys）のFCF乖離
（divergence_ratio 2.19倍・1.47倍）は、いずれも大型M&A
（CWAN: Enfusion買収、SNPS: Ansys買収）に伴う無形資産償却（D&A）の
段階的増加・一過性の税務関連項目が原因と判明した（SEC XBRL実データ
`common/sec_data/data/{CWAN,SNPS}/annual_YYYY.json`で確認済み）。

- CWAN: D&Aが2024年$12.2M→2025年$85.5Mに急増（買収による無形資産
  償却ステップアップと整合）。2024年NIが$424.4Mの巨額プラスとなって
  いるのはUp-C構造特有の税務関連負債（tax receivable agreement）
  再評価等の一過性項目の可能性が高い
- SNPS: D&Aが2024年$295.1M→2025年$660.4Mに急増（Ansys買収の無形資産
  償却ステップアップと整合）。SNPSはsector_rationale適用済み9銘柄の
  1つのためconversion_rate自体は業種特性に基づき設定済みであり、
  実害は限定的

当初の対応方針（未確定）は「M&A起因の一過性歪みを認識した上で、生FCF
の複数年平均に統合初年度を含めるべきか除外すべきかの設計判断が必要」
だった。

#### 原因調査結果（2026-07-20・前提の転換）
一次データ確認の結果、当初想定は**前提不成立**と判明。CWANは統合年
（2025）にFCFがむしろ倍増（$69.1M→$164.3M）しており、生FCFが
「統合初年度に歪んで低く出ている」という前提自体が成立しなかった。

真因は`estimate_fcf_from_eps()`が参照する`adjusted_net_income`
（EPS Analyzer annual.json）に「買収・統合関連」カテゴリ（無形資産
償却費等、非現金・買収由来の加算）が含まれたまま、通常時の
conversion_rateをそのまま掛けていたため、実際のキャッシュフロー
創出力を超える推定FCFが算出されていたこと。生FCF側（実績）は正常
だった。

#### 対応（実装完了・コミット`479500ac1`）
`estimate_fcf_from_eps()`のestimated_fcf算出専用に、「買収・統合関連」
カテゴリの加算分を控除したAdj_NIを使う方式に変更。EPS Analyzer側
annual.jsonのadjusted_net_income自体・他の呼び出し元での参照値は
変更しない。新規フィールド`FCFEstimationResult.ma_addback_excluded`
で控除額を透明化。新規ticker_overrides・フラグは追加せず、EPS
Analyzerの既存の構造化されたカテゴリ分類を直接参照する設計とした。

#### 全母集団シミュレーション（実装前）
「買収・統合関連」加算を持つ銘柄は**47件**（CWAN/SNPS/SOFI/CELH以外に
AVGO/MSFT/AMD/MRVL/AMZN/META/NVDA/LLY/INTU/DELL/ADBE/APP/GEV/VRT/
ENTG/HQY/LITE/HEI/GOOGL/NOW/CSGP/PEP/ADSK/ZETA/LOAR/ELF/FROG/LYFT/
FLYW/DOCN/CEG/SITM/NET/CPRT/FRSH/ESTC/GTLB/SCCO/RMBS/DDOG/PAYS/SPIR/
CAKE）。全銘柄でdivergence_ratioが改善し悪化ゼロを確認。LITEのみ
控除後にadj_net_incomeがマイナスに転じ、既存のFCF_Conversion_Rate
→FCF_Base方式フォールバックガードが正しく発火することを確認。

#### CELHの扱い（最終判断）
特例化せず一律控除を適用。改善は限定的（divergence 1.30x→1.23x、
restructuring費$327.5Mが支配的要因のため）だが、①控除自体は
方法論的に正しく悪化もない、②タスクの設計方針（新規ticker_overrides
不要）に反するため特例化は避けるべき、③残る乖離は別課題（事業再編費
側）として切り分けるのが妥当、と判断。新規タスク化するかは次回検討。

#### 全100銘柄再生成（コミット`42531f681`）
主要4銘柄の変化: CWAN 2.19x→0.88x（IV $69.90→$38.10）、SNPS
1.47x→1.34x（$335.32→$310.32）、SOFI 1.33x→1.20x（$16.77→$18.22）、
CELH 1.30x→1.23x（$28.12→$26.73）。いずれもWATCH維持
（CWAN/SNPS/SOFI/CELHとも`fcf_outlier.detected=True・action="flagged"`
が独立にPolicy Bを発火させ続けるため）。LITEはFCF_Conversion_Rate
方式→FCF_Base方式へフォールバック（IV $14.72→$9.17）。ENTG（WATCH→
SELL）・GOOGL（HOLD→TRIM）は既存分類ロジックがより正確なIV・upside
入力を受けて正当に再判定した結果であり、分類ロジック自体は変更していない。

#### 検証
- `report_consistency_check.py --fail-on-ng`: NG=0件（対象100銘柄、
  WARN=69件は既存の無関係事象）
- `pytest tests/`: 433 passed / 2 known failed（regressionなし。
  回帰テスト`tests/test_estimate_fcf_ma_addback.py`を新規追加、4件）
- 対象外52/53銘柄はほぼ変化なし。1件（BROS）のみ微小変化したが
  `ma_addback_excluded=0`で本タスク無関係と確認済み（EPS Analyzer側
  net_income_priority修正の遅延反映によるもの）
- LYFTの`anomaly_detection`検証失敗は本タスク以前から存在する既知の
  状態（構造的にFCF恒久マイナス銘柄）でregressionではないことを確認

---

### ✅ [CIK-DISCONTINUITY-OLDEST-YEAR-GAP-1] 法人再編によるCIK断絶で最古年度のPL/CF項目が構造的に欠落するパターン
**優先度:** 未定
**分類:** データ品質 / SECデータ正規化
**登録日:** 2026-07-20
**発見:** [[MRVL-2019-2020-NULL-1]]原因調査時の副次発見
**完了日:** 2026-07-20（全106銘柄棚卸し→汎用検知ロジック設計・精度検証→
スキーマ・アクセッサ調査→複数CIK統合実装・検知ロジックの登録フロー組み込み
→GOOGL FY2012/2013個別上書きまで完了）

#### 背景
法人再編（持株会社化・スピンオフ等）でCIKが切り替わった銘柄は、現在
追跡中のCIK配下の最古10-Kの比較年度ウィンドウより前の年度でPL/CF項目が
構造的に取得不能になるパターンを全106銘柄で棚卸しした。以下3類型に分類:
- ①同一事業の法人形態変更型（MRVL/GOOGL/AVGO/DELL）: 持株会社化・買収に伴う
  CIK切替だが、同一事業が継続している
- ②スピンオフ・カーブアウト型（CEG/LITE/ABBV/GEV/SN/CON）: 親会社からの
  分離により新規CIKが発行されている
- ③破産再生型（VST）: Chapter 11破産手続きのfresh-start会計により新規CIKが
  発行されている

#### 対応方針
①のみ複数CIK統合で連続データ化する。②③は接続せず構造的境界の注記のみ
表示する。理由: ②は親会社連結からの区分推定値、③はfresh-start会計で
連続性自体が断絶しているため、旧データを接続すると実績としての性質が
異なるデータを混同表示することになり不正確なため。

#### 実装（コミット`57e84af52`・`68d24a0e9`）
- `common/sec_data/cik_history.json`を新設し、①4銘柄の旧CIK・移行経緯を登録。
  `fetcher.py`層で該当銘柄のみ旧CIKのcompany_facts.json・submissions.jsonを
  追加取得しus-gaap facts・submissionsをマージする実装（マージ専用の優先順位
  ロジックは追加せず、既存のparser.py本人データ優先ロジックにそのまま委ねる）
- 拡張年度: MRVL 2007-2018、GOOGL 2006-2011、AVGO 2006-2014、DELL 2007-2013
  （DELLはFY2013〜FY2016が旧CIK・新CIKいずれの自社10-Kも存在しない申告
  ギャップと判明。FY2015/2016は新CIKのFY2017 10-Kの比較年度再掲データ
  〈本人データではない〉のみ存在し、FY2014は値が完全に欠落。フロントエンドに
  `DELL_PRIVATE_PERIOD_NOTE`で注記）
- GOOGL FY2012/2013はMotorola Mobile事業の非継続事業区分変更（2015年
  遡及修正）により、本人データ優先ロジックが当初申告値（未修正）を採用して
  しまうと判明。`fact_overrides.json`（ticker_overrides型と同型の個別上書き
  設定）を新設し、parser.pyの`_apply_fact_overrides()`で該当4項目
  （revenue/operating_income/research_and_development/selling_and_marketing）
  のみ修正後の値に置き換え。net_incomeは修正前後で金額が完全一致するため
  対象外、eps_diluted/eps_basicは別要因（2014年株式分割の遡及調整）による
  変動と判明したためスコープ外として切り分けた
- 汎用検知ロジック（境界年>=2010かつ判定年度revenue>=$500M、既知9銘柄で
  Recall100%/Precision65%）を`registration_validator.py`のP6チェックとして
  新規銘柄登録フローに組み込み。確定済み4銘柄・確認済み構造的境界7銘柄
  （CEG/LITE/ABBV/GEV/SN/CON/VST）以外の新規候補（APP/BSY/CART/PLTR/RBRK/
  LYFT）はWARNとして人手確認待ちで提示する設計（自動でcik_history.jsonへ
  登録することはしない）
- フロントエンド（pipeline.py）: ②③7銘柄に`CIK_DISCONTINUITY_TICKERS`で
  構造的境界の注記を表示。DELLのみ`DELL_PRIVATE_PERIOD_NOTE`で申告ギャップの
  注記を追加表示

#### 検証
- pytest: 433/435 passed（NVDA/MSFT失敗2件はstock split起因の既知の無関係な
  問題、regressionなし）
- `report_consistency_check.py`: NG=0（WARN=71件、うちMRVL/DELL各1件は
  新規追加した古い年度のfyタグ裏取り不一致・自動修正なしの情報用WARNで
  Classificationに影響なし）
- 対象外101銘柄のデータファイルへの影響ゼロを確認済み
- GOOGLの成長率計算（`growth_sanity.calc_revenue_cagr`）は2点間CAGRのため
  現行の本番窓（直近5年）では上書きの影響を受けないことを確認。FY2013を
  終点とする仮想窓ではcagr_3yr 26.8%→23.7%、cagr_5yr 22.4%→20.6%と、
  遡及修正前の過大な成長率が是正されることを確認

#### 副次的成果
本タスクの過程（GOOGL FY2012/2013個別上書きの実装方式検討）が、
CHAT_RULES.mdに「銘柄固定のハードコード禁止」原則を新規追加するきっかけと
なった（別途ブラッシュアップ時に反映予定）。

---

### ✅ [FCF-EST-DIRECTION-GUARD-1] 買収・統合関連控除にdr>1限定の方向性ガードを追加
**優先度:** 中
**分類:** アーキテクチャ / TANUKI VALUATION / FCF-CONVRATE②派生
**登録日:** 2026-07-20
**発見:** [[MA-INTEGRATION-TAG-GAP-1]]全105銘柄タグ影響網羅調査時
**完了日:** 2026-07-20

#### 背景
CWAN-SNPS-MA-DISTORTION-1の「買収・統合関連」加算控除メカニズムは、
divergence_ratio（dr、推定FCF÷実測FCFの比）>1（過大推定）の是正には
有効だが、dr<=1（過小推定）の銘柄に同じ控除を適用すると乖離がさらに
悪化する構造的な副作用があった（例: CSGP 0.52→0.28、ZETA 0.66→0.53、
いずれも[[MA-INTEGRATION-TAG-GAP-1]]のタグ追加を仮定した試算）。
Classification/WATCH丸めには影響しないが、`estimated_fcf`はDCF計算の
`base_fcf`として直接使われintrinsic_value_per_shareを実質的に左右する
ため、IVの絶対値精度に実害があった。

#### 対応（コミット`3b413b849`）
`estimate_fcf_from_eps()`に方向性ガードを実装。控除前のAdj_NIベースで
独立に`pre_deduction_dr = (adj_net_income_orig × conversion_rate) /
raw_fcf`を算出し、`pre_deduction_dr > 1.0`の場合のみ既存の控除を適用
する（`<=1.0`の場合は元のAdj_NIをそのまま使用）。控除後のdrを判定基準に
使うと「控除するかどうかを、控除した結果のdrで決める」循環参照になる
ため、必ず控除前の値を使う設計とした。`FCFEstimationResult`に新フィールド
`ma_addback_detected_but_not_applied`を追加し、ガード発火時の検出額を
記録（`ma_addback_excluded`は実際に控除された額のみを表す設計を維持）。

#### 全母集団シミュレーション（実関数呼び出し、対象72銘柄）
CWAN-SNPS-MA-DISTORTION-1完了時の47銘柄から、定例データ更新で72銘柄に
自然増加していたことを確認した上で全72銘柄を検証。無関係51銘柄
（生FCF安定スキップ17・控除前から赤字8・pre_dr>1で現状維持26）は
est_fcf・dr・method全て完全無変化を確認。実質的な変化ありは
**21銘柄**（ADSK/AMD/CEG/CSGP/DELL/ELF/ENTG/ESTC/FLYW/FROG/GEV/HEI/HQY/
LOAR/LYFT/MSFT/PAYS/PEP/RMBS/VRT/ZETA）でdrが是正方向に上昇、method自体
（raw_fcfフォールバック⇔推定適用）の切替は発生しないことを確認。対象外
28銘柄（ma_addback_excluded=0）は完全一致（ミスマッチ0件）。

#### 本番データ再生成・IV変化幅
該当21銘柄を`pipeline.py --skip-risk`で再生成。IV変化幅は+1.6%（PEP）
〜+116.1%（ENTG）。**ENTGはClassificationがSELL→WATCHに是正**（従来IV
$13.14→$28.40の是正により、upside -90.5%→-79.5%となりDCF信頼性LOWの
WATCH丸めロジックが正しく適用された。過小評価されたIVによる過大な
割高判定が解消）。他20銘柄はClassification変化なし。

#### 検証
- pytest: 434/435 passed（新規テスト1件追加。NVDA/MSFT失敗2件は既知の
  無関係な問題）
- `report_consistency_check.py`: NG=0（WARN=71件、前回と同数、新規WARNなし）
- LYFTの`anomaly_detection`検証失敗（構造的FCF恒久マイナス銘柄）は
  既知の非regression事象と再確認済み

#### 副次的成果
方向性ガード実装により、[[MA-INTEGRATION-TAG-GAP-1]]でタグ追加時の
懸念事項だった「グループC（悪化方向）」が構造的に解消される見込みと
なった。詳細は同エントリの状況追記を参照（正式な再検証は次回タグ追加
検討時に実施）。

---

### ✅ [FCF-EST-NET-BASIS-FIX-1] ma_addback計算の税引前amount/税引後net_amount基準不一致
**優先度:** 高
**分類:** バグ修正 / TANUKI VALUATION / FCF-CONVRATE②派生
**登録日:** 2026-07-20
**発見:** [[MA-INTEGRATION-TAG-GAP-1]]再検証時の副次発見（境界跳ね返りリスク調査中に
tax_adjuster.py::apply_tax_adjustments()との基準比較で判明）
**完了日:** 2026-07-20

#### 背景
CWAN-SNPS-MA-DISTORTION-1実装当初から、`adjusted_net_income`自体は
EPS Analyzer側で税引後（`net_amount`）ベースで構築されているのに、
これを控除する`ma_addback`は税引前（`amount`）を合算しており、基準が
不一致だった。税効果分だけ過剰に控除する系統的バイアスが生じ、dr>1の
是正が行き過ぎて過小推定側に転じていた（CWAN: 0.88倍で停止、本来は
1.15倍程度が正しい）。

#### 対応（コミット`52730546e`）
`estimate_fcf_from_eps()`の`ma_addback`計算を`net_amount`基準に変更
（`net_amount`未設定時は`amount`へフォールバック）。`pre_deduction_dr`・
方向性ガードの判定ロジック自体（FCF-EST-DIRECTION-GUARD-1）は無変更
（ガード判定は`adj_net_income_orig`のみに依存し`ma_addback`を参照しない
ため、ガードの許可/阻止決定は本修正の影響を受けない）。
テスト2件追加（`test_ma_addback_uses_net_amount_not_pretax_amount`・
`test_ma_addback_falls_back_to_amount_when_net_amount_missing`）。

#### 全母集団シミュレーション（実関数呼び出し）
ガード阻止中の21銘柄は`ma_addback`自体を参照しないため完全無変化を
確認。ガード許可中51銘柄のうち実質的な変化があったのは**25銘柄**
（いずれも`est_fcf`が増加する方向のみ、悪化ゼロ）。

#### 本番データ再生成・IV変化幅
該当25銘柄を`pipeline.py --skip-risk`で再生成。IV変化幅は+0.01%
（GOOGL）〜+17.11%（CWAN）。Classification変化は0件（全25銘柄とも
変化前後で同一クラス）。

#### 検証
pytest: regression検出なし（NVDA/MSFT既知2件のみ、無関係）

---

### ✅ [AMZN-DIVERGENCE-HIGH-1] 買収・統合関連控除後もdr=2.95と高止まり
**優先度:** 未定
**分類:** データ品質 / TANUKI VALUATION / FCF-CONVRATE②派生
**登録日:** 2026-07-20
**発見:** [[TRUST-SUMMARY-EPIC-1]]段階2再調査（CWAN-SNPS-MA-DISTORTION-1適用後の
全数再スキャン）
**完了日:** 2026-07-20

#### 内容
CWAN-SNPS-MA-DISTORTION-1・FCF-EST-DIRECTION-GUARD-1・
FCF-EST-NET-BASIS-FIX-1を経てもAMZNのみdivergence_ratioが2.96倍と
高止まりしていたため、KO-SPIR-CF-CAUSE-UNCONFIRMED-1と同型の一次情報
調査を実施した。

#### 原因確定（確度：高、10-K・外部報道・ローカルデータの3系統一致）
**③conversion_rateの構造的ミスマッチ（FCF-CONVRATE②型の変種）**と確定した。

- GAAP純利益$77.67B・調整済み純利益$93.52Bとも健全。Adj_NI押し上げ要因は
  ほぼ全て株式報酬（$19.47B、pretax）の非現金加算であり、異常項目はない
- 営業キャッシュフロー（OCF）は$115.9B（2024）→$139.5B（2025）と
  前年比+20%拡大しており、事業自体は健全（10-K MD&A確認）
- 乖離の主因はAWS/AI向け史上最大規模のCapEx急増（2025年$131.8B、
  前年比+59%、2026年計画$200B）——「大部分はAWS事業成長を支えるための
  技術インフラ投資」と10-K MD&Aに明記（[SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm)）。外部報道でも
  TTM FCFが$38.2B→$11.2B（71%減）の主因は「AI関連CapExによる有形固定
  資産購入の$50.7B増」と一致
- KO/SPIRのような単発の一過性会計イベントではなく、複数年にわたる
  意図的な投資フェーズであり、TRUST-SUMMARY-EPIC-1（2026-07-18分析）で
  既に「一時的な成長投資フェーズ・可視化対象外・対応不要」と整理済みの
  位置づけと完全に整合する

#### 対応
実装不要。構造的な性質（複数年の意図的投資フェーズ）のため個別修正の
対象外と判断し、クローズする。

#### 副次的成果
AMZNのticker_override（conversion_rate 0.55）の設定根拠が「AWS高転換率・
EC低転換率の加重平均」を前提としていたが、2025年以降のCapEx急増は
AWS自体が主因であり、当初の二分法の前提と実態にズレがある可能性が
判明した。0.55が誤りとまでは断定できないため、再較正要否の検討を
[[AMZN-CONVRATE-OVERRIDE-REVIEW-1]]として新規登録した。

---

### ✅ [FCF-EST-NOTE-DISPLAY-1] 買収・統合関連控除の理由がreport.txtに未表示
**優先度:** 低
**分類:** TANUKI VALUATION / 透明性
**登録日:** 2026-07-20
**発見:** [[TRUST-SUMMARY-EPIC-1]]段階2再調査（divergence_ratio消費箇所の一次コード確認）
**完了日:** 2026-07-20

#### 背景
`estimate_fcf_from_eps()`が生成する「買収・統合関連」控除理由
（`fcf_estimation.note`）がreport.txt・stock.htmlのいずれにも
表示されていなかった。KO/SPIRのFCF_TRANSIENT_ITEM_EXPLANATIONSバナー
（一過性費用の理由を明示表示する既存の仕組み）とは対照的で、透明性
という設計思想（TRUST-SUMMARY-EPIC-1の骨子）に照らすと表示漏れが
あった。

#### 対応（コミット`649c404d8`・`170ba198c`）
- report.txt（`pipeline.py`）: applied=True・applied=False両分岐に、
  `ma_addback_excluded`・`ma_addback_detected_but_not_applied`を
  参照する控除理由表示を追加
- stock.html: applied=True分岐の入力グリッドに、既存の
  `fcfEstWarning`ブロックと同型の条件付きブロックを追加。固定リスト
  方式は使わず、latest.jsonの既存フィールドを直接参照する設計とした
  （M&A控除情報は機械的な値のため、KO/SPIR型の個別リスト手動保守は
  不要と判断）
- 生FCF安定(CV<0.3)分岐（17銘柄）は、控除自体がestimated_fcfの計算に
  使われないため誤解を招くと判断し、意図的に表示対象外のまま維持
  （noteが「生FCF安定」で始まるかで判定）

#### 全55銘柄への本番反映
対象銘柄（applied=True 46・applied=False 9）全55銘柄に
`pipeline.py --skip-risk`で反映完了。IV・Classificationとも全銘柄で
変化なしを確認（表示のみの変更）。その他の差分は全て無関係な要因と
特定済み：
- yfinance由来の生きた市場データ（PEG・analyst_target等）の定例的な変動
- CRWV/IONQ/JOBY/QBTS/RCAT/RXRX/S/SOUNの8銘柄の`adj_net_income`変化は、
  これらがFCF-EST-DIRECTION-GUARD-1・FCF-EST-NET-BASIS-FIX-1のいずれの
  再生成対象にも含まれていなかった（最終出力`estimated_fcf`が不変のため
  対象外と判定されていた）ことによる遅延反映効果であり、`estimated_fcf`・
  IV自体は不変

#### 検証
- pytest: 438件中436件passed（NVDA/MSFT既知2件のみ、regressionなし）
- `report_consistency_check.py`: NG=0（WARN=71件、新規WARNなし）

---

### ✅ [FCF-OUTLIER-PREROUNDING-LOSS-1] Policy A/B丸め処理で丸め前のClassificationが保持されず失われる
**優先度:** 未定
**分類:** アーキテクチャ / TANUKI VALUATION / 検証基盤
**登録日:** 2026-07-18
**発見:** [[TRUST-SUMMARY-EPIC-1]]棚卸し再検証（fcf_outlier丸めによる理由喪失の一次確認）
**完了日:** 2026-07-20

#### 背景
`pipeline.py::_compute_tanuki_score()`にて、Policy A/B（DCF_Reliability=LOW
丸め）発火時、それまでに計算済みの`score`/`comment`ローカル変数を単純に
上書きしており、丸め前の分類（元々BUY/TRIM/HOLDのどれだったか）を保持する
フィールドが存在しなかった。

#### 対応
丸め処理直前に`score`/`comment`を`_pre_rounding_score`/
`_pre_rounding_comment`として退避し、発火したポリシー
（`_rounded_by_policy`＝"A"|"B"|None）と共に戻り値に追加。
`_compute_tanuki_score()`は純粋関数の性質を維持（valuation辞書の
読み取りのみ、DCF計算・IV算出には無変更）。`latest_data`構築部に
3フィールド（`pre_rounding_score`・`pre_rounding_comment`・
`rounded_by_policy`）を同型でフラット追加。report.txtの
`[1. TANUKI SCORE]`セクションに、丸め発生時のみ
`Classification_Pre_Rounding`行を追加。

#### 全母集団検証（重要な発見）
`_compute_tanuki_score()`を全100銘柄の`latest.json`に対して再実行し、
全銘柄で最終Classificationが不変であることを確認した。実際に丸めが
発生するのは**65銘柄**（Policy A 10・Policy B 55）で、report.txtの
「DCF_Reliability: LOW」表示件数（70）とは5銘柄分の差があった。
差分の5銘柄（BBAI/QBTS/RDW/SPIR/KULR）は全て`tanuki_score=PASS`で
あり、Policy A/B発火条件「`score not in (SELL, PASS)`」により実際の
丸めは発生しない（PASSのまま）。report.txt側のDCF_Reliability表示は
独立した判定でこの除外を考慮しないため情報表示としてLOWが出るのみで
Classification自体は丸められない、という既存の仕様差であり、本タスクの
バグではないと確認した。

#### サンプル確認
ENTG（WATCH←丸め前TRIM、Policy B）・SNPS（WATCH←HOLD、Policy B）・
JOBY（WATCH←HOLD、Policy A）・QBTS（PASS、`Classification_Pre_Rounding`
は正しく非表示）・AAPL（WATCH←TRIM、Policy B）で表示・挙動を確認。
全銘柄でIV・Classification（丸め後の最終値）に変化なし。

#### 検証
- pytest: 438件中436件passed（既知2件のみ、regressionなし）
- `report_consistency_check.py`: NG=0（WARN=71件、新規WARNなし）

#### スコープ外として記録
stock.html側への表示は、そもそもClassification自体がstock.html
（銘柄個別ページ）に表示されていないという別の未解決論点のため対象外と
した。必要であれば別タスクとして今後検討する。

---

## 2026-07-19（完了）

### ✅ [FY52WEEK-BS-FADEOUT-FALLBACK-1] 生涯フェードアウト22件への履歴フォールバックロジック（3件除外・年数閾値なし）
**優先度:** 中
**分類:** アーキテクチャ / データ品質ゲート
**登録日:** 2026-07-19
**完了日:** 2026-07-19
**発見:** [[FY52WEEK-BS-NULL-SILENT-1]] Phase B/C 全179件の一次情報確認

#### 設計方針（事前調査で確定・実装方針の根拠）
- **年数閾値を設けない**: 事前調査（ギャップ年数分布: 最小1年・最大12年・
  中央値3年）の結果、単一の固定閾値では広い分布をカバーできず、また
  「過去に明示的$0実績がある」という条件自体が既に十分に強いシグナル
  （企業が意図的に$0を申告した実績）であるため、年数による足切りは
  設けないこととした。
- **M&A等重大イベント時の無効化の仕組みは設けない**: 事前調査で25件と
  BACKLOG既知のM&A・組織再編イベント（BROS Up-C再編・CART・CWAN
  Enfusion買収・SNPS Ansys買収・CON 2024年スピンオフ・AVAV BlueHalo
  買収）との重複がないことを確認済みのため、無効化機構は今回のスコープ
  外とした。
- **25件中3件を除外**: CSGP/short_term_investments・KULR/short_term_debt・
  RCAT/long_term_debtは「最後の$0の後に実額の非ゼロ値が再登場してから
  消失する」複雑パターンと判明したため、[[BS-FIELD-FADEOUT-NONZERO-
  LAST-VALUE-1]]として別タスクに分離し、今回は対象外とした。

#### 実装内容
- **reader.py**: `_lookup_last_confirmed_zero_year()`を新設。
  22件のハードコードリストではなく、**「最新年度が完全欠損（None）かつ
  直近の既知値（過去に遡って最初に見つかった非None値）が明示的0である」
  という条件判定による汎用ロジック**として実装（この条件により
  CSGP/KULR/RCAT型は「直近の既知値が非ゼロ」のため自然に除外される）。
  `get_net_cash()`の3フィールド（short_term_investments/long_term_debt/
  short_term_debt）それぞれに適用し、`{field}_estimated_zero`・
  `{field}_last_confirmed_zero_year`をprovenanceとして返す。
  - **既存ロジックとの整合を確保するための追加修正**: 実装当初は
    四半期側の同一時点原則（BUG-NETDEBT-4）・正規化データ補完
    （BUG-NETDEBT-3）が発火した際に無条件で推定ゼロフラグをリセット
    していたが、これだと「四半期側も同じタグ欠損を抱えている場合」に
    annual側の推定ゼロ注記が不必要に消えてしまうことが判明（例:
    ENTG/short_term_debtは四半期が明示的0を報告済みのため正しく
    リセットされるべきだが、他のケースでは四半期側もNoneのままの
    場合がある）。四半期・正規化データ側が「そのフィールド自身の
    実データ」を持っている場合のみリセットするよう修正した。
- **adjustments.py**: `BSAdjustmentResult`に6フィールド
  （sti/ltdebt/stdebt × estimated_zero/last_confirmed_zero_year）を追加。
- **pipeline.py**: `financial_health`辞書に`long_term_debt`/
  `short_term_debt`の個別値（従来`total_debt`への合算のみ）と上記6
  フィールドを追加露出。report.txtのST_Invest行に推定ゼロ注記
  （近似値注記と排他）を追加、LTDebt/STDebtいずれかが推定ゼロの場合
  のみ新規「Debt内訳」行を表示。
- **report_consistency_check.py**: コード変更は不要と判断（後述）。
- **tests/test_pipeline_logic.py**: `TestFadeoutZeroFallback`
  （7件、PLTR型の代表例・年数閾値なし確認・CSGP/KULR/RCAT型の
  非該当確認×3・構造的不明ケース・最新年度に実データありのケース）
  を合成データで新設。

#### 検証結果
- **全100銘柄スキャン**（reader.py直接呼び出し、データ再生成なしの
  安全な方式）: `estimated_zero`が付与されたのは想定19件（22件中、
  3件は下記理由でより新しい実データに委ねられ非該当）。ENTG/
  short_term_debt・FLYW/long_term_debt・CPRT/long_term_debtは、
  四半期の明示的0報告・正規化データの実額発見により、推定ゼロより
  優先される新しい情報が見つかったため`estimated_zero=False`となる
  （設計上正しい挙動、バグではない）。他78銘柄・rpoフィールドは
  0件で想定通り非該当。
- **除外3件の再確認**: CSGP/short_term_investments・KULR/
  short_term_debt・RCAT/long_term_debtはいずれも`estimated_zero=False`
  のまま（誤って推定ゼロにならないことを確認）。
- **19件の実ライブ確認**: PLTR/CSGP(std)/KULR/RCAT/APP/BKNG/CDNS/DELL/
  DOCN/ENTG(sti)/HQY/META/MSCI/NOW/RMBS(両field)/RXRX/S/SOUN(両field)/
  TER・FLYW・CPRTの計21銘柄で`pipeline.py --skip-risk`を実行。
  report.txtで想定通り「推定ゼロ（最終確認: FY20XX）」注記・Debt内訳
  行が表示され、FLYW/CPRTは想定通り注記なし（正規の実データに解決）
  であることを確認。**IV・Classification・Net_Debtの数値は全21銘柄で
  一切変化なし**（本タスクは既にNone→0扱いされていた値へメタデータ・
  表示注記を追加するのみで、実際の計算値は変更しないため）。
  TERのみNet_Debt表示が$-0.04B→$-0.05Bと僅かに変化したが、baseline
  コード（本タスクの変更前）でも同一の再生成で同じ値になることを
  確認済みで、本タスクとは無関係な既存データの再生成漏れ（他タスクでも
  複数回確認済みの既知パターン）と判断した。
- **他銘柄への影響**: `git status`でPLTR/CSGP/KULR/RCAT/APP/BKNG/CDNS/
  CPRT/DELL/DOCN/ENTG/FLYW/HQY/META/MSCI/NOW/RMBS/RXRX/S/SOUN/TER
  の21銘柄以外のデータファイルが一切変更されていないことを確認
  （`tickers.json`のタイムスタンプ更新のみ、count=100不変）。
- **report_consistency_check.py**: WARN-25（`_BS_NULL_CHECK_FIELDS`）は
  対象3フィールドを含まないため無関係。WARN-26（BS項目遷移検知）は
  raw annual_YYYY.jsonを直接読むためreader.py層の本フォールバックとは
  独立しており、影響がないことを実行確認済み（コード変更は行っていない）。
- **pytest**: 413件中411 passed（既知failのMSFT/NVDA 2件のみ、
  新規failなし）。
- **report_consistency_check.py --fail-on-ng**: NG=0（WARN=69件、
  既存分から変化なし）。

#### 着手条件（消滅・完了）
なし（実装完了）

---

### ✅ [WST-SECTOR-MISCLASSIFICATION-1] sector分類修正（RCAT-SECTOR-MISCLASSIFICATION-1と2件一括対応）
**優先度:** 中
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-19
**完了日:** 2026-07-19
**発見:** WST=[[GROWTH-SANITY-CLASS-SYNC-1]]（完了）verdict≠PLAUSIBLE全32銘柄の
原因分析、RCAT=[[GROWTH-VERDICT-SEQUENCING-BUG-1]]対応中のverdict悪化3銘柄
個別調査

#### 問題（再掲）
両銘柄とも`config/beta_config.json`のsector値がyfinance実態（industry）と
不一致。WST: "Healthcare_IT"→実態"Medical Instruments & Supplies"。
RCAT: "Electronics_General"→実態"Aerospace & Defense"。

**RCATについては、分類修正してもgrowth_sanityのREVIEW警告自体は解消しない
（乖離比率が拡大する）ことを事前調査時点で確認済みであり、本対応は
データ品質としての正しさを目的とし、verdict改善を目的としないという前提の
まま実施した。**

#### 実装内容
1. `growth_sanity.py::SECTOR_TO_DAMODARAN`辞書から、`beta_config.json`に
   実在する業種カテゴリキーを確認（推測で決め打ちせず）:
   - WST向け: `Healthcare_Products` → Damodaran「Healthcare Products」
   - RCAT向け: `Aerospace_Defense` → Damodaran「Aerospace/Defense」
     （`Space_Defense`も同一Damodaranシート名にマップされ機能的に等価だが、
     RCATはドローン〈航空機〉であり衛星等の「Space」要素はないため
     `Aerospace_Defense`をyfinance industry文字列との対応の分かりやすさで
     採用）
2. `config/beta_config.json`のWST・RCATエントリの`sector`値をそれぞれ
   `Healthcare_Products`・`Aerospace_Defense`に修正（`beta`/`source`は無変更）。
3. `sector`値を参照する全計算経路をgrepで洗い出し、以下の通り整理:
   - **growth_sanity Damodaran業種ベンチマーク比較**
     （`pipeline.py::_load_beta_sector()`→`check_growth_sanity(sector=...)`）:
     意図通り影響を受ける（本対応の主目的）。
   - **FCF実力推定の転換率**（`core_calculator.py`の`_sector`→
     `estimate_fcf_from_eps(sector=...)`→`fcf_conversion_config.json`の
     `sector_conversion_rates`）: RCATは`Electronics_General`（テーブル
     未掲載→デフォルト0.7）から`Aerospace_Defense`（テーブル掲載値0.55）
     に変わり**表示上の転換率は変化する**が、RCATは`adj_net_income`が
     マイナスのため`fcf_estimation.applied=False`（生FCFへフォールバック）
     であり、**実際のIVには影響しない**ことを確認。WSTは新旧いずれの
     キーもテーブル未掲載でデフォルト0.7のまま変化なし。
   - **WACC/β計算**（`core_calculator.py`→`calculate_wacc(sector=...)`）:
     `sector`引数は`beta`がNoneの場合のみのフォールバック用。WST・RCATとも
     `beta_config.json`に明示的な`beta`値（1.159/1.296）があるため、この
     フォールバック経路は発火せず**影響なし**。
   - **Phase2成長率上限**（`_sector_caps`）・**αセクター/業種別上限**
     （`_alpha_caps`/`_industry_alpha_caps`、`maturity_config.json`）:
     いずれも新旧いずれのキーも未掲載のため**影響なし**。加えて
     `_alpha_caps`のキーは実際にはyfinanceの広義sector（"Healthcare"
     "Industrials"等のGICS的分類、`financials["sector"]`由来）であり、
     `beta_config.json`の狭義sector（Damodaran向け）とは別軸の値である
     ことも確認した（両者を混同しないよう注意）。
   - **beta_fetcher.py**（Software_System暫定分類判定）:
     `sector=="Software_System"`限定のロジックのため対象外。

#### 検証結果（新旧比較、具体的数値）
- **WST**: IV $99.97（不変）、Classification TRIM（不変）、WACC 10.906%
  （不変）。growth_sanity: verdict REVIEW→**PLAUSIBLE**、industry_benchmark
  1.66%→7.81%、damodaran_industry "Heathcare Information and Technology"→
  "Healthcare Products"、recommended_g（Layer2参考値・DCF未適用）3.3%→5.9%、
  warnings「3.9倍超」→解消（0.8倍以内）。IVが不変な理由: WSTはLayer 1
  （セグメント加重モデル）で実際のDCF成長率6.4%を直接使用しており、
  recommended_gは参考表示のみでDCF計算には使われないため。
- **RCAT**: IV $3.89→**$3.73**（-4.2%）、乖離率-49.1%→-51.2%、
  Classification WATCH（不変）。growth_sanity: verdict REVIEW→REVIEW
  （**不変、事前調査通り**）、industry_benchmark 13.8%→10.9%、
  damodaran_industry "Electronics (General)"→"Aerospace/Defense"、
  実際にDCFへ適用される成長率（Layer2逓減モデル、CAGR_max×35%+
  industry_benchmark×65%）44.0%→**42.1%**、warnings「3.2倍超」→
  **「3.9倍超」（乖離拡大、事前調査で予告した通り）**。IVが変化した理由:
  RCATはセグメント未設定のためLayer 2（逓減モデル）の成長率が実際のDCFに
  直接使用されており、industry_benchmarkの低下がrecommended_gを
  引き下げDCF成長率を下げたため（FCF転換率変化は前述の通り無関係）。
- **他98銘柄への影響**: `pipeline.py WST RCAT --skip-risk`のみ実行し、
  `git status`でWST/RCAT以外の98銘柄のデータファイルが一切変更されて
  いないことを確認（`tickers.json`の`updated_at`タイムスタンプ更新のみ、
  `count`は100で不変）。sector値はticker単位のオーバーライドのため
  他銘柄への影響は構造的にゼロであることも設計上確認済み。
- **pytest**: 406件中404 passed（既知failのMSFT/NVDA 2件のみ、新規fail
  なし）。
- **report_consistency_check.py --fail-on-ng**: NG=0（WARN=69件、既存分
  から変化なし）。

#### 着手条件（消滅・完了）
なし（実装完了）

---

### ✅ [RCAT-SECTOR-MISCLASSIFICATION-1] sector分類修正（WST-SECTOR-MISCLASSIFICATION-1と2件一括対応）
**優先度:** 中
**完了日:** 2026-07-19

上記[[WST-SECTOR-MISCLASSIFICATION-1]]エントリと同一コミットで一括対応。
実装内容・検証結果（RCAT: IV $3.89→$3.73、Classification WATCH不変、
growth_sanity verdict REVIEW→REVIEW不変〈事前調査通り〉等）は同エントリ参照。

---

### ✅ [SKIP-RISK-EVENTS-WIPE-1] pipeline.py --skip-risk実行時のrisk_events保全
**優先度:** 中
**分類:** バグ修正 / TANUKI VALUATION / データ保全
**登録日:** 2026-07-18
**完了日:** 2026-07-19
**発見:** [[FCF-CONVRATE②]]（BACKLOG_DONE.md参照）検証手順で全100銘柄を
`pipeline.py --skip-risk`で再生成した際に発見

#### 問題（再掲）
`pipeline.py`の`risk_events`（Grok web検索による週次リスクイベント取得、
GitHub Actions週次自動実行が本来の更新経路）が、`--skip-risk`実行時に
既存値を保持せず無条件で空配列`[]`に上書きされていた。CLAUDE_CODE_START.md
は「手動実行時は原則--skip-riskを付けること」と明記しており、複数銘柄・
全銘柄を対象にした手動再生成のたびに再発しうる構造的リスクだった。

#### 実装内容
`pipeline.py::_save_result()`に以下を実装：
- メソッド冒頭（`os.makedirs(history_dir, exist_ok=True)`直後、他の処理が
  始まる前）で、`self.skip_risk`がTrueの場合のみ既存`latest.json`の
  `risk_events`を`_pre_existing_risk_events`として退避する。
- **実装中の重要な発見**: 当初、risk_events確定箇所（メソッド末尾付近）で
  直接`latest_path`を読み直す実装にしたところ、**risk_eventsが常に空配列に
  なる**という新たな不具合が発生した。原因は、`_save_result()`内で
  risk_events確定より前に一度`latest_data`が中間保存される処理（`with
  open(latest_path, "w")`、matrix計算直後）が既に存在しており、この中間
  保存時点ではrisk_eventsキー自体がまだ設定されていないため、後から
  同じ`latest_path`を読み直すと「自分自身が書いた、risk_events未設定の
  状態」を読んでしまうため。この中間保存より前（メソッド冒頭）で退避する
  設計に修正して解消した。
- `self.skip_risk`がFalse時の既存の取得ロジック（`fetch_risk_events`）は
  一切変更していない。
- `tests/test_pipeline_logic.py`に`TestSkipRiskEventsPreserved`（3件:
  既存risk_events保持・新規銘柄相当で空配列・risk_eventsキー欠落時に
  空配列）を追加。このテストファイル冒頭で`growth_sanity`モジュール
  全体がMagicMockに差し替えられているため（本物のロジックはテスト6での
  み`_gs`経由で検証）、`_save_result()`を直接呼ぶ本テストでは
  `pipeline.check_growth_sanity`を空dictを返すようmonkeypatchし、
  無関係な`growth_sanity`関連コードパスでのTypeError
  （MagicMockとfloatの比較エラー）を回避した。

#### 検証結果
- **既存risk_events保持確認**（AAPL、risk_events 3件保有）:
  `pipeline.py AAPL --skip-risk`実行前後でrisk_events完全一致（git diffで
  risk_eventsセクションに差分なしを確認）。
- **全100銘柄再生成**: `pipeline.py --skip-risk`（引数なし、全銘柄）実行、
  成功100/100。実行前後でrisk_eventsを全銘柄比較した結果、
  **不一致0件・空配列への意図しない後退0件**（うち29銘柄が非空の
  risk_eventsを保有しており、全て完全一致で保持されたことを確認）。
  なお、この検証用の全銘柄再生成データ（calculation_date更新・IV変動等、
  本修正とは無関係な通常の再計算結果）はコミットに含めず、検証後に
  ベースラインへ復元した（本タスクは risk_events の保全ロジックのみが
  スコープであり、無関係なデータ再生成をコミットに含めないため）。
- **通常実行（--skip-riskなし）の回帰確認**: `if not self.skip_risk:`
  分岐（`fetch_risk_events`呼び出し）は本修正で一切変更していないため、
  コードレベルで回帰なしを確認済み（Grok API実費が発生するため実行での
  再確認は行わず、CLAUDE_CODE_START.mdの「手動実行時は--skip-risk推奨」
  方針に従った）。
- **pytest**: 406件中404 passed・2 failed（`test_iv_formula.py`のMSFT/NVDA、
  [[TEST-STALE-IV-1]]として既知・登録済みの事前確認済み失敗のみ）。
- **report_consistency_check.py --fail-on-ng**: NG=0（WARN=69件、既存分
  から変化なし）。

#### 着手条件（消滅・完了）
なし（実装完了）

---

### ✅ [FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1] 決算期変更境界のバケツ競合検知（WARN-24新設・クラスタリングスキャン補助ツール化）
**優先度:** 中
**分類:** アーキテクチャ / データ品質ゲート
**登録日:** 2026-07-18
**完了日:** 2026-07-19
**発見:** RCAT型決算期変更検知 事前調査（ARCH-DATA-1派生）

#### 問題（再掲）
決算期を実際に変更した企業で、変更の境界年に「真の本人データ」と
「翌年の10-Kが比較年度として再掲した非本人データ」が同一computed_year
に衝突するケースが、既存の検知網（CHECK-22/CHECK-23）のいずれにも
引っかからず記録されない。RCAT（決算期を2回変更）で実在確認済み。

#### 設計調査での結論（実装前に確定・実装方針の根拠）
- 105銘柄クラスタリングスキャン（support≧2・循環距離30日超）は独立
  スクリプトとして残っておらず一時的なアドホック分析だったことを確認。
  `common/sec_data/utils.py::_cluster_fiscal_anchor_candidates()`は
  再利用可能な純関数（入力: day_counts、出力: クラスタのリスト）として
  現存することを確認し、これを再利用する形で候補抽出ツールとして
  常設化した（後述）。
- **クラスタリングはWARN-24本体の発火条件には採用しない**（設計判断の
  根拠）: クラスタリングは「決算日の分布が過去2箇所に分かれている」と
  いう統計的シグナルに過ぎず、実際の年度バケツ競合を保証しない。事前
  調査時点で4候補（RCAT/ELF/MSCI/NOW）中、実際に競合していたのは
  RCATのみで、ELF/MSCIは決算期変更はあったが競合なし、NOWは単発の
  参考開示によるノイズだった。誤検知率が高いため、常設WARNの発火条件
  としては不適切と判断した。
- WARN-24本体は`parser.py`側での精密な検知（既存側・本人データ候補側の
  実際のバケツ競合発生時のaccn・fyタグ・end_date単位での記録）を採用。
  CHECK-22（同一fyタグ前提）・CHECK-23（勝者自身のfyタグとバケツの
  不一致、敗者側は対象外）のいずれとも異なる軸で、「fyタグが元々異なる
  2エントリが同一バケツで競合する」ケースを対象とする。

#### 実装内容
- **parser.py**: `_own_override_is_safe()`自体は変更せず（既存テスト済み
  の安定関数のため）、`_extract_values_best_candidate`・
  `_extract_values_merged`の2箇所で、既存側と本人データ候補側の情報を
  比較する新規メソッド`_is_boundary_collision()`（純関数、テスト容易性
  のため独立実装）と`_fiscal_anchors_far_apart()`（(月,日)の循環距離が
  30日超かを判定）を新設。
  - **実装中の重要な発見・設計修正**: 当初「生fyタグが異なる・end_dateが
    異なる」のみを条件にしたところ、ADSK/AVAV/CAKE/CRM等**7銘柄**で
    誤って発火した。原因は、固定決算日企業で「同一の(月,日)・隣接する
    暦年」の組み合わせ（filer側のfyタグが実際の期間より1年ずれる
    WARN-23既知パターン、例: end=2011-01-31/fy=2010とend=2012-01-31/
    fy=2011）が、単なる年ズレであるにも関わらず境界衝突と誤認識されて
    いたため。`_fiscal_anchors_far_apart()`（(月,日)循環距離>30日）を
    追加の必須条件とすることで、この7銘柄を正しく除外した（詳細は
    下記検証結果参照）。
  - 新規`_save_fye_boundary_collision_log(ticker, records)`メソッドを
    `_save_fy_collision_log`/`_save_fy_tag_mismatch_log`と同一パターンで
    新設。0件でも毎回書き込む。出力先:
    `common/sec_data/data/{TICKER}/fye_boundary_collision_log.json`
- **report_consistency_check.py**: `_read_fye_boundary_collision_log()`・
  CHECK-24（WARN-24、非ブロッキング）を既存2チェックと同一パターンで新設。
- **common/sec_data/fye_change_candidate_scan.py**（新規ファイル）:
  `_cluster_fiscal_anchor_candidates()`を再利用した候補抽出補助ツール。
  WARN-24の発火条件には使わず、新規銘柄登録時・定期監査時の手動実行を
  想定。「誤検知を含みうる統計的シグナルである」旨を冒頭コメントに明記。
- **tests**: `tests/test_fiscal_year_anchor_window.py`に
  `_fiscal_anchors_far_apart()`・`_is_boundary_collision()`の単体テスト
  9件（RCAT型で発火・fy_tag一致で非発火・同一end_dateで非発火・
  ADSK型〈同一(月,日)・隣接暦年〉で非発火・既存側なしで非発火 等）、
  `tests/test_report_consistency_check.py`にCHECK-24読み取り側のテスト
  4件（既存のCHECK-23テストと同一パターン）を追加。

#### 検証結果
- **全100銘柄再生成**（`parser.parse_company_facts()`を全銘柄に対しメモリ内
  実行、`fye_boundary_collision_log.json`のみを新規生成する安全な方式で
  実施。既存のannual/quarterly/raw/normalized等は一切変更しない）:
  `fye_boundary_collision_log.json`が非空になったのは**RCAT（2件）・
  LITE（1件）・WST（1件）の3銘柄**（当初想定「RCATのみ」とは異なる結果。
  下記「想定外の発見」参照）。ELF/MSCI/NOWは想定通り空のまま。
- **想定外の発見（LITE・WST）**: いずれも`_fiscal_anchors_far_apart()`
  フィルタ通過後も残った、単発の孤立した比較年度エントリ（LITE:
  net_income、end=2015-08-01がfy=2018の10-Qで参考開示。WST: rpo、
  end=2013-06-30がfy=2022の10-Kで参考開示）。両者とも`override_applied:
  true`（現在のパイプラインは既に正しい本人データ側の値を採用済み）で
  あり、RCATのような継続的な決算期変更パターンとは異なる、NOW型と同種の
  「単発の参考開示ノイズ」の可能性が高いと判断。ただし個別の一次情報
  確認は未実施のため、WARN-24は非ブロッキング・未確認のまま残し、
  **[[FYE-BOUNDARY-COLLISION-UNCONFIRMED-1]]としてBACKLOG.mdへ独立
  タスク登録した**（override_applied=trueで現在のデータに実害はないが、
  一次情報未確認のまま残っている旨を明記。WARN-24自体が「非ブロッキング
  な可視化」を目的とする設計のため優先度は低〜未定とし、[[BS-FIELD-
  NEWLY-MISSING-2026-1]]のような実害のあるデータ欠損とは性質が異なる
  と判断）。
- **クラスタリングスキャンツール再実行**: RCAT/ELF/MSCI/NOWの4銘柄のみ
  該当（事前調査結果と完全一致、新規候補の増加なし）。
- **pytest**: 403件中401 passed・2 failed（`test_iv_formula.py`のMSFT/NVDA、
  [[TEST-STALE-IV-1]]として既知・登録済みの事前確認済み失敗のみ）。
- **report_consistency_check.py --fail-on-ng**: NG=0。WARN合計69件
  （確認済み50・未確認19、内訳: WARN-24由来の新規未確認3件〈RCAT/LITE/
  WST〉＋既存の未確認16件）。
- **既存チェックへの影響**: WARN-22/23はADSK/CAKE/COHR/CRM/FCX/FICO/HON/
  WMT等で従来通り発火し、WARN-24とは独立して動作することを確認
  （`_fiscal_anchors_far_apart()`フィルタにより、これら8銘柄で
  WARN-24が誤って発火することはない）。SECデータ層は
  `fye_boundary_collision_log.json`の新規追加以外に変更なし
  （実行中に無関係な既存データdrift〈AVAV/COHR/FICO/HONのfy_collision_
  log.json、以前のNVDA/WARN-26タスクで確認済みの再生成漏れと同種〉が
  発生したがコミット前に復元済み、本タスクのスコープ外）。

#### 着手条件（消滅・完了）
なし（実装完了）

---

### ✅ [BS-FIELD-NONE-TRANSITION-DETECT-1] BS項目「前年有値→当年None」遷移検知（WARN-26新設・既知8件事前登録）
**優先度:** 中〜高
**分類:** データ品質ゲート / 検知体制
**登録日:** 2026-07-19
**完了日:** 2026-07-19
**発見:** [[NVDA-STI-TAG-UNIDENTIFIED-1]]調査中の体制確認（XBRLタグ申告停止による
完全欠損の検知が、BS項目に関して一切存在せず、実例6件がいずれも偶然発見だった
ことが判明）

#### 事前確認（実装前調査、着手条件の事前クリア）
WARN-26実装前に、[[FY52WEEK-BS-NULL-SILENT-1]] Phase B/Cで確認済みの「生涯
フェードアウト」25件（short_term_investments/long_term_debt/short_term_debt/
rpoのいずれかで過去に明示的`val=0`の申告実績があるが最新年度でタグ自体が
欠損している組み合わせ）が、実際にWARN-26の発火条件（直近2年度分の
annual_*.json比較）に該当するか個別確認した。結果:
- 25件中8件（APP/short_term_debt・BKNG/short_term_investments・CPRT/
  long_term_debt・DOCN/short_term_investments・ENTG/short_term_debt・
  KULR/short_term_debt・MSCI/short_term_debt・SOUN/long_term_debt）は
  遷移年が最新年度と一致し、実装直後に発火することを確認
- 残り17件は遷移が2年より前に既に発生済みで、直近2年度は両方ともNoneのため
  発火しない（PLTR long_term_debt等）
- RCAT（long_term_debt）は遷移年2024が[[FYE-CHANGE-BOUNDARY-COLLISION-
  BLIND-1]]で確定済みの決算期変更境界（2024-2025年）と一致する実例だが、
  現時点では発火対象外（将来別ケースで境界がずれ込んだ場合の潜在リスクとして
  コード内コメントに記録）
- 新規登録銘柄（annual_*.jsonが1年分のみ）の混入はゼロ件

#### 実装内容
- **report_consistency_check.py**: CHECK-26（WARN-26）を新設。short_term_
  investments/long_term_debt/short_term_debt/rpoを対象に、直近2年度分の
  annual_*.jsonを比較し`prior_bs.get(field) is not None and latest_bs.get(field)
  is None`でWARN発火。period（fyラベル）の年度差が厳密に1でない場合（決算期
  変更等でfiles[-2]が真の「1年前」を表さない可能性がある場合）・
  annual_*.jsonが1年分のみ（新規登録銘柄）の場合は判定不能として発火させない
  設計とした（誤判定より見逃しを優先）。
- **config/warn_acknowledged.json**: 事前確認済みの8件を(WARN-26, ticker)単位で
  登録（既存スキーマに準拠。フィールド名はcommentに明記）。
- **tests/test_report_consistency_check.py**: `TestCheck26BsFieldNoneTransition`
  （遷移検知・年度差≠1でのスキップ・新規登録銘柄でのスキップ・複数フィールド
  列挙・対象外フィールドの無視、計7件）と`TestWarn26KnownFadeoutAcknowledged`
  （既知8件が本番のwarn_acknowledged.jsonで確認済み扱いになることの回帰、1件）
  を新設。既存の`TestCheck23FyTagMismatch`と同一パターン（monkeypatchで
  `rcc.DATA_DIR`/`rcc.SEC_DATA_DIR`をtmp_pathへ差し替え）で実装。
  **注記**: 依頼書はtests/test_pipeline_logic.pyへの追加を指定していたが、
  report_consistency_check.py::check_ticker()の単体テストに必要な
  monkeypatch基盤（DATA_DIR/SEC_DATA_DIR差し替え）が既にtests/
  test_report_consistency_check.pyに整備済み（WARN-21/23が同パターンで
  実装済み）だったため、モジュール境界に合わせてそちらに実装した。

#### 検証結果
- **全100銘柄再実行**: WARN-26が新規に11件発火（想定8件＋想定外3件）。
  想定8件はすべてwarn_acknowledged.json登録により「確認済み」表示（🆕マーク
  なし）。総計 NG=0 / WARN=66件（確認済み50・未確認16、内訳: WARN-26由来の
  未確認3件＋既存の未確認13件）。`--fail-on-ng`ゲート通過。
- **想定外3件（LLY/short_term_investments・SCCO/short_term_debt・
  SPIR/long_term_debt）の調査**: 実装ミスではなく、いずれも直近年度
  （FY2025）で**実際に非ゼロの値**（LLY $154.8M・SCCO $499.8M・SPIR $4.618M）
  が申告されていたのに、最新年度でタグ自体が欠損する**本物の新規遷移**。
  事前調査時点（[[FY52WEEK-BS-NULL-SILENT-1]] Phase B/C確認）の「生涯
  フェードアウト25件」は「過去に明示的$0の申告実績がある」ケースに限定して
  抽出しており、この3件（過去は非ゼロの実額）は元々その25件の定義に該当
  しない別カテゴリだった。GitHub Actionsによる自動データ更新でFY2025分の
  annual_*.jsonが事前調査時点より新しくなったことで新たに顕在化したとみられる。
  一次情報（10-K原本）での確認は未実施のため、warn_acknowledged.jsonへの
  登録は行わず「🆕未確認」のまま残し、[[CASH-TAG-MISSING-1]]と同様に一次
  情報確認が必要な事項として**[[BS-FIELD-NEWLY-MISSING-2026-1]]をBACKLOG.md
  へ独立タスクとして新規登録した**（本タスクのスコープ外のため、本コミット
  では原因調査・修正は行わない）。
- **pytest**: 390件中388 passed・2 failed（`test_iv_formula.py`のMSFT/NVDA、
  [[TEST-STALE-IV-1]]として既知・登録済みの事前確認済み失敗のみ。新規failなし）
- **既存チェックへの影響**: WARN-25はCPRT/GEV/HEI/SITM/SOFIの5件（本タスクと
  無関係、CASH-TAG-MISSING-1由来。前回セッション時点の2件〈SITM/SOFI〉から
  増えているのは、GitHub Actions自動更新でCPRT/GEV/HEIのannual_2025.jsonが
  新たに追加されデータが進んだためで、CHECK-25コード自体は本タスクで一切
  変更していない）。WARN-21/22/23等の既存チェックの発火内容にも変化なし。

#### 対応方針として先送りした事項
[[FY52WEEK-BS-FADEOUT-FALLBACK-1]]（生涯フェードアウト25件への履歴フォール
バックロジック本体、「過去に明示的$0実績があれば真のゼロと推定表示する」設計）
は、本タスクのスコープ外として引き続き別タスクのまま残す。理由: WARN-26は
「検知」のみを目的とし、`warn_acknowledged.json`による事前登録で当面の
アラート疲れは回避できているため、フォールバック表示ロジック自体の実装
（残高推定・report.txt表示形式・信頼度低下の年数閾値等の設計論点）を今回
同時に着手する必然性がない。将来的にwarn_acknowledged.json台帳が肥大化する
場合や、フェードアウト銘柄の推定残高をreport.txtに明示したいという別の
ニーズが生じた場合に、独立したタスクとして着手する。

#### 着手条件（消滅・完了）
なし（実装完了）

---

### ✅ [NVDA-STI-TAG-UNIDENTIFIED-1] short_term_investmentsのNVDAは対応タグ未特定（対応方針①採用・cross_filing_tags機構で実装完了）
**優先度:** 中〜高
**分類:** アーキテクチャ / データ品質ゲート
**登録日:** 2026-07-19
**完了日:** 2026-07-19
**発見:** [[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]（完了）実装時、KLAC/TER/V/SOFIの
4銘柄は解決したがNVDAのみ対応タグ未特定のため分離。個別調査の結果、
[[ANOMALY-PATTERN-CATALOG-1]]型C（資産クラス変化・当年度未タグ化型）と判明。

#### 問題（調査結果の要約）
FY2026（会計年度末2026-01-25）第1四半期に、非上場だった投資先1社が上場した
ことで保有株式が非上場株式からmarketable securities区分へ再分類され、単一
XBRLタグでの捕捉が不可能になった。債券部分`AvailableForSaleSecuritiesDebtSecurities`
（$39,520M、当該10-K本体に申告あり）＋株式部分`EquitySecuritiesFvNi`
（$12,886M）を合算すると近似値$52,406M（実額$51,951M比+0.88%）となるが、
`EquitySecuritiesFvNi`は当該10-K本体には一切申告されておらず、後続10-Q
（2026-05-20提出、Q1 FY2027）の比較年度遡及開示にのみ登場するため、単一
filing内では解決できず既存の`sti_concept`方式（KLAC/TER/V/SOFI）は適用不可。

#### 実装内容（対応方針①: 複数タグ合算近似値＋残差明示、採用）
- **quarterly.py**: `TICKER_RESTRICTIONS["NVDA"]`に新エントリ種別
  `cross_filing_tags`を追加。ticker×period×fieldを明示指定した場合のみ、
  指定end_date・指定form制限で複数XBRLタグを直接検索し合算する。
  - annual FY2026（end 2026-01-25）: 主タグ`AvailableForSaleSecuritiesDebtSecurities`
    （form限定10-K/10-K/A）＋補助タグ`EquitySecuritiesFvNi`（form限定10-Q、
    真のクロスfiling参照）を合算。`approx_residual_pct=0.0088`を明示登録。
  - quarterly 2027Q1（end 2026-04-26）: 両タグとも当該10-Q自身のown data
    （form=10-Q）だが、既存の`_extract_values_best_candidate()`が複数タグ
    同時合算に対応しないため同一機構を転用。近似ではなく正規合算値。
- **parser.py**: `_find_entry_by_end_date()`（指定タグ・end_date・form群への
  ピンポイント検索。既存の`_collect_own_data_annual/_instant`が持つ
  `form in (10-K, 10-K/A)`フィルタ・accn_reportdate自己一致チェックを
  意図的に迂回する唯一の経路）と`_apply_cross_filing_tags()`
  （`TICKER_RESTRICTIONS`の`cross_filing_tags`に明示登録された組み合わせに
  のみ発火し、複数タグ合算値でextracted辞書の該当バケツを上書き）を新設。
  `_parse_raw_data()`の標準抽出ループ後に適用し、既存の抽出ロジック自体は
  一切変更しない（他の全銘柄・全フィールドの既存挙動に影響なし）。
- **reader.py**: `get_net_cash()`にannual側`bs_provenance.short_term_investments.
  is_approximated`/`residual_pct`を読み取り、返却dictに`sti_approximated`/
  `sti_residual_pct`として追加。四半期側の値に上書きされた場合はFalse/None
  にリセット（四半期側は同一filing内合算のため近似ではない）。
- **adjustments.py**: `BSAdjustmentResult`に`sti_approximated`/`sti_residual_pct`
  フィールドを追加し`to_dict()`で伝播。
- **pipeline.py**: `financial_health`辞書に同フィールドを追加。report.txtの
  ST_Invest行に、近似値採用時のみ残差率注記
  （例: `ST_Invest: $52.41B (近似値、実額比+0.88%)`）を追加する表示分岐を実装。
- **report_consistency_check.py**: CHECK-27（WARN-27 近似値残差過大）を新設。
  `bs_provenance[field].is_approximated=True`のエントリで`residual_pct`が
  閾値5%を超過した場合のみ発火する安全網（NVDA自身は+0.88%のため非発火。
  cross_filing_tags機構の将来の再利用先向け）。
- **tests/test_pipeline_logic.py**: `TestNvdaCrossFilingSTI`クラスを新設し、
  annual FY2026の合算近似値$52,406M・残差フラグ、quarterly 2027Q1の正規
  合算値$69,470M、latest.jsonが四半期の非近似値を採用すること（BUG-NETDEBT-4
  との整合）の3件を回帰テスト化。

#### 実装中に発覚した設計上の分岐点（ユーザー判断済み）
`reader.py::get_net_cash()`のBUG-NETDEBT-4「同一時点原則」により、annual FY2026
のみにcross_filing_tagsを実装しても、最新四半期（2027Q1）にCash/LTDebtが揃って
いる限りreport.txt/latest.jsonの表示には反映されない（四半期側が優先される）
ことが実装中に判明。ユーザー判断により、四半期(2027Q1)側にも同一の複数タグ
合算機構を適用し、両方の期で正しい値が得られるようにした（reader.pyの
同一時点優先ロジック自体を迂回する案は、BUG-NETDEBT-5由来の期ズレ防止という
別の設計目的と衝突するリスクがあるため不採用）。

#### 検証結果
- **annual FY2026**（`common/sec_data/data/NVDA/annual_2026.json`）:
  `bs.short_term_investments=52,406,000,000`（合算近似値）・
  `bs_provenance.short_term_investments={is_approximated: true, residual_pct: 0.0088,
  combined_tags: [AvailableForSaleSecuritiesDebtSecurities, EquitySecuritiesFvNi]}`
- **quarterly 2027Q1**（`quarterly_2027Q1.json`）:
  `bs.short_term_investments=69,470,000,000`（$39,233M+$30,237Mの正規合算値）
- **latest.json/report.txt**（`docs/value-monitor/tanuki_valuation/data/NVDA/`）:
  修正前 `short_term_investments=0.0, net_debt=-4,767,000,000`（STI欠損によりNet Debt
  過小評価）→ 修正後 `short_term_investments=69,470,000,000, net_debt=-74,237,000,000,
  sti_approximated=false, sti_residual_pct=null`（net_debt_period="2027Q1"のため
  四半期の正規値を採用、近似値フラグは伝播しない）。Intrinsic_Value: $774.69→$777.56
- **他104銘柄への影響確認**: `TICKER_RESTRICTIONS`に`cross_filing_tags`を持つのは
  NVDAのみであることをコードレベルで確認（`if _cross_filing_tags:`ガードにより
  他銘柄では新規コードパス自体が実行されない）。KLAC/TER/V/SOFI/AAPL/MSFTを
  対象にparser.py単体実行でshort_term_investments抽出値が既知の値と完全一致する
  ことをスポットチェックで確認（全銘柄一括再生成は、無関係な既存データ staleness
  との切り分けコストが高いため実施せず、コードレベルのガード確認に留めた）
- **pytest**: 382件中380 passed・2 failed（`test_iv_formula.py`のMSFT/NVDA、
  [[TEST-STALE-IV-1]]として既知・登録済みの事前確認済み失敗のみ。新規failなし）
- **report_consistency_check.py**: 全100銘柄でNG=0（実行前後で変化なし）。
  WARN合計55件（確認済み42・未確認13、いずれもNVDAのSTI以外の既存WARN
  〈WARN-21/22/23〉およびSITM/SOFI/WMTの既存WARNで、本対応による新規WARNは
  ゼロ）。新設WARN-27は全銘柄で非発火（NVDAの残差+0.88%は閾値5%未満）

#### 実装中に発見した別課題（未修正・スコープ外）
NVDAデータ再生成時、`annual_2010/2011/2012/2013/2015/2016/2017/2018.json`の
`other.rpo`フィールドおよび`raw/normalized/NVDA_quarterly_*.json`・
`common/sec_data/ttm/NVDA_ttm_series.json`に、本対応（short_term_investments/
cross_filing_tags）と無関係なドリフトが検出された。既存コード（本セッションで
一切変更していないベースラインのparser.py/quarterly.py）でも同一ドリフトが
再現することを確認済みで、NVDAのコミット済みデータが現在のコードに対して
単純に陳腐化していた（過去のいずれかのタイミングで再生成漏れが発生した）
ことによるものと判断。本対応のスコープ外のため、当該ファイルはコミット前に
ベースラインへ復元し、この発見のみ記録に残す（要すれば別途調査・再生成の
判断を仰ぐ）。

---

### ✅ [GROWTH-SANITY-CLASS-SYNC-1] growth_sanity.verdictがDCF_Reliability/Classification判定と未連動（MO型iv実装で解消、2026-07-19完了）
**優先度:** 高
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-11
**完了日:** 2026-07-19
**発見:** [[POLICYB-GATE-FIX-1]]横断調査時（DCF_Reliability関連ゲートの棚卸し）

#### 問題
`growth_sanity.py`の`check_growth_sanity()`が返す`verdict`（PLAUSIBLE/REVIEW/
AGGRESSIVE/FLOOR_HIT_REVIEW）は、report.txtの`[4] 成長率根拠`セクションに
表示されるのみで、TANUKI SCORE Classification・DCF_Reliability判定には
一切反映されない（pipeline.py内でverdictを参照するのは`GROWTH_PREMIUM`判定用の
`phase1_growth`取得箇所のみで、verdict自体を条件分岐に使う箇所は存在しない）。

2026-07-11時点の実データ確認では、**MO（Classification: BUY）が
`verdict=FLOOR_HIT_REVIEW`・`floor_hit=True`のまま**である（成長率算出ロジックが
破綻し、実績と無関係な機械的floor値15%を採用しているにも関わらず、BUY判定が
変わらない）。LOAR（WATCH）・XOM（HOLD）も同verdictだが、既に低い分類のため
実害は限定的。`report_consistency_check.py`のCHECK-20（WARN-20）でも検知されるが、
WARNは非ブロッキングのため見落とされやすい。

#### [[GROWTH-FLOOR-VERDICT-1]]・[[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）との関係
[[GROWTH-FLOOR-VERDICT-1]]（2026-07-11完了）は、fcf_cagr経路の成長率がfloor値に
機械的に張り付くケース（MO/LOAR/XOM）の**検知**（`verdict=FLOOR_HIT_REVIEW`・
`floor_hit`フィールド新設・CHECK-20）を意図的なスコープとして実装しており、
Classificationへの反映は最初から対象外だった（BACKLOG_DONE.md参照）。

[[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）が当初から問題意識としていた
「信頼できない前提のBUYがスクリーニングを素通りする」という同じ課題の、fcf_outlier系列とは別の
バリエーション（成長率前提の信頼性）にあたる。[[POLICYB-GATE-FIX-1]]で
fcf_outlier系（Policy A/B）側は解消したが、growth_sanity系はまだ未着手。

#### 対応方針（未確定・次回セッションで設計判断）
- Policy A/B同様の「WATCHへの丸め」を追加するか、別Policy（Policy C等）として
  新設するかは未確定
- MO/LOAR/XOMの3銘柄はいずれもfcf_cagr経路のみで発生する既知パターンだが、
  今後segment_weighted等の他経路でも同種の「算出不可・機械的floor採用」が
  起きうるか確認が必要
- Policy A/Bとの優先順位・同時発火時の扱い（floor_hit=Trueとfcf_outlier flaggedが
  同一銘柄で重複する場合の丸めメッセージの一貫性）を設計時に検討する

#### 状況更新（2026-07-11）: [[GROWTH-CAGR-SIGN-1]]によりMO/LOARのfloor_hitが解消
本タスクの発見過程（growth_sanity調査）で、`calculate_fcf_cagr()`のCAGR計算式
自体に符号反転バグがあることが判明し、[[GROWTH-CAGR-SIGN-1]]として分離・修正した
（詳細はBACKLOG.md該当エントリ参照。全銘柄再生成保留中のため未アーカイブ）。
修正の結果、**MO・LOARは`floor_hit=False`
（verdict=PLAUSIBLE）に変わり、本タスクが問題視していた「MO（BUY）がfloor張り付き
のままBUY判定が変わらない」という最も緊急性の高い実例は解消済み**。
`verdict=FLOOR_HIT_REVIEW`のまま残るのはXOM（Classification: HOLD）のみとなり、
既に非BUYのため実害は限定的。

ただし[[GROWTH-CAGR-SIGN-1]]の修正確認時、MOの成長率が15.0%→29.9%に変わったことで
IV乖離率が+34.9%→+286.3%へ大きく変動する事象が判明し、根本原因は
[[TTM-QUARTERS-CHECK-1]]（TTM系列構築時の四半期完全性チェック不足）と
確定した（一過性の事業要因ではない）。この点も踏まえ、**本タスク（growth_sanity.verdictの
Classification連動）は緊急性が下がったため、着手要否を次回セッションで改めて判断する**。

#### 状況更新（2026-07-12）
[[TTM-QUARTERS-CHECK-1]]・[[GROWTH-CAGR-SIGN-1]]完了に伴い全銘柄再生成した結果、
MOのverdictは再び`FLOOR_HIT_REVIEW`・`floor_hit=True`に戻った
（Classification: BUY）。本タスクが問題視していた「MO（BUY）がfloor張り付きの
ままBUY判定が変わらない」という実例は未解消のまま残っている。ENTG/GEV/HQY
（PLAUSIBLE→REVIEW）、HWM（PLAUSIBLE→AGGRESSIVE）の新規verdict変化も発生しており、
Classification未連動の実害範囲がむしろ拡大した。次回セッションでの着手優先度を
改めて検討する必要がある。

#### 設計再検討（2026-07-12・セッション議論）
本タスクを「growth_sanity.verdictをClassificationに丸めて反映する」という
単発対応として進める方針（Policy A/B型のWATCH丸め）は不採用と判断した。
理由は、Classification自体を丸めても「なぜ信頼できないのか」という情報が
握りつぶされ、数値をそのまま受け取って良いかの判断材料としてはむしろ後退
するため。

代わりに、信頼性が崩れうる段階を洗い出したところ、以下の3段階が直列に
連鎖していることが判明した：
- **段階0（データ完全性）**: TTM系列・年次実績等の入力データ自体が完全か
- **段階1（成長率算出）**: `growth_sanity.verdict`。report.txtのみに表示
- **段階2（FCF/DCF計算）**: `fcf_outlier.detected`。Policy A/B経由で
  Classificationに反映済み

さらに議論の中で重要な軸が1つ抜けていたことが判明した：「信頼できない」と
判定された事象には、**構造的に解消不能なもの**（可視化するしかないもの）と、
**取得・算出ロジックの不備で本来解消可能なもの＝バグ**が混在しており、
これを区別せずに一律で可視化対象にすると、直せるはずのバグが「これは
限界です」という顔をして放置され続けるリスクがある（実例：
[[LLY-CAPEX-STALE-1]]（完了・BACKLOG_DONE.md参照）は「データが存在しないから
信頼度を下げて表示する」話ではなく、本来取得できるはずのCapEx四半期データが
取得ロジックの不備で取れていない、解消可能な事例だった。実際にPhase 2aで
根本原因（タグ切替の見逃し）を解消済み）。

方針は「Classificationを書き換える」のではなく「**各数値がそのまま信じて
良い状態か、信じてはいけない状態かを一目で分かるようにする**」ことが目的だが、
可視化に着手する前に、まず個々の「信頼できない」事象が解消可能（バグ）か
構造的限界かを切り分ける工程を挟む。詳細は[[TRUST-SUMMARY-EPIC-1]]参照。

#### 状況更新（2026-07-19）: MO型iv（floor到達）を解消、残る論点は分離登録

[[TRUST-SUMMARY-EPIC-1]]完了後の段階1（成長率算出）棚卸しで、本タスクが
当初問題視していた「MO（BUY）がfloor張り付きのままBUY判定が変わらない」を
含むverdict≠PLAUSIBLE全32銘柄を(i)候補タグ欠落等のシーケンシングバグ・
(ii)入力データ不完全性・(iii)構造的ミスマッチ・(iv)floor設計の妥当性、
の4類型に分解した（詳細な調査記録は同日の複数セッション参照）。

**MO単体（型iv）は本日解消済み**:
- 原因: ①`beta_config.json`にMOの`sector`未設定でDamodaran業種
  ベンチマークがNone、②`recommended_g`算出候補（rev_cagr_3yr/5yr・
  g_fundamental・industry_benchmark）が全てNone/マイナスで候補0件のため
  `recommended_g`が機能せず、`calculate_fcf_cagr()`の生floor=15%が
  そのままDCFに採用されていた
- 対応: `growth_sanity.py::TICKER_INDUSTRY_OVERRIDES`に`"MO": "Tobacco"`を
  追加（Damodaranデータセットに実在するTobacco業種g_ebit≈1.5%を取得可能に）。
  加えて、`fcf_cagr`経路でfloor(15%)に到達しておりindustry_g単独1件のみが
  候補となる銘柄に限り、中央値の候補数閾値を2件から1件へ緩和する分岐を追加
  （事前検証でLOARのような真の高成長銘柄への一般適用は成長率過小評価の
  副作用があると確認済みのため、floor到達中の銘柄のみへ厳密に限定）
- 結果: MOの`growth.source`が`fcf_cagr`→`segment_weighted`（rate 15.0%→1.5%）、
  `floor_hit`が`True`→`False`、Classification`BUY`→`HOLD`、
  乖離率+111.8%→-25.4%に変化。LOARを含む他99銘柄は完全に無変化を確認済み

**検証結果:**
- MO単体再生成: `growth.source`が`fcf_cagr`→`segment_weighted`、
  `growth_sanity.recommended_g`がTobacco g_ebit（1.5015%）と一致、
  `floor_hit`が`False`に変化することを確認
- 全100銘柄再生成による新旧比較: Classification変化はMOのみ（BUY→HOLD）、
  `growth.source`変化もMOのみ、`floor_hit`変化もMOのみ、
  MO以外のIntrinsic_Value変化はゼロ件（LOAR含む）
- `report_consistency_check.py --fail-on-ng`: NG=0（WARN 56→55、MOの
  WARN-20〈fcf_cagr floor張り付き〉が解消したことによる想定通りの減少）
- `pytest tests/ -v`: 377 passed / 2 known failures（MSFT/NVDA、
  [[TEST-STALE-IV-1]]、本タスクと無関係）
- MOの`formula_verification`検証WARN（alpha cap起因）は本修正と無関係の
  既存WARNであることをHEAD比較で確認済み

**残る論点は今回のスコープ外として個別分離登録した**（詳細は各エントリ参照）:
- [[GROWTH-VERDICT-SEQUENCING-BUG-1]]（型i・24銘柄・優先度：高相当）:
  本タスクが本来最も広く扱うべきだった「verdictが1回目パス〈override前〉の
  値を検証し続ける」根本バグ。VZ（BUY）を含む実害あり
- [[WST-SECTOR-MISCLASSIFICATION-1]]（型ii）
- [[GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1]]（型iii・[[TRUST-SUMMARY-EPIC-1]]
  可視化候補）
- [[JOBY-STATIC-GROWTH-HARDCODE-1]]（副次発見）
- [[JNJ-XOM-PM-FLOOR-RISK-1]]（潜在リスク監視）

#### コミット
- `46b5e911d`: fix: GROWTH-SANITY-CLASS-SYNC-1 MOのfloor(15%)問題を解消
  （growth_sanity.py・BACKLOG.md・BACKLOG_DONE.md）
- `1691e3622`: data: TANUKI VALUATION 全100銘柄再生成（MOのfloor問題解消を反映）

---

### ✅ [FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1] BS4フィールド標準タグ追加（57件・41銘柄、2026-07-19完了）
**分類:** バグ修正 / データ品質ゲート / SECデータ正規化
**登録日:** 2026-07-15（本体）/ 2026-07-19（Stage1着手）
**完了日:** 2026-07-19
**発見:** [[FY52WEEK-BS-NULL-SILENT-1]] Phase B/C absent銘柄全179件の一次情報（SEC EDGAR 10-K原本）個別確認

#### 背景
Phase A完了時点で保留されていたPhase B/C対象4フィールド
（short_term_investments/long_term_debt/short_term_debt/rpo）の
absent銘柄179件（105銘柄中）について、複数セッションにわたる
一次情報調査（SEC EDGAR 10-K原本の直接取得・照合）を実施し、
以下3類型に分解した：

- **①候補タグ欠落（CASH-TAG-MISSING-1と同型）**: タグリスト拡充で
  安全に解消可能
- **②生涯フェードアウト**: 過去に明示的$0申告実績があるが最新年度で
  タグ自体が申告されない
- **③真の構造的ゼロ**: 候補タグのいずれにも申告実績が一切ない

①のうち、10-K原本で単一の標準候補タグ追加により安全に解消でき、
かつ既存のticker override機構（SOFI-DATA-1の`ltdebt_concept`等）と
衝突しないことを個別確認した57件（41銘柄）をStage1として実装した。

#### 実装内容
`common/sec_data/parser.py`の`XBRL_MAPPING`に以下の候補タグを、
既存タグの後段（フォールバック）として追加：

- **short_term_investments**（15銘柄: ALAB/BBAI/CRM/DDOG/GTLB/INTU/IOT/
  KO/NET/NOW/RBRK/RMBS/SITM/VRT/ZS）: `AvailableForSaleSecuritiesDebtSecuritiesCurrent`・
  `DebtSecuritiesAvailableForSaleExcludingAccruedInterestCurrent`・
  `DebtSecuritiesHeldToMaturityAmortizedCostAfterAllowanceForCreditLossCurrent`・
  `OtherShortTermInvestments`
- **long_term_debt**（15銘柄: AVGO/CDNS/CON/DDOG/HEI/KO/NET/NOW/ONDS/PM/
  RBRK/RXRX/VZ/XOM/ZS）: `LongTermDebtAndCapitalLeaseObligations`・
  `UnsecuredLongTermDebt`・`ConvertibleLongTermNotesPayable`・
  `ConvertibleDebtNoncurrent`・`OtherLongTermDebt`
- **short_term_debt**（7銘柄: CON/DDOG/ELF/NET/QBTS/RXRX/ZS）:
  `LongTermDebtAndCapitalLeaseObligationsCurrent`・
  `ConvertibleNotesPayableCurrent`・`ConvertibleDebtCurrent`・
  `OtherLongTermDebtCurrent`
- **rpo**（20銘柄: ADSK/ALAB/APP/BBAI/CAKE/CART/CELH/CIX/CPRT/DOCN/ENTG/
  FLYW/INTU/JOBY/KULR/MRVL/RXRX/TASK/VRT/ZETA）:
  `ContractWithCustomerLiabilityCurrent`・`DeferredRevenueCurrent`

**明示的に対象外**（Stage2/3・二重計上リスク等として個別に除外確認済み）:
- short_term_investments: CAT・LLY（BS本体に科目行なし、footnote専用）、
  KLAC/NVDA/SOFI/TER/V（[[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]へ分離）
- long_term_debt/short_term_debt: SOFI（既存`ltdebt_concept`
  ticker_restrictionsと衝突、追加すると二重計上）、
  AVAV/ESTC/ZETA（該当額は既にlong_term_debtに正しく計上済み）、
  SCCO（最新年度のCurrent portion of long-term debtが明示的$0）

#### 検証結果
- `common/sec_data/update.py`（41銘柄）実行 → 41/41成功
- 対象57件全件がNone→実値に解消したことを機械確認
- 全41銘柄のannual_YYYY.jsonをHEAD比較 → 対象4フィールド以外への
  意図しない変化ゼロを確認
- SOFIのSECデータ層（company_facts/annual等）が一切未変更であることを
  `git status`で確認（update.py対象に含めていないため）
- `src/value/tanuki_valuation/pipeline.py --skip-risk`で全100銘柄再生成
  → 成功100/100、検証FAIL=2（FRSH/LYFT、anomaly_detection。growth
  rate前提由来の既知パターンで本タスクと無関係、対象41銘柄外）
- Intrinsic_Value変化23銘柄（長期債務捕捉によるIV低下: HEI -28.9%・
  VZ -29.1%・PM -17.9%・XOM -11.7%・CON -48.0%・CDNS -13.8%等、
  流動資産捕捉によるIV上昇: BBAI +29.7%・GTLB +6.5%・RMBS +9.6%等。
  いずれも実際のBS実態を正しく反映する方向の変化であり想定通り）
- Classification変化1銘柄（CON: HOLD→GROWTH_PREMIUM。long_term_debt
  がNone〈実質$0扱い〉→$1.51Bの実債務に修正されNet Debtが正しく
  反映、IV $29.47→$15.32〈乖離率-51.5%〉となりTRIM/GROWTH_PREMIUM
  判定の閾値を跨いだ正当な変化と個別確認済み）
- SOFIのtanuki_score・intrinsic_value_per_shareともに完全不変を確認
  （最重要リスク項目）
- `--skip-risk`使用により68銘柄でrisk_eventsが空配列に上書きされる
  既知の副作用（[[SKIP-RISK-EVENTS-WIPE-1]]）を確認、latest.json/
  report.txt双方でHEAD時点の値へ復元済み
- `report_consistency_check.py --fail-on-ng`: NG=0（WARN 56件は既知/
  無関係、SITM/SOFIのWARN-25はPhase A起因の既知未確認WARN）
- `pytest tests/ -v`: 377 passed / 2 known failures（MSFT/NVDA、
  [[TEST-STALE-IV-1]]、本タスクと無関係）

#### 残タスク
- [[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]（Stage2・優先度：中〜高）
- [[FY52WEEK-BS-FADEOUT-FALLBACK-1]]（Stage3・優先度：中）
- [[FY52WEEK-BS-NULL-SILENT-1]]本体はStage2/3が残るため引き続き
  完了扱いにしない

#### コミット
- `a29e0322d`: fix: FY52WEEK-BS-NULL-SILENT-1 Phase B Stage1 BS4フィールド
  標準タグ追加（parser.py・BACKLOG.md・BACKLOG_DONE.md・SYSTEM_MAP.md）
- `3bf3262ac`: data: SECデータ層41銘柄再生成・TANUKI VALUATION全100銘柄再生成

---

### ✅ [FCF-CONVRATE②] FCF実力推定の固定比率設計限界の可視化（SITM・LITE限定、2026-07-18完了）
**分類:** 可視化 / TANUKI VALUATION / TRUST-SUMMARY-EPIC-1
**登録日:** 2026-07-12（TRUST-SUMMARY-EPIC-1の一部として）
**完了日:** 2026-07-18
**発見:** [[TRUST-SUMMARY-EPIC-1]]棚卸し・原因ベース分析

#### 背景
TRUST-SUMMARY-EPIC-1の方針の骨子②（Classification〈BUY/WATCH等〉は
書き換えず、分類とは独立に信頼性情報を並記する）に基づき、`estimate_
fcf_from_eps()`が用いる業種平均の固定転換率（`fcf_conversion_config.json`
の`sector_conversion_rates`）が、業界サイクルにより年度ごとのFCFが
大きく変動する銘柄を表現できない構造的限界の可視化を実装した。

#### 閾値調査での数学的限界の発見
当初想定7銘柄（SITM/LITE/SPIR/AMZN/SOFI/CWAN/DOCN）についてcv・
divergence_ratioの閾値による機械的切り分けを試みたが、LLY
（cv=0.989, dr=1.92）がDOCN（cv=0.405, dr=1.85）を両軸で完全に上回るため
「どのように閾値を調整してもDOCNを含めればLLYも必ず含まれる」ことが判明し、
閾値方式での自動分離は数学的に不可能と確定した。

#### 原因分析による2銘柄への収束
閾値方式を断念し、境界域のGTLB/LLY/KO/FRSH/SNPSを加えた計12銘柄について
SEC XBRL実データ（`common/sec_data/data/{TICKER}/annual_YYYY.json`、
6-7年分）を用いた個別の原因分析を実施。結果、真に「業界サイクル起因で
解消不能な構造的限界」と呼べるのはSITM・LITEの2銘柄のみと確定した。
残り10銘柄は以下に分解され対象外となった：
- **一時的な成長投資フェーズ（対応不要）**: AMZN・LLY・DOCN・FRSH
- **一過性要因・M&A（[[CWAN-SNPS-MA-DISTORTION-1]]へ分離）**: CWAN・SNPS
- **一次情報不足で未確定（[[KO-SPIR-CF-CAUSE-UNCONFIRMED-1]]へ分離）**: KO・SPIR
- **既存機構で対応済み（新規対応不要）**: SOFI（`stock.html`の
  `FCF_LOW_RELIABILITY_SECTORS`〈Financial Services〉バナーが既に発火済み）
- **成長ステージ＋推定手法混在（記録のみ）**: GTLB

#### 実装内容
- `src/value/tanuki_valuation/pipeline.py`にモジュール定数
  `FCF_CYCLICAL_VOLATILITY_TICKERS = {"SITM", "LITE"}`を新設。
  閾値による自動判定は数学的に不可能と判明済みのため、個別ティッカーの
  手動リスト方式を採用（コメントで理由・将来追加時の手順を明記）
- `docs/value-monitor/tanuki_valuation/stock.html`に同名の`Set`を新設し、
  既存の`FCF_LOW_RELIABILITY_SECTORS`バナー（業種ベース、850-863行）と
  同じUIコンポーネントを流用した別バナーを追加。条件は
  `ticker in FCF_CYCLICAL_VOLATILITY_TICKERS`、文言は「⚠️ FCF実力推定に
  注意（業績サイクル変動）」＋`fcf_estimation.divergence_ratio`を表示。
  両バナーは独立条件のため同時発火可能な設計（現状は該当銘柄が重複しないため
  実際に同時発火するケースはない）
- `pipeline.py`のreport.txt生成箇所（`_generate_report`のFCF_Conversion_Rate
  表示ブロック）に、同条件でdivergence_ratioを追記表示する行を追加
  （既存ではdivergence_ratio自体がreport.txtに非表示だったため新規追加）
- Classification（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）の
  判定ロジックには一切触れない、表示専用の追加であることをコードレビューで
  確認済み（新規コードはいずれも`L.append()`／JSXテンプレートへの追記のみで、
  `valuation`・`score_data`等の判定に使われる変数を変更しない）

#### 検証結果
- SITM・LITEの2銘柄を個別再生成し、stock.htmlバナー・report.txt双方に
  新規表示（divergence_ratio: SITM 3.09倍・LITE 4.33倍）を確認
- 全100銘柄（tanuki=true）を`pipeline.py --skip-risk`で再生成し、新規バナー
  文言がSITM・LITE以外のreport.txtに一切出現しないことを確認
  （`grep -rl "FCF実力推定に注意（業績サイクル変動）"`で2件のみヒット）
- `report_consistency_check.py --fail-on-ng`: NG=0（既存WARN 56件は
  今回の変更と無関係な既知/新規WARNで、SITM側WARN-25はFY52WEEK-BS-NULL-
  SILENT-1 Phase A起因の既知未確認WARN）
- `pytest tests/ -v`: 377 passed / 2 known failures（MSFT/NVDA、
  [[TEST-STALE-IV-1]]、本タスクと無関係）

#### コミット
- `4966d3f31`: feat: FCF-CONVRATE② SITM・LITE限定のFCFサイクル変動可視化バナー実装
  （pipeline.py/stock.html/BACKLOG.md/BACKLOG_DONE.md）
- `e39e7c495`: data: TANUKI VALUATION 全100銘柄再生成（FCF-CONVRATE②検証・日次データ更新、
  risk_events意図しない上書きの復元含む）

---

### ✅ [FCF-ESTIMATE-SKIP-STABLE-1] estimate_fcf_from_eps()に生FCF安定時のスキップ条件を追加（2026-07-18完了）
**分類:** バグ修正 / TANUKI VALUATION / TRUST-SUMMARY-EPIC-1
**登録日:** 2026-07-18
**完了日:** 2026-07-18
**発見:** [[TRUST-SUMMARY-EPIC-1]]棚卸し確定後のFCF-CONVRATE②可視化設計の事前調査（FCF代用推定82銘柄の個別検証）

#### 背景
TANUKI VALUATION対象100銘柄中82銘柄が`calculator/adjustments.py::
estimate_fcf_from_eps()`によるEPSベースのFCF代用推定に依存していたが、
`estimate_fcf_from_eps()`のdocstring（導入時原文）に「EPSアナライザーの
annual.jsonが存在する場合に常時適用」とある通り、生FCF（`base_fcf`）が
`determine_fcf_base()`のCV方式で多年度安定と判定され、かつ
`analyze_fcf_outlier()`の外れ値検知でも異常なしと判定された銘柄まで、
判定条件なしに無条件で推定値へ置換されていることが判明した。

導入経緯の一次調査（`git log --follow`）により、この「無条件置換」は
意図的な設計判断ではなく、2026-04-19の導入コミット
（`745a68c556680a6b61a071954dc025c2e457ba21`・`00f3a15797c320499f500f443e497435e7e6f582`、
いずれも"Add files via upload"で説明文なし）時点で対象銘柄がわずか13銘柄
しかなく、その後100銘柄まで拡大する過程で前提が一度も再検証されないまま
持ち越されたものと判明した（BACKLOG.md/BACKLOG_DONE.mdの全履歴を検索したが
「生FCFが安定している銘柄は推定に置き換えない」という設計議論の形跡は
一度も見つからなかった）。

#### 事前調査結果
- 全105銘柄機械集計で該当24銘柄を特定（CV<0.3 AND `outlier_detected`==False）。
  0.2〜0.5の閾値感度シミュレーションでも該当数はほぼ安定（20〜25件）
- `fcf_conversion_config.json`の`_sector_rationale`に業種固有理由が明記済みの
  9銘柄（AVGO/CRM/CWAN/DDOG/DOCN/HEI/NOW/SNPS/TSLA）との重複はゼロ
  （全9銘柄が`outlier_detected=True`のため自動的に除外される）
- **実装直前に新規発見**: `ticker_overrides`（AI CapEx急増等の個別配慮、
  AMZN/CEG/GOOGL/META/MRVL/MSFTの6銘柄）のうちGOOGL・MSFTの2銘柄が
  該当24銘柄に含まれることが判明。両銘柄はCV/外れ値検知データ上は
  「安定・異常なし」だが、ticker_overrides自体がAI CapEx急増による
  実態FCF過大評価を補正する個別設定であり、CV/外れ値データにはまだ
  その影響が反映されていないため、Koichiさんに確認の上
  **ticker_overrides該当銘柄はスキップ条件の対象外とする方針を決定**
  （対象は24→22銘柄に縮小）
- 下流の全消費箇所（`_calc_dcf_reliability_policy_b()`・SELL判定・
  report.txt生成・stock.html）は既存の`applied=False`契約
  （`estimated_fcf=raw_fcf`へのフォールバック）で問題なく動作することを
  コード・実データ・既存テストケースで確認済み

#### 実装内容
- `calculator/adjustments.py::estimate_fcf_from_eps()`に`fcf_cv`・
  `outlier_detected`引数を追加。既存の5フォールバック条件
  （config存在／非excluded／EPSデータあり／年度あり／純利益プラス）の
  最後（調整済み純利益マイナス判定の直後）に、
  `ticker not in ticker_overrides and fcf_cv < 0.3 and not outlier_detected`
  のスキップ条件を新設。該当時は`applied=False`・`estimated_fcf=raw_fcf`・
  note欄に理由（例:「生FCF安定(CV=0.14<0.3)かつ外れ値未検出のため推定を
  適用せず生FCFを採用」）を明記
- `core_calculator.py`の呼び出し元に`fcf_cv=fcf_base_result.cv`・
  `outlier_detected=fcf_outlier_result.detected`を追加

#### 検証結果
- 影響22銘柄（ABBV/AMAT/BSY/CART/CAT/CDNS/CIX/CON/HON/JNJ/KLAC/LMT/MO/
  MSCI/PM/TASK/TDY/TER/V/VZ/WMT/WST）を`pipeline.py --skip-risk`で再生成。
  成功22/失敗0。全銘柄で`applied`がTrue→False、`estimated_fcf`が
  生FCF（`raw_fcf`と同値）に切り替わったことを確認
- GOOGL/MSFTは意図的に対象外のまま未再生成、ticker_override由来の
  conversion_rateが従来通り適用されていることを確認
- Classification（TANUKI SCORE）変化5銘柄: BSY(BUY→WATCH)・
  CIX(HOLD→BUY)・CON(GROWTH_PREMIUM→HOLD)・JNJ(GROWTH_PREMIUM→TRIM)・
  VZ(HOLD→BUY)。残り17銘柄はIV変化のみでClassification不変
- Policy A/B発火状況（DCF_Reliability=LOWのscore_comment）は22銘柄
  いずれも変化なし（元々`outlier_detected=False`かつ乖離率2.0倍未満の
  ため、変更前からPolicy A/Bは未発火だった）
- pytest: 377 passed（既知2件MSFT/NVDA・[[TEST-STALE-IV-1]]のみ、無関係）
- `report_consistency_check.py`: NG=0/WARN=56（新規WARN増加なし）
- report.txt表示: 既存の`applied=False`銘柄（BKNG等）と同一形式
  （`FCF_Base: $X M (Nyr平均)`・`DCF_Reliability: HIGH`）で表示されることを
  目視確認

#### 依存関係・関連エントリ
- **[[POLICY-AB-TREND-BLIND-1]]（未着手・優先度：低）との関係**: 同エントリは
  `outlier_detected=True`の上方乖離側（`latest_fcf>fcf_5yr_avg`）に高い
  false positive率があることを既に診断済み（70銘柄中50銘柄が該当）。
  本タスクのスキップ条件は`outlier_detected==False`を要求する保守的な
  設計であり、この既知のノイズを持つ`detected=True`側を意図的に対象外
  としている。**将来この条件を緩和する（`detected=True`側にも拡張する）
  場合は、POLICY-AB-TREND-BLIND-1の解消（上方乖離の健全ケース切り分け）が
  前提となる**
- **[[FCF-CONVRATE-DESIGN-LIMIT-1]]（完了）・[[TRUST-SUMMARY-EPIC-1]]
  （FCF-CONVRATE②）との関係**: 本タスクにより、機械的置換だった54銘柄
  （前回調査の類型(e)相当）のうち22銘柄が解消した。TRUST-SUMMARY-EPIC-1の
  可視化スコープは、残る構造的限界（真にボラティリティが大きい銘柄群
  ＝SITM/LITE/SPIR等のFCF-CONVRATE②）に絞られる。詳細は
  TRUST-SUMMARY-EPIC-1エントリの状況更新を参照

#### コミット
- `05924a0c0`: fix: estimate_fcf_from_eps()に生FCF安定時のスキップ条件を追加
  （calculator/adjustments.py・core_calculator.py・影響22銘柄データ）

---

### ✅ [TTM-STOCK-FIELDS-DEAD-1] ttm_calculator.pyのSTOCK_FIELDS/SHARES_FIELDS分類が構造的に本番未到達（対応方針a: デッドコード削除で完了）
**分類:** アーキテクチャ / SECデータ取得層 / QUALITY-GATES-EPIC-1（GATE2-PHASE3B-1関連）
**登録日:** 2026-07-17
**完了日:** 2026-07-18
**発見:** GATE2-PHASE3B-1②実装時の検証で発見

#### 内容
GATE2-PHASE3B-1②（規約C: フィールド分類の二重管理是正）の実装・検証過程で、
`ttm_calculator.py::STOCK_FIELDS`にCurrentAssets/CurrentLiabilitiesを追加しても
本番の`{ticker}_ttm_series.json`（update.pyが実際に呼ぶ`calc_ttm_series()`の
出力）には一切反映されないことが判明した。追加調査の結果、これは
CurrentAssets/CurrentLiabilities固有の問題ではなく、STOCK_FIELDS/
SHARES_FIELDS分類全体が構造的に本番未到達という、より広い構造的問題と
判明した。

**根本原因**: `calc_ttm()`/`save_ttm()`（`{ticker}_ttm.json`生成、STOCK_FIELDS/
SHARES_FIELDSを実際に処理する唯一の関数）は、2026-05-07の`c3880e737`
（"switch FCF/RICE source to rolling TTM series"）で`calc_ttm_series()`が
追加されて以降、用途を失った。2026-05-11に一瞬（2分間）update.pyから
誤って呼ばれた形跡があるが、それ以降は本番から一切呼ばれていない
到達不能コードだった。

**8メンバーの内訳**（全て`calc_ttm_series()`＝本番経路を経由しない）:
- 完全にデッド（他経路の消費者もゼロ）: Cash・STDebt・DeferredRevenue・
  Equity・Assets（5件）
- 別実装で個別生存（ttm_calculator.pyの分類・calc_ttm_series()を経由せず、
  reader.py・audit.py・quarterly_review_generator.py・tail_dcf_bridge.py・
  pipeline.pyがそれぞれ独立にnormalized JSONを直接読む）: LTDebt・
  SharesBasic・SharesDiluted（3件）

#### 対応方針(a)の実装（2026-07-18完了）

**実装前の再確認**: `calc_ttm()`/`save_ttm()`への呼び出し箇所を全リポジトリで
再grepし、本番コードからの呼び出しが引き続きゼロであることを再確認した
（テストコードからの直接呼び出しのみ存在: `tests/test_ttm_calculator.py`・
`tests/test_pipeline_logic.py`）。8メンバーの完全デッド5件/個別生存3件の
切り分けもBACKLOG記載と現状で変わっていないことを確認した。

**削除内容:**
- `calc_ttm()`/`save_ttm()`本体を削除
- `calc_ttm()`からのみ呼ばれていた補助関数`_make_q4_implied_output()`・
  `_latest_end()`・`_calc_burn_rate()`も連動して削除（`calc_ttm_series()`は
  これらを使わない）
- 調査中に新たに発見した完全に呼び出し元ゼロの孤立関数`_calc_q4_implied()`
  （`_build_q4_quarterly_entries()`の重複排除機能を持たない旧版と推測される、
  `calc_ttm()`からも呼ばれていなかった）も削除
- `_build_q4_quarterly_entries()`は`calc_ttm_series()`（本番経路）が使用する
  ため削除せず維持
- STOCK_FIELDS/SHARES_FIELDS定数自体は**削除せず維持**（判断理由: モジュール
  ロード時の契約チェック`validate_field_classification(FIELD_CONCEPTS,
  FLOW_FIELDS, STOCK_FIELDS, SHARES_FIELDS, EXCLUDED_FIELDS)`が、
  `quarterly.py::FIELD_CONCEPTS`の全キーがFLOW/STOCK/SHARES/EXCLUDEDの
  いずれかに分類されることをimport時に保証する安全網として機能しており、
  これを維持したまま8メンバーを削除するとEXCLUDED_FIELDSへ統合するしかなく
  「意図的除外」の意味が変質してしまうため。両定数に「実際の値処理経路は
  もう存在せず、契約チェックのためだけに残置している」ことを明記するコメントを
  追記した）
- テストコード: `tests/test_ttm_calculator.py`の`calc_ttm`import・
  `test_calc_ttm_outputs_current_assets_and_liabilities_as_latest_quarter_value`
  （calc_ttm()を直接呼ぶテスト）を削除。STOCK_FIELDSメンバーシップ検証の
  2テストは分類定義自体が残るため維持。`tests/test_pipeline_logic.py`の
  `TestTTMNullValGuard`（calc_ttm()のNone値ガードをテスト、2テスト）を削除
  （同等のNone値ガードは本番経路`calc_ttm_series()`向けに
  `TestCalcTtmSeriesNullValGuard`ですでに別途カバー済みのため、テスト
  カバレッジの実質的な喪失はない）
- 孤立データファイル`common/sec_data/ttm/NVDA_ttm.json`（2026-05-11の
  2分間の誤呼び出しで生成された唯一の残存ファイル、以後どこからも
  参照されない）を削除

**検証結果:**
- pytest: 377 passed（既知2件除く、削除した3テスト分を除き変更前と同一。
  380→377は意図した3テスト削除分）
- report_consistency_check.py: NG=0/WARN=56（変更前と同一）
- `calc_ttm_series()`を既存の`normalized`入力データで再計算し、AAPL/MSFT/
  NVDA/RCAT/WMTの5銘柄で既存の`{ticker}_ttm_series.json`と値レベルで
  完全一致することを確認（本番出力への影響ゼロを実証）
- `update.py WMT`を実際に実行しimport error等が発生しないことを確認
  （実行に伴うWMTデータの再生成は診断目的のみのため、値が実質的に
  同一〈生成時刻とfrozenset由来のキー順序のみの差〉であることを確認した
  上で復元し、意図しない本番データ変更として残さなかった）

---

### ✅ [GATE2-PHASE3B-1] Gate2 Phase 3b: 独立実装4ファイルのreader.py統合・規約C/Dの型化（全項目完了）
**分類:** アーキテクチャ / SECデータ取得層 / QUALITY-GATES-EPIC-1関連
**登録日:** 2026-07-13
**完了日:** 2026-07-18（①4ファイル統合・②規約C・③-a規約D〈verdict〉は2026-07-17、
③-b規約D〈Classification〉は2026-07-18完了。全4項目完了につきBACKLOG.mdから
本ファイルへ全文移動）
**発見:** Gate2設計材料収集調査（①〜④）・Phase 3a実装時

#### 背景
Gate2設計材料収集調査で、以下2点がPhase 3a（正規化契約の型導入・完了）の
スコープ外として意図的に見送られた。

**① 独立実装4ファイルのreader.py統合**: `financial_trend_calculator.py`
（STONKS SILO）・`quarterly_review_generator.py`（TAIL）・`tail_dcf_bridge.py`
（TAIL）・`hypecore.py`が、共有アクセサ（reader.py/TTMReader）を経由せず
「is_annual=False かつ is_ytd=False の最新エントリを取る」ロジックをそれぞれ
独立に再実装していた（`_latest_q()`・`_lq()`等、名前も実装も微妙に異なる）。
型を導入しても、この4ファイルが辞書アクセス前提のままでは規約C/Dの効果が
及ばない。

**② 規約C（フィールド分類の二重管理）**: `ttm_calculator.py`の
`FLOW_FIELDS`/`STOCK_FIELDS`/`SHARES_FIELDS`が`quarterly.py::FIELD_CONCEPTS`とは
別ファイルで独立管理されており、新フィールド追加時にいずれかへの追加を
忘れてもエラーにならず黙って出力から消える。実例として`CurrentAssets`/
`CurrentLiabilities`（quarterly.pyでは「シガーバット検出用」とコメントされて
いる）が、現在これを消費するコードが皆無であることを確認済み（抽出されて
いるがTTM層で分類漏れのまま出力対象外になっている状態）。

**③ 規約D（enum風文字列の型化）**: `growth_sanity.py`の`verdict`
（PLAUSIBLE/REVIEW/AGGRESSIVE/FLOOR_HIT_REVIEW）・`pipeline.py`の`Classification`
（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）はいずれも生文字列の代入
（例: `verdict = "PLAUSIBLE"`）。タイプミスがあっても実行時エラーにならず、
静かに「未知の分類」として扱われる。

#### ②規約C完了（2026-07-17）

`ttm_calculator.py::STOCK_FIELDS`に`CurrentAssets`/`CurrentLiabilities`を追加し、
`_COGS`/`RPO`用の`EXCLUDED_FIELDS`を新設。`contracts.py::validate_field_classification()`
を新設し、`quarterly.py::FIELD_CONCEPTS`の全キーがFLOW/STOCK/SHARES/EXCLUDEDの
いずれかに属することをモジュールロード時に検証する契約チェックを追加した
（新フィールド追加時の分類漏れをimport時点で即座に検知）。

**循環import対応**: `contracts.py`は既に`quarterly.py`からimportされているため、
`contracts.py`側が`quarterly.py`/`ttm_calculator.py`を逆にimportすると循環import
になることを確認。汎用チェック関数`validate_field_classification()`は
`contracts.py`に置きつつ、具体的なフィールド集合（`FIELD_CONCEPTS`・
`FLOW_FIELDS`等）の受け渡しは呼び出し元（`ttm_calculator.py`）が担う設計
にして回避した（`contracts.py`はどちらもimportしない）。

**既存テストへの副次修正**: `ttm_calculator.py`がモジュールとして
`quarterly.py`/`contracts.py`をimportするようになった結果、パッケージ構造を
経由しない「ファイルパス直接ロード」（`tests/test_ttm_calculator.py`の
`sys.path.insert`方式・`tests/test_pipeline_logic.py`の
`importlib.util.spec_from_file_location`方式）が相対importエラーで壊れることが
判明し、他8ファイルと同じ`from common.sec_data.xxx import ...`のパッケージ
形式に統一して解消した。

**検証結果の読み替え（重要）**: 実装過程の検証で、①のSTOCK_FIELDS追加が
本番の`_ttm_series.json`（update.pyが実際に呼ぶ`calc_ttm_series()`の出力）
には一切反映されないことが判明した。追加調査の結果、これは
CurrentAssets/CurrentLiabilities固有の問題ではなく、**STOCK_FIELDS/
SHARES_FIELDS分類全体が構造的に本番未到達**（8メンバー中5件は完全に
デッド、残り3件は分類を経由しない別実装で個別に生存）という、より広い
構造的問題であり、根本原因は`calc_ttm()`（2026-05-07〜05-11の
`calc_ttm_series()`移行期の廃止漏れコード、本番からは到達不能）と判明した。
この構造的問題は②のスコープでは解消せず、[[TTM-STOCK-FIELDS-DEAD-1]]として
新規分離登録した（詳細は同エントリ参照）。

②の検証手順は「本番の`_ttm_series.json`への反映」ではなく「`ttm_calculator.py`
内の分類（STOCK_FIELDS）に正しく追加され、契約チェックがFIELD_CONCEPTS
全キーの分類網羅性を検証できる状態になったこと」に読み替えて完了とした
（全105銘柄でのデータ再生成は本番出力に変化がないため実施していない）。

**検証結果:**
- pytest 345 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く。新規17件
  〈`tests/test_contracts.py`5件・`tests/test_ttm_calculator.py`3件、他は
  既存テストの相対import修正〉を含む）
- report_consistency_check.py: NG=0/WARN=51（本セッションでは本番データ・
  latest.json/report.txtへの変更を一切行っていないため、ステージ3完了時点
  から不変）

#### ③-a規約D完了（2026-07-17・verdictのEnum化）

`common/sec_data/contracts.py`に`GrowthVerdict(str, Enum)`
（PLAUSIBLE/REVIEW/AGGRESSIVE/FLOOR_HIT_REVIEW）を新設し、
`growth_sanity.py::check_growth_sanity()`の`verdict`代入6箇所
（デフォルト値・4箇所の代入・戻り値dict格納）を生文字列から
`GrowthVerdict.XXX`（Enumメンバー参照）に置き換えた。

**実装時に発覚した罠（重要）**: Python 3.11以降、`Enum`の`__str__`/
`__format__`は「`str, Enum`を継承していても」デフォルトで
`GrowthVerdict.PLAUSIBLE`というクラス名付き表記を返す仕様に変わっている
（3.10以前は素の文字列を返していたが3.11で仕様変更）。そのため
f-string補間（`f"{verdict}"`）やstr()は、`__str__`をオーバーライドしない
限り事前の想定（str継承なので.value不要で動作する）通りには動かない
ことが実装検証で判明した（`==`比較・JSON出力〈json.dump〉はstr継承のため
元々問題なし）。`GrowthVerdict`に`__str__`をoverrideして`self.value`を
返すようにし、f-string補間を含めた全ての既存コード（`growth_sanity.py`の
戻り値dict格納・`pipeline.py`のreport.txt生成`f"判定 : {gs_verdict}"`）が
`.value`付与なしに意図通り動作するようにした（`enum.StrEnum`は
Python 3.11+限定でpyproject.tomlの`requires-python=">=3.10"`と整合しない
ため不採用、`__str__`override方式で3.10以降のどのバージョンでも同じ
挙動になるようにした）。

**検証結果:**
- pytest 351 passed（既知2件除く、新規6件〈`tests/test_contracts.py`の
  `TestGrowthVerdict`〉を含む。既存の`tests/test_pipeline_logic.py`の
  verdict `==`比較テスト2件は無改修でpass）
- report_consistency_check.py: NG=0/WARN=51（不変）
- 実データでの目視確認: growth_sanity判定がREVIEW（ABBV）・
  AGGRESSIVE（CWAN）・FLOOR_HIT_REVIEW（MO）の3銘柄でpipeline.pyを
  再実行し、report.txtの「判定」行・latest.jsonの`verdict`フィールドが
  Enum化前後で完全に同一（`GrowthVerdict.XXX`ではなく素の文字列のまま）
  であることを確認。stock.htmlはJSON経由で文字列を受け取るのみのため
  無改修で動作（latest.jsonの値が不変のため表示も不変と判断）。
  検証用に再生成した3銘柄のデータは本番反映せず元に戻した
  （市場データの日次変動のみが差分となり、verdict関連の差分はゼロだったため）

#### ①4ファイル統合完了（2026-07-17）

`common/sec_data/reader.py`にモジュールレベルの汎用アクセサ
`get_quarterly_series(normalized, field_name)`（is_annual・is_ytd両方を
除外した四半期エントリをend日昇順で返す）と`get_latest_quarterly(normalized,
field_name)`（その最新1件、空ならNone）を新設。戻り値は素の辞書のまま
（dataclass化は今回スコープ外・見送り）。

`get_rpo_context()`内の既存`_q_sorted()`（is_annualのみ除外・is_ytdは
除外していなかった）を`get_quarterly_series()`呼び出しに置き換え。
これは意図した挙動変化（is_ytdエントリの除外を追加）だが、現在のRPO関連
データにはis_ytd=Trueの実データがほとんど存在しないため無害であることを
実データ5銘柄（CRM/NOW/GTLB/RPD/DDOG）でのネットワーク未使用の新旧比較で
確認した（差分0件）。

4ファイルそれぞれの独自実装を新規アクセサに置き換えた:
- **quarterly_review_generator.py**: `_latest_q()`を削除しget_latest_quarterlyに、
  インライン重複2箇所（rev_qs・oi_map）をget_quarterly_seriesに置き換え
- **tail_dcf_bridge.py**: `_lq()`を削除しget_latest_quarterlyに置き換え
  （quarterly_review_generator.pyとのコピペ重複を解消）
- **financial_trend_calculator.py**: `_get_quarterly_entries()`の内部実装を
  get_quarterly_series呼び出し＋既存の`_build_q4_implied()`（このファイル
  固有のQ4逆算ロジックのためreader.py側へは移動せずローカルに残置）の
  組み合わせに変更。呼び出し箇所2箇所は関数シグネチャ不変のため無改修
- **hypecore.py**: `extract()`の内部実装をget_quarterly_series呼び出し結果
  をpandas Seriesに変換する形に変更（pandas変換ロジックはhypecore.py側に
  残置、reader.py側にpandas依存を持ち込まない設計を維持）。呼び出し箇所
  3箇所は関数シグネチャ不変のため無改修

**検証結果:**
- `tests/test_gate2_phase3b1_reader_integration.py`新設（14件）:
  get_quarterly_series/get_latest_quarterlyの単体テスト（is_annual・
  is_ytd除外、空リスト時のNone返却、end日ソート順）、get_rpo_context移行後
  の挙動確認、4ファイルそれぞれの移行前後の回帰テスト（is_ytd除外・
  Q4 implied構築・最新四半期選択が合成フィクスチャで期待通りに動作する
  ことを確認）
- pytest 387 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く。新規14件を含む）
- report_consistency_check.py: NG=0/WARN=51（本タスクでは本番データへの
  変更を一切行っていないため③-a完了時点から不変）
- ネットワーク未使用の新旧比較（実データ）: get_rpo_context（5銘柄）・
  financial_trend_calculator.\_get_quarterly_entries（3銘柄×5フィールド、
  Revenue/GrossProfit/OperatingIncome/NetIncome/OCFの全時系列）・
  tail_dcf_bridge.\_load_layer1_financials（3銘柄）・
  quarterly_review_generator.load_layer1_financials（3銘柄）・
  hypecore.fetch_quarterly_fundamentals（3銘柄、DataFrame全体を
  `.equals()`で比較、YoY/QoQ/TTM rollingを含む時系列全体が対象）で
  移行前後の出力が完全一致することを確認。検証用に生成した一時ファイルは
  すべて削除済み（本番データへの反映なし）

#### ③-b規約D完了（2026-07-18・Classificationの型化）

`common/sec_data/contracts.py`に`Classification(str, Enum)`
（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）を、③-aの`GrowthVerdict`と
全く同じパターン（`__str__`override必須）で新設し、`pipeline.py::classify()`の
`score`代入・比較18箇所（`classify()`内の代入8箇所・比較3箇所・
`_generate_score_comment()`内の比較1箇所、計464-544行目付近の12箇所＋
`_calc_dcf_reliability_policy_b()`との等価比較で使う`"LOW"`は別ドメインのため
対象外）を生文字列から`Classification.XXX`（Enumメンバー参照）に置き換えた。
695/756/995/1221行目（`latest.json`/`score_history.json`永続化・
`_generate_report()`でのデフォルト値取得・report.txt生成のf-string補間）は
事前調査で無改修と判断した通り無改修で完了（995行目の`"N/A"`デフォルトは
7メンバーいずれにも該当しない特別値のため、意図的にEnum化対象から除外）。

**事前調査で発見した最重要リスクの解消**: `report_consistency_check.py`の
NG-3（LOW丸め未発動、380-381行目）はreport.txtのテキストをregexで
再パースした文字列と比較するため、③-aで発覚した「Python 3.11+の
`str, Enum`は`__str__`をoverrideしないとf-string補間が
`Classification.WATCH`のようなクラス名付き表記になる」問題が再発すると
NG-3が全銘柄で誤発火するリスクがあった。`Classification`にも同様の
`__str__`overrideを適用し、`tests/test_report_consistency_check.py`に
`TestClassificationStrOverride`・`TestCheck3LowRoundingWithEnumClassification`
（NG-3が実際のEnum経由f-string出力で正しく発火/非発火することの回帰テスト、
および`__str__`override漏れ時の誤発火を意図的に再現して確認する対照テスト）
を新設し、事前調査で発見した「NG-3専用の回帰テストが存在しない」という
空白地帯を埋めた。

`json.dumps()`は`str`継承の`isinstance`高速パスにより`__str__`override前でも
素の文字列としてシリアライズされることを事前調査・実装検証の両方で確認済み
（f-string/`str()`のプロトコルとは別経路のため無関係）。この結果、
`latest.json`/`score_history.json`永続化・`daily_pick.py`
（`ELIGIBLE_CATEGORIES`/`CATEGORY_PRIORITY`）・フロントエンド8ファイル
（`docs/value-monitor/tanuki_score/index.html`の`CAT_META`/`CAT_COLOR`辞書等）は
いずれも無改修で動作することを確認した（`daily_pick.py`はEnum値を
`json.dumps`→`json.loads`で往復させた素の文字列でメンバーシップ判定・
辞書ルックアップが機能することを直接確認）。

**検証結果:**
- `tests/test_contracts.py::TestClassification`新設（8件）・
  `tests/test_report_consistency_check.py`に`TestClassificationStrOverride`
  （2件）・`TestCheck3LowRoundingWithEnumClassification`（5件）新設
- pytest 402 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く。新規15件を含む。
  既存の`tests/test_pipeline_logic.py`160件・`tests/test_report_consistency_check.py`
  既存分は無改修でpass）
- report_consistency_check.py: NG=0/WARN=51（NG-3が誤発火していないことを
  重点確認。不変）
- 実データ6銘柄（NVDA=BUY・SITM=WATCH・MSFT=HOLD・CON=TRIM→GROWTH_PREMIUM・
  JNJ=GROWTH_PREMIUM・RDW=PASS）でpipeline.pyを再実行し、Classification分類
  そのものに変化がないことを確認。**CON銘柄で`tanuki_score`が
  `TRIM`→`GROWTH_PREMIUM`に変化したが、フローズン入力（コミット済みの
  `latest.json`をそのまま`_calc_required_growth()`に再投入）での直接比較で
  `req_g=0.150001`（旧・price=$32.04時点）→`req_g=0.147917`
  （新・price=$31.755時点、`ttm_g=0.15`固定）と判明し、DCF-2の
  `GROWTH_PREMIUM`/`TRIM`分岐閾値（`req_g < ttm_g`）を約1%の株価変動のみで
  跨いだ既存ロジック自体の境界鋭敏性（Enum化とは無関係の挙動、CHAT_RULESの
  一時停止は不要と判断）と確認した。検証用に再生成した6銘柄のデータ・
  付随ファイル（history/hypecore_history/tickers.json）はすべて本番反映せず
  元に戻した

#### 残課題
- [[GATE2-PHASE3B-1]]は本エントリで①②③-a③-bすべて完了。関連の分離登録
  課題2件が引き続きオープン: [[TTM-STOCK-FIELDS-DEAD-1]]（②で発見、優先度未定）・
  `report_txt_parser.py`クリーンアップ候補・`history.json`レガシーエントリ矛盾
  （③-b事前調査で発見、BACKLOG.mdに優先度：低で新規登録）


---

## 2026-07-17（完了）

### ✅ [GATE2-PHASE3B-1] ①独立実装4ファイルのreader.py統合（2026-07-17完了）
**分類:** アーキテクチャ / SECデータ取得層 / QUALITY-GATES-EPIC-1関連
**登録日:** 2026-07-13
**完了日:** 2026-07-17（①のみ。③-b Classification型化は引き続き未着手。
②規約C・③-a規約D〈verdict〉は同日中に別途完了済み）
**発見:** Gate2設計材料収集調査・GATE2-PHASE3B-1事前調査（規模見積もり）

#### 背景
`financial_trend_calculator.py`（STONKS SILO）・`quarterly_review_generator.py`
（TAIL）・`tail_dcf_bridge.py`（TAIL）・`hypecore.py`が、共有アクセサ
（reader.py）を経由せず「is_annual=False かつ is_ytd=False の最新エントリを
取る」ロジックをそれぞれ独立に再実装していた（`_latest_q()`・`_lq()`等、
名前も実装も微妙に異なる。呼び出し箇所は計15箇所〈2+5+5+3〉）。
事前調査で、既存の`reader.py::get_rpo_context`内`_q_sorted`はis_ytdを
除外していない点で4ファイルの実装と異なる（現状データでは無害だが
将来リスクあり）ことも判明していた。

#### 対応内容
- `common/sec_data/reader.py`にモジュールレベル汎用アクセサ2つを新設:
  `get_quarterly_series(normalized, field_name)`（is_annual・is_ytd両方を
  除外した四半期エントリをend日昇順で返す）・`get_latest_quarterly(normalized,
  field_name)`（その最新1件、空ならNone）。戻り値は素の辞書のまま
  （dataclass化は今回スコープ外・見送り）
- `get_rpo_context()`内の既存`_q_sorted()`（is_annualのみ除外）を
  `get_quarterly_series()`呼び出しに置き換え（is_ytd除外を追加する意図的な
  挙動修正）
- 4ファイルの独自実装を削除し新規アクセサに置き換え:
  - `quarterly_review_generator.py`: `_latest_q()`削除＋インライン重複2箇所
    （rev_qs・oi_map）も置き換え
  - `tail_dcf_bridge.py`: `_lq()`削除（quarterly_review_generator.pyとの
    コピペ重複を解消）
  - `financial_trend_calculator.py`: `_get_quarterly_entries()`の内部実装を
    get_quarterly_series＋既存`_build_q4_implied()`（このファイル固有の
    Q4逆算ロジックのためreader.py側へは移動せずローカルに残置）の組み合わせに変更
  - `hypecore.py`: `extract()`の内部実装をget_quarterly_series呼び出し結果を
    pandas Seriesに変換する形に変更（pandas依存はhypecore.py側に残置）
  - いずれも呼び出し側の関数シグネチャは不変のため呼び出し箇所自体は無改修

#### 検証結果
- `tests/test_gate2_phase3b1_reader_integration.py`新設（14件）:
  get_quarterly_series/get_latest_quarterlyの単体テスト（is_annual・is_ytd
  除外・空リスト時None・end日ソート順）、get_rpo_context移行後の挙動確認、
  4ファイルそれぞれの移行前後の回帰テスト（合成フィクスチャでis_ytd除外・
  Q4 implied構築・最新四半期選択が期待通り動作することを確認）
- pytest 387 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く。新規14件を含む）
- report_consistency_check.py: NG=0/WARN=51（本タスクでは本番データへの
  変更を一切行っていないため③-a完了時点から不変）
- ネットワーク未使用の新旧比較（実データ、移行前後で完全一致を確認）:
  get_rpo_context（CRM/NOW/GTLB/RPD/DDOGの5銘柄）・
  financial_trend_calculator.\_get_quarterly_entries（CRM/NOW/DDOGの3銘柄×
  Revenue/GrossProfit/OperatingIncome/NetIncome/OCFの5フィールド、全時系列）・
  tail_dcf_bridge.\_load_layer1_financials（同3銘柄）・
  quarterly_review_generator.load_layer1_financials（同3銘柄）・
  hypecore.fetch_quarterly_fundamentals（同3銘柄、DataFrame全体を`.equals()`
  で比較、YoY/QoQ/TTM rolling等の時系列全体が対象）。検証用の一時ファイルは
  すべて削除済み（本番データへの反映なし）

#### 残課題
- [[GATE2-PHASE3B-1]]③-b（pipeline.py::Classificationの型化、pipeline.py内
  14箇所の分岐比較を含み③-aより影響範囲が大きい）は引き続き未着手


### ✅ [GATE2-PHASE3B-1] ③-a規約D: growth_sanity.py::verdictのEnum化（2026-07-17完了）
**分類:** アーキテクチャ / QUALITY-GATES-EPIC-1関連
**登録日:** 2026-07-13
**完了日:** 2026-07-17（③-aのみ。①4ファイル統合は同日中に別途完了済み。
③-b Classification型化は引き続き未着手）
**発見:** Gate2設計材料収集調査・GATE2-PHASE3B-1事前調査

#### 背景
`growth_sanity.py::check_growth_sanity()`の`verdict`（PLAUSIBLE/REVIEW/
AGGRESSIVE/FLOOR_HIT_REVIEW）が生文字列の代入・比較のみで、タイプミスが
あっても実行時エラーにならず静かに「未知の分類」として扱われる問題への対応。

#### 対応内容
- `common/sec_data/contracts.py`に`GrowthVerdict(str, Enum)`を新設
- `growth_sanity.py`のverdict代入6箇所（デフォルト値・4箇所の代入・
  戻り値dict格納）をEnumメンバー参照に置き換え

#### 実装時に発覚した罠（重要な技術的発見）
Python 3.11以降、`Enum`の`__str__`/`__format__`は`str, Enum`を継承していても
デフォルトで`GrowthVerdict.PLAUSIBLE`というクラス名付き表記を返す仕様に
変わっている（3.10以前は素の文字列を返していたが3.11で変更）。そのため
f-string補間・str()は`__str__`をオーバーライドしない限り、当初想定していた
「str継承だから.value不要でそのまま動く」が成立しないことが実装検証で判明した
（`==`比較・json.dumpは元々str継承のため無関係に正常動作）。`GrowthVerdict`に
`__str__`をoverrideして`self.value`を返すよう修正し、report.txt生成の
f-string補間（`f"判定 : {gs_verdict}"`）を含めた全既存コードが無改修で
動作するようにした。`enum.StrEnum`（Python 3.11+限定）は
`requires-python=">=3.10"`と不整合のため不採用とし、`__str__`override方式を
採用した。

#### 検証結果
- pytest 351 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く。新規6件
  〈`tests/test_contracts.py::TestGrowthVerdict`〉。既存の
  `tests/test_pipeline_logic.py`のverdict `==`比較テスト2件は無改修でpass）
- report_consistency_check.py: NG=0/WARN=51（不変）
- 実データ検証: growth_sanity判定がREVIEW（ABBV）・AGGRESSIVE（CWAN）・
  FLOOR_HIT_REVIEW（MO）の3銘柄でpipeline.pyを再実行し、report.txtの
  「判定」行・latest.jsonの`verdict`フィールドがEnum化前後で完全に
  同一であることを確認。stock.htmlはJSON経由で文字列を受け取るのみのため
  無改修で動作（検証用に再生成した3銘柄のデータは本番反映せず復元済み）

#### 残課題
- [[GATE2-PHASE3B-1]]③-b（pipeline.py::Classificationの型化、pipeline.py内
  14箇所の分岐比較を含み③-aより影響範囲が大きい）は引き続き未着手
  （①独立実装4ファイルのreader.py統合は同日2026-07-17に別途完了済み）


### ✅ [GATE2-PHASE3B-1] ②規約C: フィールド分類の二重管理是正（2026-07-17完了）
**分類:** アーキテクチャ / SECデータ取得層 / QUALITY-GATES-EPIC-1関連
**登録日:** 2026-07-13
**完了日:** 2026-07-17（②のみ。③規約D型化は引き続き未着手。①4ファイル統合は
同日中に別途完了済み）
**発見:** Gate2設計材料収集調査・Phase 3a実装時

#### 背景
`ttm_calculator.py`の`FLOW_FIELDS`/`STOCK_FIELDS`/`SHARES_FIELDS`が
`quarterly.py::FIELD_CONCEPTS`とは別ファイルで独立管理されており、
新フィールド追加時にいずれかへの追加を忘れてもエラーにならず黙って
出力から消える問題（実例: `CurrentAssets`/`CurrentLiabilities`が
抽出されているがTTM層で分類漏れのまま出力対象外になっていた）への対応。

#### 対応内容
- `ttm_calculator.py::STOCK_FIELDS`に`CurrentAssets`/`CurrentLiabilities`を追加
- `EXCLUDED_FIELDS = frozenset(["_COGS", "RPO"])`を新設（`_COGS`はGrossProfit
  逆算用の内部計算専用フィールド、`RPO`は`reader.py`が別経路で消費するため
  TTM層での分類が不要、という理由をコメント明記）
- `contracts.py::validate_field_classification()`を新設し、`FIELD_CONCEPTS`の
  全キーがFLOW/STOCK/SHARES/EXCLUDEDのいずれかに属することを
  `ttm_calculator.py`のモジュールロード時に検証する契約チェックを追加
  （新フィールド追加時の分類漏れをimport時点で即座に検知）
- **循環import対応**: `contracts.py`は既に`quarterly.py`からimportされている
  ため、逆方向の依存を追加すると循環importになることを確認。汎用チェック
  関数は`contracts.py`に置きつつ、具体的なフィールド集合の受け渡しは
  呼び出し元（`ttm_calculator.py`）が担う設計にして回避した
- テスト17件新設（`tests/test_contracts.py`5件・`tests/test_ttm_calculator.py`3件、
  他は既存2ファイル〈`tests/test_ttm_calculator.py`・`tests/test_pipeline_logic.py`〉の
  相対import修正）
- 既存テスト2ファイルの修正: `ttm_calculator.py`が`quarterly.py`/`contracts.py`を
  importするようになった結果、パッケージ構造を経由しない「ファイルパス
  直接ロード」（`sys.path.insert`方式・`importlib.util.spec_from_file_location`方式）
  が相対importエラーで壊れることが判明し、他8ファイルと同じパッケージ形式の
  importに統一して解消

#### 検証結果の読み替え（重要な発見）
実装過程の検証で、①のSTOCK_FIELDS追加が本番の`_ttm_series.json`
（`update.py`が実際に呼ぶ`calc_ttm_series()`の出力）には一切反映されない
ことが判明した。追加調査の結果、これはCurrentAssets/CurrentLiabilities
固有の問題ではなく、**STOCK_FIELDS/SHARES_FIELDS分類全体が構造的に
本番未到達**（8メンバー中5件は完全にデッド、残り3件は分類を経由しない
別実装で個別に生存）という、より広い構造的問題であり、根本原因は
`calc_ttm()`（2026-05-07の`c3880e737`で`calc_ttm_series()`が追加されて以降
用途を失い、2026-05-11の`38ae3f75a`→`210cdb01e`の2分間だけ誤って
update.pyから呼ばれた形跡はあるものの、それ以降は本番から一切呼ばれて
いない到達不能コード）と判明した。

この構造的問題は②のスコープでは解消せず、[[TTM-STOCK-FIELDS-DEAD-1]]と
して新規分離登録した。②の検証手順は「本番の`_ttm_series.json`への反映」
ではなく「`ttm_calculator.py`内の分類（STOCK_FIELDS）に正しく追加され、
契約チェックがFIELD_CONCEPTS全キーの分類網羅性を検証できる状態になった
こと」に読み替えて完了とした（全105銘柄でのデータ再生成は本番出力に
変化がないため実施していない）。

#### 検証結果
- pytest 345 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く）
- report_consistency_check.py: NG=0/WARN=51（本番データ・latest.json/
  report.txtへの変更は本タスクでは一切行っていないため不変）

#### 残課題
- [[GATE2-PHASE3B-1]]③（規約D: enum風文字列の型化）は引き続き未着手
  （①独立実装4ファイルのreader.py統合は同日2026-07-17に別途完了済み）
- [[TTM-STOCK-FIELDS-DEAD-1]]（本項目で発見・新規分離登録、優先度未定）


---

## 2026-07-15（完了）

### ✅ [FY52WEEK-BUCKET-MISPLACE-1] 52/53週会計年度企業の年次revenue値がdetermine_fiscal_year()の月判定により隣接年度バケツへ誤って混入する問題の根本修正（2026-07-15完了）
**分類:** アーキテクチャ / SECデータ正規化
**登録日:** 2026-07-15
**完了日:** 2026-07-15
**発見:** REVENUE-TAG-CONFLICT-SCAN-1（revenueタグ競合検知）の全銘柄実行時、
AVGO/DELL採用値が公表売上高と大きく乖離している疑いから調査

#### 問題（登録時点の内容）
AVGO・DELL・CAKE・ELF（52/53週会計年度企業。決算日が年によって
10月末〜11月初旬／1月末〜2月初旬等の範囲で微妙に変動）で、
`determine_fiscal_year()`の「月で判定」ロジックにより、真の年次値
（365日間の正規エントリ）が誤って隣接年度バケツに押し出され、
空いたバケツに90日間の四半期スタブがduration filterなしで
「年次データ」として無審査で採用される。1年限りの孤立事象ではなく、
決算日が月境界をまたぐたびに毎年系統的に発生する。

具体例：
- AVGO FY2019: 真の年次値$22,597M（3つの独立10-K申告で一貫）が
  end_year=2020バケツに誤登録され、end_year=2019バケツには90日間の
  四半期スタブ$5,515Mのみが残り採用される
- DELL FY2019: 真の年次値$90,621M（2つの独立10-K申告で一貫）が
  同様にend_year=2020バケツに押し出され、end_year=2019には
  90日間スタブ$22,482Mのみが残る

#### 調査過程で確定した根本原因（事前調査完了時点のまとめ）
1. **判定ロジックの欠陥**: `determine_fiscal_year()`
   （`common/sec_data/utils.py`）は`end_date.month > fiscal_end_month`の
   月比較のみで日を見ない設計。52/53週対応は皆無。12月決算企業では
   `month > 12`が常に偽となるため年またぎ補正が原理的に発生しない
   副次的欠陥もあり（CAKE/CDNS/JNJ/TDY等に影響）。
2. **対象銘柄の拡大確定（当初4銘柄→10銘柄）**: 全106銘柄スキャンにより
   DELL/JNJ/ADBE/CDNS/AVGO/CAKE/TDY/MRVL/LITE/IOTの10銘柄が対象と確定。
   ELF/MSCI/RCATはFYE一回限りの変更（移行期スタブ由来）で別種と判明し除外。
3. **tie-breakカスケード側の欠陥**: バケツ分類ロジックだけでなく
   `_extract_values_merged`/`_extract_single_key`の「同一exactness→
   end_date新しい方優先」規則にも複合欠陥があり、DELL FY2019等の
   真の値が完全消失するケースが判明。
4. **ARCH-DATA-1-FYコミット（2026-06-25, ab792d38b）による回帰と判明**:
   旧ロジック（`end_year = int(end_date[:4])`）から新ロジック
   （`determine_fiscal_year()`月比較）への切替が、mid-year四半期
   誤ラベル（INTU等）は修正した一方、52/53週バケツ誤配置を新たに
   持ち込んだ。IOT/AVGO/MRVLでは空いたバケツを埋める代替値が存在しない
   ため「化石ファイル」（`save_parsed_data()`に古い年度ファイルの
   削除ロジックがなく、旧ロジック下での最後の正しい状態が凍結される
   現象）として現れ、DELL/ADBE/LITEでは四半期スタブによる継続的な
   「誤配置」として現れる、という表面上の違いがあるのみで根本原因は同一。
5. **本人データ判定の設計**: SEC `submissions` API（`reportDate`）を
   突き合わせることで`reportDate == end_date`が「本人データ（比較年度の
   再掲ではない）」の100%信頼できる判定シグナルであることを、
   830件超の年次・859件の四半期エントリで例外ゼロで検証。

#### 対応内容（実装、2026-07-15）
上記調査結果に基づき、`determine_fiscal_year()`自体は変更せず、
SEC submissionsの`reportDate`による「本人データ」判定を新設して
既存のfallbackロジックの上に安全に上書きする方式で実装：
1. `common/sec_data/fetcher.py`: `SECFetcher.fetch_submissions()`/
   `load_submissions()`を新設。`data.sec.gov/submissions/CIK{cik}.json`
   （+ archives）から`{accn: reportDate}`を取得・キャッシュ。
   `update.py`にStep 1bとして非blocking組み込み。
2. `common/sec_data/parser.py`: `_collect_own_data_annual()`
   （form=10-K・fp=FY/Q4・duration 340-380日・`reportDate==end_date`の
   エントリのみを収集し、fyタグ衝突時はdetermine_fiscal_year()フォール
   バックが自然に分離できるかで解決方式を切替）と
   `_own_override_is_safe()`（対象キーの既存値が「月またぎ補正なしで
   到達した自己無矛盾な年次データ」の場合は上書きを拒否する安全弁）を
   新設し、`_extract_values_best_candidate()`内で全xbrl_keys横断で
   本人データをマージしてから安全確認付きで上書きする方式に統合。
   反復検証で5件の回帰（JNJ 2011の四半期スタブ誤採用、WMT/CRM/FCXの
   タグ優先度・衝突解決ロジック欠陥、IOT安全弁の過剰ブロック）を発見・修正。
3. `common/sec_data/report_consistency_check.py`: CHECK-22として
   fyタグ衝突ログ（`fy_collision_log.json`）を検知しWARN表示する
   仕組みを追加。
4. 全106銘柄のSEC生データ再取得・再パース、TANUKI VALUATION・
   EPS Analyzerの再生成を実施。

対象は当初の10銘柄に加え、全106銘柄スキャンで新規発見した
fyタグ衝突8銘柄（CRM/FCX/WMT等）も含めて解消。

#### 検証結果
- `pytest tests/`: 既知の2件（MSFT/NVDA、ALPHA-REDESIGN-1関連の
  別課題）を除き全件パス。
- `report_consistency_check.py --fail-on-ng`: NG=0。WARN-22
  （fyタグ衝突）が想定通り8銘柄でのみ発火。
- `dcf_validity_checker.py`: 対象18銘柄で新規の誤検知なし。
- TANUKI VALUATION: 44/44銘柄成功で再生成完了。
- EPS Analyzer: 43/43銘柄成功で再生成完了。
- git stashによるOLD/NEWパーサーのA/Bテストで、DELL 2019・JNJ 2011・
  IOT 2024/2025・CRM 2025/2026・FCX 2023/2024・WMT 2009/2013の
  全対象銘柄・年度で修正を個別に再確認済み。

#### 実装過程で新規発見しスコープ外として登録した既知の残課題
- `[[FY52WEEK-BS-INSTANT-FACT-1]]`: BS項目（instant fact、start日を
  持たないため340-380日duration filterの対象外）は本修正のカバー
  範囲外のまま。
- `[[FY52WEEK-BS-NULL-SILENT-1]]`: BS項目のNone値が`reader.py`等の
  `or 0`パターンにより無警告でゼロ扱いされる、既存の別課題。

#### 着手条件
なし（完了）

---

### ✅ [REPORT-ALPHA-STALE-1] report.txt（REPORT-6ブロック）がALPHA-REDESIGN-1廃止済みのalpha乗算式のまま表示されている問題の修正（2026-07-15完了）
**分類:** レポート表示 / データ品質
**登録日:** 2026-07-15
**完了日:** 2026-07-15
**発見:** [[ALPHA-CAP-HARDCODE-1]]影響範囲調査時の横展開確認

#### 背景（登録時点の内容）
`pipeline.py:1478-1510`（report.txt生成のREPORT-6ブロック）が、
`_v0_x_alpha_r6 = _v0_rm * (1 + _alpha_r6)` という廃止済み
（ALPHA-REDESIGN-1でalpha乗算廃止済み）のalpha乗算式を使って
`DCF_v0_x_alpha`・`Equity_Value`をreport.txtに表示している一方、
実際に表示される`Intrinsic_Value`は`valuation.get("intrinsic_value_per_share")`
（正しい値・alpha非乗算）をそのまま出力していたため、report.txt上で
「Equity_Value ÷ Shares_Used = Intrinsic_Value」という自己記載の式が
成立しない状態だった（ADBE実例: Equity_Value $458.58B ÷ Shares_Used
397.5M = $1153.65のはずがIntrinsic_Value表示は$639.89）。

#### 事前調査で追加発見した2箇所（実装着手前、読み取り専用調査で確認）
`pipeline.py`内の「Definition」固定テキストブロックにも同型の陳腐化を発見し、
本タスクのスコープに含めて対応した：
- `pipeline.py:1612`付近（`[3.TANUKI VALUATION]`セクション）:
  `"P_t = DCF_v0 × (1 + Alpha) + RPO_PV + Growth_Option_PV"`という
  alpha乗算前提の説明文
- `pipeline.py:1927`付近（`[7.HYPECORE]`セクション）:
  `"Alpha: Growth expectation premium added to IV"`という
  IVに加算される前提の説明文

なお横展開調査（scenarios.py・sensitivity.py・calculator/adjustments.py・
validator.py・stock.html）では、いずれも呼び出し元が`alpha=0.0`を
明示的に渡す設計のため実害なしと確認済み（`calculate_intrinsic_value()`
本体の汎用式自体は`v0*(1+alpha)+...`のままだが、全呼び出し元で
alpha固定のため問題化しない）。`validator.py`は`VALIDATOR-IVPS-MISMATCH-1`で
既に同種の修正が完了済みだったことも確認した。

#### 対応内容
`src/value/tanuki_valuation/pipeline.py`の3箇所を修正:
1. `DCF_v0_x_alpha`のtrace/append行を削除（alpha乗算後V0は実計算経路に
   存在しないため式チェーンから除外）
2. `_pt_r6`の算出を`_v0_x_alpha_r6`ではなく`_v0_rm`（既存のDCF_v0行と同一値）
   を使うよう変更。`Equity_Value`の表示文言も「= v0 + RPO_PV + GO_PV + ...」に
   修正し`v0_x_alpha`という語を除去
3. `[3.TANUKI VALUATION]`・`[7.HYPECORE]`の各Definitionブロックの説明文を
   alpha非乗算の実態（参考値表示のみ・計算には未使用）に即した文言へ修正
4. `Alpha_Premium`の表示行自体は変更せず維持（参考値表示として引き続き有効）

#### 検証結果
全100銘柄（tanuki=true・report.txt存在銘柄）を`pipeline.py --skip-risk`で
再生成し確認:
- 成功100/失敗0
- `report_consistency_check.py`: NG=0（WARN=36件、全て本タスクと無関係な
  既存の確認済み警告）
- `pytest tests/`: 309 passed / 2 failed（既存の[[TEST-STALE-IV-1]]、
  MSFT/NVDA、ALPHA-REDESIGN-1後にテスト式が未更新の既知バグ。本タスクの
  変更前後で件数・対象銘柄とも同一）
- ADBE手計算検証: Equity_Value $254.36B ÷ Shares_Used 397.5M = $639.90
  ≈ Intrinsic_Value表示$639.89（式が成立することを確認）。NVDA
  （$18763.83B ÷ 24221.0M = $774.69）でも同様に成立を確認
- 全report.txt・pipeline.pyから`DCF_v0_x_alpha`/`v0_x_alpha`の文字列が
  消滅したことをgrepで確認

#### コミット
- `581a93d28`: コード修正（`pipeline.py`）
- `59ae5b6c6`: 全100銘柄report.txt/latest.json/history.json/score_history.json再生成

### ✅ [ARCH-DATA-1] 残課題① 計算層への重複実装一本化（2026-07-15完了）
**分類:** アーキテクチャ / SECデータ正規化
**登録日:** 2026-07-15
**完了日:** 2026-07-15
**発見:** [[ARCH-DATA-1]]着手前棚卸し調査

#### 背景
ARCH-DATA-1着手前の棚卸しで、正規化層（`tag_definitions.py`等）への
集約は部分的に進行済みだが、計算層（`pipeline.py`・`reader.py`）への
重複実装が①暦年グルーピング（trailing 370日窓）②BS項目「同一時点原則」
の2件残存していることを確認した。

#### 対応内容
- ①`common/sec_data/utils.py::quarters_in_trailing_window()`に窓計算
  部分を共有化し、`quarterly.py::check_revenue_quality()`・
  `pipeline.py`（DILUTION-FYE-1）双方から参照する形に統一。窓の中身の
  使い方（4件のみ合計 vs 何件でも中央値）は目的が異なるため各呼び出し
  元に残置
- ②`reader.py::get_net_cash()`を正としてBS項目取得ロジックを一本化。
  単なるコード重複ではなくreader.py側だけがInsurance/Fintechセクター
  ガードを適用しており、V（Visa）で実際に約$1.56Bの表示乖離
  （report.txt・TANUKI SCORE判定に使う値がDCF計算に使う値とズレていた）
  が発生していたことを実データで確認・是正した。`BSAdjustmentResult`に
  `net_debt_period`を追加し、`pipeline.py`は`valuation["bs_adjustment"]`
  を再利用する形に変更（二重のファイル読み込み自体を解消）

#### 検証結果
- 副次的にSOUN（LTDebt=0のFY2024 10-K値が旧pipeline.py独自フィルタで
  誤除外されていたバグ）も是正された。いずれもIntrinsic_Value自体・
  TANUKI SCORE分類には影響なし
- 全100銘柄再生成: 成功100/失敗0、`report_consistency_check.py` NG=0、
  pytest 309 passed / 2 known failed（MSFT/NVDA、TEST-STALE-IV-1既知
  バグ、無関係）
- 意味のある差分はV・SOUNの2銘柄のみ（他98銘柄は`financial_health`/
  `bs_adjustment`/`intrinsic_value_per_share`等の主要フィールドに変化なし）

#### コミット
- `4e4629a3b`: コード修正（`utils.py`/`quarterly.py`/`reader.py`/
  `adjustments.py`/`pipeline.py`）
- `60d44b2d8`: 全100銘柄report.txt/latest.json/history.json再生成

残課題②（EPS Analyzer経路のスコープ判断）は[[EPS-ANALYZER-NORMALIZE-SCOPE-1]]
として分離登録。残課題③は下記参照。

### ✅ [ARCH-DATA-1] 残課題③ revenue系タグ競合検知の実装（2026-07-15完了・スコープ縮小）
**分類:** アーキテクチャ / SECデータ正規化
**登録日:** 2026-07-15
**完了日:** 2026-07-15
**発見:** [[ARCH-DATA-1]]残課題①完了後の着手前調査

#### 背景
当初想定していた「PREFLIGHT-CHECK-1と共有する汎用パターン判定カタログ」
構想を着手前調査した結果、①`_extract_values_merged()`に候補タグ比較・
競合検知の仕組みが一切なく、既存の「検知トリガー」もSEC-REV-FINTECH-1/
BUG-REV-SPAC-1型については人間が一次情報で正誤判断した一回限りの手動
オーバーライドにすぎなかった、②PREFLIGHT-CHECK-1が想定する新規登録
時点の情報だけでは大半が「リスクフラグ立て」止まりで精度未検証、と
判明したため、汎用カタログ構想は見送り、revenue系タグ競合の実データ
検知に最小スコープを絞って実装した。

#### 対応内容
- `common/sec_data/revenue_tag_conflict_check.py`新設。`parser.py`本体は
  無変更、`SECParser`の既存メソッド（`_detect_fiscal_end_month`/
  `_extract_single_key`/`_extract_values_merged`）を再利用し候補タグ
  一覧・年度判定ロジックを重複させない設計
- `update.py`のStep1完了直後（`check_revenue_quality()`の直後、4c.相当）
  に配線。新規のStep番号追加は不要だった
- 自動修正は一切行わず、WARN出力（候補タグ名・各値・採用値の明示）のみ

#### 検証結果
- SOFI（$619.4M vs $3,613.4M、乖離5.8倍）・IONQ（$1,235.0M vs $11.1M、
  乖離111.0倍）の既知ケースを正しく再現することを確認
- 全100銘柄実行の結果、revenue系で14銘柄を検知。詳細・判定結果の内訳は
  [[REVENUE-TAG-CONFLICT-SCAN-1]]参照（LITE・TERは実害なし、PMは正当な
  業種差と判定済み。AVGO/DELL/CAKE/ELF＋RCATは[[FY52WEEK-BUCKET-MISPLACE-1]]、
  TDY/ASTSは[[REVENUE-TAG-PRIORITY-FRAGILE-1]]へ分離登録）
- pytest 309 passed / 2 known failed（既知のみ、無関係）。既存の
  `check_revenue_quality()`の出力・挙動には影響なし（並行動作の独立
  チェックであり既存ロジックは無変更）

#### コミット
- `f05cae0ba`: コード修正（`revenue_tag_conflict_check.py`新設・
  `update.py`配線）。データ再生成は不要（report.txt/latest.jsonに影響
  しないコンソール診断のみのため）

#### 副次的な設計上の発見（重要）
`selling_and_marketing`・`depreciation_and_amortization`フィールドも
同時に検知対象としたが、候補タグ同士が親子/包含関係にあるため
（例: `DepreciationAndAmortization` ⊇ `AmortizationOfIntangibleAssets`）、
revenue系のような「本来同一概念であるべき候補の食い違い」ではなく
大半が構造的なfalse positiveと判明した（詳細は[[REVENUE-TAG-CONFLICT-SCAN-1]]参照）。

また、この調査の過程で未使用の`quality_checker.py`（独自のQ01〜Q13
チェックカタログを持つが全リポジトリからimportされていない死蔵コード）
を発見し、[[QUALITY-CHECKER-CLEANUP-1]]として新規登録した。

### ✅ [VALIDATOR-IVPS-MISMATCH-1] validator.pyのpt_shares_consistency不整合の根本修正（2026-07-15完了）
**分類:** DCF信頼性判定ロジック / データ品質
**登録日:** 2026-07-14
**完了日:** 2026-07-15
**発見:** [[FCF-CONVRATE-DESIGN-LIMIT-1]] Software_Systemグループ分割の
影響18銘柄再生成時、FRSHの`validation.overall`がFAILになったことへの
原因調査中に新規発見・登録（事前BACKLOG登録なし）

#### 背景（登録時点の内容）
`validator.py::run_basic_checks`の`pt_shares_consistency`チェックが
DCF構成要素から再計算する理論株価と、`latest.json`に最終保存される
`intrinsic_value_per_share`が一致しないケースを確認していた
（FRSH: 検証時$127.83 vs 最終保存$41.47、ADBE: 検証時$1153.85 vs
最終保存$639.89 等）。原因は未検証のまま「`pipeline.py`が
`calculate_pt()`を1銘柄につき複数回呼んでいる（pipeline.py:127/625/649）
ことによるスナップショットのズレではないか」という仮説のみを登録していた。

#### 影響範囲調査の結果（実装前調査、2026-07-15）
tanuki=true 100銘柄で検証時再計算IVと最終保存`intrinsic_value_per_share`を
突き合わせたところ、100銘柄中88銘柄で乖離1%以上、うち64銘柄が
`pt_shares_consistency`のfail（diff_pct≥1.0）を通じて`overall`を
WARN/FAILに引き上げていた（残り2銘柄=FRSH/LYFTは`anomaly_detection`
経由でFAIL）。

#### 根本原因（2件、独立して併発）
1. **主因（仮説にはなかった、影響がより大きい原因）**: `core_calculator.py:541-545`
   等（ALPHA-REDESIGN-1）で`intrinsic_value_per_share`の実計算は
   `calculate_intrinsic_value(v0, rpo_pv, alpha=0.0, growth_option_pv)`と
   常にalpha非乗算になっていた（alphaは参考値として`data["alpha"]`に
   保持されるのみ）。ところが`validator.py`の`run_basic_checks`
   （272行目付近）と`build_validation_prompt`（93-94行目）は
   `p_t = total_v0 * (1 + alpha)`という廃止済みの式のまま再計算しており、
   alpha>0の銘柄ほぼ全てで検証時再計算IVが実際の`intrinsic_value_per_share`
   より`(1+alpha)`倍に近い比率で過大に出ていた（ADBEで実証: alpha=0.8、
   alpha乗算ありの式で$1153.85、実際の式（alpha非乗算）で$639.89、
   最終保存値と完全一致を確認）。auto_adjusted=False（下記②の対象外）の
   銘柄でも29銘柄が乖離1%以上あり、これが②とは独立したバグであることを
   確認した。
2. **副因（登録時点の仮説どおり）**: `pipeline.py:622-640`（`_save_result`内）で
   `segment_configured=False`かつ`recommended_g`再計算が発火する60銘柄
   （`phase1_growth_auto_adjusted=True`）で、`calculate_pt(tapering_g_end=...)`
   （line 625）により`valuation`全体を新スナップショットに差し替える際、
   旧スナップショット（pipeline.py:127由来）に対する`validate_calculation()`
   の結果（`_orig_validation`）をそのまま新スナップショットに貼り付けて
   いた。`validate_calculation()`は新スナップショットに対して再実行
   されないため、`validation`一式（4チェックとも）が最終保存データと
   対応しないスナップショットを検証した結果のまま残っていた。
   3回目の呼び出し（bear評価、line 649）は`scenario_valuations.bear`
   のみを更新するため本問題とは無関係と確認済み。

#### 対応内容
① `src/value/tanuki_valuation/validator.py`:
   - `run_basic_checks`の`pt_shares_consistency`（P_t算出式からalpha乗算を除去、
     `total_v0`をそのまま使用。alphaはdetail文言に参考値として残す）
   - `build_validation_prompt`（AI検証プロンプト、現状`XAI_API_KEY`未設定時は
     未使用だが同一の廃止済み式を含んでいたため同様に修正。算式説明文も
     ALPHA-REDESIGN-1後の実装に合わせて更新）
② `src/value/tanuki_valuation/pipeline.py`（`_save_result`内）:
   - `valuation`を`_valuation_adj`（新スナップショット）に差し替える際、
     旧スナップショットの検証結果を使い回さず、`validate_calculation()`を
     `_valuation_adj`に対して再実行し、その結果を`valuation["validation"]`に
     設定するよう変更。再実行が例外発生した場合のみ旧検証結果へフォール
     バックしログに警告を出す。

#### 検証結果
全100銘柄（tanuki=true）を`pipeline.py --skip-risk`で再生成し新旧比較:
- `pt_shares_consistency` pass件数: 36/100 → **100/100**（全銘柄で差異0.00%に統一）
- `dcf_components` も同時に全銘柄passへ改善（同じスナップショット差し替え問題の対象だったため）
- `validation.overall`分布: PASS 34→**69** / WARN 64→**30** / FAIL 2→**1**
- スポットライト銘柄（依頼書指定）:
  - ADBE: pt_shares_consistency False→**True**（乖離80.32%→0.00%）。
    overallは依然WARN——ただし原因は`formula_verification`
    （後述の別バグ、本タスクのスコープ外）に切り替わっており、
    pt_shares_consistency起因ではなくなったことを確認
  - FRSH: overall **FAIL→PASS**（`anomaly_detection`の乖離率判定も含め
    全4チェックがPASS）
  - LYFT: overall FAIL維持（正当な理由=FCF恒久マイナスによる
    `anomaly_detection`）だが、detail文言の理論株価が旧スナップショットの
    $-4.42から実際の最終保存値$-0.98に修正され、表示内容が最終保存データと
    整合するようになった
  - DELL: pt_shares_consistency False→**True**（乖離1362.87%→0.00%）、overall WARN→**PASS**
  - GEV: pt_shares_consistency False→**True**（乖離474.05%→0.00%）、overall WARNのまま
    （formula_verificationへ原因変化、後述）
  - CWAN: pt_shares_consistency False→**True**（乖離451.54%→0.00%）、overall WARN→**PASS**
  - ENTG: pt_shares_consistency False→**True**（乖離803.31%→0.00%）、overall WARN→**PASS**
- `report_consistency_check.py`: NG=0（WARN=36件、全て本タスクと無関係な既存の
  警告——Revenue段差型急変・PS異常値・growth_floor張り付き等）
- `pytest tests/`: 309 passed / 2 failed（既存の[[TEST-STALE-IV-1]]、
  MSFT/NVDA、ALPHA-REDESIGN-1後にテスト式が未更新の既知バグ。本タスクの
  変更ファイル（validator.py/pipeline.py）とは無関係で、変更前後で
  件数・対象銘柄とも同一）

#### 範囲外として報告のみ・未実装（次セッション以降の判断材料）
本タスク実施中に以下2件を新規発見したが、依頼スコープ外のためその場では
未実装（BACKLOGへの新規登録は次回セッションで判断）:

1. **`formula_verification`のalpha_cap不整合**: `validator.py::_extract_params`
   が`alpha_cap = 1.0`を全銘柄一律ハードコードしているが、
   `core_calculator.py`は業種別（`_industry_alpha_caps`）・セクター別
   （`_alpha_caps`）・メガテック（`_mega_tech_tickers`）に応じて
   0.8等の動的なalpha capを適用している（[[industry_alpha_caps 方針]]
   参照）。このため実際にキャップされたalpha値と、validatorが
   `alpha_cap=1.0`を前提に再計算した理論alpha値が一致せず、
   `formula_verification`が誤ってFAILする。本タスクの再生成後、
   overall=WARNの30銘柄は全てこれが原因（残るFAIL 1件=LYFTは
   `anomaly_detection`起因で正当）。ADBEで実証確認済み
   （HEAD時点から`formula_verification: False`は変化なし＝本タスクの
   変更由来ではなく既存バグ）。
2. **`tests/test_iv_formula.py`（[[TEST-STALE-IV-1]]）が今回修正した
   validator.pyと全く同じ廃止済み式（`v0_rm * (1.0 + alpha)`）を
   使用している**ことを確認した。CLAUDE_CODE_START.mdに既知の失敗として
   記載済みのため今回は対象外としたが、根本原因は本タスクで特定した
   ALPHA-REDESIGN-1追随漏れと同一であり、validator.py同様の修正
   （alpha非乗算化）で解消できる可能性が高い。

---

## 2026-07-14（完了）

### ✅ [SECTOR-FCF-RATE-BROKEN-1] FCF実力推定のsector取得経路破損によるセクター別転換率の無効化（2026-07-14完了）
**分類:** バグ / TANUKI VALUATION / データ品質
**登録日:** 2026-07-11
**完了日:** 2026-07-14
**発見:** [[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）関連調査時

#### 背景・原因（登録時点）
`adjustments.py`（`estimate_fcf_from_eps`内）のFCF転換率セクター別レート判定・
Financial Services向け`ni_direct`判定が、以下3つの重なったバグにより
実質的に無効化されていた：
- **バグ①**: `core_calculator.py:227-233`の`beta_config.json`読み込みパスが誤り
  （存在しない`src/value/beta_config.json`を参照、実際は`config/beta_config.json`）
- **バグ②**: `config/beta_config.json`の`overrides`に`sector`キーがほぼ存在しない
  （全103エントリ中1件のみ）
- **バグ③**: `fcf_conversion_config.json`の`sector_conversion_rates`とbeta_config.json側の
  タクソノミーが一致しない（後の調査で「タクソノミー自体は同一系統〈Damodaran業種〉だが
  fcf_conversion_config.json側のカバレッジが8/114分類と極端に少ないだけ」と判明）

#### 対応内容
1. **バグ①修正**: `core_calculator.py:226-235`の独自実装（パス誤り）を削除し、
   `data_fetcher.py::_load_beta_config()`（正しいパスを参照する既存の共通ローダー）を
   呼び出す形に統一。`pipeline.py::_load_beta_sector()`と同じ正しいパスを参照する。
2. **バグ②解消**: Damodaran公式データセット`indname.xls`（企業別48,157社の実分類データ、
   docs/value-monitor/tanuki_valuation/common/damodaran_cache/配下に既存キャッシュ）に対し、
   tanuki=true全100銘柄のtickerを主要取引所（NasdaqGS/NasdaqGM/NasdaqCM/NYSE/NYSEAM）
   限定で直接照合し、97銘柄で対応するIndustry Group文字列を取得。
   `growth_sanity.py::SECTOR_TO_DAMODARAN`の逆引き（値→キー、beta_config.json形式ブロックのみ
   対象）で対応する省略キーへ変換し、`config/beta_config.json`の該当ticker `overrides.sector`に
   書き込んだ（`beta`/`source`等の既存フィールドは変更なし）。
   - 照合不能: 3銘柄（CIX/MO/PM）— 該当するDamodaran分類（Office Equipment & Services /
     Tobacco）に対応する省略キーがSECTOR_TO_DAMODARANに存在しないため。CIXは
     TICKER_INDUSTRY_OVERRIDESの直接値修正で対応済み（後述）。MO/PMは対応するキーが
     存在せずbeta_config.json側は未設定のまま据え置き（従来通りdefault 0.70・
     growth_sanity industry_benchmarkもNoneのまま。回帰ではなく既存の未解消状態を維持）。
3. **TICKER_INDUSTRY_OVERRIDES 8件の修正（Koichiさん確認済み: これらはテストデータであり
   意図的な業務判断ではなかった）**: `growth_sanity.py::TICKER_INDUSTRY_OVERRIDES`の
   HON/TDY/KULR/META/AMZN/NET/CIX/BKNGを、indname.xls実態分類の値に置き換え
   （例: HON "Machinery"→"Diversified"、META "Advertising"→"Software (Entertainment)"）。
   併せてCRWVの既存sector値（"Information_Services"）もindname.xls実態（"Software (Internet)"）
   と不一致だったため`beta_config.json`側を修正（TICKER_INDUSTRY_OVERRIDES未登録のため
   sector経由の修正のみ）。
4. **バグ③は範囲外のまま維持**: fcf_conversion_config.jsonのカテゴリ拡張は
   [[FCF-CONVRATE-DESIGN-LIMIT-1]]で別途対応。

#### 検証
- 全105銘柄（tanuki=true 100銘柄）でpipeline.py再実行（`--skip-risk`）、成功100/失敗0
- 新旧比較の結果、`fcf_estimation.conversion_rate`が変化したのは9銘柄
  （ALAB/AMD/AVGO/NVDA/RMBS/SITM→Semiconductor 0.85、CRWV/DOCN/NET→Software_Internet 0.9）
  のみで、意図した銘柄以外への波及なしを確認
- `growth_sanity.damodaran_industry`が変化したのは80銘柄（大半はNone→実値。
  HON/TDY/KULR/META/AMZN/NET/CIX/BKNG/CRWVの9件はテストデータ値→indname.xls実態値）
- `report_consistency_check.py`: NG=0（警告36件は全て既存確認済み、新規警告0件）
- pytest: 309 passed / 2 known failed（MSFT/NVDA、[[TEST-STALE-IV-1]]の既知バグ、
  本修正とは無関係）

#### 実装判断の経緯
実装前段階で、HON/TDY/KULR/META/AMZN/NET/CIX/BKNGの8件のミスマッチ
（indname.xls実態分類とTICKER_INDUSTRY_OVERRIDES登録値の不一致）を
機械的ルールで説明できないか複数の仮説を検証した：最大収益セグメント
ルール（再現率1/8）・業種平均ベータ近似（材料不足で検証不能）・
収益性/成長率近似ルール（再現率最大1/8）。いずれも再現率が低く、
単一の業務ロジックで一貫して説明できなかったため、テストデータの
可能性を疑うに至った。

実装依頼時、この8件が「意図的な業務判断ではなくテストデータ」と
記載されていたが、各エントリに具体的な業務理由コメントが付いていたこと、および
全105銘柄の成長率サニティチェックに使われる本番辞書であることから、実装前にKoichiさんに
直接確認を行った。Koichiさんより「直接確認済み」との回答を得た上で着手。あわせて
`beta_config.json`のsectorより優先順位が高い`TICKER_INDUSTRY_OVERRIDES`との不整合を
防ぐため、8件（+CRWV）を同時に修正する方針とした。

---

### ✅ [FCF-EPS-CONVRATE-SECTOR-1] LITE/SITM等でEPS推定FCFの一律conversion_rate=0.7が業種特性に不適合の疑い（2026-07-14完了・既存バグの実害具体例と判明）
**分類:** DCF信頼性判定ロジック / データ推定
**登録日:** 2026-07-14
**完了日:** 2026-07-14
**発見:** [[POLICY-AB-TREND-BLIND-1]]と同一調査

#### 内容
LITE・SITM共にPolicy B（eps_invalid型、divergence_ratio 4.33倍・2.55倍）で
LOW判定。`calculator/adjustments.py::estimate_fcf_from_eps()`が使う業種一律
conversion_rate=0.7が、両銘柄（光デバイス・ファブレス半導体、循環的CapEx/
在庫サイクル変動大）の実態に合っていない疑い。個別XBRLタグ自体（OCF/CapEx/
NetIncome）に重複値・欠損は確認されず、タグ由来ではなく推定手法の
アサンプション由来の疑い。

#### 調査結果・クローズ理由
LITE・SITMのconversion_rate異常（乖離3.65倍/2.55倍）を調査した結果、
独立バグではなく既存[[SECTOR-FCF-RATE-BROKEN-1]]（beta_config.jsonの
パス誤り`src/value/beta_config.json`→正しくは`config/beta_config.json`で
sectorが空文字列になる）が実際に引き起こしている実害の具体例と判明した
ためクローズ。同じバグ経路を通るLRCX・ENTGでは乖離がほぼ無い
（0.86〜0.94）ことから、バグ自体は業種横断だが実害の大きさは
LITE/SITM固有の事業特性（在庫・キャップサイクルの振れ幅）に依存する
ことを確認。副次発見の2課題は[[FCF-CONVRATE-DESIGN-LIMIT-1]]として
分離登録。

---

### ✅ [TRANSIENT-EXPENSE-COVERAGE-1] AVAV/RDWで一過性費用検出モジュールがFCF悪化幅を説明しきれない（2026-07-14完了・悪化の主因は構造的要因と確認）
**分類:** データ品質 / 一過性費用検出
**登録日:** 2026-07-14
**完了日:** 2026-07-14
**発見:** [[POLICY-AB-TREND-BLIND-1]]と同一調査

#### 内容
AVAV: 検出された一過性費用$11M（在庫評価損・貸倒引当金）に対し実際の
悪化幅$100M超で説明力不足。M&A統合費用カテゴリは分類器に存在するが
今回検出されず、検出網羅性に疑問。
RDW: 検出された一過性費用$14M（在庫評価損）に対し実際の悪化幅$150M超で
同様に説明力不足。

関連: [[FCF-OUTLIER-QUAL-1]]（一過性費用の説明妥当性の定性評価導入。
本件はaction=excluded判定が量的閾値だけで下りている実例の一つ）

#### 調査結果・クローズ理由
AVAV・RDWとも一過性費用の検出漏れ（M&A取引費用タグ不足）は実在するが、
10-K原文（MD&A）で悪化の主因を確認した結果、AVAVは在庫・売掛金増加に
伴う運転資本投資（$236.6M）、RDWは契約マイルストーン請求タイミングに
よる運転資本変動（$74.0M）＋純損失拡大（$112.2M）であり、いずれも
構造的要因が主因と判明。両銘柄の現状のFCF数値・DCF計算は正しいと判断し
クローズ。検出モジュール自体の穴は[[MA-INTEGRATION-TAG-GAP-1]]として
分離登録（全銘柄への影響は未調査）。

---

## 2026-07-13（完了）

### ✅ [HYPECORE-DASHBOARD-COUNT-BUG-1] docs/index.htmlのhypecore ticker数表示修正（2026-07-13完了）
**分類:** バグ / フロントエンド表示
**登録日:** 2026-07-12
**完了日:** 2026-07-13
**発見:** [[HYPECORE-SAVE-INDEX-NAMEERROR-1]]（完了・BACKLOG_DONE.md参照）実装時の副次発見

#### 対応内容
`docs/index.html`（233-236行目）が`value-monitor/hypecore/data/tickers.json`
（実形式`{tickers: [...], updated_at, count}`のオブジェクト）に対して
`Array.isArray(arr)`という配列判定を行っており常にfalseとなるため、
トップダッシュボードの「hypecore-ticker-count」「hypecore-status-count」
表示が機能していなかった。判定を`data && Array.isArray(data.tickers)`に、
カウント元を`data.tickers.length`に修正した。

hypecore.py側で`count`フィールドは常に`len(tickers)`から生成されており
（`_save_tickers_index()`）`tickers.length`と`count`は完全に一致するため、
どちらを使っても結果は同じだが、元コードの意図（`arr.length`で配列長を
数える）に近い`tickers.length`を採用した。

#### 検証
- 修正後のJSロジックを実データ（tickers.json、103銘柄）に対して
  Pythonでシミュレーションし、`hypecore-ticker-count`/
  `hypecore-status-count`が正しく「103」を表示することを確認
- ローカルHTTPサーバーでページ・JSONの200応答を確認
- **横展開確認**: tickers.jsonを参照する他8箇所
  （`docs/portfolio/index.html`・`docs/value-monitor/admin.html`・
  `docs/value-monitor/extreme-fear/index.html`・
  `docs/value-monitor/hypecore/index.html`・
  `docs/value-monitor/tanuki_score/index.html`・
  `docs/value-monitor/tanuki_valuation/index.html`・
  `docs/value-monitor/tanuki_valuation/stock.html`）を全て確認した結果、
  いずれも`.tickers || []`等で正しくオブジェクト形式を処理しており、
  同型バグは`docs/index.html`のみだった
- pytest 309 passed / 2 known failed（既知のみ、フロントエンド変更のため
  Python側への影響なし）

---

### ✅ [WARN12-COHR-ONDS-1] COHR・ONDSのCash-STI期ズレWARN解消（2026-07-13完了・原因はコードバグではなく生成順序のズレ）
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-12
**完了日:** 2026-07-13
**発見:** [[HYPECORE-ZS-EPS-STALE-1]]完了検証時（`report_consistency_check.py`実行）

#### 根本原因（実態調査で判明）
fact競合型のバグ（SEC-TAG-FICO-CPRT-1・Phase 2a等）ではなく、**SEC自動更新と
TANUKI VALUATION再生成の生成順序のズレ**だった。

| コミット | 内容 | JST時刻 |
|---|---|---|
| `54bacca72` | TANUKI VALUATION全銘柄再生成（latest.json生成） | 2026-07-12 01:52:42 |
| `b6abc0a2a` | SEC Data自動更新（COHR/ONDSのSTIが825M/448Mに更新） | 2026-07-12 21:45:35 |

latest.jsonはSEC自動更新の約20時間前に生成されており、その時点の
quarterly_*.jsonにはまだ現在の短期投資額が反映されていなかった。
pipeline.py側の`_q_st_invest_override`ロジック自体は正しく動作しており、
コード修正は不要と判断。COHR・ONDSともannual_2025.jsonに
`short_term_investments`キーが存在しないことから、両銘柄とも直近の四半期
（COHR 2026Q3・ONDS 2026Q1）で初めて短期投資を保有し始めたとみられる
（実際の事業変化、タグ誤りではない）。

#### 対応
`pipeline.py COHR ONDS --skip-risk`を再実行。
- COHR: `short_term_investments` 0.0 → 825,000,000（net_debt 1,601,051,000 →
  776,051,000、intrinsic_value_per_share $32.38 → $36.59）
- ONDS: `short_term_investments` 0.0 → 447,842,000（net_debt -1,024,203,000 →
  -1,472,045,000、intrinsic_value_per_share $2.23 → $3.01）
- Classificationはいずれも変化なし

#### 検証
- `report_consistency_check.py`: WARN-12がCOHR/ONDS双方で解消、
  未確認WARN 2件→0件（総WARN数39→37件）、NG=0維持
- pytest 309 passed / 2 known failed（既知のみ、新規回帰なし）

#### 副次発見: 構造的ギャップ
根本原因調査の過程で、SEC_Data_Update.yml（日曜21:00 JST）と
TANUKI_VALUATION_Update.yml（平日23:05 JST）の間に自動連携がなく、
`config/workflow_dependencies.json`が定義する論理的依存関係が実際の
GitHub Actionsトリガーとして実装されていないことが判明。日曜〜月曜の
約26時間、同種のズレが構造的・恒常的に発生しうる。[[WORKFLOW-SEC-TANUKI-GAP-1]]
として優先度：中で新規登録（実装は次回セッション判断）。

---

### ✅ [ASTS-SHARES-OSCILLATION-1] diluted_shares_used往復変動の恒久修正（2026-07-13完了・影響範囲がASTS/AVAV/RCATの3銘柄に拡大確認）
**分類:** バグ修正 / EPS ANALYZER
**登録日:** 2026-07-12
**完了日:** 2026-07-13
**発見:** [[SPLIT-AUTO-CHECK-1]]実装後の全105銘柄横断ジャンプスキャン時

#### 調査の経緯（3セッションにわたる段階的調査）
1. **実態調査**: ASTSの`diluted_shares_used`往復パターンの根本原因を特定。
   `extract_key_facts.py`の株式数フォールバック④（yfinance現在株数の
   無条件代入、892-963行目付近）が原因。本来「全期間タグ欠落」銘柄
   （Visa等）向けの設計だったが、一部四半期のみタグが欠落している
   ASTSにも適用され、スクリプト実行時点の現在株数が過去の四半期
   （2020年〜2024年、SPAC合併前を含む）に一律で逆行伝播していた。
2. **横展開調査**: 全105銘柄を機械スキャンし、同一値が3回以上出現かつ
   中央値から1.5倍以上乖離するパターンを検出。ASTS・AVAV・RCATの3銘柄で
   yfinance現在株数との完全一致を確認（フォールバック④確定）。LOARは
   別原因（IPO前の名目株数、既存[[EPS-LOAR-1]]で追跡中）と判明し対象外。
3. **恒久修正**: 上記調査結果に基づき実装。

#### 恒久修正の内容
`src/value/adjusted_eps_analyzer/extract_key_facts.py`のみ変更。
- 新設: `_neighbor_quarter_diluted_shares(quarters_map, target_key)` —
  target_keyに時間的に最も近い他の四半期の実株数（直前優先、なければ直後）
  を返す共通ヘルパー
- 株式数フォールバック③として、②(Basic株数代用)と旧③(yfinance、④に改番)の
  間に「隣接する実四半期からの引き継ぎ」を挿入。②までで埋まらなかった
  四半期は、まず隣接する実四半期の値を引き継ぐようになり、隣接データが
  一切ない（＝全期間欠落）銘柄のみ従来通りyfinance代入（④）に落ちる
- Q4ブロック（10-KからQ4を計算する際の既存の「Q3の実株数を引き継ぐ」
  インライン処理）を、新設ヘルパーを使う形に一般化（Q3も欠落している場合に
  より遠い四半期まで探索できるようになった。通常ケース〈Q3にデータあり〉
  では挙動は変わらない）

#### 検証結果
- ASTS・AVAV・RCAT: 修正後、往復パターンが解消し滑らかな時系列になったことを
  実データで確認（例: ASTS 298,746,383株の7回repeated stampが消滅し、
  51.8M→53.2M→81.8M→141M→...→290.7Mの一貫した成長トレンドに）
- Visa（全期間タグ欠落、フォールバック④本来の対象）: 修正後も引き続き
  yfinance代入（1,659,709,932株）にフォールバックすることを確認、
  既存動作は維持されている
- **全101銘柄（EPS Analyzer対象、eps=true）でのライブ新旧比較の結果、
  当初のASTS/AVAV/RCAT3銘柄に加え、CART・CEG・BROS・GEV・XOM・CONの
  計6銘柄でも同型の値変化を検出した（影響範囲は当初推定の3銘柄から
  9銘柄に拡大）**。いずれも「特定の値が複数四半期・複数年に渡って
  不自然に繰り返される」→「四半期ごとに異なる、より妥当な値」という
  同じ方向の変化であり、正しい修正結果と判断した。これらは初回の
  横展開調査（count>=3・ratio>1.5の閾値）では検出されなかった、より
  軽微な発生パターン（1〜4四半期のみの影響等）だった。
- **副次的な挙動変化（想定外だが正の効果と判断）**: BROSの2021-03-31が
  修正後に新たに出力へ含まれるようになった。原因は、旧フォールバック④
  （yfinance代入）が`net_income != 0`を発動条件としていたため、
  net_income=0（実在するが損益ゼロの四半期）が無条件に出力から除外
  されていたため。新設のフォールバック③にはこの条件がなく、隣接四半期の
  実データで埋められる限り出力に含まれるようになった（データの欠落が
  減る方向の変化、副作用ではなく改善と判断）。
  一次情報で確認したところ、この四半期は売上$98.785Mが実在する一方
  net_income=0（端数なし）というUp-C構造特有の組織再編前会計処理の
  産物と判明。株数の引き継ぎ自体は妥当だが、SBC調整により見かけ上
  プラスのAdjusted EPSが新たに算出される点は別軸の設計論点のため
  [[EPS-UPC-PREREORG-1]]として分離登録した。
- pytest 309 passed / 2 known failed（新規4件`tests/test_extract_key_facts_share_fallback.py`
  追加、既存`tests/test_extract_key_facts_split.py`の4件を含め回帰なし）
- 新規テストにGROWTH-CAGR-SIGN-1的な「意図的な違反シナリオ」は不要だが、
  「全期間欠落銘柄は引き続きyfinanceに落ちる」ことの回帰テストを含めた

---

### ✅ [TICKER-DIRECT-ACCESS-GUARD-1] 銘柄フラグ・SECデータ直接参照の機械的検知（CIガード新設）（2026-07-13完了）
**分類:** アーキテクチャ / 予防的品質ゲート（QUALITY-GATES-EPIC-1関連）
**登録日:** 2026-07-13
**完了日:** 2026-07-13
**発見:** FLAG-CONSUMER-AUDIT-2/3で発見した7箇所の独立実装の根本原因分析

#### 背景
FLAG-CONSUMER-AUDIT-2/3で発見した7箇所の独立実装（「共有アクセサ経由で
銘柄リストを取得する」規約の違反）は、規約がCLAUDE_CODE_START.mdという
ドキュメントのみに存在し、CIによる機械的強制がなかったことが根本原因。
新規スクリプト追加のたびに同種の問題が再発するリスクが高いため、
pytestレベルでの検知ガードを新設した。

#### 実装内容
`tests/test_no_direct_ticker_access.py`を新設。2パターンを検知する：
- **①cik_lookup.csv直接パース**: `csv.DictReader`で直接パースしている
  箇所をAST解析で検出
- **②ルートデータディレクトリの`os.listdir()`直接スキャン**: SEC/
  TANUKI VALUATION/HypeCore/EPS ANALYZERの「全ティッカーのサブ
  ディレクトリを含むルートディレクトリ」への`os.listdir()`を、
  `os.path.join(...)`の末尾引数がリテラル`"data"`（それ以降に
  追加の位置引数がない＝ティッカー名等が続かない）というパターンで
  AST解析により検出

いずれも許可リスト方式（ファイル単位）。単一ティッカーのCIK参照・
既知ティッカーのサブディレクトリ内ファイル列挙等の正当な用途を機械的に
区別することは（変数の間接参照解決の複雑性から）割に合わないと判断し、
「検出されたファイルは全て許可リストに載せ、用途をコメントで明記する」
設計とした。新規ファイルがいずれかのパターンに一致すると、許可リストに
追加するかtickers.py経由に直すかの判断を強制するレビューフィルターとして
機能する。

既知の限界（意図的な設計上の簡略化、テストファイルのdocstringに明記）：
関数呼び出しを介した間接参照（例: `score_verifier.py`の
`data_dir = _data_dir()`）は解決しない、文字列結合・f-stringは認識しない。

#### 全リポジトリスキャン結果（許可リストの内容）
①cik_lookup.csv直接パース検出: 12ファイル（全て許可リスト入り）
- 共有アクセサ本体: `tickers.py`・`config.py`
- 監査ツール（設計上無条件スキャンが必要）: `registration_validator.py`・
  `system_health.py`
- 単一ティッカーのCIK/会社名参照（バッチリスト構築ではない）:
  `data_fetcher.py`・`pipeline.py`（tanuki_valuation）・
  `kpi_proposer.py`・`sec_ctrl_fetcher.py`・`text_kpi_extractor.py`（TAIL）
- EPS ANALYZER独自パイプライン（`common/sec_data/`とは完全独立と
  SYSTEM_MAP.mdに明記済み）: `extract_key_facts.py`・
  `adjusted_eps_analyzer/pipeline.py`・`sector_classifier_v2.py`

②ルートディレクトリlistdir直接スキャン検出: 5ファイル（全て許可リスト入り）
- `registration_validator.py`（P4-SecDataOrphan/P5監査、設計上無条件
  スキャンが必要）
- `reader.py::get_available_tickers()`（未使用・`__main__`専用の
  デバッグ関数、本番呼び出し元なし）
- **`phase1_scan.py`・`tail_dcf_bridge.py`・`backfill_history.py`
  （下記「本タスクのスコープ外の発見」参照）**

#### 本タスクのスコープ外の発見（内訳: 1件対応・4件BACKLOG登録）
遵守事項に従い、検出時点では既存の違反箇所をその場で修正せず報告のみに
留めた。その後、追加依頼を受けて1件（tail_dcf_bridge.py）のみ同日中に
対応し、残り4件はBACKLOG登録した。

**対応済み（同日中）:**
1. **`src/tail/tail_dcf_bridge.py`**（`main()`の`--ticker`未指定時
   フォールバックパス）: `os.listdir(VALUATION_DIR)`で
   `docs/value-monitor/tanuki_valuation/data/`を無条件スキャンし、
   tanukiフラグを見ない構造だった。`.github/workflows/
   TANUKI_TAIL_RSS_Monitor.yml`から呼ばれているが、ワークフロー側は常に
   `--ticker $TICKERS`を明示指定しており自動実行での実害はなかったが、
   手動での引数なし実行時の潜在リスクを解消するため`tickers.
   get_tanuki_tickers()`との積集合でフィルタを追加。副次的に、
   VALUATION_DIR直下に残存していた非ティッカーディレクトリ
   （`hypecore_history`）が誤ってティッカー扱いされる潜在バグも解消。
   検証: フィルタ適用後の実データで`RKLB`・`ZS`（tanuki=false）・
   `hypecore_history`が対象から正しく除外され、103ディレクトリ中
   100件（tanuki=true）のみが残ることを確認。pytest 305 passed/
   2 known failed（新規回帰なし）。

**BACKLOG登録のみ（未対応）:**
2. **[[PHASE1-SCAN-CLEANUP-1]]**: `common/sec_data/phase1_scan.py`が
   `os.listdir(DATA)`で無条件スキャン。ハードコードされた
   `TODAY = date(2026, 6, 11)`から一回限りの診断スクリプトと推測。
3. **[[BACKFILL-HISTORY-CLEANUP-1]]**: `src/value/tanuki_valuation/
   backfill_history.py`が`os.listdir(DATA_ROOT)`で無条件スキャン。
   コメント「May 14-16 History Backfill (v8.2)」から一回限りの
   バックフィルスクリプトと推測。
4. **[[SYSHEALTH-CIK-DEDUP-1]]**: `system_health.py`が`tickers.
   get_all_tickers()`で代替可能な独自CSVパースをしている（バグではなく
   コード重複）。
5. **[[TAIL-CIK-LOOKUP-DEDUP-1]]**: TANUKI TAILの3スクリプト
   （`kpi_proposer.py`・`sec_ctrl_fetcher.py`・`text_kpi_extractor.py`）が
   `load_cik(ticker)`を3箇所独立に重複実装している（FLAG-CONSUMER-
   AUDIT-2/3型のバイパスバグではなく単純なDRY違反）。

いずれも優先度：低でBACKLOG.mdに登録済み。

#### 検証
- 新設テストが意図的な違反コード（`common/sec_data/_tmp_violation_check.py`
  を一時追加、①②双方のパターンを含む）に対して正しく失敗することを確認
  後、一時ファイルを削除
- 現状のリポジトリに対して3件のテストが全てパスすることを確認
- tail_dcf_bridge.py修正後も引き続き3件のテストがパスすることを確認
  （許可リストのコメントを「未確認」→「フィルタ済み」に更新）
- pytest 305 passed / 2 known failed（新規3件追加、既存回帰なし）

#### CLAUDE_CODE_START.md更新
「新規スクリプト追加時、このCIガード（`tests/test_no_direct_ticker_access.py`）
が自動的に規約違反を検知する」旨を追記。既存の手動チェックリスト記述
（銘柄フラグを参照するスクリプトの必須パターン）と重複しないよう、
「手動での実施事項」と「CIが機械的に検知する事項」を書き分けた。

---

### ✅ [ARCH-DATA-1-PREP-1] QUALITY-GATES-EPIC-1 Phase 3前提整理・小粒4項目（2026-07-13完了）
**分類:** アーキテクチャ / SECデータ取得層 / 品質管理
**登録日:** 2026-07-13
**完了日:** 2026-07-13
**発見:** ARCH-DATA-1棚卸し調査（Gate2設計セッション前の前提整理）

#### 背景
ARCH-DATA-1の棚卸し調査で、Gate2本体（正規化契約の構造化）着手前に
片付けるべき小粒4項目（TAG-DEFS-UNIFY-1のクローズ判断・normalized JSON
不足フィールド補完・audit.py UP-C検知・バグA/Bのスコープ判断）が
残っていることが判明したため、まとめて対応した。

#### ①TAG-DEFS-UNIFY-1のクローズ判断 → 完了クローズ（BACKLOG.mdから本ファイルへ全文移動）
- LTDebt・RPOはpoint-in-time概念のためduration競合バグの対象外（2026-07-12の
  機械調査で既に確定済み）。今回のSOFI-DATA-1調査でも改めて確認し、判断を追認。
- revenueの残論点（parser.pyのみが持つ候補タグ`RevenueFromContractWithCustomer`
  〈接尾辞なし〉がquarterly.pyの`_REVENUE_FALLBACKS`に未統合）を機械調査した結果、
  現行105銘柄中このタグを申告している銘柄は**0件**。理論上の拡張余地はあるが
  実害ゼロと確認。新規登録銘柄がこのタグに依存するケースが出た場合はStep 1
  （SECデータ取得）後のaudit.py/report_consistency_checkで検知される設計のため、
  個別対応で十分と判断しクローズ。

#### ②normalized JSON不足フィールド補完 → 実装完了
- **ShortTermInvestments**: 調査の結果、**既に解消済み**と判明（当初のARCH-DATA-1
  記載が陳腐化していた）。parser.py（年次・per-quarter snapshot側）は
  XBRL_MAPPINGに`short_term_investments`を既に保有しており、pipeline.py/
  reader.pyのget_net_cash()がBUG-NETDEBT-4/5（同一時点原則）経由で正しく
  消費している。quarterly.py（TTM/normalized側）には存在しないが、
  ShortTermInvestmentsを必要とする下流消費者（net_debt計算）はTTM経路を
  使っていないため実害なし。追加実装は不要と判断。
- **銀行移行後LTDebt（SOFI-DATA-1）**: SOFIは銀行免許取得後（2022年以降）
  `LongTermDebt`/`LongTermDebtNoncurrent`タグの申告を停止し、`DebtLongtermAnd
  ShorttermCombinedAmount`（短期+長期合算）タグに移行していたが、2026-06-24の
  過去修正はnormalized JSONへの**手動一回限りパッチ**（quarterly.pyフェッチ
  スクリプトが対応していないため）であり、その後の自動再生成（`update.py`実行）で
  静かに巻き戻り、本セッション開始時点でLTDebtが2022-12-31のまま3年以上
  stale化していた実害を発見（Net_Debt +$2.08B〈実際は誤り〉として表示）。
  - 恒久修正: `quarterly.py`のグローバルなLTDebtフォールバック候補リストに
    このタグを追加する案は、AVGO（annual最新年2021→2025に変化）・VZ
    （annual最新年2013→2025、quarterly 0件→19件に変化）等、無関係な既存銘柄
    18件に予期せぬ副作用を及ぼすことを検証で確認したため**不採用**。
  - 代わりに、既存の`revenue_concept`オーバーライド（`TICKER_RESTRICTIONS`）と
    同一パターンで`ltdebt_concept`を新設し、SOFI限定のticker-scopedオーバーライド
    として実装（`quarterly.py`・`parser.py`双方に同一ロジックを追加）。
    他17銘柄への影響ゼロを個別確認済み。
  - 検証: `update.py SOFI`→`audit.py SOFI`（正常）→`pipeline.py --skip-risk SOFI`
    →`report_consistency_check.py`（NG=0、SOFI該当WARNなし）→pytest 265 passed/
    2 known failed（新規回帰なし）。
  - 影響: SOFI Net_Debt +$2.08B（誤・stale）→ -$1.59B（正・net cash、
    net_debt_period="Cash=2026Q1/Debt=FY2025"の期ズレも解消し"2026Q1"に統一）。
    Intrinsic_Value $15.76→$21.17。Classification は WATCH のまま変化なし
    （DCF_Reliability=LOW・Policy B丸めが引き続き適用されるため）。

#### ③audit.py: UP-C構造株式数タグ一覧化 → 実装完了
- `common/sec_data/audit.py`の`audit_ticker()`に、raw quarterly table
  （`common/sec_data/raw/{ticker}_quarterly_raw.json`）のSharesBasic/
  SharesDiluted双方が四半期エントリ0件の銘柄を検知するチェックを追加。
- 全100銘柄でテスト実行し、**V（Visa）**を新規検知（複数株式クラス構造のため
  `CommonStockSharesOutstanding`/`WeightedAverageNumberOfDilutedSharesOutstanding`
  等の標準us-gaapタグを一切申告しておらず、`dei:EntityCommonStockSharesOutstanding`
  のみ保有）。他99銘柄は誤検知なし。
- 検証: pytest 265 passed/2 known failed（新規回帰なし）。

#### ④バグA・Bのスコープ判断 → 既に解消済みと判明（記録訂正のみ）
- `_estimate_ttm_operating_income()`のGrossProfit/RD/SM期末日不整合
  （`dict.get(end, 0)`による暗黙0円フォールバック）は、ARCH-DATA-1に
  「新規スコープ候補」として記載された**同日**（2026-07-09）の
  コミット`1a8f5253d`「Moat Scoreフォールバックの2件のバグを修正
  （バグA・B）」で、3フィールド共通end日のset intersection方式
  （4件未満ならNone）に**既に修正済み**だったことが判明。
  BACKLOG.mdへの記載（同日20:32、修正コミットの38分後）が、直前の
  修正を反映せず「未着手の新規スコープ候補」のまま残置されていた
  記録上の陳腐化だった。grep確認により同種パターン（`.get(end, 0)`式の
  暗黙0円フォールバック）の他箇所残存もなし。追加実装不要。

#### 影響ファイル
`common/sec_data/quarterly.py`・`common/sec_data/parser.py`
（SOFI限定`ltdebt_concept`オーバーライド追加）・`common/sec_data/audit.py`
（UP-C検知追加）・`BACKLOG.md`（ARCH-DATA-1記載の陳腐化3箇所訂正・
TAG-DEFS-UNIFY-1クローズ）

#### QUALITY-GATES-EPIC-1への反映
Phase 3（ゲート0＋2）着手前提として本タスクを実施。Gate2本体
（正規化契約の構造化・型によるフィールド規約のコード化）は未着手のまま、
次回セッションでの設計セッション対象として残る。

---

## 2026-07-12（完了）

### ✅ [HYPECORE-SAVE-INDEX-NAMEERROR-1] hypecore.pyのNameError緊急修正（本番障害・2026-07-12完了）
**分類:** バグ / HypeCore（優先度：高・実害確認済みの本番障害）
**登録日:** 2026-07-12
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 実害確認調査（別途実施済み）で判明した内容:
  - `_save_tickers_index()`の呼び出し（旧1009行目）が関数定義（旧1012行目）
    より前にあり、`if __name__ == "__main__":`実行時に必ず`NameError`が
    発生（`--all`/`--batch`/単体指定/無引数いずれのモードでも無条件・
    try/exceptなしでクラッシュ）。個別ticker処理自体は影響を受けないが、
    末尾のインデックス再生成ステップが常に失敗する。
  - バグ混入はコミット`5f754eda4`（2026-07-09 21:54:13）。同一コミットで
    呼び出しと定義を同時新設し、実機検証なしでコミットされたと推定
    （`tickers.json`の`updated_at`が混入コミットの3分前`21:51:17`で
    停止していたことから裏付け）。
  - `.github/workflows/HypeCore_Update.yml`の"Run HypeCore Pipeline"
    ステップに`continue-on-error`/`if: always()`の設定がなく、
    GitHub Actionsのデフォルト動作（fail-fast）により
    **NameError発生時は後続の"Commit and push changes"ステップが
    スキップされる**。2026-07-09 21:54以降、週次自動更新
    （毎週日曜13:08 UTC=22:08 JST）が3日間沈黙的に空振りし続けていた
    本番障害と判断。
- 対応: `src/value/hypecore/hypecore.py`の`_save_tickers_index()`の
  関数定義を、`_filter_hypecore_tickers()`の直後・
  `if __name__ == "__main__":`ブロックより前へ移動（ロジック自体は無変更）。
- 検証: 前回の混入がまさに「実機検証なしのコミット」で発生したため、
  pytestだけでなく`python hypecore.py PLTR`を実機で直接実行し、
  NameErrorが発生せず終了コード0で完走することを確認。実行後
  `tickers.json`の`updated_at`が最新化（2026-07-09 21:51:17→
  2026-07-12 22:21:34）され、`tickers.json`記載103銘柄と実在する
  `*_poc.json`103件の一致状態が維持されていることを確認。
  pytest 265 passed/2 known failed（既存回帰なし、今回新規テスト追加なし。
  検証対象がロジック変更ではなく定義位置の移動のため、既存の
  `tests/test_flag_consumer_audit_3.py`の`TestHypecoreFilterTickers`が
  引き続き通ることで間接的にモジュールロード健全性を確認済み）。
- 副次発見（今回のスコープ外・BACKLOG登録のみ、修正せず）:
  `docs/index.html`が`tickers.json`を`Array.isArray(arr)`で判定しているが、
  実際の形式は`{tickers, updated_at, count}`というオブジェクトのため
  判定が常にfalseになる、独立した別の形式不一致バグを発見。
  [[HYPECORE-DASHBOARD-COUNT-BUG-1]]として新規登録。

### ✅ [HYPECORE-ZS-EPS-STALE-1] ZSのEPS Analyzer残存データ削除（2026-07-12完了・RKLB分は登録内容を訂正の上対応不要と判断）
**分類:** データ品質 / 銘柄登録フロー
**登録日:** 2026-07-12
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 実装着手前にcik_lookup.csvを直接再確認したところ、**RKLBは実際は
  hypecore=true**（tanuki=false・stonks_silo=true・eps=true・hypecore=true）
  であり、前回セッション（FLAG-CONSUMER-AUDIT-3実装時）での私自身の調査ミスで
  「RKLBはhypecore=false」と誤った前提のままBACKLOG登録していたことが判明。
  `docs/value-monitor/hypecore/data/RKLB_poc.json`は残存データではなく
  hypecore=true銘柄として正当に必要なデータであり、**削除対象外**と訂正。
  検証中に一度誤って削除してしまったが、コミット前に`git checkout`で
  復元済み（本番には反映されていない）。
- ZSは`eps=false`（tanuki=false・stonks_silo=true・eps=false・hypecore=true）
  を直接確認済みで、こちらの前提は正しかったため、
  `docs/value-monitor/adjusted_eps_analyzer/data/ZS/`
  （annual.json・quarterly.json・ttm.json）を削除。ZSのhypecore用データ
  （`ZS_poc.json`、hypecore=trueのため正当）・stonks-silo側データ
  （stonks_silo=trueのため正当）は削除対象外として維持。
- 検証: `adjusted_eps_analyzer/pipeline.py --ticker ZS`実行でeps=false検出の
  警告が出て正しく除外され、ディレクトリが再生成されないことを確認。
  hypecore.py・stonks-silo側のRKLB・ZSデータが無影響であることを確認。
  `report_consistency_check.py --fail-on-ng`でNG=0を確認（WARN数はGitHub
  Actions自動SEC更新による無関係な新規WARN2件を含むため37→39に変化、
  詳細は[[WARN12-COHR-ONDS-1]]参照）。pytest 265 passed/2 known failed
  （既存回帰なし、今回新規テスト追加なし）。
- 副次発見（今回のスコープ外・BACKLOG登録のみ、修正せず）:
  1. hypecore.pyの実機検証中、`_save_tickers_index()`の呼び出しが関数定義
     より前の行にあるため常にNameErrorでクラッシュする既存バグを発見
     （FLAG-CONSUMER-AUDIT-3の変更とは無関係、5f754eda4時点から存在）。
     [[HYPECORE-SAVE-INDEX-NAMEERROR-1]]として新規登録。
  2. GitHub Actions自動SEC更新後にCOHR・ONDSで新規WARN-12（Cash-STI期ズレ）
     を検出。[[WARN12-COHR-ONDS-1]]として新規登録。

### ✅ [FLAG-CONSUMER-AUDIT-3] 他パイプラインへのCLI引数フラグ検証横展開（2026-07-12完了）
**分類:** アーキテクチャ / 銘柄登録フロー
**登録日:** 2026-07-12
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- Part 1調査で、FLAG-CONSUMER-AUDIT-2と同型（`--all`はcik_lookup.csvの
  フラグで正しくフィルタされるが、CLI引数でticker明示指定時はフラグ検証を
  一切行わない）の構造的ギャップを3箇所で確認:
  1. `src/value/hypecore/hypecore.py`: `--batch TICKER...`・単体指定
     （`python hypecore.py TICKER`）がhypecore=trueを検証せず処理
  2. `src/discover/catalyst.py`: `--ticker NVDA,IONQ`指定時にhypecore=trueを
     検証せず処理
  3. `src/value/adjusted_eps_analyzer/pipeline.py`: `--ticker`指定時、
     monitor_tickers.yaml突合（非ブロッキング警告のみ）はあったが、
     eps=trueフラグの検証は一切なし
- 対応: 上記3ファイルに`_filter_hypecore_tickers()`（hypecore.py・
  catalyst.pyそれぞれに新設。関数シグネチャ統一のため対象ticker集合を引数化）・
  `_filter_eps_tickers()`（adjusted_eps_analyzer/pipeline.py）を追加し、
  範囲外ticker指定時は警告・除外するガードを実装。hypecore.pyは元々
  `_filter_hypecore_tickers`が`if __name__ == "__main__":`ブロック内の
  ローカル関数として書かれていたため、テスト可能にするためモジュールレベルへ
  リファクタし、`ALL_TICKERS`への暗黙依存を引数化した。
- **`common/screening/dcf_validity_checker.py`は意図的に未修正**（Koichiさん
  確認済み）: 同型のギャップ（`tickers = args.tickers or _all_tanuki_tickers(...)`
  でpositional引数指定時にtanuki=true検証なし）を発見したが、これは
  `--output`未指定時は標準出力のみで本番データを書き換えない読み取り専用の
  診断ツールであり、tanuki=false/candidate銘柄の事前診断用途を意図的に
  許容している設計と判断。他3件（pipeline書き込み系）とはリスクレベルが
  異なるため対象外とした。
- 検証: `_filter_hypecore_tickers()`・`_filter_eps_tickers()`を直接呼び出し、
  本番cik_lookup.csvのhypecore=false銘柄（ENB）・eps=false銘柄（ZS）が
  正しく除外されることを確認。回帰テスト`tests/test_flag_consumer_audit_3.py`
  7件追加、pytest 265 passed/2 known failed。
- 副次発見（今回のスコープ外・BACKLOG登録のみ、修正せず）: `hypecore.py --batch`
  等の対象外化に伴い実データ側（`docs/value-monitor/hypecore/data/RKLB_poc.json`
  ＜hypecore=false＞・`docs/value-monitor/adjusted_eps_analyzer/data/ZS/`
  ＜eps=false＞）にも同種の残存ファイル問題があることを発見。
  [[HYPECORE-ZS-EPS-STALE-1]]として新規登録。

### ✅ [STALE-REPORT-CLEANUP-1] tanuki=false化後のRKLB・ZS残存ファイル削除（2026-07-12完了）
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 当初はRKLB・ZSの`report.txt`残存のみが問題として登録されていたが、
  実際の調査では`report.txt`・`latest.json`・`history.json`・`history/`
  （日次IV履歴、いずれもTANUKI VALUATION固有アーティファクト）の4種が
  両銘柄とも残存していることを確認。
- `score_history.json`（TANUKI SCORE判定実績追跡ファイル）は
  [[FLAG-CONSUMER-AUDIT-2]]で確立した方針（tanuki=false銘柄の過去実績
  データとして削除しない）を踏襲し、削除対象から明示的に除外した。
- 依頼文の当初スコープはRKLBのみだったが、ZSも同一の残存パターンだったため
  Koichiさんに確認の上、両銘柄を同様に削除。
- `docs/value-monitor/tanuki_valuation/data/RKLB/`・
  `docs/value-monitor/tanuki_valuation/data/ZS/`から`report.txt`・
  `latest.json`・`history.json`・`history/`を削除、`score_history.json`
  のみ残置。EPS Analyzer・STONKS SILO側の両銘柄データ（RKLB: eps=true・
  stonks_silo=true、ZS: stonks_silo=true）は別ディレクトリのため無影響を確認。
- 検証: 削除後`report_txt_parser.py::_all_tickers_with_report()`で
  RKLBが対象外であることを確認（元々tanuki=falseフィルタで除外済みのため
  スキャン結果自体に変化なし、ファイル削除によるクラッシュ等がないことの
  確認）。`report_consistency_check.py --fail-on-ng`でNG=0/WARN=37の
  維持を確認。pytest 265 passed/2 known failed。

### ✅ [SPLIT-AUTO-CHECK-1] EPS Analyzerのfact選定ロジック不整合による分割株数汚染（2026-07-12完了・QUALITY-GATES-EPIC-1 Phase 2b-3）
**分類:** データ品質 / EPS ANALYZER
**登録日:** 2026-07-12
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 当初の登録内容（split_history.yaml未登録の株式分割が16銘柄分ある）は、
  実害確認調査で**根本原因の理解が誤っていたと判明**。真因はsplit_history.yaml
  登録漏れではなく、EPS Analyzer独自の抽出パイプライン
  `src/value/adjusted_eps_analyzer/extract_key_facts.py::extract_quarterly_facts()`
  のfact選定ロジック不整合だった（common/sec_data配下とは完全に独立した経路で、
  Phase 2aのtag_definitions.py統一の対象外）。
- SEC company facts APIを直接調査し、NVDA 2024-01-28四半期で同一期間
  `(2023-01-30〜2024-01-28)`に3件のfactが競合していることを確認
  （原初filed値=分割前株数、翌年・翌々年10-Kの比較年度再掲値=分割後株数）。
  これはSEC-TAG-FICO-CPRT-1と同型のfact競合パターンだった。
- 抽出ロジックはQ1〜Q3用ループ（マッチする全factを無条件上書き＝実質
  リスト末尾勝ち）とQ4専用ロジック（先頭一致で`break`＝先頭勝ち）で
  **異なる選定規則**を使っており、偶然結果が揃うこともあれば
  （Q1〜Q3）、ズレることもあった（Q4）。
- 対応: `extract_key_facts.py`のみを対象に、Q1〜Q3・Q4両方の選定ロジックを
  「同一期間に複数factが競合した場合、filed日が最新のものを優先する」という
  単一規則に統一（Q1〜Q3: 無条件上書き→filed日比較付き上書き、Q4: 先頭一致
  break→全candidate走査でfiled日最新を採用）。split_history.yamlへの個別登録
  （対症療法）は行わず、根本修正のみで対応。
- 検証: 全105銘柄（eps=true対象）でEPS Analyzerパイプラインを再実行し、
  修正前データ（バックアップ済み）と新旧比較。**NVDA・AVGO・TSLA・LRCX・CPRT・
  CELH・KULR・RCAT・SPIR・WMT**の株数系列異常是正を確認。加えて新規発見として
  **SCCO**（periodic stock dividendの累積再掲による約2.9%の妥当な補正）が
  影響銘柄に含まれることを確認。`apply_split_adjustments()`はsplit_history.yaml
  にNOW以外未登録のため全銘柄で無介入（誤動作なし）。pytest 258 passed/2 known
  failed（新規`tests/test_extract_key_facts_split.py`4件追加）。
- 残存する構造的限界: SEC自体にfactが1件も存在しない期間（分割直後〜翌年10-Kでの
  比較年度再掲まで、10-Qは前年同四半期のみ比較掲載のため恒久的に空白となる四半期
  がある）は本修正でも是正不能。NVDA 2023-04-30四半期がこれに該当し、
  [[SPLIT-REALTIME-GAP-1]]として切り出した。
- 副次発見（今回のスコープ外・BACKLOG登録のみ、修正せず）: ASTSのdiluted_shares_used
  が往復変動する異常パターンを検出。分割由来のfact競合とは別種の可能性があり
  [[ASTS-SHARES-OSCILLATION-1]]として新規登録。DELL/HEI/SCCO/HONの当初の
  端数比率懸念はyfinance実測でperiodic stock dividend/スピンオフ調整と確認済みで
  対応不要と判断（SCCOのみ上記の通り抽出ロジック修正の副次的な恩恵を受けた）。

### ✅ [FLAG-CONSUMER-AUDIT-2] 銘柄リスト構築の未統一箇所（残る3消費者への統一アクセサ適用）（2026-07-12完了）
**分類:** アーキテクチャ / 銘柄登録フロー
**登録日:** 2026-07-12
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 発端: [[ZS-TICKERS-LEAK-1]]完了時の検証で、`common/sec_data/tickers.py`
  への統一アクセサ移行が及んでいない同型の構造的ギャップが3箇所
  （report_consistency_check.py・stonks-silo/pipeline.py・score_verifier.py）
  残っていることを発見し、本タスクとして登録・着手。
- 対応:
  1. `common/sec_data/report_consistency_check.py::run_checks()`:
     スキャン対象の`all_tickers`構築を`os.listdir(DATA_DIR)`
     （tickers.pyもcik_lookup.csvも経由しない第三の独立経路）から、
     `tickers.get_tanuki_tickers()`とreport.txt存在確認の積集合
     （report_txt_parser.pyで採用済みのパターンを踏襲）に置換。
  2. `discover/stonks-silo/src/pipeline.py::run()`: `tanuki_valuation/pipeline.py`
     のCLI引数パス修正と同型の`_filter_stonks_silo_tickers()`を新設し、
     CLI引数でticker明示指定時（`partial=True`）もstonks_silo=trueの範囲内かを
     検証。範囲外指定時は警告を出し、無条件実行はしない。
  3. `src/value/tanuki_valuation/score_verifier.py`: `--ticker`省略時の
     全銘柄スキャン（`os.listdir(data_dir)`）を`tickers.get_tanuki_tickers()`
     との積集合に限定。tanuki=false銘柄（ZS・RKLB等）の既存
     `score_history.json`は削除せず、以後の自動更新対象からのみ除外。
     `--ticker`明示指定時の挙動は変更していない。
- 検証: report_consistency_check.pyはgit stash差分で新旧スキャン結果を比較し、
  102→100銘柄・38→37 WARNで、変化はRKLBのWARN-21消失とticker数のみ
  （他銘柄のNG/WARN結果に変化なし）であることを確認。stonks-silo/pipeline.py・
  score_verifier.pyはフィルタ関数を直接呼び出し、本番cik_lookup.csvに対して
  stonks_silo=false銘柄（AAPL等）・tanuki=false銘柄（ZS・RKLB）が正しく除外
  されることと、明示ticker指定パスが変更されていないことを確認。
  `report_consistency_check.py --fail-on-ng`（NG=0/WARN=37/exit 0）で回帰なし
  確認。pytest 254 passed/2 known failed（新規10件: `tests/test_report_consistency_check.py`
  `TestRunChecksTickerScan` 2件・新規`tests/test_stonks_silo_pipeline.py` 4件・
  新規`tests/test_score_verifier.py` 3件、既存ファイルへの追加1件）。
- 追加発見（今回のスコープ外・BACKLOG登録のみ、修正せず）:
  `hypecore.py --batch`等、他のパイプラインにも同型のCLI引数フラグ検証欠如が
  ないかの横展開確認は未実施。[[FLAG-CONSUMER-AUDIT-3]]として新規登録。

### ✅ [ZS-TICKERS-LEAK-1] 銘柄リスト統一アクセサ導入＋tanuki=false銘柄(ZS)混入除去（2026-07-12完了・TICKER-SOURCE-UNIFY-1の延長）
**分類:** アーキテクチャ / 銘柄登録フロー
**登録日:** 2026-07-12
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 発端: tanuki=falseへ変更済み（2026-06-27、意図的な業態分類判断
  「Zscaler=不採算SaaS企業、DCFベースのTANUKI VALUATIONではなくSTONKS SILOの
  評価軸で扱う」）のZSが、`docs/value-monitor/tanuki_valuation/data/tickers.json`
  （TANUKI SCORE daily_pick.pyの対象銘柄リストの実体）に混入し続けていることが
  一連の調査タスクで判明。除外決定直後の時点で既に混入しており、少なくとも
  2026-07-11（前回セッション）から繰り返し発生していた既存の問題だった。
- 根本原因を3箇所特定:
  1. `pipeline.py::run()`はtickers引数が`None`（全銘柄バッチ）の場合のみ
     tanuki=trueへフィルタしており、CLI引数で明示的にティッカーを指定した
     経路はフィルタを一切通らなかった
  2. `pipeline.py::_save_tickers_index()`が既存tickers.jsonとの**和集合**
     マージのみで、一度書き込まれた銘柄はtanuki=falseへ変更されても
     除去されない構造だった（latest.json存在確認のみでフラグを見ていなかった）
  3. `common/screening/report_txt_parser.py::_all_tickers_with_report()`が
     `tickers.get_all_tickers()`（cik_lookup.csv全銘柄、tanukiフラグ無視）から
     report.txtの存在有無だけで対象銘柄を選んでいた
- 対応: `common/sec_data/tickers.py`に`get_active_tickers(flag)`を新設し
  （フラグ='true'かつstatusが'retired'でない銘柄を返す。'candidate'は
  既存運用＜WST/CON等＞を壊さないため対象に含める）、既存の
  `get_tanuki_tickers()`等4つの便利関数を内部的にこれ経由へ統一。
  上記1〜3を全て修正（1: `_filter_tanuki_tickers()`新設・CLI引数パスに適用、
  2: `_save_tickers_index()`のmerged集合をtanuki=trueへも絞り込み自己修復化、
  3: `tickers.get_tanuki_tickers()`使用へ変更）。
  `common/system_health.py`の重複CSV読み込みロジック（tanuki_tickers・
  eps_tickers）もtickers.py経由に統一（all_tickersは孤立エントリ監査目的の
  ため意図的に維持）。
- tickers.jsonから直接ZSを除去（101件→100件）。
- 検証: `pipeline.py --skip-risk ZS`実行でZSが正しく除外されることを確認
  （tickers.json更新自体スキップ）。RKLB（tanuki=false・report.txt残存のみで
  tickers.json未混入）が本修正の影響を受けないことを確認。
  `system_health.py`・`report_consistency_check.py --fail-on-ng`（NG=0/exit 0）
  で回帰なしを確認。pytest 245 passed/2 known failed（新規19件:
  `tests/test_tickers.py` 12件・`tests/test_pipeline_logic.py`
  `TestFilterTanukiTickers` 4件・新規`tests/test_report_txt_parser.py` 3件）。
- 追加発見（今回のスコープ外・BACKLOG登録のみ、修正せず）:
  `report_consistency_check.py::run_checks()`は`os.listdir(DATA_DIR)`という
  **第三の独立した経路**でスキャン対象を決めており、tickers.pyもcik_lookup.csvも
  経由しないため、ZS・RKLBとも引き続きスキャン対象に含まれている
  （実害は限定的、WARN-21等の誤検知源にはなるがNG化はしていない）。
  `discover/stonks-silo/src/pipeline.py::run()`にも同型のCLI引数フラグ検証
  欠如が存在する。詳細は[[FLAG-CONSUMER-AUDIT-2]]参照。

### ✅ [SEC-TAG-FICO-CPRT-1] FICO・CPRTのSECタグ誤取得疑い（2026-07-12完了・対象銘柄がLITEを含む3件に拡大）
**分類:** データ品質 / SECデータ取得層
**登録日:** 2026-07-10
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 当初の仮説（XBRL-TAG-KLAC-1の`_classify_period()`修正で解消済みのはず）は
  誤りと判明。`_classify_period()`はquarterly.py（四半期/TTM側）専用のロジックで、
  parser.py（年次側、revenueは`MERGE_ALL_TAGS_FIELDS`対象）の年次抽出
  （`_extract_values_merged()`）はこれを一切使用していなかった。
- 真因: 同一end_dateに複数タグ（例: FICO FY2020なら91日間の四半期比較開示を
  含む`Revenues`タグと、365日間の正規年次値を持つ
  `RevenueFromContractWithCustomerExcludingAssessedTax`タグ）が競合した場合、
  `_extract_values_merged()`が`XBRL_MAPPING`の列挙順（先に処理されたタグ）で
  実質的に早い者勝ちになっており、91日間の誤値が年次値として採用されていた。
- company_facts.jsonベースの機械調査（`start`日からduration＝期間日数を算出し
  「短期間データがform='10-K'・fp='FY'で年次候補に混入」パターンのみに絞り込み）
  により、FICO・CPRTに加え**LITE（FY2019）を新規発見**。対象は3銘柄に拡大。
  一方selling_and_marketing・depreciation_and_amortizationは同一ロジックだが
  実害0件、long_term_debt・rpoは貸借対照表の時点データ（point-in-time）で
  duration概念自体を持たないため構造的に対象外と確認（詳細は[[TAG-DEFS-UNIFY-1]]）。
- 修正: `_extract_values_merged()`に、同一end_date・同一exact_matchレベルで
  複数候補が競合した場合、期間日数（end-start）が365日に近い方を優先する
  tie-breakを追加（`annual_durations`辞書を新設）。end_dateが異なる場合の
  既存ロジック（最新end_date優先）は変更していない。
- 検証: 同日生成company_facts.jsonでの新旧比較（git stash）により、
  105銘柄中FICO/CPRT/LITEの3銘柄・revenueフィールドのみが変化し、
  selling_and_marketing/depreciation_and_amortizationは全銘柄で無変化
  （回帰なし）を確認。`update.py FICO CPRT LITE`→`audit.py`（3銘柄正常）→
  `pipeline.py --skip-risk FICO CPRT LITE`（3/3成功）→
  `report_consistency_check.py`（NG=0）→pytest 219 passed/2 known failed
  （新規5件`tests/test_parser_merge_duration.py`追加）で検証済み。
- 修正後の値: FICO FY2019=$1,160.1M/FY2020=$1,294.6M、
  CPRT FY2019=$2,042.0M/FY2020=$2,205.6M、LITE FY2019=$1,565.3M
  （いずれも正規の365日間年次値）。
- 副次的な影響: FICO・CPRTのTANUKI SCORE乖離率が是正された
  （FICO: +27.9%→-61.3%、CPRT: +58.0%→-14.2%。分類はいずれもWATCHで維持）。
  quarterly.py側（TTM系列）は現在の5年カットオフ窓に問題のFY2019/2020
  エントリが含まれないため実害なしと確認、修正不要と判断。
- 発見したLITE FY2021の低い revenue値（$419.5M、98日間の期間）は本バグとは
  無関係（LITEの会計年度末変更に伴う移行期間の正規の10-K提出とみられる、
  修正前から存在していた別要因）と確認、本タスクでは対応していない。

### ✅ [LLY-CAPEX-STALE-1] LLYのCapEx四半期データが2022年以降取得できず古い値を使い回し（2026-07-12完了・QUALITY-GATES-EPIC-1 Phase 2a）
**分類:** データ品質 / SECデータ取得層
**登録日:** 2026-07-12
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- 根本原因確定: LLYはCapEx主要タグ`PaymentsToAcquirePropertyPlantAndEquipment`を
  一度も申告しておらず、旧フォールバックタグ`PaymentsToAcquireProductiveAssets`も
  2022-09-30を最後に申告停止していた。2023年以降は新タグ
  `PaymentsToAcquireOtherPropertyPlantAndEquipment`に切替済みだったが、
  quarterly.py/parser.pyいずれの候補リストにも未登録だったため一切参照されていなかった。
- KLAC型（`_classify_period()`の期間分類ミス）とLLY型（タグ切替見逃し）が
  「候補タグ群の中で最初に条件を満たしたものを採用して打ち切る」という
  同一のフォールバック選定ロジックに起因すると判明したため、個別のタグ追加ではなく
  選定ロジック自体を「最小件数を満たす候補の中から最新end日が最も新しいものを
  採用する」方式へ転換（`quarterly.py::_select_best_candidate()`・
  `parser.py::_extract_values_best_candidate()`新設）。
- `common/sec_data/tag_definitions.py`を新設し、quarterly.py/parser.pyで独立管理
  されていたタグ候補リストのうち9概念（CapEx・FinanceLeasePmts・SBC・GrossProfit・
  NetIncome・Cash・RD・Buyback・OCF）を統合。LTDebt・SM・DA・RPO・Revenueは
  優先順位・候補集合が構造的に異なるため意図的に統合対象外とし
  [[TAG-DEFS-UNIFY-1]]として分離登録。
- 影響範囲確認（同日生成のcompany_facts.jsonで新旧ロジックを比較、raw/*.json生成日時差
  による見かけ上の差分を排除）: 105銘柄中LLY（CapEx: 4件→19件、最新end日
  2022-09-30→2026-03-31）とWMT（SBC: 0件→6件、副次的に発見）の2銘柄のみに影響が
  限定されることを確認。他103銘柄は無変化。
- 検証: `update.py LLY WMT`→`audit.py`→`pipeline.py --skip-risk LLY WMT`（2/2成功）→
  `report_consistency_check.py`（NG=0、既存WARN3件のみ）→pytest 214 passed/2 known failed
  （新規8件`tests/test_tag_fallback_selection.py`追加、既存2件のみ既知失敗）。
- LLY FY2025 CapEx: $7.84B（新タグ反映後）。WMT FY2026 SBC: $3.60B。

### ✅ [GROWTH-SOURCE-LABEL-1] segment_detail.sourceの誤表示バグ（2026-07-12完了）
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
- `calculator/growth.py::get_segment_growth()`が`segment_detail["source"]`に
  固定文字列`"segment_config"`をハードコードしていた箇所を、
  `config.get("source", "segment_config")`に修正（実際の出所を転記）。
  `segment_config.py::get_segment_growth()`側は既に`"growth_override"`
  （recommended_g自動注入時）/`"segment_config"`を正しく返していたが、
  呼び出し側でこの値を無視していたのが原因。
- 影響銘柄（`phase1_growth_auto_adjusted=True`、全て`segment_config`と
  誤表示されていた）58銘柄を特定し`pipeline.py --skip-risk`で再生成。
  再生成後は全58銘柄で`source=growth_override`に修正されたことを確認。
- 検証: pytest 204 passed/2 known failed（既知）、
  `report_consistency_check.py` NG=0/警告3件（全て確認済み）。
  再生成に伴うFCF系列等の微小な変動は本修正とは無関係な
  TTM系列の通常の日次データ更新によるもの（`growth.py`はFCF計算に関与しない）。

---

### ✅ [TTM-QUARTERS-CHECK-1] TTM系列構築時の四半期完全性チェック不足（2026-07-12完了）
**分類:** データ品質 / SECデータ取得層
**登録日:** 2026-07-11
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
案1（quarters_used>=4フィルタ）を実装。TTMReader.get_fcf_series()にOCF・CapEx
両方のquarters_used>=4フィルタ、get_periods()を同条件に統一、
build_rice_annual_shape()にOCF/CapEx/Revenue/NetIncomeの完全性フィルタを追加。

実装過程で当初想定になかった追加課題を2件発見・同一タスク内で解消：
- OCFとCapExのquarters_usedが食い違うケース（11銘柄）→両方チェックする設計に拡張
- CRWV/CONでTTM点数が年次データより少ないのに優先され計算全体が失敗する
  回帰を自己誘発 → `_select_fcf_source()`ヘルパー新設で対応
  （min_years=3以上ならTTM優先を維持、min_years未満かつ年次の方が多い場合のみ
  年次フォールバック。当初「TTM<年次なら常に年次優先」で実装した際に
  AAPL等95銘柄が意図せず年次へ後退する重大回帰を自己検証で発見・訂正済み）

105銘柄フルバッチ再生成完了（成功100/失敗0、CRWV/CON含む）。
pytest 194/196（test_iv_formula.py MSFT/NVDA既存2件は無関係の別問題、
[[TEST-IV-FORMULA-ALPHA-1]]として別登録）。report_consistency_check.py NG=0/WARN=3
（既知のみ）。コミット3件push済み（98066c642→ad8c6d127→54bacca72）。

NVDAの当初試算（-19.0%）は簡易計算であり、実際はOCF/CapEx食い違いにより
2022年・2023年双方に不完全期間が存在したため-37.5%（$47.97B→$76.82B）と
より大きい影響だったことが判明。

全銘柄集計結果（Classification変化14銘柄、fcf_outlier.detected変化13銘柄、
growth_sanity.verdict変化5銘柄、floor_hit変化1銘柄）は[[GROWTH-CAGR-SIGN-1]]
完了注記に記載。

副産物：LLY CapEx四半期取得バグ（[[LLY-CAPEX-STALE-1]]）、
test_iv_formula.py既存回帰（[[TEST-IV-FORMULA-ALPHA-1]]）を新規登録。

以下、本タスクのBACKLOG.md記載全文をアーカイブとして保存する。

---

**優先度:** 高
**発見:** [[GROWTH-CAGR-SIGN-1]]のMO/XOM IV急変動を一次データで追跡した過程

#### 問題
`TTMReader.get_fcf_series()`・`build_rice_annual_shape()`（いずれも
`data_fetcher.py`）が、TTM値採用時に各期間の`flow.OCF.quarters_used`/
`missing`フィールドを一切参照せず、`flow.FCF.val is not None`のみを
判定条件としている。この結果、本来4四半期分の集計が必要なTTM値のうち、
実際には1〜3四半期分しか揃っていない**不完全なTTM値**が、正常な
4四半期集計値と区別なく`fcf_list_raw`（および`fcf_5yr_avg`）に
混入している。

#### 影響範囲（全銘柄横断調査、2026-07-11実施）
- 全105銘柄中**101銘柄**で`quarters_used<4`のTTM期間が存在
- そのうち**94銘柄で実際に`fcf_list_raw`へ混入**していることを確認
  （`RKLB`のみFCF値自体がNoneのため偶然除外）
- 大半が**2022-03-31期前後**（新規上場銘柄はその上場時期に応じて後ろ倒し）
  の1期に集中。原因は共通で、**四半期粒度のSECデータ取得が2022年Q1前後
  から開始されており、それ以前は年次10-Kの通期集計値しか存在しない**ため、
  TTM系列の最古境界期で必要な4四半期のうち1〜2四半期分しか揃わない

#### 波及先（fcf_5yr_avg・fcf_list_raw経由で横断的に影響）
- `calculate_fcf_cagr()`（[[GROWTH-CAGR-SIGN-1]]）: 2点間CAGRの一端点として直接使用
- `adjust_fcf()`（Policy A revenue_floor判定）: `fcf_5yr_avg`が入力
- `determine_fcf_base()`（CV・FCFベース方式選択）: `fcf_5yr_avg`が候補値、CV計算にも同系列を使用
- `analyze_fcf_outlier()`（Policy A/B外れ値検知の分母）: `fcf_5yr_avg`の過小評価により
  乖離%が本来より大きく表示され、**誤検知（false positive）方向のバイアス**
- `build_rice_annual_shape()` → RICE計算にも同型の汚染が波及

#### 試算結果（4銘柄、汚染込み5yr平均 vs 除外後4yr平均）
| 銘柄 | 差分 | 実際のFCFベース方式 | fcf_outlier表示への影響 |
|---|---|---|---|
| MO | **-12.9%** | avg_5yr（直接使用） | 検知なし（変化なし） |
| XOM | **-13.7%** | recent_2yr（汚染値不使用、実害小） | 検知なし（変化なし） |
| NVDA | **-19.0%** | recent_2yr（実害小） | 検知あり（乖離148%表示、正しくは約101%） |
| AAPL | **-6.9%** | avg_5yr（直接使用） | 検知あり（乖離30%表示、正しくは約21%、成熟企業閾値20%に対し**境界線上**） |

AAPLの例が示す通り、94銘柄全体では「補正すると外れ値検知の判定自体が
反転する」境界線上のケースが他にも存在しうる。個別精査なしに軽微と
断定はできない。

#### 対応方針の選択肢
- **案1（推奨）**: `TTMReader.get_fcf_series()`・`build_rice_annual_shape()`に
  `quarters_used>=4`（または一定閾値以上）フィルタを追加し不完全期間を除外。
  低コスト（関数2箇所の修正のみ）。対象銘柄の実効ルックバックが5年→4年に
  短縮するが、`calculate_fcf_cagr`のmin_periods=2・`determine_fcf_base`の
  最低3年要件は満たすため実害小
- 案2: 不完全四半期を按分補完（非推奨。四半期の季節性を考慮すると単純な
  按分はかえって不正確な値を生むリスクが高い）
- 案3: 該当期間のSECデータを遡って再取得し真の4四半期分を揃える
  （高コスト。2021年以前の四半期粒度データがEDGARから取得可能か次第）

#### [[GROWTH-CAGR-SIGN-1]]・[[DCF-REL-SYNC-1]]・[[ARCH-DATA-1]]との関係
[[GROWTH-CAGR-SIGN-1]]の全銘柄再生成は本タスクの対応方針確定まで保留中。
[[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）が扱っていたfcf_outlier
系の信頼性問題とも間接的に関連する（分母の汚染が誤検知バイアスを生む）。

[[ARCH-DATA-1]]は「XBRLタグの型・非12月決算・SPAC等のSECデータ形の
不均一性」を主眼とするが、本件は「データの型ではなく、四半期充足数という
完全性チェックの欠如」という異なる性質の問題。案1はTTMReader周辺への
小さな修正で完結するため、**ARCH-DATA-1の大規模刷新を待たず独立タスクとして
先行対応することを推奨**する。

#### 着手条件
なし（次回セッションで対応方針確定の上、着手判断）

---

### ✅ [GROWTH-CAGR-SIGN-1] calculate_fcf_cagr()のCAGR計算式が符号反転していた（2026-07-12完了）
**分類:** バグ修正 / TANUKI VALUATION
**登録日:** 2026-07-11
**完了日:** 2026-07-12

#### 完了に至った経緯（要約）
[[TTM-QUARTERS-CHECK-1]]対応完了に伴い保留していた全銘柄再生成を実施。
CAGR符号修正とTTM完全性フィルタを同時反映。

MOは連鎖効果により、GROWTH-CAGR-SIGN-1単独適用時点の成長率+29.9%
（乖離+286.3%）から、TTM-QUARTERS-CHECK-1重畳後は再びfloor 15%
（FLOOR_HIT_REVIEW、乖離+34.9%）に戻った。+29.9%という値自体が
TTM-QUARTERS-CHECK-1で除外対象になった2022年の欠陥値（$3,030M）を
起点に計算されていたため。除去後の真の直近成長率は約2.7%であり、
floor張り付きが正しい結果。数値は奇しくも両修正前のオリジナル値
（+34.9%）とほぼ一致。

全銘柄集計結果（前回コミット時点比較）：
- **Classification変化（14銘柄）**: AMZN(TRIM→WATCH)、BKNG(WATCH→BUY)、
  BSY(WATCH→TRIM)、CDNS(WATCH→HOLD)、CON(WATCH→GROWTH_PREMIUM)、
  FCX(TRIM→WATCH)、KLAC(WATCH→TRIM)、MSCI(WATCH→HOLD)、NVDA(WATCH→BUY)、
  PEP(TRIM→WATCH)、TSLA(TRIM→WATCH)、V(WATCH→TRIM)、WST(WATCH→TRIM)、
  XOM(HOLD→WATCH)
- **fcf_outlier.detected変化（13銘柄）**: BKNG/BSY/CDNS/CON/KLAC/MSCI/NVDA/
  V/WST（True→False）、FCX/PEP/TSLA/XOM（False→True）
- **growth_sanity.verdict変化（5銘柄）**: ENTG/GEV/HQY（PLAUSIBLE→REVIEW）、
  HWM（PLAUSIBLE→AGGRESSIVE）、MO（PLAUSIBLE→FLOOR_HIT_REVIEW）
- **growth_sanity.floor_hit変化（1銘柄）**: MO（False→True）

XOMはClassification HOLD→WATCHに変化（fcf_outlier検知45%乖離・
一過性費用説明なしでPolicy Bが正しく発火。バグではなく5yr平均が
正確になったことで既存の外れ値が可視化された結果）。

以下、本タスクのBACKLOG.md記載全文をアーカイブとして保存する。

---

**優先度:** 高
**発見:** [[GROWTH-SANITY-CLASS-SYNC-1]]実装前調査時
**状態:** コード修正・単体テスト・MO/LOAR/XOM 3銘柄検証データともコミット済み。
**全銘柄再生成は[[TTM-QUARTERS-CHECK-1]]対応後まで保留**（下記参照）

#### 問題
`calculator/growth.py::calculate_fcf_cagr()`（95-146行目）のCAGR計算式で、
`start_value`/`end_value`の割り当てが本コードベース全体の`fcf_list`規約
（新しい順、`fcf_list[0]`が直近。`adjustments.py:897`のdocstring・
`adjustments.py:268-272`の別のCAGR計算で明示・実装されている規約）と逆向きになっており、
実際には成長している銘柄でも負のCAGRが算出される致命的なバグだった。
加えて`fcf_list[-5:]`という末尾スライスも、5年超のデータがある場合に
最古側5年を誤って対象にする副次的なバグだった（実データでは該当銘柄なし、
潜在バグとして合わせて修正）。

**実データ検証結果（バグ修正前後の比較）:**
| 銘柄 | 直近FCF | 最古FCF | 修正前（バグ） | 修正後（正しい向き） |
|---|---|---|---|---|
| NVDA（動作確認用） | $119,076M | $3,028M | -60.1% | **+150.4%**（cap 50%） |
| MO | $8,623M | $3,030M | -23.0%→floor 15% | **+29.9%**（クリップなし） |
| LOAR | $112M | $13M | -66.2%→floor 15% | **+196.0%**（cap 50%） |
| XOM | $18,792M | $10,877M | -12.8%→floor 15% | +14.6%→floor 15%（実質不変） |

`growth_source=="fcf_cagr"`となる銘柄は現行データでMO/LOAR/XOMの3件のみ
（全銘柄横断で確認、他に該当なし。segment_weighted等の他経路は本バグの影響を受けない）。

#### 修正内容
- `start_value`（chronological start＝最古）に`recent_fcfs[-1]`、
  `end_value`（chronological end＝直近）に`recent_fcfs[0]`を割り当てるよう修正
  （`raw_cagr = (end_value/start_value)**(1/periods)-1`という式自体は変更せず、
  どちらの変数がどちらの向きかを規約に合わせて訂正）
- `fcf_list[-5:]` → `fcf_list[:5]`（新しい順の先頭5年＝直近5年を対象にするよう修正）
- `calculate_fcf_cagr()`の単体テストを新規追加（5件、既存カバレッジ0件だった）:
  急成長（NVDA型）・floor/cap内に収まる中成長（MO型）・cap張り付き（LOAR型）・
  減少トレンドで正しく負のCAGRになること・5年超データで直近5年が正しく使われること
- pytest 136件全件パス（131→136、新規テスト5件純増）

#### 3銘柄個別確認結果（`pipeline.py MO LOAR XOM --skip-risk`実行）
- **MO**: 成長率15.0%→**29.9%**、`growth_sanity.verdict`が`FLOOR_HIT_REVIEW`→
  `PLAUSIBLE`に解消。Classification=BUY不変だが、**Intrinsic_Value_BASEが
  $96.87→$277.29、乖離率+34.9%→+286.3%へ大幅変動**
- **LOAR**: 成長率15.0%→**50.0%**（cap）、verdict`FLOOR_HIT_REVIEW`→`PLAUSIBLE`に解消。
  Classification=WATCH不変（既存のfcf_outlier flagged起因、本修正とは別要因）。
  IV $9.98→$56.95、乖離率-86.3%→-22.1%
- **XOM**: 成長率15.0%のまま実質不変（修正後の生値14.6%が floorにわずかに満たない
  ため）。verdict=FLOOR_HIT_REVIEW・Classification=HOLDともに不変

#### ⚠️ MOのIV急変動の根本原因を特定 → [[TTM-QUARTERS-CHECK-1]]として分離
MOのIV乖離率が+34.9%→+286.3%へ変動した要因を一次データで追跡した結果、
「2点間CAGRが外れ値に敏感」という設計論点にとどまらず、**最古年FCF（$3,030M）
自体がTTM系列構築時のデータ不足（本来4四半期必要なところ1四半期分しか
揃っていない：`quarters_used=1, missing=3`）による欠陥値である**ことが
判明した（一過性の訴訟和解金・減損等の事業要因ではないことも確認済み）。

この問題はMO固有ではなく、**全105銘柄中94銘柄で`fcf_list_raw`に同型の
不完全TTM値が混入**しているシステム全体の根本課題と判明したため、
[[TTM-QUARTERS-CHECK-1]]として分離・新規登録した（詳細は同エントリ参照）。

**本タスク（GROWTH-CAGR-SIGN-1）の符号修正自体は独立して正しく、そのまま
維持する。ただし全銘柄再生成は[[TTM-QUARTERS-CHECK-1]]の対応方針が
確定するまで保留する**（不完全な最古年データが混入したまま成長率を
再計算しても、MOのように歪んだ値が量産される可能性があるため）。

#### [[GROWTH-FLOOR-VERDICT-1]]・[[GROWTH-SANITY-CLASS-SYNC-1]]との関係
本バグ修正により、[[GROWTH-SANITY-CLASS-SYNC-1]]が問題視していた
「MO（BUY）がfloor張り付きのままBUY判定が変わらない」という最も緊急性の高い
実例が解消された（MO/LOARのfloor_hitが解消、残るXOMはHOLDのため実害限定的）。
詳細は[[GROWTH-SANITY-CLASS-SYNC-1]]エントリの状況更新を参照。

#### 進捗
コード修正（`growth.py`）・単体テスト5件・MO/LOAR/XOM 3銘柄検証データはコミット済み。
**全銘柄再生成は[[TTM-QUARTERS-CHECK-1]]対応後まで保留**。

---

## 2026-07-11（完了）

### ✅ [DCF-REL-SYNC-1] report.txtのDCF_Reliability判定にFCF乖離%が未反映（2026-07-11完了）
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**完了日:** 2026-07-11

#### 完了に至った経緯（要約）
FCF乖離%の`FCFOutlierResult.deviation_pct`への反映・report.txt表示は
2026-07-11同日3回目のセッションで実装完了（コミット`b5c91180d`）。
残っていた未決着点2件は以下の通り解消：
- **未決着点①（Policy Bの`excluded`分岐の扱い）**: 当初は構造的に到達不可能な
  デッドコードと判明し簡略化方針を確定していたが、②の修正でPolicy Bの呼び出し
  ゲートが変わった結果、副次的に到達可能になったことが再調査で判明
  （AMZN・COHRの2銘柄で実際にNORMAL判定を返し機能している）。
  簡略化方針は撤回し、現状維持（コード変更なし）に訂正してクローズ。
- **未決着点②（Policy A未カバー範囲、ENTG/RMBS等）**: 調査の結果、真に構造的な
  未カバー範囲（BKNG: BUY・乖離36%未説明、RBRK: 241%乖離）を新規発見し、
  [[POLICYB-GATE-FIX-1]]として分離・根本修正・全銘柄再生成まで完了（下記参照）。

以下、本タスクのBACKLOG.md記載全文をアーカイブとして保存する。

---

**優先度:** 高（2026-07-10・中から格上げ）
**発見:** サテライト投資候補91銘柄への前提妥当性チェック展開時
**状況更新（2026-07-11）:** 関連課題[[GROWTH-FLOOR-VERDICT-1]]は2026-07-11
コミット`8df1f1172`で完了（BACKLOG_DONE.md参照）。「信頼できない前提のBUYが
スクリーニングを素通りする」問題のうち、floor値張り付き検知の部分は解消済み。
本タスク（FCF乖離%の未反映）は引き続き未着手。

**状況更新（2026-07-11 同日2回目）:** 本タスクの実装前調査中に、既存の
Policy B判定ロジック自体のバグ（`transient_evidence.found`と`action=="excluded"`の
取り違え）を発見・分離して[[TANUKI-POLICYB-FIX-1]]（完了・BACKLOG_DONE.md参照）
として先行修正した。この修正により下記「Policy Aとの相互作用」節の例示銘柄
FLYW（215%乖離）は既にDCF_Reliability=LOW・Classification=WATCHへ是正済みであり、
影響を受けた30銘柄中27銘柄でTANUKI SCORE分類が変化している。ただし本タスク
本来の要求（`fcf_outlier`の乖離%を新たな閾値としてDCF_Reliability判定に
組み込む設計。既存のdetected/actionの真偽判定とは別軸）は引き続き未着手。
また`fcf_outlier`には乖離%を格納する専用の数値フィールドが存在せず、
`note`の日本語文字列内にのみ埋め込まれている（正規表現パースが必要）ことが
調査で判明しており、実装時は`FCFOutlierResult`への`deviation_pct`フィールド
追加も合わせて検討する。

**状況更新（2026-07-11 同日3回目・セッション最終）:**

**実装済み・コミット済み:**
- `FCFOutlierResult`に`deviation_pct`フィールドを追加（`note`文字列のパースではなく
  `analyze_fcf_outlier()`内の計算済み数値をそのまま格納。`rule="latest_negative"`型は
  概念が成立しないためNone）。report.txt生成時、Policy BでLOW判定の場合に
  `[DCF-REL-SYNC-1: FCF実績が5年平均から○○%乖離]`として表示に反映済み
- 当初`action=="excluded"`でも`deviation_pct>=200%`ならLOWに戻す安全弁を追加したが、
  実データ調査で対象母集団が0件（`action=="excluded"`となる銘柄は全て
  `fcf_estimation.applied=False`＝Policy A対象でPolicy B自体が発火しないと判明）
  だったため安全弁は削除し、`action=="excluded"`→NORMAL / `action=="flagged"`→LOWの
  シンプルな判定に確定（コミット`b5c91180d`）

**未決着（次回以降に判断、指示待ち）:**
1. ~~Policy Bの`excluded`分岐の扱い：現状データでは構造的に発火し得ないと判明済み
   （`estimate_fcf_from_eps`のガードAが`action=="excluded"`を`fcf_estimation.applied=False`
   に強制するため）。①将来`skip_guard_a`が機能した場合に備えたセーフティネットとして
   残置する ②実質デッドコードとして簡略化を検討する、の2択で保留中~~
   ✅ 2026-07-11 再調査によりクローズ（詳細は下記「状況更新（同日5回目）」参照）。
2. ~~Policy A未カバー範囲（ENTG/RMBS等、FCF_Base方式・floor未適用）への対応~~
   ✅ 2026-07-11 [[POLICYB-GATE-FIX-1]]（完了・BACKLOG_DONE.md参照）で解消。

**状況更新（2026-07-11 同日4回目）:** 上記「未決着」項目2（Policy A未カバー範囲）を
調査した結果、ENTG/RMBSは実際にはEPS Analyzerデータ未生成による一時的なstale状態
（applied=False）であり再生成のみで自動解消することが判明。一方で真に構造的に
Policy A/Bどちらからも判定されないケース（BKNG: FCF実績プラス・乖離36%未説明・
BUY分類のまま素通り、RBRK: 同241%乖離）を新規発見し、[[POLICYB-GATE-FIX-1]]として
分離・修正・全銘柄再生成まで完了した（詳細はBACKLOG_DONE.md参照）。
上記「未決着」項目1（Policy Bのexcluded分岐の扱い）は引き続き未着手。

**状況更新（2026-07-11 同日5回目）:** 上記「未決着」項目1（Policy Bの`excluded`分岐の
扱い）を[[POLICYB-GATE-FIX-1]]完了後の状態で再調査した結果、**前提が崩れていたことが
判明した**。当初（POLICYB-GATE-FIX-1着手前）はPolicy Bの呼び出しゲートが
`fcf_estimation.applied==True`のみだったため、Guard A（`action=="excluded"`なら
`applied=False`を強制）により`excluded`分岐は構造的に到達不可能と判明し、
「②デッドコードとして簡略化」の方針を確定していた。しかし[[POLICYB-GATE-FIX-1]]で
Policy Bの呼び出しゲートが`not _policy_a_fires`（`floor_applied>0 and not applied`の否定）
に変更された結果、`applied=False`かつ`floor_applied<=0`の場合もPolicy Bが評価される
ようになり、`excluded`分岐が副次的に到達可能になった。実データ確認では
**AMZN・COHRの2銘柄が実際にこの分岐に到達し、正しくNORMAL判定を返している**ことを
確認済み（`test_detected_true_explained_is_normal`・`test_eps_invalid_overrides_explained_true`の
2テストも、デッドコードのテストではなくこの実挙動を保証する現役テストと判明）。
そのため「②デッドコードとして簡略化」の方針は撤回し、**現状維持（コード変更なし）**に
訂正する。`excluded`分岐は「デッドコード」ではなく「AMZN/COHR型の実挙動を保証する
現役ロジック」として位置づける。

以上により、DCF-REL-SYNC-1の未決着点は**実質的に解消（残る未決着点なし）**となった。

**派生タスク（本日の調査過程で発見・分離登録）:**
- [[TANUKI-POLICYB-FIX-1]]（完了・BACKLOG_DONE.md参照）: Policy Bの
  `transient_found`/`action`取り違えバグ修正
- [[POLICYB-GATE-FIX-1]]（完了・BACKLOG_DONE.md参照）: Policy Bの
  `fcf_estimation.applied`ゲート漏れ修正（BKNG/RBRK型のFCF_Base方式未カバー範囲を解消）
- [[FCF-OUTLIER-QUAL-1]]（優先度未定・新規登録）: 一過性費用の説明妥当性の定性評価導入
- [[SECTOR-FCF-RATE-BROKEN-1]]（優先度中・新規登録）: FCF実力推定のsector取得経路破損
- [[GROWTH-SANITY-CLASS-SYNC-1]]（優先度高・新規登録）: growth_sanity.verdict
  （AGGRESSIVE/FLOOR_HIT_REVIEW）がDCF_Reliability/Classificationと未連動

#### 問題
`latest.json` の `fcf_outlier.note`（実績FCFの5年平均からの乖離%を含む注記、
例: FLYWで乖離215%）と、`report.txt` の `DCF_Reliability`（NORMAL/LOW表示ロジック）
が独立して存在し、相互参照されていない。この結果、FCF実績が5年平均から
大きく乖離している銘柄でもDCF_Reliability=NORMALのまま表示され、
乖離の大きさが伝わらないまま見過ごされるリスクがある。

#### 格上げ理由（2026-07-10）
本タスクと[[GROWTH-FLOOR-VERDICT-1]]（完了・BACKLOG_DONE.md参照）はいずれも
「信頼できない前提のBUYがスクリーニングを素通りする」直接原因であり、
スクリーニング運用の信頼性に直結するため優先度を高へ格上げする。

#### Policy Aとの相互作用（重要な影響範囲・実装時必須確認事項）
CLAUDE_CODE_START.md記載のPolicy A（DCF_Reliability=LOWの銘柄はTANUKI SCORE
分類をBUY/TRIM/HOLD→**WATCHに丸める**、SELL/PASSは維持）により、本タスクの
実装でFCF乖離の大きい銘柄（例: FLYW 215%乖離）がLOWに格下げされると、
**表示変更にとどまらずBUY分類自体がWATCHに丸められる**。これはスクリーニング
精度向上の観点では望ましい効果（乖離の大きいBUYの自動除外）だが、
分類挙動が変わる銘柄の事前リストアップと影響確認を実装時の必須手順とする
（Policy A明文化時に影響確認対象とされたCRWV/SOUN/RKLB/JOBY/CEG等、
既存の該当銘柄への影響も併せて再確認すること）。

#### common/screening/dcf_validity_checker.pyとの関係
Check C（SEC売上ジャンプ検知）はSEC売上高のみが対象でFCF異常ジャンプは
対象外という制約があるが、本タスクの実装によりlatest.json側の`fcf_outlier`
判定がDCF_Reliabilityに反映されるようになれば、report.txt経由でFCF異常も
実質的に可視化されるため、この制約は実質的に解消される。

#### 対応方針
report.txt生成時に `fcf_outlier` の乖離%を閾値判定に組み込み、
一定以上の乖離があればDCF_Reliabilityを自動的にLOWへ格下げする。
既存のDCF_Reliability判定条件（FCF_Conversion_Rate方式・revenue_floor適用等）
との優先順位・閾値設計、およびPolicy A発動によるTANUKI SCORE分類変更の
影響確認を含め、実装は別タスクとして着手する。

---

### ✅ [POLICYB-GATE-FIX-1] Policy Bのfcf_estimation.appliedゲート漏れ修正（2026-07-11完了）
**分類:** バグ修正 / TANUKI VALUATION
**発見:** [[DCF-REL-SYNC-1]]「Policy A未カバー範囲」調査中（事前BACKLOG登録なし・発見即修正のケース）

#### 背景・ゲート条件の経緯
`pipeline.py::_compute_tanuki_score()`のPolicy B丸め（DCF-RELIABILITY-1、
コミット`5b0ee587c`、2026-06-23導入）は当初から`fcf_estimation.applied`を
ゲート条件としており、これは「Policy A（revenue_floor適用＝FCF_Base直接方式向け）
とfcf_estimation.appliedの真偽で排他的」という意図的な設計だった。
ただしこの設計は「applied=FalseならPolicy Aのfloorチェックだけで十分」という
前提に依っており、FCF実績プラス・floor未発火のまま外れ値が未説明で残る
ケースを想定していなかった。

#### 問題
[[DCF-REL-SYNC-1]]の残課題「Policy A未カバー範囲（ENTG/RMBS等）」の調査で、
ENTG/RMBSは実際にはEPS Analyzerデータ未生成による一時的なstale状態
（`fcf_estimation.applied=False`、再生成のみで解消）と判明する一方、
真に構造的な未カバー範囲として以下2銘柄を新規発見した：
- **BKNG**（Classification: BUY、FCF実績$9033M・5年平均$6655Mから**36%乖離**・
  `fcf_outlier.action="flagged"`＝一過性費用で未説明）
- **RBRK**（Classification: WATCH、同**241%乖離**・未説明）

いずれも`fcf_estimation.applied=False`（BKNG: EPSデータなし、RBRK: 調整済み
純利益マイナス）かつ`fcf_floor_applied=0`（FCF実績自体はプラス）のため、
Policy A（floor>0が発火条件）・Policy B（applied=Trueが発火条件）の
どちらのゲートにも該当せず、DCF_Reliability=HIGH誤表示のままスクリーニングを
素通りしていた。`_calc_dcf_reliability_policy_b()`自体は`applied`を参照しない
（`fcf_outlier`のみで判定）ため、呼び出し側のゲート条件のみが問題だった。

#### 追加発見（回帰）: floor_applied>0とapplied=Trueの共存ケース
初回修正案（ゲートを`fcf_floor_applied<=0`に置換）を全銘柄でシミュレーション
検証したところ、**BROS/CEG/SOFI/SPIRの4銘柄で新たな回帰**を発見した。
`core_calculator.py:249-250`の確認により、`fcf_floor_applied`は
`fcf_estimation.applied`の真偽に関わらず計算される値（raw fcfに対して先に
floor判定→その後applied=Trueならconversion-rate推定値に差し替え、floor値は
使われない）と判明。単純に`floor_applied<=0`でゲートすると、この4銘柄で
「実際のDCFに使われていないrevenue_floorのメッセージ」がPolicy Bの正しい
判定を上書きしてしまうところだった。

#### 修正内容
`pipeline.py`のPolicy A/Bゲートを以下に修正:
- Policy A発火条件: `_floor_applied > 0 and not _fcf_estimation.get("applied")`
  （floor値が実際にDCFで使われるケースに限定）
- Policy B発火条件: `not _policy_a_fires`（Policy A発火時はメッセージを
  上書きしない。Policy A非発火なら`_calc_dcf_reliability_policy_b()`で判定）
- Policy B発火時のコメント文言を`fcf_estimation.applied`の真偽で分岐
  （applied=True: 「FCF_Conversion_Rate方式」/ applied=False: 「FCF_Base方式」、
  raw_fcf方式の銘柄に誤ったコメントが付かないようにする）
- report.txt生成側（`_generate_report`内、`applied=False`かつfloor未発火の分岐）
  にも同型のPolicy B評価を追加（スコア側だけ修正すると
  「Classification=WATCHなのにreport.txtはHIGH」という表示矛盾が生じるため）
- `tests/test_pipeline_logic.py`に回帰テスト3件追加（BKNG/RBRK型が正しくWATCH化
  すること、floor既発火11銘柄でコメントが上書きされないこと、
  BROS/CEG/SOFI/SPIR型でPolicy Bが正しく評価されること）

#### 検証結果
- 全銘柄（tanuki=true 100銘柄、RKLB/ZSはtanuki=false化済みのため対象外）で
  pipeline.py再生成を実施。実質的な分類変化はBKNG（BUY→WATCH）・
  RBRK（DCF_Reliability表示のみHIGH→LOW、Classification=WATCH自体は不変）の
  2銘柄のみ。floor既発火11銘柄（ASTS/CRWV/IONQ/JOBY/ONDS/QBTS/RCAT/RKLB/
  RXRX/SOUN/S）・BROS/CEG/SOFI/SPIR（floor+applied=True共存型）とも
  想定外の副作用なしを実データで確認済み
- pytest 131件全件パス（128→131、回帰テスト3件純増）
- `report_consistency_check.py`: NG=0（WARN 4件はELF PS異常値・
  LOAR/MO/XOM FLOOR_HIT_REVIEWのみで、いずれも既知・無関係）

#### 関連
- [[DCF-REL-SYNC-1]]の「Policy A未カバー範囲」課題を実質的に解消（詳細は
  BACKLOG.md該当エントリの状況更新参照）
- 横断調査で新たに[[GROWTH-SANITY-CLASS-SYNC-1]]（`growth_sanity.verdict`が
  DCF_Reliability/Classificationと未連動、MO/LOAR/XOMのFLOOR_HIT_REVIEW）を
  優先度：高でBACKLOG.mdに新規登録

---

### ✅ [TANUKI-POLICYB-FIX-1] Policy B DCF_Reliability判定のtransient_found/action取り違え修正（2026-07-11完了）
**分類:** バグ修正 / TANUKI VALUATION
**発見:** [[DCF-REL-SYNC-1]]の実装前調査中（事前BACKLOG登録なし・発見即修正のケース）

#### 問題
`pipeline.py::_calc_dcf_reliability_policy_b()`（DCF_Reliability Policy B、
FCF_Conversion_Rate方式向け）が、`fcf_outlier.transient_evidence.found`
（一過性費用の証拠項目が1件でも"存在するか"の真偽値）を判定に使っていたが、
本来使うべきは`fcf_outlier.action == "excluded"`（`analyze_fcf_outlier()`が
その証拠の金額が乖離を"説明しきれているか"まで判定した結果）だった。
証拠は少額存在するが金額不足（`action="flagged"`）のケースでも`found=True`
となるため誤ってNORMAL判定され、DCF信頼性が低いにも関わらずTANUKI SCORE
のWATCH丸めが発火しなかった。
（例: FLYW FY2025、5年平均から215%乖離、一過性費用$11M<必要説明額の20%）

#### 修正内容
- `transient_found`判定を`fcf_outlier.get("action") == "excluded"`に置換
- `tests/test_pipeline_logic.py`のテストケースを新仕様に更新、回帰防止用に
  `test_detected_true_flagged_with_partial_evidence_is_low`（FLYW型ケース）を追加
- 影響を受けた30銘柄（ADSK/AMD/APP/BSY/CDNS/CEG/CELH/CPRT/CRM/CWAN/DDOG/DOCN/
  ESTC/FICO/FLYW/FRSH/GEV/HQY/INTU/IOT/LITE/MRVL/MSCI/NET/SNPS/SOFI/VRT/WST/
  ZETA/ZS）のlatest.json/report.txt/history.json/score_history.jsonを再生成

#### 影響（TANUKI SCORE分類変化）
30銘柄中27銘柄で分類変化（BUY→WATCH 10件、TRIM→WATCH 10件、HOLD→WATCH 7件、
変化なし3件）。SELL/PASSは維持ルールのため対象外。

#### 副作用確認結果
- **LOW→NORMALへの逆転ケース: なし。** `analyze_fcf_outlier()`の実装上
  `action=="excluded"`は常に`transient_evidence.found==True`を要求するため
  （数学的に旧LOW判定銘柄が新ロジックでNORMALに変わることはない）、
  tanuki=true全100銘柄の実データでも該当0件を確認。
- `action`フィールドの取り得る値は`{"excluded","flagged","none"}`の3値のみ、
  `detected=True`かつ`action=="none"`という分岐漏れ懸念ケースも全銘柄で0件。
- 再生成後のWARN 18件は全て`pt_shares_consistency`チェック起因で、
  [[TEST-STALE-IV-1]]（ALPHA-REDESIGN-1後に旧α乗算式のまま陳腐化した既知問題）
  に該当し、修正前から存在した無関係の既存事象と確認済み（ADSK/AMD/CEGで
  HEAD時点=修正前でも同一WARNを確認）。

#### DCF-REL-SYNC-1との関係
本タスクはPolicy Bの既存判定ロジックの取り違えバグであり、
[[DCF-REL-SYNC-1]]本来の要求（`fcf_outlier`の乖離%を新たな閾値として
DCF_Reliability判定に組み込む設計）とは別物。DCF-REL-SYNC-1は引き続き
未着手のままBACKLOG.mdに残置する。

---

### ✅ [GROWTH-FLOOR-VERDICT-1] 成長率floor値張り付きの検知不足（2026-07-11完了・コミット`8df1f1172`）
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**発見:** サテライト投資候補91銘柄への前提妥当性チェック展開時

#### 問題
`growth_source=fcf_cagr` で `calculate_fcf_cagr()` の `growth_floor`（15%）に
成長率が完全一致した場合、実態（実績成長率）との乖離があっても
`growth_sanity` の `Verdict` が機械的に `PLAUSIBLE` になる。
2026-07-10の調査ではMO（実績FCF CAGR約2.4%・売上マイナス成長にも関わらず
15%floor採用でPLAUSIBLE判定）に加え、LOAR・XOMでも同型のfloor張り付きを検出した
（fcf_cagrソースを使う3銘柄が全てfloor値に一致するという100%的中率だった）。

#### 格上げ理由（2026-07-10）
以下2点が判明したため、単なる検知不足ではなく既存の恒久対策の穴と判断し格上げした：

a) **修正済みバグ（DCF-DEFAULT-G-1）の回帰・再発の疑い**：
   MOは[[DCF-DEFAULT-G-1]]（2026-06-15完了、BACKLOG_DONE.md参照）で
   「G=15%デフォルト問題」を名指しで修正されたはずの銘柄（JNJ/MO/PEP/PM/
   WMT/VZ等）だが、2026-07-10時点でfcf_cagr経路のfloor値15%を再び採用している。
   MOのhistory.json（2026-06-14以降）を確認したところ、`growth_rate`は
   記録が残る全期間（2026-06-14〜2026-07-11）を通じて一貫して0.15のままで、
   DCF-DEFAULT-G-1修正日（2026-06-15）の前後で変化していない。
   コードを読む限り、DCF-DEFAULT-G-1は「segment未設定銘柄でも
   `_GROWTH_OVERRIDES`を有効にする」修正（`get_segment_growth`が
   `_GROWTH_OVERRIDES`を優先参照するよう変更）だが、この`_GROWTH_OVERRIDES`
   自体は`recommended_g`が算出できた場合にのみ`pipeline.py`側でセットされる
   （`if _is_seg_unconfigured and _recommended_g is not None:`の条件下でのみ
   `set_growth_override`が呼ばれる）。MOはrev_cagr_3yr/5yrが共にマイナスで
   `recommended_g`の中央値候補から除外されるため`recommended_g`自体がNoneになり、
   overrideが一度もセットされないまま`determine_growth_rate()`が
   segment/override経路を素通りしてfcf_cagr経路（独自のfloor=15%を持つ、
   DCF-DEFAULT-G-1の修正対象外の別経路）に落ちていると推測されていた。

b) **CHECK-18の構造的な穴**：
   `report_consistency_check.py`のCHECK-18（DCF-DEFAULT-G-1回帰検知）は
   「recommended_gあり & phase1_growth_auto_adjusted=False & source≠segment_weighted
   & rate≈15%」が発火条件のため、**recommended_g自体がNoneになるMO型のケースを
   構造的に検知できない**という構造的な穴が指摘されていた。

#### 実装着手前調査（2026-07-11）
上記a)・b)の推測をコード読解・実データ両面で検証し、**いずれも正しいことを確定**した：
- `growth_sanity.py`の`recommended_g`算出ロジック（候補>0のみ採用・中央値に2件必要）を
  読解し、rev_cagr_3yr/5yr両方マイナスのMO、CAGRデータ欠落のLOAR、3yrのみマイナスで
  候補1件のXOMがいずれも`recommended_g=None`になることを実データで確認
- git log調査でDCF-DEFAULT-G-1（コミット`3fdca1c6f`、2026-06-15）のdiffを確認した結果、
  同コミットは`segment_config.py::get_segment_growth()`の**下流消費ゲート**
  （overrideをsegment_config.json未設定銘柄にも適用する変更）のみを修正しており、
  `pipeline.py`の`if _is_seg_unconfigured and _recommended_g is not None:`という
  **上流生成ゲート**（`recommended_g`がそもそも算出できるか）は2026-05-30の
  コミット`4849f14331`（recommended_g機能の初回実装）から一度も変更されていないことを確認。
  → **「同じバグの再発（regression）」ではなく「隣接する別経路が最初から未カバーだった」**
  というa)の推測が確定
- CHECK-18（`latest.get("recommended_g") is not None`が発火条件）が`recommended_g=None`の
  ケースを構造的に検知できないことをコード上で確認、b)の推測も確定

#### 実装内容（コミット`8df1f1172`）
1. `growth_sanity.py`: `growth_source=fcf_cagr` かつ `recommended_g=None`
   （override発火せず）かつ `rate≈floor(15%)`の場合、`verdict=FLOOR_HIT_REVIEW`・
   新規フィールド`floor_hit=True`を出力するよう修正。
   `recommended_g=None`を条件に含めた理由: 本関数はoverride適用**前**に呼ばれるため、
   JNJ/PEP/PM/WMT/VZ等のoverride成功銘柄も適用前は軒並みfcf_cagr floor(15%)だったことが
   実測で判明しており、単純に`growth_source==fcf_cagr`のみで判定すると誤検知するため
2. `report_consistency_check.py`: **CHECK-20**新設。`growth_source=fcf_cagr` かつ
   `rate≈floor(15%)`を`recommended_g`の有無を問わず機械検知（`latest.json`の
   最終確定値を見るため、override成功銘柄はsourceが`segment_weighted`に
   変わっており誤検知しない）。CHECK-18のロジックは無変更
3. 実装着手前にMOのgrowth_source切り替わりの経緯をgit logで確認済み（上記参照）

#### 検証結果
- MO/LOAR/XOMの3銘柄で`verdict=FLOOR_HIT_REVIEW`・`floor_hit=True`・CHECK-20発火を実測確認
- JNJ/PEP/PM/WMT/VZの5銘柄で誤検知なし（`floor_hit=False`、CHECK-20非発火）を実測確認
- pytest 124件全通過（`test_iv_formula.py`のNVDA/MSFT失敗は[[TEST-STALE-IV-1]]起因の
  既知・無関係の失敗、本修正前から存在）
- 全106銘柄調査の結果、`growth_source=fcf_cagr`の銘柄は現状LOAR/MO/XOMの3件のみで、
  いずれも今回のデータ再生成に含まれるため、追加の再生成が必要な残銘柄は現時点でゼロ。
  今後の決算更新で新たにfcf_cagr経路に落ちる銘柄が出た場合はCHECK-20が継続的に検知する設計

---

### ✅ [CIK-ORPHAN-FLAGS-1（BX分）] BX(Blackstone Inc.)登録抹消（2026-07-11完了）
**発見:** [[CIK-ORPHAN-FLAGS-1]]で報告された全フラグfalseの孤立エントリ（BX・ENBの2件）のうちBX分
**コミット:** `8dde36fdc`

#### 内容
BXは`registration_note`に「列追加時点(2026-07-02)での遡及登録のため経緯不明」と
記載されたまま、status=active・stonks_silo/tanuki/eps/hypecoreの4フラグ全てfalseで
放置されていた孤立エントリ。[[CIK-ORPHAN-FLAGS-1]]で検討したA案（登録抹消）/B案
（適切な評価軸への振り分け、TANUKI-FIN-1着手時に判断）のうち、登録経緯不明のまま
放置され続けていたためKoichiさんの判断でA案（登録抹消）を採用し完全削除した。

削除範囲（cik_lookup.csv 1行＋関連データ73件）:
- `config/cik_lookup.csv` からBX行を削除
- `common/sec_data/data/BX/`（annual 19年分・quarterly約51四半期分・company_facts.json）
- `common/sec_data/normalized/BX_quarterly_normalized.json`
- `common/sec_data/raw/BX_quarterly_raw.json`
- `common/sec_data/ttm/BX_ttm_series.json`
- `docs/value-monitor/adjusted_eps_analyzer/data/BX/`（[[EPS-BX-1]]でeps=false化後も
  未削除のまま残存していたデータ）

事前調査でmonitor_tickers.yaml・discover_config.json等の銘柄リスト系ファイルには
BX参照が元々なかったことを確認済み（削除前に孤立状態だったため）。
`docs/market-monitor/market-pulse/data/sp500_tickers.json`のBX記載はMarket Pulse
独立システムの実際のS&P500構成銘柄スナップショットのため対象外（削除不要）と判断。

#### 検証結果
- `registration_validator.py`実行: BX関連のNG/WARN 0件、対象銘柄数106→105
- pytest 124件全通過
- `git status`: cik_lookup.csv 1行削除＋BX関連ファイル73件削除のみで意図した範囲と一致

---

### ✅ [TICKER-SOURCE-UNIFY-1] 銘柄リスト正本参照の一元化（根本課題）（2026-07-11 対応方針1・2・3すべて完了・BACKLOG.mdから完全移動）
**分類:** アーキテクチャ / 銘柄リスト参照
**登録日:** 2026-07-11
**発見:** [[REGISTER-FLOW-REDESIGN-1]]で判明したregistration_validator.pyの
盲点（monitor_tickers.yamlを全銘柄と取り違え）を起点に、同型バグの横断調査を実施

#### 背景
`config/cik_lookup.csv`（106件・正本）と`config/monitor_tickers.yaml`
（105件・サブセット、手動同期）を、リポジトリ内の各処理がどちらから
対象銘柄を取得しているかを全件横断調査した結果、**確定した同型バグが2件**、
および**既に統一ユーティリティが存在するが未活用**という根本原因が判明した。

#### 確定した同型バグ（2件・「全銘柄が対象のはずがサブセットを参照」）
1. **`src/value/adjusted_eps_analyzer/pipeline.py::run()`**
   （ticker_filter未指定時のデフォルトバッチ実行）が`monitor_tickers.yaml`を
   直接読み取り、cik_lookup.csvの`eps=true`フラグを参照していない
2. **`common/sec_data/registration_validator.py::run()`**のP1系チェック
   （7ステップ登録完全性）が、デフォルト実行（引数なし）時の走査対象を
   `monitor_tickers.yaml`から取得している（`tickers_to_check = target_tickers
   if target_tickers else monitor_tickers`）。[[REGISTER-FLOW-REDESIGN-1]]の
   根本原因

#### 根本原因: 統一ユーティリティは存在するが不採用
`common/sec_data/tickers.py`（2026-05-20 HypeCore全銘柄展開時に新設）は、
モジュールdocstringに明記された責務が「config/cik_lookup.csv から銘柄リストを
取得する共通ユーティリティ。**各サブシステムの--allオプションはこのモジュールを
使う**」であり、`get_tanuki_tickers()`/`get_eps_tickers()`/`get_stonks_silo_tickers()`/
`get_hypecore_tickers()`という各フラグ専用の取得関数まで用意されている。

しかし実際に採用しているのは`src/discover/catalyst.py`（`get_hypecore_tickers()`
経由）**1箇所のみ**。上記2件のバグを含め、他の全ての呼び出し箇所
（`tanuki_valuation/pipeline.py`・`discover/stonks-silo/src/pipeline.py`・
`hypecore.py`・`adjusted_eps_analyzer/pipeline.py`・`registration_validator.py`等）は
各々が独自に`csv.DictReader`でcik_lookup.csvを読み直すか、無関係な
`monitor_tickers.yaml`を参照しており、既存の統一ユーティリティへ収束していない。
**「正本一元化のためのインフラは既に存在するが、後から書かれたコードが
それを使わず車輪の再発明・別ソース参照を繰り返した」ことが根本原因**であり、
新規に共通関数を作る必要はなく、既存呼び出し箇所の移行が本質的な対応となる。

**訂正（2026-07-11・対応方針3着手時の追加調査）:** 上記「1箇所のみ」との記述は
不正確だった。`hypecore.py`も既に`get_hypecore_tickers()`を使用済み
（`from tickers import get_hypecore_tickers`という素のモジュール名importで、
`from common.sec_data.tickers import ...`とは異なるimport方式のため見落とされていた）。
正しくは「2箇所」。hypecore.py自体への追加修正は不要（import方式の流儀統一は任意）。

#### 参考: 一元化されていなくても問題ない箇所（正しい設計）
以下は`cik_lookup.csv`を直接読むが、対象が単一ティッカーのCIK参照のみ
（バッチ選定ロジックではない）ため問題なし: TANUKI TAIL系
（kpi_proposer.py/sec_ctrl_fetcher.py/text_kpi_extractor.py、`--ticker`必須）・
extract_key_facts.py・tanuki_valuation/data_fetcher.py（インサイダー取引CIK参照）。
`common/system_health.py`の`check_i_eps()`はcik_lookup.csvの`eps=true`と
`summary.json`収録銘柄を直接比較しており、この一元化問題とは無関係に
正しい設計（後述の検証強制力の評価も参照）。

#### 検出済みだが見落とされていた点（REGISTER-FLOW-REDESIGN-1の補足）
`common/system_health.py`の`check_i_eps()`は`.github/workflows/System_Health.yml`
により**毎日JST 8:30に自動実行されDiscordへ投稿**されており、2026-07-09の
半導体5銘柄登録以降、EPS Analyzerデータ欠損（今回の6件同期漏れの一部）を
検出したWARNが日次で投稿され続けていたはずである。つまり検出手段は
`registration_validator.py`のP4-CIKOrphan（WARN）に加えてもう1つ、既に
自動化された日次アラートとして存在していたが、いずれも実際のアクションに
つながらなかった。「検出の欠如」ではなく「WARN/非ブロッキングアラートが
運用上アクションされない」という、より根深い問題であることを示している。

#### 対応方針（診断のみ・実装は別タスク）
1. ✅ `adjusted_eps_analyzer/pipeline.py::run()`を`tickers.py`の
   `get_eps_tickers()`を使うよう修正（確定バグ1の解消）
   → **2026-07-11 コミット`ba2cfef42`で完了**
2. ✅ `registration_validator.py`のデフォルト実行時の走査対象を
   `tickers.py`の`get_all_tickers()`（cik_lookup.csv全銘柄）に変更
   （確定バグ2の解消、[[REGISTER-FLOW-REDESIGN-1]]対応方針1と同一の修正）
   → **2026-07-11 コミット`ba2cfef42`で完了**
3. ✅ 上記2件の移行を機に、他の呼び出し箇所（tanuki_valuation/pipeline.py・
   stonks-silo/pipeline.py・common/screening/dcf_validity_checker.py・
   common/screening/report_txt_parser.pyの計4ファイル）も`tickers.py`経由へ
   統一し、以後の新規コードが「各サブシステムの--allオプションはこのモジュールを
   使う」という原設計意図に自然に従うようにする
   → **2026-07-11 コミット`b41b447d6`で完了**。`hypecore.py`は横断調査の結果
   既に移行済みと判明したため対応不要（上記「訂正」参照）。残る
   `common/system_health.py`（check_h_config）は比較専用のため移行候補基準に
   非該当、低リスクな参考事項として残置（[[TICKER-SOURCE-CONFIG-DUP-1]]と
   あわせて任意対応）
4. WARN/非ブロッキングアラートが運用上見落とされる問題自体は
   [[REGISTER-FLOW-REDESIGN-1]]側の対応方針（P4のNG格上げ等）で扱う

#### 検証結果（2026-07-11・対応方針1・2完了時）
- pytest 124件全通過
- eps対象銘柄リスト新旧完全一致（monitor_tickers.yaml経由 vs
  get_eps_tickers()経由、共に101件・差分0件）
- `registration_validator.py`実行比較（修正前後）: 新規発火は`BX`1件のみ
  （全フラグfalseの孤立エントリ、[[CIK-ORPHAN-FLAGS-1]]の既知対象で
  本修正のスコープ外。従来`monitor_tickers.yaml`未登録のため走査対象外で
  不可視だったが、確定バグ2の修正によりP1系NGとして初めて検出されるように
  なった）

#### 検証結果（2026-07-11・対応方針3完了時）
- pytest 124件全通過
- TANUKI対象銘柄リスト新旧完全一致（旧ロジック vs get_tanuki_tickers()経由、
  共に100件・差分0件・順序も一致、skippedリストも`APGE/BX/ENB/RKLB/SN/ZS`で一致）
- STONKS SILO対象銘柄リスト新旧完全一致（旧ロジック vs
  get_stonks_silo_tickers()経由、共に25件・差分0件）
- `common/screening/dcf_validity_checker.py`・`report_txt_parser.py`は
  単一ティッカー・引数なし（全銘柄バッチ）の両モードで実行しエラーなしを確認

#### 優先度・着手順についての所感
確定した2件のバグはいずれも「既存関数を呼ぶだけ」で直せる低コスト・低リスクな
修正であり、[[REGISTER-FLOW-REDESIGN-1]]が提案する対応方針の中で
最も費用対効果が高い。着手する場合は、根本課題である本タスクの1・2を
先に解消してから、REGISTER-FLOW-REDESIGN-1の残り（原子性・status列拡張等、
コストの高い対応）に進むことを推奨する。

---

### ✅ [TICKER-SOURCE-UNIFY-1（対応方針3）] 残る呼び出し箇所4件をtickers.py経由へ統一（2026-07-11完了）
**発見:** [[TICKER-SOURCE-UNIFY-1]]対応方針1・2完了後の横断調査（対応方針3の対象洗い出し）
**コミット:** `b41b447d6`

#### 内容
対応方針1・2（`ba2cfef42`）に続き、独自にcik_lookup.csvを読んでいた残り4ファイルを
`common/sec_data/tickers.py`経由に移行：
- `src/value/tanuki_valuation/pipeline.py::_load_tickers_from_csv()`:
  `get_tanuki_tickers()`経由に変更（列欠損時のデフォルト挙動差異をコメントで明記）
- `discover/stonks-silo/src/pipeline.py::stonks_tickers()`:
  `get_stonks_silo_tickers()`へ委譲する1行に簡素化（不要になった定数`_CIK_LOOKUP`・
  `import csv`を削除）
- `common/screening/dcf_validity_checker.py::_all_tanuki_tickers()`:
  `get_tanuki_tickers()`に置換
- `common/screening/report_txt_parser.py::_all_tickers_with_report()`:
  `get_all_tickers()`に置換（report.txt存在フィルタは維持）

横断調査の過程で、対応方針3が当初想定していた`hypecore.py`は**既に
`get_hypecore_tickers()`使用済み**（素のモジュール名importのため見落とされていた）
と判明し、BACKLOG.mdの誤記述（「採用1箇所のみ」）を訂正した。

対応方針1・2・3が完了し、TICKER-SOURCE-UNIFY-1の残作業はなくなったが、
エントリの完全クローズ（本ファイルへの全文移動）はKoichiさんの判断待ちのため
BACKLOG.mdに残置している。新規発見の`common/sec_data/config.py`重複ユーティリティ
問題は[[TICKER-SOURCE-CONFIG-DUP-1]]として別途登録した。

#### 検証結果
- pytest 124件全通過
- TANUKI対象銘柄リスト新旧完全一致（旧ロジック vs get_tanuki_tickers()経由、
  共に100件・差分0件・順序も一致）
- STONKS SILO対象銘柄リスト新旧完全一致（旧ロジック vs
  get_stonks_silo_tickers()経由、共に25件・差分0件）
- `dcf_validity_checker.py`・`report_txt_parser.py`は単一ティッカー・
  引数なし（全銘柄バッチ）の両モードで実行しエラーなしを確認

---

### ✅ [TICKER-SOURCE-UNIFY-1（対応方針1・2）] 銘柄リスト取得元をcik_lookup.csvへ統一（2026-07-11完了）
**発見:** [[REGISTER-FLOW-REDESIGN-1]]診断を起点にした銘柄リスト参照の横断調査
**コミット:** `ba2cfef42`

#### 内容
確定した同型バグ2件を、既存の統一ユーティリティ`common/sec_data/tickers.py`を
呼ぶだけの修正で解消：
- `adjusted_eps_analyzer/pipeline.py::run()`: `ticker_filter`未指定時の
  デフォルト対象銘柄を`monitor_tickers.yaml`直読みから`tickers.get_eps_tickers()`に変更
- `registration_validator.py::run()`: `tickers_to_check`のデフォルト値を
  `monitor_tickers`から`tickers.get_all_tickers()`（cik_lookup.csv全銘柄）に変更
  （[[REGISTER-FLOW-REDESIGN-1]]対応方針1と同一の修正）

新規ロジックの追加は行わず、既存関数の呼び出し先を切り替えたのみ。
対応方針3（tanuki pipeline.py・stonks-silo pipeline.py・hypecore.py等、
他の呼び出し箇所のtickers.py経由統一）は任意の追加対応として
[[TICKER-SOURCE-UNIFY-1]]にBACKLOG.md残置（完全クローズは対応方針3
完了後）。

#### 検証結果
- pytest 124件全通過
- eps対象銘柄リスト新旧完全一致（monitor_tickers.yaml経由 vs
  get_eps_tickers()経由、共に101件・差分0件）
- `registration_validator.py`実行比較（git stashで修正前後を切り替えて実測）:
  新規発火は`BX`1件のみ（全フラグfalseの孤立エントリ、[[CIK-ORPHAN-FLAGS-1]]の
  既知対象で本修正のスコープ外。従来`monitor_tickers.yaml`未登録のため
  走査対象外で不可視だったが、確定バグ2の修正によりP1系NGとして
  初めて検出されるようになった）

---

### ✅ [MONITOR-SYNC-FIX-1] monitor_tickers.yaml同期漏れ6件の修正（2026-07-11完了）
**発見:** SYSTEM_MAP.md実態調査（2026-07-10）でcik_lookup.csv（106件）と
monitor_tickers.yaml（99件）の6件差分が判明

#### 内容
APGE/RMBS/ENTG/TER/KLAC/LRCXの6銘柄（いずれもeps=true、登録手順Step 7の
実施漏れ）をconfig/monitor_tickers.yamlへ追加。registration_validator.pyで
P1-Step7-Monitor NGが6件とも解消したことを確認（BXのみ全フラグfalseで
除外が正当なため対象外のまま）。pytest 124件パス確認済み。
根本原因の診断・再発防止策は[[TICKER-AUDIT-1]]・[[REGISTER-FLOW-REDESIGN-1]]・
[[TICKER-SOURCE-UNIFY-1]]としてBACKLOG登録済み（本エントリは実データ修正の
完了記録のみ）。

---

### ✅ [EPS-BACKFILL-SEMI-1] 半導体6銘柄のEPS Analyzerデータ生成（2026-07-11完了）
**発見:** MONITOR-SYNC-FIX-1修正時、6銘柄が登録手順Step 5b未実施
（EPS Analyzerデータなし）であることが判明

#### 内容
APGE/RMBS/ENTG/TER/KLAC/LRCXに対し`adjusted_eps_analyzer/pipeline.py --ticker`を
実行しEPS Analyzerデータを生成。registration_validator.pyでP1-Step5b-EPS
WARNが6件とも解消したことを確認。RMBS/ENTG/TER/KLAC/LRCXは黒字半導体企業として
妥当なadjusted_eps（$2.5〜$38）、APGEは売上ゼロの臨床段階バイオのため
TTM全期間赤字（データ自体は正常生成だがEPS評価の実用性は限定的）。
report_consistency_check.py NG=0、pytest 124件パス確認済み。

---

### ✅ [SYSTEM-MAP-PATH-FIX-1] SYSTEM_MAP.md出力先パス誤記5件の修正（2026-07-11完了）
**発見:** SYSTEM_MAP.md全体像の実態調査時、システム一覧テーブルの記載パスと
リポジトリ実態の突合で判明

#### 内容
「システム一覧と責任範囲」テーブルのうちSTONKS SILO・EPS ANALYZER・
MACRO PULSE・Market Pulse・PORTFOLIOの5件で、記載パスが実在しない
ディレクトリ構成になっていたことを修正（例: PORTFOLIOの旧記載
`docs/management/portfolio/`は該当ディレクトリ自体が存在せず、
正しくは`docs/portfolio/`）。併せて「銘柄振り分けの正本（cik_lookup.csv）」
セクション新設・STONKS SILOの解像度向上・AutoTrade運用実体/OpenD前提の
追記等、SYSTEM_MAP.md全体の実態調査結果を反映。

---

## 2026-07-10（完了）

### ✅ [ARCH-DATA-1-CONSOLIDATE-1] SEC-TAG-FICO-CPRT-1のARCH-DATA-1への統合検討（2026-07-10完了）
**発見:** サテライト投資候補91銘柄への前提妥当性チェック展開時の自己点検

#### 問題
本日登録した[[SEC-TAG-FICO-CPRT-1]]（FICO・CPRTのSECタグ誤取得疑い）は、
[[ARCH-DATA-1]]（SECデータ正規化レイヤー強化、優先度：高）が対処すべき
「データ形起因バグ」の一事例であり、独立タスクとして扱うと管理が
重複する懸念があった。

#### 対応
登録と同時に、ARCH-DATA-1の「着手条件」（次にデータ形起因バグが発生した
時点で着手）にSEC-TAG-FICO-CPRT-1が該当する事例であることをARCH-DATA-1
エントリ側に相互参照として追記済み（ARCH-DATA-1エントリ内「着手条件に
該当する新規事例」参照）。SEC-TAG-FICO-CPRT-1エントリ自体は個別事例の
記録としてBACKLOG.mdに残し、実際の一次情報確認・修正はARCH-DATA-1着手時に
まとめて行う方針とした。登録タスクとしてはこの時点で完了のため、
本エントリ自体をクローズする。

---

### ✅ [SCREENING-INFRA-1] スクリーニングスクリプト2本をcommon/screening/へ正式格納（2026-07-10完了）
**発見:** サテライト投資候補91銘柄への前提妥当性チェック展開時

#### 内容
サテライト投資候補スクリーニングで使用したアドホックスクリプト2本を
再利用可能な形に整理し、`common/screening/`へ正式格納した（commit e8838df30）：
- `dcf_validity_checker.py`: DCF成長率前提・ROIC投下資本の妥当性を機械チェック
  （growth_source=fcf_cagr floor値張り付き検知・segment_detail.source実態確認等）
- `report_txt_parser.py`: report.txt（統合レポート）を読み取り専用でJSON構造化する
  パーサー（フォーマット差異3件に対応済み）

いずれも既存パイプライン成果物（latest.json/annual_{year}.json/report.txt等）を
読み取るのみで本番ファイルは変更しない。SYSTEM_MAP.mdにも追記済み。

---

## 2026-07-09（完了）

### ✅ [DILUTION-FYE-1] LRCX希薄化率異常値（10:1株式分割誤検知）（2026-07-09完了）
**発見:** LRCX 2024年10月株式分割の希薄化率誤算出（109.34%/年）指摘

#### 問題
希薄化率算出（pipeline.py _calc_moat_inputs近傍）の四半期グルーピングが
暦年ラベル（end[:4]）ベースだったため、非12月決算企業（FYE≠12月）で
分割前基準・分割後遡及修正済み基準の四半期が同一暦年内に混在し、
分割検知ロジックが機能せず実際の希薄化と誤判定していた。
CHECK-QREV-FYE-1と同型のバグ。

#### 対応
四半期グルーピングを年次end日起点のtrailing 12ヶ月窓（会計年度ベース）
に変更。LRCX: 109.34%→-1.7%（自社株買い、実態と整合）、
split_factor=9.66で10:1分割を正しく検知。

#### 横断確認
NOW（5:1分割）・AVGO（10:1分割）・WMT（3:1分割）・NVDA（10:1分割）で
回帰なし確認。ALAB・RBRKは分割ではなく正当な希薄化と確認（誤検知なし）。
LOARはデータ不足でスキップ（誤検知なし）。

### ✅ [HYPECORE-TICKERS-INDEX-1] HypeCore画面に新規登録5銘柄が表示されない問題（2026-07-09完了）
- 原因: `docs/value-monitor/hypecore/index.html` の一覧表示が
  `const ALL_TICKERS=[...]` というHTML内に直接ハードコードされた配列を
  参照しており、cik_lookup.csvのhypecore=trueフラグとは完全に独立していた。
  `docs/value-monitor/hypecore/data/tickers.json` という一覧ファイルは
  既に存在していたが、index.htmlはこれをfetchしておらず、`hypecore.py`側も
  このファイルを書き込む処理を持っていなかった（2つとも同一の古い
  ハードコード内容の孤立コピーで、6/26以降どちらも更新されていなかった）
- 対応: (1) `hypecore.py`に`_save_tickers_index()`を新設し、実行のたびに
  `docs/value-monitor/hypecore/data/*_poc.json`の実在ファイルを走査して
  `tickers.json`を再生成するよう変更（TANUKI VALUATIONの
  `_save_tickers_index`と同一パターン）。(2) `index.html`のハードコード配列を
  削除し、`loadAll()`冒頭で`data/tickers.json`をfetchする方式に変更
- 効果: RMBS/ENTG/TER/KLAC/LRCXを含む実在103銘柄（cik_lookup.csv
  hypecore=true 104銘柄中、データ不足で失敗した1銘柄を除く）が
  tickers.jsonに反映され、index.htmlに正しく表示されるようになった。
  以後の新規銘柄登録時もhypecore.py実行のたびに自動反映される
  （手動でのtickers.json更新は不要）
- 検証: ローカルHTTPサーバーでindex.html→tickers.json→各poc.jsonの
  fetchチェーンが正しく機能することを確認（この環境にはブラウザ自動化
  ツールがなく実ブラウザでの目視確認は未実施）。pytest 124件パス・
  report_consistency_check NG=0・check_links.py エラー0件を確認

### ✅ [PARSER-ENTG-COMPYEAR-1] ENTGのFY2022年次Revenue誤抽出（2026-07-09完了）
- 原因: `common/sec_data/quarterly.py` の `_classify_period()` が `is_annual` 判定にform制限を
  課しておらず、10-Q内に混入する比較用contextRef（ENTGのFY2023 Q3 10-Q内にあった
  `start=2022-01-01/end=2022-12-31`のQ1-Q3累計値、form=10-Q）が「最新filed優先」で
  正規のFY2022 10-K年次値（$3,282,033,000）を上書きし、$2,335,963,000（実質Q1+Q2+Q3合計）
  に化けていた。結果としてQ4 2022合成値が$0になりZeroDivisionErrorでrevenue品質チェックが
  クラッシュしていた
- 対応: `is_annual` 判定にform=10-K/10-K-A限定の条件を追加。10-Q由来でduration>300日の
  エントリは比較用ノイズとみなし除外する処理も追加
- 影響確認: 同パターンの混入がAMZN/BSY/DELL/ESTCのOCF/ICF等でも見つかったため
  合わせて再生成（実annual値は別途Dec-31形式で存在しており実害なしと確認済み）
- ENTG Step1〜3再実行完了。理論株価$48.79（乖離-64.8%）で正常完了

### ✅ [XBRL-TAG-KLAC-1] KLACのoperating_income/gross_profit抽出失敗（2026-07-09完了）
- 原因1（GrossProfit）: KLA Corpは自社のFY2021 10-K内に「四半期duration（91日）だが
  fp='FY'」という比較開示データを含めており、`_classify_period()`が`fp=='FY'`のみで
  年次判定していたため誤って年次GrossProfitとして取り込まれ、FY2022以降は本来の
  年次GrossProfitタグ自体をKLAが報告していないため4件の古い四半期データのまま
  更新が止まっていた（Moat Score計算でGM=10%表示、実態は約60%）
- 原因2（OperatingIncome）: KLA CorpはFY2015 10-K以降、年次OperatingIncomeLossタグを
  一度も報告しておらず、ROIC計算が恒常的にNoneになりMoat ScoreのROIC項が0floor
  になっていた
- 対応: (1) `_classify_period()`のis_annual判定に`fp=='FY' and days>130`の下限を追加し、
  四半期durationの誤タグ混入を排除。(2) `pipeline.py`の`_calc_moat_inputs()`にGrossProfit
  annual欠落時の四半期12件合算フォールバックを追加。(3) `_calc_roic_wacc_ratio()`に
  `_estimate_ttm_operating_income()`（直近4四半期のGrossProfit-RD-SM合算）フォールバックを
  新設。この2フォールバックは汎用実装のため他銘柄にも自動適用される
- 効果: KLAC Moat Score 0.240→0.843（GM=10%→61%、ROIC=0%→100%capped）、
  Phase1=5yr→9yr、理論株価$58.59→$70.33（乖離-68.2%）に是正
  （当初「$82.06」と報告したのはstdout表示バグによる誤報告。実際に保存された
  JSON値は$70.33。詳細は[[STDOUT-JSON-MISMATCH-1]]参照）
- 横断監査（軽め）: 直近3年operating_income全欠落銘柄が他に6件（ASTS/BX/JNJ/LLY/SOFI/XOM）
  存在することを確認。→ [[XBRL-TAG-KLAC-1-FOLLOWUP]]で検証・対応完了

### ✅ [CHECK-QREV-FYE-1] check_revenue_quality()の暦年グルーピング誤検知（2026-07-09完了）
- 原因: `check_revenue_quality()`のチェック4（四半期合計vsFY年次整合性）が年次end日の
  暦年ラベル（`a_end[:4]`）で四半期をグルーピングしており、非12月決算企業
  （KLAC=6月期・LRCX=6月期・DELL=1月期・ESTC=4月期等）で本来同一会計年度に属する
  四半期が正しく合算されず、false positiveの❌ISSUEを出していた
- 対応: 年次end日を起点にtrailing 12ヶ月窓（370日以内）で4四半期を抽出する
  会計年度ベースのグルーピングに変更
- 検証: KLAC/LRCX/ESTCはISSUE解消。DELLはISSUE解消の上で別要因（直近四半期の
  実売上急増+87.5%、AI関連需要とみられる）によるWARNのみに変化。report_consistency_check.py
  はNG=0を維持

### ✅ [XBRL-TAG-KLAC-1-FOLLOWUP] operating_income欠落6銘柄への新設フォールバック適用確認（2026-07-09完了）
- 対象6銘柄中BXはtanuki=false（TANUKI VALUATION対象外）のため除外、残り5銘柄
  （ASTS/JNJ/LLY/SOFI/XOM）で検証
- 検証の過程でバグA・バグBの2件を新規発見・根本修正（詳細は下記参照）：
  - バグA: `_calc_moat_inputs()`のGrossProfit年次フォールバック条件が
    `elif not gp_annual:`（完全に空の場合のみ発動）になっており、年次データが
    存在するが直近年とマッチしない（stale）場合にフォールバックが発動しない
    欠陥があった。`else:`（pairs 0件なら常に発動）に修正
  - バグB: `_estimate_ttm_operating_income()`がGrossProfit/RD/SMを独立に
    「直近4四半期」取得しており、いずれかのタグ報告が停止しているとR&D控除
    漏れ等でTTM営業利益を過大・無意味に算出していた（LLY: RDが2022-2023年で
    停止、JNJ: RDタグ自体が空）。3フィールド共通の期末日（intersection）が
    4件未満ならNoneを返す方式に修正
- 効果（バグA・B修正後の最終結果）:
  - ASTS: Moat Score 0.000→0.183、GM算出可能化（0.00→0.46）。ROICは元々の
    無意味な誤算出値から「算出不可（0扱い）」の安全側挙動に是正
  - LLY: ROIC過大評価（1.00 capped）を是正し0.00（算出不可）に。
    乖離率+23.0%→-25.2%へ逆転（修正後の方が実態に近いと判断）
  - JNJ: 同様にROIC過大評価（0.64）を是正し0.00に。既存のR&Dタグ抽出漏れ
    （システム全体の既知ギャップ、今回の修正対象外）に起因
  - SOFI/XOM/KLAC: 回帰なしを確認
- 副産物: KLACの当初報告値「$82.06」がstdout表示バグ（[[STDOUT-JSON-MISMATCH-1]]）
  による誤報告と判明し、記録を$70.33に訂正

### ✅ [STDOUT-JSON-MISMATCH-1] pipeline.py stdout表示とJSON保存値の不一致（2026-07-09完了）
- 原因: `_save_result()`内、`recommended_g`によるDCF再計算ロジック
  （`segment_configured=False`の銘柄が対象）がローカル変数`valuation`を
  再代入するだけで、呼び出し元（`process_ticker`ループ）の`valuation`
  オブジェクトを更新していなかった。stdoutの完了メッセージ・
  `results[ticker]`は再計算前の古い`valuation`を参照し続け、実際に
  JSON保存される値（再計算後）と食い違っていた
- 対応: `_save_result()`の戻り値を`None`→`dict`に変更し、最終的な
  `valuation`を返すよう修正。呼び出し元も`valuation = self._save_result(...)`
  と戻り値を受け取る形に変更
- 影響範囲: `segment_configured=False`は102銘柄中65銘柄。ただし実際に
  発火するのは`recommended_g`が算出され再計算が成功した場合のみのため、
  65銘柄全てが被害を受けているとは限らない
- 本日確認済みの被害銘柄（BACKLOG_DONE.md記載の理論株価とJSON実値の突合により確認）:
  RMBS（$83.54→実際$87.50）・ENTG（$48.79→実際$28.11）・TER（$108.49→実際$53.64）・
  LRCX（$110.06→実際$58.51）・CON（$40.47→実際$17.78、記録は[[新規銘柄登録]] WST・CONエントリで訂正済み）。
  KLACは[[XBRL-TAG-KLAC-1]]対応時（2026-07-09）に$70.33へ訂正済み
- 検証: RMBS/ENTG/TER/KLAC/LRCXでpipeline.py再実行し、修正後はstdout表示が
  JSON保存値と完全一致することを確認。JSON値自体は修正前後で不変
  （表示のみのバグで計算結果には影響しなかったことを確認）
- **未検証の既知リスク**: BACKLOG_DONE.md内の過去記録（JNJ・VST/FCX/SCCO/CEG/KO・
  ALAB等、`segment_configured`変更やG変更・逓減DCF適用を伴う記録）は同種の
  発火条件（`segment_configured=False`時点での再計算）に該当しうるが、
  当時のコード・データ状態を遡って検証する工数が大きいため今回は棚卸し
  一覧化のみに留め、個別の正誤判定は未実施

### ✅ [新規銘柄登録] RMBS・ENTG・TER・KLAC・LRCX（2026-07-09完了）
- CIK確認・cik_lookup.csv登録（status=active, registration_source=manual,
  registration_note="半導体関連・手動一括登録"）
- RMBS/TER/LRCX: Step1〜3完了、異常なし
  （RMBS理論株価$83.54/乖離-23.8%、TER理論株価$108.49/乖離-69.1%、
  LRCX理論株価$110.06/乖離-67.0%）
- ENTG: Step1でFY2022年次Revenue誤抽出を検知、PARSER-ENTG-COMPYEAR-1として
  根本修正後Step1〜3完了（理論株価$48.79/乖離-64.8%）
- KLAC: Step3完了後operating_income/gross_profit欠落を検知、XBRL-TAG-KLAC-1
  として根本修正後再計算完了（Moat Score 0.240→0.843、理論株価$58.59→$70.33）
- 副産物: CHECK-QREV-FYE-1（非12月決算企業の誤検知修正）、
  XBRL-TAG-KLAC-1-FOLLOWUP（他6銘柄への横展開確認）をBACKLOG登録

### ✅ [TAIL-DCF-TABIDX-1] index.htmlのDCFタブ非同期再描画がtab index不一致（2026-07-09完了）
- `docs/portfolio/tail/index.html` の `buildTabDcf()`（Tab 4: DCFシナリオ）内、シナリオファイル
  未ロード時の非同期コールバックが誤って `modalTabIdx === 3` / `renderModalBody(ticker, 3)`
  （KPIトレンドタブのindex）を参照していたのを `modalTabIdx === 4` / `renderModalBody(ticker, 4)` に修正
- コメント「Tab 3: DCFシナリオ」も実態（TABS_CORE/TABS_SATのindex=4）に合わせ「Tab 4」に修正
- KPIトレンド側（L1365、modalTabIdx===3）は正しい実装のため変更対象外と確認済み

---

## 2026-07-08（完了）

### ✅ [BACKLOG-DEDUP-CHECK-1] BACKLOG.md・BACKLOG_DONE.md間の項目ID重複チェック（2026-07-08完了）
- 背景: [[TTM-NULL-1]]・[[STONKS-DIV-1]]で2件連続、BACKLOG_DONE.mdに完了記録があるのに
  BACKLOG.md側の削除が漏れて再度アクティブ項目として残存していたパターンが発覚したため、
  両ファイル間で同一項目IDの重複がないか全数チェックを実施した
- 抽出範囲: `###`見出し形式に加え、旧セクションで使われている行頭`✅`/`❌`箇条書き形式のID宣言も
  対象に含めて全数抽出（旧形式のみに存在するIDが見出し限定の抽出では漏れることが判明したため）
  - BACKLOG.md: 40件（すべて`###`見出し形式）
  - BACKLOG_DONE.md: 219件（`###`見出し形式 + 旧`✅`箇条書き形式の混在）
- **BACKLOG.md・BACKLOG_DONE.md 両方に存在するID: 2件（いずれも削除不要と判定）**
  - `DESIGN-8`: BACKLOG.mdは8-3・8-4（未着手）、BACKLOG_DONE.mdは8-1・8-2・8-5・8-6（完了済み）で
    枝番が重複しておらず、同一エピック配下の子タスクを分担管理する正常な設計と確認
  - `UI-DISCOVER-1`: BACKLOG.mdの現行エントリ自体が「✅ 影響予測機能追加（2026-07-05完了、
    BACKLOG_DONE.md参照）」「[ ] その他のUI課題（未着手）」と部分完了を明示しており、
    BACKLOG_DONE.mdの完了記録はその一部分を正しく裏付けている（親タスクは意図的に継続中）
  - → 今回はBACKLOG.mdからの削除対象なし（TTM-NULL-1・STONKS-DIV-1のような真の削除漏れは
    このタイミングでは他に見つからなかった）
- **副次的発見: BACKLOG_DONE.md内部でのID再利用（6件、削除対象ではないが記録として残す）**
  - `SEC-CTRL-1`・`STONKS-DIV-1`・`TTM-NULL-1`: 同一機能・同一バグへの段階的対応（初回実装→
    追加対応）としてのID再利用で、実害なしと判断
  - `DCF-RELIABILITY-1`・`MP-GAUGE-NEEDLE-1`: 関連はするが厳密には別内容の対応（前者は
    「調査のみ・対応不要」と「実装」、後者は「針とラベルの重なり修正」と「0/100ラベル除去」）に
    同一IDが再利用されている。実害は軽微（両エントリともBACKLOG.mdには存在せず参照される機会が
    少ない）だが、本来は枝番号（`-2`等）を振るべきだった
  - `TAIL-UX-1`: **最も紛らわしい例**。2026-06-24「TANUKI TAIL使い方ガイダンス充実」（ツールチップ
    追加）と2026-07-05「TANUKI TAIL詳細モーダルの一覧性向上（Phase1+2）」という**内容的に無関係な
    2つのタスク**が同一IDを共有している。`[[TAIL-UX-1]]`形式のwikiリンクで参照した場合にどちらを
    指すか一意に定まらない状態
- 再発防止策の提案（ファイル追記はチャット側判断のため提案のみ）:
  1. BACKLOG更新のタイミング（BACKLOG.mdの「タスク完了後の①②③手順」）に、複数項目を一括対応した
     場合は「対応した全IDについてBACKLOG.mdへのgrepでヒット0件を確認してからコミットする」ことを
     明記する（TTM-NULL-1/STONKS-DIV-1はまさに5項目一括コミットの中で1手順が漏れたケース）
  2. 新規IDを採番する前に`grep -n "\[候補ID\]" BACKLOG.md BACKLOG_DONE.md`でID未使用を確認する
     ステップを新規課題登録時のルールに追加する（TAIL-UX-1型の無関係タスクへのID再利用を防止）
  3. 本チェック（項目ID抽出→重複検出）をワンショットではなく`check_backlog_dedup.py`のような
     再利用可能スクリプト化し、月次メンテナンスタスク（CLAUDE_CODE_START.md「⑤横断整合性チェック」）
     に組み込むことを検討する

---

### ✅ [STONKS-DIV-1] analyzer.pyのゼロ除算ガード再確認・回帰テスト追加（2026-07-08完了）
- 経緯: BACKLOG.mdに残っていた本項目も2026-06-27に一度「調査の結果、3箇所（r_start/rev/
  avg_past）はすでにガード済みと判明（実装修正不要）」として対応済みだったが、
  BACKLOG.mdからの削除漏れで再度アクティブ項目として残存していた（[[TTM-NULL-1]]と同型の
  記録漏れパターン）
- 再調査: 指摘された3箇所（L222の`r_start > 0`・L314の`_lpr()`内`rev <= 0`・L625の
  `avg_past > 0`）は現在も全てガード済みと再確認。TTM-NULL-1の前例（同種パターンの
  見落とし発見）を踏まえ、`analyzer.py`全体（1267行）の除算演算子を全数grepし直したが、
  今回は追加の未ガード箇所は発見されなかった（実装修正なし）
- テスト: 既存の`TestStonksDivisionGuards`（L222/L314相当の2件）に加えて、
  L625（avg_past=0）を検証する回帰テストが未整備だったため
  `test_discontinuous_growth_avg_past_zero_skips_comparison`を追加。
  過去YoY平均がちょうど0%・直近YoYが+300%（急拡大条件）になるデータを構成し、
  ガードを外すと実際にZeroDivisionErrorが再現することを事前確認した上で採用
- pytest: 167 passed（新規1件込み）+ 既知の無関係な2件失敗（[[TEST-STALE-IV-1]]、NVDA/MSFT）

---

### ✅ [TTM-NULL-1] ttm_calculator.py calc_ttm_series()のval=None TypeErrorガード追加（2026-07-08完了）
- 経緯: BACKLOG.mdに残っていた本項目は2026-06-27に一度対応済み（L94のcalc_ttm/L185の
  _build_q4_quarterly_entries を`sum(e["val"] or 0 for e in ...)`にガード済み、
  BACKLOG_DONE.md参照）だったが、BACKLOG.mdからの削除漏れで再度アクティブ項目として残存していた
- 再調査の結果、同一ファイル内`calc_ttm_series()`（L489、rolling TTM系列生成。update.py経由で
  本番パイプラインが実際に使用）に同型の未ガード`sum(e["val"] for e in last4)`が別途存在すると判明
  （2026-06-27修正時のgrep漏れ。`_calc_q4_implied`のL312は既にガード済みだったため見落とされた）
- 対応: `common/sec_data/ttm_calculator.py` L489を`sum(e["val"] or 0 for e in last4)`に修正
- テスト: `tests/test_ttm_calculator.py`に`TestCalcTtmSeriesNullValGuard`を追加（1件）。
  修正前コードで実際にTypeErrorが再現することを確認した上で回帰テストとして採用
- pytest: 166 passed（新規1件込み）+ 既知の無関係な2件失敗（[[TEST-STALE-IV-1]]、NVDA/MSFT）

---

### ✅ [MACRO-NFP-HIST-1] NFP過去履歴の水準→前月比一括再計算（2026-07-08完了）
- 背景: [[MACRO-NFP-1]]（2026-07-07完了）でNFPの新規fetchロジックは前月比に修正済みだったが、
  `05_events.csv`内の既存NFP行370件（1996-01〜2026-07）は水準値のまま据え置かれており、
  `05_audit.py`のCHECK-2がNG（水準残存）を検出し続けていた
- 新設: `src/market/macro_pulse/05_backfill_nfp_mom.py`（一括変換スクリプト、`--dry-run`対応）
  - FRED PAYEMS全期間水準系列を再取得し、`(level_now - level_prev) * 1000`で前月比に変換
    （`05_import_history.py`の`import_from_fred()`と同一方式）
  - 対象月判定: release_dateの日が「01」→release_date月そのものが観測月（旧FRED一括投入 /
    スケジュール未一致のrefresh由来）。日が「01」以外→release_date月の1ヶ月前が観測月
    （BLS実発表日でスケジュール一致したrefresh由来。NFPの実発表日が月初1日になることはなく
    両者は曖昧なく判別可能なことを`05_indicator_schedule.csv`の実データで確認済み）
  - `forecast_source="actual_as_forecast"`の8行（consensus=actualのコピー）はconsensus/
    surprise/surprise_pctも新actualに合わせて更新。それ以外362行（consensus空欄）はactualのみ更新
  - 書き換え前に`05_events.csv.bak_{timestamp}`へバックアップを自動作成
- 実行結果: NFP全370行を変換（1996-01-01〜2026-07-02、スキップ0件）
- 検証: `python src/market/macro_pulse/05_audit.py` → CHECK-2 NG=0を確認
  （WARN 49→48件。うち1件はNFP水準の偶然一致によるものが解消され、MoM値の偶然一致
  （nfp_2017-04-01/05-01が共に205000）が新たにWARN対象になったが人間確認要の範囲内で許容）
- テスト: `tests/test_macro_pulse_logic.py`（18件）・`tests/`全体（165件）継続パスを確認
  （test_iv_formula.py MSFT/NVDAの2件失敗は[[TEST-STALE-IV-1]]起因の既知の無関係な失敗）

---

## 2026-07-07（完了）

### ✅ [MACRO-NFP-1] MACRO PULSE NFP表示ロジック修正（2026-07-07完了）
- 発覚経緯: ユーザー報告（RECENT SIGNALSパネルのNFP行が5/8・6/1・6/5・7/2の4回連続で
  ACTUAL=PREV=159.0K・CHANGE=±0と表示、stale疑い）→ 調査の結果、fetch失敗ではなく
  ロジック誤り2件の複合と判明（詳細調査ログは会話履歴参照）
- 原因①: `05_main.py`の`fetch_event_row()`がPAYEMS（雇用者数の**水準**、約15.9億人規模）を
  そのまま`actual`に格納しており、本来の「NFP＝前月比新規雇用者数」になっていなかった。
  フロントエンドの`fmtK()`が水準値を`/1000`表示するため、月次のわずかな水準変動が
  小数第1位に丸め込まれ同一表示に見えていた
- 原因②: `run()`内でscheduledループが追加した行を`refresh_monthly_indicators()`に渡す
  `events`スナップショットが反映されておらず、同一FRED観測値が別々のevent_idスロット
  （例: nfp_2026-06-01とnfp_2026-07-02、共に158984.0）に二重書き込みされていた
  （Building Permits・Michigan Consumer Sentimentでも同型の重複を実データで確認）
- 対応①: `fred_latest_with_prev()`を新設し、`fetch_event_row()`のNFP分岐で
  `actual = round((level_now - level_prev) * 1000)`（千人→人単位の前月比）に変更。
  `05_import_history.py`の`import_from_fred()`も同様にNFPのみ`s.diff()*1000`で変換
  （既存05_events.csvの過去NFP行は本タスクでは書き換えず、[[MACRO-NFP-HIST-1]]に切り出し）
- 対応②: `run()`が`refresh_monthly_indicators()`に渡す`events`をscheduledループの
  新規行を反映したスナップショットに更新。加えて`dedupe_new_rows()`を新設し、
  「同一indicator×同一actual値×release_date差が窓（obs_to_release_lag+14日）以内」の
  行を最終マージ前に除外する防御的ガードを追加
- 対応③: 再発防止用の軽量監査スクリプト`src/market/macro_pulse/05_audit.py`を新設
  （CHECK-1: 重複行検出=WARN、CHECK-2: NFP水準残存兆候=NG）。CHECK-1はIC4WSA等の
  移動平均系指標が正常運用でも同値継続することがあるためWARN、CHECK-2は前月比なら
  大きく振れるはずの値が狭いレンジに収束していることを検出するためNGとした
- テスト: `tests/test_macro_pulse_logic.py`新設（18件、fred_latest_with_prev・
  NFP前月比変換・dedupe_new_rows・監査スクリプトの2チェックを網羅、実際に発生した
  Building Permits/Michigan Consumer Sentimentの重複を再現する回帰テストを含む）。
  既存pytest（tests/全体、165件）は無影響（test_iv_formula.py MSFT/NVDAの2件失敗は
  [[TEST-STALE-IV-1]]起因の既知の無関係な失敗）
- 副産物: 過去NFP履歴の水準→前月比一括再計算を[[MACRO-NFP-HIST-1]]としてBACKLOG登録

---

## 2026-07-06（完了）

### ✅ [HYPE-TRANS-1] HYPECOREステージ遷移確率が「現ステージへの過去滞在履歴なし」で0%誤表示（2026-07-06完了）
- 発覚経緯: ユーザー報告（HYPECORE SOFI画面、ステージ遷移確率が全項目0%表示）
- 原因: `docs/value-monitor/hypecore/detail.html` の `calcTrans(m,cur)` が
  現在stageから過去に一度も遷移していない場合（`tot=0`）に `tot=...||1` の
  フォールバックで分母を1に置き換えていたため、「算出不能」が「0%（絶対に
  遷移しない）」という誤った意味の数値として表示されていた。特定銘柄固有の
  データ不整合ではなく、全銘柄で起こりうる汎用的なエッジケース（現在stageが
  直近月に初めて到達したもので、それ以前の履歴内に出現しない場合に発生）
- 対応: `calcTrans` の戻り値を `{insufficient, data}` 形式に変更し、`tot===0`
  の場合は `insufficient:true` を返す。呼び出し元（遷移確率リスト描画部）で
  `insufficient:true` の場合はバー幅0%のまま数値表示を「データ不足」に切り替え、
  従来の0%埋めを廃止（恒久対応）
- 影響銘柄: 98銘柄全件をシミュレーション再検証し、SOFI（stage1・履歴内出現0回）・
  FLYW（stage3・同0回）・RKLB（stage2・同0回）の3銘柄で該当を確認。修正後は
  3銘柄とも「データ不足」表示に切り替わることをPlaywrightで実描画確認
- 回帰確認: 通常ケース（NVDA、tot>0）で従来通りprob値（%）が降順ソートで
  表示されることを確認し、既存表示への影響なしを確認

---

## 2026-07-05（完了）

### ✅ [UI-DISCOVER-1] 「連想・考察→影響予測」機能追加（方式C: 独立パイプライン・2026-07-05）
- 新規独立スクリプト `src/discover/impact_predictor.py` を追加（collect.py/catalyst.py本体は変更なし）。
  collect.py実行後(`--source news`)・catalyst.py実行後(`--source catalyst`)にそれぞれ呼び出し、
  銘柄単位でその日/週の新規項目をまとめてGrokに1回渡し、各項目のdirection(positive/negative/neutral)・
  magnitude(高/中/低)・thesis_effect(補強/弱化/中立)・1行summaryを生成
- 前提整備: `collect.py` `append_to_monthly_history()` にnews item安定id(ticker×日付内の連番)を付与
  （catalyst.jsonは既存の`id`フィールドをそのまま利用）
- 出力先は新規ファイル `docs/discover/data/impact_predictions_YYYY_MM.json`（news_history/catalyst.json
  は無改変・案2）。catalyst.htmlは各カタリストの`first_detected`から必要な月ファイルを逆引きしてマージ
- GitHub Actions（Discover_Update.yml・Catalyst_Update.yml）に実行ステップとgit add対象を追加、
  `.gitattributes`にmerge=ours設定を追加
- catalyst.pyは既存の累積分を再処理せずfirst_detected==当日実行分のみを対象とし、
  [[CATALYST-DEDUP-1]]の無制限増加問題を新機能側では悪化させない設計とした
- 検証: モックGrok応答による単体ロジックテスト（news/catalyst両モード、新規分のみが対象になることを確認）、
  Playwrightでnews_history.html・catalyst.htmlの実描画（1行サマリ表示・予測未生成月の404を握りつぶすフォール
  バック動作）を確認。pytest 123件は無影響（データ層のみの変更のため）
- 副産物: [[CATALYST-DEDUP-1]]・[[GROK-MODEL-PRICE-1]]をBACKLOG登録（優先度未定・別タスク）

---

### ✅ [TAIL-UX-1] TANUKI TAIL詳細モーダルの一覧性向上（Phase1+2 完了・2026-07-05）
- Phase2: AI視点セクションを3実装（detail.html/index.htmlタブ/index.htmlダッシュボードZoneE）から
  detail.html一本化。表示順を「業績見通し（KPI予想・新規）→テーゼへの問いかけ・次回確認論点→
  歴史的類比等→5観点（折りたたみ・デフォルト閉）」に再構成し、優先度のない均等表示を解消
- index.htmlのAI視点タブ（buildTabCall2）・ダッシュボードZoneEを削除し、detail.htmlへの
  リンク導線に置き換え。内部統制タブがindex 6→5にシフトするため関連参照4箇所を同期修正
- Playwrightでdetail.html（PLTR/SOFI/TSLA=KPI予想テーブル正常描画、ADBE=データなし表示）と
  index.htmlモーダル（タブ構成6個・内部統制タブ動作・ZoneEリンク遷移）を検証、新規コンソール
  エラーなしを確認。副産物として[[TAIL-DCF-TABIDX-1]]（既存のtab index不一致バグ）を発見しBACKLOG登録

---

## 2026-07-03（完了）

### ✅ [ARCH-DATA-1-YTD] SEC四半期正規化ロジック 全101銘柄ロールアウト完了（2026-07-03 完了）
- commit: c00c3abc5（バグA・B修正）, 1c0920ec4（全銘柄データ再生成）
- [[BUG-CON-YTD-1/2]]（2026-07-02完了）で特定した14銘柄のうちAMD/AMZN/HWMをスポットチェックした際、
  AMZN固有の新規回帰バグ2件を追加発見・修正した：
  - バグA: `_calc_gross_profit()`がend日付のみでRevenue/COGSを引き当て、単独四半期値と
    未解決の累積値（is_ytd=True）が同一endで共存すると累積値を誤採用（GrossProfitが実際の
    数倍に膨張）。`_index_quarterly_by_end()`新設で単独四半期値を優先するよう修正
  - バグB: `_build_missing_quarter_implied_entries()`が算出する欠落四半期のend/start日付が
    暦四半期境界と1日ずれ、`_build_q4_implied_entries()`の結果と重複排除できず、
    FY2022/2023/2024のOCF/ICF/CFF/CapEx/SBC/DA/NetIncomeが12/31と1/1の2エントリに
    二重計上。日付演算のオフバイワンを修正（AMZN TTM NetIncome 2023〜2025年3月末時点で
    最大+53.7%誤って膨張していたものを是正）
- 検証: pytest129件パス（既存123+新規test_normalizer.py 6件）。AMD/HWMはデグレなし
  （TTM系列バイト単位で完全一致）。APGE/AVAV/CIX/CON/ESTC/GEV/HEI/PM/RCAT/SOUN/ZSの
  11銘柄を横断スキャンし同パターン0件を確認
- 全101銘柄で`update.py`・`pipeline.py --skip-risk`を再実行し、
  `report_consistency_check.py`でNG=0（WARN=1件、ELF PSステール値・既存事象で無関係）を確認
- IV変化: AMZN+3.5%, AVAV+12.3%, BKNG-6.6%, FCX-23.2%, SITM-11.9%, XOM-2.2%
  FCF_Base変化（IV不変含む）: 40銘柄（5年ロールウィンドウ境界四半期の重複計上是正・
  誤除外復元による想定通りの補正）
- 副産物: [[TEST-STALE-IV-1]]（test_iv_formula.pyのALPHA-REDESIGN-1未追従）を発見しBACKLOG登録

---

## 2026-07-02（完了）

### ✅ [TICKER-META-1] cik_lookup.csv登録メタデータ機能追加（2026-07-02 完了）
- commit: 337bf3d29
- cik_lookup.csvにstatus/registered_date/registration_source/registration_note列を新設
- 既存97銘柄をstatus=active/registration_source=unknownでバックフィル
- CLAUDE_CODE_START.mdの新規銘柄登録手順にStep 0.5として組み込み（登録理由が不明な場合はユーザーに確認を求める仕様）

---

### ✅ [新規銘柄登録] WST・CON（ミネルヴィニ・スーパーストック条件）（2026-07-02 完了）
- commit: 3d45e6794
- registration_source=technical_screening を新設カテゴリとして追加
- WST: Step0〜8完了。セグメント設定（Proprietary Products 81.07%/West Vantage 18.93%）。理論株価$96.85、現在株価比乖離-73.5%
- CON: Step0〜8完了。単一セグメント（設定不要）。β=0.511（yfinance未提供のため2年週次データから手動算出）。理論株価$17.78、乖離-43.4%
  （当初「$40.47、乖離+31.5%」と記録したのは[[STDOUT-JSON-MISMATCH-1]]による誤報告。2026-07-09にJSON実値へ訂正）

---

### ✅ [新規銘柄登録] APGE（TANUKI TAIL satellite登録）（2026-07-02 完了）
- commit: 3d45e6794
- 収益系XBRLタグが皆無（臨床段階バイオで売上ゼロ）と判定。TANUKI VALUATION（DCF）・STONKS SILO（黒字化パス追跡）とも設計上不適合
- cik_lookup.csv: tanuki=false, stonks_silo=false
- TANUKI TAIL satelliteとして `APGE_thesis.json` を作成（テーゼ: カタリスト追跡・治験マイルストーン主導）

---

### ✅ [新規銘柄登録] SN（一時的にTANUKI VALUATION保留）（2026-07-02 完了）
- commit: 3d45e6794
- 2025年まで20-F提出企業（外国民間発行体）のため四半期データが2026年Q1分のみ存在し、TTM/トレンド系列が構築不能
- Discover/HypeCore/EPS Analyzerは完了。cik_lookup.csv: tanuki=false（一時的措置とregistration_noteに明記）
- BACKLOG.mdに [SN-TANUKI-DELAY-1] を登録（2026年8月Q2 10-Q提出後にtanuki=true復帰予定）

---

### ✅ [BUG-CON-YTD-1/2] SECデータ正規化: SA/YTD重複判定バグ根本修正（2026-07-02 完了）
- commit: 3d45e6794
- 発端: CON（2024年IPO）のFY2023 Revenue 48.8%乖離調査
- `common/sec_data/quarterly.py::_process_entries()`: グルーピングキーを `end` → `(start, end)` に変更。同一end・異なるstart（例: Q3単独 vs Q1-Q3累計）を誤って重複扱いしYTDを破棄していた不具合を修正
- `common/sec_data/normalizer.py`: 3段階修正
  - `_ytd_to_quarterly`: チェーン先頭がYTD（起点Q1未申告）の場合、その値自体は未解決として分離しつつ差分計算の起点には使用
  - `_build_missing_quarter_implied_entries` 新設: 複数累計候補（6ヶ月YTD・9ヶ月YTD等）から欠落四半期を逆算、重複導出も排除
  - passthrough（生SA）優先の重複排除、未解決YTD残骸の最終除去
- 検証: pytest全123件パス。CON FY2023はQ1〜Q4復元、年次値との乖離0%に解消
- 影響範囲確認（既存96銘柄の raw/normalized データは未再生成）: 101銘柄中87銘柄に差分。うち2023年以降の直近データに影響する14銘柄
  （AMD, AMZN, APGE, AVAV, CIX, CON, ESTC, GEV, HEI, HWM, PM, RCAT, SOUN, ZS）を特定。
  CON・HEI・ZSをスポット検証し、いずれも旧コードの誤り（疑似四半期・二重計上）を修正したことを確認
  （例: HEI CapEx旧Q3=$23.33M〈Q2+Q3混入〉→新Q3=$12.26M、Q1〜Q4合計が年次と完全一致）
- 残タスク: BACKLOG.mdに [ARCH-DATA-1-YTD] として、全銘柄再生成前のスポットチェック・before/after全件差分の手順を記録済み

---

### ✅ [MINERVINI-NOTE-1] ミネルヴィニ4銘柄のregistration_note詳細化（2026-07-02 完了）
- commit: 0b67a6a62
- WST/APGE/CON/SNのregistration_noteに、moomoo AIスクリーニングが簡易版（株価・出来高ベースのテクニカル条件のみ）であり、
  本来の条件であるRS Rating・EPS/売上成長率の加速が未評価である旨を明記
- SNは既存の「tanuki=false一時的措置」注記を保持したまま追記

---

## 2026-07-01（完了）

### ✅ [PREVENT-4] system_health.pyの監視対象拡充（2026-07-01 完了）
- check_f_tail: 全thesis銘柄（9件）のctrl/latest.json存在確認
- check_g_hypecore: poc.json全件のInf/NaN混入チェック＋generated_at鮮度確認（14日閾値）
- check_h_config: tanuki=trueのbeta_config未登録・segment/maturityの孤立エントリ検出
- check_i_eps: summary.jsonの鮮度（14日閾値）＋eps=trueカバレッジ確認
- 実行結果: F/G/I=✅（正常）、H=⚠️（QBIT孤立エントリ検出: segment_config.json・maturity_config.json）

---

### ✅ [EXTREME-FEAR-1] extreme-fear/index.html 正式登録（2026-07-01 完了）
- **重複削除**: F&Gゲージカード（① F&G INDEX）・ステータスバナー・renderFG/renderBanner/fgLabel/gaugeSVG を削除
- **独自機能4つを保持**: ① 買い候補 TOP10 / ② 投入額シミュレーター / ③ 過去EF一覧 / ④ 買い付け方針メモ
- **共通化**: site-theme.css・site-header.js・site-nav.js を適用、`data-tool="ef"` 追加
- **nav 登録**: site-nav.js に `key:'ef'` エントリを Market Pulse の直後に追加
- **site-header.js**: `'ef'` ツール定義を TOOL_META に追加（タイトル: EXTREME FEAR / サブタイトル: 買付支援・Macro Buy Signal）
- **site-theme.css**: `body[data-tool="ef"] { --acc: #f43f5e; }` を追加（恐怖赤アクセント）
- **SYSTEM_MAP.md**: Extreme Fear をシステム一覧に追記、site-header.js 適用ページ一覧を更新

---

### ✅ [EPS-BX-1] BXのEPS ANALYZERでfetch失敗リスク解消（2026-07-01 完了）
- `config/cik_lookup.csv`: BX の eps フラグ true → false（TANUKI-FIN-1で金融機関向けDDM実装まで保留）
- `docs/value-monitor/adjusted_eps_analyzer/data/summary.json`: BXエントリを直接削除（generate_summaryがマージ方式のため手動削除が必要）
- 結果: summary.json が95→94銘柄。EPS ANALYZER一覧からBXが除外された。

**追記（2026-07-11）:** BX自体がcik_lookup.csvから登録抹消された（コミット`8dde36fdc`）ため、
本エントリの「TANUKI-FIN-1で金融機関向けDDM実装まで保留」という判断自体が対象消滅した。

---

### ✅ [DUPONT-COLOR-1] DuPont ROE色分け統一（2026-07-01 完了）
- `docs/value-monitor/tanuki_valuation/stock.html` L1539: `> 0.15 ? 'var(--green)' : > 0 ? 'var(--txt)'` → `>= 0.15 ? '#4ade80' : >= 0 ? '#facc15'` に変更。赤も `var(--red)` → `#f87171` に変更。
- `docs/common/glossary.json`: `tscore_dupont_roe_color` キーの「オレンジ」表記を「黄」に修正（実装色 #facc15 と一致させる）
- 統一後: tanuki_score/index.html と stock.html の両方で 0〜15%=黄、<0%=赤、15%以上=緑 に統一。

---

### ✅ [QBIT孤立エントリ削除] QBIT残骸config3ファイル削除（2026-07-01 完了）
- PREVENT-4のcheck_hが検出したQBIT孤立エントリ（QBTSの旧ティッカー残骸）を削除
- 削除ファイル: `config/segment_config.json` / `config/maturity_config.json` / `src/value/tanuki_valuation/kpi_config.py`
- 再実行結果: `[H] Config: ✅ 整合OK` に改善。repo全体でQBIT参照ゼロ確認済み

---

### ✅ [STOCK-GLOSSARY-1] stock.htmlへのglossaryツールチップ導入（2026-07-01 完了）
- stock.html末尾に `../../common/info-tooltip.js` をimport追加
- DuPont card関数に第5引数 `infoKey` を追加し、ROEカードのラベルに `data-info="tscore_dupont_roe_color"` を付与
- αステップ内Phase1スパンに `data-info="stock_moat_phase1"` を付与
- glossary.json に `stock_moat_phase1` キーを新規追加（Moat Score由来のPhase1期間算出ロジックの説明）

---

## 2026-06-27（完了）

### [TAIL-PAGE-1] TANUKI TAIL 詳細ページ別ページ化
**完了日:** 2026-06-27
**分類:** 機能追加 / TANUKI TAIL

#### 実施内容
- docs/portfolio/tail/detail.html を新規作成
- タブ廃止・全情報を縦スクロール1ページに統合
- 構成: サマリーバー / 投資テーゼ（折りたたみ）/ 最新レビュー+KPIトレンド（左右並列）/ AI視点+DCFシナリオ（左右並列）/ 内部統制 / 過去レビュー履歴
- 銘柄切り替えナビ（prev/next）・SHA-256認証・site-nav.js統合
- index.htmlの「詳細」ボタンをdetail.html?ticker=XXXへのリンクに変更
- DCF将来株価テーブル・過去レビュー前期比デルタ表示・KPI赤枠ハイライト実装

---

### [BUG-CTRL-EFFECTIVE-1] sec_ctrl_fetcher.py effective判定ロジック修正
**完了日:** 2026-06-27
**分類:** バグ修正 / TANUKI TAIL

#### 原因
_RE_EFFECTIVEの正規表現が "were effective" の直接隣接のみを想定していたため、
"were, in design and operation, effective" のように間に語句が入るPLTR等のケースで
effective=Noneになっていた。

#### 対応
_RE_EFFECTIVEに "were\s+.{0,60}\beffective\b" パターンを追加。
既存9銘柄のctrlデータを再判定・更新（PLTR: None→True）。

---

### [TAIL-UX-1-P1] TANUKI TAIL詳細モーダル ダッシュボードタブ追加（Phase1）
**完了日:** 2026-06-27
**分類:** UX改善 / TANUKI TAIL

#### 実施内容
- 詳細モーダルにダッシュボードタブを先頭に追加（既存6タブは維持）
- ゾーンA: 乖離率・理論株価・現在株価・直近スコア+判定を1行表示
- ゾーンB: 最新レビュー概要（左）＋スコア推移スパークライン（右）の2カラム
- ゾーンC: KPIトレンド小型グラフ（左）＋DCFシナリオ簡易テーブル（右）の2カラム
- ゾーンD: AI視点・内部統制を折りたたみで表示
- KPI・DCF・ctrlのキャッシュ済み即時再描画対応
- データなしKPIの非表示対応
- COREテーブルに「直近スコア」列を追加

#### 残課題（TAIL-UX-1として継続）
- スコア推移グラフのX軸右端が切れる
- その他一覧性向上の改善余地あり

---

### [CN-ENB-1] company_names.jsonのENB残存クリーンアップ（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `docs/common/company_names.json` から `"ENB": "ENBRIDGE INC"` エントリを削除
- TANUKI-ENB-1（2026-06-26）でENBをカナダ企業として除外済み、company_names側の残骸を除去

---

### [RKLB-CLEANUP-1] RKLBのtickers.json残存・eps_sector空欄修正（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `docs/value-monitor/tanuki_valuation/data/tickers.json` から RKLB エントリを削除（tanuki=false銘柄）
- `config/cik_lookup.csv` の RKLB の eps_sector に `宇宙・航空` を設定

---

### [PICK-DUP-1] daily_pick.pyの同日重複エントリバグ修正（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `daily_pick.py` の history 書き込み前に同日エントリ削除処理を追加（`[e for e in history if e.get("date") != today_str]`）
- `docs/value-monitor/tanuki_score/history.json` の既存重複を除去（25→11件、同日は最新1件を保持）

---

### [TTM-NULL-1] ttm_calculator.pyのval=None TypeErrorガード追加（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `ttm_calculator.py` の2箇所（FLOW_FIELDS合算・Q4合成top3合算）で `sum(e["val"] for e in ...)` → `sum(e["val"] or 0 for e in ...)` に修正
- pytest TestTTMNullValGuard（2テスト）を追加して回帰防止

---

### [STONKS-DIV-1] analyzer.pyのゼロ除算ガード確認・テスト追加（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- 調査の結果、3箇所（r_start/rev/avg_past）はすでにガード済みと判明（実装修正不要）
- pytest TestStonksDivisionGuards（2テスト）を追加してガードの継続的動作を担保

---

### [PREVENT-1] CLAUDE_CODE_START.mdチェックリスト追記（2026-06-27クローズ）

**完了日:** 2026-06-27（追記は前セッションで実施済み）
**対応内容:**
- 「新規計算フィールドを追加した場合、report_consistency_check.pyにCHECKを追加」項目が CLAUDE_CODE_START.md L697 に既実装
- BACKLOG から削除

---

### [PREVENT-2] CLAUDE_CODE_START.mdチェックリスト追記（2026-06-27クローズ）

**完了日:** 2026-06-27（追記は前セッションで実施済み）
**対応内容:**
- 「新規フィールド追加時の全画面grepで確認」「廃止機能の残骸grep確認」「複数銘柄への横展開確認」項目が CLAUDE_CODE_START.md L698-702 に既実装
- BACKLOG から削除

---

### [PREVENT-3] pytestの対象拡充（Inf/None/ゼロ除算）（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- TTM-NULL-1対応時に `tests/test_pipeline_logic.py` へ TestTTMNullValGuard（2テスト）を追加
- STONKS-DIV-1対応時に TestStonksDivisionGuards（2テスト）を追加
- HYPE-INF-1対応時に hypecore.py の rev_ttm_prior=0 時 Inf 非発生テストを追加
- pytest 119 → 123 件、全件パス確認済み
- 当初3件とも未カバーだったが、各バグ修正と同時にテスト追加することで対応完了

---

### [SEC-CTRL-1] ctrl JSONパス変更・Grok翻訳追加・既存ファイルマイグレーション（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `src/tail/sec_ctrl_fetcher.py`: 保存先を `{TICKER}_ctrl.json` → `{TICKER}/{QUARTER}.json` + `{TICKER}/latest.json` に変更
- `_translate_item4()` 関数を追加: Grok API（grok-3-mini→grok-3→grok-2-1212フォールバック）でitem4_excerptを日本語訳し `item4_excerpt_ja` フィールドとして保存
- `docs/portfolio/tail/index.html`: fetchパスを `latest.json` に変更、`buildTabCtrl` で日本語訳を上部に表示し英文を `<details>` 折りたたみに変更
- 既存9ファイル（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/SOUN/TSLA）を新ディレクトリ構造へマイグレーション
- `SYSTEM_MAP.md`: パス記述を新構造に更新

---

### [TAIL-CTRL-JA-1] TANUKI TAIL 内部統制タブ：日本語翻訳＋履歴表示
**完了日:** 2026-06-27
**分類:** 機能追加 / TANUKI TAIL

#### 実施内容
- sec_ctrl_fetcher.py: Grok翻訳フィールド（item4_excerpt_ja）追加、保存構造を {TICKER}/{QUARTER}.json + latest.json + index.json の3ファイル構成に変更
- 既存9銘柄（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/SOUN/TSLA）のctrlデータを新構造に移行し、Grok翻訳を一括適用（18ファイル）
- index.html buildTabCtrl: 日本語訳を上部に表示・英文原文を<details>折りたたみに移動、履歴セレクター追加（2期以上の場合のみ表示）
- SYSTEM_MAP.md: ctrlデータパス記述を新構造に更新

#### コミット
0e7eb2518

---

### [TAIL-CTRL-TRANS-1] TANUKI TAIL 内部統制タブ：日本語翻訳＋履歴表示
**完了日:** 2026-06-27
**分類:** 機能追加 / TANUKI TAIL

#### 実施内容
- sec_ctrl_fetcher.py: Grok翻訳(_translate_item4())を追加し item4_excerpt_ja フィールドを生成
- 保存構造を {TICKER}_ctrl.json（1ファイル上書き）から data/ctrl/{TICKER}/{QUARTER}.json + latest.json + index.json に変更
- 既存9銘柄（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/SOUN/TSLA）を新構造に移行し翻訳を一括追加（18ファイル）
- index.html buildTabCtrl: 日本語訳を上部表示・英文原文を折りたたみに変更、履歴セレクター追加（2期以上で表示）
- SYSTEM_MAP.md: ctrlデータパス記述を更新

#### 補足
- 翻訳はGrok APIで生成。既存ファイルに item4_excerpt_ja が存在する場合は再翻訳スキップ
- 履歴セレクターは現状1期分のみのため非表示。次回fetch後2期分になると表示される

---

## 2026-06-26（完了）

### [TAIL-SAT-CORE-1] satelliteモーダルをcore同等の6タブ構成に変更（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `TABS_SAT = ['戦略']` → `['テーゼ', '最新レビュー', 'KPIトレンド', 'DCFシナリオ', 'AI視点', '内部統制']` に変更
- `openModal()` 内の KPI・DCFシナリオ・ctrl fetch から `isCore &&` 条件を除去
- `renderModalBody()` の `!isCore` early return と `isCore` 変数を削除してタブ分岐を統一
- CRWV（satellite）で内部統制タブが表示され、effective=False / MW=12件を確認可能に
- PLTR/SOFI（core）の6タブが引き続き正常表示されることをPlaywrightで確認

---

### [CATALYST-DATA-1] catalyst.json初回データ投入（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `catalyst.py --all` で全95銘柄（hypecore=true）のカタリストを一括生成（Grok API使用）
- 登録銘柄数: 95銘柄 / カタリスト総数: 682件
- 上位: TSLA(9件), FLYW(9件), NVDA(8件), AAPL(8件), ALAB(8件)

---

### [DISCOVER-THEMES-1] macro_themes_history.json初回生成・.gitattributes登録（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `explore_macro_themes()` を直接呼び出して初回エントリを生成（Grok API使用）
  - collect.py は日曜のみ生成する設計のため、バイパス用スクリプトで実行
- 生成テーマ3件: 「AI電力需要爆発」[高]、「量子コンピューティング商用化」[中]、「LEO衛星通信拡大」[中]
- `.gitattributes` に `merge=ours` を追加（discover/data/catalyst.jsonの直後）
- 「過去のテーマを見る」機能が稼働状態に

---

### [HYPE-FLAG-1] CSGP/ZSのcik_lookupフラグ設定（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- CSGP（CoStar Group、Real Estate、黒字）: `hypecore=true, tanuki=true, eps=true, stonks_silo=false`
  - beta_config.jsonにβ=0.72が既存 → pipeline.pyを実行してlatest.json生成（理論株価$9.87）
- ZS（Zscaler、Technology/Software-Infrastructure、赤字）: `hypecore=true, tanuki=false, eps=false, stonks_silo=true`
  - stonks-silo pipeline を実行してresults.jsonに追加（score=88.0、10x_CANDIDATE）

### [HYPE-ENB-1] ENBのhypecore=false修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- ENBの `hypecore=true` → `false` に修正（カナダ企業・TANUKI-ENB-1で永続除外決定済み）
- 他フラグ（tanuki/eps/stonks_silo=false）は現状維持

---

### [SEC-CTRL-2] TANUKI TAIL内部統制データ未取得銘柄の一括生成（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `sec_ctrl_fetcher.py` を残8銘柄（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/TSLA）に実行
- 全9銘柄の ctrl データが揃い TANUKI TAIL の内部統制タブが全銘柄で表示可能に
- 注目: CRWV のみ `not_effective / MW=12`（重要な欠陥あり）、PLTR は `unknown`（判定不能）

### [HYPE-INF-1] HypeCoreのpoc.jsonにInf値が混入するバグ修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `rev_ttm_prior` の 0 を `np.nan` に変換（0除算による `rev_yoy=inf` を防止）
- `op_margin` の `rev=0` を `np.nan` に変換（`ni/0=-inf` を防止）
- `safe()` 関数に `np.isinf(v)` チェックを追加（JSON出力前の Inf→None 変換）
- `z_score_series()` 入力 Series の `inf/-inf` を `np.nan` に置換（スコアへの伝播防止）
- ASTS/JOBY を再生成して Inf 値 0 件を確認（ASTS 9件・JOBY 3件が解消）

### [STAGE0-STOCK-1] stock.htmlでstage=0（S0失望期）が非表示になるバグ修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `STAGE_LABELS` に `0:'失望/蓄積期'` を追加
- falsyチェック（`hStage ?`）をnullチェック（`hStage != null ?`）に変更
- 現時点で stage=0 の実績データなし（全期間スキャン済み）。コード修正のみ実施。

### [ALPHA-REDESIGN-2] stock.htmlのα乗算残存修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `calcSensIV()` から `(1+alpha)` 乗算を除去（感度分析テーブルの2倍過大表示を修正）
- `renderChart()` の `alphaPremium` 計算・「α プレミアム」バーを削除
- CALCULATION BREAKDOWN Step 7 ヘッダーを `×(1+α)` 表示 → `Phase1: N年（Moat Score由来）` に変更
- Step 7 説明文・P_t 計算式・P_t 企業価値表示から `(1+α)` を除去
- `applyLayer2Toggle()` の pt 計算から `(1+alpha)` を除去

### [EVAL-3] Moat Scoreスクリーニング画面への組み込み（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- tanuki_valuation/index.html にMoat Score列を追加（乖離率の隣、ソート対応）
- α列を削除（ALPHA-REDESIGN-1で廃止済みの残骸）
- stats barの「平均α」→「平均Moat」に変更
- RKLBのlatest.jsonを再生成（moat_score欠落を解消）
**結果:** 94銘柄中94銘柄にmoat_score表示。スコア範囲0.00〜0.95、平均0.33。

### [ALPHA-REDESIGN-1] alpha乗算廃止・Moat Score駆動Phase1期間自動算出（2026-06-26完了）

**概要:** DCFの `v0*(1+alpha)` 乗算を廃止し、企業の競争優位性（Moat Score）から
Phase1期間を自動算出する方式に切り替えた。alphaは参照値としてJSONに保持。

**実装内容:**

- `calculator/adjustments.py`
  - `MoatScoreResult` dataclass を追加
  - `calculate_moat_score()` を追加
    - Moat Score = `gross_margin_norm×0.40 + roic_norm×0.40 + fcf_margin_norm×0.20`
    - 正規化基準: GM=100%、ROIC超過=(roic-Rm)/30%、FCF=30%
    - Phase1 years = `3 + round(moat_score × 7)`（範囲: 3〜10年）
  - `calculator/__init__.py` に `calculate_moat_score, MoatScoreResult` をexport

- `core_calculator.py`
  - STEP 4e 追加: `financials` から `moat_gross_margin_3yr/moat_roic/moat_fcf_margin_3yr` を読んで `calculate_moat_score()` を呼び出し
  - three_stage/two_stage DCF、WACC感度分析、シナリオ計算、将来価値計算の全 `phase1_years`/`high_growth_years` を `_moat_phase1_years` に統一
  - `calculate_intrinsic_value(..., alpha=0.0)` に全箇所を変更
  - 結果dictに `moat_score/moat_phase1_years/moat_gross_margin_norm/moat_roic_norm/moat_fcf_margin_norm` を追加

- `pipeline.py`
  - `_calc_moat_inputs()` を追加: normalized quarterly JSONからGM 3年平均、annual JSONからFCF margin 3年平均を算出
  - `calculate_pt()` 呼び出し前に `financials.update(_moat_inputs)` でmoat入力を注入
  - ROIC: `rice.roic_wacc_ratio × 0.10` を `moat_roic` として渡す

**動作確認結果（2026-06-26実行）:**

| 銘柄 | Moat Score | Phase1 | IV (変更後) | upside | 判定 | 旧alpha | 変化メモ |
|------|-----------|--------|-------------|--------|------|---------|---------|
| NVDA | 0.892 | 9yr | $648.50 | +231.4% | WATCH | 1.0 (cap) | alpha廃止で非乗算化。Phase1 5yr→9yr拡張で相殺 |
| PLTR | 0.641 | 7yr | $89.40 | -16.9% | WATCH | 0.0 | Phase1 5yr→7yr延長によりIV増加 |
| MSFT | 0.713 | 8yr | $381.76 | +7.3% | WATCH | 1.0 (cap) | alpha廃止（v0×2.0→v0）でIV大幅減 |
| IONQ | 0.000 | 3yr | $41.84 | -18.2% | WATCH | 0.0 | GM/ROIC/FCF全0→最短Phase1。upside低下 |

**pytest:** `tests/test_pipeline_logic.py` 119件 全パス（2026-06-26確認）

**変更ファイル:**
- `src/value/tanuki_valuation/calculator/adjustments.py`
- `src/value/tanuki_valuation/calculator/__init__.py`
- `src/value/tanuki_valuation/core_calculator.py`
- `src/value/tanuki_valuation/pipeline.py`

### [SS-1] Stonks Silo 営業利益ETA四半期系列合成
**完了日:** 2026-06-26
**判断:** 現状維持でクローズ
**理由:**
- NET・IONQの営業利益はQ1 2026時点で全8四半期赤字かつ悪化傾向
  （NET: -62M$、IONQ: -272M$）
- 「改善トレンドなし」表示は正しい判定であり、無理にETAを出すと誤情報になるリスクがある
- 機能上の欠落ではなく仕様通りの動作と確認

### [TANUKI-ROE-2-PARTIAL] DuPont分析パネルをstock.htmlに追加
**完了日:** 2026-06-26
**対応内容:**
- FINANCIAL HEALTHセクション直後にDUPONT ANALYSISパネルを追加
- 4カード構成：純利益率・資産回転率・財務レバレッジ・ROE（分解値）
- ROEは値に応じて色分け（>15%緑・>0%白・負値赤）
- dupont フィールドがない銘柄は非表示
**残タスク:** 業種平均比較・潜在ROE試算はデータソース確保後に別途実装

### [MP-ASSETFLOW-UI-1] 資産クラス資金フロービジュアライザーUI調整
**完了日:** 2026-06-26
**対応内容:**
- short_bond tickerを^IRXからDGS3MOに統一
- スペクトルバーの高さを3px→8pxに変更
- fallback ※マークは実装済みのため現状維持

### [SILO-UX-1] 黒字化チャート達成済みラベル追加
**完了日:** 2026-06-26
**対応内容:**
- buildProfitPath() で state === 'done' の指標ドット右に「✅ 達成済」ピルを追加
- 表示対象: 粗利益・FCF等、直近Q値が黒字の指標
- スタイル: 緑色背景・緑テキスト（var(--grn)）
**背景:** 達成済み指標と未達指標が混在するチャートでどれが達成済みか不明瞭だったUX問題を解消

---

## 2026-06-25（完了）

### [HYPE-1] HypeCoreフェーズ判定の精緻化 — 完了（2026-06-25）
- `run_poc()` に `s4_streak`（S4連続月数）を追加し `determine_stage()` に渡すよう変更
- `determine_stage()` にS4脱出条件を追加: `s4_streak>=6 AND rev_yoy>20 AND ni_yoy>0` → S2へ脱出
- `detect_substage()` にS4長期継続ラベルを追加: `stage_months>=6 AND real_strong` → "長期調整・実体強"
- PLTR: 2026-04が"長期調整・実体強"（6ヶ月目）、2026-05でS2脱出に変更。NVDA: 影響なし
- 変更ファイル: `src/value/hypecore/hypecore.py`

## 2026-06-25（廃止）

### [RICE-2] CF_adjのMatrix判定への組み込み — 廃止（2026-06-25）
理由: 設計再検討の結果、実装不要と判断。削除。

---

## 2026-06-25（TANUKI-MAXEPS-1）

### [TANUKI-MAXEPS-1] 最大EPS計算・TANUKI SCORE表示（2026-06-25完了）
対応内容:
- `src/value/tanuki_valuation/pipeline.py` に max_eps / max_eps_per / max_eps_reliability の計算・格納を追加
  （max_eps = (GAAP NI TTM + SBC TTM) / 希薄化後株式数、一過性損失は将来拡張）
  - GAAP NI TTM ソース: `dupont.ni_ttm`（quarterly TTM集計）
  - SBC TTM ソース: `financial_health.sbc_ttm`（annual最新年SBC）
  - 株式数ソース: `components.diluted_shares`
  - HIGH: 3フィールド全取得 + max_eps > 0
  - MED: ni_ttm か sbc_ttm の一方欠落、ゼロ代入で近似計算
  - LOW: 2フィールド以上欠落 または max_eps <= 0
- `docs/value-monitor/tanuki_score/index.html` の詳細テーブルに3列を追加
  - GAAP PER: `components.per`（既存チップバッジの値をテーブルにも表示）
  - 最大EPS PER: `components.max_eps_per`（信頼性LOW時 opacity:0.45 でグレーアウト）
  - 乖離: GAAP PER − 最大EPS PER（正値=オレンジ表示、SBC依存度を可視化）
- NVDA実行確認: max_eps=6.8535, max_eps_per=29.0x, reliability=HIGH
  （GAAP PER 30.4x との乖離 +1.4x: SBCが純利益比4%と小さいためギャップ小）

---

## 2026-06-25（小規模ロジック系 一括対応）

### [MP-WEEKEND-1] 休場日（土日）ラベル追加（2026-06-25完了）
対応内容: `docs/market-monitor/market-pulse/index.html` の `renderAssetFlow()` を改修。
ワークフローは既に `cron: "35 21 * * 1-5"` で月〜金のみ実行済みのため、フロントエンドで補完。
- 取引日間に土日がある場合、「休場」行をグリッドに挿入
- 今日が土日の場合、最新取引日より前に当日を含む休場行を先頭表示
- 休場行は背景 `var(--sur2)` + 不透明度0.5で視覚的に区別

### [MP-CSV-1] CSVヘッダー整合チェック（2026-06-25完了）
対応内容: `src/market/market_pulse/collect_and_send.py` の `save_data_to_json_and_csv` 関数の
CSV書込み前にヘッダー整合チェックを追加。
- 既存CSVを読込み、先頭行のヘッダーを `CSV_COLUMNS` と比較
- 不一致の場合、全データ行を読込んで新ヘッダーで全体再書込み
- `extrasaction='ignore'` により旧カラム値は破棄、新カラムには空値が入る

### [HYPE-DISP-5] HypeCore グラフX軸整列改善（2026-06-25完了）
対応内容: `docs/value-monitor/hypecore/detail.html` の Chart.js 設定を修正。
- `eChart`（期待の強度）の左Y軸に `afterFit: ax => { ax.width = 55; }` を追加
- `eChart` の右Y軸（y2）に `afterFit: ax => { ax.width = 30; }` を追加
- `fChart`（実体の強度）の左Y軸にも同様の `afterFit` を追加
- `fChart` に不可視ダミー右Y軸（`ticks/grid/border: {display:false}`, `width=30`）を追加
- 両グラフのプロット幅が統一され、X軸の時間目盛りが縦に揃う

---

## 2026-06-25（表示統一系 一括対応）

### [HOME-COLOR-1] ツールカードのテーマカラー修正（2026-06-25完了）
対応内容: `docs/index.html` の `.card-score` アクセントカラーを `#14b8a6`（シアン）→ `#84cc16`（ライム）に変更。
色相環の最大空白（MACRO PULSE H=38° ～ MARKET PULSE H=160°、122°のギャップ）の中点 H=82° に配置し、
隣接色との最小距離44°を確保。全9色が色相環上でより均等に分布するよう改善。

### [TSCORE-DISP-1] `—` と `N/A` の表示統一（2026-06-25完了）
対応内容: `docs/value-monitor/tanuki_score/index.html` を調査した結果、コード全体で `N/A` 表記は使用されておらず
すべて `—` に統一済みであることを確認。`pct()` 関数に `typeof v !== 'number' || !isFinite(v)` の防衛チェックを追加し、
数値以外の値（文字列・NaN等）が渡された場合も `—` を返すよう強化。

### [TSCORE-DISP-2] JOBY・ASTSのフェーズ欄空欄修正（2026-06-25完了）
対応内容: `docs/value-monitor/tanuki_score/index.html` の `stageLabel()` 関数を修正。
`stage=0`（未フェーズ）・`stage=null`・範囲外（1〜4以外）の場合に明示的に `—` を返すよう変更。
従来のコードは `stage=0` で空文字列が生成される可能性があったため、これを防ぐ。

### [TSCORE-DISP-3] RICEマトリクスY軸ラベルの可読性改善（2026-06-25完了）
対応内容: `docs/value-monitor/tanuki_score/index.html` のSVG Y軸ラベルを
`transform="rotate(-90,...)"` の縦書きから横書きに変更。
プロット左上に `↑ RICE`（font-size:10）と `対数軸`（font-size:8）の2行ラベルを配置。

### [DISCOVER-DISP-3] 新規候補カードのタグ視認性改善（2026-06-25完了）
対応内容: `docs/discover/index.html` のタグCSSを全面改善。
- `.screen-pass`: alpha `.08` → `.15`、`border:1px solid` 追加、文字色 `#10b981` → `#34d399`
- `.conv-低`: 文字色 `#64748b`（低コントラスト）→ `#94a3b8` に変更、border追加
- `.cand-catalyst` / `.conv-高` / `.conv-中`: alpha `.12` → `.20`、border追加で視認性向上

### [MP-DISP-5] 資産クラス並び順の視覚的勾配追加（2026-06-25完了）
対応内容: `docs/market-monitor/market-pulse/index.html` の `renderAssetFlow()` に
グラデーションバー（高さ3px、青→シアン→紫→緑→アンバー→オレンジ→赤）を追加。
グリッド右側の7データ列に対応する幅で描画し、「安全資産→リスク資産」の方向を視覚的に表現。

---

## 2026-06-25（実装）

### [TAIL-DISP-3] SATELLITE一覧「戦略名」の表記揺れ修正（2026-06-25完了）
対応内容: `docs/portfolio/tail/data/positions/CRWV_thesis.json` および
`SOUN_thesis.json` の `strategy_name` フィールドを
「グロース追及」→「グロース追求」に修正。HTML/JSファイルに該当箇所なし。

### [HOME-ANIM-1] LIVEドットのパルスアニメーション統一確認（2026-06-25完了）
対応内容: `docs/index.html` の全9カードを調査した結果、
すべてのカードに `class="dot dot-live"` が一貫して適用されており、
`@keyframes live` パルスアニメーションは混在なし・統一済みであることを確認。
修正不要のため変更なし。

### [MP-DISP-6] AI分析末尾の俳句的フレーズ削除（2026-06-25完了）
対応内容: `src/market/market_pulse/collect_and_send.py` のGrokプロンプトから
「最後に俳句を一句（5-7-5）のみ添えること」の指示を削除し、
代わりに「末尾に俳句・詩的フレーズ・文学的な一文を添えることは禁止。総評の最終文は具体的な相場シナリオで終えること」という禁止文を追加。
既存データ（`market_data.json` の `summary` フィールド末尾に残る俳句）は次回ワークフロー実行時に自動更新される。

### [CATALYST-1] カタリスト発掘・追跡機能
完了日: 2026-06-25
対応内容:
- `src/discover/catalyst.py` 新規作成（Grok Web検索で銘柄ごとにカタリスト発掘・週次再評価）
  - 対象: `get_hypecore_tickers()` 経由 cik_lookup.csv の hypecore=true 94銘柄
  - 呼び出し①: 新規カタリスト発掘（grok-3 web検索）
  - 呼び出し②: 既存「未達」カタリストの再評価（status: 未達/達成済み/消滅）
  - ID採番: `{TICKER}-{YYYY}-{3桁連番}` 形式、冪等（再実行で積み上げ）
  - `--ticker`/`--all`/`--dry-run` オプション対応
- `docs/discover/catalyst.html` 新規作成
  - 重要度・種別・ステータス・銘柄テキストフィルター
  - 未達カタリストを上位表示、達成済み/消滅は折りたたみ
  - ステータス色分け: 未達=青、達成済み=緑、消滅=グレー
  - site-header.js + site-nav.js 使用
- `docs/common/site-nav.js`: 「カタリスト」エントリをニュース履歴の直後に追加
- `.github/workflows/Catalyst_Update.yml` 新規作成（毎週日曜 JST 23:30）
- `.gitattributes`: `docs/discover/data/catalyst.json text eol=lf merge=ours` を追加

---

## 2026-06-25（廃止）

🗑️ [Short report contrarian戦略] 廃止・関連ファイル一括削除（2026-06-25）
- 戦略コンセプト: ショートセラーレポート（Hindenburg等）公開直後の逆張りロング
- バックテストv4まで完了していたが、本番運用には至らず廃止
- 削除ファイル（10件）:
  - `.github/workflows/short_report_monitor.yml`（毎営業日 JST 7:18 定期実行ワークフロー）
  - `src/subport/short_report/news_bot.py`
  - `src/subport/short_report/notify.py`
  - `src/subport/short_report/position_manager.py`
  - `src/subport/short_report/screener.py`
  - `src/subport/short_report/config.json`
  - `src/subport/short_report/requirements.txt`
  - `src/subport/short_report/state.json`
  - `src/subport/short_report/processed_content.json`
  - `src/subport/short_report/README.md`

---

## 2026-06-25（実装）

✅ [DISCOVER-FEATURE-1] ニュース履歴保存・閲覧機能（2026-06-25完了）
- **`src/discover/collect.py`** に3関数を追加
  - `get_price_change(ticker)`: yfinance で直近2営業日の終値比騰落率（%）を取得
  - `add_price_changes_to_yesterday(now_jst)`: 前日分の `news_history_YYYY_MM.json` を読み込み、各銘柄・各itemに `price_change_next_day` を追記して上書き保存
  - `append_to_monthly_history(results, now_jst)`: 当日分の分類結果を `docs/discover/data/news_history_YYYY_MM.json` に追記（同日キーは上書き・冪等）
  - `main()` で `daily_report.json` 書き込み前に上記2関数を呼び出す
- **`docs/discover/news_history.html`** 新規作成
  - 月選択・銘柄フィルター付きニュース履歴閲覧画面
  - 日付降順・銘柄ごとに `price_change_next_day` を色付き表示（↑緑/↓赤/—グレー）
  - importance・category バッジ、URL付きタイトルリンク、summary・source 表示
  - `data-tool="news-history"` で site-theme.css のシアン accent を適用
- **`docs/common/site-nav.js`**: DISCOVER の次に `{ key: 'news-history', label: 'ニュース履歴' }` を追加（全ページのナビに波及）
- **`.gitattributes`**: `docs/discover/data/news_history_*.json text eol=lf merge=ours` を追加
- **`.github/workflows/Discover_Update.yml`**: pip install に `yfinance` 追加、git add に `news_history_*.json` 追加

✅ [ARCH-DATA-1一部] 年度判定の共通関数化（2026-06-25完了）
- `common/sec_data/utils.py` を新規作成し `determine_fiscal_year(end_date, fiscal_end_month)` を定義
- `common/sec_data/parser.py`: `_detect_fiscal_end_month()` メソッドを追加し、`_extract_values()` 内の `end_date[:4]` を `determine_fiscal_year` 呼び出しに統一。INTUガード（exactフラグ）は保持
- `src/value/adjusted_eps_analyzer/extract_key_facts.py`: 4か所のインライン `end.month > fiscal_end_month` 判定を `determine_fiscal_year` に置き換え
- `src/value/adjusted_eps_analyzer/pipeline.py` `aggregate_annual()`: `fiscal_year=None` フォールバック時に警告ログを追加（動作は維持）
- pytest 119件全通過確認済み

---

## 2026-06-24（実装）

✅ [MP-BIZDAY-1] MARKET PULSE 営業日ベース化（2026-06-24完了）
- `Market_Pulse_Update.yml` の cron を `* * *` → `* * 1-5` に変更（月〜金のみ実行）
- 土日はワークフロー自体をスキップ。前日比計算・フロントエンドの変更は不要（yfinanceが営業日のみ返すため前日比はすでに正しい）

✅ [SEC-CTRL-1] 内部統制評価機能 TANUKI TAIL 実装（2026-06-24完了）
- **`src/tail/sec_ctrl_fetcher.py`** 新規作成
  - EDGAR 10-Q「Controls and Procedures」(Part I Item 4) を取得・解析
  - Material Weakness / Significant Deficiency をregexで検出
  - 有効性 (effective: true/false/null) を判定して `docs/portfolio/tail/data/ctrl/{ticker}_ctrl.json` に保存
  - CLI: `python src/tail/sec_ctrl_fetcher.py [TICKER ...]`（無引数で全tail銘柄）
- **`docs/portfolio/tail/index.html`** 更新
  - `TABS_CORE` に `'内部統制'` (n=5) 追加
  - `openModal` に ctrl データのlazy load追加
  - `renderModalBody` で n===5 を `buildTabCtrl` へディスパッチ
  - `buildTabCtrl`: 有効性バッジ（緑/赤）、MW件数・スニペット、SD件数、Item4原文折りたたみ表示
- **`.github/workflows/TANUKI_TAIL_SEC_Ctrl.yml`** 新規作成（週次月曜 10:00 JST 自動実行）
- **SOUN検証**: MW=3種類（統制環境・複雑取引・職務分掌）を正常検出、effective=false確認

✅ [TSCORE-TRAP-1] 投資トラップ検出パネル Phase1+Phase2全件実装（2026-06-24完了）
- `docs/value-monitor/tanuki_score/index.html` に `renderTrapPanel()` を追加（DuPontパネル直後・`<details>` 折りたたみ形式）
- 6種をフロントエンドでリアルタイム計算: バリュー/グロース/バリューデスト/ナラティブ/サイクリカル/ワンタイム
- 🔴高/🟡中/🟢低/– で表示、ホバーで判定根拠ツールチップ、列ソート・0件非表示トグル実装
- Phase2実装（全4件）:
  - #7 アセットヘビー: asset_turnover近似（pipeline変更なし）
  - #4 ディビデンドトラップ: `data_fetcher.py`+`core_calculator.py` に dividend_yield/payout_ratio 追加
  - #2 シガーバット: `quarterly.py`+`parser.py` に CurrentAssets/CurrentLiabilities 追加 → `pipeline.py` で net_current_assets_ratio 計算
  - #10 キャッシュトラップ: `quarterly.py`+`parser.py` に Buyback 追加 → `ttm_calculator.py` FLOW_FIELDSに追加 → `pipeline.py` で buyback_ttm を financial_health に格納
- 最終TRAP_KEYS: バリュー/グロース/バリデスト/ナラティブ/サイクリカル/ワンタイム/シガーバット/配当/キャッシュ/アセット重（10種）

✅ [DAILY-PICK-BUG-1] daily_pick.jsonのtanukiキー欠落修正（2026-06-24完了）
- `main()` 内で `build_data_package()` を明示的に呼び出し、`output` 辞書に `"tanuki": data_pkg["tanuki"]` を追加
- `daily_pick.json` に `tanuki`（`fcf_conversion_rate` 等16フィールド）が正常出力されることを確認

✅ [MP-DISP-1] ゲージ数値ラベル配置不揃い修正（2026-06-24完了）
- **対象**: `docs/market-monitor/market-pulse/index.html`
- 全3ゲージ（メインセンチメント・CNN F&G・Tech Pulse）の FEAR/GREED/50 ラベルを弧の端点・頂点基準で `text-anchor="middle"` に統一
- メインゲージ: FEAR→(x=22,y=124)、GREED→(x=198,y=124)、50→(x=110,y=14) に修正
- ミニゲージ(CNN/Tech): FEAR→(x=18,y=106)、GREED→(x=162,y=106)、50→(x=90,y=12) に修正
- 左右が弧端点を中心とした鏡対称、「50」が弧頂点の外側に統一配置

✅ [EPS-DISP-5] 「調整内訳（全期間）」ページ長大化対策（2026-06-24完了）
- **対象**: `docs/value-monitor/adjusted_eps_analyzer/stock.html`
- **方式A採用**: 直近8四半期のみ表示 + 「全N件を表示 ▼」展開ボタン
- `buildAdjHtml()` を分離してHTML生成を共通化、`updateAllAdjustments()` で8件超の場合にボタンを追加
- `expandAllAdj()` でボタンクリック時に全件展開

✅ [EPS-DISP-4] グラフ軸ラベル・フォントサイズ統一（2026-06-24完了）
- **対象**: `docs/value-monitor/adjusted_eps_analyzer/stock.html`
- メインEPS推移チャート `scales.x/y ticks.font.size`: 10 → 11
- ウォーターフォールチャート `scales.x/y ticks.font.size`: 9 → 11
- 参照: market-pulse は12で統一。EPS は表示密度を考慮し11に統一

✅ [TSCORE-DISP-4] バックテストのデフォルト展開（2026-06-24完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- `#sv-body` の `display:none` を除去、矢印テキストを「▶ 展開して見る」→「▲ 折りたたむ」に変更
- データなし時は「データなし（pipeline.py 実行後に表示）」が自動表示されるため展開状態でも問題なし

✅ [EPS-DISP-3] 「投資機会ランキング」デフォルト展開（2026-06-24完了）
- **対象**: `docs/value-monitor/adjusted_eps_analyzer/index.html`
- `#opp-body` の `display:none` を除去、矢印テキストを「▲ 折りたたむ」に変更

✅ [EPS-DISP-2] BX会社名空欄補完（2026-06-24完了）
- **原因**: `config/cik_lookup.csv` に BX エントリが存在せず → `ticker_to_name["BX"]` が未定義 → pipeline が SEC metadata 名にもフォールバックできず空文字で保存
- `config/cik_lookup.csv` に BX 行を追記（CIK: 0001393818、name: Blackstone Inc.、eps: true）
- `docs/value-monitor/adjusted_eps_analyzer/data/summary.json` の BX エントリを即時パッチ（`company_name: "Blackstone Inc."`）

✅ [TSCORE-BT-1] バックテスト直近件数ラベル修正（2026-06-24完了）
- **実態**: 全銘柄の `score_history.json` を横断し、`date` 降順で最大20件を表示（`allEntries` 全銘柄横断・`slice(0,20)`）
- `recentRows` の前に `recentArr`（配列）を分離し、ラベルを `直近20件` → `直近${recentArr.length}件（全銘柄横断・判定日降順）` に修正
- **対象**: `docs/value-monitor/tanuki_score/index.html`

✅ [TSCORE-FIX-5] RICEマトリクス有効銘柄数の動的取得（2026-06-24確認・対応不要）
- 調査結果: `docs/value-monitor/tanuki_score/index.html` line 1119 で既に `${allPoints.length}銘柄` として動的実装済み
- コード変更なし

✅ [HOME-FIX-3] HYPECOREカード銘柄数の動的化（2026-06-24完了）
- `docs/value-monitor/hypecore/data/tickers.json` を新規作成（hypecore `ALL_TICKERS` と同一の60銘柄配列）
- `docs/index.html`: カード説明文・ステータスバッジの銘柄数を `<span id>` に変更し、fetch 後に書き換え
- 取得失敗時はステータスを空文字にフォールバック（`LIVE ·` のみ残る）

✅ [SOFI-DATA-1] SOFI LTDebt 正規化データ更新（2026-06-24完了）
- **⚠️ 2026-07-13追記**: 本エントリの手動パッチは、その後の`update.py`自動再生成
  （手動編集を経由しない標準パイプライン）で静かに巻き戻り、2026-07-13時点で
  LTDebtが2022-12-31のまま3年近くstale化していたことが判明した（Net_Debtが
  実際はnet cashであるにも関わらず+$2.08Bのnet debtとして表示され続けていた）。
  `ltdebt_concept`によるticker_restrictionsオーバーライドとして恒久修正済み。
  詳細は[[ARCH-DATA-1-PREP-1]]（本ファイル内、2026-07-13完了）参照。
- **対象**: `common/sec_data/normalized/SOFI_quarterly_normalized.json`・`docs/common/sec_data/normalized/SOFI_quarterly_normalized.json`
- **調査結果**: SOFI は銀行免許取得後（2022年以降）、`LongTermDebt` XBRL タグを報告しなくなった。代替タグ `DebtLongtermAndShorttermCombinedAmount`（短期+長期の合計社債）が SEC EDGAR に存在。
- **対応方針: B（カスタム概念使用）**:
  - `DebtLongtermAndShorttermCombinedAmount` は SOFI の senior notes（社債）を代表する最適タグ
  - 2023〜2026のデータを同概念から直接 normalized JSON に手動追記（`quarterly.py` フェッチスクリプトはフォールバック未対応のため手動パッチ）
- **追記したエントリ（13件）**:
  - 2023-03-31: $6.126B / 2023-06-30: $6.484B / 2023-09-30: $6.241B / 2023-12-31: $5.233B（倉庫ローン残存期）
  - 2024-03-31: $2.891B / 2024-06-30: $3.107B / 2024-09-30: $3.180B / 2024-12-31: $3.093B
  - 2025-03-31: $3.046B / 2025-06-30: $3.943B / 2025-09-30: $2.714B / 2025-12-31: $1.815B / 2026-03-31: $1.813B
- **注意**: 2023年前半は倉庫ファシリティ残存により $6B超（旧 `LongTermDebt` の2022値と同等）。2024-Q1以降は senior notes のみとなり ~$1.8〜3.2B に収束。

✅ [MP-LOGIC-2] BUY チェックリスト実装（2026-06-24完了）
- **対象**: `src/market/market_pulse/collect_and_send.py`・`docs/common/glossary.json`・`docs/market-monitor/market-pulse/index.html`
- `collect_and_send.py`:
  - `calc_buy_checklist()` 追加: F&G ≤ 25 で `triggered=True`、F&G ≤ 10 で `extreme=True`。3チェック×1pt（S&P500 200日MAシグナル・HYスプレッド縮小・ヒンデンブルグ非活性）。0〜1pt→WATCH / 2pt以上→BUY
  - `fetch_hy_spread_from_fred()` 拡張: `max_90d`（90日最高値）・`is_contracting`（`current < max_90d - 0.30`）を追加。`window = hy.iloc[-90:]` から `min()` / `max()` を同一ウィンドウで計算
  - `save_data_to_json_and_csv()` に `buy_checklist=None` 引数を追加し `new_entry` に `buy_checklist` キーとして保存
- `docs/common/glossary.json`: `buy_ma200`・`buy_hy_spread`・`buy_hindenburg` 追加
- `docs/market-monitor/market-pulse/index.html`:
  - `renderBuyChecklist()` 追加（TAKE PROFITカード直後・アセットフロー直前）
  - F&G > 25: グレーアウトテキスト表示
  - F&G ≤ 25 かつ `triggered=true` 時: action別カラーバナー（WATCH=アンバー/BUY=緑）＋3チェック項目（✅該当/❌非該当バッジ・pt・詳細行・glossaryツールチップ）＋買いポイント合計表示
  - F&G ≤ 10（`extreme=true`）時: セクションヘッダーを `pulse-red` アニメーション強調＋「🚨 Extreme Fear — 絶好の買い場の可能性」バナーを追加表示
  - `RENDER_ALL_FNS` に `renderBuyChecklist` を登録

✅ [MP-LOGIC-1] TAKE PROFIT チェックリスト実装（2026-06-24完了）
- **対象**: `src/market/market_pulse/collect_and_send.py`・`docs/common/glossary.json`・`docs/market-monitor/market-pulse/index.html`
- `collect_and_send.py`:
  - `_get_sp500_ma_deviation()`: `period="3mo"` → `"1y"` に変更。200日MA計算を追加し戻り値をdict化（`deviation_50`/`above_ma200`/`ma200_slope`）。傾き判定は MA200[today] vs MA200[10日前]（`close[-200:].mean()` vs `close[-210:-10].mean()`）。`compute_sentiment()` の呼び出し箇所を `deviation_50` を参照する形に更新
  - `fetch_hy_spread_from_fred()` 追加: FRED `BAMLH0A0HYM2`（ICE BofA US High Yield Index OAS）を120日分取得。`is_expanding = current > min_90d + 0.30`（30bps閾値）
  - ヒンデンブルグ簡易判定: `breadth_data.json` の `new_highs_52w` / `new_lows_52w` が各々 `500 × 2.2%`（11件）以上で `hindenburg_active = True`
  - `calc_take_profit_checklist()` 追加: F&G ≥ 75 で `triggered=True`。3チェック×1pt（S&P500 200日MAシグナル・HYスプレッド拡大・ヒンデンブルグ）。0〜1pt→HOLD / 2pt→PARTIAL / 3pt→TAKE PROFIT
  - `save_data_to_json_and_csv()` に `take_profit_checklist=None` 引数を追加し `new_entry` に `take_profit_checklist` キーとして保存
- `docs/common/glossary.json`: `tp_ma200`・`tp_hy_spread`・`tp_hindenburg` 追加
- `docs/market-monitor/market-pulse/index.html`:
  - `renderTakeProfit()` 追加（Tech Pulse〜アセットフロー間の `.sec` + `.unified-card` として配置）
  - F&G < 75 または `triggered=false` 時: グレーアウトテキスト表示
  - F&G ≥ 75 かつ `triggered=true` 時: action別カラーバナー（HOLD=緑/PARTIAL=アンバー/TAKE PROFIT=赤）＋3チェック項目（✅/❌バッジ・pt・detail行・glossaryツールチップ）＋利確ポイント合計表示
  - `escHtml()` ユーティリティを追加、`RENDER_ALL_FNS` に `renderTakeProfit` を登録

✅ [DISCOVER-FEATURE-3] テーマ内銘柄の役割分類表示（2026-06-24完了）
- **対象**: `src/discover/collect.py`・`docs/discover/index.html`
- `src/discover/collect.py`: `related_tickers` を文字列配列→オブジェクト配列に変更（`ticker`/`role`/`note` フィールド）。role定義（主要・ボトルネック・注目）と各役割の説明をプロンプトに明示
- `docs/discover/index.html`: `buildRelatedTickers()` ヘルパーを追加
  - 旧形式（文字列配列）→ `typeof rt[0] === 'string'` 判定で従来のシアンバッジ表示（後方互換）
  - 新形式（オブジェクト配列）→ role順（主要→ボトルネック→注目）にグループ化し色別バッジ表示（主要:シアン・ボトルネック:アンバー・注目:グリーン）。`note` がある場合は `data-info-text` 属性で `info-tooltip.js` にⓘツールチップを自動付与
- 次の日曜（Grok再生成）まで旧表示が維持される（後方互換性により問題なし）

✅ [DISCOVER-FEATURE-2] テーマ選定根拠・証跡の明示（2026-06-24完了）
- **対象**: `src/discover/collect.py`・`.github/workflows/Discover_Update.yml`・`docs/common/glossary.json`・`docs/discover/index.html`
- `src/discover/collect.py`: プロンプトに `sources` フィールド（1〜3件）を追加。日曜実行時に `docs/discover/data/macro_themes_history.json` へ週次追記（最大26件・新しい順）
- `.github/workflows/Discover_Update.yml`: `macro_themes_history.json` を git add 対象に追加（ファイル未存在時はスキップ）
- `docs/common/glossary.json`: `discover_conviction` キー追加（高/中/低の判定基準）
- `docs/discover/index.html`: 確信度バッジにツールチップ追加（`data-info="discover_conviction"`）・`sources` をリンク付きリストとしてカード末尾に表示・streak ≥ 1 の場合に「🔥 N週連続」バッジをテーマ名横に表示・「過去のテーマを見る（N週分）」折りたたみセクションを追加（直近4週分）

✅ [DISCOVER-LAYOUT-1] 一覧性の向上（DISCOVER画面）（2026-06-24 完了）
- **対象**: `docs/discover/index.html`
- `.ticker-cards` を `display:flex;flex-direction:column` → `display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr))` に変更し2カラム以上のグリッド表示を実現
- `buildTickerCard()` に `data-collapsed=""` + `onclick="toggleCard()"` + `▶` トグルアイコン + リンクへの `event.stopPropagation()` + `ticker-card-body` に `style="display:none"` を追加し、デフォルト折りたたみに変更
- 既存の `toggleCard()` 関数（`data-collapsed`属性トグル）をそのまま流用

✅ [MP-FEATURE-1] AIコメントの過去履歴保持・表示機能（Market Pulse画面）（2026-06-24 完了）
- **対象**: `src/market/market_pulse/collect_and_send.py`・`docs/market-monitor/market-pulse/index.html`
- **データ側**: `save_data_to_json_and_csv()` に `comments_history` 配列を追加。同日エントリ重複除去後の `all_data` から直近11件の `{date, summary}` を逆順収集し、当日分と合わせて最大12件を `new_entry.comments_history` として保存
- **表示側**: `renderDetail()` の末尾に `buildCommentsHistory(d)` を追加。`comments_history[1:]`（過去分）が1件以上ある場合、「▶ 過去の分析を見る（N件）」トグルボタンと折りたたみパネルを生成。`toggleCmtHist()` で開閉制御

✅ [TSCORE-DUPONT-1] DuPontパネルのソート機能追加（2026-06-24完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- 全6列（銘柄・ROE(DuPont)・純利益率・資産回転率・財務レバレッジ・ROE(実績)）にヘッダークリックソートを追加
- 昇順→降順→昇順トグル、ソート列に矢印インジケーター（▼▲）とアクセントカラーを表示
- 既存の全銘柄詳細テーブルのソートロジック（`_sortCol`/`_sortDir`・`thArr`等）を流用
- 初期状態はROE(DuPont)降順（従来の固定ソートと同一）

✅ [TSCORE-DUPONT-3] ROE(DuPont)と実績ROEの乖離警告（2026-06-24完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- 閾値: |DuPont ROE − 実績ROE| ≥ 10%pt
- 表示: アンバー背景（rgba(245,158,11,.06)）+ ROE(実績)セルに⚠バッジ
- ツールチップ: 乖離幅・両値・要因説明（info-tooltip.js流用）
- 既存の黄色⚠（信頼性・極端値）と色違いで共存
- 現データで50銘柄/86銘柄が警告対象

✅ [SILO-LAYOUT-2] 「総合スコア判定根拠」配置・コンパクト化（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html`
- 旧位置: detail-bottom後ろ（画面最下部）→ 新位置: pillar-row直下・valuation bar上
- `<details>`タグでデフォルト折りたたみ（▶ 総合スコア 判定根拠）

✅ [SILO-LAYOUT-3] 各詳細セクションを評点カード下にネスト配置（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html`
- 変更後構造: pillar-row内の各カード（①②③）直下に対応する詳細を折りたたみで配置
- 総合スコア判定根拠はpillar-row直下に配置（SILO-LAYOUT-2と統合）

✅ [SILO-LAYOUT-1] 「黒字化への道のり」チャートの凡例・説明追加（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html` — `buildProfitPath()` return
- タイトル行に `?` ツールチップ（0ライン=黒字化基準、単位説明）を追加
- 凡例3項目（緑=黒字達成済み / 紫=次の黒字化目標（ETA自動算出）/ グレー=ペンディング）をドット付きで追加

✅ [SILO-LAYOUT-4] 時価総額等のサマリー情報をティッカー名近くに集約（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html` — `buildDetail()` return
- `valInlineHtml` 変数を追加し `conclusion-left` 内（conclusion-summary直下）にコンパクト表示
- 表示形式: `MC $1.23B　$45.67　PSR 12x　EV/S 10x　NC $0.50B`
- standalone val-bar IIFE（旧1行）を削除

✅ [SILO-LAYOUT-5] 棒グラフと財務トレンドセクションの隣接配置（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html` — CSS
- `.chart-row{margin-bottom:16px}` → `margin-bottom:0`
- `.fv-section{margin-top:14px;border:1px solid var(--bdr)}` → `margin-top:0;border-top:none` でシームレスに結合

✅ [PORT-FEATURE-1] 主要金額表示への円貨表示切り替え追加（2026-06-24完了）
- **対象**: `docs/portfolio/index.html`
- `_usdJpy`（history.jsonのlatestスナップから取得）・`_currMode2`・`fmtC()`・`switchCurr()` を追加
- `loadData()` に history.json の並行フェッチを追加（usdjpy抽出 + `loadHistoryChart()`の二重フェッチ排除）
- 適用箇所: 総資産・時価残高合計・評価損益・キャッシュ/ブローカー別サマリー（全金額）/テーブル全金額列
- サマリー左上に USD/JPY 切り替えボタン追加
- `switchChart()` を scoped に修正（currency ボタンと競合しないよう）

✅ [TAIL-LAYOUT-1] DECISION LOGの別ページ分離（2026-06-24完了）
- **新規ファイル**: `docs/portfolio/tail/decision_log.html`
- 元ページの journal section を「DECISION LOG を見る →」リンク + 最終ログサマリーに置き換え
- 新ページ: 同auth・フィルターUI・全ログ表示（全件数バッジ付き）
- site-nav.js への追加なし（サブページのため）

✅ [TAIL-UX-1] TANUKI TAIL使い方ガイダンス充実（2026-06-24完了）
- **対象**: `docs/portfolio/tail/index.html`・`docs/common/glossary.json`
- ページ冒頭に利用フロー（①登録→②Grokレビュー→③ログ記録）バナーを追加
- 「前回レビューからN日」を journal.json 最新エントリーから算出（30日以内=緑/90日以内=amber/超過=赤）
- OVERVIEW CORE/SAT・NEW POSITION セクションに `data-info` ツールチップ追加
- glossary.json に `tail_overview`/`tail_overview_sat`/`tail_new_position`/`tail_decision_log` を追加

---

## 2026-06-24（調査）

✅ [DCF-RELIABILITY-1] FCF_Conversion_Rate表示欠け調査（2026-06-24完了・対応不要）
- **調査結果**: rate=null の銘柄はゼロ。非表示19件はすべて設計上の正常動作
  - 赤字（adj_net_income≤0）: 12件（ASTS, CRWV, IONQ, JOBY, ONDS, QBTS, RBRK, RCAT, RKLB, RXRX, S, SOUN）
  - FCF外れ値除外（二重補正防止）: 5件（AMZN, BBAI, COHR, KULR, RDW）
  - EPSデータ欠落: 2件（BKNG, FCX）
- 「74銘柄表示欠け」は過去のClaude Code調査時点の記録であり現状と乖離していた
- 別途 [DAILY-PICK-BUG-1] を新規登録（daily_pick.jsonのtanukiキー欠落）

---

## 2026-06-24（Task Group 2）

✅ [TSCORE-FIX-2] TANUKIスコアテーブルの行間・フォント改善（2026-06-24 完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- **対応**: `.dtbl th` の padding を 9px/12px→10px/14px、font-size を 10px→11px に拡大。`.dtbl td` の padding を 8px/12px→10px/14px に拡大（HypeCore detail.html の基準に統一）

✅ [TVAL-FORMULA-1] TANUKI VALUATION 算式と実装の整合性監査・修正（2026-06-24 完了）
- **対象**: `docs/value-monitor/tanuki_valuation/index.html`（formula-preview・method-card・TABLE LEGEND）
- **監査結果**（7式）:
  - RICE: **不一致→修正** VC_Factorが表示から欠落。`(G×Q×CF)/WACC`→`(G×VC_Factor×Q×CF)/WACC`（3箇所修正）
  - Q: **不一致→修正** SBC補正が表示から欠落。`OCF÷純利益`→`OCF÷(純利益+SBC)`（1箇所修正）
  - IV(P_t): **不一致→修正** `GO_PV×(1+α)÷株式数`と表示していたが実装は`GO_PV÷株式数`（αはGO_PVに乗らない）
  - α, WACC, 乖離率, CF: **一致**（修正なし）
- **根拠**: `adjustments.py` L598: `intrinsic_value_pt = v0*(1+alpha) + rpo_pv + growth_option_pv`
- **注記**: CLAUDE_CODE_START.md記載の「RICEのVC_Factor欠落は既知」の解消も含む

✅ [EPS-LAYOUT-1] 個別明細画面にティッカー＋会社名表示（2026-06-24 完了）
- **対象**: 3画面 + 共通データファイル新規生成
  - `docs/common/company_names.json`（新規）: `config/cik_lookup.csv`から96銘柄の`{ticker: name}`マッピングを生成
  - `docs/value-monitor/adjusted_eps_analyzer/stock.html`: `ticker-title`を`TICKER — Company Name`形式に
  - `docs/value-monitor/tanuki_valuation/stock.html`: `.ticker-symbol`に会社名を付加
  - `docs/value-monitor/hypecore/detail.html`: `page-title-sub`に選択銘柄の会社名を表示
- **実装方式**: ページ初期化時に`company_names.json`をfetchし、会社名が存在する場合のみ付加（フォールバックはティッカーのみ）

---

## 2026-06-24

✅ [HYPE-BUG-2] 開閉アイコンの向きが逆さま修正（2026-06-24 完了）
- **対象**: `docs/value-monitor/hypecore/detail.html`
- **原因**: `.narrative-toggle-arrow.open { transform: rotate(180deg) }` とJS側テキスト切り替え（▼→▲）が二重適用。展開時に▲が180°回転して▼に見えるバグ
- **対応**: CSS の `rotate(180deg)` を削除。テキスト切り替えのみで方向制御

✅ [MP-GAUGE-NEEDLE-1] ゲージの数値ラベル「0」「100」除去（2026-06-24 完了）
- **対象**: `docs/market-monitor/market-pulse/index.html`（センチメント・CNN F&G・Tech Pulse の3ゲージ）
- **原因**: 右端の「100」テキストラベルと「GREED」ラベルが同位置で重なっていた
- **対応**: 3ゲージすべてから `<text>` の「0」「100」を除去。FEAR/GREEDラベルが両端を示すため不要、「50」中央ラベルのみ残置

✅ [HOME-FIX-4] FEATURESセクションの`//`は意図的装飾と確認（2026-06-24 完了）
- **調査結果**: `<div class="feat-icon">//</div>` はリテラルテキスト。フォントアイコン未ロードではなく、コードコメント風の意図的デザイン装飾（Space Monoフォント×アクセントカラー）
- **対応**: コード変更なし

---

## 2026-06-23

✅ [TAIL-DISP-2] CORE一覧「乖離率」列が全銘柄`–`表示の修正（2026-06-23 完了）
- **対象**: `docs/portfolio/tail/index.html`・`docs/common/glossary.json`
- **原因（2段階）**:
  1. `renderCoreTable()`の乖離率セルが`'<td class="num" style="color:var(--mut)">—</td>'`と
     ハードコードされており、そもそもどのデータフィールドも参照していなかった（未実装）
  2. 仮にデータ参照に書き換えても、`loadValuations()`（TANUKI VALUATIONのlatest.jsonを
     fetchして`latestValCache`に格納する関数）が`p.type === 'satellite'`銘柄のみを
     対象にしており、CORE銘柄のTANUKI VALUATIONデータが一度も取得されていなかった
     （SATELLITE一覧の「現在価格」列は同じキャッシュを参照しており正常表示されていたため
     見落とされやすい構造だった）
- **対応**:
  - `loadValuations()`への対象ティッカー収集を`type==='satellite'`限定から
    `status!=='archived'`（CORE含む全銘柄）に拡大
  - `renderCoreTable()`で`latestValCache[p.ticker].upside_percent`
    （TANUKI VALUATIONの理論株価IVと現在株価の乖離率、既存フィールドを流用・新規計算ロジックなし）
    を参照し、プラス=緑/マイナス=赤で表示する分岐を追加（SATELLITE一覧のP/L%表示と同じ配色規約）
  - `data-info="tail_deviation_rate"`をth要素に付与し、`glossary.json`に新規キーを追加
    （CLAUDE_CODE_START.md記載の「ユーザー向け数値を追加した場合はglossary.json登録」ルールに準拠）
- **検証**: Playwrightで実データ確認（パスワードゲートはsessionStorageバイパス）。
  CORE銘柄（PLTR/SOFI/TSLA）で乖離率が実数値（-49.4%/-7.9%/-87.3%）かつ正しい色で表示、
  ツールチップ文言も正しく表示されることを確認。SATELLITE一覧側への影響がないことも確認。
  pytest 119件全件パス、check_links.py リンク切れ0件

✅ [PORT-DISP-2/PORT-LAYOUT-1/PORT-LAYOUT-2] ポートフォリオ画面の表示修正3件（2026-06-23 完了）
- **対象**: `docs/portfolio/index.html`
- **PORT-DISP-2（セクション番号②から始まる）**: `#summary-section`の資産サマリー
  （総資産・時価残高合計・評価損益・キャッシュ比率の4カード）に`<div class="sec">`見出しが
  一切存在しなかったことが原因。`① 資産サマリー`見出しを追加し②③④と連続させた
- **PORT-LAYOUT-1（「その他」が2番目に表示）**: `brokerSummaries`の並び順は
  `portfolio.json`の`brokers`オブジェクトのキー順（`Moomoo→その他→Moomoo(N)→MONEX→RAKUTEN`）
  そのままで、ソート処理が一切なかったことが原因。カード描画前に
  `bAssets===0`（残高$0）を末尾へ送る安定ソートを追加（他の並び順は維持）
- **PORT-LAYOUT-2（RAKUTENカードのみ横長）**: `.broker-summary{display:flex;flex-wrap:wrap}`+
  `.broker-card{flex:1}`構成で、5枚中4枚が1行目を埋め5枚目（RAKUTEN、配列末尾）が
  2行目に単独で残り、`flex:1`によりその行の全幅まで伸長していたことが原因
  （flexの`flex-basis:0%`は同一行内の兄弟数に応じて幅を再分配するため、単独行では
  100%まで広がる）。`display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr))`に
  変更し、行をまたいでも列トラック幅が固定されるようにした（`auto-fit`ではなく`auto-fill`を
  採用: ブローカー数が少ない場合にカードが不必要に間延びするのを防ぐため）
- **検証**: Playwrightで実データを使い確認（パスワードゲートは`sessionStorage`に
  認証フラグを注入してバイパス）。① 資産サマリー〜⑤ 資産推移までセクション番号が連続、
  5枚のブローカーカードが全て等幅（約183px）になったこと、「その他（$0.00）」が
  5枚目（最後）に移動したことを確認。600px/960px幅でも崩れずグリッドが機能することを
  スクリーンショットで確認。pytest 119件全件パス、check_links.py リンク切れ0件

✅ [PORT-DISP-1] 最終更新日が古いまま（PORTFOLIO画面）の調査完了・仕様通りと判明（2026-06-23 完了）
- **対象**: `docs/portfolio/index.html`（`#last-updated`、`pf.last_updated`表示）・
  `docs/portfolio/data/portfolio.json`
- **調査結果**: `portfolio.json`の`last_updated`は実データも2026-06-03のまま停止しており
  表示側のバグではないことを確認。`src/portfolio/snapshot.py`を含む全Pythonスクリプト・
  全GitHub Actionsワークフローを検索したが、`portfolio.json`を書き込む自動化パイプラインは
  存在しないと判明
- **真の更新経路**: `docs/value-monitor/admin.html`の`savePortfolio()`関数（3500-3530行目）が
  管理画面の「💾 ポートフォリオを保存」ボタン経由で`last_updated`をセットしGitHub API経由で
  直接コミットする、**人間による手動更新が唯一の設計上の経路**。git履歴上の過去コミット
  （`feat(portfolio): ポートフォリオ更新`、コミット者は人間でgithub-actions[bot]ではない）が
  admin.htmlの生成パターンと完全一致することで裏付け
- **結論**: 2026-06-03以降ユーザーが管理画面から保存操作を行っていないことが原因であり、
  コード上の不具合ではないため**修正なし**。自動更新が必要な場合は新機能として別途
  BACKLOG起票が必要（証券会社API連携等、既存の【Moomoo API】系BACKLOGと関連）

✅ [TAIL-SAT-CI-1] Satellite Monitor CIのgit pull --rebase失敗修正（2026-06-23 完了）
- **対象**: `.github/workflows/TANUKI_TAIL_Satellite_Monitor.yml`（「Commit updated
  alert history」ステップ）
- **原因特定**: `src/tail/satellite_monitor.py`が`satellite_alerts.json`
  （`_save_alerts`）と`journal.json`（`_save_journal`、`_append_journal_watchlist`
  経由でアラート発生時に毎回書き込み）の2ファイルを更新するが、ワークフローの
  `git add`は`satellite_alerts.json`のみをステージしていた。いずれかのsatellite
  銘柄でアラート条件（エントリー/エグジット/ニュース/決算接近）が1件でも発火すると
  journal.jsonも更新され、`git commit`後に未ステージ変更が残ることで後続の
  `git pull --rebase`が「cannot pull with rebase: You have unstaged changes」で
  失敗していた。journal.json・satellite_alerts.json両方の最終更新日が2026-06-07で
  一致しており、この日以降ローカルコミットは成立するもpushまで到達していなかった
  ことと整合（コミットはランナーの使い捨てクローン内で完結し破棄されるため、
  リモートのデータは更新されないまま停滞していた）
- **比較**: 正常動作している`TANUKI_TAIL_RSS_Monitor.yml`は、スクリプトが更新する
  全ファイルを`git add`に明示列挙する既存パターンを採用しており、これに倣った
- **対応（案B採用）**: `git add`に`docs/portfolio/tail/data/journal.json`を追加。
  スクリプト内の書き込み対象（`json.dump`呼び出し）を全件grepで洗い出し、
  この2ファイル以外に書き込みがないことを確認済み
- **検証**: このセッションには`gh` CLI等のGitHub Actions認証手段がなく
  workflow_dispatchを直接トリガーできなかったため、修正pushの上でユーザーに
  GitHub Web UIからの手動トリガー、または次回定期実行（平日JST 08:00/17:00）での
  自然検証を依頼

✅ [MACRO-DISP-2] Michigan Sent.*指標名の850px/1200px幅省略修正（2026-06-23 完了）
- **対象**: `docs/market-monitor/macro-pulse/index.html`（`.phase-signals`/`.pg-sig`、
  EPIC-LAYOUT-1グループB対応の残課題）
- **実測調査**: Playwrightで700/800/850/960/1024/1200/1400pxの`.v3-main`実幅・
  `.phase-signals`の列数・列幅を計測。850px/1200pxはともに`.v3-main`が約800〜810px
  まで縮み、`repeat(auto-fit,minmax(260px,1fr))`で3列になった結果、列幅が266〜269px
  まで圧縮されることを確認（「Michigan Sent.*」の必要幅83pxに対し名前スパンの
  `clientWidth`が77〜80pxしかなく数px不足→省略）。850px（`.v3-dash`が単一カラムに
  切替わる1000px境界の直下）と1200px（2カラムでサイドバー340px+gap18pxを差し引いた
  幅）がたまたま同程度の`.v3-main`幅に収束する非線形性が原因で、`minmax`調整だけでは
  別の幅で再発する「モグラ叩き」と判明（対応方針候補1/3はこの非線形性に追従し続ける
  ため不採用、候補2を選択）
- **対応**: `.pg-sig`を1行レイアウトから2行レイアウトに変更（候補2）。
  Row1=dot+name、Row2=val+badge+leadに分離し、`.pg-sig-name`がval/badge/leadと
  横幅を奪い合わなくなるようにした。`minmax(260px,1fr)`は変更不要（2行化だけで
  必要最小幅が大幅に下がり、260px floorに対して十分な余白が生まれた）
- **検証**: Playwrightで700/800/850/960/1024/1200/1400pxの全7幅で
  「Michigan Sent.*」を含む全8指標名の省略が0件であることを確認
  （`scrollWidth>clientWidth`チェック）。スクリーンショットで視覚的にも確認。
  ツールチップのホバー表示が引き続き機能することも確認（DOM構造変更後も
  `.pg-sig{position:relative}`は維持）。pytest 119件全件パス、check_links.py
  リンク切れ0件

✅ [MP-GAUGE-NEEDLE-1] センチメントゲージの針とラベルの重なり修正（2026-06-23 完了）
- **対象**: `docs/market-monitor/market-pulse/index.html`（CNN Fear&Greed・Tech Pulse
  両ゲージ、`#fgGaugeSvg`/`#tpGaugeSvg`共通の`.tp-gauge-center`クラス）
- **構造調査**: 針（`<line>`要素、`#fgNeedle`/`#tpNeedle`）の回転軸は`(90,94)`固定で
  `rotate(${score/100*180-90},90,94)`によりscore=0で-90°（左/FEAR方向）・score=50で
  0°（真上）・score=100で+90°（右/GREED方向）に回転する。半径66の単一線分。
  一方スコア数値・ラベル（`.tp-gauge-center`、HTML divをSVG上に絶対配置）は
  `bottom:2px`で下端y=104に固定され、上端は内容次第でy=54付近まで達する。
  **針の回転軸(90,94)自体がラベル領域(y=54〜104)の内側にある**ため、針をどれだけ
  短縮してもラベル中央(x≈90)を回転軸付近で必ず通過することが判明（案A＝針短縮は
  幾何学的に不採用、選択基準通り案Bへ）
- **Playwright実測**: stroke-width考慮のbbox当たり判定で、score=0/25/50/75/100の
  全パターンで針とラベルが重なることを確認（score=0/100でも回転軸近傍でラベル下端と
  軽微に重なる）
- **対応**: `.tp-gauge-center`に`background:var(--sur)`（カード背景色と同色の不透明
  背景）・`padding:2px 8px`・`border-radius:6px`を追加（案B）。DOM順序上もともと
  `.tp-gauge-center`は`<svg>`より後に配置されており、CSSデフォルトの重なり順で
  針より上に描画されるため、背景を不透明にするだけで針が完全にマスクされる
  （z-index等の追加調整は不要だった）
- **検証**: Playwrightで0/25/50/75/100の5スコア × CNN Fear&Greed/Tech Pulse
  両ゲージ × 600/960/1400px幅の全組み合わせで、針がラベル背景の外側でのみ視認でき
  文字との重なりがないことをスクリーンショットで確認。pytest 119件全件パス
  （CSS変更のみのためロジック影響なし）、check_links.py リンク切れ0件

✅ [DCF-RELIABILITY-1] FCF_Conversion_Rate方式銘柄へのDCF_Reliability判定拡張（2026-06-23 完了）
- **実装箇所**: `src/value/tanuki_valuation/pipeline.py`
  - `_calc_dcf_reliability_policy_b()`（静的メソッド新設）に判定ロジックを集約し、
    スコアリング（`_compute_tanuki_score`）とreport.txt生成の両方から共通利用
  - 判定表（仕様通り、eps_invalid優先で曖昧さを解消）:
    `eps_invalid=true → LOW`（detected/transient_foundに関わらず最優先）、
    `eps_invalid=false, detected=true, transient_found=false → LOW`、
    `eps_invalid=false, detected=true, transient_found=true → NORMAL`、
    `eps_invalid=false, detected=false → NORMAL`
  - `eps_invalid`はEPSアナライザー自体にreliabilityフラグが存在しないため、
    `FCFEstimationResult.divergence_warning`（推定FCFが生FCFの2倍以上乖離）を
    代理指標として採用（設計判断・コード内コメントに明記）
  - report.txt: FCF_Conversion_Rate方式の`else`分岐に`DCF_Reliability: LOW/NORMAL`を
    常時出力するよう追加（Policy Aと同形式の`[Policy B: ...]`注記付き）
  - TANUKI SCORE: `fcf_estimation.applied=True`（Policy B対象）かつPolicy B=LOW時に
    BUY/TRIM/HOLD/WATCHをWATCHへ丸め（SELL/PASSは維持）。Policy A
    （`fcf_floor_applied>0`）とは適用条件が排他的なため同時発火しない
- **report_consistency_check.py**: CHECK-2（DCF_Reliability欠落検出）を拡張し、
  `FCF_Conversion_Rate:`行ありでDCF_Reliability行なしのケースも検出するよう
  `has_fcf_conversion_rate`判定を追加（既存のCHECK-3 LOW丸め未発動は
  正規表現が両Policy共通のため無改修で適用される）
- **テスト**: `tests/test_pipeline_logic.py`に`TestDcfReliabilityPolicyB`を新設
  （9件: 判定表4パターン・eps_invalid優先順位の境界値・スコア丸め3パターン・
  Policy A/B排他性）。pytest 110→119件、全件パス
- **検証**: ADBE/NVDA/SITM/SPIR（LOW想定）、AAPL（detected=false→NORMAL）、
  ADSK（transient_found=true→NORMAL）で実データ確認。ASTS/AMZN（Policy A
  LOW/HIGH）を再生成し既存挙動が変化しないことを確認。全95銘柄を
  `--skip-risk`で再生成（成功94/失敗0）、`report_consistency_check.py` NG=0
  （WARN=1件、ELFのPS異常値はDCF-RELIABILITY-1と無関係の既存事項）

✅ [TVAL-TS-FIX-1] タイムスタンプ表示の未整形・フォーマット不具合修正（2026-06-23 完了）
- **TVAL-TS-1**: `docs/value-monitor/tanuki_valuation/stock.html`の`.version-tag`
  （950行目）とfooter「計算日:」（2037行目）が`calculation_date`
  （フルISOタイムスタンプ）を未整形のまま表示していたのを、既存の`toJST()`関数
  （2588行目、`2026/06/20 17:36 JST`形式に変換）を適用して解決
- **TVAL-TS-2**: `docs/value-monitor/tanuki_valuation/index.html`の`fmtDate()`
  （388行目）`(d)=>d.slice(5).replace('-','/')`が、フルISO文字列に対して
  `slice(5)`すると`"06/20T17:36:48+09:00"`という壊れた文字列になる実装バグを修正。
  `d.slice(0,10).slice(5).replace('-','/')`に変更し、まず日付部分のみ
  （YYYY-MM-DD）を確定してから整形するようにした
- **検証**: Playwrightで実機確認。stock.htmlのversion-tag/footerが
  `2026/06/23 03:21 JST`形式で表示されること、index.htmlの更新日列が
  フルISO（`2026-06-23T03:22:43+09:00`）でも日付のみ（`2026-06-20`）でも
  `06/23`/`06/20`形式に正しく整形されること（壊れた文字列が出ないこと）を確認。
  `fmtDate(null)`/`fmtDate('')`が`'—'`を返すことも確認。pytest 110件全件パス・
  check_links.py リンク切れ0件

✅ [EPIC-LAYOUT-1 グループC] SILO-DISP-3: Stonks Siloテーブルのバッジ省略修正（2026-06-23 完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html`
- **問題①（主因）**: TICKER列にTANUKI SCOREバッジ（BUY/WATCH/PASS等）が非同期注入
  されるが、列幅（72px）がティッカー文字のみを想定したサイズでバッジ分の余白が
  確保されておらず、1400px幅でもWATCH/PASS等5文字ラベルが省略されていた
  → `.col-ticker{min-width:100px}`をth/tdに付与して解消
- **問題②**: `table-layout:fixed`+colgroupのpx幅指定（全docs/配下でこのページのみ
  使用）により、コンテナ幅が808px未満（半分画面幅相当）になると総合判定列（118px）の
  サブラベル「成長・生存・黒字化が均衡」がはみ出していた
  → `table-layout:fixed`とcolgroupを廃止して自然幅テーブルに変更し、
  EPIC-LAYOUT-1標準パターン（`data-priority="low"`＋`docs/common/site-theme.css`の
  既存`@media(max-width:1000px)`ルール）をCF改善列・粗利率列に適用。
  `@media(max-width:1000px){.tbl-wrap table{min-width:0}}`をページ内で追加し
  間引き後に残り列が自然に広がるようにした（portfolio/index.html準拠）
- **検証**: Playwrightで600/850/960/1024/1400pxの5幅を実機確認。
  全幅でTICKER列バッジ省略0件・総合判定列はみ出し0件、960px以下でCF改善・粗利率列が
  非表示、1024px以上で再表示されることを確認。check_links.py でリンク切れ0件も確認
- **これでEPIC-LAYOUT-1の統合元7件（グループA/B/C）が全件完了**。
  詳細はBACKLOG.mdの[[MACRO-DISP-2]]（850px/1200px幅の残存課題）のみ低優先度で継続

---

## 2026-06-22

✅ [EPIC-LAYOUT-1 グループB] フレックス行ラベル省略・推奨列折り返し不揃いの修正（2026-06-22 完了）
- **MACRO-DISP-1**: `docs/market-monitor/macro-pulse/index.html`の`.phase-signals`の
  `minmax()`値を200px→260pxに拡張（200→240→260pxの2段階調整。240pxでは800px幅で
  「Michigan Sent.*」が省略されたため260pxへ追加調整）
  - 700/800/960/1024/1400px幅で省略解消を確認
  - **850px/1200px幅で「Michigan Sent.*」の省略が残存**（モグラ叩き現象。
    根本原因は親コンテナ`.v3-main`の幅がビューポート幅に比例せず非線形に
    変動するため。下記[[MACRO-DISP-2]]として新規登録）
  - コミット: ef52e10e6
- **HYPE-DISP-1**: `docs/value-monitor/hypecore/index.html`の推奨クラス
  （`.rec-buy`/`.rec-hold`/`.rec-sell`/`.rec-watch`）に`white-space:nowrap`追加、
  推奨列`<td>`に`.rec-cell{min-width:120px}`付与（「様子見（底打ち）」実測幅89px+
  td padding20pxが根拠）
  - 700〜1400px全幅で行高さ33pxに統一、折り返し不揃いを完全解消
  - 副作用として700/750/800/1024px幅でテーブル内（`.table-wrap`）横スクロールが
    新規発生するが、bodyレベルのはみ出しはなし（HYPE-DISP-2と同じ許容範囲の挙動）
  - コミット: e8857f6b2
- **教訓**: グループAのMP-LAYOUT-1に続き、グループBの2件も「960px固有の問題」
  という当初の前提が外れた（MACRO-DISP-1は700〜1400px全幅で発生する画面幅非依存の
  問題、HYPE-DISP-1も960pxでは無症状で700px/1024pxで発生する非単調な問題だった）。
  EPIC-LAYOUT-1全体を通じて「960px境界の問題」という分類自体を疑ってから
  実装することが重要だと再確認した

### ✅ [MP-BREADTH-2] Market Pulse 市場の広がり強化・二極化警告実装（2026-06-22 完了）
- **内容**: 市場の二極化（一部銘柄のみ上昇）を捉えるための5指標を新規実装
  1. RSP/SPY乖離指標（Equal Weight vs Cap Weight）: yfinanceで1d=-0.576pt /
     20日平均=+0.097ptを実取得確認。`breadth_data.json`に保存
  2. 累積A-Dライン: 既存47件をバックフィル（最古日ad_line=102→最新日530）。
     既存のセンチメントスコア推移チャート（OSC_METRICS、トグル選択式）に
     S&P500・McClellanとあわせて新規トグル項目として追加
     （依頼は専用ミニチャート新設だったが、既存の複数指標トグル比較機構を
     再利用する形に実装方針を変更した）
  3. NH/NL・AD Ratio独立警告バッジ（AD Ratio<0.8→「⚠ 市場が薄い」、
     NH-NL<-50→「⚠ 新安値優勢」）
  4. S&P500ベース近似マクラレンオシレーター（19日EMA-39日EMA、実データ-16.4。
     NYSE全銘柄ではなくS&P500構成銘柄ベースの近似である旨を画面上に明記）
  5. 二極化総合警告バッジ（上記+50MA%<60%+マクラレン低下中の5シグナル中
     3つ以上点灯で「市場の二極化を検出 N/5シグナル点灯」表示）
- **センチメントスコアウェイト変更**: 既存7指標（VIX/MA乖離/ADRatio/HYG-LQD/
  NH-NL/グロースバリュー/出来高）を×0.9に圧縮し、RSP/SPY乖離(20日平均)を
  weight 10%で新規追加。合計100%を維持（実行確認済み）
- **コミット**: 24cfb42d2
- **確認**: pytest 110件パス、Python構文チェックOK、Playwrightで960px/1400px幅の
  レイアウト崩れ・JSエラーなし、二極化シナリオ注入テストで5/5シグナル点灯の
  全バッジ表示を確認
- **前段の調査**: 同日実施したMarket Pulse現状調査（実装無し・調査のみ）で
  FRED/yfinanceでのNYSE全銘柄ベースの厳密なヒンデンブルグオーメン再現は
  困難と判明したため、本実装はS&P500ベースの近似・代替指標として位置づけた

✅ [FOUR-DELETE-1] FOUR（Shift4 Payments）を全システムから削除（2026-06-22 完了）
- **理由**: 投資対象として見送り。株式数XBRLバグ（2026-06-14のBUG修正、CIK誤報告74倍過小）により
  EPSアナライザーが構造的に無効化されており、IV計算の信頼性も担保できないと判断
- **削除範囲**:
  - 設定: `config/cik_lookup.csv`・`beta_config.json`・`discover_config.json`（+`docs/portfolio/data/`同期）・
    `monitor_tickers.yaml`・`docs/value-monitor/tanuki_valuation/data/tickers.json`（count 96→95）・
    `docs/value-monitor/tanuki_valuation/data/.watcher_state.json`・
    `src/value/tanuki_valuation/growth_sanity.py`（業種分類オーバーライドの不使用エントリ）
  - 生成データ: `common/sec_data/{data,normalized,raw,ttm}/FOUR`関連・
    `docs/value-monitor/tanuki_valuation/data/FOUR/`一式・`hypecore_history/FOUR.json`・
    `docs/value-monitor/hypecore/data/FOUR_poc.json`・`src/value/hypecore/data/FOUR_poc.json`（実体側）・
    `docs/value-monitor/adjusted_eps_analyzer/data/FOUR`（空ディレクトリ）。計104ファイル
  - **意図的に残置**: `docs/discover/data/daily_report.json`・`docs/integrated-dashboard/history.json`・
    `docs/value-monitor/tanuki_score/history.json`（日付キーの共有履歴ログのため遡及編集せず）、
    `common/sec_data/data/_cik_cache.json`のFOURエントリ（単なる参照キャッシュで実害なし）
- **削除手順書の見落とし発見**: 当初の削除依頼にはなかった`beta_config.json`・`growth_sanity.py`・
  `src/value/hypecore/data/`（docsとは別の実体ファイル）・`.watcher_state.json`の4件を
  grep横展開で追加発見・対応した。CLAUDE_CODE_START.mdの銘柄削除手順にも
  `growth_sanity.py`等のコード内ハードコード参照は記載がなく、今後の削除作業でも
  `grep -rln "TICKER" docs/ config/ common/ src/`のような全文横断検索を都度実施する必要がある
- **コミット**: f3cd4a111
- **確認**: `system_health.py` HEALTHY（95/95件存在、latest.json欠損0件）・pytest 110件パス・
  `check_links.py` エラー0件
- BKNG・FCXは（同種のEPSアナライザー無効銘柄だが）削除対象から明示的に除外

✅ [MP-LAYOUT-1] Tech Pulseゲージ3列が1行に収まらず縦積みになる問題の修正（2026-06-22 完了・EPIC-LAYOUT-1グループAへ追加対応）
- **背景**: 当初の調査（同日早い時点）で「`.unified-gauge-row`は`flex-wrap:wrap`があるため
  オーバーフローしない＝対象外」と判断したが、その後の指摘で「オーバーフローしない＝
  正常」ではなく「1行に収まるはずのゲージ3つが常に縦積みに折り返される」こと自体が
  症状であると判明し、対応した
- **原因**: 列幅（391px/443px）の正体はSVGゲージ本体（固定180px）ではなく、
  `.tp-gauge-title`内のサブタイトル文言（折り返し制約なしの1行テキスト）だった。
  700px〜1100px幅のいずれでも3列合計が利用可能幅を超えるため、どの幅でも縦積みになっていた
- **修正**: `.tp-gauge-title`と乖離説明文divに`max-width:172px`を追加してサブタイトルを
  複数行に折り返すようにし、列幅の必要量を391px/443px→180px/212px程度に圧縮。
  あわせて`.unified-gauge-row`のインラインgapを40px→12pxに縮小。
  結果、700px幅以上で3列が常に1行に収まるようになった（Playwrightで700/760/800/960/1024/1400px
  全幅で1行表示を確認）
- **派生バグを分離**: 調査の過程で「GREEDラベル見切れ」も報告されたが、検証の結果
  これは画面幅に依存しない別バグ（ゲージ針が中央ラベルに重なる固定ジオメトリの問題、
  1400px幅でも再現）と判明したため、本対応には含めず[[MP-GAUGE-NEEDLE-1]]として
  BACKLOG.mdに新規登録した

✅ [EPIC-LAYOUT-1 グループA] 固定/自然幅テーブル＋横スクロール対応（PORT-LAYOUT-3 / PORT-DISP-3 / HYPE-DISP-2、2026-06-22 完了）
- **実装方式**: `docs/common/site-theme.css`に`@media (max-width:1000px)`で
  `[data-priority="low"]`を`display:none`にする共通ルールを追加（EPIC-LEGEND-1/
  EPIC-HEADER-1と同じ「共通CSS追加＋属性付与」パターンを踏襲）
- **教訓（regression発生→即修正）**: 当初`table{min-width:0 !important}`も
  site-theme.cssにグローバルで追加したが、これはdata-priority未適用の他ページの
  tableにまで波及し、admin.html(min-width:600px)・tanuki_valuation/index.html
  (820px)・stock.htmlの`.matrix-table`(400px)のmin-widthを960px以下で0に
  潰すregressionを発生させた（pushしてから気づいた）。共通CSSに書くのは
  `data-priority`の表示制御のみに留め、min-width解除は実際に必要な
  `portfolio/index.html`自身の`<style>`内で`.tbl-wrap table`にスコープして
  追記する形に修正した。**「共通CSSに書く」＝「個別ページの調整も全部共通化してよい」
  ではない**。要素セレクタ（`table`等）を共通CSSの`@media`に書くと、その共通CSSを
  読み込む全ページに無条件で波及する点に注意（クラス無しの裸セレクタは特に危険）
- **PORT-LAYOUT-3/PORT-DISP-3**（`docs/portfolio/index.html`の明細テーブル、13列）:
  加重平均単価・取得総額・現在株価・理論株価・メモの5列に`data-priority="low"`を付与。
  TOTAL/CASH行は元々`colspan`でまとめていたが、列ごとの個別`<td>`に分解してから
  対応する列に同じ`data-priority`を付与（colspanのまま非表示列を間引くと表組みの
  グリッドモデルがズレるリスクがあったため）。960px幅でscrollWidth 1201→918pxとなり
  横スクロール解消。PORT-DISP-3で問題視されていた乖離率列は常時表示列として残した
- **HYPE-DISP-2**（`docs/value-monitor/hypecore/index.html`の銘柄一覧テーブル、11列）:
  ライフサイクル・Rule of 40・高値比の3列に`data-priority="low"`を付与。
  960px幅でscrollWidth 980→920pxとなり横スクロール解消
- **MP-LAYOUT-1（Tech Pulseはみ出し）は対象外**: 2026-06-21調査時点でグループAに
  分類されていたが、本セッションでPlaywrightによる実機検証（850px/900px/960px/1024px）
  を実施したところ、いずれの幅でも`.unified-gauge-row`に横はみ出しは再現しなかった
  （`.unified-gauge-row`はすでに`flex-wrap:wrap`が設定済みで、2つのゲージ＋乖離情報が
  自然に縦積みされる）。調査時点から状態が変わったか、調査対象範囲の認識違いの
  可能性がある。BACKLOG.mdの[[EPIC-LAYOUT-1]]側からはMP-LAYOUT-1のグループA該当分を
  除外して記録した
- **検証方法**: ローカルで`docs/`をGitHub Pagesのベースパス（`/On-a-journey/`）に
  合わせて配信する必要があったため、`New-Item -ItemType Junction`で`docs`を
  `On-a-journey`という名前にマウントしたディレクトリ経由でhttp.serverを起動し、
  Playwrightで960px等の各幅でscrollWidth/clientWidthとスクリーンショットを確認した
  （portfolio/index.htmlはクライアント側パスワード認証があるため、テスト時のみ
  `auth-screen`を直接非表示にして`loadData()`を呼び出した。本番の認証ロジック自体は
  変更していない）
- pytest 110件全件パス（フロントエンドのみの変更のため回帰なし）。1400px幅では
  両テーブルとも全列表示を維持することも確認済み

## 2026-06-21

✅ [EPIC-LAYOUT-1-INVESTIGATION] 27インチ半分画面対応の現状調査（2026-06-21 完了・調査のみ）
- **背景**: [[EPIC-LAYOUT-1]]（27インチ半分画面・列幅・はみ出し対応）の統合元9件
  （MP-LAYOUT-1, PORT-LAYOUT-3, PORT-DISP-3, MACRO-DISP-1, SILO-DISP-3, TVAL-TS-1,
  TVAL-TS-2, HYPE-DISP-1, HYPE-DISP-2）について、実装に先立ち現状調査を実施。
  本セッションでは調査のみでファイル変更（実装）は行っていない
- **調査方法**: 960px幅（27インチ半分画面相当）でのheadless Chrome検証＋
  各画面の静的コード解析（行番号レベルで原因箇所を特定）
- **既存共通CSS基盤の確認**: `docs/common/site-theme.css`にはメディアクエリ・
  コンテナクエリが一切存在せず、960px境界の共通設計は皆無と判明。各画面が
  個別のブレークポイント（480/640/700/768/900/1000px等バラバラ）で対応して
  おり、`tanuki_valuation/index.html`・`hypecore/index.html`・
  `hypecore/detail.html`はレスポンシブ対応が完全に皆無だった
- **9件を症状別に4グループへ分類**:
  - グループA（固定/自然幅テーブル＋横スクロール）: MP-LAYOUT-1の一部、
    PORT-LAYOUT-3、PORT-DISP-3（`portfolio/index.html`の同一テーブル・
    実質同一バグと判明）、HYPE-DISP-2
  - グループB（フレックス行ラベル省略）: MACRO-DISP-1（`.pg-sig-name`の
    ellipsis省略を960pxスクショで実視確認済み）、HYPE-DISP-1の一部
  - グループC（`table-layout:fixed`、列幅が常時カツカツ）: SILO-DISP-3
    （`stonks-silo/index.html`の`<colgroup>`固定px幅設計が原因。960px固有の
    問題ではなく列幅設計自体の見直しが必要なため個別対応とする）
  - グループD（純粋なバグ、レイアウト課題ではない）: TVAL-TS-1（ISO文字列
    未整形表示）、TVAL-TS-2（`fmtDate()`の`slice(5)`がフルISO文字列に対して
    破綻する実装バグ、Pythonで`"06/20T17:36:48+09:00"`という壊れた出力を
    再現確認済み）。960px特有の問題ではなく解決策もJSロジック修正のため、
    [[TVAL-TS-FIX-1]]として新規分離した（BACKLOG.md側で対応済み）
- **実装方式の検討**: 3案（①data-priority属性＋`@media`段階的非表示、
  ②横スクロールUIの統一強化のみ、③`@container`クエリ採用）を比較し、
  「①をまず`@media`ベースで導入し、効果を見てから`@container`へ段階拡張する」
  方針を採用（個人利用ツールのためブラウザ互換性の制約は実質なし。
  EPIC-LEGEND-1/EPIC-HEADER-1と同じ共通CSS追加＋属性付与パターンを踏襲）
- **次回着手順序**: グループA → グループB → グループC（SILO-DISP-3は個別対応）。
  BACKLOG.mdのEPIC-LAYOUT-1セクションを対象7件に整理し、着手順序・実装方式を
  注記。TVAL-TS-FIX-1を新規追加した
- 本セッションはファイル変更なし（BACKLOG.md/BACKLOG_DONE.mdへの記録のみ別途実施）

✅ [MACRO-RISKSCORE-CHECK-1] RECESSION RISK SCORE急変動（35→27）の原因調査（2026-06-21 完了・調査のみ）
- **発端**: ユーザーから「先週比35→現在27と短期間で8pt下落しているが原因は何か」との
  確認依頼。コード変更は行わず原因究明のみ実施
- **結論**: 8ポイント下落は計算バグではなく、2つの要因の組み合わせと判明
  - **要因①（構造的・既知）**: 「○ヶ月前比/先週比」はlerp（線形補間）方式、「現在」は
    step（階段関数）方式で算出される仕様（コミット`c3eb81572`、本日対応済みの
    [[MACRO-COMPUTE-DUP-1]]により「現在のみstep統一・過去日付は引き続きlerp維持」と
    確定済みの意図的設計）。この方式の違いだけで2-3pt相当のズレが生じる
  - **要因②（支配的要因）**: フィラデルフィア連銀製造業景況指数（ウェイト18%）が
    -0.4→+10.3へ急改善（6月分データ、2026-06-19公表・`05_events.csv`へ反映）。
    これが8〜11pt相当を占める、本物の経済データ変動
- **検証方法**: `05_events.csv`の実データをPythonで`computeCurrentScore()`/
  `computeScoreAsOf()`双方のロジック通りに再現し、ユーザー報告値（32/29/34/35/27）と
  完全一致することを確認した上で、lerp統一・step統一それぞれの条件で6/14時点と
  現在を再計算（lerp統一: 35→29、step統一(point-in-time): 38→27）。いずれの方式で
  揃えてもフィラデルフィア連銀指数の変化が下落の大半を説明することを確認
- 他7指標（YC/HY Spread/Building Permits/CFNAI/Initial Claims/Michigan Sentiment/
  Sahm Rule）はこの期間ほぼ無風で、閾値（バケット）を跨ぐ変化もなし
- 先読みバイアス対策（`updatedMs<=targetMs`、`idxLatestKnownAsOf`、MACRO-BUG-1由来）が
  正しく機能しており、「先週時点ではまだ5月分(-0.4)しか分かっていなかった」という
  時系列整合性も確認済み。算出ロジック自体に新たなバグは発見されなかった
- **副次的な訂正**: ユーザーが当初想定していた8指標構成に「M2 Money Supply」が
  含まれていたが、実際のRECESSION RISK SCOREの8指標目は「Michigan Consumer
  Sentiment」であり、M2はNET LIQUIDITYゲージ（別指標）にのみ使用されている点を
  調査時に確認・報告
- **対応**: 不要、現状維持（ファイル変更なし）

✅ [MP-FALLBACK-DISPLAY-1] 取得失敗時の前回値補完＋表示区別の実装（2026-06-21 完了）
- **背景**: ^IRXの4日連続取得失敗等を機に、Market Pulseの市場データ表示方針を
  3パターンに整理: ①正常値=実数値表示 ②休場日等で本来データがない=
  yfinanceのperiod="5d"仕様により前営業日データが自動表示（既存仕様・対応不要）
  ③取得失敗（本来データはあるはず）=前回値で補完し、リアルタイム値と記号で区別。
  本対応は③を実装するもの。①②には一切手を加えていない
- **データ収集側（collect_and_send.py）**:
  - `_load_recent_entries()`: market_data.jsonの直近`FALLBACK_LOOKBACK_ENTRIES`
    （=5）件を新しい順に読み込む新規ヘルパー
  - `_is_real_value()`: あるエントリが「本物の値」かを判定する新規ヘルパー。
    `is_fallback`タグ付きを除外するだけでなく、**コンテナのdict自体は存在するが
    中の`value`/`change_pct`フィールドだけNoneという混入データ（MP-DATA-NULL-1の
    NaN→null置換で生じたパターン）も「本物ではない」と判定する**よう設計。
    実装中の単体テストで、この判定を `prev_val and not prev_val.get("is_fallback")`
    のみにすると、2026-06-21の汚染エントリ（S&P500.value=null等）を誤って
    「正常値」として補完元に使ってしまうバグを発見・修正済み
  - `_fill_fallbacks()`: indicators/asset_flow双方に使える共通関数。値がNoneの
    キーについて、直近5件を新しい順に遡り、最初に見つかった「本物の値」を
    コピーして`is_fallback: true`を付与する。フォールバックの連鎖（フォール
    バックされた値をさらにフォールバック元にする）を避けるため、
    `is_fallback=true`のエントリは探索時にスキップして遡り続ける。5件以内に
    見つからなければNoneのまま据え置く（「無限に古いデータを引きずらない」
    という要件を5件の探索上限で実現）
  - `__main__`内で`get_realtime_data()`直後・`collect_asset_flow()`直後にそれぞれ
    `_fill_fallbacks()`を適用。**`compute_sentiment()`はフォールバック適用前の
    今回実測データのみで算出**（センチメントスコアの計算ロジック自体は
    今回のスコープ外、副作用を避けるため意図的に順序を分離）
  - 既存の`[WARN]`ログに、補完を行った旨／5件以内に見つからずnullのまま
    据え置いた旨をそれぞれ追記
- **フロントエンド側（index.html）**: `renderMetrics()`・`renderAssetFlow()`
  （タイル・履歴行の両方）で`is_fallback`を検出した場合、①背景色を通常の
  緑/赤グラデーションから`var(--sur2)`（「—」と同じ無彩色）に、文字色を
  `var(--mut)`に変更し、②値の末尾に`※`マーク（`.stale-mark`、`var(--amb)`、
  クリック/ホバーで`ⓘ`アイコン付きツールチップ表示）を付与。値自体は実数値の
  まま表示し、`opacity:.7`の`.is-stale-value`クラスで視覚的に控えめにする。
  ツールチップ本文（前回値の日付を含む動的文言）は`info-tooltip.js`の
  `data-info-text`属性を利用（CLAUDE_CODE_START.mdの既存規約に準拠。日付が
  値ごとに変わる動的内容のためglossary.json静的辞書は使わず、新規エントリ追加なし）
- **「—」表示との視覚的区別**: 「—」は引き続き`var(--mut)`単色・記号なし。
  フォールバック値は「実数値＋※マーク＋ⓘアイコン」で構成が異なり、一目で
  区別可能
- **動作確認**: ローカルでheadless Chromeを使い実際にレンダリング結果を
  スクリーンショット確認（テスト用に`market_data.json`へ一時的に
  `is_fallback:true`のダミーデータを注入→確認後に元の状態へ復元、
  リポジトリには反映していない）。短期国債(^IRX)タイルが「+1.05%※ⓘ」と
  灰色背景で表示され、同じ画面内でLQD列の「—」（データなし）、SPY列の
  通常色「+1.04%」（正常値）と明確に区別できることを確認。S&P500メトリック
  カードでも同様に「7,501※ⓘ」表示を確認。pytest 110件全パス・
  check_links.pyエラー0件・market_data.json正常パースを維持
- **SYSTEM_MAP.md**: 新規システム・新規データ依存関係の追加ではなく既存
  Market Pulse内部の表示ロジック拡張のため、更新不要と判断

✅ [MP-IRX-FRED-1] 短期国債データ取得をyfinance(^IRX)からFRED API(DGS3MO)へ切替（2026-06-21 完了）
- **発端**: `asset_flow.short_bond`（^IRX）がGitHub Actions環境からの収集で
  4日連続（6/18〜6/21）取得失敗（None）。Yahoo Finance公式サイトでは同期間の
  ^IRXデータが実在することをユーザーが直接確認しており、「データ不在」では
  なく「取得経路側の問題」と判明（推定原因: GitHub Actions環境のクラウドIPに
  対するYahoo側レート制限。スクリプト内に約29回の逐次yfinance呼び出しに
  対しsleep等の間隔調整が皆無で、かつ`^IRX`等の指数系シンボルはETF系シンボル
  （SHV/GLD/TLT/LQD/HYG/SPY、同期間14日で実質ノーエラー）よりYahoo側の
  配信が不安定という状況証拠あり。GitHub Actions実行ログ自体は本セッション
  からは認証不足のため確認不可だった）
- **対応**: `collect_asset_flow()`内の`short_bond`のみ、新設の
  `fetch_fred_short_bond()`経由でFRED API（`DGS3MO`＝3ヶ月T-Bill流通市場
  利回り系列）から取得するよう切替。`fredapi`は既存の`fetch_vxn_from_fred()`
  （VXNCLS取得）と同じ`FRED_API_KEY`環境変数・呼び出しパターンを踏襲しており、
  GitHub Secrets側の追加設定は不要（`Market_Pulse_Update.yml`に既に
  `FRED_API_KEY`が渡されている）
- **他6資産（yfinance経由）には一切手を加えていない**。ループ内で
  `short_bond`のみ専用関数に分岐させる形で、既存の`result`辞書構造
  （label/ticker/desc/value/change_pct/date）はそのまま維持
- **change_pctの定義**: 他6資産（ETF価格ベース）との表示整合性を優先し、
  ^IRX時代と同じ「利回り値そのものの変化率（%）」をそのまま踏襲（bp差分には
  変更していない）。フロントエンド（`renderAssetFlow()`）側の表示ロジック・
  色分け・ツールチップは無改修で動作する
- **FREDの更新ラグ対応**: DGS3MOは1営業日程度遅れて公表されるため、
  `date`フィールドはFRED側の実際の最終データ日付をそのまま採用（既存の
  他資産が休場日に前回値の日付を据え置く挙動と同じ設計）
- **副次対応**: `collect_asset_flow()`の残り6資産（yfinance経由）の
  `hist is None`等の取得失敗分岐に、失敗理由（hist=None／行数不足／NaN混入）
  を切り分けるログ出力を追加。次回同種の取得失敗が他銘柄で発生した場合に
  GitHub Actionsログから直接原因を追えるようにした
- **動作確認**: ローカル環境（FRED_API_KEY設定済み）で`fetch_fred_short_bond()`
  単体・`collect_asset_flow()`全体を実行し、`short_bond`が`value=3.83,
  date=2026-06-17`（FREDの最新公表日）で正常取得されることを確認。他6資産も
  従来通りyfinance経由で正常値を返すことを確認。pytest 110件全パス維持
- **SYSTEM_MAP.md**: 「Market Pulse ← yfinance / CNN F&G / FREDデータ」の
  記載が既にFREDを情報源として含んでいたため、更新不要と判断（確認済み）

✅ [MP-RENDERALL-CRASH-1] Market Pulse表示崩れ（テックパルス未計算・スコア構成指標50%固定・Tech Pulseセクション「LOADING」停止）の一連の対応（2026-06-21 完了）
- **経緯①（症状発覚〜応急処置）**: 本日朝の自動更新コミット`ccd763082`（github-actions[bot]）で
  `market_data.json`に生の`NaN`トークンが24箇所混入 →`Response.json()`構文エラー→
  `index.html`が無言で`makeSample()`（ダミーデータ）にフォールバック（症状: テックパルス
  未計算、スコア構成指標6/7が50%固定）。`NaN`→`null`へのsurgical手動修正で復旧
  （ロールバックではなく直接修正を採用。理由は当日分の正当なデータを失わないため）
- **経緯②（恒久対応＝MP-DATA-NULL-1）**: `collect_and_send.py`の`Close`値抽出12箇所に
  `math.isnan()`ガードを追加し、`NaN`の再混入自体を防止（詳細は[[MP-DATA-NULL-1]]参照）
- **経緯③（新たな症状の発覚）**: ②の対応後、Tech Pulseセクションが「LOADING」のまま
  停止し、CNN F&G/VXN/QQQ vs SPY/乖離Zスコアが表示されない別症状が判明
- **根本原因**: `renderMetrics()`内`ind.value.toFixed(2)`（610行目）が、②によって
  `null`化された値（`S&P500`/`NASDAQ`等。オブジェクト自体は存在し`value`フィールドのみ
  `null`という形）に対して例外を投げていた。`renderAll()`が同期・try-catchなしで
  各render関数を直列呼び出ししていたため、1関数の例外で後続6関数（`renderMetricBtns`
  以降、Tech Pulse描画を含む）が一切実行されなくなる構造的問題だった。
  `renderAssetFlow()`の`pct.toFixed(2)`（`asset_flow.ig_bond`等）にも同型の漏れがあり、
  610行目の例外に隠れて潜在していた
- **根本修正（コミット`1a03e1b42`）**:
  `renderMetrics()`/`renderAssetFlow()`/`renderTimeline()`にnullガードを追加し、
  既存の「データなし」表示（カード/タイルの`—`表示）にフォールバックするよう統一。
  `renderAll()`を`RENDER_ALL_FNS`配列＋`forEach`+`try-catch`化し、1関数の例外が
  後続の描画を連鎖停止させない構造に変更（例外発生時は`console.error`で関数名付き
  ログを出力し無言で握りつぶさない）
- **横展開確認**: ファイル内の`.toFixed()`/`.toLocaleString()`呼び出し全箇所を監査。
  VIX9D比較（`vix9dRow`）はPython側でデータ無効時にオブジェクト全体が`null`になる
  設計のため既存ガードで安全、`sub_scores`系はPython側で常にスコアが補完される
  設計（無効時は中立値0.5＝50点を設定）のため安全と確認し、追加修正は不要と判断
- **教訓**: `NaN`の直接JSON出力という収集側の欠陥（MP-DATA-NULL-1）が表面化した際、
  その場しのぎでJSONを直すだけでは「オブジェクトは存在するが個別フィールドが
  `null`」という新しい状態を生み、フロントエンド側に潜在していた別のnullガード
  漏れを誘発した。データ修復とフロントエンドのエラー耐性（1箇所の例外が全体を
  道連れにしない設計）は別レイヤーの課題であり、両方そろって初めて再発に強い
  状態になる

✅ [MP-DATA-NULL-1] Market Pulse収集データのNaN混入防御（応急処置＋恒久対応、2026-06-21 完了）
- **発端**: Market Pulse画面で「テックパルス未計算」「スコア構成指標の多くが50%固定」と
  ユーザー報告。調査の結果、本日朝の自動更新コミット`ccd763082`（github-actions[bot]、
  cron 21:35 UTC実行）で`market_data.json`に生の（クォートされていない）`NaN`トークンが
  24箇所混入し、ブラウザ側`Response.json()`が構文エラーで例外 →
  `index.html`の`catch{allData=makeSample()}`が無言でダミーデータにフォールバックしていた
  ことが直接原因と判明（前回コミット`cf566c2ad`は NaN 0件で正常）
- **応急処置**: `market_data.json`の24箇所の生`NaN`トークンを`null`へ surgical 置換
  （ロールバックではなく手動修正を採用。理由: 当該エントリ内の他フィールド
  （tech_pulse score=78等）は正常値であり、ロールバックすると本日分の正当なデータが
  失われるため。CLAUDE_CODE_START.mdの「自動生成データファイルをcheckout --theirs等で
  古い版に巻き戻さない」原則とも整合）。修正後`json.load`で65件全件パース成功を確認
- **恒久対応**: `collect_and_send.py`に`_is_nan()`ヘルパーを新設し、Close値抽出箇所
  12箇所（main_tickers/NYSE Composite/IVW・IVE/大型対小型比/VIX9D vs VIX/HYG・LQD・
  HYG対LQD比/collect_asset_flow/_get_sp500_ma_deviation/fetch_qqq_tech_data/
  format_line）に`math.isnan()`ガードを追加し、NaN検出時は既存の`None`フォールバック
  経路（`data[name]=None`等）に合流させた。`compute_sentiment()`等の下流ロジックは
  元々`is not None`チェックで作られておりNaNだけがすり抜けていたため、下流の修正は不要
  だった
- **副次的に発見・修正したバグ**: NYSE Compositeブロックで`divergence_vs_sp`の算出に
  同一条件の判定が2箇所に重複しており（`sp_hist`の検証を2回別々に実施）、NaNガードを
  片方にだけ追加すると`UnboundLocalError`になることをモックテストで検出。`sp_valid`
  フラグに一本化して解消（ARCH-DATA-1的な「同一判定の分散」パターンと同根）
- **検証**: ①ライブ実行で`get_realtime_data()`がNaN 0件を返すことを確認、②`^GSPC`の
  最新Closeを`NaN`にモックした再現テストでクラッシュなく`S&P500:null`に正しく
  フォールバックすることを確認、③`json.dumps(data, allow_nan=False)`で厳密JSON妥当性を
  確認、④pytest 130件全パス（market_data.csv側にも同根の小文字`nan`文字列混入が
  残存することを発見したが、CSVは現状どこからも読み込まれておらず実害なしのため
  今回は対象外として記録のみ）
- **対応C（保留・報告のみ）**: `index.html`の「fetchエラー時に無言でダミーデータへ
  フォールバック」設計は変更せず、挙動の説明のみユーザーに報告（設計判断はユーザー側）

✅ [EPIC-HEADER-1] ページヘッダー・タイトル共通部品化（2026-06-21 完了）
- **統合元9件全件対応**: TVAL-HEADER-1/2/3, TSCORE-FIX-1/3/4, EPS-DISP-1, HOME-FIX-2
  （TVAL-HEADER-4はEPIC自体の実行で解消）。対象4画面（TANUKI VALUATION/TANUKI SCORE/
  EPS ANALYZER/HOME）に適用。stock.html（個別銘柄詳細ページ）は動的バージョンタグの
  実用性が異なるため対象外として現状維持
- **新設**: `docs/common/site-header.js`（`header a.logo`を検出し、ロゴ画像・ドット・
  タイトル・サブタイトルを統一DOMに置換。`body[data-tool]`からツール名/タイトル/
  サブタイトルを自動解決。`data-title`/`data-subtitle`/`data-no-subtitle`属性で
  ページごとに上書き可能。バージョン表記は撤廃方針のため生成しない）
- **site-theme.css拡張**: `--tool-*`トークンをHOME画面の`.card-*`配色を正として統一
  （tanuki: #a78bfa→#8b5cf6、eps: #22d3ee→#3b82f6 に補正。tanuki-score/discover/
  portfolio/tailのbody[data-tool]マッピングを新規追加、tail はportfolio配下のため
  同色を採用）。`.site-header-inner`コンポーネントCSSと専用keyframe
  `site-header-pulse`（`color-mix(var(--acc))`でツール別アクセントに自動追従する
  パルス発光）を追加
- **発見した副次的効果**: TANUKI SCOREページは`.logo-dot`が`var(--grn)`固定で
  ページ内の実際のアクセント色（Daily Pick等で既に使われていた#14b8a6ティール）と
  不一致だった。新トークンへの統一でこの不一致が解消。HOME画面の`.card-vm`/`.card-tanuki`
  も「枠線・タグ等の`--card-acc`」と「タイトル文字の直書きhex」が食い違っていたが
  `--tool-eps`/`--tool-tanuki`補正により一致した
- TANUKI SCOREは独自に`--mono: 'DM Mono'`を上書きしSpace Monoフォントを読み込んでいな
  かったため、`--mono`上書きを削除しGoogle Fonts importにSpace Monoを追加（フォント
  不統一の実体的な原因）
- TANUKI SCOREフッターの「計算: Koichi式 v8.0」（TSCORE-FIX-4対象）を削除。
  TANUKI VALUATION/HOMEのヘッダー内version-tagも削除
- 検証: check_links.py リンク切れ0件、4画面とも HTTP 200 で配信されることを確認。
  ブラウザでの実描画確認は環境制約上未実施（手動確認を推奨）

✅ [TSCORE-DAILYPICK-BUG-1] TANUKI SCORE「今日の特選銘柄」APIキー未設定エラー表示（2026-06-21 完了）
- **直接原因①**: `daily_pick.json`が2026-06-20 17:16 JSTにXAI_API_KEY未設定のローカル検証実行
  （ARCH-SCORE-SYNC-1 Stage3のテスト目的）の出力のまま本番コミットされていた
- **直接原因②（自動更新が直らなかった真因）**: `daily_pick.py`の`build_data_package()`が
  `mkt.get("indicators", {}).get("VIX9D（短期VIX）", {}).get("value")`という3階層チェーンで
  market_data.jsonを参照していたが、`indicators["VIX9D（短期VIX）"]`がキー自体は存在し値が
  `None`の場合（2026-06-19以降発生）、`dict.get(key, default)`のdefaultはキー不在時のみ有効
  なため`None.get("value")`でAttributeErrorが発生し、GitHub Actions側の自動実行
  （XAI_API_KEY設定済み環境）が`Run daily_pick`ステップで2日連続クラッシュしていた
  （このバグ自体は2026-05-23のコミットから存在する潜在バグで、本日・前日の変更とは無関係）
- **修正**: `_nested_get(d, *keys)`ヘルパーを新設し、ネスト辞書アクセスを「途中の値がNone/非dict
  ならその時点でNoneを返す」安全な実装に統一。3階層チェーン10箇所（vix/vix9d/tech_pulse系/
  asset_flow系）を置換。2階層チェーン（isinstanceガード済みで元々安全）は変更なし
- **データ復旧**: 修正後にXAI_API_KEYを使ってdaily_pick.pyをローカル実行し、正常な
  AIレポート付きdaily_pick.json/history.jsonを生成・コミット（workflow_dispatchの
  実行権限がローカル環境になかったため、同等の結果が得られるローカル実行で代替）
- 「選出理由：分類変化：仕込み時 → BUY」表記は別件・コードバグではなく、ARCH-SCORE-SYNC-1
  での分類体系統一直後に旧history.json内の旧ラベルと1回だけ比較されて生じた想定内の
  過渡的表記と判明（history.jsonは新規実行ごとに新ラベルへ更新されるため自然に解消する）
- 予防的に`src/portfolio/snapshot.py`の同型パターン（「ドル円」「S&P500」参照箇所、
  daily_pick.pyと同じ`TANUKI_Score_Update.yml`内で連続実行されるため波及リスクがあった）
  にも同じ`_nested_get`ヘルパーを適用
- 検証: ローカル再現テストでクラッシュを確認 → 修正適用後に再実行しクラッシュ解消を確認、
  Playwrightで実機ページの「APIキー未設定」表示が消え正常なAIレポートが表示されることを
  確認。pytest 152件全パス、check_links.py リンク切れ0件

✅ [EPIC-LEGEND-1] 指標説明・凡例コンポーネントの共通化（2026-06-21 完了）
- **統合元18件中15件を実装、3件は別種の問題と判明し除外**（詳細はBACKLOG.md該当項目の注記参照）:
  - 除外: HYPE-DISP-5（X軸整列＝レイアウトバグ）, MP-DISP-6（俳句フレーズ＝要否判断タスク）,
    TVAL-FORMULA-1（算式整合性監査＝説明追加ではなく実装監査）
- **共通コンポーネント新設**: `docs/common/glossary.json`（用語キー→説明文の静的辞書）、
  `docs/common/info-tooltip.js`（`<span data-info="key">`を自動検出しホバー/タップでポップ
  アップ表示。動的に追加されるDOM要素もMutationObserverで自動検出。後から動的な説明文を
  付与したい場合は`data-info-text="..."`属性も後付けで使える ― 属性変更もMutationObserver
  で監視）
- **試験実装で発見・修正したバグ**: `<span data-info>`をクリックで開閉トグルする初期実装は、
  ホバーで開いた直後のクリックで即座に閉じる不具合があった。クリックは「常に開く/再描画」
  のみとし、閉じる動作はmouseleave・ドキュメントクリック・スクロールに委譲する設計に変更
- **システム別実装内容**（計15箇所＋既存tip-box拡張2箇所）:
  - HYPE CORE: index.htmlステージ列見出し、detail.html PEG・EV/EBITDA・株価チャート背景色凡例
    （計4箇所。チャート背景色は当初index.htmlのみだったが原文確認でdetail.htmlが本来の対象と判明し追加）
  - DISCOVER: 要注目ゾーン判定基準、ニュースタグ色凡例（2箇所）
  - PORTFOLIO: HYPEMIX危険バッジ判定基準（1箇所）
  - TANUKI TAIL: テーゼ健全度の基準（1箇所）
  - MARKET PULSE: VIX判定文言、乖離基準、資金の動き「–」表示の意味、スコア構成バー色凡例（4箇所）
  - MACRO PULSE: REPO/TGA/RRP用語、REGIMEの解釈、AI失敗時のmodel欄の意味、FOMC声明日付
    （4箇所。FOMC声明日付は`data-info-text`による動的注入の実例）
  - STONKS SILO: 生存期間「–」・黒字化「–」の意味、拡大再生産ドットの意味
    （生存期間・黒字化は既存の`tip-box`カスタムツールチップに追記する形で対応。
    新規コンポーネントとの二重実装を避けるための判断）
  - TANUKI SCORE: DuPont⚠マーク（`data-info-text`化で可読性改善）、ROE色分け基準（2箇所）
- **CLAUDE_CODE_START.md更新**: 「新規銘柄属性を追加した場合の必須対応」に③として
  「ユーザー向け数値・バッジを追加した場合はglossary.jsonに説明を追加する」を追記（再発防止）
- 検証: 全システムでPlaywrightによる実機ホバー/クリック確認、pytest152件全パス、
  check_links.pyリンク切れ0件を確認してから各システム単位でコミット

✅ [ARCH-MATRIX-DUP-1] RICE×乖離率マトリクスの重複・差異実装（2026-06-21 完了）
- **設計判断（ユーザー確定）**: TANUKI SCORE「②RICE×乖離率マトリクス」とTANUKI VALUATION
  「①投資効率系」はそれぞれ異なる用途（前者=多銘柄の最終相対判断、後者=TANUKI VALUATION
  自体・RICE指標の精度検証）を持つため統合せず、両画面とも維持。表示差異のみ解消する方針
- `docs/value-monitor/tanuki_valuation/stock.html`のX軸（乖離率）上限を+100%固定クランプ
  から、tanuki_score側と同じ+300%（X_MAX_CLIP方式）に変更。`buildScatterSVG()`に`xClip`
  オプションを追加し、超過銘柄は右端に▶で縦積み折りたたみ表示（tanuki_score側のoverDotsと
  同方式）。`xClip`は①投資効率系パネルのみ指定し、②③④パネルは未指定のため挙動不変
- ラベル重なり回避ロジックを追加（`xClip`指定時のみ有効）。tanuki_score側の「ドット直上
  固定配置」を基準に、ラベルのバウンディングボックスが衝突しなくなるまで上方向へ
  ずらす貪欲アルゴリズムを実装。X軸+300%化と合わせて、FOUR/TASK/ADBE/NVDA/INTU/CPRT/
  FRSH/GTLB/META/FLYW等の密集を解消
- 対象銘柄ゲート（`rice.available`チェック）の差異を予防的に解消。tanuki_score側の
  `_stocks`構築に`riceAvailable`フィールドを追加し、`renderRiceMatrix()`のフィルタに
  `s.riceAvailable`を追加（stock.html側の`rice.available && riceVal>=0`と同条件に統一）
- 配色ロジック（TANUKI SCORE7分類 vs 象限位置ベース4色）は意図的に維持・変更なし
- **検証（Playwrightで実ページ起動・実データ照合）**:
  - ラベル重なり: 修正前7件（IOT-GOOGL/IOT-NOW/IOT-HQY/CPRT-META/FLYW-INTU/FRSH-GTLB/
    NVDA-FOUR）→ 修正後0件（バウンディングボックス衝突検出で確認）
  - 座標一致: 両画面のRICE有効銘柄49件全件で、ticker集合・upside値・RICE値が完全一致
    （差異0件）。SVGのtitle要素から実測値を抽出し _stocks の値と直接比較
- 検証: pytest 152件全パス、check_links.py リンク切れ0件

✅ [MACRO-COMPUTE-DUP-1] カスタム比較機能のスコア計算が別ロジック（lerp方式）で第3の値を返す（2026-06-21 完了）
- **調査結果（実装前にユーザー確認済み）**: `computeScoreAsOf()`のlerp方式は重複バグではなく、
  コミット`c3eb81572`（2026-05-22「RECESSIONスコアをステップ関数→線形補間に変更（閾値付近の
  急変を緩和）」）で意図的に導入されたもの。用途はスコア履歴チャート（1996年〜の長期推移、
  `renderScoreHistory`）とL3レーダーの時間スライダー（`onL3SliderInput`）で、過去日付を
  辿る際の急激な階段状ジャンプを緩和する目的。renderPhaseGauge()側はstep関数のまま据え置き
  だったため、asOf=「現在」を渡した場合だけstep版（38）とlerp版（35）の3つ目の値が出ていた
- **実装方針**: 全面統一（step化 or lerp化）ではなく、asOfが実質「現在」を指す場合のみ
  renderPhaseGauge()と完全に同一のロジックを使い、過去日付は引き続きlerpで補間する方式を
  採用（5/22の意図的な急変緩和修正を維持しつつ、「現在」の3値問題のみ解消）
- `renderPhaseGauge()`の指標スコア計算部分（trend3考慮のstep関数、8指標分）を
  `computeCurrentScore()`として分離・共通化。`renderPhaseGauge()`はこれを呼び出してDOM
  描画のみ行う構成に変更。`computeScoreAsOf(asOf)`の冒頭に`isEffectivelyNow(asOf)`判定を
  追加し、真の場合は`computeCurrentScore().score`をそのまま返す
- 検証（Playwrightで実ページを起動し検証。pytestではカバーできないフロントエンドJSのため）:
  `computeCurrentScore().score` / `renderPhaseGauge`のゲージ表示値 / `computeScoreAsOf(now)`
  / `computeScoreAsOf(今日23:59:59)`の4値が完全一致（27）することを確認。60日前等の過去日付
  では`isEffectivelyNow`=false・lerp値（30）を引き続き返すことを確認（lerp区分は維持）。
  比較バー4セル（3ヶ月前/2ヶ月前/前月末/先週）も正常表示・JSエラーなしを確認
- 検証: pytest 152件全パス、check_links.py リンク切れ0件

✅ [ARCH-PORTFOLIO-DUP-1] portfolio/index.htmlに独自のfunda/timing/classify実装が存在（2026-06-21 完了）
- ARCH-SCORE-SYNC-1の方針（判断ロジックをpipeline.pyに集約し、表示側は再計算しない）に
  倣い、`docs/portfolio/index.html`の独自実装`calcFunda()`/`calcTiming()`/`classify()`を
  削除。保有銘柄テーブルの分類は`latest.json`の`tanuki_score`/`funda_score`/`timing_score`を
  直接参照する方式に変更（PORT-LOGIC-1のfindHypemixCandidates()と同一パターンに統一）
- 副次的に、独自timing計算でのみ使われていたMarket Pulse fear&greedフェッチ（M_PATH/mkt/fg）
  が完全に不要になったため、フェッチ呼び出し自体を削除（不要なネットワークリクエスト解消）
- **実データでの差異検証**（保有中9銘柄: NVDA/PLTR/TSLA/CELH/APP/CRWV/SOFI/SOUN/ADBE）:
  分類バッジが旧計算と一致しなかったのは4/9銘柄（TSLA: HOLD→TRIM、CRWV: BUY→WATCH、
  SOFI: HOLD→WATCH、SOUN: HOLD→WATCH）。funda_scoreも6/9銘柄で乖離（旧JSの簡易3要素
  計算 vs pipeline.pyのRICE等を含む本格計算のため）。timing_scoreは全銘柄で一致
  （ARCH-SCORE-SYNC-1時点で既にtanuki_score/index.html側のtiming式とpipeline.pyが
  揃っていたため）。この差異はバグではなく、より正確なpipeline.py側の判定に
  統一されたことによる意図した変化
- 検証: pytest 152件全パス、check_links.py リンク切れ0件、div開閉整合性確認

✅ [TAIL-SEC-1] GH TOKENの平文入力欄がセキュリティリスク（TANUKI TAIL画面・2026-06-21 完了・2段階対応）
- 段階1（認証ゲート）: `docs/portfolio/tail/index.html`に`docs/portfolio/index.html`と同等の
  sessionStorageベース簡易パスワード保護（`checkPassword()`/SHA-256ハッシュ照合）を追加。
  PW_HASHはportfolio/index.htmlと共通値を流用、SESSION_KEYは`tail_auth`としてページ別に分離
- 段階2（トークン運用の根本対応）: ブラウザから直接実行していたGitHub Contents API
  書き込み（`fetchFile()`/`commitFile()`、contents:write権限のPATが必要）を廃止し、
  GitHub Actions `workflow_dispatch`経由の書き込みに移行。対象は「ポジション登録」
  「ジャーナル記録」「KPI確定」の3処理すべて（ユーザー判断により全件移行）
  - 新設: `.github/workflows/TANUKI_TAIL_Position_Write.yml`（workflow_dispatch、
    `action`/`payload`入力、GITHUB_TOKEN・contents:writeで書き込み・コミット・push）
  - 新設: `src/tail/workflow_write.py`（register_position/register_journal/confirm_kpis
    のサーバーサイド実装。コミットメッセージは`/tmp/tail_commit_message.txt`経由で
    `git commit -F`に渡し、シェルへの直接埋め込み（インジェクションリスク）を回避）
  - `tail/index.html`側はGH TOKEN欄の用途をactions:write専用のFine-grained PATに変更
    （placeholder/ヘルプ文言を更新）。書き込みが非同期になったため、登録系3関数は
    完了確認メッセージを「反映まで数十秒〜数分」に変更し、楽観的なローカル即時更新を廃止
  - テスト追加: `tests/test_tail_workflow_write.py`（11件、tmp_pathで実ファイルに触れず検証）
- 検証: pytest 152件全パス、check_links.py リンク切れ0件、ローカルサーバーで認証ゲートの
  表示・main-content非表示初期状態を確認

✅ [PORT-LOGIC-1] HYPEMIX注記の誘導先が不適切（PORTFOLIO画面・2026-06-21 完了）
- 設計判断: 「仕込みゾーン不足」時のDISCOVER誘導文言を廃止し、登録済み・分析済み銘柄
  （TANUKI VALUATION全96銘柄ロスター）からTANUKI SCORE BUY判定×HypeCore早期フェーズ
  （失望/蓄積期・期待覚醒期・期待拡大期）×未保有のAND条件で候補を直接抽出し、
  HYPEMIXセクション内にリスト表示する方式に変更
- 実装: `docs/portfolio/index.html`にtickers.json（全銘柄ロスター）取得を追加し、
  既存のtanukiMap/hypeMapフェッチ対象を保有銘柄のみから全銘柄に拡張。
  `findHypemixCandidates()`を新設し、latest.jsonの`tanuki_score`/`funda_score`/
  `timing_score`を直接参照（ARCH-SCORE-SYNC-1の方針を踏襲、独自再計算は行わない）
- 並び順: daily_pick.pyのstocks.sort（-funda, -timing）に揃え、上位5件まで表示
- 0件時は「BUY判定×仕込みゾーンの新規候補銘柄は現在ありません。」と表示
- 検証: 実データ（latest.json/poc.json）でのPythonシミュレーションにより、
  現状3件（NVDA/MO/VZ）が正しい順序で抽出されることを確認。pytest 110件全パス、
  check_links.py でリンク切れ0件を確認。既存のフェーズ分布表示・乖離判定ロジック
  （devHtml/badgeCls等）は変更していないため影響なし

✅ [DISCOVER-BUG-1] CELHで同一記事が重複表示される（2026-06-21 完了）
- 原因: `src/discover/collect.py`に重複排除ロジックが一切存在しなかった（不具合ではなく未実装）。
  NEWS_API/Grok web検索が同一の出来事（Bernsteinの格付け変更等）を複数配信元の別記事として
  取得し、Grokがそれぞれを別アイテムとして分類していた
- 修正: タイトル正規化（trim+小文字化）での完全一致を除外する`_dedupe_items()`を新設し、
  `classify_news()`・`classify_news_with_grok_search()`の両方に適用（同一バグパターンが
  両関数に存在したため横展開）。両関数のGrokプロンプトにも「同一の出来事を報じる複数の
  見出しは1件にまとめる」指示を追加
- 検証: pytest 110件全パス。ダミーデータ（完全一致・大文字小文字違い・前後空白違いの
  3バリエーション＋importance=なし）で重複排除が正しく機能することを確認

✅ [HYPE-BUG-3] 一覧テーブル「推奨」列のソートが機能していない（2026-06-21 完了）
- 原因: `docs/value-monitor/hypecore/index.html`のソート比較関数が、文字列以外を一律
  `av-bv`で数値減算していた。`rec`列のみ`{cat,text}`オブジェクトを格納しており、
  オブジェクト同士の減算は常に`NaN`になるため`sort()`が実質無効化されていた
- 修正: `REC_ORDER={buy:0,hold:1,watch:2,sell:3}`を新設し、`sortCol==='rec'`の場合は
  投資判断の優先順位（強い推奨が上位）でcatを比較する専用分岐を追加
- `getRec()`が返す`cat`値はbuy/hold/sell/watchの4種のみであることをコードレビューで確認済み
  （該当4分岐＋デフォルトのwatchフォールバックのみで、他のcat値は存在しない）
- 他列（ticker/lc/stage/phase/price/piv/revyoy/rule40/ma200/peak）のソートロジックは
  変更なし。Pythonでの比較関数シミュレーションで昇順/降順とも正しい並び替えを確認済み
  （ブラウザ実機確認は環境制約により省略）

---

## 2026-06-20

✅ [HYPE-BUG-1] 「成長期」セクションの本文が黒文字で読めない（2026-06-20 完了）
- 原因: `docs/value-monitor/hypecore/detail.html`の`.narrative-toggle`（button要素）に
  `color`未指定。button要素は祖先のcolorを自動継承しないブラウザ仕様のため、
  子要素`.narrative-toggle-headline`（同じく色指定漏れ）がUAデフォルトの黒系文字色になり、
  暗色背景（`var(--sur2)`）とのコントラスト不足で読めなくなっていた
- 修正: `.narrative-toggle`に`color:inherit`を追加し、ボタン内の子孫要素全体が
  ページの文字色（`var(--txt)`）を継承するように変更
- `.narrative-toggle-phase`/`.narrative-toggle-arrow`は個別`color`指定済みのため
  本修正による影響なし（直接指定が継承より優先されるため）
- 横展開確認: 同パターン（button自体にもcolor未指定）を他ページの主要button class
  （`.cond-toggle`/`.low-toggle`/`.type-btn`/`.tab`/`.filter-btn`×2/`.chart-btn`）で
  簡易grep確認したが該当なし。いずれもbutton自体にcolor明示済みで安全

✅ [MACRO-BUG-1] RECESSION RISK SCOREとAI Weekly Commentaryのスコア不一致（2026-06-20 完了）
- 原因①（本質）: `index.html`の過去時点再構築（`computeScoreAsOf`/`latestDataDateBefore`）が
  `release_date`のみでフィルタしており、後日`05_events.csv`にバックフィルされたデータ
  （release_dateは過去日付だが実際の取込みは後日）が過去時点表示に先読み混入していた
  （look-ahead bias）。6/13時点のPhilly Fed指数が好例：当時の実値は-0.4だったが、
  6/19に取り込まれた最新値10.3が「6/13時点」の計算に紛れ込み、スコアが37→27に変動
- 修正①: `IND_INDEX`に`updatedMs`（データの実取込み時刻）を追加し、新設の
  `idxLatestKnownAsOf()`で`dateMs<=対象日 かつ updatedMs<=対象日`の両方を要求する
  方式に変更。`latestActualAsOf()`/`latestDataDateBefore()`をこれに切替え。
  現在時点表示（`renderPhaseGauge()`）は対象外（最新の改訂後データを見せるのが正しいため）
- 原因②（副次）: `05_main.py` `_compute_current_score()`にPhilly Fed/Initial Claimsの
  トレンド補正（±10pt）が欠落しており、「renderPhaseGaugeと同一ロジック」というコメントが
  実態と乖離していた
- 修正②: トレンド補正をPython側にも追加し、JS `renderPhaseGauge()`と完全一致させた
- 検証: look-ahead bias単体修正後、6/13時点の再計算は凍結値37と完全一致を確認。
  トレンド補正も同時適用すると38（Philly Fedの正しいトレンド加点+10が反映されるため、
  1pt上振れは想定通り・バグではない）。現在時点のメイン画面スコアは27のまま不変を確認
- 残課題: `computeScoreAsOf()`はlerp（連続補間）方式、Pythonはstep+trend（離散閾値）方式と
  根本的に異なる計算式のため、別途ARCH-MATRIX-DUP-1的な一本化課題として残る可能性あり
  （本対応のスコープ外、未着手）

✅ [ARCH-SCORE-SYNC-1] TANUKI SCORE判定ロジックの一本化（根本解決・2026-06-20 完了）
- Python（pipeline.py）/JS（tanuki_score/index.html）/daily_pick.pyの3箇所に
  分散していた独自分類実装（calcFunda/calcTiming/classify相当）を全廃し、
  pipeline.pyが計算する6分類（BUY/WATCH/HOLD/GROWTH_PREMIUM/TRIM/SELL/PASS）
  をlatest.jsonに一本化。JS/daily_pick.pyはその値をそのまま表示・選定に使う
  構成に変更（4段階でコミット: pipeline.py→index.html→daily_pick.py→workflow yml）
- pipeline.pyに不足していたsellTech条件（技術的SELL判定）・timing_score・
  matrix位置情報・sell_reason構造化フラグを新規追加。JS側にしかなかった
  ロジックの欠落を解消し、Matrix④のFCFマージン定義も実績値に統一
- daily_pick.pyのSELL/TRIM/PASS除外ロジックを追加し、SELL判定銘柄が
  「特選銘柄」として強気寄りラベルで表示される問題を解消（ダミーデータで
  SELL非選出を実証）
- TANUKI_Score_Update.ymlをworkflow_runトリガーに変更し、daily_pick.pyが
  pipeline.py完了前に古いデータを参照する実行順序逆転リスク（実測で
  cron遅延2〜4時間を確認）を解消。土日は独立cronで現状の毎日実行を維持
- pytest 110件全パス。残課題: Stage1コミット時点でNVDA以外の95銘柄は
  新フィールド（timing_score等）未反映のため、次回平日pipeline実行
  （月曜23:05 JST想定）またはマニュアル全銘柄再生成で解消する

✅ [RICE-THRESHOLD-1] RICE閾値・マトリクス表示改善（2026-06-20 完了）
- 旧閾値2.0（理論的根拠なし）を理論値ベース（RICE<1.0=低効率/1.0〜3.0=中効率/
  RICE>=3.0=高効率）に統一。対象: tanuki_score/index.html・stock.html・
  pipeline.py（report.txt生成部）の計4箇所
- 両マトリクス（tanuki_score「②RICE×乖離率」・stock.html「①投資効率系」）の
  Y軸を対数軸化し、NVDA等の外れ値による中央値帯の圧縮（旧表示で下から
  7.5〜15.7%に圧縮）を解消
- RICE<=0（計算不能・マイナス）は対数軸でプロット不可なため下端に▼で別枠表示
- 判定ロジック（_compute_tanuki_score）は変更せず表示のみ対応。pytest 110件
  全パス、report_consistency_check.py NG=0、全96銘柄でBUY/TRIM/WATCH等判定が
  変更前後で完全一致を確認済み（commit bc9c1dc71）
- 検証過程で判明した別課題（TANUKI SCORE判定ロジックがRICEをほぼ参照して
  いない）はARCH-SCORE-SYNC-1の関連事実としてBACKLOG.mdに残置・別タスク化

---

## 2026-06-19

✅ [HOME-FIX-1] 「Gemini API」誤記の修正（2026-06-19 完了）
- HOME画面FEATURESセクション「AI POWERED」カードの説明文に
  `Grok API / Gemini API` という併記が残存していた
- GeminiはGrokに移行済みのため `Grok API` のみに修正
- 対象: docs/index.html（229行目）

---

## 2026-06-17

✅ [BUG-INSIDER-1] インサイダー取引データ取得バグ修正（2026-06-17 完了）
- data_fetcher.py の Form4 XML取得が `form4.xml` 固定パスで提出者依存のファイル名
  （wk-form4_xxx.xml等）に404、85/96銘柄が buy=0/sell=0 の誤表示になっていた
- `filings.recent.primaryDocument` の実ファイル名（basename）を使う方式に修正。
  PLTR sell=46 / NVDA sell=40 / TSLA sell=33 / AAPL sell=13(対照・変化なし) を実機検証
- 修正後 0/0 表示は85→14銘柄に減少。report_consistency_check.py NG=0確認後コミット

✅ [BUG-TTM-Q4DUP-1] ttm_calculator.py implied-Q4 二重計上バグ修正（2026-06-17 完了）
- `_build_q4_quarterly_entries()` に既存end日付チェックを追加（financial_trend_calculator.py
  の実証済み重複排除パターンを適用）。テスト4件追加（tests/test_ttm_calculator.py）
- 全97銘柄でbefore/after差分確認: NetIncome/Revenue等87銘柄で重複混入を検出、
  うち8件（IONQ 3.84倍等）が1.5倍以上の乖離・3件（IOT/SPIR/SITM）が符号反転
- update.py→pipeline.py全銘柄再生成、report_consistency_check.py NG=0確認後コミット

✅ [BUG-DUPONT-1] DuPont分解レビュー由来の4改善（2026-06-17 完了）
- 一過性NI集中チェック（reliability=LOW・19銘柄該当）・dupont_bs_period追加・
  表示バッジ（|ROE|>100%等）・極小売上除外（$10M閾値、該当0件）
- 残課題はTANUKI-ROE-3としてBACKLOG.mdに記録（テスト追加・閾値再検証）

✅ [TANUKI-ROE-3] DuPont売上閾値引き上げ＋テスト追加（2026-06-17 完了）
- 極小売上除外の閾値を $10M → $15M に引き上げ。QBTS（TTM Revenue=$12.4M）が除外対象に
  （変更前: net_margin=-2957%等の極端値表示 → 変更後: excluded=true）
- tests/test_pipeline_logic.py にDuPontユニットテスト7件追加
  （正常計算・Equity除外・売上閾値境界値・reliability=LOW判定・極端ROE計算）
- pytest 119件全パス、report_consistency_check.py NG=0確認後コミット

## 2026-06-16

✅ [REPORT-4] 既知リスクイベント表示（2026-06-16 完了）
- risk_fetcher.py 新規作成: Grok API (grok-3) 英語プロンプトで継続中リスクを最大3件取得
- pipeline.py 統合: --skip-risk フラグ追加、cik_lookup.csv から会社名取得
- stock.html: 既知リスクイベントセクション（高/中/低 バッジ、色分け）
- impactNorm() で英語(high/mid/low)・日本語(高/中/低)両対応

✅ [REPORT-1] DCF感応度分析表示（2026-06-16 完了）
- stock.htmlに割引率Rm(8-12%)×成長率(base±5%/±2%/base)の5×5感応度テーブル追加
- 現在株価超=緑・未満=赤の色分け、現在パラメータセルを太枠ハイライト
- JS側計算のみ・バックエンド変更なし

✅ [REPORT-5] データタイムスタンプ表示（2026-06-16 完了）
- stock.html フッター直上に財務基準日・生成日・次回決算・インサイダー最終日を1行表示
- バックエンド変更なし・既存フィールド（fcf_ttm_end/calculation_date等）を活用

✅ [HYPE-2] HypeCoreヒストリカルパーセンタイル表示（2026-06-16 完了）
- poc.jsonの月次30件からexpectation_scoreのパーセンタイルをJS側で計算
- stock.htmlのMATRIX×HYPEバッジ直下に「現在値 | 過去30ヶ月中XX%ile」を追加
- 色分け: 80%ile以上=赤/50-79%=オレンジ/20-49%=グレー/20%未満=緑

✅ [REPORT-3] インサイダー取引履歴表示（2026-06-16 完了）
- SEC EDGAR Form4 XML解析で直近90日の買い/売り件数・純方向を取得
- stock.htmlにインサイダー1行カード追加（Buy優勢=緑/Sell優勢=赤/中立=グレー）
- report.txt Insider_Activity行追加

✅ [REPORT-2] アナリスト目標株価レンジ表示（2026-06-16 完了）
- data_fetcher.py/core_calculator.py/pipeline.py にアナリスト目標株価6フィールド追加
- stock.html に中央値・レンジ・推奨・vs IV乖離率の3列カード追加
- report.txt Analyst_Consensus行を中央値/レンジ/件数/vs IV形式に拡充

✅ [TANUKI-ROE-1] デュポン分解ROE分析（TANUKI SCOREに追加）（2026-06-16 完了）
- normalizer.py/quarterly.py/ttm_calculator.py に TotalAssets追加・全銘柄update.py再実行
- pipeline.py にDuPont計算ブロック追加（88/96銘柄・負債超過8銘柄除外）
- tanuki_score/index.html にROE降順・折りたたみパネル追加
- 業種平均比較・潜在ROE試算は[TANUKI-ROE-2]としてBACKLOGに新規追加

✅ [SCORE-1] RICE × VALUATION MATRIX（2026-06-16 完了）
- TANUKI SCORE に SVG 散布図セクション「② RICE × 乖離率マトリクス」を追加
- X軸: 乖離率（+300%クランプ、超過銘柄は▶マーカー＋注記表示）/ Y軸: RICEスコア（上限10クランプ）
- 負RICE銘柄除外・4象限色分け・ホバーtip・クリックで stock.html 遷移

✅ [REVIEW-1 #4] LYFT・MRVL TANUKI VALUATION 再生成（2026-06-16 完了）
- DTA補正（BUG-LYFT-EPS-1）適用後の再生成。LYFT IV=-$0.93 / MRVL IV=$138.75(-55.1%)

---

## 2026-06-15

✅ [BUG-LYFT-EPS-1] DTA（繰延税金資産）認識による adj_eps 異常高値（2026-06-15 完了）
- 対象: LYFT Q4 2025（GAAP NI $2.755B、他四半期 $23M〜$120M）、MRVL は DTA 非該当と確定
- 根本原因: `IncomeTaxExpenseBenefit` に大規模負値（-$2,897M）が発生するが既存の `tax_one_time` タグでは捕捉不可
- 修正: `pipeline.py` に `apply_dta_adjustments()` を追加。Type-A（pretax≤0かつNI>0）/ Type-B（NI>pretax×3）の2パターンを検出し、正常四半期の税費用中央値で補正
- 検証: LYFT Q4 adj_eps $6.5964 → **-$0.3469** ✓ / MRVL tax=+$314M → DTA非該当・正常処理 ✓

✅ [BUG-SCCO-CIK-1] SCCO CIK誤登録＋ProfitLoss未対応によるEPS異常値（2026-06-15 完了）
- **根本原因（二重）**:
  1. cik_lookup.csv に誤CIK 0000077360（=PENTAIR plc、全く別会社）が登録 → 0001001838（Southern Copper Corp）に修正
  2. SCCO は 2012年以降 NetIncomeLoss を申告せず ProfitLoss タグに移行。EPS Analyzer にフォールバックなし → extract_key_facts.py に ProfitLoss 追加、タグ選択ロジックを「最初に見つかったタグ」→「最新データを持つタグ優先」に変更
- **修正ファイル**: config/cik_lookup.csv + src/value/adjusted_eps_analyzer/extract_key_facts.py
- **検証**: Q1 2026 gaap_eps=$1.9252, diluted_shares=821,700,000, net_income=$1,581,900,000 ✓

✅ [TANUKI-SEG-1] LMT・VRT segment_config FY2025更新（2026-06-15 完了）
- **LMT FY2025**: Aeronautics 40%/0.05, MFC 19%(+1%)/0.12(+0.02), RMS 23%(-1%)/0.03(-0.03), Space 18%/0.04(+0.01)
  - MFC: +13.9% YoY（ミサイル需要高）→ growth 0.10→0.12 に引き上げ
  - RMS: +0.3% YoY（ほぼ横ばい）→ growth 0.06→0.03 に引き下げ
- **VRT FY2025**: Americas 62%(+6pt)/0.22, Asia Pacific 20%(-2pt)/0.15, EMEA 18%(-4pt)/0.13
  - Americas: +41.9% YoY（AI データセンター需要急増）→ weight 0.56→0.62、growth 0.15→0.22
  - APAC: +17.5% YoY → weight 0.22→0.20、growth 0.13→0.15
  - EMEA: +1.7% YoY（欧州不振）→ weight 0.22→0.18、growth 0.13 維持
- 出典: LMT Q4 2025 IR リリース（2026-01-29）、VRT Q4 2025 IR リリース（2026-02-11）

✅ [BUG-NOW-SPLIT-1] NOW 株式分割未対応修正（2026-06-15 完了）
- ServiceNow 2025-12-18 5:1分割でQ2/Q3 FY2025の株数が分割前（~209M）のまま残存
- `config/split_history.yaml`（新規）+ `pipeline.py` に `apply_split_adjustments()` を実装
- threshold = post_split_avg / ratio × 1.5 で補正済み四半期（Q1 FY2025など）を誤補正しない
- TTM adj_eps $9.75 → 正常値 ~$3.28 に修正・Adjusted_EPS_PER 10.5x → 31.2x に修正
- 次回 Adjusted_EPS_Analyzer パイプライン実行で quarterly.json が再生成される

✅ [ARCH-CHECK-1] consistency_check をパイプライン出口ゲート化（2026-06-15 完了）
- `report_consistency_check.py` に `--fail-on-ng` / `--ticker` / `--quiet` オプションを argparse で追加
- SEC_Data_Update / TANUKI_VALUATION_Update / Adjusted_Eps_Analyzer_update / Stonks_Silo_Update の4本に `Consistency Check Gate` ステップを挿入（git push の直前）
- NG>0 かつ `--fail-on-ng` 指定時に exit(1) → Actionsに赤バッジ表示でサイレント失敗を防止

✅ [BUG-EPS-ZERO-1] V/XOM/VZ EPS=$0 修正・株式数フォールバック追加 ✅ 2026-06-15
- **V (Visa)**: WeightedAverageNumberOfDilutedSharesOutstanding が XBRL 10-Q に存在しないため EPS=$0 → yfinance fallback で 20四半期に拡充（ただし Class A 株数 ~1.66B = 稀薄化後 2.07B の過小）
- **XOM**: 同タグ 10-Q 未提供 → EarningsPerShareDiluted 逆算（NI/EPS）で 8四半期分を補完、Q4 は yfinance fallback
- **VZ**: quarterly.json は既に有効（18四半期 valid）、EPS pipeline 再実行で summary.json に反映
- **実装**: `extract_key_facts.py` に 3段フォールバック追加（①EPS逆算 ②Basic株数代用 ③yfinance）
- **required_tags に追加**: `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic`

✅ [BUG-IV-DISP-1] KULR/S/TDY IV表示不整合修正（tapering 未適用バグ） ✅ 2026-06-15
- **根本原因**: `core_calculator.py` の `_calc_ivps_with_wacc` が `dcf_type == "tapering"` 時でも 2段階 DCF に fallthrough → メイン IV がタペリング未適用、シナリオ BASE はタペリング適用で不整合
- **修正**: `_calc_ivps_with_wacc` に `elif dcf_type == "tapering"` ブランチを追加
- **修正**: `_res_rm` 計算ブロックにも tapering ブランチを追加（STEP11 表示の一貫性）
- **効果**: KULR IV $5.57 → $5.63（ScenBASE との差 $1.23 → $0.00）、S $29.50 → $23.65、TDY $517.61 → $596.10

✅ [DCF-DEFAULT-G-1] G=15%デフォルト問題修正（set_growth_override が segment 未設定銘柄に無効だったバグ） ✅ 2026-06-15
- **根本原因**: `segment_config.py` の `get_segment_growth` が `_GROWTH_OVERRIDES` を参照するのは segment_config.json に登録 かつ "General" 単一セグメント銘柄のみ → JNJ/MO/PEP/PM/WMT/VZ 等の未設定銘柄では override が無効
- **修正**: `get_segment_growth` 冒頭に `if ticker in _GROWTH_OVERRIDES: return override` を追加（全銘柄対象）
- **修正**: `pipeline.py` の auto-adjustment ブロックに `finally: clear_growth_override(ticker)` を追加
- **修正**: `pipeline.py` Section 4 表示: `Phase1成長率` を DCF 適用値（推奨成長率）に変更、元成長率を別行表示
- **JNJ**: IV $363.76 → $202.12（G=15%→1.47% で upside +51% → -16.1%）
- **VZ**: G=15%→0.9% で IV 大幅変動

**注記（2026-07-09・STDOUT-JSON-MISMATCH-1発見時）**: 本記録を含む
2026-06-11（BUG-SCAN-FULLSCAN-1 Fix2）以降・recommended_g再計算を
伴うDCF関連の完了記録（SEGMENT-1後半バッチ・BUG-NETDEBT-6・
BUG-IV-DISP-1等）は、STDOUT-JSON-MISMATCH-1（2026-07-09根本修正済み）
と同種のstdout/JSON不一致が起きていた可能性があり、記載された数値が
当時のJSON実値と一致しない場合がある。現在の計算結果（最新JSON値）は
本バグ修正後のものであり正確。過去記録の数値は参考情報として扱い、
正確な現在値が必要な場合は都度JSON実値を確認すること。

✅ [FCF-OUTLIER-1] FCF外れ値誤除外修正（DOCN/LITE/VST） ✅ 2026-06-15
- **根本原因**: `analyze_fcf_outlier` が "deviation_large" ルールで `latest_fcf > fcf_5yr_avg`（上方乖離）のケースを一過性コストで「除外」していた。
  一過性コストはFCFを下押しするため、上方乖離が「コスト由来」とするのは矛盾。
- **修正**: `adjustments.py` の `transient_explains` 計算で `is_upward_deviation`（上方乖離）の場合は `False` に強制
  → action が "excluded" → "flagged" に変更
- **DOCN**: FCF base = 4yr avg $86M → 5yr avg $104M（除外撤回）
- **LITE**: FCF base = 4yr avg $49M → 5yr avg $62M（除外撤回）  
- **VST**: FCF base = 4yr avg ? → 5yr avg $1276M（除外撤回）
- テスト: 130/130 pass, consistency_check NG=0

✅ [CHECK-17/18/19] 回帰検知チェック3件を report_consistency_check.py に追加 ✅ 2026-06-15
- **CHECK-17 [NG]**: 直近3年の全四半期 adj_eps=gaap_eps=0.0 → BUG-EPS-ZERO-1 回帰検知
- **CHECK-18 [WARN]**: recommended_g あり & phase1_growth_auto_adjusted=False & source≠segment_weighted & rate≈15% → DCF-DEFAULT-G-1 回帰検知
- **CHECK-19 [NG]**: 直近3年の四半期で diluted_shares=0 かつ NI≠0 → 株式数取得失敗回帰検知
- **日付フィルタ**: 2022-01-01以降のみ対象（旧上場前・スピンオフ前データの偽陽性を除外）
- **テスト結果**: 96銘柄 NG=0 / 警告=3件（既知: ELF PS乖離, LMT/VRT segment陳腐化）

✅ [ROE-ZERO-1] ROE=0% 誤表示修正（PM 等の純資産マイナス銘柄） ✅ 2026-06-15
- **根本原因**: `reader.py` の `get_roe_avg_detail` がすべての年で equity≤0 の場合に `(0.0, 0, False)` を返す → 0%として表示
- **修正**: `roe_list` が空の場合は `(None, 0, False)` を返すよう変更
- **修正**: `data_fetcher.py` の print 文で None を `N/A (負債超過)` と表示
- **修正**: `core_calculator.py` で `roe_avg or 0.0` として alpha 計算に渡す
- **修正**: `validator.py` の 2 箇所で `c.get("roe_10yr_avg") or c.get("roe_used") or 0.0` に変更
- **修正**: `pipeline.py` で `roe_years_used == 0` の場合に `"ROE = N/A (負債超過)"` を表示
- **PM**: 旧 `ROE_avg (?yr) = 0.0%` → 新 `ROE = N/A (負債超過)` ✅
- テスト: 130/130 pass, consistency_check NG=0

✅ [ALPHA-SECTOR-1] VZ Alpha=1.0 過大評価修正（Telecom セクター上限 cap 追加） ✅ 2026-06-15
- **根本原因**: `maturity_config.json` に Communication Services alpha_cap=1.0 が設定されているが Telecom 向けの業種別上限が未設定
  → VZ ROE=30.2% × 0.60 / 0.10 × 0.7 = 1.27 → cap(1.0) → alpha=1.0（過大）
- **修正**: `maturity_config.json` に `_industry_alpha_caps: {"Telecom Services": 0.4}` を追加
- **修正**: `core_calculator.py` の alpha_cap 決定ロジックに industry チェックを追加（業種 > セクターの優先順）
- **VZ**: alpha 1.0 → 0.4（`α: 1.269 → cap(0.4) → 0.400`）
- **VZ IV**: alpha 1.0 → 0.4 でより保守的な IV に変更
- テスト: 130/130 pass, consistency_check NG=0

✅ [AUDIT-SHARES-1] audit.py に yfinance/SEC 株数乖離チェック(5x閾値)を追加 ✅ 2026-06-15
- **実装**: `audit_ticker` に株数乖離チェックを追加（EPS quarterly.json latest vs latest.json components.diluted_shares）
- **閾値**: 5倍以上の乖離で WARN 出力
- **検出例**: SCCO 株数乖離 5.1x（EPS=163.7M vs DCF=834.3M）→ データソース不一致疑い

## 2026-06-14

✅ [MP-DIV-UNIFY] 乖離計算ソースをCNN F&Gに統一（2026-06-14 完了）
- 原因: 乖離=Tech Pulse - feargreedchart.com(~57)で、画面表示のCNN F&G(~34)と不一致
- 修正: div_value = tech_pulse.score - fear_greed.score(CNN) → 乖離+15→+38に正常化
- _get_tp_signal のfg_score<30判定もCNNスコアに更新
- z-score履歴はdivergence.value優先参照(前コミット修正済み)のため次回実行からCNNベースで再計算

✅ [MP-DIV-ZSCORE-FIX] divergence z-score データソース不整合修正（2026-06-14 完了）
- 原因: `_load_div_history` が fear_greed.score（CNN, ~34）を使って履歴構築していたが、
  当日 div_value は fg_score_tech（feargreedchart.com, ~57）から計算 → ソース不一致
- 影響: 誤ったz-score（-0.11 ≒ 平均以下と誤判断 vs 正しくは +0.82 = 平均より上）
- 修正: 保存済み tech_pulse.divergence.value を優先使用 / 旧エントリは components.fg_score で再計算
- 次回 collect_and_send.py 実行からz-scoreが正確に算出される

✅ [MP-REGIME-LABEL] REGIME判定ソース明示（2026-06-14 完了）
- fed_context に regime_source 列を追加（Grok成功時: "FOMC声明分析（Grok）" / fallback時: "DGS1数値ベース"）
- index.html の REGIME セルにサブラベルとして判定ソースを表示
- 旧CSVは ai_reason から後付け推定して補完（3月:DGS1ベース / 4-6月:Grok）
- _fallback_regime の文言を "ZQ先物が…" → "DGS1ベースで…" に更新

✅ [MP-1YEFF-FIX] 1Y EXPECTED FF 表示値バグ修正（2026-06-14 完了）
- 原因: ラベルが "FRED T1YFF" と表示されていたが T1YFF は DGS1-FEDFUNDS スプレッドであり絶対金利ではない
- 修正: DGS1（1年国債利回り）を直接使用 → 表示値 3.62% → 3.85% / IMPLIED CUTS +0.02 → -0.90回
- ZQ=F term premium 補正ロジックを廃止しシンプル化
- サブラベルを「正値=利下げ織り込み / 負値=利上げ・高止まり織り込み」に更新
- 解釈: DGS1(3.85%) > FF(3.625%) = 市場は高金利継続を織り込み中（-0.90 = BALANCED判定）

✅ [MP-DISPLAY-FIX] Macro Pulse 表示バグ3件修正・データ取得ロジック改善（2026-06-14 完了）
- 修正1: NET LIQUIDITY / HY Spread の "++" 二重符号 → chgHtml の sign と fmt lambda が二重加算していた
- 修正2 (コードではなくデータ問題): refresh_monthly_indicators の obs_to_release_lag 導入
  - obs_date+60日の広すぎるウィンドウで既存スロットを飛ばし未来スロットに誤マッピングする問題を修正
  - NFP 2026-06-05 (5月雇用統計) / Building Permits 2026-05-19 を正常取得
  - Recent Signals の最新表示が 5/15 → 6/5 に改善
  - Michigan CS / Mich Inf 1Y は FRED データが April 止まり（FRED 側ラグ、許容）
- 修正3: AI Weekly Commentary ヘッダー "Gemini 2.5 Flash" → "GROK-3-MINI"

✅ [MP-HISTORY-FIX] Market Pulse 過去データ異常値修正・バリデーション追加（2026-06-14 完了）
- 原因: VIX9D列追加時のCSVヘッダズレでsentiment_scoreに誤値（-2.66〜1.41）が42件混入
- 修正: market_data.json 42件再計算・91件→58件に重複集約
- 再発防止: collect_and_send.py に sentiment_score の 0〜100 範囲チェック追加

✅ [MP-PRED-FIX] センチメント予測リターン異常値修正（2026-06-14 完了）
- 原因: 同一列ズレバグによりS&P500.valueに0.08等の誤値 → getAvgRetが+9億%を出力
- 修正: 5/21-6/7の17エントリ全indicators再構築・index.htmlに防衛チェック追加
- Tech Pulse 5/21-6/5欠落はCSV未保存のため復元不可（許容）

---

## 2026-06-13 完了

### ✅ STALE-CHECK-1 フォローアップ (2026-06-13 完了): 11銘柄ステールデータ更新
- **対象**: FICO/ZETA/BBAI/CELH/COHR/CRWV/RCAT/CPRT/ZS/HQY/RBRK（4〜5月決算後未更新）
- **手順**: update.py → pipeline.py → audit.py → consistency_check
- **結果**: 全11銘柄 SEC 再取得完了（11/11）、pipeline PASS=9 WARN=2 FAIL=0 ERROR=0
  - WARN=2 は FICO/CPRT の formula_verification（既存）
  - WARN-8（ステール警告）: 全消去確認済み
- **IV 更新後**: FICO=$928/ZETA=$30.4/BBAI=$1.79/CELH=$21.2/COHR=$39.1/CRWV=$159.8/RCAT=$3.49/CPRT=$49.3/ZS=$141.9/HQY=$105.8/RBRK=$135.7
- **audit.py**: 正常77銘柄・警告2件（CART/JOBY 既存 Revenue None）NG=0
- **consistency_check**: NG=0 全銘柄整合（残警告: ELF WARN-10、LMT/VRT WARN-9 は既存）
- **pytest**: 108件全パス

### ✅ EPS-PER-TTM-1 (2026-06-13 完了): 調整後PERをGAAPと同一TTM期に統一
- **根本課題**: `_calc_adjusted_per` が `annual.json years[0].adjusted_eps`（年次FY）を分母に使うため、GAAP PER（yfinance trailingPE = TTM）と期間不一致。成長株で ADJ>GAAP 逆転（NVDA: 48.3x vs 31.4x）
- **修正**: `core_calculator._calc_adjusted_per` を `quarterly.json` 直近4Q `adjusted_eps` 合計（TTM）に変更。4Q未満は None（年次フォールバック禁止）
- **文言**: report.txt 注記「年次EPSベース」→「TTM調整後EPS: $x.xxxx」、Definition に「same trailing 12M period」明記
- **検証**: NVDA 48.3x → 30.3x（Delta -1.1x）、46銘柄 ADJ/GAAP 非対称を解消
- pytest: 105件全パス / 全78銘柄再生成 FAIL=0

### ✅ ANNUAL-FY-1 (2026-06-13 完了): aggregate_annualを会計年度ベース集計に修正（IV影響あり）
- **根本課題**: `aggregate_annual`（pipeline.py）が `filing_date[:4]` でグループ化するため、非12月FY企業で FY跨ぎ混合が発生。例: NVDA annual.json year=2025 = FY2025Q4+FY2026Q1-Q3（混合）→ 誤FCF推定値を経由してIVに影響
- **修正**: `fiscal_year` フィールドベースに変更。フィールド未設定の場合は `filing_date[:4]` にフォールバック
- **PARSER-1との関係**: 独立した修正。parser.py は期末日年キー、aggregate_annual は会計年度キーで別レイヤー
- **影響**: 20銘柄の annual.json 更新 → `estimate_fcf_from_eps` 経由でIVに波及
  - 大型: NVDA +18% ($201→$238) / MSFT -12% ($621→$546) / AVAV +93% ($54→$105)
  - IOT: applied=False→True（FY2026 adj_ni +$265.8M、本物の黒字化）
  - COHR/LITE/RBRK/S: applied=False のまま（IV変化なし）
- **スポットチェック**: NVDA FY2026=$5.12/AAPL FY2025=$8.11/MSFT FY2025=$15.44（10-K通年と一致）
- **consistency_check追加**: TestAnnualFYConsistency（3件）- 年跨ぎ混合の恒久ガード
- **ARCH-DATA-1注記**: 年度判定が parser.py / extract_key_facts.py / aggregate_annual の3箇所に分散。共通関数化は次の前倒し対象
- pytest: 108件全パス / 全78銘柄再生成 FAIL=0

### ✅ PARSER-1 (2026-06-13 完了): 年次キーを fy→end_date年 に変更
- **根本課題**: FCX の FY2025 10-K で `fy=2025, end='2024-12-31'` エントリが混入し、`annual_2024.json` が生成されない年度ズレ
- **修正1**: `_extract_values` の年次辞書キーを `fy` → `int(end_date[:4])` に変更（end_year ベース）
- **副作用**: INTU（FY end=7月31日）で FY2020 10-K 内の Q1 比較値（`fy=2020, end='2019-10-31', val=$1.16B`）が `end_year=2019` として通年値（$6.78B）を上書きする regression が発生
- **修正2**: `annual_exact_match` 辞書を追加し、`fy==end_year`（exact match）が存在する年度は non-exact エントリによる上書きを禁止する一般解で解決
- **波及検証**: 差分 150件はすべて non-December 決算企業（AAPL/MSFT/NVDA/CRM/ELF/HQY/COHR 等）の FY2019 以前の revenue/NI が正しい FYE 値へ修正されたもので、潜在バグ群の一括解消
- **IV への影響**: 直近5年 FCF 系列は不変のため IV/FCF_Base/CAGR への波及ゼロ
- **検証**: 全 78 銘柄再パース成功（FAIL=0）、exact matchなし競合 234件の tie-break（最新 end_date 優先）は意図通り動作確認済み

### ✅ REPORT-6 (2026-06-13 完了): DCF透明性強化
- `pipeline.py` の report.txt [3]TANUKI VALUATIONに`DCF_FCF_PV`/`DCF_TV_PV`を追加（全銘柄）
- FCF外れ値除外銘柄のみ`DCF_FCF_Base_Detail`/`DCF_FCF_Base_Excluded`を追加出力
- 3段階DCF(three_stage)は`pv_phase1+pv_phase2`、2段階は`pv_high_growth`でFCF現在価値を算出
- pytest: 122件全パス / 全78銘柄再生成: FAIL=0 / NG=0

### ✅ SEGMENT-1 後半バッチ完了 (2026-06-13 完了): LLY/LMT/MRVL/AMAT/VRT/COHR/LITE/CSGP/BSY/ALAB/ELF/AVAV（12銘柄）
- **単一セグメント確認・修正不要（LLY型）**: LLY / MRVL / BSY / ALAB / ELF（5銘柄）
  - MRVL補足: 5エンドマーケット = disaggregated revenue（ASC 606）≠ ASC 280 formal segment。FY2026から2カテゴリ報告へ変更予定だが従来通り単一
- **複数セグメント設定（LMT型）・IV変化一覧**:

| Ticker | セグメント数 | 設定内容 | IV before | IV after | 変化率 |
|--------|------------|---------|-----------|----------|--------|
| LMT | 4 | Aeronautics(40%/5%)/MFC(18%/10%)/RMS(24%/6%)/Space(18%/3%) | $309 | $347 | +12.3% |
| AMAT | 3 | Semiconductor_Systems(74%/8%)/Applied_Global_Services(23%/6%)/Display(3%/2%) | $274 | $253 | -7.5% |
| VRT | 3 | Americas(56%/15%)/Asia_Pacific(22%/13%)/EMEA(22%/13%) | $129 | $101 | -21.0% |
| COHR | 3 | Networking(59%/20%)/Lasers(25%/10%)/Materials(16%/6%) FY2025 | $90 | $39 | -56.5% |
| LITE | 2 | Cloud_Networking(86%/20%)/Industrial_Tech(14%/4%) FY2025 | $60 | $27 | -56.0% |
| CSGP | 2 | North_America(95%/10%)/International(5%/20%) FY2025 | $13.6 | $11.78 | -13.6% |
| AVAV | 3 | Uncrewed_Systems(40%/12%)/Loitering_Munitions(50%/20%)/MacCready_Works(10%/15%) | $135.53 | $94.23 | -30.5% |

- **growth_floor bypass**: segment_configured=True の場合 recommended_g サニティ回避（weighted_growth 直接採用）
- **COHR/LITE の大幅低下**: FCF base が超小型（$31.8M/$62.1M）のためΔgrowth が IV に直接増幅
- **weighted_growth 計算**: sum(weight_i × g_i)。AVAV weighted_g = 16.3%（before recommended_g 25.64%）
- CSGP 補足: net_debt/shares_used=None は全銘柄共通の latest.json 仕様（report.txt の値は正常）
- pytest: 108件全パス / 全銘柄再生成 FAIL=0

### ✅ SEGMENT-1 VST/FCX/SCCO/CEG/KO (2026-06-13 完了): filing準拠セグメント修正
- VST: Texas_ERCOT/East_Nuclear/Retail/West（地理別、wg 7.2%→7.85%、IV $31.36→$33.69）
- FCX: Indonesia/North_America/South_America（Gold独立セグ削除、wg 8.3%→6.4%、IV $3.95→$3.34）
- SCCO: Peruvian_Operations/Mexican_Operations（OtherMetals削除、wg 8.6%→8.45%、IV $17.48→$17.36）
- CEG: Mid_Atlantic/Midwest/ERCOT/New_York/Other_Retail（Calpine統合後、wg 10.3%→9.65%、IV $52.48→$49.54）
- KO: North_America_NAOU/International/Global_Ventures（wg 5.0%→4.7%、IV $46.39→$45.71）
- 残タスク: LLY/LMT/MRVL/AMAT/VRT/COHR/LITE/CSGP/BSY/ALAB/ELF/AVAV（12銘柄）

### ✅ BUG-NETDEBT-6 (2026-06-13 完了): 同一時点原則による Net Debt 計算修正
> ⚠️ ID注記: 本項は当初 BUG-NETDEBT-4 と命名していたが、2026-06-10 完了分に
> 同一 ID（レポート Net Debt 内訳表示）が既存のため BUG-NETDEBT-6 に改番（NETDEBT-5まで使用済み）。
- **原因1**: BUG-NETDEBT-1でCashは最新quarterly上書きされるが、Total_Debtは年次のまま（時点混在）。
  さらに表示値とequity bridge投入値が別物（表示$8.10B vs engine net_cash -$5.26B）という二重の不整合
- **原因2**: CEG等は10-QでLTDebtをLongTermDebtNoncurrentタグで報告するが、quarterly.pyがLongTermDebt(annual tag)のみ参照してNone扱い
- **修正**: quarterly.py に `LongTermDebtNoncurrent` を `_FIELD_FALLBACKS["LTDebt"]` に追加
- **修正**: reader.py + pipeline.py に同一時点原則ブロック実装（quarterly に Cash+LTDebt が揃う場合に全BS項目を同一filingから参照）
- **修正**: pipeline.py に BUG-NETDEBT-2 補完復活（annual lt_debt=0 かつ quarterly LTDebt未取得の場合にnormalized LTDebtで補完）
- **条件設計**: `_q_lt is not None` が必須ゲート。`_q_lt=None`（パース失敗）時は cash-only → BUG-NETDEBT-2 でnormalized補完
- **影響銘柄 (Net_Debt が実質変化)**:
  - CEG: Net_Debt $+8.10B → **+$21.30B**（Calpine買収負債$16.99B Q1 2026反映）、IV $97.39 → **$52.48**
    （乖離 -61% → -79%。ΔIV -$44.91/sh = 100% Net Debt起因: Cash -$7.96 / LTDebt -$27.29 / STDebt -$9.67、FCFベース寄与ゼロ）
  - KO: Net_Debt **-$9.08B → +$27.42B**（annual lt=None → normalized $36.5B補完）
  - ELF: Net_Debt -$0.20B → **+$0.65B**（term loan $0.85B）
  - SOFI: Net_Debt -$3.40B → **+$2.08B**（normalized LTDebt $5.49B、2022データ※）
  - ZS: Net_Debt -$1.20B → **-$0.05B**（convertible notes $1.15B）
  - JOBY: Net_Debt -$2.47B → **-$1.77B**（Toyota financing $0.70B）
  - ※SOFI: 2022-12-31以降の10-Qに標準LTDebtタグなし（銀行移行後の報告変更）。IV計算パスと表示パスは一致。
- **display改善追加**: DCF_FCF_Base行、Net_Debt_Period行、dilution乖離フラグ、beta staleness警告（90日超）、株式数表示修正
- 回帰テスト: 100件パス（変更なし）

### ✅ REPORT-6拡張: DCF再現性の完全確立 (2026-06-13 完了)
- 背景: VST時点のREPORT-6（DCF_FCF_PV/TV_PV追加）では、α倍率・equity bridge・採用株数が
  非表示のため外部AIが「IV再現不能」を全メガキャップで誤指摘（MSFT/NVDA/APP/PLTR/TSLA等）。
  PV2項の和だけではα乗算後段が見えず、α≒0の小型株でのみ偶然近似できていた
- 修正: report.txt [3]DCFブロックを「上から足すと必ずIVになる」構造に再構成
  DCF_FCF_PV → DCF_TV_PV → DCF_v0 → Alpha_Premium → DCF_v0_x_alpha
  → RPO_PV → Growth_Option_PV → Equity_Value(−Net_Debt) → Shares_Used(source明記) → Intrinsic_Value
- 優先株がある銘柄（CELH等）はequity bridgeに控除行を追加表示
- 検証: test_iv_formula.py 5件（MSFT/NVDA/CELH/PLTR/TSLA、誤差<$0.01）。IV値自体は不変（表示追加のみ）
- 効果: 外部レビュー最頻出指摘「IV再現不能」を構造的に解消

### ✅ MATRIX-1 (2026-06-13 完了): ROE_avg窓長のreport.txt明示
- 採用案: (b)動的採用+report表示。Matrix象限ロジック・ROE計算自体は不変（低リスク）
- report.txt [2] Key_Metric_Y を `ROE_avg (Nyr, equity>0全年) = XX%` に変更
- 窓長Nyrは銘柄ごとのequity>0年数を動的算出して表示（VST=7yr/CEG=4yr等）
- 効果: 外部AIが「なぜ固定窓長でないか」を誤検出しなくなる（再現性の可視化）
- 補足設計論点（未対応・低優先）: VST ROE_avg(7yr)=10.5% vs 直近3yr≈31% のように
  窓長次第で象限が動く件は表示で可視化済み。固定窓長化(a)は全銘柄IV波及のため見送り

### ✅ STALE-CHECK-1 (2026-06-13 完了): 決算後未更新データの検出
- report_consistency_check に決算日経過後の未更新検出を追加
- 検出11件: FICO/ZETA/BBAI/CELH/COHR/CRWV/RCAT/CPRT/ZS/HQY/RBRK（4〜5月決算後未更新）
- 次回更新サイクルでSEC再取得を実施予定（残タスク）

### ✅ 独自仕様の注記追加 (2026-06-13 完了): 外部AI誤検出の恒久防止
- RICE定義式を実装に一致: `(G × VC_Factor × Q × CF) / WACC`（VC_Factorが式本体から欠落していた注記バグ）
- FCF_Conversion注記: Adj_NI×rate であり OCF→FCF変換率とは別物。高FCFマージン企業で実績FCFを
  下回るのは正常化前提による保守設計と明記
- IV/割引率注記: 高β銘柄でWACC比IVが高めに出るのは市場リスクを意図的に除外した本源価値の設計。
  市場リスク調整後はWACC_CAPM_ReferenceでのIVを併用
- DCF_Reliability=LOW判定（Policy A明文化）: LOW時はBUY/TRIM/HOLD/WATCH→WATCH、SELL/PASS維持。
  IVは参考値、乖離率は表示するが分類には使用しない

## 2026-06-12 完了

### ✅ CHECK-13 / WARN-12修正 (2026-06-12 完了): RICE負値ラベル回帰検知 + 偽陽性除去
- `report_consistency_check.py` に CHECK-13 追加（RICE<0 時 Matrix Label 確認）
- CHECK-12 の `_latest` 変数名バグ修正（正: `latest`）→ WARN-12 が正常検知されるように
- WARN-12 の false positive 除去: quarterly_STI ≈ annual_STI のとき誤検出しないよう `_sti_already_qtr` 条件追加
- 修正後: NG-13 発生 5 件 → 影響 5 銘柄を再生成 → NG=0 確認
- テスト: `TestRiceNegativeLabel` 3 件追加（total: 100 件パス）

### ✅ RICE-3 (2026-06-12 完了): 負 RICE 値の閾値定義明記
- OCF 赤字時に RICE が負値になるが「低効率」と誤表示されていた問題を修正
- `pipeline.py` の rice_efficiency 判定に `< 0 → "N/A (OCF赤字)"` ブランチを追加（4分類化）
- Matrix Label・RICE_Threshold・Interpretation 定義文すべてに `<0=undefined (OCF negative)` を追記
- IONQ 確認: RICE=-0.552 で Label が "N/A (OCF赤字)" に正しく表示されることを確認

### ✅ BUG-NETDEBT-5 (2026-06-12 完了): ST_Invest期ズレ修正(年次→最新四半期)
- **原因**: BUG-NETDEBT-1でCashは最新四半期bs値に上書きされるが、ST_Investはannual年次のまま
  normalized JSONにShortTermInvestmentsフィールドがなく自動更新経路がなかった
- **修正**: pipeline.py の financial_health 計算ブロックに BUG-NETDEBT-5 ブロック追加
  最新 `quarterly_*.json` の `bs.short_term_investments` で上書き（値が0なら年次にフォールバック）
- **影響26銘柄**: IONQ(-$0.18B)、META(-$12.04B)、MSFT(+$18.16B)、GOOGL(+$7.36B)、
  AAPL(-$4.17B)、AMD(-$1.75B)、AMZN(-$5.05B)、JOBY(-$0.42B) 等
  IONQ: Net_Debt -$1.85B → **-$2.03B**（$1,361M→$1,540M、Q1 2026 から）
- **CHECK-12追加**: `report_consistency_check.py` にCash-STI期整合チェック（WARN-12）
  Cash≈四半期値 かつ STI≈年次値 なら期ズレ未修正として警告。26銘柄修正後NG=0確認済み
- 回帰テスト: Section 23 (3件追加、計97件合格)

### ✅ BUG-REV-SPAC-1 / A-2-TTM (2026-06-12 完了): IONQレビュー指摘: FCF_Margin単年異常 / TTM二義性
- **BUG-REV-SPAC-1 (A-1)**: IONQの2022年10-K `Revenues` タグが$1,235M(SPAC調達金)を誤タグ
  正規営業収益 `RevenueFromContractWithCustomerExcludingAssessedTax`=$11.1M と重複
  `merge_all_tags=True` + 同一end_date で先頭タグ `Revenues` が勝ち、FCF_Margin 2022=-4.4% に (正常値は-485%)
  修正: `TICKER_RESTRICTIONS["IONQ"]["revenue_concept"]` で単一タグ固定
  横断スキャン: 全79銘柄に同型バグなし (ASTS/JOBY/RCATは正常高成長)
- **A-2-TTM**: [3]`TTM_Revenue_Growth=201.9%` (実TTM YoY) と
  [4]`TTM15.0%のため中央値モデル適用` (`_trigger_max`=max(phase1_g, CAGR)) が同一`TTM`表記
  修正: [3]→`TTM_YoY_Growth`, [4]中央値→`CAGR_max=XX%`, [4]逓減→`CAGR_max=`/`G入力値=`
  逓減モデルの start_g もCAGR最大値を優先するよう修正 (IONQ: recommended_g 12.5%→55%)
- **CHECK-11追加**: `report_consistency_check.py` に Revenue孤立年チェック(前後両年<5%の孤立異常値)
- 回帰テスト: Section 22 (5件追加、計94件合格)

## 2026-06-11 完了

### ✅ BUG-NETDEBT-2 (2026-06-11 完了): LongTermDebt優先順位修正による二重計上防止
- 原因: `XBRL_MAPPING["long_term_debt"]` の先頭が `LongTermDebt`（current+non-current合計）だった
  `short_term_debt` で `LongTermDebtCurrent` を別途加算するため、current分が二重計上されていた
- 修正: `parser.py` の `long_term_debt` マッピングを `LongTermDebtNoncurrent` 優先に変更
- 影響: 48銘柄の annual.json を再生成、全銘柄の pipeline を再実行
- DOCN 例: Total_Debt $1.62B → $1.30B、Net_Debt $0.88B → $0.55B
- 回帰テスト: `tests/test_pipeline_logic.py` Section 21 (3件追加、計89件合格)

### ✅ SEC-REV-FINTECH-1 (2026-06-11 完了): 金融系銘柄 annual revenue 過小評価の修正
- 原因: `MERGE_ALL_TAGS` 動作で狭義 `RevenueFromContractWithCustomer`($0.62B) が
  広義 `RevenuesNetOfInterestExpense`($3.61B) より先に見つかりrevenuが過小計上
- 修正: `parser.py` に `TICKER_RESTRICTIONS["revenue_concept"]` オーバーライドを実装
  指定タグのみ使用し merge_all=False でシングルタグ取得
- SOFI: FY2024 annual revenue $0.62B → $3.61B 是正
- 回帰テスト: `tests/test_pipeline_logic.py` Section 20 (3件追加)

### ✅ 登録パイプラインWARN清掃 (2026-06-11 完了): WARN 23→10 件
- CSGP/ZS: HypeCore実行によりデータ整備
- BKNG/FCX: `eps=false` 設定（XBRL quarterly NetIncomeLoss データ欠如）
- ASML: IFRS外国企業のため cik_lookup.csv から削除
- 孤立エントリ削除: CRWD/FIG/MDB/PUBM/WEAV (tanuki=false なのにエントリ残存) + REKR/SENS/VUZI
- `registration_validator.py` に `eps_disabled` 除外ロジック追加
- `CLAUDE_CODE_START.md` に EPS analyzer Step 5b / IFRS注意事項 を補強

### ✅ BUG-RPO-1 whitelist構造化 (2026-06-11 完了): RPO適用をwhitelist+比率条件に構造化
- _get_rpo_application_rate に via_whitelist フラグを追加（whitelist登録銘柄は比率チェック免除）
- adjust_rpo に RPO/Revenue < 0.3 の比率ゲートを実装（whitelist以外全員適用）
- exclusion_reason を rpo_adjustment に格納、report.txt の RPO_PV 行に除外理由を表示
- V(ratio=0.11)・BSY(ratio=0.18)が除外、GOOGL/MSCI は維持

### ✅ DCF_Reliability=LOW SCORE丸め (2026-06-11 完了): LOWのとき WATCH に統一
- _compute_tanuki_score にて fcf_floor_applied > 0 の場合 SELL/PASS 以外を WATCH に丸める
- score_comment に「DCF信頼性LOW(実績FCF赤字)のためupside依存判定を抑制→WATCH」を付記
- CRWV: HOLD → WATCH に変更（期待通り）

### ✅ BUG-ROE-NI-1 (2026-06-11 完了): ROE集計でnet_incomeがNoneの年を除外していた問題
- 原因: SEC XBRL旧フォーマット(2015-2019頃)は net_income=None だがeps_diluted×sharesから代替推計可能
- 修正: get_roe_avg_detail() に `eps_diluted × shares_diluted` フォールバックを追加（NI=None時）
- 結果: CAKE 5yr平均ROE 5.2%→13.4% (有効年数 5→10年、COVID赤字年の影響が薄まる)
- 汎用修正: 同様の旧SEC形式を持つ全銘柄に自動適用

### ✅ BUG-FCF-CAGR-SPAN-1 (2026-06-11 完了): FCF CAGR計算の固定3年指数バグ
- 原因: `(fcf_new/fcf_old)**(1/3)` の固定指数が年次データ欠落時に誤ったCAGRを算出
  CAKE: annual_2022.json 欠落 → 実際は4年スパンなのに3年として計算
- 修正: `span = yr_new - yr_old` で実際の年数差を算出し `(1/span)` を使用
- ラベル変更: `FCF_CAGR_3yr` → `FCF_CAGR_{span}yr`（スパン明示）
- 結果: CAKE FCF_CAGR_4yr: +1.5%（旧: FCF_CAGR_3yr: +2.0%）

### ✅ BUG-SCAN-FULLSCAN-1 (2026-06-11 完了): 全79銘柄スキャンによるバグ3件の発見と修正
- **Fix1 (core_calculator.py)**: `scenario_valuations` を `growth_result.source == "segment_weighted"` ゲートなしで全銘柄に計算
  - 旧バグ: segment未設定の15銘柄でBEAR/BULLが $0.00 / Growth=0.0% になっていた
  - 修正: `if growth_result.source == "segment_weighted":` ガードを削除し無条件計算に変更
- **Fix2 (pipeline.py _load_extra_data)**: segment_config.json 未登録銘柄に `segment_configured=False` をセット
  - 旧バグ: 未登録銘柄では `extra.get("segment_configured", True)` が True を返し `_is_seg_unconfigured=False` になっていた
  - 修正: `not segs` のとき `result["segment_configured"] = False` を追加
- **Fix3 (pipeline.py _generate_report)**: Matrix② 定義文の ROE 年数を `roe_years_used` から動的生成
  - 旧バグ: 固定文字列 `"ROE_10yr_avg"` を使用、6年・8年集計の銘柄で不一致
  - 修正: `_roe_n_def = comps.get("roe_years_used") or 10` で動的に年数を取得
- スキャナー: `common/sec_data/phase1_scan.py` を新規作成（10カテゴリ 全銘柄検査）
- 再実行: 影響15銘柄 + Matrix②5銘柄 を再生成 → NG=0 / WARN=12(期限切れ決算日11件+軽微逆転1件)
- 回帰テスト: `tests/test_pipeline_logic.py` にFix1/Fix2/Fix3の回帰防止テスト6件を追加 (計83件合格)

### ✅ CONFIG-CAKE-SEG-1 (2026-06-11 完了): CAKEセグメント設定の名称・注記修正
- 修正: segment_config.json CAKE エントリー更新
  "Restaurant Sales" → "Restaurant Operations"（North Italia/FRC brands含む）
  "Bakery Operations" → "Bakery & Other"（外部卸売バクリー配送のみ）
- fiscal_year: FY2025 に更新

### ✅ FEAT-CHECK9-1 (2026-06-11 完了): consistency_check CHECK-9 セグメント設定陳腐化検知
- report_consistency_check.py に CHECK-9 追加（WARN）
- segment_config の fiscal_year が Generated年から2年以上前の場合 WARN-9 を発行
- _raw_lines を _parse_report() 結果に追加して Generated 行の年を取得
- 現状: FY2025設定(2026年生成)は1年差のためWARN未発動（設計通り）

---

## 2026-06-10 完了

### ✅ BUG-FCFBASE-2 (2026-06-10 完了): FCF赤字銘柄DCFガード
- DCF_Reliability: HIGH/LOW を report.txt に追加（revenue_floor適用時 = LOW）
- FCF_Base 表示を調整前後併記（実績avg: $-XX.XM を付記）
- 「5yr平均」を実データ年数で動的化（fcf_list_raw の len を使用）

### ✅ BUG-MATRIX4-1 (2026-06-10 完了): Matrix④ Y軸をFCF_History実績と統一
- Matrix④ Key_Metric_Y を fcf_history 最新年の実績マージンに修正
- （従来: FCF_Base/Revenue の比率 → 過大評価バイアスあり）
- **追補 (2026-06-11)**: fcf_history[-1]がNone(上場直後・SEC未取得年末尾)の銘柄で
  revenue_floor正値にフォールバックするバグを修正（RCATで検出）
  → reversed()で最新非Noneエントリーを採用 / 全None+floor適用時はN/A表示

### ✅ BUG-NETDEBT-4 (2026-06-10 完了): レポートNet Debt内訳表示
> 注記: これは表示のみの修正。同一時点原則によるNet Debt計算修正（当初BUG-NETDEBT-4と
> 重複命名されていた2026-06-13分）は BUG-NETDEBT-6 に改番済み（2026-06-13セクション参照）。
- Total_Debt/Cash 行に ST_Invest を追加表示（残高 > 0 の場合）
- 定義文を "Total Debt - Cash - Short_Term_Investments" に修正

### ✅ BUG-WACC-DISP-1 (2026-06-10 完了): 割引率表示の分離
- "WACC: XX%" を "Discount_Rate_Primary: 10.00%" + "WACC_CAPM_Reference: XX%" に分離
- 定義文も両者の役割を明記

### ✅ BUG-RPO-1 (2026-06-10 完了): RPO適用条件の強制
- SECTOR_RATES["Technology"] を (1.0, "SaaS") から (0.0, "Non-SaaS") に変更
- SaaS whitelist または industry キーワード（software/cloud/saas/internet）必須に
- NVDA（Semiconductors）の rpo_pv が $170.8M → $0 に修正

### ✅ BUG-ROEAVG-1 (2026-06-10 完了): ROE平均修正
- reader.py: 損失年度も含む全期間を平均（従来: 連続黒字期間のみ・上方バイアスあり）
- winsorize: |ROE| > 80% → ±80% にキャップ（CELH 119% → 80%）
- 動的ラベル: "ROE_avg (Nyr)" 表示、外れ値処理時は "(outlier-adjusted)" タグ追加
- SOFI: -3.9% (6yr) / CELH: -8.5% (10yr, outlier-adjusted)

### ✅ FEAT-SEGCHECK-1 (2026-06-10 完了): セグメント鮮度ガード
- segment_config.json 更新:
  - APP: Apps segment 削除 → Software Platform 100%（2024年 Apps 売却済み）
  - TSLA: Services and Other セグメント追加（12%）、Automotive 87%→77%
- APP の Segment_Weighted_Growth: 34.2% → 45.0% に修正

### ✅ BUG-NETDEBT-3 (2026-06-10 完了): reader.py 主要IV計算経路修正
- 内容: Net Debt補完が主要IVに反映されていなかった問題を解消
- AVGO -$14 / KO -$8 の過大評価を解消
- 修正: reader.py の主要IV計算経路にNet Debtフォールバック補完を適用

### ✅ β修正 (2026-06-10 完了): KO/LLY/HQY のβ値修正
- KO / LLY / HQY の beta_config.json 登録値を実態に合わせて修正

### ✅ TANUKI-DCF-1 (2026-06-10 完了): DCF基準FCFの採用方法改善
**分類:** 設計課題 / TANUKI VALUATION

#### 問題
FCF減少トレンドがある銘柄でDCF理論価格が過大評価される構造的バイアスが存在。

#### ①基準FCFに2年平均を使用 → CAGR < -5% 時に直近値へ自動切替（回復判定付き）
- `calculator/adjustments.py` に CAGR判定ロジック追加
- 最古値が負（先行投資期）の場合は判定スキップ（VST等の誤発動防止）
- method: `recent_1yr` / `avg_5yr_recovery` を新設

#### ②推奨成長率とDCF計算値の乖離 → 警告表示で対応済み
- segment_configured銘柄で recommended_g と実際のDCF成長率の乖離が ≥5pt の場合に
  ⚠️ 警告をレポートに表示（pipeline.py `_generate_report` 内）

#### ③FCFマージン悪化が成長率に未反映 → BEARシナリオへの反映で対応済み
- FCFマージン低下トレンドをBEARシナリオの乗数補正として反映
- `fcf_margin_bear_multiplier` を growth_sanity 経由で pipeline.py に渡す構造を追加

### ✅ BUG-TTM-1 (2026-06-10 完了): TTM Revenue GrowthがQ1単四半期YoYと混同
**分類:** バグ / pipeline.py

#### 問題
TTM Revenue Growthとして表示・DCF計算に使用されている値が、
実際にはQ1単四半期のYoY成長率である場合がある。
- PLTR: 84.7%（真のTTMは約67.8%）
- TSLA: 15.8%（真のTTMは約+2.25%）

#### 修正
TTMは「直近4四半期合計 / 前4四半期合計 - 1」で計算。
単四半期YoYとの混同を防ぐため、計算式を明示的にlog出力する。

### ✅ BUG-NETDEBT-2 (2026-06-10 完了): annual_2025.jsonでlong_term_debtが欠落
**分類:** バグ / pipeline.py / パーサー

#### 問題
4銘柄（AVGO, KO, SOFI, ZS）の `annual_2025.json` に `long_term_debt` が欠落。
- KO: total_debt $1.5B（short_debt のみ）→ 修正後 $38.0B
- AVGO: total_debt ~$3B → 修正後 $69.2B

#### 修正
`_load_extra_data()`, `_calc_g_fundamental()`, `_calc_roic_wacc_ratio()` にて
annual BS の `long_term_debt` が 0 の場合、normalized quarterly JSON の `LTDebt`
最新値（`_get_normalized_lt_debt()` ヘルパー）でフォールバック補完。

### ✅ BUG-NETDEBT-1 (2026-06-10 完了): Net Debt / Cashの定義不整合
**分類:** バグ / pipeline.py

#### 問題
Cash表示値とNet Debt計算値の参照タイミング・定義が不整合。
- PLTR: Cash $1.42B（FY2025末）vs 実際Q1末$2.29B。Net Debt -$7.18Bは短期投資含みだがCash定義と矛盾。
- SOFI: Total Debt $0（実際$1.82B）、Cash $4.93B（実際$3.40B）。

#### 修正（実施済み）
1. CashはSEC最新四半期末の値を使用（FY末ではなく直近10-Q）
2. Net Debt = Total Debt - Cash - Short_Term_Investments と定義を統一
3. Total Debtを明示的に取得・表示する（$0は異常値として警告）

---

## 2026-06-07 完了（TANUKI TAIL主要機能完了）

### ✅ TANUKI TAIL（投資テーゼ継続検証システム）
- Phase 1: テーゼ登録UI（GitHub Contents API ワンボタン保存）
- Phase 2: xbrl_segment_fetcher.py（Layer 2 KPI自動取得）
- Phase 3: EDGAR RSS監視・レビューキュー管理
- Phase 4: Grok四半期レビュー生成（Call 1定量・Call 2定性）
- Phase 5: レビュー表示UI（5タブモーダル）
- Step 0: KPI確定フロー（Grok提案→UI確認）
- Layer 3: MD&A・8-Kテキストからの非XBRL KPI抽出
- tail_dcf_bridge.py: 将来理論価格計算（bear/base/bull×1/3/5年）
- satellite_monitor.py: 変化通知（±20%・エグジット充足・決算接近）
- journal.json: 判断ログ・DECISION LOG UI
- prediction_tracker.py: 過去予測の振り返り
- 残タスク: EWM楽観バイアス係数・データパス統一（優先度低）→ BACKLOG.md管理

---

## 2026-06-03〜04 完了

### ✅ [DESIGN-11] Stonks Silo UEスコアバックエンド補完（2026-06-03 完了）
- analyzer.py に unit_economics_score/label/gross_margin_trend 計算を追加
- IOT/AVAV/ZETA=100pt（優秀）、BBAI/KULR/RDW=0pt（低調）で直感と一致
- ASTS/JOBY は gross_margin_note="construction_phase" で処理

### ✅ [ACTION-6] Macro Extreme Fear戦略実行支援（2026-06-03 完了）
- docs/value-monitor/extreme-fear/index.html を新規作成
- F&Gゲージ・買い候補TOP10・過去EF実績・シミュレーター・メモ欄の5セクション
- スコアリング: BUY+40/WATCH+20/upside+30/funda+20/Phase≤2+10/Phase4-20pt

### ✅ [ACTION-2] 判定実績の自動追跡・検証ループ（2026-06-03 完了）
- score_history.json に判定スナップショットを日次追記
- score_verifier.py で 30/60/90日後リターンを自動計算
- index.html に判定別勝率テーブル＋直近20件を表示
- score_verifier.py の定期実行: Score_Verifier.yml 登録済み（毎日 JST 9:00）
  → 2026-07-03 以降に初回リターンが記録される
- 判定実績セクションをTANUKI VALUATION→TANUKI SCOREに移設（2026-06-04）
  docs/value-monitor/tanuki_score/index.html を新設

### ✅ [ACTION-4] HYPEMIXポートフォリオ管理（2026-06-03 完了）
- フェーズ分布バー・目標乖離・リバランス提案・銘柄テーブルを TANUKI index.html に追加
- 現状: P4=52%（目標10%比+42pt超過）・P1=0%（目標20%比-20pt不足）を検出
- 実装: docs/value-monitor/tanuki_valuation/index.html に renderHypemix() 関数追加

### ✅ [MP-5] IMPLIED CUTS根本解決（2026-06-03 完了）
- get_implied_cuts(): ZQ=F implied rate でterm premium補正・FRED FEDFUNDS/DGS1使用
- 旧: DGS1生値 -0.82cuts（誤）→ 新: ZQ=F補正 +0.01cuts（実態）
- ZQ=F取得失敗時はDGS1生値にフォールバック

### ✅ [MP-4] センチメントゲージへのバックテスト予測ミニゲージ統合（2026-06-03 完了）
- バックテスト表を削除し「明日は？」「5日後は？」「20日後は？」のSVGミニゲージ3つに置換
- 現在ゾーンの過去平均リターンから予測スコア計算（S&P500 +1%≈+2pt換算）
- 点線=現在針・実線=予測針の2針表示

### ✅ [MP-3] 資金フローUI改善：タイルと推移テーブルの縦統合レイアウト（2026-06-03 完了）
- grid-template-columns: 60px + 7列でタイルをヘッダー兼任にした統合グリッドに変更
- 日付行を降順（最新上）でタイル直下に縦連結、色分け・軸ラベル・5日平均フッター維持
- renderAssetFlow/renderAfHeatmapを1関数に統合、旧クラス（af-grid/af-hm-*）を削除

---

## 2026-06-01〜02 完了

### ✅ [MP-1] AIレポート「出来高比」表現の修正（2026-06-02 完了）
- 修正: S&P500/NASDAQ を個別表記に変換してGrokに渡すよう collect_and_send.py を修正
- プロンプトに「指数を限定して記述・両者をまとめる表現禁止」制約を追加

### ✅ [MP-6] AIレポートの表現・解釈バグ（2026-06-02 完了）
- ①債券バッジ「リスクオン/オフ」→「債券売り/買い」に変更（collect_and_send.py + index.html）
- ②信用収縮誤解釈防止：HYG・LQD同時下落→「金利上昇圧力/デュレーションリスク」限定。HYGのみ下落時のみ「信用スプレッド拡大」を許可するプロンプト制約を追加
- ③乖離Zスコア符号定義明示：正=NASDAQ優位/負=S&P500優位をextended_dataとプロンプト両方に付記

### ✅ [MP-2] AIレポート品質改善・表記統一（2026-06-03 完了）
- ①センチメントスコアを:.0f整数変換してGrok渡し・プロンプト小数禁止制約追加
- ②VIX小数点2桁（16.05形式）統一・1桁禁止制約追加
- ③Risk-Off Score 3軸配点（33/33/34pt）と全体要約への1行明記を義務化
- ④VIX9D上昇+1pt未満は「急騰」禁止→「上昇加速(+Xpt)」、+3pt以上のみ「急騰」許可
- ⑤VIX9D＜VIX30D維持しつつ9D上昇加速中は「移行期」文脈を必ず明記
- ⑥NH=xxx, NL=yyy, NH-NL差=±zzzの3値表示に変更・差の拡縮分析を義務化

### ✅ [DESIGN-8] 8-1 推薦理由・スクリーニング条件の可視化（2026-06-01 完了）
- 実装: conditions_met / risk_flags フィールドをGrokプロンプトに追加
  銘柄カードにアコーディオンパネル（▼ 詳細）で展開表示

### ✅ [DESIGN-8] 8-2 ニュース表示の改善（2026-06-01 完了）
- 実装: ニュースタイトルをURLリンク化（hover下線・新タブ）
  出典「via ○○」表示対応（sourceフィールドをGrok出力に追加）
  ニュースなし銘柄をゾーンレベルで折りたたみ（デフォルト非表示）

---

## 2026-05-31 完了

### ✅ [DCF-1] 本当の5年逓減DCFエンジン（2026-05-31 完了）
- 概要: Phase1内でg_start（推奨成長率）→g_end（業界ベンチマーク）へ年次線形逓減
- 適用条件: growth_model=="decay"（TTM>50%）かつindustry_benchmark取得済みの未設定銘柄
- 実装:
  calculator/dcf.py: calculate_tapering_dcf() 追加
  calculator/scenarios.py: tapering_g_end パラメータ追加
  core_calculator.py: calculate_pt(tapering_g_end) に対応
  pipeline.py: _tapering_g_end を growth_sanity から取得して渡す
- 実績: 10銘柄に逓減DCF適用（ALAB例: 51.5%→9.6%、IV $667→$206）
- テスト: 5件追加（計37件）
- 適用外の銘柄と理由:
  segment_configured=True の銘柄（NVDA/META/GOOGL等）→ 手動設定済みのため再計算ブロック非実行
  maturity_config で three_stage DCF の銘柄（NVDA等）→ Phase2で成長減速を既に表現済み
  将来: segment_configured 銘柄への逓減対応は DCF-1b として別途検討

### ✅ [DCF-2] 高成長銘柄向け GROWTH_PREMIUM カテゴリ追加（2026-05-31 完了）
- 概要: 通常TRIM条件（upside<-30%・funda≥50・phase≥3）でも
  逆DCF Required Growth < TTM成長率の場合は GROWTH_PREMIUM を返す
  （現在の成長率が市場要求をすでに上回っているため、プレミアムに根拠あり）
- 実装:
  pipeline.py: _calc_required_growth() 追加（逆DCF・5年CAGR）
  _compute_tanuki_score(): GROWTH_PREMIUM vs TRIM の分岐追加
  valuation_enriched に growth_sanity を事前注入（タイミングバグ修正）
- 実績: ALAB（RequiredG=75% < TTM=93%）→ GROWTH_PREMIUM
        SITM（RequiredG=77% < TTM=88%）→ GROWTH_PREMIUM
        LITE/PLTR（RequiredG > TTM）→ TRIM（従来通り）
- テスト: 3件追加（計40件）

### ✅ [DCF-3] β個別推定の精緻化（2026-05-31 完了）
- 概要: 全67銘柄を yfinance 5年βで一括更新、source フィールドを付与
- 更新ルール:
  上限 2.5（CAPM前提崩壊を防ぐ）/ 下限 0.3（異常値対策）
  LMT のみ Damodaran Aerospace/Defense β=0.74 を使用（yfinance=0.10 は異常値）
- 主要変更:
  NVDA: 1.05 → 2.24（+1.19） WACC 8.9%→17.1%
  LLY:  1.10 → 0.48（−0.62） WACC 10.7%→7.0%
  LMT:  1.10 → 0.74（−0.36） WACC 10.6%→8.5% (Damodaran使用)
  AMD:  1.10 → 2.40（+1.30） GOOGL: 未設定→1.27 追加
  大幅乖離（>0.5）: 25銘柄更新
- 設定ファイル: config/beta_config.json（_updated_at/source フィールド追加）

### ✅ [RICE-1] RICEから成長率依存を減らす（2026-05-31 完了）
- 現状: RICE = (G × Q × CF) / WACC でGが支配的
- 実装: 価値創造係数（VC_Factor）を導入
  新式: RICE = (G × VC_Factor × Q × CF) / WACC
  VC_Factor = clamp(ROIC / WACC_Rm, 0.3, 2.0)
  ROIC = NOPAT / Invested_Capital（最新年次、実効税率21%固定）
  ROIC > WACC（10%）: 再投資が価値創造 → G を最大2倍に増幅
  ROIC < WACC: 再投資が価値毀損 → G を最小0.3倍にペナルティ
  ROIC 不明（赤字企業等）: VC_Factor=1.0（後退互換）
- 結果例: NVDA ROIC/WACC=6.6→cap2.0、MRVL ROIC/WACC=0.63（ペナルティ）
- テスト: 5件追加（計45件）
- 変更ファイル: calculator/rice.py, core_calculator.py, pipeline.py

### ✅ [GROWTH-1] 成長逓減モデルの精緻化（2026-05-31 完了）
- 旧: recommended_g = (TTM + 業界平均) / 2（固定50:50）
- 新: HypeCoreフェーズで重みを調整
  Phase1-2（黎明〜拡大）: TTM×65% ＋ 業界平均×35%（成長継続余地あり）
  Phase3 （陶酔期）     : TTM×50% ＋ 業界平均×50%（旧来バランス）
  Phase4 （剥落期）     : TTM×35% ＋ 業界平均×65%（正規化加速）
- 変更: growth_sanity.py（hype_phase追加）、pipeline.py（_load_hype_phase追加）
- テスト: 3件追加（計55件）

### ✅ [WACC-1] ターミナル成長率の銘柄別設定（2026-05-31 完了）
- 変更: 全銘柄一律 3.0% → Damodaran 業種ベースのセクター別設定
- テーブル:
  テック・半導体・SaaS: 3.5%（デジタル経済の長期構造成長）
  防衛・ヘルスケア・金融: 3.0%
  消費者・飲食: 2.5%（成熟市場）
  業種不明: 3.0%（デフォルト維持）
- 実装:
  maturity_config.py: _DAMODARAN_TV_G・_TICKER_TV_G テーブル追加
  get_terminal_growth(): 直引き→業種→デフォルトの3段階フォールバック
  pipeline.py: _calc_required_growth(tv_g) パラメータ化・GROWTH_PREMIUM判定に適用
- テスト: 7件追加（計52件）

### ✅ [NET-1] financial_health.net_debt と bs_adjustment.net_cash の不整合（2026-05-31 完了）
- 修正: pipeline.py _load_extra_data() で short_term_investments を net_debt に加算
  net_debt = total_debt - cash - short_term_investments
  bs_adjustment.short_term_investments を参照して整合を取る
- 結果: AAPL Net_Debt +67.09B → +48.33B（bs_adjustmentと一致）
  financial_health に short_term_investments フィールドを追加

### ✅ [DESIGN-1] ERP参考表示（2026-05-31 完了）
- 実装: ERP = ForwardEPS/Price - Rf（10年国債利回り）を HYPECORE セクションに追加
  ERP≥4%: 明確な割安感 / 2〜4%: 魅力あり / 0〜2%: 薄い / <0%: 割高感
  pipeline.py: _generate_report() 追加 + latest.json に erp/forward_earnings_yield 保存
- 残タスク: HypeCoreフェーズ判定への組み込みは効果確認後に検討（DESIGN-1b）

### ✅ [DESIGN-3] 将来株価計算機能（2026-05-31 完了）
- 概要: 将来理論株価を3年→5年に拡張、期待リターン表示を追加
- 実装:
  core_calculator.py: projection_years=5 に変更
  core_calculator.py: calculate_return_metrics() の結果を
    "return_metrics" キーとして latest.json に保存
  stock.html: 将来価値テーブルを5列に自動拡張
  stock.html: 「現在株価」行に各年の期待リターン%を緑/赤色で表示
  stock.html: 「5年BASE年率換算: +XX% / 年」を表示
- 実績（NVDA）: 5年後BASE $2,046（年率+57.7%、現在株価$211起点）

### ✅ [DESIGN-7] HYPEMIXの概念導入（2026-05-31 完了）
- 概要: 保有銘柄のHypeCoreフェーズを意図的に分散させる
  ポートフォリオ管理概念（Koichi氏の造語）
- 実装: Phase分布の可視化 + 目標HYPEMIXからの乖離スコア + リバランス提案

### ✅ [DESIGN-8] 8-5 特大テーマの発掘・予測（2026-05-31/2026-06-01 完了）
- 概要: Grokが週次で「次の特大テーマ候補」を分析
  根拠・確度・時間軸を構造化して表示
  「Grokの見解」として参考表示にとどめる

### ✅ [DESIGN-8] 8-6 銘柄への投資テーマ付与とテーマ別比較（2026-05-31 完了）
- 概要: 各銘柄にテーマタグを付与（手動 or AI提案）
  theme_config.jsonで管理・admin.htmlから編集
  テーマ別に登録銘柄を一覧・比較できる画面を追加
  HYPEMIX的な視点（フェーズ分散）も同時表示

### ✅ [DESIGN-10] RICEの三分類見直し（2026-05-31 完了）
- 概要: 現行の閾値2.0（高/低の二分類）を三分類に変更
  高効率: RICE ≥ 2.0（価値創造・現行維持）
  中効率: RICE 1.0〜2.0（資本コスト上回る・価値中立）
  低効率: RICE < 1.0（資本コスト未満・価値破壊水準）
- 理論的根拠: RICE=1.0がWACCとの均衡点
- 実装: pipeline.py Matrix①のラベル三分類化 + テスト5件追加

### ✅ [DESIGN-12] ステルス流動性の3層構造改善（2026-05-31 完了）
- 実装: 3層構造でステルスカードを再構成
  Layer1: FRBレジーム（fed_context.csvから非同期取得）
  Layer2: ステルス流動性（従来のsupply/absorb/neutral＋連続週数）
  Layer3: NET流動性トレンド（▼▼▼で視認性）
- 新カラム: stealth_absorb_weeks / net_liq_decline_weeks / stealth_alert
- 警戒アラート: 3条件を評価して赤枠ボックス表示
- 変更: 05_main.py（計算）/ index.html（3ペイン表示）

### ✅ [DESIGN-13] MACROPULSEでマクロサプライズ検知（2026-05-31 完了）
- 実装: detect_macro_surprises()を05_main.pyに追加
  9指標の前回比急変を閾値検知（NFP±5万、Claims±2万、Philly±10pt等）
  逆指標判定あり（Claims↑=悪化、NFP↓=悪化）
  同カテゴリ2件以上同時悪化→「複合サプライズ」
  カテゴリ: インフレ/雇用/景気（色分けバッジ）
- 保存: weekly_analysis.csv に surprise_alerts カラム追加
- 表示: AI WEEKLY COMMENTARY直前に.surprise-banner追加（空時は非表示）
  Discord通知にもサプライズ一覧を追記

### ✅ [ACTION-10] TANUKI SCOREの変化検知機能（2026-05-31 完了）
- 検知対象: 判定変化（BUY→TRIM等）/ HypeCoreフェーズ転換（Phase2→Phase3等）/ 乖離率の大きな変化（±10pt以上）/ 撤退条件への接近
- 通知タイミング: 変化が発生した時のみ
- 通知先: Discord（既存WEBHOOK活用）

### ✅ [DISCOVER-1] 未発掘銘柄優先のプロンプト改善（2026-05-31 完了）
- 変更内容:
  時価総額: 100億〜1000億ドル → $5億〜$100億（小〜中型）
  機関投資家: 「増加傾向」→ 保有率 < 40%（定量化）
  売上成長: 20%以上 → 30%以上
  追加: 主要指数未採用（S&P500・Russell1000・Nasdaq100等）
  追加: 推薦JSONに market_cap_b / revenue_growth_pct / institutional_ownership_pct を出力
- 実装: src/discover/collect.py の explore_candidates プロンプトのみ変更

### ✅ [BUG-2b] _calc_q: GAAP赤字年のSBC偽陽性Q値（2026-05-31 完了）
- 発見: NI<0年にSBCで earnings>0 になるとQ計算に混入し異常Q値が発生
  例: NI=-469M, SBC=+608M → earnings=139M → Q=OCF/139M=13.43
- 影響: MRVL（Q=6.97→0.51）をはじめ11銘柄のRICE値が不正確だった
  NET/ZS/ZETA/SOUN: 誤ってRICE有りと判定（正しくはQ計算不可）
- 修正: `calculator/rice.py` _calc_q に `if ni < 0: continue` を追加
- テスト: 3件追加（計32件）

### ✅ [BUG-11] quarterly.py: NetIncomeフォールバック未設定（2026-05-31 完了）
- 発見: AVGO/BKNG/AVAVのTTM系列でNI=None（Q計算不可・RICE誤分類）
  原因: quarterly.py が NetIncomeLoss のみ参照し ProfitLoss 等を見ていなかった
  AVGO: NetIncomeLossの四半期データが2019以前で途絶 → ProfitLossが必要
  BKNG: NetIncomeLoss自体が未申告 → NetIncomeLossAvailableToCommonStockholdersBasicが必要
  また _FALLBACK_MIN_FIELDS に NetIncome がなく q_count<4でもフォールバック未発動
- 修正: `common/sec_data/quarterly.py` に NetIncome フォールバック追加
  _FIELD_FALLBACKS["NetIncome"] = (ProfitLoss, NetIncomeLossAvailableToCommonStockholdersBasic)
  _FALLBACK_MIN_FIELDS に NetIncome を追加
- 結果: AVGO RICE=2.3(Matrix①正常), BKNG セクター除外(Matrix②正常), AVAV Q取得成功

### ✅ [FEAT-8] SECデータ品質監査の自動化（2026-05-31 完了）
- `common/sec_data/audit.py` 作成
  NI/OCF/Revenue の全件・一部 None を検出、重大問題は Discord 通知
- `.github/workflows/SEC_Data_Audit.yml` 作成
  SEC_Data_Update 完了後に自動実行
- `CLAUDE_CODE_START.md` にパイプラインコード変更時の必須手順を追記

### ✅ [FEAT-9] Matrix③散布図: Q計算不可銘柄を表示（2026-05-31 完了）
- 赤字銘柄（Q計算不可）が散布図に表示されていなかった
- stock.html の loadAndRenderMatrices を修正
  Q計算不可銘柄もMatrix③にルーティング（11銘柄が新規表示）
  Q異常値（Q>5）との視覚区別: 白ストローク付きドットで区別

### ✅ [FEAT-10] β再発防止の3施策（2026-05-31）
- beta_fetcher.py: 全銘柄βをyfinanceから自動取得・更新（cap2.5/floor0.3）
  Damodaran手動設定は保護、sourceフィールドで取得元を記録
- audit.py --check-beta: SEC監査にβ乖離チェック追加（0.5超で警告、1.0超で重大）
- Beta_Config_Update.yml: 月次自動更新ワークフロー（第1日曜JST8:00）
- CLAUDE_CODE_START.md: 新規銘柄登録Step2にbeta_fetcher.py追加

### ❌ [DESIGN-9] RIMモデル（廃止 2026-05-31）
- 実装後に廃止。理由: 66銘柄中3銘柄のみ信ぴょう性あり（BV/P>30%）
  自社株買い主体のテックポートフォリオでは会計上BVが圧縮されており
  NVDA BV/P=3%・AAPL BV/P=1.6% など大半で過小評価となり誤解を招く

---

## 2026-05-30 完了

### ✅ [BUG-1] FCF外れ値が5年平均に含まれていた
- action="excluded" の結果がbase_fcfに反映されていなかった
- 修正: 外れ値除外後の残り年数で平均を再計算

### ✅ [BUG-2] Q分母のmax(NI+SBC, 1)設計ミス
- 赤字年でQ=数千万倍の異常値が発生
- 修正: 赤字年・利益ほぼゼロ年をスキップ

### ✅ [BUG-3] META Q4 SBC二重タグ問題
- A-2グループ8銘柄に波及修正

### ✅ [BUG-4] GOOGLセグメント設定漏れ
- Cloud Infrastructure 100%→3セグメントに修正

### ✅ [BUG-5] FCFコメント誤判定・HYPE_Signal EPS条件誤り
- FCFマイナスなのに「FCF黒字」表示
- EPS YoYマイナスなのに「EPSは強い」表示

### ✅ [BUG-6] Matrix割高/割安逆転
- upside参照先の誤りを修正

### ✅ [BUG-7] Runway計算バイパス
- 一時的黒字でRunway計算がスキップされていた

### ✅ [BUG-8] substage_watch固定テキスト幻覚
- hypecore.pyの固定文字列をeps_surprise実値ベースに変更

### ✅ [BUG-9] shares_yr年号格納バグ
- 株式数フィールドに年号が入っていた

### ✅ [BUG-10] NOW株式分割（5:1）対応
- 希薄化率72.61%→0.6%に修正

### ✅ [FEAT-1] Damodaran業種別ベンチマーク導入
- growth_sanity.pyによるサニティチェック実装

### ✅ [FEAT-2] 成長率自動精緻化
- セグメント未設定銘柄にTTM実績値を自動適用
- 高成長銘柄（TTM>50%）に逓減モデルを適用
- recommended_gをDCFに反映

### ✅ [FEAT-3] RICE_adj追加
- R&D除外CF（設備投資のみ）ベースのRICE補正版

### ✅ [FEAT-4] 逆DCF分析追加
- 現在株価を正当化する必要成長率を逆算表示

### ✅ [FEAT-5] 希薄化スコア追加
- 6段階評価・report.txt・stock.htmlに表示

### ✅ [FEAT-6] Forward EPS追加
- yfinanceのforwardEpsをレポートに表示

### ✅ [FEAT-7] ユニットテスト24件追加
- 回帰バグ検出の基盤を整備

---

## 過去セッション完了

### ✅ MACRO PULSE 関連
- MACRO PULSE 流動性モニター・NET LIQUIDITY実装
- MACRO PULSE Hollow Rally検知
- MACRO PULSE ステルス流動性（TGA/RRP）可視化

### ✅ TANUKI VALUATION 関連
- αキャップ（上限1.0）実装
- RPO補正実装
- ネットキャッシュ補正を有利子負債のみに限定（実装済みを確認）

### ✅ Stonks Silo 関連
- フロントエンド（HTML）実装済み（index.html 1298行）
- GitHub Actions 設定済み（Stonks_Silo_Update.yml）
- gross_margin: ASTS/JOBY のみ null（construction_phase として扱い）→ 他20銘柄は取得済み

---

## 2026-06-14 完了

✅ [BUG-EPS-UNIT-1] LOAR/ONDS EPS per-share 株式数単位バグ修正 + CHECK-14/15/16追加 ✅ 2026-06-14
- **症状**: LOAR adj_eps=$151/$396/$320（実株価$68）、ONDS Q1 2026 adj_eps=$119.24
- **根本原因**: SEC XBRL の WeightedAverageNumberOfDilutedSharesOutstanding が
  千株単位で報告されているが unit="shares" と誤記されているケース
  LOAR: 全四半期平均95,913 << 1M → 全期間千株単位と判断
  ONDS Q1 2026: 461,706 << 直近8Q中央値×1% → 孤立四半期の千株単位
- **修正**: `extract_key_facts.py` に 2段階サニティチェックを追加
  Stage①: 全期間平均 < 1M → 全四半期 ×1000（LOAR適用）
  Stage②: 直近8Q中央値の1%未満の孤立四半期 → その四半期 ×1000（ONDS適用）
- **CHECK追加**: `report_consistency_check.py` に CHECK-14/15/16 追加
  CHECK-14: adj_eps > 現在株価×50% → NG（単位ミス異常値検知）
  CHECK-15: adj_eps > 現在株価 → NG（さらに深刻な単位ミス）
  CHECK-16: 直近4Q未満のデータ → WARN（TTM不完全）
- **結果**: LOAR FY2025 GAAP_EPS $752.20→$0.7522、Adj_EPS→$1.1061 ✓
  ONDS Q1 2026 株式数461,706→461,706,000、adj_eps $119.24→$0.1192 ✓
  consistency_check: NG=0 確認済み

✅ [BUG-INTU-GROWTH-1] INTU Section 4 Layer 1 成長率表示バグ修正 ✅ 2026-06-14
- **症状**: INTU の [4. 成長率根拠] で "中央値モデル" が 19.7% を参照し
  DCF適用値 12.8% との関係が不明瞭
- **根本原因**: Layer 1（segment_configured=True）銘柄でも Layer 2 と同じ
  表示フローを使っており、DCF G（セグメント加重平均直接）とラベルが乖離
- **修正**: `pipeline.py` Section 4 を `_seg_configured` で分岐
  Layer 1: "セグメント加重モデル（Layer 1）" と表示、recommended_g を "Layer 2 参考値・DCF未適用" と明記
  Layer 2: 従来通り "中央値モデル/逓減モデル"
- **結果**: INTU 報告が "DCF適用値: 12.8%（セグメント加重平均）/ 推奨成長率: 19.7%（Layer 2 参考値）" と整合 ✓

✅ [BUG-INTU-NETDEBT-1] INTU 短期投資 Net Debt 欠落調査 → 誤検知 ✅ 2026-06-14
- **疑惑**: INTU の短期投資がNet Debt計算から漏れている可能性
- **調査結果**: INTU の XBRL には ShortTermInvestments タグが存在しない
  INTUの財務構造上 short_term_investments=0 は正しい値。修正不要。

## [BUG-FOUR-1] FOUR（Shift4 Payments）EPS・株式数・希薄化異常値 ✅ 2026-06-14

### 症状
- Latest_Adjusted_EPS: $49.93（正常値: ~$0.40）
- TTM調整後EPS: $119.70（正常値: ~$1.20）
- Dilution_3yr_Annual: -29.86%/yr（誤）
- ⚠️ 株式数乖離警告: yf=99M vs SEC=1M (+7332.8%)

### 根本原因
FOUR の UP-C LLC 構造変更（2021-2022）後、XBRL の
WeightedAverageNumberOfDilutedSharesOutstanding が
Class A 株式のみを報告（~1.33M）し、実際の経済的持分（~99M）の
約1/74 しか反映されない。10-Q には株式数タグが一切存在しないため、
TTM が4四半期合計ではなく4年分の年次EPS合計になる二次バグも発生。

### 修正内容
1. `config/cik_lookup.csv`: FOURのepsフラグ true→false（EPS Analyzerスキップ）
2. `src/value/tanuki_valuation/pipeline.py`: yf/SEC株式数乖離>10倍の場合に
   希薄化計算をスキップするサニティチェック追加（comps参照修正も含む）
3. `config/discover_config.json`: FOURのmemoにUP-C構造の注意事項を記録

### 汎用効果
SEC/yfinance乖離10倍サニティチェックはFOUR以外にも適用される。
同様のUP-C構造銘柄（APP等）でXBRL異常が発生した際も自動保護される。

### 教訓
UP-C構造（上場会社がLLC管理会社になる形態）ではXBRL株式数が
経済的実態を反映しないケースがある。新規銘柄登録時にUP-C構造の
有無を確認し、該当する場合はeps=false設定を検討する。

---

### [TAIL-EWM-1] EWM楽観バイアス係数の定義明確化
**完了日:** 2026-06-26
**判断:** B案（現状維持）でクローズ

#### 理由
- optimism_bias_warningのUIコードはtail/index.html L1252-1253に実装済み
- predictions/データが生成されれば自動表示される設計になっている
- 数値的EWM係数補正は過剰設計と判断

---

### [GROWTH-VERDICT-SEQUENCING-BUG-1] growth_sanity.verdictがDCF再計算前の初期計算値を検証し続けるシーケンシングバグ
**優先度:** 高
**分類:** アーキテクチャ / TANUKI VALUATION / 検証基盤
**登録日:** 2026-07-19
**完了日:** 2026-07-19
**発見:** [[GROWTH-SANITY-CLASS-SYNC-1]]（完了・本ファイル参照）のMO型iv対応時、
verdict≠PLAUSIBLE全32銘柄の原因分析

#### 問題
`pipeline.py::_save_result()`は`check_growth_sanity()`を、`segment_configured=False`
かつ`recommended_g`算出可能な銘柄向けの再計算（条件付き発火、`recommended_g`による
`calculate_pt()`再実行、`pipeline.py:637-669`）の**前**に1回だけ呼び出す。
`growth_sanity`（`verdict`・`warnings`・`phase1_growth`）はこの初期計算の値
（`fcf_cagr`floor等、しばしば非現実的な値）を検証したまま再計算では
再実行されず、`latest_data`にはそのまま保存される。一方`growth.rate`
（実際にDCF・IVに使われる値）は再計算の`recommended_g`（segment_weighted
ラベルで保存）に置き換わる。結果、**`growth_sanity`が検証している成長率と
実際にDCFへ採用されている成長率が別物になる**。TANUKI SCOREのGROWTH_PREMIUM
判定（`pipeline.py:487`、`_ttm_g = growth_sanity.phase1_growth`参照）も
同じ`_growth_sanity`辞書を参照するため、同一バグの影響を受けていた。

#### 実データでの確認（2026-07-19時点、verdict≠PLAUSIBLE 32銘柄の原因分析時点）
`phase1_growth_auto_adjusted=True`（再計算が発火した）銘柄24件
（ABBV/ASTS/BKNG/BROS/CWAN/DELL/ELF/ENTG/FICO/GEV/HQY/HWM/JNJ/KULR/LLY/
LYFT/MRVL/PEP/RDW/SITM/TER/**VZ**/WMT/XOM）について、実際に採用されている
`recommended_g`で判定ロジックを再計算したところ、**16銘柄がPLAUSIBLE
（またはより軽い区分）へ改善**した：
- PLAUSIBLEへ改善（14件）: ABBV・DELL・ENTG・FICO・GEV・HQY・HWM・JNJ・
  LYFT・MRVL・PEP・RDW・**VZ**・WMT
- AGGRESSIVE→REVIEWへ改善（2件）: CWAN・SITM
- 残り（型iii相当、別途[[GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1]]等で個別判断）:
  ASTS/BKNG/BROS/ELF/KULR/LLY/TERの7件は実際のレートでも警告が残ることを
  当時確認していたが、後日実装時点での61銘柄全数シミュレーション（下記）で
  XOMも同一パターンに該当することが判明し、**8件**（ASTS/BKNG/BROS/ELF/
  KULR/LLY/TER/XOM）が正しい件数と確定した（登録時点の記載漏れ）。

**VZ（Classification: BUY、乖離率+97.7%）が本バグの典型的な実害例**。
verdict算出時のphase1_growth=15.0%（fcf_cagr floor）は業界平均比10.4倍・
過去実績比10.0倍でAGGRESSIVE判定だが、実際にDCFで使われている
`recommended_g=1.44%`（業界平均とほぼ同値）で再評価すれば0警告＝
PLAUSIBLEになる。**VZのAGGRESSIVE判定は完全なバグ由来の誤検知**。

ENTG/GEV/HQYが2026-07-12以降REVIEW→AGGRESSIVEへ悪化していた事象も
本バグが原因（初期計算の中間値が変化したため）と判明した。

#### 対応内容（2026-07-19実装）
再計算（`pipeline.py:637-669`）が成功した直後に、実際にDCF・IVへ採用された
`recommended_g`を基準に`check_growth_sanity()`を再実行し、`verdict`・
`warnings`・`signals`・`phase1_growth`・`floor_hit`のみを更新する方式
（対応方針の「案」を採用）。`recommended_g`・`growth_model`・
`growth_model_reason`等の「どう導出されたか」を示すフィールドは初期計算
パスの値のまま維持し、report.txtの「推奨成長率内訳」表示との不整合が
生じないようにした。

- `pipeline.py:487`（TANUKI SCORE GROWTH_PREMIUM判定の`_ttm_g`）は、
  `_growth_sanity`辞書を共有参照しているため追加コード不要で同時に是正
  （コメントのみ追記）
- report.txt「元成長率」表示は、修正後`growth_sanity.phase1_growth`が
  採用値と同値になるため、`extra["phase1_growth_original"]`（初期計算値、
  修正の影響を受けない）を参照するよう分離
- floor_hit判定は再計算後`growth.source`が`"segment_weighted"`になるため、
  `growth_source=="fcf_cagr"`条件が自動的に不成立となり整合を確認

#### 実装前の安全確認（全母集団シミュレーション、CHAT_RULES.md記載手法）
`phase1_growth_auto_adjusted=True`61銘柄全件について、既存latest.jsonの
データとPipelineの読み取り専用ヘルパーメソッドのみを使い、実際にpipeline.py
を再実行せずオフラインで新旧verdictを比較。結果は以下の通りで、実データ
再生成後の結果と完全一致した：

| 区分 | 件数 | 銘柄 |
|---|---|---|
| verdict改善 | 17件 | ABBV・CWAN・DELL・ENTG・FICO・GEV・HQY・HWM・JNJ・LYFT・MO・MRVL・PEP・RDW・SITM・**VZ**・WMT |
| verdict悪化 | 3件 | ALAB・IONQ・RCAT（PLAUSIBLE→REVIEW） |
| 変化なし（非PLAUSIBLEのまま） | 8件 | ASTS・BKNG・BROS・ELF・KULR・LLY・TER・XOM |
| TANUKI SCORE変化 | 1件 | CON（GROWTH_PREMIUM→TRIM） |

**verdict悪化3件（ALAB/IONQ/RCAT）の個別調査結果**: 3銘柄とも
`growth_model_audit.py`が既に把握している「CAGR_max>100%クランプ」対象
銘柄（NVDA/ONDSと同型）で、初期計算値がたまたま15%floorに張り付いていた
ため見かけ上PLAUSIBLEだったが、実際に採用されているrecommended_g（41〜
55%）は業界平均の4〜5倍あり、本来warningが出るべきケース。業種分類は
ALAB（Semiconductor、SEC SIC 3674と完全一致）・IONQ（Computers_Peripherals、
Damodaranに量子コンピューティング相当の業種が存在しないための構造的限界）
は概ね妥当。RCATのみbeta_config.json内部バケット（Electronics_General）が
yfinance実態（Aerospace & Defense）と食い違っており、これは別途
[[RCAT-SECTOR-MISCLASSIFICATION-1]]として新規登録した（ただし業種を
Aerospace/Defenseに修正してもDamodaran g_ebitはより低くなり乖離は
さらに拡大するため、本バグの悪化3件という結論自体には影響しない）。
3銘柄とも修正前からTANUKI SCORE=WATCHで、verdict変化によるスコアへの
実害はない。「誤ってマスクされていた警告の正しい表面化」と判断し実装を
承認。

#### 検証結果（2026-07-19、実データ再生成）
61銘柄を`pipeline.py <tickers...> --skip-risk`で再生成し、シミュレーション
結果と完全一致することを確認（改善17件・悪化3件・変化なし8件・
TANUKI SCORE変化1件）。git diffで対象61銘柄（+tickers.json）以外に
一切副作用がないことを確認。VZがPLAUSIBLEへ改善・CONがTRIMへ是正された
ことを個別確認。`report_consistency_check.py` NG=0（既存の無関係な
WARN55件のみ）。`pytest tests/` 377 passed（既知の
[[TEST-STALE-IV-1]] MSFT/NVDA 2件を除き新規失敗なし）。

#### 未着手として残した項目
- 8銘柄（ASTS/BKNG/BROS/ELF/KULR/LLY/TER/XOM）の型iii（ハイパーグロースと
  成熟業種平均のミスマッチ）としての扱いは[[GROWTH-STRUCTURAL-MISMATCH-
  CANDIDATES-1]]に委ねる
- growth_sanityのprovenance構造による表示再設計（「初期計算の検証結果」
  と「採用値ベースの検証結果」を両方保持しreport.txt/latest.jsonで区別
  表示する別案）は別途改めて依頼予定
- AIプロンプト経由の定性的楽観バイアス警告（quarterly_review_generator.py）で十分

---

### [FY52WEEK-BS-STI-OVERRIDE-DESIGN-1] short_term_investmentsのKLAC/NVDA/SOFI/TER/V 5銘柄は銘柄別override設計が必要
**優先度:** 中〜高
**分類:** アーキテクチャ / データ品質ゲート
**登録日:** 2026-07-19
**完了日:** 2026-07-19（KLAC/TER/V/SOFIの4銘柄。NVDAは対応タグ未特定のため
[[NVDA-STI-TAG-UNIDENTIFIED-1]]として分離継続）
**発見:** [[FY52WEEK-BS-NULL-SILENT-1]] Phase B「合算/準タグ」12件の個別確定調査

#### 背景
short_term_investments absent銘柄の一次情報確認で、KLAC・NVDA・SOFI・
TER・Vの5銘柄はBS本体に「Marketable securities」「Investment
securities」等の実在する流動資産行を持つことを10-K原本で確認済み
（①候補タグ欠落は確定）。ただし候補となるXBRL値は銘柄ごとに異なる
挙動を示し、単一の汎用候補タグをXBRL_MAPPINGへ追加する方式
（Phase B Stage1で採用した方式）では対応できない：

- **KLAC**: `AvailableForSaleSecuritiesDebtSecuritiesCurrent`系タグは
  債券部分のみで、株式性有価証券（差額約$24M）を除外し実額をわずかに
  過小評価
- **NVDA**: 同タグはBS計上額$51,951Mを約24%（$12.4B）過小評価。
  差額の対応タグをXBRL全項目照合したが特定できず
- **TER/V**: 同タグは非流動分も含む合算値のため、真の流動値を過大評価
  （TER: タグ$97.1M vs 真の流動値$28.2M）。正確な値は
  `AvailableForSaleSecuritiesDebtMaturitiesWithinOneYearFairValue`
  （TER）・`Investments`（V、汎用的すぎる名前で他銘柄への誤爆リスク大）
  という、いずれも汎用候補リストに不向きなタグで個別確認済み
- **SOFI**: 非分類BS（流動/非流動を区分しない銀行持株会社）のため
  「Current」概念自体が適用されにくい。MD&A「Investment securities」
  $2,575.6Mとタグ値の差は約5%（償却原価ベースの違いと推測）

#### 対応内容（2026-07-19実装、KLAC/TER/V/SOFIの4銘柄）
実装前調査で以下4銘柄の正しいXBRL概念を一次情報（SEC EDGAR 10-K原本）で
確定した：

- **KLAC**: `AvailableForSaleSecuritiesDebtSecurities`（"Current"接尾辞
  なし版）。**訂正記録**: 登録時点の背景記述にあった候補タグ
  `AvailableForSaleSecuritiesDebtSecuritiesCurrent`は2021-03-31を最後に
  申告停止済みの死んだタグであることが実装前調査で判明し、使用しな
  かった。BS「Marketable securities」（FY2025: $2,415,715K）の99.0%
  （$2,391,753K）に一致、残差は`EquitySecuritiesFvNiCost`約$22.9Mの
  株式性有価証券（対象外が正しい挙動）
- **TER**: `AvailableForSaleSecuritiesDebtMaturitiesWithinOneYearFairValue`。
  BS「Marketable securities」（FY2025: $28,247K）と誤差ゼロで完全一致
- **V**: `Investments`（"Current"接尾辞なしの汎用タグ名）。BS流動側
  「Investment securities」（FY2025: $1,833,000,000）と完全一致。
  他9銘柄（ADSK/BSY/CEG/CRWV/DELL/LRCX/LYFT/MO/ONDS）が同タグを別の
  意味で申告しているため、グローバル候補リストへの追加は行わずV限定
  オーバーライドとして厳格運用
- **SOFI**: `OtherInvestments`。**経緯記録**: 登録時点では「非分類BS
  特有の近似値許容が必要（MD&A比約5%の残差を許容）」と想定していたが、
  実装前調査でNote 15（公正価値ヒエラルキー）の内訳を確認したところ、
  残差の正体は証券化VIE由来の非AFS分類資産担保証券・残余持分と判明し、
  `OtherInvestments`タグがBS「Investment securities」合計と全期間
  （2021〜2025年）で完全一致することを発見。当初想定していた近似値
  扱いは不要だった

実装は`SOFI-DATA-1`の`ltdebt_concept`ticker_restrictions方式と同型：
- `quarterly.py`の`TICKER_RESTRICTIONS`辞書へ、既存の`ltdebt_concept`と
  同型の`sti_concept`キーを4銘柄分追加（SOFIは既存の`revenue_concept`/
  `ltdebt_concept`に続く3つ目のキー）
- `parser.py::_parse_raw_data()`へ、既存の`ltdebt_concept`分岐と同型の
  `field_name == "short_term_investments" and _sti_concept_override`
  分岐を追加（`xbrl_keys`を単一タグへ完全置換）
- `quarterly.py`のFIELD_CONCEPTS側は変更不要（short_term_investments
  はBS項目のためquarterly.pyのPL/CF専用ロジックの対象外）

#### 実装前の安全確認・検証結果
既存company_facts.jsonのみを使ったオフライン全銘柄再パース
（`SECParser.parse_company_facts()`、ネットワークアクセスなし）で実装
前後を比較し、105銘柄中KLAC/TER/V/SOFIの4銘柄以外に一切変化がないこと
を確認してから本番反映した。

本番反映（`update.py KLAC TER V SOFI`実行）後の実測値は事前確認した
一次情報の値と完全一致：

| Ticker | 実装後の値（annual_2025.json） | 一次情報の値 |
|---|---|---|
| KLAC | $2,391,753,000 | $2,391,753K ✓ |
| TER | $28,247,000 | $28,247K ✓ |
| V | $1,833,000,000 | $1,833,000,000 ✓ |
| SOFI | $2,575,607,000 | $2,575,607K ✓ |

`report_consistency_check.py` NG=0（WARN55件、既存の無関係な項目のみ）。
`pytest tests/` 377 passed（既知の[[TEST-STALE-IV-1]] MSFT/NVDA 2件を
除き新規失敗なし）。git diffでKLAC/TER/V/SOFI（annual/quarterly/
normalized/raw/ttm各ファイル）以外に意図しない変更がないことを確認済み。

#### 副次発見（未対応・別途記録が必要）
実装前後比較のためのオフライン全銘柄再パース実行中、`AVAV`/`COHR`/
`FICO`/`HON`の`fy_collision_log.json`が実行のたびに重複エントリを
蓄積する非決定的な挙動を発見した（本タスクの`sti_concept`変更とは
無関係。`_save_fy_collision_log()`自体は`ticker`引数で正しくスコープ
されているが、衝突検知リスト`_fy_collisions`の構築ロジックに、
再実行のたびに結果が変わりうる要因があると推測される）。今回はscope外
のため該当4ファイルを`git checkout`で復元し、本コミットには含めて
いない。新規BACKLOG項目として別途起票が必要。

#### 未着手として残した項目
NVDA: `AvailableForSaleSecuritiesDebtSecuritiesCurrent`系タグがBS計上額
$51,951Mを約24%（$12.4B）過小評価する問題は、対応タグが特定できて
いない（XBRL全項目照合済みだが該当なし）。[[NVDA-STI-TAG-UNIDENTIFIED-1]]
として分離継続。

---

### ✅ [TTM-PASCALCASE-KEY-STALE-1] フェーズC移行（ttm_series.jsonキーPascalCase→snake_case化）で消費側2箇所が旧キー参照のまま取り残され本番障害化
**優先度:** 高
**分類:** バグ / 移行漏れ
**完了日:** 2026-07-29
**コミット:** a7b840c32fde3b6619707f7a7c588baeaed12fd1
**発見:** [[LAYER3-TTM-REGRESSION-NEWFIELD-BLINDSPOT-1]]対応の実装検証中

#### 内容
フェーズC（コミット`0148301c1`、2026-07-25 20:34 JST）で`ttm_calculator.py`の
`flow`辞書キーをPascalCase（`"Revenue"`/`"OCF"`/`"NetIncome"`等）から
snake_case（`"revenue"`/`"operating_cash_flow"`/`"net_income"`等）へ移行した際、
`ttm_series.json`の全消費者への横展開確認が行われず、以下2箇所が旧キー参照の
まま取り残されていた:

- `common/sec_data/audit.py`（L69-71）: `flow.get("NetIncome"/"OCF"/"Revenue")`
  参照。診断ツールのみへの影響（実害なし、誤検知のみ）。
- `src/value/tanuki_valuation/data_fetcher.py`: `build_rice_annual_shape()`・
  `_quarters_complete()`・`get_fcf_series()`が`"OCF"/"CapEx"/"Revenue"/
  "NetIncome"/"RD"/"SM"/"SBC"`という旧キーを参照。**本番影響あり。**

データ自体は2026-07-26 21:50 JST（Phase C後最初の自動データ再生成
コミット`340b8b8ae`）にPascalCase→snake_case化され、この時点から
上記2箇所が「キーが存在しない＝quarters_used=0扱い」として全件フィルタ
アウトする状態が実際に発火した。

#### 影響
2026-07-26 21:50 JST 〜 2026-07-29（発見・修正まで、約3日間）:
- 監視100銘柄**全100銘柄**で`audit.py`のNI/OCF/Revenueチェックが
  誤って「全件None」の重大エラーを報告（診断機能の機能不全、実害なし）
- **監視100銘柄中100銘柄でRICEスコアが完全停止**（`rice_data_source=
  "ttm_series"`のまま誤って確定するが`build_rice_annual_shape()`が
  内部で空リストを返し`rice.available=False, note="SEC年次データ未取得"`
  という誤った表示。`report.txt`のMatrix①・RICE=N/A表示として可視化）
- **監視100銘柄中94銘柄でFCFソース選択が本来のTTM系列（`ttm_series`）
  ではなく年次実績（`annual_fallback`）へ誤って後退**（`get_fcf_series()`
  の同一キー不一致が原因。`_select_fcf_source()`の設計意図「TTM系列を
  常に優先する」が機能不全に陥っていた）
- DCF/Intrinsic Value自体は`_select_fcf_source()`のフォールバック設計に
  救われ実害を免れていた（FCFソースが年次実績に後退するだけで計算自体は
  継続。LYFT等の既知の恒久マイナスFCF銘柄によるFAIL判定は本件と無関係の
  既存事象と確認済み）

#### 対応方針
変換層（マッピングテーブル）を新設せず、消費側をLayer3のsnake_case
キーに合わせて書き換える方針を採用（PascalCase/snake_case二重管理を
避けるため）。

【2026-07-29対応完了】
- `audit.py`: L69-71を`"net_income"/"operating_cash_flow"/"revenue"`に修正
- `data_fetcher.py`: `build_rice_annual_shape()`・`_quarters_complete()`・
  `get_fcf_series()`の全呼び出し箇所をsnake_case化。加えて
  `build_rice_annual_shape()`が空リストを返す場合に`rice_data_source=
  "annual_fallback"`へ再フォールバックする分岐を追加（`get_series()`が
  非空というだけで`rice_data_source="ttm_series"`を確定させていた設計上の
  非対称性を解消。`get_fcf_series()`側は元々フィルタ後の結果で判定する
  対称的な設計だったため実害を免れていた）
- `tests/test_pipeline_logic.py`のフィクスチャ（`_make_ttm_entry()`等）も
  snake_caseに追従

**検証結果**: pytest 442 passed（既知2件`[[TEST-STALE-IV-1]]`のみ）、
`audit.py`（NI/OCF/Revenue正常値復帰、WARN14件のみ・重大エラー解消）、
`report_consistency_check.py`（NG=0/WARN=71、既存WARNと同一）。全100銘柄
`pipeline.py --skip-risk`再生成の結果:
- RICE: 100銘柄中62銘柄が`rice.available=True`へ復帰（残る38銘柄は
  「OCF/純利益データなし」「セクター除外」等、正当な既存の対象外理由で
  RICE不算出。バグに起因する誤表示は0件に解消）
- FCFソース: 94銘柄が`annual_fallback`→`ttm_series`へ復帰
- うち40銘柄でIntrinsic_Value_Per_Shareが1セント超変化（MSCI+113.4%・
  LITE-89.5%・ENTG+90.9%等）。3銘柄について一次データ（SEC EDGAR
  company_facts.json、MSCIはQ1 2026 10-Q原本まで直接確認）で検証した結果、
  TTM系列のOCF/CapEx自体は正確（単一タグ一貫使用・合算値も原本と完全一致）
  であり、変化は既存の`core_calculator.py`側FCF_Base選択・外れ値調整
  ロジック（本件の修正対象外、変更なし）が正しいデータソースを初めて
  受け取った結果と判断（詳細は該当調査のチャット記録参照）
- LRCXの`intrinsic_value_per_share=$62.76`等、FCF_Baseの選択結果が
  たまたま同一だった銘柄ではIV完全一致を確認（デグレなし）

---

### ✅ [LAYER3-SGA-Q4-MISSING-1] selling_general_and_administrativeがQ4逆算・欠落四半期逆算どちらのスコープにも含まれておらずQ4が恒常的に欠落する
**優先度:** 中〜高
**分類:** バグ
**完了日:** 2026-07-29
**コミット:** a7b840c32fde3b6619707f7a7c588baeaed12fd1
**発見:** SM/SGA分離258件全数検証

#### 内容
selling_general_and_administrativeが、q4_implied.py::
Q4_IMPLIED_FIELDS・layer3_builder.py::MISSING_QUARTER_IMPLIED_FIELDS
のどちらのスコープにも含まれていない。年次・Q1・Q2・Q3は正しく
取得できるが、Q4（多くの企業の12月決算年度末）が恒常的に欠落する。
ABBVで実データ確認: 2024-12-31年次14,752,000,000・Q1〜Q3は正常
だが、Q4単体・Q4逆算エントリともに0件。

#### 影響
42銘柄・171四半期に影響（ABBV/AMD/AVGO/BBAI/BROS/CAT/CIX/COHR/
DELL/ELF/ENTG/FCX/FICO/GEV/HEI/HON/HWM/JNJ/JOBY/KLAC/KO/KULR/LITE/
LLY/LOAR/LRCX/NVDA/PAYS/PEP/RDW/RKLB/RMBS/SCCO/SITM/TASK/TDY/TSLA/
VRT/VST/VZ/WMT/WST/XOM）。selling_general_and_administrative自体が
既存TTM回帰比較の対象外（旧パイプラインに存在しない新規フィールド
のため）のため、これまでの不一致件数には一切反映されておらず可視化
されていなかった。

#### 対応方針
Q4_IMPLIED_FIELDS・MISSING_QUARTER_IMPLIED_FIELDS双方に
selling_general_and_administrativeを追加する。

【2026-07-29対応完了】
- `q4_implied.py`: `_SNAKE_TO_PASCAL`に`selling_general_and_administrative→
  "SGA"`を追加、`Q4_IMPLIED_FIELDS`（15→16フィールド）に`"SGA"`を追加
- `layer3_builder.py`: `MISSING_QUARTER_IMPLIED_FIELDS`に
  `selling_general_and_administrative`を追加
- `common/sec_data/newfield_q4_cutoff_check.py`（新規常設スクリプト）で
  修正後の全量検証を実施した結果、SGAのQ4欠落は**0件**に解消
  （旧: 42銘柄・171四半期）。cost_of_revenue側にも同種の検証を適用し
  NG 0件（FRSHのsource_tag不一致による正当なガードスキップ1件のみ）
- pytest 442 passed（既知2件のみ）、`report_consistency_check.py`
  NG=0/WARN=71（既存と同一）で確認済み

---

### ✅ [LAYER3-TTM-REGRESSION-NEWFIELD-BLINDSPOT-1] TTM回帰比較スクリプトが旧パイプライン非存在の新規フィールドを検証対象外にしている
**優先度:** 中
**分類:** テスト / 検証プロセスの欠陥
**完了日:** 2026-07-29
**コミット:** a7b840c32fde3b6619707f7a7c588baeaed12fd1
**発見:** SM/SGA分離258件全数検証

#### 内容
現行のTTM回帰比較スクリプトは、旧ttm/データが持つキーのみを起点に
新旧を突合する設計（for pascal_key, old_val in old_flow.items():）
のため、旧パイプラインに存在しなかった新規フィールド
（selling_general_and_administrative等、Layer2スキーマ追加時に
新設された6フィールド）は回帰比較の対象外になる。このため
[[LAYER3-SGA-Q4-MISSING-1]]のような新規フィールド側のバグは、
これまでの一連の回帰検証を何度実施しても一切検出されなかった。

#### 影響
新規追加6フィールド（short_term_investments・total_liabilities・
eps_basic・eps_diluted・cost_of_revenue・
selling_general_and_administrative）全てが、同様の「検証の死角」に
入っている可能性がある。selling_general_and_administrative以外の
5フィールドは未検証だった。

#### 対応方針
回帰比較スクリプトを汎用的に拡張するのではなく、6フィールドそれぞれの
性質を個別調査した上で対応要否を判断する方針とした。

【2026-07-29対応完了】6フィールド全件の投資調査を実施し、以下の通り
決着した:
- **short_term_investments・total_liabilities（STOCK系）**: 「年次−Q1−
  Q2−Q3」という新旧突合の前提自体が数学的に成立しないため対象外と判定
  （対応不要）。既存のreport_consistency_check.py（WARN-25/26）による
  None検知・遷移検知で部分的にカバーされていることを確認
- **eps_basic・eps_diluted（比率フィールド）**: 加重平均株式数の変動に
  より単純合算・差分が数学的に無意味なため対象外と判定（対応不要）。
  eps_dilutedはreader.py::get_roe_avg_detail()のROEフォールバックとして
  実消費されている一方、eps_basicは消費者ゼロと判明（[[LAYER3-VISA-
  EPS-TAG-MISSING-1]]等、副次課題を分離して記録）
- **cost_of_revenue（FLOW系）**: Q4逆算スコープには既に含まれていたが、
  GrossProfitバックフィルが本番データパスに到達しない構造的欠落
  （[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]）、および監視105
  銘柄中16銘柄でタグ自体が構造的に欠落するパターン（[[LAYER3-COGS-
  STRUCTURAL-GAP-16TICKERS-1]]）を新たに発見・分離記録
- **selling_general_and_administrative（FLOW系）**: [[LAYER3-SGA-Q4-
  MISSING-1]]として実バグを特定・修正済み
- 汎用的な「新store全キー起点」への回帰スクリプト拡張の代わりに、
  SGA・cost_of_revenueの2フィールドに限定した常設チェックツール
  `common/sec_data/newfield_q4_cutoff_check.py`を新規実装（Q4欠落チェック・
  非12月決算企業向けカットオフチェック）。汎用スクリプト化は見送り、
  短期間で実効性のある個別対応を優先した

---

### ✅ [DOCS-SECDATA-NORMALIZED-DIR-STALE-1] docs/common/sec_data/normalized/という第7の重複ディレクトリが陳腐化したまま本番参照されている
**優先度:** 高
**分類:** データ品質 / バグ
**完了日:** 2026-07-30
**コミット:** 5ee157c6bbbc9e4972718181f69d0f613dcd4e46
**発見:** common/sec_data統合投資調査（フェーズ1）⑤(A)

#### 内容
`docs/common/sec_data/normalized/`という第7の重複ディレクトリが存在し、
`src/tail/quarterly_review_generator.py`（L49）と
`src/tail/tail_dcf_bridge.py`（L47）が`COMMON_NORMALIZED_DIR`として
これを参照している（本来の正規化ストア`common/sec_data/normalized/`
ではない）。2026-05-23作成以降、同期処理が見つからず更新されて
いない（本家は週次自動更新）。ファイル数51件 vs 105件、55ティッカー
分がこちら側に存在しなかった。

【2026-07-30再調査で追加発見】本ディレクトリには第3の消費者が
存在することが判明した。`docs/value-monitor/tanuki_valuation/
stock.html`（GitHub Pages公開フロントエンド）がクライアントサイド
JavaScriptから`/On-a-journey/common/sec_data/normalized/{ticker}_
quarterly_normalized.json`を直接fetchしており、これは実際には
`docs/common/sec_data/normalized/`を指す。TANUKI TAILだけでなく
**公開サイトのキャッシュフロー表示も同期間陳腐化していた**。

#### 影響
TANUKI TAILの四半期レビュー生成（layer1財務指標）とDCFブリッジが、
約2.2〜2.3ヶ月古い・55銘柄で存在しないSECデータを参照し続けていた。
加えてGitHub Pages公開のstock.htmlも同様に陳腐化データを表示していた。

#### 対応方針
選択肢A（TANUKI TAIL側のredirect）＋選択肢B（docs/側の週次自動同期
新設）を併用する。`docs/common/sec_data/normalized/`自体は
stock.html向け公開専用コピーとして維持し削除しない。

【2026-07-30対応完了】
- `src/tail/quarterly_review_generator.py`（L49）・`tail_dcf_bridge.py`
  （L47）の`COMMON_NORMALIZED_DIR`を`docs/common/sec_data/normalized/`
  から`common/sec_data/normalized/`（本家）へredirect
- `.github/workflows/SEC_Data_Update.yml`に、本家から
  `docs/common/sec_data/normalized/`へ毎回同期する`rsync --delete`
  ステップを新設（stock.html向け公開コピーの鮮度を今後自動的に維持）
- `.gitattributes`に`docs/common/sec_data/normalized/*.json`の
  `merge=ours`設定を追加（他の自動生成docsデータと同じ規約）
- 初回手動同期を実施し、105銘柄全件を本家と完全一致（`diff -rq`で
  差分ゼロ）させた
- TANUKI TAIL 10ポジション（ADBE/APGE/APP/CELH/CRWV/NVDA/PLTR/SOFI/
  SOUN/TSLA）で`load_layer1_financials()`相当の出力を新旧比較した
  結果、ADBE・APGEは陳腐化データではファイル自体が存在せず空扱い
  だったが復帰後は実データが取得できるようになり、NVDAは参照四半期が
  2026-01-25（stale）→2026-04-26（fresh）に更新され
  operating_margin/sbc_quarterly/eps_dilutedの値が変化した
  （残り7ポジションは該当期間に新規四半期データがなく変化なし）
- 検証: pytest 442 passed（既知2件のみ）、`audit.py` exit 0、
  `report_consistency_check.py` NG=0/WARN=71（既存と同一）

---

### ✅ [SEGMENT-FETCHER-DUPLICATE-ORPHAN-1] segment_fetcher.pyが2箇所に存在し内容が乖離している
**優先度:** 低
**分類:** リファクタリング / 技術的負債
**完了日:** 2026-07-30
**コミット:** 0e60ee255561d66245a9926b23b415006f1b7fa9
**発見:** common/sec_data統合投資調査（フェーズ1）⑤(C)

#### 内容
`src/value/tanuki_valuation/segment_fetcher.py`と
`common/sec_data/segment_fetcher.py`が両方存在し内容が乖離
（両方ともannual_{fy}.jsonのsegmentsフィールドを更新する処理、
467/468行）。common/sec_data側にのみXBRLコンテキスト正規表現の
バグ修正（コンテキストブロック境界を跨ぐ誤マッチ防止）と金融業向け
追加タグ（revenuesnetofinterestexpense/netrevenues）が存在し、
src/value側には未反映。

【2026-07-30再調査で追加確認】`git log`により、両ファイルの分岐は
単一のコミット`01fa5dec5`（2026-04-25）に起因することが判明した。
同コミットが`common/sec_data`側にバグ修正を適用すると同時に、
修正前のスナップショットを`src/value`側へ新規ファイルとして複製して
いた。以降どちらも一度も変更されておらず、`src/value`側の独自要素は
XBRL値スケールに関する説明コメント1件のみ（機能的な差ではない）。

#### 影響
両ファイルとも他モジュールからimportされず、GitHub Actionsからも
呼ばれていない（手動実行専用のオーファンスクリプト）ため、現状の実害は
なし。ただしどちらが「正」か不明な状態が放置されていた。

#### 対応方針
`common/sec_data/segment_fetcher.py`が機能的に完全上位互換（コンテキスト
境界跨ぎ誤マッチ防止・金融業向けタグ2件を保持）であり、両ファイルとも
呼び出し元ゼロのため統合の影響範囲もゼロと確認済み。

**セグメントデータ手動取得スクリプト自体は、今後の銘柄新規登録が原則
Claude Code経由で行われる方針となったため、現時点では使用しない**
（将来的な再検討の余地は残す）。

【2026-07-30対応完了】
- `src/value/tanuki_valuation/segment_fetcher.py`側にのみ存在した
  XBRL値スケール（decimals=-6）に関する補足コメントを、削除前に
  `common/sec_data/segment_fetcher.py`の該当箇所へ移植
- `src/value/tanuki_valuation/segment_fetcher.py`を削除。削除前後で
  リポジトリ全体をgrepし、コードからの参照が皆無であることを最終確認
- 検証: pytest 442 passed（既知2件のみ）、`audit.py` exit 0、
  `report_consistency_check.py` NG=0/WARN=71（既存と同一）

---

### ✅ [LAYER3-COGS-ASTS-LRCX-RECOVERABLE-FOLLOWUP-1] ASTS・LRCXのcost_of_revenue欠落は回収可能なタグサイレント切替の可能性
**優先度:** 中
**分類:** データ品質 / 要個別調査
**完了日:** 2026-07-30
**コミット:** e39c40cc84
**発見:** cost_of_revenue/EPS投資調査（チャット記録）

#### 内容
[[LAYER3-COGS-STRUCTURAL-GAP-16TICKERS-1]]のGAP型8銘柄のうち、ASTS(約2.2年前に
報告停止)・LRCX(約0.7年前に報告停止)は他6銘柄(CAKE等、数年〜十数年前に停止)と比べて
停止時期が新しく、CAKEのような「タグ付け自体の廃止」ではなく、単に別の標準タグに
切り替えた(LLY-CAPEX-STALE-1型の本当のサイレント切替)である可能性が残ると仮説されて
いた。

#### 影響
この2銘柄は候補タグ拡充・ticker overrideで回収できる見込みがあると推測されていた。

#### 対応方針・完了記録

【2026-07-30調査・対応完了】ASTS・LRCXそれぞれについて一次情報（10-Q原本・
company_facts.json構造）で個別に裏取りし、両銘柄とも**回収不可能**と結論した。

**LRCX**: 最新10-Q（Q3 FY2026、accession `0000707549-26-000022`）のR2.htm
（連結損益計算書のXBRLレンダリング）を確認したところ、「Cost of goods sold」
科目は標準タグ`us-gaap:CostOfGoodsAndServicesSold`から、LRCX独自の拡張タグ
`lrcx:CostOfGoodsAndServicesSoldExcludingRestructuringCharges`へ切り替わって
いた（比較期間の金額は旧タグと完全一致、会計処理・科目自体に変化なし）。
当初はticker_override（`override_concept`に名前空間プレフィックス付きで
指定）による回収を試みたが、以下2点が判明し断念した:
1. **`lrcx:`名前空間自体がSEC EDGARの`companyfacts.json` APIに存在しない**
   （`data.sec.gov/api/xbrl/companyfacts/CIK0000707549.json`をライブ取得し
   直接確認。10-Q本文のXBRLレンダリング〈R2.htm〉には表示されるが、SEC
   companyfacts APIのレスポンスには反映されないという、企業独自拡張タグに
   関するAPI仕様上の制約と判明）。ローカルキャッシュの陳腐化ではなく、
   SEC側APIが現に返さないデータであることを確認済み
2. `override_concept`は指定フィールドの候補タグリストを丸ごと1つの指定
   タグに置き換える設計のため、解決不可能なタグで置き換えると、従来
   標準タグ（`CostOfGoodsAndServicesSold`）経由で正常に取得できていた
   21件の四半期データ（2025-06-29まで）が消失する**回帰**を引き起こす
   ことをbefore/after比較（全105銘柄regeneration）で確認した

このためLRCXへのticker_override追加は見送り、`[[LAYER3-COGS-STRUCTURAL-
GAP-16TICKERS-1]]`の「完全なギャップ」銘柄として現状維持する。

**ASTS**: 前回調査（2026-07-30）で確定した通り、標準タグ`us-gaap:
CostOfRevenue`は技術的には存続しているが、製品別売上内訳のディメンション
付き脚注文脈でのみ開示され、`company_facts.json` APIの仕様上（デフォルト
コンテキストのみ公開）取得不可能。加えて損益計算書自体がCOGS概念を持たない
区分（Engineering services costs等）に再構成済みのため、回収不可能。

**副産物（実装済み・保持）**: `layer3_builder.py::_get_concept_units()`に、
concept文字列の"名前空間:タグ名"形式（コロン区切り）対応コードを実装した。
今回のLRCXでは根本原因（API自体がデータを公開しない）により活用に至らな
かったが、コード自体は動作検証済み（全105銘柄regenerationでNVDA/KLAC/TER/
V/SOFIを含む既存動作に差分ゼロを確認、コロンを含まない場合は完全に後方
互換）であり、将来別銘柄で同種の企業固有拡張タグが`companyfacts.json`に
実際に含まれるケースが出た場合に備え、保持することとした（現状の利用箇所
はゼロ）。

**一般的な教訓**: 企業独自の拡張タグ（`{ticker}:`名前空間）は、SEC EDGARの
10-Q/10-K本文のXBRLレンダリング（R-file等）には表示されても、`companyfacts.
json` APIのレスポンスには反映されない場合がある。一次情報での裏取りは
「10-K/10-Q本文で科目・タグ参照が確認できること」だけでなく、「実際に
`companyfacts.json`（またはcompany-concept API）から当該データが取得できる
こと」まで確認しないと、回収可能性の判断を誤るリスクがある。

検証: pytest 442 passed（既知2件のみ）、`audit.py` exit 0、
`report_consistency_check.py` NG=0/WARN=71（既存と同一）。

---

### ✅ [STONKS-SILO-COGS-DEAD-FALLBACK-1] STONKS SILOのcost_of_revenue代替キー参照が実質常にNoneを返す死んだフォールバック
**優先度:** 低〜中
**分類:** バグ / デッドコード
**完了日:** 2026-07-30
**コミット:** 84385c2714a396ac08d2d508101a1e59456181e2
**発見:** cost_of_revenue/EPS投資調査（チャット記録）

#### 内容
discover/stonks-silo/src/fetcher.py(L174-175)がpl_raw.get("cost_of_revenue") or
pl_raw.get("cost_of_goods_sold") or pl_raw.get("cost_of_goods_and_services_sold")で
GrossProfit補完を行っているが、後2者のキー(cost_of_goods_sold・
cost_of_goods_and_services_sold)はparser.py生成のannual_YYYY.jsonのpl辞書に実在しない
(parser.py側は複数候補タグをcost_of_revenueという単一キーに統合するため)。実質的に
cost_of_revenue頼みの1経路のみが機能しており、後2者は常にNoneを返すデッドコード。

#### 影響
現状は実害が顕在化していない(cost_of_revenueキーが機能する限り問題ないため)が、
将来のリファクタ時に誤解を招く可能性がある。

#### 対応方針・完了記録

【2026-07-30対応完了】着手前の現状再確認で、fetcher.pyのコードが登録時から
不変であること、annual_YYYY.jsonのpl辞書に`cost_of_goods_sold`・
`cost_of_goods_and_services_sold`のいずれのキーも実在しないこと（全105銘柄・
1441ファイルを走査し0件）、および当該コード追加コミット(`d23a410b62`,
2026-05-09)のメッセージからも「parser.py側の将来のキー分離を見越した予約」
である根拠は見当たらないことを確認した。意図的な設計上の予約ではなく、単純な
誤った憶測(parser.pyの複数候補タグ→単一キー統合設計を正しく把握しないまま
3候補を並べたもの)に基づくデッドコードと結論し、以下の通り単純削除で対応した。

変更前:
```python
cost = (
    pl_raw.get("cost_of_revenue")
    or pl_raw.get("cost_of_goods_sold")
    or pl_raw.get("cost_of_goods_and_services_sold")
)
```

変更後:
```python
cost = pl_raw.get("cost_of_revenue")
```

**副次的発見・修正**: 変更前後で全stonks_silo対象25銘柄(直近5年分)の
fetcher出力を比較した結果、RXRX 2021年のみ差分（`gross_profit`: `null`→
`10178000`）を検出した。原因は、Pythonの`0`がfalsyであるため、
`cost_of_revenue`が正当な値`0`（同年のannual_2021.jsonに実在）であっても
`or`チェーンが次の候補キー(実在しない`cost_of_goods_sold`)へフォールスルーし、
結果的に`cost`全体が`None`扱いとなってgross_profit補完自体がスキップされる
という、デッドコードとは別の潜在バグ（falsy-zero値の取りこぼし）を内包して
いたことによる。今回の単純化によりこの副次バグも同時に解消され、RXRX 2021年の
gross_profit補完が正しく機能するようになった。

この副作用の影響範囲を`analyzer.py::_calc_incremental_margin()`経由で検証した
ところ、RXRX 2021年のgross_profit確定により増分粗利率ペア(2021→2022)が
新たに計算対象へ追加され、`incremental_margin_trend`のOLS回帰対象点数が
3点→4点に増えることを確認した。ただし実際に全25銘柄の`StonksAnalyzer.analyze()`
出力全体を変更前後でフィールド単位まで比較した結果、差分は**ゼロ**であった
(RXRXの`incremental_margin`・`incremental_margin_prev`は直近2ペア
(2025年・2024年分)のみを参照するため2021年データの影響を受けず、
`incremental_margin_trend`のOLS判定も追加点を含めて再計算してもDETERIORATING
のまま変化しなかったため)。現時点のデータでは表示結果への影響はないが、
将来別ティッカー・別年度でcost_of_revenue=0のケースが増えた場合はOLS対象点数の
増加により`incremental_margin_trend`の判定が変わり得る点は留意事項として記録する。

検証: pytest 442 passed（既知2件のみ）、`audit.py` exit 0、
`report_consistency_check.py` NG=0/WARN=71（既存と同一）。加えて、全25
stonks_silo銘柄の`StonksAnalyzer.analyze()`出力を変更前後でシリアライズし
diffがゼロであることを個別に確認済み。

---

### ✅ [JNJ-RD-TAG-PRIORITY-1] JNJのresearch_and_developmentが誤タグ採用により実態の約1/30に過小計上
**優先度:** 高
**分類:** データ品質 / 計算ロジックへの実害あり
**完了日:** 2026-07-30
**コミット:** b52128ec1419aedcf891dc74ed9576e214e0e890
**発見:** SECデータ全体の網羅的正確性検証

#### 内容
`common/sec_data/tag_definitions.py::TAG_CANDIDATES["RESEARCH_AND_DEVELOPMENT"]`
の候補タグ優先順位は`ResearchAndDevelopmentExpense`を1位、
`ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost`を2位としていた。
大半の企業ではどちらか一方のみ報告するため問題にならないが、JNJは2023年以降
両タグを並存報告しており、優先度1位のタグが誤って採用され続けていた。

一次情報（SEC EDGAR 10-K原本、FY2023/2024/2025の3期連続）で裏取りした結果:
- `ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost` = 損益計算書
  本体（Consolidated Statements of Earnings, R5.htm）の主要科目
  「Research and development expense」。FY2023: $15,085M / FY2024: $17,232M /
  FY2025: $14,665M。JNJの実態R&D総額。
- `ResearchAndDevelopmentExpense` = キャッシュフロー計算書（R10.htm）の非資金
  調整項目「Charge(s) for (acquired) in-process research and development
  assets」。M&A実行時に取得したIPR&D資産を即時費用化する一時的会計処理で、
  通常のR&D活動とは無関係。FY2023: $483M / FY2024: $1,841M / FY2025: $109M。

誤って後者が採用され続けた結果、annual_YYYY.jsonの`research_and_development`
は実態の約1/30〜1/150という値になっていた。

#### 影響
- `src/value/tanuki_valuation/calculator/adjustments.py::capitalize_rd()`
  （R&D資本化調整、R&D/Revenue≥5%閾値で適用）が、誤った比率0.1%
  （正しくは約15.6%）により`applied: false`のまま誤って不適用になっていた
  （現在進行形の実害、JNJのFCF・Intrinsic Valueに直接影響）。
- RICE（`rice.py`）・STONKS SILO等、`research_and_development`を参照する
  他経路にも波及する設計だが、JNJのRICEは現状別要因
  （`note: "SEC年次データ未取得"`）で`available: false`のため、本バグの影響は
  現時点では顕在化していない。
- `data_fetcher.py`経由のTTM系列（`build_rice_annual_shape()`）は
  `config/sec_concept_definitions.json`（Layer3、`layer3_builder.py`が参照）
  という**別の独立した候補タグリスト**を経由しており、本対応では修正して
  いない。同ファイルの`research_and_development`候補順序も現状
  `["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcluding
  AcquiredInProcessCost", ...]`と同一の誤った優先順位のままであり、
  Layer3/TTM経路が将来有効化された際に同型の問題が再発する可能性がある
  （残課題として記録、本対応のスコープ外）。

#### 対応方針・完了記録

【2026-07-30対応完了】`tag_definitions.py::TAG_CANDIDATES["RESEARCH_AND_
DEVELOPMENT"]`の優先順位を入れ替え、`ResearchAndDevelopmentExpenseExcluding
AcquiredInProcessCost`を1位、`ResearchAndDevelopmentExpense`を2位とした。

**後方互換性の確認**: `parser.py`（annual/quarterly、merge型候補選択）・
`quarterly.py`（raw table、primary+fallback-if-empty型候補選択）の両消費者で
優先順位を入れ替えた場合の影響を検証した。`quarterly.py`は主タグが空の場合
のみフォールバックする設計のため、両タグが並存しない大半の銘柄では
主タグが空→フォールバックで従来通り`ResearchAndDevelopmentExpense`が
採用され、動作に変化がないことをロジック上確認した上で、全105銘柄について
`SECParser.parse_company_facts()`・`quarterly.build_raw_table()`を変更前後で
実行し出力を比較した（実際の企業データを用いた実証、ロジック確認のみに
留めない）。

**変更が生じた3銘柄**:
- **JNJ**（意図した修正）: annual_2023/2024/2025の`research_and_development`
  が$483M/$1,841M/$109M → $15,085M/$17,232M/$14,665Mに修正された。
  `capitalize_rd()`の適用判定も`applied: false`（R&D/Rev=0.1%）→
  `applied: true`（R&D/Rev=15.6%、FCF調整-$975M）に変化することを確認した。
- **LLY**（副次的改善）: `quarterly.py`のraw table「RD」フィールドが、旧タグ
  （`ResearchAndDevelopmentExpense`、2023-06-30で報告終了）に主タグが
  張り付いたまま2023Q3以降のデータを一切拾えず停止していた潜在バグを
  同時に解消した。修正後は2023Q3〜2026Q1まで正しく（新タグ`Excluding
  AcquiredInProcessCost`経由で）継続取得できるようになった。
- **AMD**（軽微な副作用、許容範囲と判断）: annual_2011.jsonの
  `research_and_development`が$1,453M→$79Mに変化した。AMDは2012年提出の
  FY2011 10-Kで`ExcludingAcquiredInProcessCost`タグを3件のみ（FY2010・
  FY2011・2012Q1）例外的に報告しており、その値はJNJとは逆にごく小さい
  （$79M/$114M、実態のR&D総額とは無関係な別区分と推測される）。しかし
  これは2011年という14年以上前の単年データのみへの影響であり、
  `research_and_development`を参照するRICE・R&D資本化調整のいずれも直近
  数年のデータしか使用しないため、実質的な実害はないと判断した。

全105銘柄について、変更が生じたAMD/JNJ/LLY以外の102銘柄は
`annual_*.json`・`quarterly_*.json`・raw table・normalizedのいずれにも
差分がないことを確認済み（変更前後比較、`research_and_development`以外の
フィールドを含め完全一致）。

検証: pytest 442 passed（既知2件のみ）、`audit.py` exit 0、
`report_consistency_check.py` NG=0/WARN=71（既存と同一）。JNJ/AMD/LLYの
`common/sec_data/data/`・`raw/`・`normalized/`配下の該当ファイルを実際に
再生成し、上記3銘柄以外に差分が生じないことを確認済み。
