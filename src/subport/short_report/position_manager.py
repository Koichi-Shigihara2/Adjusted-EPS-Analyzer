"""
ポジション管理スクリプト
========================
GitHub Actionsで毎日実行し、保有中ポジションの
利確・損切・タイムアウトを判定してDiscordに通知する。

実行: python position_manager.py
"""

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yfinance as yf

from notify import send_exit_notice
from screener import load_config, load_state, save_state

CONFIG_PATH = Path(__file__).parent / "config.json"
TRADES_PATH = Path(__file__).parent / "trades.csv"
STATE_PATH  = Path(__file__).parent / "state.json"


def append_trade(trade: dict):
    """trades.csv にトレード結果を追記"""
    fieldnames = [
        "entry_date", "exit_date", "ticker", "entry_price", "exit_price",
        "return_pct", "hold_days", "exit_reason", "impact_score",
        "analysts", "inst_ownership", "drop_from_high"
    ]
    write_header = not TRADES_PATH.exists()
    with open(TRADES_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(trade)


def check_position(state: dict, cfg: dict) -> dict | None:
    """
    保有中ポジションを確認し、決済条件を判定。
    決済すべき場合は決済情報dictを返す。
    """
    pos = state.get("open_position")
    if not pos:
        return None

    ticker      = pos["ticker"]
    entry_price = float(pos["entry_price"])
    entry_date  = datetime.fromisoformat(pos["entry_date"]).replace(tzinfo=timezone.utc)

    # 現在価格取得
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if hist.empty:
            print(f"[価格取得失敗] {ticker}")
            return None
        current_price = float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"[yfinanceエラー] {e}")
        return None

    ret_pct     = (current_price - entry_price) / entry_price * 100
    hold_days   = (datetime.now(timezone.utc) - entry_date).days
    target      = cfg["exit"]["target_gain_pct"]
    stop        = cfg["exit"]["stop_loss_pct"]
    timeout     = cfg["exit"]["timeout_days"]

    exit_reason = None
    if ret_pct >= target:
        exit_reason = f"利確 (+{ret_pct:.1f}%)"
    elif ret_pct <= stop:
        exit_reason = f"損切 ({ret_pct:.1f}%)"
    elif hold_days >= timeout:
        exit_reason = f"タイムアウト ({hold_days}日経過)"

    if exit_reason:
        return {
            "ticker":       ticker,
            "entry_date":   pos["entry_date"],
            "exit_date":    datetime.now(timezone.utc).date().isoformat(),
            "entry_price":  entry_price,
            "exit_price":   round(current_price, 2),
            "return_pct":   round(ret_pct, 2),
            "hold_days":    hold_days,
            "exit_reason":  exit_reason,
            "impact_score": pos.get("impact_score", ""),
            "analysts":     pos.get("analysts", ""),
            "inst_ownership": pos.get("inst_ownership", ""),
            "drop_from_high": pos.get("drop_from_high", ""),
        }

    # 保有継続
    print(f"[保有継続] {ticker} | 現在値 ${current_price:.2f} | "
          f"リターン {ret_pct:+.1f}% | 保有{hold_days}日 | "
          f"目標 +{target}% | 損切 {stop}% | 残り{timeout - hold_days}日")
    return None


def update_state_after_exit(state: dict, exit_info: dict, cfg: dict) -> dict:
    """決済後の状態を更新"""
    ticker  = exit_info["ticker"]
    ret_pct = exit_info["return_pct"]
    stop    = cfg["exit"]["stop_loss_pct"]
    ban_days = cfg["position"]["reentry_ban_days"]

    # ポジションクリア
    state["open_position"] = None

    # 再エントリー禁止登録
    ban_until = (datetime.now(timezone.utc) + timedelta(days=ban_days)).date().isoformat()
    state.setdefault("banned_tickers", {})[ticker] = ban_until

    # 連続損失カウント
    if ret_pct < 0:
        state["consecutive_losses"] = state.get("consecutive_losses", 0) + 1
        skip_threshold = cfg["position"]["consecutive_loss_skip"]
        if state["consecutive_losses"] >= skip_threshold:
            state["skip_next"] = True
            print(f"[警告] {state['consecutive_losses']}連敗。次のシグナルをスキップします。")
    else:
        state["consecutive_losses"] = 0
        state["skip_next"] = False

    return state


def main():
    cfg   = load_config()
    state = load_state()

    if not state.get("open_position"):
        print("[ポジションなし] 保有中のポジションはありません。")
        return

    print(f"[確認中] {state['open_position']['ticker']} ...")
    exit_info = check_position(state, cfg)

    if exit_info:
        print(f"\n[決済判定] {exit_info['exit_reason']}")
        print(f"  {exit_info['ticker']}: "
              f"${exit_info['entry_price']} → ${exit_info['exit_price']} "
              f"({exit_info['return_pct']:+.1f}% / {exit_info['hold_days']}日)")

        # trades.csv に記録
        append_trade(exit_info)

        # Discord通知
        send_exit_notice(
            ticker=exit_info["ticker"],
            entry_price=exit_info["entry_price"],
            exit_price=exit_info["exit_price"],
            reason=exit_info["exit_reason"],
            cfg=cfg,
        )

        # 状態更新
        state = update_state_after_exit(state, exit_info, cfg)
        save_state(state)
        print("✅ 状態を更新しました。")
    else:
        print("→ 決済条件未達。保有継続。")


if __name__ == "__main__":
    main()
