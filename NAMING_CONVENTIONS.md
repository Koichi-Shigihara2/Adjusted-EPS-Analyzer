# NAMING_CONVENTIONS.md — 出力項目の命名規則

作成日: 2026-07-22
出発点: `OUTPUT_ITEMS_INVENTORY.md`（AS-ISスナップショット）・`TO_BE.md`
（統一定義設計）。特に`TO_BE.md`の⑫〜⑭群（計算ロジックベースの再点検で
新規発見した重複パターン）を踏まえて策定する。

対象外: BUY/WATCH・HypeCore推奨・tanuki_score等の最終判定ラベル系
（機能的重複調査は別途実施予定のため、本命名規則の適用対象外とする）。

実装（コード修正・リネーム）は行っていない。命名規則の策定のみ。

## 背景: 今回の調査で発見された2種類の命名問題

### 問題パターンA: 同名だが計算元が異なる
`net_cash`という同じ名前が、TANUKI VALUATION（`SECReader.get_net_cash()`、
SEC XBRL由来、四半期フォールバック・セクターガードあり）とSTONKS SILO
（`pipeline.py`、cash - yfinance `totalDebt`）で全く異なる計算ロジック・
データソースにより算出されていた（`TO_BE.md`⑫参照、AS-IS-025/134）。
25銘柄中23銘柄で乖離を確認し、NET/RBRK/RDWでは符号が反転していた。

### 問題パターンB: 同名だが定義（期間・基準）が異なる
`rule40`/`rule_of_40`という類似の名前が、HypeCore（YoY成長率＋純利益率、
変数名は"op_margin"だが実体は誤り）とSTONKS SILO（3年CAGR＋営業利益率）
で異なる期間・異なる利益率の定義により算出されていた（`TO_BE.md`⑬参照、
AS-IS-095/143）。25銘柄中23銘柄で乖離、複数銘柄で符号が反転していた。

`net_income`という同じ名前も、STONKS SILO（`common/sec_data`経由の年次
正規化パイプライン）とEPS Analyzer（自身の`extract_key_facts.py`による
四半期XBRL抽出）という独立した2パイプラインで、期間定義（単年度 vs
TTM）が異なるまま同名で出力されていた（`TO_BE.md`⑭参照、AS-IS-129/281）。

## 命名規則

### 規則1: 計算元（データソース）が異なる場合は、必ず接尾辞で区別する
同じ経済的概念（例: net_cash、PER、乖離率）を算出する場合でも、
参照するデータソースの系統が異なるなら、フィールド名だけで区別できる
接尾辞を付与する。

- SEC XBRL由来（`common/sec_data`経由）: `_sec`
- yfinance `.info`由来: `_yf`
- FRED由来: `_fred`
- 自サブシステム内の独自算出（他システムのSECデータを直接参照しない）: `_local`

例（`TO_BE.md`⑫の是正案）:
- TANUKI: `net_cash_sec`（`SECReader.get_net_cash()`由来、四半期フォールバックあり）
- STONKS SILO: 独自算出を廃止し`net_cash_sec`を直接参照（TO_BE.md⑫の統一定義通り）

### 規則2: 期間・時間軸が異なる場合は、必ず期間を明示する
「成長率」「利益」等、期間の取り方（直近実績YoY／3年CAGR／TTM／単年度FY）
によって値が大きく変わる指標は、フィールド名またはメタデータに期間を
必須で含める。

- 直近四半期比較: `_yoy`
- TTM（直近4四半期合算）: `_ttm`
- 単年度決算（Fiscal Year）: `_fy`
- 複数年CAGR: `_cagr{N}y`（例: `_cagr3y`）

例（`TO_BE.md`⑬の是正案）:
- HypeCore: `rule40_yoy_netmargin`（旧名`rule40`。YoY成長率＋純利益率であることを明示）
- STONKS SILO: `rule40_cagr3y_opmargin`（旧名`rule_of_40`。3年CAGR＋営業利益率であることを明示）

例（`TO_BE.md`⑭の是正案）:
- STONKS SILO: `net_income_fy`（単年度決算）
- EPS Analyzer: `net_income_ttm`（TTM合算）

### 規則3: 変数名は実際に計算している内容と一致させる（誤称の禁止）
変数名が示唆する概念と、実際の計算式が乖離してはならない。

例（是正対象、`TO_BE.md`⑬関連）: HypeCoreの`op_margin`は実際には
`net_income / revenue`（純利益率）を計算しているが、変数名は
「営業利益率(operating margin)」を示唆する。`net_margin`へのリネームを
推奨する（実装は範囲外、命名規則としての記録のみ）。

### 規則4: 生データを直接転記する項目には、出所（provenance）を明示する
複数サブシステムが同一の生データファイル（例:
`common/sec_data/data/{TICKER}/annual_*.json`）を参照している場合、
その事実を各サブシステムの出力JSONに`{フィールド名}_source`または
`provenance`という付随フィールドとして明示する。これにより、片方の
抽出ロジックが変更された際に、もう片方が影響を受けることを利用者が
追跡できるようにする（`TO_BE.md`⑦・⑫・⑭で推奨した対応の一般化）。

例:
```json
{
  "fcf_history": [...],
  "fcf_history_source": "common/sec_data/data/{TICKER}/annual_*.json#cf.free_cash_flow"
}
```

### 規則5: 「唯一の正」が定められた概念は、参照元システムを明示する
複数サブシステムが同じ値を参照する設計（`TO_BE.md`①⑤⑧のようにパススルー
実装が正しいパターン）の場合、パススルー先のフィールド名にも同一の
ベース名を用い、独自の別名を付けない。

例: EPS Analyzerの`deviation_rate`はTANUKIの`upside_percent`をそのまま
参照するパススルーであるため、命名としても`upside_percent`（またはそれを
明示するエイリアス`upside_percent_from_tanuki`）を用いることが望ましく、
無関係な独自名`deviation_rate`を新たに作らない方が誤解を防げる
（既存実装の変更は範囲外、新規開発時の指針として記録）。

### 規則6: 最終判定ラベル系は本規則の適用対象外
`tanuki_score`・`funda_score`・`timing_score`・HypeCoreの`stage`・
推奨（買い/保有/売り）・STONKS SILOの`overall_score`/`overall_verdict`・
MACRO PULSEのRECESSION RISK SCORE表示・EPS Analyzerの`health`等、
複数の入力を統合した最終判定ラベルは、命名の統一よりも「各サブシステム
固有の判定軸である」ことを明示する現状の命名（サブシステム名を冠する等）
の方が実務上は適切であり、本ドキュメントの規則1〜5は適用しない。
これらの機能的重複（用途が実質的に同じかどうか）は別途のステップで
調査する。

## 適用チェックリスト（新規フィールド追加時）

新しい出力項目を追加する際、以下を確認する:

1. 同じ名前が他サブシステムに既に存在しないか（`OUTPUT_ITEMS_INVENTORY.md`
   を検索する）。存在する場合、計算ロジック・データソースが同一か確認する。
2. 同一でない場合、規則1（データソース接尾辞）または規則2（期間接尾辞）
   に従って名前を分ける。
3. 生データを他サブシステムと共有する場合、規則4（provenance明示）に従う。
4. 既存の「唯一の正」を参照する場合、規則5に従い独自の別名を作らない。
5. 変数名が実際の計算内容と一致しているか確認する（規則3）。

## 参照

- `OUTPUT_ITEMS_INVENTORY.md`: AS-ISスナップショット（全284項目、AS-IS-001〜284）
- `TO_BE.md`: 統一定義設計（①〜⑭群、うち⑫⑬⑭が本命名規則の直接の根拠）
