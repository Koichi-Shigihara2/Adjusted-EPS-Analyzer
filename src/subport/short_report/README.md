# ショートレポート逆張り戦略

## ファイル構成

```
src/subport/short_report/
├── config.json           ← パラメータ設定（ここだけ編集すればOK）
├── screener.py           ← スクリーニング本体
├── notify.py             ← Discord通知
├── position_manager.py   ← 日次ポジション監視・決済判定
├── state.json            ← 保有状態（自動更新、手動編集不要）
└── trades.csv            ← トレード履歴（自動追記）

.github/workflows/
└── short_report_screener.yml  ← GitHub Actions
```

---

## 使い方

### ショートレポートを発見したとき

**方法A: GitHub Actions から手動実行（推奨）**

1. GitHubリポジトリ → Actions → "Short Report Screener"
2. "Run workflow" をクリック
3. ticker・report_url（またはreport_text）を入力して実行
4. Discordに結果が届く → ENTRYならMoomooで手動発注

**方法B: ローカルで直接実行**

```powershell
cd src/subport/short_report

# URLから（Grokが本文取得・採点）
python screener.py --ticker ACME --report-url https://hindenburgresearch.com/acme

# テキスト直接入力
python screener.py --ticker ACME --report-text "The company has inflated revenues..."

# スコア手動指定（API使わない）
python screener.py --ticker ACME --report-text "..." --score 35

# テスト（通知・状態更新なし）
python screener.py --ticker ACME --report-text "..." --dry-run
```

---

## パラメータ変更方法

`config.json` を直接編集してpushするだけ。

```json
{
  "entry": {
    "impact_score_threshold": 50,   ← 閾値を下げると厳選、上げると緩和
    "min_analysts": 10,
    "min_inst_ownership_pct": 60,
    "min_drop_from_20d_high_pct": 10
  },
  "exit": {
    "target_gain_pct": 20,          ← 利確ライン
    "stop_loss_pct": -12,           ← 損切ライン
    "timeout_days": 60
  },
  "position": {
    "size_pct_of_subport": 30       ← ポジションサイズ（参考値・Moomooで手動設定）
  }
}
```

変更履歴はGitのコミットログに残るため、「どのパラメータで何回トレードしたか」が追跡できる。

---

## 日次監視フロー（自動）

```
毎営業日 UTC 22:00 (JST 朝7時)
  ↓
position_manager.py 実行
  ↓
保有中ポジションなし → 終了
保有中あり → 現在価格取得
  ↓
利確(+20%) / 損切(-12%) / タイムアウト(60日) 判定
  ↓
条件達成 → Discord通知 + trades.csv追記 + state.json更新
条件未達 → 「保有継続」ログ出力
```

---

## GitHub Secrets（既存を使用）

| Secret | 用途 |
|--------|------|
| `DISCORD_WEB_HOOK` | Discord通知 |
| `XAI_API_KEY` | Grokインパクトスコア採点 |

---

## 注意事項

- **自動発注は行わない**。ENTRYシグナルはDiscord通知止まり。Moomooで手動発注。
- state.jsonを手動編集する場合は、`open_position` の形式に注意。
- `trades.csv` はExcelで開いて実績確認・インパクトスコア相関分析に活用する。
