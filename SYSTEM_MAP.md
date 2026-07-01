# SYSTEM MAP — On-a-journey

最終更新: 2026-06-26（ALPHA-REDESIGN-1・DISCOVER系新機能・ARCH-DATA-1-FY反映）

---

## システム一覧と責任範囲

| システム | 主な責任 | 出力先 |
|---|---|---|
| TANUKI VALUATION | DCF理論株価・RICE投資効率 | docs/value-monitor/tanuki_valuation/ |
| HypeCore | 期待プレミアム・フェーズ判定 | docs/value-monitor/hypecore/ |
| TANUKI SCORE | 多銘柄比較・最終投資判断 | docs/value-monitor/tanuki_score/ |
| STONKS SILO | 赤字企業の投資適合性評価 | docs/value-monitor/stonks_silo/ |
| EPS ANALYZER | GAAP/Non-GAAP乖離・割安発掘 | docs/value-monitor/eps_analyzer/ |
| MACRO PULSE | マクロ環境・景気後退リスク | docs/market/macro_pulse/ |
| Market Pulse | 市場センチメント・資金フロー | docs/market/market_pulse/ |
| Extreme Fear | 買付支援・TANUKI TOP10・投入額シミュレーター（Market Pulse配下） | docs/value-monitor/extreme-fear/ |
| DISCOVER | 未発掘銘柄の発掘・ニュース収集 | docs/discover/ |
| PORTFOLIO | 保有ポートフォリオ管理 | docs/management/portfolio/ |
| AutoTrade | F&G×TQQQ自動売買 | C:\Users\shigi\AutoTrade\（リポジトリ外） |

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
├─ ttm_calculator.py # TTM系列計算
├─ parser.py         # XBRL解析
├─ extract_key_facts.py  # EPS逆算・株数3段フォールバック（quarterly.json生成）
└─ utils.py  # determine_fiscal_year() — 年度判定共通関数（ARCH-DATA-1-FY 2026-06-25）
     ↓ TTMデータ（JSON）
【バリュエーション計算層】
├─ core_calculator.py    # DCF・理論株価
├─ calculator/rice.py    # RICE投資効率
├─ calculator/dcf.py     # DCFエンジン
├─ calculator/adjustments.py  # alpha計算（参考値保持）・Moat Score計算（ALPHA-REDESIGN-1 2026-06-25）
│   注記: ALPHA-REDESIGN-1によりDCF_v0へのalpha乗算を廃止。
│        競争優位はMoat Score（粗利率・ROIC超過幅・FCFマージン）によるPhase1期間自動計算で表現。
└─ growth_sanity.py      # 成長率サニティチェック
↑ HypeCoreフェーズを参照
     ↓ latest.json（銘柄ごと）
pipeline.py              # 全銘柄を統合・TANUKI SCORE算出
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
DISCOVER      ← Grok Web検索 / NewsAPI
　　ニュース収集・分類: src/discover/collect.py → docs/discover/data/daily_report.json（日次）
　　ニュース履歴: docs/discover/data/news_history_YYYY_MM.json（月別蓄積・翌日騰落率付き）
　　カタリスト発掘: src/discover/catalyst.py → docs/discover/data/catalyst.json（週次）
PORTFOLIO     ← 手動入力 / 証券会社API
TANUKI TAIL（docs/portfolio/tail/）← EDGAR RSS / Grok（KPI提案・四半期レビュー生成）
　　内部統制評価: src/tail/sec_ctrl_fetcher.py → docs/portfolio/tail/data/ctrl/{TICKER}/{QUARTER}.json + latest.json
　　（SEC-CTRL-1 2026-06-24実装、週次自動更新）
　　モーダル構成: coreとsatelliteで同等の6タブ（テーゼ/最新レビュー/KPIトレンド/DCFシナリオ/AI視点/内部統制）
　　（TAIL-SAT-CORE-1 2026-06-26、旧:satelliteは戦略タブのみ）
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
| extract_key_facts.py | EPS quarterly.json 再生成 → report_consistency_check.py（CHECK-17/19確認）|
| core_calculator.py / calculator/dcf.py | 影響銘柄のpipeline.py再実行 |
| calculator/adjustments.py | 影響銘柄のpipeline.py再実行（FCF外れ値・estimate_fcf等）|
| calculator/rice.py | 影響銘柄のpipeline.py再実行 |
| config/maturity_config.json | 影響銘柄のpipeline.py再実行（alpha上限・WACC・成熟度設定変更時）|
| growth_sanity.py | HypeCoreデータ確認 → 影響銘柄のpipeline.py再実行 |
| hypecore結果（hypecore_results.json） | growth_sanity経由でDCF成長率が変わるため影響銘柄のpipeline.py再実行 |
| hypecore_results（poc.json）更新時 | 影響銘柄のpipeline.py再実行（hypecore_history/{TICKER}.jsonが更新される） |
| pipeline.py | audit.py → 全銘柄pipeline.py再実行 |
| Market Pulse / MACRO PULSE 各スクリプト | 独立しているため他システムへの影響なし |

---

## SYSTEM_MAP更新タイミング

以下の変化が生じたときのみ更新する（毎作業ごとの更新は不要）：
- 新しいシステムを追加したとき
- システム間に新しいデータの依存関係が生まれたとき
- 主要ファイルの役割・配置が変わったとき
