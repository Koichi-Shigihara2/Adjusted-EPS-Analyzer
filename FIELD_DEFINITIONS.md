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
