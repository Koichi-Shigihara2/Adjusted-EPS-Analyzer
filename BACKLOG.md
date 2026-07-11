# On-a-journey — 改善バックログ（全システム）

最終更新: 2026-07-11（セッション最終ブラッシュアップ: PREVENT-5・TICKER-AUDIT-1・
TICKER-SOURCE-UNIFY-1・REGISTER-FLOW-REDESIGN-1・PREFLIGHT-CHECK-1
（いずれも優先度：中）が「## 優先度：低」セクション配下に誤配置されていた
構造的不整合を修正し「## 優先度：中」セクション末尾へ移動。全55項目のID・
本文を保持したまま再配置したことを検証済み。銘柄リスト参照の一元化調査を
実施しTICKER-SOURCE-UNIFY-1を新規登録。registration_validator.py・
adjusted_eps_analyzer/pipeline.pyのmonitor_tickers.yaml誤参照2件を確定、
common/sec_data/tickers.pyが既存の未活用統一ユーティリティであることを特定。
REGISTER-FLOW-REDESIGN-1にP1/P4の同時導入経緯（git履歴確認）・
system_health.py日次アラート見落としを追記、TICKER-AUDIT-1・
CIK-ORPHAN-FLAGS-1・PREFLIGHT-CHECK-1に相互参照追記）

追記（2026-07-11 同日中）: TICKER-SOURCE-UNIFY-1の対応方針1・2
（adjusted_eps_analyzer/pipeline.py・registration_validator.pyの
monitor_tickers.yaml誤参照2件）をコミット`ba2cfef42`で修正・完了。
対応方針3（他呼び出し箇所のtickers.py経由統一）は未着手のため
エントリはBACKLOG.mdに残置。REGISTER-FLOW-REDESIGN-1の対応方針1も
同一修正のため完了注記を追記、CIK-ORPHAN-FLAGS-1に本修正で新規検出
されるようになったBXの追記を反映。

追記（2026-07-11 同日3回目）: TICKER-SOURCE-UNIFY-1の対応方針3
（tanuki_valuation/pipeline.py・stonks-silo/pipeline.py・
common/screening配下2スクリプトの計4ファイル）をコミット`b41b447d6`で
完了。横断調査でhypecore.pyが既に移行済みと判明したため訂正を反映
（「1箇所のみ採用」の記述を「2箇所」に修正）。対応方針1・2・3すべて完了・
残作業なしとなったが、エントリの完全クローズはKoichiさんの判断待ちのため
保留。新規発見のcommon/sec_data/config.py重複ユーティリティ問題を
TICKER-SOURCE-CONFIG-DUP-1として新規登録。

追記（2026-07-11 同日4回目）: TICKER-SOURCE-UNIFY-1は対応方針1・2・3すべて
完了・残作業なしとなったため、エントリ全文（対応方針1・2・3の完了注記・
検証結果セクションを含む）をBACKLOG.mdからBACKLOG_DONE.mdへ完全移動した。
移動に伴い、BACKLOG.md内で本エントリを参照していた他エントリ
（CIK-ORPHAN-FLAGS-1・TICKER-AUDIT-1・REGISTER-FLOW-REDESIGN-1・
PREFLIGHT-CHECK-1・TICKER-SOURCE-CONFIG-DUP-1）のリンク表記を
「[[TICKER-SOURCE-UNIFY-1]]（完了・BACKLOG_DONE.md参照）」に更新し、
リンク切れの体裁を解消した。
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
- **新規スコープ候補（2026-07-09追加）**: 上記3件と同時に発見された
  バグA・B（_estimate_ttm_operating_income()等のフォールバック実装が、
  GrossProfit/RD/SM等複数フィールドの期末日整合性を検証せず暗黙に
  0円扱いしていた）は、SECデータ形の不均一性とは別種の技術的負債
  （フォールバック実装時の防御的プログラミング不足）。ARCH-DATA-1の
  正規化レイヤー強化と合わせて「フィールド間の期末日整合性を保証する
  共通ユーティリティ」の新設を着手スコープに含めるか、ARCH-DATA-1着手時に判断する。

#### 着手条件（成立・2026-07-09）
2026-07-09の新規5銘柄登録（RMBS/ENTG/TER/KLAC/LRCX）で
PARSER-ENTG-COMPYEAR-1・CHECK-QREV-FYE-1・XBRL-TAG-KLAC-1の
3件のデータ形起因バグが同一セッション内で同時発生し、着手条件
「次にデータ形起因バグが発生した時点で着手する」が満たされた。

追記: 2026-07-09同日中に、CHECK-QREV-FYE-1と同型の暦年グルーピング
バグがDILUTION-FYE-1（LRCX希薄化率誤算出）としてもう1件発見された。
report_consistency_check.py・pipeline.py双方の別々の箇所で同種の
「非12月決算企業を暦年ラベルでグルーピングする」実装が独立に存在し、
同じ欠陥を繰り返していたことになる。単発の偶然ではなく、正規化
レイヤーが薄いことに起因する再発パターンであることの裏付けとして記録する。

個別バグの掃討が一段落してから、ではなく、**次にデータ形起因バグが
発生した時点で着手する**（先送りを重ねるほど一本化コストが増えるため）。

**audit.py に追加すべき項目（SECデータ取得層・一部着手済み）:**
- ✅ yfinance株式数とSEC株式数の乖離が5倍以上の銘柄を WARNING 出力（2026-06-15 実装）
- 10-Qに株式数タグが存在しない銘柄（UP-C構造等）を一覧表示（未着手）

**着手条件に該当する新規事例（2026-07-10追記）:** [[SEC-TAG-FICO-CPRT-1]]
（FICO・CPRTの2020→2021年次売上高の不自然なジャンプ、XBRL-TAG-KLAC-1と同型の
タグ取得ミス疑い）を検出。「次にデータ形起因バグが発生した時点で着手する」
という本タスクの着手条件に該当する事例として記録する。SEC-TAG-FICO-CPRT-1
エントリ自体は個別事例の記録として残すが、実際の一次情報確認・修正は
ARCH-DATA-1着手時にまとめて行う（詳細は[[ARCH-DATA-1-CONSOLIDATE-1]]参照）。

#### 設計メモ（2026-07-02・検討中）
- PREFLIGHT-CHECK-1とパターン判定ロジックを共有する設計が望ましい。
  「このティッカーはこの変種パターンに該当する」という判定を
  ARCH-DATA-1側で作れば、Step1後の正規化（事後）とStep1前の
  警告（事前）の両方から同じロジックを呼び出せる。別々に作らない。
- 未知パターン（カタログにない初見の異常）への対応として、
  異常検知→AIが仮説生成→一次情報で検証→カタログに追加、という
  学習ループが構想として挙がっている。詳細はPREFLIGHT-CHECK-1参照。

---

### [BACKTEST-SCORE-1] TANUKI SCORE分類の事後検証
**優先度:** 高
**分類:** アーキテクチャ / 検証基盤
**登録日:** 2026-07-10

#### 背景
TANUKI乖離率・HypeCoreステージ・ROICトレンド・TANUKI SCORE分類
（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）のいずれも、
過去に同じ状態だった銘柄がその後どう動いたかを検証したことがない。
Market Pulseの「予測バックテスト表示」（未実装）とは別に、
TANUKI SCORE自体の的中率検証が必要。

#### Step 0 確認結果（2026-07-10・着手条件の妥当性確認）
- `history.json`（latest.json相当のスナップショット履歴）の蓄積開始日は
  銘柄により異なるが、確認した範囲では最古で2026-05-14（AAPL/NVDA/PLTR）、
  MOは2026-06-14、FICOは2026-06-03からで、**いずれも2ヶ月未満**。
- **重要な発見**: `score_history.json` に、本タスクが新規実装しようとしている
  ものとほぼ同等の仕組み（`date`・`tanuki_score`・`price_at_judgment`・
  `upside_pct`・`hype_phase`に加えて `return_30d`/`return_60d`/`return_90d`
  フィールド）が**既に存在**している。ただし記録開始日が2026-06-03のため、
  2026-07-10時点で `return_30d` は一部の初期日付でようやく値が入り始めた段階、
  `return_60d`/`return_90d` は**全銘柄で依然nullのまま**（まだ60日・90日が
  経過していないため計算不可）。
- **着手条件の見直し**: 依頼文にある「1年未満のデータしかない場合は暫定結果」
  という粒度の注意では不十分で、実態は「3ヶ月（90日）リターンすら
  1件も算出できていない」段階。3ヶ月後・6ヶ月後・1年後比較を求める本タスクの
  実装方針Step 2は、**現時点では実行不可能**（サンプルサイズ0件）。

#### 実装方針
1. 新規スクリプトを作成する前に、既存の `score_history.json` の
   `return_30d`/`return_60d`/`return_90d` フィールドが「誰が・いつ・どのロジックで」
   埋めているか（pipeline.py内の該当箇所）を確認し、可能な限りこの既存の
   仕組みを再利用する（重複実装を避ける）
2. history.json から、過去の各時点でのTANUKI SCORE Classificationと
   その時点のCurrent_Priceを時系列抽出するスクリプトを作成
3. 各時点から3ヶ月後・6ヶ月後・1年後の株価（yfinance historical取得）と
   比較し、Classification別（BUY/WATCH/TRIM等）の平均リターン・勝率を集計
4. 全銘柄・全時点を対象にした場合のサンプルサイズを事前見積もりし、
   統計的に意味のある結果が出せるか（銘柄数×観測時点数）を確認してから着手
5. 出力：Classification別リターン分布を可視化するレポート
   （docs配下、Market Pulse or TANUKI SCORE画面への追加を想定）

#### 着手条件
90日リターンの蓄積が進み、統計的に意味のあるサンプル数
（銘柄数×観測時点数の事前見積もりで確認）が確保できてから着手する。
2026-07-10時点では30日リターンの記録が始まったばかりのため、
最短でも90日リターンが一定数蓄積される2026年10月以降に再確認する。
それまでは着手せず、`score_history.json`への蓄積を継続する。

---

### [GROWTH-FLOOR-VERDICT-1] 成長率floor値張り付きの検知不足
**優先度:** 高（2026-07-10・中から格上げ）
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**発見:** サテライト投資候補91銘柄への前提妥当性チェック展開時

#### 問題
`growth_source=fcf_cagr` で `calculate_fcf_cagr()` の `growth_floor`（15%）に
成長率が完全一致した場合、実態（実績成長率）との乖離があっても
`growth_sanity` の `Verdict` が機械的に `PLAUSIBLE` になる。
2026-07-10の調査ではMO（実績FCF CAGR約2.4%・売上マイナス成長にも関わらず
15%floor採用でPLAUSIBLE判定）に加え、LOAR・XOMでも同型のfloor張り付きを検出した
（fcf_cagrソースを使う3銘柄が全てfloor値に一致するという100%的中率だった）。

#### 格上げ理由（2026-07-10）
以下2点が判明したため、単なる検知不足ではなく既存の恒久対策の穴と判断し格上げする：

a) **修正済みバグ（DCF-DEFAULT-G-1）の回帰・再発の疑い**：
   MOは[[DCF-DEFAULT-G-1]]（2026-06-15完了、BACKLOG_DONE.md参照）で
   「G=15%デフォルト問題」を名指しで修正されたはずの銘柄（JNJ/MO/PEP/PM/
   WMT/VZ等）だが、2026-07-10時点でfcf_cagr経路のfloor値15%を再び採用している。
   MOのhistory.json（2026-06-14以降）を確認したところ、`growth_rate`は
   記録が残る全期間（2026-06-14〜2026-07-11）を通じて一貫して0.15のままで、
   DCF-DEFAULT-G-1修正日（2026-06-15）の前後で変化していない。
   コードを読む限り、DCF-DEFAULT-G-1は「segment未設定銘柄でも
   `_GROWTH_OVERRIDES`を有効にする」修正（`get_segment_growth`が
   `_GROWTH_OVERRIDES`を優先参照するよう変更）だが、この`_GROWTH_OVERRIDES`
   自体は`recommended_g`が算出できた場合にのみ`pipeline.py`側でセットされる
   （`if _is_seg_unconfigured and _recommended_g is not None:`の条件下でのみ
   `set_growth_override`が呼ばれる）。MOはrev_cagr_3yr/5yrが共にマイナスで
   `recommended_g`の中央値候補から除外されるため`recommended_g`自体がNoneになり、
   overrideが一度もセットされないまま`determine_growth_rate()`が
   segment/override経路を素通りしてfcf_cagr経路（独自のfloor=15%を持つ、
   DCF-DEFAULT-G-1の修正対象外の別経路）に落ちていると推測される。
   これは「同じ症状が戻った」のではなく「DCF-DEFAULT-G-1の修正範囲が
   カバーしていなかった隣接経路が表面化した」可能性が高いが、
   確定にはgit log・当時のhistory.json等でのより詳しい経緯調査が必要
   （実装着手時に本調査から着手する）。

b) **CHECK-18の構造的な穴**：
   `report_consistency_check.py`のCHECK-18（DCF-DEFAULT-G-1回帰検知）は
   「recommended_gあり & phase1_growth_auto_adjusted=False & source≠segment_weighted
   & rate≈15%」が発火条件のため、**recommended_g自体がNoneになるMO型のケースを
   構造的に検知できない**。上記a)の推測が正しければ、CHECK-18は
   「recommended_gが算出できる場合の回帰」しかカバーしておらず、
   「recommended_gが算出できずfcf_cagr floorに落ちる場合」は検知対象外という
   構造的な穴が存在する。

#### 対応方針
1. floor値との完全一致を検知した場合、専用の警告Verdict（例: `FLOOR_HIT_REVIEW`）を
   出すよう `growth_sanity.py` を修正する
2. `report_consistency_check.py`に**CHECK-20**（fcf_cagr floor値張り付き検知：
   `growth_source=fcf_cagr` かつ `rate≈growth_floor(15%)`を機械検知）を追加して
   恒久化する（CLAUDE_CODE_START.mdの規約「新種バグを修正したら同スクリプトに
   検出項目を追加して恒久化する」に準拠）
3. 実装着手時、まずMOのgrowth_source切り替わりの経緯（git log・history.json）を
   確認し、a)の推測が正しいかを検証してから修正範囲を確定する
4. 実装は別タスクとして着手する

---

### [DCF-REL-SYNC-1] report.txtのDCF_Reliability判定にFCF乖離%が未反映
**優先度:** 高（2026-07-10・中から格上げ）
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**発見:** サテライト投資候補91銘柄への前提妥当性チェック展開時

#### 問題
`latest.json` の `fcf_outlier.note`（実績FCFの5年平均からの乖離%を含む注記、
例: FLYWで乖離215%）と、`report.txt` の `DCF_Reliability`（NORMAL/LOW表示ロジック）
が独立して存在し、相互参照されていない。この結果、FCF実績が5年平均から
大きく乖離している銘柄でもDCF_Reliability=NORMALのまま表示され、
乖離の大きさが伝わらないまま見過ごされるリスクがある。

#### 格上げ理由（2026-07-10）
本タスクと[[GROWTH-FLOOR-VERDICT-1]]はいずれも「信頼できない前提のBUYが
スクリーニングを素通りする」直接原因であり、スクリーニング運用の信頼性に
直結するため優先度を高へ格上げする。

#### Policy Aとの相互作用（重要な影響範囲・実装時必須確認事項）
CLAUDE_CODE_START.md記載のPolicy A（DCF_Reliability=LOWの銘柄はTANUKI SCORE
分類をBUY/TRIM/HOLD→**WATCHに丸める**、SELL/PASSは維持）により、本タスクの
実装でFCF乖離の大きい銘柄（例: FLYW 215%乖離）がLOWに格下げされると、
**表示変更にとどまらずBUY分類自体がWATCHに丸められる**。これはスクリーニング
精度向上の観点では望ましい効果（乖離の大きいBUYの自動除外）だが、
分類挙動が変わる銘柄の事前リストアップと影響確認を実装時の必須手順とする
（Policy A明文化時に影響確認対象とされたCRWV/SOUN/RKLB/JOBY/CEG等、
既存の該当銘柄への影響も併せて再確認すること）。

#### common/screening/dcf_validity_checker.pyとの関係
Check C（SEC売上ジャンプ検知）はSEC売上高のみが対象でFCF異常ジャンプは
対象外という制約があるが、本タスクの実装によりlatest.json側の`fcf_outlier`
判定がDCF_Reliabilityに反映されるようになれば、report.txt経由でFCF異常も
実質的に可視化されるため、この制約は実質的に解消される。

#### 対応方針
report.txt生成時に `fcf_outlier` の乖離%を閾値判定に組み込み、
一定以上の乖離があればDCF_Reliabilityを自動的にLOWへ格下げする。
既存のDCF_Reliability判定条件（FCF_Conversion_Rate方式・revenue_floor適用等）
との優先順位・閾値設計、およびPolicy A発動によるTANUKI SCORE分類変更の
影響確認を含め、実装は別タスクとして着手する。

---

## 優先度：未定（要判断）

### [CATALYST-DEDUP-1] catalyst.jsonの重複排除なし無制限追記問題
**優先度:** 未定
**分類:** アーキテクチャ / Discover
**登録日:** 2026-07-05

#### 問題
`src/discover/catalyst.py` の `discover_catalysts()` は既存カタリストとの内容重複チェックを
行わず、`process_ticker()` が既存分に新規発掘分を無条件で追記し続ける設計になっている
（`next_id()` はID重複回避のみでコンテンツ重複は見ない）。週次実行のたびに1銘柄あたり
約7件が積み増される現状ペースだと、年間3万件超に達する見込み。

#### 対応方針
重複排除ロジック（タイトル類似度判定・既存detailとの意味的重複チェック等）の導入を検討する。

#### 関連発見（2026-07-05・UI-DISCOVER-1影響予測機能の実API検証時）
`discover_catalysts()` の母集団は「上振れ事象のみを発掘する」設計（プロンプトが黒字化転換・
指数採用・大型契約獲得等の株価インパクト事象を列挙させる指示のため）。保有10銘柄への
本実行1回（72件）に対しimpact_predictor.pyでdirection/thesis_effectを実測したところ、
positive 71件・neutral 1件・negative 0件という極端な偏りが確認された。バグではなく
catalyst.py側の設計上の性質だが、影響予測機能の表示が「常にpositive寄り」に見える点は
将来のUI設計時の留意事項として残す（negative方向のカタリストが実質存在しないため、
方向性フィルタ等を設ける場合は母集団の偏りを踏まえる必要がある）。

---

### [GROK-MODEL-PRICE-1] Grok呼び出しモデルの実価格確認
**優先度:** 未定
**分類:** コスト管理 / 全体
**登録日:** 2026-07-05

#### 問題
collect.py・catalyst.py・risk_fetcher.py等で使用中の `grok-3-mini`/`grok-3`/`grok-2-1212` が
xAI現行価格表（docs.x.ai/developers/models）に存在せず、レガシーエイリアスとして
`grok-4.3`（$1.25/M入力・$2.50/M出力）へ自動ルーティングされ、想定（旧grok-3-mini想定
$0.30/M入力・$0.50/M出力）の4倍以上の価格で課金されている可能性がある
（UI-DISCOVER-1事前調査時に発見）。

#### 対応方針
xAI Consoleで実際の請求モデル名・単価を確認し、必要なら呼び出し先モデル名を
明示的に現行モデル名へ更新する。

#### 実測値（2026-07-05・impact_predictor.py実API検証時）
`grok-3-mini` を指定して呼び出したところ、レスポンスの `model` フィールドには
実際に応答したモデルとして **`grok-4.3`** が返ってきており、レガシーエイリアスの
自動ルーティングを実測で確認した。usageの実測例：
```
prompt_tokens=329, completion_tokens=45, reasoning_tokens=534, total_tokens=908
cost_in_usd_ticks=15227500（tick単位がnano-USDなら約$0.0152/回）
```
- **reasoning_tokens（534）が可視のcompletion_tokens（45）の10倍以上**あり、
  応答本文には出てこない非表示コストとして課金対象に含まれている可能性が高い
- **`max_tokens` パラメータは `completion_tokens` のみを制御し、`reasoning_tokens` は
  別枠で消費されると見られる**ため、reasoning側で予算を使い切りJSON出力本体が
  途中で打ち切られる（パース失敗）リスクが理論上ある（今回の検証では発生せず）
- tick単位（nano-USD想定）・実際の総コストはxAI Console側での一次確認が必要

---

## 優先度：中（こなれてきたら対応）

### [ENTG-TER-SEGMENT-1] ENTG・TERのsegment_config.json未設定
**優先度:** 中
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-09
**発見:** 5銘柄登録の横断整合性確認時

#### 問題
ENTG（Materials Solutions 43.9% / Advanced Purity Solutions 56.1%）・
TER（Semiconductor Test 79.1% / Product Test 11.2% / Robotics 9.7%）
は共にASC 280 formal segment数2つ以上のLMT型に該当するが、
segment_config.json未登録のまま_default設定でDCF計算されている。

#### 対応方針
各セグメントのgrowth rate設定に過去YoY実績・ガイダンスを踏まえた
判断が必要なため、Step 3.5として別途セッションで着手する。

---

### [GROWTH-SOURCE-LABEL-1] segment_detail.sourceの誤表示バグ
**優先度:** 中
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**発見:** サテライト投資候補10銘柄のDCF前提妥当性チェック時

#### 問題
`calculator/growth.py` の `get_segment_growth()` が返す `segment_detail.source`
が、実際の成長率算出経路（segment_config由来／recommended_g自動注入／
TTM実績成長率注入）によらず、常に固定文字列 `"segment_config"` として
ハードコードされている（`config.get("source")` の実際の値を転記していない）。

この結果、latest.json上は「セグメント設定に基づく成長率」に見える銘柄でも、
実際は10-Kセグメント内訳が未設定（segment_configured=False）で、
TTM実績成長率の直接注入や中央値フォールバックが使われているケースが
区別できない。2026-07-10の10銘柄サンプル調査ではCART/MSCI/CDNS/FICO/LRCXの
5銘柄（半数）でこの誤表示が発生していた。

#### 影響
成長率自体の計算ロジックは正しく動作しており、誤っているのは
provenance情報（根拠のラベル）のみ。ただし、この情報は「この銘柄の
成長率前提はどの程度セグメント別実績に基づく手堅いものか」を
判断する材料として使われるため、誤表示により前提の信頼度評価を
誤らせるリスクがある。

#### 対応方針
`get_segment_growth()` 内で `segment_detail["source"]` に固定文字列を
代入している箇所を、実際の `config.get("source")` の値を転記するよう修正する。
影響範囲（全銘柄への波及有無）の確認とテスト追加を含め、修正は別タスクとして着手する。

---

### [REPORT-CATALYST-1] カタリスト（Discoverのアップサイド事象）がreport.txtに未統合
**優先度:** 中
**分類:** 機能追加 / TANUKI VALUATION・Discover
**登録日:** 2026-07-10
**発見:** サテライト投資候補91銘柄への前提妥当性チェック展開時

#### 問題
report.txtの `[9] RISK EVENTS` はGrok web検索由来のリスクイベント（ダウンサイド）
のみを表示しており、`docs/discover/data/catalyst.json` 由来のカタリスト
（アップサイド事象）が含まれない。銘柄の投資判断材料としてリスク・カタリストの
双方を並列参照したい場面で、report.txt単体では片面（リスクのみ）の情報しか
得られない。

#### 対応方針
`[9] RISK EVENTS` と並列で `[10] CATALYSTS` セクションを新設し、
catalyst.json記載の直近カタリスト（重要度・確度付き）を表示する。
catalyst.jsonのデータ鮮度・カタリスト件数の多さ（CATALYST-DEDUP-1参照）を
踏まえた表示件数の絞り込み設計を含め、実装は別タスクとして着手する。

---

### [SEC-TAG-FICO-CPRT-1] FICO・CPRTのSECタグ誤取得疑い
**優先度:** 中
**分類:** データ品質 / SECデータ取得層
**登録日:** 2026-07-10
**発見:** サテライト投資候補の妥当性チェック時

#### 問題
FICO・CPRTともに2020年→2021年の年次売上高に不自然なジャンプが確認された
（FICO: 3.5倍、CPRT: 5.1倍）。FICOについては実際の2020年売上（$1.2億台後半と
推定）とSECデータ（$3.74億）が乖離しており、XBRL-TAG-KLAC-1と同種の
タグ取得ミスの疑いが濃厚。この異常値が成長率CAGR算出の基準年に使われており、
DCF理論株価・ROIC双方を歪めている。

#### 対応方針
XBRL-TAG-KLAC-1の対応方法を参考に、両銘柄の2020-2021年SECタグを一次情報
（EDGAR）で確認し、正規化層での修正を検討する。

---

### [STALE-REPORT-CLEANUP-1] tanuki=false化後もreport.txtが残存する
**優先度:** 中
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-10
**発見:** report.txt一括取得時（RKLB/ZS）

#### 問題
cik_lookup.csvでtanuki=falseに変更された銘柄でも、変更前に生成された
report.txtが物理的に削除されずフォルダに残存する（RKLB: 2026-06-26生成、
ZS: 2026-06-27生成のまま）。この状態でreport.txtを参照すると、
既にTANUKI対象外の銘柄が有効なBUY/WATCH等の判定を持っているように
誤読されるリスクがある。

#### 対応方針
tanuki=false切り替え時にreport.txtを削除するか、ファイル冒頭に
「STALE: tanuki対象外に変更済み」等の明示的な注記を自動挿入する処理を追加する。

---

### [CIK-ORPHAN-FLAGS-1] BX・ENBが全システムフラグfalseの孤立エントリ
**優先度:** 低〜中
**分類:** データ品質 / 銘柄登録
**登録日:** 2026-07-10
**発見:** サテライト投資候補91銘柄への前提妥当性チェック自己点検時

#### 問題
cik_lookup.csvのBX（Blackstone）・ENBの2銘柄は、status=activeでありながら
stonks_silo/tanuki/eps/hypecoreの4フラグが全てfalseになっており、
どのシステムからも実質的に参照されない状態で「active」登録が残っている。
いずれも `registration_note` に「列追加時点(2026-07-02)での遡及登録のため経緯不明」
と記載されており、2026-07-02のカラム追加時に経緯不明のまま機械的にactive化
されたものと推測される。

なおENBについては本タスクの自己点検でyfinance `country` フィールドを直接確認した
結果 `Canada` であることを確認した。CLAUDE_CODE_START.mdのStep 0
（カナダ企業は登録中止）に本来抵触するはずの銘柄であり、tanuki=falseの状態は
結果的に正しいが、システム非対応銘柄がactive登録のまま残ること自体は
[[TICKER-AUDIT-1]]（銘柄棚卸しスクリプト）の対象パターンと重なる。

#### 対応方針
[[TICKER-AUDIT-1]]着手時に「全フラグfalseかつstatus=active」を棚卸し対象条件の
一つとして組み込む。BX・ENBの具体的な扱いについては以下2案を検討した
（2026-07-10 チャット側検討）：

- **A案：登録抹消**
  評価不能な状態が続くなら、cik_lookup.csvから除外し追跡対象から外す。
- **B案：適切な評価軸への正式な振り分け**
  BXは代替資産運用会社（PL項目が薄くFCFベースDCF非適合）、ENBはカナダの
  エネルギー企業（IFRS/40-F、TANUKI-FIN-1が想定する金融機関向けDDMと
  親和性がある可能性）。TANUKI-FIN-1（DDM等の代替バリュエーション導入）の
  検討時に、この2銘柄を具体的な適用候補として扱うことを検討する。

チャット側の所感としてはB案（適切な評価軸への正式な振り分け）が筋が良いと
考えるが、最終判断はTANUKI-FIN-1着手時に行う。それまでは現状（4フラグfalse・
孤立状態）を維持し、除外は行わない。

#### 根本原因との関係（2026-07-11追記）
本件はregistration_validator.pyのP4-CIKOrphanチェック（cik_lookup.csv全体を
無条件スキャンする唯一のセーフティネット、WARN扱い）で検出可能だったが
運用上見落とされていた。[[TICKER-SOURCE-UNIFY-1]]（完了・BACKLOG_DONE.md参照）・
[[REGISTER-FLOW-REDESIGN-1]]の診断で、同種の見落とし（2026-07-10の半導体6銘柄
monitor_tickers.yaml同期漏れ）が再発したことを確認済み。詳細はそちらを参照。

#### 修正の波及（2026-07-11追記）
2026-07-11の[[TICKER-SOURCE-UNIFY-1]]（完了・BACKLOG_DONE.md参照）修正（コミット`ba2cfef42`）により、
registration_validator.pyのデフォルト実行でBXがP1系NGとして新規検出される
ようになった（従来はmonitor_tickers.yaml未登録のため走査対象外で不可視だった）。
BX自体への対応方針（A案:登録抹消／B案:評価軸振り分け）は変更なし。

---

### [STALE-SUBPORT-CLEANUP-1] src/subport/fg_level2/ 陳腐化複製の整理
**優先度:** 低〜中
**分類:** 保守性 / リポジトリ整理
**登録日:** 2026-07-11
**発見:** SYSTEM_MAP.md実態調査（2026-07-10）でAutoTrade運用実体を確認した際

#### 問題
AutoTrade（F&G Level2×TQQQ自動売買）の運用実体はリポジトリ外
`C:\Users\shigi\AutoTrade\fg_level2\`にあり、Windowsタスクスケジューラから
`trader.py --entry`/`--monitor`を日次実行している（signal.json/state.json/
trade_log.jsonlが実際に日次更新される）。一方、リポジトリ内
`src/subport/fg_level2/`は2026-05-03の開発初期に作成された同名モジュール一式
（trader.py/signal.py/config.json等）だが、2026-05-03以降git上で更新がなく、
内容が本番運用側と既に乖離している。`register_tasks.ps1`が`$RepoRoot`をこの
リポジトリパスに設定しているにも関わらず、実際には使われていない（詳細は
SYSTEM_MAP.md「AutoTrade/OpenD運用前提」参照）。

#### 対応方針
即削除はリスクがあるため、以下いずれかを判断する：
- A案: `src/subport/fg_level2/`が本番運用（リポジトリ外）から一切参照されて
  いないことを確認した上で削除する。削除の場合、他モジュールからの
  import参照がないことを`grep -rn "subport.fg_level2\|subport/fg_level2"`等で
  確認してから行うこと
- B案: 削除せず、README等を追加して「これは非稼働の旧複製であり、
  正は`C:\Users\shigi\AutoTrade\fg_level2\`である」と明示する

#### 影響
実害は薄い（本番運用に影響しない陳腐化コードの残存）が、将来このモジュールを
誤って参照・変更するリスクがあるため記録する。

---

### [UI-DISCOVER-1] カタリスト・ニュース履歴のUI改善
**優先度:** 中
**分類:** UX / Discover
**登録日:** 2026-06-27

#### 問題
catalyst.html・news_history.html のUIが使いづらく実用に耐えない。

#### 対応方針
現状のUI課題を洗い出してから設計する（次セッションで詳細ヒアリング）。

#### 着手状況
- ✅ 「連想・考察→影響予測」機能を追加（2026-07-05完了。詳細はBACKLOG_DONE.md参照）
- [ ] その他のUI課題（次セッションで詳細ヒアリング）

---

### [TAIL-SEC-ITEMS-1] TANUKI TAIL SEC項目の保存拡張（Item 1/1A/3/7）
**優先度:** 中
**分類:** 機能追加 / TANUKI TAIL
**登録日:** 2026-06-27

#### 問題
現在はItem 4（内部統制）のみ保存・表示している。
以下の項目もItem 4と同様にEDGARから取得・保存・表示したい：
- Item 1: Business（事業概要）
- Item 1A: Risk Factors（リスク要因）
- Item 3: Legal Proceedings（法的手続き）
- Item 7: Management's Discussion and Analysis（MD&A）

#### 対応方針
sec_ctrl_fetcher.pyを拡張するか別スクリプトを作成するか設計判断が必要。
TAIL-CTRL-TRANS-1（2026-06-27完了）の構造を踏襲する。

---

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

### [TANUKI-FIN-2] 金融機関銘柄（JPM・GS）へのエクイティDCF対応
**優先度:** 低（設計相談は完了・実装未着手）
**分類:** 設計課題 / TANUKI VALUATION
**登録日:** 2026-07-06
**ステータス:** 保留（着手時期未定、AI側の調子が良いタイミングで着手予定）

#### 背景
金融機関（JPM・GS）は負債が事業構造そのものの一部であるため、通常のFCFF
（企業DCF）が適合しにくい。業界標準としてFCFEベースのエクイティDCFが
適合する。Vは決済ネットワーク型で通常のFCFF DCFが適合するため対象外。

#### 対応方針
- 案（A）: 既存のTANUKI VALUATIONパイプライン内に業種分岐を追加し、
  対象銘柄のみエクイティDCFモードに切り替える
- 判定方式: SIC code等による自動判定ではなく、対象ティッカー（JPM・GS）を
  設定ファイルに明記する方式を採用（対象が少数のため過剰実装を避ける）
- 今後対象銘柄が増える場合、自動判定ロジックへの切り替えを再検討する

#### 関連
[[TANUKI-FIN-1]]（金融機関向けバリュエーション対応・DDM等）とは対象アプローチが異なる
（DDMではなくFCFEエクイティDCF、対象は少数ティッカーのハードコード方式）。
着手時にどちらの方式を採用するか、あるいは併存させるかを判断する。

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

### [EPS-ANALYZER-INTEGRATE-1] スクリーニング判断へのEPS Analyzer統合
**優先度:** 中
**分類:** 機能統合 / EPS ANALYZER
**登録日:** 2026-07-10

#### 背景
EPS Analyzer（GAAP/Non-GAAP乖離・割安発掘）は独立したシステムとして
存在するが、TANUKI SCOREベースのスクリーニング判断に統合されていない。
report.txt [6]セクションにAdjustment_Delta・PER_Comparison
（Market_PER_GAAP vs Adjusted_EPS_PER）が既に出力されているが、
これを比較・除外判定に使う仕組みがない。

#### 実装方針
1. `common/screening/dcf_validity_checker.py`（2026-07-10格納済み）に、
   EPS Analyzerの PER_Comparison（Delta: GAAP PERとAdjusted EPS PERの差）を
   追加チェック項目として組み込む
2. Deltaが一定閾値以上（要検討：例えば±10x以上）の銘柄をフラグし、
   「SBCや一時費用の影響で見かけの割安度が歪んでいる可能性」として
   出力に含める
3. 既存のTANUKI乖離率と、Adjusted EPSベースのPERから逆算した
   簡易的な参考株価を並記できるか検討する

---

### [RICE-INTEGRATE-1] スクリーニング判断へのRICE指標統合
**優先度:** 中
**分類:** 機能統合 / TANUKI VALUATION
**登録日:** 2026-07-10

#### 背景
RICE（投資効率指標、Matrix①投資効率系の軸）が計算可能な銘柄
（今回確認では55銘柄）について、スクリーニング時にRICE値を
参照していない。RICE>=3.0（高効率）/1.0-3.0（中効率）/<1.0（低効率）
という既存の閾値定義があるにもかかわらず未活用。

#### 実装方針
1. `common/screening/dcf_validity_checker.py`または
   `common/screening/report_txt_parser.py`の出力に、
   RICE値とその閾値区分（高/中/低効率）を追加フィールドとして含める
2. TANUKI SCORE=BUY かつ RICE<1.0（低効率）の銘柄を「割安だが
   再投資効率が低い」候補として別途フラグする運用を検討する
3. RICE Available=falseの銘柄（Revenue/CapExデータ不足）は
   従来通りMatrix②〜④で評価する

#### 関連（2026-07-10追記）
[[MULTI-1]]（マルチバリュエーション表示）とRICE指標の活用目的が部分重複する。
役割分担としては、本タスク（RICE-INTEGRATE-1）は**スクリーニング判定への
組み込み**（機械的なフラグ付け・除外候補の抽出）が主眼、MULTI-1は
**画面表示**（DCF/PEG/EV/Sales/RICE/HypeCoreの並列スコアカード表示）が
主眼という違いがある。将来的にどちらかへ統合するか、双方独立で進めるかは
どちらかの着手時に判断する。

---

### [ANALYST-VS-IV-INTEGRATE-1] アナリストコンセンサスとの突合せ
**優先度:** 中
**分類:** 機能統合 / TANUKI VALUATION
**登録日:** 2026-07-10

#### 背景
report.txtに「Analyst_Consensus ... vs IV: +151.4%」のような、
アナリスト目標株価とTANUKI理論株価の乖離が既に出力されているが、
スクリーニング判断に系統的に組み込まれていない。TANUKIは
「市場心理から独立した本源的価値」を意図的に狙っているため、
アナリストコンセンサス（市場心理側の代表値）との大幅な乖離は、
どちらの前提がズレているかを問い直す材料になる。

#### 実装方針
1. `common/screening/dcf_validity_checker.py`に、TANUKI IVとアナリスト
   目標株価中央値の乖離幅を計算するチェックを追加する（vs IVの値を
   そのまま利用可）
2. 乖離が大きい銘柄（例：50pt以上）を「TANUKIとアナリストの意見が
   大きく割れている銘柄」としてフラグし、どちらの前提に無理があるか
   個別確認を促す出力にする
3. 乖離の方向性（TANUKIが強気/弱気どちらに倒れているか）も記録する

---

### [PREVENT-5] 定期横断調査スクリプトの整備
**優先度:** 中
**分類:** 再発防止 / 品質管理

#### 背景
今回のような横断調査を毎回手動で実施するのはコストが高い。
system_health.pyでカバーできない観点（表示ロジック・用語統一・
フィールド定義整合性等）については、定期的な手動調査が必要。

#### 優先度見直し理由（2026-07-09）
現状、データ形起因バグの発見手段が「新規銘柄登録・決算更新時に
たまたま発火する」という受動的トリガーに限られている。
2026-07-09のASTS/LLYの期末日不整合バグ（バグB）は、
XBRL-TAG-KLAC-1-FOLLOWUP検証がなければ発見されず、既存102銘柄の
IVが過大評価されたまま放置されていた可能性がある。
ARCH-DATA-1の着手条件（次にデータ形起因バグが発生した時点で着手）は
維持するが、そのバグを発見する手段自体を能動化する必要があるため、
横断監査スクリプト整備の優先度を引き上げる。

#### 対応内容
以下を整備する：
- 横断調査用のチェックスクリプト（cross_check.py）を新規作成
  - cik_lookup.csv vs 全configの整合性
  - glossary.jsonのdata-info属性カバレッジ
  - console.log残存チェック
  - フィールド名の表記ゆれ検出
- 月次メンテナンスタスクとしてCLAUDE_CODE_START.mdに追記

---

### [TICKER-AUDIT-1] 銘柄棚卸しスクリプト
**優先度:** 中
**分類:** 再発防止 / 品質管理
**登録日:** 2026-07-02

#### 背景
テスト目的等での銘柄追加が本番パイプラインに紛れ込み、野放図に増加する問題への対処。
cik_lookup.csvへのstatus/registration_source/registration_note列追加を前提に、
定期的な棚卸しを自動化する。

#### 前提条件
cik_lookup.csvへのstatus/registered_date/registration_source/registration_note列追加、
完了済み（commit 337bf3d29。既存97銘柄はstatus=active/registration_source=unknownで
バックフィル済み。CLAUDE_CODE_START.mdのStep 0.5として新規登録手順にも組み込み済み）

#### 想定機能
① status=test かつ registered_date が一定期間（閾値は要検討、例：30日）より古い銘柄を
   「見直し候補」として一覧化
② registration_source=moomoo_screening等の検証由来かつポジションなしの銘柄を抽出
③ system_health.pyの拡張として実装するか、独立スクリプトにするか要検討
④ 判断（retired化等）は自動化せず、候補出しまでに留める。最終判断はKoichi自身が行う。
⑤ `registration_validator.py`のP4-CIKOrphanチェック相当（全フラグfalseかつ
   status=activeの孤立エントリ検出）を定期棚卸しレポートに明示的に集約する
   （下記「P4-CIKOrphan WARN見落とし問題」参照）
⑥ monitor_tickers.yamlとcik_lookup.csvの件数差・銘柄差分の検出も棚卸し対象条件に含める
   （下記「monitor_tickers.yaml同期漏れ」参照）

#### P4-CIKOrphan WARN見落とし問題（2026-07-10発見・2026-07-11追記）
`registration_validator.py`のP4-CIKOrphanチェックは、全フラグfalseかつactiveな
孤立エントリ（BX・ENB）を以前から検出していたが、WARNは非ブロッキングのため
運用上見落とされていた。[[CIK-ORPHAN-FLAGS-1]]（2026-07-10登録）は実質この
見落としの再発見だった。TICKER-AUDIT-1実装時は、WARNレベルの検出結果であっても
定期的に人の目に触れる仕組み（棚卸しレポートへの明示的な集約等）にすること。

#### monitor_tickers.yaml同期漏れ（2026-07-10発見・2026-07-11修正済み）
SYSTEM_MAP.md実態調査（2026-07-10）で、cik_lookup.csv（正本・106件）に対し
monitor_tickers.yaml（99件）が6件未反映（RMBS/ENTG/TER/KLAC/LRCX/APGE、
いずれもStep 7の同期漏れ）だったことが判明し、2026-07-11に手動追加で修正済み
（BXのみ全フラグfalseで除外が正当なため対象外のまま）。cik_lookup.csvと
monitor_tickers.yamlの同期は自動化されておらず、新規登録手順Step 7の手動実施のみに
依存しているため、TICKER-AUDIT-1実装時は両ファイルの差分検出も棚卸し対象に含めること。

#### 銘柄リスト正本参照の一元化との関係（2026-07-11追記・同日完了済み）
本タスクが検出すべき「同期漏れ」の根本原因は、[[TICKER-SOURCE-UNIFY-1]]
（完了・BACKLOG_DONE.md参照）で確定した「本来cik_lookup.csvを参照すべき箇所が
monitor_tickers.yamlを参照している」同型バグ（registration_validator.py・
adjusted_eps_analyzer/pipeline.py）にある。TICKER-AUDIT-1は「症状の棚卸し」、
TICKER-SOURCE-UNIFY-1は「原因の是正」という役割分担だったが、
TICKER-SOURCE-UNIFY-1は対応方針1・2・3すべて2026-07-11中に完了したため、
本タスクが検出すべき同期漏れ自体の新規発生は構造的に減っている。

#### 着手条件
当面は運用でカバー可能。銘柄数がさらに増えた場合に着手。

---

### [TICKER-SOURCE-CONFIG-DUP-1] common/sec_data/config.pyがtickers.pyと機能重複
**優先度:** 低
**分類:** アーキテクチャ / 銘柄リスト参照
**登録日:** 2026-07-11
**発見:** [[TICKER-SOURCE-UNIFY-1]]（完了・BACKLOG_DONE.md参照）対応方針3実施時の横断調査

#### 背景
`common/sec_data/config.py`は`tickers.py`とは別の独立した重複ユーティリティで、
`_load_from_csv()`が独自にcik_lookup.csvを読み、`get_all()`（全銘柄）・
`get_holdings()`・`get_watchlist()`・`get_ticker_info()`を提供している。
`common/sec_data/update.py`（SEC生データ取得）が現在も正規にこれを使用しており
「バグ」ではないが、`tickers.py`の`get_all_tickers()`と機能重複している。

#### 対応方針
統合要否・移行方針は本タスクのスコープ外として別途検討する。
[[TICKER-SOURCE-UNIFY-1]]（完了・BACKLOG_DONE.md参照）の関連課題として記録する。

---

### [REGISTER-FLOW-REDESIGN-1] 新規銘柄登録プロセスの原子性・検証強制力の欠如
**優先度:** 中
**分類:** アーキテクチャ / 銘柄登録フロー
**登録日:** 2026-07-11
**発見:** 2026-07-10の半導体5銘柄monitor_tickers.yaml同期漏れ・BX/ENB孤立エントリの
構造診断（[[TICKER-AUDIT-1]]・[[CIK-ORPHAN-FLAGS-1]]と関連）

#### 診断結果サマリ
2026-07-10のインシデント（RMBS/ENTG/TER/KLAC/LRCXのStep 7/5b未実施、
BX/ENBの孤立エントリ）は単発ミスではなく、登録プロセス自体に以下3つの
構造的欠陥があることに起因する。

#### 1. 原子性の欠如
`cik_lookup.csv`に行を追加した瞬間（Step 0.5）から、その銘柄は
`status=active`かつ各フラグ（tanuki/stonks_silo/eps/hypecore）がtrueであれば
即座に各パイプライン（SEC定期更新・tanuki pipeline.py・stonks-silo pipeline.py・
hypecore.py --batch等）から「対象銘柄」として扱われる。Step 1〜8は独立した
逐次コマンドの羅列であり、オーケストレーション層が存在しないため：
- Step 0.5だけ実施してStep 1〜8が未完了の状態でも、cik_lookup.csv上は
  「完了済み銘柄」と見分けがつかない（status列にはactive/candidate/retiredの
  3値しかなく「登録進行中」を表す状態がない）
- セッション中断（コンテキスト制限・作業者都合等）が発生すると、
  そのまま「中途半端な登録」が本番データに混入する
- 「手動一括登録」（今回の半導体5銘柄のようにStep-by-stepを経ない一括操作）は
  特にこの構造の影響を受けやすく、複数銘柄をまとめて処理する過程で
  個別ステップ（特にStep 7/5b）が抜け落ちやすい

#### 2. 検証の強制力不足（registration_validator.pyの構造的盲点）
`registration_validator.py`のP1系チェック（7ステップ登録完全性）は
**デフォルト実行時（引数なし）のスキャン対象がmonitor_tickers.yamlの
既存銘柄のみ**（`tickers_to_check = target_tickers if target_tickers else monitor_tickers`）。
つまり、monitor_tickers.yamlに未登録の銘柄はP1チェックのループに
そもそも入らず、「monitor_tickers.yaml未登録」自体を検出できるのは
明示的に対象ティッカーを指定した場合（Step 8を個別実行した場合）のみ。
デフォルト実行でこの種の抜けを検出できるのは、cik_lookup.csv全体を
無条件スキャンするP4-CIKOrphanチェックだけだが、これはWARN止まりで
非ブロッキングのため運用上見落とされやすい（[[CIK-ORPHAN-FLAGS-1]]・
今回の6件漏れは共にこの穴の顕在化）。

**原因確定（2026-07-11 git履歴調査）:** P1（monitor_tickers.yamlスキャン）と
P4-CIKOrphan（cik_lookup.csv全体スキャン）は、後から片方が追加されて
想定がズレたのではなく、**同一の初回コミット**（`0d718e2d4`、2026-06-11）で
同時に実装されていた。当時の設計はP1を「monitor_tickers.yamlに登録済みの
運用中銘柄の日次健全性チェック」、P4を「cik_lookup.csv全体を対象にした
孤立エントリの定期監査」と役割分担する意図だったと見られ、後続コミット
（`e902ee037`、同日）ではP4-CIKOrphanが実際に検出したCRWD/FIG/MDB/PUBM/WEAV
5件を「monitor_tickers.yamlへ追加」ではなく「登録抹消（削除）」で解消していた。
つまりP4-CIKOrphanの想定是正手段は当初から「追加」と「削除」の両方があり得る
ため機械的にNG化しづらく、これがWARN据え置きの設計理由だったと推測される。
根本原因は「2つのチェックの役割分担自体」ではなく、**新規登録時にP1相当の
完全性チェックをcik_lookup.csv全体に対しても実行する仕組みが存在しない**こと
（=デフォルト実行モードが「運用中銘柄の日次チェック」用途しか想定しておらず、
「登録直後の完全性監査」用途を兼ねられていない）。詳細は[[TICKER-SOURCE-UNIFY-1]]
（完了・BACKLOG_DONE.md参照）参照。

またNG/WARNの重大度分類にも一貫性の欠如がある：
| チェック | 重大度 | 実質的な影響 |
|---|---|---|
| P1-Step1-SEC（SECデータ未取得） | NG | ブロッキング |
| P1-Step2-Beta（Beta未設定） | WARN | raw yfinance値で代替されるため実害は小さい |
| P1-Step3-Valuation（latest.json未生成） | NG | ブロッキング |
| P1-Step5-HypeCore（poc.json未生成） | WARN | 非ブロッキングだが実質Step5未完了と同義 |
| P1-Step5b-EPS（EPS Analyzerなし） | WARN | 同上（今回6件のうち5件がこれに該当） |
| P1-Step6-Discover | NG | ブロッキング |
| P1-Step7-Monitor | NG | ブロッキングだが上記スキャン範囲の穴で発火しないケースがある |
| P4-CIKOrphan | WARN | cik_lookup全体を見る唯一のセーフティネットだが非ブロッキング |

Step 3.5（segment_config設定）は、既存エントリの内容検証（P3）はあるが
「本来設定すべきなのに未設定」自体を検出する仕組みが存在しない
（[[ENTG-TER-SEGMENT-1]]も同型の見落とし）。Step 4（audit.py --check-beta）は
コード中に明示的に「runtimeチェックのためskip（別途audit.pyで実行）」と
コメントされており、registration_validator.py自体はStep 4の実施有無を
一切検証しない。

#### 3. データソース起因とプロセス起因の混同リスク
今回の調査対象銘柄を分類すると：
- **プロセス起因**（本来フルパイプライン完走すべきだったが手順が飛んだ）:
  RMBS/ENTG/TER/KLAC/LRCX（全件tanuki=true/eps=true/hypecore=true、
  SECデータ取得は正常。2026-07-11に修正済み）
- **データソース起因・真の取得失敗**: ENB（IFRS/40-F企業のためSEC annual data
  0件、`update.py`はエラーを出さず「完了」表示のまま空データを返す。
  P1-Step1-SEC NGで検出可能だが、Step 0（カナダ企業チェック）が本来
  弾くべきケース。列追加時点の遡及登録のため経緯不明のまま残存）
- **データソース起因・評価枠組み非適合（意図的除外）**: APGE（売上ゼロの
  臨床段階バイオ、SEC取得自体は正常）・BX（資産運用会社でPL項目が薄い）・
  SN（20-F提出企業で四半期系列不足、[[SN-TANUKI-DELAY-1]]参照）。
  いずれも全フラグor一部フラグfalseは意図的な設計判断であり「失敗」ではない

この3分類が明示的にラベル化されていないため、「フラグfalseの銘柄」を見ても
「意図的除外」なのか「取得失敗の放置」なのか「登録途中」なのかが
cik_lookup.csvの記載だけでは判別できない。

#### 対応方針（診断のみ・実装は別タスク）
優先順位付きで以下を提案する（実装順は着手時に判断）：
1. ✅ **P4-CIKOrphan相当のチェックをNG（ブロッキング）へ格上げ、または
   デフォルト実行のスキャン範囲をcik_lookup.csv全体に拡張**する
   （最も低コストで効果が大きい。P1のスキャン範囲を`monitor_tickers`から
   `cik_lookup.csv全銘柄`に変更すれば、monitor_tickers未登録自体もP1が
   直接検出できるようになる。**この修正自体は[[TICKER-SOURCE-UNIFY-1]]
   （完了・BACKLOG_DONE.md参照）の確定バグ2と同一であり、着手時はそちらの
   対応方針2をそのまま適用すればよい**）
   → **2026-07-11 コミット`ba2cfef42`で完了**（`tickers_to_check`のデフォルト値を
   cik_lookup.csv全銘柄に変更）。対応方針2〜5は引き続き未着手。
2. **cik_lookup.csvのstatus列に「登録進行中」を表す値を追加する**
   （例: `status=provisioning`。Step 8のNG=0確認後に`active`へ昇格する運用にすれば、
   各パイプラインは`status=active`のみを対象とすることで中途半端な登録の
   本番混入を防げる。ただし既存パイプラインの対象銘柄取得ロジック
   （フラグベース）に`status`条件を追加する変更が必要）
3. **Step 1〜8を1つのオーケストレーションスクリプトにまとめ、
   全ステップ成功後にのみcik_lookup.csvへコミット可能にする**（原子化。
   実装コストは最も高いが、根本解決になる）
4. **cik_lookup.csvに「意図的除外」を示す列・値を追加する**
   （例: `exclusion_reason`列。APGE/BX/SN等の"評価枠組み非適合"ケースを
   明示すれば、フラグfalse＝異常ではないことがCSV自体から読み取れる）
5. **「手動一括登録」という抜け道を塞ぎ、単一エントリポイント経由の
   登録に集約する**（複数銘柄を一括処理する場合でも、内部的には
   1銘柄ずつ完全なStep 1〜8を実行する設計にする）

#### 優先度についての所感
現時点では実際のIV計算等を歪める実害はなく（今回の漏れはデータ欠損であり
誤計算ではない）、ARCH-DATA-1のような「優先度：高」の即時実害はない。
一方で同型の見落とし（BX/ENB→今回の6件）が既に2回発生しており、
銘柄数が増えるほど再発確率が上がる構造的問題のため「優先度：中」を提案する。
[[TICKER-AUDIT-1]]・[[PREFLIGHT-CHECK-1]]と統合的に設計すべき
（別々に実装しない）。

**着手順の推奨（2026-07-11追記・同日完了済み）:** 対応方針1（P4のNG格上げ/
スキャン範囲拡張）は[[TICKER-SOURCE-UNIFY-1]]（完了・BACKLOG_DONE.md参照）で
確定した同型バグの修正と同一であり、上記の通り既に完了している。
本タスクの対応方針2〜5（status列拡張・オーケストレーション化等、
コストの高い対応）は引き続き未着手。

---

### [PREFLIGHT-CHECK-1] 新規登録時のデータ品質プリフライトチェック
**優先度:** 中
**分類:** 品質管理 / 銘柄登録フロー
**登録日:** 2026-07-02

#### 背景
2026-07-02のWST/APGE/CON/SN一括登録で、4銘柄中3銘柄がRevenue品質ISSUEを検出した
（APGE=売上ゼロ・臨床段階バイオ、CON=2024年IPO直後でQ1 2023データ欠落、
SN=2023年20-F提出企業でQ2-Q4 2025データ欠落）。IPO/スピンオフ直後や
臨床段階企業・直近まで20-F提出企業（外国民間発行体）はXBRLデータが構造的に
不安定な傾向があることが判明した。

#### 想定機能
CLAUDE_CODE_START.mdのStep 0.5直後に「プリフライトチェック」ステップを新設し、
Step1（SECデータ取得）本実行前に以下を自動検知する：
① SEC EDGARの提出履歴（submissions API）から上場日/直近フォーム種別を確認し、
   上場後3年未満であれば「データ不安定リスクあり」を自動フラグ
② 直近提出書類が20-F等（10-K/10-Q以外）の場合、四半期データ欠落の
   可能性を自動フラグ
③ 収益系XBRLタグ（Revenues等）が存在しない場合、
   「売上ゼロ企業の可能性」を自動フラグ
④ フラグが立った銘柄はStep1実行前にユーザーへ警告表示し、
   続行するか確認を求める（自動停止はしない、判断材料の提示に留める）

#### 優先度
中（次回以降の新規登録が発生する前に着手が望ましい）

#### [[REGISTER-FLOW-REDESIGN-1]]・[[TICKER-SOURCE-UNIFY-1]]との関係（2026-07-11追記）
本タスクは「データソース起因（真の取得失敗）」を登録**前**に検知する仕組みであり、
ENB（IFRS/40-F企業、SEC annual data 0件のまま遡及登録され孤立）は本タスクが
実装されていれば①のフラグで登録前に弾けたはずの事例。一方
REGISTER-FLOW-REDESIGN-1・TICKER-SOURCE-UNIFY-1（完了・BACKLOG_DONE.md参照）は
「プロセス起因（手順の飛ばし・銘柄リスト参照の取り違え）」を扱っており、
対象とする失敗モードが異なる（データソース起因 vs プロセス起因の分類は
[[REGISTER-FLOW-REDESIGN-1]]参照）。両者は補完関係にあり、どちらかで
代替できるものではない。

#### 設計メモ（2026-07-02・検討中）
- ARCH-DATA-1のパターン判定ロジックを共有する統合設計とする
  （別々に実装しない）。
- 未知パターン対応の学習ループ案：
  ① 異常検知（既存のreport_consistency_check.py等）
  ② カタログに既知パターンがあれば自動判定
  ③ 未知の場合、AIが仮説を生成
  ④ 仮説を一次情報（SEC EDGAR等）で検証
  ⑤ 検証済みならカタログに追加、①に還元
- ④の検証プロセスはClaude Codeが自律的に行ってよい
  （2026-07-02のCON/SN/APGE調査で実証済み：仮説形成→一次情報での
  検証→根拠明記、という流れが機能した）。
  ただし「対応の決定」（コード修正の実施・登録継続の可否等）は
  引き続き人間確認を挟む。事実確認（仮説→検証）と対応決定を
  分離すること。
- 仮説と検証結果には、判定根拠となった一次情報（URL・具体的数値）を
  必ず併記することをルール化する（確証バイアス防止）。
- 検証役／実装役の権限分離案：Claude Codeのサブエージェント機能
  （`/agents`）を使い、検証役（Read/Grep/Glob/WebFetch等のみ、
  Edit権限なし）と実装役（検証役の報告を受けてから対応・修正を行う）
  を分離する案がある。ただし未着手・要検討（2026-07-02時点）。

---

## 優先度：低（アイデア段階）

### [TAIL-DETAIL-1] detail.htmlレイアウト微調整
**優先度:** 低
**分類:** UX / TANUKI TAIL
**登録日:** 2026-06-27

#### 問題
- DCF右カラムの下半分が空白（AI視点左カラムの方が縦に長いため）
- 内部統制がAI視点左カラムの下に食い込んでいる（並列ブロックの外に出ていない）

#### 対応方針
- AI視点・DCF並列ブロックのmin-height調整またはgrid align設定
- 内部統制セクションを並列ブロックの完全な下に配置する

---

### [UX-FLOW-1] On a Journey標準利用フローの設計
**優先度:** 低（思想設計タスク、実装ではなく方針検討から開始）
**分類:** 設計課題 / 全画面横断

#### 内容
画面間を行き来する非線形な利用が前提だが、緩やかな標準利用フロー
（例: stock.htmlで個別検証→TANUKI SCOREで横断相対判断、等）を
今後設計したい。

#### 格上げ検討理由（2026-07-01）
EXTREME-FEAR-1対応時、買い候補TOP10機能（TANUKI score×乖離率×funda×phaseベースの
銘柄選定）のナビ登録先を検討した際、本来TANUKI SCOREの役割に近い機能をMarket Pulse
配下に置く形で暫定決着した。これは各画面の役割定義はあるものの、画面間の回遊動線・
機能配置の指針が未設計であることに起因する。今後複数システムの性質を跨ぐ機能が増える
たびに同種の判断コストが発生するため、次セッション以降の設計着手候補として優先的に
検討する。

---

### [MULTI-1] マルチバリュエーション表示
- 現状: DCF一本槍
- 改善: DCF / PEG / EV/Sales / RICE / HypeCoreを並列スコアカード表示
- GPT提案: 2026-05-30
- 関連（2026-07-10追記）: [[RICE-INTEGRATE-1]]とRICE指標の活用目的が部分重複。
  本タスク（MULTI-1）は画面表示（並列スコアカード）が主眼、RICE-INTEGRATE-1は
  スクリーニング判定への組み込みが主眼という役割分担。どちらかの着手時に
  統合要否を判断する。

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

### [TEST-STALE-IV-1] test_iv_formula.pyがALPHA-REDESIGN-1に未追従
**優先度:** 低
**分類:** テスト保守 / 品質管理
**発見:** 2026-07-02（ARCH-DATA-1-YTDスポットチェック時）

#### 問題
tests/test_iv_formula.pyがALPHA-REDESIGN-1（2026-06-25完了）以前の旧計算式
（iv_pt = v0_rm × (1+alpha) + rpo_pv + go_pv）をハードコードしたまま。
現行core_calculator.pyはalpha=0.0固定（alpha廃止済み）だが、latest.jsonには
旧フィールドalphaが残存しているため、テストの再計算値と保存値が乖離し
NVDA/MSFTで恒常的にpytest失敗する（機能的な実害はなし、テストコードのみ陳腐化）。

#### 対応方針
test_iv_formula.pyの期待値算出ロジックをALPHA-REDESIGN-1後の計算式に更新する。

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

### [ADMIN-LOG-1] admin.html・stock.htmlにconsole.log残存
**優先度:** 低
**分類:** コード品質 / admin.html・TANUKI VALUATION
**発見:** 2026-06-26横断バグ調査

#### 問題
本番HTMLにconsole.logが32件残存している：
- admin.html: 26件（ワークフロー実行ポーリングのデバッグトレース）
- stock.html: 6件（matricesタブ読み込みデバッグログ）

#### 対応方針
不要なconsole.logを削除する。
admin.htmlのポーリングログはワークフロー実行確認のデバッグとして
有用な場合があるため、削除前に必要性を判断する。

---

### [PICK-FIELD-1] daily_pick.jsonとhistory.jsonのフィールド名乖離
**優先度:** 低
**分類:** データ定義不整合 / TANUKI SCORE
**発見:** 2026-06-26横断バグ調査

#### 問題
同一データが異なるキー名で保存されている：
- daily_pick.json: selection_reason
- history.json: reason

daily_pick.pyが書き込む際にキー名が統一されていない。
機能的な問題はないが保守上の混乱を招く。

#### 対応方針
どちらかに統一する（selection_reasonを推奨・より説明的なため）。
history.jsonの既存エントリは移行不要（読み取り時に両キーを参照するフォールバックを追加）。

---

### [SN-TANUKI-DELAY-1] SN TANUKI VALUATION再検討
**優先度:** 低
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-02

#### 背景
SNは2025年まで20-F提出企業（外国民間発行体）のため四半期報告義務がなく、
四半期データが2026年Q1分（初回10-Q、2026-05-06提出）のみ存在する。
四半期トレンド・TTM系列が構築不能なため、当面 tanuki=false で保留中。

#### 対応
2026年8月頃のQ2 10-Q提出後、四半期系列が蓄積された時点で tanuki=true に戻し
TANUKI VALUATION Step3（pipeline.py）を実行する。

#### 優先度
低（時期依存、8月まで着手不可）

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
- 懸念: OpenDのローカルPC起動が前提だが、KoichiさんのAutoTrade運用のためOpenDは
  既に常時起動しており、この制約は実質的に解消済み（2026-07-10確認）。
  ただしPC自体の停止・再起動（ハードウェア障害・停電・OS更新等）が発生した場合は
  連携も止まるため、「運用上の恒常的な制約」ではなく「稀な障害シナリオ」として
  引き続き留意する
- 参考: https://www.moomoo.com/ja/community/feed/moomoo-api-skills-now-unlocked-ai-becomes-a-24-7-116413328916486

【SCREEN-2STAGE-1】二段階スクリーニング運用（構想）
- 背景: moomoo AIによる価格・出来高ベースのテクニカルスクリーニング
  （移動平均線順序・52週高値位置・RSI等）は取得できるが、
  ミネルヴィニ条件に必要なRS Rating・EPS/売上成長率の加速は
  moomoo単体では評価できないことが判明（2026-07-02）
- 想定運用: ①moomooで価格モメンタム側を粗くスクリーニング
  →②On-a-Journey登録後、既存の四半期系列データ
  （TANUKI VALUATIONのnormalized/series_q等）を使い、
  EPS/売上成長率が直近四半期で加速しているかを事後確認する
- 目的: 「それっぽい」スクリーニングから、ミネルヴィニ条件に
  近い精度への引き上げ
- 実装イメージ: 既存の四半期系列から成長率加速判定を行う
  軽量スクリプト（新規 or 既存パイプラインへの追加関数）。
  詳細設計は未着手
- 優先度: 低（構想段階、着手時期未定）

### 【TANUKI TAIL】
- 残タスク: データパス統一（優先度低）
- ~~EWM楽観バイアス係数~~ → TAIL-EWM-1としてB案（現状維持）でクローズ済み（2026-06-26）

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

### [DESIGN-16] Moomoo Skills Hub（情報検索・個別株ダイジェスト）のDISCOVER機能への組み込み検討
**優先度:** 低（設計相談は完了・実装未着手）
**分類:** 設計課題 / DISCOVER
**登録日:** 2026-07-10
**ステータス:** 保留（2026-07-10追記: OpenDは常時起動確認済み。ローカル定期実行での
自動化を検討可能、詳細設計は別タスク）

#### 背景
moomoo証券が2026年5月にリリースした「Moomoo Skills Hub」には、Moomoo API Skill
（既存BACKLOG「Moomoo API Skill 移行」参照）に加え、投資分析系の6Skillが追加された。
うち以下2つがDISCOVER機能と関連しうるため調査した：
- **情報検索Skill**: moomoo上のニュース・適時開示・レポートを横断検索
- **個別株ダイジェストSkill**: 銘柄別に最新ニュース・市況を要約

#### 調査結果①：現行DISCOVERの実行環境
`src/discover/collect.py`（日次）・`catalyst.py`（週次）・`impact_predictor.py`は
いずれもGitHub Actions（`.github/workflows/Discover_Update.yml` /
`Catalyst_Update.yml`、`runs-on: ubuntu-latest`）上で完全自動実行されており、
ローカルPC・OpenD等のローカル依存は一切ない。
一方、Moomoo Skills Hubは（Moomoo API Skillと同様）ローカルゲートウェイ
OpenDを介したセキュリティ設計（ローカルゲートウェイ＋パスワード＋監査ログの
三層構成）を前提とする。

**2026-07-10追記:** KoichiさんはAutoTrade運用のためOpenDを既に常時起動しており、
「OpenD起動」という前提条件は実質的に満たされている。これにより、moomoo Skills Hub
（情報検索Skill・個別株ダイジェストSkill）をローカルのタスクスケジューラ等で
定期実行し、DISCOVERパイプラインの一部または代替として自動化できる可能性がある。
ただし、GitHub Actions（クラウド、Koichiさんの端末状態に非依存）とローカル
タスクスケジューラ（Koichiさんの端末稼働・OpenD接続状態に依存）では可用性の
性質が異なる（PC自体の停止・再起動時はローカル側のみ止まる）ため、
**完全な代替ではなく「補完」または「条件付き代替」として位置づける。**

#### 調査結果②：データ範囲の比較
| 観点 | 現行DISCOVER（Grok/NewsAPI） | Moomoo Skills Hub（情報検索・個別株ダイジェスト） |
|---|---|---|
| 対応市場 | 制約なし（Web検索ベース） | 日本語版は香港・米国・日本・シンガポール・マレーシアが対象 |
| 保有・候補銘柄の対応可否 | ○ | ○（cik_lookup.csv登録銘柄はyfinance country確認済みの範囲で全て米国上場のため対応市場内） |
| 実行形態 | 完全自動（スケジュール実行・GitHub Actions、Koichiさんの端末状態に非依存） | オンデマンド呼び出しに加え、OpenD常時起動済みのためローカルタスクスケジューラ等での定期実行も可能（ただしKoichiさんの端末稼働に依存） |
| 機能の性質 | 発掘・分類・方向性予測（catalyst.py=上振れ事象発掘、impact_predictor.py=direction/magnitude予測） | 横断検索・要約（プル型の深掘り調査ツール） |
| 重複/補完 | — | **補完、または条件付き代替**。継続的なバッチ発掘の完全な置き換えとしてはクラウド/ローカルの可用性特性が異なるため慎重な判断が必要だが、特定銘柄のオンデマンド深掘り（moomoo一次情報での裏取り）や、ローカル定期実行によるDISCOVER補助バッチとしての活用の両方に価値がある |

#### 調査結果③：Koichiさん側の前提条件（Claude Codeが代行できない範囲）
- moomoo証券口座の保有・開設
- OpenDのローカル起動（**2026-07-10追記: AutoTrade運用のため既に常時起動済み、追加対応不要**）
- Moomoo API利用規約への同意

#### チャット側の推奨方針（2026-07-10改訂）
OpenD常時起動という前提条件が既に満たされているため、「時期尚早」ではなく
**ローカル定期実行での自動化（DISCOVER補助バッチ）を検討可能な段階**にある。
ただし、GitHub Actions（クラウド・無人運用・端末状態非依存）と
ローカルタスクスケジューラ（端末稼働・OpenD接続状態に依存）は可用性の性質が
異なるため、DISCOVERパイプラインの完全な置き換えではなく、当面は
「補完」または「条件付き代替」として位置づける。着手判断は以下の順で行う：
1. 既存BACKLOG「Moomoo API Skill 移行」（signal.jsonバックテスト後に判断）の
   結論と合わせて、Moomoo Skills Hub全体の導入要否を判断する
2. 導入する場合の位置づけを設計する（案A: chat側オンデマンド利用のみ、
   案B: ローカルタスクスケジューラでの定期実行によるDISCOVER補助バッチ化。
   案Bを採る場合はPC停止・再起動時のデータ欠落をどう扱うか設計が必要）
3. Moomoo API利用規約への同意状況を確認してから着手する

#### 実装難易度
低〜中（Skillのインストール自体は容易。ローカル定期実行を選ぶ場合は
タスクスケジューラ設定・PC停止時のフォールバック設計が別途必要）

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
優先度：高のバグ修正を先に実施してから、優先度：中の機能追加に移る。

**バグ修正（優先）:**
1. ~~ALPHA-REDESIGN-2: stock.htmlのα乗算残存・説明文修正~~ ✅ 2026-06-26完了
2. ~~STAGE0-STOCK-1: stock.htmlでstage=0が非表示~~ ✅ 2026-06-26完了
3. ~~HYPE-INF-1: poc.jsonにInf値混入（ASTS/JOBY）~~ ✅ 2026-06-26完了

**データ補完（コマンド実行のみ）:**
4. ~~SEC-CTRL-2: tailの内部統制データ8銘柄一括生成~~ ✅ 2026-06-26完了
5. ~~CATALYST-DATA-1: catalyst.py --allで全94銘柄初回投入~~ ✅ 2026-06-26完了

**機能・設定修正:**
6. ~~HYPE-FLAG-1: CSGP/ZSのcik_lookupフラグ設定~~ ✅ 2026-06-26完了
7. ~~HYPE-ENB-1: ENBのhypecore=false修正~~ ✅ 2026-06-26完了
8. ~~DISCOVER-THEMES-1: macro_themes_history.json初回生成~~ ✅ 2026-06-26完了

**本日追加完了（未予定だったが実施）:**
9. ~~TAIL-SAT-CORE-1: satelliteモーダルをcore同等6タブ構成に変更~~ ✅ 2026-06-26完了

※ 2026-06-26完了: EVAL-3・TANUKI-ENB-1・SILO-UX-1・MP-ASSETFLOW-UI-1・
  TANUKI-ROE-2（部分）・SS-1（クローズ）
※ 2026-06-26横断調査・バグ調査実施: PREVENT-1〜5・各バグ・設定不整合をBACKLOG登録済み
※ 2026-06-27完了: CN-ENB-1・RKLB-CLEANUP-1・PICK-DUP-1・TTM-NULL-1・STONKS-DIV-1（ガード確認+テスト追加）・PREVENT-1・PREVENT-2・PREVENT-3・SEC-CTRL-1（パス変更・Grok翻訳・マイグレーション）
※ 2026-07-01完了: STOCK-GLOSSARY-1・PREVENT-4・QBITconfig孤立エントリ削除・DUPONT-COLOR-1・EPS-BX-1・EXTREME-FEAR-1
※ 2026-07-03完了: ARCH-DATA-1-YTD（AMZN固有の追加回帰バグA・B発見・修正含め全101銘柄ロールアウト完了。副産物としてTEST-STALE-IV-1を登録）
※ 2026-07-08完了: MACRO-NFP-HIST-1（NFP過去履歴370件を水準→前月比に一括変換）・
  TTM-NULL-1（calc_ttm_series()内の見落とし箇所を追加修正、2026-06-27対応時の残存分）・
  STONKS-DIV-1（再調査の結果ガード済みと再確認、L625の回帰テスト追加）・
  BACKLOG-DEDUP-CHECK-1（BACKLOG.md/BACKLOG_DONE.md間ID重複の全数チェック、削除対象なしと判定）
※ 2026-07-09完了: TAIL-DCF-TABIDX-1（DCFタブindex不一致修正）・
  新規銘柄5件登録（RMBS/ENTG/TER/KLAC/LRCX）・PARSER-ENTG-COMPYEAR-1・
  XBRL-TAG-KLAC-1・CHECK-QREV-FYE-1（パーサーバグ3件根本修正、
  副産物としてXBRL-TAG-KLAC-1-FOLLOWUPを登録）
※ 2026-07-10: サテライト投資候補91銘柄への前提妥当性チェック展開に伴い、
  新規バグ・課題16件超を登録（GROWTH-SOURCE-LABEL-1・SEC-TAG-FICO-CPRT-1・
  STALE-REPORT-CLEANUP-1・CIK-ORPHAN-FLAGS-1・DESIGN-16等）。精査の結果
  GROWTH-FLOOR-VERDICT-1・DCF-REL-SYNC-1を「中」→「高」へ格上げ、
  ARCH-DATA-1-CONSOLIDATE-1を完了クローズ、RICE-INTEGRATE-1/MULTI-1に
  相互参照を追記。common/screening/にdcf_validity_checker.py・
  report_txt_parser.pyを正式格納。CHAT_RULES.mdに確認プロセス適用範囲・
  銘柄スクリーニング標準フローを追記。この結果、次に着手可能な
  優先度：高の項目はGROWTH-FLOOR-VERDICT-1・DCF-REL-SYNC-1・ARCH-DATA-1
  （着手条件成立済み・ただし難易度高）の3件（BACKTEST-SCORE-1は
  着手条件未達のため2026年10月以降まで対象外）。
※ 2026-07-11: SYSTEM_MAP.md全体像の実態調査を実施し出力先パス誤記5件を修正、
  銘柄振り分けの正本（cik_lookup.csv）セクションを新設。monitor_tickers.yaml
  同期漏れ6件（APGE/RMBS/ENTG/TER/KLAC/LRCX）を修正し、同6銘柄のEPS Analyzer
  データ生成（Step 5b）も実施。新規銘柄登録プロセスの構造診断を行い
  REGISTER-FLOW-REDESIGN-1を登録、続く銘柄リスト参照の横断調査で
  TICKER-SOURCE-UNIFY-1（根本課題）を登録。セッション終了時ブラッシュアップで
  PREVENT-5・TICKER-AUDIT-1・TICKER-SOURCE-UNIFY-1・REGISTER-FLOW-REDESIGN-1・
  PREFLIGHT-CHECK-1（いずれも優先度：中）の「## 優先度：低」への誤配置を
  「## 優先度：中」へ修正。
  **次セッションの筆頭候補は[[TICKER-SOURCE-UNIFY-1]]**（既存関数
  `common/sec_data/tickers.py`を呼ぶだけで直せる低コスト・低リスク対応。
  確定済みバグ2件: `registration_validator.py`のP1デフォルトスキャン・
  `adjusted_eps_analyzer/pipeline.py::run()`）。着手後、余力があれば
  [[REGISTER-FLOW-REDESIGN-1]]の残り対応方針（status列拡張・
  オーケストレーション化等、コスト高）に進む。

（ARCH-SCORE-SYNC-1は2026-06-20、TAIL-SEC-1/EPIC-LEGEND-1は2026-06-21、
EPIC-HEADER-1は2026-06-21、EPIC-LAYOUT-1グループA/グループBは2026-06-22、
EPIC-LAYOUT-1グループC（SILO-DISP-3）・MP-GAUGE-NEEDLE-1・MACRO-DISP-2は
2026-06-23に完了。BACKLOG_DONE.md参照）
