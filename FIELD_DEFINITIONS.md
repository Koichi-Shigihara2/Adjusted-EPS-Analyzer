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

## フェーズ2着手前の訂正: AS-IS-132・AS-IS-139の分類再判定

`TO_BE_FINAL_LIST.md`ステップ7では、AS-IS-132（STONKS SILO
`valuation.psr`）とAS-IS-139（STONKS SILO`gross_margin`）を「一次データ」
に含めていたが、本フェーズでの定義作業中に再検証した結果、いずれも
**誤分類**であると判断した。

- **AS-IS-132**: `pipeline.py:127` `market_cap ÷ latest_rev` という除算で
  算出される計算値であり、「計算を一切加えていない生の値」という一次
  データの定義に該当しない。
- **AS-IS-139**: `analyzer.py:235-236` `gross_profit÷revenue_sanitized`
  という除算で算出される計算値であり、同様に該当しない。

両者とも「導出データ」に再分類する。この結果、一次データは31件→**29件**
（本フェーズの対象）、導出データは403件→405件となる（合計499件は
変わらない）。`TO_BE_FINAL_LIST.md`のステップ7もあわせて更新した。

**参考（次フェーズへの申し送り）**: 本訂正の過程で、HypeCoreの
`psr`(AS-IS-099)・`peg_ratio`(AS-IS-098)・`forward_pe`(AS-IS-097)等、
yfinanceの単一フィールドをそのまま格納しているはずの項目が「導出データ」
バケット（403/405件、範囲外）に分類されたままになっている可能性がある
ことに気づいた。これらは本来「一次データ」に該当しうるため、次フェーズ
（導出データ403件の定義作業）着手時に優先的に再確認することを推奨する。

---

## 対象1（フェーズ2）: 一次データ（29件、訂正後）

**定義**: SEC EDGAR・yfinance・FRED等から直接取得し、計算を一切加えていない
生の値。優先順位の選択（例: trailingPE優先・forwardPEフォールバック）は
「計算」ではなく「選択」のため一次データに含める。除算・加算等の
計算式が明示されている場合は導出データとする（上記訂正を参照）。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義 | データ取得元 | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-032 | TANUKI VALUATION | PER/PEG/PS/EV_EBITDA/移動平均/予想EPS/アナリスト目標/配当利回り/配当性向/インサイダー保有等（束ね行） | `per, peg, ps, ev_ebitda, ma200, forward_eps, analyst_target_*, dividend_yield, payout_ratio, insider_*` | yfinance `.info`辞書の複数フィールドをそのまま格納（`per`のみtrailingPE優先/forwardPEフォールバックの選択あり） | yfinance: `trailingPE`/`forwardPE`/`pegRatio`/`priceToSalesTrailing12Months`/`enterpriseToEbitda`等（`data_fetcher.py:513-541`） | 一次データ |
| AS-IS-129 | STONKS SILO | 年次売上高・純利益 | `records`（yr→{revenue, net_income}） | SEC年次決算の売上高・純利益をそのまま抽出 | SEC EDGAR: `pl.revenue`/`pl.net_income`（`common/sec_data`経由、`pipeline.py:111-117`） | 一次データ |
| AS-IS-190 | MACRO PULSE | S&P500現在値 | （`tk-sp`表示、フィールド名なし） | S&P500指数終値 | FRED: `SP500`系列優先、失敗時stooqへフォールバック（`05_main.py:get_sp500()`825-830） | 一次データ。**複数取得経路あり**: Market Pulse(AS-IS-312内包)もyfinanceで独自にS&P500を取得（下記参照） |
| AS-IS-192 | MACRO PULSE | 10Y-2Y SPREAD | （`tk-yc`表示） | 米国10年債-2年債利回り格差 | FRED: `T10Y2Y`系列（`INDICATOR_CONFIG["Yield Curve 10Y-2Y"]`、`05_main.py:fetch_event_row()`） | 一次データ |
| AS-IS-194 | MACRO PULSE | HY SPREAD（ticker用） | （`tk-hy`表示） | ハイイールド債OASスプレッド | FRED: `BAMLH0A0HYM2`系列（`05_main.py:fetch_event_row()`309-317） | 一次データ。**複数取得経路あり**: MACRO PULSE内部でAS-IS-199と重複取得、Market Pulseとも重複（TO_BE.md⑮群参照） |
| AS-IS-197 | MACRO PULSE | M2マネーサプライ | （`liqGrid`カード表示） | M2マネーサプライ | FRED: `M2SL`系列（`05_main.py:update_liquidity_csv()`1952） | 一次データ |
| AS-IS-199 | MACRO PULSE | HYスプレッド（流動性カード用） | （`renderLiquidityCards()`表示） | ハイイールド債OASスプレッド | FRED: `BAMLH0A0HYM2`系列（`05_main.py:update_liquidity_csv()`1956） | 一次データ。**AS-IS-194と同一系列の重複取得**（TO_BE.md⑮群、統一候補） |
| AS-IS-200 | MACRO PULSE | FRBバランスシート | （`renderLiquidityCards()`表示） | FRB総資産 | FRED: `WALCL`系列（`05_main.py`1954） | 一次データ |
| AS-IS-205 | MACRO PULSE | ステルス流動性LAYER1（FRB政策意図） | （`stealthLayer1`表示） | Fed政策レジーム文字列の再表示 | `05_fed_context.csv`の`regime`列（AS-IS-182/183と同一値、MACRO PULSE内部の重複表示） | 一次データ |
| AS-IS-210 | MACRO PULSE | REPO残高 | （ステルスカード内metric） | オーバーナイトリバースレポ残高 | FRED: `RRPONTSYD`系列（×1000でMillions換算、`05_main.py`1962-1963） | 一次データ |
| AS-IS-211 | MACRO PULSE | 準備預金 | （ステルスカード内metric） | 銀行準備預金残高 | FRED: `WRBWFRBL`系列（`05_main.py`1966-1967） | 一次データ |
| AS-IS-212 | MACRO PULSE | TGA残高 | （ステルスカード内metric） | 財務省一般勘定残高 | FRED: `WTREGEN`系列、失敗時`FTSD`（`05_main.py`1957-1960） | 一次データ |
| AS-IS-262 | Discover | 翌営業日騰落率 | `price_change_next_day` | 銘柄の翌営業日株価騰落率 | yfinance: `history(period="2d")`（`collect.py:get_price_change`295-307） | 一次データ |
| AS-IS-266 | EPS Analyzer | 決算提出日・会計期末・会計年度・四半期 | `quarters[].filing_date/period_end/fiscal_year/quarter` | XBRL提出書類のメタデータ | SEC EDGAR: XBRLタグ由来（`extract_key_facts.py:extract_quarterly_facts`） | 一次データ |
| AS-IS-273 | EPS Analyzer | 銘柄コード・会社名・最終提出日 | `ticker/company_name/latest_filing_date` | 銘柄基本情報 | SEC EDGAR: `company_name`は`cik_lookup.csv`→SEC Submissions APIの順にフォールバック（`pipeline.py:generate_summary`） | 一次データ |
| AS-IS-298 | TANUKI SCORE | 前日選出ticker | `ticker`（history.json各エントリ） | 前日選出銘柄コード（画面非表示、内部処理用） | システム内部（`daily_pick.py`自身が前回実行結果を記録） | 一次データ |
| AS-IS-312 | Market Pulse | 米10年債/VIX指数/ドル円/日経平均/S&P500/NASDAQ/WTI原油/金/HYG/LQD終値 | （束ね行、フィールド名は指標ごとに個別） | 各種市場指標の終値 | yfinance: `history()`（`collect_and_send.py`67-73等） | 一次データ。**S&P500は複数取得経路あり**（MACRO PULSEのAS-IS-190と重複、下記参照） |
| AS-IS-320 | Market Pulse | S&P500グロース(IVW) | （value/change_percent/dateの束ね） | グロースETF終値 | yfinance: `history()` | 一次データ（`value`部分のみ。`change_percent`は`(change/prev)*100`で計算される導出値、下記注記参照） |
| AS-IS-321 | Market Pulse | S&P500バリュー(IVE) | 同上 | バリューETF終値 | yfinance: `history()` | 一次データ（同上の注記が適用） |
| AS-IS-322 | Market Pulse | Russell2000小型(RUT) | 同上 | 小型株指数終値 | yfinance: `history()` | 一次データ（同上の注記が適用） |
| AS-IS-325 | Market Pulse | VIX9D | （value/change/change_percent/dateの束ね） | VIX9D終値 | yfinance: `^VIX9D` `history()` | 一次データ（同上の注記が適用） |
| AS-IS-333 | Market Pulse | サブスコア実値（ツールチップ表示） | `sub_scores.{key}.raw` | センチメントサブスコア算出前の生値 | 各サブスコアの元となる生データ（VIX・MA乖離等）をそのまま保持 | 一次データ |
| AS-IS-352 | Market Pulse | VXN終値 | `tech_pulse.components.vxn_latest` | ナスダック版VIX終値 | yfinance/FRED: `VXNCLS`（`fetch_vxn_from_fred()`、GitHub Actions環境での`^IRX`障害を機にFRED切替） | 一次データ |
| AS-IS-362 | Market Pulse | 資産クラス別終値 | `asset_flow.{key}.value` | 資産クラス別ETF/指数の終値 | yfinance: `history()` | 一次データ |
| AS-IS-395 | TANUKI TAIL | 提出日 | `filing_date` | 10-Q提出日 | SEC EDGAR: `submissions API`（`sec_ctrl_fetcher.py`） | 一次データ |
| AS-IS-406 | TANUKI TAIL | 銘柄コード | `ticker`（review_queue.json） | レビュー対象銘柄コード | システム内部（`edgar_rss_monitor.py`が新規提出検知時に記録） | 一次データ |
| AS-IS-407 | TANUKI TAIL | 対象四半期 | `quarter`（review_queue.json） | レビュー対象四半期 | システム内部（同上） | 一次データ |
| AS-IS-478 | TANUKI TAIL | 銘柄コード | `ticker`（トップレベル、reviews/*.json） | レビューJSON対象銘柄 | システム内部（`quarterly_review_generator.py`） | 一次データ |
| AS-IS-479 | TANUKI TAIL | 対象四半期 | `quarter`（トップレベル、reviews/*.json） | レビューJSON対象四半期 | システム内部（同上） | 一次データ |

### 複数取得経路の記録（統一するかどうかの判断は別途）

| 一次データ | 経路1 | 経路2 | 経路3 |
|---|---|---|---|
| **S&P500指数終値** | MACRO PULSE(AS-IS-190): FRED `SP500`優先→stooqフォールバック | Market Pulse(AS-IS-312内包): yfinance `history()` | — |
| **HYスプレッド(BAMLH0A0HYM2)** | MACRO PULSE ticker用(AS-IS-194): `fetch_event_row()` | MACRO PULSE流動性カード用(AS-IS-199): `update_liquidity_csv()` | Market Pulse(AS-IS-371、⑮群参照): `fetch_hy_spread_from_fred()` |

（HYスプレッドは既に`TO_BE.md`⑮群で統一候補として記録済み。S&P500指数の
MACRO PULSE⇔Market Pulse間の重複取得は本フェーズで新たに記録した。）

### プログラム名称の不統一・統一案

一次データ29件の多くはJSON構造体の生値として格納されており、独立した
「プログラム名称」を持たない（表構造・束ね行の一部としてのみ存在）ものが
多い。明確な統一提案ができるのは以下の1点:

- **MACRO PULSE(AS-IS-205)の`regime`表示とAS-IS-182/183の`regime`が同一
  値の重複再表示**であることを`TO_BE_FINAL_LIST.md`ステップ2-A(⑮群)で
  既に記録済みだが、命名としては同一（`regime`列）のため追加の統一提案は
  不要。

### 束ね行に含まれる導出値サブフィールドの注記

AS-IS-320/321/322/325（Market Pulse ETF/指数の束ね行）は、`value`（終値、
一次データ）に加えて`change_percent`（`(change/prev)*100`で計算される
前日比変化率、`collect_and_send.py:665,810`）という**導出データの
サブフィールドを内包**している。AS-IS-032の`insider_*`同様、束ね行の
主要成分（終値）を代表させて一次データに分類しているが、`change_percent`
サブフィールド自体は導出データの性質を持つ点を明記する。

---

## 対象2（フェーズ2）: 手動入力データ（44件）

**定義**: 人手で入力・設定される値。データ取得元には入力される場所
（設定ファイルパス・UI画面名）を明記する。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義 | データ取得元 | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-242 | MACRO PULSE | コンセンサス予想値 | `CONSENSUS`（`05_indicator_schedule.csv`） | 経済指標発表の市場予想値 | `05_indicator_schedule.csv`（Discordリマインダー経由で運用者が手動入力、`update_schedule()`は空文字で初期化のみ） | 手動入力データ |
| AS-IS-249 | Discover | 銘柄区分・メモ | `tickers{}.category/memo` | 保有中/監視中/様子見の区分とメモ書き | `docs/discover/admin.html`（`saveDiscoverConfig()`） | 手動入力データ |
| AS-IS-263 | Discover | テーママスタ（ID/ラベル/カラー） | `theme_config`（`config/theme_config.json`） | テーマ分類の定義 | `docs/discover/admin.html`（`saveThemeConfig()`） | 手動入力データ |
| AS-IS-264 | Discover | 銘柄別テーマ割当・区分・メモ | `discover_config`（`config/discover_config.json`） | 銘柄ごとのテーマ・区分設定 | `docs/discover/admin.html`（`saveDiscoverConfig()`） | 手動入力データ |
| AS-IS-412〜416 | TANUKI TAIL | ウォッチリストアラート記録一式 | `journal.json`（timestamp/ticker/type/reason/tags） | サテライト監視アラートの記録 | `satellite_monitor.py`が自動記録（人手介在は限定的、アラート発報の自動記録） | 手動入力データ（自動記録寄り、下記備考参照） |
| AS-IS-425〜436 | TANUKI TAIL | KPI提案（名称/説明/出典/閾値/XBRLタグ等11フィールド） | `proposed_kpis[].*` | AI提案KPIの最終確定内容 | `docs/portfolio/tail/index.html`「KPI設定モーダル」（Grok提案を人間が確認・編集して確定） | 手動入力データ（**AI下書き＋人手承認のハイブリッド**、下記備考参照） |
| AS-IS-455〜458 | TANUKI TAIL | ポジション基本情報（ticker/type/status/version） | `positions/{T}_thesis.json`共通ヘッダ | 監視銘柄の基本属性 | `docs/portfolio/tail/index.html`→`workflow_write.py`（ポジション登録フォーム） | 手動入力データ |
| AS-IS-459〜463 | TANUKI TAIL | 投資テーゼ・エントリーストーリー・エグジット目安・取得単価・監視開始日（core型） | `thesis/entry_story/exit_guide/entry_price/entry_date` | 投資判断の根拠記録 | 同上（ポジション登録フォーム、core型） | 手動入力データ |
| AS-IS-464〜467 | TANUKI TAIL | 戦略名・エントリー条件・エグジット条件・保有期間（satellite型） | `strategy_name/entry_condition/exit_condition/holding_period` | 短期戦略の条件記録 | 同上（ポジション登録フォーム、satellite型） | 手動入力データ |
| AS-IS-468 | TANUKI TAIL | KPI一覧（パススルー格納） | `kpis[]`（core/satellite共通） | 提案KPIの保存先 | AS-IS-425〜436のproposed_kpis[]を`workflow_write.py`がそのまま保存 | 手動入力データ |
| AS-IS-469 | TANUKI TAIL | ポジション一覧インデックス | `positions`（positions_index.json） | 登録済みthesisファイル名配列 | `workflow_write.py`（ポジション登録時に自動追記） | 手動入力データ（登録操作の副産物） |
| AS-IS-470〜477 | TANUKI TAIL | 判断ログ一式（timestamp/ticker/type/reason/health_score_at_action/tags/price/shares） | `journal.json` entries | 売買判断・テーゼ修正等の記録 | `docs/portfolio/tail/index.html`「ジャーナル記録」フォーム | 手動入力データ |

**注記**: 44件のうち39件（AS-IS-455〜477）は`docs/portfolio/tail/`の
ポジション登録・ジャーナル記録フォームに集約される。表の簡潔性のため
連番範囲で1行にまとめた箇所があるが、実際は個別フィールドとして44件
存在する。

### バリデーション有無の状況

| 対象 | バリデーション有無 | 詳細 |
|---|---|---|
| TANUKI TAIL: ポジション登録（AS-IS-455〜467） | **あり** | `workflow_write.py:43-46` `_validate_ticker()`（正規表現チェック）、`workflow_write.py:51-78`必須フィールドチェック（type別）。index.html側もクライアント検証あり（`markError()`、`.field.invalid`スタイル、2494-2515行） |
| TANUKI TAIL: ジャーナル記録（AS-IS-470〜477） | **あり** | `workflow_write.py:101-109` ticker/date/reason必須チェック |
| TANUKI TAIL: KPI提案確定（AS-IS-425〜436） | **一部あり** | `workflow_write.py:149-152` kpisが空リストでないことのみチェック。個別フィールド（warning_threshold等の数値妥当性、xbrl_tagの形式等）の検証は確認できず |
| TANUKI TAIL: ウォッチリストアラート（AS-IS-412〜416） | 該当なし（自動記録のため） | `satellite_monitor.py`が条件成立時に自動生成、人手入力ではないため妥当性検証の対象外 |
| Discover: `theme_config`/`discover_config`（AS-IS-249, 263, 264） | **なし（将来リスク）** | `docs/discover/admin.html`の`saveThemeConfig()`/`saveDiscoverConfig()`は内容検証を一切行わず、そのままJSON化してGitHub API経由でコミットする（`valid`/`required`等の検証キーワードがadmin.html全体で0件）。テーマID重複・空ラベル・不正な色コード等が入力されてもエラーなく保存されてしまう |
| MACRO PULSE: CONSENSUS（AS-IS-242） | **なし** | `05_indicator_schedule.csv`への直接編集運用のため、値の型・妥当性チェックは存在しない |

**将来的なリスクとして記録**: Discoverのconfig系2ファイル（theme_config.json,
discover_config.json）は、バリデーションなしで直接GitHubにコミットされる
運用のため、誤入力によるJSON破損やUI表示崩れのリスクがある。修正は
本タスクの範囲外のため、リスクの記録にとどめる。

## 次フェーズへの申し送り（更新）

- 導出データ（405件、AS-IS-132/139追加反映後）は未着手
- HypeCoreの`psr`/`peg_ratio`/`forward_pe`等、一次データに該当しうる項目が
  導出データバケットに残っている可能性を確認したため、次フェーズ着手時に
  優先確認する
- 監視状態管理系（TANUKI TAILの`last_accn`等）を「システム設定データ」の
  サブカテゴリとして`NAMING_CONVENTIONS.md`に追記するかどうかは次フェーズ
  以降で検討する
- AS-IS-390の`usdjpy`のprovenance明示、Discoverのconfig系保存処理への
  バリデーション追加は、いずれも範囲外（実装）のため今回は記録のみ

---

## 対象3（フェーズ3）: 導出データ — 評価倍率・バリュエーション系（13件）

出発点: `DERIVED_DATA_SUBCATEGORIES.md`「評価倍率・バリュエーション系（13件）」
（ステップ6確定後392件ベース、AS-IS-002/003/004/005/006/031/055/056/113/116/122/132/133）

実装（コード修正）は行っていない。定義の記録のみ。

### 計算式分解の前提

各項目の計算式は、登場する変数を中間変数で止めずに再帰的に展開し、以下の
いずれかに到達するまで分解する:

1. **`FIELD_DEFINITIONS.md`に既に定義済みの一次データ・手動入力データ・
   移送データのAS-IS-ID**（例: AS-IS-032, AS-IS-129）→ 到達したら展開を止め、
   既存定義を参照する
2. **DCF/WACC構成要素系・成長率トレンド系など、別サブカテゴリに属する
   導出データのAS-IS-ID**（例: WACC・成長率・FCFベース・RPO補正・成長
   オプションPV・ネットキャッシュ等）→ これらは別サブカテゴリで別途
   定義予定のため、本フェーズでは「そのサブモデルが何を表すか」を一文で
   示した上でAS-IS-IDを引用し、内部アルゴリズムの再展開は行わない
   （本タスクの依頼文中の良い例自体が「割引率（AS-IS-XXX、WACC構成要素）」
   という粒度で止めていることに準拠）
3. **AS-IS番号を持たない一次データ**（`components.current_price`・
   `diluted_shares`・`beta`等、499件の最終カタログには個別項目として
   含まれていない内部フィールド）→ yfinance/SEC EDGARの実際の取得経路を
   直接明記する

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義（最小単位まで分解した計算式） | データ取得元（最終的にたどり着く一次データ等のAS-IS-ID一覧） | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-002 | TANUKI VALUATION | 理論株価（β込みWACC、参考①） | `intrinsic_value_beta` | `intrinsic_value_beta = round(IVPS_β, 2)`<br>`IVPS_β = V0_β/diluted_shares + RPO_PV/diluted_shares + GrowthOption_PV/diluted_shares + net_cash_per_share`<br>（本来 `P_t = V0×(1+α) + RPO_PV + GrowthOption_PV` だが `α=0.0` 固定〈ALPHA-REDESIGN-1、alpha_uncappedは参考値としてのみ保持〉のため実質 `P_t = V0 + RPO_PV + GrowthOption_PV`）<br>`V0_β` = base_fcfを高成長率で複利成長させた将来FCF列を、割引率=**WACC_β（β込みCAPM）**で現在価値化した合計（2段階/3段階/線形逓減DCFのいずれか、`maturity_config`の判定に従う）<br>`base_fcf` = AS-IS-019（`fcf_base.base_fcf`、DCF/WACC構成要素系・未定義。fcf_5yr_avgとfcf_2yr_avgのCV〈変動係数〉が閾値0.5超か否かで自動選択）<br>高成長率 = AS-IS-012（`growth.rate`、DCF/WACC構成要素系・未定義）<br>WACC_β = AS-IS-013（`wacc.value`、DCF/WACC構成要素系・未定義。CAPM: `Rf + β×(Rm-Rf)`、Rf=4.3%/Rm=10%固定定数）<br>`RPO_PV` = AS-IS-024（`rpo_adjustment.rpo_pv`、未定義）<br>`GrowthOption_PV` = AS-IS-016（`growth_options.total_pv`、未定義）<br>`diluted_shares` = SEC EDGAR一次データ（`SECReader.get_diluted_shares()`、499件カタログ対象外、`data_fetcher.py:402`）<br>`net_cash_per_share` = AS-IS-025（`bs_adjustment.net_cash_per_share`、未定義。`net_cash/diluted_shares`。net_cash自体は`SECReader.get_net_cash()`由来のSEC EDGARベース値） | AS-IS-019, AS-IS-012, AS-IS-013, AS-IS-024, AS-IS-016, AS-IS-025（いずれもDCF/WACC構成要素系・未定義）＋ diluted_shares（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-003 | TANUKI VALUATION | 乖離率（β込みWACC、参考①） | `upside_percent_beta` | `upside_percent_beta = round(((IVPS_β_raw / current_price) - 1) × 100, 1)`<br>`IVPS_β_raw` は丸め前の`intrinsic_value_per_share_beta`（AS-IS-002の`intrinsic_value_beta`は同じ値を別途round(2)した表示用フィールドであり、参照元は共通だが丸め段階が異なる点に注意）<br>`current_price` = yfinance一次データ（現在株価、499件カタログ対象外、`data_fetcher.py:491-497`） | AS-IS-002と同じ構成要素（本表参照）＋ current_price（yfinance、カタログ対象外） | 導出データ |
| AS-IS-004 | TANUKI VALUATION | 理論株価（リスクフリーレート、参考②） | `intrinsic_value_rf` | `intrinsic_value_rf = round(IVPS_rf, 2)`<br>`IVPS_rf = V0_rf/diluted_shares + RPO_PV/diluted_shares + GrowthOption_PV/diluted_shares + net_cash_per_share`（α=0固定はAS-IS-002と同様）<br>`V0_rf` = base_fcfの将来FCF列を、割引率=**risk_free_rate（AS-IS-013のrisk_free_rate要素、固定値4.3%）**で現在価値化した合計。β・市場リターン要素を使わない「リスクゼロ」割引のため理論上の上限値となる<br>他の構成要素（base_fcf・高成長率・RPO_PV・GrowthOption_PV・diluted_shares・net_cash_per_share）はAS-IS-002と共通 | AS-IS-002と同じ（risk_free_rate定数のみ相違、AS-IS-013に内包） | 導出データ |
| AS-IS-005 | TANUKI VALUATION | 乖離率（リスクフリーレート、参考②） | `upside_percent_rf` | `upside_percent_rf = round(((IVPS_rf / current_price) - 1) × 100, 1)`<br>`IVPS_rf`はAS-IS-004、`current_price`はAS-IS-003と同じ | AS-IS-004と同じ＋ current_price（yfinance、カタログ対象外） | 導出データ |
| AS-IS-006 | TANUKI VALUATION | 乖離率（メイン、統一クラスタの唯一の正） | `upside_percent` | `upside_percent = round(((intrinsic_value_per_share / current_price) - 1) × 100, 1)`<br>`intrinsic_value_per_share = V0_rm/diluted_shares + RPO_PV/diluted_shares + GrowthOption_PV/diluted_shares + net_cash_per_share`（=AS-IS-001相当値。α=0固定はAS-IS-002と同様）<br>`V0_rm` = base_fcfの将来FCF列を、割引率=**market_return（AS-IS-013のmarket_return要素、固定値10%、βを使わず「市場から独立した本質的価値」を意図した割引率）**で現在価値化した合計<br>他の構成要素（base_fcf・高成長率・RPO_PV・GrowthOption_PV・diluted_shares・net_cash_per_share）はAS-IS-002と共通 | AS-IS-002と同じ（market_return定数のみ相違、AS-IS-013に内包） | 導出データ |
| AS-IS-031 | TANUKI VALUATION | 調整後PER（EPS Analyzer基準） | `per_adjusted` | `per_adjusted = round(current_price / ttm_adj_eps, 2)`（`ttm_adj_eps<=0`または直近四半期4件未満ならNone。年次フォールバックなし）<br>`ttm_adj_eps = Σ(直近4四半期のadjusted_eps)`<br>`adjusted_eps` = AS-IS-267（EPS Analyzer `quarters[].adjusted_eps`、CF収益性系・未定義。GAAP EPSに一過性項目除去・DTA自動補正等を反映した調整後値）<br>`current_price` = yfinance一次データ（カタログ対象外） | AS-IS-267（CF収益性系・未定義）＋ current_price（yfinance、カタログ対象外） | 導出データ |
| AS-IS-055 | TANUKI VALUATION | ERP①（株式リスクプレミアム、latest.json保存版） | `erp` / `forward_earnings_yield` | `forward_earnings_yield = round(forward_eps / current_price, 4)`<br>`erp = round(forward_earnings_yield - risk_free_rate, 4)`<br>`forward_eps` = AS-IS-032（TANUKI VALUATION `components.forward_eps`、**一次データ・既定義**。yfinance `forwardEps`）<br>`current_price` = yfinance一次データ（カタログ対象外）<br>`risk_free_rate` = AS-IS-013（`wacc.risk_free_rate`、DCF/WACC構成要素系・未定義。`calculate_wacc()`のデフォルト引数固定値4.3%であり、実勢金利をその都度取得する設計ではない） | AS-IS-032（既定義・一次データ）＋ AS-IS-013（未定義）＋ current_price（yfinance、カタログ対象外） | 導出データ |
| AS-IS-056 | TANUKI VALUATION | ERP②（report.txt表示版、非保存） | （report.txt内ローカル変数 `_erp`/`_ey`、JSON非保存） | AS-IS-055と完全に同一の式（`_ey = forward_eps / current_price; _erp = _ey - risk_free_rate`）だが、`pipeline.py:_generate_report()`内で`latest.json`の`comps`/`wacc_data`から改めて同じforward_eps・current_price・risk_free_rateを読み直し、**別実装として重複計算**している（`round()`は明示適用されず、表示時のf-string`.2f`でのみ丸められる）。入力が同一である限り値は一致するはずだが、コードが2箇所に分かれているため、将来どちらか一方だけを修正すると不整合が生じるリスクがある | AS-IS-055と同じ（本質的に同一データ源を再取得しているのみ） | 導出データ |
| AS-IS-113 | HypeCore | 期待スコア | `expectation_score` | `expectation_score = mean( z(ma200_dev), z(ma50_dev), z(price_iv_ratio), analyst_score )`（存在する列のみ平均、いずれも算出不可ならNaN）<br>`z(x) = (x - rolling_mean_24(x)) / (rolling_std_24(x) + 1e-9)`（24ヶ月ローリングZ-score、`min_periods=6`）<br>`ma200_dev` = AS-IS-087（成長率・トレンド系・未定義）、`ma50_dev` = AS-IS-088（同・未定義）<br>`price_iv_ratio` = AS-IS-116（本表参照）<br>`analyst_score = z(analyst_upgrade_rate)`、`analyst_upgrade_rate` = AS-IS-105（成長率・トレンド系・未定義。yfinance `upgrades_downgrades`から算出した月次アップグレード比率の3ヶ月移動平均） | AS-IS-087, AS-IS-088, AS-IS-105（成長率・トレンド系・未定義）＋ AS-IS-116（本表内） | 導出データ |
| AS-IS-116 | HypeCore | 株価/IV比率 | `price_iv_ratio` | `price_iv_ratio = price / iv`<br>`price` = AS-IS-084（HypeCore `price`、一次データ・未定義。yfinance `history()`の月末終値を`resample("ME").agg({"price":"last"})`で選択したもの、計算なし）<br>`iv` = TANUKI VALUATIONの`intrinsic_value_per_share`（AS-IS-006の乖離率算出に用いる理論株価と同一値）を`fetch_tanuki_iv()`が`history/*.json`・`latest.json`から直接読み取り月次系列化したもの | AS-IS-084（一次データ・未定義）＋ AS-IS-006の理論株価（本表参照。実体はAS-IS-001、DCF/WACC構成要素系・未定義） | 導出データ |
| AS-IS-122 | HypeCore | バリュエーション倍率パネル（PER/PS/PEG/EV-EBITDA） | `renderValMultiples()`（detail.html） | TANUKI `latest.json`優先→HypeCore自身の`poc.json`（`fetch_info_snapshot()`）へフォールバックする2ルート併存構造（**PERのみフォールバックなし**）:<br>`PER = comps.per`（nullなら「—」表示。フォールバックなし）。`comps.per`はAS-IS-032の一部（yfinance trailingPE優先/forwardPEフォールバック）<br>`PS = comps.ps ?? poc.psr`。`comps.ps`はAS-IS-032の一部（yfinance `priceToSalesTrailing12Months`）。`poc.psr` = AS-IS-099（一次データ・未定義、同一のyfinanceフィールド）<br>`PEG = comps.peg ?? poc.peg_ratio`。`comps.peg`はAS-IS-032の一部。`poc.peg_ratio` = AS-IS-098（一次データ・未定義、yfinance `pegRatio`）<br>`EV/EBITDA = (comps.ev_ebitda が正値ならそれ) ?? (poc.ev_ebitda が正値ならそれ)`。`comps.ev_ebitda`はAS-IS-032の一部（yfinance `enterpriseToEbitda`、負値もそのまま格納）。`poc.ev_ebitda` = AS-IS-117（一次データ・未定義、同フィールド。`hypecore.py:130`のコメントで「負値も格納（UIで変換）」と明記） | AS-IS-032（既定義・一次データ）＋ AS-IS-099, AS-IS-098, AS-IS-117（一次データ・未定義） | 導出データ |
| AS-IS-132 | STONKS SILO | PSR（Annual基準） | `valuation.psr` | `psr = round(market_cap / latest_rev, 1)`（いずれか欠落/0ならNone）<br>`market_cap` = AS-IS-130（一次データ・未定義。yfinance `info.get("marketCap")`、`valuation_fetcher.py:8`）<br>`latest_rev` = 直近年度の`revenue_sanitized`（2パス外れ値検出でNoneにされていない最新年のもの。`fetcher.py:_sanitize_revenue()`: 非最新年かつ「最大値を除いた中央値の10倍超」または「Pass1後の中央値の1/10未満」ならNoneに置換、それ以外は`revenue`そのまま）<br>`revenue` = AS-IS-129（**一次データ・既定義**。SEC EDGAR `pl.revenue`） | AS-IS-130（未定義）＋ AS-IS-129（既定義・一次データ） | 導出データ |
| AS-IS-133 | STONKS SILO | EV/Sales（Annual基準） | `valuation.ev_sales` | `ev_sales = round(enterprise_value / latest_rev, 1)`（いずれか欠落/0ならNone）<br>`enterprise_value` = yfinance `info.get("enterpriseValue")`（`valuation_fetcher.py:10`。499件最終カタログでは「JSON出力のみ・未参照」としてステップ6で除外されたためAS-IS番号を持たない）<br>`latest_rev` = AS-IS-132と同じ（`revenue_sanitized`、最終的にAS-IS-129〈既定義〉に帰着） | AS-IS-129（既定義・一次データ）＋ enterprise_value（yfinance、カタログ対象外） | 導出データ |

### 分解の過程で新たに気づいた問題

- **PSRの定義がサブシステム間で本当に異なる箇所を特定した**: 従来「TANUKI・
  HypeCore・STONKS SILOでPSRの定義自体が異なる」と認識されていたが、
  実際にコードを追うと**TANUKI（AS-IS-032の`ps`）とHypeCore（AS-IS-099の
  `psr`）は同一のyfinance `priceToSalesTrailing12Months`（TTM・市場データ
  基準）を参照しており、この2つは定義が一致している**。定義が異なるのは
  **STONKS SILOの`valuation.psr`（AS-IS-132）のみ**であり、こちらはSEC年次
  決算の`revenue_sanitized`（Annual・直近開示年度基準）を分母にしている。
  TTM基準とAnnual基準の混同であり、`CLAUDE_CODE_START.md`の
  EPS-PER-TTM-1（GAAP PERとAdjusted PERの期間ベース不一致）と同種の問題が
  PSRについても未反映のまま残っている。
- **EV/EBITDAの負値格納は一次データ段階の設計であり、AS-IS-122の表示自体は
  正しくガードされている**: `hypecore.py:130`のコメント「負値も格納
  （UIで変換）」の通り、AS-IS-032・AS-IS-117いずれも負のEV/EBITDAを
  そのまま`latest.json`/`poc.json`に格納する設計。AS-IS-122
  （`renderValMultiples()`）自体は正値のみ表示するガードが入っており画面上の
  実害はないが、**この生の負値をガードなしに消費する別画面・別システムが
  将来追加された場合、そこで初めて誤表示が発生しうる**という潜在リスクが
  残る。
- **ERP①（AS-IS-055）とERP②（AS-IS-056）は同一データソース・同一式を
  2箇所で独立に再計算している**: `pipeline.py`内の`_save_result()`と
  `_generate_report()`が、どちらも`forward_eps`/`current_price`/
  `risk_free_rate`を個別に読み直して同じ式を計算する構造になっており、
  共通関数化されていない。片方だけ修正すると①②が食い違う保守リスクが
  ある。
- **risk_free_rate（AS-IS-013の一部）はMACRO PULSEのような実勢金利取得
  ではなく固定定数**: `calculate_wacc()`のデフォルト引数`0.043`が
  そのまま使われ続けており（呼び出し側もオーバーライドしていない）、
  AS-IS-185（MACRO PULSE「1Y EXPECTED FF」、FRED `DGS1`実勢取得）のような
  動的取得の仕組みは持たない。ERP（AS-IS-055/056）はこの固定値を
  そのままリスクフリーレートとして使うため、実勢金利が変動してもERPの
  「金利側」の要素は追随しない。
- **PERのみHypeCoreバリュエーションパネル（AS-IS-122）でフォールバックが
  ない非対称構造**: PS/PEG/EV-EBITDAはTANUKIデータ欠落時にHypeCore自身の
  `poc.json`へフォールバックするが、PERだけはTANUKIの`comps.per`のみを
  参照しフォールバックしない（`detail.html:550`）。意図的な設計か単なる
  実装漏れかはコード上は判別できない。

### 次フェーズへの申し送り

- 本フェーズで参照した以下のAS-IS-IDは、今回「引用のみ」で内部アルゴリズムの
  再展開を行っていない。DCF/WACC構成要素系（45件）フェーズで定義予定:
  AS-IS-001, AS-IS-012, AS-IS-013, AS-IS-016, AS-IS-019, AS-IS-024, AS-IS-025
- 成長率・トレンド系（43件）フェーズで定義予定: AS-IS-087, AS-IS-088, AS-IS-105
- CF収益性系（27件）フェーズで定義予定: AS-IS-267
- 一次データとして既に性質は特定済みだが`FIELD_DEFINITIONS.md`本体の
  一次データ表にはまだ書き込まれていないもの（`DERIVED_DATA_SUBCATEGORIES.md`
  着手前訂正の13件に該当）: AS-IS-084, AS-IS-098, AS-IS-099, AS-IS-117,
  AS-IS-130。次に一次データ表を更新する機会に合わせて追記することを推奨する
- `components.current_price`・`diluted_shares`・`beta`・`roe_10yr_avg`・
  `latest_revenue`・`sector`等、TANUKI VALUATIONの計算入力として使われる
  内部フィールドの多くはAS-IS番号を持たない（499件の最終カタログに個別
  項目として含まれていない）。DCF/WACC構成要素系フェーズで`fcf_base`等を
  定義する際、これらの実際の取得経路（`data_fetcher.py`経由のyfinance/
  SEC EDGAR）も合わせて記録することを推奨する

---

## 対象4（フェーズ4）: 導出データ — キャッシュフロー・収益性系（27件）

出発点: `DERIVED_DATA_SUBCATEGORIES.md`「キャッシュフロー・収益性系（27件）」
（ステップ6確定後392件ベース、AS-IS-026/028/045/046/047/049/071/073/096/139/
144/145/146/147/148/153/154/155/156/157/160/267/274/281/391/392/393）

実装（コード修正）は行っていない。定義の記録のみ。分解ルールは前フェーズ
（評価倍率・バリュエーション系）と同一（既定義AS-IS-IDで停止／別サブ
カテゴリのAS-IS-IDは一文引用で停止／カタログ対象外の一次データは実際の
取得経路を直接明記）。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義（最小単位まで分解した計算式） | データ取得元（最終的にたどり着く一次データ等のAS-IS-ID一覧） | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-026 | TANUKI VALUATION | Moat Score（経済的濠スコア） | `components.moat_score` 等 | `moat_score = gm_norm×0.40 + roic_norm×0.40 + fcf_norm×0.20`（3指標が全てNoneの場合のみ`moat_score=0.5`固定）<br>`gm_norm = clamp(gross_margin_3yr_avg / 1.0, 0, 1)`<br>`roic_norm = clamp((roic - 0.10) / 0.30, 0, 1)`（0.10はAS-IS-013の`market_return`要素、DCF/WACC構成要素系・未定義）<br>`fcf_norm = clamp(fcf_margin_3yr_avg / 0.30, 0, 1)`<br>`phase1_years = 3 + round(moat_score × 7)`（3〜10年、DCF高成長期間・感応度分析base_yearsに連動）<br>`gross_margin_3yr_avg` = normalized四半期JSONの年次GrossProfit/Revenue直近3年平均（年次タグ欠如時は直近12四半期合算にフォールバック。SEC EDGAR一次データ、カタログ対象外、`pipeline.py:_calc_moat_inputs`）<br>`roic = NOPAT/Invested_Capital`、`NOPAT=OperatingIncome×(1-21%固定実効税率)`、`Invested_Capital=Equity+LTDebt+STDebt-Cash`（いずれもSEC EDGAR annual一次データ、カタログ対象外、`pipeline.py:_calc_roic_wacc_ratio`）<br>`fcf_margin_3yr_avg` = annual SECの`free_cash_flow/revenue`直近3年平均（`free_cash_flow`はAS-IS-047と同一データ由来） | AS-IS-013（未定義）＋ GrossProfit/Revenue/OperatingIncome/Equity/LTDebt/STDebt/Cash/FCF（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-028 | TANUKI VALUATION | moat_score / moat_phase1_years / moat_gross_margin_norm / moat_roic_norm / moat_fcf_margin_norm | 同上 | AS-IS-026と完全に同一の`calculator/adjustments.py:calculate_moat_score()`戻り値を指す別カタログエントリ（重複、下記「気づいた問題」参照） | AS-IS-026と同じ | 導出データ |
| AS-IS-045 | TANUKI VALUATION | financial_health.*（net_debt/total_debt/cash_and_equivalents/sbc_ttm/dilution_3yr_annual_pct等） | `financial_health` | `total_debt = bs_adjustment.long_term_debt + bs_adjustment.short_term_debt`<br>`cash_and_equivalents = bs_adjustment.cash`、`short_term_investments = bs_adjustment.short_term_investments`<br>`net_debt = -bs_adjustment.net_cash`（符号反転。net_cashは「純キャッシュ」+、net_debtは「純負債」+の逆符号設計）<br>`bs_adjustment.*` = AS-IS-025（DCF/WACC構成要素系・未定義。TANUKIのDCF計算に使うBS値〈`SECReader.get_net_cash()`戻り値〉をreport.txt表示にもそのまま再利用し、単一の計算経路に統一）<br>`sbc_ttm` = 直近年`annual_{yr}.json`の`cf.stock_based_compensation`（SEC EDGAR、カタログ対象外）<br>`dilution_3yr_annual_pct = ((直近希薄化後株式数/3年前希薄化後株式数)^(1/3) - 1) × 100`。株式数はnormalized JSONの年次`SharesDiluted`（株式分割の遡及調整・SEC/yfinance株式数10倍超乖離時のsanity-check skipあり、SEC EDGAR、カタログ対象外） | AS-IS-025（未定義）＋ SharesDiluted/SBC（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-046 | TANUKI VALUATION | dupont.net_margin/asset_turnover/financial_leverage/roe_decomposed | `dupont` | `net_margin = NI_TTM / Revenue_TTM`<br>`asset_turnover = Revenue_TTM / Total_Assets`<br>`financial_leverage = Total_Assets / Equity`<br>`roe_decomposed = net_margin × asset_turnover × financial_leverage`<br>`NI_TTM`/`Revenue_TTM` = `common/sec_data/ttm/{ticker}_ttm_series.json`の`series[0].flow.NetIncome/Revenue`（SEC EDGAR、カタログ対象外）<br>`Total_Assets`/`Equity` = 直近四半期`quarterly_*.json`の`bs.total_assets`/`bs.stockholders_equity`（同上）<br>除外条件: `Revenue_TTM < $15M`は計算せず`{"excluded": True}`<br>信頼性フラグ: 直近4四半期のうち最大1四半期の`NetIncome`絶対値がTTM合計の60%超なら`reliability="LOW"` | NI_TTM/Revenue_TTM/Total_Assets/Equity（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-047 | TANUKI VALUATION | fcf_history[] | `fcf_history` | `fcf_history[].fcf` = 直近5年`annual_{yr}.json`の`cf.free_cash_flow`（SEC EDGAR一次データ、カタログ対象外。`common/sec_data/parser.py`が`FCF=OCF-max(0,\|CapEx\|-\|FinanceLeasePmts\|)`として事前計算済みの値をそのまま転記）<br>`fcf_history[].fcf_margin = round(fcf/revenue×100, 1)`、`revenue`は同年`pl.revenue`（SEC EDGAR、カタログ対象外） | free_cash_flow/revenue（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-049 | TANUKI VALUATION | computed_runway_months | `computed_runway_months` | `computed_runway_months = cash / monthly_burn`、`monthly_burn = abs(直近年fcf) / 12`<br>発動条件（いずれか）: 直近四半期GAAP EPS<0（AS-IS-267参照）／直近年FCF<0（AS-IS-047参照）／`cash < $100M`<br>`cash` = AS-IS-045の`financial_health.cash_and_equivalents`（本表参照） | AS-IS-045, AS-IS-047, AS-IS-267（いずれも本表内） | 導出データ |
| AS-IS-071 | TANUKI VALUATION | キャッシュフロー分析セクション（stock.html独自チャート） | `loadCfData()` / `renderCfCharts()` | `OCF`/`CapEx`/`Revenue`/`SBC`/`DA` = `common/sec_data/normalized/{ticker}_quarterly_normalized.json`の直近8四半期値。**latest.jsonは使用せず、stock.htmlが独自に別ファイルを直接fetchして再計算する**（`loadCfData():411-456`）<br>チャート①CF推移: `OCF`（バー）、`CapEx`は`-CapEx`（符号反転して表示）、`FCF = OCF - CapEx`（**abs()なしでそのまま減算**）<br>チャート②FCFマージン: `(OCF-CapEx)/Revenue×100`。直近4四半期FCF合計が負なら「FCF赤字」バナー<br>チャート③SBC・D&A比率: `SBC/Revenue×100`、`DA/Revenue×100`。SBC比率100%超の四半期があれば注記（`renderCfCharts():458-580`） | OCF/CapEx/Revenue/SBC/DA（SEC EDGAR、common/sec_data正規化JSON、カタログ対象外） | 導出データ |
| AS-IS-073 | TANUKI VALUATION | 平均Moat | `avg-moat`（index.html集計表示） | `avg-moat = mean(全銘柄のcomponents.moat_score)`（nullは除外）。`components.moat_score`はAS-IS-026/028と同一値（`loadTickers():567-569`） | AS-IS-026（本表参照） | 導出データ |
| AS-IS-096 | HypeCore | FCF Yield | `fcf_yield` | `fcf_yield = ocf / (price × shares) × 100`<br>`ocf` = HypeCoreが`{ticker}_quarterly_normalized.json`から取得した**単一四半期**のOCF値（TTM合算ではない。SEC EDGAR、カタログ対象外、`fetch_quarterly_fundamentals():155-157`）<br>`price` = AS-IS-084（HypeCore `price`、一次データ・未定義、評価倍率フェーズ参照）<br>`shares` = yfinance `info.get("sharesOutstanding")`（カタログ対象外、`fetch_info_snapshot():129`） | AS-IS-084（一次データ・未定義）＋ ocf(SEC EDGAR、カタログ対象外) + shares(yfinance、カタログ対象外) | 導出データ |
| AS-IS-139 | STONKS SILO | gross_margin | `gross_margin` | `gross_margin = gross_profit / revenue_sanitized × 100`（直近年）<br>`gross_profit` = SEC EDGAR一次データ（`pl.gross_profit`、カタログ対象外。欠損時は`revenue-cost_of_revenue`等で逆算し`gross_profit_derived=True`）<br>`revenue_sanitized` = 前フェーズ定義のAS-IS-132/133と同じ2パス外れ値検出済み値（最終的にAS-IS-129に帰着） | AS-IS-129（既定義・一次データ）＋ gross_profit（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-144 | STONKS SILO | mature_profit（成熟想定利益） | `mature_profit` | `mature_profit = net_income + (research_and_development or 0) + (selling_and_marketing or 0)`（直近年、投資的支出を全て足し戻した想定利益）<br>`net_income`/`research_and_development`/`selling_and_marketing` = SEC EDGAR一次データ（`pl.*`、カタログ対象外） | net_income/R&D/S&M（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-145 | STONKS SILO | mature_profit_note | `mature_profit_note` | `mature_profit < 0` の場合のみ`"投資除外後も赤字"`を設定、それ以外は空文字。AS-IS-144のmature_profitに従属 | AS-IS-144（本表参照） | 導出データ |
| AS-IS-146 | STONKS SILO | sbc_adjusted_fcf | `sbc_adjusted_fcf` | `sbc_adjusted_fcf = free_cash_flow - stock_based_compensation`（直近年、両方非Noneの場合のみ）<br>`free_cash_flow` = AS-IS-047と同一の`common/sec_data`由来FCF（既にCapEx符号吸収済み）<br>`stock_based_compensation` = SEC EDGAR一次データ（`cf.stock_based_compensation`、カタログ対象外） | AS-IS-047（本表参照）＋ stock_based_compensation（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-147 | STONKS SILO | sbc_ratio | `sbc_ratio` | `sbc_ratio = stock_based_compensation / revenue_sanitized × 100`（直近年） | AS-IS-139のrevenue_sanitized経由でAS-IS-129（既定義）＋ SBC（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-148 | STONKS SILO | sbc_yoy_change | `sbc_yoy_change` | `sbc_yoy_change = (sbc_今年 - sbc_前年) / abs(sbc_前年) × 100`（前年SBCが0でない場合のみ算出） | SBC（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-153 | STONKS SILO | cash | `cash` | `cash = cash_and_equivalents + short_term_investments`（Noneは0扱い、両方Noneならcash=None。直近年`bs.*`、SEC EDGAR、カタログ対象外） | bs.cash_and_equivalents/short_term_investments（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-154 | STONKS SILO | monthly_burn | `monthly_burn` | `monthly_burn = (ocf - abs(capex)) / 12`（ocf・capex両方非None時）。ocfのみ判明時は`monthly_burn = ocf / 12`<br>`ocf`/`capex` = 直近年`cf.operating_cash_flow`/`cf.capital_expenditure`（SEC EDGAR、カタログ対象外） | ocf/capex（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-155 | STONKS SILO | runway_months | `runway_months` | `runway_months = cash / abs(monthly_burn)`（`monthly_burn<0`の場合のみ。`monthly_burn>=0`は無限大=SAFE扱い）<br>`cash`=AS-IS-153、`monthly_burn`=AS-IS-154（いずれも本表参照） | AS-IS-153, AS-IS-154（本表内） | 導出データ |
| AS-IS-156 | STONKS SILO | ocf_annual（単年、月次バーン内訳表示用） | `ocf_annual` | 直近年`cf.operating_cash_flow`（AS-IS-154の`ocf`と同一値。SEC EDGAR、カタログ対象外） | ocf（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-157 | STONKS SILO | capex_annual | `capex_annual` | 直近年`cf.capital_expenditure`のSEC EDGAR生値を**符号正規化なしでそのまま表示**（SEC EDGAR、カタログ対象外） | capex（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-160 | STONKS SILO | ocf_annual（年次dict） | `ocf_annual`（`_analyze_profitability_path()`内） | `{year: cf.operating_cash_flow for year in years}`（複数年。AS-IS-156の単年版を全年に拡張したもの） | AS-IS-156と同じ（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-267 | EPS Analyzer | quarters[].gaap_eps/adjusted_eps/gaap_net_income/adjusted_net_income/diluted_shares_used/adjustments/net_adjustment_total | `calculate_eps()` | `gaap_eps = gaap_net_income / diluted_shares_used`<br>`gaap_net_income`/`diluted_shares_used` = 四半期`net_income`/`diluted_shares`のXBRL正規化値（計算なしのパススルー。SEC EDGAR、カタログ対象外）<br>`adjusted_net_income = gaap_net_income + net_adjustment_total`<br>`adjusted_eps = adjusted_net_income / diluted_shares_used`<br>`net_adjustment_total`/`adjustments[]` = 一過性項目検出（`detect_adjustments()`）＋税効果適用（`apply_tax_adjustments()`）の結果。信頼性・品質判定系のAS-IS-268/269（未定義。DTA自動補正Type-A/B等の内部ロジックは当該サブカテゴリで別途定義予定） | AS-IS-268, AS-IS-269（信頼性・品質判定系・未定義）＋ net_income/diluted_shares（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-274 | EPS Analyzer | gaap_eps/adjusted_eps（summary.json） | `generate_summary()` | `summary.json`の`gaap_eps`/`adjusted_eps` = 最新四半期`quarters[0]`（AS-IS-267）の値をそのまま転記（再計算なし） | AS-IS-267（本表参照） | 導出データ |
| AS-IS-281 | EPS Analyzer | ttm.json（ttm[].period/net_income/adjusted_income/diluted_shares/eps/adjusted_eps） | `calculate_ttm()` | `net_income = Σ(直近4四半期のgaap_net_income)`<br>`adjusted_income = net_income + Σ(直近4四半期のnet_adjustment_total)`<br>`diluted_shares = mean(直近4四半期のdiluted_shares_used)`（単純平均、加重なし）<br>`eps = net_income/diluted_shares`、`adjusted_eps = adjusted_income/diluted_shares`。いずれもAS-IS-267の4四半期分から算出 | AS-IS-267（本表参照） | 導出データ |
| AS-IS-391 | Portfolio | total_assets_usd | `total_assets_usd` | `total_assets_usd = total_equity_usd + total_cash_usd`<br>`total_equity_usd = Σ(shares × price)`（全ブローカー・全ポジション合算）<br>`shares`/`avg_cost` = `docs/portfolio/data/portfolio.json`の`brokers.{broker}.positions.{ticker}.shares/avg_cost`（手動編集ファイル、書き込みスクリプトなし。カタログ対象外）<br>`price` = AS-IS-084（HypeCore `{ticker}_poc.json`の`monthly[-1].price`、一次データ・未定義、評価倍率フェーズ参照）<br>`total_cash_usd = Σ(brokers.{broker}.cash)`（同portfolio.json） | portfolio.json（手動入力相当、カタログ対象外）＋ AS-IS-084（一次データ・未定義） | 導出データ |
| AS-IS-392 | Portfolio | total_assets_jpy | `total_assets_jpy` | `total_assets_jpy = total_assets_usd × usdjpy`。`usdjpy` = AS-IS-390（Portfolio `usdjpy`、**既定義・移送データ**。Market Pulseの`indicators.ドル円.value`=AS-IS-312〈既定義・一次データ〉を再利用） | AS-IS-391（本表参照）＋ AS-IS-390（既定義・移送データ） | 導出データ |
| AS-IS-393 | Portfolio | total_pnl_usd | `total_pnl_usd` | `total_pnl_usd = total_equity_usd - total_cost_usd`<br>`total_cost_usd = Σ(shares × avg_cost)`（全ブローカー・全ポジション合算、portfolio.json由来）<br>`total_equity_usd`はAS-IS-391と共通 | portfolio.json（カタログ対象外）＋ AS-IS-391の構成要素 | 導出データ |

### 分解の過程で新たに気づいた問題

- **FCF/CapExの符号不統一が実害化している箇所を特定した（AS-IS-071・最重要）**:
  `common/sec_data/parser.py:1499`が既知の設計注記として明記する通り、
  SEC XBRLの`CapEx`（capital_expenditure相当）は報告企業により正負どちらの
  符号でも報告されうる。正式なFCF計算（AS-IS-047が使う`cf.free_cash_flow`、
  `common/sec_data/parser.py`側）は`FCF = OCF - max(0, |CapEx|-|FinanceLease|)`
  と`abs()`で符号を吸収済みだが、**stock.htmlの「キャッシュフロー分析
  セクション」（AS-IS-071、`loadCfData()`/`renderCfCharts()`）はlatest.json
  を使わず独自に`{ticker}_quarterly_normalized.json`を直接fetchして
  `FCF = OCF - CapEx`をabs()なしで再計算している**。CapExが負値（cash
  outflowをマイナス表現する報告様式）の銘柄では`OCF - (負のCapEx) =
  OCF + |CapEx|`となり、実際より高いFCFを表示してしまう。同様に
  `capexNeg = -CapEx`（棒グラフ表示用）も、CapExが既に負値の銘柄では
  正のバー（あたかも現金流入であるかのような表示）になる。この画面は
  latest.json不使用・独自再計算のため、AS-IS-047（正しくabs()処理済み）
  との整合性チェックが構造的に効かない。
- **同種の符号不統一がSTONKS SILOの表示専用フィールドにも存在する
  （AS-IS-157）**: `_analyze_runway()`内部の`monthly_burn`計算
  （AS-IS-154）は`abs(capex)`で符号を正規化するのに対し、**表示用の
  `capex_annual`フィールド自体（AS-IS-157）は生の符号のまま**
  （`analyzer.py:495,524`）。同一のCapEx原因で「ロジック側は正規化・
  表示側は未正規化」という非対称な設計が2箇所（TANUKI VALUATIONの
  AS-IS-071とSTONKS SILOのAS-IS-157）で独立に発生している。
- **moat_score（AS-IS-026/028）の部分欠損が「実測値0」として混入する**:
  `gm_norm`/`roic_norm`/`fcf_norm`はいずれも`(値 or 0.0)`で計算されており、
  3指標が**全て**Noneの場合のみ`moat_score=0.5`のデフォルトが働く
  （`calculate_moat_score()`冒頭の特殊ケース）。しかし3指標のうち
  1〜2個だけが欠損している場合はこの特殊ケースに該当せず、欠損指標が
  「実測値ゼロ」（例: ROIC=市場期待リターンちょうど、成長率=0等の
  最悪スコア相当）としてそのまま平均に混入し、moat_scoreが不当に
  低く算出される。
- **mature_profit/mature_profit_note（AS-IS-144/145）にS&M支出欠落の
  実例が確認できる**: `research_and_development`・`selling_and_marketing`
  がSEC上非開示（タグなし=None、SG&Aに統合計上する企業等）の場合、
  `or 0`により「支出ゼロ」として足し戻される。実際にはS&M費用が存在する
  のに個別タグ開示していないだけの銘柄では、本来より過小な足し戻し額に
  なり`mature_profit`が実態より低く算出される。`mature_profit_note`は
  この「タグ欠落による過小評価」と「真の赤字」を区別する仕組みを持たず、
  `mature_profit<0`という結果のみで判定する。
- **「Runway」概念がTANUKI VALUATION（AS-IS-049）とSTONKS SILO
  （AS-IS-155）で独立実装されており、cashの算出経路が異なる**:
  TANUKI側は`cash`をAS-IS-025（`SECReader.get_net_cash()`、セクター
  ガード適用・複数タグフォールバック補完あり）経由で取得するのに対し、
  STONKS SILO側の`cash`（AS-IS-153）は直近年`annual_{yr}.json`の`bs`
  セクションを単純合算するのみで、そうした補正を一切経由しない。
- **AS-IS-096（HypeCore `fcf_yield`）は名称と実体が食い違う**: 変数名は
  `fcf_yield`だが分子はOCF（営業CF、CapEx控除前）そのものであり、FCF
  ではない。かつ分子が単一四半期値のまま年率換算（×4等）されておらず、
  TANUKIのFCFマージン（年次・TTM前提）やSTONKS SILOのrunway計算
  （年次FCF/12=月次バーン）と単純比較すると期間ベースが食い違う。
- **AS-IS-267は同一AS-IS内に一次データ相当のパススルーと計算値が混在する**:
  `gaap_eps`/`gaap_net_income`/`diluted_shares_used`はXBRL値のパススルー
  （計算なし）である一方、`adjusted_eps`/`adjusted_net_income`は
  `net_adjustment_total`の加算を伴う真の計算値であり、Market Pulse
  ETF束ね行（AS-IS-320等）で既に記録済みのパターンと同型の混在が
  ここにも存在する。
- **AS-IS-045の`net_debt`はAS-IS-025の`net_cash`を符号反転しただけの
  別名フィールド**: `net_debt = -net_cash`という単純な符号反転だが、
  「正=ネットキャッシュ」の概念と「正=純負債」の概念が同じ元データから
  並存しているため、report.txt・latest.jsonを横断的に参照するコードで
  符号を取り違えるリスクがある。
- **AS-IS-026とAS-IS-028は同一の`calculate_moat_score()`戻り値を指す
  重複カタログエントリ**: 過去のインベントリ作成過程で同じ関数の出力が
  2つの異なるAS-IS-IDとして重複記録されている（前フェーズで発見した
  ERP①②の「重複計算」とは異なり、こちらは「同一計算の重複カタログ化」）。

### 次フェーズへの申し送り

- 本フェーズで引用のみ行い内部アルゴリズムを再展開しなかったAS-IS-ID:
  AS-IS-013（DCF/WACC構成要素系）、AS-IS-025（DCF/WACC構成要素系）、
  AS-IS-268・AS-IS-269（信頼性・品質判定系）、AS-IS-084・AS-IS-390・
  AS-IS-312（評価倍率フェーズで参照済み、AS-IS-312/390は既定義）
- STONKS SILOのSEC EDGAR一次データ（`gross_profit`/`net_income`/
  `research_and_development`/`selling_and_marketing`/`operating_cash_flow`/
  `capital_expenditure`/`stock_based_compensation`等）およびTANUKI
  VALUATIONの同種フィールド（`total_assets`/`stockholders_equity`等）は
  いずれもAS-IS番号を持たない内部フィールドである。DCF/WACC構成要素系・
  信頼性・品質判定系フェーズで関連項目を定義する際、実際の取得経路
  （`common/sec_data`正規化JSON経由）を合わせて記録することを推奨する
- AS-IS-026/028の重複統合、AS-IS-071とAS-IS-157のCapEx符号不統一修正は
  いずれも実装（コード修正）を伴うため、本タスクの範囲外として記録に
  とどめた。修正が必要と判断される場合は別途依頼文で着手する

---

## 対象5（フェーズ5）: 導出データ — 成長率・トレンド系（43件）

出発点: `DERIVED_DATA_SUBCATEGORIES.md`「成長率・トレンド系（43件）」
（ステップ6確定後392件ベース、AS-IS-068/076/077/079/085/086/087/088/089/090/
091/092/093/094/095/109/110/111/112/115/118/119/121/135/136/137/138/143/151/
152/161/165/166/167/168/169/170/171/172/174/175/176/177）

実装（コード修正）は行っていない。定義の記録のみ。分解ルールは前フェーズ
までと同一。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義（最小単位まで分解した計算式） | データ取得元（最終的にたどり着く一次データ等のAS-IS-ID一覧） | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-068 | TANUKI VALUATION | FCF CAGR(3yr)（stock.html独自チャート） | render内IIFE | `valid = fcf_history.filter(fcf!=null && fcf>0)`（AS-IS-047の`fcf_history[]`、既定義・前フェーズ参照）<br>`cagr = ((valid[-1].fcf / valid[-4].fcf) ** (1/3) - 1) × 100`（`valid.length>=4`のときのみ算出） | AS-IS-047（既定義・前フェーズ） | 導出データ |
| AS-IS-076 | TANUKI VALUATION | 200MA乖離（index.html独自計算） | `buildRows()` | `ma200_dev = (price - ma200_raw) / ma200_raw`<br>`price` = `components.current_price`（yfinance、カタログ対象外）<br>`ma200_raw` = `components.ma200` = yfinance `info.get("twoHundredDayAverage")`（Yahoo Finance側算出のスナップショット値、カタログ対象外、`data_fetcher.py:544`） | current_price/twoHundredDayAverage（yfinance、カタログ対象外） | 導出データ |
| AS-IS-077 | HypeCore | stage_label（他サブシステムからの参照、削除候補） | （TANUKI stock.html/pipeline.py、tanuki_score/index.htmlが直接読取） | AS-IS-086（本表参照）の値を、TANUKI VALUATION（MATRIX×HYPEシグナル表示、`_load_hype_info`/`_save_hypecore_history`）・TANUKI SCORE（TRIMチップ表示）がそのまま再表示しているだけの参照 | AS-IS-086（本表参照） | 導出データ |
| AS-IS-079 | HypeCore | STONKS SILO `deficit_quality.revenue_growth_pct`（他サブシステムからの参照、削除候補） | （TANUKI stock.html Matrix③パネル） | AS-IS-152（本表参照、STONKS SILO `revenue_growth_pct`）の値を、TANUKI VALUATION（Matrix③成長性系パネルのY軸）がそのまま再表示しているだけの参照 | AS-IS-152（本表参照） | 導出データ |
| AS-IS-085 | HypeCore | stage | `determine_stage()` | 優先順位付きルールベースでステージ番号(0〜4)を判定。主な入力: `ma200_dev`(AS-IS-087)・`ma200_mom`(`ma200_dev.diff(3)`、**JSON出力なし**、下記備考)・`from_peak`(AS-IS-089)・`price_mom3m`(月次価格3ヶ月変化率、カタログ対象外)・`rsi`(AS-IS-090)・`vol_surge`(AS-IS-092)・`sell_on_good_news`/`eps_surprise`/`analyst_upgrade_rate`/`buy_hold_ratio`(カタリスト・イベント予測系・未定義)・`expectation_score`(前フェーズ既定義AS-IS-113)/`fundamental_score`/`momentum_score`(本表AS-IS-115)。前月ステージとS3/S4連続月数によるヒステリシス（優先チェック）を持つ | AS-IS-087, AS-IS-089, AS-IS-090, AS-IS-092, AS-IS-113(既定義), AS-IS-115(本表参照) ＋ ma200_mom/price_mom3m(カタログ対象外) ＋ カタリスト系複数(未定義) | 導出データ |
| AS-IS-086 | HypeCore | stage_label | `STAGE_LABELS[stage]` | `{0:"失望/蓄積期",1:"期待覚醒期",2:"期待拡大期",3:"陶酔期",4:"期待剥落期"}`。AS-IS-085のstageをラベル文字列化しただけ | AS-IS-085（本表参照） | 導出データ |
| AS-IS-087 | HypeCore | ma200_dev | `ma200_dev` | `ma200_dev = (price - ma200) / (ma200+1e-9) × 100`<br>`price` = AS-IS-084（一次データ・未定義、評価倍率フェーズ参照）<br>`ma200` = 同一日次価格系列の`rolling(200).mean()`（HypeCore内部計算、カタログ対象外） | AS-IS-084（一次データ・未定義） | 導出データ |
| AS-IS-088 | HypeCore | ma50_dev（JSON出力のみ、未使用） | `ma50_dev` | `ma50_dev = (price - ma50) / (ma50+1e-9) × 100`。`ma50 = price.rolling(50).mean()`。AS-IS-087と同型（窓50日） | AS-IS-084（一次データ・未定義） | 導出データ |
| AS-IS-089 | HypeCore | from_peak | `from_peak` | `from_peak = (price - peak_24m) / peak_24m × 100`<br>`peak_24m = price.rolling(24, min_periods=6).max()`（**24ヶ月**の過去最高値。月次df上のrolling、日足ベースではない） | AS-IS-084（一次データ・未定義） | 導出データ |
| AS-IS-090 | HypeCore | rsi | `rsi` | 標準的な14日RSI（日次価格ベースで計算後、月末値のみ保持）<br>`gain=delta.clip(lower=0).rolling(14).mean()`、`loss=(-delta.clip(upper=0)).rolling(14).mean()`<br>`rsi = 100 - 100/(1+gain/(loss+1e-9))` | AS-IS-084（一次データ・未定義） | 導出データ |
| AS-IS-091 | HypeCore | volume_ratio（JSON出力のみ、未使用） | `volume_ratio` | `volume_ratio = volume/(vol_20d_avg+1e-9)`、`vol_20d_avg = volume.rolling(20).mean()`（日次出来高ベース、月末値を保持） | volume（yfinance history()、カタログ対象外） | 導出データ |
| AS-IS-092 | HypeCore | vol_surge | `vol_surge` | `vol_surge = volume_monthly/(vol_avg+1e-9)`、`vol_avg = volume_monthly.rolling(6, min_periods=3).mean()`（**月次**出来高の6ヶ月移動平均比。AS-IS-091〈日次20日平均比〉とは時間粒度が異なる別指標） | volume（yfinance history()、カタログ対象外） | 導出データ |
| AS-IS-093 | HypeCore | rev_yoy | `rev_yoy` | `rev_ttm = Revenue.rolling(4).sum()`（直近4四半期合計=TTM）<br>`rev_yoy = (rev_ttm / rev_ttm.shift(4) - 1) × 100`（TTM同士のYoY）<br>`Revenue` = `{ticker}_quarterly_normalized.json`のRevenue四半期系列（SEC EDGAR、カタログ対象外） | Revenue（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-094 | HypeCore | ni_yoy（JSON出力のみ、直接表示なし） | `ni_yoy` | `ni_yoy = NetIncome.pct_change(4) × 100`（**単一四半期**同士のYoY。AS-IS-093のTTMベースとは時間粒度が異なる、下記備考） | NetIncome（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-095 | HypeCore | rule40 | `rule40` | `rule40 = rev_yoy + op_margin`<br>`rev_yoy` = AS-IS-093（TTMベース、本表参照）<br>`op_margin = NetIncome/Revenue×100`（**単一四半期**の値同士の比率、TTMではない） | AS-IS-093（本表参照）＋ NetIncome(SEC EDGAR、カタログ対象外) | 導出データ |
| AS-IS-109 | HypeCore | substage_phase | `detect_substage()` | `detect_substage(row, stage, stage_months)`が返す`phase`キー（"入口"/"中盤"/"中盤A"/"中盤B"/"中盤B*"/"出口"等）。ステージごとに個別ロジック（下記real_strong等を参照） | AS-IS-085他（本表参照） | 導出データ |
| AS-IS-110 | HypeCore | substage_label | `detect_substage()` | `label`キー。stage=3(陶酔期)は`ma200_mom`/`from_peak`/`rsi`の組合せ、stage=4(期待剥落期)は`real_strong`・`valuation_overheat`(`price_iv_ratio>2.0`または`forward_pe>100`)・`ma200_shrinking`(`ma200_mom>-5`)の組合せで判定<br>`real_strong = _real_standard or _real_growth`<br>`_real_standard=(rev_yoy>15 and (eps_surprise is None or eps_surprise>-5)) or (eps_surprise>0 and rev_yoy>0)`<br>`_real_growth=(rev_yoy>30 and (eps_surprise is None or eps_surprise>-30))` | AS-IS-093他（本表参照）＋ price_iv_ratio(前フェーズ既定義AS-IS-116) | 導出データ |
| AS-IS-111 | HypeCore | substage_watch | `detect_substage()` | `watch`キー（次に確認すべき観点の説明文）。AS-IS-109/110と同一ロジック内で生成 | AS-IS-109/110（本表参照） | 導出データ |
| AS-IS-112 | HypeCore | substage_next | `detect_substage()` | `next`キー（次のアクション方針の説明文）。AS-IS-109/110と同一ロジック内で生成 | AS-IS-109/110（本表参照） | 導出データ |
| AS-IS-115 | HypeCore | momentum_score（JSON出力のみ、未使用） | `momentum_score` | `momentum_score = mean(z(ma50_dev), z(ma200_dev), z(rsi))`（存在する列のみ平均）。`z()`は前フェーズAS-IS-113と同じ24ヶ月ローリングZ-score | AS-IS-087, AS-IS-088（本表参照）＋ AS-IS-090（本表参照） | 導出データ |
| AS-IS-118 | HypeCore | low_base_effect（JSON出力のみ、未使用） | `low_base_effect` | `low_base_effect = prev_rev_yoy.notna() & (prev_rev_yoy<-10) & (rev_yoy.fillna(0)>50)`<br>`prev_rev_yoy = rev_yoy.shift(12)`（12ヶ月前=前年同月のrev_yoy） | AS-IS-093（本表参照） | 導出データ |
| AS-IS-119 | HypeCore | ライフサイクル（黎明/成長/拡大/成熟） | `detectLifecycle()`（detail.html/index.html重複実装、ロジック同一） | `g = (revenue_growth!=null) ? revenue_growth×100 : (rev_yoy ?? 0)`<br>`g>40→growth`、`g>15→expand`、`g>0→mature`、`それ以外→dawn`<br>`revenue_growth` = HypeCore一次データ相当（評価倍率フェーズでAS-IS-100として一次データへ再分類済みだが未定義。yfinance `revenueGrowth`、小数）<br>`rev_yoy` = AS-IS-093（本表参照、SEC EDGAR TTM%） | revenue_growth(一次データ相当・未定義) ＋ AS-IS-093（本表参照） | 導出データ |
| AS-IS-121 | HypeCore | 1ヶ月後のステージ遷移確率 | `calcTrans()` | `cnt[from][to]+=1`（`monthly`配列の隣接月同士のステージ遷移を全期間で集計、マルコフ的頻度表）<br>`prob[to] = round(cnt[cur][to]/Σcnt[cur][*]×100)`（当該銘柄の月次履歴全体から集計、JSON側に事前計算値はなくクライアント側で毎回集計） | AS-IS-085（本表参照、月次履歴全体） | 導出データ |
| AS-IS-135 | STONKS SILO | financial_vectors.fields.*（angle/length等） | `compute_vectors()` | `angle = _pct_to_angle(percentile)`、`length = _pct_to_length(percentile)`<br>`_pct_to_angle(pct) = (pct-50)/50×90`（-90°〜+90°）、`_pct_to_length(pct) = abs(pct-50)/50`（0〜1）<br>`percentile = _calc_percentile(change_pct, 同時点の全STONKS SILO銘柄のchange_pct分布)`（二分探索）<br>対象フィールド: Revenue/GrossProfit/OperatingIncome/RD/NetIncome/OCF/CapEx（SEC EDGAR、normalized四半期JSON経由、カタログ対象外） | SEC EDGAR（common/sec_data正規化JSON、カタログ対象外） | 導出データ |
| AS-IS-136 | STONKS SILO | cagr_3yr | `cagr_3yr` | `cagr_3yr = ((revenue_sanitized[years[-1]] / revenue_sanitized[years[-4]]) ** (1/3) - 1) × 100`（`len(years)>=4`のときのみ）。`years`は連続した年次リスト（フィルタなし）のため、AS-IS-068のような経過年数ズレは生じにくい | AS-IS-129（既定義・一次データ、revenue_sanitized経由） | 導出データ |
| AS-IS-137 | STONKS SILO | rnd_ratio | `rnd_ratio` | `rnd_ratio = research_and_development / revenue_sanitized × 100`（直近年） | AS-IS-129（既定義）＋ R&D(SEC EDGAR、カタログ対象外) | 導出データ |
| AS-IS-138 | STONKS SILO | sm_ratio | `sm_ratio` | `sm_ratio = selling_and_marketing / revenue_sanitized × 100`（直近年） | AS-IS-129（既定義）＋ S&M(SEC EDGAR、カタログ対象外) | 導出データ |
| AS-IS-143 | STONKS SILO | rule_of_40 | `rule_of_40` | `rule_of_40 = round(cagr_3yr + operating_income/revenue_sanitized×100, 1)`<br>`cagr_3yr` = AS-IS-136（本表参照）<br>`operating_income` = SEC EDGAR一次データ（カタログ対象外） | AS-IS-136（本表参照）＋ operating_income(SEC EDGAR、カタログ対象外) | 導出データ |
| AS-IS-151 | STONKS SILO | revenue_outlier_years | `revenue_outlier_years` | `[yr for yr in years if revenue_is_outlier[yr]]`。`revenue_is_outlier`はAS-IS-129の2パス外れ値検出（`revenue_sanitized`と表裏の関係） | AS-IS-129（既定義・一次データ） | 導出データ |
| AS-IS-152 | STONKS SILO | revenue_growth_pct | `revenue_growth_pct` | `revenue_growth_pct[yr] = (revenue_sanitized[yr]/revenue_sanitized[yr-1]-1)×100`（年次。前年が0以下または存在しない場合はNone） | AS-IS-129（既定義・一次データ） | 導出データ |
| AS-IS-161 | STONKS SILO | ocf_trend | `_ocf_trend()` | `ocf_yoy[yr] = ocf_annual[yr]-ocf_annual[yr-1]`（**差分**、比率ではない）<br>`ocf_accel[yr] = ocf_yoy[yr]-ocf_yoy[yr-1]`（2階差分）<br>判定: 最新年ocf_yoy<=0→(ocf_annual>0なら"FLAT"、他"DETERIORATING")／ocf_yoy>0かつocf_accel>0→"ACCELERATING"／直近2年ともocf_yoy>0→"IMPROVING"／他→"FLAT" | AS-IS-156（既定義・前フェーズ） | 導出データ |
| AS-IS-165 | STONKS SILO | discontinuous_growth | `discontinuous_growth` | 直近年revenue_sanitized YoY(`latest_yoy`)が200%以上、かつ過去1〜4年前ペアの平均YoYの3倍超の場合に`True`。黒字化予測でOLS回帰を使った場合（`ols_used`）のみ判定対象 | AS-IS-129（既定義、revenue_sanitized経由） | 導出データ |
| AS-IS-166 | STONKS SILO | discontinuous_growth_note | `discontinuous_growth_note` | AS-IS-165が`True`の場合のみ`"直近売上が急拡大（+{latest_yoy:.0f}%）、予測精度が低下している可能性があります"`を設定 | AS-IS-165（本表参照） | 導出データ |
| AS-IS-167 | STONKS SILO | incremental_margin | `incremental_margin` | `(gross_profit[yr]-gross_profit[yr-1]) / (revenue_sanitized[yr]-revenue_sanitized[yr-1]) × 100`（直近の年ペア。`prev_rev<latest_rev×10%`の年はスキップ、`rev_delta<=0`もスキップ） | AS-IS-129（既定義）＋ gross_profit(SEC EDGAR、カタログ対象外) | 導出データ |
| AS-IS-168 | STONKS SILO | incremental_margin_prev | `incremental_margin_prev` | AS-IS-167と同一計算式の「1つ前の年ペア」版 | AS-IS-167（本表参照） | 導出データ |
| AS-IS-169 | STONKS SILO | incremental_margin_trend | `incremental_margin_trend` | 全年ペアの増分粗利率系列にOLS単回帰（x=年次インデックス、y=増分粗利率%）。傾き`>5`→"IMPROVING"、`<-5`→"DETERIORATING"、他→"FLAT" | AS-IS-167/168（本表参照） | 導出データ |
| AS-IS-170 | STONKS SILO | incremental_rev_delta/incremental_gp_delta | `incremental_rev_delta`/`incremental_gp_delta` | `incremental_rev_delta=revenue_sanitized[yr]-revenue_sanitized[yr-1]`、`incremental_gp_delta=gross_profit[yr]-gross_profit[yr-1]`（AS-IS-167計算過程の分子・分母実額） | AS-IS-167と同じ | 導出データ |
| AS-IS-171 | STONKS SILO | reproduction_score | `reproduction_score` | `incremental_margin`水準の基礎スコア（`>=70→4,>=50→3,>=30→2,>=0→1,else→0`）に`incremental_margin_trend=="IMPROVING"`なら`+0.5`を加算し`min(4,...)`でキャップ | AS-IS-167, AS-IS-169（本表参照） | 導出データ |
| AS-IS-172 | STONKS SILO | reproduction_label | `reproduction_label` | `reproduction_score`のしきい値による5段階ラベル（`>=3.5`"極めて強い拡大再生産"〜`else`"拡大再生産なし"。年ペアが1件も取れない場合は"データ不足"） | AS-IS-171（本表参照） | 導出データ |
| AS-IS-174 | STONKS SILO | fields.{name}.yoy/qoq.change_pct/val_latest/val_prev/end_latest/end_prev/fp | `_calc_yoy_change()`/`_calc_qoq_change()` | `yoy: change_pct=(val_latest-val_prev)/abs(val_prev)×100`（同一fp=Q1〜Q4同士の前年比較）<br>`qoq: change_pct=(val_latest-val_prev)/abs(val_prev)×100`（直近四半期と前四半期の比較）<br>`val_latest`/`val_prev` = 対象フィールド（Revenue/GrossProfit/OperatingIncome/RD/NetIncome/OCF/CapEx）のnormalized四半期値（Q4 implied計算含む、SEC EDGAR、カタログ対象外） | SEC EDGAR（common/sec_data正規化JSON、カタログ対象外） | 導出データ |
| AS-IS-175 | STONKS SILO | fields.{name}.yoy/qoq.percentile | `_calc_percentile()` | AS-IS-135と同一の`_calc_percentile()`（同時点の全STONKS SILO銘柄の当該フィールドchange_pct分布内での順位、0-100） | AS-IS-174（本表参照） | 導出データ |
| AS-IS-176 | STONKS SILO | fields.{name}.yoy/qoq.angle,length | `_pct_to_angle()`/`_pct_to_length()` | AS-IS-135と同一の変換式（AS-IS-175のpercentileから変換） | AS-IS-175（本表参照） | 導出データ |
| AS-IS-177 | STONKS SILO | fields.{name}.series_q（四半期時系列） | `compute_vectors()`内`series_q` | `base_end`（全対象フィールド中の最新end日の最大値）以下の直近8四半期分の`{end,fp,val}`をそのまま格納（計算なし、表示用時系列） | SEC EDGAR（common/sec_data正規化JSON、カタログ対象外） | 導出データ |

### 分解の過程で新たに気づいた問題

- **AS-IS-068（FCF CAGR(3yr)）: CAGR経過年数未補正の確定バグ（最重要）**:
  `valid = fcf_history.filter(fcf!=null && fcf>0)`はゼロ・マイナスFCFの
  年を除外した**フィルタ後**配列であり、`valid[-4]`と`valid[-1]`の間に
  除外年が挟まっていた場合、実際の経過年数は3年より多くなる（例:
  5年分のうち1年がFCF赤字で除外されていれば実質4年差）。にもかかわらず
  指数は`1/3`に固定されており、経過年数の実測値（`valid[-1].year -
  valid[-4].year`）を一切使っていない。表示ラベルは常に「CAGR(3yr)」だが、
  除外年がある銘柄では実際より長い期間の変化率を3年複利換算したかのように
  誤表示する。同種のSTONKS SILO側`cagr_3yr`（AS-IS-136）は`years`配列
  自体が連続した年次リスト（フィルタなし）のため、この問題は生じない。
- **AS-IS-076とAS-IS-087は同名「200MA乖離」だが完全に別のデータソース・
  計算方法**: AS-IS-087はHypeCoreが独自にyfinance `history()`で取得した
  日次終値から`rolling(200).mean()`で自前計算するのに対し、AS-IS-076は
  yfinanceが内部で計算済みの`twoHundredDayAverage`（算出方法・対象期間が
  非公開のブラックボックス値）をそのまま使う。同じ概念・同じ変数名
  （`ma200_dev`）でありながら両者が一致する保証はない。
- **ma200_momがステージ判定の複数の重要分岐で使われるがJSON未出力**:
  `ma200_mom = ma200_dev.diff(3)`は`determine_stage()`のS3→S4遷移判定
  （例: `prev_stage in (3,4) and s3_streak>=2 and from_peak<-28 and
  rsi<47`に隣接する分岐）や`detect_substage()`のS4底打ち判定
  （`ma200_shrinking = ma200_mom>-5`）で使われるにもかかわらず、
  `run_poc()`のJSON出力には一切含まれていない。ステージ判定の根拠を
  事後的に検証・監査しようとしても、この中間変数だけは出力データから
  再現できない。
- **rev_yoy（TTM）とni_yoy/op_margin（単一四半期）の時間粒度混在**:
  AS-IS-093の`rev_yoy`は`Revenue.rolling(4).sum()`によるTTM同士のYoYだが、
  AS-IS-094の`ni_yoy`は`NetIncome.pct_change(4)`という**単一四半期**の
  前年同期比であり、TTMではない。AS-IS-095の`rule40 = rev_yoy + op_margin`
  も、TTMベースの`rev_yoy`と単一四半期ベースの`op_margin`（`NetIncome/
  Revenue`、四半期値同士）を単純加算しており、分子・分母の期間ベースが
  そもそも揃っていない。
- **「Rule of 40」がHypeCoreとSTONKS SILOで別定義であるだけでなく、
  STONKS SILO側はコード内コメントと実装自体が食い違っている**:
  HypeCoreの`rule40`（AS-IS-095）はTTM売上YoY+四半期営業利益率。
  STONKS SILOの`rule_of_40`（AS-IS-143）は3年CAGR（AS-IS-136）+
  営業利益率。既存のOUTPUT_ITEMS_INVENTORY.mdの注記通り両者は別式だが、
  加えて`DeficitQuality`データクラスの`rule_of_40`フィールドには
  `# 売上成長率 + 営業利益率`というコメントが付いている一方、実装は
  単年成長率ではなく3年CAGRを使っており、**コード内コメント自体が
  実装と矛盾している**。
- **real_strong判定がPython（サーバー側）とJS（クライアント側）で
  別々に実装され、条件・閾値が異なる**: `detect_substage()`
  （AS-IS-109〜112の計算元）の`real_strong`は
  `(rev_yoy>15 and eps_surprise>-5超) or (eps_surprise>0 and rev_yoy>0)
  or (rev_yoy>30 and eps_surprise>-30超)`という複数条件のORで構成される。
  一方、detail.htmlのクライアント側`getRec()`関数は
  `real_strong=(rev_yoy>30)&&(eps_surprise>0)`という「ANDのみ・閾値も
  別」の簡略版を独自に再実装している。`getRec()`自体は信頼性・品質判定系
  （本フェーズ対象外）の推奨表示に使われるが、同じ「実体が強いか」という
  概念を判定するのに、JSON生成時とクライアント表示時で別ロジックが
  走っており、同一銘柄・同一月でもサーバーの`substage`とクライアントの
  推奨表示が矛盾する組み合わせ（例: substageは「実体崩壊中」なのに
  getRecは「底打ち兆候」）が起こり得る。
- **AS-IS-091（volume_ratio）とAS-IS-092（vol_surge）は「出来高急増」系
  指標として並存するが時間粒度が異なる**: AS-IS-091は日次出来高の20日
  平均比（月末値のみ保持）、AS-IS-092は月次出来高の6ヶ月移動平均比。
  どちらも「出来高の急増」を表す名称・目的だが、算出する時間窓が
  全く異なる別指標である。
- **AS-IS-135/175/176（financial_vectors）のpercentile・angle・lengthは
  絶対的な変化率ではなく、同時点の全STONKS SILO銘柄集合に対する相対順位**:
  新規銘柄の追加・除外のたびに、対象銘柄自身のデータが変わっていなくても
  他銘柄のpercentileが変動しうる。過去のresults.json保存値と時系列比較
  する際はこの母集団変動の影響を考慮する必要がある。
- **AS-IS-119（ライフサイクル）のフォールバック元`revenue_growth`
  （yfinance、小数）と`rev_yoy`（AS-IS-093、SEC EDGAR TTM%）は算出基準が
  異なる別の指標**であり、どちらが使われるかは単に
  `revenue_growth`がnullかどうかで決まる。銘柄によって暗黙に異なる基準で
  ライフサイクル判定される。detail.html/index.htmlの重複実装自体は
  完全に同一ロジックのコードコピーであり値の不整合は生じないが、
  保守時に片方だけ修正されるリスクがある。
- **AS-IS-077/AS-IS-079は既に「削除候補」とマークされた重複カタログ
  エントリであることを実コードで確認した**: 前者はAS-IS-086（stage_label）
  の、後者はAS-IS-152（revenue_growth_pct）の単純な他サブシステム参照
  （移送）であり、独立した計算ロジックを持たない。

**依頼文で例示された問題のうち、本バッチでは直接該当が見つからなかったもの**:
「Bear/Bull成長率の符号未考慮」「growth_floor根拠不明」は、コード上
`bear_multiplier`・`fcf_growth_floor`/`fcf_growth_cap`がいずれも
`core_calculator.py`（DCF/WACC構成要素系、未着手フェーズ）側にのみ存在し、
成長率・トレンド系43件のいずれの計算にも直接関与していないことを確認した。
該当する可能性がある場合はDCF/WACC構成要素系フェーズで確認する。

### 次フェーズへの申し送り

- 本フェーズで引用のみ行い内部アルゴリズムを再展開しなかったAS-IS-ID:
  AS-IS-084・AS-IS-100相当・AS-IS-116（評価倍率フェーズで参照済み）、
  AS-IS-047・AS-IS-129・AS-IS-156（前フェーズ既定義/参照済み）、
  カタリスト・イベント予測系の`sell_on_good_news`/`eps_surprise`/
  `analyst_upgrade_rate`/`buy_hold_ratio`（未定義）
- HypeCoreの`determine_stage()`/`detect_substage()`は140行超のルール
  ベース分岐を持つため、本フェーズでは主要な入力変数とロジック構造の
  紐付けに留め、全ての閾値分岐を逐一書き出してはいない。詳細は
  `src/value/hypecore/hypecore.py`の該当関数を参照
- AS-IS-068のCAGR経過年数未補正、AS-IS-109〜112のreal_strong Python/JS
  二重実装、AS-IS-143のコメント/実装不一致はいずれも実装（コード修正）を
  伴うため、本タスクの範囲外として記録にとどめた

---

## 対象6（フェーズ6）: 導出データ — DCF/WACC構成要素系（45件）

出発点: `DERIVED_DATA_SUBCATEGORIES.md`「DCF/WACC構成要素系（45件）」
（ステップ6確定後392件ベース。TANUKI VALUATION 28件: AS-IS-001/007/008/
009/010/011/012/013/014/015/016/017/018/019/020/021/022/023/024/025/027/
029/030/059/064/065/066/067。TANUKI TAIL 17件: AS-IS-442/443/444/445/446/
448/449/450/451/492/493/494/495/496/497/498/509）

本サブカテゴリは、既に定義済みの評価倍率系（AS-IS-002〜006等、フェーズ3）
・キャッシュフロー収益性系（フェーズ4）から`base_fcf`（AS-IS-019）・
`growth.rate`（AS-IS-012）・`wacc.value`（AS-IS-013）・`RPO_PV`
（AS-IS-024）・`GrowthOption_PV`（AS-IS-016）・`net_cash`（AS-IS-025）
として繰り返し引用されてきた中核部分であり、本フェーズで初めて内部
アルゴリズムまで完全に展開する。実装（コード修正）は行っていない。
定義の記録のみ。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義（最小単位まで分解した計算式） | データ取得元（最終的にたどり着く一次データ等のAS-IS-ID一覧） | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-001 | TANUKI VALUATION | 理論株価（メイン、Rmβなし基準） | `intrinsic_value_per_share` | フェーズ3でAS-IS-006（乖離率）の分母として既に完全分解済み: `intrinsic_value_per_share = V0_rm/diluted_shares + RPO_PV/diluted_shares + GrowthOption_PV/diluted_shares + net_cash_per_share`。`V0_rm`はbase_fcf（AS-IS-019、本表）を高成長率（AS-IS-012、本表）で成長させた将来FCFを割引率=market_return（AS-IS-013の一部、本表、10%固定）で現在価値化した合計 | AS-IS-019, AS-IS-012, AS-IS-013, AS-IS-024, AS-IS-016, AS-IS-025（すべて本表で完全分解） | 導出データ |
| AS-IS-007 | TANUKI VALUATION | v0（DCF現在価値合計） | `v0` | 2/3段階/線形逓減DCF（`maturity_config`判定）でbase_fcfを高成長率（AS-IS-012）で成長させた将来FCF列を、割引率=**WACC_β（AS-IS-013のβ込みCAPM値、Rmβなしではない）**で現在価値化した合計。`calculate_two_stage_dcf`/`calculate_three_stage_dcf`/`calculate_tapering_dcf`（`calculator/dcf.py`）が実装 | AS-IS-019, AS-IS-012, AS-IS-013（本表） | 導出データ |
| AS-IS-008 | TANUKI VALUATION | v0_adjusted | `v0_adjusted` | `calculate_intrinsic_value()`内で`v0_adjusted = v0`（`adjustments.py:647`のコメント「RPO加算前（後方互換のため戻り値として維持）」の通り、**常にAS-IS-007と完全に同一の値**。実質的な「調整」は行われていない） | AS-IS-007（本表、常に同値） | 導出データ |
| AS-IS-009 | TANUKI VALUATION | alpha / alpha_was_capped | `alpha` / `alpha_was_capped` | `calculate_alpha(roe=roe_avg, wacc=Rm, retention_rate=0.60, alpha_cap=業種/セクター別上限)`で計算される実際の値がそのまま格納される。`g_individual=max(0,roe×0.60)`、`alpha_raw=(g_individual/Rm)×discount_factor(0.7固定)`、`alpha=min(alpha_cap, max(0,alpha_raw))`、`alpha_was_capped=(alpha_raw>alpha_cap)`。**ただしP_t/IV計算では`alpha=0.0`固定（ALPHA-REDESIGN-1）が使われるため、この`alpha`フィールドはIV計算に反映されない参考値専用**（CLAUDE_CODE_START.mdに既記載の設計） | roe_10yr_avg（カタログ対象外）＋ AS-IS-013のmarket_return要素（本表） | 導出データ |
| AS-IS-010 | TANUKI VALUATION | future_values（1〜5年後理論株価） | `future_values` | `calculate_future_values()`: 年ごとに`value *= (1+g)`を反復適用。`g = high_growth_rate（AS-IS-012）`が高成長期間内（Moat Score連動、AS-IS-026経由・フェーズ4既定義参照）、それ以降は`terminal_growth`（AS-IS-059、本表）。起点値は`scenario_valuations.base.intrinsic_value_per_share`（AS-IS-015、本表）優先、なければAS-IS-001 | AS-IS-012, AS-IS-015, AS-IS-059（本表） | 導出データ |
| AS-IS-011 | TANUKI VALUATION | return_metrics（期待リターン指標） | `return_metrics` | `calculate_return_metrics()`: 各期間について`value_growth_pct=(future_value/current_value-1)×100`、`expected_return_pct=(future_value/current_price-1)×100`。`current_value`=AS-IS-010起点値、`future_value`=AS-IS-010各年値、`current_price`はyfinance（カタログ対象外） | AS-IS-010（本表）＋ current_price（yfinance、カタログ対象外） | 導出データ |
| AS-IS-012 | TANUKI VALUATION | growth.rate/source（高成長率決定） | `determine_growth_rate()` | 優先順位: ①セグメント加重成長率（`get_segment_growth()`: `weighted_growth=Σ(segment.weight×segment.growth)`、`config/segment_config.json`の`segments`辞書。admin.html経由の手動入力相当、カタログ対象外）②FCF CAGR（`calculate_fcf_cagr()`: 直近5年の正のFCFのみ対象、`raw_cagr=(直近/最古)^(1/periods)-1`を`[growth_floor=0.15, growth_cap=0.50]`にクリップ。**両閾値ともコード内に根拠コメントなし**、下記備考）③デフォルト25%固定 | fcf_list_raw（AS-IS-019由来、カタログ対象外）＋ segment_config.json（手動入力相当、カタログ対象外） | 導出データ |
| AS-IS-013 | TANUKI VALUATION | wacc.value/beta/risk_free_rate/market_return | `calculate_wacc()` | `WACC = risk_free_rate + beta × (market_return - risk_free_rate)`（CAPM）、`max(0.06, min(0.25, WACC))`にクリップ<br>`risk_free_rate=4.3%固定`（10年国債利回り、根拠コメントあり）<br>`market_return=10%固定`（**根拠コメントなし、下記備考**）<br>`beta`決定は2段階: (1)月次GitHub Actions（`Beta_Config_Update.yml`、毎月第1日曜JST8時）が`beta_fetcher.py`を実行し、yfinance 5年β取得→`max(0.3,min(2.5,raw_beta))`で`config/beta_config.json`のoverrides欄に書込（Damodaran手動設定銘柄・0.3〜2.5範囲外は個別対応）。(2)実行時、`data_fetcher.py:_determine_beta()`が優先順位: ①`beta_config.json`のoverride（無条件採用、再検証なし）②yfinance直接値（0.1〜3.0の範囲内のみ採用）③セクター別デフォルト④全体デフォルト1.0。**β=0/負値の無条件フォールバック、下記備考** | risk_free_rate/market_return(コード内定数)＋ yfinance beta(カタログ対象外)＋ beta_config.json(手動設定、カタログ対象外) | 導出データ |
| AS-IS-014 | TANUKI VALUATION | sensitivity.matrix/wacc_values/growth_years | `calculate_sensitivity_matrix()` | WACC±1%（3値）× 高成長期間（base_years中心に3値、base_years=AS-IS-026のPhase1年数）の3×3マトリクス。各セルは`create_sensitivity_calc_func()`が生成する`calc_func(wacc,years)`で計算（two_stage/three_stage DCFを切替、tapering DCFは非対応）。`P_t=v0×(1+alpha)+rpo_pv`（alpha=0固定、rpo_pv=AS-IS-024+AS-IS-016合算） | AS-IS-019, AS-IS-013, AS-IS-024, AS-IS-016（本表） | 導出データ |
| AS-IS-015 | TANUKI VALUATION | scenario_valuations.bear/base/bull | `calculate_scenario_valuations()` | `bear_rate=base_growth_rate×0.7`、`base_rate=base_growth_rate`、`bull_rate=base_growth_rate×1.2`（`base_growth_rate`=AS-IS-012）。各成長率で`create_scenario_calc_func()`がDCF（tapering/three_stage/two_stageを切替）を再計算し1株あたり価値を算出。**base_growth_rateが負の場合、Bear/Bullの符号が意図と逆転する構造的欠陥あり（下記備考、最重要）** | AS-IS-012, AS-IS-019, AS-IS-013, AS-IS-024, AS-IS-016（本表） | 導出データ |
| AS-IS-016 | TANUKI VALUATION | growth_options.total_pv/count/options | `calculate_growth_option_total_pv()` | `expected_fcf = tam × penetration × fcf_margin × probability`<br>`pv = expected_fcf / (1+discount_rate)^delay_years`<br>`total_pv = Σ(pv)`。`tam`/`penetration`/`fcf_margin`/`probability`/`discount_rate`/`delay_years`は全て`config/growth_options_config.json`のticker別手動設定値（admin.html経由） | growth_options_config.json（手動入力相当、カタログ対象外） | 導出データ |
| AS-IS-017 | TANUKI VALUATION | maturity_profile | `get_maturity_profile()` | `config/maturity_config.json`のticker別設定（`type`: two_stage/three_stage、`phase1.years`/`phase1.growth`〈null時はAS-IS-012流用〉、`phase2.years`/`phase2.growth`、`terminal_growth`）。admin.html経由の手動設定 | maturity_config.json（手動入力相当、カタログ対象外） | 導出データ |
| AS-IS-018 | TANUKI VALUATION | dcf_components.*（v0/pv_high_growth/pv_terminal/high_growth_detail/terminal_fcf/terminal_value/v0_rm/pv_fcf_rm/pv_tv_rm/pv_phase1_rm/pv_phase2_rm） | `dcf_result.to_dict()` 等 | `DCFResult`/`ThreeStageDCFResult`（`calculator/dcf.py`、フェーズ3で式決定済み）の全フィールドをそのまま格納したバンドル。`v0`はAS-IS-007と同値。`_rm`サフィックス系（`v0_rm`/`pv_fcf_rm`/`pv_tv_rm`）はmarket_return基準（AS-IS-001のV0_rmと同一）で別途計算した参考値 | AS-IS-007（本表）＋ AS-IS-001のV0_rm系（本表） | 導出データ |
| AS-IS-019 | TANUKI VALUATION | fcf_base.base_fcf/method/cv | `determine_fcf_base()` | CV（変動係数=std/\|mean\|）方式で自動選択。特殊ケース優先順: (1)データ3年未満→recent_2yr保守フォールバック (2)直近2年平均≤0または直近1年マイナス→avg_5yr (3)直近2年平均が5年平均の15%未満→avg_5yr (4)5年平均≤0→recent_2yr (5)5年CAGRが-5%未満かつ回復傾向なし→recent_1yr、回復傾向あり→avg_5yr_recovery (6)`CV≤0.5`→avg_5yr（成熟企業）、`CV>0.5`→recent_2yr（成長企業）。`fcf_5yr_avg`/`fcf_2yr_avg`/`fcf_list`はSEC EDGAR annual_*.jsonの`cf.free_cash_flow`（AS-IS-047と同一データ、フェーズ4既定義参照） | AS-IS-047（既定義・フェーズ4） | 導出データ |
| AS-IS-020 | TANUKI VALUATION | fcf_outlier.detected/rule/action/note/deviation_pct | `analyze_fcf_outlier()` | ルール判定: 直近FCF<0→`latest_negative`（閾値なし）／5年平均からの乖離が閾値超（CV≤0.5なら±20%、CV>0.5なら±60%）→`deviation_large`。EPSアナライザーの`adjusted_eps_analyzer`annual.jsonから「一過性費用」カテゴリ（リストラ・在庫サプライチェーン・金融関連）を突合し、`transient_total≥閾値`なら`action="excluded"`（5年平均採用）、そうでなければ`action="flagged"`。**上方乖離（latest>5yr_avg）は一過性コストで除外しない**（FCF-OUTLIER-1、既知設計） | AS-IS-019（本表）＋ EPS Analyzerのadjustments（信頼性・品質判定系AS-IS-268/269、未定義） | 導出データ |
| AS-IS-021 | TANUKI VALUATION | fcf_estimation.applied/conversion_rate/estimated_fcf等 | `estimate_fcf_from_eps()` | `estimated_fcf = adj_net_income × conversion_rate`。`conversion_rate`は`fcf_conversion_config.json`のticker別override＞保険/金融業種は1.0固定＞セクター別レートの優先順。`adj_net_income`はEPSアナライザーannual.jsonの直近年`adjusted_net_income`から「買収・統合関連」加算を条件付き控除（`pre_deduction_dr>1.0`の場合のみ控除、循環参照回避のため控除前drで判定）。スキップ条件: FCF外れ値`excluded`済み（保険/金融除く）／生FCF安定（CV<0.3）かつ外れ値未検出（ticker_overrides対象は除く）／調整済み純利益≤0 | AS-IS-019, AS-IS-020（本表）＋ EPS Analyzerのadjusted_net_income（CF収益性系AS-IS-267、既定義・フェーズ4） | 導出データ |
| AS-IS-022 | TANUKI VALUATION | software_system_reclassification.* | `check_software_system_reclassification()` | `realized_ratio = mean(生FCF/調整済み純利益)`（黒字年のみ、直近5年）。現分類のレート（Mature=1.00/SaaS=1.61固定）から30%以上乖離し、かつもう一方のレートの方が実測値に近い場合のみ見直しを推奨（config書き換えは行わず、その実行限りの差替え） | AS-IS-021（本表）＋ AS-IS-047（既定義・フェーズ4） | 導出データ |
| AS-IS-023 | TANUKI VALUATION | rd_capitalization.* | `capitalize_rd()` | `capitalized_rd = rd_current`（当年R&D全額を資本計上）、`amortization_current = mean(過去3年R&D、現年の3倍超は外れ値除外)`、`rd_adjustment = capitalized_rd - amortization_current`（FCFへの調整額）。適用条件: R&D/Revenue≥5%かつ過去2年以上のR&Dデータあり | R&D/Revenue（SEC EDGAR annual_*.json、カタログ対象外） | 導出データ |
| AS-IS-024 | TANUKI VALUATION | rpo_adjustment.rpo_pv/application_rate/sector_category/rpo_incremental等 | `adjust_rpo()` | `rpo_incremental`: 前年同期RPO・Revenue成長率が判明→`max(0, rpo-rpo_yago×(1+rev_yoy))`／不明ならTTM Revenue代用→`max(0, rpo-rev_ttm×1.0)`／両方不明→0<br>`rpo_pv = rpo_incremental × application_rate × op_margin / (1+15%)^1.5年`（`op_margin≤0`ならrpo_pv=0）<br>`application_rate`: `config/rpo_config.json`のwhitelist登録済み銘柄は100%（比率ゲート免除）、保険0%、Fintech(Financial Services)50%、industry keywordでSaaS判定なら100%、セクター別テーブル参照<br>非whitelistは`rpo/rev_ttm<30%`で不適用（**rev_ttmがNoneの場合この安全弁ゲート自体がスキップされる、下記備考**） | rpo/op_margin/rpo_yago/rev_yoy/rev_ttm（SECReader経由、カタログ対象外）＋ rpo_config.json（手動設定、カタログ対象外） | 導出データ |
| AS-IS-025 | TANUKI VALUATION | bs_adjustment.net_cash/net_cash_per_share/sector_guard | `calculate_bs_adjustment()` | `net_cash_per_share = net_cash / diluted_shares`（`diluted_shares>0`かつ`available`の場合のみ）。`net_cash`自体は`SECReader.get_net_cash()`（本タスク対象外ファイル）が算出するSEC EDGARベース値（cash+ST投資-LT債務-ST債務、セクターガード〈保険/fintech特殊処理〉・複数タグフォールバック補完あり） | SECReader.get_net_cash()（common/sec_data、カタログ対象外） | 導出データ |
| AS-IS-027 | TANUKI VALUATION | rice.q/cf_conversion/q_years/cf_years/avg_intensity/avg_rev_growth/vc_factor/bear・base・bull | `calculate_rice()` | `RICE = (G × VC_Factor × Q × CF) / WACC`<br>`Q = mean(OCF/(NI+SBC))`直近3年（GAAP赤字年・利益ほぼゼロの年は除外、SBCは非現金費用の補正として純利益に足し戻す）<br>`CF = mean(売上成長率(t+1)/投資強度(t))`1年ラグ直近3点（投資強度=(\|CapEx\|+\|R&D\|+\|S&M\|)/Revenue、CF点は±10にクリップ）<br>`CF_adj`はCapExのみの投資強度版<br>`VC_Factor = clamp(roic_wacc_ratio, 0.3, 2.0)`（`roic_wacc_ratio`はAS-IS-026のmoat_score計算で使うROIC値と同一算出、フェーズ4既定義参照）<br>`G`=AS-IS-015の各シナリオgrowth_rate、`WACC`=market_return(10%固定)<br>`rice = (G×VC×Q×CF)/WACC`、`rice_adj = (G×VC×Q×CF_adj)/WACC`（**`cf_adj≤0`の場合のみ0.0にフォールバックする条件があり、mainのrice側には同等のcf≤0ガードがない非対称設計、下記備考RICE_adj非対称ゼロ化**） | AS-IS-015（本表）＋ SEC EDGAR annual_*.json（カタログ対象外）＋ roic_wacc_ratio（AS-IS-026関連、カタログ対象外） | 導出データ |
| AS-IS-029 | TANUKI VALUATION | pv_high / pv_terminal（components内） | `components.pv_high`/`components.pv_terminal` | AS-IS-018の`pv_high_growth`/`pv_terminal`と完全に同一の値を`components`辞書に再格納しただけの重複フィールド | AS-IS-018（本表、完全重複） | 導出データ |
| AS-IS-030 | TANUKI VALUATION | alpha_uncapped（components内） | `components.alpha_uncapped` | `alpha_result.alpha_uncapped = max(0.0, alpha_raw)`（AS-IS-009のcap適用前の値）。AS-IS-009の一部を再掲したもの | AS-IS-009（本表） | 導出データ |
| AS-IS-059 | TANUKI VALUATION | terminal_growthの出所 | `get_terminal_growth()` | 優先順位: ①`maturity_config.json`のticker個別`terminal_growth`が**デフォルト3.0%と1e-5超の差**を持つ場合はそれを採用（**3.0%ちょうどを明示設定したい場合は区別できずセクター別フォールバックに流れる、下記備考**）②`growth_sanity.TICKER_INDUSTRY_OVERRIDES`経由でDamodaran業種別テーブル（長期GDP成長率+セクター構造成長プレミアム、2.0%〜3.5%）を参照③デフォルト3.0%固定 | maturity_config.json（手動設定、カタログ対象外）＋ growth_sanity.TICKER_INDUSTRY_OVERRIDES（カタログ対象外） | 導出データ |
| AS-IS-064 | TANUKI VALUATION | 将来価値予測（シナリオ別テーブル、stock.html独自計算） | `projectFuture()` | クライアント側`projectFuture(baseVal, growthRate)`が`v×=(1+g)`を反復（`g`は高成長期間内`sc.rate`〈シナリオ別成長率、AS-IS-015〉・以降`terminalGrowth`）。**バックエンドのAS-IS-010〈future_values〉は不使用**、シナリオ数（bear/base/bullの有無）・年数（`Object.keys(futureVals).length`からの逆算）のみJSONを参照し、値自体は完全に独自再計算 | AS-IS-015（本表）＋ AS-IS-010（本表、年数構造の参照のみ） | 導出データ |
| AS-IS-065 | TANUKI VALUATION | 5年BASE年率換算リターン（stock.html独自計算） | `annRate` | `annRate = (fv5/currentPrice)^0.2 - 1`（`fv5`=AS-IS-011の`return_metrics["5年後"].future_value`、`0.2=1/5`固定指数） | AS-IS-011（本表）＋ current_price（yfinance、カタログ対象外） | 導出データ |
| AS-IS-066 | TANUKI VALUATION | 感応度分析（独自5×5マトリクス、stock.html独自計算） | `calcSensIV()` | クライアント側で`base_fcf`（AS-IS-019）を**常に2段階DCFのみ**で再計算する独自5×5マトリクス（WACC5値×成長率オフセット5値）。`iv=(pv+tvPv)/shares+bsps`。**バックエンドのAS-IS-014〈sensitivity.matrix、3×3、DCFタイプ切替あり〉とは別に、同一ページ内に完全に独立実装として並存**（下記備考、最重要級）。`const alpha=d.alpha??1.0`は宣言されるが式中で未使用（死コード） | AS-IS-019, AS-IS-014（本表、後者とは別実装で並存） | 導出データ |
| AS-IS-067 | TANUKI VALUATION | Reverse DCF（市場vs DCF乖離分析、stock.html独自計算） | render内IIFE | 表示条件: `(base_iv-currentPrice)/currentPrice < -50%`（DCF価値が市場価格より50%超低い場合のみ）。`EV = currentPrice×diluted_shares + net_debt`（AS-IS-045、既定義・フェーズ4）<br>`fcfTerm = EV×(Rm-g_TV)/(1+g_TV)`（Rm=AS-IS-013のmarket_return、g_TV=AS-IS-059）<br>`reqGr = (fcfTerm/fcfCur)^(1/5) - 1`（fcfCur=AS-IS-019のbase_fcf） | AS-IS-045（既定義・フェーズ4）＋ AS-IS-013, AS-IS-059, AS-IS-019（本表） | 導出データ |
| AS-IS-442 | TANUKI TAIL | assumptions.Y1_growth/Y2_growth/Y3_growth | `tail_dcf_bridge.py:generate_scenario_files()` | `review["stage2"]["scenarios"][シナリオ].revenue_growth_y1/y2/y3`（AS-IS-492、本表）をそのまま`round(値,4)`で転記 | AS-IS-492（本表） | 導出データ |
| AS-IS-443 | TANUKI TAIL | assumptions.terminal_growth | 同上 | `review["stage2"]["scenarios"][シナリオ].terminal_growth`（AS-IS-493、本表）をそのまま転記 | AS-IS-493（本表） | 導出データ |
| AS-IS-444 | TANUKI TAIL | assumptions.operating_margin | 同上 | `review["stage2"]["scenarios"][シナリオ].operating_margin_terminal`（AS-IS-494、本表）をそのまま転記 | AS-IS-494（本表） | 導出データ |
| AS-IS-445 | TANUKI TAIL | assumptions.weighted_growth | `_weighted_growth()` | `weighted_growth = (Y1×3 + Y2×2 + Y3×1) / 6`（近い将来を重く見る加重平均。Y1/Y2/Y3=AS-IS-442） | AS-IS-442（本表） | 導出データ |
| AS-IS-446 | TANUKI TAIL | base_intrinsic_value | `generate_scenario_files()` | TANUKI VALUATIONの`latest.json`から`intrinsic_value_per_share`（AS-IS-001、本表）を読み取り`round(値,2)`で転記するだけの移送 | AS-IS-001（本表） | 導出データ |
| AS-IS-448 | TANUKI TAIL | future_values["1年後"] | `calculate_future_values()`（TANUKI VALUATIONの関数を直接import） | `current_value=base_intrinsic_value（AS-IS-446）`、`high_growth_rate=weighted_growth（AS-IS-445）`、`high_growth_years=3固定`、`terminal_growth=AS-IS-443`で計算した1年後値。**関数自体はAS-IS-010と共通（`future_values.py`を直接import）だが入力の成長率がTANUKI VALUATION本体〈AS-IS-012〉ではなくGrok生成の`weighted_growth`である点が異なる** | AS-IS-446, AS-IS-445, AS-IS-443（本表） | 導出データ |
| AS-IS-449 | TANUKI TAIL | future_values["3年後"] | 同上 | AS-IS-448と同一計算の3年目要素 | AS-IS-448と同じ | 導出データ |
| AS-IS-450 | TANUKI TAIL | future_values["5年後"] | 同上 | AS-IS-448と同一計算の5年目要素（`high_growth_years=3`のため4〜5年目は`terminal_growth`適用） | AS-IS-448と同じ | 導出データ |
| AS-IS-451 | TANUKI TAIL | kpi_forecasts["1年後"/"3年後"].{KPI名} | `generate_scenario_files()` | `review["stage2"]["scenarios"][シナリオ].kpi_forecasts`（AS-IS-496、本表）をそのまま転記するだけの移送 | AS-IS-496（本表） | 導出データ |
| AS-IS-492 | TANUKI TAIL | stage2.scenarios.{bear,base,bull}.revenue_growth_y1/y2/y3 | `build_stage2_prompt()`→Grok API | **決定論的な計算式は存在しない。AI（Grok）が下記プロンプト入力に基づき生成したJSON値**: 直近KPIテーブル・YoY・Stage1評価結果（health_score/concerns、信頼性・品質判定系AS-IS-482〜491・未定義）・営業利益率推移（4四半期連続改善なら現在値未満のシナリオを避けるよう指示）を渡し、bear/base/bull各シナリオの`revenue_growth_y1/y2/y3`を生成させる（下記備考、AI生成データの位置づけ） | Stage1評価結果（信頼性・品質判定系・未定義）＋ KPI実績（カタリスト・イベント予測系AS-IS-419〜423等・未定義）＋ 営業利益率推移（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-493 | TANUKI TAIL | stage2.scenarios.{...}.terminal_growth | 同上 | AS-IS-492と同一のAI生成JSON内のフィールド（プロンプト例では0.03〜0.035） | AS-IS-492と同じ | 導出データ |
| AS-IS-494 | TANUKI TAIL | stage2.scenarios.{...}.operating_margin_terminal | 同上 | AS-IS-492と同一のAI生成JSON内のフィールド | AS-IS-492と同じ | 導出データ |
| AS-IS-495 | TANUKI TAIL | stage2.scenarios.{...}.rationale | 同上 | AS-IS-492と同一のAI生成JSON内のフィールド（各シナリオの根拠を説明する自由記述文） | AS-IS-492と同じ | 導出データ |
| AS-IS-496 | TANUKI TAIL | stage2.scenarios.{...}.kpi_forecasts["1年後"/"3年後"][KPI名] | 同上 | AI生成。プロンプトはKPI現在値（layer2実績優先・なければlayer1財務指標）と各シナリオの成長率を踏まえた1年後・3年後予想値を指示するが、**実際の計算はAIの推論に委ねられ、コード側での検算・固定式適用は行われない** | AS-IS-492（同一AI応答内）＋ KPI現在値（カタリスト・イベント予測系・未定義） | 導出データ |
| AS-IS-497 | TANUKI TAIL | stage2.key_assumptions | 同上 | AI生成。全シナリオ共通の前提条件を箇条書きで生成させたリスト（決定論的な計算式なし） | AS-IS-492と同じプロンプト応答 | 導出データ |
| AS-IS-498 | TANUKI TAIL | stage2.risk_factors | 同上 | AI生成。リスク要因を箇条書きで生成させたリスト（決定論的な計算式なし） | AS-IS-492と同じプロンプト応答 | 導出データ |
| AS-IS-509 | TANUKI TAIL | scenario | `generate_scenario_files()` | `"scenario": sc_name`（"bear"/"base"/"bull"のいずれかのラベルをそのまま格納するだけのループ変数） | なし（ループ変数の転記） | 導出データ |

### 分解の過程で新たに気づいた問題

- **AS-IS-015（scenario_valuations）: Bear/Bull成長率の符号が負の成長率で
  意図と逆転する構造的欠陥（最重要）**: `calculate_scenario_valuations()`
  （`calculator/scenarios.py:64-66`）は`bear_rate=base_growth_rate×0.7`・
  `bull_rate=base_growth_rate×1.2`という単純な乗算で構成される。
  `base_growth_rate`が正の値である前提では「Bearは基準より控えめ・Bullは
  基準より強気」という意図通りに機能するが、**`base_growth_rate`が負の
  場合（例: -10%）はBear(-10%×0.7=-7%、実際は基準より緩やかな下落=
  楽観的)・Bull(-10%×1.2=-12%、実際は基準より急な下落=悲観的)と
  ラベルと実態が完全に逆転する**。現状の`determine_growth_rate()`
  （AS-IS-012）はFCF CAGRを`growth_floor=0.15`で下限クリップし、
  セグメント加重成長率も現状の`config/segment_config.json`には負値の
  設定例が存在しないため、本番データでは顕在化していないが、ロジック
  自体の欠陥は現在も残る。同一の乗算ロジックは`calculator/growth.py`の
  `get_scenario_growth_rates()`（未使用のデッドコード）・
  `segment_config.py`の`calculate_scenario_growth()`（同じく未使用の
  デッドコード、こちらは`max(0.0,min(0.50,...))`で追加クリップされる
  点のみ異なる）にも重複実装されている。
- **AS-IS-012: growth_floor(15%)・growth_cap(50%)の根拠が
  コード内に一切記載されていない**: `calculate_fcf_cagr()`の
  デフォルト引数として`growth_floor=0.15`・`growth_cap=0.50`が設定
  されているが、なぜ15%・50%なのかを説明するコメントが存在しない
  （`risk_free_rate=4.3%`には「10年国債利回り」という出典コメントが
  付いているのと対照的）。
- **AS-IS-013: market_return=10%固定の根拠もコード内に記載がない**:
  `risk_free_rate`同様「一般的な株式市場の長期平均リターン想定」と
  推測されるが、明示的な出典コメントはwacc.py内に存在しない。
- **AS-IS-013: β=0/負値がbeta_fetcher.py（月次更新）で無条件に
  フォールバックされ、かつdata_fetcher.py側で再検証されない**:
  `beta_fetcher.py:calc_capped_beta()`（`beta_fetcher.py:262-268`）は
  yfinanceから取得した生βが`None`かどうかのみをチェックし
  （`beta_fetcher.py:304`）、`0`や負値であっても`max(0.3,min(2.5,raw_beta))`
  で**無条件に0.3へフロアされ、beta_config.jsonに書き込まれる**。
  この値は本来のyfinanceデータ異常（一時的な取得エラー等でゼロ値が
  返る可能性）を示すシグナルかもしれないが、警告フラグは一切付与
  されない。さらに、実行時の`data_fetcher.py:_determine_beta()`は
  `beta_config.json`のoverrideを**最優先かつ無条件に採用**するため
  （`data_fetcher.py:841-848`）、このoverride経由のβに対しては
  `_determine_beta()`自身が持つ「yfinance直接値は0.1〜3.0の範囲内
  のみ採用」という健全性チェックが一切適用されない。加えて
  `beta_fetcher.py`の許容範囲（0.3〜2.5）と`_determine_beta()`の
  直接値許容範囲（0.1〜3.0）が異なる2つの基準として並存している。
- **AS-IS-024（RPO補正）: rev_ttm未提供時に比率安全弁がスキップされる**:
  `adjust_rpo()`の比率条件ゲート（`adjustments.py:525`
  `if not via_whitelist and rev_ttm is not None and rev_ttm > 0`）は、
  `rev_ttm`が`None`の場合**ゲート自体を素通り**する。`rpo_incremental`の
  計算（`adjustments.py:542-543`）は`rpo_yago`と`rev_yoy`さえあれば
  `rev_ttm`なしでも非ゼロ値を返せるため、「`rpo_yago`/`rev_yoy`は
  取得できたが`rev_ttm`だけがNone」という組み合わせでは、
  RPO/Revenue比率が閾値（30%）未満でもRPO補正が適用されてしまう
  可能性がある。
- **AS-IS-027（RICE）: rice_adjのみに0フロアガードがあり、mainのrice
  には対応するガードがない非対称設計**: `calculate_rice()`
  （`rice.py:440`）で`rice_adj_val = (...) if cf_adj > 0 and wacc > 0
  else 0.0`と明示的にゼロフロアされるのに対し、直上の`rice_val`
  （`rice.py:438`）には`cf`（本来のCF値）が負であっても同様のガードが
  なく、そのまま計算される。CF（投資再生産効率）が構造的に負値を
  取りうる銘柄では、`rice`は符号が反転した値をそのまま返すのに
  `rice_adj`だけが0にフォールバックするという不整合が生じる。
- **AS-IS-007（v0）とAS-IS-001（intrinsic_value_per_share）は別々の
  WACCで計算された別の値であり、latest.jsonのトップレベル`v0`
  フィールドはメイン理論株価の直接の計算根拠ではない**: `v0`
  （AS-IS-007）はSTEP1で計算されたβ込みCAPM WACCベースのDCF結果
  （`intrinsic_value_beta`＝AS-IS-002の計算根拠）であるのに対し、
  画面のメイン理論株価（AS-IS-001/AS-IS-006）は別途`_rm`（market_return
  10%固定、βなし）で再計算した`_v0_rm`（`dcf_components.v0_rm`に
  格納）を使う。latest.jsonを読む外部AIやレビュアーが「v0からIVを
  積み上げ検算」しようとすると、トップレベルの`v0`ではなく
  `dcf_components.v0_rm`を使わなければ整合しない、という罠になりうる
  （CLAUDE_CODE_START.mdの`REPORT-ALPHA-STALE-1`と同種の「表示順序と
  実際の計算根拠の不一致」パターン）。
- **AS-IS-008（v0_adjusted）はAS-IS-007と常に完全に同一の値を返す
  実質的な死フィールド**: `calculate_intrinsic_value()`内で
  `v0_adjusted = v0`（`adjustments.py:647`）という代入のみで、
  変数名が示唆する「調整」は一切行われない。コメント自体が
  「後方互換のため戻り値として維持」と明記しており、意図的な
  後方互換用の重複フィールドである。
- **AS-IS-066: バックエンドのAS-IS-014（sensitivity.matrix、3×3、
  DCFタイプに応じてtwo_stage/three_stageを切替）とは別に、stock.html
  上に完全に独立したクライアント側5×5感応度マトリクス
  （`calcSensIV()`）が同一ページに並存する**: `calcSensIV()`は
  **常に2段階DCFのみ**で再計算するため、three_stage DCF
  （`maturity_config.json`でtype="three_stage"設定済みの銘柄）や
  tapering DCF（高成長銘柄向け線形逓減）を採用している銘柄では、
  同じページ内の2つの「感応度分析」セクションが異なる計算式で
  異なる数値を表示することになる。加えて`const alpha=d.alpha??1.0`
  という変数が宣言されているが式中では一切使用されておらず、
  ALPHA-REDESIGN-1以前の名残と思われる死コードが残存している。
- **AS-IS-059: `get_terminal_growth()`はticker個別設定が「デフォルト値
  3.0%ちょうど」の場合、それが意図的な明示設定か単なる未設定かを
  区別できない**: `abs(ticker_tv_g - 0.03) > 1e-5`という差分チェックの
  設計上、管理者が意図的に「このticker のTVは3.0%にする」と
  `maturity_config.json`へ明示設定しても、デフォルト値と一致するため
  「未設定」とみなされ、セクター別Damodaranテーブルの値がもし
  異なればそちらが優先されてしまう。3.0%を明示指定したい場合の
  抜け道が存在しない。
- **AS-IS-492〜498（TANUKI TAIL stage2）は本サブカテゴリの他の
  大半の項目と異なり、決定論的な計算式ではなくAI（Grok）による
  自由生成JSONである**: 「定義」列に記載した内容は実際には
  「このプロンプトをAIに渡すとこの構造のJSONが返る」という関係で
  あり、`revenue_growth_y1`等の具体的な数値がどのような論理で
  導かれたかをコード側から再現・検算することはできない。同じ
  DCF/WACC構成要素系というサブカテゴリの中に「厳密な数式」と
  「AIの裁量」が混在している点は、本カテゴリの定義作業における
  特筆すべき構造的差異である。

### 次フェーズへの申し送り

- 本フェーズで引用のみ行い内部アルゴリズムを再展開しなかったAS-IS-ID:
  信頼性・品質判定系のAS-IS-268/269（EPS Analyzer adjustments）・
  AS-IS-482〜491（TANUKI TAIL stage1評価）、カタリスト・イベント予測系の
  AS-IS-419〜423（TANUKI TAIL KPI実績）
- AS-IS-026（moat_score）・AS-IS-047（fcf_history）・AS-IS-129（revenue）・
  AS-IS-267（EPS Analyzer quarters）は既定義（フェーズ4）のものを
  そのまま引用した
- 本フェーズで発見したBear/Bull符号反転（AS-IS-015）・rev_ttm未提供時の
  RPO安全弁スキップ（AS-IS-024）・RICE_adj非対称ゼロ化（AS-IS-027）・
  β=0/負値の無条件フォールバック（AS-IS-013）・v0/v0_rmの取り違えリスク
  （AS-IS-007）はいずれも実装（コード修正）を伴うため、本タスクの範囲外
  として記録にとどめた

---

## 対象7（フェーズ7）: 導出データ — カタリスト・イベント予測系（50件）

出発点: `DERIVED_DATA_SUBCATEGORIES.md`「カタリスト・イベント予測系
（50件）」（ステップ6確定後392件ベース。AS-IS-048/051/104/105/106/108/
162/163/164/243/244/245/246/248/250/251/252/253/254/255/256/257/258/259/
260/275/276/278/279/419/420/421/422/423/452/499/500/501/502/503/504/505/
507/508/510/511/512/513/514/515）

実装（コード修正）は行っていない。定義の記録のみ。

**前フェーズ（DCF/WACC構成要素系）での訂正**: フェーズ6でAS-IS-113
（HypeCore `expectation_score`）の構成要素として引用したAS-IS-105
（`analyst_upgrade_rate`）を誤って「成長率・トレンド系」と記載したが、
本ドキュメント作成時に`DERIVED_DATA_SUBCATEGORIES.md`を再確認したところ
AS-IS-105は正しくは本フェーズの「カタリスト・イベント予測系」に属する
（492行目のセクション見出し配下）。分類ラベルの誤記であり計算式自体への
影響はない。

**本カテゴリの特徴（依頼文の想定通り）**: Discover（16件）・TANUKI TAIL
のcall2系（7件）・stage2 kpi_forecasts等はAI（Grok）による自由生成
コンテンツであり、決定論的な計算式が存在しない。該当項目は「定義」欄に
プロンプトの入力データ・生成頻度・出力構造を記載する（フェーズ6のTANUKI
TAIL stage2で確立した記載方法を踏襲）。

| AS-IS ID(元) | サブシステム | 表示名 | プログラム名称 | 定義（最小単位まで分解、AI生成の場合は入力データ・生成方法） | データ取得元 | データ性質分類 |
|---|---|---|---|---|---|---|
| AS-IS-048 | TANUKI VALUATION | next_earnings_date | `pipeline.py:_load_extra_data()` | yfinance `Ticker.calendar["Earnings Date"]`から本日以降の最初の日付を採用。全て過去日の場合はリスト先頭（＝最も古い過去日）をそのまま採用する（**この場合「次回決算日」が実際には過去日になる、下記備考**） | yfinance calendar（カタログ対象外） | 導出データ |
| AS-IS-051 | TANUKI VALUATION | breakeven_estimate | `pipeline.py:_load_extra_data()` | 対象は直近四半期`adjusted_eps<0`（赤字）銘柄のみ。直近4四半期の`adjusted_eps`（AS-IS-267、既定義・フェーズ4）にOLS単回帰（x=四半期インデックス、y=EPS）を適用し、回帰直線がゼロを横切る時点`x_zero=-intercept/slope`を四半期数に換算、`slope>0`かつ`0<quarters_until<20`の場合のみ`round(現在年+quarters_until/4)`で黒字化年を算出 | AS-IS-267（既定義・フェーズ4） | 導出データ |
| AS-IS-104 | HypeCore | eps_surprise | `fetch_analyst_history()` | 優先順位: ①yfinance `earnings_history.surprisePercent`（四半期ごとの実績、月次前方補完、最大4ヶ月）②`quarterly_earnings["Surprise(%)"]`（フォールバック1）③`info.get("earningsGrowth")×100`（フォールバック2、欠損月のみ適用）。最終的に3ヶ月まで前方補完 | yfinance（カタログ対象外） | 導出データ |
| AS-IS-105 | HypeCore | analyst_upgrade_rate | `fetch_analyst_history()` | yfinance `upgrades_downgrades`を月次集計し、`ToGrade`がBuy系（Buy/Strong Buy/Outperform等）なら`is_upgrade=1`、Sell系なら`is_downgrade=1`として月次件数を集計。`upgrade_rate = upgrades/(upgrades+downgrades+1e-9)`を3ヶ月移動平均で平滑化 | yfinance（カタログ対象外） | 導出データ |
| AS-IS-106 | HypeCore | analyst_downgrade_rate | `fetch_analyst_history()` | AS-IS-105と同一集計の`downgrade_rate = downgrades/(upgrades+downgrades+1e-9)`（3ヶ月移動平均あり） | AS-IS-105と同じ（yfinance、カタログ対象外） | 導出データ |
| AS-IS-108 | HypeCore | buy_hold_ratio | `fetch_analyst_history()` | yfinance `recommendations`の直近月（`period=="0m"`）行から`buy_ratio = (strongBuy+buy)/(strongBuy+buy+hold+sell+strongSell+1e-9)`。**名称は「buy_hold」だがholdは分子に含まれない、下記備考**。現時点値のみ本日の月に設定（過去月は未設定） | yfinance（カタログ対象外） | 導出データ |
| AS-IS-162 | STONKS SILO | gaap_breakeven_year/gaap_breakeven_reason | `_gaap_margin_breakeven()` | 直近年`net_income>0`なら`ACHIEVED`。それ以外は2段階: Step1「純利益率(NI/Revenue×100)」の直近2点線形外挿（傾き≤500pt/年）でゼロ交差年を算出、`be_year<=latest_yr`なら`IMMINENT`、`>latest_yr+5年`なら`TOO_FAR`。Step1不成立ならStep2「直近3年の絶対値OLS回帰」にフォールバック（`NO_TREND`/`NO_DATA`/`PREDICTED`等）。`ocf_trend`（AS-IS-161、既定義・フェーズ5）が`DETERIORATING`の場合は最終的に`NO_TREND`へ上書き | AS-IS-129（既定義・一次データ、revenue_sanitized経由）＋ AS-IS-161（既定義・フェーズ5）＋ net_income（SEC EDGAR、カタログ対象外） | 導出データ |
| AS-IS-163 | STONKS SILO | ocf_breakeven_year/ocf_breakeven_reason | `_margin_breakeven()` | 直近年`OCF>0`なら`ACHIEVED`（＝AS-IS-164）。それ以外はAS-IS-162と同型の2段階（OCFマージン=OCF/Revenueの2点線形外挿→3年絶対値OLSフォールバック）だが`IMMINENT`判定分岐はなくStep1不成立時は直ちにStep2へ | AS-IS-129（既定義）＋ AS-IS-156（既定義・フェーズ4、ocf_annual経由） | 導出データ |
| AS-IS-164 | STONKS SILO | hidden_profit_already | `_breakeven_estimate()` | `latest_ocf = ocf_annual[直近年] > 0`の単純真偽判定（AS-IS-163のACHIEVED条件と同一式） | AS-IS-156（既定義・フェーズ4） | 導出データ |
| AS-IS-243 | Discover | catalysts[].id | `next_id()` | `{ticker}-{年}-{連番3桁}`形式の決定論的な採番（既存IDと重複しないシーケンス番号）。AI生成ではない | システム内部（カタログ対象外） | 導出データ |
| AS-IS-244 | Discover | catalysts[].title/detail/timing/importance/type/probability | `discover_catalysts()`→Grok | **AI生成**: `{ticker}について今後12ヶ月以内のカタリスト候補を幅広く列挙`というプロンプト（grok-3、web検索）。毎週日曜JST23:30、HypeCore対象銘柄（`get_hypecore_tickers()`）全件に対して実行。`importance`/`type`/`probability`は選択肢外の値ならデフォルト（中/不確定シナリオ/中）に丸められる | Grok API（grok-3、web検索、カタログ対象外） | 導出データ |
| AS-IS-245 | Discover | catalysts[].status | `reevaluate_catalysts()`→Grok | 新規発掘時は`"未達"`固定。既存の「未達」カタリストのみ、別のGrok呼び出し（web検索で最新情報確認）で`"未達"/"達成済み"/"消滅"`に再判定。**判定対象は`status=="未達"`の既存分のみ**（達成済み・消滅済みは再評価対象外） | Grok API（web検索、カタログ対象外） | 導出データ |
| AS-IS-246 | Discover | catalysts[].first_detected | `process_ticker()` | 新規発掘時点の`today`（**JST基準ではなく`date.today()`という素の日付、下記備考UTC/JST不整合参照**） | システム内部（カタログ対象外） | 導出データ |
| AS-IS-248 | Discover | 影響予測{direction, magnitude, thesis_effect, summary} | `predict_for_items()`→Grok（`impact_predictor.py`） | **AI生成**: news/catalyst由来の項目一覧を渡し、株価・投資シナリオへの影響方向（positive/negative/neutral）・度合い（高中低）・保有テーゼへの影響（補強/弱化/中立）・30字要約を生成させる。3モデルフォールバック（grok-3-mini→grok-3→grok-2-1212）。**catalystモードは`first_detected==本日`の新規項目のみ対象**（既存カタリストは再評価されない、下記備考）。**表示先はcatalyst.html/news_history.htmlのみで、Discoverのメイン一覧index.htmlには一切表示されない**（下記備考） | AS-IS-244, AS-IS-250（本表）＋ Grok API（カタログ対象外） | 導出データ |
| AS-IS-250 | Discover | classified.items[].{title,category,importance,summary,url,source,published_at} | `classify_news()`/`classify_news_with_grok_search()` | **AI生成**: NEWS API（NewsAPI.org、直近2日分見出し5件）を渡しGrokに分類させる。NEWS APIが0件かつ`category∈{保有中,監視中}`の銘柄のみGrok web検索に代替（**category=様子見はAPI 0件時そのまま「データなし」、下記備考**）。カテゴリ（カタリスト/リスク/ブレイクスルー/一般）・重要度（高中低なし）を判定、`importance="なし"`および完全重複タイトルは`_dedupe_items()`で除外。毎日JST 7:00実行 | NewsAPI.org（カタログ対象外）＋ Grok API（カタログ対象外） | 導出データ |
| AS-IS-251 | Discover | classified.summary | 同上 | 同一Grok応答内の`summary`（全体を50字以内で要約、AI生成） | AS-IS-250と同じ | 導出データ |
| AS-IS-252 | Discover | classified.conditions_met[]/risk_flags[] | 同上 | 同一Grok応答内の`conditions_met`（銘柄の通過条件、最大3件）・`risk_flags`（リスク要因、最大3件）。いずれもAI生成 | AS-IS-250と同じ | 導出データ |
| AS-IS-253 | Discover | top_importance | 同上 | 同一Grok応答内の`top_importance`（高/中/低、AI生成）。`tickers[ticker]`直下に`classified.top_importance`のコピーとしても格納される（同一値の重複格納） | AS-IS-250と同じ | 導出データ |
| AS-IS-254 | Discover | candidates[].{ticker,company,sector,reason,risk} | `explore_candidates()`→Grok | **AI生成**: 時価総額$5億〜$100億・機関投資家保有率40%未満・直近12ヶ月売上成長率30%以上・主要指数未採用等の条件を満たす新規候補銘柄をGrokにweb検索させる。既存監視リスト銘柄は除外指示。毎日JST 7:00実行（collect.pyのメインフロー） | Grok API（web検索、カタログ対象外） | 導出データ |
| AS-IS-255 | Discover | candidates[].screening_pass[] | 同上 | 同一Grok応答内の`screening_pass`（実際に満たす通過条件、最大5件、AI自己申告） | AS-IS-254と同じ | 導出データ |
| AS-IS-256 | Discover | candidates[].catalyst_type | 同上 | 同一Grok応答内の`catalyst_type`（決算サプライズ/製品発表/規制変化/市場拡大/その他） | AS-IS-254と同じ | 導出データ |
| AS-IS-257 | Discover | candidates[].conviction | 同上 | 同一Grok応答内の`conviction`（高中低） | AS-IS-254と同じ | 導出データ |
| AS-IS-258 | Discover | macro_themes[].{theme,horizon,conviction,background,catalyst} | `explore_macro_themes()`→Grok | **AI生成**: 今後6〜18ヶ月の「特大テーマ候補」3件をGrok（grok-3固定、web検索）に生成させる。**日曜日のみ実行**（`now_jst.weekday()==6`）、それ以外の曜日は前回`daily_report.json`の`macro_themes`をそのまま引き継ぐ（下記備考）。履歴は`macro_themes_history.json`に最大26件（≒半年分）保持 | Grok API（web検索、カタログ対象外） | 導出データ |
| AS-IS-259 | Discover | macro_themes[].related_tickers[].{ticker,role,note} | 同上 | 同一Grok応答内の`related_tickers`。プロンプトで既存監視銘柄リストを提示し「リスト外の銘柄は含めない」よう指示。`role`は「主要」「ボトルネック」「注目」の3種類に限定指示（AI生成のため厳密な保証はプロンプト依存） | AS-IS-258と同じ | 導出データ |
| AS-IS-260 | Discover | macro_themes[].sources[] | 同上 | 同一Grok応答内の`sources`（情報源名・URL、1〜3件。URLが不明な場合はnullをAIが自己申告） | AS-IS-258と同じ | 導出データ |
| AS-IS-275 | EPS Analyzer | eps_diff | `generate_summary()` | `eps_diff = round(adjusted_eps - gaap_eps, 4)`（最新四半期`quarters[0]`、AS-IS-267既定義・フェーズ4のサブフィールド） | AS-IS-267（既定義・フェーズ4） | 導出データ |
| AS-IS-276 | EPS Analyzer | eps_ratio | 同上 | `ratio = (adjusted_eps-gaap_eps)/abs(gaap_eps)×100`（`gaap_eps==0`なら0） | AS-IS-267（既定義・フェーズ4） | 導出データ |
| AS-IS-278 | EPS Analyzer | yoy_growth | 同上 | `yoy_growth = (quarters[0].adjusted_eps - quarters[4].adjusted_eps) / abs(quarters[4].adjusted_eps)`（直近四半期と4件前＝前年同期の比較。5四半期未満のデータではNone） | AS-IS-267（既定義・フェーズ4） | 導出データ |
| AS-IS-279 | EPS Analyzer | health | 同上 | `eps_ratio`（AS-IS-276）の値による5段階分類: `0→調整なし`、`0<ratio≤20→調整小`、`20<ratio≤80→調整中`、`ratio>80→調整大`、`-20≤ratio<0→調整小（マイナス）`、`ratio<-20→過大調整`。ただし`gaap_eps<0かつadjusted_eps>0`の場合は強制的に`調整大`に上書き | AS-IS-276（本表） | 導出データ |
| AS-IS-419 | TANUKI TAIL | kpis.{kpi_name}.unit | `xbrl_segment_fetcher.py:fetch_ticker()` | **常に固定文字列`"USD"`**（KPIの実際の性質〈比率・件数等〉に関わらず無条件、下記備考） | 定数（カタログ対象外） | 導出データ |
| AS-IS-420 | TANUKI TAIL | kpis.{kpi_name}.data[].quarter | 同上 | `quarter_label(period)`（10-Q提出書類のperiod日付から四半期ラベルへ変換） | SEC EDGAR 10-Q（カタログ対象外） | 導出データ |
| AS-IS-421 | TANUKI TAIL | kpis.{kpi_name}.data[].value | 同上 | XBRL 10-Qファイリングから`parse_and_extract()`が抽出した値。整数に近い値（USD金額）は`int`、小数値（比率）は`round(値,4)`のfloatで保持 | SEC EDGAR 10-Q XBRL（カタログ対象外） | 導出データ |
| AS-IS-422 | TANUKI TAIL | kpis.{name}.value（Layer3テキスト抽出） | `text_kpi_extractor.py:extract_layer3()` | **AI生成**: `auto_fetchable=false`のKPI（XBRL構造化データで取得不可）のみ対象。10-Q MD&Aテキスト＋8-K EX-99.1（決算プレスリリース）をGrokに渡し、`extraction_hint`を手がかりに数値を抽出させる。「数値が明示されている場合のみ記入・推測禁止」と指示。`value`は原文の文字列表現（例:"150%"） | Grok API（10-Q MD&A/8-K EX-99.1テキストベース、カタログ対象外） | 導出データ |
| AS-IS-423 | TANUKI TAIL | kpis.{name}.value_numeric（Layer3） | 同上 | AS-IS-422と同一Grok応答内の`value_numeric`（AIが自ら数値化した値、例:150）。`confidence`（high/medium/low）もAI自己申告 | AS-IS-422と同じ | 導出データ |
| AS-IS-452 | TANUKI TAIL | kpi_current.{KPI名} | `tail_dcf_bridge.py:_build_current_kpi_values()` | `layer2.kpis[KPI名].data[0].value`（最新1件、AS-IS-421既定義のパススルー） | AS-IS-421（本表） | 導出データ |
| AS-IS-499 | TANUKI TAIL | call2.five_perspectives.{5観点} | `build_call2_prompt()`→Grok | **AI生成**（web検索併用）: ①ビジネスモデル②成長性③競争優位④経営⑤市場環境の5観点分析。プロンプト入力: 投資テーゼ・エントリーストーリー・Call1（stage1）評価結果全体・マクロ環境・過去call2の引き継ぎ事項（前回5観点要約等、重複回避目的）・KPI実績8四半期＋YoY/QoQ・Layer3抽出KPI・健全度推移。「KPI実績を各観点の起点として必ず使用」「テーゼの言い換え禁止」と明示的に指示 | Stage1評価結果（信頼性・品質判定系・未定義）＋ KPI実績（AS-IS-420/421既定義、本表422/423）＋ マクロ環境（未定義） | 導出データ |
| AS-IS-500 | TANUKI TAIL | call2.entry_story_progress | 同上 | 同一Grok応答内。「エントリーストーリーは現在どの程度実現しているか」をweb検索で確認させた自由記述 | AS-IS-499と同じ | 導出データ |
| AS-IS-501 | TANUKI TAIL | call2.market_attention | 同上 | 同一Grok応答内。「市場・メディア・アナリストが今最も注目している点」をweb検索させた自由記述（出典明示指示あり） | AS-IS-499と同じ | 導出データ |
| AS-IS-502 | TANUKI TAIL | call2.historical_analogy | 同上 | 同一Grok応答内。ビジネスモデル・成長軌跡・リスク構造が類似する歴史的企業1社（`company`/`similarity`/`outcome`/`implication`）。「一般的な類比は禁止」と明示指示 | AS-IS-499と同じ | 導出データ |
| AS-IS-503 | TANUKI TAIL | call2.macro_implications | 同上 | 同一Grok応答内。現在のマクロ環境（スコア・フェーズ）がテーゼに与える影響の自由記述 | AS-IS-499と同じ | 導出データ |
| AS-IS-504 | TANUKI TAIL | call2.thesis_questions | 同上 | 同一Grok応答内。テーゼへの問いかけ3件。「言い換え禁止」「過去の問いと重複禁止」（過去call2の`thesis_questions`をプロンプトに含めて重複回避） | AS-IS-499と同じ | 導出データ |
| AS-IS-505 | TANUKI TAIL | call2.next_review_focus | 同上 | 同一Grok応答内。次回決算で確認すべき論点3件（優先度順）。過去call2の`next_review_focus`との重複除外指示あり | AS-IS-499と同じ | 導出データ |
| AS-IS-507 | TANUKI TAIL | review_quarter | `prediction_tracker.py:track_ticker()` | レビューJSON自体の`quarter`フィールドをそのまま参照（`quarterly_review_generator.py`が生成時に設定） | レビューJSONのquarter（カタログ対象外） | 導出データ |
| AS-IS-508 | TANUKI TAIL | forecast_target | 同上 | `_add_quarters(review_quarter, 4)`（レビュー対象四半期の1年後＝4四半期後を計算） | AS-IS-507（本表） | 導出データ |
| AS-IS-510 | TANUKI TAIL | predictions[KPI名].predicted | 同上 | `stage2.scenarios.{シナリオ}.kpi_forecasts["1年後"][KPI名]`（AS-IS-496、既定義・フェーズ6、AI生成値）をそのまま参照 | AS-IS-496（既定義・フェーズ6） | 導出データ |
| AS-IS-511 | TANUKI TAIL | predictions[KPI名].actual | 同上 | `layer2.kpis[KPI名]`の`forecast_target`（AS-IS-508）時点の実績値（AS-IS-421既定義のXBRL実測値） | AS-IS-421（本表）＋ AS-IS-508（本表） | 導出データ |
| AS-IS-512 | TANUKI TAIL | predictions[KPI名].deviation_pct | 同上 | `round((actual-predicted)/abs(predicted)×100, 1)`（`predicted`が非ゼロの場合のみ、それ以外はNone） | AS-IS-510, AS-IS-511（本表） | 導出データ |
| AS-IS-513 | TANUKI TAIL | predictions[KPI名].accuracy | 同上 | `_classify_deviation(dev_pct)`: `abs(dev_pct)≤10→accurate`、`dev_pct>10→under_estimated`（実績が予測を上回った＝予測が過小だった）、`dev_pct<-10→over_estimated`（実績が予測を下回った＝予測が過大だった） | AS-IS-512（本表） | 導出データ |
| AS-IS-514 | TANUKI TAIL | kpi_forecast_available | 同上 | `bool(stage2.scenarios.{シナリオ}.kpi_forecasts["1年後"])`（AI生成のkpi_forecastsが空でないか） | AS-IS-496（既定義・フェーズ6） | 導出データ |
| AS-IS-515 | TANUKI TAIL | matchable | 同上 | `len(predictions_1y) > 0`（AS-IS-510〜513が1件以上生成できたか＝予測KPIと実績KPIが最低1つ一致したか） | AS-IS-510〜513（本表） | 導出データ |

### 分解の過程で新たに気づいた問題

- **UTC/JST日付不整合（`explore_macro_themes()`、最重要）**:
  `collect.py:249` `today = date.today().isoformat()`は**タイムゾーン
  非対応の素の日付**（GitHub Actionsランナーの実行環境時刻、実質UTC）を
  使うのに対し、同じcollect.pyの他の箇所（`main()`内`now_jst =
  datetime.now(JST)`、`append_to_monthly_history()`内`today =
  now_jst.strftime(...)`）は明示的にJST変換している。collect.pyは
  「毎日JST 7:00」に実行される設計（ファイル冒頭コメント）だが、
  JST 7:00は同日UTC ではまだ前日22:00（UTC 7:00-9:00=-2:00、日付が
  繰り下がる）であり、`date.today()`はJSTの実行日より**1日古い日付**を
  返す。この結果`macro_themes[].generated_at`（AS-IS-258の一部、
  `explore_macro_themes()`が設定）は、同じレポート内の
  `daily_report.json.generated_at`（正しくJST基準）より1日古い値に
  なりうる。`catalyst.py`（毎週日曜JST23:30実行）の同種の`date.today()`
  使用（`first_detected`/`last_updated`、AS-IS-246）はJST23:30が
  UTC 14:30で日付を跨がないため実害が生じにくいが、同様に
  タイムゾーン非対応である点は同一の設計リスクとして残る。
- **影響予測（AS-IS-248）はDiscoverのメイン画面index.htmlに一切表示
  されない**: `docs/discover/catalyst.html`・`docs/discover/
  news_history.html`は`impact_predictions_{ym}.json`をfetchして
  表示するが、`docs/discover/index.html`は同ファイルを一切参照しない
  （grep確認済み、0件）。影響予測は計算・保存されているにもかかわらず、
  Discoverの一覧画面を見るだけのユーザーには存在自体が伝わらない。
- **config二重管理（discover_config.json/theme_config.json）**:
  管理画面`docs/discover/admin.html`は`config/discover_config.json`・
  `config/theme_config.json`にGitHub API経由で直接コミットする。
  日次バッチ`collect.py`も`config/discover_config.json`を正しく参照する。
  しかし**表示画面`docs/discover/index.html`は別パス
  `docs/portfolio/data/discover_config.json`・
  `docs/portfolio/data/theme_config.json`（コピー）を参照する**。
  この2ファイルの同期は新規銘柄登録手順（Step 6）の
  `shutil.copy()`一回限りの処理に依存しており、admin.html経由で
  テーマ・カテゴリを直接編集した場合はこのコピー処理を経由しないため、
  「admin.htmlは保存成功と表示するがindex.htmlの表示は更新されない」
  というズレが発生しうる。
- **テーマ連続登場判定（index.html）が文字列部分一致に依存し精度が
  低い**: `themeStreakMap`の算出ロジック
  （`docs/discover/index.html:452-457`）は、今週のテーマ名と過去4週分の
  テーマ名を`hn.includes(name) || name.includes(hn)`という**単純な
  部分文字列一致**で比較する。テーマ名自体は`explore_macro_themes()`
  （AS-IS-258）が毎週Grokに自由生成させた20字以内の文字列であり、
  同一の実質的テーマでも週によって表現が微妙に変わりうる（例:
  「AI電力インフラ需要」と「データセンター電力不足」）。この場合
  部分文字列一致では継続と判定されず「🔥N週連続」バッジが過小評価
  される（偽陰性）。逆に無関係な2つのテーマが偶然共通の部分文字列を
  持つ場合は誤って連続登場と判定される（偽陽性）リスクもある。
  ID・埋め込みベースの意味的一致ではなく素朴な文字列比較である点が
  精度の限界。
- **AS-IS-248（影響予測）はcatalystモードで新規発掘分のみが対象**:
  `impact_predictor.py:run_catalyst()`は`first_detected==本日`の
  カタリストのみを予測対象とする（既存の累積カタリストは対象外、
  コスト抑制目的とコード内コメントに明記）。このため、ある日の
  `catalyst.py`実行後に`impact_predictor.py --source catalyst`の
  実行が何らかの理由で漏れた場合、そのカタリストは**未来永劫
  影響予測を持てない**（翌日以降は`first_detected`が過去日になり
  対象外になるため）。
- **classified.items（AS-IS-250）は「様子見」カテゴリ銘柄でNEWS API
  0件時のフォールバックが効かない**: `collect.py:main()`の分岐
  （`elif info.get("category") in ["保有中","監視中"]`）はGrok web検索
  代替を「保有中」「様子見」に限定せず「様子見」を除外している。
  「様子見」銘柄はNEWS APIで0件だった場合、Grok代替を試さず
  無条件で`{"items":[],"summary":"データなし"}`になる。
- **buy_hold_ratio（AS-IS-108）は名称と実体が食い違う**:
  変数名・フィールド名は「buy_HOLD_ratio」だが、実際の計算式
  `(strongBuy+buy)/(strongBuy+buy+hold+sell+strongSell)`には
  `hold`が分子に含まれておらず、実質的に「Buy比率」（Strong Buy+Buy
  の比率）である。
- **kpis.{kpi_name}.unit（AS-IS-419）が常に"USD"固定**:
  `xbrl_segment_fetcher.py:fetch_ticker()`は抽出したKPIの`unit`欄に
  無条件で`"USD"`を設定する。同じ関数内で「整数に近い値（USD金額）は
  int、小数値（比率）はfloat」と値の型を使い分けている（コード自身が
  比率KPIの存在を認識している）にもかかわらず、`unit`フィールドは
  比率KPIであっても"USD"のままになる。
- **「黒字化年予測」がTANUKI VALUATION（AS-IS-051）とSTONKS SILO
  （AS-IS-162/163）で全く異なる手法を採る**: 前者は調整後EPS
  （四半期）4点のOLS単回帰、後者はマージン（OCF or NI ÷ Revenue）の
  直近2点線形外挿を優先しOLS絶対値回帰へフォールバックする2段階方式。
  同じ「黒字化時期の予測」という概念に対し、データ粒度（四半期EPS vs
  年次マージン）・手法（単純OLS vs 2段階外挿）ともに独立した実装が
  並存している。
- **macro_themes（AS-IS-258〜260）は日曜以外に「見た目上は毎日更新
  されているが中身は先週のまま」になりうる**: `collect.py:main()`は
  日曜以外`macro_themes`を前回`daily_report.json`からそのまま引き継ぐ
  （416-422行）が、`daily_report.json`自体の`generated_at`は毎日
  更新される。ユーザーが`generated_at`だけを見て「今日生成された
  最新のテーマ」と誤認するリスクがある（各テーマオブジェクト自体が
  持つ`generated_at`〈週次生成日〉を見れば区別できるが、レポート全体の
  タイムスタンプとは別に確認する必要がある）。

### 次フェーズへの申し送り

- 本フェーズで引用のみ行い内部アルゴリズムを再展開しなかったAS-IS-ID:
  信頼性・品質判定系のStage1評価結果（AS-IS-482〜491、未定義）、
  マクロ環境スコア（未定義）
- AS-IS-129・AS-IS-156・AS-IS-161・AS-IS-267・AS-IS-420・AS-IS-421・
  AS-IS-496は既定義（フェーズ4/5/6）のものをそのまま引用した
- 本フェーズで発見したUTC/JST日付不整合・config二重管理・テーマ連続
  登場判定の精度不足・影響予測のindex.html非表示・buy_hold_ratioの
  名称不一致・unit常時"USD"固定はいずれも実装（コード修正）を伴うため、
  本タスクの範囲外として記録にとどめた
