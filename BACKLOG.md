# On-a-journey — 改善バックログ（全システム）

最終更新: 2026-07-12（同日11回目: HYPECORE-ZS-EPS-STALE-1完了。
実装前提の再確認で、RKLBはhypecore=true（前回セッションでの調査ミスにより
hypecore=falseと誤登録していた）と判明したためRKLB分は対応不要と判断・
訂正。ZSはeps=falseを確認済みのため`docs/value-monitor/adjusted_eps_analyzer/data/ZS/`
のみ削除。実機検証で発見した`hypecore.py::_save_tickers_index()`の既存
NameErrorバグ（`__main__`ブロック内の呼び出しが関数定義より前にあるため
常に失敗）を[[HYPECORE-SAVE-INDEX-NAMEERROR-1]]として新規登録。詳細は
BACKLOG_DONE.md参照）

最終更新: 2026-07-12（同日10回目: FLAG-CONSUMER-AUDIT-3・STALE-REPORT-CLEANUP-1
完了。hypecore.py --batch/単体指定・catalyst.py --ticker・
adjusted_eps_analyzer/pipeline.py --ticker の3箇所で、FLAG-CONSUMER-AUDIT-2と
同型（CLI引数明示指定時のフラグ検証バイパス）の構造的ギャップを発見・修正
（_filter_hypecore_tickers()・_filter_eps_tickers()を新設）。
dcf_validity_checker.pyの同型ギャップは読み取り専用診断ツールのため意図的に
未修正と判断。RKLB・ZS双方のTANUKI VALUATION残存ファイル（report.txt・
latest.json・history.json・history/）を削除（score_history.jsonは過去実績
データとして保持）。副次発見をHYPECORE-ZS-EPS-STALE-1として新規登録。
詳細はBACKLOG_DONE.md参照）

最終更新: 2026-07-12（同日9回目: QUALITY-GATES-EPIC-1 Phase 2b-3完了。
[[SPLIT-AUTO-CHECK-1]]の実害確認調査で根本原因がsplit_history.yaml未登録では
なくEPS Analyzer独自パイプライン`extract_key_facts.py`のfact選定ロジック不整合
（SEC-TAG-FICO-CPRT-1と同型のfact競合パターン）と判明し、選定ロジックを
「filed日最新優先」に統一する根本修正を実施。全105銘柄で新旧比較し11銘柄の
株数系列異常是正を確認。残存する構造的ギャップを[[SPLIT-REALTIME-GAP-1]]、
副次発見のASTS異常変動を[[ASTS-SHARES-OSCILLATION-1]]として新規登録。
詳細はBACKLOG_DONE.md参照）

最終更新: 2026-07-12（同日6回目: FLAG-CONSUMER-AUDIT-2完了。
report_consistency_check.py::run_checks()・stonks-silo/pipeline.py::run()・
score_verifier.pyの残る3消費者に統一アクセサ（tickers.get_tanuki_tickers()/
get_stonks_silo_tickers()）ベースのフラグ検証を適用し、ZS-TICKERS-LEAK-1で
発見した構造的ギャップを解消。横展開未確認事項をFLAG-CONSUMER-AUDIT-3として
新規登録。詳細はBACKLOG_DONE.md参照）

最終更新: 2026-07-12（同日5回目: QUALITY-GATES-EPIC-1のゲート1を
「取得時データ検証（検知のみ）」から「複数ソース自動照合・自動補正」に
設計修正。単一ソース依存の思考停止だったと認識し、検知止まりではなく
自動補正までをスコープに含めるようPhase 2の説明も更新。ゲート2・3は
「検知」ではなく「予防設計」（型による構造的な間違え防止）であることを
明示する注記を追加。詳細は本セクション末尾の「追記（2026-07-12 同日5回目）」参照）

最終更新: 2026-07-12（同日4回目: QUALITY-GATES-EPIC-1のPhase 1
（全テスト実行化・WARN確認済み台帳導入）が完了。CLAUDE_CODE_START.mdのStep 2を
test_pipeline_logic.py単体からtests/全体実行に変更、config/warn_acknowledged.json
新設・report_consistency_check.pyにannotate_warn()/load_warn_ledger()追加。
次はPhase 2（ゲート1: 取得時データ検証）。詳細は本セクション末尾の
「追記（2026-07-12 同日4回目）」参照）

最終更新: 2026-07-12（同日3回目: QUALITY-GATES-EPIC-1（バグ根絶に向けた
5段階品質ゲート導入）を優先度：最高で新規登録し、既存タスク（ARCH-DATA-1・
REGISTER-FLOW-REDESIGN-1・PREFLIGHT-CHECK-1・PREVENT-5・TICKER-AUDIT-1・
LLY-CAPEX-STALE-1等）をゲート0〜4配下の統合マッピングとして整理。
TEST-IV-FORMULA-ALPHA-1とTEST-STALE-IV-1の重複登録を発見しTEST-STALE-IV-1に
統合（優先度は低→中に格上げ）、TEST-IV-FORMULA-ALPHA-1は削除。
詳細は本セクション末尾の「追記（2026-07-12 同日3回目）」参照）

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

追記（2026-07-11 同日5回目）: BX（Blackstone Inc.）の登録抹消（コミット
`8dde36fdc`、cik_lookup.csv 1行＋関連SECデータ73件削除）をBACKLOGに反映。
[[CIK-ORPHAN-FLAGS-1]]のBX該当箇所を解消済みに更新（ENBは未解消のまま残置）、
REGISTER-FLOW-REDESIGN-1の分類記載のBXを取り消し線で解消済み表示に更新、
BACKLOG_DONE.md内のEPS-BX-1に対象消滅の追記、BX完全削除自体を新規
BACKLOG_DONE.mdエントリとして記録。TANUKI-FIN-2（JPM・GS対象）にBXの
記載はなく対応不要と確認済み。

追記（2026-07-11 同日6回目）: GROWTH-FLOOR-VERDICT-1（コミット`8df1f1172`）が
完了したため、エントリ全文（実装着手前調査・実装完了・検証結果を含む）を
BACKLOG.mdからBACKLOG_DONE.mdへ完全移動した。同じ2026-07-10格上げ組の
[[DCF-REL-SYNC-1]]に状況更新（GROWTH-FLOOR-VERDICT-1完了・本タスクは未着手のまま
残置）を追記。

追記（2026-07-11 同日7回目・セッション最終ブラッシュアップ）: [[DCF-REL-SYNC-1]]
実装検討を進め、以下を実施：①Policy Bの`transient_found`/`action`取り違えバグを
発見・分離し[[TANUKI-POLICYB-FIX-1]]として先行修正・完了（コミット`327982770`）、
②`FCFOutlierResult`に`deviation_pct`フィールドを追加しreport.txt表示に反映
（コミット`b5c91180d`。当初追加した200%安全弁は対象母集団0件と判明し削除・
シンプル化）、③調査過程で新規発見した[[FCF-OUTLIER-QUAL-1]]（一過性費用の
説明妥当性の定性評価・優先度未定）・[[SECTOR-FCF-RATE-BROKEN-1]]（FCF実力推定の
sector取得経路破損・優先度中）を新規登録。DCF-REL-SYNC-1本体は
「Policy Bのexcluded分岐の扱い」「Policy A未カバー範囲（ENTG/RMBS等）への対応」
の2点が未決着のまま次回セッション持ち越し。

追記（2026-07-11 同日8回目）: DCF-REL-SYNC-1「Policy A未カバー範囲」の調査を
進め、ENTG/RMBSはEPS Analyzerデータ未生成によるstale状態（再生成のみで解消）と
判明する一方、真に構造的な未カバー範囲（BKNG: BUY・乖離36%未説明、RBRK: 241%
乖離）を新規発見し[[POLICYB-GATE-FIX-1]]として分離・修正・完了（コミット未反映の
場合はBACKLOG_DONE.md参照）。修正過程で「floor_applied>0でもfcf_estimation.applied
=Trueなら実際のDCFはconversion-rate推定値を使う」という別の回帰リスク
（BROS/CEG/SOFI/SPIR型）も発見し同時に修正済み。全銘柄再生成・pytest 131件・
report_consistency_check NG=0を確認済み。横断調査で新たに
[[GROWTH-SANITY-CLASS-SYNC-1]]（growth_sanity.verdictとClassification未連動、
MO/LOAR/XOMのFLOOR_HIT_REVIEW）を優先度：高で新規登録。

追記（2026-07-11 同日9回目）: DCF-REL-SYNC-1の未決着点①（Policy Bの`excluded`分岐の
扱い）を再調査した結果、POLICYB-GATE-FIX-1でPolicy Bの呼び出しゲートが変わったことで
`excluded`分岐が副次的に到達可能になっていたと判明（AMZN/COHRの2銘柄で実際に機能）。
当初確定していた「デッドコードとして簡略化」の方針は撤回し現状維持に訂正した上で、
DCF-REL-SYNC-1本体を**完全クローズ**しBACKLOG.mdからBACKLOG_DONE.mdへ全文移動した
（未決着点①②とも解消済みのため）。移動に伴い、BACKLOG.md内で本エントリを参照していた
他エントリ（GROWTH-SANITY-CLASS-SYNC-1・FCF-OUTLIER-QUAL-1・SECTOR-FCF-RATE-BROKEN-1）
のリンク表記を「[[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）」に更新した。

追記（2026-07-11 同日10回目・セッション最終）: POLICYB-GATE-FIX-1の3コミットを
push（コンフリクトなし）。[[GROWTH-SANITY-CLASS-SYNC-1]]実装前調査中に
`calculate_fcf_cagr()`のCAGR計算式符号反転バグを発見し[[GROWTH-CAGR-SIGN-1]]
として分離・修正・コミット（`b09757ee5`/`41c95bf3d`）。MO/XOMのIV急変動を
一次データで追跡した結果、TTM系列構築時の四半期完全性チェック不足
（全105銘柄中94銘柄でfcf_list_rawへ不完全TTM値が混入）を発見し
[[TTM-QUARTERS-CHECK-1]]として優先度：高で新規登録。GROWTH-CAGR-SIGN-1の
全銘柄再生成は同タスクの対応方針確定まで保留。
完了済み項目は BACKLOG_DONE.md にアーカイブ

追記（2026-07-12）: [[TTM-QUARTERS-CHECK-1]]（案1・quarters_used>=4フィルタ）と
[[GROWTH-CAGR-SIGN-1]]（保留中だった全銘柄再生成）を完了し、両エントリを
BACKLOG_DONE.mdへ移動した。実装過程でCRWV/CONの計算失敗（TTM点数が年次実績
より少ないのに優先され`min_fcf_years`未満でエラー）を自己誘発・同一タスク内で
修正（`_select_fcf_source()`新設）。105銘柄フルバッチ再生成完了（成功100/
失敗0）。Classification変化14銘柄・fcf_outlier.detected変化13銘柄・
growth_sanity.verdict変化5銘柄（詳細はBACKLOG_DONE.md参照）。
[[GROWTH-SANITY-CLASS-SYNC-1]]にMOのfloor_hit再発の状況更新を追記。
副産物として発見した[[LLY-CAPEX-STALE-1]]（LLY CapEx四半期取得バグ）・
[[TEST-IV-FORMULA-ALPHA-1]]（test_iv_formula.pyのALPHA-REDESIGN-1後未更新、
MSFT/NVDA既存2件失敗）を優先度：中で新規登録。

追記（2026-07-12 同日2回目）: [[GROWTH-SANITY-CLASS-SYNC-1]]の設計を再検討し、
「verdictをClassificationに丸めて反映する」単発対応は不採用と判断。
信頼性が崩れうる段階を段階0（データ完全性）・段階1（成長率算出）・
段階2（FCF/DCF計算）の3段階に整理した上で、各段階の「信頼できない」事象を
可視化前に「解消可能（バグ）」と「構造的に解消不能」へ切り分ける方針を
新たに追加し、[[TRUST-SUMMARY-EPIC-1]]として優先度：高で新規登録した
（実装は未着手、次回セッションで設計方針を固めてから着手）。
[[GROWTH-SANITY-CLASS-SYNC-1]]は本EPICの段階1担当として位置づけを更新。

追記（2026-07-12 同日3回目）: セッション振り返り議論で、過去1ヶ月の主要バグが
共通して「発見手段が別作業中の偶然」に依存し機械的ゲートが存在しないことが
根本原因と判明したため、[[QUALITY-GATES-EPIC-1]]（バグ根絶に向けた5段階品質
ゲート：ゲート0登録適格性・ゲート1取得時データ検証・ゲート2正規化契約・
ゲート3計算式検証・ゲート4出力整合＋回帰）を優先度：最高で新規登録した。
[[ARCH-DATA-1]]・[[REGISTER-FLOW-REDESIGN-1]]・[[PREFLIGHT-CHECK-1]]・
[[PREVENT-5]]・[[TICKER-AUDIT-1]]・[[LLY-CAPEX-STALE-1]]等の既存タスクを
ゲート0〜4配下の統合マッピングとして整理し、[[TRUST-SUMMARY-EPIC-1]]は
本EPIC完了後の再評価対象（Phase 5）と位置づけた。

同日中に[[TEST-IV-FORMULA-ALPHA-1]]（本日新規登録）と[[TEST-STALE-IV-1]]
（2026-07-02発見・先行登録済み）が同一バグの重複登録であることが判明したため、
先行するTEST-STALE-IV-1を正式エントリとして残し優先度を低→中に格上げ、
TEST-IV-FORMULA-ALPHA-1は削除した。

追記（2026-07-12 同日4回目）: [[QUALITY-GATES-EPIC-1]]のPhase 1
（即時・低コスト施策）が完了した。CLAUDE_CODE_START.mdのStep 2・
「よく使うコマンド」内pytest実行の2箇所をtest_pipeline_logic.py単体から
tests/全体実行に変更（既知例外[[TEST-STALE-IV-1]]のMSFT/NVDAを明記、
全体実行で新規失敗なしを確認：204 passed/2 known failed）。
report_consistency_check.pyにWARN確認済み台帳機能を追加し、
`config/warn_acknowledged.json`に既知WARN3件（ELF WARN-10、MO/XOM WARN-20）を
事前登録。未登録WARNは`[🆕未確認 WARN-N ...]`と強調表示されるようになった
（既存の非ブロッキング動作は維持）。単体テスト10件追加、全件パス。
次はPhase 2（ゲート1）に進む。

追記（2026-07-12 同日5回目）: セッション振り返りの議論で、[[QUALITY-GATES-EPIC-1]]
ゲート1の設計思想に問題があったことが判明した。「外部データは不確実だから
検知しかできない」という前提は、SEC EDGARという単一ソースへの依存を
無自覚に前提していた思考停止であり、独立した複数ソース（yfinance等）と
機械的に突合すれば、多くのケースは「検知して人間に投げる」のではなく
「取り込む前に自動で弾く・補正する」構造にできると整理し直した。ゲート1を
「取得時データ検証（検知のみ）」から「複数ソース自動照合・自動補正」に
名称・内容とも修正し、タグ取得ミス（KLAC/FICO/CPRT型）・同一値の使い回し
（LLY型CapEx欠損）・株式分割見逃しの3パターンを自動補正対象として明記。
Phase 2の説明も「取得時検証6項目の実装」から「複数ソース自動照合・
自動補正の実装（検知止まりではなく自動補正までをスコープに含める）」に
更新した。

あわせて、ゲート2（正規化契約）・ゲート3（計算式検証）は外部データの
不確実性への対処ではなく自分たちのコード内の規約違反を対象とする
「予防設計」（型による構造的な間違え防止）であり、実行時の検知を行う
ゲート1とは性質が異なることを明示する注記を追加した。

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

### [QUALITY-GATES-EPIC-1] バグ根絶に向けた5段階品質ゲートの導入
**優先度:** 最高
**分類:** アーキテクチャ / 品質管理 / マスタープランEPIC
**登録日:** 2026-07-12
**発見:** セッション振り返り議論（バックログ増加原因の分析）

#### 背景
過去1ヶ月の主要バグ（KLAC/FICO/CPRT/LLY/NOW/TTM系・CAGR符号反転等）を
横断すると、共通して「発見手段が別作業中の偶然」に依存しており、
機械的に検知・ブロックするゲートが存在しないことが根本原因と判明した。
1件の修正が新たな発見を誘発する連鎖（TTM-QUARTERS-CHECK-1で3件誘発、
DCF-REL-SYNC-1で複数件誘発等）もこの構造に起因する。

対症療法（発見された個別バグを都度直す）を続ける限りバグ発見ペースは
落ちないため、データの上流（取得）→中流（正規化）→計算（式の正しさ）→
下流（出力整合）の各段階に機械的なゲートを設け、多くのバグをそもそも
本番に到達させない構造に転換する。

#### ゲート構成
**ゲート0（登録適格性）**: 米国上場・10-K/10-Q提出企業のみを機械判定で
通す。submissions APIで提出フォーム種別（20-F/40-F即NG）・国・上場年数・
収益タグ存在を確認。除外時は`exclusion_reason`をcik_lookup.csvに必須記録し
「フラグfalse＝経緯不明」を根絶する。

**ゲート1（複数ソース自動照合・自動補正）**: 単一ソース（SEC EDGAR）の値を
無条件に正としない。「外部データは不確実だから検知しかできない」という
前提は、SEC EDGARという単一ソースへの依存を無自覚に前提していた思考停止
であり、独立した複数ソースと機械的に突合すれば、多くのケースは「検知して
人間に投げる」のではなく「取り込む前に自動で弾く・補正する」構造にできる：
- **タグ取得ミス（KLAC/FICO/CPRT型）**: yfinance数値・前年/前々年からの
  連続性・同業他社水準と突合し、乖離が閾値超過なら該当タグ値を不採用とし、
  暫定値または前期繰越等の安全な代替に自動フォールバックする
  （人間確認待ちにしない）
- **同一値の使い回し（LLY型CapEx欠損）**: 「同じ値がN期連続」という
  時系列パターン自体を機械検知し、取得失敗とみなして別経路
  （yfinance cashflow等）へ自動フォールバックする
- **株式分割見逃し**: yfinance splits履歴という独立ソースと突合し、
  SEC側の対応漏れがあっても自動補正する
- **主要数値の前年比急変**: 上記の自動照合で説明できない急変のみ、
  従来通り理由確認までブロックする（機械的に解消できないものだけを
  人間の確認対象に絞り込む）
- 決算期末日の同一as-of日整合チェック・10-K/A等訂正データの優先取得・
  四半期充足数チェック（TTM-QUARTERS-CHECK-1の考え方をFCF以外の全系列に
  一般化）は既存方針を維持

**ゲート2（正規化契約）・ゲート3（計算式検証）の位置づけ**: ゲート2・3は
外部データの不確実性への対処ではなく、自分たちのコード内の規約違反
（GROWTH-CAGR-SIGN-1のfcf_list並び順取り違え等）を対象とする「**予防設計**」
である。docstringの規約ではなく型（dataclass等）で構造的に間違えられなく
することが目的であり、実行時の検知ではなくコード自体が誤りを許容しない
設計を指す。ゲート1（実行時の外部データ検証・自動補正）とは性質が異なる。

**ゲート2（正規化契約）**: 全計算ロジックは正規化済みJSONのみを読む。
各フィールドに出所・充足度メタデータを必須付与。規約（fcf_listの並び順等）は
docstringではなく型（dataclass等）でコード化し、構造的に間違えられなくする。

**ゲート3（計算式検証）**: 全計算式に「ゴールデンテスト（教科書的定義との
手計算突合）」と「性質テスト（単調性等の性質検証）」を1式1件以上必須にする。
同一概念の計算が2箇所以上に重複実装される状態自体をNG検知する。

**ゲート4（出力整合＋回帰）**: report_consistency_checkのWARN放置を廃止し
「確認済み」台帳管理に変更（未確認WARNは次回実行でNG化）。CI相当の実行対象を
全テストファイルにする。フルバッチ再生成時のClassification差分レポートを
標準出力にする。

#### 既存タスクの位置づけ（統合マッピング）
以下は個別タスクとして独立進行させず、本EPIC配下のPhase実装時に吸収する：
- ゲート0: [[REGISTER-FLOW-REDESIGN-1]]の対応方針2〜4、[[PREFLIGHT-CHECK-1]]
- ゲート1: [[ARCH-DATA-1]]のaudit.py拡張項目、[[PREVENT-5]]。
  [[LLY-CAPEX-STALE-1]]（完了・BACKLOG_DONE.md参照）はPhase 2aで
  「フォールバック選定ロジックの最新end日優先化」として一般化実装済み
- ゲート2: [[ARCH-DATA-1]]本体（正規化レイヤー強化）
- ゲート3: 新規（計算式ゴールデンテスト整備は現状ほぼ手つかず）
- ゲート4: [[TICKER-AUDIT-1]]のWARN集約構想
- 上記いずれでも解消しない構造的限界の可視化は[[TRUST-SUMMARY-EPIC-1]]に
  引き続き委ねる（本EPIC完了後に再評価）

#### 着手順序（Phase）
1. **Phase 1（即時・低コスト）**: BACKLOG重複統合
   （[[TEST-IV-FORMULA-ALPHA-1]]・[[TEST-STALE-IV-1]]の統合）、
   CLAUDE_CODE_START.md Step 2を全テストファイル実行に変更、
   WARN台帳方式の導入
2. **Phase 2（ゲート1）**: 複数ソース自動照合・自動補正の実装（過去の
   KLAC/FICO/CPRT/LLY型バグを発生前に自動無害化することが目標。検知止まり
   ではなく自動補正までをスコープに含める）。投資対効果最大と判断
   （過去1ヶ月の主要バグの大半がここで止まっていたはず）
3. **Phase 3（ゲート0＋2）**: 登録適格性の機械化・正規化契約の整備
4. **Phase 4（ゲート3）**: 全計算式のゴールデンテスト・性質テスト整備
5. **Phase 5**: [[TRUST-SUMMARY-EPIC-1]]（可視化）を、上記ゲートで拾いきれない
   構造的限界に対象を絞って再評価

**Phase 1完了（2026-07-12）**:
- CLAUDE_CODE_START.mdのStep 2・「よく使うコマンド」内pytest実行の2箇所を
  test_pipeline_logic.py単体からtests/全体実行に変更。既知例外
  （[[TEST-STALE-IV-1]]のMSFT/NVDA）を明記。
- 全テスト実行結果: 204 passed / 2 known failed（新規失敗なし）
- `config/warn_acknowledged.json`を新設し、report_consistency_check.pyに
  `load_warn_ledger()`/`annotate_warn()`を追加。未登録WARNは
  `[🆕未確認 WARN-N ...]`と強調表示、既存の非ブロッキング動作は維持。
  既知3件（ELF WARN-10、MO/XOM WARN-20）を確認済みとして事前登録。
- 単体テスト10件追加（tests/test_report_consistency_check.py）、全件パス
- 検証: pytest 204 passed/2 known failed、report_consistency_check.py NG=0/
  警告3件（確認済み3・未確認0）

次はPhase 2（ゲート1）に進む。

**ゲート1設計修正（2026-07-12 同日5回目）**: 「取得時データ検証（検知のみ）」
から「複数ソース自動照合・自動補正」に設計を修正した。詳細は上記
「ゲート構成」の該当箇所を参照。

**Phase 2a完了（2026-07-12 同日6回目）**: Step 0調査（同日中）で、
LLY型（タグ切替見逃し）とKLAC型（期間分類ミスによるノイズタグ混入）が
「候補タグ群の中で最初に条件を満たしたものを採用して打ち切る」という
同一のフォールバック選定ロジックに起因すると判明したため、選定ロジックを
「最小件数を満たす候補の中から最新end日が最も新しいものを採用する」方式へ
転換した（[[LLY-CAPEX-STALE-1]]（完了・BACKLOG_DONE.md参照）として着手）。
- `common/sec_data/tag_definitions.py`を新設し、quarterly.py（四半期/TTM側）と
  parser.py（年次側）で独立管理されていたタグ候補リストのうち、優先順位・
  候補集合が完全一致または一方が他方の厳密な上位集合になっている9概念
  （CapEx・FinanceLeasePmts・SBC・GrossProfit・NetIncome・Cash・RD・Buyback・OCF）
  を統合。LTDebt・SM・DA・RPO・Revenueは優先順位・候補集合が構造的に異なり
  （既存の修正済みバグ・設計判断と衝突するリスクがあるため）意図的に統合対象外とし、
  [[TAG-DEFS-UNIFY-1]]として別タスクに切り出した。
- `quarterly.py::_select_best_candidate()`・`parser.py::_extract_values_best_candidate()`
  を新設し、候補タグを全て評価した上で最小件数を満たすものの中から最新end日優先で
  採用する方式に変更（parser.py側はuse_max/merge_all_tags使用フィールド
  ＜Revenue・selling_and_marketing・depreciation_and_amortization・SharesBasic/Diluted等＞
  は従来ロジックを完全に維持し、変更対象外とした）。
- 影響範囲確認: 同日生成のcompany_facts.jsonを用いて新旧ロジックを直接比較した結果
  （raw/*.jsonの生成日時差による見かけ上の差分を排除するため、旧コードをgit stash
  で一時退避し同一日に再生成して比較）、105銘柄中**LLY（CapEx: 4件→19件、
  最新end日2022-09-30→2026-03-31）とWMT（SBC: 0件→6件、副次的に発見。WMTは
  ShareBasedCompensationタグを一度も申告せずAllocatedShareBasedCompensationExpense
  のみで申告しており、旧ロジックの厳密な四半期件数改善要求により従来フォールバックが
  発動しなかった）の2銘柄のみ**に影響が限定されることを確認済み。他103銘柄は無変化。
- 検証: `update.py LLY WMT`→`audit.py`（LLY正常、WMT既存の軽微なWARN「OCF一部None」
  のみ・私の変更とは無関係）→`pipeline.py --skip-risk LLY WMT`（2/2成功）→
  `report_consistency_check.py`（NG=0、既存WARN3件のみ・LLY/WMTともにWARN対象外）→
  pytest 214 passed/2 known failed（新規8件追加、既存2件のみ既知失敗）。
- 単体テスト`tests/test_tag_fallback_selection.py`を新規追加（8件、全件パス）。

**Phase 2b-1完了（2026-07-12 同日7回目）**: ゲート1「同一値使い回し」パターンの
一般化として、TTM鮮度チェックを新設した（段差型検知の統合・株式分割自動照合は
別依頼、Phase 2b-2以降）。
- `src/value/tanuki_valuation/data_fetcher.py`に`_quarters_fresh()`・
  `_freshest_end()`を新設。`_quarters_complete()`（quarters_used>=4の件数チェック）
  とは別の姉妹関数とし、既存関数自体は変更していない。
- 閾値根拠: 105銘柄のTTM系列でttm_end(最新)と実行日の差を実測した結果、
  正常銘柄は44〜113日に収まっていた（四半期決算の通常の報告ラグ）ため、
  その3倍弱にあたる270日を閾値に設定（詳細はコード内コメント参照）。
- **実装前の分布確認で重大な設計変更が必要と判明**: TTM系列は各エントリが
  約1年間隔で過去5年分の実データとして保存される設計のため、依頼文通り
  「件数チェックと並列に各エントリごとに鮮度を適用」すると、series[0]
  （最新）以外の全エントリが構造的に365日超で陳腐化扱いされ、全105銘柄で
  `get_fcf_series()`が1点以下（=None、年次フォールバックに全件落ちる）になる
  ことが判明した。ユーザー確認の上、**鮮度チェックはシリーズ中の最新エントリ
  （`_freshest_end()`でソート順に依存せず判定）のみに適用し、最新エントリが
  陳腐化していればシリーズ全体を不採用とする**方式に設計変更した（過去年度の
  正規の履歴エントリは引き続き信頼する）。
- `TanukiDataFetcher.get_financials()`内の3呼び出し元
  （`TTMReader.get_fcf_series()`・`get_periods()`・`build_rice_annual_shape()`）
  すべてに同一の判定を適用。
- 影響範囲確認: 同日生成データで新旧を直接比較した結果、**105銘柄中0銘柄が
  影響**（現時点で全銘柄のfreshest_endが270日以内に収まっているため）。
  データ再生成（update.py/pipeline.py）は不要と判断し実施していない。
  LLY CapEx（Phase 2a修正後）が引き続き正しく採用されることも個別確認済み。
- 検証: `report_consistency_check.py`（NG=0、既存WARN3件のみ）→
  pytest 223 passed/2 known failed（新規5件`tests/test_pipeline_logic.py`に
  追加、既存の`TestTTMReaderQuartersCompleteness`等8件はdate.today()依存の
  陳腐化を防ぐため絶対日付から相対日付ベースに書き換え）。

**Phase 2b-2完了（2026-07-12 同日8回目）**: 段差型の前年比急変検知として、
既存の`common/screening/dcf_validity_checker.py::check_c_data_jump()`
（手動実行専用スクリプト内、Revenue専用・直近6年の隣接年比2.0倍以上/0.5倍以下）を
`report_consistency_check.py`へ統合した（関数自体は改変せず、呼び出し元を
追加するのみ）。株式分割自動照合は引き続き未着手（[[SPLIT-AUTO-CHECK-1]]
（完了・BACKLOG_DONE.md参照）参照）。
- `common/sec_data/report_consistency_check.py`が`common.screening.dcf_validity_checker`を
  importするため、`registration_validator.py`と同一の`sys.path.insert(0, REPO_ROOT)`
  パターンを追加。
- NG-11（孤立年検知：前後両年とも閾値未満のスパイク型）との役割分担を明記:
  新設チェックは前後判定を要さず、ジャンプ後も高い水準が継続する**段差型**
  （FICO/CPRT/LITE型）を検知する。両者は検知パターンが異なるため併存させた。
- **重要度をNGからWARNへ変更（依頼書の想定から判断変更）**: 全105銘柄で試験実行した
  結果、19銘柄（ALAB・ASTS・AVAV・BBAI・CELH・CRWV・IONQ・JOBY・KULR・LITE・NVDA・
  ONDS・QBTS・RCAT・RDW・RKLB・RXRX・S・TDY）が新規該当。うちNVDA（AI GPU需要による
  実際の売上急成長$26.9B→$130.5B）・JOBY（プレコマーシャル航空機企業のほぼゼロからの
  売上立ち上がり）等を一次情報（annual_YYYY.json）で確認した結果、いずれもタグ取得
  ミスではなく実際の事業成長だった。check_c_data_jump()の2.0倍/0.5倍閾値は元々
  「人間が目視で選別する前提のフラグ付けツール」向けの設計でNG（ブロッキング）には
  誤検知率が高すぎると判断し、ユーザー確認の上でWARN-21として実装した。
- 19銘柄全件を一次情報で個別確認し（IPO直後の急成長・AI需要急増・M&A〈TDY=FLIR
  Systems買収・AVAV=BlueHalo買収〉・プレコマーシャル企業の立ち上がり・LITE=既知の
  会計年度末変更、いずれもタグ誤りなし）、`config/warn_acknowledged.json`に
  確認済みとして登録済み。
- 検証: `report_consistency_check.py --fail-on-ng`でNG=0・exit 0（警告38件、
  確認済み38・未確認0）を確認。pytest 226 passed/2 known failed
  （新規`tests/test_report_consistency_check.py`に3件追加）。

**Phase 2b-3完了（2026-07-12 同日9回目）**: [[SPLIT-AUTO-CHECK-1]]の実害確認調査で、
根本原因はsplit_history.yaml未登録ではなく、EPS Analyzer独自の抽出パイプライン
`extract_key_facts.py`のfact選定ロジック不整合（Q1〜Q3は末尾勝ち・Q4は先頭勝ちで
filed日を見ていなかった。SEC-TAG-FICO-CPRT-1と同型のfact競合パターン）と判明。
`extract_key_facts.py`のみを対象にfiled日最新優先へ統一する根本修正を実施し、
split_history.yamlへの個別登録（対症療法）は行わなかった。全105銘柄で新旧比較し、
NVDA・AVGO・TSLA・LRCX・CPRT・CELH・KULR・RCAT・SPIR・WMT・SCCO（新規発見）の
株数系列異常が是正されたことを確認。ただしfact自体が1件も存在しない期間
（分割直後〜翌年10-K再掲まで）は原理的に是正不能な残存ギャップがあり、
[[SPLIT-REALTIME-GAP-1]]として切り出した。詳細はBACKLOG_DONE.md参照。

次はPhase 3（ゲート0＋2: 登録適格性の機械化・正規化契約の整備）。

#### 着手条件
なし。Phase 1・Phase 2a・Phase 2b-1・Phase 2b-2は完了。Phase 2b-3以降は次回セッションで詳細設計を行う。

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
（完了・BACKLOG_DONE.md参照。FICO・CPRTの2020→2021年次売上高の不自然な
ジャンプ、当初はXBRL-TAG-KLAC-1と同型のタグ取得ミス疑いとして検出したが、
実際の根本原因は`_extract_values_merged()`の早い者勝ちマージだった）を検出。
「次にデータ形起因バグが発生した時点で着手する」という本タスクの着手条件に
該当する事例として記録する。

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

### [GROWTH-SANITY-CLASS-SYNC-1] growth_sanity.verdictがDCF_Reliability/Classification判定と未連動
**優先度:** 高
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-11
**発見:** [[POLICYB-GATE-FIX-1]]横断調査時（DCF_Reliability関連ゲートの棚卸し）

#### 問題
`growth_sanity.py`の`check_growth_sanity()`が返す`verdict`（PLAUSIBLE/REVIEW/
AGGRESSIVE/FLOOR_HIT_REVIEW）は、report.txtの`[4] 成長率根拠`セクションに
表示されるのみで、TANUKI SCORE Classification・DCF_Reliability判定には
一切反映されない（pipeline.py内でverdictを参照するのは`GROWTH_PREMIUM`判定用の
`phase1_growth`取得箇所のみで、verdict自体を条件分岐に使う箇所は存在しない）。

2026-07-11時点の実データ確認では、**MO（Classification: BUY）が
`verdict=FLOOR_HIT_REVIEW`・`floor_hit=True`のまま**である（成長率算出ロジックが
破綻し、実績と無関係な機械的floor値15%を採用しているにも関わらず、BUY判定が
変わらない）。LOAR（WATCH）・XOM（HOLD）も同verdictだが、既に低い分類のため
実害は限定的。`report_consistency_check.py`のCHECK-20（WARN-20）でも検知されるが、
WARNは非ブロッキングのため見落とされやすい。

#### [[GROWTH-FLOOR-VERDICT-1]]・[[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）との関係
[[GROWTH-FLOOR-VERDICT-1]]（2026-07-11完了）は、fcf_cagr経路の成長率がfloor値に
機械的に張り付くケース（MO/LOAR/XOM）の**検知**（`verdict=FLOOR_HIT_REVIEW`・
`floor_hit`フィールド新設・CHECK-20）を意図的なスコープとして実装しており、
Classificationへの反映は最初から対象外だった（BACKLOG_DONE.md参照）。

[[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）が当初から問題意識としていた
「信頼できない前提のBUYがスクリーニングを素通りする」という同じ課題の、fcf_outlier系列とは別の
バリエーション（成長率前提の信頼性）にあたる。[[POLICYB-GATE-FIX-1]]で
fcf_outlier系（Policy A/B）側は解消したが、growth_sanity系はまだ未着手。

#### 対応方針（未確定・次回セッションで設計判断）
- Policy A/B同様の「WATCHへの丸め」を追加するか、別Policy（Policy C等）として
  新設するかは未確定
- MO/LOAR/XOMの3銘柄はいずれもfcf_cagr経路のみで発生する既知パターンだが、
  今後segment_weighted等の他経路でも同種の「算出不可・機械的floor採用」が
  起きうるか確認が必要
- Policy A/Bとの優先順位・同時発火時の扱い（floor_hit=Trueとfcf_outlier flaggedが
  同一銘柄で重複する場合の丸めメッセージの一貫性）を設計時に検討する

#### 状況更新（2026-07-11）: [[GROWTH-CAGR-SIGN-1]]によりMO/LOARのfloor_hitが解消
本タスクの発見過程（growth_sanity調査）で、`calculate_fcf_cagr()`のCAGR計算式
自体に符号反転バグがあることが判明し、[[GROWTH-CAGR-SIGN-1]]として分離・修正した
（詳細はBACKLOG.md該当エントリ参照。全銘柄再生成保留中のため未アーカイブ）。
修正の結果、**MO・LOARは`floor_hit=False`
（verdict=PLAUSIBLE）に変わり、本タスクが問題視していた「MO（BUY）がfloor張り付き
のままBUY判定が変わらない」という最も緊急性の高い実例は解消済み**。
`verdict=FLOOR_HIT_REVIEW`のまま残るのはXOM（Classification: HOLD）のみとなり、
既に非BUYのため実害は限定的。

ただし[[GROWTH-CAGR-SIGN-1]]の修正確認時、MOの成長率が15.0%→29.9%に変わったことで
IV乖離率が+34.9%→+286.3%へ大きく変動する事象が判明し、根本原因は
[[TTM-QUARTERS-CHECK-1]]（TTM系列構築時の四半期完全性チェック不足）と
確定した（一過性の事業要因ではない）。この点も踏まえ、**本タスク（growth_sanity.verdictの
Classification連動）は緊急性が下がったため、着手要否を次回セッションで改めて判断する**。

#### 着手条件
なし（[[GROWTH-CAGR-SIGN-1]]対応後の状況を踏まえ、次回セッションで方針確定してから着手）

#### 状況更新（2026-07-12）
[[TTM-QUARTERS-CHECK-1]]・[[GROWTH-CAGR-SIGN-1]]完了に伴い全銘柄再生成した結果、
MOのverdictは再び`FLOOR_HIT_REVIEW`・`floor_hit=True`に戻った
（Classification: BUY）。本タスクが問題視していた「MO（BUY）がfloor張り付きの
ままBUY判定が変わらない」という実例は未解消のまま残っている。ENTG/GEV/HQY
（PLAUSIBLE→REVIEW）、HWM（PLAUSIBLE→AGGRESSIVE）の新規verdict変化も発生しており、
Classification未連動の実害範囲がむしろ拡大した。次回セッションでの着手優先度を
改めて検討する必要がある。

#### 設計再検討（2026-07-12・セッション議論）
本タスクを「growth_sanity.verdictをClassificationに丸めて反映する」という
単発対応として進める方針（Policy A/B型のWATCH丸め）は不採用と判断した。
理由は、Classification自体を丸めても「なぜ信頼できないのか」という情報が
握りつぶされ、数値をそのまま受け取って良いかの判断材料としてはむしろ後退
するため。

代わりに、信頼性が崩れうる段階を洗い出したところ、以下の3段階が直列に
連鎖していることが判明した：
- **段階0（データ完全性）**: TTM系列・年次実績等の入力データ自体が完全か
- **段階1（成長率算出）**: `growth_sanity.verdict`。report.txtのみに表示
- **段階2（FCF/DCF計算）**: `fcf_outlier.detected`。Policy A/B経由で
  Classificationに反映済み

さらに議論の中で重要な軸が1つ抜けていたことが判明した：「信頼できない」と
判定された事象には、**構造的に解消不能なもの**（可視化するしかないもの）と、
**取得・算出ロジックの不備で本来解消可能なもの＝バグ**が混在しており、
これを区別せずに一律で可視化対象にすると、直せるはずのバグが「これは
限界です」という顔をして放置され続けるリスクがある（実例：
[[LLY-CAPEX-STALE-1]]（完了・BACKLOG_DONE.md参照）は「データが存在しないから
信頼度を下げて表示する」話ではなく、本来取得できるはずのCapEx四半期データが
取得ロジックの不備で取れていない、解消可能な事例だった。実際にPhase 2aで
根本原因（タグ切替の見逃し）を解消済み）。

方針は「Classificationを書き換える」のではなく「**各数値がそのまま信じて
良い状態か、信じてはいけない状態かを一目で分かるようにする**」ことが目的だが、
可視化に着手する前に、まず個々の「信頼できない」事象が解消可能（バグ）か
構造的限界かを切り分ける工程を挟む。詳細は[[TRUST-SUMMARY-EPIC-1]]参照。

---

### [TRUST-SUMMARY-EPIC-1] データ信頼性の3段階（入力完全性・成長率算出・FCF/DCF計算）を貫通する可視化EPIC
**優先度:** 高（要設計、実装未着手）
**分類:** アーキテクチャ / 検証基盤 / EPIC候補
**登録日:** 2026-07-12
**発見:** [[GROWTH-SANITY-CLASS-SYNC-1]]設計議論時

#### 背景
各銘柄の数値（特に成長率・FCF・IV）が「そのまま信じて良い状態か」を
判断する材料が、信頼性が崩れうる段階ごとにバラバラに存在し、統一された
見え方をしていない。整理すると信頼性は以下の3段階で直列に連鎖する：

- **段階0（データ完全性）**: TTM系列・年次実績等の入力データ自体が完全か。
  恒常的な可視化指標が現状ない。[[TTM-QUARTERS-CHECK-1]]（完了・
  BACKLOG_DONE.md参照）で個別事象には対応したが、今後同種の欠損が
  別の形で起きても検知する仕組みがない。
- **段階1（成長率算出）**: `growth_sanity.verdict`
  （PLAUSIBLE/REVIEW/AGGRESSIVE/FLOOR_HIT_REVIEW）。report.txtのみに表示。
- **段階2（FCF/DCF計算）**: `fcf_outlier.detected`・Policy A/B。
  唯一Classificationまで反映されているが「丸め」の形で理由が失われる。

#### 方針の骨子①：可視化の前にバグ切り分けを行う（2026-07-12議論で追加）
「信頼できない」と判定された事象は、可視化する前に**まず取得・算出
ロジックの不備で解消可能かを個別に切り分ける**。切り分けの結果：
- **解消可能（バグ）**なものは、可視化の対象にせず個別のバグ修正タスクとして
  即時扱う（例: [[LLY-CAPEX-STALE-1]]（完了・BACKLOG_DONE.md参照）のような
  データ取得ロジックの不備）
- **構造的に解消不能**なもの（例: SECデータが特定期間存在しない、
  企業側が開示していない等）のみ、可視化の対象とする

可視化は「直せない残り」に対する最終手段であり、直せるものを直さず
見せるだけで済ませてはならない。段階0〜2それぞれで、既存の「信頼できない」
事象一覧を棚卸しし、この切り分けを行うことが本EPIC着手時の最初のステップとなる。

#### 方針の骨子②：残った構造的限界の可視化
バグ切り分け後もなお構造的に解消不能な事象について、
Classification（BUY/WATCH等の分類）自体は書き換えず、**分類とは独立に
「この銘柄のこの数値は段階0〜2のどこで、どの理由で信頼性が損なわれて
いるか」を並記する**方向で設計する。分類を信用するかどうかは
Koichiさんの判断に委ね、判断材料としての透明性を上げることを目的とする。

#### 関連タスク（本EPICに整理・統合される可能性がある既存項目）
- [[GROWTH-SANITY-CLASS-SYNC-1]]（段階1）: 状況追記済み
- [[SECTOR-FCF-RATE-BROKEN-1]]（段階2寄り）: sector取得経路破損。これ自体が
  「解消可能な不備」の実例（バグ①②③として既に構造分析済み）
- [[ARCH-DATA-1]]（段階0寄り）: SECデータ正規化レイヤーの強化。着手条件
  成立済みだが難易度高
- [[LLY-CAPEX-STALE-1]]（段階0・完了・BACKLOG_DONE.md参照）: 解消可能な
  バグの実例として先行登録され、Phase 2aで根本原因を解消済み

#### 対応方針（未確定・次回セッションで設計）
1. 段階0〜2それぞれの既存「信頼できない」事象を棚卸しし、
   解消可能（バグ）か構造的限界かを個別に判定する
2. 解消可能と判定したものは個別バグ修正タスクとして分離・BACKLOG登録する
3. 構造的限界と判定したものについて、フィールド構成・表示箇所
   （report.txt拡張／Classification一覧への列追加／別画面新設）を設計する
4. 段階0の恒常的な可視化指標（quarters_used完全性チェックの一般化等）を検討する
5. 実装規模の見積もり（既存タスクを統合するか、独立EPICとして段階的に
   着手するか）

#### 着手条件
なし（次回セッションで設計方針を固めてから着手判断）

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

### [FCF-OUTLIER-QUAL-1] 一過性費用の説明妥当性に関する定性評価の導入
**優先度:** 未定（要判断）
**分類:** データ品質 / TANUKI VALUATION / AI活用
**登録日:** 2026-07-11
**発見:** [[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）実装検討時

#### 背景
`fcf_outlier.action`（`excluded`/`flagged`）は、一過性費用の金額が
FCF乖離の一定割合（20%等）を占めるかという**金額比率のみ**で機械的に
判定されており、その一過性費用の内容自体が乖離を実質的に説明しているか
（例: 事業の一時的な問題か、構造的な問題の兆候か）は評価されていない。
`transient_evidence.items`には一過性費用の個別項目（内容の記述含む）が
既に格納されているため、これをAI（`quarterly_review_generator.py`等の
既存の定性評価の仕組みを参考に）に評価させ、action判定に反映する、
または別フィールドとして表示する設計が考えられる。

#### 対応方針（未確定・検討課題）
- 案A: action判定自体にAI定性評価を組み込む（判定ロジックの複雑化に注意）
- 案B: 定性評価は別フィールド（例: `transient_evidence.ai_assessment`）として
  追加し、report.txtに参考情報として表示するのみでaction判定は変えない
  （既存の機械的判定はそのまま維持し、人間の最終判断材料を増やす方向）
- 案Bの方がリスクが低く、[[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）のスコープとも独立して着手しやすい

#### 着手条件
なし（設計判断が必要なため、次回セッションで方針確定してから着手）

---

## 優先度：中（こなれてきたら対応）

### [SECTOR-FCF-RATE-BROKEN-1] FCF実力推定のsector取得経路破損によるセクター別転換率の無効化
**優先度:** 中（要判断・緊急ではないが影響範囲は広い）
**分類:** バグ / TANUKI VALUATION / データ品質
**登録日:** 2026-07-11
**発見:** [[DCF-REL-SYNC-1]]（完了・BACKLOG_DONE.md参照）関連調査時

#### 背景
`adjustments.py`（`estimate_fcf_from_eps`内）のFCF転換率セクター別レート判定・
Financial Services向け`ni_direct`判定が、以下3つの重なったバグにより
実質的に無効化されている：

- **バグ①**: `core_calculator.py:227-233`の`beta_config.json`読み込みパスが誤り
  （存在しない`src/value/beta_config.json`を参照、実際は`config/beta_config.json`）
- **バグ②**: 仮にパスを直しても`config/beta_config.json`の`overrides`に`sector`キーが
  ほぼ存在しない（全106エントリ中1件のみ、スキーマ移行の残骸）
- **バグ③**: `fcf_conversion_config.json`の`sector_conversion_rates`はDamodaran業種
  カテゴリをキーとするが、`beta_config.json`側はGICS分類であり、
  パス・入力を直してもタクソノミーが一致しない

#### 影響範囲
Policy B対象76銘柄中71銘柄（93%）が業種を問わず一律`conversion_rate=0.70`
（default値）で計算されている。yfinance実測`sector`が"Financial Services"の
SOFI/V/MSCIは、本来`use_ni_direct`（転換率1.0）が適用される設計意図と推測されるが
未適用（試算では該当銘柄のFCFが1.43倍程度過小評価されている可能性）。
ただしV・MSCIは[[TANUKI-FIN-2]]の議論で「通常のFCFF DCFが適合する」と既に整理
されており、機械的に1.0倍を適用することが正しいとは限らない点に注意。
WACC・alpha上限・RPO適用率・保険業判定等、他のsector依存ロジックは
別の正常な変数（`financials.get("sector")`）を使っており本問題の影響を受けない。

#### 対応方針（未確定・着手時に設計判断）
- 案①（部分対応・低コスト）: `core_calculator.py:244`のsector変数を、
  既に正しく取得されている変数に差し替える。バグ①②は解消するが、
  バグ③（タクソノミー不一致）は残るため効果は限定的
  （Financial Services判定のみ改善見込み、他業種別レート差別化は未解決）
- 案②（本格対応）: `growth_sanity.py`の`damodaran_industry`判定ロジックを
  `estimate_fcf_from_eps()`からも参照するよう設計変更する。バグ③まで解消するが
  作業規模が大きい
- Financial Services業種の対象範囲判定（V/MSCI等、GICS分類は該当するが
  `ni_direct`適用が不適切な可能性がある銘柄の扱い）は案①②のいずれでも
  別途設計判断が必要

#### 着手条件
なし（優先度含め次回以降のセッションで判断）

---

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

### [TAG-DEFS-UNIFY-1] quarterly.py/parser.pyのタグ候補リスト未統合フィールドの整理
**優先度:** 中
**分類:** アーキテクチャ / SECデータ取得層
**登録日:** 2026-07-12
**発見:** [[LLY-CAPEX-STALE-1]]（完了・BACKLOG_DONE.md参照）Phase 2a実装時

#### 背景
Phase 2aで`common/sec_data/tag_definitions.py`を新設し、quarterly.py（四半期/TTM側）と
parser.py（年次側）で独立管理されていたタグ候補リストのうち、優先順位・候補集合が
完全一致または一方が他方の厳密な上位集合になっている9概念（CapEx・FinanceLeasePmts・
SBC・GrossProfit・NetIncome・Cash・RD・Buyback・OCF）を統合した。

一方、以下5フィールドは優先順位・候補集合が構造的に異なり、無条件でのマージは
既存の修正済みバグ・設計判断を壊すリスクがあるため意図的に統合対象外とした：

- **LTDebt/long_term_debt**: 優先タグの順序がquarterly.pyとparser.pyで逆
  （parser.pyはBUG-NETDEBT-2対策でLongTermDebtNoncurrentを意図的に最優先。
  quarterly.pyはLongTermDebtが優先）
- **SM/selling_and_marketing**: quarterly.pyはSGA全体（SellingGeneralAndAdministrativeExpense等）
  への最終フォールバックを持つが、parser.pyはSGAを`sga_gap_warning`専用に意図的に分離している
- **DA/depreciation_and_amortization**: primaryタグの優先順序が逆
  （quarterly.pyはDepreciationDepletionAndAmortization優先・単一タグのみ、
  parser.pyはDepreciationAndAmortization優先・4タグ＋merge_all_tags=True）で
  挙動が根本的に異なる
- **RPO/rpo**: quarterly.pyはContractWithCustomerLiabilityNoncurrent/
  DeferredRevenueNoncurrent（noncurrent限定）、parser.pyはContractWithCustomerLiability/
  DeferredRevenue（current/noncurrent区分なし）と、単純な合算が概念的に不正確になりうる
- **Revenue/revenue**: ティッカー別revenue_conceptオーバーライド（SOFI/IONQ等）と
  merge_all_tagsの相互作用が複雑。parser.py側に quarterly.py の`_REVENUE_FALLBACKS`
  にない候補タグ`RevenueFromContractWithCustomer`（Excluding/IncludingAssessedTax
  接尾辞なし）が1件存在することを確認済み（低リスクな拡張余地だが未着手）

#### 対応方針
各フィールドごとに、優先順位・候補集合の相違が意図的な設計判断か歴史的な放置かを
個別に精査した上で、統合可否・統合する場合の優先順位を判断する。LTDebt・SMは
既存の修正済みバグ（BUG-NETDEBT-2・SGA/SM分離）の経緯を熟読してから着手すること。

#### 状況更新（2026-07-12・SEC-TAG-FICO-CPRT-1実装依頼前の網羅調査時）
Revenueで発見された「同一end_dateに複数タグが競合した際の早い者勝ち」バグ
（[[SEC-TAG-FICO-CPRT-1]]、完了・BACKLOG_DONE.md参照）を踏まえ、LTDebt・RPOに
同型の問題が潜んでいないかcompany_facts.jsonベースで機械調査した。

結論: **LTDebt・RPOは構造的にこの種のバグの対象外**と確認した。revenue/SM/DAは
「期間（duration）」を持つフロー概念のため、91日間の四半期データが365日間の
年次データを装って混入しうるが、LTDebt・RPOはいずれも貸借対照表の**時点データ
（point-in-time）**であり、そもそも「期間の長さ」という混入経路が存在しない。
実際に検出された多数の「衝突」（LTDebt 20件・RPO 132件）は全て、意図的に
スコープが異なる別概念の比較だった（例: LTDebtの`LongTermDebtNoncurrent`
（非流動部分のみ）vs `LongTermDebt`（流動+非流動合計）は、まさにBUG-NETDEBT-2
で意図的に設計された優先順位そのもの）。

**LTDebt・RPOについては本タスクのスコープから除外し、対応不要としてクローズする
方向が妥当と考えられるが、最終判断は次回セッションで行う（今回は判断・変更しない）。**
残るSM・DAは、SEC-TAG-FICO-CPRT-1実装時に同様の機械調査を行い、実害0件
（同一end_date競合による誤混入は1件も確認されず）と確認済み。revenue自体は
SEC-TAG-FICO-CPRT-1で対応完了（`_extract_values_merged()`にduration優先の
tie-break追加。SM/DAにも同一ロジックが適用され、今回の調査で回帰なしを確認済み）。
残る論点は「Revenue/revenueのティッカー別オーバーライドとmerge_all_tagsの相互作用」
のみとなり、範囲は当初の5フィールドから大幅に縮小している。

#### 着手条件
なし（LTDebt・RPOのクローズ判断とrevenueの残論点の扱いは次回以降のセッションで判断）

---

### [SPLIT-REALTIME-GAP-1] 分割直後〜翌年10-K再掲までの期間はfact競合ロジックでも是正できない
**優先度:** 低〜中
**分類:** データ品質 / EPS ANALYZER
**登録日:** 2026-07-12
**発見:** [[SPLIT-AUTO-CHECK-1]]（完了・BACKLOG_DONE.md参照）実装検証時

#### 問題
SPLIT-AUTO-CHECK-1で`extract_key_facts.py`のfact選定ロジックを「filed日が
最新のfactを優先」に統一し、同一期間に複数factが競合するケース（分割による
比較年度再掲）は是正できるようになったが、**そもそも競合factが1件も存在しない
期間は原理的に是正できない**。

具体例（NVDA 2023-04-30、FY2024 Q1）: SEC company facts APIには当該四半期の
`WeightedAverageNumberOfDilutedSharesOutstanding`が2件しかなく、いずれも
分割前株数（2,490,000,000）。2件目は翌年同時期の10-Q（2024-05-29提出）が
比較年度として再掲したものだが、この提出日は実際の分割効力発生日
（2024-06-07）より**前**のため、再掲値も分割前のまま。10-Qは前年同四半期のみを
比較掲載するため、この四半期はその後二度と別の提出書類で再掲される機会がなく、
恒久的に分割前株数が残存する。annual.json側もこの1四半期分だけ歪んだ値を
引きずるため、FY2024通期のdiluted_shares_used平均値も完全には是正されない。

RCAT（2023年に複数回の変動: 2023-04-30↓、2023-07-31↑、2024-03-31↓）も
同種の構造的ギャップか、別要因（実際の自己株買い等）かが未切り分けのまま
残っている。

#### 対応方針（未確定・次回セッションで判断）
- yfinance `Ticker.splits`を独立ソースとして参照し、この「re-統計上の空白期間」
  に該当する四半期のみ機械的に按分補正する設計を検討する（SPLIT-AUTO-CHECK-1の
  当初案だった「yfinance splits自動照合」を、全銘柄一律ではなくこのギャップ
  埋め用途に限定して採用するか判断）
- あるいは`split_history.yaml`への個別登録＋既存`apply_split_adjustments()`の
  併用に戻すか（対症療法だが実装コストは低い）
- RCATの2023年変動が本ギャップと同種か別要因かを一次情報（10-Q本文）で確認する

#### 着手条件
なし（次回セッションで判断）

---

### [ASTS-SHARES-OSCILLATION-1] ASTSのdiluted_shares_usedが四半期ごとに大きく往復変動
**優先度:** 低
**分類:** データ品質 / EPS ANALYZER
**登録日:** 2026-07-12
**発見:** [[SPLIT-AUTO-CHECK-1]]実装後の全105銘柄横断ジャンプスキャン時

#### 問題
ASTS（AST SpaceMobile）の`quarterly.json`で、四半期ごとにdiluted_shares_used
が約29.9万株↔約5.2万株の間を複数回往復する異常パターンを検出した
（2021-09-30・2022-03-31・2022-06-30・2023-03-31・2023-12-31・2024-03-31・
2024-06-30で往復）。単一方向のstep変化（真の株式分割・大型増資）ではなく
往復パターンのため、[[SPLIT-AUTO-CHECK-1]]で対応した株式分割由来のfact競合とは
別種の問題（ワラント・種類株式の希薄化算入条件の四半期ごとの揺れ、またはSEC
fact競合の分割以外のバリエーション）の可能性がある。今回はSPLIT-AUTO-CHECK-1の
スコープ外のため未調査。

#### 対応方針
一次情報（10-Q本文の希薄化後株式数の算定根拠）で原因を切り分けてから対応要否を
判断する。

#### 着手条件
なし（次回セッションで調査要否を判断）

---

### [DATA-JUMP-CHECK-GENERALIZE-1] Revenue以外のフィールドへの段差型検知の展開要否
**優先度:** 未定
**分類:** アーキテクチャ / 品質管理
**登録日:** 2026-07-12
**発見:** QUALITY-GATES-EPIC-1 Phase 2b-2（WARN-21 Revenue段差型急変統合）実装時

#### 背景
Phase 2b-2で`check_c_data_jump()`をreport_consistency_check.pyへ統合したが、
このスコープはRevenueのみに限定した（`check_c_data_jump()`は現状Revenue専用の
ハードコードであり、対象フィールドをパス引数化する改修が必要なため、実質的な
新規設計として意図的に対象外とした）。

CapEx・NetIncome・GrossProfit・SBC等の他の主要フィールドについても、
段差型の前年比急変（タグ切替・タグ取得ミスによる不連続）が理論上起こりうるが
（LLYのCapExはTTM-QUARTERS-CHECK-1の副産物として偶然発見されたに過ぎない）、
現状これらのフィールドを対象にした前年比急変チェックは存在しない。

#### 対応方針（未確定・次回セッション以降で判断）
- `check_c_data_jump()`をフィールドパス引数化する改修（例:
  `check_c_data_jump(repo_root, ticker, section="pl", field="revenue", ...)`）の
  設計要否を判断する
- Revenue以外のフィールドに展開する場合、Phase 2b-2で判明した「2.0倍/0.5倍という
  閾値はNG（ブロッキング）には誤検知率が高すぎる」教訓を踏まえ、フィールドごとに
  適切な閾値・重要度（NG/WARN）を再検討する必要がある（成長率の高いフィールドほど
  正当な急変が起きやすいため、一律の閾値では機能しない可能性がある）
- 展開する場合の対象フィールド候補: CapEx・NetIncome・GrossProfit・SBC等
  （TAG-DEFS-UNIFY-1で統合済みの9概念、LTDebt・RPOは時点データのため対象外
  ＜TAG-DEFS-UNIFY-1参照＞）

#### 着手条件
なし（優先度含め次回以降のセッションで判断）

---

### [FLAG-THRESHOLD-DESIGN-1] tanuki/stonks_silo等4フラグの判定基準ロジック導入（第二段階）
**優先度:** 未定
**分類:** アーキテクチャ / 銘柄登録フロー
**登録日:** 2026-07-12
**発見:** [[ZS-TICKERS-LEAK-1]]（完了・本ファイル上部参照）の消費者統一（第一段階）に伴う調査時

#### 背景
一連の調査（フラグ判定ロジック確認・基準設計材料収集）の結果、`cik_lookup.csv`の
4フラグ（tanuki/stonks_silo/eps/hypecore）は**完全手動設定**であり、財務指標等に
基づく自動判定は一切存在しないことが確認された。暗黙の基準（赤字→stonks_silo=true）は
概ね成立するが、以下の逸脱事例が判明している：

- **ESTC・LITE**: 黒字転換後もstonks_silo=trueのまま残留（直近1年基準では不一致）
- **GTLB**: 直近5年間**一度も黒字化していない**にもかかわらずstonks_silo=false
  （既知8件の逸脱事例には含まれていなかった新規発見。明示的な除外理由の記録もなし）
- **APGE**: 売上ゼロのプレレベニュー企業。「赤字」という1軸だけでは判定基準として
  不十分であることを示す事例（「売上の有無」も判定軸に含める必要）

#### 対応方針（未確定・基準案をKoichiさんに複数提示して確認後に実装）
- 直近5年中N年以上赤字継続→stonks_silo=true、といった機械判定可能な基準の導入
  （Nの値・判定ウィンドウは要確認）
- プレレベニュー企業・金融機関・IFRS企業・特殊株式構造企業等、「赤字」以外の
  軸での評価枠組み非適合パターンの明文化
- GTLB・ESTC・LITEの現行フラグ設定の是正（基準確定後に個別対応）
- フラグ再判定のトリガー（新規登録時のみか、定期棚卸しか）の設計
- tanuki=trueとstonks_silo=trueの併用は意図的な設計（SYSTEM_MAP.mdに明記の
  TANUKI VALUATION↔STONKS SILO runway参照依存）であり、「赤字企業は両方trueに
  する」という運用を基準に組み込む余地がある

#### 着手条件
なし（基準案の確認・確定後に着手）

---

### [HYPECORE-SAVE-INDEX-NAMEERROR-1] hypecore.pyの_save_tickers_index()がNameErrorで未実行
**優先度:** 中
**分類:** バグ / HypeCore
**登録日:** 2026-07-12
**発見:** [[HYPECORE-ZS-EPS-STALE-1]]（完了・BACKLOG_DONE.md参照）実装時の実機検証

#### 問題
`src/value/hypecore/hypecore.py`を直接実行すると、`if __name__ == "__main__":`
ブロック内（1009行目）で`_save_tickers_index(_DOCS_DIR)`を呼び出しているが、
その関数定義自体（1012行目）はブロックより**後**にファイル上で配置されている。
Pythonはモジュール読み込み時に上から順に実行するため、呼び出し時点では
`_save_tickers_index`が未定義で`NameError`が発生し、poc.json保存後の
tickers.jsonインデックス再生成が常に失敗している（コミット5f754eda4時点
から存在する既存バグ、FLAG-CONSUMER-AUDIT-3の変更とは無関係）。

実害: HypeCore実行のたびに"完了"ログの直後でクラッシュし、
`docs/value-monitor/hypecore/data/tickers.json`が最新のpoc.json構成を
反映しないまま放置される（新規銘柄登録時の一覧表示漏れ等につながりうる）。

#### 対応方針
`_save_tickers_index`の関数定義を`if __name__ == "__main__":`ブロックより
前に移動する（1行の並び替えで解消可能）。

#### 着手条件
なし（次回セッションで着手可能・低リスク）

---

### [WARN12-COHR-ONDS-1] SEC自動更新後にCOHR・ONDSでCash-STI期ズレの新規WARN検出
**優先度:** 低
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-12
**発見:** [[HYPECORE-ZS-EPS-STALE-1]]完了検証時（`report_consistency_check.py`実行）

#### 問題
GitHub Actionsの自動SEC更新（コミット`b6abc0a2a`）後、COHR
（Cash=1593M(2026Q3) vs ST_Invest=0M(年次2025)、正=825M）・ONDS
（Cash=1026M(2026Q1) vs ST_Invest=0M(年次2025)、正=448M）で
`WARN-12 Cash-STI期ズレ`が新規発生（未確認扱い）。今回のタスクとは無関係の
発見のため未対応。

#### 対応方針
一次情報（10-Q）でCash・ST_Investの正しい組み合わせを確認し、
`config/warn_acknowledged.json`への登録要否を判断する。

#### 着手条件
なし（次回セッションで判断）

---

### [CIK-ORPHAN-FLAGS-1] BX・ENBが全システムフラグfalseの孤立エントリ
**優先度:** 低〜中（BX分は解消済み・残るはENBのみ）
**分類:** データ品質 / 銘柄登録
**登録日:** 2026-07-10
**発見:** サテライト投資候補91銘柄への前提妥当性チェック自己点検時
**進捗（2026-07-11追記）:** BXは2026-07-11 コミット`8dde36fdc`でcik_lookup.csv行・
関連SECデータを完全削除し、登録抹消（下記A案）により解消済み。
以下の問題・対応方針の記載はBXについては過去の記録として残すが、
現状はENBのみが未解消。

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

**BXについてはKoichiさんの判断によりA案（登録抹消）を採用（2026-07-11・
コミット`8dde36fdc`）。** ENBについては上記の通り現状維持中で、B案の検討は
TANUKI-FIN-1着手時に持ち越し。

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

**同日中にBX自体が登録抹消されたため対象消滅（コミット`8dde36fdc`）。**
削除後にregistration_validator.pyを再実行し、BX関連のNG/WARNが0件に
なったことを確認済み（対象銘柄数106→105）。

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
  臨床段階バイオ、SEC取得自体は正常）・~~BX（資産運用会社でPL項目が薄い）~~
  2026-07-11 登録抹消（コミット`8dde36fdc`）により解消・SN（20-F提出企業で
  四半期系列不足、[[SN-TANUKI-DELAY-1]]参照）。
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
**優先度:** 中（2026-07-12・低から格上げ）
**分類:** テスト保守 / 品質管理
**発見:** 2026-07-02（ARCH-DATA-1-YTDスポットチェック時）。
2026-07-12: [[TTM-QUARTERS-CHECK-1]]Step4実施時にも独立発見
（[[TEST-IV-FORMULA-ALPHA-1]]として重複登録されていたが本エントリに統合）

#### 問題
tests/test_iv_formula.pyがALPHA-REDESIGN-1（2026-06-25完了）以前の旧計算式
（iv_pt = v0_rm × (1+alpha) + rpo_pv + go_pv）をハードコードしたまま。
現行core_calculator.pyはalpha=0.0固定（alpha廃止済み）だが、latest.jsonには
旧フィールドalphaが残存しているため、テストの再計算値と保存値が乖離し
NVDA/MSFTで恒常的にpytest失敗する（機能的な実害はなし、テストコードのみ陳腐化）。

#### 影響
`CLAUDE_CODE_START.md`のStep 2はtest_pipeline_logic.pyのみ実行する運用のため、
この回帰は登録（2026-07-02発見）から2026-07-12の再発見まで約2週間見逃されて
いた。優先度格上げはこの見逃し期間の長さを踏まえた判断。

#### 対応方針
test_iv_formula.pyの期待値算出ロジック自体の修正が本タスクの残作業。
CLAUDE_CODE_START.mdのStep 2実行対象への追加は[[QUALITY-GATES-EPIC-1]]
Phase 1（2026-07-12完了）でtests/全体実行への変更により対応済み
（同種見逃しの再発防止は解消、本エントリの残スコープは計算式修正のみ）。

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
