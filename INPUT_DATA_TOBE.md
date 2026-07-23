# INPUT_DATA_TOBE.md — 一次データ層のTO-BE設計

作成日: 2026-07-23
出発点: `FIELD_DEFINITIONS.md`（499項目の計算式最小単位分解、完了済み）の
「データ取得元」列、`CONCEPT_PARAMETER_VARIATIONS.md`軸2（取得元・データ
ソース）、`OUTPUT_ITEMS_INVENTORY.md`「外部データ取得経路」セクション、
`NAMING_CONVENTIONS.md`規則4（provenance明示）。

## 本ドキュメントの位置づけ

`FIELD_DEFINITIONS.md`で499項目全件（一次データ42件＋導出データ392件、
残り65件は手動入力・移送・システム設定）の計算式を最小単位まで分解した
結果、これらを充足するために実際に必要な一次データ（外部ソース由来の
生データ）の全体像が判明した。本ドキュメントは、この一次データ層を
**現状の実装（複数経路・複数ファイルでの重複取得）にとらわれず、白紙から
「あるべき姿（TO-BE）」として設計する**。

現状（AS-IS）の実装との具体的な比較・移行計画は次ステップで行う。
本ドキュメントは設計のみを記録し、実装（コード修正）は一切行っていない。

**更新（2026-07-23、`INPUT_DATA_AS_IS.md`との突合結果を反映）**: `INPUT_DATA_AS_IS.md`
作成時に実コードを直接確認した結果、本ドキュメントの初版（本更新前）には
8件の考慮漏れがあった。該当箇所（1-D手動入力データ、2-A SEC EDGAR層）に
是正を反映済み。判定の詳細・根拠は`INPUT_DATA_AS_IS.md`「考慮漏れの判定
結果」を参照。

---

## ステップ1: 必要な一次データの棚卸し（ソース別・重複排除済み）

`FIELD_DEFINITIONS.md`の「データ取得元」列を全件走査し、499項目が最終的に
依存する一次データを、実際にソースコードを直接確認しながら4系統に分類した
（Grok/AI生成コンテンツは、この一次データ層を入力として消費する側であり、
一次データそのものではないため対象外とする。5分類上も「導出データ」に
分類済み）。

### 1-A. SEC EDGAR（XBRL構造化データ）

499項目のうち、TANUKI VALUATION／HypeCore／STONKS SILO／Discover／
TANUKI TAIL／EPS Analyzerの各サブシステムが依存する財務諸表項目を、
「銘柄×決算期（四半期・通期）」単位のXBRLファクトとして整理すると、
以下の一意なファクト種別に集約される（同一概念が複数サブシステムの
式に登場しても、必要なXBRLタグ自体は1種類）。

| ファクト種別 | 代表XBRLタグ相当 | 用途（依存する主な計算） |
|---|---|---|
| 売上高 | `Revenues`等 | PSR分母、成長率、Rule of 40成長率項、moat_score fcf_norm分母 |
| 純利益 | `NetIncomeLoss` | EPS、rule40純利益率項、net_income系 |
| 営業利益 | `OperatingIncomeLoss` | rule_of_40営業利益率項、moat_score ROIC計算のNOPAT |
| 売上総利益 | `GrossProfit`（欠如時はRevenue−COGSで代替） | moat_score gross_margin |
| 営業キャッシュフロー | `NetCashProvidedByUsedInOperatingActivities` | FCF計算、STONKS SILO runway |
| 設備投資（CapEx） | `PaymentsToAcquirePropertyPlantAndEquipment`等（符号が発行体によって正負混在） | FCF計算（符号正規化必須、AS-IS-071既知バグの根本原因） |
| ファイナンスリース関連 | 各種リース系タグ | FCF計算の`FinanceLease`控除項 |
| 研究開発費 | `ResearchAndDevelopmentExpense` | moat_score・成熟利益計算の投資強度分母 |
| 販管費・S&M | `SellingGeneralAndAdministrativeExpense`等（S&M単独タグは発行体により非開示） | 投資強度分母（欠如時の扱いが既知の課題） |
| 株式報酬（SBC） | `ShareBasedCompensation` | RICE Q項、純利益への足し戻し |
| 現金・現金同等物 | `CashAndCashEquivalentsAtCarryingValue` | net_cash計算 |
| 短期投資 | `ShortTermInvestments` | net_cash計算 |
| 長期有利子負債 | `LongTermDebtNoncurrent`等 | net_cash・total_debt計算 |
| 短期有利子負債 | `LongTermDebtCurrent`等 | net_cash・total_debt計算 |
| 希薄化後株式数 | `WeightedAverageNumberOfDilutedSharesOutstanding` | EPS、1株あたり価値、希薄化率 |
| セグメント別売上・KPI | `StatementBusinessSegmentsAxis`配下の各種タグ | TANUKI TAILのセグメントKPI抽出 |
| 内部統制関連テキスト | 10-Q Item4本文（非XBRL、全文テキスト） | TANUKI TAILの内部統制監視 |
| 直近提出日・提出書類一覧 | EDGAR submissions API（`data.sec.gov/submissions/`） | 新規提出監視、CIKルックアップ |

**必要なアクセス方式**: (a) XBRL構造化ファクト取得（Company Facts API相当）、
(b) 提出書類一覧・メタデータ取得（submissions API）、(c) 10-Q本文の
全文テキスト取得（Archives経由）——の3方式に整理できる。

### 1-B. yfinance（株価・市場データ・企業属性スナップショット）

| データ種別 | 内容 | 用途 |
|---|---|---|
| 個別銘柄の価格・出来高履歴 | 日次OHLCV（少なくとも過去252営業日） | 移動平均・乖離率・ボラティリティ・52週高安値・出来高比 |
| 個別銘柄の`.info`属性 | trailingPE/forwardPE/pegRatio/priceToSalesTrailing12Months/enterpriseToEbitda/forwardEps/targetMeanPrice/dividendYield/payoutRatio/heldPercentInsiders/beta/shortRatio/marketCap/sector/industry | PER/PEG/PSR/EV_EBITDA等の倍率系、moat_score・timing_score入力 |
| アナリスト格上げ・格下げ履歴 | `upgrades_downgrades` | analyst_upgrade_rate/downgrade_rate |
| 指数・ETF・商品の価格・出来高履歴 | S&P500(`^GSPC`)、NASDAQ、NYSE Composite(`^NYA`)、日経平均、VIX(`^VIX`)、VIX9D(`^VIX9D`)、WTI原油、金、HYG、LQD、QQQ、SPY、RSP、IVW（グロース）、IVE（バリュー）、RUT（小型株）、TLT、SHV、USD/JPY | MACRO/Market Pulseの各種指標、asset_flow、breadth計算 |
| S&P500構成銘柄一括データ | 構成銘柄リスト＋日次OHLCV一括ダウンロード | market breadth（騰落レシオ・新高値新安値・NH-NL等）算出 |

**フォールバック方針の設計**: `^IRX`（3ヶ月T-Bill）はGitHub Actions環境
からの取得が構造的に不安定であることが既に判明しているため、TO-BE設計
でも短期金利は最初からFRED `DGS3MO`を正とし、yfinanceでの取得を試みない
（現状のMarket Pulseが既に採用している回避策を、設計レベルの標準として
採用する）。

### 1-C. FRED（マクロ経済系列）

ソースコード（`05_main.py`の`INDICATOR_CONFIG`辞書、`update_liquidity_csv()`、
Market Pulseの`collect_and_send.py`/`backfill_tech_pulse.py`）を直接確認し、
必要なFRED系列を重複なく24系列に整理した。

| 系列コード | 内容 | 用途 |
|---|---|---|
| `T10Y2Y` | 10年債-2年債利回り格差 | RECESSION RISK SCORE・イールドカーブ判定 |
| `BAMLH0A0HYM2` | ハイイールド債OASスプレッド | RECESSION RISK SCORE・流動性カード（現状3箇所で重複取得、後述） |
| `GACDFSA066MSFRBPHI` | フィラデルフィア連銀製造業景況指数 | RECESSION RISK SCORE |
| `CFNAI` | シカゴ連銀全米活動指数 | RECESSION RISK SCORE |
| `IC4WSA` | 新規失業保険申請件数4週平均 | RECESSION RISK SCORE |
| `MICH` | ミシガン大学インフレ期待(1年) | RECESSION RISK SCORE |
| `T5YIE` | 5年ブレークイーブンインフレ率(ミシガン5年の市場ベース代替) | RECESSION RISK SCORE |
| `UMCSENT` | ミシガン大学消費者信頼感指数 | RECESSION RISK SCORE |
| `PERMIT` | 住宅着工許可件数 | RECESSION RISK SCORE |
| `SAHMCURRENT` | Sahm Ruleリセッション指標 | RECESSION RISK SCORE |
| `PAYEMS` | 非農業部門雇用者数(NFP) | マクロサプライズ検知 |
| `VIXCLS` | VIX恐怖指数(FRED版) | MACRO PULSE文脈記録 |
| `SP500` | S&P500指数終値 | MACRO PULSEティッカー表示 |
| `DGS1` | 1年国債利回り | 利下げ/利上げ織り込み計算 |
| `DFEDTARU`/`DFEDTARL` | FF金利誘導目標レンジ上限/下限 | FF金利現在値 |
| `FEDFUNDS` | 実効FF金利(フォールバック) | FF金利現在値のフォールバック |
| `WALCL` | FRB総資産(バランスシート) | NET LIQUIDITY計算 |
| `WTREGEN` | 財務省一般勘定(TGA)残高 | NET LIQUIDITY計算・ステルス供給/吸収判定 |
| `RRPONTSYD` | オーバーナイトリバースレポ残高 | NET LIQUIDITY計算・ステルス供給/吸収判定 |
| `WRBWFRBL` | 銀行準備預金残高 | ステルス供給/吸収判定の補助指標 |
| `M2SL` | M2マネーサプライ | 流動性カード表示 |
| `VXNCLS` | ナスダック版VIX(VXN) | Tech Pulse divergence計算 |
| `DGS3MO` | 3ヶ月国債利回り | asset_flow短期金利(yfinance `^IRX`の構造的フォールバック先) |

**設計上の指摘**: `TANUKI VALUATION`の`risk_free_rate`（DCF計算のCAPM構成
要素、現状は`0.043`のハードコード定数）は、本来であればこのFRED系列層
から`DGS10`（10年国債利回り、現状は未取得）等を都度取得すべき性質の
データである。TO-BE設計では、DCF計算が参照する「無リスク金利」も
この一次データ層の管理対象に含める（現状比較・実装要否の判断は次ステップ）。

### 1-D. 手動入力データ（人手設定・承認済み設定ファイル）

| ファイル | 内容 | 更新方式 |
|---|---|---|
| `config/segment_config.json` | セグメント別加重成長率の手動設定 | admin.html経由 |
| `config/growth_options_config.json` | 成長オプション（TAM/浸透率/FCFマージン等）の銘柄別手動設定 | admin.html経由 |
| `config/maturity_config.json` | DCF成熟プロファイル（2段階/3段階、フェーズ年数・成長率）の銘柄別設定 | admin.html経由 |
| `config/rpo_config.json` | RPO（残存履行義務）調整設定 | admin.html経由 |
| `config/beta_config.json` | β値のオーバーライド（月次自動更新＋範囲外銘柄の手動設定） | GitHub Actions月次自動更新＋手動 |
| `config/discover_config.json` | 銘柄別テーマ・区分・メモ | admin.html経由 |
| `config/theme_config.json` | テーママスタ（ID/ラベル/カラー） | admin.html経由 |
| `config/portfolio.json` | 保有株数・平均取得単価（ブローカー別） | 手動編集（書き込みスクリプトなし）。**現状`docs/portfolio/data/portfolio.json`にバイト完全一致の重複コピーが存在し、同期処理が存在しない（`INPUT_DATA_AS_IS.md`2-D参照）。TO-BEでは`config/portfolio.json`を唯一の保持場所とし、表示側は都度この1箇所を参照する設計とする** |
| `config/tail_kpi_map.json` | TANUKI TAILのKPI設定（AI提案＋人手確定のハイブリッド） | kpi_proposer.py提案→人手確定。**現状`config/`ではなく`docs/portfolio/tail/data/`配下（生成データと同居）に置かれているため、TO-BEでは他の手動設定ファイルと同様`config/`配下への集約を設計方針とする** |
| `config/fcf_conversion_config.json`/`ticker_overrides`類 | Damodaran業種別FCF変換率等の銘柄別上書き | 手動設定。**現状は`src/value/tanuki_valuation/`直下（`config/`外）に配置されており、TO-BEでは`config/`への集約を設計方針とする** |
| `config/monitor_tickers.yaml`（**考慮漏れ、2026-07-23追加**） | 監視銘柄マスタリスト（全サブシステムが対象とする銘柄の起点） | 手動編集。全ての一次データ取得（SEC EDGAR/yfinance/FRED）に先立って参照される最上流の設定であり、一次データ層の設計対象として明示する |
| `config/prompts.yaml`（**考慮漏れ、2026-07-23追加、重要**） | Grok/AI分析プロンプトテンプレート集約（EPS調整分析・カタリスト予測・TANUKI TAIL Stage2シナリオ等） | 手動編集。392件の導出データの相当数がAI生成コンテンツであり、その生成品質・再現性を左右するプロンプト自体を一次データ層の管理対象として扱う（プロンプトの変更履歴・バージョン管理も将来的な設計対象） |
| `config/split_history.yaml`（**考慮漏れ、2026-07-23追加**） | 株式分割の遡及補正用手動記録（比率・効力発生日） | 手動編集。希薄化後株式数の正規化（複数の計算式が依存する基礎データ）に直接影響する |
| `config/sectors.yaml`（**考慮漏れ、2026-07-23追加**） | セクター/業種のキーワードマッピング | 手動編集。β・成長率のセクターデフォルト判定に使われる基礎データ |
| `config/adjustment_items.json`（**考慮漏れ、2026-07-23追加**） | EPS Analyzerの調整項目カテゴリ・XBRLタグ定義 | 手動編集。EPS調整ロジックの根幹となる定義データ |
| `config/cik_lookup.csv`／`config/cik_lookup_result.json`（**考慮漏れ、2026-07-23追加**） | Ticker→CIKマッピング（1-A SEC EDGAR取得の前提データ） | 半自動（`TANUKI_CIK_Lookup.yml`手動実行）。1-AのSEC EDGAR取得経路の前提条件として、本来1-Aと合わせて棚卸しすべきだった |

**対象外と判定した項目（2026-07-23、`INPUT_DATA_AS_IS.md`との突合で確認）**:
`config/warn_acknowledged.json`（品質ゲートの確認済み状態台帳）・
`config/workflow_dependencies.json`（ワークフロー依存関係定義）は、
いずれも499項目のいずれの計算にも入力されない運用状態データ・
メタ設定であり、5分類上は「システム設定データ」に相当するため、
一次データ層の設計対象には含めない。

---

## ステップ2: 保持方法の設計

### 2-A. SEC EDGAR層: 銘柄×決算期の正規化ストアに一本化

**設計方針**: XBRLファクトは「銘柄×決算期（四半期/通期）」を主キーとする
単一の正規化ストアに保持する。現状`common/sec_data/`が担っているこの役割を
TO-BEの唯一の正とし、**EPS Analyzer・TANUKI TAILが現在独自に持つ3系統の
独立SEC EDGARアクセス（B・C1〜C3）は、このストアの利用に一本化する**
（提出書類テキスト全文やセグメントKPIのような、現状の正規化ストアが
保持していないデータ種別は、同じストアの中に別テーブル/別ファイルとして
追加する形で吸収し、別パイプラインとして並存させない）。

**統合スコープの明確化（2026-07-23、`INPUT_DATA_AS_IS.md`との突合で是正）**:
「単一の正規化ストア」への一本化と述べたが、現状`common/sec_data/`自体が
既に`data/{TICKER}/annual_*.json・quarterly_*.json`に加え、`raw/`
（正規化前の生XBRL）・`normalized/`（`data/quarterly_*.json`とは別スキーマの
独立した正規化四半期データ）・`ttm/`（TTM系列）という**最低6ファイル系統**に
分岐している。特に`normalized/{TICKER}_quarterly_normalized.json`は
stock.htmlのキャッシュフロー分析セクション（CapEx符号未処理バグ、
`FIELD_DEFINITIONS.md`AS-IS-071）が直接参照する独立スキーマであるため、
統合時は「どちらのスキーマを正とするか」を明示的に決定する必要がある
（本ドキュメントは設計のみのため、この決定自体は次ステップの移行計画に
委ねる）。TO-BEの統合対象は`data/`だけでなく`raw/`・`normalized/`・
`ttm/`を含めた全系統である旨をここに明示する。

保持構造の案:
```
common/sec_data/data/{TICKER}/
  annual_{FY}.json        # 通期ファクト（正規化済み）
  quarterly_{FYQ}.json    # 四半期ファクト（正規化済み）
  filing_meta.json        # 提出日・CIK・最終確認日等のメタ情報
  segments/{FYQ}.json     # セグメント別KPI（新規吸収）
  filing_text/{accession}.json  # 10-Q本文抽出結果（新規吸収）
```

四半期データへのフォールバック（TANUKI側の`get_net_cash()`が既に持つ
設計）は、正規化ストア自身の標準機能として全サブシステムに開放する
（STONKS SILO等が年次データのみ参照する現状の制約を、ストア側の
API仕様に含める）。

### 2-B. yfinance層: 更新頻度でサブレイヤーを分離

**設計方針**: yfinanceのデータは性質上、更新頻度が大きく異なる3つの
サブレイヤーに分割して保持する。

1. **日次スナップショット層**（毎営業日更新）: 個別銘柄・指数・ETF・
   商品の価格/出来高。`common/market_data/daily/{SYMBOL}.json`（または
   時系列DB）に、シンボルをキーとして一元管理する。個別銘柄・指数・ETFを
   区別せず同一スキーマで扱う（現状「個別銘柄用」「指数用」「ETF用」が
   別ファイル・別関数で管理されている構造を統合する）。
2. **準静的属性層**（週次〜月次更新で十分）: `.info`辞書由来の
   PER/PEG/PSR/EV_EBITDA/配当利回り/配当性向/インサイダー保有/β/
   セクター/業種等。日次で再取得する必要性が薄いため、独立した更新
   スケジュールで`common/market_data/attributes/{TICKER}.json`に保持する。
3. **イベント履歴層**（発生都度追記）: アナリスト格上げ・格下げ履歴。
   `common/market_data/analyst_history/{TICKER}.json`に追記型で保持し、
   月次集計（3ヶ月移動平均等）は参照側（HypeCore等）が都度計算する。

S&P500構成銘柄の一括ダウンロード（market breadth用）は、上記1の日次
スナップショット層と同じ取得バッチ内で完結させ、個別銘柄の日次取得と
可能な限り1回のAPI呼び出しに統合する。

### 2-C. FRED層: 系列単位の時系列ストア

**設計方針**: FRED系列は「系列コード」を主キーとする単一の時系列ストア
に保持する。`common/macro_data/series/{SERIES_ID}.csv`（または同等の
時系列形式）に、観測日・値・（該当する場合は）公表日・改定履歴を保持する。

MACRO PULSEの`INDICATOR_CONFIG`が持つ`fred_release_id`/`obs_to_release_lag`
等のメタ情報（サプライズ検知・重複判定に必須）は、系列コードに紐づく
メタデータとしてこのストアの一部に統合する（現状MACRO PULSE内部にのみ
存在するメタ情報を、FRED層全体で共有可能な形にする）。

Market Pulse固有の`VXNCLS`/`DGS3MO`も、MACRO PULSEが使う`T10Y2Y`等と
全く同じストア・同じスキーマで管理し、「MACRO PULSE用FRED」「Market
Pulse用FRED」という現状のサブシステム別分断を解消する。

### 2-D. Provenance（出所・取得日時）の付与設計

`NAMING_CONVENTIONS.md`規則4（生データを直接転記する項目への出所明示）
を一次データ層自体にも適用する。各データポイントに以下を付随させる:

```json
{
  "value": ...,
  "as_of": "2026-07-23",           // データが表す時点（決算期・観測日等）
  "fetched_at": "2026-07-23T07:15:00+09:00",  // 実際に取得した日時
  "source": "SEC_EDGAR_XBRL",      // SEC_EDGAR_XBRL / YFINANCE / FRED / MANUAL
  "source_detail": "10-Q accession 0000320193-26-000050",  // 具体的な出所
  "fallback_used": false           // フォールバック値を採用した場合true
}
```

これにより、①どの時点のデータか（`as_of`）と②いつ取得したか
（`fetched_at`）を区別できる（現状のMACRO PULSE/Market Pulse間の
非同期実行タイミングのズレのような問題を、後から機械的に検知できる
ようにするための最小限のメタデータ）。四半期フォールバック
（TANUKIのnet_cash計算等）を使った場合は`fallback_used`で明示し、
利用側が「正規のannualデータか、フォールバック値か」を区別できる
ようにする。

---

## ステップ3: 取得方法の設計

### 3-A. 取得頻度・タイミングの設計

| 対象 | 頻度 | 想定タイミング | 設計根拠 |
|---|---|---|---|
| SEC EDGAR新規提出監視（submissions API） | 日次（平日） | 1日1回、市場クローズ後 | 10-Q/10-Kは不定期提出のため、ポーリングで検知する以外に方法がない。現状TANUKI TAILが平日17:00 JSTで実施している頻度を踏襲すれば十分 |
| SEC EDGAR XBRLファクト取得（新規提出検知時のみ） | イベント駆動 | 新規提出検知の都度 | 決算期ごとにしか値が変わらないデータを毎日再取得する必要はない |
| yfinance日次スナップショット（価格・出来高） | 日次（平日） | 市場クローズ後、1回のみ | 現状11ファイル（`INPUT_DATA_AS_IS.md`で実測、既存記載の「13〜14」はF&G Level2 TQQQトレーダー等の対象外プロジェクト混入分を含む数だったと判明）がそれぞれ独自のタイミングで同じ銘柄の価格を取得しているのを1回に統合する |
| yfinance準静的属性（.info由来） | 週次 | 週次バッチ1回 | PER・β・配当性向等は日次で変動しても実務上の意味が薄い。過度な頻度はAPI呼び出し回数の浪費 |
| yfinanceアナリスト履歴 | 週次 | 週次バッチ1回 | 格上げ・格下げは高頻度イベントではない |
| FRED系列 | 各系列の公表頻度に整合（日次系列は日次、月次系列は月次） | 系列ごとに設定された`obs_to_release_lag`を考慮した日次ポーリング | 月次公表データを日次ポーリングすること自体は問題ないが（値が変わらない日は差分なしとして処理）、重複排除（`dedupe_new_rows()`相当）は一次データ層側で一元的に行う |
| 手動入力データ | イベント駆動（admin.html保存時） | 保存操作の都度 | 定期実行は不要。ただし保存内容のバリデーション（現状ゼロ、既知の問題）は取得方法の設計とは別軸のため本ドキュメントでは扱わない |

### 3-B. 単一共有レイヤーとしてのアクセス設計

全サブシステムが一次データ層を参照する際、**個々のサブシステムが外部
APIを直接呼び出すことを禁止し、必ず共有アクセサ経由で取得済みデータを
読む**という設計を基本方針とする。

```
common/
  sec_data/       # 既存。SEC EDGAR正規化ストア（唯一の正、2-A参照）
    fetcher.py    # 外部取得を行う唯一のモジュール
    reader.py     # 全サブシステムが読み取りに使う唯一のモジュール
  market_data/    # 新設。yfinance統合層（2-B参照）
    fetcher.py    # 外部取得を行う唯一のモジュール（日次/週次バッチを内包）
    reader.py     # 全サブシステムが読み取りに使う唯一のモジュール
  macro_data/     # 新設。FRED統合層（2-C参照）
    fetcher.py    # 外部取得を行う唯一のモジュール
    reader.py     # 全サブシステムが読み取りに使う唯一のモジュール
```

**この設計が現状の重複取得を構造的に防止する理由**:
- SEC EDGAR: 現状7系統（`common/sec_data`本体1・EPS Analyzer独自1・
  TANUKI TAIL独自3ファイル・手動運用2）に分散しているアクセスコードを
  `common/sec_data/fetcher.py`1箇所に統合すれば、新規サブシステムが
  「自分で取得する」という選択肢自体を持たなくなる（`reader.py`しか
  importできない設計にする）。
- yfinance: 現状11ファイル（`INPUT_DATA_AS_IS.md`実測値）が個別に`yf.Ticker()`/`yf.download()`を
  呼んでいる状態を、`common/market_data/fetcher.py`1箇所（＋日次/週次の
  バッチ実行スケジュール）に統合すれば、同一銘柄・同一指数への重複
  リクエスト（現状確認済み: 現在株価2系統、PER/PEG/PSR/EV_EBITDA3系統、
  アナリストコンセンサス2系統、β3系統、`^GSPC`のMarket Pulse内4重取得等）
  が構造的に発生しなくなる。
- FRED: 現状MACRO PULSE内部2箇所＋Market Pulse1箇所で計3箇所から独立に
  取得している`BAMLH0A0HYM2`（HYスプレッド）のような事例は、
  `common/macro_data/fetcher.py`1箇所に統合すれば、同一系列への
  複数回リクエスト自体が発生しない設計になる。

**サブシステム固有の後処理は引き続き各サブシステム側で行う**: この
統合はあくまで「取得・保持」の一元化であり、「加工・表示」（例:
Market PulseのHYG/LQD比率による代理判定、MACRO PULSEの実際のスプレッド
値としての利用）はサブシステムごとの目的に応じて個別に行ってよい
（`TO_BE.md`⑮群で既に確認済みの設計思想と整合させる）。

### 3-C. 「唯一の正」と接尾辞規則の適用

一次データ層自体が複数の経路を持つことがないため、`NAMING_CONVENTIONS.md`
規則1（データソース接尾辞）は主に導出データ側（一次データ層を加工した後の
出力フィールド）に適用される。一次データ層のフィールド名自体は、
ソースの性質を示す前置（`sec_`/`yf_`/`fred_`）を持つ形で統一し、
各サブシステムが「唯一の正」を参照していることをコード上も明示する。

---

## 次ステップへの申し送り

- **2026-07-23、`INPUT_DATA_AS_IS.md`との突合完了**: 現状（AS-IS）の実装
  との項目単位の比較を実施済み（比較結果・考慮漏れの判定は
  `INPUT_DATA_AS_IS.md`参照）。本ドキュメントの1-D（手動入力データ6件
  追加）・2-A（SEC EDGAR統合スコープの明確化）に是正を反映した
- 移行コスト評価・移行手順の設計（何を・どの順序で・どう移行するか）は
  引き続き次ステップで行う（本ドキュメント自体は設計のみに留める）
- `common/market_data/`・`common/macro_data/`という新設レイヤーの命名・
  配置場所は暫定案であり、既存の`common/`配下の他モジュールとの整合は
  次ステップで確認する
- risk_free_rate（TANUKI VALUATION、現状0.043ハードコード）をFRED
  `DGS10`経由に切り替えるかどうかは設計上の指摘に留め、実装可否の判断は
  次ステップに委ねる
- Discoverのconfig二重管理（`admin.html`保存先と`docs/discover/index.html`
  参照先の不一致）は一次データ層の設計とは別軸の問題（手動入力データの
  同期バグ）であり、本ドキュメントでは設計対象に含めていない。ただし
  Portfolio（`config/portfolio.json`と`docs/portfolio/data/portfolio.json`
  の重複）については、同型の同期リスクとして一次データ層の「唯一の
  保持場所」設計（1-D）に含めた
- `common/sec_data`の`raw/`・`normalized/`・`ttm/`統合時にどちらのスキーマ
  を正とするか（特に`normalized/`をAS-IS-071バグの温床として廃止するか、
  修正して存置するか）の決定は、次ステップの移行計画に委ねる
