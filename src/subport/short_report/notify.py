"""
Discord通知モジュール
"""

import json
import os
from datetime import datetime, timezone

import requests


def _webhook_url(cfg: dict) -> str:
    env_key = cfg["notifications"]["discord_webhook_env"]
    return os.environ.get(env_key, "")


def _post(webhook_url: str, payload: dict) -> bool:
    if not webhook_url:
        print("[通知スキップ] DISCORD_WEB_HOOK が未設定")
        return False
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Discord通知エラー] {e}")
        return False


def send_signal(result: dict, cfg: dict):
    """スクリーニング結果をDiscordに通知"""
    if not cfg["notifications"]["notify_on_signal"]:
        return

    webhook_url = _webhook_url(cfg)
    action = result["action"]
    ticker = result["ticker"]
    pd     = result.get("price_data") or {}
    sr     = result.get("score_result") or {}

    if action == "ENTRY":
        color = 0x1D9E75   # 緑
        title = f"🟢 エントリー候補: {ticker}"
        desc  = (
            f"**ショートレポート逆張り** — 全条件クリア\n\n"
            f"現在値: **${pd.get('current_price', '?')}**\n"
            f"20日高値比: {pd.get('drop_from_high', '?')}%\n"
            f"インパクトスコア: **{sr.get('score', '?')}** （< {cfg['entry']['impact_score_threshold']}）\n"
            f"アナリスト: {pd.get('analysts', '?')}人 / 機関保有: {pd.get('inst_ownership', '?')}%\n"
            f"市場: {'強気' if pd.get('bull_market') else '弱気'}\n\n"
            f"採点理由: {sr.get('reason', '不明')}\n"
            f"最大リスク: {sr.get('highest_risk_item', '不明')}\n\n"
            f"**→ Moomooで手動発注してください**\n"
            f"利確: +{cfg['exit']['target_gain_pct']}% | "
            f"損切: {cfg['exit']['stop_loss_pct']}% | "
            f"タイムアウト: {cfg['exit']['timeout_days']}日"
        )
        fields = []

    elif action == "SKIP" and cfg["notifications"]["notify_on_skip"]:
        color = 0x888780   # グレー
        title = f"⏭ スキップ: {ticker}"
        reasons = result.get("skip_reasons", [])
        desc = "条件未達のためスキップ\n" + "\n".join(f"・{r}" for r in reasons)
        fields = []

    elif action == "WAIT":
        color = 0xBA7517   # アンバー
        title = f"⏳ 待機中: {ticker}"
        desc  = "\n".join(result.get("skip_reasons", []))
        fields = []

    else:
        return

    payload = {
        "embeds": [{
            "title":       title,
            "description": desc,
            "color":       color,
            "footer":      {"text": f"short-report-screener • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
        }]
    }
    _post(webhook_url, payload)


def send_exit_notice(ticker: str, entry_price: float, exit_price: float,
                     reason: str, cfg: dict):
    """決済通知（利確・損切・タイムアウト）"""
    if not cfg["notifications"]["notify_on_exit"]:
        return

    webhook_url = _webhook_url(cfg)
    ret = (exit_price - entry_price) / entry_price * 100

    if ret >= 0:
        color = 0x1D9E75
        icon  = "✅"
    else:
        color = 0xA32D2D
        icon  = "🔴"

    payload = {
        "embeds": [{
            "title":       f"{icon} 決済: {ticker}",
            "description": (
                f"理由: **{reason}**\n"
                f"エントリー: ${entry_price:.2f} → 決済: ${exit_price:.2f}\n"
                f"リターン: **{ret:+.1f}%**"
            ),
            "color": color,
            "footer": {"text": f"short-report-screener • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
        }]
    }
    _post(webhook_url, payload)


def send_heartbeat(cfg: dict, message: str = "スクリーナー正常稼働中"):
    """GitHub Actions 定期実行の生存確認"""
    webhook_url = _webhook_url(cfg)
    payload = {
        "embeds": [{
            "title":       "💓 Heartbeat",
            "description": message,
            "color":       0x3266ad,
            "footer":      {"text": f"short-report-screener • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
        }]
    }
    _post(webhook_url, payload)
