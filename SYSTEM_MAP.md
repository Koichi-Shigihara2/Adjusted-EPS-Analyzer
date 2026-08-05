# SYSTEM MAP — On-a-journey

最終更新: 2026-08-02（2026-07-30の4コミット分の陳腐化を追加是正。
data_fetcher.py::TTMReader項に[[TTM-PASCALCASE-KEY-STALE-1]]
（audit.py::audit_ticker()・build_rice_annual_shape()のPascalCase→
snake_case取り残しでRICEスコア3日間全停止・94銘柄FCFソース誤後退、
コミットa7b840c32）を追記。layer3_builder.py項にLAYER3-SGA-Q4-MISSING-1
（selling_general_and_administrativeのQ4恒常欠落42銘柄171四半期を解消、
同コミット）を追記。同項に[[DOCS-SECDATA-NORMALIZED-DIR-STALE-1]]
（`docs/common/sec_data/normalized/`が2.2〜2.3ヶ月55銘柄分陳腐化、
quarterly_review_generator.py/tail_dcf_bridge.pyのredirect＋
SEC_Data_Update.ymlへのrsync同期ステップ新設で解消、コミット5ee157c6b）を
追記。新規`segment_fetcher.py`項を追加し[[SEGMENT-FETCHER-DUPLICATE-
ORPHAN-1]]（src/value/tanuki_valuation側の重複ファイル削除・
common/sec_data側へ一本化、コミット0e60ee255）を記載。STONKS SILO節に
STONKS-SILO-COGS-DEAD-FALLBACK-1（discover/stonks-silo/src/fetcher.py::
_normalize_record()のcost_of_revenue代替キー参照デッドコード削除・
falsy-zeroバグ副次修正、コミット84385c271）を追記。newfield_q4_cutoff_
check.pyの新設日表記を2026-08-01→2026-07-30〈同コミットa7b840c32〉に訂正）

最終更新: 2026-08-02（2026-08-01〜02セッションの陳腐化是正。parser.py項に
[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]（`_backfill_total_
liabilities_via_identity()`）・[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]
案b（`_align_cost_of_revenue_to_revenue_period()`）・[[LAYER3-GROSSPROFIT-
BACKFILL-PROD-UNREACHED-1]]①（`_backfill_gross_profit_from_revenue_
cogs()`）・[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1・段階2
（`_resolve_bs_entity_mixing()`、新設`spac_shell_detection_log.json`）を
追記。utils.py項に`detect_fiscal_anchor_clusters()`（ELF-FISCAL-END-
MONTH-MISDETECTION-1案②）を追記。fetcher.py項に[[FETCHER-10KT-10QT-
FORM-EXCLUSION-1]]案③（report_consistency_check.pyのCHECK-28/WARN-28）を
追記。新規スクリプト`newfield_q4_cutoff_check.py`を独立ツールとして追記。
いずれも2026-08-01実装済みだが本ファイル未反映だった陳腐化箇所）

最終更新: 2026-07-30（common/sec_data統合フェーズA〜D準備セッション。
【SECデータ取得層】ツリーに`layer3_builder.py`（Layer3、
`config/sec_concept_definitions.json`ベースの統一snake_caseインメモリ
ストア、`build_ticker_store()`）を新規追記し、`ttm_calculator.py`の
入力元がフェーズC対応で旧`normalize()`戻り値からLayer3ストアに切替済み
であることを反映。現状「新旧2スキーマ併存」ではなく実態は
Layer3（snake_case・インメモリ）・`data/annual_*.json`等（parser.py、
snake_case・ファイル）・`normalized/`（normalizer.py、PascalCase・
quality_checker.py/STONKS SILO financial_trend_calculator.pyが直接消費）
の**3スキーマ併存**であることを明記（詳細は`docs/architecture/
new_data_platform/SEC_EDGAR_LAYER_DESIGN.md`「3スキーマ併存の実態」・
移行手順は同ディレクトリ`MIGRATION_CHECKLIST.md`参照）。
`tag_definitions.py`の項に、`config/sec_concept_definitions.json`
（Layer3側の独立した候補タグリスト）との乖離リスク（[[JNJ-RD-TAG-
PRIORITY-1]]・[[LAYER3-CONFIG-RD-TAG-PRIORITY-1]]で発見）を追記。
フェーズD（本体consumer切替）は対象優先順位確定済みで着手可能な段階
〈詳細はCLAUDE_CODE_START.md・PROJECT_STATUS.md参照〉）

最終更新: 2026-07-23（新一次データベース構築プロジェクトの存在を追記。
現状の一次データ取得（`common/sec_data/`のSEC EDGAR・yfinance11ファイル/
FRED2サブシステムの分散状態）を、TO-BE設計に基づく統合層へ再構築する
プロジェクトが2026-07-22〜23の設計フェーズを経て起票された（**実装は
まだ未着手**）。進捗は`PROJECT_STATUS.md`（リポジトリルート）で管理する。
仕様書一式は`docs/architecture/new_data_platform/`配下:
`INPUT_DATA_TOBE.md`（新DB設計仕様書）・`INPUT_DATA_AS_IS.md`（移行対象
棚卸し）・`FIELD_DEFINITIONS.md`（導出データ499項目要件定義書）・
`TO_BE_FINAL_LIST.md`（導出データ最終仕様）・`NAMING_CONVENTIONS.md`
（命名規約）・`CONCEPT_PARAMETER_VARIATIONS.md`（要注意パラメータ
バリエーション一覧）。経緯記録は同ディレクトリ`archive/`配下
（`RETROSPECTIVE_2026-07-22.md`・`OUTPUT_ITEMS_INVENTORY.md`・
`TO_BE.md`・`DERIVED_DATA_SUBCATEGORIES.md`）。本プロジェクトに関わる
実装・仕様書更新を依頼する際は、完了報告に`PROJECT_STATUS.md`の該当
ステータス更新有無を含めること（`CHAT_RULES.md`参照）。）

最終更新: 2026-07-12（TTM-QUARTERS-CHECK-1完了に伴いdata_fetcher.py::TTMReader
の説明を更新（_select_fcf_source()導入・quarters_used>=4フィルタ反映）、
report_consistency_check.pyのWARN確認済み台帳（config/warn_acknowledged.json・
QUALITY-GATES-EPIC-1 Phase 1）を追記、変更時の影響範囲チェックリストに
data_fetcher.py行を追加）

最終更新: 2026-07-10（銘柄振り分けの正本（cik_lookup.csv）セクション新設、
システム一覧テーブルの出力先パス誤記5件を修正、STONKS SILOの解像度向上、
AutoTrade運用実体・OpenD前提を追記、report.txt統合レポートの存在・構成・
パース注意点を追記、common/screening/配下2スクリプト新設反映）

---

## システム一覧と責任範囲

| システム | 主な責任 | 出力先 |
|---|---|---|
| TANUKI VALUATION | DCF理論株価・RICE投資効率 | docs/value-monitor/tanuki_valuation/ |
| HypeCore | 期待プレミアム・フェーズ判定 | docs/value-monitor/hypecore/ |
| TANUKI SCORE | 多銘柄比較・最終投資判断 | docs/value-monitor/tanuki_score/（daily pick機能の出力は docs/integrated-dashboard/、下記参照） |
| STONKS SILO | 赤字企業の投資適合性評価（詳細は下記セクション参照） | docs/value-monitor/stonks-silo/ |
| EPS ANALYZER | GAAP/Non-GAAP乖離・割安発掘 | docs/value-monitor/adjusted_eps_analyzer/ |
| MACRO PULSE | マクロ環境・景気後退リスク | docs/market-monitor/macro-pulse/ |
| Market Pulse | 市場センチメント・資金フロー | docs/market-monitor/market-pulse/ |
| Extreme Fear | 買付支援・TANUKI TOP10・投入額シミュレーター（Market Pulse配下） | docs/value-monitor/extreme-fear/ |
| DISCOVER | 未発掘銘柄の発掘・ニュース収集 | docs/discover/ |
| PORTFOLIO | 保有ポートフォリオ管理 | docs/portfolio/ |
| AutoTrade | F&G×TQQQ自動売買 | C:\Users\shigi\AutoTrade\fg_level2\（リポジトリ外、運用中の実体。下記「AutoTrade/OpenD運用前提」参照） |

（2026-07-10全件棚卸しで、上記5システムの出力先パス記載がリポジトリ実態と
乖離していたことが判明したため修正: STONKS SILO/EPS ANALYZER/MACRO PULSE/
Market Pulse/PORTFOLIO。特にPORTFOLIOの旧記載`docs/management/portfolio/`は
該当ディレクトリ自体が存在しなかった）

---

## 銘柄振り分けの正本（cik_lookup.csv）（2026-07-10追記）

`config/cik_lookup.csv`（106銘柄）が、どの銘柄をどのシステムで評価するかを
決める**入力側の正本**。カラム構成:

| カラム | 役割 |
|---|---|
| ticker / cik / name | 銘柄コード・CIK・会社名 |
| eps_sector | EPS ANALYZERのセクター分類上書き（`sector_classifier_v2.py`が参照。多くの銘柄で空欄） |
| stonks_silo / tanuki / eps / hypecore | 各システムの対象可否フラグ（後述） |
| status | active / candidate / retired。新規登録手順Step 0.5で記録（詳細はCLAUDE_CODE_START.md参照） |
| registered_date / registration_source / registration_note | 登録日・登録経緯（moomoo_screening/manual_thesis等）・登録理由の要約 |

**銘柄リスト統一アクセサ（`common/sec_data/tickers.py`、2026-07-12 ZS-TICKERS-LEAK-1で新設・
FLAG-CONSUMER-AUDIT-2/3で全面適用完了）:**
`get_active_tickers(flag)`（フラグ='true'かつstatus≠'retired'の銘柄を返す。'candidate'は
含める）を核に、`get_tanuki_tickers()`/`get_stonks_silo_tickers()`/`get_eps_tickers()`/
`get_hypecore_tickers()`の4便利関数を提供する。以下の全システムがこれ経由で
「フラグ='true'銘柄の一括取得」を行う——**cik_lookup.csvの独自読み込み・
`os.listdir()`直接スキャン等の独立経路は原則存在しない**：

**フラグと各システムの対象銘柄取得経路（実装確認済み・2026-07-12時点）:**
- `tanuki=true` → `src/value/tanuki_valuation/pipeline.py`（`_load_tickers_from_csv()`が
  `get_tanuki_tickers()`経由で取得）。CLI引数でticker明示指定時も`_filter_tanuki_tickers()`で
  同フラグを検証し範囲外を除外
- `stonks_silo=true` → `discover/stonks-silo/src/pipeline.py`（`stonks_tickers()`が
  `get_stonks_silo_tickers()`経由）。CLI引数明示指定時も`_filter_stonks_silo_tickers()`で検証
- `hypecore=true` → `src/value/hypecore/hypecore.py --all`（`get_hypecore_tickers()`直接）。
  `--batch`/単体指定時も`_filter_hypecore_tickers()`で検証（2026-07-12まではノーガードだった、
  FLAG-CONSUMER-AUDIT-3参照）。`src/discover/catalyst.py --ticker`も同型のガードを持つ
- `eps=true` → `src/value/adjusted_eps_analyzer/pipeline.py`の`run()`（引数なし＝通常の
  バッチ実行）が`get_eps_tickers()`を**直接使用**（旧SYSTEM_MAP記載の「使われない」は
  誤りだったため訂正）。`--ticker`明示指定時も`_filter_eps_tickers()`で検証（2026-07-12まで
  はmonitor_tickers.yaml突合＜非ブロッキング警告のみ＞しかなく、フラグ検証自体がなかった）。
  `registration_validator.py`でもEPS未対応銘柄のWARN抑制に使用
- `common/sec_data/report_consistency_check.py`のスキャン対象も`get_tanuki_tickers()`と
  report.txt存在確認の積集合（旧`os.listdir(DATA_DIR)`直接スキャンから2026-07-12に変更）
- `src/value/tanuki_valuation/score_verifier.py`の`--ticker`省略時の全銘柄スキャンも
  `get_tanuki_tickers()`に限定（2026-07-12まではディレクトリ実在のみで判定していた）
- フラグに依らない共通upstream: `common/sec_data/config.py::get_all()`がcik_lookup.csv**全106銘柄**を返し、`common/sec_data/update.py`（SEC生データ取得）はこれを既定の対象とする。個別システムのフラグはこのSECデータ取得より下流の各パイプラインで参照される

**`config/monitor_tickers.yaml`（99銘柄）との関係:**
cik_lookup.csvとは独立した別ファイルで、以下の実際の用途を持つ:
- `src/value/adjusted_eps_analyzer/pipeline.py`の`run()`は`--ticker`明示指定時のみ、
  指定銘柄がmonitor_tickers.yamlに存在するかを**非ブロッキング警告**としてチェックする
  （未登録でも処理は続行。eps=trueフラグの検証＝ブロッキングとは別軸）
- `common/sec_data/registration_validator.py`の既定スキャン範囲（`target_tickers`未指定時）
- `docs/value-monitor/adjusted_eps_analyzer/admin/`のUIから直接編集可能（EPS ANALYZER運用者向けの手動キュレーションリスト）

cik_lookup.csvとの同期は自動化されておらず、新規銘柄登録手順Step 7
（CLAUDE_CODE_START.md）で手動追加する運用。`registration_validator.py`の
P4-CIKOrphanチェックが乖離をWARN（NGではない）として検出するが、
WARNはコミットをブロックしないため見落とされやすい。

**2026-07-10棚卸しで判明した実際の差分（cik_lookup.csv 106件 − monitor_tickers.yaml 99件 = 7件）:**
- `RMBS`/`ENTG`/`TER`/`KLAC`/`LRCX`（5件・2026-07-09に「半導体関連・手動一括登録」で登録、
  いずれも`tanuki=true`/`eps=true`/`hypecore=true`）: Step 7が未実施のまま残っている
  同期漏れと判定（本来monitor_tickers.yamlに存在すべき）
- `APGE`（1件・2026-07-02登録、`eps=true`/`hypecore=true`、status=candidate）: 他のcandidate銘柄
  （WST/CON/SN）はmonitor_tickers.yamlに存在するため、status=candidateであること自体は
  除外理由にならない。こちらも同期漏れの可能性が高い
- `BX`（1件）: `stonks_silo`/`tanuki`/`eps`/`hypecore`が全てfalseのため、monitor_tickers.yaml
  非掲載は正当（[[CIK-ORPHAN-FLAGS-1]]参照）
- 対応要否（monitor_tickers.yamlへの6件追加）は本調査のスコープ外のため、
  別途BACKLOG化を検討する

---

## 統合レポート（report.txt）— 銘柄ごとのAI向け横断出力（2026-07-10追記）

各TICKERフォルダ `docs/value-monitor/tanuki_valuation/data/{TICKER}/` には、
`latest.json`/`history.json`/`score_history.json` と並んで `report.txt`
（統合レポート・AIプロンプト用プレーンテキスト）が生成されている。
TANUKI VALUATION・HypeCore・STONKS SILO・RISK EVENTS等、複数システムの
出力を1ファイルに集約した横断ビューであり、**複数銘柄のスクリーニング・
比較作業に着手する前に、個別JSONを組み合わせる前段としてまずこのファイルの
有無を確認すること**（2026-07-10のサテライト投資候補スクリーニングで
この存在に気づかず大きく遠回りした教訓）。

**主要セクション構成:**
- `[1] TANUKI SCORE`: Classification（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）・Funda_Score・Timing_Score構成要素
- `[2] MATRIX POSITION`: Matrix種別（①投資効率系〜④キャッシュ創出力系）・Quadrant・Key_Metric_Y
- `[3] TANUKI VALUATION`: Current_Price・Intrinsic_Value_BASE・BEAR/BASE/BULLシナリオ・DCF_Reliability・**Growth_Rate_Rec（乖離⚠️警告付き。この項目は[3]内にあり[4]ではない）**
- `[4] 成長率根拠`: Phase1成長率（DCF適用値）・推奨成長率/元成長率/最終推奨値・判定（PLAUSIBLE/REVIEW/AGGRESSIVE）
- `[5] RICE METRICS` / `[6] EPS ANALYZER`
- `[7] HYPECORE`: Current_Phase・Phase_History（直近6ヶ月）
- `[8] STONKS SILO`: Short_Interest・Runway_Months・Breakeven_Estimate等（TANUKI VALUATION対象銘柄でもセクション自体は常に出力され、非該当項目はN/A表示になるだけ）
- `[9] RISK EVENTS`: Grok web検索由来のリスクイベント（高/中/低の重要度付き。カタリスト等アップサイド事象は含まれない、[[REPORT-CATALYST-1]]参照）

**パース時の注意点（2026-07-10のスクリーニング作業で発生した3件のバグより）:**
- `Growth_Rate_Rec`（乖離⚠️付き）はセクション`[3]`内にあり、セクション`[4]`の
  「推奨成長率」「元成長率」「最終推奨値」とは別の場所にある。`[4]`のみを
  見て「見つからない」と誤判定しないこと
- `Intrinsic_Value_BASE`・シナリオIVはマイナス値（例: `$-1.34`）を取り得る
  （LYFT等、DCF評価がマイナスになる赤字銘柄で発生）
- シナリオ行 `"IV=$X, Deviation=Y%"` のIV捕捉を貪欲マッチにすると
  末尾のカンマまで飲み込みDeviationが取得できなくなる（非貪欲マッチが必要）
- 上記3件の教訓を反映済みの正式パーサー: `common/screening/report_txt_parser.py`

**report.txt生成対象外の銘柄（cik_lookup.csvでtanuki=false）の注意点:**
tanuki=falseに変更された後も、変更前に生成された`report.txt`/`latest.json`が
自動削除されずファイルシステム上に残存することがある（例: RKLB/ZSは
2026-07-02にtanuki=falseへ変更されたが、2026-06-26/27生成のreport.txtが
現存する）。`generated_at`/`calculation_date`が他銘柄より古い場合は
tanuki=false化前の旧データである可能性を疑い、参考値扱いとすること。

**DCF前提・ROIC妥当性の機械チェック:** `common/screening/dcf_validity_checker.py`
（成長率floor値張り付き・SECデータ異常ジャンプ・投下資本の妥当性・
HypeCore遷移確率サンプル数の4観点を機械判定。詳細はスクリプト内docstring参照）

**report_consistency_check.pyのWARN確認済み台帳（QUALITY-GATES-EPIC-1 Phase 1・
2026-07-12新設）:** `config/warn_acknowledged.json`に`(CHECK番号, ticker)`の
組み合わせを事前登録すると「確認済み」として通常表示される。未登録のWARNは
実行時に`[🆕未確認 WARN-N ...]`と強調表示される（既存の非ブロッキング動作は
維持、NG化はしない）。台帳読み込み・照合ロジックは`load_warn_ledger()`/
`annotate_warn()`（同スクリプト内）、単体テストは`tests/test_report_consistency_check.py`。

---

## STONKS SILO（詳細・2026-07-10追記）

赤字企業（cik_lookup.csv `stonks_silo=true`、2026-07-10時点25銘柄）を対象に、
黒字化までの投資適合性を評価する。

**パイプライン:** `discover/stonks-silo/src/pipeline.py`（analyzer.py/fetcher.py/
financial_trend_calculator.py/valuation_fetcher.pyで構成）→
`docs/value-monitor/stonks-silo/data/results.json`

**追記（STONKS-SILO-COGS-DEAD-FALLBACK-1 2026-07-30実装完了、コミット
84385c271）**: `fetcher.py::_normalize_record()`のgross_profit補完で、
`cost_of_goods_sold`・`cost_of_goods_and_services_sold`の2キーはannual_
YYYY.jsonのpl辞書に実在せず常にNoneを返すデッドコードだったため削除し
`cost_of_revenue`のみ参照に単純化（登録時コミットのメッセージ確認により、
意図的な将来予約ではなくparser.pyの複数候補タグ→単一キー統合設計を誤認
した憶測に基づくデッドコードと確認）。副次的発見として、旧`or`チェーンは
`cost_of_revenue=0`（RXRX 2021年で実在）の場合に次の候補キーへ誤って
フォールスルーしcostがNone扱いになるfalsy-zeroバグを内包していたが、
今回の単純化で同時に解消。全25 stonks_silo銘柄のStonksAnalyzer.analyze()
出力を変更前後で比較し差分ゼロを確認済み。

**主要フィールド構成（`results.json.tickers.{TICKER}`）:**
- `deficit_quality`: revenue_growth_pct・cagr_3yr・rnd_ratio・sm_ratio・gross_margin・
  verdict（BUY/WATCH等）・score・sbc_adjusted_fcf・sbc_ratio・dilution_risk
- `runway`: cash・monthly_burn・**runway_months**・verdict（SAFE等）・score
- `profitability_path`: core_profit/ocf_annualの年次推移・ocf_yoy_change・ocf_acceleration
- `overall_score` / `overall_verdict` / `summary` / `records` / `valuation` / `financial_vectors`

**TANUKI VALUATIONとの依存関係（重要・従来SYSTEM_MAPに未記載）:**
`src/value/tanuki_valuation/pipeline.py`は`docs/value-monitor/stonks-silo/data/results.json`を
**直接読み取り**、以下2箇所で使用する:
1. Matrix③（成長性系）のX軸「Runway(years)」表示（`stonks_data.get("runway", {}).get("runway_months")`）
2. Runway 12ヶ月未満のペナルティ判定（資金枯渇リスクをDCF評価に反映）

STONKS SILO非対象銘柄（stonks_silo=false）でRunway相当の情報が必要な場合は、
pipeline.py内で`computed_runway_months`（Cash / 月次FCF Burn）を独自にフォールバック計算する。
→ 変更時の影響範囲チェックリストに関わる: `discover/stonks-silo/src/pipeline.py`の
runway計算ロジックを変更する場合、TANUKI VALUATION側のMatrix③・Runwayペナルティへの
影響も確認すること。

---

## TANUKI SCORE daily pick（docs/integrated-dashboard/）（2026-07-10追記）

`src/value/tanuki_score/daily_pick.py`の出力先は`docs/value-monitor/tanuki_score/`配下ではなく
リポジトリ直下の`docs/integrated-dashboard/`（`daily_pick.json`・`history.json`）。
`docs/value-monitor/tanuki_score/index.html`がfetchして表示する（CHAT_RULES.mdの
「銘柄スクリーニング着手前の確認事項」で言及される「Extreme Fear TOP10」の実体データ）。

---

## ワークフロー依存関係定義（config/workflow_dependencies.json）（2026-07-10追記）

GitHub Actions各ワークフロー（SEC_Data_Update → HypeCore_Update / Adjusted_EPS_Update等）の
依存関係グラフを定義するJSON。`docs/value-monitor/admin.html`の「実行」タブが読み取り、
一括更新ボタンの実行順序制御に使用する。ワークフローを新設・依存関係変更した場合は
このファイルへの追記が必要（admin.html側の実行UIに反映されないと手動個別実行が必要になる）。

---

## AutoTrade/OpenD運用前提（2026-07-10追記）

**運用中の実体はリポジトリ外:** `C:\Users\shigi\AutoTrade\fg_level2\`が実際に稼働している
F&G Level2×TQQQ自動売買システム（Windowsタスクスケジューラから`trader.py --entry`/
`--monitor`を日次実行、moomoo OpenD経由で発注）。signal.json/state.json/trade_log.jsonlが
日次で更新される。

**リポジトリ内に陳腐化した初期複製が残存（要注意）:** `src/subport/fg_level2/`は
2026-05-03の開発初期に作成された同名モジュール一式（trader.py/signal.py/config.json等）だが、
2026-05-03以降git上で更新がなく、`register_tasks.ps1`が`$RepoRoot`をこのリポジトリパスに
設定しているにも関わらず実際には使われていない（運用中のsignal.json更新は
`C:\Users\shigi\AutoTrade\fg_level2\`側でのみ発生）。両者は既に内容が乖離しており、
このモジュールを参照・変更する際は誤って更新対象外の複製を編集しないよう注意すること。
削除要否は本調査のスコープ外のため対応保留（別途判断が必要）。

**OpenD常時起動という運用前提:** AutoTrade運用のため、moomoo OpenD（ローカルゲートウェイ）は
既に常時起動している（2026-07-10 DESIGN-16調査時に確認）。この前提により、Moomoo API Skillや
Moomoo Skills Hub等、OpenD経由のローカル連携機能が「導入すれば追加のローカル常駐プロセスなしで
利用可能」という状態にある。ただしPC自体の停止・再起動時はOpenD接続も途切れるため、
GitHub Actions（クラウド・端末状態非依存）と同等の可用性は持たない。

---

## 共通フロントエンド部品（docs/common/）

| ファイル | 役割 | 適用範囲 |
|---|---|---|
| site-nav.js | `.nav-links`/`[data-site-nav]`をナビゲーションリンク行に置換。`body[data-tool]`でアクティブリンクをハイライト | 全ページ |
| site-header.js | `header a.logo`をロゴ画像・タイトルドット・タイトル・サブタイトルの統一DOMに置換。`body[data-tool]`からタイトル/サブタイトル/アクセント色を自動解決（EPIC-HEADER-1 2026-06-21新設） | TANUKI VALUATION・TANUKI SCORE・EPS ANALYZER・HOME・Extreme Fear（EXTREME-FEAR-1 2026-07-01追加） |
| site-theme.css | 配色トークン（`--tool-*`）・タイポ・ナビ/ヘッダー共通CSSを`!important`で上書き | 全ページ |
| glossary.json + info-tooltip.js | `<span data-info="key">`を自動検出しホバー/タップで用語説明をポップアップ表示（EPIC-LEGEND-1） | 該当箇所のみ |

---

## データフロー（上流→下流）
【SECデータ取得層】
SEC EDGAR
└─ common/sec_data/update.py
├─ fetcher.py  # SECFetcher::fetch_company_facts()/fetch_submissions()。SEC EDGAR
│    Company Facts/Submissions APIへの生取得（update.py Step1が最初に呼ぶ）。
│    **追記（CIK-DISCONTINUITY-OLDEST-YEAR-GAP-1 2026-07-20新設）**: 企業再編で
│    CIKが不連続になった銘柄（買収・スピンオフ・LBO等でSECが新CIKを発番し、
│    旧CIK側のcompany_facts.json取得が新CIK単独では最古年度が欠落する）向けに、
│    `common/sec_data/cik_history.json`（`{TICKER: {legacy_ciks: [...],
│    transition_note: "..."}}`）を`_load_cik_history()`で読み込み、
│    `_fetch_legacy_company_facts()`/`_fetch_legacy_submissions()`で旧CIKの
│    データも取得した上で`_merge_us_gaap_facts()`（静的メソッド）が
│    us-gaapタグ単位でマージする。`fetch_company_facts()`/`fetch_submissions()`
│    は保存前に本マージを実行。現在登録銘柄: MRVL/GOOGL/AVGO/DELL
│    （DELLはFY2013-2016非公開期間のフィリングギャップの注記あり）。
│    `registration_validator.py::check_p6_cik_discontinuity_candidate()`
│    （P6-CIKDiscontinuity、`CIK_DISCONTINUITY_CONFIRMED_STRUCTURAL`＝
│    {CEG,LITE,ABBV,GEV,SN,CON,VST}・境界年2010以降・売上5億ドル以上を
│    ヒューリスティックとする）が新規登録時にCIK不連続候補をWARN検知する。
│    **追記（FETCHER-10KT-10QT-FORM-EXCLUSION-1案③ 2026-08-01実装完了、
│    コミット1fd44fc0a）**: fetcher.py本体は無変更（案①のrelevant_forms
│    追加+バケツ再設計はコスト過大と判明し見送り確定）。代わりに
│    `report_consistency_check.py`にCHECK-28/WARN-28を新設し、
│    company_facts.json上のform=10-KT/10-QTのaccnが`accn_to_reportdate`に
│    未登録の場合を検知する（検知のみ、自動修正なし）。全105銘柄実行で
│    RCATにWARN-28が2件発火（10-KT accn`0001641172-25-001892`・10-QT accn
│    `0001554795-19-000269`〈2019年、RCAT第1回目の決算期変更に伴う移行期
│    四半期報告書〉）、他104銘柄で誤検知なし。単体テストは
│    `tests/test_report_consistency_check.py`。詳細はBACKLOG_DONE.md
│    [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]参照。
├─ quarterly.py      # 四半期データ取得・正規化
├─ normalizer.py     # フィールド正規化
├─ layer3_builder.py # Layer3（common/sec_data統合、config/sec_concept_definitions.json
│    〈全32フィールドの候補タグ・分類定義〉に基づきcompany_facts.json生データから
│    直接、統一snake_caseの銘柄別ストア（インメモリのみ、ファイル永続化なし）を
│    構築する`build_ticker_store()`が本体。update.py Step5で呼ばれ、戻り値は
│    そのままttm_calculator.py::calc_ttm_series()へ渡される（フェーズC対応、
│    2026-07-24〜。旧経路はnormalize()の戻り値を渡していた）。
│    Q4逆算（q4_implied.py::Q4_IMPLIED_FIELDS）・欠落四半期逆算
│    （MISSING_QUARTER_IMPLIED_FIELDS）・GrossProfitバックフィル
│    （`_backfill_gross_profit()`、インメモリのみで本番の`data/annual_*.json`
│    には反映されない＝[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]）・
│    ticker_overrides機構（`action: "exclude"`/`"override_concept"`、
│    `cross_filing_tags`によるNVDA向け複数タグ合算）を持つ。
│    `_get_concept_units()`は2026-07-30、[[LAYER3-COGS-ASTS-LRCX-
│    RECOVERABLE-FOLLOWUP-1]]対応で「名前空間:タグ名」形式（コロン区切り）の
│    企業固有拡張タグ参照に対応（現状利用箇所はゼロ、将来の再利用向けに保持）。
│    **追記（[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]① 2026-08-01
│    実装完了）**: 上記「インメモリのみで本番に反映されない」ギャップは、
│    parser.py側に独立の`_backfill_gross_profit_from_revenue_cogs()`を
│    新設し本番`data/annual_YYYY.json`への反映経路を追加したことで解消（34
│    銘柄342件是正）。本ファイルの`_backfill_gross_profit()`自体は無変更の
│    ままインメモリ専用として残置。詳細はparser.pyの項・BACKLOG_DONE.md参照。
│    **追記（LAYER3-SGA-Q4-MISSING-1 2026-07-30実装完了、コミットa7b840c32）**:
│    `selling_general_and_administrative`をQ4_IMPLIED_FIELDS・
│    MISSING_QUARTER_IMPLIED_FIELDS双方に追加し、42銘柄・171四半期のQ4
│    恒常欠落を解消。同コミットでLAYER3-TTM-REGRESSION-NEWFIELD-BLINDSPOT-1
│    （Layer2新規6フィールドの投資調査）も完了し、他4フィールド
│    （short_term_investments/total_liabilities/eps_basic/eps_diluted）は
│    性質上Q4逆算・カットオフチェックの対象外と判定した（SGA/cost_of_revenue
│    向けの常設チェックは`newfield_q4_cutoff_check.py`、詳細は同ファイルの
│    項参照）。
│    **重要（3スキーマ併存の実態、詳細は`docs/architecture/new_data_platform/
│    SEC_EDGAR_LAYER_DESIGN.md`参照）**: 2026-07-30時点で
│    ①Layer3（本ファイル、snake_case・インメモリ）②`data/annual_*.json`等
│    （parser.py、snake_case・ファイル永続化）③`normalized/`
│    （normalizer.py、**PascalCase**・`quality_checker.py`/STONKS SILO
│    `financial_trend_calculator.py`が直接消費）の3スキーマが並行して
│    存在する。`config/sec_concept_definitions.json`は`common/sec_data/
│    tag_definitions.py::TAG_CANDIDATES`と一部フィールド（例:
│    research_and_development、[[JNJ-RD-TAG-PRIORITY-1]]で発見）で
│    独立した候補タグリストを保持しており、片方のみ修正すると優先順位が
│    3スキーマ間で乖離する（[[LAYER3-CONFIG-RD-TAG-PRIORITY-1]]参照）。
│    フェーズD（本体consumer切替、対象優先順位: ①TANUKI VALUATION本体
│    ②STONKS SILO ③TANUKI TAIL ④HypeCore ⑤stock.html）着手前提条件は
│    `SEC_EDGAR_LAYER_DESIGN.md`「フェーズD」節・`MIGRATION_CHECKLIST.md`参照。
│    **追記（DOCS-SECDATA-NORMALIZED-DIR-STALE-1 2026-07-30実装完了、
│    コミット5ee157c6b）**: GitHub Pages公開フロントエンド（stock.html）向け
│    公開コピー`docs/common/sec_data/normalized/`が2026-05-23以降同期
│    されず、本家`common/sec_data/normalized/`（③、上記）から約2.2〜2.3
│    ヶ月・55銘柄分乖離していた。選択肢A+B併用で解消: (A)
│    `src/tail/quarterly_review_generator.py`・`src/tail/tail_dcf_bridge.py`
│    のCOMMON_NORMALIZED_DIR定数を本家`common/sec_data/normalized/`へ
│    redirect（TANUKI TAIL側は公開コピーではなく本家を直接参照するよう変更）、
│    (B)`.github/workflows/SEC_Data_Update.yml`に本家→公開コピーへの
│    `rsync --delete`同期ステップを新設（`.gitattributes`に
│    `merge=ours`設定も追加）。初回手動同期で105銘柄を本家と完全一致させた。
│    TANUKI TAIL 10ポジションでの新旧比較: ADBE/APGEはファイル不在→実データ
│    復帰、NVDAは参照四半期が更新されoperating_margin等が変化（残り7銘柄は
│    変化なし）。詳細はBACKLOG_DONE.md
│    [[DOCS-SECDATA-NORMALIZED-DIR-STALE-1]]参照。
├─ ttm_calculator.py # TTM系列計算。本番経路は calc_ttm_series()/save_ttm_series()
│    のみ（update.pyが呼ぶ）。**フェーズC対応（2026-07-24〜）**: 入力元は
│    旧`normalize()`の戻り値から`layer3_builder.py::build_ticker_store()`の
│    戻り値（Layer3、インメモリ）に切替済み。フィールド抽出は
│    `layer3_builder.py::get_field_entries()`経由。FLOW_FIELDS（4Q合算）のみを処理し、STOCK_FIELDS/
│    SHARES_FIELDS（Cash/STDebt/LTDebt/DeferredRevenue/Equity/Assets/
│    SharesBasic/SharesDiluted）は処理しない。
│    **追記（TTM-STOCK-FIELDS-DEAD-1 2026-07-18・対応方針a完了）**:
│    STOCK_FIELDS/SHARES_FIELDSを実際に処理していたcalc_ttm()/save_ttm()
│    （{ticker}_ttm.json生成）は2026-05-07のcalc_ttm_series()追加以降
│    用途を失った到達不能コードだったため削除した（calc_ttm()専用の補助関数
│    `_make_q4_implied_output()`・`_latest_end()`・`_calc_burn_rate()`、
│    および呼び出し元ゼロの孤立関数`_calc_q4_implied()`も連動して削除。
│    `_build_q4_quarterly_entries()`はcalc_ttm_series()が使うため維持）。
│    STOCK_FIELDS/SHARES_FIELDS定数自体は、下記のvalidate_field_classification()
│    契約チェックを維持するため削除せず残置（EXCLUDED_FIELDSへ統合すると
│    「意図的除外」の意味が変質するため）。CurrentAssets/CurrentLiabilities
│    を含む8メンバー全て、本番のcalc_ttm_series()経由の_ttm_series.jsonには
│    引き続き反映されない（LTDebt/SharesBasic/SharesDilutedのみ別実装で
│    個別生存）。孤立データファイルcommon/sec_data/ttm/NVDA_ttm.json
│    （2026-05-11の2分間の誤呼び出しの残存物）も削除済み。
│    EXCLUDED_FIELDS（_COGS・RPO）新設・FIELD_CONCEPTS全キーの分類網羅性を
│    モジュールロード時に検証する契約チェック（contracts.py::
│    validate_field_classification()）も同時に追加済み。
├─ parser.py         # XBRL解析
│    **追記（CIK-DISCONTINUITY-OLDEST-YEAR-GAP-1 2026-07-20新設）**:
│    `common/sec_data/fact_overrides.json`（`{TICKER: {YEAR: {reason, fields:
│    {field: {value, ...}}}}}`）による年度・フィールド単位の個別上書き機構を
│    追加。本人データ優先ロジック自体は変更せず、`_apply_fact_overrides()`が
│    `save_parsed_data()`内でannual/quarterly保存直前の最終ステージとして
│    特定ticker+year+fieldのみ明示的に差し替える（GOOGL FY2012/2013の非継続
│    事業区分変更に伴う遡及修正値など、本人データ優先では当初申告値のまま
│    残ってしまうケース向け）。ファイル不在時は空dictで無効化。
│    **追記（[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]] 2026-08-05新設）**:
│    `common/sec_data/fixed_registry.json`（`{TICKER: {YEAR: {fixed_at,
│    fixed_by, verified_against, fields_snapshot, snapshot_hash}}}`）による
│    「フィックス」機構を追加。`fact_overrides.json`（値の個別上書き）とは
│    役割が異なり、`_apply_fixed_registry_freeze()`が`_apply_fact_
│    overrides()`・各種逆算バックフィルより後・`result["annual"]`組み立て
│    直後に、`fields_snapshot`記録済みフィールドを既存`annual_{year}.json`
│    の値へ強制復元する（差分適用方式、新規フィールドのみ通常抽出を通す）。
│    2026-08-05時点でStage1（26銘柄・372エントリ、`fixed_by:
│    checkgate_pass`）・Stage2（12銘柄・17エントリ）・Stage3a
│    （MO/PM/LLY 3銘柄・31エントリ）まで累計**41銘柄・420銘柄×年度
│    エントリ**登録済み（Stage2以降は`fixed_by: manual_verification`）。
│    CI側は`report_consistency_check.py`のCHECK-31/WARN-31がsnapshot_hash
│    不一致をNG検知。quarterly/TTM側（layer3_builder.py）は対象外
│    （[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]と同じ独立パイプライン構造の
│    ため）。**新規登録時は必ずannual_{year}.json実ファイルでfields_
│    snapshot対象フィールドの現存を確認すること**
│    （CLAUDE_CODE_START.md該当節・BACKLOG_DONE.md「2026-08-05（完了）」
│    Stage2/Stage3エントリ参照。BACKLOG_DONE.mdの過去記述と実データが
│    後続タスクにより乖離しうるため）。
├─ tag_definitions.py  # XBRLタグ候補の共通定義（TAG_CANDIDATES。quarterly.py・parser.py
│    双方が参照。9概念のみ統合済み、LTDebt/SM/DA/RPO/Revenueは意図的に未統合。
│    LLY-CAPEX-STALE-1 Phase 2a 2026-07-12新設）
│    **注意（[[JNJ-RD-TAG-PRIORITY-1]] 2026-07-30）**: `config/
│    sec_concept_definitions.json`（Layer3、layer3_builder.pyが参照）は
│    本ファイルとは独立した候補タグリストを保持する。両タグが並存報告
│    される銘柄（研究開発費のResearchAndDevelopmentExpense vs
│    ExcludingAcquiredInProcessCost等）で優先順位を修正する際は、本ファイル
│    だけでなくLayer3側の候補順序も同時に確認すること
│    （[[LAYER3-CONFIG-RD-TAG-PRIORITY-1]]は本ファイルのみ修正し
│    Layer3側が未修正のまま残っている既知の実例）。
├─ contracts.py  # 正規化契約の型（QUALITY-GATES-EPIC-1 Gate2 Phase 3a 2026-07-13新設）
│    FinancialEntry/EntryProvenance/FCFSeries。quarterly.py::save_raw_table()・
│    normalizer.py::save_normalized()がjson.dump()直前にFinancialEntryで
│    エントリ形状を検証（違反時ContractViolation、既存try/exceptで捕捉）。
│    **追記（GATE2-PHASE3B-1② 2026-07-17）**: validate_field_classification()
│    新設（規約C）。field_concepts辞書と分類セット（frozenset）を引数で
│    受け取る汎用設計とし、quarterly.py/ttm_calculator.pyのどちらも
│    importしない（contracts.pyは既にquarterly.pyからimportされているため、
│    逆方向の依存を追加すると循環importになる。呼び出し元のttm_calculator.py
│    側でFIELD_CONCEPTS・FLOW_FIELDS等の具体的な値を渡す設計で回避）。
│    **追記（GATE2-PHASE3B-1③-a 2026-07-17）**: GrowthVerdict(str, Enum)
│    新設（規約D）。src/value/tanuki_valuation/growth_sanity.py::
│    check_growth_sanity()のverdict（PLAUSIBLE/REVIEW/AGGRESSIVE/
│    FLOOR_HIT_REVIEW）を型で表現する。Python 3.11+のEnum仕様変更
│    （str,Enum継承でも__str__がデフォルトでクラス名付き表記
│    "GrowthVerdict.PLAUSIBLE"を返す）に対応するため__str__をoverrideし
│    self.valueを返すようにしている。enum.StrEnum（3.11+限定）は
│    pyproject.tomlのrequires-python=">=3.10"と不整合のため不採用。
│    data_fetcher.py同様、growth_sanity.py側もsys.path解決を自前で
│    行いcommon.sec_data.contractsをimportする（growth_sanity.pyは
│    src/value/tanuki_valuation/配下でパッケージ化されておらず
│    bareモジュールとしてimportされるため）。
│    **追記（GATE2-PHASE3B-1③-b 2026-07-18）**: Classification(str, Enum)
│    新設（規約D）。pipeline.py::classify()のscore（BUY/WATCH/HOLD/TRIM/
│    GROWTH_PREMIUM/SELL/PASS）を型で表現する。GrowthVerdict同様
│    __str__をoverride。json.dumps()はstr継承のisinstance高速パスにより
│    __str__override前でも素の文字列でシリアライズされることを確認済み
│    （f-string/str()のプロトコルとは別経路のため無関係）。影響が及ぶのは
│    pipeline.py内でf-string補間される箇所のみで、特にreport.txt生成の
│    f"Classification: {score}"（1221行目）はreport_consistency_check.py
│    のNG-3（LOW丸め未発動）がこの行をregexで再パースして比較するため
│    最重要（__str__override漏れがあるとNG-3が全銘柄で誤発火する）。
│    daily_pick.py（ELIGIBLE_CATEGORIES/CATEGORY_PRIORITY）・フロントエンド
│    （tanuki_score/index.htmlのCAT_META/CAT_COLOR辞書等）はJSON経由で
│    文字列を受け取るのみのため無改修で動作。
│    quarterly.py::_select_best_candidate()のフォールバック採用時・
│    ticker_restrictionsオーバーライド採用時に_provenance.source_tagを付与。
│    FCFSeriesはdata_fetcher.py::TTMReader.get_fcf_series()内でのみ使用し
│    （JSONシリアライズ不可のため.as_list()で境界越えさせる）、fcf_listの
│    新しい順規約をconstruction時に検証する。parser.py・ttm_calculator.py・
│    reader.py::get_fcf_list()は未対応（Phase 3bで判断、[[GATE2-PHASE3B-1]]・
│    [[GATE2-READER-FCFLIST-1]]参照）
│
│    **注意（2026-07-16）**: parser.py側にも別設計の独自provenance機構が
│    追加された（ARCH-DATA-1ステージ1、`{bs,pl,cf,shares,other}_provenance`）。
│    これはannual_{YEAR}.jsonの各フィールド単位でaccn/filed/is_own_data
│    （reportDate==end_date本人データ判定の結果）を記録するもので、
│    上記contracts.py（EntryProvenance.source_tag/duration_days、
│    quarterly.py/normalizer.py向け・エントリ単位）とは設計思想・
│    対象データ・粒度が異なる別の仕組みである。同じ「_provenance」という
│    語で2つの異なる機構を指すため、混同しないよう注意すること。
│    **追記（2026-07-17・ARCH-DATA-1ステージ3）**: 同provenanceに`fy_tag`
│    （採用エントリの生XBRL fyタグ値）を追加。年度バケツキー（determine_
│    fiscal_year()計算結果）と食い違う場合、`_extract_values_merged`/
│    `_extract_values_best_candidate`が`common/sec_data/data/{ticker}/
│    fy_tag_mismatch_log.json`に記録する（`is_own_data=True`限定。
│    比較年度再掲エントリ〈is_own_data=False〉のfyタグ不一致は正常仕様
│    のため対象外——全105銘柄検証で対象外にする前は4,434件・105銘柄という
│    ノイズになることが判明したための設計）。report_consistency_check.py
│    のCHECK-23/WARN-23が読み取り、既存のCHECK-22（fy_collision_log.json、
│    同一fyタグへの複数本人end_date競合）とは独立した別軸のチェックとして動作する。
│    **追記（FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1 2026-07-19）**: CHECK-22
│    （同一fyタグ前提）・CHECK-23（勝者自身のfyタグとバケツの不一致、敗者側は
│    対象外）のいずれにも該当しない第3の軸として、CHECK-24/WARN-24を新設。
│    決算期変更の境界年で、生fyタグ・end_dateの両方が異なる2エントリ（本人
│    データ側と非本人データ側）が同一年度バケツ（computed_year）で競合する
│    ケース（RCAT型、決算期を2回変更）を検知する。`_own_override_is_safe()`
│    自体は変更せず、`_extract_values_best_candidate`/`_extract_values_merged`
│    内の呼び出し前後で新設した`_is_boundary_collision()`（純関数）が判定する。
│    「生fyタグ・end_dateが異なる」だけでは不十分（ADSK/AVAV/CRM/CAKE等の
│    固定決算日企業で「同一(月,日)・隣接暦年」の組み合わせ＝fyタグが実際の
│    期間より1年ずれるWARN-23既知パターンが頻出し、実装中に7銘柄で誤発火する
│    ことが判明した）ため、`_fiscal_anchors_far_apart()`（(月,日)の循環距離が
│    30日超かを判定。`fye_change_candidate_scan.py`のMIN_CLUSTER_DISTANCE_DAYS
│    と同じ閾値）を追加の必須条件とし、決算日そのものが動いたケースのみに
│    限定した。検知結果は`common/sec_data/data/{ticker}/fye_boundary_
│    collision_log.json`に記録（fy_collision_log.json等と同一パターン、
│    0件でも毎回書き込み）。全100銘柄再生成でRCAT/LITE/WSTの3銘柄が該当
│    （事前調査時点の想定はRCATのみだったが、LITE/WSTは単発の孤立した
│    比較年度エントリで`override_applied=true`＝実害なしと確認済み。詳細は
│    BACKLOG_DONE.md [[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]参照）。
│    併せて、候補抽出用の統計的シグナル（`_cluster_fiscal_anchor_candidates()`
│    再利用、support≧2クラスタ・循環距離30日超）を`common/sec_data/
│    fye_change_candidate_scan.py`として独立ツール化した。WARN-24本体の
│    常設発火条件としては採用していない（誤検知率が高く、過去4候補中
│    RCAT以外は実害なしと判明したため）。新規銘柄登録時・定期監査時の
│    手動実行による候補洗い出し補助という位置づけに限定する。
│    **追記（FY-COLLISION-LOG-NONDETERMINISTIC-1 2026-07-20）**: CHECK-22
│    （`fy_collision_log.json`）は`_extract_values_best_candidate()`が
│    フィールドの候補XBRLタグごとに`_collect_own_data()`を独立呼び出しする
│    設計のため、複数の候補タグが同一(fy, end_dates)衝突を独立に検出すると
│    内容が完全同一のエントリが候補タグ数だけ重複する決定的なバグがあった
│    （AVAV/CAKE/COHR/CRM/FCX/FICO/HONで実在確認済み、実行のたびに増殖
│    するのではなく毎回同じ件数だけ重複）。値の採用ロジックには影響しない
│    ため、根本原因（候補タグループ）には手を入れず、
│    `_save_fy_collision_log()`側で(field, fy, end_dates, resolution)を
│    キーに重複排除するガードを追加する対症療法で対応した。詳細は
│    BACKLOG_DONE.md [[FY-COLLISION-LOG-NONDETERMINISTIC-1]]参照。
│    **追記（2026-07-18・ARCH-DATA-1残課題④）**: `_collect_own_data_annual()`は
│    start_date必須フィルタを持つためBS項目（instant fact）を常に除外していた
│    （本人データ判定の対象外）。`_collect_own_data_instant()`を新設し
│    （start_date/期間長フィルタなし版）、`INSTANT_FACT_FIELDS`（BS9項目+rpo）を
│    `_collect_own_data()`ディスパッチャで振り分け。`_own_override_is_safe()`に
│    `is_instant`引数を追加し、「同一end_date→上書き安全」ショートカットを
│    instant factでは無効化（duration factでは同一end_dateの2候補タグが
│    同一概念の別名表記である前提が成立するが、instant factのBS項目は
│    同一年度なら別概念のタグでもend_dateが機械的に一致するため。VZの
│    short_term_debtがShortTermBorrowings＝短期借入金でLongTermDebtCurrent
│    ＝長期債務流動化分を誤って上書きする回帰を実装中に検出・修正）。
│    **追記（TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1 2026-08-01実装完了、
│    コミットee46018b2）**: `_backfill_total_liabilities_via_identity()`新設。
│    `XBRL_MAPPING["total_liabilities"]`の2番目の候補タグ
│    `LiabilitiesAndStockholdersEquity`（定義上total_assetsと数学的に一致する
│    誤った代替タグ）が誤採用された年度をtotal_liabilities==total_assetsという
│    数学的シグネチャで検知し、貸借対照表恒等式（total_assets-
│    stockholders_equity）で逆算した値に置き換える。105銘柄中278件（銘柄年度、
│    AMZN/GOOGL/MSFT/NVDA等の大型株含む）を是正、全105銘柄フローズン入力比較で
│    対象外無変化を確認済み。
│    **追記（PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1案b 2026-08-01実装完了、
│    コミットb756021f6・ゲート追加9616e8058）**: `_align_cost_of_revenue_to_
│    revenue_period()`新設。revenueとcost_of_revenueが異なるaccnから独立
│    採用されている年度についてのみ、revenueと同一accn・同一期間を持つ
│    cost_of_revenue候補タグが存在すればそちらを優先採用する（欠損穴埋め型の
│    ゲート条件）。検証時の実データ確認で発見した「数学的矛盾がない場合は適用
│    しない」ガードを追加（巻き添え防止）。LRCX(2010)のみ是正、CRM(2013)・
│    JNJ(2017)・MRVL(2017)・ONDS(2017)は本案単独では未解決のまま残存
│    （案a・案cはゲート条件込みの再設計が必要、詳細はBACKLOG.md参照）。
│    **追記（LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1① 2026-08-01実装
│    完了、コミットdc0507c27）**: `_backfill_gross_profit_from_revenue_cogs()`
│    新設。標準タグからgross_profitが取得できない年度のみ、
│    revenue-cost_of_revenueで逆算した値を本番data/annual_YYYY.jsonへ
│    書き戻す（欠損の穴埋めのみ、既存の正しい値は上書きしない）。34銘柄342件を
│    是正。従来layer3_builder.py::_backfill_gross_profit()はインメモリのみで
│    本番ファイルに反映されない設計だった（同ファイル該当箇所参照）が、本対応で
│    parser.py側から独立に本番ファイルへの反映経路を新設した。
│    **追記（SPAC-SHELL-BS-ENTITY-MIXING-1段階1・段階2 2026-08-01実装完了、
│    コミット段階1 4f9588fb1・段階2 1f6e95d92）**: `_resolve_bs_entity_
│    mixing()`新設。SPAC合併等により同一年度のBS(instant fact)フィールドが
│    異なる法的実体（accn）から混在採用されているケースを是正する（実例:
│    BBAI/RDW/RKLB/SOFI/VRT/ONDS/KULR(2016)、段階2追加によりSPIR(2020)も対象）。
│    「①複数accnが混在」「②本人データaccnが単一に定まる」「③数学的矛盾が
│    確認できる、または③'アンカー候補accnのreportDateが法人名変更履歴
│    〈former_names〉のいずれかの区間内にある（段階2、SPAC合併疑いの機械的
│    検知）」「④アンカー統一で実際に矛盾が解消する」の4条件をすべて満たす
│    年度のみ、本人データaccnをアンカーとして採用し他accn由来の値をNone化する
│    （減算的設計、既存の正しい値を上書きする経路を持たない）。105銘柄・87件の
│    複数accn混在ケースへのシミュレーションで矛盾のない56件（41銘柄）・
│    KULR(2019)に無影響を確認済み。段階2で発火した年度の詳細は新設
│    common/sec_data/data/{ticker}/spac_shell_detection_log.json
│    （_save_spac_shell_detection_log()が保存、0件でも毎回書き込みの化石
│    ファイル対策パターン）に記録。詳細はBACKLOG_DONE.md
│    [[SPAC-SHELL-BS-ENTITY-MIXING-1]]参照。
├─ utils.py  # determine_fiscal_year() — 年度判定共通関数（ARCH-DATA-1-FY 2026-06-25）。
│    ARCH-DATA-1ステージ2（2026-07-17）でアンカー日ウィンドウ方式に刷新:
│    end_date.month > fiscal_end_monthの片方向月比較を廃し、
│    detect_fiscal_end_month()（会計年度末月検出。parser.py・
│    extract_key_facts.py双方が参照する統一関数）・detect_fiscal_anchor_date()
│    （決算アンカー日〈月+日〉検出。年境界〈Dec31/Jan1〉をまたぐ(月,日)分布を
│    _cluster_fiscal_anchor_candidates()で循環クラスタリングしてから中央値/
│    最頻値を採用——JNJ/TDY型の52/53週企業で完全一致最頻値だと企業自身の
│    fyタグと矛盾する誤判定が起きることが実データ検証で判明したための設計）
│    を新設し、determine_fiscal_year()はend_date.yearを中心とした
│    [year-1,year,year+1]の3候補年度とアンカー日との日数差で判定する方式に
│    変更。最小日数差60日超はWARN+月のみ比較にフォールバック（安全弁）。
│    呼び出し元8箇所（parser.py 4箇所・extract_key_facts.py 4箇所）に
│    anchor_month/anchor_day引数を追加。parser.py::_own_override_is_safe()の
│    条件2（12月決算企業で機能しない欠陥があった月のみ比較の事前フィルタ）も
│    同時に統一版determine_fiscal_year()呼び出しへ置き換えた
│    quarters_in_trailing_window()も同ファイルに追加（ARCH-DATA-1残課題① 2026-07-15新設）
│    ——会計年度end日起点のtrailing 370日窓で四半期エントリを抽出する共有関数。
│    quarterly.py::check_revenue_quality()・src/value/tanuki_valuation/pipeline.py
│    （DILUTION-FYE-1、希薄化率の分割検知）双方が参照し、暦年グルーピングの
│    重複実装（CHECK-QREV-FYE-1型バグの再発）を解消した
│    **追記（ELF-FISCAL-END-MONTH-MISDETECTION-1案② 2026-08-01新設、
│    コミット499b4d478）**: detect_fiscal_anchor_clusters(us_gaap,
│    candidate_keys, min_support=2)新設。detect_fiscal_anchor_date()と同一の
│    (月,日)クラスタリング結果のうち、主anchor（最大クラスタ）以外で合計得票が
│    min_support以上の「有意な」クラスタのアンカー日を、era別決算期変更の
│    追加候補（determine_fiscal_year()のextra_anchors引数）として返す。単一
│    クラスタしか存在しない銘柄（実測105銘柄中100銘柄）は必ず空リストを返す
│    設計（加算的操作のみ、既存の正しい判定を上書きする経路を作らない）。
│    ELFの2015-2018年度データ是正に使用。詳細はBACKLOG_DONE.md
│    [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]参照
├─ revenue_tag_conflict_check.py  # revenue系タグ競合検知（ARCH-DATA-1残課題③
│    2026-07-15新設）。company_facts.jsonを再読込し、MERGE_ALL_TAGS_FIELDS対象
│    （revenue/selling_and_marketing/depreciation_and_amortization）の候補タグ間で
│    同一年度の値が閾値以上乖離していないかWARN検知する。parser.py本体は無変更、
│    SECParserの既存メソッドを再利用（新規の候補タグ一覧は作らない）。
│    update.py Step1完了直後（check_revenue_quality()の直後、4c.相当）に配線。
│    自動修正は行わない（人間がTICKER_RESTRICTIONS登録可否を判断する既存フロー
│    に委ねる）。詳細はBACKLOG.md [[REVENUE-TAG-CONFLICT-SCAN-1]]参照
├─ fact_selection.py  # fact競合解決の共通プリミティブ（EPS-ANALYZER-NORMALIZE-
│    SCOPE-1 2026-07-20新設）。`select_latest_filed(candidates)`——同一期間
│    （同一end_date等）に複数XBRL factが競合する場合に「filed日が最新のものを
│    優先する」という単一規則のみを担う末端プリミティブ。quarterly.py
│    （`_process_entries`/`_select_best_filing`）とsrc/value/adjusted_eps_analyzer/
│    extract_key_facts.py（SPLIT-AUTO-CHECK-1）がそれぞれ独立実装していた
│    同一ロジックをここに集約。parser.py本体（本人データ優先・fy一致等の
│    多段規則）は対象外
├─ newfield_q4_cutoff_check.py  # LAYER3-TTM-REGRESSION-NEWFIELD-BLINDSPOT-1
│    対応の常設チェックツール（2026-07-30新設、コミットa7b840c32）。現行の
│    TTM回帰比較（旧ttm/データのキーを起点に新旧を突合する設計）は、旧
│    パイプラインに存在しなかった新規フィールドを検証対象外にしてしまう
│    構造的欠陥がある。selling_general_and_administrative・cost_of_revenue
│    の2フィールドについて、①Q4欠落チェック（年次エントリのFY窓内に
│    Q1〜Q3が揃っているのにQ4が存在しないケースを検出、LAYER3-SGA-Q4-
│    MISSING-1型の再発検知）・②カットオフチェック（非12月決算企業の単
│    四半期エントリのperiod_daysがlayer3_builder.py::_is_plausible_
│    standalone_quarter()の妥当範囲〈75〜100日〉に収まっているか確認）を
│    行う。対象2フィールドに限定する理由はq4_implied.pyのモジュール
│    docstring参照
└─ segment_fetcher.py  # セグメント別売上・KPI取得（SEC EDGARセグメント
     報告、ASC280）。コンテキスト境界跨ぎ誤マッチ防止・金融業向けタグ2件を
     保持する。**追記（SEGMENT-FETCHER-DUPLICATE-ORPHAN-1 2026-07-30実装
     完了、コミット0e60ee255）**: `src/value/tanuki_valuation/
     segment_fetcher.py`（機能的下位互換の重複ファイル）を削除し本ファイルへ
     一本化。両ファイルとも他モジュールからimportされておらず影響範囲は
     ゼロだった。削除前に旧ファイル側のみに存在したXBRL値スケール
     （decimals=-6）に関する補足コメントは本ファイルへ移植済み。セグメント
     データ手動取得スクリプト自体は、銘柄新規登録が原則Claude Code経由と
     なったため現状は使用しない（将来的な再検討の余地は残す）。詳細は
     BACKLOG_DONE.md [[SEGMENT-FETCHER-DUPLICATE-ORPHAN-1]]参照

【EPS ANALYZER 独自抽出パイプライン（common/sec_data/とは完全に独立・2026-07-12訂正）】
`src/value/adjusted_eps_analyzer/extract_key_facts.py`はSEC Company Facts APIを
都度ライブ取得する**独自の抽出パイプライン**であり、上記`common/sec_data/`配下の
quarterly.py・parser.py・tag_definitions.pyは一切importしていない（importは
`common.sec_data.utils`の`determine_fiscal_year`・`detect_fiscal_end_month`・
`detect_fiscal_anchor_date`の3関数のみ、ARCH-DATA-1ステージ2 2026-07-17時点）。
自前で持っていた会計年度末月検出ロジック（旧`determine_fiscal_year_end()`、
10-K/Aを含むstartswith判定でparser.py側とは基準が異なっていた）は削除し、
統一関数を参照するよう変更済み。ローカルraw JSONキャッシュも
持たない。Phase 2a（タグフォールバック選定ロジック統一）の対象範囲外であり、
恩恵を受けていない点に注意（旧SYSTEM_MAP記載が`common/sec_data/`ツリーの一部
であるかのような誤解を招く配置だったため2026-07-12訂正）。
- `extract_quarterly_facts()`: 株数4段フォールバック（quarterly.json生成。
  ①EarningsPerShareDilutedからのEPS逆算 ②Basic株数代用 ③隣接する実四半期
  からの引き継ぎ〈`_neighbor_quarter_diluted_shares()`、ASTS-SHARES-
  OSCILLATION-1 2026-07-13新設〉④yfinance現在株数代入〈全期間タグ欠落
  銘柄・Visa等限定〉。③新設前は②で埋まらない四半期に無条件で④が適用され、
  スクリプト実行時点の現在株数が過去の四半期に逆行伝播していた
  〈ASTS/AVAV/RCAT/CART/CEG/BROS/GEV/XOM/CONの9銘柄で実害確認〉）
- 同一期間に複数fact（原初filed値と後年10-Kの比較年度再掲値）が競合する場合、
  「filed日が最新のものを優先」に統一済み（SPLIT-AUTO-CHECK-1 2026-07-12完了。
  以前はQ1〜Q3が末尾勝ち・Q4が先頭勝ちで不整合、NVDA等の分割前後で分割前株数が
  残存する実害があった。SEC自体にfactが1件も存在しない期間＜分割直後〜翌年
  10-K再掲まで＞は原理的に是正不能な残存ギャップあり、詳細はSPLIT-REALTIME-GAP-1
  参照）
  **追記（SPLIT-REALTIME-GAP-1 2026-07-20完了）**: 上記の「再掲機会が一度も
  ない先頭ブロックが恒久固着する」ギャップに対し、`pipeline.py:140-205`の
  `load_split_history()`/`apply_split_adjustments()`（`config/split_history.yaml`
  への個別登録＋post-split四半期平均の1.5倍を閾値とした遡及補正、NOWで
  既に実績あり）を流用して対応。NVDA単独の想定から、全101銘柄の横断スキャン
  でAVGO/CPRT/WMT/LRCX/CELHの5銘柄にも同型ギャップを確認し登録を拡大。
  KLAC（2026-06-12分割済みだがpost-split四半期データ未到達）は事前登録のみ
  （`post_split_shares`空リストで安全にno-op）。RCATは分割自体が存在せず
  （2019年以降無分割、SEC XBRL確認済み）、往復変動の正体は
  `_neighbor_quarter_diluted_shares()`（[[ASTS-SHARES-OSCILLATION-1]]）が
  RCAT自身の四半期単位XBRL開示欠落を埋めていただけと判明したため対象外。
  KULR/SPIRのリバース分割（1-for-8）は同型ギャップの有無が未検証のまま
  [[SPLIT-REALTIME-GAP-REVERSE-1]]として分離登録。詳細はBACKLOG_DONE.md
  [[SPLIT-REALTIME-GAP-1]]参照
     ↓ TTMデータ（JSON）
【バリュエーション計算層】
├─ common/sec_data/reader.py::SECReader.get_net_cash()  # BS項目（Cash/ST_Invest/
│    LTDebt/STDebt）の同一時点原則統合＋Insurance/Fintechセクターガード適用。
│    data_fetcher.pyから呼ばれ、calculator/adjustments.py::calculate_bs_adjustment()
│    経由でvaluation["bs_adjustment"]として保存される（ARCH-DATA-1残課題①
│    2026-07-15でnet_debt_periodフィールドを追加、pipeline.py側の重複実装を解消）
│    **追記（GATE2-PHASE3B-1① 2026-07-17）**: モジュールレベル汎用アクセサ
│    get_quarterly_series(normalized, field_name)（is_annual・is_ytd両方を
│    除外した四半期エントリをend日昇順で返す）・get_latest_quarterly(normalized,
│    field_name)（その最新1件、空ならNone）を新設。戻り値は素の辞書のまま
│    （dataclass化は見送り）。get_rpo_context()内の既存_q_sorted()
│    （is_annualのみ除外・is_ytdは除外していなかった）をget_quarterly_series()
│    に置き換え（is_ytd除外を追加する意図的な挙動修正、現行データでは無害と
│    実データ検証済み）。従来は`financial_trend_calculator.py`（STONKS SILO）・
│    `quarterly_review_generator.py`/`tail_dcf_bridge.py`（TAIL）・
│    `hypecore.py`（HypeCore）が同種ロジック（`_latest_q()`・`_lq()`等）を
│    それぞれ独立再実装していたが、本アクセサ経由に統一した（呼び出し箇所計
│    15箇所は関数シグネチャ不変のため無改修。financial_trend_calculator.py
│    固有のQ4逆算ロジック`_build_q4_implied()`・hypecore.py固有のpandas変換
│    ロジックはそれぞれのファイル側にローカル残置し、reader.py側にはpandas
│    依存を持ち込まない設計を維持）。詳細は[[GATE2-PHASE3B-1]]参照
│    **追記（FY52WEEK-BS-NULL-SILENT-1 Phase A 2026-07-18）**:
│    `cash_and_equivalents`が全105銘柄実測でNone率0-4%（ほぼ確実にデータ
│    異常のシグナル）と判明したため、`or 0`による暗黙のゼロ化を廃止。
│    annual・四半期のいずれからも取得できなかった場合`available=False`・
│    新規`cash_missing`フラグをTrueにし、`calculate_bs_adjustment()`側の
│    既存フォールバック（`available=False`→`net_cash_per_share=0.0`）で
│    BS補正自体を安全にスキップする設計とした。`short_term_investments`/
│    `long_term_debt`/`short_term_debt`は「真のゼロ」との判別困難のため
│    対象外（Phase B/C、従来通り`or 0`を維持）。`pipeline.py::
│    _calc_g_fundamental()`（成長率g候補）・`_calc_roic_wacc_ratio()`
│    （RICEのVC_Factor）でも同フィールドに同種の除外パターンを追加。
│    `report_consistency_check.py`にCHECK-25/WARN-25を新設し、最新
│    annual_YYYY.jsonの対象6フィールド（total_assets/total_liabilities/
│    stockholders_equity/current_assets/current_liabilities/
│    cash_and_equivalents）のNoneを独立検知する。詳細はBACKLOG.md
│    [[FY52WEEK-BS-NULL-SILENT-1]]参照
│    **追記（NVDA-STI-TAG-UNIDENTIFIED-1 2026-07-19）**: `common/sec_data/
│    quarterly.py::TICKER_RESTRICTIONS`のticker別オーバーライドに、
│    `sti_concept`/`ltdebt_concept`/`revenue_concept`（単一タグへの差替え、
│    同一filing内・fy/fpタグベースの標準抽出の延長）と並ぶ新エントリ種別
│    `cross_filing_tags`を追加（KLAC/TER/V/SOFIは前者、NVDAは後者。
│    [[ANOMALY-PATTERN-CATALOG-1]]型C「資産クラス変化・当年度未タグ化型」
│    向け）。`sti_concept`等が「1フィールド=1タグの差替え」なのに対し、
│    `cross_filing_tags`は「指定end_date・指定form制限で複数XBRLタグを
│    直接検索し合算する」ため、`parser.py::_find_entry_by_end_date()`/
│    `_apply_cross_filing_tags()`という別関数群で実装されている。既存の
│    `_collect_own_data_annual/_instant`が持つ`form in (10-K, 10-K/A)`
│    フィルタ・accn_reportdate自己一致チェック（他銘柄の「比較年度再掲」
│    誤混入を防ぐ主要な防波堤）はグローバルには一切変更せず、
│    `cross_filing_tags`に明示登録されたticker×period×fieldの組み合わせ
│    にのみ迂回を適用する設計（`_parse_raw_data()`の標準抽出ループ後に
│    後付け上書きする形で配線、既存抽出ロジック自体は無改修）。合算値が
│    近似値の場合（NVDAのannual FY2026: +0.88%残差）は`bs_provenance
│    [field].is_approximated`/`residual_pct`に記録し、reader.py::
│    get_net_cash()→adjustments.py::BSAdjustmentResult→pipeline.py::
│    financial_health（`sti_approximated`/`sti_residual_pct`）を経由して
│    report.txtのST_Invest行に残差率を注記する。ただしBUG-NETDEBT-4
│    「同一時点原則」により、最新四半期にCash/LTDebtが揃っている場合は
│    四半期側の値が優先されるため、annual側の近似値フラグが実際に
│    report.txtへ表示されるのは四半期データが annual より古い/欠落して
│    いる期間に限られる（NVDA自身は現在2027Q1四半期側の正規合算値が
│    優先され、近似値表示は発生していない）。詳細はBACKLOG_DONE.md
│    [[NVDA-STI-TAG-UNIDENTIFIED-1]]参照
│    **追記（BS-FIELD-NONE-TRANSITION-DETECT-1 2026-07-19）**:
│    `report_consistency_check.py`にCHECK-26/WARN-26を新設。WARN-25が
│    「None率が高すぎる（35〜65%）」ことを理由に対象外とした
│    `short_term_investments`/`long_term_debt`/`short_term_debt`/`rpo`の
│    4フィールドについて、「Noneであること自体」ではなく「前年は値が
│    あったのに当年からNoneになる**遷移**」を検知する（正常な企業では
│    発生しないため、WARN-25のブランケット型不採用理由〈ノイズの多さ〉が
│    当てはまらない）。直近2年度分のannual_*.jsonのperiod（fyラベル）の
│    年度差が厳密に1であることを確認したうえでのみ判定し（決算期変更で
│    files[-2]が真の「1年前」を表さない可能性がある場合、RCATの
│    long_term_debt遷移年〈2024〉が[[FYE-CHANGE-BOUNDARY-COLLISION-
│    BLIND-1]]の決算期変更境界〈2024-2025年〉と一致する実例あり、判定不能
│    として発火させない）、annual_*.jsonが1年分のみの新規登録銘柄も対象外
│    とする。実装直後にFY52WEEK-BS-NULL-SILENT-1で確認済みの「生涯
│    フェードアウト」8件（APP/BKNG/CPRT/DOCN/ENTG/KULR/MSCI/SOUN）が
│    発火することが事前調査済みのため、`config/warn_acknowledged.json`へ
│    事前登録済み。詳細はBACKLOG_DONE.md
│    [[BS-FIELD-NONE-TRANSITION-DETECT-1]]参照
│    **追記（FY52WEEK-BS-FADEOUT-FALLBACK-1 2026-07-19）**: 「生涯
│    フェードアウト」（過去に明示的$0申告があるが最新年度はNone）銘柄向けに
│    `short_term_investments`/`long_term_debt`/`short_term_debt`の履歴
│    フォールバックを追加。新設`_lookup_last_confirmed_zero_year()`が
│    `get_annual_range(ticker, years=100)`を最新年度を除き降順走査し、
│    最初に見つかった非None値が**厳密に0**の場合のみその年度を返す
│    （非0ならNoneを返し即座にフォールバック不成立とする）。年数閾値・
│    M&A等イベント判別の専用機構は設けず、この「直近既知値が0か否か」
│    という条件のみで判定する設計（CSGP/KULR/RCATの3件は最後の$0の後に
│    非0の実額が再出現する複雑パターンのため、この条件で自然に除外
│    される。ハードコードされた銘柄リストは一切使用しない）。該当時は
│    `{field}_estimated_zero`/`{field}_last_confirmed_zero_year`を
│    戻り値に追加し、BUG-NETDEBT-3（正規化データからのLTDebt補完）・
│    BUG-NETDEBT-4（同一時点原則の四半期上書き）のいずれかで実データが
│    見つかった場合はフラグを解除する（四半期上書き時は該当サブ
│    フィールド自体に実データがある場合のみ解除、四半期側も同フィールドを
│    欠く場合はannualベースの推定ゼロ注記を維持）。adjustments.py::
│    BSAdjustmentResult・pipeline.py::financial_health経由でreport.txtに
│    「推定ゼロ（最終確認: FY20XX）」注記として表示、および従来combined
│    のみだった`total_debt`に加え`long_term_debt`/`short_term_debt`を
│    financial_healthへ個別公開。100銘柄実測で対象22件中19件が発火
│    （残3件はBUG-NETDEBT-3/4のより新しいデータへの正当な迂回）。
│    詳細はBACKLOG_DONE.md [[FY52WEEK-BS-FADEOUT-FALLBACK-1]]、除外3件は
│    BACKLOG.md [[BS-FIELD-FADEOUT-NONZERO-LAST-VALUE-1]]参照
├─ data_fetcher.py::TTMReader  # common/sec_data/ttm/{TICKER}_ttm_series.jsonを
│    読み込み、_select_fcf_source()経由でSEC 10-Kベースのfcf_5yr_avg/fcf_listと
│    比較のうえ採用可否を決定する（TTM-QUARTERS-CHECK-1 2026-07-12完了:
│    OCF・CapEx双方のquarters_used>=4フィルタを追加し不完全TTM値を除外。
│    TTM点数が年次実績より少ない場合は年次を優先する_select_fcf_source()
│    ヘルパーも新設。詳細はBACKLOG_DONE.md参照）
│    **追記（TTM-PASCALCASE-KEY-STALE-1 2026-07-30実装完了、コミット
│    a7b840c32）**: `get_fcf_series()`/`get_periods()`（本ファイル）・
│    `build_rice_annual_shape()`（同ファイル、RICE用annual_data形状への
│    変換）・`common/sec_data/audit.py::audit_ticker()`が、フェーズC移行
│    （2026-07-25、ttm_calculator.py snake_case化）後もttm_series.jsonの
│    flowキーを旧PascalCase（"OCF"/"CapEx"/"Revenue"/"NetIncome"等）のまま
│    参照し続けていたため、2026-07-26〜29の約3日間、監視100銘柄全件で
│    RICEスコアが完全停止し94銘柄でFCFソースが誤ってannual_fallbackへ後退
│    していた。両ファイルのキー参照をsnake_caseへ修正し、全100銘柄再生成で
│    RICE 62銘柄・FCFソース94銘柄が正常化（IVが変化した40銘柄のうち
│    MSCI/LITE/ENTGは一次データで裏取りしFCF_Base選択ロジックの妥当な挙動と
│    確認済み）。詳細はBACKLOG_DONE.md [[TTM-PASCALCASE-KEY-STALE-1]]参照。
├─ core_calculator.py    # DCF・理論株価
├─ calculator/rice.py    # RICE投資効率
├─ calculator/dcf.py     # DCFエンジン
├─ calculator/adjustments.py  # alpha計算（参考値保持）・Moat Score計算（ALPHA-REDESIGN-1 2026-06-25）・
│   calculate_bs_adjustment()（reader.py::get_net_cash()の戻り値をBSAdjustmentResultへ変換）
│   注記: ALPHA-REDESIGN-1によりDCF_v0へのalpha乗算を廃止。
│        競争優位はMoat Score（粗利率・ROIC超過幅・FCFマージン）によるPhase1期間自動計算で表現。
└─ growth_sanity.py      # 成長率サニティチェック
↑ HypeCoreフェーズを参照
     ↓ latest.json（銘柄ごと）
pipeline.py              # 全銘柄を統合・TANUKI SCORE算出
├─ _load_extra_data()内のfinancial_health（report.txt表示＋TANUKI SCORE判定用）は
│    valuation["bs_adjustment"]を再利用する形に統一（ARCH-DATA-1残課題① 2026-07-15。
│    従来はpipeline.py独自にcommon/sec_data配下の生JSONを再読込しBS同一時点原則を
│    別実装していたため、reader.py::get_net_cash()側のみが適用するセクターガードが
│    反映されずV〈Visa〉で表示乖離が生じていた。二重読み込み自体も解消）
├─ risk_fetcher.py   # Grok APIによる既知リスクイベント取得
├─ hypecore_history/{TICKER}.json生成
│   （docs/value-monitor/hypecore/data/{TICKER}_poc.json を参照 →
│    docs/value-monitor/tanuki_valuation/data/hypecore_history/ に出力）
├─ stock.html（個別銘柄ページ）
└─ tanuki_score結果 → Discord通知（ACTION-10）
【独立データ取得層（他システムへの依存なし）】
Market Pulse  ← yfinance / CNN F&G / FREDデータ
　　TAKE PROFIT / BUY チェックリスト（F&G×200日MA×HYスプレッド×ヒンデンブルグ簡易版、
　　MP-LOGIC-1/2 2026-06-24実装）を market_data.json に出力
MACRO PULSE   ← FREDデータ / FRBステートメント
　　整合性チェック: src/market/macro_pulse/05_audit.py（05_events.csvの重複行検出・
　　NFP水準残存兆候の検出、report_consistency_check.py相当の軽量版。MACRO-NFP-1 2026-07-07新設）
　　過去データ補正: src/market/macro_pulse/05_backfill_nfp_mom.py（05_events.csv内の
　　既存NFP行を水準→前月比に一括変換する一回限りのバックフィルスクリプト。
　　MACRO-NFP-HIST-1 2026-07-08新設、実行済み）
DISCOVER      ← Grok Web検索 / NewsAPI
　　ニュース収集・分類: src/discover/collect.py → docs/discover/data/daily_report.json（日次）
　　ニュース履歴: docs/discover/data/news_history_YYYY_MM.json（月別蓄積・翌日騰落率付き）
　　カタリスト発掘: src/discover/catalyst.py → docs/discover/data/catalyst.json（週次）
　　影響予測: src/discover/impact_predictor.py → docs/discover/data/impact_predictions_YYYY_MM.json
　　（news_history/catalyst.jsonとは独立パイプライン。collect.py/catalyst.py実行後にそれぞれ
　　呼び出し、news_history.html/catalyst.htmlがフロントエンドで結合表示。UI-DISCOVER-1 2026-07-05）
PORTFOLIO     ← 手動入力 / 証券会社API
TANUKI TAIL（docs/portfolio/tail/）← EDGAR RSS / Grok（KPI提案・四半期レビュー生成）
　　内部統制評価: src/tail/sec_ctrl_fetcher.py → docs/portfolio/tail/data/ctrl/{TICKER}/{QUARTER}.json + latest.json
　　（SEC-CTRL-1 2026-06-24実装、週次自動更新）
　　モーダル構成: coreとsatelliteで同等の5タブ（テーゼ/最新レビュー/KPIトレンド/DCFシナリオ/内部統制）
　　（TAIL-SAT-CORE-1 2026-06-26でcore同等化。AI視点タブはTAIL-UX-1 2026-07-05でdetail.htmlに
　　一本化・モーダルから削除）
　　分離ページ: decision_log.html（TAIL-LAYOUT-1 2026-06-24新設）
　　詳細ページ: detail.html（TAIL-PAGE-1 2026-06-27新設、モーダル廃止・全情報1ページ表示）
　　内部統制データ: data/ctrl/{TICKER}/{QUARTER}.json + latest.json + index.json
　　（TAIL-CTRL-TRANS-1 2026-06-27、期別保存・Grok日本語翻訳・履歴セレクター対応）
　　書き込み系（ポジション登録・ジャーナル記録・KPI確定）は
　　tail/index.html → GitHub Actions workflow_dispatch
　　（.github/workflows/TANUKI_TAIL_Position_Write.yml → src/tail/workflow_write.py）
　　経由でリポジトリにコミット（TAIL-SEC-1 2026-06-21、旧:ブラウザから直接GitHub API書き込み）

---

## 変更時の影響範囲チェックリスト

| 変更ファイル | 必要な追加作業 |
|---|---|
| quarterly.py / normalizer.py / ttm_calculator.py | 全銘柄TTM再生成（update.py）→ audit.py |
| parser.py | 影響銘柄のupdate.py → audit.py。`XBRL_MAPPING`の`short_term_investments`/`long_term_debt`/`short_term_debt`/`rpo`候補タグリストは[[FY52WEEK-BS-NULL-SILENT-1]] Phase B Stage1（2026-07-19）で拡充済み（各フィールドの追加タグはコード内コメント参照）。**候補タグを追加する際は`quarterly.py`の`TICKER_RESTRICTIONS`（`ltdebt_concept`等の銘柄別override、SOFI-DATA-1）と衝突しないか個別確認すること**（SOFIは流動/非流動を分けず合算タグ`DebtLongtermAndShorttermCombinedAmount`を`long_term_debt`に固定済みのため、`short_term_debt`側に同種の合算タグを追加すると二重計上になる） |
| tag_definitions.py（TAG_CANDIDATES） | quarterly.py/parser.py双方に波及するため、変更前後で全銘柄のbuild_raw_table/_extract_values出力を比較し影響銘柄を特定（同日生成のcompany_facts.jsonで新旧比較すること。raw/*.jsonの生成日時差だけで見かけ上の差分が出るため単純な過去ファイル比較は不可）→ 影響銘柄のみupdate.py → audit.py |
| contracts.py（FinancialEntry必須キー変更等） | quarterly.py::save_raw_table()・normalizer.py::save_normalized()の検証が全銘柄で走るため、変更後は全105銘柄のupdate.pyを実行しContractViolationが新規発生しないか確認 → report_consistency_check.py |
| data_fetcher.py（TTMReader・_select_fcf_source） | 全銘柄fcf_list_raw/fcf_5yr_avgに影響するため全銘柄pipeline.py再実行 → report_consistency_check.py |
| extract_key_facts.py | EPS quarterly.json 再生成 → report_consistency_check.py（CHECK-17/19確認）|
| core_calculator.py / calculator/dcf.py | 影響銘柄のpipeline.py再実行 |
| calculator/adjustments.py | 影響銘柄のpipeline.py再実行（FCF外れ値・estimate_fcf等）。`check_software_system_reclassification()`（FCF-CONVRATE-DESIGN-LIMIT-1、2026-07-14追加）はconfig書き換えを行わない純関数で、`determine_fcf_base()`と同じ「pipeline.py実行のたびに実績データから再判定」パターンを踏襲している。今後この種の自己補正ロジックを追加する際も同パターンを踏襲すること |
| src/value/tanuki_valuation/fcf_conversion_config.json（`estimate_fcf_from_eps()`が参照。ticker_overrides / sector_conversion_rates） | 影響銘柄のpipeline.py再実行（EPS推定FCFのconversion_rate変更時）。sector_conversion_ratesのキーはDamodaran業種カテゴリの省略形（下記beta_config.json/SECTOR_TO_DAMODARANと同一タクソノミー）だが、114分類中10分類（`Software_System_Mature`/`_SaaS`分割後）しかカバーしておらず、該当なしの銘柄は一律default(0.70)になる点に注意（[[FCF-CONVRATE-DESIGN-LIMIT-1]]参照。SECTOR-FCF-RATE-BROKEN-1で2026-07-14完了、Software_Systemグループ分割も2026-07-14完了）。`Software_System`（未分割・0.80）はIOT/QBTS/RBRK/S/SOUN等の判定保留銘柄向けに残置している |
| `FCF_CYCLICAL_VOLATILITY_TICKERS`（FCF-CONVRATE②、TRUST-SUMMARY-EPIC-1、2026-07-18新設。業界サイクルにより固定転換率が実態を表現できないと個別原因分析で確定した銘柄の手動リスト。閾値〈cv・divergence_ratio〉による自動判定はLLYがDOCNを両軸で上回るなど数学的に分離不可能と判明済みのため不採用） | `stock.html`（バナー表示）と`pipeline.py`（report.txtのdivergence_ratio表示）の**2箇所に同一のSetが独立定義**されており、共通configファイル経由ではない。3件目以降を追加する場合は個別原因分析（業界サイクル起因かどうかの確認）を経た上で**両ファイルに同期して追記**すること（片方のみの追記だとバナー・report.txtの表示が食い違う）。Classification判定ロジックには一切参照されない表示専用の定数（`FCF_LOW_RELIABILITY_SECTORS`と並ぶ第2の個別ティッカーベース信頼性フラグ機構。既存のFCF_LOW_RELIABILITY_SECTORSは業種ベース・stock.html単独定義で、pipeline.py側の対応はない） |
| `GROWTH_STRUCTURAL_MISMATCH_TICKERS`（GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1、TRUST-SUMMARY-EPIC-1段階1可視化、2026-07-20新設。ハイパーグロース事業と成熟業種平均〈Damodaran業種分類〉との構造的ミスマッチが原因分析で確定した14銘柄〈AMD/NVDA/ONDS/ASTS/BKNG/BROS/ELF/KULR/LLY/TER/XOM/ALAB/IONQ/RCAT〉の手動リスト。`FCF_CYCLICAL_VOLATILITY_TICKERS`と同型の設計） | `stock.html`（`#growth-sanity-container`内のsanityHTMLバナー）と`pipeline.py`（report.txtの[4. 成長率根拠]セクション、signals/warnings表示直後）の**2箇所に同一のSetが独立定義**されており、共通configファイル経由ではない。TERのみ業界平均比ではなく自社実績比での警告のため注記文言を専用に分岐させている。追加・削除時は両ファイルへの同期を忘れないこと。Classification判定ロジックには一切参照されない表示専用の定数 |
| config/beta_config.json（`overrides[ticker].sector`。`data_fetcher.py::_load_beta_config()`が正しいパスで読み込む共通ローダーで、`core_calculator.py::estimate_fcf_from_eps()`〈FCF転換率〉と`pipeline.py::_load_beta_sector()`〈growth_sanity向け〉の両方から参照される） | 影響銘柄のpipeline.py再実行。`sector`値は`growth_sanity.py::SECTOR_TO_DAMODARAN`の「beta_config.json形式」ブロック（例: `Semiconductor`/`Software_Internet`/`Aerospace_Defense`/`Software_System_Mature`/`Software_System_SaaS`）のキー形式で統一すること |
| src/value/tanuki_valuation/beta_fetcher.py（β自動取得＋`classify_software_system_subgroup()`〈FCF-CONVRATE-DESIGN-LIMIT-1、2026-07-14追加〉） | β変更時: 影響銘柄のpipeline.py再実行。`--classify-software-system`は新規銘柄登録時（sector="Software_System"の未分類銘柄）に前受収益/売上高比率（company_facts.jsonから算出、閾値0.40）でMature/SaaSを暫定分類する。CLAUDE_CODE_START.mdのStep 2.5として登録手順に組み込み済み |
| growth_sanity.py::TICKER_INDUSTRY_OVERRIDES / SECTOR_TO_DAMODARAN（ticker→Damodaran業種名の直接上書き辞書・sector省略キー→正式業種名の変換表。`beta_config.json`の`sector`より優先順位が高い） | 影響銘柄のpipeline.py再実行。妥当性検証はDamodaran公式データセット`docs/value-monitor/tanuki_valuation/common/damodaran_cache/indname.xls`（企業別48,157社の実分類データ、`Exchange:Ticker`列を主要取引所限定でticker照合すると該当企業の実際のIndustry Groupが直接引ける）と突き合わせて行う |
| config/adjustment_items.json（一過性費用・調整項目のXBRLタグ定義。EPS Analyzerとcalculator/adjustments.pyのFCF外れ値判定`TRANSIENT_CATEGORIES`が共に参照） | EPS Analyzer全銘柄再実行 → 影響銘柄のtanuki pipeline.py再実行（fcf_outlier判定への波及）|
| calculator/rice.py | 影響銘柄のpipeline.py再実行 |
| config/maturity_config.json | 影響銘柄のpipeline.py再実行（alpha上限・WACC・成熟度設定変更時）|
| growth_sanity.py（Damodaran業種別成長率ベンチマーク。fundgrEB.xls〈ROC/再投資率/期待EBIT成長率〉を`docs/value-monitor/tanuki_valuation/common/damodaran_cache/`から読み込み） | HypeCoreデータ確認 → 影響銘柄のpipeline.py再実行 |
| hypecore結果（hypecore_results.json） | growth_sanity経由でDCF成長率が変わるため影響銘柄のpipeline.py再実行 |
| hypecore_results（poc.json）更新時 | 影響銘柄のpipeline.py再実行（hypecore_history/{TICKER}.jsonが更新される） |
| pipeline.py | audit.py → 全銘柄pipeline.py再実行 |
| discover/stonks-silo/src/pipeline.py（runway計算ロジック） | TANUKI VALUATION側のMatrix③・Runwayペナルティも影響を受けるため、影響銘柄のtanuki pipeline.py再実行を確認 |
| Market Pulse / MACRO PULSE 各スクリプト | 独立しているため他システムへの影響なし |

---

## SYSTEM_MAP更新タイミング

以下の変化が生じたときのみ更新する（毎作業ごとの更新は不要）：
- 新しいシステムを追加したとき
- システム間に新しいデータの依存関係が生まれたとき
- 主要ファイルの役割・配置が変わったとき

**2026-07-10の教訓:** 上記は「変化が生じたとき」の更新基準だが、今回のように
既存の構造（銘柄振り分けの正本・STONKS SILOとTANUKI VALUATIONの依存関係・
出力先パスの誤記等）が長期間未記載/誤記のまま気づかれないケースもある。
CHAT_RULES.mdの「一日の作業終了時のブラッシュアップ」にSYSTEM_MAP.md点検を
定例項目として追加した（詳細はCHAT_RULES.md参照）。
