# TANUKI VALUATION — 改善バックログ

最終更新: 2026-06-01（DISCOVER全面改修 8-1/8-2/8-5/8-6 完了）

---

## 優先度：高（次の改修サイクルで対応）

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
- 問題: 成長率が高い銘柄が機械的に高RICE評価になる
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

---

## 優先度：中（こなれてきたら対応）

### [SEGMENT-1] 主要銘柄のセグメント精緻設定
- 現状: 36銘柄がTTM実績自動適用（General 100%）
- 問題: セグメント別成長率の差異が反映されない
- 対象: 時価総額上位の未設定銘柄から順次
- 現状の自動化: TTM実績値を自動適用済み（デフォルト15%より改善）

### ✅ [GROWTH-1] 成長逓減モデルの精緻化（2026-05-31 完了）
- 旧: recommended_g = (TTM + 業界平均) / 2（固定50:50）
- 新: HypeCoreフェーズで重みを調整
  Phase1-2（黎明〜拡大）: TTM×65% ＋ 業界平均×35%（成長継続余地あり）
  Phase3 （陶酔期）     : TTM×50% ＋ 業界平均×50%（旧来バランス）
  Phase4 （剥落期）     : TTM×35% ＋ 業界平均×65%（正規化加速）
- 変更: growth_sanity.py（hype_phase追加）、pipeline.py（_load_hype_phase追加）
- テスト: 3件追加（計55件）

### [EPS-1] アナリスト予想EPS四半期値の取得
- 現状: Next_Quarter_EPSはN/A（Alpha Vantage無料枠の制約）
- 問題: 四半期サプライズ率が計算できない
- 改善: 有料API検討 or yfinance の quarterly_earnings 活用

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

---

## 優先度：低（アイデア段階）

### [MULTI-1] マルチバリュエーション表示
- 現状: DCF一本槍
- 改善: DCF / PEG / EV/Sales / RICE / HypeCoreを並列スコアカード表示
- GPT提案: 2026-05-30

### [RICE-2] CF_adj のMatrix判定への組み込み
- 現状: RICE_adj は表示のみ（Matrix判定はRICE生値を使用）
- 改善: RICE_adjをMatrix判定のY軸に使うオプションを追加

### [HYPE-1] HypeCoreフェーズ判定の精緻化
- 現状: MA200乖離・モメンタム中心
- 問題: NVDA・PLTRのような長期陶酔期銘柄で過剰警告
- 改善: 期間別フェーズ継続スコアを追加

### [REPORT-1] DCF感応度分析の表示
- 現状: WACC固定での3シナリオ（bear/base/bull）
- 改善: WACC変化時のIV感応度テーブルを追加
  例: WACC 9% / 10% / 11% × 成長率 base での IV変化

### [ARCH-1] ボトルネック企業プレミアム
- 現状: 未実装
- 内容: NVDA・ASML等の独占的ポジションを持つ企業への追加プレミアム
- 設計: 手動フラグ（bottleneck: true）+ α加算の形
- 記録日: 2026-04-12

### [EVAL-1] PEAD バックテスト
- 現状: 設計済み・未着手
- 内容: 決算サプライズ後の株価ドリフト戦略のバックテスト
- 制約: データコスト高のため延期中

### [EVAL-2] 期待値エンジン（仮称）
- 現状: 構想中
- 内容: 各サブポート戦略の期待値を統合管理するエンジン

### [EVAL-3] モート強度の相対スクリーニング軸化
- 現状: 構想中
- 内容: 競争優位性（モート）を定量化してスクリーニングに組み込む

---

## 完了済み（2026-05-30 本日対応）

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

### ✅ [FEAT-10] β再発防止の3施策（2026-05-31）
- beta_fetcher.py: 全銘柄βをyfinanceから自動取得・更新（cap2.5/floor0.3）
  Damodaran手動設定は保護、sourceフィールドで取得元を記録
- audit.py --check-beta: SEC監査にβ乖離チェック追加（0.5超で警告、1.0超で重大）
- Beta_Config_Update.yml: 月次自動更新ワークフロー（第1日曜JST8:00）
- CLAUDE_CODE_START.md: 新規銘柄登録Step2にbeta_fetcher.py追加

---

## 完了済み（2026-05-31 本日対応）

### ✅ [DESIGN-10] RICEの三分類見直し
- 詳細は上記 設計相談メモ 参照

### ✅ [BUG-2b] _calc_q: GAAP赤字年のSBC偽陽性Q値
- 発見: NI<0年にSBCで earnings>0 になるとQ計算に混入し異常Q値が発生
  例: NI=-469M, SBC=+608M → earnings=139M → Q=OCF/139M=13.43
- 影響: MRVL（Q=6.97→0.51）をはじめ11銘柄のRICE値が不正確だった
  NET/ZS/ZETA/SOUN: 誤ってRICE有りと判定（正しくはQ計算不可）
- 修正: `calculator/rice.py` _calc_q に `if ni < 0: continue` を追加
- テスト: 3件追加（計32件）

### ✅ [BUG-11] quarterly.py: NetIncomeフォールバック未設定
- 発見: AVGO/BKNG/AVAVのTTM系列でNI=None（Q計算不可・RICE誤分類）
  原因: quarterly.py が NetIncomeLoss のみ参照し ProfitLoss 等を見ていなかった
  AVGO: NetIncomeLossの四半期データが2019以前で途絶 → ProfitLossが必要
  BKNG: NetIncomeLoss自体が未申告 → NetIncomeLossAvailableToCommonStockholdersBasicが必要
  また _FALLBACK_MIN_FIELDS に NetIncome がなく q_count<4でもフォールバック未発動
- 修正: `common/sec_data/quarterly.py` に NetIncome フォールバック追加
  _FIELD_FALLBACKS["NetIncome"] = (ProfitLoss, NetIncomeLossAvailableToCommonStockholdersBasic)
  _FALLBACK_MIN_FIELDS に NetIncome を追加
- 結果: AVGO RICE=2.3(Matrix①正常), BKNG セクター除外(Matrix②正常), AVAV Q取得成功

### ✅ [FEAT-8] SECデータ品質監査の自動化
- `common/sec_data/audit.py` 作成
  NI/OCF/Revenue の全件・一部 None を検出、重大問題は Discord 通知
- `.github/workflows/SEC_Data_Audit.yml` 作成
  SEC_Data_Update 完了後に自動実行
- `CLAUDE_CODE_START.md` にパイプラインコード変更時の必須手順を追記

### ✅ [FEAT-9] Matrix③散布図: Q計算不可銘柄を表示
- 赤字銘柄（Q計算不可）が散布図に表示されていなかった
- stock.html の loadAndRenderMatrices を修正
  Q計算不可銘柄もMatrix③にルーティング（11銘柄が新規表示）
  Q異常値（Q>5）との視覚区別: 白ストローク付きドットで区別

---

## システム全体バックログ（TANUKI VALUATION以外）

### 【Stonks Silo】
- ✅ フロントエンド（HTML）実装済み（index.html 1298行）
- ✅ GitHub Actions 設定済み（Stonks_Silo_Update.yml）
- ✅ gross_margin: ASTS/JOBY のみ null（construction_phase として扱い）→ 他20銘柄は取得済み
- ✅ [DESIGN-11] unit_economics_score バックエンド補完（2026-06-03）: 全22銘柄に適用
- 現状: 22銘柄・results.json更新済み

### 【Moomoo API】
- [ ] β自動計算（SPY日次リターンからbeta_config.jsonを自動更新）
- [ ] advance/decline比率収集（MACRO PULSE向け）
- [ ] CANSLIM候補スクリーニングリスト（US株対象）
- [ ] 資金フロー（大口/小口）表示
- [ ] 決算ウォッチ用プレ/アフターマーケットデータ
- [ ] Momentum Burst 2023-2024バックテスト（データクォータ回復待ち・約2026-06-01）

### 【Market Pulse】
- ✅ [MP-1] AIレポート「出来高比」表現の修正（2026-06-02 完了）
  - 修正: S&P500/NASDAQ を個別表記に変換してGrokに渡すよう collect_and_send.py を修正
  - プロンプトに「指数を限定して記述・両者をまとめる表現禁止」制約を追加
- ✅ [MP-2] AIレポート品質改善・表記統一（2026-06-03 完了）
  - ①センチメントスコアを:.0f整数変換してGrok渡し・プロンプト小数禁止制約追加
  - ②VIX小数点2桁（16.05形式）統一・1桁禁止制約追加
  - ③Risk-Off Score 3軸配点（33/33/34pt）と全体要約への1行明記を義務化
  - ④VIX9D上昇+1pt未満は「急騰」禁止→「上昇加速(+Xpt)」、+3pt以上のみ「急騰」許可
  - ⑤VIX9D＜VIX30D維持しつつ9D上昇加速中は「移行期」文脈を必ず明記
  - ⑥NH=xxx, NL=yyy, NH-NL差=±zzzの3値表示に変更・差の拡縮分析を義務化
- [ ] 予測バックテスト表示
- [ ] 資産クラス資金フロービジュアライザーUI調整（実装済みだがUI調整待ち）
- ✅ [MP-6] AIレポートの表現・解釈バグ（2026-06-02 完了）
  - ①債券バッジ「リスクオン/オフ」→「債券売り/買い」に変更（collect_and_send.py + index.html）
  - ②信用収縮誤解釈防止：HYG・LQD同時下落→「金利上昇圧力/デュレーションリスク」限定。HYGのみ下落時のみ「信用スプレッド拡大」を許可するプロンプト制約を追加
  - ③乖離Zスコア符号定義明示：正=NASDAQ優位/負=S&P500優位をextended_dataとプロンプト両方に付記
- ✅ [MP-5] IMPLIED CUTS プロキシ注釈追加（2026-06-03 暫定対応完了）
  - 05_main.py（1172行）: Geminiプロンプトのレート渡し部分にDGS1プロキシ・term premium注記を追加
  - index.html（545行）: IMPLIED CUTS数値直下に「※プロキシ値・term premium含む」をvar(--mut)で表示
  - 根本解決（FF Futures/SOFR OIS）は引き続き要検討
- ✅ [MP-4] センチメントゲージへのバックテスト予測ミニゲージ統合（2026-06-03 完了）
  - バックテスト表を削除し「明日は？」「5日後は？」「20日後は？」のSVGミニゲージ3つに置換
  - 現在ゾーンの過去平均リターンから予測スコア計算（S&P500 +1%≈+2pt換算）
  - 点線=現在針・実線=予測針の2針表示
- ✅ [MP-3] 資金フローUI改善：タイルと推移テーブルの縦統合レイアウト（2026-06-03 完了）
  - grid-template-columns: 60px + 7列でタイルをヘッダー兼任にした統合グリッドに変更
  - 日付行を降順（最新上）でタイル直下に縦連結、色分け・軸ラベル・5日平均フッター維持
  - renderAssetFlow/renderAfHeatmapを1関数に統合、旧クラス（af-grid/af-hm-*）を削除

### 【Short report contrarian戦略】
- [ ] GitHub Actions化（現在は手動実行）
- 現状: バックテストv4完了。最優先サブポート戦略

### 【情報収集支援システム】
- [ ] カタリスト×割安検知（価格下落+空売り比率+カタリスト接近）
- [ ] テック/市場ブレークスルーニュース分類
- [ ] NEWS_API_KEY + Grok使用、yfinance/FMP連携

### 【完了済み（過去セッション）】
- ✅ MACRO PULSE 流動性モニター・NET LIQUIDITY実装
- ✅ MACRO PULSE Hollow Rally検知
- ✅ MACRO PULSE ステルス流動性（TGA/RRP）可視化
- ✅ αキャップ（上限1.0）実装
- ✅ RPO補正実装
- ✅ ネットキャッシュ補正を有利子負債のみに限定（実装済みを確認）
- ✅ Stonks Silo yfinance ModuleNotFoundError修正

---

## 設計相談メモ（2026-05-31）

### ✅ [DESIGN-1] ERP参考表示（2026-05-31 完了）
- 実装: ERP = ForwardEPS/Price - Rf（10年国債利回り）を HYPECORE セクションに追加
  ERP≥4%: 明確な割安感 / 2〜4%: 魅力あり / 0〜2%: 薄い / <0%: 割高感
  pipeline.py: _generate_report() 追加 + latest.json に erp/forward_earnings_yield 保存
- 残タスク: HypeCoreフェーズ判定への組み込みは効果確認後に検討（DESIGN-1b）

### [DESIGN-2] マクロによる銘柄フェーズ変化の認識
- 概要: マクロ環境（金利・流動性・センチメント）の変化が
  銘柄固有の品質変化なしにHypeCoreフェーズを変動させることを認める
- 設計: 2層構造
  Layer1（マクロ環境層）: Risk-On/Neutral/Risk-Off
  Layer2（銘柄固有層）: 現行HypeCore Phase1〜4
  最終フェーズ = 銘柄フェーズ × マクロ補正
- 連携: TANUKIの高成長期間・成長率への反映も将来検討
- 実装難易度: 高

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
- 実装難易度: 中

### [DESIGN-4] 期待込みの価値計算
- 概要: TANUKI（本源的価値）+ HypeCore α + マクロ補正
  = 期待込みの価値（フロアまたは最高値の目安）
- 連携: DESIGN-2・DESIGN-5と連動
- 実装難易度: 高

### [DESIGN-5] 期待の要素と構造の可視化
- 概要: 株価に織り込まれた「期待」を分解して可視化する
  TAM期待・シェア期待・利益率期待・時間軸期待・流動性期待
- 現状: 逆DCF（必要成長率）は実装済み → 拡張
- アイデア未固まり。設計を深める必要あり
- 実装難易度: 高

### [DESIGN-6] 経営者の実行力評価
- 概要: 目標の難易度 × ビート度合いで経営者を定量評価
- 指標候補:
  ガイダンス達成率（過去8四半期の実績/予想）
  売上成長の加速度
  ROICの改善トレンド
  SBC比率（希薄化の質）
- データ: EPS Analyzerで近似可能
- 実装難易度: 中

### ✅ [DESIGN-7] HYPEMIXの概念導入（2026-05-31 完了）
- 概要: 保有銘柄のHypeCoreフェーズを意図的に分散させる
  ポートフォリオ管理概念（Koichi氏の造語）
- 目的: 全銘柄が同時に期待剥落期に入ることを回避
  → 売り時と買い時が銘柄間でずれる自然なローテーション
  → キャッシュ比率の最適化・機会損失の回避
- 実装: Phase分布の可視化 + 目標HYPEMIXからの乖離スコア
  + リバランス提案
- 実装難易度: 低〜中（データは揃っている）

### [DESIGN-8] Discoverの改善
#### ✅ 8-1 推薦理由・スクリーニング条件の可視化（2026-05-31 完了）
- 概要: Grokへのプロンプトを改修し
  推薦理由・通過条件・リスクフラグを構造化JSONで返させる
- 実装難易度: 低

#### ✅ 8-2 ニュース表示の改善（2026-05-31 完了）
- 概要: ニュースなし銘柄を折りたたみ表示
  元ネタURL・出典・カタリスト種別バッジを追加
  GrokプロンプトにURL・published_at・relevanceを必須出力化
- 実装難易度: 低

#### ✅ 8-1 推薦理由・スクリーニング条件の可視化（2026-06-01 完了）
- 実装: conditions_met / risk_flags フィールドをGrokプロンプトに追加
  銘柄カードにアコーディオンパネル（▼ 詳細）で展開表示

#### ✅ 8-2 ニュース表示の改善（2026-06-01 完了）
- 実装: ニュースタイトルをURLリンク化（hover下線・新タブ）
  出典「via ○○」表示対応（sourceフィールドをGrok出力に追加）
  ニュースなし銘柄をゾーンレベルで折りたたみ（デフォルト非表示）

#### 8-3 ワンクリック銘柄登録〜更新
- 概要: Discover画面から「➕ 登録」ボタンで
  CIK取得→β/セグメント/Damodaran業種AI提案→承認→一括更新
  を一気通貫で実行
- 実装難易度: 高

#### 8-4 指数採用候補銘柄の発掘（設計見直し済み・実装保留）
- 概要: S&P MidCap 400 → S&P 500 昇格候補を定期サーチ
  GS・バンカメ等が発表する昇格候補レポートをGrok Web検索で収集
  機械的条件判定（yfinance）ではなくアナリストレポートベースの設計
- 実装方針: Grokのweb検索で「S&P 500 addition candidates」を定期検索
  週次でDiscover候補セクションに表示
- 実装難易度: 中
- 状態: 実装保留（着手時期未定）

#### ✅ 8-5 特大テーマの発掘・予測（2026-05-31/2026-06-01 完了）
- 概要: Grokが週次で「次の特大テーマ候補」を分析
  根拠・確度・時間軸を構造化して表示
  「Grokの見解」として参考表示にとどめる
- 実装難易度: 中

#### ✅ 8-6 銘柄への投資テーマ付与とテーマ別比較（2026-05-31 完了）
- 概要: 各銘柄にテーマタグを付与（手動 or AI提案）
  theme_config.jsonで管理・admin.htmlから編集
  テーマ別に登録銘柄を一覧・比較できる画面を追加
  HYPEMIX的な視点（フェーズ分散）も同時表示
- 実装難易度: 中

### ❌ [DESIGN-9] RIMモデル（廃止 2026-05-31）
- 実装後に廃止。理由: 66銘柄中3銘柄のみ信ぴょう性あり（BV/P>30%）
  自社株買い主体のテックポートフォリオでは会計上BVが圧縮されており
  NVDA BV/P=3%・AAPL BV/P=1.6% など大半で過小評価となり誤解を招く

### ✅ [DESIGN-10] RICEの三分類見直し（2026-05-31 完了）
- 概要: 現行の閾値2.0（高/低の二分類）を三分類に変更
  高効率: RICE ≥ 2.0（価値創造・現行維持）
  中効率: RICE 1.0〜2.0（資本コスト上回る・価値中立）
  低効率: RICE < 1.0（資本コスト未満・価値破壊水準）
- 理論的根拠: RICE=1.0がWACCとの均衡点
- 実装難易度: 低
- 実装: pipeline.py Matrix①のラベル三分類化 + テスト5件追加

### ✅ [DESIGN-11] Stonks Silo UEスコアバックエンド補完（2026-06-03 完了）
- analyzer.py に unit_economics_score/label/gross_margin_trend 計算を追加
- IOT/AVAV/ZETA=100pt（優秀）、BBAI/KULR/RDW=0pt（低調）で直感と一致
- ASTS/JOBY は gross_margin_note="construction_phase" で処理

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

### [DESIGN-14] 非線形的成長の検知スコア
- 概要: 構造変化×経営者実行力×業界変曲点の3要素で
  企業が非線形的成長を起こしそうかをスコア化
  非線形成長スコア = 構造変化(40%) × 実行力(30%) × 変曲点(30%)
- 各要素の計算:
  構造変化: RPO急増・粗利率急改善・Grok分析
  経営者実行力: ガイダンス達成率・ROIC改善・成長加速度
  業界変曲点: RPO/売上比率・競合動向・Grok分析
- TANUKIとの連携:
  スコア高→成長期間延長・逓減傾きを緩やかに設定
- 実装難易度: 高

---

## システム設計の基本思想（2026-05-31）

### On-a-journeyの本質的な目的

このシステムは「情報表示ツール」ではなく
「投資仮説の構築・検証を支援するツール」である。

長期投資家の本質的な行動サイクル：
  仮説を立てる
  → ポジションを取る（仮説への賭け）
  → 仮説を検証し続ける
  → 仮説が崩れたら撤退・正しければ保有継続

各システムの位置づけ：
  TANUKI VALUATION：
    「この企業は本質的にXXXドルの価値がある」
    という仮説を数値化するツール
  HypeCore：
    「今市場はどの程度の期待を織り込んでいるか」
    という仮説を検証するツール
  MACRO PULSE・Market Pulse：
    「仮説が成立する外部環境か」を確認するツール
  EPS Analyzer：
    「企業が仮説通りに実行しているか」を
    四半期ごとに検証するツール
  Discover：
    「次の有望な仮説候補を発掘する」ツール

この思想に基づき、全ての新機能開発において
「仮説の構築・検証にどう貢献するか」を
設計判断の基準とする。

---

## 追加課題（2026-05-31）

### ✅ [ACTION-6] Macro Extreme Fear戦略実行支援（2026-06-03 完了）
- docs/value-monitor/extreme-fear/index.html を新規作成
- F&Gゲージ・買い候補TOP10・過去EF実績・シミュレーター・メモ欄の5セクション
- スコアリング: BUY+40/WATCH+20/upside+30/funda+20/Phase≤2+10/Phase4-20pt

### ✅ [ACTION-2] 判定実績の自動追跡・検証ループ（2026-06-03 完了）
- score_history.json に判定スナップショットを日次追記
- score_verifier.py で 30/60/90日後リターンを自動計算
- index.html に判定別勝率テーブル＋直近20件を表示

### ✅ [ACTION-4] HYPEMIXポートフォリオ管理（2026-06-03 完了）
- フェーズ分布バー・目標乖離・リバランス提案・銘柄テーブルを TANUKI index.html に追加
- 現状: P4=52%（目標10%比+42pt超過）・P1=0%（目標20%比-20pt不足）を検出
- 実装: docs/value-monitor/tanuki_valuation/index.html に renderHypemix() 関数追加

### ✅ [ACTION-10] TANUKI SCOREの変化検知機能（2026-05-31 完了）
- 背景:
  現状のTANUKI SCOREは「状態の表示」であり
  「変化の検知」になっていないため使われていない
  変動があっても気づけない構造が問題
- 概要: 判定・フェーズ・乖離率の変化を検知して通知する
- 検知対象:
  判定変化（BUY→TRIM等）
  HypeCoreフェーズ転換（Phase2→Phase3等）
  乖離率の大きな変化（±10pt以上）
  撤退条件への接近
- 通知タイミング: 変化が発生した時のみ（毎日ではない）
- 通知先: Discord（既存WEBHOOK活用）
- 長期投資家向け: 毎日の変化ではなく
  「仮説の検証に影響する大きな変化」のみを通知
- 実装難易度: 低〜中

### ✅ [DISCOVER-1] 未発掘銘柄優先のプロンプト改善（2026-05-31 完了）
- 概要: explore_candidates() の Grok プロンプトを改修
- 変更内容:
  時価総額: 100億〜1000億ドル → $5億〜$100億（小〜中型）
  機関投資家: 「増加傾向」→ 保有率 < 40%（定量化）
  売上成長: 20%以上 → 30%以上
  追加: 主要指数未採用（S&P500・Russell1000・Nasdaq100等）
  追加: 推薦JSONに market_cap_b / revenue_growth_pct / institutional_ownership_pct を出力
- 実装: src/discover/collect.py の explore_candidates プロンプトのみ変更

### [DESIGN-15] 期待と理論価格の関係の整理（前提課題）
- 背景:
  HYPOTHESIS-2（KPI仮説・AI原案生成）や
  DESIGN-4（期待込みの価値）を実装する前に
  「期待と理論価格がどう関係するか」を
  システム内で整理・可視化する必要がある
- 概要:
  現在の理論株価（本源的価値）に対して
  市場価格との差分（期待プレミアム）が
  何によって構成されているかを可視化する
  逆DCF（必要成長率）は実装済み→これを起点に拡張
- 着手条件:
  DESIGN-4・5の設計議論が固まってから
- 実装難易度: 高
- 備考:
  この整理が完了して初めて
  HYPOTHESIS-2（KPI仮説・AI原案）の実装に着手する
