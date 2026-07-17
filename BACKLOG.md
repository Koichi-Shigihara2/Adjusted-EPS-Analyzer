# On-a-journey — 改善バックログ（全システム）

最終更新: 2026-07-13（同日2回目: セッション終了時ブラッシュアップ。
Phase 3a完了後に追加で完了した4件——TICKER-DIRECT-ACCESS-GUARD-1
（FLAG-CONSUMER-AUDIT-2/3再発防止CIガード新設・全リポジトリスキャンで
発見したtail_dcf_bridge.pyのtanukiフラグ検証漏れを同日中に修正）・
ASTS-SHARES-OSCILLATION-1（diluted_shares_used往復変動の恒久修正。
影響範囲が調査時点推定の3銘柄から新旧比較でCART/CEG/BROS/GEV/XOM/CONを
加えた9銘柄に拡大、副次発見のBROS Up-C組織再編前四半期をEPS-UPC-
PREREORG-1として分離登録）・WARN12-COHR-ONDS-1（根本原因がfact競合型
バグではなくSEC自動更新とTANUKI VALUATION再生成の生成順序のズレ〈約20
時間の陳腐化窓〉と判明、構造的ギャップをWORKFLOW-SEC-TANUKI-GAP-1として
新規登録）・HYPECORE-DASHBOARD-COUNT-BUG-1（index.htmlのticker数表示
修正、他8箇所の横展開確認で同型バグなしと確認）——を反映。前回
ブラッシュアップの教訓（「次セッションでの着手順序」欄の陳腐化）を踏まえ、
同日中の完了分もその場で同欄に反映し、次回候補をFLAG-THRESHOLD-DESIGN-1
筆頭に更新した。他の確認項目（BACKLOG_DONE.md記録の正確性・git status
のクリーン状態）はいずれも問題なし）

最終更新: 2026-07-13（セッション終了時ブラッシュアップ。ARCH-DATA-1の棚卸し
調査でQUALITY-GATES-EPIC-1のゲート1/ゲート2への統合マッピングを確認し、
Phase 3前提整理として[[ARCH-DATA-1-PREP-1]]（TAG-DEFS-UNIFY-1クローズ・
SOFI-DATA-1のLTDebt恒久修正〈2026-06-24の手動パッチが自動再生成で巻き戻って
いたことを発見・ticker_restrictionsによる恒久修正に切替〉・audit.py UP-C
検知・バグA/Bスコープ判断〈同日中に既に別コミットで解消済みと判明〉）を完了。
続けてPhase 3a（Gate2本体第一段階: `common/sec_data/contracts.py`新設。
FinancialEntry/EntryProvenance/FCFSeriesで規約A・B・③を型化し、
quarterly.py/normalizer.py/data_fetcher.pyのjson.dump()直前・fcf_list生成
箇所に検証を配線）を完了。全105銘柄で新旧比較（git stash、ネットワーク
未使用）し値の差分0件・TTMReader系メソッドの新旧比較も差分0件を確認。
pytest 302 passed/2 known failed。Phase 3b（独立実装4ファイルのreader.py
統合・規約C/Dの型化）・GATE2-READER-FCFLIST-1（reader.py::get_fcf_list()の
順序規約が未検証のまま残存）を新規登録。セッション終了時ブラッシュアップで
「次セッションでの着手順序」欄が2026-07-11以降更新されていなかった陳腐化を
発見し2026-07-12・07-13分を追記、SYSTEM_MAP.mdにcontracts.pyの記載漏れを
発見し追記、SOFI-DATA-1の旧完了エントリに巻き戻り発見の相互参照を追記。
他の確認項目（BACKLOG_DONE.md記録の正確性・git statusのクリーン状態）は
いずれも問題なし）

最終更新: 2026-07-12（同日13回目: セッション終了時ブラッシュアップ。
BACKLOG.md内QUALITY-GATES-EPIC-1エントリの陳腐化した中間ポインタ
（「次はPhase 2」、Phase 2a〜2b-3完了後も残置）を削除。
CLAUDE_CODE_START.mdに2件追記——①`if __name__ == "__main__":`ブロックを
持つスクリプト変更時はpytestに加え実機直接実行を必須化
（HYPECORE-SAVE-INDEX-NAMEERROR-1の教訓）、②cik_lookup.csvの4フラグを
参照するスクリプトの必須パターン（全銘柄一括取得は統一アクセサ経由、
CLI引数明示指定時も同フラグで検証、FLAG-CONSUMER-AUDIT-2/3の教訓）。
SYSTEM_MAP.mdの「銘柄振り分けの正本」セクションが本日の統一アクセサ導入・
CLI引数フラグ検証追加前の記述のまま陳腐化していたため全面更新
（`eps=true`が「バッチ実行に使われない」という誤記述を含む）。加えて
`extract_key_facts.py`が`common/sec_data/`ツリーの一部であるかのような
誤解を招く配置を訂正し、独立パイプラインである旨とfact選定ロジック統一
（SPLIT-AUTO-CHECK-1）を明記。他の確認項目（BACKLOG_DONE.md記録の正確性・
git statusのクリーン状態）はいずれも問題なし）

最終更新: 2026-07-12（同日12回目: HYPECORE-SAVE-INDEX-NAMEERROR-1を緊急対応
（優先度：高）で完了。`src/value/hypecore/hypecore.py::_save_tickers_index()`
の関数定義位置を`if __name__ == "__main__":`ブロックより前へ移動し、
2026-07-09 21:54以降3日間続いていたNameErrorを解消。GitHub Actionsの
"Run HypeCore Pipeline"失敗により"Commit and push"ステップがスキップされ、
週次自動更新が沈黙的に空振りしていた本番障害を解消。実機実行
（`python hypecore.py PLTR`）でNameErrorが発生せず終了コード0・
tickers.json自己再生成（updated_at最新化・103銘柄一致維持）を確認。
副次発見のdocs/index.html側の形式不一致バグを
[[HYPECORE-DASHBOARD-COUNT-BUG-1]]として新規登録。詳細はBACKLOG_DONE.md参照）

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

**Phase 3前提整理完了（2026-07-13）**: Gate2本体（正規化契約の構造化）着手前の
小粒4項目（[[ARCH-DATA-1]]棚卸しで発見・[[ARCH-DATA-1-PREP-1]]として実施、
完了・BACKLOG_DONE.md参照）を完了した。TAG-DEFS-UNIFY-1のクローズ判断・
normalized JSON不足フィールド補完（SOFI-DATA-1のLTDebt恒久修正）・
audit.py UP-C検知・バグA/Bのスコープ判断（既に解消済みと判明）のいずれも
Gate2の設計自体を左右する新規発見はなく、Phase 3設計セッションの着手条件が
整った。Gate2本体（型によるフィールド規約のコード化・出所/充足度メタデータ
付与）は未着手のまま。

**Phase 3a完了（2026-07-13）**: Gate2本体の第一段階として、JSON on-disk形式を
変えずに読み込み直後・書き込み直前でバリデーションする薄い型層
`common/sec_data/contracts.py` を新設した。対象は規約A（fcf_listの新しい順規約）・
規約B（quarterly.py標準エントリ形状）・規約③（出所・充足度メタデータ）の3点。
規約C（フィールド分類の二重管理）・規約D（enum風文字列の型化）と、4ファイル
（financial_trend_calculator.py・quarterly_review_generator.py・tail_dcf_bridge.py・
hypecore.py）のreader.py経由統合はPhase 3bとして分離登録（[[GATE2-PHASE3B-1]]参照）。

- `FinancialEntry`/`EntryProvenance`: quarterly.py::save_raw_table()・
  normalizer.py::save_normalized()のjson.dump()直前に検証を追加（検証のみ、
  保存対象データ自体は変更しないためJSON on-disk形式は不変）。あわせて
  `_select_best_candidate()`のフォールバック採用時・SOFI等のticker_restrictions
  オーバーライド採用時に`_provenance.source_tag`を付与するよう配線し、
  「なぜこの値が採用されたか」を出力JSONから追跡可能にした（全105銘柄で
  114件のフィールド×銘柄組み合わせに付与されることを確認）。SOFI-DATA-1の
  ような手動パッチが自動再生成で静かに巻き戻る事態の再発防止に直結する。
- `FCFSeries`: data_fetcher.py::TTMReader.get_fcf_series()内でのみ使用し、
  新しい順（降順）規約をconstruction時に検証する。JSONシリアライズ不可能な
  ため呼び出し境界で`.as_list()`により素のlist[float]へ変換して返す（戻り値の
  型・下流5+消費者への影響は変えない設計判断）。
- 検証: 全105銘柄の既存company_facts.jsonを用い、新旧コード（git stash）で
  build_raw_table()/normalize()の出力を`_provenance`除外で直接比較した結果、
  **値の差分は0件**（純粋な追加的変更であることを確認）。pytest 302 passed/
  2 known failed（既存4テストファイルのうち、正規表現importの都合で
  test_normalizer.pyのimport文をパッケージ経由に変更、_select_best_candidate()の
  戻り値がタプル化したことに伴いtest_tag_fallback_selection.pyの3箇所を
  タプルアンパックに変更、test_pipeline_logic.pyの1テストを新しい順序規約に
  合わせて仕様変更〈混在順序のTTM seriesを与えた場合、旧実装は誤った順序の
  まま`get_fcf_series()`が返していたが、新実装は安全側でNoneを返すよう変更〉）。
  新規`tests/test_contracts.py`を追加（26件、GROWTH-CAGR-SIGN-1相当の順序違反を
  意図的に発生させ`ContractViolation`が送出されることを確認するテストを含む）。
  `report_consistency_check.py` NG=0。

**規約A（fcf_list順序）の限界（次回セッションへの申し送り）**: `FCFSeries`は
「construction時に渡されたデータの順序」を検証するものであり、GROWTH-CAGR-SIGN-1の
実際のバグ（`calculate_fcf_cagr()`内部で`start_value`/`end_value`という変数への
割り当てを取り違えた、渡されたデータ自体は正しい順序だった）を直接再現・検知する
ものではない。`.newest`/`.oldest`という named accessor の提供によって「正しい
使い方を選びやすくする」ことが主眼であり、growth.py側がこれらのaccessorを実際に
採用するかはGate3（計算式検証）の範疇として別途判断が必要（今回は未着手）。

**規約A（reader.py::get_fcf_list()）の未カバー範囲**: 年次ベースのfcf_list
（`reader.py::get_fcf_list()`が生成、TTM系列が使えない銘柄のフォールバック経路）は
生成時点で既に日付情報が失われているため、`FCFSeries`の順序検証を今回は
適用できていない。reader.pyはPhase 3aの対象ファイル外（当初スコープの
normalizer.py/quarterly.py/data_fetcher.pyに含まれない）のため、対応要否は
次回セッションで判断する（[[GATE2-READER-FCFLIST-1]]として新規登録）。

#### 着手条件
なし。Phase 1・Phase 2a・Phase 2b-1・Phase 2b-2・Phase 3前提整理・Phase 3aは完了。
Phase 3b（4ファイル統合・規約C/D）は次回セッションで設計・着手する。
ARCH-DATA-1のスコープ拡張（2026-07-16、年次データ正規化3段階設計）
とは対象領域が重複しないため、並行して進めて支障ない。

---

### [ARCH-DATA-1] SECデータ正規化レイヤーの強化
**優先度:** 最高（2026-07-16、旧「高」からさらに格上げ — 「残課題④」参照）
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
- ~~normalized JSON に不足フィールド（ShortTermInvestments / 銀行移行後LTDebt 等）を補完~~
  ✅ 2026-07-13再調査で判明・完了。詳細はBACKLOG_DONE.md
  [ARCH-DATA-1-PREP-1] 参照（ShortTermInvestmentsは既に解消済みと確認、
  銀行移行後LTDebtはSOFI-DATA-1として恒久修正）
- ~~**年度判定の3箇所分散を単一関数に統合**~~ ✅ 2026-06-25完了
  （`common/sec_data/utils.py` に `determine_fiscal_year` を追加。parser.py・extract_key_facts.py・aggregate_annual の3箇所を統一）
- ~~**新規スコープ候補（2026-07-09追加）**: バグA・B（_estimate_ttm_operating_income()等の
  フォールバック実装がGrossProfit/RD/SM等複数フィールドの期末日整合性を検証せず
  暗黙に0円扱いしていた）~~ ✅ **既に解消済みと2026-07-13判明**。本追記の33分前、
  同日2026-07-09 19:54のコミット`1a8f5253d`「Moat Scoreフォールバックの2件のバグを
  修正（バグA・B）」で`_estimate_ttm_operating_income()`が`dict.get(end, 0)`の
  暗黙0円フォールバックから、GrossProfit/RD/SM3フィールドの共通end日
  （set intersection・4件未満ならNone）方式に修正済みだった。本追記時点で
  未反映のまま「新規スコープ候補」として残置されていた記録上の陳腐化。
  同種パターンの他箇所残存なし（grep確認済み）。

**年次データ正規化の3段階設計（2026-07-16確定）:**
今回（2026-07-16）のセッションで固まった年次データ正規化の設計方針。
[[FY52WEEK-BS-INSTANT-FACT-1]]事前調査で判明した未解決課題（残課題④
参照）を含め、以下の3段階でARCH-DATA-1本体として実装する。
1. ✅ **値の確定**: タグ＋日付をキーに正規化。同一キーで金額が食い違う
   場合は新しい報告書（filed日）を優先する（2026-07-16完了）
2. ✅ **年度ラベルの計算**: `determine_fiscal_year()`の月比較方式
   （month <= fiscal_end_monthによる片方向の年またぎ補正のみ）を廃し、
   企業ごとの決算アンカー日（月＋日）からの前後日数ウィンドウ判定に
   置き換える。12月決算企業でmonth<=12が恒常的にTrueになり判定が
   無効化する欠陥、および52/53週企業で決算日が前後にずれる際の
   片方向補正の限界を、両方とも解消する設計。（2026-07-17完了。
   詳細は下記「ステージ2完了」参照）
3. ✅ **裏取り**: 上記2で計算した年度と、XBRLの`fy`タグとの突き合わせを
   検証用の副次チェックとして実装（WMT型：企業側のfyタグ自体が誤って
   いるケースの検知用）。2026-07-17完了。詳細は下記「ステージ3完了」参照

**3段階設計は全て完了（2026-07-17）。**

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

**audit.py に追加すべき項目（SECデータ取得層）:**
- ~~yfinance株式数とSEC株式数の乖離が5倍以上の銘柄を WARNING 出力（2026-06-15 実装）~~
  **記録訂正（2026-07-13）**: audit.pyに実装されているのはAUDIT-SHARES-1
  （EPS Analyzer quarterly.json vs latest.json/DCFの希薄化株数比較、5倍閾値）で
  あり、「yfinance株式数 vs SEC株式数」の比較ではなかった。該当する
  yfinance-vs-SEC比較の実装は現状存在しない（本項目は元々の記述が誤りだった）。
- ~~10-Qに株式数タグが存在しない銘柄（UP-C構造等）を一覧表示~~ ✅ 2026-07-13完了。
  詳細はBACKLOG_DONE.md [ARCH-DATA-1-PREP-1] 参照

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

#### 着手前棚卸し・残課題①完了（2026-07-15）
着手前調査で、`contracts.py`（QUALITY-GATES-EPIC-1 Phase 3a）はARCH-DATA-1が
目指す「SEC変種吸収の正規化層への一本化」とは別レイヤー（型による構造検証の
み、変種吸収ロジックは含まない）と確認し、二重実装リスクなしと判断した。
既知SECデータ形バグ（PARSER-1・BUG-NETDEBT-1〜6・XBRL-TAG-KLAC-1系・
CHECK-QREV-FYE-1・DILUTION-FYE-1・LLY-CAPEX-STALE-1・BUG-EPS-ZERO-1/UNIT-1・
BUG-FOUR-1・SPLIT-AUTO-CHECK-1等20件超）を棚卸しし、正規化層（`tag_definitions.py`
等）への集約は部分的に進行済みだが、計算層（`pipeline.py`・`reader.py`）への
重複実装が①暦年グルーピング（trailing 370日窓）②BS項目「同一時点原則」の
2件残存していることを確認した。

上記①②を残課題①として一本化完了（コミット`4e4629a3b`・`60d44b2d8`）:
- ①`common/sec_data/utils.py::quarters_in_trailing_window()`に窓計算部分を
  共有化し、`quarterly.py::check_revenue_quality()`・`pipeline.py`
  （DILUTION-FYE-1）双方から参照する形に統一
- ②`reader.py::get_net_cash()`を正としてBS項目取得ロジックを一本化。
  調査の結果、単なるコード重複ではなくreader.py側だけがInsurance/Fintech
  セクターガードを適用しており、V（Visa）で実際に約$1.56Bの表示乖離
  （report.txt・TANUKI SCORE判定に使う値がDCF計算に使う値とズレていた）が
  発生していたことを実データで確認・是正した。副次的にSOUN（LTDebt=0の
  FY2024 10-K値が旧pipeline.py独自フィルタで誤除外されていたバグ）も是正。
  いずれもIntrinsic_Value自体・TANUKI SCORE分類には影響なし

残課題②（EPS Analyzer経路を正規化統合対象に含めるかのスコープ判断）は
[[EPS-ANALYZER-NORMALIZE-SCOPE-1]]として分離登録。残課題③（パターン判定
ロジックの実装、PREFLIGHT-CHECK-1と共有設計）は依然未着手（設計メモの
段階のまま）。

**軽微な残存（記録漏れの追加登録、2026-07-15）**: 残課題①の「最新
quarterly_*.jsonファイルを探す」処理パターンは、統合前は4箇所
（`reader.py`に2箇所・`pipeline.py`に2箇所）独立実装されていたが、
今回の一本化で`pipeline.py`側の1箇所を解消し3箇所に減った。残る
`pipeline.py`のDuPont分解（ROE = Net Margin × Asset Turnover ×
Financial Leverage）セクション内の1箇所は、Net_Debt算出とは無関係
（別の計算目的）のため今回のスコープ外としたが、将来
`reader.py::get_quarterly_range(ticker, quarters=1)`への統一で
解消可能。優先度は低く、着手条件なし。

#### 残課題③ 対応内容（2026-07-15完了・スコープ縮小）
着手前調査（2026-07-15）で、当初想定していた「PREFLIGHT-CHECK-1と共有する
汎用パターン判定カタログ」構想には2つの問題があると判明した:
1. `_extract_values_merged()`には候補タグ比較・競合検知の仕組みが一切なく、
   カタログの初期エントリとして使えそうな既存の「検知トリガー」も、
   SEC-REV-FINTECH-1/BUG-REV-SPAC-1型（revenue系タグ競合）については
   人間が10-K相当の文脈情報で正誤判断した一回限りの手動オーバーライド
   （`TICKER_RESTRICTIONS`）にすぎず、自動トリガーが存在しなかった
2. PREFLIGHT-CHECK-1が想定する新規登録時点（SEC EDGAR submissions API
   取得直後）の情報だけでは、revenue系タグ競合等の大半は「正誤確定」
   まではできず「リスクフラグ立て」止まりであり、精度未検証のまま
   共有カタログ化するのはリスクが高いと判断した

これを踏まえ、汎用カタログ構想は見送り、**revenue系タグ競合の実データ
検知**（`_extract_values_merged()`が静かに一本化してしまう競合を、
company_facts.json再読込により機械的に可視化する）に最小スコープを
絞って実装した（コミット`f05cae0ba`）:
- `common/sec_data/revenue_tag_conflict_check.py`新設。parser.py本体は
  無変更、`SECParser`の既存メソッド（`_detect_fiscal_end_month`/
  `_extract_single_key`/`_extract_values_merged`）を再利用し候補タグ
  一覧・年度判定ロジックを重複させない設計
- `update.py`のStep1完了直後（`check_revenue_quality()`の直後、4c.相当）
  に配線。新規のStep番号追加は不要だった（既存の4b.と同じ場所に
  差し込むだけで「Step1.5」相当のタイミングを実現できた）
- SOFI（$619.4M vs $3,613.4M、乖離5.8倍）・IONQ（$1,235.0M vs $11.1M、
  乖離111.0倍）の既知ケースを正しく再現することを確認
- 全100銘柄実行の結果、revenue系で14銘柄を検知（詳細は
  [[REVENUE-TAG-CONFLICT-SCAN-1]]参照。新規発見分の対応要否は別途判断）
- 自動修正は一切行わず、WARN出力（候補タグ名・各値・採用値の明示）のみ

残課題③はrevenue系タグ競合検知の実装をもって一区切りとする。パターン
判定ロジックの汎用カタログ化自体は、今回の知見（自動トリガーがほぼ
存在しない・登録時点情報では確定判定できないケースが多い）を踏まえ、
優先度を下げて次回以降に再検討する。

#### 残課題④（2026-07-16新規）
当初[[FY52WEEK-BS-INSTANT-FACT-1]]として個別調査した「BS項目
（instant fact）が52/53週バグの本人データ判定から対象外」問題は、
上記3段階設計で根本解決されるためARCH-DATA-1へ統合する
（[[FY52WEEK-BS-INSTANT-FACT-1]]エントリは削除し本項目への統合注記に置換）。

調査過程で、`_own_override_is_safe`の安全弁条件2
（`existing_end_dt.month <= fiscal_end_month`）が12月決算企業で
恒常的にTrueとなり機能しない欠陥を実データで確認した。実例:
CDNS FY2015のtotal_assets/revenueが、実際にはFY2014の値のまま
誤って保持されている（total_assets: 現状$3,209,556,000〈FY2014値〉、
正しくは$2,351,015,000。revenue: 現状$1,580,932,000〈FY2014値〉、
正しくは$1,702,091,000）。revenueは「完了済み」のFY52WEEK-
BUCKET-MISPLACE-1のスコープ内項目であったにもかかわらず、この
安全弁の欠陥により回帰が未解決のまま本番データに残っていた。
report_consistency_check.pyのCHECK-22（fyタグ衝突検知）はこの
ケースを検知しない（fy_collision_log.jsonにCDNSの記録なし）。

緊急の個別パッチ（安全弁条件2のみの差し替え）は見送り、根本解決
である上記3段階設計の実装をもって解消する方針とする（Koichiさん
判断・2026-07-16）。

また、「bsが空」のみを条件とした従来の対象件数カウント方法
（23件・53件）は、CDNS型（値は存在するが別年度の値が誤って
居座るケース）を検出できないことが判明した。3段階設計の実装後、
「フォールバック値と本人データ値の食い違い」チェックによる
全量再カウントが別途必要になる。

#### ステージ1（値の確定）完了（2026-07-16）
10-K/A候補プール化・filed日タイブレーク・出所メタデータサイドカー
（{bs,pl,cf,shares,other}_provenance）を実装（コミット`4587ee09e`）。
全105銘柄再生成（コミット`ba9927676`）し、事前検証の185件・18銘柄
（AAPL/ASTS/CELH/CPRT/DOCN/IONQ/JOBY/LITE/LYFT/QBTS/RDW/RKLB/RMBS/
SOFI/SPIR/TSLA/VRT/WST）と完全一致することを確認した。全件が実際に
公表されているSEC訂正事象（SPACワラント会計是正・QBTSのSR&ED税額
控除誤り・LYFTの再保険会計問題・AAPLのサブスクリプション会計早期
適用等）と整合することを一次情報で確認済み。pytest 309 passed
（既知2件除く）・report_consistency_check NG=0、いずれも変更前と同一。

5年トレーリング指標への影響が見込まれたDOCN/LYFT/QBTS/SPIRを個別
確認した結果、DOCN/LYFT/QBTSはROE平均が変化したもののalpha=0.0000
床打ちにより吸収されIntrinsic_Value・TANUKI SCORE分類とも完全不変。
SPIRのみR&D資本化経路の変化によりIntrinsic_Value_BASEが+7.6%
（$29.44→$31.68）変化したが、分類（PASS）は維持された。

ステージ2（年度ラベル計算のアンカー日ウィンドウ化・RCAT型決算期変更
検知）・ステージ3（fyタグ裏取り強化）は未着手。CDNS FY2015の
total_assets/revenue誤りはステージ1の対象外のため未解消のまま
（想定通り、ステージ2待ち）。

#### ステージ2（年度ラベル計算のアンカー日ウィンドウ化）完了（2026-07-17）

`determine_fiscal_year()`の「month > fiscal_end_month」片方向月比較を、
決算アンカー日（月+日）を中心とした前後日数ウィンドウ判定に置き換えた
（`common/sec_data/utils.py`）。

**実装内容:**
- `detect_fiscal_end_month()`: parser.py・extract_key_facts.pyに分散していた
  会計年度末月検出ロジックを統一（parser.py側の「10-K完全一致・10-K/A除外」を
  正本採用）。extract_key_facts.py側の独自実装（旧`determine_fiscal_year_end()`）
  は削除
- `detect_fiscal_anchor_date()`: 本人10-K annualエントリ（340〜380日）の
  end日から決算アンカー日（月+日）を検出
- `determine_fiscal_year()`: end_date.yearを中心に[year-1,year,year+1]の
  3候補年度でアンカー日との日数差を比較し最小の年度を採用。最小日数差が
  60日を超える場合はWARNログを出力し月のみ比較にフォールバック（安全弁）
- `_own_override_is_safe()`（parser.py）: 条件2の`no_crossing_needed`
  事前フィルタ（月のみ比較で12月決算企業では恒常的にTrueとなり機能しない
  欠陥があった）を廃止し、統一版`determine_fiscal_year()`の1条件に統一
- 呼び出し元8箇所（parser.py 4箇所・extract_key_facts.py 4箇所）に
  anchor_month/anchor_dayを追加

**JNJ/TDY型の追加発見と対応（実装中の検証で判明）:**
`detect_fiscal_anchor_date()`の初版（(月,日)完全一致の最頻値方式）で
105銘柄ネットワーク未使用比較を実施したところ、JNJ・TDY（決算日が
12月末〜1月頭を往復する52/53週企業）で、企業自身のfyタグと矛盾する
誤判定を新たに発見した（例: JNJのend=2013-12-29はJNJ自身がfy=2013と
申告しているが、アンカーが(1,1)と検出されたため2014と誤判定）。
BS項目（instant fact）は本人データ上書きの安全網対象外（残課題④/
FY52WEEK-BS-INSTANT-FACT-1系統、未解消のまま）のため、この誤判定が
そのまま年度ラベルに反映されてしまう。

原因はDec側（複数の微妙に異なる日）とJan側（別の複数の日）に得票が
分散し、たまたまJan側の1点が単独最多になったこと。年境界をまたぐ
循環距離（±7日）でクラスタリングし、最大クラスタの中央値（実在しない
場合はクラスタ内最頻値）を採用する方式に変更して解消した
（`_cluster_fiscal_anchor_candidates()`新設）。この経緯を反映し、
CHAT_RULESの「検証結果が依頼の前提と乖離した場合の一時停止」ルールに
従い一度立ち止まって報告・設計変更の承認を得てから実装した。

**検証結果:**
- 全105銘柄ネットワーク未使用新旧比較: 830件・16銘柄
  （ADBE/AVGO/CAKE/CDNS/CEG/DELL/ELF/IOT/JNJ/KLAC/LITE/MRVL/MSCI/
  RDW/TDY/WST）に差分。CDNS FY2015のtotal_assets $3,209,556,000→
  **$2,351,015,000**・revenue $1,580,932,000→**$1,702,091,000**が
  ステージ1完了時点から引き継いでいた既知の誤りとして正しく是正されたことを
  一次情報（company_facts.json内のown data・reportDate照合）で確認。
  AVGOの真のFY2025値がbucket 2026という存在しない年度に誤配置されていた
  問題も是正（是正に伴い`common/sec_data/data/AVGO/annual_2026.json`が
  化石ファイル化したため削除。`save_parsed_data()`に古い年度ファイルの
  自動削除ロジックがない既知の構造的問題〈IOT/AVGO/MRVLの化石ファイル
  問題と同型〉に起因し、今回もCLAUDE Code側で手動削除が必要だった）
- JNJ/TDYはクラスタリング方式変更後、企業自身のfyタグと一致する年度に
  是正されることを確認（是正範囲は52/53週の年境界越えが実際に発生する
  年度のみに限定され、修正前の(1,1)アンカー版で発生していた「ほぼ全年度が
  1年ずつシフトする」広範な誤判定は解消）
- 影響16銘柄でTANUKI VALUATIONを再生成し、TANUKI SCORE分類
  （BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）は全銘柄で不変を確認。
  Intrinsic_Value_Per_Shareは AVGO +10.6%・JNJ +2.8%・TDY -1.4%
  変化（他13銘柄は不変）
- pytest 325 passed（既知2件除く、新規16件のアンカー日ウィンドウ境界
  テストを含む）・report_consistency_check.py NG=0/WARN=41（変更前と同一）

**未解決のまま残る点（ステージ3以降）:**
- RCAT型決算期変更検知（企業が実際に決算期を変更したケースと、単なる
  52/53週の測定誤差との区別）は本ステージのスコープ外で未着手
- 残課題④のBS項目（instant fact）本人データ判定除外は未解消のまま
  （ステージ3のfyタグ裏取り強化、または別途の安全網設計が必要）

#### ステージ3（fyタグ裏取り）完了（2026-07-17）

ステージ2で計算した年度ラベル（`determine_fiscal_year()`の結果）と、
XBRLの`fy`タグとの突き合わせを検証用の副次チェックとして実装した
（WMT型：企業側のfyタグ自体が誤っているケースの検知用）。

**実装内容:**
- `parser.py`: `{bs,pl,cf,shares,other}_provenance`サイドカーに
  生XBRL `fy`タグ値を`fy_tag`フィールドとして追加（既存の
  accn/filed/is_own_dataに追加するのみ、破壊的変更なし）。
  `_own_override_is_safe`内で`_collect_own_data_annual`の戻り値も
  `(val, end_date, accn, filed, raw_fy_tag)`の5要素に拡張し、
  fyタグ衝突・自然分離ケースでも本来の生タグを正しく追跡できるようにした
- `_extract_values_merged`/`_extract_values_best_candidate`の両方に
  `fy_mismatches_out`引数を追加し、`annual_provenance`構築後に
  `fy_tag != 年度バケツキー`のエントリを検出して集約する仕組みを新設
- `_save_fy_tag_mismatch_log()`（`_save_fy_collision_log`と同パターン）で
  `common/sec_data/data/{ticker}/fy_tag_mismatch_log.json`に記録
- `report_consistency_check.py`にCHECK-23/WARN-23を新設。CHECK-22
  （同一fyタグへの複数本人end_date競合）とは独立した別軸で、
  「fyタグは単一だが値の年度バケツ配置自体がfyタグと異なる」CDNS型を検知する
- `config/warn_acknowledged.json`にWARN-23のNVDA・CAKEを一次情報検証済みとして事前登録

**設計変更の経緯（is_own_data=False側の除外、2026-07-17）:**
初版実装では`is_own_data`の値に関わらず全ての不一致を記録し、
`is_own_data=True`を「要確認」・`is_own_data=False`を「info」として
記録する2段階設計だったが、全105銘柄検証で**4,434件・105/105銘柄**
という実用に耐えないノイズになることが判明した。原因は、
`is_own_data=False`側の大半が比較年度再掲エントリ（例: 2008年の数値が
2011年の10-Kに比較年度として再掲載）由来であり、XBRLの`fy`タグは
「その数値がどの10-Kに載っていたか」というfiling側の属性でしかなく、
比較年度再掲エントリでは載っていた10-Kの年と数値が表す期間が
一致しないのが正常仕様（企業の申告ミスとは無関係）と判明したため。
CHAT_RULESの一時停止ルールに従い報告・設計変更の承認を得た上で、
`is_own_data=True`（本人データ自身のfyタグが実際に採用されてしまって
いるケース）のみを検知対象に限定し、severity区分（要確認/info）自体を
撤去して単一区分に簡素化した。

**検証結果:**
- 全105銘柄ネットワーク未使用検証: `is_own_data=True`限定後は
  **281件・10銘柄**（ADSK/AVAV/CAKE/COHR/CRM/FCX/FICO/HON/NVDA/WMT）
  に集約。281件を(ticker, end_date, fy_tag, computed_year)で重複排除
  すると**16件の distinct イベント**まで縮小し、1イベントあたり平均
  12〜26フィールドに重複計上されていたことを確認（同一10-Kから
  抽出される複数フィールドが同じ期間ズレを共有するため。フィールド
  単位ではなく期間単位で見れば実態はさらに小さい）
- NVDA・CAKEの2件は一次情報（NVIDIA自身の決算発表・Cheesecake Factory
  自身の決算発表）で検証済み: いずれもXBRL `fy`タグ側の誤りで
  computed_year側が正しいことを確認（NVDA: end=2013-01-27の売上$4.28Bは
  NVIDIA自身が「fiscal 2013」と公表・fyタグは2012と誤り。CAKE:
  end=2023-01-03はCheesecake Factory自身が「Fourth Quarter of Fiscal
  2022」と公表・fyタグは2023と誤り）。両者とも`_own_override_is_safe()`
  の安全弁によりcomputed_year経由の正しい値が本番データで既に採用されて
  おり実害なし
- 全105銘柄で新旧比較（annual_*.jsonの値そのもの）: **差分0件**を確認
  （fy_tagサイドカー追加のみで既存の値・TANUKI SCORE分類には一切影響しない）
- pytest 337 passed（既知2件除く、新規12件のfy_tag裏取りテストを含む）
- report_consistency_check.py: NG=0/WARN=51（stage2完了時点の41件から
  +10、影響10銘柄それぞれにWARN-23が1件ずつ追加。NVDA/CAKEは事前登録済み
  のため確認済み表示、残り8銘柄は🆕未確認として表示される）

**3段階設計（値の確定→年度ラベル計算→裏取り）が全完了。**

**未解決のまま残る点:**
- RCAT型決算期変更検知は引き続き未着手
- 残課題④のBS項目（instant fact）本人データ判定除外は未解消のまま
  （BS項目はstart日を持たないため`_collect_own_data_annual`の対象外
  であり、fy_tagサイドカーはフォールバック経路でのみ記録される。
  ステージ3の裏取りチェック自体はBS項目にも及ぶが、本人データ判定
  自体の拡張は別途必要）
- WARN-23の281件→16件イベントという重複計上は、(ticker, end_date)
  単位での集約表示に改善する余地があるが、今回のスコープ外として
  reportのみに留めた

---

## 優先度：高（早急に対応）

### [FY52WEEK-BS-INSTANT-FACT-1] BS項目（instant fact）が52/53週バグの本人データ判定から対象外で値がNoneに変化する
**状態:** [[ARCH-DATA-1]]へ統合済み（2026-07-16）

2026-07-16の事前調査で、本問題（duration検証を経由しないBS項目が
reportDate==end_date本人データ判定の対象外になり値がNoneに変化する
事象。DELL 2023・AVGO 2024・ADBE 2021・CDNS 2014/2020ほか）は、
[[ARCH-DATA-1]]が計画する年次データ正規化の3段階設計（値の確定→
決算アンカー日ベースの年度ラベル計算→XBRLタグ・reportDateとの
突き合わせ検証）で根本解決される対象と判断し、個別タスクとしては
クローズして[[ARCH-DATA-1]]へ統合した。調査過程で発見した
`_own_override_is_safe`安全弁の未解決の欠陥（CDNSでの実害確認含む）・
「bsが空」のみでは対象を網羅できない問題等の詳細は[[ARCH-DATA-1]]の
「残課題④」参照。

---

### [FY52WEEK-BS-NULL-SILENT-1] BS項目がNoneの場合`or 0`パターンで静かに$0として計算に組み込まれる
**優先度:** 高
**分類:** アーキテクチャ / データ品質ゲート
**登録日:** 2026-07-15
**発見:** FY52WEEK-BUCKET-MISPLACE-1の実装過程

#### 問題
BS項目（total_assets/stockholders_equity/cash_and_equivalents等）が
Noneになった場合、コードベース全体で一貫して`or 0`パターンにより
静かに$0として計算に組み込まれることが判明した。None自体を検知して
警告する仕組みは存在しない。確認済みの該当箇所（最低3件、他に類似
パターンが存在する可能性あり）：

- `common/sec_data/reader.py:382`（Net Debt計算）
  `cash = bs.get("cash_and_equivalents", 0) or 0`
- `common/screening/dcf_validity_checker.py:173-176`（投下資本計算）
  `equity = bs.get("stockholders_equity") or bs.get("total_equity") or 0`
- `common/sec_data/report_consistency_check.py:532-539`（WARN-12
  Cash-STI期ズレ）
  `_ann_cash12 = _ann_bs12.get("cash_and_equivalents") or 0`

複数年度を横断参照する箇所（`reader.py:172` `get_roe_avg_detail()`の
ROE平均計算等）では、該当年度がif文により静かにサンプルから除外
される（クラッシュはしないが、利用者からは「その年のデータが
減った」ことが一切分からない）。

これは「各データポイントは正しいか、明確に信頼できないとフラグ
付けされているか」という本プラットフォームの根本方針に反する、
TRUST-SUMMARY-EPIC-1が対象とする領域の具体的な一事例。
[[ARCH-DATA-1]]（旧[[FY52WEEK-BS-INSTANT-FACT-1]]、2026-07-16に
ARCH-DATA-1へ統合済み）の修正が入るまでの間、及び今後同種の
None化が他の原因で発生した場合全般に関わる、より広い構造的リスク。

#### 対応方針
`or 0`パターンをNone検知＋明示的警告（report_consistency_check.py
のWARN体系への追加、または該当データを「信頼できない」フラグ付きで
返す設計）に置き換える。対象箇所の網羅的な洗い出しが必要（今回発見
した3箇所は氷山の一角の可能性）。

#### 着手条件
なし

ARCH-DATA-1の3段階設計とは独立に着手可能。ただしARCH-DATA-1の
実装後に新たに生まれるNoneパターン（値の確定・年度ラベル計算の
途中で生じうる欠落等）も本タスクの対象に含めて拾えるよう、
ARCH-DATA-1の設計・実装状況を横目に見ながら進めることが望ましい。

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
- [[SECTOR-FCF-RATE-BROKEN-1]]（完了・BACKLOG_DONE.md参照）（段階2寄り）: sector取得経路破損。
  「解消可能な不備」の実例（バグ①②③として構造分析→2026-07-14完了）
- [[ARCH-DATA-1]]（段階0寄り）: SECデータ正規化レイヤーの強化。
  2026-07-15に残課題①（計算層重複実装の一本化: 暦年グルーピング・
  BS項目同一時点原則）・残課題③（revenue系タグ競合検知の実装）が
  完了済み。残課題②（EPS Analyzer経路のスコープ判断、
  [[EPS-ANALYZER-NORMALIZE-SCOPE-1]]へ分離）は未着手のまま
- [[LLY-CAPEX-STALE-1]]（段階0・完了・BACKLOG_DONE.md参照）: 解消可能な
  バグの実例として先行登録され、Phase 2aで根本原因を解消済み
- [[FCF-CONVRATE-DESIGN-LIMIT-1]]（段階2寄り）: 残課題2・3を2026-07-15
  本EPICへ統合（下記「FCF/DCF信頼性層への統合スコープ」参照）

#### FCF/DCF信頼性層への統合スコープ（追記、2026-07-15・[[FCF-CONVRATE-DESIGN-LIMIT-1]]より）
FCF/DCF信頼性層のスコープに、FCF-CONVRATE-DESIGN-LIMIT-1由来の
2課題を統合：①固定比率設計がサイクル変動銘柄（SITM実測: 転換率が
年により0.065倍〜3.65倍に変動）を表現できない構造的限界、
②Damodaran EBIT(1-t)ベースの業種比率を純利益ベースへ変換する
ロジックが存在せず、LITE/SITM実データで符号反転ケースを確認済み。
対応方針: 精緻な変動モデル・変換式の個別開発ではなく、該当銘柄の
conversion_rateの信頼度を下げてフラグ化する設計に寄せる
（on-a-journeyの『データ点は正しいか、明確に不信頼フラグを
立てるか』というコンセプトに沿う）。

加えてFCF-CONVRATE-DESIGN-LIMIT-1残課題①由来として、sector未収録
のためconversion_rateがdefault(0.70)のまま実質未検証となっている
44銘柄（うちfcf_estimation.applied=True 33銘柄、乖離大: LITE 4.33倍・
SPIR 8.65倍・LLY 1.92倍等）を統合。カテゴリの個別追加ではなく、
sector未収録＝conversion_rate未検証という状態そのものを信頼度フラグ
として表面化する設計に一本化する。

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

### [REVENUE-TAG-CONFLICT-SCAN-1] revenue_tag_conflict_check.py全銘柄実行で新規発見した候補タグ競合
**優先度:** 未定
**分類:** データ品質 / SECデータ取得層
**登録日:** 2026-07-15
**発見:** [[ARCH-DATA-1]]残課題③ `revenue_tag_conflict_check.py`実装時の全100銘柄検証

#### 内容
新設した`revenue_tag_conflict_check.py`（乖離2.0倍以上を検知）を全100銘柄
（tanuki=true）で実行した結果、revenue系フィールドで**14銘柄**が該当した。

- **既知・対応済み**: SOFI（乖離5.8倍、SEC-REV-FINTECH-1で対応済み）・
  IONQ（乖離111.0倍、BUG-REV-SPAC-1で対応済み）
- **既知・SEC-TAG-FICO-CPRT-1で既に修正済みと再確認できた**: CPRT
  （FY2019-2020）・FICO（FY2019-2020）。現在の採用値が同タスクの
  修正記録と一致することを確認
- **判定完了・実害なし（2026-07-15確認）**: **LITE・TER**。採用された値
  （マージ後の値）は実際には正しい年次値であり、「競合」として検知
  されたのは比較対象タグが当該年度の年次データを持たず四半期の残骸
  しかない場合だった（false positiveに近い）
- **判定完了・正当な業種差でバグではない（2026-07-15確認）**: **PM**
  （Philip Morris、FY2016-2022）。すべての候補タグ
  （`RevenueFromContractWithCustomerExcludingAssessedTax`＝$26-31B、
  `IncludingAssessedTax`/`SalesRevenueNet`＝$74-82B）が正規の365日間
  年次エントリであり、税抜/税込という実在する会計上の区分（SOFIと
  同種の「業種知識が必要な正当な差異」）
- **要対応・[[FY52WEEK-BUCKET-MISPLACE-1]]へ統合済み**: **AVGO・DELL・
  CAKE・ELF**（+**RCAT**要確認）。52/53週会計年度企業で
  `determine_fiscal_year()`の月判定により真の年次値が隣接年度バケツへ
  誤って混入する問題。詳細・対応方針・duration filter試行結果は
  同エントリ参照
- **要対応・[[REVENUE-TAG-PRIORITY-FRAGILE-1]]へ統合済み**: **TDY・ASTS**。
  `XBRL_MAPPING["revenue"]`の候補優先順位設計に起因する別種の欠陥
  （TDYはセグメント限定タグの誤優先、ASTSは提出元XBRL入力ミスだが
  現状の採用値は処理順で偶然正しく救われているのみ）。詳細は同エントリ参照

#### 対応方針（絞り込み済み・2026-07-15）
14銘柄の内訳を精査した結果、**残る要対応銘柄はAVGO/DELL/CAKE/ELF
（+RCAT要確認）に絞り込まれた**（TDY/ASTSは別種の欠陥として分離、
LITE/TER/PMは実害なし・正当な差異と判定済みでクローズ）。
AVGO/DELL/CAKE/ELF＋RCATの対応は[[FY52WEEK-BUCKET-MISPLACE-1]]、
TDY/ASTSの対応は[[REVENUE-TAG-PRIORITY-FRAGILE-1]]にそれぞれ統合した
ため、本エントリは調査記録として維持しつつ、今後の作業は上記2エントリ
側で追跡する。

#### 副次的な設計上の発見（重要・将来の横展開時に必読）
`selling_and_marketing`（35銘柄該当）・`depreciation_and_amortization`
（83銘柄該当）フィールドも同時に検知対象としたが、これらは候補タグ同士が
実際には親子/包含関係にある（例: `DepreciationAndAmortization` ⊇
`AmortizationOfIntangibleAssets`、`SellingAndMarketingExpense` ⊇
`AdvertisingExpense`）ため、revenue系のような「本来同一概念であるべき
候補の食い違い」ではなく、大半が構造的なfalse positiveと判明した。将来
この2フィールドの精度を上げる場合、単純な倍率閾値ではなく候補タグ間の
包含関係を考慮した判定ロジックが必要（現状は`revenue_tag_conflict_check.py`
の出力上は3フィールドまとめて表示されるため、運用時はrevenue系の結果を
中心に見ること）。

#### 着手条件
なし

---

### [EPS-ANALYZER-NORMALIZE-SCOPE-1] EPS Analyzer独自SECデータ抽出パイプラインの正規化統合対象化の要否判断
**優先度:** 未定
**分類:** アーキテクチャ / SECデータ取得層
**登録日:** 2026-07-15
**発見:** [[ARCH-DATA-1]]着手前棚卸し調査

#### 内容
EPS Analyzer（`src/value/adjusted_eps_analyzer/extract_key_facts.py`）は
ARCH-DATA-1が現在スコープとする`parser.py`/`normalizer.py`/`data_fetcher.py`/
`common/sec_data/`配下とは別の独立SECデータ抽出パイプラインであり、同種の
タグフォールバック・fact選定ロジックを独自実装している（`SPLIT-AUTO-CHECK-1`
完了記録で対象外と明記済み。SEC Company Facts APIを都度ライブ取得し、
ローカルraw JSONキャッシュも持たない。importしているのは
`common.sec_data.utils.determine_fiscal_year`のみ）。

これをARCH-DATA-1の正規化統合対象に含めるか、独立パイプラインとして維持
するかを次回セッションで判断する。

#### 着手条件
なし（次回セッションで方針判断してから着手）

---

### [TTM-STOCK-FIELDS-DEAD-1] ttm_calculator.pyのSTOCK_FIELDS/SHARES_FIELDS分類が構造的に本番未到達
**優先度:** 未定
**分類:** アーキテクチャ / SECデータ取得層 / QUALITY-GATES-EPIC-1（GATE2-PHASE3B-1関連）
**登録日:** 2026-07-17
**発見:** GATE2-PHASE3B-1②実装時の検証で発見

#### 内容
GATE2-PHASE3B-1②（規約C: フィールド分類の二重管理是正）の実装・検証過程で、
`ttm_calculator.py::STOCK_FIELDS`にCurrentAssets/CurrentLiabilitiesを追加しても
本番の`{ticker}_ttm_series.json`（update.pyが実際に呼ぶ`calc_ttm_series()`の
出力）には一切反映されないことが判明した。追加調査の結果、これは
CurrentAssets/CurrentLiabilities固有の問題ではなく、**STOCK_FIELDS/
SHARES_FIELDS分類全体が構造的に本番未到達**という、より広い構造的問題と
判明した。

**根本原因**: `calc_ttm()`/`save_ttm()`（`{ticker}_ttm.json`生成、STOCK_FIELDS/
SHARES_FIELDSを実際に処理する唯一の関数）は、2026-05-07の`c3880e737`
（"switch FCF/RICE source to rolling TTM series"）で`calc_ttm_series()`が
追加されて以降、用途を失った。2026-05-11に一瞬（2分間）update.pyから
誤って呼ばれた形跡があるが（`38ae3f75a`→`210cdb01e`で即座に
`calc_ttm_series()`へ修正）、それ以降は**本番から一切呼ばれていない
到達不能コード**である。

**8メンバーの内訳**（全て`calc_ttm_series()`＝本番経路を経由しない）:
- 完全にデッド（他経路の消費者もゼロ）: Cash・STDebt・DeferredRevenue・
  Equity・Assets（5件）
- 別実装で個別生存（ttm_calculator.pyの分類・calc_ttm_series()を経由せず、
  reader.py・audit.py・quarterly_review_generator.py・tail_dcf_bridge.py・
  pipeline.pyがそれぞれ独立にnormalized JSONを直接読む）: LTDebt・
  SharesBasic・SharesDiluted（3件）

残り3件の「別実装で個別生存」構造は、[[GATE2-PHASE3B-1]]①（独立実装4ファイルの
reader.py統合）が対象とする問題と一部重複する。

#### 対応方針候補（未確定、次回セッションで判断）
(a) `calc_ttm()`/`save_ttm()`を削除し、STOCK_FIELDS/SHARES_FIELDS分類自体も
    「現状使われていない予約分類」として整理する（最小対応）
(b) `calc_ttm_series()`にSTOCK_FIELDS/SHARES_FIELDS相当の処理を追加し、
    本番の`_ttm_series.json`に`stock`/`shares`キーを持たせるよう拡張する
    （LTDebt/SharesBasic/SharesDilutedの既存個別実装をこちらに統合する
    将来性を含む、[[GATE2-PHASE3B-1]]①との連携も視野に入れた対応）
(c) 現状維持（デッドコードの存在自体は実害なしのため、着手条件が
    整うまで先送り）

#### 着手条件
なし（次回セッションで規模見積もり・対応方針・優先順位を判断してから着手）

---

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

### [MA-INTEGRATION-TAG-GAP-1] adjustment_items.jsonのma_integration項目がXBRLタグ不足、TRANSIENT_CATEGORIESからも除外され実キャッシュM&A費用を検出漏れ
**優先度:** 未定（全銘柄への影響範囲を網羅調査した上で確定）
**分類:** データ品質 / 一過性費用検出
**登録日:** 2026-07-14
**発見:** [[TRANSIENT-EXPENSE-COVERAGE-1]]（完了・BACKLOG_DONE.md参照）（AVAV/RDW調査）の副次発見

#### 内容
AVAV・RDWの一過性費用検出漏れを10-K原文で調査した結果、両社とも
`config/adjustment_items.json`のma_integration項目（買収・統合関連
カテゴリ）が実際に両社が使用するXBRLタグを拾えていないことが判明した：

1. **タグ不足**: ma_integration項目のxbrl_tagsが
   `us-gaap:BusinessCombinationIntegrationCosts`のみで、以下が未登録：
   - `us-gaap:BusinessCombinationAcquisitionRelatedCosts`
     （AVAV FY2026: $48.17M、RDW FY2025: $21.24M で実際に使用）
   - `us-gaap:BusinessCombinationIntegrationRelatedCosts`
     （RDW FY2025: $1.14M、登録タグと"Related"の有無のみ相違）

2. **カテゴリ設計の問題**: `calculator/adjustments.py:772-776`の
   `TRANSIENT_CATEGORIES = {"リストラ・事業再編関連", "在庫・サプライチェーン
   関連", "金融関連"}`から「買収・統合関連」カテゴリ自体が丸ごと除外されて
   いる。これはのれん減損・無形資産償却等の非現金項目を除外する意図の
   設計だが、ma_integration（実キャッシュ支出項目）も同一カテゴリに
   含まれているため巻き込まれて除外されている

AVAV・RDW自体は悪化の主因が別（運転資本変動）だったため実害は軽微
だったが、M&A取引費用そのものが悪化の主因になる別の銘柄では実害が
大きくなる可能性がある。

#### 調査要望（着手時）
全105銘柄でM&A関連XBRLタグ（`BusinessCombinationAcquisitionRelatedCosts`等、
未登録タグ候補を含む）の申告有無・金額を洗い出し、上記2つの穴
（タグ不足・カテゴリ除外設計）の影響を受けている銘柄が他にないか
網羅的に確認すること。

#### 着手条件
なし

---

### [FCF-CONVRATE-DESIGN-LIMIT-1] SECTOR-FCF-RATE-BROKEN-1修正後もLITEの業種カテゴリ欠落・固定比率設計の限界が残存
**優先度:** 未定（2026-07-14 6/8カテゴリのキー名不一致修正・
Software_Systemグループ分割は完了。残るIOT等判定保留5銘柄・暫定判定
精度の2課題は再評価待ち。LITE/SITMカテゴリ欠落・固定比率設計の限界・
EBIT(1-t)→純利益変換ロジック不在の3課題は2026-07-15
TRUST-SUMMARY-EPIC-1へ統合済み）
**分類:** DCF信頼性判定ロジック / データ推定
**登録日:** 2026-07-14
**発見:** [[FCF-EPS-CONVRATE-SECTOR-1]]（完了・BACKLOG_DONE.md参照）（LITE/SITM）調査時

#### 内容
SECTOR-FCF-RATE-BROKEN-1（sector取得経路のバグ）を修正しても、
以下2点はLITE/SITMのconversion_rate精度改善には不十分であることが判明：

1. **LITEに対応するfcf_conversion_config.jsonの業種カテゴリが存在しない**
   （Software_Internet/AdTech_Internet/Semiconductor/Cloud_Services/
   EV_Automotive/Fintech/Consumer_Beverage/Space_Defenseの8分類中、
   光学部品・通信機器ハードウェア製造業に該当するものがなく、
   sector修正後もdefaultに留まる可能性が高い）

2. **固定比率という設計自体がサイクル変動の大きい銘柄を表現できない**
   （SITMの実質転換率は年により0.065倍〜3.65倍と振れており、
   どの固定値を設定しても大幅乖離は解消しない構造的限界）

代替経路として`growth_sanity.py`のdamodaran_industry判定
（Damodaranデータ＋銘柄別手動マッピング辞書）も確認したが、
LITE・SITMともに未登録（damodaran_industry=None）でこちらも
追加整備が必要。

#### 追加調査で判明した問題（2026-07-14 調査・キー名不一致）
上記1の再評価のため`estimate_fcf_from_eps()`の基準（純利益ベースか
EBIT(1-t)ベースか）を確認する調査を実施した際、当初想定と異なる
より根の深い問題が判明した：**現行8カテゴリのキー名
（EV_Automotive/Fintech/Consumer_Beverage/Space_Defense/
AdTech_Internet/Cloud_Services）が、実際に`config/beta_config.json`
の`overrides.<TICKER>.sector`へ書き込まれるDamodaran taxonomy準拠の
表記（Auto_Truck/Financial_NonBank/Beverage_Soft/Aerospace_Defense等）
と文字列不一致だったため、Software_Internet（3銘柄）・Semiconductor
（7銘柄）を除く6カテゴリは該当銘柄0件＝事実上デッドコードだった**
（tanuki=true全100銘柄で実測。TSLA/LMT/KO/PEP/SOFI/V/MSCI等、本来
非defaultレートが適用されるべきだった銘柄が軒並みdefault(0.70)に
落ちていた）。ダモドラン公式データセット（oifcff.xls、94業種）との
突合では、現行8カテゴリは全て単一のダモドラン業種への1:1対応で
あり、複数業種の平均・統合ではないことも確認した。

#### 対応内容（2026-07-14 実装完了・キー名リネームのみ）
`fcf_conversion_config.json`の`sector_conversion_rates`・
`_sector_rationale`のキー名を、`growth_sanity.py::SECTOR_TO_DAMODARAN`
（既存の正式なDamodaran業種マッピング辞書）を用いて実際の
beta_config.json sector表記に一致させてリネームした（**転換率の数値は
一切変更していない**）：
- `EV_Automotive` → `Auto_Truck`（0.65のまま）
- `Space_Defense` → `Aerospace_Defense`（0.55のまま）
- `Consumer_Beverage` → `Beverage_Soft`（0.75のまま）
- `Fintech` → `Financial_NonBank`（0.50のまま）
- `AdTech_Internet` → `Advertising`（0.88のまま。該当銘柄0件のため
  SECTOR_TO_DAMODARANの逆引きで本来の表記に合わせた）
- `Cloud_Services` → `Software_System`（0.80のまま。同様に逆引き。
  結果としてADBE/CRM/NOW/PLTR/INTU/DDOG等23銘柄の広範な
  エンタープライズソフトウェア群が対象になった。この23銘柄は
  Azure型クラウドインフラ企業を想定した`Software_System`の
  _sector_rationale説明文とは事業特性が幅広く異なる可能性があり、
  レート0.80の妥当性自体は未検証のまま——次項の残課題参照）
- `Software_Internet`・`Semiconductor`は元々一致していたため変更なし

全105銘柄（tanuki=true 100銘柄）で新旧比較を実施し、38銘柄で
新たにdefault以外のconversion_rateが適用されるようになったことを
確認（TSLA→0.65、LMT/AVAV/HEI/HWM/LOAR/RDW→0.55、KO/PEP/CELH→0.75、
SOFI/V/MSCI/FLYW/PAYS→0.50、ADBE/ADSK/APP/BSY/CDNS/CRM/CWAN/DDOG/
ESTC/FICO/FROG/FRSH/GTLB/INTU/IOT/NOW/PLTR/QBTS/RBRK/S/SNPS/SOUN/
ZETA→0.80の23銘柄）。Software_Internet・Semiconductor該当銘柄
（10銘柄）およびticker_overrides銘柄（AMZN/GOOGL/MSFT/META/MRVL/CEG）
の計15銘柄と、元々どの分類にも該当しない残り47銘柄には差分が
発生していないことを確認した。pytest: 309 passed / 2 failed
（MSFT/NVDA、[[TEST-STALE-IV-1]]の既知バグで本修正とは無関係）。

**注意**: 今回の修正は`fcf_conversion_config.json`のキー名変更のみ。
影響を受ける38銘柄の`latest.json`/`report.txt`（conversion_rateが
反映されたIV）は未再生成であり、次回`pipeline.py`実行まで
生成済みデータとコードの間に不整合が残る（コミット・本番反映方針は
別途判断が必要）。

#### Software_Systemグループ分割 実装完了（2026-07-14）
残課題4（旧: `Software_System`統合カテゴリのAzure型想定レート0.80が
エンタープライズソフトウェア全般23銘柄に妥当か未検証）に対応するため、
23銘柄の実績データ（生FCF/調整済み純利益比率、直近5年）を検証した結果、
成熟ライセンス/プラットフォーム型（グループA、平均比率≈1.00）と
サブスクリプション型SaaS（グループB、平均比率≈1.61、NOWの一時的DTA
歪み除外後）の二極化を確認（相関検証・前受収益比率での分離可能性も
調査済み。分離精度は約78%）。

**実装内容:**
1. `fcf_conversion_config.json`に`Software_System_Mature`(1.00)・
   `Software_System_SaaS`(1.61)を新設。`Software_System`(0.80)キー自体は
   判定保留銘柄向けに残置（削除していない）
2. `config/beta_config.json`の18銘柄のsectorを更新:
   - グループA→`Software_System_Mature`: SNPS/ZETA/FICO/CDNS/APP/ADSK/
     PLTR/ADBE/INTU
   - グループB→`Software_System_SaaS`: BSY/DDOG/CWAN/CRM/FRSH/GTLB/
     FROG/NOW/ESTC
   - IOT（サンプル1件のみ）・QBTS/RBRK/S/SOUN（常時赤字で判定不能）・
     MSFT（ticker_override適用のため無関係）は`Software_System`のまま
     据え置き
3. `growth_sanity.py::SECTOR_TO_DAMODARAN`に新sector値2件を追加
   （両方とも既存と同じ"Software (System & Application)"を指す）。
   sectorリネームがgrowth_sanity側の成長率ベンチマーク参照
   （damodaran_industry）を壊さないための必須の付随対応
4. `calculator/adjustments.py::check_software_system_reclassification()`
   を新設。determine_fcf_base()と同じ設計思想（config書き換えなし、
   pipeline.py実行のたびに実績から純関数として再判定）で、実測FCF/
   調整済み純利益比率が現在のサブグループのレートから30%以上乖離、
   かつもう一方のレートの方が近い場合にこの実行に限り推奨レートへ
   差し替え、report.txtに見直し推奨を表示する
5. `beta_fetcher.py::classify_software_system_subgroup()`を新設
   （`--classify-software-system`オプション）。新規銘柄でsectorが
   `Software_System`（未分類）の場合、前受収益（Deferred Revenue/
   Contract Liability）/売上高比率（company_facts.jsonから算出）で
   0.40を閾値にMature/SaaSを暫定分類する。0.30〜0.50の境界近傍は
   report.txtに要確認フラグを表示
6. `CLAUDE_CODE_START.md`の新規銘柄登録手順にStep 2.5として追記

**検証:**
- 全105銘柄（tanuki=true 100銘柄）で新旧比較を実施し、意図した18銘柄
  （グループA9銘柄→1.00、グループB9銘柄→1.61）のみが変化し、
  IOT/QBTS/RBRK/S/SOUN/MSFTを含む残り82銘柄には差分がないことを確認
- pytest: 309 passed / 2 failed（MSFT/NVDA、[[TEST-STALE-IV-1]]の
  既知バグで本修正とは無関係）
- 影響18銘柄の`pipeline.py`再実行（`--skip-risk`）: 成功18/失敗0
- `report_consistency_check.py`: NG=0、警告36件は全て既存確認済み
  （新規0件）
- 自己補正チェック（`check_software_system_reclassification`）を
  18銘柄全件で検証し、いずれも見直し推奨が発火しないことを確認
  （実績データから直接分類した銘柄なので当然の結果。初期実装では
  現分類との乖離幅のみで判定しもう一方のレートとの近さを見ていなかった
  ため、ESTC（実測比率2.21、SaaS想定1.61からの乖離+37%）で
  「より遠いはずのMature(1.00)へ切替」という誤判定を検出・修正済み）

#### 発見した別問題（未対応・要別途調査）
本タスクの影響18銘柄再生成時、`FRSH`の内部検証（`validation.overall`）が
FAILになった。原因調査の結果、**本修正とは無関係の既存バグ**と判明:
`validator.py::run_basic_checks`の`pt_shares_consistency`チェックが
再計算する理論株価（例: FRSH $127.83、ADBE $1153.85）と、最終的に
`latest.json`へ保存される`intrinsic_value_per_share`（FRSH $41.47、
ADBE $639.89）が大きく乖離しており（ADBEは本修正前のHEAD時点データでも
乖離80.40%で再現、pass=False・overall=WARN）、pipeline.py内で検証時点の
IVスナップショットと最終保存IVの間に何らかの後段調整（alphaテーパリング等の
候補）が挟まっていると推測される。乖離幅が閾値（±1000%）を超えたのは
FRSHが初めてで、`report_consistency_check.py`のNG判定には含まれず
実害はNG=0のまま維持されているが、`validation.overall`の信頼性に
関わる別バグとして新規登録が必要（本タスクでは未調査・未修正）。

#### 残課題（クローズしない）
4. **IOT・QBTS/RBRK/S/SOUNの判定保留**: IOTはDR/Rev比率0.50で境界上
   （サンプル不足）、QBTS/RBRK/S/SOUNは観測期間中一貫して調整済み
   純利益が赤字のためMature/SaaS判定の前提が成立しない。いずれも
   `Software_System`(0.80)のまま据え置き
5. 前受収益比率による新規銘柄暫定判定の分離精度は約78%（実績検証済み
   18銘柄ベース）。ADSK/BSY/CWAN型（DR/Rev比率と実際のFCF転換挙動が
   逆相関する例外）が一定数存在するため、暫定判定はあくまで初期値
   であり、`check_software_system_reclassification()`による実績ベース
   の自動見直しに委ねる設計

**移設注記（2026-07-15）**: 上記のうち残課題2（固定比率という設計自体が
サイクル変動の大きい銘柄を表現できない構造的限界）・残課題3（EBIT(1-t)
ベース→純利益ベースの変換ロジックが存在しない）は[[TRUST-SUMMARY-EPIC-1]]
へ統合済み（詳細は同エントリ参照）。

残課題1（LITE/SITM型カテゴリ欠如）は調査の結果、SITMは既に解決済み
（beta_config.jsonのsector確定済み）、LITE単体の追加対応は残課題③と
同根の問題（EBIT(1-t)→純利益変換ロジック不在）のため見送り。加えて
調査中にLITE以外44銘柄（うち33銘柄がfcf_estimation.applied=Trueで
default(0.70)使用中）のsector未収録という同型の広範なギャップを新規発見し、
TRUST-SUMMARY-EPIC-1へ統合済み（詳細は同エントリ参照）。

このエントリには残課題4（IOT等判定保留）・残課題5（暫定判定精度78%）のみ
残置する。

#### 着手条件
**キー名不一致修正・Software_Systemグループ分割は完了済み（2026-07-14）**。
上記残課題4・5はいずれも着手条件なし（次回セッションで優先度・方針を
判断してから着手）。

---

## 優先度：中（こなれてきたら対応）

### [CASH-TAG-MISSING-1] tag_definitions.pyのCASH_AND_EQUIVALENTS候補リストにASU 2016-18対応タグが未登録で複数銘柄のcash_and_equivalentsが欠落
**優先度:** 中
**分類:** データ取得 / タグ定義
**登録日:** 2026-07-16
**発見:** FY52WEEK-BS-INSTANT-FACT-1調査時の副次発見

#### 問題
`tag_definitions.py`のTAG_CANDIDATES["CASH_AND_EQUIVALENTS"]に、
ASU 2016-18（制限付き現金を含むキャッシュフロー期首・期末残高調整表示
義務化）対応後に多くの企業が移行した
`CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`タグが
一度も追加されておらず、以下でcash_and_equivalentsが欠落している
（52/53週バグとは無関係と確認済み）:
- CAT: 2010-2019年（優先順位1位タグが同期間データを持たないため
  他候補にフォールバックせず欠落。`_extract_values_best_candidate`の
  単一勝者タグ設計の限界、LLY-CAPEX-STALE-1と同型）
- CPRT: 2020-2025年（候補リストに一切なし）
- ELF: 2014-2021年（候補リストに一切なし、2014-2015分は他候補にも
  該当なし）
- GEV: 全期間（候補リストに一切なし、CashAndCashEquivalentsAt
  CarryingValue自体が存在しない）
- HEI: 2023-2025年（候補リストに一切なし）

#### 対応方針
該当タグを候補リストに追加する。ただしこのタグは「制限付き現金」を
含む定義のため、単純追加すると純粋な現金同等物より過大計上になる
リスクがある点に注意。追加時は定義上の影響範囲（Net Debt計算等への
影響）を確認すること。

#### 着手条件
なし

---

### [MRVL-2019-2020-NULL-1] MRVLのannual_2019.json/annual_2020.jsonが両方ともrevenue/net_income=None
**優先度:** 中〜低
**分類:** データ品質 / SECデータ正規化
**登録日:** 2026-07-15
**発見:** [[FY52WEEK-BUCKET-MISPLACE-1]] IOT `_build_period_data`追加調査時の機械スキャン（副次発見）

#### 内容
MRVLの`annual_2019.json`・`annual_2020.json`が両方ともrevenue/net_income=None
であることを、隣接年度の完全重複を検出する機械スキャンで発見した。
`git log`で確認したところ、`annual_2019.json`の最終更新は2026-06-13時点
（ARCH-DATA-1-FYコミット`ab792d38b`＝2026-06-25より前）であり、
その時点で既に空だった。したがって[[FY52WEEK-BUCKET-MISPLACE-1]]で
特定した回帰バグ（determine_fiscal_year()導入コミットによる年度キー
シフト）とは無関係の別原因と判断される。

CLAUDE_CODE_START.mdの「調査中に発見した別バグの実装は別途依頼を待つ」
ルールに従い、その場での原因調査・修正は行わず、新規登録のみ実施。

#### 対応方針（未定）
原因調査は別途依頼が必要。MRVLの2019/2020年度revenue/net_income抽出元
タグの履歴（データ欠落かタグ不在か等）を確認するところから着手する。

#### 着手条件
なし

---

### [REVENUE-TAG-PRIORITY-FRAGILE-1] XBRL_MAPPING["revenue"]の候補優先順位が脆弱で誤った銘柄への波及リスクあり
**優先度:** 中〜低
**分類:** データ品質 / SECデータ正規化
**登録日:** 2026-07-15
**発見:** [[REVENUE-TAG-CONFLICT-SCAN-1]]のTDY・ASTS一次情報確認時

#### 内容
- **TDY**: タグ優先順位設計（`_extract_values_merged()`が`XBRL_MAPPING["revenue"]`
  の列挙順で先に処理されたタグを、tie-break規則の厳密な不等号により
  維持し続ける挙動）により、セグメント限定タグとみられる`Revenues`
  （2012年FY=$831.7M、公表連結売上高の約39%）が、正しい連結売上高
  `SalesRevenueNet`（同年$2,127.3M）より先に処理され誤って優先される
- **ASTS**: 提出元（ASTS自身）のXBRL入力ミス（FY2024の10-Kで
  `RevenueFromContractWithCustomerExcludingAssessedTax`にFY2022の値
  $13,825,000がそのまま複製されている）が原因だが、現状の採用値
  （`Revenues`=$4.4M、正しい）は「複数候補が同着の場合は処理順で
  先勝ち」という設計に偶然救われているだけで、頑健な仕組みによる
  ものではない。将来別銘柄で`Revenues`タグ自体に同種の提出ミスが
  発生した場合は、誤った値がそのまま採用されるリスクが残る

#### 対応方針（未定）
`XBRL_MAPPING["revenue"]`の候補優先順位（現状`Revenues`が最優先）の
妥当性を見直す必要がある。単純な列挙順ではなく、複数候補が同着の
場合に何らかの追加検証（例: 前年比の連続性チェック）を挟む設計が
考えられるが、詳細は未検討。[[FY52WEEK-BUCKET-MISPLACE-1]]とは
別種の欠陥（duration/年度バケツの問題ではなく、優先順位リストの
妥当性の問題）のため、区別して扱う。

#### 着手条件
なし

---

### [WORKFLOW-SEC-TANUKI-GAP-1] SEC_Data_UpdateとTANUKI_VALUATION_Updateの自動連携欠如
**優先度:** 中
**分類:** アーキテクチャ / GitHub Actions / 品質管理
**登録日:** 2026-07-13
**発見:** [[WARN12-COHR-ONDS-1]]実態調査時

#### 背景
`config/workflow_dependencies.json`は`TANUKI_VALUATION_Update`が
`SEC_Data_Update`に（HypeCore_Update/Adjusted_EPS_Update/Stonks_Silo_Update
経由で）依存すると論理的に定義しているが、これは実際のGitHub Actions
ワークフロートリガーとしては実装されていない（`workflow_run`等の連携なし。
admin.htmlの手動一括更新ボタン用のメタデータに留まる）。

実際のcronスケジュールは完全に独立している：
- `SEC_Data_Update.yml`: 毎週**日曜12:00 UTC**（=JST21:00）
- `TANUKI_VALUATION_Update.yml`: **平日**（月〜金）JST23:05のみ

このため、日曜のSEC自動更新完了から次のTANUKI VALUATION自動更新
（月曜23:05）までの**約26時間、SECデータは最新だがTANUKI VALUATIONの
latest.json/report.txtは陳腐化したまま**という状態が構造的・恒常的に
毎週発生しうる。[[WARN12-COHR-ONDS-1]]（COHR/ONDSのCash-STI期ズレ）は
この構造的ギャップが2026-07-12に顕在化した実例（コード修正ではなく
pipeline.py再実行のみで解消した）。

#### 対応方針（未確定・次回セッションで判断）
- 案①: `SEC_Data_Update`完了後に`TANUKI_VALUATION_Update`（および
  HypeCore_Update/Adjusted_EPS_Update/Stonks_Silo_Update）を`workflow_run`
  トリガーで自動連鎖させ、`config/workflow_dependencies.json`が定義する
  論理的依存関係を実際のCI構成に反映する
- 案②: 許容運用として現状維持する（日曜〜月曜のズレは
  report_consistency_check.pyのWARN検知で拾えており、実害は小さいため）
- 案①を採用する場合、既存の個別cronスケジュール（HypeCore週次・
  EPS Analyzer等）との統合方法・実行時間帯の見直しが必要になる可能性がある

#### 着手条件
なし（次回セッションで方針判断してから着手）

---

### [EPS-UPC-PREREORG-1] Up-C構造・組織再編前四半期のAdjusted EPS計算への算入方針
**優先度:** 中
**分類:** データ品質 / EPS ANALYZER / 設計方針
**登録日:** 2026-07-13
**発見:** [[ASTS-SHARES-OSCILLATION-1]]恒久修正時、BROS 2021-03-31の
復活データ妥当性確認調査

#### 背景
BROS（Dutch Bros、Up-C構造でIPO・組織再編は2021年9月）の2021-03-31
（Q1 2021、組織再編前）を一次情報（SEC EDGARライブ）で確認したところ、
以下の特異なパターンが判明した：
- **revenue**: $98,785,000（実在・妥当。FY2021通期$497,876,000から逆算した
  四半期進捗とも整合）
- **net_income**: 正確に`0`（端数なし）
- **調整項目**: `ShareBasedCompensation: $14,650,000`が存在

売上$98.8Mの実在企業がドル単位まで正確にゼロ利益、というのは通常の事業活動
としては不自然であり、**Up-C構造特有の会計処理の産物**と推測される：
組織再編（IPO）前は、SEC登録主体（PubCo）が事業会社（OpCo）の経済的持分を
まだ保有していないため、OpCoの実際の売上・損益とは無関係に、PubCo単体の
帰属純利益が形式的に$0となる。

[[ASTS-SHARES-OSCILLATION-1]]の恒久修正（隣接四半期からの株数引き継ぎ）に
より、この四半期の希薄化後株数が新たに埋まるようになった結果、
`adjusted_net_income = gaap_net_income(0) + 税引後SBC加算 ≈ プラスの値`と
なり、**PubCoの帰属利益が実質ゼロだった四半期に対して、見かけ上プラスの
Adjusted EPSが新たに算出される**ようになった。株数の引き継ぎ自体（実データに
基づく合理的な近似）は妥当だが、この四半期をAdjusted EPS計算にそのまま
含めてよいかは、今回の株数バグ修正とは別軸の設計論点である。

#### 対応方針（未確定・次回セッションで判断）
- Up-C組織再編前かつnet_income=0（または売上に対して不自然に小さい）四半期を
  機械的に検知し、Adjusted EPS計算から除外する、または「参考値」として
  別枠表示するかを検討する
- 「net_income=0だが売上は実在」というパターン自体を検知条件として使えるか
  （閾値・誤検知率を含めて設計）
- 他のUp-C構造銘柄（CART等、組織再編を経て上場した銘柄）で同型のケースが
  ないか横展開確認する（[[ASTS-SHARES-OSCILLATION-1]]の新旧比較でCARTも
  値変化が確認されている。組織再編前四半期を含むかどうかの個別確認が必要）

#### 着手条件
なし（次回セッションで検知方法・対応方針を設計してから着手）

---

### [GATE2-PHASE3B-1] Gate2 Phase 3b: 独立実装4ファイルのreader.py統合・規約C/Dの型化
**優先度:** 中
**分類:** アーキテクチャ / SECデータ取得層 / QUALITY-GATES-EPIC-1関連
**登録日:** 2026-07-13
**発見:** Gate2設計材料収集調査（①〜④）・Phase 3a実装時

#### 背景
Gate2設計材料収集調査で、以下2点がPhase 3a（正規化契約の型導入・完了）の
スコープ外として意図的に見送られた。

**① 独立実装4ファイルのreader.py統合**: ✅ **2026-07-17完了**（詳細は下記
「①4ファイル統合完了」参照）。`financial_trend_calculator.py`
（STONKS SILO）・`quarterly_review_generator.py`（TAIL）・`tail_dcf_bridge.py`
（TAIL）・`hypecore.py`が、共有アクセサ（reader.py/TTMReader）を経由せず
「is_annual=False かつ is_ytd=False の最新エントリを取る」ロジックをそれぞれ
独立に再実装していた（`_latest_q()`・`_lq()`等、名前も実装も微妙に異なる）。
型を導入しても、この4ファイルが辞書アクセス前提のままでは規約C/Dの効果が
及ばない。

**② 規約C（フィールド分類の二重管理）**: ✅ **2026-07-17完了**（詳細は下記
「②規約C完了」参照）。`ttm_calculator.py`の
`FLOW_FIELDS`/`STOCK_FIELDS`/`SHARES_FIELDS`が`quarterly.py::FIELD_CONCEPTS`とは
別ファイルで独立管理されており、新フィールド追加時にいずれかへの追加を
忘れてもエラーにならず黙って出力から消える。実例として`CurrentAssets`/
`CurrentLiabilities`（quarterly.pyでは「シガーバット検出用」とコメントされて
いる）が、現在これを消費するコードが皆無であることを確認済み（抽出されて
いるがTTM層で分類漏れのまま出力対象外になっている状態）。

**③ 規約D（enum風文字列の型化）**: `growth_sanity.py`の`verdict`
（PLAUSIBLE/REVIEW/AGGRESSIVE/FLOOR_HIT_REVIEW）・`pipeline.py`の`Classification`
（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）はいずれも生文字列の代入
（例: `verdict = "PLAUSIBLE"`）。タイプミスがあっても実行時エラーにならず、
静かに「未知の分類」として扱われる。**③-a（verdict）は✅2026-07-17完了**
（詳細は下記「③-a規約D完了」参照）。**③-b（Classification）は引き続き未着手**
（pipeline.py内14箇所・分岐条件としての比較を含み、③-aより影響範囲が大きい）。

#### 対応方針（未確定・次回セッションで判断）
- ①はttm_calculator.py（Phase 3aでは対象外だったファイル）を巻き込む改修に
  なるため、規模を見積もった上で着手要否を判断する
- ②③はPhase 3aで新設した`common/sec_data/contracts.py`に型を追加する形で
  実装できる見込みだが、`growth_sanity.py`/`pipeline.py`側の代入箇所を
  型に置き換える改修が伴うため影響範囲の洗い出しが必要

#### 着手条件
なし（次回セッションで規模見積もり・優先順位判断してから着手）。
**③-b（Classification型化）は引き続き未着手のまま残っている**
（①4ファイル統合・②規約C・③-a規約D〈verdict〉は2026-07-17完了）。

#### ②規約C完了（2026-07-17）

`ttm_calculator.py::STOCK_FIELDS`に`CurrentAssets`/`CurrentLiabilities`を追加し、
`_COGS`/`RPO`用の`EXCLUDED_FIELDS`を新設。`contracts.py::validate_field_classification()`
を新設し、`quarterly.py::FIELD_CONCEPTS`の全キーがFLOW/STOCK/SHARES/EXCLUDEDの
いずれかに属することをモジュールロード時に検証する契約チェックを追加した
（新フィールド追加時の分類漏れをimport時点で即座に検知）。

**循環import対応**: `contracts.py`は既に`quarterly.py`からimportされているため、
`contracts.py`側が`quarterly.py`/`ttm_calculator.py`を逆にimportすると循環import
になることを確認。汎用チェック関数`validate_field_classification()`は
`contracts.py`に置きつつ、具体的なフィールド集合（`FIELD_CONCEPTS`・
`FLOW_FIELDS`等）の受け渡しは呼び出し元（`ttm_calculator.py`）が担う設計
にして回避した（`contracts.py`はどちらもimportしない）。

**既存テストへの副次修正**: `ttm_calculator.py`がモジュールとして
`quarterly.py`/`contracts.py`をimportするようになった結果、パッケージ構造を
経由しない「ファイルパス直接ロード」（`tests/test_ttm_calculator.py`の
`sys.path.insert`方式・`tests/test_pipeline_logic.py`の
`importlib.util.spec_from_file_location`方式）が相対importエラーで壊れることが
判明し、他8ファイルと同じ`from common.sec_data.xxx import ...`のパッケージ
形式に統一して解消した。

**検証結果の読み替え（重要）**: 実装過程の検証で、①のSTOCK_FIELDS追加が
本番の`_ttm_series.json`（update.pyが実際に呼ぶ`calc_ttm_series()`の出力）
には一切反映されないことが判明した。追加調査の結果、これは
CurrentAssets/CurrentLiabilities固有の問題ではなく、**STOCK_FIELDS/
SHARES_FIELDS分類全体が構造的に本番未到達**（8メンバー中5件は完全に
デッド、残り3件は分類を経由しない別実装で個別に生存）という、より広い
構造的問題であり、根本原因は`calc_ttm()`（2026-05-07〜05-11の
`calc_ttm_series()`移行期の廃止漏れコード、本番からは到達不能）と判明した。
この構造的問題は②のスコープでは解消せず、[[TTM-STOCK-FIELDS-DEAD-1]]として
新規分離登録した（詳細は同エントリ参照）。

②の検証手順は「本番の`_ttm_series.json`への反映」ではなく「`ttm_calculator.py`
内の分類（STOCK_FIELDS）に正しく追加され、契約チェックがFIELD_CONCEPTS
全キーの分類網羅性を検証できる状態になったこと」に読み替えて完了とした
（全105銘柄でのデータ再生成は本番出力に変化がないため実施していない）。

**検証結果:**
- pytest 345 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く。新規17件
  〈`tests/test_contracts.py`5件・`tests/test_ttm_calculator.py`3件、他は
  既存テストの相対import修正〉を含む）
- report_consistency_check.py: NG=0/WARN=51（本セッションでは本番データ・
  latest.json/report.txtへの変更を一切行っていないため、ステージ3完了時点
  から不変）

#### ③-a規約D完了（2026-07-17・verdictのEnum化）

`common/sec_data/contracts.py`に`GrowthVerdict(str, Enum)`
（PLAUSIBLE/REVIEW/AGGRESSIVE/FLOOR_HIT_REVIEW）を新設し、
`growth_sanity.py::check_growth_sanity()`の`verdict`代入6箇所
（デフォルト値・4箇所の代入・戻り値dict格納）を生文字列から
`GrowthVerdict.XXX`（Enumメンバー参照）に置き換えた。

**実装時に発覚した罠（重要）**: Python 3.11以降、`Enum`の`__str__`/
`__format__`は「`str, Enum`を継承していても」デフォルトで
`GrowthVerdict.PLAUSIBLE`というクラス名付き表記を返す仕様に変わっている
（3.10以前は素の文字列を返していたが3.11で仕様変更）。そのため
f-string補間（`f"{verdict}"`）やstr()は、`__str__`をオーバーライドしない
限り事前の想定（str継承なので.value不要で動作する）通りには動かない
ことが実装検証で判明した（`==`比較・JSON出力〈json.dump〉はstr継承のため
元々問題なし）。`GrowthVerdict`に`__str__`をoverrideして`self.value`を
返すようにし、f-string補間を含めた全ての既存コード（`growth_sanity.py`の
戻り値dict格納・`pipeline.py`のreport.txt生成`f"判定 : {gs_verdict}"`）が
`.value`付与なしに意図通り動作するようにした（`enum.StrEnum`は
Python 3.11+限定でpyproject.tomlの`requires-python=">=3.10"`と整合しない
ため不採用、`__str__`override方式で3.10以降のどのバージョンでも同じ
挙動になるようにした）。

**検証結果:**
- pytest 351 passed（既知2件除く、新規6件〈`tests/test_contracts.py`の
  `TestGrowthVerdict`〉を含む。既存の`tests/test_pipeline_logic.py`の
  verdict `==`比較テスト2件は無改修でpass）
- report_consistency_check.py: NG=0/WARN=51（不変）
- 実データでの目視確認: growth_sanity判定がREVIEW（ABBV）・
  AGGRESSIVE（CWAN）・FLOOR_HIT_REVIEW（MO）の3銘柄でpipeline.pyを
  再実行し、report.txtの「判定」行・latest.jsonの`verdict`フィールドが
  Enum化前後で完全に同一（`GrowthVerdict.XXX`ではなく素の文字列のまま）
  であることを確認。stock.htmlはJSON経由で文字列を受け取るのみのため
  無改修で動作（latest.jsonの値が不変のため表示も不変と判断）。
  検証用に再生成した3銘柄のデータは本番反映せず元に戻した
  （市場データの日次変動のみが差分となり、verdict関連の差分はゼロだったため）

#### ①4ファイル統合完了（2026-07-17）

`common/sec_data/reader.py`にモジュールレベルの汎用アクセサ
`get_quarterly_series(normalized, field_name)`（is_annual・is_ytd両方を
除外した四半期エントリをend日昇順で返す）と`get_latest_quarterly(normalized,
field_name)`（その最新1件、空ならNone）を新設。戻り値は素の辞書のまま
（dataclass化は今回スコープ外・見送り）。

`get_rpo_context()`内の既存`_q_sorted()`（is_annualのみ除外・is_ytdは
除外していなかった）を`get_quarterly_series()`呼び出しに置き換え。
これは意図した挙動変化（is_ytdエントリの除外を追加）だが、現在のRPO関連
データにはis_ytd=Trueの実データがほとんど存在しないため無害であることを
実データ5銘柄（CRM/NOW/GTLB/RPD/DDOG）でのネットワーク未使用の新旧比較で
確認した（差分0件）。

4ファイルそれぞれの独自実装を新規アクセサに置き換えた:
- **quarterly_review_generator.py**: `_latest_q()`を削除しget_latest_quarterlyに、
  インライン重複2箇所（rev_qs・oi_map）をget_quarterly_seriesに置き換え
- **tail_dcf_bridge.py**: `_lq()`を削除しget_latest_quarterlyに置き換え
  （quarterly_review_generator.pyとのコピペ重複を解消）
- **financial_trend_calculator.py**: `_get_quarterly_entries()`の内部実装を
  get_quarterly_series呼び出し＋既存の`_build_q4_implied()`（このファイル
  固有のQ4逆算ロジックのためreader.py側へは移動せずローカルに残置）の
  組み合わせに変更。呼び出し箇所2箇所は関数シグネチャ不変のため無改修
- **hypecore.py**: `extract()`の内部実装をget_quarterly_series呼び出し結果
  をpandas Seriesに変換する形に変更（pandas変換ロジックはhypecore.py側に
  残置、reader.py側にpandas依存を持ち込まない設計を維持）。呼び出し箇所
  3箇所は関数シグネチャ不変のため無改修

**検証結果:**
- `tests/test_gate2_phase3b1_reader_integration.py`新設（14件）:
  get_quarterly_series/get_latest_quarterlyの単体テスト（is_annual・
  is_ytd除外、空リスト時のNone返却、end日ソート順）、get_rpo_context移行後
  の挙動確認、4ファイルそれぞれの移行前後の回帰テスト（is_ytd除外・
  Q4 implied構築・最新四半期選択が合成フィクスチャで期待通りに動作する
  ことを確認）
- pytest 387 passed（既知2件MSFT/NVDA・TEST-STALE-IV-1除く。新規14件を含む）
- report_consistency_check.py: NG=0/WARN=51（本タスクでは本番データへの
  変更を一切行っていないため③-a完了時点から不変）
- ネットワーク未使用の新旧比較（実データ）: get_rpo_context（5銘柄）・
  financial_trend_calculator.\_get_quarterly_entries（3銘柄×5フィールド、
  Revenue/GrossProfit/OperatingIncome/NetIncome/OCFの全時系列）・
  tail_dcf_bridge.\_load_layer1_financials（3銘柄）・
  quarterly_review_generator.load_layer1_financials（3銘柄）・
  hypecore.fetch_quarterly_fundamentals（3銘柄、DataFrame全体を
  `.equals()`で比較、YoY/QoQ/TTM rollingを含む時系列全体が対象）で
  移行前後の出力が完全一致することを確認。検証用に生成した一時ファイルは
  すべて削除済み（本番データへの反映なし）

---

### [GATE2-READER-FCFLIST-1] reader.py::get_fcf_list()のfcf_list順序規約が未検証のまま残存
**優先度:** 中
**分類:** アーキテクチャ / SECデータ取得層 / QUALITY-GATES-EPIC-1関連
**登録日:** 2026-07-13
**発見:** Gate2 Phase 3a実装時

#### 背景
Phase 3aで新設した`FCFSeries`（fcf_listの新しい順規約をconstruction時に検証する
ラッパー）は、`data_fetcher.py::TTMReader.get_fcf_series()`（TTM系列ベースの
fcf_list生成箇所）にのみ適用した。もう一方のfcf_list生成経路である
`common/sec_data/reader.py::get_fcf_list()`（年次実績ベース、TTM系列が使えない
銘柄・TTM点数不足銘柄のフォールバックとして`_select_fcf_source()`経由で
採用されうる）は、`get_annual_range()`が返す年次データから`free_cash_flow`の
値だけを抽出して素の`List[float]`として返しており、抽出した時点で各値の
年度・end日情報が失われるため、Phase 3aのスコープ（normalizer.py/
quarterly.py/data_fetcher.py）のままでは順序検証を後付けできない。

現状、`get_annual_range()`はファイル名の降順ソート（`annual_2025.json`→
`annual_2024.json`→...）に依存して新しい順を実現しており、この規約自体も
型で保証されていない。

#### 対応方針（未確定・次回セッションで判断）
- `get_fcf_list()`自体を対象ファイルに含め、`get_annual_range()`が返す
  年次データの`period`（年度）情報を保持したまま`FCFSeries`を構築するよう
  改修する
- reader.pyはPhase 3aの当初スコープに含まれていなかったため、他の
  reader.pyメソッド（get_roe_avg_detail等）への影響有無も含めて次回
  セッションで規模を見積もる

#### 着手条件
なし（次回セッションで規模見積もり・優先順位判断してから着手）

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
  （[[TAG-DEFS-UNIFY-1]]（完了・BACKLOG_DONE.md参照）で統合済みの9概念、
  LTDebt・RPOは時点データのため対象外）

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

#### 議論の要旨（2026-07-14追記・タスクの本質的なゴールの整理）
本日の一連の調査（DCF計算可否ロジック確認・Policy A/B判定ロジックの網羅調査・
AVAV/RDW/LITE/SITM個別調査）を経て、本タスクの本質的なゴールは
「stonks_silo判定基準を確定させること」単体ではなく、**「TANUKI VALUATION・
STONKS SILOのどちらの評価軸でも適切に評価しにくい銘柄をどう判定・振り分ける
か」**という、より広い問いであると整理された。

根拠：
- GTLB/ESTC/LITEの逸脱事例は、既存のDCF_Reliability判定（Policy A/B）を
  そのまま機械基準に転用しても再現できないことが判明した（[[POLICY-AB-
  TREND-BLIND-1]]で確認したPolicy Bの設計限界が一因）
- APGE（プレレベニュー）のような「赤字」以外の軸で評価不適合になる
  パターンが存在し、stonks_silo単独の基準では収まらない
- LITE/SITMの調査で判明したFCF推定ロジックの限界（[[SECTOR-FCF-RATE-
  BROKEN-1]]・[[FCF-CONVRATE-DESIGN-LIMIT-1]]）も、根本的には「TANUKI
  VALUATIONのDCFフレームワークが不得意とする事業特性の銘柄をどう扱うか」
  という同根の問題

**注意：上記は議論の要旨・方向性の整理であり、基準案の具体的な数値
（N年赤字継続のN等）やフラグ再判定の実装方針は本日時点でも未確定のまま。**
上記「対応方針（未確定）」の内容と矛盾するものではなく、着手時に
判断材料として踏まえるべき文脈を追記したもの。

#### 着手条件
なし（基準案の確認・確定後に着手）

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

#### 設計メモ追記（2026-07-15・ARCH-DATA-1残課題③調査結果を反映）
「ARCH-DATA-1のパターン判定ロジックを共有する」方針を見直した。調査の
結果、SIC/formerNamesベースの事前推測（新規登録時点の情報のみでの
判定）は精度未検証のリスクが高いと判明した：submissions APIの
`sic`/`formerNames`は「リスクフラグ立て」までは可能でも、実際に
どのXBRLタグが正しいかの確定判定にはXBRL取得後の実データ比較が必須
であり（SOFI/IONQの過去の対応も、人間が10-K相当の文脈情報で正誤判断
した一回限りの手動オーバーライドだった）、登録前段階の統計的推測だけで
共有カタログを構築するのは時期尚早と判断した。

revenue系タグ競合（SEC-REV-FINTECH-1/BUG-REV-SPAC-1型）については、
登録時点（本タスクが想定するタイミング）ではなく**Step1（SECデータ
取得）完了後の実データ検知**に統合する方針とした。実装は
`common/sec_data/revenue_tag_conflict_check.py`（ARCH-DATA-1残課題③で
新設、`update.py`の4c.相当に配線済み）で、`update.py`実行時に自動的に
WARN表示される。したがって本タスク（PREFLIGHT-CHECK-1、Step1**前**の
事前警告）のスコープからはrevenue系タグ競合を除外し、当初の3項目
（①上場後3年未満 ②直近フォームが20-F等 ③revenueタグ不存在、いずれも
登録時点の情報のみで判定可能）に限定する。本タスク自体は依然未着手。

---

## 優先度：低（アイデア段階）

### [CLAUDE-CODE-START-FY-DESC-FIX-1] CLAUDE_CODE_START.mdのdetermine_fiscal_year()呼び出し箇所記述の修正
**優先度:** 低
**分類:** 保守 / ドキュメント
**登録日:** 2026-07-15
**発見:** [[FY52WEEK-BUCKET-MISPLACE-1]]根本修正設計のための事前調査時

#### 問題
CLAUDE_CODE_START.mdの「年度判定は`common/sec_data/utils.py`の
`determine_fiscal_year()`に統一済み（ARCH-DATA-1-FY 2026-06-25完了）:
parser.py・extract_key_facts.py・aggregate_annualの3箇所が同関数を参照」
という記述が不正確と判明した。

実際に`determine_fiscal_year()`を直接呼び出しているのは`parser.py`
（2箇所: 341行目・469行目、年次10-Kエントリの分類）と
`extract_key_facts.py`（4箇所: 549・590・613・668行目、四半期エントリの
(fiscal_year, quarter)分類およびQ4逆算時の年次エントリマッチング）の
2ファイル6箇所のみ。`aggregate_annual`（adjusted_eps_analyzer/pipeline.py:306）
は本関数を呼ばず、extract_key_facts.pyが設定済みのfiscal_yearフィールドで
単純にグループ化するのみの間接消費箇所であり、独立した呼び出し箇所ではない。

#### 対応方針
CLAUDE_CODE_START.mdの当該記述を「parser.py（2箇所）とextract_key_facts.py
（4箇所）が直接呼び出し、aggregate_annualはextract_key_facts.pyが設定した
fiscal_yearフィールドを間接的に消費する」旨に修正する。

#### 着手条件
なし（軽微な文書修正のため優先度低）

---

### [QUALITY-CHECKER-CLEANUP-1] 未使用のquality_checker.py削除要否判断
**優先度:** 低
**分類:** 保守 / SECデータ取得層
**登録日:** 2026-07-15
**発見:** [[ARCH-DATA-1]]残課題③調査時

#### 問題
`common/sec_data/quality_checker.py`（独自のQ01〜Q13チェックカタログ、
独自の`TICKER_RESTRICTIONS`定義を保持）が、全リポジトリを検索した結果
どこからもimportされていない未使用コードと判明した。同ファイル内の
`TICKER_RESTRICTIONS`はコメント上「quarterly.pyと同期」とあるが実態は
非同期で、SOFI・IONQのエントリ（quarterly.py側には存在）を欠いている。

`report_consistency_check.py`（CHECK-N命名）・`quality_checker.py`
（Q0N命名）・`registration_validator.py`（P1-xxx命名）と、既に3種類の
独立したチェックカタログ・命名規則が併存しており、本ファイルは実質的に
その一つが死蔵された状態。

#### 対応方針（未確定）
- 一度も呼ばれていないことを再確認できれば削除する
- 何らかの理由で将来利用予定がある場合は、`TICKER_RESTRICTIONS`を
  quarterly.py側と同期させるか、共有カタログへの統合を検討する

#### 着手条件
なし

---

### [PHASE1-SCAN-CLEANUP-1] phase1_scan.pyの陳腐化確認・削除要否判断
**優先度:** 低
**分類:** 保守 / SECデータ取得層
**登録日:** 2026-07-13
**発見:** [[TICKER-DIRECT-ACCESS-GUARD-1]]実装時の全リポジトリスキャン

#### 問題
`common/sec_data/phase1_scan.py`が`os.listdir(DATA)`で
`docs/value-monitor/tanuki_valuation/data/`を無条件スキャンし、tanukiフラグを
見ずに全ディレクトリを対象銘柄として扱う。ハードコードされた
`TODAY = date(2026, 6, 11)`から、2026-06-11頃に使われた一回限りの診断
スクリプトと推測される。CIワークフロー・他スクリプトからの参照なし
（grep全数確認済み）。

#### 対応方針（未確定）
- 一回限りの診断スクリプトであることを確認できれば削除する
- 継続利用の可能性がある場合は`tickers.get_tanuki_tickers()`経由に修正する

#### 着手条件
なし

---

### [BACKFILL-HISTORY-CLEANUP-1] backfill_history.pyの陳腐化確認・削除要否判断
**優先度:** 低
**分類:** 保守 / TANUKI VALUATION
**登録日:** 2026-07-13
**発見:** [[TICKER-DIRECT-ACCESS-GUARD-1]]実装時の全リポジトリスキャン

#### 問題
`src/value/tanuki_valuation/backfill_history.py`が`os.listdir(DATA_ROOT)`で
無条件スキャンし、tanukiフラグを見ない。ファイル内コメント
「May 14-16 History Backfill (v8.2)」から特定日付向けの一回限りの
バックフィルスクリプトと推測される。

#### 対応方針（未確定）
- 一回限りのバックフィルスクリプトであることを確認できれば削除する
- 継続利用の可能性がある場合は`tickers.get_tanuki_tickers()`経由に修正する

#### 着手条件
なし

---

### [SYSHEALTH-CIK-DEDUP-1] system_health.pyの独自CSVパースをtickers.get_all_tickers()に統一
**優先度:** 低
**分類:** 保守 / 品質管理
**登録日:** 2026-07-13
**発見:** [[TICKER-DIRECT-ACCESS-GUARD-1]]実装時の全リポジトリスキャン

#### 問題
`common/system_health.py::check_h_config()`が、segment/maturity configの
孤立エントリ検出のため`all_tickers`（フラグ無視の全登録銘柄）を
`csv.DictReader`で独自にパースしている。同一の全銘柄取得は
`tickers.get_all_tickers()`が既に提供しており、置換可能（バグではなく
コード重複の解消のみ）。

#### 対応方針
`all_tickers = {r["ticker"] for r in rows}`を
`tickers.get_all_tickers()`ベースに置換する。挙動が完全に同一であることを
確認してから着手する。

#### 着手条件
なし

---

### [TAIL-CIK-LOOKUP-DEDUP-1] TANUKI TAIL 3スクリプトのload_cik(ticker)重複実装の統合
**優先度:** 低
**分類:** 保守 / TANUKI TAIL
**登録日:** 2026-07-13
**発見:** [[TICKER-DIRECT-ACCESS-GUARD-1]]実装時の全リポジトリスキャン

#### 問題
`src/tail/kpi_proposer.py`・`src/tail/sec_ctrl_fetcher.py`・
`src/tail/text_kpi_extractor.py`の3ファイルが、`load_cik(ticker)`
（cik_lookup.csvから指定ティッカーのCIKを検索して返す関数）を
それぞれ独立に実装している（関数名・実装内容ともほぼ同一）。
FLAG-CONSUMER-AUDIT-2/3のようなフラグバイパスバグ型ではなく、単純な
DRY違反（3箇所の重複実装）。

#### 対応方針
共有ヘルパー（例: `common/sec_data/tickers.py`または`config.py`への
`get_cik(ticker)`追加）に統合し、3ファイルから呼び出す形に変更する。

#### 着手条件
なし

---

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

#### 追記（[[VALIDATOR-IVPS-MISMATCH-1]]対応時の発見、2026-07-15）
本テストの失敗原因は、VALIDATOR-IVPS-MISMATCH-1で修正したvalidator.pyと
同じ、ALPHA-REDESIGN-1（alpha乗算廃止）に追随していない廃止済みP_t式
（× (1+alpha)）を使用していることが根本原因と判明。validator.py本体は
既に修正済みだが、本テストファイル自体の式は未修正のまま残っている。

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

### [POLICY-AB-TREND-BLIND-1] Policy A/B判定ロジックが直近トレンド好転を検知できず、健全企業を恒常的にLOW判定
**優先度:** 低（2026-07-14 高→低に変更。理由は下記参照）
**分類:** DCF信頼性判定ロジック / バグ
**登録日:** 2026-07-14
**発見:** [[FLAG-THRESHOLD-DESIGN-1]]検討過程の調査（tanuki=true・DCF_Reliability=LOW
23銘柄の原因分類調査）

#### 優先度変更の理由（2026-07-14）
WATCH等のラベルはDCF数値自体には影響せず、他AI/外部評価者への見え方を
緩和する程度の実利用価値のため、優先度を高→低に変更した。ただし対応自体は
取り下げない。修正方針〈直近2年連続黒字を主基準に上方乖離をLOW対象から
除外〉は既に確定済みのため、後日着手時にそのまま使用可能。

#### 内容
tanuki=true・DCF_Reliability=LOW判定の23銘柄を精査した結果、うち8銘柄
（CWAN, ESTC, FROG, IOT, NET, RBRK, ZETA, S）はFCF実績がいずれも黒字化・
拡大という健全な業績改善を示しているにもかかわらず、恒常的にLOW判定に
なっていることが判明した。データ・事業実態には問題がなく、判定ロジック
自体の設計特性に起因する：
- Policy A（`_calc_dcf_reliability_policy_a`等）が5年平均FCFを基準にする
  ため、過去の大幅赤字が牽引して現在の黒字転換を反映できない
  （例: S＝SentinelOneは直近2年連続黒字転換にもかかわらずPolicy A発火）
- Policy B（`_calc_dcf_reliability_policy_b`、pipeline.py:335-381）は
  FCF-OUTLIER-1ルール（CLAUDE_CODE_START.md記載: 上方乖離時は一過性費用が
  検出されてもaction=excludedにしない設計）により、黒字転換・好転による
  乖離も恒久的に「未解決の外れ値」としてLOW判定し続ける

続く網羅調査（2026-07-14 同日2回目）で、tanuki=true全100銘柄中70銘柄
（70%）がDCF_Reliability=LOWであり、うち50銘柄（AAPL/TSLA/PLTR/CRM/ADBE/
AVGO/INTU/KO/LLY/PEP/NOW等の主力銘柄含む）がPolicy Bの上方乖離
（latest_fcf>fcf_5yr_avg）起因と判明。修正方針は「直近2年連続黒字
（`fcf_2yr_avg>0`）を主基準に上方乖離をLOW対象から除外」で確定済み
（実データ検証で50銘柄中48銘柄を安全に救済できることを確認）。

関連: [[TRUST-SUMMARY-EPIC-1]]（段階2＝FCF/DCF計算の「解消可能バグ vs
構造的限界」切り分けを扱うEPIC。本件はその棚卸し対象の具体事例）

#### 影響範囲
tanuki=true全100銘柄中70銘柄（DCF_Reliability=LOW）。うちPolicy A起因14
銘柄（trend-blindはS 1銘柄のみ）、Policy B eps_invalid起因4銘柄（AMZN,
LITE, SITM, SPIR）、Policy B上方乖離起因50銘柄（AAPL, ADBE, ADSK, ALAB,
AMD, APP, AVGO, BROS, CAKE, CEG, CELH, CPRT, CRM, CWAN, DDOG, DELL, DOCN,
ELF, ENTG, ESTC, FCX, FICO, FLYW, FROG, FRSH, GEV, GTLB, HEI, HQY, HWM,
INTU, IOT, KO, LLY, LOAR, LRCX, LYFT, MRVL, NET, NOW, PAYS, PEP, PLTR,
RBRK, RMBS, SCCO, SNPS, TSLA, VRT, ZETA）、Policy B下方乖離/継続赤字
（正当な懸念）2銘柄（SOFI, XOM）。ただし影響はClassification表示の
WATCH丸めに限られ、IV・upside等のDCF計算値自体は変更されない。

#### 着手条件
なし（修正方針の設計から着手可能。優先度：低のため次回以降の余力時対応）

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

### [ALPHA-CAP-HARDCODE-1] validator.pyのalpha_capハードコードとcore_calculator.pyの動的alpha上限の不一致
**優先度:** 低（2026-07-15調査完了・未定から確定）
**分類:** DCF信頼性判定ロジック / データ品質
**登録日:** 2026-07-15
**発見:** [[VALIDATOR-IVPS-MISMATCH-1]]対応時のスポットライト銘柄検証（ADBE等）で発見

#### 内容
`validator.py::_extract_params`が`alpha_cap = 1.0`を全銘柄一律ハードコード
しているが、`core_calculator.py`は業種別に動的なalpha上限（例: 0.8等）を
適用しており不一致。この不整合が`formula_verification`チェックの誤FAILの
原因になっており、VALIDATOR-IVPS-MISMATCH-1修正後も残るWARN 30件全ての
原因であることを確認済み（ADBEで実装変更前から同一事象を確認、既存バグ）。

#### 影響範囲調査の結果（2026-07-15完了）
- **実害はなし**。formula_verificationがWARNになっている30銘柄全件を確認し、
  実際に保存されている`alpha`値はcore_calculator.pyの業種別/セクター別
  上限と全銘柄で完全一致することを確認済み（core_calculator.py側の計算
  自体は正しい）。IV計算そのものには影響せず、`validator.py`の
  `formula_verification`チェックの誤警告表示（実害のない表示バグ）に
  限定される。ALPHA-REDESIGN-1によりP_t/intrinsic_value_per_shareの実計算は
  常にalpha非乗算のため、仮にvalidator.py側の誤ったcap(1.0)を実計算に
  適用したとしても理論株価への影響はゼロ。
- **原因**: core_calculator.pyの動的alpha_cap判定（優先順位: mega_tech
  ticker → 業種（`_industry_alpha_caps`） → セクター（`_alpha_caps`） →
  デフォルト1.0、`config/maturity_config.json`参照）に対応する統一
  アクセサが`maturity_config.py`（同JSONを専用にラップする既存モジュール、
  `get_terminal_growth()`等を提供）に存在しない（`get_alpha_cap()`相当が
  未実装）ことが構造的な一因。core_calculator.py自身もこのモジュールを
  経由せず、`calculate_pt()`呼び出しの都度JSONを生読み込みしている。

#### 着手条件
なし（実害なしのため優先度は低。着手する場合は`maturity_config.py`への
`get_alpha_cap()`相当の統一アクセサ追加とvalidator.py側の参照切り替えが
対応の骨子になると見込まれる）

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

※ 2026-07-12: TICKER-SOURCE-UNIFY-1対応方針1〜3を完了しBACKLOG_DONE.mdへ
  全文移動。QUALITY-GATES-EPIC-1（バグ根絶に向けた5段階品質ゲート）を
  優先度：最高で新規登録し、Phase 1（BACKLOG重複統合・pytest全体実行化・
  WARN台帳導入）・Phase 2a（タグフォールバック選定ロジック統一、
  common/sec_data/tag_definitions.py新設）・Phase 2b-1（TTM鮮度チェック）・
  Phase 2b-2（段差型急変検知統合）・Phase 2b-3（EPS Analyzer fact選定ロジック
  統一）を同日中に完了。副産物としてSEC-TAG-FICO-CPRT-1・LLY-CAPEX-STALE-1・
  GROWTH-CAGR-SIGN-1（CAGR計算式符号反転バグ）・TTM-QUARTERS-CHECK-1・
  SPLIT-AUTO-CHECK-1等の個別バグを多数発見・修正。HYPECORE-SAVE-INDEX-
  NAMEERROR-1（3日間沈黙していた本番障害）を緊急対応で完了。詳細は
  BACKLOG_DONE.md「2026-07-12（完了）」セクション参照。
※ 2026-07-13: ARCH-DATA-1の棚卸し調査を実施し、QUALITY-GATES-EPIC-1の
  ゲート1/ゲート2への統合マッピングを確認。Phase 3前提整理として
  [[ARCH-DATA-1-PREP-1]]（TAG-DEFS-UNIFY-1クローズ・SOFI-DATA-1のLTDebt
  恒久修正〈2026-06-24の手動パッチが自動再生成で巻き戻っていたことを発見〉・
  audit.py UP-C検知・バグA/Bスコープ判断〈既に解消済みと判明〉）を完了。
  続けてPhase 3a（Gate2本体第一段階: `common/sec_data/contracts.py`新設。
  FinancialEntry/EntryProvenance/FCFSeriesで規約A・B・③を型化し、
  quarterly.py/normalizer.py/data_fetcher.pyに検証を配線）を完了。
  全105銘柄で新旧比較し値の差分0件を確認済み。詳細はBACKLOG_DONE.md
  「2026-07-13（完了）」セクション参照。
  ~~次セッションの候補: ①ASTS-SHARES-OSCILLATION-1 ②WARN12-COHR-ONDS-1・
  HYPECORE-DASHBOARD-COUNT-BUG-1 ③FLAG-THRESHOLD-DESIGN-1
  ④GATE2-PHASE3B-1~~ → ①②は同日中に完了（下記追記参照）。

追記（2026-07-13 同日2回目・セッション終了時ブラッシュアップ）:
上記候補のうち①[[ASTS-SHARES-OSCILLATION-1]]・②[[WARN12-COHR-ONDS-1]]・
[[HYPECORE-DASHBOARD-COUNT-BUG-1]]を全て完了。加えて予定外だった
[[TICKER-DIRECT-ACCESS-GUARD-1]]（FLAG-CONSUMER-AUDIT-2/3の再発防止CI
ガード新設、`tests/test_no_direct_ticker_access.py`）も完了し、同ガードで
発見した`tail_dcf_bridge.py`のtanukiフラグ検証漏れを修正した。

- ASTS-SHARES-OSCILLATION-1: 調査時点の推定（ASTS/AVAV/RCATの3銘柄）から
  恒久修正の全105銘柄新旧比較で影響範囲がCART/CEG/BROS/GEV/XOM/CONを
  加えた**9銘柄に拡大**。副次発見のBROS 2021-03-31（Up-C組織再編前
  四半期）の妥当性を一次情報で確認し[[EPS-UPC-PREREORG-1]]として分離登録
- WARN12-COHR-ONDS-1: 根本原因はfact競合型バグではなく、**SEC自動更新
  （日曜21:00 JST）とTANUKI VALUATION再生成（平日23:05 JST）の生成順序の
  ズレ**（約20時間の陳腐化窓）と判明。pipeline.py再実行のみで解消し、
  この構造的ギャップ自体を[[WORKFLOW-SEC-TANUKI-GAP-1]]として新規登録
- TICKER-DIRECT-ACCESS-GUARD-1: 全リポジトリスキャンでcik_lookup.csv直接
  パース12ファイル・ルートディレクトリlistdir直接スキャン5ファイルを検出・
  許可リスト化。うち3件の既存直し漏れ（`phase1_scan.py`・
  `backfill_history.py`は一回限りスクリプトの疑い、`tail_dcf_bridge.py`は
  同日中に修正）を発見し、後者2件は[[PHASE1-SCAN-CLEANUP-1]]・
  [[BACKFILL-HISTORY-CLEANUP-1]]として登録。副次発見の軽微な重複実装2件
  （[[SYSHEALTH-CIK-DEDUP-1]]・[[TAIL-CIK-LOOKUP-DEDUP-1]]）も登録

**次セッションの候補（優先順位の所感）**:
① [[FLAG-THRESHOLD-DESIGN-1]]（優先度：未定・4フラグの機械判定基準を
Koichiさんに複数案提示して確定させる設計セッション。他タスクの前提に
なりうるため筆頭候補）に進む。
② 余力があれば[[GATE2-PHASE3B-1]]（優先度：中・独立実装4ファイルの
reader.py統合＋規約C/Dの型化、規模見積もりから）・
[[GATE2-READER-FCFLIST-1]]（優先度：中・reader.py::get_fcf_list()の
順序規約未検証）・[[EPS-UPC-PREREORG-1]]（優先度：中・Up-C組織再編前
四半期のAdjusted EPS算入方針）・[[WORKFLOW-SEC-TANUKI-GAP-1]]
（優先度：中・SEC更新とTANUKI VALUATION更新のworkflow連携）のいずれかに
着手する。
③ 優先度：低の軽量クリーンアップ4件（[[PHASE1-SCAN-CLEANUP-1]]・
[[BACKFILL-HISTORY-CLEANUP-1]]・[[SYSHEALTH-CIK-DEDUP-1]]・
[[TAIL-CIK-LOOKUP-DEDUP-1]]、いずれも陳腐化確認・重複実装解消の軽微作業）
は手が空いた時に片付ける。
[[SPLIT-REALTIME-GAP-1]]（優先度：低〜中）・
[[DATA-JUMP-CHECK-GENERALIZE-1]]（優先度：未定）は引き続き待機的な
着手条件（「次に関連バグが発生したら」等）のため後回しでよい。

（ARCH-SCORE-SYNC-1は2026-06-20、TAIL-SEC-1/EPIC-LEGEND-1は2026-06-21、
EPIC-HEADER-1は2026-06-21、EPIC-LAYOUT-1グループA/グループBは2026-06-22、
EPIC-LAYOUT-1グループC（SILO-DISP-3）・MP-GAUGE-NEEDLE-1・MACRO-DISP-2は
2026-06-23に完了。BACKLOG_DONE.md参照）

追記（2026-07-14）: FLAG-THRESHOLD-DESIGN-1の検討過程で
[[POLICY-AB-TREND-BLIND-1]]（優先度：高、8銘柄影響）を新規発見。
フラグ判定基準の設計はPolicy A/Bの結果を前提にできないため、
本バグの修正をFLAG-THRESHOLD-DESIGN-1より先行して対応する方針とした。
副次発見として[[FCF-EPS-CONVRATE-SECTOR-1]]・[[TRANSIENT-EXPENSE-COVERAGE-1]]
（いずれも優先度：未定）も新規登録。

追記（2026-07-14 同日2回目）: POLICY-AB-TREND-BLIND-1の網羅調査完了後、
ラベル（DCF_Reliability表示）の実利用価値は限定的（DCF数値自体には
影響せず、外部AI評価時の見え方緩和が主目的）と整理されたため、
優先度を高→低に変更。修正方針〈直近2年連続黒字を主基準に上方乖離を
LOW対象から除外〉は確定済みのまま保留し、後日必ず着手する。
代わりにFCF数値自体に影響しうる[[FCF-EPS-CONVRATE-SECTOR-1]]・
[[TRANSIENT-EXPENSE-COVERAGE-1]]を優先度：高に格上げし、次の着手対象とする。

追記（2026-07-14 同日3回目）: TRANSIENT-EXPENSE-COVERAGE-1のAVAV/RDW調査
完了。両銘柄とも一過性費用の検出漏れ（M&A取引費用タグ不足）は実在するが、
悪化の主因は別（運転資本変動）と10-K原文で確認したため、この2銘柄に
関しては現状のFCF数値・DCF計算は正しいと判断しクローズ・BACKLOG_DONE.mdへ
移動。副次発見のタグ・カテゴリ設計の穴を[[MA-INTEGRATION-TAG-GAP-1]]として
新規登録（優先度は全銘柄への影響範囲調査後に確定）。

追記（2026-07-14 同日4回目）: FCF-EPS-CONVRATE-SECTOR-1（LITE/SITM）の
調査完了。独立バグではなく既存[[SECTOR-FCF-RATE-BROKEN-1]]の実害具体例と
判明したためクローズ・BACKLOG_DONE.mdへ移動。同バグの優先度を中→高に
格上げ（LITE/SITMでの実害確認による）。副次発見の2課題（LITEの業種
カテゴリ欠落・固定比率設計の限界）を[[FCF-CONVRATE-DESIGN-LIMIT-1]]として
分離登録（着手条件: SECTOR-FCF-RATE-BROKEN-1完了後）。

追記（2026-07-14 セッション終了時ブラッシュアップ）: 本日1〜4回目の
変更を踏まえ、次セッションの筆頭候補を更新する。

**次セッションの筆頭候補は[[SECTOR-FCF-RATE-BROKEN-1]]**（本日 中→高に
格上げ・LITE/SITMでの実害を実データで確認済み・対応方針①②が既に整理
済みで着手条件もなし）。案①（`core_calculator.py:244`のsector変数差し替え、
低コスト）から着手し、効果範囲（Financial Services判定改善のみか）を
確認した上で案②（`damodaran_industry`連携、本格対応）の要否を判断する
のが妥当。

[[POLICY-AB-TREND-BLIND-1]]は優先度：高→低に変更済みだが、修正方針
〈直近2年連続黒字を主基準に上方乖離をLOW対象から除外〉は確定済みのまま
のため、余力があれば並行着手も可能（他タスクをブロックしない独立作業）。

[[FLAG-THRESHOLD-DESIGN-1]]は本日の議論でゴールを再整理した
（エントリ本文の「議論の要旨」追記参照）ものの、基準案の具体的な数値は
未確定のまま。[[POLICY-AB-TREND-BLIND-1]]の実装（優先度は下がったが
未着手）がstonks_silo判定基準の材料に影響するため、着手順序としては
SECTOR-FCF-RATE-BROKEN-1・POLICY-AB-TREND-BLIND-1の後が妥当。

新規登録の[[MA-INTEGRATION-TAG-GAP-1]]・[[FCF-CONVRATE-DESIGN-LIMIT-1]]
はいずれも優先度：未定（前者は全銘柄影響調査後、後者はSECTOR-FCF-RATE-
BROKEN-1完了後に再評価）のため、今回の筆頭候補には含めない。

追記（2026-07-14 実装完了）: [[SECTOR-FCF-RATE-BROKEN-1]]を実装・完了し
BACKLOG_DONE.mdへ全文移動した。①`core_calculator.py`のbeta_config.json
読み込みパス誤りを`data_fetcher.py::_load_beta_config()`呼び出しに統一、
②Damodaran公式データセット`indname.xls`への直接照合でtanuki=true97銘柄
（100銘柄中、CIX/MO/PMの3銘柄は対応キー不存在のため対応する省略キーが
なく据え置き）に`beta_config.json`の`sector`を新規付与、③既存
`TICKER_INDUSTRY_OVERRIDES`のうちテストデータと判明した8件
（HON/TDY/KULR/META/AMZN/NET/CIX/BKNG）+ CRWV（既存値がindname.xlsと
不一致と判明）をindname.xls実態値に修正。全105銘柄再生成・
report_consistency_check NG=0・pytest 309 passed（既知の2件除く）を確認済み。
副次課題[[FCF-CONVRATE-DESIGN-LIMIT-1]]の着手条件（本タスク完了）が
成立したため、次回セッションで再評価可能な状態になった。
これでSECTOR-FCF-RATE-BROKEN-1発の一連の調査・実装
（FCF-EPS-CONVRATE-SECTOR-1・MA-INTEGRATION-TAG-GAP-1・
FCF-CONVRATE-DESIGN-LIMIT-1・POLICY-AB-TREND-BLIND-1を含む）が一区切り。
次セッションの筆頭候補は[[FCF-CONVRATE-DESIGN-LIMIT-1]]（着手条件成立・
残存する8/114カバレッジ不足への対応方針検討）または
[[POLICY-AB-TREND-BLIND-1]]（修正方針確定済みで着手可能・優先度は低だが
軽量な独立作業）のいずれか。

追記（2026-07-14 セッション終了時ブラッシュアップ・2回目）:
[[SECTOR-FCF-RATE-BROKEN-1]]をコミット`3df6f4da2`（core_calculator.pyの
beta_config.json読み込みパス誤り修正＋indname.xls直接照合による
全銘柄sector一括付与＋TICKER_INDUSTRY_OVERRIDESテストデータ8件修正）・
`9e03134ad`（全105銘柄再生成）で完了・push済みであることを最終確認。
CIX/MO/PMの3銘柄は対応するDamodaran分類（Office Equipment & Services /
Tobacco）に対応する省略キーがSECTOR_TO_DAMODARANに存在しないため
sector未設定のまま残存するが、いずれも`fcf_conversion_config.json`の
8分類に該当しないため実害はない（default 0.70のまま、回帰でもない）。

次セッションの筆頭候補：
① [[FCF-CONVRATE-DESIGN-LIMIT-1]]（着手条件〈SECTOR-FCF-RATE-BROKEN-1完了〉
成立済み。LITEの`fcf_estimation.sector`が`Telecom_Equipment`に正しく設定
されたが該当カテゴリがないため`conversion_rate`はdefault(0.70)のまま
残存することを実データで確認済み。fcf_conversion_config.jsonのカテゴリ
拡張方針を検討）
② [[POLICY-AB-TREND-BLIND-1]]（優先度：低・修正方針〈直近2年連続黒字を
主基準に上方乖離をLOW対象から除外〉確定済みのまま。他タスクをブロック
しない軽量な独立作業のため余力があれば並行着手も可）

追記（2026-07-14 [[FCF-CONVRATE-DESIGN-LIMIT-1]] キー名不一致修正）:
上記①の着手として、まず`estimate_fcf_from_eps()`のconversion_rate基準
（純利益ベースであることを実装確認・確定）とダモドラン公式データ
（oifcff.xls、94業種）との整合性を調査したところ、想定していた
「LITEに対応するカテゴリが1つ足りない」以上に根が深い問題を発見した：
`fcf_conversion_config.json`の8カテゴリキー名が`config/beta_config.json`
のsector表記（Damodaran taxonomy準拠の略称）と文字列不一致で、
Software_Internet・Semiconductor以外の6カテゴリが該当銘柄0件＝
事実上デッドコード化していた。この6カテゴリのキー名リネーム
（数値は無変更）を実装し、38銘柄（TSLA/LMT他Aerospace_Defense6銘柄/
KO・PEP・CELH/SOFI・V・MSCI・FLYW・PAYS/ADBE・CRM・NOW・PLTR等
Software_System 23銘柄）で新たに非defaultレートが適用されるように
なったことを新旧比較で確認、pytest回帰なし（既知のMSFT/NVDA 2件除く）。
**ただし本修正はconfig側のキー名変更のみで、影響を受ける38銘柄の
`latest.json`/`report.txt`（本番データ）は未再生成のまま**——次回
再生成の要否・タイミングをKoichiさんと要確認。

次セッションの筆頭候補：
① 上記38銘柄の`pipeline.py`再実行・`report_consistency_check.py`
   NG=0確認・本番データコミットの要否判断（未実施のまま残っている）
② [[FCF-CONVRATE-DESIGN-LIMIT-1]]の残課題3点（LITE/SITM型のカテゴリ
   自体の欠如、固定比率設計の限界、EBIT(1-t)→純利益変換ロジック不在）
   ——優先度・対応方針は未定のまま
③ `Software_System`にリネームしたことで新規に対象となった23銘柄への
   レート0.80の妥当性検証（Azure型インフラ企業を想定した設計だが
   対象は汎用エンタープライズソフトウェア全般に拡大したため）

追記（2026-07-14 [[FCF-CONVRATE-DESIGN-LIMIT-1]] Software_Systemグループ分割実装完了）:
上記③の検証として23銘柄（IOT・QBTS/RBRK/S/SOUN除く18銘柄）の直近5年
実績（生FCF/調整済み純利益比率）を検証し、成熟ライセンス型（グループA、
平均≈1.00）とSaaS型（グループB、平均≈1.61）の二極化を確認。
`Software_System_Mature`/`Software_System_SaaS`の2カテゴリへ分割し、
18銘柄のsectorを実績ベースで確定した。新規銘柄向けには前受収益比率
（DR/Rev、閾値0.40）による暫定判定ロジック（`beta_fetcher.py
--classify-software-system`）と、実績蓄積後にpipeline.py実行のたびに
純関数として再判定する自己補正ロジック（`check_software_system_
reclassification()`、config書き換えなし・determine_fcf_base()と同設計
思想）を実装。全105銘柄で新旧比較・pytest・report_consistency_check
（NG=0）を確認済み。

このタスクの過程で[[VALIDATOR-IVPS-MISMATCH-1]]（validator.pyの
pt_shares_consistencyチェックが検証時と最終保存時で異なるIVを比較して
いる疑い、本タスクとは無関係の既存バグ）を新規発見・登録した。

次セッションの筆頭候補：
① [[VALIDATOR-IVPS-MISMATCH-1]]の影響範囲調査（WARN/FAILになっている
   銘柄の全件洗い出し）——DCF_Reliability表示の信頼性に関わるため
② [[FCF-CONVRATE-DESIGN-LIMIT-1]]残課題1〜3（LITE/SITM型のカテゴリ
   自体の欠如、固定比率設計の限界、EBIT(1-t)→純利益変換ロジック不在）
   ——優先度・対応方針は依然未定
③ 前受収益比率による暫定判定ロジックの分離精度（約78%）を踏まえ、
   新規銘柄登録が発生した際に実際にIOT型（境界近傍）のケースが
   出た場合の運用確認（テストケースがまだ実データで発生していない）

追記（本日セッション終了時ブラッシュアップ）: VALIDATOR-IVPS-MISMATCH-1
（主因: validator.pyがALPHA-REDESIGN-1のalpha非乗算式に未追随、
副因: _save_resultでのvalidation再実行漏れ）を対応①②で修正・完了
（コミット03b855b54・3d0f1de43・26328aab5）。全100銘柄で新旧比較し
pt_shares_consistency pass 36→100/100、overall PASS 34→69・WARN
64→30・FAIL 2→1を確認。report_consistency_check NG=0・pytest
309 passed（既知2件除く）。

派生課題2件を登録・優先度確定（コミットa6555e3b0）:
- [[REPORT-ALPHA-STALE-1]]（優先度：中〜高・pipeline.py:1478-1510の
  report.txt REPORT-6ブロックが廃止済みalpha乗算式のまま、DCF構成要素の
  自己完結性が崩れている実害あり・未着手）
- [[ALPHA-CAP-HARDCODE-1]]（優先度：低・実害なしと確認済み・
  validator.pyのformula_verification誤警告のみ）

次セッションの筆頭候補：
① [[REPORT-ALPHA-STALE-1]]（実害あり・優先度中〜高・未着手）
② [[FCF-CONVRATE-DESIGN-LIMIT-1]] 残課題1〜3（持ち越し中）
③ [[POLICY-AB-TREND-BLIND-1]]（優先度低・軽量な独立作業）
④ [[ALPHA-CAP-HARDCODE-1]]（優先度低・手が空いた時に）

追記（2026-07-15 [[REPORT-ALPHA-STALE-1]]完了）: 事前調査（読み取り専用）で
`pipeline.py:1478-1510`（REPORT-6ブロック）に加え、同ファイル内の
Definition固定テキスト2箇所（`[3.TANUKI VALUATION]`セクションの
`P_t = DCF_v0 × (1+Alpha) + ...`説明文、`[7.HYPECORE]`セクションの
`Alpha: ... added to IV`説明文）にも同型の陳腐化を追加発見したため、
これら3箇所を一括してスコープに含めて実装・完了した（コミット
`581a93d28`コード修正・`59ae5b6c6`全100銘柄再生成）。ADBE/NVDAで
Equity_Value ÷ Shares_Used = Intrinsic_Valueの式が成立することを手計算で
確認済み。report_consistency_check NG=0・pytest 309 passed（既知2件除く）。
横展開調査でscenarios.py/sensitivity.py/adjustments.py/validator.py/
stock.htmlはいずれも実害なしと確認済み（詳細はBACKLOG_DONE.md
「2026-07-15（完了）」セクション参照）。

これにより次セッションの筆頭候補を更新する：
① [[FCF-CONVRATE-DESIGN-LIMIT-1]] 残課題1〜3（LITE/SITM型のカテゴリ
   自体の欠如、固定比率設計の限界、EBIT(1-t)→純利益変換ロジック不在。
   着手条件成立済み・持ち越し中）
② [[POLICY-AB-TREND-BLIND-1]]（優先度：低・修正方針〈直近2年連続黒字を
   主基準に上方乖離をLOW対象から除外〉確定済み。他タスクをブロック
   しない軽量な独立作業）
③ [[ALPHA-CAP-HARDCODE-1]]（優先度：低・実害なしと確認済み・
   validator.pyのformula_verification誤警告のみ・手が空いた時に）

追記（2026-07-15 [[FCF-CONVRATE-DESIGN-LIMIT-1]]残課題2・3を
[[TRUST-SUMMARY-EPIC-1]]へ統合）: 残課題2（固定比率設計がサイクル変動
銘柄を表現できない構造的限界）・残課題3（EBIT(1-t)ベース→純利益ベース
変換ロジック不在）をTRUST-SUMMARY-EPIC-1のFCF/DCF信頼性層スコープへ
統合し、FCF-CONVRATE-DESIGN-LIMIT-1エントリからは削除（移設注記を追記）。
FCF-CONVRATE-DESIGN-LIMIT-1には残課題1（LITE/SITM型カテゴリ欠如。
LITE/SITM型カテゴリ追加の調査を別途依頼済み・報告待ち）・残課題4
（IOT等判定保留）・残課題5（暫定判定精度78%）のみ残置。

これにより次セッションの筆頭候補を更新する：
① [[FCF-CONVRATE-DESIGN-LIMIT-1]]残課題①（LITE/SITM型カテゴリ追加、
   調査依頼発行済み・報告待ち）
② [[TRUST-SUMMARY-EPIC-1]]（②③統合後の設計検討・優先度：高で未着手のまま）
③ [[POLICY-AB-TREND-BLIND-1]]（優先度：低・軽量な独立作業）
④ [[ALPHA-CAP-HARDCODE-1]]（優先度：低）

追記（2026-07-15 [[FCF-CONVRATE-DESIGN-LIMIT-1]]残課題①をTRUST-SUMMARY-EPIC-1へ統合）:
残課題①（LITE/SITM型カテゴリ欠如）の調査完了。SITMは既に解決済み
（beta_config.jsonのsector確定済み）、LITE単体の追加対応は残課題③と
同根の問題（EBIT(1-t)→純利益変換ロジック不在）のため見送りと判断。
加えて調査中にLITE以外44銘柄（うち33銘柄がfcf_estimation.applied=Trueで
default(0.70)使用中、乖離大: LITE 4.33倍・SPIR 8.65倍・LLY 1.92倍等）の
sector未収録という同型の広範なギャップを新規発見したため、個別対応では
なくTRUST-SUMMARY-EPIC-1のFCF/DCF信頼性層スコープへ統合。
FCF-CONVRATE-DESIGN-LIMIT-1エントリからは残課題①を削除し移設注記を追記、
残課題4（IOT等判定保留）・残課題5（暫定判定精度78%）のみ残置。

これにより次セッションの筆頭候補を更新する：
① [[TRUST-SUMMARY-EPIC-1]]（優先度：高・②③・残課題①統合後の
   設計検討、未着手）
② [[POLICY-AB-TREND-BLIND-1]]（優先度：低・軽量な独立作業）
③ [[ALPHA-CAP-HARDCODE-1]]（優先度：低）
④ [[FCF-CONVRATE-DESIGN-LIMIT-1]]（残課題4・5のみ残置・優先度未定
   のまま待機）

追記（2026-07-15 [[ARCH-DATA-1]]残課題①完了）: 計算層への重複実装
一本化（暦年グルーピング・BS項目同一時点原則）を完了（コミット
`4e4629a3b`・`60d44b2d8`）。調査の過程でV（Visa）の表示乖離（約$1.56B）・
SOUN（LTDebt誤除外）の2件の実害を発見・是正した（いずれもIntrinsic_Value・
TANUKI SCORE分類には影響なし）。残課題②（EPS Analyzer経路のスコープ判断）を
[[EPS-ANALYZER-NORMALIZE-SCOPE-1]]として分離登録。残課題③（パターン判定
ロジックの実装）は依然未着手。

これにより次セッションの筆頭候補を更新する：
① [[ARCH-DATA-1]]残課題③（パターン判定ロジックの実装、PREFLIGHT-CHECK-1と
   共有設計・今回洗い出したパターン一覧を材料に設計）
② [[EPS-ANALYZER-NORMALIZE-SCOPE-1]]（優先度未定・スコープ判断待ち）
③ [[TRUST-SUMMARY-EPIC-1]]（段階0の可視化検討はARCH-DATA-1①③の進捗を
   踏まえて再開）
④ [[POLICY-AB-TREND-BLIND-1]]（優先度：低・軽量な独立作業）

追記（2026-07-15 [[ARCH-DATA-1]]残課題③完了・revenue系タグ競合検知）:
当初想定していたPREFLIGHT-CHECK-1と共有する汎用パターン判定カタログ構想は
精度未検証のリスクが高いと判明したため見送り、revenue系タグ競合の実データ
検知（`common/sec_data/revenue_tag_conflict_check.py`新設、`update.py`の
Step1完了直後に配線）に最小スコープを絞って実装した（コミット
`f05cae0ba`）。SOFI・IONQの既知ケースを正しく再現することを確認し、全100
銘柄実行でPM・AVGO・DELL等の新規候補タグ競合を発見（詳細・対応要否は
[[REVENUE-TAG-CONFLICT-SCAN-1]]に分離登録）。副次的に未使用の
`quality_checker.py`を発見し[[QUALITY-CHECKER-CLEANUP-1]]として登録。
PREFLIGHT-CHECK-1エントリにも見送りの経緯を追記済み。

これにより次セッションの筆頭候補を更新する：
① [[TRUST-SUMMARY-EPIC-1]]（段階0の可視化検討を再開。ARCH-DATA-1残課題
   ①③が完了しFCF/DCF信頼性層〈段階2〉統合も済んだため、段階0側の
   前提が揃った状態）
② [[EPS-ANALYZER-NORMALIZE-SCOPE-1]]（優先度未定・スコープ判断待ち）
③ [[POLICY-AB-TREND-BLIND-1]]（優先度：低・軽量な独立作業）
④ [[QUALITY-CHECKER-CLEANUP-1]]（優先度：低・未使用コードの削除要否判断）

追記（2026-07-15 [[FY52WEEK-BUCKET-MISPLACE-1]]新規登録・実装は見送り）:
[[REVENUE-TAG-CONFLICT-SCAN-1]]で新規発見したAVGO/DELL/CAKE/ELFの
revenueタグ競合について、根本原因（52/53週会計年度企業で
`determine_fiscal_year()`の月判定により真の年次値が隣接年度バケツへ
系統的に押し出される）を特定した。duration filterによる最小修正
（誤った値→値なしの明示）を試行したが、①複数年度にわたる系統的な
ズレのため一部年度は隣接年度の値へのラベル誤りのまま横滑りするだけで
値なしにならない、②DELLの真のFY2019値自体がduration filterとは無関係な
別種のend_yearバケツ衝突により消失したまま、という2点から目的を
達成できないと判明。実装は復元・未コミットのまま
[[FY52WEEK-BUCKET-MISPLACE-1]]として根本修正の設計待ちで新規登録した
（growth_sanity実害はCAGR参照窓の外のため現時点でなしと確認済み）。
併せてTDY・ASTSの一次情報確認結果を[[REVENUE-TAG-PRIORITY-FRAGILE-1]]
として新規登録した。

これにより次セッションの筆頭候補を更新する：
① [[FY52WEEK-BUCKET-MISPLACE-1]]（優先度：高・根本修正の設計要）
② [[TRUST-SUMMARY-EPIC-1]]
③ [[EPS-ANALYZER-NORMALIZE-SCOPE-1]]
④ [[REVENUE-TAG-PRIORITY-FRAGILE-1]]
⑤ [[POLICY-AB-TREND-BLIND-1]]
⑥ [[QUALITY-CHECKER-CLEANUP-1]]

追記（2026-07-15 [[FY52WEEK-BUCKET-MISPLACE-1]]実装完了）:
submissions API（`reportDate==end_date`本人データ判定）による根本修正を
実装・全106銘柄のデータ再生成・検証まで完了し、BACKLOG_DONE.mdへ全文
移動した（コミット`b93daff80`〜`cd43b03cf`の5件、push済み）。当初10銘柄
に加え、実装過程で新規発見したfyタグ衝突8銘柄（CRM/FCX/WMT等）も解消。

実装過程で新規に2件（[[FY52WEEK-BS-INSTANT-FACT-1]]・
[[FY52WEEK-BS-NULL-SILENT-1]]、いずれも優先度：高・着手条件なし）と、
別原因のデータ欠損1件（[[MRVL-2019-2020-NULL-1]]、優先度：中〜低・
原因調査は別途依頼要）を新規登録した。

これにより次セッションの筆頭候補を更新する：
① [[FY52WEEK-BS-INSTANT-FACT-1]]（優先度：高・着手条件なし・instant
   fact〈BS項目〉向けの本人データ判定を今回のPL/CF項目向け実装と
   同型で再設計。対応方針は本文に明記済みで着手しやすい）
② [[FY52WEEK-BS-NULL-SILENT-1]]（優先度：高・着手条件なし・①と対になる
   構造的リスク。`or 0`パターンのNone検知＋明示的警告化。①の修正後も
   別原因のNone化全般に効くため、①と独立に着手可能）
③ [[TRUST-SUMMARY-EPIC-1]]（優先度：高・要設計・実装未着手の大規模EPIC。
   ①②はこのEPICが対象とする構造的リスクの具体事例のため、①②を先に
   片付けてから再開するのが妥当）
④ [[EPS-ANALYZER-NORMALIZE-SCOPE-1]]（優先度：未定だがスコープ判断のみの
   軽量タスク・着手条件は「次回セッションで方針判断してから」）
⑤ [[REVENUE-TAG-PRIORITY-FRAGILE-1]]（優先度：中〜低）
⑥ [[MRVL-2019-2020-NULL-1]]（優先度：中〜低・原因調査は別途依頼要）
⑦ [[QUALITY-CHECKER-CLEANUP-1]]（優先度：低）
⑧ [[POLICY-AB-TREND-BLIND-1]]（優先度：低・修正方針確定済みの軽量独立
   作業・他タスクをブロックしないため手が空いた時でも可）

追記（2026-07-16 [[FY52WEEK-BS-INSTANT-FACT-1]]事前調査②完了・ARCH-DATA-1へ統合）:
[[FY52WEEK-BS-INSTANT-FACT-1]]の安全弁ロジック設計調査（2回目）で、
`_own_override_is_safe`の安全弁条件2が12月決算企業で機能しない欠陥を
実データ（CDNS FY2015のtotal_assets/revenueがFY2014の値のまま誤って
保持されている実例）で確認した。個別パッチではなく、年次データ正規化を
「値の確定→決算アンカー日ベースの年度ラベル計算→XBRLタグとの突き合わせ
検証」の3段階で再設計する方針が固まったため、[[FY52WEEK-BS-INSTANT-FACT-1]]
は個別タスクとしてはクローズし[[ARCH-DATA-1]]へ統合、同時に[[ARCH-DATA-1]]
の優先度を「高」→「最高」に格上げした。副次発見として
[[CASH-TAG-MISSING-1]]（優先度：中、CAT/CPRT/ELF/GEV/HEIのcash_and_equivalents
欠落、52/53週バグとは無関係なタグ定義漏れ）を新規登録した。

これにより次セッションの筆頭候補を更新する：
①~~[[ARCH-DATA-1]]（3段階設計の実装着手・優先度：最高）~~
   ✅ ステージ1（値の確定）のみ2026-07-16完了。ステージ2・3は未着手
   （下記追記参照）
② [[QUALITY-GATES-EPIC-1]] Phase 3b（①と並行可）
③ [[FY52WEEK-BS-NULL-SILENT-1]]（①と独立着手可）
④ [[TRUST-SUMMARY-EPIC-1]]（①進捗待ちで据え置き）
⑤ [[POLICY-AB-TREND-BLIND-1]]（優先度：低・軽量な独立作業）
⑥ [[CASH-TAG-MISSING-1]]（優先度：中・新規）

追記（2026-07-16 [[ARCH-DATA-1]]ステージ1「値の確定」完了）:
10-K/A候補プール化・filed日タイブレーク・出所メタデータサイドカーを
実装・全105銘柄再生成完了（コミット`4587ee09e`・`ba9927676`）。事前
検証の185件・18銘柄と完全一致、pytest・report_consistency_check.py
とも変更前と同一水準を確認。DOCN/LYFT/QBTS/SPIRの個別確認では
TANUKI SCORE分類はいずれも不変（SPIRのみIntrinsic_Value_BASEが
+7.6%変化）。詳細は[[ARCH-DATA-1]]「残課題④」参照。

これにより次セッションの筆頭候補を更新する：
① [[ARCH-DATA-1]]ステージ2（年度ラベル計算のアンカー日ウィンドウ化）
② [[QUALITY-GATES-EPIC-1]] Phase 3b
③ [[FY52WEEK-BS-NULL-SILENT-1]]
