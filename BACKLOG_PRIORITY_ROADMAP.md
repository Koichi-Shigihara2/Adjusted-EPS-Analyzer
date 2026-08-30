# BACKLOG優先度ロードマップ

**作成日:** 2026-08-30
**作成経緯:** 2026-08-29〜30の全5ラウンドで、BACKLOG.md未完了項目181件
全件の「陳腐化・ニーズ・課題認識の合理性」を検証（9件をBACKLOG_DONE.md
へ移設、4件を⚠️課題認識に疑義ありとして報告のみに留めた）。残る168件を
「開発合理性による分類＋重要性判断＋着手手順」まで踏み込んで整理した。
Koichiさんの指示「このレベルまでやって棚卸である」を受け、この方法論と
実施計画をリポジトリに恒久記録として残す。

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

1. `[[FCF-CAGR-YEARS-MISMATCH-1]]` — stock.html CAGR(3yr)誤表示
2. `[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]` — VRT/CRM
   のROE実害
3. ✅**完了**（2026-08-30、バッチA cluster 2）~~`[[CASH-TAG-MISSING-1]]`~~
   — 複数銘柄でcash_and_equivalents欠落（BACKLOG_DONE.md参照）
4. `[[EPS-DISCREPANCY-FLAG-OVERLOAD-1]]` — フラグ名の意味重複
5. `[[RICE-ADJ-ASYMMETRIC-ZERO-1]]` — 非対称0フロア設計
6. `[[HYPECORE-REALSTRONG-DUAL-IMPL-1]]` — Python/JS二重実装の矛盾
   リスク
7. ✅**完了**（2026-08-30、バッチA cluster 1）
   ~~`[[QUARTERLY-CLASSIFY-PERIOD-NO-UPPER-BOUND-1]]`~~ — is_annual判定に
   上限なし（BACKLOG_DONE.md参照）
8. ✅**完了**（2026-08-30、バッチA cluster 3）~~`[[V0-V0RM-CONFUSION-RISK-1]]`~~
   — v0/v0_rm取り違えリスク（BACKLOG_DONE.md参照）
9. `[[TVGROWTH-EXPLICIT-DEFAULT-AMBIGUOUS-1]]` — terminal_growth明示/
   未設定の区別不能
10. ✅**完了**（2026-08-30、バッチA cluster 1）
    ~~`[[LAYER3-ANNUAL-MISCLASSIFICATION-NOW-RMBS-1]]`~~ — 実証済み修正
    パターンの横展開（BACKLOG_DONE.md参照）

上記10件中4件がバッチA（2026-08-30）で完了。残る6件
（FCF-CAGR-YEARS-MISMATCH-1・PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-
MISSELECT-1・EPS-DISCREPANCY-FLAG-OVERLOAD-1・RICE-ADJ-ASYMMETRIC-ZERO-1・
HYPECORE-REALSTRONG-DUAL-IMPL-1・TVGROWTH-EXPLICIT-DEFAULT-AMBIGUOUS-1）
は将来の「バッチB」着手候補として据え置き。

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
