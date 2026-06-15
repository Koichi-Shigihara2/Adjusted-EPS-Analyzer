# BACKLOG 完了アーカイブ / アクティブな課題は BACKLOG.md を参照

---

## 2026-06-15

✅ [BUG-EPS-ZERO-1] V/XOM/VZ EPS=$0 修正・株式数フォールバック追加 ✅ 2026-06-15
- **V (Visa)**: WeightedAverageNumberOfDilutedSharesOutstanding が XBRL 10-Q に存在しないため EPS=$0 → yfinance fallback で 20四半期に拡充（ただし Class A 株数 ~1.66B = 稀薄化後 2.07B の過小）
- **XOM**: 同タグ 10-Q 未提供 → EarningsPerShareDiluted 逆算（NI/EPS）で 8四半期分を補完、Q4 は yfinance fallback
- **VZ**: quarterly.json は既に有効（18四半期 valid）、EPS pipeline 再実行で summary.json に反映
- **実装**: `extract_key_facts.py` に 3段フォールバック追加（①EPS逆算 ②Basic株数代用 ③yfinance）
- **required_tags に追加**: `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic`

✅ [BUG-IV-DISP-1] KULR/S/TDY IV表示不整合修正（tapering 未適用バグ） ✅ 2026-06-15
- **根本原因**: `core_calculator.py` の `_calc_ivps_with_wacc` が `dcf_type == "tapering"` 時でも 2段階 DCF に fallthrough → メイン IV がタペリング未適用、シナリオ BASE はタペリング適用で不整合
- **修正**: `_calc_ivps_with_wacc` に `elif dcf_type == "tapering"` ブランチを追加
- **修正**: `_res_rm` 計算ブロックにも tapering ブランチを追加（STEP11 表示の一貫性）
- **効果**: KULR IV $5.57 → $5.63（ScenBASE との差 $1.23 → $0.00）、S $29.50 → $23.65、TDY $517.61 → $596.10

✅ [DCF-DEFAULT-G-1] G=15%デフォルト問題修正（set_growth_override が segment 未設定銘柄に無効だったバグ） ✅ 2026-06-15
- **根本原因**: `segment_config.py` の `get_segment_growth` が `_GROWTH_OVERRIDES` を参照するのは segment_config.json に登録 かつ "General" 単一セグメント銘柄のみ → JNJ/MO/PEP/PM/WMT/VZ 等の未設定銘柄では override が無効
- **修正**: `get_segment_growth` 冒頭に `if ticker in _GROWTH_OVERRIDES: return override` を追加（全銘柄対象）
- **修正**: `pipeline.py` の auto-adjustment ブロックに `finally: clear_growth_override(ticker)` を追加
- **修正**: `pipeline.py` Section 4 表示: `Phase1成長率` を DCF 適用値（推奨成長率）に変更、元成長率を別行表示
- **JNJ**: IV $363.76 → $202.12（G=15%→1.47% で upside +51% → -16.1%）
- **VZ**: G=15%→0.9% で IV 大幅変動

## 2026-06-14

✅ [MP-DIV-UNIFY] 乖離計算ソースをCNN F&Gに統一（2026-06-14 完了）
- 原因: 乖離=Tech Pulse - feargreedchart.com(~57)で、画面表示のCNN F&G(~34)と不一致
- 修正: div_value = tech_pulse.score - fear_greed.score(CNN) → 乖離+15→+38に正常化
- _get_tp_signal のfg_score<30判定もCNNスコアに更新
- z-score履歴はdivergence.value優先参照(前コミット修正済み)のため次回実行からCNNベースで再計算

✅ [MP-DIV-ZSCORE-FIX] divergence z-score データソース不整合修正（2026-06-14 完了）
- 原因: `_load_div_history` が fear_greed.score（CNN, ~34）を使って履歴構築していたが、
  当日 div_value は fg_score_tech（feargreedchart.com, ~57）から計算 → ソース不一致
- 影響: 誤ったz-score（-0.11 ≒ 平均以下と誤判断 vs 正しくは +0.82 = 平均より上）
- 修正: 保存済み tech_pulse.divergence.value を優先使用 / 旧エントリは components.fg_score で再計算
- 次回 collect_and_send.py 実行からz-scoreが正確に算出される

✅ [MP-REGIME-LABEL] REGIME判定ソース明示（2026-06-14 完了）
- fed_context に regime_source 列を追加（Grok成功時: "FOMC声明分析（Grok）" / fallback時: "DGS1数値ベース"）
- index.html の REGIME セルにサブラベルとして判定ソースを表示
- 旧CSVは ai_reason から後付け推定して補完（3月:DGS1ベース / 4-6月:Grok）
- _fallback_regime の文言を "ZQ先物が…" → "DGS1ベースで…" に更新

✅ [MP-1YEFF-FIX] 1Y EXPECTED FF 表示値バグ修正（2026-06-14 完了）
- 原因: ラベルが "FRED T1YFF" と表示されていたが T1YFF は DGS1-FEDFUNDS スプレッドであり絶対金利ではない
- 修正: DGS1（1年国債利回り）を直接使用 → 表示値 3.62% → 3.85% / IMPLIED CUTS +0.02 → -0.90回
- ZQ=F term premium 補正ロジックを廃止しシンプル化
- サブラベルを「正値=利下げ織り込み / 負値=利上げ・高止まり織り込み」に更新
- 解釈: DGS1(3.85%) > FF(3.625%) = 市場は高金利継続を織り込み中（-0.90 = BALANCED判定）

✅ [MP-DISPLAY-FIX] Macro Pulse 表示バグ3件修正・データ取得ロジック改善（2026-06-14 完了）
- 修正1: NET LIQUIDITY / HY Spread の "++" 二重符号 → chgHtml の sign と fmt lambda が二重加算していた
- 修正2 (コードではなくデータ問題): refresh_monthly_indicators の obs_to_release_lag 導入
  - obs_date+60日の広すぎるウィンドウで既存スロットを飛ばし未来スロットに誤マッピングする問題を修正
  - NFP 2026-06-05 (5月雇用統計) / Building Permits 2026-05-19 を正常取得
  - Recent Signals の最新表示が 5/15 → 6/5 に改善
  - Michigan CS / Mich Inf 1Y は FRED データが April 止まり（FRED 側ラグ、許容）
- 修正3: AI Weekly Commentary ヘッダー "Gemini 2.5 Flash" → "GROK-3-MINI"

✅ [MP-HISTORY-FIX] Market Pulse 過去データ異常値修正・バリデーション追加（2026-06-14 完了）
- 原因: VIX9D列追加時のCSVヘッダズレでsentiment_scoreに誤値（-2.66〜1.41）が42件混入
- 修正: market_data.json 42件再計算・91件→58件に重複集約
- 再発防止: collect_and_send.py に sentiment_score の 0〜100 範囲チェック追加

✅ [MP-PRED-FIX] センチメント予測リターン異常値修正（2026-06-14 完了）
- 原因: 同一列ズレバグによりS&P500.valueに0.08等の誤値 → getAvgRetが+9億%を出力
- 修正: 5/21-6/7の17エントリ全indicators再構築・index.htmlに防衛チェック追加
- Tech Pulse 5/21-6/5欠落はCSV未保存のため復元不可（許容）

---

## 2026-06-13 完了

### ✅ STALE-CHECK-1 フォローアップ (2026-06-13 完了): 11銘柄ステールデータ更新
- **対象**: FICO/ZETA/BBAI/CELH/COHR/CRWV/RCAT/CPRT/ZS/HQY/RBRK（4〜5月決算後未更新）
- **手順**: update.py → pipeline.py → audit.py → consistency_check
- **結果**: 全11銘柄 SEC 再取得完了（11/11）、pipeline PASS=9 WARN=2 FAIL=0 ERROR=0
  - WARN=2 は FICO/CPRT の formula_verification（既存）
  - WARN-8（ステール警告）: 全消去確認済み
- **IV 更新後**: FICO=$928/ZETA=$30.4/BBAI=$1.79/CELH=$21.2/COHR=$39.1/CRWV=$159.8/RCAT=$3.49/CPRT=$49.3/ZS=$141.9/HQY=$105.8/RBRK=$135.7
- **audit.py**: 正常77銘柄・警告2件（CART/JOBY 既存 Revenue None）NG=0
- **consistency_check**: NG=0 全銘柄整合（残警告: ELF WARN-10、LMT/VRT WARN-9 は既存）
- **pytest**: 108件全パス

### ✅ EPS-PER-TTM-1 (2026-06-13 完了): 調整後PERをGAAPと同一TTM期に統一
- **根本課題**: `_calc_adjusted_per` が `annual.json years[0].adjusted_eps`（年次FY）を分母に使うため、GAAP PER（yfinance trailingPE = TTM）と期間不一致。成長株で ADJ>GAAP 逆転（NVDA: 48.3x vs 31.4x）
- **修正**: `core_calculator._calc_adjusted_per` を `quarterly.json` 直近4Q `adjusted_eps` 合計（TTM）に変更。4Q未満は None（年次フォールバック禁止）
- **文言**: report.txt 注記「年次EPSベース」→「TTM調整後EPS: $x.xxxx」、Definition に「same trailing 12M period」明記
- **検証**: NVDA 48.3x → 30.3x（Delta -1.1x）、46銘柄 ADJ/GAAP 非対称を解消
- pytest: 105件全パス / 全78銘柄再生成 FAIL=0

### ✅ ANNUAL-FY-1 (2026-06-13 完了): aggregate_annualを会計年度ベース集計に修正（IV影響あり）
- **根本課題**: `aggregate_annual`（pipeline.py）が `filing_date[:4]` でグループ化するため、非12月FY企業で FY跨ぎ混合が発生。例: NVDA annual.json year=2025 = FY2025Q4+FY2026Q1-Q3（混合）→ 誤FCF推定値を経由してIVに影響
- **修正**: `fiscal_year` フィールドベースに変更。フィールド未設定の場合は `filing_date[:4]` にフォールバック
- **PARSER-1との関係**: 独立した修正。parser.py は期末日年キー、aggregate_annual は会計年度キーで別レイヤー
- **影響**: 20銘柄の annual.json 更新 → `estimate_fcf_from_eps` 経由でIVに波及
  - 大型: NVDA +18% ($201→$238) / MSFT -12% ($621→$546) / AVAV +93% ($54→$105)
  - IOT: applied=False→True（FY2026 adj_ni +$265.8M、本物の黒字化）
  - COHR/LITE/RBRK/S: applied=False のまま（IV変化なし）
- **スポットチェック**: NVDA FY2026=$5.12/AAPL FY2025=$8.11/MSFT FY2025=$15.44（10-K通年と一致）
- **consistency_check追加**: TestAnnualFYConsistency（3件）- 年跨ぎ混合の恒久ガード
- **ARCH-DATA-1注記**: 年度判定が parser.py / extract_key_facts.py / aggregate_annual の3箇所に分散。共通関数化は次の前倒し対象
- pytest: 108件全パス / 全78銘柄再生成 FAIL=0

### ✅ PARSER-1 (2026-06-13 完了): 年次キーを fy→end_date年 に変更
- **根本課題**: FCX の FY2025 10-K で `fy=2025, end='2024-12-31'` エントリが混入し、`annual_2024.json` が生成されない年度ズレ
- **修正1**: `_extract_values` の年次辞書キーを `fy` → `int(end_date[:4])` に変更（end_year ベース）
- **副作用**: INTU（FY end=7月31日）で FY2020 10-K 内の Q1 比較値（`fy=2020, end='2019-10-31', val=$1.16B`）が `end_year=2019` として通年値（$6.78B）を上書きする regression が発生
- **修正2**: `annual_exact_match` 辞書を追加し、`fy==end_year`（exact match）が存在する年度は non-exact エントリによる上書きを禁止する一般解で解決
- **波及検証**: 差分 150件はすべて non-December 決算企業（AAPL/MSFT/NVDA/CRM/ELF/HQY/COHR 等）の FY2019 以前の revenue/NI が正しい FYE 値へ修正されたもので、潜在バグ群の一括解消
- **IV への影響**: 直近5年 FCF 系列は不変のため IV/FCF_Base/CAGR への波及ゼロ
- **検証**: 全 78 銘柄再パース成功（FAIL=0）、exact matchなし競合 234件の tie-break（最新 end_date 優先）は意図通り動作確認済み

### ✅ REPORT-6 (2026-06-13 完了): DCF透明性強化
- `pipeline.py` の report.txt [3]TANUKI VALUATIONに`DCF_FCF_PV`/`DCF_TV_PV`を追加（全銘柄）
- FCF外れ値除外銘柄のみ`DCF_FCF_Base_Detail`/`DCF_FCF_Base_Excluded`を追加出力
- 3段階DCF(three_stage)は`pv_phase1+pv_phase2`、2段階は`pv_high_growth`でFCF現在価値を算出
- pytest: 122件全パス / 全78銘柄再生成: FAIL=0 / NG=0

### ✅ SEGMENT-1 後半バッチ完了 (2026-06-13 完了): LLY/LMT/MRVL/AMAT/VRT/COHR/LITE/CSGP/BSY/ALAB/ELF/AVAV（12銘柄）
- **単一セグメント確認・修正不要（LLY型）**: LLY / MRVL / BSY / ALAB / ELF（5銘柄）
  - MRVL補足: 5エンドマーケット = disaggregated revenue（ASC 606）≠ ASC 280 formal segment。FY2026から2カテゴリ報告へ変更予定だが従来通り単一
- **複数セグメント設定（LMT型）・IV変化一覧**:

| Ticker | セグメント数 | 設定内容 | IV before | IV after | 変化率 |
|--------|------------|---------|-----------|----------|--------|
| LMT | 4 | Aeronautics(40%/5%)/MFC(18%/10%)/RMS(24%/6%)/Space(18%/3%) | $309 | $347 | +12.3% |
| AMAT | 3 | Semiconductor_Systems(74%/8%)/Applied_Global_Services(23%/6%)/Display(3%/2%) | $274 | $253 | -7.5% |
| VRT | 3 | Americas(56%/15%)/Asia_Pacific(22%/13%)/EMEA(22%/13%) | $129 | $101 | -21.0% |
| COHR | 3 | Networking(59%/20%)/Lasers(25%/10%)/Materials(16%/6%) FY2025 | $90 | $39 | -56.5% |
| LITE | 2 | Cloud_Networking(86%/20%)/Industrial_Tech(14%/4%) FY2025 | $60 | $27 | -56.0% |
| CSGP | 2 | North_America(95%/10%)/International(5%/20%) FY2025 | $13.6 | $11.78 | -13.6% |
| AVAV | 3 | Uncrewed_Systems(40%/12%)/Loitering_Munitions(50%/20%)/MacCready_Works(10%/15%) | $135.53 | $94.23 | -30.5% |

- **growth_floor bypass**: segment_configured=True の場合 recommended_g サニティ回避（weighted_growth 直接採用）
- **COHR/LITE の大幅低下**: FCF base が超小型（$31.8M/$62.1M）のためΔgrowth が IV に直接増幅
- **weighted_growth 計算**: sum(weight_i × g_i)。AVAV weighted_g = 16.3%（before recommended_g 25.64%）
- CSGP 補足: net_debt/shares_used=None は全銘柄共通の latest.json 仕様（report.txt の値は正常）
- pytest: 108件全パス / 全銘柄再生成 FAIL=0

### ✅ SEGMENT-1 VST/FCX/SCCO/CEG/KO (2026-06-13 完了): filing準拠セグメント修正
- VST: Texas_ERCOT/East_Nuclear/Retail/West（地理別、wg 7.2%→7.85%、IV $31.36→$33.69）
- FCX: Indonesia/North_America/South_America（Gold独立セグ削除、wg 8.3%→6.4%、IV $3.95→$3.34）
- SCCO: Peruvian_Operations/Mexican_Operations（OtherMetals削除、wg 8.6%→8.45%、IV $17.48→$17.36）
- CEG: Mid_Atlantic/Midwest/ERCOT/New_York/Other_Retail（Calpine統合後、wg 10.3%→9.65%、IV $52.48→$49.54）
- KO: North_America_NAOU/International/Global_Ventures（wg 5.0%→4.7%、IV $46.39→$45.71）
- 残タスク: LLY/LMT/MRVL/AMAT/VRT/COHR/LITE/CSGP/BSY/ALAB/ELF/AVAV（12銘柄）

### ✅ BUG-NETDEBT-6 (2026-06-13 完了): 同一時点原則による Net Debt 計算修正
> ⚠️ ID注記: 本項は当初 BUG-NETDEBT-4 と命名していたが、2026-06-10 完了分に
> 同一 ID（レポート Net Debt 内訳表示）が既存のため BUG-NETDEBT-6 に改番（NETDEBT-5まで使用済み）。
- **原因1**: BUG-NETDEBT-1でCashは最新quarterly上書きされるが、Total_Debtは年次のまま（時点混在）。
  さらに表示値とequity bridge投入値が別物（表示$8.10B vs engine net_cash -$5.26B）という二重の不整合
- **原因2**: CEG等は10-QでLTDebtをLongTermDebtNoncurrentタグで報告するが、quarterly.pyがLongTermDebt(annual tag)のみ参照してNone扱い
- **修正**: quarterly.py に `LongTermDebtNoncurrent` を `_FIELD_FALLBACKS["LTDebt"]` に追加
- **修正**: reader.py + pipeline.py に同一時点原則ブロック実装（quarterly に Cash+LTDebt が揃う場合に全BS項目を同一filingから参照）
- **修正**: pipeline.py に BUG-NETDEBT-2 補完復活（annual lt_debt=0 かつ quarterly LTDebt未取得の場合にnormalized LTDebtで補完）
- **条件設計**: `_q_lt is not None` が必須ゲート。`_q_lt=None`（パース失敗）時は cash-only → BUG-NETDEBT-2 でnormalized補完
- **影響銘柄 (Net_Debt が実質変化)**:
  - CEG: Net_Debt $+8.10B → **+$21.30B**（Calpine買収負債$16.99B Q1 2026反映）、IV $97.39 → **$52.48**
    （乖離 -61% → -79%。ΔIV -$44.91/sh = 100% Net Debt起因: Cash -$7.96 / LTDebt -$27.29 / STDebt -$9.67、FCFベース寄与ゼロ）
  - KO: Net_Debt **-$9.08B → +$27.42B**（annual lt=None → normalized $36.5B補完）
  - ELF: Net_Debt -$0.20B → **+$0.65B**（term loan $0.85B）
  - SOFI: Net_Debt -$3.40B → **+$2.08B**（normalized LTDebt $5.49B、2022データ※）
  - ZS: Net_Debt -$1.20B → **-$0.05B**（convertible notes $1.15B）
  - JOBY: Net_Debt -$2.47B → **-$1.77B**（Toyota financing $0.70B）
  - ※SOFI: 2022-12-31以降の10-Qに標準LTDebtタグなし（銀行移行後の報告変更）。IV計算パスと表示パスは一致。
- **display改善追加**: DCF_FCF_Base行、Net_Debt_Period行、dilution乖離フラグ、beta staleness警告（90日超）、株式数表示修正
- 回帰テスト: 100件パス（変更なし）

### ✅ REPORT-6拡張: DCF再現性の完全確立 (2026-06-13 完了)
- 背景: VST時点のREPORT-6（DCF_FCF_PV/TV_PV追加）では、α倍率・equity bridge・採用株数が
  非表示のため外部AIが「IV再現不能」を全メガキャップで誤指摘（MSFT/NVDA/APP/PLTR/TSLA等）。
  PV2項の和だけではα乗算後段が見えず、α≒0の小型株でのみ偶然近似できていた
- 修正: report.txt [3]DCFブロックを「上から足すと必ずIVになる」構造に再構成
  DCF_FCF_PV → DCF_TV_PV → DCF_v0 → Alpha_Premium → DCF_v0_x_alpha
  → RPO_PV → Growth_Option_PV → Equity_Value(−Net_Debt) → Shares_Used(source明記) → Intrinsic_Value
- 優先株がある銘柄（CELH等）はequity bridgeに控除行を追加表示
- 検証: test_iv_formula.py 5件（MSFT/NVDA/CELH/PLTR/TSLA、誤差<$0.01）。IV値自体は不変（表示追加のみ）
- 効果: 外部レビュー最頻出指摘「IV再現不能」を構造的に解消

### ✅ MATRIX-1 (2026-06-13 完了): ROE_avg窓長のreport.txt明示
- 採用案: (b)動的採用+report表示。Matrix象限ロジック・ROE計算自体は不変（低リスク）
- report.txt [2] Key_Metric_Y を `ROE_avg (Nyr, equity>0全年) = XX%` に変更
- 窓長Nyrは銘柄ごとのequity>0年数を動的算出して表示（VST=7yr/CEG=4yr等）
- 効果: 外部AIが「なぜ固定窓長でないか」を誤検出しなくなる（再現性の可視化）
- 補足設計論点（未対応・低優先）: VST ROE_avg(7yr)=10.5% vs 直近3yr≈31% のように
  窓長次第で象限が動く件は表示で可視化済み。固定窓長化(a)は全銘柄IV波及のため見送り

### ✅ STALE-CHECK-1 (2026-06-13 完了): 決算後未更新データの検出
- report_consistency_check に決算日経過後の未更新検出を追加
- 検出11件: FICO/ZETA/BBAI/CELH/COHR/CRWV/RCAT/CPRT/ZS/HQY/RBRK（4〜5月決算後未更新）
- 次回更新サイクルでSEC再取得を実施予定（残タスク）

### ✅ 独自仕様の注記追加 (2026-06-13 完了): 外部AI誤検出の恒久防止
- RICE定義式を実装に一致: `(G × VC_Factor × Q × CF) / WACC`（VC_Factorが式本体から欠落していた注記バグ）
- FCF_Conversion注記: Adj_NI×rate であり OCF→FCF変換率とは別物。高FCFマージン企業で実績FCFを
  下回るのは正常化前提による保守設計と明記
- IV/割引率注記: 高β銘柄でWACC比IVが高めに出るのは市場リスクを意図的に除外した本源価値の設計。
  市場リスク調整後はWACC_CAPM_ReferenceでのIVを併用
- DCF_Reliability=LOW判定（Policy A明文化）: LOW時はBUY/TRIM/HOLD/WATCH→WATCH、SELL/PASS維持。
  IVは参考値、乖離率は表示するが分類には使用しない

## 2026-06-12 完了

### ✅ CHECK-13 / WARN-12修正 (2026-06-12 完了): RICE負値ラベル回帰検知 + 偽陽性除去
- `report_consistency_check.py` に CHECK-13 追加（RICE<0 時 Matrix Label 確認）
- CHECK-12 の `_latest` 変数名バグ修正（正: `latest`）→ WARN-12 が正常検知されるように
- WARN-12 の false positive 除去: quarterly_STI ≈ annual_STI のとき誤検出しないよう `_sti_already_qtr` 条件追加
- 修正後: NG-13 発生 5 件 → 影響 5 銘柄を再生成 → NG=0 確認
- テスト: `TestRiceNegativeLabel` 3 件追加（total: 100 件パス）

### ✅ RICE-3 (2026-06-12 完了): 負 RICE 値の閾値定義明記
- OCF 赤字時に RICE が負値になるが「低効率」と誤表示されていた問題を修正
- `pipeline.py` の rice_efficiency 判定に `< 0 → "N/A (OCF赤字)"` ブランチを追加（4分類化）
- Matrix Label・RICE_Threshold・Interpretation 定義文すべてに `<0=undefined (OCF negative)` を追記
- IONQ 確認: RICE=-0.552 で Label が "N/A (OCF赤字)" に正しく表示されることを確認

### ✅ BUG-NETDEBT-5 (2026-06-12 完了): ST_Invest期ズレ修正(年次→最新四半期)
- **原因**: BUG-NETDEBT-1でCashは最新四半期bs値に上書きされるが、ST_Investはannual年次のまま
  normalized JSONにShortTermInvestmentsフィールドがなく自動更新経路がなかった
- **修正**: pipeline.py の financial_health 計算ブロックに BUG-NETDEBT-5 ブロック追加
  最新 `quarterly_*.json` の `bs.short_term_investments` で上書き（値が0なら年次にフォールバック）
- **影響26銘柄**: IONQ(-$0.18B)、META(-$12.04B)、MSFT(+$18.16B)、GOOGL(+$7.36B)、
  AAPL(-$4.17B)、AMD(-$1.75B)、AMZN(-$5.05B)、JOBY(-$0.42B) 等
  IONQ: Net_Debt -$1.85B → **-$2.03B**（$1,361M→$1,540M、Q1 2026 から）
- **CHECK-12追加**: `report_consistency_check.py` にCash-STI期整合チェック（WARN-12）
  Cash≈四半期値 かつ STI≈年次値 なら期ズレ未修正として警告。26銘柄修正後NG=0確認済み
- 回帰テスト: Section 23 (3件追加、計97件合格)

### ✅ BUG-REV-SPAC-1 / A-2-TTM (2026-06-12 完了): IONQレビュー指摘: FCF_Margin単年異常 / TTM二義性
- **BUG-REV-SPAC-1 (A-1)**: IONQの2022年10-K `Revenues` タグが$1,235M(SPAC調達金)を誤タグ
  正規営業収益 `RevenueFromContractWithCustomerExcludingAssessedTax`=$11.1M と重複
  `merge_all_tags=True` + 同一end_date で先頭タグ `Revenues` が勝ち、FCF_Margin 2022=-4.4% に (正常値は-485%)
  修正: `TICKER_RESTRICTIONS["IONQ"]["revenue_concept"]` で単一タグ固定
  横断スキャン: 全79銘柄に同型バグなし (ASTS/JOBY/RCATは正常高成長)
- **A-2-TTM**: [3]`TTM_Revenue_Growth=201.9%` (実TTM YoY) と
  [4]`TTM15.0%のため中央値モデル適用` (`_trigger_max`=max(phase1_g, CAGR)) が同一`TTM`表記
  修正: [3]→`TTM_YoY_Growth`, [4]中央値→`CAGR_max=XX%`, [4]逓減→`CAGR_max=`/`G入力値=`
  逓減モデルの start_g もCAGR最大値を優先するよう修正 (IONQ: recommended_g 12.5%→55%)
- **CHECK-11追加**: `report_consistency_check.py` に Revenue孤立年チェック(前後両年<5%の孤立異常値)
- 回帰テスト: Section 22 (5件追加、計94件合格)

## 2026-06-11 完了

### ✅ BUG-NETDEBT-2 (2026-06-11 完了): LongTermDebt優先順位修正による二重計上防止
- 原因: `XBRL_MAPPING["long_term_debt"]` の先頭が `LongTermDebt`（current+non-current合計）だった
  `short_term_debt` で `LongTermDebtCurrent` を別途加算するため、current分が二重計上されていた
- 修正: `parser.py` の `long_term_debt` マッピングを `LongTermDebtNoncurrent` 優先に変更
- 影響: 48銘柄の annual.json を再生成、全銘柄の pipeline を再実行
- DOCN 例: Total_Debt $1.62B → $1.30B、Net_Debt $0.88B → $0.55B
- 回帰テスト: `tests/test_pipeline_logic.py` Section 21 (3件追加、計89件合格)

### ✅ SEC-REV-FINTECH-1 (2026-06-11 完了): 金融系銘柄 annual revenue 過小評価の修正
- 原因: `MERGE_ALL_TAGS` 動作で狭義 `RevenueFromContractWithCustomer`($0.62B) が
  広義 `RevenuesNetOfInterestExpense`($3.61B) より先に見つかりrevenuが過小計上
- 修正: `parser.py` に `TICKER_RESTRICTIONS["revenue_concept"]` オーバーライドを実装
  指定タグのみ使用し merge_all=False でシングルタグ取得
- SOFI: FY2024 annual revenue $0.62B → $3.61B 是正
- 回帰テスト: `tests/test_pipeline_logic.py` Section 20 (3件追加)

### ✅ 登録パイプラインWARN清掃 (2026-06-11 完了): WARN 23→10 件
- CSGP/ZS: HypeCore実行によりデータ整備
- BKNG/FCX: `eps=false` 設定（XBRL quarterly NetIncomeLoss データ欠如）
- ASML: IFRS外国企業のため cik_lookup.csv から削除
- 孤立エントリ削除: CRWD/FIG/MDB/PUBM/WEAV (tanuki=false なのにエントリ残存) + REKR/SENS/VUZI
- `registration_validator.py` に `eps_disabled` 除外ロジック追加
- `CLAUDE_CODE_START.md` に EPS analyzer Step 5b / IFRS注意事項 を補強

### ✅ BUG-RPO-1 whitelist構造化 (2026-06-11 完了): RPO適用をwhitelist+比率条件に構造化
- _get_rpo_application_rate に via_whitelist フラグを追加（whitelist登録銘柄は比率チェック免除）
- adjust_rpo に RPO/Revenue < 0.3 の比率ゲートを実装（whitelist以外全員適用）
- exclusion_reason を rpo_adjustment に格納、report.txt の RPO_PV 行に除外理由を表示
- V(ratio=0.11)・BSY(ratio=0.18)が除外、GOOGL/MSCI は維持

### ✅ DCF_Reliability=LOW SCORE丸め (2026-06-11 完了): LOWのとき WATCH に統一
- _compute_tanuki_score にて fcf_floor_applied > 0 の場合 SELL/PASS 以外を WATCH に丸める
- score_comment に「DCF信頼性LOW(実績FCF赤字)のためupside依存判定を抑制→WATCH」を付記
- CRWV: HOLD → WATCH に変更（期待通り）

### ✅ BUG-ROE-NI-1 (2026-06-11 完了): ROE集計でnet_incomeがNoneの年を除外していた問題
- 原因: SEC XBRL旧フォーマット(2015-2019頃)は net_income=None だがeps_diluted×sharesから代替推計可能
- 修正: get_roe_avg_detail() に `eps_diluted × shares_diluted` フォールバックを追加（NI=None時）
- 結果: CAKE 5yr平均ROE 5.2%→13.4% (有効年数 5→10年、COVID赤字年の影響が薄まる)
- 汎用修正: 同様の旧SEC形式を持つ全銘柄に自動適用

### ✅ BUG-FCF-CAGR-SPAN-1 (2026-06-11 完了): FCF CAGR計算の固定3年指数バグ
- 原因: `(fcf_new/fcf_old)**(1/3)` の固定指数が年次データ欠落時に誤ったCAGRを算出
  CAKE: annual_2022.json 欠落 → 実際は4年スパンなのに3年として計算
- 修正: `span = yr_new - yr_old` で実際の年数差を算出し `(1/span)` を使用
- ラベル変更: `FCF_CAGR_3yr` → `FCF_CAGR_{span}yr`（スパン明示）
- 結果: CAKE FCF_CAGR_4yr: +1.5%（旧: FCF_CAGR_3yr: +2.0%）

### ✅ BUG-SCAN-FULLSCAN-1 (2026-06-11 完了): 全79銘柄スキャンによるバグ3件の発見と修正
- **Fix1 (core_calculator.py)**: `scenario_valuations` を `growth_result.source == "segment_weighted"` ゲートなしで全銘柄に計算
  - 旧バグ: segment未設定の15銘柄でBEAR/BULLが $0.00 / Growth=0.0% になっていた
  - 修正: `if growth_result.source == "segment_weighted":` ガードを削除し無条件計算に変更
- **Fix2 (pipeline.py _load_extra_data)**: segment_config.json 未登録銘柄に `segment_configured=False` をセット
  - 旧バグ: 未登録銘柄では `extra.get("segment_configured", True)` が True を返し `_is_seg_unconfigured=False` になっていた
  - 修正: `not segs` のとき `result["segment_configured"] = False` を追加
- **Fix3 (pipeline.py _generate_report)**: Matrix② 定義文の ROE 年数を `roe_years_used` から動的生成
  - 旧バグ: 固定文字列 `"ROE_10yr_avg"` を使用、6年・8年集計の銘柄で不一致
  - 修正: `_roe_n_def = comps.get("roe_years_used") or 10` で動的に年数を取得
- スキャナー: `common/sec_data/phase1_scan.py` を新規作成（10カテゴリ 全銘柄検査）
- 再実行: 影響15銘柄 + Matrix②5銘柄 を再生成 → NG=0 / WARN=12(期限切れ決算日11件+軽微逆転1件)
- 回帰テスト: `tests/test_pipeline_logic.py` にFix1/Fix2/Fix3の回帰防止テスト6件を追加 (計83件合格)

### ✅ CONFIG-CAKE-SEG-1 (2026-06-11 完了): CAKEセグメント設定の名称・注記修正
- 修正: segment_config.json CAKE エントリー更新
  "Restaurant Sales" → "Restaurant Operations"（North Italia/FRC brands含む）
  "Bakery Operations" → "Bakery & Other"（外部卸売バクリー配送のみ）
- fiscal_year: FY2025 に更新

### ✅ FEAT-CHECK9-1 (2026-06-11 完了): consistency_check CHECK-9 セグメント設定陳腐化検知
- report_consistency_check.py に CHECK-9 追加（WARN）
- segment_config の fiscal_year が Generated年から2年以上前の場合 WARN-9 を発行
- _raw_lines を _parse_report() 結果に追加して Generated 行の年を取得
- 現状: FY2025設定(2026年生成)は1年差のためWARN未発動（設計通り）

---

## 2026-06-10 完了

### ✅ BUG-FCFBASE-2 (2026-06-10 完了): FCF赤字銘柄DCFガード
- DCF_Reliability: HIGH/LOW を report.txt に追加（revenue_floor適用時 = LOW）
- FCF_Base 表示を調整前後併記（実績avg: $-XX.XM を付記）
- 「5yr平均」を実データ年数で動的化（fcf_list_raw の len を使用）

### ✅ BUG-MATRIX4-1 (2026-06-10 完了): Matrix④ Y軸をFCF_History実績と統一
- Matrix④ Key_Metric_Y を fcf_history 最新年の実績マージンに修正
- （従来: FCF_Base/Revenue の比率 → 過大評価バイアスあり）
- **追補 (2026-06-11)**: fcf_history[-1]がNone(上場直後・SEC未取得年末尾)の銘柄で
  revenue_floor正値にフォールバックするバグを修正（RCATで検出）
  → reversed()で最新非Noneエントリーを採用 / 全None+floor適用時はN/A表示

### ✅ BUG-NETDEBT-4 (2026-06-10 完了): レポートNet Debt内訳表示
> 注記: これは表示のみの修正。同一時点原則によるNet Debt計算修正（当初BUG-NETDEBT-4と
> 重複命名されていた2026-06-13分）は BUG-NETDEBT-6 に改番済み（2026-06-13セクション参照）。
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

---

## 2026-06-14 完了

✅ [BUG-EPS-UNIT-1] LOAR/ONDS EPS per-share 株式数単位バグ修正 + CHECK-14/15/16追加 ✅ 2026-06-14
- **症状**: LOAR adj_eps=$151/$396/$320（実株価$68）、ONDS Q1 2026 adj_eps=$119.24
- **根本原因**: SEC XBRL の WeightedAverageNumberOfDilutedSharesOutstanding が
  千株単位で報告されているが unit="shares" と誤記されているケース
  LOAR: 全四半期平均95,913 << 1M → 全期間千株単位と判断
  ONDS Q1 2026: 461,706 << 直近8Q中央値×1% → 孤立四半期の千株単位
- **修正**: `extract_key_facts.py` に 2段階サニティチェックを追加
  Stage①: 全期間平均 < 1M → 全四半期 ×1000（LOAR適用）
  Stage②: 直近8Q中央値の1%未満の孤立四半期 → その四半期 ×1000（ONDS適用）
- **CHECK追加**: `report_consistency_check.py` に CHECK-14/15/16 追加
  CHECK-14: adj_eps > 現在株価×50% → NG（単位ミス異常値検知）
  CHECK-15: adj_eps > 現在株価 → NG（さらに深刻な単位ミス）
  CHECK-16: 直近4Q未満のデータ → WARN（TTM不完全）
- **結果**: LOAR FY2025 GAAP_EPS $752.20→$0.7522、Adj_EPS→$1.1061 ✓
  ONDS Q1 2026 株式数461,706→461,706,000、adj_eps $119.24→$0.1192 ✓
  consistency_check: NG=0 確認済み

✅ [BUG-INTU-GROWTH-1] INTU Section 4 Layer 1 成長率表示バグ修正 ✅ 2026-06-14
- **症状**: INTU の [4. 成長率根拠] で "中央値モデル" が 19.7% を参照し
  DCF適用値 12.8% との関係が不明瞭
- **根本原因**: Layer 1（segment_configured=True）銘柄でも Layer 2 と同じ
  表示フローを使っており、DCF G（セグメント加重平均直接）とラベルが乖離
- **修正**: `pipeline.py` Section 4 を `_seg_configured` で分岐
  Layer 1: "セグメント加重モデル（Layer 1）" と表示、recommended_g を "Layer 2 参考値・DCF未適用" と明記
  Layer 2: 従来通り "中央値モデル/逓減モデル"
- **結果**: INTU 報告が "DCF適用値: 12.8%（セグメント加重平均）/ 推奨成長率: 19.7%（Layer 2 参考値）" と整合 ✓

✅ [BUG-INTU-NETDEBT-1] INTU 短期投資 Net Debt 欠落調査 → 誤検知 ✅ 2026-06-14
- **疑惑**: INTU の短期投資がNet Debt計算から漏れている可能性
- **調査結果**: INTU の XBRL には ShortTermInvestments タグが存在しない
  INTUの財務構造上 short_term_investments=0 は正しい値。修正不要。

## [BUG-FOUR-1] FOUR（Shift4 Payments）EPS・株式数・希薄化異常値 ✅ 2026-06-14

### 症状
- Latest_Adjusted_EPS: $49.93（正常値: ~$0.40）
- TTM調整後EPS: $119.70（正常値: ~$1.20）
- Dilution_3yr_Annual: -29.86%/yr（誤）
- ⚠️ 株式数乖離警告: yf=99M vs SEC=1M (+7332.8%)

### 根本原因
FOUR の UP-C LLC 構造変更（2021-2022）後、XBRL の
WeightedAverageNumberOfDilutedSharesOutstanding が
Class A 株式のみを報告（~1.33M）し、実際の経済的持分（~99M）の
約1/74 しか反映されない。10-Q には株式数タグが一切存在しないため、
TTM が4四半期合計ではなく4年分の年次EPS合計になる二次バグも発生。

### 修正内容
1. `config/cik_lookup.csv`: FOURのepsフラグ true→false（EPS Analyzerスキップ）
2. `src/value/tanuki_valuation/pipeline.py`: yf/SEC株式数乖離>10倍の場合に
   希薄化計算をスキップするサニティチェック追加（comps参照修正も含む）
3. `config/discover_config.json`: FOURのmemoにUP-C構造の注意事項を記録

### 汎用効果
SEC/yfinance乖離10倍サニティチェックはFOUR以外にも適用される。
同様のUP-C構造銘柄（APP等）でXBRL異常が発生した際も自動保護される。

### 教訓
UP-C構造（上場会社がLLC管理会社になる形態）ではXBRL株式数が
経済的実態を反映しないケースがある。新規銘柄登録時にUP-C構造の
有無を確認し、該当する場合はeps=false設定を検討する。
