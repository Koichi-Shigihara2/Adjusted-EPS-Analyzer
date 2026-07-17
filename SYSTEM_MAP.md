# SYSTEM MAP — On-a-journey

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
├─ quarterly.py      # 四半期データ取得・正規化
├─ normalizer.py     # フィールド正規化
├─ ttm_calculator.py # TTM系列計算。本番経路は calc_ttm_series()/save_ttm_series()
│    のみ（update.pyが呼ぶ）。FLOW_FIELDS（4Q合算）のみを処理し、STOCK_FIELDS/
│    SHARES_FIELDS（Cash/STDebt/LTDebt/DeferredRevenue/Equity/Assets/
│    SharesBasic/SharesDiluted）は処理しない。
│    **注意（GATE2-PHASE3B-1② 2026-07-17）**: STOCK_FIELDS/SHARES_FIELDSを
│    実際に処理するcalc_ttm()/save_ttm()（{ticker}_ttm.json生成）は
│    2026-05-07のcalc_ttm_series()追加以降に用途を失った到達不能コード
│    （本番からは一切呼ばれない）。GATE2-PHASE3B-1②でCurrentAssets/
│    CurrentLiabilitiesをSTOCK_FIELDSに追加したが、この到達不能性のため
│    本番の_ttm_series.jsonには反映されない（[[TTM-STOCK-FIELDS-DEAD-1]]
│    として構造的問題を分離登録・対応未定）。
│    EXCLUDED_FIELDS（_COGS・RPO）新設・FIELD_CONCEPTS全キーの分類網羅性を
│    モジュールロード時に検証する契約チェック（contracts.py::
│    validate_field_classification()）も同時に追加済み。
├─ parser.py         # XBRL解析
├─ tag_definitions.py  # XBRLタグ候補の共通定義（TAG_CANDIDATES。quarterly.py・parser.py
│    双方が参照。9概念のみ統合済み、LTDebt/SM/DA/RPO/Revenueは意図的に未統合。
│    LLY-CAPEX-STALE-1 Phase 2a 2026-07-12新設）
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
└─ revenue_tag_conflict_check.py  # revenue系タグ競合検知（ARCH-DATA-1残課題③
     2026-07-15新設）。company_facts.jsonを再読込し、MERGE_ALL_TAGS_FIELDS対象
     （revenue/selling_and_marketing/depreciation_and_amortization）の候補タグ間で
     同一年度の値が閾値以上乖離していないかWARN検知する。parser.py本体は無変更、
     SECParserの既存メソッドを再利用（新規の候補タグ一覧は作らない）。
     update.py Step1完了直後（check_revenue_quality()の直後、4c.相当）に配線。
     自動修正は行わない（人間がTICKER_RESTRICTIONS登録可否を判断する既存フロー
     に委ねる）。詳細はBACKLOG.md [[REVENUE-TAG-CONFLICT-SCAN-1]]参照

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
├─ data_fetcher.py::TTMReader  # common/sec_data/ttm/{TICKER}_ttm_series.jsonを
│    読み込み、_select_fcf_source()経由でSEC 10-Kベースのfcf_5yr_avg/fcf_listと
│    比較のうえ採用可否を決定する（TTM-QUARTERS-CHECK-1 2026-07-12完了:
│    OCF・CapEx双方のquarters_used>=4フィルタを追加し不完全TTM値を除外。
│    TTM点数が年次実績より少ない場合は年次を優先する_select_fcf_source()
│    ヘルパーも新設。詳細はBACKLOG_DONE.md参照）
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
| parser.py | 影響銘柄のupdate.py → audit.py |
| tag_definitions.py（TAG_CANDIDATES） | quarterly.py/parser.py双方に波及するため、変更前後で全銘柄のbuild_raw_table/_extract_values出力を比較し影響銘柄を特定（同日生成のcompany_facts.jsonで新旧比較すること。raw/*.jsonの生成日時差だけで見かけ上の差分が出るため単純な過去ファイル比較は不可）→ 影響銘柄のみupdate.py → audit.py |
| contracts.py（FinancialEntry必須キー変更等） | quarterly.py::save_raw_table()・normalizer.py::save_normalized()の検証が全銘柄で走るため、変更後は全105銘柄のupdate.pyを実行しContractViolationが新規発生しないか確認 → report_consistency_check.py |
| data_fetcher.py（TTMReader・_select_fcf_source） | 全銘柄fcf_list_raw/fcf_5yr_avgに影響するため全銘柄pipeline.py再実行 → report_consistency_check.py |
| extract_key_facts.py | EPS quarterly.json 再生成 → report_consistency_check.py（CHECK-17/19確認）|
| core_calculator.py / calculator/dcf.py | 影響銘柄のpipeline.py再実行 |
| calculator/adjustments.py | 影響銘柄のpipeline.py再実行（FCF外れ値・estimate_fcf等）。`check_software_system_reclassification()`（FCF-CONVRATE-DESIGN-LIMIT-1、2026-07-14追加）はconfig書き換えを行わない純関数で、`determine_fcf_base()`と同じ「pipeline.py実行のたびに実績データから再判定」パターンを踏襲している。今後この種の自己補正ロジックを追加する際も同パターンを踏襲すること |
| src/value/tanuki_valuation/fcf_conversion_config.json（`estimate_fcf_from_eps()`が参照。ticker_overrides / sector_conversion_rates） | 影響銘柄のpipeline.py再実行（EPS推定FCFのconversion_rate変更時）。sector_conversion_ratesのキーはDamodaran業種カテゴリの省略形（下記beta_config.json/SECTOR_TO_DAMODARANと同一タクソノミー）だが、114分類中10分類（`Software_System_Mature`/`_SaaS`分割後）しかカバーしておらず、該当なしの銘柄は一律default(0.70)になる点に注意（[[FCF-CONVRATE-DESIGN-LIMIT-1]]参照。SECTOR-FCF-RATE-BROKEN-1で2026-07-14完了、Software_Systemグループ分割も2026-07-14完了）。`Software_System`（未分割・0.80）はIOT/QBTS/RBRK/S/SOUN等の判定保留銘柄向けに残置している |
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
