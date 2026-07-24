# SEC_EDGAR_LAYER_DESIGN.md — SEC EDGARレイヤー統合設計

作成日: 2026-07-24
位置づけ: 新一次データベース構築プロジェクト フェーズ1、
common/sec_data統合（INPUT-A-001〜018・048）の設計判断・根拠を記録する。
進捗ステータスは`PROJECT_STATUS.md`、実装後の実態は`SYSTEM_MAP.md`を
参照。本ドキュメントは「なぜこの設計にしたか」の記録に特化する。

---

## 1. 背景

現状9系統（後に10系統と判明、下記2-4参照）に分岐した読み取り経路
（`data/{annual,quarterly}_*.json`・`raw/`・`normalized/`・`ttm/`・
`company_facts.json`・EPS Analyzer独自3ファイル）を、統合スキーマへ
一本化する設計を、複数回の投資調査（読み取り専用）を通じて確定した。

---

## 2. 現状分析で判明した事実

### 2-1. quarterly系統の構造的欠陥

`data/quarterly_{FYQ}.json`のQ2以降の値は会計年度累計（YTD）値の
ままであり、真の単四半期値ではない。`normalized/`は真の単四半期値に
変換済みだが、タグ網羅性が乏しく（例: STDebtは単一タグのみ、
AAPL/XOM/V等主要銘柄で0件）、フィールド網羅性でも
`free_cash_flow`・`short_term_investments`等の最高影響度フィールドを
欠いている（105銘柄全数で確認済み、[[SCHEMA-STDEBT-COVERAGE-GAP-1]]・
[[SCHEMA-SM-SGA-CONFLATION-1]]としてBACKLOG登録済み）。

### 2-2. annual系統

`annual_{FY}.json`と`quarterly_{FYQ}.json`はフィールド集合が完全一致
（105銘柄全数で確認）。BS系10フィールド（Cash/STDebt/LTDebt/
DeferredRevenue/Equity/Assets/SharesBasic/RPO/CurrentAssets/
CurrentLiabilities）は、四半期末＝年度末となる期のQ4エントリが
年度末値を兼ねる構造的帰結であり、annual専用の別ストアは不要と判断。

### 2-3. segmentKPI（INPUT-A-016）

当初`INPUT_DATA_TOBE.md`は正式ASC280セグメントを想定していたが、
実態（`xbrl_segment_fetcher.py`）は銘柄固有カスタムKPI（
`tail_kpi_map.json`定義）であり、取得方式（生XBRL XML直接解析）も
他フィールドと異なる。TOBE側の前提誤りと判明したため、
`INPUT_DATA_TOBE.md`側を訂正（2026-07-23実施済み）し、**フェーズ1の
統合スコープからは除外**。現状の独立実装を維持する。

### 2-4. company_facts.json（Layer1の実態）

`common/sec_data/data/{TICKER}/company_facts.json`が、SEC EDGAR
company_facts APIの完全な生レスポンス（フィルタなし、AAPL実測505
concept、105銘柄合計582.2MB）を無加工のまま週次保存していることが
判明した（過去の複数回の投資調査でも見落とされていた、
[[SECDATA-COMPANYFACTS-OVERLOOKED-1]]参照）。統合設計上、これが
系統数を「9→10」に訂正する根拠であり、かつ後述Layer1として
そのまま活用できる。

### 2-5. EPS Analyzer独立取得（52タグ）

EPS Analyzer（`extract_key_facts.py`）は同一のSEC EDGAR
companyfacts APIエンドポイントを独自に週次で叩いており、
common/sec_dataとは19タグが共通、52タグが独自（税務・一過性項目・
公正価値変動・銀行業向け、`INPUT-A-048`として登録済み）。
company_facts APIはconcept単位の部分取得に対応せず、同一銘柄・
同一タイミングであれば理論上バイト同一のレスポンスとなるため、
2-4のLayer1が既に52タグ全量を含んでいる。「独自取得層の統合」では
なく「Layer2設定への52概念追加」で対応可能という結論に至った
（詳細は4章）。

### 2-6. raw/の実態

`raw/{TICKER}_quarterly_raw.json`は「正規化前生XBRL」という名称に
反し、`FIELD_CONCEPTS`（26エントリ、うち1件は内部専用フィールド
`_COGS`、出力からは除外）で既にフィルタ済みの狭い
サブセット（AAPL実測26 concept、company_facts.jsonの505概念の
約5.2%）。診断専用（`audit.py`のみ参照）であり、Layer1の役割は
果たせないことが定量的に裏付けられた。

---

## 3. 決定した統合スキーマ（Layer3、31フィールド）

既存`normalized/`の25フィールドに、`data/quarterly`側にのみ存在し
参照実績のある6フィールドを追加。

| # | フィールド | 追加理由 |
|---|---|---|
| 1〜25 | （既存normalized 25フィールド: OCF/ICF/CFF/CapEx/FinanceLeasePmts/SBC/DA/Revenue/GrossProfit/OperatingIncome/NetIncome/Cash/STDebt/LTDebt/DeferredRevenue/Equity/Assets/SharesBasic/SharesDiluted/RD/SM/RPO/CurrentAssets/CurrentLiabilities/Buyback） | 既存 |
| 26 | short_term_investments | Net Debt計算の中核入力、既存欠落 |
| 27 | total_liabilities | 診断・警告表示で参照実績あり |
| 28 | eps_basic | reader.py代替推計で参照実績あり |
| 29 | eps_diluted | reader.py代替推計で参照実績あり |
| 30 | cost_of_revenue | 内部取得済み（_COGS）、露出するのみ |
| 31 | selling_general_and_administrative | SM/SGA明示分離（[[SCHEMA-SM-SGA-CONFLATION-1]]解消） |

`free_cash_flow`は生フィールドとして維持（既存設計原則「符号正規化は
取得レイヤーで一度」に整合すると判断、導出データ層への移動は不要と
結論、詳細4章参照）。

---

## 4. Layer1〜3アーキテクチャ

タグはSEC提出者（発行体）側が定義するものであり、内部システム側の
利用ニーズによって必要タグ数が可変であるという性質を踏まえ、
「取得（Acquisition）」と「抽出（Extraction）」を分離する3層構造を
採用する。

- **Layer1（無加工アーカイブ）**: `company_facts.json`（既存、
  新規構築不要）。SEC APIレスポンス全量を無加工のまま保持する唯一の
  層。
- **Layer2（概念定義）**: 現状Pythonコードにハードコードされている
  `FIELD_CONCEPTS`/`XBRL_MAPPING`を、設定ファイル（1エントリ＝1概念：
  内部フィールド名・タグ候補リスト・フォールバック順・カテゴリ・
  利用サブシステム）による管理へ移行する（詳細設計は別タスク）。
  新規フィールド追加（52タグ含む）はコード変更ではなく設定追加で
  対応可能にする。
- **Layer3（抽出済み正規化ストア）**: Layer1にLayer2を適用して
  生成される、3章の31フィールド統合ストア。`raw/`は本アーキテクチャ
  移行後は冗長化するため廃止候補（[[SECDATA-STORAGE-FRAGMENTATION-1]]
  で検討）。

---

## 4-1. Layer2スキーマ設計

概念定義（現状`FIELD_CONCEPTS`/`XBRL_MAPPING`としてPythonコードに
ハードコード）を、`config/sec_concept_definitions.json`（仮称）という
JSON設定ファイル形式へ移行する。設計方針は以下の通り。

- フィールド名はsnake_caseに統一（`NAMING_CONVENTIONS.md`規則7）
- `category`（flow/stock/shares/excluded）は`contracts.py::
  validate_field_classification()`の完全性契約をそのまま踏襲し、
  必須項目とする
- 意図的に除外した候補タグは`excluded_candidates`に理由とともに
  記録する（DA・SharesBasic等で発覚した「候補数が多い方を機械的に
  採用すると別の会計概念が混入する」問題の再発防止）
- 既存`TICKER_RESTRICTIONS`（銘柄ごとにキー体系が不統一だった）は
  `exclude`/`override_concept`/`note`の3キーに統一する

以下は代表フィールドの抜粋であり、全31フィールド分の完全なエントリは
実装タスク側で本スキーマ形式に沿って`FIELD_CONCEPTS`・`XBRL_MAPPING`
全量を機械変換する。

```json
{
  "_schema_version": "1.0",
  "_description": "SEC EDGAR XBRLタグ→内部フィールド定義（Layer2）。新規フィールド追加はコード変更ではなく本ファイルへの追記で行う。",
  "fields": {
    "capital_expenditure": {
      "category": "flow",
      "unit": "USD",
      "candidates": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsForCapitalImprovements",
        "PaymentsToAcquireOtherPropertyPlantAndEquipment"
      ],
      "sign_normalize": "abs",
      "_note": "2026-07-23 CAPEX-SIGN-UNNORMALIZED-1対応に基づきsign_normalizeを明示"
    },
    "depreciation_and_amortization": {
      "category": "flow",
      "unit": "USD",
      "candidates": [
        "DepreciationAndAmortization",
        "DepreciationDepletionAndAmortization",
        "Depreciation",
        "AmortizationOfIntangibleAssets"
      ],
      "_note": "2026-07-24 SCHEMA-DA-FALLBACK-MISSING-1対応。primaryはDepreciationAndAmortization（Depletion除外、実際の成長率計算消費箇所の前提と一致）。DepreciationDepletionAndAmortizationは資源セクター銘柄（FCX/XOM/SCCO/CAT/HON等、Depletion込みタグのみ報告）向けの意図的なフォールバックとして2番目に維持する（完全除外するとこれらの銘柄でDA値が空になるため）。両タグは会計上厳密には異なる概念（Depletion込み/除外）である点に留意"
    },
    "shares_diluted": {
      "category": "shares",
      "unit": "shares",
      "candidates": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "CommonStockSharesOutstanding"
      ]
    },
    "shares_basic_weighted_avg": {
      "category": "shares",
      "unit": "shares",
      "candidates": [
        "WeightedAverageNumberOfSharesOutstandingBasic"
      ],
      "_note": "2026-07-24 期中加重平均株式数（PL項目）。SCHEMA-SHARESBASIC-CONCEPT-MISMATCH-1によりshares_outstanding_period_endと分離"
    },
    "shares_outstanding_period_end": {
      "category": "shares",
      "unit": "shares",
      "candidates": [
        "CommonStockSharesOutstanding"
      ],
      "_note": "2026-07-24 期末発行済株式数（BS項目）"
    },
    "long_term_debt": {
      "category": "stock",
      "unit": "USD",
      "candidates": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "LongTermNotesPayable",
        "SeniorNotes",
        "LongTermDebtAndCapitalLeaseObligations",
        "UnsecuredLongTermDebt",
        "ConvertibleLongTermNotesPayable",
        "ConvertibleDebtNoncurrent",
        "OtherLongTermDebt"
      ],
      "_note": "2026-07-24 SCHEMA-LTDEBT-DOUBLECOUNT-RISK-1対応。Noncurrentを先頭固定（二重計上防止）"
    }
  },
  "ticker_overrides": {
    "MSFT": {
      "field": "revenue",
      "action": "exclude",
      "note": "既存TICKER_RESTRICTIONS移行"
    }
  }
}
```

**未確定事項**:
- Revenue・RPO・_COGS（単純網羅性差、union採用予定）の具体的な統合後
  candidates順序は実装時に確定する
- `TICKER_RESTRICTIONS`（9銘柄分の既存override）の3キー形式への変換
  内容は実装時に個別確認する

---

## 5. スコープ確定事項

| 対象 | 判断 | 理由 |
|---|---|---|
| quarterly/annual（31フィールド） | 統合スコープに含める | 3章参照 |
| segments（セグメントKPI） | **除外**（現状維持） | 2-3参照、TOBE前提の誤りが判明 |
| filing_text（内部統制テキスト） | 統合スコープに含める（低コスト、書き込み側1＋消費側3ファイル） | 既にfiling_text概念と構造的親和性高 |
| submissions | 現状の`fetcher.py`キャッシュ経路を正とし、`edgar_rss_monitor.py`側は個別修正 | [[SEC-SUBMISSIONS-DUAL-FETCH-1]]で対応、統合スキーマ構造への影響なし |
| EPS Analyzer（52タグ） | Layer2設定拡張で対応、独自API取得は将来的に廃止候補 | 2-5・4章参照 |

---

## 6. 未確定・今後の検討事項

- Layer2（概念定義設定ファイル）の詳細スキーマ設計
- `raw/`・`ttm/`の最終的な廃止／統合方法
- 統合スキーマへの実際の移行順序・既存consumer（reader.py・
  pipeline.py等）の切り替え計画
- EPS Analyzer変換ロジック（調整項目検出・DTA異常検知等）の
  配線変更実装
- filing_text吸収の実装
- 現行105銘柄ユニバースにJPM/GS等の伝統的金融機関・古典的REITが
  含まれておらず、これら業態でのフィールド網羅性は未検証。金融機関の
  FCFF/FCFE比較評価（TANUKI-FIN-2）に着手する際は、本設計が前提とする
  フィールド網羅性が同様に成立するか、別途検証が必要
- Equity（stockholders_equity）とNetIncome（net_income）の非支配持分
  （NCI）扱いの一貫性未検証。両フィールドとも現状の消費箇所
  （ROE計算・DuPont分解・投下資本計算等）はNCI除外版（親会社株主帰属分）
  のprimaryタグを使用しているが、NI側とEquity側でNCI包含・除外の定義が
  実際に揃っているかを検証したコード・調査は存在しない。ROE等の比率
  計算は分子・分母でNCI扱いが揃っていないと歪みが生じるため、Layer2
  統合時までに検証が必要（2026-07-24、Layer2設計調査で発見）

---

## 7. 関連BACKLOG項目

[[CAPEX-SIGN-UNNORMALIZED-1]]（対応完了）・
[[RICE-TTM-CAPEX-SUM-SIGN-1]]（対応完了）・
[[SCHEMA-STDEBT-COVERAGE-GAP-1]]・[[SCHEMA-SM-SGA-CONFLATION-1]]・
[[NORMALIZER-YTD-METADATA-STALE-1]]・
[[DOCS-SECDATA-NORMALIZED-DIR-STALE-1]]・
[[SEGMENT-FETCHER-DUPLICATE-ORPHAN-1]]・
[[SCHEMA-NORMALIZED-ANNUAL-NAMING-MISMATCH-1]]・
[[SEC-SUBMISSIONS-DUAL-FETCH-1]]・
[[SECDATA-COMPANYFACTS-OVERLOOKED-1]]・
[[Q4-IMPLIED-CALC-TRIPLICATION-1]]・
[[TTM-FLOW-FIELDS-FROZENSET-NONDETERMINISTIC-1]]
