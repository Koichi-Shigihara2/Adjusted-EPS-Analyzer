"""
F&G Level2 × TQQQ エントリーシグナル判定
==========================================
market_data.json から最新のF&GとTech Pulseを読み込み、
エントリー条件を判定する。

条件:
  - fear_greed.score = 11〜20（Extreme Fear深部）
  - tech_pulse.score > fear_greed.score
  - 既存ポジションなし

実行:
  python signal.py
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path

# ============================================================
# パス設定
# ============================================================

BASE_DIR    = Path(__file__).parent
CONFIG      = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
STATE_FILE  = BASE_DIR / "state.json"
SIGNAL_FILE = BASE_DIR / "signal.json"

REPO_ROOT  = BASE_DIR.parent.parent.parent
JSON_PATH  = REPO_ROOT / "docs/market-monitor/market-pulse/data/market_data.json"


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
# market_data.json からスコアを取得
# ============================================================

def load_latest_scores() -> dict | None:
    """
    market_data.json の最新エントリから
    fear_greed.score と tech_pulse.score を取得する。

    JSON構造:
      [
        {
          "date": "...",
          "fear_greed": {"score": 66.6, "rating": "greed", ...},
          "tech_pulse":  {"score": 63, "label": "NEUTRAL", ...},
          ...
        },
        ...
      ]
    """
    if not JSON_PATH.exists():
        print(f"[error] market_data.json が見つかりません: {JSON_PATH}")
        return None

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if not data:
        print("[error] market_data.json が空です")
        return None

    # 最新エントリ取得
    last = data[-1] if isinstance(data, list) else list(data.values())[-1]

    fg_data = last.get("fear_greed", {})
    tp_data = last.get("tech_pulse", {})

    fg_score = fg_data.get("score")
    tp_score = tp_data.get("score")

    if fg_score is None:
        print("[error] fear_greed.score が見つかりません")
        return None

    result = {
        "date":        last.get("date", str(date.today())),
        "fg_score":    float(fg_score),
        "fg_rating":   fg_data.get("rating", ""),
        "tech_pulse":  float(tp_score) if tp_score is not None else None,
        "tp_label":    tp_data.get("label", ""),
    }
    print(f"[info] F&G={result['fg_score']:.1f}({result['fg_rating']}) "
          f"TechPulse={result['tech_pulse']}({result['tp_label']})")
    return result


# ============================================================
# エントリー条件判定
# ============================================================

def check_entry_signal(scores: dict, state: dict) -> dict:
    cfg = CONFIG["entry"]
    fg  = scores["fg_score"]
    tp  = scores.get("tech_pulse")
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    base = {
        "fg_score":   fg,
        "fg_rating":  scores.get("fg_rating", ""),
        "tech_pulse": tp,
        "tp_label":   scores.get("tp_label", ""),
        "timestamp":  ts,
        "date":       scores["date"],
    }

    # 既存ポジションチェック
    if state.get("position"):
        return {**base, "action": "NO_TRADE",
                "reason": f"既存ポジションあり ({state['position']['ticker']})"}

    # F&G Level2チェック（11〜20）
    if not (cfg["fg_level2_min"] <= fg <= cfg["fg_level2_max"]):
        return {**base, "action": "NO_TRADE",
                "reason": f"F&G={fg:.1f} がLevel2範囲外 "
                           f"(条件: {cfg['fg_level2_min']}〜{cfg['fg_level2_max']})"}

    # Tech Pulseチェック
    if cfg["tech_pulse_above_fg"] and tp is not None:
        if tp <= fg:
            return {**base, "action": "NO_TRADE",
                    "reason": f"Tech Pulse({tp:.1f}) ≤ F&G({fg:.1f}) 条件不成立"}

    # 全条件クリア → BUY
    tp_str = f"{tp:.1f}" if tp is not None else "N/A"
    return {**base, "action": "BUY",
            "reason": f"F&G={fg:.1f}（Level2）TechPulse={tp_str} → エントリー条件成立"}


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 50)
    print("F&G Level2 シグナル判定")
    print("=" * 50)

    scores = load_latest_scores()
    if scores is None:
        signal = {
            "action":    "NO_TRADE",
            "reason":    "データ取得失敗",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_signal(signal)
        sys.exit(1)

    state  = load_state()
    signal = check_entry_signal(scores, state)

    print(f"\n[結果] {signal['action']}: {signal['reason']}")
    save_signal(signal)

    if signal["action"] == "BUY":
        print("\n✅ BUYシグナル → trader.py --entry を実行してください")
    else:
        print(f"\n⏸ トレードなし")

    sys.exit(0)


if __name__ == "__main__":
    main()
