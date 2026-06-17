# SYSTEM MAP — On-a-journey

最終更新: 2026-06-17

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
| DISCOVER | 未発掘銘柄の発掘・ニュース収集 | docs/discover/ |
| PORTFOLIO | 保有ポートフォリオ管理 | docs/management/portfolio/ |
| AutoTrade | F&G×TQQQ自動売買 | C:\Users\shigi\AutoTrade\（リポジトリ外） |

---

## データフロー（上流→下流）
【SECデータ取得層】
SEC EDGAR
└─ common/sec_data/update.py
├─ quarterly.py      # 四半期データ取得・正規化
├─ normalizer.py     # フィールド正規化
├─ ttm_calculator.py # TTM系列計算
├─ parser.py         # XBRL解析
└─ extract_key_facts.py  # EPS逆算・株数3段フォールバック（quarterly.json生成）
     ↓ TTMデータ（JSON）
【バリュエーション計算層】
├─ core_calculator.py    # DCF・理論株価
├─ calculator/rice.py    # RICE投資効率
├─ calculator/dcf.py     # DCFエンジン
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
MACRO PULSE   ← FREDデータ / FRBステートメント
DISCOVER      ← Grok Web検索
PORTFOLIO     ← 手動入力 / 証券会社API

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
