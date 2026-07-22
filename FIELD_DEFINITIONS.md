# FIELD_DEFINITIONS.md — 出力項目の定義台帳（段階的作成）

作成日: 2026-07-22
出発点: `TO_BE_FINAL_LIST.md`（ステップ6・7確定後の499項目、データ性質分類済み）

## 本ドキュメントの位置づけ

499項目を、簡単なものから順に定義していく。本ドキュメントは複数フェーズに
分けて作成し、今回（フェーズ1）は最も単純な2分類（システム設定データ・
移送データ）を対象とする。一次データ・手動入力データ・導出データは
次フェーズ以降で扱う。

実装（コード修正）は行っていない。定義の記録のみ。

## フェーズ1着手前の訂正: AS-IS-183の分類再判定

`TO_BE_FINAL_LIST.md`のステップ7では、AS-IS-183（MACRO PULSE
`regime_source`）を「システム設定データ」16件の1つに含めていたが、
本フェーズでの定義作業中に再検証した結果、これは**誤分類**であると
判断した。

**理由**: `regime_source`は「FOMC声明分析（Grok）」または「DGS1数値
ベース」という**どちらの計算方法でregimeが判定されたか**を示す値であり、
生成日時・実行スケジュールのような「銘柄・分析内容とは無関係な運用上の
値」（システム設定データの定義）には該当しない。regimeの判定方法という
**分析内容そのものに関わるメタ情報**であるため、「導出データ」に
再分類する。

この訂正により、システム設定データは16件→**15件**、導出データは
402件→**403件**となる（合計499件は変わらない）。`TO_BE_FINAL_LIST.md`
のステップ7もあわせて更新する。

---

## 対象1: システム設定データ（15件、訂正後）

**定義**: 生成日時・実行スケジュール等、銘柄・分析内容とは無関係な運用上の値。
データ取得元は「システム内部（バッチ実行時刻）」または、監視・状態管理を
目的とした内部状態変数の場合は個別に記載する。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義 | データ取得元 | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-080 | HypeCore | 最終更新（生成日時） | `generated_at` | poc.json生成時点のJST日時 | システム内部（バッチ実行時刻） | システム設定データ |
| AS-IS-123 | STONKS SILO | 生成日時 | `generated_at` | results.json生成時点の日時 | システム内部（バッチ実行時刻） | システム設定データ |
| AS-IS-195 | MACRO PULSE | LAST UPDATE | （UI集約表示、単一フィールドなし） | 全指標中の最新`release_date`とその`data_source`列の集約表示 | システム内部（events.csv内の各指標発表実績から`updateTicker()`が算出） | システム設定データ |
| AS-IS-196 | MACRO PULSE | 最終更新表示（画面最上部） | `generated_at`（`05_meta.json`） | 流動性データ更新バッチの最終実行時刻(JST) | システム内部（`update_liquidity_csv()`末尾で書き込み） | システム設定データ |
| AS-IS-247 | Discover | 銘柄別最終更新日 | `updated_at`（`tickers{}.updated_at`） | 銘柄単位でのカタリスト処理最終実行日 | システム内部（`process_ticker()`戻り値） | システム設定データ |
| AS-IS-261 | Discover | テーマ生成日 | `generated_at`（`macro_themes[].generated_at`） | マクロテーマのGrok検索実行日 | システム内部（`explore_macro_themes()`、日曜のみ更新） | システム設定データ |
| AS-IS-265 | EPS Analyzer | 銘柄コード・最終更新日 | `ticker` / `last_updated` | quarterly.json生成時点の日時 | システム内部（`pipeline.py:process_one_ticker`） | システム設定データ |
| AS-IS-285 | TANUKI SCORE | 生成日時 | `generated_at` | daily_pick.json生成時点のJST日時 | システム内部（バッチ実行時刻） | システム設定データ |
| AS-IS-300 | Market Pulse | 生成日時 | `date` | market_data.jsonエントリのJST実行時刻 | システム内部（バッチ実行時刻） | システム設定データ |
| AS-IS-401 | TANUKI TAIL | 取得日時 | `fetched_at` | 内部統制データ（sec_ctrl_fetcher.py）の取得日時 | システム内部（バッチ実行時刻） | システム設定データ |
| AS-IS-403 | TANUKI TAIL | 直近確認accession number | `last_accn`（`rss_state.json`） | 新規提出監視の差分比較用、内部状態変数（画面非表示） | システム内部（`edgar_rss_monitor.py`自身が次回実行時に読取） | システム設定データ（監視状態管理系） |
| AS-IS-405 | TANUKI TAIL | 提出遅延連続検知日数 | `no_filing_days`（`rss_state.json`） | 提出遅延アラート発報回数カウント用、内部状態変数（画面非表示） | システム内部（`edgar_rss_monitor.py`自身が次回実行時に読取） | システム設定データ（監視状態管理系） |
| AS-IS-409 | TANUKI TAIL | レビュー生成完了時刻 | `completed_at`（`review_queue.json`） | 四半期レビュー生成の完了記録 | システム内部（`quarterly_review_generator.py`が記録） | システム設定データ |
| AS-IS-411 | TANUKI TAIL | アラート発報タイムスタンプ | `"{ticker}:{condition}"`キー（`satellite_alerts.json`） | 4条件別の直近アラート発報時刻、24時間以内重複通知抑止用 | システム内部（`satellite_monitor.py`自身が次回実行時に読取） | システム設定データ（監視状態管理系） |
| AS-IS-480 | TANUKI TAIL | レビュー生成日時 | `generated_at`（`reviews/*.json`トップレベル） | 四半期レビューJSON生成時点の日時 | システム内部（`quarterly_review_generator.py`） | システム設定データ |

### プログラム名称の不統一・統一案

現状、「このデータ（ファイル/レコード）がいつ生成・更新されたか」を表す
フィールド名が、サブシステムをまたいで最低4通りに分散している:

| 使用中の名称 | 使用サブシステム | 件数 |
|---|---|---|
| `generated_at` | HypeCore／STONKS SILO／Discover(テーマ)／TANUKI SCORE／TANUKI TAIL(reviews)／MACRO PULSE(05_meta.json内部) | 6箇所相当 |
| `date` | Market Pulse | 1箇所 |
| `updated_at` | Discover(tickers{}単位) | 1箇所 |
| `last_updated` | EPS Analyzer | 1箇所 |
| `fetched_at` | TANUKI TAIL(内部統制) | 1箇所 |

**統一案**: 意味的に2階層に分けて統一することを提案する。
1. **ファイル/レポート全体の生成時刻** → `generated_at`に統一
   （対象: Market Pulseの`date`→`generated_at`への改名を推奨。他は
   既に`generated_at`使用中のため変更不要）
2. **個別データ単位（銘柄・四半期等）の更新時刻** → `updated_at`に統一
   （対象: EPS Analyzerの`last_updated`→`updated_at`への改名を推奨。
   Discoverの`updated_at`は既に統一候補の名称と一致）
3. **取得専用の意味合いを持つ`fetched_at`**（TANUKI TAIL内部統制データ）は、
   「バッチが値を生成した時刻」ではなく「外部ソースから実際にデータを
   取得した時刻」という独自の意味を持つため、無理に統一せず存置を推奨
   （SEC提出書類の取得タイミング記録という監査目的があるため）

監視状態管理系3件（`last_accn`/`no_filing_days`/`"{ticker}:{condition}"`
タイムスタンプ）は、そもそも「表示用の生成日時」ではなく**スクリプト
自身が次回実行時に読み返す内部状態**という別の性質を持つため、命名統一の
対象から除外する（NAMING_CONVENTIONS.mdへの新規カテゴリ追加候補として
別途記録する価値がある）。

---

## 対象2: 移送データ（6件）

**定義**: 他のサブシステムの出力を、再計算せずそのまま転記・参照している
だけの値。データ取得元には転記元のAS-IS-ID・サブシステム名を記載する。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義 | データ取得元 | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-178 | STONKS SILO | TANUKIスコアバッジ | `tanuki_score` | TANUKI VALUATIONのTANUKI SCORE分類をバッジ表示 | **AS-IS-034（TANUKI VALUATION `tanuki_score`）**、`loadTanukiBadges()`がlatest.jsonを直接fetch | 移送データ |
| AS-IS-180 | STONKS SILO | 黒字転換目算（Adj.EPS線形推定） | `breakeven_estimate` | TANUKI VALUATIONが算出した黒字転換予想年をそのまま表示 | **AS-IS-051（TANUKI VALUATION `breakeven_estimate`）**、`toggleDetail()`がlatest.jsonを直接fetch | 移送データ |
| AS-IS-181 | STONKS SILO | Adj.EPS系列（黒字化ロードマップ） | `adjusted_eps` | EPS Analyzerが算出した調整後EPS四半期系列をそのまま表示 | **AS-IS-267（EPS Analyzer `quarters[].adjusted_eps`）**、`toggleDetail()`がquarterly.jsonを直接fetch | 移送データ |
| AS-IS-282 | EPS Analyzer | GAAP PER | `components.per` | TANUKI VALUATIONが算出したPERをそのまま表示 | **AS-IS-032（TANUKI VALUATION `components.per`、束ね行の一部）**、stock.htmlがlatest.jsonを直接fetch | 移送データ |
| AS-IS-388 | Market Pulse（extreme-fear経由） | Extreme Fearイベント抽出用スコア参照 | `fear_greed.score` | Market Pulse自身が算出したCNN F&Gスコアを、非独立フロントエンドextreme-fearが参照 | **AS-IS-344（Market Pulse `fear_greed.score`）**、同一サブシステム内の別画面（extreme-fear）がmarket_data.jsonを直接fetch | 移送データ |
| AS-IS-390 | Portfolio | USD/JPYレート | `usdjpy` | Market Pulseが取得したドル円レートを資産評価の換算に再利用 | **AS-IS-312（Market Pulse `indicators.ドル円.value`、束ね行の一部）**、`snapshot.py`がmarket_data.jsonを直接fetch | 移送データ |

### 転記元・転記先の名称不一致

6件中5件は転記元・転記先でプログラム名称が完全一致していた
（`tanuki_score`、`breakeven_estimate`、`adjusted_eps`、`components.per`、
`fear_greed.score`）。**1件のみ不一致を発見した**:

**AS-IS-390（Portfolio `usdjpy`）**: 転記元であるMarket Pulseの
`indicators`辞書内のキーは**日本語の`"ドル円"`**（`snapshot.py:39`
`_nested_get(last_mp, "indicators", "ドル円", "value")`）である一方、
転記先のPortfolioでは英語の`usdjpy`という別名称で保存・出力している。

**NAMING_CONVENTIONS.md規則5（パススルー時の命名一貫性）に基づく統一案**:
Market Pulse側の`indicators`辞書キーが日本語（`"米10年債"`, `"VIX指数"`,
`"ドル円"`, `"日経平均"`等）で統一されており、これはMarket Pulse自身の
表示ラベルとして機能している設計のため、無理に英語化するとMarket Pulse
側のUI表示ロジックにも影響が及ぶ。したがって**統一案としては、Market
Pulse側のキー名は現状維持し、Portfolio側が`usdjpy`という独自名称を
使う代わりに、取得元のキー名をコード内コメントで明示する
（例: `usdjpy  # source: market_data.json indicators."ドル円".value`）**
という、命名そのものの統一ではなく**出所の明示（provenance明示）**による
対応を推奨する。これは`NAMING_CONVENTIONS.md`規則4（provenance明示）にも
合致する対応である。

---

## 次フェーズへの申し送り

- 一次データ（31件）・手動入力データ（44件）・導出データ（403件、
  AS-IS-183の訂正反映後）は未着手
- 監視状態管理系（TANUKI TAILの`last_accn`等）を「システム設定データ」の
  サブカテゴリとして`NAMING_CONVENTIONS.md`に追記するかどうかは次フェーズ
  以降で検討する
- AS-IS-390の`usdjpy`のprovenance明示は、範囲外（実装）のため今回は
  記録のみ
