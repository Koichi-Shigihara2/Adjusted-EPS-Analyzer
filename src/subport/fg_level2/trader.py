"""
F&G Level2 × TQQQ 発注・ポジション管理
=========================================
完全自動化版：
  - エントリー時はgit pullで最新signal.jsonを取得してから判定
  - moomoo OpenD（ローカル常時起動）経由で発注
  - Windowsタスクスケジューラから毎日自動実行

実行モード:
  python trader.py --entry    # エントリー判定+発注（タスクスケジューラから）
  python trader.py --monitor  # ポジション監視・決済判定（タスクスケジューラから）
  python trader.py --status   # 現在のポジション状態確認
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

# ============================================================
# パス設定
# ============================================================

BASE_DIR    = Path(__file__).parent
REPO_ROOT   = BASE_DIR.parent.parent.parent
CONFIG      = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
STATE_FILE  = BASE_DIR / "state.json"
SIGNAL_FILE = BASE_DIR / "signal.json"


# ============================================================
# git pull（最新シグナルを取得）
# ============================================================

def git_pull():
    """リモートから最新のsignal.jsonを取得する"""
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "kaihatsu"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"[git] pull成功: {result.stdout.strip()}")
        else:
            print(f"[git] pull失敗: {result.stderr.strip()}")
    except Exception as e:
        print(f"[git] pull例外: {e}")


def git_push():
    """state.jsonの変更をpushする"""
    try:
        subprocess.run(["git", "add", str(STATE_FILE)], cwd=REPO_ROOT, timeout=10)
        subprocess.run(
            ["git", "commit", "-m",
             f"chore(fg-level2): update state {date.today()}"],
            cwd=REPO_ROOT, capture_output=True, timeout=10
        )
        result = subprocess.run(
            ["git", "push", "origin", "kaihatsu"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
        )
        print(f"[git] push: {result.stdout.strip() or result.stderr.strip()}")
    except Exception as e:
        print(f"[git] push例外: {e}")


# ============================================================
# 状態管理
# ============================================================

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"position": None, "trades": []}


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )


# ============================================================
# moomoo API接続
# ============================================================

def get_moomoo_context():
    try:
        from moomoo import OpenTradeContext, TrdSide, OrderType, TrdEnv, TrdMarket
        ctx = OpenTradeContext(
            host="127.0.0.1",
            port=11111,
            trd_env=TrdEnv.SIMULATE,   # まずシミュレーション
        )
        return ctx
    except ImportError:
        print("[error] moomoo パッケージがインストールされていません")
        return None
    except Exception as e:
        print(f"[error] moomoo接続失敗: {e}")
        return None


def get_current_price(ticker: str) -> float | None:
    """現在価格を取得"""
    try:
        from moomoo import OpenQuoteContext
        ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
        ret, data = ctx.get_stock_quote([ticker])
        ctx.close()
        if ret == 0 and not data.empty:
            return float(data["last_price"].iloc[0])
    except Exception as e:
        print(f"[error] 価格取得失敗: {e}")

    # フォールバック: yfinanceで取得
    try:
        import yfinance as yf
        ticker_yf = CONFIG["strategy"]["ticker_yf"]
        data = yf.download(ticker_yf, period="1d", interval="1m",
                          progress=False, auto_adjust=True)
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception as e:
        print(f"[error] yfinance価格取得失敗: {e}")

    return None


# ============================================================
# エントリー
# ============================================================

def do_entry():
    """signal.jsonを読んでBUYなら発注"""
    print("\n[entry] エントリー処理開始")

    # 最新シグナルをpull
    git_pull()

    # シグナル確認
    if not SIGNAL_FILE.exists():
        print("[error] signal.json が見つかりません。signal.py を先に実行してください")
        sys.exit(1)

    signal = json.loads(SIGNAL_FILE.read_text(encoding="utf-8"))
    if signal.get("action") != "BUY":
        print(f"[skip] BUYシグナルなし: {signal.get('reason')}")
        sys.exit(0)

    # 状態確認
    state = load_state()
    if state.get("position"):
        print(f"[skip] 既存ポジションあり: {state['position']}")
        sys.exit(0)

    # 価格取得
    ticker = CONFIG["strategy"]["ticker"]
    price = get_current_price(ticker)
    if price is None:
        print("[error] 価格取得失敗")
        sys.exit(1)

    # 株数計算
    invest = CONFIG["sizing"]["invest_usd"]
    qty    = int(invest / price)
    if qty <= 0:
        print(f"[error] 株数0: 投資額=${invest} 価格=${price:.2f}")
        sys.exit(1)

    print(f"[entry] {ticker} @ ${price:.2f} × {qty}株 = ${qty*price:.2f}")

    # 発注（moomoo API）
    ctx = get_moomoo_context()
    if ctx is None:
        print("[warn] moomoo未接続のため発注スキップ（ペーパートレードモード）")
        order_id = "PAPER_" + datetime.now().strftime("%Y%m%d%H%M%S")
    else:
        try:
            from moomoo import TrdSide, OrderType, TrdEnv
            ret, data = ctx.place_order(
                price=0,               # 成行
                qty=qty,
                code=ticker,
                trd_side=TrdSide.BUY,
                order_type=OrderType.MARKET,
                trd_env=TrdEnv.SIMULATE,
            )
            ctx.close()
            if ret != 0:
                print(f"[error] 発注失敗: {data}")
                sys.exit(1)
            order_id = str(data["order_id"].iloc[0])
            print(f"[entry] 発注成功: order_id={order_id}")
        except Exception as e:
            print(f"[error] 発注例外: {e}")
            sys.exit(1)

    # 状態保存
    position = {
        "ticker":      ticker,
        "qty":         qty,
        "entry_price": price,
        "entry_date":  str(date.today()),
        "order_id":    order_id,
        "fg_score":    signal.get("fg_score"),
        "tech_pulse":  signal.get("tech_pulse"),
        "take_profit": price * (1 + CONFIG["exit"]["take_profit_pct"] / 100),
        "stop_loss":   price * (1 + CONFIG["exit"]["stop_loss_pct"] / 100),
    }
    state["position"] = position
    save_state(state)
    git_push()

    print(f"[entry] ポジション保存完了")
    print(f"  利確ライン: ${position['take_profit']:.2f} (+{CONFIG['exit']['take_profit_pct']}%)")
    print(f"  損切ライン: ${position['stop_loss']:.2f} ({CONFIG['exit']['stop_loss_pct']}%)")

    return position


# ============================================================
# ポジション監視・決済
# ============================================================

def do_monitor():
    """ポジションを監視して利確/損切/タイムアウトを判定"""
    print("\n[monitor] ポジション監視開始")

    state = load_state()
    pos   = state.get("position")

    if not pos:
        print("[skip] ポジションなし")
        sys.exit(0)

    ticker = pos["ticker"]
    price  = get_current_price(ticker)
    if price is None:
        print("[error] 価格取得失敗")
        sys.exit(1)

    entry_price = pos["entry_price"]
    pnl_pct     = (price - entry_price) / entry_price * 100
    entry_date  = datetime.strptime(pos["entry_date"], "%Y-%m-%d").date()
    hold_days   = (date.today() - entry_date).days

    print(f"[monitor] {ticker}: 現在${price:.2f} エントリー${entry_price:.2f}")
    print(f"  損益: {pnl_pct:+.2f}% 保有{hold_days}日")
    print(f"  利確: ${pos['take_profit']:.2f} 損切: ${pos['stop_loss']:.2f}")

    # 決済判定
    exit_reason = None

    if price >= pos["take_profit"]:
        exit_reason = f"利確 +{pnl_pct:.1f}%"
    elif price <= pos["stop_loss"]:
        exit_reason = f"損切 {pnl_pct:.1f}%"
    elif hold_days >= CONFIG["exit"]["timeout_days"]:
        exit_reason = f"タイムアウト {hold_days}日経過"

    if exit_reason:
        print(f"\n[exit] 決済条件成立: {exit_reason}")
        do_exit(state, pos, price, exit_reason)
    else:
        print(f"\n[hold] 保有継続")


def do_exit(state: dict, pos: dict, price: float, reason: str):
    """決済実行"""
    ticker = pos["ticker"]
    qty    = pos["qty"]

    print(f"[exit] {ticker} × {qty}株 @ ${price:.2f} 決済: {reason}")

    # 発注
    ctx = get_moomoo_context()
    if ctx is None:
        print("[warn] moomoo未接続のためペーパートレードモード")
        order_id = "PAPER_EXIT_" + datetime.now().strftime("%Y%m%d%H%M%S")
    else:
        try:
            from moomoo import TrdSide, OrderType, TrdEnv
            ret, data = ctx.place_order(
                price=0,
                qty=qty,
                code=ticker,
                trd_side=TrdSide.SELL,
                order_type=OrderType.MARKET,
                trd_env=TrdEnv.SIMULATE,
            )
            ctx.close()
            if ret != 0:
                print(f"[error] 決済失敗: {data}")
                sys.exit(1)
            order_id = str(data["order_id"].iloc[0])
        except Exception as e:
            print(f"[error] 決済例外: {e}")
            sys.exit(1)

    # 損益計算
    pnl_pct = (price - pos["entry_price"]) / pos["entry_price"] * 100
    pnl_usd = (price - pos["entry_price"]) * qty

    # トレード履歴に追加
    trade = {
        "ticker":      ticker,
        "qty":         qty,
        "entry_price": pos["entry_price"],
        "entry_date":  pos["entry_date"],
        "exit_price":  price,
        "exit_date":   str(date.today()),
        "exit_reason": reason,
        "pnl_pct":     round(pnl_pct, 2),
        "pnl_usd":     round(pnl_usd, 2),
        "hold_days":   (date.today() -
                        datetime.strptime(pos["entry_date"], "%Y-%m-%d").date()).days,
        "fg_entry":    pos.get("fg_score"),
        "tp_entry":    pos.get("tech_pulse"),
    }

    state["trades"].append(trade)
    state["position"] = None
    save_state(state)
    git_push()

    print(f"[exit] 完了: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
    print(f"  累計トレード数: {len(state['trades'])}")


# ============================================================
# ステータス表示
# ============================================================

def do_status():
    state = load_state()
    pos   = state.get("position")

    print("\n" + "=" * 50)
    print("F&G Level2 ポジション状態")
    print("=" * 50)

    if pos:
        price = get_current_price(pos["ticker"])
        pnl_str = ""
        if price:
            pnl = (price - pos["entry_price"]) / pos["entry_price"] * 100
            pnl_str = f" 現在${price:.2f} ({pnl:+.1f}%)"

        hold_days = (date.today() -
                     datetime.strptime(pos["entry_date"], "%Y-%m-%d").date()).days

        print(f"保有中: {pos['ticker']} × {pos['qty']}株")
        print(f"  エントリー: ${pos['entry_price']:.2f} ({pos['entry_date']}){pnl_str}")
        print(f"  保有日数: {hold_days}日")
        print(f"  利確: ${pos['take_profit']:.2f} / 損切: ${pos['stop_loss']:.2f}")
        print(f"  エントリー時F&G: {pos.get('fg_score')} Tech Pulse: {pos.get('tech_pulse')}")
    else:
        print("ポジションなし")

    trades = state.get("trades", [])
    if trades:
        print(f"\n過去トレード: {len(trades)}件")
        wins = sum(1 for t in trades if t["pnl_pct"] > 0)
        total_pnl = sum(t["pnl_usd"] for t in trades)
        print(f"  勝率: {wins}/{len(trades)} = {wins/len(trades)*100:.0f}%")
        print(f"  合計損益: ${total_pnl:+.2f}")
        print(f"\n  直近3件:")
        for t in trades[-3:]:
            print(f"    {t['entry_date']}→{t['exit_date']} "
                  f"{t['pnl_pct']:+.1f}% (${t['pnl_usd']:+.1f}) {t['exit_reason']}")


# ============================================================
# メイン
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F&G Level2 Trader")
    parser.add_argument("--entry",   action="store_true", help="エントリー実行")
    parser.add_argument("--monitor", action="store_true", help="ポジション監視・決済")
    parser.add_argument("--status",  action="store_true", help="状態確認")
    args = parser.parse_args()

    if args.entry:
        do_entry()
    elif args.monitor:
        do_monitor()
    elif args.status:
        do_status()
    else:
        parser.print_help()
