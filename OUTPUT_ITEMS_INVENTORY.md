# 全サブシステム 出力項目インベントリ

本ドキュメントは、6サブシステム（TANUKI VALUATION / HypeCore / STONKS SILO /
MACRO PULSE / Discover / EPS Analyzer）の出力項目を洗い出し、統一定義の
検討・実データ突合・計算ルート紐付けを行った調査結果の記録である。

調査は2026-07-22に4段階（ステップ1〜4）で実施した。いずれも読み取り専用調査であり、
本ドキュメント自体もその結果を転記したものであって、コード修正は一切含まない。

- ステップ1: 全サブシステムの出力項目洗い出し（共通項目候補・削除候補の特定）
- ステップ2〜4: 共通項目候補（11群）の統一定義提案・データ要件特定・実データ検証
- ステップ5: 出力項目一覧＋計算ルート紐付け（各項目がどのファイル・関数で計算されるか）

## 目次

1. [ステップ1: 出力項目一覧（サブシステム別）](#ステップ1-出力項目一覧サブシステム別)
2. [ステップ1: 共通項目候補グルーピング（11群）](#ステップ1-共通項目候補グルーピング11群)
3. [ステップ1: 削除候補リスト（サブシステム別）](#ステップ1-削除候補リストサブシステム別)
4. [ステップ2〜4: 統一定義・実データ突合・データ要件検証](#ステップ24-統一定義実データ突合データ要件検証)
5. [ステップ5: 出力項目 計算ルート紐付け（サブシステム別）](#ステップ5-出力項目-計算ルート紐付けサブシステム別)
6. [横断的な発見事項まとめ](#横断的な発見事項まとめ)

---

## ステップ1: 出力項目一覧（サブシステム別）

### 1-1. TANUKI VALUATION

調査対象: `src/value/tanuki_valuation/core_calculator.py`、`pipeline.py`（全3219行）、
`docs/value-monitor/tanuki_valuation/stock.html`（全3033行）、`index.html`（全592行）、
実データ`data/AAPL/latest.json`・`report.txt`。

#### core_calculator.py が latest.json トップレベルに書き出す主要フィールド

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| intrinsic_value_pt | latest.json | 本質的価値（総額、株数換算前） |
| intrinsic_value_per_share | latest.json / stock.html メインカード / report.txt[3] | メイン理論株価（Rmβなし基準） |
| intrinsic_value_beta | latest.json / stock.html 参考①ブロック / history.json | β込みWACC基準の参考理論株価 |
| upside_percent_beta | latest.json（stock.htmlでは差額を都度再計算、この値自体は直接表示されない） | β込みWACC基準の乖離率 |
| intrinsic_value_rf | latest.json / stock.html 参考②ブロック | リスクフリーレート基準の理論上限株価 |
| upside_percent_rf | latest.json（同上、画面独自再計算あり） | Rf基準の乖離率 |
| v0 / v0_adjusted | latest.json / stock.html CALCULATION BREAKDOWN | DCF企業価値（Rmβなし） |
| alpha / alpha_was_capped | latest.json / stock.html α欄 / report.txt[3] Alpha_Premium | HypeCore期待プレミアム（参考値、計算には不使用） |
| future_values（1〜5年後） | latest.json / stock.html 将来価値予測表（画面側で複利再計算あり） | 将来理論株価予測 |
| return_metrics（年別） | latest.json / stock.html 期待リターン行 | 現在株価からの期待リターン |
| upside_percent | latest.json / report.txt[1][2][3] / index.html（ただしindex.htmlは自前で再計算し使わない） | メイン乖離率 |
| calculation_date | latest.json / report.txt全ページ / index.html「最終更新」 | 計算実行日時 |
| formula / dcf_type | latest.json / stock.html ティッカータグ | バージョン式、2段階/3段階/逓減DCF種別 |
| growth.rate / source / phase1_years | latest.json / report.txt[4] / index.html「成長率」列 | 採用成長率とその出所、Phase1年数 |
| wacc.*（value/beta/risk_free_rate/market_return） | latest.json / report.txt[3] / index.html「Ke/WACC」列 | CAPM WACC計算結果 |
| sensitivity.matrix/wacc_values/growth_years | latest.json / stock.html 感応度マトリクス（ただし表示は独自クライアント再計算） | 感応度分析（JSON値は実質未使用、画面はcalcSensIV()で作り直し） |
| growth_scenarios.primary/segment | latest.json / stock.html ティッカータグ・成長根拠 | セグメント加重成長率情報 |
| scenario_valuations.bear/base/bull | latest.json / report.txt[3] / stock.html シナリオ表 | BEAR/BASE/BULLシナリオ別IV |
| growth_options.* | latest.json / report.txt[3] / stock.html（件数バッジ＋詳細） | 成長オプションPV |
| maturity_profile | latest.json / stock.html Phase1/2内訳 | 3段階DCF設定 |
| dcf_components.*（v0/pv_high_growth/pv_terminal/terminal_fcf/terminal_value/v0_rm/pv_fcf_rm/pv_tv_rm/pv_phase1_rm/pv_phase2_rm） | latest.json / report.txt[3] / stock.html DCF詳細・ウォーターフォールチャート | DCF内訳の各構成要素 |
| fcf_base.*（base_fcf/method/fcf_5yr_avg/fcf_2yr_avg/cv/threshold） | latest.json / report.txt[3] / stock.html CALCULATION BREAKDOWN・ティッカータグ | FCFベース自動判定結果 |
| fcf_outlier.*（detected/rule/deviation_pct/action/note/transient_evidence） | latest.json / report.txt[3] DCF_Reliability文中 / stock.html（条件付き表示） | FCF外れ値分析 |
| fcf_estimation.*（applied/conversion_rate/estimated_fcf/divergence_warning/divergence_ratio/ma_addback_*） | latest.json / report.txt[3] / stock.html（条件付き）・警告バナー | FCF実力推定（EPS×転換率） |
| software_system_reclassification.* | latest.json / report.txt[3]のみ | Software_System分類見直し推奨（stock.html非表示、既知） |
| software_system_provisional.* | latest.json / report.txt[3]のみ | 暫定分類フラグ（stock.html非表示、既知） |
| rd_capitalization.* | latest.json / report.txt[3]のみ | R&D資本化補正（stock.html非表示、既知） |
| rpo_adjustment.* | latest.json / report.txt[3] / stock.html（条件付き） | RPO補正詳細 |
| bs_adjustment.* | latest.json / report.txt[3] / stock.html（条件付き） | BS（ネットキャッシュ）補正 |
| rice.*（q/cf_conversion/cf_adj/vc_factor/roic_wacc_ratio/bear,base,bull） | latest.json / report.txt[5] / stock.html RICEセクション・散布図 / index.html「RICE」「RICE/PER」「Q」「CF」列 | RICE投資効率指標一式 |
| fcf_source / fcf_ttm_end / fcf_ttm_periods / rice_data_source | latest.json / report.txtには出ない / stock.htmlはfcf_ttm_endのみフッターで使用 | データソース記録（fcf_source, fcf_ttm_periods, rice_data_sourceは未参照＝削除候補） |
| components.*（fcf_5yr_avg, diluted_shares, roe_10yr_avg, beta, sector, industry, per, per_adjusted, peg, ps, ev_ebitda, ma200, analyst_target_*, insider_*, max_eps, max_eps_per, max_eps_reliability 等30項目超） | latest.json / report.txt各所 / stock.html アナリスト・インサイダー・PER/PEG/PSRカード / index.html 各列 | 個別コンポーネント値（ほぼ全て何らかの画面で使用） |

#### pipeline.py が追加で latest.json に書き込むフィールド（TANUKI SCORE・成長サニティ等）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| tanuki_score / funda_score / score_comment / timing_score / sell_reason | latest.json / report.txt[1] / 別画面`docs/value-monitor/tanuki_score/index.html` | TANUKI SCORE分類（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）。stock.html/index.html(tanuki_valuation)自体には非表示だが、同名の別サブシステム画面`tanuki_score/index.html`で消費されているため真の孤立フィールドではない |
| pre_rounding_score / pre_rounding_comment / rounded_by_policy | latest.json / report.txt[1] Classification_Pre_Rounding | Policy A/B丸め前の分類（丸め発生時のみ） |
| matrix.*（matrix/quadrant/label/key_metric_y/qx/qy） | latest.json / report.txt[2] / 別画面tanuki_score側で使用の可能性大 | MATRIX象限判定（①②③④） |
| growth_sanity.verdict/signals/warnings/recommended_g/recommended_g_median | latest.json / report.txt[4] / stock.html Growth Sanityブロック | 成長率妥当性判定 |
| growth_sanity.industry_benchmark / growth_model / growth_model_reason | latest.json / report.txt[4]のみ | 業界ベンチマーク%・成長モデル種別（stock.html非表示、既知） |
| phase1_growth_original / phase1_growth_auto_adjusted | latest.json / report.txt[3][4] / stock.html自動適用バナー（originalは非表示） | 推奨成長率自動再計算の有無 |
| recommended_g | latest.json / report.txt[3][4] / stock.html Growth Sanityブロック | 推奨成長率 |
| fcf_margin_bear_mult_applied / fcf_margin_note | latest.json / report.txt[3] | FCFマージン悪化によるBEAR補正 |
| erp / forward_earnings_yield | latest.json のみ | ERP（株式リスクプレミアム）。report.txt[7]では独自に再計算表示、stock.htmlはこのJSON値を直接参照せず（未参照＝削除候補寄り） |
| dilution_severity / dilution_comment | latest.json / report.txt[3] / stock.html FINANCIAL HEALTHカード | 希薄化率の深刻度バッジ |
| risk_events[] | latest.json / report.txt[9] / stock.html 既知リスクイベント欄 | Grok検索によるリスクイベント |
| financial_health.*（net_debt, sbc_ttm, dilution_3yr_annual_pct, total_debt, cash_and_equivalents, shares_yr_now, shares_yr_3ago 等） | latest.json / report.txt[3] / stock.html FINANCIAL HEALTHカード | 財務健全性指標 |
| financial_health.cash_missing / buyback_ttm / shares_yr_3ago_label / split_adjusted / split_factor | latest.json のみ | いずれもreport.txt・stock.html両方で未参照＝削除候補 |
| dupont.net_margin / asset_turnover / financial_leverage / roe_decomposed | latest.json / stock.html DUPONT ANALYSISカード（report.txtには非表示） | デュポン分解ROE |
| dupont.ni_ttm / revenue_ttm / total_assets / equity / dupont_bs_period / reliability / reliability_reason | latest.json のみ（ni_ttmはpipeline内部でmax_eps計算に利用されるのみ） | report.txt・stock.html両方で未参照＝削除候補（ni_ttmのみ間接利用あり） |
| net_current_assets_ratio | latest.json のみ | 「シガーバット」指標。report.txt・stock.html・index.html全て未参照＝削除候補 |
| next_earnings_date | latest.json / report.txt[3][6][8] / stock.html フッター・ティッカータグ | 次回決算日 |
| segments[] / segment_configured / segment_ttm_applied | latest.json / report.txt[3] segment_breakdown / stock.html セグメント別売上構成 | セグメント別売上・成長率（segment_configuredフラグ自体はstock.html非表示、既知） |
| fcf_history[]（year/fcf/fcf_margin） | latest.json / report.txt[3] / stock.html FCF推移バーチャート / matrix④判定 | FCF年次推移 |
| computed_runway_months | latest.json（extra経由） / report.txt[8] Runway_Months フォールバック | STONKS SILO未登録銘柄向けランウェイ推定 |
| breakeven_estimate | latest.json / report.txt[8] | 黒字転換予想年 |
| validation.*（checks/overall/ai_comment） | latest.json / stock.html 検証失敗バナー | AI検証結果 |

#### report.txt 独自セクション構成（latest.jsonの値を整形して出力）

| セクション | 主な内容 |
|---|---|
| ヘッダー | Generated, Price, CIK断絶警告（該当ティッカーのみ）, DELLデータ期間注記 |
| [1] TANUKI SCORE | Classification, Classification_Pre_Rounding, Funda_Score, Timing_Score内訳（Deviation_Rate/MA200_Deviation/HypeCore_Phase/Analyst_Consensus）, Comment, 定義文 |
| [2] MATRIX POSITION | Matrix種別/Quadrant/Label/Key_Metric_Y, 閾値定義 |
| [3] TANUKI VALUATION | IV本体、シナリオ、Valuation_Gap_Analysis（逆DCF、乖離-50%超のみ）、FCF_Base、DCF_Reliability（Policy A/B、report.txt専用でJSON化されていない）、Software_System分類見直し警告、暫定分類警告、FCF_CYCLICAL_VOLATILITY_TICKERS注記、KO/SPIR一過性項目個別注記、DCF内訳、財務健全性、FCF推移、セグメント内訳 |
| [4] 成長率根拠 | Phase1成長率、成長モデル、推奨成長率内訳、判定、業界ベンチマーク、signals、構造的ミスマッチ注記 |
| [5] RICE METRICS | BEAR/BASE/BULL RICE、Q/CF/CF_adj、VC_Factor、ROIC_WACC_Ratio |
| [6] EPS ANALYZER | 調整後EPS、GAAP EPS、YoY成長率、直近4四半期実績、PER比較 |
| [7] HYPECORE | Phase、Alpha、HYPE_Signal、6ヶ月履歴、PER/PEG/PS/EV_EBITDA、ERP |
| [8] STONKS SILO | Short_Interest、Institutional_Ownership（常にN/A固定・実質未実装）、Analyst_Consensus、Insider_Activity、Runway、Revenue_Growth_YoY、Breakeven |
| [9] RISK EVENTS | リスクイベント一覧またはN/A |

#### stock.html 独自加工・画面固有項目（latest.jsonにない、または再計算するもの）

| 項目 | 内容 |
|---|---|
| フェアPER／PEGレシオ／PSR | JSON値から画面側で算出・バッジ判定 |
| WACCスライダー再計算 | クライアント側でIVをその場再計算 |
| 感応度マトリクス（表示用） | JSONの`sensitivity`は使わず`calcSensIV()`で独自再構築 |
| Reverse DCF（乖離-50%超時のみ） | EV逆算・必要成長率をクライアント側で完全再計算 |
| RICE×乖離率散布図・MATRIX×HYPEシグナル行 | 全銘柄横断fetch＋独自SVG描画、hypecore stage等を合成 |
| FCF CAGR(3yr) | fcf_history[]から画面側で算出 |
| キャッシュフロー分析セクション | `sec_data/normalized/...`を別途fetchしOCF/CapEx/FCF推移を独自集計 |
| セクター別FCF信頼性注意バナー・FCF実力推定注意バナー・KO/SPIR注記 | pipeline.py側のハードコードリストをJS側にも別途複製保持 |
| 理論株価時系列チャート | `history.json`（latest.json外）を使用 |
| HYPECOREフェーズ履歴 | `hypecore_history/{ticker}.json`（latest.json外） |
| 統合レポート表示ボタン | `report.txt`をモーダル表示 |

#### index.html 表示項目

| 項目 | 内容 |
|---|---|
| 銘柄数／平均Moat／平均RICE／最終更新 | 全銘柄latest.jsonを個別fetchし画面側で集計（サマリーバー） |
| TICKER＋バッジ（2yr/SEG/GO） | fcf_base.method, growth_scenarios.primary.source, growth_options.count から判定 |
| 現在株価／理論株価BASE／理論株価β込み | components.current_price, intrinsic_value_per_share（フォールバックあり）, intrinsic_value_beta |
| 乖離率 | JSONのupside_percentは使わず画面側で再計算 |
| Moat／RICE base／RICE/PER | components.moat_score, rice.base.rice, rice.base.rice_per_ratio |
| 200MA乖離 | ma200生値から画面側で乖離率算出 |
| 成長率BASE／WACC／Q／CF | scenario_valuations.base, wacc.value, rice.q, rice.cf_conversion |
| 更新日 | calculation_date |
| ソート機能 | 全14列クリックソート（フィルタUIなし、既定は乖離率降順） |
| 集計ファイル`data/tickers.json` | ティッカー一覧のみ（スコア等の実データは含まない）。各銘柄データは個別latest.jsonを並列fetch |

### 1-2. HypeCore

対象ファイル: `src/value/hypecore/hypecore.py`（生成ロジック、`run_poc()`の`out.append(...)`が最終JSON構造）、
`docs/value-monitor/hypecore/detail.html`（個別銘柄詳細）、`docs/value-monitor/hypecore/index.html`（一覧）、
`docs/value-monitor/hypecore/data/AAPL_poc.json`（実データ確認済み）、`docs/value-monitor/hypecore/data/tickers.json`。

#### トップレベル（`{ticker}_poc.json`）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `ticker` | JSON出力のみ | 銘柄コード（フロントでは未参照。index.html/detail.htmlともticker変数はループ元/URLパラメータから取得） |
| `generated` | JSON出力のみ | 生成日（日付のみ、未参照） |
| `generated_at` | index.html（last-updated表示） | JST生成時刻。一覧画面ヘッダーに表示 |
| `monthly` | 両画面 | 月次データ配列（本体） |

#### `monthly[]` 各要素

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `month` | 両画面 | 対象月（YYYY-MM） |
| `price` | 両画面 | 月末株価 |
| `stage` | 両画面 | ステージ番号0-4（判定結果） |
| `stage_label` | JSON出力のみ | ステージ名（フロントは独自に`STAGE_LABEL`/`STAGES`を再定義、hypecore.py側`STAGE_LABELS`と合わせ計3重定義）※ステップ5調査で他サブシステム参照が判明、詳細は5-2節参照 |
| `ma200_dev` | 両画面（チャート・指標・テーブル） | MA200乖離率% |
| `ma50_dev` | JSON出力のみ | MA50乖離率%（未参照） |
| `from_peak` | 両画面 | 直近24ヶ月高値からの下落率% |
| `rsi` | 両画面 | RSI（14日） |
| `volume_ratio` | JSON出力のみ | 20日平均比出来高比率（未参照、`vol_surge`が代わりに使用） |
| `vol_surge` | detail.html（黎明期指標） | 6ヶ月平均比の出来高急増度 |
| `rev_yoy` | 両画面（チャート・テーブル・指標） | 売上YoY成長率% |
| `ni_yoy` | JSON出力のみ | 純利益YoY成長率%（未参照、fundamental_score計算にのみ内部利用） |
| `rule40` | 両画面 | Rule of 40（売上成長率＋営業利益率） |
| `fcf_yield` | detail.html（成熟期指標） | FCF利回り% |
| `forward_pe` | detail.html（成長期/陶酔期系指標・valMultiples） | 予想PER |
| `peg_ratio` | detail.html（成熟期指標・valMultiples） | PEGレシオ |
| `psr` | detail.html（拡大期指標・valMultiples） | 株価売上高倍率 |
| `revenue_growth` | 両画面（ライフサイクル判定`detectLifecycle`のみ） | yfinance由来の売上成長率（小数） |
| `earnings_growth` | JSON出力のみ | yfinance由来の利益成長率（未参照。Python側`determine_stage`内でも`earn_growth`変数に代入されるが判定条件で未使用の完全デッドコード） |
| `recommendation_mean` | JSON出力のみ | アナリスト平均評価（未参照。Python側`determine_stage`のS1判定条件では使用されている＝ステージ判定には寄与するがJSON値自体は表示されない） |
| `short_pct_float` | JSON出力のみ | 空売り比率（未参照。Python側`determine_stage`のS0判定条件では使用） |
| `eps_surprise` | 両画面 | EPSサプライズ率% |
| `analyst_upgrade_rate` | detail.html（成長期指標） | アナリスト上方修正率 |
| `analyst_downgrade_rate` | JSON出力のみ | アナリスト下方修正率（未参照） |
| `sell_on_good_news` | JSON出力のみ | 良決算下落フラグ（未参照、既知） |
| `buy_hold_ratio` | JSON出力のみ | Buy/Hold比率（未参照、Python側`determine_stage`のS1条件では使用） |
| `substage_phase` | 両画面 | 内部フェーズ（入口/中盤/出口等） |
| `substage_label` | 両画面 | フェーズラベル |
| `substage_watch` | detail.html | 現状の見方テキスト |
| `substage_next` | detail.html | 次のシグナルテキスト |
| `expectation_score` | JSON出力のみ | 期待Zスコア（未参照、ステージ判定のZ-scoreベース条件でのみ内部利用）※ステップ5調査で他サブシステム参照が判明、詳細は5-2節参照 |
| `fundamental_score` | JSON出力のみ | 実体Zスコア（未参照） |
| `momentum_score` | JSON出力のみ | モメンタムZスコア（未参照、判定条件で使用） |
| `price_iv_ratio` | 両画面 | 株価÷TANUKI理論価格 |
| `ev_ebitda` | detail.html（valMultiples） | EV/EBITDA |
| `low_base_effect` | JSON出力のみ | 低ベース効果フラグ（未参照、既知） |

#### `tickers.json`（一覧画面用インデックス）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `tickers` | index.html | 対象銘柄リスト（実際に描画に使用） |
| `updated_at` | JSON出力のみ | インデックス更新日時（未参照、index.htmlは各`_poc.json`の`generated_at`を使う） |
| `count` | JSON出力のみ | 銘柄数（未参照） |

### 1-3. STONKS SILO

対象ファイル: `discover/stonks-silo/src/analyzer.py`（`DeficitQuality`/`RunwayAnalysis`/`ProfitabilityPath`/`StonksAnalysis`データクラス定義）、
`discover/stonks-silo/src/pipeline.py`（`_to_dict()`で全dataclassフィールドをJSON化、`valuation`/`financial_vectors`/`records`を追加）、
`docs/value-monitor/stonks-silo/index.html`、`docs/value-monitor/stonks-silo/data/results.json`（実データ確認済み）。

results.json構造: `{generated_at, ticker_count, tickers:{TICKER:{...}}, errors:{...}}`

#### `deficit_quality`（① 良い赤字 vs 悪い赤字）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `latest_year` | JSON出力のみ | 最新年度（未参照） |
| `revenue` | JSON出力のみ | 最新年売上生データ（未参照。表示は別途`records[yr].revenue`を使用） |
| `net_income` | JSON出力のみ | 最新年純利益（未参照、同上） |
| `revenue_growth_pct` | JSON出力のみ | 年次売上成長率系列（未参照、既知）※ステップ5調査で他サブシステム参照が判明、詳細は5-2節参照 |
| `cagr_3yr` | index.html（サマリー文、詳細パネル、ソート） | 3年CAGR |
| `rnd_ratio` | index.html（成長投資比率） | R&D/売上比 |
| `sm_ratio` | index.html（成長投資比率） | S&M/売上比 |
| `gross_margin` | index.html（テーブル・ソート・詳細） | 粗利率 |
| `gross_margin_derived` | index.html（「逆」バッジ） | 逆算値フラグ |
| `verdict` | index.html（バッジ、ソート、フィルタ用ではないがピラーラベル） | GOOD_DEFICIT等 |
| `verdict_reason` | JSON出力のみ | 判定根拠文字列（未参照。総合サマリー`summary`とは別の柱別詳細文で未表示） |
| `score` | index.html（① 赤字品質スコア表示） | 0-100点 |
| `rule_of_40` | index.html（詳細パネル） | Rule of 40 |
| `mature_profit` | index.html（成熟想定利益） | 純利益+R&D+SM |
| `mature_profit_note` | index.html（注記表示） | 「投資除外後も赤字」 |
| `sbc_adjusted_fcf` | index.html（SBC調整後FCF） | FCF-SBC |
| `sbc_ratio` | index.html（SBC比率） | SBC/売上 |
| `sbc_yoy_change` | index.html（SBCトレンド） | SBC前年比 |
| `dilution_risk` | index.html（希薄化リスクバッジ） | HIGH/MEDIUM/LOW |
| `deficit_fixed_risk` | index.html（赤字固定化リスクバッジ） | HIGH/MEDIUM/LOW |
| `revenue_outlier_years` | index.html（チャート注記） | 外れ値除去年リスト |
| `gross_margin_trend` | JSON出力のみ | improving/stable/declining（未参照、既知DESIGN-11） |
| `gross_margin_note` | JSON出力のみ | construction_phase等（未参照、既知） |
| `unit_economics_score` | JSON出力のみ | 0-100（未参照、既知） |
| `unit_economics_label` | JSON出力のみ | 優秀/良好/低調（未参照、既知） |

#### `runway`（② 生存能力）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `latest_year` | JSON出力のみ | 未参照 |
| `cash` | index.html（現金） | 現金+短期投資 |
| `monthly_burn` | index.html（月次資金消費、サマリー文） | 月次バーン |
| `runway_months` | index.html（テーブル・ソート・バー・詳細） | 生存可能月数 |
| `ocf_annual` | index.html（月次バーン注記内訳） | 年間OCF |
| `capex_annual` | index.html（同上） | 年間CapEx |
| `verdict` | index.html（バッジ・色分け） | SAFE/WATCH/DANGER |
| `verdict_reason` | JSON出力のみ | 未参照（UI側は`fmtRunway()`で独自にラベル再生成） |
| `score` | index.html（② 生存能力スコア） | 0-100点 |

#### `profitability_path`（③ 隠れ黒字化パス）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `core_profit` | JSON出力のみ | OCF+R&D+SM年次系列（未参照、既知） |
| `ocf_annual` | index.html（チャート・latestOCF） | 年次OCF |
| `ocf_yoy_change` | JSON出力のみ | OCF速度（未参照） |
| `ocf_acceleration` | JSON出力のみ | OCF加速度（未参照） |
| `ocf_trend` | index.html（バッジ・ソート・ピラーラベル） | ACCELERATING等 |
| `gaap_breakeven_year` | index.html（黒字化予測表示） | GAAP黒字化予測年 |
| `gaap_breakeven_reason` | index.html（fmtBe） | ACHIEVED等の理由コード |
| `ocf_breakeven_year` | index.html（beCell、ソート） | OCF黒字化予測年 |
| `ocf_breakeven_reason` | index.html（fmtBe） | 理由コード |
| `hidden_profit_already` | index.html（beCell、サマリー文） | 隠れ黒字化済みフラグ |
| `verdict_reason` | JSON出力のみ | GAAP/OCF理由の結合文字列（未参照。総合`summary`は別途組み立て） |
| `discontinuous_growth` | index.html（⚠注記） | 非連続成長フラグ |
| `discontinuous_growth_note` | index.html（注記本文） | 説明文 |
| `incremental_margin` | index.html（拡大再生産バー詳細） | 増分粗利率 |
| `incremental_margin_prev` | index.html（トレンド文言） | 前回増分粗利率 |
| `incremental_margin_trend` | index.html（トレンド文言分岐） | IMPROVING等 |
| `incremental_rev_delta` | index.html（拡大再生産詳細） | 売上増分 |
| `incremental_gp_delta` | index.html（拡大再生産詳細） | 粗利増分 |
| `reproduction_score` | index.html（●○ドット表示） | 0-4スコア |
| `reproduction_label` | index.html（ラベル表示） | 「極めて強い拡大再生産」等 |
| `score` | index.html（③ 黒字化パススコア） | 0-100点 |

#### `StonksAnalysis`本体・付随フィールド

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `ticker` | JSON出力のみ | 未参照（`tickers`辞書のキーと重複、UIはキー側のticker変数を使用） |
| `years` | index.html（チャートX軸、yearRange表示） | 対象年度リスト |
| `overall_score` | index.html（スコア列・バー・ソート） | 総合スコア |
| `overall_verdict` | index.html（バッジ・フィルタ・ソート） | 10x_CANDIDATE等 |
| `summary` | index.html（判定根拠テキスト展開パネル） | 総合スコア根拠文 |
| `records`（pipeline.py追加、revenue/net_income） | index.html（売上・純利益チャート） | 年次売上・純利益生データ |
| `valuation.market_cap` | index.html（valInlineHtml） | 時価総額 |
| `valuation.current_price` | index.html（株価列） | 現在株価 |
| `valuation.enterprise_value` | JSON出力のみ | 未参照（ev_sales計算に内部使用のみ） |
| `valuation.total_debt` | JSON出力のみ | 未参照（net_cash計算に内部使用のみ） |
| `valuation.psr` | index.html（valInlineHtml） | PSR |
| `valuation.ev_sales` | index.html（valInlineHtml） | EV/Sales |
| `valuation.net_cash` | index.html（valInlineHtml） | 純現金 |
| `valuation.fetched_at` | JSON出力のみ | 未参照 |
| `valuation.error` | JSON出力のみ | 未参照（取得エラー時のメッセージだがUI非表示） |
| `financial_vectors.fields.*`（Revenue/GrossProfit/RD/NetIncome/OCF/CapEx/OperatingIncome） | index.html（スパークライン・ヒートマップ・黒字化ロードマップ） | 各科目のQoQ/YoY角度・変化率・四半期系列 |
| `financial_vectors.composite` | JSON出力のみ | 全体角度・長さ（未参照） |
| `financial_vectors.data_quality` | JSON出力のみ | 利用可能/欠損フィールドリスト（未参照） |
| `financial_vectors.updated_at` | JSON出力のみ | 未参照 |
| `errors`（トップレベル） | JSON出力のみ | 取得失敗銘柄一覧（UI非表示。パイプライン運用ログ用途と推測） |

### 1-4. MACRO PULSE

対象ファイル: `src/market/macro_pulse/05_main.py`（2282行）、`docs/market-monitor/macro-pulse/index.html`（2897行）、
`data/05_events.csv` / `05_liquidity.csv` / `05_indicator_schedule.csv` / `05_weekly_analysis.csv` / `05_fed_context.csv` / `05_meta.json`。

#### 共通ヘッダー

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| last-updated（生成時刻 JST） | index.html `#last-updated` | `05_meta.json`の`generated_at` |

#### FEDレジームバー（画面上部）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| REGIME (`#rb-regime`) | regime-bar | fed_context.csv `regime`（EASING/BALANCED/TIGHTENING） |
| regime_source (`#rb-regime-src`) | regime-bar | `regime_source`（"FOMC声明分析（Grok）" or "DGS1数値ベース"） |
| FF RATE (`#rb-ff`) | regime-bar | `ff_current` |
| 1Y EXPECTED FF (`#rb-exp`) | regime-bar | `zq_rate`（実体はFRED DGS1） |
| IMPLIED CUTS (`#rb-cuts`) | regime-bar | `cuts_implied` |
| FRB主眼 (`#rb-concern`) | regime-bar | `dominant_label`（fallback: `dominant_concern`） |
| 判断理由 (`#rb-reason`) | regime-bar | `ai_reason` |
| FOMC日付ツールチップ | regime-bar (data-info-text) | `fomc_date` |

#### ティッカー

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| S&P500 現在値・前日比 | ticker `#tk-sp`/`#tk-sp-c` | events.csv 各行の`sp500_t0`から最新2営業日を抽出 |
| 10Y-2Y SPREAD・INVERTED/FLAT/NORMAL判定 | ticker `#tk-yc`/`#tk-yc-i` | indicator="Yield Curve 10Y-2Y"の`actual` |
| HY SPREAD | ticker `#tk-hy` | indicator="HY Spread"の`actual` |
| LAST UPDATE 日付・データソース | ticker `#tk-last`/`#tk-src` | 最新イベントの`release_date`/`data_source` |

#### 💧 流動性モニター

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| M2マネーサプライ（値/前月比/パーセンタイル/ベクトル/コメント） | liq-wrap カード | liquidity.csv `m2` |
| NET LIQUIDITY（同上） | liq-wrap カード | `net_liquidity` = (WALCL-TGA-RRP)/1e6 |
| HYスプレッド（同上、tickerとは別建て） | liq-wrap カード | `hy_spread` |
| FRBバランスシート（同上） | liq-wrap カード | `fed_balance`（WALCL） |
| Hollow Rallyバッジ | liq-wrap 上部 | S&P5日騰落率とnet_liquidity週次変化の組合せ判定（実質常時非表示、詳細は5-4節参照） |
| ステルス流動性 Layer1（FRB政策意図） | stealth-card | fed_context.csv `regime` |
| ステルス流動性 Layer2（供給/吸収/中立バッジ） | stealth-card | liquidity.csv `stealth_signal` |
| ステルス流動性 Layer3（NET流動性トレンド▼表示） | stealth-card | `net_liq_decline_weeks` |
| 警戒アラート文 | stealth-card | `stealth_alert`（`\|`区切り） |
| REPO残高(RRPONTSYD) 値・前週比 | stealth-card | `rrp` |
| 準備預金(WRBWFRBL) 値・前週比 | stealth-card | `reserve_balance` |
| TGA残高(WTREGEN) 値・前週比 | stealth-card | `tga` |
| ステルス吸収週数表示 | stealth-card テキスト | `stealth_absorb_weeks` |

#### ① 景気フェーズ判定

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| フェーズbadge（拡張/踊り場/後退入口/後退） | phase-wrap | events.csv 8指標から算出したスコアの区分 |
| RECESSION RISK SCORE（0-100） | `#pg-score-num` | 8指標加重平均スコア |
| スコアバー・境界線(25/52/70) | phase-bar | 同上 |
| シグナルテキスト（後退/注意カウント） | `#pg-signal-text` | 同上 |
| ⚠ALERTバナー | `#pg-alert` | bearCount≥3 かつ score≥52 で表示 |
| 8指標シグナルグリッド（値/BULL・注意・後退バッジ/先行月数/ツールチップ） | `#pg-signals` | YC 10Y-2Y(20%), HY Spread(15%), Building Permits(10%), Philly Fed Mfg(18%), CFNAI MA3(12%), Initial Claims(10%), Michigan Sent.*(8%), Sahm Rule(7%) |
| スコア比較バー（3ヶ月前/2ヶ月前/前月末/先週/カスタム日） | compare-bar | 各時点でのスコア再計算＋差分 |
| "?見方" ヘルプパネル | `#scoreHelp` | スコア定義・指標ウェイト表・解釈区分表（静的テキスト） |

#### マクロサプライズバナー（DESIGN-13）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| サプライズアラート一覧（カテゴリバッジ付き） | `#surpriseBanner` | weekly_analysis.csv 最新行の`surprise_alerts`（`;`区切り） |

#### AI WEEKLY COMMENTARY

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| 週次カード（日付/スコア/フェーズ/週差月差） | `#aiTimeline` | weekly_analysis.csv `analysis_date`,`score`,`phase`,`score_change_1w`,`score_change_1m` |
| 総括 | ai-card | `summary` |
| 要因分析 | ai-card | `factor_analysis` |
| 注視ポイント | ai-card | `watchpoints` |
| 各指標コメント＋週差/月差バッジ | ai-card | `indicator_comments` + `indicator_deltas` |
| model名・updated_at | ai-card 末尾 | `model`,`updated_at` |

#### ② 各指標の現在地（Indicator Health Bars）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| 8指標のバー（値・BULL/CAUTION/NEUTRAL/BEAR・閾値ラベル） | `#l2Grid` | YC 10Y-2Y, HY Spread, Philly Fed Mfg, CFNAI MA3, Sahm Rule, Initial Claims 4WMA, Michigan Sentiment, Building Permits（閾値はHTML内`L2_CFG`にハードコードされた別定義） |

#### ③ RECESSION RISK SCORE 推移

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| スコア時系列折れ線＋NBER景気後退期網掛け（通常/外生ショック）＋フェーズゾーン背景 | `#scoreHistoryChart` | 各時点のスコア再計算値の時系列 |
| 期間切替ボタン（1年/3年/5年/全期間） | score-range-btn | 表示期間フィルタ |

#### ④ 過去の後退局面との類似度

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| レーダーチャート（現在/スライダー日/2019-11/2001-09） | `#l3Chart` | 8指標を0-100正規化 |
| 類似度スコア(%)＋説明文 | `#l3Scores` | ユークリッド距離ベースの類似度 |
| スライダー（過去に戻る）・時点別スコア・再生ボタン | `.l3-slider-wrap` | 過去スナップショット再生機能 |

#### ⑤ 直近の動き（RECENT SIGNALS、過去90日）

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| DATE, INDICATOR, ACTUAL, PREV, DIR(↑↓→), CHANGE | `#recentSignals` テーブル | events.csv 各指標の直近発表実績（デイリー指標除く） |

#### ⑥ 今後2週間の発表スケジュール

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| DATE, INDICATOR, DAYS(TODAY/+Nd), CONSENSUS | `#schedGrid` テーブル | 05_indicator_schedule.csv `release_date`,`indicator`,`consensus` |

### 1-5. Discover

対象ファイル: `src/discover/catalyst.py`, `collect.py`, `impact_predictor.py`、
`docs/discover/{index,catalyst,news_history,admin}.html`、
実データ`docs/discover/data/{catalyst.json, daily_report.json, impact_predictions_2026_07.json, macro_themes_history.json, news_history_2026_07.json}`。

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `catalysts[].title` | catalyst.html | カタリスト短縮タイトル |
| `catalysts[].detail` | catalyst.html (ci-detail) | 詳細説明100字以内 |
| `catalysts[].timing` | catalyst.html (ci-timing) | 想定時期 |
| `catalysts[].importance` (高/中/低) | catalyst.html バッジ | 重要度、フィルター対象 |
| `catalysts[].type` (確定イベント/不確定シナリオ) | catalyst.html バッジ | 種別、フィルター対象 |
| `catalysts[].probability` (高/中/低) | catalyst.html バッジ | 実現確率 |
| `catalysts[].status` (未達/達成済み/消滅) | catalyst.html バッジ・フィルター | ステータス、達成済み/消滅は折りたたみ表示 |
| `catalysts[].first_detected` | catalyst.html (ci-detected "初回:") | 初回検出日 |
| `catalysts[].id` | (画面非表示、内部キー) | impact_predictions紐付け用ID |
| `tickers{}.updated_at` | catalyst.html (tc-updated) | 銘柄単位の最終更新日 |
| 影響予測 `direction`(positive/negative/neutral) | catalyst.html, news_history.html renderImpact | 株価影響方向（矢印） |
| 影響予測 `magnitude`(高/中/低) | 同上 | 影響度合い |
| 影響予測 `thesis_effect`(補強/弱化/中立) | 同上 | 保有テーゼへの影響 |
| 影響予測 `summary` | 同上 | 30字要約 |
| `tickers{}.category`(保有中/監視中/様子見) | index.html バッジ・フィルター・ソート | 銘柄区分 |
| `tickers{}.memo` | index.html (tc-memo) | メモ |
| `top_importance` | index.html バッジ・ゾーン振り分け | 要注目/通常/なしゾーンの判定に使用 |
| `classified.items[].title/category/importance/summary/url/source/published_at` | index.html news-item、news_history.html | ニュース個票（分類・要約・出典・日付） |
| `classified.summary` | index.html (tc-summary見出し) | 全体要約 |
| `classified.conditions_met[]` | index.html conditions-panel「📋通過条件」 | スクリーニング通過条件 |
| `classified.risk_flags[]` | index.html conditions-panel「⚠️リスクフラグ」 | リスク要因 |
| `candidates[].ticker/company/sector/reason/risk` | index.html cand-card | 新規候補基本情報 |
| `candidates[].screening_pass[]` | index.html screen-passバッジ | 通過条件バッジ群 |
| `candidates[].catalyst_type` | index.html cand-catalystバッジ | カタリスト種別 |
| `candidates[].conviction`(高/中/低) | index.html convバッジ | 確信度 |
| `macro_themes[].theme/horizon/conviction/background/catalyst` | index.html theme-card | テーマ名・時間軸・確信度・背景・トリガー |
| `macro_themes[].related_tickers[].ticker/role/note` | index.html buildRelatedTickers | 関連銘柄（主要/ボトルネック/注目でグループ化） |
| `macro_themes[].sources[].title/url` | index.html「情報源：」 | 根拠情報源 |
| `macro_themes[].generated_at` | index.html「生成日」+連続登場週数バッジ | 生成日、過去4週との突合で連続登場を判定 |
| `macro_themes_history.json` | index.html 過去テーマ折りたたみ表示 | 直近4週の過去テーマ一覧 |
| `price_change_next_day` | news_history.html (tc-change ↑/↓%) | 翌営業日の株価騰落率 |
| theme_config/discover_config (`id/label/color`, `category/themes/memo`) | admin.html エディタ | テーママスタ・銘柄テーマ割当編集 |

### 1-6. EPS Analyzer

対象ファイル: `src/value/adjusted_eps_analyzer/{pipeline.py, maturity_monitor.py, eps_calculator.py}`、
`docs/value-monitor/adjusted_eps_analyzer/{index,stock,tickers,admin}.html`、
実データ`docs/value-monitor/adjusted_eps_analyzer/data/{summary.json, AAPL/quarterly.json}`。

| 項目名 | 出力先 | 内容説明 |
|---|---|---|
| `ticker` / `company_name` / `latest_filing_date` | index.html, tickers.html, stock.html | 銘柄コード・社名・決算日 |
| `gaap_eps` / `adjusted_eps` | 全画面 | GAAP EPS / Non-GAAP調整後EPS |
| `eps_diff`（adj−gaap） | index.htmlのみ「差分額」列 | GAAPとAdjの差額 |
| `eps_ratio`（%） | index.htmlのみ「差分比率」列、デフォルトソート・ピン表示・投資機会スコアに使用 | 差分比率 |
| `gaap_to_adj_positive` | index.htmlのみ「⚡黒字転換」バッジ・フィルター | GAAP赤字→Adj黒字の判定 |
| `yoy_growth` | index.html, tickers.html | 前年同期比成長率 |
| `health`（調整なし/小/中/大/過大調整/調整小マイナス） | index.html, stock.html（バッジ色分け） | EPS差分比率に基づく調整健全性分類（`ai_analysis.health`とは別概念、5-6節参照） |
| `deviation_rate`（TANUKI latest.json `upside_percent`から算出） | index.htmlのみ「乖離率」列・ピン表示・投資機会スコアのdevBonus | TANUKI理論株価との乖離率 |
| `quarters[].gaap_net_income` / `adjusted_net_income` | stock.html ウォーターフォール図 | 純利益（GAAP/調整後） |
| `quarters[].diluted_shares_used` | (表示自体はされないがEPS算出根拠) | 希薄化後株式数 |
| `quarters[].adjustments[].item_name` | stock.html 調整内訳テーブル「項目」列 | 調整項目名 |
| `quarters[].adjustments[].net_amount` | 同上「金額（税後）」列＋ウォーターフォール棒 | 税効果適用後の調整額 |
| `quarters[].adjustments[].reason` | 同上「理由」列 | 調整理由 |
| `quarters[].adjustments[].extracted_from` | 同上「抽出元」列（タグpill） | 元XBRLタグ名 |
| `quarters[].filing_date` / `period_end` / `fiscal_year` / `quarter` | チャートラベル（年度-Q表記）、調整ブロック見出し | 決算期表示 |
| `quarters[].ai_analysis.health/comment` | stock.html AI分析欄・ヘッダーバッジ | AIによる調整健全性コメント |
| `quarters[].ai_analysis.sources[].item/snippet/confidence` | 引用ソースリスト＋確信度バー（調整内訳テーブルにも転用） | 一過性判定の根拠・確信度 |
| `quarters[].special_flags`（EPS_DISCREPANCY） / `special_notes.eps_discrepancy` | stock.html GAAP EPSカードの⚠️アイコン・ツールチップ | Alpha Vantage公式値とXBRL計算値の乖離警告（SOUN/CELH等） |
| `next_earnings_date`（tanuki latest.json） | stock.html「次回決算」 | 次回決算予定日 |
| `components.per` / `components.per_adjusted`（tanuki latest.json） | stock.html PER比較パネル | GAAP/調整後PERとその乖離 |
| `ttm.json`（TTM系列） | stock.html TTMタブのチャート | 直近12ヶ月集計 |

## ステップ1: 共通項目候補グルーピング（11群）

**① 乖離率／IV比 系**
- TANUKI: `upside_percent`, `upside_percent_beta`, `upside_percent_rf`
- HypeCore: `price_iv_ratio`（株価÷TANUKI理論株価）
- EPS Analyzer: `deviation_rate`（TANUKI `latest.json`の`upside_percent`から画面側で再計算）
→ 同一概念がTANUKI本体・HypeCore・EPS Analyzerの3箇所に分散。特にEPS Analyzerは独自再計算で、TANUKI側の値を直接使っていない。（→ステップ2〜4で実データ突合済み）

**② 信頼性／品質判定バッジ系**
- TANUKI: DCF_Reliability(Policy A/B), `fcf_outlier.detected`, `growth_sanity.verdict`, `validation.checks`
- STONKS SILO: `deficit_quality.verdict`, `runway.verdict`, `profitability_path.verdict`, `dilution_risk`, `deficit_fixed_risk`
- MACRO PULSE: `regime`, `stealth_signal`
→ 6サブシステムそれぞれが独自の「信頼度／状態バッジ」体系を持ち、用語・閾値・粒度が統一されていない。（→ステップ2〜4で統一可否検討済み）

**③ 成長率系**
- TANUKI: `growth.rate/source`, `growth_scenarios.primary`, `recommended_g`, `phase1_growth_*`
- HypeCore: `rev_yoy`, `revenue_growth`
- STONKS SILO: `cagr_3yr`, `revenue_growth_pct`, `ocf_yoy_change`
→ 「成長率」概念が各サブシステムで異なる期間・計算式のまま個別保持。同一銘柄でも値が一致しない可能性（次ステップの検証対象）。

**④ 総合スコア／判定系**
- TANUKI: `tanuki_score`, `funda_score`, `timing_score`, matrix quadrant
- HypeCore: `stage`(0-4)
- STONKS SILO: `overall_score`, `overall_verdict`
- MACRO PULSE: RECESSION RISK SCORE(0-100)
- EPS Analyzer: `health`（調整健全性5段階）
→ 6サブシステム全てが独自の「総合判定」を持つが統一スコア基盤はない。

**⑤ アナリストコンセンサス／マルチプル系（PER/PEG/PSR/EV_EBITDA）**
- TANUKI: `components.per/peg_ratio/ps/ev_ebitda/analyst_target_*`
- HypeCore: `forward_pe`, `peg_ratio`, `psr`, `ev_ebitda`, `analyst_upgrade_rate`, `recommendation_mean`, `buy_hold_ratio`
- STONKS SILO: `valuation.psr`, `ev_sales`
→ 同一マルチプルが3サブシステムで別々に取得・保持。（→ステップ2〜4で実データ突合済み）

**⑥ モメンタム/複合トレンド系**
- HypeCore: `momentum_score`, `expectation_score`, `fundamental_score`（Zスコア方式）
- STONKS SILO: `financial_vectors.fields.*`（ベクトル角度方式）
→ 概念（複数指標の合成トレンド）は類似だが実装方式が全く異なる。

**⑦ FCF/キャッシュフロー系**
- TANUKI: `fcf_base`, `fcf_outlier`, `fcf_estimation`, `fcf_history`, `dcf_components`
- STONKS SILO: `profitability_path.ocf_annual`, `sbc_adjusted_fcf`, `incremental_margin`
→ 同一企業のFCFをDCF用途とサバイバル分析用途で別々に取得・加工。

**⑧ 次回決算日**
- TANUKI: `next_earnings_date`
- EPS Analyzer: `next_earnings_date`（TANUKIの`latest.json`から取得、実質1系統）

**⑨ インサイダー/空売り系**
- TANUKI: `components.insider_*`
- HypeCore: `short_pct_float`, `buy_hold_ratio`

**⑩ リスクイベント／カタリスト系**
- TANUKI: `risk_events[]`（Grok検索の簡易版）
- Discover: `catalysts[]`, `macro_themes[]`（確度・時期・影響予測付きではるかに詳細）
→ 概念は類似も粒度に大差。

**⑪ マクロ環境認識系**
- MACRO PULSE: `regime`, RECESSION RISK SCORE
- Discover: `macro_themes[]`
- TANUKI report.txt: `erp`, `forward_earnings_yield`
→ 個別銘柄分析側とマクロ専用サブシステムが部分的に重複した市場環境情報を独自算出。

## ステップ1: 削除候補リスト（サブシステム別）

### TANUKI VALUATION（16件、一部は後にステップ5で「削除候補ではなかった」と訂正、下記参照）

DCF_Reliability（Policy A/B判定結果全体。`pipeline.py`の`_calc_dcf_reliability_policy_b()` 426-472行、latest.jsonに構造化フィールドとして一切保存されていない）。
`growth_sanity.industry_benchmark／growth_model／growth_model_reason`（`check_growth_sanity()`呼出711-727行、latest.json保存もstock.html非表示）。
R&D資本化／Software_System分類見直し警告（`rd_capitalization`, `software_system_reclassification`, `software_system_provisional`、report.txt[3]のみ、stock.html非表示）。
CIK断絶警告（`CIK_DISCONTINUITY_TICKERS`辞書、pipeline.py 93-109行、report.txtヘッダーのみ）。
segment_configuredフラグ（`_load_extra_data`内保存、stock.html・index.html双方未参照）。
`net_current_assets_ratio`（pipeline.py約2560行、シガーバット指標、全画面未参照）。
`financial_health.buyback_ttm`（pipeline.py約2541行、cash-trap detection用とコメントあるが対応ロジックなし）。
`financial_health.cash_missing`（pipeline.py約2392行）。
`financial_health.shares_yr_3ago_label`（pipeline.py約2503-2505行）。
`financial_health.split_adjusted／split_factor`（pipeline.py約2507-2508行）。
`dupont.ni_ttm／revenue_ttm／total_assets／equity／dupont_bs_period／reliability／reliability_reason`（`_load_extra_data`内、約2581-2619行、ni_ttmのみmax_eps算出に間接利用）。
`erp／forward_earnings_yield`（latest.jsonトップレベル、約939-940行、report.txt[7]は独自再計算）。
`fcf_source／fcf_ttm_periods／rice_data_source`（core_calculator.py出力）。
`growth.source／growth.phase1_years`（トップレベル`growth`サブフィールド）。
`phase1_growth_original`。
トップレベル`matrix`オブジェクト（stock.html/index.html範囲では未参照、別画面tanuki_score/index.htmlで使用の可能性あり、要件外のため未検証）。

**注記**: `tanuki_score`, `funda_score`, `score_comment`, `timing_score`, `sell_reason`, `pre_rounding_score`, `pre_rounding_comment`, `rounded_by_policy`はstock.html・index.html(tanuki_valuation)で0件ヒットだが、別画面`tanuki_score/index.html`で消費されている可能性が高く削除候補には含めない。

### HypeCore（16件、うち`stage_label`と`expectation_score`はステップ5で「削除候補ではなかった」と訂正）

`ma50_cross`（hypecore.py:446、完全デッドコード、JSON出力にも含まれず他所でも未参照）。
`stage_label`（hypecore.py:880、~~JSON出力されるがフロントは独自定義~~ ※ステップ5訂正: TANUKI VALUATION側から`pipeline.py:3059-3060,3112`・`tanuki_score/index.html:481,517,576`で読取使用されており削除候補から除外）。
`sell_on_good_news`（hypecore.py:452-459,905、JSON化されるがdetail.html/index.htmlどちらも参照せず）。
`low_base_effect`（hypecore.py:838-843,920、同上）。
`ma50_dev`（JSON出力883行、未参照）。
`volume_ratio`（JSON出力886行、未参照）。
`ni_yoy`（JSON出力890行、内部でfundamental_score計算にのみ使用）。
`earnings_growth`（JSON出力898行、`determine_stage`898/535行`earn_growth`変数、JSON未参照かつPython側でも代入のみで条件未使用の二重デッドコード）。
`recommendation_mean`（JSON出力899行、JSON表示は未参照だがPython側S1判定条件636行で使用）。
`short_pct_float`（JSON出力900行、同上、S0判定条件608行で使用）。
`analyst_downgrade_rate`（JSON出力904行、未参照）。
`buy_hold_ratio`（JSON出力906行、JSON表示未参照だがS1判定条件636行で使用）。
`expectation_score`／`fundamental_score`／`momentum_score`（JSON出力913-915行、いずれもJSON未参照。expectation_scoreは~~JSON未参照~~ ※ステップ5訂正: TANUKI `stock.html:667,670-698`で「期待プレミアム」パーセンタイル表示に使用されており削除候補から除外。fundamental_score/momentum_scoreは判定条件内利用のみで削除候補のまま）。
`ticker`（トップレベル、run_poc結果dict925行、フロントはループ変数/URLパラメータのtickerを使い未参照）。
`generated`（トップレベル、同926行、`generated_at`に置き換わり未参照）。
`tickers.json`の`updated_at`/`count`（`_save_tickers_index()` 971-975行、index.htmlは`idx.tickers`のみ使用）。

### STONKS SILO（12件、うち`deficit_quality.revenue_growth_pct`はステップ5で「削除候補ではなかった」と訂正）

`gross_margin_trend`/`gross_margin_note`/`unit_economics_score`/`unit_economics_label`（analyzer.py:64-67 DESIGN-11実装、算出285-356行、UI未参照）。
`revenue_growth_pct`（analyzer.py:38、算出196-212行、~~UI未使用~~ ※ステップ5訂正: TANUKI `stock.html:2907-2912`（Matrix③成長性系パネルのY軸）で使用されており削除候補から除外）。
`core_profit`（analyzer.py:92、算出558-568行、UI未参照）。
`verdict_reason`（3箇所: DeficitQuality/RunwayAnalysis/ProfitabilityPath、analyzer.py:49,83,109、各柱の詳細判定根拠文字列だがUIには一切表示されず）。
`latest_year`（DeficitQuality/RunwayAnalysis、analyzer.py:33,75、UI未参照）。
`revenue`/`net_income`（DeficitQuality、analyzer.py:34-35、算出185-187行、UIは代わりに`records[yr].revenue/net_income`を使用しており重複）。
`ocf_yoy_change`/`ocf_acceleration`（ProfitabilityPath、analyzer.py:96-97、算出570-596行、UI未参照、CLIの`__main__`ブロックでのprint表示にのみ使用）。
`valuation.enterprise_value`/`total_debt`/`fetched_at`/`error`（pipeline.py:135-145、UI未参照）。
`financial_vectors.composite`/`data_quality`（financial_trend_calculator.py`compute_vectors`が生成、pipeline.py:181で結合、UI未参照）。
`ticker`（StonksAnalysis本体フィールド、analyzer.py:130、pipeline.py:110、`tickers`辞書のキーと重複、UI未参照）。
`errors`（トップレベル、pipeline.py:192、UI（index.html）には表示ロジックなし）。

### MACRO PULSE（15件）

`INDICATOR_CONFIG.threshold_bull/threshold_bear`（05_main.py 197-327行目、全12指標で定義されるがどこからも読まれない。HTML側は`L2_CFG`に独自の`bull`/`bear`をハードコードした別定義があり二重管理）。
`unit`（全指標で定義されるが参照箇所皆無）。
`discord_remind`（全指標で`False`固定、読み取り箇所なし）。
`michigan_rule`（246,257,269行目）/`permit_rule`（281行目）フラグ（実際の発表日計算は別ハードコード関数が行っており未参照）。
`_SURPRISE_THRESHOLDS`内の`Michigan Inflation 5Y`閾値（0.30、116行目、`detect_macro_surprises()`内の`_DAILY`セット132行目で先に除外され到達不能）。
`analysis`列（events.csv、`EVENTS_COLUMNS`に定義されるが書き込み処理でも一切値を設定するコードがなく常に空文字、完全な死に列）。
`regime, ff_rate, yc_10y2y, hy_spread, vix, cuts_implied`（イベント発表時点の金融環境スナップショット列、HTML側`COL`マッピングは定義のみで実使用箇所なし）。
`sp500_t1〜sp500_t20, ret_t1〜ret_t20`（市場反応t+N日、`fill_returns()`で算出、`COL.sp1`/`COL.ret1`は定義のみで未参照、t5/t10/t20系は定義すらされておらず完全未使用）。
`surprise_pct`（`COL.surprise_pct`として定義されるが参照箇所なし）。
`forecast_source`（`COL.src`は`applyForecasts()`内での書き込みのみで画面表示には使われない）。
VIX指標（毎日FRED取得しevents.csvに記録されるが、ticker・②健康バー・①フェーズゲージ8指標・④類似度レーダーのいずれにも含まれずダッシュボード上で表示場所がない）。
Michigan Inflation 5Y（T5YIE、`DAILY_INDICATORS`かつ`SCHED_EXCLUDE`の両方に含まれ「直近の動き」表にも「発表スケジュール」表にも出ず、スコアリング/②/④にも未使用）。
`status`, `fred_id`, `input_method`列（05_indicator_schedule.csv、`renderSchedule()`は`release_date`/`indicator`/`consensus`のみ参照）。
`zq_ticker`, `zq_price`（05_fed_context.csv、`renderRegimeBar()`では`zq_rate`のみ使用）。
Hollow Rally検知バッジ（動作していない機能。判定コードは`sp500`列を`liquidity.csv`から探すが実際のスキーマに`sp500`列は存在せず、条件が常に満たされず実質常時非表示）。

### Discover（4件）

`candidates[].market_cap_b`/`revenue_growth_pct`/`institutional_ownership_pct`（collect.py `explore_candidates()` L230でGrokに収集させているがindex.htmlの候補カード構築L559-570で未参照、既知）。
`catalysts[].last_updated`（catalyst.py `process_ticker()` L202でstatus変更時に更新するが、catalyst.html `renderItem()` L319-341は`first_detected`のみ表示し未参照、新規発見）。
news_history_*.jsonの日次・銘柄単位`conditions_met`/`risk_flags`（collect.py `append_to_monthly_history()` L357-358で保存されるがnews_history.htmlのrender()では一切参照されない、新規発見）。
news_history_*.jsonの`top_importance`（日次・銘柄単位、同上、軽微）。

### EPS Analyzer（13件）

`quarters[].maturity_monitor`（alert/sbc_contribution/sbc_to_revenue/sbc_per_share/sector_threshold全項目、pipeline.py L559-576、maturity_monitor.py L79-85で計算・最新四半期に保存、4画面いずれからも未参照、既知・48銘柄で実データ確認済み）。
tickers.htmlの`eps_diff`/`eps_ratio`/`deviation_rate`列（tickers.html columns定義L252-294に存在しない）。
stock.htmlのTANUKI乖離率（`upside_percent`、`updateTanukiInfo()` L592-630は`next_earnings_date`とPER比較のみ使用）。
`gaap_to_adj_positive`のtickers.html非表示（index.htmlのみ⚡黒字転換バッジで使用）。
`quarters[].sector`/`sector_exclusions[]`（全四半期に付与されるが4画面いずれのHTMLからも参照なし）。
`quarters[].revenue`（全四半期に保存されるが未表示）。
`quarters[].tax_expense`/`pretax_income`（同上）。
`quarters[].diluted_shares`（raw、`diluted_shares_used`とは別キー、保存されるが未参照）。
`adjustments[].item_id`/`amount`（税前生値）/`unit`/`direction`/`pre_tax`/`category`/`tax_rate_applied`（`buildAdjHtml()`はitem_name/net_amount/reason/extracted_from/confidenceのみ表示）。
`quarters[].form`（10-Q/10-K、`q-block-hdr`はfiling_dateのみ表示）。
`quarters[].dta_detected`/`split_adjusted`フラグ（`apply_dta_adjustments()` L264、`apply_split_adjustments()` L200で設定、画面上どこにも出ない）。
`docs/value-monitor/adjusted_eps_analyzer/data/{ticker}/annual.json`全体（`aggregate_annual()`で生成・保存L636-638、4画面のいずれもfetchしておらず年次集計データが完全に死んでいる、重要度高）。

## ステップ2〜4: 統一定義・実データ突合・データ要件検証

### ①乖離率／IV比

#### 各値の正確な計算式

**TANUKI VALUATION `upside_percent`**（`calculator/adjustments.py:662-669`）:
```python
def calculate_upside(intrinsic_value_per_share, current_price):
    if current_price <= 0:
        return 0.0
    return ((intrinsic_value_per_share / current_price) - 1) * 100
```
分子＝理論株価、分母＝現在株価。プラス＝割安。メイン理論株価はβ込みWACCではなくRm（市場期待リターン）で割り引いたDCFから算出（`core_calculator.py:613-616`のコメント: 「β込みWACCは市場の評価を割引率に持ち込むため『市場から独立した本質的価値』という目的と矛盾する」という設計意図が明記）。`core_calculator.py:641-645,799`で計算・出力。参考値として`upside_percent_beta`（788-789行）、`upside_percent_rf`（791-792行）も併記。

**HypeCore `price_iv_ratio`**（`hypecore.py:406`）: `df["price_iv_ratio"] = df["price"] / df["iv"]`（TANUKIとは逆で株価÷理論株価）。TANUKIのIV取得は`fetch_tanuki_iv`（186-220行）が`history/*.json`と`latest.json`から`intrinsic_value_per_share`を取得。TANUKIの`upside_percent`は一切参照せず`intrinsic_value_per_share`のみ取得して独自比率計算。株価は`fetch_price_data`（70-73行）で`yfinance`から独自取得しTANUKIの`current_price`とは完全に別ルート・別タイミング。

**EPS Analyzer `deviation_rate`**: pipeline.pyには計算が存在しない。`docs/value-monitor/adjusted_eps_analyzer/data/summary.json`に`deviation_rate`フィールド自体が含まれない。実際の計算はフロントエンドJS（`index.html:230-237`）がページ表示時にTANUKIの`latest.json`をライブfetchして`t.deviation_rate = up/100`（237行）と算出。表示は`fmtPct()`で×100して戻すため画面表示値はTANUKIの`upside_percent`と完全に同一（独自計算・丸め差分なし）。補足: `docs/common/glossary.json:18`、`src/tail/quarterly_review_generator.py:161`も同じくTANUKIの`upside_percent`を直接引用するパススルー実装。

#### 実データ横断突合（7銘柄: AAPL/MSFT/AMZN/META/TSLA/GOOGL/NVDA）

| 銘柄 | TANUKI upside_percent（算出日時） | HypeCore price_iv_ratio→換算乖離率（生成日時） | EPS Analyzer deviation_rate | HypeCore−TANUKI 差分(pp) |
|---|---|---|---|---|
| AAPL | -61.9%（2026-07-22 00:51） | ratio=2.663→-62.45%（2026-07-19 23:26） | -61.9% | -0.55 |
| MSFT | -4.6%（2026-07-22 00:57） | ratio=1.034→-3.29%（2026-07-19 23:27） | -4.6% | +1.31 |
| AMZN | -48.7%（2026-07-22 00:51） | ratio=1.932→-48.24%（2026-07-19 23:26） | -48.7% | +0.46 |
| META | +22.5%（2026-07-22 00:56） | ratio=0.810→+23.46%（2026-07-19 23:27） | +22.5% | +0.96 |
| TSLA | -87.0%（2026-07-22 01:00） | ratio=7.665→-86.95%（2026-07-19 23:27） | -87.0% | +0.05 |
| GOOGL | -30.8%（2026-07-22 00:55） | ratio=1.432→-30.17%（2026-07-19 23:27） | -30.8% | +0.63 |
| NVDA | +276.6%（2026-07-22 00:57） | ratio=0.261→+283.14%（2026-07-19 23:27） | +276.6% | **+6.54（最大）** |

EPS Analyzerの差分は常に0（ライブfetchでTANUKI値をそのまま流用のため原理的に一致）。HypeCoreとTANUKIの差の原因: 生成日時が3日ずれている（HypeCore 07-19 vs TANUKI 07-22）。この間の株価変動がHypeCore側`price`とTANUKI側`current_price`の差になる（例: AAPL 333.74 vs 328.82、NVDA 202.81 vs 205.905）。IV自体はHypeCoreも`latest.json`から直接読むためほぼ一致（NVDA逆算: HypeCore側iv=777.05 vs TANUKI iv=775.35、差0.2%程度）。差分の主因は株価スナップショットのずれであり、乖離率が大きい銘柄ほど価格変化の影響が%換算で増幅される（NVDAはupside 276%＝IV/price比が約3.75倍のため1.5%の価格差が6.5ppの乖離率差に増幅）。計算式のバグではなく非同期な株価取得タイミングによる誤差。

#### 統一定義の提案

TANUKI VALUATIONの`upside_percent`（`latest.json`）を唯一の正とし、HypeCoreとEPS Analyzer（および`tail`モジュール）は独自計算をやめてこの値を直接参照する。EPS Analyzerは既に実質この方式（現状維持が望ましい）。HypeCoreの`price_iv_ratio`算出自体（時系列トレンド分析目的）はHypeCore独自の月次価格系列を使う設計は妥当だが、「最新月」の値だけはTANUKIの`latest.json`の`components.current_price`と`upside_percent`をそのまま採用する形にすれば、最新値に限り3システムで完全一致させられる（過去の月次履歴はHypeCore独自のままでよい）。

必要データ項目: `latest.json`の`upside_percent`、`intrinsic_value_per_share`、`components.current_price`、`calculation_date`。

統一が難しい部分: HypeCoreの過去月次系列は時系列トレンド判定に使うためTANUKIの過去`history/*.json`に依存する現状設計は妥当。各システムの生成バッチタイミングが独立している（TANUKIは毎日再計算、HypeCoreは別スケジュール）ため「完全リアルタイム同期」を望まなければ、最低限「参照元JSONの`calculation_date`を全画面に併記する」運用ルールが現実的な落としどころ。

#### 正確性確認で見つかった問題点

1. `docs/value-monitor/adjusted_eps_analyzer/data/{ticker}/summary.json`は存在しない（想定と異なる）。実際は`data/summary.json`（全銘柄横断の単一ファイル）であり`deviation_rate`フィールド自体もこのファイルには含まれず、フロントエンドJSがページ表示のたびにTANUKIの`latest.json`をライブfetchして初めて生成される値。サーバ側にキャッシュされた`deviation_rate`は存在しない。
2. HypeCoreの`price_iv_ratio`はTANUKIの`upside_percent`を全く参照していない独自計算（設計上は妥当）。
3. NVDAで6.5ポイントの乖離。原因はバグではなくHypeCore生成日時（07-19）とTANUKI算出日時（07-22）の3日ギャップによる株価スナップショットのずれ。upside_percentが大きい銘柄ほどこの価格ずれが%換算で増幅される点は利用者への注意喚起が必要（HypeCore画面上に「TANUKI IV基準日」を明示すべき）。
4. EPS Analyzerの`summary.json`の`last_updated`は2026-07-20で、TANUKIの最新計算（07-22）より2日古い。`eps_diff`/`eps_ratio`/`health`等はこの古い日付のまま固定表示される一方、`deviation_rate`だけはページ閲覧時に常に最新のTANUKI値を取得するため、同一画面内で「EPS指標は2日前」「乖離率は最新」という鮮度の不一致が生じている。
5. TANUKIの`latest.json`はメインの`upside_percent`（Rmβなし）以外に`upside_percent_beta`、`upside_percent_rf`の3種類の乖離率を保持しており、他システムがどのバージョンを参照すべきか明示的な取り決めがコード上にない。

### ⑤マルチプル系（PER/PEG/PSR/EV_EBITDA）

#### 各値の正確な計算式・データソース

**TANUKI VALUATION**（`data_fetcher.py:513-541`）:
```python
_trailing_pe = info.get("trailingPE")
_forward_pe  = info.get("forwardPE")
per = _trailing_pe or _forward_pe or None        # trailing優先、forwardフォールバック
per_is_forward = (_trailing_pe is None or _trailing_pe <= 0) and _forward_pe is not None and _forward_pe > 0
peg_raw = info.get("pegRatio") or None
ps_raw = info.get("priceToSalesTrailing12Months") or None
ev_ebitda_raw = info.get("enterpriseToEbitda") or None
if ev_ebitda_raw is not None and ev_ebitda_raw > 0:   # 負値は捨てる
    ev_ebitda = float(ev_ebitda_raw)
```
いずれもyfinance `.info`の既算値をそのまま採用。PEG/PS/EV_EBITDAは正値のみ採用（負値は`None`として捨てられる）。さらに`per_adjusted`という独自指標（`core_calculator.py:930-962`）はEPS Analyzerの調整後TTM EPSを分母にした自前計算のPERで、yfinanceのGAAP trailingPEとは別基準。

**HypeCore**（`hypecore.py:110-131 fetch_info_snapshot`）:
```python
"forward_pe":  info.get("forwardPE"),        # 常にforward、フォールバックなし
"trailing_pe": info.get("trailingPE"),        # 取得はするが出力JSONに含めない
"psr":         info.get("priceToSalesTrailing12Months"),
"peg_ratio":   info.get("pegRatio"),
"ev_ebitda":   info.get("enterpriseToEbitda"),  # 負値もそのまま格納（TANUKIと真逆の方針）
```
出力JSON（`monthly[]`）に書き込まれるキーは`compute_scores`（419-421行）で`forward_pe, peg_ratio, ..., psr, ev_ebitda`のみ選定、`trailing_pe`は出力対象外。HypeCoreの"PER"は常にforward PE。

**STONKS SILO**（`valuation_fetcher.py` + `pipeline.py:119-141`）:
```python
psr = val["market_cap"] / latest_rev if val["market_cap"] and latest_rev else None
ev_sales = val["enterprise_value"] / latest_rev if val["enterprise_value"] and latest_rev else None
```
`latest_rev`は`data["records"][最新年]["pl"]["revenue_sanitized"]`（SEC EDGAR由来の年次決算revenue）であり、yfinanceのTTM revenueではない。STONKS SILOのPSR/EV_Salesは「分子＝yfinance算出のmarket_cap/EV（現在時点）」「分母＝SEC年次決算revenue（直近通期）」というハイブリッド計算で、TANUKI/HypeCoreの「yfinanceのTTM値をそのまま使う」方式とは根本的に異なる。同名`psr`でも定義が異なる点に要注意。STONKS SILOはEV/EBITDAではなくEV/Salesを持つ。

#### 実データ突合結果

TANUKIとHypeCoreは対象ティッカーがほぼ完全一致（各103銘柄）。STONKS SILO（25銘柄）は全銘柄がTANUKI/HypeCoreの103銘柄集合に完全包含。データ取得日: TANUKI=2026-07-22、HypeCore=2026-07-19（3日前）、STONKS SILO=2026-07-10（12日前・最古）。

| Ticker | TANUKI per (is_fwd) | HypeCore forward_pe | TANUKI per_adjusted | TANUKI peg | HypeCore peg | TANUKI ps | HypeCore psr | STONKS psr | TANUKI ev_ebitda | HypeCore ev_ebitda | STONKS ev_sales |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ASTS | -247.19 (F) | -222.14 | None | None | None | 293.92 | 264.13 | 401.3 | None | -56.29 | 318.9 |
| AVAV | 33.15 (T) | 31.38 | 40.14 | 1.57 | 1.57 | 3.85 | 3.64 | 3.7 | 37.98 | 37.88 | 3.9 |
| BBAI | -14.68 (F) | -14.20 | None | None | None | 11.04 | 10.68 | 12.5 | None | -16.06 | 9.9 |
| IONQ | 91.81 (T?) | -31.65 | None | None | None | 71.43 | 69.38 | 124.5 | None | -16.60 | 113.2 |
| IOT | 366.60 (T) | 42.82 | 63.97 | None | None | 12.34 | None | 13.1 | None | -16713.74 | 12.9 |
| RKLB | データなし（latest.json不存在） | 2254.00 | — | — | — | — | 62.17 | 84.7 | — | -229.88 | 77.3 |
| RXRX | -3.22 (F) | -3.13 | None | None | None | 24.20 | 23.54 | 25.0 | None | -1.95 | 18.9 |
| SOUN | -53.79 (F) | -52.25 | None | None | None | 15.29 | 14.85 | 17.1 | None | -15.89 | 15.9 |

「(F)」＝TANUKIがforward PEにフォールバックした銘柄、「(T)」＝trailing PEを使用した銘柄。

差分の切り分け: AVAV（唯一の黒字銘柄）はPEG完全一致、PER/PS/EV_EBITDAも近似——差の主因は3日間の株価変動のみと判断できロジック不一致は無い。IONQはTANUKI per=91.81（trailing疑い、GAAP一過性要因の可能性）だがHypeCore forward_pe=-31.65と符号すら逆転——trailingとforwardの基準の違いによる典型例。IONQ PSRはTANUKI/HypeCore（TTM基準）69〜71 vs STONKS SILO（SEC年次決算基準＋12日前株価）124.5と約1.75倍の乖離——(a)STONKS SILOデータが12日古くIONQ株価は同期間に約-17%下落、(b)分母がyfinance TTM revenue（新しい四半期含む）に対しSEC年次決算revenue（古い期間）を使うため急成長銘柄ほど乖離拡大。IOT ev_ebitdaはHypeCoreで-16713.74という異常値（EBITDAゼロ近傍での比率発散、TANUKIは正値フィルタで偶然回避しHypeCoreはフィルタなしで生の異常値を格納・UI表示）。IOT psrはHypeCoreがNoneなのにTANUKIは12.34——同じyfinanceフィールド参照でも3日違いの取得タイミングでyfinance側の値の有無が変わった可能性（一時的欠損、両システムともリトライ機構なし）。

#### 統一定義の提案

統一すべき部分: PEG, PS(TTM), EV/EBITDA(TTM)はyfinance `.info`の該当フィールドをそのまま使う点で3システム共通化できる。具体案: `common/`配下に1箇所の取得関数を作り`{ticker, as_of, trailing_pe, forward_pe, peg_ratio, psr_ttm, ev_ebitda_ttm, market_cap, enterprise_value, ...}`を返し、TANUKI/HypeCore/STONKS SILOが全てこの関数を呼び出す。正負フィルタ方針を統一（TANUKIは負値をNone化、HypeCoreは負値もそのまま格納——統一関数側で生値を保持しつつ`is_valid`フラグを別途付与）。PERのtrailing/forward基準を明示（両方独立フィールドとして常に返す）。

統一が難しい部分: STONKS SILOのPSR/EV_Sales（分母がSEC年次決算revenue）は対象がプレレベニュー・低収益企業でyfinanceのTTM revenueが荒い・欠損しがちな銘柄群であるための意図的設計と考えられ、統一するとしても「TTM基準PSR」と「Annual基準PSR」を両方併記する形が妥当。TANUKIの`per_adjusted`は他システムには存在しない情報源（EPS Analyzerの調整後EPS）を使っており統一先の共通指標には含めずTANUKI固有の付加指標として残すべき。取得タイミングの非同期性（TANUKI日次、HypeCore月次、STONKS SILO不定期）は統一関数を作るだけでは解決せず、`as_of`タイムスタンプを全出力JSONに必須フィールドとして持たせる運用ルールも必要。

必要データ項目: `ticker, as_of, current_price, shares_outstanding, market_cap, enterprise_value, total_debt, cash_and_equivalents, trailing_pe, forward_pe, peg_ratio, psr_ttm, ev_ebitda_ttm(+is_valid flag), forward_eps, trailing_eps, data_quality_flags`。加えてSTONKS SILO向けにSEC年次revenueベースのPSR/EV_Salesを別関数として維持。

#### 正確性確認で見つかった問題点

1. RKLBのTANUKIデータ欠損: `docs/value-monitor/tanuki_valuation/data/RKLB/`に`latest.json`が存在せず（`score_history.json`のみ）、tickers.json上は103銘柄に含まれるにもかかわらずPER/PEG/PS/EV_EBITDAが一切取得不能。パイプライン実行失敗が放置されている可能性。
2. IOTのHypeCore PSR欠損 vs TANUKI取得成功: 同一yfinanceフィールド参照でも3日違いのタイミングで片方だけ値が取れていない。両システムともリトライ機構なし。
3. IOTのHypeCore EV/EBITDA異常値（-16713.74倍）: EBITDAがほぼゼロの銘柄で比率が発散。TANUKI側は正値フィルタで偶然回避しているが根本対策（EBITDA近傍ゼロの場合はNull化する等）はどちらにも入っていない。
4. STONKS SILOのデータ鮮度: `results.json`の`generated_at`が2026-07-10で、TANUKI（07-22）・HypeCore（07-19）と比べ12日古い。急変動する銘柄では鮮度差だけでPSR等の比較値が大きく歪む。
5. PER基準の暗黙的混在（TANUKI）: `per_is_forward`フラグを見ないと銘柄のPERがtrailingかforwardか判別できない。
6. 命名の紛らわしさ: TANUKIの`ps`とHypeCoreの`psr`は同一定義（yfinance TTM）だが、STONKS SILOの`psr`は自前計算（Annual基準）で同名・別定義になっている。

### ②信頼性／品質判定バッジ系

#### 各判定ロジック整理表

**TANUKI VALUATION**

| 判定 | 判定対象 | 出力カテゴリ | 閾値／根拠 | ファイル:行番号 |
|---|---|---|---|---|
| DCF_Reliability Policy A | revenue_floor適用時（FCF実績赤字）のDCF信頼性 | 2値: LOW/HIGH | `fcf_floor_applied>0 かつ fcf_estimation.applied=False`→LOW | `pipeline.py:611-618`（適用判定）, `1526-1571`（表示） |
| DCF_Reliability Policy B | fcf_outlier未解消・EPS乖離によるDCF信頼性 | 2値: LOW/NORMAL | `eps_invalid`優先→LOW／`detected=True かつ action!="excluded"`→LOW／それ以外NORMAL | `pipeline.py:426-471`（docstring 455-459に判定表） |
| fcf_outlier.detected | FCFが直近1年で異常値かどうか | 2値(detected) + action 3値(none/excluded/flagged) | 直近マイナス→`latest_negative`。5年平均乖離が成熟企業(CV≤0.5): 20%超／成長企業(CV>0.5): 60%超→`deviation_large`。一過性費用が乖離額の20%（latest_negativeは10%）以上→`excluded` | `calculator/adjustments.py:813-816`(閾値), `917-1066`(判定本体) |
| growth_sanity.verdict | Phase1成長率の妥当性 | 3値+1: PLAUSIBLE/REVIEW/AGGRESSIVE（+FLOOR_HIT_REVIEW） | warning数0→PLAUSIBLE, 1→REVIEW, 2以上→AGGRESSIVE。業界平均比1.5/2.5倍、過去CAGR比1.3/2.0倍 | `growth_sanity.py:430-476`, `645-647` |
| validation.checks/overall | DCF計算式そのものの内部無矛盾性 | 3値: PASS/WARN/FAIL | 全項目pass→PASS、anomaly_detection失敗→FAIL優先、それ以外WARN | `validator.py:300-372` |

**STONKS SILO**（`discover/stonks-silo/src/analyzer.py`）

| 判定 | 判定対象 | 出力カテゴリ | 閾値 | 行番号 |
|---|---|---|---|---|
| deficit_quality.verdict | 赤字の質 | 実質4値: PROFITABLE/GOOD_DEFICIT/WATCH/BAD_DEFICIT | 黒字→PROFITABLE、score≥65→GOOD_DEFICIT、≥35→WATCH、それ未満→BAD_DEFICIT | `460-467` |
| runway.verdict | 資金生存能力 | 実質3値+UNKNOWN: SAFE/WATCH/DANGER | 黒字/トントン→SAFE、24ヶ月以上→SAFE、12-24ヶ月→WATCH、12ヶ月未満→DANGER | `529-543` |
| profitability_path（ocf_trend） | OCF改善の速度・加速度 | 5値: ACCELERATING/IMPROVING/FLAT/DETERIORATING/UNKNOWN | 最新YoY≤0→DETERIORATING(黒字ならFLAT)、加速度プラス→ACCELERATING、2年連続改善→IMPROVING、それ以外FLAT | `718-763` |
| dilution_risk | SBCによる希薄化リスク | 実質3値+UNKNOWN: HIGH/MEDIUM/LOW | SBC比率≥15%→HIGH、≥8%→MEDIUM、それ未満→LOW | `275-283` |
| deficit_fixed_risk | 赤字固定化リスク | 3値: HIGH/MEDIUM/LOW | GOOD_DEFICIT×OCF改善中→LOW、BAD_DEFICIT×悪化中→HIGH、それ以外全てMEDIUM（PROFITABLEも含む＝既知バグ） | `472-479` |
| overall_verdict | 3本柱の統合評価 | 4値: 10x_CANDIDATE/PROMISING/WATCH/AVOID | 加重スコア(赤字品質40%/生存能力30%/黒字化パス30%)≥75/55/35で区分 | `807-855` |

**MACRO PULSE**（`src/market/macro_pulse/05_main.py`）

| 判定 | 判定対象 | 出力カテゴリ | 閾値 | 行番号 |
|---|---|---|---|---|
| regime | Fed政策スタンス | 3値: EASING/BALANCED/TIGHTENING | AI(Grok)判定が第一優先。フォールバック時はDGS1織り込み利下げ回数≥1.0→EASING、≤-1.0→TIGHTENING、それ以外BALANCED | `1207-1216`, `1264` |
| stealth_signal | 週次の流動性供給/吸収 | 3値: supply/absorb/neutral | RRP減少 OR TGA減少→supply、RRP増加 AND TGA増加→absorb、準備預金増加のみ→補助的supply | `2027-2049` |

#### 統一可能性の分析

統一すべきでない部分（本質的に異なるドメイン）: DCF計算精度（TANUKI）、企業財務品質（STONKS SILO）、マクロ環境（MACRO PULSE）は判定対象が完全に別レイヤーであり単一フィールドへの統合は不適切。例えば「マクロがTIGHTENINGだから個別銘柄のDCF計算精度もLOW」のような誤った連想を利用者に与えかねず有害。フィールド自体は現状通りドメインごとに独立させるべき。

統一する価値がある部分（表示規約レベル）: 同じ「2値のNG/OK判定」でも`LOW/HIGH`、`LOW/NORMAL`、`GOOD/BAD`、`SAFE/DANGER`、`PASS/FAIL`、`supply/absorb`と命名がバラバラで色（緑/黄/赤）との対応もUI側で個別実装されている。重大度という抽象軸だけ共通スケールにマッピングし、各ドメイン固有ラベルは維持しつつ色・アイコン表現だけ共通コンポーネント化する、という2階層設計が現実的。段階数（2値・3値・5値混在）についても表示上は3段階(RED/AMBER/GREEN)に丸める表示規約を敷けば視覚的一貫性が生まれる。

共通重大度スケール案:

| 共通スケール | TANUKI | STONKS SILO | MACRO PULSE |
|---|---|---|---|
| GREEN（問題なし） | DCF_Reliability HIGH/NORMAL, validation PASS, growth_sanity PLAUSIBLE | PROFITABLE, GOOD_DEFICIT, runway SAFE, dilution LOW, deficit_fixed_risk LOW, overall 10x_CANDIDATE/PROMISING | regime BALANCED, stealth neutral |
| AMBER（要注意） | validation WARN, growth_sanity REVIEW, fcf_outlier detected(action=excluded) | WATCH系全て, dilution MEDIUM, deficit_fixed_risk MEDIUM | regime EASING/TIGHTENING（方向性シグナルであり必ずしも悪ではない）, stealth absorb |
| RED（信頼性・品質に懸念） | DCF_Reliability LOW, validation FAIL, growth_sanity AGGRESSIVE, fcf_outlier detected(action=flagged) | BAD_DEFICIT, runway DANGER, dilution HIGH, deficit_fixed_risk HIGH, overall AVOID | （マクロ環境自体には「悪い」がないため対象外、または個別に定義） |

注意点: マクロ環境（regime, stealth_signal）は本質的に「方向性」の情報でありGOOD/BADの軸に強制的に当てはめるのは不適切（対象外扱いが妥当）。fcf_outlierとgrowth_sanityは判定対象がほぼ同じ（DCF計算の入力信頼性）なのでマッピングしやすいが、企業品質系（deficit_quality等）とは軸が違うためあくまで「同じ列に並べたときの色」の話であって意味の同一視はしないこと。

#### 既知バグとの関連整理

STONKS SILO `_calc_deficit_fixed_risk`のPROFITABLE誤判定（`analyzer.py:472-479`）: 統一設計をする場合、この関数が「else節で無条件にMEDIUM」という設計自体が既に3値の意味を壊しており共通スケールへのマッピング表を作る前提が崩れる。統一以前にロジック側の分岐漏れ（`dq.verdict == "PROFITABLE"`のケースを明示的にLOWとして早期returnする）を直さないと、共通GREENに属すべきケースがAMBER相当のMEDIUMバッジとして表示され続ける。

`pillarColor`(70/45)とDEFICIT判定(65/35)の閾値不一致（`index.html:860-865` vs `analyzer.py:462-467`）: 「同じ概念を2箇所で別々の閾値でカテゴリ化している」問題であり、共通重大度スケール導入の動機そのものに合致する。判定ロジック側（65/35）を単一のソースオブトゥルースとしUI側の色分け閾値もそこから導出する設計にすれば境界値矛盾は原理的に発生しなくなる。

TANUKI DCF_Reliability(Policy A/B)がlatest.jsonに構造化保存されずstock.htmlに非表示: 実際にはPolicy A/Bの判定結果は「Classificationの丸め」という形でスコアには反映されており（`pipeline.py:598-637`）、その結果を示す`rounded_by_policy`（"A"/"B"/None）フィールドはlatest.jsonに保存されている（`pipeline.py:854`、実データ確認済み）が、①LOW/HIGH/NORMALという生の判定値自体は保存されていない、②`rounded_by_policy`はstock.html側で一切参照されていない（grep 0件）。共通重大度スケールを導入するなら、まさにこの`rounded_by_policy`を起点に「DCF信頼性: RED/GREEN」のようなバッジをstock.htmlに新設する余地がある。

未使用の`_dcf_reliability`変数（`pipeline.py:1534`）: Policy Aの判定と全く同じロジックを再計算しているが直後の表示コードは全てハードコードされた文字列リテラルを使っており一切参照されない。

追加で見つかった軽微な不整合: Policy B関数(`_calc_dcf_reliability_policy_b`)は`"LOW"/"NORMAL"`の2値を返すが、report.txt表示コードでは呼び出し箇所によって`"NORMAL"`（`pipeline.py:1667`, FCF_Conversion_Rate方式のとき）とハードコードされた`"HIGH"`（`pipeline.py:1571`, FCF_Base方式・floor未適用のとき）という異なる語彙で表示されている。`growth_sanity`の`FLOOR_HIT_REVIEW`（`growth_sanity.py:647`）はstock.htmlの色マップ（PLAUSIBLE/REVIEW/AGGRESSIVEの3値のみ、`stock.html:2144-2148`）に含まれておらずデフォルトのグレーにフォールバックする。

#### 現状データの正確性確認

`_calc_deficit_fixed_risk`のロジックを読む限り、`dq.verdict == "PROFITABLE"`の銘柄は必ずelse節（`return "MEDIUM"`）に落ちる——黒字化済みの企業であっても機械的に「赤字固定化リスク: MEDIUM」バッジが付く、実データ照合するまでもなくコードから断定できる誤判定。`pillarColor`(70/45)と`deficit_quality`判定(65/35)の閾値差により、スコア45〜65かつ65〜70の帯（合計25点幅）にある銘柄ではバッジラベルとスコア数値の色が食い違う可能性がある。TANUKIのBKNG（既知バグ調査で言及されていたfcf_outlier未解消銘柄の例）を実データ確認したところ、現時点のlatest.jsonでは`fcf_outlier.detected: False`, `rounded_by_policy: None`となっており本日時点のデータでは当該銘柄でPolicy Bは発火していない（過去に修正済みか直近決算で乖離が解消された可能性）。

### ③④⑥⑦⑧⑨⑩⑪（簡易報告）

| 群 | 判断 |
|---|---|
| ③成長率 | 統一不可（将来予測/直近実績/トラジェクトリで目的が別: TANUKIは将来予測、HypeCoreは直近実績、STONKS SILOはトラジェクトリ評価）。TANUKI `growth_scenarios.primary`の実績入力とHypeCore `revenue_growth`が同一yfinance系列を参照している可能性があり、生データソース一致性は次ステップの検証候補 |
| ④総合スコア | 統一不可（DCF妥当性／ハイプ段階／赤字品質／マクロリスク／EPS調整健全性で評価軸が全く別）。「0-100点」という表現スケール自体は既に共有されているため表示規約（色分け閾値等）のみ統一する価値あり（②と同じ論点） |
| ⑥モメンタム | 統一不可。HypeCoreはZスコア正規化、STONKS SILOはベクトル角度と数学的手法が根本的に異なり対象企業層（成熟企業のセンチメント vs 赤字企業の財務トレンド）も別。並存が妥当 |
| ⑦FCF | 用途別（DCF入力用 vs 黒字化ロードマップ実績）のため上位概念の統一は不可。同一企業・同一決算期の生FCF自体は本来一致すべき値であり、TANUKIとSTONKS SILOでデータソース（SEC XBRL由来かyfinance由来か）が異なる場合は生データレベルの不一致リスクがある。次ステップの検証候補 |
| ⑧次回決算日 | EPS Analyzer側はTANUKIの`latest.json`を参照しているため実質1系統。既に統一済みとみなせる。追加対応不要 |
| ⑨インサイダー/空売り | TANUKI（表示用）とHypeCore（ステージ判定の内部変数、JSON非表示）で用途が異なる。取得元（yfinance）は同じ可能性が高く統一するなら「生データ取得の1箇所集約」が現実的な着地点 |
| ⑩リスクイベント/カタリスト | TANUKIの`risk_events`（Grok検索簡易版、report.txtのみ）とDiscoverの`catalysts`/`macro_themes`（確度・時期・影響予測付きの本格版）は粒度が大きく異なる重複開発。統一するならTANUKI側の簡易版を廃止しDiscoverの該当銘柄カタリストへのリンクに置き換えるのが自然な方向性 |
| ⑪マクロ環境認識 | MACRO PULSE（市場全体のマクロレジーム）、Discover（個別テーマ）、TANUKI `erp`/`forward_earnings_yield`（個別銘柄DCF用リスクプレミアム）は粒度・用途が異なり統一不可。TANUKIのERP計算とMACRO PULSEが把握する金利環境（`ff_rate`等）が独立して別々に取得されている可能性があり、リスクフリーレート等の生データ一致性は要検証候補 |

### 次ステップに向けた検証候補の棚卸し

1. TANUKI `growth_scenarios.primary`とHypeCore `revenue_growth`の元系列一致性
2. TANUKIとSTONKS SILOのFCF生データ（SEC XBRL vs yfinance由来の違い）
3. TANUKI ERPとMACRO PULSEの金利環境データ（risk_free_rate等）の一致性
4. RKLBのTANUKIデータ完全欠損（バグとして別途対応要否を判断すべき）

## ステップ5: 出力項目 計算ルート紐付け（サブシステム別）

対象の定義: 「画面（html）に実際に表示される」「report.txt等のファイルに実際に出力される」「他のサブシステムから読み取られ消費される」のいずれかを満たす項目のみ。内部でのみ計算され上記いずれにも該当しない中間変数・削除候補は対象外。

### 5-1. TANUKI VALUATION

#### A. トップレベルDCF指標（core_calculator.py: `KoichiValuationCalculator.calculate_pt()`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| intrinsic_value_per_share | 両方 | core_calculator.py:641 `_calc_ivps_with_wacc(_rm)` | メインDCF株価（Rmβなし、10%割引率） |
| intrinsic_value_beta | 両方 | core_calculator.py:550-556（`_calc_ivps_with_wacc`型計算にBS補正加算） | β込みWACCで再計算 |
| upside_percent_beta | 両方 | core_calculator.py:789 `calculate_upside()`呼出 | |
| intrinsic_value_rf | 両方 | core_calculator.py:650 `_ivps_rf = _calc_ivps_with_wacc(_rf)` | リスクフリーレート基準 |
| upside_percent_rf | 両方 | core_calculator.py:791-792 | |
| upside_percent | 両方 | core_calculator.py:642-645, 799 `calculator/dcf.py`系`calculate_upside()` | |
| v0 | 両方 | core_calculator.py:353-440（dcf_type分岐: two_stage/three_stage/tapering） | `calculator/dcf.py`各関数のv0 |
| v0_adjusted | 両方 | core_calculator.py:544 `calculate_intrinsic_value(v0, rpo_pv, alpha=0.0, growth_option_pv)` | |
| alpha / alpha_was_capped | 両方 | core_calculator.py:517-525 `calculate_alpha()`（RM基準ROE差分） | ALPHA-REDESIGN-1により乗算には使わず参考値のみ |
| future_values | 両方 | `calculator/future_values.py:calculate_future_values()` L11-49、呼出core_calculator.py:714 | |
| return_metrics | 両方 | `calculator/future_values.py:calculate_return_metrics()` L52-86、呼出core_calculator.py:726 | current_price>0のときのみ |

#### B〜Q. calculator/配下の計算モジュール由来項目

| 項目名 | 計算ルート | 計算式概要 | 補足 |
|---|---|---|---|
| growth.rate/source | `calculator/growth.py:determine_growth_rate()` L159-195（セグメント加重→FCF CAGR→デフォルトの優先順） | 優先順位ロジック | segment_weightedは外部`segment_config.py`に委譲 |
| wacc.value/beta/risk_free_rate/market_return | `calculator/wacc.py:calculate_wacc()` L54-100 | `WACC=Rf+β×(Rm-Rf)`、上下限6-25% | |
| sensitivity.matrix/wacc_values/growth_years | `calculator/sensitivity.py:calculate_sensitivity_matrix()` L61-83、セル計算は`create_sensitivity_calc_func`内calc_func L122-172 | 3×3、各セルで`calculator/dcf.py`のDCF関数を都度呼出 | 中央セルがメイン理論株価と一致するようbase_wacc=Rm |
| scenario_valuations.bear/base/bull | `calculator/scenarios.py:calculate_scenario_valuations()` L64-84、実体は`create_scenario_calc_func`内calc_func L121-183 | growth_rate=base×0.7/1.0/1.2、内部で`dcf.py`呼出 | |
| growth_options.total_pv/count/options | `calculator/adjustments.py:calculate_growth_option_pv()` L672-689 | 実計算式はadjustments.py内になし、外部`segment_config.calculate_growth_option_total_pv(ticker)`に完全委譲 | |
| maturity_profile | core_calculator.py:363 `get_maturity_profile(ticker)`（`maturity_config.py`、対象外ファイル） | config読み込みそのまま | |
| dcf_components.*（v0,pv_high_growth,pv_terminal,high_growth_detail,terminal_fcf,terminal_value等） | `calculator/dcf.py`: two_stage L106-132／three_stage L185-232／tapering L308-351 | 割引CF積算＋Gordon成長ターミナルバリュー | dcf_components.v0_rm/pv_fcf_rm/pv_tv_rm/pv_phase1_rm/pv_phase2_rmはcore_calculator.py:819-828でRm基準別途計算し追加合成 |
| fcf_base.base_fcf/method/cv | `calculator/adjustments.py:determine_fcf_base()` L211-317 | データ不足/直近赤字/2yr-5yr乖離/過去赤字/減少トレンド/CV判定の順次分岐、CV=`stdev/mean` L260-265 | |
| fcf_outlier.detected/rule/action/note/deviation_pct | `calculator/adjustments.py:analyze_fcf_outlier()` L941-1067 | ルール1(直近マイナス)/ルール2(乖離率)+EPSアナライザー突合 | |
| fcf_estimation.applied/conversion_rate/estimated_fcf等 | `calculator/adjustments.py:estimate_fcf_from_eps()` L1495-1773 | `estimated_fcf=adj_net_income×conversion_rate`（L1710） | conversion_rateはticker override→保険金融直接NI→セクター別レートの優先順L1589-1598 |
| software_system_reclassification.* | `calculator/adjustments.py:check_software_system_reclassification()` L1388-1492 | `realized_ratio=mean(生FCF/調整済純利益)`（黒字年のみ、L1455） | core_calculator.py:277-311で乖離時に実行限定の差替えも実施 |
| rd_capitalization.* | `calculator/adjustments.py:capitalize_rd()` L1151-1280 | `rd_adjustment=資本化額-当期償却額`（L1260）、適用条件R&D/Rev≥5%(L1234) | |
| rpo_adjustment.rpo_pv/application_rate/sector_category/rpo_incremental等 | `calculator/adjustments.py:adjust_rpo()` L473-565、レート決定`_get_rpo_application_rate()` L411-470 | `rpo_incremental=max(0,rpo-rpo_yago×(1+rev_yoy))`、`rpo_pv=incremental×rate×op_margin/(1+r)^years` | |
| bs_adjustment.net_cash/net_cash_per_share/sector_guard | `calculator/adjustments.py:calculate_bs_adjustment()` L753-797 | `net_cash_per_share=net_cash/diluted_shares` | net_cash自体は`SECReader.get_net_cash()`（対象外ファイル）由来 |
| moat_score系（components.moat_score等） | `calculator/adjustments.py:calculate_moat_score()` L597-634 | `moat_score=gm_norm×0.4+roic_norm×0.4+fcf_norm×0.2`、`phase1_years=3+round(moat_score×7)`(L625-626) | Phase1年数を通じてDCF年数・感度分析base_yearsに連動 |
| rice.q/cf_conversion/q_years/cf_years/avg_intensity/avg_rev_growth/vc_factor/bear・base・bull | `calculator/rice.py`: Q=`_calc_q()` L153-158、CF=`_calc_cf_lagged()` L294-306、シナリオ本体=`calculate_rice()` L438-446 | `rice=g×vc_factor×Q×CF/wacc`、`vc_factor=clamp(roic_wacc_ratio,0.3,2.0)`(L420) | |

#### R. components.*（core_calculator.py:861-923、30項目超）

`fcf_5yr_avg`〜`insider_latest_date`まで大半は`financials.get(...)`の直接パススルー（データ取得元は`data_fetcher.py`など今回対象外のファイル）。本サブシステム内での計算ルートは以下のもののみ:

| 項目名 | 計算ルート |
|---|---|
| moat_score / moat_phase1_years / moat_gross_margin_norm / moat_roic_norm / moat_fcf_margin_norm | 上記B〜Q節`adjustments.py:calculate_moat_score()`参照 |
| pv_high / pv_terminal | dcf.py各DCF関数の戻り値をcore_calculator.py:889-890でそのまま転記 |
| alpha_uncapped | core_calculator.py:899、`calculate_alpha()`結果 |
| per_adjusted | core_calculator.py:930-962 `_calc_adjusted_per()`（EPS Analyzer調整後TTM EPSベースで独自算出、GAAP PERとの比較用） |
| per, peg, ps, ev_ebitda, ma200, forward_eps, analyst_target_*, dividend_yield, payout_ratio, insider_* | `financials.get()`パススルー（計算元はdata_fetcher.py側、本調査対象ファイル外） |
| max_eps / max_eps_per / max_eps_reliability | core_calculator.pyではなくpipeline.py側で追加: `_load_extra_data`（pipeline.py:976-978、`dupont.ni_ttm`＋`financial_health.sbc_ttm`から算出） |

#### S〜Z. pipeline.py（TANUKI SCORE / report.txt / latest.json）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| tanuki_score | 両方 | pipeline.py:`_compute_tanuki_score()` L473-645（返却L639-645） | latest.json代入L846、report.txt「Classification」L1392 |
| funda_score | 両方 | 同上 L503-533、返却L640 | latest.json L847、report.txt「Funda_Score」L1396 |
| score_comment | 両方 | `_generate_score_comment()` L647-669（Policy A/B時はL616/633/635で上書き） | latest.json L848、report.txt「Comment」L1399 |
| timing_score | 両方 | `_calc_timing()` L372-395、呼出L536 | report.txt内訳L1384-1389 |
| sell_reason | latest.jsonのみ | `_compute_tanuki_score()` L552-557 | report.txt非出力 |
| pre_rounding_score | latest.jsonのみ | 同上 L594, 642 | report.txtは別途`Classification_Pre_Rounding`として再取得(L1394-1395) |
| rounded_by_policy | latest.jsonのみ | 同上 L596, 618("A")/637("B") | |
| matrix.*（quadrant/label/key_metric_y/qx/qy） | 両方 | `_compute_matrix_position()` L1023-1124 | RICE可否/セクター除外(ROE軸)/Q異常値(Revenue_Growth軸)/通常(FCF_Margin軸)の4分岐 |
| growth_sanity.verdict/signals/warnings/recommended_g | 両方 | `growth_sanity.py::check_growth_sanity()`、pipeline.py側呼出は2箇所: `_save_result()` L710-723(初回)・L779-793(recommended_g採用後の再判定) | 出力: latest.json L928 `growth_sanity`, report.txt「[4. 成長率根拠]」L1920-1995 |
| phase1_growth_auto_adjusted | 両方 | `_save_result()` L731初期化, L767成功時True | |
| fcf_margin_bear_mult_applied | 両方 | `_save_result()` L811初期化, L823成功時True | report.txt L1468 |
| financial_health.*（net_debt,total_debt,cash_and_equivalents,sbc_ttm,dilution_3yr_annual_pct等） | 両方 | `_load_extra_data()` L2305-2740内、確定代入L2360-2508 | report.txtは「[3. TANUKI VALUATION]」内Financial_Healthブロック L1754-1815（STONKS SILOセクションではない点に注意） |
| dupont.net_margin/asset_turnover/financial_leverage/roe_decomposed | latest.jsonのみ | `_load_extra_data()` L2512-2621、確定L2573-2587（`roe_decomposed=net_margin×asset_turnover×financial_leverage`） | report.txtには一切出力なし |
| fcf_history[] | 両方 | `_load_extra_data()` L2313-2347 | report.txt「FCF_History:」L1816-1841 |
| next_earnings_date | 両方 | `_load_extra_data()` L2625-2649（yfinance calendar、過去日除外） | report.txt L1815/2123/2264 |
| computed_runway_months | latest.jsonメイン | `_load_extra_data()` L2408-2420（`cash/月次バーン`） | `_compute_tanuki_score()`のRunwayペナルティ判定でも使用(L518-522) |
| segments[] | 両方 | `_load_extra_data()` L2684-2738、確定L2724-2730 | report.txt「Segment_Breakdown:」L1844-1867 |
| breakeven_estimate | 両方 | `_load_extra_data()` L2651-2682（線形回帰） | report.txt L2265-2266 |
| validation.* | latest.jsonのみ | `validator.py::validate_calculation()`呼出2箇所: `run()` L225-230（初回）／`_save_result()` L754-765（recommended_g再計算後） | report.txt非出力 |
| dilution_severity / dilution_comment | latest.jsonのみ | `_dilution_severity_info()`（L123-138）呼出、`_save_result()` L942-945 | report.txt側は同関数を`_generate_report()` L1760で再呼出し「Dilution_3yr_Annual」「Dilution_Comment」L1803-1804として別出力 |
| risk_events | 両方 | `_save_result()` L980-1005（`risk_fetcher.py::fetch_risk_events()`、Grok検索） | report.txt「[RISK EVENTS]」L2282-2295 |

**erp（2ルート、既知の重複実装）**

| ルート | 出力先 | 場所 | 数式 |
|---|---|---|---|
| ① | latest.json（`erp`,`forward_earnings_yield`） | pipeline.py:`_save_result()` L931-940 | `_ey=forward_eps/current_price; erp=round(_ey-risk_free_rate,4)` |
| ② | report.txtのみ（ローカル変数、JSON非保存） | pipeline.py:`_generate_report()` L2206-2230 | 同数式だがround非適用、HYPECOREセクション |

数式・入力元は同一だが完全に独立した重複実装（丸め桁数のみ差異）。

**Reverse DCF必要成長率（2ルート、既知の差異）**

| | `_calc_required_growth()`（判定用） | report.txtインライン（表示用） |
|---|---|---|
| 場所 | pipeline.py L397-423（静的メソッド） | pipeline.py:`_generate_report()` L1505-1525 |
| 用途 | Classification判定（GROWTH_PREMIUM/TRIM分岐）内部使用のみ、report.txt非表示 | 「Valuation_Gap_Analysis」表示専用、スコア判定に不使用 |
| terminal_growthの出所 | `maturity_config.get_terminal_growth(ticker)`（セクター別） | `components.terminal_growth_used`（DCF計算結果、なければ0.03固定） |
| ガード | `ev<=0`／`required_fcf5<=0`で早期None等、厳密 | `ev<=0`チェックなし、やや緩い |

tv_gの出所が異なるため同一銘柄でも両者の必要成長率が食い違い得る。

**report.txt 9セクション生成箇所**: すべて単一メソッド`_generate_report()`（pipeline.py L1126-2303）内でセクションごとに直接文字列生成（サブ関数分割なし）: [1.TANUKI SCORE]L1391-1414 / [2.MATRIX POSITION]L1416-1443 / [3.TANUKI VALUATION]L1445-1919 / [4.成長率根拠]L1920-1995 / [RICE METRICS]L1999-2058 / [EPS ANALYZER]L2059-2137 / [HYPECORE]L2138-2248 / [STONKS SILO]L2250-2281 / [RISK EVENTS]L2282-2295

**latest.json保存**: `_save_result()`（L671-1021）が2段階書き込み: 中間保存(L858-860, valuation全体+スコア系+matrix)→最終保存(L1007-1008, extra全キー+growth_sanity+erp+dilution+risk_events等をマージ)。補助ファイルとして`history/{date}.json`、`history.json`、`score_history.json`、`hypecore_history/{ticker}.json`、`tickers.json`も生成。

#### AC. stock.html（サーバー値そのまま表示 vs クライアント独自計算）

主要なJSON直接表示: `intrinsic_value_per_share`, `intrinsic_value_beta`, `intrinsic_value_rf`, `upside_percent`, `sensitivity.matrix`（数値そのもの、色分けのみ独自）, `scenario_valuations`, `rice.*`, `validation.*`, `dcf_components`, `financial_health`, `dupont`, `segments`, `risk_events`, `components.analyst_target_*`, `components.insider_*`, `components.per`/`per_adjusted`。

| クライアント独自計算項目 | 計算箇所（関数:行番号） | 計算式・入力 |
|---|---|---|
| フェアPER | render:942-943 | `ivps/(currentPrice/perForCalc)` |
| PEGレシオ | render:944-945 | `perForCalc/(growthRate×100)`（入力: `per_adjusted`, `growth_scenarios.primary.rate`） |
| PSR | render:946-947 | `(currentPrice×diluted_shares)/latest_revenue` |
| 将来価値予測（シナリオ別テーブル） | `projectFuture()`:1205-1215、呼出1221-1230 | 各年`v×=(1+g)`（`scenario_valuations`のg使用、JSONの`future_values`は不使用） |
| 5年BASE年率換算リターン | render:1252-1261 | `(fv5/currentPrice)^0.2-1` |
| 感応度分析（独自5×5マトリクス） | `calcSensIV()`:1285-1294 | 2段階DCFの完全クライアント再実装 |
| Reverse DCF | render内IIFE:1480-1522 | `EV=price×shares+netDebt; fcfTerm=EV×(Rm-g_TV)/(1+g_TV); reqGr=(fcfTerm/fcfCur)^(1/5)-1` |
| FCF CAGR(3yr) | render内IIFE:2106-2113 | `(最新FCF/3年前FCF)^(1/3)-1` |
| WACCスライダー | `updateWacc()`:2524-2556 | 正確な再DCFではなく`adjustFactor=baseWacc/newWacc`の比例近似 |
| Layer2トグル | `applyLayer2Toggle()`:2558-2580 | `(v0+rpoPV+goPv)/shares+bs` |
| キャッシュフロー分析セクション | `loadCfData()`:411-456, `renderCfCharts()`:458-580 | latest.json不使用、別ファイル`{ticker}_quarterly_normalized.json`から独自算出 |

**重要な不一致（実データAAPLで検証済み）**:
- PEGレシオ: JSON`components.peg=2.69` vs クライアント再計算値≈4.92（約1.8倍乖離、JSON値は画面に一切表示されず破棄）
- PSR: JSON`components.ps=10.70` vs クライアント再計算値≈11.61（約8.5%乖離）
- 感応度マトリクスの基準セル: `calcSensIV()`が使う`fcfBase.base_fcf`($106.77B)は実際のDCF計算で使われた`components.fcf_base_used`($90.77B)と異なり、手計算すると公式理論株価と約18%乖離

#### AD. index.html

JSON直接表示: 現在株価、理論株価BASE/β込み、Moat、RICE base/RICE_PER、成長率BASE、WACC、Q、CF、更新日（`buildRows()` L396-427）。

| クライアント独自集計項目 | 箇所 | 計算式 |
|---|---|---|
| 銘柄数 | `loadTickers()`:561 | `valid.length` |
| 平均Moat | `loadTickers()`:567-569 | `moat_score`配列の算術平均 |
| 平均RICE | `loadTickers()`:571-573 | `rice.base.rice`配列の算術平均 |
| 乖離率 | `buildRows()`:401 | `(ivps-price)/price`（JSON`upside_percent`は同ファイル内に一切参照なし、grep確認済み） |
| 200MA乖離 | `buildRows()`:407-408 | `(price-ma200_raw)/ma200_raw`（率自体はJSON非保持、生MA値のみJSON由来） |

### 5-2. HypeCore

#### 前提の訂正

事前情報で「削除候補」とされていた項目のうち、実際には他サブシステムから読み取られており削除候補扱いが誤りだった項目が見つかった。

| 項目 | 事前情報での扱い | 実際の使用箇所 |
|---|---|---|
| HypeCore `stage_label` | 削除候補 | `tanuki_valuation/stock.html:666`（MATRIX×HYPEシグナル表示）／`tanuki_valuation/pipeline.py:3059-3060,3112`（`_load_hype_info`/`_save_hypecore_history`）／`tanuki_score/index.html:481,517,576`（TRIMチップ表示） |
| HypeCore `expectation_score` | 削除候補 | `tanuki_valuation/stock.html:667,670-673,691-698`（「期待プレミアム」パーセンタイル表示） |
| STONKS SILO `deficit_quality.revenue_growth_pct` | 削除候補 | `tanuki_valuation/stock.html:2907-2912`（Matrix③成長性系パネルのY軸＝売上成長率） |

いずれも自サブシステムのHTML（hypecore/detail.html・index.html、stonks-silo/index.html）内では未使用だが、他サブシステムが直接JSONを読みに来ているため「他サブシステムから読み取られる」の基準に該当し削除候補から除外すべき。

また、HypeCoreの「推奨（レコメンド）」判定ロジックは3箇所で独立に再実装されており乖離リスクがある。
- `docs/value-monitor/hypecore/detail.html:364-378 getRec()`（JS）
- `docs/value-monitor/hypecore/index.html:155-169 getRec()`（JS、判定条件はdetail.htmlとほぼ同一だが別実装）
- `src/value/tanuki_valuation/pipeline.py:3067-3090 _hypecore_recommendation()`（Python、コメントに「hypecore.htmlのgetRec()をPython移植」とあるが、real_strong等の派生ロジックは持たず簡略版）

出力元: `src/value/hypecore/hypecore.py`の`run_poc()`（801-934行）が`docs/value-monitor/hypecore/data/{TICKER}_poc.json`を生成。`_save_tickers_index()`（956-980行）が`tickers.json`を生成。

#### トップレベル・tickers.json

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `generated_at` | poc.json トップレベル | `hypecore.py:923,927` `datetime.now(JST)` | index.html:217,225,241-244で`toJST()`表示。detail.htmlでは未使用 |
| `monthly` | poc.json トップレベル | `hypecore.py:874-921` のリスト構築 | 以下で個別項目を列挙 |
| `tickers`（配列） | tickers.json | `hypecore.py:969` `sorted(p.stem[:-4] for p in docs_dir.glob("*_poc.json"))` | index.html:206-211 `loadAll()`が一覧描画に使用 |

#### `monthly[]` 各項目

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `month` | 両HTML | `hypecore.py:80-81`（月次resample index）→`877` `idx.strftime("%Y-%m")` | 全チャート/テーブルのX軸・ラベル |
| `price` | 両HTML | `fetch_price_data:78,80`（yfinance日次Close→月末値）→`878` | hero株価・チャート・テーブル |
| `stage` | 両HTML＋他サブシステム | `determine_stage()`（501-644行）、呼び出しループ`810-820`→`879` | 全表示の起点。TANUKI VALUATION `pipeline.py:3040-3064,3107`、`tanuki_score/index.html:474`でも読取 |
| `stage_label` | 他サブシステムのみ | `STAGE_LABELS`辞書（37-43行）→`821,880` | 自HTML未使用（STAGES定数で独自定義）。上記「前提の訂正」参照 |
| `ma200_dev` | 両HTML | `fetch_price_data:93,99-100` | buildVsMetrics各分岐・チャート・テーブル |
| `ma50_dev` | JSON出力のみ（未使用） | `fetch_price_data:92,99-100`→`883` | どのHTML・他サブシステムからも未参照 |
| `from_peak` | 両HTML | `compute_scores:442-443` | hero推奨サブ文言・buildRatio・テーブル・index.html高値比列 |
| `rsi` | detail.htmlのみ | `fetch_price_data:87-90,99-100` | buildVsMetrics(dawn/expand)・expectChart・テーブル |
| `volume_ratio` | JSON出力のみ（未使用） | `fetch_price_data:96-97,99-100`→`886` | 参照箇所なし（`vol_surge`とは別物） |
| `vol_surge` | detail.htmlのみ | `compute_scores:448-450` | buildVsMetrics(dawn分岐) |
| `rev_yoy` | 両HTML＋他サブシステム | `fetch_quarterly_fundamentals:155,162-164,169-175`（SEC正規化データ） | buildVsMetrics/fundChart/index.html revyoy列。TANUKI stock.html:631,3119、tanuki_score/index.html:472で読取 |
| `ni_yoy` | JSON出力のみ（直接表示なし） | `fetch_quarterly_fundamentals:156,165,169-175`→`890` | 表としては未表示だが`determine_stage:550-554`のS4脱出判定、`detect_substage:732-733,748-749`のwatchテキストに間接的に反映 |
| `rule40` | 両HTML＋他サブシステム | `fetch_quarterly_fundamentals:167,169-175`（rev_yoy+op_margin方式） | buildVsMetrics/index.html rule40列。TANUKI stock.html:632、tanuki_score/index.html:473で読取。※STONKS SILOのrule_of_40とは計算式が異なる |
| `fcf_yield` | detail.htmlのみ | `compute_scores:410-415` | buildVsMetrics(mature分岐) |
| `forward_pe` | detail.html＋内部判定 | `fetch_info_snapshot:116`（yfinance `.info`）、最新月にのみ注入`compute_scores:418-424` | buildVsMetrics(growth/mature)。`determine_stage:572-573`のS3判定、`detect_substage:704-726`のバリュエーション過熱判定にも使用 |
| `peg_ratio` | detail.html | `fetch_info_snapshot:119`→`418-424` | buildVsMetrics(mature)、renderValMultiples フォールバック（552行） |
| `psr` | detail.html | `fetch_info_snapshot:118`→`421`（明示的にpsrキー追加） | buildVsMetrics(expand)、renderValMultiples フォールバック（553行） |
| `revenue_growth` | 両HTML | `fetch_info_snapshot:120`→`419` | `detectLifecycle()`（detail.html:297, index.html:151）のライフサイクル判定の主要入力 |
| `earnings_growth` | JSON出力のみ（未使用） | `fetch_info_snapshot:121`→`419`→`898` | HTML未参照。`compute_scores:434-438`でeps_surpriseフォールバック元として内部利用のみ |
| `recommendation_mean` | JSON出力のみ（未使用） | `fetch_info_snapshot:123`→`419`→`899` | HTML未参照。`determine_stage:537,636`のS1判定に内部利用 |
| `short_pct_float` | JSON出力のみ（未使用） | `fetch_info_snapshot:125`→`419`→`900` | HTML未参照。`determine_stage:536,608`のS0判定に内部利用 |
| `eps_surprise` | 両HTML | `fetch_analyst_history:277-347`（3段階フォールバック）＋`compute_scores:430-438` | buildVsMetrics(growth)・buildRatio(S4)。両HTMLの`getRec()`のreal_strong算出にも使用 |
| `analyst_upgrade_rate` | detail.html | `fetch_analyst_history:242-272` | buildVsMetrics(growth)。`determine_stage:528,631-634`のS1判定にも使用 |
| `analyst_downgrade_rate` | JSON出力のみ（未使用） | `fetch_analyst_history:265-266`→`904` | 参照箇所なし |
| `sell_on_good_news` | JSON出力のみ（直接表示なし） | `compute_scores:452-459` | 直接表示なしだが`determine_stage:526,589`のS4核心シグナルとして`stage`値自体を決定 |
| `buy_hold_ratio` | JSON出力のみ（未使用） | `fetch_analyst_history:349-364`→`906` | 参照箇所なし。`determine_stage:529,577,636`に内部利用のみ |
| `substage_phase` | 両HTML | `detect_substage()`戻り値`phase`キー（680-799行）、ループ`824-835`→`908` | phaseVal/subBadge・テーブル・index.htmlフェーズ列 |
| `substage_label` | 両HTML＋他サブシステム | `detect_substage()`の`label`キー→`909` | phaseVal/subLabel・テーブル。TANUKI pipeline.py:3060,3112、tanuki_score/index.html:480,517,530-532,572-573で読取 |
| `substage_watch` | detail.htmlのみ | `detect_substage()`の`watch`キー→`910` | phaseSub/subWatch |
| `substage_next` | detail.htmlのみ | `detect_substage()`の`next`キー→`911` | subNext |
| `expectation_score` | 他サブシステムのみ | `compute_scores:470-480`（ma200_dev/ma50_dev/price_iv_ratio/analyst_scoreのz-score合成）→`913` | 自HTML未使用。TANUKI stock.html:667,670-698で読取（上記「前提の訂正」参照） |
| `fundamental_score` | JSON出力のみ（未使用） | `compute_scores:482-487`→`914` | 参照箇所なし |
| `momentum_score` | JSON出力のみ（未使用） | `compute_scores:489-494`→`915` | 参照箇所なし |
| `price_iv_ratio` | 両HTML＋他サブシステム | `compute_scores:402-408`（price÷iv）。iv元は`fetch_tanuki_iv:186-220`がTANUKI `history/*.json`・`latest.json`の`intrinsic_value_per_share`を月次化 | buildVsMetrics(dawn/expand)。index.html piv列(237,279,287)。TANUKI stock.html:630,3118、pipeline.py:3118でも読取 |
| `ev_ebitda` | detail.html | `fetch_info_snapshot:130`→`421` | renderValMultiples（正値のみ表示、554-556行） |
| `low_base_effect` | JSON出力のみ（未使用） | `run_poc:838-843`（rev_yoyの12ヶ月shift比較） | 参照箇所なし |

#### クライアント側で独自算出される表示項目（JSONフィールドではない）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| ライフサイクル（黎明/成長/拡大/成熟） | 両HTML | `detectLifecycle()` — detail.html:295-299／index.html:149-153（同一ロジックの重複実装） | `revenue_growth`（無ければ`rev_yoy`）から閾値判定 |
| HypeCore推奨（買い/保有/売り等） | 両HTML＋TANUKI | `getRec()` — detail.html:364-378／index.html:155-169（重複実装、判定文言が微妙に異なる）／`_hypecore_recommendation()` tanuki_valuation/pipeline.py:3067-3090（Python簡略版） | 上記「前提の訂正」参照。3実装間の同期リスクあり |
| 1ヶ月後のステージ遷移確率 | detail.htmlのみ | `calcTrans()` detail.html:380-388 | `monthly`配列全体からのマルコフ的頻度集計、JSON側計算なし |
| バリュエーション倍率パネル（PER/PS/PEG/EV-EBITDA） | detail.htmlのみ | `renderValMultiples()` detail.html:537-601 | TANUKI `latest.json`の`components.{per,peg,ps,ev_ebitda,per_is_forward}`を優先取得し無ければpoc.jsonの`peg_ratio`/`psr`/`ev_ebitda`にフォールバック（552-556行）＝2ルート併存 |

### 5-3. STONKS SILO

出力元: `discover/stonks-silo/src/pipeline.py`の`run()`（85-201行）が`discover/stonks-silo/src/analyzer.py`の`StonksAnalyzer.analyze()`（149-174行）を呼び出し、`_to_dict()`（67-78行）でシリアライズして`docs/value-monitor/stonks-silo/data/results.json`に保存。

#### トップレベル

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `generated_at` | index.html hero | `pipeline.py:189` | `dt.toLocaleDateString`表示(415-417行) |
| `tickers`（辞書, ticker→result） | index.html全体 | `pipeline.py:191`, `allData`格納 | `loadData()`406-421行 |
| `years` | index.htmlチャート | `analyzer.py:154,166-167`（`fetcher.load_annual_data`の年リストをそのまま透過） | yearRange表示(857行)、chart X軸(903,928行) |
| `overall_score` | index.htmlスコア列 | `_overall()` analyzer.py:807-855（840-844行で加重合計） | render()527行、score-bar |
| `overall_verdict` | index.html判定バッジ | `_overall()` analyzer.py:846-853 | `verdictBadge()`表示、フィルターボタン |
| `summary` | index.html「総合スコア判定根拠」 | `_build_summary()` analyzer.py:857-1004 | `formatSummary()`1467-1482行でパース表示 |
| `records`（yr→{revenue,net_income}） | index.html売上/純利益チャート | `pipeline.py:111-117`（`fetcher.load_annual_data()`のpl.revenue/net_incomeをそのまま抽出、SEC由来） | `buildDetail()`935-946行のrevVals/niVals |
| `valuation.market_cap` | index.html詳細パネル | `valuation_fetcher.py:8`(yfinance `.info.marketCap`)→`pipeline.py:136` | valInlineHtml(994-1004行) |
| `valuation.current_price` | index.htmlテーブル・詳細 | `valuation_fetcher.py:9`→`pipeline.py:137` | テーブル価格列(558行)、ソート(463行) |
| `valuation.psr` | index.html詳細パネル | `pipeline.py:127`（`market_cap ÷ latest_rev`、rev=SEC年次`revenue_sanitized`） | valInlineHtml |
| `valuation.ev_sales` | index.html詳細パネル | `pipeline.py:128`（`enterprise_value ÷ latest_rev`） | valInlineHtml |
| `valuation.net_cash` | index.html詳細パネル | `pipeline.py:131-133`（cash - total_debt） | valInlineHtml |
| `financial_vectors.fields.*` | index.html財務トレンドパネル | `financial_trend_calculator.py:compute_vectors()`230-405行 | `buildVectorPanel`/`initFvCharts`/`buildProfitPath` |

#### `deficit_quality`（`_analyze_deficit_quality`, analyzer.py:180-383）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `cagr_3yr` | index.html詳細＋サマリー | `analyzer.py:215-222`（4年分の売上比較） | 詳細行1050、summary内`cagr_cmt()`892-898 |
| `rnd_ratio` | index.html詳細（合算表示） | `analyzer.py:225-236` | 「成長投資比率」としてsm_ratioと合算表示(1054行) |
| `sm_ratio` | 同上 | `analyzer.py:225-236` | 同上 |
| `gross_margin` | index.html詳細＋サマリー | `analyzer.py:235-236`（gross_profit÷revenue_sanitized） | 1051行、`gm_cmt()`906-911 |
| `gross_margin_derived` | index.html詳細（"逆"バッジ） | `analyzer.py:237`（`pl.get("gross_profit_derived")`を透過） | CostOfRevenueからの逆算フラグ、1051行 |
| `verdict` | index.htmlバッジ・ソート | `_deficit_verdict()` analyzer.py:385-469（459-467行で最終判定） | `deficitBadge()` |
| `score` | index.htmlスコア円・ソート | `_deficit_verdict()`同上（405-457行のスコアリング） | `s1`表示、`getSortVal('deficit')` |
| `rule_of_40` | index.html詳細 | `analyzer.py:245-249`（cagr_3yr + operating_income÷revenue） | 1052行（HypeCoreの`rule40`とは別計算式） |
| `mature_profit` | index.html詳細 | `analyzer.py:252-259`（net_income + R&D + S&M） | 1055行 |
| `mature_profit_note` | index.html詳細 | `analyzer.py:253,258-259` | 1055行の注記表示 |
| `sbc_adjusted_fcf` | index.html詳細 | `analyzer.py:262-265`（FCF - SBC） | 1056行 |
| `sbc_ratio` | index.html詳細 | `analyzer.py:266` | 1057行 |
| `sbc_yoy_change` | index.html詳細 | `analyzer.py:269-273` | 1058行 |
| `dilution_risk` | index.html詳細バッジ | `analyzer.py:276-283` | `riskBadge()`1062行 |
| `deficit_fixed_risk` | index.html詳細バッジ | `_calc_deficit_fixed_risk()` analyzer.py:472-479、`analyze()`160行で呼出 | `riskBadge()`1061行。既知バグ: 黒字企業でもverdict="PROFITABLE"は条件分岐に含まれず常にMEDIUM |
| `revenue_outlier_years` | index.htmlチャート注記 | `analyzer.py:190-193`（`revenue_is_outlier`フラグ集計） | 1115行 |
| `revenue_growth_pct` | index.html未使用、他サブシステムから参照 | `analyzer.py:196-212` | TANUKI `stock.html:2907-2912`（Matrix③のY軸）で使用。5-2節「前提の訂正」参照 |

#### `runway`（`_analyze_runway`, analyzer.py:484-527）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `cash` | index.html詳細 | `analyzer.py:490-493`（現金＋短期投資） | 1078行 |
| `monthly_burn` | index.html詳細 | `analyzer.py:499-504`（(OCF-\|CapEx\|)÷12） | 1079行 |
| `runway_months` | index.htmlテーブル・詳細・ソート | `analyzer.py:507-513` | テーブルバー(537-546行)、`fmtRunway()`、TANUKI `stock.html:2904`でも読取（Matrix③のX軸） |
| `ocf_annual` | index.html詳細（テキスト内） | `analyzer.py:494` | 1079行の月次バーン内訳表示 |
| `capex_annual` | index.html詳細（テキスト内） | `analyzer.py:495` | 同上 |
| `verdict` | index.htmlバッジ・pillar-label | `_runway_verdict()` analyzer.py:529-543 | 1071,1077行 |
| `score` | index.htmlスコア円 | `_overall()` analyzer.py:837 | `s2`表示 |

#### `profitability_path`（`_analyze_profitability_path`, analyzer.py:549-716）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `ocf_annual`（年次dict） | index.html営業CFチャート | `analyzer.py:551-553` | `buildDetail()`938-939行のocfVals、`buildProfitPath`のOCF系列 |
| `ocf_trend` | index.htmlバッジ多数 | `_ocf_trend()` analyzer.py:718-763 | pillar-label、trendCell、サマリー |
| `gaap_breakeven_year`/`gaap_breakeven_reason` | index.html詳細 | `_breakeven_estimate()`(765-801)→`_gaap_margin_breakeven()`(1132-1210, マージン外挿＋OLSフォールバック) | `fmtBe()`1099行 |
| `ocf_breakeven_year`/`ocf_breakeven_reason` | index.htmlテーブル・詳細 | `_breakeven_estimate()`(765-801)→`_margin_breakeven()`(1055-1129) | テーブルbeCell(531-534行)、詳細1098行 |
| `hidden_profit_already` | index.htmlテーブル・詳細 | `_breakeven_estimate()`analyzer.py:787 | beCell(533行)、詳細1097行 |
| `discontinuous_growth` | index.html詳細（警告） | `analyzer.py:606-627`（OLS使用時のみ、直近YoY≥200%かつ過去比3倍超で検出） | 1100,1108行 |
| `discontinuous_growth_note` | index.html詳細 | `analyzer.py:627` | 1100行の警告文 |
| `incremental_margin` | index.html拡大再生産バー | `_calc_incremental_margin()`(1020-1042)を`analyze:630`で呼出 | 984-990行の`reproDetailText` |
| `incremental_margin_prev` | 同上 | `analyzer.py:645-647` | reproTrendText差分計算(984-987行) |
| `incremental_margin_trend` | 同上 | `analyzer.py:648-665`（OLS回帰スロープ判定） | reproTrendText分岐 |
| `incremental_rev_delta`/`incremental_gp_delta` | 同上 | `analyzer.py:641-643` | reproDetailText(989-990行) |
| `reproduction_score` | index.html拡大再生産バー（●○表示） | `analyzer.py:669-680` | `reproDots`(982行) |
| `reproduction_label` | 同上 | `analyzer.py:682-693` | `repro-label`表示 |
| `score` | index.htmlスコア円 | `_overall()` analyzer.py:838 | `s3`表示 |

#### `financial_vectors.fields.{Revenue,GrossProfit,OperatingIncome,RD,NetIncome,OCF,CapEx}`

計算元: `financial_trend_calculator.py`の`compute_vectors()`（230-405行）。`pipeline.py:176-184`が`load_all_normalized()`（408-421行）と併せて呼出し、`results[ticker]["financial_vectors"]`に格納。

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `fields.{name}.yoy/qoq.change_pct,val_latest,val_prev,end_latest,end_prev,fp` | index.html spark統計・ヒートマップ | `_calc_yoy_change()`(151-190)/`_calc_qoq_change()`(193-211)、`compute_vectors:335-361`で格納 | sparkCols(1160-1176行)、hmRows(1205-1225行、独自にQoQ再計算もしている点に注意=1210-1219行) |
| `fields.{name}.yoy/qoq.percentile` | 未直接表示（角度算出の中間値） | `_calc_percentile()`(276-289)、`compute_vectors:346` | HTML上は角度化された値のみ利用、percentile自体は非表示 |
| `fields.{name}.yoy/qoq.angle,length` | チャート未直接使用だが将来利用想定 | `_pct_to_angle()`(214-222)/`_pct_to_length()`(225-227)、`compute_vectors:347-348` | index.html grep上は未参照。ただしJSON出力＝正式仕様のため一覧には含める |
| `fields.{name}.series_q`（四半期時系列） | index.html sparkline・ヒートマップ・黒字化ロードマップ | `compute_vectors:323-333`（Q4逆算含む`_build_q4_implied:86-129`） | `initFvCharts()`のChart.js描画(1311-1364行)、`buildProfitPath()`のgetSeries/getLatest(708-726行、CapEx込みFCF系列算出にも使用) |

（`financial_vectors.composite`・`financial_vectors.data_quality`は削除候補として未使用を確認。index.html全体を検索しても`fv.composite`/`fv.data_quality`の参照なし）

#### クライアント側の他サブシステムデータ結合（STONKS SILO自身のJSON外）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| TANUKIスコアバッジ | index.htmlティッカー横 | `loadTanukiBadges()` index.html:428-446 | `../tanuki_valuation/data/{ticker}/latest.json`の`tanuki_score`を読取 |
| 次回決算日 | index.html詳細 | `toggleDetail()` index.html:611-619 | 同上`latest.json`の`next_earnings_date` |
| 黒字転換目算（Adj.EPS線形推定） | index.html詳細 | `toggleDetail()` index.html:620-627 | 同上`latest.json`の`breakeven_estimate` |
| Adj.EPS系列（黒字化ロードマップ） | index.html「黒字化への道のり」 | `toggleDetail()` index.html:631-680 | `adjusted_eps_analyzer/data/{ticker}/quarterly.json`の`quarters[].adjusted_eps` |

### 5-4. MACRO PULSE

#### FEDレジームバー（`#regimeBar`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| REGIME | `rb-regime` | 05_main.py: `analyze_fomc_with_grok()`(1218-1271) / `_fallback_regime()`(1207-1216) → `update_fed_context()`(1273-1345)がfed_context.csvの`regime`列に保存／index.html: `renderRegimeBar()`(979-1001) | CSV値をそのまま表示（加工は大文字化と枠色分岐のみ） |
| regime_source | `rb-regime-src` | 同上（`analyze_fomc_with_grok`は"FOMC声明分析（Grok）"、`_fallback_regime`は"DGS1数値ベース"を設定） | XAI_API_KEY未設定/失敗時はDGS1ベースにフォールバック |
| FF RATE | `rb-ff` | 05_main.py: `get_ff_current()`(727-735, DFEDTARU/DFEDTARL平均、失敗時FEDFUNDS) → `update_fed_context()`(1291-1293、取得失敗時3.625固定フォールバック)／index.html: `renderRegimeBar()` | |
| 1Y EXPECTED FF | `rb-exp` | 05_main.py: `get_implied_cuts()`(737-753、FRED:DGS1をそのまま採用) / エイリアス`get_zq_futures()`(757-758) → `update_fed_context()`(1290)／index.html: `renderRegimeBar()` | 旧ZQ先物ロジックは廃止済み、DGS1直採用 |
| IMPLIED CUTS | `rb-cuts` | 05_main.py: `update_fed_context()`内でインライン計算 `(ff_current - zq_rate) / 0.25`(1295-1297)／index.html: `renderRegimeBar()` | |
| FRB主眼(dominant_label) | `rb-concern` | 05_main.py: `analyze_fomc_with_grok()`/`_fallback_regime()` → `update_fed_context()`／index.html: `renderRegimeBar()` | |
| 判断理由(ai_reason) | `rb-reason` | 同上 | |
| FOMC日付 | `rb-concern-label`のツールチップ | 05_main.py: `fetch_latest_fomc_statement()`(1149-1205、FRB声明カレンダーHTMLスクレイピング＋既知日付フォールバック) → `update_fed_context()`の`new_row["fomc_date"]`(1328)／index.html: `renderRegimeBar()`(996-998) | |

#### ティッカー（`.ticker`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| S&P500現在値 | `tk-sp` | 05_main.py: `get_sp500()`(825-830、FRED SP500優先→stooqフォールバック) → `run()`内で`row["sp500_t0"]`に格納(2211, 2220)、events.csvへ保存／index.html: `updateTicker()`(1006-1018)がDATA中の最新日`sp500_t0`をスキャン | |
| S&P500前日比 | `tk-sp-c` | index.html: `updateTicker()`(1020-1043)のみで計算。events.csvの日別`sp500_t0`から直近2日分を抽出し差分・騰落率を算出 | バックエンドに対応する計算なし。frontend専用ロジック |
| 10Y-2Y SPREAD | `tk-yc` | 05_main.py: `fetch_event_row()`(896-956)がFRED `T10Y2Y`（`INDICATOR_CONFIG["Yield Curve 10Y-2Y"]`, 300-308）を取得、`run()`の日次ループ(2217-2223)で毎日1行events.csvへ追加／index.html: `updateTicker()`(1008, 1045)が`idxLatestAsOf()`で最新値取得 | |
| 10Y-2Y判定(INVERTED/FLAT/NORMAL) | `tk-yc-i` | index.html: `updateTicker()`(1045) `yc<-0.2:INVERTED / yc<0.5:FLAT / else NORMAL` | frontend専用の閾値。②Health Bars（L2_CFG: bull 0.5/bear -0.2）や①フェーズゲージ内のYC閾値（-0.5/0/0.5）とは別の第3の閾値セット |
| HY SPREAD | `tk-hy` | 05_main.py: `fetch_event_row()`が FRED `BAMLH0A0HYM2`（`INDICATOR_CONFIG["HY Spread"]`, 309-317）を取得、同じ日次ループでevents.csvへ追加／index.html: `updateTicker()`(1009, 1046) | 流動性モニターのHYスプレッドカードとは別経路。同一FRED系列を2箇所で独立に取得・保存している |
| LAST UPDATE | `tk-last` / `tk-src` | index.html: `updateTicker()`(1049-1062)のみ。全指標のIND_INDEXを走査し最新`release_date`とその行の`data_source`列（backendの`fetch_event_row()`953-954で"FRED"/"manual"/"N/A"を設定）を表示 | frontend計算だがdata_source自体はbackend由来 |
| （画面最上部）最終更新表示 | `#last-updated` | 05_main.py: `update_liquidity_csv()`末尾(2126-2130)が`05_meta.json`の`generated_at`（JST）を書き込み／index.html: `loadLiquidityData()`(2730-2750)が`toJST()`で整形して表示 | 上記`tk-last`とは別の値・別経路。流動性CSV更新時のみ更新される |

#### 流動性モニター（`.liq-wrap`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| M2 | `liqGrid`カード | 05_main.py: `update_liquidity_csv()`内 FRED `M2SL`取得(1952)、carry-forward処理(2004-2020)含め保存(2096)／index.html: `renderLiquidityCards()`(2373-2582)が`latestNonEmpty()`(2365-2371)で表示 | |
| NET LIQUIDITY | 同上 | 05_main.py: `update_liquidity_csv()`内 `net_liq = (fed_val - tga_val - rrp_val) / 1_000_000`(1973-1977、carry-forward後に再計算2022-2025)／index.html: `renderLiquidityCards()` | |
| HYスプレッド（流動性カード） | 同上 | 05_main.py: `update_liquidity_csv()`内 FRED `BAMLH0A0HYM2`取得(1956)、events.csv経路とは独立の取得・保存(2097)／index.html: `renderLiquidityCards()` | ②ティッカーのHY SPREADと二重取得（同一系列を別CSVに別途保存） |
| FRBバランスシート | 同上 | 05_main.py: FRED `WALCL`取得(1954)、保存(2098)／index.html: `renderLiquidityCards()` | |
| 各カードの前月比/前週比(chg) | 同上 | index.html: `chgHtml()`(2383-2392)、`liqPrevVal()`(2354-2362)がCSV内の過去行と比較して算出 | frontend計算 |
| 各カードのパーセンタイル/水準バー | 同上 | index.html: `pctRank()`(2415-2420)、`levelBar()`(2475-2484)が過去全履歴内での順位を算出 | frontend計算のみ、backendに対応ロジックなし |
| 各カードの解説コメント(m2Comment/nlComment/hyComment/fedComment) | 同上 | index.html: 2438-2467 | frontend専用のルールベース文言生成 |
| Hollow Rallyバッジ | `liq-wrap`直下 | index.html: `renderLiquidityCards()`(2533-2559) `rows.sp500`列とNET LIQUIDITY週比を条件判定 | 注意: `LIQUIDITY_COLUMNS`(05_main.py 1934-1941)に`sp500`列は存在しない。`rows.filter(r=>r.sp500!==undefined)`は常に空集合となり、現行データパイプラインではこの条件分岐が実質到達不能（バッジが表示されることはない）。削除候補には含まれていなかった追加の要確認箇所 |
| ステルス流動性 LAYER1（FRB政策意図） | `stealthLayer1` | 05_main.py: `update_fed_context()`が書き込む`regime`列／index.html: `updateStealthLayer1()`(2703-2717)が`05_fed_context.csv`を別途fetchして表示 | 上部REGIMEバーと同じ列を独立に再取得表示 |
| LAYER2（ステルス供給/吸収バッジ） | `stealthLayer2`相当 | 05_main.py: `update_liquidity_csv()`内「ステルス流動性シグナル計算」ブロック(2027-2049) RRP/TGA/準備預金の増減から`stealth_signal`列を決定／index.html: `renderStealthCard()`(2585-2700) | |
| LAYER3（NET流動性連続減少週数） | `stealthLayer3`相当 | 05_main.py: `update_liquidity_csv()`内(2063-2073) `net_liq_decline_weeks`列を算出／index.html: `renderStealthCard()` | |
| 警戒アラート文 | ステルスカード内 | 05_main.py: `update_liquidity_csv()`内(2084-2092) `stealth_alert`列（`\|`区切り）／index.html: `renderStealthCard()`(2653-2659) | |
| ステルス吸収週数(stealth_absorb_weeks) | ステルスカード内Layer2補足 | 05_main.py: `update_liquidity_csv()`(2053-2061)／index.html: `renderStealthCard()`(2677) | |
| REPO残高(RRPONTSYD) | ステルスカード内metric | 05_main.py: FRED `RRPONTSYD`取得後 ×1000でMillionsに換算(1962-1963)、保存(2100)／index.html: `renderStealthCard()`のmetrics配列(2620-2628) | |
| 準備預金(WRBWFRBL) | 同上 | 05_main.py: FRED `WRBWFRBL`取得(1966-1967)、保存(2102)／index.html: 同上(2629-2636) | |
| TGA残高(WTREGEN) | 同上 | 05_main.py: FRED `WTREGEN`（失敗時`FTSD`）取得(1957-1960)、保存(2099)／index.html: 同上(2637-2644) | |

#### ①景気フェーズ判定（`#phaseGauge`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| フェーズbadge / phase-sub | `pg-phase-badge`/`pg-phase-sub` | index.html: `computeCurrentScore()`(1070-1149、8指標の値取得とステップ関数式スコア化) → `renderPhaseGauge()`(1151-1215、score<30/52/70でフェーズ判定) | 完全にfrontend計算。events.csvの各指標`actual`列を直接読み込んで再計算しており、backendに対応する「表示用スコア」の生成関数はない |
| RECESSION RISK SCOREバー・マーカー | `pg-track-fill`/`pg-track-marker` | 同上 `renderPhaseGauge()` | |
| RECESSION RISK SCORE数値 | `pg-score-num` | 同上 | 既知バグ: 境界値は実装上30だが画面下部の目盛り表示は25のまま |
| シグナルテキスト | `pg-signal-text` | `renderPhaseGauge()`(1162-1165) bearCount/cautionCountの集計 | |
| ALERTバナー | `pg-alert`/`pg-alert-msg` | `renderPhaseGauge()`(1177-1182) `bearCount>=3 && score>=52` | |
| 8指標シグナルグリッド | `pg-signals` | `computeCurrentScore()`内で各指標ごとにscore/signal/weight/lead/desc/threshを算出(1096-1148)、`renderPhaseGauge()`(1191-1214)でHTML化 | |
| スコア比較バー（3ヶ月前/2ヶ月前/前月比/先週比/カスタム） | `#compareBar` | index.html: `renderCompareBar()`(2093-2131) → `computeScoreAsOf()`(1990-2076) | `computeScoreAsOf()`は「現在」時点は`computeCurrentScore()`を再利用するが、過去日付では`calcSignal()`内でlerp補間する別ロジック（1990-2076内`calcSignal`）を使用。ステップ関数（現在値用）とlerp補間（過去値用）で2種類の計算式が併存 |

バックエンド側の対応スコア計算: 05_main.py `_compute_current_score()`(1378-1486)は上記①ゲージの表示には使われず、週次AI解説用に独立して動く。同一の閾値・重みをPython側に再実装しており（コメントにも「renderPhaseGaugeと同一ロジック」と明記、1445-1446）、frontend/backendで計算ロジックが二重管理されている。

#### マクロサプライズバナー（`#surpriseBanner`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| surprise_alerts | `surpriseBannerBody` | 05_main.py: `detect_macro_surprises()`(124-192、前回比が`_SURPRISE_THRESHOLDS`を超えた指標を検知、複合カテゴリサプライズも検知) → `run_weekly_analysis()`(1729)で呼び出し、weekly_analysis.csvの`surprise_alerts`列に保存(1743)／index.html: `renderWeeklyAnalysis()`(2192-2222)がセミコロン分割・カテゴリバッジ化して表示 | 週次バッチでのみ更新（日次では更新されない） |

#### AI WEEKLY COMMENTARY（`.ai-wrap`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| 週次カード日付/スコア/フェーズ | `ai-card-date`/`ai-card-score`/`ai-card-phase` | 05_main.py: `run_weekly_analysis()`(1655-1766)が`_compute_current_score()`(1378-1486)を呼び出しweekly_analysis.csvの`score`/`phase`列に保存／index.html: `renderWeeklyAnalysis()`(2182-2340) | この`score`は①フェーズゲージのJS計算(`computeCurrentScore()`)とは別のPython再計算値。週次生成時点の値が固定表示される |
| 週差/月差(chg1w/chg1m) | ai-card-header内 | 05_main.py: `_compute_score_change()`(1488-1495)がweekly_analysis.csvの`score_change_1w`/`score_change_1m`列に保存／index.html: `renderWeeklyAnalysis()`(2235-2244) | |
| 総括(summary) | `ai-card-section-text` | 05_main.py: `generate_weekly_analysis_with_grok()`(1520-1640、xAI Grok API呼び出し) / 失敗時`_fallback_weekly_analysis()`(1642-1653) → weekly_analysis.csv `summary`列 | |
| 要因分析(factor_analysis) | 同上 | 同上 | |
| 注視ポイント(watchpoints) | 同上 | 同上 | |
| 各指標コメント(indicator_comments) | `ai-card-indicators`内チップ | 同上（Grok出力の`;`区切りテキスト） → index.html `renderWeeklyAnalysis()`(2277-2303)でパース・チップ化 | |
| 週差/月差バッジ(各指標) | チップ内`deltaBadge` | 05_main.py: `run_weekly_analysis()`内`indicator_deltas`計算(1672-1685、`_compute_current_score()`の1週間前/1ヶ月前スナップショットとの差分) → weekly_analysis.csv `indicator_deltas`列 ／index.html: `deltaBadge()`(2264-2274) | |
| model表示 | ai-card下部 | 05_main.py: `generate_weekly_analysis_with_grok()`のモデル試行ループ(1602-1636、grok-3-mini→grok-3→grok-2-1212の順にフォールバック) → weekly_analysis.csv `model`列 | |

#### ②Indicator Health Bars（`#l2Grid`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| 8指標の値/シグナル(BULL/CAUTION/NEUTRAL/BEAR)/バー位置 | `l2-row`各行 | index.html: `renderL2()`(1220-1314)、指標値は`idxLatestAsOf()`でevents.csv由来、閾値は`L2_CFG`配列(1227-1240)にハードコード | 既知の二重管理: `05_main.py`の`INDICATOR_CONFIG`（197-327、threshold_bull/threshold_bear列、削除候補）とは独立にindex.html側で全閾値・レンジ(rMin/rMax)を再定義している |

#### ③RECESSION RISK SCORE推移チャート（`#scoreHistoryChart`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| スコア推移折れ線 | `scoreHistoryChart` | index.html: `renderScoreHistory()`(1631-1780) → `buildScoreTimeSeries()`(1598-1629) → `computeScoreAsOf()`(1990-2076、lerp補間版) | 完全frontend計算。比較バーと同じ`computeScoreAsOf()`を共用 |
| NBER後退期帯 | 同上マークエリア | index.html: ハードコード定数`NBER_RECESSIONS`(1577-1586) | 計算ではなく静的データ |
| フェーズゾーン背景(0-25/25-52/52-70/70-100) | 同上 | index.html: `renderScoreHistory()`内`zoneMarkAreas`(1669-1680) | |
| 期間切替(1年/3年/5年/全期間)ボタン | `.score-range-btn` | index.html: `setScoreRange()`(1590-1596) | UI状態のみ、値の計算は上記と同じ |

#### ④類似度レーダーチャート（`#l3Chart`, `#l3Scores`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| レーダーチャート（現在/2019/2001/スライダー） | `l3Chart` | index.html: `renderL3()`(1782-1792) → `l3norm()`(1349-1352、指標を0-100正規化) → `drawL3Chart()`(1478-1569) | `L3_INDICATORS`(1329-1338)のmin/maxもハードコード、①フェーズゲージ・②Health Barsとはまた別の正規化レンジ定義 |
| 類似度スコア(2019年/2001年、%) | `l3Scores`内 | index.html: `l3similarity()`(1354-1359、ユークリッド距離ベース) | REF_DATE_2019/2001(1341-1342)もハードコード定数 |
| スライダー（過去に戻る） | `#l3Slider` | index.html: `buildL3Snapshots()`(1372-1423)、`onL3SliderInput()`(1425-1442)、`resetL3Slider()`(1444-1476) | スライダー移動時のスコア表示(`l3SliderScore`)は`computeScoreAsOf()`(1990-2076)を再利用 |

#### ⑤RECENT SIGNALS（`#recentSignals`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| DATE/INDICATOR/ACTUAL | `signals-table` | 05_main.py: `fetch_event_row()`(896-956)がevents.csvの`actual`/`release_date`/`indicator`列を生成／index.html: `renderRecentSignals()`(1797-1900、直近90日をIND_INDEXから抽出) | |
| PREV | 同上 | index.html: `renderRecentSignals()`内で1つ前のIND_INDEXエントリを参照(1816-1817) | CSVの直前行を単純に前値として使用（サプライズ用の`consensus`列とは無関係） |
| DIR(↑/↓/→)・CHANGE | 同上 | index.html: `renderRecentSignals()`(1854-1876) `BULL_UP`/`BULL_DOWN`セットで方向色分け、差分と閾値判定 | frontend専用計算 |

#### ⑥発表スケジュール（`#schedGrid`）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| DATE/INDICATOR | `sched-table` | 05_main.py: `update_schedule()`(520-609)が`fred_release_dates()`(458-498)・`michigan_release_dates()`(438-453)・`building_permit_release_dates()`(424-436)・`michigan_consumer_sentiment_release_dates()`(408-422)から05_indicator_schedule.csvへ書き込み／index.html: `renderSchedule()`(1905-1952)が今後14日分をフィルタ表示 | |
| DAYS | 同上 | index.html: `renderSchedule()`(1929-1937) `diffDays`をJSで計算 | |
| CONSENSUS | 同上 | 05_indicator_schedule.csvの`consensus`列を直接表示 | この列は`update_schedule()`では常に空文字で初期化。実際の値は運用者が手動でCSVに入力する運用（Discordリマインダー`remind_manual_indicators()`566-647が入力を促す）。計算値ではなく手入力値 |

#### その他の付随ルート（参考）

- events.csvのactual値自体: `fetch_event_row()`(896-956)がFREDから取得。NFPのみ`fred_latest_with_prev()`(701-725)で水準値を前月差に変換(924-932)。月次指標の欠測補完は`refresh_monthly_indicators()`(1783-1863)、重複排除は`dedupe_new_rows()`(1868-1922)が担当。これらは①〜⑥すべての表示の入力データとなる共通の計算経路。
- AI週次解説の`recent_events`コンテキスト（`surprise`/`consensus`列を含む）: `_get_recent_events_summary()`(1497-1518)が生成しGrokプロンプトに渡す。この`surprise`値自体は画面に直接数値表示されないが、AIが生成する`summary`/`factor_analysis`テキストに間接的に反映される。

#### frontend/backend二重計算のまとめ

1. ①RECESSION RISK SCORE本体: index.html `computeCurrentScore()`（ステップ関数）が唯一の表示計算経路。05_main.py `_compute_current_score()`は週次AI解説用の別計算で画面ゲージには使われない。
2. 過去日付スコア（比較バー・スコア推移チャート・L3スライダー）: index.html `computeScoreAsOf()`内の`calcSignal()`がlerp補間を使う第3の計算式。
3. ②Health Bars閾値: index.html `L2_CFG`が独自定義（既知の重複、`INDICATOR_CONFIG`側は未参照）。
4. YC/HY閾値: ティッカー判定(-0.2/0.5)、②Health Bars(bull 0.5/bear -0.2)、①フェーズゲージ(-0.5/0/0.5)で3種類の閾値セットが並存。
5. HYスプレッド: ティッカー用（events.csv経由）と流動性モニターカード用（liquidity.csv経由）で同一FRED系列(`BAMLH0A0HYM2`)を独立に2回取得・保存。
6. Hollow Rallyバッジ: `LIQUIDITY_COLUMNS`に`sp500`列が存在せず、判定条件が実質的に到達不能（要確認事項として追加報告）。

### 5-5. Discover

#### カタリスト（catalyst.json / catalyst.html）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `catalysts[].id` | catalyst.json / catalyst.html | `src/discover/catalyst.py:next_id`(81-88) → `process_ticker`(173) で採番 | |
| `catalysts[].title/detail/timing/importance/type/probability` | catalyst.json / catalyst.html | `catalyst.py:discover_catalysts`(93-117, Grok呼び出し・JSON抽出) → `process_ticker`(172-186, 値の正規化・デフォルト補完) | |
| `catalysts[].status` | catalyst.json / catalyst.html | 初期値`"未達"`は`process_ticker`(183)。以降は`reevaluate_catalysts`(120-151, Grok再評価)→`process_ticker`(195-203)で更新 | |
| `catalysts[].first_detected` | catalyst.json / catalyst.html | `process_ticker`(184) `= today` | |
| `tickers{}.updated_at` | catalyst.json / catalyst.html(`tc-updated`) | `process_ticker`の戻り値(210-213)。`main`(277-278)でマージし保存 | |
| 影響予測`{direction, magnitude, thesis_effect, summary}` | impact_predictions_*.json / catalyst.html・news_history.html（`renderImpact`） | `src/discover/impact_predictor.py:predict_for_items`(80-102, Grok呼び出し) → `_normalize_prediction`(72-77, 値域チェック) | catalyst向け=`run_catalyst`(167-212)、news向け=`run_news`(116-162)の2つの呼び出し経路があるが計算関数自体は共通 |

#### 日次ニュース分類・候補・テーマ（daily_report.json / index.html）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `tickers{}.category/memo` | daily_report.json / index.html | `collect.py:main`(369, 389-390) — `config/discover_config.json`からの単純パススルー（計算なし） | `memo`は`docs/discover/admin.html:saveDiscoverConfig`(317-335)で人手編集しGitHub API経由でconfig更新 |
| `classified.items[].{title,category,importance,summary,url,source,published_at}` | daily_report.json / index.html | 経路①`collect.py:classify_news`(107-161, NEWS_API記事+Grok分類) / 経路②`classify_news_with_grok_search`(164-202, NEWS_API 0件時のGrok代替検索)。いずれも`_dedupe_items`(93-104)で重複除去 | どちらが使われるかは`main`(381-387)の分岐（NEWS_API結果有無・category）による |
| `classified.summary` | daily_report.json / index.html | 上記と同一（Grok応答の`summary`キー） | 経路①②同様 |
| `classified.conditions_met[]` / `classified.risk_flags[]` | daily_report.json / index.html（`buildConditionsPanel`, 257-273） | 上記と同一関数のGrok応答（プロンプトで`conditions_met`/`risk_flags`を指示、collect.py:149, 188-189） | news_history側の日次・銘柄単位の同名フィールドは削除候補だが、daily_report.json側はindex.htmlで実際に表示されているため対象外ではない |
| `top_importance`（tickers[ticker]直下） | daily_report.json / index.html | `collect.py:main`(392) `= classified.get("top_importance","低")` | `classified.top_importance`（Grok応答）の複製。表示側は`data.top_importance`（複製後の値）を参照 |
| `candidates[].{ticker,company,sector,reason,risk}` | daily_report.json / index.html | `collect.py:explore_candidates`(205-241, Grok Web検索プロンプト+JSON抽出) | |
| `candidates[].screening_pass[]` | 同上 | 同上（Grok応答の`screening_pass`キー、collect.py:230） | |
| `candidates[].catalyst_type` | 同上 | 同上（Grok応答の`catalyst_type`キー） | |
| `candidates[].conviction` | 同上 | 同上（Grok応答の`conviction`キー） | |
| `macro_themes[].{theme,horizon,conviction,background,catalyst}` | daily_report.json / index.html | `collect.py:explore_macro_themes`(244-292, Grok Web検索、日曜のみ実行`main`400-414) | 日曜以外は前回`daily_report.json`から引き継ぎ（`main`415-422） |
| `macro_themes[].related_tickers[].{ticker,role,note}` | 同上 | `explore_macro_themes`内Grok応答（254-278） | index.html側`buildRelatedTickers`(594-630)はrole別グルーピング表示のみ、値の再計算なし |
| `macro_themes[].sources[]` | 同上 | 同上（Grok応答の`sources`キー） | |
| `macro_themes[].generated_at` | 同上 | `explore_macro_themes`(287-288) `theme["generated_at"]=today` | |
| `price_change_next_day` | news_history_*.json / news_history.html | `collect.py:get_price_change`(295-307, yfinance 2日終値比) → `add_price_changes_to_yesterday`(310-333)で前日分の履歴JSONに事後付加 | 当日の`daily_report.json`側itemsには付かない（`append_to_monthly_history`336-363で明示的に除外、352行目） |
| `theme_config`（テーマID/ラベル/カラー） | config/theme_config.json / index.html（テーマフィルタ・バッジ色）・admin.html | 静的設定ファイル。計算ロジックなし。`docs/discover/admin.html:renderThemeEditor/saveThemeConfig`(228-287)で人手編集しGitHub commit | |
| `discover_config`（銘柄別category/memo/themes） | config/discover_config.json / index.html・admin.html | 静的設定ファイル。`admin.html:renderTickerEditor/saveDiscoverConfig`(290-335)で人手編集 | |

補足: index.htmlの`loadData`(446-458)は`macro_themes_history.json`から`themeStreakMap`（🔥N週連続バッジ）をクライアント側でのみ算出。サーバー側には保存されない純粋な表示専用の派生値。

### 5-6. EPS Analyzer

#### quarterly.json（四半期データ）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `ticker` / `last_updated` | quarterly.json | `pipeline.py:process_one_ticker`(626-630) | |
| `quarters[].filing_date/period_end/fiscal_year/quarter` | quarterly.json / stock.html（チャートラベル`formatLabel`849-859） | `extract_key_facts.py:extract_quarterly_facts`（quarters_map構築554-561、最終確定1024-1029）→ `pipeline.py:process_one_ticker`(532, 539-541)でコピー | |
| `quarters[].gaap_eps/adjusted_eps/gaap_net_income/adjusted_net_income/diluted_shares_used/adjustments/net_adjustment_total` | quarterly.json / stock.html（メトリクスカード・ウォーターフォール・チャート） | 基本経路: `eps_calculator.py:calculate_eps`(10-50) | 複数経路あり（下記参照）。分割補正・DTA検出・公正価値自動検出が事後的に上書きする |
| `quarters[].adjustments[].item_name/reason/extracted_from` | quarterly.json / stock.html（調整内訳テーブル`buildAdjHtml`1027-1064） | 通常項目: `adjustment_detector.py:detect_adjustments`(86-147, item_name:136, reason:141, extracted_from:142) | 下記の通りDTA・公正価値ルートでも別途生成される |
| `quarters[].adjustments[].net_amount` | 同上 | `tax_adjuster.py:apply_tax_adjustments`(41-57, net_amount:53) | |
| `quarters[].ai_analysis.health/comment` | quarterly.json / stock.html（AdjEPS信頼性バッジ・AI分析欄`updateAI`814-847） | `ai_analyzer.py:analyze_adjustments`(64-152, Grok応答から取得) → `pipeline.py:process_one_ticker`(613-619)で最新四半期にのみ付与 | 重要: この`health`は英語enum（Excellent/Good/Caution/Warning/Error）。summary.json/tickers.htmlの`health`（日本語enum、後述）とは値ドメインが異なる別概念で混同注意 |
| `quarters[].ai_analysis.sources[].item/snippet/confidence` | quarterly.json / stock.html | `ai_analyzer.py:analyze_adjustments`(114, Grok応答)。confidenceは115-123行で0.0-1.0にクランプ・丸め | stock.htmlの調整内訳テーブルでは`buildAdjHtml`(1039-1042)が`item_name`/`item_id`一致でsourcesとクライアント側JOINし、行ごとのconfidenceバーを表示 |
| `quarters[].special_flags(EPS_DISCREPANCY)` / `special_notes.eps_discrepancy` | quarterly.json / stock.html（⚠️EPS差分ツールチップ`updateMetricsWithQuarter`754-805） | `pipeline.py:check_eps_discrepancy`(66-138, Alpha Vantage比較) → `process_one_ticker`(579-593)で`EPS_CHECK_TICKERS=['SOUN','CELH']`のみに適用 | 同じフラグ値がもう1経路で発生: `fair_value_detector.py:apply_fair_value_detection`(377-380)も全銘柄対象に同一フラグを立てるが、こちらは`special_notes.fair_value_auto_detect`という別キーに詳細を格納（383-404）。両者は独立でどちらか一方または両方が付く |

#### `adjusted_eps`等の複数計算経路（重要・見落とし注意）

pipeline.pyの実行順序（551行→556行→597行）に沿って、以下3経路が同一四半期に対して段階的に上書きする可能性がある。

1. 基本値: `eps_calculator.py:calculate_eps`(10-50) — `pipeline.py:process_one_ticker`(531)で全四半期に適用
2. 株式分割補正: `pipeline.py:apply_split_adjustments`(154-205, 呼び出し553) — `diluted_shares_used/diluted_shares/gaap_eps/adjusted_eps`を分割比率で再計算（196-199行）
3. DTA（繰延税金資産）補正: `pipeline.py:apply_dta_adjustments`(208-273, 呼び出し556) — 検出条件を満たす四半期のみ`adjusted_net_income/adjusted_eps/net_adjustment_total`を再計算し、合成調整項目`{item_name:"DTA認識（繰延税金資産）除外", net_amount, note}`を`adjustments`に追加（261-271）。この合成項目には`reason`キーがなく`note`キーのみ（他ルートと構造が異なる）
4. 公正価値変動自動検出: `fair_value_detector.py:apply_fair_value_detection`(234-408, 呼び出し597) — `_scan_for_fv_items`(108-186)で条件を満たす四半期に調整項目を追加し、`adjustments/net_adjustment_total/adjusted_net_income/adjusted_eps`を再計算（339-369）

#### summary.json / ttm.json（ダッシュボード集計値）

| 項目名 | 出力先 | 計算ルート | 補足 |
|---|---|---|---|
| `ticker/company_name/latest_filing_date` | summary.json / index.html・tickers.html | `pipeline.py:generate_summary`(346-411, 393-397)。`company_name`は`process_one_ticker`(644)で`ticker_to_name`(cik_lookup.csv)→`metadata['name']`(SEC Submissions API, `company_metadata.py:get_company_metadata`14-44)の順にフォールバック | |
| `gaap_eps/adjusted_eps` | summary.json / index.html・tickers.html | `generate_summary`(373-374) — 最新四半期(`quarters[0]`)の値をそのまま転記 | |
| `eps_diff` | summary.json / index.html | `generate_summary`(400) `round(adj_eps-gaap_eps,4)` | stock.htmlは`diff = q.adjusted_eps - q.gaap_eps`(793)をクライアント側で再計算（丸めなし）。同一概念の別経路 |
| `eps_ratio` | summary.json / index.html | `generate_summary`(375, 401) `(adj_eps-gaap_eps)/|gaap_eps|*100` | |
| `gaap_to_adj_positive` | summary.json / index.html | `generate_summary`(402) `gaap_eps<0 and adj_eps>0` | |
| `yoy_growth` | summary.json / tickers.html・index.html | `generate_summary`(366-370) — `quarters[0]`と`quarters[4]`（4期前）の`adjusted_eps`比較 | stock.htmlは`calculateYoY`(730-752)で独立に再計算：日付フィルタ後の最新四半期と「前年同一暦四半期」を優先照合し、なければidx-4にフォールバック。同一概念だがロジックが異なる別経路で値が一致しない場合がある |
| `health` | summary.json / tickers.html・index.html | `generate_summary`(372-392) — `eps_ratio`に基づく閾値判定（日本語enum：調整なし/調整小/調整中/調整大/過大調整/調整小（マイナス）） | `ai_analysis.health`（英語enum）とは別概念（同名だが別ドメイン、混同注意） |
| `deviation_rate` | index.html（テーブル・投資機会ランキング） | サーバー側には存在しない。`index.html`(230-240)がTANUKIの`../tanuki_valuation/data/{ticker}/latest.json`を都度fetchし`upside_percent/100`で算出（クライアント側ライブ計算） | stock.htmlのPER比較欄とは別の取得先・別計算（下記参照） |
| `ttm.json`（`ttm[].period/net_income/adjusted_income/diluted_shares/eps/adjusted_eps`） | ttm.json / stock.html（TTMタブ） | `pipeline.py:calculate_ttm`(288-304) — 直近4四半期の合算・平均 | |

#### TANUKI由来フィールド（`per`/`per_adjusted`/`next_earnings_date`）

stock.htmlは`../tanuki_valuation/data/{ticker}/latest.json`をfetch（567行）し、`updateTanukiInfo`(592-630)でそのまま表示（再計算なし。`per-delta`のみ`perAdj-perGaap`をクライアント側で算出、619行）。TANUKI側の算出元は以下の通り。

| 項目名 | TANUKI側の計算ルート | 補足 |
|---|---|---|
| `components.per`（GAAP PER） | `src/value/tanuki_valuation/data_fetcher.py:get_financials`(513-523) — yfinanceの`trailingPE`優先・`forwardPE`フォールバック → `core_calculator.py:calculate_pt`(900)で`components.per`に格納 | |
| `components.per_adjusted` | `src/value/tanuki_valuation/core_calculator.py:_calc_adjusted_per`(930-962) → `calculate_pt`(902-906)で呼び出し | EPS Analyzer自身の`quarterly.json`を直接読みに行く（947行：`docs/value-monitor/adjusted_eps_analyzer/data/{ticker}/quarterly.json`）。直近4四半期の`adjusted_eps`合計で現在株価を割る。**EPS Analyzer→TANUKI→EPS Analyzer(stock.html)という一方向の周回参照になっている点に注意** |
| `next_earnings_date` | `src/value/tanuki_valuation/pipeline.py:_load_extra_data`(2305, 本体2625-2649) | yfinanceの`calendar["Earnings Date"]`から本日以降の直近日を採用 |

#### 追加で判明した留意点

1. `health`は2つの別概念が同名で存在（summary.json系＝日本語enum・ルールベース／`ai_analysis.health`＝英語enum・AI判定）。定義統一時に混同しないよう注意。
2. `eps_diff`・`yoy_growth`はサーバー算出値とstock.htmlのクライアント再計算値が別ロジックのため乖離しうる。
3. `quarters[].adjustments[]`は起源が3経路（通常検出／DTA合成／公正価値自動検出）あり、DTA合成項目のみ`reason`キーを持たない構造上の非対称性がある。
4. `special_flags`の`EPS_DISCREPANCY`も起源が2経路（Alpha Vantage比較／公正価値自動検出）あり、対象銘柄範囲が異なる（前者は`SOUN`/`CELH`限定、後者は全銘柄）。
5. stock.htmlのページタイトルに表示される会社名は`summary.json`の`company_name`ではなく`../../common/company_names.json`という第三の独立ソースから取得している（1121行）。

## 横断的な発見事項まとめ

今回の一連の調査（ステップ1〜5）を通じて、6サブシステムに共通する構造的な問題パターンが見えた。

1. **サーバー計算値とクライアント再計算値の乖離が実データで実証された**。特にTANUKI VALUATIONのstock.htmlで顕著:
   - PEGレシオ: JSON`components.peg=2.69` vs クライアント再計算値≈4.92（AAPL、約1.8倍の乖離）。JSON値は画面に一切表示されず破棄される
   - PSR: JSON`components.ps=10.70` vs クライアント再計算値≈11.61（AAPL、約8.5%乖離）
   - 感応度マトリクスの基準セル: `calcSensIV()`が使う`fcfBase.base_fcf`が実際のDCF計算で使われた`components.fcf_base_used`と異なり、公式理論株価と約18%乖離（AAPL）
   - index.htmlの乖離率: JSONの`upside_percent`を一切参照せず独自に再計算
   「JSONに正しい値があるのに画面はそれを使わず別計算している」パターンが最も実害が大きい。

2. **同一指標名でも複数サブシステム間で定義が異なる**。STONKS SILOの`psr`はAnnual基準（SEC年次revenue分母）、TANUKI/HypeCoreの`psr`/`ps`はTTM基準（yfinance）。`rule40`もHypeCore（rev_yoy+op_margin）とSTONKS SILO（cagr_3yr+operating_income÷revenue）で計算式が異なる。

3. **ステップ1の「削除候補」判定に誤りがあった（3件）**。HypeCoreの`stage_label`/`expectation_score`、STONKS SILOの`revenue_growth_pct`はTANUKI VALUATION側から読まれていた。自サブシステム内のみでの未参照判定は、クロスサブシステム参照を見落とすリスクがある（ステップ5で訂正済み、詳細は各セクション参照）。

4. **判定ロジックがfrontend/backendで二重管理**されている箇所が複数:
   - MACRO PULSEのRECESSION RISK SCOREは3種類の計算式が並存（①フェーズゲージ本体のステップ関数、AI週次解説用のPython再計算、過去日付表示用のlerp補間）
   - HypeCoreの推奨（レコメンド）ロジックが3箇所で別実装（detail.html、index.html、TANUKI pipeline.py内簡略版）
   - MACRO PULSEのYC(10Y-2Y)閾値だけで3種類（ティッカー用-0.2/0.5、②Health Bars用bull0.5/bear-0.2、①フェーズゲージ用-0.5/0/0.5）

5. **データ取得タイミングの非同期性**が乖離の主因になるケースが多い。①乖離率のNVDA 6.5pt差、⑤マルチプルのIONQ 1.75倍差は、いずれもロジックのバグではなく生成日時のズレ（HypeCore3日前、STONKS SILO最大12日前）が主因。

6. **統一すべきレイヤーとすべきでないレイヤーの区別が重要**。DCF計算精度・企業財務品質・マクロ環境は判定対象が異なるドメインであり、フィールドの統合はすべきでない。一方、重大度スケール（RED/AMBER/GREEN等）の表示規約は統一する価値がある。

7. **新規発見の重要度が高いバグ候補**（いずれも今回の調査過程で偶発的に発見、範囲外のため修正はしていない）:
   - EPS Analyzerの`annual.json`が完全に無参照（年次集計パイプラインが丸ごと死んでいる）
   - MACRO PULSEのHollow Rallyバッジが`sp500`列の不在により実質的に到達不能
   - RKLBのTANUKI VALUATIONデータが完全欠損（`latest.json`が存在しない）
   - stock.htmlのPEGレシオ・PSR・感応度マトリクスがJSON値と実質的に無関係な独自再計算値を表示

## 調査で使用した実データ・銘柄一覧（参考）

- ①乖離率突合: AAPL, MSFT, AMZN, META, TSLA, GOOGL, NVDA（7銘柄）
- ⑤マルチプル突合: ASTS, AVAV, BBAI, IONQ, IOT, RKLB, RXRX, SOUN（8銘柄、STONKS SILO対象銘柄）
- stock.html独自計算の実データ検証: AAPL

## 本ドキュメントの位置づけ

本ドキュメントは2026-07-22実施の読み取り専用調査の記録であり、統一定義の実装・データ項目の実際の変更・バグ修正のいずれも行っていない。次ステップ（定義統一・データ項目特定・修正の実施）を行う際の出発点として参照すること。

