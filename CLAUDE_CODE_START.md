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

## BACKLOG優先順位の目安

### 今すぐ着手可能（優先度高・難易度低）
- DESIGN-10: RICE三分類（閾値見直し）
- DISCOVER-1: Discoverプロンプト改善（小型・未発掘銘柄優先）
- ACTION-10: TANUKI SCOREの変化検知機能
- ACTION-6: Macro Extreme Fear戦略の実行支援

### 順次着手（優先度高・難易度中）
- ACTION-2: 判定実績の自動追跡・検証ループ
- ACTION-4: HYPEMIXポートフォリオ管理
- DESIGN-11: STONKSSILOユニットエコノミクス改善評価
- DESIGN-12: ステルス流動性のレベル感改善
- DESIGN-13: MACROPULSEマクロサプライズ検知

### 着手条件あり（先にDESIGN-4・5の設計が必要）
- HYPOTHESIS-1: 投資仮説管理
- HYPOTHESIS-2: KPI仮説・AI原案生成
- DESIGN-15: 期待と理論価格の関係の整理

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
```

**注意事項：**
- Step 2 を忘れると β=未設定のまま yfinance の raw 値が使われる
- 異常値が疑われる場合は `--dry-run` で差分確認してから適用
- LMT 等 Damodaran 手動設定銘柄は `beta_fetcher.py` の `DAMODARAN_OVERRIDES` に追加
- Step 5 HypeCore は yfinance 依存。KULR 等データ不足銘柄は失敗するが無視してよい
- Step 6 の discover_config.json は **dict 形式**（キー=ticker）。list 形式のコードは誤り
- Step 7 の monitor_tickers.yaml は **単純リスト形式**（yaml.dump 使用不可 → コメントが消える）

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
- [ ] BACKLOG.mdの該当項目を「完了済み」に移動
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
- TANUKI VALUATION系: BACKLOG.md
- システム全体バックログ: BACKLOG.md の末尾セクションに統合
- 編集前に必ず grep で行を特定してから変更する（行番号の直接指定は誤差が出るため禁止）

```bash
# 対象行の特定
grep -n "\[MP-5\]\|IMPLIED CUTS" BACKLOG.md
```

### BACKLOG更新のタイミング
- タスク完了後、**メモリではなくBACKLOG.mdに記録する**
- 完了時のフォーマット:
  - `[ ]` → `✅ [XX-N] タスク名（YYYY-MM-DD 完了）`
  - 実装内容を箇条書きで3行以内に要約して残す

### コミットルール（BACKLOG更新時）
git add BACKLOG.md
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
