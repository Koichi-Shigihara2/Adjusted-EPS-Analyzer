# RETROSPECTIVE_2026-07-22.md — 本日の作業総括

作成日: 2026-07-23（セッション自体は2026-07-22朝に開始し、日付をまたいで継続した）
出発点: `git log`による本日分全コミットの機械的抽出（記憶・要約ではなく実際の
コミット履歴を事実的土台とする）。

---

## 0. 本日の全コミット履歴（機械的抽出）

対象範囲: `f6201ae0`（本日最初の実装コミット）〜`17d5f0bed`（FIELD_DEFINITIONS.md
フェーズ10・最終コミット、本総括作成直前の最新コミット）。

```
git rev-list --count f6201ae0~1..17d5f0bed
→ 54
```

**内訳**:
- ドキュメント作成・更新／実装コミット（本セッションの実作業）: **38件**
- GitHub Actions等の自動更新コミット（`chore:`接頭辞、market pulse/macro-pulse/
  discover/score_verifier/satellite_alerts/TANUKI TAIL RSS/TANUKI SCORE/
  TANUKI VALUATIONの定期実行ジョブ。本セッションの作業とは無関係に独立した
  スケジュールで実行され、コミット履歴上に時系列で混在している）: **16件**

以下、本セッションの実作業38件をコミットハッシュ・日時（JST）・変更ファイル
とともに時系列で列挙する（`chore:`系16件は事実の土台として存在を記録するに
留め、個別列挙は省略する）。

| # | 日時(JST) | コミットハッシュ | メッセージ | 変更ファイル |
|---|---|---|---|---|
| 1 | 07-22 07:29 | `f6201ae0` | fix: divergence_ratioの符号反転を独立ガードで検知（FCF-DIVERGENCE-SIGN-GUARD-1） | BACKLOG.md, src/value/tanuki_valuation/calculator/adjustments.py, tests/test_divergence_sign_guard.py |
| 2 | 07-22 07:29 | `560fb3b5` | docs: FCF-DIVERGENCE-SIGN-GUARD-1をBACKLOG_DONE.mdへ記録・BACKLOG.md更新 | BACKLOG_DONE.md |
| 3 | 07-22 07:38 | `99014218` | fix: raw_fcf<=0側の対称ケースをdivergence_warningへ追加（追補） | src/value/tanuki_valuation/calculator/adjustments.py, tests/test_divergence_sign_guard.py |
| 4 | 07-22 07:38 | `dcb4612c` | docs: raw_fcf<=0対称ケース対応のコミットハッシュをBACKLOG_DONE.mdへ記録 | BACKLOG_DONE.md |
| 5 | 07-22 07:44 | `513d696d` | docs: BACKLOG.md次セッション着手順序の注記を2段階分に更新 | BACKLOG.md |
| 6 | 07-22 07:45 | `7ae4f5d1` | docs: CHAT_RULES.mdに独立ガード追加時の全象限洗い出し・BACKLOG起票先行の教訓を追記 | CHAT_RULES.md |
| 7 | 07-22 08:20 | `ececdc3f` | docs: BACKLOG_DONE.md内のARCH-DATA-1 Stage1/2/3重複記載を解消 | BACKLOG_DONE.md |
| 8 | 07-22 08:26 | `12c172b0` | docs: CHAT_RULES.mdに入力精度向上前の下流ゲート影響確認の教訓を追記 | CHAT_RULES.md |
| 9 | 07-22 08:29 | `5d5d9e97` | docs: BACKLOG.md冒頭「最終更新」ログに2026-07-22セッションサマリーを追記 | BACKLOG.md |
| 10 | 07-22 08:34 | `4f4689e7` | docs: BACKLOG.md方針記述を訂正・CHAT_RULES.mdを日付順に整理 | BACKLOG.md, CHAT_RULES.md |
| 11 | 07-22 08:57 | `6a9bc40d` | docs: BACKLOG.md陳腐化記述3件を是正 | BACKLOG.md, BACKLOG_DONE.md |
| 12 | 07-22 08:57 | `229a8ff3` | docs: REVIEW-1移動記録にコミットハッシュを追記 | BACKLOG_DONE.md |
| 13 | 07-22 08:59 | `f0dafcb4` | docs: CHAT_RULES.mdに全文確認の実施基準を新規セクションとして追記 | CHAT_RULES.md |
| 14 | 07-22 09:05 | `90ccd3e4` | docs: BACKLOG_DONE.md見出しフォーマット不整合2件を修正 | BACKLOG_DONE.md |
| 15 | 07-22 14:59 | `78398848` | docs: 出力項目インベントリ(OUTPUT_ITEMS_INVENTORY.md)を新規作成 | OUTPUT_ITEMS_INVENTORY.md |
| 16 | 07-22 15:04 | `b4b3e722` | docs: CHAT_RULES.mdに作業目的の整合性確認プロセスを最重要ルールとして追記 | CHAT_RULES.md |
| 17 | 07-22 16:23 | `640991a3` | docs: AS-IS→TO-BE移行（ID化・自動分類・機械的網羅性証明） | OUTPUT_ITEMS_INVENTORY.md, TO_BE.md |
| 18 | 07-22 16:39 | `56afe109` | docs: TO_BE.mdに機械的網羅性証明セクションを追記（未実施の是正） | TO_BE.md |
| 19 | 07-22 17:11 | `1f5b7535` | docs: 計算ロジック一致ベースの重複再点検（命名に依存しない検査） | NAMING_CONVENTIONS.md（新規）, TO_BE.md |
| 20 | 07-22 18:12 | `ad7eaeec` | docs: OUTPUT_ITEMS_INVENTORY.mdに残り4サブシステム(AS-IS-285〜515)を追加 | OUTPUT_ITEMS_INVENTORY.md |
| 21 | 07-22 18:32 | `0c9d8d8c` | docs: 全515項目対象の重複再分類（フェーズ2、取得経路調査含む） | OUTPUT_ITEMS_INVENTORY.md, TO_BE.md |
| 22 | 07-22 19:19 | `6cd508a7` | docs: TO_BE.md矛盾是正+重複排除後の最終出力項目リスト作成 | TO_BE.md, TO_BE_FINAL_LIST.md（新規） |
| 23 | 07-22 19:34 | `6b0e1400` | docs: TO_BE_FINAL_LIST.mdの欠落是正・集計方法の透明化 | TO_BE_FINAL_LIST.md |
| 24 | 07-22 20:20 | `5fac3fb5` | docs: TO_BE_FINAL_LIST.mdに項目単位の同一定義/異なる定義判定を追加 | TO_BE_FINAL_LIST.md |
| 25 | 07-22 20:41 | `f96fcd63` | docs: 期間パラメータ違いの第3カテゴリ導入(CONCEPT_PARAMETER_VARIATIONS.md新設) | CONCEPT_PARAMETER_VARIATIONS.md（新規）, TO_BE_FINAL_LIST.md |
| 26 | 07-22 22:34 | `682cf5fd` | docs: TO_BE_FINAL_LIST.mdにデータ性質分類（5区分）を追加 | TO_BE_FINAL_LIST.md |
| 27 | 07-22 22:40 | `e9aadc58` | docs: UI操作機構4件の除外(ステップ6)+データ性質分類の499件ベース再適用(ステップ7) | TO_BE_FINAL_LIST.md |
| 28 | 07-22 23:12 | `7bf80a5c` | docs: FIELD_DEFINITIONS.md新規作成(フェーズ1: システム設定データ・移送データ) | FIELD_DEFINITIONS.md（新規）, TO_BE_FINAL_LIST.md |
| 29 | 07-22 23:28 | `bade6fbe` | docs: FIELD_DEFINITIONS.md追記(フェーズ2: 一次データ・手動入力データ) | FIELD_DEFINITIONS.md, TO_BE_FINAL_LIST.md |
| 30 | 07-23 00:12 | `d23c0e64` | docs: 導出データ405件の性格別サブ分類+一次データ13件の追加訂正 | DERIVED_DATA_SUBCATEGORIES.md（新規）, TO_BE_FINAL_LIST.md |
| 31 | 07-23 06:59 | `26e2be53` | docs: FIELD_DEFINITIONS.md追記(フェーズ3: 評価倍率・バリュエーション系13件) | FIELD_DEFINITIONS.md |
| 32 | 07-23 07:16 | `8c3a3e2d` | docs: FIELD_DEFINITIONS.md追記(フェーズ4: キャッシュフロー・収益性系27件) | FIELD_DEFINITIONS.md |
| 33 | 07-23 07:53 | `368993f0` | docs: FIELD_DEFINITIONS.md追記(フェーズ5: 成長率・トレンド系43件) | FIELD_DEFINITIONS.md |
| 34 | 07-23 08:08 | `18bcb06e` | docs: FIELD_DEFINITIONS.md追記(フェーズ6: DCF/WACC構成要素系45件) | FIELD_DEFINITIONS.md |
| 35 | 07-23 08:19 | `2c14d567` | docs: FIELD_DEFINITIONS.md追記(フェーズ7: カタリスト・イベント予測系50件) | FIELD_DEFINITIONS.md |
| 36 | 07-23 08:32 | `684698c1` | docs: FIELD_DEFINITIONS.md追記(フェーズ8: 信頼性・品質判定系60件) | FIELD_DEFINITIONS.md |
| 37 | 07-23 08:46 | `8f5909c3` | docs: FIELD_DEFINITIONS.md追記(フェーズ9: その他30件、最終導出データバッチ) | DERIVED_DATA_SUBCATEGORIES.md, FIELD_DEFINITIONS.md |
| 38 | 07-23 12:15 | `17d5f0be` | docs: FIELD_DEFINITIONS.md追記(フェーズ10・最終: マクロ・市場環境系124件、導出データ392件完了) | FIELD_DEFINITIONS.md |

---

## a. 本日の作業の変遷

1. **起点（07:29〜09:05）**: 前日から持ち越されていた
   [[FCF-DIVERGENCE-SIGN-GUARD-1]]（divergence_ratioの符号反転検知漏れ）を
   2段階で実装完了。この過程で「独立ガード実装時は全象限を先に洗い出すべき
   だった」「新規発見事象はBACKLOG起票を実装依頼に先行させるべきだった」
   という2件の運用上の反省が生まれ、CHAT_RULES.mdへ即座に反映した（#6）。
   続けてBACKLOG.md/BACKLOG_DONE.mdの記載整合性を数件是正する、通常の
   セッション運営作業が09:05まで続いた。

2. **転換点1（14:59、#15）**: ここで約6時間の空白を挟み、作業の性質が
   「個別タスクの実装・記録」から「全システム横断の出力項目監査」へ
   転換する。`OUTPUT_ITEMS_INVENTORY.md`を新規作成し、6サブシステム
   （TANUKI VALUATION/HypeCore/STONKS SILO/MACRO PULSE/Discover/
   EPS Analyzer）の出力項目にAS-IS-001〜284の連番IDを付番した。
   このドキュメント自体に「本ドキュメントは2026-07-22時点のAS-ISスナップ
   ショットである。以後の更新は事実誤認の訂正・AS-IS-ID付番のみとする」
   という凍結宣言が付されている（このコンセプトが後述e項の「開発凍結」
   認識の実体である。詳細はe項参照）。

3. **転換点2（16:23、#17）**: 監査の途中で「リポジトリ内に独立稼働
   サブシステムが実は10個あり、当初の6個では4個（TANUKI SCORE/
   Market Pulse/Portfolio/TANUKI TAIL）が漏れていた」という発見があり、
   「追加統合フェーズ1」として残り4サブシステムのAS-IS-285〜515を追加。
   ここで初めてAS-IS→TO-BE（あるべき姿の統一定義）への移行を`TO_BE.md`
   として開始した。

4. **転換点3（17:11、#19）**: `TO_BE.md`のブラッシュアップ依頼中に
   「項目名のキーワード一致だけで重複判定をしていたのでは、名前が
   異なるが計算元は同じ／名前が同じだが計算元が異なる、という重複を
   見落とす」という指摘が生まれ、「計算ロジック一致ベースの重複再点検」
   （命名に依存しない検査）に方針転換。この過程で`net_cash`
   （TANUKI VALUATION vs STONKS SILOで計算元が全く異なる、23銘柄中23銘柄
   乖離）・`net_income`（STONKS SILO vs EPS Analyzerで独立抽出パイプライン、
   IONQ/IOT/ONDSで黒字/赤字が逆転）という、名前一致検索だけでは
   発見できなかった実害級の重複が新たに見つかった（詳細はc項参照）。
   この発見を体系化するため`NAMING_CONVENTIONS.md`（命名規則の提言）と
   `CONCEPT_PARAMETER_VARIATIONS.md`（期間パラメータ違いという第3分類）
   を新設した。

5. **転換点4（18:32〜22:40、#21〜27）**: 全515項目を対象に取得経路調査を
   含むフェーズ2の重複再分類を実施し、515件→503件（純粋重複6件除去・
   同一定義クラスタ統合）→499件（UI操作機構4件の除外）という段階的な
   絞り込みを`TO_BE_FINAL_LIST.md`として確定。499件全件を
   「一次データ／手動入力データ／移送データ／システム設定データ／
   導出データ」の5分類に再分類した（導出データ392件・手動入力44件・
   一次42件・システム設定15件・移送6件）。

6. **転換点5（23:12〜翌12:15、#28〜38）**: 確定した499件のうち最大の
   導出データ392件について、`DERIVED_DATA_SUBCATEGORIES.md`で性格別に
   8サブカテゴリへ再分類した上で、`FIELD_DEFINITIONS.md`として全392件の
   計算式を最小単位（一次データ・外部API・手動設定・既定義AS-IS-ID）まで
   遂次分解するフェーズ1〜10の作業を実施。フェーズ9では分類誤り3件
   （AS-IS-447/453/454）を発見し`DERIVED_DATA_SUBCATEGORIES.md`側を
   訂正、フェーズ10（本日最終）では自分自身の草稿内の誤り1件
   （AS-IS-344を「既定義」と誤記していたもの）を書き込み前に自己発見・
   訂正した上で、499件カタログ全体の導出データAS-IS-ID集合が
   `DERIVED_DATA_SUBCATEGORIES.md`の392件と機械的に完全一致することを
   `grep`+`diff`で証明して完了した。

**要約**: 「BACKLOG.mdの整理」という当初の依頼は、実装した1件の不具合修正
（FCF-DIVERGENCE-SIGN-GUARD-1）の周辺整理から始まったが、その過程で
「命名一致だけの重複検査では実害級の重複を見落とす」という発見（転換点3）
が最大の推進力となり、最終的に515→503→499件の全出力項目の棚卸しと、
そのうち392件（導出データ）の完全な計算式分解という、当初依頼の規模を
大きく超える全社的な監査作業に発展した。

---

## b. 成果物一覧

| ファイル | 状態 | 行数 | 役割 |
|---|---|---|---|
| `BACKLOG.md` | 更新（既存） | 4,359行 | 改善バックログの正本。本日はFCF-DIVERGENCE-SIGN-GUARD-1の完了記録・陳腐化記述の是正のみ |
| `BACKLOG_DONE.md` | 更新（既存） | 8,701行 | 完了タスクのアーカイブ。本日は記載整合性の是正のみ |
| `CHAT_RULES.md` | 更新（既存） | 520行 | チャット側Claudeの運用ルール正本。本日新規5件の教訓を追記（詳細はd項） |
| `OUTPUT_ITEMS_INVENTORY.md` | **新規作成** | 1,877行 | 10サブシステム全515出力項目のAS-ISスナップショット（AS-IS-001〜515付番）。凍結宣言付き |
| `TO_BE.md` | **新規作成** | 1,080行 | 515項目の重複判定・統一定義（あるべき姿）の設計記録。⑫〜⑯群を含む新規発見の重複パターンを記録 |
| `NAMING_CONVENTIONS.md` | **新規作成** | 127行 | 「同名だが計算元が異なる」「同名だが期間定義が異なる」という2種の命名問題への命名規則提言 |
| `TO_BE_FINAL_LIST.md` | **新規作成** | 1,293行 | 515件→503件→499件の段階的絞り込みと、499件の5分類（一次/手動入力/移送/システム設定/導出）確定リスト |
| `CONCEPT_PARAMETER_VARIATIONS.md` | **新規作成** | 153行 | 「計算目的は同じだが集計期間のみ異なる」重複（PSR/net_income/売上成長率/OCF、計9件）を独立分類として記録 |
| `DERIVED_DATA_SUBCATEGORIES.md` | **新規作成** | 589行 | 導出データ392件を性格別8サブカテゴリ（評価倍率13/CF収益性27/成長率トレンド43/DCF-WACC48/カタリスト50/信頼性品質60/その他27/マクロ市場環境124）に再分類 |
| `FIELD_DEFINITIONS.md` | **新規作成** | 1,528行 | 499件全項目（フェーズ1-2）＋導出データ392件（フェーズ3-10）の計算式最小単位分解。本日の最終・最大の成果物 |

**訂正**: 依頼文に挙げられていた`SYSTEM_MAP.md`（692行）は、本日は
**更新されていない**（最終更新は2026-07-20のブラッシュアップ時。
`git log --follow -- SYSTEM_MAP.md`で確認済み）。既存の参照ドキュメントとして
存在するが、本日の成果物には含めない。

---

## c. 確定した実害バグ・設計上の問題（重要度順）

重要度は「影響銘柄数・データ点数」および「判断ミスへの直結度」で判定した。
**【実装済み】**は本日コード修正まで完了したもの、それ以外は
**【記録のみ・未修正】**（FIELD_DEFINITIONS.md/TO_BE.md等への記録に留まる）。

### 1. 【記録のみ・未修正】net_cash の二重計算・実害あり乖離（TO_BE.md ⑫）
TANUKI VALUATION（`SECReader.get_net_cash()`、SEC XBRL・四半期フォールバック・
セクターガードあり）とSTONKS SILO（`pipeline.py`、cash − yfinance
`totalDebt`、セクターガードなし・年次データのみ）が同名`net_cash`を
独立計算。**比較可能25銘柄中23銘柄で乖離、うちNET/RBRK/RDWの3銘柄では
符号が反転**（TANUKI側は数億〜十億ドル規模の「純キャッシュ」だが
STONKS SILO側は同じ銘柄を「純負債」と表示）。統一定義は
`SECReader.get_net_cash()`を唯一の正とする方針が`TO_BE.md`で確定済み。

### 2. 【記録のみ・未修正】net_income の二重抽出パイプライン・符号反転（TO_BE.md ⑭）
STONKS SILO（`common/sec_data`の年次正規化パイプライン経由）とEPS Analyzer
（自身の`extract_key_facts.py`による独立四半期XBRL抽出）が、同一のSEC XBRL
概念（`NetIncomeLoss`）を2つの独立実装でパースしている。期間が一致する
銘柄（AVAV/ESTC）は完全一致するため抽出ロジック自体に矛盾はないが、
**IONQ/IOT/ONDSの3銘柄でTTMとFY単年度の期間差により黒字/赤字が逆転**
（例: IONQはEPS Analyzer TTMで+327M黒字、STONKS SILO Annualで-510M赤字）。
統一はせず、TTM/FY{year}の期間ラベル明示を推奨、と`TO_BE.md`で判断済み。

### 3. 【記録のみ・未修正】risk_free_rate の常時ハードコード（0.043固定）
`calculate_wacc()`のデフォルト引数が10年国債利回りとして`0.043`固定であり、
実勢金利をその都度取得する設計になっていない（`FIELD_DEFINITIONS.md`
AS-IS-013）。**TANUKI VALUATIONの理論株価計算（AS-IS-002/004/006等、
全銘柄のDCF計算の中核）に組み込まれる定数**であり、影響範囲はTANUKI
VALUATIONの対象銘柄全件（現状100銘柄）。`market_return=10%固定`も同様に
根拠コメントなしのハードコード。

### 4. 【記録のみ・未修正】moat_score の部分欠損が「実測値ゼロ」として混入
`calculate_moat_score()`は`gm_norm`/`roic_norm`/`fcf_norm`の各値を
`(値 or 0.0)`で計算しており、3指標が**全て**Noneの場合のみ`moat_score=0.5`
のデフォルトが働く。1〜2指標だけの欠損では欠損指標が「最悪スコア相当の
実測値ゼロ」として平均に混入し、moat_scoreが不当に低く算出される
（`FIELD_DEFINITIONS.md` AS-IS-026/028）。
**本総括作成にあたり実データを機械的に再検証したところ**（`components.*_norm`
が厳密に0.0のケースをプロキシとして集計）、対象100銘柄中56銘柄で
3指標中1〜2個が厳密ゼロだった（うち3銘柄IONQ/JOBY/RCATは3指標全てゼロ＝
仕様通りの0.5デフォルト対象）。**注意**: `roic_norm`はROIC≤10%で正当に
0へクランプされるため、厳密ゼロ＝欠損データとは限らず、この56件は
「欠損の可能性がある銘柄数の上限値」である（依頼文にあった「43銘柄」という
数値の一次ソースをリポジトリ内・BACKLOG系ファイルいずれにも確認できず、
本総括作成時点の再計測値として56件を採用した）。

### 5. 【記録のみ・未修正】stock.htmlのCF分析セクション独自FCF計算（CapEx符号未処理）
`common/sec_data/parser.py`の正式なFCF計算は
`FCF = OCF - max(0, |CapEx|-|FinanceLease|)`とabs()で符号を吸収済みだが、
stock.htmlの「キャッシュフロー分析セクション」（`loadCfData()`/
`renderCfCharts()`、AS-IS-071）はlatest.jsonを使わず
`{ticker}_quarterly_normalized.json`を直接fetchして
`FCF = OCF - CapEx`をabs()なしで再計算している。CapExを負値で報告する
銘柄では`OCF - (負のCapEx) = OCF + |CapEx|`となり、**実際より高いFCFを
表示**。同一のCapEx符号不統一パターンがSTONKS SILOの表示専用フィールド
（AS-IS-157、`capex_annual`）にも独立に存在する。

### 6. 【記録のみ・未修正】MACRO PULSEのff_rate/yc/hy/vx truthy判定バグ
`05_import_history.py:122`の`get_historical_context()`が
`if ff_hi and ff_lo: ctx["ff_rate"]=...`という真偽値判定を使用。
**2020-2022年のゼロ金利期間（`ff_lo=0.0`）でPython偽値扱いとなり、
正当なデータがあるにもかかわらず`ff_rate`が欠落**。同型の`if yc:`/
`if hy:`/`if vx:`判定も同じ関数内に存在（値がちょうど0になった場合に
同様の欠落リスク、発生頻度はff_rateほど高くない）。現行稼働中の
`05_main.py`本体（`is not None`で正しく判定）ではなく、履歴データ
バックフィル専用スクリプトにのみ存在するバグ。

### 7. 【記録のみ・未修正】Hollow Rally検知の構造的恒久不発火
`05_liquidity.csv`の実列（`LIQUIDITY_COLUMNS`）に`sp500`列が一切存在しない
にもかかわらず、フロントエンドの判定コードが`r.sp500`を参照しているため、
`sp500Rows`が常に空配列となり、トリガー条件が恒久的に成立しない。
**実装以来一度も発火したことがない**ことが構造的に確定している。

### 8. 【記録のみ・未修正】RECESSION RISK SCOREの3計算式併存・25 vs 30閾値不一致
現在値用（ステップ関数、JS/Python一致）と過去日付用（`computeScoreAsOf()`の
lerp補間、全く別の閾値カーブ）という異なる2方式が「現在」と「過去」で
使い分けられており、スコア推移チャート・比較バーは常に別数式同士の比較に
なっている。加えてフェーズ判定の実閾値（30）に対し、ゲージバー背景・
チャート背景・**週次AI解説生成のGrokプロンプト文自体**の3箇所で「25」が
誤用されている（Grokプロンプトの誤りは本日新規に発見、依頼文で名指しされた
範囲を超える追加確認事項）。

### 9. 【実装完了】FCF-DIVERGENCE-SIGN-GUARD-1（divergence_ratio符号反転検知）
本日唯一の実装済み修正。`estimated_fcf`/`raw_fcf`比率（divergence_ratio）が
符号・境界を無視することで生じていた乖離検知漏れを2段階で解消
（コミット`f6201ae04a`: raw_fcf>0×estimated_fcf<0の符号反転ガード、
コミット`99014218b`: raw_fcf<=0×estimated_fcf>0の対称ケース）。回帰テスト
計6件・全100銘柄フローズン入力比較で既存データへの影響なしを確認済み。

### 10. 【記録のみ・未修正】rule_of_40 の定義相違（HypeCore vs STONKS SILO）
HypeCore（TTM売上YoY＋四半期純利益率）とSTONKS SILO（3年CAGR＋営業利益率）
で成長率・利益率いずれも定義が異なる。加えてSTONKS SILO側の
`DeficitQuality`データクラスは「`# 売上成長率 + 営業利益率`」という
コード内コメントを持つが、実装は単年度成長率ではなく3年CAGRを使っており
**コード内コメント自体が実装と矛盾**している。期間パラメータ違いの範疇には
収まらない（成長率項は同一だが利益率項の会計上の定義自体が異なるため）と
`CONCEPT_PARAMETER_VARIATIONS.md`で判定済み。

### 11. 【記録のみ・未修正】Discoverのconfig二重管理・admin.htmlバリデーション欠如
管理画面`admin.html`は`config/discover_config.json`・`theme_config.json`に
直接コミットするが、表示画面`docs/discover/index.html`は別パス
`docs/portfolio/data/`配下のコピーを参照する。同期は新規銘柄登録手順の
`shutil.copy()`一回限りの処理に依存しており、admin.html経由の直接編集では
このコピーを経由しないため表示に反映されないズレが起こりうる。加えて
admin.htmlの`saveThemeConfig()`/`saveDiscoverConfig()`は**内容検証を一切
行わず**（`valid`/`required`等の検証キーワードがadmin.html全体で0件）、
テーマID重複・空ラベル・不正な色コードもエラーなく保存されてしまう。

### 12. 【記録のみ・未修正】FRED HYスプレッド3箇所独立取得（依頼文既知の⑮追加確定）
既知だったMACRO PULSE内部2箇所（events.csv用・流動性カード用）に加え、
Market Pulseの`buy_checklist`判定用取得が**3箇所目**として完全に独立している
ことをフェーズ2の外部取得経路調査で確定。3箇所とも約40分差で連続的に
同一FRED系列`BAMLH0A0HYM2`を独立取得しており、1回のfetchで済む構造が
3回に分散している。

### その他（軽微・構造的リスクに留まるもの）
ERP①②（TANUKI VALUATION）の重複計算、moat_score(AS-IS-026)とAS-IS-028の
重複カタログ化、STONKS SILO OCF年次値の同一関数内再抽出（概念4）、
Market Pulseの`fear_greed.previous_close`/`one_week_ago`キー重複バグ、
`^GSPC`のMarket Pulse内4重独立フェッチ、`market_data.csv`のCSV列欠落
（NASDAQ本体・volume_ratio等）、Hindenburg Omenの銘柄数固定値500
（実測503）、S&P500の複数取得経路（MACRO PULSE FRED版 vs Market Pulse
yfinance版）——いずれも`FIELD_DEFINITIONS.md`フェーズ10に詳細記録済み。

---

## d. プロセス上の教訓（チャット側Claudeの失敗と是正）

本日CHAT_RULES.mdへ新規追記された教訓は**5件**（コミット4件に分散）。

### 1. 作業目的の整合性確認（最重要ルール、コミット`b4b3e722`）
新しい作業に着手する前に「大きな作業目的との適合性」を自問し、Claude Code
からの完了報告を受けた際も「成果物が実際にファイル化・コミットされているか」
「大きな目的に照らして意味があるか」を確認してから「完了」の語を使う、
という最重要ルールを新設。
**失敗の起源（実例2件、本文に明記）**:
- 実例1: TANUKI VALUATION出力項目調査で、分析（ステップ1〜4）自体は
  実施していたが結果がターミナル出力のみでファイル化されておらず、
  Koichiさんに「一覧表はどこにあるか」と指摘されるまで気づかなかった。
- 実例2: 「BUY/WATCHが何を意味するか」の議論で、本来の目的（全体を
  見なくても矛盾が起きない仕組みに作り替えられるか判断すること）から
  何度も個別の技術的話題に逸れ、同じ指摘を繰り返し受けた。

### 2. 独立ガード追加時は全象限を事前に洗い出す（コミット`7ae4f5d1`）
ある条件の閾値外にある質的に致命的なケースを独立ガードとして追加する際、
実装前に関係する変数の符号・境界の組み合わせ（全象限）を明示的に洗い出す。
**失敗の起源**: [[FCF-DIVERGENCE-SIGN-GUARD-1]]で
raw_fcf>0×estimated_fcf<0の符号反転ガードを先に実装したが、対称ケース
（raw_fcf<=0×estimated_fcf>0）の存在は後から別依頼で発覚し、2段階の
実装になった。

### 3. 新規発見事象は実装依頼に先行してBACKLOG.md起票を経る（コミット`7ae4f5d1`）
調査完了報告で「別タスクとして起票が必要」と申し送られた事項は、実装を
依頼する前にまずBACKLOG.mdへの起票を独立のステップとして挟む。
**失敗の起源**: raw_fcf<=0ケースは前回完了報告で「別タスクとして起票が
必要」と明記されたが、起票を経ずに直接実装依頼を作成した（同日中の解消の
ため実害はなかったが、手順が前後していた）。

### 4. 入力精度向上の前に下流の丸め・ゲート条件への影響を先に安価に確認する（コミット`12c172b0`）
ある入力データの精度を上げる作業に着手する前に、「その入力が変わった場合
最終出力は実際にどれだけ動くか」を既存の下流ロジック（Policy A/B等の
強制丸め・ゲート条件）に照らして安価に確認する。
**失敗の起源**: FCF-CONVRATE①③でDamodaranデータ取得・較正・比較設計の
訂正まで一通り実施した後、最後にシミュレーションでPolicy Bの強制丸めを
確認したところ、53銘柄中49銘柄で対応が無関係と判明した。同種の教訓を
既に持っていたにもかかわらず、調査着手時に想起・適用できなかった。

### 5. 全文確認の実施基準（コミット`f0dafcb4`）
「全文を確認してください」等の依頼を受けた際、直前の変更箇所の照合だけで
終わらせず、①結論の骨子を複数の言い回しでgrep再検索する、②類似構造を
横断的に検索する、③自分自身のツールで直接検証してから報告する、
④確認範囲を絞った場合はその旨を明示する、を必須手順とする。
**失敗の起源**: TRUST-SUMMARY-EPIC-1のFCF-CONVRATE①③方針撤回時、
「次セッション着手順序」欄は訂正したが、同じ古い結論が別セクション
（953-954行目）にも残っていることを、完全一致検索では発見できず見落とした。

---

## e. 未完了・申し送り事項

### 5分類レベルの再判定が未実施（本タスクの範囲外として記録のみ）
- **AS-IS-437〜441**（TANUKI TAIL `tail_kpi_map.json`関連5項目）:
  性質としては「手動入力データ」（AS-IS-425〜436と同一のAI下書き＋人手承認
  ワークフロー）に酷似しているが、ステップ7の一次分類時点で「導出データ」
  側に区分されたため本カテゴリ作業の対象になった。分類そのものを見直す
  余地がある。
- **AS-IS-404**（TANUKI TAIL `last_filed`）: フェーズ1で定義した
  「システム設定データ（監視状態管理系）」と同種の性質だが、本サブ
  カテゴリでの再検討時点では「その他」に分類されていたため取り残された。
- **AS-IS-057/058/060**（Reverse DCF比較表のメタ情報行「場所」「用途」
  「ガード」）: 実データ値ではなく、過去調査で作成された「既知の実装差異」
  比較表そのものにAS-IS番号が振られてしまったメタ情報であり、カタログに
  存置すべきか自体が要検討。

いずれも実装・分類変更を伴わないため、次回の判断機会に委ねる。

### TO_BE_FINAL_LIST.mdで確定した統一定義はコード未反映
`TO_BE.md`⑫（net_cash統一: `SECReader.get_net_cash()`を唯一の正とする）・
⑬〜⑯群を含め、`TO_BE_FINAL_LIST.md`で「あるべき姿」として確定した統一
定義・重複解消・命名規則（`NAMING_CONVENTIONS.md`）は、**いずれもまだ
実際のソースコードに反映されていない**。本日の作業は一貫して
「実装（コード修正）は行っていない、定義・分類の記録のみ」という
範囲宣言のもとで進められており、c項に挙げた実害バグも含め、対応の
実装着手は次回以降のセッション判断に委ねられている。

### 「開発凍結」の実態（依頼文の前提を検証した結果の訂正）
依頼文には「開発凍結（BACKLOG.md記載）が継続中」とあったが、`BACKLOG.md`
本文を検索した限り「凍結」という語の記載は確認できなかった。実際に
確認できた凍結宣言は`OUTPUT_ITEMS_INVENTORY.md`冒頭のものであり、
これは「本ドキュメント（AS-ISスナップショット）自体の以後の更新を
事実誤認の訂正・AS-IS-ID付番のみに限定する」という**ドキュメント単位の
凍結**であって、リポジトリ全体の開発を止める宣言ではない。
一方、実態としては本日07:38の[[FCF-DIVERGENCE-SIGN-GUARD-1]]追補
（コミット`99014218b`）以降、本日中に他のソースコード修正コミットは
一件も発生しておらず（`chore:`系の自動更新16件を除く）、以後の全作業は
各フェーズが明示する「実装は行っていない」という範囲宣言のもとで
ドキュメント作成のみに終始した。この意味では「実質的な実装作業の休止」は
事実として継続しているが、それを指す「開発凍結」という文言自体は
`BACKLOG.md`に記載されていない。次回セッション開始時に、この認識の
ずれ（依頼文の前提とリポジトリの実際の記載）を踏まえて解除方針を
確認することを推奨する。

---

## 完了報告サマリー

- 本日のコミット総数: **54件**（うちセッション実作業38件、自動更新
  `chore:`系16件）
- 最終コミットハッシュ: `17d5f0bed7cf26312f0f281cb78fcc22afc669c1`
  （`docs: FIELD_DEFINITIONS.md追記(フェーズ10・最終: マクロ・市場環境系
  124件、導出データ392件完了)`）
- 本ドキュメント（RETROSPECTIVE_2026-07-22.md）自体は本完了報告と併せて
  別途コミットする。
