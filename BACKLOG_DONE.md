# BACKLOG 完了アーカイブ / アクティブな課題は BACKLOG.md を参照

---

## 2026-06-22

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
