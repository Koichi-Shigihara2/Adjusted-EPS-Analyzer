# PROJECT_STATUS.md — 新一次データベース構築プロジェクト進捗

作成日: 2026-07-23
更新日: 2026-07-24（一次データベース設計の投資調査で判明した3件の実態を
反映。①INPUT-A-016〈セグメント別売上・KPI〉を正式ASC280セグメントから
`tail_kpi_map.json`ベースの銘柄固有カスタムKPI〈フェーズ1統合スコープ外〉
に訂正、②Adjusted EPS算出専用の税務・一過性項目タグ群52種を`INPUT-A-048`
として新規追加、③`common/sec_data/data/{TICKER}/company_facts.json`
〈SEC EDGAR company_facts API生レスポンス全量、既存〉がLayer1（無加工
アーカイブ）の要件を既に満たしていることが判明し、新規構築不要と判明。
分類A件数を47件→48件に更新。詳細は`INPUT_DATA_TOBE.md`該当箇所・
BACKLOG.md `[[SECDATA-COMPANYFACTS-OVERLOOKED-1]]`参照）
位置づけ: 「新一次データベース構築プロジェクト」（2段階プロジェクトの
第1段階＝一次データ層の構築・過去データ移管、第2段階＝導出データ層
〈`FIELD_DEFINITIONS.md`499項目〉の管理方法検討）の進捗を追跡する。
仕様書本体は`docs/architecture/new_data_platform/`を参照。

2026-07-24より`common/sec_data/` 統合（フェーズ1の一部）が**構築中**。
他コンポーネント（`common/market_data/`・`common/macro_data/`等）は
未着手のまま（設計フェーズは2026-07-22〜23に完了済み）。

## 一次データ層の総数（`INPUT_DATA_TOBE.md`3分類、2026-07-24時点）

| 分類 | 件数 | ID範囲 | フェーズ1・2のスコープ内か |
|---|---|---|---|
| A. 一次データ本体 | 48件 | `INPUT-A-001`〜`048` | **対象**（一次データ層構築の主対象） |
| B. 取得前提条件 | 3件 | `INPUT-B-001`〜`003` | **対象**（SEC EDGAR取得〈`INPUT-B-002`/`003`〉・全体の対象銘柄決定〈`INPUT-B-001`〉の前提として、分類Aの取得と一体で構築する） |
| C. 導出データの入力 | 14件 | `INPUT-C-001`〜`014` | **対象外**（一次データそのものではなく`FIELD_DEFINITIONS.md`導出データ側の入力のため、フェーズ3〈導出データ層の管理方法検討〉で扱う） |
| **合計** | **65件** | — | — |

---

## フェーズ1: 一次データ層の構築（分類A48件＋分類B3件が対象）

| コンポーネント | 状態（未着手/構築中/完成） | 備考 |
|---|---|---|
| `common/sec_data/` 統合（raw/normalized/ttm統合含む、`INPUT-A-001〜018`対応） | 構築中（着手日2026-07-24） | `INPUT_DATA_TOBE.md` 2-A参照。統合スコープに`raw/`・`normalized/`・`ttm/`の3系統を含む旨を明記済み。`SEC_EDGAR_LAYER_DESIGN.md`のフェーズA〜C（Layer3スキーマ構築・`layer3_builder.py`実装・`ttm_calculator.py`snake_case統一）が実装済み。2026-07-29、フェーズC移行時の消費者横展開漏れ（`data_fetcher.py`・`audit.py`が旧PascalCaseキー参照のまま取り残されRICEスコア全銘柄停止）を`[[TTM-PASCALCASE-KEY-STALE-1]]`として修正完了（コミット
`a7b840c32fde3b6619707f7a7c588baeaed12fd1`、`BACKLOG_DONE.md`参照）。残課題: `[[LAYER3-COGS-STRUCTURAL-GAP-16TICKERS-1]]`・`[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]`等、`BACKLOG.md`該当項目を参照 |
| `common/market_data/` 新設（yfinance統合層、`INPUT-A-019〜023`対応） | 未着手 | `INPUT_DATA_TOBE.md` 2-B参照。日次/週次属性/イベント履歴の3層分離設計 |
| `common/macro_data/` 新設（FRED統合層、`INPUT-A-024〜047`対応） | 未着手 | `INPUT_DATA_TOBE.md` 2-C参照。系列単位の時系列ストア設計 |
| 取得前提条件の一元管理（`INPUT-B-001〜003`） | 未着手 | `INPUT_DATA_TOBE.md`分類B参照。監視銘柄マスタ・CIKマッピングの管理方法は分類Aの取得と一体で設計する |
| provenanceメタデータ標準化 | 未着手 | `INPUT_DATA_TOBE.md` 2-D参照（`as_of`/`fetched_at`/`source`/`source_detail`/`fallback_used`） |
| fetcher/reader分離アクセス制御 | 未着手 | `INPUT_DATA_TOBE.md` 3-B参照 |

## フェーズ2: 過去データ移管（分類A48件＋分類B3件が対象）

| データソース | 状態 | 対象範囲 |
|---|---|---|
| SEC EDGAR既存データ（`INPUT-A-001〜018`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-A・2-A参照（実測7経路） |
| yfinance既存データ（`INPUT-A-019〜023`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-B・2-B参照（実測11ファイル） |
| FRED既存データ（`INPUT-A-024〜047`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-C・2-C参照（実測2サブシステム） |
| 取得前提条件（`INPUT-B-001〜003`） | 未着手 | `INPUT_DATA_AS_IS.md` 1-D・1-E参照（`monitor_tickers.yaml`・`cik_lookup.csv`／`cik_lookup_result.json`はいずれも現状`config/`配下に存在確認済み） |

**分類Cはフェーズ1・2の対象外**: `config/segment_config.json`等14件
（`INPUT-C-001〜014`）は一次データそのものではなく`FIELD_DEFINITIONS.md`
導出データ側（392件）が消費する入力であるため、一次データ層の構築・
移管スコープには含めない。Portfolio二重保持（`INPUT-C-008`）・
`config/`外配置（`INPUT-C-009`/`010`）等の是正要否は、フェーズ3
（導出データ層の管理方法検討）で扱う。

## フェーズ3: 導出データ層の管理方法検討（分類C14件を含む）

| 項目 | 状態 |
|---|---|
| `FIELD_DEFINITIONS.md` 499項目の新DB参照への切替方針 | 未着手（フェーズ1・2完了後に着手） |
| 分類C14件（`INPUT-C-001〜014`）の管理方法検討（`config/`外配置2件の是正、Portfolio二重保持の是正等） | 未着手（フェーズ1・2完了後に着手） |

---

## 関連BACKLOG項目

`NETCASH-DUAL-CALC-1`・`NETINCOME-DUAL-PIPELINE-1`・
`SECDATA-STORAGE-FRAGMENTATION-1`・`FRED-HYSPREAD-TRIPLE-FETCH-1`・
`SP500-GSPC-MULTI-FETCH-1`・`PORTFOLIO-CONFIG-DUP-1`・
`BETA-FALLBACK-DESIGN-GAPS-1`等、2026-07-22〜23に起票した39件のうち、
新DB構築（本プロジェクト）によって構造的に自動解消されるものと、新DB
構築後も個別対応が必要なもの（例: [[SCENARIO-BEARBULL-SIGN-FLIP-1]]の
ような計算ロジック自体の欠陥は、一次データ層の統合だけでは解消しない）
を区別する必要がある。この整理は本プロジェクトの各コンポーネント着手時に
行う。

## 更新ルール

本ファイルの各ステータスは、該当コンポーネントの実装依頼が完了した都度、
その完了報告に含まれる更新内容を反映して更新する（`CHAT_RULES.md`
「新DB構築プロジェクトの進捗管理」参照）。「未着手」→「構築中」→
「完成」の3段階で管理し、「構築中」に遷移した場合は着手日を、
「完成」に遷移した場合は完了日とコミットハッシュを備考欄に追記する。

分類A/B/Cの件数・IDリストに追加・削除が生じた場合は、本ファイル冒頭の
「一次データ層の総数」表も同時に更新する（`CHAT_RULES.md`
「一次データ層の件数管理」参照）。
