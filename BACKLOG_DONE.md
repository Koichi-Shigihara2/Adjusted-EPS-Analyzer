# BACKLOG 完了アーカイブ / アクティブな課題は BACKLOG.md を参照

---

## 2026-07-09（完了）

### ✅ [HYPECORE-TICKERS-INDEX-1] HypeCore画面に新規登録5銘柄が表示されない問題（2026-07-09完了）
- 原因: `docs/value-monitor/hypecore/index.html` の一覧表示が
  `const ALL_TICKERS=[...]` というHTML内に直接ハードコードされた配列を
  参照しており、cik_lookup.csvのhypecore=trueフラグとは完全に独立していた。
  `docs/value-monitor/hypecore/data/tickers.json` という一覧ファイルは
  既に存在していたが、index.htmlはこれをfetchしておらず、`hypecore.py`側も
  このファイルを書き込む処理を持っていなかった（2つとも同一の古い
  ハードコード内容の孤立コピーで、6/26以降どちらも更新されていなかった）
- 対応: (1) `hypecore.py`に`_save_tickers_index()`を新設し、実行のたびに
  `docs/value-monitor/hypecore/data/*_poc.json`の実在ファイルを走査して
  `tickers.json`を再生成するよう変更（TANUKI VALUATIONの
  `_save_tickers_index`と同一パターン）。(2) `index.html`のハードコード配列を
  削除し、`loadAll()`冒頭で`data/tickers.json`をfetchする方式に変更
- 効果: RMBS/ENTG/TER/KLAC/LRCXを含む実在103銘柄（cik_lookup.csv
  hypecore=true 104銘柄中、データ不足で失敗した1銘柄を除く）が
  tickers.jsonに反映され、index.htmlに正しく表示されるようになった。
  以後の新規銘柄登録時もhypecore.py実行のたびに自動反映される
  （手動でのtickers.json更新は不要）
- 検証: ローカルHTTPサーバーでindex.html→tickers.json→各poc.jsonの
  fetchチェーンが正しく機能することを確認（この環境にはブラウザ自動化
  ツールがなく実ブラウザでの目視確認は未実施）。pytest 124件パス・
  report_consistency_check NG=0・check_links.py エラー0件を確認

### ✅ [PARSER-ENTG-COMPYEAR-1] ENTGのFY2022年次Revenue誤抽出（2026-07-09完了）
- 原因: `common/sec_data/quarterly.py` の `_classify_period()` が `is_annual` 判定にform制限を
  課しておらず、10-Q内に混入する比較用contextRef（ENTGのFY2023 Q3 10-Q内にあった
  `start=2022-01-01/end=2022-12-31`のQ1-Q3累計値、form=10-Q）が「最新filed優先」で
  正規のFY2022 10-K年次値（$3,282,033,000）を上書きし、$2,335,963,000（実質Q1+Q2+Q3合計）
  に化けていた。結果としてQ4 2022合成値が$0になりZeroDivisionErrorでrevenue品質チェックが
  クラッシュしていた
- 対応: `is_annual` 判定にform=10-K/10-K-A限定の条件を追加。10-Q由来でduration>300日の
  エントリは比較用ノイズとみなし除外する処理も追加
- 影響確認: 同パターンの混入がAMZN/BSY/DELL/ESTCのOCF/ICF等でも見つかったため
  合わせて再生成（実annual値は別途Dec-31形式で存在しており実害なしと確認済み）
- ENTG Step1〜3再実行完了。理論株価$48.79（乖離-64.8%）で正常完了

### ✅ [XBRL-TAG-KLAC-1] KLACのoperating_income/gross_profit抽出失敗（2026-07-09完了）
- 原因1（GrossProfit）: KLA Corpは自社のFY2021 10-K内に「四半期duration（91日）だが
  fp='FY'」という比較開示データを含めており、`_classify_period()`が`fp=='FY'`のみで
  年次判定していたため誤って年次GrossProfitとして取り込まれ、FY2022以降は本来の
  年次GrossProfitタグ自体をKLAが報告していないため4件の古い四半期データのまま
  更新が止まっていた（Moat Score計算でGM=10%表示、実態は約60%）
- 原因2（OperatingIncome）: KLA CorpはFY2015 10-K以降、年次OperatingIncomeLossタグを
  一度も報告しておらず、ROIC計算が恒常的にNoneになりMoat ScoreのROIC項が0floor
  になっていた
- 対応: (1) `_classify_period()`のis_annual判定に`fp=='FY' and days>130`の下限を追加し、
  四半期durationの誤タグ混入を排除。(2) `pipeline.py`の`_calc_moat_inputs()`にGrossProfit
  annual欠落時の四半期12件合算フォールバックを追加。(3) `_calc_roic_wacc_ratio()`に
  `_estimate_ttm_operating_income()`（直近4四半期のGrossProfit-RD-SM合算）フォールバックを
  新設。この2フォールバックは汎用実装のため他銘柄にも自動適用される
- 効果: KLAC Moat Score 0.240→0.843（GM=10%→61%、ROIC=0%→100%capped）、
  Phase1=5yr→9yr、理論株価$58.59→$70.33（乖離-68.2%）に是正
  （当初「$82.06」と報告したのはstdout表示バグによる誤報告。実際に保存された
  JSON値は$70.33。詳細は[[STDOUT-JSON-MISMATCH-1]]参照）
- 横断監査（軽め）: 直近3年operating_income全欠落銘柄が他に6件（ASTS/BX/JNJ/LLY/SOFI/XOM）
  存在することを確認。→ [[XBRL-TAG-KLAC-1-FOLLOWUP]]で検証・対応完了

### ✅ [CHECK-QREV-FYE-1] check_revenue_quality()の暦年グルーピング誤検知（2026-07-09完了）
- 原因: `check_revenue_quality()`のチェック4（四半期合計vsFY年次整合性）が年次end日の
  暦年ラベル（`a_end[:4]`）で四半期をグルーピングしており、非12月決算企業
  （KLAC=6月期・LRCX=6月期・DELL=1月期・ESTC=4月期等）で本来同一会計年度に属する
  四半期が正しく合算されず、false positiveの❌ISSUEを出していた
- 対応: 年次end日を起点にtrailing 12ヶ月窓（370日以内）で4四半期を抽出する
  会計年度ベースのグルーピングに変更
- 検証: KLAC/LRCX/ESTCはISSUE解消。DELLはISSUE解消の上で別要因（直近四半期の
  実売上急増+87.5%、AI関連需要とみられる）によるWARNのみに変化。report_consistency_check.py
  はNG=0を維持

### ✅ [XBRL-TAG-KLAC-1-FOLLOWUP] operating_income欠落6銘柄への新設フォールバック適用確認（2026-07-09完了）
- 対象6銘柄中BXはtanuki=false（TANUKI VALUATION対象外）のため除外、残り5銘柄
  （ASTS/JNJ/LLY/SOFI/XOM）で検証
- 検証の過程でバグA・バグBの2件を新規発見・根本修正（詳細は下記参照）：
  - バグA: `_calc_moat_inputs()`のGrossProfit年次フォールバック条件が
    `elif not gp_annual:`（完全に空の場合のみ発動）になっており、年次データが
    存在するが直近年とマッチしない（stale）場合にフォールバックが発動しない
    欠陥があった。`else:`（pairs 0件なら常に発動）に修正
  - バグB: `_estimate_ttm_operating_income()`がGrossProfit/RD/SMを独立に
    「直近4四半期」取得しており、いずれかのタグ報告が停止しているとR&D控除
    漏れ等でTTM営業利益を過大・無意味に算出していた（LLY: RDが2022-2023年で
    停止、JNJ: RDタグ自体が空）。3フィールド共通の期末日（intersection）が
    4件未満ならNoneを返す方式に修正
- 効果（バグA・B修正後の最終結果）:
  - ASTS: Moat Score 0.000→0.183、GM算出可能化（0.00→0.46）。ROICは元々の
    無意味な誤算出値から「算出不可（0扱い）」の安全側挙動に是正
  - LLY: ROIC過大評価（1.00 capped）を是正し0.00（算出不可）に。
    乖離率+23.0%→-25.2%へ逆転（修正後の方が実態に近いと判断）
  - JNJ: 同様にROIC過大評価（0.64）を是正し0.00に。既存のR&Dタグ抽出漏れ
    （システム全体の既知ギャップ、今回の修正対象外）に起因
  - SOFI/XOM/KLAC: 回帰なしを確認
- 副産物: KLACの当初報告値「$82.06」がstdout表示バグ（[[STDOUT-JSON-MISMATCH-1]]）
  による誤報告と判明し、記録を$70.33に訂正

### ✅ [STDOUT-JSON-MISMATCH-1] pipeline.py stdout表示とJSON保存値の不一致（2026-07-09完了）
- 原因: `_save_result()`内、`recommended_g`によるDCF再計算ロジック
  （`segment_configured=False`の銘柄が対象）がローカル変数`valuation`を
  再代入するだけで、呼び出し元（`process_ticker`ループ）の`valuation`
  オブジェクトを更新していなかった。stdoutの完了メッセージ・
  `results[ticker]`は再計算前の古い`valuation`を参照し続け、実際に
  JSON保存される値（再計算後）と食い違っていた
- 対応: `_save_result()`の戻り値を`None`→`dict`に変更し、最終的な
  `valuation`を返すよう修正。呼び出し元も`valuation = self._save_result(...)`
  と戻り値を受け取る形に変更
- 影響範囲: `segment_configured=False`は102銘柄中65銘柄。ただし実際に
  発火するのは`recommended_g`が算出され再計算が成功した場合のみのため、
  65銘柄全てが被害を受けているとは限らない
- 本日確認済みの被害銘柄（BACKLOG_DONE.md記載の理論株価とJSON実値の突合により確認）:
  RMBS（$83.54→実際$87.50）・ENTG（$48.79→実際$28.11）・TER（$108.49→実際$53.64）・
  LRCX（$110.06→実際$58.51）・CON（$40.47→実際$17.78、記録は[[新規銘柄登録]] WST・CONエントリで訂正済み）。
  KLACは[[XBRL-TAG-KLAC-1]]対応時（2026-07-09）に$70.33へ訂正済み
- 検証: RMBS/ENTG/TER/KLAC/LRCXでpipeline.py再実行し、修正後はstdout表示が
  JSON保存値と完全一致することを確認。JSON値自体は修正前後で不変
  （表示のみのバグで計算結果には影響しなかったことを確認）
- **未検証の既知リスク**: BACKLOG_DONE.md内の過去記録（JNJ・VST/FCX/SCCO/CEG/KO・
  ALAB等、`segment_configured`変更やG変更・逓減DCF適用を伴う記録）は同種の
  発火条件（`segment_configured=False`時点での再計算）に該当しうるが、
  当時のコード・データ状態を遡って検証する工数が大きいため今回は棚卸し
  一覧化のみに留め、個別の正誤判定は未実施

### ✅ [新規銘柄登録] RMBS・ENTG・TER・KLAC・LRCX（2026-07-09完了）
- CIK確認・cik_lookup.csv登録（status=active, registration_source=manual,
  registration_note="半導体関連・手動一括登録"）
- RMBS/TER/LRCX: Step1〜3完了、異常なし
  （RMBS理論株価$83.54/乖離-23.8%、TER理論株価$108.49/乖離-69.1%、
  LRCX理論株価$110.06/乖離-67.0%）
- ENTG: Step1でFY2022年次Revenue誤抽出を検知、PARSER-ENTG-COMPYEAR-1として
  根本修正後Step1〜3完了（理論株価$48.79/乖離-64.8%）
- KLAC: Step3完了後operating_income/gross_profit欠落を検知、XBRL-TAG-KLAC-1
  として根本修正後再計算完了（Moat Score 0.240→0.843、理論株価$58.59→$70.33）
- 副産物: CHECK-QREV-FYE-1（非12月決算企業の誤検知修正）、
  XBRL-TAG-KLAC-1-FOLLOWUP（他6銘柄への横展開確認）をBACKLOG登録

### ✅ [TAIL-DCF-TABIDX-1] index.htmlのDCFタブ非同期再描画がtab index不一致（2026-07-09完了）
- `docs/portfolio/tail/index.html` の `buildTabDcf()`（Tab 4: DCFシナリオ）内、シナリオファイル
  未ロード時の非同期コールバックが誤って `modalTabIdx === 3` / `renderModalBody(ticker, 3)`
  （KPIトレンドタブのindex）を参照していたのを `modalTabIdx === 4` / `renderModalBody(ticker, 4)` に修正
- コメント「Tab 3: DCFシナリオ」も実態（TABS_CORE/TABS_SATのindex=4）に合わせ「Tab 4」に修正
- KPIトレンド側（L1365、modalTabIdx===3）は正しい実装のため変更対象外と確認済み

---

## 2026-07-08（完了）

### ✅ [BACKLOG-DEDUP-CHECK-1] BACKLOG.md・BACKLOG_DONE.md間の項目ID重複チェック（2026-07-08完了）
- 背景: [[TTM-NULL-1]]・[[STONKS-DIV-1]]で2件連続、BACKLOG_DONE.mdに完了記録があるのに
  BACKLOG.md側の削除が漏れて再度アクティブ項目として残存していたパターンが発覚したため、
  両ファイル間で同一項目IDの重複がないか全数チェックを実施した
- 抽出範囲: `###`見出し形式に加え、旧セクションで使われている行頭`✅`/`❌`箇条書き形式のID宣言も
  対象に含めて全数抽出（旧形式のみに存在するIDが見出し限定の抽出では漏れることが判明したため）
  - BACKLOG.md: 40件（すべて`###`見出し形式）
  - BACKLOG_DONE.md: 219件（`###`見出し形式 + 旧`✅`箇条書き形式の混在）
- **BACKLOG.md・BACKLOG_DONE.md 両方に存在するID: 2件（いずれも削除不要と判定）**
  - `DESIGN-8`: BACKLOG.mdは8-3・8-4（未着手）、BACKLOG_DONE.mdは8-1・8-2・8-5・8-6（完了済み）で
    枝番が重複しておらず、同一エピック配下の子タスクを分担管理する正常な設計と確認
  - `UI-DISCOVER-1`: BACKLOG.mdの現行エントリ自体が「✅ 影響予測機能追加（2026-07-05完了、
    BACKLOG_DONE.md参照）」「[ ] その他のUI課題（未着手）」と部分完了を明示しており、
    BACKLOG_DONE.mdの完了記録はその一部分を正しく裏付けている（親タスクは意図的に継続中）
  - → 今回はBACKLOG.mdからの削除対象なし（TTM-NULL-1・STONKS-DIV-1のような真の削除漏れは
    このタイミングでは他に見つからなかった）
- **副次的発見: BACKLOG_DONE.md内部でのID再利用（6件、削除対象ではないが記録として残す）**
  - `SEC-CTRL-1`・`STONKS-DIV-1`・`TTM-NULL-1`: 同一機能・同一バグへの段階的対応（初回実装→
    追加対応）としてのID再利用で、実害なしと判断
  - `DCF-RELIABILITY-1`・`MP-GAUGE-NEEDLE-1`: 関連はするが厳密には別内容の対応（前者は
    「調査のみ・対応不要」と「実装」、後者は「針とラベルの重なり修正」と「0/100ラベル除去」）に
    同一IDが再利用されている。実害は軽微（両エントリともBACKLOG.mdには存在せず参照される機会が
    少ない）だが、本来は枝番号（`-2`等）を振るべきだった
  - `TAIL-UX-1`: **最も紛らわしい例**。2026-06-24「TANUKI TAIL使い方ガイダンス充実」（ツールチップ
    追加）と2026-07-05「TANUKI TAIL詳細モーダルの一覧性向上（Phase1+2）」という**内容的に無関係な
    2つのタスク**が同一IDを共有している。`[[TAIL-UX-1]]`形式のwikiリンクで参照した場合にどちらを
    指すか一意に定まらない状態
- 再発防止策の提案（ファイル追記はチャット側判断のため提案のみ）:
  1. BACKLOG更新のタイミング（BACKLOG.mdの「タスク完了後の①②③手順」）に、複数項目を一括対応した
     場合は「対応した全IDについてBACKLOG.mdへのgrepでヒット0件を確認してからコミットする」ことを
     明記する（TTM-NULL-1/STONKS-DIV-1はまさに5項目一括コミットの中で1手順が漏れたケース）
  2. 新規IDを採番する前に`grep -n "\[候補ID\]" BACKLOG.md BACKLOG_DONE.md`でID未使用を確認する
     ステップを新規課題登録時のルールに追加する（TAIL-UX-1型の無関係タスクへのID再利用を防止）
  3. 本チェック（項目ID抽出→重複検出）をワンショットではなく`check_backlog_dedup.py`のような
     再利用可能スクリプト化し、月次メンテナンスタスク（CLAUDE_CODE_START.md「⑤横断整合性チェック」）
     に組み込むことを検討する

---

### ✅ [STONKS-DIV-1] analyzer.pyのゼロ除算ガード再確認・回帰テスト追加（2026-07-08完了）
- 経緯: BACKLOG.mdに残っていた本項目も2026-06-27に一度「調査の結果、3箇所（r_start/rev/
  avg_past）はすでにガード済みと判明（実装修正不要）」として対応済みだったが、
  BACKLOG.mdからの削除漏れで再度アクティブ項目として残存していた（[[TTM-NULL-1]]と同型の
  記録漏れパターン）
- 再調査: 指摘された3箇所（L222の`r_start > 0`・L314の`_lpr()`内`rev <= 0`・L625の
  `avg_past > 0`）は現在も全てガード済みと再確認。TTM-NULL-1の前例（同種パターンの
  見落とし発見）を踏まえ、`analyzer.py`全体（1267行）の除算演算子を全数grepし直したが、
  今回は追加の未ガード箇所は発見されなかった（実装修正なし）
- テスト: 既存の`TestStonksDivisionGuards`（L222/L314相当の2件）に加えて、
  L625（avg_past=0）を検証する回帰テストが未整備だったため
  `test_discontinuous_growth_avg_past_zero_skips_comparison`を追加。
  過去YoY平均がちょうど0%・直近YoYが+300%（急拡大条件）になるデータを構成し、
  ガードを外すと実際にZeroDivisionErrorが再現することを事前確認した上で採用
- pytest: 167 passed（新規1件込み）+ 既知の無関係な2件失敗（[[TEST-STALE-IV-1]]、NVDA/MSFT）

---

### ✅ [TTM-NULL-1] ttm_calculator.py calc_ttm_series()のval=None TypeErrorガード追加（2026-07-08完了）
- 経緯: BACKLOG.mdに残っていた本項目は2026-06-27に一度対応済み（L94のcalc_ttm/L185の
  _build_q4_quarterly_entries を`sum(e["val"] or 0 for e in ...)`にガード済み、
  BACKLOG_DONE.md参照）だったが、BACKLOG.mdからの削除漏れで再度アクティブ項目として残存していた
- 再調査の結果、同一ファイル内`calc_ttm_series()`（L489、rolling TTM系列生成。update.py経由で
  本番パイプラインが実際に使用）に同型の未ガード`sum(e["val"] for e in last4)`が別途存在すると判明
  （2026-06-27修正時のgrep漏れ。`_calc_q4_implied`のL312は既にガード済みだったため見落とされた）
- 対応: `common/sec_data/ttm_calculator.py` L489を`sum(e["val"] or 0 for e in last4)`に修正
- テスト: `tests/test_ttm_calculator.py`に`TestCalcTtmSeriesNullValGuard`を追加（1件）。
  修正前コードで実際にTypeErrorが再現することを確認した上で回帰テストとして採用
- pytest: 166 passed（新規1件込み）+ 既知の無関係な2件失敗（[[TEST-STALE-IV-1]]、NVDA/MSFT）

---

### ✅ [MACRO-NFP-HIST-1] NFP過去履歴の水準→前月比一括再計算（2026-07-08完了）
- 背景: [[MACRO-NFP-1]]（2026-07-07完了）でNFPの新規fetchロジックは前月比に修正済みだったが、
  `05_events.csv`内の既存NFP行370件（1996-01〜2026-07）は水準値のまま据え置かれており、
  `05_audit.py`のCHECK-2がNG（水準残存）を検出し続けていた
- 新設: `src/market/macro_pulse/05_backfill_nfp_mom.py`（一括変換スクリプト、`--dry-run`対応）
  - FRED PAYEMS全期間水準系列を再取得し、`(level_now - level_prev) * 1000`で前月比に変換
    （`05_import_history.py`の`import_from_fred()`と同一方式）
  - 対象月判定: release_dateの日が「01」→release_date月そのものが観測月（旧FRED一括投入 /
    スケジュール未一致のrefresh由来）。日が「01」以外→release_date月の1ヶ月前が観測月
    （BLS実発表日でスケジュール一致したrefresh由来。NFPの実発表日が月初1日になることはなく
    両者は曖昧なく判別可能なことを`05_indicator_schedule.csv`の実データで確認済み）
  - `forecast_source="actual_as_forecast"`の8行（consensus=actualのコピー）はconsensus/
    surprise/surprise_pctも新actualに合わせて更新。それ以外362行（consensus空欄）はactualのみ更新
  - 書き換え前に`05_events.csv.bak_{timestamp}`へバックアップを自動作成
- 実行結果: NFP全370行を変換（1996-01-01〜2026-07-02、スキップ0件）
- 検証: `python src/market/macro_pulse/05_audit.py` → CHECK-2 NG=0を確認
  （WARN 49→48件。うち1件はNFP水準の偶然一致によるものが解消され、MoM値の偶然一致
  （nfp_2017-04-01/05-01が共に205000）が新たにWARN対象になったが人間確認要の範囲内で許容）
- テスト: `tests/test_macro_pulse_logic.py`（18件）・`tests/`全体（165件）継続パスを確認
  （test_iv_formula.py MSFT/NVDAの2件失敗は[[TEST-STALE-IV-1]]起因の既知の無関係な失敗）

---

## 2026-07-07（完了）

### ✅ [MACRO-NFP-1] MACRO PULSE NFP表示ロジック修正（2026-07-07完了）
- 発覚経緯: ユーザー報告（RECENT SIGNALSパネルのNFP行が5/8・6/1・6/5・7/2の4回連続で
  ACTUAL=PREV=159.0K・CHANGE=±0と表示、stale疑い）→ 調査の結果、fetch失敗ではなく
  ロジック誤り2件の複合と判明（詳細調査ログは会話履歴参照）
- 原因①: `05_main.py`の`fetch_event_row()`がPAYEMS（雇用者数の**水準**、約15.9億人規模）を
  そのまま`actual`に格納しており、本来の「NFP＝前月比新規雇用者数」になっていなかった。
  フロントエンドの`fmtK()`が水準値を`/1000`表示するため、月次のわずかな水準変動が
  小数第1位に丸め込まれ同一表示に見えていた
- 原因②: `run()`内でscheduledループが追加した行を`refresh_monthly_indicators()`に渡す
  `events`スナップショットが反映されておらず、同一FRED観測値が別々のevent_idスロット
  （例: nfp_2026-06-01とnfp_2026-07-02、共に158984.0）に二重書き込みされていた
  （Building Permits・Michigan Consumer Sentimentでも同型の重複を実データで確認）
- 対応①: `fred_latest_with_prev()`を新設し、`fetch_event_row()`のNFP分岐で
  `actual = round((level_now - level_prev) * 1000)`（千人→人単位の前月比）に変更。
  `05_import_history.py`の`import_from_fred()`も同様にNFPのみ`s.diff()*1000`で変換
  （既存05_events.csvの過去NFP行は本タスクでは書き換えず、[[MACRO-NFP-HIST-1]]に切り出し）
- 対応②: `run()`が`refresh_monthly_indicators()`に渡す`events`をscheduledループの
  新規行を反映したスナップショットに更新。加えて`dedupe_new_rows()`を新設し、
  「同一indicator×同一actual値×release_date差が窓（obs_to_release_lag+14日）以内」の
  行を最終マージ前に除外する防御的ガードを追加
- 対応③: 再発防止用の軽量監査スクリプト`src/market/macro_pulse/05_audit.py`を新設
  （CHECK-1: 重複行検出=WARN、CHECK-2: NFP水準残存兆候=NG）。CHECK-1はIC4WSA等の
  移動平均系指標が正常運用でも同値継続することがあるためWARN、CHECK-2は前月比なら
  大きく振れるはずの値が狭いレンジに収束していることを検出するためNGとした
- テスト: `tests/test_macro_pulse_logic.py`新設（18件、fred_latest_with_prev・
  NFP前月比変換・dedupe_new_rows・監査スクリプトの2チェックを網羅、実際に発生した
  Building Permits/Michigan Consumer Sentimentの重複を再現する回帰テストを含む）。
  既存pytest（tests/全体、165件）は無影響（test_iv_formula.py MSFT/NVDAの2件失敗は
  [[TEST-STALE-IV-1]]起因の既知の無関係な失敗）
- 副産物: 過去NFP履歴の水準→前月比一括再計算を[[MACRO-NFP-HIST-1]]としてBACKLOG登録

---

## 2026-07-06（完了）

### ✅ [HYPE-TRANS-1] HYPECOREステージ遷移確率が「現ステージへの過去滞在履歴なし」で0%誤表示（2026-07-06完了）
- 発覚経緯: ユーザー報告（HYPECORE SOFI画面、ステージ遷移確率が全項目0%表示）
- 原因: `docs/value-monitor/hypecore/detail.html` の `calcTrans(m,cur)` が
  現在stageから過去に一度も遷移していない場合（`tot=0`）に `tot=...||1` の
  フォールバックで分母を1に置き換えていたため、「算出不能」が「0%（絶対に
  遷移しない）」という誤った意味の数値として表示されていた。特定銘柄固有の
  データ不整合ではなく、全銘柄で起こりうる汎用的なエッジケース（現在stageが
  直近月に初めて到達したもので、それ以前の履歴内に出現しない場合に発生）
- 対応: `calcTrans` の戻り値を `{insufficient, data}` 形式に変更し、`tot===0`
  の場合は `insufficient:true` を返す。呼び出し元（遷移確率リスト描画部）で
  `insufficient:true` の場合はバー幅0%のまま数値表示を「データ不足」に切り替え、
  従来の0%埋めを廃止（恒久対応）
- 影響銘柄: 98銘柄全件をシミュレーション再検証し、SOFI（stage1・履歴内出現0回）・
  FLYW（stage3・同0回）・RKLB（stage2・同0回）の3銘柄で該当を確認。修正後は
  3銘柄とも「データ不足」表示に切り替わることをPlaywrightで実描画確認
- 回帰確認: 通常ケース（NVDA、tot>0）で従来通りprob値（%）が降順ソートで
  表示されることを確認し、既存表示への影響なしを確認

---

## 2026-07-05（完了）

### ✅ [UI-DISCOVER-1] 「連想・考察→影響予測」機能追加（方式C: 独立パイプライン・2026-07-05）
- 新規独立スクリプト `src/discover/impact_predictor.py` を追加（collect.py/catalyst.py本体は変更なし）。
  collect.py実行後(`--source news`)・catalyst.py実行後(`--source catalyst`)にそれぞれ呼び出し、
  銘柄単位でその日/週の新規項目をまとめてGrokに1回渡し、各項目のdirection(positive/negative/neutral)・
  magnitude(高/中/低)・thesis_effect(補強/弱化/中立)・1行summaryを生成
- 前提整備: `collect.py` `append_to_monthly_history()` にnews item安定id(ticker×日付内の連番)を付与
  （catalyst.jsonは既存の`id`フィールドをそのまま利用）
- 出力先は新規ファイル `docs/discover/data/impact_predictions_YYYY_MM.json`（news_history/catalyst.json
  は無改変・案2）。catalyst.htmlは各カタリストの`first_detected`から必要な月ファイルを逆引きしてマージ
- GitHub Actions（Discover_Update.yml・Catalyst_Update.yml）に実行ステップとgit add対象を追加、
  `.gitattributes`にmerge=ours設定を追加
- catalyst.pyは既存の累積分を再処理せずfirst_detected==当日実行分のみを対象とし、
  [[CATALYST-DEDUP-1]]の無制限増加問題を新機能側では悪化させない設計とした
- 検証: モックGrok応答による単体ロジックテスト（news/catalyst両モード、新規分のみが対象になることを確認）、
  Playwrightでnews_history.html・catalyst.htmlの実描画（1行サマリ表示・予測未生成月の404を握りつぶすフォール
  バック動作）を確認。pytest 123件は無影響（データ層のみの変更のため）
- 副産物: [[CATALYST-DEDUP-1]]・[[GROK-MODEL-PRICE-1]]をBACKLOG登録（優先度未定・別タスク）

---

### ✅ [TAIL-UX-1] TANUKI TAIL詳細モーダルの一覧性向上（Phase1+2 完了・2026-07-05）
- Phase2: AI視点セクションを3実装（detail.html/index.htmlタブ/index.htmlダッシュボードZoneE）から
  detail.html一本化。表示順を「業績見通し（KPI予想・新規）→テーゼへの問いかけ・次回確認論点→
  歴史的類比等→5観点（折りたたみ・デフォルト閉）」に再構成し、優先度のない均等表示を解消
- index.htmlのAI視点タブ（buildTabCall2）・ダッシュボードZoneEを削除し、detail.htmlへの
  リンク導線に置き換え。内部統制タブがindex 6→5にシフトするため関連参照4箇所を同期修正
- Playwrightでdetail.html（PLTR/SOFI/TSLA=KPI予想テーブル正常描画、ADBE=データなし表示）と
  index.htmlモーダル（タブ構成6個・内部統制タブ動作・ZoneEリンク遷移）を検証、新規コンソール
  エラーなしを確認。副産物として[[TAIL-DCF-TABIDX-1]]（既存のtab index不一致バグ）を発見しBACKLOG登録

---

## 2026-07-03（完了）

### ✅ [ARCH-DATA-1-YTD] SEC四半期正規化ロジック 全101銘柄ロールアウト完了（2026-07-03 完了）
- commit: c00c3abc5（バグA・B修正）, 1c0920ec4（全銘柄データ再生成）
- [[BUG-CON-YTD-1/2]]（2026-07-02完了）で特定した14銘柄のうちAMD/AMZN/HWMをスポットチェックした際、
  AMZN固有の新規回帰バグ2件を追加発見・修正した：
  - バグA: `_calc_gross_profit()`がend日付のみでRevenue/COGSを引き当て、単独四半期値と
    未解決の累積値（is_ytd=True）が同一endで共存すると累積値を誤採用（GrossProfitが実際の
    数倍に膨張）。`_index_quarterly_by_end()`新設で単独四半期値を優先するよう修正
  - バグB: `_build_missing_quarter_implied_entries()`が算出する欠落四半期のend/start日付が
    暦四半期境界と1日ずれ、`_build_q4_implied_entries()`の結果と重複排除できず、
    FY2022/2023/2024のOCF/ICF/CFF/CapEx/SBC/DA/NetIncomeが12/31と1/1の2エントリに
    二重計上。日付演算のオフバイワンを修正（AMZN TTM NetIncome 2023〜2025年3月末時点で
    最大+53.7%誤って膨張していたものを是正）
- 検証: pytest129件パス（既存123+新規test_normalizer.py 6件）。AMD/HWMはデグレなし
  （TTM系列バイト単位で完全一致）。APGE/AVAV/CIX/CON/ESTC/GEV/HEI/PM/RCAT/SOUN/ZSの
  11銘柄を横断スキャンし同パターン0件を確認
- 全101銘柄で`update.py`・`pipeline.py --skip-risk`を再実行し、
  `report_consistency_check.py`でNG=0（WARN=1件、ELF PSステール値・既存事象で無関係）を確認
- IV変化: AMZN+3.5%, AVAV+12.3%, BKNG-6.6%, FCX-23.2%, SITM-11.9%, XOM-2.2%
  FCF_Base変化（IV不変含む）: 40銘柄（5年ロールウィンドウ境界四半期の重複計上是正・
  誤除外復元による想定通りの補正）
- 副産物: [[TEST-STALE-IV-1]]（test_iv_formula.pyのALPHA-REDESIGN-1未追従）を発見しBACKLOG登録

---

## 2026-07-02（完了）

### ✅ [TICKER-META-1] cik_lookup.csv登録メタデータ機能追加（2026-07-02 完了）
- commit: 337bf3d29
- cik_lookup.csvにstatus/registered_date/registration_source/registration_note列を新設
- 既存97銘柄をstatus=active/registration_source=unknownでバックフィル
- CLAUDE_CODE_START.mdの新規銘柄登録手順にStep 0.5として組み込み（登録理由が不明な場合はユーザーに確認を求める仕様）

---

### ✅ [新規銘柄登録] WST・CON（ミネルヴィニ・スーパーストック条件）（2026-07-02 完了）
- commit: 3d45e6794
- registration_source=technical_screening を新設カテゴリとして追加
- WST: Step0〜8完了。セグメント設定（Proprietary Products 81.07%/West Vantage 18.93%）。理論株価$96.85、現在株価比乖離-73.5%
- CON: Step0〜8完了。単一セグメント（設定不要）。β=0.511（yfinance未提供のため2年週次データから手動算出）。理論株価$17.78、乖離-43.4%
  （当初「$40.47、乖離+31.5%」と記録したのは[[STDOUT-JSON-MISMATCH-1]]による誤報告。2026-07-09にJSON実値へ訂正）

---

### ✅ [新規銘柄登録] APGE（TANUKI TAIL satellite登録）（2026-07-02 完了）
- commit: 3d45e6794
- 収益系XBRLタグが皆無（臨床段階バイオで売上ゼロ）と判定。TANUKI VALUATION（DCF）・STONKS SILO（黒字化パス追跡）とも設計上不適合
- cik_lookup.csv: tanuki=false, stonks_silo=false
- TANUKI TAIL satelliteとして `APGE_thesis.json` を作成（テーゼ: カタリスト追跡・治験マイルストーン主導）

---

### ✅ [新規銘柄登録] SN（一時的にTANUKI VALUATION保留）（2026-07-02 完了）
- commit: 3d45e6794
- 2025年まで20-F提出企業（外国民間発行体）のため四半期データが2026年Q1分のみ存在し、TTM/トレンド系列が構築不能
- Discover/HypeCore/EPS Analyzerは完了。cik_lookup.csv: tanuki=false（一時的措置とregistration_noteに明記）
- BACKLOG.mdに [SN-TANUKI-DELAY-1] を登録（2026年8月Q2 10-Q提出後にtanuki=true復帰予定）

---

### ✅ [BUG-CON-YTD-1/2] SECデータ正規化: SA/YTD重複判定バグ根本修正（2026-07-02 完了）
- commit: 3d45e6794
- 発端: CON（2024年IPO）のFY2023 Revenue 48.8%乖離調査
- `common/sec_data/quarterly.py::_process_entries()`: グルーピングキーを `end` → `(start, end)` に変更。同一end・異なるstart（例: Q3単独 vs Q1-Q3累計）を誤って重複扱いしYTDを破棄していた不具合を修正
- `common/sec_data/normalizer.py`: 3段階修正
  - `_ytd_to_quarterly`: チェーン先頭がYTD（起点Q1未申告）の場合、その値自体は未解決として分離しつつ差分計算の起点には使用
  - `_build_missing_quarter_implied_entries` 新設: 複数累計候補（6ヶ月YTD・9ヶ月YTD等）から欠落四半期を逆算、重複導出も排除
  - passthrough（生SA）優先の重複排除、未解決YTD残骸の最終除去
- 検証: pytest全123件パス。CON FY2023はQ1〜Q4復元、年次値との乖離0%に解消
- 影響範囲確認（既存96銘柄の raw/normalized データは未再生成）: 101銘柄中87銘柄に差分。うち2023年以降の直近データに影響する14銘柄
  （AMD, AMZN, APGE, AVAV, CIX, CON, ESTC, GEV, HEI, HWM, PM, RCAT, SOUN, ZS）を特定。
  CON・HEI・ZSをスポット検証し、いずれも旧コードの誤り（疑似四半期・二重計上）を修正したことを確認
  （例: HEI CapEx旧Q3=$23.33M〈Q2+Q3混入〉→新Q3=$12.26M、Q1〜Q4合計が年次と完全一致）
- 残タスク: BACKLOG.mdに [ARCH-DATA-1-YTD] として、全銘柄再生成前のスポットチェック・before/after全件差分の手順を記録済み

---

### ✅ [MINERVINI-NOTE-1] ミネルヴィニ4銘柄のregistration_note詳細化（2026-07-02 完了）
- commit: 0b67a6a62
- WST/APGE/CON/SNのregistration_noteに、moomoo AIスクリーニングが簡易版（株価・出来高ベースのテクニカル条件のみ）であり、
  本来の条件であるRS Rating・EPS/売上成長率の加速が未評価である旨を明記
- SNは既存の「tanuki=false一時的措置」注記を保持したまま追記

---

## 2026-07-01（完了）

### ✅ [PREVENT-4] system_health.pyの監視対象拡充（2026-07-01 完了）
- check_f_tail: 全thesis銘柄（9件）のctrl/latest.json存在確認
- check_g_hypecore: poc.json全件のInf/NaN混入チェック＋generated_at鮮度確認（14日閾値）
- check_h_config: tanuki=trueのbeta_config未登録・segment/maturityの孤立エントリ検出
- check_i_eps: summary.jsonの鮮度（14日閾値）＋eps=trueカバレッジ確認
- 実行結果: F/G/I=✅（正常）、H=⚠️（QBIT孤立エントリ検出: segment_config.json・maturity_config.json）

---

### ✅ [EXTREME-FEAR-1] extreme-fear/index.html 正式登録（2026-07-01 完了）
- **重複削除**: F&Gゲージカード（① F&G INDEX）・ステータスバナー・renderFG/renderBanner/fgLabel/gaugeSVG を削除
- **独自機能4つを保持**: ① 買い候補 TOP10 / ② 投入額シミュレーター / ③ 過去EF一覧 / ④ 買い付け方針メモ
- **共通化**: site-theme.css・site-header.js・site-nav.js を適用、`data-tool="ef"` 追加
- **nav 登録**: site-nav.js に `key:'ef'` エントリを Market Pulse の直後に追加
- **site-header.js**: `'ef'` ツール定義を TOOL_META に追加（タイトル: EXTREME FEAR / サブタイトル: 買付支援・Macro Buy Signal）
- **site-theme.css**: `body[data-tool="ef"] { --acc: #f43f5e; }` を追加（恐怖赤アクセント）
- **SYSTEM_MAP.md**: Extreme Fear をシステム一覧に追記、site-header.js 適用ページ一覧を更新

---

### ✅ [EPS-BX-1] BXのEPS ANALYZERでfetch失敗リスク解消（2026-07-01 完了）
- `config/cik_lookup.csv`: BX の eps フラグ true → false（TANUKI-FIN-1で金融機関向けDDM実装まで保留）
- `docs/value-monitor/adjusted_eps_analyzer/data/summary.json`: BXエントリを直接削除（generate_summaryがマージ方式のため手動削除が必要）
- 結果: summary.json が95→94銘柄。EPS ANALYZER一覧からBXが除外された。

---

### ✅ [DUPONT-COLOR-1] DuPont ROE色分け統一（2026-07-01 完了）
- `docs/value-monitor/tanuki_valuation/stock.html` L1539: `> 0.15 ? 'var(--green)' : > 0 ? 'var(--txt)'` → `>= 0.15 ? '#4ade80' : >= 0 ? '#facc15'` に変更。赤も `var(--red)` → `#f87171` に変更。
- `docs/common/glossary.json`: `tscore_dupont_roe_color` キーの「オレンジ」表記を「黄」に修正（実装色 #facc15 と一致させる）
- 統一後: tanuki_score/index.html と stock.html の両方で 0〜15%=黄、<0%=赤、15%以上=緑 に統一。

---

### ✅ [QBIT孤立エントリ削除] QBIT残骸config3ファイル削除（2026-07-01 完了）
- PREVENT-4のcheck_hが検出したQBIT孤立エントリ（QBTSの旧ティッカー残骸）を削除
- 削除ファイル: `config/segment_config.json` / `config/maturity_config.json` / `src/value/tanuki_valuation/kpi_config.py`
- 再実行結果: `[H] Config: ✅ 整合OK` に改善。repo全体でQBIT参照ゼロ確認済み

---

### ✅ [STOCK-GLOSSARY-1] stock.htmlへのglossaryツールチップ導入（2026-07-01 完了）
- stock.html末尾に `../../common/info-tooltip.js` をimport追加
- DuPont card関数に第5引数 `infoKey` を追加し、ROEカードのラベルに `data-info="tscore_dupont_roe_color"` を付与
- αステップ内Phase1スパンに `data-info="stock_moat_phase1"` を付与
- glossary.json に `stock_moat_phase1` キーを新規追加（Moat Score由来のPhase1期間算出ロジックの説明）

---

## 2026-06-27（完了）

### [TAIL-PAGE-1] TANUKI TAIL 詳細ページ別ページ化
**完了日:** 2026-06-27
**分類:** 機能追加 / TANUKI TAIL

#### 実施内容
- docs/portfolio/tail/detail.html を新規作成
- タブ廃止・全情報を縦スクロール1ページに統合
- 構成: サマリーバー / 投資テーゼ（折りたたみ）/ 最新レビュー+KPIトレンド（左右並列）/ AI視点+DCFシナリオ（左右並列）/ 内部統制 / 過去レビュー履歴
- 銘柄切り替えナビ（prev/next）・SHA-256認証・site-nav.js統合
- index.htmlの「詳細」ボタンをdetail.html?ticker=XXXへのリンクに変更
- DCF将来株価テーブル・過去レビュー前期比デルタ表示・KPI赤枠ハイライト実装

---

### [BUG-CTRL-EFFECTIVE-1] sec_ctrl_fetcher.py effective判定ロジック修正
**完了日:** 2026-06-27
**分類:** バグ修正 / TANUKI TAIL

#### 原因
_RE_EFFECTIVEの正規表現が "were effective" の直接隣接のみを想定していたため、
"were, in design and operation, effective" のように間に語句が入るPLTR等のケースで
effective=Noneになっていた。

#### 対応
_RE_EFFECTIVEに "were\s+.{0,60}\beffective\b" パターンを追加。
既存9銘柄のctrlデータを再判定・更新（PLTR: None→True）。

---

### [TAIL-UX-1-P1] TANUKI TAIL詳細モーダル ダッシュボードタブ追加（Phase1）
**完了日:** 2026-06-27
**分類:** UX改善 / TANUKI TAIL

#### 実施内容
- 詳細モーダルにダッシュボードタブを先頭に追加（既存6タブは維持）
- ゾーンA: 乖離率・理論株価・現在株価・直近スコア+判定を1行表示
- ゾーンB: 最新レビュー概要（左）＋スコア推移スパークライン（右）の2カラム
- ゾーンC: KPIトレンド小型グラフ（左）＋DCFシナリオ簡易テーブル（右）の2カラム
- ゾーンD: AI視点・内部統制を折りたたみで表示
- KPI・DCF・ctrlのキャッシュ済み即時再描画対応
- データなしKPIの非表示対応
- COREテーブルに「直近スコア」列を追加

#### 残課題（TAIL-UX-1として継続）
- スコア推移グラフのX軸右端が切れる
- その他一覧性向上の改善余地あり

---

### [CN-ENB-1] company_names.jsonのENB残存クリーンアップ（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `docs/common/company_names.json` から `"ENB": "ENBRIDGE INC"` エントリを削除
- TANUKI-ENB-1（2026-06-26）でENBをカナダ企業として除外済み、company_names側の残骸を除去

---

### [RKLB-CLEANUP-1] RKLBのtickers.json残存・eps_sector空欄修正（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `docs/value-monitor/tanuki_valuation/data/tickers.json` から RKLB エントリを削除（tanuki=false銘柄）
- `config/cik_lookup.csv` の RKLB の eps_sector に `宇宙・航空` を設定

---

### [PICK-DUP-1] daily_pick.pyの同日重複エントリバグ修正（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `daily_pick.py` の history 書き込み前に同日エントリ削除処理を追加（`[e for e in history if e.get("date") != today_str]`）
- `docs/value-monitor/tanuki_score/history.json` の既存重複を除去（25→11件、同日は最新1件を保持）

---

### [TTM-NULL-1] ttm_calculator.pyのval=None TypeErrorガード追加（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `ttm_calculator.py` の2箇所（FLOW_FIELDS合算・Q4合成top3合算）で `sum(e["val"] for e in ...)` → `sum(e["val"] or 0 for e in ...)` に修正
- pytest TestTTMNullValGuard（2テスト）を追加して回帰防止

---

### [STONKS-DIV-1] analyzer.pyのゼロ除算ガード確認・テスト追加（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- 調査の結果、3箇所（r_start/rev/avg_past）はすでにガード済みと判明（実装修正不要）
- pytest TestStonksDivisionGuards（2テスト）を追加してガードの継続的動作を担保

---

### [PREVENT-1] CLAUDE_CODE_START.mdチェックリスト追記（2026-06-27クローズ）

**完了日:** 2026-06-27（追記は前セッションで実施済み）
**対応内容:**
- 「新規計算フィールドを追加した場合、report_consistency_check.pyにCHECKを追加」項目が CLAUDE_CODE_START.md L697 に既実装
- BACKLOG から削除

---

### [PREVENT-2] CLAUDE_CODE_START.mdチェックリスト追記（2026-06-27クローズ）

**完了日:** 2026-06-27（追記は前セッションで実施済み）
**対応内容:**
- 「新規フィールド追加時の全画面grepで確認」「廃止機能の残骸grep確認」「複数銘柄への横展開確認」項目が CLAUDE_CODE_START.md L698-702 に既実装
- BACKLOG から削除

---

### [PREVENT-3] pytestの対象拡充（Inf/None/ゼロ除算）（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- TTM-NULL-1対応時に `tests/test_pipeline_logic.py` へ TestTTMNullValGuard（2テスト）を追加
- STONKS-DIV-1対応時に TestStonksDivisionGuards（2テスト）を追加
- HYPE-INF-1対応時に hypecore.py の rev_ttm_prior=0 時 Inf 非発生テストを追加
- pytest 119 → 123 件、全件パス確認済み
- 当初3件とも未カバーだったが、各バグ修正と同時にテスト追加することで対応完了

---

### [SEC-CTRL-1] ctrl JSONパス変更・Grok翻訳追加・既存ファイルマイグレーション（2026-06-27完了）

**完了日:** 2026-06-27
**対応内容:**
- `src/tail/sec_ctrl_fetcher.py`: 保存先を `{TICKER}_ctrl.json` → `{TICKER}/{QUARTER}.json` + `{TICKER}/latest.json` に変更
- `_translate_item4()` 関数を追加: Grok API（grok-3-mini→grok-3→grok-2-1212フォールバック）でitem4_excerptを日本語訳し `item4_excerpt_ja` フィールドとして保存
- `docs/portfolio/tail/index.html`: fetchパスを `latest.json` に変更、`buildTabCtrl` で日本語訳を上部に表示し英文を `<details>` 折りたたみに変更
- 既存9ファイル（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/SOUN/TSLA）を新ディレクトリ構造へマイグレーション
- `SYSTEM_MAP.md`: パス記述を新構造に更新

---

### [TAIL-CTRL-JA-1] TANUKI TAIL 内部統制タブ：日本語翻訳＋履歴表示
**完了日:** 2026-06-27
**分類:** 機能追加 / TANUKI TAIL

#### 実施内容
- sec_ctrl_fetcher.py: Grok翻訳フィールド（item4_excerpt_ja）追加、保存構造を {TICKER}/{QUARTER}.json + latest.json + index.json の3ファイル構成に変更
- 既存9銘柄（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/SOUN/TSLA）のctrlデータを新構造に移行し、Grok翻訳を一括適用（18ファイル）
- index.html buildTabCtrl: 日本語訳を上部に表示・英文原文を<details>折りたたみに移動、履歴セレクター追加（2期以上の場合のみ表示）
- SYSTEM_MAP.md: ctrlデータパス記述を新構造に更新

#### コミット
0e7eb2518

---

### [TAIL-CTRL-TRANS-1] TANUKI TAIL 内部統制タブ：日本語翻訳＋履歴表示
**完了日:** 2026-06-27
**分類:** 機能追加 / TANUKI TAIL

#### 実施内容
- sec_ctrl_fetcher.py: Grok翻訳(_translate_item4())を追加し item4_excerpt_ja フィールドを生成
- 保存構造を {TICKER}_ctrl.json（1ファイル上書き）から data/ctrl/{TICKER}/{QUARTER}.json + latest.json + index.json に変更
- 既存9銘柄（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/SOUN/TSLA）を新構造に移行し翻訳を一括追加（18ファイル）
- index.html buildTabCtrl: 日本語訳を上部表示・英文原文を折りたたみに変更、履歴セレクター追加（2期以上で表示）
- SYSTEM_MAP.md: ctrlデータパス記述を更新

#### 補足
- 翻訳はGrok APIで生成。既存ファイルに item4_excerpt_ja が存在する場合は再翻訳スキップ
- 履歴セレクターは現状1期分のみのため非表示。次回fetch後2期分になると表示される

---

## 2026-06-26（完了）

### [TAIL-SAT-CORE-1] satelliteモーダルをcore同等の6タブ構成に変更（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `TABS_SAT = ['戦略']` → `['テーゼ', '最新レビュー', 'KPIトレンド', 'DCFシナリオ', 'AI視点', '内部統制']` に変更
- `openModal()` 内の KPI・DCFシナリオ・ctrl fetch から `isCore &&` 条件を除去
- `renderModalBody()` の `!isCore` early return と `isCore` 変数を削除してタブ分岐を統一
- CRWV（satellite）で内部統制タブが表示され、effective=False / MW=12件を確認可能に
- PLTR/SOFI（core）の6タブが引き続き正常表示されることをPlaywrightで確認

---

### [CATALYST-DATA-1] catalyst.json初回データ投入（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `catalyst.py --all` で全95銘柄（hypecore=true）のカタリストを一括生成（Grok API使用）
- 登録銘柄数: 95銘柄 / カタリスト総数: 682件
- 上位: TSLA(9件), FLYW(9件), NVDA(8件), AAPL(8件), ALAB(8件)

---

### [DISCOVER-THEMES-1] macro_themes_history.json初回生成・.gitattributes登録（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `explore_macro_themes()` を直接呼び出して初回エントリを生成（Grok API使用）
  - collect.py は日曜のみ生成する設計のため、バイパス用スクリプトで実行
- 生成テーマ3件: 「AI電力需要爆発」[高]、「量子コンピューティング商用化」[中]、「LEO衛星通信拡大」[中]
- `.gitattributes` に `merge=ours` を追加（discover/data/catalyst.jsonの直後）
- 「過去のテーマを見る」機能が稼働状態に

---

### [HYPE-FLAG-1] CSGP/ZSのcik_lookupフラグ設定（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- CSGP（CoStar Group、Real Estate、黒字）: `hypecore=true, tanuki=true, eps=true, stonks_silo=false`
  - beta_config.jsonにβ=0.72が既存 → pipeline.pyを実行してlatest.json生成（理論株価$9.87）
- ZS（Zscaler、Technology/Software-Infrastructure、赤字）: `hypecore=true, tanuki=false, eps=false, stonks_silo=true`
  - stonks-silo pipeline を実行してresults.jsonに追加（score=88.0、10x_CANDIDATE）

### [HYPE-ENB-1] ENBのhypecore=false修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- ENBの `hypecore=true` → `false` に修正（カナダ企業・TANUKI-ENB-1で永続除外決定済み）
- 他フラグ（tanuki/eps/stonks_silo=false）は現状維持

---

### [SEC-CTRL-2] TANUKI TAIL内部統制データ未取得銘柄の一括生成（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `sec_ctrl_fetcher.py` を残8銘柄（ADBE/APP/CELH/CRWV/NVDA/PLTR/SOFI/TSLA）に実行
- 全9銘柄の ctrl データが揃い TANUKI TAIL の内部統制タブが全銘柄で表示可能に
- 注目: CRWV のみ `not_effective / MW=12`（重要な欠陥あり）、PLTR は `unknown`（判定不能）

### [HYPE-INF-1] HypeCoreのpoc.jsonにInf値が混入するバグ修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `rev_ttm_prior` の 0 を `np.nan` に変換（0除算による `rev_yoy=inf` を防止）
- `op_margin` の `rev=0` を `np.nan` に変換（`ni/0=-inf` を防止）
- `safe()` 関数に `np.isinf(v)` チェックを追加（JSON出力前の Inf→None 変換）
- `z_score_series()` 入力 Series の `inf/-inf` を `np.nan` に置換（スコアへの伝播防止）
- ASTS/JOBY を再生成して Inf 値 0 件を確認（ASTS 9件・JOBY 3件が解消）

### [STAGE0-STOCK-1] stock.htmlでstage=0（S0失望期）が非表示になるバグ修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `STAGE_LABELS` に `0:'失望/蓄積期'` を追加
- falsyチェック（`hStage ?`）をnullチェック（`hStage != null ?`）に変更
- 現時点で stage=0 の実績データなし（全期間スキャン済み）。コード修正のみ実施。

### [ALPHA-REDESIGN-2] stock.htmlのα乗算残存修正（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- `calcSensIV()` から `(1+alpha)` 乗算を除去（感度分析テーブルの2倍過大表示を修正）
- `renderChart()` の `alphaPremium` 計算・「α プレミアム」バーを削除
- CALCULATION BREAKDOWN Step 7 ヘッダーを `×(1+α)` 表示 → `Phase1: N年（Moat Score由来）` に変更
- Step 7 説明文・P_t 計算式・P_t 企業価値表示から `(1+α)` を除去
- `applyLayer2Toggle()` の pt 計算から `(1+alpha)` を除去

### [EVAL-3] Moat Scoreスクリーニング画面への組み込み（2026-06-26完了）

**完了日:** 2026-06-26
**対応内容:**
- tanuki_valuation/index.html にMoat Score列を追加（乖離率の隣、ソート対応）
- α列を削除（ALPHA-REDESIGN-1で廃止済みの残骸）
- stats barの「平均α」→「平均Moat」に変更
- RKLBのlatest.jsonを再生成（moat_score欠落を解消）
**結果:** 94銘柄中94銘柄にmoat_score表示。スコア範囲0.00〜0.95、平均0.33。

### [ALPHA-REDESIGN-1] alpha乗算廃止・Moat Score駆動Phase1期間自動算出（2026-06-26完了）

**概要:** DCFの `v0*(1+alpha)` 乗算を廃止し、企業の競争優位性（Moat Score）から
Phase1期間を自動算出する方式に切り替えた。alphaは参照値としてJSONに保持。

**実装内容:**

- `calculator/adjustments.py`
  - `MoatScoreResult` dataclass を追加
  - `calculate_moat_score()` を追加
    - Moat Score = `gross_margin_norm×0.40 + roic_norm×0.40 + fcf_margin_norm×0.20`
    - 正規化基準: GM=100%、ROIC超過=(roic-Rm)/30%、FCF=30%
    - Phase1 years = `3 + round(moat_score × 7)`（範囲: 3〜10年）
  - `calculator/__init__.py` に `calculate_moat_score, MoatScoreResult` をexport

- `core_calculator.py`
  - STEP 4e 追加: `financials` から `moat_gross_margin_3yr/moat_roic/moat_fcf_margin_3yr` を読んで `calculate_moat_score()` を呼び出し
  - three_stage/two_stage DCF、WACC感度分析、シナリオ計算、将来価値計算の全 `phase1_years`/`high_growth_years` を `_moat_phase1_years` に統一
  - `calculate_intrinsic_value(..., alpha=0.0)` に全箇所を変更
  - 結果dictに `moat_score/moat_phase1_years/moat_gross_margin_norm/moat_roic_norm/moat_fcf_margin_norm` を追加

- `pipeline.py`
  - `_calc_moat_inputs()` を追加: normalized quarterly JSONからGM 3年平均、annual JSONからFCF margin 3年平均を算出
  - `calculate_pt()` 呼び出し前に `financials.update(_moat_inputs)` でmoat入力を注入
  - ROIC: `rice.roic_wacc_ratio × 0.10` を `moat_roic` として渡す

**動作確認結果（2026-06-26実行）:**

| 銘柄 | Moat Score | Phase1 | IV (変更後) | upside | 判定 | 旧alpha | 変化メモ |
|------|-----------|--------|-------------|--------|------|---------|---------|
| NVDA | 0.892 | 9yr | $648.50 | +231.4% | WATCH | 1.0 (cap) | alpha廃止で非乗算化。Phase1 5yr→9yr拡張で相殺 |
| PLTR | 0.641 | 7yr | $89.40 | -16.9% | WATCH | 0.0 | Phase1 5yr→7yr延長によりIV増加 |
| MSFT | 0.713 | 8yr | $381.76 | +7.3% | WATCH | 1.0 (cap) | alpha廃止（v0×2.0→v0）でIV大幅減 |
| IONQ | 0.000 | 3yr | $41.84 | -18.2% | WATCH | 0.0 | GM/ROIC/FCF全0→最短Phase1。upside低下 |

**pytest:** `tests/test_pipeline_logic.py` 119件 全パス（2026-06-26確認）

**変更ファイル:**
- `src/value/tanuki_valuation/calculator/adjustments.py`
- `src/value/tanuki_valuation/calculator/__init__.py`
- `src/value/tanuki_valuation/core_calculator.py`
- `src/value/tanuki_valuation/pipeline.py`

### [SS-1] Stonks Silo 営業利益ETA四半期系列合成
**完了日:** 2026-06-26
**判断:** 現状維持でクローズ
**理由:**
- NET・IONQの営業利益はQ1 2026時点で全8四半期赤字かつ悪化傾向
  （NET: -62M$、IONQ: -272M$）
- 「改善トレンドなし」表示は正しい判定であり、無理にETAを出すと誤情報になるリスクがある
- 機能上の欠落ではなく仕様通りの動作と確認

### [TANUKI-ROE-2-PARTIAL] DuPont分析パネルをstock.htmlに追加
**完了日:** 2026-06-26
**対応内容:**
- FINANCIAL HEALTHセクション直後にDUPONT ANALYSISパネルを追加
- 4カード構成：純利益率・資産回転率・財務レバレッジ・ROE（分解値）
- ROEは値に応じて色分け（>15%緑・>0%白・負値赤）
- dupont フィールドがない銘柄は非表示
**残タスク:** 業種平均比較・潜在ROE試算はデータソース確保後に別途実装

### [MP-ASSETFLOW-UI-1] 資産クラス資金フロービジュアライザーUI調整
**完了日:** 2026-06-26
**対応内容:**
- short_bond tickerを^IRXからDGS3MOに統一
- スペクトルバーの高さを3px→8pxに変更
- fallback ※マークは実装済みのため現状維持

### [SILO-UX-1] 黒字化チャート達成済みラベル追加
**完了日:** 2026-06-26
**対応内容:**
- buildProfitPath() で state === 'done' の指標ドット右に「✅ 達成済」ピルを追加
- 表示対象: 粗利益・FCF等、直近Q値が黒字の指標
- スタイル: 緑色背景・緑テキスト（var(--grn)）
**背景:** 達成済み指標と未達指標が混在するチャートでどれが達成済みか不明瞭だったUX問題を解消

---

## 2026-06-25（完了）

### [HYPE-1] HypeCoreフェーズ判定の精緻化 — 完了（2026-06-25）
- `run_poc()` に `s4_streak`（S4連続月数）を追加し `determine_stage()` に渡すよう変更
- `determine_stage()` にS4脱出条件を追加: `s4_streak>=6 AND rev_yoy>20 AND ni_yoy>0` → S2へ脱出
- `detect_substage()` にS4長期継続ラベルを追加: `stage_months>=6 AND real_strong` → "長期調整・実体強"
- PLTR: 2026-04が"長期調整・実体強"（6ヶ月目）、2026-05でS2脱出に変更。NVDA: 影響なし
- 変更ファイル: `src/value/hypecore/hypecore.py`

## 2026-06-25（廃止）

### [RICE-2] CF_adjのMatrix判定への組み込み — 廃止（2026-06-25）
理由: 設計再検討の結果、実装不要と判断。削除。

---

## 2026-06-25（TANUKI-MAXEPS-1）

### [TANUKI-MAXEPS-1] 最大EPS計算・TANUKI SCORE表示（2026-06-25完了）
対応内容:
- `src/value/tanuki_valuation/pipeline.py` に max_eps / max_eps_per / max_eps_reliability の計算・格納を追加
  （max_eps = (GAAP NI TTM + SBC TTM) / 希薄化後株式数、一過性損失は将来拡張）
  - GAAP NI TTM ソース: `dupont.ni_ttm`（quarterly TTM集計）
  - SBC TTM ソース: `financial_health.sbc_ttm`（annual最新年SBC）
  - 株式数ソース: `components.diluted_shares`
  - HIGH: 3フィールド全取得 + max_eps > 0
  - MED: ni_ttm か sbc_ttm の一方欠落、ゼロ代入で近似計算
  - LOW: 2フィールド以上欠落 または max_eps <= 0
- `docs/value-monitor/tanuki_score/index.html` の詳細テーブルに3列を追加
  - GAAP PER: `components.per`（既存チップバッジの値をテーブルにも表示）
  - 最大EPS PER: `components.max_eps_per`（信頼性LOW時 opacity:0.45 でグレーアウト）
  - 乖離: GAAP PER − 最大EPS PER（正値=オレンジ表示、SBC依存度を可視化）
- NVDA実行確認: max_eps=6.8535, max_eps_per=29.0x, reliability=HIGH
  （GAAP PER 30.4x との乖離 +1.4x: SBCが純利益比4%と小さいためギャップ小）

---

## 2026-06-25（小規模ロジック系 一括対応）

### [MP-WEEKEND-1] 休場日（土日）ラベル追加（2026-06-25完了）
対応内容: `docs/market-monitor/market-pulse/index.html` の `renderAssetFlow()` を改修。
ワークフローは既に `cron: "35 21 * * 1-5"` で月〜金のみ実行済みのため、フロントエンドで補完。
- 取引日間に土日がある場合、「休場」行をグリッドに挿入
- 今日が土日の場合、最新取引日より前に当日を含む休場行を先頭表示
- 休場行は背景 `var(--sur2)` + 不透明度0.5で視覚的に区別

### [MP-CSV-1] CSVヘッダー整合チェック（2026-06-25完了）
対応内容: `src/market/market_pulse/collect_and_send.py` の `save_data_to_json_and_csv` 関数の
CSV書込み前にヘッダー整合チェックを追加。
- 既存CSVを読込み、先頭行のヘッダーを `CSV_COLUMNS` と比較
- 不一致の場合、全データ行を読込んで新ヘッダーで全体再書込み
- `extrasaction='ignore'` により旧カラム値は破棄、新カラムには空値が入る

### [HYPE-DISP-5] HypeCore グラフX軸整列改善（2026-06-25完了）
対応内容: `docs/value-monitor/hypecore/detail.html` の Chart.js 設定を修正。
- `eChart`（期待の強度）の左Y軸に `afterFit: ax => { ax.width = 55; }` を追加
- `eChart` の右Y軸（y2）に `afterFit: ax => { ax.width = 30; }` を追加
- `fChart`（実体の強度）の左Y軸にも同様の `afterFit` を追加
- `fChart` に不可視ダミー右Y軸（`ticks/grid/border: {display:false}`, `width=30`）を追加
- 両グラフのプロット幅が統一され、X軸の時間目盛りが縦に揃う

---

## 2026-06-25（表示統一系 一括対応）

### [HOME-COLOR-1] ツールカードのテーマカラー修正（2026-06-25完了）
対応内容: `docs/index.html` の `.card-score` アクセントカラーを `#14b8a6`（シアン）→ `#84cc16`（ライム）に変更。
色相環の最大空白（MACRO PULSE H=38° ～ MARKET PULSE H=160°、122°のギャップ）の中点 H=82° に配置し、
隣接色との最小距離44°を確保。全9色が色相環上でより均等に分布するよう改善。

### [TSCORE-DISP-1] `—` と `N/A` の表示統一（2026-06-25完了）
対応内容: `docs/value-monitor/tanuki_score/index.html` を調査した結果、コード全体で `N/A` 表記は使用されておらず
すべて `—` に統一済みであることを確認。`pct()` 関数に `typeof v !== 'number' || !isFinite(v)` の防衛チェックを追加し、
数値以外の値（文字列・NaN等）が渡された場合も `—` を返すよう強化。

### [TSCORE-DISP-2] JOBY・ASTSのフェーズ欄空欄修正（2026-06-25完了）
対応内容: `docs/value-monitor/tanuki_score/index.html` の `stageLabel()` 関数を修正。
`stage=0`（未フェーズ）・`stage=null`・範囲外（1〜4以外）の場合に明示的に `—` を返すよう変更。
従来のコードは `stage=0` で空文字列が生成される可能性があったため、これを防ぐ。

### [TSCORE-DISP-3] RICEマトリクスY軸ラベルの可読性改善（2026-06-25完了）
対応内容: `docs/value-monitor/tanuki_score/index.html` のSVG Y軸ラベルを
`transform="rotate(-90,...)"` の縦書きから横書きに変更。
プロット左上に `↑ RICE`（font-size:10）と `対数軸`（font-size:8）の2行ラベルを配置。

### [DISCOVER-DISP-3] 新規候補カードのタグ視認性改善（2026-06-25完了）
対応内容: `docs/discover/index.html` のタグCSSを全面改善。
- `.screen-pass`: alpha `.08` → `.15`、`border:1px solid` 追加、文字色 `#10b981` → `#34d399`
- `.conv-低`: 文字色 `#64748b`（低コントラスト）→ `#94a3b8` に変更、border追加
- `.cand-catalyst` / `.conv-高` / `.conv-中`: alpha `.12` → `.20`、border追加で視認性向上

### [MP-DISP-5] 資産クラス並び順の視覚的勾配追加（2026-06-25完了）
対応内容: `docs/market-monitor/market-pulse/index.html` の `renderAssetFlow()` に
グラデーションバー（高さ3px、青→シアン→紫→緑→アンバー→オレンジ→赤）を追加。
グリッド右側の7データ列に対応する幅で描画し、「安全資産→リスク資産」の方向を視覚的に表現。

---

## 2026-06-25（実装）

### [TAIL-DISP-3] SATELLITE一覧「戦略名」の表記揺れ修正（2026-06-25完了）
対応内容: `docs/portfolio/tail/data/positions/CRWV_thesis.json` および
`SOUN_thesis.json` の `strategy_name` フィールドを
「グロース追及」→「グロース追求」に修正。HTML/JSファイルに該当箇所なし。

### [HOME-ANIM-1] LIVEドットのパルスアニメーション統一確認（2026-06-25完了）
対応内容: `docs/index.html` の全9カードを調査した結果、
すべてのカードに `class="dot dot-live"` が一貫して適用されており、
`@keyframes live` パルスアニメーションは混在なし・統一済みであることを確認。
修正不要のため変更なし。

### [MP-DISP-6] AI分析末尾の俳句的フレーズ削除（2026-06-25完了）
対応内容: `src/market/market_pulse/collect_and_send.py` のGrokプロンプトから
「最後に俳句を一句（5-7-5）のみ添えること」の指示を削除し、
代わりに「末尾に俳句・詩的フレーズ・文学的な一文を添えることは禁止。総評の最終文は具体的な相場シナリオで終えること」という禁止文を追加。
既存データ（`market_data.json` の `summary` フィールド末尾に残る俳句）は次回ワークフロー実行時に自動更新される。

### [CATALYST-1] カタリスト発掘・追跡機能
完了日: 2026-06-25
対応内容:
- `src/discover/catalyst.py` 新規作成（Grok Web検索で銘柄ごとにカタリスト発掘・週次再評価）
  - 対象: `get_hypecore_tickers()` 経由 cik_lookup.csv の hypecore=true 94銘柄
  - 呼び出し①: 新規カタリスト発掘（grok-3 web検索）
  - 呼び出し②: 既存「未達」カタリストの再評価（status: 未達/達成済み/消滅）
  - ID採番: `{TICKER}-{YYYY}-{3桁連番}` 形式、冪等（再実行で積み上げ）
  - `--ticker`/`--all`/`--dry-run` オプション対応
- `docs/discover/catalyst.html` 新規作成
  - 重要度・種別・ステータス・銘柄テキストフィルター
  - 未達カタリストを上位表示、達成済み/消滅は折りたたみ
  - ステータス色分け: 未達=青、達成済み=緑、消滅=グレー
  - site-header.js + site-nav.js 使用
- `docs/common/site-nav.js`: 「カタリスト」エントリをニュース履歴の直後に追加
- `.github/workflows/Catalyst_Update.yml` 新規作成（毎週日曜 JST 23:30）
- `.gitattributes`: `docs/discover/data/catalyst.json text eol=lf merge=ours` を追加

---

## 2026-06-25（廃止）

🗑️ [Short report contrarian戦略] 廃止・関連ファイル一括削除（2026-06-25）
- 戦略コンセプト: ショートセラーレポート（Hindenburg等）公開直後の逆張りロング
- バックテストv4まで完了していたが、本番運用には至らず廃止
- 削除ファイル（10件）:
  - `.github/workflows/short_report_monitor.yml`（毎営業日 JST 7:18 定期実行ワークフロー）
  - `src/subport/short_report/news_bot.py`
  - `src/subport/short_report/notify.py`
  - `src/subport/short_report/position_manager.py`
  - `src/subport/short_report/screener.py`
  - `src/subport/short_report/config.json`
  - `src/subport/short_report/requirements.txt`
  - `src/subport/short_report/state.json`
  - `src/subport/short_report/processed_content.json`
  - `src/subport/short_report/README.md`

---

## 2026-06-25（実装）

✅ [DISCOVER-FEATURE-1] ニュース履歴保存・閲覧機能（2026-06-25完了）
- **`src/discover/collect.py`** に3関数を追加
  - `get_price_change(ticker)`: yfinance で直近2営業日の終値比騰落率（%）を取得
  - `add_price_changes_to_yesterday(now_jst)`: 前日分の `news_history_YYYY_MM.json` を読み込み、各銘柄・各itemに `price_change_next_day` を追記して上書き保存
  - `append_to_monthly_history(results, now_jst)`: 当日分の分類結果を `docs/discover/data/news_history_YYYY_MM.json` に追記（同日キーは上書き・冪等）
  - `main()` で `daily_report.json` 書き込み前に上記2関数を呼び出す
- **`docs/discover/news_history.html`** 新規作成
  - 月選択・銘柄フィルター付きニュース履歴閲覧画面
  - 日付降順・銘柄ごとに `price_change_next_day` を色付き表示（↑緑/↓赤/—グレー）
  - importance・category バッジ、URL付きタイトルリンク、summary・source 表示
  - `data-tool="news-history"` で site-theme.css のシアン accent を適用
- **`docs/common/site-nav.js`**: DISCOVER の次に `{ key: 'news-history', label: 'ニュース履歴' }` を追加（全ページのナビに波及）
- **`.gitattributes`**: `docs/discover/data/news_history_*.json text eol=lf merge=ours` を追加
- **`.github/workflows/Discover_Update.yml`**: pip install に `yfinance` 追加、git add に `news_history_*.json` 追加

✅ [ARCH-DATA-1一部] 年度判定の共通関数化（2026-06-25完了）
- `common/sec_data/utils.py` を新規作成し `determine_fiscal_year(end_date, fiscal_end_month)` を定義
- `common/sec_data/parser.py`: `_detect_fiscal_end_month()` メソッドを追加し、`_extract_values()` 内の `end_date[:4]` を `determine_fiscal_year` 呼び出しに統一。INTUガード（exactフラグ）は保持
- `src/value/adjusted_eps_analyzer/extract_key_facts.py`: 4か所のインライン `end.month > fiscal_end_month` 判定を `determine_fiscal_year` に置き換え
- `src/value/adjusted_eps_analyzer/pipeline.py` `aggregate_annual()`: `fiscal_year=None` フォールバック時に警告ログを追加（動作は維持）
- pytest 119件全通過確認済み

---

## 2026-06-24（実装）

✅ [MP-BIZDAY-1] MARKET PULSE 営業日ベース化（2026-06-24完了）
- `Market_Pulse_Update.yml` の cron を `* * *` → `* * 1-5` に変更（月〜金のみ実行）
- 土日はワークフロー自体をスキップ。前日比計算・フロントエンドの変更は不要（yfinanceが営業日のみ返すため前日比はすでに正しい）

✅ [SEC-CTRL-1] 内部統制評価機能 TANUKI TAIL 実装（2026-06-24完了）
- **`src/tail/sec_ctrl_fetcher.py`** 新規作成
  - EDGAR 10-Q「Controls and Procedures」(Part I Item 4) を取得・解析
  - Material Weakness / Significant Deficiency をregexで検出
  - 有効性 (effective: true/false/null) を判定して `docs/portfolio/tail/data/ctrl/{ticker}_ctrl.json` に保存
  - CLI: `python src/tail/sec_ctrl_fetcher.py [TICKER ...]`（無引数で全tail銘柄）
- **`docs/portfolio/tail/index.html`** 更新
  - `TABS_CORE` に `'内部統制'` (n=5) 追加
  - `openModal` に ctrl データのlazy load追加
  - `renderModalBody` で n===5 を `buildTabCtrl` へディスパッチ
  - `buildTabCtrl`: 有効性バッジ（緑/赤）、MW件数・スニペット、SD件数、Item4原文折りたたみ表示
- **`.github/workflows/TANUKI_TAIL_SEC_Ctrl.yml`** 新規作成（週次月曜 10:00 JST 自動実行）
- **SOUN検証**: MW=3種類（統制環境・複雑取引・職務分掌）を正常検出、effective=false確認

✅ [TSCORE-TRAP-1] 投資トラップ検出パネル Phase1+Phase2全件実装（2026-06-24完了）
- `docs/value-monitor/tanuki_score/index.html` に `renderTrapPanel()` を追加（DuPontパネル直後・`<details>` 折りたたみ形式）
- 6種をフロントエンドでリアルタイム計算: バリュー/グロース/バリューデスト/ナラティブ/サイクリカル/ワンタイム
- 🔴高/🟡中/🟢低/– で表示、ホバーで判定根拠ツールチップ、列ソート・0件非表示トグル実装
- Phase2実装（全4件）:
  - #7 アセットヘビー: asset_turnover近似（pipeline変更なし）
  - #4 ディビデンドトラップ: `data_fetcher.py`+`core_calculator.py` に dividend_yield/payout_ratio 追加
  - #2 シガーバット: `quarterly.py`+`parser.py` に CurrentAssets/CurrentLiabilities 追加 → `pipeline.py` で net_current_assets_ratio 計算
  - #10 キャッシュトラップ: `quarterly.py`+`parser.py` に Buyback 追加 → `ttm_calculator.py` FLOW_FIELDSに追加 → `pipeline.py` で buyback_ttm を financial_health に格納
- 最終TRAP_KEYS: バリュー/グロース/バリデスト/ナラティブ/サイクリカル/ワンタイム/シガーバット/配当/キャッシュ/アセット重（10種）

✅ [DAILY-PICK-BUG-1] daily_pick.jsonのtanukiキー欠落修正（2026-06-24完了）
- `main()` 内で `build_data_package()` を明示的に呼び出し、`output` 辞書に `"tanuki": data_pkg["tanuki"]` を追加
- `daily_pick.json` に `tanuki`（`fcf_conversion_rate` 等16フィールド）が正常出力されることを確認

✅ [MP-DISP-1] ゲージ数値ラベル配置不揃い修正（2026-06-24完了）
- **対象**: `docs/market-monitor/market-pulse/index.html`
- 全3ゲージ（メインセンチメント・CNN F&G・Tech Pulse）の FEAR/GREED/50 ラベルを弧の端点・頂点基準で `text-anchor="middle"` に統一
- メインゲージ: FEAR→(x=22,y=124)、GREED→(x=198,y=124)、50→(x=110,y=14) に修正
- ミニゲージ(CNN/Tech): FEAR→(x=18,y=106)、GREED→(x=162,y=106)、50→(x=90,y=12) に修正
- 左右が弧端点を中心とした鏡対称、「50」が弧頂点の外側に統一配置

✅ [EPS-DISP-5] 「調整内訳（全期間）」ページ長大化対策（2026-06-24完了）
- **対象**: `docs/value-monitor/adjusted_eps_analyzer/stock.html`
- **方式A採用**: 直近8四半期のみ表示 + 「全N件を表示 ▼」展開ボタン
- `buildAdjHtml()` を分離してHTML生成を共通化、`updateAllAdjustments()` で8件超の場合にボタンを追加
- `expandAllAdj()` でボタンクリック時に全件展開

✅ [EPS-DISP-4] グラフ軸ラベル・フォントサイズ統一（2026-06-24完了）
- **対象**: `docs/value-monitor/adjusted_eps_analyzer/stock.html`
- メインEPS推移チャート `scales.x/y ticks.font.size`: 10 → 11
- ウォーターフォールチャート `scales.x/y ticks.font.size`: 9 → 11
- 参照: market-pulse は12で統一。EPS は表示密度を考慮し11に統一

✅ [TSCORE-DISP-4] バックテストのデフォルト展開（2026-06-24完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- `#sv-body` の `display:none` を除去、矢印テキストを「▶ 展開して見る」→「▲ 折りたたむ」に変更
- データなし時は「データなし（pipeline.py 実行後に表示）」が自動表示されるため展開状態でも問題なし

✅ [EPS-DISP-3] 「投資機会ランキング」デフォルト展開（2026-06-24完了）
- **対象**: `docs/value-monitor/adjusted_eps_analyzer/index.html`
- `#opp-body` の `display:none` を除去、矢印テキストを「▲ 折りたたむ」に変更

✅ [EPS-DISP-2] BX会社名空欄補完（2026-06-24完了）
- **原因**: `config/cik_lookup.csv` に BX エントリが存在せず → `ticker_to_name["BX"]` が未定義 → pipeline が SEC metadata 名にもフォールバックできず空文字で保存
- `config/cik_lookup.csv` に BX 行を追記（CIK: 0001393818、name: Blackstone Inc.、eps: true）
- `docs/value-monitor/adjusted_eps_analyzer/data/summary.json` の BX エントリを即時パッチ（`company_name: "Blackstone Inc."`）

✅ [TSCORE-BT-1] バックテスト直近件数ラベル修正（2026-06-24完了）
- **実態**: 全銘柄の `score_history.json` を横断し、`date` 降順で最大20件を表示（`allEntries` 全銘柄横断・`slice(0,20)`）
- `recentRows` の前に `recentArr`（配列）を分離し、ラベルを `直近20件` → `直近${recentArr.length}件（全銘柄横断・判定日降順）` に修正
- **対象**: `docs/value-monitor/tanuki_score/index.html`

✅ [TSCORE-FIX-5] RICEマトリクス有効銘柄数の動的取得（2026-06-24確認・対応不要）
- 調査結果: `docs/value-monitor/tanuki_score/index.html` line 1119 で既に `${allPoints.length}銘柄` として動的実装済み
- コード変更なし

✅ [HOME-FIX-3] HYPECOREカード銘柄数の動的化（2026-06-24完了）
- `docs/value-monitor/hypecore/data/tickers.json` を新規作成（hypecore `ALL_TICKERS` と同一の60銘柄配列）
- `docs/index.html`: カード説明文・ステータスバッジの銘柄数を `<span id>` に変更し、fetch 後に書き換え
- 取得失敗時はステータスを空文字にフォールバック（`LIVE ·` のみ残る）

✅ [SOFI-DATA-1] SOFI LTDebt 正規化データ更新（2026-06-24完了）
- **対象**: `common/sec_data/normalized/SOFI_quarterly_normalized.json`・`docs/common/sec_data/normalized/SOFI_quarterly_normalized.json`
- **調査結果**: SOFI は銀行免許取得後（2022年以降）、`LongTermDebt` XBRL タグを報告しなくなった。代替タグ `DebtLongtermAndShorttermCombinedAmount`（短期+長期の合計社債）が SEC EDGAR に存在。
- **対応方針: B（カスタム概念使用）**:
  - `DebtLongtermAndShorttermCombinedAmount` は SOFI の senior notes（社債）を代表する最適タグ
  - 2023〜2026のデータを同概念から直接 normalized JSON に手動追記（`quarterly.py` フェッチスクリプトはフォールバック未対応のため手動パッチ）
- **追記したエントリ（13件）**:
  - 2023-03-31: $6.126B / 2023-06-30: $6.484B / 2023-09-30: $6.241B / 2023-12-31: $5.233B（倉庫ローン残存期）
  - 2024-03-31: $2.891B / 2024-06-30: $3.107B / 2024-09-30: $3.180B / 2024-12-31: $3.093B
  - 2025-03-31: $3.046B / 2025-06-30: $3.943B / 2025-09-30: $2.714B / 2025-12-31: $1.815B / 2026-03-31: $1.813B
- **注意**: 2023年前半は倉庫ファシリティ残存により $6B超（旧 `LongTermDebt` の2022値と同等）。2024-Q1以降は senior notes のみとなり ~$1.8〜3.2B に収束。

✅ [MP-LOGIC-2] BUY チェックリスト実装（2026-06-24完了）
- **対象**: `src/market/market_pulse/collect_and_send.py`・`docs/common/glossary.json`・`docs/market-monitor/market-pulse/index.html`
- `collect_and_send.py`:
  - `calc_buy_checklist()` 追加: F&G ≤ 25 で `triggered=True`、F&G ≤ 10 で `extreme=True`。3チェック×1pt（S&P500 200日MAシグナル・HYスプレッド縮小・ヒンデンブルグ非活性）。0〜1pt→WATCH / 2pt以上→BUY
  - `fetch_hy_spread_from_fred()` 拡張: `max_90d`（90日最高値）・`is_contracting`（`current < max_90d - 0.30`）を追加。`window = hy.iloc[-90:]` から `min()` / `max()` を同一ウィンドウで計算
  - `save_data_to_json_and_csv()` に `buy_checklist=None` 引数を追加し `new_entry` に `buy_checklist` キーとして保存
- `docs/common/glossary.json`: `buy_ma200`・`buy_hy_spread`・`buy_hindenburg` 追加
- `docs/market-monitor/market-pulse/index.html`:
  - `renderBuyChecklist()` 追加（TAKE PROFITカード直後・アセットフロー直前）
  - F&G > 25: グレーアウトテキスト表示
  - F&G ≤ 25 かつ `triggered=true` 時: action別カラーバナー（WATCH=アンバー/BUY=緑）＋3チェック項目（✅該当/❌非該当バッジ・pt・詳細行・glossaryツールチップ）＋買いポイント合計表示
  - F&G ≤ 10（`extreme=true`）時: セクションヘッダーを `pulse-red` アニメーション強調＋「🚨 Extreme Fear — 絶好の買い場の可能性」バナーを追加表示
  - `RENDER_ALL_FNS` に `renderBuyChecklist` を登録

✅ [MP-LOGIC-1] TAKE PROFIT チェックリスト実装（2026-06-24完了）
- **対象**: `src/market/market_pulse/collect_and_send.py`・`docs/common/glossary.json`・`docs/market-monitor/market-pulse/index.html`
- `collect_and_send.py`:
  - `_get_sp500_ma_deviation()`: `period="3mo"` → `"1y"` に変更。200日MA計算を追加し戻り値をdict化（`deviation_50`/`above_ma200`/`ma200_slope`）。傾き判定は MA200[today] vs MA200[10日前]（`close[-200:].mean()` vs `close[-210:-10].mean()`）。`compute_sentiment()` の呼び出し箇所を `deviation_50` を参照する形に更新
  - `fetch_hy_spread_from_fred()` 追加: FRED `BAMLH0A0HYM2`（ICE BofA US High Yield Index OAS）を120日分取得。`is_expanding = current > min_90d + 0.30`（30bps閾値）
  - ヒンデンブルグ簡易判定: `breadth_data.json` の `new_highs_52w` / `new_lows_52w` が各々 `500 × 2.2%`（11件）以上で `hindenburg_active = True`
  - `calc_take_profit_checklist()` 追加: F&G ≥ 75 で `triggered=True`。3チェック×1pt（S&P500 200日MAシグナル・HYスプレッド拡大・ヒンデンブルグ）。0〜1pt→HOLD / 2pt→PARTIAL / 3pt→TAKE PROFIT
  - `save_data_to_json_and_csv()` に `take_profit_checklist=None` 引数を追加し `new_entry` に `take_profit_checklist` キーとして保存
- `docs/common/glossary.json`: `tp_ma200`・`tp_hy_spread`・`tp_hindenburg` 追加
- `docs/market-monitor/market-pulse/index.html`:
  - `renderTakeProfit()` 追加（Tech Pulse〜アセットフロー間の `.sec` + `.unified-card` として配置）
  - F&G < 75 または `triggered=false` 時: グレーアウトテキスト表示
  - F&G ≥ 75 かつ `triggered=true` 時: action別カラーバナー（HOLD=緑/PARTIAL=アンバー/TAKE PROFIT=赤）＋3チェック項目（✅/❌バッジ・pt・detail行・glossaryツールチップ）＋利確ポイント合計表示
  - `escHtml()` ユーティリティを追加、`RENDER_ALL_FNS` に `renderTakeProfit` を登録

✅ [DISCOVER-FEATURE-3] テーマ内銘柄の役割分類表示（2026-06-24完了）
- **対象**: `src/discover/collect.py`・`docs/discover/index.html`
- `src/discover/collect.py`: `related_tickers` を文字列配列→オブジェクト配列に変更（`ticker`/`role`/`note` フィールド）。role定義（主要・ボトルネック・注目）と各役割の説明をプロンプトに明示
- `docs/discover/index.html`: `buildRelatedTickers()` ヘルパーを追加
  - 旧形式（文字列配列）→ `typeof rt[0] === 'string'` 判定で従来のシアンバッジ表示（後方互換）
  - 新形式（オブジェクト配列）→ role順（主要→ボトルネック→注目）にグループ化し色別バッジ表示（主要:シアン・ボトルネック:アンバー・注目:グリーン）。`note` がある場合は `data-info-text` 属性で `info-tooltip.js` にⓘツールチップを自動付与
- 次の日曜（Grok再生成）まで旧表示が維持される（後方互換性により問題なし）

✅ [DISCOVER-FEATURE-2] テーマ選定根拠・証跡の明示（2026-06-24完了）
- **対象**: `src/discover/collect.py`・`.github/workflows/Discover_Update.yml`・`docs/common/glossary.json`・`docs/discover/index.html`
- `src/discover/collect.py`: プロンプトに `sources` フィールド（1〜3件）を追加。日曜実行時に `docs/discover/data/macro_themes_history.json` へ週次追記（最大26件・新しい順）
- `.github/workflows/Discover_Update.yml`: `macro_themes_history.json` を git add 対象に追加（ファイル未存在時はスキップ）
- `docs/common/glossary.json`: `discover_conviction` キー追加（高/中/低の判定基準）
- `docs/discover/index.html`: 確信度バッジにツールチップ追加（`data-info="discover_conviction"`）・`sources` をリンク付きリストとしてカード末尾に表示・streak ≥ 1 の場合に「🔥 N週連続」バッジをテーマ名横に表示・「過去のテーマを見る（N週分）」折りたたみセクションを追加（直近4週分）

✅ [DISCOVER-LAYOUT-1] 一覧性の向上（DISCOVER画面）（2026-06-24 完了）
- **対象**: `docs/discover/index.html`
- `.ticker-cards` を `display:flex;flex-direction:column` → `display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr))` に変更し2カラム以上のグリッド表示を実現
- `buildTickerCard()` に `data-collapsed=""` + `onclick="toggleCard()"` + `▶` トグルアイコン + リンクへの `event.stopPropagation()` + `ticker-card-body` に `style="display:none"` を追加し、デフォルト折りたたみに変更
- 既存の `toggleCard()` 関数（`data-collapsed`属性トグル）をそのまま流用

✅ [MP-FEATURE-1] AIコメントの過去履歴保持・表示機能（Market Pulse画面）（2026-06-24 完了）
- **対象**: `src/market/market_pulse/collect_and_send.py`・`docs/market-monitor/market-pulse/index.html`
- **データ側**: `save_data_to_json_and_csv()` に `comments_history` 配列を追加。同日エントリ重複除去後の `all_data` から直近11件の `{date, summary}` を逆順収集し、当日分と合わせて最大12件を `new_entry.comments_history` として保存
- **表示側**: `renderDetail()` の末尾に `buildCommentsHistory(d)` を追加。`comments_history[1:]`（過去分）が1件以上ある場合、「▶ 過去の分析を見る（N件）」トグルボタンと折りたたみパネルを生成。`toggleCmtHist()` で開閉制御

✅ [TSCORE-DUPONT-1] DuPontパネルのソート機能追加（2026-06-24完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- 全6列（銘柄・ROE(DuPont)・純利益率・資産回転率・財務レバレッジ・ROE(実績)）にヘッダークリックソートを追加
- 昇順→降順→昇順トグル、ソート列に矢印インジケーター（▼▲）とアクセントカラーを表示
- 既存の全銘柄詳細テーブルのソートロジック（`_sortCol`/`_sortDir`・`thArr`等）を流用
- 初期状態はROE(DuPont)降順（従来の固定ソートと同一）

✅ [TSCORE-DUPONT-3] ROE(DuPont)と実績ROEの乖離警告（2026-06-24完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- 閾値: |DuPont ROE − 実績ROE| ≥ 10%pt
- 表示: アンバー背景（rgba(245,158,11,.06)）+ ROE(実績)セルに⚠バッジ
- ツールチップ: 乖離幅・両値・要因説明（info-tooltip.js流用）
- 既存の黄色⚠（信頼性・極端値）と色違いで共存
- 現データで50銘柄/86銘柄が警告対象

✅ [SILO-LAYOUT-2] 「総合スコア判定根拠」配置・コンパクト化（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html`
- 旧位置: detail-bottom後ろ（画面最下部）→ 新位置: pillar-row直下・valuation bar上
- `<details>`タグでデフォルト折りたたみ（▶ 総合スコア 判定根拠）

✅ [SILO-LAYOUT-3] 各詳細セクションを評点カード下にネスト配置（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html`
- 変更後構造: pillar-row内の各カード（①②③）直下に対応する詳細を折りたたみで配置
- 総合スコア判定根拠はpillar-row直下に配置（SILO-LAYOUT-2と統合）

✅ [SILO-LAYOUT-1] 「黒字化への道のり」チャートの凡例・説明追加（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html` — `buildProfitPath()` return
- タイトル行に `?` ツールチップ（0ライン=黒字化基準、単位説明）を追加
- 凡例3項目（緑=黒字達成済み / 紫=次の黒字化目標（ETA自動算出）/ グレー=ペンディング）をドット付きで追加

✅ [SILO-LAYOUT-4] 時価総額等のサマリー情報をティッカー名近くに集約（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html` — `buildDetail()` return
- `valInlineHtml` 変数を追加し `conclusion-left` 内（conclusion-summary直下）にコンパクト表示
- 表示形式: `MC $1.23B　$45.67　PSR 12x　EV/S 10x　NC $0.50B`
- standalone val-bar IIFE（旧1行）を削除

✅ [SILO-LAYOUT-5] 棒グラフと財務トレンドセクションの隣接配置（2026-06-24完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html` — CSS
- `.chart-row{margin-bottom:16px}` → `margin-bottom:0`
- `.fv-section{margin-top:14px;border:1px solid var(--bdr)}` → `margin-top:0;border-top:none` でシームレスに結合

✅ [PORT-FEATURE-1] 主要金額表示への円貨表示切り替え追加（2026-06-24完了）
- **対象**: `docs/portfolio/index.html`
- `_usdJpy`（history.jsonのlatestスナップから取得）・`_currMode2`・`fmtC()`・`switchCurr()` を追加
- `loadData()` に history.json の並行フェッチを追加（usdjpy抽出 + `loadHistoryChart()`の二重フェッチ排除）
- 適用箇所: 総資産・時価残高合計・評価損益・キャッシュ/ブローカー別サマリー（全金額）/テーブル全金額列
- サマリー左上に USD/JPY 切り替えボタン追加
- `switchChart()` を scoped に修正（currency ボタンと競合しないよう）

✅ [TAIL-LAYOUT-1] DECISION LOGの別ページ分離（2026-06-24完了）
- **新規ファイル**: `docs/portfolio/tail/decision_log.html`
- 元ページの journal section を「DECISION LOG を見る →」リンク + 最終ログサマリーに置き換え
- 新ページ: 同auth・フィルターUI・全ログ表示（全件数バッジ付き）
- site-nav.js への追加なし（サブページのため）

✅ [TAIL-UX-1] TANUKI TAIL使い方ガイダンス充実（2026-06-24完了）
- **対象**: `docs/portfolio/tail/index.html`・`docs/common/glossary.json`
- ページ冒頭に利用フロー（①登録→②Grokレビュー→③ログ記録）バナーを追加
- 「前回レビューからN日」を journal.json 最新エントリーから算出（30日以内=緑/90日以内=amber/超過=赤）
- OVERVIEW CORE/SAT・NEW POSITION セクションに `data-info` ツールチップ追加
- glossary.json に `tail_overview`/`tail_overview_sat`/`tail_new_position`/`tail_decision_log` を追加

---

## 2026-06-24（調査）

✅ [DCF-RELIABILITY-1] FCF_Conversion_Rate表示欠け調査（2026-06-24完了・対応不要）
- **調査結果**: rate=null の銘柄はゼロ。非表示19件はすべて設計上の正常動作
  - 赤字（adj_net_income≤0）: 12件（ASTS, CRWV, IONQ, JOBY, ONDS, QBTS, RBRK, RCAT, RKLB, RXRX, S, SOUN）
  - FCF外れ値除外（二重補正防止）: 5件（AMZN, BBAI, COHR, KULR, RDW）
  - EPSデータ欠落: 2件（BKNG, FCX）
- 「74銘柄表示欠け」は過去のClaude Code調査時点の記録であり現状と乖離していた
- 別途 [DAILY-PICK-BUG-1] を新規登録（daily_pick.jsonのtanukiキー欠落）

---

## 2026-06-24（Task Group 2）

✅ [TSCORE-FIX-2] TANUKIスコアテーブルの行間・フォント改善（2026-06-24 完了）
- **対象**: `docs/value-monitor/tanuki_score/index.html`
- **対応**: `.dtbl th` の padding を 9px/12px→10px/14px、font-size を 10px→11px に拡大。`.dtbl td` の padding を 8px/12px→10px/14px に拡大（HypeCore detail.html の基準に統一）

✅ [TVAL-FORMULA-1] TANUKI VALUATION 算式と実装の整合性監査・修正（2026-06-24 完了）
- **対象**: `docs/value-monitor/tanuki_valuation/index.html`（formula-preview・method-card・TABLE LEGEND）
- **監査結果**（7式）:
  - RICE: **不一致→修正** VC_Factorが表示から欠落。`(G×Q×CF)/WACC`→`(G×VC_Factor×Q×CF)/WACC`（3箇所修正）
  - Q: **不一致→修正** SBC補正が表示から欠落。`OCF÷純利益`→`OCF÷(純利益+SBC)`（1箇所修正）
  - IV(P_t): **不一致→修正** `GO_PV×(1+α)÷株式数`と表示していたが実装は`GO_PV÷株式数`（αはGO_PVに乗らない）
  - α, WACC, 乖離率, CF: **一致**（修正なし）
- **根拠**: `adjustments.py` L598: `intrinsic_value_pt = v0*(1+alpha) + rpo_pv + growth_option_pv`
- **注記**: CLAUDE_CODE_START.md記載の「RICEのVC_Factor欠落は既知」の解消も含む

✅ [EPS-LAYOUT-1] 個別明細画面にティッカー＋会社名表示（2026-06-24 完了）
- **対象**: 3画面 + 共通データファイル新規生成
  - `docs/common/company_names.json`（新規）: `config/cik_lookup.csv`から96銘柄の`{ticker: name}`マッピングを生成
  - `docs/value-monitor/adjusted_eps_analyzer/stock.html`: `ticker-title`を`TICKER — Company Name`形式に
  - `docs/value-monitor/tanuki_valuation/stock.html`: `.ticker-symbol`に会社名を付加
  - `docs/value-monitor/hypecore/detail.html`: `page-title-sub`に選択銘柄の会社名を表示
- **実装方式**: ページ初期化時に`company_names.json`をfetchし、会社名が存在する場合のみ付加（フォールバックはティッカーのみ）

---

## 2026-06-24

✅ [HYPE-BUG-2] 開閉アイコンの向きが逆さま修正（2026-06-24 完了）
- **対象**: `docs/value-monitor/hypecore/detail.html`
- **原因**: `.narrative-toggle-arrow.open { transform: rotate(180deg) }` とJS側テキスト切り替え（▼→▲）が二重適用。展開時に▲が180°回転して▼に見えるバグ
- **対応**: CSS の `rotate(180deg)` を削除。テキスト切り替えのみで方向制御

✅ [MP-GAUGE-NEEDLE-1] ゲージの数値ラベル「0」「100」除去（2026-06-24 完了）
- **対象**: `docs/market-monitor/market-pulse/index.html`（センチメント・CNN F&G・Tech Pulse の3ゲージ）
- **原因**: 右端の「100」テキストラベルと「GREED」ラベルが同位置で重なっていた
- **対応**: 3ゲージすべてから `<text>` の「0」「100」を除去。FEAR/GREEDラベルが両端を示すため不要、「50」中央ラベルのみ残置

✅ [HOME-FIX-4] FEATURESセクションの`//`は意図的装飾と確認（2026-06-24 完了）
- **調査結果**: `<div class="feat-icon">//</div>` はリテラルテキスト。フォントアイコン未ロードではなく、コードコメント風の意図的デザイン装飾（Space Monoフォント×アクセントカラー）
- **対応**: コード変更なし

---

## 2026-06-23

✅ [TAIL-DISP-2] CORE一覧「乖離率」列が全銘柄`–`表示の修正（2026-06-23 完了）
- **対象**: `docs/portfolio/tail/index.html`・`docs/common/glossary.json`
- **原因（2段階）**:
  1. `renderCoreTable()`の乖離率セルが`'<td class="num" style="color:var(--mut)">—</td>'`と
     ハードコードされており、そもそもどのデータフィールドも参照していなかった（未実装）
  2. 仮にデータ参照に書き換えても、`loadValuations()`（TANUKI VALUATIONのlatest.jsonを
     fetchして`latestValCache`に格納する関数）が`p.type === 'satellite'`銘柄のみを
     対象にしており、CORE銘柄のTANUKI VALUATIONデータが一度も取得されていなかった
     （SATELLITE一覧の「現在価格」列は同じキャッシュを参照しており正常表示されていたため
     見落とされやすい構造だった）
- **対応**:
  - `loadValuations()`への対象ティッカー収集を`type==='satellite'`限定から
    `status!=='archived'`（CORE含む全銘柄）に拡大
  - `renderCoreTable()`で`latestValCache[p.ticker].upside_percent`
    （TANUKI VALUATIONの理論株価IVと現在株価の乖離率、既存フィールドを流用・新規計算ロジックなし）
    を参照し、プラス=緑/マイナス=赤で表示する分岐を追加（SATELLITE一覧のP/L%表示と同じ配色規約）
  - `data-info="tail_deviation_rate"`をth要素に付与し、`glossary.json`に新規キーを追加
    （CLAUDE_CODE_START.md記載の「ユーザー向け数値を追加した場合はglossary.json登録」ルールに準拠）
- **検証**: Playwrightで実データ確認（パスワードゲートはsessionStorageバイパス）。
  CORE銘柄（PLTR/SOFI/TSLA）で乖離率が実数値（-49.4%/-7.9%/-87.3%）かつ正しい色で表示、
  ツールチップ文言も正しく表示されることを確認。SATELLITE一覧側への影響がないことも確認。
  pytest 119件全件パス、check_links.py リンク切れ0件

✅ [PORT-DISP-2/PORT-LAYOUT-1/PORT-LAYOUT-2] ポートフォリオ画面の表示修正3件（2026-06-23 完了）
- **対象**: `docs/portfolio/index.html`
- **PORT-DISP-2（セクション番号②から始まる）**: `#summary-section`の資産サマリー
  （総資産・時価残高合計・評価損益・キャッシュ比率の4カード）に`<div class="sec">`見出しが
  一切存在しなかったことが原因。`① 資産サマリー`見出しを追加し②③④と連続させた
- **PORT-LAYOUT-1（「その他」が2番目に表示）**: `brokerSummaries`の並び順は
  `portfolio.json`の`brokers`オブジェクトのキー順（`Moomoo→その他→Moomoo(N)→MONEX→RAKUTEN`）
  そのままで、ソート処理が一切なかったことが原因。カード描画前に
  `bAssets===0`（残高$0）を末尾へ送る安定ソートを追加（他の並び順は維持）
- **PORT-LAYOUT-2（RAKUTENカードのみ横長）**: `.broker-summary{display:flex;flex-wrap:wrap}`+
  `.broker-card{flex:1}`構成で、5枚中4枚が1行目を埋め5枚目（RAKUTEN、配列末尾）が
  2行目に単独で残り、`flex:1`によりその行の全幅まで伸長していたことが原因
  （flexの`flex-basis:0%`は同一行内の兄弟数に応じて幅を再分配するため、単独行では
  100%まで広がる）。`display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr))`に
  変更し、行をまたいでも列トラック幅が固定されるようにした（`auto-fit`ではなく`auto-fill`を
  採用: ブローカー数が少ない場合にカードが不必要に間延びするのを防ぐため）
- **検証**: Playwrightで実データを使い確認（パスワードゲートは`sessionStorage`に
  認証フラグを注入してバイパス）。① 資産サマリー〜⑤ 資産推移までセクション番号が連続、
  5枚のブローカーカードが全て等幅（約183px）になったこと、「その他（$0.00）」が
  5枚目（最後）に移動したことを確認。600px/960px幅でも崩れずグリッドが機能することを
  スクリーンショットで確認。pytest 119件全件パス、check_links.py リンク切れ0件

✅ [PORT-DISP-1] 最終更新日が古いまま（PORTFOLIO画面）の調査完了・仕様通りと判明（2026-06-23 完了）
- **対象**: `docs/portfolio/index.html`（`#last-updated`、`pf.last_updated`表示）・
  `docs/portfolio/data/portfolio.json`
- **調査結果**: `portfolio.json`の`last_updated`は実データも2026-06-03のまま停止しており
  表示側のバグではないことを確認。`src/portfolio/snapshot.py`を含む全Pythonスクリプト・
  全GitHub Actionsワークフローを検索したが、`portfolio.json`を書き込む自動化パイプラインは
  存在しないと判明
- **真の更新経路**: `docs/value-monitor/admin.html`の`savePortfolio()`関数（3500-3530行目）が
  管理画面の「💾 ポートフォリオを保存」ボタン経由で`last_updated`をセットしGitHub API経由で
  直接コミットする、**人間による手動更新が唯一の設計上の経路**。git履歴上の過去コミット
  （`feat(portfolio): ポートフォリオ更新`、コミット者は人間でgithub-actions[bot]ではない）が
  admin.htmlの生成パターンと完全一致することで裏付け
- **結論**: 2026-06-03以降ユーザーが管理画面から保存操作を行っていないことが原因であり、
  コード上の不具合ではないため**修正なし**。自動更新が必要な場合は新機能として別途
  BACKLOG起票が必要（証券会社API連携等、既存の【Moomoo API】系BACKLOGと関連）

✅ [TAIL-SAT-CI-1] Satellite Monitor CIのgit pull --rebase失敗修正（2026-06-23 完了）
- **対象**: `.github/workflows/TANUKI_TAIL_Satellite_Monitor.yml`（「Commit updated
  alert history」ステップ）
- **原因特定**: `src/tail/satellite_monitor.py`が`satellite_alerts.json`
  （`_save_alerts`）と`journal.json`（`_save_journal`、`_append_journal_watchlist`
  経由でアラート発生時に毎回書き込み）の2ファイルを更新するが、ワークフローの
  `git add`は`satellite_alerts.json`のみをステージしていた。いずれかのsatellite
  銘柄でアラート条件（エントリー/エグジット/ニュース/決算接近）が1件でも発火すると
  journal.jsonも更新され、`git commit`後に未ステージ変更が残ることで後続の
  `git pull --rebase`が「cannot pull with rebase: You have unstaged changes」で
  失敗していた。journal.json・satellite_alerts.json両方の最終更新日が2026-06-07で
  一致しており、この日以降ローカルコミットは成立するもpushまで到達していなかった
  ことと整合（コミットはランナーの使い捨てクローン内で完結し破棄されるため、
  リモートのデータは更新されないまま停滞していた）
- **比較**: 正常動作している`TANUKI_TAIL_RSS_Monitor.yml`は、スクリプトが更新する
  全ファイルを`git add`に明示列挙する既存パターンを採用しており、これに倣った
- **対応（案B採用）**: `git add`に`docs/portfolio/tail/data/journal.json`を追加。
  スクリプト内の書き込み対象（`json.dump`呼び出し）を全件grepで洗い出し、
  この2ファイル以外に書き込みがないことを確認済み
- **検証**: このセッションには`gh` CLI等のGitHub Actions認証手段がなく
  workflow_dispatchを直接トリガーできなかったため、修正pushの上でユーザーに
  GitHub Web UIからの手動トリガー、または次回定期実行（平日JST 08:00/17:00）での
  自然検証を依頼

✅ [MACRO-DISP-2] Michigan Sent.*指標名の850px/1200px幅省略修正（2026-06-23 完了）
- **対象**: `docs/market-monitor/macro-pulse/index.html`（`.phase-signals`/`.pg-sig`、
  EPIC-LAYOUT-1グループB対応の残課題）
- **実測調査**: Playwrightで700/800/850/960/1024/1200/1400pxの`.v3-main`実幅・
  `.phase-signals`の列数・列幅を計測。850px/1200pxはともに`.v3-main`が約800〜810px
  まで縮み、`repeat(auto-fit,minmax(260px,1fr))`で3列になった結果、列幅が266〜269px
  まで圧縮されることを確認（「Michigan Sent.*」の必要幅83pxに対し名前スパンの
  `clientWidth`が77〜80pxしかなく数px不足→省略）。850px（`.v3-dash`が単一カラムに
  切替わる1000px境界の直下）と1200px（2カラムでサイドバー340px+gap18pxを差し引いた
  幅）がたまたま同程度の`.v3-main`幅に収束する非線形性が原因で、`minmax`調整だけでは
  別の幅で再発する「モグラ叩き」と判明（対応方針候補1/3はこの非線形性に追従し続ける
  ため不採用、候補2を選択）
- **対応**: `.pg-sig`を1行レイアウトから2行レイアウトに変更（候補2）。
  Row1=dot+name、Row2=val+badge+leadに分離し、`.pg-sig-name`がval/badge/leadと
  横幅を奪い合わなくなるようにした。`minmax(260px,1fr)`は変更不要（2行化だけで
  必要最小幅が大幅に下がり、260px floorに対して十分な余白が生まれた）
- **検証**: Playwrightで700/800/850/960/1024/1200/1400pxの全7幅で
  「Michigan Sent.*」を含む全8指標名の省略が0件であることを確認
  （`scrollWidth>clientWidth`チェック）。スクリーンショットで視覚的にも確認。
  ツールチップのホバー表示が引き続き機能することも確認（DOM構造変更後も
  `.pg-sig{position:relative}`は維持）。pytest 119件全件パス、check_links.py
  リンク切れ0件

✅ [MP-GAUGE-NEEDLE-1] センチメントゲージの針とラベルの重なり修正（2026-06-23 完了）
- **対象**: `docs/market-monitor/market-pulse/index.html`（CNN Fear&Greed・Tech Pulse
  両ゲージ、`#fgGaugeSvg`/`#tpGaugeSvg`共通の`.tp-gauge-center`クラス）
- **構造調査**: 針（`<line>`要素、`#fgNeedle`/`#tpNeedle`）の回転軸は`(90,94)`固定で
  `rotate(${score/100*180-90},90,94)`によりscore=0で-90°（左/FEAR方向）・score=50で
  0°（真上）・score=100で+90°（右/GREED方向）に回転する。半径66の単一線分。
  一方スコア数値・ラベル（`.tp-gauge-center`、HTML divをSVG上に絶対配置）は
  `bottom:2px`で下端y=104に固定され、上端は内容次第でy=54付近まで達する。
  **針の回転軸(90,94)自体がラベル領域(y=54〜104)の内側にある**ため、針をどれだけ
  短縮してもラベル中央(x≈90)を回転軸付近で必ず通過することが判明（案A＝針短縮は
  幾何学的に不採用、選択基準通り案Bへ）
- **Playwright実測**: stroke-width考慮のbbox当たり判定で、score=0/25/50/75/100の
  全パターンで針とラベルが重なることを確認（score=0/100でも回転軸近傍でラベル下端と
  軽微に重なる）
- **対応**: `.tp-gauge-center`に`background:var(--sur)`（カード背景色と同色の不透明
  背景）・`padding:2px 8px`・`border-radius:6px`を追加（案B）。DOM順序上もともと
  `.tp-gauge-center`は`<svg>`より後に配置されており、CSSデフォルトの重なり順で
  針より上に描画されるため、背景を不透明にするだけで針が完全にマスクされる
  （z-index等の追加調整は不要だった）
- **検証**: Playwrightで0/25/50/75/100の5スコア × CNN Fear&Greed/Tech Pulse
  両ゲージ × 600/960/1400px幅の全組み合わせで、針がラベル背景の外側でのみ視認でき
  文字との重なりがないことをスクリーンショットで確認。pytest 119件全件パス
  （CSS変更のみのためロジック影響なし）、check_links.py リンク切れ0件

✅ [DCF-RELIABILITY-1] FCF_Conversion_Rate方式銘柄へのDCF_Reliability判定拡張（2026-06-23 完了）
- **実装箇所**: `src/value/tanuki_valuation/pipeline.py`
  - `_calc_dcf_reliability_policy_b()`（静的メソッド新設）に判定ロジックを集約し、
    スコアリング（`_compute_tanuki_score`）とreport.txt生成の両方から共通利用
  - 判定表（仕様通り、eps_invalid優先で曖昧さを解消）:
    `eps_invalid=true → LOW`（detected/transient_foundに関わらず最優先）、
    `eps_invalid=false, detected=true, transient_found=false → LOW`、
    `eps_invalid=false, detected=true, transient_found=true → NORMAL`、
    `eps_invalid=false, detected=false → NORMAL`
  - `eps_invalid`はEPSアナライザー自体にreliabilityフラグが存在しないため、
    `FCFEstimationResult.divergence_warning`（推定FCFが生FCFの2倍以上乖離）を
    代理指標として採用（設計判断・コード内コメントに明記）
  - report.txt: FCF_Conversion_Rate方式の`else`分岐に`DCF_Reliability: LOW/NORMAL`を
    常時出力するよう追加（Policy Aと同形式の`[Policy B: ...]`注記付き）
  - TANUKI SCORE: `fcf_estimation.applied=True`（Policy B対象）かつPolicy B=LOW時に
    BUY/TRIM/HOLD/WATCHをWATCHへ丸め（SELL/PASSは維持）。Policy A
    （`fcf_floor_applied>0`）とは適用条件が排他的なため同時発火しない
- **report_consistency_check.py**: CHECK-2（DCF_Reliability欠落検出）を拡張し、
  `FCF_Conversion_Rate:`行ありでDCF_Reliability行なしのケースも検出するよう
  `has_fcf_conversion_rate`判定を追加（既存のCHECK-3 LOW丸め未発動は
  正規表現が両Policy共通のため無改修で適用される）
- **テスト**: `tests/test_pipeline_logic.py`に`TestDcfReliabilityPolicyB`を新設
  （9件: 判定表4パターン・eps_invalid優先順位の境界値・スコア丸め3パターン・
  Policy A/B排他性）。pytest 110→119件、全件パス
- **検証**: ADBE/NVDA/SITM/SPIR（LOW想定）、AAPL（detected=false→NORMAL）、
  ADSK（transient_found=true→NORMAL）で実データ確認。ASTS/AMZN（Policy A
  LOW/HIGH）を再生成し既存挙動が変化しないことを確認。全95銘柄を
  `--skip-risk`で再生成（成功94/失敗0）、`report_consistency_check.py` NG=0
  （WARN=1件、ELFのPS異常値はDCF-RELIABILITY-1と無関係の既存事項）

✅ [TVAL-TS-FIX-1] タイムスタンプ表示の未整形・フォーマット不具合修正（2026-06-23 完了）
- **TVAL-TS-1**: `docs/value-monitor/tanuki_valuation/stock.html`の`.version-tag`
  （950行目）とfooter「計算日:」（2037行目）が`calculation_date`
  （フルISOタイムスタンプ）を未整形のまま表示していたのを、既存の`toJST()`関数
  （2588行目、`2026/06/20 17:36 JST`形式に変換）を適用して解決
- **TVAL-TS-2**: `docs/value-monitor/tanuki_valuation/index.html`の`fmtDate()`
  （388行目）`(d)=>d.slice(5).replace('-','/')`が、フルISO文字列に対して
  `slice(5)`すると`"06/20T17:36:48+09:00"`という壊れた文字列になる実装バグを修正。
  `d.slice(0,10).slice(5).replace('-','/')`に変更し、まず日付部分のみ
  （YYYY-MM-DD）を確定してから整形するようにした
- **検証**: Playwrightで実機確認。stock.htmlのversion-tag/footerが
  `2026/06/23 03:21 JST`形式で表示されること、index.htmlの更新日列が
  フルISO（`2026-06-23T03:22:43+09:00`）でも日付のみ（`2026-06-20`）でも
  `06/23`/`06/20`形式に正しく整形されること（壊れた文字列が出ないこと）を確認。
  `fmtDate(null)`/`fmtDate('')`が`'—'`を返すことも確認。pytest 110件全件パス・
  check_links.py リンク切れ0件

✅ [EPIC-LAYOUT-1 グループC] SILO-DISP-3: Stonks Siloテーブルのバッジ省略修正（2026-06-23 完了）
- **対象**: `docs/value-monitor/stonks-silo/index.html`
- **問題①（主因）**: TICKER列にTANUKI SCOREバッジ（BUY/WATCH/PASS等）が非同期注入
  されるが、列幅（72px）がティッカー文字のみを想定したサイズでバッジ分の余白が
  確保されておらず、1400px幅でもWATCH/PASS等5文字ラベルが省略されていた
  → `.col-ticker{min-width:100px}`をth/tdに付与して解消
- **問題②**: `table-layout:fixed`+colgroupのpx幅指定（全docs/配下でこのページのみ
  使用）により、コンテナ幅が808px未満（半分画面幅相当）になると総合判定列（118px）の
  サブラベル「成長・生存・黒字化が均衡」がはみ出していた
  → `table-layout:fixed`とcolgroupを廃止して自然幅テーブルに変更し、
  EPIC-LAYOUT-1標準パターン（`data-priority="low"`＋`docs/common/site-theme.css`の
  既存`@media(max-width:1000px)`ルール）をCF改善列・粗利率列に適用。
  `@media(max-width:1000px){.tbl-wrap table{min-width:0}}`をページ内で追加し
  間引き後に残り列が自然に広がるようにした（portfolio/index.html準拠）
- **検証**: Playwrightで600/850/960/1024/1400pxの5幅を実機確認。
  全幅でTICKER列バッジ省略0件・総合判定列はみ出し0件、960px以下でCF改善・粗利率列が
  非表示、1024px以上で再表示されることを確認。check_links.py でリンク切れ0件も確認
- **これでEPIC-LAYOUT-1の統合元7件（グループA/B/C）が全件完了**。
  詳細はBACKLOG.mdの[[MACRO-DISP-2]]（850px/1200px幅の残存課題）のみ低優先度で継続

---

## 2026-06-22

✅ [EPIC-LAYOUT-1 グループB] フレックス行ラベル省略・推奨列折り返し不揃いの修正（2026-06-22 完了）
- **MACRO-DISP-1**: `docs/market-monitor/macro-pulse/index.html`の`.phase-signals`の
  `minmax()`値を200px→260pxに拡張（200→240→260pxの2段階調整。240pxでは800px幅で
  「Michigan Sent.*」が省略されたため260pxへ追加調整）
  - 700/800/960/1024/1400px幅で省略解消を確認
  - **850px/1200px幅で「Michigan Sent.*」の省略が残存**（モグラ叩き現象。
    根本原因は親コンテナ`.v3-main`の幅がビューポート幅に比例せず非線形に
    変動するため。下記[[MACRO-DISP-2]]として新規登録）
  - コミット: ef52e10e6
- **HYPE-DISP-1**: `docs/value-monitor/hypecore/index.html`の推奨クラス
  （`.rec-buy`/`.rec-hold`/`.rec-sell`/`.rec-watch`）に`white-space:nowrap`追加、
  推奨列`<td>`に`.rec-cell{min-width:120px}`付与（「様子見（底打ち）」実測幅89px+
  td padding20pxが根拠）
  - 700〜1400px全幅で行高さ33pxに統一、折り返し不揃いを完全解消
  - 副作用として700/750/800/1024px幅でテーブル内（`.table-wrap`）横スクロールが
    新規発生するが、bodyレベルのはみ出しはなし（HYPE-DISP-2と同じ許容範囲の挙動）
  - コミット: e8857f6b2
- **教訓**: グループAのMP-LAYOUT-1に続き、グループBの2件も「960px固有の問題」
  という当初の前提が外れた（MACRO-DISP-1は700〜1400px全幅で発生する画面幅非依存の
  問題、HYPE-DISP-1も960pxでは無症状で700px/1024pxで発生する非単調な問題だった）。
  EPIC-LAYOUT-1全体を通じて「960px境界の問題」という分類自体を疑ってから
  実装することが重要だと再確認した

✅ [MP-BREADTH-2] Market Pulse 市場の広がり強化・二極化警告実装（2026-06-22 完了）
- **内容**: 市場の二極化（一部銘柄のみ上昇）を捉えるための5指標を新規実装
  1. RSP/SPY乖離指標（Equal Weight vs Cap Weight）: yfinanceで1d=-0.576pt /
     20日平均=+0.097ptを実取得確認。`breadth_data.json`に保存
  2. 累積A-Dライン: 既存47件をバックフィル（最古日ad_line=102→最新日530）。
     既存のセンチメントスコア推移チャート（OSC_METRICS、トグル選択式）に
     S&P500・McClellanとあわせて新規トグル項目として追加
     （依頼は専用ミニチャート新設だったが、既存の複数指標トグル比較機構を
     再利用する形に実装方針を変更した）
  3. NH/NL・AD Ratio独立警告バッジ（AD Ratio<0.8→「⚠ 市場が薄い」、
     NH-NL<-50→「⚠ 新安値優勢」）
  4. S&P500ベース近似マクラレンオシレーター（19日EMA-39日EMA、実データ-16.4。
     NYSE全銘柄ではなくS&P500構成銘柄ベースの近似である旨を画面上に明記）
  5. 二極化総合警告バッジ（上記+50MA%<60%+マクラレン低下中の5シグナル中
     3つ以上点灯で「市場の二極化を検出 N/5シグナル点灯」表示）
- **センチメントスコアウェイト変更**: 既存7指標（VIX/MA乖離/ADRatio/HYG-LQD/
  NH-NL/グロースバリュー/出来高）を×0.9に圧縮し、RSP/SPY乖離(20日平均)を
  weight 10%で新規追加。合計100%を維持（実行確認済み）
- **コミット**: 24cfb42d2
- **確認**: pytest 110件パス、Python構文チェックOK、Playwrightで960px/1400px幅の
  レイアウト崩れ・JSエラーなし、二極化シナリオ注入テストで5/5シグナル点灯の
  全バッジ表示を確認
- **前段の調査**: 同日実施したMarket Pulse現状調査（実装無し・調査のみ）で
  FRED/yfinanceでのNYSE全銘柄ベースの厳密なヒンデンブルグオーメン再現は
  困難と判明したため、本実装はS&P500ベースの近似・代替指標として位置づけた

✅ [FOUR-DELETE-1] FOUR（Shift4 Payments）を全システムから削除（2026-06-22 完了）
- **理由**: 投資対象として見送り。株式数XBRLバグ（2026-06-14のBUG修正、CIK誤報告74倍過小）により
  EPSアナライザーが構造的に無効化されており、IV計算の信頼性も担保できないと判断
- **削除範囲**:
  - 設定: `config/cik_lookup.csv`・`beta_config.json`・`discover_config.json`（+`docs/portfolio/data/`同期）・
    `monitor_tickers.yaml`・`docs/value-monitor/tanuki_valuation/data/tickers.json`（count 96→95）・
    `docs/value-monitor/tanuki_valuation/data/.watcher_state.json`・
    `src/value/tanuki_valuation/growth_sanity.py`（業種分類オーバーライドの不使用エントリ）
  - 生成データ: `common/sec_data/{data,normalized,raw,ttm}/FOUR`関連・
    `docs/value-monitor/tanuki_valuation/data/FOUR/`一式・`hypecore_history/FOUR.json`・
    `docs/value-monitor/hypecore/data/FOUR_poc.json`・`src/value/hypecore/data/FOUR_poc.json`（実体側）・
    `docs/value-monitor/adjusted_eps_analyzer/data/FOUR`（空ディレクトリ）。計104ファイル
  - **意図的に残置**: `docs/discover/data/daily_report.json`・`docs/integrated-dashboard/history.json`・
    `docs/value-monitor/tanuki_score/history.json`（日付キーの共有履歴ログのため遡及編集せず）、
    `common/sec_data/data/_cik_cache.json`のFOURエントリ（単なる参照キャッシュで実害なし）
- **削除手順書の見落とし発見**: 当初の削除依頼にはなかった`beta_config.json`・`growth_sanity.py`・
  `src/value/hypecore/data/`（docsとは別の実体ファイル）・`.watcher_state.json`の4件を
  grep横展開で追加発見・対応した。CLAUDE_CODE_START.mdの銘柄削除手順にも
  `growth_sanity.py`等のコード内ハードコード参照は記載がなく、今後の削除作業でも
  `grep -rln "TICKER" docs/ config/ common/ src/`のような全文横断検索を都度実施する必要がある
- **コミット**: f3cd4a111
- **確認**: `system_health.py` HEALTHY（95/95件存在、latest.json欠損0件）・pytest 110件パス・
  `check_links.py` エラー0件
- BKNG・FCXは（同種のEPSアナライザー無効銘柄だが）削除対象から明示的に除外

✅ [MP-LAYOUT-1] Tech Pulseゲージ3列が1行に収まらず縦積みになる問題の修正（2026-06-22 完了・EPIC-LAYOUT-1グループAへ追加対応）
- **背景**: 当初の調査（同日早い時点）で「`.unified-gauge-row`は`flex-wrap:wrap`があるため
  オーバーフローしない＝対象外」と判断したが、その後の指摘で「オーバーフローしない＝
  正常」ではなく「1行に収まるはずのゲージ3つが常に縦積みに折り返される」こと自体が
  症状であると判明し、対応した
- **原因**: 列幅（391px/443px）の正体はSVGゲージ本体（固定180px）ではなく、
  `.tp-gauge-title`内のサブタイトル文言（折り返し制約なしの1行テキスト）だった。
  700px〜1100px幅のいずれでも3列合計が利用可能幅を超えるため、どの幅でも縦積みになっていた
- **修正**: `.tp-gauge-title`と乖離説明文divに`max-width:172px`を追加してサブタイトルを
  複数行に折り返すようにし、列幅の必要量を391px/443px→180px/212px程度に圧縮。
  あわせて`.unified-gauge-row`のインラインgapを40px→12pxに縮小。
  結果、700px幅以上で3列が常に1行に収まるようになった（Playwrightで700/760/800/960/1024/1400px
  全幅で1行表示を確認）
- **派生バグを分離**: 調査の過程で「GREEDラベル見切れ」も報告されたが、検証の結果
  これは画面幅に依存しない別バグ（ゲージ針が中央ラベルに重なる固定ジオメトリの問題、
  1400px幅でも再現）と判明したため、本対応には含めず[[MP-GAUGE-NEEDLE-1]]として
  BACKLOG.mdに新規登録した

✅ [EPIC-LAYOUT-1 グループA] 固定/自然幅テーブル＋横スクロール対応（PORT-LAYOUT-3 / PORT-DISP-3 / HYPE-DISP-2、2026-06-22 完了）
- **実装方式**: `docs/common/site-theme.css`に`@media (max-width:1000px)`で
  `[data-priority="low"]`を`display:none`にする共通ルールを追加（EPIC-LEGEND-1/
  EPIC-HEADER-1と同じ「共通CSS追加＋属性付与」パターンを踏襲）
- **教訓（regression発生→即修正）**: 当初`table{min-width:0 !important}`も
  site-theme.cssにグローバルで追加したが、これはdata-priority未適用の他ページの
  tableにまで波及し、admin.html(min-width:600px)・tanuki_valuation/index.html
  (820px)・stock.htmlの`.matrix-table`(400px)のmin-widthを960px以下で0に
  潰すregressionを発生させた（pushしてから気づいた）。共通CSSに書くのは
  `data-priority`の表示制御のみに留め、min-width解除は実際に必要な
  `portfolio/index.html`自身の`<style>`内で`.tbl-wrap table`にスコープして
  追記する形に修正した。**「共通CSSに書く」＝「個別ページの調整も全部共通化してよい」
  ではない**。要素セレクタ（`table`等）を共通CSSの`@media`に書くと、その共通CSSを
  読み込む全ページに無条件で波及する点に注意（クラス無しの裸セレクタは特に危険）
- **PORT-LAYOUT-3/PORT-DISP-3**（`docs/portfolio/index.html`の明細テーブル、13列）:
  加重平均単価・取得総額・現在株価・理論株価・メモの5列に`data-priority="low"`を付与。
  TOTAL/CASH行は元々`colspan`でまとめていたが、列ごとの個別`<td>`に分解してから
  対応する列に同じ`data-priority`を付与（colspanのまま非表示列を間引くと表組みの
  グリッドモデルがズレるリスクがあったため）。960px幅でscrollWidth 1201→918pxとなり
  横スクロール解消。PORT-DISP-3で問題視されていた乖離率列は常時表示列として残した
- **HYPE-DISP-2**（`docs/value-monitor/hypecore/index.html`の銘柄一覧テーブル、11列）:
  ライフサイクル・Rule of 40・高値比の3列に`data-priority="low"`を付与。
  960px幅でscrollWidth 980→920pxとなり横スクロール解消
- **MP-LAYOUT-1（Tech Pulseはみ出し）は対象外**: 2026-06-21調査時点でグループAに
  分類されていたが、本セッションでPlaywrightによる実機検証（850px/900px/960px/1024px）
  を実施したところ、いずれの幅でも`.unified-gauge-row`に横はみ出しは再現しなかった
  （`.unified-gauge-row`はすでに`flex-wrap:wrap`が設定済みで、2つのゲージ＋乖離情報が
  自然に縦積みされる）。調査時点から状態が変わったか、調査対象範囲の認識違いの
  可能性がある。BACKLOG.mdの[[EPIC-LAYOUT-1]]側からはMP-LAYOUT-1のグループA該当分を
  除外して記録した
- **検証方法**: ローカルで`docs/`をGitHub Pagesのベースパス（`/On-a-journey/`）に
  合わせて配信する必要があったため、`New-Item -ItemType Junction`で`docs`を
  `On-a-journey`という名前にマウントしたディレクトリ経由でhttp.serverを起動し、
  Playwrightで960px等の各幅でscrollWidth/clientWidthとスクリーンショットを確認した
  （portfolio/index.htmlはクライアント側パスワード認証があるため、テスト時のみ
  `auth-screen`を直接非表示にして`loadData()`を呼び出した。本番の認証ロジック自体は
  変更していない）
- pytest 110件全件パス（フロントエンドのみの変更のため回帰なし）。1400px幅では
  両テーブルとも全列表示を維持することも確認済み

## 2026-06-21

✅ [EPIC-LAYOUT-1-INVESTIGATION] 27インチ半分画面対応の現状調査（2026-06-21 完了・調査のみ）
- **背景**: [[EPIC-LAYOUT-1]]（27インチ半分画面・列幅・はみ出し対応）の統合元9件
  （MP-LAYOUT-1, PORT-LAYOUT-3, PORT-DISP-3, MACRO-DISP-1, SILO-DISP-3, TVAL-TS-1,
  TVAL-TS-2, HYPE-DISP-1, HYPE-DISP-2）について、実装に先立ち現状調査を実施。
  本セッションでは調査のみでファイル変更（実装）は行っていない
- **調査方法**: 960px幅（27インチ半分画面相当）でのheadless Chrome検証＋
  各画面の静的コード解析（行番号レベルで原因箇所を特定）
- **既存共通CSS基盤の確認**: `docs/common/site-theme.css`にはメディアクエリ・
  コンテナクエリが一切存在せず、960px境界の共通設計は皆無と判明。各画面が
  個別のブレークポイント（480/640/700/768/900/1000px等バラバラ）で対応して
  おり、`tanuki_valuation/index.html`・`hypecore/index.html`・
  `hypecore/detail.html`はレスポンシブ対応が完全に皆無だった
- **9件を症状別に4グループへ分類**:
  - グループA（固定/自然幅テーブル＋横スクロール）: MP-LAYOUT-1の一部、
    PORT-LAYOUT-3、PORT-DISP-3（`portfolio/index.html`の同一テーブル・
    実質同一バグと判明）、HYPE-DISP-2
  - グループB（フレックス行ラベル省略）: MACRO-DISP-1（`.pg-sig-name`の
    ellipsis省略を960pxスクショで実視確認済み）、HYPE-DISP-1の一部
  - グループC（`table-layout:fixed`、列幅が常時カツカツ）: SILO-DISP-3
    （`stonks-silo/index.html`の`<colgroup>`固定px幅設計が原因。960px固有の
    問題ではなく列幅設計自体の見直しが必要なため個別対応とする）
  - グループD（純粋なバグ、レイアウト課題ではない）: TVAL-TS-1（ISO文字列
    未整形表示）、TVAL-TS-2（`fmtDate()`の`slice(5)`がフルISO文字列に対して
    破綻する実装バグ、Pythonで`"06/20T17:36:48+09:00"`という壊れた出力を
    再現確認済み）。960px特有の問題ではなく解決策もJSロジック修正のため、
    [[TVAL-TS-FIX-1]]として新規分離した（BACKLOG.md側で対応済み）
- **実装方式の検討**: 3案（①data-priority属性＋`@media`段階的非表示、
  ②横スクロールUIの統一強化のみ、③`@container`クエリ採用）を比較し、
  「①をまず`@media`ベースで導入し、効果を見てから`@container`へ段階拡張する」
  方針を採用（個人利用ツールのためブラウザ互換性の制約は実質なし。
  EPIC-LEGEND-1/EPIC-HEADER-1と同じ共通CSS追加＋属性付与パターンを踏襲）
- **次回着手順序**: グループA → グループB → グループC（SILO-DISP-3は個別対応）。
  BACKLOG.mdのEPIC-LAYOUT-1セクションを対象7件に整理し、着手順序・実装方式を
  注記。TVAL-TS-FIX-1を新規追加した
- 本セッションはファイル変更なし（BACKLOG.md/BACKLOG_DONE.mdへの記録のみ別途実施）

✅ [MACRO-RISKSCORE-CHECK-1] RECESSION RISK SCORE急変動（35→27）の原因調査（2026-06-21 完了・調査のみ）
- **発端**: ユーザーから「先週比35→現在27と短期間で8pt下落しているが原因は何か」との
  確認依頼。コード変更は行わず原因究明のみ実施
- **結論**: 8ポイント下落は計算バグではなく、2つの要因の組み合わせと判明
  - **要因①（構造的・既知）**: 「○ヶ月前比/先週比」はlerp（線形補間）方式、「現在」は
    step（階段関数）方式で算出される仕様（コミット`c3eb81572`、本日対応済みの
    [[MACRO-COMPUTE-DUP-1]]により「現在のみstep統一・過去日付は引き続きlerp維持」と
    確定済みの意図的設計）。この方式の違いだけで2-3pt相当のズレが生じる
  - **要因②（支配的要因）**: フィラデルフィア連銀製造業景況指数（ウェイト18%）が
    -0.4→+10.3へ急改善（6月分データ、2026-06-19公表・`05_events.csv`へ反映）。
    これが8〜11pt相当を占める、本物の経済データ変動
- **検証方法**: `05_events.csv`の実データをPythonで`computeCurrentScore()`/
  `computeScoreAsOf()`双方のロジック通りに再現し、ユーザー報告値（32/29/34/35/27）と
  完全一致することを確認した上で、lerp統一・step統一それぞれの条件で6/14時点と
  現在を再計算（lerp統一: 35→29、step統一(point-in-time): 38→27）。いずれの方式で
  揃えてもフィラデルフィア連銀指数の変化が下落の大半を説明することを確認
- 他7指標（YC/HY Spread/Building Permits/CFNAI/Initial Claims/Michigan Sentiment/
  Sahm Rule）はこの期間ほぼ無風で、閾値（バケット）を跨ぐ変化もなし
- 先読みバイアス対策（`updatedMs<=targetMs`、`idxLatestKnownAsOf`、MACRO-BUG-1由来）が
  正しく機能しており、「先週時点ではまだ5月分(-0.4)しか分かっていなかった」という
  時系列整合性も確認済み。算出ロジック自体に新たなバグは発見されなかった
- **副次的な訂正**: ユーザーが当初想定していた8指標構成に「M2 Money Supply」が
  含まれていたが、実際のRECESSION RISK SCOREの8指標目は「Michigan Consumer
  Sentiment」であり、M2はNET LIQUIDITYゲージ（別指標）にのみ使用されている点を
  調査時に確認・報告
- **対応**: 不要、現状維持（ファイル変更なし）

✅ [MP-FALLBACK-DISPLAY-1] 取得失敗時の前回値補完＋表示区別の実装（2026-06-21 完了）
- **背景**: ^IRXの4日連続取得失敗等を機に、Market Pulseの市場データ表示方針を
  3パターンに整理: ①正常値=実数値表示 ②休場日等で本来データがない=
  yfinanceのperiod="5d"仕様により前営業日データが自動表示（既存仕様・対応不要）
  ③取得失敗（本来データはあるはず）=前回値で補完し、リアルタイム値と記号で区別。
  本対応は③を実装するもの。①②には一切手を加えていない
- **データ収集側（collect_and_send.py）**:
  - `_load_recent_entries()`: market_data.jsonの直近`FALLBACK_LOOKBACK_ENTRIES`
    （=5）件を新しい順に読み込む新規ヘルパー
  - `_is_real_value()`: あるエントリが「本物の値」かを判定する新規ヘルパー。
    `is_fallback`タグ付きを除外するだけでなく、**コンテナのdict自体は存在するが
    中の`value`/`change_pct`フィールドだけNoneという混入データ（MP-DATA-NULL-1の
    NaN→null置換で生じたパターン）も「本物ではない」と判定する**よう設計。
    実装中の単体テストで、この判定を `prev_val and not prev_val.get("is_fallback")`
    のみにすると、2026-06-21の汚染エントリ（S&P500.value=null等）を誤って
    「正常値」として補完元に使ってしまうバグを発見・修正済み
  - `_fill_fallbacks()`: indicators/asset_flow双方に使える共通関数。値がNoneの
    キーについて、直近5件を新しい順に遡り、最初に見つかった「本物の値」を
    コピーして`is_fallback: true`を付与する。フォールバックの連鎖（フォール
    バックされた値をさらにフォールバック元にする）を避けるため、
    `is_fallback=true`のエントリは探索時にスキップして遡り続ける。5件以内に
    見つからなければNoneのまま据え置く（「無限に古いデータを引きずらない」
    という要件を5件の探索上限で実現）
  - `__main__`内で`get_realtime_data()`直後・`collect_asset_flow()`直後にそれぞれ
    `_fill_fallbacks()`を適用。**`compute_sentiment()`はフォールバック適用前の
    今回実測データのみで算出**（センチメントスコアの計算ロジック自体は
    今回のスコープ外、副作用を避けるため意図的に順序を分離）
  - 既存の`[WARN]`ログに、補完を行った旨／5件以内に見つからずnullのまま
    据え置いた旨をそれぞれ追記
- **フロントエンド側（index.html）**: `renderMetrics()`・`renderAssetFlow()`
  （タイル・履歴行の両方）で`is_fallback`を検出した場合、①背景色を通常の
  緑/赤グラデーションから`var(--sur2)`（「—」と同じ無彩色）に、文字色を
  `var(--mut)`に変更し、②値の末尾に`※`マーク（`.stale-mark`、`var(--amb)`、
  クリック/ホバーで`ⓘ`アイコン付きツールチップ表示）を付与。値自体は実数値の
  まま表示し、`opacity:.7`の`.is-stale-value`クラスで視覚的に控えめにする。
  ツールチップ本文（前回値の日付を含む動的文言）は`info-tooltip.js`の
  `data-info-text`属性を利用（CLAUDE_CODE_START.mdの既存規約に準拠。日付が
  値ごとに変わる動的内容のためglossary.json静的辞書は使わず、新規エントリ追加なし）
- **「—」表示との視覚的区別**: 「—」は引き続き`var(--mut)`単色・記号なし。
  フォールバック値は「実数値＋※マーク＋ⓘアイコン」で構成が異なり、一目で
  区別可能
- **動作確認**: ローカルでheadless Chromeを使い実際にレンダリング結果を
  スクリーンショット確認（テスト用に`market_data.json`へ一時的に
  `is_fallback:true`のダミーデータを注入→確認後に元の状態へ復元、
  リポジトリには反映していない）。短期国債(^IRX)タイルが「+1.05%※ⓘ」と
  灰色背景で表示され、同じ画面内でLQD列の「—」（データなし）、SPY列の
  通常色「+1.04%」（正常値）と明確に区別できることを確認。S&P500メトリック
  カードでも同様に「7,501※ⓘ」表示を確認。pytest 110件全パス・
  check_links.pyエラー0件・market_data.json正常パースを維持
- **SYSTEM_MAP.md**: 新規システム・新規データ依存関係の追加ではなく既存
  Market Pulse内部の表示ロジック拡張のため、更新不要と判断

✅ [MP-IRX-FRED-1] 短期国債データ取得をyfinance(^IRX)からFRED API(DGS3MO)へ切替（2026-06-21 完了）
- **発端**: `asset_flow.short_bond`（^IRX）がGitHub Actions環境からの収集で
  4日連続（6/18〜6/21）取得失敗（None）。Yahoo Finance公式サイトでは同期間の
  ^IRXデータが実在することをユーザーが直接確認しており、「データ不在」では
  なく「取得経路側の問題」と判明（推定原因: GitHub Actions環境のクラウドIPに
  対するYahoo側レート制限。スクリプト内に約29回の逐次yfinance呼び出しに
  対しsleep等の間隔調整が皆無で、かつ`^IRX`等の指数系シンボルはETF系シンボル
  （SHV/GLD/TLT/LQD/HYG/SPY、同期間14日で実質ノーエラー）よりYahoo側の
  配信が不安定という状況証拠あり。GitHub Actions実行ログ自体は本セッション
  からは認証不足のため確認不可だった）
- **対応**: `collect_asset_flow()`内の`short_bond`のみ、新設の
  `fetch_fred_short_bond()`経由でFRED API（`DGS3MO`＝3ヶ月T-Bill流通市場
  利回り系列）から取得するよう切替。`fredapi`は既存の`fetch_vxn_from_fred()`
  （VXNCLS取得）と同じ`FRED_API_KEY`環境変数・呼び出しパターンを踏襲しており、
  GitHub Secrets側の追加設定は不要（`Market_Pulse_Update.yml`に既に
  `FRED_API_KEY`が渡されている）
- **他6資産（yfinance経由）には一切手を加えていない**。ループ内で
  `short_bond`のみ専用関数に分岐させる形で、既存の`result`辞書構造
  （label/ticker/desc/value/change_pct/date）はそのまま維持
- **change_pctの定義**: 他6資産（ETF価格ベース）との表示整合性を優先し、
  ^IRX時代と同じ「利回り値そのものの変化率（%）」をそのまま踏襲（bp差分には
  変更していない）。フロントエンド（`renderAssetFlow()`）側の表示ロジック・
  色分け・ツールチップは無改修で動作する
- **FREDの更新ラグ対応**: DGS3MOは1営業日程度遅れて公表されるため、
  `date`フィールドはFRED側の実際の最終データ日付をそのまま採用（既存の
  他資産が休場日に前回値の日付を据え置く挙動と同じ設計）
- **副次対応**: `collect_asset_flow()`の残り6資産（yfinance経由）の
  `hist is None`等の取得失敗分岐に、失敗理由（hist=None／行数不足／NaN混入）
  を切り分けるログ出力を追加。次回同種の取得失敗が他銘柄で発生した場合に
  GitHub Actionsログから直接原因を追えるようにした
- **動作確認**: ローカル環境（FRED_API_KEY設定済み）で`fetch_fred_short_bond()`
  単体・`collect_asset_flow()`全体を実行し、`short_bond`が`value=3.83,
  date=2026-06-17`（FREDの最新公表日）で正常取得されることを確認。他6資産も
  従来通りyfinance経由で正常値を返すことを確認。pytest 110件全パス維持
- **SYSTEM_MAP.md**: 「Market Pulse ← yfinance / CNN F&G / FREDデータ」の
  記載が既にFREDを情報源として含んでいたため、更新不要と判断（確認済み）

✅ [MP-RENDERALL-CRASH-1] Market Pulse表示崩れ（テックパルス未計算・スコア構成指標50%固定・Tech Pulseセクション「LOADING」停止）の一連の対応（2026-06-21 完了）
- **経緯①（症状発覚〜応急処置）**: 本日朝の自動更新コミット`ccd763082`（github-actions[bot]）で
  `market_data.json`に生の`NaN`トークンが24箇所混入 →`Response.json()`構文エラー→
  `index.html`が無言で`makeSample()`（ダミーデータ）にフォールバック（症状: テックパルス
  未計算、スコア構成指標6/7が50%固定）。`NaN`→`null`へのsurgical手動修正で復旧
  （ロールバックではなく直接修正を採用。理由は当日分の正当なデータを失わないため）
- **経緯②（恒久対応＝MP-DATA-NULL-1）**: `collect_and_send.py`の`Close`値抽出12箇所に
  `math.isnan()`ガードを追加し、`NaN`の再混入自体を防止（詳細は[[MP-DATA-NULL-1]]参照）
- **経緯③（新たな症状の発覚）**: ②の対応後、Tech Pulseセクションが「LOADING」のまま
  停止し、CNN F&G/VXN/QQQ vs SPY/乖離Zスコアが表示されない別症状が判明
- **根本原因**: `renderMetrics()`内`ind.value.toFixed(2)`（610行目）が、②によって
  `null`化された値（`S&P500`/`NASDAQ`等。オブジェクト自体は存在し`value`フィールドのみ
  `null`という形）に対して例外を投げていた。`renderAll()`が同期・try-catchなしで
  各render関数を直列呼び出ししていたため、1関数の例外で後続6関数（`renderMetricBtns`
  以降、Tech Pulse描画を含む）が一切実行されなくなる構造的問題だった。
  `renderAssetFlow()`の`pct.toFixed(2)`（`asset_flow.ig_bond`等）にも同型の漏れがあり、
  610行目の例外に隠れて潜在していた
- **根本修正（コミット`1a03e1b42`）**:
  `renderMetrics()`/`renderAssetFlow()`/`renderTimeline()`にnullガードを追加し、
  既存の「データなし」表示（カード/タイルの`—`表示）にフォールバックするよう統一。
  `renderAll()`を`RENDER_ALL_FNS`配列＋`forEach`+`try-catch`化し、1関数の例外が
  後続の描画を連鎖停止させない構造に変更（例外発生時は`console.error`で関数名付き
  ログを出力し無言で握りつぶさない）
- **横展開確認**: ファイル内の`.toFixed()`/`.toLocaleString()`呼び出し全箇所を監査。
  VIX9D比較（`vix9dRow`）はPython側でデータ無効時にオブジェクト全体が`null`になる
  設計のため既存ガードで安全、`sub_scores`系はPython側で常にスコアが補完される
  設計（無効時は中立値0.5＝50点を設定）のため安全と確認し、追加修正は不要と判断
- **教訓**: `NaN`の直接JSON出力という収集側の欠陥（MP-DATA-NULL-1）が表面化した際、
  その場しのぎでJSONを直すだけでは「オブジェクトは存在するが個別フィールドが
  `null`」という新しい状態を生み、フロントエンド側に潜在していた別のnullガード
  漏れを誘発した。データ修復とフロントエンドのエラー耐性（1箇所の例外が全体を
  道連れにしない設計）は別レイヤーの課題であり、両方そろって初めて再発に強い
  状態になる

✅ [MP-DATA-NULL-1] Market Pulse収集データのNaN混入防御（応急処置＋恒久対応、2026-06-21 完了）
- **発端**: Market Pulse画面で「テックパルス未計算」「スコア構成指標の多くが50%固定」と
  ユーザー報告。調査の結果、本日朝の自動更新コミット`ccd763082`（github-actions[bot]、
  cron 21:35 UTC実行）で`market_data.json`に生の（クォートされていない）`NaN`トークンが
  24箇所混入し、ブラウザ側`Response.json()`が構文エラーで例外 →
  `index.html`の`catch{allData=makeSample()}`が無言でダミーデータにフォールバックしていた
  ことが直接原因と判明（前回コミット`cf566c2ad`は NaN 0件で正常）
- **応急処置**: `market_data.json`の24箇所の生`NaN`トークンを`null`へ surgical 置換
  （ロールバックではなく手動修正を採用。理由: 当該エントリ内の他フィールド
  （tech_pulse score=78等）は正常値であり、ロールバックすると本日分の正当なデータが
  失われるため。CLAUDE_CODE_START.mdの「自動生成データファイルをcheckout --theirs等で
  古い版に巻き戻さない」原則とも整合）。修正後`json.load`で65件全件パース成功を確認
- **恒久対応**: `collect_and_send.py`に`_is_nan()`ヘルパーを新設し、Close値抽出箇所
  12箇所（main_tickers/NYSE Composite/IVW・IVE/大型対小型比/VIX9D vs VIX/HYG・LQD・
  HYG対LQD比/collect_asset_flow/_get_sp500_ma_deviation/fetch_qqq_tech_data/
  format_line）に`math.isnan()`ガードを追加し、NaN検出時は既存の`None`フォールバック
  経路（`data[name]=None`等）に合流させた。`compute_sentiment()`等の下流ロジックは
  元々`is not None`チェックで作られておりNaNだけがすり抜けていたため、下流の修正は不要
  だった
- **副次的に発見・修正したバグ**: NYSE Compositeブロックで`divergence_vs_sp`の算出に
  同一条件の判定が2箇所に重複しており（`sp_hist`の検証を2回別々に実施）、NaNガードを
  片方にだけ追加すると`UnboundLocalError`になることをモックテストで検出。`sp_valid`
  フラグに一本化して解消（ARCH-DATA-1的な「同一判定の分散」パターンと同根）
- **検証**: ①ライブ実行で`get_realtime_data()`がNaN 0件を返すことを確認、②`^GSPC`の
  最新Closeを`NaN`にモックした再現テストでクラッシュなく`S&P500:null`に正しく
  フォールバックすることを確認、③`json.dumps(data, allow_nan=False)`で厳密JSON妥当性を
  確認、④pytest 130件全パス（market_data.csv側にも同根の小文字`nan`文字列混入が
  残存することを発見したが、CSVは現状どこからも読み込まれておらず実害なしのため
  今回は対象外として記録のみ）
- **対応C（保留・報告のみ）**: `index.html`の「fetchエラー時に無言でダミーデータへ
  フォールバック」設計は変更せず、挙動の説明のみユーザーに報告（設計判断はユーザー側）

✅ [EPIC-HEADER-1] ページヘッダー・タイトル共通部品化（2026-06-21 完了）
- **統合元9件全件対応**: TVAL-HEADER-1/2/3, TSCORE-FIX-1/3/4, EPS-DISP-1, HOME-FIX-2
  （TVAL-HEADER-4はEPIC自体の実行で解消）。対象4画面（TANUKI VALUATION/TANUKI SCORE/
  EPS ANALYZER/HOME）に適用。stock.html（個別銘柄詳細ページ）は動的バージョンタグの
  実用性が異なるため対象外として現状維持
- **新設**: `docs/common/site-header.js`（`header a.logo`を検出し、ロゴ画像・ドット・
  タイトル・サブタイトルを統一DOMに置換。`body[data-tool]`からツール名/タイトル/
  サブタイトルを自動解決。`data-title`/`data-subtitle`/`data-no-subtitle`属性で
  ページごとに上書き可能。バージョン表記は撤廃方針のため生成しない）
- **site-theme.css拡張**: `--tool-*`トークンをHOME画面の`.card-*`配色を正として統一
  （tanuki: #a78bfa→#8b5cf6、eps: #22d3ee→#3b82f6 に補正。tanuki-score/discover/
  portfolio/tailのbody[data-tool]マッピングを新規追加、tail はportfolio配下のため
  同色を採用）。`.site-header-inner`コンポーネントCSSと専用keyframe
  `site-header-pulse`（`color-mix(var(--acc))`でツール別アクセントに自動追従する
  パルス発光）を追加
- **発見した副次的効果**: TANUKI SCOREページは`.logo-dot`が`var(--grn)`固定で
  ページ内の実際のアクセント色（Daily Pick等で既に使われていた#14b8a6ティール）と
  不一致だった。新トークンへの統一でこの不一致が解消。HOME画面の`.card-vm`/`.card-tanuki`
  も「枠線・タグ等の`--card-acc`」と「タイトル文字の直書きhex」が食い違っていたが
  `--tool-eps`/`--tool-tanuki`補正により一致した
- TANUKI SCOREは独自に`--mono: 'DM Mono'`を上書きしSpace Monoフォントを読み込んでいな
  かったため、`--mono`上書きを削除しGoogle Fonts importにSpace Monoを追加（フォント
  不統一の実体的な原因）
- TANUKI SCOREフッターの「計算: Koichi式 v8.0」（TSCORE-FIX-4対象）を削除。
  TANUKI VALUATION/HOMEのヘッダー内version-tagも削除
- 検証: check_links.py リンク切れ0件、4画面とも HTTP 200 で配信されることを確認。
  ブラウザでの実描画確認は環境制約上未実施（手動確認を推奨）

✅ [TSCORE-DAILYPICK-BUG-1] TANUKI SCORE「今日の特選銘柄」APIキー未設定エラー表示（2026-06-21 完了）
- **直接原因①**: `daily_pick.json`が2026-06-20 17:16 JSTにXAI_API_KEY未設定のローカル検証実行
  （ARCH-SCORE-SYNC-1 Stage3のテスト目的）の出力のまま本番コミットされていた
- **直接原因②（自動更新が直らなかった真因）**: `daily_pick.py`の`build_data_package()`が
  `mkt.get("indicators", {}).get("VIX9D（短期VIX）", {}).get("value")`という3階層チェーンで
  market_data.jsonを参照していたが、`indicators["VIX9D（短期VIX）"]`がキー自体は存在し値が
  `None`の場合（2026-06-19以降発生）、`dict.get(key, default)`のdefaultはキー不在時のみ有効
  なため`None.get("value")`でAttributeErrorが発生し、GitHub Actions側の自動実行
  （XAI_API_KEY設定済み環境）が`Run daily_pick`ステップで2日連続クラッシュしていた
  （このバグ自体は2026-05-23のコミットから存在する潜在バグで、本日・前日の変更とは無関係）
- **修正**: `_nested_get(d, *keys)`ヘルパーを新設し、ネスト辞書アクセスを「途中の値がNone/非dict
  ならその時点でNoneを返す」安全な実装に統一。3階層チェーン10箇所（vix/vix9d/tech_pulse系/
  asset_flow系）を置換。2階層チェーン（isinstanceガード済みで元々安全）は変更なし
- **データ復旧**: 修正後にXAI_API_KEYを使ってdaily_pick.pyをローカル実行し、正常な
  AIレポート付きdaily_pick.json/history.jsonを生成・コミット（workflow_dispatchの
  実行権限がローカル環境になかったため、同等の結果が得られるローカル実行で代替）
- 「選出理由：分類変化：仕込み時 → BUY」表記は別件・コードバグではなく、ARCH-SCORE-SYNC-1
  での分類体系統一直後に旧history.json内の旧ラベルと1回だけ比較されて生じた想定内の
  過渡的表記と判明（history.jsonは新規実行ごとに新ラベルへ更新されるため自然に解消する）
- 予防的に`src/portfolio/snapshot.py`の同型パターン（「ドル円」「S&P500」参照箇所、
  daily_pick.pyと同じ`TANUKI_Score_Update.yml`内で連続実行されるため波及リスクがあった）
  にも同じ`_nested_get`ヘルパーを適用
- 検証: ローカル再現テストでクラッシュを確認 → 修正適用後に再実行しクラッシュ解消を確認、
  Playwrightで実機ページの「APIキー未設定」表示が消え正常なAIレポートが表示されることを
  確認。pytest 152件全パス、check_links.py リンク切れ0件

✅ [EPIC-LEGEND-1] 指標説明・凡例コンポーネントの共通化（2026-06-21 完了）
- **統合元18件中15件を実装、3件は別種の問題と判明し除外**（詳細はBACKLOG.md該当項目の注記参照）:
  - 除外: HYPE-DISP-5（X軸整列＝レイアウトバグ）, MP-DISP-6（俳句フレーズ＝要否判断タスク）,
    TVAL-FORMULA-1（算式整合性監査＝説明追加ではなく実装監査）
- **共通コンポーネント新設**: `docs/common/glossary.json`（用語キー→説明文の静的辞書）、
  `docs/common/info-tooltip.js`（`<span data-info="key">`を自動検出しホバー/タップでポップ
  アップ表示。動的に追加されるDOM要素もMutationObserverで自動検出。後から動的な説明文を
  付与したい場合は`data-info-text="..."`属性も後付けで使える ― 属性変更もMutationObserver
  で監視）
- **試験実装で発見・修正したバグ**: `<span data-info>`をクリックで開閉トグルする初期実装は、
  ホバーで開いた直後のクリックで即座に閉じる不具合があった。クリックは「常に開く/再描画」
  のみとし、閉じる動作はmouseleave・ドキュメントクリック・スクロールに委譲する設計に変更
- **システム別実装内容**（計15箇所＋既存tip-box拡張2箇所）:
  - HYPE CORE: index.htmlステージ列見出し、detail.html PEG・EV/EBITDA・株価チャート背景色凡例
    （計4箇所。チャート背景色は当初index.htmlのみだったが原文確認でdetail.htmlが本来の対象と判明し追加）
  - DISCOVER: 要注目ゾーン判定基準、ニュースタグ色凡例（2箇所）
  - PORTFOLIO: HYPEMIX危険バッジ判定基準（1箇所）
  - TANUKI TAIL: テーゼ健全度の基準（1箇所）
  - MARKET PULSE: VIX判定文言、乖離基準、資金の動き「–」表示の意味、スコア構成バー色凡例（4箇所）
  - MACRO PULSE: REPO/TGA/RRP用語、REGIMEの解釈、AI失敗時のmodel欄の意味、FOMC声明日付
    （4箇所。FOMC声明日付は`data-info-text`による動的注入の実例）
  - STONKS SILO: 生存期間「–」・黒字化「–」の意味、拡大再生産ドットの意味
    （生存期間・黒字化は既存の`tip-box`カスタムツールチップに追記する形で対応。
    新規コンポーネントとの二重実装を避けるための判断）
  - TANUKI SCORE: DuPont⚠マーク（`data-info-text`化で可読性改善）、ROE色分け基準（2箇所）
- **CLAUDE_CODE_START.md更新**: 「新規銘柄属性を追加した場合の必須対応」に③として
  「ユーザー向け数値・バッジを追加した場合はglossary.jsonに説明を追加する」を追記（再発防止）
- 検証: 全システムでPlaywrightによる実機ホバー/クリック確認、pytest152件全パス、
  check_links.pyリンク切れ0件を確認してから各システム単位でコミット

✅ [ARCH-MATRIX-DUP-1] RICE×乖離率マトリクスの重複・差異実装（2026-06-21 完了）
- **設計判断（ユーザー確定）**: TANUKI SCORE「②RICE×乖離率マトリクス」とTANUKI VALUATION
  「①投資効率系」はそれぞれ異なる用途（前者=多銘柄の最終相対判断、後者=TANUKI VALUATION
  自体・RICE指標の精度検証）を持つため統合せず、両画面とも維持。表示差異のみ解消する方針
- `docs/value-monitor/tanuki_valuation/stock.html`のX軸（乖離率）上限を+100%固定クランプ
  から、tanuki_score側と同じ+300%（X_MAX_CLIP方式）に変更。`buildScatterSVG()`に`xClip`
  オプションを追加し、超過銘柄は右端に▶で縦積み折りたたみ表示（tanuki_score側のoverDotsと
  同方式）。`xClip`は①投資効率系パネルのみ指定し、②③④パネルは未指定のため挙動不変
- ラベル重なり回避ロジックを追加（`xClip`指定時のみ有効）。tanuki_score側の「ドット直上
  固定配置」を基準に、ラベルのバウンディングボックスが衝突しなくなるまで上方向へ
  ずらす貪欲アルゴリズムを実装。X軸+300%化と合わせて、FOUR/TASK/ADBE/NVDA/INTU/CPRT/
  FRSH/GTLB/META/FLYW等の密集を解消
- 対象銘柄ゲート（`rice.available`チェック）の差異を予防的に解消。tanuki_score側の
  `_stocks`構築に`riceAvailable`フィールドを追加し、`renderRiceMatrix()`のフィルタに
  `s.riceAvailable`を追加（stock.html側の`rice.available && riceVal>=0`と同条件に統一）
- 配色ロジック（TANUKI SCORE7分類 vs 象限位置ベース4色）は意図的に維持・変更なし
- **検証（Playwrightで実ページ起動・実データ照合）**:
  - ラベル重なり: 修正前7件（IOT-GOOGL/IOT-NOW/IOT-HQY/CPRT-META/FLYW-INTU/FRSH-GTLB/
    NVDA-FOUR）→ 修正後0件（バウンディングボックス衝突検出で確認）
  - 座標一致: 両画面のRICE有効銘柄49件全件で、ticker集合・upside値・RICE値が完全一致
    （差異0件）。SVGのtitle要素から実測値を抽出し _stocks の値と直接比較
- 検証: pytest 152件全パス、check_links.py リンク切れ0件

✅ [MACRO-COMPUTE-DUP-1] カスタム比較機能のスコア計算が別ロジック（lerp方式）で第3の値を返す（2026-06-21 完了）
- **調査結果（実装前にユーザー確認済み）**: `computeScoreAsOf()`のlerp方式は重複バグではなく、
  コミット`c3eb81572`（2026-05-22「RECESSIONスコアをステップ関数→線形補間に変更（閾値付近の
  急変を緩和）」）で意図的に導入されたもの。用途はスコア履歴チャート（1996年〜の長期推移、
  `renderScoreHistory`）とL3レーダーの時間スライダー（`onL3SliderInput`）で、過去日付を
  辿る際の急激な階段状ジャンプを緩和する目的。renderPhaseGauge()側はstep関数のまま据え置き
  だったため、asOf=「現在」を渡した場合だけstep版（38）とlerp版（35）の3つ目の値が出ていた
- **実装方針**: 全面統一（step化 or lerp化）ではなく、asOfが実質「現在」を指す場合のみ
  renderPhaseGauge()と完全に同一のロジックを使い、過去日付は引き続きlerpで補間する方式を
  採用（5/22の意図的な急変緩和修正を維持しつつ、「現在」の3値問題のみ解消）
- `renderPhaseGauge()`の指標スコア計算部分（trend3考慮のstep関数、8指標分）を
  `computeCurrentScore()`として分離・共通化。`renderPhaseGauge()`はこれを呼び出してDOM
  描画のみ行う構成に変更。`computeScoreAsOf(asOf)`の冒頭に`isEffectivelyNow(asOf)`判定を
  追加し、真の場合は`computeCurrentScore().score`をそのまま返す
- 検証（Playwrightで実ページを起動し検証。pytestではカバーできないフロントエンドJSのため）:
  `computeCurrentScore().score` / `renderPhaseGauge`のゲージ表示値 / `computeScoreAsOf(now)`
  / `computeScoreAsOf(今日23:59:59)`の4値が完全一致（27）することを確認。60日前等の過去日付
  では`isEffectivelyNow`=false・lerp値（30）を引き続き返すことを確認（lerp区分は維持）。
  比較バー4セル（3ヶ月前/2ヶ月前/前月末/先週）も正常表示・JSエラーなしを確認
- 検証: pytest 152件全パス、check_links.py リンク切れ0件

✅ [ARCH-PORTFOLIO-DUP-1] portfolio/index.htmlに独自のfunda/timing/classify実装が存在（2026-06-21 完了）
- ARCH-SCORE-SYNC-1の方針（判断ロジックをpipeline.pyに集約し、表示側は再計算しない）に
  倣い、`docs/portfolio/index.html`の独自実装`calcFunda()`/`calcTiming()`/`classify()`を
  削除。保有銘柄テーブルの分類は`latest.json`の`tanuki_score`/`funda_score`/`timing_score`を
  直接参照する方式に変更（PORT-LOGIC-1のfindHypemixCandidates()と同一パターンに統一）
- 副次的に、独自timing計算でのみ使われていたMarket Pulse fear&greedフェッチ（M_PATH/mkt/fg）
  が完全に不要になったため、フェッチ呼び出し自体を削除（不要なネットワークリクエスト解消）
- **実データでの差異検証**（保有中9銘柄: NVDA/PLTR/TSLA/CELH/APP/CRWV/SOFI/SOUN/ADBE）:
  分類バッジが旧計算と一致しなかったのは4/9銘柄（TSLA: HOLD→TRIM、CRWV: BUY→WATCH、
  SOFI: HOLD→WATCH、SOUN: HOLD→WATCH）。funda_scoreも6/9銘柄で乖離（旧JSの簡易3要素
  計算 vs pipeline.pyのRICE等を含む本格計算のため）。timing_scoreは全銘柄で一致
  （ARCH-SCORE-SYNC-1時点で既にtanuki_score/index.html側のtiming式とpipeline.pyが
  揃っていたため）。この差異はバグではなく、より正確なpipeline.py側の判定に
  統一されたことによる意図した変化
- 検証: pytest 152件全パス、check_links.py リンク切れ0件、div開閉整合性確認

✅ [TAIL-SEC-1] GH TOKENの平文入力欄がセキュリティリスク（TANUKI TAIL画面・2026-06-21 完了・2段階対応）
- 段階1（認証ゲート）: `docs/portfolio/tail/index.html`に`docs/portfolio/index.html`と同等の
  sessionStorageベース簡易パスワード保護（`checkPassword()`/SHA-256ハッシュ照合）を追加。
  PW_HASHはportfolio/index.htmlと共通値を流用、SESSION_KEYは`tail_auth`としてページ別に分離
- 段階2（トークン運用の根本対応）: ブラウザから直接実行していたGitHub Contents API
  書き込み（`fetchFile()`/`commitFile()`、contents:write権限のPATが必要）を廃止し、
  GitHub Actions `workflow_dispatch`経由の書き込みに移行。対象は「ポジション登録」
  「ジャーナル記録」「KPI確定」の3処理すべて（ユーザー判断により全件移行）
  - 新設: `.github/workflows/TANUKI_TAIL_Position_Write.yml`（workflow_dispatch、
    `action`/`payload`入力、GITHUB_TOKEN・contents:writeで書き込み・コミット・push）
  - 新設: `src/tail/workflow_write.py`（register_position/register_journal/confirm_kpis
    のサーバーサイド実装。コミットメッセージは`/tmp/tail_commit_message.txt`経由で
    `git commit -F`に渡し、シェルへの直接埋め込み（インジェクションリスク）を回避）
  - `tail/index.html`側はGH TOKEN欄の用途をactions:write専用のFine-grained PATに変更
    （placeholder/ヘルプ文言を更新）。書き込みが非同期になったため、登録系3関数は
    完了確認メッセージを「反映まで数十秒〜数分」に変更し、楽観的なローカル即時更新を廃止
  - テスト追加: `tests/test_tail_workflow_write.py`（11件、tmp_pathで実ファイルに触れず検証）
- 検証: pytest 152件全パス、check_links.py リンク切れ0件、ローカルサーバーで認証ゲートの
  表示・main-content非表示初期状態を確認

✅ [PORT-LOGIC-1] HYPEMIX注記の誘導先が不適切（PORTFOLIO画面・2026-06-21 完了）
- 設計判断: 「仕込みゾーン不足」時のDISCOVER誘導文言を廃止し、登録済み・分析済み銘柄
  （TANUKI VALUATION全96銘柄ロスター）からTANUKI SCORE BUY判定×HypeCore早期フェーズ
  （失望/蓄積期・期待覚醒期・期待拡大期）×未保有のAND条件で候補を直接抽出し、
  HYPEMIXセクション内にリスト表示する方式に変更
- 実装: `docs/portfolio/index.html`にtickers.json（全銘柄ロスター）取得を追加し、
  既存のtanukiMap/hypeMapフェッチ対象を保有銘柄のみから全銘柄に拡張。
  `findHypemixCandidates()`を新設し、latest.jsonの`tanuki_score`/`funda_score`/
  `timing_score`を直接参照（ARCH-SCORE-SYNC-1の方針を踏襲、独自再計算は行わない）
- 並び順: daily_pick.pyのstocks.sort（-funda, -timing）に揃え、上位5件まで表示
- 0件時は「BUY判定×仕込みゾーンの新規候補銘柄は現在ありません。」と表示
- 検証: 実データ（latest.json/poc.json）でのPythonシミュレーションにより、
  現状3件（NVDA/MO/VZ）が正しい順序で抽出されることを確認。pytest 110件全パス、
  check_links.py でリンク切れ0件を確認。既存のフェーズ分布表示・乖離判定ロジック
  （devHtml/badgeCls等）は変更していないため影響なし

✅ [DISCOVER-BUG-1] CELHで同一記事が重複表示される（2026-06-21 完了）
- 原因: `src/discover/collect.py`に重複排除ロジックが一切存在しなかった（不具合ではなく未実装）。
  NEWS_API/Grok web検索が同一の出来事（Bernsteinの格付け変更等）を複数配信元の別記事として
  取得し、Grokがそれぞれを別アイテムとして分類していた
- 修正: タイトル正規化（trim+小文字化）での完全一致を除外する`_dedupe_items()`を新設し、
  `classify_news()`・`classify_news_with_grok_search()`の両方に適用（同一バグパターンが
  両関数に存在したため横展開）。両関数のGrokプロンプトにも「同一の出来事を報じる複数の
  見出しは1件にまとめる」指示を追加
- 検証: pytest 110件全パス。ダミーデータ（完全一致・大文字小文字違い・前後空白違いの
  3バリエーション＋importance=なし）で重複排除が正しく機能することを確認

✅ [HYPE-BUG-3] 一覧テーブル「推奨」列のソートが機能していない（2026-06-21 完了）
- 原因: `docs/value-monitor/hypecore/index.html`のソート比較関数が、文字列以外を一律
  `av-bv`で数値減算していた。`rec`列のみ`{cat,text}`オブジェクトを格納しており、
  オブジェクト同士の減算は常に`NaN`になるため`sort()`が実質無効化されていた
- 修正: `REC_ORDER={buy:0,hold:1,watch:2,sell:3}`を新設し、`sortCol==='rec'`の場合は
  投資判断の優先順位（強い推奨が上位）でcatを比較する専用分岐を追加
- `getRec()`が返す`cat`値はbuy/hold/sell/watchの4種のみであることをコードレビューで確認済み
  （該当4分岐＋デフォルトのwatchフォールバックのみで、他のcat値は存在しない）
- 他列（ticker/lc/stage/phase/price/piv/revyoy/rule40/ma200/peak）のソートロジックは
  変更なし。Pythonでの比較関数シミュレーションで昇順/降順とも正しい並び替えを確認済み
  （ブラウザ実機確認は環境制約により省略）

---

## 2026-06-20

✅ [HYPE-BUG-1] 「成長期」セクションの本文が黒文字で読めない（2026-06-20 完了）
- 原因: `docs/value-monitor/hypecore/detail.html`の`.narrative-toggle`（button要素）に
  `color`未指定。button要素は祖先のcolorを自動継承しないブラウザ仕様のため、
  子要素`.narrative-toggle-headline`（同じく色指定漏れ）がUAデフォルトの黒系文字色になり、
  暗色背景（`var(--sur2)`）とのコントラスト不足で読めなくなっていた
- 修正: `.narrative-toggle`に`color:inherit`を追加し、ボタン内の子孫要素全体が
  ページの文字色（`var(--txt)`）を継承するように変更
- `.narrative-toggle-phase`/`.narrative-toggle-arrow`は個別`color`指定済みのため
  本修正による影響なし（直接指定が継承より優先されるため）
- 横展開確認: 同パターン（button自体にもcolor未指定）を他ページの主要button class
  （`.cond-toggle`/`.low-toggle`/`.type-btn`/`.tab`/`.filter-btn`×2/`.chart-btn`）で
  簡易grep確認したが該当なし。いずれもbutton自体にcolor明示済みで安全

✅ [MACRO-BUG-1] RECESSION RISK SCOREとAI Weekly Commentaryのスコア不一致（2026-06-20 完了）
- 原因①（本質）: `index.html`の過去時点再構築（`computeScoreAsOf`/`latestDataDateBefore`）が
  `release_date`のみでフィルタしており、後日`05_events.csv`にバックフィルされたデータ
  （release_dateは過去日付だが実際の取込みは後日）が過去時点表示に先読み混入していた
  （look-ahead bias）。6/13時点のPhilly Fed指数が好例：当時の実値は-0.4だったが、
  6/19に取り込まれた最新値10.3が「6/13時点」の計算に紛れ込み、スコアが37→27に変動
- 修正①: `IND_INDEX`に`updatedMs`（データの実取込み時刻）を追加し、新設の
  `idxLatestKnownAsOf()`で`dateMs<=対象日 かつ updatedMs<=対象日`の両方を要求する
  方式に変更。`latestActualAsOf()`/`latestDataDateBefore()`をこれに切替え。
  現在時点表示（`renderPhaseGauge()`）は対象外（最新の改訂後データを見せるのが正しいため）
- 原因②（副次）: `05_main.py` `_compute_current_score()`にPhilly Fed/Initial Claimsの
  トレンド補正（±10pt）が欠落しており、「renderPhaseGaugeと同一ロジック」というコメントが
  実態と乖離していた
- 修正②: トレンド補正をPython側にも追加し、JS `renderPhaseGauge()`と完全一致させた
- 検証: look-ahead bias単体修正後、6/13時点の再計算は凍結値37と完全一致を確認。
  トレンド補正も同時適用すると38（Philly Fedの正しいトレンド加点+10が反映されるため、
  1pt上振れは想定通り・バグではない）。現在時点のメイン画面スコアは27のまま不変を確認
- 残課題: `computeScoreAsOf()`はlerp（連続補間）方式、Pythonはstep+trend（離散閾値）方式と
  根本的に異なる計算式のため、別途ARCH-MATRIX-DUP-1的な一本化課題として残る可能性あり
  （本対応のスコープ外、未着手）

✅ [ARCH-SCORE-SYNC-1] TANUKI SCORE判定ロジックの一本化（根本解決・2026-06-20 完了）
- Python（pipeline.py）/JS（tanuki_score/index.html）/daily_pick.pyの3箇所に
  分散していた独自分類実装（calcFunda/calcTiming/classify相当）を全廃し、
  pipeline.pyが計算する6分類（BUY/WATCH/HOLD/GROWTH_PREMIUM/TRIM/SELL/PASS）
  をlatest.jsonに一本化。JS/daily_pick.pyはその値をそのまま表示・選定に使う
  構成に変更（4段階でコミット: pipeline.py→index.html→daily_pick.py→workflow yml）
- pipeline.pyに不足していたsellTech条件（技術的SELL判定）・timing_score・
  matrix位置情報・sell_reason構造化フラグを新規追加。JS側にしかなかった
  ロジックの欠落を解消し、Matrix④のFCFマージン定義も実績値に統一
- daily_pick.pyのSELL/TRIM/PASS除外ロジックを追加し、SELL判定銘柄が
  「特選銘柄」として強気寄りラベルで表示される問題を解消（ダミーデータで
  SELL非選出を実証）
- TANUKI_Score_Update.ymlをworkflow_runトリガーに変更し、daily_pick.pyが
  pipeline.py完了前に古いデータを参照する実行順序逆転リスク（実測で
  cron遅延2〜4時間を確認）を解消。土日は独立cronで現状の毎日実行を維持
- pytest 110件全パス。残課題: Stage1コミット時点でNVDA以外の95銘柄は
  新フィールド（timing_score等）未反映のため、次回平日pipeline実行
  （月曜23:05 JST想定）またはマニュアル全銘柄再生成で解消する

✅ [RICE-THRESHOLD-1] RICE閾値・マトリクス表示改善（2026-06-20 完了）
- 旧閾値2.0（理論的根拠なし）を理論値ベース（RICE<1.0=低効率/1.0〜3.0=中効率/
  RICE>=3.0=高効率）に統一。対象: tanuki_score/index.html・stock.html・
  pipeline.py（report.txt生成部）の計4箇所
- 両マトリクス（tanuki_score「②RICE×乖離率」・stock.html「①投資効率系」）の
  Y軸を対数軸化し、NVDA等の外れ値による中央値帯の圧縮（旧表示で下から
  7.5〜15.7%に圧縮）を解消
- RICE<=0（計算不能・マイナス）は対数軸でプロット不可なため下端に▼で別枠表示
- 判定ロジック（_compute_tanuki_score）は変更せず表示のみ対応。pytest 110件
  全パス、report_consistency_check.py NG=0、全96銘柄でBUY/TRIM/WATCH等判定が
  変更前後で完全一致を確認済み（commit bc9c1dc71）
- 検証過程で判明した別課題（TANUKI SCORE判定ロジックがRICEをほぼ参照して
  いない）はARCH-SCORE-SYNC-1の関連事実としてBACKLOG.mdに残置・別タスク化

---

## 2026-06-19

✅ [HOME-FIX-1] 「Gemini API」誤記の修正（2026-06-19 完了）
- HOME画面FEATURESセクション「AI POWERED」カードの説明文に
  `Grok API / Gemini API` という併記が残存していた
- GeminiはGrokに移行済みのため `Grok API` のみに修正
- 対象: docs/index.html（229行目）

---

## 2026-06-17

✅ [BUG-INSIDER-1] インサイダー取引データ取得バグ修正（2026-06-17 完了）
- data_fetcher.py の Form4 XML取得が `form4.xml` 固定パスで提出者依存のファイル名
  （wk-form4_xxx.xml等）に404、85/96銘柄が buy=0/sell=0 の誤表示になっていた
- `filings.recent.primaryDocument` の実ファイル名（basename）を使う方式に修正。
  PLTR sell=46 / NVDA sell=40 / TSLA sell=33 / AAPL sell=13(対照・変化なし) を実機検証
- 修正後 0/0 表示は85→14銘柄に減少。report_consistency_check.py NG=0確認後コミット

✅ [BUG-TTM-Q4DUP-1] ttm_calculator.py implied-Q4 二重計上バグ修正（2026-06-17 完了）
- `_build_q4_quarterly_entries()` に既存end日付チェックを追加（financial_trend_calculator.py
  の実証済み重複排除パターンを適用）。テスト4件追加（tests/test_ttm_calculator.py）
- 全97銘柄でbefore/after差分確認: NetIncome/Revenue等87銘柄で重複混入を検出、
  うち8件（IONQ 3.84倍等）が1.5倍以上の乖離・3件（IOT/SPIR/SITM）が符号反転
- update.py→pipeline.py全銘柄再生成、report_consistency_check.py NG=0確認後コミット

✅ [BUG-DUPONT-1] DuPont分解レビュー由来の4改善（2026-06-17 完了）
- 一過性NI集中チェック（reliability=LOW・19銘柄該当）・dupont_bs_period追加・
  表示バッジ（|ROE|>100%等）・極小売上除外（$10M閾値、該当0件）
- 残課題はTANUKI-ROE-3としてBACKLOG.mdに記録（テスト追加・閾値再検証）

✅ [TANUKI-ROE-3] DuPont売上閾値引き上げ＋テスト追加（2026-06-17 完了）
- 極小売上除外の閾値を $10M → $15M に引き上げ。QBTS（TTM Revenue=$12.4M）が除外対象に
  （変更前: net_margin=-2957%等の極端値表示 → 変更後: excluded=true）
- tests/test_pipeline_logic.py にDuPontユニットテスト7件追加
  （正常計算・Equity除外・売上閾値境界値・reliability=LOW判定・極端ROE計算）
- pytest 119件全パス、report_consistency_check.py NG=0確認後コミット

## 2026-06-16

✅ [REPORT-4] 既知リスクイベント表示（2026-06-16 完了）
- risk_fetcher.py 新規作成: Grok API (grok-3) 英語プロンプトで継続中リスクを最大3件取得
- pipeline.py 統合: --skip-risk フラグ追加、cik_lookup.csv から会社名取得
- stock.html: 既知リスクイベントセクション（高/中/低 バッジ、色分け）
- impactNorm() で英語(high/mid/low)・日本語(高/中/低)両対応

✅ [REPORT-1] DCF感応度分析表示（2026-06-16 完了）
- stock.htmlに割引率Rm(8-12%)×成長率(base±5%/±2%/base)の5×5感応度テーブル追加
- 現在株価超=緑・未満=赤の色分け、現在パラメータセルを太枠ハイライト
- JS側計算のみ・バックエンド変更なし

✅ [REPORT-5] データタイムスタンプ表示（2026-06-16 完了）
- stock.html フッター直上に財務基準日・生成日・次回決算・インサイダー最終日を1行表示
- バックエンド変更なし・既存フィールド（fcf_ttm_end/calculation_date等）を活用

✅ [HYPE-2] HypeCoreヒストリカルパーセンタイル表示（2026-06-16 完了）
- poc.jsonの月次30件からexpectation_scoreのパーセンタイルをJS側で計算
- stock.htmlのMATRIX×HYPEバッジ直下に「現在値 | 過去30ヶ月中XX%ile」を追加
- 色分け: 80%ile以上=赤/50-79%=オレンジ/20-49%=グレー/20%未満=緑

✅ [REPORT-3] インサイダー取引履歴表示（2026-06-16 完了）
- SEC EDGAR Form4 XML解析で直近90日の買い/売り件数・純方向を取得
- stock.htmlにインサイダー1行カード追加（Buy優勢=緑/Sell優勢=赤/中立=グレー）
- report.txt Insider_Activity行追加

✅ [REPORT-2] アナリスト目標株価レンジ表示（2026-06-16 完了）
- data_fetcher.py/core_calculator.py/pipeline.py にアナリスト目標株価6フィールド追加
- stock.html に中央値・レンジ・推奨・vs IV乖離率の3列カード追加
- report.txt Analyst_Consensus行を中央値/レンジ/件数/vs IV形式に拡充

✅ [TANUKI-ROE-1] デュポン分解ROE分析（TANUKI SCOREに追加）（2026-06-16 完了）
- normalizer.py/quarterly.py/ttm_calculator.py に TotalAssets追加・全銘柄update.py再実行
- pipeline.py にDuPont計算ブロック追加（88/96銘柄・負債超過8銘柄除外）
- tanuki_score/index.html にROE降順・折りたたみパネル追加
- 業種平均比較・潜在ROE試算は[TANUKI-ROE-2]としてBACKLOGに新規追加

✅ [SCORE-1] RICE × VALUATION MATRIX（2026-06-16 完了）
- TANUKI SCORE に SVG 散布図セクション「② RICE × 乖離率マトリクス」を追加
- X軸: 乖離率（+300%クランプ、超過銘柄は▶マーカー＋注記表示）/ Y軸: RICEスコア（上限10クランプ）
- 負RICE銘柄除外・4象限色分け・ホバーtip・クリックで stock.html 遷移

✅ [REVIEW-1 #4] LYFT・MRVL TANUKI VALUATION 再生成（2026-06-16 完了）
- DTA補正（BUG-LYFT-EPS-1）適用後の再生成。LYFT IV=-$0.93 / MRVL IV=$138.75(-55.1%)

---

## 2026-06-15

✅ [BUG-LYFT-EPS-1] DTA（繰延税金資産）認識による adj_eps 異常高値（2026-06-15 完了）
- 対象: LYFT Q4 2025（GAAP NI $2.755B、他四半期 $23M〜$120M）、MRVL は DTA 非該当と確定
- 根本原因: `IncomeTaxExpenseBenefit` に大規模負値（-$2,897M）が発生するが既存の `tax_one_time` タグでは捕捉不可
- 修正: `pipeline.py` に `apply_dta_adjustments()` を追加。Type-A（pretax≤0かつNI>0）/ Type-B（NI>pretax×3）の2パターンを検出し、正常四半期の税費用中央値で補正
- 検証: LYFT Q4 adj_eps $6.5964 → **-$0.3469** ✓ / MRVL tax=+$314M → DTA非該当・正常処理 ✓

✅ [BUG-SCCO-CIK-1] SCCO CIK誤登録＋ProfitLoss未対応によるEPS異常値（2026-06-15 完了）
- **根本原因（二重）**:
  1. cik_lookup.csv に誤CIK 0000077360（=PENTAIR plc、全く別会社）が登録 → 0001001838（Southern Copper Corp）に修正
  2. SCCO は 2012年以降 NetIncomeLoss を申告せず ProfitLoss タグに移行。EPS Analyzer にフォールバックなし → extract_key_facts.py に ProfitLoss 追加、タグ選択ロジックを「最初に見つかったタグ」→「最新データを持つタグ優先」に変更
- **修正ファイル**: config/cik_lookup.csv + src/value/adjusted_eps_analyzer/extract_key_facts.py
- **検証**: Q1 2026 gaap_eps=$1.9252, diluted_shares=821,700,000, net_income=$1,581,900,000 ✓

✅ [TANUKI-SEG-1] LMT・VRT segment_config FY2025更新（2026-06-15 完了）
- **LMT FY2025**: Aeronautics 40%/0.05, MFC 19%(+1%)/0.12(+0.02), RMS 23%(-1%)/0.03(-0.03), Space 18%/0.04(+0.01)
  - MFC: +13.9% YoY（ミサイル需要高）→ growth 0.10→0.12 に引き上げ
  - RMS: +0.3% YoY（ほぼ横ばい）→ growth 0.06→0.03 に引き下げ
- **VRT FY2025**: Americas 62%(+6pt)/0.22, Asia Pacific 20%(-2pt)/0.15, EMEA 18%(-4pt)/0.13
  - Americas: +41.9% YoY（AI データセンター需要急増）→ weight 0.56→0.62、growth 0.15→0.22
  - APAC: +17.5% YoY → weight 0.22→0.20、growth 0.13→0.15
  - EMEA: +1.7% YoY（欧州不振）→ weight 0.22→0.18、growth 0.13 維持
- 出典: LMT Q4 2025 IR リリース（2026-01-29）、VRT Q4 2025 IR リリース（2026-02-11）

✅ [BUG-NOW-SPLIT-1] NOW 株式分割未対応修正（2026-06-15 完了）
- ServiceNow 2025-12-18 5:1分割でQ2/Q3 FY2025の株数が分割前（~209M）のまま残存
- `config/split_history.yaml`（新規）+ `pipeline.py` に `apply_split_adjustments()` を実装
- threshold = post_split_avg / ratio × 1.5 で補正済み四半期（Q1 FY2025など）を誤補正しない
- TTM adj_eps $9.75 → 正常値 ~$3.28 に修正・Adjusted_EPS_PER 10.5x → 31.2x に修正
- 次回 Adjusted_EPS_Analyzer パイプライン実行で quarterly.json が再生成される

✅ [ARCH-CHECK-1] consistency_check をパイプライン出口ゲート化（2026-06-15 完了）
- `report_consistency_check.py` に `--fail-on-ng` / `--ticker` / `--quiet` オプションを argparse で追加
- SEC_Data_Update / TANUKI_VALUATION_Update / Adjusted_Eps_Analyzer_update / Stonks_Silo_Update の4本に `Consistency Check Gate` ステップを挿入（git push の直前）
- NG>0 かつ `--fail-on-ng` 指定時に exit(1) → Actionsに赤バッジ表示でサイレント失敗を防止

✅ [BUG-EPS-ZERO-1] V/XOM/VZ EPS=$0 修正・株式数フォールバック追加 ✅ 2026-06-15
- **V (Visa)**: WeightedAverageNumberOfDilutedSharesOutstanding が XBRL 10-Q に存在しないため EPS=$0 → yfinance fallback で 20四半期に拡充（ただし Class A 株数 ~1.66B = 稀薄化後 2.07B の過小）
- **XOM**: 同タグ 10-Q 未提供 → EarningsPerShareDiluted 逆算（NI/EPS）で 8四半期分を補完、Q4 は yfinance fallback
- **VZ**: quarterly.json は既に有効（18四半期 valid）、EPS pipeline 再実行で summary.json に反映
- **実装**: `extract_key_facts.py` に 3段フォールバック追加（①EPS逆算 ②Basic株数代用 ③yfinance）
- **required_tags に追加**: `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic`

✅ [BUG-IV-DISP-1] KULR/S/TDY IV表示不整合修正（tapering 未適用バグ） ✅ 2026-06-15
- **根本原因**: `core_calculator.py` の `_calc_ivps_with_wacc` が `dcf_type == "tapering"` 時でも 2段階 DCF に fallthrough → メイン IV がタペリング未適用、シナリオ BASE はタペリング適用で不整合
- **修正**: `_calc_ivps_with_wacc` に `elif dcf_type == "tapering"` ブランチを追加
- **修正**: `_res_rm` 計算ブロックにも tapering ブランチを追加（STEP11 表示の一貫性）
- **効果**: KULR IV $5.57 → $5.63（ScenBASE との差 $1.23 → $0.00）、S $29.50 → $23.65、TDY $517.61 → $596.10

✅ [DCF-DEFAULT-G-1] G=15%デフォルト問題修正（set_growth_override が segment 未設定銘柄に無効だったバグ） ✅ 2026-06-15
- **根本原因**: `segment_config.py` の `get_segment_growth` が `_GROWTH_OVERRIDES` を参照するのは segment_config.json に登録 かつ "General" 単一セグメント銘柄のみ → JNJ/MO/PEP/PM/WMT/VZ 等の未設定銘柄では override が無効
- **修正**: `get_segment_growth` 冒頭に `if ticker in _GROWTH_OVERRIDES: return override` を追加（全銘柄対象）
- **修正**: `pipeline.py` の auto-adjustment ブロックに `finally: clear_growth_override(ticker)` を追加
- **修正**: `pipeline.py` Section 4 表示: `Phase1成長率` を DCF 適用値（推奨成長率）に変更、元成長率を別行表示
- **JNJ**: IV $363.76 → $202.12（G=15%→1.47% で upside +51% → -16.1%）
- **VZ**: G=15%→0.9% で IV 大幅変動

**注記（2026-07-09・STDOUT-JSON-MISMATCH-1発見時）**: 本記録を含む
2026-06-11（BUG-SCAN-FULLSCAN-1 Fix2）以降・recommended_g再計算を
伴うDCF関連の完了記録（SEGMENT-1後半バッチ・BUG-NETDEBT-6・
BUG-IV-DISP-1等）は、STDOUT-JSON-MISMATCH-1（2026-07-09根本修正済み）
と同種のstdout/JSON不一致が起きていた可能性があり、記載された数値が
当時のJSON実値と一致しない場合がある。現在の計算結果（最新JSON値）は
本バグ修正後のものであり正確。過去記録の数値は参考情報として扱い、
正確な現在値が必要な場合は都度JSON実値を確認すること。

✅ [FCF-OUTLIER-1] FCF外れ値誤除外修正（DOCN/LITE/VST） ✅ 2026-06-15
- **根本原因**: `analyze_fcf_outlier` が "deviation_large" ルールで `latest_fcf > fcf_5yr_avg`（上方乖離）のケースを一過性コストで「除外」していた。
  一過性コストはFCFを下押しするため、上方乖離が「コスト由来」とするのは矛盾。
- **修正**: `adjustments.py` の `transient_explains` 計算で `is_upward_deviation`（上方乖離）の場合は `False` に強制
  → action が "excluded" → "flagged" に変更
- **DOCN**: FCF base = 4yr avg $86M → 5yr avg $104M（除外撤回）
- **LITE**: FCF base = 4yr avg $49M → 5yr avg $62M（除外撤回）  
- **VST**: FCF base = 4yr avg ? → 5yr avg $1276M（除外撤回）
- テスト: 130/130 pass, consistency_check NG=0

✅ [CHECK-17/18/19] 回帰検知チェック3件を report_consistency_check.py に追加 ✅ 2026-06-15
- **CHECK-17 [NG]**: 直近3年の全四半期 adj_eps=gaap_eps=0.0 → BUG-EPS-ZERO-1 回帰検知
- **CHECK-18 [WARN]**: recommended_g あり & phase1_growth_auto_adjusted=False & source≠segment_weighted & rate≈15% → DCF-DEFAULT-G-1 回帰検知
- **CHECK-19 [NG]**: 直近3年の四半期で diluted_shares=0 かつ NI≠0 → 株式数取得失敗回帰検知
- **日付フィルタ**: 2022-01-01以降のみ対象（旧上場前・スピンオフ前データの偽陽性を除外）
- **テスト結果**: 96銘柄 NG=0 / 警告=3件（既知: ELF PS乖離, LMT/VRT segment陳腐化）

✅ [ROE-ZERO-1] ROE=0% 誤表示修正（PM 等の純資産マイナス銘柄） ✅ 2026-06-15
- **根本原因**: `reader.py` の `get_roe_avg_detail` がすべての年で equity≤0 の場合に `(0.0, 0, False)` を返す → 0%として表示
- **修正**: `roe_list` が空の場合は `(None, 0, False)` を返すよう変更
- **修正**: `data_fetcher.py` の print 文で None を `N/A (負債超過)` と表示
- **修正**: `core_calculator.py` で `roe_avg or 0.0` として alpha 計算に渡す
- **修正**: `validator.py` の 2 箇所で `c.get("roe_10yr_avg") or c.get("roe_used") or 0.0` に変更
- **修正**: `pipeline.py` で `roe_years_used == 0` の場合に `"ROE = N/A (負債超過)"` を表示
- **PM**: 旧 `ROE_avg (?yr) = 0.0%` → 新 `ROE = N/A (負債超過)` ✅
- テスト: 130/130 pass, consistency_check NG=0

✅ [ALPHA-SECTOR-1] VZ Alpha=1.0 過大評価修正（Telecom セクター上限 cap 追加） ✅ 2026-06-15
- **根本原因**: `maturity_config.json` に Communication Services alpha_cap=1.0 が設定されているが Telecom 向けの業種別上限が未設定
  → VZ ROE=30.2% × 0.60 / 0.10 × 0.7 = 1.27 → cap(1.0) → alpha=1.0（過大）
- **修正**: `maturity_config.json` に `_industry_alpha_caps: {"Telecom Services": 0.4}` を追加
- **修正**: `core_calculator.py` の alpha_cap 決定ロジックに industry チェックを追加（業種 > セクターの優先順）
- **VZ**: alpha 1.0 → 0.4（`α: 1.269 → cap(0.4) → 0.400`）
- **VZ IV**: alpha 1.0 → 0.4 でより保守的な IV に変更
- テスト: 130/130 pass, consistency_check NG=0

✅ [AUDIT-SHARES-1] audit.py に yfinance/SEC 株数乖離チェック(5x閾値)を追加 ✅ 2026-06-15
- **実装**: `audit_ticker` に株数乖離チェックを追加（EPS quarterly.json latest vs latest.json components.diluted_shares）
- **閾値**: 5倍以上の乖離で WARN 出力
- **検出例**: SCCO 株数乖離 5.1x（EPS=163.7M vs DCF=834.3M）→ データソース不一致疑い

## 2026-06-14

✅ [MP-DIV-UNIFY] 乖離計算ソースをCNN F&Gに統一（2026-06-14 完了）
- 原因: 乖離=Tech Pulse - feargreedchart.com(~57)で、画面表示のCNN F&G(~34)と不一致
- 修正: div_value = tech_pulse.score - fear_greed.score(CNN) → 乖離+15→+38に正常化
- _get_tp_signal のfg_score<30判定もCNNスコアに更新
- z-score履歴はdivergence.value優先参照(前コミット修正済み)のため次回実行からCNNベースで再計算

✅ [MP-DIV-ZSCORE-FIX] divergence z-score データソース不整合修正（2026-06-14 完了）
- 原因: `_load_div_history` が fear_greed.score（CNN, ~34）を使って履歴構築していたが、
  当日 div_value は fg_score_tech（feargreedchart.com, ~57）から計算 → ソース不一致
- 影響: 誤ったz-score（-0.11 ≒ 平均以下と誤判断 vs 正しくは +0.82 = 平均より上）
- 修正: 保存済み tech_pulse.divergence.value を優先使用 / 旧エントリは components.fg_score で再計算
- 次回 collect_and_send.py 実行からz-scoreが正確に算出される

✅ [MP-REGIME-LABEL] REGIME判定ソース明示（2026-06-14 完了）
- fed_context に regime_source 列を追加（Grok成功時: "FOMC声明分析（Grok）" / fallback時: "DGS1数値ベース"）
- index.html の REGIME セルにサブラベルとして判定ソースを表示
- 旧CSVは ai_reason から後付け推定して補完（3月:DGS1ベース / 4-6月:Grok）
- _fallback_regime の文言を "ZQ先物が…" → "DGS1ベースで…" に更新

✅ [MP-1YEFF-FIX] 1Y EXPECTED FF 表示値バグ修正（2026-06-14 完了）
- 原因: ラベルが "FRED T1YFF" と表示されていたが T1YFF は DGS1-FEDFUNDS スプレッドであり絶対金利ではない
- 修正: DGS1（1年国債利回り）を直接使用 → 表示値 3.62% → 3.85% / IMPLIED CUTS +0.02 → -0.90回
- ZQ=F term premium 補正ロジックを廃止しシンプル化
- サブラベルを「正値=利下げ織り込み / 負値=利上げ・高止まり織り込み」に更新
- 解釈: DGS1(3.85%) > FF(3.625%) = 市場は高金利継続を織り込み中（-0.90 = BALANCED判定）

✅ [MP-DISPLAY-FIX] Macro Pulse 表示バグ3件修正・データ取得ロジック改善（2026-06-14 完了）
- 修正1: NET LIQUIDITY / HY Spread の "++" 二重符号 → chgHtml の sign と fmt lambda が二重加算していた
- 修正2 (コードではなくデータ問題): refresh_monthly_indicators の obs_to_release_lag 導入
  - obs_date+60日の広すぎるウィンドウで既存スロットを飛ばし未来スロットに誤マッピングする問題を修正
  - NFP 2026-06-05 (5月雇用統計) / Building Permits 2026-05-19 を正常取得
  - Recent Signals の最新表示が 5/15 → 6/5 に改善
  - Michigan CS / Mich Inf 1Y は FRED データが April 止まり（FRED 側ラグ、許容）
- 修正3: AI Weekly Commentary ヘッダー "Gemini 2.5 Flash" → "GROK-3-MINI"

✅ [MP-HISTORY-FIX] Market Pulse 過去データ異常値修正・バリデーション追加（2026-06-14 完了）
- 原因: VIX9D列追加時のCSVヘッダズレでsentiment_scoreに誤値（-2.66〜1.41）が42件混入
- 修正: market_data.json 42件再計算・91件→58件に重複集約
- 再発防止: collect_and_send.py に sentiment_score の 0〜100 範囲チェック追加

✅ [MP-PRED-FIX] センチメント予測リターン異常値修正（2026-06-14 完了）
- 原因: 同一列ズレバグによりS&P500.valueに0.08等の誤値 → getAvgRetが+9億%を出力
- 修正: 5/21-6/7の17エントリ全indicators再構築・index.htmlに防衛チェック追加
- Tech Pulse 5/21-6/5欠落はCSV未保存のため復元不可（許容）

---

## 2026-06-13 完了

### ✅ STALE-CHECK-1 フォローアップ (2026-06-13 完了): 11銘柄ステールデータ更新
- **対象**: FICO/ZETA/BBAI/CELH/COHR/CRWV/RCAT/CPRT/ZS/HQY/RBRK（4〜5月決算後未更新）
- **手順**: update.py → pipeline.py → audit.py → consistency_check
- **結果**: 全11銘柄 SEC 再取得完了（11/11）、pipeline PASS=9 WARN=2 FAIL=0 ERROR=0
  - WARN=2 は FICO/CPRT の formula_verification（既存）
  - WARN-8（ステール警告）: 全消去確認済み
- **IV 更新後**: FICO=$928/ZETA=$30.4/BBAI=$1.79/CELH=$21.2/COHR=$39.1/CRWV=$159.8/RCAT=$3.49/CPRT=$49.3/ZS=$141.9/HQY=$105.8/RBRK=$135.7
- **audit.py**: 正常77銘柄・警告2件（CART/JOBY 既存 Revenue None）NG=0
- **consistency_check**: NG=0 全銘柄整合（残警告: ELF WARN-10、LMT/VRT WARN-9 は既存）
- **pytest**: 108件全パス

### ✅ EPS-PER-TTM-1 (2026-06-13 完了): 調整後PERをGAAPと同一TTM期に統一
- **根本課題**: `_calc_adjusted_per` が `annual.json years[0].adjusted_eps`（年次FY）を分母に使うため、GAAP PER（yfinance trailingPE = TTM）と期間不一致。成長株で ADJ>GAAP 逆転（NVDA: 48.3x vs 31.4x）
- **修正**: `core_calculator._calc_adjusted_per` を `quarterly.json` 直近4Q `adjusted_eps` 合計（TTM）に変更。4Q未満は None（年次フォールバック禁止）
- **文言**: report.txt 注記「年次EPSベース」→「TTM調整後EPS: $x.xxxx」、Definition に「same trailing 12M period」明記
- **検証**: NVDA 48.3x → 30.3x（Delta -1.1x）、46銘柄 ADJ/GAAP 非対称を解消
- pytest: 105件全パス / 全78銘柄再生成 FAIL=0

### ✅ ANNUAL-FY-1 (2026-06-13 完了): aggregate_annualを会計年度ベース集計に修正（IV影響あり）
- **根本課題**: `aggregate_annual`（pipeline.py）が `filing_date[:4]` でグループ化するため、非12月FY企業で FY跨ぎ混合が発生。例: NVDA annual.json year=2025 = FY2025Q4+FY2026Q1-Q3（混合）→ 誤FCF推定値を経由してIVに影響
- **修正**: `fiscal_year` フィールドベースに変更。フィールド未設定の場合は `filing_date[:4]` にフォールバック
- **PARSER-1との関係**: 独立した修正。parser.py は期末日年キー、aggregate_annual は会計年度キーで別レイヤー
- **影響**: 20銘柄の annual.json 更新 → `estimate_fcf_from_eps` 経由でIVに波及
  - 大型: NVDA +18% ($201→$238) / MSFT -12% ($621→$546) / AVAV +93% ($54→$105)
  - IOT: applied=False→True（FY2026 adj_ni +$265.8M、本物の黒字化）
  - COHR/LITE/RBRK/S: applied=False のまま（IV変化なし）
- **スポットチェック**: NVDA FY2026=$5.12/AAPL FY2025=$8.11/MSFT FY2025=$15.44（10-K通年と一致）
- **consistency_check追加**: TestAnnualFYConsistency（3件）- 年跨ぎ混合の恒久ガード
- **ARCH-DATA-1注記**: 年度判定が parser.py / extract_key_facts.py / aggregate_annual の3箇所に分散。共通関数化は次の前倒し対象
- pytest: 108件全パス / 全78銘柄再生成 FAIL=0

### ✅ PARSER-1 (2026-06-13 完了): 年次キーを fy→end_date年 に変更
- **根本課題**: FCX の FY2025 10-K で `fy=2025, end='2024-12-31'` エントリが混入し、`annual_2024.json` が生成されない年度ズレ
- **修正1**: `_extract_values` の年次辞書キーを `fy` → `int(end_date[:4])` に変更（end_year ベース）
- **副作用**: INTU（FY end=7月31日）で FY2020 10-K 内の Q1 比較値（`fy=2020, end='2019-10-31', val=$1.16B`）が `end_year=2019` として通年値（$6.78B）を上書きする regression が発生
- **修正2**: `annual_exact_match` 辞書を追加し、`fy==end_year`（exact match）が存在する年度は non-exact エントリによる上書きを禁止する一般解で解決
- **波及検証**: 差分 150件はすべて non-December 決算企業（AAPL/MSFT/NVDA/CRM/ELF/HQY/COHR 等）の FY2019 以前の revenue/NI が正しい FYE 値へ修正されたもので、潜在バグ群の一括解消
- **IV への影響**: 直近5年 FCF 系列は不変のため IV/FCF_Base/CAGR への波及ゼロ
- **検証**: 全 78 銘柄再パース成功（FAIL=0）、exact matchなし競合 234件の tie-break（最新 end_date 優先）は意図通り動作確認済み

### ✅ REPORT-6 (2026-06-13 完了): DCF透明性強化
- `pipeline.py` の report.txt [3]TANUKI VALUATIONに`DCF_FCF_PV`/`DCF_TV_PV`を追加（全銘柄）
- FCF外れ値除外銘柄のみ`DCF_FCF_Base_Detail`/`DCF_FCF_Base_Excluded`を追加出力
- 3段階DCF(three_stage)は`pv_phase1+pv_phase2`、2段階は`pv_high_growth`でFCF現在価値を算出
- pytest: 122件全パス / 全78銘柄再生成: FAIL=0 / NG=0

### ✅ SEGMENT-1 後半バッチ完了 (2026-06-13 完了): LLY/LMT/MRVL/AMAT/VRT/COHR/LITE/CSGP/BSY/ALAB/ELF/AVAV（12銘柄）
- **単一セグメント確認・修正不要（LLY型）**: LLY / MRVL / BSY / ALAB / ELF（5銘柄）
  - MRVL補足: 5エンドマーケット = disaggregated revenue（ASC 606）≠ ASC 280 formal segment。FY2026から2カテゴリ報告へ変更予定だが従来通り単一
- **複数セグメント設定（LMT型）・IV変化一覧**:

| Ticker | セグメント数 | 設定内容 | IV before | IV after | 変化率 |
|--------|------------|---------|-----------|----------|--------|
| LMT | 4 | Aeronautics(40%/5%)/MFC(18%/10%)/RMS(24%/6%)/Space(18%/3%) | $309 | $347 | +12.3% |
| AMAT | 3 | Semiconductor_Systems(74%/8%)/Applied_Global_Services(23%/6%)/Display(3%/2%) | $274 | $253 | -7.5% |
| VRT | 3 | Americas(56%/15%)/Asia_Pacific(22%/13%)/EMEA(22%/13%) | $129 | $101 | -21.0% |
| COHR | 3 | Networking(59%/20%)/Lasers(25%/10%)/Materials(16%/6%) FY2025 | $90 | $39 | -56.5% |
| LITE | 2 | Cloud_Networking(86%/20%)/Industrial_Tech(14%/4%) FY2025 | $60 | $27 | -56.0% |
| CSGP | 2 | North_America(95%/10%)/International(5%/20%) FY2025 | $13.6 | $11.78 | -13.6% |
| AVAV | 3 | Uncrewed_Systems(40%/12%)/Loitering_Munitions(50%/20%)/MacCready_Works(10%/15%) | $135.53 | $94.23 | -30.5% |

- **growth_floor bypass**: segment_configured=True の場合 recommended_g サニティ回避（weighted_growth 直接採用）
- **COHR/LITE の大幅低下**: FCF base が超小型（$31.8M/$62.1M）のためΔgrowth が IV に直接増幅
- **weighted_growth 計算**: sum(weight_i × g_i)。AVAV weighted_g = 16.3%（before recommended_g 25.64%）
- CSGP 補足: net_debt/shares_used=None は全銘柄共通の latest.json 仕様（report.txt の値は正常）
- pytest: 108件全パス / 全銘柄再生成 FAIL=0

### ✅ SEGMENT-1 VST/FCX/SCCO/CEG/KO (2026-06-13 完了): filing準拠セグメント修正
- VST: Texas_ERCOT/East_Nuclear/Retail/West（地理別、wg 7.2%→7.85%、IV $31.36→$33.69）
- FCX: Indonesia/North_America/South_America（Gold独立セグ削除、wg 8.3%→6.4%、IV $3.95→$3.34）
- SCCO: Peruvian_Operations/Mexican_Operations（OtherMetals削除、wg 8.6%→8.45%、IV $17.48→$17.36）
- CEG: Mid_Atlantic/Midwest/ERCOT/New_York/Other_Retail（Calpine統合後、wg 10.3%→9.65%、IV $52.48→$49.54）
- KO: North_America_NAOU/International/Global_Ventures（wg 5.0%→4.7%、IV $46.39→$45.71）
- 残タスク: LLY/LMT/MRVL/AMAT/VRT/COHR/LITE/CSGP/BSY/ALAB/ELF/AVAV（12銘柄）

### ✅ BUG-NETDEBT-6 (2026-06-13 完了): 同一時点原則による Net Debt 計算修正
> ⚠️ ID注記: 本項は当初 BUG-NETDEBT-4 と命名していたが、2026-06-10 完了分に
> 同一 ID（レポート Net Debt 内訳表示）が既存のため BUG-NETDEBT-6 に改番（NETDEBT-5まで使用済み）。
- **原因1**: BUG-NETDEBT-1でCashは最新quarterly上書きされるが、Total_Debtは年次のまま（時点混在）。
  さらに表示値とequity bridge投入値が別物（表示$8.10B vs engine net_cash -$5.26B）という二重の不整合
- **原因2**: CEG等は10-QでLTDebtをLongTermDebtNoncurrentタグで報告するが、quarterly.pyがLongTermDebt(annual tag)のみ参照してNone扱い
- **修正**: quarterly.py に `LongTermDebtNoncurrent` を `_FIELD_FALLBACKS["LTDebt"]` に追加
- **修正**: reader.py + pipeline.py に同一時点原則ブロック実装（quarterly に Cash+LTDebt が揃う場合に全BS項目を同一filingから参照）
- **修正**: pipeline.py に BUG-NETDEBT-2 補完復活（annual lt_debt=0 かつ quarterly LTDebt未取得の場合にnormalized LTDebtで補完）
- **条件設計**: `_q_lt is not None` が必須ゲート。`_q_lt=None`（パース失敗）時は cash-only → BUG-NETDEBT-2 でnormalized補完
- **影響銘柄 (Net_Debt が実質変化)**:
  - CEG: Net_Debt $+8.10B → **+$21.30B**（Calpine買収負債$16.99B Q1 2026反映）、IV $97.39 → **$52.48**
    （乖離 -61% → -79%。ΔIV -$44.91/sh = 100% Net Debt起因: Cash -$7.96 / LTDebt -$27.29 / STDebt -$9.67、FCFベース寄与ゼロ）
  - KO: Net_Debt **-$9.08B → +$27.42B**（annual lt=None → normalized $36.5B補完）
  - ELF: Net_Debt -$0.20B → **+$0.65B**（term loan $0.85B）
  - SOFI: Net_Debt -$3.40B → **+$2.08B**（normalized LTDebt $5.49B、2022データ※）
  - ZS: Net_Debt -$1.20B → **-$0.05B**（convertible notes $1.15B）
  - JOBY: Net_Debt -$2.47B → **-$1.77B**（Toyota financing $0.70B）
  - ※SOFI: 2022-12-31以降の10-Qに標準LTDebtタグなし（銀行移行後の報告変更）。IV計算パスと表示パスは一致。
- **display改善追加**: DCF_FCF_Base行、Net_Debt_Period行、dilution乖離フラグ、beta staleness警告（90日超）、株式数表示修正
- 回帰テスト: 100件パス（変更なし）

### ✅ REPORT-6拡張: DCF再現性の完全確立 (2026-06-13 完了)
- 背景: VST時点のREPORT-6（DCF_FCF_PV/TV_PV追加）では、α倍率・equity bridge・採用株数が
  非表示のため外部AIが「IV再現不能」を全メガキャップで誤指摘（MSFT/NVDA/APP/PLTR/TSLA等）。
  PV2項の和だけではα乗算後段が見えず、α≒0の小型株でのみ偶然近似できていた
- 修正: report.txt [3]DCFブロックを「上から足すと必ずIVになる」構造に再構成
  DCF_FCF_PV → DCF_TV_PV → DCF_v0 → Alpha_Premium → DCF_v0_x_alpha
  → RPO_PV → Growth_Option_PV → Equity_Value(−Net_Debt) → Shares_Used(source明記) → Intrinsic_Value
- 優先株がある銘柄（CELH等）はequity bridgeに控除行を追加表示
- 検証: test_iv_formula.py 5件（MSFT/NVDA/CELH/PLTR/TSLA、誤差<$0.01）。IV値自体は不変（表示追加のみ）
- 効果: 外部レビュー最頻出指摘「IV再現不能」を構造的に解消

### ✅ MATRIX-1 (2026-06-13 完了): ROE_avg窓長のreport.txt明示
- 採用案: (b)動的採用+report表示。Matrix象限ロジック・ROE計算自体は不変（低リスク）
- report.txt [2] Key_Metric_Y を `ROE_avg (Nyr, equity>0全年) = XX%` に変更
- 窓長Nyrは銘柄ごとのequity>0年数を動的算出して表示（VST=7yr/CEG=4yr等）
- 効果: 外部AIが「なぜ固定窓長でないか」を誤検出しなくなる（再現性の可視化）
- 補足設計論点（未対応・低優先）: VST ROE_avg(7yr)=10.5% vs 直近3yr≈31% のように
  窓長次第で象限が動く件は表示で可視化済み。固定窓長化(a)は全銘柄IV波及のため見送り

### ✅ STALE-CHECK-1 (2026-06-13 完了): 決算後未更新データの検出
- report_consistency_check に決算日経過後の未更新検出を追加
- 検出11件: FICO/ZETA/BBAI/CELH/COHR/CRWV/RCAT/CPRT/ZS/HQY/RBRK（4〜5月決算後未更新）
- 次回更新サイクルでSEC再取得を実施予定（残タスク）

### ✅ 独自仕様の注記追加 (2026-06-13 完了): 外部AI誤検出の恒久防止
- RICE定義式を実装に一致: `(G × VC_Factor × Q × CF) / WACC`（VC_Factorが式本体から欠落していた注記バグ）
- FCF_Conversion注記: Adj_NI×rate であり OCF→FCF変換率とは別物。高FCFマージン企業で実績FCFを
  下回るのは正常化前提による保守設計と明記
- IV/割引率注記: 高β銘柄でWACC比IVが高めに出るのは市場リスクを意図的に除外した本源価値の設計。
  市場リスク調整後はWACC_CAPM_ReferenceでのIVを併用
- DCF_Reliability=LOW判定（Policy A明文化）: LOW時はBUY/TRIM/HOLD/WATCH→WATCH、SELL/PASS維持。
  IVは参考値、乖離率は表示するが分類には使用しない

## 2026-06-12 完了

### ✅ CHECK-13 / WARN-12修正 (2026-06-12 完了): RICE負値ラベル回帰検知 + 偽陽性除去
- `report_consistency_check.py` に CHECK-13 追加（RICE<0 時 Matrix Label 確認）
- CHECK-12 の `_latest` 変数名バグ修正（正: `latest`）→ WARN-12 が正常検知されるように
- WARN-12 の false positive 除去: quarterly_STI ≈ annual_STI のとき誤検出しないよう `_sti_already_qtr` 条件追加
- 修正後: NG-13 発生 5 件 → 影響 5 銘柄を再生成 → NG=0 確認
- テスト: `TestRiceNegativeLabel` 3 件追加（total: 100 件パス）

### ✅ RICE-3 (2026-06-12 完了): 負 RICE 値の閾値定義明記
- OCF 赤字時に RICE が負値になるが「低効率」と誤表示されていた問題を修正
- `pipeline.py` の rice_efficiency 判定に `< 0 → "N/A (OCF赤字)"` ブランチを追加（4分類化）
- Matrix Label・RICE_Threshold・Interpretation 定義文すべてに `<0=undefined (OCF negative)` を追記
- IONQ 確認: RICE=-0.552 で Label が "N/A (OCF赤字)" に正しく表示されることを確認

### ✅ BUG-NETDEBT-5 (2026-06-12 完了): ST_Invest期ズレ修正(年次→最新四半期)
- **原因**: BUG-NETDEBT-1でCashは最新四半期bs値に上書きされるが、ST_Investはannual年次のまま
  normalized JSONにShortTermInvestmentsフィールドがなく自動更新経路がなかった
- **修正**: pipeline.py の financial_health 計算ブロックに BUG-NETDEBT-5 ブロック追加
  最新 `quarterly_*.json` の `bs.short_term_investments` で上書き（値が0なら年次にフォールバック）
- **影響26銘柄**: IONQ(-$0.18B)、META(-$12.04B)、MSFT(+$18.16B)、GOOGL(+$7.36B)、
  AAPL(-$4.17B)、AMD(-$1.75B)、AMZN(-$5.05B)、JOBY(-$0.42B) 等
  IONQ: Net_Debt -$1.85B → **-$2.03B**（$1,361M→$1,540M、Q1 2026 から）
- **CHECK-12追加**: `report_consistency_check.py` にCash-STI期整合チェック（WARN-12）
  Cash≈四半期値 かつ STI≈年次値 なら期ズレ未修正として警告。26銘柄修正後NG=0確認済み
- 回帰テスト: Section 23 (3件追加、計97件合格)

### ✅ BUG-REV-SPAC-1 / A-2-TTM (2026-06-12 完了): IONQレビュー指摘: FCF_Margin単年異常 / TTM二義性
- **BUG-REV-SPAC-1 (A-1)**: IONQの2022年10-K `Revenues` タグが$1,235M(SPAC調達金)を誤タグ
  正規営業収益 `RevenueFromContractWithCustomerExcludingAssessedTax`=$11.1M と重複
  `merge_all_tags=True` + 同一end_date で先頭タグ `Revenues` が勝ち、FCF_Margin 2022=-4.4% に (正常値は-485%)
  修正: `TICKER_RESTRICTIONS["IONQ"]["revenue_concept"]` で単一タグ固定
  横断スキャン: 全79銘柄に同型バグなし (ASTS/JOBY/RCATは正常高成長)
- **A-2-TTM**: [3]`TTM_Revenue_Growth=201.9%` (実TTM YoY) と
  [4]`TTM15.0%のため中央値モデル適用` (`_trigger_max`=max(phase1_g, CAGR)) が同一`TTM`表記
  修正: [3]→`TTM_YoY_Growth`, [4]中央値→`CAGR_max=XX%`, [4]逓減→`CAGR_max=`/`G入力値=`
  逓減モデルの start_g もCAGR最大値を優先するよう修正 (IONQ: recommended_g 12.5%→55%)
- **CHECK-11追加**: `report_consistency_check.py` に Revenue孤立年チェック(前後両年<5%の孤立異常値)
- 回帰テスト: Section 22 (5件追加、計94件合格)

## 2026-06-11 完了

### ✅ BUG-NETDEBT-2 (2026-06-11 完了): LongTermDebt優先順位修正による二重計上防止
- 原因: `XBRL_MAPPING["long_term_debt"]` の先頭が `LongTermDebt`（current+non-current合計）だった
  `short_term_debt` で `LongTermDebtCurrent` を別途加算するため、current分が二重計上されていた
- 修正: `parser.py` の `long_term_debt` マッピングを `LongTermDebtNoncurrent` 優先に変更
- 影響: 48銘柄の annual.json を再生成、全銘柄の pipeline を再実行
- DOCN 例: Total_Debt $1.62B → $1.30B、Net_Debt $0.88B → $0.55B
- 回帰テスト: `tests/test_pipeline_logic.py` Section 21 (3件追加、計89件合格)

### ✅ SEC-REV-FINTECH-1 (2026-06-11 完了): 金融系銘柄 annual revenue 過小評価の修正
- 原因: `MERGE_ALL_TAGS` 動作で狭義 `RevenueFromContractWithCustomer`($0.62B) が
  広義 `RevenuesNetOfInterestExpense`($3.61B) より先に見つかりrevenuが過小計上
- 修正: `parser.py` に `TICKER_RESTRICTIONS["revenue_concept"]` オーバーライドを実装
  指定タグのみ使用し merge_all=False でシングルタグ取得
- SOFI: FY2024 annual revenue $0.62B → $3.61B 是正
- 回帰テスト: `tests/test_pipeline_logic.py` Section 20 (3件追加)

### ✅ 登録パイプラインWARN清掃 (2026-06-11 完了): WARN 23→10 件
- CSGP/ZS: HypeCore実行によりデータ整備
- BKNG/FCX: `eps=false` 設定（XBRL quarterly NetIncomeLoss データ欠如）
- ASML: IFRS外国企業のため cik_lookup.csv から削除
- 孤立エントリ削除: CRWD/FIG/MDB/PUBM/WEAV (tanuki=false なのにエントリ残存) + REKR/SENS/VUZI
- `registration_validator.py` に `eps_disabled` 除外ロジック追加
- `CLAUDE_CODE_START.md` に EPS analyzer Step 5b / IFRS注意事項 を補強

### ✅ BUG-RPO-1 whitelist構造化 (2026-06-11 完了): RPO適用をwhitelist+比率条件に構造化
- _get_rpo_application_rate に via_whitelist フラグを追加（whitelist登録銘柄は比率チェック免除）
- adjust_rpo に RPO/Revenue < 0.3 の比率ゲートを実装（whitelist以外全員適用）
- exclusion_reason を rpo_adjustment に格納、report.txt の RPO_PV 行に除外理由を表示
- V(ratio=0.11)・BSY(ratio=0.18)が除外、GOOGL/MSCI は維持

### ✅ DCF_Reliability=LOW SCORE丸め (2026-06-11 完了): LOWのとき WATCH に統一
- _compute_tanuki_score にて fcf_floor_applied > 0 の場合 SELL/PASS 以外を WATCH に丸める
- score_comment に「DCF信頼性LOW(実績FCF赤字)のためupside依存判定を抑制→WATCH」を付記
- CRWV: HOLD → WATCH に変更（期待通り）

### ✅ BUG-ROE-NI-1 (2026-06-11 完了): ROE集計でnet_incomeがNoneの年を除外していた問題
- 原因: SEC XBRL旧フォーマット(2015-2019頃)は net_income=None だがeps_diluted×sharesから代替推計可能
- 修正: get_roe_avg_detail() に `eps_diluted × shares_diluted` フォールバックを追加（NI=None時）
- 結果: CAKE 5yr平均ROE 5.2%→13.4% (有効年数 5→10年、COVID赤字年の影響が薄まる)
- 汎用修正: 同様の旧SEC形式を持つ全銘柄に自動適用

### ✅ BUG-FCF-CAGR-SPAN-1 (2026-06-11 完了): FCF CAGR計算の固定3年指数バグ
- 原因: `(fcf_new/fcf_old)**(1/3)` の固定指数が年次データ欠落時に誤ったCAGRを算出
  CAKE: annual_2022.json 欠落 → 実際は4年スパンなのに3年として計算
- 修正: `span = yr_new - yr_old` で実際の年数差を算出し `(1/span)` を使用
- ラベル変更: `FCF_CAGR_3yr` → `FCF_CAGR_{span}yr`（スパン明示）
- 結果: CAKE FCF_CAGR_4yr: +1.5%（旧: FCF_CAGR_3yr: +2.0%）

### ✅ BUG-SCAN-FULLSCAN-1 (2026-06-11 完了): 全79銘柄スキャンによるバグ3件の発見と修正
- **Fix1 (core_calculator.py)**: `scenario_valuations` を `growth_result.source == "segment_weighted"` ゲートなしで全銘柄に計算
  - 旧バグ: segment未設定の15銘柄でBEAR/BULLが $0.00 / Growth=0.0% になっていた
  - 修正: `if growth_result.source == "segment_weighted":` ガードを削除し無条件計算に変更
- **Fix2 (pipeline.py _load_extra_data)**: segment_config.json 未登録銘柄に `segment_configured=False` をセット
  - 旧バグ: 未登録銘柄では `extra.get("segment_configured", True)` が True を返し `_is_seg_unconfigured=False` になっていた
  - 修正: `not segs` のとき `result["segment_configured"] = False` を追加
- **Fix3 (pipeline.py _generate_report)**: Matrix② 定義文の ROE 年数を `roe_years_used` から動的生成
  - 旧バグ: 固定文字列 `"ROE_10yr_avg"` を使用、6年・8年集計の銘柄で不一致
  - 修正: `_roe_n_def = comps.get("roe_years_used") or 10` で動的に年数を取得
- スキャナー: `common/sec_data/phase1_scan.py` を新規作成（10カテゴリ 全銘柄検査）
- 再実行: 影響15銘柄 + Matrix②5銘柄 を再生成 → NG=0 / WARN=12(期限切れ決算日11件+軽微逆転1件)
- 回帰テスト: `tests/test_pipeline_logic.py` にFix1/Fix2/Fix3の回帰防止テスト6件を追加 (計83件合格)

### ✅ CONFIG-CAKE-SEG-1 (2026-06-11 完了): CAKEセグメント設定の名称・注記修正
- 修正: segment_config.json CAKE エントリー更新
  "Restaurant Sales" → "Restaurant Operations"（North Italia/FRC brands含む）
  "Bakery Operations" → "Bakery & Other"（外部卸売バクリー配送のみ）
- fiscal_year: FY2025 に更新

### ✅ FEAT-CHECK9-1 (2026-06-11 完了): consistency_check CHECK-9 セグメント設定陳腐化検知
- report_consistency_check.py に CHECK-9 追加（WARN）
- segment_config の fiscal_year が Generated年から2年以上前の場合 WARN-9 を発行
- _raw_lines を _parse_report() 結果に追加して Generated 行の年を取得
- 現状: FY2025設定(2026年生成)は1年差のためWARN未発動（設計通り）

---

## 2026-06-10 完了

### ✅ BUG-FCFBASE-2 (2026-06-10 完了): FCF赤字銘柄DCFガード
- DCF_Reliability: HIGH/LOW を report.txt に追加（revenue_floor適用時 = LOW）
- FCF_Base 表示を調整前後併記（実績avg: $-XX.XM を付記）
- 「5yr平均」を実データ年数で動的化（fcf_list_raw の len を使用）

### ✅ BUG-MATRIX4-1 (2026-06-10 完了): Matrix④ Y軸をFCF_History実績と統一
- Matrix④ Key_Metric_Y を fcf_history 最新年の実績マージンに修正
- （従来: FCF_Base/Revenue の比率 → 過大評価バイアスあり）
- **追補 (2026-06-11)**: fcf_history[-1]がNone(上場直後・SEC未取得年末尾)の銘柄で
  revenue_floor正値にフォールバックするバグを修正（RCATで検出）
  → reversed()で最新非Noneエントリーを採用 / 全None+floor適用時はN/A表示

### ✅ BUG-NETDEBT-4 (2026-06-10 完了): レポートNet Debt内訳表示
> 注記: これは表示のみの修正。同一時点原則によるNet Debt計算修正（当初BUG-NETDEBT-4と
> 重複命名されていた2026-06-13分）は BUG-NETDEBT-6 に改番済み（2026-06-13セクション参照）。
- Total_Debt/Cash 行に ST_Invest を追加表示（残高 > 0 の場合）
- 定義文を "Total Debt - Cash - Short_Term_Investments" に修正

### ✅ BUG-WACC-DISP-1 (2026-06-10 完了): 割引率表示の分離
- "WACC: XX%" を "Discount_Rate_Primary: 10.00%" + "WACC_CAPM_Reference: XX%" に分離
- 定義文も両者の役割を明記

### ✅ BUG-RPO-1 (2026-06-10 完了): RPO適用条件の強制
- SECTOR_RATES["Technology"] を (1.0, "SaaS") から (0.0, "Non-SaaS") に変更
- SaaS whitelist または industry キーワード（software/cloud/saas/internet）必須に
- NVDA（Semiconductors）の rpo_pv が $170.8M → $0 に修正

### ✅ BUG-ROEAVG-1 (2026-06-10 完了): ROE平均修正
- reader.py: 損失年度も含む全期間を平均（従来: 連続黒字期間のみ・上方バイアスあり）
- winsorize: |ROE| > 80% → ±80% にキャップ（CELH 119% → 80%）
- 動的ラベル: "ROE_avg (Nyr)" 表示、外れ値処理時は "(outlier-adjusted)" タグ追加
- SOFI: -3.9% (6yr) / CELH: -8.5% (10yr, outlier-adjusted)

### ✅ FEAT-SEGCHECK-1 (2026-06-10 完了): セグメント鮮度ガード
- segment_config.json 更新:
  - APP: Apps segment 削除 → Software Platform 100%（2024年 Apps 売却済み）
  - TSLA: Services and Other セグメント追加（12%）、Automotive 87%→77%
- APP の Segment_Weighted_Growth: 34.2% → 45.0% に修正

### ✅ BUG-NETDEBT-3 (2026-06-10 完了): reader.py 主要IV計算経路修正
- 内容: Net Debt補完が主要IVに反映されていなかった問題を解消
- AVGO -$14 / KO -$8 の過大評価を解消
- 修正: reader.py の主要IV計算経路にNet Debtフォールバック補完を適用

### ✅ β修正 (2026-06-10 完了): KO/LLY/HQY のβ値修正
- KO / LLY / HQY の beta_config.json 登録値を実態に合わせて修正

### ✅ TANUKI-DCF-1 (2026-06-10 完了): DCF基準FCFの採用方法改善
**分類:** 設計課題 / TANUKI VALUATION

#### 問題
FCF減少トレンドがある銘柄でDCF理論価格が過大評価される構造的バイアスが存在。

#### ①基準FCFに2年平均を使用 → CAGR < -5% 時に直近値へ自動切替（回復判定付き）
- `calculator/adjustments.py` に CAGR判定ロジック追加
- 最古値が負（先行投資期）の場合は判定スキップ（VST等の誤発動防止）
- method: `recent_1yr` / `avg_5yr_recovery` を新設

#### ②推奨成長率とDCF計算値の乖離 → 警告表示で対応済み
- segment_configured銘柄で recommended_g と実際のDCF成長率の乖離が ≥5pt の場合に
  ⚠️ 警告をレポートに表示（pipeline.py `_generate_report` 内）

#### ③FCFマージン悪化が成長率に未反映 → BEARシナリオへの反映で対応済み
- FCFマージン低下トレンドをBEARシナリオの乗数補正として反映
- `fcf_margin_bear_multiplier` を growth_sanity 経由で pipeline.py に渡す構造を追加

### ✅ BUG-TTM-1 (2026-06-10 完了): TTM Revenue GrowthがQ1単四半期YoYと混同
**分類:** バグ / pipeline.py

#### 問題
TTM Revenue Growthとして表示・DCF計算に使用されている値が、
実際にはQ1単四半期のYoY成長率である場合がある。
- PLTR: 84.7%（真のTTMは約67.8%）
- TSLA: 15.8%（真のTTMは約+2.25%）

#### 修正
TTMは「直近4四半期合計 / 前4四半期合計 - 1」で計算。
単四半期YoYとの混同を防ぐため、計算式を明示的にlog出力する。

### ✅ BUG-NETDEBT-2 (2026-06-10 完了): annual_2025.jsonでlong_term_debtが欠落
**分類:** バグ / pipeline.py / パーサー

#### 問題
4銘柄（AVGO, KO, SOFI, ZS）の `annual_2025.json` に `long_term_debt` が欠落。
- KO: total_debt $1.5B（short_debt のみ）→ 修正後 $38.0B
- AVGO: total_debt ~$3B → 修正後 $69.2B

#### 修正
`_load_extra_data()`, `_calc_g_fundamental()`, `_calc_roic_wacc_ratio()` にて
annual BS の `long_term_debt` が 0 の場合、normalized quarterly JSON の `LTDebt`
最新値（`_get_normalized_lt_debt()` ヘルパー）でフォールバック補完。

### ✅ BUG-NETDEBT-1 (2026-06-10 完了): Net Debt / Cashの定義不整合
**分類:** バグ / pipeline.py

#### 問題
Cash表示値とNet Debt計算値の参照タイミング・定義が不整合。
- PLTR: Cash $1.42B（FY2025末）vs 実際Q1末$2.29B。Net Debt -$7.18Bは短期投資含みだがCash定義と矛盾。
- SOFI: Total Debt $0（実際$1.82B）、Cash $4.93B（実際$3.40B）。

#### 修正（実施済み）
1. CashはSEC最新四半期末の値を使用（FY末ではなく直近10-Q）
2. Net Debt = Total Debt - Cash - Short_Term_Investments と定義を統一
3. Total Debtを明示的に取得・表示する（$0は異常値として警告）

---

## 2026-06-07 完了（TANUKI TAIL主要機能完了）

### ✅ TANUKI TAIL（投資テーゼ継続検証システム）
- Phase 1: テーゼ登録UI（GitHub Contents API ワンボタン保存）
- Phase 2: xbrl_segment_fetcher.py（Layer 2 KPI自動取得）
- Phase 3: EDGAR RSS監視・レビューキュー管理
- Phase 4: Grok四半期レビュー生成（Call 1定量・Call 2定性）
- Phase 5: レビュー表示UI（5タブモーダル）
- Step 0: KPI確定フロー（Grok提案→UI確認）
- Layer 3: MD&A・8-Kテキストからの非XBRL KPI抽出
- tail_dcf_bridge.py: 将来理論価格計算（bear/base/bull×1/3/5年）
- satellite_monitor.py: 変化通知（±20%・エグジット充足・決算接近）
- journal.json: 判断ログ・DECISION LOG UI
- prediction_tracker.py: 過去予測の振り返り
- 残タスク: EWM楽観バイアス係数・データパス統一（優先度低）→ BACKLOG.md管理

---

## 2026-06-03〜04 完了

### ✅ [DESIGN-11] Stonks Silo UEスコアバックエンド補完（2026-06-03 完了）
- analyzer.py に unit_economics_score/label/gross_margin_trend 計算を追加
- IOT/AVAV/ZETA=100pt（優秀）、BBAI/KULR/RDW=0pt（低調）で直感と一致
- ASTS/JOBY は gross_margin_note="construction_phase" で処理

### ✅ [ACTION-6] Macro Extreme Fear戦略実行支援（2026-06-03 完了）
- docs/value-monitor/extreme-fear/index.html を新規作成
- F&Gゲージ・買い候補TOP10・過去EF実績・シミュレーター・メモ欄の5セクション
- スコアリング: BUY+40/WATCH+20/upside+30/funda+20/Phase≤2+10/Phase4-20pt

### ✅ [ACTION-2] 判定実績の自動追跡・検証ループ（2026-06-03 完了）
- score_history.json に判定スナップショットを日次追記
- score_verifier.py で 30/60/90日後リターンを自動計算
- index.html に判定別勝率テーブル＋直近20件を表示
- score_verifier.py の定期実行: Score_Verifier.yml 登録済み（毎日 JST 9:00）
  → 2026-07-03 以降に初回リターンが記録される
- 判定実績セクションをTANUKI VALUATION→TANUKI SCOREに移設（2026-06-04）
  docs/value-monitor/tanuki_score/index.html を新設

### ✅ [ACTION-4] HYPEMIXポートフォリオ管理（2026-06-03 完了）
- フェーズ分布バー・目標乖離・リバランス提案・銘柄テーブルを TANUKI index.html に追加
- 現状: P4=52%（目標10%比+42pt超過）・P1=0%（目標20%比-20pt不足）を検出
- 実装: docs/value-monitor/tanuki_valuation/index.html に renderHypemix() 関数追加

### ✅ [MP-5] IMPLIED CUTS根本解決（2026-06-03 完了）
- get_implied_cuts(): ZQ=F implied rate でterm premium補正・FRED FEDFUNDS/DGS1使用
- 旧: DGS1生値 -0.82cuts（誤）→ 新: ZQ=F補正 +0.01cuts（実態）
- ZQ=F取得失敗時はDGS1生値にフォールバック

### ✅ [MP-4] センチメントゲージへのバックテスト予測ミニゲージ統合（2026-06-03 完了）
- バックテスト表を削除し「明日は？」「5日後は？」「20日後は？」のSVGミニゲージ3つに置換
- 現在ゾーンの過去平均リターンから予測スコア計算（S&P500 +1%≈+2pt換算）
- 点線=現在針・実線=予測針の2針表示

### ✅ [MP-3] 資金フローUI改善：タイルと推移テーブルの縦統合レイアウト（2026-06-03 完了）
- grid-template-columns: 60px + 7列でタイルをヘッダー兼任にした統合グリッドに変更
- 日付行を降順（最新上）でタイル直下に縦連結、色分け・軸ラベル・5日平均フッター維持
- renderAssetFlow/renderAfHeatmapを1関数に統合、旧クラス（af-grid/af-hm-*）を削除

---

## 2026-06-01〜02 完了

### ✅ [MP-1] AIレポート「出来高比」表現の修正（2026-06-02 完了）
- 修正: S&P500/NASDAQ を個別表記に変換してGrokに渡すよう collect_and_send.py を修正
- プロンプトに「指数を限定して記述・両者をまとめる表現禁止」制約を追加

### ✅ [MP-6] AIレポートの表現・解釈バグ（2026-06-02 完了）
- ①債券バッジ「リスクオン/オフ」→「債券売り/買い」に変更（collect_and_send.py + index.html）
- ②信用収縮誤解釈防止：HYG・LQD同時下落→「金利上昇圧力/デュレーションリスク」限定。HYGのみ下落時のみ「信用スプレッド拡大」を許可するプロンプト制約を追加
- ③乖離Zスコア符号定義明示：正=NASDAQ優位/負=S&P500優位をextended_dataとプロンプト両方に付記

### ✅ [MP-2] AIレポート品質改善・表記統一（2026-06-03 完了）
- ①センチメントスコアを:.0f整数変換してGrok渡し・プロンプト小数禁止制約追加
- ②VIX小数点2桁（16.05形式）統一・1桁禁止制約追加
- ③Risk-Off Score 3軸配点（33/33/34pt）と全体要約への1行明記を義務化
- ④VIX9D上昇+1pt未満は「急騰」禁止→「上昇加速(+Xpt)」、+3pt以上のみ「急騰」許可
- ⑤VIX9D＜VIX30D維持しつつ9D上昇加速中は「移行期」文脈を必ず明記
- ⑥NH=xxx, NL=yyy, NH-NL差=±zzzの3値表示に変更・差の拡縮分析を義務化

### ✅ [DESIGN-8] 8-1 推薦理由・スクリーニング条件の可視化（2026-06-01 完了）
- 実装: conditions_met / risk_flags フィールドをGrokプロンプトに追加
  銘柄カードにアコーディオンパネル（▼ 詳細）で展開表示

### ✅ [DESIGN-8] 8-2 ニュース表示の改善（2026-06-01 完了）
- 実装: ニュースタイトルをURLリンク化（hover下線・新タブ）
  出典「via ○○」表示対応（sourceフィールドをGrok出力に追加）
  ニュースなし銘柄をゾーンレベルで折りたたみ（デフォルト非表示）

---

## 2026-05-31 完了

### ✅ [DCF-1] 本当の5年逓減DCFエンジン（2026-05-31 完了）
- 概要: Phase1内でg_start（推奨成長率）→g_end（業界ベンチマーク）へ年次線形逓減
- 適用条件: growth_model=="decay"（TTM>50%）かつindustry_benchmark取得済みの未設定銘柄
- 実装:
  calculator/dcf.py: calculate_tapering_dcf() 追加
  calculator/scenarios.py: tapering_g_end パラメータ追加
  core_calculator.py: calculate_pt(tapering_g_end) に対応
  pipeline.py: _tapering_g_end を growth_sanity から取得して渡す
- 実績: 10銘柄に逓減DCF適用（ALAB例: 51.5%→9.6%、IV $667→$206）
- テスト: 5件追加（計37件）
- 適用外の銘柄と理由:
  segment_configured=True の銘柄（NVDA/META/GOOGL等）→ 手動設定済みのため再計算ブロック非実行
  maturity_config で three_stage DCF の銘柄（NVDA等）→ Phase2で成長減速を既に表現済み
  将来: segment_configured 銘柄への逓減対応は DCF-1b として別途検討

### ✅ [DCF-2] 高成長銘柄向け GROWTH_PREMIUM カテゴリ追加（2026-05-31 完了）
- 概要: 通常TRIM条件（upside<-30%・funda≥50・phase≥3）でも
  逆DCF Required Growth < TTM成長率の場合は GROWTH_PREMIUM を返す
  （現在の成長率が市場要求をすでに上回っているため、プレミアムに根拠あり）
- 実装:
  pipeline.py: _calc_required_growth() 追加（逆DCF・5年CAGR）
  _compute_tanuki_score(): GROWTH_PREMIUM vs TRIM の分岐追加
  valuation_enriched に growth_sanity を事前注入（タイミングバグ修正）
- 実績: ALAB（RequiredG=75% < TTM=93%）→ GROWTH_PREMIUM
        SITM（RequiredG=77% < TTM=88%）→ GROWTH_PREMIUM
        LITE/PLTR（RequiredG > TTM）→ TRIM（従来通り）
- テスト: 3件追加（計40件）

### ✅ [DCF-3] β個別推定の精緻化（2026-05-31 完了）
- 概要: 全67銘柄を yfinance 5年βで一括更新、source フィールドを付与
- 更新ルール:
  上限 2.5（CAPM前提崩壊を防ぐ）/ 下限 0.3（異常値対策）
  LMT のみ Damodaran Aerospace/Defense β=0.74 を使用（yfinance=0.10 は異常値）
- 主要変更:
  NVDA: 1.05 → 2.24（+1.19） WACC 8.9%→17.1%
  LLY:  1.10 → 0.48（−0.62） WACC 10.7%→7.0%
  LMT:  1.10 → 0.74（−0.36） WACC 10.6%→8.5% (Damodaran使用)
  AMD:  1.10 → 2.40（+1.30） GOOGL: 未設定→1.27 追加
  大幅乖離（>0.5）: 25銘柄更新
- 設定ファイル: config/beta_config.json（_updated_at/source フィールド追加）

### ✅ [RICE-1] RICEから成長率依存を減らす（2026-05-31 完了）
- 現状: RICE = (G × Q × CF) / WACC でGが支配的
- 実装: 価値創造係数（VC_Factor）を導入
  新式: RICE = (G × VC_Factor × Q × CF) / WACC
  VC_Factor = clamp(ROIC / WACC_Rm, 0.3, 2.0)
  ROIC = NOPAT / Invested_Capital（最新年次、実効税率21%固定）
  ROIC > WACC（10%）: 再投資が価値創造 → G を最大2倍に増幅
  ROIC < WACC: 再投資が価値毀損 → G を最小0.3倍にペナルティ
  ROIC 不明（赤字企業等）: VC_Factor=1.0（後退互換）
- 結果例: NVDA ROIC/WACC=6.6→cap2.0、MRVL ROIC/WACC=0.63（ペナルティ）
- テスト: 5件追加（計45件）
- 変更ファイル: calculator/rice.py, core_calculator.py, pipeline.py

### ✅ [GROWTH-1] 成長逓減モデルの精緻化（2026-05-31 完了）
- 旧: recommended_g = (TTM + 業界平均) / 2（固定50:50）
- 新: HypeCoreフェーズで重みを調整
  Phase1-2（黎明〜拡大）: TTM×65% ＋ 業界平均×35%（成長継続余地あり）
  Phase3 （陶酔期）     : TTM×50% ＋ 業界平均×50%（旧来バランス）
  Phase4 （剥落期）     : TTM×35% ＋ 業界平均×65%（正規化加速）
- 変更: growth_sanity.py（hype_phase追加）、pipeline.py（_load_hype_phase追加）
- テスト: 3件追加（計55件）

### ✅ [WACC-1] ターミナル成長率の銘柄別設定（2026-05-31 完了）
- 変更: 全銘柄一律 3.0% → Damodaran 業種ベースのセクター別設定
- テーブル:
  テック・半導体・SaaS: 3.5%（デジタル経済の長期構造成長）
  防衛・ヘルスケア・金融: 3.0%
  消費者・飲食: 2.5%（成熟市場）
  業種不明: 3.0%（デフォルト維持）
- 実装:
  maturity_config.py: _DAMODARAN_TV_G・_TICKER_TV_G テーブル追加
  get_terminal_growth(): 直引き→業種→デフォルトの3段階フォールバック
  pipeline.py: _calc_required_growth(tv_g) パラメータ化・GROWTH_PREMIUM判定に適用
- テスト: 7件追加（計52件）

### ✅ [NET-1] financial_health.net_debt と bs_adjustment.net_cash の不整合（2026-05-31 完了）
- 修正: pipeline.py _load_extra_data() で short_term_investments を net_debt に加算
  net_debt = total_debt - cash - short_term_investments
  bs_adjustment.short_term_investments を参照して整合を取る
- 結果: AAPL Net_Debt +67.09B → +48.33B（bs_adjustmentと一致）
  financial_health に short_term_investments フィールドを追加

### ✅ [DESIGN-1] ERP参考表示（2026-05-31 完了）
- 実装: ERP = ForwardEPS/Price - Rf（10年国債利回り）を HYPECORE セクションに追加
  ERP≥4%: 明確な割安感 / 2〜4%: 魅力あり / 0〜2%: 薄い / <0%: 割高感
  pipeline.py: _generate_report() 追加 + latest.json に erp/forward_earnings_yield 保存
- 残タスク: HypeCoreフェーズ判定への組み込みは効果確認後に検討（DESIGN-1b）

### ✅ [DESIGN-3] 将来株価計算機能（2026-05-31 完了）
- 概要: 将来理論株価を3年→5年に拡張、期待リターン表示を追加
- 実装:
  core_calculator.py: projection_years=5 に変更
  core_calculator.py: calculate_return_metrics() の結果を
    "return_metrics" キーとして latest.json に保存
  stock.html: 将来価値テーブルを5列に自動拡張
  stock.html: 「現在株価」行に各年の期待リターン%を緑/赤色で表示
  stock.html: 「5年BASE年率換算: +XX% / 年」を表示
- 実績（NVDA）: 5年後BASE $2,046（年率+57.7%、現在株価$211起点）

### ✅ [DESIGN-7] HYPEMIXの概念導入（2026-05-31 完了）
- 概要: 保有銘柄のHypeCoreフェーズを意図的に分散させる
  ポートフォリオ管理概念（Koichi氏の造語）
- 実装: Phase分布の可視化 + 目標HYPEMIXからの乖離スコア + リバランス提案

### ✅ [DESIGN-8] 8-5 特大テーマの発掘・予測（2026-05-31/2026-06-01 完了）
- 概要: Grokが週次で「次の特大テーマ候補」を分析
  根拠・確度・時間軸を構造化して表示
  「Grokの見解」として参考表示にとどめる

### ✅ [DESIGN-8] 8-6 銘柄への投資テーマ付与とテーマ別比較（2026-05-31 完了）
- 概要: 各銘柄にテーマタグを付与（手動 or AI提案）
  theme_config.jsonで管理・admin.htmlから編集
  テーマ別に登録銘柄を一覧・比較できる画面を追加
  HYPEMIX的な視点（フェーズ分散）も同時表示

### ✅ [DESIGN-10] RICEの三分類見直し（2026-05-31 完了）
- 概要: 現行の閾値2.0（高/低の二分類）を三分類に変更
  高効率: RICE ≥ 2.0（価値創造・現行維持）
  中効率: RICE 1.0〜2.0（資本コスト上回る・価値中立）
  低効率: RICE < 1.0（資本コスト未満・価値破壊水準）
- 理論的根拠: RICE=1.0がWACCとの均衡点
- 実装: pipeline.py Matrix①のラベル三分類化 + テスト5件追加

### ✅ [DESIGN-12] ステルス流動性の3層構造改善（2026-05-31 完了）
- 実装: 3層構造でステルスカードを再構成
  Layer1: FRBレジーム（fed_context.csvから非同期取得）
  Layer2: ステルス流動性（従来のsupply/absorb/neutral＋連続週数）
  Layer3: NET流動性トレンド（▼▼▼で視認性）
- 新カラム: stealth_absorb_weeks / net_liq_decline_weeks / stealth_alert
- 警戒アラート: 3条件を評価して赤枠ボックス表示
- 変更: 05_main.py（計算）/ index.html（3ペイン表示）

### ✅ [DESIGN-13] MACROPULSEでマクロサプライズ検知（2026-05-31 完了）
- 実装: detect_macro_surprises()を05_main.pyに追加
  9指標の前回比急変を閾値検知（NFP±5万、Claims±2万、Philly±10pt等）
  逆指標判定あり（Claims↑=悪化、NFP↓=悪化）
  同カテゴリ2件以上同時悪化→「複合サプライズ」
  カテゴリ: インフレ/雇用/景気（色分けバッジ）
- 保存: weekly_analysis.csv に surprise_alerts カラム追加
- 表示: AI WEEKLY COMMENTARY直前に.surprise-banner追加（空時は非表示）
  Discord通知にもサプライズ一覧を追記

### ✅ [ACTION-10] TANUKI SCOREの変化検知機能（2026-05-31 完了）
- 検知対象: 判定変化（BUY→TRIM等）/ HypeCoreフェーズ転換（Phase2→Phase3等）/ 乖離率の大きな変化（±10pt以上）/ 撤退条件への接近
- 通知タイミング: 変化が発生した時のみ
- 通知先: Discord（既存WEBHOOK活用）

### ✅ [DISCOVER-1] 未発掘銘柄優先のプロンプト改善（2026-05-31 完了）
- 変更内容:
  時価総額: 100億〜1000億ドル → $5億〜$100億（小〜中型）
  機関投資家: 「増加傾向」→ 保有率 < 40%（定量化）
  売上成長: 20%以上 → 30%以上
  追加: 主要指数未採用（S&P500・Russell1000・Nasdaq100等）
  追加: 推薦JSONに market_cap_b / revenue_growth_pct / institutional_ownership_pct を出力
- 実装: src/discover/collect.py の explore_candidates プロンプトのみ変更

### ✅ [BUG-2b] _calc_q: GAAP赤字年のSBC偽陽性Q値（2026-05-31 完了）
- 発見: NI<0年にSBCで earnings>0 になるとQ計算に混入し異常Q値が発生
  例: NI=-469M, SBC=+608M → earnings=139M → Q=OCF/139M=13.43
- 影響: MRVL（Q=6.97→0.51）をはじめ11銘柄のRICE値が不正確だった
  NET/ZS/ZETA/SOUN: 誤ってRICE有りと判定（正しくはQ計算不可）
- 修正: `calculator/rice.py` _calc_q に `if ni < 0: continue` を追加
- テスト: 3件追加（計32件）

### ✅ [BUG-11] quarterly.py: NetIncomeフォールバック未設定（2026-05-31 完了）
- 発見: AVGO/BKNG/AVAVのTTM系列でNI=None（Q計算不可・RICE誤分類）
  原因: quarterly.py が NetIncomeLoss のみ参照し ProfitLoss 等を見ていなかった
  AVGO: NetIncomeLossの四半期データが2019以前で途絶 → ProfitLossが必要
  BKNG: NetIncomeLoss自体が未申告 → NetIncomeLossAvailableToCommonStockholdersBasicが必要
  また _FALLBACK_MIN_FIELDS に NetIncome がなく q_count<4でもフォールバック未発動
- 修正: `common/sec_data/quarterly.py` に NetIncome フォールバック追加
  _FIELD_FALLBACKS["NetIncome"] = (ProfitLoss, NetIncomeLossAvailableToCommonStockholdersBasic)
  _FALLBACK_MIN_FIELDS に NetIncome を追加
- 結果: AVGO RICE=2.3(Matrix①正常), BKNG セクター除外(Matrix②正常), AVAV Q取得成功

### ✅ [FEAT-8] SECデータ品質監査の自動化（2026-05-31 完了）
- `common/sec_data/audit.py` 作成
  NI/OCF/Revenue の全件・一部 None を検出、重大問題は Discord 通知
- `.github/workflows/SEC_Data_Audit.yml` 作成
  SEC_Data_Update 完了後に自動実行
- `CLAUDE_CODE_START.md` にパイプラインコード変更時の必須手順を追記

### ✅ [FEAT-9] Matrix③散布図: Q計算不可銘柄を表示（2026-05-31 完了）
- 赤字銘柄（Q計算不可）が散布図に表示されていなかった
- stock.html の loadAndRenderMatrices を修正
  Q計算不可銘柄もMatrix③にルーティング（11銘柄が新規表示）
  Q異常値（Q>5）との視覚区別: 白ストローク付きドットで区別

### ✅ [FEAT-10] β再発防止の3施策（2026-05-31）
- beta_fetcher.py: 全銘柄βをyfinanceから自動取得・更新（cap2.5/floor0.3）
  Damodaran手動設定は保護、sourceフィールドで取得元を記録
- audit.py --check-beta: SEC監査にβ乖離チェック追加（0.5超で警告、1.0超で重大）
- Beta_Config_Update.yml: 月次自動更新ワークフロー（第1日曜JST8:00）
- CLAUDE_CODE_START.md: 新規銘柄登録Step2にbeta_fetcher.py追加

### ❌ [DESIGN-9] RIMモデル（廃止 2026-05-31）
- 実装後に廃止。理由: 66銘柄中3銘柄のみ信ぴょう性あり（BV/P>30%）
  自社株買い主体のテックポートフォリオでは会計上BVが圧縮されており
  NVDA BV/P=3%・AAPL BV/P=1.6% など大半で過小評価となり誤解を招く

---

## 2026-05-30 完了

### ✅ [BUG-1] FCF外れ値が5年平均に含まれていた
- action="excluded" の結果がbase_fcfに反映されていなかった
- 修正: 外れ値除外後の残り年数で平均を再計算

### ✅ [BUG-2] Q分母のmax(NI+SBC, 1)設計ミス
- 赤字年でQ=数千万倍の異常値が発生
- 修正: 赤字年・利益ほぼゼロ年をスキップ

### ✅ [BUG-3] META Q4 SBC二重タグ問題
- A-2グループ8銘柄に波及修正

### ✅ [BUG-4] GOOGLセグメント設定漏れ
- Cloud Infrastructure 100%→3セグメントに修正

### ✅ [BUG-5] FCFコメント誤判定・HYPE_Signal EPS条件誤り
- FCFマイナスなのに「FCF黒字」表示
- EPS YoYマイナスなのに「EPSは強い」表示

### ✅ [BUG-6] Matrix割高/割安逆転
- upside参照先の誤りを修正

### ✅ [BUG-7] Runway計算バイパス
- 一時的黒字でRunway計算がスキップされていた

### ✅ [BUG-8] substage_watch固定テキスト幻覚
- hypecore.pyの固定文字列をeps_surprise実値ベースに変更

### ✅ [BUG-9] shares_yr年号格納バグ
- 株式数フィールドに年号が入っていた

### ✅ [BUG-10] NOW株式分割（5:1）対応
- 希薄化率72.61%→0.6%に修正

### ✅ [FEAT-1] Damodaran業種別ベンチマーク導入
- growth_sanity.pyによるサニティチェック実装

### ✅ [FEAT-2] 成長率自動精緻化
- セグメント未設定銘柄にTTM実績値を自動適用
- 高成長銘柄（TTM>50%）に逓減モデルを適用
- recommended_gをDCFに反映

### ✅ [FEAT-3] RICE_adj追加
- R&D除外CF（設備投資のみ）ベースのRICE補正版

### ✅ [FEAT-4] 逆DCF分析追加
- 現在株価を正当化する必要成長率を逆算表示

### ✅ [FEAT-5] 希薄化スコア追加
- 6段階評価・report.txt・stock.htmlに表示

### ✅ [FEAT-6] Forward EPS追加
- yfinanceのforwardEpsをレポートに表示

### ✅ [FEAT-7] ユニットテスト24件追加
- 回帰バグ検出の基盤を整備

---

## 過去セッション完了

### ✅ MACRO PULSE 関連
- MACRO PULSE 流動性モニター・NET LIQUIDITY実装
- MACRO PULSE Hollow Rally検知
- MACRO PULSE ステルス流動性（TGA/RRP）可視化

### ✅ TANUKI VALUATION 関連
- αキャップ（上限1.0）実装
- RPO補正実装
- ネットキャッシュ補正を有利子負債のみに限定（実装済みを確認）

### ✅ Stonks Silo 関連
- フロントエンド（HTML）実装済み（index.html 1298行）
- GitHub Actions 設定済み（Stonks_Silo_Update.yml）
- gross_margin: ASTS/JOBY のみ null（construction_phase として扱い）→ 他20銘柄は取得済み

---

## 2026-06-14 完了

✅ [BUG-EPS-UNIT-1] LOAR/ONDS EPS per-share 株式数単位バグ修正 + CHECK-14/15/16追加 ✅ 2026-06-14
- **症状**: LOAR adj_eps=$151/$396/$320（実株価$68）、ONDS Q1 2026 adj_eps=$119.24
- **根本原因**: SEC XBRL の WeightedAverageNumberOfDilutedSharesOutstanding が
  千株単位で報告されているが unit="shares" と誤記されているケース
  LOAR: 全四半期平均95,913 << 1M → 全期間千株単位と判断
  ONDS Q1 2026: 461,706 << 直近8Q中央値×1% → 孤立四半期の千株単位
- **修正**: `extract_key_facts.py` に 2段階サニティチェックを追加
  Stage①: 全期間平均 < 1M → 全四半期 ×1000（LOAR適用）
  Stage②: 直近8Q中央値の1%未満の孤立四半期 → その四半期 ×1000（ONDS適用）
- **CHECK追加**: `report_consistency_check.py` に CHECK-14/15/16 追加
  CHECK-14: adj_eps > 現在株価×50% → NG（単位ミス異常値検知）
  CHECK-15: adj_eps > 現在株価 → NG（さらに深刻な単位ミス）
  CHECK-16: 直近4Q未満のデータ → WARN（TTM不完全）
- **結果**: LOAR FY2025 GAAP_EPS $752.20→$0.7522、Adj_EPS→$1.1061 ✓
  ONDS Q1 2026 株式数461,706→461,706,000、adj_eps $119.24→$0.1192 ✓
  consistency_check: NG=0 確認済み

✅ [BUG-INTU-GROWTH-1] INTU Section 4 Layer 1 成長率表示バグ修正 ✅ 2026-06-14
- **症状**: INTU の [4. 成長率根拠] で "中央値モデル" が 19.7% を参照し
  DCF適用値 12.8% との関係が不明瞭
- **根本原因**: Layer 1（segment_configured=True）銘柄でも Layer 2 と同じ
  表示フローを使っており、DCF G（セグメント加重平均直接）とラベルが乖離
- **修正**: `pipeline.py` Section 4 を `_seg_configured` で分岐
  Layer 1: "セグメント加重モデル（Layer 1）" と表示、recommended_g を "Layer 2 参考値・DCF未適用" と明記
  Layer 2: 従来通り "中央値モデル/逓減モデル"
- **結果**: INTU 報告が "DCF適用値: 12.8%（セグメント加重平均）/ 推奨成長率: 19.7%（Layer 2 参考値）" と整合 ✓

✅ [BUG-INTU-NETDEBT-1] INTU 短期投資 Net Debt 欠落調査 → 誤検知 ✅ 2026-06-14
- **疑惑**: INTU の短期投資がNet Debt計算から漏れている可能性
- **調査結果**: INTU の XBRL には ShortTermInvestments タグが存在しない
  INTUの財務構造上 short_term_investments=0 は正しい値。修正不要。

## [BUG-FOUR-1] FOUR（Shift4 Payments）EPS・株式数・希薄化異常値 ✅ 2026-06-14

### 症状
- Latest_Adjusted_EPS: $49.93（正常値: ~$0.40）
- TTM調整後EPS: $119.70（正常値: ~$1.20）
- Dilution_3yr_Annual: -29.86%/yr（誤）
- ⚠️ 株式数乖離警告: yf=99M vs SEC=1M (+7332.8%)

### 根本原因
FOUR の UP-C LLC 構造変更（2021-2022）後、XBRL の
WeightedAverageNumberOfDilutedSharesOutstanding が
Class A 株式のみを報告（~1.33M）し、実際の経済的持分（~99M）の
約1/74 しか反映されない。10-Q には株式数タグが一切存在しないため、
TTM が4四半期合計ではなく4年分の年次EPS合計になる二次バグも発生。

### 修正内容
1. `config/cik_lookup.csv`: FOURのepsフラグ true→false（EPS Analyzerスキップ）
2. `src/value/tanuki_valuation/pipeline.py`: yf/SEC株式数乖離>10倍の場合に
   希薄化計算をスキップするサニティチェック追加（comps参照修正も含む）
3. `config/discover_config.json`: FOURのmemoにUP-C構造の注意事項を記録

### 汎用効果
SEC/yfinance乖離10倍サニティチェックはFOUR以外にも適用される。
同様のUP-C構造銘柄（APP等）でXBRL異常が発生した際も自動保護される。

### 教訓
UP-C構造（上場会社がLLC管理会社になる形態）ではXBRL株式数が
経済的実態を反映しないケースがある。新規銘柄登録時にUP-C構造の
有無を確認し、該当する場合はeps=false設定を検討する。

---

### [TAIL-EWM-1] EWM楽観バイアス係数の定義明確化
**完了日:** 2026-06-26
**判断:** B案（現状維持）でクローズ

#### 理由
- optimism_bias_warningのUIコードはtail/index.html L1252-1253に実装済み
- predictions/データが生成されれば自動表示される設計になっている
- 数値的EWM係数補正は過剰設計と判断
- AIプロンプト経由の定性的楽観バイアス警告（quarterly_review_generator.py）で十分
