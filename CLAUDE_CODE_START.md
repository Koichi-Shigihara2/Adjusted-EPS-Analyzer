# Claude Code 作業開始テンプレート

## 毎回の作業開始時に必ず実行すること

### Step 0: ローカルリポジトリの最新化（最優先）
GitHub Actions が前回セッション後にデータを自動更新している可能性があるため、
作業開始前に必ずローカルを最新化する。

```bash
cd C:\Users\shigi\Documents\On-a-journey-git
git pull --rebase origin kaihatsu
```

コンフリクトが発生した場合：
- 自動生成データファイル（.gitattributes の merge=ours 対象）→ ローカル版が自動採用される
- 手書きファイル（.py / .md / config/*.json 等）→ 内容を確認してから解決する

### Step 1: 現状確認
以下のファイルを読んでください：
- SYSTEM_MAP.md（システム間の依存関係・変更影響範囲を把握）
- BACKLOG.md
- src/value/tanuki_valuation/pipeline.py（直近の変更を把握）

### Step 2: テスト実行
cd C:\Users\shigi\Documents\On-a-journey-git
python -m pytest tests/test_pipeline_logic.py -v
全件パスを確認してから作業を開始する。
失敗があれば先に修正する。

### Step 3: 作業内容の確認
BACKLOGから以下の優先順位で作業項目を選定：
1. 優先度：高 かつ 着手条件が満たされているもの
2. 難易度が低いものを優先
3. 着手条件が未達のものはスキップ

### Step 3.5: 既存実装の確認と設置場所の妥当性検証
実装前に必ず以下を確認する：

**① 既存の類似機能を検索**
```bash
grep -rn "[機能キーワード]" docs/ src/ --include="*.html" --include="*.py"
```
既存実装がある場合は新規実装ではなく改善・移動を検討する。

**② 設置先ファイルの利用目的との整合性を確認**
実装しようとしている機能が、設置先ファイルの本来の目的と一致しているか確認する。
- そのファイルは何のためのファイルか？
- 追加しようとしている機能はその目的の範囲内か？
- 目的が異なる場合は正しいファイルを探すか、新規ファイルを作成する

例：ポートフォリオ管理機能 → TANUKI VALUATION画面ではなくPORTFOLIO画面へ

誤配置の実例（2026-06-17修正済み）:
  誤: TANUKI SCOREの売買判定履歴 → stock.html（TANUKI VALUATION）に実装
  正: 売買判定 → TANUKI SCOREの責任範囲
     HYPECOREフェーズ履歴 → TANUKI VALUATIONの文脈に合致

### Step 4: 作業前の宣言
「〇〇（BACKLOG項目名）を実装します。
 変更するファイルは△△のみです。」
と宣言してから作業を開始する。

---

## 作業ルール

### ファイル変更の原則
- 指示されたファイルのみを変更する
- 変更範囲を事前に明示する
- 既存の動作を壊さない

### 履歴JSONへの記録ルール
- 記録キーは必ず日付ベース（YYYY-MM-DD）で重複排除する
  （タイムスタンプ全体を記録する場合でも重複排除キーはdate[:10]を使う）
- 実装参照: score_history.json（pipeline.py:566）・hypecore_history/（同パターン）

### 新規銘柄属性を追加した場合の必須対応

バックエンド（pipeline.py・data_fetcher.py等）に新しい銘柄属性・設定項目を追加した場合、
以下を必ずセットで実施する：

**① フロントエンドへの登録機能追加**
- admin.html（または該当する管理画面）に
  新属性の入力・編集UIを追加する
- 既存銘柄への一括適用手段も合わせて用意する

**② 銘柄登録手順への追記**
- CLAUDE_CODE_START.md の「新規銘柄登録時の必須手順」に
  新属性の設定ステップを追加する
- 設定漏れ時の影響（フォールバック値・デフォルト動作）も明記する

**③ ユーザー向け数値・バッジを追加した場合は glossary.json に説明を追加する**（EPIC-LEGEND-1）
- 新しいスコア・バッジ・色分け・「–」表示等、ユーザーが意味を読み取れない可能性のある
  表示を追加した場合は `docs/common/glossary.json` に用語キー→説明文のエントリを追加し、
  該当箇所のHTMLに `<span data-info="key">` を付与する（`docs/common/info-tooltip.js` が
  自動でホバー/タップ可能なツールチップに変換する）
- 銘柄ごとに異なる動的な説明文（理由付きの警告等）には `data-info-text="説明文"` を使う
  （glossary.jsonの静的辞書を経由しない。既存要素への後付け属性設定もJSから可能）
- 既存の用語と意味が同じ場合は新規エントリを作らず既存キーを再利用する
  （例: 「DCF_Reliability=LOW」の説明はTANUKI VALUATION/TANUKI SCORE両方で共通利用）

例：
  discover_config.json への登録 → Step 6 として追加（2026-06-03）
  HypeCore 実行 → Step 5 として追加（2026-06-03）

### コミットルール
git add [変更ファイル]
git commit -m "feat/fix/docs: 変更内容の説明"
git pull --rebase origin kaihatsu
git push origin kaihatsu

# ※ パイプラインコード変更後の再生成コミット時は、pushの前に手動でも確認可能：
# python common/sec_data/report_consistency_check.py --fail-on-ng
# （GitHub Actionsの自動ゲートで止まるが、ローカルで先に確認したい場合）
- `git push --force` は絶対に使わない
- results.json を含むコミットは必ず rebase してから push
- **バグ修正時の再生成順序を守る（巻き戻り防止）**:
  「コード修正 → コミット＆push → 全銘柄再生成 → 再生成結果をコミット＆push」の順で行う。
  「再生成が先・コード修正pushが後」にすると、Actions自動再生成が修正前コードで走り
  修正前レポートが本番に残存する（2026-06-11事例: 再生成02:32 → 修正push04:49）。

### テストルール
- 実装後に必ず pytest を実行する
- 新機能には必ずテストを追加する
- テスト失敗のままコミットしない

### フロントエンドのエラー耐性ルール（MP-RENDERALL-CRASH-1の教訓・必須）

画面内の複数セクションを描画する一括処理（renderAll()的な関数）を
実装・変更する際は、1つのセクションの描画失敗が他のセクションの描画を
道連れにしない構造にする：

- 個々の描画関数（renderXxx()）呼び出しはtry-catchで包むか、
  config配列化してforEach+try-catchでループ処理する
- 例外発生時はconsole.errorで関数名付きログを出力する（無言で
  握りつぶさない）
- オブジェクトの外側（`if(!obj)`等）をnullガードしても、内部の
  個々のフィールド（`obj.value`等）が独立してnullになり得る場合は
  別途ガードが必要。「外側を確認した＝中身も安全」と類推しない。
  フィールドアクセスごとに`!=null`/`?.`の有無を確認する
- 新しいnull/undefined値を生む可能性のある変更（データクレンジング・
  フォールバック処理の追加等）を行った場合、その値を消費する側の
  全箇所（renderXxx関数群）にガード漏れがないか横展開で確認する

### フロントエンドのデータ表示不具合の調査順序

データがN/A・空白・読込中のまま表示される場合、以下の順序で調査する：

**① まずfetchパスを確認（最優先）**
データが存在するのに表示されない場合は、
fetchパスが正しいかを最初に確認する。

```bash
# detail.htmlからの相対パスを計算
python3 -c "
import os
base = 'docs/[HTMLファイルのディレクトリ]'
target = 'docs/[JSONファイルのパス]'
print('正しい相対パス:', os.path.relpath(target, base))
"
# HTMLのfetchパスと一致しているか確認
grep -n "fetch" docs/[対象HTMLファイル]
```

**② 次にデータの存在確認**
fetchパスが正しい場合に限り、JSONファイルの
フィールド名・値を確認する。

**③ 最後にロジック確認**
データが存在してパスも正しい場合に
計算ロジック・フィルタ条件を確認する。

※ データ側の調査を先にするとfetchパスの問題を見落とす。

**④ 「データソース側の問題（外部要因）」と結論づける前の確認
（MP-IRX-FRED-1の教訓・必須）**

特定のティッカー・指標だけ繰り返し取得失敗する場合、安易に
「Yahoo Finance側にデータがない」等の外部要因と結論づけない。
取得コード（yfinance等）が失敗していることと、データソース自体に
データが存在しないことは別問題であり、混同すると誤った対応（様子見・
放置）につながる。

判断前に以下を確認する：
1. データソースの公式サイト・一次情報で、実際にそのデータが存在するか
   直接確認する（例: Yahoo Financeの該当銘柄ページを直接見る）
2. 同じ取得ループ内の他の銘柄・指標と比較し、処理の違い（個別分岐の
   有無）を確認する
3. GitHub Actions実行ログ（取得できる範囲で）を確認し、実際に
   何が返ってきているか（空応答・エラー・タイムアウト等）を確認する
4. レート制限・IPブロック等、実行環境（GitHub Actions等）特有の問題の
   可能性を検討する（同一コード・同一ティッカーでもクラウド環境からは
   失敗し、別環境からは成功することがある）

データソース自体に確かにデータがあるにも関わらず取得が失敗する場合は、
「外部要因だから仕方ない」ではなく、取得経路の変更（代替API・リトライ・
レート制限対策等）を検討する。

**⑤ 「値が変化しない」症状はfetch失敗だけが原因とは限らない（MACRO-NFP-1の教訓）**

同一値が連続する場合、fetch失敗・staleキャッシュだけでなく、格納している値の
意味論自体が想定と異なっている（水準 vs 差分、絶対値 vs 増減率等）ケースも疑う。
表示側の丸め処理（例：`/1000`表示）が微小な変動を吸収して「同一値」に見せている
可能性も確認する。

（2026-07-07事例: MACRO PULSEのNFPがFRED PAYEMSの雇用者数**水準**をそのまま
格納しており、本来の「前月比新規雇用者数」になっていなかった。fetchは正常に
成功していたため、①〜④の調査だけでは「正常」に見えてしまうパターンだった）

### パイプラインコード変更時の追加手順

以下のファイルを変更した場合は、コミット前に影響銘柄を特定して再生成する。

**対象ファイル（変更したら必ず監査を実行）：**
- `common/sec_data/quarterly.py`
- `common/sec_data/normalizer.py`
- `common/sec_data/ttm_calculator.py`
- `common/sec_data/parser.py`
- `src/value/tanuki_valuation/calculator/rice.py`
- `src/value/tanuki_valuation/core_calculator.py`

**手順：**

```bash
# Step 1: データ品質監査（影響銘柄を特定）
python common/sec_data/audit.py

# Step 2: quarterly.py / normalizer.py / ttm_calculator.py を変更した場合
python common/sec_data/update.py [影響銘柄]

# Step 3: rice.py / core_calculator.py を変更した場合
#   → TTMデータ変更なし。影響銘柄のパイプラインのみ再実行
python src/value/tanuki_valuation/pipeline.py [影響銘柄]

# Step 4: 再監査で問題消滅を確認
python common/sec_data/audit.py
```

**影響銘柄の特定方法（rice.py変更時）：**
全銘柄 TTM を走査して変更前後の Q 値を比較するスクリプトを都度作成するか、
変更内容から論理的に対象銘柄を絞り込む（例：ni < 0 チェック追加 → 赤字年が含まれる銘柄）。

**全銘柄再生成後の必須検証：**
```bash
python common/sec_data/report_consistency_check.py
# NG=0 を確認してからコミットする
# WARN は内容確認の上、対処が必要なもののみ修正する
```

**年度キー・年度割り当てに関わる変更時の追加検証（PARSER-1の教訓・必須）：**

`parser.py` の年次辞書キーや年度割り当てロジックを変更した場合、
pytest と test_iv_formula が全通過しても**過去年度データの破壊を見逃す**。
（2026-06-13 事例: 年次キーを fy→end_date年 に変更した際、INTU FY2019 revenue が
10-K内Q1比較値 $1.16B で通年値 $6.78B を上書きする regression が発生したが、
式の整合テストでは検出できなかった）

そのため以下を必須とする:
```bash
# 変更前後で annual_YYYY.json の主要系列が変わった銘柄を全件抽出
#   対象フィールド: revenue / net_income / fcf / total_debt
#   特に non-December 決算企業（AAPL/MSFT/NVDA/CRM/ELF/HQY/COHR/INTU等）と
#   上場直後・SPAC銘柄は FY 10-K 内の他時点比較値が混入しやすい
```
- 差分が出た銘柄は 10-K 実績との一致を 3 銘柄以上スポットチェックする
- IV/FCF_Base/CAGR が動いた銘柄を一覧化する（直近5年系列が変われば波及する）
- **「テスト全通過」は年度割り当ての正しさを保証しない**ことを前提に、
  必ず before/after の全件差分で担保してからコミットする

**aggregate_annual を変更した場合の追加確認（ANNUAL-FY-1の教訓）：**

`aggregate_annual`（EPS Analyzer pipeline.py）のグループ化ロジックを変更した場合、
IV に直接影響する `estimate_fcf_from_eps` 経由の波及が起きる。
（2026-06-13 事例: filing_date[:4] → fiscal_year に変更した際、
NVDA +18% / MSFT -12% / AVAV +93% / IOT applied=False→True 等、20銘柄のIVが変化）

そのため以下を必須とする:
- `adjustments.py の estimate_fcf_from_eps` が参照する `annual.json years[0]` の
  adjusted_net_income が変わった銘柄を全件抽出する
- IOT等の applied=False→True の変化（赤字→黒字化）は特に要注意:
  本物の黒字化なら許容、ゼロ近傍アーティファクトならゲート閾値を見直す
- **年度判定は `common/sec_data/utils.py` の `determine_fiscal_year()` に統一済み**（ARCH-DATA-1-FY 2026-06-25完了）:
  parser.py・extract_key_facts.py・aggregate_annual の3箇所が同関数を参照。
  変更する際は `determine_fiscal_year()` のみを修正し、3箇所で矛盾が生じないか確認すること。

---

## 重要ルール

### pipeline.py 実行時のAPI費用管理

- risk_fetcher.py（Grok API呼び出し）は全銘柄実行でAPIコストが発生する
- 手動実行時は原則 --skip-risk を付けること
  例: python src/value/tanuki_valuation/pipeline.py AAPL --skip-risk
- 全銘柄の risk_events 更新は GitHub Actions 週次自動実行に任せる
- 新規銘柄登録時の初回生成も --skip-risk 推奨（登録後に Actions が自動取得）

### AI APIキー管理ルール

- システム全体のAI APIはxAI（XAI_API_KEY）に統一されている
- 新規AI API呼び出しを実装する際は必ずGrok（`api.x.ai/v1/chat/completions`）を使用すること
- モデルはフォールバック方式：`["grok-3-mini", "grok-3", "grok-2-1212"]` の順で試行
- GeminiやOpenAI等の別APIを使用しているコードを発見した場合はGrokに移行すること

### 財務指標計算における期ズレ防止ルール（BUG-NETDEBT-5の教訓）

Net Debt 等、複数の BS 項目（Cash / ST_Invest / Debt）を組み合わせて計算する場合、
**すべての項目が同一決算期（同じ as-of 日）から取得されていること**を確認する。

- **NG例**: Cash は最新四半期（Q1 2026）・ST_Invest は年次（FY2025）から混在取得
- **OK例**: Cash・ST_Invest・Debt のすべてを同じ四半期 bs から取得

**normalized JSON にフィールドが存在しない項目は自動上書き経路から漏れやすい。**
BUG-NETDEBT-1 で Cash は自動更新されても、ShortTermInvestments がない場合は
ST_Invest が年次のまま取り残される（→ BUG-NETDEBT-5 で修正済み）。
新たに BS 項目を追加するときも同様のズレが起きないか確認すること。

### レポート定義の明示ルール（外部AIレビュー誤指摘の予防）

外部 AI が「計算がおかしい」と指摘するパターンのうち、設計仕様として明示化しておくもの：

- **FCF_History の CapEx 定義**: 素の OCF − PP&E 購入（Capitalized Software 除く・FinanceLease 除外）。
  R&D 資本化補正・maintenance CapEx 分離は FCF_Base にのみ反映し、FCF_History には乗せない。
  外部 AI が「CapEx が過少だ」と指摘してきた場合は FCF_Base との差分を確認してから判断する。
- **OperatingLeaseLiability は Total_Debt に含めない**: ASC 842 オペレーティングリースは
  利付き借入（金融負債）ではなく将来リース支払義務。IONQ の $30M 等は意図的に除外。
  EV 計算にリースを含める「アジャステッド EV」方式を採用する場合は設計変更として明示すること。
- **DCF構成要素は「上から足すと必ずIVになる」構造で表示する（REPORT-6拡張の教訓・必須）**:
  外部AIは report.txt のDCF項目を順に足してIVを逆算する。途中の段（特に α 乗算）が
  非表示だと「IV再現不能」と誤指摘される（2026-06-13: α≒0の小型株では偶然近似でき、
  α=1.0のメガキャップで一斉に破綻が顕在化）。DCFブロックは必ず次の順序で全段を表示する:
  `DCF_FCF_PV → DCF_TV_PV → DCF_v0(=PV合計) → Alpha_Premium → DCF_v0_x_alpha(=v0×(1+α))
   → RPO_PV → Growth_Option_PV → Equity_Value(=上記−Net_Debt、優先株があれば控除行追加)
   → Shares_Used(source明記) → Intrinsic_Value`。
  DCF構成要素を追加・変更する際は test_iv_formula.py で「表示項目を積み上げてIVに一致」を
  必ず回帰テストすること。
- **DCF_Reliability=LOW の判定仕様（Policy A・明文化済み）**:
  FCF実績マイナスで revenue_floor 適用時は DCF_Reliability=LOW とし、IVは参考値扱い。
  TANUKI SCORE 分類は BUY/TRIM/HOLD/WATCH → **WATCH に丸める**（SELL/PASS は維持）。
  乖離率は表示するが分類判定には使用しない。この仕様を変更する場合は CRWV/SOUN/RKLB/JOBY/CEG 等
  該当銘柄への影響を確認すること。
- **RICE 定義式は実装に一致させる**: 表示する定義式は `(G × VC_Factor × Q × CF) / WACC`。
  VC_Factor を式本体から省くと外部AIが「定義と計算値が2倍ずれる」と誤指摘する（注記バグ）。
- **FCF_Conversion_Rate は Adj_NI への変換率であり OCF→FCF 変換率ではない**: 高FCFマージン企業
  （ADBE/PLTR等）では実績FCFを下回るが、これは正常化前提による保守設計。定義文に明記する。
- **IV割引率（Rm=10%/β=0）は市場リスクを意図的に除外した本源価値**: 高β銘柄では市場WACC比で
  IVが高めに出るが設計通り。市場リスク調整後の参照は WACC_CAPM_Reference でのIVを併用する旨を
  定義文に記載（外部AIは「高β銘柄でIV過大」を頻繁に誤指摘するため）。
- **ROE=N/A（負債超過）表示仕様**: 全年度で株主資本≤0の銘柄（PM/TSLA等）は ROE=0% ではなく
  ROE=N/A（負債超過）と表示する。`reader.py get_roe_avg_detail` が `(None, 0, False)` を返し、
  `pipeline.py` が `roe_years_used==0` をシグナルとして N/A 表示に切り替える仕様。
  `roe_avg or 0.0` のような OR 短絡評価は None を 0.0 に変換するため禁止（ROE-ZERO-1の教訓）。
- **industry_alpha_caps 方針**: セクター別 `_alpha_caps` よりも業種別 `_industry_alpha_caps` を優先する。
  同一セクター内で業種差が大きい場合（例: Communication Services 内の Telecom Services）に使用。
  `core_calculator.py` でのチェック順は `_mega_tech_tickers` → `_industry_alpha_caps` → `_alpha_caps`。
  新銘柄でαが過大になる場合は業種名（yfinance `info.industry`）を確認してから設定すること。
- **FCF外れ値の除外方向性ルール（FCF-OUTLIER-1の教訓）**: 上方乖離（latest_fcf > 5yr_avg）の場合、
  一過性コスト（impairment等）が検出されても `transient_explains=False` とし FCF を除外しない。
  一過性コストは FCF を下げる方向に働くため、FCF が高い年に一過性コストがあれば
  「コストがなければさらに高かった」ことを意味し、除外の根拠にならない。
  除外が許可されるのは下方乖離（latest_fcf < 0 か latest_fcf < 5yr_avg）のみ。
- **比較表示する2つの倍率は必ず同一期ベースで計算する（EPS-PER-TTM-1の教訓）**:
  GAAP PER（yfinance trailingPE = TTM）と Adjusted_EPS_PER を並べる場合、
  後者も同じTTM（直近4四半期の adjusted_eps 合計）を分母にしなければ比較が無意味になる。
  年次FYを使うとGAAP（TTM）と期間が食い違い、成長株では ADJ > GAAP の逆転が常態化する
  （実例: NVDA 48.3x vs GAAP 31.4x → TTM統一後 30.3x に正常化）。
  新たにPER・EV・PS等の倍率を並列表示する場合は、両者の分母期間が同一か必ず確認すること。
  片方が TTM なら他方も TTM、片方が NTM（Forward）なら他方も NTM に揃える。

### 外部AIレビューの活用と品質還元ループ

大きな修正後は `report.txt` を外部 AI（Grok / Claude 等）に敬対的レビューさせることで
ロジックバグを早期に発見できる。

**レビューの仕分けルール（指摘 → 分類 → 対応）：**
1. **本物のバグ**: 再現可能な計算誤り → 修正 → `report_consistency_check.py` に検出項目を追加して恒久化
2. **設計仕様**: 意図的なモデル選択（FCF_Base方式・OperatingLease除外等）→ 定義文を明記して予防
3. **外部データ差**: AI の学習データと XBRL 値の差 → 一次ソース（SEC EDGAR）で照合して判定

**サンプル選定のコツ:**
- 主力9銘柄だけでなく、消費セクター・金融・赤字初期（IONQ/JOBY等）をセクター横断でかけると
  属性固有のバグ（SPAC誤タグ・金融収益混入・CAGR過大等）が出やすい。
- 成熟・ディフェンシブセクター（通信: VZ/T、公益: CEG/VST、タバコ: PM/MO等）を含めると
  ROE=N/A（負債超過）/ alpha上限抵触 / FCF外れ値 等の設計端ケースを検出しやすい。

### 自動生成データファイルのgit管理ルール

- `docs/` 以下の自動生成JSON/CSVは `.gitattributes` で `merge=ours` 設定済み
- `git pull --rebase` でコンフリクトが発生した場合、対象データファイルは自動でローカル版が採用される
- 新たに自動生成データファイルを追加した場合は `.gitattributes` にも追記すること
  （対象: `docs/market-monitor/`, `docs/portfolio/tail/data/`, `docs/value-monitor/tanuki_valuation/data/`）
- **`git checkout --theirs` をデータファイルに使用してはならない**
  （JSONが古いリモート版で上書きされデータが消失する）

### 表示期間フィルタのルール

- HTMLの日付フィルタ（`getDate()-N`）は指標の更新頻度に合わせて設定すること
- 月次指標を含むセクションは最低90日以上を確保すること（14日では月次指標が表示されない）

---

## BACKLOG優先順位の目安

### 今すぐ着手可能（優先度中・難易度低〜中）
- MP-BIZDAY-1: MARKET PULSE営業日ベース化
- ARCH-DATA-1: SECデータ正規化レイヤー強化（PARSER-1/BUG-NETDEBT-6/ANNUAL-FY-1が第一〜三歩として完了。
  次の前倒し対象: 年度判定の共通関数化（parser.py/extract_key_facts.py/aggregate_annualの3箇所を統合））

### 順次着手（優先度中・難易度中〜高）
- TSCORE-TRAP-1: 投資トラップ検出（10種+逆シグナル）
- SEC-CTRL-1: 内部統制評価（Item4/9A・実装先はTANUKI TAIL有力）
- TANUKI-FIN-1: 金融株DDM対応

### 着手条件あり
- DESIGN-15: 期待と理論価格の整理（DESIGN-4・5の設計確定後）
- Moomoo API Skill移行（signal.jsonバックテスト実施後）
- Moomoo API系4件（クォータ回復後）

---

## 新規銘柄登録時の必須手順

cik_lookup.csv に新規銘柄を追加した後、以下を必ず実行すること。

```bash
# Step 0: カナダ企業チェック（登録前に必ず実行）
python -c "import yfinance as yf; t = yf.Ticker('[TICKER]'); print(t.info.get('country', 'N/A'))"
# 出力が "Canada" の場合は登録を中止する。
# カナダ企業はIFRS/40-Fのため TANUKI VALUATION・EPS Analyzerに非対応。

# Step 0.5: 登録メタデータの記録（必須・Step 1の前に実施）
# cik_lookup.csv の新規行に以下4項目を記録してからStep 1に進むこと：
#   status: 指示書内で明示されていればその値を使用。
#     明示がなければ status=candidate をデフォルトとし、
#     「明示的にactiveへ変更する指示がない限りcandidateのまま」と報告に明記する。
#   registered_date: 作業実行日（本日の日付、YYYY-MM-DD）
#   registration_source: 指示書内で明示されていればその値を使用。
#     不明な場合は manual_thesis をデフォルトとする。
#     （定型カテゴリ例: moomoo_screening / manual_thesis / catalyst_discovery /
#      satellite_watch / initial_setup / technical_screening / unknown）
#   registration_note: 指示書内の登録理由・経緯を1〜2文で要約して記録。
#     指示書に理由が書かれていない場合は、Claude Codeから
#     「登録理由が指示書に見当たりません。記録すべき経緯を教えてください」と
#     確認を求め、回答を得てから記録する。

# Step 1: SEC データ取得
python common/sec_data/update.py [TICKER]

# Step 2: β を yfinance から自動取得して beta_config.json に登録
python src/value/tanuki_valuation/beta_fetcher.py [TICKER]

# Step 3: TANUKI VALUATION パイプライン実行
python src/value/tanuki_valuation/pipeline.py [TICKER]

# Step 3.5: セグメント設定（SEGMENT-1ルール準拠）
# ASC 280 の formal operating segment 数を 10-K で確認し、以下のルールで判断する：
#
# LLY型（設定不要）: formal segment が1つ → General 100%のままでOK、このステップをスキップ
# LMT型（設定対象）: formal segment が2つ以上 → 以下を実施：
#   1. 10-K の "Segment Information"（ASC 280）セクションで各セグメントの売上比率を確認
#   2. 各セグメントの過去YoYとガイダンスを参考にgrowth rateを設定
#   3. config/segment_config.json に比率・成長率・根拠コメントを記録
#   4. pipeline.py を再実行してIV before/afterを確認・記録
#
# 注意: 製品別・エンドマーケット別の disaggregated revenue（ASC 606）は
#       formal segment ではないため使用しない（VST/CEGの失敗事例参照）

# Step 4: データ品質確認（β設定含む）
python common/sec_data/audit.py [TICKER] --check-beta

# Step 5: HypeCore 実行
python src/value/hypecore/hypecore.py --batch [TICKER]
# 失敗した場合はログを確認。データ不足銘柄（上場直後等）は失敗することがある。

# Step 5b: EPS Analyzer 実行（cik_lookup.csv の eps=true 銘柄のみ）
python -m src.value.adjusted_eps_analyzer.pipeline --ticker [TICKER]
# eps=false の銘柄はスキップ（XBRL非対応・上場直後等）
# "データなし"で失敗する場合は cik_lookup.csv の eps 列を false に設定する

# Step 6: Discover 監視リストに追加
python3 -c "
import json, shutil
from datetime import date
ticker = '[TICKER]'
with open('config/discover_config.json', encoding='utf-8') as f:
    config = json.load(f)
if ticker not in config.get('tickers', {}):
    config['tickers'][ticker] = {'category': '監視中', 'memo': '', 'themes': []}
    config['last_updated'] = str(date.today())
    with open('config/discover_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    shutil.copy('config/discover_config.json', 'docs/portfolio/data/discover_config.json')
    print(f'{ticker} をDiscover監視リストに追加しました')
else:
    print(f'{ticker} はすでに登録済みです')
"

# Step 7: monitor_tickers.yaml に追加（SEC定期更新・EPS Analyzer・admin.html の対象）
python3 -c "
ticker = '[TICKER]'
with open('config/monitor_tickers.yaml', encoding='utf-8') as f:
    content = f.read()
existing = {l.strip().lstrip('- ') for l in content.splitlines() if l.strip().startswith('- ')}
if ticker not in existing:
    with open('config/monitor_tickers.yaml', 'a', encoding='utf-8') as f:
        f.write(f'  - {ticker}\n')
    print(f'{ticker} を monitor_tickers.yaml に追加しました')
else:
    print(f'{ticker} はすでに登録済みです')
"

# Step 8: 登録パイプライン健全性チェック（必須）
python common/sec_data/registration_validator.py [TICKER]
# NG=0 を確認してからコミットする。
# WARN は内容を確認して対処が必要なもののみ対応する（上場直後の SEC 件数不足は許容）。
```

**Step 8.5: 対象システム横断チェック（必須・XBRL-TAG-KLAC-1-FOLLOWUP 2026-07-09新設）**

Step 1〜8はシステム個別の登録手順だが、「意図した通りに対象/対象外が
振り分けられているか」を横断で確認する項目がなかったため、Step 5
（HypeCore）の実行漏れが後から発覚する事例が発生した。以下を確認する：

- [ ] TANUKI VALUATION（tanuki）/ HypeCore（hypecore）/
      EPS Analyzer（eps）/ STONKS SILO（stonks_silo）—
      cik_lookup.csvの4フラグが業態と整合しているか
      （例: 黒字大型株なのにstonks_silo=trueになっていないか、
      hypecore=trueなのに実データ`docs/value-monitor/hypecore/data/{TICKER}_poc.json`
      が生成されていないか）
- [ ] segment_config.json — ASC 280 formal segment数を確認し
      LMT型（2segment以上）なら登録済みか（Step 3.5参照）
- [ ] rpo_config.json — SaaS/クラウド業態ならwhitelist登録済みか
- [ ] TANUKI TAIL — 保有ポジションでない限り登録しない
      （誤操作防止の注意書き。thesis.json等を新規登録手順の
      一環として作成しないこと）

**注意事項：**
- Step 2 を忘れると β=未設定のまま yfinance の raw 値が使われる
- 異常値が疑われる場合は `--dry-run` で差分確認してから適用
- LMT 等 Damodaran 手動設定銘柄は `beta_fetcher.py` の `DAMODARAN_OVERRIDES` に追加
- Step 5 HypeCore は yfinance 依存。KULR 等データ不足銘柄は失敗するが無視してよい
- Step 5b EPS Analyzer: 非US GAAP（IFRS系外国企業、例: ASML）は us-gaap タグが欠如しているため
  update.py で annual データ 0 件になる。その場合は cik_lookup.csv の eps 列を false に設定すること。
  XBRL形式が US GAAP でも NetIncomeLoss の四半期データが欠損している銘柄（BKNG, FCX 等）も
  同様に eps=false を設定する。
  ※ NetIncomeLoss が古いデータしか持たない場合は ProfitLoss タグへ自動フォールバックする（SCCO対応 2026-06-15）。
    タグ選択ロジック: 「最初に見つかったタグ」→「最新エントリが最も新しいタグを優先」（extract_key_facts.py）

**EPS Analyzer 設計ルール（2026-06-15 更新）：**
- **ProfitLoss フォールバック（extract_key_facts.py）**: NetIncomeLoss が 5年以上古い場合、ProfitLoss タグへ
  自動フォールバック。タグ選択は「最新エントリが最も新しいタグ優先」ロジック。対象: SCCO 等の再編企業
- **DTA 自動補正（pipeline.py `apply_dta_adjustments()`）**: 繰延税金資産（DTA）認識による adj_eps 異常高値を
  自動検出・補正。
  - Type-A: `pretax ≤ 0 かつ NI > 0`（損失→DTA還付で黒字化） ← LYFT Q4 2025 型
  - Type-B: `NI > pretax × 3`（黒字にDTAが上乗せ）
  - 補正値: `adjusted_net = pretax - median(正常四半期の税費用)`
- **split_history.yaml 管理**: 株式分割が確認された銘柄は `config/split_history.yaml` に追記する。
  現在登録済み: NOW（2025-12-18 5:1）。追記後は EPS Analyzer を単体実行して TTM adj_eps を確認すること。
- Step 6 の discover_config.json は **dict 形式**（キー=ticker）。list 形式のコードは誤り
- Step 7 の monitor_tickers.yaml は **単純リスト形式**（yaml.dump 使用不可 → コメントが消える）
- Step 8 の NG は必ず解消してからコミットする。主なNG要因:
  - `P2-A NG`: latest_revenue が TTM の 3 倍以上乖離 → SEC パーサーのタグ確認
  - `P1-Step3 NG`: latest.json 未生成 → pipeline.py を再実行
  - `P1-Step7 NG`: monitor_tickers 未登録 → Step 7 を再確認
- SaaS系銘柄でRPOプレミアムを適用する場合は `config/rpo_config.json` の
  whitelist に理由コメント付きで明示登録する（industry keyword 依存禁止）
  理由: keyword は将来銘柄追加時に意図しない適用の再発リスクあり（GOOGL等参照）

**新規銘柄のセグメント設定判断ルール（SEGMENT-1 全17銘柄完了の教訓）：**

segment_config.json の設定要否は **ASC 280 の formal operating segment 数** で判断する。
製品別・エンドマーケット別の売上開示（disaggregated revenue）は **formal segment ではない**。

| 判定 | 条件 | 設定 | 例 |
|------|------|------|-----|
| LLY型（設定不要） | formal segment が1つ | General 100%のまま | LLY/MRVL/BSY/ALAB/ELF |
| LMT型（設定対象） | formal segment が2つ以上 | 比率・成長率を設定 | LMT/AMAT/VRT/COHR/LITE |

設定する際の注意:
- セグメントの名称・比率は 10-K の **"Segment Information"（ASC 280）** セクションの数値を使う
- 製品別や顧客別の disaggregated revenue（ASC 606）は使わない（VST/CEGで架空セグメントを埋めた失敗参照）
- **growth rate の設定根拠を segment_config.json の comment フィールドに記録する**
  （例: "FY2024 YoY +13%、中期ガイダンス考慮で10%設定"）
- weighted_growth が recommended_g より大幅に高い場合はIV上昇（LMT +12%型）、
  低い場合はIV下落（COHR -57%型）。どちらも「正しい是正」だが before/after を記録すること
- COHR/LITEのような光通信デバイス・M&A統合後の銘柄は rec_g が急成長TTMを引いて過大になりやすい。
  設定後のIV下落が大きい（-50%超）場合でも、長期成長率として妥当なら正しい是正

---

## よく使うコマンド

### 単体テスト実行
python src/value/tanuki_valuation/pipeline.py NVDA

### 全銘柄再生成
python src/value/tanuki_valuation/pipeline.py

### pytest実行
python -m pytest tests/test_pipeline_logic.py -v

### GitHub Actions 確認
admin.html の「実行」タブ → 一括更新ボタンを使用

---

## TANUKI TAIL 銘柄追加手順

TANUKI TAIL（長期投資テーゼ管理）に新規銘柄を追加する場合、
以下の順序で実施すること。

```bash
# Step T1: TANUKI TAILページでテーゼ登録（UIで実施）
#   → docs/portfolio/tail/data/positions/{TICKER}_thesis.json が生成される

# Step T2: KPI提案生成（Grok）
python src/tail/kpi_proposer.py --ticker {TICKER}
# → docs/portfolio/tail/data/kpi_proposals/{ticker}_proposal.json 生成
# → tail_kpi_map.json に auto_fetchable=true 分が自動追記

# Step T3: TANUKI TAILページでKPI確定（UIで実施）
#   → thesis.json の kpis フィールドにKPIが保存される
#   → 「⚠ KPI未設定」バッジが消える

# Step T4: XBRL セグメントデータ取得（layer2）
python src/tail/xbrl_segment_fetcher.py --ticker {TICKER}
# → docs/portfolio/tail/data/kpi/{ticker}_layer2.json 生成

# Step T5: テキストKPI抽出（layer3）
python src/tail/text_kpi_extractor.py --ticker {TICKER}
# → docs/portfolio/tail/data/kpi/{ticker}_layer3.json 生成
# → auto_fetchable=false のKPIを10-Q MD&A + 8-K EX-99.1 から抽出

# Step T6: コミット
git add docs/portfolio/tail/data/kpi_proposals/ \
        docs/portfolio/tail/data/tail_kpi_map.json \
        docs/portfolio/tail/data/kpi/
git commit -m "feat: TANUKI TAIL {TICKER} 銘柄追加 layer2/layer3 初期データ"
git pull --rebase origin kaihatsu
git push origin kaihatsu
```

**Step T6以降**: 次回RSS検知時（EDGAR 10-Q/10-K 提出）から四半期レビューが自動生成される。

**注意事項:**
- Step T2 は thesis.type="core" の銘柄のみ対象（satellite銘柄はスキップ）
- Step T5 が失敗した場合（EX-99.1未発見等）でも Step T6 に進んでよい
  → レビュー生成時に layer3 未取得KPIは「— 未取得」と表示される
- CIK が cik_lookup.csv にない場合、Step T2/T4/T5 前に追加すること:
  `echo "{TICKER},{CIK},{会社名},,,true,true,true" >> config/cik_lookup.csv`

---

## 銘柄削除時の必須手順

### 削除対象の判断基準
- 投資対象として見込みがなくなった銘柄
- 上場廃止・買収・合併により追跡不要になった銘柄
- リポジトリサイズ管理のため（目安：100銘柄を超えたら低優先銘柄を削除）

### 削除手順

```bash
# Step 1: 削除対象を確認
grep [TICKER] config/cik_lookup.csv
grep [TICKER] config/discover_config.json

# Step 2: 設定ファイルから削除
# cik_lookup.csv から該当行を削除
grep -v "^[TICKER]," config/cik_lookup.csv > /tmp/cik_tmp.csv
mv /tmp/cik_tmp.csv config/cik_lookup.csv

# beta_config.json から削除
python3 -c "
import json
with open('config/beta_config.json') as f:
    d = json.load(f)
d.get('overrides', {}).pop('[TICKER]', None)
with open('config/beta_config.json', 'w') as f:
    json.dump(d, f, indent=2)
"

# discover_config.json から削除
python3 -c "
import json, shutil
with open('config/discover_config.json') as f:
    d = json.load(f)
d['tickers'] = {k: v for k, v in d['tickers'].items() if k != '[TICKER]'}
with open('config/discover_config.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
shutil.copy('config/discover_config.json',
            'docs/portfolio/data/discover_config.json')
"

# monitor_tickers.yaml から削除
python3 -c "
ticker = '[TICKER]'
with open('config/monitor_tickers.yaml', encoding='utf-8') as f:
    lines = f.readlines()
lines = [l for l in lines if l.strip() != f'- {ticker}']
with open('config/monitor_tickers.yaml', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f'{ticker} を monitor_tickers.yaml から削除しました')
"

# Step 3: データファイルを削除
rm -rf common/sec_data/data/[TICKER]
rm -f common/sec_data/normalized/[TICKER]_quarterly_normalized.json
rm -f common/sec_data/raw/[TICKER]_quarterly_raw.json
rm -f common/sec_data/ttm/[TICKER]_ttm_series.json
rm -rf docs/value-monitor/tanuki_valuation/data/[TICKER]
rm -f docs/value-monitor/hypecore/data/[TICKER]_poc.json
rm -rf docs/value-monitor/adjusted_eps_analyzer/data/[TICKER]

# Step 4: 健全性チェックで不整合がないことを確認
python common/system_health.py

# Step 5: コミット
git add -A
git commit -m "chore: [TICKER] 銘柄削除"
git pull --rebase origin kaihatsu
git push origin kaihatsu
```

---

## 作業完了時のチェックリスト

- [ ] pytest 全件パス
- [ ] 単体テストで動作確認
- [ ] 全銘柄再生成で成功率確認
- [ ] **`python common/sec_data/report_consistency_check.py` を実行し NG=0 を確認**
  - 現行チェック項目（CHECK-1〜19 + STALE-CHECK-1）:
    CHECK-1:FCF符号矛盾 / CHECK-2:DCF_Reliability欠落 / CHECK-3:LOW丸め / CHECK-4:割引率2段 /
    CHECK-5:NetDebt旧表示 / CHECK-6:負PER / CHECK-7:RPO条件 / CHECK-8:Matrix④高FCFラベル赤字 /
    CHECK-9:セグメント鮮度 / CHECK-10:PS異常値 / CHECK-11:Revenue孤立年 / CHECK-12:Cash-STI期ズレ /
    CHECK-13:RICE負値ラベル / CHECK-14:EPS>株価50% / CHECK-15:EPS>株価 / CHECK-16:TTM四半期不足 /
    CHECK-17:EPS全値$0 / CHECK-18:G=15%未調整 / CHECK-19:SEC株数=0
    ※ STALE-CHECK-1（決算後未更新）は未実装。BACKLOG [STALE-CHECK-1-IMPL] 参照。
  - **新種バグを修正したら同スクリプトに検出項目を追加して恒久化する**
- [ ] HTMLファイルを新規作成・移設・削除した場合は `python ~/check_links.py` でリンク切れ0件を確認
- [ ] **新規計算フィールドを追加した場合**: report_consistency_check.pyに対応CHECKを追加（追加できない場合はBACKLOGにCHECK-COVERAGE-Nとして登録）
- [ ] **新規フィールド・指標を追加した場合**: 同一指標を表示する全画面をgrepで確認し全画面への反映を確認してから完了宣言する
- [ ] **機能を廃止した場合**: 全HTML・全Pythonで残骸をgrepで確認する
- [ ] **複数銘柄への適用が必要な処理**: 全対象銘柄への実行完了を確認する
- [ ] BACKLOG.mdから該当項目を削除し、BACKLOG_DONE.mdに完了記録を移動
- [ ] コミット・プッシュ完了

---

## 月次メンテナンスタスク（月初の作業開始時に実施）

### フロントエンド表示内容の最新性確認

以下を確認し、実態と乖離している箇所を修正する：

**① 各画面のタイトル・サブタイトル・説明文**
- 機能追加後に説明文が古いままになっていないか
- 廃止した機能の説明が残っていないか

**② ツールチップ・凡例・ラベル**
- スコアリング基準やフェーズ定義の変更がUIに反映されているか
- 単位・計算式の説明が実装と一致しているか

**③ CLAUDE_CODE_START.md 自体の内容**
- よく使うコマンドが現在の構成と一致しているか
- 登録銘柄数・ファイルパス等の記載が最新か
- 新規銘柄登録手順・削除手順のステップが実態と一致しているか
- 手順を実際に実施した際に漏れ・誤りがあれば即座に手順書を更新する
  （気づいた時点で更新・次回以降に先送りしない）
- BACKLOG優先順位の目安が BACKLOG.md の実態と一致しているか
  （完了済み項目が残っていないか）

**④ SYSTEM_MAP.md の更新確認**
以下のいずれかに該当する作業を行った場合は必ずSYSTEM_MAP.mdを更新する：
- 新規ファイル・モジュールを追加した
- 既存ファイルの役割・出力先が変わった
- システム間の依存関係が変わった
- 新規銘柄登録でパイプライン対象が増えた

月次メンテナンス時にも全体を通読して陳腐化がないか確認する。

**⑤ 横断整合性チェック（PREVENT-5）**
以下を実行して不整合を検出する：
- cik_lookup.csv vs 全config（segment/maturity/beta）の銘柄整合性確認
- glossary.jsonのdata-info属性カバレッジ確認（HTML未使用キーがないか）
- console.log残存チェック（本番コードに残っていないか）
- system_health.py の実行（全チェックがHEALTHYか確認）
整合性問題が見つかった場合はその場でBACKLOGに登録する。

確認後、修正があればコミット：
```bash
git add docs/
git commit -m "docs: 月次フロントエンド表示内容の最新化"
git pull --rebase origin kaihatsu
git push origin kaihatsu
```

---

## BACKLOG管理ルール

### BACKLOGファイルの場所
- アクティブな課題: BACKLOG.md（TANUKI VALUATION系+システム全体を統合）
- 完了済みアーカイブ: BACKLOG_DONE.md
- Step 1 で読むのは BACKLOG.md のみ。BACKLOG_DONE.md は
  過去の実装経緯を調べる必要があるときだけ参照する
- 編集前に必ず grep で行を特定してから変更する（行番号の直接指定は禁止）

### BACKLOG更新のタイミング
- タスク完了後、メモリではなくファイルに記録する
- 完了時の手順:
  ① BACKLOG.md から該当項目を削除
  ② BACKLOG_DONE.md の該当日付セクション（なければ新設・新しい日付が上）に
     `✅ [XX-N] タスク名（YYYY-MM-DD 完了）` として移動
  ③ 実装内容を箇条書きで3行以内に要約して残す
- 新規課題の追加は BACKLOG.md の該当優先度セクションへ

### コミットルール（BACKLOG更新時）
git add BACKLOG.md BACKLOG_DONE.md
git commit -m "docs: [タスクID] 完了済みに更新"
git pull --rebase origin kaihatsu
git push origin kaihatsu

---

## Market Pulse プロンプト修正時の注意

対象ファイル: src/market/market_pulse/collect_and_send.py

修正時に必ず確認すること：
- 出来高比はS&P500/NASDAQを個別表記（まとめ表現禁止）
- 債券バッジは「債券売り/債券買い」（「リスクオン/オフ」は禁止）
- HYG・LQD同時下落は「信用収縮」禁止→「金利上昇圧力」に限定
- 乖離Zスコアの符号：正=NASDAQ優位 / 負=S&P500優位

修正後は index.html のバッジ表示との整合性も確認すること。

---

## Market Pulse CSV列追加時の注意（MP-HISTORY-FIX / MP-PRED-FIX の教訓）

対象: collect_and_send.py に新しい指標列を追加するとき

### 必須確認手順

**列追加後は必ず以下を実行すること：**

```bash
# 1. ヘッダー列数と最新行の列数が一致しているか確認
python3 -c "
import csv
with open('docs/market-monitor/market-pulse/data/market_data.csv') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)
    print(f'ヘッダー列数: {len(header)}')
    for row in rows[-3:]:
        print(f'データ列数: {len(row)}  (日付: {row[0]})')
"

# 2. 主要フィールドの値域チェック
python3 -c "
import json
with open('docs/market-monitor/market-pulse/data/market_data.json') as f:
    data = json.load(f)
for entry in data[-5:]:
    ind = entry.get('indicators', {})
    sp = (ind.get('S&P500') or {}).get('value', '?')
    score = (entry.get('sentiment') or {}).get('score', '?')
    print(f\"{entry['date'][:10]}: S&P500={sp}, score={score}\")
"
```

**正常値の目安：**
- `S&P500.value`: 3000〜15000 の範囲（0.08 等の小数は列ズレ）
- `sentiment.score`: 0〜100 の範囲（負値・100超は異常）
- `sentiment.label`: EXTREME FEAR / FEAR / CAUTION / NEUTRAL / GREED / EXTREME GREED のいずれか

### CSV列追加後の必須ゲートチェック

**列追加・collect_and_send.py 実行後に必ず実行すること：**

```python
python3 -c "
import csv
with open('docs/market-monitor/market-pulse/data/market_data.csv') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)
    header_len = len(header)
    errors = []
    for i, row in enumerate(rows):
        if len(row) != header_len:
            errors.append(f'行{i+2}: {len(row)}列 (ヘッダー{header_len}列)')
    if errors:
        print('❌ 列数不一致:')
        for e in errors: print(' ', e)
    else:
        print(f'✅ 全{len(rows)}行 列数一致（{header_len}列）')
"
```

✅ が出ること。❌ が出た場合は以下の対処へ。

### 列ズレが発生した場合の対処
1. CSV の旧行（列追加前）と新ヘッダーの列数差を確認
2. ずれた列数分だけオフセットした正しいフィールドを特定
3. market_data.json の異常期間エントリを CSV 生データから再構築
4. index.html 側の計算ロジックに防衛チェックを追加

---

## リンク整合性チェック（HTMLファイルを新規作成・移設・削除した場合は必須）

```bash
python ~/check_links.py
```

リンク切れが0件であることを確認してからコミットすること。
スクリプトが存在しない場合は以下で再作成：

```python
# ~/check_links.py
import os, re
from pathlib import Path

DOCS_ROOT = Path("docs")
html_files = sorted(DOCS_ROOT.rglob("*.html"))

PATTERNS = [
    r'href=["\']([^"\'#?]+)["\']',
    r"fetch\(['\"]([^'\"?#]+)['\"]",
    r"src=['\"]([^'\"?#]+)['\"]",
]

errors = []

for html_path in html_files:
    base_dir = html_path.parent
    content = html_path.read_text(encoding="utf-8", errors="ignore")
    for pat in PATTERNS:
        for match in re.finditer(pat, content):
            raw = match.group(1).strip()
            if raw.startswith(("http", "//", "data:", "mailto:", "#", "javascript")) or not raw:
                continue
            if raw.startswith("/"):
                target = DOCS_ROOT / raw.lstrip("/")
            else:
                target = (base_dir / raw).resolve()
                try:
                    target.relative_to(Path("docs").resolve())
                except ValueError:
                    errors.append(f"[OUT-OF-DOCS] {html_path} → {raw}")
                    continue
            if not target.exists():
                errors.append(f"[DEAD] {html_path} → {raw}  (resolved: {target})")

print(f"=== チェック対象: {len(html_files)} ファイル ===\n")
if errors:
    for e in errors: print(e)
    print(f"\n合計 {len(errors)} 件のリンク切れ")
else:
    print("リンク切れなし ✅")
```

---

## 新規HTMLページ作成時の必須チェックリスト

### ① リンク切れチェック（HTMLファイル作成・移設・削除後は必須）

```bash
python ~/check_links.py
```

リンク切れ0件を確認してからコミットすること。

### ② site-nav.js への登録（新規ページ作成時は必須）

`docs/common/site-nav.js` の `ITEMS` 配列に新ページのエントリを追加：

```js
{ key: 'xxx', label: 'PAGE NAME', href: BASE + '/path/to/page/' }
```

新規HTMLの `<body>` タグに `data-tool="xxx"` を設定すること（key と完全一致）。
これを忘れるとナビが正しく生成されず、activeハイライトも当たらない。

**確認コマンド：**

```bash
grep -n "data-tool" docs/path/to/new/index.html
grep -n "key:.*'xxx'" docs/common/site-nav.js
```

### ③ ナビのactiveハイライト確認（新規ページ作成時は必須）

```bash
python -m http.server 8767 --directory docs
```

ブラウザで新規ページを開いてナビの該当項目がハイライトされていることを目視確認すること。

### ④ 共通デザイン適用（新規ページ作成時は必須）

`docs/common/site-header.js` の `TOOL_META` に新ページのツール定義を追加：

```js
xxx: { title: 'PAGE TITLE', subtitle: 'サブタイトル' }
```

`docs/common/site-theme.css` に `body[data-tool="xxx"] { --acc: #xxxxxx; }` を追加。

これを忘れると、ナビには登録されてもヘッダーが未適用のまま
（ロゴ・タイトル・アクセントカラーが統一されない）になる。

**確認コマンド：**

```bash
grep -n "xxx:" docs/common/site-header.js
grep -n "data-tool=\"xxx\"" docs/common/site-theme.css
```

（2026-07-01 EXTREME-FEAR-1対応時の実施パターンより追記）

---

## ファイル削除・上書き前の必須確認（重要）

### HTMLファイルを削除・新規作成・上書きする前に必ず実行すること

1. 削除・上書き対象ファイルの行数と主要セクションを確認

```bash
wc -l <対象ファイル>
grep -n "<section\|<div id\|<h2" <対象ファイル>
```

2. 「旧ページ」「不要」と判断する前に git log で履歴を確認

```bash
git log --oneline -- <対象ファイル>
```

3. 新規HTMLを作成する場合、同じ役割のページが既存していないか確認

```bash
find docs/ -name "*.html" | xargs grep -l "<キーワード>" 2>/dev/null
```

4. 上記確認結果をレポートしてから削除・作成を実行すること。
   **確認なしの削除・上書きは禁止。**
