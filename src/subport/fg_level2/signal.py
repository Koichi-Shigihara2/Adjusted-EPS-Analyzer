"""
F&G Level2 × TQQQ エントリーシグナル判定
==========================================
market_data.csv から最新のF&GとTech Pulseを読み込み、
エントリー条件を判定する。

条件:
  - F&G = 11〜20（Extreme Fear深部）
  - Tech Pulse > F&G（ナスダック感情がF&Gを上回っている）
  - 既存ポジションなし

出力:
  - signal.json にシグナル結果を書き出す
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

import pandas as pd

# ============================================================
# パス設定
# ============================================================

BASE_DIR   = Path(__file__).parent
CONFIG     = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
STATE_FILE = BASE_DIR / "state.json"
SIGNAL_FILE = BASE_DIR / "signal.json"

# リポジトリルートからmarket_data.csvを取得
REPO_ROOT  = BASE_DIR.parent.parent.parent
CSV_PATH   = REPO_ROOT / CONFIG["data"]["market_pulse_csv"]


# ============================================================
# 状態読み込み
# ============================================================

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"position": None, "trades": []}


def save_signal(signal: dict):
    SIGNAL_FILE.write_text(
        json.dumps(signal, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[signal] {SIGNAL_FILE} に書き出しました")


# ============================================================
# market_data.csv からF&G・Tech Pulseを取得
# ============================================================

def load_latest_scores() -> dict | None:
    """
    market_data.csv の最新行からF&GとTech Pulseを取得する。

    期待するカラム（Market Pulseの収集データ）:
      - date
      - fg_score または fear_greed_score
      - tech_pulse_score または tech_pulse
    """
    if not CSV_PATH.exists():
        print(f"[error] market_data.csv が見つかりません: {CSV_PATH}")
        return None

    df = pd.read_csv(CSV_PATH, encoding="utf-8")
    if df.empty:
        print("[error] market_data.csv が空です")
        return None

    # カラム名の正規化
    df.columns = [c.lower().strip() for c in df.columns]
    print(f"[info] カラム一覧: {list(df.columns)}")

    # 最新行を取得
    latest = df.iloc[-1]

    # F&Gスコアのカラムを探す
    fg_score = None
    for col in ["fg_score", "fear_greed_score", "fg", "fear_greed"]:
        if col in df.columns:
            fg_score = float(latest[col])
            break

    # Tech Pulseスコアのカラムを探す
    tp_score = None
    for col in ["tech_pulse_score", "tech_pulse", "tp_score", "tp"]:
        if col in df.columns:
            tp_score = float(latest[col])
            break

    if fg_score is None:
        print(f"[error] F&Gスコアのカラムが見つかりません")
        print(f"  利用可能なカラム: {list(df.columns)}")
        return None

    result = {
        "date":        str(latest.get("date", date.today())),
        "fg_score":    fg_score,
        "tech_pulse":  tp_score,
    }
    print(f"[info] 最新スコア: {result}")
    return result


# ============================================================
# エントリー条件判定
# ============================================================

def check_entry_signal(scores: dict, state: dict) -> dict:
    """
    エントリー条件を判定してシグナルを返す。

    Returns:
        {
            "action": "BUY" | "NO_TRADE",
            "reason": str,
            "fg_score": float,
            "tech_pulse": float,
            "timestamp": str,
        }
    """
    cfg    = CONFIG["entry"]
    fg     = scores["fg_score"]
    tp     = scores.get("tech_pulse")
    ts     = datetime.now().strftime("%Y-%m-%d %Human:%M:%S")

    base = {
        "fg_score":   fg,
        "tech_pulse": tp,
        "timestamp":  ts,
        "date":       scores["date"],
    }

    # 既存ポジションチェック
    if state.get("position"):
        return {**base, "action": "NO_TRADE",
                "reason": f"既存ポジションあり ({state['position']['ticker']})"}

    # F&G Level2チェック
    if not (cfg["fg_level2_min"] <= fg <= cfg["fg_level2_max"]):
        return {**base, "action": "NO_TRADE",
                "reason": f"F&G={fg:.1f} がLevel2範囲外 ({cfg['fg_level2_min']}〜{cfg['fg_level2_max']})"}

    # Tech Pulse チェック
    if cfg["tech_pulse_above_fg"] and tp is not None:
        if tp <= fg:
            return {**base, "action": "NO_TRADE",
                    "reason": f"Tech Pulse({tp:.1f}) ≤ F&G({fg:.1f}) 条件不成立"}

    # 全条件クリア → BUY
    tp_str = f"{tp:.1f}" if tp is not None else "N/A"
    return {**base, "action": "BUY",
            "reason": f"F&G={fg:.1f}（Level2）Tech Pulse={tp_str} > F&G → エントリー条件成立"}


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 50)
    print("F&G Level2 シグナル判定")
    print("=" * 50)

    # スコア取得
    scores = load_latest_scores()
    if scores is None:
        signal = {
            "action":    "NO_TRADE",
            "reason":    "データ取得失敗",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_signal(signal)
        sys.exit(1)

    # 状態読み込み
    state = load_state()

    # シグナル判定
    signal = check_entry_signal(scores, state)

    print(f"\n[結果] {signal['action']}: {signal['reason']}")

    # シグナル書き出し
    save_signal(signal)

    # BUYシグナルの場合は終了コード0以外で通知
    if signal["action"] == "BUY":
        print("\n✅ BUYシグナル発生 → trader.py を実行してください")
        sys.exit(0)
    else:
        print(f"\n⏸ トレードなし: {signal['reason']}")
        sys.exit(0)


if __name__ == "__main__":
    main()
