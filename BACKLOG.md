# TANUKI VALUATION — 改善バックログ

最終更新: 2026-06-26（本日作業反映・BACKLOG整備）
完了済み項目は BACKLOG_DONE.md にアーカイブ

---

## 📌 このバックログの読み方（2026-06-19 統合で追加）

前回までのバックログは個別バグ・個別画面の課題を1件1項目で並列管理しており、
94件超まで肥大化していた。分析の結果、その多くが少数の**横断的パターン**に
起因することが判明したため、今回以下の方針で再構成した。

1. **「個別画面の表示崩れ」90件以上 → 6つの横断課題（EPIC）に統合**
   個別チケットは各EPICの「対象一覧」に格下げし、EPIC単位で一括対応する。
   1件ずつ直すと作業コストが線形に積み上がるが、共通コンポーネント化すれば
   1回の実装で全画面に波及する。
2. **「個別バグ」は引き続き個別管理**（データ不整合・計算ロジック誤り等、
   汎用化できない性質のもの）
3. **アーキテクチャ課題（ARCH-DATA-1 / BUG-SCORE-SYNC-1根本解決）を「高」に格上げ**
   個別バグの多くがこの2つに起因しており、先送りするほど利息が複利で積み上がる
   技術的負債である。詳細は下部「開発方針メモ」参照。

---

## 優先度：最高（構造的負債・着手で多くの後続課題が消える）

（最高優先度の残課題なし。2026-06-23時点。EPIC-LAYOUT-1はグループA/B/C全件完了し
BACKLOG_DONE.mdへ移動。MACRO-DISP-2も2026-06-23完了）

---

## 優先度：高（早急に対応）

### [ARCH-DATA-1] SECデータ正規化レイヤーの強化
**優先度:** 高（旧「中」から格上げ — 下記理由参照）
**分類:** アーキテクチャ / 根本対策

#### 格上げ理由（2026-06-19）
2026年6月の修正ログを通読すると、BUG-NETDEBT-6/PARSER-1/ANNUAL-FY-1/
BUG-EPS-UNIT-1/BUG-FOUR-1等、直近1ヶ月の主要バグの大半が「ロジックミス」
ではなく「想定外のSECデータ形への対応漏れ」だった。このレイヤーが薄いままだと、
新規ティッカー追加・既存ティッカーの決算更新のたびに同種バグが再発し続ける。
個別バグ修正は対症療法であり、ここへの投資が最も複利で効く。

#### 背景
79銘柄以上のXBRLデータ形式が不均一（旧タグ / 金融の狭いrevenue / 非12月決算期 /
上場直後の年次不足 / SPAC / IFRS等）で、計算ロジックの各所でデータの個性を
吸収している。これがエッジケースバグの温床。

#### 着手状況
- **PARSER-1（2026-06-13 完了）が本タスクの第一歩**: 年次キーを fy→end_date年 に変更し
  非12月決算企業の過去データ汚染を根治。exact_match優先ロジックを正規化層に導入済み。
- **BUG-NETDEBT-6（2026-06-13 完了）で同一時点原則を実装**: BS項目を同一filingから
  取得する規則を pipeline に導入済み。
- **ANNUAL-FY-1（2026-06-13 完了）が第三歩**: aggregate_annual の filing_date[:4] →
  fiscal_year フィールドベースに変更。20銘柄のIV誤計算を是正。
  ~~**残課題**: 年度判定が parser.py / extract_key_facts.py / aggregate_annual の
  3箇所に分散。~~ ✅ 2026-06-25完了（ARCH-DATA-1-FY）

#### 残りの方針
計算ロジックに渡す前に、SECの変種を統一フォーマットに均す
正規化レイヤーを厚くする。下流のエッジケースを構造的に減らす。
- BS項目はすべて同一決算期（同一 as-of 日）から取得する統一規則を敷く
  （BUG-NETDEBT-6で同一時点原則を実装済み。残課題は normalized JSON 自体の
   フィールド網羅性向上）
- 旧SECタグ・金融revenueタグ・非12月期等の吸収を正規化層に集約し、
  計算ロジックからデータ個性の処理を排除（PARSER-1で年度キー部分は対応済み）
- normalized JSON に不足フィールド（ShortTermInvestments / 銀行移行後LTDebt 等）を補完
- ~~**年度判定の3箇所分散を単一関数に統合**~~ ✅ 2026-06-25完了
  （`common/sec_data/utils.py` に `determine_fiscal_year` を追加。parser.py・extract_key_facts.py・aggregate_annual の3箇所を統一）

#### 着手条件
個別バグの掃討が一段落してから、ではなく、**次にデータ形起因バグが
発生した時点で着手する**（先送りを重ねるほど一本化コストが増えるため）。

**audit.py に追加すべき項目（SECデータ取得層・一部着手済み）:**
- ✅ yfinance株式数とSEC株式数の乖離が5倍以上の銘柄を WARNING 出力（2026-06-15 実装）
- 10-Qに株式数タグが存在しない銘柄（UP-C構造等）を一覧表示（未着手）

---

### [ALPHA-REDESIGN-2] stock.htmlのα乗算残存修正
**優先度:** 高
**分類:** バグ / TANUKI VALUATION
**発見:** 2026-06-26横断調査

#### 問題
ALPHA-REDESIGN-1（2026-06-25）はcore_calculator.pyのα乗算廃止のみ完了。
stock.htmlへの反映が漏れており、以下の2箇所でα乗算が残存している。

- **感度分析テーブル（calcSensIV関数 L1233）**:
  `return (pv + tvPv) * (1 + alpha) / shs + bsps`
  → フロントエンドがDCFを独自再計算して(1+alpha)を乗算。
    NVDAではalpha=1.0のため×2.0となり、メイン表示($648.5)と大きく乖離した値を表示中。

- **DCFウォーターフォールチャート（renderChart L2492/L2512）**:
  `pt = v0*(1+alpha) + rpoPV + goPv*(1+alpha)`
  `alphaPremium = (v0+goPv) * alpha`
  → 廃止済みの「αプレミアム」バーが非ゼロで描画される。

#### 影響
- メイン理論株価（intrinsic_value_per_share）は正しい（バックエンド計算値を直読み）
- 感度分析テーブルとDCFチャートが過大な値を表示するバグ

#### 対応方針
- calcSensIV()から(1+alpha)乗算を除去
- renderChart()のalphaプレミアム計算・描画を除去またはゼロ固定
- alphaフィールドはJSONに参照値として残るため、表示のみ削除（削除してはいけない）
- CALCULATION BREAKDOWNのStep 7説明テキストを修正（L1826/L1832/L1940/L1941）
  - L1826: ×(1+alpha)の表示を削除またはゼロ固定表示に変更
  - L1832: α乗算式の説明文を「Phase1期間への反映」に書き換え
  - L1940/L1941: P_t計算式とαの説明文をMoat Score方式の説明に更新

---

## 優先度：中（こなれてきたら対応）

### [REVIEW-1] 外部AIレビュー指摘・要調査案件（2026-06-15 レビュー由来）
**優先度:** 低〜中（調査してから判断）
**分類:** データ品質 / 外部AIレビュー
**状態:** 全件対応完了・記録としてのみ残置（次回同種レビュー時の参照用）

#### 案件一覧（全件✅完了済み）
| 銘柄 | 指摘内容 | 対応状況 |
|------|---------|---------|
| SCCO | EPS quarterly 株数（163.7M）vs 実際（821M）が 5.1x 乖離 | 修正完了: CIK誤登録修正 + ProfitLossフォールバック追加 |
| NOW | adj_eps が SEC XBRL 値と乖離している疑い | 修正完了: 5:1株式分割未対応をBUG-NOW-SPLIT-1として修正 |
| MRVL | EPS 四半期データに異常値の可能性 | 修正完了: DTA認識NIをBUG-LYFT-EPS-1と同類処理で対応 |
| LMT | Q2 2025 EPS異常値、Adjustment_Delta=$0.0000 | 調査完了: プログラム損失はLIMITATION-1として記録、コード修正不要 |

### [EPS-1] アナリスト予想EPS四半期値の取得
- 現状: Next_Quarter_EPSはN/A（Alpha Vantage無料枠の制約）
- 問題: 四半期サプライズ率が計算できない
- 改善: 有料API検討 or yfinance の quarterly_earnings 活用


### [TANUKI-ROE-2] デュポン分解 業種平均比較・潜在ROE試算
**優先度:** 低
**状態:** 部分完了（2026-06-26）
- ✅ stock.htmlにDUPONT ANALYSISパネルを追加（4カード：純利益率・資産回転率・財務レバレッジ・ROE）
- [ ] 業種平均との比較表示（Damodaranにデータなし・データソース確保が必要）
- [ ] 潜在ROE試算（業種平均データ確保後に実装）

### [TANUKI-FIN-1] 金融機関向けバリュエーション対応（DDM等）
**優先度:** 中
**分類:** 設計課題 / TANUKI VALUATION

#### 背景
金融機関（銀行・保険・証券等）はFCFの概念がなじまず、TANUKI VALUATIONへの
登録が困難。一方で保有銘柄・ウォッチ銘柄に金融株が含まれるケースがある。

#### 対応方針（案）
- DDM（配当割引モデル）を新たなバリュエーション手法として導入
- TANUKI VALUATIONと横並びで主要データ（PER/PBR/ROE/配当利回り等）を保持できる
  金融株専用セクションまたは別フレームワークの設計
- 無理にFCFベースDCFに当てはめることを廃止

---

### [DISCOVER-THEMES-1] macro_themes_history.json未生成・.gitattributes未登録
**優先度:** 中
**分類:** 機能未稼働 / DISCOVER
**発見:** 2026-06-26横断調査

#### 問題
DISCOVER-FEATURE-2（2026-06-24）でdiscover/index.htmlはmacro_themes_history.jsonを
参照する実装が追加されたが、ファイル自体がリポジトリに存在しない。

- `docs/discover/data/macro_themes_history.json` が未生成
- `.gitattributes`にも未登録（merge=oursなし）
- index.htmlに`??[]`フォールバックがあるためUI破綻はしないが、
  「過去のテーマを見る」機能が完全に未稼働

#### 対応方針
- collect.pyを手動実行してmacro_themes_history.jsonを初回生成
- .gitattributesに`docs/discover/data/macro_themes_history.json text eol=lf merge=ours`を追加

---

### [DUPONT-COLOR-1] DuPont ROE色分けの不統一
**優先度:** 中
**分類:** UX不統一 / TANUKI VALUATION・TANUKI SCORE
**発見:** 2026-06-26横断調査

#### 問題
同一指標（DuPont ROE）の色分けが画面間で不一致。

| ページ | 0〜15% ROE | <0% ROE |
|--------|-----------|---------|
| tanuki_score/index.html | 黄 #facc15 | 赤 #f87171 |
| stock.html（DUPONT ANALYSISパネル）| 無色 var(--txt) | 赤 var(--red) |
| glossary説明（tscore_dupont_roe_color）| "オレンジ" | "赤" |

また glossary説明の「オレンジ」は実際の実装色「黄 #facc15」と表現が乖離。

#### 対応方針（要設計判断）
- stock.htmlをtanuki_scoreに合わせて黄を採用するか、現状の無色を維持するか
- 統一する場合はglossary説明も合わせて修正

---

### [STOCK-GLOSSARY-1] stock.htmlにglossaryポップアップ機能がない
**優先度:** 中
**分類:** UX / TANUKI VALUATION
**発見:** 2026-06-26横断調査

#### 問題
tanuki_score/index.htmlはinfo-tooltip.js経由でdata-info属性によるglossaryポップアップを
実装済みだが、stock.htmlにはglossaryポップアップ機能自体が未実装（data-info属性0件）。

DUPONTパネル・FINANCIAL HEALTHパネル等、説明を必要とする指標が多数あるが
ツールチップが使えない。

#### 対応方針
- stock.htmlにinfo-tooltip.jsをimportし、glossaryポップアップを有効化
- 有効化後、以下にdata-info属性を付与：
  - DUPONT ANALYSISパネルのROEカード（色基準説明）
  - その他説明が必要な指標（Moat Score由来のPhase1等）

---

### [SEC-CTRL-2] TANUKI TAIL内部統制データ未取得銘柄の一括生成
**優先度:** 中
**分類:** データ欠落 / TANUKI TAIL
**発見:** 2026-06-26横断調査

#### 問題
SEC-CTRL-1（2026-06-24）実装後、sec_ctrl_fetcher.pyをSOUNにしか実行していない。
tail登録9銘柄のうち8銘柄（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/TSLA）の
ctrlデータが未取得。内部統制タブを開くと「データなし（未取得 or CIK未登録）」と表示される。
UIクラッシュはないが機能として未稼働。

#### 対応方針
以下を実行して残8銘柄のctrlデータを生成する：
python src/tail/sec_ctrl_fetcher.py ADBE APP CELH CRWV NVDA PLTR SOFI TSLA

---

### [EPS-LOAR-1] LOAR IPO前EPS異常値の表示対象外処理
**優先度:** 中
**分類:** データ品質 / EPS ANALYZER
**発見:** 2026-06-26横断調査

#### 問題
LOAR（2024年4月IPO）の2023年以前のEPSが異常値を示している。
- 2023Q4: adjusted_eps=106.37（diluted_shares=204,000）
- 2023Q3: adjusted_eps=-20.995
- 原因: IPO前の株式構造（20万4千株）がIPO後（約9,300万株）と根本的に別物
- 計算自体はSECデータから正しく計算されているが、現在の株式数ベースでは意味をなさない

#### 対応方針
- EPS Analyzerの表示でIPO前データ（株式数が現在の1%未満等）を除外する処理を追加
- または|EPS|>50等の閾値でグレーアウト・除外表示する
- report_consistency_check.pyのCHECK-14/15（EPS>株価）との整合も確認

---

### [EXTREME-FEAR-1] extreme-fear/index.htmlの扱い方針決定
**優先度:** 中
**分類:** 設計判断 / 全体
**発見:** 2026-06-26横断調査

#### 問題
docs/value-monitor/extreme-fear/index.htmlがサイト公式ナビ（site-nav.js・docs/index.html）
に未接続で実質休眠状態。

- コミット1件のみ（ACTION-6追加時）、以後更新なし
- site-header.js / site-nav.js未使用・独自ナビを内包
- URLを直接知らないとアクセス不可

#### 対応方針（要設計判断）
- A案: site-nav.jsに登録してMARKET PULSE配下のサブページとして復活
- B案: 機能がMarket Pulseに統合済みであれば削除
- いずれにせよ放置は避ける

---

### [EPS-BX-1] BXのEPS ANALYZERでfetch失敗リスク
**優先度:** 中
**分類:** データ欠落 / EPS ANALYZER
**発見:** 2026-06-26横断調査

#### 問題
BX（Blackstone）はcik_lookup.csvでeps=trueだがtanuki=false。
EPS ANALYZERのindex.htmlは銘柄表示時に
../tanuki_valuation/data/BX/latest.jsonをfetchするが、
BXはtanuki=falseのためlatest.jsonが存在せず404になる。
IVが表示されない（エラーハンドリング次第でUIクラッシュの可能性あり）。

#### 対応方針
- A案: BXをtanuki=trueに変更してpipeline.pyを実行しlatest.jsonを生成
- B案: EPS ANALYZERのfetchロジックでlatest.json不在時のフォールバックを追加
- C案: BXをeps=falseに変更（BXは金融機関のためTANUKI-FIN-1対応まで保留）

---

### [HYPE-FLAG-1] CSGP/ZSのhypecore=falseフラグ更新漏れ
**優先度:** 中
**分類:** 設定不整合 / HypeCore
**発見:** 2026-06-26横断調査

#### 問題
CSGP・ZSのpoc.jsonが現役データとして存在（2026-06-11生成・stage=4）しているが、
cik_lookup.csvのtanuki/hypecore/eps/stonks_silo全フラグが空欄（falseですらなく未設定）。
CIKとnameのみ登録されており、フラグ列が省略されたまま放置された状態。
poc.jsonはhypecore.pyが独自の対象リストで実行した結果として生成された可能性がある。

#### 確認事項
- hypecore.pyのデフォルト対象リストがどこで定義されているか確認
- CSGP/ZSの各システムへの登録方針を決定してフラグを適切に設定する
  （hypecoreは原則全銘柄対象のためhypecore=trueは確定）
  （tanuki/eps/stonks_siloは銘柄特性に応じて判断）

---

### [CATALYST-DATA-1] catalyst.json初回データ未投入
**優先度:** 中
**分類:** 運用漏れ / DISCOVER
**発見:** 2026-06-26横断調査

#### 問題
CATALYST-1（2026-06-25実装）後の初回データ投入が未完全。
- 登録銘柄: 3銘柄（NVDA/IONQ/PLTR）のみ（hypecore=true 94銘柄が対象のはず）
- 全銘柄のcatalysts配列が0件（データ未取得）
- 原因: --allオプションなしの手動実行で3銘柄のみ処理されたと推測

#### 対応方針
以下を実行して全94銘柄のカタリストを初回投入する：
python src/discover/catalyst.py --all
（Grok APIコスト発生のため実行タイミングに注意）

---

### [RKLB-CLEANUP-1] RKLBのtickers.json残存・eps_sector空欄
**優先度:** 中
**分類:** 設定不整合 / TANUKI VALUATION・EPS ANALYZER
**発見:** 2026-06-26横断調査

#### 問題
RKLBはcik_lookup.csvでtanuki=falseに設定済みだが、
docs/value-monitor/tanuki_valuation/data/tickers.jsonに登録が残存している。
pipeline.pyがtanuki=falseの銘柄をtickers.jsonから除外する処理が
実行されていない（または未実装）。

また eps_sector フィールドが空欄のため、EPS Analyzerでセクター分類不可。

#### 対応方針
- tickers.jsonからRKLBエントリを削除（またはpipeline.py再実行で自動クリーン）
- eps_sectorにRKLBの正しいセクター（Aerospace & Defense等）を設定

---

### [STAGE0-STOCK-1] stock.htmlでstage=0（S0失望期）が非表示になるバグ
**優先度:** 中
**分類:** バグ / TANUKI VALUATION
**発見:** 2026-06-26横断バグ調査

#### 問題
stock.html L2086-2093でHypeCoreフェーズ表示ロジックにバグ。

```js
const STAGE_LABELS = {1:'黎明期', 2:'期待拡大期', 3:'陶酔期', 4:'期待剥落期'};
// stage=0 が未定義

const sl = hStage ? `Phase${hStage}・${STAGE_LABELS[hStage]||''}` : '';
// hStage=0 はfalsyのため sl='' → フェーズ表示が消える
```

stage=0（S0 失望/蓄積期）を持つ銘柄でHypeCoreフェーズ補正欄が
空白表示になる。hypecore/index.htmlとdetail.htmlは0を正しく定義済みで
stock.htmlのみ未対応。

#### 対応方針
- STAGE_LABELSに0:'失望/蓄積期'を追加
- falsyチェック（hStage ?）をnullチェック（hStage != null ?）に変更

---

### [HYPE-INF-1] HypeCoreのpoc.jsonにInf値が混入するバグ
**優先度:** 中
**分類:** バグ / HypeCore
**発見:** 2026-06-26横断バグ調査

#### 問題
hypecore.py L160でrev_ttm_prior=0（初期売上ゼロ期間）のとき
rev_yoy = (rev_ttm / rev_ttm_prior - 1) * 100 がInfになる。

z_score_series()にInfガードがないためfundamental_scoreにも伝播し、
poc.jsonにInf/-Inf値が混入している。

影響銘柄:
- ASTS: 2025-01〜03 → rev_yoy=inf, rule40=inf, fundamental_score=inf（9件）
- JOBY: 2025-04〜06 → rule40=-inf（3件）

フロントエンドのdetail.htmlで"Infinity%"が表示される（クラッシュなし・不正表示）。

#### 対応方針
- hypecore.py L160でrev_ttm_prior=0の場合のガードを追加
  （例: rev_yoy = None if rev_ttm_prior == 0 else (rev_ttm / rev_ttm_prior - 1) * 100）
- z_score_series()でInf/-Infを除外する処理を追加
- JSON保存前にInf/-Infをnullに変換する処理を追加
- 修正後にASTS/JOBYのpoc.jsonを再生成

---

### [PICK-DUP-1] daily_pick.pyの同日重複エントリバグ
**優先度:** 中
**分類:** バグ / TANUKI SCORE
**発見:** 2026-06-26横断バグ調査

#### 問題
daily_pick.py L515でhistory.jsonへの書き込み時に同日チェックが存在しない。
CIの再実行や手動実行のたびに無条件でinsertするため、
同日に複数回実行すると同日エントリが重複蓄積する。

現状の重複状況:
- 2026-05-30: NVDA が7件重複
- 2026-05-23: NVDAが3件・PLTRが別エントリ

```python
history.insert(0, {...})
history = history[:30]  # 同日チェックなし
```

フロントエンド（tanuki_score/index.html）は重複除去をしないため
同日の重複エントリが全て表示に反映される可能性がある。

#### 対応方針
history.jsonへの書き込み前に同日エントリを削除または上書きする処理を追加：
```python
history = [e for e in history if e.get('date') != today_str]
history.insert(0, new_entry)
history = history[:30]
```
修正後に既存の重複エントリをhistory.jsonから手動クリーンアップする。

---

## 優先度：低（アイデア段階）


### [UX-FLOW-1] On a Journey標準利用フローの設計
**優先度:** 低（思想設計タスク、実装ではなく方針検討から開始）
**分類:** 設計課題 / 全画面横断

#### 内容
画面間を行き来する非線形な利用が前提だが、緩やかな標準利用フロー
（例: stock.htmlで個別検証→TANUKI SCOREで横断相対判断、等）を
今後設計したい。


### [MULTI-1] マルチバリュエーション表示
- 現状: DCF一本槍
- 改善: DCF / PEG / EV/Sales / RICE / HypeCoreを並列スコアカード表示
- GPT提案: 2026-05-30



### [ARCH-1] ボトルネック企業プレミアム
- 現状: 未実装
- 内容: NVDA・ASML等の独占的ポジションを持つ企業への追加プレミアム
- 設計: 手動フラグ（bottleneck: true）+ Moat Scoreへの上乗せ or Phase1延長の形
- 注記: ALPHA-REDESIGN-1（2026-06-25）でalphaが廃止されたため、
  α加算方式は使用不可。設計を再検討する必要あり。
- 記録日: 2026-04-12

### [EVAL-2] 期待値エンジン（仮称）
- 現状: 構想中
- 内容: 各サブポート戦略の期待値を統合管理するエンジン



### [DESIGN-8] 8-3 ワンクリック銘柄登録〜更新
- 概要: Discover画面から「➕ 登録」ボタンで
  CIK取得→β/セグメント/Damodaran業種AI提案→承認→一括更新
  を一気通貫で実行
- 実装難易度: 高

### [DESIGN-8] 8-4 指数採用候補銘柄の発掘（設計見直し済み・実装保留）
- 概要: S&P MidCap 400 → S&P 500 昇格候補を定期サーチ
  GS・バンカメ等が発表する昇格候補レポートをGrok Web検索で収集
  機械的条件判定（yfinance）ではなくアナリストレポートベースの設計
- 実装方針: Grokのweb検索で「S&P 500 addition candidates」を定期検索
  週次でDiscover候補セクションに表示
- 実装難易度: 中
- 状態: 実装保留（着手時期未定）

---

### [STALE-CHECK-1-IMPL] STALE-CHECK-1の未実装とドキュメント乖離
**優先度:** 低
**分類:** ドキュメント乖離 / 品質管理
**発見:** 2026-06-26横断調査

#### 問題
CLAUDE_CODE_START.md（L689〜693）に「STALE-CHECK-1:決算後未更新」と記載されているが、
common/sec_data/report_consistency_check.pyにこのチェックの実装が存在しない。
ドキュメントの記述が実装より先行している状態。

#### 対応方針
- A案: STALE-CHECK-1を実装する
  （直近決算発表日からN日以上経過しているのにlatest.jsonが更新されていない銘柄を検出）
- B案: 実装予定なければCLAUDE_CODE_START.mdの記載を削除する

---

### [CHECK-FORMAT-1] report_consistency_check.pyのコメント形式不統一
**優先度:** 低
**分類:** 保守性 / 品質管理
**発見:** 2026-06-26横断調査

#### 問題
CHECK-1〜11は「# ── CHECK N: 説明 ───」形式、
CHECK-12〜19は「# CHECK-N:」形式で記述されており、
grepやスクリプトによる自動検出で漏れが発生しやすい。

#### 対応方針
全CHECKを「# CHECK-N:」形式に統一する（CHECK-1〜11を修正）。

---

### [RPO-ADMIN-1] rpo_config.jsonがadmin.htmlで編集できない
**優先度:** 低
**分類:** 管理UI漏れ / admin.html
**発見:** 2026-06-26横断調査

#### 問題
rpo_config.json（RPOプレミアムのホワイトリスト管理）は
report_consistency_check.py L42で参照されているが、
admin.htmlにUI編集機能が存在しない。
RPOプレミアムを付与・変更する際は手動JSONファイル編集が必要。

#### 対応方針
admin.htmlにrpo_config.jsonの編集UIセクションを追加する。

---

### [CHECK-COVERAGE-1] 新機能に対応するconsistency checkが未追加
**優先度:** 低
**分類:** 品質管理
**発見:** 2026-06-26横断調査

#### 問題
直近実装された以下の機能に対応するconsistency checkが未追加：
- Moat Score（ALPHA-REDESIGN-1）: moat_scoreがNoneまたは範囲外（0〜1）の検出
- DuPont分解（TANUKI-ROE-1）: dupont=nullの銘柄のうち負債超過でないものの検出
- s4_streak（HYPE-1）: 内部変数のため対象外

#### 対応方針
report_consistency_check.pyに以下を追加：
- CHECK-20: moat_scoreが存在しない、または0〜1範囲外の銘柄を検出
- CHECK-21: dupont=nullかつstockholders_equity>0の銘柄を検出（除外ロジックの検証）

---

### [TTM-NULL-1] ttm_calculator.pyでval=None時のTypeError未ガード
**優先度:** 低
**分類:** バグ / SECデータ処理
**発見:** 2026-06-26横断バグ調査

#### 問題
ttm_calculator.py L94・L185でe["val"]がNoneの場合にTypeErrorが発生しうる。

```python
# L94
total = sum(e["val"] for e in last4)  # val=NoneでTypeError
# L185
q4_val = fy_val - sum(e["val"] for e in top3)  # 同上
```

SECデータは通常数値のため実害は低いが防御的ガードがない。

#### 対応方針
sum()内でNoneを0として扱うガードを追加：
```python
total = sum(e["val"] or 0 for e in last4)
```

---

### [STONKS-DIV-1] analyzer.pyの複数箇所でゼロ除算ガードなし
**優先度:** 低
**分類:** バグ / STONKS SILO
**発見:** 2026-06-26横断バグ調査

#### 問題
discover/stonks-silo/src/analyzer.pyの以下の箇所でゼロ除算ガードなし：
- L222: (r_end / r_start) ** (1/3) — r_start=0でZeroDivisionError
- L314: abs(min(ni, 0.0)) / rev * 100 — rev=0でZeroDivisionError
- L625: latest_yoy / avg_past > 3 — avg_past=0でZeroDivisionError

STONKS SILOは売上がある赤字企業が対象のため実害は低いが、
エッジケースでのクラッシュリスクがある。

#### 対応方針
各箇所にゼロガードを追加：
- L222: r_start == 0 の場合はNoneまたはデフォルト値を返す
- L314: rev == 0 の場合は0または計算スキップ
- L625: avg_past == 0 の場合は比較をスキップ

---

### [THESIS-FIELD-1] thesis.jsonのフィールド定義不整合
**優先度:** 低
**分類:** データ定義不整合 / TANUKI TAIL
**発見:** 2026-06-26横断バグ調査

#### 問題
thesis.jsonの実際のフィールドが期待値と乖離している（全9銘柄共通）：

- company: 未実装（フィールド自体なし）
- position_size: 未実装（フィールド自体なし）
- strategy → 実際は strategy_name（フィールド名相違）
- thesis_version → 実際は version（フィールド名相違）
- entry_price: NVDAでnull（既存ポジション登録時に取得価格未記録）

機能的な問題はないが、スキーマ定義と実データの乖離が蓄積している。

#### 対応方針
- TAIL-LAYOUT系の実装時にthesis.jsonのスキーマを正式定義して統一
- NVDAのentry_priceを実際の取得価格で更新

---

## システム全体バックログ（TANUKI VALUATION以外）

### 【Stonks Silo】
- 現状: 26銘柄・results.json更新済み

### 【Moomoo API】
- [ ] β自動計算（SPY日次リターンからbeta_config.jsonを自動更新）
- [ ] advance/decline比率収集（MACRO PULSE向け）
      ※ Market Pulse向けの二極化検知はRSP/SPY乖離・A-Dライン・マクラレンオシレーターで
        2026-06-22に実装済み（[[MP-BREADTH-2]]、BACKLOG_DONE.md参照）。本項目はMACRO PULSE向けの残タスク。
- [ ] CANSLIM候補スクリーニングリスト（US株対象）
- [ ] 資金フロー（大口/小口）表示
- [ ] 決算ウォッチ用プレ/アフターマーケットデータ

【Moomoo API Skill 移行】※2026-06-07以降着手
- 背景: moomoo証券が2026年4月にリリースしたClaude Code向けSkillパック
  自然言語指示で発注・バックテスト・戦略変更が可能
  現在の手製trader.pyと基本アーキテクチャ（ローカルPC+OpenD）は同じ
- 前提: signal.jsonの蓄積データ（2026-04-04〜）でバックテストを実施してから移行判断
- 手順:
  ① Claude CodeにMoomoo API Skillをインストール・動作確認
  ② 蓄積済みsignal.jsonデータ（約62件）でF&G Level2×TQQQ戦略をバックテスト
  ③ 結果が良好なら手製trader.pyをAPI Skillに移行
- 懸念: OpenDはローカルPC起動が必要（PC停止で自動売買も停止する制約は変わらず）
- 参考: https://www.moomoo.com/ja/community/feed/moomoo-api-skills-now-unlocked-ai-becomes-a-24-7-116413328916486

### 【TANUKI TAIL】
- 残タスク: EWM楽観バイアス係数・データパス統一（優先度低）

### 【情報収集支援システム】
- ~~カタリスト×割安検知（価格下落+空売り比率+カタリスト接近）~~ → CATALYST-1として実装完了（2026-06-25）
- [ ] テック/市場ブレークスルーニュース分類
- [ ] NEWS_API_KEY + Grok使用、yfinance/FMP連携

### 【Market Pulse】
- [ ] 予測バックテスト表示

---

## 設計相談メモ（未着手）

### [DESIGN-2] マクロによる銘柄フェーズ変化の認識
- 概要: マクロ環境（金利・流動性・センチメント）の変化が
  銘柄固有の品質変化なしにHypeCoreフェーズを変動させることを認める
- 設計: 2層構造
  Layer1（マクロ環境層）: Risk-On/Neutral/Risk-Off
  Layer2（銘柄固有層）: 現行HypeCore Phase1〜4
  最終フェーズ = 銘柄フェーズ × マクロ補正
- 連携: TANUKIの高成長期間・成長率への反映も将来検討
- 実装難易度: 高

### [DESIGN-4] 期待込みの価値計算
- 概要: TANUKI（本源的価値）+ Moat Premium（競争優位・Moat Score連動Phase1で表現）
  + マクロ補正 = 期待込みの価値（フロアまたは最高値の目安）
- 注記: ALPHA-REDESIGN-1（2026-06-25）でHypeCore αは廃止。
  Moat Scoreが競争優位の定量化を担う設計に変更済み。
- 連携: DESIGN-2・DESIGN-5と連動
- 実装難易度: 高

### [DESIGN-5] 期待の要素と構造の可視化
- 概要: 株価に織り込まれた「期待」を分解して可視化する
  TAM期待・シェア期待・利益率期待・時間軸期待・流動性期待
- 現状: 逆DCF（必要成長率）は実装済み → 拡張
- アイデア未固まり。設計を深める必要あり
- 実装難易度: 高

### [DESIGN-6] 経営者の実行力評価
- 概要: 目標の難易度 × ビート度合いで経営者を定量評価
- 指標候補:
  ガイダンス達成率（過去8四半期の実績/予想）
  売上成長の加速度
  ROICの改善トレンド
  SBC比率（希薄化の質）
- データ: EPS Analyzerで近似可能
- 実装難易度: 中

### [DESIGN-14] 非線形的成長の検知スコア
- 概要: 構造変化×経営者実行力×業界変曲点の3要素で
  企業が非線形的成長を起こしそうかをスコア化
  非線形成長スコア = 構造変化(40%) × 実行力(30%) × 変曲点(30%)
- 各要素の計算:
  構造変化: RPO急増・粗利率急改善・Grok分析
  経営者実行力: ガイダンス達成率・ROIC改善・成長加速度
  業界変曲点: RPO/売上比率・競合動向・Grok分析
- TANUKIとの連携:
  スコア高→成長期間延長・逓減傾きを緩やかに設定
- 実装難易度: 高

### [DESIGN-15] 期待と理論価格の関係の整理（前提課題）

#### 目的
「なぜ今この乖離率なのか」を銘柄をまたいで同じフレームで説明できるようにする。
数値的精密さよりも説明の一貫性と納得感が目的。

#### 設計方針
理論価格（資産＋FCF割引現在価値）と市場価格の差分（乖離率）の時系列を蓄積し、
主要イベントとオーバーレイすることで、人間が目視で因果を判断できる材料を提供する。

#### レイヤー構造（APTベース）
乖離率の発生要因を以下の4レイヤーで説明する：
- L1 マクロ：金利・景気サイクルへの感応度（全銘柄共通）
- L2 マーケット：相場を動かすテーマへの感応度（全銘柄共通、やや業種差あり）
- L3 業種／業態：業種ナラティブの盛衰（例：SaaSの死、AI半導体相場）への感応度（業種単位）
- L4 銘柄固有：個社のナラティブ・期待（HypeCoreが担う領域）

各レイヤーは正にも負にも働く調整要因であり、独立ではなく相互に影響し合った結果が乖離率として現れる。

#### 着手条件
- 過去理論価格の時系列蓄積には財務データのpoint-in-time管理が必要
- 精度を妥協した実装は行わない
- ARCH-DATA-1（SECデータ正規化レイヤー強化）が実質的に完了してから着手する
- それまでは理論価格スナップショットの定期保存（将来の時系列構築のための仕込み）のみ検討する

#### 理論的背景
- APT（裁定価格理論、Ross 1976）を骨格として採用
- 因子はFama-Frenchから借用せず、ONAJURNEY独自指標で構成する
  （RECESSION RISK SCORE・Market Pulseセンチメント・セクター騰落・HypeCoreスコア）

#### 実装難易度
高

---

### [SILO-LEGEND-1] 黒字化チャート凡例にpillスタイルの説明追加
**優先度:** 低
**分類:** UX / STONKS SILO
**発見:** 2026-06-26横断調査

#### 問題
SILO-LAYOUT-1（2026-06-24）で追加した凡例にはドット（緑丸）の説明のみ。
SILO-UX-1（2026-06-26）で追加した「✅ 達成済」pillスタイルの説明が凡例に含まれていない。
ドット凡例とpill説明が独立実装のため不整合。

#### 対応方針
buildProfitPath()の凡例部分に「✅ 達成済（pill）= 直近四半期で黒字」の説明を追加。

---

### [MP-TOOLTIP-1] BUY/TAKE PROFITチェックリストのglossaryツールチップ未付与
**優先度:** 低
**分類:** UX / Market Pulse
**発見:** 2026-06-26横断調査

#### 問題
glossary.jsonにbuy_ma200・buy_hy_spread・buy_hindenburg・
tp_ma200・tp_hy_spread・tp_hindenburgの6キーが登録済みだが、
market-pulse/index.htmlのチェックリスト表示箇所にdata-info属性が
付与されていないため、ツールチップが表示されない。
glossaryキーが「登録済み・未使用」の状態。

#### 対応方針
renderBuyChecklist()・renderTakeProfit()の各チェック項目ラベルに
data-info="buy_ma200"等のdata-info属性を付与する。

---

### [TOOLTIP-INDEX-1] tanuki_valuation/index.html・catalyst.html・news_history.htmlへのinfo-tooltip未適用
**優先度:** 低
**分類:** UX / 全体
**発見:** 2026-06-26横断調査

#### 問題
以下の画面でinfo-tooltip.jsがimportされておらずglossaryツールチップが使えない：
- docs/value-monitor/tanuki_valuation/index.html
- docs/discover/catalyst.html
- docs/discover/news_history.html

（stock.htmlはSTOCK-GLOSSARY-1として既登録）

#### 対応方針
各ファイルにinfo-tooltip.jsのimportを追加し、
説明が必要な要素にdata-info属性を付与する。

---

## システム設計の基本思想（2026-05-31）

### On-a-journeyの本質的な目的

このシステムは「情報表示ツール」ではなく
「投資仮説の構築・検証を支援するツール」である。

長期投資家の本質的な行動サイクル：
  仮説を立てる
  → ポジションを取る（仮説への賭け）
  → 仮説を検証し続ける
  → 仮説が崩れたら撤退・正しければ保有継続

各システムの位置づけ：
  TANUKI VALUATION：
    「この企業は本質的にXXXドルの価値がある」
    という仮説を数値化するツール
  HypeCore：
    「今市場はどの程度の期待を織り込んでいるか」
    という仮説を検証するツール
  MACRO PULSE・Market Pulse：
    「仮説が成立する外部環境か」を確認するツール
  EPS Analyzer：
    「企業が仮説通りに実行しているか」を
    四半期ごとに検証するツール
  Discover：
    「次の有望な仮説候補を発掘する」ツール

この思想に基づき、全ての新機能開発において
「仮説の構築・検証にどう貢献するか」を
設計判断の基準とする。

---

## 開発方針メモ（2026-06-19 統合時に追加）

### 今回の統合で見えた3つの教訓

**1. 表示系の個別バグは「症状」であり「病気」ではない**
凡例不足・ヘッダー不統一・列はみ出しの3カテゴリで合計36件、
全アクティブ課題の4割近くを占めていた。これらは個別に直すと
1件あたり小さな工数でも、画面数×指標数で掛け算的に増え続ける。
共通コンポーネント化（EPIC-LEGEND-1/EPIC-HEADER-1/EPIC-LAYOUT-1）に
先行投資すれば、今後の新機能開発でも「説明を書き忘れる」「ヘッダーが
バラバラになる」という再発自体を構造的に防げる。

**2. アーキテクチャ課題は「優先度：中」に埋もれると複利で効いてくる**
ARCH-DATA-1とBUG-SCORE-SYNC-1（→ARCH-SCORE-SYNC-1に改名）は
どちらも「個別バグ修正の繰り返しコスト」を生み出す根本原因であるにも
関わらず、これまで「個別バグの掃討が落ち着いてから」という消極的な
着手条件で塩漬けにされていた。直近1ヶ月の修正ログを読むと、
両者に起因するバグ修正だけで全体の半分近くを占めている。
今回「高」に格上げし、次の同種バグが出た時点で着手する条件に変更した。

**3. 「N/A」「–」の表示規約が画面ごとにバラバラ**
TSCORE-DISP-1/2、SILO-DISP-1/2、MP-DISP-4は同じ症状（空値の意味不明）。
EPIC化はしなかったが、どこかのタイミングで「空値表示規約」を
一度ドキュメント化し、site-nav.js的な共通JSに寄せることを推奨する。

**4. 個別タスク中に発見した構造的問題はその場でBACKLOG化する**
2026-06-21のセッションで、PORT-LOGIC-1実装中にARCH-PORTFOLIO-DUP-1を、
MACRO-BUG-1修正中にMACRO-COMPUTE-DUP-1を、それぞれ作業の副産物として
発見しBACKLOG登録した。個別タスクの調査・実装過程で見つかった「これは
ARCH-SCORE-SYNC-1と同種の問題では」という気づきを記憶やメモに留めず、
気づいた時点でBACKLOG.mdに登録することを標準動作とする。

### 次セッションでの着手順序（提案）
1. 優先度：中の残項目（TANUKI-FIN-1・EPS-1）または設計相談メモ（DESIGN-2/5/6等）へ展開
※ 2026-06-26完了: EVAL-3・TANUKI-ENB-1・SILO-UX-1・MP-ASSETFLOW-UI-1・TANUKI-ROE-2（部分）・SS-1（クローズ）

（ARCH-SCORE-SYNC-1は2026-06-20、TAIL-SEC-1/EPIC-LEGEND-1は2026-06-21、
EPIC-HEADER-1は2026-06-21、EPIC-LAYOUT-1グループA/グループBは2026-06-22、
EPIC-LAYOUT-1グループC（SILO-DISP-3）・MP-GAUGE-NEEDLE-1・MACRO-DISP-2は
2026-06-23に完了。BACKLOG_DONE.md参照）
