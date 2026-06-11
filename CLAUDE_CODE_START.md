# Claude Code 作業開始テンプレート

## 毎回の作業開始時に必ず実行すること

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

例：
  discover_config.json への登録 → Step 6 として追加（2026-06-03）
  HypeCore 実行 → Step 5 として追加（2026-06-03）

### コミットルール
git add [変更ファイル]
git commit -m "feat/fix/docs: 変更内容の説明"
git pull --rebase origin kaihatsu
git push origin kaihatsu
- `git push --force` は絶対に使わない
- results.json を含むコミットは必ず rebase してから push

### テストルール
- 実装後に必ず pytest を実行する
- 新機能には必ずテストを追加する
- テスト失敗のままコミットしない

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

---

## 重要ルール

### AI APIキー管理ルール

- システム全体のAI APIはxAI（XAI_API_KEY）に統一されている
- 新規AI API呼び出しを実装する際は必ずGrok（`api.x.ai/v1/chat/completions`）を使用すること
- モデルはフォールバック方式：`["grok-3-mini", "grok-3", "grok-2-1212"]` の順で試行
- GeminiやOpenAI等の別APIを使用しているコードを発見した場合はGrokに移行すること

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
- TANUKI-ROE-1: デュポン分解ROE（TANUKI SCORE）
- MP-BIZDAY-1: MARKET PULSE営業日ベース化
- SEGMENT-1: セグメント精緻設定（LLY→LMT→MRVL→AMAT→VRTの順）

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
# Step 1: SEC データ取得
python common/sec_data/update.py [TICKER]

# Step 2: β を yfinance から自動取得して beta_config.json に登録
python src/value/tanuki_valuation/beta_fetcher.py [TICKER]

# Step 3: TANUKI VALUATION パイプライン実行
python src/value/tanuki_valuation/pipeline.py [TICKER]

# Step 4: データ品質確認（β設定含む）
python common/sec_data/audit.py [TICKER] --check-beta

# Step 5: HypeCore 実行
python src/value/hypecore/hypecore.py --batch [TICKER]
# 失敗した場合はログを確認。データ不足銘柄（上場直後等）は失敗することがある。

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

**注意事項：**
- Step 2 を忘れると β=未設定のまま yfinance の raw 値が使われる
- 異常値が疑われる場合は `--dry-run` で差分確認してから適用
- LMT 等 Damodaran 手動設定銘柄は `beta_fetcher.py` の `DAMODARAN_OVERRIDES` に追加
- Step 5 HypeCore は yfinance 依存。KULR 等データ不足銘柄は失敗するが無視してよい
- Step 6 の discover_config.json は **dict 形式**（キー=ticker）。list 形式のコードは誤り
- Step 7 の monitor_tickers.yaml は **単純リスト形式**（yaml.dump 使用不可 → コメントが消える）
- Step 8 の NG は必ず解消してからコミットする。主なNG要因:
  - `P2-A NG`: latest_revenue が TTM の 3 倍以上乖離 → SEC パーサーのタグ確認
  - `P1-Step3 NG`: latest.json 未生成 → pipeline.py を再実行
  - `P1-Step7 NG`: monitor_tickers 未登録 → Step 7 を再確認
- SaaS系銘柄でRPOプレミアムを適用する場合は `config/rpo_config.json` の
  whitelist に理由コメント付きで明示登録する（industry keyword 依存禁止）
  理由: keyword は将来銘柄追加時に意図しない適用の再発リスクあり（GOOGL等参照）

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
- [ ] HTMLファイルを新規作成・移設・削除した場合は `python ~/check_links.py` でリンク切れ0件を確認
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
