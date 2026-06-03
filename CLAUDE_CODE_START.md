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
```

**注意事項：**
- Step 2 を忘れると β=未設定のまま yfinance の raw 値が使われる
- 異常値が疑われる場合は `--dry-run` で差分確認してから適用
- LMT 等 Damodaran 手動設定銘柄は `beta_fetcher.py` の `DAMODARAN_OVERRIDES` に追加

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

## 作業完了時のチェックリスト

- [ ] pytest 全件パス
- [ ] 単体テストで動作確認
- [ ] 全銘柄再生成で成功率確認
- [ ] BACKLOG.mdの該当項目を「完了済み」に移動
- [ ] コミット・プッシュ完了

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
