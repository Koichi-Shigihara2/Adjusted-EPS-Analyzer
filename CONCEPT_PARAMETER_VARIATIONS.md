# CONCEPT_PARAMETER_VARIATIONS.md — 概念統一・パラメータ違いの記録

作成日: 2026-07-22
出発点: `OUTPUT_ITEMS_INVENTORY.md`（AS-IS全515項目）、`TO_BE.md`（16群統一定義）、
`TO_BE_FINAL_LIST.md`（同一定義／異なる定義の項目単位判定）

## 本ドキュメントの位置づけ

`TO_BE_FINAL_LIST.md`で「異なる定義」（497件）に分類されていた項目のうち、
実際には**計算の目的・対象データは同じだが、集計期間（TTM/FY/YoY/3年CAGR等）
というパラメータのみが異なる**ペア・グループが存在することが判明した。
これらを第3カテゴリ「概念統一・パラメータ違い」として本ドキュメントに
記録する。

**重要**: このカテゴリは項目を削除・統合するものではない。各パラメータ
バリエーションは、それぞれ固有の目的（例: STONKS SILOのAnnual基準は
プレレベニュー企業のSEC実績重視、HypeCoreのTTM基準は市場の直近評価反映）
のために個別に存置される。本ドキュメントは「これらが同じ根本概念の異なる
窓（period window）である」という関係性を記録し、将来の`NAMING_CONVENTIONS.md`
（期間接尾辞規則）適用時の参照台帳とすることを目的とする。

実装（コード修正）は行っていない。分類の見直しと記録のみ。

## 判定基準

以下をすべて満たすペア・グループを「概念統一・パラメータ違い」と判定した:
1. 同一の根本的な財務指標・データ項目を測定対象としている（例: 売上高、
   純利益、OCF、PSR＝時価総額÷売上高）
2. 実際にコードを確認し、同一の生データフィールド（同一XBRLタグ相当・
   同一yfinanceフィールド）または同一の`common/sec_data`系列を参照して
   いることを確認した
3. 相違点が集計期間・窓（TTM／単年度FY／YoY系列／3年CAGR／最新1年のみ
   等）のみであり、測定対象の財務指標そのものは変わらない

この基準を満たさない場合（データソース自体が異なる、測定対象の財務指標
そのものが異なる等）は「異なる定義」のまま維持する。判定の過程で
**棄却した候補**（③成長率系のTANUKI FCF CAGR、⑬Rule of 40）も本文末尾に
理由とともに記録する。

---

## 概念1: PSR（株価売上高倍率）

**共通の計算対象**: 時価総額（または株価）を売上高で除した倍率。「割高/割安」
の簡易指標として3サブシステムが独立に保持。

**パラメータバリエーション**:

| AS-IS ID | サブシステム | 期間パラメータ | 値の説明 |
|---|---|---|---|
| AS-IS-032（内包、`ps`サブフィールド） | TANUKI VALUATION | TTM | `data_fetcher.py:532` `info.get("priceToSalesTrailing12Months")`。**注記**: AS-IS-032はper/peg/ev_ebitda等を含む束ねられた行のため、`ps`はその一部のサブフィールドとして概念1に属する（AS-IS-032自体は他の非PSRフィールドを含むため「異なる定義」プールにも残る） |
| AS-IS-099 | HypeCore | TTM | `hypecore.py:118` `info.get("priceToSalesTrailing12Months")`。TANUKIの`ps`と**全く同一のyfinanceフィールド**を参照（取得タイミングのみ非同期） |
| AS-IS-132 | STONKS SILO | Annual | `pipeline.py:127` `market_cap / latest_rev`（`latest_rev`は`common/sec_data`の`revenue_sanitized`、直近通期決算）。TTM基準の2件とは分母の期間が異なる |

**実データ突合（本日別調査で既実施）**: AVAV等の黒字銘柄でTTM同士（032/099相当）はほぼ完全一致を確認済み。Annual基準（132）はIONQ等で最大1.75倍の乖離を確認済み（`TO_BE.md`⑤群参照）。

---

## 概念2: net_income（純利益）

**共通の計算対象**: SEC XBRL `NetIncomeLoss`相当の純利益額。

**パラメータバリエーション**:

| AS-IS ID | サブシステム | 期間パラメータ | 値の説明 |
|---|---|---|---|
| AS-IS-129 | STONKS SILO | FY（単年度決算） | `pipeline.py:111-117`、`common/sec_data`の年次正規化パイプライン経由 |
| AS-IS-281 | EPS Analyzer | TTM（直近4四半期合算） | `pipeline.py:calculate_ttm`(288-304)、EPS Analyzer自身の独立XBRL抽出パイプライン経由 |

**実データ突合（本日別調査で既実施）**: 期間が実質整合する銘柄（AVAV, ESTC）では完全一致を確認済み。IONQ/IOT/ONDS等では期間差により符号反転を含む乖離を確認済み（`TO_BE.md`⑭群参照）。

---

## 概念3: 売上高成長率（Revenue Growth Rate）

**共通の計算対象**: 売上高の期間比較による成長率（%）。

**パラメータバリエーション**:

| AS-IS ID | サブシステム | 期間パラメータ | 値の説明 |
|---|---|---|---|
| AS-IS-152 | STONKS SILO | 単年度YoY系列 | `analyzer.py:196-212` `(curr/prev - 1) * 100`（年ごと）、`common/sec_data`年次`revenue_sanitized`由来 |
| AS-IS-136 | STONKS SILO | 3年CAGR | `analyzer.py:215-222` `((r_end/r_start)**(1/3) - 1) * 100`（4年前と直近年を比較）、152と**同一の`revenue_sanitized`系列**を参照、窓の長さのみ異なる |
| AS-IS-093 | HypeCore | TTM YoY | `hypecore.py:162-164` `rev_ttm = rev.rolling(4).sum()`、`(rev_ttm / rev_ttm.shift(4) - 1) * 100`。**データソースに注意**: `{ticker}_quarterly_normalized.json`（SEC四半期正規化データ）由来であり、152/136の年次`annual_*.json`（`revenue_sanitized`）とは**別の正規化パイプラインを経由**している。同じ「SEC由来の売上高」という大分類には属するが、集計元ファイル自体が異なるため、152/136ほど厳密に「同一データソース」とは言い切れない点を明記する |

**新規発見**: AS-IS-136とAS-IS-152は`analyzer.py`内の同一関数・同一変数`revenues[yr]`から算出されており、**データソースの同一性が最も厳密に確認できるペア**。AS-IS-093は概念としては同じだが、正規化パイプラインの違いというprovenance上の注意点がある。

---

## 概念4: STONKS SILO OCF年次値（単年 vs 多年）

**共通の計算対象**: 年次営業キャッシュフロー（`cf.operating_cash_flow`）。

**パラメータバリエーション**:

| AS-IS ID | サブシステム | 期間パラメータ | 値の説明 |
|---|---|---|---|
| AS-IS-156 | STONKS SILO（`_analyze_runway`） | 最新1年のみ | `analyzer.py:494` `ocf = cf.get("operating_cash_flow")`（`records[years[-1]]`、月次バーン計算用） |
| AS-IS-160 | STONKS SILO（`_analyze_profitability_path`） | 全年度（複数年dict） | `analyzer.py:551-553` `ocf_annual[yr] = records[yr]["cf"].get("operating_cash_flow")`（黒字化ロードマップのチャート用） |

**注記**: 156は160が保持する複数年dictのうち「最新1年分」のみを別の関数で再抽出したものであり、同一サブシステム内での軽微な重複実装。データソース・フィールドは完全に同一（`cf.get("operating_cash_flow")`）で、窓の長さ（1年 vs 全年）のみが異なる、最も明確な「概念統一・パラメータ違い」の例。

---

## 精査した結果、棄却した候補（第3カテゴリに該当しないと判定）

### ③成長率系: TANUKI「FCF CAGR(3yr)」(AS-IS-068) vs STONKS SILO「cagr_3yr」(AS-IS-136)
**棄却理由**: 名称は類似（共に"3yr CAGR"）だが、測定対象の財務指標そのものが異なる。
AS-IS-068はFCF（フリーキャッシュフロー）の3年複利成長率（stock.html:2106-2113
`(最新FCF/3年前FCF)^(1/3)-1`）、AS-IS-136は売上高の3年複利成長率
（`analyzer.py:215-222`）。「3年窓」という期間パラメータは共通するが、
FCF≠売上高であり測定対象の財務指標自体が異なるため、判定基準2（同一の
生データフィールドを参照）を満たさない。「異なる定義」のまま維持する。

### ⑬Rule of 40系: HypeCore「rule40」(AS-IS-095) vs STONKS SILO「rule_of_40」(AS-IS-143)
**精査結果**: 部分的に概念3（売上高成長率）を内包していることを新たに発見した。
- HypeCoreの`rule40 = rev_yoy + op_margin`の成長率項`rev_yoy`は、**AS-IS-093と
  完全に同一の値**（同じ変数を再利用、`hypecore.py:166-167`）
- STONKS SILOの`rule_of_40 = cagr_3yr + operating_income/revenue*100`の
  成長率項`cagr_3yr`は、**AS-IS-136と完全に同一の値**（同じ変数を再利用、
  `analyzer.py:245-249`）

しかし、Rule of 40全体としては**棄却**する。理由: 各々の「利益率」項
（HypeCore: 純利益率＝NI/Revenue、STONKS SILO: 営業利益率＝
OperatingIncome/Revenue）が、期間パラメータの違いではなく**会計上の
定義そのものが異なる指標**（純利益率と営業利益率は非営業項目・税金・
利息の扱いが本質的に異なる）であるため、Rule of 40という合成指標
全体を1つの「概念＋パラメータ違い」として扱うことはできない。
AS-IS-095／AS-IS-143は「異なる定義」のまま維持し、それぞれの成長率
サブコンポーネントが概念3と関連している旨のみ、概念3のテーブルに
注記として残す（既に上記に記載済み）。

### ⑦FCF系: TANUKI「fcf_base」(AS-IS-019) vs STONKS SILO「ocf_annual」(AS-IS-156/160)
**棄却理由**: `common/sec_data`の同一`cf`辞書を参照する点は`TO_BE.md`⑦群で
既に確認済みだが、TANUKIの`fcf_base`は`cf.get("free_cash_flow")`
（OCF−CapEx、FCF）を参照するのに対し、STONKS SILOの`ocf_annual`は
`cf.get("operating_cash_flow")`（CapEx控除前のOCF）を参照しており、
**フィールド自体が異なる**（FCF≠OCF）。判定基準2を満たさないため
「異なる定義」のまま維持する。

---

## 再集計への反映

概念1〜4に該当する項目の総数: **9件**（`AS-IS-032`の内包分は`AS-IS-032`
自体を「異なる定義」プールから除外しないため、独立カウント対象は
`AS-IS-099, 132, 129, 281, 152, 136, 093, 156, 160`の9件）。

これらは削除・統合されるわけではなく、引き続き9件それぞれが個別の
出力項目として存在し続ける。変わるのは分類上の扱い（「異なる定義」
→「概念統一・パラメータ違い」という第3カテゴリへの移動）のみであり、
**最終的な出力項目の実数（503件）に変化はない**。詳細は`TO_BE_FINAL_LIST.md`
のステップ5を参照。
