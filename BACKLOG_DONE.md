# BACKLOG 完了アーカイブ / アクティブな課題は BACKLOG.md を参照

---

## 2026-06-11 完了

### ✅ BUG-RPO-1 whitelist構造化 (2026-06-11 完了): RPO適用をwhitelist+比率条件に構造化
- _get_rpo_application_rate に via_whitelist フラグを追加（whitelist登録銘柄は比率チェック免除）
- adjust_rpo に RPO/Revenue < 0.3 の比率ゲートを実装（whitelist以外全員適用）
- exclusion_reason を rpo_adjustment に格納、report.txt の RPO_PV 行に除外理由を表示
- V(ratio=0.11)・BSY(ratio=0.18)が除外、GOOGL/MSCI は維持

### ✅ DCF_Reliability=LOW SCORE丸め (2026-06-11 完了): LOWのとき WATCH に統一
- _compute_tanuki_score にて fcf_floor_applied > 0 の場合 SELL/PASS 以外を WATCH に丸める
- score_comment に「DCF信頼性LOW(実績FCF赤字)のためupside依存判定を抑制→WATCH」を付記
- CRWV: HOLD → WATCH に変更（期待通り）

---

## 2026-06-10 完了

### ✅ BUG-FCFBASE-2 (2026-06-10 完了): FCF赤字銘柄DCFガード
- DCF_Reliability: HIGH/LOW を report.txt に追加（revenue_floor適用時 = LOW）
- FCF_Base 表示を調整前後併記（実績avg: $-XX.XM を付記）
- 「5yr平均」を実データ年数で動的化（fcf_list_raw の len を使用）

### ✅ BUG-MATRIX4-1 (2026-06-10 完了): Matrix④ Y軸をFCF_History実績と統一
- Matrix④ Key_Metric_Y を fcf_history 最新年の実績マージンに修正
- （従来: FCF_Base/Revenue の比率 → 過大評価バイアスあり）

### ✅ BUG-NETDEBT-4 (2026-06-10 完了): レポートNet Debt内訳表示
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
- Stonks Silo yfinance ModuleNotFoundError修正
