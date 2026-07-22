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
