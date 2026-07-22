# TO_BE.md — 全サブシステム出力項目 あるべき姿の設計

作成日: 2026-07-22
出発点: `OUTPUT_ITEMS_INVENTORY.md`（2026-07-22時点のAS-ISスナップショット、全284項目にAS-IS-001〜284のIDを付番済み）

## 本ドキュメントの位置づけ

AS-IS全284項目を、(a) 11共通項目群（①〜⑪）のいずれかに該当する項目、
(b) 単独ルートで重複のない項目、の2種類に機械的に分類し、(a)については
統一定義・唯一の正とする計算ルート・削除対象ルートを設計する。(b)は
「変更なし」として一括記録する。全284件のAS-IS-IDが本ドキュメントの
どこかに一度は言及されていることを、末尾の「機械的網羅性証明」で
diffにより証明する。

実装（コード修正）は行っていない。設計提案と現状検証の記録のみ。

## 分類方法（機械的ルール）

各AS-IS項目の「項目名」セル（テーブルの第1列）に対し、11群それぞれの
キーワード正規表現をマッチングし、該当した群のうち最小番号を「主群」、
それ以外を「重複候補（副群）」として記録した。項目名セルのみを対象と
することで、計算ルート列に別項目名が入力として言及されているケース
（例:「PEGレシオ」の計算式が`growth_scenarios.primary.rate`を入力に
使う等）による誤マッチを排除している。1件のみ、テーブル構造上
項目名列に識別子が入らない副表（ERP 2ルート比較表）について、
手動での対応付けを行った（後述、AS-IS-055/056）。

分類スクリプトは本セッションのスクラッチパッドに保存済み
（`classify_groups.py`）。

## ① 乖離率／IV比 系

### 統一定義
TANUKI VALUATIONの`upside_percent`（AS-IS-006）を唯一の正とする。
計算式: `((intrinsic_value_per_share / current_price) - 1) * 100`
（`calculator/adjustments.py:662-669`、Rmβなし本体DCF基準）。
データソース: `docs/value-monitor/tanuki_valuation/data/{TICKER}/latest.json`。
更新頻度: TANUKI VALUATIONの日次バッチ実行時。

実データ突合（AAPL/MSFT/AMZN/META/TSLA/GOOGL/NVDA、7銘柄）により、
HypeCore・EPS Analyzer側の値との差分は計算式のバグではなく取得タイミングの
非同期性（HypeCore生成日時が最大3日古い）に起因することを確認済み
（詳細は`OUTPUT_ITEMS_INVENTORY.md`のステップ2〜4セクション参照）。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-003 | 5-1. TANUKI VALUATION | upside_percent_beta | 維持（TANUKI内部の参考値。β込みWACC基準。他システム参照なし、削除対象外） |
| AS-IS-005 | 5-1. TANUKI VALUATION | upside_percent_rf | 維持（TANUKI内部の参考値。Rf基準。他システム参照なし、削除対象外） |
| AS-IS-006 | 5-1. TANUKI VALUATION | upside_percent | **唯一の正とする**。TANUKI `upside_percent`（Rmβなし本体DCF基準）。他システムはこの値を直接参照する。 |
| AS-IS-075 | 5-1. TANUKI VALUATION | 乖離率 | **削除対象**。index.htmlのクライアント側再計算 `(ivps-price)/price` を廃止し、AS-IS-006のJSON値を直接参照するよう変更する。 |
| AS-IS-116 | 5-2. HypeCore | `price_iv_ratio` | **部分維持・部分変更**。月次時系列トレンド分析という別目的のためHypeCore独自計算の枠組みは維持してよいが、「最新月」の値のみAS-IS-006由来の`current_price`/`upside_percent`で上書きし、株価取得タイミングのズレ（実データでNVDA最大6.5pt差を確認済み）を解消する。 |
| AS-IS-280 | 5-6. EPS Analyzer | `deviation_rate` | 変更不要。既にAS-IS-006をライブfetchするパススルー実装であり、TO-BEの参照実装として適切。 |

## ② 信頼性／品質判定バッジ系

### 統一定義（統一しない判断）
**フィールドの統合はしない**。DCF計算精度（TANUKI: AS-IS-020 fcf_outlier,
AS-IS-042 growth_sanity, AS-IS-052 validation.*）・企業財務品質
（STONKS SILO: AS-IS-141/158 verdict, AS-IS-149 dilution_risk,
AS-IS-150 deficit_fixed_risk, AS-IS-161 ocf_trend）・マクロ環境
（MACRO PULSE: AS-IS-182/183 regime, AS-IS-205/206/209 stealth系）は
判定対象が完全に別レイヤーであり、単一フィールドへの統合は「マクロが
TIGHTENINGだから個別銘柄のDCF計算精度もLOW」のような誤った連想を
利用者に与えるため不適切と判断する。

**統一するのは表示規約のみ**: 各ドメイン固有ラベル・段階数は維持したまま、
共通の重大度スケール（GREEN=問題なし／AMBER=要注意／RED=懸念）へのマッピング表
を新設し、UI側の色・アイコン表現のみ共通コンポーネント化する
（マッピング表の詳細は`OUTPUT_ITEMS_INVENTORY.md`ステップ2〜4「②信頼性／品質判定バッジ系」参照）。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-020 | 5-1. TANUKI VALUATION | fcf_outlier.detected/rule/action/note/deviation_pct | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-042 | 5-1. TANUKI VALUATION | growth_sanity.verdict/signals/warnings/recommended_g | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-052 | 5-1. TANUKI VALUATION | validation.* | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-141 | 5-3. STONKS SILO | `verdict` | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-149 | 5-3. STONKS SILO | `dilution_risk` | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-150 | 5-3. STONKS SILO | `deficit_fixed_risk` | 統一しない（フィールドは維持）。ただし`_calc_deficit_fixed_risk`のPROFITABLE誤判定（常にMEDIUM表示）を先に修正しないと共通スケール導入の前提が崩れる。修正は本依頼の範囲外、別途実装依頼が必要。 |
| AS-IS-158 | 5-3. STONKS SILO | `verdict` | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-161 | 5-3. STONKS SILO | `ocf_trend` | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-182 | 5-4. MACRO PULSE | REGIME | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-183 | 5-4. MACRO PULSE | regime_source | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-205 | 5-4. MACRO PULSE | ステルス流動性 LAYER1（FRB政策意図） | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-206 | 5-4. MACRO PULSE | LAYER2（ステルス供給/吸収バッジ） | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |
| AS-IS-209 | 5-4. MACRO PULSE | ステルス吸収週数(stealth_absorb_weeks) | 統一しない（フィールドは維持）。表示規約（重大度スケール）のみRED/AMBER/GREENに統一する候補。 |

## ③ 成長率系

### 統一定義（統一しない判断・ステップ3実データ確認により確定）
**統一しない（確定）**。ステップ3で実コードを確認した結果:

- TANUKI `growth.rate`（AS-IS-012）: `calculator/growth.py:determine_growth_rate()`。
  優先順位＝①セグメント加重成長率（`segment_config.py`）→②FCF CAGR
  （SEC由来のFCF実績から算出）→③デフォルト値。**yfinanceの`revenueGrowth`
  フィールドは一切参照しない**（`growth.py`全文でヒット0件を確認）。
- HypeCore `revenue_growth`（AS-IS-100）: `hypecore.py:120`
  `info.get("revenueGrowth")`。yfinanceの`.info`辞書由来の単一スカラー値
  （直近実績YoY）。

両者は**同一yfinance APIコール・同一フィールドを一切参照しておらず**、
データソース（SEC由来の将来DCF予測入力 vs yfinance報告済み直近実績）も
計算目的も完全に独立していることが確認された。当初（ステップ2〜4）の
簡易判断「統一不可」が実データ・実コード確認で裏付けられた。

STONKS SILOの`cagr_3yr`（AS-IS-136）・`revenue_growth_pct`
（AS-IS-152/079）はSEC年次データ（`common/sec_data`）由来のため、
TANUKIのFCF CAGR経路とデータソースの根っこ（SEC annual data）は
部分的に重なりうるが、期間・計算式（3年CAGR vs FCFベース）が異なるため
統合対象外とする。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-012 | 5-1. TANUKI VALUATION | growth.rate/source | 統一しない（確定） |
| AS-IS-042 | 5-1. TANUKI VALUATION | growth_sanity.verdict/signals/warnings/recommended_g | 統一しない（確定） |
| AS-IS-043 | 5-1. TANUKI VALUATION | phase1_growth_auto_adjusted | 統一しない（確定） |
| AS-IS-079 | 5-2. HypeCore | STONKS SILO `deficit_quality.revenue_growth_pct` | 統一しない（確定） |
| AS-IS-093 | 5-2. HypeCore | `rev_yoy` | 統一しない（確定） |
| AS-IS-100 | 5-2. HypeCore | `revenue_growth` | 統一しない（確定） |
| AS-IS-136 | 5-3. STONKS SILO | `cagr_3yr` | 統一しない（確定） |
| AS-IS-152 | 5-3. STONKS SILO | `revenue_growth_pct` | 統一しない（確定） |

## ④ 総合スコア／判定系

### 統一定義（統一しない判断）
**統一しない**。DCF妥当性（TANUKI: AS-IS-034/035/037/041）・ハイプ段階
（HypeCore: AS-IS-085 stage）・赤字品質（STONKS SILO: AS-IS-126/127）・
マクロリスク（MACRO PULSE: AS-IS-214/215）・EPS調整健全性
（EPS Analyzer: AS-IS-279 health）は評価軸が完全に別ドメインであり
統合は不適切。表示スケール（0-100点または5段階）の色分け規約のみ、
②のRED/AMBER/GREENマッピングと合わせて統一する価値がある。

AS-IS-214/215（RECESSION RISK SCORE表示）は⑪マクロ環境認識系とも
重複候補（同一の数値を扱う）。フィールド統合はしないが、UI上は
1つの「RECESSION RISK SCOREウィジェット」を複数箇所（フェーズゲージ・
マクロ環境ダッシュボード）から参照する設計にできる。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-034 | 5-1. TANUKI VALUATION | tanuki_score | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |
| AS-IS-035 | 5-1. TANUKI VALUATION | funda_score | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |
| AS-IS-037 | 5-1. TANUKI VALUATION | timing_score | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |
| AS-IS-041 | 5-1. TANUKI VALUATION | matrix.*（quadrant/label/key_metric_y/qx/qy） | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |
| AS-IS-085 | 5-2. HypeCore | `stage` | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |
| AS-IS-126 | 5-3. STONKS SILO | `overall_score` | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |
| AS-IS-127 | 5-3. STONKS SILO | `overall_verdict` | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |
| AS-IS-214 | 5-4. MACRO PULSE | RECESSION RISK SCOREバー・マーカー | 統一しない。⑪（マクロ環境認識）とのUIレベル共有候補（同じRECESSION RISK SCOREウィジェットを複数箇所から参照する設計は可能）。 |
| AS-IS-215 | 5-4. MACRO PULSE | RECESSION RISK SCORE数値 | 統一しない。⑪とのUIレベル共有候補（同上）。 |
| AS-IS-279 | 5-6. EPS Analyzer | `health` | 統一しない（フィールドは維持）。表示スケール（0-100点/5段階の色分け規約）のみ②と合わせて統一候補。 |

## ⑤ アナリストコンセンサス／マルチプル系（PER/PEG/PSR/EV_EBITDA）

### 統一定義
`common/valuation/`配下に1箇所の取得関数を新設し、以下のフィールドを
返す: `{ticker, as_of, trailing_pe, forward_pe, peg_ratio, psr_ttm,
ev_ebitda_ttm(+is_validフラグ), market_cap, enterprise_value,
forward_eps, trailing_eps, data_quality_flags}`。
TANUKI VALUATION・HypeCoreはこの統一関数を共通利用する。

実データ突合（ASTS/AVAV/BBAI/IONQ/IOT/RKLB/RXRX/SOUN、8銘柄）で、
黒字銘柄AVAVはほぼ完全一致（差はデータ取得日3日ズレのみ）した一方、
IONQのPSRはTTM基準(69-71) vs Annual基準(124.5)で約1.75倍、
IOTのEV/EBITDAはHypeCoreで-16713.74倍の異常値、という具体的な
不一致・欠陥を確認済み（`OUTPUT_ITEMS_INVENTORY.md`ステップ2〜4参照）。

STONKS SILOのPSR/EV_Salesは対象がプレレベニュー・低収益企業向けの
意図的なAnnual基準設計のため統一対象外とし、「TTM基準」「Annual基準」
を明示的に併記する形で存置する。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-031 | 5-1. TANUKI VALUATION | per_adjusted | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-032 | 5-1. TANUKI VALUATION | per, peg, ps, ev_ebitda, ma200, forward_eps, analyst_target_*, dividen… | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-061 | 5-1. TANUKI VALUATION | フェアPER | 削除対象。stock.htmlのクライアント側独自フェアPER計算（同種の重複実装、実データ未検証だが同じ問題パターン）。 |
| AS-IS-062 | 5-1. TANUKI VALUATION | PEGレシオ | **削除対象**。stock.htmlのクライアント側独自PEG再計算。実データ（AAPL）でJSON値2.69に対しクライアント再計算値≈4.92と約1.8倍の乖離を確認済み。JSON値（AS-IS-031 per_adjusted由来）を直接表示するよう変更する。 |
| AS-IS-063 | 5-1. TANUKI VALUATION | PSR | **削除対象**。stock.htmlのクライアント側独自PSR再計算。実データでJSON値10.70に対しクライアント再計算値≈11.61と約8.5%の乖離を確認済み。 |
| AS-IS-097 | 5-2. HypeCore | `forward_pe` | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-098 | 5-2. HypeCore | `peg_ratio` | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-099 | 5-2. HypeCore | `psr` | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-102 | 5-2. HypeCore | `recommendation_mean` | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-105 | 5-2. HypeCore | `analyst_upgrade_rate` | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-108 | 5-2. HypeCore | `buy_hold_ratio` | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-117 | 5-2. HypeCore | `ev_ebitda` | **修正対象**（削除ではなく正値フィルタの追加）。HypeCoreのEV/EBITDAが負値無フィルタで格納されており、実データでIOT銘柄にて-16713.74倍の異常値を確認済み。統一関数側で`is_valid`フラグを付与する設計に含める。 |
| AS-IS-132 | 5-3. STONKS SILO | `valuation.psr` | 統一対象外（併存）。STONKS SILOのPSRはSEC年次decisionrevenue基準のAnnual-basis PSRであり、TTM基準の統一関数とは別に「Annual基準PSR」として明示的に併記する。 |
| AS-IS-133 | 5-3. STONKS SILO | `valuation.ev_sales` | 統一対象外（併存）。EV/Salesも同様、Annual基準として明示併記。 |
| AS-IS-282 | 5-6. EPS Analyzer | `components.per`（GAAP PER） | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |
| AS-IS-283 | 5-6. EPS Analyzer | `components.per_adjusted` | 統一定義に準拠（`common/valuation/`の共通取得関数を参照） |

## ⑥ モメンタム／複合トレンド系

### 統一定義（統一しない判断）
**統一しない（並存）**。HypeCoreの`momentum_score`/`expectation_score`/
`fundamental_score`（AS-IS-113/114/115）はZスコア正規化方式、
STONKS SILOの`financial_vectors.fields.*`（AS-IS-135）はベクトル角度方式
と数学的手法が根本的に異なり、対象企業層（成熟企業のセンチメント分析 vs
赤字企業の財務トレンド分析）も別であるため統合の意義がない。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-078 | 5-2. HypeCore | HypeCore `expectation_score` | 統一しない（並存） |
| AS-IS-113 | 5-2. HypeCore | `expectation_score` | 統一しない（並存） |
| AS-IS-114 | 5-2. HypeCore | `fundamental_score` | 統一しない（並存） |
| AS-IS-115 | 5-2. HypeCore | `momentum_score` | 統一しない（並存） |
| AS-IS-135 | 5-3. STONKS SILO | `financial_vectors.fields.*` | 統一しない（並存） |

## ⑦ FCF／キャッシュフロー系

### 統一定義（生データ層のみ明示的共有を推奨、上位加工は統一しない）
ステップ3で実コードを確認した結果、TANUKIの`fcf_history`（AS-IS-047、
`pipeline.py:_load_extra_data`）とSTONKS SILOの`ocf_annual`/
`sbc_adjusted_fcf`（AS-IS-156/160/146、`analyzer.py`）は、**共に
`common/sec_data/data/{TICKER}/annual_*.json`の同一`cf`辞書の同一
フィールド**（`free_cash_flow`/`operating_cash_flow`/
`capital_expenditure`）を参照していることが確認された（**一致**）。

ただし、この共有関係を明示する`provenance`/`source`タグは、
両システムの出力JSONのいずれにも存在しない（`fcf_source`探索でTANUKI側に
ヒットなし、STONKS SILO側も`source`/`provenance`探索でヒットなし）。

**統一定義**: 上位の「用途別に加工されたFCF値」（TANUKIのfcf_base外れ値
調整後の値AS-IS-019、STONKS SILOのincremental_margin系AS-IS-167-170等）
は用途が異なるため統一しない。ただし、**生データ取得層が既に暗黙的に
共有されている事実を可視化するため、両システムの出力JSONに
`fcf_history[].source: "common/sec_data"`相当のprovenanceタグを追加する
ことを推奨する**。これにより、将来SEC正規化ロジック（`common/sec_data`側）
が変更された際に両システムが連動して影響を受けることが明示的に追跡可能になる。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-018 | 5-1. TANUKI VALUATION | dcf_components.*（v0,pv_high_growth,pv_terminal,high_growth_detail,term… | 個別ルート維持（用途別） |
| AS-IS-019 | 5-1. TANUKI VALUATION | fcf_base.base_fcf/method/cv | 個別ルート維持（用途別） |
| AS-IS-021 | 5-1. TANUKI VALUATION | fcf_estimation.applied/conversion_rate/estimated_fcf等 | 個別ルート維持（用途別） |
| AS-IS-047 | 5-1. TANUKI VALUATION | fcf_history[] | 個別ルート維持（用途別） |
| AS-IS-068 | 5-1. TANUKI VALUATION | FCF CAGR(3yr) | 個別ルート維持（用途別） |
| AS-IS-071 | 5-1. TANUKI VALUATION | キャッシュフロー分析セクション | 個別ルート維持（用途別） |
| AS-IS-146 | 5-3. STONKS SILO | `sbc_adjusted_fcf` | 個別ルート維持（用途別） |
| AS-IS-156 | 5-3. STONKS SILO | `ocf_annual` | 個別ルート維持（用途別） |
| AS-IS-160 | 5-3. STONKS SILO | `ocf_annual`（年次dict） | 個別ルート維持（用途別） |
| AS-IS-167 | 5-3. STONKS SILO | `incremental_margin` | 個別ルート維持（用途別） |
| AS-IS-168 | 5-3. STONKS SILO | `incremental_margin_prev` | 個別ルート維持（用途別） |
| AS-IS-169 | 5-3. STONKS SILO | `incremental_margin_trend` | 個別ルート維持（用途別） |
| AS-IS-170 | 5-3. STONKS SILO | `incremental_rev_delta`/`incremental_gp_delta` | 個別ルート維持（用途別） |

## ⑧ 次回決算日

### 統一定義
既に統一済み。TANUKI VALUATIONの`next_earnings_date`（AS-IS-048、
`pipeline.py:_load_extra_data`、yfinanceの`calendar["Earnings Date"]`
から本日以降の直近日を採用）を唯一の正とする。STONKS SILO（AS-IS-179）・
EPS Analyzer（AS-IS-284）は共にTANUKIの`latest.json`をクライアント側で
ライブ参照するパススルー実装であり、変更不要。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-048 | 5-1. TANUKI VALUATION | next_earnings_date | **唯一の正とする**。TANUKI `_load_extra_data`（yfinance calendar由来）。変更不要。 |
| AS-IS-179 | 5-3. STONKS SILO | 次回決算日 | 統一済み（変更不要） |
| AS-IS-284 | 5-6. EPS Analyzer | `next_earnings_date` | 統一済み（変更不要） |

## ⑨ インサイダー／空売り系

### 統一定義（統一しない判断）
**統一しない**。TANUKI VALUATIONの`components.insider_*`
（AS-IS-032に内包）は表示用、HypeCoreの`short_pct_float`（AS-IS-103）・
`buy_hold_ratio`（AS-IS-108）はステージ判定の内部変数（JSON非表示）で
用途が異なる。取得元（yfinance）は同じ可能性が高く、⑤の統一取得関数に
相乗りする形で生データ取得だけ集約するのが将来的に現実的な着地点。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-032 | 5-1. TANUKI VALUATION | per, peg, ps, ev_ebitda, ma200, forward_eps, analyst_target_*, dividen… | 統一しない（用途別）。取得元（yfinance）の集約は⑤の統一関数への相乗りとして将来的に有効。 |
| AS-IS-103 | 5-2. HypeCore | `short_pct_float` | 統一しない（用途別）。取得元（yfinance）の集約は⑤の統一関数への相乗りとして将来的に有効。 |
| AS-IS-108 | 5-2. HypeCore | `buy_hold_ratio` | 統一しない（用途別）。取得元（yfinance）の集約は⑤の統一関数への相乗りとして将来的に有効。 |

## ⑩ リスクイベント／カタリスト系

### 統一定義
TANUKI VALUATIONの`risk_events`（AS-IS-054、Grok検索の簡易版、
report.txtのみに出力）を廃止し、Discoverの`catalysts[]`
（AS-IS-243-246、確度・時期・影響予測付きの本格実装）へのリンクに
置き換える。Discover側は変更なし（既に唯一の正）。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-054 | 5-1. TANUKI VALUATION | risk_events | **削除対象**。TANUKI VALUATIONの`risk_events`（Grok検索簡易版、report.txtのみ出力）を廃止し、該当銘柄のDiscoverカタリスト（AS-IS-243-246）へのリンクに置き換える。 |
| AS-IS-243 | 5-5. Discover | `catalysts[].id` | 変更なし（Discover側が唯一の正） |
| AS-IS-244 | 5-5. Discover | `catalysts[].title/detail/timing/importance/type/probability` | 変更なし（Discover側が唯一の正） |
| AS-IS-245 | 5-5. Discover | `catalysts[].status` | 変更なし（Discover側が唯一の正） |
| AS-IS-246 | 5-5. Discover | `catalysts[].first_detected` | 変更なし（Discover側が唯一の正） |
| AS-IS-258 | 5-5. Discover | `macro_themes[].{theme,horizon,conviction,background,catalyst}` | 変更なし（Discover側が唯一の正） |
| AS-IS-259 | 5-5. Discover | `macro_themes[].related_tickers[].{ticker,role,note}` | 変更なし（Discover側が唯一の正） |
| AS-IS-260 | 5-5. Discover | `macro_themes[].sources[]` | 変更なし（Discover側が唯一の正） |
| AS-IS-261 | 5-5. Discover | `macro_themes[].generated_at` | 変更なし（Discover側が唯一の正） |

## ⑪ マクロ環境認識系

### 統一定義（統一しない判断・ステップ3実データ確認により確定、新事実あり）
**統一しない（確定）**。ステップ3で実コードを確認した結果、TANUKIの
`risk_free_rate`（WACC/ERP計算の入力）は`calculator/wacc.py:59`の
**デフォルト引数`0.043`というハードコード定数**（10年国債利回りを想定した
固定値、"通常4.3%"というコメントあり）が常に使用されており
（`core_calculator.py:159`の呼び出し`calculate_wacc(beta=beta,
sector=sector)`で`risk_free_rate`引数は一切渡されず、常にデフォルト値のまま）、
MACRO PULSEの`ff_rate`（FRED `DFEDTARU`/`DFEDTARL`平均、失敗時
`FEDFUNDS`からの**日次ライブ取得**）とは、(a) 参照する経済指標そのものが
異なる（10年国債利回り想定 vs FF金利）、(b) 取得方式も異なる
（静的ハードコード vs ライブFRED取得）ことが判明した。統一不可の判断は
この新事実によりさらに強化される。

（参考・範囲外の付記: TANUKIのrisk_free_rateが市場実勢から乖離した
静的値のまま運用されている点は、本タスクの範囲外のため修正しないが、
別途の品質課題として認識しておく価値がある）

AS-IS-055/056（erp 2ルート重複）は⑪の群統一問題ではなく、TANUKI内部の
重複実装解消問題として扱う（上表参照）。AS-IS-182/183・214/215・
258-261はそれぞれ②④⑩で主判断済みのため、⑪ではUIレベルでの
「マクロ環境ダッシュボードへの集約」余地があるとだけ記録し、
フィールド統合はしない。

### 対象AS-IS項目と判断
| AS-IS ID | サブシステム | 項目名 | TO-BE判断 |
|---|---|---|---|
| AS-IS-055 | 5-1. TANUKI VALUATION | ① | **TANUKI内部の重複解消対象**（⑪の群統一とは別問題）。latest.json用のerp計算（`pipeline.py:_save_result()` L931-940）を正とし、report.txt側の再実装（AS-IS-056）はこの値を参照する形に統一する。 |
| AS-IS-056 | 5-1. TANUKI VALUATION | ② | **削除対象**（TANUKI内部の重複解消）。report.txt生成時のローカル変数によるerp再計算（`_generate_report()` L2206-2230）を廃止し、AS-IS-055（latest.json保存値）を参照するよう変更する。 |
| AS-IS-182 | 5-4. MACRO PULSE | REGIME | ②で主判断済み（regime）。⑪ではUIレベルの「マクロ環境ダッシュボード」への集約候補としてのみ記録、フィールド統合はしない。 |
| AS-IS-183 | 5-4. MACRO PULSE | regime_source | ②で主判断済み（regime_source）。同上。 |
| AS-IS-214 | 5-4. MACRO PULSE | RECESSION RISK SCOREバー・マーカー | ④で主判断済み（RECESSION RISK SCORE）。同上。 |
| AS-IS-215 | 5-4. MACRO PULSE | RECESSION RISK SCORE数値 | ④で主判断済み（RECESSION RISK SCORE）。同上。 |
| AS-IS-258 | 5-5. Discover | `macro_themes[].{theme,horizon,conviction,background,catalyst}` | ⑩で主判断済み（macro_themes）。同上。 |
| AS-IS-259 | 5-5. Discover | `macro_themes[].related_tickers[].{ticker,role,note}` | ⑩で主判断済み（macro_themes）。同上。 |
| AS-IS-260 | 5-5. Discover | `macro_themes[].sources[]` | ⑩で主判断済み（macro_themes）。同上。 |
| AS-IS-261 | 5-5. Discover | `macro_themes[].generated_at` | ⑩で主判断済み（macro_themes）。同上。 |

## 単独ルート項目（変更なし、機械的一括生成）

以下は11共通項目群のいずれにも該当しない単独ルート項目（199件）。
重複がないため、統一定義・削除対象の設計は不要。全件、以下の形式で
機械的に一括記録する。

- AS-IS-001：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / intrinsic_value_per_share
- AS-IS-002：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / intrinsic_value_beta
- AS-IS-004：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / intrinsic_value_rf
- AS-IS-007：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / v0
- AS-IS-008：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / v0_adjusted
- AS-IS-009：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / alpha / alpha_was_capped
- AS-IS-010：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / future_values
- AS-IS-011：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / return_metrics
- AS-IS-013：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / wacc.value/beta/risk_free_rate/market_return
- AS-IS-014：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / sensitivity.matrix/wacc_values/growth_years
- AS-IS-015：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / scenario_valuations.bear/base/bull
- AS-IS-016：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / growth_options.total_pv/count/options
- AS-IS-017：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / maturity_profile
- AS-IS-022：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / software_system_reclassification.*
- AS-IS-023：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / rd_capitalization.*
- AS-IS-024：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / rpo_adjustment.rpo_pv/application_rate/sector_category/rpo_i…
- AS-IS-025：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / bs_adjustment.net_cash/net_cash_per_share/sector_guard
- AS-IS-026：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / moat_score系（components.moat_score等）
- AS-IS-027：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / rice.q/cf_conversion/q_years/cf_years/avg_intensity/avg_rev_…
- AS-IS-028：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / moat_score / moat_phase1_years / moat_gross_margin_norm / mo…
- AS-IS-029：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / pv_high / pv_terminal
- AS-IS-030：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / alpha_uncapped
- AS-IS-033：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / max_eps / max_eps_per / max_eps_reliability
- AS-IS-036：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / score_comment
- AS-IS-038：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / sell_reason
- AS-IS-039：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / pre_rounding_score
- AS-IS-040：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / rounded_by_policy
- AS-IS-044：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / fcf_margin_bear_mult_applied
- AS-IS-045：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / financial_health.*（net_debt,total_debt,cash_and_equivalents,…
- AS-IS-046：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / dupont.net_margin/asset_turnover/financial_leverage/roe_deco…
- AS-IS-049：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / computed_runway_months
- AS-IS-050：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / segments[]
- AS-IS-051：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / breakeven_estimate
- AS-IS-053：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / dilution_severity / dilution_comment
- AS-IS-057：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 場所
- AS-IS-058：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 用途
- AS-IS-059：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / terminal_growthの出所
- AS-IS-060：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / ガード
- AS-IS-064：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 将来価値予測（シナリオ別テーブル）
- AS-IS-065：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 5年BASE年率換算リターン
- AS-IS-066：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 感応度分析（独自5×5マトリクス）
- AS-IS-067：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / Reverse DCF
- AS-IS-069：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / WACCスライダー
- AS-IS-070：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / Layer2トグル
- AS-IS-072：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 銘柄数
- AS-IS-073：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 平均Moat
- AS-IS-074：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 平均RICE
- AS-IS-076：変更なし（単独ルート、重複なし） — 5-1. TANUKI VALUATION / 200MA乖離
- AS-IS-077：変更なし（単独ルート、重複なし） — 5-2. HypeCore / HypeCore `stage_label`
- AS-IS-080：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `generated_at`
- AS-IS-081：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `monthly`
- AS-IS-082：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `tickers`（配列）
- AS-IS-083：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `month`
- AS-IS-084：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `price`
- AS-IS-086：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `stage_label`
- AS-IS-087：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `ma200_dev`
- AS-IS-088：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `ma50_dev`
- AS-IS-089：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `from_peak`
- AS-IS-090：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `rsi`
- AS-IS-091：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `volume_ratio`
- AS-IS-092：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `vol_surge`
- AS-IS-094：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `ni_yoy`
- AS-IS-095：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `rule40`
- AS-IS-096：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `fcf_yield`
- AS-IS-101：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `earnings_growth`
- AS-IS-104：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `eps_surprise`
- AS-IS-106：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `analyst_downgrade_rate`
- AS-IS-107：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `sell_on_good_news`
- AS-IS-109：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `substage_phase`
- AS-IS-110：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `substage_label`
- AS-IS-111：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `substage_watch`
- AS-IS-112：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `substage_next`
- AS-IS-118：変更なし（単独ルート、重複なし） — 5-2. HypeCore / `low_base_effect`
- AS-IS-119：変更なし（単独ルート、重複なし） — 5-2. HypeCore / ライフサイクル（黎明/成長/拡大/成熟）
- AS-IS-120：変更なし（単独ルート、重複なし） — 5-2. HypeCore / HypeCore推奨（買い/保有/売り等）
- AS-IS-121：変更なし（単独ルート、重複なし） — 5-2. HypeCore / 1ヶ月後のステージ遷移確率
- AS-IS-122：変更なし（単独ルート、重複なし） — 5-2. HypeCore / バリュエーション倍率パネル（PER/PS/PEG/EV-EBITDA）
- AS-IS-123：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `generated_at`
- AS-IS-124：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `tickers`（辞書, ticker→result）
- AS-IS-125：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `years`
- AS-IS-128：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `summary`
- AS-IS-129：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `records`（yr→{revenue,net_income}）
- AS-IS-130：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `valuation.market_cap`
- AS-IS-131：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `valuation.current_price`
- AS-IS-134：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `valuation.net_cash`
- AS-IS-137：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `rnd_ratio`
- AS-IS-138：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `sm_ratio`
- AS-IS-139：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `gross_margin`
- AS-IS-140：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `gross_margin_derived`
- AS-IS-142：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `score`
- AS-IS-143：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `rule_of_40`
- AS-IS-144：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `mature_profit`
- AS-IS-145：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `mature_profit_note`
- AS-IS-147：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `sbc_ratio`
- AS-IS-148：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `sbc_yoy_change`
- AS-IS-151：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `revenue_outlier_years`
- AS-IS-153：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `cash`
- AS-IS-154：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `monthly_burn`
- AS-IS-155：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `runway_months`
- AS-IS-157：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `capex_annual`
- AS-IS-159：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `score`
- AS-IS-162：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `gaap_breakeven_year`/`gaap_breakeven_reason`
- AS-IS-163：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `ocf_breakeven_year`/`ocf_breakeven_reason`
- AS-IS-164：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `hidden_profit_already`
- AS-IS-165：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `discontinuous_growth`
- AS-IS-166：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `discontinuous_growth_note`
- AS-IS-171：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `reproduction_score`
- AS-IS-172：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `reproduction_label`
- AS-IS-173：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `score`
- AS-IS-174：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `fields.{name}.yoy/qoq.change_pct,val_latest,val_prev,end_la…
- AS-IS-175：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `fields.{name}.yoy/qoq.percentile`
- AS-IS-176：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `fields.{name}.yoy/qoq.angle,length`
- AS-IS-177：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / `fields.{name}.series_q`（四半期時系列）
- AS-IS-178：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / TANUKIスコアバッジ
- AS-IS-180：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / 黒字転換目算（Adj.EPS線形推定）
- AS-IS-181：変更なし（単独ルート、重複なし） — 5-3. STONKS SILO / Adj.EPS系列（黒字化ロードマップ）
- AS-IS-184：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / FF RATE
- AS-IS-185：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 1Y EXPECTED FF
- AS-IS-186：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / IMPLIED CUTS
- AS-IS-187：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / FRB主眼(dominant_label)
- AS-IS-188：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 判断理由(ai_reason)
- AS-IS-189：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / FOMC日付
- AS-IS-190：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / S&P500現在値
- AS-IS-191：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / S&P500前日比
- AS-IS-192：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 10Y-2Y SPREAD
- AS-IS-193：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 10Y-2Y判定(INVERTED/FLAT/NORMAL)
- AS-IS-194：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / HY SPREAD
- AS-IS-195：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / LAST UPDATE
- AS-IS-196：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / （画面最上部）最終更新表示
- AS-IS-197：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / M2
- AS-IS-198：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / NET LIQUIDITY
- AS-IS-199：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / HYスプレッド（流動性カード）
- AS-IS-200：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / FRBバランスシート
- AS-IS-201：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 各カードの前月比/前週比(chg)
- AS-IS-202：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 各カードのパーセンタイル/水準バー
- AS-IS-203：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 各カードの解説コメント(m2Comment/nlComment/hyComment/fedComment)
- AS-IS-204：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / Hollow Rallyバッジ
- AS-IS-207：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / LAYER3（NET流動性連続減少週数）
- AS-IS-208：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 警戒アラート文
- AS-IS-210：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / REPO残高(RRPONTSYD)
- AS-IS-211：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 準備預金(WRBWFRBL)
- AS-IS-212：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / TGA残高(WTREGEN)
- AS-IS-213：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / フェーズbadge / phase-sub
- AS-IS-216：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / シグナルテキスト
- AS-IS-217：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / ALERTバナー
- AS-IS-218：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 8指標シグナルグリッド
- AS-IS-219：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / スコア比較バー（3ヶ月前/2ヶ月前/前月比/先週比/カスタム）
- AS-IS-220：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / surprise_alerts
- AS-IS-221：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 週次カード日付/スコア/フェーズ
- AS-IS-222：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 週差/月差(chg1w/chg1m)
- AS-IS-223：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 総括(summary)
- AS-IS-224：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 要因分析(factor_analysis)
- AS-IS-225：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 注視ポイント(watchpoints)
- AS-IS-226：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 各指標コメント(indicator_comments)
- AS-IS-227：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 週差/月差バッジ(各指標)
- AS-IS-228：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / model表示
- AS-IS-229：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 8指標の値/シグナル(BULL/CAUTION/NEUTRAL/BEAR)/バー位置
- AS-IS-230：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / スコア推移折れ線
- AS-IS-231：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / NBER後退期帯
- AS-IS-232：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / フェーズゾーン背景(0-25/25-52/52-70/70-100)
- AS-IS-233：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 期間切替(1年/3年/5年/全期間)ボタン
- AS-IS-234：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / レーダーチャート（現在/2019/2001/スライダー）
- AS-IS-235：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / 類似度スコア(2019年/2001年、%)
- AS-IS-236：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / スライダー（過去に戻る）
- AS-IS-237：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / DATE/INDICATOR/ACTUAL
- AS-IS-238：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / PREV
- AS-IS-239：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / DIR(↑/↓/→)・CHANGE
- AS-IS-240：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / DATE/INDICATOR
- AS-IS-241：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / DAYS
- AS-IS-242：変更なし（単独ルート、重複なし） — 5-4. MACRO PULSE / CONSENSUS
- AS-IS-247：変更なし（単独ルート、重複なし） — 5-5. Discover / `tickers{}.updated_at`
- AS-IS-248：変更なし（単独ルート、重複なし） — 5-5. Discover / 影響予測`{direction, magnitude, thesis_effect, summary}`
- AS-IS-249：変更なし（単独ルート、重複なし） — 5-5. Discover / `tickers{}.category/memo`
- AS-IS-250：変更なし（単独ルート、重複なし） — 5-5. Discover / `classified.items[].{title,category,importance,summary,url,s…
- AS-IS-251：変更なし（単独ルート、重複なし） — 5-5. Discover / `classified.summary`
- AS-IS-252：変更なし（単独ルート、重複なし） — 5-5. Discover / `classified.conditions_met[]` / `classified.risk_flags[]`
- AS-IS-253：変更なし（単独ルート、重複なし） — 5-5. Discover / `top_importance`（tickers[ticker]直下）
- AS-IS-254：変更なし（単独ルート、重複なし） — 5-5. Discover / `candidates[].{ticker,company,sector,reason,risk}`
- AS-IS-255：変更なし（単独ルート、重複なし） — 5-5. Discover / `candidates[].screening_pass[]`
- AS-IS-256：変更なし（単独ルート、重複なし） — 5-5. Discover / `candidates[].catalyst_type`
- AS-IS-257：変更なし（単独ルート、重複なし） — 5-5. Discover / `candidates[].conviction`
- AS-IS-262：変更なし（単独ルート、重複なし） — 5-5. Discover / `price_change_next_day`
- AS-IS-263：変更なし（単独ルート、重複なし） — 5-5. Discover / `theme_config`（テーマID/ラベル/カラー）
- AS-IS-264：変更なし（単独ルート、重複なし） — 5-5. Discover / `discover_config`（銘柄別category/memo/themes）
- AS-IS-265：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `ticker` / `last_updated`
- AS-IS-266：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `quarters[].filing_date/period_end/fiscal_year/quarter`
- AS-IS-267：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `quarters[].gaap_eps/adjusted_eps/gaap_net_income/adjusted_n…
- AS-IS-268：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `quarters[].adjustments[].item_name/reason/extracted_from`
- AS-IS-269：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `quarters[].adjustments[].net_amount`
- AS-IS-270：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `quarters[].ai_analysis.health/comment`
- AS-IS-271：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `quarters[].ai_analysis.sources[].item/snippet/confidence`
- AS-IS-272：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `quarters[].special_flags(EPS_DISCREPANCY)` / `special_notes…
- AS-IS-273：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `ticker/company_name/latest_filing_date`
- AS-IS-274：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `gaap_eps/adjusted_eps`
- AS-IS-275：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `eps_diff`
- AS-IS-276：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `eps_ratio`
- AS-IS-277：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `gaap_to_adj_positive`
- AS-IS-278：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `yoy_growth`
- AS-IS-281：変更なし（単独ルート、重複なし） — 5-6. EPS Analyzer / `ttm.json`（`ttm[].period/net_income/adjusted_income/diluted_…
