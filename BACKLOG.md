# On-a-journey — 改善バックログ（全システム）

最終更新: 2026-08-12（`[[MACRODATA-LAYER-CONSTRUCTION-1]]`: 本番消費者
2ファイル（`05_main.py`・`collect_and_send.py`）を`common.macro_data.
reader`経由へ全面切替し**完成**。MIGRATION_CHECKLIST.md Step1〜3に
従い実施。Step1（洗い出し）で想定リストになかった2箇所
（`refresh_monthly_indicators()`・`update_fed_context()`）と、grepパターン
（`Fred(`/`fred_latest(`）では検出できなかった`_load_sp500_cache()`の
`fred.get_series()`直接呼び出しを追加発見。重複3系列
（`BAMLH0A0HYM2`・`T10Y2Y`・`VIXCLS`）は`reader.get_latest()`への集約で
解消。単一最新値だけでは機能を維持できない5箇所（NFP前月比・VXN
MA50・HYスプレッド90日min/max・DGS3MO前日比・S&P500複数日履歴）は
`reader.get_series()`（期間指定）を使用（依頼の`get_latest()`一本化
方針から実装上必要な範囲でのみ逸脱、詳細を明記）。Step2（値突合）で
18項目全て完全一致（差分0件）を実測確認。Step3（grep最終確認）で
`Fred(`・`fred_latest(`等の直接呼び出しが両ファイルとも0件であることを
確認。リトライ・指数バックオフロジックも削除（`fred_release_dates()`
は別API表面のため対象外・維持）。`tests/test_macro_pulse_logic.py`の
関連7件をmonkeypatch方式に更新。pytest全体771 passed / 2 known-failed。
PROJECT_STATUS.md・SYSTEM_MAP.mdも同時更新）

最終更新: 2026-08-12（`[[MACRODATA-LAYER-CONSTRUCTION-1]]`:
`.github/workflows/Macro_Data_Update.yml`（毎日UTC10:00・
workflow_dispatch対応）を新設し定期取得ワークフローが稼働開始。
GitHub Actions側のworkflow_dispatchを直接トリガーする手段がセッション
環境になかったため、同一エントリポイントをローカルで実FRED_API_KEY
実行し代替検証。25系列中24系列成功（更新レコード合計94,909件）、
`FTSD`のみFRED API上に系列が実在せず失敗（`[[MACRODATA-FTSD-SERIES-
ID-INVALID-1]]`新規登録）。`macro_data_violations_log.json`の警告
255件は全て実在する経済事象・近ゼロ交差によるorder-of-magnitude
jump検知でありデータ品質問題なしと判断。副次発見として日次cronが
毎回全期間履歴を再取得する非効率な設計も判明
（`[[MACRODATA-FULL-HISTORY-DAILY-REFETCH-1]]`新規登録）。05_main.py・
collect_and_send.pyは今回も変更していない。PROJECT_STATUS.md・
SYSTEM_MAP.mdも同時更新）

最終更新: 2026-08-12（`[[MACRODATA-LAYER-CONSTRUCTION-1]]`:
`common/macro_data/fetcher.py`/`reader.py`本体を実装（**構築中**）。
`fetch_series`/`update_series`/`fetch_all_series`（fredapiクライアント
のモジュールレベル一元化・リトライ3回＋指数バックオフ・保存前検証2項目
＋`macro_data_violations_log.json`）・`get_latest`/`get_series`/
`get_value_as_of`・25系列分の`series_meta.json`を実装。新規テスト
`tests/test_macro_data_fetcher.py`・`tests/test_macro_data_reader.py`
（計43件）を追加、pytest全体771 passed / 2 known-failedで回帰なしを
確認。今回のスコープは新規モジュール構築のみで、`05_main.py`・
`collect_and_send.py`側の本番消費者切替（重複3系列解消含む）・GitHub
Actionsワークフロー新設・過去データ一括投入（フェーズ2）はいずれも
今回変更していない（次段階）。PROJECT_STATUS.md・SYSTEM_MAP.mdも
同時更新。詳細は`[[MACRODATA-LAYER-CONSTRUCTION-1]]`参照）

最終更新: 2026-08-12（セッション終了時ブラッシュアップ。遡って
`[[MACRODATA-LAYER-CONSTRUCTION-1]]`（`common/macro_data/`新設、
FRED統合層）をマスター追跡エントリとして正式登録（`[[MARKETDATA-
LAYER-CONSTRUCTION-1]]`と同型。投資調査サマリー・新規発見4件への
リンク・次セッション着手順序を記載）。前回投資調査で言及していたが
未登録のまま参照していたことが本ブラッシュアップで判明したための
訂正登録。あわせて`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`エントリ内の
「次セッションでの着手順序」を`[[MACRODATA-LAYER-CONSTRUCTION-1]]`
参照に更新。実装コード変更なし）

最終更新: 2026-08-12（`common/macro_data/`新設事前調査（FRED消費者洗い出し、
`MIGRATION_CHECKLIST.md`Step1相当）で発見した新規4件を登録（記録のみ、
実装なし）。優先度：中に`[[MACRODATA-AS-IS-DUPLICATION-UNDERCOUNT-1]]`
（`INPUT_DATA_TOBE.md`記載の`BAMLH0A0HYM2`重複取得「3箇所」は実際には
`get_financial_context()`を含む4箇所、`T10Y2Y`・`VIXCLS`にも同型の
未記載重複あり）・`[[MACRODATA-SCHEDULED-SILENT-GAP-CSCICP-USALOL-1]]`
（現行`INDICATOR_CONFIG`から削除済みの2系列の残存`scheduled`行が
サイレントにactual欠落を起こす疑い、実データ確認が着手条件）、
優先度：低に`[[MACRODATA-FTSD-MISSING-FROM-INVENTORY-1]]`（`FTSD`が
24系列台帳に未掲載）・`[[MACRODATA-IMPORT-HISTORY-CONFIG-DRIFT-1]]`
（`05_import_history.py`の独自`FRED_INDICATORS`辞書が現行
`INDICATOR_CONFIG`と2系列分乖離）を登録。実装コード変更なし）

最終更新: 2026-08-12（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`着手順序6-2:
`backfill_tech_pulse.py`（QQQ/SPY取得）切替が**完了**。前提作業として
`reader.py`へ`get_price_series_as_of(symbol, as_of_date, days)`を新規
追加（任意過去基準日起点のトレイリングウィンドウ取得、共通実装
`_price_series_ending_at()`へ`get_price_series()`ともリファクタ）した
上で本体切替。「実行時点で1回だけ取得し全エントリで使い回す」旧設計
思想は維持。51件のmissingエントリ全件で`--dry-run`実行・旧実装との
`tp_score`/`tp_label`突合を実施し、`_tp_label()`バケット判定のクロス
0件を確認。pytest全体は728 passed（既知失敗2件はTEST-STALE-IV-1、
無関係）。**これにより着手順序6は周辺ツール2/2（全数完了）、着手順序
4〜6（本番消費者8＋診断ツール2＋周辺ツール2の全12ファイル）が完了し、
`common/market_data/`構築プロジェクト自体が完了**。詳細・検証結果は
BACKLOG_DONE.md「2026-08-12（完了）」`[[MARKETDATA-LAYER-CONSTRUCTION-1]]
着手順序6-2`参照（コミット`4a864bc1c`）

最終更新: 2026-08-12（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`着手順序6-1:
`extract_key_facts.py`（株式数フォールバック④）切替が**完了**。
yfinance直接呼び出し（`.info.get('sharesOutstanding') or
.get('impliedSharesOutstanding')`）を`reader.get_attributes()`経由
（`shares_outstanding`優先→`implied_shares_outstanding`フォールバック、
既存優先順位パターン維持）に置換。V（該当フォールバックの実例銘柄）で
切替後コードを実際に発動させ、切替前のキャッシュ値と完全一致を確認。
EPS Analyzer対象101銘柄をキャッシュ済みquarterly.jsonで走査した結果、
fallback④該当はV 1件のみと判明（他100銘柄は影響なし）。pytest全体は
721 passed（既知失敗2件はTEST-STALE-IV-1、無関係）。これで着手順序6は
周辺ツール2ファイル中1ファイル完了（1/2）、残るは`backfill_tech_pulse.py`
（`reader.py`への新規API追加が前提と判明済み）のみ。詳細・検証結果は
BACKLOG_DONE.md「2026-08-12（完了）」`[[MARKETDATA-LAYER-CONSTRUCTION-1]]
着手順序6-1`参照（コミット`212454681`）

最終更新: 2026-08-12（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`着手順序5-2:
`score_verifier.py`切替が**完了**。前提作業として`reader.py`へ
`get_price_on_or_after(symbol, date)`を新規追加（date以降5日ウィンドウで
先頭値を採用、旧`fetch_price_after()`と同じクエリ形状をdaily/層に対して
再現）。`fetch_price_after()`をyfinance直接呼び出しから同API経由に置換。
`Score_Verifier.yml`の依存インストールも`pip install -r requirements.txt`
へ更新。ライブA/Bテスト（RKLB/ZS各3サンプル）で旧実装との価格・日付特定
ロジック完全一致を確認、実データ全102銘柄でscore_verifier.py実行が
例外なく完走することを確認済み。これで診断ツール2/2（`audit.py`・
`score_verifier.py`）とも切替完了、本番消費者8＋診断ツール2の
全10ファイルが切替完了。残るは着手順序6（周辺ツール2ファイル）のみ。
詳細・検証結果はBACKLOG_DONE.md「2026-08-12（完了）」
`[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序5-2`参照（コミット
`2668f3aaf`・`bc0f6fb24`）

最終更新: 2026-08-11（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`着手順序5-1:
`audit.py`（β乖離監査・カナダ企業判定）切替完了。`attributes/`へ
`country`フィールドを新規追加し、両判定ともyfinance直接呼び出しから
`reader.get_attributes()`経由に切替（設計確定事項6の方針通り）。
`SEC_Data_Audit.yml`の依存インストールも`pip install -r requirements.txt`
へ更新。副次発見: 旧`SEC_Data_Audit.yml`はyfinance未導入のためカナダ判定が
本番自動実行で常に無音スキップされ事実上死んでいたが、今回の切替で
実際に機能するようになった。残る5-2`score_verifier.py`は、`reader.py`へ
任意過去日点参照API（`get_price_on_or_after`相当）の新規追加が前提と
判明し次点保留。詳細はBACKLOG_DONE.md「2026-08-11（完了）」着手順序5-1・
`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`エントリ参照）

最終更新: 2026-08-11（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`: `fetcher.py`・
`reader.py`新設と定期実行ワークフロー2件（Daily/Weekly Update）を実装、
続けて本番消費者8ファイル（`beta_fetcher.py`・`data_fetcher.py`・
`valuation_fetcher.py`・`pipeline.py`・`collect.py`・`collect_and_send.py`・
`breadth_calculator.py`・`hypecore.py`）**全数の切替が完了**。うち
`hypecore.py`は前提作業3件（daily/バックフィルを`start="2021-01-01"`へ
拡張・attributes/へ7フィールド追加・analyst_history/へearnings_history・
recommendations_historyの2系統追加）を要する最複雑の消費者だった。
一連の作業で発見した副次課題を`[[MARKETDATA-CWAN-FROZEN-DATA-
SUSPECT-1]]`・`[[MARKETDATA-SP500-SCRAPE-INVALID-TICKERS-1]]`・
`[[MARKETDATA-VIX9D-DATA-GAP-1]]`・`[[STONKS-SILO-CLI-TICKERS-
SHADOW-1]]`として登録。誤って「バグ」登録した`[[MARKETDATA-DAILY-
UNADJUSTED-PRICE-DIVIDEND-DRIFT-1]]`（daily/層のauto_adjust=False
〈未調整終値〉と旧実装のauto_adjust=True〈調整済み終値〉の乖離）は、
事実確認調査の結果「旧実装の調整済み終値使用の方が技術指標としては
元々不適切だった」と判明したため訂正・クローズ（対応不要で確定）。
次は着手順序5（診断ツール2ファイル`score_verifier.py`・`audit.py`の
切替）。詳細はBACKLOG_DONE.md「2026-08-11（完了）」および
`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`エントリ参照）

最終更新: 2026-08-08（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`の未決定
事項9件を全件最終確定。1.営業日連続性保証〈pandas_market_calendars
新規依存採用〉2.fetched_at付与 3.書き込みアトミック化〈tempfile→
os.replace()〉4.層またぎ再計算禁止〈reader.pyドキュメント明記〉
5.保存前検証〈時価総額乖離許容率=相対2%または絶対$1,000,000の
大きい方、52週高安は日次バッチ時点のみ、失敗時は警告フラグ付き保存、
market_data_violations_log.json〉6.audit.pyとの役割分担〈内部整合性
ゲートvs外部妥当性監視、両方維持〉7.twoHundredDayAverageは非保存・
アナリスト目標株価コンセンサスはattributes/へ 8.workflow_run連鎖
トリガー採用 9.NETCASH-DUAL-CALC-1とは独立並行進行、の内容で確定。
着手順序を「fetcher.py→reader.py→本番消費者→周辺ツール」の4段階に
更新（設計判断ステップを解消により削除）。実装コード変更・データ
再生成なし（BACKLOG登録のみ）。

最終更新: 2026-08-07（セッション終了時ブラッシュアップ。「次セッション
での着手順序」欄を全面再構成し、1〜5を`[[MARKETDATA-LAYER-
CONSTRUCTION-1]]`の未決定事項9件確認→`fetcher.py`→`reader.py`→本番
消費者→周辺ツールの具体的5段階に、6を本線外課題群（優先度中の
AVGO-CIK-HISTORY-WRONG-LEGACY-CIK-1・優先度低のLayer3関連10件）に
整理。`common/macro_data/`着手はmarket_data完了後の継続タスクとして
注記。実装コード変更なし）

最終更新: 2026-08-07（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`の「未決定
事項」に、`EXTRACTION_DESIGN_PRINCIPLES.md`3原則照合投資調査（チャット
記録）の結果である追加6項目（営業日連続性保証・`fetched_at`付与・
書き込みアトミック化・層またぎ再計算の禁止・保存前恒等式検証＋
`market_data_violations_log.json`・`audit.py`との役割分担）を追記。
着手順序を「6項目の設計確定」を最初のステップとして追加した5段階に
更新。実装コード変更・データ再生成なし（BACKLOG登録のみ）。

最終更新: 2026-08-07（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`を新規登録
（本来は事前調査着手時点で登録すべきだったが未登録のまま3回の投資
調査を実施していたため遡って正式登録）。3回の投資調査サマリー
（12ファイル使用実態・3区分分類・`fetcher.py`/`reader.py`実装設計）
と、設計確定事項（保存構造・API設計、`.info`取得方式案C採用、
TANUKI VALUATION/STONKS SILOの株価を取引時間中リアルタイムから前日
終値ベースへ仕様変更、`audit.py`の`reader.py`経由切替）を記録。
未決定事項3件（`twoHundredDayAverage`等の格納先・`workflow_run`連鎖
トリガーの適用範囲・`[[NETCASH-DUAL-CALC-1]]`との関係整理）と着手
順序（`fetcher.py`→`reader.py`→本番消費者→周辺ツール）を明記。
実装コード変更・データ再生成なし（BACKLOG登録のみ）。

最終更新: 2026-08-07（`common/market_data/`新設事前調査で発見した
`[[MARKETDATA-AS-IS-AUDIT-PY-OMITTED-1]]`（優先度：低）を登録。
`INPUT_DATA_AS_IS.md` 1-B節の「11ファイル」調査が`src/`配下のみを
対象としており、`common/sec_data/audit.py`（β乖離監査、
`SEC_Data_Audit.yml`経由で本番稼働中）を見落としていたと判明。
`INPUT_DATA_AS_IS.md`本体は別途12ファイルへ訂正。実装コード変更・
データ再生成なし（BACKLOG登録＋ドキュメント訂正のみ）。

最終更新: 2026-08-07（フェーズE（`normalized/`廃止）の着手不可判定を
`[[SECDATA-STORAGE-FRAGMENTATION-1]]`（マスター追跡エントリ）に反映。
フェーズD最終状況：Step2-1〜2-4（①〜④主要4消費者パイプライン）完了、
Step2-5（⑤stock.html＋診断・補助スクリプト7件）は切替対象ほぼ存在
せず実質完了、保留中だった2判断（`fetcher.py`選択思想・stock.html
公開パイプライン）はいずれも現状維持・着手見送りで確定。
`fetcher.py`・`dcf_validity_checker.py`・stock.htmlが`normalized/`
またはparser.py系データへの依存を意図的に継続する恒久的例外として
残るため、フェーズE（`normalized/`完全廃止）は着手不可と判定し、
`normalized/`はこの3系統向けに存続する設計とすることを記録。
CLAUDE_CODE_START.mdのフェーズD進捗欄も、フェーズD実質完了・次の
優先タスクは新DB構築プロジェクトの他フェーズ（`common/market_data/`・
`common/macro_data/`新設）への移行検討である旨に更新。実装コード
変更・データ再生成なし（BACKLOG登録のみ）。

最終更新: 2026-08-07（stock.htmlのLayer3切替着手要否投資調査結果を
反映。`[[STOCKHTML-LAYER3-PUBLISH-PIPELINE-MISSING-1]]`（優先度：低、
Layer3ストア公開パイプライン未整備が着手ブロッカー、技術コストは
低いが現状実害ゼロのため見送り）・`[[STOCKHTML-YTD-FILTER-BUG-
SUSPECT-1]]`（優先度：低、JS側`getQ()`のis_ytd未除外は構造的リスク
だが105銘柄×5フィールド全数実測で現状未発現と確認）を新規登録。
`[[SCHEMA-NORMALIZED-ISSUES-1]]`⑥DAフォールバック欠如に、今回の
実測データ（105銘柄中30銘柄・約29%でDAフィールド空、MSFT/TSLA/
GOOGL/AVGO等主要銘柄含む）を追記。実装コード変更・データ再生成なし
（BACKLOG登録のみ）。

最終更新: 2026-08-07（`[[LAYER3-FETCHER-SELECTION-PHILOSOPHY-
MISMATCH-1]]`の対応方針を確定。案2（Layer3切替を見送り、`fetcher.py`・
`dcf_validity_checker.py::check_c_data_jump()`とも`data/annual_*.json`
直読みを継続）を採用し、優先度を高→低に格下げ（対応不要、記録のみ・
恒久的な例外扱い、BACKLOG.md「優先度：低」セクションへ移動）。採用
理由：Layer3の「filed日最新優先」は修正再表示の正誤を区別できない
不確実な方式である一方、parser.pyの「own-year優先」は実績ある一貫
した基準のため、正確性の確実性を犠牲にしてまで統一する理由がない。
本決定により前提条件が消滅した`[[LAYER3-STONKS-SPAC-EARLY-YEAR-
GAP-1]]`をクローズしBACKLOG_DONE.mdへ移動。CLAUDE_CODE_START.mdの
フェーズD進捗欄も本決定を反映するよう更新。実装コード変更・データ
再生成なし（BACKLOG登録のみ）。

最終更新: 2026-08-07（フェーズD Step2-4（HypeCore）実装完了。
`hypecore.py::fetch_quarterly_fundamentals()`のnormalized/参照を
SEC EDGAR Layer3（`layer3_builder.py::build_ticker_store()`/
`get_quarterly_series()`）経由に切替。104銘柄全数比較で事前調査の
予測（差分銘柄数6/104：ASTS/CEG/CWAN/DDOG/RCAT/BROS）と完全一致、
ASTS/RCAT/DDOGの`determine_stage()`再確認でもステージ判定差分ゼロを
再確認。report_consistency_check.py NG=0・WARN=78件（不変）、pytest
505 passed/2 known failed（既知のみ）。完了記録は`[[SEC-EDGAR-LAYER-
DESIGN-PHASE-D-STEP2-4]]`としてBACKLOG_DONE.mdへ記録。
`[[HYPECORE-SUBSTAGE-LAYER3-UNVERIFIED-1]]`（優先度：低）も登録。
「次セッションでの着手順序」欄を更新：①フェーズD Step2-5（⑤stock.html
フロントエンド＋診断・補助スクリプト7件、主要4消費者パイプライン
完了に伴う残る最後のフェーズD対象）②`[[LAYER3-FETCHER-SELECTION-
PHILOSOPHY-MISMATCH-1]]`（Step2-2で保留中のSTONKS SILO fetcher.py
設計判断、並行して選択可能）③フェーズE（`normalized/`廃止、Step2-5
完了後）の3項目を明記。

最終更新: 2026-08-07（フェーズD Step2-4（HypeCore）事前調査（読み取り
専用）を反映。`hypecore.py::fetch_quarterly_fundamentals()`は
`reader.py`共通アクセサのみでnormalized/を参照（独自インライン実装
なし）、対象母集団は104銘柄（`hypecore=true`、ほぼ全銘柄ユニバース）
と確認。104銘柄全数のLayer3事前差分シミュレーションでRevenue 2/104
（ASTS/RCAT、既知パターン）・NetIncome 4/104（CEG/CWAN/DDOG/BROS、
うちDDOGはLayer3側が異常な30日フラグメントを正しく除外する改善を
実測）・OCF 0/104差分ゼロを確認。差分がpoc.json表示（2024年以降）に
及ぶASTS/RCAT/DDOGの3銘柄について`determine_stage()`を実際に実行し
ステージ判定への影響ゼロ（32ヶ月×3銘柄すべて一致）を確認。substage
（別ロジック、rev_yoy/eps_surprise直接参照）は範囲外として
`[[HYPECORE-SUBSTAGE-LAYER3-UNVERIFIED-1]]`（優先度：低）で記録。
実装コード変更・データ再生成なし（BACKLOG登録のみ）。

最終更新: 2026-08-07（フェーズD Step2-3（TANUKI TAIL）実装完了。
`quarterly_review_generator.py`・`tail_dcf_bridge.py`の
normalized/参照をSEC EDGAR Layer3（`layer3_builder.py::
build_ticker_store()`/`get_quarterly_series()`/`get_latest_
quarterly()`）経由に個別切替。10銘柄全数比較で差分ゼロ、
report_consistency_check.py NG=0・WARN=78件（不変）、pytest 505
passed/2 known failed（既知のみ）。完了記録は`[[SEC-EDGAR-LAYER-
DESIGN-PHASE-D-STEP2-3]]`としてBACKLOG_DONE.mdへ記録。「次セッション
での着手順序」欄をフェーズD Step2-4（④HypeCore）に更新。STONKS SILO
の`fetcher.py`（年次データ）切替は`[[LAYER3-FETCHER-SELECTION-
PHILOSOPHY-MISMATCH-1]]`の設計判断待ちのまま並行して選択肢として
残置（Step2-4着手前に対応してもよい）。

最終更新: 2026-08-07（フェーズD Step2-3（TANUKI TAIL）着手前の使用実態
調査（読み取り専用）を反映。`quarterly_review_generator.py`・
`tail_dcf_bridge.py`はいずれも`reader.py`共通アクセサ（独自インライン
実装なし）のみでnormalized/を参照しており、対象母集団は105銘柄でも
STONKS SILOの25銘柄でもなく、実データが存在する3銘柄（PLTR/SOFI/
TSLA、ポジション登録10銘柄中）と訂正。10銘柄×5フィールド全数の
Layer3事前差分シミュレーションで差分ゼロを確認した一方、
`[[LAYER3-SHARESDILUTED-TAG-GAP-1]]`の対応がpipeline.py限定実装で
あり本2ファイルの`get_latest_quarterly()`直接呼び出しには及ばないため
`[[TAIL-SHARESDILUTED-Q4-TIMING-RISK-1]]`（優先度：低、現状実害なし）
を新規登録。TANUKI TAIL独自の「Layer3」用語（AI KPI抽出、SEC EDGAR
Layer3とは別概念）との衝突に注意する旨も記録。実装コード変更・データ
再生成なし（BACKLOG登録のみ）。

最終更新: 2026-08-07（フェーズD Step2-2（STONKS SILO）実装完了。
`financial_trend_calculator.py`のnormalized/参照をLayer3
（`layer3_builder.py::get_field_entries()`）経由に切替（`fetcher.py`は
`[[LAYER3-FETCHER-SELECTION-PHILOSOPHY-MISMATCH-1]]`の対応方針決定待ちで
現状維持、`analyzer.py`は変更不要と確認済み）。25銘柄全数比較で25/25
銘柄に差分が生じたが、パーセンタイル母集団の連鎖効果・GrossProfit
バックフィル改善・AVAV/ESTCのYoY計算停止解消（good side effect、
normalized/側に`q4_implied.py`集約以前の旧世代`fp:"implied"`ラベルが
残存していたことが原因と判明）・RCATの既知パターンのみで、いずれも
許容範囲・改善方向と確認。`SUB_FIELDS`（SM/SBC）が`compute_vectors()`
から現状呼び出されていない未使用の定数と判明したため
`[[FINTREND-SM-JOBY-NONE-1]]`に補足を追記。完了記録は
`[[SEC-EDGAR-LAYER-DESIGN-PHASE-D-STEP2-2]]`としてBACKLOG_DONE.mdへ
記録。report_consistency_check.py NG=0・WARN=78件（不変）、pytest 505
passed/2 known failed（既知のみ）。「次セッションでの着手順序」欄を
更新。

最終更新: 2026-08-07（フェーズD Step2-2（STONKS SILO）着手前の使用実態
調査（読み取り専用）を反映。`financial_trend_calculator.py`・
`fetcher.py`・`analyzer.py`の実装・25銘柄（`stonks_silo=true`）全数の
Layer3事前差分シミュレーション結果から、新規課題4件を登録:
`[[LAYER3-FETCHER-SELECTION-PHILOSOPHY-MISMATCH-1]]`（優先度：高。
fetcher.pyの年次データ選択思想がLayer3〈filed日最新優先〉とparser.py
〈own-year優先〉で異なり、単純差替えでPL/CF系年次データのほぼ全セルが
変わることをAVAV実測で確認。フェーズD Step2-2完了の前提条件）・
`[[LAYER3-STONKS-SPAC-EARLY-YEAR-GAP-1]]`（優先度：中、①の対応方針
決定後に再評価）・`[[FETCHER-PY-BS-FIELDS-DEAD-KEYS-1]]`（優先度：低、
Layer3移行と無関係の既存デッドコード）・`[[FINTREND-SM-JOBY-NONE-1]]`
（優先度：低、`[[SCHEMA-NORMALIZED-ISSUES-1]]`②の既知帰結）。調査時、
依頼文の「105銘柄」前提が誤りで実際の消費範囲は25銘柄（`stonks_silo=
true`）のみと訂正した。実装コード変更・データ再生成なし（BACKLOG登録
のみ）。コミット・push未実施（ユーザー確認待ち）。

最終更新: 2026-08-06（Layer3統一方針への文書横断整合性確認・修正。
`SEC_EDGAR_LAYER_DESIGN.md`フェーズD（Layer3統合）と
`[[SECDATA-STORAGE-FRAGMENTATION-1]]`が5消費者の移行先（Layer3 vs
data/）で1ヶ月弱食い違ったまま併存していた問題を発見し、本エントリの
対応方針・残タスクをフェーズD方向に統一。分岐の経緯を記録として追記。
`INPUT_DATA_TOBE.md`2-A章の保持構造案に、実際の統合先が`store_v2/`
（Layer3）である旨の位置づけ注記を追加。`FIELD_DEFINITIONS.md`に
TANUKI TAIL側「Layer3」（AI KPI抽出）との用語衝突を記録。以前チャット
上言及のみで未登録だった`[[PARSER-MERGED-TAG-MIXING-RISK-1]]`
（`parser.py::_extract_values_merged()`のタグ混入リスク疑い）を正式
登録（優先度：低）。`CHAT_RULES.md`に再発防止のためのルール3件
（文書横断整合性チェック・根拠のない懸念提示の禁止・確定済み方針の
独自変更禁止）を新設。本セッション追加分が旧セッション（2026-08-05）
の日付表記をそのまま引き継いでいた5箇所を2026-08-06へ訂正。
`PROJECT_STATUS.md`の残タスク記述も同様にLayer3方向へ修正。「次
セッションでの着手順序」欄を更新。実装コード変更・データ再生成なし
（ドキュメントのみ）。機能コミット・BACKLOG更新コミットとも同一
コミットで実施、push済み。

最終更新: 2026-08-05（新DB構築プロジェクト フェーズ1 Step1、
`[[SECDATA-STORAGE-FRAGMENTATION-1]]`対応の一環として`data/
quarterly_{FYQ}.json`のpl/cf/shares区分のYTD→単一四半期(SA)修正を
実装。normalized/→data/統合の事前調査4段階を通じて、`quarterly_*.json`
がXBRL申告のYTD累積値のまま保存されていた（約65〜66%のエントリが
該当）ことが判明し、`quarterly.py::_classify_period()`・
`normalizer.py::_ytd_to_quarterly()`（normalized/側で実績のある
ロジック）を再利用する統一アルゴリズムを`parser.py::
parse_company_facts()`に実装した。手作業シミュレーションが
`parser.py`本体のタグ選定ロジックを正確に再現できず誤った結果を
出したため、実際の`parser.py`関数への直接実装＋メモリ上比較方式に
切り替えて検証し、その後の実書き込み・全105銘柄再パース結果と完全
一致することを確認。annual側は無変化（1,441ファイル横断比較で差分
0件）、report_consistency_check.py NG=0・WARN=78件（不変）、
pytest 497 passed/2 known failed確認。残タスクは新設アクセサ実装・
5本番消費者のnormalized/→data/切り替え。詳細はBACKLOG_DONE.md
「2026-08-05（完了）」参照。コミット・push未実施（ユーザー確認待ち）。

最終更新: 2026-08-05（`[[SCHEMA-NORMALIZED-ISSUES-1]]`④SharesBasic概念
不一致の実害調査完了（読み取り専用）。normalized/側の「SharesBasic」
フィールドはリポジトリ全体で消費者ゼロの死んだフィールドと確認、
data/側の`shares_basic`は`reader.py::get_diluted_shares()`の
異常値フォールバックとしてのみ限定的に参照されると判明。結論として
④自体による実害はなし・normalized/→data/統合の障害にはならないと
確定し、`[[SCHEMA-NORMALIZED-ISSUES-1]]`④の優先度を中→低に格下げ。
副次発見として、フォールバックが現在実際に発火しているONDS・LOARの
2銘柄で、shares_basic自体も同じ桁の異常値を持ち救済不能な疑いが
判明したため`[[ONDS-LOAR-SHARES-SCALE-SUSPECT-1]]`として新規登録
（記録のみ、実装なし）。

最終更新: 2026-08-05（新DB構築プロジェクト フェーズ1 Step1: SEC EDGAR
統合、`[[SECDATA-STORAGE-FRAGMENTATION-1]]`対応の一環として
`common/sec_data/raw/`を削除した。全消費者洗い出し（Step1調査）で
`raw/{TICKER}_quarterly_raw.json`が`quarterly.py`の書き込み専用出力
であり、リポジトリ全体で読み込み側が一切存在しない実質デッドコードと
確認済み。削除前の最終確認（Step0）で`.github/workflows/
SEC_Data_Update.yml`に想定外の参照（`git add common/sec_data/raw/ ||
true`）を新規発見し、これも含めて削除する方針をユーザーに確認の上で
実施。`quarterly.py`の書込処理削除・既存105ファイル（約16MB）削除・
`update.py`のimport整理・`SEC_Data_Update.yml`の該当行削除・
`contracts.py`/`audit.py`のコメント整理を実施。全105銘柄フローズン
検証（`build_raw_table()`+`normalize()`再実行）でnormalized/出力に
`generated_at`タイムスタンプ以外の実質的な差分がないことを確認（検証用の
タイムスタンプ差分は復元しコミット対象から除外）。
`report_consistency_check.py --fail-on-ng`でNG=0（WARN=78件、既存と
不変）、pytest 497 passed/2 known failed（既知）を確認。残タスクは
normalized/→data/統合のみ（別途設計セッション）。「次セッションでの
着手順序」欄を更新。コミット・push未実施（ユーザー確認待ち）。

最終更新: 2026-08-05（[[AVGO-2015-DATA-THIN-1]]原因調査完了（読み取り
専用）。SEC EDGAR一次情報の決算期比較（現行CIK・真の前身候補CIK
1441634はいずれも10月末〜11月初決算、`cik_history.json`登録済みの
旧CIK 1054374は12月31日決算）により、AVGOの旧CIK登録が無関係な買収先
企業（Broadcom Corporation、2016年にAvago Technologies社に買収され
Broadcomへ社名変更）を指している疑いが判明。2006-2014年の「AVGO」
年次データがAvago自身ではなくBroadcom Corpの実績を表している可能性が
あり、2015年欠落はこの誤りの副産物と確認。真の前身企業CIK 1441634
「Avago Technologies LTD」は2016-02-08にForm 15-12B提出で消滅して
おり`cik_history.json`に未登録のまま。実害は現時点でゼロと確認済み
（growth_sanity・roe_10yr_avgとも窓が届く範囲外、fixed_registry.json
はAVGO 2016/2017のみ登録済みで無関係）。原因確定により
`[[AVGO-2015-DATA-THIN-1]]`をクローズし、`[[AVGO-CIK-HISTORY-WRONG-
LEGACY-CIK-1]]`として新規登録（優先度：高、着手条件: 新DB構築フェーズ
1完了後または実害発生時まで保留）。対応方針3案（旧CIK差し替え・
現状維持＋警告・2006-2014年データ削除）を記録、実装は未実施。「次
セッションでの着手順序」欄を更新。コミット・push未実施
（ユーザー確認待ち）。

最終更新: 2026-08-05（[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]
Stage 3b実装完了。SCCO(2010-2019)のgross_profit、RDW(2020)・
ASTS(2020)のBS恒等式修正後の値（total_assets/total_liabilities/
stockholders_equity）を`fixed_by: manual_verification`で
`fixed_registry.json`へ登録した（3銘柄・計12エントリ）。

**登録前確認（SCCO）**: annual_2010.json〜annual_2019.jsonを実測し、
gross_profit値・revenue-cost_of_revenue逆算差分が前回のStage 3調査
時点から不変であることを確認。BACKLOG.md（未完了側）をgrepしたが
SCCOのgross_profit・当該年度に関するOPEN課題は見つからなかった
（唯一の関連言及は既にクローズ済みエントリ内の過去スナップショット
記述）。**新たな発見**: SCCO(2010)は`is_own_data=False`（同一accnの
2011年10-K比較列由来）であり、以前の報告「2010-2019は全年度is_own_
data=True」は不正確だったと判明。ただし`derived`キーはなし（直接タグ
値）であり、genuine定義差の対象母集団として妥当と判断し登録対象に
含めた。

**fields_snapshot特定（RDW/ASTS）**: 依頼は「一時的持分に対応する
実際のフィールド名」の特定を求めていたが、実ファイル確認の結果、
`bs_identity_violations_log.json`のextra_components（一時的持分の値）
は検証専用ロジックがraw XBRLから都度算出するのみで、annual_{year}.json
への書き戻しは一切行われない設計と確認した。したがってfields_snapshot
はStage 2のHEI/LRCX/TSLA/XOMと同じ`total_assets`/`total_liabilities`/
`stockholders_equity`の3項目とした。

**検証結果**: 全105銘柄フローズン再パースで新規12件を含め無変化
（`bs_identity_violations_log.json`10銘柄分の既知の非決定的キー順序
差分のみ発生、復元しコミット対象から除外）。CHECK-31試験発火:
SCCO(2015)を意図的に改変→NG-31検知→復元後NG=0に復帰を確認。
`report_consistency_check.py --fail-on-ng`でNG=0（WARN=78件、既存と
不変）。pytest 497 passed/2 known failed（既知）を確認。「次セッション
での着手順序」欄を更新。コミット・push未実施（ユーザー確認待ち）。

最終更新: 2026-08-05（ASTS(2020) BS恒等式残差$150,596,928を解消。
Step 0でannual_2020.json実測により残差額が前回報告時点から不変と確認
した上で着手。Step 1の全105銘柄机上シミュレーションで、RDWと同じ
「フォールバック機構への追加」案を試したところ、ASTSでは既存の
MinorityInterestのcross-accn一致（$2,490,000）に本タグが後乗せされ
diff=-$2,490,000という不正確な合算（許容誤差内で見かけ上resolvedに
なるだけ）が生じることが判明。一方`_BS_IDENTITY_ALLOWLIST`への無条件
追加案はown-accn一次パスのみでdiff=0の厳密一致となることを確認し、
**RDWとは異なり主許可リストへの無条件追加を採用**
（`TemporaryEquityValueExcludingAdditionalPaidInCapital`は簿価系の
測定基準であり、RDW型のRedemptionValue〈測定基準が異なる開示専用
タグ〉とは性質が異なるため）。全105銘柄シミュレーションで他に影響
したのはFRSH(2020)のみ（解消済み年度に名目値$0.0001が追加一致するのみ、
実質影響なしと確認）。全105銘柄フローズン再パースでASTS/FRSH以外に
差分なし、`report_consistency_check.py`でASTS(2020)分のWARN-29解消・
全体NG=0（ASTS(2019)は別問題として存続）、pytest 497 passed/2 known
failed（既知）を確認。
`[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]`の「②許可リスト拡張で対応
可能」2件（RDW/ASTS）が両方解消。ASTS(2020)のTA/TL/SE等は今後
fixed_registry.json Stage 3登録候補になりうる旨を`[[SEC-DATA-REDESIGN-
OPERATIONAL-POLICY-1]]`へ申し送り（今回は未登録）。「次セッションでの
着手順序」欄を更新。コミット・push未実施（ユーザー確認待ち）。

最終更新: 2026-08-05（RDW(2020) BS恒等式残差$120,314,578を解消。
`_BS_IDENTITY_FALLBACK_ONLY_TAG`を複数タグ対応（`_BS_IDENTITY_
FALLBACK_ONLY_TAGS`）へ拡張し、`RedeemableNoncontrollingInterest
EquityCommonRedemptionValue`を追加（`_BS_IDENTITY_ALLOWLIST`への
無条件追加ではなく、HEI型と同じ安全側のフォールバック機構を採用）。
Step 1で全105銘柄・全既知違反年度の机上シミュレーションを実施し、
無条件追加案・フォールバック追加案の両方でRDW(2020)のみが解消し他104
銘柄・RDW自身の他年度（2019/2021含む）に影響がないことを確認してから
実装。全105銘柄フローズン再パースでRDW(2020)以外に差分なし、
`report_consistency_check.py`でRDW単体WARN=0・全体NG=0、pytest
497 passed/2 known failed（既知）を確認。
[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]の「②許可リスト拡張で対応可能」
はASTS(2020)のみ残存。RDW(2020)のTA/TL/SE等は今後fixed_registry.json
Stage 3登録候補になりうる旨を申し送り（今回は未登録）。「次セッション
での着手順序」欄を更新。コミット・push未実施（ユーザー確認待ち）。

最終更新: 2026-08-05（[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]
Stage 3a実装完了。Stage 3準備調査（BACKLOG_DONE.md各エントリの訂正・
新規登録2件）で特定した対象年度に基づき、MO(2016-2025)・PM(2016-2017)の
gross_profit、LLY(2007-2025)のcapital_expenditure・free_cash_flow・
fcf_method・finance_lease_payments_appliedの計3銘柄・31銘柄×年度
エントリを`fixed_by: manual_verification`で`fixed_registry.json`へ
登録した。

MO/PMは10-K原本のExciseAndSalesTaxesタグ突合によるgenuine業界定義差
確認（Stage 2以前のBACKLOG_DONE.md記載）＋Stage 3調査での対象年度実測を
根拠とする。PMは従来「10年連続」との誤認があったが2016-2017の2年度のみが
対象と訂正済み。LLYはタグフォールバック選定ロジック転換
（コミット`14862976f`）のgit diff直接確認を根拠とし、従来「2023-2025のみ」
という想定を2007-2025全19年度に訂正済み。SCCO(2010-2019)は今回のStage 3a
の対象外（別途対応）。

**検証結果**: 全105銘柄フローズン再パースで新規31件を含め無変化
（`bs_identity_violations_log.json`10銘柄分の既知の非決定的キー順序
差分〈[[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]〉のみ発生、復元し
コミット対象から除外）。CHECK-31試験発火: LLY(2023)を意図的に改変→NG-31
検知→復元後NG=0に復帰を確認。`report_consistency_check.py --fail-on-ng`
でNG=0（WARN=79件、既存と同水準）。pytest 497 passed/2 known failed
（既知の[[TEST-STALE-IV-1]] MSFT/NVDA、新規回帰なし）。

**残タスク**: SCCO(2010-2019)のfixed_registry登録（今回スコープ外）・
RDW(2020)の許可リスト拡張実装・MRVL/AVGO/DELL旧CIK分の個別確認・
AVGO(2015)原因調査・BBAI/RKLB/SOFI/VRT/ONDSグループの検討。「次セッション
での着手順序」欄を更新。コミット未実施（ユーザー確認待ち）。

最終更新: 2026-08-05（[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]
Stage 2実装完了。taxonomy属性①〜⑧該当58銘柄のうち、過去の個別バグ
調査（BACKLOG_DONE.md）とSEC EDGAR一次情報照合（companyconcept API
直接照合）の両方で正しさが確定済みの12銘柄・17銘柄×年度エントリを
`fixed_by: manual_verification`で`fixed_registry.json`へ登録した:
HEI(2020)/LRCX(2012)/TSLA(2018)/XOM(2023)（会計恒等式TA=TL+SE全タグ
網羅確認）、AVGO(2016 revenue・net_income／2017 revenue・
operating_income、SEC EDGAR companyconcept API accn
0001730168-18-000084と完全一致確認）、RCAT(2024
stock_based_compensation)、ELF(2015/2016、10-K原本Selected Financial
Data表と一致確認)、FICO(2019/2020)・CPRT(2019/2020)・LITE(2019)の
revenue（365日正規年次値へのフローズン入力比較検証）、GOOGL(2012/2013、
revenue/operating_income/research_and_development/selling_and_
marketing/gross_profit、SEC EDGAR accn 0001288776-15-000008と完全
一致確認。selling_and_marketingはGOOGL固有のMarketingAndAdvertising
Expenseタグ規約との整合性も確認）、SPIR(2025 net_income・
operating_cash_flow、10-K MD&A一次情報と一致確認)。

**登録前検証で2件を対象外に確定（判定: 対応不要・既に是正済みのため
凍結対象なし）**: VRT(2016)/net_income・SPIR(2020)/long_term_debtは、
候補リスト作成時点のBACKLOG_DONE.md記述（前者は
`[[PERIOD-LENGTH-VALIDATION-GAP-1]]`実装時点、後者は
`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`登録時点の記述）を根拠にしていたが、
本Stage 2実装の登録前検証でannual_{year}.jsonの実ファイルを直接確認した
ところ、**現在は対象フィールド自体が存在しない**と判明した:
- **VRT(2016)/net_income**: annual_2016.jsonの`pl`セクションが完全に空
  （`{}`）。VRT(2016)はSPACシェル期（Vertivと合併前のGS Acquisition
  Holdings Corp）で、PERIOD-LENGTH-VALIDATION-GAP-1完了時点では値が
  存在した可能性が高いが、後続の`[[SPAC-STUB-PERIOD-VERIFICATION-1]]`
  調査で「stockholders_equity/operating_cash_flowのみ残存」と再確定され、
  その過程でPL系フィールドがNone化・削除されたとみられる（両タスクの
  完了日はいずれも2026-08-02で近接しており、実行順序の記録は本セッション
  時点では追跡できていない）。
- **SPIR(2020)/long_term_debt**: annual_2020.jsonの`bs`セクションに
  キー自体が存在しない。`[[SPAC-SHELL-BS-ENTITY-MIXING-1]]`段階2
  （2026-08-01）で該当値$26,645,000が誤った値としてNone化済みであり、
  そもそも凍結すべき正しい値が存在しない。

いずれも**Stage 3（保留・要追加調査）ではなく、この時点で「対応不要」
として判定完了**する。もし将来これらのフィールドに値が再度現れた場合
（例: 候補タグ拡充によるVRT(2016)のPL復旧、RDW(2020)と同型の許可リスト
拡張がSPIR(2020)にも適用された場合等）、その時点で改めてfixed_registry
登録の要否を検討する。

**教訓**: BACKLOG_DONE.mdの記述はその投稿時点のスナップショットであり、
同一領域で後続の別タスク（本件はいずれも同日2026-08-01/02の別エントリ）
が実行されると記述と実データが乖離しうる。fixed_registry登録のような
「値そのものを対象にした」作業では、BACKLOG_DONE.mdの記述を根拠として
そのまま信用せず、登録直前に必ず実ファイル（annual_{year}.json）で
対象フィールドの現存を確認する工程を欠かせない。一般化の要否（
`MIGRATION_CHECKLIST.md`または`EXTRACTION_DESIGN_PRINCIPLES.md`への
反映）は次回セッション終了時のブラッシュアップで検討する（今回は
記録のみ）。

**検証結果**: 全105銘柄フローズン再パースで新規21件を含め無変化
（`bs_identity_violations_log.json`9銘柄分の非決定的キー順序差分〈既知の
[[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]〉のみ発生、復元しコミット
対象から除外）。CHECK-31試験発火: RCAT(2024)を意図的に改変→NG-31検知
→復元後NG=0に復帰を確認。`report_consistency_check.py --fail-on-ng`で
NG=0（WARN=79件、既存と同水準）。pytest 497 passed/2 known failed
（既知の[[TEST-STALE-IV-1]] MSFT/NVDA、新規回帰なし）。

**残タスク: Stage 3**（対象年度・フィールドの追加特定が必要な保留分）:
RDW(2020)〈[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]で別途未解決の残差
$120,314,578が判明、要RedeemableNoncontrollingInterestEquityCommon
RedemptionValue加算〉、MO/PM/SCCO〈gross_profit genuine定義差は確定済み
だが対象年度リストの明示が必要〉、MRVL/AVGO/DELL旧CIK拡張分（MRVL
2007-2018・AVGO 2006-2014・DELL 2007-2013、フィールド別の詳細特定が
必要）、LLY（capital_expenditureの正確な対象年度特定）、BBAI/RKLB/SOFI/
VRT/ONDS（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1で解消済みだが
None化されたBSフィールド名の特定が必要）。「次セッションでの着手順序」欄
を更新。コミット未実施（ユーザー確認待ち）。

最終更新: 2026-08-05（[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]
Stage 1実装完了。fixed_registry.jsonフィックス機構を実データで実測・
実登録した。taxonomy属性①〜⑧非該当銘柄を実測した結果47銘柄（属性
該当58銘柄、前回見積「約55銘柄」から上方修正）、既存チェックゲート
（registration_validator.py・report_consistency_check.py CHECK-1〜29・
revenue_tag_conflict_check.py）全通過の絞り込みを経て**Stage 1最終候補
26銘柄・372銘柄×年度エントリ**を確定・実登録した（revenue_tag_
conflict_check.pyのD&A/S&M系警告は`SEC_DATA_BUG_TAXONOMY.md` #19の
既知誤検知パターンと判断し除外対象から除外、TDYは真のrevenue系競合
`[[REVENUE-TAG-PRIORITY-FRAGILE-1]]`のためStage1から除外）。
`parser.py`（`_apply_fixed_registry_freeze()`、差分適用方式）・
`utils.py`（`compute_snapshot_hash()`）・`report_consistency_check.py`
（CHECK-31/WARN-31、NG化）を実装し、全105銘柄再パースでフィックス対象
372エントリ含め無変化を確認、CHECK-31の発火・復元も確認、pytest
497 passed/2 known failed（既知）、NG=0を確認。機能コミット
`7d7c63faf`。pushは保留、コミットのみ。Stage 2〜3（属性該当58銘柄の
段階的フィックス）が残タスク。「次セッションでの着手順序」欄を更新）

最終更新: 2026-08-03（[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-
MISSELECT-1]]の全105銘柄横断スキャン結果を反映（チャット記録、読み取り
のみ）。不一致は1249年度中13件（1.04%）のみと判明。真のバグは
CRM(2011)・VRT(2017)の2件、CWAN(2023)は構造的に必然（cross-accn、
値は正しい可能性が高い）、9件（ELF/LITE/QBTS/TSLA/BKNG2009/HON/
V2008/DOCN/LYFT）はメタデータのみ不一致で実害なし、CAKE(2009)・
LITE(2014)は別種の異常（total_liabilities欠損、本バグとは無関係）。
根本原因を`_collect_own_data_instant()`のフィールド独立抽出設計と
`_resolve_bs_entity_mixing()`の「本人データaccnが単一」前提の限界と
特定（EXTRACTION_DESIGN_PRINCIPLES.md原則2の新実例）。実害確認:
CRM(2011)は現在の10年ROEトレイリング窓外のため実害なし、VRT(2017)は
窓内のため現在進行形の実害可能性あり（winsorize仕様により影響は限定的
と推測、実測は未実施）。対応方針2案（VRT型・CRM型）を記録し、VRT型
から着手する方針を確定。登録・更新のみ、実装は未着手。

最終更新: 2026-08-03（[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]残り13件の
個別調査結果を反映（チャット記録、読み取りのみ）。①genuine（対応不要）
2件（BKNG2011/2012、Redeemable NCIがFairValue基準のみで簿価タグが
存在しないため既存の許可リスト設計方針と整合的に対応不要と確定）・
②許可リスト拡張で対応可能2件（ASTS2020のTemporaryEquityValue
ExcludingAdditionalPaidInCapital加算・RDW2020のRedeemableNoncontrolling
InterestEquityCommonRedemptionValue、HEI型フォールバックと同型の別タグ名
パターン）・③要さらなる確認7件（PLTR2019・CART2023-2025・V2008・
CELH2025・ASTS2019）に分類。調査の過程でCRM(2011)・VRT(2017)の2件が
CHECK29の対象外（NCI/一時的持分タグ不足ではなく、stockholders_equity
抽出自体が別年度・別filingの無関係な値を誤って採用している独立した
parser.pyバグ）と判明し、[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-
MISSELECT-1]]（優先度：高、新規）として分離登録。「次セッションでの
着手順序」欄を更新。登録・更新のみ、実装は未着手。

最終更新: 2026-08-03（BACKLOG.md統合作業。同一種類の作業をまとめられる
3グループを統合（実装・修正は行わず記録整理のみ）。①normalized/スキーマ
問題群6件（SCHEMA-STDEBT-COVERAGE-GAP-1・SCHEMA-SM-SGA-CONFLATION-1・
SCHEMA-LTDEBT-DOUBLECOUNT-RISK-1・SCHEMA-SHARESBASIC-CONCEPT-MISMATCH-1・
SCHEMA-NORMALIZED-ANNUAL-NAMING-MISMATCH-1・SCHEMA-DA-FALLBACK-MISSING-1）
を`[[SCHEMA-NORMALIZED-ISSUES-1]]`へ統合。②不要ファイル判定待ち4件
（PHASE1-SCAN-CLEANUP-1・BACKFILL-HISTORY-CLEANUP-1・QUALITY-CHECKER-
CLEANUP-1・REPORT-TXT-PARSER-CLEANUP-1）を`[[DEAD-CODE-AUDIT-BATCH-1]]`
へ統合（STALE-SUBPORT-CLEANUP-1は判定基準がリポジトリ外の別システム
〈AutoTrade〉の参照確認を要し、他4件の「grep確認→未使用なら削除」という
共通基準と異なるため統合対象から除外し、既存エントリのまま残置）。
③銘柄リスト重複読み込み3件（SYSHEALTH-CIK-DEDUP-1・TAIL-CIK-LOOKUP-
DEDUP-1・TICKER-SOURCE-CONFIG-DUP-1）を`[[TICKER-LOADING-
UNIFICATION-1]]`へ統合。いずれも旧ID参照を「(旧XXX)」形式で各箇条書きに
残置し、`SEC_EDGAR_LAYER_DESIGN.md`・`layer3_builder.py`等の外部からの
旧ID言及の追跡可能性を維持。DESIGN-8の既知のID重複（8-3/8-4が同一
`[DESIGN-8]`タグを共有）も確認し、`[DESIGN-8-3]`/`[DESIGN-8-4]`へ表記
訂正（他ファイルからの`[[DESIGN-8]]`参照が皆無であることを確認済みの
ため実質的な参照断絶リスクなし）。BACKLOG_DONE.mdの8-1/8-2/8-5/8-6
（完了済み）も同型のID共有パターンを持つが、今回のスコープ外のため
未対応のまま。コミットのみ、pushは保留。

最終更新: 2026-08-03（[[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]実装
完了。CHECK29の本人データ〈own-accn〉限定照合に、cross-accnフォール
バック（同一end_dateの他filingへ探索範囲を拡張）を実装。M&A・組織再編
直後、一時的持分が当該年度自身の10-Kには存在せず後続filingの比較列
としてのみ開示されるケース（COHR2022/2023・CRWV2024・VRT2018）を解消。
実装過程の最初の版で、既存の正しい解消結果を壊す回帰5件（SOUN2021・
PM2010/2011・TSLA2020/2021・HEI2014・FCX2015、いずれも「別タグ族での
同額重複計上」または「own-accnのみで既に完成していた解への不要な追加」
が原因）を検知し、コミット前に復元。2段階ガード
（①ベースゲート: own-accnのみで恒等式が厳密に一致する場合はフォール
バック自体をスキップ、②重複値ガード: 候補値が既にmatched済みの値と
同額の場合は不採用）を再設計し、全105銘柄・全156エントリの網羅的な
before/after比較で回帰5件の再発防止・意図した4件の解消・TSLA(2016)の
精度改善（1件、既存判定は不変）を確認してからコミット。WARN-29は
17件/11銘柄→13件/9銘柄に減少。annual_YYYY.json等の実データは無変更
（検知専用ロジックのため）。pytest 497 passed/2 known failed（既知・
無関係）。機能コミット`b63be0026`・データ再生成コミット`05e7f853d`。
[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]の残件を15件→13件に更新。
「次セッションでの着手順序」欄を更新。pushは保留、コミットのみ。

最終更新: 2026-08-03（[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]の長期的構造
対応（パイプライン統合）の設計調査結果を反映（チャット記録、読み取り
のみ）。当初「parser.py⇔layer3_builder.pyの2パイプライン問題」という
認識を訂正し、`update.py`内で3つの独立生成パス（①parser.py→
annual_*.json、②quarterly.py→normalizer.py→normalized/*.json、
③layer3_builder.py→ttm_calculator.py→ttm/*.json）が並存する構造であり、
SEC_EDGAR_LAYER_DESIGN.mdが既に「3スキーマ併存」として認識済みの既知
課題の一部だったと確定。重複ロジック棚卸しの結果、parser.py側の安全
ロジックの大半（BS系バックフィル等）はTTM出力対象外フィールドで移植
不要と判明し、真に問題になりうるスコープは「FLOW型フィールドの本人
データ優先判定」のみに縮小。統合案A（完全統合・新DB構築フェーズ相当）・
案B（部分統合・個別バグ修正1〜2件相当）・案C（運用チェック継続）を
再評価し、実害ゼロ確定・スコープ限定・新DB構築フェーズD以降の射程・
既存の個別重複許容先例を根拠に案C（運用チェック継続、統合作業は
着手しない）を推奨として確定。着手条件を「案Bのトリガー（TTM anchor
範囲内×FLOW型フィールドの実害発生）」「案A/Bのトリガー（新DB構築
フェーズD着手時）」の2条件保留に更新。登録・更新のみ、実装は未着手。

最終更新: 2026-08-02（セッション終了処理。BACKLOG.md/BACKLOG_DONE.mdの
クロスリファレンス整合性を確認（本セッションでクローズした7件
〈[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]・[[GOOGL-FACT-
OVERRIDE-SEQUENCING-BUG-1]]・[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]・
[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]・[[TTM-CALC-QUARTER-CONTIGUITY-
UNCHECKED-1]]・[[KULR-CAPEX-TTM-STUB-ENTRY-CONTAMINATION-1]]〉が
BACKLOG.mdに残存していないこと、双方向の[[...]]参照が機能していることを
確認済み。DESIGN-8・UI-DISCOVER-1のID重複は本セッション以前からの既知の
構造的経緯のため今回は対応せず記録のみ）。作業ツリークリーン確認済み。
「次セッションでの着手順序」欄を最終整理（[[TTM-DATA-DRIFT-BEHIND-
PIPELINE-1]]を①に、以降指定順で再構成、[[XBRL-UNIT-SCALE-MISMATCH-
DETECTION-1]]はリストから除外）。PROJECT_STATUS.mdのcommon/sec_data/
統合フェーズ1備考欄・更新日も、セッション最終盤の構造的発見
（layer3_builder.pyとparser.pyの独立パイプライン問題）を反映して更新。
登録・整理のみで実装は未着手）。

最終更新: 2026-08-02（[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]の影響実測
結果を反映（チャット記録、読み取りのみ）。7件の既知修正
（[[PERIOD-LENGTH-VALIDATION-GAP-1]]・[[SPAC-SHELL-BS-ENTITY-
MIXING-1]]・[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]・
[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]・[[GOOGL-FACT-OVERRIDE-
SEQUENCING-BUG-1]]・[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]・
[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]）について、TANUKI VALUATION・
STONKS SILOいずれも現在進行形の実害はゼロと確定。BS項目・shares系は
TTM出力（FLOW_FIELDS）に構造的に含まれず消費経路もannual_*.json直接
参照のため無関係、その他は対象年度が現在のTTM anchor範囲（2021〜2022年
始まり）の外のため無関係、STONKS SILOはTTM/layer3を一切参照しない独立
パイプラインのため無関係、と確認。ただし2つの独立パイプラインが同期
しない構造的脆弱性自体は温存されているため、優先度を「高」→「中」に
引き下げつつエントリは残置。短期的運用対応・長期的構造対応の2案を記録。
「次セッションでの着手順序」欄を更新。登録・更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]の内容を確定
（チャット記録、読み取りのみ）。GitHub Actions APIでワークフロー実行
履歴を確認した結果、`SEC Data Update`ワークフロー自体は正常稼働中
（毎週日曜success、無効化なし）で、単なる週次発火タイミングの問題と
判明。一方、より深刻な構造的発見: `common/sec_data/ttm/`を生成する
`layer3_builder.py`は`parser.py`（annual_YYYY.json生成）とは完全に
独立した別実装のパイプラインであり、`fact_overrides.json`も読み込まず
`_resolve_bs_entity_mixing()`等annual側の主要ロジックも実装されていない
ことを確認。結果、本セッションの修正（[[PERIOD-LENGTH-VALIDATION-
GAP-1]]・[[SPAC-SHELL-BS-ENTITY-MIXING-1]]・[[TOTAL-LIABILITIES-
FALLBACK-TAG-DESIGN-FLAW-1]]・[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]・
[[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]・[[COHR-SHARES-DILUTED-UNIT-
SCALE-BUG-1]]・[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]）はワークフローが
正常実行されてもTTM系列には反映されない（唯一の例外は
[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]、ttm_calculator.py自体への
実装のため次回実行で全105銘柄に自動反映）。対応方針を確定: まずTANUKI
VALUATION・STONKS SILOの実消費への影響を実測確認してから、大規模な
layer3_builder.pyへの個別移植の要否・優先度を判断する。「次セッション
での着手順序」欄を更新。登録のみ、実装は未着手）。

最終更新: 2026-08-02（[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]を新規登録
（優先度：高）。[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]実装検証時に
発見した「common/sec_data/ttm/配下が2026-07-26生成のまま、以降の
layer3_builder.py/q4_implied.py〈2026-07-30〉・parser.py〈2026-08-02〉
側のパイプライン修正に追従せず陳腐化している」という事象について、
既存BACKLOG.md/BACKLOG_DONE.mdに独立登録がないことをgrepで確認した
うえで新規登録した。PEP実測（SG&A約9.5%差）・`.github/workflows/
SEC_Data_Update.yml`（毎週日曜自動実行の既存ワークフローの存在、なぜ
2026-07-26以降ttm/が更新されていないかは未確認）を記載。対応方針は
未定、まず陳腐化の実際の範囲（何銘柄・何フィールド）とワークフロー
実行履歴の確認調査が必要。「次セッションでの着手順序」欄を更新。登録
のみ、実装は未着手）。

最終更新: 2026-08-02（[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]実装
完了。`ttm_calculator.py`に`_last4_is_contiguous()`（合計スパン305-425日・
隣接ギャップ±10日）を新設し`calc_ttm_series()`のlast4選定直後に挿入
（機能コミット`e2892a91f`）。実装中に、eps_basic/eps_dilutedを対象外
とする除外を実装し忘れ99/105銘柄が誤って影響を受ける不具合を発見し
即座に是正（`CONTIGUITY_CHECK_EXEMPT_FIELDS`追加）。該当18銘柄のTTM
系列を再生成（データコミット`426b4fa2f`、対象外の87銘柄は無変化を
確認の上で意図的に据え置き）。`pipeline.py`試験実行によりRCAT・KULRの
IV影響を実測しΔIV=$0を確定（`FCF外れ値`検知時の代替推定オーバーライドが
fcf_avgの値によらず同一の理論株価を出力するため、当初見立てていた
「約20%改善がIVに反映される」は誤りと訂正）。FROGはTTM系列を維持し
投資適格性の結論に変化なし。report_consistency_check.py NG=0・
pytest 519 passed/2 known failedを確認。[[TTM-CALC-QUARTER-CONTIGUITY-
UNCHECKED-1]]・[[KULR-CAPEX-TTM-STUB-ENTRY-CONTAMINATION-1]]をいずれも
BACKLOG_DONE.mdへ移動。「次セッションでの着手順序」欄を更新。pushは
保留、コミットのみ）。

最終更新: 2026-08-02（[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]の実装前
最終シミュレーション完了（チャット記録、読み取り・オフラインシミュレー
ションのみ）。重要な設計上の発見: 「不完全な四半期の代わりに古い代替
4四半期を探索する」設計は、KULRで試験実装した結果、正規四半期を巻き
添えで飛ばし約6ヶ月古いデータを現在時点のものとして無自覚に混入させる
危険な挙動が判明したため不採用とし、単純に`quarters_used=0`とする保守的
設計を採用確定。該当18銘柄中FCF自体に変化が生じるのはRCAT・KULR・FROGの
3銘柄のみ、他87銘柄・PEP等の正当ケースで新規誤検知なしを最終確認。
重要な訂正: KULR・RCATともにTTM系列の完全点数不足で年次実績への完全
フォールバックが発生することが判明し、KULRのfcf_avgは約20%改善
（前回試算2.7%より大幅に大きい）・RCATは約59%改善（既報告の34〜55%
過小評価の枠組みより大きい変化、ただしΔIV=$0の結論は別経路のオーバー
ライドにより引き続き有効と推定）。実装設計を確定（calc_ttm_series()内
last4選定直後に連続性チェックを挿入、既存のTTM-QUARTERS-CHECK-1と自然に
統合）。[[KULR-CAPEX-TTM-STUB-ENTRY-CONTAMINATION-1]]は本実装で自動解消
される旨を追記。「次セッションでの着手順序」欄を更新。登録・更新のみ、
実装は未着手）。

最終更新: 2026-08-02（[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]の105
銘柄横断スキャン完了（チャット記録、読み取りのみ）。eps_basic/eps_diluted
は既知・実害なしの仕様のため対象外と確定。除外後18銘柄が該当し、①RCAT型
（標準タグの一時的空白、既報告・ΔIV=$0で確定済み）②タグ切り替え・段階的
移行型（5銘柄、FCF中核フィールド非該当）③本人データ側の異常エントリ型
（新規発見、KULR/FROG）の3タイプに分類。KULRは開始日欠落の異常エントリ
（$2,000,000）がcapital_expenditureに混入し、2024年度で約10.8倍・2023
年度で約30%過大、fcf_avgが約2.7%変化する現在進行形の実害を確認し
[[KULR-CAPEX-TTM-STUB-ENTRY-CONTAMINATION-1]]として新規登録（優先度：
高）。FROGは同型だが影響僅少。対応方針の実現可能性を確認: 「合計スパン
305〜425日」「隣接四半期間ギャップ±10日以内」の統一チェックで3タイプ
全てを検知できることを確認、個々の四半期長は判定基準に含めない（PEP等
の正当な決算暦特性を誤検知しないため）。実装前には全母集団シミュレー
ションが必要。「次セッションでの着手順序」欄を更新。登録・更新のみ、
実装は未着手）。

最終更新: 2026-08-02（[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]実装完了。
`fact_overrides.json`にCOHR(2009-2011)のshares_diluted/shares_basic
（単位スケール補正、値は事前確定済み）を追加（機能コミット`82e25d92d`）。
GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1で確立済みの`_apply_fact_overrides()`
がそのまま機能し、コード変更は不要と確認。COHR再生成（データコミット
`3896f7393`）でshares_diluted/basicを3年度とも是正、net_income/eps系は
無変化、NI≈EPS×Sharesの恒等式が1%未満の誤差で成立するようになったことを
確認（修正前は約1000倍の乖離）。105銘柄フローズン入力比較でCOHR以外は
0件差分、report_consistency_check.py NG=0・WARN 81件（変化なし）、
pytest 519 passed/2 known failed（既知・無関係）を確認。TANUKI VALUATION
（get_diluted_shares()は直近1年度のみ参照）・STONKS SILO（COHRは
stonks_silo=falseで追跡対象外）いずれも影響なしと確定。同エントリを
BACKLOG_DONE.mdへ移動。「次セッションでの着手順序」欄を更新。pushは
保留、コミットのみ）。

最終更新: 2026-08-02（[[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]の実装前
最終確認（チャット記録、読み取り・オフラインシミュレーションのみ）完了。
既存の恒等式ベース安全網（`_backfill_total_liabilities_via_identity()`・
[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]）との相互作用リスクは
なし（BS項目とshares項目でフィールド集合が重ならず構造的に相互作用
経路が存在しない）と確認、前回懸念したWMT(2014)型のすり抜けもガード
条件により正しく除外されることを確認。ガード適用後の全母集団シミュ
レーションで該当・変化するのはCOHR(2010)のshares_diluted/basicの2
フィールドのみと最終確定。実装方針を確定: [[COHR-SHARES-DILUTED-
UNIT-SCALE-BUG-1]]の`fact_overrides.json`個別上書き（3年度とも1回で
解決）を実装対象とし、tie-break変更（ソースコード変更）は当面見送る
（2010年度1件しか解決せずfact_overrides側で重複解決される・現時点で
COHR以外に該当する実ケースがゼロと確定しコストに見合う価値が現状ない
ため。ガード条件の設計自体は破棄せず将来の予防的対応として保留）。
着手条件を更新。登録・更新のみ、実装は未着手）。

最終更新: 2026-08-02（セッション終了処理。BACKLOG.md/BACKLOG_DONE.mdの
クロスリファレンス整合性を確認（本セッションでクローズした5件
〈[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]・[[GOOGL-FACT-
OVERRIDE-SEQUENCING-BUG-1]]・[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]〉が
BACKLOG.mdに残存していないこと、双方向の[[...]]参照が機能していることを
確認済み。DESIGN-8・UI-DISCOVER-1のID重複はいずれも本セッション以前から
存在する既知の構造的経緯（DESIGN-8はサブタスク8-1〜8-6の共有ベースID、
UI-DISCOVER-1は同一IDの別タスクへの再利用）であり、本セッションの作業
とは無関係のため今回は対応せず記録のみ）。作業ツリークリーン確認済み。
「次セッションでの着手順序」欄を最終整理（[[XBRL-UNIT-SCALE-MISMATCH-
DETECTION-1]]を①に、[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]は密結合の
ため①内に統合表示）。PROJECT_STATUS.mdのcommon/sec_data/統合フェーズ1
備考欄・更新日も本セッション後半の完了項目を反映して更新。登録・整理の
みで実装は未着手）。

最終更新: 2026-08-02（[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]の全母集団
シミュレーション（チャット記録、読み取り・オフラインシミュレーションの
み）の結果、当初提起した「tie-break条件を新しいfiling優先に単純変更
する」という方針は不採用と確定。31銘柄・124件で値が変化し、確実な改善は
COHRの2件のみで、残り122件は改悪（VZ(2008)純利益が黒字$6,428M→赤字
-$2,193Mに反転等）・改悪疑い（SOUN/KULRのSPAC実体混同、HON/FCX/HEIの
restatement・株式分割調整）が大半。WMT(2014)では既存の恒等式ベース
安全網が偶発的にすり抜け[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-
FLAW-1]]型のバグを別経路で復活させかねない相互作用リスクも発見。
「同符号かつ比が10のべき乗値」というガード条件を適用すると124件中
COHRの2件のみが該当することを確認し、ガード条件付き介入として
[[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]に統合・実装方針を追記。
[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]は「解消・統合」として
BACKLOG_DONE.mdへ移動。「次セッションでの着手順序」欄を更新。登録・
統合のみ、実装は未着手）。

最終更新: 2026-08-02（[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]の対応方針を
確定（チャット記録、読み取り・オフラインシミュレーションのみ）。COHR個別の
是正は`fact_overrides.json`個別上書き（GOOGLと同型）に確定、値は2009年度
60,164,000/59,334,000・2010年度61,504,000/60,304,000・2011年度
63,612,000/62,211,000（shares_diluted/basic）。「後続filing優先」への
一般設計変更は不採用（2011年度は本人データ優先ロジックが他銘柄で正しく
機能しており巻き添えリスク大、2009年度はそもそも後続filingに正しい値が
存在せず解決しない）。調査過程で2件を新規分離登録: 本人データ不在時に
複数比較年度再掲が競合すると最も古いfilingが勝つ未文書化tie-break欠陥
[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]（優先度：中〜高、COHR2010で実証）、
同一タグ・同一期間の値が複数filing間で10のべき乗単位（1000倍等）で乖離
する場合を検知する汎用チェック提案[[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]
（優先度：中、105銘柄試験適用で18銘柄・126件を検出）。「次セッションでの
着手順序」欄を更新。登録・更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]実装完了。
影響範囲確認（チャット記録、読み取り・オフラインシミュレーションのみ）で
fact_overrides.json対象がGOOGL(2012/2013)限定であること、逆算バックフィル
との重複入力がrevenueのみ（→gross_profit逆算にのみ影響）であることを確認
した上で、案A（`_apply_fact_overrides()`を全逆算バックフィルより前に移動）
を採用して実装（機能コミット`ba8628198`）。extracted[field]["annual"]
[year]構造への書き込みに作り直し、`_parse_raw_data()`内で抽出直後・
`_backfill_total_liabilities_via_identity()`/`_backfill_gross_profit_
from_revenue_cogs()`より前で実行するよう変更。GOOGL再生成（データコミット
`dd6fba1a1`）でgross_profitを是正（2012: $32,999M→$28,863M、2013:
$37,832M→$33,526M）。105銘柄フローズン入力比較でGOOGL(2012/2013)以外は
0件差分・全19年次/51四半期も他の変化なしを確認。report_consistency_
check.py NG=0・WARN 81件（変化なし）、pytest 519 passed/2 known failed
（MSFT/NVDA、既知・無関係）を確認。TANUKI VALUATIONはgross_profitを参照
しておらずSTONKS SILOの追跡対象にもGOOGLは含まれないため影響なしと確定。
同エントリをBACKLOG_DONE.mdへ移動。「次セッションでの着手順序」欄を更新。
pushは保留、コミットのみ）。

最終更新: 2026-08-02（[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]
の残る3種（GP≠Revenue−COGS・OI>GP・NI≠EPS×Shares）の分類調査結果
（チャット記録、読み取りのみ）を反映し、同エントリを「分類調査完了・
後継タスクへ引き継ぎ」としてBACKLOG_DONE.mdへ移動しクローズ。GOOGL
(2012/2013)のGP≠Revenue−COGSは`fact_overrides.json`によるrevenue手動
補正が`_backfill_gross_profit_from_revenue_cogs()`より後段で実行される
シーケンシングバグと確定し[[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]
（優先度：中〜高）として新規登録。LMT(18/19年度)のOI>GPは同一accn・
非derivedの安定パターンから①genuine（設計スコープ外、対応不要）と確定。
COHR(2009-2011)のNI≠EPS×Sharesは、COHR自身のFY2011 10-Kが
shares_dilutedを実際の1/1000でタグ付けしていた本人データ側の単位
スケール申告誤りと確定し[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]
（優先度：中）として新規登録。「次セッションでの着手順序」欄を更新。
登録・クローズのみ、実装は未着手）。

最終更新: 2026-08-02（[[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]を
新規登録（優先度：低）。CHECK29のHEI・ONDS実装検証時、PM銘柄の
`bs_identity_violations_log.json`でキー順序のみが実行のたびに非決定的に
変化する現象を発見（Python `frozenset`のハッシュランダム化が原因と推定、
値・resolved状態は完全に同一で実害なし）。登録のみ、実装は未着手）。

最終更新: 2026-08-02（[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]のHEI・
ONDS型を実装完了。CHECK29の許可リストに`TemporaryEquityRedemption
Value`（CarryingAmount系タグ不在時のフォールバック限定）・
`RedeemableNoncontrollingInterestEquityCarryingAmount`のSUPERSEDES
ルールを追加（機能コミット`a910afef2`）。全105銘柄で再検証し156件中
133件→139件が解消（HEI×5・ONDS×1）、副次的にFCX(2013)も改善、他99
銘柄・既存133件・COHR型2件・残り15件のresolved状態は維持を確認。
annual_YYYY.json等は無変更、pytest 497 passed/2 known failed、
WARN 83→81件（-2）を確認。「次セッションでの着手順序」欄を更新。
BACKLOG更新コミットは機能コミットとは別）。

最終更新: 2026-08-02（[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]の個別調査
（COHR・HEI・ONDS優先、チャット記録、読み取りのみ）完了。3件とも
①genuineと確定（②タグ選定バグに分類されるものはなし）。COHR(2022/2023)
はCHECK29の「本人データ限定」照合という設計方針そのものが原因で検知
不可能な構造的限界と判明し[[CHECK29-COHR-CROSS-ACCN-TEMPORARY-
EQUITY-1]]として別スコープで新規登録（優先度：中）。HEI(2009-2013)は
TemporaryEquityRedemptionValueをCarryingAmount系タグ不在時のフォール
バックとして許可リストに追加すれば対応可能と判明。ONDS(2023)は
CHECK29自体のSUPERSEDESルール不備（自己申告）と判明、既存ルールと
同型の拡張で対応可能。残る20件（PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/
VRT/RDW）は未着手のまま。「次セッションでの着手順序」欄を更新。調査・
登録のみ、実装は未着手）。

最終更新: 2026-08-02（[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]
実装完了。会計恒等式TA=TL+SE(+NCI+一時的持分)検証をOR条件フォールバック
方式（許可リスト方式のタグ選定）でparser.py・report_consistency_
check.py（CHECK-29/WARN-29）に実装（機能コミット`bd91000f0`）。全105銘柄
で検証し156件中133件が拡張形で解消・23件が未解消（事前シミュレーションと
完全一致）、既存1,085件への新規誤検知なし、annual_YYYY.json等の既存
データ値は無変更（新規bs_identity_violations_log.json 105件のみ追加）、
pytest 497 passed/2 known failed、WARN 70→83件（純増13件、全てWARN-29）を
確認。同エントリをBACKLOG_DONE.mdへ移動し、[[CHECK29-UNRESOLVED-23-MIXED-
CAUSES-1]]（着手条件充足）・[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-
MISSING-1]]（TA=TL+SE分の対応完了を反映、残る3種の分類調査は未着手のため
存置）を更新。「次セッションでの着手順序」欄を更新。BACKLOG更新コミットは
機能コミットとは別）。

最終更新: 2026-08-02（[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]
実装前シミュレーション完了（チャット記録、読み取り・オフライン試算のみ）。
当初想定した「TA=TL+SE+NCI+TemporaryEquityへの拡張」を無条件適用する
設計は、既存の正しい1,085件のうち33件（VZ最大-$56.6B・WMT・KO・AVGO・
LLY・AMD・ASTS・BROS・CAKE）で新規誤検知を生む重大な危険があると実証。
「TA=TL+SEが不一致の場合のみNCI・一時的持分を試すOR条件フォールバック
方式」・許可リスト方式のタグ選定に設計を確定。この設計で156件中133件
（85.3%）が解消見込みと判明し、残る23件を
[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]として新規登録（優先度：中）。
検知専用ログフォーマット・report_consistency_check.py側の実装方法・
実装コストの再評価も反映。「次セッションでの着手順序」欄を更新。設計
確定・登録のみ、実装は未着手）。

最終更新: 2026-08-02（[[HEI-LRCX-TA-TLSE-UNEXPLAINED-RESIDUAL-1]]根本原因
調査完了（チャット記録、読み取りのみ）。登録時は「バグ・未特定の会計
恒等式不整合」としたが、対象accn・end_dateの全XBRLタグを機械的に網羅する
手法で再調査した結果、HEI(2020)は`TemporaryEquityCarryingAmountIncluding
PortionAttributableToNoncontrollingInterests`（前回未チェックの別名
タグ）、LRCX(2012)は`TemporaryEquityCarryingAmountAttributableToParent`
（候補には含めていたが確認スクリプトの表示件数制限で該当年度分を見落とし）
で、いずれもTA=TL+SE+NCI+TemporaryEquityが完全一致することを確認。
「誤登録・訂正のうえクローズ（原因は①genuine、探索範囲不足による誤判定
だった）」としてBACKLOG_DONE.mdへ移動。追加でTSLA・XOMもサンプル確認し
完全一致を確認したことで、累計10銘柄が例外なく①genuineに分類され、
[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]のTA=TL+SE違反156件は
ほぼ全件が①genuineへ収束する見込みが高いと判明。同エントリへ追加調査
結果・確定対応方針を追記。「次セッションでの着手順序」欄を更新。訂正・
クローズ・更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]
のTA=TL+SE違反156件・分類調査完了（チャット記録、読み取りのみ）。持続性
区分（単年度28銘柄・2年度5銘柄・3年度以上17銘柄）を確定。8銘柄のサンプル
確認で6銘柄（FCX/BROS/RKLB/GTLB/COHR/ONDS）が①genuine（NCI・一時的持分の
未捕捉、設計スコープ外）と確定、156件の過半数が①に該当する見込みと判明。
HEI・LRCXの2銘柄はNCI等を含めても解消しない未特定の不整合と判明し
[[HEI-LRCX-TA-TLSE-UNEXPLAINED-RESIDUAL-1]]として新規登録（優先度：
中〜高）。恒等式検証の対応方針を「TA==TL+SE+NCI+一時的持分」の拡張形で
確定。「次セッションでの着手順序」欄を更新。分類調査・登録のみ、実装は
未着手）。

最終更新: 2026-08-02（`docs/architecture/new_data_platform/
EXTRACTION_DESIGN_PRINCIPLES.md`を新規作成。common/sec_data/抽出
アーキテクチャの俯瞰的脆弱性分析で判明した5バグの教訓（期間の妥当性・
フィールド間整合性・会計恒等式の3原則）を、これから新設する
`common/market_data/`・`common/macro_data/`向けに一般化。
`MIGRATION_CHECKLIST.md`と同型の位置づけの独立文書。
[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]・[[CHECK29-
ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]から本文書への参照を追記。
CHAT_RULES.mdの「新DB構築プロジェクトの進捗管理」節・PROJECT_STATUS.md
のcommon/market_data/・common/macro_data/行にも参照を追記。作成・登録
のみ、実装は未着手）。

最終更新: 2026-08-02（common/sec_data/抽出アーキテクチャの俯瞰的脆弱性
分析完了（チャット記録、読み取りのみ）。本セッションで発見した5バグ
（[[PERIOD-LENGTH-VALIDATION-GAP-1]]・[[TOTAL-LIABILITIES-FALLBACK-TAG-
DESIGN-FLAW-1]]・[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]・[[SPAC-SHELL-
BS-ENTITY-MIXING-1]]・[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]）が
「候補プールから単純な新しさ基準で1つを確定し、他フィールド・他期間・
会計上の制約とは一切照合しない」という共通の設計的欠陥に帰着すると判明。
105銘柄への機械的予備スキャンでTA≠TL+SE違反156件（50銘柄）・GP≠Revenue−
COGS違反43件（9銘柄、GOOGL(2012/2013)は新規発見）・OI>GP違反22件（LMT
単独、新規発見）・NI≠EPS×Shares違反67件（31銘柄、COHRに単位スケール
バグの疑い）を確認。[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]
（優先度：高、分類調査未着手）・[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-
LAYER-1]]（優先度：高、横断検証レイヤー新設提案）を新規登録。「次
セッションでの着手順序」欄を更新。登録のみ、実装は未着手）。

最終更新: 2026-08-02（[[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-
UNCHECKED-1]]根本原因調査完了（チャット記録、読み取りのみ）。当初の懸念
（継続/非継続タグの取り扱いミス）ではなく、`ttm_calculator.py::
calc_ttm_series()`が採用四半期の日付連続性を検証しない一般的な設計欠陥が
根本原因と判明。RCATでは標準タグの空白（継続/非継続分割開示と決算期変更が
重なった約11ヶ月間）により、2023年7〜10月・10月〜2024年1月の四半期が
`ttm_end=2025-03-31`・`2026-03-31`の両方に重複使用され、現在の
fcf_5yr_avg（-40,185,008.5）・fcf_2yr_avg（-50,540,837.0）が正しい値
（試算：約-53,985,212・約-78,141,244）より34〜55%過小評価と確定。ただし
IVへの影響は現時点でΔIV=$0（revenue floor＋EPSベース推定オーバーライド
が吸収、将来業績改善時に顕在化しうる潜在リスクの留保付き）。他銘柄
（HON/AVAV/TER）への現時点の実害なしと確認。優先度を「高→中」に訂正し、
根本原因（ticker非依存の一般的欠陥）を
[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]として新規登録（優先度：
中〜高）。「次セッションでの着手順序」欄を更新。登録・更新のみ、実装は
未着手）。

最終更新: 2026-08-02（[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]パターンB実装前
シミュレーション完了（チャット記録、読み取り・オフライン試算のみ）。RCATの
本番FCF計算がreader.py::get_fcf_5yr_avg()（年次ファイルベース）を使わず、
data_fetcher.py::_select_fcf_source()がTTM系列
（common/sec_data/ttm/RCAT_ttm_series.json）を優先採用する設計と判明。
TTM系列は四半期10-Qの集計であり年次10-Kの継続/非継続事業分割タグ問題の
影響を受けず既に完全な値を持つため、年次パーサー側のパターンB実装では
RCATのfcf_base_used・DCF・tanuki_score・Classificationは一切変化しない
（ΔIV=$0と試算確認）ことが判明し、優先度を「高→低」に訂正。副次的に
発見したTTM系列生成ロジック側の継続/非継続タグ扱い未検証の問題を
[[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]として新規登録
（優先度：高）。「次セッションでの着手順序」欄を更新。訂正・登録のみ、
実装は未着手）。

最終更新: 2026-08-02（[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-
GAP-1]]TANUKI VALUATION実害確認調査完了（チャット記録、読み取りのみ）。
25銘柄中24銘柄（AAPL/MSFT/TSLA/XOM/CAT/ABBV等を含む）は該当年度がすべて
現在の直近5年窓（2021-2026年）の外にあり実害なしと確定、優先度を「高→
中」に訂正。RCAT単独については、前回（[[FETCHER-10KT-10QT-FORM-
EXCLUSION-1]]）の「成長率決定には影響しない」という限定的確認だけでの
「実害なし」結論を訂正し、`reader.py::get_fcf_5yr_avg()`が実質2021-2023年
の3年平均になっておりDCFのFCFベース値計算に構造的な実害があることを確認、
[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]として新規登録（優先度：高）。「次
セッションでの着手順序」欄を更新。登録・訂正のみ、実装は未着手）。

最終更新: 2026-08-02（[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]根本原因
調査完了（チャット記録、読み取りのみ）。RCATのoperating_cash_flow欠落は
標準タグ`NetCashProvidedByUsedInOperatingActivities`がFY2024フィリングから
継続/非継続事業の分割タグに置き換わったことが原因と確定。105銘柄横断
スキャンで25銘柄該当（AAPL/MSFT/TSLA/XOM/CAT/ABBV等の主力銘柄を含む）する
候補タグ設計欠陥と判明し、`operating_cash_flow`はTANUKI VALUATIONのDCF/
FCF計算に直結するため実害の可能性が高いと判断。「原因確定・スコープ拡大・
統合」としてBACKLOG_DONE.mdへ移動し、
[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]として新規登録
（優先度：高）。「次セッションでの着手順序」欄を更新。登録のみ、実装は
未着手）。

最終更新: 2026-08-02（[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]案③実装完了。
`report_consistency_check.py`にCHECK-28（WARN-28）を新規追加（コード
`1fd44fc0a`）し、company_facts.json上のform=10-KT/10-QTのaccnが
`accn_to_reportdate`に未登録の場合を検知（検知のみ、自動修正なし）。全105
銘柄実行でRCATにWARN-28が2件発火（10-KT・**新規発見**の10-QT
〈2019年、RCAT第1回目の決算期変更由来〉）、他104銘柄で誤検知なし、WARN数
68→70件、NG=0維持。pytest 519 passed/2 known failed。データファイルは
無変更（検知のみ）。案1（relevant_forms追加+バケツ再設計）は見送り確定の
まま、BACKLOG_DONE.mdへ全文移動。「次セッションでの着手順序」欄を更新。
pushは保留、コミットのみ）。

最終更新: 2026-08-02（[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]対応方針を
確定（チャット記録、読み取りのみ）。案1（relevant_forms追加+バケツ再設計）
は見送り。RCAT own-data 10-K・10-KTがSEC自身により両方ともfy=2024と
タグ付けされており真正のバケツキー衝突が発生すること、旧12ヶ月データの
再配置先がないこと、複数消費者の改修が必要になることを確認し、コストが
当初想定より高いと判明。実害は確認済みでゼロ・対象は105銘柄中RCAT1銘柄
限定のため、案3（`report_consistency_check.py`への新規WARN追加のみ）を
採用方針として確定。トリガー条件（RCAT再変更または他銘柄での実害確認）
発生時に案1を再検討する旨を着手条件に明記。副産物として発見した
STONKS SILOのfpラベル脆弱性（fetcher.py側とは独立）を
[[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]として新規登録（優先度：
低〜中）。登録・更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]案b実装
完了。`_align_cost_of_revenue_to_revenue_period()`を新規追加し、
revenue・cost_of_revenueが異なるaccnから独立採用され、かつ数学的矛盾
（revenue−cost_of_revenue≠gross_profit）が現に存在する年度についてのみ、
revenueと同一accn・同一期間の候補で矛盾が厳密に解消する場合に限り置換
（コード`b756021f6`＋安全性修正`9616e8058`・データ`7c94c6f95`）。
**実装検証時に重大な副作用を発見**（初回実装が矛盾のない年度＝GOOGL
(2008)/HON(2008)/SCCO(2009/2010)まで誤って書き換える巻き添え、
gross_profit未確定〈derived前〉年度との比較が原因）し、ゲート条件強化で
是正。最終的に対象はLRCX(2010)の1件のみ、全105銘柄フローズン入力比較で
無変化を確認、report_consistency_check.py NG=0（WARN=68件）、pytest
513 passed/2 known failed。CRM(2013)・JNJ(2017)・MRVL(2017)・ONDS(2017)
は案b単独では未解決のまま残存（案aの対応が必要な可能性）。エントリは
全件解決していないためBACKLOG.mdに残置し、実装結果・残存部分を明記。
「次セッションでの着手順序」欄を更新。pushは保留、コミットのみ）。

最終更新: 2026-08-02（[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]対応方針を
全面改訂（チャット記録、全母集団シミュレーション結果）。案a（候補タグ追加）
・案c（2タグ合算）とも単純適用は既存の正しい値を壊す重大な副作用を確認
（案aはLLY/FCX/CAT/ABBV等で新規劣化10件、案cはENTG/TERで2倍計上・CAT等
6件で破壊）、ゲート条件込みの再設計が必要として保留。案d（revenue側優先
順位変更）は105銘柄202件スキャンで大半がgenuine定義差と判明し不採用確定。
案b（同一accn優先）を採用方針とし、CRM型検知のため期間一致までの精密化
が必要と明記。着手条件に「ゲート条件を伴わない実装は行わないこと」を追加。
登録・更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]内容確定
（チャット記録、読み取りのみ）。残り6銘柄（AMD/BSY/KO/LRCX/ONDS/RMBS）を
個別調査した結果、全6銘柄が②タグ選定バグと確定（①genuine定義差は0件）。
確定9銘柄（AMD/BSY/CRM/JNJ/KO/LRCX/MRVL/ONDS/RMBS）の根本原因を4サブ
パターン（(a)候補タグ完全欠落・(b)クロスaccn/期間不整合・(c)複数タグの
合算漏れ・(d)同一filing内での類似タグ誤選択）に整理。net_income/
operating_income等主要フィールドへの波及なしと確認し、当初想定した重い
「同一期間強制」設計変更は不要と判明、軽量な個別候補タグ拡張（案a・c）
優先の対応方針に更新。着手条件（6銘柄個別確認）を充足済みとして削除。
登録・更新のみ、実装は未着手）。

最終更新: 2026-08-02（セッション終了処理。「次セッションでの着手順序」欄を
最終整理（①PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1 ②FETCHER-10KT-10QT-
FORM-EXCLUSION-1 ③RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1 ④LITE-COGS-
DA-TAG-UNMERGED-1 ⑤HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1
⑥ELF-ROE10YR-RECALC-PENDING-1 ⑦REPORT-CONSISTENCY-GROSSPROFIT-COGS-
CHECK-MISSING-1 ⑧STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1〈クローズ
済み、コード整理のみ将来検討〉の8件）。2026-08-01〜02セッション全体
（gross_profit調査発端の一連の作業）の完了・クローズ・新規登録サマリを
記録。BACKLOG整合性チェック実施、クロスリファレンス双方向・重複なしを
確認。クローズ・更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-
SCCO-1]]個別調査完了（チャット記録、読み取りのみ）。MO・PM・SCCOの3銘柄
を「①genuine定義差、確定・対応不要」としてクローズしBACKLOG_DONE.mdへ
移動（PM/MOはExciseAndSalesTaxesタグ、SCCOはDepreciationDepletionAnd
Amortizationタグが検出diffと完全一致することを10-K原本相当の生データ
突合で確認）。CRM/JNJ/MRVLで確定した「revenue/cost_of_revenue/gross_
profitが異なるaccn・会計年度から独立採用される」設計欠陥を
[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]として新規登録（優先度：中〜
高、[[SPAC-SHELL-BS-ENTITY-MIXING-1]]と同種のフィールド間整合性問題、
残り6銘柄は要個別確認）。LITEのCOGS由来償却費タグ未合算を
[[LITE-COGS-DA-TAG-UNMERGED-1]]として新規登録（優先度：低〜中）。
「次セッションでの着手順序」欄を更新。登録・クローズのみ、実装は未着手）。

最終更新: 2026-08-02（[[SPAC-STUB-PERIOD-VERIFICATION-1]]個別調査完了
（チャット記録、読み取りのみ）。11銘柄・12ティッカー年度すべてで現状の
処理が妥当と確認。SPAC系6銘柄（ASTS/IONQ/JOBY/RKLB/SOFI/SPIR）はBSが
SPAC本体の自己データ（Nasdaq上場要件由来の$5,000,00X型自己資本）、
PL/CFは後年filingの正しい12ヶ月比較列と確認（340-380日フィルタが単純に
None化するだけでなく、正しい代替値を自動的に拾い上げていたことが判明）。
SOUN(2020)・APGE(2022)・NOW(2010/2011)も現状妥当と確認（NOW(2010)の
BS一部欠落は原因未特定だが実害軽微につき注記のみ）。RCAT(2012)は
own-dataで充実、D&A「1日間」エントリはval=0のXBRLタグ付けミスと特定し
実害ゼロと確認。VRT(2016)は当初の記載理由（Emersonスピンオフ）が
事実誤認と判明し、実際はSPAC〈GS Acquisition Holdings Corp〉自身の
設立初年度スタブと訂正（データ自体は正確、実害はほぼゼロ）。
「解消（実害なし、現状の処理は妥当）」としてBACKLOG_DONE.mdへ移動。
「次セッションでの着手順序」欄を更新。クローズ・訂正のみ、実装は未着手）。

最終更新: 2026-08-02（[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]TANUKI
VALUATION/STONKS SILO実害確認調査結果を反映（チャット記録、読み取りのみ）。
TANUKI VALUATIONは実害なし（RCATのgrowth rateはsegment_weighted手動設定が
優先されannual_YYYY.jsonの年度系列・fcf_listを一切参照しないため）。
STONKS SILOは一時的な実害を確認（financial_trend_calculator.py::
_calc_yoy_change()のfpラベル完全一致照合が、8ヶ月しか離れていない新旧
"Q4"を誤って比較しchange_pct=-152.2%という歪んだシグナルを生成していた
可能性、実際に関数実行し数値確認済み）が、データ蓄積により現在は自然解消
済みと確認。優先度を「高→中」に訂正。副産物として発見した
[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（RCATのoperating_cash_flow
完全欠落、10-KT除外バグとは別原因の疑い）を新規登録（優先度：中）。
「次セッションでの着手順序」欄を更新。登録・更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]根本原因
調査完了（チャット記録、読み取りのみ）。3段階目の決算期変更は存在せず、
直近10-Kの12月/4月両クラスタ同時出現はSEC開示規則（Regulation S-X
Article 3-06等）による比較列表示の正常な挙動、era別anchor不一致も対称
探索設計により無害と確認。「解消（実害なし、当初の懸念は誤りだったと
確認）」としてBACKLOG_DONE.mdへ移動。調査中に発見した別種の実害
（RCATの決算期変更移行期スタブ8ヶ月分〈2024-05-01〜2024-12-31〉が
annual_YYYY.jsonから完全欠落。根本原因はfetcher.pyのrelevant_formsに
10-KT・10-QTが含まれずis_own_data判定が恒常的にFalseになるticker非依存の
設計欠落）を[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]として新規登録
（優先度：高）。「次セッションでの着手順序」欄を更新。クローズ・新規登録
のみ、実装は未着手）。

最終更新: 2026-08-02（[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]
実装完了。`SECParser._backfill_total_liabilities_via_identity()`を新規
追加し、貸借対照表恒等式逆算（total_assets − stockholders_equity）で
278件のtotal_liabilitiesをバックフィル（コード`ee46018b2`・データ
`11d75b2c0`）。278件全件で完全一致（許容誤差なし）、全105銘柄フローズン
入力比較で対象278件以外に変化なし、NVDA(2015)/RCAT(2023)で代替候補タグ
値ではなく逆算値が採用されていることを確認。derived provenanceに加え
逆算元データの本人データ有無を示すsource_is_own_dataを新設。
report_consistency_check.py NG=0（WARN=68件、変化なし）、pytest 504
passed/2 known failed（既知）。TANUKI VALUATION（growth.py・DCF/EV計算）
への影響なしを再確認。BACKLOG_DONE.mdへ全文移動。「次セッションでの
着手順序」欄を更新。pushは保留、コミットのみ）。

最終更新: 2026-08-02（[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]の
設計調査＋全母集団シミュレーション結果を反映（チャット記録、読み取り・
オフラインシミュレーションのみ）。278件の内訳をパターンA(恒常的欠如)
14銘柄238件・パターンB(過渡期欠如)8銘柄40件に確定。候補タグのフォール
スルー案は271件で代替候補が存在せずNone化にしかならないため不採用とし、
貸借対照表恒等式逆算（total_assets − stockholders_equity）によるバック
フィルを採用方針として確定（278件全件で計算可能・100%是正可能、
[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]①と同型パターン）。
安全性（既存の正しい値への影響ゼロ・負の自己資本10件でも意味を持つ）を
確認。実装時の留意点として、本人データでない基礎値に依存する11件を
明記。登録のみ、実装は未着手）。

最終更新: 2026-08-02（[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（KULR2019
単独）の根本原因調査完了（チャット記録、読み取りのみ）。原因を
`XBRL_MAPPING["total_liabilities"]`の2番目のフォールバック候補
`LiabilitiesAndStockholdersEquity`（定義上`Assets`と数学的に一致する
誤った代替タグ）と確定。105銘柄への予備スキャンでAMZN/GOOGL/MSFT/NVDA等
大型株を含む278件（銘柄年度）に及ぶ横断的な設計欠陥と判明したため、
[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]をクローズしBACKLOG_DONE.md
「2026-08-02（完了）」へ移動、[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-
FLAW-1]]として新規登録（優先度：高）。downstream影響調査により
Net_Debt/Total_Debt算出への直接汚染はないことを確認済み（`pipeline.py`
内の診断WARN専用の消費のみ）。「次セッションでの着手順序」欄を更新
（①TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1を筆頭に追加）。登録のみ、
実装は未着手）。

最終更新: 2026-08-02（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階2実装完了・
BACKLOG_DONE.mdへ移動（段階1・段階2いずれも完了）。`fetcher.py`で
formerNames（法人名変更履歴）を既存レスポンスから追加取得・保存（新規API
コールなし）、`_resolve_bs_entity_mixing()`にformerNames区間一致による
新トリガー条件③'を追加（コード`1f6e95d92`・データ`43470bccf`）。SPIR(2020)
のlong_term_debtをformerNames一致（triggered_by="former_names_window"）で
新規検知・None化。BBAI/RDW/RKLB/SOFI/VRTは③'でも重複検知されるが結果不変
（冪等性を確認）。全105銘柄フローズン入力比較でSPIR以外に変化なし（RKLBの
2025年再法人化という「単純な改名」ケースでの誤検知なしを含む）。
`spac_shell_detection_log.json`を全105銘柄で新規生成。pytest 473 passed/
2 known failed、report_consistency_check.py NG=0（WARN=68件、変化なし）。
残り99銘柄のformerNamesは通常の週次自動更新で自然にバックフィルされる
設計（特別な一括再取得は未実施）。pushは保留、コミットのみ）。

最終更新: 2026-08-02（セッション終了処理。[[STONKS-SILO-FETCHER-
GROSSPROFIT-BACKFILL-DUP-1]]をクローズしBACKLOG_DONE.mdへ移動（実害解消済み
〈STONKS SILO対象25銘柄で発火条件0件を確認〉、fetcher.py側のコード自体は
デッドコードとして残存・削除ではない旨を明記。コード整理はcommon/sec_data
統合フェーズ1到達時に別途検討）。「次セッションでの着手順序」欄を最終整理
（①SPAC-SHELL-BS-ENTITY-MIXING-1段階2 ②BS-ENTITY-MIXING-UNEXPLAINED-
ONDS-KULR-1 ③RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1 ④SPAC-STUB-PERIOD-
VERIFICATION-1 ⑤GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1
⑥HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1 ⑦ELF-ROE10YR-RECALC-
PENDING-1 ⑧REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1の8件）。
2026-08-01〜02セッションで完了6件・新規登録5件・訂正1件のサマリを記録）。

最終更新: 2026-08-02（[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]①
（本番書き戻し）実装完了・BACKLOG_DONE.mdへ移動。`SECParser._backfill_
gross_profit_from_revenue_cogs()`を新規追加し、標準タグから取得できない
gross_profitをrevenue-cost_of_revenue逆算値で埋め、`pl_provenance.
gross_profit.derived=True`を付与（コード`dc0507c27`・データ`65ddd0d6b`）。
Case A対象34銘柄342件で完全一致を確認、Case B残存49件・他71銘柄は無変化。
STONKS SILO fetcher.pyの重複自己修復ロジック（[[STONKS-SILO-FETCHER-
GROSSPROFIT-BACKFILL-DUP-1]]）はSTONKS SILO対象25銘柄全体で発火条件が
0件になり実質デッドコード化したことを確認（同エントリのクローズ判断材料）。
TANUKI VALUATIONはannual_YYYY.jsonのgross_profitを一切参照しないため
IV・Classificationへの影響はゼロと確定。②（突合検算）は[[GROSSPROFIT-
COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]へ引き継ぎ済み。pushは保留、
コミットのみ）。

最終更新: 2026-08-02（[[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]新規登録
（優先度：低。HON(2009)のgross_profit乖離が[[PERIOD-LENGTH-VALIDATION-
GAP-1]]是正後も残存、他8銘柄は全解消したのに対し既知パターンと異なる原因の
疑い）＋[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]の対象を
MO/PM/SCCOの3銘柄から14銘柄（AMD/BSY/CRM/JNJ/KO/LITE/LRCX/MO/MRVL/ONDS/
PM/RMBS/SCCO）へ拡大訂正。再スキャンでMO/SCCOが各10年連続の持続的乖離、
LITE(9年)・CRM(7年)という当初未記載の大規模クラスタが判明したことを反映。
登録・訂正のみ、実装は未着手）。

最終更新: 2026-08-02（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1実装完了。
`SECParser._resolve_bs_entity_mixing()`を新規追加し、「①複数accn混在・
②本人データaccnが単一に定まる・③現に数学的矛盾が確認できる・④アンカー
統一で実際に矛盾が解消する」の4条件を満たす年度に限定して単一accn強制を
適用（コード`80e51d2c2`・データ`c5e588474`）。条件④はKULR(2019)型の
巻き添えNone化を防ぐため実装中に追加。BBAI(2020)/RDW(2020)/RKLB(2020)/
SOFI(2020)/VRT(2019)/ONDS(2017)/KULR(2016)の7銘柄7年度で数学的矛盾を解消し、
全105銘柄フローズン入力比較で対象7件以外（矛盾のない56件・KULR(2019)・
SPIR(2020)含む）に変化がないことを確認。pytest 461 passed/2 known failed、
report_consistency_check.py NG=0（WARN=68件、変化なし）。優先度を高→中に
訂正（残る段階2はSPIR型の事前検知という予防的対応のため）。pushは保留、
コミットのみ）。

最終更新: 2026-08-02（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]対応方針設計調査結果
を反映。案A（単一accn強制）単独は105銘柄・87件シミュレーションで正常系56件
（41銘柄）を新たにNone化する副作用が判明し不採用と確定。段階1（複数accn混在
かつ数学的矛盾が既に確認されている場合のみ単一accn強制、新規データ取得
不要・副作用ゼロ）と段階2（SPIR型の事故的正しさを事前検知するSPAC合併疑い
機械的検知＝案B、submissions.jsonへのformerNames取得拡張が前提）の二段構成に
整理した。[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]をKULR(2019)単独の
課題に再定義（ONDS(2017)・KULR(2016)は段階1で副次的に解消見込みのため対象
除外。KULR(2019)のみcurrent_liabilities/total_liabilitiesが既に同一accn
〈entity混在ではない〉から採用されているにも関わらず矛盾しており、同一
filing内でのcandidate tag誤選択が原因と確定）。登録・訂正のみ、実装は
未着手）。

最終更新: 2026-08-02（[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]の優先度を
低〜中→中に訂正。ONDS(2017)・KULR(2016)・KULR(2019)の3件とも数学的矛盾＝
実害が確定済みであり「原因未特定」は優先度を下げる理由にならないこと、また
原因が[[SPAC-SHELL-BS-ENTITY-MIXING-1]]と異なりSPAC文脈に限定されない汎用的な
抽出ロジックの欠陥である可能性があり105銘柄全体への影響範囲が未確認である点を
理由とする。更新のみ、実装は未着手）。

最終更新: 2026-08-02（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]対象銘柄にSPIR(2020)を
明示追加（同一パターンだが数学的矛盾は未顕在化の"事故的な正しさ"。対応方針の
設計・検証範囲にBBAI/RDW/RKLB/SOFI/VRTと並べて含める）。[[BS-ENTITY-MIXING-
UNEXPLAINED-ONDS-KULR-1]]を新規登録（優先度：低〜中。ONDS(2017)・KULR(2016)・
KULR(2019)でSPACシェル型と一致しないBS混在＋数学的矛盾を確認。ONDS/KULR2016は
total_assets側の値がcurrent_assetsより著しく過小、KULR2019はtotal_liabilities
とcurrent_liabilitiesの食い違いで、いずれもSPAC実体混在とは異なりtotal_assets/
total_liabilities集計タグ自体の誤選択が疑われる。原因未特定・登録のみ、
実装は未着手）。

最終更新: 2026-08-01（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]新規登録（優先度：高、
登録・調査のみ実装は未着手）＋[[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]訂正
（ELF/KULR除外・BBAI/RDWのPL/CF系は既にNone化済みと確認しクローズ扱いへ）。
[[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]個別調査で、BBAI/RDW 2020のBS系フィールドが
合併前SPACシェルと合併後本体の異なる法的実体から混在採用され、数学的に矛盾
する値（current_assets>total_assets等）が本番稼働中であることが判明。全105
銘柄横断スキャンでRKLB(2020)・SOFI(2020)・VRT(2019)にも同型の数学的矛盾を
確認、SPIR(2020)は同一パターンだが偶然矛盾していない状態を確認。ONDS(2017)・
KULR(2016/2019)は類似症状だがSPACパターンと一致せず別原因の可能性ありとして
対応方針検討の対象外に区分。BS系は期間長フィルタの対象外のため
[[PERIOD-LENGTH-VALIDATION-GAP-1]]では検知不可能だった独立した欠陥系統）。

最終更新: 2026-08-01（[[ELF-ROE10YR-RECALC-PENDING-1]]新規登録、登録のみで
TANUKI VALUATION側のコミット・反映は未実施。[[ELF-FISCAL-END-MONTH-
MISDETECTION-1]]完了時の試験実行で、ELF 2015-2018年度データ是正に伴い
ROE_avg(10yr)が7.0%→9.6%・Alpha_Premiumが0.29→0.40へ変化することを確認
〈TANUKI SCORE分類・Matrix Quadrant/Labelは不変〉。バグではなく是正済み
データに基づく期待された再計算結果のため、通常の定期更新サイクルでの
反映を待つ方針で優先度：中で登録）。

最終更新: 2026-08-01（[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]案②実装完了・
BACKLOG_DONE.mdへ移動。`detect_fiscal_anchor_clusters()`を新規追加し、
`determine_fiscal_year()`にextra_anchors引数を追加、SECParserの5つの
呼び出し箇所全てに配線した（コード`7c44ac266`）。全105銘柄でbucketing
比較を行い、変化があったのはELFのみ（RCAT/AVGO/MSCI/NOWは複数クラスタ
検出も実害ゼロ、単一クラスタの100銘柄は完全不変）を確認。前回除外していた
ELFのannual_2014-2019.jsonをフローズン入力で再生成し除外を解除（データ
`6d9c18b2f`）。2015-2018は真の暦年値に復旧、2014・2019（移行期）はPL/CF
系フィールドをNone化（BS項目は維持）。pytest 453 passed/2 known failed、
report_consistency_check.py NG=0（WARN=68件、変化なし）。TANUKI VALUATION
試験実行でIV/DCF/Growth_Rate（5年FCF窓）は無変化を確認したが、ROE_10yr_avg
（7.0%→9.6%）は変化することを検知（10年窓は2017-2019年度を含むため。
TANUKI SCORE分類は不変、この再生成自体は未実施・未コミット）。
ユーザー指示によりpushは保留、コミットのみ）。

最終更新: 2026-08-01（[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]新規登録、
登録のみで実装・調査は未着手。[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]案②
シミュレーションの過程で、RCATの`detect_fiscal_anchor_date()`クラスタ分析が
直近10-K〈filed 2026-03-19〉を12月31日・4月30日の両クラスタに同時投票させて
いることを発見。RCATは既に決算期を2回変更済みとBACKLOG_DONE.mdに記載済みだが、
今回の重複は3段階目の移行が進行中の可能性を示唆する。現時点でbucketingへの
実害はゼロ〈月のみ比較フォールバックによる「事故的な正しさ」〉だが、将来の
データ追加で均衡が崩れるリスクがあるため優先度：中で登録）。

最終更新: 2026-07-31（[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]案①実装完了。
`detect_fiscal_end_month()`に`detect_fiscal_anchor_date()`と同一の340-380日
必須フィルタを追加し、四半期注記再掲載による得票汚染を除去（コミット
`96c42d8f0`）。全105銘柄で判定結果を新旧比較した結果、変化した銘柄は0件
（ELF/RCAT/AVGO含む全銘柄で不変）。事前見立て通り、この修正単独では
ELF（3月18票 vs 12月11票のまま）・RCAT（12月/(4,30)の食い違いのまま）・
AVGO（12月のままで真のFYE 10月末と不一致）いずれの誤判定も解消せず、
era別対応（案②）が根治に必須であることを実証的に確定した。ELFの
annual_2015〜2019.json 5ファイルは引き続き除外を維持。pytest 447 passed/
2 known failed、report_consistency_check.py NG=0（WARN=68件、変化なし）を
確認。[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]の「対応方針」を案①完了・
案②着手待ちに更新）

最終更新: 2026-07-31（[[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]完了総括の
記録是正＋[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]統合タスク化、報告・登録のみ
実装は未着手）。[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]調査の過程で、
BACKLOG_DONE.mdの[[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]完了総括
（「RCAT型決算期変更検知は解消済み」）が、実際の解決範囲（WARN-24による
検知・ログ記録層のみ、`_own_override_is_safe()`は無改修）より広いラベルで
表現されており、`_detect_fiscal_end_month()`/`_detect_fiscal_anchor_date()`
自体のera別対応（1銘柄が単一のfiscal_end_month/anchorしか持てないアーキ
テクチャ上の限界）は一貫して未着手のまま残っていたことが判明。BACKLOG_DONE.md
のARCH-DATA-1クローズ根拠・冒頭changelog（本ファイル114行目付近）・
「次セッションでの着手順序」欄の2026-07-17〜18付けブロックに訂正注記を追加。
[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]を、ELF単独ではなくRCAT
（2026-07-17から未着手のまま持ち越し）・AVGO（[[PERIOD-LENGTH-VALIDATION-
GAP-1]]で背景要因として既発見）を含む統合タスクとして再定義（優先度：高、
IDは変更せず内容を拡張）。

最終更新: 2026-07-31（[[PERIOD-LENGTH-VALIDATION-GAP-1]]実装完了。
`_extract_single_key()`（gross_profit等9フィールド）・`_extract_values_merged()`
（revenue/S&M/D&A）双方に340-380日の期間長フィルタを追加し、全105銘柄の
annual_YYYY.jsonをフローズン入力で再生成（コード`e3723b3eb`・データ
`d6d404016`）。実際に値が変化したのは28銘柄・194フィールドエントリで、AVGO
revenue 2016/2017の是正値($13,240M/$17,636M)は10-K原本と完全一致。
pytest 446 passed/2 known failed（既知のみ）、report_consistency_check.py
NG=0（WARN 71→68件に減少、新規WARNなし）を確認。STONKS SILOの自己修復
ロジック・TANUKI VALUATIONの直近5年窓への影響も個別確認済み（RCAT 2024の
stock_based_compensationのみ現役銘柄で該当、軽微な是正）。検証過程でELF
固有の別バグ（fiscal_end_month自動検出誤り）を発見しELF分5ファイルは
本コミットから除外、[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]として新規登録。
[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]の着手条件は充足（対応方針
決定・実装は別タスク）。詳細はBACKLOG_DONE.md「2026-07-31（完了）」参照）

最終更新: 2026-07-31（[[PERIOD-LENGTH-VALIDATION-GAP-1]]の追加シミュレーション
（`MERGE_ALL_TAGS_FIELDS`側revenue/selling_and_marketing/depreciation_and_
amortizationの3フィールド）結果を反映（登録・確認のみ、実装・データ再生成は
未実施）。OK約3,487件・b:改善13件（AVGO revenue 2016/2017の是正後値$13,240M/
$17,636Mが10-K原本値と完全一致）・c:新規欠損化12件を確認。対応スコープを
`_extract_single_key()`経由9フィールドに加えこの3フィールドにも拡大し、
tie-breakを候補単一時も含めた無条件340-380日フィルタへ変更する方針を確定。
新規発見のVRT 2016(revenue)・RCAT 2012(depreciation_and_amortization)を
[[SPAC-STUB-PERIOD-VERIFICATION-1]]に追加（9銘柄→11銘柄）。また
2026-07-12完了済み[[SEC-TAG-FICO-CPRT-1]]のFICO/CPRT/LITEについて、無条件
フィルタ適用後もregressionが発生しないことを実コード・実データで個別確認済み
（FICO全18年度・CPRT全17年度・LITE全13年度、合計48年度すべて340-380日の
範囲内で維持）。

最終更新: 2026-07-31（[[PERIOD-LENGTH-VALIDATION-GAP-1]]の全母集団オフライン
シミュレーション結果を反映（登録・訂正のみ、実装・データ再生成は未実施）。
105銘柄×9フィールドで実コード（`_detect_fiscal_end_month()`・
`_detect_fiscal_anchor_date()`・`determine_fiscal_year()`）を読み取り専用で
実行し、現状OK約9,700件・b:改善53件・c:新規欠損化138件を確認。対応方針
（`_extract_single_key()`への340-380日フィルタ追加）の安全性（既存の正しい
約9,700件には影響しない設計）を確認し、同エントリの「対応方針」を確定扱いに
更新。新規発見のMRVL(gross_profit)・COHR/INTU(cost_of_revenue、INTUは
12年連続)を影響範囲に追加。
[[SPAC-STUB-PERIOD-VERIFICATION-1]]からRCAT 2024(stock_based_compensation)
を訂正削除（「決算期変更に伴う正当なスタブ期」との推定が誤りと判明、実際は
正しい年次代替値が存在する[[PERIOD-LENGTH-VALIDATION-GAP-1]]側のb:改善
ケースだったため、対象9銘柄に変更）。

最終更新: 2026-07-31（[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]の調査から
派生した横断調査（登録のみ、実装は未着手）。新規登録6件:
[[PERIOD-LENGTH-VALIDATION-GAP-1]]〈優先度：高。parser.pyのFLOW型フィールド抽出
（`_extract_values_best_candidate()`→`_extract_single_key()`経路）に期間長検証が
構造的に欠落しており、AVGO revenue/net_income/operating_income(2016/2017)・
gross_profit9銘柄(TDY/AVGO/CPRT/ABBV/CAT/FICO/HEI/HON/KLAC)で四半期値が年次値
として誤採用されていたことを確認。2026-07-12 [[SEC-TAG-FICO-CPRT-1]]の対症療法
（revenue等3フィールド限定のtie-break追加）では根本原因が未解消だったことも確定〉・
[[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]〈優先度：高、要個別調査。BBAI/RDW/ELF/KULRで
同一年度内にフィールドごと異なる期間長が混在、predecessor/successor期間混在の疑い〉・
[[SPAC-STUB-PERIOD-VERIFICATION-1]]〈優先度：中。ASTS/IONQ/JOBY/RKLB/SOFI/SOUN/
SPIR/APGE/NOW/RCATの非365日期間データは正当なスタブ期の可能性が高く要個別確認〉・
[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]〈優先度：低〜中。MO/PM/SCCO
の年次同士の乖離は会計上の定義差の疑い〉・
[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]〈優先度：低。gross_profit
逆算ロジックの3箇所重複〉・
[[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]〈優先度：低〜中。
gross_profit/cost_of_revenue整合性の常設監査項目が存在しない〉。
既存[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]の着手条件に
[[PERIOD-LENGTH-VALIDATION-GAP-1]]解消を前提として追記。次回セッション筆頭候補は
[[PERIOD-LENGTH-VALIDATION-GAP-1]]）

最終更新: 2026-07-30（common/sec_data統合フェーズA〜D準備セッション。
[[TTM-PASCALCASE-KEY-STALE-1]]〈Phase C移行によるPascalCase→snake_case
キー不一致バグ、RICEスコア100/100銘柄・FCFフォールバック94/100銘柄への
本番影響を修正〉・[[LAYER3-SGA-Q4-MISSING-1]]〈SGA/cost_of_revenueのQ4
逆算・欠落四半期逆算スコープ漏れ、42銘柄・171四半期影響を修正、
newfield_q4_cutoff_check.py新設〉・[[LAYER3-TTM-REGRESSION-NEWFIELD-
BLINDSPOT-1]]〈TTM回帰比較スクリプトの新規フィールド検証漏れ〉・
[[DOCS-SECDATA-NORMALIZED-DIR-STALE-1]]〈TANUKI TAIL/stock.htmlが参照する
docs/common/sec_data/normalized/の2ヶ月超陳腐化、週次自動同期を追加〉・
[[SEGMENT-FETCHER-DUPLICATE-ORPHAN-1]]〈segment_fetcher.py重複統合〉・
[[LAYER3-COGS-ASTS-LRCX-RECOVERABLE-FOLLOWUP-1]]〈ASTS/LRCXのcost_of_
revenue欠落を一次情報で個別裏取りし両銘柄とも回収不可能と確定、
副産物として`layer3_builder.py::_get_concept_units()`に名前空間対応
コードを追加〉・[[STONKS-SILO-COGS-DEAD-FALLBACK-1]]〈デッドな代替キー
参照削除、副次的にfalsy-zeroバグ(RXRX)も解消〉・[[JNJ-RD-TAG-PRIORITY-1]]
〈research_and_development候補タグ優先順位誤りをSEC EDGAR 10-K原本裏取り
の上で修正、adjustments.py R&D資本化調整の不適用という現在進行形の実害を
解消〉を完了。新規登録・未着手:
[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]・
[[LAYER3-COGS-STRUCTURAL-GAP-16TICKERS-1]]・
[[LAYER3-VISA-EPS-TAG-MISSING-1]]・[[LAYER3-GA-STANDALONE-TAG-UNMAPPED-1]]・
[[LAYER3-CONFIG-RD-TAG-PRIORITY-1]]〈JNJ-RD-TAG-PRIORITY-1と同一の誤りが
config/sec_concept_definitions.json側に残存〉。詳細は各エントリ・
BACKLOG_DONE.md参照。CHAT_RULES.mdへ運用原則2件を追記
〈「バグが0にならなければ次に進まない」・「新セッション開始時は渡された
資料を全文確認する」〉）

最終更新: 2026-07-23（AS-IS/TO-BE設計セッション〈RETROSPECTIVE_2026-07-22.md・
FIELD_DEFINITIONS.md全10フェーズ・CONCEPT_PARAMETER_VARIATIONS.md・
INPUT_DATA_AS_IS.md/TOBE.md〉で発見された未対応事象を一括起票。優先度高
11件〈net_cash/net_income二重計算・stock.html CapEx符号バグ・MACRO PULSE
truthy判定バグ・RECESSION RISK SCORE閾値不一致・Hollow Rally恒久不発火・
Portfolio二重保持・risk_free_rateハードコード・moat_score部分欠損・FCF
CAGR経過年数未補正・Bear/Bull符号反転〉・中19件・低9件、計39件を新規
登録。既存BACKLOG.mdとの重複は確認済みで該当なし。詳細は各エントリの
「発見」欄の根拠ドキュメント参照）

最終更新: 2026-07-22（[[FCF-DIVERGENCE-SIGN-GUARD-1]]実装完了。
divergence_ratio（estimated_fcf/raw_fcf）が符号・境界を無視することで
生じる乖離検知漏れを2段階で解消：第1段階はraw_fcf>0×estimated_fcf<0
の符号反転ガード（コミット`f6201ae04a4e242bbda2014b0f71ca2ef42911b6`）、
第2段階はraw_fcf<=0×estimated_fcf>0の対称ケース（コミット
`99014218b676fa4e36e4babefaf9ce407cac8ba4`）。いずれも既存の閾値判定
（>=2.0/>=5.0）とは独立に無条件で警告を生成する設計とし、回帰テスト
計6件・全100銘柄フローズン入力比較で既存データへの影響なしを確認済み。
FCF-CONVRATE①③（sector未収録銘柄・Damodaran NIベース設計の構造的
脆弱性）を調査し、対象53銘柄中49銘柄でPolicy Bの強制丸めが支配的で
TANUKI SCORE Classificationには無関係と判明したため、根本修正は
見送り現状維持と決定。ARCH-DATA-1をゼロベース棚卸しし、SEC正規化
3段階設計は既に全完了済み（RCAT型決算期変更検知も引き継ぎ先で解消済み）
であることを再確認するとともに、BACKLOG_DONE.md内でStage1/2/3の
完了記録が本体エントリと重複していた問題を解消（コミット
`0316b90f2badd5797a9b3409e0880dd7d98da9fc`）。CHAT_RULES.mdへ教訓3件を
追記: 独立ガード追加時の全象限（符号・境界の組み合わせ）事前洗い出し、
新規発見事象はBACKLOG.md起票を実装依頼に先行させる運用徹底、入力精度
向上に着手する前に下流の丸め・ゲート条件（Policy A/B等）への影響を
安価に確認する。）

最終更新: 2026-07-20（同日2回目: BACKLOG.md/BACKLOG_DONE.md整合性修正。
ARCH-DATA-1・FY52WEEK-BS-NULL-SILENT-1（+統合済みのFY52WEEK-BS-
INSTANT-FACT-1）の2件をクローズしBACKLOG_DONE.mdへ完全移動——ARCH-DATA-1は
3段階設計+残課題④まで全完了、唯一残っていたRCAT型決算期変更検知は
[[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]へ引き継がれ完了済みと確認
（※2026-07-31追記: この完了はWARN-24による検知・ログ記録層のみを指す。
`_detect_fiscal_end_month()`等の抽出ロジック自体のera別対応は含まれておらず、
[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]調査で未解消と再確認した）。
FY52WEEK-BS-NULL-SILENT-1はPhase A・Phase B Stage1-3・Phase C全完了
（Stage2=FY52WEEK-BS-STI-OVERRIDE-DESIGN-1・Stage3=FY52WEEK-BS-
FADEOUT-FALLBACK-1、いずれも完了・分離先タスクへ相互参照済み）。
ANOMALY-PATTERN-CATALOG-1の型C実例（NVDA）・FCF-CONVRATE-DESIGN-LIMIT-1
の発見した別問題（FRSH validator誤FAIL）を、それぞれ対応完了タスクへの
参照に更新。PREVENT-5・TICKER-AUDIT-1にQUALITY-GATES-EPIC-1への統合
マッピング済みである旨を追記（二重実装防止）。DESIGN-15の着手条件
「ARCH-DATA-1完了」を充足済みとして反映。詳細はBACKLOG_DONE.md
「[ARCH-DATA-1]」「[FY52WEEK-BS-NULL-SILENT-1]」参照）

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

#### 着手条件（2026-08-19再訂正）
なし。Phase 1・Phase 2a・Phase 2b-1・Phase 2b-2・Phase 2b-3・Phase 3前提整理・
Phase 3aは完了。Phase 3b（[[GATE2-PHASE3B-1]]、4ファイル統合・規約C/D）も
2026-07-17〜18に①②③-a③-b全項目完了し、BACKLOG_DONE.mdへ全文移動済み。
**Phase 4（ゲート3）の優先順位は2026-08-19に再訂正**——本線3の
`operating_income`第一歩完了後の実測（`[[LAYER3-ANNUAL-CLASSIFICATION-
DROPS-DATA-1]]`・`[[OI-RECONSTRUCTION-MISSING-OPEX-LINES-1]]`の発見）を
踏まえ、Phase 4棚卸しはLayer3範囲実測の次点に位置づけ直した。優先順位の
全体像・判断基準（真値一致ではなく思想↔式↔データの整合性で評価する）は
`CHAT_RULES.md`「本線の定義」の「次の本線候補」参照（重複記載を避けここ
では詳細を繰り返さない）。
（2026-07-22訂正）。

**上記の個々のPhase完了記録は事実（コミットは存在する）だが、「これにより
Phase 3までの目的が達成された」という従来の含意は誤りだったと2026-08-18の
実コード確認で判明したため、着手条件を以下の通り訂正する。**

**未着手として残るのはPhase 4・5だけではない**:
- **ゲート0（登録適格性の機械化）は未着手**。「Phase 3（ゲート0＋2）完了」
  と記載していたが、実際に完了したのはゲート2（`contracts.py`、Phase 3a/3b）
  のみで、ゲート0側は手つかずのまま。詳細は下記「ゲート0の実装状況
  （2026-08-18訂正）」参照
- **ゲート1（Phase 2a〜2b-3）は「複数ソース自動照合・自動補正」という
  設計変更（2026-07-12同日5回目）の適用範囲が限定的なまま**。詳細は下記
  「ゲート1の実装状況（2026-08-18訂正）」参照。次に着手すべきは
  Phase 4（ゲート3）ではなく、**Phase 2（ゲート1）の適用範囲拡大**と
  判断する（Phase 4は「予防設計」であり、`[[OPERATING-INCOME-
  EXTRACTION-GAP-1]]`（2026-08-16）が実害を出したデータ取得層とは
  性質が異なる層のため）
- Phase 4（ゲート3: 全計算式のゴールデンテスト・性質テスト整備、現状ほぼ
  手つかず）・Phase 5（[[TRUST-SUMMARY-EPIC-1]]の再評価）が未着手である
  こと自体は従来の記載通り

ARCH-DATA-1のスコープ拡張（2026-07-16、年次データ正規化3段階設計）
とは対象領域が重複しないため、並行して進めて支障ない。

#### ゲート1の実装状況（2026-08-18訂正）
ゲート1は2026-07-12同日5回目の追記で「取得時データ検証（検知のみ）」から
「複数ソース自動照合・自動補正」へ設計変更された。Phase 2a〜2b-3の完了
記録（上記）はそれぞれ事実だが、この設計変更の核心である**外部ソース
（yfinance）との突合**は、Phase 2a〜2b-3のいずれにも含まれていなかった
ことが2026-08-18の実コード確認で判明した：

| Phase | 実装内容 | 外部ソース突合 |
|---|---|---|
| 2a | SEC内部の候補タグ群から「最新end日優先」で選ぶロジック改善（`tag_definitions.py`） | なし |
| 2b-1 | TTM系列の鮮度チェック（内部の日付比較） | なし |
| 2b-2 | 前年比2.0倍/0.5倍の統計的閾値検知（WARN-21） | なし |
| 2b-3（[[SPLIT-AUTO-CHECK-1]]） | EPS Analyzer独自パイプラインのfact選定ロジック不整合の修正（BACKLOG_DONE.mdの完了記録で確認） | なし（yfinance splits履歴との突合は未実施） |

Phase 2a〜2b-3で変更対象だったファイル（`tag_definitions.py`・
`data_fetcher.py`・`quarterly.py`・`parser.py`・`extract_key_facts.py`）
に`yfinance`の参照は存在しない（2026-08-18確認）。

**ただし「外部ソース突合の仕組み自体が存在しない」わけではない**（当初
そう誤認しかけたが訂正）。`common/sec_data/`配下の診断・監査層には既に
以下が稼働している：
- `report_consistency_check.py` WARN-10: yfinanceのPS比率と自社計算のPS
  比率を突合（2.5倍超/0.4倍未満で警告）。**Gate1設計変更（2026-07-12
  同日5回目）より前から存在する既存機能**であり、Phase 2a〜2b-3の成果物
  ではない
- `audit.py`: `beta_config`とyfinance実測βの乖離チェック
- `registration_validator.py`: P1-Step2-Betaで「raw yfinance値使用中」を
  WARN表示

**したがってゲート1の未達は「仕組みの不在」ではなく「適用範囲の限定」**:
外部照合が適用されているのはPS比率・βという派生的・参考的な指標のみで、
**営業利益・売上・純利益といった損益計算書の中核項目には適用されて
いない**。`[[OPERATING-INCOME-EXTRACTION-GAP-1]]`（2026-08-16）で6銘柄の
営業利益がゼロ扱いされていた問題は、この適用範囲の偏りが直接の原因。
yfinanceはこれら4銘柄（LLY/JNJ/XOM/KLAC）の営業利益を問題なく返すことを
実測確認済み（2026-08-18、`yfinance.Ticker(t).income_stmt`で全件取得成功）。

**着手コストへの影響**: ゲート1の残作業は新規機構の開発ではなく、**既存
のWARN-10と同型のパターンを主要財務数値へ横展開する作業**である。した
がって当初見積もりより着手コストは小さくなる可能性が高い。主な作業は
実装そのものではなく、フィールドごとの閾値の実データ検証（Phase 2b-2で
NG想定がWARNへ格下げになった経緯を踏まえ、誤検知率の確認が必要）。

**本線3・ゲート1第一歩完了（2026-08-19）**: `operating_income`単体を
対象にyfinance自動照合を実装した（既存CHECK-35の拡張、新規CHECK番号
なし）。

- 実装: `common/sec_data/report_consistency_check.py::
  _check_operating_income_reconstruction()`にNone/derived判定済みの
  銘柄のみを対象とした`_get_yf_operating_income()`を追加し、WARN文言に
  yfinance実測値・乖離率を含めるよう拡張。`common.yfinance_utils.
  safe_yf_ticker()`（既存の安全呼び出しラッパー）経由で取得し、
  取得失敗時は照合をスキップする
- 対象範囲の限定によりレート制限リスクを抑制: 全105銘柄ではなく、
  CHECK-35が既にNone/derivedと判定した銘柄（2026-08-19時点で7銘柄
  ——LLY/JNJ/XOM/KLAC/ASTS/COHR/SOFI）のみyfinance呼び出しが発生する
  設計
- **既存パターンからの逸脱とその理由**: WARN-10（PS比率）・audit.pyの
  β照合が使う`common.market_data.reader.get_attributes()`ローカル
  キャッシュにはoperating_income相当のフィールドが存在せず踏襲不能
  だったため、単一ティッカーの直接取得に適した別の既存パターン
  （`common.yfinance_utils.safe_yf_ticker()`）を採用した
- **乖離率によるNG格上げは行わない**: 全105銘柄の乖離率分布を実測した
  結果、標準タグ採用済みの「正常」銘柄でも中央値0.2%な一方でp95=81%・
  最大342%（AVAV）まで裾が広く、Phase 2b-2と同型の誤検知リスクがある
  ため、乖離率は情報提供のみに留めWARNのまま据え置いた
- **新たな発見（当初）**: 再構成6銘柄のうちASTS・JNJはyfinanceとの
  乖離0.0%で再構成の正しさを裏付けたが、COHRは-89.6%
  （reconstructed_pretax $94.2M vs yfinance $901.5M）と大きく乖離して
  おり、再構成値自体の妥当性に疑問符が残ることが判明した
- 検証: 6対象銘柄全件でWARN文言に乖離率が正しく出ることを確認。
  残り99銘柄で意図しないWARN新規発火なし（トリガー条件自体は変更して
  いないため設計上当然）。pytest 781 passed/2 known-failed（既存の
  MSFT/NVDA）、`report_consistency_check.py --fail-on-ng` NG=0/
  WARN=88件、`audit.py` exit 0

**期ズレバグの発見・フォールバック向き反転（2026-08-19、同日追加）**:
実装翌日の検証で、上記COHR -89.6%という数値自体が`_get_yf_operating_
income()`の期ズレバグ（`row.iloc[0]`が決算期12月以外の銘柄でSECデータ
より1期先の予備的な値を指す）に起因すると判明し、期末日ベースの照合
（±10日許容窓）に修正した。正しく照合した結果、COHRの真の乖離は
-82.4%であり、これは「2手法不一致時にpretax法へフォールバックする」
という旧設計自体が誤りだったことを示していた（GP法が算出可能な4銘柄
全てでyfinanceと0.0%完全一致、フォールバック発動2銘柄はpretax採用値が
-11.4%/-82.4%も乖離）。フォールバック向きを反転（案A、GP法優先）し、
VRT FY2018の異常値対策として入力整合性ガード（案D）を追加実装した。
詳細・全検証結果は`[[OPERATING-INCOME-EXTRACTION-GAP-1]]`
（BACKLOG_DONE.md「2026-08-19（完了）」参照）。

#### ゲート0の実装状況（2026-08-18訂正）
- `exclusion_reason`は`src/value/tanuki_valuation/calculator/
  adjustments.py`（3件）・`pipeline.py`（1件）に存在するが、これは
  RPO/Revenue比率調整で「なぜ調整を適用しなかったか」を記録するDCF計算
  内部のフィールドであり、**ゲート0が求める`cik_lookup.csv`の銘柄登録
  除外理由列とは無関係の同名フィールド**
- `cik_lookup.csv`向けの`exclusion_reason`列は存在しない（2026-08-18確認）
- `audit.py`のカナダ企業（IFRS/40-F）検知は登録済み銘柄への事後WARNで
  あり、ゲート0が求める「登録時点でのsubmissions API照会による機械的
  ブロック」ではない
- `[[REGISTER-FLOW-REDESIGN-1]]`（ゲート0のマッピング元）の対応方針5件
  のうち完了は方針1（P4-CIKOrphanのスキャン範囲拡張、実質は
  `[[TICKER-SOURCE-UNIFY-1]]`の確定バグ2の修正と同一）のみ。方針2〜5
  （status列拡張・オーケストレーション化・`exclusion_reason`列・単一
  エントリポイント化）は未着手

#### CHECK-32〜36の位置づけ（2026-08-18追記）
2026-08-15〜16に新設したCHECK-32〜36が、本EPICの5ゲート構造の**どこにも
正式にマッピングされていない**ことを記録する。

| CHECK | 内容 | 対応ゲート |
|---|---|---|
| CHECK-32 | discover_config/theme_config同期チェック | ゲート4寄りだが元々のスコープ外（config二重管理検知） |
| CHECK-33 | fcf_conversion_config.json専用実装（→CHECK-34へ統合） | 同上 |
| CHECK-34 | config読み込み失敗の横断検知（レジストリテーブル方式） | 当初の5ゲートに定義されていない新種 |
| CHECK-35 | operating_income再構成使用・取得不可の検知（WARN） | 2026-08-18時点ではゲート1に最も近いが検知止まり（自動照合・自動補正ではない） |
| CHECK-36 | moat_score中立フォールバックの検知（WARN） | ゲート4寄り（出口側の検知） |

実態は「`report_consistency_check.py`のWARN機構を土台に、その都度発見した
個別の脆弱箇所を検知専用で塞いだパッチ群」であり、**いずれも「検知して
WARN表示する」段階に留まり、自動補正まで到達しているものは1つもない**
——これはEPIC自身が2026-07-12に「検知止まりでは不十分」と自己批判した、
まさにその手前の水準である。本EPICを「部分的に実施していた」とは言えない。
今後、これらをゲート構造に正式に位置づけるか独立した仕組みとして扱うかは
未決（着手時に判断する）。

**（2026-08-19追記）** CHECK-35はその後、本線3の第一歩として
`operating_income`のyfinance自動照合（実測値・乖離率のWARN文言への
追記）を獲得し、上表時点（自動照合ゼロ）から前進した——ただし自動
「補正」（値の書き換え）までは依然到達していない点は変わらない。
CHECK-32〜34・CHECK-36は本追記時点でも検知止まりのまま。詳細は
`[[OPERATING-INCOME-EXTRACTION-GAP-1]]`（BACKLOG_DONE.md
「2026-08-19（完了）」）参照。

---

## 優先度：高（早急に対応）

### [MARKETDATA-LAYER-CONSTRUCTION-1] common/market_data/新設（yfinance統合層）— 全12ファイル＋collect_asset_flow()6資産とも切替完了（低優先度3件は判断保留）
**優先度:** 高（新DB構築プロジェクト フェーズ1の本線、`common/sec_data`
統合が2026-08-07に実質完了したことに伴う次の優先タスク）
**状態:** 本番消費者8＋診断ツール2＋周辺ツール2の全12ファイルに加え、
`collect_and_send.py::collect_asset_flow()`のSHV等6資産
（SHV/GLD/TLT/LQD/HYG/SPY）も`common.market_data.reader`経由へ切替完了
（`[[MARKETDATA-COLLECT-ASSET-FLOW-UNTRACKED-1]]`、2026-08-13解消）。
低優先度3件（`[[MARKETDATA-CWAN-FROZEN-DATA-SUSPECT-1]]`・
`[[MARKETDATA-SP500-SCRAPE-INVALID-TICKERS-1]]`・`[[MARKETDATA-VIX9D-
DATA-GAP-1]]`）は引き続き判断保留中
**分類:** アーキテクチャ / 新DB構築プロジェクト フェーズ1
**登録日:** 2026-08-07（本来は事前調査着手時点で登録すべきだったが
未登録のまま3回の投資調査を実施していたため、本エントリで遡って
正式登録する）
**更新日:** 2026-08-12（着手順序6-2`backfill_tech_pulse.py`（QQQ/SPY
取得）が**完了**。前提作業として`reader.py`へ`get_price_series_as_of()`
（任意過去基準日起点のトレイリングウィンドウ取得、共通実装
`_price_series_ending_at()`へ`get_price_series()`ともリファクタ）を
新規追加した上で本体切替。「実行時点で1回だけ取得し全エントリで使い回す」
旧設計思想は維持。51件のmissingエントリ全件で`--dry-run`実行・旧実装との
`tp_score`/`tp_label`突合を実施し、`_tp_label()`バケット判定のクロスは
0件と確認。詳細・検証結果はBACKLOG_DONE.md「2026-08-12（完了）」着手順序
6-2参照（コミット`4a864bc1c`）。**これにより着手順序4〜6（本番消費者8＋
診断ツール2＋周辺ツール2の全12ファイル）が完了し、`common/market_data/`
構築プロジェクト自体が完了**。一連の切替作業中に発見した別課題群を
`[[MARKETDATA-CWAN-FROZEN-DATA-SUSPECT-1]]`・`[[MARKETDATA-SP500-
SCRAPE-INVALID-TICKERS-1]]`・`[[MARKETDATA-VIX9D-DATA-GAP-1]]`・
`[[STONKS-SILO-CLI-TICKERS-SHADOW-1]]`として登録済み（本線外・低優先度、
未対応）。誤って「バグ」登録した`[[MARKETDATA-DAILY-UNADJUSTED-PRICE-
DIVIDEND-DRIFT-1]]`は事実確認調査により前提の誤りが判明し訂正・クローズ
済み。詳細は下記「着手順序」参照）
**更新日:** 2026-08-13（新DB構築プロジェクト フェーズ1〜3総点検の結果、
`collect_and_send.py::collect_asset_flow()`のSHV等6資産
（DGS3MO以外の全6資産）が`_fetch_hist_legacy()`＝yfinance直接呼び出しの
まま未切替であり、かつBACKLOG.md本体に専用エントリが存在しない
「追跡漏れ」だったことが判明。`[[MARKETDATA-COLLECT-ASSET-FLOW-
UNTRACKED-1]]`として新規登録した。見出し・状態欄を「実装完了（全12
ファイル完了）」から実態に合わせて訂正。実装コード変更なし）
**更新日:** 2026-08-13（`[[MARKETDATA-COLLECT-ASSET-FLOW-
UNTRACKED-1]]`の切替実装が完了し**解消**（コミット`d021216e8`）。
`SHV`を`fetcher.py::INDEX_ETF_COMMODITY_SYMBOLS`へ追加・バックフィル
（他資産と同じ1,408件、2021-01-04〜）した上で、`collect_asset_flow()`の
SHV/GLD/TLT/LQD/HYG/SPY6資産を`fetch_recent_records()`経由に切替。
唯一の呼び出し元だった`_fetch_hist_legacy()`・`import yfinance as yf`も
削除し、`collect_and_send.py`から外部API直接呼び出しが完全に排除
された。6資産全数で切替前後の出力が完全一致（`value`/`change_pct`/
`date`のdiff 0件）することを確認済み、pytest回帰なし。低優先度3件
（CWAN/SP500スクレイピング/VIX9D）は本対応のスコープ外のため引き続き
判断保留のまま残る。詳細はBACKLOG_DONE.md「2026-08-13（完了）」
`[[MARKETDATA-COLLECT-ASSET-FLOW-UNTRACKED-1]]`参照。見出しから
「collect_asset_flow()6資産・低優先度3件は未解決」を削除し解消を反映）
**発見:** `common/market_data/`新設事前調査・実装設計投資調査（チャット
記録、2026-08-07）

#### 背景・投資調査サマリー
`INPUT_DATA_TOBE.md` 2-B（yfinance層設計）・`MIGRATION_CHECKLIST.md`
Step1に基づき、3回の投資調査を実施済み：

1. **使用実態洗い出し**：`INPUT_DATA_AS_IS.md`記載の「11ファイル」を
   実コードで再確認した結果、`common/sec_data/audit.py`
   （`audit_beta_drift()`）が見落とされており実際は**12ファイル**と
   判明（`[[MARKETDATA-AS-IS-AUDIT-PY-OMITTED-1]]`、`INPUT_DATA_
   AS_IS.md`・`INPUT_DATA_TOBE.md`とも訂正済み）。既知の重複取得
   パターン（現在株価2系統・PER/PEG/PSR/EV_EBITDA3系統・
   アナリストコンセンサス2系統・β3系統・`^GSPC`のMarket Pulse内
   4重取得）を全て実データで再確認し、`^GSPC`4重取得は
   `collect_and_send.py`内の4箇所（行292・652・682・750）と特定した。
2. **3区分分類**（`MIGRATION_CHECKLIST.md`準拠）：本番消費者8
   （`pipeline.py`・`data_fetcher.py`・`beta_fetcher.py`・
   `hypecore.py`・`valuation_fetcher.py`・`collect_and_send.py`・
   `breadth_calculator.py`・`collect.py`）・診断ツール2
   （`score_verifier.py`・`audit.py`）・周辺ツール2
   （`backfill_tech_pulse.py`・`extract_key_facts.py`）。
3. **実装設計**：`data_fetcher.py`の`.info`単発呼び出しが抽出する
   全フィールドを洗い出し3サブレイヤーへ仕分け、`fetcher.py`/
   `reader.py`API設計案・リトライ機構統合の影響範囲・GitHub Actions
   スケジュールとレート制限スタガリング案・`audit.py`の扱いを設計。

#### 設計確定事項（2026-08-07、投資調査＋ユーザー判断）

**保存構造・API設計**:
```
common/market_data/
  fetcher.py・reader.py（sec_data/と同型構成）
  daily/{SYMBOL}.json        # 日次価格層
  attributes/{SYMBOL}.json   # 週次準静的属性層
  analyst_history/{SYMBOL}.json  # イベント履歴層
```
`reader.py` API: `get_latest_price`・`get_price_series`・
`get_ma_deviation`（`price_series`から都度計算、`twoHundredDayAverage`
事前計算値は保存しない）・`get_attributes`・`get_analyst_events`・
`get_calendar`・`get_index_series`・`get_sp500_constituents_prices`

**取得方式（Step1案C採用）**:
日次バッチ: `.history()`のみで株価・出来高取得→`daily/`へ
週次バッチ: `.info`丸ごと取得→`attributes/`へ（PER/PEG/PSR/EV_EBITDA/
β/セクター/業種/配当/株式数/Forward EPS/アナリスト目標株価コンセンサス
を含む）

**【重要・仕様変更】TANUKI VALUATION・STONKS SILOの株価仕様変更**:
現状、`data_fetcher.py`・`valuation_fetcher.py`は市場取引時間中に
リアルタイム株価を取得している（`TANUKI_VALUATION_Update.yml`平日
14:05 UTC・`Stonks_Silo_Update.yml`平日15:05 UTC、いずれも米国市場
取引時間中）。統合後は前日終値ベース（日次バッチ、市場クローズ後
21:35 UTC付近に一本化）に仕様変更する。DCF計算・スコアリングに使用
する株価の性質が「取引時間中の変動値」から「確定した前営業日終値」に
変わる。ユーザー判断により決定（2026-08-07）。

**`audit.py`（12番目消費者）の扱い**:
`reader.get_attributes()["beta"]`経由に切替。`beta_fetcher.py`とは
独立に`reader.py`を参照する（診断ツールが本番消費者ロジックに依存
しない設計を維持）。

#### 設計確定事項（続き、2026-08-08、未決定事項9件の最終確定）
2026-08-07時点の未決定事項9件（3原則照合による追加6件＋既存3件）
それぞれについて投資調査（チャット記録、2026-08-07）で具体案を提示し、
以下の内容で全件確定した：

1. 営業日連続性保証：`pandas_market_calendars`を新規依存として採用
   （NYSE公式カレンダー準拠、正確性優先。既存の`src/market/
   macro_pulse/05_main.py::us_holidays()`は米国連邦祝日〈Columbus
   Day・Veterans Day含む、Good Friday除く〉でありNYSE取引カレンダー
   とは異なるため流用不可と確認済み）。`get_price_series()`は
   `nyse.valid_days()`と実際のレコード日付集合を突合し、説明のつかない
   欠損があれば警告フラグ付きで返す。`get_ma_deviation(window=200)`
   は200日分未満のデータしかない場合はNoneを返す。
2. `attributes/{SYMBOL}.json`へ`fetched_at`（ISO8601 UTC）フィールドを
   追加する。
3. `daily/`・`attributes/`書き込みをアトミック化する（`tempfile`で
   同一ディレクトリに一時ファイルを作成→`os.replace()`、Python標準
   ライブラリのみで実装、外部依存不要）。
4. 層またぎ再計算の禁止を`reader.py`のdocstringに明記する（実行時
   強制は過剰設計と判断、コメントレベルの明記に留める）。
5. 保存前検証ロジック（恒等式検証）:
   - 時価総額乖離許容率: `abs(computed_mcap - reported_mcap) <=
     max(reported_mcap * 0.02, 1_000_000)`（`common/sec_data/
     parser.py`のBS恒等式検証`_BS_IDENTITY_TOL_REL = 0.02`の相対2%を
     踏襲し、小型株向けに絶対フロア$1,000,000を追加）
   - 52週高安の検証は日次バッチ実行時点でのみ行う（過去データの
     都度再検証はしない、sec_data既存パターン〈CHECK29等〉と整合）
   - 検証失敗時は警告フラグ付きで保存する（保存拒否はしない、
     `_validation_warnings: [...]`フィールドを追加。理由:
     `fy_collision_log.json`等の既存パターンと同じ「検知のみ・
     自動修正なし・保存継続」方式を踏襲し、保存拒否による日次欠損が
     項目1の連続性保証に穴を作る副作用を避けるため）
   - 検証結果は`common/market_data/{SYMBOL}/
     market_data_violations_log.json`（`fy_collision_log.json`型、
     0件でも毎回書き込む）に記録する
6. `audit.py`のβ乖離監査（`beta_config.json`との外部妥当性監視）と
   `fetcher.py`保存前検証（同一スナップショット内の内部整合性
   ゲート）は検証対象が異なるため、両方維持する（役割分担を設計
   文書に明記）。
7. `twoHundredDayAverage`は保存しない（`get_ma_deviation`が
   `price_series`から都度計算する設計を最終確定。`[[HYPECORE-MISC-
   NAMING-GAPS-1]]`③既知の別データソース問題を踏まえ独自計算へ
   一本化）。アナリスト目標株価コンセンサス（`targetMeanPrice`等）は
   `.info`由来のスナップショット値のため`attributes/`へ格納し、
   アップグレード・ダウングレード等の真のイベントを扱う
   `analyst_history/`とは明確に区別する。
8. `workflow_run`連鎖トリガーを採用する：`Market_Data_Daily_
   Update.yml`（市場クローズ後、21:35 UTC付近想定）完了後にTANUKI
   VALUATION・STONKS SILOをworkflow_runでトリガーする（前日終値
   ベース化に伴うレース条件〈日次バッチ未完了時に読みに行くリスク〉
   回避のため）。週次`attributes/`バッチは本番消費者を待たせる必要が
   ないため独立cronのまま維持する。
9. `[[NETCASH-DUAL-CALC-1]]`とは独立タスクとして並行進行する。
   market_data層の`attributes/`には`totalDebt`を含めるが、STONKS
   SILOの`net_cash`計算をmarket_data経由の`totalDebt`に置き換える
   新規実装は行わない（`[[NETCASH-DUAL-CALC-1]]`の既存対応方針＝
   `SECReader.get_net_cash()`〈SEC XBRLベース〉への統一を優先する）。

これにより未決定事項9件は全件解消した。

#### 着手順序
1. **【完了・2026-08-10】** `fetcher.py`新設（`.history()`・`.download()`
   呼び出しの一元化、`pandas_market_calendars`依存追加含む）。
   `common/market_data/fetcher.py`に`fetch_daily_prices()`（`daily/`）・
   `fetch_weekly_attributes()`（`attributes/`）・`fetch_analyst_events()`
   （`analyst_history/`）を実装。保存前検証（`validate_price_record()`・
   `validate_attributes_record()`）・`{SYMBOL}/market_data_violations_log.json`
   への毎回書き込み・`tempfile`→`os.replace()`アトミック書き込み・
   `pandas_market_calendars`によるNYSE営業日判定（`is_trading_day()`）を
   確定事項1〜7通りに実装済み。AAPL・IONQ（小型株）・`^GSPC`（指数）の
   3層実データ取得動作確認・保存前検証の発火確認（正常系/異常系）・既知の
   祝日/臨時休場日（感謝祭・独立記念日振替休場・ハリケーンサンディ2012・
   9/11 2001）でのNYSEカレンダー認識確認・アトミック書き込みの中断耐性
   確認まで完了。新規テスト`tests/test_market_data_fetcher.py`26件PASS、
   pytest全体531 passed/2 known-failed（`[[TEST-STALE-IV-1]]`、無関係）。
   既存消費者はまだ本モジュールを参照しないためシステムへの影響なし。
   `reader.py`未実装のため`__init__.py`から`reader`は未import。
2. **【完了・2026-08-10】** `reader.py`新設（API群の実装）。
   `common/market_data/reader.py`に`get_latest_price`・`get_price_series`・
   `get_ma_deviation`・`get_attributes`・`get_analyst_events`・
   `get_calendar`・`get_index_series`・`get_sp500_constituents_prices`を
   実装。`get_price_series()`は`pandas_market_calendars`で期待される
   営業日集合と実レコード日付集合を突合し、欠損があれば`_gap: True`の
   プレースホルダーで埋めて返す設計（確定事項1）。`get_ma_deviation()`は
   window日分の実データ（欠損を除く）が揃わない場合`None`を返す
   （`twoHundredDayAverage`等の事前計算値は保存せず都度計算、確定事項7）。
   全APIのdocstringに層またぎ再計算禁止（確定事項4）を明記。
   `get_calendar()`はfetcher.pyが次回決算日等を未取得のため現状常に
   空dictを返す（将来`attributes/`に`calendar`キーが追加されれば
   reader.py側の変更なしに対応する設計）。`__init__.py`に`fetcher`・
   `reader`をexport。AAPL・IONQ・`^GSPC`の実データ（fetcher.py実行）＋
   合成30営業日データ（欠損なし/欠損注入の両方）で全API動作確認・
   未フェッチ銘柄への全API呼び出しが例外なくNone/空リスト/空dictを返す
   ことを確認。新規テスト`tests/test_market_data_reader.py`27件PASS、
   pytest全体558 passed/2 known-failed（`[[TEST-STALE-IV-1]]`、無関係）。
   動作確認で生成したAAPL/IONQ/^GSPCの実データ（`daily/`・`attributes/`・
   `analyst_history/`・`{TICKER}/market_data_violations_log.json`計12
   ファイル）は手動テスト由来のため今回のコミットには含めず、本番
   GitHub Actionsバッチが最初に生成する際に正式にコミットする方針とした
   （`common/sec_data/data/`と同様、これらのディレクトリ自体は追跡対象
   とすべきものであり`.gitignore`追加は行っていない）。
3. **【完了・2026-08-10】** 定期実行ワークフロー新設。
   `.github/workflows/Market_Data_Daily_Update.yml`（平日21:40 UTC、
   `fetch_daily_prices()`を全銘柄実行し`daily/`＋violations logをコミット
   ＆push）・`Market_Data_Weekly_Update.yml`（日曜13:20 UTC、
   `fetch_weekly_attributes()`＋`fetch_analyst_events()`を全銘柄実行し
   `attributes/`＋`analyst_history/`＋violations logをコミット＆push）の
   2ファイルを新設。いずれも`SEC_Data_Update.yml`と同型構成、既存
   ワークフローとのcron衝突なし（Market_Pulse_Update 21:35 UTC・
   HypeCore_Update 13:08 UTCとそれぞれ5分・12分ずらして分散、設計
   確定事項8）。設計確定事項8のworkflow_run連鎖（本ワークフロー完了後に
   TANUKI VALUATION・STONKS SILOを起動）は、発火先の本番消費者切替
   （着手順序4）が完了するまで無効のまま、`Market_Data_Daily_Update.yml`
   内にコメントとして記法のみ準備した（`TANUKI_VALUATION_Update.yml`・
   `Stonks_Silo_Update.yml`自体は今回変更していない）。

   **push後の`workflow_dispatch`実行確認（Daily/Weekyとも完了）**:
   push直後にDaily・Weeklyをほぼ同時に手動起動したところ、Dailyは成功
   したがWeeklyは`git pull --rebase`で`add/add`コンフリクト
   （両者が同一の新規ファイル`{TICKER}/market_data_violations_log.json`
   にほぼ同時commitしたため）により失敗した。原因は
   `common/market_data/`配下が`docs/market-monitor/`等の既存自動生成
   データディレクトリと異なり`.gitattributes`の`merge=ours`対象に
   未登録だったこと。**恒久対応として`.gitattributes`に
   `common/market_data/daily/*.json`・`attributes/*.json`・
   `analyst_history/*.json`・`*/market_data_violations_log.json`・
   `_sp500_constituents_cache.json`の5パターンへ`merge=ours`を追加**
   （コミット`4749fbd6f`）。追加後にWeeklyを単独で再実行し成功
   （コミット`51cc6e38f`）。`{TICKER}/market_data_violations_log.json`に
   `daily_price_validation`（Daily由来）・`attributes_validation`
   （Weekly由来）の両セクションが正しく共存することを確認、
   `attributes/`・`analyst_history/`の実データ生成（AAPL/IONQ/^GSPCの
   3銘柄、AAPL analyst_history 969件等）も確認済み。
   本番cronでは実行日自体が重ならない（平日 vs 日曜）ためこの衝突は
   通常発生しない想定だが、手動再実行が重なる場合等への保険として
   本対応を維持する。

   Daily/Weeklyとも`workflow_dispatch`によるGitHub Actions上での実行
   確認が完了し、生成された実データ（`daily/`・`attributes/`・
   `analyst_history/`・violations log、AAPL/IONQ/^GSPCの3銘柄分）は
   本番バッチ生成分としてそのままリポジトリに残している。
4. 本番消費者8ファイルの段階的切替（TANUKI VALUATION本体から、フェーズD
   と同様の優先順位を検討）。**【完了・2026-08-11】進捗 8/8（全数完了）。**

   **優先順位案（2026-08-10時点、着手順序3完了時の提案）**
   1. **【完了・2026-08-10】** `beta_fetcher.py`。詳細・検証結果は
      BACKLOG_DONE.md「2026-08-11（完了）」`[[MARKETDATA-LAYER-
      CONSTRUCTION-1]]着手順序4-1`参照（コミット`d0b9fefdf`）。
   2. **【完了・2026-08-11】** `data_fetcher.py`（株価取得を前日終値ベースへ
      仕様変更する本丸。TANUKI VALUATION本体のDCF計算に直結する消費者）。
      前提条件（`attributes/`スキーマ拡張・日次価格層バックフィル）を
      含め、詳細・検証結果はBACKLOG_DONE.md「2026-08-11（完了）」
      `[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序4-2前提条件`・
      `着手順序4-2`参照（コミット`1b710759c`・`0d5dbd18c`・`94887bde6`）。
      **ma200はget_ma_deviation()の乖離率を代数的に逆算する方式を採用し
      pipeline.py側は無変更**、実データ100銘柄比較で97/100完全一致。
   3. **【完了・2026-08-11】** `valuation_fetcher.py`（`discover/
      stonks-silo/src/`、STONKS SILO対象25銘柄）。詳細・検証結果は
      BACKLOG_DONE.md「2026-08-11（完了）」`[[MARKETDATA-LAYER-
      CONSTRUCTION-1]]着手順序4-3`参照（コミット`40b20411c`）。
      実データ25銘柄比較で24/25完全一致、`pipeline.py`側の`net_cash`・
      PSR/EV_Sales算出ロジックは無変更（`[[NETCASH-DUAL-CALC-1]]`既存
      方針と整合）。副次発見`[[STONKS-SILO-CLI-TICKERS-SHADOW-1]]`
      （CLI引数実行の既存バグ）は本切替の範囲外のため未修正のまま
      新規登録。
   4. **【完了・2026-08-11】** `pipeline.py`（`.calendar`のみ、他フィールドは
      着手順序4-2で対応済み）。詳細・検証結果はBACKLOG_DONE.md
      「2026-08-11（完了）」`[[MARKETDATA-LAYER-CONSTRUCTION-1]]
      着手順序4-4`参照（コミット`c6bfb83f6`）。実データ100銘柄比較で
      next_earnings_date 100/100完全一致。
   5. **【完了・2026-08-11】** `collect.py`（Discover参考株価）。詳細・
      検証結果はBACKLOG_DONE.md「2026-08-11（完了）」
      `[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序4-5`参照
      （コミット`dfd7e3ef2`）。実データ98銘柄比較で96/98完全一致。
   6. **【完了・2026-08-11】** `collect_and_send.py`（Market Pulse）。
      詳細・検証結果はBACKLOG_DONE.md「2026-08-11（完了）」
      `[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序4-6`参照
      （コミット`4e95e23ce`）。sentiment_score・TAKE PROFIT/BUY判定
      とも完全一致。副次発見`[[MARKETDATA-VIX9D-DATA-GAP-1]]`を新規登録。
   7. **【完了・2026-08-11】** `breadth_calculator.py`（Market Pulse
      breadth指標）。詳細・検証結果はBACKLOG_DONE.md「2026-08-11
      （完了）」`[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序4-7`参照
      （コミット`e49ffb905`）。実データ502銘柄比較でrsp_spy_divergence
      完全一致・breadth指標も軽微な乖離のみ。
   8. **【完了・2026-08-11】** `hypecore.py`本体（daily/attributes/
      analyst_historyの3層すべてが混在する最複雑の消費者）。前提作業
      3件（daily/バックフィル拡張・attributes/7フィールド追加・
      analyst_history/2系統追加）を含め、詳細・検証結果はBACKLOG_DONE.md
      「2026-08-11（完了）」`[[MARKETDATA-LAYER-CONSTRUCTION-1]]
      着手順序4-8前提作業1〜3`・`着手順序4-8`参照（コミット
      `afa3c954b`・`223840d13`・`f223464f1`・`09d2151fd`）。HypeCore
      対象104銘柄比較でanalyst_history 104/104完全一致。切替過程で
      発見した`auto_adjust`不一致は、後続の事実確認調査で「旧実装の
      調整済み終値使用の方が技術指標としては不適切だった」と判明し
      訂正・クローズ（`[[MARKETDATA-DAILY-UNADJUSTED-PRICE-DIVIDEND-
      DRIFT-1]]`、対応不要で確定）。

5. 診断ツール2ファイルの切替（`score_verifier.py`・`audit.py`）。
   **【完了・2026-08-12】進捗2/2（全数完了）。**
   1. **【完了・2026-08-11】** `audit.py`（β乖離監査・カナダ企業判定）。
      `audit_beta_drift()`のβ乖離監査（設計確定事項6通り
      `reader.get_attributes()["beta"]`経由）・`audit_ticker()`の
      カナダ企業判定（`attributes/`へ`country`フィールドを新規追加した
      上で`reader.get_attributes()["country"]`経由）とも切替完了。
      詳細・検証結果はBACKLOG_DONE.md「2026-08-11（完了）」
      `[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序5-1`参照（コミット
      `be48054cc`）。副次発見: `SEC_Data_Audit.yml`は従来
      `pip install requests`のみでyfinance未導入のため、旧カナダ判定は
      import失敗のexcept節で本番自動実行時は常に無音スキップされ
      事実上死んでいた。今回`pip install -r requirements.txt`への変更と
      合わせ実際に機能するようになった。
   2. **【完了・2026-08-12】** `score_verifier.py`（判定実績の事後検証、
      `fetch_price_after()`）。前提作業として`reader.py`へ
      `get_price_on_or_after(symbol, date)`を新規追加（date以降5日
      ウィンドウで先頭値を採用、旧`fetch_price_after()`と同じクエリ形状を
      daily/層に対して再現）した上で本体切替。詳細・検証結果は
      BACKLOG_DONE.md「2026-08-12（完了）」`[[MARKETDATA-LAYER-
      CONSTRUCTION-1]]着手順序5-2`参照（コミット`2668f3aaf`・
      `bc0f6fb24`）。
6. 周辺ツール2ファイル（`backfill_tech_pulse.py`・`extract_key_facts.py`）
   の切替。**【完了・2026-08-12】進捗2/2（全数完了）。**
   1. **【完了・2026-08-12】** `extract_key_facts.py`（株式数フォールバック④、
      V等SEC全期間で希薄化後株式数タグ未申告の銘柄向け最終フォールバック）。
      yfinance直接呼び出しを`reader.get_attributes()`経由（`shares_outstanding`
      優先→`implied_shares_outstanding`フォールバック、既存優先順位パターン
      維持）に切替。V実例での再現テストで切替前後の値が完全一致、EPS Analyzer
      対象101銘柄中fallback④該当はV 1件のみと判明（他100銘柄は影響なし）。
      詳細・検証結果はBACKLOG_DONE.md「2026-08-12（完了）」`[[MARKETDATA-
      LAYER-CONSTRUCTION-1]]着手順序6-1`参照（コミット`212454681`）。
   2. **【完了・2026-08-12】** `backfill_tech_pulse.py`（Tech Pulse履歴
      バックフィル専用の一過性ツール、QQQ/SPY取得）。前提作業として
      `reader.py`へ`get_price_series_as_of(symbol, as_of_date, days)`を
      新規追加（任意過去基準日起点のトレイリングウィンドウ取得、共通実装
      `_price_series_ending_at()`へ`get_price_series()`ともリファクタ）
      した上で本体切替。「実行時点で1回だけ取得し全エントリで使い回す」
      旧設計思想は維持。51件のmissingエントリ全件で`--dry-run`実行・
      旧実装との`tp_score`/`tp_label`突合を実施し、`_tp_label()`バケット
      判定のクロス0件を確認。詳細・検証結果はBACKLOG_DONE.md
      「2026-08-12（完了）」`[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序
      6-2`参照（コミット`4a864bc1c`）。

**これにより着手順序4〜6（本番消費者8＋診断ツール2＋周辺ツール2の
全12ファイル）が完了し、`common/market_data/`構築プロジェクト自体が
完了した。**

**次セッションでの着手順序（2026-08-12時点、`[[MACRODATA-LAYER-
CONSTRUCTION-1]]`完成を反映し訂正。旧内容は`common/macro_data/`実装設計
着手を指示していたが同日中にプロジェクト自体が完成したため陳腐化、
ブラッシュアップで発見し削除。詳細はBACKLOG_DONE.md
`[[BACKLOG-STALE-NEXTSTEPS-BLOCK-MACRODATA-1]]`参照）**:
最新の「次セッションでの着手順序」は`[[MACRODATA-LAYER-CONSTRUCTION-1]]`
エントリ側（本ファイル内）を参照。

#### hypecore.py切替の前提作業・本体切替（着手順序4-8、2026-08-11完了）
事前調査で判明した3件の前提作業（daily/バックフィル期間拡張・
attributes/7フィールド追加・analyst_history/2系統のスキーマ設計）を
実装した上で本体切替まで完了。詳細・検証結果はBACKLOG_DONE.md
「2026-08-11（完了）」`[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序
4-8前提作業1〜3`・`着手順序4-8`参照。副次発見（`__main__`フォールバック
ticker配列の陳腐化、48銘柄ハードコードが実際の104銘柄と乖離。実害は
限定的で対応不要）も記録済み。`ValueError`送出の改善（実データ完全
欠如の場合のみ発火）は実装済み。

#### 日次価格層バックフィル（着手順序4-2 data_fetcher.py切替の前提条件、2026-08-11完了）
`daily/`の日次収集は2026-08-10開始のため、200営業日移動平均
（`reader.get_ma_deviation(window=200)`）が自然蓄積で計算可能になるまで
約10ヶ月かかる問題を、`backfill_daily_prices(symbols, period="1y")`
（一過性ツール、`backfill_tech_pulse.py`型、定期cronには組み込まない、
CLIの`--backfill`フラグ経由で手動実行）の新設により即時解消した。
`period="1y"`で251営業日分取得（window=200に対し51日の余裕、window=50にも
十分）を実測確認。全母集団570銘柄（`get_default_symbol_universe()`）で
実行し全銘柄成功。AAPL等サンプルで`get_ma_deviation(window=200)`が実値
（例: AAPL≒10.2%）を返すこと、既存の日次cron取得分（2026-08-10）が
バックフィル後も消失せず保持されることを確認済み。新規テスト
`tests/test_market_data_fetcher.py`（`TestMergeDailyRecords`・
`TestBackfillDailyPrices`10件）。

**バックフィル実行中に判明した2件の別課題**（本エントリとは独立、
下記2件として新規登録・詳細はBACKLOG該当エントリ参照）:
`[[MARKETDATA-CWAN-FROZEN-DATA-SUSPECT-1]]`（CWANのyfinanceデータが
1日分・出来高0のフリーズ状態）・`[[MARKETDATA-SP500-SCRAPE-INVALID-
TICKERS-1]]`（S&P500構成銘柄Wikipediaスクレイピングに`FDXF`/`HONA`/`Q`
という不正銘柄が混入、正規の`FDX`/`HON`とは別に重複存在）。

**注記（2026-08-11、再実装の経緯）**: 本バックフィル機能は一度実装・
検証済みだったが、コミット前に作業ツリーの変更が失われ再実装が必要と
なった（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`本体には影響なし、独立した
作業ロスのみ）。今回は検証完了後直ちにコミット・pushを実施し再発を防止。

**注記（2026-08-15、フィールド単位の切替完了確認）**: `FIELD_
DEFINITIONS.md`499項目単位での新DB参照切替状況を集計する投資調査を
実施した結果、`common/market_data/`（yfinance）由来の一次データ8件
（AS-IS-032・262・312・320・321・322・325・362）が全件切替済みである
ことを実コードで確認した（詳細は`PROJECT_STATUS.md`フェーズ3参照）。
ファイル単位（本エントリの全12ファイル＋asset_flow）の切替完了に加え、
フィールド単位でも本線タスクの完了を確認できた。

#### 着手条件
なし（未決定事項9件は全件確定済み、実装着手可能）。

---

### [MACRODATA-LAYER-CONSTRUCTION-1] common/macro_data/新設（FRED統合層）— 完成（本番消費者2ファイル＋周辺ツール1件とも切替完了、外部API直接呼び出し完全排除）
**優先度:** 高（新DB構築プロジェクト フェーズ1の次コンポーネント、
`common/market_data/`が2026-08-12に全12ファイル切替完了したことに伴う
次の優先タスク）
**分類:** アーキテクチャ / 新DB構築プロジェクト フェーズ1
**登録日:** 2026-08-12（本来は事前調査着手時点で登録すべきだったが、
`common/market_data/`と同様の経緯で未登録のまま投資調査を実施していた
ため、本エントリで遡って正式登録する）
**更新日:** 2026-08-12（本番消費者2ファイル（`05_main.py`・
`collect_and_send.py`）を`common.macro_data.reader`経由へ全面切替し
**完成**。重複3系列（`BAMLH0A0HYM2`・`T10Y2Y`・`VIXCLS`）は
`get_financial_context()`・`daily`系列ループ・`update_liquidity_csv()`の
いずれも同一の`reader.get_latest()`呼び出しへ集約し重複取得を解消。
両ファイルから`Fred(`・`fred_latest(`等の外部API直接呼び出しを完全に
排除（grep最終確認で残存0件）。切替前後で18項目の値突合を実施し
**全項目完全一致**（差分0件）。詳細は下記「本番消費者切替完了」参照）
**更新日:** 2026-08-13（新DB構築プロジェクト フェーズ1〜3総点検の結果、
「完成（本番消費者切替完了）」の射程は`05_main.py`・
`collect_and_send.py`の**本番消費者2ファイルに限定**されており、周辺
ツール`backfill_tech_pulse.py`の`VXNCLS`取得（`Fred(api_key=
FRED_API_KEY).get_series("VXNCLS", ...)`直接呼び出し）は射程外のまま
未切替で残存し、かつBACKLOG.md本体に専用エントリがない「追跡漏れ」
だったことが判明。`[[MACRODATA-BACKFILL-TECH-PULSE-VXNCLS-
UNTRACKED-1]]`として新規登録した。見出しに射程の限定を明記。実装
コード変更なし）
**更新日:** 2026-08-13（`[[MACRODATA-BACKFILL-TECH-PULSE-VXNCLS-
UNTRACKED-1]]`の切替実装が完了し**解消**（コミット`4930458e7`）。
`backfill_tech_pulse.py`の`VXNCLS`取得も`Fred(`直接呼び出しから
`common.macro_data.reader.get_series()`経由に切替済みとなり、
本番消費者2ファイル＋周辺ツール1件のいずれからも外部API直接呼び出し
が完全に排除された。51件のmissingエントリ全件で切替前後の出力が
完全一致（`tp_score`/`tp_label`/`vxn_vs_ma50`等diff 0件）することを
確認済み、pytest回帰なし。詳細はBACKLOG_DONE.md「2026-08-13
（完了）」`[[MACRODATA-BACKFILL-TECH-PULSE-VXNCLS-UNTRACKED-1]]`参照。
見出しから「周辺ツール1件は射程外で未切替」を削除し解消を反映）
**発見:** `common/macro_data/`新設事前調査・FRED消費者洗い出し
（`MIGRATION_CHECKLIST.md`Step1相当、チャット記録、2026-08-12）

#### 背景・投資調査サマリー
`common/market_data/`（yfinance統合層）の全12ファイル切替完了
（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`）を受け、新DB構築プロジェクト
フェーズ1の次コンポーネントとして`common/macro_data/`（FRED統合層）の
着手前投資調査を実施した。`market_data`着手時の教訓（当初の「11ファイル」
調査が`common/sec_data/audit.py`1件を見落としていた、
`[[MARKETDATA-AS-IS-AUDIT-PY-OMITTED-1]]`）を踏まえ、探索範囲を`src/`
配下に限定せず`common/`・`discover/`配下も含めリポジトリ全体をgrep等で
網羅的に確認した。

**FRED呼び出し箇所の特定（実コード確認）**:
- FRED呼び出しは**2サブシステットのみ**（`src/market/macro_pulse/`・
  `src/market/market_pulse/`）。`common/`・`discover/`配下には現状ゼロ
  （`INPUT_DATA_AS_IS.md`の「実測2サブシステム」を実データで再確認）
- MACRO PULSE本番: `05_main.py`（`INDICATOR_CONFIG`辞書12系列＋
  `get_financial_context()`/`get_ff_current()`/`get_implied_cuts()`/
  `get_sp500()`/`update_liquidity_csv()`が独自に追加系列を取得）
- Market Pulse本番: `collect_and_send.py`（`VXNCLS`・`BAMLH0A0HYM2`・
  `DGS3MO`、3関数がそれぞれ独立に`Fred()`インスタンスを生成）
- 診断ツール: `05_audit.py`（FRED呼び出しなし、`05_events.csv`の
  監査のみ、`common/macro_data/`切替の対象外）
- 周辺ツール: `05_backfill_nfp_mom.py`（一過性、NFP履歴修正済み）・
  `05_import_history.py`（一過性、独自`FRED_INDICATORS`辞書が現行
  `INDICATOR_CONFIG`と乖離、`[[MACRODATA-IMPORT-HISTORY-CONFIG-
  DRIFT-1]]`参照）・`backfill_tech_pulse.py`（`VXNCLS`のみ未切替、
  QQQ/SPY部分は`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`着手順序6-2で
  切替済み）

**重複取得パターンの実態確認**: `INPUT_DATA_TOBE.md`が指摘する
`BAMLH0A0HYM2`重複取得「3箇所」を実データで再検証した結果、実際は
`get_financial_context()`を含む**4箇所**（MACRO PULSE内部3箇所＋
Market Pulse1箇所）。`T10Y2Y`・`VIXCLS`にも同型の未記載重複あり
（詳細は`[[MACRODATA-AS-IS-DUPLICATION-UNDERCOUNT-1]]`参照）。

**24系列台帳の正確性確認**: `INPUT_DATA_TOBE.md`のFRED系列台帳
（`INPUT-A-024`〜`047`、24系列）は主要系列としては網羅的だったが、
`FTSD`（`WTREGEN`フォールバック先）が1系列漏れていた
（`[[MACRODATA-FTSD-MISSING-FROM-INVENTORY-1]]`、2026-08-12の設計確定
作業で`INPUT-A-049`として追加し解消済み・BACKLOG_DONE.mdへ移動）。

**取得頻度・エラーハンドリングの現状確認**:
- cron: `MACRO_PULSE_Update.yml`（日次×2＋週次×2、4種類のcronが並存）・
  `Market_Pulse_Update.yml`（平日日次）
- メタ情報（`obs_to_release_lag`等）は`INDICATOR_CONFIG`辞書内に
  フラットなキーとして直接埋め込み。専用configファイルは存在しない
- リトライ機構があるのは`05_main.py::fetch_event_row()`・
  `fred_release_dates()`と`05_import_history.py::_load_ctx_cache()`の
  計3箇所のみ（3回リトライ＋指数バックオフ）。残り大半（`fred_latest()`
  本体・`update_liquidity_csv()`・Market Pulse側3関数・
  `backfill_tech_pulse.py`）はリトライなしの素朴なtry/except
- 共有フェッチャー層は存在せず、各ファイルが個別に`Fred(api_key=...)`
  クライアントを生成している状態（`market_data`着手前のyfinance分散
  状態と同型）

投資調査の過程で新規発見した4件をBACKLOG登録済み（記録のみ、
実装なし）: `[[MACRODATA-AS-IS-DUPLICATION-UNDERCOUNT-1]]`（優先度：中、
**2026-08-13、`[[FRED-HYSPREAD-TRIPLE-FETCH-1]]`と同型の理由で解消・
BACKLOG_DONE.mdへ移動済み**）・
`[[MACRODATA-SCHEDULED-SILENT-GAP-CSCICP-USALOL-1]]`（優先度：低〜中）・
`[[MACRODATA-FTSD-MISSING-FROM-INVENTORY-1]]`（優先度：低、**2026-08-12
の設計確定作業で解消・BACKLOG_DONE.mdへ移動済み**）・
`[[MACRODATA-IMPORT-HISTORY-CONFIG-DRIFT-1]]`（優先度：低）。

#### 設計確定事項（2026-08-12、投資調査完了を受けた確定）

**保存形式・スキーマ**:
- 保存形式は`common/macro_data/series/{SERIES_ID}.json`（系列ごとの
  JSONファイル、観測日昇順のリスト）に確定。当初案のCSVではなく
  `common/market_data/`（`daily/{SYMBOL}.json`等）と形式を揃える
  （2つの新設データ層が別々の保存慣習を持つ状態を避けるため）。
- 各エントリのスキーマは`INPUT_DATA_TOBE.md`2-D節のprovenance標準
  （`value`/`as_of`/`fetched_at`/`source`/`source_detail`/
  `fallback_used`）をそのまま適用。`source`は`"FRED"`固定、
  `source_detail`に系列コードを含める。
- 系列単位のメタ情報（`fred_release_id`/`obs_to_release_lag`等、現状
  `INDICATOR_CONFIG`にフラット埋め込み）は`common/macro_data/
  series_meta.json`へ切り出す。

**fetcher.py/reader.py API**:
- `fetcher.py::fetch_series(series_id, start=None)`を外部アクセスの
  唯一の窓口とし、リトライ＋指数バックオフを全系列で統一する（現状は
  `05_main.py::fetch_event_row()`/`fred_release_dates()`/
  `05_import_history.py::_load_ctx_cache()`の3箇所のみ実装という
  不統一を解消）。保存前に系列ごとの定義域チェック（比率系の範囲外
  検知、前回値からの桁違い変化検知）を行い、`common/macro_data/
  macro_data_violations_log.json`（0件でも毎回書き込む、
  `market_data_violations_log.json`と同型）へ記録する
  （`EXTRACTION_DESIGN_PRINCIPLES.md`原則3対応）。
- `reader.py`: `get_latest(series_id)`・`get_series(series_id,
  start=None, end=None)`・`get_value_as_of(series_id, date)`を提供。
  `get_series`の返り値は観測日を含み、消費側（VXN50日MA等の「直近N件」
  ロジック）が期間の連続性を自前で検証できるようにする
  （`EXTRACTION_DESIGN_PRINCIPLES.md`原則1対応）。

**重複3系列（`BAMLH0A0HYM2`・`T10Y2Y`・`VIXCLS`）の解消方式**:
`05_main.py::get_financial_context()`・`INDICATOR_CONFIG`の`daily`系列
ループ・`update_liquidity_csv()`、および`collect_and_send.py`側3関数の
いずれも独自に`Fred()`を呼ぶのをやめ、全て`reader.py`経由に統一する
ことで解消する（`TO_BE_FINAL_LIST.md`⑮-final「取得共通化・出力3件
存続」に対応。出力項目自体は3件とも存続し削除しない）。

**FTSD追加・機械的網羅性証明の再実行**: `FTSD`を`INPUT-A-049`として
`INPUT_DATA_TOBE.md`・`INPUT_DATA_AS_IS.md`の両方へ追加。分類A件数は
48件→49件、3分類合計は65件→66件に更新。機械的網羅性証明の再実行時、
`INPUT-A-048`（税務・一過性項目タグ群52種）が`INPUT_DATA_AS_IS.md`側
に反映漏れ（2026-07-24時点で発生していた既存の乖離、今回の再実行で
発覚）していたことが判明したため同ファイルへ追加して解消し、
再実行結果は両ファイルとも**66件・差分0件**を確認した。

これらの確定事項はいずれもドキュメント記録のみで、実装コード変更・
データ再生成は行っていない。

#### 実装完了事項（fetcher.py/reader.py、2026-08-12）
設計確定事項を踏まえ、`common/macro_data/`の新規モジュールを実装した
（新規モジュール構築のみがスコープ、本番消費者切替・cronワークフロー
新設・過去データ一括投入は次段階に分離し今回は一切変更していない）。

**series_meta.json**: `INDICATOR_CONFIG`12系列＋流動性カード/FOMC/
Market Pulse用13系列（`SP500`/`DGS1`/`DFEDTARU`/`DFEDTARL`/
`FEDFUNDS`/`WALCL`/`WTREGEN`/`RRPONTSYD`/`WRBWFRBL`/`M2SL`/`FTSD`/
`VXNCLS`/`DGS3MO`）を実コードから機械的に走査し、`INPUT-A-024`〜`049`
の25系列全件を`{series_id: {input_id, fred_release_id,
obs_to_release_lag, category, consumers}}`形式で生成。メタ情報が
存在しない系列は`note`フィールドに明記、`consumers`には実際の参照
関数名を記録（重複3系列は複数`consumers`を保持）。

**fetcher.py**: `fetch_series(series_id, start=None)`（FRED外部アクセス
の唯一の窓口、リトライ3回＋指数バックオフは`05_main.py::
fetch_event_row()`のパターンを踏襲）・`update_series(series_id,
start=None)`（日付単位upsert、`value`/`as_of`/`fetched_at`〈JST〉/
`source`/`source_detail`を付与）・`fetch_all_series(series_ids=None)`
（`series_meta.json`駆動のバッチ関数、cron配線自体は次段階）。保存前
検証2項目（①バッチ内`as_of`重複②直前値比1桁以上の変化）を
`macro_data_violations_log.json`へ0件でも毎回書き込み（単一の共有
ログファイル、系列IDでセクション分割。`market_data_violations_
log.json`が銘柄ごと別ファイルなのとは異なる設計）。fredapiクライアント
はモジュールレベルで1つだけ生成し使い回す（現状の各ファイルが個別に
`Fred()`を生成する設計は踏襲しない）。`FRED_API_KEY`環境変数名・
`Fred(api_key=...)`初期化方法は`05_main.py::get_fred()`・
`collect_and_send.py`側3関数を実コード確認の上で踏襲（新規の変数名は
導入していない）。

**reader.py**: `get_latest(series_id)`・`get_series(series_id,
start=None, end=None)`（観測日昇順、観測日を含むため消費側が連続性を
自前検証可能）・`get_value_as_of(series_id, date, lookback_days=45)`
（指定日以前の直近値をルックバック窓内で探索、`market_data/reader.py::
get_price_on_or_after()`系のAPIパターンを踏襲）。外部API呼び出しは
一切行わない。

**検証**: `tests/test_macro_data_fetcher.py`（リトライ・upsert・
保存前検証・violations log・fetch_all_series・アトミック書き込み）・
`tests/test_macro_data_reader.py`（get_latest/get_series/
get_value_as_ofのルックバック境界含む）を新規追加、計43件。実データ
（実際のFRED系列名）を使ったモック経由の手動スモークテストで
upsert・重複検知・桁違い変化検知・ルックバック境界の動作を個別確認
済み。pytest全体は既知失敗2件〈`[[TEST-STALE-IV-1]]`〉以外の回帰なし。

#### 定期取得ワークフロー稼働開始（2026-08-12）

**事前確認**: `common/market_data/`の`Market_Data_Daily_Update.yml`/
`Market_Data_Weekly_Update.yml`を実コード確認し、エントリポイントが
`fetcher.py`自身の`if __name__ == "__main__":`ブロック（argparse、
`python common/market_data/fetcher.py [symbols] --layer daily`形式）
であり、別ファイルの起動スクリプトは存在しないことを確認。同じ
パターンを`common/macro_data/fetcher.py`にも踏襲し、`python
common/macro_data/fetcher.py [series_ids]`で`fetch_all_series()`を
呼ぶCLIを追加した。

`.github/workflows/MACRO_PULSE_Update.yml`（`15 22 * * *`・
`3 13 * * *`・`7 22 * * 6`・`11 22 * * 6`の4種）・
`Market_Pulse_Update.yml`（`35 21 * * 1-5`）の実際のcronを再確認した
結果、最速は`3 13 * * *`（UTC 13:03、毎日）。新設した
`Macro_Data_Update.yml`は`0 10 * * *`（UTC 10:00、毎日）とし、最速の
既存cronより3時間3分早く、他4件（21:35/22:07/22:11/22:15 UTC）より
11時間以上早く設定した。

**実装**: `.github/workflows/Macro_Data_Update.yml`新設（`workflow_
dispatch`の`series_ids`入力対応、`market_data`の2ワークフローと同じ
checkout/setup-python/pip install/commit・push/Summary構成）。
`.gitattributes`へ`common/macro_data/series/*.json`・
`macro_data_violations_log.json`のmerge=ours設定も追加。

**動作確認（代替検証の経緯）**: GitHub Actions側でworkflow_dispatchを
直接トリガーする手段（`gh` CLI・GitHubトークン）がこのセッション環境
になかった（`gh: command not found`、`GITHUB_TOKEN`等の環境変数も
未設定）。そのため、ワークフローが呼び出すのと**同一のエントリ
ポイント**（`python common/macro_data/fetcher.py`）を、この環境に
設定済みの実`FRED_API_KEY`を用いてローカルで直接実行し代替検証した
（GitHub Actions環境そのものでの実行確認は別途ユーザー側で
workflow_dispatchを手動トリガーする必要がある）。

結果: 25系列中**24系列が成功**（更新レコード合計94,909件）、`FTSD`の
みFRED API側で`Bad Request. The series does not exist.`（curlで
`https://api.stlouisfed.org/fred/series?series_id=FTSD`を直接叩いても
同一エラーを確認済み、fredapiライブラリ側の問題ではない）。`FTSD`は
`05_main.py::update_liquidity_csv()`の`WTREGEN`フォールバック先として
実装されているが、このフォールバックが発動する状況では実際には
機能しない可能性が高いと判明したため`[[MACRODATA-FTSD-SERIES-ID-
INVALID-1]]`として新規登録（05_main.py自体は今回変更しない）。

`macro_data_violations_log.json`は255件の警告を記録（全件
order-of-magnitude jump検知、duplicate as_of検知は0件）。内訳を
サンプル確認した結果、近ゼロ値を横断する拡散指数（`GACDFSA066MSFRBPHI`
36件・`CFNAI`70件・`SAHMCURRENT`3件）、2008年金融危機
（`WRBWFRBL`・`DGS3MO`各1件）・2020年COVID急変（`FEDFUNDS`1件）・
1980年代金利変動期（`T10Y2Y`7件）・2009-2011年のRRP制度低使用期
（`RRPONTSYD`136件）等、いずれも実在する経済事象・近ゼロ交差による
妥当な検知と判断した（データ品質問題ではない）。今回が全期間初回投入
（`start`指定なし＝FRED提供する最古データから全件取得）だったため
検知件数が多いが、これは想定内である。

**副次発見（設計上の考慮事項）**: `fetch_series()`/`fetch_all_series()`
は`start`未指定時に常に全期間履歴を再取得する設計であり、
`common/market_data/fetcher.py`の`fetch_daily_prices()`（日次は直近
のみ）と`backfill_daily_prices()`（全期間取得は一過性の別関数）という
分離を踏襲していない。このため`Macro_Data_Update.yml`の日次cronが
毎回全系列・全期間（合計約9.5万レコード・18MB）を再取得する非効率な
状態のまま稼働開始する。実害は限定的（FRED APIへの負荷・実行時間の
増加のみ、正確性への影響はupsertのため無し）だが、
`[[MACRODATA-FULL-HISTORY-DAILY-REFETCH-1]]`として新規登録した
（`--start`引数追加等の対応要否は次回判断）。

#### 本番消費者切替完了（2026-08-12、MIGRATION_CHECKLIST.md Step1〜3）

**Step1: 全消費者の洗い出し（実コードgrep結果）**

`05_main.py`（`Fred(`・`fred_latest(`・`fred_latest_with_prev(`・
`fred.get_series`を横断grep、想定箇所に加え2箇所を追加発見）:
- `get_fred()`（674行）→ 削除（`Fred()`インスタンス生成そのもの）
- `fred_latest()`（686行）→ `reader.get_latest()`ベースに全面書き換え
- `fred_latest_with_prev()`（701行）→ `reader.get_series()`ベースに
  全面書き換え（末尾2件を使用）
- `get_ff_current()`: `DFEDTARU`・`DFEDTARL`・`FEDFUNDS`（フォールバック）
- `get_implied_cuts()`: `DGS1`
- `get_financial_context()`: `T10Y2Y`・`BAMLH0A0HYM2`・`VIXCLS`
- `get_sp500()`: `SP500`（stooqフォールバックは維持）
- `fetch_event_row()`: `INDICATOR_CONFIG`の`fred_id`（NFP=`PAYEMS`は
  `fred_latest_with_prev`、他は`fred_latest`）＋3回リトライ＋指数
  バックオフ削除
- `refresh_monthly_indicators()`: `_MONTHLY_REFRESH_SET`7指標の
  `fred_id`（想定リストになかった追加発見。`fetch_event_row()`と同一
  指標を二重取得しうる構造だったが、切替後はローカルファイル読み取り
  のため実害なし）
- `update_liquidity_csv()`: `M2SL`・`WALCL`・`BAMLH0A0HYM2`・
  `WTREGEN`（→`FTSD`フォールバック）・`RRPONTSYD`・`WRBWFRBL`
- `update_fed_context()`: `get_zq_futures()`/`get_ff_current()`経由
  （想定リストになかった追加発見）
- `_load_sp500_cache()`（**追加発見**、`fred.get_series()`を`Fred\(`・
  `fred_latest\(`のgrepパターンでは検出できず気づかなかった箇所）:
  `fill_returns()`が複数日分のS&P500履歴を必要とするため、
  `reader.get_series(start=, end=)`（日付範囲指定）ベースに書き換え
- `fred_release_dates()`（458行）: **対象外**（`https://
  api.stlouisfed.org/fred/release/dates`への直接`requests.get()`で
  あり、fredapiクライアントの`Fred(`/`fred_latest(`とは別のAPI表面
  〈将来の発表日カレンダー、observation値ではない〉。
  `common/macro_data/`はカレンダー情報を持たないため切替対象外、
  リトライロジックも維持）

`collect_and_send.py`（3関数、想定通り）:
- `fetch_vxn_from_fred()`: `VXNCLS`（直近120日→MA50計算のため
  `reader.get_series(start=)`ベースに書き換え）
- `fetch_hy_spread_from_fred()`: `BAMLH0A0HYM2`（直近120日→90日
  min/max計算のため同上）
- `fetch_fred_short_bond()`: `DGS3MO`（直近30日→末尾2件の変化率計算の
  ため同上）

**切替方針の実装上の判断**: 依頼文は「`reader.get_latest(series_id)`
経由への統一」を主方針としていたが、実コード確認の結果、
`fred_latest_with_prev()`（NFP前月比計算に前月値が必要）・
`fetch_vxn_from_fred()`（MA50に50日分必要）・
`fetch_hy_spread_from_fred()`（90日min/maxに90日分必要）・
`fetch_fred_short_bond()`（前日比に前日値が必要）・
`_load_sp500_cache()`（複数日の履歴が必要）の5箇所は単一最新値だけでは
機能を維持できないと判明したため、これらのみ`reader.get_series()`
（期間指定）を使用し、それ以外（単一最新値で足りる約15箇所）は
`reader.get_latest()`を使用した。Step2の値突合で全項目一致を確認して
おり、この判断による機能面の後退はない。

**Step2: 切替前後の値突合（実施結果、2026-08-12実施）**

切替前（live FRED直接呼び出し）と切替後（`reader`経由）を同一セッション
内で実測比較した結果、**18項目全て完全一致（差分0件）**:

| 系列/関数 | 旧実装（live FRED） | 新実装（reader経由） |
|---|---|---|
| T10Y2Y | 0.48 @ 2026-08-11 | 0.48 @ 2026-08-11 |
| BAMLH0A0HYM2 | 2.7 @ 2026-08-10 | 2.7 @ 2026-08-10 |
| VIXCLS | 15.46 @ 2026-08-10 | 15.46 @ 2026-08-10 |
| DGS1 | 4.04 @ 2026-08-10 | 4.04 @ 2026-08-10 |
| DFEDTARU/DFEDTARL | 3.75/3.5 | 3.75/3.5 |
| FEDFUNDS | 3.63 @ 2026-07-01 | (フォールバック未使用、DFEDTARU/L成立のため) |
| SP500 | 7728.2 @ 2026-08-11 | 7728.2 |
| M2SL | 23155.2 @ 2026-06-01 | 23155.2 @ 2026-06-01 |
| WALCL | 6748567.0 @ 2026-08-05 | 6748567.0 @ 2026-08-05 |
| WTREGEN | 907324.0 @ 2026-08-05 | 907324.0 @ 2026-08-05 |
| RRPONTSYD | 1.25 @ 2026-08-11 | 1.25 @ 2026-08-11 |
| WRBWFRBL | 3002731.0 @ 2026-08-05 | 3002731.0 @ 2026-08-05 |
| PAYEMS（now/prev） | 158858.0@07-01 / 158881.0@06-01 | 同一 |
| get_ff_current() | 3.625 | 3.625 |
| get_financial_context() | yc=0.48/hy=2.7/vix=15.46/ff=3.625 | 同一 |
| get_sp500() | 7728.2 | 7728.2 |
| VXN（latest/vs_ma50） | 23.04 / -15.29% | 23.04 / -15.29% |
| HYスプレッド（current/min90/max90/expanding/contracting） | 2.7/2.63/2.87/False/False | 同一 |
| DGS3MO（latest/change_pct） | 3.89 / +0.517% | 3.89 / +0.517% |

差分0件だった理由: `common/macro_data/series/`のローカルストアが
同日（2026-08-12、`Macro_Data_Update.yml`のworkflow_dispatch実行）に
最新化されており、FRED日次系列は日中に再公表されないため、
live直接呼び出しと数時間前に取得済みのローカルストアの値が完全一致した。

`FTSD`（`WTREGEN`フォールバック先）は`reader.get_latest("FTSD")`が
`None`を返すことを確認したが、これは`[[MACRODATA-FTSD-SERIES-ID-
INVALID-1]]`で判明済みの通り旧実装でも`FTSD`自体がFRED上に存在せず
同じく取得失敗していたため、**今回の切替による回帰ではない**
（フォールバック構造自体は変更せず維持）。

**Step3: 旧参照の最終確認（grep結果）**

```
grep -n "Fred(\|from fredapi\|fred\.get_series" src/market/macro_pulse/05_main.py
→ 1件（`_load_sp500_cache()`のdocstring内、コメントで旧実装を説明する文言のみ）
grep -n "Fred(\|from fredapi\|fred_api_key" src/market/market_pulse/collect_and_send.py
→ 4件（いずれも切替を説明するdocstring/コメント内のみ）
```
実コード上の直接呼び出しは**0件**。両ファイルとも`fred`パラメータ・
リトライ/指数バックオフロジック（`fetch_event_row()`の3回リトライ）も
削除済み（`fred_release_dates()`は対象外のため維持）。

**テスト**: `tests/test_macro_pulse_logic.py`の`TestFredLatestWithPrev`・
`TestFetchEventRowNFPDiff`（計7件）が旧`_FakeFred`パターンで失敗した
ため、`main05._md_reader.get_series`/`get_latest`をmonkeypatchする方式
に更新（`[[MACRODATA-FTSD-MISSING-FROM-INVENTORY-1]]`等での
`_get_market_data_attributes`monkeypatchパターンを踏襲）。pytest全体
771 passed / 2 known-failed（`[[TEST-STALE-IV-1]]`）。

これにより`common/macro_data/`（FRED統合層）は`fetcher.py`/`reader.py`
実装・定期取得ワークフロー・本番消費者2ファイル全数切替が完了し、
**`common/market_data/`と同じ「完成」状態に到達した**。

#### 次セッションでの着手順序（2026-08-12時点、フェーズ3着手・分類C3件のBACKLOG整理完了を反映）
1. `common/macro_data/`構築プロジェクト自体は完成。フェーズ1（一次
   データ層の構築）・フェーズ2（過去データ移管）はいずれも完了:
   - フェーズ1: `common/sec_data/`・`common/market_data/`・
     `common/macro_data/`の3コンポーネントとも完成（`PROJECT_STATUS.md`
     フェーズ1表参照）
   - フェーズ2: `[[PHASE2-MIGRATION-POLICY-DECIDED-1]]`（移行方針確定）・
     `[[MACRODATA-BAMLH0A0HYM2-HISTORY-EXCEPTION-1]]`（FRED、
     `BAMLH0A0HYM2`のみ例外的移行を実装・実行完了、他23系列は対象外）・
     `[[PHASE2-SECDATA-FULL-DEPTH-VERIFICATION-1]]`（SEC EDGAR、全105
     銘柄精査完了・フェーズ2対象外と確定）・
     `[[PHASE2-YFINANCE-REFETCH-DESIGN-1]]`（yfinance、投資調査の結果
     移行作業不要・フェーズ2対象外と確定）・取得前提条件（当初調査
     時点で対象外と判定済み）の4データソース全てに結論確定済み
2. **フェーズ3（導出データ層の管理方法検討）着手済み**:
   - 分類C14件のうち3件（設定ファイル配置・重複問題）をBACKLOG登録済み
     （実装は未着手）: `[[PORTFOLIO-CONFIG-DUP-1]]`（`INPUT-C-008`、
     Portfolio二重保持）・`[[TAILKPI-CONFIG-LOCATION-1]]`
     （`INPUT-C-009`、`tail_kpi_map.json`のconfig外配置）・
     `[[FCFCONFIG-LOCATION-1]]`（`INPUT-C-010`、
     `fcf_conversion_config.json`のconfig外配置）
   - `FIELD_DEFINITIONS.md`499項目の新DB参照への切替は未着手。次の
     アクションは、まず対象件数（yfinance/FRED由来で`common/
     market_data/`・`common/macro_data/`への参照に未更新の項目数）を
     数える調査から（`common/sec_data/`は既に13箇所で参照済みと
     フェーズ3投資調査で確認済み、`common/market_data/`・
     `common/macro_data/`は0件）
   - 分類C残り11件（`INPUT-C-001〜007`・`011〜014`）の管理方法検討は
     未着手
3. （本線外）SEC EDGAR全105銘柄精査で新規発見した異常ケース:
   `[[SECDATA-ENB-NORMALIZATION-MISSING-1]]`（ENBの正規化データ
   〈annual_*.json/quarterly_*.json〉が1件も生成されていない、原因調査
   未着手）
4. （本線外）今回発見した2件の対応要否判断:
   `[[MACRODATA-FTSD-SERIES-ID-INVALID-1]]`（`FTSD`系列がFRED上に
   存在しない、`05_main.py`側の対応要否）・`[[MACRODATA-FULL-HISTORY-
   DAILY-REFETCH-1]]`（日次cronの全期間再取得の非効率、`--start`
   引数追加等の対応要否）
5. （本線外）新規発見のうち残る優先度中1件の対応要否判断:
   `[[MACRODATA-SCHEDULED-SILENT-GAP-CSCICP-USALOL-1]]`（実データ確認が
   着手条件）。`[[MACRODATA-AS-IS-DUPLICATION-UNDERCOUNT-1]]`は
   2026-08-13、`[[FRED-HYSPREAD-TRIPLE-FETCH-1]]`と同型の理由で解消・
   BACKLOG_DONE.mdへ移動済み
6. （本線外）過去セッションで蓄積した低優先度課題群一式:
   `[[MARKETDATA-CWAN-FROZEN-DATA-SUSPECT-1]]`・`[[MARKETDATA-SP500-
   SCRAPE-INVALID-TICKERS-1]]`・`[[MARKETDATA-VIX9D-DATA-GAP-1]]`・
   `[[STONKS-SILO-CLI-TICKERS-SHADOW-1]]`等（`[[MACRODATA-IMPORT-
   HISTORY-CONFIG-DRIFT-1]]`・`[[NETCASH-DUAL-CALC-1]]`は解消済み・
   BACKLOG_DONE.mdへ移動済み）

**注記（2026-08-15、フィールド単位の切替完了確認）**: `FIELD_
DEFINITIONS.md`499項目単位での新DB参照切替状況を集計する投資調査を
実施した結果、`common/macro_data/`（FRED）由来の一次データ10件
（AS-IS-190・192・194・197・199・200・210・211・212・352）が全件
切替済みであることを実コードで確認した（詳細は`PROJECT_STATUS.md`
フェーズ3参照）。ファイル単位（本番消費者2ファイル＋周辺ツール1件）の
切替完了に加え、フィールド単位でも本線タスクの完了を確認できた。

#### 着手条件
なし（`common/macro_data/`本体・フェーズ1・フェーズ2はいずれも完了。
フェーズ3は分類C3件のBACKLOG登録・`FIELD_DEFINITIONS.md`切替調査
（2026-08-15完了）まで完了、残り11件の検討・ENB異常ケース・本線外
課題群のみ残置）。

---

### [SECDATA-ENB-NORMALIZATION-MISSING-1] ENB（Enbridge）の正規化データ（annual_*.json/quarterly_*.json）が1件も生成されていない
**状態:** 未着手
**優先度:** 中（監視対象銘柄でありながら本番データが欠落しているため）
**分類:** データ品質 / `common/sec_data/`正規化パイプライン
**登録日:** 2026-08-12
**発見:** フェーズ2 SEC EDGAR全105銘柄精査（`[[PHASE2-SECDATA-FULL-
DEPTH-VERIFICATION-1]]`、チャット記録、2026-08-12）

#### 内容
`config/monitor_tickers.yaml`（85行目）で監視対象として登録されている
ENB（Enbridge Inc.）について、`common/sec_data/data/ENB/`配下に
`company_facts.json`（SEC EDGAR生アーカイブ、599概念）・
`submissions.json`は存在するが、正規化済みデータ（`annual_*.json`・
`quarterly_*.json`）が**1件も生成されていない**ことが、フェーズ2
投資調査（SEC EDGAR全105銘柄の履歴深度精査）の過程で発見された。

#### 対応方針（未定）
なぜENBだけ正規化パイプラインが機能していないのか（銘柄固有のXBRL
データ構造の問題か、処理時のエラーが握りつぶされているか等）の原因
調査が必要。原因調査は次回以降に別途着手する。

#### 着手条件
なし。

---

### [MACRODATA-FTSD-SERIES-ID-INVALID-1] FRED系列コード「FTSD」がFRED API上に実在しない（05_main.pyのWTREGENフォールバックが機能しない可能性）
**優先度:** 中で据え置き（2026-08-13事実確認の結果、実害は極めて稀と
確認できたため引き上げ不要と判断。ただし機能しないフォールバックを
放置すべきではないため記録は残す。詳細は下記「追記」参照）
**分類:** バグ疑い / データソース側の系列コード誤り
**登録日:** 2026-08-12
**更新日:** 2026-08-13（事実確認調査完了。原因特定・実害実績確認・
修正案提示。詳細は下記「追記」参照。実装コード変更なし）
**発見:** `common/macro_data/`定期取得ワークフロー新設・動作確認
（`fetch_all_series()`の実FRED_API_KEYによるローカル実行、チャット
記録、2026-08-12）

#### 内容
`common/macro_data/fetcher.py::fetch_series("FTSD")`を実行したところ、
fredapi経由・`curl`による直接FRED REST API呼び出し
（`https://api.stlouisfed.org/fred/series?series_id=FTSD&api_key=...`）
の両方で`{"error_code":400,"error_message":"Bad Request.  The series
does not exist."}`が返り、**`FTSD`はFRED上に実在しない系列コードで
あることを確認した**（ネットワーク一時障害やfredapiライブラリ側の
問題ではなく、系列コード自体が無効）。

`05_main.py::update_liquidity_csv()`は`WTREGEN`（TGA残高）取得失敗時に
`FTSD`へフォールバックする実装になっている（1959-1960行:
`if tga_val is None: tga_val, _ = fred_latest(fred, "FTSD",
target_date, lookback=21)`）が、このフォールバックが実際に発動しても
`FTSD`自体が無効な系列コードのため取得は失敗し、TGA値は結局取得
できないままになると推定される。`FTSD`は
`[[MACRODATA-FTSD-MISSING-FROM-INVENTORY-1]]`（`INPUT_DATA_TOBE.md`の
24系列台帳への追加漏れ、`INPUT-A-049`として2026-08-12に対応済み）で
台帳に追加した系列だが、台帳追加時点では実際にFRED上に存在するかの
検証は行っていなかった。

#### 追記（2026-08-13、事実確認調査完了、記録のみ・実装なし）

**原因特定**: `FTSD`は2026-05-08のコミット`8561125f3`（`Co-Authored-By:
Claude Sonnet 4.6`、NET LIQUIDITY計算のためWTREGEN/RRPONTSYD取得を
追加した際にフォールバック先として導入）で、実在確認なしに導入されて
いたことをコミット履歴で確認した。コミットメッセージ・コードいずれにも
典拠の記載はない。

**正しい代替系列の特定**: FRED検索API（`search_text=treasury general
account`）で調査した結果、`WDTGAL`（Liabilities and Capital: Deposits
with F.R. Banks, Other Than Reserve Balances: U.S. Treasury, General
Account: **Wednesday Level**）が有力な代替候補と判明。`WTREGEN`
（**Week Average**）と同一カテゴリ・同一期間（2002-12-18〜2026-08-05、
現在も更新中）・同一単位（Millions USD、週次）でありながら集計方法が
異なる（週平均 vs 水曜時点値）ため、名目だけの重複ではなく実務上意味の
あるフォールバックになる。なお同種の旧系列`WLTGAL`・`LDGUST`は2018年に
DISCONTINUEDと確認済みのため候補外。`search_text=FTSD`はFRED検索でも
0件ヒットで、類似候補すら存在しない。

**実害実績の確認**: `docs/market-monitor/macro-pulse/data/
05_liquidity.csv`（2023-01-01〜現在、1302日分）を全件確認した結果、
`tga`列が空欄なのは**2026-05-31の1件のみ**（前日5/30・翌日6/1は正常
取得）。この日、`WTREGEN`取得失敗→`FTSD`へフォールバック→`FTSD`も
無効のため結局取得失敗、という実際の発火・失敗の実績を確認した。
同日`net_liquidity`列（`=(WALCL−TGA−RRP)/1,000,000`）も算出不能で
空欄。`stealth_signal`列はその日も"neutral"のまま記録が継続しており
致命的な誤判定はないが、NET LIQUIDITY系列に1日分の欠測点が生じていた。
WTREGEN自体の失敗頻度は1302日中1日（約0.08%）で極めて低頻度。

**新アーキテクチャ（`[[MACRODATA-LAYER-CONSTRUCTION-1]]`切替後）での
位置づけ**: 現行`fred_latest()`は`reader.get_latest()`を呼ぶのみで、
旧実装が持っていた`target_date`基準・`lookback`日数ウィンドウの制約が
廃止されている。ローカルの`series/WTREGEN.json`に一度でも値が書き込ま
れていれば、当日の取得が一時的に失敗しても直近キャッシュ値をそのまま
返すため、フォールバック発動条件（`reader.get_latest("WTREGEN")`が
Noneを返す）は「`WTREGEN`系列ファイル自体が存在しない／空」という、
旧実装よりさらに稀なケースに限定される。初回投入時点でWTREGENは25系列
中の成功24系列に含まれており、現状ローカルにデータが存在するため、
現行アーキテクチャ下ではこのフォールバックが発動する可能性はさらに
低下していると評価できる。ただし「発動条件が稀になったこと」と
「発動時に機能するか」は別問題であり、後者（`FTSD`が無効）は現在も
未解消。

**修正案（未実装、次回対応時の実装指針）**:
1. `05_main.py::update_liquidity_csv()`のフォールバック先を
   `"FTSD"`→`"WDTGAL"`に変更
2. `common/macro_data/series_meta.json`に`WDTGAL`エントリを新規追加
   （`category: "liquidity"`、`consumers: ["05_main.py::
   update_liquidity_csv (WTREGENフォールバック候補)"]`）。追加すれば
   `fetch_all_series()`が自動的にバッチ取得対象に含める
3. `INPUT_DATA_TOBE.md`/`INPUT_DATA_AS_IS.md`の`FTSD`
   （`INPUT-A-049`）記載を`WDTGAL`に置き換えるか、無効系列だった旨の
   注記を追加

**優先度判断**: 実害頻度は旧実装でも0.08%、新実装ではさらに稀と推定
されるため、優先度「中」からの引き上げは不要と判断し据え置く。一方で
「一度も機能しないフォールバックが存在し続ける」こと自体は望ましくない
ため、記録は残す。

#### 着手条件
次回の低優先度課題群まとめ対応時（`[[MACRODATA-AS-IS-DUPLICATION-
UNDERCOUNT-1]]`・`[[MACRODATA-SCHEDULED-SILENT-GAP-CSCICP-USALOL-1]]`・
`[[MACRODATA-IMPORT-HISTORY-CONFIG-DRIFT-1]]`・
`[[MACRODATA-FULL-HISTORY-DAILY-REFETCH-1]]`等と合わせて着手検討）。
上記「修正案」を踏まえ、対応方針は事実上確定済み。

---

### [MACRODATA-FULL-HISTORY-DAILY-REFETCH-1] fetch_series()/fetch_all_series()がstart未指定時に常に全期間履歴を再取得する設計になっている（日次cronが非効率）
**優先度:** 低〜中（実害は限定的〈FRED APIへの負荷・実行時間増加のみ、
upsert設計のため正確性への影響はない〉が、`common/market_data/`が
確立した「日次は直近のみ・全期間取得は一過性の別関数」という設計
パターンから逸脱している）
**分類:** 設計改善 / 効率性
**登録日:** 2026-08-12
**発見:** `common/macro_data/`定期取得ワークフロー新設・動作確認
（`fetch_all_series()`の実FRED_API_KEYによるローカル実行、チャット
記録、2026-08-12）

#### 内容
`common/macro_data/fetcher.py::fetch_series(series_id, start=None)`は
`start`未指定時、`observation_start`パラメータをFRED APIへ渡さない
ため、系列の提供開始日（系列によっては1940〜1970年代）からの**全期間
履歴**を毎回取得する。`.github/workflows/Macro_Data_Update.yml`
（毎日UTC10:00実行、`python common/macro_data/fetcher.py`を`start`
指定なしで呼び出す）はこの関数を経由するため、**日次cronが実行の
たびに25系列全件・合計約9.5万レコード（初回実測、18MB）を毎回
再取得する**設計になっている。

これは`common/market_data/fetcher.py`が確立した設計パターン
（`fetch_daily_prices()`＝日次cronは直近数日分のみ取得・
`backfill_daily_prices(period/start)`＝全期間取得は定期cronに
組み込まない一過性の別関数）から逸脱している。`update_series()`は
日付単位のupsertのため正確性への実害はないが、FRED APIへの負荷・
GitHub Actions実行時間・git差分サイズが日次cronとしては不必要に
大きい。

#### 対応方針（未定）
- `fetcher.py`のCLIへ`--start`引数を追加し、`Macro_Data_Update.yml`の
  日次cron呼び出し側は直近数日〜数週間分のみを指定する
  （`common/market_data/`の`fetch_daily_prices()`相当の設計に揃える）
- 初回の全期間投入は今回実施済みのため、以降は「直近分のみ日次取得・
  全期間再取得が必要な場合のみ手動で`--start`省略実行」という運用に
  切替える

#### 着手条件
なし。次回`common/macro_data/`関連作業時に対応要否を判断する。

---

### [MACRODATA-FETCH-FAILURE-VISIBILITY-GAP-1] 系列単位の取得失敗がviolations_log.jsonで「正常」と区別できない
**優先度:** 中（実害は現時点でFTSD1件のみ確認済みだが、今後同様の
失敗〈系列ID変更・FRED側仕様変更等〉が起きても気づけない構造的リスク）
**分類:** 設計上のギャップ / 可視性欠如
**登録日:** 2026-08-15
**発見:** `common/macro_data/`更新実行実績・データ鮮度の確認調査
（チャット記録、2026-08-15）

#### 内容
`fetch_series()`は失敗時に例外を投げずNoneを返す設計（print()ログの
みでリポジトリには残らない）。`update_series()`はNone時に
`{"updated": 0, "warnings": []}`を返し`violations_log.json`へ書き込む
が、この構造は正常に0件警告だった健全な系列と区別がつかない。
FTSDエントリ（`{"checked_at": ..., "warnings": []}`）が実例。
`series/{ID}.json`ファイルが存在しないことに能動的に気づかない限り、
取得失敗を発見できない。

加えて、`fetch_all_series()`のforループには系列単位のtry/exceptが
なく、予期しない例外（ディスクエラー等）が発生した場合、その系列
以降の全系列が未処理のままバッチ全体が中断する構造的リスクも
あわせて確認された（今回の3日間の実行では未発生）。

#### 対応方針（未定）
- `violations_log.json`に「fetch自体の成否」を示すフィールド
  （例: `fetch_status: "success"/"failed"/"skipped"`）を追加する
- `fetch_all_series()`のforループに系列単位のtry/exceptを追加し、
  1系列の失敗が他系列の処理を止めないようにする
- 週次等の定期監視（`audit.py`型の診断ツール）で
  `series_meta.json`の全系列と`series/`ディレクトリの実ファイルを
  突合し、欠落を検知する仕組みを追加する

#### 着手条件
なし。対応方針の具体化から。

---

### [MARKETDATA-CWAN-FROZEN-DATA-SUSPECT-1] CWANのyfinance日次データが1日分・出来高0のフリーズ状態で取得される
**優先度:** 低（監視銘柄1件のみ・実害は限定的、`daily_price_validation`が
既に警告フラグ付きで検知・保存継続しており実害顕在化はしていない）
**分類:** データ品質疑い / 外部データソース側の異常疑い
**登録日:** 2026-08-11
**発見:** `common/market_data/`日次価格層バックフィル（`backfill_daily_prices()`、
period=1y）実行時（チャット記録、2026-08-11。前回2026-08-10の同種
バックフィル検証時にも同一事象を確認済みだが、当時は未登録のまま
作業ツリーごと消失していたため今回改めて登録する）

#### 内容
`CWAN`（Clearwater Analytics、`config/monitor_tickers.yaml`監視銘柄・
`config/beta_config.json`に`source: "yfinance_5yr_2026"`のアクティブな
βオーバーライドを持つ実在の上場企業）に対し`yf.download(period="1y")`で
バックフィルを実行したところ、**1日分（2026-07-02）のデータしか返らず、
かつそのレコードはopen=high=low=close（完全に同一値）・volume=0という
「フリーズしたような」異常な形状**だった。`validate_price_record()`が
`volume must be > 0`として正しく検知・警告フラグを付けて保存継続している
（保存拒否はしない設計通り、実害は生じていない）。

通常の`fetch_daily_prices()`（period="5d"の日次バッチ）でも同様の事象が
起きるかは未確認（バックフィル=period="1y"でのみ確認済み）。

#### 対応方針（未定）
- まずyfinance公式（Yahoo Finance）でCWANの実際の価格チャートを確認し、
  一次情報として本当にデータが存在しないのか、取得側の問題かを切り分ける
  （`[[MP-IRX-FRED-1]]`の教訓「取得コード側の失敗とデータソース側の
  データ不在は別問題」を踏まえること）
- 単発の事象か、繰り返し発生するかを次回バックフィル・日次バッチ実行時に
  再確認する
- 実害が顕在化した場合（`get_ma_deviation()`等の計算に影響する場合）の
  み優先度を上げて対応する

#### 着手条件
なし。優先度低のため次回同種事象の再確認時に着手判断する。

---

### [MARKETDATA-SP500-SCRAPE-INVALID-TICKERS-1] get_sp500_constituents()のWikipediaスクレイピングに不正銘柄コード（FDXF/HONA/Q）が混入
**優先度:** 低（実害は限定的。該当銘柄の日次データ取得が無駄になる程度で、
`validate_price_record()`等の検証機構は正常に機能し保存自体は成立する）
**分類:** バグ疑い / データソース側スクレイピングの解析精度
**登録日:** 2026-08-11
**発見:** `common/market_data/`日次価格層バックフィル全母集団実行時
（チャット記録、2026-08-11。前回2026-08-10の同種バックフィル検証時にも
同一事象を確認済みだが、当時は未登録のまま作業ツリーごと消失していた
ため今回改めて登録する）

#### 内容
`fetcher.py::get_sp500_constituents()`（Wikipedia
`List_of_S%26P_500_companies`テーブルを`pandas.read_html()`でスクレイピング）
の取得結果に、正規のS&P500構成銘柄コード（`FDX`・`HON`）とは**別に**
`FDXF`・`HONA`という不正な銘柄コードが混入していることを確認した
（`common/market_data/_sp500_constituents_cache.json`実測: `FDX`/`FDXF`・
`HON`/`HONA`がいずれも別エントリとして両方存在、総数503件）。加えて
`Q`という短い銘柄コードも含まれており、こちらは実在ティッカーの
可能性もあるが要確認。実際にこの3銘柄（`FDXF`・`HONA`・`Q`）へ
`backfill_daily_prices()`を実行したところ、正規のS&P500構成銘柄と異なり
それぞれ52日・39日・197日分という不完全な履歴しか取得できず、実在しない
または別の性質を持つ銘柄コードである可能性が高い。

推定原因: Wikipediaのテーブル構造変化・脚注マーカーの混入・列ズレ等に
よる`pandas.read_html()`側のパース精度問題（未特定）。

#### 対応方針（未定）
- `get_sp500_constituents()`のWikipediaスクレイピング結果を手動で
  Wikipedia実ページと突合し、`FDXF`/`HONA`/`Q`がどの行・どのセルから
  混入しているか特定する
- 原因判明後、パースロジックに除外フィルタ（例: 既知の正規ティッカーと
  重複するprefixを持つ不審なコードを除外する、またはテーブル列数の
  妥当性チェックを追加する）を実装する
- 対症療法として不正コードのブロックリストを設ける案もあるが、
  Wikipedia側の構造変化のたびに再発しうるため根本原因の特定を優先する

#### 着手条件
なし。優先度低のため`common/market_data/`本線完了後の低優先度タスクと
して余裕があるときに着手する（2026-08-13更新: 登録時点の「着手順序4の
残作業と並行」という前提は、`common/market_data/`本番消費者切替が全数
完了したことで消滅した。バグ自体〈不正銘柄コードの混入〉は未解消の
まま有効）。

---

### [MARKETDATA-VIX9D-DATA-GAP-1] ^VIX9Dのyfinanceデータに約1ヶ月の欠落期間（2026-07-17〜08-10）が存在する
**優先度:** 中（`collect_and_send.py`のsentiment_score算出
〈vix_level補正〉・VIX9D対VIX比較の直接入力のため、`[[MARKETDATA-
CWAN-FROZEN-DATA-SUSPECT-1]]`より実害の潜在範囲が広い。ただし現時点の
実測ではsentiment_scoreへの影響はゼロと確認済み、詳細は「内容」参照）
**分類:** データ品質疑い / 外部データソース側の異常疑い
**登録日:** 2026-08-11
**発見:** `[[MARKETDATA-LAYER-CONSTRUCTION-1]]`着手順序4-6
（`collect_and_send.py`切替）のStep3検証中（チャット記録、2026-08-11）

#### 内容
`common/market_data/daily/^VIX9D.json`（`period="1y"`バックフィル済み）
を確認したところ、2026-07-17を最後に次のレコードが2026-08-10まで
存在しない（約1ヶ月分の欠落）。**yfinance側の問題であることを実測で
確認済み**: `yf.Ticker("^VIX9D").history(period="1mo")`を実行しても
Yahoo Finance自体が2026-07-13〜07-17の5件しか返さず、`period="5d"`では
2026-08-10の1件のみしか返らない。取得コード側の不具合ではなくデータ
ソース側の欠落（`[[MP-IRX-FRED-1]]`の教訓通り、一次情報〈yfinance直接
呼び出し〉で切り分け済み）。

実害範囲: `collect_and_send.py::get_realtime_data()`のVIX9D関連2出力
（メイン指標表示・VIX9D対VIX比較）と`compute_sentiment()`の
`vix_level`サブスコア補正（VIX9D逆転時-0.05）が、直近2営業日の実データ
不足により中立デフォルト（None・補正なし）にフォールバックする。
2026-08-11時点の実測比較では、`compute_sentiment()`の`vix_level`
サブスコアは切替前後（yfinance直接呼び出し版・market_data版）で完全
一致しており、両者ともVIX9D欠落の影響を同一に受けている（本切替による
新規劣化ではない）ことを確認済み。

#### 対応方針（未定）
- 単発の事象か、繰り返し発生するかを次回日次バッチ実行時に再確認する
- yfinance側でVIX9Dのデータ提供が回復するかを継続監視する
- 実害が拡大した場合（sentiment_scoreの結果自体に有意な影響が出る場合）
  のみ優先度を上げ、代替データソース（CBOE公式等）への切替を検討する

#### 着手条件
なし。優先度中だが実害は現時点でゼロと確認済みのため、次回同種事象の
再確認時に着手判断する。

---

### [STONKS-SILO-CLI-TICKERS-SHADOW-1] pipeline.pyのCLIティッカー指定実行が変数名衝突で必ず失敗する
**優先度:** 中（デフォルト全件実行の自動cronは影響を受けないが、個別
ティッカー指定でのCLI手動実行——新規登録直後の確認等——が現在完全に
機能しない）
**分類:** バグ / 変数名衝突 / STONKS SILO
**登録日:** 2026-08-11
**発見:** `[[MARKETDATA-LAYER-CONSTRUCTION-1]]`着手順序4-3（`valuation_
fetcher.py`切替）のStep3検証中（チャット記録、2026-08-11）

#### 内容
`discover/stonks-silo/src/pipeline.py`の`if __name__ == "__main__":`
ブロックが`tickers = sys.argv[1:] if len(sys.argv) > 1 else None`という
モジュールレベル変数代入を行っており、これがファイル冒頭で`from
common.sec_data import tickers`によりimportされたモジュール参照を
グローバルスコープごと上書きしてしまう。結果として`python pipeline.py
TICKER1 TICKER2`のようにティッカーを指定して実行すると、`run()`内部の
`_filter_stonks_silo_tickers()` → `stonks_tickers()`が
`tickers.get_stonks_silo_tickers()`を呼ぼうとした時点で`tickers`が
（モジュールではなく）CLI引数のリストになっており
`AttributeError: 'list' object has no attribute 'get_stonks_silo_tickers'`
で必ず失敗する（実機確認済み、2026-07-12の最終更新時点から存在する
既存バグ、今回の`market_data`切替とは無関係）。

引数なし実行（`python pipeline.py`、`stonks_silo=true`全件処理、
Stonks_Silo_Update.ymlの自動cronが使う経路）は`run(None)`が呼ばれるため
`partial=False`分岐となり、こちらも同じグローバル`tickers`上書きの影響を
受けるはずだが要実機再確認（`stonks_tickers()`が`tickers`モジュールを
参照する点は同じ）。

#### 対応方針（未定）
`__main__`ブロックの変数名を`tickers`から別名（例: `cli_tickers`）に
変更するだけの軽微な修正で解消できる見込み。修正後、CLI引数あり・
なし両方の実行パスで動作確認すること。

#### 着手条件
なし

---

### [LAYER3-ANNUAL-MISCLASSIFICATION-NOW-RMBS-1] _classify_period()のfp=='FY' and days>130判定漏れが、BBAI以外にNOW（41件）・RMBS（16件）でも広範に該当
**優先度:** 中（`[[LAYER3-ANNUAL-MISCLASSIFICATION-BBAI-1]]`と同型だが、NOW/RMBSでの実害〈Moat Score等への影響〉は未確認）
**分類:** バグ疑い / 期間分類ロジックの誤判定
**登録日:** 2026-08-06
**発見:** `[[LAYER3-ANNUAL-MISCLASSIFICATION-BBAI-1]]`対応時の全銘柄横断スキャン（チャット記録、2026-08-06）

#### 内容
BBAI修正時に採用した「同一accn・同一start日内に複数end日付を持つ
fp=='FY'エントリを除外」方式が同様に適用できるか、NOW・RMBSの
実データで確認した上で、pipeline.py計算への実害有無を検証する必要が
ある。

#### 着手条件
BBAI修正の本番適用後、実害調査から着手。

### [LAYER3-ANNUAL-MISCLASSIFICATION-MINOR-5TICKERS-1] ASTS/SPIR/DELL/VRT/METAで同型の判定漏れが1〜3件ずつ孤立的に該当
**優先度:** 低
**分類:** バグ疑い / 期間分類ロジックの誤判定（軽微）
**登録日:** 2026-08-06
**発見:** `[[LAYER3-ANNUAL-MISCLASSIFICATION-BBAI-1]]`対応時の全銘柄横断スキャン（チャット記録、2026-08-06）

#### 内容
該当件数が少なく特定のconcept・accnに限定されるため、実害有無の
確認を含め優先度を下げる。

#### 着手条件
なし。

### [SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1] common/sec_data再設計の運用方針確定（フィックス機構・銘柄数絞り込み・新規登録フロー）— Stage 2〜3残タスク
**優先度:** 高
**分類:** アーキテクチャ再設計 / 運用方針確定・実装
**登録日:** 2026-08-04
**更新日:** 2026-08-05（Stage 1完了。詳細はBACKLOG_DONE.md「2026-08-05
（完了）」参照。以下はStage 2〜3の残タスクのみ記載）
**発見:** common/sec_data一次データ取得層 再設計 運用方針検討（chat記録）

#### 内容（要約。運用方針・スキーマ設計・Stage 1実装の全詳細は
BACKLOG_DONE.md「[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]] Stage 1」参照）
`common/sec_data/`再設計の運用方針3点（フィックス機構・銘柄数絞り込み
基準・新規登録フロー）を確定し、フィックス機構（`fixed_registry.json`、
銘柄×年度単位の差分適用方式）のスキーマ設計・`parser.py`/`utils.py`/
`report_consistency_check.py`（CHECK-31/WARN-31）への実装・taxonomy属性
①〜⑧非該当26銘柄・372銘柄×年度エントリのStage 1登録・検証（全105銘柄
再パースで無変化確認、pytest 497 passed/2 known failed、NG=0確認）まで
完了した（機能コミット`7c15b2a75`、BACKLOG更新コミット`ae88715c5`、
いずれもpush済み）。

**残タスク（Stage 2〜3、未着手）**: taxonomy属性①〜⑧該当58銘柄
（AAPL, ABBV, APGE, ASTS, AVAV, AVGO, BBAI, BKNG, BROS, CAKE, CART,
CAT, CELH, CEG, CIX, COHR, CON, CPRT, DELL, ELF, ESTC, FICO, GEV,
GOOGL, HEI, HON, IONQ, JOBY, KLAC, LITE, LLY, LRCX, MO, MRVL, MSFT,
NOW, NVDA, ONDS, PAYS, PLTR, PM, RCAT, RDW, RKLB, RMBS, SCCO, SN,
SNPS, SOFI, SOUN, SPIR, TER, TSLA, V, VRT, VST, WST, XOM）のうち、
BACKLOG_DONE.mdで個別バグ対応が完了・確認済みの年度をStage 2として
`fixed_by: manual_verification`で登録する作業（次のアクション）。
Stage 3（属性該当銘柄でOPEN課題が残る年度は保留のまま）も未着手。

#### 対応方針
次のステップとして、Stage 2対象銘柄×年度リストの生成（属性該当58銘柄の
うちBACKLOG_DONE.mdで解消済み確認済みの年度の洗い出し）に着手する。
Stage1〜2の対象範囲生成結果は差分としてユーザーに提示し、確認を経てから
`fixed_registry.json`へ一括登録する運用（[[CHECK29-COHR-CROSS-ACCN-
TEMPORARY-EQUITY-1]]の教訓「対象サブセットのみへのシミュレーションでは
既解決集団への回帰を見逃す——常に全母集団で再シミュレーションすること」
を踏襲）を継続する。

#### 着手条件
なし。優先度高（sec_data再設計の土台となる方針決定のため）。Stage 1は
実装完了、Stage 2〜3が残タスク。

#### 完了報告の必須項目
- 反映されたコミットハッシュ

---

### [RCAT-FCF-5YR-AVG-ACTUAL-3YR-1] RCATのget_fcf_5yr_avg()が実質2021-2023年の3年平均になっておりDCFのFCFベース値計算に構造的な実害がある
**優先度:** 高（登録時）→低（実装前シミュレーションの結果、実害なしと判明）
**分類:** バグ / 確定・現在進行形の実害・DCF計算に直結
**登録日:** 2026-08-02
**訂正日:** 2026-08-02（パターンB実装前シミュレーション結果を反映）
**発見:** [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]実害確認
調査（チャット記録）

#### 内容
`reader.py::get_fcf_5yr_avg()`は、`get_annual_range(ticker, 5)`（直近5
ファイル）からNoneを除外して平均する設計のため、RCATでは
[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のOCF欠落により、
実質2021〜2023年の3年分のみで計算された値が「5年平均」として扱われて
いる（`latest.json`実測: `fcf_history`直近2件〈2024・2025〉が
`fcf: None`）。

RCATの真のFY2024 OCF（継続+非継続合算）は約-$18.6M、真のFY2025 OCFは
約-$89.1M（現在使用中の代替年度2021-2023年、-$1.4M〜-$31.6Mより大幅に
悪化）であり、これらが平均計算から欠落している。前回
（[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]調査）は成長率決定
（`determine_growth_rate()`が`segment_weighted`優先でFCF非参照）のみを
確認し「実害なし」と結論していたが、DCFの基礎となるFCFベース値の計算
経路（`get_fcf_5yr_avg()`→`adjust_fcf()`→`determine_fcf_base()`→
`fcf_base_used=$16,564,815`）は未確認であり、この訂正版調査で構造的な
実害を確認した。

#### 影響
売上高フロア補正（`latest_revenue`基準）・変動係数ベースの補正層が感応度
をある程度緩和している可能性は確認済みだが、「2024/2025年の真のOCFを
含めていた場合とIVが実際に何ドル変わるか」の精密な定量化は未実施。RCATの
tanuki_score・IV・Classificationへの最終的な影響度は未定量化のまま。

#### 対応方針
未定。[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（RCATパターン
B、継続+非継続の合算、営業活動限定タグでのガード付き）の解決が前提と
なる可能性が高い。合算後、`annual_2024.json`・`annual_2025.json`に
`operating_cash_flow`が充足されれば、`get_fcf_5yr_avg()`は自動的に正しい
5年平均に復旧すると見込まれる（reader.py側の追加修正は不要な可能性）。
ただし、この見込みの検証と、充足後の最終IV・Classificationへの影響
定量化が実装前に必要。

#### 実害訂正（2026-08-02、パターンB実装前シミュレーション結果・チャット記録）
上記「reader.py側の追加修正は不要」という見込みの検証を実施した結果、
そもそも**RCATの本番FCF計算がreader.py::get_fcf_5yr_avg()（年次ファイル
ベース）を一切使用していない**ことが判明した。`data_fetcher.py::
_select_fcf_source()`が、四半期10-Qの4四半期ロール集計である
TTM系列（`common/sec_data/ttm/RCAT_ttm_series.json`）を常に優先採用する
設計であり、この系列は年次10-Kの継続/非継続事業分割タグ問題の影響を
受けず、FY2024・FY2025相当の期間も含め既に完全な非NULL値を持っている。
実測した`fcf_5yr_avg=-40,185,008.5`・`fcf_2yr_avg=-50,540,837.0`は
`latest.json`の実績値と完全一致し、この経路が実際に使われていることを
確認済み。

したがって、[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]の
RCAT分（パターンB）を年次パーサー側のみに実装しても、RCATの
`fcf_base_used`（$16,564,815.33）・DCF・tanuki_score・Classificationは
一切変化しない（ΔIV=$0と試算確認済み）。年次パーサー修正の実益は
「年次JSONのデータ品質改善」（他消費者・将来TTM系列欠損時のフォール
バック精度向上）に限定される。TTM系列生成ロジック側に同型の継続/
非継続タグ問題があるかは未調査であり、これは
[[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]として別途登録した。

#### 着手条件
[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
同時に、副次的効果として解消される（単独での緊急対応は不要）。

---

### [RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1] RCATの本番FCF計算が使うTTM系列の継続/非継続事業タグ扱いが未検証
**優先度:** 高（登録時）→中（根本原因確定の結果、現時点のIV実害はゼロと判明）
**分類:** 調査要 / 確認済み実害箇所の可能性
**登録日:** 2026-08-02
**確定日:** 2026-08-02（根本原因調査結果を反映）
**発見:** [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]実装前シミュレーション
（チャット記録）

#### 内容
RCATの本番FCF計算はTTM系列（`RCAT_ttm_series.json`、四半期10-Qの4四半期
ロール集計）経由であることが確認された。年次10-Kで発生している継続/
非継続事業の分割タグ問題（[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-
GAP-1]]）が、TTM系列生成ロジック（四半期タグ選択）側にも同型で存在する
かは未調査。現時点でTTM系列の該当四半期は「値の有無」のみ確認済み
（非NULL）で、その値自体が継続事業のみを反映しているのか、継続+非継続の
正しい合算値なのかは未検証。

#### 影響
RCATの実際のIV・DCF・Classificationに直結する可能性がある（年次パーサー
側とは異なり、こちらは本番計算で実際に使用されている経路のため）。もし
TTM系列側の値が継続事業のみ（非継続事業分を含まない過小計上）であれば、
現在のfcf_5yr_avg（-40,185,008.5）・fcf_2yr_avg（-50,540,837.0）自体が
誤りであり、[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]で懸念していたのとは別の
形で実害が現在進行形で存在する可能性がある。

#### 対応方針
未定。まずTTM系列生成ロジック（四半期タグ選択、`common/sec_data/ttm_
calculator.py`等）が、RCATの継続/非継続事業分割四半期タグをどう扱って
いるかを調査し、正しく合算できているか、それとも継続事業のみを拾って
いるかを確認する。

#### 根本原因確定結果（2026-08-02、チャット記録）
当初の懸念（継続/非継続タグの取り扱いミス）ではなく、より一般的な設計
欠陥が根本原因と判明した。`build_ticker_store('RCAT')`を実際に呼び出し
検証:

- `config/sec_concept_definitions.json`の`operating_cash_flow`候補タグは
  標準タグ（`NetCashProvidedByUsedInOperatingActivities`）1つのみで、
  年次パーサーと同型の候補タグ設計欠陥がLayer3（四半期・TTM経路）にも
  存在する。
- `ttm_calculator.py::calc_ttm_series()`が「アンカー日以前の直近4件を
  採用」するロジック（`quarters_used=4`は件数のみをチェックし、実際に
  日付が連続した12ヶ月分かは検証しない）を持つ、より根本的な設計欠陥を
  発見した。
- RCATでは、標準タグが継続/非継続分割開示と決算期変更（4月末→12月末、
  8ヶ月スタブ期間）が重なった約11ヶ月間で完全な空白となり、この結果
  2023年7〜10月・10月〜2024年1月の2四半期が、`ttm_end=2025-03-31`・
  `2026-03-31`の両方のTTM算出に重複使用されるという実害を実機で確認・
  再現した。
- 定量化: 現在の`fcf_5yr_avg`（-40,185,008.5）・`fcf_2yr_avg`
  （-50,540,837.0）は、正しい合算値の試算（約-53,985,212・
  約-78,141,244）より34〜55%過小評価（悪化方向を過小に表示）されている、
  現在進行形のデータ品質問題。
- IVへの影響試算: 現時点はΔIV=$0（`fcf_5yr_avg`・`adj_net_income`が
  両方赤字のため、revenue floor（$3,258,320固定）＋EPSベース推定
  オーバーライドが吸収し、`fcf_base_used`=$16,564,815.33は修正前後で
  完全に同一）。ただし将来RCATの業績が改善し`adj_net_income`が黒字転換
  する、または`fcf_5yr_avg`が正転すればこのバグが直接IVに影響しうる、
  という留保付き。
- 他銘柄への一般化: HON・TERは直近四半期まで完全に連続（ギャップなし）、
  AVAVは2022年の古い1件のみ（現在のTTMウィンドウ外）。現時点で同様の
  実害なしと確認。

根本原因（日付連続性チェックの欠如）自体はticker非依存の一般的設計欠陥
のため、[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]として切り出して
新規登録した。

#### 着手条件
なし。優先度中（現時点のIV実害はゼロだが、データ品質問題は現在進行形かつ
将来IVに影響しうる潜在リスクのため）。根本原因の恒久対応は
[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（日付連続性チェック追加）
側で行う。

---

### [XBRL-UNIT-SCALE-MISMATCH-DETECTION-1] 同一タグ・同一期間の値が複数filing間で10のべき乗単位で乖離する場合を検知する汎用チェックの新設提案
**優先度:** 中
**分類:** アーキテクチャ改善 / 新規検知チェック提案
**登録日:** 2026-08-02
**発見:** [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]調査から派生（chat記録）

#### 内容
同一XBRLタグ・同一unit・同一(start,end)期間について、異なるaccn
（filing）間で値の比率が10のべき乗値（1000倍・1,000,000倍等、±2%許容）
に近い場合、SEC提出時のスケール指定漏れ（"in thousands"欠落等）という
業界共通のXBRLタグ付けミスの可能性が高いことが判明した。素朴な閾値
（比≥100）のみでは72銘柄がヒットしノイズが大きすぎたが、比≒10の
べき乗という条件を追加することで、SPAC逆合併の会計主体入替
（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]と同系統、正当な処理）等のノイズを
排除し、18銘柄・126件まで収束することを確認した。

該当銘柄・件数: COHR(26)・KO(20)・NVDA(20)・CPRT(18)・TER(12)・ONDS(5)・
FCX(4)・HEI(4)・MO(4)・ADSK(2)・CELH(2)・TSLA(2)・ZS(2)・ASTS(1)・
IONQ(1)・MSCI(1)・SOUN(1)・ZETA(1)。対象フィールドはWeightedAverageNumber
OfSharesOutstandingBasic/Diluted(計98)が過半だが、CommonStockShares
Outstanding・EPS系・Depreciation系・NetIncomeLoss系・LongTermDebt・
DebtCurrent・Liabilities・OperatingIncomeLoss・AmortizationOfIntangible
Assets等、幅広いフィールドに及ぶ。

#### 影響
COHR以外の該当銘柄は未トリアージ。検知＝即実害ではなく、本人データ優先
ロジックにより既に正しい値が採用されているケース（実害なし、COHR自身の
FY2019/2020 Q3・FY2023/2024 D&A等で確認済み）もあれば、実際に格納値が
誤っているケース（COHR 2009-2011のshares系）もある、個別トリアージが
必要な問題。

#### 対応方針（登録時点）
未定。既存WARN群（WARN-24等）と同型の「検知のみ・自動修正なし」枠組みで
新設（WARN-30候補）することを推奨する。ただし既存WARN群がextracted
（抽出済み）データを対象にするのに対し、本チェックはcompany_facts.json
の生タグレベル（抽出前）を横断的に見る必要があり、`_parse_raw_data()`
または`report_consistency_check.py`への新規ロジック層追加という設計に
なる。検知後は126件を個別トリアージし、実害あり/なしを分類する運用が
必要。

#### 実装方針追記（2026-08-02、[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]
全母集団シミュレーション結果を統合、チャット記録・読み取り・オフライン
シミュレーションのみ）
[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]として個別登録していた
「`_extract_single_key()`のtie-break条件を新しいfiling優先に変更する」
という対応方針を、本エントリに統合する（詳細は同エントリのBACKLOG_DONE.md
移動後の記録を参照）。

全母集団シミュレーションの結果、tie-break条件を単純に「新しいfiling優先」
へ変更する広範な設計変更は不採用と確定した。31銘柄・124件で値が変化し、
確実な改善はCOHRの2件（shares_diluted/basic）のみで、残り122件は改悪
（VZ(2008)純利益が黒字$6,428M→赤字-$2,193Mに反転等）・改悪疑い
（SOUN/KULRのSPAC実体混同、HON/FCX/HEIのrestatement・株式分割調整）・
判断不能な乖離が大半だった。また、WMT(2014)でtotal_assetsが微小変動した
結果、`_backfill_total_liabilities_via_identity()`の安全網（TL==TAの
場合のみ発動）が完全一致条件を偶然すり抜け、[[TOTAL-LIABILITIES-
FALLBACK-TAG-DESIGN-FLAW-1]]と同型のバグを別経路で復活させかねない
という重大な相互作用リスクも判明した。

**実装方式を確定**: 「同符号 かつ 比が10のべき乗値（±2%許容、n≥2）」
という本エントリのガード条件に該当する場合のみ、tie-breakをより新しい
filing優先に切り替える設計とする。この条件で124件をフィルタしたところ、
COHRの2件（shares_diluted/basic）のみが該当し、他122件は自動的に
除外されることを確認済み。

実装前に2点の追加確認が必須:
(a) 既存の恒等式ベース安全網（`_backfill_total_liabilities_via_
    identity()`等）との相互作用を個別に再検証する（WMT(2014)のような
    偶発的なすり抜けがないか）
(b) ガード適用後も105銘柄で改めて全母集団シミュレーションを行い、
    新規の意図しない変化がゼロであることを確認する

対象は当面COHRの2件（shares_diluted/basic、2009-2011年度）に限定される
見込み。`fact_overrides.json`での個別対応（[[COHR-SHARES-DILUTED-
UNIT-SCALE-BUG-1]]で確定済み）と、tie-break側の恒久対応のどちらを
採るか、または両方必要かは実装時に判断する。

#### 実装前最終確認結果・実装方針確定（2026-08-02、チャット記録、読み取り・
オフラインシミュレーションのみ）
実装前の2点の追加確認（前項）を完了した。

(a) 既存の恒等式ベース安全網との相互作用リスクはなし。
`_backfill_total_liabilities_via_identity()`・[[CHECK29-ACCOUNTING-
IDENTITY-DETECTION-LAYER-1]]はいずれもBS項目（total_assets/total_
liabilities/stockholders_equity/NCI/一時的持分）のみを対象とする一方、
ガード条件付き介入が実際に触れるのはshares項目の2フィールドのみで、
両者が扱うフィールド集合に重なりがなく構造的に相互作用の経路が存在し
ないことを確認した。前回懸念したWMT(2014)型のすり抜けは、ガード条件
（比が10のべき乗、最低100倍）により正しく除外されることを確認した
（WMTの乖離比≒1.001はガード条件を満たさないため対象外）。

(b) ガード適用後の全母集団シミュレーションで、該当・変化するのはCOHRの
2010年度shares_diluted/basicの2フィールドのみと最終確定した。他104
銘柄・COHRの他年度（2009・2011年度含む）は完全に無変化、新規の意図
しない波及も確認されなかった。

**実装方針を確定**: [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]の
`fact_overrides.json`個別上書き（2009-2011年度、3年度とも1回で解決）を
実装対象とし、tie-break変更（ソースコード変更）は当面見送る。理由:
(a)tie-break変更は2010年度1件しか解決せず、その1件もfact_overrides側
で重複解決される（tie-break変更単独では2009・2011年度は解決しない:
2009年度は後続filingに正しい値自体が存在せず、2011年度は本人データ
優先ロジックにより保護されているため）、(b)現時点でCOHR以外に該当する
実ケースがゼロと確定しており、ソースコード変更のコストに見合う実利用
価値が現状ない。ガード条件の設計自体は妥当性・安全性が確認済みのため
破棄せず、将来「本人データ優先ロジックでは救えず、かつ個別override
登録が非現実的な規模の」新規ケースが発見された時点で再検討する。

#### 着手条件
[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]のfact_overrides実装で事実上
完結、tie-break変更部分は将来の予防的対応として保留。優先度中（業界
共通のミスパターンとして汎用的価値が高いが、即座の実害は限定的
〈COHR以外は未確認〉のため）。

---

### [TTM-DATA-DRIFT-BEHIND-PIPELINE-1] common/sec_data/ttm/配下のTTM系列ファイルが2026-07-26生成のまま、以降のパイプライン修正に追従しておらず陳腐化している可能性
**優先度:** 中（登録時「高」から引き下げ、影響実測の結果、現在進行形の
実害はゼロと確定したため。構造的リスクは残存）
**分類:** データ品質 / パイプライン出力の陳腐化
**登録日:** 2026-08-02
**発見:** [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]実装検証時（チャット記録）

#### 内容
`common/sec_data/ttm/`配下の全105銘柄のTTM系列ファイル
（`{ticker}_ttm_series.json`）が、`git log`確認で2026-07-26生成のまま
であることが判明した。一方、TTM系列の入力元となる抽出パイプライン
（`common/sec_data/layer3_builder.py`・`common/sec_data/q4_implied.py`）
は2026-07-30に、`common/sec_data/parser.py`は本セッション中の
2026-08-02に、それぞれ別コミットで修正されている。実際にPEP銘柄で
検証したところ、現行パイプライン（2026-08-02時点）で再生成すると
`selling_general_and_administrative`が$34,501,000,000→$37,791,000,000
（約9.5%）変化することを確認済み（`[[TTM-CALC-QUARTER-CONTIGUITY-
UNCHECKED-1]]`実装作業の副産物として発見。この差分は今回実装した連続性
チェックとは無関係で、単純にttm/ファイルが2026-07-26時点のパイプライン
出力のまま更新されていないことに起因すると特定済み）。

`.github/workflows/SEC_Data_Update.yml`を確認したところ、毎週日曜
12:00 UTC（cron: `0 12 * * 0`）に`update.py`を実行し
`common/sec_data/ttm/`を含む全出力を自動再生成・commit・pushする
ワークフローが既に存在する。**このワークフローが正常に稼働していれば
陳腐化は本来自然解消されるはずであり、なぜ2026-07-26以降ttm/が
更新されていないのか（ワークフロー自体の失敗・無効化・直近未実行等）
が未確認の論点として残る。**

#### 影響
未確定。PEP1銘柄のSG&Aで約9.5%の差分を確認したのみで、105銘柄全体で
どのフィールド・どの銘柄にどの程度の乖離があるかは未調査。TTM系列は
TANUKI VALUATIONのFCFベースDCF計算・STONKS SILOのrunway計算に直結する
ため、陳腐化の程度次第では現在進行形のIV算出精度への実害がありうる。
`[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]`実装時は対象18銘柄のみを
最新化し、残り87銘柄は意図的に未対応のまま据え置いている。

#### 対応方針（登録時点）
未定。実装は行わず、まず以下の調査が必要:
- `.github/workflows/SEC_Data_Update.yml`のGitHub Actions実行履歴を
  確認し、2026-07-26以降に正常実行されているか・失敗しているか・
  無効化されていないかを特定する
- 陳腐化の実際の範囲（全105銘柄中何銘柄・どのフィールドで実質的な差分が
  生じるか）を、現行パイプラインでの全銘柄再生成とフローズン入力比較で
  定量化する
- 通常の週次自動更新サイクルで自然解消される見込みか（ワークフローが
  正常なら次回日曜実行で解消するはず）を確認する
- 上記調査の結果次第で、手動での全105銘柄再生成が必要か、ワークフロー
  側の修正が必要かを判断する

#### 根本原因調査結果（2026-08-02、チャット記録、読み取りのみ・重大な
構造的発見）
GitHub Actions APIで`SEC Data Update`ワークフローの実行履歴を確認した
結果、**ワークフロー自体は正常稼働中**と判明した（毎週日曜、直近9回超
すべて`schedule`トリガーで`success`、無効化もされていない。`git log`上の
`ttm/`最終更新コミット`340b8b8ae`〈author=`github-actions[bot]`〉が
2026-07-26の実行と完全に一致）。調査時点（2026-08-02 12:32〜12:36 UTC、
本日も日曜）では本日分の実行が未発火だったが、前週の実行もcron時刻
（12:00 UTC）から49分遅れて開始しており、GitHub自身が公式に案内する
「12:00〜15:00 UTC帯はscheduleトリガーの遅延が起きやすい」時間帯と
一致するため、**単なる未発火（これから発火する見込み）であり失敗では
ない可能性が高い**。default_branch=`kaihatsu`とワークフローの
checkout先も一致しており、本セッションのコード変更後も
`common.sec_data.update`のimportエラーなし・ゲート
（`report_consistency_check.py`）もNG=0を確認済みで、本セッションの
変更との衝突の兆候はない。

**真の問題（当初想定より深刻）**: `common/sec_data/ttm/`を生成する
`layer3_builder.py`（＋`quarterly.py`・`fact_selection.py`・
`q4_implied.py`）は、`parser.py`（annual_YYYY.json生成）とは**完全に
独立した別実装のパイプライン**であることを確認した。`layer3_builder.py`
は`parser.py`のクラス・関数を一切importせず、`fact_overrides.json`も
読み込まない。`parser.py`側の`_resolve_bs_entity_mixing()`・
`_backfill_total_liabilities_via_identity()`・
`_align_cost_of_revenue_to_revenue_period()`に相当する処理も存在しない。

結果、本セッションで実装した以下の修正は、**ワークフローが正常実行
されてもTTM系列には反映されない**（唯一の例外は
[[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]。これは`ttm_calculator.py`
自体への実装のため次回実行で全105銘柄に自動反映される）:
- [[PERIOD-LENGTH-VALIDATION-GAP-1]]（28銘柄）
- [[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1・2（7銘柄+SPIR）
- [[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]（22銘柄278件、
  AMZN/GOOGL/MSFT/NVDA/AMD/WMT等の大型株含む）
- [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]案b（LRCX）
- [[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]（GOOGL、`fact_overrides.json`
  自体が未読込のため）
- [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]（COHR、同上）
- [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]（ELF）

なお`layer3_builder.py`側は`gross_profit`逆算のみ独自に別実装済みで
（既存の別系統バグ追跡ID`[[LAYER3-GROSSPROFIT-BACKFILL-MISSING-1]]`、
annual側の`[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]`とは別系統
であることを確認済み）、全ての annual側修正が未移植というわけではない。

**結論**: 「ワークフローを動かせば陳腐化が解消する」という単純な話では
なく、今回実装した連続性チェック以外のannual側の修正は、たとえ
ワークフローが毎週正常に動いても恒久的にTTM側へは反映されない
（別途`layer3_builder.py`側への個別移植が必要）という、より根深い
構造的問題であることが判明した。

**対応方針の選択肢**:
1. 現状維持（cron待ち）: [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]の
   みが次回実行で全105銘柄に自動反映される。他は反映されないまま。
2. 手動トリガー（`workflow_dispatch`）: pushを伴うため明示的承認が必要。
3. `layer3_builder.py`側への個別移植: 範囲が大きく複数タスクへの分割が
   必要。
4. 影響の実測確認を先行: TANUKI VALUATION・STONKS SILOがTTM経由で
   未移植の修正対象フィールド・銘柄をどの程度消費しているか確認し、
   実害の大きさに応じて3の優先度を判断する。

#### 対応方針（前回時点）
④（影響の実測確認を先行）から着手する。範囲の大きい③（個別移植）に
いきなり着手する前に、実装前に実害を確認するという原則に基づき、実際に
どれだけの影響があるかをまず確認する。

#### 影響実測結果（2026-08-02、チャット記録、読み取りのみ）
7件の既知修正について、TANUKI VALUATION・STONKS SILOいずれも**現在
進行形の実害は確認されなかった**。

- [[SPAC-SHELL-BS-ENTITY-MIXING-1]]・[[TOTAL-LIABILITIES-FALLBACK-
  TAG-DESIGN-FLAW-1]]（AMZN/GOOGL/MSFT/NVDA/AMD/WMT等22銘柄278件）・
  [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]: 対象フィールド（BS項目・
  shares系）が構造的にTTM出力（`FLOW_FIELDS`17種のみ）に一切含まれない
  カテゴリであり、消費経路（`get_net_cash()`・`get_diluted_shares()`）も
  `annual_*.json`を直接参照するため無関係と確定。
- [[PERIOD-LENGTH-VALIDATION-GAP-1]]（28銘柄）・[[PL-FIELD-CROSS-ACCN-
  PERIOD-MISMATCH-1]]（LRCX）・[[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]・
  [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]: 対象年度が現在のTTM系列
  anchor範囲（実測で2021〜2022年始まり）の外にあるため無関係。唯一の
  例外RCAT(2024年度)のstock_based_compensationも、FCF計算式
  （`_calc_fcf()`）に直接使われず、現状RCATのRICEスコア自体が「年次
  データ不足で計算不可」のため現時点で出力に無影響。
- STONKS SILOは独立した第3のパイプライン（`load_annual_data()`経由で
  `annual_*.json`を直接読み込み）であり、コード全体を検索してもTTM/
  layer3経由の参照が一切存在せず、実害はゼロと確定。

**重要な留保**: これは「今回はたまたま対象年度がTTM窓の外だった」結果
であり、2つの独立パイプラインが同期しない設計上の脆弱性自体は温存されて
いる。将来のannual側修正が、対象年度が現在のTTM窓内である場合には同様の
未反映リスクが顕在化しうる。

#### 対応方針
現在進行形の実害がゼロと確定したため、優先度を「高」から「中」に
引き下げる。ただし構造的脆弱性は残存するため、以下のいずれかの対応を
将来検討する:
- 短期的な運用対応: annual側で新規修正を行う際は、対象年度がTTM系列の
  anchor範囲内かどうかを都度確認し、範囲内の場合はlayer3_builder.py側
  への個別移植も検討するというチェック項目を、今後の実装依頼テンプレート
  に追加する
- 長期的な構造対応: layer3_builder.pyとparser.pyの重複ロジック
  （gross_profit逆算等）を統合する、またはannual側の修正結果をTTM側が
  参照する設計に変更する等、パイプライン統合自体の検討（大規模な設計
  変更のため別途独立検討が必要）

#### 長期的構造対応の検討結果（2026-08-03、チャット記録、読み取りのみ）
上記「長期的な構造対応」（パイプライン統合）の実現可能性を設計調査した。

**認識の訂正**: 当初「parser.py⇔layer3_builder.pyの2パイプライン問題」
としていたが、実際は`update.py`内で3つの独立生成パスが並存する構造
であり（①`parser.py`→`annual_*.json`、②`quarterly.py`→`normalizer.py`
→`normalized/*.json`、③`layer3_builder.py`→`ttm_calculator.py`→
`ttm/*.json`）、`SEC_EDGAR_LAYER_DESIGN.md`が既に「3スキーマ併存」として
認識済みの既知課題の一部だったと判明した。

**重複ロジックの棚卸し結果**: parser.py側の安全ロジック（本人データ優先・
BS系バックフィル・cost_of_revenue期間整合）の大半はTTM出力対象フィールド
（FLOW_FIELDS 17種）に該当しないBS/shares系であり、構造的に「移植する
意味自体がない」。真に問題になりうるスコープは「FLOW型フィールドに
関わる本人データ優先判定」のみという、当初想定より狭い範囲であることが
判明した。

**経緯の確認**: `layer3_builder.py`初出は2026-07-24（既存コード非改変
方針で新規構築）、parser.py側の安全ロジック追加は2026-08-01（本
セッション）。設計時点で後からparser.py側にこれらのロジックが追加
されることは想定されておらず、意図的な除外ではなく単純な時間差による
取り残されと確定した。

**選択肢の再評価**:
- 案A（完全統合）: layer3_builder.pyがparser.pyの共通ロジックを
  import・再利用する設計。新DB構築フェーズ相当の規模
- 案B（部分統合）: FLOW_FIELDS関連の本人データ優先ロジックのみ
  `fact_selection.py`へ追加。個別バグ修正1〜2件相当の規模
- 案C（運用チェック継続）: CHAT_RULES.md追記済みの現状（parser.py修正
  依頼作成時のTTM同期確認チェック）を維持

**推奨・対応方針**: 現時点は案C（運用チェック継続）を維持し、統合作業
（案A/B）には着手しない。根拠:
(a) 実害が実測でゼロと確定済み
(b) 真に問題になるスコープは当初想定より狭い（FLOW型フィールドの
    本人データ優先判定のみ）
(c) 3スキーマ併存自体は新DB構築プロジェクトのフェーズD（consumer切替）
    以降で本格的に扱われる射程の既存の中長期課題であり、前倒しの
    必然性が薄い
(d) gross_profit逆算のように既に個別重複が許容されている先例
    （[[LAYER3-GROSSPROFIT-BACKFILL-MISSING-1]]系）がある

#### 着手条件
以下いずれかのトリガー条件が発生するまで保留:
1. 今後の運用チェックでTTM anchor範囲内×FLOW型フィールドの修正が発生し
   実害が確認された場合 → 案B（部分統合）を個別タスクとして起票
2. 新DB構築プロジェクトのフェーズDに進む際、3スキーマ併存全体の解消を
   検討するタイミングで本件も合わせて設計する

---

### [CHECK29-UNRESOLVED-23-MIXED-CAUSES-1] 拡張恒等式検証（許可リスト＋OR条件方式）を適用しても解消しない23件が複数原因混在で残存
**優先度:** 中
**分類:** データ品質 / 複数原因混在・個別対応要
**登録日:** 2026-08-02
**発見:** [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]実装前
シミュレーション（チャット記録）

#### 内容
拡張恒等式検証（許可リスト＋OR条件フォールバック方式）を適用しても解消
しない23件が判明した。原因は複数混在:
- COHR(2022/2023): 該当タグが自社当該年度10-Kに存在せず後年の比較列
  としてのみ開示（クロスaccn問題、本人データ限定照合では発見不可）
- HEI(2009-2013): TemporaryEquityRedemptionValue（償還価額、簿価とは
  別基準）のみ存在。許可リストから意図的に除外したため未解消
- PLTR(2019)・CART(2023-2025)・CRWV(2024)・BKNG(2011/2012)・V(2008)・
  CRM(2011): 該当accn・end_dateにNoncontrolling/TemporaryEquity系タグが
  一切存在せず、標準タグ体系と異なる命名の優先株式等の可能性
- CELH(2025): 大型買収（Alani Nu）関連の会計処理の可能性
- ASTS(2019/2020)・VRT(2017/2018)・RDW(2020): RedemptionValue系タグの
  みが存在、許可リストの基準（簿価のみ）から除外したため未解消
- ONDS(2023): 優先株式・普通株式2区分のタグが両方存在し、追加検出で
  むしろ過大計上（-13.7%）に転じた二重計上の疑い

#### 影響
未確定。156件中の残り23件（14.7%）。COHR・ONDS等一部は追加調査で
①genuineと確定できる可能性が高いが、標準タグ体系外の命名を持つ銘柄
（PLTR/CART/CRWV等）は個別の10-K確認が必要。

#### COHR・HEI・ONDS個別調査結果（2026-08-02、チャット記録）
件数の多い3件を優先調査し、いずれも①genuineと確定した（②タグ選定バグ
〈抽出パイプライン側の不具合〉に分類されるものはなし）。

- **COHR(2022/2023)**: 自社own accnの10-Kには`TemporaryEquityCarrying
  AmountAttributableToParent`が一切存在しないが、後続四半期filing
  （2022年分は次四半期10-Q、2023年分はFY2024 Q2 10-Q）の比較列としては
  同一値が一貫して報告されており、その値を用いるとTA=TL+SE+extraが
  完全一致することを確認済み（2022年: $766,803,000、2023年:
  $2,241,415,000）。COHR/II-VI合併がFY2022期末の翌日（2022-07-01）に
  完了しており、合併対価の優先株式が合併後最初の四半期報告書で遡及的に
  付与されたものと推定される。**CHECK29の「本人データ（own accn）限定」
  照合という設計方針そのものが原因で検知不可能な構造的限界**であり、
  単純な許可リスト拡張では解決しない。[[CHECK29-COHR-CROSS-ACCN-
  TEMPORARY-EQUITY-1]]として別スコープで新規登録した。
- **HEI(2009-2013)**: 該当5年度いずれも`TemporaryEquityRedemptionValue`
  （償還価額）以外に簿価（CarryingAmount）タグが一切存在せず、この
  タグを用いるとTA=TL+SE+MinorityInterest+RedemptionValueが完全一致
  することを確認済み（例: 2013年度 $750,562,000+$606,346,000+
  $116,889,000+$59,218,000=$1,533,015,000=TA）。2009-2013年当時のHEIは
  RedemptionValueをそのまま貸借対照表上の簿価として計上していたと
  推定される（2014年以降は`...Including...NoncontrollingInterests`
  タグに移行）。**許可リストに`TemporaryEquityRedemptionValue`を、
  CarryingAmount系タグが1つも存在しない場合のみのフォールバックとして
  追加すれば対応可能**（無条件追加は他銘柄での二重計上リスクがあるため
  不可）。
- **ONDS(2023)**: `RedeemableNoncontrollingInterestEquityCarrying
  Amount`($11,920,694、合算値）と`...PreferredCarryingAmount`
  ($14,692,000、内訳の一部）が両方存在し、元の乖離額が前者単体と完全
  一致することから、後者は前者に既に含まれる内訳であり両方合算すると
  優先株式分が二重計上されると確定。**原因はCHECK29自体の実装不備
  （自己申告）**: `TemporaryEquityCarryingAmountIncludingPortionAttribu
  tableToNoncontrollingInterests`と同型のSUPERSEDESルール（合算値タグが
  存在する場合に内訳タグを除外する）を`RedeemableNoncontrollingInterest
  Equity...`系にも追加すれば解決可能。

残る20件（PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW）は未着手のまま。

#### HEI・ONDS実装完了（2026-08-02、チャット記録）
HEI型・ONDS型（計6件）の許可リスト拡張を実装した。

- **HEI型**: `TemporaryEquityRedemptionValue`を許可リストに追加。無条件
  加算ではなく、簿価（CarryingAmount）系タグが同一accn・同一end_dateに
  1つも存在しない場合のみのフォールバックとして限定（他社での二重計上
  を防止）。
- **ONDS型**: `RedeemableNoncontrollingInterestEquityCarryingAmount`
  （合算値）が存在する場合に`...CommonCarryingAmount`・
  `...PreferredCarryingAmount`（内訳）を除外するSUPERSEDESルールを、
  既存の`TemporaryEquityCarryingAmount...`系ルールと同型で追加。

全105銘柄でオフライン再パースを実行し、HEI(2009-2013、5件)・
ONDS(2023、1件)が`resolved_by_extension=true`に変わることを確認
（156件中133件→**139件が解消**）。副次的にFCX(2013)の拡張形一致が
より厳密に改善（残差$716,000,000→$0、resolved自体は変化なし）。他99
銘柄・既存133件のresolved=trueは維持、COHR型2件・残り15件のresolved=
falseも維持を確認。annual_YYYY.json等の既存データ値は無変更。
pytest 497 passed/2 known failed（既知・無関係）。report_consistency_
check.py実行: WARN 83→81件（-2、HEI・ONDSのWARN-29が解消）。

機能コミット: `a910afef2`。

#### 対応方針
CHECK29本体（133件解消分）は実装完了済み
（[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]、BACKLOG_DONE.md
参照）。HEI・ONDS（6件）は許可リスト拡張を実装完了。
- COHR/CRWV/VRT(2018)分（4件）: [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-
  EQUITY-1]]でcross-accnフォールバック（2段階ガード）を実装し解消済み
  （2026-08-03、BACKLOG_DONE.md参照）。
- 残る13件（PLTR/CART/BKNG/V/CRM/CELH/ASTS/VRT(2017)/RDW）は
  `resolved_by_extension=false`として検知ログ
  （`{ticker}/bs_identity_violations_log.json`）・WARN-29に記録済みの
  まま、個別調査で②genuine確定→config/warn_acknowledged.json登録、
  または③真のバグとして別途対応、のいずれかに順次分類していく。

#### 残り13件個別調査結果（2026-08-03、チャット記録・読み取りのみ）
残り13件を個別に調査し、①genuine・②許可リスト拡張可能・③要さらなる
確認の3分類に整理した。

**①genuine（対応不要、2件）**:
- **BKNG(2011/2012)**: `RedeemableNoncontrollingInterestEquityCommon
  FairValue`（own accn）のみが存在し、CarryingAmount基準のタグは
  一切ない。加算しても乖離は解消しない（2012年: 必要額$214,942,000 vs
  タグ値$160,287,000）。既存の許可リスト設計方針（簿価タグのみ限定、
  LYFT型過大計上の教訓）と整合的に、FairValue基準の値は加算対象外と
  すべきであり対応不要と確定。

**②許可リスト拡張で対応可能（2件）**:
- **ASTS(2020)**: own accnに`TemporaryEquityValueExcludingAdditional
  PaidInCapital: $150,596,928`が存在し、加算すると完全一致
  （diff=$0）。現行の許可リスト（7タグ）に含まれていないタグ。
  cross-accn問題ではなくown-accnのみで解決する。
- **RDW(2020)**: own accnに`RedeemableNoncontrollingInterestEquity
  CommonRedemptionValue: $120,314,578`が存在し、加算すると完全一致
  （diff=$0）。HEI型フォールバック（`TemporaryEquityRedemptionValue`
  のみ対象）と同型だが別タグ名のため現行フォールバックの対象外に
  なっている。

**③要さらなる確認（7件）**:
- **PLTR(2019)**: 全namespace横断でもNCI/TemporaryEquity系タグは
  一切存在しない。stockholders_equity（$-1,980,642,000）は自身の
  内訳（CommonStock+APIC+RetainedEarnings+AOCI−TreasuryStock）と
  完全一致し抽出バグではない。乖離$2,127,231,000の原因は上場前の
  複雑な資本構成に起因する可能性が高いが特定できず。
- **CART(2023/2024/2025)**: 3年度ともNCI/一時的持分/優先株式系タグは
  一切存在せず、stockholders_equity・liabilitiesとも各々の内訳合計と
  一致（抽出は正しい）。乖離（$177M〜$195M）の原因が特定できず、
  NCI/一時的持分以外の可能性が高い。
- **V(2008)**: `SharesSubjectToMandatoryRedemptionSettlementTerms
  AmountCurrent: $1,508,000,000`（own accn）を発見したが、加算すると
  $372,000,000超過し一致しない（既にLiabilities側に含まれている
  可能性）。Visa 2008年IPO特有のクラスB/C制限株式・訴訟エスクロー
  構造に起因する可能性が高いが確証は得られず。
- **CELH(2025)**: NCI/一時的持分/優先株式系タグは一切存在せず、
  stockholders_equityは内訳と一致（抽出は正しい）。乖離
  $1,759,975,000は大型買収（Alani Nu）関連の負債側項目に起因する
  可能性が高いが特定できず。
- **ASTS(2019)**: own accnには一時的持分タグが一切存在しない
  （2021年SPAC規制ガイダンスによる遡及的restatement以前の初回10-Kの
  ため）。後続の2020年10-K/A比較列に近い値（$202,557,751）はあるが
  必要額（$218,519,748）と一致せず（残差$15,961,997）。restatement
  時にtotal_assets/total_liabilities自体も変更されている可能性があり
  単純加算では解消しない。

**CHECK29対象外の独立バグ発見（2件、別エントリへ分離）**:
- **CRM(2011)・VRT(2017)**: 調査の過程で、この2件は「NCI/一時的持分
  タグ不足」ではなく、`stockholders_equity`の抽出自体が別年度・別
  filingの無関係な値を誤って採用している独立したバグと判明した。
  [[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]として別途
  新規登録した。

#### 着手条件
なし（充足済み）。実測で対象は当初23件から**13件**に減少（HEI×5・
ONDS×1・COHR×2・CRWV×1・VRT×1〈2018分〉の計10件が解消）。残る13件は
上記個別調査により①genuine2件（BKNG×2）・②許可リスト拡張可能2件
（ASTS2020・RDW2020）・③要さらなる確認7件（PLTR・CART×3・V・CELH・
ASTS2019）に整理。CRM・VRTの2件は[[PARSER-STOCKHOLDERS-EQUITY-
CROSS-YEAR-MISSELECT-1]]へ分離（CHECK29対象外）。WARN-29発火銘柄も
13→9銘柄に減少（ASTS/BKNG/CART/CELH/CRM/PLTR/RDW/V/VRT）。

**追記（2026-08-05、[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]] Stage 3
準備調査）**: RDW(2020)について、②許可リスト拡張（`RedeemableNoncontrolling
InterestEquityCommonRedemptionValue`の追加）が**まだ実装されていない**
ことを実データで確認した。annual_2020.jsonを実測したところ現在も
TA=$167,724,005・TL+SE=$47,409,427で**diff=$120,314,578が解消していない**
（parser.pyの`_BS_IDENTITY_ALLOWLIST`に当該タグが未登録のまま）。
ASTS(2020)側の実装状況は本追記では未確認（別途要確認）。RDW(2020)は
fixed_registry.json Stage 3の登録候補から除外済み
（BACKLOG_DONE.md「2026-08-05（完了）」Stage 2エントリ参照）。

**実装完了（2026-08-05、RDW(2020) BS恒等式残差解消）**: `_BS_IDENTITY_
FALLBACK_ONLY_TAG`（単数）を`_BS_IDENTITY_FALLBACK_ONLY_TAGS`（複数、
`TemporaryEquityRedemptionValue`・`RedeemableNoncontrollingInterest
EquityCommonRedemptionValue`の2タグ）へ拡張し、RDW(2020)を解消した。
`_BS_IDENTITY_ALLOWLIST`への無条件追加ではなくフォールバック機構への
追加を採用（RedemptionValueは簿価と異なる測定基準のため、HEI型と同じ
安全側設計を踏襲。全105銘柄・全既知違反年度での机上シミュレーションで
両案の結果が同一〈RDW(2020)のみ解消〉であることを確認した上での判断）。
全105銘柄フローズン再パースでRDW(2020)以外に差分なし、
`report_consistency_check.py`でRDW単体WARN=0・全体NG=0を確認、pytest
497 passed/2 known failed（既知）を確認。詳細はBACKLOG_DONE.md該当
エントリ参照。

**実装完了（2026-08-05、ASTS(2020) BS恒等式残差解消）**: Step 0で
annual_2020.json実測により残差$150,596,928が前回報告時点から変化して
いないことを確認した上で着手。全105銘柄・全既知違反年度の机上
シミュレーションで、RDWと同じ「フォールバック機構への追加」案を試した
ところ、ASTSでは既存のMinorityInterestのcross-accn一致（$2,490,000）の
上に本タグが後乗せされ、diff=-$2,490,000という不正確な合算（許容誤差内
のため見かけ上resolvedになるだけ）が生じることが判明した。一方
`_BS_IDENTITY_ALLOWLIST`へ無条件追加する案は、own-accn一次パスのみで
$150,596,928が完全一致し、二次パス（MinorityInterestのcross-accn
探索）自体が発火しないため、diff=0の厳密な一致となることを確認した。
`TemporaryEquityValueExcludingAdditionalPaidInCapital`は「Value
Excluding APIC」という名称通り簿価（CarryingAmount系と同種の測定基準）
であり、RDW型のRedemptionValue（測定基準が異なる開示専用タグ）とは
性質が異なるため、**RDWとは異なりフォールバック機構ではなく主許可
リストへ無条件追加する設計を採用**（設計判断がタグの性質によって
異なりうることをEXTRACTION_DESIGN_PRINCIPLES.md原則2に沿って確認した
実例）。全105銘柄シミュレーションで他に影響したのはFRSH(2020)のみ
（既に解消済みの年度に`$0.0001`という名目値が追加で一致するのみ、
複数期間で同一の定型値と確認済み、解決判定・金額とも実質影響なし）。
全105銘柄フローズン再パースでASTS/FRSH以外に差分なし、
`report_consistency_check.py`でASTS(2020)分のWARN-29解消・全体NG=0を
確認（ASTS(2019)のWARN-29は別問題として存続、想定通り）、pytest
497 passed/2 known failed（既知）を確認。詳細はBACKLOG_DONE.md該当
エントリ参照。**`[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]`の「②許可
リスト拡張で対応可能」2件（RDW/ASTS）が両方解消**。

---

### [AVGO-2015-DATA-THIN-1] AVGO(2015)がCIK拡張対象年度範囲外にもかかわらずデータが薄い（bs=2項目・pl=0項目・is_own_data=False）
**優先度:** 中
**分類:** データ品質 / 要調査
**登録日:** 2026-08-05
**発見:** [[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]] Stage 3準備調査（チャット記録）

#### 内容
[[CIK-DISCONTINUITY-OLDEST-YEAR-GAP-1]]の旧CIK拡張対象年度範囲
（AVGO 2006-2014）の**外側**であるAVGO(2015)のannual_2015.jsonを
実測したところ、`bs`2項目・`pl`0項目のみと極端に薄く、
`is_own_data=False`だった。2009-2014年は完全充足
（bs=7〜9項目・pl=7〜9項目・is_own_data=True）だったのに対し、2015年
のみ突然薄くなっている。

DELL(2014-2016)で確認済みの「旧CIK・新CIKいずれの自社10-Kも存在しない
申告ギャップ」と同種のパターンの疑いがあるが、AVGO側では未確認。AVGOは
2016年にBroadcom LimitedによるBroadcom Corporation買収が完了しており、
その前後の法人再編・CIK切替の境界が2015年に関わっている可能性がある。

#### 影響
未確認。fixed_registry.json Stage 3での登録要否判断に影響する
（AVGO(2015)を凍結候補に含めるべきか、DELL型の構造的ギャップとして
扱うべきかが未確定なため）。

#### 対応方針
未定。原因調査（旧CIK→新CIK移行境界のSEC提出履歴を`submissions.json`
で確認、DELL(2014-2016)調査と同じ手法を適用）が必要。

#### 原因調査結果（2026-08-05完了、チャット記録・読み取りのみ）
SEC EDGAR一次情報（submissions API）で調査した結果、DELL型の「申告
ギャップ」ではなく、**より根本的な問題（`cik_history.json`のAVGO旧CIK
登録が無関係な買収先企業を指している疑い）**と判明した。詳細・分類
（(a)〜(e)）・実害確認・対応方針の選択肢は
`[[AVGO-CIK-HISTORY-WRONG-LEGACY-CIK-1]]`として分離登録した（本エントリ
は原因確定によりクローズ）。

**状態: 原因確定・`[[AVGO-CIK-HISTORY-WRONG-LEGACY-CIK-1]]`へ統合**

---

### [AVGO-CIK-HISTORY-WRONG-LEGACY-CIK-1] AVGOの旧CIK登録が無関係な買収先企業（Broadcom Corp）を指しており、真の前身企業（Avago Technologies LTD, CIK 1441634）と決算期が不一致
**優先度:** 中（2026-08-16、高→中へ訂正。理由は下記「優先度訂正の経緯」参照）
**分類:** バグ疑い / CIK統合設計の誤り
**登録日:** 2026-08-05
**発見:** [[AVGO-2015-DATA-THIN-1]]原因調査（チャット記録）

#### 内容
`cik_history.json`のAVGO `legacy_ciks=["1054374"]`は、SEC EDGAR一次
情報の決算期比較（現行CIK・真の前身候補CIK 1441634はいずれも10月末〜
11月初決算、登録済み旧CIK 1054374は12月31日決算）により、無関係な
買収先企業（Broadcom Corporation、2016年にAvago Technologies社に
買収されBroadcomへ社名変更）のデータである可能性が高いと判明した。
真の前身企業CIK 1441634「Avago Technologies LTD」は2016-02-08に
Form 15-12B提出で消滅しており、`cik_history.json`に未登録。

現状、2006-2014年の「AVGO」年次データは、Avago自身の実績ではなく
Broadcom Corpの実績を表している可能性がある。2015年の欠落はこの
誤りの副産物（真の前身CIKが未登録のためFY2015 10-Kが参照されない）。

#### 実害
現時点でゼロと確認済み（growth_sanity・roe_10yr_avgともに窓が届く
範囲外、fixed_registry.jsonはAVGO 2016/2017のみ登録済みで無関係）。
潜在リスクとして、将来ROE/CAGR窓が拡張された場合、または2006-2014年
実績が直接参照された場合に誤ったデータを見せるリスクが残る。

#### 対応方針の選択肢（未実装のまま並記）
案A: 旧CIKを1441634へ差し替え・2006-2014年データ再生成（コスト中、
決算期変更に伴う年度キー再検証が必要）
案B: 現状維持＋警告表示のみ（コスト低、誤データ残存）
案C: 2006-2014年データを削除・DELL型の「接続しない」構造的境界扱い
（コスト低〜中）

#### 着手条件
**充足済み（2026-08-13更新）**。着手条件だった「新DB構築フェーズ1
完了」は、`common/sec_data`統合（フェーズD、2026-08-06実質完了）・
`common/market_data/`・`common/macro_data/`（いずれも2026-08-13本線
タスク完了）を含め満たされた。対応方針〈案A: 旧CIK差し替え・案B:
現状維持＋警告表示・案C: 2006-2014年データ削除〉のいずれを採るかの
判断が必要な状態（実装は未着手のまま）。

#### 優先度訂正の経緯（2026-08-16）
案2 Step C（BACKLOG優先度中以上の棚卸し）で、本文の「#### 実害」欄に
「現時点でゼロと確認済み」と明記されているにもかかわらず優先度が
「高」のまま維持されている自己矛盾を発見した。潜在リスクは「将来
ROE/CAGR窓が拡張された場合」「2006-2014年実績が直接参照された場合」
という、いずれも未確定の仮定条件下でのみ顕在化するものであり、対応
方針も3案並記のまま未決定。実害ゼロが確認済みという記述自体は正しく
（データが誤っている可能性という事実認識は変えない）、優先度表記の
みを「中」へ訂正する。

---

### [SPAC-SHELL-MAINTAINED-FIELDS-FREEZE-CONSIDERATION-1] BBAI/RKLB/SOFI/VRT/ONDSグループの「維持フィールド」の凍結検討
**優先度:** 低
**分類:** データ品質 / 将来検討事項
**登録日:** 2026-08-05
**発見:** [[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]] Stage 3準備調査（チャット記録）

#### 内容
[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1でBS項目をNone化・修正した
BBAI(2020)・RDW(2020)・RKLB(2020)・SOFI(2020)・VRT(2019)・ONDS(2017)の
6件は、None化されたフィールド自体（current_assets/current_liabilities/
long_term_debt/short_term_debt等）に「凍結すべき正しい値」が存在しない
ため、現行のfixed_registry.jsonスキーマでは登録不可と確定済み
（Stage 3調査、BACKLOG_DONE.md「2026-08-05（完了）」Stage 2エントリ
参照）。

一方、各銘柄でNone化されず**維持**されたフィールド（例: BBAIの
total_assets/stockholders_equity/total_liabilities/cash_and_equivalents）
は、`_resolve_bs_entity_mixing()`の数学的整合性チェック
（current_assets<=total_assets等）を通過済みであり、「誤った値をNone化
した」修正の裏返しとして「正しいと確認済みの値」というカテゴリに
位置づけられる可能性がある。

#### 影響
未確定。仮に凍結対象とする場合、Stage 1/2とは異なる「除外的検証
（誤りが混入していないことの消去法的確認）」という性質を持つため、
Stage 1/2の「積極的な値の検証」基準にそのまま当てはめてよいか設計判断が
必要。

#### 対応方針
未定。次回以降、余力があれば検討する将来課題。

#### 着手条件
なし（Stage 2/3の主要スコープ外、優先度低のため急ぎ着手しない）。

---

### [PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1] stockholders_equityが正しいaccnと異なる別年度・別filingの無関係な値を誤って採用するケースが存在する
**優先度:** 高
**分類:** バグ / 確定・CHECK29対象外の独立した抽出バグ
**登録日:** 2026-08-03
**発見:** [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]個別調査から派生
（チャット記録）

#### 内容
CRM(2011)・VRT(2017)で、stockholders_equityの抽出が正しいaccn
（total_assets/total_liabilitiesと同一のfiling）ではなく、別年度・別
filingの無関係な値を誤って採用している:
- CRM(2011): 正しいaccn（FY2011 10-K）はStockholdersEquity単体タグを
  持たずStockholdersEquityIncludingPortionAttributableToNoncontrolling
  Interest（$1,587,360,000）のみタグ付けされているが、抽出ロジックが
  これを見つけられず1年前のFY2010の値（$1,276,491,000）にフォール
  バックしていた
- VRT(2017): 正しいaccn自体にStockholdersEquity: $23,724が存在するに
  もかかわらず、3年後のFY2020 10-K/A比較列（-$129,600,000、全く無関係
  な値）を誤って採用していた

いずれも、正しい値を採用すればCHECK29の恒等式検証も完全一致する
（CRM: 加算後diff=$0、VRT: diff=$0）ことを確認済み。

#### 影響
CHECK29のNCI/一時的持分許可リスト拡張では解決しない、独立した
stockholders_equity own-data選定ロジックのバグ。

#### 全105銘柄横断スキャン結果・根本原因（2026-08-03、チャット記録・
読み取りのみ）
全105銘柄・1249年度でtotal_assetsとstockholders_equityのaccn一致を
確認したところ、**不一致は13件（1.04%）のみ**だった。

- **真のバグ（値も誤り、2件）**: CRM(2011)・VRT(2017)（既知）
- **構造的に必然（1件）**: CWAN(2023) — 正しいaccnに
  StockholdersEquity系タグが一切存在せず、後続3つの異なるfiling
  （10-Q×2・10-K×1）で一貫して報告される値（$354,329,000）を採用。
  MinorityInterest($55,328,000)加算で恒等式が完全一致するため値自体は
  正しい可能性が高い（COHR/CRWV型のcross-accn必然パターンと同種で、
  CRM/VRT型の見落としバグとは性質が異なる）
- **無害（9件）**: ELF(2019)・LITE(2014)・QBTS(2021)・TSLA(2010)・
  BKNG(2009)・HON(2010)・V(2008)・DOCN(2020)・LYFT(2018) —
  provenanceのaccnフィールド（メタデータ）は真の同一accnと異なるが、
  格納されている値自体は真の同一accnのタグ値と完全一致することを
  個別確認済み（比較対象filingが過去の確定値をそのまま繰り返し開示
  しているため無害）
- **別種の異常（本バグとは無関係、2件）**: CAKE(2009)・LITE(2014) —
  total_liabilities自体が完全に欠損（None）。本調査のスコープ外

**根本原因（コードレベルで確認済み）**: `parser.py::_collect_own_data_
instant()`（L1190-1277）が各BSフィールドを完全に独立して抽出する設計
であり、既存の安全策`_resolve_bs_entity_mixing()`（L567-682）は
「本人データ（is_own_data=True）を提供するaccnが単一に定まる」ことを
前提とするため、以下2パターンではこの前提の外側にあり是正されない:
- **CRM型**: total_assets・stockholders_equityの両方が別々の年度に
  対してそれぞれ独立に`is_own_data=True`と判定される（アンカー候補が
  2つで一意に定まらない）
- **VRT型**: 両方とも`is_own_data=False`（アンカー候補が0個で一意に
  定まらない）

`EXTRACTION_DESIGN_PRINCIPLES.md`原則2（「相互に関連するフィールドは
独立に抽出・選定しないこと」）が指摘する一般的な設計欠陥の新しい実例。

**実害確認**: `get_net_cash()`はstockholders_equityに依存しないため
無関係。`get_roe_avg_detail()`（ROE=net_income/stockholders_equity、
TANUKI VALUATIONのROE平均に使用、tanuki=trueの銘柄が対象）が唯一の
消費経路。CRM(2011)は現在の10年ROEトレイリング窓（2017-2026年、
annual_2026.jsonまで存在）の外のため実害なし。VRT(2017)は現在の窓
（2016-2025年のちょうど10件）に含まれており現在進行形の実害の可能性
あり（ただし`get_roe_avg_detail()`の`|ROE|>80%` winsorize仕様により、
誤った値・正しい値のいずれも分母が極端に小さくROEが±80%に丸められる
可能性が高く、影響は「その1年分の符号がおそらく反転する」程度に限定
される可能性。実際の影響度はpipeline.py再実行が必要なため未確定）。

#### 対応方針
未定。CRM型・VRT型で有効な修正方式が異なるため2案を記録する:
- **VRT型（0アンカー）向け**: total_assets/total_liabilitiesが採用した
  accnと同一のaccnを、stockholders_equity抽出時にも優先的に探索する
  設計。今回確認した「正しいaccn内に正しい値が実在していた」ケース
  （VRT・CRMのIncludingタグ）に有効
- **CRM型（2アンカー競合）向け**: `_resolve_bs_entity_mixing()`の
  条件②を「本人データaccnのうち、他の同年度フィールドと一致するもの
  を優先する」形に緩和する設計。既存の安全側原則（「一意に定まらない
  場合は何もしない」）の変更を伴うため、KULR(2019)型の巻き添え
  None化防止等の既存安全性を壊さないよう全母集団シミュレーションが
  必須

まずVRT型向けの設計（より安全・影響範囲が明確）から全母集団
シミュレーションを行い、実装する。CRM型向けの設計は既存の安全側原則の
変更を伴うためより慎重な検討が必要。

#### 着手条件
なし。優先度高を維持（VRT(2017)は現在進行形の実害可能性があるため）。

---

### [BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1] bs_identity_violations_log.jsonのキー順序が実行のたびに非決定的に変化する
**優先度:** 低
**分類:** データ品質 / 再現性
**登録日:** 2026-08-02
**発見:** [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]HEI・ONDS実装検証時
（チャット記録）

#### 内容
PM銘柄の`bs_identity_violations_log.json`で、キー順序のみが実行のたびに
非決定的に変化する現象を発見した（Python `frozenset`のハッシュランダム化
が原因と推定。値・resolved状態は完全に同一で実害なし）。

#### 影響
実害なし（データの正しさには影響しない）。ただし将来の検証作業で、
実質的な変化がないにもかかわらずgit diffにノイズが生じ、確認作業を
誤らせるリスクがある。

#### 対応方針
未定。frozensetをsorted listに置き換える、またはJSON出力時に
sort_keys=True相当の安定化を行う等、低コストな対応が見込まれる。

#### 着手条件
なし。優先度低。

---

### [PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1] revenue/cost_of_revenue/gross_profitが独立にaccn・期間を選定するため異なる会計年度のデータが混在する
**優先度:** 中〜高
**分類:** バグ / 確定・複数フィールド間の期間不整合
**登録日:** 2026-08-02
**発見:** [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]個別調査
（チャット記録）

#### 内容
`revenue`/`cost_of_revenue`/`gross_profit`という相互に関連する複数のPL
flow-typeフィールドが、フィールドごとに独立してaccn・期間（fy_tag）を
選定するため、結果として異なる会計年度のデータが混在する設計上の欠陥。
[[SPAC-SHELL-BS-ENTITY-MIXING-1]]がBS instant-factフィールド間で解決した
「同一accn強制」と同種の思想が、PL flow-typeフィールド間・同一期間強制
として応用できる可能性がある。

確定した実害（2026-08-02、9銘柄・全件②タグ選定バグと確定。①genuine
定義差は0件）:

根本原因は単一メカニズムではなく、以下4つのサブパターンに整理できる:
- **(a) 候補タグ完全欠落**: AMD(2016/2017)・KO(2017)。`CostOfGoodsSold`
  タグが`cost_of_revenue`の候補リストに一切ない（[[TOTAL-LIABILITIES-
  FALLBACK-TAG-DESIGN-FLAW-1]]と同型の「候補タグ設計の不完全さ」）。own
  filingの`CostOfGoodsSold`を使えば乖離ゼロ（KOのみ比較列との差が僅少
  〈$1M・0.003%〉で実質無害）
- **(b) クロスaccn/期間不整合**: LRCX(2010)・ONDS(2017)・CRM(2013)・
  JNJ(2017)・MRVL(2017)。正しい候補タグが正しいaccn内に存在するのに、
  別accnの値が誤採用される。ONDSは規模が約100倍異なる異常な誤マッチング
  だったが、本人データで乖離ゼロと確認
- **(c) 複数タグの合算漏れ**: RMBS(2018/2019)。真のコストが2つの独立
  タグ（`CostOfRevenue`・`CostOfGoodsAndServicesSold`）の合算値
  （[[LITE-COGS-DA-TAG-UNMERGED-1]]と同型）。2018年は合算で乖離ゼロ、
  2019年は$23.6M→$3.6Mへ85%削減（残差は追加のrestatementの可能性）
- **(d) 同一filing内での類似タグ誤選択**: BSY(2019)。revenue側で複数の
  類似タグ（`Revenues`・`RevenueFromContractWithCustomerExcludingAssessed
  Tax`）から誤ったものが選ばれる新種パターン。正しいrevenueタグで乖離ゼロ

**予備検討で判明した設計上の示唆**: net_income/operating_income/R&D/
SGAへの波及は確認されず（AMD・LRCX・CRMで検証）、問題は`cost_of_revenue`
（の一部、AMD/KO/LRCX）と`revenue`（BSYのみ）に限定的。「同一accn強制」
（[[SPAC-SHELL-BS-ENTITY-MIXING-1]]型）は、BS instant factと異なり
PL/CF flow factは同一accn内に複数の(start,end)期間が混在するため実装が
複雑化する（1つのaccnに四半期・累計・年次等、数十種類の期間区分が混在
することをRCAT調査で確認済み）。

#### 影響
9銘柄（AMD/BSY/CRM/JNJ/KO/LRCX/MRVL/ONDS/RMBS）で確定。他フィールド
（同種のPL/CF flow-typeフィールド全般）への一般化可能性は限定的と判明
（net_income等主要フィールドへの波及なし）。

#### 対応方針（2026-08-02、全母集団シミュレーション結果により全面改訂）
当初想定した「単純な候補タグ拡張・優先順位変更」は**全案（a〜d）とも既存
の正しい値を壊す重大な副作用**を持つことが実データシミュレーション
（チャット記録）で判明した。設計上の教訓: 現状の
`_extract_values_best_candidate()`は「候補全体から最も新しい年データを
持つ1タグを丸ごと採用する」設計のため、**候補プールへの単純追加・変更
自体が危険**である。

- **案a（候補タグ追加）**: 単純追加は危険と確定。全105銘柄シミュレーション
  で、AMD/KO/JNJは解消できる一方、**LLY/FCX/CAT/ABBVで新規劣化を10件
  確認**（特にFCX $1,109M・CAT $211M級の大口破壊）。「他候補が本人データ
  を持たない年度に限定する」ゲート条件が必須。**ゲート条件込みの再設計が
  必要なため保留**
- **案c（2タグ合算）**: 単純合算は危険と確定。ENTG/TERは2タグが完全重複
  タグ付けのため合算すると2倍計上になり、CAT等6件で既存の正しい値を破壊
  する。「現在値とgross_profitが既に不一致な場合のみ合算を試みる」ゲート
  条件が必須。真に合算が必要なのはRMBS(2018/2019)のみと確認済み。
  **ゲート条件込みの再設計が必要なため保留**
- **案b（同一accn優先、採用）**: 比較的安全（対象が既存の別accn状態49件
  に限定されるため）。ただしaccn単位の照合だけではCRM(2013)型（同一accn・
  別期間の本人データ年度違い）を検知できない限界を確認したため、
  **(start,end)期間の一致まで見る精密化が必要**。6件（AVGO2017・
  FICO2009・LRCX2010・LYFT2018・NOW2011・ZS2017）は同一accn内一致で
  解決可能と確認済み
- **案d（revenue側優先順位変更、不採用）**: 極めて危険と確定。105銘柄
  202件スキャンで13銘柄が複数収益タグ併存も、大半（WMT/XOM/FCX/VST/CAT/
  TDY/LYFT等）はgenuine定義差の疑いが強く、機械的な優先順位変更はWMT/
  XOM等主力銘柄を破壊するリスクがある。BSY型のみ個別対応に限定する

**当面の対象**: 案b（同一accn＋期間一致優先、CRM型を除く効果確認済み分）
とBSY単独の個別対応に絞り込む。案a・cは次回セッションでゲート条件込みの
設計を詰める。

#### 実装結果（2026-08-02、案b実装完了・LRCX(2010)のみ解消）
`SECParser._align_cost_of_revenue_to_revenue_period()`を新規追加。
revenue・cost_of_revenueが異なるaccnから独立採用され、かつ
`revenue − cost_of_revenue ≠ gross_profit`という数学的矛盾が現に存在する
年度についてのみ、revenueと同一accn・同一(start,end)期間のcost_of_revenue
候補で矛盾が厳密に解消する場合に限り置換する設計（コード`b756021f6`＋
安全性修正`9616e8058`・データ`7c94c6f95`）。

**実装時に発見・是正した重大な副作用**: 初回実装（accn不一致のみを
トリガーとする単純な設計）を全105銘柄フローズン入力比較で検証したところ、
既に矛盾のない年度（GOOGL(2008)・HON(2008)・SCCO(2009/2010)、いずれも
gross_profit自体が実タグを持たずderived値だった年度）まで誤って書き換える
副作用を発見した（特にHON(2008)はgross_profitが$8,562M→$5,438M相当に
劣化する規模）。原因はgross_profitがNone〈導出前〉の年度との巻き添え比較。
ゲート条件を「矛盾が現に存在する年度のみ・gross_profitはNoneでない実タグ
起源の値のみ対象・置換後に矛盾が厳密に解消する場合のみ採用」に強化して
再検証し、対象をLRCX(2010)の1件のみに絞り込んだ上で実装完了とした。

**検証結果**: LRCX(2010)のcost_of_revenueが$1,166,219,000→$1,163,841,000
に是正され、revenue−cost_of_revenue=gross_profit($969,935,000)と完全
一致することを確認。全105銘柄フローズン入力比較でLRCX(2010)以外に変化
なし（GOOGL/HON/SCCO等の巻き添えが解消したことを含む）。
report_consistency_check.py NG=0（WARN=68件、変化なし）、pytest 513
passed/2 known failed（既知のMSFT/NVDA）。`cost_of_revenue`はTANUKI
VALUATIONのDCF/growth計算に一切使用されず、STONKS SILO側の消費経路も
gross_profit既存時は発火しないデッドコードのため、影響ゼロと確認。

**残存（案b単独では未解決、CRM/JNJ/MRVL/ONDS）**: CRM(2013)は同一accn・
別期間の本人データ年度違いのため設計上の既知の限界により対象外。
JNJ(2017)・MRVL(2017)・ONDS(2017)はrevenueと同一accn内に矛盾を解消する
候補が見つからず未解決のまま残存（案a〈候補タグ拡張〉の対応が必要な
可能性がある）。RMBS(2018/2019、案c）・BSY(2019、案d）・AMD/KO(案a）も
未着手のまま残存。

#### 対応方針
案bは完了。残る案a（候補タグ拡張、AMD/KO/JNJ/MRVL等）・案c（2タグ合算、
RMBS）・案d（BSY個別対応）は、いずれもゲート条件込みの再設計
（[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]と同一思想）が必要な
まま次回セッションに引き継ぐ。

#### 着手条件
案a・案c・案d（BSY）: ゲート条件（欠損穴埋めのみ・既存の正しい値を上書き
しない設計）を伴わない実装は行わないこと。優先度中〜高。

---

（[[SECDATA-COMPANYFACTS-OVERLOOKED-1]]は登録翌日の2026-07-24に
実質解消済みだったと判明、2026-08-16に移設漏れを訂正しBACKLOG_DONE.md
「2026-08-16（完了）」へ移設。参照）

---

### [MACRO-TRUTHY-ZERO-BUG-1] MACRO PULSE履歴バックフィルのtruthy判定によるゼロ値欠落
**優先度:** 高
**分類:** バグ / MACRO PULSE
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ10（AS-IS-184関連）

#### 背景
`05_import_history.py:122`の`get_historical_context()`が
`if ff_hi and ff_lo: ctx["ff_rate"]=...`という真偽値判定を使っており、
2020-2022年のゼロ金利期間（`ff_lo=0.0`）ではPythonの偽値として扱われ、
正当なデータがあるにもかかわらず`ff_rate`が欠落する。同じ関数内の
`yc_10y2y`/`hy_spread`/`vix`も同型の`if yc:`等の真偽値判定を使っており、
値がちょうど0になった場合は同様に欠落しうる。現行稼働中の`05_main.py`
本体（`is not None`で正しく判定）ではなく、履歴データバックフィル専用
スクリプトにのみ存在するバグ。

#### 対応方針
`if ff_hi and ff_lo:`を`if ff_hi is not None and ff_lo is not None:`に
修正する（`yc_10y2y`/`hy_spread`/`vix`も同様）。修正後、2020-2022年の
ゼロ金利期間のデータが正しく再構築されるか実データで確認する。

#### 検証記録
2026-08-16のBACKLOG棚卸しで`05_import_history.py:121`の
`if ff_hi and ff_lo:`が現在も未修正であることを確認、現状再現を確認。
優先度維持が妥当と判定した。

#### 着手条件
なし

---

### [RECESSION-SCORE-TRIPLE-CALC-1] RECESSION RISK SCOREの3計算式併存・フェーズ境界25/30の3箇所不一致
**優先度:** 高
**分類:** バグ / 設計不整合 / MACRO PULSE
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ10（AS-IS-215/213/219/230、依頼文名指し）

#### 背景
現在時点用（`computeCurrentScore()`/`_compute_current_score()`、ステップ
関数）と過去日付用（`computeScoreAsOf()`、lerp補間）という異なる2方式が
「現在」と「過去」で使い分けられており、スコア推移チャート・比較バーは
常に別数式同士の比較になっている（コード自体のコメントは意図的設計と
明記しているが、この事実は画面表示上どこにも明記されていない）。

加えてフェーズ判定の実閾値（30）に対し、①ゲージバーのゾーン区切り線
（`left:25%`）②スコア推移チャートの背景色分け（`zoneMarkAreas`）③週次
AI解説生成のGrokプロンプト自体（"フェーズ: 0-25=拡張"という文言を直接
指示）の3箇所で「25」が誤用されている。③はAIが誤った境界を前提に景気
解説文を生成しうるため、単なる表示ズレに留まらずAI生成コンテンツの
正確性にも影響する。

#### 対応方針
①25→30への表示閾値修正（ゲージバー・チャート背景の2箇所）②Grokプロンプト
文言の30への修正③lerp補間版とステップ関数版の関係（意図的な設計である
ことを画面上にも明示するか、統一するか）を判断してから着手する。

#### 検証記録
2026-08-16のBACKLOG棚卸しで`index.html:588`の`left:25%`が現在も
未修正であることを確認、現状再現を確認。Grokプロンプトが誤った境界を
前提に文章生成しうるという実害は表示ズレを超えAI生成コンテンツの
正確性に直結するため、優先度維持が妥当と判定した。

#### 着手条件
なし

---

### [HOLLOW-RALLY-DEAD-1] Hollow Rally検知の構造的恒久不発火
**優先度:** 高
**分類:** バグ / MACRO PULSE
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ10（AS-IS-204、依頼文名指し）

#### 背景
判定コードが参照する`r.sp500`列が`05_liquidity.csv`（`LIQUIDITY_COLUMNS`
定数で列挙される全列）に一切存在しないため、`sp500Rows`は常に空配列となり、
トリガー条件`sp500Rows.length>=6`が恒久的に成立しない。実装以来一度も
発火したことがないことが構造的に確定している。

#### 対応方針
`05_liquidity.csv`にS&P500値を追加するか（`update_liquidity_csv()`側の
改修）、判定ロジック自体を別データソース（例: 既存の`events.csv`や
Market Pulseのmarket_data.json）から取得する設計に変更するかを判断して
から着手する。

#### 検証記録
2026-08-16のBACKLOG棚卸しで`05_liquidity.csv`のヘッダに`sp500`列が
現在も存在しないこと、`index.html:2537-2539`の`sp500Rows`が現在も
恒久的に空配列であることを確認、現状再現を確認した。ただし本項目は
「誤った情報を表示する」型ではなく「一度も発火しない」型の不具合で
あり、AVGO/SCENARIO-BEARBULLのような本文中の明示的な自己矛盾（実害
ゼロの明記）は見当たらない。優先度「高」を維持すべきか、実害の性質
（機能が使えないだけで誤情報は出していない）を踏まえて引き下げるべき
かの判断は保留とし、次回以降の個別判断に委ねる。

#### 着手条件
なし

---

（[[PORTFOLIO-CONFIG-DUP-1]]は2026-08-15実装完了、BACKLOG_DONE.md
「2026-08-15（完了）」参照）

---

（[[TAILKPI-CONFIG-LOCATION-1]]・[[FCFCONFIG-LOCATION-1]]は2026-08-15
実装完了、BACKLOG_DONE.md「2026-08-15（完了）」参照）

（[[FCFCONFIG-MISSING-DETECTION-WEAK-1]]は2026-08-15実装完了、
BACKLOG_DONE.md「2026-08-15（完了）」参照）

---

（[[EPSANALYZER-ADMIN-ORPHAN-PAGE-1]]は2026-08-15実装完了、
BACKLOG_DONE.md「2026-08-15（完了）」参照）

---

### [CONFIG-LOAD-SILENT-FALLBACK-1] config/設定ファイル読み込み失敗時のサイレントフォールバックが複数箇所に存在（残り3件）
**優先度:** 低
**分類:** データ品質 / 監視・検知
**登録日:** 2026-08-15
**発見:** `[[FCFCONFIG-MISSING-DETECTION-WEAK-1]]`実装中の観察事項

#### 内容（部分対応済み、2026-08-16）
当初7ファイルを対象に登録したが、悪質度「完全サイレント（ログ出力
なし）」の4件（`rpo_config.json`・`beta_config.json`・
`split_history.yaml`・統合対象の`fcf_conversion_config.json`）は
CHECK-34として実装完了（詳細はBACKLOG_DONE.md参照）。

**残り3件は未実装のまま本項目に残す**:

| ファイル | ローダー | ファイル不存在時のログ | フォールバック値の性質 |
|---|---|---|---|
| `config/prompts.yaml` | `ai_analyzer.py::load_prompt()` | `Warning:`あり | もっともらしい偽装データ（`DEFAULT_PROMPT`定数） |
| `config/maturity_config.json` | `maturity_config.py::_ensure_loaded()` | `[ERROR]`あり | デフォルトプロファイルのみ（銘柄別設定は全て失われる） |
| `config/segment_config.json`・`growth_options_config.json` | `segment_config.py::_load_json()` | `[ERROR]`あり | 空辞書 |

いずれも既に`[ERROR]`/`Warning`ログが出ており相対的に緊急性が低い。
特に`maturity_config.json`・`segment_config.json`はWACC/DCF計算コアに
直結し、変更時は全銘柄再生成による影響確認が必須になるため対応
コストが高い。

#### 対応方針
CHECK-34で確立したレジストリテーブル方式（`SYSTEM_MAP.md`
「config/読み込み失敗の横断検知」参照）を踏襲する。対象モジュールに
`resolve_*_path()`を切り出し、`report_consistency_check.py`の
`_CONFIG_LOADER_REGISTRY`に1エントリずつ追記すれば、汎用チェック関数
`_check_config_loaders_resolvable()`がそのまま対応する（新規CHECK
番号の採番は不要、CHECK-34のテーブルにエントリを追加するのみ）。

#### 着手条件
なし

---

（[[RISK-FREE-RATE-HARDCODE-1]]は2026-08-16調査完了、優先度「高」は
実態と乖離していたと判明し「低」へ訂正の上、現状維持〈対応不要〉で
BACKLOG_DONE.mdへ移設。詳細はBACKLOG_DONE.md「2026-08-16（完了）」
参照）

---

（[[OPERATING-INCOME-EXTRACTION-GAP-1]]は2026-08-16実装完了、
BACKLOG_DONE.md「2026-08-16（完了）」参照）

---

### [MACRO-STYLE-FCF-ZERO-TRUTHY-EXCLUDE-1] Moat Score算出用FCFマージン平均で、正当なFCF=0年がtruthy判定により暗黙除外される
**優先度:** 低（現時点で該当データ0件・実害ゼロ）
**分類:** バグ / TANUKI VALUATION / データ品質
**登録日:** 2026-08-16
**発見:** `[[MOAT-SCORE-PARTIAL-NULL-1]]`調査中の観察事項（チャット記録）

#### 内容
`pipeline.py::_calc_moat_inputs()`のfcf_margin_3yr_avg計算部分
（2026-08-16時点で3128行目付近。`[[MOAT-SCORE-PARTIAL-NULL-1]]`実装で
周辺行が増減しているため、着手時に`grep`で現在地を再確認すること）が
`if fcf and rev and rev > 0:`というtruthy判定を
使っており、`[[MACRO-TRUTHY-ZERO-BUG-1]]`と同型のfalsy-zeroパターンを
持つ。FCFが正当な実測値0.0の年は暗黙にNoneと同じ扱いで平均対象から
除外され、3年平均のはずが実質1〜2年平均になりうる。全105銘柄の直近
3年分annual_*.jsonを実データ走査した結果、現時点でFCF=0.0ちょうどの
年は0件で、現状は実害ゼロの潜伏バグ。

#### 対応方針
`if fcf is not None and rev and rev > 0:`へ修正する。

#### 着手条件
なし（着手条件なしのため、いつでも着手可能。ただし現状実害ゼロのため
急ぎではない）

#### 関連
`[[FALSY-ZERO-PATTERN-SWEEP-1]]`（本件を含むfalsy-zeroパターンの横断
調査項目）。`[[OPERATING-INCOME-EXTRACTION-GAP-1]]`とは異なるメカニズム
（タグ不在ではなく、実測値0のtruthy誤判定）。

---

### [FALSY-ZERO-PATTERN-SWEEP-1] 数値のfalsy判定（0/0.0）による欠損誤認バグの横断調査
**優先度:** 中
**分類:** データ品質 / 横断調査
**登録日:** 2026-08-16
**発見:** `[[MOAT-SCORE-PARTIAL-NULL-1]]`調査過程の連鎖的発見（チャット記録）

#### 内容
Pythonの`0`/`0.0`がfalsyであることに起因し、正当なゼロ値を欠損と
誤認する（またはその逆の）バグが繰り返し発見されている。本セッションだけで
5例目であり、個別バグではなくコードベース全体のパターンと判断できる。
既知の発見:
- `[[STONKS-SILO-COGS-DEAD-FALLBACK-1]]`（2026-07-30対応済み、RXRX
  2021年で発見）
- `[[MACRO-TRUTHY-ZERO-BUG-1]]`（未対応、`if ff_hi and ff_lo:`）
- `[[MOAT-SCORE-PARTIAL-NULL-1]]`（`(値 or 0.0)`、2026-08-16対応済み。
  詳細はBACKLOG_DONE.md「2026-08-16（完了）」参照）
- `pipeline.py:2940`の`(oi or 0)`（`[[OPERATING-INCOME-EXTRACTION-
  GAP-1]]`調査中に発見。ただしこちらはタグ不在が根本原因で、falsy-zero
  自体は結果に影響していないと確認済み）
- `pipeline.py:3074`付近のFCF truthy除外（潜伏、`[[MACRO-STYLE-FCF-
  ZERO-TRUTHY-EXCLUDE-1]]`）

#### 対応方針
数値を扱う経路で`or 0`・`or 0.0`・`if <数値変数> and`・
`if not <数値変数>`等のパターンを`grep -rn`で網羅的に抽出し、各箇所で
「0が正当な実測値でありうるか」を判定する。正当なゼロがありうる箇所は
`is not None`ベースへ修正する。修正は影響範囲ごとに分割して実施する
（一括変更しない）。

#### 着手条件
なし

#### 関連
`[[OPERATING-INCOME-EXTRACTION-GAP-1]]`とはメカニズムが異なる
（タグ不在 vs falsy-zero誤判定）ため別項目として並存させる。本線
（`[[OPERATING-INCOME-EXTRACTION-GAP-1]]`の解消）の範囲外。

---

（[[MOAT-SCORE-PARTIAL-NULL-1]]は2026-08-16実装完了、
BACKLOG_DONE.md「2026-08-16（完了）」参照）

---

### [FCF-CAGR-YEARS-MISMATCH-1] FCF CAGR(3yr)のCAGR経過年数未補正
**優先度:** 高
**分類:** バグ / TANUKI VALUATION / stock.html
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ5（AS-IS-068）

#### 背景
stock.htmlの`valid = fcf_history.filter(fcf!=null && fcf>0)`はゼロ・
マイナスFCFの年を除外した**フィルタ後**配列であり、`valid[-4]`と
`valid[-1]`の間に除外年が挟まっていた場合、実際の経過年数は3年より多く
なる。にもかかわらず指数は`1/3`に固定されており、経過年数の実測値を
一切使っていない。表示ラベルは常に「CAGR(3yr)」だが、除外年がある銘柄
では実際より長い期間の変化率を3年複利換算したかのように誤表示する。
同種のSTONKS SILO側`cagr_3yr`（AS-IS-136）は`years`配列自体が連続した
年次リストのため、この問題は生じない。

#### 対応方針
`valid[-1].year - valid[-4].year`から実際の経過年数を算出し、指数計算
（`^(1/実経過年数)`）に反映する。表示ラベルも実経過年数を明示する
（例:「CAGR(4yr)」）よう変更する。

#### 検証記録
2026-08-16のBACKLOG棚卸しで`stock.html:2110-2112`の指数`1/3`・
ラベル`CAGR(3yr)`が現在も固定のままであることを確認、現状再現を
確認した。ユーザーが直接目にする数値ラベルの誤表示であり実害が具体的
なため、優先度維持が妥当と判定した。

#### 着手条件
なし

---

### [SCENARIO-BEARBULL-SIGN-FLIP-1] Bear/Bull成長率の符号が負の基準成長率で意図と逆転
**優先度:** 中（2026-08-16、高→中へ訂正。理由は下記「優先度訂正の経緯」参照）
**分類:** バグ / 設計上の欠陥 / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ6（AS-IS-015、依頼文名指し）

#### 背景
`calculate_scenario_valuations()`（`calculator/scenarios.py:64-66`）は
`bear_rate=base_growth_rate×0.7`・`bull_rate=base_growth_rate×1.2`という
単純な乗算で構成される。`base_growth_rate`が正の値である前提では
「Bearは基準より控えめ・Bullは基準より強気」という意図通りに機能するが、
`base_growth_rate`が負の場合（例: -10%）はBear(-7%、実際は緩やかな下落=
楽観的)・Bull(-12%、実際は急な下落=悲観的)とラベルと実態が完全に逆転する。
現状は`growth_floor=0.15`による下限クリップ等により本番データでは顕在化
していないが、ロジック自体の欠陥は残る。同一の乗算ロジックは
`calculator/growth.py::get_scenario_growth_rates()`・`segment_config.py::
calculate_scenario_growth()`という2つの未使用デッドコードにも重複実装
されている。

#### 対応方針
`base_growth_rate`が負の場合の乗数を反転させる（例: Bearは`×1.3`、Bullは
`×0.8`とし、下落幅がBear>Bullになるよう補正する）等の修正方針を設計して
から実装する。使われていないデッドコード2箇所の削除も合わせて検討する。

#### 優先度訂正の経緯（2026-08-16）
案2 Step C（BACKLOG優先度中以上の棚卸し）で、本文の「#### 背景」欄に
「`growth_floor=0.15`による下限クリップ等により本番データでは顕在化
していない」と明記されているにもかかわらず優先度が「高」のまま維持
されている自己矛盾を発見した。`calculator/growth.py:142`の
`max(growth_floor, min(growth_cap, raw_cagr))`で下限クリップ（0.15）
が実在することをコードで確認済みで、本文の主張自体は正確。さらに
同一ロジックの重複実装2箇所は本文で明示的に「未使用デッドコード」と
されている。ロジック自体の欠陥という事実認識は変えないが、優先度
表記のみを「中」へ訂正する。

#### 着手条件
なし

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

#### 棚卸し結果（2026-07-18確定）

2026-07-18の中間記録（分類の一部が未検証のまま確定していた）を受け、
15項目全件をゼロベースで再検証した（一次情報: BACKLOG.md本文各エントリ・
実装コード・BACKLOG_DONE.md記録）。

**確定した分類サマリー:**
- **解消可能（バグ）に分類（8件）**: FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1・
  CASH-TAG-MISSING-1・REVENUE-TAG-PRIORITY-FRAGILE-1・
  WORKFLOW-SEC-TANUKI-GAP-1（要設計判断のニュアンスあり）・FCF-CONVRATE①・
  MA-INTEGRATION-TAG-GAP-1・**SPLIT-REALTIME-GAP-1（今回再分類。詳細は
  同エントリの状況更新参照）**・**fcf_outlier丸めによる理由喪失＝
  [[FCF-OUTLIER-PREROUNDING-LOSS-1]]（今回再分類・新規登録）**
- **構造的限界（可視化対象）に分類（1件のみに縮小）**: FCF-CONVRATE②
  （固定比率設計がサイクル変動銘柄を表現できない構造的限界。LITE/SPIR/LLYの
  乖離倍率〈4.33倍/8.65倍/1.92倍〉を本番経路で再確認済み、本EPICの可視化
  対象として維持）
- **判断保留（5件、変更なし）**: FY52WEEK-BS-NULL-SILENT-1 Phase B/C・
  MRVL-2019-2020-NULL-1・EPS-ANALYZER-NORMALIZE-SCOPE-1・
  GROWTH-SANITY-CLASS-SYNC-1・FCF-CONVRATE③

**再分類・新規登録の詳細:**

1. **SPLIT-REALTIME-GAP-1**: 「構造的限界（是正不能）」は誤りと判明。
   タイトルは「fact競合ロジックでも是正できない」という限定的な主張で
   あり、「原理的に是正不能」ではない。`apply_split_adjustments()`・
   `split_history.yaml`が既に実装・稼働中（NOW銘柄で実績あり）であり、
   個別登録という既存の仕組みの流用のみで対応可能と判明。
   「解消可能（別アプローチでの実装待ち）」に再分類済み（詳細・根拠は
   同エントリの状況更新を参照）。

2. **fcf_outlier丸めによる理由喪失**: `pipeline.py::_compute_tanuki_score()`
   のPolicy A/B発火時、丸め前に計算済みの`score`/`comment`ローカル変数を
   単純に上書きしており、丸め前のClassificationを保持するフィールドが
   存在しないことをコードで確認した。report.txt側は乖離率・発火理由自体は
   明示表示しており「理由」そのものは喪失していないが、「丸め前は元々
   BUY/TRIM/HOLDのどれだったか」という情報のみが失われている。これは
   上書き前に新フィールドとして保持し表示に使うだけで解消できる可能性が
   高いため、「解消可能（設計変更）」と判定し
   [[FCF-OUTLIER-PREROUNDING-LOSS-1]]として新規登録した（「優先度：未定
   （要判断）」セクション参照）。POLICYB-GATE-FIX-1（BACKLOG_DONE.md）は
   発火条件（ゲート）の修正が本題で、「理由喪失」自体は同タスクの
   スコープ外だったことも確認済み。

3. **FCF-CONVRATE②**: 現在も本番経路で生存確認済み。
   `estimate_fcf_from_eps()`（core_calculator.py経由、全銘柄で無条件実行）
   が現在も`fcf_conversion_config.json`の`sector_conversion_rates`を
   使用中。LITE/SPIR/LLYの乖離倍率（4.33倍/8.65倍/1.92倍）が現在の
   スナップショットでも完全一致することを確認済み。分類は「構造的限界」の
   まま維持。

4. **sector未収録44→36の食い違いは解決済み**: 全105銘柄の`latest.json`を
   機械集計した結果、母集団（ticker_overrides・ガードA早期returnを除いた
   sector未収録数）は44銘柄で両時点とも安定していることを確認した。
   「44」は全体母集団、「36」はそのうち`fcf_estimation.applied=True`の
   サブセット件数であり、比較時にこの2つを取り違えていたことが真因と
   判明（母集団の実変化ではない、単なるカウント条件の混同）。実質的な
   変化はapplied=Trueサブセットが33銘柄（2026-07-15時点）→36銘柄
   （2026-07-18時点）に増えたことのみ（EPS Analyzerデータ反映等で
   3銘柄が新たに条件を満たした）。

**次回の進め方（申し送り）**: 本棚卸しは2026-07-18に確定した。可視化対象
となる構造的限界はFCF-CONVRATE②の1件に縮小されたため、次回セッションでは
以下を検討する：①FCF-CONVRATE②単独の可視化設計（**SITM・LITE限定**の
スコープ、フィールド構成・表示箇所。詳細は下記追記参照）、②
SPLIT-REALTIME-GAP-1（解消可能・分離済み）とFCF-OUTLIER-PREROUNDING-LOSS-1
（解消可能・新規登録）はそれぞれ独立タスクとして個別に着手判断する。

**追記（2026-07-18・[[FCF-ESTIMATE-SKIP-STABLE-1]]完了により可視化スコープ縮小）**:
FCF-CONVRATE②の可視化設計に先立つ事前調査で、82銘柄中「機械的置換」に
分類していた54銘柄のうち、生FCFが多年度で安定（CV<0.3）かつ外れ値未検出の
22銘柄について、`estimate_fcf_from_eps()`にスキップ条件を追加し**解消済み**
（詳細はBACKLOG_DONE.md参照）。これにより本EPICが可視化対象とする
「構造的限界」の実体は、真にボラティリティが大きい銘柄群
（SITM/LITE/SPIR等、FCF-CONVRATE②の固定比率設計限界）により明確に
絞り込まれた。ticker_overrides該当のGOOGL/MSFTと、CV 0.3〜0.5の中間域
（乖離が小さく実害の乏しい銘柄群）は今回のスキップ条件の対象外のまま
残っており、これらへの対応要否は別途判断が必要。

**追記（2026-07-18・原因ベース分析によるFCF-CONVRATE②最終スコープ確定）**:
当初想定7銘柄（SITM/LITE/SPIR/AMZN/SOFI/CWAN/DOCN）について、cv・
divergence_ratioの閾値による機械的切り分けを試みたが、**LLY（cv=0.989,
dr=1.92）がDOCN（cv=0.405, dr=1.85）を両軸で完全に上回るため、閾値だけ
での分離は数学的に不可能**と判明した（どのように閾値を調整してもDOCNを
含めればLLYも必ず含まれる）。

そこで閾値ではなく、境界域のGTLB/LLY/KO/FRSH/SNPSを加えた計12銘柄について
SEC XBRL実データ（`common/sec_data/data/{TICKER}/annual_YYYY.json`、6-7年分）
を用いた個別の原因分析を実施した。結果、**真に「業界サイクル起因で解消
不能な構造的限界」と呼べるのはSITM・LITEの2銘柄のみと確定**した。残り
10銘柄は以下の通り性質の異なる複数グループに分解された：

- **一時的な成長投資フェーズ（可視化対象外・対応不要）**: AMZN
  （AI/クラウドCapEx急増、OCF自体は健全）・LLY（GLP-1製品向け製造能力
  増強、[[LLY-CAPEX-STALE-1]]完了時の実測値$7.84Bと一致確認済み）・
  DOCN（黒字化途上、NI/OCFとも単調改善トレンド）・FRSH（SaaS成熟化、
  2025年初黒字化）。いずれも設備投資が一巡・事業が成熟すればFCFが
  正常化する見込みのため、可視化対象からも個別バグ修正対象からも除外する
- **一過性要因・M&A（個別タスクへ分離）**: CWAN（Enfusion買収）・SNPS
  （Ansys買収、D&A急増$295M→$660Mで確認）。詳細は
  [[CWAN-SNPS-MA-DISTORTION-1]]へ分離登録
- **一次情報不足で未確定（個別調査タスクへ分離）**: KO（2024年OCF急落の
  原因がSEC XBRL構造化データからは特定不能）・SPIR（2025年NI黒字転換と
  OCF最悪化の不整合、一次情報未確認）。詳細は
  [[KO-SPIR-CF-CAUSE-UNCONFIRMED-1]]へ分離登録
- **conversion_rate設計限界（既存機構で対応済み・新規対応不要）**: SOFI。
  貸付金組成額がOCFを支配する会計構造上のFCF概念不適合であり、
  `stock.html:850-863`の既存`FCF_LOW_RELIABILITY_SECTORS`
  （Financial Services）バナーが既にSOFIに対して発火済みのため、
  FCF-CONVRATE②としての新規対応は不要と判定
- **成長ステージ＋推定手法混在（対応不要・記録のみ）**: GTLB。SaaS請求
  サイクルの未成熟（年間契約の請求・回収タイミングによるOCF符号反転）と
  `estimate_fcf_from_eps()`の単年度NI依存という推定手法自体の限界が
  混在。5年間黒字化なしという既知の事実（BACKLOG.md:2334参照）と整合する
  が、新規の個別対応タスクとしては切り出さず本記録に留める

**FCF-CONVRATE②の可視化設計スコープは、SITM・LITEの2銘柄に確定し、次回
セッションで着手する。**

**追記（2026-07-18・FCF-CONVRATE②可視化実装完了）**: 上記スコープ確定を
受け、SITM・LITE限定の個別ティッカーリスト方式（`FCF_CYCLICAL_VOLATILITY_TICKERS`）
によるstock.htmlバナー・report.txt表示を実装完了。詳細は
BACKLOG_DONE.md「[FCF-CONVRATE②] ...」を参照。本EPIC自体は、方針の骨子②
（構造的限界の可視化）の実装対象がFCF-CONVRATE②の1件のみだったため
これで実質完了だが、判断保留のまま残る5件（FY52WEEK-BS-NULL-SILENT-1
Phase B/C・MRVL-2019-2020-NULL-1・EPS-ANALYZER-NORMALIZE-SCOPE-1・
GROWTH-SANITY-CLASS-SYNC-1・FCF-CONVRATE③）があるため、EPICエントリ自体は
BACKLOG.mdに残置する。

**追記（2026-07-20・GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1完了、段階1可視化を追加実装）**:
[[GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1]]について、骨子①（可視化前の
バグ切り分け）でHONのsegment_config.json成長率（8.5%）が2026-05-30の
12銘柄一括登録時にAIが機械生成した裏付けなしの値と判明したため実績CAGR
水準（2.6%）へ修正（verdict: AGGRESSIVE→PLAUSIBLE）。骨子②（構造的限界の
可視化）として、残る14銘柄（AMD/NVDA/ONDS/ASTS/BKNG/BROS/ELF/KULR/LLY/
TER/XOM/ALAB/IONQ/RCAT）に対し、FCF-CONVRATE②と同型の個別ティッカー
リスト方式（`GROWTH_STRUCTURAL_MISMATCH_TICKERS`）でstock.htmlバナー・
report.txt表示を追加実装した。これにより段階1（成長率算出）についても
骨子①②の適用が完了し、段階2（FCF-CONVRATE②）と合わせて両段階で
可視化パターンが確立された。詳細はBACKLOG_DONE.md
「[GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1]」参照。

**追記（2026-07-20・段階2の広範な再調査。FCF-OUTLIER-PREROUNDING-LOSS-1
着手前の状況確認）**:

- **判断保留5件の記載修正**: このうち**GROWTH-SANITY-CLASS-SYNC-1は
  2026-07-19に既に完了・BACKLOG_DONE.md移動済み**であり、上記
  「判断保留5件」の記載は陳腐化していたと判明した。判断保留として
  実質残るのは4件（FY52WEEK-BS-NULL-SILENT-1 Phase B/C・
  MRVL-2019-2020-NULL-1・EPS-ANALYZER-NORMALIZE-SCOPE-1・
  FCF-CONVRATE③）のみ
- **FCF-CONVRATE①・③は独立した定義エントリが見つからず**、
  BACKLOG.md・BACKLOG_DONE.mdのいずれを検索しても2026-07-18棚卸し時点の
  暫定ラベル以外の記述が存在しないことを確認した。次回このEPICに触れる際に
  定義を確認・明文化するか、既存の完了タスク（例:
  [[FCF-CONVRATE-DESIGN-LIMIT-1]]のキー名不一致修正等）への再マッピングを
  検討する必要がある
- **FCF-CONVRATE②の現状値を更新**: CWAN-SNPS-MA-DISTORTION-1完了後、
  LITEは買収・統合関連加算の控除により調整済み純利益がマイナス転落し、
  生FCFフォールバックへ切替わった（4.33倍→フォールバック採用、
  DCF_Reliability=LOWである点は変わらず）。SPIRは8.65倍→8.47倍、
  LLYは1.92倍→1.88倍（いずれも微減）。`FCF_CYCLICAL_VOLATILITY_TICKERS`
  （LITE・SITM限定）の可視化スコープ自体は変更不要と判断した
- 本再調査から派生した新規タスク: [[MA-INTEGRATION-TAG-GAP-1]]
  （状況追記）・[[FCF-EST-DIRECTION-GUARD-1]]・
  [[FCF-CONVRATE-LOWER-DIVERGENCE-1]]・[[AMZN-DIVERGENCE-HIGH-1]]・
  [[FCF-EST-NOTE-DISPLAY-1]]（いずれも新規登録、詳細は各エントリ参照）

**追記（2026-07-21・FCF-CONVRATE①③の調査完了・対応方針確定）**:

①③の実体を[[FCF-CONVRATE-DESIGN-LIMIT-1]]まで遡って確認した結果、
①＝sector未収録銘柄の未検証問題、③＝Damodaran EBIT(1-t)ベース業種比率を
純利益(NI)ベースへ変換するロジック不在、と定義を確定した。

**①の実害範囲を再確認**: sector未収録49銘柄のうち、実際にDCF計算へ
反映される（`fcf_estimation.applied=True`）のは18銘柄のみ（SPIR, CPRT,
AAPL, DELL, LLY, VRT, GEV, HQY, ELF, SCCO, XOM, VST, CSGP, CAKE, BROS,
LRCX, ENTG, LYFT）。残り28銘柄はconversion_rateが計算・表示されるのみで
最終IVには無関係。

**③の根本修正（案A: 会計恒等式によるDamodaran比率置換）を見送り、
現状維持と決定**。理由:
1. Damodaran公式データ（oifcff.xls・margin.xlsから算出したFCFF/NI比率）
   への置換を①対象18銘柄＋既存9カテゴリ使用銘柄の計53銘柄でオフライン
   シミュレーションした結果、IV/upsideが2〜20倍動く銘柄があるにも
   関わらず、53銘柄中49銘柄でTANUKI SCORE Classificationは変化しない
   （Policy B WATCH強制丸めが支配的なため）。実害改善効果が乏しい
2. 既存の較正値（Software_System_Mature=1.00/SaaS=1.61、実測データに
   基づく較正済み）は、Damodaran生値（両者とも0.477に収束、
   Mature/SaaSの区別自体を持たない）より明確に優れており、置換すると
   較正作業の成果を失う
3. 残り7カテゴリ（Aerospace_Defense等）もDamodaran生値の機械的適用は
   リスクが高い（Software_Internet業種でNet Margin≈0のため比率が21倍に
   発散、Power_Utility業種でFCFF/NI比率が負値-0.473になりVSTのIVが
   マイナスに符号反転する等を実データで確認済み）

**新規発見: divergence_warningの符号反転検知漏れ**（重要度：高、
[[FCF-DIVERGENCE-SIGN-GUARD-1]]として別途新規登録、下記参照）

**①③の今後の扱い（2026-07-22訂正）**: 「②と同型に統合」という上記の
方針は撤回し、3件に分けて設計し直す:
- ①: FCFEstimationResultに`rate_is_sector_default`等のフラグを追加し、
  機械的に検知・表示する設計（固定リスト不要）
- ③: ticker単位の表示ではなく、fcf_conversion_config.json側に
  セクターカテゴリ単位の開発者向けメタ情報として持たせる設計
  （画面表示は変更しない）
- ②表示不一致バグ（新規発見）: report.txtはfcf_estimation.applied=True
  前提でネストされているが、stock.htmlはticker集合の所属のみで判定し
  applied状態を見ないため、LITE等でapplied=Falseの間、両者の表示が
  食い違う。独立バグとして修正要
いずれも実装未着手。詳細は「次セッション着手順序」欄参照。

**過去記録の不正確性（新規発見）**: [[FCF-CONVRATE-DESIGN-LIMIT-1]]
（2026-07-14完了記録）の「oifcff.xlsとの突合でEBIT(1-t)/Revenue比率を
確認した」という記述は、oifcff.xls実データに比率列自体が存在しない
（実額集計のみ、Revenue列なし）ため、当時の確認内容が不正確だった
可能性が高い。事実として記録するのみで、当時の判断への遡及的な
是正は行わない。

---

## 優先度：未定（要判断）

### [FCF-CONVRATE-LOWER-DIVERGENCE-1] dr<1側29銘柄の構造的ミスマッチをFCF-CONVRATE②可視化に統合
**優先度:** 未定
**分類:** データ品質 / TANUKI VALUATION / FCF-CONVRATE②派生
**登録日:** 2026-07-20
**発見:** [[TRUST-SUMMARY-EPIC-1]]段階2再調査・divergence_warning閾値検証

#### 背景
`divergence_warning`はdr>=2.0のみ検知し、dr<1（過小推定）側は一切検知
しない非対称設計になっている。既存の2.0/5.0という閾値はgit調査の結果、
明確な根拠のない経験的な割り切り値と確認済み（導入コミット`3c12dd1b1`
2026-04-19「Add files via upload」、根拠記載なし）。

dr<1の銘柄はtanuki=true・fcf_estimation.applied=Trueの59銘柄中
**29銘柄（49%）**と多数存在する。サンプル5銘柄（LYFT/PAYS/FLYW/CSGP/
ZETA）を10-K等の一次情報で確認した結果、いずれも①raw_fcfの一過性な
水増しでも③Adj_NI側の異常な過小評価（バグ）でもなく、
**②conversion_rateの構造的ミスマッチ**（FCF-CONVRATE②と同型の性質）
と判明した。内訳は以下の通り異なるメカニズムに分解される：
- **決済/フロート型（LYFT/PAYS/FLYW）**: 事業モデル特有の運転資本
  タイミング（保険準備金・顧客資金float等）がOCFを体系的に押し上げる、
  SITM/LITEの「サイクル変動」とは別種の固定比率限界
- **意図的な成長投資による一時圧縮（CSGP）**: AMZN/LLY等で既に確認済みの
  「戦略的投資による収益圧縮」と同型パターン（CoStarはHomes.com投資を
  2026年に$3億削減予定と表明済みで、時間経過で正常化する見込み）
- **SBC比重の高い高成長企業のD&A非加算（ZETA）**:
  [[FCF-CONVRATE-DESIGN-LIMIT-1]]既知の残課題（Mature/SaaS判定精度
  約78%問題）と関連する可能性

#### 対応方針（未確定）
Policy B判定に新たな下限閾値を追加する方向（＝異常検知として扱う）
ではなく、既存のFCF-CONVRATE②可視化パターン（現在
`FCF_CYCLICAL_VOLATILITY_TICKERS`＝LITE・SITMのみ）を拡張し、構造的
限界として透明化する方向を推奨する。ただし残り29銘柄中、サンプル5件を
除く24銘柄は未確認のままであり、同様の一次情報確認が必要。

#### 着手条件
なし（残り24銘柄の一次情報確認を先行させることを推奨）

---

### [AMZN-CONVRATE-OVERRIDE-REVIEW-1] AMZNのticker_override（conversion_rate 0.55）の前提再検証
**優先度:** 低
**分類:** データ品質 / TANUKI VALUATION / FCF-CONVRATE②派生
**登録日:** 2026-07-20
**発見:** [[AMZN-DIVERGENCE-HIGH-1]]（完了・BACKLOG_DONE.md参照）原因調査時の副次発見

#### 背景
AMZNのticker_override（`fcf_conversion_config.json`、conversion_rate
0.55）の設定根拠は「EC部門の重いCapEx・ファイナンスリースを考慮。AWSの
高転換とEC低転換の加重平均」——すなわちAWS＝軽CapEx・高転換率、EC＝重
CapEx・低転換率という二分法を前提としている。

しかし2025年以降のCapEx急増（$131.8B、前年比+59%、2026年計画$200B）は
10-K・外部報道とも「大部分はAWS事業成長を支えるための技術インフラ投資」
と明記されており、**AWS自体が現在のCapEx急増の主因**になっている。
当初の二分法（AWS=軽CapEx）の前提が現在の実態とズレている可能性がある。

0.55という数値自体が誤りとまでは断定できないため、次回セッションで
実測データに基づく再較正の要否を検討する。

#### 着手条件
なし

---

### [STOCK-HTML-CLASSIFICATION-MISSING-1] stock.html個別銘柄ページにTANUKI SCORE Classificationが表示されていない
**優先度:** 未定
**分類:** TANUKI VALUATION / 表示 / フロントエンド
**登録日:** 2026-07-20
**発見:** [[FCF-OUTLIER-PREROUNDING-LOSS-1]]（完了・BACKLOG_DONE.md参照）調査時の副次発見

#### 背景
FCF-OUTLIER-PREROUNDING-LOSS-1の実装可否調査時、`stock.html`
（銘柄個別ページ）には`tanuki_score`・`score_comment`・
Classification（BUY/WATCH/HOLD/TRIM/GROWTH_PREMIUM/SELL/PASS）の
いずれも表示されていないことが判明した。ファイル内の"tanuki_score"の
出現箇所はMatrix可視化に関するコメント文言のみで、実際のフィールド
参照ではない。

Classification一覧がどの画面・ツール（`index.html`等）に存在するかは、
本タスクの発見元調査の範囲では特定できなかった。FCF-OUTLIER-
PREROUNDING-LOSS-1で追加した`pre_rounding_score`・
`rounded_by_policy`等の表示先を検討する際にも関わる可能性がある。

#### 着手条件
なし

---

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

#### 状況追記（2026-07-20・全105銘柄タグ影響網羅調査完了）
機械スキャンの結果、未登録2タグを過去に一度でも申告した銘柄は34件、
うち現在（EPS Analyzer最新年度）も申告中は**17件**（過去申告のみで
現在は無関係な17件を除外済み）。

現在も申告中の17件を、CWAN-SNPS-MA-DISTORTION-1控除メカニズムへの
影響で3グループに分類した：
- **グループA（メカニズム未到達・無関係、6件）**: AVAV/BBAI/COHR/RDW
  （`fcf_outlier.action=="excluded"`によりガードAで早期リターンし
  控除ロジック自体に到達しない）・CART（該当額$0）・VZ（別要因で
  `applied=False`）
- **グループB（タグ追加で改善方向、dr>1が是正される、4件）**: SNPS
  （1.34→1.18）・SITM（2.41→2.14）・NOW（1.54→1.50）・AVGO
  （1.15→1.14、ほぼ無視できる）
- **グループC（タグ追加で悪化方向、dr<1が更に悪化する、4件）**: CSGP
  （0.52→0.28、明確に悪化）・ZETA（0.66→0.53）・AMD（0.52→0.51、
  無視できる）・HQY（0.52→0.51、無視できる）

**単純なタグ追加は改善（グループB）と悪化（グループC）がほぼ相殺し、
net効果は中立に近いと判明**。控除メカニズムはdr>1（過大推定の是正）を
前提に設計されており、dr<1の銘柄に同じ控除を機械的に適用する妥当性は
別途検証が必要（詳細は[[FCF-EST-DIRECTION-GUARD-1]]参照）。タグ追加
単独での対応は非推奨、方向性ガード実装を優先すべきと判断する。

`TRANSIENT_CATEGORIES`からの「買収・統合関連」除外設計（カテゴリ除外
問題）についても検証した。技術的にはitem_id単位の分離が
`adjustment_items.json`のスキーマ変更なしで実現可能と確認したが、
現在flagged状態の対象銘柄は全て上方乖離（FCF-OUTLIER-1ルールにより
一過性費用の有無に関わらずaction=flaggedのまま変化しない設計）のため、
**現在の母集団では実害ゼロ**と確認した。優先度は低のまま据え置く。

#### 状況追記（2026-07-20・[[FCF-EST-DIRECTION-GUARD-1]]完了により
グループC懸念が構造的に解消）
方向性ガード実装（コミット`3b413b849`）により、控除前Adj_NIベースの
`pre_deduction_dr<=1.0`の銘柄には控除自体が適用されなくなった。これにより
上記グループC（タグ追加で悪化方向、CSGP/ZETA/AMD/HQY）の懸念は構造的に
解消されている見込みである——タグ追加後に新たに`pre_deduction_dr<=1`と
判定される銘柄は、ガードにより自動的に控除対象から除外されるため、
「タグ追加で改善と悪化が相殺する」問題自体が発生しないはずである。
ただし本追記はガードの設計上の帰結からの推論であり、実際にタグを
追加した場合の正式な全母集団再検証は次回タグ追加検討時に行うこと。

#### 状況追記（2026-07-20・正式再検証の結果、上記「構造的解消」は
一部誤りと判明）
実関数呼び出しによる正式な全母集団再検証の結果、上記の推論は
**AMD・HQYの2銘柄では正しかったが、CSGP・ZETAの2銘柄では成立しない**
ことが判明した。CSGP・ZETAは現在のpre_dr（0.96・0.95）が1.0のすぐ下に
あり、タグ追加によるAdj_NI増分（新タグの税引後net_amount）だけで
pre_drが1.0を超えてしまう「境界の跳ね返り」が実データで確認された
（CSGP: dr 0.96→0.45、ZETA: dr 0.95→0.63、いずれも悪化）。ガードは
「pre_drの計算に用いるadj_net_income_orig自体が変化する」ケースまでは
防げないため、タグ追加時にAdj_NI自体を押し上げる副作用がある限り、
境界近傍銘柄の跳ね返りリスクは残る。

**副次発見・別件として対応済み**: 上記の精査過程で、`ma_addback`計算が
税引前`amount`を合算していたのに対し、`adjusted_net_income`自体は
EPS Analyzer側で税引後`net_amount`ベースで構築されているという基準
不一致（CWAN-SNPS-MA-DISTORTION-1実装当初からの系統的な過剰是正バグ、
本件の境界跳ね返りリスクとは独立の問題）を発見し、`net_amount`基準へ
統一する修正を実施済み（コミット`3d434c29d`）。ガード許可中51銘柄中
25銘柄で実質的な変化（全件est_fcf増加方向、悪化ゼロ）。IV変化幅
+0.01%（GOOGL）〜+17.11%（CWAN、想定通り0.88倍→1.15倍相当に是正）。
Classification変化は0件。この修正はpre_deduction_dr・ガード判定自体には
影響しないため、上記の境界跳ね返りリスクの解消には寄与しない（別軸の
独立した問題であることを確認済み）。

**本タスク本体（未登録タグ追加の要否）は引き続き判断保留**。境界跳ね返り
リスクへの対応方針として、CSGP・ZETAを固定除外リストで弾く案は
CHAT_RULES.md「銘柄固定のハードコード禁止」原則（機械的に判定可能な
条件がないか5回以上検討する）に反するため不採用とする。次回検討時は
①根本原因（pre_dr=1.0近傍の境界脆弱性）そのものへの対応、②境界近傍銘柄
（pre_dr 0.9〜1.1、現在17銘柄該当: INTU/ADBE/NET/CPRT/META/CSGP/ESTC/
MSFT/ZETA/ADSK/SCCO/FROG/PM/WST/RMBS/ENTG/KLAC）を機械的に検知し
タグ追加前に個別確認する運用、のいずれかを検討する。

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
**2026-07-15完了の[[VALIDATOR-IVPS-MISMATCH-1]]（BACKLOG_DONE.md参照）
で解消済み**。

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

### [OI-RECONSTRUCTION-MISSING-OPEX-LINES-1] 営業利益再構成が別建て営業費用（RestructuringCharges等）を見落とし系統的に誤差を生む
**優先度:** 中（実測で-11.9%〜-38.3%〈HON〉・+320.9%〈COHR FY2023〉という
定量化済みの既知の誤差が判明しているため「低」ではないが、現時点で
投資判断〈IV・TANUKI SCORE・MATRIX分類〉への実害は確認されていないため
「高」でもない）
**分類:** バグ / データ品質 / SEC EDGAR / 確定・候補タグ設計欠陥
**登録日:** 2026-08-19
**発見:** `[[OPERATING-INCOME-EXTRACTION-GAP-1]]`フォールバック向き
反転（案A・案D）実装時のHON/COHR実データ検証

#### 問題
GP法（`gross_profit − R&D − SGA/S&M`）は、`RestructuringCharges`・
`OtherOperatingIncomeExpenseNet`等の**別建てで報告される営業費用**を
控除しないため、これらを計上する企業で営業利益を系統的に誤る。

#### 実測（2026-08-19）
- HON: `OperatingIncomeLoss`標準タグが再開されたFY2022-2025（真値既知）
  でGP法をバックテストした結果、**-11.9%〜-38.3%の系統的な過小評価**
- HON FY2011の`RestructuringCharges`は$743M（別建て営業費用の実例）
- COHR FY2023: GP法でも誤差**+320.9%**
- COHRは`RestructuringCosts`（$160M）・`OtherOperatingIncomeExpenseNet`
  （$47.6M）を別建て報告

#### Layer3側にも同型の問題がある（重要）
2026-08-19の消費者確認で、TANUKI TAIL等が使う
`layer3_builder.py::build_ticker_store()`は`annual_YYYY.json`を読まず
`company_facts.json`から独自に再抽出しており、`operating_income`の
候補タグは`OperatingIncomeLoss`単独で**GP法/pretax法のフォールバックを
持たない**ことが判明した。標準タグが取得できない銘柄では、Layer3側は
`operating_income`が欠損したままになる。**「GP法の」ではなく「営業利益
再構成の」課題として登録しているのはこのため**——GP法固有の課題として
登録すると対象範囲を見誤る。

**（2026-08-19追記）** その後の実測で、Layer3側の問題は「フォールバック
不在」だけでなく**「実在するデータの取りこぼし」**という別種の欠陥も
併発している**疑いがあった**（JNJのcompany_facts.jsonには
`OperatingIncomeLoss`のFY 10-Kエントリが実在するのに、Layer3の年次
エントリは0件）。この取りこぼし自体は`[[LAYER3-ANNUAL-CLASSIFICATION-
DROPS-DATA-1]]`として別項目に切り出した。

**（2026-08-19②訂正）** 上記の切り出し先で範囲実測を実施した結果、
JNJ・KLAC・LLY・XOMの年次`operating_income`0件は**「期間分類の欠陥」
ではなく「6年保持窓の意図した挙動＋タグ報告打ち切りが古い」**ことが
判明した（`_classify_period()`自体は正しく分類、保持窓フィルタのみで
除外）。**「フォールバック不在」自体は事実として残る**（Layer3側には
`operating_income`のGP法/pretax法相当の再構成が存在しない）が、
「取りこぼし」という別種の欠陥は年次側では確認されなかった。本項目の
対応方針にある「Layer3側（フォールバック自体の有無）」は、この
フォールバック不在そのものを指すものとして引き続き有効。詳細は
`[[LAYER3-ANNUAL-CLASSIFICATION-DROPS-DATA-1]]`参照。

本項目の対応を検討する際は、**parser.py側（GP法の控除項目追加）と
Layer3側（フォールバック自体の有無）の両方を対象範囲に含めるか**を
判断すること。

#### 影響範囲が拡大した経緯（記録として重要）
2026-08-19のフォールバック向き反転（案A）により、GP法は「算出可能なら
常に採用」される設計になった。反転前よりGP法の適用範囲が広がっており、
**この弱点を認識した上で適用範囲を拡大した**という判断の経緯をここに
明記する。反転自体は実データ（GP法が算出可能な4銘柄全てでyfinanceと
0.0%完全一致、旧pretax法は-11.4%/-82.4%乖離）に基づく妥当な判断だが、
GP法が完璧という意味ではない。

#### 実測結果（2026-08-19、タグ候補の実データ検証）

**検証セット**: `OperatingIncomeLoss`標準タグが利用可能（真値既知）な
ticker-yearを全105銘柄から収集——GP法検証675件・pretax法検証979件。
HON/COHRに限定せず全105銘柄の該当年度を使用した。

**方法論上の注意（次に同種のバックテストをする際に必ず踏襲すること）**:
誤差を「真値に対する%」で測定すると、真値がゼロ近傍の年度（AMZN 2014
〈損益分岐点、真値$178M〉等）で+12,471%のような桁外れの値が出て指標
として機能しなくなる。**「revenue（売上高）に対する%」で測定する**
ことで、この罠を回避した。

**GP法の候補タグ実測**:

| 追加候補 | 中央値誤差（対売上高） | 改善した該当行の割合 |
|---|---|---|
| ベースライン（候補なし） | 5.92% | — |
| +`RestructuringCharges` | 4.73% | 61%（267件中） |
| +`GoodwillImpairmentLoss` | 8.32% | 32%（335件中） |
| +`ImpairmentOfLongLivedAssetsHeldForUse` | 8.75% | 39%（119件中） |
| +`ImpairmentOfIntangibleAssetsExcludingGoodwill` | 2.76% | 34%（83件中） |
| +`AssetImpairmentCharges` | 5.83% | 50%（162件中） |
| 5候補全て合算 | 5.02% | 改善220・悪化72・無変化383 |

**結論**: `RestructuringCharges`のみが一貫して改善に寄与する（該当行の
61%で改善）。他の候補（特に`GoodwillImpairmentLoss`・
`ImpairmentOfIntangibleAssetsExcludingGoodwill`）は改善する行より
悪化する行の方が多く、**採用しない**。「候補を増やすほど良くなる」
わけではないことが実測で示された。

**pretax法の候補拡充は実測の結果、見送りと判断**:

| 追加候補 | 該当件数 | 追加前→追加後（中央値） | 改善割合 |
|---|---|---|---|
| `InterestExpenseNonoperating` | 173 | 0.00%→1.24%（悪化） | 20% |
| `IncomeLossFromEquityMethodInvestments` | 274 | 0.61%→0.58% | 34% |
| `ForeignCurrencyTransactionGainLossBeforeTax` | 417 | 0.11%→0.49%（悪化） | 24% |
| `GainsLossesOnExtinguishmentOfDebt` | 278 | 0.24%→0.57%（悪化） | 23% |

- 現行のpretax候補セットは既に高精度（ベースライン中央値誤差
  **0.12%**〈対売上高〉）
- 4候補全てで追加すると中央値が悪化した。**原因は未検証の推測だが**、
  これらの項目の多くは既存の`OtherNonoperatingIncomeExpense`集計タグに
  既に含まれており、追加控除すると二重計上になっている可能性がある
  （断定はしない）
- `InterestExpenseOperating`（本項目のきっかけ）はCOHR・SOFIの2銘柄
  のみが使用する稀なタグで、汎用候補への追加による全体改善効果は
  期待できない
- **結論: pretax法の候補拡充は行わない**

#### 対応方針（実測結果を踏まえ2026-08-19に範囲を絞り込み）
**残る実装候補は`RestructuringCharges`（および`RestructuringCosts`
——COHRが使う別名タグ、未検証）のGP法への追加のみ**。当初案にあった
`OtherOperatingIncomeExpenseNet`等の追加、およびpretax法側の候補拡充は
実測の結果いずれも見送りと判断したため、着手範囲から外す。

- `RestructuringCharges`・`RestructuringCosts`をGP法の控除項目に追加
  する（`RestructuringCosts`は未検証のため、追加前にRestructuringCharges
  と同様のバックテストを実施すること）
- 追加後は、`OperatingIncomeLoss`標準タグが利用可能な銘柄・年度で
  **バックテスト**し、誤差が縮小することを実測で確認する（675件の
  検証セットが既にある）
- pretax法の候補拡充・その他GP法候補（Goodwill/Intangible減損等）は
  実測の結果採用しないと決定済みのため、再検証は不要

#### 関連
- `[[OPERATING-INCOME-EXTRACTION-GAP-1]]`（BACKLOG_DONE.md、本問題の
  発見元）
- `[[QUALITY-GATES-EPIC-1]]`本線3（ゲート1のyfinance照合が本問題の
  検証手段になる）
- `[[VRT-REVENUE-2018-MISSING-1]]`（同じ検証で発見された別の入力品質
  問題）
- `[[LAYER3-ANNUAL-CLASSIFICATION-DROPS-DATA-1]]`（Layer3側の別種の
  欠陥、2026-08-19新規登録）

#### 着手条件
なし。ただし対象は`RestructuringCharges`/`RestructuringCosts`のGP法
追加のみに絞る（pretax法拡充・他のGP法候補は実測により見送り済み）。

---

### [LAYER3-ANNUAL-CLASSIFICATION-DROPS-DATA-1] Layer3の年次期間分類が実在するデータを取りこぼしている（年次側は調査完了・実質解消／四半期側は限定的な残課題あり）
**優先度:** 低（2026-08-19②の範囲実測により、当初の仮説は大半が誤りと
判明。年次側は確認された未解決の欠陥が0件、四半期側も確認された欠陥は
4件でいずれもTAIL非消費フィールド）
**分類:** 調査完了 / データ品質 / SEC EDGAR / Layer3統合スキーマ
**登録日:** 2026-08-19
**更新日:** 2026-08-19③（`CELH stock_based_compensation`のgap=1を
個別調査。原因未特定のまま記録、TAIL実消費への影響なしを確認）
（2026-08-19②：全105銘柄相当・32フィールドの範囲実測を実施。
年次側の仮説はほぼ全否定、四半期側も実測。詳細は本文参照）
**発見:** `[[OI-RECONSTRUCTION-MISSING-OPEX-LINES-1]]`実測調査（Step 3、
Layer3側の営業利益再構成の実態確認）

#### 内容（登録時点、2026-08-19①）
`layer3_builder.py::build_ticker_store()`を全tanuki銘柄（100件）で
実行した結果、JNJ・KLAC・LLY・XOMの4銘柄で`operating_income`（年次）の
エントリが0件だった。JNJの`company_facts.json`には`OperatingIncomeLoss`
のFY 10-Kエントリが12件存在することを確認し、「Layer3独自の期間分類が
実在するデータを拾えていない可能性」という仮説のもとで登録した。

#### 年次側 範囲実測結果（2026-08-19②）——仮説は大半が否定された
100銘柄×32フィールド＝3,200行を本番の`_classify_period()`・
`build_ticker_store()`をimportして実測（自前の判定ロジック再実装なし）。

| 状態 | 件数 |
|---|---|
| (a) 元データなし | 1,820 |
| (b) 正常 | 13 |
| (b) 部分取りこぼし | 1,335 |
| (c) 完全取りこぼし | 32 |

- (c) 32件のうち**30件は`_ANNUAL_YEARS=6`保持窓で完全に説明可能**
  （タグ報告終了が6年より前）。JNJ・KLAC・LLY・XOMの`operating_income`
  もこれに該当——**「期間分類のバグ」ではなく「6年保持窓の意図した
  挙動＋タグ報告打ち切りが古い」の組み合わせ**だった（JNJの最新
  `OperatingIncomeLoss`エントリ〈`end=2014-12-28`〉を1条件ずつ評価し、
  `_classify_period()`自体は`is_annual=True`と正しく分類、
  `_process_entries()`の`end>=cutoff_a`保持窓チェックのみで除外される
  ことを実際に確認済み）
- 残り2件（`APP capital_expenditure`・`MSFT depreciation_and_
  amortization`）は当初「6年窓内に生データがあるのにLayer3が0件＝真の
  異常」と報告したが、**これも誤りだった**。`config/sec_concept_
  definitions.json`の`ticker_overrides`にAPP/MSFTそれぞれ`action:
  "exclude"`の設定が存在し、**意図的な除外設定**だった（旧
  `quarterly.py::TICKER_RESTRICTIONS`からの移行済み設定）。当初の実測
  スクリプトが`ticker_overrides`を参照していなかったための誤検知
- (b)部分取りこぼしのうち保持窓で説明できない14件は**全てBBAI**
  （11フィールドで一律`raw_within_6yr=11→l3_count=7`）だったため、
  当初「銘柄固有の構造的異常、原因未特定」と報告したが、**これも誤り**
  だった。`[[LAYER3-ANNUAL-MISCLASSIFICATION-BBAI-1]]`
  （2026-08-06完了・BACKLOG_DONE.md参照）が`_reclassify_misannotated_
  fy_entries()`をBBAI限定（`_ANNUAL_MISCLASSIFICATION_FIX_TICKERS =
  frozenset({"BBAI"})`）で既に実装済みであり、中間期のYTD比較開示が
  誤ってis_annual=Trueに混入する既知パターンを正しく除外した**結果**
  だった。当初の実測スクリプトはこの後処理を呼び出しておらず
  `_classify_period()`単体の結果と比較したための誤検知

**訂正の結論**: 年次側は`ticker_overrides`未考慮・既存修正の後処理
未再現という**2つの計測方法の誤り**により偽陽性を報告していた。
これらを補正した結果、**年次側で確認された未解決の取りこぼしは0件**。
`SEC_EDGAR_LAYER_DESIGN.md`のフォールバック不在に関する記載なしという
指摘自体は事実として残るが、期間分類ロジックそのものに未知の欠陥は
確認されなかった。

#### 四半期側 範囲実測結果（2026-08-19②、新規）
TAILの実消費経路（`get_quarterly_series`/`get_latest_quarterly`）は
四半期データを読むため、年次側だけでの「実害ゼロ」は消費経路を測らず
安全宣言することになるとの指摘を受け、四半期側も同一100銘柄×32
フィールドで実測した（`_QUARTERLY_YEARS=5`、末尾のend日ベースで
Layer3側の最終エントリ集合と比較）。

| 状態 | 件数 |
|---|---|
| (a) 元データなし | 881 |
| (b) 正常 | 2,189 |
| (b) 部分取りこぼし | 41 |
| (c) 完全取りこぼし | 89 |

- (c) 89件のうち83件は5年保持窓で説明可能。残り6件のうち2件
  （`APP capital_expenditure`・`MSFT depreciation_and_amortization`）
  は年次側と同じ`ticker_overrides`除外設定で説明できる。
  **残る4件が現時点で唯一の確認された欠陥**:
  `ALAB buyback`・`CRWV buyback`・`CWAN buyback`・
  `FICO finance_lease_payments`（5年窓内に生データがあるのにLayer3が
  0件、`ticker_overrides`にも該当なし、原因未特定）
- 「Layer3の実エントリ末尾end日が、5年窓内の生データend日集合と
  一致しない」という粗い指標（`genuine_gap`）では442件が該当したが、
  **この数値は信頼性が低いと判断し、確定した欠陥件数としては扱わない**。
  理由: 同じ粗い指標で年次側は当初32件・14件（BBAI）を「真の異常」と
  誤検知しており、四半期側でも`_merge_candidate_entries()`の候補間
  優先度マージ・`_is_plausible_standalone_quarter`等のプルーニングを
  本実測では再現できていないため、同型の誤検知が442件の大半を占めて
  いる可能性が高い。442件を欠陥として扱う前に、これらの内部ロジックを
  踏まえた再測定が必要（本項目のスコープ外、着手時に再実施すること）

#### 実害判定（TAIL消費経路そのものを実測、2026-08-19②）
TAILが実際に消費する5フィールド（revenue/operating_income/
stock_based_compensation/net_income/shares_diluted）×保有10銘柄
（ADBE/APGE/APP/CELH/CRWV/NVDA/PLTR/SOFI/SOUN/TSLA）の50セルを
四半期データで個別確認した。

- **APGEは`get_tanuki_tickers()`に含まれておらず**（tanuki=false）、
  当初の100銘柄スキャンから漏れていた。`build_ticker_store('APGE')`を
  個別実行し確認
- 欠落2件: `APGE revenue`（0件）・`SOFI operating_income`（0件）。
  **いずれも(a)元データなし**——APGEはcompany_facts.jsonにrevenue系
  タグが1件も存在しない（臨床段階バイオ、実際に無収益と推測）。SOFIが
  `OperatingIncomeLoss`を報告しないことは`[[OPERATING-INCOME-
  EXTRACTION-GAP-1]]`で既に確認済みの事実と整合。**取りこぼし(c)では
  ない**
- `CELH stock_based_compensation`のgap=1は2026-08-19③で追加調査した。
  欠落しているend日は**`2021-09-30`（1件のみ）**——CELHの生データでは
  この期がQ3 2021のYTD開示（10-Q、`is_ytd=True`）だが、`_ytd_to_
  quarterly()`が単一四半期額へ差分するために必要なQ1/Q2 2021の同一
  YTDチェーン先行エントリが、`_QUARTERLY_YEARS=5`の保持窓カットオフ
  （実測時点基準で`cutoff_q≈2021-08-20`）の外側にあるため存在しない。
  結果としてこのYTDエントリは差分元を持たない「孤立エントリ」となり、
  `_ytd_to_quarterly()`内で`unresolved`リストへ追加される経路を通る
  （`_normalize_field_entries()`が`all_quarterly.extend(unresolved)`で
  再結合する箇所まではコード追跡で確認）。**ただし、この`unresolved`
  エントリが最終的に`build_ticker_store()`の出力へ現れない具体的な
  分岐点までは特定できなかった**——推測で断定せず「原因未特定」として
  記録する。実害は`get_latest_quarterly(store, 'stock_based_
  compensation')`で個別確認済みで、TAILが実際に消費する最新エントリは
  `end=2026-03-31, val=7,626,000`であり、2021-09-30の欠落はTAILの
  `sbc_quarterly`出力に**影響しない**（優先度低のまま据え置き、対応
  不要）
- 残り48セルは全て正常一致

**消費側の欠損時挙動（i/ii/iii判定）**: `tail_dcf_bridge.py`・
`quarterly_review_generator.py`とも
```python
if rev and oi and rev.get("val"):
    result["operating_margin"] = round(oi["val"] / rev["val"], 4)
if sbc:
    result["sbc_quarterly"] = sbc["val"]
if ni and sd and sd.get("val"):
    result["eps_diluted"] = round(ni["val"] / sd["val"], 4)
```
**(ii) 欠損として明示的に除外される**（対応するresultキー自体が
出力されない、クラッシュなし）。**(iii)の0/既定値への暗黙置換は
確認されなかった**。ただし`rev.get("val")`・`sd.get("val")`は
truthy評価されており、収益・希薄化株式数が正当に`0`となる四半期が
将来発生した場合、そこだけ`operating_margin`/`eps_diluted`が欠損扱い
される軽微なfalsy-zeroリスクが理論上残る（実データでは現状該当なし、
優先度低）。

#### parser.py↔Layer3の2経路乖離（2026-08-19②、事実の登録のみ）
`[[OPERATING-INCOME-EXTRACTION-GAP-1]]`本線1でparser.py側に
`operating_income`のGP法/pretax法再構成を実装したが、`layer3_builder.py`
側には同等のフォールバックがない。同一`company_facts.json`から同一概念
を取る2経路のうち、片方だけ再構成されている非対称な状態。

実数（100銘柄）: **Layer3年次`operating_income`が0件の4銘柄
（JNJ・KLAC・LLY・XOM）は、4/4ともparser.py側の`annual_YYYY.json`には
`operating_income`が入っている**（JNJ: $25.596B `reconstructed_gp`・
KLAC: $5.014B `reconstructed_gp`・LLY: $29.696B `reconstructed_gp`・
XOM: $41.871B `reconstructed_pretax`）。実装（Layer3側への再構成移植）
は別途判断、本項目では事実の登録のみ。

#### 対応方針
- 四半期側の4件（ALAB/CRWV/CWAN buyback、FICO finance_lease_payments）
  は原因未特定のまま優先度低で保留可（TAIL非消費フィールドのため実害
  なし）
- 442件の粗いgenuine_gap指標は、`_merge_candidate_entries()`内部の
  候補優先度マージ・プルーニングロジックを実測に組み込んだ上での
  再測定が必要（未着手）
- parser.py↔Layer3の2経路乖離への対応要否は別途判断

#### 関連
- `[[OI-RECONSTRUCTION-MISSING-OPEX-LINES-1]]`（本問題の発見元、
  GP法/pretax法フォールバック不在の課題とは別種）
- `[[OPERATING-INCOME-EXTRACTION-GAP-1]]`（BACKLOG_DONE.md、parser.py側
  の再構成実装元。Layer3側との2経路乖離の一方の当事者）
- `[[LAYER3-ANNUAL-MISCLASSIFICATION-BBAI-1]]`（BACKLOG_DONE.md、
  2026-08-19②の実測でBBAIパターンの真因と判明した既存完了項目）
- `[[LAYER3-FALLBACK-STALE-TAG-PRIORITY-1]]`（BACKLOG_DONE.md、Layer3の
  別の既知問題〈古いタグ優先バグ〉。本問題とは異なる原因）

#### 着手条件
なし（優先度低のため急ぎ不要）

---

### [TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1] kpi_proposer.pyのcore限定ゲートは撤廃済み — ただしKPI値の取得自体が別の理由でブロックされていることが判明
**優先度:** 中（core限定ゲート自体は解消済みだが、値取得のブロックに
よりKPIデータ欠如という実害は未解消のまま）
**分類:** 運用ギャップ / TAIL自動化パイプライン / ゲート撤廃は完了・
値取得の課題は継続
**登録日:** 2026-08-19③
**更新日:** 2026-08-19④（core限定ゲート撤廃を実装・検証。ただし
KPI値取得が別途ブロックされていることを新たに発見、下記参照）
**発見:** `[[TAIL-COVERAGE-POLICY-UNDECIDED-1]]`（BACKLOG_DONE.md、TAIL
監視対象の全保有ポジション拡大）の完了後、`kpi_proposer.py`のcore限定
ゲートを判定調査した結果

#### 内容
`kpi_proposer.py::propose_kpis()`（298-302行目）は`thesis.get("type")
!= "core"`でsatelliteを早期returnし、KPI提案生成（Grok呼び出し→
`kpi_proposals/{ticker}_proposal.json`→`config/tail_kpi_map.json`への
`auto_fetchable=true`分の自動登録）を行わない。四半期レビュー生成は
`[[TAIL-COVERAGE-POLICY-UNDECIDED-1]]`で全保有ポジションに拡大したが、
KPI提案生成はcore限定のままであり、**satelliteはレビューは出るがKPI
提案が出ない非対称な状態**になっている。

#### 判定1: core限定である技術的な理由があるか
**ある。`build_kpi_prompt()`（138-154行目）は`thesis.get('thesis',
'未設定')`・`thesis.get('exit_guide', '未設定')`という、coreスキーマ
専用のフィールド名を直接読んでいる。** これは
`[[TAIL-COVERAGE-POLICY-UNDECIDED-1]]`実装時に
`quarterly_review_generator.py`で発見・修正したのと**全く同じ型の
スキーマ不整合バグ**である。satelliteのthesisファイルは
`strategy_name`/`entry_condition`/`exit_condition`/`holding_period`と
いう別スキーマのため、これらのキーは存在せず、修正なしにゲートだけを
外すと`thesis`/`exit_guide`が両方とも「未設定」としてGrokに渡り、
`quarterly_review_generator.py`で実際に発生したのと同じ内容破綻
（テーゼ未設定という誤った前提でのKPI提案生成）が再発する。**現状の
core限定ゲートは、このスキーマ不整合バグを偶然マスクしている状態**
であり、恣意的な制限ではなく現時点で必要な安全装置になっている。

#### 判定2: satelliteに広げた場合、何が必要になるか
`quarterly_review_generator.py`に実装した`thesis_narrative_fields()`
（2026-08-19④に`src/tail/thesis_utils.py`へ抽出・共通化、下記「実装
状況」参照）と同様の、type別スキーマ正規化ヘルパーを`kpi_proposer.py`
側にも実装し、`build_kpi_prompt()`内の`thesis.get('thesis', ...)`・
`thesis.get('exit_guide', ...)`の2箇所を正規化後の値に差し替える必要が
ある。修正自体の規模は小さい（`quarterly_review_generator.py`での実装
実績あり）が、ゲートを外すだけでは不可。

#### 判定3: 広げなかった場合、レビューの品質にどう影響するか
**実測で確認済みの構造的な影響がある。** `[[TAIL-COVERAGE-POLICY-
UNDECIDED-1]]`実装時に実際に生成したsatellite 7銘柄
（ADBE/APGE/NVDA/APP/CELH/SOUN/CRWV全て）のレビューの
`summary`・`concerns`を確認したところ、**全銘柄で共通して「KPIデータが
一切提供されておらず（欠如しており）テーゼの方向性を検証できない」旨の
文言が出現**しており、Grokがこれをhealth_score算定上の重大な不確実性
要因として毎回明示的に評価へ組み込んでいることを確認した。原因は
`kpi_proposer.py`がcore限定のため`config/tail_kpi_map.json`に
satelliteのKPIが1件も登録されておらず、`xbrl_segment_fetcher.py`・
`text_kpi_extractor.py`（layer2/layer3のKPI取得、いずれもcore/
satellite区別なくpendingキューのtickerを処理する設計）が取得対象を
持たないため。加えて`TANUKI_TAIL_KPI_Update.yml`（週次KPI更新）も
`config/tail_kpi_map.json`のキーをticker一覧としているため、satellite
は自動的にこの対象からも外れている。**KPI提案が無いレビューは
「定量的な裏付けを欠いた定性評価のみ」になっており、これは今回の
監視対象拡大が半分（レビュー生成）しか完了していないことを意味する。**

#### 対応方針(a)の実装状況（2026-08-19④、方針判断不要と判断され実装）
本項目の判定1〜3が「方針判断を要さない技術的対応」と判断されたため、
(a)が実装された。

- `_thesis_narrative_fields()`は複製せず、`src/tail/thesis_utils.py`
  （新設）へ抽出・共通化し、`quarterly_review_generator.py`・
  `kpi_proposer.py`の両方から`thesis_narrative_fields()`としてimport
  する形にした（`quarterly_review_generator.py`は`common.sec_data.
  layer3_builder`という重量な依存を持つため、`kpi_proposer.py`が
  そちらから直接importすると不要な結合が生じる。共通化先を新規の
  軽量モジュールにすることでこれを回避した）
- `build_kpi_prompt()`の`thesis.get('thesis', ...)`・
  `thesis.get('exit_guide', ...)`を`thesis_narrative_fields()`の
  戻り値に差し替えた
- `propose_kpis()`のcore限定ゲートを撤廃した
- NVDA単独で先行検証: 生成されたKPI提案（データセンター売上成長率・
  データセンター粗利益率等）は投資テーゼ（「AI産業の成長期待」）と
  明確に噛み合った内容であり、「未設定」を前提とした汎用提案には
  なっていないことを確認。残り6銘柄（ADBE/APGE/APP/CELH/SOUN/CRWV）
  も実行し、いずれも銘柄固有の妥当なKPI提案（例: APGEは臨床試験進捗、
  APPは広告ROAS等）を確認。`config/tail_kpi_map.json`への
  `auto_fetchable=true`分の自動登録も7銘柄全てで確認済み

#### 新たに発見された未解決の問題（2026-08-19④、値の取得がブロックされている）
**KPI提案の生成・登録until成功したが、その値を実際に取得することが
できないことが判明した。** `xbrl_segment_fetcher.py`（layer2、XBRL
タグベース抽出）をsatellite 7銘柄全てで実行した結果、**提案された
KPIの実測値が1件も取得できなかった**（全て「取得失敗」）。

原因を追跡した結果、2つの要因を確認:

1. **`xbrl_segment_fetcher.py`の構造的な設計上の制約**:
   `parse_contexts()`（223-252行目）は指定ディメンション軸の
   `explicitMember`を持つコンテキストのみを`ctx_map`に格納し、
   セグメント区分のない会社全体の事実（`xbrl_dimension`が空の
   ファクト）は**構造的に一切取得できない**（該当するコンテキストが
   `ctx_map`に存在しないため）。Grokが提案するKPIの多くは
   `xbrl_dimension: null`（例: 「総売上高成長率」等の会社全体指標）
   であり、これらは**銘柄に関わらず**この設計上の制約に該当する。
   これは今回新たに作られた問題ではなく、既存のcore銘柄（PLTR）でも
   同型の失敗（6件中3件が非セグメント指標で「取得失敗」）が実際に
   発生していることを実測で確認した——satellite拡大以前から存在した
   既知の制約が、KPI提案対象がsatelliteに広がったことで顕在化した形
2. **Grokが生成する`xbrl_member`名の精度**: セグメント指標（
   `xbrl_dimension`あり）についても失敗が発生した。NVDAの
   「ゲーミング売上成長率」（`xbrl_member: "nvda:GamingMember"`）を
   例に実際のXBRLファイルを直接検査したところ、NVDAの実際のセグメント
   タグは`nvda:GraphicsSegmentMember`であり、Grokが生成した
   `xbrl_member`名は実際のXBRLタグ付け慣行と一致していなかった
   （実測確認、推測ではない）

`text_kpi_extractor.py`（layer3、MD&Aテキスト抽出）もNVDAで実行した
ところ、手動抽出対象2件（AI関連顧客数推移・次世代GPU受注残高）とも
「未発見」となり値を取得できなかった。

**結論: KPI提案の生成・登録という入口は今回のセッションで解消したが、
値を実際に取得して四半期レビューへ反映する出口が別途ブロックされて
おり、`[[TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1]]`が目指した「KPIデータ
欠如を理由とする減点の解消」自体はまだ達成されていない。** 対応方針
・優先度は別途判断（本項目のスコープを超える別種の課題のため、
新規登録を検討）。

#### 関連
- `[[TAIL-COVERAGE-POLICY-UNDECIDED-1]]`（BACKLOG_DONE.md、同型の
  スキーマ不整合バグを`quarterly_review_generator.py`側で発見・修正
  した項目。`thesis_narrative_fields()`の実装元）

#### 着手条件
方針判断を要する部分（本項目のcore限定ゲート撤廃）は実装済み・完了。
残る「KPIの値が取得できない」問題は、対応方針の検討が必要（別項目化を
含め判断すること）。

---

### [TAIL-XBRL-SEGMENT-FETCHER-NONDIMENSIONED-GAP-1] xbrl_segment_fetcher.pyが非セグメント指標（会社全体のKPI）を構造的に取得できない — Layer3経由取得の自動振替を実装、satellite実取得38件へ改善（構造的制約自体は未解消）
**優先度:** 高→**中**（2026-08-19⑨、機械的なLayer3振替を実装した
結果、実務上の実害〈satelliteのKPI欠落〉はほぼ解消。
`xbrl_segment_fetcher.py`自体の非ディメンション取得不可という構造的
制約そのものは未解消のまま残るが、Layer3という代替経路で実質的に
迂回できているため優先度を引き下げ）
**分類:** バグ / TAIL自動化パイプライン / 設計上の制約・サイレント
フォールバック → 代替経路（Layer3）で実務上は迂回
**登録日:** 2026-08-19④
**更新日:** 2026-08-19⑤（Step 1: coreの既存失敗範囲を確定〈いつから・
どの程度AI評価に混入していたか・なぜ沈黙していたか〉。Step 2: Layer3
経由での代替取得可否をKPI単位で判定）→ 2026-08-19⑨（却下KPIをLayer3
経由へ機械的に振り分ける仕組みを実装。satellite全体で却下26件中24件を
解決、実取得成功KPIは14件→38件に増加。下記「Step 3」参照）
**発見:** `[[TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1]]`のsatellite対応実装後、
Step 3（KPI値の実際の取得確認）でsatellite 7銘柄のKPI提案値が1件も
取得できなかったことの原因調査

#### 内容
`xbrl_segment_fetcher.py::parse_contexts()`（223-252行目）は指定
ディメンション軸の`explicitMember`を持つコンテキストのみを`ctx_map`
へ格納する設計であり、セグメント区分の無い会社全体の事実
（`xbrl_dimension`が空のファクト）は**構造的に一切取得できない**
（該当コンテキストが`ctx_map`に存在しないため`_try("")`が常に空集合を
返す）。

`kpi_proposer.py`（Grok）が提案するKPIの多くは会社全体の成長率・比率
（例: 「総売上高成長率」「営業利益率」）であり`xbrl_dimension: null`。
これらは銘柄に関わらずこの制約に該当する。**satellite 7銘柄で提案
された合計約38件のKPIのうち、実際に値が取得できたものは0件**
（`xbrl_segment_fetcher.py --ticker NVDA ADBE APGE APP CELH SOUN CRWV`
を実行し全件「取得失敗」を確認）。

**既存のcore銘柄（PLTR）でも同型の失敗が実際に発生していることを実測
確認済み**——PLTRの登録済み6KPIのうち、セグメント指標
（Commercial売上・Government売上・貢献利益率）3件は取得成功、非
セグメント指標（営業利益率・株式報酬費用・希薄化後EPS成長率）3件は
「取得失敗」。**これは今回新たに作られた問題ではなく、satellite拡大
以前から存在していた既存の制約が、KPI提案対象の拡大によって顕在化
した**（satellite拡大前はcoreのKPI提案しか存在せず、非セグメント指標
の失敗が「一部のKPIだけ取れない」程度の目立たない状態だったが、
satelliteのKPI提案はGrokが会社全体指標を多く提案する傾向があり、
100%失敗という形で問題が可視化された）。

副次的な要因として、セグメント指標であってもGrokが生成する
`xbrl_member`名が実際のXBRLタグ付け慣行と一致しない場合がある
（実測確認: NVDA「ゲーミング売上成長率」の`xbrl_member: "nvda:
GamingMember"`は誤りで、実際のXBRLタグは`nvda:
GraphicsSegmentMember`）。ただしこれは構造的制約とは別の、個別の
タグ精度の問題。

#### Step 1: coreの既存失敗の範囲確定（2026-08-19⑤）

**1-1 core 3銘柄の取得成功・失敗内訳（実測）**

| ticker | 成功 | 失敗 | 失敗KPI |
|---|---|---|---|
| PLTR | 3/6 | 3/6 | 営業利益率・株式報酬費用・希薄化後EPS成長率（いずれも`dimension=''`） |
| SOFI | 3/7 | 4/7 | Technology Platform売上成長率・正味貸倒率（NCO）・純金利マージン（NIM）・GAAP純利益（`dimension`が空、または非空でも失敗） |
| TSLA | 6/6 | 0/6 | なし（登録済み6件全てセグメント指標で成功） |

TSLAが0失敗なのは、登録済み6KPIが全て`dimension`が空でない
（セグメント指標として設計されている）ため。PLTR・SOFIの失敗KPIは
`dimension=''`（非セグメント・会社全体指標）が中心だが、SOFIは
`dimension`が設定されているKPI（Technology Platform売上成長率・
正味貸倒率）も失敗しており、これはStep 3のxbrl_member精度問題（下記
`[[TAIL-XBRL-MEMBER-VALIDATION-GAP-1]]`参照）が原因。

**1-2 いつから失敗しているか（`docs/portfolio/tail/data/kpi/{ticker}_
layer2.json`のgit履歴を追跡）**

`TANUKI_TAIL_KPI_Update.yml`が週次でこのファイルを更新・コミットして
おり、2026-06-06の初回セットアップ時点ではPLTRは3KPI（Commercial売上・
Government売上・貢献利益率）のみ登録・全件成功（`missing_kpis: []`）
だった。**2026-06-08の次回更新で、営業利益率・株式報酬費用・希薄化後
EPS成長率の3KPIが新規追加され、この時点から`missing_kpis`に3件とも
記録されている。** 以降、2026-06-15・06-22・…・08-17（直近の週次更新）
まで**全ての履歴で同じ3件が変わらず失敗し続けている**（SOFIも同様の
パターンを2026-06-08から08-17まで確認）。**「一度も取れたことがない」
——途中から取れなくなったのではなく、これらのKPIが登録された最初の
取得試行から一貫して失敗している。** 2026-06-08から本調査日
（2026-08-19）まで約72日間（10週間強）、週次実行の度に同じ失敗が
サイレントに繰り返されていた。

**1-3 過去のcoreレビュー（各9件、計27件）へのKPI不足言及の実測**

`summary`・`concerns`テキストを正規表現で走査した結果（「未取得」を
含む表現で再検索、初回の狭い正規表現では0件ヒットだったが「未取得」
という言い回しを見落としていたため広げて再実施——本セッション自身が
このタイミングで一度検証手法の誤りを起こしかけた）:

| ticker | KPI不足言及あり | 全体 |
|---|---|---|
| PLTR | 7 | 9 |
| SOFI | 4 | 9 |
| TSLA | 4 | 9 |
| **合計** | **15** | **27** |

**core 3銘柄のレビューのうち15/27件（56%）が、satelliteで発見された
のと同種の「KPIデータが不足している」旨の言及を伴ったまま生成されて
いた。** 例（PLTR 2026Q2）: 「NDR・チャーン・SBC・EPSなど核心KPIが
未取得で健全度評価が不完全」。TSLAの言及例は必ずしも本問題（`xbrl_
segment_fetcher.py`の非セグメント指標取得失敗）に限らず、`text_kpi_
extractor.py`側（layer3、手動KPI）の未取得も混在している可能性がある
（例: TSLA 2026Q1「FSD・Optimusの進捗データは依然未取得」は手動KPIの
話であり本問題とは別経路）——**15件全てが本問題に単一起因すると断定は
しない**が、KPI不足という結果自体は実測の通り。

**1-4 失敗が沈黙していた理由**

`xbrl_segment_fetcher.py::fetch_ticker()`は`missing_kpis`が存在しても
**常に`True`を返す**（`False`を返すのはCIK取得失敗・10-Q取得失敗の
場合のみ）。`main()`最後の完了サマリーは`{'✓' if ok else '✗'}`という
表示のため、**KPIが部分的に取得失敗していても`✓ PLTR`と表示される**
（実測確認: `ok=True`が返るため）。非ゼロ終了コードも存在しない。
`missing_kpis`自体は`{ticker}_layer2.json`の`missing_kpis`フィールドに
記録され、`quarterly_review_generator.py`がこれを`layer2_missing_kpis`
としてレビューJSONへ転記するのみで、`print`はコンソール（CI生ログ）に
`missing_kpis: [...]`が出るが、これを消費・検知する仕組み（`report_
consistency_check.py`・`audit.py`等のNG/WARNチェック）はどこにも
存在しない（`missing_kpis`を`grep`した結果、参照元は`xbrl_segment_
fetcher.py`〈書き込み〉と`quarterly_review_generator.py`〈転記〉のみ）。

**これは本日の一連の調査で繰り返し発見してきたサイレント・フォール
バックと同型である。** CI（`TANUKI_TAIL_KPI_Update.yml`）は毎週GREEN
（成功）で完走し続け、失敗の唯一の可視化経路は「AIがレビュー本文の
中で自発的に『未取得』と書く」ことだけであり、これを系統的に集計する
仕組みが存在しなかったため、本調査（Step 1-3の実測）まで15/27件という
実数は誰にも把握されていなかった。

#### Step 2: Layer3経由での代替取得可否（2026-08-19⑤、実装しない）

現在「取得失敗」となっている全KPI（core 7件＋satellite約33件、合計
40件）を、Layer3（`config/sec_concept_definitions.json`の32フィールド）
で代替できるかを判定した。

| 区分 | 件数 | 内容 |
|---|---|---|
| (A) Layer3の既存フィールドで直接まかなえる | 6 | SOFI GAAP純利益（`net_income`）・PLTR株式報酬費用（`stock_based_compensation`）・APGE現金及び現金等価物残高（`cash_and_equivalents`）・APGE研究開発費（`research_and_development`）・APGE営業活動によるキャッシュフロー（`operating_cash_flow`）・CELH営業キャッシュフロー（`operating_cash_flow`） |
| (B) Layer3フィールドの組み合わせ・計算でまかなえる | 15 | PLTR営業利益率（`operating_income/revenue`）・PLTR希薄化後EPS成長率（`eps_diluted`系列のYoY）・NVDA総売上高成長率（`revenue`系列）・NVDA研究開発費対売上比率（`research_and_development/revenue`）・ADBE売上高成長率・ADBE営業利益率・ADBEフリーキャッシュフロー（`operating_cash_flow - capital_expenditure`）・APP総売上成長率・CELH売上高成長率・CELH株主資本成長率（`stockholders_equity`系列）・CELH粗利益率（`gross_profit/revenue`）・SOUN総売上高成長率・CRWV総売上高成長率・CRWV Gross Margin・CRWV Operating Cash Flow成長率 |
| (C) Layer3にも無く、セグメント分解が必要 | 17 | SOFI Technology Platform売上成長率・SOFI正味貸倒率（NCO）・SOFI純金利マージン（NIM）・NVDAデータセンター売上成長率／粗利益率・NVDAゲーミング売上成長率・ADBEデジタルメディア売上成長率・ADBEサブスクリプション売上比率・APGE一般管理費（Layer3は`selling_general_and_administrative`〈SG&A合算〉と`selling_and_marketing`は別途あるが、両者の差分がG&A単体と一致する保証はなく確度が低いため(C)に分類）・APP広告売上成長率／アプリ売上成長率・CELH北米売上成長率／国際売上成長率・SOUN自動車向け売上成長率／レストランIoT売上成長率・CRWV Commercial売上成長率／Government売上成長率 |
| (D) そもそもXBRLに無い（非GAAP・テキストのみ） | 2 | APP Adjusted EBITDAマージン（非GAAP調整後指標）・SOUN ARR（年間経常収益、SaaS非GAAP指標） |

**(A)+(B)＝21件（52.5%）がLayer3経由で解決可能。(C)+(D)＝19件
（47.5%）はセグメント分解またはテキスト抽出が引き続き必要。** つまり
「Layer3に回せば半分は解決するが、残り半分はセグメント区分自体を
`xbrl_segment_fetcher.py`側で解決する必要が残る」というのが実数に
基づく答えであり、Layer3への切り替えだけでは全解決しない。

**Layer3経由に回す場合の技術的な障害（2026-08-19⑤）**: `config/
tail_kpi_map.json`のスキーマ（`kpi_name`/`change_risk`/`tag_history`/
`fallback_tags`/`fallback_action`/`revenue_tag`/`dimension`）には
**取得元（XBRL直接 vs Layer3）を指定する仕組みが存在しない**
（`layer2_name`フィールドは既存の別KPIエントリとの重複排除用の別
概念であり、取得元の切り替えとは無関係）。追加が必要なもの: (i)
`"source": "layer3"`＋直接参照する`"layer3_field"`（(A)の場合）または
計算式を表す`"layer3_formula"`（(B)の場合、例:
`"operating_income/revenue"`）の新フィールド、(ii) それを読んで
`build_ticker_store()`/`get_quarterly_series()`から値を取得し既存の
`{ticker}_layer2.json`スキーマへ書き込む新規フェッチャー（または
`xbrl_segment_fetcher.py`の拡張）。振り分けの判断主体は2案:
`kpi_proposer.py`のプロンプト側でGrokに32フィールドのリストを提示し
判断させる（実装は単純だが、Step 3で判明したGrokのタグ名精度問題と
同型のリスク——検証していないAI判断への依存）か、取得側で機械的に
判定する（Grokの提案結果からKPI名・revenue_tagを既知の32フィールド
名・エイリアスと機械的に照合し、一致すれば自動でLayer3経路に振り分け
る。Grokの判断に依存しない分、確実性が高い）。実装はしない。

#### Step 3: 対応方針(d)の実装（2026-08-19⑨、Layer3経由取得の自動振替）

`tail_kpi_map.json`に`"source": "layer3"`＋`"layer3_field"`（直接参照）
／`"layer3_formula"`（`"a/b"`形式の除算のみ対応）を追加（既存エントリは
`source`キー無し＝従来通りXBRL直接取得のまま後方互換）。
`xbrl_segment_fetcher.py::fetch_layer3_kpis()`が`build_ticker_store()`/
`get_quarterly_series()`から値を取得し、既存の`{ticker}_layer2.json`
スキーマへ書き込む（消費側は無変更）。**`layer3_formula`で分母が
0またはNoneの四半期はその四半期のエントリ自体を作らずスキップする**
（falsy-zeroを作らない設計、実装済みだが今回の実測では実際に分母が
0/Noneになるケースは発生していない）。

**振り分けの判断主体は取得側の機械的照合**（`kpi_proposer.py::
route_rejected_to_layer3()`）とした——`config/sec_concept_definitions.
json`の`fields[*].candidates`（Layer3ビルダー自身が使う唯一の正の
タグ一覧）から`xbrl_tag`のローカル名を逆引きするだけで、Grokに
「これはLayer3から取れる」と判断させていない（今日tag名をGrokに
生成させて失敗したのと同型のリスクを避けるため）。**名前が一致する
だけでは登録しない**——`build_ticker_store()`を実際に呼び、対象
ティッカーにそのLayer3フィールドの実データが存在するか
（`get_latest_quarterly()`が非Noneを返すか）も確認してから登録する
（事例5の原則）。

**実測結果（satellite 7銘柄全体）**: 却下26件中**24件がLayer3経由で
解決**（実データ確認済み）。残る2件は`config/sec_concept_definitions.
json`の全32フィールドの候補タグを確認しても一致しなかった真の未解決:
- ADBE「研究開発費」（`xbrl_tag`は`ResearchAndDevelopmentExpense
  SoftwareExcludingAcquiredInProcessCost`というADBE固有のタグ変異形で、
  Layer3の`research_and_development`フィールドの候補リストに存在しない）
- APGE「営業費用」（`OperatingExpenses`というタグ自体に対応する
  Layer3フィールドが32フィールド中に存在しない）

`xbrl_segment_fetcher.py`を7銘柄で本番実行し、**satelliteの実取得
成功KPIは14件→38件に増加**（NVDA/ADBE/APP/CELH/SOUN/CRWVは
`layer2_complete: True`、APGEも初めて`missing_kpis: []`を達成）。
1件を手動で決算突合（Step 3-4、事例5の原則）: NVDAの`gross_profit`
（Layer3経由）を実測した結果、`common/sec_data/data/NVDA/company_
facts.json`の生タグ`GrossProfit`（period 2026-01-26〜2026-04-26）と
完全一致（$61,157,000,000）。加えてR&D $6.321B・Operating Income
$53.536Bとも内部整合（Gross Profit − R&D − SG&A ≈ Operating Income）
を確認し、値が単に取得できただけでなく妥当であることを確認した。

**総合計（core+satellite）: 実取得成功KPIは26件→50件に増加**
（core 12件〈不変〉＋satellite 38件）。

**残課題**: 今回はLayer3経由の(d)対応のみを実施し、(a)（`xbrl_
segment_fetcher.py`自体の非ディメンション取得対応）・(b)（`text_kpi_
extractor.py`への誘導）は未着手。上記のADBE・APGEの2件、および
Step 2で判定した(C)+(D)＝19件（セグメント分解・非GAAP指標、Layer3にも
存在しない）は`xbrl_segment_fetcher.py`自体の構造的制約が残る限り
未解決のまま。ただし今回のkpi_proposer.py側の実測（Grokが提案する
セグメント指標の大半がLayer3で解決可能な会社全体指標だったという
実態）により、(C)+(D)として当初分類した19件のうち実際に必要となる
ものは限定的である可能性が高い。

#### 関連
- `[[TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1]]`（本問題の発見元。KPI提案の
  生成・登録という入口は解消したが、本問題により値取得という出口が
  ブロックされたまま）
- `[[TAIL-XBRL-MEMBER-VALIDATION-GAP-1]]`（Grokが生成する`xbrl_member`
  名の精度問題を切り出した新規項目、2026-08-19⑤）
- `[[LAYER3-ANNUAL-CLASSIFICATION-DROPS-DATA-1]]`（Layer3側のデータ
  存在確認の実測元。TAILの5フィールド消費経路確認から派生）
- `config/tail_kpi_fetch_baseline.json`（rejected_countをLayer3振替後の
  実測値〈satellite残り2件〉へ引き下げ更新済み、2026-08-19⑨）

#### 着手条件（残課題、2026-08-19⑨時点）
(d)は実装済み。残る(a)〈xbrl_segment_fetcher.py自体の非ディメンション
取得対応〉・(b)〈text_kpi_extractor.pyへの誘導〉は、ADBE・APGEの
2件および構造的制約が残る非セグメント指標について、着手要否・優先度を
ユーザーに確認してから着手すること（実務上の実害はLayer3経由でほぼ
解消済みのため、急ぎ性は低い）。

---

### ✅ [TAIL-XBRL-MEMBER-VALIDATION-GAP-1] kpi_proposer.pyがGrok生成のタグ名を検証せず登録していた問題 — 登録前の実取得検証方式への切り替えで解消（satellite 0件→14件）
**状態:** 完了（2026-08-19⑦。「タグ一覧を提示して選ばせる」方式では
値取得0件のままだったが、「登録前に本番の取得経路で実際に値が取れる
か試し、取れたものだけ登録する」方式〈事例5の原則をKPI登録に適用〉に
切り替えた結果、satelliteで実際に値が取れるKPIが0件→14件に増加した
ことを`xbrl_segment_fetcher.py`本番実行で実測確認）
**優先度:** 中→解消（satelliteの取得失敗は0件、coreは既存KPI未変更の
ため従来通り一部残存——`[[TAIL-XBRL-SEGMENT-FETCHER-NONDIMENSIONED-
GAP-1]]`として別途管理）
**分類:** バグ / TAIL自動化パイプライン / 未検証AI出力への依存 → 解消
**登録日:** 2026-08-19⑤
**更新日:** 2026-08-19⑥（対応方針(a)を実装〈実XBRLタグに基づくKPI
提案への切り替え〉。NVDAで実測検証したところdimension/member一致率は
100%に改善したが、実際のKPI値取得は0/6のまま改善せず。原因はxbrl_tag
〈概念〉自体の精度という別の問題と判明。**一致率の改善を成果として
記録せず、値が取れていないという事実の方を記録し未完了のまま残した**）
→ 2026-08-19⑦（登録前の実取得検証方式に切り替え、satelliteで14件の
実取得成功を確認。完了として処理）
**発見:** `[[TAIL-XBRL-SEGMENT-FETCHER-NONDIMENSIONED-GAP-1]]`調査中に
NVDA「ゲーミング売上成長率」の`xbrl_member: "nvda:GamingMember"`が
実際のXBRLタグ`nvda:GraphicsSegmentMember`と一致しないことを発見。
単発事象か系統的な問題かを確認するための追加調査

#### 内容
`kpi_proposer.py`はGrokに`xbrl_tag`/`xbrl_dimension`/`xbrl_member`を
提案させ、`_update_kpi_map()`（258行目以降）はこれを**実際のXBRL
ファイルと一切照合せず**そのまま`config/tail_kpi_map.json`へ登録する。
Grokは学習データに基づく「もっともらしい」タグ名を生成するのみで、
対象銘柄の実際の提出書類を検証していない。

**セグメント指標として提案された全22件の`xbrl_member`を、実際の直近
10-Q XBRLファイルと照合した結果、一致は7/22件（32%）。**

| ticker | KPI名 | 提案されたxbrl_member | 実XBRLとの一致 |
|---|---|---|---|
| NVDA | データセンター売上成長率 | nvda:DataCenterMember | ✓一致 |
| NVDA | データセンター粗利益率 | nvda:DataCenterMember | ✓一致 |
| NVDA | ゲーミング売上成長率 | nvda:GamingMember | ✗不一致（正: GraphicsSegmentMember） |
| ADBE | デジタルメディア売上成長率 | adbe:DigitalMediaSegmentMember | ✗不一致 |
| ADBE | サブスクリプション売上比率 | adbe:SubscriptionMember | ✗不一致 |
| APP | 広告売上成長率 | app:AdvertisingMember | ✗不一致 |
| APP | アプリ売上成長率 | app:AppsMember | ✗不一致 |
| CELH | 北米売上成長率 | celh:NorthAmericaMember | ✗不一致 |
| CELH | 国際売上成長率 | celh:InternationalMember | ✗不一致 |
| CRWV | 総売上高成長率 | crwv:ConsolidatedMember | ✗不一致 |
| CRWV | Commercial売上成長率 | crwv:CommercialSegmentMember | ✗不一致 |
| CRWV | Government売上成長率 | crwv:GovernmentSegmentMember | ✗不一致 |
| SOUN | 自動車向け売上成長率 | soun:AutomotiveSegmentMember | ✗不一致 |
| SOUN | レストラン・IoT売上成長率 | soun:RestaurantAndIoTSegmentMember | ✗不一致 |
| SOFI | Technology Platform売上成長率 | sofi:TechnologyPlatformMember | ✗不一致 |
| SOFI | 正味貸倒率（NCO） | sofi:PersonalLoansMember | ✗不一致 |
| PLTR | 米民間売上成長率 | pltr:CommercialOperatingSegmentMember | ✓一致 |
| PLTR | 政府部門売上成長率 | pltr:GovernmentOperatingSegmentMember | ✓一致 |
| TSLA | エネルギー事業粗利益率 | tsla:EnergyGenerationAndStorageMember | ✓一致 |
| TSLA | エネルギー受注残高 | tsla:EnergyGenerationAndStorageMember | ✓一致 |
| TSLA | サービス売上成長率 | tsla:ServicesAndOtherMember | ✓一致 |
| TSLA | 自動車売上総利益率 | tsla:AutomotiveMember | ✗不一致 |

**注目すべき内訳の偏り**: PLTR・TSLAの登録済みKPI（初期セットアップ時
に登録された既存KPI、2026-06-06〜の`tail_kpi_map.json`に元から存在）
は5/8件（62.5%）が一致するのに対し、**今回のセッションでGrokに
一括生成させたsatellite銘柄の新規提案は2/14件（14%）しか一致しない**
（NVDAのDataCenterMember 2件のみ）。この差は、初期セットアップ時の
登録がより慎重に（人手による確認を伴って）行われていた可能性を示唆
し、逆に言えば**Grokの一括生成だけに頼ると一致率がさらに下がる**
ことを示す実測結果。

**「Grokが正しいタグ名を知っている」という前提のまま登録される設計
であり、これ自体が検証していない前提に基づく仕組みになっている。**

#### 対応方針(a)の実装（2026-08-19⑥、方針判断不要と判断され実装）
`kpi_proposer.py::build_kpi_prompt()`に、直近10-QのXBRLから実際の
セグメント関連タグ（dimension・memberの組）を抽出して埋め込み、
「一覧に無い名称を記憶や推測で生成しないこと」という指示を追加した。
抽出には`xbrl_segment_fetcher.py::parse_contexts()`のロジックを再利用
した新規関数`extract_segment_members()`を使用（新規のパース処理は
書き起こしていない）。`update_tail_kpi_map()`にも登録時の照合を追加し、
実タグ一覧に存在しない`(dimension, member)`は**登録せず、却下した
ことを`[kpi_map] 却下（実XBRLに存在しないタグ）`として必ず表示する**
（黙って捨てない）。

#### NVDAでの実測検証結果（2026-08-19⑥）
**変更前**: セグメント指標3件中2件一致（`nvda:GamingMember`が不一致、
正しくは`nvda:GraphicsSegmentMember`）。

**変更後**: NVDAの既存5KPI（全て取得失敗だったため、satelliteの
既存KPIは上書き可という判断のもとクリアして再提案）を再生成した結果、
**セグメント指標5件全て（データセンター売上高・Compute & Networking
セグメント売上高・中国売上高・Hyperscale売上高・AI Clouds Industrial
Enterprise売上高）が実XBRLのdimension/memberと完全一致（5/5＝
100%）、却下0件**。特筆すべき点として、NVDAの実際のXBRLは
`DataCenterMember`を`us-gaap:StatementBusinessSegmentsAxis`ではなく
`srt:ProductOrServiceAxis`という**別のディメンション軸**で報告して
おり、Grokが以前`xbrl_dimension: "us-gaap:StatementBusinessSegmentsAxis"`
と誤って組み合わせていたために、たとえ`DataCenterMember`という
member名自体は文字列として一致していても実際には取得できない
（ディメンション不一致で`ctx_map`に該当コンテキストが存在しない）
状態だったことが判明した——**「member名の一致」だけでなく「dimension
との正しい組み合わせ」が必要**という、当初の検証手法（member名の
単純一致確認のみ）では見えていなかった追加の精度要件。新方式は
dimension・memberを常にペアで実データから提示するため、この種の
不一致も構造的に防止する。

**しかし、値取得（`xbrl_segment_fetcher.py`実行）は0/6のまま改善
しなかった。** 原因を追跡した結果、**dimension/memberが完全に正しい
場合でも、`xbrl_tag`（概念そのもの）が実際に使われているタグと異なる
と値は取得できない**ことが判明した。NVDAの「データセンター売上高」
（dimension/member一致）は`xbrl_tag: "us-gaap:
RevenueFromContractWithCustomerExcludingAssessedTax"`で提案されたが、
実際にそのコンテキストで使われているタグは`us-gaap:Revenues`
（実XBRLを直接確認して特定、推測ではない）だった。**Step 3の対応は
dimension・memberの精度は解決したが、xbrl_tag自体の精度という
別の問題は範囲外だった**——同じ「Grokが記憶から生成し、実データと
照合していない」という型の問題が、tagにも独立して存在する。

**指示（「改善しなかった場合はそのまま報告し、仮説に合わせて結論を
作らない」）に従い、残り6銘柄への展開は行っていない。** NVDAの
`config/tail_kpi_map.json`エントリは実測後に元の5件（変更前と同じ、
いずれも取得失敗）へ差し戻した——新旧どちらも値が取得できない点で
差がなく、検証用の一時的な登録を製品データとして残す理由がないため。

当時は「本項目は完了としない」と明記し、一致率の改善（100%）を成果
として書かず、値が取得できていないという事実の方を記録した
（2026-08-19⑥時点の判断、下記で覆った）。

#### 方式転換: 登録前の実取得検証（2026-08-19⑦、対応方針を実装）
タグ・member一覧の提示だけでは、個々のタグ・memberが実在してもその
**組み合わせのファクトが存在するとは限らない**ため、個別の存在照合
では不十分と判断し、方式そのものを変更した。**登録前に本番の取得経路
（`xbrl_segment_fetcher.py::parse_and_extract()`をそのまま呼ぶ、検証
専用の簡易版は書き起こさない）で実際に値が取れるか試し、取れたものだけ
登録する**——事例5の原則（部分の代理判定ではなく本番の入口から出口
まで通す）をKPI登録そのものに適用した。新設`validate_kpis_fetchable()`
が直近1四半期分のXBRLに対して本番の抽出関数を実行し、値が取れなかった
KPIは**登録せず、却下理由（tag不在／member不在／組み合わせ不在／
非セグメント指標の構造的制約／検証不能）を必ず表示**する。却下記録は
`kpi_proposals/{ticker}_proposal.json`の`rejected_kpis`にも残す
（黙って捨てない）。全KPIが却下された銘柄は`tail_kpi_map.json`に
`[]`を明示的に書き込み、「未処理」と「0件」を区別できるようにした。

合わせて、`xbrl_tag`自体の精度問題にも対応した——`company_facts.json`
（新規取得なし、ローカル既存ファイル）から直近2年以内に出現した
us-gaap概念一覧（NVDA: 626件中279件に絞り込み、絞り込み基準は表示
済み）を`build_kpi_prompt()`に埋め込み、「一覧の中からのみ`xbrl_tag`
を選ぶこと」と指示した。

#### 実測結果（2026-08-19⑦、satellite 7銘柄すべてで実施）
NVDA単独で先行検証した後、satellite残り6銘柄（ADBE/APGE/APP/CELH/
SOUN/CRWV）も実行。core 3銘柄（PLTR/SOFI/TSLA）の既存KPIは上書きせず
現状維持。

| ticker | 提案数 | 検証通過 | 却下 | 実取得成功（本番xbrl_segment_fetcher.py実行で確認） |
|---|---|---|---|---|
| NVDA | 6 | 3 | 3 | 3/3（100%） |
| ADBE | 6 | 3 | 3 | 3/3（100%） |
| APGE | 5 | 0 | 4※ | 0/0（登録0件） |
| APP  | 6 | 2 | 4 | 2/2（100%） |
| CELH | 6 | 1 | 5 | 1/1（100%） |
| SOUN | 6 | 3 | 3 | 3/3（100%） |
| CRWV | 6 | 2 | 4 | 2/2（100%） |

※APGEは提案5件のうち1件が元々`auto_fetchable=false`（手動KPI）で
検証対象外、残り4件全て却下。

却下理由の内訳（satellite全体、22件): 非セグメント指標（構造的制約、
`[[TAIL-XBRL-SEGMENT-FETCHER-NONDIMENSIONED-GAP-1]]`該当）が大半、
CELHの「機能性エナジードリンク売上」・APPの「継続営業利益」の2件は
「組み合わせ不在（tag・memberは個別に実在するが該当ファクトなし）」。

**satellite合計: 登録14件、実取得成功14件（登録された分は100%成功）。**
`xbrl_segment_fetcher.py`を7銘柄で本番実行し、NVDA/ADBE/APP/CELH/
SOUN/CRWVは全て`layer2_complete: True`・`missing_kpis: []`を確認。
**変更前（本項目の登録時点）はcore 12件・satellite 0件だったのに対し、
変更後はcore 12件（不変）・satellite 14件、合計26件が実際に値を
取得できるKPIとなった。**

検証中に、`config/cik_lookup.csv`のCRWV行のみCIKが10桁ゼロ埋めされて
いない（`"1769628"`）ため`get_10q_filings()`が404で失敗する問題も
発見・修正した（`load_cik()`側で`.zfill(10)`により正規化。CSV全105行
を確認し未パディングはCRWV 1件のみと確認済み、CSV自体は変更していない）。

#### 関連
- `[[TAIL-XBRL-SEGMENT-FETCHER-NONDIMENSIONED-GAP-1]]`（本問題の発見元。
  非セグメント指標の構造的な取得不可は本項目の対応後も残存、却下理由
  として引き続き検知される）
- `config/tail_kpi_fetch_baseline.json`（satellite分をbaseline引き下げ
  で更新済み、2026-08-19⑦）

---

### [TAIL-SATELLITE-MONITOR-CORE-APPLICABILITY-1] satellite_monitor.pyの4条件をcore 3銘柄へ適用できるかの技術調査（調査のみ、実装なし）
**優先度:** 低（現状維持でも実害はない。core側の高頻度監視が無いことは
事実だが、四半期レビューによる評価は別途機能している）
**分類:** 運用ギャップ / TAIL自動化パイプライン / 技術調査
**登録日:** 2026-08-19④
**発見:** `[[TAIL-SATELLITE-POSITION-MONITORING-GAP-1]]`・
`[[TAIL-COVERAGE-POLICY-UNDECIDED-1]]`のSYSTEM_MAP.md記録時に発見した
「core 3銘柄はsatellite_monitor.pyの対象外＝価格変動・エグジット条件・
テーゼ否定ニュースの継続監視を一切受けていない」という非対称の技術的
検証

#### 内容
`satellite_monitor.py`は`positions_index.json`の`type=="satellite"`を
直接フィルタする独立システムで、4条件（①価格変動±20%、②エグジット
条件の数値目標到達、③Grokによるテーゼ否定ニュース検知、④決算接近）を
Discord通知する。core（PLTR/SOFI/TSLA）は対象外であり、同等の監視を
提供する別システムは存在しない（`.github/workflows/`の全TAIL関連
ワークフローを確認、該当なし）。4条件それぞれについて、core 3銘柄の
実際のthesisデータに対して技術的に適用可能かを実測で判定した。

#### 判定結果（4条件それぞれ）

**①価格変動±20%: そのまま適用可**
core 3銘柄はいずれも`entry_price: null`（`thesis.json`）だが、
`monitor_ticker()`は`pos.get("entry_price") or avg_costs.get(ticker)`
という、`portfolio.json`の加重平均取得単価へのフォールバックを既に
実装している。このフォールバック自体はcore/satelliteのスキーマに
依存しないため、そのまま機能する（同様のフォールバックは
`quarterly_review_generator.py`でも既に使われている既存パターン）。

**②エグジット条件の数値目標到達: 適用不可（そのままでは）**
`_extract_numeric_exit()`（正規表現による「$XXX到達」「X倍」等の短い
定型文からの数値抽出）を、core 3銘柄の実際の`exit_guide`テキストに
対して実行した結果、**3銘柄とも`None`（抽出不可）を実測確認**。
core 3銘柄の`exit_guide`は数千文字規模の構造化された長文エッセイ
（複数の「壊れる条件」シナリオ・監視指標を段落形式で記述）であり、
satelliteの短い`exit_condition`（例:「割安感がなくなって利が乗ったら
売り切る」）とは形式が根本的に異なる。

加えて、`monitor_ticker()`自体（376行目）が`pos.get("exit_condition",
"（条件未設定）")`という**satellite専用のフィールド名**を直接読んで
おり、修正なしにcoreへ適用すると`exit_cond`が常に「（条件未設定）」に
なる——これは本セッションで3回目に発見した同型のスキーマ不整合
（`quarterly_review_generator.py`・`kpi_proposer.py`ではsatellite側が
「未設定」になっていたが、今度は逆方向にcore側が「未設定」になる）。

代替案（実装はしない）: (i) Grokによる定性判定（`exit_guide`の長文を
渡し、現在の決算・株価状況が「壊れる条件」に近づいているかをAIに判断
させる、正規表現による数値抽出とは別の方式）、(ii) 将来的な数値目標
フィールドの新設（thesisに`exit_price_target`等を追加）。

**③テーゼ否定ニュース検知: 要改修**
`_call_grok_news()`自体はstrategy_name・exit_condition文字列を
プロンプトへ埋め込むだけの汎用的な実装で、機構的にはcoreのテキストを
渡しても動作する。ただし②と同じ理由（`monitor_ticker()`が
`exit_condition`という satellite専用フィールドを直接読む）で、
修正なしでは「（条件未設定）」がプロンプトに渡ってしまう。今回新設した
`thesis_narrative_fields()`（`src/tail/thesis_utils.py`）を
`satellite_monitor.py`側でも使うよう改修すれば、`exit_guide`を正しく
読めるようになり解消可能。`strategy_name`はcoreに存在しないフィールド
のため空文字のままになるが、プロンプト自体は成立する。

**④決算接近: そのまま適用可**
`rss_state.json`にcore 3銘柄のエントリが実際に存在することを確認
（PLTR/SOFI/TSLAとも`last_filed`等が記録済み）。`_check_earnings_
approach()`を実際に呼び出し、3銘柄とも次回決算予想日を正しく計算
できることを実測確認（例: PLTR推定2026-11-02・74日後、現時点では
2週間以内の閾値に達していないため`triggered=False`）。

#### 通知頻度への影響
現状`satellite_monitor.py`は平日2回（JST 08:00・17:00）×satellite
7銘柄＝1日あたり最大14回の`monitor_ticker()`呼び出し。core 3銘柄を
追加した場合、1日あたり最大20回（+43%、週あたり+30回）に増加する。
Grok Web検索（条件③）・Discord通知の呼び出し回数もこれに比例して
増加する。

#### 対応方針
未定（本項目では技術調査の記録のみ、実装しない）。着手する場合は
最低限②③の改修（`thesis_narrative_fields()`の`satellite_monitor.py`
への導入、②は代替案の選定）が前提となる。

#### 関連
- `[[TAIL-SATELLITE-POSITION-MONITORING-GAP-1]]`・
  `[[TAIL-COVERAGE-POLICY-UNDECIDED-1]]`（BACKLOG_DONE.md、逆方向の
  同型の非対称〈satelliteがレビュー生成から漏れていた〉を発見・是正
  した項目）
- `SYSTEM_MAP.md`「TANUKI TAIL」節（本調査の要点を記録済み）

#### 着手条件
ユーザーに、core 3銘柄へsatellite_monitor.pyの監視を広げるべきかの
投資方針判断を確認してから着手すること。

---

### [OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1] 標準OCFタグ不在時にContinuing/Discontinued分割タグを拾えずoperating_cash_flowが構造的に欠落する（25銘柄該当）
**優先度:** 高（登録時）→中（実害確認調査の結果、緊急性は低いと判明）
**分類:** バグ / 確定・候補タグ設計欠陥
**登録日:** 2026-08-02
**訂正日:** 2026-08-02（実害確認調査結果を反映）
**発見:** [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]根本原因調査から
派生した横断スキャン（チャット記録）

#### 内容
標準タグ`NetCashProvidedByUsedInOperatingActivities`が存在せず、
`ContinuingOperations`分割タグ（および一部で`DiscontinuedOperations`
分割タグ）のみが存在する年度で、`operating_cash_flow`が構造的に欠落する。
105銘柄スキャンで**25銘柄該当**（AAPL/ABBV/AVAV/BKNG/CAKE/CAT/CELH/CIX/
CPRT/ELF/FICO/HEI/HON/LRCX/MRVL/MSFT/ONDS/PAYS/RCAT/RMBS/SCCO/SNPS/TER/
TSLA/XOM）。

2つのサブパターン:
- **パターンA（大多数）**: 非継続事業タグが一切存在せず、
  `ContinuingOperations`タグがそのまま企業全体のOCF。候補タグリストへの
  追加のみで解決可能（[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]と
  同型の低リスク）
- **パターンB（少数、RCAT/HON/AVAV）**: 非継続事業タグが存在し真の合算が
  必要な可能性。合算時は必ず「営業活動限定タグ」（`CashProvidedByUsedIn
  OperatingActivitiesDiscontinuedOperations`、範囲の広い
  `NetCashProvidedByUsedInDiscontinuedOperations`ではなく）を選択する
  ガードが必須（RCATでは投資・財務活動の非継続事業CFが偶然$0のため実害
  なしだったが、他銘柄では非営業CFの混入という設計トラップになりうる
  ことを確認済み）

#### 実害確認結果（2026-08-02、チャット記録）
25銘柄すべての`get_annual_range(ticker, 5)`（直近5ファイル）を実測した
結果、`operating_cash_flow=None`が現在の直近5年窓に含まれるのは
**RCATのみ**（2024・2025年）。**残り24銘柄（AAPL/MSFT/TSLA/XOM/CAT/ABBV
等を含む）は該当年度がすべて2011〜2017年頃の古い年度であり、現在の直近
5年窓（2021〜2026年）の外**にあるため、実害なしと確定した。将来的に
該当年度が直近5年窓に入る銘柄は原理的に存在しない（過去の固定年度の
ため）。優先度を「高→中」に訂正する理由: 現在進行形の実害が確定した
のはRCATのみで、それは[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]として個別に
切り出したため。

RCAT単独の実害は[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：高）として
独立登録した。

#### 影響
現在進行形の実害はRCAT以外に確認されていない。候補タグ追加という低
リスク修正自体は、将来のデータ品質向上（過去年度の`operating_cash_flow`
充足）として引き続き価値がある。

#### 対応方針
未定。実害の緊急性は低いため、パターンA（候補タグ追加）・パターンB
（ガード付き合算）の実装設計・全母集団シミュレーションは優先度中として
着手する。

#### 着手条件
なし。優先度中（過去年度のデータ品質向上、現在進行形の実害はRCAT分を
除き確認されていない）。

---

### [STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1] STONKS SILOのYoY計算がfpラベルの完全一致のみで照合し期間長の妥当性チェックを持たない
**優先度:** 低〜中
**分類:** データ品質 / 設計改善
**登録日:** 2026-08-02
**発見:** [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]対応方針確定調査（チャット記録）

#### 内容
STONKS SILOのYoY計算（`financial_trend_calculator.py::_calc_yoy_change()`）
がfpラベル（Q1〜Q4）の完全一致のみでYoY照合しており、期間長の妥当性
チェックを持たない。RCATの決算期変更移行期（2024年）で、8ヶ月しか離れて
いない新旧"Q4"を誤って比較し歪んだYoYシグナル（`change_pct=-152.2%`）を
生成していた実例が確認済み（現在はデータ蓄積により自然解消済み）。
[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]の対応方針（fetcher.py側）とは
完全に独立した問題であり、fetcher.py側の対応の有無に関わらず必要な改善
（STONKS SILOのYoY計算は`quarterly_normalized.json`という別パイプライン
を参照するため）。

#### 影響
現時点で実害はない（自然解消済み）。決算期変更を経た他銘柄でも将来
同様の問題が起こりうる。

#### 対応方針
未定。「同fp・かつ期間長〜365日程度（許容誤差込み）」という追加の妥当性
チェックを`_calc_yoy_change()`に導入することを検討する。決算期変更を経た
他銘柄でも将来同様の問題が起こりうるため、ticker非依存の一般的な改善
として設計する。

#### 着手条件
なし。優先度低〜中（現状は自然解消済みで緊急性なし、将来の決算期変更
銘柄への予防的対応）。

---

### [LITE-COGS-DA-TAG-UNMERGED-1] LITEのcost_of_revenueがCOGS由来の償却費タグを合算しておらずgross_profitが過大評価される
**優先度:** 低〜中
**分類:** データ品質 / タグ拡張で解消可能な構造的ギャップ
**登録日:** 2026-08-02
**発見:** [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]個別調査
（チャット記録）

#### 内容
LITE（2024年他、9年持続: 2015-2016・2019-2025）で、`cost_of_revenue`が
`CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization`
（$1,023.8M、現在採用中）のみを拾い、COGS由来の償却費
`CostOfGoodsAndServicesSoldAmortization`（$83.9M、未採用）が候補タグに
含まれていない。SCCOと類似の「D&A分離型」構造だが、SCCOと異なりタグの
合算拡張で原理的に解消可能。

#### 影響
LITE単独、9年間持続。gross_profit自体はown-dataの正しい値を維持している
ため、`gross_profit`自体への実害はない。`cost_of_revenue`フィールド単体
を参照する消費者がいる場合、過小評価（$83.9M程度、年度により変動）の
影響を受ける可能性がある。

#### 対応方針
未定。`cost_of_revenue`のXBRL_MAPPINGに
`CostOfGoodsAndServicesSoldAmortization`型タグの合算を追加するか検討
する。他銘柄への影響範囲（全母集団シミュレーション）を踏まえて判断する。

#### 着手条件
なし。優先度低〜中。

---

### [DCF-RELIABILITY-LABEL-MISMATCH-1] DCF_Reliability非LOW表示語彙の不一致（HIGH/NORMAL）
**優先度:** 中
**分類:** 表示不整合 / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ8（依頼文名指し）

#### 内容
`_calc_dcf_reliability_policy_b()`は常に`"LOW"`/`"NORMAL"`のいずれかを
返す一貫した関数だが、report.txtの表示文言はどちらの文脈で呼ばれたかに
よって異なる。FCF_Base方式の分岐でPolicy Bが`"NORMAL"`を返した場合は
`"DCF_Reliability: HIGH"`（`pipeline.py:1571`）、FCF_Conversion_Rate方式の
分岐で同じ`"NORMAL"`を返した場合は`"DCF_Reliability: NORMAL"`
（`pipeline.py:1667`）と表示される。report.txtを横断的にパースする外部
ツールが「非LOW側」を単純な2値として扱おうとすると正規化が必要になる。

#### 対応方針
report.txt生成コードの表示文言を「LOWの対義語」として統一する
（`HIGH`/`NORMAL`のどちらかに揃える）。

#### 着手条件
なし

---

### [STONKS-PILLAR-THRESHOLD-MISMATCH-1] pillarColor(70/45)とDEFICIT判定(65/35)の閾値不一致
**優先度:** 中
**分類:** 表示不整合 / STONKS SILO
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ8（AS-IS-141、依頼文名指し）

#### 内容
`index.html`の`pillarColor(s)`は`s>=70`緑・`s>=45`amber・それ未満赤だが、
同じスコア値に対する`verdict`ラベル（AS-IS-141）は`>=65→GOOD_DEFICIT`・
`>=35→WATCH`・それ未満`BAD_DEFICIT`で決まる。スコア65〜69点の銘柄は
verdict="GOOD_DEFICIT"（好意的ラベル）なのに表示色はamber、スコア35〜44点
の銘柄はverdict="WATCH"なのに表示色は赤、という不整合区間が存在する。

#### 対応方針
`pillarColor()`の閾値をverdict判定と同じ65/35に揃えるか、意図的に別基準
とする理由を明示するかを判断する。

#### 着手条件
なし

---

### [BETA-FALLBACK-DESIGN-GAPS-1] β取得の3経路重複・0/負値無条件フォールバック・許容範囲の2基準並存
**優先度:** 中
**分類:** 設計不整合 / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ6（AS-IS-013）・`OUTPUT_ITEMS_INVENTORY.md`「β（3経路：日次/月次/監査トリガー時）」

#### 内容
`beta_fetcher.py::calc_capped_beta()`は生βが`None`かどうかのみをチェックし、
`0`や負値であっても`max(0.3,min(2.5,raw_beta))`で無条件に0.3へフロアされ
`beta_config.json`に書き込まれる。警告フラグは一切付与されない。さらに
実行時の`data_fetcher.py::_determine_beta()`は`beta_config.json`のoverride
を最優先かつ無条件に採用するため、`_determine_beta()`自身が持つ「yfinance
直接値は0.1〜3.0の範囲内のみ採用」という健全性チェックが一切適用されない。
加えて`beta_fetcher.py`の許容範囲（0.3〜2.5）と`_determine_beta()`の
直接値許容範囲（0.1〜3.0）が異なる2つの基準として並存している。β取得
自体も日次/月次/監査トリガー時の3経路が重複している。

#### 対応方針
①生βが0/負値だった場合に警告フラグを付与する②`beta_config.json`の
overrideにも健全性チェックを適用する③許容範囲の基準を1つに統一する
④3経路の重複を整理する、の優先順位を検討してから着手する。

#### 着手条件
なし

---

### [RPO-REVTTM-GATE-SKIP-1] RPO補正のrev_ttm未提供時に比率安全弁がスキップされる
**優先度:** 中
**分類:** バグ / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ6（AS-IS-024）

#### 内容
`adjust_rpo()`の比率条件ゲート（`adjustments.py:525`
`if not via_whitelist and rev_ttm is not None and rev_ttm > 0`）は、
`rev_ttm`が`None`の場合ゲート自体を素通りする。`rpo_incremental`の計算は
`rpo_yago`と`rev_yoy`さえあれば`rev_ttm`なしでも非ゼロ値を返せるため、
「`rpo_yago`/`rev_yoy`は取得できたが`rev_ttm`だけがNone」という組み合わせ
では、RPO/Revenue比率が閾値（30%）未満でもRPO補正が適用されてしまう
可能性がある。

#### 対応方針
`rev_ttm is None`の場合の代替チェック（例: 直近年次revenueで代用する等）
を設計してから実装する。

#### 着手条件
なし

---

（[[DISCOVER-CONFIG-DUAL-MGMT-1]]は2026-08-15実装完了、BACKLOG_DONE.md
「2026-08-15（完了）」参照）

---

### [DISCOVER-UTCJST-DATE-MISMATCH-1] UTC/JST日付不整合によるmacro_themes.generated_atのズレ
**優先度:** 中
**分類:** バグ / Discover
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ7（依頼文名指し）

#### 内容
`collect.py:249`の`today = date.today().isoformat()`はタイムゾーン非対応
の素の日付（GitHub Actionsランナーの実行環境時刻、実質UTC）を使うのに
対し、同じcollect.pyの他の箇所は明示的にJST変換している。collect.pyは
「毎日JST 7:00」に実行される設計だが、JST 7:00は同日UTCではまだ前日22:00
であり、`date.today()`はJSTの実行日より1日古い日付を返す。この結果
`macro_themes[].generated_at`は同じレポート内の`daily_report.json.
generated_at`より1日古い値になりうる。`catalyst.py`の同種の`date.today()`
使用はUTC変換で日付を跨がないため実害が生じにくいが、同様にタイムゾーン
非対応である点は同一の設計リスクとして残る。

#### 対応方針
`collect.py:249`を他の箇所と同様に`datetime.now(JST)`ベースに統一する。
`catalyst.py`側も将来のスケジュール変更に備えて同様に統一しておくことを
推奨する。

#### 着手条件
なし

---

### [FEARGREED-DUPKEY-BUG-1] fear_greed.previous_close/one_week_agoの重複キーバグ
**優先度:** 中
**分類:** バグ / Market Pulse
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ10（AS-IS-346/347）

#### 内容
`collect_and_send.py:1458-1459`で`fear_greed.previous_close`と
`fear_greed.one_week_ago`が両方とも`history.get("1w")`という同一のキーを
参照しており、常に同じ値になる。「前日終値」を意図しているなら本来
`history.get("1d")`等の別キーを参照すべきところ、コピペミスの可能性が
高い。

#### 対応方針
`previous_close`が本来参照すべきキー（CNN `fear_greed`パッケージの
`history`辞書の実際のキー構成を確認の上）に修正する。

#### 着手条件
なし

---

### [SECDATA-STORAGE-FRAGMENTATION-1] common/sec_data内のraw/normalized/ttm3系統並存によるスキーマ分岐
**優先度:** 中
**分類:** アーキテクチャ / データ品質
**登録日:** 2026-07-23
**発見:** `INPUT_DATA_AS_IS.md`2-A（一次データ層AS-IS調査）

#### 内容
`common/sec_data/`配下は`data/{TICKER}/annual_*.json・quarterly_*.json`に
加え、`raw/`（正規化前の生XBRL）・`normalized/`（別スキーマの独立した
正規化四半期データ）・`ttm/`（TTM系列）という最低6ファイル系統に分岐して
いる。`normalized/`はstock.html直接fetchに加え、reader.py共通アクセサ
経由で最低5系統（TANUKI VALUATION本体のNet Debt計算・
financial_trend_calculator.py〈STONKS SILO〉・
quarterly_review_generator.py〈TANUKI TAIL〉・tail_dcf_bridge.py
〈TANUKI TAIL DCF〉・hypecore.py〈HypeCore〉）が本番で依存している
（GATE2-PHASE3B-1で意図的に共通化された経緯あり）。廃止・統合時は
これら5系統全ての移行が必要。

なお、[[DOCS-SECDATA-NORMALIZED-DIR-STALE-1]]・
[[NORMALIZER-YTD-METADATA-STALE-1]]は、本タスクの統合設計時に
合わせて解消すべき関連課題として発見されている。

#### 対応方針
`SEC_EDGAR_LAYER_DESIGN.md`フェーズD（Layer3統合、5消費者の優先順位
確定済み: ①TANUKI VALUATION本体 ②STONKS SILO ③TANUKI TAIL
④HypeCore ⑤stock.htmlフロントエンド）を正とする（2026-08-06投資調査で
確定、下記「2計画併存の経緯」参照）。`normalized/`のCapEx符号不統一は
[[CAPEX-SIGN-UNNORMALIZED-1]]（2026-07-24対応完了、BACKLOG_DONE.md
参照）で解消済みのため、統合スキーマ側は正規化済みCapExを前提に
設計できる。

**進捗（2026-08-07更新・フェーズD最終状況）**:

- Step2-1〜2-4（①TANUKI VALUATION本体・②STONKS SILO主要部
  〈`financial_trend_calculator.py`のみ〉・③TANUKI TAIL・
  ④HypeCore）: **完了**（完了記録は`[[SEC-EDGAR-LAYER-DESIGN-PHASE-D-
  STEP2-1]]`〜`[[SEC-EDGAR-LAYER-DESIGN-PHASE-D-STEP2-4]]`参照）
- Step2-5（⑤stock.htmlフロントエンド＋診断・補助スクリプト7件）:
  **実質完了**（2026-08-07投資調査の結果、9系統中Layer3切替の実質
  対象は`dcf_validity_checker.py::check_c_data_jump()`のみと判明、
  他8系統は死蔵コード・書き込み専用・既にLayer3経由・アーキテクチャ上
  切替不可のいずれかで切替対象自体が存在しなかった）
- 保留中だった2判断（`fetcher.py`選択思想・stock.html公開パイプライン）:
  **いずれも現状維持を選択、着手見送りが確定**（`[[LAYER3-FETCHER-
  SELECTION-PHILOSOPHY-MISMATCH-1]]`案2採用・`[[STOCKHTML-LAYER3-
  PUBLISH-PIPELINE-MISSING-1]]`着手見送り、いずれも2026-08-07確定）

**フェーズE（`normalized/`廃止）は着手不可**: 上記の通り、
`fetcher.py`・`dcf_validity_checker.py`（いずれも`data/annual_*.json`
依存を意図的に継続）・stock.html（`normalized/`直接依存、Layer3公開
パイプライン未整備のため切替不可）が意図的に現状維持のまま残るため、
`normalized/`を完全に廃止することはできない。**`normalized/`はこの
3系統向けに存続し続ける設計とする**（フェーズDの目標だった「全消費者
Layer3統一」は、この3系統を恒久的な例外として除いた形で達成とみなす）。

**次セッション着手順序**: フェーズD（`common/sec_data`統合スキーマ
移行）は実質完了。次の一次データ層プロジェクトの優先タスクは、
新DB構築プロジェクトの他フェーズ（`PROJECT_STATUS.md`フェーズ1記載の
`common/market_data/`・`common/macro_data/`新設）へ移行することを
検討する。

**Step1完了（2026-08-05、全消費者洗い出し・読み取り専用調査）**:
`raw/`（実消費者ゼロのデッドコード）・`normalized/`（5本番消費者、
pipeline.py内部は最低5用途に細分化）・`ttm/`（独立パイプライン、
`[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]`参照）・EPS Analyzer/TANUKI TAIL
独自アクセス経路（EPS Analyzer1系統・TANUKI TAIL3系統＋RSS監視）の
全消費者を実ファイルで確認済み。`[[SCHEMA-NORMALIZED-ISSUES-1]]`①
（STDebt網羅性）を実測再確認した結果、AAPL/XOM/Vいずれもnormalized側
STDebtが完全に0件（既存記載より悪化）と確認。詳細はチャット記録参照。

**raw/削除完了（2026-08-05実装）**: 全消費者ゼロと確認済みの`raw/`を
撤去した（`quarterly.py`の書込処理削除・既存105ファイル削除・
`SEC_Data_Update.yml`のgit add対象からも除去）。詳細はBACKLOG_DONE.md
参照。

**残タスクは`SEC_EDGAR_LAYER_DESIGN.md`フェーズDの実装**（TANUKI
VALUATION本体を最優先に、5消費者＋診断・補助スクリプト7件を
Layer3〈`layer3_builder.py::build_ticker_store()`〉経由へ順次切替）。
`data/quarterly_{FYQ}.json`のpl/cf/shares区分SA/YTD修正（コミット
939b8f57f、2026-08-05）は、フェーズD完了までの暫定的な正確性向上
として意味を持つ。フェーズD完了後の`normalized/`廃止（フェーズE）が
実施されれば5消費者はLayer3のみに依存するようになり、data/系統向け
アクセサの新規実装は不要になる見込み（Layer3側`get_field_entries()`が
`get_quarterly_series()`相当の既存アクセサとして既に実装済みであると
2026-08-06投資調査で確認済み）。

**2計画併存の経緯（2026-08-06投資調査で判明）**: 本エントリ（登録日
2026-07-23）と`SEC_EDGAR_LAYER_DESIGN.md`（作成日2026-07-24）は、
`INPUT_DATA_AS_IS.md`・`INPUT_DATA_TOBE.md`という同一の調査を起点に
1日違いで分岐した。`SEC_EDGAR_LAYER_DESIGN.md`は本エントリの
「対応方針」欄（`INPUT_DATA_TOBE.md`2-Aが設計した単一正規化ストアへの
統合）を詳細設計として具体化したものと位置づけられるが、本エントリの
「対応方針」欄は2026-08-05まで`SEC_EDGAR_LAYER_DESIGN.md`への
クロスリンクを持たないまま更新され続け、5消費者の移行先を独自に
「normalized/→data/統合」と記述していた。2026-08-02〜03の
`[[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]`調査で「両者は`SEC_EDGAR_LAYER_
DESIGN.md`が既に『3スキーマ併存』として認識済みの既知課題の一部」と
一度確定していたにも関わらず、その2日後（2026-08-05）に本エントリの
ロードマップ（0-A〜0-C）が独立して実行され、フェーズDとの整合確認は
行われなかった。両エントリとも技術的に誤ってはいなかったが、移行先
（Layer3 vs data/）という最も重要な点で1ヶ月弱食い違ったまま別々に
進行していた。原因は、担当セッションが参照した一次ドキュメントが
異なっていたためと推測される（本エントリ自身が`SEC_EDGAR_LAYER_
DESIGN.md`への参照を持たなかったため、本エントリの「次セッションでの
着手順序」欄だけを見て着手すると、フェーズD側の決定事項に辿り着けない
構造だった）。再発防止策はCHAT_RULES.md「文書横断整合性チェック」
（2026-08-06追加）参照。

**新DB構築プロジェクト最終確認（2026-08-15）**: `FIELD_DEFINITIONS.md`
499項目単位での新DB参照切替状況を集計する投資調査を完了。SEC EDGAR
由来4件（AS-IS-129・266・273・395）はいずれも意図的にフェーズD
（Layer3統合）の対象外と確定済みで、記載も現状と一致することを確認
（AS-IS-129は`[[LAYER3-FETCHER-SELECTION-PHILOSOPHY-MISMATCH-1]]`に
よるSTONKS SILO `fetcher.py`の現状維持確定、AS-IS-266・273はEPS
Analyzerの独立ライブ取得設計、AS-IS-395はTANUKI TAILのリアルタイム
監視専用ファイルによる対象外）。既に確認済みのyfinance/FRED由来18件
（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`・`[[MACRODATA-LAYER-
CONSTRUCTION-1]]`の2026-08-15付注記参照）と合わせ、**新DB構築
プロジェクト（sec_data/market_data/macro_data）は消費者ファイル単位・
重複計算パターン単位・フィールド単位の全ての粒度で完了確認済み**と
なった。

**フロントエンド横断点検（2026-08-15）**: `docs/`配下の全フロント
エンドファイル（HTML/JS、28ファイル）を対象に、`fetch()`呼び出しを
全数抽出・分類する横断点検を実施した結果、`normalized/`を直接fetch
しているのは`tanuki_valuation/stock.html`の1件のみと確認された。他に
`normalized/`を直接参照するフロントエンドファイルは存在しない
（`[[SCHEMA-NORMALIZED-ISSUES-1]]`の同日付「調査依頼文の前提訂正」は
`fetcher.py`・`dcf_validity_checker.py`・stock.htmlという既知の3系統
限定の調査であり、本点検とは対象範囲が異なる別調査。両者は結論が
一致するが、本点検は3系統に限定せずフロントエンド全ファイルを対象と
した点で独立の裏付けとなる）。

#### 着手条件
なし（着手条件だった「[[CAPEX-SIGN-UNNORMALIZED-1]]の対応方針確定」は
2026-07-24の実装完了により満たされた。raw/撤去は完了、
`SEC_EDGAR_LAYER_DESIGN.md`フェーズDの実装から再開可能）

---

### [NORMALIZER-YTD-METADATA-STALE-1] normalizer.py::_ytd_to_quarterly()変換後にstart/period_daysが変換前のYTD期間のまま残る
**優先度:** 低〜中
**分類:** データ品質
**登録日:** 2026-07-23
**発見:** common/sec_data統合投資調査（フェーズ1）⑤(B)

#### 内容
`normalizer.py::_ytd_to_quarterly()`のQ2以降エントリで、val（値）は
正しくYTD差分変換済みだが、start/period_daysが変換前のYTD期間の
まま残る（AAPL実データ: Q2 CapEx val=1,971,000,000は正しい単四半期値
だがperiod_days=181・start=2025-09-28＝会計年度開始日のまま、本来は
約90日・2025-12-28になるべき）。原因は`normalizer.py`L186の
`new_entry = dict(entry)`が元のYTDエントリをコピーするのみで、
start/period_daysを再計算していないこと（L215-218）。

#### 影響
valのみを参照するロジックには実害なし。period_daysやstartを期間長
判定・比較に使う将来のコード（または既存の未確認箇所）があれば
誤動作しうる。既知の[[CAPEX-SIGN-UNNORMALIZED-1]]（符号バグ）とは
別種の問題。

#### 対応方針
未定。start/period_daysを実際に参照している箇所の網羅調査を行って
から判断する。

#### 着手条件
なし（優先度低のため急ぎではない）

---

### [SCHEMA-NORMALIZED-ISSUES-1] normalized/スキーマ関連の構造的ギャップまとめ（STDebtタグ網羅性劣化・SM/SGA概念混同・LTDebt優先順序逆転・SharesBasic概念不一致・ファイル名annualデータ混在・DAフォールバック欠如）
**優先度:** 中〜高（内訳: 中〜高1件・低5件、個別優先度は各項目参照。
2026-08-15、①②を実害調査完了により中〜高/中→低へ引き下げ）
**分類:** データ品質 / normalized/スキーマ（common/sec_data統合スキーマ設計関連）
**登録日:** 2026-07-23〜2026-07-24（統合日: 2026-08-03）
**発見:** data/quarterly⇔normalizedフィールド網羅性比較調査・Layer2設計調査

#### 内容
`normalized/`（`quarterly.py::FIELD_CONCEPTS`由来）と`data/quarterly`
（`parser.py::XBRL_MAPPING`由来）の間で、タグ網羅性・優先順序・概念
定義が系統的に食い違っている個別事象をまとめる。いずれも
`docs/architecture/new_data_platform/SEC_EDGAR_LAYER_DESIGN.md`
（367-378行目）でLayer2/Layer3統合スキーマ設計時の解消対象として
参照されている。

① **STDebtタグ網羅性劣化**（旧SCHEMA-STDEBT-COVERAGE-GAP-1、優先度
中〜高→**実害調査完了により低（2026-08-15）**）: 短期有利子負債
（STDebt/short_term_debt）のタグ網羅性が、normalized/側
（`quarterly.py::FIELD_CONCEPTS`、単一タグ`ShortTermBorrowings`のみ・
フォールバックなし）でdata/quarterly側（`parser.py::XBRL_MAPPING`、
9タグ候補＋フォールバック）に対し著しく劣化している。10銘柄実データ
確認でAAPL 33/51件・XOM 51/51件・V 30/51件がnormalized側で**0件**と
いう深刻な乖離を示した（逆にCAT等はdata/quarterly側が0件でnormalized
側に値がある逆転ケースもあり）。

**実害調査結果（2026-08-13〜15、読み取り専用調査・チャット記録）**:
消費箇所の洗い出しを完了。TANUKI VALUATION本体の主要消費経路
（`SECReader.get_net_cash()`）は`data/annual_*.json`（parser.py層、
9タグ候補版）を参照しており、normalized/の劣化版STDebtは経由しない。
normalized/を恒久的に使い続けると決定済みの3系統（フェーズE恒久的
例外、`[[SECDATA-STORAGE-FRAGMENTATION-1]]`参照）についても個別に
確認した:
- `fetcher.py`（STONKS SILO）: `_BS_FIELDS`に`short_term_debt`単体
  フィールドは存在せず（`total_debt`のみ）、対象外
- `dcf_validity_checker.py`（診断ツール）: `common/sec_data/data/
  {TICKER}/annual_{year}.json`（parser.py層）を参照しており、
  normalized/は経由しない
- `stock.html`（TANUKI VALUATION frontend）: normalized/を直接
  fetchする唯一の系統だが、取得フィールドはCF滝グラフ用の
  `OCF`/`CapEx`/`Revenue`/`SBC`/`DA`の5つに限定され`STDebt`は対象外。
  ページ内に表示される`bsAdj.short_term_debt`は`get_net_cash()`が
  計算済みの値（parser.py層由来）のパススルー表示であり、normalized/
  の直接読み取りではない

**結論: normalized/のSTDebtタグ網羅性劣化による実害は現時点で確認
できない**（リポジトリ全体を通じてnormalized/側の劣化版STDebtを
実際に読む消費者がゼロ）。スキーマ自体の欠陥（`ShortTermBorrowings`
単一タグ・フォールバックなし）は現存するため、`common/sec_data`統合
スキーマ設計時の一括解消対象としては残す。着手条件: なし（優先度を
中〜高→低に格下げ、統合作業と同時対応で可）。

② **SM/SGA概念混同**（旧SCHEMA-SM-SGA-CONFLATION-1、優先度中→
**実害調査完了により低（2026-08-15）**）: data/quarterlyは
`selling_and_marketing`（純S&M費用）と
`selling_general_and_administrative`（SGA総額）を別フィールドとして
両方保持するが、normalized/は`SM`という単一フィールドしか持たず、
S&M単体タグが取得できない銘柄（JOBY/NVDA/CIX/ELF/KO等、
quarterly.py:236-243に明記）では`_FIELD_FALLBACKS["SM"]`経由でSGA
総額へ静かにフォールバックする。同じ`SM`値が銘柄によって「純S&M」と
「SGA総額」という異なる意味を持ちうるが、フィールド名からは判別
できない。

**実害調査結果（2026-08-13〜15、読み取り専用調査・チャット記録）**:
TANUKI VALUATION本体の`_estimate_ttm_operating_income()`
（`pipeline.py`、フェーズD Step2-1でLayer3化済み）は
`get_field_entries(store, "selling_and_marketing")`でLayer3の
`selling_and_marketing`フィールド（data/quarterly側と同型の分離
フィールド）を参照しており、normalized/の混同版`SM`は経由しない。
①と同じ3系統（fetcher.py・dcf_validity_checker.py・stock.html）も
個別に確認した:
- `fetcher.py`: `_PL_FIELDS`に`selling_and_marketing`（parser.py層の
  分離フィールド）を参照するが、normalized/の`SM`ではない
- `dcf_validity_checker.py`: SM/SGA系フィールドへの参照なし
- `stock.html`: CF滝グラフの取得フィールド（OCF/CapEx/Revenue/SBC/
  DA）に`SM`は含まれず対象外

**結論: normalized/のSM/SGA概念混同による実害は現時点で確認できない**
（リポジトリ全体を通じてnormalized/側の混同版`SM`を実際に読む消費者が
ゼロ）。スキーマ自体の欠陥は現存するため、統合スキーマ設計時の一括
解消対象としては残す。着手条件: なし（優先度を中→低に格下げ、統合
作業と同時対応で可）。

③ **LTDebt優先順序逆転**（旧SCHEMA-LTDEBT-DOUBLECOUNT-RISK-1、優先度
中〜高）: 長期有利子負債（LTDebt/long_term_debt）のprimaryタグ優先
順序が`quarterly.py::FIELD_CONCEPTS`と`parser.py::XBRL_MAPPING`の間で
逆転している。`parser.py`側は`LongTermDebtNoncurrent`を`LongTermDebt`
より優先しており、これは「`LongTermDebtCurrent`との二重計上防止」
という明示的な設計意図（BUG-NETDEBT-2対応コメントあり）に基づく。一方
`quarterly.py`側（`normalized/`生成元）は`LongTermDebt`を先に試す設定
になっており、この配慮が反映されていない。【2026-07-24検証結果】
reader.py::get_net_cash()の実装を確認した結果、二重計上が発生しうる
のは「annual側long_term_debtが0/欠損 かつ normalizedフォールバックが
非ゼロ」の場合に限られる。105銘柄全数で確認したところ該当銘柄は0件
であり、現行データでは実害が確認されなかった。ただし構造的リスクは
残るため、Layer2統合時にparser.py側の優先順序（二重計上防止済み）へ
統一することで解消する方針とする。着手条件: なし。

④ **SharesBasic概念不一致**（旧SCHEMA-SHARESBASIC-CONCEPT-MISMATCH-1、
優先度中→**実害調査完了により低**）: SharesBasic（発行済株式数関連）の
primaryタグが、2システム間で単なる順序差ではなく**意味的に異なる財務
概念**を指している。`quarterly.py`側は`CommonStockSharesOutstanding`
（貸借対照表項目・期末時点の発行済株式数）をprimaryとするのに対し、
`parser.py`側は`WeightedAverageNumberOfSharesOutstandingBasic`
（損益計算書項目・期中加重平均株式数）をprimaryとする。

**実害調査結果（2026-08-05、チャット記録・読み取りのみ）**: 消費箇所の
洗い出しを完了。**normalized/側の「SharesBasic」フィールドは、
`quarterly.py`（定義側）以外に参照するコードがリポジトリ全体でゼロ件**
（既存5本番消費者はいずれも未参照の死んだフィールドと確認）。data/側の
`shares_basic`は`reader.py::get_diluted_shares()`が
`shares_diluted<1,000,000`時のフォールバックとしてのみ参照（呼び出し元:
`data_fetcher.py`、TANUKI VALUATION）。15銘柄サンプルでnormalized側
SharesBasicが5/15銘柄（BKNG/WMT/JNJ/PEP/VZ）で0件という新たな網羅性
ギャップも確認。**結論: normalized/⇔data/間の概念不一致自体による実害は
なし**（normalized/側に消費者がいないため、normalized/→data/統合の
障害にはならない）。副次発見（ONDS/LOARのshares_basic単位スケール
異常疑い）は`[[ONDS-LOAR-SHARES-SCALE-SUSPECT-1]]`として別途登録。
着手条件: なし（優先度を中→低に格下げ、統合作業と同時対応で可）。

⑤ **ファイル名とannualデータ混在**（旧SCHEMA-NORMALIZED-ANNUAL-NAMING-
MISMATCH-1、優先度低）: `normalized/{TICKER}_quarterly_normalized.json`
はファイル名に"quarterly"と明記されているが、実際は`is_annual: true`
エントリとしてannualデータも同一ファイル内に混在保持している
（`quarterly.py::build_raw_table()`がcompany_factsから四半期・年次
両方を同一fieldsに格納するため）。現状の実害は確認されていないが、
統合スキーマ設計時にファイル名から内容を誤推測する混乱要因になり
うる。着手条件: なし。

⑥ **DAフォールバック欠如**（旧SCHEMA-DA-FALLBACK-MISSING-1、優先度
低）: `quarterly.py::FIELD_CONCEPTS`のDA（減価償却）概念はフォール
バック候補が一切設定されておらず（単一タグ
`DepreciationDepletionAndAmortization`のみ）、このタグを報告しない
銘柄（LMT等、`DepreciationAndAmortization`のみ報告）で`normalized/`側
のDAフィールドが完全に空（0エントリ）になる。①と同型のフォール
バック欠如パターン。実質的な計算消費箇所（成長率推計、
pipeline.py:2807）は`normalized/`ではなくannual/quarterly側
（parser.py由来、フォールバック4候補あり）を参照しているため、現状の
計算結果への実害はない。`normalized/`のDAはstock.htmlの単純表示にしか
使われていないため影響は限定的。着手条件: なし。

**定量実測結果（2026-08-07、`[[STOCKHTML-LAYER3-PUBLISH-PIPELINE-
MISSING-1]]`着手要否投資調査の一環）**: `normalized/`105銘柄全数を
実測した結果、**30銘柄（約29%）でDAフィールドが完全に空（0件）**と
確認。MSFT・TSLA・GOOGL・AVGOを含む主要銘柄も対象:
`ABBV, ADSK, AMD, APGE, AVGO, BBAI, CEG, COHR, CON, ENB, ESTC, GEV,
GOOGL, INTU, IONQ, KULR, LITE, LMT, LOAR, LRCX, MRVL, MSFT, RKLB,
TASK, TDY, TSLA, VZ, V, WMT, ZETA`。いずれもstock.htmlのCF滝グラフ
「SBC・D&A比率」チャートでD&A系列が欠落する（表示のみへの影響、
TANUKI VALUATION計算結果への実害は上記の通りなし）。

**調査依頼文の前提訂正（2026-08-15）**: ①②の実害調査を進める過程で、
依頼文が前提としていた「fetcher.py・dcf_validity_checker.pyは
normalized/直読み継続で確定済み」という記述を実コードで確認したところ
**誤りと判明した**。両ファイルとも実際には`common/sec_data/data/
{TICKER}/annual_*.json`（parser.py層）を参照しており、normalized/を
直接fetchするのは`[[SECDATA-STORAGE-FRAGMENTATION-1]]`が記す
フェーズE恒久的例外3系統のうち**stock.htmlのみ**（`CLAUDE_CODE_
START.md`自体の記述「`fetcher.py`・`dcf_validity_checker.py`
（`data/annual_*.json`依存継続）・stock.html（`normalized/`直接依存
継続）」が正しかった）。この訂正を経た上で3系統×2フィールド
（STDebt・SM）の実消費有無を個別に確認し、上記①②の結論に至った。

#### 対応方針
①〜⑥のいずれも、`common/sec_data`統合スキーマ（Layer2/Layer3）設計時に
`parser.py`側の定義（フォールバック網羅性・優先順序とも既に安全性検証
済み）へ統一することで一括解消する見込み。個別の緊急対応は不要。

#### 着手条件
①〜⑥いずれも個別の着手条件なし（優先度に応じて統合作業と同時対応で
可。①②は2026-08-15、実害調査完了〈実消費者ゼロ確認〉により
「common/sec_data統合スキーマ設計の確定後」という着手条件を撤廃し
優先度低へ格下げ済み）。

---

### [ONDS-LOAR-SHARES-SCALE-SUSPECT-1] ONDS/LOARのshares_diluted・shares_basicがいずれも100万未満で、get_diluted_shares()のフォールバックが救済不能な疑い
**優先度:** 中（実害の可能性はDCF計算に直結するが、規模2銘柄限定）
**分類:** バグ疑い / データ品質
**登録日:** 2026-08-05
**発見:** [[SCHEMA-NORMALIZED-ISSUES-1]]④SharesBasic実害調査の副次発見
（チャット記録）

#### 内容
`reader.py::get_diluted_shares()`のフォールバックロジック
（`shares_diluted<1,000,000`の場合に`shares_basic`を試す）が、
ONDS（shares_diluted=221,769・shares_basic=221,769、同一）・LOAR
（shares_diluted=95,893・shares_basic=93,597）の2銘柄では両方とも
100万未満のため、フォールバックが発火しても救済されず、最終的に
桁違いの小さい値がDCF計算の株式数インプットにそのまま使われている
可能性がある。`[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]`（解決済み）
と同型の単位スケール異常の疑い。

#### 着手条件
なし。次回の個別バグ対応セッションで着手可能（本線＝新DB構築
フェーズ1とは別トラック）。

---

### [SEC-SUBMISSIONS-DUAL-FETCH-1] SEC EDGAR submissions APIがfetcher.pyとedgar_rss_monitor.pyで独立に重複取得されている
**優先度:** 低〜中
**分類:** 技術的負債 / API呼び出し重複
**登録日:** 2026-07-23
**発見:** annual/segment/filing_text AS-IS構造調査（フェーズ1）④

#### 内容
SEC EDGAR submissions API（`data.sec.gov/submissions/CIK{cik}.json`）
が、`common/sec_data/fetcher.py::fetch_submissions()`（週次、全filings
一括、`submissions.json`へキャッシュ）と`src/tail/
edgar_rss_monitor.py::get_filing_period()`（平日毎日、特定accnのみ
live fetch・キャッシュなし）の2箇所で独立に叩かれている。
EPS Analyzerの独立SEC取得（前回調査⑤(A)②-3で確認済み、別課題）と
同型のパターン。

#### 影響
API呼び出しの無駄な重複。実害としては、新規提出直後は週次キャッシュ
に未反映なため、TAIL側がlive fetchで補っているという設計上の理由が
ある（鮮度ギャップの解消目的）。単純な参照統合は鮮度要件を壊す
リスクがある。

#### 対応方針
未定。edgar_rss_monitor.py側をsubmissions.json参照＋未ヒット時のみ
live fetchにフォールバックする設計への変更が有力候補だが、鮮度
ギャップの設計対応が別途必要。

#### 着手条件
なし

---

### [NAMING-CONVENTIONS-APPLY-1] NAMING_CONVENTIONS.md規則1〜5の実装への適用
**優先度:** 中
**分類:** リファクタリング / 命名規則
**登録日:** 2026-07-23
**発見:** `NAMING_CONVENTIONS.md`

#### 内容
`NAMING_CONVENTIONS.md`が策定した5つの命名規則（データソース接尾辞・
期間接尾辞・誤称禁止・provenance明示・唯一の正の参照元明示）は、策定の
みで実装（既存フィールドのリネーム）には未反映。個別の適用例
（[[NETCASH-DUAL-CALC-1]]の`net_cash_sec`化、[[RULE40-DEFINITION-
MISMATCH-1]]の期間接尾辞化等）は該当タスク側で扱うが、命名規則全体の
チェックリスト運用（新規フィールド追加時の適用）自体は独立したタスクと
して管理する。

**2026-08-15追記（実装結果との食い違い）**: `[[NETCASH-DUAL-CALC-1]]`の
実際の実装（2026-08-13完了）は、想定していた規則1の接尾辞化
（`net_cash`→`net_cash_sec`）を行わず、**フィールド名`net_cash`を維持
したまま算出元のみ`SECReader.get_net_cash()`へ統一**した（STONKS
SILOの独自算出`cash − yfinance totalDebt`を廃止）。これは規則1の趣旨
（データソースが異なる場合に接尾辞で識別できるようにする）に照らすと
矛盾ではない解釈も成り立つ：統一後はTANUKI VALUATION・STONKS SILOとも
同一のデータソース（`SECReader.get_net_cash()`）を参照するようになった
ため、「データソースが異なる場合」という規則1の適用前提自体が消滅し、
接尾辞による識別の必要性がなくなったとも言える。一方`[[RULE40-
DEFINITION-MISMATCH-1]]`の期間接尾辞化（`rule40_yoy_netmargin`・
`rule40_cagr3y_opmargin`）は想定通り規則2に従って実装済み。個別適用例
の記載は「命名規則の適用＝機械的な接尾辞付与」ではなく「適用要否は
統一後のデータソース同一性を踏まえて都度判断する」という運用実態に
即した表現に将来更新することが望ましい（本エントリの対応方針自体
〈チェックリスト運用〉には影響しないため、記録として付記するのみ）。

#### 対応方針
新規フィールド追加時に`NAMING_CONVENTIONS.md`の適用チェックリストを
参照する運用をCLAUDE_CODE_START.md等に明記する。既存フィールドの一括
リネームは影響範囲が大きいため、個別タスク（上記関連タスク）の実装時に
順次適用する。

#### 着手条件
なし

---

### [HYPECORE-REALSTRONG-DUAL-IMPL-1] real_strong判定のPython/JS二重実装で条件・閾値が相違
**優先度:** 中
**分類:** バグ / 設計不整合 / HypeCore
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ5（AS-IS-109〜112）

#### 内容
`detect_substage()`（サーバー側）の`real_strong`は`(rev_yoy>15 and
eps_surprise>-5超) or (eps_surprise>0 and rev_yoy>0) or (rev_yoy>30 and
eps_surprise>-30超)`という複数条件のORで構成されるが、detail.htmlの
クライアント側`getRec()`関数は`real_strong=(rev_yoy>30)&&(eps_surprise>0)`
という「ANDのみ・閾値も別」の簡略版を独自に再実装している。同一銘柄・
同一月でもサーバーの`substage`とクライアントの推奨表示が矛盾する組み合わせ
が起こり得る。

#### 対応方針
クライアント側`getRec()`をサーバー側`detect_substage()`と同一ロジックに
統一するか、JSON出力に`real_strong`の値自体を含めてクライアント側の
再計算を廃止する。

#### 着手条件
なし

---

### [SENS-MATRIX-DUAL-IMPL-1] stock.html独自5×5感応度マトリクスとbackend 3×3の並存
**優先度:** 中
**分類:** 設計不整合 / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ6（AS-IS-066/AS-IS-014）・`OUTPUT_ITEMS_INVENTORY.md`横断的発見事項1

#### 内容
バックエンドのAS-IS-014（`sensitivity.matrix`、3×3、DCFタイプにより
two_stage/three_stageを切替）とは別に、stock.html上に完全に独立した
クライアント側5×5感応度マトリクス（`calcSensIV()`）が同一ページに並存
する。`calcSensIV()`は常に2段階DCFのみで再計算するため、three_stage DCFや
tapering DCFを採用している銘柄では、同じページ内の2つの「感応度分析」
セクションが異なる計算式で異なる数値を表示する。`const alpha=d.alpha??1.0`
という宣言されているが式中で未使用の死コードも残存する。

#### 対応方針
バックエンドのAS-IS-014をそのまま表示する設計に統一するか、クライアント側
5×5マトリクスをDCFタイプ切替に対応させるかを判断する。死コード
（`alpha`変数）は合わせて削除する。

#### 着手条件
なし

---

### [RICE-ADJ-ASYMMETRIC-ZERO-1] RICEのrice_adjのみ0フロアガードがある非対称設計
**優先度:** 中
**分類:** バグ / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ6（AS-IS-027）

#### 内容
`calculate_rice()`（`rice.py:440`）で`rice_adj_val = (...) if cf_adj > 0
and wacc > 0 else 0.0`と明示的にゼロフロアされるのに対し、直上の
`rice_val`（`rice.py:438`）には`cf`（本来のCF値）が負であっても同様の
ガードがなく、そのまま計算される。CF（投資再生産効率）が構造的に負値を
取りうる銘柄では、`rice`は符号が反転した値をそのまま返すのに`rice_adj`
だけが0にフォールバックするという不整合が生じる。

#### 対応方針
`rice_val`にも`cf`が負の場合の同等のガードを追加するか、両者とも
ガードなしにするかを設計判断してから実装する。

#### 着手条件
なし

---

### [V0-V0RM-CONFUSION-RISK-1] v0(AS-IS-007)とv0_rmの取り違えリスク
**優先度:** 中
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ6（AS-IS-007/AS-IS-001）

#### 内容
`v0`（AS-IS-007）はβ込みCAPM WACCベースのDCF結果（`intrinsic_value_beta`
＝AS-IS-002の計算根拠）であるのに対し、画面のメイン理論株価
（AS-IS-001/AS-IS-006）は別途`market_return`10%固定・βなしで再計算した
`_v0_rm`（`dcf_components.v0_rm`に格納）を使う。latest.jsonを読む外部AI
やレビュアーが「v0からIVを積み上げ検算」しようとすると、トップレベルの
`v0`ではなく`dcf_components.v0_rm`を使わなければ整合しない罠になりうる。

#### 対応方針
latest.jsonのフィールド名・配置を見直し、どちらが「メイン計算根拠」かを
明確にする（例: トップレベル`v0`を廃止し`dcf_components`配下に統一する等）。

#### 着手条件
なし

---

### [DISCOVER-IMPACT-PRED-GAPS-1] 影響予測(AS-IS-248)のindex.html非表示・catalystモード新規分限定・様子見銘柄フォールバック欠如
**優先度:** 中
**分類:** 機能ギャップ / Discover
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ7（AS-IS-248/AS-IS-250）

#### 内容
①`impact_predictor.py`が生成する影響予測（AS-IS-248）は
`docs/discover/catalyst.html`・`news_history.html`では表示されるが、
Discoverのメイン画面`index.html`は`impact_predictions_{ym}.json`を一切
参照しない。②`run_catalyst()`は`first_detected==本日`のカタリストのみを
予測対象とするため、ある日の`catalyst.py`実行後に`impact_predictor.py`の
実行が漏れた場合、そのカタリストは未来永劫影響予測を持てない。
③`collect.py:main()`の分岐は「様子見」カテゴリ銘柄をGrok web検索代替の
対象から除外しており、NEWS APIで0件だった場合に無条件で空データになる。

#### 対応方針
①index.htmlに影響予測サマリーを追加表示する②catalyst実行と
impact_predictor実行の依存関係をワークフロー上で保証する（同一
ジョブ内での連続実行等）③「様子見」もGrok web検索代替の対象に含める。

#### 着手条件
なし

---

### [BREAKEVEN-FORECAST-METHOD-MISMATCH-1] 黒字化年予測の手法相違（TANUKI VALUATION vs STONKS SILO）
**優先度:** 中
**分類:** 設計不整合 / TANUKI VALUATION / STONKS SILO
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ7（AS-IS-051/AS-IS-162/163）

#### 内容
TANUKI VALUATION（AS-IS-051）は調整後EPS（四半期）4点のOLS単回帰、
STONKS SILO（AS-IS-162/163）はマージン（OCF or NI÷Revenue）の直近2点
線形外挿を優先しOLS絶対値回帰へフォールバックする2段階方式。同じ
「黒字化時期の予測」という概念に対し、データ粒度・手法ともに独立した
実装が並存している。

#### 対応方針
両者を統一すべきか（判定対象が異なるドメイン=DCF精度 vs 企業財務品質
のため統一不要の可能性もある）を設計判断してから対応要否を決める。

#### 着手条件
なし

---

### [EPS-DISCREPANCY-FLAG-OVERLOAD-1] 同一フラグ名EPS_DISCREPANCYが意味の異なる2処理で設定される
**優先度:** 中
**分類:** データ品質 / EPS Analyzer
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ8（AS-IS-272）

#### 内容
`check_eps_discrepancy()`（XBRL vs Alpha Vantage公式値の20%超乖離＝
データ品質上の疑義）と`apply_fair_value_detection()`（公正価値変動の
自動検出・調整が適用されたことの記録）は、意味的に全く異なる状況を
示すにもかかわらず同一の`special_flags: ["EPS_DISCREPANCY"]`を使う。
`special_notes`のどちらのサブキーが埋まっているかを確認しない限り原因を
判別できない。

#### 対応方針
2つの状況に別のフラグ名（例:`EPS_DISCREPANCY`と`FAIR_VALUE_ADJUSTED`）を
割り当てる。

#### 着手条件
なし

---

### [EPS-AI-ANALYSIS-LATEST-ONLY-1] EPS Analyzer ai_analysisが最新四半期のみ・過去四半期に遡及されない
**優先度:** 中
**分類:** 機能ギャップ / EPS Analyzer
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ8（AS-IS-270/271）

#### 内容
`pipeline.py`は`quarterly_results[0]`（最新のみ）に対して
`analyze_adjustments()`を呼ぶため、過去四半期の調整項目についてはAIに
よる健全性評価（health/comment/sources）が生成されない。

#### 対応方針
過去四半期についても遡及的にAI分析を生成するか、意図的な設計（コスト
抑制目的）であることを明示するかを判断する。

#### 着手条件
なし

---

### [FIVE-CATEGORY-RECLASSIFY-1] 5分類レベルの再判定（AS-IS-437〜441・404・057/058/060）
**優先度:** 中
**分類:** ドキュメント整合性 / 分類見直し
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ9・フェーズ10

#### 内容
①AS-IS-437〜441（TANUKI TAIL `tail_kpi_map.json`関連5項目）は「手動入力
データ」（AS-IS-425〜436と同一のAI下書き＋人手承認ワークフロー）に酷似
しているが、ステップ7の一次分類時点で「導出データ」側に区分された。
②AS-IS-404（`last_filed`）はフェーズ1で定義した「システム設定データ
（監視状態管理系）」と同種の性質だが「その他」に取り残されている。
③AS-IS-057/058/060（Reverse DCF比較表のメタ情報行「場所」「用途」
「ガード」）は実データ値ではなく「実装差異の比較分析」自体がAS-IS番号を
持ってしまっている。いずれも`DERIVED_DATA_SUBCATEGORIES.md`の8分類内の
再配置ではなく、より上位の5分類（一次データ／手動入力データ／移送
データ／システム設定データ／導出データ）自体の再判定が必要。

#### 対応方針
①②は5分類を手動入力データ・システム設定データへ変更するか判断する。
③はカタログから除外する（メタ情報であり出力データではないため）か、
現状維持するかを判断する。`TO_BE_FINAL_LIST.md`・
`DERIVED_DATA_SUBCATEGORIES.md`・`FIELD_DEFINITIONS.md`への反映が
必要になる。

#### 着手条件
なし

---

### [SP500-GSPC-MULTI-FETCH-1] S&P500/^GSPCの複数取得経路（クロスシステム+Market Pulse内4重取得、外部APIコストの実害は解消済み）
**優先度:** 低（2026-08-13、中から引き下げ。理由は下記「2026-08-13更新」参照）
**分類:** 効率化 / 重複取得 / MACRO PULSE / Market Pulse
**登録日:** 2026-07-23
**更新日:** 2026-08-13（重複計算パターン棚卸し調査〈チャット記録〉で
実コードを再確認。`collect_and_send.py`の`^GSPC`参照は現在
`_get_sp500_ma_deviation()`内3箇所（`_md_get_ma_deviation()`×2・
`_md_get_price_series()`×1）＋`fetch_recent_records()`呼び出し3箇所
（主要9銘柄ブロック・NYSE Composite divergence用・大型対小型比用）の
計6箇所に整理されているが、いずれも`common.market_data.reader`経由の
ローカルファイル読み取りに統一済み（`[[MARKETDATA-LAYER-
CONSTRUCTION-1]]`実装済み）。**外部API直接呼び出しは0件になっており、
当初の実害（外部APIコストの無駄な重複）は既に消滅している。**
一方、対応方針が挙げていた「Market Pulse内部の複数箇所を1回の取得
結果を使い回す設計に統合する」というコードレベルの集約リファクタリング
自体は未実施のまま（呼び出し箇所は依然として独立）。実装しても実害
削減効果はほぼゼロ（ローカルファイル読み取りの重複コストは無視できる
水準）で、コード整理としての価値のみのため優先度を「中」から「低」へ
引き下げる）
**発見:** `FIELD_DEFINITIONS.md`フェーズ1・フェーズ10（AS-IS-190/312）・`CONCEPT_PARAMETER_VARIATIONS.md`軸2概念5

#### 内容
MACRO PULSE（FRED `SP500`優先→stooqフォールバック）とMarket Pulse
（yfinance `history()`）が完全に独立した経路でS&P500を取得しているのに
加え、Market Pulse単体のスクリプト内だけで`^GSPC`が少なくとも4箇所
独立にyfinance取得されている（主要9銘柄ブロック・NYSE Composite
divergence用・大型対小型比用・`sentiment.sub_scores.sp500_ma_dev`及び
両checklistのMA200判定用）。いずれもキャッシュ・再利用されていない。
（登録時点＝yfinance直接呼び出し時代の記述。2026-08-13時点の実コード
状況は上記「更新日」参照）

#### 対応方針
Market Pulse内部の複数箇所はまず1回の取得結果を使い回す設計に統合する
（低コストで対応可能。ただし2026-08-13時点で外部APIコストの実害は
解消済みのため、着手はコード整理目的の優先度低タスクとして扱う）。
MACRO PULSE・Market Pulse間の統合は`INPUT_DATA_TOBE.md`のyfinance
統合層設計に委ねる（`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`で実施済み）。

#### 着手条件
なし

---

### [MARKETPULSE-MINOR-INCONSISTENCIES-1] Market Pulseの軽微な構造的不整合まとめ（Hindenburg固定値・credit原資産不整合・CSV列欠落・breadthパススルー漏れ・F&G情報源混同・Tech Pulseバックフィル式相違）
**優先度:** 中
**分類:** データ品質 / Market Pulse
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ10

#### 内容
①Hindenburg Omen判定が実測`total_stocks`（503件）ではなく固定値500を
ハードコード。②`credit.stock`（^GSPC指数）と`credit.bond`の株式側判定
（SPY ETF）が同一の`credit`ブロック内で異なる原資産を参照。
`credit.credit`（HYG/LQD各ETFのchange_percent差分）とAS-IS-328（HYG対
LQD比、比率そのものの変化）も独立した別計算経路。③`market_data.csv`は
`CSV_COLUMNS`に列挙されていないフィールド（NASDAQ本体・全volume_ratio・
tech_pulse/asset_flow/credit/両checklist/fear_greed/comments_history）を
無条件に欠落させる。④`sentiment.breadth`は`breadth_data.json`の単純な
パススルーだが`unchanged`/`ad_ratio_1d`/`total_stocks`/`rsp_return_1d`/
`spy_return_1d`がパススルー対象から漏れている。⑤CNN（`fear_greed`
パッケージ）とfeargreedchart.comという2つの異なるF&G情報源が一部の
フォールバック・後方互換コードで区別なく代替される。⑥`backfill_tech_
pulse.py`のTech Pulseスコア計算式（固定レンジ加算方式）が現行
`collect_and_send.py`（90日パーセンタイル方式）と全く異なり、過去の
バックフィル値と最近の値は単純比較できない。

#### 対応方針
①実測`total_stocks`を使うよう修正②原資産を統一するか意図的差異である
旨を明示③CSV出力対象フィールドを見直すか、CSVとJSONの非互換性を明示
④パススルー対象フィールドを追加⑤2つのF&G情報源を明確に区別する
⑥バックフィル済みデータの再計算要否を判断する。優先順位を付けて
順次対応する。

#### 着手条件
なし

---

### [TVGROWTH-EXPLICIT-DEFAULT-AMBIGUOUS-1] terminal_growth 3.0%の明示設定と未設定を区別できない
**優先度:** 中
**分類:** バグ / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ6（AS-IS-059）

#### 内容
`get_terminal_growth()`は`abs(ticker_tv_g - 0.03) > 1e-5`という差分
チェックの設計上、管理者が意図的に「このtickerのTVは3.0%にする」と
`maturity_config.json`へ明示設定しても、デフォルト値と一致するため
「未設定」とみなされ、セクター別Damodaranテーブルの値がもし異なれば
そちらが優先されてしまう。3.0%を明示指定したい場合の抜け道が存在
しない。

#### 対応方針
「明示設定」と「未設定」を区別するフラグ（例: `maturity_config.json`
側に`terminal_growth_explicit: true`等）を追加する。

#### 着手条件
なし

---

### [JNJ-XOM-PM-FLOOR-RISK-1] JNJ・XOM・PM・CONはrecommended_g候補が最低ラインでMO型floor転落の潜在リスクあり
**優先度:** 中
**分類:** データ品質 / TANUKI VALUATION / 監視対象
**登録日:** 2026-07-19
**発見:** [[GROWTH-SANITY-CLASS-SYNC-1]]（完了・BACKLOG_DONE.md参照）floor適用対象
範囲確認調査

#### 内容
`segment_config.json`未登録37銘柄のうち、`recommended_g`算出候補
（rev_cagr_3yr/5yr・g_fundamental・industry_benchmark）が**ちょうど
2件**（1件失えば`recommended_g`算出不能＝MO型のfloor転落リスク）の
銘柄が6件存在する: JNJ・PM・XOM・GEV・FLYW・PAYS。うちJNJ・PM・XOMは
成熟ディフェンシブ株（GEV/FLYW/PAYSは高成長株で候補不足が偶発的、
リスクの性質が異なる）。CONも`rev_cagr_5yr`算出不能（2024年スピンオフで
データ不足）な近接リスク銘柄。

実際のFCF生成長率（`calculate_fcf_cagr()`のraw_cagr、floor適用前）を
実データで確認したところ、**JNJ（+3.1%）・XOM（-31.5%）はMO
（+2.7%）と同等またはそれ以上にfloor(15%)との乖離が大きい**
（JNJ: floor gap +11.9pt、XOM: floor gap +46.5pt、MOの+12.3ptと同等〜
それ以上）。特にXOMはFCFが実際に大きく減少している局面（raw=-31.5%）で、
もしfloorが発動すれば「FCFが3割減っている最中の企業に年15%成長を
仮定する」という最も危険なミスマッチになる。

#### 対応方針（未確定）
即座の対応は不要（現時点でrecommended_g算出候補2件を維持できており
floorには落ちていない）。ただし次回以降の決算更新でJNJ/PM/XOM/CONの
`rev_cagr_3yr`/`5yr`のいずれかがマイナスへ転じ候補が1件以下になった
場合、MOと同型の`TICKER_INDUSTRY_OVERRIDES`追加＋
[[GROWTH-SANITY-CLASS-SYNC-1]]で実装した案B'（floor到達中かつ
industry_g単独1件の場合のみ候補数閾値を緩和）が既存の実装パターンとして
そのまま適用できる見込み。

#### 着手条件
候補件数が実際に2件を下回った場合（`report_consistency_check.py`等での
継続監視、またはgrowth_sanity再確認時に検知）

---

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

#### 追記（2026-07-18・FY52WEEK-BS-NULL-SILENT-1 Phase A実装時の副次発見）
新設したWARN-25（BS項目None検知）で**SITMのcash_and_equivalents
（FY2025）欠落**を新規検知した。上記5銘柄（CAT/CPRT/ELF/GEV/HEI）の
リストにSITMは含まれていなかったが、同一のタグ未登録が原因の未
カタログ化インスタンスと推測される（`tag_definitions.py`は本追記時点
で未更新のため）。対応方針自体に変更はなく、着手時に対象銘柄の再洗い出し
（全105銘柄への機械スキャン）を行うことを推奨する。

#### 着手条件
なし

---

### [BS-FIELD-NEWLY-MISSING-2026-1] LLY/SCCO/SPIRのBS項目が実額から当年Noneへ新規遷移（CASH-TAG-MISSING-1と同型、一次情報確認が必要）
**優先度:** 未定〜中
**分類:** データ取得 / データ品質ゲート
**登録日:** 2026-07-19
**発見:** [[BS-FIELD-NONE-TRANSITION-DETECT-1]]（完了・BACKLOG_DONE.md参照）
実装後の全銘柄検証時、WARN-26が事前確認済み8件に加え想定外3件で発火し判明

#### 内容
WARN-26（前年値あり→当年None遷移検知）実装後の全100銘柄検証で、以下3件が
新規に発火した。事前調査（FY52WEEK-BS-NULL-SILENT-1 Phase B/C）の「生涯
フェードアウト25件」は「過去に明示的`val=0`の申告実績がある」ケースに
限定して抽出していたため、この3件（過去は実額の非ゼロ値）は元々その25件の
定義に該当しない別カテゴリであり、事前確認・`config/warn_acknowledged.json`
登録の対象外のまま「🆕未確認」で残っている：

- **LLY（short_term_investments）**: FY2024=$154.8M（実額）→FY2025=None
- **SCCO（short_term_debt）**: FY2024=$499.8M（実額）→FY2025=None
- **SPIR（long_term_debt）**: FY2024=$4.618M（実額）→FY2025=None

いずれも直近年度に実額の非ゼロ値が申告されていたにも関わらず、最新年度で
候補タグ自体の申告が停止した可能性がある。[[CASH-TAG-MISSING-1]]
（CAT/CPRT/ELF/GEV/HEI/SITMのcash_and_equivalents欠落）と同型のパターン
（候補タグリストの網羅漏れによる`_extract_values_best_candidate`の単一
勝者タグ設計の限界）が疑われるが、一次情報（SEC EDGAR 10-K原本）での
確認は未実施。

#### 対応方針（未確認・要一次情報調査）
[[CASH-TAG-MISSING-1]]の対応手順に準じ、各銘柄の10-K原本を確認し、
以下いずれかを判定する：
- 候補タグの申告停止によるデータ取得ミス（別タグへの移行・
  `XBRL_MAPPING`への候補追加が必要）
- 実際に真のゼロ・借入/投資解消が発生した（真の値、対応不要。
  `config/warn_acknowledged.json`への「生涯フェードアウト」登録を検討）

調査後、`report_consistency_check.py::CHECK-26`（WARN-26）は現状
「🆕未確認」のまま維持しておりブロッキングではないため、緊急対応は不要。

#### 着手条件
なし

---

### [FYE-BOUNDARY-COLLISION-UNCONFIRMED-1] LITE/WSTの決算期変更境界バケツ競合が一次情報未確認のまま残存
**優先度:** 低〜未定
**分類:** データ品質ゲート / 検知体制
**登録日:** 2026-07-19
**発見:** [[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]（完了・BACKLOG_DONE.md参照）
実装後の全銘柄検証時、WARN-24が想定していたRCAT以外にLITE・WSTでも発火し判明

#### 内容
WARN-24（決算期変更境界の年度バケツ競合検知）実装後の全100銘柄検証で、
事前調査で想定していたRCAT（2件）に加え、以下2件が新規に発火した：

- **LITE（net_income）**: end=2015-06-27（本人データ、fy=2015）と
  end=2015-08-01（fy=2018の10-Qで参考開示、is_own_data=False）が
  同一年度バケツで競合
- **WST（rpo）**: end=2013-12-31（本人データ、fy=2013）と
  end=2013-06-30（fy=2022の10-Kで参考開示、is_own_data=False）が
  同一年度バケツで競合

いずれも`override_applied: true`（現在のパイプラインは既に本人データ側の
正しい値を採用済み）であり、`_fiscal_anchors_far_apart()`フィルタ
（(月,日)循環距離>30日）を通過しているため、決算日そのものが動いた
可能性を示す一次シグナルとしては真陽性の候補だが、RCATのような継続的な
決算期変更パターン（クラスタリングスキャンでも複数クラスタとして検出
される）とは異なり、`fye_change_candidate_scan.py`の再スキャンでは
LITE/WSTともに候補として検出されていない（単発の孤立したエントリ1件のみ）。
そのため、NOW型（2013年10-Kの単発参考開示によるノイズ、[[FYE-CHANGE-
BOUNDARY-COLLISION-BLIND-1]]参照）と同種の「決算期変更を伴わない単発の
参考開示・データ入力ミス」の可能性が高いと推測されるが、SEC EDGAR
10-K/10-Q原本による一次情報確認は未実施。

#### 対応方針（未確認・要一次情報調査）
LITE（accn 0001633978-18-000108、end=2015-08-01のnet_income参考開示）・
WST（accn 0000105770-23-000012、end=2013-06-30のrpo参考開示）それぞれの
該当filingを10-K/10-Q原本で確認し、以下いずれかを判定する：
- 単発の参考開示・タグ付けミス（対応不要、`config/warn_acknowledged.json`
  への登録を検討）
- 未確認の決算期変更が実在する（`fye_change_candidate_scan.py`の
  クラスタリング閾値の見直し、または個別のticker_restrictions対応を検討）

調査後、`report_consistency_check.py::CHECK-24`（WARN-24）は現状
「🆕未確認」のまま維持しておりブロッキングではないため、緊急対応は不要
（`override_applied: true`のため現時点で実害はない）。

#### 着手条件
なし

---

### [BS-FIELD-FADEOUT-NONZERO-LAST-VALUE-1] CSGP/KULR/RCATのBS項目フェードアウトは直近既知値が非ゼロで単純な$0フォールバック不可
**優先度:** 中〜低
**分類:** データ品質ゲート / アーキテクチャ
**登録日:** 2026-07-19
**発見:** [[FY52WEEK-BS-FADEOUT-FALLBACK-1]]（完了・BACKLOG_DONE.md参照）
事前調査時、25件の「生涯フェードアウト」候補のうち3件が単純パターンと
異なることが判明したため分離

#### 内容
FY52WEEK-BS-FADEOUT-FALLBACK-1で実装した履歴フォールバック（過去の
直近既知値が明示的$0であれば真のゼロと推定する）の条件判定ロジックでは、
以下3件は「直近の既知値が非ゼロ」のため対象外のまま残っている：

- **CSGP（short_term_investments）**: 2013年$0の後、2015-2018年に
  $9.95M〜$15.5Mの実額が続き、2019年から消失。直近既知値（2018年、
  $10.07M）は非ゼロ。
- **KULR（short_term_debt）**: 2021-2022年$0の後、2024年に$516,547の
  実額が出現し、2025年から消失。直近既知値は非ゼロ。
- **RCAT（long_term_debt）**: 2012-2015年$0の後、2018/2020/2022/2023年
  に$0.4M〜$2.0Mの実額が断続的に出現し、2024年から消失。直近既知値
  （2023年、$401,569）は非ゼロ。

これら3件は「過去に$0実績があれば真のゼロと推定する」という単純な
フォールバックロジックを適用すると誤り（特にCSGPは直近既知額が$10M超
であり真のゼロとは考えにくい）になるため、意図的に対象外としている
（`_lookup_last_confirmed_zero_year()`の条件判定により自然に除外される
設計、コード変更は不要）。

#### 対応方針（未確定・要設計）
以下いずれかの方向性が考えられるが、優先度は低く次回以降の判断とする：
- 直近の非ゼロ実額を「暫定値」として採用し、経過年数に応じた信頼度
  低下の注記を付ける別ロジックを設計する
- 一次情報（10-K/10-Q原本）で当該期間のBS実態を個別確認し、真の
  最新値を特定してticker_restrictions等で個別対応する
- 現状（Noneのまま、または`or 0`による暗黙のゼロ扱い）を許容し、
  対応不要と判断する

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

### [SPLIT-REALTIME-GAP-REVERSE-1] KULR/SPIRのリバース分割で同型の恒久固着ギャップ有無が未確認
**優先度:** 低
**分類:** データ品質 / EPS ANALYZER
**登録日:** 2026-07-20
**発見:** [[SPLIT-REALTIME-GAP-1]]（完了・BACKLOG_DONE.md参照）実装時

#### 背景
SPLIT-REALTIME-GAP-1の実装前調査で行った全101銘柄横断スキャンは、フォワード
分割（`diluted_shares_used`が数倍に「ジャンプ」するパターン、比率>1のみ）を
検知対象としていたため、リバース分割（比率<1、株数が「減る」パターン）を
見落としていた。

BACKLOG_DONE.md「Phase 2b-3完了（2026-07-12）」の記述で、KULR・SPIRの2銘柄が
当時から`extract_key_facts.py`のfact選定ロジック修正の対象銘柄として言及
されていたことを再確認し、yfinanceでKULR（2025-06-23、1-for-8）・SPIR
（2023-08-31、1-for-8）のリバース分割が実在することを確認した。

ローカルキャッシュ（`docs/value-monitor/adjusted_eps_analyzer/data/{KULR,SPIR}/
quarterly.json`）を見ると、いずれも「高い値が数四半期続いた後、低い値へ
ジャンプし、以後低い値が続く」というNVDA型と鏡写しのパターンが見られる
（KULR: 2022-06-30〜2024-03-31が約104M〜142M→2024-06-30以降は約22.7M〜46.2M。
SPIR: 2022-03-31〜2022-06-30が約139M→2022-09-30以降は約17.5M〜33.3M）。
いずれも実際のリバース分割日より1年程度早いタイミングでジャンプしており、
SPLIT-REALTIME-GAP-1のNVDA等と同型の「翌年以降の10-Q再掲で先に是正された
四半期」＋「再掲機会がなく古い側の値が残存」という構造が疑われるが、
一次情報（SEC 10-Q/8-K）での確認・`apply_split_adjustments()`が
リバース比率（ratio<1）を正しく扱えるかのコード確認はいずれも未実施。

SCCO（yfinanceに2024年以降ほぼ毎四半期`~1.005-1.01`という極小の「分割様」
記録があるが、ローカルキャッシュのdiluted_shares_used系列はほぼ横ばい
〜緩やかな増加のみで明確なジャンプ/ドロップなし）は、特別配当等に伴う
yfinance側のデータ仕様上のノイズであり実分割ではないと判断、対象外。

#### 対応方針（未確定）
- KULR/SPIRそれぞれのSEC 10-Q/8-K一次情報でリバース分割日・比率を確認する
- `apply_split_adjustments()`の閾値計算（`pre_split_threshold = post_split_avg
  / ratio × 1.5`）がratio<1（リバース分割）でも意図通り機能するか
  （現状の実装はratio>1のフォワード分割のみで検証されている）をコードで確認する
- 実装するか否か・優先度はKoichiさんの次回判断待ち

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

### [TANUKI-FIN-2] 金融機関銘柄（JPM・GS・SOFI）へのエクイティDCF並行評価対応
**優先度:** 低（設計相談は完了・実装未着手）
**分類:** 設計課題 / TANUKI VALUATION
**登録日:** 2026-07-06
**ステータス:** 保留（着手時期未定、AI側の調子が良いタイミングで着手予定）

#### 背景
金融機関（JPM・GS・SOFI）は負債が事業構造そのものの一部であるため、通常の
FCFF（企業DCF）が適合しにくい。業界標準としてFCFEベースのエクイティDCFが
適合する。Vは決済ネットワーク型で通常のFCFF DCFが適合するため対象外。

**SOFI追加の経緯（2026-07-19）**: SOFI-DATA-1（銀行免許取得後にLongTermDebt
系タグの申告を停止し合算タグへ移行した問題のLTDebt恒久修正）、および
[[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]のSOFI個別調査（流動/非流動を区分
しない銀行持株会社特有の非分類BS構造であることが判明）を通じて、SOFIも
JPM・GS同様「負債・投資有価証券が事業構造そのものの一部」という金融機関
特有の性質を持つことが確認された。これを契機に、対象銘柄にSOFIを追加する
意向が確定した。

#### 対応方針
- 案（A）: 既存のFCFF（企業DCF）は維持したまま、対象銘柄（JPM・GS・SOFI）
  について追加でFCFE（エクイティDCF）評価を並行実施し、latest.json/
  report.txt上で両方式の結果を比較できるようにする機能拡張とする
  （既存FCFFを置き換える「切り替え」ではなく「並行評価・比較」）
- 判定方式: SIC code等による自動判定ではなく、対象ティッカー
  （JPM・GS・SOFI）を設定ファイルに明記する方式を採用（対象が少数のため
  過剰実装を避ける）
- 今後対象銘柄が増える場合、自動判定ロジックへの切り替えを再検討する

#### 関連
- [[TANUKI-FIN-1]]（金融機関向けバリュエーション対応・DDM等）とは対象アプローチが異なる
  （DDMではなくFCFEエクイティDCF、対象は少数ティッカーのハードコード方式）。
  着手時にどちらの方式を採用するか、あるいは併存させるかを判断する。
- [[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]（SOFIのshort_term_investments
  override設計）は、既存FCFFのNet Debt計算に引き続き使われるフィールドの
  ため、本エントリの着手を待たず独立に進めてよい（FCFE並行評価の実装
  時期に関わらず、既存FCFFの正確性向上に直接寄与するため）。
  **2026-07-19実装完了（`sti_concept=OtherInvestments`、BACKLOG_DONE.md
  参照）。既存FCFFのNet Debt計算にSOFIの正しいshort_term_investments値が
  反映される状態になった**。

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

**QUALITY-GATES-EPIC-1への統合について**: 本タスクは
[[QUALITY-GATES-EPIC-1]]のゲート1（PREVENT-5）/ゲート4
（TICKER-AUDIT-1）に統合マッピング済み。個別に着手する前に
QUALITY-GATES-EPIC-1のPhase 3/4の進行状況を確認し、二重実装を
避けること。

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

**QUALITY-GATES-EPIC-1への統合について**: 本タスクは
[[QUALITY-GATES-EPIC-1]]のゲート1（PREVENT-5）/ゲート4
（TICKER-AUDIT-1）に統合マッピング済み。個別に着手する前に
QUALITY-GATES-EPIC-1のPhase 3/4の進行状況を確認し、二重実装を
避けること。

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

### [TICKER-LOADING-UNIFICATION-1] 銘柄リスト読み込みロジックのtickers.py統一
**優先度:** 低
**分類:** 保守 / 銘柄リスト参照
**登録日:** 2026-07-11〜2026-07-13（統合日: 2026-08-03）
**発見:** [[TICKER-DIRECT-ACCESS-GUARD-1]]実装時の全リポジトリスキャン・
[[TICKER-SOURCE-UNIFY-1]]（完了・BACKLOG_DONE.md参照）対応方針3実施時の
横断調査

#### 内容
以下3箇所が、`tickers.py`が既に提供する銘柄リスト取得機能
（`get_all_tickers()`等）を使わず、cik_lookup.csv等を独自に読み込む
重複実装を持つ。いずれもバグではなくコード重複（DRY違反）で、
`tickers.py`経由への統一で解消できる。

**対象箇所**:

① `common/system_health.py::check_h_config()`（旧SYSHEALTH-CIK-
DEDUP-1、優先度低）: segment/maturity configの孤立エントリ検出のため
`all_tickers`（フラグ無視の全登録銘柄）を`csv.DictReader`で独自に
パースしている。同一の全銘柄取得は`tickers.get_all_tickers()`が既に
提供しており、置換可能（バグではなくコード重複の解消のみ）。
`all_tickers = {r["ticker"] for r in rows}`を`tickers.get_all_
tickers()`ベースに置換する。挙動が完全に同一であることを確認してから
着手する。

② `src/tail/kpi_proposer.py`・`src/tail/sec_ctrl_fetcher.py`・
`src/tail/text_kpi_extractor.py`（旧TAIL-CIK-LOOKUP-DEDUP-1、優先度
低）: 3ファイルが`load_cik(ticker)`（cik_lookup.csvから指定ティッカー
のCIKを検索して返す関数）をそれぞれ独立に実装している（関数名・実装
内容ともほぼ同一）。FLAG-CONSUMER-AUDIT-2/3のようなフラグバイパスバグ
型ではなく、単純なDRY違反（3箇所の重複実装）。共有ヘルパー（例:
`common/sec_data/tickers.py`または`config.py`への`get_cik(ticker)`
追加）に統合し、3ファイルから呼び出す形に変更する。

③ `common/sec_data/config.py`（旧TICKER-SOURCE-CONFIG-DUP-1、優先度
低）: `tickers.py`とは別の独立した重複ユーティリティで、
`_load_from_csv()`が独自にcik_lookup.csvを読み、`get_all()`（全銘柄）・
`get_holdings()`・`get_watchlist()`・`get_ticker_info()`を提供して
いる。`common/sec_data/update.py`（SEC生データ取得）が現在も正規に
これを使用しており「バグ」ではないが、`tickers.py`の
`get_all_tickers()`と機能重複している。統合要否・移行方針は他2件より
スコープが広い可能性があるため、個別に検討する。

#### 対応方針
①②は単純な置換で完結する見込み。③は`common/sec_data/update.py`が
正規に依存している既存の公開APIのため、統合時は移行方針
（config.pyのAPI群をtickers.py側にどう吸収するか）を先に検討してから
着手する。

#### 着手条件
なし

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

### [ANOMALY-PATTERN-CATALOG-1] 異常データパターンのカタログ化・新規登録時照合の仕組み
**優先度:** 中
**分類:** アーキテクチャ / データ品質ゲート / 銘柄登録フロー
**登録日:** 2026-07-19
**発見:** [[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]（完了・BACKLOG_DONE.md参照。
KLAC/TER/V/SOFI）の対応中の議論

#### 背景
XBRLタグ選定等で銘柄固有の異常が見つかるたび、都度ゼロから個別調査
する非効率を解消するため、異常パターンを「型」として整理・蓄積し、
新規銘柄登録時（または既存銘柄で新たな異常が疑われた時）に既知の
型と照合してから対応判断する運用を導入する。

**2026-07-15の関連決定との関係（重要・要参照）**：
PREFLIGHT-CHECK-1で一度、ARCH-DATA-1と共有する汎用パターン判定
カタログ構想を検討したが、「登録前段階の統計的推測（SIC・社名等）
だけでは、実際にどのタグが正しいかの確定判定はできない」との理由で
見送られた経緯がある（本エントリ直前の「設計メモ追記（2026-07-15・
ARCH-DATA-1残課題③調査結果を反映）」参照）。本タスクはこれを覆すもの
ではなく、**照合のタイミングを「登録前」ではなく「登録後・実データ
取得後」に置く**点で異なる。2026-07-15の決定が「登録前の統計的推測は
時期尚早」としつつ、revenue系タグ競合を「Step1完了後の実データ検知」
（`revenue_tag_conflict_check.py`）へ統合する方針を既に採用していた
ことと同じ考え方を、short_term_investments等の他フィールドにも
一般化するのが本タスクの位置づけ。

#### 初期カタログ（今回確定した型）
**型A：候補集合＋freshness収束型**
- 症状: 正しいXBRLタグが他銘柄でも広く使われる汎用タグで、上限
  チェック等の値ベース検証だけでは誤タグの混入を検知できない
- 根本原因: 汎用タグ自体は銘柄非依存で存在するが、どのタグが
  「その銘柄にとって正しいか」は銘柄固有の申告慣行に依存する
- 対応方法: TICKER_RESTRICTIONSにticker別の候補タグ（単一または
  複数）を登録し、既存の`_extract_values_best_candidate()`の
  freshnessスコアで自動選定させる。グローバル候補リストへは
  追加しない
- 実例: KLAC/TER/V/SOFI（short_term_investments、2026-07-19実装）

**型B：非分類BS・近似値許容型（予約・実例なし）**
- 症状: BS構造自体が流動/非流動を区分しない等、単一タグでは
  真の値を表現できない
- 根本原因: 会計上の科目構造そのものの制約
- 対応方法: 近似値を採用しつつreport.txt/latest.json上で残差・
  不確実性を明示する
- 実例: なし（SOFIで型B該当を想定したが、調査の結果OtherInvestments
  タグで完全一致し型Aに収束したため、2026-07-19時点で実例なし。
  将来型B該当銘柄が見つかった場合の受け皿として型定義のみ残す）

**型C：資産クラス変化・当年度未タグ化型**
- 症状: BS計上額の構成が、単発の企業イベント（保有先の非上場
  投資先が新規上場する等）により当年度から質的に変化する。
  従来使用していた候補タグの申告自体も同時に停止する。新たに
  混入した資産クラスは、その変化が発生した当年度の10-K自体では
  対応するXBRL概念が明確にタグ付けされておらず、後続の四半期
  報告（10-Q）の比較年度開示で初めて該当タグが登場することがある
- 根本原因: (a) 一時的・単発的な企業イベント（投資先のIPO等に
  よる会計分類の切替）、(b) filer側のXBRLタグ付けが、その年の
  10-K提出時点では新資産クラスに対応する概念を採用しておらず、
  翌四半期以降に整備される、という2つの要因が重なったもの。
  型A（銘柄固有の恒常的な申告慣行の違い）・型B（BS構造自体の
  恒常的制約）と異なり、恒常的な性質ではなく一過性の移行期
  特有の欠損である可能性が高い
- 対応方法: 単一タグでの完全解消は不可能なことが多い。選択肢は
  以下3つ（優先順位はケースバイケースで判断）：
  ① 複数タグの合算による近似値を採用し、型Bと同様に残差を明示する
  ② 翌年度の10-K提出後、filer側のタグ付けが整備され単一/合算
     タグで正確に捕捉できるようになったか再確認する（型Aへ
     収束する可能性がある）
  ③ 当面はNoneのまま許容し、Net Debt計算等の下流への影響を
     個別確認する
- 実例: NVDA（short_term_investments、2026-07-19発見・2026-07-20
  対応方針①〈候補タグ合算の近似値〉採用・cross_filing_tags機構で
  実装完了。詳細はBACKLOG_DONE.md「NVDA-STI-TAG-UNIDENTIFIED-1」参照）

#### 対応方針（設計・未着手）
- REGISTER-FLOW-REDESIGN-1・PREFLIGHT-CHECK-1と統合的に設計する
  （別々に実装しない）
- 照合タイミングはStep1（SECデータ取得）完了後とし、
  `revenue_tag_conflict_check.py`（ARCH-DATA-1残課題③で実装済み）と
  同様の位置に配線することを想定
- REGISTER-FLOW-REDESIGN-1の対応方針2（status=provisioning導入、
  未着手）と組み合わせ、カタログ照合を通過するまでactiveへ
  昇格しない設計との統合要否を検討する
- 自動適用は既知パターンと完全一致した場合のみとし、非該当の
  場合は個別調査へ回す（自動停止はしない、判断材料の提示に留める
  というPREFLIGHT-CHECK-1の原則を踏襲）

#### 着手条件
なし（ただし新規銘柄登録はいつでも発生しうるため、着手を
先延ばしにする前提にはしないこと）

---

### [MACRODATA-SCHEDULED-SILENT-GAP-CSCICP-USALOL-1] CSCICP03USM665S・USALOLITONOSTSAMが現行INDICATOR_CONFIGから削除済みにも関わらず、05_indicator_schedule.csvの既存scheduled行がfred_id空文字列のまま処理され、actualが埋まらない静かなデータ欠落を起こす可能性
**優先度:** 低〜中（実害の有無・範囲が未確認）
**分類:** バグ疑い（サイレント欠落）
**登録日:** 2026-08-12
**発見:** `common/macro_data/`新設事前調査・FRED消費者洗い出し
（チャット記録、2026-08-12）

#### 内容
`CSCICP03USM665S`（CB Consumer Confidence）・`USALOLITONOSTSAM`
（Conference Board LEI）は`05_import_history.py`固有の旧
`FRED_INDICATORS`辞書にのみ存在し、現行`05_main.py`の
`INDICATOR_CONFIG`（12系列）には**含まれていない**（実コード確認済み）。
にもかかわらず、`docs/market-monitor/macro-pulse/data/
05_indicator_schedule.csv`には両指標の`scheduled`行が現存する
（実データ確認済み、例:
`Conference Board LEI,2026-06-08,USALOLITONOSTSAM,FRED,,,scheduled`）。

`fred_release_dates()`（458-498行）は`INDICATOR_CONFIG.items()`のみを
走査するため、この2系列の**新規**`scheduled`行が今後生成されることは
ない。しかし**既存の残存`scheduled`行**は`main()`の`for sched in
scheduled:`ループ（2196-2216行）で処理対象になり、`fetch_event_row()`
内で`cfg = INDICATOR_CONFIG.get(indicator, {})`が空dictを返すため
`fred_id`が空文字列となり、`if fred and fred_id and actual_val is
None:`（921行）の条件が成立せずFRED取得がスキップされる。**例外は
発生しないが、`actual`欄が空欄のまま行だけが`05_events.csv`に
生成される**静かな欠落が起こりうる。

#### 対応方針（未定・実データ確認が必要）
- `05_events.csv`・`05_indicator_schedule.csv`の実データを確認し、
  この2指標の`scheduled`行が既に処理済み（過去日、`actual`空欄のまま
  残存）か、まだ未来日で残存しているかを確認する
- 既に空欄行が生成されている場合は実害の範囲（何件か）を確認する
- 対応要否の判断: ①`05_indicator_schedule.csv`から該当2系列の
  残存`scheduled`行を削除する、②`INDICATOR_CONFIG`に復活させる
  （意図的に除外されたのか要確認）、のいずれかを実データ確認後に判断

#### 着手条件
実際に`05_events.csv`等でこの欠落が発生しているか（scheduled行の
残存有無）を実データで確認してから対応要否を判断する。

---

## 優先度：低（アイデア段階）

### [VRT-REVENUE-2018-MISSING-1] VRT FY2018のrevenue=0取得失敗（gross_profitと定義上矛盾）
**優先度:** 低（実害はGP法入力整合性ガードで既に遮断済み、着手緊急性なし）
**分類:** バグ / データ取得 / SEC EDGAR
**登録日:** 2026-08-19
**発見:** `[[OPERATING-INCOME-EXTRACTION-GAP-1]]`案D（GP法入力整合性
ガード）実装時の全105銘柄実測

#### 内容
VRT（Vertiv Holdings）FY2018の`annual_2018.json`で`revenue=0`
（取得失敗）であるにもかかわらず`gross_profit=-$2,865,200,000`
（マイナス28.65億ドル）という、定義上（`gross_profit = revenue - COGS`）
成立しない組み合わせが存在する。FY2019も同様に`revenue=0`だが、こちらは
`operating_income`が標準タグ（比較年度再掲、`is_own_data=False`）から
取得されているため実害はない。

**推測（未検証）**: VRTは2020年2月にVertiv Holdings（旧GS Acquisition
Holdings、SPAC）とVertiv Group（Platinum Equity傘下）の合併により上場した
企業。2018年は合併前の前身法人（Vertiv Group、非公開）のデータであり、
SEC EDGARへの遡及登録時にrevenueタグが適切に紐付けられなかった可能性が
高いと推測されるが、実際の登録経緯（S-4等）は未確認。

#### 実害
`_backfill_operating_income()`のGP法計算にこの矛盾したgross_profitが
そのまま入力されると、`operating_income=-$4,287,300,000`という明らかに
誤った値を生成することを実際に確認した（2026-08-19、
`[[QUALITY-GATES-EPIC-1]]`本線3のフォールバック向き反転〈案A〉検証時に
発見）。現在は案D（GP法入力の整合性ガード）により、この年度はGP法を
使わずpretax調整法（$6,370,187、元の値と同一）へフォールバックする設計に
なっており、実害は遮断済み。ただし根本原因（revenue取得失敗）自体は
未解消のまま残っている。

**全105銘柄・全年度の実測で、他に該当する年度は無かった**（`revenue=0`
または未取得なのに`gross_profit`が非ゼロという組み合わせは、標準タグ
採用済みで実害ゼロの数件〈AMD/CELH/JNJ/KO等の`revenue`未取得だが
`gross_profit`は個別に正常取得されている古い年度、IONQ 2020〈標準タグ〉〉
を除き、GP法が実際に計算されうる年度としてはVRT FY2018のみ）。

#### 対応方針
`_extract_values_best_candidate()`等のrevenue抽出ロジックで、VRT FY2018
に該当するcompany_facts.jsonのタグを実際に調査し、取得可能な候補タグが
あるかを確認する。実装は本項目のスコープ外（登録のみ）。

**`[[QUALITY-GATES-EPIC-1]]`ゲート1のyfinance照合をrevenueへ横展開すれば、
この種の破綻は取得時点で検知できる**（CHECK-35のoperating_income照合と
同型のパターンをrevenueに適用すれば、
`revenue=0`という取得失敗を、yfinance実測値との突合で即座に検知できる）。
ただし2026-08-19時点の優先順位では、revenue横展開は他3件（Layer3範囲
実測・ゲート3対象棚卸し・`RestructuringCharges`追加）より後回し
（`CHAT_RULES.md`「本線の定義」参照）。

#### 着手条件
なし

### [MARKETDATA-AS-IS-AUDIT-PY-OMITTED-1] INPUT_DATA_AS_IS.md 1-B節の「11ファイル」がcommon/sec_data/audit.pyを見落としていた
**優先度:** 低（記録のみ、ドキュメント訂正で対応完了）
**分類:** ドキュメント正確性 / 調査精度
**登録日:** 2026-08-07
**発見:** `common/market_data/`新設事前調査（チャット記録、2026-08-07）

#### 内容
`INPUT_DATA_AS_IS.md` 1-B節の調査方法は「`src/`配下でヒットする
14ファイル」を起点にしており、`common/`配下は探索範囲外だった
（`discover/`配下のSTONKS SILOは別途手当て済みだったが、同種の
見落としが`common/`配下には残っていた）。`common/sec_data/audit.py`
が`import yfinance`をローカルスコープで2箇所（`audit_beta_drift()`
等）行っており、`SEC_Data_Audit.yml`（`workflow_run`で"SEC Data
Update"完了後に連鎖実行、独立cronなし）から呼ばれる本番稼働中の
診断ツールだが、11ファイルの母集団には含まれていなかった。

#### 対応
`INPUT_DATA_AS_IS.md` 1-B節に12番目のファイルとして追加、総数表記を
11→12件に訂正（別途ドキュメント修正で対応）。

#### 着手条件
なし。

---

### [STOCKHTML-LAYER3-PUBLISH-PIPELINE-MISSING-1] stock.htmlのLayer3切替は新規公開パイプライン構築が前提だが、現時点で着手しない
**優先度:** 低（対応不要、記録のみ）
**分類:** アーキテクチャ上のブロッカー / 着手見送り
**登録日:** 2026-08-07
**発見:** フェーズD Step2-5事前調査・着手要否投資調査（チャット記録、2026-08-07）

#### 内容
stock.htmlは`normalized/`を直接fetchしており、Layer3切替には
Layer3ストアをJSON化して`docs/`配下に公開する新規パイプライン
（GitHub Actions拡張）が必要。技術コストは低い（既存`SEC_Data_
Update.yml`への追加ステップとして実装可能、ファイルサイズ2〜4MB
程度、計算コストも軽微）が、以下の理由で着手を見送る：
- 現状に緊急性のある実害はゼロ（is_ytdフィルタ漏れは実データで
  未発現、DAフィールド欠如29%も表示のみへの影響でフォールバックも
  堅牢）
- CF滝グラフはページ最下部の補助的機能、2.5ヶ月間安定稼働
- 着手すれば`[[LAYER3-FETCHER-SELECTION-PHILOSOPHY-MISMATCH-1]]`と
  同じ「filed日最新優先 vs own-year優先」の検証課題が再発する
  可能性がある（未検証）

#### 着手条件
なし。DAフィールド欠如が実際にユーザー影響を持つと判明した場合、
またはstock.htmlの利用実態が変化した場合に再検討。

---

### [STOCKHTML-YTD-FILTER-BUG-SUSPECT-1] stock.htmlのJS側フィルタがis_ytdを除外していない（構造的リスク、現状未発現）
**優先度:** 低
**分類:** バグ疑い（潜在的、実データでは未発現）
**登録日:** 2026-08-07
**発見:** フェーズD Step2-5事前調査・着手要否投資調査（チャット記録、2026-08-07）

#### 内容
JS側`getQ()`は`.filter(e => e.is_annual === false)`のみで`is_ytd`を
除外しない。`normalizer.py`側がYTDエントリを標準四半期値へ変換完了
させてから`normalized/`へ永続化しているため、現状データ（105銘柄×
5フィールド全数実測）には未解決のYTD残骸が1件も存在せず、実害なし。

#### 着手条件
なし。将来`normalizer.py`側の変換ロジックが変わり未解決YTDが
残存するようになった場合に再検討。

---

### [LAYER3-FETCHER-SELECTION-PHILOSOPHY-MISMATCH-1] STONKS SILO fetcher.py・dcf_validity_checker.py（check_c_data_jump）の年次データがparser.py（own-year優先）を直接参照している一方、Layer3（filed日最新優先）とは選択思想が異なる
**優先度:** 低（対応不要、記録のみ。案2〈現状維持〉採用により
2026-08-07に高→低へ格下げ）
**分類:** 設計判断確定（恒久的な例外扱い）
**登録日:** 2026-08-07
**更新日:** 2026-08-07（対応方針確定。優先度を高→低に格下げ）
**発見:** フェーズD Step2-2事前調査（チャット記録、2026-08-07）

#### 内容
Layer3の年次エントリ選択（`_process_entries()`→`select_latest_filed()`）
は「同一end日付の全候補中、filed日最新」を機械的に採用する設計。
parser.py（`fetcher.py`・`dcf_validity_checker.py::check_c_data_
jump()`が直読みする`annual_*.json`の生成元）は`is_own_data`判定・
`_resolve_bs_entity_mixing()`等で「当年自身の10-K（own-year）」を
優先する設計。両者は元々別目的（Layer3のこの設計は四半期のYTD
チェーン解決・10-K/A訂正取り込みのため）で作られており、PL/CF系
フィールド（10-Kで2〜3年比較列を持つ）でほぼ全銘柄・全年度異なる
値を拾う。AVAV FY2022 revenueで実測検証済み（現状値445,732,000＝
own-year10-K、Layer3選択値＝2年後の10-Kの比較列が同一期間を
再採録したもの）。BS（残高、通常2年比較）で差分ゼロなのはこの説明と
整合。

フェーズD Step2-5事前調査（2026-08-07）で、`dcf_validity_checker.py::
check_c_data_jump()`（`report_consistency_check.py`のWARN-21として
本番稼働中）も同一のデータソース・同一の参照パターンで、この課題を
同様に引き継ぐことを確認した。

#### 対応方針（確定・2026-08-07）
**案2を採用**：Layer3切替を見送り、現状維持。`fetcher.py`・
`dcf_validity_checker.py`（`check_c_data_jump()`）は`data/
annual_*.json`（parser.py経由）の直読みを継続する。

**採用理由**：Layer3の「filed日最新優先」は、修正再表示（10-K/A等）を
正しく反映するケースと、タグ定義変更等で不正確な値を拾うケースを
区別できない不確実な方式である一方、parser.pyの「own-year優先」は
一貫した基準を持つ実績のある方式。正確性の確実性を犠牲にしてまで
統一する理由がない。

3スキーマ並存のうち、この2ファイル分（`fetcher.py`・
`dcf_validity_checker.py`の該当関数）は恒久的な例外として残る。

#### 着手条件
なし。将来、修正再表示の理由自動判定の仕組み（フェーズF/G
「filing_text吸収」関連）が実現した場合に再検討する。

---

### [HYPECORE-SUBSTAGE-LAYER3-UNVERIFIED-1] detect_substage()がrev_yoy・eps_surpriseを直接参照するが、Layer3切替時の影響が未検証
**優先度:** 低（`determine_stage()`〈ステージ本体〉への影響はゼロと
確認済み、substageは別ロジックのため範囲外のまま）
**分類:** 未検証事項
**登録日:** 2026-08-07
**発見:** フェーズD Step2-4事前調査（チャット記録、2026-08-07）

#### 内容
substage（内部フェーズ）はrev_yoy・eps_surpriseを直接参照する別
ロジックのため、stageとは独立してLayer3切替の影響を受ける可能性が
ある。Step2-4実装時のスコープには含めない。

#### 着手条件
Step2-4実装完了後、必要であれば追加調査。

---

### [TAIL-SHARESDILUTED-Q4-TIMING-RISK-1] TANUKI TAILのeps_diluted計算が、レビュー生成タイミングによってはCommonStockSharesOutstanding（期末発行済株式数）由来のSharesDilutedを拾う構造的リスクを持つ
**優先度:** 低（現時点で10銘柄全数、最新四半期はWeightedAverage側が
採用されており実害なし）
**分類:** 潜在リスク
**登録日:** 2026-08-07
**発見:** フェーズD Step2-3事前調査（チャット記録、2026-08-07）

#### 内容
`[[LAYER3-SHARESDILUTED-TAG-GAP-1]]`の対応（source_tagフィルタで
CommonStockSharesOutstanding由来を除外）はpipeline.pyの希薄化率
計算箇所に限定実装されており、共通アクセサ（reader.py/
layer3_builder.py）自体には手を入れていない。TANUKI TAILの
`quarterly_review_generator.py`・`tail_dcf_bridge.py`は
`get_latest_quarterly()`を直接呼ぶため、この既存フィルタの恩恵を
受けない。直近四半期がQ4に当たるタイミング（WeightedAverage系タグが
四半期報告されない期）でレビューが生成された場合、eps_diluted計算が
期末発行済株式数ベースの値を使ってしまう可能性がある。

#### 着手条件
なし。実際にQ4タイミングでの計算誤りが発生した時点、または
`[[LAYER3-SHARESDILUTED-TAG-GAP-1]]`の対応をpipeline.py外にも展開する
判断がされた時点で再検討。

---

### [FETCHER-PY-BS-FIELDS-DEAD-KEYS-1] fetcher.pyの_BS_FIELDSでtotal_debt・shares_outstanding・shares_dilutedがannual_*.jsonに実在しないキーを参照しており常にNone
**優先度:** 低（analyzer.pyがこの4項目を参照しないため現状無害）
**分類:** バグ（死んだコード）
**登録日:** 2026-08-07
**発見:** フェーズD Step2-2事前調査（チャット記録、2026-08-07）

#### 内容
実際は`long_term_debt`/`short_term_debt`が別名、shares系は`shares`
セクション別置き。Layer3移行とは無関係の独立した既存バグ。

#### 着手条件
なし。実害が発生した時点で対応。

---

### [FINTREND-SM-JOBY-NONE-1] financial_trend_calculator.pyのSMフィールドがJOBYでNone化する（Layer3切替時）
**優先度:** 低（既知の`[[SCHEMA-NORMALIZED-ISSUES-1]]`②の帰結、
`[[LAYER3-ROIC-WACC-NONE-4TICKERS-1]]`と同型・同じ判断基準を適用）
**分類:** 仕様変更（改善）
**登録日:** 2026-08-07
**発見:** フェーズD Step2-2事前調査（チャット記録、2026-08-07）

#### 内容
normalized側はSGA総額へのフォールバック値を保持していたがLayer3側は
`selling_and_marketing`のみを候補としNoneを返す。正しい方の挙動として
受け入れる。

**補足（2026-08-07、実装時に判明）**: `financial_trend_calculator.py`の
`compute_vectors()`は`VECTOR_FIELDS`（Revenue/GrossProfit/OperatingIncome/
RD/NetIncome/OCF/CapExの7項目）のみを処理しており、`SUB_FIELDS`
（SM・SBC）は定義されているだけで`compute_vectors()`から一切呼び出され
ていない未使用の定数と判明した。そのため本項目のJOBY None化は
`_get_quarterly_entries()`単体の挙動としては真だが、**現状の
`results.json`出力（`financial_vectors`）には実影響がゼロ**である。
将来`SUB_FIELDS`が実際に配線された場合に初めて表面化する。

#### 着手条件
SM/SGA概念混同問題（`[[SCHEMA-NORMALIZED-ISSUES-1]]`②）の根本解消時に
再検討。

---

### [RCAT-2016Q3-ORPHANED-QUARTERLY-FILE-1] RCAT 2016Q3のquarterly_*.jsonが新ロジックで未上書きのまま残存
**優先度:** 低
**分類:** データ品質 / SEC EDGARデータ（新DB構築プロジェクト フェーズ1）
**登録日:** 2026-08-05
**発見:** `[[SECDATA-STORAGE-FRAGMENTATION-1]]` quarterly_*.json YTD→SA修正の
検証中（メモリ上シミュレーションと実書き込み結果のSBC集計に±1件の
差異が発生、原因調査で発見）

#### 内容
`parser.py::save_parsed_data()`は`parsed["quarterly"]`に存在する
四半期キーのみを上書き保存する。RCATの`2016Q3`は、当該四半期の
XBRL申告が極端に薄く（`AllocatedShareBasedCompensationExpense`タグの
単独9ヶ月YTD候補〈起点四半期なし〉のみで、他フィールドも同様に
差分計算不能）、統一アルゴリズム適用後は**どのフィールドも解決できず
四半期キー自体が`parsed["quarterly"]`から消滅**した。結果、
`common/sec_data/data/RCAT/quarterly_2016Q3.json`は今回の一括再パースで
一切上書きされず、修正前（YTD値をSA値として誤保存していた）の内容が
そのまま残存している（`stock_based_compensation=78472`は9ヶ月YTD値）。

全105銘柄・2,296ファイルの再パースでこのパターンに該当するのは
RCAT 2016Q3の1ファイルのみと確認済み（全銘柄横断で「旧ファイルには
存在したが新抽出結果には四半期キー自体が存在しない」ケースを検索）。

#### 実害
現時点でゼロ。`data/quarterly_*.json`のpl/cf区分を直接参照する本番
消費者は存在しない（`[[SECDATA-STORAGE-FRAGMENTATION-1]]`調査で確認済み）。

#### 対応方針（未実施）
残存ファイルを放置するか、明示的に削除する（「その四半期は再現不能」と
正直に示す）か、設計判断が必要。優先度は低（1ファイルのみ・実害ゼロ・
将来のアクセサ実装時に再検討で十分）。

### [PARSER-MERGED-TAG-MIXING-RISK-1] parser.py::_extract_values_merged()が、Layer3が[[LAYER3-FALLBACK-STALE-TAG-PRIORITY-1]]で廃棄した危険パターン（複数タグの生エントリを先に混ぜてからYTD変換）と同型の構造を持つ疑い
**優先度:** 低（Layer3統一方針確定により、data/系統の重要度自体が
低下したため、中→低に格下げ）
**分類:** バグ疑い / 構造的リスク
**登録日:** 2026-08-06
**発見:** `SEC_EDGAR_LAYER_DESIGN.md`との整合性確認調査（チャット記録、
2026-08-06）

#### 内容
`layer3_builder.py::_merge_candidate_entries()`は、候補タグごとに
独立して`_process_entries()`→`_normalize_field_entries()`（YTD→単四半期
変換を含む）を完了させてから、正規化済み系列同士をend_date単位で
マージする設計になっている。これは当初の実装（生エントリを先に
end_date単位でマージしてからYTD→単四半期変換する順序）が、異なる
タグ由来のエントリが同一end_dateで競合した際にFYチェーン判定を
破壊し、YTD差分計算が中間四半期を1つ読み飛ばして2四半期分を1四半期
として誤算出するバグを引き起こした（CPRT・PEP等6銘柄・20エントリで
実データ確認、[[LAYER3-FALLBACK-STALE-TAG-PRIORITY-1]]）ことを踏まえた
意図的な設計変更。

一方、`common/sec_data/parser.py::_extract_values_merged()`
（merge_all_tags対象フィールド向け、`SECDATA-STORAGE-FRAGMENTATION-1`
2026-08-05実装のSA/YTD統一アルゴリズム）は、全キー（＝複数タグ）を
早期終了せずループし、四半期の生候補`(fy, fp, start, end, val)`を
タグ区別のないまま単一の`quarterly_candidates`リストへ蓄積してから、
`_resolve_quarterly_values()`でまとめて解決する構造になっている。これは
Layer3が明示的に廃棄した「生エントリを先に混ぜてから変換」という
旧パターンと同型であり、複数タグが競合する銘柄・フィールドで同種の
誤算出が発生する構造的リスクを持つ疑いがある。

なお、単一タグのみを扱う`_extract_values_best_candidate()`経路は
タグ混入の余地がないため対象外。939b8f57fコミット時の検証（全105銘柄
再パース結果が独自シミュレーションと完全一致）は旧parser.py実装との
内部整合性確認であり、Layer3側の値との突合ではないため、本リスクを
検出できるものではない。実データでの影響有無は未検証。

#### 着手条件
merge_all_tags対象フィールド一覧の洗い出し・実データでの影響有無検証
から。ただしdata/系統の位置づけがLayer3統一に伴い補助的になったため、
緊急性は低い。

### [LAYER3-SNPS-STALE-TAG-PRIORITY-1] SNPS FY2022のRevenueで、Layer3の候補タグ優先順位が後発の修正再表示（restatement）を拾えず、原本の古い値に固定される構造的リスク
**優先度:** 低（現時点でMoat Score計算への実害なし、将来的リスクの記録）
**分類:** 設計上の潜在リスク
**登録日:** 2026-08-06
**発見:** フェーズD Step2-1事前調査（チャット記録、2026-08-06）

#### 内容
SNPS FY2022（2022-10-31）で、原本$5,081,542,000（`Revenues`タグ、
2022年10-K）が、後に$4,615,714,000へ修正再表示
（`RevenueFromContractWithCustomerExcludingAssessedTax`タグ、2024年
10-K）されたが、Layer3の候補優先順位は`Revenues`が固定で先頭のため、
修正再表示を拾えていない。SEC EDGARで裏取り確認済み。

現時点では`rev_annual[-3:]`の対象外（FY2023/24/25は完全一致）のため
実害なし。将来的にFY2022が対象窓に入る用途、または他の類似ケース
（同種のrestatementパターン）で実害化しうる。

#### 着手条件
なし。実害が発生した時点、または類似ケースの横断調査を行う際に
再検討する。

### [LAYER3-ROIC-WACC-NONE-4TICKERS-1] COHR/LLY/JNJ/KLACのROIC-WACC比率・Moat ROICが、Layer3切替に伴いNone表示になった
**優先度:** 低（意図的な仕様、既知のSM/SGA概念混同問題の帰結）
**分類:** 仕様変更（改善）/ ユーザー影響あり
**登録日:** 2026-08-06
**発見:** フェーズD Step2-1実装時（チャット記録、2026-08-06）

#### 内容
normalized/時代は間違った値（SGA総額を誤混入）でROIC-WACC比率を
計算していたが、Layer3切替後はselling_and_marketingが正しく分離
されたため、3フィールド共通end日のintersectionが0件となりNoneを
返すようになった。`[[SCHEMA-NORMALIZED-ISSUES-1]]`②SM/SGA概念混同
問題の根本解消（別タスク）まで、この4銘柄はROIC-WACC比率非表示の
まま。

#### 着手条件
SM/SGA概念混同問題の解消時に再検討。

### [DEFICIT-SCORE-CEILING-95-1] STONKS SILO DEFICIT分類、赤字企業の実質上限95点
**優先度:** 低
**分類:** 設計上の制約 / STONKS SILO
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ8（セッション終了時ブラッシュアップで39件起票から漏れていたものを追加起票）

#### 内容
`analyzer.py::_deficit_verdict()`の黒字状況(10pt)項目は、`is_profitable`が
真の場合のみ10ptを付与し、赤字企業（`net_income is not None`のみが条件の
`elif`分岐）は最大5ptしか取れない（`analyzer.py:453-457`）。売上成長40pt＋
投資姿勢30pt＋粗利率20pt＋黒字状況10pt＝100点満点の設計だが、STONKS SILOの
対象銘柄は原則として赤字企業（プレレベニュー/赤字拡大企業の投資適合性
評価が目的）であるため、実質的な達成可能上限は95点になる。

#### 実データでの影響確認（本追加起票時に実施）
`docs/value-monitor/stonks-silo/data/results.json`（現行25銘柄）を確認した
ところ、**QBTS が実際に95.0点（現行データの最高スコア）に到達しており、
本問題が理論上の懸念ではなく現行データで実際に発生していることを確認**
した。ただし`verdict`判定の閾値（`GOOD_DEFICIT>=65`／`WATCH>=35`／
`BAD_DEFICIT`未満）はいずれも95点を大きく下回るため、**この5pt差が
verdict分類（GOOD_DEFICIT/WATCH/BAD_DEFICIT）を変えることはない**。
実害は「なぜ赤字企業は100点に到達できないのか」という数値スケールの
解釈上の疑問に留まり、投資判断そのものへの影響は現行データでは
確認されなかった。以上を踏まえ優先度は低のまま登録する。

#### 対応方針
黒字企業（`is_profitable=True`）は既に`verdict="PROFITABLE"`として
score非依存の別カテゴリに分岐するため、スコア自体を100点満点で比較する
必要があるのは実質的に赤字企業同士のみである。「赤字企業内での相対
比較」であることを踏まえ、100点満点表記を95点満点表記に変更するか、
現状維持のまま「黒字状況」項目の配点自体を見直すかを判断する。

#### 着手条件
なし

---

### [TAILKPI-FIELD-VALIDATION-GAP-1] TANUKI TAIL KPI提案確定時の個別フィールド妥当性検証未実装
**優先度:** 低〜未定
**分類:** データ品質 / TANUKI TAIL
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ2（セッション終了時ブラッシュアップで39件起票から漏れていたものを追加起票）

#### 内容
TANUKI TAILのKPI提案確定フロー（AS-IS-425〜436、`kpi_proposer.py`のGrok
提案を人間が画面で確認・編集して確定する）において、`workflow_write.py:
149-152`は`kpis`が空リストでないことのみをチェックしており、個別
フィールド（`warning_threshold`の数値妥当性、`xbrl_tag`の形式等）の
検証ロジックは確認できなかった。Discoverのconfig系（[[DISCOVER-CONFIG-
DUAL-MGMT-1]]、バリデーション0件）ほど深刻ではない（コンテナレベルの
非空チェックは存在する）が、個別フィールドの誤入力を防ぐ仕組みがない
点は同種のリスクである。

#### 対応方針
`warning_threshold`が数値であること・`xbrl_tag`が既知のタグ命名規則に
従っていること等、個別フィールドレベルのバリデーションを
`workflow_write.py`に追加することを検討する。

#### 着手条件
なし

---

### [ERP-DUAL-CALC-1] ERP①②の重複計算
**優先度:** 低
**分類:** 保守性 / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ3（AS-IS-055/056）

#### 内容
`pipeline.py`内の`_save_result()`と`_generate_report()`が、どちらも
`forward_eps`/`current_price`/`risk_free_rate`を個別に読み直して同じERP
計算式を独立に再計算している。共通関数化されていないため、片方だけ修正
すると①②が食い違う保守リスクがある。

#### 対応方針
共通関数に統合する。

#### 着手条件
なし

---

### [MOAT-CATALOG-DUP-1] moat_score（AS-IS-026/028）のカタログ重複
**優先度:** 低
**分類:** ドキュメント整合性
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ4

#### 内容
AS-IS-026とAS-IS-028は同一の`calculate_moat_score()`戻り値を指す重複
カタログエントリ。過去のインベントリ作成過程で同じ関数の出力が2つの
異なるAS-IS-IDとして重複記録されている。

#### 対応方針
どちらか一方に統合する（コード修正は不要、カタログ整理のみ）。

#### 着手条件
なし

---

### [TANUKI-VALUATION-MISC-GAPS-1] TANUKI VALUATIONの軽微な構造的ギャップまとめ（PERフォールバック欠如・EV/EBITDA負値格納・net_debt符号エイリアス・v0_adjusted死フィールド・Runway cash算出相違・mature_profit S&M欠落・根拠不明な定数）
**優先度:** 低
**分類:** データ品質 / TANUKI VALUATION
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ3・4・6

#### 内容
①PS/PEG/EV-EBITDAはTANUKIデータ欠落時にHypeCore自身の`poc.json`へ
フォールバックするが、PERだけはTANUKIの`comps.per`のみを参照しフォール
バックしない（`detail.html:550`）。②`hypecore.py:130`は負のEV/EBITDAを
そのまま格納する設計（現状UIガードで実害なしだが将来別画面追加時に
誤表示リスク）。③`net_debt = -net_cash`という単純な符号反転が「正=
ネットキャッシュ」「正=純負債」という2つの概念を並存させており、
横断参照コードで符号取り違えリスクがある。④`v0_adjusted`（AS-IS-008）は
`v0_adjusted = v0`という代入のみで実質的な死フィールド（コメント自体が
後方互換用と明記）。⑤Runway概念がTANUKI（`SECReader.get_net_cash()`
経由、セクターガードあり）とSTONKS SILO（`annual_{yr}.json`の`bs`単純
合算のみ）でcash算出経路が異なる。⑥`research_and_development`・
`selling_and_marketing`がSEC非開示の場合`or 0`で「支出ゼロ」として
足し戻され、`mature_profit`が実態より低く算出される。⑦`growth_floor
(15%)`・`growth_cap(50%)`・`market_return(10%)`の根拠がコード内に一切
記載されていない。

#### 対応方針
各項目とも影響が限定的なため、他の関連タスク（[[RISK-FREE-RATE-
HARDCODE-1]]等）着手時に合わせて解消することを推奨する。

#### 着手条件
なし

---

### [HYPECORE-MISC-NAMING-GAPS-1] HypeCoreの軽微な命名・観測性ギャップまとめ（buy_hold_ratio誤称・fcf_yield誤称・200MA乖離の別ソース並存・ma200_mom未出力・出来高指標の粒度相違・lifecycle基準相違）
**優先度:** 低
**分類:** 命名・観測性 / HypeCore
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ5・7

#### 内容
①`buy_hold_ratio`（AS-IS-108）は名称と実体が食い違う。実際の計算式
`(strongBuy+buy)/(strongBuy+buy+hold+sell+strongSell)`には`hold`が
分子に含まれておらず、実質的に「Buy比率」である。②`fcf_yield`
（AS-IS-096）も名称と実体が食い違う。分子はOCF（CapEx控除前）その
ものでありFCFではなく、年率換算もされていない。③AS-IS-076と
AS-IS-087は同名「200MA乖離」だがAS-IS-087はHypeCore自前計算
（`rolling(200).mean()`）、AS-IS-076はyfinance内部計算済み値
（`twoHundredDayAverage`）という別データソース。④`ma200_mom`は
ステージ判定の複数の重要分岐で使われるがJSON出力に一切含まれず、
判定根拠を事後検証できない。⑤`volume_ratio`（AS-IS-091、日次20日平均
比）と`vol_surge`（AS-IS-092、月次6ヶ月移動平均比）は「出来高急増」系
指標として並存するが時間窓が全く異なる。⑥ライフサイクル判定の
フォールバック元`revenue_growth`（yfinance）と`rev_yoy`（SEC EDGAR
TTM%）は算出基準が異なる別指標であり、どちらが使われるかは単に
`revenue_growth`がnullかどうかで暗黙に決まる。

#### 対応方針
①②は`NAMING_CONVENTIONS.md`規則3（誤称の禁止）に基づきリネームを
検討する。③⑤⑥は接尾辞での区別（規則1・2）を検討する。④はJSON出力に
`ma200_mom`を追加する。

#### 着手条件
なし

---

### [DISCOVER-PRECISION-GAPS-1] Discoverの精度上の軽微なギャップ（テーマ連続登場の文字列部分一致・macro_themesの見た目上の更新）
**優先度:** 低
**分類:** データ品質 / Discover
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ7

#### 内容
①`themeStreakMap`（`docs/discover/index.html:452-457`）は今週と過去4週
分のテーマ名を`hn.includes(name) || name.includes(hn)`という単純な部分
文字列一致で比較する。テーマ名はGrokが毎週自由生成する20字以内の文字列
のため、同一の実質的テーマでも表現が微妙に変わると継続と判定されず
（偽陰性）、逆に無関係な2テーマが偶然共通の部分文字列を持つと誤って
連続登場と判定される（偽陽性）リスクがある。②`collect.py:main()`は
日曜以外`macro_themes`を前回`daily_report.json`から引き継ぐが、
`daily_report.json`自体の`generated_at`は毎日更新されるため、ユーザーが
「今日生成された最新のテーマ」と誤認するリスクがある。

#### 対応方針
①ID・埋め込みベースの意味的一致への変更を検討する②レポート全体の
タイムスタンプとは別に各テーマオブジェクトの`generated_at`（週次生成日）
を画面上でも明示する。

#### 着手条件
なし

---

### [MACRO-THRESHOLD-INCONSISTENCY-1] MACRO PULSEの閾値不一致・重複判定の軽微な構造的リスク（YC閾値3セット・dedupe_new_rows()のCFNAI/Sahm無条件適用）
**優先度:** 低
**分類:** データ品質 / MACRO PULSE
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ10

#### 内容
①10Y-2Yスプレッドの判定閾値が用途によって3セット存在する（ティッカー
表示のINVERTED/FLAT/NORMAL: -0.2/0.5、RECESSION RISK SCOREのステップ
関数: -0.5/0/0.5の4段階、LAYER2健全性バーのbull/bear: 0.5/-0.2）。②
`dedupe_new_rows()`の重複判定は`obs_to_release_lag`に基づく日数窓＋
完全一致する`actual`値のみで行われ、指標ごとの「値の反復が正常で
ありうるか」を区別する例外リストがない。Sahm Ruleが複数月連続で0.00に
近い値を取る、CFNAI MA3が安定期に近似値を繰り返す、といった正当な
ケースを重複と誤判定して新規データ行を捨てるリスクが構造的に残る。

#### 対応方針
①閾値セットを統一するか、用途別に異なる理由を明示する②指標別の
「反復許容」例外リストを`dedupe_new_rows()`に追加する。

#### 着手条件
なし

---

### [MACRO-PULSE-STALENESS-DISCLOSURE-GAP-1] 景気サイクルフェーズ複合スコアで、CFNAI・Building Permitsに鮮度注記が欠けている
**優先度:** 中（複合スコアの22%〈CFNAI 12%＋Building Permits 10%〉が
実測約7週間遅れのデータに基づくが、閲覧者がこれに気づく手段がない）
**分類:** UI/UX / データ鮮度の開示不足
**登録日:** 2026-08-15
**発見:** MACRO PULSEにおける遅延系列の扱い確認調査（チャット記録、
2026-08-15）

#### 内容
`docs/market-monitor/macro-pulse/index.html`の「景気サイクルフェーズ」
複合スコア（`computeCurrentScore()`、合計100%）で、Michigan Sentiment
（8%）のみ「※FREDは1ヶ月遅延公開のため、最新発表値と異なる場合が
あります」という鮮度注記があるが、より大きなウェイトを持つCFNAI
（12%）・Building Permits（10%）には注記がない。

FRED自身の再公開遅延（大学等の発表からFRED反映まで）が実測で約
7週間（49日）規模であることを、Michigan Consumer Sentiment
2026年6月分の実データ（大学発表2026-06-12、FRED反映検知
2026-07-31）で具体的に確認済み。`obs_to_release_lag`設定
（大学の速報発表タイミングのみを表す、10日）とは別に、この
FRED再公開遅延が上乗せされる構造。

技術的制約: `idxLatestAsOf()`（901-912行目）が`.actual`（値）のみを
返し観測日情報を構造的に破棄する実装のため、現状は各指標の
ツールチップに観測日自体を表示する手段がない。

#### 対応方針の選択肢（未実装）
1. CFNAI・Building Permitsへの鮮度注記追加（低コスト、Michigan
   Sentimentと同様のdesc文言追加のみ）
2. `idxLatestAsOf()`が観測日も返すよう拡張し、各指標のツールチップに
   「観測日: YYYY-MM-DD」を表示できるようにする（中コスト、構造変更）
3. AI週次レポートのプロンプト（`05_main.py` 1626-1631行目）へ各指標の
   観測月を付記し、AI生成コメントが遅延データを「直近」と誤って
   記述しないようにする（低〜中コスト）

#### 着手条件
なし。優先度に応じて対応方針を選択の上、実装する。

---

### [KPI-UNIT-HARDCODE-USD-1] TANUKI TAILのkpis.{kpi_name}.unitが常時USD固定
**優先度:** 低
**分類:** バグ / TANUKI TAIL
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ7（AS-IS-419）

#### 内容
`xbrl_segment_fetcher.py:fetch_ticker()`は抽出したKPIの`unit`欄に無条件
で`"USD"`を設定する。同じ関数内で「整数に近い値（USD金額）はint、小数値
（比率）はfloat」と値の型を使い分けている（コード自身が比率KPIの存在を
認識している）にもかかわらず、`unit`フィールドは比率KPIであっても
"USD"のままになる。

#### 対応方針
値の型判定ロジックと連動させ、比率KPIには`"ratio"`等の適切な`unit`を
設定する。

#### 着手条件
なし

---

### [STONKS-FINANCIAL-VECTORS-RELATIVE-1] financial_vectorsのpercentile/angle/lengthが相対順位であることの明示
**優先度:** 低〜未定
**分類:** ドキュメント整合性 / STONKS SILO
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ5（AS-IS-135/175/176）

#### 内容
`financial_vectors`のpercentile・angle・lengthは絶対的な変化率ではなく、
同時点の全STONKS SILO銘柄集合に対する相対順位である。新規銘柄の追加・
除外のたびに、対象銘柄自身のデータが変わっていなくても他銘柄の
percentileが変動しうる。過去の`results.json`保存値と時系列比較する際は
この母集団変動の影響を考慮する必要がある。

#### 対応方針
コード修正ではなく、画面上または`results.json`のメタデータとして
「相対順位である」旨・母集団サイズを明示することを検討する。

#### 着手条件
なし

---

### [EPS-267-MIXED-PASSTHROUGH-1] AS-IS-267内でパススルー値と計算値が混在
**優先度:** 低〜未定
**分類:** ドキュメント整合性 / EPS Analyzer
**登録日:** 2026-07-23
**発見:** `FIELD_DEFINITIONS.md`フェーズ4

#### 内容
AS-IS-267の`gaap_eps`/`gaap_net_income`/`diluted_shares_used`はXBRL値の
パススルー（計算なし）である一方、`adjusted_eps`/`adjusted_net_income`は
`net_adjustment_total`の加算を伴う真の計算値であり、同一AS-IS内に性質の
異なるフィールドが混在する。

#### 対応方針
コード修正は不要。将来カタログを再整理する際に、パススルー値と計算値を
分離したAS-ID採番を検討する。

#### 着手条件
なし

---

### [TTM-SBC-QUARTERS-GAP-1] build_rice_annual_shape()のSBCがquarters完全性チェック対象外
**優先度:** 低〜未定
**分類:** データ品質 / SECデータ取得層
**登録日:** 2026-07-18
**発見:** TRUST-SUMMARY-EPIC-1ステップ1棚卸し調査時の副次発見

#### 内容
`data_fetcher.py::build_rice_annual_shape()`は、OCF/CapEx/Revenue/
NetIncomeの4フィールドについて`_quarters_complete()`（quarters_used≥4）で
完全性を判定してから出力対象に含めるが、同じ辞書内に含まれる`SBC`
（stock_based_compensation）はこの完全性チェックの対象外のまま無条件で
出力される（298行目付近、`_quarters_complete()`呼び出し引数にSBCが
含まれていない）。RD/SMがrice.py側で意図的にNone許容（0扱い・警告ログ
のみ）とされているのとは異なり、SBCについては「意図的な許容」なのか
「チェック漏れ」なのか、現時点では未確認。

#### 対応方針（未定）
`build_rice_annual_shape()`のSBC出力が実際にquarters_used<4の不完全な
値を含むケースがあるか実データで確認し、意図的な設計か単純な漏れかを
切り分けてから対応要否を判断する。

#### 着手条件
なし

---

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

### [DEAD-CODE-AUDIT-BATCH-1] common/sec_data配下の陳腐化・未使用ファイル一括監査（削除要否判断）
**優先度:** 低
**分類:** 保守 / リポジトリ整理
**登録日:** 2026-07-13〜2026-07-18（統合日: 2026-08-03）
**発見:** [[TICKER-DIRECT-ACCESS-GUARD-1]]実装時の全リポジトリスキャン・
[[ARCH-DATA-1]]残課題③調査時・[[GATE2-PHASE3B-1]]③-b事前調査時

#### 内容
以下4ファイルは、いずれも「全リポジトリでのimport/参照有無をgrep確認
→未使用と確認できれば削除、継続利用の可能性があれば個別対応」という
共通の判定基準で削除要否を判断できる状態にある。1つの監査作業単位として
まとめて調査・判断する。

**対象ファイルリスト**:

① `common/sec_data/phase1_scan.py`（旧PHASE1-SCAN-CLEANUP-1、優先度
低）: `os.listdir(DATA)`で`docs/value-monitor/tanuki_valuation/data/`を
無条件スキャンし、tanukiフラグを見ずに全ディレクトリを対象銘柄として
扱う。ハードコードされた`TODAY = date(2026, 6, 11)`から、2026-06-11頃に
使われた一回限りの診断スクリプトと推測される。CIワークフロー・他
スクリプトからの参照なし（grep全数確認済み）。一回限りの診断スクリプト
であることを確認できれば削除、継続利用の可能性がある場合は
`tickers.get_tanuki_tickers()`経由に修正する。

② `src/value/tanuki_valuation/backfill_history.py`（旧BACKFILL-
HISTORY-CLEANUP-1、優先度低）: `os.listdir(DATA_ROOT)`で無条件スキャン
し、tanukiフラグを見ない。ファイル内コメント「May 14-16 History
Backfill (v8.2)」から特定日付向けの一回限りのバックフィルスクリプトと
推測される。一回限りのバックフィルスクリプトであることを確認できれば
削除、継続利用の可能性がある場合は`tickers.get_tanuki_tickers()`経由に
修正する。

③ `common/sec_data/quality_checker.py`（旧QUALITY-CHECKER-CLEANUP-1、
優先度低）: 独自のQ01〜Q13チェックカタログ、独自の`TICKER_RESTRICTIONS`
定義を保持するが、全リポジトリを検索した結果どこからもimportされて
いない未使用コードと判明している。同ファイル内の`TICKER_RESTRICTIONS`は
コメント上「quarterly.pyと同期」とあるが実態は非同期で、SOFI・IONQの
エントリ（quarterly.py側には存在）を欠いている。
`report_consistency_check.py`（CHECK-N命名）・`quality_checker.py`
（Q0N命名）・`registration_validator.py`（P1-xxx命名）と、既に3種類の
独立したチェックカタログ・命名規則が併存しており、本ファイルは実質的に
その一つが死蔵された状態。一度も呼ばれていないことを再確認できれば
削除する、何らかの理由で将来利用予定がある場合は`TICKER_RESTRICTIONS`を
quarterly.py側と同期させるか共有カタログへの統合を検討する。

④ `common/screening/report_txt_parser.py`（旧REPORT-TXT-PARSER-
CLEANUP-1、優先度低）: report.txt を regex でパースして
`Classification`/`Matrix`/`FCF_History`等を抽出する公開API
（`parse_report_text()`/`parse_ticker_report()`）を持つが、
`common/sec_data/report_consistency_check.py`・
`common/screening/dcf_validity_checker.py`のどちらからも`import`されて
おらず、`tests/test_report_txt_parser.py`からのみ使用される孤立モジュール
であることが判明した。一方`report_consistency_check.py`は同じ
「report.txtのClassification行をregexでパースする」ロジックを255-259
行目に**独自に**実装しており（`report_txt_parser.py::_parse_tanuki_
score()`とは別の正規表現・別の実装）、実質的な重複が存在する。対応方針
候補（未確定）: a.`report_txt_parser.py`を削除する（未使用コードの
整理）b.`report_consistency_check.py`側の独自パース実装を
`report_txt_parser.py`に統合し重複を解消する c.現状維持（実害なし、
テストのみで担保されている状態を許容）。

#### 対応方針
4件とも「grep確認→未使用なら削除、継続利用の可能性があれば個別対応」の
共通フローで一括調査する。個別の判定結果（削除/修正/現状維持）は対象
ごとに異なってよい。

#### 着手条件
なし（実害報告なし、優先度低。次回セッションで方針判断してから着手）

---

### [HISTORY-JSON-LEGACY-TANUKI-SCORE-1] history.jsonにレガシーtanuki_scoreフィールドが残存
**優先度:** 低
**分類:** データ整合性 / TANUKI VALUATION
**登録日:** 2026-07-18
**発見:** [[GATE2-PHASE3B-1]]③-b事前調査時

#### 問題
`src/value/tanuki_valuation/pipeline.py`723行目のDESIGNコメントは
「history.jsonはIV/株価等のチャート用データのみに絞る（判定ラベルは
TANUKI VALUATION/TANUKI SCOREで別ロジックのため混乱を招く。
score_history.json側に集約）」と明記しており、現行コードは実際に
`tanuki_score`を書き込んでいない。

しかし`docs/value-monitor/tanuki_valuation/data/SITM/history.json`・
`ALAB/history.json`等、複数銘柄の実データに`"tanuki_score": "GROWTH_PREMIUM"`
のようなエントリが実在することを確認した。過去（DESIGNコメントの方針が
確定する前）に書き込まれたレガシーエントリが削除されずに残存していると
推測される。ドキュメント（コメント）と実データの乖離状態。

#### 対応方針候補（未確定）
a. レガシーエントリの`tanuki_score`フィールドを一括削除するスクリプトを作成
b. 実害がないため現状維持（history.jsonの当該フィールドを読む消費者は
   現状確認されていない）

#### 着手条件
なし（実害報告なし、優先度低。次回セッションで方針判断してから着手）

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

### [DESIGN-8-3] 8-3 ワンクリック銘柄登録〜更新
- 概要: Discover画面から「➕ 登録」ボタンで
  CIK取得→β/セグメント/Damodaran業種AI提案→承認→一括更新
  を一気通貫で実行
- 実装難易度: 高

### [DESIGN-8-4] 8-4 指数採用候補銘柄の発掘（設計見直し済み・実装保留）
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

**再確認（追記、2026-08-15、フェーズ3未登録11件調査）**: 編集UI欠如を
再確認済み（`INPUT-C-004`）。加えて`rpo_config.json`は`_meta`相当の
メタ情報（更新者・更新日時）も持たないことが判明した。管理UI追加時は
`_meta`付与（`NAMING_CONVENTIONS.md`規則8参照）も併せて検討対象とする。

#### 対応方針
admin.htmlにrpo_config.jsonの編集UIセクションを追加する。追加時は
`_meta`フィールドの付与も併せて検討する（2026-08-15追記）。

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

### [Q4-IMPLIED-CALC-TRIPLICATION-1] 「FY年次値-(Q1+Q2+Q3)=Q4」のQ4逆算ロジックが3箇所に独立実装されている
**優先度:** 低
**分類:** リファクタリング / 技術的負債
**登録日:** 2026-07-24
**発見:** CapEx符号処理・TTM入力元確認調査（フェーズ1）

#### 内容
「FY年次値 - (Q1+Q2+Q3) = Q4」という同一のQ4逆算ロジックが、
normalizer.py::_build_q4_implied_entries()・ttm_calculator.py::
_build_q4_quarterly_entries()・financial_trend_calculator.py（STONKS
SILO、同種の_build_q4_implied）の最低3箇所に独立実装されている。
ttm_calculator.py側はnormalizer.py側と重複しないよう明示的なガード
（BUG-TTM-Q4DUP-1）を持つが、3箇所とも同一ロジックが個別に保守されて
いる状態自体は変わらない。現状ロジックは一貫しており直ちに実害は
ないが、将来1箇所だけ修正すると挙動が分岐するリスクを構造的に
抱えている。

#### 対応方針
未定。3箇所を共通関数へ集約する設計を将来検討する。

#### 着手条件
なし（優先度低、急ぎではない）

---

### [TTM-FLOW-FIELDS-FROZENSET-NONDETERMINISTIC-1] ttm_calculator.pyのFLOW_FIELDSがfrozensetのためキー順序が非決定的になる
**優先度:** 低
**分類:** 技術的負債 / 保守性
**登録日:** 2026-07-24
**発見:** CapEx符号正規化実装（フェーズ1）データ再生成作業中

#### 内容
ttm_calculator.pyのFLOW_FIELDSがfrozensetで定義されているため、
プロセス起動ごとにキー順序が非決定的になる。値が同一でも
ttm/{ticker}_ttm_series.jsonを再生成するたびに無関係なdiffが
大量発生し、意図した変更内容がgit diff上で埋もれる。

#### 影響
通常のパイプライン再実行時には毎回この無関係diffが発生し続けている
状態と推測される。

#### 対応方針
未定。FLOW_FIELDSをfrozensetから順序が決定的なtuple等に変更する
対応が有力候補。

#### 着手条件
なし（優先度低）

---

### [TOBE-SEGMENTS-RESIDUAL-WORDING-1] INPUT_DATA_TOBE.mdの保持構造案にsegments除外判断前の「新規吸収」表現が残存している
**優先度:** 低
**分類:** ドキュメント不整合
**登録日:** 2026-07-24
**発見:** SEC_EDGAR_LAYER_DESIGN.md横断整合性確認調査（フェーズ1）③-1

#### 内容
`INPUT_DATA_TOBE.md`のセグメントKPI（INPUT-A-016）について、L104の
定義行は実態訂正済み（正式ASC280セグメントではなく`tail_kpi_map.json`
ベースの銘柄固有カスタムKPI、フェーズ1統合スコープ除外）だが、同一
ドキュメント内L264の保持構造案（統合ストアのツリー図）には
「segments/{FYQ}.json # セグメント別KPI（新規吸収、INPUT-A-016）」
という、除外判断以前の「新規吸収」という表現が訂正されずに残存
している。

#### 影響
実装への影響はない（[[SEC_EDGAR_LAYER_DESIGN.md]] 5章のスコープ確定
事項が正としてsegments除外を明記しているため）。ドキュメントを読む順序
によっては、保持構造案の図だけを見て「segmentsも統合対象」と誤解する
可能性がある字句レベルの不整合。

#### 対応方針
L264の該当行を、除外判断を反映した表現（例: 該当行を削除するか、
「segments/{FYQ}.json（対象外、詳細は2-3節参照）」等に修正する）に
揃える。

#### 着手条件
なし（優先度低、次にINPUT_DATA_TOBE.mdを編集する機会に合わせて対応
してよい）

---

### [LAYER3-RPO-CANDIDATE-ORDER-1] layer3_builder.pyのrpo候補統合（union）で総額系タグが長期限定タグより優先され値が大幅変動する
**優先度:** 中〜高→**実害調査完了により低（2026-08-15）**
**分類:** データ品質 / バグ
**登録日:** 2026-07-24
**発見:** フェーズA（layer3_builder.py）105銘柄回帰レポート

#### 内容
統合スキーマのrpo候補リスト（quarterly.py・parser.py双方のunion後）
において、`ContractWithCustomerLiability`（総額系）が
`ContractWithCustomerLiabilityNoncurrent`（長期のみ）より優先順位で
先に選ばれてしまい、値が大きく変動する（AMZN実データ: 4.4B→25B）。
15銘柄で差異確認。

#### 影響（登録時点の記述）
RPO（残存履行義務）はHypeCore・STONKS SILO等で成長シグナルとして
参照される指標であり、値の大幅な変動は下流の判定に影響しうる、と
記載されていたが、下記「実害調査結果」の通りこの記述自体が実態と
食い違っていることが判明した。

#### 実害調査結果（2026-08-13〜15、読み取り専用調査・チャット記録）
①**TANUKI VALUATIONのRPO取得経路**: `core_calculator.py`が呼ぶ
`SECReader.get_rpo_context()`/`get_rpo_series()`（`reader.py:264-330`）
は`common/sec_data/normalized/{TICKER}_quarterly_normalized.json`を
直接読んでおり、**Layer3（`layer3_builder.py`）を一切経由しない**。
normalized/側のRPOフォールバック候補（`RemainingPerformanceObligation`
→`ContractWithCustomerLiabilityNoncurrent`→`DeferredRevenueNoncurrent`）
は本バグの原因である総額系タグ`ContractWithCustomerLiability`を
そもそも含んでおらず、構造的に別物。

②**フェーズD Step2-1（2026-08-06完了）にrpoが含まれなかった理由**:
見落としではなく、TANUKI VALUATIONのRPO取得が元々別経路
（`SECReader`専用メソッド、normalized/直読み）のままで、Layer3切替の
対象リスト（SharesDiluted/NetIncome/LTDebt/TTM営業利益/Moat入力の
6項目）に最初から含まれていなかったため。

③**layer3_builder.py側のrpoフィールドの実消費者**: `layer3_builder.py`
は`rpo`を`NO_CANDIDATE_MERGE_FIELDS`（本バグ対応を意図的に別タスクへ
委ねる旨のコメント付き）として保持しているが、リポジトリ全体で
`get_field_entries(store, "rpo")`という呼び出しは0件。「影響」欄が
挙げていたHypeCore・STONKS SILOも実コードを確認したところ`rpo`/`RPO`
への参照は一切存在しない（当初の記述自体が誤りだった可能性が高い）。

**結論**: バグを含むコード（layer3_builder.pyのrpo候補統合ロジック）
自体は現存するが、リポジトリ全体で実際にこれを読む消費者がゼロ
（TANUKI VALUATIONは別経路、HypeCore・STONKS SILOはそもそも無関係）。
着手条件の締切（フェーズD Step2-1着手前）は形式的には超過している
が、rpoがLayer3切替の対象になったことが一度もないため実害はない。

#### 対応方針
未定。総額系タグと長期のみタグのどちらを正とすべきか（あるいは
両者を別フィールドとして分離すべきか）の判断が必要。
[[SCHEMA-NORMALIZED-ISSUES-1]]（旧SCHEMA-SHARESBASIC-CONCEPT-
MISMATCH-1）と同種の「候補統合時の概念混在」パターンの可能性がある。
実消費者が現れた場合（RPOをLayer3経由に切替する計画が具体化した場合
等）に優先度を再度引き上げて対応する。

#### 着手条件
なし（優先度を中〜高→低に格下げ、実消費者が現れた時点で再判断する。
登録時点の「フェーズD Step2-1着手前までに解消」という締切は、rpoが
同Step2-1の切替対象に一度も含まれなかったため実質的に意味を持たな
かったと2026-08-15に確認済み）。

---

### [LAYER3-UNEXPLAINED-SINGLE-TICKER-DIFFS-1] layer3_builder.py回帰レポートで検出された原因未調査の単一銘柄差異
**優先度:** 低
**分類:** データ品質 / 要調査
**登録日:** 2026-07-24
**発見:** フェーズA（layer3_builder.py）105銘柄回帰レポート

#### 内容
【2026-07-24再調査】
- capital_expenditure（LLY）・stock_based_compensation（CAT）:
  解消済み。一連の修正（候補タグ正規化順序変更・優先タグ内欠落
  フォールバック・年次/四半期複合キー分離・Q4逆算統一）の副次効果と
  推定される（どの修正が直接要因かは未特定）
- gross_profit（ABBV/HON）: 原因判明。normalizer.py::
  _calc_gross_profit()（Revenue−cost_of_revenueからのGrossProfit
  逆算バックフィル）はlayer3_builder.pyのモジュールdocstringに
  フェーズA当初から「未実装（既知の制限）」と明記済みのスコープ外
  機能であり、新規バグではない。対応は当該バックフィル機能の
  layer3_builder.pyへの実装が必要（別タスク化を検討）
- 残る未調査: cash_and_equivalents（PAYS/RCAT 2件）・
  short_term_investments（7件）・total_liabilities（AVAV/ELF/ESTC
  3件）。いずれもSTOCK分類のためTTM非対象、フェーズD以降に持ち越し可

#### 対応方針
未定。フェーズB以降で個別に原因調査する。

#### 着手条件
なし

---

### [LAYER3-EPS-UNIT-MISMATCH-1] eps_basic/eps_dilutedのunit指定誤りにより105銘柄全数で完全に空になっている
**優先度:** 高
**分類:** バグ
**登録日:** 2026-07-24
**発見:** eps_basic/eps_diluted加法性検証（フェーズC前提確認）

#### 内容
config/sec_concept_definitions.jsonのeps_basic・eps_dilutedが
"unit": "USD"と誤って指定されている（正しくは"USD/shares"）。
extract_field_raw_entries()はcompany_facts["facts"]["us-gaap"]
[concept]["units"][unit]という厳密一致でルックアップするため、
この不一致により105銘柄全数・完全に空（0エントリ、source_tag:
None）のまま出力されている。

#### 影響
フェーズA完了時（105銘柄回帰レポート）でこの欠落が検出されな
かった。両フィールドは新規追加分（旧データに対応物がない）のため、
「diffなし」の判定に紛れて見落とされたと考えられる。現状のTTM
消費者はこの2フィールドを参照していないため実害はないが、config
自体が機能していない状態のまま「フェーズA完了」としていたことに
なる。

#### 対応方針
unit指定を"USD/shares"に修正する。修正後、105銘柄で
extract_field_raw_entries()が正しくエントリを取得できることを
確認する。

#### 着手条件
なし（フェーズC実装前に修正すべき、本作業で対応）

---

### [SEC-BKNG-SHARES-ANOMALY-1] BKNGのWeightedAverageNumberOfDilutedSharesOutstandingがSEC提出データ自体で異常値
**優先度:** 低〜中
**分類:** データ品質 / SEC提出データ異常
**登録日:** 2026-07-24
**発見:** eps_basic/eps_diluted加法性検証時の希薄化銘柄スクリーニング

#### 内容
BKNGのWeightedAverageNumberOfDilutedSharesOutstanding
（2026-03-31期、accession 0001075531-26-000025、2026-04-28提出）
が、前四半期比24倍（32.6M→794M株）という異常値でSEC XBRL上に
そのまま存在する。company_facts.json（Layer1）の生データ自体に
含まれており、本コードベースのパイプラインが生成した値ではない。
既知の大型分割の発表・登録もない（config/split_history.yaml未登録）
ため、SEC提出企業側のXBRLタグ付けミスの可能性が高い。

#### 影響
BKNGの株式数・1株当たり指標を参照する計算（EPS・希薄化率等）が、
この四半期のみ大きく歪む可能性がある。

#### 対応方針
未定。原因の詳細調査（他のSEC提出書類との突合等）と、判明した場合の
除外・補正方法の検討が必要。

#### 着手条件
なし

---

### [QUARTERLY-CLASSIFY-PERIOD-NO-UPPER-BOUND-1] _classify_period()のis_annual判定に上限が無く中間的な期間長を誤って年次扱いする
**優先度:** 中〜高
**分類:** バグ / SECデータ正規化
**登録日:** 2026-07-24
**発見:** [[LAYER3-ANNUAL-QUARTERLY-COLLISION-1]]波及範囲調査中の
副次発見（DELL net_income 2023-08-04期の調査）

#### 内容
`quarterly.py::_classify_period()`（488-522行目）のis_annual判定は
`form in ("10-K","10-K/A") and ((fp=='FY' and days>130) or
days>300)`という基準で、130日という**下限のみ**設定されている
（[[XBRL-TAG-KLAC-1]]対応として、fp='FY'だが実際は四半期程度
〈89〜91日〉の期間を誤って年次扱いしないための下限）。**上限が
存在しない**ため、181日（約6ヶ月累計）のような「四半期でも真の
年次（365日前後）でもない」中間的な期間を持つエントリが
is_annual=Trueに誤分類される。

具体例: DELL（会計年度末は例年2月上旬）の2023-08-04期
（181日、真の年度末ではない）が誤ってis_annual=Trueに分類されて
いた。

#### 影響
このバグは`quarterly.py`という既存の本番コード（`normalized/`
生成元）に存在するため、Layer3（新規コード）に限らず、現行の
`normalized/`データ自体にも影響している可能性がある。会計年度末が
暦年末以外の企業（DELL等）で、10-K内に埋め込まれた中間的な期間長の
開示がある場合に発生しうる。影響範囲の全数調査は未実施。

#### 対応方針
未定。is_annualの上限（例: 300〜400日程度の範囲に限定する）を
追加する対応が候補。[[LAYER3-ANNUAL-QUARTERLY-COLLISION-1]]の
根本修正とは別に、既存本番コードへの影響有無を別途確認する必要が
ある。

#### 着手条件
なし。ただし本番`normalized/`への影響が疑われるため、優先度は
[[LAYER3-ANNUAL-QUARTERLY-COLLISION-1]]と独立して判断すべき

---

### [SEC-XBRL-MISSING-START-ENTRY-1] raw XBRLにstart日付が欠落した変則的なエントリが含まれる
**優先度:** 低
**分類:** データ品質 / SEC提出データ異常
**登録日:** 2026-07-24
**発見:** LAYER3-ANNUAL-QUARTERLY-COLLISION-1根本修正後の
105銘柄回帰レポート（4回目）

#### 内容
AVAV（accession 0001104659-26-078906、2026-06-29提出の新しい
10-K）等で、raw XBRLに`start`日付が欠落した変則的なエントリが
含まれており、shares_dilutedで比較対象normalized/生成後に到着した
新規提出によるデータドリフトとして3件（AVAV/ELF/ESTC）の差異と
して検出された。

#### 影響
shares_dilutedはNO_CANDIDATE_MERGE_FIELDS（今回の変更対象外パス）
を通るため、今回の修正とは無関係。影響範囲・実害は未調査。

#### 対応方針
未定。start欠落エントリの扱い（除外するか、end日付のみで妥当性
判定するか）の検討が必要。

#### 着手条件
なし

---

### [LAYER3-IONQ-REVENUE-2022Q1-ANOMALY-1] IONQのRevenuesタグ2022年Q1データが事業規模に対して不自然に大きい
**優先度:** 低〜中
**分類:** データ品質 / SEC提出データ異常
**登録日:** 2026-07-24
**発見:** フェーズC実装、TTM系列全体での105銘柄回帰

#### 内容
IONQのRevenues（2022年Q1 anchor）が、旧比較値2,186,000に対し新値
1,070,233,000と489倍の差異。原因はIONQの古いRevenuesタグ自体が
raw XBRL上でval=1,070,000,000という値を持っており、これをそのまま
採用した結果。当時のIONQの事業規模から見て値自体が不自然に大きく、
[[SEC-BKNG-SHARES-ANOMALY-1]]と同種のSEC提出データ異常の可能性が
ある。未検証。

【2026-07-24スコープ拡大確認】2022Q1の異常値が4四半期ローリング
窓に含まれるTTM期間（2023-03-31）にも波及することを確認。原因は
同一（2022Q1の異常値そのもの）。

【2026-07-24原因確定】旧TICKER_RESTRICTIONSのIONQエントリ
（revenue_concept: "RevenueFromContractWithCustomerExcludingAssessedTax"、
note: "2022年10-KのRevenuesタグがSPAC調達金($1,235M)を誤タグ"）と
金額・時期とも完全一致。SEC提出データ自体の誤タグ付けであることが
確定した（未検証ステータスを解除）。対応は
[[SOFI-TICKER-RESTRICTIONS-NOT-MIGRATED-1]]（IONQのrevenue_concept
固定オーバーライド移行）に一本化する。

#### 対応方針
未定。原因調査（他のSEC提出書類との突合）が必要。

#### 着手条件
[[SOFI-TICKER-RESTRICTIONS-NOT-MIGRATED-1]]の対応と一体で解消

---

### [LAYER3-ANCHOR-MISSING-LOOKBACK-WINDOW-1] TTM系列の古いanchor（H1YTD逆算による先行四半期復元）がlayer3_builder.pyで欠落
**優先度:** 中
**分類:** バグ / 要調査
**登録日:** 2026-07-24
**発見:** フェーズC実装、TTM系列全体での105銘柄回帰

#### 内容
【2026-07-24原因判明、当初推測を訂正】当初「5年ロールバック境界の
実行時点依存」を疑ったが、実データ調査により異なる原因と判明した。
10銘柄（ADSK/CRM/DELL/GTLB/HQY/IOT/MRVL/NVDA/S/WMT）の該当anchor
四半期（例: NVDA 2021Q1）は、SEC提出上「単独四半期」としては一度も
開示されておらず、同一10-Q提出物内の「H1（半期）YTD累計」と「Q2
単独」の2エントリのみが存在する。旧パイプライン
（normalizer.py::_build_missing_quarter_implied_entries()、
「後続四半期の単独値をYTDから差し引いて先行四半期を逆算する」任意
欠落四半期の逆算機能）はH1YTD−Q2SAでQ1を復元していたが、
layer3_builder.pyにはこの機能が未実装（フェーズA当初からdocstringに
既知の制限として明記済み、q4_implied.pyのFY−Q1−Q2−Q3パターンとは
別種）。カットオフ（5年ロールバック）自体は無関係（該当エントリの
end日付はカットオフを余裕を持って超えている）。決定論性は確認済み
（同一日内の複数回実行で結果は完全一致、非決定性バグではない）。

【2026-07-24範囲拡大】105銘柄全体の機械スキャンにより、当初記載の
10銘柄（72件）に加え、6銘柄・16件の追加ケースを確認した
（AVAV/SM×2件・CON/Revenue,OperatingIncome,SM×3件・
ELF/Revenue,GrossProfit,OperatingIncome,NetIncome,SM,_COGS×6件・
ONDS/_COGS×1件・PM/SBC×2件・SOUN/DA,Revenue×2件）。対象は計16銘柄・
88件に拡大する。

なお、この機能（_build_missing_quarter_implied_entries()）自体には
フィールド種別のガードが内蔵されておらず、shares_diluted等の
株式数系フィールドに無条件適用すると符号異常（意味不明な負値等）を
生むことを確認済み。実装時はnormalizer.py側の既存スコープ
（Revenue/_COGS/OCF/ICF/CFF/CapEx/RD/SM/SBC/DA/NetIncome/
OperatingIncome/GrossProfit、13フィールド。q4_implied.pyの15
フィールドとは非対称でFinanceLeasePmts/Buybackを含まない）を
そのまま踏襲する。

#### 影響
5年ロールバック境界付近のTTMデータが不安定になる可能性がある
（本番切替後、実行タイミングによって同じ結果が再現しないリスク）。

#### 対応方針
未定。_build_missing_quarter_implied_entries()相当の機能を
layer3_builder.pyに実装する必要がある。
[[LAYER3-GROSSPROFIT-BACKFILL-MISSING-1]]と同種の「フェーズA
スコープ外機能の実装漏れ」であり、両者は関連タスクとして扱う。

#### 着手条件
なし。フェーズC完了の前提（TTM系列の完全性に直接影響するため）

---

### [LAYER3-TTM-TEST-SUITE-SHAPE-MISMATCH-1] tests/test_ttm_calculator.pyの既存テストが新store形状でクラッシュする
**優先度:** 中
**分類:** テスト / 技術的負債
**登録日:** 2026-07-24
**発見:** フェーズC実装、既存テストスイート実行確認

#### 内容
tests/test_ttm_calculator.pyの既存単体テスト3件が、新しいstore形状
（{"fields": {name: {"entries": [...]}}}）と旧normalized形状
（{"fields": {name: [...]}}）の不一致によりクラッシュする
（AttributeError: 'list' object has no attribute 'get'）。テスト
コード自体が旧形状を前提にしたまま。

#### 対応方針
テストを新形状に対応させる。フェーズC完了に必須。

#### 着手条件
なし

---

### [LAYER3-CROSS-TAG-YEARLY-QUARTERLY-GENERAL-RISK-1] _merge_normalized_by_priority()のキー単位独立選択が他フィールドでも年次/四半期クロスタグ混入を起こしうる一般的リスク
**優先度:** 低
**分類:** データ品質 / 要調査
**登録日:** 2026-07-24
**発見:** LAYER3-DA-SBC-CANDIDATE-REGRESSION-1対応方針検討時

#### 内容
_merge_normalized_by_priority()の「(end_date, is_annual)キーごとに
独立して候補タグを評価・選択する」という設計は、DA/SBC以外の複数
候補タグを持つ他フィールドでも、理論上同型の年次/四半期クロスタグ
混入を起こしうる一般的な性質。今回はDA/SBCの範囲内でのみ実例を
確認・修正するが、他フィールドでの発生有無は未調査。

【2026-07-24】懸念が実際に43銘柄・9フィールドで顕在化していた
ことを確認。[[LAYER3-DA-SBC-CANDIDATE-REGRESSION-1]]対応
（同一source_tagガード＋単独タグ完結フォールバック）で同時に解消
済み。本項目は「他フィールドでも起こりうる」という一般的懸念の
記録としては役割を終えたが、今後Layer2 candidatesに新規タグが
追加された際に同型の問題が再発しうるため、設計上の注意点として
クローズせず残す。

#### 対応方針
未定。他の複数候補タグフィールド（LTDebt・SM・Revenue等）で同様の
機械スキャンを行う必要がある。

#### 着手条件
対応不要（[[LAYER3-DA-SBC-CANDIDATE-REGRESSION-1]]で機構自体は
解消済み）。将来Layer2 candidates拡張時の設計注意点として保持

---

### [LAYER3-GA-STANDALONE-TAG-UNMAPPED-1] GeneralAndAdministrativeExpense（Selling抜きG&A単体タグ）がLayer2のどのフィールドにもマッピングされていない
**優先度:** 低〜中（2026-07-30投資調査により中→低〜中に修正。理由は下記対応方針参照）
**分類:** データ品質 / タグ網羅性
**登録日:** 2026-07-24
**発見:** SM/SGA分離258件全数検証

#### 内容
GeneralAndAdministrativeExpense（Selling抜きのG&A単体タグ）が、
Layer2の32フィールドのいずれにもマッピングされていない。

【2026-07-30投資調査で規模を再確認】当初「少なくとも6銘柄」としていた
規模認識は過小評価だった。全105銘柄スキャンの結果、
GeneralAndAdministrativeExpenseタグを報告している銘柄は56銘柄に及ぶ。
ただし影響度で3分類できる:
- **実害なし（4銘柄: AAPL/AMAT/CELH/TER）**: SGA総額
  （selling_general_and_administrative）が別途取得済みのため対応不要
- **部分的ギャップ（47銘柄）**: selling_and_marketingは機能するが、
  selling_general_and_administrativeのみ空
- **完全なギャップ（5〜6銘柄: APGE/ASTS/CON/ENB/RXRX）**: SM・SGA両方が
  完全に空。当初報告の6銘柄のうちCAKE/CPRTは、実際にはAdvertisingExpense
  （SM候補タグ）を報告しており部分的ギャップ側に該当することが判明
  （ただし四半期粒度では取り込まれないため実質SM空という当初の観測自体は
  誤りではない）。ENBは今回の調査で新たに完全なギャップ銘柄として発見

#### 影響
5〜6銘柄（APGE/ASTS/CON/ENB/RXRX、CAKE/CPRTは部分的ギャップ）でSM・SGA
両フィールドが完全に空になる。GeneralAndAdministrativeExpenseタグ自体の
存在という意味では56銘柄規模。

#### 対応方針
- **選択肢B（既存selling_general_and_administrativeへのフォールバック
  候補化）は非推奨**: [[SCHEMA-NORMALIZED-ISSUES-1]]（旧SCHEMA-SM-SGA-
  CONFLATION-1）と同型の概念混在リスクを再導入する。G&A単体とSGA総額は金額の性質が異なり（SGA総額は
  Selling費用を含むため同規模の企業でもG&A単体より必然的に大きい）、
  同一フィールドに混在させると時系列比較・銘柄間比較の両方で不整合が
  生じる
- **選択肢A（新規フィールド化、例: general_and_administrative_expense）
  を推奨するが、優先度は低〜中に留める**: selling_general_and_
  administrative自体が現状TANUKI VALUATION計算に一切消費されておらず
  （report_consistency_check.pyのSGA整合性チェック用途のみ）、新規
  フィールド追加の実利は当面限定的なため
- 技術的には、GeneralAndAdministrativeExpenseはFLOW系（duration型）
  のため、Q4_IMPLIED_FIELDS・MISSING_QUARTER_IMPLIED_FIELDS・
  newfield_q4_cutoff_check.pyの対象に加えることは可能
  （selling_general_and_administrativeと同型の扱いができる）

#### 着手条件
SGA（selling_general_and_administrative）・SM（selling_and_marketing）
のいずれかが新機能（投資強度分析の精緻化等）で実消費される計画が
立った時点、またはreport_consistency_check.pyのSGA整合性チェックを
強化するタイミングで、選択肢A（新規フィールド化）を再検討する。

---

### [ELF-ROE10YR-RECALC-PENDING-1] ELFのROE_avg(10yr)是正が未反映（TANUKI VALUATION側の定期更新待ち）
**優先度:** 中
**分類:** データ反映待ち / TANUKI VALUATION
**登録日:** 2026-08-01
**発見:** [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]完了時の試験実行（チャット記録）

#### 内容
[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]（era別fiscal_end_month対応）により
ELFの2015-2018年度データが是正された結果、TANUKI VALUATIONのROE_avg(10yr)が
7.0%→9.6%へ、連動してAlpha_Premiumが0.29→0.40へ変化することを試験実行
（未コミット、出力破棄済み）で確認した。これはバグではなく、是正済みの正しい
入力データに基づく期待された再計算結果である。TANUKI SCORE分類（WATCH）・
Matrix Quadrant/Labelは不変であることを確認済み。

#### 影響
ELF単一銘柄。現時点でTANUKI VALUATION側のannual output（IV・Classification等）
は未更新のまま古いROE値を参照し続けている。分類自体への影響はないため
緊急性は低い。

#### 対応方針
TANUKI VALUATIONの通常の定期更新サイクル（全銘柄再計算）に含めて反映する。
単独での緊急反映は不要。

#### 着手条件
なし。次回のTANUKI VALUATION全銘柄再計算時に自然に解消される見込み。
反映確認後、本エントリをクローズすること。

---

### [SPAC-STUB-PERIOD-FIELD-SPLIT-1] BBAI/RDW 2020年度のPredecessor/Successor期間混在、PL/CF系は既にNone化済みで対応不要（2026-08-01訂正: ELF/KULR除外・BS系実害は[[SPAC-SHELL-BS-ENTITY-MIXING-1]]へ分離）
**優先度:** 低（記録のみ・追加対応不要）
**分類:** データ品質 / SPAC会計特有の期間混在（確認完了）
**登録日:** 2026-07-31
**訂正日:** 2026-08-01
**発見:** [[PERIOD-LENGTH-VALIDATION-GAP-1]]調査時の横断スキャン（チャット記録）、
2026-08-01個別調査（チャット記録）で対象を絞り込み

#### 内容（2026-08-01個別調査で確定）
BBAI(2020)・RDW(2020)を10-K原本で確認したところ、いずれも実在するPredecessor/
Successor会計処理だった：
- BBAI 2020: BigBear.ai FY2021 10-K原本に"Successor 2020 Period"（2020-05-22〜
  12-31、223日）・"Predecessor 2020 Period"（2020-01-01〜10-22、295日）の記載を
  確認。合併前SPAC「GigCapital4, Inc.」自身の最初の10-K（27日間、2020-12-04〜
  12-31）も同一CIKに混在
- RDW 2020: Redwire FY2021 10-K原本に"the registrant... previously known as
  Genesis Park Acquisition Corp."・Successor期間（2020-02-10〜12-31、325日）・
  Predecessor期間（2020-01-01〜06-21、172日）の記載を確認

revenue/gross_profit/cost_of_revenue/net_income/operating_income等のPL/CF系
フィールドは、Predecessor(295日/172日)・Successor(223日/325日)いずれも
340-380日フィルタの範囲外であり、**既存の[[PERIOD-LENGTH-VALIDATION-GAP-1]]
フィルタによって両銘柄とも安全側にNone化済みであることを確認した（実データ・
現行コードで検証済み）**。追加対応は不要。

**訂正: ELF(2015)・KULR(2015)は対象外と判明したため本エントリから削除**
（2026-08-01個別調査）：
- ELF(2015): predecessor/successor分裂は実在せず、四半期比較開示の再掲載
  （89/90/91/91日）と真の年次値（364日、$191,413,000等）の混在であり、
  [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]により既に正しい年次値が採用
  されている。元の「89日/333日で分裂」という記述は、隣接する2014年度
  （predecessor/successor分割、333日）との混同だった可能性が高い
- KULR(2015): SPAC・M&Aとは無関係。10-K原本に"Predecessor"/"Successor"/
  "reverse merger"の記載は一切なく、2015-12-11の法人設立から会計年度末までの
  20日間が単純に最初の（短い）事業年度だった。PL/CF系は正しくNone化済み、
  BS系は単一実体（同一accn）から内部整合的に取得されており問題なし

#### 影響
なし（PL/CF系は安全側のNone化で確認完了）。ただしBS系（instant fact、
期間長フィルタの対象外）で、BBAI/RDWとも「合併前SPACシェルのBS」と
「合併後本体のBS」が同一年度内で混在し、数学的に矛盾する値
（current_assets>total_assetsの類）が本番稼働中であることが同じ調査で
新たに判明した。この実害は本エントリのスコープ外とし、
[[SPAC-SHELL-BS-ENTITY-MIXING-1]]として独立登録した（2026-08-01、優先度：高）。

#### 対応方針
なし。PL/CF系は追加対応不要（確認完了・現状維持）。BS系の対応は
[[SPAC-SHELL-BS-ENTITY-MIXING-1]]側で検討する。

#### 着手条件
なし（本エントリはクローズ扱い。記録として残置）。

---

### [HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1] HON(2009)のgross_profit乖離が期間長是正後も残存、既知パターンと異なる原因の疑い
**優先度:** 低
**分類:** データ品質 / 要個別確認
**登録日:** 2026-08-02
**発見:** [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]現状再確認（チャット記録）

#### 内容
HON(2009)のみ、[[PERIOD-LENGTH-VALIDATION-GAP-1]]是正後も乖離が残存
（gross_profit=$6,896M vs revenue-cost_of_revenue逆算値=$7,723M、差$827M）。
同じ「四半期→年次誤採用」パターンが確認されていた他の8銘柄（TDY/AVGO/CPRT/
ABBV/CAT/FICO/HEI/KLAC）は全て解消したのに対し、この1件のみ既知パターンとは
異なる原因の可能性がある。

#### 影響
HON単一年度。金額規模（$827M差）は小さくないが、他年度・他フィールドへの
波及は未確認。

#### 対応方針
未定。10-K原本での個別確認が必要。

#### 着手条件
なし。優先度低。

---

### [REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1] gross_profit/cost_of_revenue整合性を検証する監査項目が存在しない
**優先度:** 低〜中
**分類:** 品質ゲート / 監査カバレッジ欠如
**登録日:** 2026-07-31
**発見:** [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]調査（チャット記録）

#### 内容
report_consistency_check.pyに、gross_profitとcost_of_revenueの整合性
(Revenue−cost_of_revenueとの乖離検知等)を検証するWARN項目が一件も存在しない。
今回発見した複数の乖離事象は、いずれも既存の常設監査では検知できず、個別調査
でのみ発覚した。

#### 影響
同種の新規乖離が将来再発しても、既存の監査プロセスでは検知できない。

#### 対応方針
未定。[[PERIOD-LENGTH-VALIDATION-GAP-1]]等の根本原因対応が固まった後、
再発防止のための常設WARN項目化を検討する(CHAT_RULES.md「探索的スキャンツールと
常設WARN条件の分離」の原則に従い、今回の探索的スキャン手法をそのまま常設WARNに
転用しない設計とする)。

#### 着手条件
[[PERIOD-LENGTH-VALIDATION-GAP-1]]系統の対応確定後。

---

### [LAYER3-COGS-STRUCTURAL-GAP-16TICKERS-1] 監視105銘柄中16銘柄でcost_of_revenue系タグが構造的に欠落
**優先度:** 中
**分類:** データ品質 / 一次データ開示側の制約
**登録日:** 2026-07-29
**発見:** cost_of_revenue/EPS投資調査（チャット記録）

#### 内容
revenue系タグの最終報告日とcost_of_revenue系6候補タグの最終報告日を比較した
横展開スキャンにより、NEVER_REPORTED型8銘柄(APGE/CEG/ENB/FLYW/JOBY/VST/V/XOM)・GAP型
8銘柄(ASTS/BKNG/CAKE/CDNS/CPRT/INTU/LRCX/VZ)、計16銘柄(約15%)で同種パターンを確認。
CAKEについては一次情報(10-K原本)で根本原因を特定: FY2022の10-Kから勘定科目名を
"Cost of goods and services sold"→"Food and beverage costs"に変更すると同時に、
当該科目へのXBRLタグ付け自体を廃止していた(金額・会計処理自体に変化はない)。
company_facts.json内を金額から逆引き検索してもマッチするタグは1件も存在せず、
別タグへの切替(LLY-CAPEX-STALE-1型)ではなく、一次データ(SEC EDGAR提出)側で
タグ付けされていない、抽出ロジック改善では回収不可能なパターンと判明。
BKNG/VZ/CDNS等も業態的にCOGS概念が薄い・別カテゴリ開示のため同種の可能性が高いが、
CAKE以外は一次情報での裏取り未実施。

#### 影響
STONKS SILOのgross margin表示がこの16銘柄について恒久的にNoneのまま表示され続ける。

#### 対応方針
未定。CAKE型(一次データ側の制約)は候補タグ拡充では解決しない。
warn_acknowledged.json的なホワイトリスト運用、またはSTONKS SILO UI側で
「原価データ未開示」等の明示区別表示を検討する余地がある。

#### 着手条件
なし。ASTS/LRCX([[LAYER3-COGS-ASTS-LRCX-RECOVERABLE-FOLLOWUP-1]])の
個別調査結果を踏まえてから全体方針を決めるのが望ましい。

---

### [LAYER3-VISA-EPS-TAG-MISSING-1] Visa(V)がEPS関連タグを一切報告せずeps_diluted経由のROEフォールバックが機能しない
**優先度:** 低
**分類:** データ品質
**登録日:** 2026-07-29
**発見:** cost_of_revenue/EPS投資調査（チャット記録）

#### 内容
Visa(V)はEarningsPerShareBasic・EarningsPerShareDiluted・
EarningsPerShareBasicAndDilutedのいずれのタグも全期間にわたり一切報告していない
(実際に報告しているのはBusinessAcquisitionProFormaEarningsPerShareDiluted等の
非該当タグのみ)。これによりVisaのeps_basic/eps_dilutedは全期間で暗黙にNoneになって
いると推測される。

#### 影響
common/sec_data/reader.py::get_roe_avg_detail()のNetIncome欠損時フォールバック
(net_income = eps_diluted × shares_diluted)がVisaに対して機能しない。Visaで
net_incomeが欠損するケースが実際に発生した場合、代替推計手段が失われる。

#### 対応方針
未定。Visa向けのEPS個別override候補タグの探索、またはVisaについては
ROEフォールバック不可を許容する明示的な設計判断が必要。

#### 着手条件
なし

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
  → ✅ 2026-07-20充足（ARCH-DATA-1完了・BACKLOG_DONE.md参照）。ただし
    着手自体は他の優先度判断とは独立に次回セッションで判断
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

**（2026-08-08更新〈`[[MARKETDATA-LAYER-CONSTRUCTION-1]]`未決定事項
9件の最終確定に伴う再更新〉。以下が最新の優先順位。旧「本線
（2026-08-05更新）」以下は`common/sec_data`統合フェーズD着手前
〈normalized/→data/統合案〉時点の古い計画のため陳腐化・参照時は
本節を優先すること）**

**1. `fetcher.py`新設**（`.history()`・`.download()`呼び出しの一元化、
`pandas_market_calendars`依存追加含む。`[[MARKETDATA-LAYER-
CONSTRUCTION-1]]`の未決定事項9件は2026-08-08に全件確定済みのため、
設計判断ステップは不要）

**2. `reader.py`新設**（API群の実装: `get_latest_price`・
`get_price_series`・`get_ma_deviation`・`get_attributes`・
`get_analyst_events`・`get_calendar`・`get_index_series`・
`get_sp500_constituents_prices`）

**3. 本番消費者8ファイル＋診断ツール2ファイルの段階的切替**
（`pipeline.py`・`data_fetcher.py`・`beta_fetcher.py`・`hypecore.py`・
`valuation_fetcher.py`・`collect_and_send.py`・
`breadth_calculator.py`・`collect.py`＋`score_verifier.py`・
`audit.py`。TANUKI VALUATION本体から、フェーズDと同様の優先順位を
検討）

**4. 周辺ツール2ファイルの切替**（`backfill_tech_pulse.py`・
`extract_key_facts.py`）

（上記1〜4完了後、新DB構築プロジェクト フェーズ1の残りコンポーネント
として`common/macro_data/`新設〈FRED統合層、`INPUT-A-024〜047`対応、
`INPUT_DATA_TOBE.md` 2-C参照、investigate未着手〉に着手する。着手前に
`docs/architecture/new_data_platform/EXTRACTION_DESIGN_PRINCIPLES.md`
を必ず確認すること）

**5. （本線外）本セッション・前セッションで蓄積した課題群**:

- **優先度中**: `[[AVGO-CIK-HISTORY-WRONG-LEGACY-CIK-1]]`対応（AVGOの
  旧CIK登録が無関係な買収先企業Broadcom Corporationを指している疑い。
  対応方針3案〈旧CIK差し替え・現状維持＋警告・2006-2014年データ
  削除〉を検討・実装。着手条件: 新DB構築フェーズ1〈SEC EDGAR統合〉
  実質完了により充足済み）
- **優先度低**（Layer3関連課題群、一覧化。いずれも着手条件「なし」
  または実害発生時まで保留）:
  - `[[LAYER3-FETCHER-SELECTION-PHILOSOPHY-MISMATCH-1]]`（fetcher.py・
    dcf_validity_checker.pyの年次データ選択思想不一致、案2で決着済み・
    恒久的例外）
  - `[[STOCKHTML-LAYER3-PUBLISH-PIPELINE-MISSING-1]]`（stock.htmlの
    Layer3切替、公開パイプライン未整備のため着手見送り）
  - `[[STOCKHTML-YTD-FILTER-BUG-SUSPECT-1]]`（stock.html JS側の
    is_ytd未除外、実データでは未発現）
  - `[[HYPECORE-SUBSTAGE-LAYER3-UNVERIFIED-1]]`（detect_substage()の
    Layer3切替影響が未検証）
  - `[[TAIL-SHARESDILUTED-Q4-TIMING-RISK-1]]`（TANUKI TAILの
    eps_diluted計算、Q4タイミング依存の構造的リスク）
  - `[[FETCHER-PY-BS-FIELDS-DEAD-KEYS-1]]`（fetcher.pyの_BS_FIELDS
    デッドコード、Layer3移行とは無関係の既存バグ）
  - `[[FINTREND-SM-JOBY-NONE-1]]`（financial_trend_calculator.pyの
    SMフィールドJOBY None化、SUB_FIELDS自体が現状未使用と判明済み）
  - `[[PARSER-MERGED-TAG-MIXING-RISK-1]]`（parser.py::
    _extract_values_merged()のタグ混入リスク疑い）
  - `[[LAYER3-SNPS-STALE-TAG-PRIORITY-1]]`（SNPS FY2022 Revenue、
    Layer3候補タグ優先順位が修正再表示を拾えない構造的リスク）
  - `[[LAYER3-ROIC-WACC-NONE-4TICKERS-1]]`（COHR/LLY/JNJ/KLACの
    ROIC-WACC比率None化、SM/SGA概念混同の帰結）

---

**旧・本線（2026-08-05更新、新DB構築プロジェクト フェーズ1 Step1: SEC EDGAR統合、CHAT_RULES.md「本線逸脱防止」参照。陳腐化・参照不要）:**
0-A. ~~`[[SECDATA-STORAGE-FRAGMENTATION-1]]` Step1: 全消費者洗い出し~~
     ✅ 2026-08-05完了（raw/normalized/ttm/data/company_facts.json・
     EPS Analyzer/TANUKI TAIL独自経路の全消費者を実ファイルで確認）
0-B. ~~raw/削除（デッドコード除去）~~ ✅ 2026-08-05完了（詳細後述）
0-C. ~~`data/quarterly_{FYQ}.json` pl/cf/shares区分のYTD→単一四半期(SA)修正~~
     ✅ 2026-08-05完了（事前調査でpl/cf/shares区分が従来XBRL申告のYTD
     累積値のまま保存されていたと判明〈約65〜66%のエントリが該当〉。
     quarterly.py::_classify_period()・normalizer.py::_ytd_to_quarterly()
     を再利用する統一アルゴリズムをparser.py::parse_company_facts()に
     実装し、全105銘柄を実再パース。annual側は無変化（1,441ファイル
     横断比較で差分0件）、report_consistency_check.py NG=0・WARN=78件
     （不変）、pytest 497 passed/2 known failed確認。RCAT 2016Q3の
     SBC1件のみ四半期キー自体が消滅しファイル未上書きという別要因の
     残存を発見・`[[RCAT-2016Q3-ORPHANED-QUARTERLY-FILE-1]]`として
     記録。詳細はBACKLOG_DONE.md参照）
1. **新設アクセサの実装**: `reader.py::get_quarterly_series()`/
   `get_latest_quarterly()`相当のdata/quarterly_*.json版（フィールド
   単位の時系列抽出関数）。前回調査で未着手と判明済み
2. **5本番消費者のnormalized/→data/切り替え**: financial_trend_
   calculator.py・quarterly_review_generator.py・tail_dcf_bridge.py・
   hypecore.py・pipeline.py内5用途。フィールド名変換
   （PascalCase→snake_case）・`[[SCHEMA-NORMALIZED-ISSUES-1]]`①〜⑥の
   残り論点（②SM/SGA概念混同の設計判断・⑤ファイル名混在等）の解消方法
   確定を含む。詳細な論点整理は別途設計セッションで実施
3. **normalized/廃止**: 上記1・2完了後、全消費者がdata/へ移行済みと
   確認した上で実施（raw/削除と同じ手順: 全消費者洗い出し→Step0最終
   確認→削除）

**本線外・優先度中（2026-08-05更新、CHAT_RULES.md「本線逸脱防止」参照）:**
4. `[[AVGO-CIK-HISTORY-WRONG-LEGACY-CIK-1]]`対応（旧CIK登録が無関係な
   買収先企業Broadcom Corpを指している疑い。対応方針3案〈差し替え/
   現状維持+警告/削除〉を検討・実装。着手条件成立まで保留）
   + MRVL/AVGO/DELL旧CIK拡張分の年度×フィールド単位の個別確認
   （AVGO分は上記の対応方針確定後に着手する方が効率的。MRVL/DELL分は
   先行して着手可）
   + `[[SPAC-SHELL-MAINTAINED-FIELDS-FREEZE-CONSIDERATION-1]]`の検討
   ※ SCCO(2010-2019)のfixed_registry.json登録は2026-08-05
   Stage 3bで完了済み（gross_profit、10エントリ）。以前の依頼文に
   残タスクとして記載されていたが、現状確認の結果既に完了と判明。

**本線外・優先度低（2026-08-05更新）:**
5. `[[ONDS-LOAR-SHARES-SCALE-SUSPECT-1]]`（shares_basic単位スケール
   異常の疑い、記録のみ）
   + `[[RCAT-2016Q3-ORPHANED-QUARTERLY-FILE-1]]`（RCAT 2016Q3の
   quarterly_*.jsonが新ロジックで未上書きのまま残存、記録のみ）

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
~~[[SPLIT-REALTIME-GAP-1]]~~ ✅ 2026-07-20完了（NVDA+新規発見AVGO/CPRT/
WMT/LRCX/CELH/TSLA〈8銘柄〉・KLAC事前登録、RCAT除外。詳細はBACKLOG_DONE.md参照）。
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

追記（2026-07-17〜18 [[ARCH-DATA-1]]ステージ2・3完了／[[GATE2-PHASE3B-1]]
①②③-a③-b全完了）: 上記①②の両方が完了した。

[[ARCH-DATA-1]]はステージ2（アンカー日ウィンドウ方式。実装中にJNJ/TDY型
〈決算日が年境界12/31〜1/1を往復する52/53週企業〉で企業自身のfyタグと
矛盾する誤判定を新規発見し、循環クラスタリング方式（`_cluster_fiscal_
anchor_candidates()`）へ設計変更して解消）・ステージ3（fyタグ裏取り、
WARN-23新設。初版は`is_own_data`不問で4,434件・105銘柄という実用不能な
ノイズになったため`is_own_data=True`限定に設計変更）を完了し、
「値の確定→年度ラベル計算→裏取り」の3段階設計が全完了した（詳細は
[[ARCH-DATA-1]]「ステージ2完了」「ステージ3完了」参照）。

[[GATE2-PHASE3B-1]]（=[[QUALITY-GATES-EPIC-1]] Phase 3b）は①（4ファイル
のreader.py統合）・②（規約C、STOCK_FIELDS分類の網羅性契約）・③-a（規約D、
`GrowthVerdict`のEnum化）・③-b（規約D、`Classification`のEnum化）の
全項目を完了し、BACKLOG_DONE.mdへ全文移動した。②の実装検証で
STOCK_FIELDS/SHARES_FIELDS分類が構造的に本番未到達（`calc_ttm()`が
2026-05-07以降到達不能）という構造的問題を新規発見し[[TTM-STOCK-FIELDS-
DEAD-1]]として分離登録。③-bの事前調査でreport_txt_parser.pyの孤立モジュール
化・history.jsonのレガシーフィールド残存も新規発見し、それぞれ
[[REPORT-TXT-PARSER-CLEANUP-1]]・[[HISTORY-JSON-LEGACY-TANUKI-SCORE-1]]
として登録した（いずれも優先度：低）。

これにより次セッションの筆頭候補を更新する：
① [[ARCH-DATA-1]]残課題④（BS項目〈instant fact〉が本人データ判定の
   対象外のまま。CDNS型の実害〈修正済み〉と同根の未解消リスク）
② RCAT型決算期変更検知（企業が実際に決算期を変更したケースと単なる
   52/53週の測定誤差との区別。ARCH-DATA-1ステージ2のスコープ外として
   引き続き未着手）
   ※2026-07-31追記: この行の内容は現在も有効（未着手のまま）。
   [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]として2026-07-31に統合的に
   再登録した（ELF/RCAT/AVGOを対象とする統合タスク）。
③ [[FY52WEEK-BS-NULL-SILENT-1]]（優先度：高・着手条件なし。
   ①と独立に着手可能）
④ [[TRUST-SUMMARY-EPIC-1]]（優先度：高・要設計・実装未着手の大規模EPIC）
⑤ ~~WARN-23残り8銘柄（ADSK/AVAV/COHR/CRM/FCX/FICO/HON/WMT）の一次情報検証~~
   ✅ 2026-07-18完了。全10銘柄・12件でXBRL fyタグ側の誤りと確認、
   実害なし。詳細はARCH-DATA-1「WARN-23残り8銘柄の一次情報検証完了」参照
⑥ ~~[[TTM-STOCK-FIELDS-DEAD-1]]（方針判断のみの軽量タスク）~~
   ✅ 2026-07-18完了。対応方針(a)デッドコード削除を実施、
   BACKLOG_DONE.mdへ全文移動

追記（2026-07-21 FCF-CONVRATE①③調査完了・[[FCF-DIVERGENCE-SIGN-GUARD-1]]新規登録）:
これにより次セッションの筆頭候補を更新する：
① ~~[[FCF-DIVERGENCE-SIGN-GUARD-1]]（優先度：高・新規・実装コスト低）~~
   ✅ 2026-07-22完了（両方向の符号不一致を検知するよう2段階で実装。
   第1段階: raw_fcf>0×estimated_fcf<0の符号反転ガード
   〈f6201ae04a4e242bbda2014b0f71ca2ef42911b6〉。
   第2段階: raw_fcf<=0×estimated_fcf>0の対称ケース
   〈99014218b676fa4e36e4babefaf9ce407cac8ba4〉。
   回帰テスト計6件・100銘柄フローズン比較で影響なしを確認済み。
   詳細はBACKLOG_DONE.md参照）
② TRUST-SUMMARY-EPIC-1の①③②対応（2026-07-22調査で「②と同型に統合」
   という前回方針を撤回、3件に分けて設計し直す）:
   - ①: FCFEstimationResultに`rate_is_sector_default`等のフラグを追加し、
     機械的に検知・表示する設計（固定リスト不要）
   - ③: ticker単位の表示ではなく、fcf_conversion_config.json側に
     セクターカテゴリ単位の開発者向けメタ情報として持たせる設計
     （画面表示は変更しない）
   - ②表示不一致バグ（新規発見）: report.txtはfcf_estimation.applied=True
     前提でネストされているが、stock.htmlはticker集合の所属のみで判定し
     applied状態を見ないため、LITE等でapplied=Falseの間、両者の表示が
     食い違う。独立バグとして修正要（report.txt側の条件に合わせる方向を推奨）
   いずれも実装未着手

追記（2026-07-31 [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]派生調査・
新規6件登録、登録のみで実装は未着手）:
これにより次セッションの筆頭候補を更新する：
① [[PERIOD-LENGTH-VALIDATION-GAP-1]]（優先度：高・新規。parser.pyのFLOW型
フィールド抽出〈`_extract_values_best_candidate()`→`_extract_single_key()`
経路〉に期間長検証が構造的に欠落しており、AVGO revenue/net_income/
operating_income(2016/2017)・gross_profit9銘柄で四半期値が年次値として
誤採用されていたことを確認済み。対応方針確定前に105銘柄×全FLOW型フィールドの
オフラインシミュレーションが必要）
② [[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]（優先度：高・要個別調査。BBAI/RDW/ELF/
KULRの10-K原本確認。①のシミュレーション精度に影響するため①と並行、または
①着手前に着手が望ましい）
③ 余力があれば[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]
（優先度：低〜中・MO/PM/SCCOの10-K原本確認）
④ [[SPAC-STUB-PERIOD-VERIFICATION-1]]・[[REPORT-CONSISTENCY-GROSSPROFIT-
COGS-CHECK-MISSING-1]]は①②の対応確定後（着手条件未達）。
[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]はcommon/sec_data統合
フェーズ進捗待ち（着手条件未達）。
[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]（本体）は①の解消が前提
のため、それまで着手保留。

追記（2026-07-31 [[PERIOD-LENGTH-VALIDATION-GAP-1]]実装完了）:
① ~~[[PERIOD-LENGTH-VALIDATION-GAP-1]]（優先度：高・全母集団シミュレーション
   〈9フィールド+revenue/S&M/D&A3フィールド〉→parser.py実装
   〈`_extract_single_key()`・`_extract_values_merged()`両方に340-380日
   フィルタ追加〉→全105銘柄フローズン入力再生成・検証まで完了）~~
   ✅ 2026-07-31完了（コード`e3723b3eb`・データ`d6d404016`。pytest 446 passed
   /2 known failed、report_consistency_check.py NG=0〈WARN 71→68件に減少〉。
   検証中にELF固有の別バグ（fiscal_end_month誤検出）を発見し
   [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]として新規登録、ELF分5ファイルは
   本コミットから除外。詳細はBACKLOG_DONE.md「2026-07-31（完了）」参照）。
これにより次セッションの筆頭候補を更新する：
~~① [[ELF-FISCAL-END-MONTH-MISDETECTION-1]]（優先度：高・新規。ELFの
   fiscal_end_month自動検出誤り〈3月と誤検出、実際は当該期間12月決算〉に
   よる年度ラベル一括ズレ。10-K原本で決算期変更の実態を確認してから設計）~~
   ✅ 2026-08-01完了（案②era別anchor対応を実装。コード`7c44ac266`・データ
   `6d9c18b2f`。全105銘柄でbucketing比較しELFのみ変化、RCAT/AVGO/MSCI/NOW
   は複数クラスタ検出も実害ゼロを確認。ELFのannual_2015-2018が真の暦年値に
   復旧、2014・2019（移行期）はPL/CF系フィールドをNone化。pytest 453
   passed/2 known failed、report_consistency_check.py NG=0〈WARN=68件、
   変化なし〉。詳細はBACKLOG_DONE.md「2026-08-01（完了）」参照。RCATの
   直近10-K重複投票は[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]として別途
   新規登録済み〈優先度：中、10-K原本確認は未着手〉。pushは保留、コミットのみ）
② [[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]（優先度：高・要個別調査。BBAI/RDW/ELF/
   KULRの10-K原本確認。ELFは①の案②実装で決算期変更自体は解消済みのため、
   本項目はELF 2015年の89日/333日フィールド分裂という別種の問題として
   引き続き要確認）
③ 余力があれば[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]
   （優先度：低〜中・MO/PM/SCCOの10-K原本確認）
④ [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]（本体、着手条件は充足済み）
   の対応方針（①本番書き戻し／②突合検算ロジック追加）決定は、②の10-K確認
   結果を踏まえてから着手するのが望ましい。
⑤ [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]（優先度：中・新規。RCATの
   直近10-Kが12月31日・4月30日の両クラスタに同時投票、3段階目の決算期変更が
   進行中の可能性。10-K原本での個別確認が未着手）

追記（2026-08-02 [[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]個別調査〜
[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1完了、複数セッションにわたる進捗を
まとめて反映）:
~~② [[SPAC-STUB-PERIOD-FIELD-SPLIT-1]]~~ ✅ 2026-08-01完了（BBAI/RDW/ELF/
   KULRを10-K原本で個別確認。ELF(2015)・KULR(2015)は対象外〈既に正しく
   処理済み〉と判明し除外、BBAI(2020)・RDW(2020)のPL/CF系は既に安全側に
   None化済みで追加対応不要と確認しクローズ扱いへ訂正。調査過程で新たに
   判明したBS系の実害を[[SPAC-SHELL-BS-ENTITY-MIXING-1]]として分離登録。
   詳細はBACKLOG_DONE.md「2026-08-01（完了）」参照）
~~[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1~~ ✅ 2026-08-02完了（コード
   `80e51d2c2`・データ`c5e588474`。BBAI(2020)/RDW(2020)/RKLB(2020)/
   SOFI(2020)/VRT(2019)/ONDS(2017)/KULR(2016)の7銘柄7年度で数学的矛盾を
   解消、全105銘柄フローズン入力比較で対象7件以外〈矛盾のない56件・
   KULR(2019)・SPIR(2020)含む〉に変化なしを確認。pytest 461 passed/
   2 known failed、report_consistency_check.py NG=0〈WARN=68件、変化
   なし〉。詳細は本ファイル該当エントリ参照）

これにより次セッションの筆頭候補を更新する：
① [[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階2（優先度：中・新規着手候補。
   SPIR(2020)型の"事故的な正しさ"を事前検知するSPAC合併疑いの機械的検知
   〈案B〉。submissions.jsonへのformerNames〈法人名変更履歴〉取得・保存
   拡張がデータ取得層の前提条件として必要）
② [[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（優先度：中。KULR(2019)
   単独の課題に再定義済み。current_liabilities/total_liabilitiesが既に
   同一accnから採用されているにも関わらず矛盾しており、同一filing内での
   candidate tag誤選択が原因と確定。タグそのものを10-K原本と突合する
   個別調査が未着手）
③ [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]（優先度：中。10-K原本での
   個別確認が未着手、①②と独立に着手可能）
④ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。ELF是正済みデータに伴う
   ROE_avg(10yr)の再計算未反映。TANUKI VALUATION通常の定期更新サイクルで
   自然解消見込みのため、優先度高の項目ではない）
⑤ 余力があれば[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]
   （優先度：低〜中・MO/PM/SCCOの10-K原本確認）
⑥ [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]（本体、着手条件は
   充足済み）の対応方針（①本番書き戻し／②突合検算ロジック追加）決定は、
   ⑤の10-K確認結果を踏まえてから着手するのが望ましい。

追記（2026-08-02 [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]①本番書き戻し
実装完了）:
~~⑥ [[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]~~ ✅ 2026-08-02完了
（①本番書き戻しを実装。コード`dc0507c27`・データ`65ddd0d6b`。標準タグから
gross_profitが取得できない年度のみrevenue-cost_of_revenue逆算値で埋め、
`pl_provenance.gross_profit.derived=True`を付与。Case A対象34銘柄342件で
完全一致・Case B残存49件は無変化を確認。STONKS SILO fetcher.pyの重複自己
修復ロジックが実質デッドコード化したことを確認〈[[STONKS-SILO-FETCHER-
GROSSPROFIT-BACKFILL-DUP-1]]のクローズ判断材料〉。TANUKI VALUATIONへの
影響はゼロと確定。pytest 467 passed/2 known failed、report_consistency_
check.py NG=0〈WARN=68件、変化なし〉。②突合検算は[[GROSSPROFIT-COGS-
ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]へ引き継ぎ。詳細はBACKLOG_DONE.md
「2026-08-02（完了）」参照。副産物として[[HON-GROSSPROFIT-2009-RESIDUAL-
DISCREPANCY-1]]を新規登録・[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-
MO-PM-SCCO-1]]の対象を14銘柄へ拡大）
これにより次セッションの筆頭候補を更新する：
① [[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階2（優先度：中。SPIR(2020)型の
   事前検知、submissions.jsonへのformerNames取得拡張が前提）
② [[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（優先度：中。KULR(2019)
   単独、candidate tag誤選択の10-K原本突合が未着手）
③ [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]（優先度：中。10-K原本での
   個別確認が未着手、①②と独立に着手可能）
④ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期
   更新サイクルで自然解消見込み）
⑤ [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは10年連続、LITE/CRMは新規大規模
   クラスタ。10-K原本確認が未着手）
⑥ 余力があれば[[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：
   低・HON(2009)単独の10-K原本確認）

追記（2026-08-02 セッション終了処理。[[STONKS-SILO-FETCHER-GROSSPROFIT-
BACKFILL-DUP-1]]クローズ）:
~~[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]~~ ✅ 2026-08-02
クローズ（[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]①実装により、
STONKS SILO対象25銘柄全体で発火条件〈gross_profit=None かつ revenue/
cost_of_revenue両方present〉が0件になったことを確認。実害解消済みだが
fetcher.py側のコード自体は残存〈デッドコード化、削除ではない〉。コード
整理はcommon/sec_data統合フェーズ1到達時に別途検討。詳細はBACKLOG_DONE.md
「2026-08-02（完了）」参照）

**2026-08-01〜02セッションの完了サマリ**: [[PERIOD-LENGTH-VALIDATION-
GAP-1]]・[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]・[[SPAC-STUB-PERIOD-
FIELD-SPLIT-1]]・[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1・[[LAYER3-
GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]①・[[STONKS-SILO-FETCHER-
GROSSPROFIT-BACKFILL-DUP-1]]の6件完了。新規登録:
[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]・[[ELF-ROE10YR-RECALC-
PENDING-1]]・[[SPAC-SHELL-BS-ENTITY-MIXING-1]]（段階2残存）・
[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（KULR2019単独に再定義）・
[[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]。訂正:
[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（3銘柄→14銘柄へ
対象拡大）。

**次セッションでの着手順序（2026-08-02時点、優先度順に整理・最終版）**:
① [[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階2（優先度：中・実害が現在進行形
   だった段階1は完了済み。SPIR(2020)型の"事故的な正しさ"を事前検知する
   SPAC合併疑いの機械的検知〈案B〉。submissions.jsonへのformerNames
   〈法人名変更履歴〉取得・保存拡張がデータ取得層の前提条件として必要）
② [[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（優先度：中・KULR(2019)
   単独の課題に再定義済み。current_liabilities/total_liabilitiesが既に
   同一accnから採用されているにも関わらず矛盾しており、同一filing内での
   candidate tag誤選択が原因と確定。タグそのものを10-K原本と突合する
   個別調査が未着手）
③ [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]（優先度：中・RCATの直近10-Kが
   12月31日・4月30日の両クラスタに同時投票、3段階目の決算期変更が進行中の
   可能性。10-K原本での個別確認が未着手、①②と独立に着手可能）
④ [[SPAC-STUB-PERIOD-VERIFICATION-1]]（優先度：中・SPAC合併前・IPO前と
   見られる正当な非365日期間データ11銘柄の個別確認、10-K原本での裏取り
   未実施）
⑤ [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは各10年連続、LITE(9年)/CRM(7年)は
   新規発見の大規模クラスタ。10-K原本確認が未着手）
⑥ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑦ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・ELF是正済みデータに伴う
   ROE_avg(10yr)の再計算未反映。TANUKI VALUATION通常の定期更新サイクルで
   自然解消見込みのため、単独での緊急着手は不要。次回定期更新後に反映
   確認・クローズ）
⑧ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・gross_profit/cost_of_revenue整合性の常設監査項目が存在しない。
   ⑤⑥の10-K確認が概ね収束してから、再発防止のための常設WARN項目化を
   検討するのが望ましい）

追記（2026-08-02 [[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階2実装完了）:
~~① [[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階2~~ ✅ 2026-08-02完了（コード
   `1f6e95d92`・データ`43470bccf`。fetcher.pyで既存レスポンスから
   formerNamesを追加取得〈新規APIコールなし〉、`_resolve_bs_entity_
   mixing()`にformerNames区間一致による新トリガー条件③'を追加。
   SPIR(2020)のlong_term_debtを新規検知・None化
   〈triggered_by="former_names_window"〉。BBAI/RDW/RKLB/SOFI/VRTは
   ③'でも重複検知されるが結果不変（冪等性を確認）。全105銘柄フローズン
   入力比較でSPIR以外に変化なし（RKLBの2025年再法人化という「単純な
   改名」ケースでの誤検知なしを含む）。spac_shell_detection_log.jsonを
   全105銘柄で新規生成。pytest 473 passed/2 known failed、
   report_consistency_check.py NG=0〈WARN=68件、変化なし〉。
   [[SPAC-SHELL-BS-ENTITY-MIXING-1]]は段階1・段階2ともに完了し
   BACKLOG_DONE.md「2026-08-02（完了）」へ全文移動。残り99銘柄の
   formerNamesは通常の週次自動更新で自然にバックフィルされる設計
   〈特別な一括再取得は未実施〉）
これにより次セッションの筆頭候補を更新する：
① [[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（優先度：中・KULR(2019)
   単独、candidate tag誤選択の10-K原本突合が未着手）
② [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]（優先度：中・10-K原本での
   個別確認が未着手、①と独立に着手可能）
③ [[SPAC-STUB-PERIOD-VERIFICATION-1]]（優先度：中・SPAC合併前・IPO前と
   見られる正当な非365日期間データ11銘柄の個別確認、10-K原本での裏取り
   未実施）
④ [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは各10年連続、LITE(9年)/CRM(7年)は
   新規発見の大規模クラスタ。10-K原本確認が未着手）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・④の10-K確認が概ね収束してから常設WARN項目化を検討）

追記（2026-08-02 [[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]根本原因調査
完了）:
~~① [[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]~~ ✅ 原因確定・
   [[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]へ統合しクローズ
   （BACKLOG_DONE.md「2026-08-02（完了）」へ移動）。KULR(2019)の矛盾は
   `XBRL_MAPPING["total_liabilities"]`の2番目のフォールバック候補
   `LiabilitiesAndStockholdersEquity`（定義上`Assets`と一致する誤った
   代替タグ）が原因と確定。予備スキャンで105銘柄中278件（AMZN/GOOGL/
   MSFT/NVDA等含む）に及ぶ横断的な設計欠陥と判明したため、KULR単独対応
   ではなく新規タスクへ統合。
これにより次セッションの筆頭候補を更新する（優先度順）：
① [[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]（優先度：高・新規。
   278件（銘柄年度）・AMZN/GOOGL/MSFT/NVDA等の大型株を含む候補タグ設計
   欠陥。対応方針（案A/案B）の設計調査・全母集団シミュレーションが未着手）
② [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]（優先度：中・10-K原本での
   個別確認が未着手、①と独立に着手可能）
③ [[SPAC-STUB-PERIOD-VERIFICATION-1]]（優先度：中・SPAC合併前・IPO前と
   見られる正当な非365日期間データ11銘柄の個別確認、10-K原本での裏取り
   未実施）
④ [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは各10年連続、LITE(9年)/CRM(7年)は
   新規発見の大規模クラスタ。10-K原本確認が未着手）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・④の10-K確認が概ね収束してから常設WARN項目化を検討）

追記（2026-08-02 [[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]実装完了）:
~~① [[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]~~ ✅ 2026-08-02完了
   （コード`ee46018b2`・データ`11d75b2c0`。貸借対照表恒等式逆算
   〈total_assets − stockholders_equity〉によるtotal_liabilitiesバック
   フィルを実装。278件全件で完全一致（許容誤差なし）を確認、全105銘柄
   フローズン入力比較で対象278件以外に変化がないことを確認。
   report_consistency_check.py NG=0（WARN=68件、変化なし）、pytest 504
   passed/2 known failed（既知のMSFT/NVDA）。BACKLOG_DONE.md
   「2026-08-02（完了）」へ全文移動）。
これにより次セッションの筆頭候補を更新する（優先度順）：
① [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]（優先度：中・10-K原本での
   個別確認が未着手、他項目と独立に着手可能）
② [[SPAC-STUB-PERIOD-VERIFICATION-1]]（優先度：中・SPAC合併前・IPO前と
   見られる正当な非365日期間データ11銘柄の個別確認、10-K原本での裏取り
   未実施）
③ [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは各10年連続、LITE(9年)/CRM(7年)は
   新規発見の大規模クラスタ。10-K原本確認が未着手）
④ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑤ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑥ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・③の10-K確認が概ね収束してから常設WARN項目化を検討）

追記（2026-08-02 [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]根本原因調査完了）:
~~① [[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]~~ ✅ 解消（実害なし、
   当初の懸念は誤りだったと確認）。3段階目の決算期変更は存在せず、直近
   10-Kの2クラスタ同時出現はSEC開示規則（Regulation S-X Article 3-06等）
   による比較列表示の正常な挙動と確認。era別anchor不一致も対称探索設計
   により計算結果に無害と確認。BACKLOG_DONE.md「2026-08-02（完了）」へ
   全文移動。調査から派生した実害（8ヶ月移行期データ完全欠落）は
   [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]として独立登録（優先度：高）。
これにより次セッションの筆頭候補を更新する（優先度順）：
① [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]（優先度：高・新規。fetcher.pyの
   relevant_formsに10-KT・10-QTが含まれず、RCATの8ヶ月移行期データが
   annual_YYYY.jsonから完全欠落。対応方針確定にはまずTANUKI VALUATION
   計算経路への実害有無の確認が必要）
② [[SPAC-STUB-PERIOD-VERIFICATION-1]]（優先度：中・SPAC合併前・IPO前と
   見られる正当な非365日期間データ11銘柄の個別確認、10-K原本での裏取り
   未実施）
③ [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは各10年連続、LITE(9年)/CRM(7年)は
   新規発見の大規模クラスタ。10-K原本確認が未着手）
④ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑤ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑥ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・③の10-K確認が概ね収束してから常設WARN項目化を検討）

追記（2026-08-02 [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]実害確認調査完了）:
①の優先度を「高→中」に訂正（TANUKI VALUATIONは実害なし・STONKS SILOの
一時的実害はデータ蓄積により自然解消済みと確認。詳細はBACKLOG.md該当項目
参照）。副産物として[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]を新規
登録（優先度：中）。これにより次セッションの筆頭候補を更新する：
① [[SPAC-STUB-PERIOD-VERIFICATION-1]]（優先度：中・SPAC合併前・IPO前と
   見られる正当な非365日期間データ11銘柄の個別確認、10-K原本での裏取り
   未実施）
② [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは各10年連続、LITE(9年)/CRM(7年)は
   新規発見の大規模クラスタ。10-K原本確認が未着手）
③ [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]（優先度：中・現在進行形の実害は
   解消済み、将来同型の決算期変更を行う他銘柄が現れた場合の再発リスクとして
   監視対象。対応方針〈案1〜3〉未確定）
④ [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（優先度：中・新規。RCATの
   operating_cash_flow欠落、継続/非継続事業タグ分割が原因の疑い。現時点で
   直接的な計算実害は未確認だが将来のOCF黒字転換時にfcf_list/DCFへ影響
   するリスク）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・②の10-K確認が概ね収束してから常設WARN項目化を検討）

追記（2026-08-02 [[SPAC-STUB-PERIOD-VERIFICATION-1]]個別確認完了）:
~~① [[SPAC-STUB-PERIOD-VERIFICATION-1]]~~ ✅ 解消（実害なし、現状の処理は
   妥当）。11銘柄・12ティッカー年度すべてで追加対応不要と確認。SPAC系
   6銘柄（ASTS/IONQ/JOBY/RKLB/SOFI/SPIR）はBSがSPAC本体の自己データ、
   PL/CFは後年filingの正しい12ヶ月比較列と確認。VRT(2016)は記載理由を
   訂正（Emersonスピンオフではなく、SPAC〈GS Acquisition Holdings
   Corp〉自身の設立初年度スタブと判明）。RCAT(2012)はown-dataで充実、
   D&A「1日間」エントリはval=0のタグ付けミスで実害ゼロと確認。
   BACKLOG_DONE.md「2026-08-02（完了）」へ全文移動。
これにより次セッションの筆頭候補を更新する：
① [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]（優先度：
   低〜中・対象14銘柄49件。MO/SCCOは各10年連続、LITE(9年)/CRM(7年)は
   新規発見の大規模クラスタ。10-K原本確認が未着手）
② [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]（優先度：中・現在進行形の実害は
   解消済み、将来同型の決算期変更を行う他銘柄が現れた場合の再発リスクとして
   監視対象。対応方針〈案1〜3〉未確定）
③ [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（優先度：中・RCATの
   operating_cash_flow欠落、継続/非継続事業タグ分割が原因の疑い。現時点で
   直接的な計算実害は未確認だが将来のOCF黒字転換時にfcf_list/DCFへ影響
   するリスク）
④ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑤ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑥ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・①の10-K確認が概ね収束してから常設WARN項目化を検討）

追記（2026-08-02 [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]
個別調査完了）:
~~① [[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]~~ ✅ 一部
   解消（MO/PM/SCCOの3銘柄は①genuine定義差、確定・対応不要としてクローズ。
   PM/MOはExciseAndSalesTaxesタグが検出diffと完全一致〈物品税込み収益vs
   税抜きベースのgross profitという業界標準〉、SCCOはDepreciationDepletion
   AndAmortizationタグが検出diffと完全一致〈D&A別建て表示という鉱業界
   標準〉。BACKLOG_DONE.md「2026-08-02（完了）」へ全文移動）。残り11銘柄
   は[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高、CRM/JNJ/
   MRVL確定3件＋AMD/BSY/KO/LRCX/ONDS/RMBS要確認6件）・
   [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中、LITE1件）へ新規分離
   登録。
これにより次セッションの筆頭候補を更新する：
① [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高・新規。
   revenue/cost_of_revenue/gross_profitが異なるaccn・会計年度から独立
   採用される設計欠陥。CRM/JNJ/MRVLで確定、残り6銘柄は要個別確認）
② [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]（優先度：中・現在進行形の実害は
   解消済み、将来同型の決算期変更を行う他銘柄が現れた場合の再発リスクとして
   監視対象。対応方針〈案1〜3〉未確定）
③ [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（優先度：中・RCATの
   operating_cash_flow欠落、継続/非継続事業タグ分割が原因の疑い。現時点で
   直接的な計算実害は未確認だが将来のOCF黒字転換時にfcf_list/DCFへ影響
   するリスク）
④ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中・新規。LITEのcost_of_
   revenueがCOGS由来償却費タグを未合算、タグ拡張で解消可能）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い。10-K原本確認が未着手）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・①の6銘柄確認が概ね収束してから常設WARN項目化を検討）

追記（2026-08-02 セッション終了処理、次セッションでの着手順序を最終整理）:
**2026-08-01〜02セッション全体のサマリ**: gross_profit調査（[[LAYER3-
GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]）を発端に、[[PERIOD-LENGTH-
VALIDATION-GAP-1]]・[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]・[[SPAC-
SHELL-BS-ENTITY-MIXING-1]]段階1/2・[[TOTAL-LIABILITIES-FALLBACK-TAG-
DESIGN-FLAW-1]]・[[GROSSPROFIT-COGS-ANNUAL-DEFINITION-GAP-MO-PM-SCCO-1]]
（一部）・[[RCAT-TRIPLE-FISCAL-CHANGE-SUSPECTED-1]]・[[SPAC-STUB-PERIOD-
VERIFICATION-1]]・[[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]の
完了・クローズが連鎖的に波及した。新規登録は
[[BS-ENTITY-MIXING-UNEXPLAINED-ONDS-KULR-1]]（後に統合クローズ）・
[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]・[[FETCHER-10KT-10QT-
FORM-EXCLUSION-1]]・[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]・
[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]・[[LITE-COGS-DA-TAG-
UNMERGED-1]]。詳細はBACKLOG_DONE.md「2026-08-01/02（完了）」参照。

**次セッションでの着手順序（2026-08-02時点、最終版）**:
① [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高・CRM/JNJ/
   MRVLで確定、残り6銘柄〈AMD/BSY/KO/LRCX/ONDS/RMBS〉の個別確認→横断的
   設計変更の検討へ）
② [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]（優先度：中・現在進行形の実害は
   解消済み、将来同型の決算期変更を行う他銘柄が現れた場合の再発リスクとして
   監視対象）
③ [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（優先度：中・RCATの
   operating_cash_flow欠落、継続/非継続事業タグ分割が原因の疑い）
④ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中・LITEのcost_of_revenue
   がCOGS由来償却費タグを未合算、タグ拡張で解消可能）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・①の6銘柄確認が概ね収束してから常設WARN項目化を検討）
⑧ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低・
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理
   自体は将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]案b実装完了）:
①の一部（案b）を実装完了。`_align_cost_of_revenue_to_revenue_period()`を
新規追加し、revenue・cost_of_revenueが異なるaccnから独立採用され、かつ
`revenue − cost_of_revenue ≠ gross_profit`という数学的矛盾が現に存在する
年度についてのみ、revenueと同一accn・同一期間のcost_of_revenue候補で
矛盾が厳密に解消する場合に限り置換する設計（コード`b756021f6`＋安全性
修正`9616e8058`・データ`7c94c6f95`）。**実装時の検証で発見した重大な
副作用**（初回実装が矛盾のない年度＝GOOGL(2008)/HON(2008)/SCCO(2009/2010)
まで誤って書き換える巻き添え）を、gross_profitがNone〈導出前〉の年度を
比較不能として除外するゲート条件の追加で是正した。結果、対象はLRCX(2010)
の1件のみとなり、それ以外は全105銘柄フローズン入力比較で無変化と確認。
report_consistency_check.py NG=0（WARN=68件）、pytest 513 passed/2 known
failed。CRM(2013)・JNJ(2017)・MRVL(2017)・ONDS(2017)は案b単独では未解決
のまま残存（案aの対応が必要な可能性）。エントリ自体は全件解決していない
ためBACKLOG.mdに残置し、実装結果・残存部分を本文に明記した
（BACKLOG_DONE.mdへの完全移動はしない）。
これにより次セッションの筆頭候補を更新する:
① [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]（優先度：中・現在進行形の実害は
   解消済み、将来同型の決算期変更を行う他銘柄が現れた場合の再発リスクとして
   監視対象）
② [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（優先度：中・RCATの
   operating_cash_flow欠落、継続/非継続事業タグ分割が原因の疑い）
③ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中・LITEのcost_of_revenue
   がCOGS由来償却費タグを未合算、タグ拡張で解消可能）
④ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]残存分（優先度：中〜高・案a
   〈候補タグ拡張、AMD/KO/JNJ/MRVL等〉・案c〈2タグ合算、RMBS〉・案d
   〈BSY個別対応〉、いずれもゲート条件込みの再設計が必要）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・④の確認が概ね収束してから常設WARN項目化を検討）
⑧ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低・
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理
   自体は将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]対応方針確定）:
①の対応方針を確定。案1（relevant_forms追加+バケツ再設計）は見送り
（RCAT own-data 10-K・10-KTが両方ともSEC自身によりfy=2024とタグ付け
されており真正のバケツキー衝突が発生すること、複数消費者の改修が必要な
ことを確認しコストが当初想定より高いと判明）。案3（`report_consistency_
check.py`への新規WARN追加のみ）を採用方針として確定、実装は未着手。
トリガー条件（RCAT再変更または他銘柄での実害確認）発生時に案1を再検討。
副産物として[[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]を新規登録
（優先度：低〜中、fetcher.py側とは独立の別タスク）。
これにより次セッションの筆頭候補を更新する:
① [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（優先度：中・RCATの
   operating_cash_flow欠落、継続/非継続事業タグ分割が原因の疑い）
② [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中・LITEのcost_of_revenue
   がCOGS由来償却費タグを未合算、タグ拡張で解消可能）
③ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]残存分（優先度：中〜高・案a
   〈候補タグ拡張、AMD/KO/JNJ/MRVL等〉・案c〈2タグ合算、RMBS〉・案d
   〈BSY個別対応〉、いずれもゲート条件込みの再設計が必要）
④ [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]案3実装（優先度：中・
   report_consistency_check.pyへの新規WARN追加、既存WARN-24との役割
   分担を明記した設計が確定済み）
⑤ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中・新規。
   _calc_yoy_change()への期間長妥当性チェック追加、緊急性なし）
⑥ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い）
⑦ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑧ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・③の確認が概ね収束してから常設WARN項目化を検討）
⑨ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低・
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理
   自体は将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]案③実装完了）:
~~④ [[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]案3実装~~ ✅ 2026-08-02完了
   （コード`1fd44fc0a`。`report_consistency_check.py`にCHECK-28
   〈WARN-28〉を新規追加、company_facts.json上のform=10-KT/10-QTのaccnが
   `accn_to_reportdate`に未登録の場合を検知〈検知のみ、自動修正なし〉。
   全105銘柄実行でRCATにWARN-28が2件発火（10-KT accn
   `0001641172-25-001892`・**新規発見**の10-QT accn
   `0001554795-19-000269`〈2019年、RCAT第1回目の決算期変更に伴う移行期
   四半期報告書〉）、他104銘柄で誤検知なし、WARN数68→70件（+2）、NG=0
   維持。pytest 519 passed/2 known failed。データファイルは無変更（検知
   のみ）。BACKLOG_DONE.md「2026-08-02（完了）」へ全文移動）。
これにより次セッションの筆頭候補を更新する:
① [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（優先度：中・RCATの
   operating_cash_flow欠落、継続/非継続事業タグ分割が原因の疑い）
② [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中・LITEのcost_of_revenue
   がCOGS由来償却費タグを未合算、タグ拡張で解消可能）
③ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]残存分（優先度：中〜高・案a
   〈候補タグ拡張、AMD/KO/JNJ/MRVL等〉・案c〈2タグ合算、RMBS〉・案d
   〈BSY個別対応〉、いずれもゲート条件込みの再設計が必要）
④ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中・
   _calc_yoy_change()への期間長妥当性チェック追加、緊急性なし）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・③の確認が概ね収束してから常設WARN項目化を検討）
⑧ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低・
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理
   自体は将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]根本原因調査
完了）:
~~① [[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]~~ ✅ 原因確定・
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]へスコープ拡大・
   統合しクローズ（BACKLOG_DONE.md「2026-08-02（完了）」へ移動）。RCATの
   OCF欠落は標準タグ`NetCashProvidedByUsedInOperatingActivities`が
   FY2024フィリングから継続/非継続事業の分割タグに置き換わったことが原因
   と確定。105銘柄横断スキャンで**25銘柄該当**（AAPL/MSFT/TSLA/XOM/CAT/
   ABBV等の主力銘柄を含む）する候補タグ設計欠陥と判明し、`operating_
   cash_flow`はTANUKI VALUATIONのDCF/FCF計算に直結するため実害の可能性が
   高いと判断、新規タスクへ統合（優先度：高）。
これにより次セッションの筆頭候補を更新する:
① [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：高・
   新規。25銘柄該当、まずTANUKI VALUATION計算経路への実害有無の確認が
   必要）
② [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中・LITEのcost_of_revenue
   がCOGS由来償却費タグを未合算、タグ拡張で解消可能）
③ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]残存分（優先度：中〜高・案a
   〈候補タグ拡張、AMD/KO/JNJ/MRVL等〉・案c〈2タグ合算、RMBS〉・案d
   〈BSY個別対応〉、いずれもゲート条件込みの再設計が必要）
④ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中・
   _calc_yoy_change()への期間長妥当性チェック追加、緊急性なし）
⑤ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い）
⑥ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑦ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・③の確認が概ね収束してから常設WARN項目化を検討）
⑧ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低・
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理
   自体は将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]
実害確認調査完了）:
①の優先度を「高→中」に訂正（25銘柄中24銘柄〈AAPL/MSFT/TSLA/XOM/CAT/ABBV
等を含む〉は該当年度がすべて現在の直近5年窓〈2021-2026年〉の外にあり実害
なしと確定。RCAT単独の実害は[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]として新規
独立登録〈優先度：高〉。RCATの`get_fcf_5yr_avg()`が実質2021-2023年の3年
平均になっており、真により大きな悪化を示す2024/2025年〈特に-$89.1M〉が
欠落していることを確認。前回〈[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]〉の
「成長率決定には影響しない」という限定的確認だけでの「実害なし」結論を
訂正）。
これにより次セッションの筆頭候補を更新する:
① [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：高・新規。RCATのDCF FCF
   ベース値計算に構造的な実害。[[OPERATING-CASH-FLOW-CONTINUING-
   DISCONTINUED-GAP-1]]のRCAT分〈パターンB〉解決が前提）
② [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中・LITEのcost_of_revenue
   がCOGS由来償却費タグを未合算、タグ拡張で解消可能）
③ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]残存分（優先度：中〜高・案a
   〈候補タグ拡張、AMD/KO/JNJ/MRVL等〉・案c〈2タグ合算、RMBS〉・案d
   〈BSY個別対応〉、いずれもゲート条件込みの再設計が必要）
④ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中・
   RCAT以外の24銘柄は現在進行形の実害なし、過去年度のデータ品質向上として
   引き続き価値あり）
⑤ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中・
   _calc_yoy_change()への期間長妥当性チェック追加、緊急性なし）
⑥ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低・HON(2009)
   単独、既知パターンと異なる原因の疑い）
⑦ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中・TANUKI VALUATION通常の
   定期更新サイクルで自然解消見込み。次回定期更新後に反映確認・クローズ）
⑧ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中・③の確認が概ね収束してから常設WARN項目化を検討）
⑨ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低・
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理
   自体は将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 セッション終了処理、優先度順に並び順を最終整理）:
**2026-08-01〜02セッション全体のサマリ（gross_profit調査発端から2日間に
わたり波及した一連のデータ品質是正作業）**: [[PERIOD-LENGTH-VALIDATION-
GAP-1]]・[[ELF-FISCAL-END-MONTH-MISDETECTION-1]]・[[SPAC-STUB-PERIOD-
FIELD-SPLIT-1]]・[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1/2・[[TOTAL-
LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]・[[GROSSPROFIT-COGS-ANNUAL-
DEFINITION-GAP-MO-PM-SCCO-1]]（一部）・[[RCAT-TRIPLE-FISCAL-CHANGE-
SUSPECTED-1]]・[[SPAC-STUB-PERIOD-VERIFICATION-1]]・[[STONKS-SILO-FETCHER-
GROSSPROFIT-BACKFILL-DUP-1]]・[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]・
[[RCAT-OCF-CONTINUING-DISCONTINUED-SPLIT-1]]（[[OPERATING-CASH-FLOW-
CONTINUING-DISCONTINUED-GAP-1]]へ統合）・[[PL-FIELD-CROSS-ACCN-PERIOD-
MISMATCH-1]]案bが完了。次回最優先タスクは
[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（現在進行形のDCF計算実害）。
**次セッションでの着手順序（2026-08-02時点、最終版）**:
① [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：高。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分
   〈パターンB〉解決が前提）
② [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCATパターンBの対応がRCAT-FCF-5YR-AVG-ACTUAL-3YR-1
   の前提）
③ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
④ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑤ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑥ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑦ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑧ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑨ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理は
   将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]パターンB実装前
シミュレーション完了）:
①の優先度を「高→低」に訂正。RCATの本番FCF計算がreader.py::
get_fcf_5yr_avg()（年次ファイルベース）を使わず、data_fetcher.py::
_select_fcf_source()がTTM系列（common/sec_data/ttm/RCAT_ttm_series.json）
を優先採用する設計と判明。TTM系列は四半期10-Qの集計であり年次10-Kの
継続/非継続事業分割タグ問題の影響を受けず既に完全な値を持つため、
[[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分（パターン
B）を年次パーサー側のみに実装してもRCATのfcf_base_used・DCF・
tanuki_score・Classificationは一切変化しない（ΔIV=$0と試算確認）。
副次的に発見したTTM系列生成ロジック側の継続/非継続タグ扱い未検証の問題を
[[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]として新規登録
（優先度：高。RCATの本番IV計算経路に直結するため、こちらを優先）。
これにより次セッションでの着手順序を更新する:
① [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：高・
   新規。TTM系列生成ロジックの継続/非継続タグ扱いが未検証、RCATの本番
   IV計算に直結する可能性）
② [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
③ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
④ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：高→低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される。単独での緊急対応は不要）
⑤ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑥ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑦ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑧ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑨ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑩ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理は
   将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]
根本原因調査完了）:
①の優先度を「高→中」に訂正。当初の懸念（継続/非継続タグの取り扱いミス）
ではなく、`ttm_calculator.py::calc_ttm_series()`が採用四半期の日付連続性
を検証しない一般的な設計欠陥が根本原因と判明。RCATでは標準タグの空白
（継続/非継続分割開示と決算期変更が重なった約11ヶ月間）により、2023年
7〜10月・10月〜2024年1月の四半期が`ttm_end=2025-03-31`・`2026-03-31`の
両方に重複使用され、現在のfcf_5yr_avg（-40,185,008.5）・fcf_2yr_avg
（-50,540,837.0）が正しい値（試算：約-53,985,212・約-78,141,244）より
34〜55%過小評価と確定。IVへの影響は現時点でΔIV=$0（revenue floor＋EPS
ベース推定オーバーライドが吸収。将来業績改善時に顕在化しうる潜在リスクの
留保付き）。他銘柄（HON/AVAV/TER）への現時点の実害なしと確認。根本原因
（ticker非依存の一般的欠陥）を[[TTM-CALC-QUARTER-CONTIGUITY-
UNCHECKED-1]]として新規登録（優先度：中〜高）。
これにより次セッションでの着手順序を更新する:
① [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高・新規。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   まず105銘柄横断スキャンから着手）
② [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
③ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：
   高→中。現時点のIV実害はゼロ、恒久対応は①側で行う）
④ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑤ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：高→低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される。単独での緊急対応は不要）
⑥ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑦ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑧ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑨ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑩ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑪ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、fetcher.py側の重複ロジックのコード整理は
   将来のcommon/sec_data統合フェーズ1到達時に検討）

追記（2026-08-02 セッション終了処理、優先度順に並び順を最終整理）:
本セッション（RCAT-FCF-5YR-AVG-ACTUAL-3YR-1パターンB実装前シミュレーション
→RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1根本原因調査、いずれも
読み取り専用の調査・BACKLOG登録のみ、実装なし）の結果を反映し、
**次セッションでの着手順序（2026-08-02時点、最終版）**を確定する:
① [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
② [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は①側で行う）
③ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
④ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑤ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑥ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑦ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑧ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑨ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑩ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑪ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 common/sec_data/抽出アーキテクチャの俯瞰的脆弱性分析
完了）:
本セッションで発見した5バグが共通の設計的欠陥（候補プールから新しさ
基準のみで値を確定し、他フィールド・他期間・会計恒等式と照合しない）に
帰着すると判明。105銘柄への機械的予備スキャンでTA≠TL+SE違反156件
（50銘柄）・GP≠Revenue−COGS違反43件（9銘柄、GOOGL(2012/2013)は新規
発見）・OI>GP違反22件（LMT単独、新規発見）・NI≠EPS×Shares違反67件
（31銘柄、COHRに単位スケールバグの疑い）を確認（詳細調査は未実施、件数
把握のみ）。[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]・
[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]を優先度：高で新規登録。
これにより次セッションでの着手順序を更新する:
① [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高・新規。
   予備スキャンで見つかった4種の違反〈TA≠TL+SE 156件・GP≠Revenue−COGS
   43件・OI>GP 22件・NI≠EPS×Shares 67件〉の分類調査〈bug/genuine差/
   対応不要〉が未着手）
② [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]（優先度：高・新規。
   横断的な会計恒等式検証レイヤーの新設提案。①の分類調査結果を踏まえて
   から実装に進むのが望ましい）
③ [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
④ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は③側で行う）
⑤ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑥ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑦ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑧ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑨ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑩ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑪ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑫ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑬ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]の
TA=TL+SE違反156件・分類調査完了）:
持続性区分（単年度28銘柄・2年度5銘柄・3年度以上17銘柄）を確定。8銘柄の
サンプル確認で6銘柄（FCX/BROS/RKLB/GTLB/COHR/ONDS）が①genuine（NCI・
一時的持分の未捕捉、設計スコープ外）と確定し、156件の過半数が①に該当する
見込みと判明。HEI・LRCXの2銘柄はNCI等を含めても解消しない未特定の不整合
（同一filing・同一accn内での恒等式不成立）と判明し
[[HEI-LRCX-TA-TLSE-UNEXPLAINED-RESIDUAL-1]]として新規登録（優先度：
中〜高）。恒等式検証の対応方針を「TA==TL+SE+NCI+一時的持分」の拡張形で
確定（許容誤差を広げるだけの対応はHEI・LRCX型の真の異常を隠蔽するため
不採用）。GP≠Revenue−COGS・OI>GP・NI≠EPS×Shares の3種の分類調査は未着手。
これにより次セッションでの着手順序を更新する:
① [[HEI-LRCX-TA-TLSE-UNEXPLAINED-RESIDUAL-1]]（優先度：中〜高・新規。
   NCI等を含めても解消しない同一filing内の恒等式不成立、原因未特定）
② [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]（優先度：高。
   横断的な会計恒等式検証レイヤーの新設提案。TA=TL+SE違反の分類調査結果
   〈①の設計方針〉を踏まえて実装可能な段階）
③ [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高。
   TA=TL+SE違反の分類調査は完了、残る3種〈GP≠Revenue−COGS 43件・
   OI>GP 22件・NI≠EPS×Shares 67件〉の分類調査が未着手）
④ [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
⑤ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は④側で行う）
⑥ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑦ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑧ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑨ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑩ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑪ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑫ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑬ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑭ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 [[HEI-LRCX-TA-TLSE-UNEXPLAINED-RESIDUAL-1]]根本原因調査
完了）:
①の判定は誤りと判明。対象accn・end_dateの全XBRLタグを機械的に網羅する
手法で再調査した結果、HEI・LRCXともNCI・一時的持分タグ（前回見落とし
分）を含めればTA=TL+SEが完全一致することを確認。「誤登録・訂正のうえ
クローズ（原因は①genuine、探索範囲不足による誤判定だった）」として
BACKLOG_DONE.mdへ移動。追加でTSLA・XOMもサンプル確認し完全一致を確認、
累計10銘柄が例外なく①genuineに分類されたことで、TA=TL+SE違反156件は
ほぼ全件が①genuineへ収束する見込みが高いと判明（詳細は
[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]参照）。
これにより次セッションでの着手順序を更新する:
① [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]（優先度：高。
   横断的な会計恒等式検証レイヤーの新設提案。TA=TL+SE違反はほぼ全件
   ①genuineへ収束する見込みが確認され、「TA==TL+SE+NCI+一時的持分」の
   拡張形での実装可否判断が可能な段階）
② [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高。
   TA=TL+SE違反の分類調査は完了、残る3種〈GP≠Revenue−COGS 43件・
   OI>GP 22件・NI≠EPS×Shares 67件〉の分類調査が未着手）
③ [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
④ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は③側で行う）
⑤ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑥ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑦ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑧ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑨ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑩ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑪ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑫ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑬ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]実装前
シミュレーション完了）:
無条件でNCI・一時的持分を加算する設計は、既存の正しい1,085件のうち33件
（VZ最大-$56.6B・WMT・KO・AVGO・LLY・AMD・ASTS・BROS・CAKE）で新規誤検知
を生む重大な危険があると実証。「TA=TL+SEが不一致の場合のみ拡張形を試す
OR条件フォールバック方式」・許可リスト方式のタグ選定に設計を確定し、
156件中133件（85.3%）が解消見込みと判明。残る23件を
[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]として新規登録（優先度：中）。
これにより次セッションでの着手順序を更新する:
① [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]（優先度：高。設計
   確定済み、実装に着手可能な段階。OR条件フォールバック方式・許可リスト
   方式のタグ選定・検知専用ログ・CHECK-29実装方法まで確定済み）
② [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高。
   TA=TL+SE違反の分類調査は完了、残る3種〈GP≠Revenue−COGS 43件・
   OI>GP 22件・NI≠EPS×Shares 67件〉の分類調査が未着手）
③ [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
④ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は③側で行う）
⑤ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑥ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑦ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑧ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑨ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中・新規。着手条件:
   ①CHECK29本体の実装後）
⑩ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑪ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑫ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑬ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑭ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]実装
完了）:
会計恒等式TA=TL+SE(+NCI+一時的持分)検証をOR条件フォールバック方式・
許可リスト方式のタグ選定でparser.py（`_check_bs_identity_violations()`・
`bs_identity_violations_log.json`新設）・report_consistency_check.py
（CHECK-29/WARN-29）に実装（機能コミット`bd91000f0`）。全105銘柄で
オフライン再パースし156件中133件が拡張形で解消・23件が未解消となる
ことを事前シミュレーションと完全一致で確認。既存1,085件（正常ケース）
への新規誤検知なし（VZ/WMT/KO/AVGO/LLY/AMD/ASTS/BROS/CAKE個別確認済み）、
annual_YYYY.json等の既存データ値は無変更、pytest 497 passed/2 known
failed、WARN 70→83件（純増13件、全てWARN-29）を確認。同エントリを
「実装完了」としてBACKLOG_DONE.mdへ移動し、
[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（着手条件充足、実測23件を
WARN-29で確認）を更新、[[ACCOUNTING-IDENTITY-VALIDATION-LAYER-
MISSING-1]]にTA=TL+SE分の対応完了を反映（残る3種の分類調査が未着手の
ため本体はクローズせず存置）。
これにより次セッションでの着手順序を更新する:
① [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高。
   TA=TL+SE分は対応完了、残る3種〈GP≠Revenue−COGS 43件・OI>GP 22件・
   NI≠EPS×Shares 67件〉の分類調査が未着手）
② [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
③ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は②側で行う）
④ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑤ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。着手条件充足済み。
   COHR・ONDS等の個別調査から着手可能）
⑥ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑦ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑧ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑨ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑩ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑪ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑫ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑬ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]個別調査完了
〈COHR・HEI・ONDS優先〉）:
3件とも①genuineと確定（②タグ選定バグに分類されるものはなし）。
COHR(2022/2023)はCHECK29の「本人データ限定」照合という設計方針そのもの
が原因で検知不可能な構造的限界と判明し
[[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]として別スコープで新規
登録（優先度：中）。HEI(2009-2013)はTemporaryEquityRedemptionValueを
CarryingAmount系タグ不在時のフォールバックとして許可リストに追加すれば
対応可能と判明。ONDS(2023)はCHECK29自体のSUPERSEDESルール不備
（RedeemableNoncontrollingInterestEquityCarryingAmount存在時に
...PreferredCarryingAmountを除外するルールの欠如、自己申告）と判明、
既存ルールと同型の拡張で対応可能。残る20件
（PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW）は未着手のまま。
これにより次セッションでの着手順序を更新する:
① [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高。
   TA=TL+SE分は対応完了、残る3種〈GP≠Revenue−COGS 43件・OI>GP 22件・
   NI≠EPS×Shares 67件〉の分類調査が未着手）
② [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
③ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は②側で行う）
④ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑤ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。COHR・HEI・
   ONDS（8件）は原因確定済み・許可リスト拡張の実装待ち。残る15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉は個別調査未着手）
⑥ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中・新規。
   CHECK29の本人データ限定照合の設計方針拡張検討、該当は現時点でCOHR
   2件のみ）
⑦ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑧ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑨ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑩ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑪ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑫ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑬ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑭ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]のHEI・ONDS型
実装完了）:
CHECK29の許可リストに`TemporaryEquityRedemptionValue`（CarryingAmount系
タグ不在時のフォールバック限定）・`RedeemableNoncontrollingInterest
EquityCarryingAmount`のSUPERSEDESルールを追加（機能コミット
`a910afef2`）。全105銘柄で再検証し156件中133件→139件が解消（HEI×5・
ONDS×1）、副次的にFCX(2013)も改善。他99銘柄・既存133件・COHR型2件・
残り15件のresolved状態は維持を確認。WARN 83→81件（-2）。
これにより次セッションでの着手順序を更新する:
① [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高。
   TA=TL+SE分は対応完了、残る3種〈GP≠Revenue−COGS 43件・OI>GP 22件・
   NI≠EPS×Shares 67件〉の分類調査が未着手）
② [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
③ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は②側で行う）
④ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑤ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中。CHECK29の
   本人データ限定照合の設計方針拡張検討、該当は現時点でCOHR2件のみ）
⑥ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残る15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉が個別調査未着手。
   HEI・ONDSは実装完了・COHRは⑤で別扱い）
⑦ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑧ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑨ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑩ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑪ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑫ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑬ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑭ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）

追記（2026-08-02 セッション終了処理、優先度順に並び順を最終整理）:
本セッション後半（[[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]
実装〈会計恒等式TA=TL+SE検証レイヤー新設、機能コミット`bd91000f0`〉→
HEI・ONDS型許可リスト拡張〈機能コミット`a910afef2`〉、いずれも全105銘柄
検証・pytest/WARN数確認済み）の結果を反映し、
**次セッションでの着手順序（2026-08-02時点、最終版）**を確定する:
① [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]（優先度：高。
   TA=TL+SE以外の残る3種の分類調査が未着手: GP≠Revenue−COGS新規2件・
   OI>GP〈LMT〉・NI≠EPS×Shares〈COHR単位スケール疑い〉）
② [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
③ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中。CHECK29の
   own-accn限定照合という設計方針そのものの緩和検討、該当は現時点で
   COHR2件のみ）
④ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残り15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉が個別調査未着手。
   HEI・ONDSは実装完了・COHRは③で別扱い）
⑤ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は②側で行う）
⑥ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑦ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑧ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑨ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑩ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑪ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑫ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑬ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑭ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）
⑮ [[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]（優先度：低。
   bs_identity_violations_log.jsonのキー順序非決定性、実害なし）

追記（2026-08-02 [[ACCOUNTING-IDENTITY-VALIDATION-LAYER-MISSING-1]]の
残る3種の分類調査が完了し同エントリをクローズしたことを反映し、
次セッションでの着手順序を更新する:
**次セッションでの着手順序（2026-08-02時点、最終版）**:
① [[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]（優先度：中〜高。GOOGL
   (2012/2013)のgross_profitがfact_overrides.json適用順序バグで誤り、
   対応方針未定・他フィールド・他銘柄への波及有無も未調査）
② [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
③ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
④ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中。CHECK29の
   own-accn限定照合という設計方針そのものの緩和検討、該当は現時点で
   COHR2件のみ）
⑤ [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]（優先度：中。COHR自身の
   FY2011 10-Kのshares_diluted単位スケール申告誤り、汎用の桁違い
   検知チェック新設も検討。105銘柄横断スキャン未着手）
⑥ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残り15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉が個別調査未着手。
   HEI・ONDSは実装完了・COHRは④で別扱い）
⑦ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は②側で行う）
⑧ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑨ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑩ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑪ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑫ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑬ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑭ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑮ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）
⑯ [[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]（優先度：低。
   bs_identity_violations_log.jsonのキー順序非決定性、実害なし）

追記（2026-08-02 [[GOOGL-FACT-OVERRIDE-SEQUENCING-BUG-1]]実装完了を反映し、
次セッションでの着手順序を更新する）:
**次セッションでの着手順序（2026-08-02時点、最終版）**:
① [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
② [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
③ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中。CHECK29の
   own-accn限定照合という設計方針そのものの緩和検討、該当は現時点で
   COHR2件のみ）
④ [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]（優先度：中。COHR自身の
   FY2011 10-Kのshares_diluted単位スケール申告誤り、汎用の桁違い
   検知チェック新設も検討。105銘柄横断スキャン未着手）
⑤ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残り15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉が個別調査未着手。
   HEI・ONDSは実装完了・COHRは③で別扱い）
⑥ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は①側で行う）
⑦ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑧ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑨ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑩ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑪ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑫ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑬ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑭ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）
⑮ [[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]（優先度：低。
   bs_identity_violations_log.jsonのキー順序非決定性、実害なし）

追記（2026-08-02 [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]の対応方針確定・
[[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]・[[XBRL-UNIT-SCALE-MISMATCH-
DETECTION-1]]新規登録を反映し、次セッションでの着手順序を更新する）:
**次セッションでの着手順序（2026-08-02時点、最終版）**:
① [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
② [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
③ [[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]（優先度：中〜高。本人データ
   不在時に複数比較年度再掲が競合すると最も古いfilingが勝つ未文書化
   tie-break欠陥、COHR(2010)で実証。105銘柄全体での該当範囲・実装前
   全母集団シミュレーションが未着手）
④ [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]（優先度：中。対応方針確定済み
   〈fact_overrides.json個別上書き、値も確定〉、実装のみ残存）
⑤ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中。CHECK29の
   own-accn限定照合という設計方針そのものの緩和検討、該当は現時点で
   COHR2件のみ）
⑥ [[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]（優先度：中。同一タグ・同一
   期間の値が複数filing間で10のべき乗単位で乖離する場合の汎用検知チェック
   新設提案、105銘柄試験適用で18銘柄・126件を検出済み・個別トリアージ未着手）
⑦ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残り15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉が個別調査未着手。
   HEI・ONDSは実装完了・COHRは⑤で別扱い）
⑧ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は①側で行う）
⑨ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑩ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑪ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑫ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑬ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑭ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑮ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑯ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）
⑰ [[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]（優先度：低。
   bs_identity_violations_log.jsonのキー順序非決定性、実害なし）

追記（2026-08-02 [[FIFO-TIEBREAK-OLDEST-FILING-WINS-1]]の全母集団
シミュレーション結果を反映し、次セッションでの着手順序を更新する。
tie-break条件の広範な見直しは不採用と確定・[[XBRL-UNIT-SCALE-
MISMATCH-DETECTION-1]]へガード条件付き介入として統合したため、
③の位置から除去し繰り上げる）:
**次セッションでの着手順序（2026-08-02時点、最終版）**:
① [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
② [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
③ [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]（優先度：中。対応方針確定済み
   〈fact_overrides.json個別上書き、値も確定〉、実装のみ残存）
④ [[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]（優先度：中。実装方式確定済み
   〈同符号かつ比が10のべき乗値のガード条件でtie-break新filing優先へ
   切り替え、対象は当面COHR2件〉。実装前に(a)既存の恒等式ベース安全網
   との相互作用再検証、(b)ガード適用後の全母集団再シミュレーションが
   必須）
⑤ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中。CHECK29の
   own-accn限定照合という設計方針そのものの緩和検討、該当は現時点で
   COHR2件のみ）
⑥ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残り15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉が個別調査未着手。
   HEI・ONDSは実装完了・COHRは⑤で別扱い）
⑦ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は①側で行う）
⑧ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑨ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑩ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑪ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑫ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑬ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑭ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑮ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）
⑯ [[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]（優先度：低。
   bs_identity_violations_log.jsonのキー順序非決定性、実害なし）

追記（2026-08-02 セッション終了処理、次セッションでの着手順序を最終整理）:
[[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]（fact_overrides.json個別対応）
と[[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]（tie-break恒久対応）は
対象・実装タイミングが密結合のため①に統合表示する。
**次セッションでの着手順序（2026-08-02時点、セッション終了時最終版）**:
① [[COHR-SHARES-DILUTED-UNIT-SCALE-BUG-1]]（優先度：中。実装前最終確認
   完了・fact_overrides.json個別上書き〈2009-2011年度、値も確定済み〉の
   実装のみ残存。[[XBRL-UNIT-SCALE-MISMATCH-DETECTION-1]]のtie-break
   変更部分は、実装しても2010年度1件しか解決せずfact_overrides側で
   重複解決される・現時点で他に該当実ケースがゼロと確定したため、
   当面見送り〈将来の予防的対応として保留〉）
② [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]（優先度：中〜高。
   calc_ttm_series()の日付連続性チェック欠如、ticker非依存の一般的欠陥。
   105銘柄横断スキャンが未着手）
③ [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]（優先度：中。CHECK29の
   own-accn限定照合という設計方針そのものの緩和検討、該当は現時点で
   COHR2件のみ）
④ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残り15件
   〈PLTR/CART/CRWV/BKNG/V/CRM/CELH/ASTS/VRT/RDW〉が個別調査未着手。
   HEI・ONDSは実装完了・COHRは③で別扱い）
⑤ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   現時点のIV実害はゼロ、恒久対応は②側で行う）
⑥ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑦ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑧ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑨ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑩ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑪ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑫ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑬ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑭ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）
⑮ [[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]（優先度：低。
   bs_identity_violations_log.jsonのキー順序非決定性、実害なし）

追記（2026-08-02 セッション終了処理、次セッションでの着手順序を最終整理）:
**次セッションでの着手順序（2026-08-03時点、最終版）**:
① [[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]（優先度：中。layer3_builder.pyと
   parser.pyが同期しない構造的脆弱性は残存するが、既知7件の修正への
   現在進行形の実害はゼロと確定済み）
~~② [[CHECK29-COHR-CROSS-ACCN-TEMPORARY-EQUITY-1]]~~ ✅ 2026-08-03完了
   （2段階ガード〈own-accnのみで厳密一致する場合はフォールバック自体を
   スキップするベースゲート＋重複値ガード〉を実装。COHR(2022/2023)・
   CRWV(2024)・VRT(2018)の4件を解消、実装過程で発見した回帰5件
   〈SOUN2021・PM2010/2011・TSLA2020/2021・HEI2014・FCX2015〉は
   ガードにより再発防止済みで検証済み。詳細はBACKLOG_DONE.md参照）
② [[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]（優先度：高・
   新規。CRM(2011)・VRT(2017)でstockholders_equityが正しいaccnと
   異なる別年度・別filingの無関係な値を誤って採用している独立バグ。
   会計恒等式の前提〈同一filingから一貫して取得〉を崩しかねないため、
   105銘柄横断でのprovenance一致率スキャンを優先的に実施すべき）
③ [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]（優先度：中。残り13件の
   個別調査完了・①genuine2件〈BKNG2011/2012〉・②許可リスト拡張可能
   2件〈ASTS2020・RDW2020〉・③要さらなる確認7件〈PLTR/CART×3/V/CELH/
   ASTS2019〉に分類済み。CRM/VRT(2017)は②〈PARSER-STOCKHOLDERS-
   EQUITY-CROSS-YEAR-MISSELECT-1〉へ分離。次のアクションは②の許可
   リスト拡張実装、または③の個別方針確定）
④ [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]（優先度：中。
   [[TTM-CALC-QUARTER-CONTIGUITY-UNCHECKED-1]]実装完了によりRCAT分の
   根本原因は解消済みの可能性が高いが、本エントリ自体のクローズ判断は
   別途確認が必要なため未着手のまま残置）
⑤ [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]（優先度：中。
   24銘柄分は実害なし・RCAT分〈パターンB〉も年次パーサーのみでは
   IVへの実効果なしと判明）
⑥ [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]（優先度：中〜高。残存: 案a
   〈候補タグ拡張再設計〉・案c〈2タグ合算再設計〉・CRM/JNJ/MRVL/ONDS型の
   未解決分）
⑦ [[LITE-COGS-DA-TAG-UNMERGED-1]]（優先度：低〜中）
⑧ [[STONKS-SILO-FP-LABEL-PERIOD-VALIDATION-1]]（優先度：低〜中）
⑨ [[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]（優先度：低。着手条件:
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]のRCAT分実装と
   同時に副次的効果として解消される見込み）
⑩ [[HON-GROSSPROFIT-2009-RESIDUAL-DISCREPANCY-1]]（優先度：低）
⑪ [[ELF-ROE10YR-RECALC-PENDING-1]]（優先度：中。TANUKI VALUATION定期更新
   で自然解消見込み）
⑫ [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]（優先度：
   低〜中）
⑬ [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]（優先度：低。
   クローズ済み〈実害解消済み〉、デッドコード整理は将来検討）
⑭ [[BS-IDENTITY-LOG-NONDETERMINISTIC-KEY-ORDER-1]]（優先度：低。
   bs_identity_violations_log.jsonのキー順序非決定性、実害なし）

**次セッションでの着手順序（2026-08-05時点、最終版）**:
① [[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]（優先度：高。Stage 1
   〈taxonomy属性①〜⑧非該当26銘柄・372エントリ〉は実装完了・push済み
   〈機能コミット`7c15b2a75`、詳細はBACKLOG_DONE.md参照〉。次はStage 2
   〈属性該当58銘柄のうちBACKLOG_DONE.mdで解消済み確認済みの年度、
   `fixed_by: manual_verification`で登録〉の対象リスト生成に着手する）
② 以下、2026-08-03時点リストから変更なし（上記①〜⑭を参照）:
   [[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]・[[PARSER-STOCKHOLDERS-EQUITY-
   CROSS-YEAR-MISSELECT-1]]・[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]・
   [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]・
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]・
   [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]・
   [[LITE-COGS-DA-TAG-UNMERGED-1]]・[[STONKS-SILO-FP-LABEL-PERIOD-
   VALIDATION-1]]・[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]・[[HON-GROSSPROFIT-
   2009-RESIDUAL-DISCREPANCY-1]]・[[ELF-ROE10YR-RECALC-PENDING-1]]・
   [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]・
   [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]・[[BS-IDENTITY-
   LOG-NONDETERMINISTIC-KEY-ORDER-1]]

**次セッションでの着手順序（2026-08-06時点、最終版）**:
上記①[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]はStage 2〜3b（Stage
2・Stage 3準備・Stage 3a・RDW/ASTS BS恒等式修正・Stage 3bまで全て
実装完了、詳細はBACKLOG_DONE.md「2026-08-05（完了）」参照）につき
本リストから除外。Layer3統一方針の確定（2026-08-06投資調査）を受け、
以下を最優先とする:
~~1. `SEC_EDGAR_LAYER_DESIGN.md`フェーズD Step1: アクセサのラッパー化~~
   ✅ 2026-08-06完了（`layer3_builder.py::get_quarterly_series()`/
   `get_latest_quarterly()`を新設。`get_field_entries()`をそのまま
   呼ぶ薄いラッパー、シグネチャは`(store, field_name)`で既存
   `get_field_entries()`に統一。10フィールドのPascalCase→snake_case
   対応表を確定〈Revenue→revenue・OperatingIncome→operating_income・
   GrossProfit→gross_profit・RD→research_and_development・
   NetIncome→net_income・OCF→operating_cash_flow・
   CapEx→capital_expenditure・SM→selling_and_marketing・
   SBC→stock_based_compensation・SharesDiluted→shares_diluted〉。
   `get_lt_debt_from_normalized()`相当のLayer3版は見送り（BUG-
   NETDEBT-3のdata/annual側フォールバックであり、フェーズD Step2で
   TANUKI VALUATION本体を切り替える際に改めて要否判断する）。実データ
   （AAPL/CPRT/PEP/RCAT/CEG）でnormalized/経由の値と突合、AAPLは
   10/10フィールド完全一致・他4銘柄もselling_and_marketing以外は
   完全一致（乖離2件はいずれも既知課題`[[SCHEMA-NORMALIZED-ISSUES-1]]`
   ②・`[[LAYER3-GA-STANDALONE-TAG-UNMAPPED-1]]`由来と特定、新規bugでは
   ない）。既存消費者は無変更、pytest 505 passed/2 known failed（既知の
   `[[TEST-STALE-IV-1]]`のみ、新規8件追加分すべてpass）。詳細は
   BACKLOG_DONE.md参照
~~2. フェーズD Step2-1: TANUKI VALUATION本体切替（reader.py・
   pipeline.py）~~ ✅ 2026-08-06完了（事前バグ修正2件
   〈`[[LAYER3-CONFIG-RD-TAG-PRIORITY-1]]`・`[[LAYER3-ANNUAL-
   MISCLASSIFICATION-BBAI-1]]`〉→pipeline.py 6箇所をget_field_entries()
   経由に切替→100銘柄全数回帰確認、の順で実施。`get_lt_debt_v2`
   （`get_long_term_debt_latest()`）新規実装、Layer3優先方式を採用
   （RCAT/SPIR/CPRTのSEC EDGAR照合結果に基づく）。全数回帰で
   `roic_wacc_ratio`/`moat_roic`が4銘柄（COHR/LLY/JNJ/KLAC）で値→
   Noneに変化したが、SM/SGA概念混同問題の既知の帰結と特定し、
   ユーザー判断で現状維持を採用（`[[LAYER3-ROIC-WACC-NONE-
   4TICKERS-1]]`参照）。pytest 505 passed/2 known failed（既知）、
   report_consistency_check.py NG=0・WARN=78件（既存と不変）。詳細は
   BACKLOG_DONE.md参照
3. **次はフェーズD Step2-2**: STONKS SILO切替
   （financial_trend_calculator.py・fetcher.py・analyzer.py）
4. フェーズD Step2-3: TANUKI TAIL切替
   （quarterly_review_generator.py・tail_dcf_bridge.py）
5. フェーズD Step2-4: HypeCore切替
6. フェーズD Step2-5: stock.htmlフロントエンド＋診断・補助スクリプト
   7件切替
7. フェーズE: `normalized/`廃止
8. （本線外・優先度中）[[AVGO-CIK-HISTORY-WRONG-LEGACY-CIK-1]]対応
9. （本線外・優先度低）[[ONDS-LOAR-SHARES-SCALE-SUSPECT-1]]・
   [[RCAT-2016Q3-ORPHANED-QUARTERLY-FILE-1]]・
   [[PARSER-MERGED-TAG-MIXING-RISK-1]]・[[LAYER3-ANNUAL-
   MISCLASSIFICATION-NOW-RMBS-1]]・[[LAYER3-ANNUAL-MISCLASSIFICATION-
   MINOR-5TICKERS-1]]・[[LAYER3-SNPS-STALE-TAG-PRIORITY-1]]・
   [[LAYER3-ROIC-WACC-NONE-4TICKERS-1]]
10. 以下、2026-08-03時点リストから変更なし（上記の旧①〜⑭のうち
   Stage系を除く未完了分）: [[TTM-DATA-DRIFT-BEHIND-PIPELINE-1]]・
   [[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]・
   [[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]・
   [[RCAT-TTM-SERIES-CONTINUING-DISCONTINUED-UNCHECKED-1]]・
   [[OPERATING-CASH-FLOW-CONTINUING-DISCONTINUED-GAP-1]]・
   [[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]・
   [[LITE-COGS-DA-TAG-UNMERGED-1]]・[[STONKS-SILO-FP-LABEL-PERIOD-
   VALIDATION-1]]・[[RCAT-FCF-5YR-AVG-ACTUAL-3YR-1]]・[[HON-GROSSPROFIT-
   2009-RESIDUAL-DISCREPANCY-1]]・[[ELF-ROE10YR-RECALC-PENDING-1]]・
   [[REPORT-CONSISTENCY-GROSSPROFIT-COGS-CHECK-MISSING-1]]・
   [[STONKS-SILO-FETCHER-GROSSPROFIT-BACKFILL-DUP-1]]・[[BS-IDENTITY-
   LOG-NONDETERMINISTIC-KEY-ORDER-1]]

---

## セッション終了時ブラッシュアップ（2026-07-19）

**2026-07-18の完了内容**: [[ARCH-DATA-1]]残課題④・[[FYE-CHANGE-BOUNDARY-
COLLISION-BLIND-1]]新規登録・[[FY52WEEK-BS-NULL-SILENT-1]]Phase A完了・
WARN-23全10銘柄検証・[[TTM-STOCK-FIELDS-DEAD-1]]完了・
[[TRUST-SUMMARY-EPIC-1]]棚卸し再検証・[[FCF-ESTIMATE-SKIP-STABLE-1]]完了・
[[FCF-CONVRATE②]]可視化実装完了・[[SKIP-RISK-EVENTS-WIPE-1]]新規登録
（詳細はBACKLOG_DONE.md該当エントリ参照）。

**2026-07-19の完了内容**:
- [[FY52WEEK-BS-NULL-SILENT-1]] Phase B Stage1完了（BS4フィールド
  〈short_term_investments/long_term_debt/short_term_debt/rpo〉の
  absent銘柄179件を一次情報〈SEC EDGAR 10-K原本〉で個別確認し、①候補
  タグ欠落・②生涯フェードアウト・③真の構造的ゼロの3類型に分解。
  安全に解消できる57件（41銘柄）を`parser.py`のXBRL_MAPPINGへ標準タグ
  追加。BACKLOG_DONE.mdへ記録済み〈本体エントリはStage2/3が残るため
  BACKLOG.mdに残置〉。残るStage2/3を[[FY52WEEK-BS-STI-OVERRIDE-
  DESIGN-1]]・[[FY52WEEK-BS-FADEOUT-FALLBACK-1]]として新規登録
- [[GROWTH-SANITY-CLASS-SYNC-1]]完了（MOのfloor〈15%〉問題を解消。
  `growth_sanity.py::TICKER_INDUSTRY_OVERRIDES`にMO: "Tobacco"追加＋
  floor到達中かつindustry_g単独1件候補の場合のみ閾値を2件→1件へ緩和
  する限定的な条件緩和〈案B'〉を実装。事前に全37銘柄でシミュレーション
  し、LOARへの副作用がないことを確認してから実装〈この手法をCHAT_RULES.md
  「候補修正の全母集団シミュレーション」として明文化〉。MO以外への影響
  ゼロを全100銘柄比較で確認。BACKLOG_DONE.mdへ全文移動済み）。残る論点
  5件を新規登録: [[GROWTH-VERDICT-SEQUENCING-BUG-1]]・
  [[WST-SECTOR-MISCLASSIFICATION-1]]・[[JNJ-XOM-PM-FLOOR-RISK-1]]・
  [[GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1]]・
  [[JOBY-STATIC-GROWTH-HARDCODE-1]]
- [[GROWTH-VERDICT-SEQUENCING-BUG-1]]完了（growth_sanityのverdict/
  warnings・TANUKI SCOREのGROWTH_PREMIUM判定が、DCF再計算前の初期計算値
  を検証し続けるシーケンシングバグを根本修正。再計算〈条件付き発火〉
  成功後に`check_growth_sanity()`を採用値`recommended_g`で再実行し
  `verdict`/`warnings`/`signals`/`phase1_growth`/`floor_hit`を更新する
  方式で実装。全母集団シミュレーションで事前確認してから61銘柄を実データ
  再生成し、改善17件〈VZ: AGGRESSIVE→PLAUSIBLE含む〉・悪化3件
  〈ALAB/IONQ/RCAT、PLAUSIBLE→REVIEW。ハイパーグロース×成熟業種平均の
  構造的ミスマッチの正しい表面化と個別調査で確認済み・想定内〉・
  変化なし8件〈ASTS/BKNG/BROS/ELF/KULR/LLY/TER/XOM〉という結果を得た。
  TANUKI SCOREはCONのみGROWTH_PREMIUM→TRIMへ是正。
  `report_consistency_check.py` NG=0・pytest 377 passed（既知の
  MSFT/NVDA 2件除く）を確認。悪化3銘柄の個別調査で判明した副次発見
  〈RCATのsector誤分類、Electronics_General設定だがyfinance実態は
  Aerospace & Defense〉を[[RCAT-SECTOR-MISCLASSIFICATION-1]]として
  新規登録。BACKLOG_DONE.mdへ全文移動済み）
- [[ANOMALY-PATTERN-CATALOG-1]]新規登録（型A「候補集合＋freshness
  収束型」を確定〈実例: KLAC/TER/V/SOFI〉、型B「非分類BS・近似値
  許容型」は予約のみで実例なし。REGISTER-FLOW-REDESIGN-1・
  PREFLIGHT-CHECK-1と統合的に設計する方針。CLAUDE_CODE_START.md
  Step 0.5付近に実装までの暫定注意書きも追加）
- [[NVDA-STI-TAG-UNIDENTIFIED-1]]個別調査完了（$12.4B差額の正体は
  FY2026〈2026-01-25期〉に新規上場した投資先の株式評価額。従来型A
  〈ticker_restrictions単一タグ適用〉で解決できると見込んでいたが、
  債券タグ＋株式タグを合算しても実額と0.9%乖離し、かつ株式タグは
  当該10-K本体では未申告〈後続10-Qの比較開示でのみ登場〉と判明。
  型Aにも型Bにも該当しない新パターン「型C: 資産クラス変化・
  当年度未タグ化型」として整理したが、対応方針〈①近似値許容
  ②翌年度10-K待ち③当面None許容〉は未確定のまま次回持ち越し）
- [[BS-FIELD-NONE-TRANSITION-DETECT-1]]新規登録（NVDA調査の過程で、
  XBRLタグ申告停止による完全欠損を検知する仕組みがBS項目に一切
  存在せず、実例6件〈SOFI-DATA-1・AVGO型14銘柄・LLY-CAPEX-STALE-1・
  CASH-TAG-MISSING-1〈未解決〉・KLAC/TER/V・NVDA〉すべてが偶然発見
  だったと判明。「前年有値→当年None」遷移を検知するWARN-26案として
  登録。[[ANOMALY-PATTERN-CATALOG-1]]の予防側・[[FY52WEEK-BS-NULL-
  SILENT-1]] Phase B/Cと補完関係）

次セッションの筆頭候補（優先順・各項目の優先度欄を確認の上で確定）：
~~① [[GROWTH-VERDICT-SEQUENCING-BUG-1]]~~ ✅ 2026-07-19完了。
   growth_sanityのverdict/warnings・TANUKI SCORE判定を採用値ベースに
   根本修正、61銘柄再生成（改善17件・悪化3件・変化なし8件）。
   詳細はBACKLOG_DONE.md参照
~~① [[FY52WEEK-BS-STI-OVERRIDE-DESIGN-1]]~~ ✅ 2026-07-19完了
   （KLAC/TER/V/SOFIの4銘柄）。NVDAのみ[[NVDA-STI-TAG-UNIDENTIFIED-1]]
   として分離継続。詳細はBACKLOG_DONE.md参照
~~① [[NVDA-STI-TAG-UNIDENTIFIED-1]]~~ ✅ 2026-07-19完了（`cross_filing_tags`
   機構を新設し実装。$12.4B差額の正体〈FY2026新規上場投資先の株式評価額〉
   を、候補タグ合算の近似値〈実額比残差+0.9%〉で解消）。詳細は
   BACKLOG_DONE.md参照
~~② [[BS-FIELD-NONE-TRANSITION-DETECT-1]]~~ ✅ 2026-07-19完了
   （`report_consistency_check.py`へWARN-26新設、既知8件を
   `warn_acknowledged.json`へ事前登録。新規3件〈LLY/SCCO/SPIR〉は
   [[BS-FIELD-NEWLY-MISSING-2026-1]]として分離登録）。詳細は
   BACKLOG_DONE.md参照
~~③ [[FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1]]~~ ✅ 2026-07-19完了
   （WARN-24新設・`fye_change_candidate_scan.py`クラスタリングツール化。
   新規2件〈LITE/WST〉は[[FYE-BOUNDARY-COLLISION-UNCONFIRMED-1]]として
   分離登録）。詳細はBACKLOG_DONE.md参照
~~④ [[SKIP-RISK-EVENTS-WIPE-1]]~~ ✅ 2026-07-19完了（`_pre_existing_risk_events`
   スナップショットパターンで解消、単一コミット）。詳細はBACKLOG_DONE.md参照
~~⑤ [[WST-SECTOR-MISCLASSIFICATION-1]]~~・~~⑥ [[RCAT-SECTOR-MISCLASSIFICATION-1]]~~
   ✅ 2026-07-19完了（2件一括対応、`beta_config.json`のsector値修正のみ）。
   詳細はBACKLOG_DONE.md参照
~~⑦ [[FY52WEEK-BS-FADEOUT-FALLBACK-1]]~~ ✅ 2026-07-19完了（22銘柄）。
   除外3件（CSGP/KULR/RCAT）は[[BS-FIELD-FADEOUT-NONZERO-LAST-VALUE-1]]
   として分離継続。詳細はBACKLOG_DONE.md参照
~~⑧ [[SPLIT-REALTIME-GAP-1]]~~ ✅ 2026-07-20完了（NVDA+新規発見AVGO/CPRT/
   WMT/LRCX/CELH/TSLA〈8銘柄〉・KLAC事前登録、RCAT除外）。詳細はBACKLOG_DONE.md参照
~~⑨ [[GROWTH-STRUCTURAL-MISMATCH-CANDIDATES-1]]~~ ✅ 2026-07-20完了
   （HON: segment_config.json修正でAGGRESSIVE→PLAUSIBLE。残る14銘柄は
   FCF-CONVRATE②型の可視化注記を実装）。詳細はBACKLOG_DONE.md参照
   ~~[[FY-COLLISION-LOG-NONDETERMINISTIC-1]]~~ ✅ 2026-07-20完了（対象7銘柄
   AVAV/CAKE/COHR/CRM/FCX/FICO/HON、詳細はBACKLOG_DONE.md参照）
   ~~[[MRVL-2019-2020-NULL-1]]~~ ✅ 2026-07-20完了（実害なし・構造的境界特性と
   判明。詳細はBACKLOG_DONE.md参照。副次発見はCIK-DISCONTINUITY-OLDEST-YEAR-GAP-1
   として分離登録）
   ~~[[EPS-ANALYZER-NORMALIZE-SCOPE-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md
   参照（net_income共通化過程で41銘柄規模の潜在バグを発見・是正）
   ~~[[KO-SPIR-CF-CAUSE-UNCONFIRMED-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md参照
   ~~[[JOBY-STATIC-GROWTH-HARDCODE-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md参照
   ~~[[CWAN-SNPS-MA-DISTORTION-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md参照
   （対応方針を生FCF平均調整から買収・統合関連加算控除へ転換、47銘柄に一般適用）
   ~~[[CIK-DISCONTINUITY-OLDEST-YEAR-GAP-1]]~~ ✅ 2026-07-20完了。詳細は
   BACKLOG_DONE.md参照（複数CIK統合実装・汎用検知ロジックの登録フロー組み込み
   まで完了）
   ~~[[FCF-EST-DIRECTION-GUARD-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md
   参照（ENTGのSELL→WATCH是正含む21銘柄のIV精度改善）
   ~~[[FCF-EST-NET-BASIS-FIX-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md参照
   （ma_addback計算をnet_amount基準に統一、25銘柄のIV精度改善）
   ~~[[AMZN-DIVERGENCE-HIGH-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md
   参照（原因確定・対応不要、副次発見はAMZN-CONVRATE-OVERRIDE-REVIEW-1として
   分離登録）
   ~~[[FCF-EST-NOTE-DISPLAY-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md参照
   ~~[[FCF-OUTLIER-PREROUNDING-LOSS-1]]~~ ✅ 2026-07-20完了。詳細はBACKLOG_DONE.md参照

**着手条件未達のため次回候補から除外**: [[JNJ-XOM-PM-FLOOR-RISK-1]]
（優先度：中だが着手条件は「候補件数が実際に2件を下回った場合」。
現時点では監視対象として登録のみ、着手不可）

---

**2026-07-23時点の申し送り（AS-IS/TO-BE設計セッション終了時）**:
本日〜翌朝（2026-07-22〜23）のセッションで、全サブシステム監査・
AS-IS/TO-BE設計・499項目の完全定義（`FIELD_DEFINITIONS.md`）・一次データ層
のAS-IS/TO-BE設計（`INPUT_DATA_AS_IS.md`/`INPUT_DATA_TOBE.md`）を実施し、
発見事象**39件を本日新規登録**した（優先度高11件・中19件・低9件、上記
「次セッションの筆頭候補」欄より上に記載の各エントリ参照）。

**次セッションで着手可能な状態にあるもの、いずれも未着手**:
- 本日登録した39件（優先度高11件を筆頭候補とする。特に
  [[NETCASH-DUAL-CALC-1]]・[[NETINCOME-DUAL-PIPELINE-1]]は`TO_BE.md`⑫⑭群
  で統一定義まで確定済みのため実装コストが低い）
- `TO_BE_FINAL_LIST.md`・`TO_BE.md`（①〜⑯群）で確定した統一定義・重複解消・
  `NAMING_CONVENTIONS.md`の命名規則は、いずれもまだ実際のソースコードに
  反映されていない。本日の作業は一貫して「実装は行っていない、定義・
  分類の記録のみ」という範囲宣言のもとで進めたため、対応の実装着手は
  本セッション終了時点で全て次回以降に持ち越しとなっている
- [[FIVE-CATEGORY-RECLASSIFY-1]]（AS-IS-437〜441・404・057/058/060の
  5分類再判定）も同様に未着手

次セッションの筆頭候補は、上記39件のうち優先度高から、実データでの
実害が確認済みかつ統一定義が既に確定している[[NETCASH-DUAL-CALC-1]]・
[[NETINCOME-DUAL-PIPELINE-1]]を推奨する（着手条件の確認は各エントリ参照）。

---

追記（2026-07-24 [[CAPEX-SIGN-UNNORMALIZED-1]]・[[RICE-TTM-CAPEX-SUM-SIGN-1]]完了）:
~~[[CAPEX-SIGN-UNNORMALIZED-1]]~~・~~[[RICE-TTM-CAPEX-SUM-SIGN-1]]~~
✅ 2026-07-24完了（normalizer.py・ttm_calculator.py・STONKS SILO
fetcher.pyの3箇所にCapEx符号正規化を実装。影響銘柄5件
〈ALAB/APGE/INTU/KULR/ONDS〉のnormalized/・ttm/・TANUKI VALUATION
出力を再生成。詳細はBACKLOG_DONE.md「2026-07-24（完了）」参照）。

この完了により、[[SECDATA-STORAGE-FRAGMENTATION-1]]（優先度：中、
common/sec_data統合フェーズ1）の着手条件「[[CAPEX-SIGN-UNNORMALIZED-1]]
の対応方針確定」が満たされ、着手可能な状態になった（同タスクの
「対応方針」「着手条件」欄に反映済み）。ただし上記[[NETCASH-DUAL-CALC-1]]・
[[NETINCOME-DUAL-PIPELINE-1]]（優先度：高）を差し置く優先度ではないため、
次セッションの筆頭候補自体は変更しない。
