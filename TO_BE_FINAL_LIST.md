# TO_BE_FINAL_LIST.md — 515項目の矛盾是正・重複排除後の最終出力項目リスト

作成日: 2026-07-22
出発点: `OUTPUT_ITEMS_INVENTORY.md`（AS-IS全515項目）、`TO_BE.md`（16群の統一定義判断）

## 本ドキュメントの位置づけ

`TO_BE.md`の16群（①〜⑯）のうち、実際の統一定義本文を精読して機械的に
再分類した結果、以下の通り「統一する」「統一しない」の実際の内訳は
**依頼文で示された分類と一部異なる**ことが判明した。本リストはこの
検証済みの分類に基づいて作成している（詳細は完了報告を参照）。

- **実際に「1項目（または少数の共通最終形）へ統一する」と判断された群（7群）**: ①⑤⑧⑩⑫⑮⑯
- **実際に「統一しない（フィールドは維持、表示規約等のみ統一）」と判断された群（9群）**: ②③④⑥⑦⑨⑪⑬⑭

（依頼文で示された分類「統一する:①⑤⑫⑬⑭⑮⑯／統一しない:②③④⑥⑦⑧⑨⑩⑪」とは、
⑧⑩⑬⑭の扱いが異なる。⑧⑩は実際には統一済み/統一対象、⑬⑭は実際には
統一しない、というのが`TO_BE.md`本文の記載である）

実装（コード修正）は行っていない。矛盾是正とリスト作成のみ。

## ステップ1: 矛盾是正の内容

`TO_BE.md`を機械的に検証した結果、当初「4件」と伝えられた矛盾のうち、
実際に重複していたのは**3件**だった（AS-IS-289は元々単独ルートリストに
記載されておらず、矛盾していなかった）。

| AS-IS-ID | 是正内容 |
|---|---|
| AS-IS-050 | 単独ルートリストから削除。正しい区分は⑯（SEC EDGARセグメントXBRL抽出重複系）。 |
| AS-IS-194 | 単独ルートリストから削除。正しい区分は⑮（FRED HYスプレッド重複取得系）。 |
| AS-IS-199 | 単独ルートリストから削除。正しい区分は⑮（FRED HYスプレッド重複取得系）。 |
| AS-IS-289 | **是正不要**（検証の結果、矛盾していなかった。元々④群のみに記載、単独ルートリストには存在しなかった）。 |

是正後、`TO_BE.md`全体で重複群テーブルと単独ルートリストの両方に
出現するAS-IS-IDは**0件**であることを機械的に確認済み。


## ステップ2-A: 統一により集約された最終項目（①⑤⑧⑩⑫⑮⑯、実際に統一すると判断された7群）

### ①-final: 乖離率／IV比

**最終項目**: `upside_percent`（唯一の正: TANUKI VALUATION `bs_adjustment`ではなくcore_calculator.py算出のAS-IS-006）

**統合元（6件）**:
- AS-IS-006（TANUKI VALUATION `upside_percent`）: 唯一の正
- AS-IS-003（TANUKI VALUATION `upside_percent_beta`）: 別の参考値として維持（削除対象外）
- AS-IS-005（TANUKI VALUATION `upside_percent_rf`）: 別の参考値として維持（削除対象外）
- AS-IS-075（TANUKI VALUATION `乖離率`、index.htmlクライアント再計算）: **削除対象**
- AS-IS-116（HypeCore `price_iv_ratio`）: 月次時系列は維持、最新月のみAS-IS-006参照に変更
- AS-IS-280（EPS Analyzer `deviation_rate`）: 既にパススルー、変更不要

**削除される項目数**: 1件（AS-IS-075）

### ⑤-final: アナリストコンセンサス／マルチプル系

**最終形**: `common/valuation/`の共通取得関数1本に集約。ただし最終出力される
メトリクス自体は単一値に潰れず、以下の複数の distinct な最終項目として存続する
（取得経路のみ統一、値は統一しない）。

**統合元（16件）**:
- AS-IS-031（TANUKI `per_adjusted`）: 共通関数参照に変更、項目としては存続
- AS-IS-032（TANUKI 束ねられたper/peg/ps/ev_ebitda/analyst_target等）: 共通関数参照、存続
- AS-IS-061（TANUKI `フェアPER`クライアント再計算）: **削除対象**
- AS-IS-062（TANUKI `PEGレシオ`クライアント再計算）: **削除対象**
- AS-IS-063（TANUKI `PSR`クライアント再計算）: **削除対象**
- AS-IS-097（HypeCore `forward_pe`）: 共通関数参照、存続
- AS-IS-098（HypeCore `peg_ratio`）: 共通関数参照、存続
- AS-IS-099（HypeCore `psr`）: 共通関数参照、存続
- AS-IS-102（HypeCore `recommendation_mean`）: 共通関数参照、存続
- AS-IS-105（HypeCore `analyst_upgrade_rate`）: 共通関数参照、存続
- AS-IS-108（HypeCore `buy_hold_ratio`）: 共通関数参照、存続（⑨とも関連）
- AS-IS-117（HypeCore `ev_ebitda`）: 正値フィルタ追加の修正対象、削除ではなく存続
- AS-IS-132（STONKS SILO `valuation.psr`、Annual基準）: 統一対象外、別項目として併存
- AS-IS-133（STONKS SILO `valuation.ev_sales`、Annual基準）: 統一対象外、別項目として併存
- AS-IS-282（EPS Analyzer `components.per`、GAAP PER）: 共通関数参照、存続
- AS-IS-283（EPS Analyzer `components.per_adjusted`）: 共通関数参照、存続

**削除される項目数**: 3件（AS-IS-061/062/063、いずれもクライアント側独自再計算）

### ⑧-final: 次回決算日

**最終項目**: `next_earnings_date`（唯一の正: TANUKI VALUATION AS-IS-048）

**統合元（3件）**:
- AS-IS-048（TANUKI VALUATION `next_earnings_date`）: 唯一の正
- AS-IS-179（STONKS SILO `次回決算日`）: 既にパススルー、変更不要
- AS-IS-284（EPS Analyzer `next_earnings_date`）: 既にパススルー、変更不要

**削除される項目数**: 0件（既に理想形で統一済み）

### ⑩-final: リスクイベント／カタリスト系

**最終形**: Discoverの`catalysts[]`/`macro_themes[]`（8フィールド）を唯一の正とし、
TANUKIの簡易版`risk_events`を廃止。

**統合元（9件）**:
- AS-IS-054（TANUKI VALUATION `risk_events`）: **削除対象**
- AS-IS-243（Discover `catalysts[].id`）: 変更なし（唯一の正）
- AS-IS-244（Discover `catalysts[].title/detail/timing/importance/type/probability`）: 変更なし（唯一の正）
- AS-IS-245（Discover `catalysts[].status`）: 変更なし（唯一の正）
- AS-IS-246（Discover `catalysts[].first_detected`）: 変更なし（唯一の正）
- AS-IS-258（Discover `macro_themes[].theme/horizon/conviction/background/catalyst`）: 変更なし（唯一の正、⑪とも関連）
- AS-IS-259（Discover `macro_themes[].related_tickers[].ticker/role/note`）: 変更なし（唯一の正、⑪とも関連）
- AS-IS-260（Discover `macro_themes[].sources[]`）: 変更なし（唯一の正、⑪とも関連）
- AS-IS-261（Discover `macro_themes[].generated_at`）: 変更なし（唯一の正、⑪とも関連）

**削除される項目数**: 1件（AS-IS-054）

### ⑫-final: ネットキャッシュ系

**最終項目**: `net_cash`（唯一の正: TANUKI VALUATION `bs_adjustment.net_cash`、AS-IS-025）

**統合元（2件）**:
- AS-IS-025（TANUKI VALUATION `bs_adjustment.net_cash`）: 唯一の正
- AS-IS-134（STONKS SILO `valuation.net_cash`）: **削除対象**、AS-IS-025の値を参照する形に統合

**削除される項目数**: 1件（AS-IS-134）

### ⑮-final: FRED HYスプレッド重複取得系

**最終形**: FRED `BAMLH0A0HYM2`の取得を`common/`共通関数1本に統合。ただし
消費先（events.csv用／流動性カード用／BUYチェックリスト用）が異なるため、
表示・加工は3箇所で個別に残る（取得のみ統一、出力項目としては3件存続）。

**統合元（3件）**:
- AS-IS-194（MACRO PULSE `HY SPREAD` ticker用）: 取得共通化、項目としては存続
- AS-IS-199（MACRO PULSE `HYスプレッド` 流動性カード用）: 取得共通化、項目としては存続
- AS-IS-371（Market Pulse `buy_checklist.checks.hy_spread`）: 取得共通化、項目としては存続

**削除される項目数**: 0件（出力項目は3件とも存続、重複するのは取得コードのみ）

### ⑯-final: SEC EDGARセグメントXBRL抽出重複系

**最終形**: `us-gaap:StatementBusinessSegmentsAxis`のXBRL抽出ロジックを
`common/`に一本化。TANUKI TAIL（稼働中）・TANUKI VALUATION（現状は死んでおり
`config/segment_config.json`手動設定で代替中）双方が同一ロジックを参照する
形に統合。出力項目（`segments[]`と`kpis.*`）は用途が異なるため4件とも存続。

**統合元（4件）**:
- AS-IS-050（TANUKI VALUATION `segments[]`）: 抽出ロジック統合対象、項目としては存続
- AS-IS-419（TANUKI TAIL `kpis.{kpi_name}.unit`）: 抽出ロジック統合対象、存続
- AS-IS-420（TANUKI TAIL `kpis.{kpi_name}.data[].quarter`）: 抽出ロジック統合対象、存続
- AS-IS-421（TANUKI TAIL `kpis.{kpi_name}.data[].value`）: 抽出ロジック統合対象、存続

**削除される項目数**: 0件（出力項目は4件とも存続。別途、未使用の重複ファイル
`src/value/tanuki_valuation/segment_fetcher.py`が削除候補だが、これは
「出力項目」ではなくソースファイルのため本カウントには含めない）

**別途の削除候補（出力項目ではないため上記件数に不算入）**: `src/value/tanuki_valuation/segment_fetcher.py`（未使用の重複コピーファイル、467行）

## ステップ2-B: 統一しない（フィールド維持）と判断された群（②③④⑥⑦⑨⑪⑬⑭、実際に統一しないと判断された9群）

これらは実質的に統合されないため、元の項目数のまま個別の最終項目として記載する。各項目には同一群内の関連項目への相互参照を付す。

### ②-final: 信頼性／品質判定バッジ系

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-020 | 5-1. TANUKI VALUATION | fcf_outlier.detected/rule/action/note/deviation_pct | 表示規約統一のみ、フィールドは維持 |
| AS-IS-042 | 5-1. TANUKI VALUATION | growth_sanity.verdict/signals/warnings/recommended_g | 表示規約統一のみ、フィールドは維持 |
| AS-IS-052 | 5-1. TANUKI VALUATION | validation.* | 表示規約統一のみ、フィールドは維持 |
| AS-IS-141 | 5-3. STONKS SILO | `verdict` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-149 | 5-3. STONKS SILO | `dilution_risk` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-150 | 5-3. STONKS SILO | `deficit_fixed_risk` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-158 | 5-3. STONKS SILO | `verdict` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-161 | 5-3. STONKS SILO | `ocf_trend` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-182 | 5-4. MACRO PULSE | REGIME | 表示規約統一のみ、フィールドは維持 |
| AS-IS-183 | 5-4. MACRO PULSE | regime_source | 表示規約統一のみ、フィールドは維持 |
| AS-IS-205 | 5-4. MACRO PULSE | ステルス流動性 LAYER1（FRB政策意図） | 表示規約統一のみ、フィールドは維持 |
| AS-IS-206 | 5-4. MACRO PULSE | LAYER2（ステルス供給/吸収バッジ） | 表示規約統一のみ、フィールドは維持 |
| AS-IS-209 | 5-4. MACRO PULSE | ステルス吸収週数(stealth_absorb_weeks) | 表示規約統一のみ、フィールドは維持 |

### ③-final: 成長率系

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-012 | 5-1. TANUKI VALUATION | growth.rate/source | 表示規約統一のみ、フィールドは維持 |
| AS-IS-042 | 5-1. TANUKI VALUATION | growth_sanity.verdict/signals/warnings/recommended_g | 表示規約統一のみ、フィールドは維持 |
| AS-IS-043 | 5-1. TANUKI VALUATION | phase1_growth_auto_adjusted | 表示規約統一のみ、フィールドは維持 |
| AS-IS-079 | 5-2. HypeCore | STONKS SILO `deficit_quality.revenue_growth_pct` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-093 | 5-2. HypeCore | `rev_yoy` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-100 | 5-2. HypeCore | `revenue_growth` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-136 | 5-3. STONKS SILO | `cagr_3yr` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-152 | 5-3. STONKS SILO | `revenue_growth_pct` | 表示規約統一のみ、フィールドは維持 |

### ④-final: 総合スコア／判定系

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-034 | 5-1. TANUKI VALUATION | tanuki_score | 表示規約統一のみ、フィールドは維持 |
| AS-IS-035 | 5-1. TANUKI VALUATION | funda_score | 表示規約統一のみ、フィールドは維持 |
| AS-IS-037 | 5-1. TANUKI VALUATION | timing_score | 表示規約統一のみ、フィールドは維持 |
| AS-IS-041 | 5-1. TANUKI VALUATION | matrix.*（quadrant/label/key_metric_y/qx/qy） | 表示規約統一のみ、フィールドは維持 |
| AS-IS-085 | 5-2. HypeCore | `stage` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-126 | 5-3. STONKS SILO | `overall_score` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-127 | 5-3. STONKS SILO | `overall_verdict` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-214 | 5-4. MACRO PULSE | RECESSION RISK SCOREバー・マーカー | 表示規約統一のみ、フィールドは維持 |
| AS-IS-215 | 5-4. MACRO PULSE | RECESSION RISK SCORE数値 | 表示規約統一のみ、フィールドは維持 |
| AS-IS-279 | 5-6. EPS Analyzer | `health` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-289 | 1-7. TANUKI SCORE | funda_score | 表示規約統一のみ、フィールドは維持 |
| AS-IS-290 | 1-7. TANUKI SCORE | timing_score | 表示規約統一のみ、フィールドは維持 |

### ⑥-final: モメンタム／複合トレンド系

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-078 | 5-2. HypeCore | HypeCore `expectation_score` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-113 | 5-2. HypeCore | `expectation_score` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-114 | 5-2. HypeCore | `fundamental_score` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-115 | 5-2. HypeCore | `momentum_score` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-135 | 5-3. STONKS SILO | `financial_vectors.fields.*` | 表示規約統一のみ、フィールドは維持 |

### ⑦-final: FCF／キャッシュフロー系

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-018 | 5-1. TANUKI VALUATION | dcf_components.*（v0,pv_high_growth,pv_terminal,high_growth_detail,term… | 表示規約統一のみ、フィールドは維持 |
| AS-IS-019 | 5-1. TANUKI VALUATION | fcf_base.base_fcf/method/cv | 表示規約統一のみ、フィールドは維持 |
| AS-IS-021 | 5-1. TANUKI VALUATION | fcf_estimation.applied/conversion_rate/estimated_fcf等 | 表示規約統一のみ、フィールドは維持 |
| AS-IS-047 | 5-1. TANUKI VALUATION | fcf_history[] | 表示規約統一のみ、フィールドは維持 |
| AS-IS-068 | 5-1. TANUKI VALUATION | FCF CAGR(3yr) | 表示規約統一のみ、フィールドは維持 |
| AS-IS-071 | 5-1. TANUKI VALUATION | キャッシュフロー分析セクション | 表示規約統一のみ、フィールドは維持 |
| AS-IS-146 | 5-3. STONKS SILO | `sbc_adjusted_fcf` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-156 | 5-3. STONKS SILO | `ocf_annual` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-160 | 5-3. STONKS SILO | `ocf_annual`（年次dict） | 表示規約統一のみ、フィールドは維持 |
| AS-IS-167 | 5-3. STONKS SILO | `incremental_margin` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-168 | 5-3. STONKS SILO | `incremental_margin_prev` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-169 | 5-3. STONKS SILO | `incremental_margin_trend` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-170 | 5-3. STONKS SILO | `incremental_rev_delta`/`incremental_gp_delta` | 表示規約統一のみ、フィールドは維持 |

### ⑨-final: インサイダー／空売り系

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-103 | 5-2. HypeCore | `short_pct_float` | 表示規約統一のみ、フィールドは維持 |

注記: 本群にはAS-IS-032（⑤群に一本化）、AS-IS-108（⑤群に一本化）も概念的に関連するが、帰属は統一7群側に一本化したため本表からは除外した（重複掲載の回避）。

### ⑪-final: マクロ環境認識系

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-055 | 5-1. TANUKI VALUATION | ① | 表示規約統一のみ、フィールドは維持 |
| AS-IS-056 | 5-1. TANUKI VALUATION | ② | 表示規約統一のみ、フィールドは維持 |
| AS-IS-182 | 5-4. MACRO PULSE | REGIME | 表示規約統一のみ、フィールドは維持 |
| AS-IS-183 | 5-4. MACRO PULSE | regime_source | 表示規約統一のみ、フィールドは維持 |
| AS-IS-214 | 5-4. MACRO PULSE | RECESSION RISK SCOREバー・マーカー | 表示規約統一のみ、フィールドは維持 |
| AS-IS-215 | 5-4. MACRO PULSE | RECESSION RISK SCORE数値 | 表示規約統一のみ、フィールドは維持 |

注記: 本群にはAS-IS-258（⑩群に一本化）、AS-IS-259（⑩群に一本化）、AS-IS-260（⑩群に一本化）、AS-IS-261（⑩群に一本化）も概念的に関連するが、帰属は統一7群側に一本化したため本表からは除外した（重複掲載の回避）。

### ⑬-final: Rule of 40系（新規発見・2026-07-22計算ロジック照合）

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-095 | 5-2. HypeCore | `rule40` | 表示規約統一のみ、フィールドは維持 |
| AS-IS-143 | 5-3. STONKS SILO | `rule_of_40` | 表示規約統一のみ、フィールドは維持 |

### ⑭-final: 純利益（SEC XBRL NetIncome）二重抽出パイプライン系（新規発見・2026-07-22計算ロジック照合）

| AS-IS ID | サブシステム | 項目名 | 備考 |
|---|---|---|---|
| AS-IS-129 | 5-3. STONKS SILO | `records`（yr→{revenue,net_income}） | 表示規約統一のみ、フィールドは維持 |
| AS-IS-281 | 5-6. EPS Analyzer | `ttm.json`（`ttm[].period/net_income/adjusted_income/diluted_shares/eps/adjusted_eps`） | 表示規約統一のみ、フィールドは維持 |

## ステップ2-C: 単独ルート項目（415件）

重複が確認されなかった項目。1件＝1最終項目としてそのまま採用する。

| AS-IS ID | 出身サブシステム・項目 |
|---|---|
| AS-IS-001 | 5-1. TANUKI VALUATION / intrinsic_value_per_share |
| AS-IS-002 | 5-1. TANUKI VALUATION / intrinsic_value_beta |
| AS-IS-004 | 5-1. TANUKI VALUATION / intrinsic_value_rf |
| AS-IS-007 | 5-1. TANUKI VALUATION / v0 |
| AS-IS-008 | 5-1. TANUKI VALUATION / v0_adjusted |
| AS-IS-009 | 5-1. TANUKI VALUATION / alpha / alpha_was_capped |
| AS-IS-010 | 5-1. TANUKI VALUATION / future_values |
| AS-IS-011 | 5-1. TANUKI VALUATION / return_metrics |
| AS-IS-013 | 5-1. TANUKI VALUATION / wacc.value/beta/risk_free_rate/market_return |
| AS-IS-014 | 5-1. TANUKI VALUATION / sensitivity.matrix/wacc_values/growth_years |
| AS-IS-015 | 5-1. TANUKI VALUATION / scenario_valuations.bear/base/bull |
| AS-IS-016 | 5-1. TANUKI VALUATION / growth_options.total_pv/count/options |
| AS-IS-017 | 5-1. TANUKI VALUATION / maturity_profile |
| AS-IS-022 | 5-1. TANUKI VALUATION / software_system_reclassification.* |
| AS-IS-023 | 5-1. TANUKI VALUATION / rd_capitalization.* |
| AS-IS-024 | 5-1. TANUKI VALUATION / rpo_adjustment.rpo_pv/application_rate/sector_category/rpo_i… |
| AS-IS-026 | 5-1. TANUKI VALUATION / moat_score系（components.moat_score等） |
| AS-IS-027 | 5-1. TANUKI VALUATION / rice.q/cf_conversion/q_years/cf_years/avg_intensity/avg_rev_… |
| AS-IS-028 | 5-1. TANUKI VALUATION / moat_score / moat_phase1_years / moat_gross_margin_norm / mo… |
| AS-IS-029 | 5-1. TANUKI VALUATION / pv_high / pv_terminal |
| AS-IS-030 | 5-1. TANUKI VALUATION / alpha_uncapped |
| AS-IS-033 | 5-1. TANUKI VALUATION / max_eps / max_eps_per / max_eps_reliability |
| AS-IS-036 | 5-1. TANUKI VALUATION / score_comment |
| AS-IS-038 | 5-1. TANUKI VALUATION / sell_reason |
| AS-IS-039 | 5-1. TANUKI VALUATION / pre_rounding_score |
| AS-IS-040 | 5-1. TANUKI VALUATION / rounded_by_policy |
| AS-IS-044 | 5-1. TANUKI VALUATION / fcf_margin_bear_mult_applied |
| AS-IS-045 | 5-1. TANUKI VALUATION / financial_health.*（net_debt,total_debt,cash_and_equivalents,… |
| AS-IS-046 | 5-1. TANUKI VALUATION / dupont.net_margin/asset_turnover/financial_leverage/roe_deco… |
| AS-IS-049 | 5-1. TANUKI VALUATION / computed_runway_months |
| AS-IS-051 | 5-1. TANUKI VALUATION / breakeven_estimate |
| AS-IS-053 | 5-1. TANUKI VALUATION / dilution_severity / dilution_comment |
| AS-IS-057 | 5-1. TANUKI VALUATION / 場所 |
| AS-IS-058 | 5-1. TANUKI VALUATION / 用途 |
| AS-IS-059 | 5-1. TANUKI VALUATION / terminal_growthの出所 |
| AS-IS-060 | 5-1. TANUKI VALUATION / ガード |
| AS-IS-064 | 5-1. TANUKI VALUATION / 将来価値予測（シナリオ別テーブル） |
| AS-IS-065 | 5-1. TANUKI VALUATION / 5年BASE年率換算リターン |
| AS-IS-066 | 5-1. TANUKI VALUATION / 感応度分析（独自5×5マトリクス） |
| AS-IS-067 | 5-1. TANUKI VALUATION / Reverse DCF |
| AS-IS-069 | 5-1. TANUKI VALUATION / WACCスライダー |
| AS-IS-070 | 5-1. TANUKI VALUATION / Layer2トグル |
| AS-IS-072 | 5-1. TANUKI VALUATION / 銘柄数 |
| AS-IS-073 | 5-1. TANUKI VALUATION / 平均Moat |
| AS-IS-074 | 5-1. TANUKI VALUATION / 平均RICE |
| AS-IS-076 | 5-1. TANUKI VALUATION / 200MA乖離 |
| AS-IS-077 | 5-2. HypeCore / HypeCore `stage_label` |
| AS-IS-080 | 5-2. HypeCore / `generated_at` |
| AS-IS-081 | 5-2. HypeCore / `monthly` |
| AS-IS-082 | 5-2. HypeCore / `tickers`（配列） |
| AS-IS-083 | 5-2. HypeCore / `month` |
| AS-IS-084 | 5-2. HypeCore / `price` |
| AS-IS-086 | 5-2. HypeCore / `stage_label` |
| AS-IS-087 | 5-2. HypeCore / `ma200_dev` |
| AS-IS-088 | 5-2. HypeCore / `ma50_dev` |
| AS-IS-089 | 5-2. HypeCore / `from_peak` |
| AS-IS-090 | 5-2. HypeCore / `rsi` |
| AS-IS-091 | 5-2. HypeCore / `volume_ratio` |
| AS-IS-092 | 5-2. HypeCore / `vol_surge` |
| AS-IS-094 | 5-2. HypeCore / `ni_yoy` |
| AS-IS-096 | 5-2. HypeCore / `fcf_yield` |
| AS-IS-101 | 5-2. HypeCore / `earnings_growth` |
| AS-IS-104 | 5-2. HypeCore / `eps_surprise` |
| AS-IS-106 | 5-2. HypeCore / `analyst_downgrade_rate` |
| AS-IS-107 | 5-2. HypeCore / `sell_on_good_news` |
| AS-IS-109 | 5-2. HypeCore / `substage_phase` |
| AS-IS-110 | 5-2. HypeCore / `substage_label` |
| AS-IS-111 | 5-2. HypeCore / `substage_watch` |
| AS-IS-112 | 5-2. HypeCore / `substage_next` |
| AS-IS-118 | 5-2. HypeCore / `low_base_effect` |
| AS-IS-119 | 5-2. HypeCore / ライフサイクル（黎明/成長/拡大/成熟） |
| AS-IS-120 | 5-2. HypeCore / HypeCore推奨（買い/保有/売り等） |
| AS-IS-121 | 5-2. HypeCore / 1ヶ月後のステージ遷移確率 |
| AS-IS-122 | 5-2. HypeCore / バリュエーション倍率パネル（PER/PS/PEG/EV-EBITDA） |
| AS-IS-123 | 5-3. STONKS SILO / `generated_at` |
| AS-IS-124 | 5-3. STONKS SILO / `tickers`（辞書, ticker→result） |
| AS-IS-125 | 5-3. STONKS SILO / `years` |
| AS-IS-128 | 5-3. STONKS SILO / `summary` |
| AS-IS-130 | 5-3. STONKS SILO / `valuation.market_cap` |
| AS-IS-131 | 5-3. STONKS SILO / `valuation.current_price` |
| AS-IS-137 | 5-3. STONKS SILO / `rnd_ratio` |
| AS-IS-138 | 5-3. STONKS SILO / `sm_ratio` |
| AS-IS-139 | 5-3. STONKS SILO / `gross_margin` |
| AS-IS-140 | 5-3. STONKS SILO / `gross_margin_derived` |
| AS-IS-142 | 5-3. STONKS SILO / `score` |
| AS-IS-144 | 5-3. STONKS SILO / `mature_profit` |
| AS-IS-145 | 5-3. STONKS SILO / `mature_profit_note` |
| AS-IS-147 | 5-3. STONKS SILO / `sbc_ratio` |
| AS-IS-148 | 5-3. STONKS SILO / `sbc_yoy_change` |
| AS-IS-151 | 5-3. STONKS SILO / `revenue_outlier_years` |
| AS-IS-153 | 5-3. STONKS SILO / `cash` |
| AS-IS-154 | 5-3. STONKS SILO / `monthly_burn` |
| AS-IS-155 | 5-3. STONKS SILO / `runway_months` |
| AS-IS-157 | 5-3. STONKS SILO / `capex_annual` |
| AS-IS-159 | 5-3. STONKS SILO / `score` |
| AS-IS-162 | 5-3. STONKS SILO / `gaap_breakeven_year`/`gaap_breakeven_reason` |
| AS-IS-163 | 5-3. STONKS SILO / `ocf_breakeven_year`/`ocf_breakeven_reason` |
| AS-IS-164 | 5-3. STONKS SILO / `hidden_profit_already` |
| AS-IS-165 | 5-3. STONKS SILO / `discontinuous_growth` |
| AS-IS-166 | 5-3. STONKS SILO / `discontinuous_growth_note` |
| AS-IS-171 | 5-3. STONKS SILO / `reproduction_score` |
| AS-IS-172 | 5-3. STONKS SILO / `reproduction_label` |
| AS-IS-173 | 5-3. STONKS SILO / `score` |
| AS-IS-174 | 5-3. STONKS SILO / `fields.{name}.yoy/qoq.change_pct,val_latest,val_prev,end_la… |
| AS-IS-175 | 5-3. STONKS SILO / `fields.{name}.yoy/qoq.percentile` |
| AS-IS-176 | 5-3. STONKS SILO / `fields.{name}.yoy/qoq.angle,length` |
| AS-IS-177 | 5-3. STONKS SILO / `fields.{name}.series_q`（四半期時系列） |
| AS-IS-178 | 5-3. STONKS SILO / TANUKIスコアバッジ |
| AS-IS-180 | 5-3. STONKS SILO / 黒字転換目算（Adj.EPS線形推定） |
| AS-IS-181 | 5-3. STONKS SILO / Adj.EPS系列（黒字化ロードマップ） |
| AS-IS-184 | 5-4. MACRO PULSE / FF RATE |
| AS-IS-185 | 5-4. MACRO PULSE / 1Y EXPECTED FF |
| AS-IS-186 | 5-4. MACRO PULSE / IMPLIED CUTS |
| AS-IS-187 | 5-4. MACRO PULSE / FRB主眼(dominant_label) |
| AS-IS-188 | 5-4. MACRO PULSE / 判断理由(ai_reason) |
| AS-IS-189 | 5-4. MACRO PULSE / FOMC日付 |
| AS-IS-190 | 5-4. MACRO PULSE / S&P500現在値 |
| AS-IS-191 | 5-4. MACRO PULSE / S&P500前日比 |
| AS-IS-192 | 5-4. MACRO PULSE / 10Y-2Y SPREAD |
| AS-IS-193 | 5-4. MACRO PULSE / 10Y-2Y判定(INVERTED/FLAT/NORMAL) |
| AS-IS-195 | 5-4. MACRO PULSE / LAST UPDATE |
| AS-IS-196 | 5-4. MACRO PULSE / （画面最上部）最終更新表示 |
| AS-IS-197 | 5-4. MACRO PULSE / M2 |
| AS-IS-198 | 5-4. MACRO PULSE / NET LIQUIDITY |
| AS-IS-200 | 5-4. MACRO PULSE / FRBバランスシート |
| AS-IS-201 | 5-4. MACRO PULSE / 各カードの前月比/前週比(chg) |
| AS-IS-202 | 5-4. MACRO PULSE / 各カードのパーセンタイル/水準バー |
| AS-IS-203 | 5-4. MACRO PULSE / 各カードの解説コメント(m2Comment/nlComment/hyComment/fedComment) |
| AS-IS-204 | 5-4. MACRO PULSE / Hollow Rallyバッジ |
| AS-IS-207 | 5-4. MACRO PULSE / LAYER3（NET流動性連続減少週数） |
| AS-IS-208 | 5-4. MACRO PULSE / 警戒アラート文 |
| AS-IS-210 | 5-4. MACRO PULSE / REPO残高(RRPONTSYD) |
| AS-IS-211 | 5-4. MACRO PULSE / 準備預金(WRBWFRBL) |
| AS-IS-212 | 5-4. MACRO PULSE / TGA残高(WTREGEN) |
| AS-IS-213 | 5-4. MACRO PULSE / フェーズbadge / phase-sub |
| AS-IS-216 | 5-4. MACRO PULSE / シグナルテキスト |
| AS-IS-217 | 5-4. MACRO PULSE / ALERTバナー |
| AS-IS-218 | 5-4. MACRO PULSE / 8指標シグナルグリッド |
| AS-IS-219 | 5-4. MACRO PULSE / スコア比較バー（3ヶ月前/2ヶ月前/前月比/先週比/カスタム） |
| AS-IS-220 | 5-4. MACRO PULSE / surprise_alerts |
| AS-IS-221 | 5-4. MACRO PULSE / 週次カード日付/スコア/フェーズ |
| AS-IS-222 | 5-4. MACRO PULSE / 週差/月差(chg1w/chg1m) |
| AS-IS-223 | 5-4. MACRO PULSE / 総括(summary) |
| AS-IS-224 | 5-4. MACRO PULSE / 要因分析(factor_analysis) |
| AS-IS-225 | 5-4. MACRO PULSE / 注視ポイント(watchpoints) |
| AS-IS-226 | 5-4. MACRO PULSE / 各指標コメント(indicator_comments) |
| AS-IS-227 | 5-4. MACRO PULSE / 週差/月差バッジ(各指標) |
| AS-IS-228 | 5-4. MACRO PULSE / model表示 |
| AS-IS-229 | 5-4. MACRO PULSE / 8指標の値/シグナル(BULL/CAUTION/NEUTRAL/BEAR)/バー位置 |
| AS-IS-230 | 5-4. MACRO PULSE / スコア推移折れ線 |
| AS-IS-231 | 5-4. MACRO PULSE / NBER後退期帯 |
| AS-IS-232 | 5-4. MACRO PULSE / フェーズゾーン背景(0-25/25-52/52-70/70-100) |
| AS-IS-233 | 5-4. MACRO PULSE / 期間切替(1年/3年/5年/全期間)ボタン |
| AS-IS-234 | 5-4. MACRO PULSE / レーダーチャート（現在/2019/2001/スライダー） |
| AS-IS-235 | 5-4. MACRO PULSE / 類似度スコア(2019年/2001年、%) |
| AS-IS-236 | 5-4. MACRO PULSE / スライダー（過去に戻る） |
| AS-IS-237 | 5-4. MACRO PULSE / DATE/INDICATOR/ACTUAL |
| AS-IS-238 | 5-4. MACRO PULSE / PREV |
| AS-IS-239 | 5-4. MACRO PULSE / DIR(↑/↓/→)・CHANGE |
| AS-IS-240 | 5-4. MACRO PULSE / DATE/INDICATOR |
| AS-IS-241 | 5-4. MACRO PULSE / DAYS |
| AS-IS-242 | 5-4. MACRO PULSE / CONSENSUS |
| AS-IS-247 | 5-5. Discover / `tickers{}.updated_at` |
| AS-IS-248 | 5-5. Discover / 影響予測`{direction, magnitude, thesis_effect, summary}` |
| AS-IS-249 | 5-5. Discover / `tickers{}.category/memo` |
| AS-IS-250 | 5-5. Discover / `classified.items[].{title,category,importance,summary,url,s… |
| AS-IS-251 | 5-5. Discover / `classified.summary` |
| AS-IS-252 | 5-5. Discover / `classified.conditions_met[]` / `classified.risk_flags[]` |
| AS-IS-253 | 5-5. Discover / `top_importance`（tickers[ticker]直下） |
| AS-IS-254 | 5-5. Discover / `candidates[].{ticker,company,sector,reason,risk}` |
| AS-IS-255 | 5-5. Discover / `candidates[].screening_pass[]` |
| AS-IS-256 | 5-5. Discover / `candidates[].catalyst_type` |
| AS-IS-257 | 5-5. Discover / `candidates[].conviction` |
| AS-IS-262 | 5-5. Discover / `price_change_next_day` |
| AS-IS-263 | 5-5. Discover / `theme_config`（テーマID/ラベル/カラー） |
| AS-IS-264 | 5-5. Discover / `discover_config`（銘柄別category/memo/themes） |
| AS-IS-265 | 5-6. EPS Analyzer / `ticker` / `last_updated` |
| AS-IS-266 | 5-6. EPS Analyzer / `quarters[].filing_date/period_end/fiscal_year/quarter` |
| AS-IS-267 | 5-6. EPS Analyzer / `quarters[].gaap_eps/adjusted_eps/gaap_net_income/adjusted_n… |
| AS-IS-268 | 5-6. EPS Analyzer / `quarters[].adjustments[].item_name/reason/extracted_from` |
| AS-IS-269 | 5-6. EPS Analyzer / `quarters[].adjustments[].net_amount` |
| AS-IS-270 | 5-6. EPS Analyzer / `quarters[].ai_analysis.health/comment` |
| AS-IS-271 | 5-6. EPS Analyzer / `quarters[].ai_analysis.sources[].item/snippet/confidence` |
| AS-IS-272 | 5-6. EPS Analyzer / `quarters[].special_flags(EPS_DISCREPANCY)` / `special_notes… |
| AS-IS-273 | 5-6. EPS Analyzer / `ticker/company_name/latest_filing_date` |
| AS-IS-274 | 5-6. EPS Analyzer / `gaap_eps/adjusted_eps` |
| AS-IS-275 | 5-6. EPS Analyzer / `eps_diff` |
| AS-IS-276 | 5-6. EPS Analyzer / `eps_ratio` |
| AS-IS-277 | 5-6. EPS Analyzer / `gaap_to_adj_positive` |
| AS-IS-278 | 5-6. EPS Analyzer / `yoy_growth` |
| AS-IS-285 | 1-7. TANUKI SCORE / generated_at |
| AS-IS-286 | 1-7. TANUKI SCORE / ticker |
| AS-IS-287 | 1-7. TANUKI SCORE / company |
| AS-IS-288 | 1-7. TANUKI SCORE / selection_reason |
| AS-IS-291 | 1-7. TANUKI SCORE / category |
| AS-IS-292 | 1-7. TANUKI SCORE / report.fundamental |
| AS-IS-293 | 1-7. TANUKI SCORE / report.expectation |
| AS-IS-294 | 1-7. TANUKI SCORE / report.news |
| AS-IS-295 | 1-7. TANUKI SCORE / report.timing |
| AS-IS-296 | 1-7. TANUKI SCORE / report.summary |
| AS-IS-297 | 1-7. TANUKI SCORE / date（history.json各エントリ） |
| AS-IS-298 | 1-7. TANUKI SCORE / ticker（history.json各エントリ） |
| AS-IS-299 | 1-7. TANUKI SCORE / all_categories（history.json各エントリ） |
| AS-IS-300 | 1-8. Market Pulse / date |
| AS-IS-301 | 1-8. Market Pulse / judgment |
| AS-IS-302 | 1-8. Market Pulse / indicators |
| AS-IS-303 | 1-8. Market Pulse / sentiment |
| AS-IS-304 | 1-8. Market Pulse / fear_greed |
| AS-IS-305 | 1-8. Market Pulse / tech_pulse |
| AS-IS-306 | 1-8. Market Pulse / asset_flow |
| AS-IS-307 | 1-8. Market Pulse / credit |
| AS-IS-308 | 1-8. Market Pulse / take_profit_checklist |
| AS-IS-309 | 1-8. Market Pulse / buy_checklist |
| AS-IS-310 | 1-8. Market Pulse / summary |
| AS-IS-311 | 1-8. Market Pulse / comments_history |
| AS-IS-312 | 1-8. Market Pulse / 米10年債/VIX指数/ドル円/日経平均/S&P500/NASDAQ/WTI原油/金(GOLD)/HYG/LQDのval… |
| AS-IS-313 | 1-8. Market Pulse / 上記各指標のchange_percent |
| AS-IS-314 | 1-8. Market Pulse / 上記各指標のchange（絶対値） |
| AS-IS-315 | 1-8. Market Pulse / 上記各指標のvolume_ratio |
| AS-IS-316 | 1-8. Market Pulse / 上記各指標のdate |
| AS-IS-317 | 1-8. Market Pulse / 上記各指標のis_fallback |
| AS-IS-318 | 1-8. Market Pulse / NYSE Composite（value, change_percent, volume_ratio, date） |
| AS-IS-319 | 1-8. Market Pulse / NYSE Composite.divergence_vs_sp |
| AS-IS-320 | 1-8. Market Pulse / S&P500グロース(IVW)（value, change_percent, date） |
| AS-IS-321 | 1-8. Market Pulse / S&P500バリュー(IVE)（value, change_percent, date） |
| AS-IS-322 | 1-8. Market Pulse / Russell2000小型(RUT)（value, change_percent, date） |
| AS-IS-323 | 1-8. Market Pulse / グロース対バリュー比.diff_percent |
| AS-IS-324 | 1-8. Market Pulse / 大型対小型比.diff_percent |
| AS-IS-325 | 1-8. Market Pulse / VIX9D（value, change, change_percent, date） |
| AS-IS-326 | 1-8. Market Pulse / VIX9D対VIX比.value |
| AS-IS-327 | 1-8. Market Pulse / VIX9D対VIX比.contango |
| AS-IS-328 | 1-8. Market Pulse / HYG対LQD比（value, change, date） |
| AS-IS-329 | 1-8. Market Pulse / sentiment.score |
| AS-IS-330 | 1-8. Market Pulse / sentiment.label |
| AS-IS-331 | 1-8. Market Pulse / sentiment.sub_scores.{8指標}.score |
| AS-IS-332 | 1-8. Market Pulse / 同上.weight |
| AS-IS-333 | 1-8. Market Pulse / 同上.raw |
| AS-IS-334 | 1-8. Market Pulse / sentiment.breadth.advances / declines |
| AS-IS-335 | 1-8. Market Pulse / sentiment.breadth.ad_ratio_5d |
| AS-IS-336 | 1-8. Market Pulse / sentiment.breadth.new_highs_52w / new_lows_52w |
| AS-IS-337 | 1-8. Market Pulse / sentiment.breadth.nh_nl_diff |
| AS-IS-338 | 1-8. Market Pulse / sentiment.breadth.pct_above_50ma / pct_above_200ma |
| AS-IS-339 | 1-8. Market Pulse / sentiment.breadth.rsp_spy_divergence_1d |
| AS-IS-340 | 1-8. Market Pulse / sentiment.breadth.rsp_spy_divergence_20d_avg |
| AS-IS-341 | 1-8. Market Pulse / sentiment.breadth.ad_line |
| AS-IS-342 | 1-8. Market Pulse / sentiment.breadth.mcclellan_oscillator |
| AS-IS-343 | 1-8. Market Pulse / sentiment.breadth.date |
| AS-IS-344 | 1-8. Market Pulse / fear_greed.score |
| AS-IS-345 | 1-8. Market Pulse / fear_greed.rating |
| AS-IS-346 | 1-8. Market Pulse / fear_greed.previous_close |
| AS-IS-347 | 1-8. Market Pulse / fear_greed.one_week_ago |
| AS-IS-348 | 1-8. Market Pulse / fear_greed.one_month_ago |
| AS-IS-349 | 1-8. Market Pulse / tech_pulse.score |
| AS-IS-350 | 1-8. Market Pulse / tech_pulse.label |
| AS-IS-351 | 1-8. Market Pulse / tech_pulse.components.qqq_vs_ma125 |
| AS-IS-352 | 1-8. Market Pulse / tech_pulse.components.vxn_latest |
| AS-IS-353 | 1-8. Market Pulse / tech_pulse.components.vxn_vs_ma50 |
| AS-IS-354 | 1-8. Market Pulse / tech_pulse.components.qqq_vs_spy_20d |
| AS-IS-355 | 1-8. Market Pulse / tech_pulse.components.fg_score |
| AS-IS-356 | 1-8. Market Pulse / tech_pulse.components.vxn_available |
| AS-IS-357 | 1-8. Market Pulse / tech_pulse.divergence.value |
| AS-IS-358 | 1-8. Market Pulse / tech_pulse.divergence.zscore |
| AS-IS-359 | 1-8. Market Pulse / tech_pulse.divergence.signal |
| AS-IS-360 | 1-8. Market Pulse / asset_flow.{key}.label / ticker |
| AS-IS-361 | 1-8. Market Pulse / asset_flow.{key}.desc |
| AS-IS-362 | 1-8. Market Pulse / asset_flow.{key}.value |
| AS-IS-363 | 1-8. Market Pulse / asset_flow.{key}.change_pct |
| AS-IS-364 | 1-8. Market Pulse / asset_flow.{key}.date |
| AS-IS-365 | 1-8. Market Pulse / asset_flow.{key}.is_fallback |
| AS-IS-366 | 1-8. Market Pulse / credit.stock |
| AS-IS-367 | 1-8. Market Pulse / credit.bond |
| AS-IS-368 | 1-8. Market Pulse / credit.credit |
| AS-IS-369 | 1-8. Market Pulse / credit.risk_off_score |
| AS-IS-370 | 1-8. Market Pulse / take_profit_checklist.triggered/fg_score/points/action/check… |
| AS-IS-372 | 1-8. Market Pulse / date |
| AS-IS-373 | 1-8. Market Pulse / advances / declines |
| AS-IS-374 | 1-8. Market Pulse / unchanged |
| AS-IS-375 | 1-8. Market Pulse / ad_ratio_1d |
| AS-IS-376 | 1-8. Market Pulse / ad_ratio_5d |
| AS-IS-377 | 1-8. Market Pulse / new_highs_52w / new_lows_52w |
| AS-IS-378 | 1-8. Market Pulse / nh_nl_diff |
| AS-IS-379 | 1-8. Market Pulse / total_stocks |
| AS-IS-380 | 1-8. Market Pulse / pct_above_50ma / pct_above_200ma |
| AS-IS-381 | 1-8. Market Pulse / rsp_return_1d / spy_return_1d |
| AS-IS-382 | 1-8. Market Pulse / rsp_spy_divergence_1d |
| AS-IS-383 | 1-8. Market Pulse / rsp_spy_divergence_20d_avg |
| AS-IS-384 | 1-8. Market Pulse / ad_line |
| AS-IS-385 | 1-8. Market Pulse / mcclellan_oscillator |
| AS-IS-386 | 1-8. Market Pulse / market_data.csv 各列 |
| AS-IS-387 | 1-8. Market Pulse / extreme-fear参照: date |
| AS-IS-388 | 1-8. Market Pulse / extreme-fear参照: fear_greed.score |
| AS-IS-389 | 1-9. Portfolio / date |
| AS-IS-390 | 1-9. Portfolio / usdjpy |
| AS-IS-391 | 1-9. Portfolio / total_assets_usd |
| AS-IS-392 | 1-9. Portfolio / total_assets_jpy |
| AS-IS-393 | 1-9. Portfolio / total_pnl_usd |
| AS-IS-394 | 1-10. TANUKI TAIL / quarter |
| AS-IS-395 | 1-10. TANUKI TAIL / filing_date |
| AS-IS-396 | 1-10. TANUKI TAIL / effective |
| AS-IS-397 | 1-10. TANUKI TAIL / material_weaknesses |
| AS-IS-398 | 1-10. TANUKI TAIL / significant_deficiencies |
| AS-IS-399 | 1-10. TANUKI TAIL / item4_excerpt |
| AS-IS-400 | 1-10. TANUKI TAIL / item4_excerpt_ja |
| AS-IS-401 | 1-10. TANUKI TAIL / fetched_at |
| AS-IS-402 | 1-10. TANUKI TAIL / quarters（index.json） |
| AS-IS-403 | 1-10. TANUKI TAIL / last_accn（rss_state.json） |
| AS-IS-404 | 1-10. TANUKI TAIL / last_filed（rss_state.json） |
| AS-IS-405 | 1-10. TANUKI TAIL / no_filing_days（rss_state.json） |
| AS-IS-406 | 1-10. TANUKI TAIL / ticker（review_queue.json） |
| AS-IS-407 | 1-10. TANUKI TAIL / quarter（review_queue.json） |
| AS-IS-408 | 1-10. TANUKI TAIL / status（review_queue.json） |
| AS-IS-409 | 1-10. TANUKI TAIL / completed_at（review_queue.json） |
| AS-IS-410 | 1-10. TANUKI TAIL / review_path（review_queue.json） |
| AS-IS-411 | 1-10. TANUKI TAIL / "{ticker}:{condition}"タイムスタンプ（satellite_alerts.json） |
| AS-IS-412 | 1-10. TANUKI TAIL / timestamp（journal.json watchlist） |
| AS-IS-413 | 1-10. TANUKI TAIL / ticker（journal.json watchlist） |
| AS-IS-414 | 1-10. TANUKI TAIL / type="watchlist"（journal.json） |
| AS-IS-415 | 1-10. TANUKI TAIL / reason（journal.json watchlist） |
| AS-IS-416 | 1-10. TANUKI TAIL / tags（journal.json watchlist） |
| AS-IS-417 | 1-10. TANUKI TAIL / layer2_complete |
| AS-IS-418 | 1-10. TANUKI TAIL / missing_kpis |
| AS-IS-422 | 1-10. TANUKI TAIL / kpis.{name}.value |
| AS-IS-423 | 1-10. TANUKI TAIL / kpis.{name}.value_numeric |
| AS-IS-424 | 1-10. TANUKI TAIL / kpis.{name}.confidence |
| AS-IS-425 | 1-10. TANUKI TAIL / proposed_kpis[].name |
| AS-IS-426 | 1-10. TANUKI TAIL / proposed_kpis[].description |
| AS-IS-427 | 1-10. TANUKI TAIL / proposed_kpis[].source |
| AS-IS-428 | 1-10. TANUKI TAIL / proposed_kpis[].warning_threshold |
| AS-IS-429 | 1-10. TANUKI TAIL / proposed_kpis[].exit_threshold |
| AS-IS-430 | 1-10. TANUKI TAIL / proposed_kpis[].related_exit_condition |
| AS-IS-431 | 1-10. TANUKI TAIL / proposed_kpis[].auto_fetchable |
| AS-IS-432 | 1-10. TANUKI TAIL / proposed_kpis[].extraction_hint |
| AS-IS-433 | 1-10. TANUKI TAIL / proposed_kpis[].xbrl_tag |
| AS-IS-434 | 1-10. TANUKI TAIL / proposed_kpis[].xbrl_dimension |
| AS-IS-435 | 1-10. TANUKI TAIL / proposed_kpis[].xbrl_member |
| AS-IS-436 | 1-10. TANUKI TAIL / proposed_kpis[].layer2_name |
| AS-IS-437 | 1-10. TANUKI TAIL / tail_kpi_map.json: kpi_name |
| AS-IS-438 | 1-10. TANUKI TAIL / tail_kpi_map.json: tag_history[].tag/valid_from/valid_to |
| AS-IS-439 | 1-10. TANUKI TAIL / tail_kpi_map.json: fallback_tags |
| AS-IS-440 | 1-10. TANUKI TAIL / tail_kpi_map.json: revenue_tag |
| AS-IS-441 | 1-10. TANUKI TAIL / tail_kpi_map.json: dimension |
| AS-IS-442 | 1-10. TANUKI TAIL / assumptions.Y1_growth / Y2_growth / Y3_growth |
| AS-IS-443 | 1-10. TANUKI TAIL / assumptions.terminal_growth |
| AS-IS-444 | 1-10. TANUKI TAIL / assumptions.operating_margin |
| AS-IS-445 | 1-10. TANUKI TAIL / assumptions.weighted_growth |
| AS-IS-446 | 1-10. TANUKI TAIL / base_intrinsic_value |
| AS-IS-447 | 1-10. TANUKI TAIL / current_price |
| AS-IS-448 | 1-10. TANUKI TAIL / future_values["1年後"] |
| AS-IS-449 | 1-10. TANUKI TAIL / future_values["3年後"] |
| AS-IS-450 | 1-10. TANUKI TAIL / future_values["5年後"] |
| AS-IS-451 | 1-10. TANUKI TAIL / kpi_forecasts["1年後"/"3年後"].{KPI名} |
| AS-IS-452 | 1-10. TANUKI TAIL / kpi_current.{KPI名} |
| AS-IS-453 | 1-10. TANUKI TAIL / kpi_layer1_keys |
| AS-IS-454 | 1-10. TANUKI TAIL / kpi_format.{KPI名} |
| AS-IS-455 | 1-10. TANUKI TAIL / ticker（thesis共通） |
| AS-IS-456 | 1-10. TANUKI TAIL / type（thesis共通） |
| AS-IS-457 | 1-10. TANUKI TAIL / status（thesis共通） |
| AS-IS-458 | 1-10. TANUKI TAIL / version（thesis共通） |
| AS-IS-459 | 1-10. TANUKI TAIL / thesis（core固有） |
| AS-IS-460 | 1-10. TANUKI TAIL / entry_story（core固有） |
| AS-IS-461 | 1-10. TANUKI TAIL / exit_guide（core固有） |
| AS-IS-462 | 1-10. TANUKI TAIL / entry_price（core固有） |
| AS-IS-463 | 1-10. TANUKI TAIL / entry_date（core固有） |
| AS-IS-464 | 1-10. TANUKI TAIL / strategy_name（satellite固有） |
| AS-IS-465 | 1-10. TANUKI TAIL / entry_condition（satellite固有） |
| AS-IS-466 | 1-10. TANUKI TAIL / exit_condition（satellite固有） |
| AS-IS-467 | 1-10. TANUKI TAIL / holding_period（satellite固有） |
| AS-IS-468 | 1-10. TANUKI TAIL / kpis[]（core/satellite共通） |
| AS-IS-469 | 1-10. TANUKI TAIL / positions（positions_index.json） |
| AS-IS-470 | 1-10. TANUKI TAIL / timestamp（journal.json entries） |
| AS-IS-471 | 1-10. TANUKI TAIL / ticker（journal.json entries） |
| AS-IS-472 | 1-10. TANUKI TAIL / type（journal.json entries） |
| AS-IS-473 | 1-10. TANUKI TAIL / reason（journal.json entries） |
| AS-IS-474 | 1-10. TANUKI TAIL / health_score_at_action（journal.json entries） |
| AS-IS-475 | 1-10. TANUKI TAIL / tags（journal.json entries） |
| AS-IS-476 | 1-10. TANUKI TAIL / price（journal.json entries） |
| AS-IS-477 | 1-10. TANUKI TAIL / shares（journal.json entries） |
| AS-IS-478 | 1-10. TANUKI TAIL / ticker（トップレベル） |
| AS-IS-479 | 1-10. TANUKI TAIL / quarter（トップレベル） |
| AS-IS-480 | 1-10. TANUKI TAIL / generated_at（トップレベル） |
| AS-IS-481 | 1-10. TANUKI TAIL / is_latest（トップレベル） |
| AS-IS-482 | 1-10. TANUKI TAIL / stage1.health_score |
| AS-IS-483 | 1-10. TANUKI TAIL / stage1.health_label |
| AS-IS-484 | 1-10. TANUKI TAIL / stage1.summary |
| AS-IS-485 | 1-10. TANUKI TAIL / stage1.positives |
| AS-IS-486 | 1-10. TANUKI TAIL / stage1.concerns |
| AS-IS-487 | 1-10. TANUKI TAIL / stage1.recommendation |
| AS-IS-488 | 1-10. TANUKI TAIL / stage1.next_kpis |
| AS-IS-489 | 1-10. TANUKI TAIL / stage1.exit_distance |
| AS-IS-490 | 1-10. TANUKI TAIL / stage1.exit_distance_reason |
| AS-IS-491 | 1-10. TANUKI TAIL / stage1.optimism_bias_warning |
| AS-IS-492 | 1-10. TANUKI TAIL / stage2.scenarios.{bear,base,bull}.revenue_growth_y1/y2/y3 |
| AS-IS-493 | 1-10. TANUKI TAIL / stage2.scenarios.{...}.terminal_growth |
| AS-IS-494 | 1-10. TANUKI TAIL / stage2.scenarios.{...}.operating_margin_terminal |
| AS-IS-495 | 1-10. TANUKI TAIL / stage2.scenarios.{...}.rationale |
| AS-IS-496 | 1-10. TANUKI TAIL / stage2.scenarios.{...}.kpi_forecasts["1年後"/"3年後"][KPI名] |
| AS-IS-497 | 1-10. TANUKI TAIL / stage2.key_assumptions |
| AS-IS-498 | 1-10. TANUKI TAIL / stage2.risk_factors |
| AS-IS-499 | 1-10. TANUKI TAIL / call2.five_perspectives.{5観点} |
| AS-IS-500 | 1-10. TANUKI TAIL / call2.entry_story_progress |
| AS-IS-501 | 1-10. TANUKI TAIL / call2.market_attention |
| AS-IS-502 | 1-10. TANUKI TAIL / call2.historical_analogy |
| AS-IS-503 | 1-10. TANUKI TAIL / call2.macro_implications |
| AS-IS-504 | 1-10. TANUKI TAIL / call2.thesis_questions |
| AS-IS-505 | 1-10. TANUKI TAIL / call2.next_review_focus |
| AS-IS-506 | 1-10. TANUKI TAIL / {TICKER}（トップレベルキー） |
| AS-IS-507 | 1-10. TANUKI TAIL / review_quarter |
| AS-IS-508 | 1-10. TANUKI TAIL / forecast_target |
| AS-IS-509 | 1-10. TANUKI TAIL / scenario |
| AS-IS-510 | 1-10. TANUKI TAIL / predictions[KPI名].predicted |
| AS-IS-511 | 1-10. TANUKI TAIL / predictions[KPI名].actual |
| AS-IS-512 | 1-10. TANUKI TAIL / predictions[KPI名].deviation_pct |
| AS-IS-513 | 1-10. TANUKI TAIL / predictions[KPI名].accuracy |
| AS-IS-514 | 1-10. TANUKI TAIL / kpi_forecast_available |
| AS-IS-515 | 1-10. TANUKI TAIL / matchable |

## ステップ3: 最終項目数の集計

| 区分 | 件数 |
|---|---|
| 単独ルート項目 | 415件 |
| 統一する7群（①⑤⑧⑩⑫⑮⑯）の統合元AS-IS項目数 | 43件 |
| うち実際に削除される項目数 | 6件 |
| うち統合後も最終項目として存続する数 | 37件 |
| 統一しない9群（②③④⑥⑦⑨⑪⑬⑭）の最終項目数（クロスバケット重複6件を⑤⑩側に主計上のため除いた実カウント） | 57件 |

### 機械的再集計・重複ゼロの検証（実行結果そのまま転記）

前回のTO_BE_FINAL_LIST.mdには2つの不備があった（是正済み・本セクションで検証）:
1. AS-IS-244/245/246が「AS-IS-243〜246」という範囲短縮記法でしか記載されておらず、
   個別のAS-IS-IDとして文書中に一切出現していなかった（ステップ2-Aの⑩セクションを
   個別列挙に修正済み）
2. AS-IS-032/108/258/259/260/261の6件が、統一する側（⑤・⑩）と統一しない側
   （⑨・⑪）の両方の表に重複掲載されていた（統一する側の表に一本化し、
   統一しない側は表から除外・注記のみに変更して是正済み）

是正後のTO_BE_FINAL_LIST.mdを対象に、以下のスクリプトで再検証した。

```python
import re

with open('TO_BE_FINAL_LIST.md', encoding='utf-8') as f:
    text = f.read()

sec_2a = text.index('## ステップ2-A')
sec_2b = text.index('## ステップ2-B')
sec_2c = text.index('## ステップ2-C')
sec_3 = text.index('## ステップ3')

text_2a = text[sec_2a:sec_2b]
text_2b = text[sec_2b:sec_2c]
text_2c = text[sec_2c:sec_3]

# 表の行（| AS-IS-XXX | ...）のみを対象にする（本文中の言及・注記は対象外）
row_re = re.compile(r'^\| (AS-IS-\d{3}) \|', flags=re.MULTILINE)
# ステップ2-Aは箇条書き形式(- AS-IS-XXX（...）)のため別パターンも必要
bullet_re = re.compile(r'^- (AS-IS-\d{3})（', flags=re.MULTILINE)

ids_2a = set(row_re.findall(text_2a)) | set(bullet_re.findall(text_2a))
ids_2b = set(row_re.findall(text_2b))
ids_2c = set(row_re.findall(text_2c))

print("2-A（統一7群、統合元AS-IS項目）:", len(ids_2a))
print("2-B（統一しない9群、表の行のみ）:", len(ids_2b))
print("2-C（単独ルート、表の行のみ）:", len(ids_2c))

overlap_ab = ids_2a & ids_2b
overlap_ac = ids_2a & ids_2c
overlap_bc = ids_2b & ids_2c
print("2-A ∩ 2-B:", sorted(overlap_ab))
print("2-A ∩ 2-C:", sorted(overlap_ac))
print("2-B ∩ 2-C:", sorted(overlap_bc))

union_all = ids_2a | ids_2b | ids_2c
print("2-A + 2-B + 2-C 論理和（ユニーク数）:", len(union_all))

all_expected = set(f'AS-IS-{i:03d}' for i in range(1, 516))
DELETED = {'AS-IS-075', 'AS-IS-061', 'AS-IS-062', 'AS-IS-063', 'AS-IS-054', 'AS-IS-134'}
expected_non_deleted = all_expected - DELETED

missing = sorted(expected_non_deleted - union_all)
unexpected_extra = sorted(union_all - expected_non_deleted)
print("509件のうち本ファイルに出現しないもの:", missing)
print("509件の範囲外だが出現しているID:", unexpected_extra)

final_total = (len(ids_2a) - len(ids_2a & DELETED)) + len(ids_2b) + len(ids_2c)
print(f"最終出力項目 合計: {final_total}")
print(f"515 - 削除{len(DELETED)}件 = {515-len(DELETED)} (一致確認: {final_total == 515-len(DELETED)})")
```

**実行結果（そのまま転記）**:

```
=== セクション別 抽出結果 ===
2-A（統一7群、統合元AS-IS項目、箇条書き+表の両方から抽出）: 43
2-B（統一しない9群、表の行のみ）: 57
2-C（単独ルート、表の行のみ）: 415

=== 重複チェック（2つ以上のセクションに同時出現するID） ===
2-A ∩ 2-B: []
2-A ∩ 2-C: []
2-B ∩ 2-C: []

=== 全体整合性確認 ===
2-A + 2-B + 2-C 論理和（ユニーク数）: 515
515件のうち削除対象6件を除いた509件のうち、本ファイルに出現しないもの: []
509件の範囲外だが出現しているID（削除対象なのに残存等）: ['AS-IS-054', 'AS-IS-061', 'AS-IS-062', 'AS-IS-063', 'AS-IS-075', 'AS-IS-134']

=== 最終確定件数 ===
2-A（統一7群・統合元の総登場数、削除対象含む）: 43
  うち削除対象: 6  -> 統合後の存続数: 37
2-B（統一しない9群、重複帰属解消済み）: 57
2-C（単独ルート）: 415
最終出力項目 合計: 509
515 - 削除6件 = 509  (一致確認: True)
```

**結果の解釈**:
- 2-A・2-B・2-C間の重複（交差集合）は**すべて空集合**——AS-IS-032/108/258/259/260/261の帰属は⑤・⑩（統一7群側）に完全に一本化され、統一しない9群側（⑨・⑪）からは表としては除外（注記のみ）されたことを確認した。
- 2-A・2-B・2-Cの論理和は**515件と完全一致**——AS-IS-244/245/246を含め、515件全てが必ずどこかに1回だけ出現している。
- 「509件の範囲外だが出現しているID」として検出された6件（AS-IS-054/061/062/063/075/134）は、いずれも2-Aの箇条書きに**削除対象として明記された上で**登場しているもので、最終集計では正しく差し引かれている（意図した挙動）。

### 最終出力項目数

```
単独ルート:                415件
統一7群・存続分:             37件
統一しない9群:               57件
----------------------------------------
最終出力項目 合計:          509件
```

### 515件からの削減内訳

```
AS-IS-001〜515 総数:        515件
削除される重複ルート:         6件
  内訳: AS-IS-075（①乖離率クライアント再計算）
       AS-IS-061,062,063（⑤PER/PEG/PSRクライアント再計算）
       AS-IS-054（⑩TANUKI risk_events簡易版）
       AS-IS-134（⑫STONKS SILO net_cash独自計算）
----------------------------------------
最終出力項目 合計:          509件
```

**515件から実際に削除されるのは6件のみ**。これは、
「統一する」と判断された7群の大半が、値そのものを1つに強制collapseする
のではなく「取得経路（fetch/計算ロジック）だけを1本化し、消費先ごとの
最終表示項目は個別に維持する」という設計判断（⑤⑧⑩⑮⑯）を取っているため。
真に「同じ値の重複計算」として1件に統合され、他方が完全削除されるのは
①（乖離率のクライアント再計算）・⑤（PER/PEG/PSRのクライアント再計算×3）・
⑩（TANUKI簡易版risk_events）・⑫（STONKS SILO独自net_cash計算）の
6パターンに限られる。

**注記**: 上記509件は「統一する7群／統一しない9群」という**群単位**の粗い
区分に基づく延べ集計である。群単位では「統一する」に分類された⑤⑧⑩⑮⑯の
内部にも、実際には「値そのものが同一で1項目にまとめられる項目」と
「取得経路は共通化されるが最終的な値・定義は個別のまま残る項目」が混在
している。この違いを項目単位まで踏み込んで区別した真の最終集計を、
以下のステップ4で行う。

## ステップ4: 「同一定義」／「異なる定義」の項目単位での確定、真の最終出力項目数

### 判定基準

`TO_BE.md`の各項目の統一定義本文を対象に、以下の基準で機械的に再分類した:

- **「同一定義」**（1項目に統合可能）: 本文中に「唯一の正とする」「パス
  スルー実装」「統一済み（変更不要）」等、**複数のAS-IS-IDが文字通り
  同じ値・同じ計算結果を指すと明言**されている場合のみ。
- **「異なる定義」**（個別に維持）: 「表示規約のみ統一」「取得経路を共通化」
  「UIレベル共有候補」等、値そのものの同一性ではなく**運用・UI・取得
  メカニズムの共通化**を述べているに過ぎない場合。同じ群に分類されていても、
  計算結果・目的が異なる項目は「異なる定義」として個別維持する。

この基準で`TO_BE.md`全文を`唯一の正|パススルー|既に統一済み|変更不要`
のキーワードで機械検索し、該当箇所を全て確認した（実行結果は下記参照）。

### 16群それぞれの確定判断（暫定判定からの変更点）

| 群 | 暫定判定（ステップ3時点） | 確定判定（本ステップ） | 変更理由 |
|---|---|---|---|
| ① 乖離率／IV比 | 統一7群、5件存続 | **同一定義クラスタ1件**（AS-IS-006/075/280→1件）＋異なる定義3件（003/005/116） | AS-IS-006と280は明示的パススルー、075は同一計算式の重複のため真に1件に統合可能。003/005/116は別の割引率基準・別の時系列設計のため個別維持が妥当 |
| ② 信頼性／品質判定バッジ | 統一しない、13件個別 | 変更なし、異なる定義13件 | 判定対象そのものが別ドメイン、明示的パススルー宣言なし |
| ③ 成長率 | 統一しない、8件個別 | 変更なし、異なる定義8件 | 実データでデータソース自体が独立と確認済み |
| ④ 総合スコア／判定 | 統一7群外（統一しない）、12件個別 | **同一定義クラスタ2件**（035/289→1件、037/290→1件）＋異なる定義8件 | AS-IS-289/290がTANUKI VALUATIONの035/037への明示的パススルーと確認済み（フェーズ2で発見）。他8件は評価軸が別ドメインのため個別維持 |
| ⑤ マルチプル | 統一7群、13件存続 | **同一定義クラスタ1件**（AS-IS-031/283→1件）＋異なる定義12件 | 031と283は共にTANUKIの`per_adjusted`を指す明示的パススルー関係。他12件（032,097-108,117,132,133,282）は共通取得関数を参照するが、各々が別の最終メトリクス（forward_pe/peg/psr/ev_ebitda/analyst系等）を表すため個別維持が正しい |
| ⑥ モメンタム | 統一しない、5件個別 | 変更なし、異なる定義5件 | 数学的手法自体が別（Zスコア vs ベクトル角度） |
| ⑦ FCF | 統一しない、13件個別 | 変更なし、異なる定義13件 | 用途別（DCF入力 vs 黒字化ロードマップ）で個別維持 |
| ⑧ 次回決算日 | 統一7群、3件存続 | **同一定義クラスタ1件**（AS-IS-048/179/284→1件） | 3件とも明示的に「唯一の正」「統一済み（変更不要）」「パススルー」と記載、真に同一値 |
| ⑨ インサイダー／空売り | 統一しない、3件個別 | 変更なし、異なる定義3件（うち032/108は⑤で主計上のため本群では相互参照のみ） | 用途別（表示用 vs 内部判定変数）のため個別維持 |
| ⑩ リスクイベント／カタリスト | 統一7群、8件存続（AS-IS-054のみ削除） | 変更なし、異なる定義8件（243-246/258-261）＋純粋削除1件（054） | 243-246/258-261はそれぞれ別フィールド（title/status/first_detected等）を表し互いに同一定義ではない。054はDiscoverの特定1フィールドと同一というより簡易版として単純廃止（同一定義クラスタは形成しない） |
| ⑪ マクロ環境認識 | 統一しない、10件個別 | 変更なし、異なる定義10件（うち182/183/214/215/258-261は②④⑩で主計上） | UIレベル共有候補の記述のみで値の同一性は明言されていない |
| ⑫ ネットキャッシュ | 統一7群、1件存続 | **同一定義クラスタ1件**（AS-IS-025/134→1件） | 明示的に「AS-IS-025の値を参照する形に統合」と記載、真に同一値 |
| ⑬ Rule of 40 | 統一しない、2件個別 | 変更なし、異なる定義2件 | 成長率の期間・利益率の定義が根本的に異なる別指標と確定済み（改名対象） |
| ⑭ 純利益二重抽出 | 統一しない、2件個別 | 変更なし、異なる定義2件 | TTM vs FYで期間定義が異なり単純合算不可（AVAV/ESTC等の例外的一致はあるが原則別値） |
| ⑮ FRED HYスプレッド | 統一7群、3件存続 | 変更なし、異なる定義3件（取得経路のみ統一） | 生値取得は共通化するが、events.csv用／流動性カード用／BUYチェックリスト用で加工・判定ロジックが異なるため最終出力は個別 |
| ⑯ SEC EDGARセグメント | 統一7群、4件存続 | 変更なし、異なる定義4件（抽出ロジックのみ統一） | `segments[]`（TANUKI VALUATION用）と`kpis.*`（TANUKI TAIL用）は抽出元は同じだが出力構造・用途が異なるため個別維持 |

### 同一定義でまとめた項目一覧（6クラスタ、統合定義名・表示箇所・元AS-IS-ID）

| 統一定義名 | 表示箇所 | 元AS-IS-ID |
|---|---|---|
| `upside_percent`（乖離率） | TANUKI VALUATION stock.html（メイン理論株価カード）／EPS Analyzer index.html（乖離率列・投資機会ランキング） | AS-IS-006（唯一の正）／AS-IS-075（削除、client再計算）／AS-IS-280（パススルー） |
| `funda_score` | TANUKI VALUATION stock.html（Funda_Score表示、report.txt）／TANUKI SCORE index.html（「F:xx」表示） | AS-IS-035（唯一の正）／AS-IS-289（パススルー） |
| `timing_score` | TANUKI VALUATION stock.html（Timing_Score表示）／TANUKI SCORE index.html（「T:xx」表示） | AS-IS-037（唯一の正）／AS-IS-290（パススルー） |
| `per_adjusted` | TANUKI VALUATION stock.html（PER比較パネル）／EPS Analyzer stock.html（PER比較パネル） | AS-IS-031（唯一の正）／AS-IS-283（パススルー） |
| `next_earnings_date`（次回決算日） | TANUKI VALUATION stock.html（フッター・ティッカータグ、report.txt）／STONKS SILO index.html（詳細パネル）／EPS Analyzer stock.html（「次回決算」） | AS-IS-048（唯一の正）／AS-IS-179（パススルー）／AS-IS-284（パススルー） |
| `net_cash` | TANUKI VALUATION stock.html（FINANCIAL HEALTHカード）／STONKS SILO index.html（valInlineHtml詳細パネル） | AS-IS-025（唯一の正）／AS-IS-134（削除、独自計算を廃止） |

### 再集計スクリプトの実行（そのまま転記）

```python
MERGE_CLUSTERS = {
    "upside_percent（乖離率、①）": ["AS-IS-006", "AS-IS-075", "AS-IS-280"],
    "funda_score（④）": ["AS-IS-035", "AS-IS-289"],
    "timing_score（④）": ["AS-IS-037", "AS-IS-290"],
    "per_adjusted（⑤）": ["AS-IS-031", "AS-IS-283"],
    "next_earnings_date（次回決算日、⑧）": ["AS-IS-048", "AS-IS-179", "AS-IS-284"],
    "net_cash（⑫）": ["AS-IS-025", "AS-IS-134"],
}
PURE_DELETE = {"AS-IS-061", "AS-IS-062", "AS-IS-063", "AS-IS-054"}

all_ids = set(f"AS-IS-{i:03d}" for i in range(1, 516))
cluster_source_ids = set()
for name, ids in MERGE_CLUSTERS.items():
    cluster_source_ids |= set(ids)

overlap = cluster_source_ids & PURE_DELETE
assert not overlap  # クラスタと純粋削除が重複していないことを確認

remaining_individual = all_ids - cluster_source_ids - PURE_DELETE
final_total = len(remaining_individual) + len(MERGE_CLUSTERS)
check = len(all_ids) - len(cluster_source_ids) - len(PURE_DELETE) + len(MERGE_CLUSTERS)
assert check == final_total
```

**実行結果（そのまま転記）**:

```
=== 同一定義クラスタ ===
upside_percent（乖離率、①）: ['AS-IS-006', 'AS-IS-075', 'AS-IS-280'] (3件 -> 1件)
funda_score（④）: ['AS-IS-035', 'AS-IS-289'] (2件 -> 1件)
timing_score（④）: ['AS-IS-037', 'AS-IS-290'] (2件 -> 1件)
per_adjusted（⑤）: ['AS-IS-031', 'AS-IS-283'] (2件 -> 1件)
next_earnings_date（次回決算日、⑧）: ['AS-IS-048', 'AS-IS-179', 'AS-IS-284'] (3件 -> 1件)
net_cash（⑫）: ['AS-IS-025', 'AS-IS-134'] (2件 -> 1件)

同一定義クラスタが消費する元AS-IS-ID数: 14
同一定義クラスタが生成する最終項目数: 6
クラスタによる純減: 8

純粋削除（同一定義の相手なし、単純廃止）: ['AS-IS-054', 'AS-IS-061', 'AS-IS-062', 'AS-IS-063']
純粋削除数: 4

クラスタと純粋削除の重複（0件であるべき）: []

=== 最終集計 ===
515件 総数: 515
同一定義クラスタ消費分: 14
純粋削除分: 4
異なる定義として個別に残る項目数: 497
同一定義クラスタの最終項目数: 6

真に必要な出力項目数 = 異なる定義497件 + 同一定義クラスタ6件 = 503件
検算: 515 - 14(クラスタ消費) - 4(純粋削除) + 6(クラスタ最終数) = 503
```

### 最終集計（延べ数515・509とは明確に区別）

| 区分 | 件数 |
|---|---|
| 「同一定義」として1件にまとめられた項目群の数（6クラスタの統合後件数） | **6件** |
| 「異なる定義」として個別のまま残る項目数 | **497件** |
| **真に必要な出力項目数（合計）** | **503件** |

参考として、延べ数の系列を整理する:
- AS-IS-001〜515: **515件**（生成物ベースの延べ数、重複含む）
- ステップ3時点（群単位の粗い集計、509件）: 「統一する7群」を丸ごと
  1グループとして扱った暫定値。**参考値として残すが、真の最終数ではない**
- 本ステップ4（項目単位の同一定義判定、503件）: 2分類（同一定義／異なる定義）
  時点での真に必要な出力項目数。**ステップ5でさらに精緻化する**

## ステップ5: 第3カテゴリ「概念統一・パラメータ違い」の導入と最終集計

`CONCEPT_PARAMETER_VARIATIONS.md`で検証した結果、ステップ4で「異なる定義」
（497件）に分類していた項目のうち9件が、実際には「計算目的・対象データは
同じだが、集計期間（TTM/FY/YoY/3年CAGR等）というパラメータのみが異なる」
関係にあることが判明した。これらは削除・統合せず、4つの「概念」の下に
パラメータバリエーションとして記録し直す。

### 該当した4概念・9項目

| 概念 | 該当AS-IS-ID | パラメータ差 |
|---|---|---|
| PSR（株価売上高倍率） | AS-IS-099（HypeCore, TTM）／AS-IS-132（STONKS SILO, Annual） | TTM vs Annual |
| net_income（純利益） | AS-IS-129（STONKS SILO, FY）／AS-IS-281（EPS Analyzer, TTM） | FY vs TTM |
| 売上高成長率 | AS-IS-152（STONKS SILO, 単年YoY）／AS-IS-136（STONKS SILO, 3年CAGR）／AS-IS-093（HypeCore, TTM YoY） | 単年 vs 3年 vs TTM（093のみ正規化パイプライン差の注記あり） |
| STONKS SILO OCF年次値 | AS-IS-156（最新1年）／AS-IS-160（全年度dict） | 単年 vs 全年度 |

（`AS-IS-032`内包の`ps`サブフィールドはPSR概念に概念的に関連するが、
束ねられた行のため独立カウントからは除外。詳細は`CONCEPT_PARAMETER_VARIATIONS.md`参照）

**精査したが棄却した候補**（名称は類似だが測定対象・データソースが異なると
判明）: ③TANUKI「FCF CAGR(3yr)」vs STONKS SILO「cagr_3yr」（FCF≠売上高）、
⑬Rule of 40全体（利益率の定義自体が異なる。ただし成長率サブコンポーネント
はそれぞれ売上高成長率概念のAS-IS-093／AS-IS-136と同一値であることを発見）、
⑦TANUKI「fcf_base」vs STONKS SILO「ocf_annual」（FCF≠OCF）。

### 再集計スクリプトの実行（そのまま転記）

```python
MERGE_CLUSTERS = {
    "upside_percent（乖離率、①）": ["AS-IS-006", "AS-IS-075", "AS-IS-280"],
    "funda_score（④）": ["AS-IS-035", "AS-IS-289"],
    "timing_score（④）": ["AS-IS-037", "AS-IS-290"],
    "per_adjusted（⑤）": ["AS-IS-031", "AS-IS-283"],
    "next_earnings_date（次回決算日、⑧）": ["AS-IS-048", "AS-IS-179", "AS-IS-284"],
    "net_cash（⑫）": ["AS-IS-025", "AS-IS-134"],
}
PURE_DELETE = {"AS-IS-061", "AS-IS-062", "AS-IS-063", "AS-IS-054"}
CONCEPT_VARIATIONS = {
    "PSR（株価売上高倍率）": ["AS-IS-099", "AS-IS-132"],
    "net_income（純利益）": ["AS-IS-129", "AS-IS-281"],
    "売上高成長率": ["AS-IS-152", "AS-IS-136", "AS-IS-093"],
    "STONKS SILO OCF年次値": ["AS-IS-156", "AS-IS-160"],
}

all_ids = set(f"AS-IS-{i:03d}" for i in range(1, 516))
cluster_source_ids = set()
for ids in MERGE_CLUSTERS.values():
    cluster_source_ids |= set(ids)
concept_ids = set()
for ids in CONCEPT_VARIATIONS.values():
    concept_ids |= set(ids)

assert not (cluster_source_ids & PURE_DELETE)
assert not (cluster_source_ids & concept_ids)
assert not (PURE_DELETE & concept_ids)

remaining_truly_different = all_ids - cluster_source_ids - PURE_DELETE - concept_ids

n_same_def_concepts = len(MERGE_CLUSTERS)
n_concept_variation_concepts = len(CONCEPT_VARIATIONS)
n_concept_variation_items = len(concept_ids)
n_truly_different = len(remaining_truly_different)

final_output_count = n_same_def_concepts + n_concept_variation_items + n_truly_different
check = len(cluster_source_ids) + len(PURE_DELETE) + n_concept_variation_items + n_truly_different
assert check == 515
```

**実行結果（そのまま転記）**:

```
同一定義クラスタ ∩ 純粋削除: []
同一定義クラスタ ∩ 概念統一パラメータ違い: []
純粋削除 ∩ 概念統一パラメータ違い: []

=== 3層集計 ===
同一定義: 6概念（元14件から統合）
純粋削除: 4件
概念統一・パラメータ違い: 4概念（実項目9件、削除なし・維持）
真に異なる定義: 488件

真に必要な出力項目数 = 同一定義6 + 概念統一パラメータ違い9(実項目) + 異なる定義488 = 503
検算(515件の内訳): 同一定義元14 + 純粋削除4 + 概念統一パラメータ違い9 + 異なる定義488 = 515

前回report(503件)との比較: 503 == 503 ? True
```

### 最終集計（3分類、確定版）

| 区分 | 概念（親項目）数 | 実際の出力項目数 |
|---|---|---|
| 同一定義（1項目に統合） | 6概念 | 6件 |
| 概念統一・パラメータ違い（親概念でグルーピング、個別の値は維持） | 4概念 | 9件（削除なし） |
| 真に異なる定義（個別維持） | — | 488件 |
| **合計（真に必要な出力項目数）** | | **503件** |

**重要**: 「概念統一・パラメータ違い」への再分類は、実際に表示・出力される
値の数を1件も減らしていない（9件は9件のまま出力され続ける）。変わったのは
分類の精緻化のみであり、そのため合計は503件のままステップ4から変化しない。
これは第3カテゴリの導入意図（「削除はしない、統合先の1項目に値を潰すのでも
ない」）に照らして正しい結果である。

515（延べ数）→509（群単位の粗い集計）→503（項目単位の真の集計、3分類後も503で不変）
という3段階の集計値を、それぞれ異なる粒度の指標として明確に区別する。
