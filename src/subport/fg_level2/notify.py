"""
F&G Level2 Discord通知
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG   = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))


def send(message: str, title: str = "F&G Level2 TQQQ"):
    webhook = os.environ.get(CONFIG["notify"]["discord_webhook_env"])
    if not webhook:
        print(f"[notify] DISCORD_WEB_HOOK未設定 → スキップ")
        print(f"  メッセージ: {message}")
        return

    payload = {
        "embeds": [{
            "title":       title,
            "description": message,
            "color":       0x3b82f6,
            "footer":      {"text": datetime.now().strftime("%Y-%m-%d %H:%M JST")},
        }]
    }
    resp = requests.post(webhook, json=payload, timeout=10)
    if resp.status_code == 204:
        print(f"[notify] Discord送信成功")
    else:
        print(f"[notify] Discord送信失敗: {resp.status_code}")


def notify_signal(signal: dict):
    if signal["action"] == "BUY":
        msg = (
            f"🟢 **BUYシグナル発生**\n"
            f"F&G: {signal['fg_score']:.1f} (Level2: 11〜20)\n"
            f"Tech Pulse: {signal.get('tech_pulse', 'N/A')}\n"
            f"→ trader.py --entry を実行してください"
        )
        send(msg, "F&G Level2 BUYシグナル")
    else:
        msg = f"⏸ シグナルなし: {signal['reason']}"
        send(msg, "F&G Level2 定期確認")


def notify_entry(position: dict):
    msg = (
        f"📈 **エントリー完了**\n"
        f"銘柄: {position['ticker']} × {position['qty']}株\n"
        f"エントリー価格: ${position['entry_price']:.2f}\n"
        f"利確ライン: ${position['take_profit']:.2f}\n"
        f"損切ライン: ${position['stop_loss']:.2f}\n"
        f"エントリー時F&G: {position.get('fg_score')}"
    )
    send(msg, "F&G Level2 エントリー")


def notify_exit(trade: dict):
    emoji = "✅" if trade["pnl_pct"] > 0 else "❌"
    msg = (
        f"{emoji} **決済完了**\n"
        f"銘柄: {trade['ticker']}\n"
        f"損益: {trade['pnl_pct']:+.2f}% (${trade['pnl_usd']:+.2f})\n"
        f"保有日数: {trade['hold_days']}日\n"
        f"決済理由: {trade['exit_reason']}"
    )
    send(msg, "F&G Level2 決済")
