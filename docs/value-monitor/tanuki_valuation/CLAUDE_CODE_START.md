# Claude Code 作業開始テンプレート

## 毎回の作業開始時に必ず実行すること

### Step 1: 現状確認
以下のファイルを読んでください：
- docs/value-monitor/tanuki_valuation/BACKLOG.md
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

## よく使うコマンド

### 単体テスト実行
python src/value/tanuki_valuation/pipeline.py --ticker NVDA

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
