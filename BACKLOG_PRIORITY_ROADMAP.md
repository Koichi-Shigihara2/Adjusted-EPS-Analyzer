# BACKLOG優先度ロードマップ

**作成日:** 2026-08-30
**作成経緯:** 2026-08-29〜30の全5ラウンドで、BACKLOG.md未完了項目181件
全件の「陳腐化・ニーズ・課題認識の合理性」を検証（9件をBACKLOG_DONE.md
へ移設、4件を⚠️課題認識に疑義ありとして報告のみに留めた）。残る168件を
「開発合理性による分類＋重要性判断＋着手手順」まで踏み込んで整理した。
Koichiさんの指示「このレベルまでやって棚卸である」を受け、この方法論と
実施計画をリポジトリに恒久記録として残す。

**更新（2026-08-30、診断結論の再検証・全19ラウンド完了後）**: 事例17
（CHAT_RULES.md）を踏まえ、168件（フェーズ1バッチAで8件完了済み分を
除く160件相当）全件について「診断結論そのものの妥当性」を実コード・
実データで再検証した。結果、2件が診断結論自体の陳腐化（登録当時は
正しかったが後続の別対応で解消済み・BACKLOG本体への反映漏れ）と判明し
BACKLOG_DONE.mdへ移設（`[[MP-TOOLTIP-1]]`・`[[MARKETDATA-AS-IS-AUDIT-
PY-OMITTED-1]]`）。現存総数は**162件**（168−8完了−2移設+4疑義件を
再カウント調整後の機械カウント値）。詳細はチャット履歴の全19ラウンド
記録を参照。この再検証と合わせて、下記5節のクラスタ構成を「タイトル・
カテゴリの類似性」ではなく「実際のコード上の隣接性」基準で再分析した
（バッチAの教訓を踏まえた対応、5B節参照）。

**更新（2026-08-30、データ鮮度監視実装＋フェーズ1バッチB完了後）**:
`[[DATA-FRESHNESS-MONITORING-FUTURE-IDEA-1]]`をKoichiさん判断で優先度
引き上げの上実装完了・BACKLOG_DONE.mdへ移設。フェーズ1バッチB6件のうち
4件（`[[FCF-CAGR-YEARS-MISMATCH-1]]`・`[[EPS-DISCREPANCY-FLAG-
OVERLOAD-1]]`・`[[HYPECORE-REALSTRONG-DUAL-IMPL-1]]`・
`[[TVGROWTH-EXPLICIT-DEFAULT-AMBIGUOUS-1]]`）を実装完了・BACKLOG_DONE.md
へ移設。残る2件（`[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]`・
`[[RICE-ADJ-ASYMMETRIC-ZERO-1]]`）はKoichiさんの設計判断が必要と判明した
ため実装を見送り、BACKLOG.mdに再検証記録を追記した上で据え置き。
現存総数は**157件**（機械カウント値、`grep -c "^### \["`で確認）。

**このドキュメントの位置づけ:** 個別項目の詳細・最新状態は常に
`BACKLOG.md`が正（このロードマップは2026-08-30時点のスナップショット）。
新規登録項目や状態変化はBACKLOG.md側にのみ反映され、このロードマップは
フェーズ1消化時・大きなBACKLOG変動時に更新する運用とする。

---

## 1. 棚卸しの方法論（今後のバックログ運用の基準）

タイトル・優先度欄だけを見た機械的な仕分けは棚卸しとして**不十分**で
ある。真の棚卸しは、以下の4段階を経て初めて完了する。

1. **陳腐化検証**: 本文精読＋実コード照合で、記載内容と現状の一致を
   確認する（コードが変わっていないか・データが変わっていないか）
2. **ニーズ検証**: 対応する意味が今も残っているか（既に別対応で
   解消済み、対象が窓外に出た等で不要になっていないか）
3. **課題認識の合理性検証**: BACKLOG記載の診断自体が実コードに照らして
   妥当か（診断の前提が誤っていないか、依存先エントリの状態と矛盾して
   いないか）
4. **開発合理性による分類＋重要性判断＋着手手順の提案**: 1〜3を経て
   有効と判定された項目群を、対応する意味の性質でカテゴリ分類し、
   カテゴリ間・案件間で重要性を比較し、着手順を具体化する

1〜3のみでは「今のところ嘘は書かれていないリスト」にしかならず、
Koichiさんが実際に次に何をすべきか判断できる状態（4）まで到達して
初めて「棚卸が完了した」と言える。

---

## 2. カテゴリ構成（2026-08-30時点、168件）

| カテゴリ | 定義 | 件数 | 重要性順位 |
|---|---|---|---|
| A. 計算結果直結の不具合 | IV・DCF・ROE・EPS・TANUKI SCORE等の数値・判定に影響しうるバグ | 44件 | 1位（最優先） |
| B. データ品質・欠損（実害限定的） | 特定銘柄・フィールドの欠落/異常だが現時点で最終計算への影響は小さいか未確認 | 16件 | 2位 |
| C. 表示・UI不整合 | フロントエンドの見た目・文言のみ、計算結果自体は正しい | 15件 | 3位 |
| F. テスト・品質保証のギャップ | 検証ロジック・監査カバレッジの欠落 | 11件 | 4位 |
| E. 監視・観測性・運用改善 | 障害検知・再発防止の仕組み | 10件 | 5位 |
| D. アーキテクチャ・技術的負債 | 将来の保守性・拡張性に関わる設計課題 | 33件 | 6位 |
| G. 新機能・拡張提案 | 未着手のアイデア・設計検討段階のもの | 30件 | 7位（既存バグ修正とは別予算枠） |
| H. ドキュメント・命名規則整備 | コメント・命名・カタログの整合性 | 9件 | 8位 |

**判断軸**: 実害の大きさ（投資判断への影響）・影響範囲（銘柄数/消費者
数）・放置コスト（時間経過での悪化性）・是正コスト。

Aが最優先なのは、唯一「Koichiさんの投資判断に使う数値そのものが変わり
うる」カテゴリだからである。B・Cは実害が確認されているか計算結果に
影響しないため2〜3位。D・E・Fは「今すぐ困らないが将来のコスト」という
性質が共通し、Fは再発防止の仕組み欠如というやや直接的なリスクがある
ためE・Dより上位に置いた。Gは新規投資の意思決定そのものであり、既存
バグ修正とは別の予算枠として扱うべきものである。

---

## 3. フェーズ1: 最優先グループ（次に着手すべき候補、10件）

「実害大×是正コスト低」の基準で抽出。いずれも局所的な修正で完結する
見込み。

1. ✅**完了**（2026-08-30、バッチB）~~`[[FCF-CAGR-YEARS-MISMATCH-1]]`~~
   — stock.html CAGR(3yr)誤表示（BACKLOG_DONE.md参照）
2. `[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]` — VRT/CRM
   のROE実害。バッチBで再検証したが、修正には`_extract_values_
   best_candidate()`（既に何重にも安全策が組み込まれた複雑な関数）・
   `_resolve_bs_entity_mixing()`（既存安全原則の変更を伴う）という
   既存の重要ロジックの大幅書き換えと105銘柄全体シミュレーションが
   必要と判明したため実装せず、Koichiさんの判断待ちとして据え置き
   （詳細はBACKLOG.md本項目「再検証記録」参照）
3. ✅**完了**（2026-08-30、バッチA cluster 2）~~`[[CASH-TAG-MISSING-1]]`~~
   — 複数銘柄でcash_and_equivalents欠落（BACKLOG_DONE.md参照）
4. ✅**完了**（2026-08-30、バッチB）~~`[[EPS-DISCREPANCY-FLAG-OVERLOAD-1]]`~~
   — フラグ名の意味重複（BACKLOG_DONE.md参照）
5. `[[RICE-ADJ-ASYMMETRIC-ZERO-1]]` — 非対称0フロア設計。バッチBで
   再検証したが、どちらのガード仕様が正しいかは表示数値そのものが
   変わる製品判断でありKoichiさんの設計判断が必要なため実装せず据え置き
   （詳細はBACKLOG.md本項目「再検証記録」参照）
6. ✅**完了**（2026-08-30、バッチB）~~`[[HYPECORE-REALSTRONG-DUAL-IMPL-1]]`~~
   — Python/JS二重実装の矛盾リスク（BACKLOG_DONE.md参照）
7. ✅**完了**（2026-08-30、バッチA cluster 1）
   ~~`[[QUARTERLY-CLASSIFY-PERIOD-NO-UPPER-BOUND-1]]`~~ — is_annual判定に
   上限なし（BACKLOG_DONE.md参照）
8. ✅**完了**（2026-08-30、バッチA cluster 3）~~`[[V0-V0RM-CONFUSION-RISK-1]]`~~
   — v0/v0_rm取り違えリスク（BACKLOG_DONE.md参照）
9. ✅**完了**（2026-08-30、バッチB）~~`[[TVGROWTH-EXPLICIT-DEFAULT-AMBIGUOUS-1]]`~~
   — terminal_growth明示/未設定の区別不能（BACKLOG_DONE.md参照）
10. ✅**完了**（2026-08-30、バッチA cluster 1）
    ~~`[[LAYER3-ANNUAL-MISCLASSIFICATION-NOW-RMBS-1]]`~~ — 実証済み修正
    パターンの横展開（BACKLOG_DONE.md参照）

上記10件中8件が完了（バッチA4件・バッチB4件）。残る2件
（`[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]`・
`[[RICE-ADJ-ASYMMETRIC-ZERO-1]]`）はいずれもKoichiさんの設計判断が
必要と判明したため実装を見送り、判断待ちとして据え置き。

---

## 4. フェーズ2・フェーズ3

**フェーズ2（中期対応グループ、約41件）**: Aカテゴリの「中」重要度の
うちフェーズ1に含めなかったもの・Cの表示整合性群・E/Fの運用改善系・
Dのepic級設計課題が該当する。

**フェーズ3（長期・保留グループ、約117件）**: 各カテゴリの「低」重要度
全件が該当する。外部データソース依存で対応不能なもの、実害ゼロ確認済み
の記録項目、Koichiさんの投資判断待ちの新機能構想（Gカテゴリの大半）が
中心。

個別IDの全件列挙はここでは行わない（BACKLOG.md本体が正、対象IDは各
項目の`### [ID]`ヘッダで機械的に再抽出可能）。

---

## 5. まとめて対応すべき依存関係クラスタ（6組）

同一コード領域・同一configファイル・同一画面群に関わる項目は、個別に
着手するより一括対応した方が効率的。

1. ✅**完了**（2026-08-30、バッチA）**Layer3期間分類クラスタ**
   （同一関数`_classify_period()`/`is_annual`周辺）:
   `[[LAYER3-ANNUAL-MISCLASSIFICATION-NOW-RMBS-1]]`・
   `[[LAYER3-ANNUAL-MISCLASSIFICATION-MINOR-5TICKERS-1]]`・
   `[[QUARTERLY-CLASSIFY-PERIOD-NO-UPPER-BOUND-1]]`（以上3件、真の
   実装対応）・`[[LAYER3-FY-SCALE-ANNUAL-MISFLAG-1]]`（前提誤りと
   判明、対応不要でクローズ）。4件は当初想定と異なり単一の根本原因を
   共有していなかった（3種の異なる原因・解消経路）。詳細は
   BACKLOG_DONE.md参照
2. ✅**完了**（2026-08-30、バッチA）**XBRL候補タグ拡張バッチ**
   （「候補タグ追加＋全母集団シミュレーション」という同一パターン）:
   `[[CASH-TAG-MISSING-1]]`のみバッチAで実装完了（BACKLOG_DONE.md
   参照）。`[[LITE-COGS-DA-TAG-UNMERGED-1]]`（複数タグの合算が必要）・
   `[[LAYER3-GA-STANDALONE-TAG-UNMAPPED-1]]`（Layer2/Layer3双方への
   新規フィールド追加が必要）は、着手前の再検証でこのバッチの単純な
   「候補タグ追加」パターンに当てはまらないと判明したため未実装のまま
   バッチB候補として据え置き
3. **stock.html表示整合性バッチ**（同一ファイル改修）、バッチAで3/4件
   実装完了: ✅`[[STOCK-HTML-CLASSIFICATION-MISSING-1]]`・
   ✅`[[DCF-RELIABILITY-LABEL-MISMATCH-1]]`・
   ✅`[[V0-V0RM-CONFUSION-RISK-1]]`（BACKLOG_DONE.md参照）。
   `[[SENS-MATRIX-DUAL-IMPL-1]]`は死コード（`alpha`変数）削除のみ完了、
   核心の5×5/3×3統一方針はKoichiさんの設計判断待ちでBACKLOG.mdに
   残置（部分対応）
4. **TAIL KPIパイプラインクラスタ**（同一パイプラインの入口〜出口）:
   `[[TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1]]`・`[[TAIL-XBRL-SEGMENT-
   FETCHER-NONDIMENSIONED-GAP-1]]`・`[[TAIL-THESIS-KPIS-EMPTY-ADBE-
   APGE-1]]`・`[[TAIL-LAYER3-FORMULA-YOY-UNSUPPORTED-1]]`
5. **FCF-CONVRATEクラスタ**（同一config `fcf_conversion_config.json`
   の再較正）: `[[FCF-CONVRATE-LOWER-DIVERGENCE-1]]`・
   `[[FCF-CONVRATE-DESIGN-LIMIT-1]]`・`[[AMZN-CONVRATE-OVERRIDE-
   REVIEW-1]]`
6. **Discover表示クラスタ**（同一画面群の改善）:
   `[[DISCOVER-UTCJST-DATE-MISMATCH-1]]`・`[[DISCOVER-IMPACT-PRED-
   GAPS-1]]`・`[[DISCOVER-PRECISION-GAPS-1]]`・`[[UI-DISCOVER-1]]`

---

## 5B. コード場所ベースのクラスタリング再分析（2026-08-30）

### 5B-1. 再分析の経緯

バッチA（クラスタ1〜3、計11件）を実施した結果、「タイトル・カテゴリの
類似性」で組んだクラスタのうち、実際に単一の根本原因を共有していたのは
**半分未満**だった（クラスタ1の4件は3種の異なる原因・解消経路、
クラスタ2の3件は1件のみが単純パターンに適合、他2件は異なる実装が必要と
判明）。この教訓を受け、Koichiさんの承認のもと、162件全件について
「本文に記載された対象ファイル・関数」を機械的に抽出し、**実際に
同一ファイル・同一関数・同一の共有ロジックパスに触れるか**を基準に
再分析した。

**方法**: 各項目の本文からバックティック引用された`.py`/`.js`ファイル名・
`関数名()`形式の文字列を正規表現で抽出し、2件以上で共有される
ファイル・関数を機械的に洗い出した上で、各候補について実際に「同じ
コード変更で複数項目が同時に解決するか」を個別に本文精読で確認した。
`FIELD_DEFINITIONS.md`等の調査手法ドキュメント・`QUALITY-GATES-EPIC-1`
等の広域参照epicは、「あらゆる項目から参照される」性質上クラスタリング
のノイズになるため対象から除外した。

### 5B-2. 確度：高（同一関数への同一パターンの変更で複数項目が解決する）

**クラスタA: `dcf_validity_checker.py`統合系3件**
`[[ANALYST-VS-IV-INTEGRATE-1]]`・`[[EPS-ANALYZER-INTEGRATE-1]]`・
`[[RICE-INTEGRATE-1]]`。3件とも`common/screening/dcf_validity_checker.py`
に「新規チェック関数を追加し、既存のIV乖離検知パターンを別の指標
（アナリストコンセンサス・EPS Analyzerの乖離・RICE値）に適用する」という
**同一の実装パターン**を提案しており、2026-08-30の診断結論再検証
（ラウンド2）で3件とも実装内容が未着手のまま現存することを確認済み。
1回のセッションで3関数を追加する形で一括対応可能。

**クラスタB: `config/`読み込み失敗検知の横断バッチ（既存1項目内で
既に3ファイル分の同一パターン）**
`[[CONFIG-LOAD-SILENT-FALLBACK-1]]`単体。CHECK-34が確立した
`_CONFIG_LOADER_REGISTRY`テーブル方式（`resolve_*_path()`切り出し＋
レジストリへの1エントリ追記）を、残り3ファイル（`prompts.yaml`・
`maturity_config.json`・`segment_config.json`/`growth_options_
config.json`）に同一パターンで適用するだけで完結する。新規の設計判断
不要、機械的な横展開。

### 5B-3. 確度：中（同一サブシステム・関連する原因だが、個別に検証しつつ
まとめて着手する価値がある）

**クラスタC: `common/macro_data/fetcher.py`のCLI・追跡性改善2件**
`[[MACRODATA-FETCH-FAILURE-VISIBILITY-GAP-1]]`（`fetch_status`
フィールド追加）・`[[MACRODATA-FULL-HISTORY-DAILY-REFETCH-1]]`
（`--start`引数追加）。いずれも同一ファイルの`fetch_series()`/
`fetch_all_series()`/`update_series()`まわりのCLI・ログ機構改善で、
実装が互いに干渉しない独立した追加のため一括実装しやすいが、対象関数が
完全に同一ではないため確度は中。

**クラスタD: TAIL KPIパイプライン小規模改善3件（旧クラスタ4の再評価）**
`[[KPI-UNIT-HARDCODE-USD-1]]`（`xbrl_segment_fetcher.py`のunit固定値
修正）・`[[TAIL-LAYER3-FORMULA-YOY-UNSUPPORTED-1]]`（同ファイルの
`layer3_formula`ミニ構文拡張）・`[[TAILKPI-FIELD-VALIDATION-GAP-1]]`
（`workflow_write.py`への個別フィールド検証追加）。いずれもTAIL KPI
登録・取得パイプラインの独立した小規模改善で、ファイルは一部重複
（前2件は`xbrl_segment_fetcher.py`）するが関数は別。**旧ロードマップの
クラスタ4（TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1・TAIL-XBRL-SEGMENT-
FETCHER-NONDIMENSIONED-GAP-1・TAIL-THESIS-KPIS-EMPTY-ADBE-APGE-1・
TAIL-LAYER3-FORMULA-YOY-UNSUPPORTED-1という4件構成は、再検証の結果
半分は既に別々に進展していたため訂正する**（`[[TAIL-KPI-PROPOSER-
CORE-ONLY-GATE-1]]`のゲート撤廃自体は2026-08-19に実装完了済み、残る
「値取得ブロック」問題は`[[TAIL-XBRL-SEGMENT-FETCHER-NONDIMENSIONED-
GAP-1]]`と同一原因でLayer3振替により実務上ほぼ解消済み。
`[[TAIL-THESIS-KPIS-EMPTY-ADBE-APGE-1]]`は`quarterly_review_
generator.py`の別関数〈`_build_kpi_status_table()`〉が原因で、
この2件とは独立したバグのため別対応が妥当）。

**クラスタE: 登録フロー改善2件**
`[[REGISTER-FLOW-REDESIGN-1]]`・`[[TICKER-AUDIT-1]]`。`TICKER-AUDIT-1`
は`REGISTER-FLOW-REDESIGN-1`が診断した`registration_validator.py`の
P1/P4チェック構造的欠陥と同一の根本原因（登録プロセスの原子性・検証の
強制力不足）に対する具体的な実装候補の一つとして位置づけられる
（`REGISTER-FLOW-REDESIGN-1`本文でも統合先として言及済み）。

### 5B-4. 確度：低（表面的な類似性のみ、個別対応を維持すべき）

以下は同一ファイルまたは同一カテゴリを共有するが、実際の修正内容・
根本原因が異なるため、**無理にクラスタ化せず個別対応候補として残す**:

- **`_resolve_bs_entity_mixing()`周辺の4件**（`[[LAYER3-FETCHER-
  SELECTION-PHILOSOPHY-MISMATCH-1]]`〈確定済み設計判断、対応不要〉・
  `[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]`・
  `[[SPAC-SHELL-MAINTAINED-FIELDS-FREEZE-CONSIDERATION-1]]`〈将来
  検討〉・`[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]`）: 調査時の文脈として
  同じ関数に言及しているだけで、修正対象・修正内容は互いに独立
- **`_extract_values_best_candidate()`周辺の3件**（`[[ANOMALY-
  PATTERN-CATALOG-1]]`〈カタログ文書、実装対象ではない〉・
  `[[PARSER-MERGED-TAG-MIXING-RISK-1]]`〈別関数`_extract_values_
  merged()`の話〉・`[[VRT-REVENUE-2018-MISSING-1]]`〈VRT個別の
  タグ取得失敗〉）: 3件は互いに独立した課題
- **Discover表示4件**（旧クラスタ6のまま維持するが確度は低〜中）:
  `catalyst.py`/`collect.py`/`index.html`と関わるファイルは一部
  重複するが、`[[DISCOVER-UTCJST-DATE-MISMATCH-1]]`（日付処理）・
  `[[DISCOVER-IMPACT-PRED-GAPS-1]]`（表示連携・実行依存関係）・
  `[[DISCOVER-PRECISION-GAPS-1]]`（部分文字列マッチ・鮮度表示）・
  `[[UI-DISCOVER-1]]`（未確定の一般的UI改善）は具体的な修正箇所が
  それぞれ別。「Discover改善セッション」としてまとめて着手する運用上の
  価値はあるが、1コミットで一括解決できる技術的根拠はない
- **FCF-CONVRATEクラスタ3件**（旧クラスタ5）: `[[FCF-CONVRATE-
  DESIGN-LIMIT-1]]`は既に残課題が`[[TRUST-SUMMARY-EPIC-1]]`へ吸収
  済みで実質完了に近い。`[[FCF-CONVRATE-LOWER-DIVERGENCE-1]]`（29
  銘柄への`FCF_CYCLICAL_VOLATILITY_TICKERS`拡張）と`[[AMZN-
  CONVRATE-OVERRIDE-REVIEW-1]]`（AMZN単体の再較正要否検討）は
  `fcf_conversion_config.json`という同一設定ファイルを触るが、
  変更の性質（汎用ルール追加 vs 個別銘柄の数値見直し）が異なるため
  同一PRでの一括対応には向かない
- **report_consistency_check.py共有9件**: 9件全てが同一ファイルを
  参照するが、各WARN/CHECKは独立したロジックのため、ファイル共有
  だけを根拠にクラスタ化する意味は薄い（`[[CONFIG-LOAD-SILENT-
  FALLBACK-1]]`のみクラスタBとして別途高確度扱い）

---

## 6. 運用ルール

- BACKLOG.mdへ新規項目が登録された際は、この168件分の判定結果を起点に、
  新規追加分のみ差分で上記1〜4の棚卸しプロセスを適用する
- フェーズ1（最優先10件）が消化されたら、フェーズ2から次の最優先候補を
  選定し直す運用とする
- このロードマップ自体も、フェーズ1消化時・大きなBACKLOG変動時に更新
  すること
- 全5ラウンドの詳細な検証記録（各項目の陳腐化判定根拠・BACKLOG_DONE.md
  への移設理由等）はチャット履歴側に残るが、このドキュメントはその
  「到達点」のみを恒久記録として要約したものである
- BACKLOG.md項目を🗑️誤診断等でクローズ・BACKLOG_DONE.mdへ移設する際は、
  その項目IDを本文中で参照している他のBACKLOG.md項目がないか確認し、
  ある場合はその参照先項目の記述（前提・依存関係の説明等）が古いままに
  ならないよう更新すること。2026-08-30の棚卸しで、クローズ済み項目を
  依然として未解決の依存先として参照したままの記述が3件見つかった
  （`SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1`・
  `LAYER3-UNEXPLAINED-SINGLE-TICKER-DIFFS-1`・
  `LAYER3-ANNUAL-CLASSIFICATION-DROPS-DATA-1`）ことが本ルール追加の
  契機である
