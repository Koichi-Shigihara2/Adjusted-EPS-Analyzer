# PROJECT_STATUS.md — 新一次データベース構築プロジェクト進捗

作成日: 2026-07-23
位置づけ: 「新一次データベース構築プロジェクト」（2段階プロジェクトの
第1段階＝一次データ層の構築・過去データ移管、第2段階＝導出データ層
〈`FIELD_DEFINITIONS.md`499項目〉の管理方法検討）の進捗を追跡する。
仕様書本体は`docs/architecture/new_data_platform/`を参照。

現時点でプロジェクトは**未着手**（設計フェーズが2026-07-22〜23に完了した
段階であり、実装〈コード構築〉はまだ1件も行われていない）。

---

## フェーズ1: 一次データ層の構築

| コンポーネント | 状態（未着手/構築中/完成） | 備考 |
|---|---|---|
| `common/sec_data/` 統合（raw/normalized/ttm統合含む） | 未着手 | `INPUT_DATA_TOBE.md` 2-A参照。統合スコープに`raw/`・`normalized/`・`ttm/`の3系統を含む旨を明記済み |
| `common/market_data/` 新設（yfinance統合層） | 未着手 | `INPUT_DATA_TOBE.md` 2-B参照。日次/週次属性/イベント履歴の3層分離設計 |
| `common/macro_data/` 新設（FRED統合層） | 未着手 | `INPUT_DATA_TOBE.md` 2-C参照。系列単位の時系列ストア設計 |
| provenanceメタデータ標準化 | 未着手 | `INPUT_DATA_TOBE.md` 2-D参照（`as_of`/`fetched_at`/`source`/`source_detail`/`fallback_used`） |
| fetcher/reader分離アクセス制御 | 未着手 | `INPUT_DATA_TOBE.md` 3-B参照 |

## フェーズ2: 過去データ移管

| データソース | 状態 | 対象範囲 |
|---|---|---|
| SEC EDGAR既存データ | 未着手 | `INPUT_DATA_AS_IS.md` 1-A・2-A参照（実測7経路） |
| yfinance既存データ | 未着手 | `INPUT_DATA_AS_IS.md` 1-B・2-B参照（実測11ファイル） |
| FRED既存データ | 未着手 | `INPUT_DATA_AS_IS.md` 1-C・2-C参照（実測2サブシステム） |
| 手動入力データ（config/配下への集約） | 未着手 | `INPUT_DATA_TOBE.md` 1-D参照（`fcf_conversion_config.json`・`tail_kpi_map.json`・Portfolio二重保持の是正含む） |

## フェーズ3: 導出データ層の管理方法検討

| 項目 | 状態 |
|---|---|
| `FIELD_DEFINITIONS.md` 499項目の新DB参照への切替方針 | 未着手（フェーズ1・2完了後に着手） |

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
