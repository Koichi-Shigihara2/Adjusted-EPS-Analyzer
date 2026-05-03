# F&G第2水準戦略 バックテスト README

## ファイル配置

```
src/subport/
├── fg_level2_backtest.py   ← メインスクリプト
├── fg_historical.csv       ← F&Gデータ（手動配置 or --fetch で取得）
├── qqq_prices.csv          ← 株価データ（--fetch で取得）
└── backtest_results/       ← 出力先（自動生成）
```

---

## Step 1: F&Gデータの準備

### 方法A: feargreedchart.com から手動ダウンロード（推奨）

1. https://feargreedchart.com にアクセス
2. ページ内の「Download CSV」または右クリック→データ取得
3. 以下の形式で `fg_historical.csv` を作成:

```csv
date,score
2018-01-02,75
2018-01-03,71
...
```

### 方法B: collect_and_send.py の既存データを活用

Market Pulseの `fg_scores.csv` があれば流用可能（4/4〜）。
ただしデータ期間が短いため補完が必要。

### 方法C: --fetch オプション（要インターネット接続）

```powershell
cd src/subport
python fg_level2_backtest.py --fetch --ticker QQQ
```

---

## Step 2: バックテスト実行

### 基本実行（利確10%, タイムアウト30日）

```powershell
python fg_level2_backtest.py
```

### 条件指定

```powershell
# 利確15%, 20日保有
python fg_level2_backtest.py --target 0.15 --hold 20

# TQQQ で検証
python fg_level2_backtest.py --ticker TQQQ --target 0.20 --hold 30

# 全条件マトリクス（利確10/15/20% × 保有10/20/30/60日）
python fg_level2_backtest.py --all
```

---

## 出力

### コンソール出力例

```
============================================================
条件: 利確=10%, タイムアウト=30日, 銘柄=QQQ
============================================================

▶ Extreme Fear (1-10) | 利確10% | 30日
  トレード数    : 8回
  勝率          : 87.5%
  目標到達率    : 75.0%
  平均リターン  : 12.3%
  ...

▶ Level2 Fear (11-20) | 利確10% | 30日   ← 本戦略
  トレード数    : 23回
  勝率          : 78.3%
  目標到達率    : 60.9%
  平均リターン  : 9.8%
  ...
```

### CSV出力

- `backtest_results/fg_level2_QQQ_target10_hold30/fg_level2_summary.csv`
- `backtest_results/fg_level2_QQQ_target10_hold30/fg_level2_trades.csv`

---

## 検証ポイント

| 問い | 確認方法 |
|------|----------|
| F&G=11-20 は F&G=1-10 より成績が落ちるか | summary.csv で勝率・平均リターン比較 |
| 最適な利確ラインは10%か20%か | --all で全マトリクス確認 |
| QQQ vs TQQQ どちらが適切か | --ticker TQQQ で再実行 |
| 年ごとのパフォーマンス変動 | trades.csv を年別にフィルタ |

---

## Stage 2 (将来): Tech Pulse上抜け条件の追加

Tech Pulseデータが半年以上蓄積後:
- エントリー条件に `tech_pulse > fg_score` を追加
- `market_pulse_history.csv` と結合してバックテスト

```python
# 将来実装予定
entry_condition = (zone[0] <= fg_val <= zone[1]) and (tech_pulse_val > fg_val)
```
