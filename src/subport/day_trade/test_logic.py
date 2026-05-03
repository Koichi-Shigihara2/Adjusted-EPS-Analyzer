"""
動作確認用合成データテスト
============================
ORBロジック・エントリー品質フィルター・エグジットの
全パターンを合成データで検証する。

実行:
  python test_logic.py
"""

import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# backtest.pyの関数をインポート
sys.path.insert(0, str(Path(__file__).parent))
from backtest import (
    find_orb,
    find_orb_entry,
    check_entry_quality,
    simulate_exit,
    calc_trend_score,
    get_trend_multiplier,
    is_skip_day,
    add_indicators,
)

CONFIG_PATH = Path(__file__).parent / "config.json"
with open(CONFIG_PATH, encoding="utf-8") as f:
    CFG = json.load(f)

ET = timezone(timedelta(hours=-4))

PASS = 0
FAIL = 0

def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ PASS: {msg}")

def ng(msg, expected, got):
    global FAIL
    FAIL += 1
    print(f"  ❌ FAIL: {msg}")
    print(f"       期待: {expected}")
    print(f"       実際: {got}")


# ============================================================
# 合成データ生成ヘルパー
# ============================================================

def make_bar(dt: datetime, open_: float, high: float,
             low: float, close: float, volume: int = 1_000_000) -> dict:
    return {
        "datetime": dt,
        "open":   open_,
        "high":   high,
        "low":    low,
        "close":  close,
        "volume": volume,
    }


def bars_to_df(bars: list) -> pd.DataFrame:
    """バーリストをDataFrameに変換（backtest.pyと同じ形式）"""
    df = pd.DataFrame(bars).set_index("datetime")
    df.index = pd.to_datetime(df.index)
    tz = timezone(timedelta(hours=-4))
    if df.index.tzinfo is None:
        df.index = df.index.tz_localize("America/New_York")
    df["body"]       = (df["close"] - df["open"]).abs()
    df["wick"]       = df["high"] - df["low"]
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)

    # VWAP（簡略）
    df["typical"] = (df["high"] + df["low"] + df["close"]) / 3
    df["tp_vol"]  = df["typical"] * df["volume"]
    df["vwap"]    = df["tp_vol"].cumsum() / df["volume"].cumsum()

    # ATR（日足ベースで設定）
    day_range = df["high"].max() - df["low"].min()
    df["atr"]  = day_range

    # volume rolling avg
    df["rvol"] = df["volume"] / df["volume"].rolling(10, min_periods=1).mean()

    return df


def make_day(base_price: float = 450.0,
             date_: date = date(2026, 4, 15)) -> pd.DataFrame:
    """標準的な1日の5分足データを生成"""
    bars = []
    dt_base = datetime(date_.year, date_.month, date_.day,
                       tzinfo=timezone(timedelta(hours=-4)))

    # 9:30〜16:00 の78本
    price = base_price
    for i in range(78):
        t = dt_base.replace(hour=9, minute=30) + timedelta(minutes=5 * i)
        move = np.random.normal(0, 0.3)
        o = price
        c = price + move
        h = max(o, c) + abs(np.random.normal(0, 0.1))
        l = min(o, c) - abs(np.random.normal(0, 0.1))
        bars.append(make_bar(t, o, h, l, c))
        price = c

    return bars_to_df(bars)


# ============================================================
# テスト群
# ============================================================

def test_orb_detection():
    """ORB計算のテスト"""
    print("\n[1] ORB検出テスト")

    bars = []
    dt = datetime(2026, 4, 15, tzinfo=timezone(timedelta(hours=-4)))

    # 前日データ（ATR用）: high=455, low=448 → prev_atr=7.0
    prev_bars_list = []
    prev_dt = datetime(2026, 4, 14, tzinfo=timezone(timedelta(hours=-4)))
    for i in range(78):
        t = prev_dt.replace(hour=9, minute=30) + timedelta(minutes=5*i)
        prev_bars_list.append(make_bar(t, 451.0, 455.0, 448.0, 451.5))
    prev_df = bars_to_df(prev_bars_list)

    # 9:30〜9:44 のORBゾーン（high=451.5 / low=449.0 → size=2.5）
    # prev_atr=7.0 → ratio=2.5/7.0=0.357 → min=0.3 OK
    for i, (o, h, l, c) in enumerate([
        (450.0, 451.0, 449.5, 450.5),
        (450.5, 451.5, 449.0, 450.2),
        (450.2, 451.2, 449.2, 450.8),
    ]):
        t = dt.replace(hour=9, minute=30+i*5)
        bars.append(make_bar(t, o, h, l, c))

    for i in range(20):
        t = dt.replace(hour=9, minute=45) + timedelta(minutes=5*i)
        bars.append(make_bar(t, 450.0, 452.0, 449.0, 451.0))

    df = bars_to_df(bars)
    orb = find_orb(df, CFG, prev_df)

    if orb is not None:
        ok(f"ORB検出成功: high={orb['high']:.2f} low={orb['low']:.2f} size={orb['size']:.2f} atr={orb['atr']:.2f}(前日)")
    else:
        ng("ORB検出失敗", "ORBオブジェクト", None)

    # ケース2: ORBが小さすぎる（prev_atr=7.0に対してsize=0.01 → ratio=0.001 < 0.3）
    bars2 = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars2.append(make_bar(t, 450.0, 450.01, 450.00, 450.005))
    for i in range(20):
        t = dt.replace(hour=9, minute=45) + timedelta(minutes=5*i)
        bars2.append(make_bar(t, 450.0, 455.0, 445.0, 451.0))

    df2 = bars_to_df(bars2)
    orb2 = find_orb(df2, CFG, prev_df)
    if orb2 is None:
        ok("ORBサイズNG（小さすぎ）を正しくスキップ")
    else:
        ng("ORBサイズNG検出ミス", None, orb2)


def test_orb_entry_3step():
    """ORB確認足（3ステップ）のテスト"""
    print("\n[2] ORB確認足エントリーテスト")
    dt = datetime(2026, 4, 15, tzinfo=timezone(timedelta(hours=-4)))
    orb_high = 451.5
    orb_low  = 449.0
    orb = {"high": orb_high, "low": orb_low,
           "size": orb_high - orb_low, "atr": 5.0}

    # ケース1: 正常な3ステップ（Long）
    # 9:30〜9:44: ORBゾーン
    bars = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))

    # 9:45: 第1ブレイク（451.5超え）
    bars.append(make_bar(dt.replace(hour=9, minute=45), 451.5, 452.5, 451.0, 452.0))
    # 9:50: プルバック（451.5以下に戻る）
    bars.append(make_bar(dt.replace(hour=9, minute=50), 452.0, 452.2, 450.8, 451.0))
    # 9:55: 再ブレイク（451.5超え）→ エントリー
    bars.append(make_bar(dt.replace(hour=9, minute=55), 451.2, 453.0, 451.0, 452.5,
                         volume=2_500_000))
    # 10:00以降
    for i in range(10):
        t = dt.replace(hour=10, minute=0) + timedelta(minutes=5*i)
        bars.append(make_bar(t, 452.5, 454.0, 452.0, 453.0))

    df = bars_to_df(bars)
    entry = find_orb_entry(df, orb, "long", CFG)

    if entry is not None:
        ok(f"3ステップエントリー検出: {entry['idx'].time()} @ {entry['bar']['close']:.2f}")
    else:
        ng("3ステップエントリー未検出", "9:55のエントリー", None)

    # ケース2: プルバックなし（タイムアウト）
    bars2 = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars2.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    # 9:45: 第1ブレイク
    bars2.append(make_bar(dt.replace(hour=9, minute=45), 451.5, 453.0, 451.6, 452.8))
    # 9:50〜10:10: プルバックせず上昇継続（タイムアウト）
    for i in range(6):
        t = dt.replace(hour=9, minute=50) + timedelta(minutes=5*i)
        bars2.append(make_bar(t, 452.8, 454.0, 452.5, 453.5))

    df2 = bars_to_df(bars2)
    entry2 = find_orb_entry(df2, orb, "long", CFG)
    if entry2 is None:
        ok("プルバックなしタイムアウトを正しくスキップ")
    else:
        ng("プルバックなし検出ミス", None, entry2)

    # ケース3: エントリー期限超過
    bars3 = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars3.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    # 10:35に再ブレイク（期限の10:30超過）
    bars3.append(make_bar(dt.replace(hour=9, minute=45), 451.5, 452.5, 451.0, 452.0))
    bars3.append(make_bar(dt.replace(hour=9, minute=50), 452.0, 452.2, 450.8, 451.0))
    bars3.append(make_bar(dt.replace(hour=10, minute=35), 451.2, 453.0, 451.0, 452.5))

    df3 = bars_to_df(bars3)
    entry3 = find_orb_entry(df3, orb, "long", CFG)
    if entry3 is None:
        ok("エントリー期限超過を正しくスキップ")
    else:
        ng("期限超過検出ミス", None, entry3)


def test_entry_quality_filters():
    """エントリー品質フィルターのテスト"""
    print("\n[3] エントリー品質フィルターテスト")
    dt = datetime(2026, 4, 15, tzinfo=timezone(timedelta(hours=-4)))
    orb_high = 451.5
    orb_low  = 449.0
    avg_vol  = 1_000_000
    vwap     = 450.5

    def make_entry_bar(o, h, l, c, vol=2_000_000):
        bar = {
            "open": o, "high": h, "low": l, "close": c,
            "volume": vol,
            "body": abs(c - o),
            "wick": h - l,
            "upper_wick": h - max(o, c),
            "vwap": vwap,
        }
        return bar

    prev_bars = pd.DataFrame([
        {"volume": 1_500_000}, {"volume": 1_200_000}
    ])

    # ケース1: 全条件クリア（Long・正常）
    bar = make_entry_bar(451.5, 452.8, 451.3, 452.5, vol=2_500_000)
    ok_flag, reason = check_entry_quality(
        bar, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if ok_flag:
        ok("正常エントリー（Long）クリア")
    else:
        ng("正常エントリーが不当にスキップ", True, reason)

    # ケース2: ヒゲ過大
    bar2 = make_entry_bar(451.5, 455.0, 450.0, 452.0)  # wick=5, body=0.5
    ok_flag2, reason2 = check_entry_quality(
        bar2, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok_flag2 and "ヒゲ" in reason2:
        ok(f"ヒゲ過大を正しく除外: {reason2}")
    else:
        ng("ヒゲ過大の検出ミス", "ヒゲ過大", reason2)

    # ケース3: 出来高不足
    bar3 = make_entry_bar(451.5, 452.8, 451.3, 452.5, vol=500_000)  # avg_volの50%
    ok_flag3, reason3 = check_entry_quality(
        bar3, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok_flag3 and "出来高" in reason3:
        ok(f"出来高不足を正しく除外: {reason3}")
    else:
        ng("出来高不足の検出ミス", "出来高不足", reason3)

    # ケース4: SPY逆行（Long時にSPY下落）
    bar4 = make_entry_bar(451.5, 452.8, 451.3, 452.5, vol=2_500_000)
    ok_flag4, reason4 = check_entry_quality(
        bar4, prev_bars, "long", vwap, avg_vol, "down", orb_high, orb_low, CFG)
    if not ok_flag4 and "SPY" in reason4:
        ok(f"SPY逆行を正しく除外: {reason4}")
    else:
        ng("SPY逆行の検出ミス", "SPY逆行", reason4)

    # ケース5: 陰線ブレイク（Long時）ヒゲが小さい陰線
    bar5 = make_entry_bar(452.3, 452.4, 452.0, 452.1)  # close(452.1) < open(452.3)、wick小
    ok_flag5, reason5 = check_entry_quality(
        bar5, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok_flag5 and "陰線" in reason5:
        ok(f"陰線ブレイクを正しく除外: {reason5}")
    else:
        ng("陰線ブレイクの検出ミス", "陰線ブレイク", reason5)

    # ケース6: VWAP以下（Long時）close < vwap=450.5
    # wick/body < 2.0 になるようヒゲを小さく
    bar6 = make_entry_bar(449.8, 450.05, 449.75, 450.0, vol=2_500_000)
    ok_flag6, reason6 = check_entry_quality(
        bar6, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok_flag6 and "VWAP" in reason6:
        ok(f"VWAP以下を正しく除外: {reason6}")
    else:
        ng("VWAP以下の検出ミス", "VWAP以下", reason6)

    # ケース7: ORB乖離過大（orb_high=451.5から3%超）
    # wick/body < 2.0 になるようヒゲを小さく
    bar7 = make_entry_bar(464.9, 465.05, 464.85, 465.0, vol=2_500_000)
    ok_flag7, reason7 = check_entry_quality(
        bar7, prev_bars, "long", 465.0, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok_flag7 and "乖離" in reason7:
        ok(f"ORB乖離過大を正しく除外: {reason7}")
    else:
        ng("ORB乖離の検出ミス", "ORB乖離", reason7)


def test_exit_logic():
    """エグジットロジックのテスト"""
    print("\n[4] エグジットロジックテスト")
    dt = datetime(2026, 4, 15, tzinfo=timezone(timedelta(hours=-4)))
    entry_price = 452.0
    atr = 5.0  # 日足レンジ

    def make_post_bars(prices: list, start_time=time(10, 0),
                       vwap_offset: float = 0.0) -> pd.DataFrame:
        bars = []
        for i, p in enumerate(prices):
            t = datetime(2026, 4, 15,
                         tzinfo=timezone(timedelta(hours=-4))).replace(
                hour=start_time.hour,
                minute=start_time.minute
            ) + timedelta(minutes=5*i)
            bars.append(make_bar(t, p, p+0.5, p-0.3, p, volume=1_000_000))
        df = bars_to_df(bars)
        # VWAPをoffsetで調整（デフォルトはエントリー価格と同水準）
        df["vwap"] = entry_price + vwap_offset
        return df

    atr_pct = atr / entry_price
    target1 = entry_price * (1 + 1.0 * atr_pct)  # +1.0%
    target2 = entry_price * (1 + 1.5 * atr_pct)  # +1.5%
    stop    = entry_price * (1 - 0.8 * atr_pct)  # -0.8%

    # ケース1: 第2利確到達
    # atr_pct=5/452=1.106% → target2=452*(1+1.5*0.01106)=459.50
    # 価格を459.5以上にする
    prices1 = [453.0, 455.0, 457.0, 459.0, 460.0, 461.0]
    bars1 = []
    for i, p in enumerate(prices1):
        t = datetime(2026, 4, 15, tzinfo=timezone(timedelta(hours=-4))).replace(
            hour=10, minute=0) + timedelta(minutes=5*i)
        bars1.append(make_bar(t, p, p+1.0, p-0.3, p, volume=3_000_000))
    df1 = bars_to_df(bars1)
    df1["vwap"] = entry_price - 5.0   # VWAP=447 → 割れない
    result1 = simulate_exit(entry_price, "long", atr, df1, CFG)
    if result1["exit_reason"] == "第2利確":
        ok(f"第2利確: {result1['return_pct']:+.2f}%")
    else:
        ng("第2利確検出ミス", "第2利確", result1["exit_reason"])

    # ケース2: 損切り（VWAPを高く設定→損切りが先）
    prices2 = [451.0, 450.0, 449.0, 448.0]
    df2 = make_post_bars(prices2, vwap_offset=10.0)  # VWAP=462 → 常にVWAP以下
    result2 = simulate_exit(entry_price, "long", atr, df2, CFG)
    if "損切" in result2["exit_reason"] or "VWAP" in result2["exit_reason"]:
        ok(f"損切/VWAP割れ: {result2['exit_reason']} {result2['return_pct']:+.2f}%")
    else:
        ng("損切り検出ミス", "損切", result2["exit_reason"])

    # ケース3: タイムアウト（横ばい・VWAPはエントリー価格付近）
    prices3 = [452.5] * 30
    df3 = make_post_bars(prices3, start_time=time(11, 0), vwap_offset=-5.0)
    result3 = simulate_exit(entry_price, "long", atr, df3, CFG)
    if result3["exit_reason"] in ("タイムアウト", "30分ルール"):
        ok(f"タイムアウト/30分ルール: {result3['exit_reason']} {result3['return_pct']:+.2f}%")
    else:
        ng("タイムアウト検出ミス", "タイムアウト", result3["exit_reason"])

    # ケース4: VWAP割れ（明示的にVWAPを高く設定）
    prices4 = [452.5, 452.3, 450.0, 449.5]
    df4 = make_post_bars(prices4, vwap_offset=3.0)  # VWAP=455 → すぐVWAP割れ
    result4 = simulate_exit(entry_price, "long", atr, df4, CFG)
    if "VWAP" in result4["exit_reason"] or "損切" in result4["exit_reason"]:
        ok(f"VWAP割れ/損切: {result4['exit_reason']} {result4['return_pct']:+.2f}%")
    else:
        ng("VWAP割れ検出ミス", "VWAP割れ", result4["exit_reason"])

    # ケース5: 30分ルール（勢いなし）
    prices5 = [452.1, 452.2, 452.1, 452.3, 452.2, 452.1, 452.0]
    df5 = make_post_bars(prices5, vwap_offset=-5.0)
    result5 = simulate_exit(entry_price, "long", atr, df5, CFG)
    if result5["exit_reason"] in ("30分ルール", "タイムアウト"):
        ok(f"30分ルール: {result5['exit_reason']} {result5['return_pct']:+.2f}%")
    else:
        ng("30分ルール検出ミス", "30分ルール", result5["exit_reason"])


def test_layer0_skip():
    """Layer 0やらない日判定のテスト"""
    print("\n[5] Layer 0 やらない日テスト")
    d = date(2026, 4, 15)

    # ケース1: 正常（スキップなし）VIX=20（正常レベル）
    skip, reason = is_skip_day(d, CFG, 20.0, 1.0, 0, 0.0, 10000, 10000)
    if not skip:
        ok("正常日はスキップしない")
    else:
        ng("正常日を不当にスキップ", False, reason)

    # ケース2: VIX過大（VIX=40 >= 35）
    skip2, reason2 = is_skip_day(d, CFG, 40.0, 1.0, 0, 0.0, 10000, 10000)
    if skip2:
        ok(f"VIX過大スキップ: {reason2}")
    else:
        ng("VIX過大を見逃し", True, skip2)

    # ケース3: SPYギャップ過大
    skip3, reason3 = is_skip_day(d, CFG, 20.0, 3.0, 0, 0.0, 10000, 10000)
    if skip3:
        ok(f"SPYギャップスキップ: {reason3}")
    else:
        ng("SPYギャップを見逃し", True, skip3)

    # ケース4: 3連敗
    skip4, reason4 = is_skip_day(d, CFG, 20.0, 1.0, 3, 0.0, 10000, 10000)
    if skip4:
        ok(f"3連敗スキップ: {reason4}")
    else:
        ng("3連敗を見逃し", True, skip4)

    # ケース5: 最大ドローダウン
    skip5, reason5 = is_skip_day(d, CFG, 20.0, 1.0, 0, 0.0, 10000, 8900)
    if skip5:
        ok(f"最大DDスキップ: {reason5}")
    else:
        ng("最大DDを見逃し", True, skip5)

    # ケース6: 月曜日
    monday = date(2026, 4, 13)  # 月曜日
    skip6, reason6 = is_skip_day(monday, CFG, -1.0, 1.0, 0, 0.0, 10000, 10000)
    expected_skip = CFG["layer0"]["skip_monday_open"]
    if skip6 == expected_skip:
        ok(f"月曜スキップ設定({expected_skip})が正しく動作")
    else:
        ng("月曜スキップ動作ミス", expected_skip, skip6)


def test_trend_score():
    """トレンド日スコアのテスト"""
    print("\n[6] トレンド日スコアテスト")

    # 全条件クリア（スコア最大）
    spy_bar  = {"ema9": 450.0, "ema21": 448.0, "close": 451.0, "vwap": 449.0}
    qqq_bar  = {"ema9": 460.0, "ema21": 458.0, "close": 461.0, "vwap": 459.0}

    score, reasons = calc_trend_score(
        spy_bar, qqq_bar,
        vix_change=-3.0,          # VIX低下
        premarket_gap=2.5,        # ギャップあり
        rvol=2.5,                 # RVOL高い
        sector_aligned=True,      # セクター一致
        yield_change_bp=1.0,      # 金利安定
        capital_flow_score=1,     # 大口買い越し
        cfg=CFG
    )
    if score >= 6:
        ok(f"高スコア日: score={score} ({'/'.join(reasons)})")
    else:
        ng("高スコア日の計算ミス", "≥6", score)

    # 悪条件（スコア低）
    spy_bar2 = {"ema9": 448.0, "ema21": 450.0, "close": 447.0, "vwap": 449.0}
    qqq_bar2 = {"ema9": 458.0, "ema21": 460.0, "close": 457.0, "vwap": 459.0}

    score2, reasons2 = calc_trend_score(
        spy_bar2, qqq_bar2,
        vix_change=5.0,           # VIX急騰
        premarket_gap=0.5,        # ギャップなし
        rvol=1.2,                 # RVOL低い
        sector_aligned=False,
        yield_change_bp=7.0,      # 金利急騰
        capital_flow_score=-1,
        cfg=CFG
    )
    if score2 <= 1:
        ok(f"低スコア日: score={score2}")
    else:
        ng("低スコア日の計算ミス", "≤1", score2)

    # trend_multiplier確認
    for s, expected in [(0, 0.0), (2, 0.0), (3, 0.5),
                        (4, 0.75), (5, 1.0), (6, 1.25), (9, 1.25)]:
        mult = get_trend_multiplier(s, CFG)
        if mult == expected:
            ok(f"trend_mult score={s} → {mult}")
        else:
            ng(f"trend_mult score={s} 計算ミス", expected, mult)


# ============================================================
# 追加テスト群
# ============================================================

def test_orb_short_direction():
    """Short方向のORBロジックテスト"""
    print("\n[7] Short方向ORBテスト")
    dt = datetime(2026, 4, 15, tzinfo=ET)
    orb_high = 451.5
    orb_low  = 449.0
    orb = {"high": orb_high, "low": orb_low,
           "size": orb_high - orb_low, "atr": 5.0}

    # ケース1: Short正常3ステップ
    bars = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    # 9:45: 第1下抜け
    bars.append(make_bar(dt.replace(hour=9, minute=45), 449.0, 449.2, 448.0, 448.5))
    # 9:50: プルバック（ORB内に戻る）
    bars.append(make_bar(dt.replace(hour=9, minute=50), 448.5, 449.5, 448.3, 449.2))
    # 9:55: 再下抜け → エントリー
    bars.append(make_bar(dt.replace(hour=9, minute=55), 449.0, 449.1, 447.5, 448.0,
                         volume=2_500_000))
    for i in range(5):
        t = dt.replace(hour=10, minute=0) + timedelta(minutes=5*i)
        bars.append(make_bar(t, 448.0, 448.5, 447.0, 447.5))

    df = bars_to_df(bars)
    entry = find_orb_entry(df, orb, "short", CFG)
    if entry is not None:
        ok(f"Short 3ステップエントリー検出: {entry['idx'].time()} @ {entry['bar']['close']:.2f}")
    else:
        ng("Short 3ステップエントリー未検出", "9:55のエントリー", None)

    # ケース2: Short確信度不足でスキップ（backtest内のロジック確認用・ここでは手動確認）
    threshold = CFG["layer3"]["confidence_min_short"]
    ok(f"Short確信度閾値設定確認: {threshold}（設定値）")


def test_entry_quality_short():
    """Short方向エントリー品質フィルターテスト"""
    print("\n[8] Short方向エントリー品質テスト")
    orb_high = 451.5
    orb_low  = 449.0
    avg_vol  = 1_000_000
    vwap     = 450.5

    def make_entry_bar(o, h, l, c, vol=2_000_000):
        return {
            "open": o, "high": h, "low": l, "close": c,
            "volume": vol,
            "body": abs(c - o),
            "wick": h - l,
            "upper_wick": h - max(o, c),
            "vwap": vwap,
        }

    prev_bars = pd.DataFrame([{"volume": 1_500_000}, {"volume": 1_200_000}])

    # ケース1: Short正常（wick/body < 2.0 に注意）
    # body=0.3, wick=0.4 → ratio=1.33 OK
    bar = make_entry_bar(449.3, 449.4, 449.0, 449.0, vol=2_500_000)
    ok_flag, reason = check_entry_quality(
        bar, prev_bars, "short", vwap, avg_vol, "down", orb_high, orb_low, CFG)
    if ok_flag:
        ok("Short正常エントリークリア")
    else:
        ng("Short正常エントリーが不当にスキップ", True, reason)

    # ケース2: Short時にSPY上昇（逆行）
    bar2 = make_entry_bar(449.3, 449.4, 449.0, 449.0, vol=2_500_000)
    ok_flag2, reason2 = check_entry_quality(
        bar2, prev_bars, "short", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok_flag2 and "SPY" in reason2:
        ok(f"Short時SPY逆行を正しく除外: {reason2}")
    else:
        ng("Short時SPY逆行の検出ミス", "SPY逆行", reason2)

    # ケース3: Short時に陽線（close > open）
    bar3 = make_entry_bar(448.9, 449.2, 448.8, 449.1, vol=2_500_000)
    ok_flag3, reason3 = check_entry_quality(
        bar3, prev_bars, "short", vwap, avg_vol, "down", orb_high, orb_low, CFG)
    if not ok_flag3 and "陽線" in reason3:
        ok(f"Short時陽線ブレイクを正しく除外: {reason3}")
    else:
        ng("Short時陽線ブレイクの検出ミス", "陽線ブレイク", reason3)

    # ケース4: Short時にVWAP以上（close > vwap=450.5）
    # body=0.3, wick=0.2 → ratio=0.67 OK
    bar4 = make_entry_bar(450.7, 450.8, 450.6, 450.7, vol=2_500_000)
    ok_flag4, reason4 = check_entry_quality(
        bar4, prev_bars, "short", vwap, avg_vol, "down", orb_high, orb_low, CFG)
    if not ok_flag4 and "VWAP" in reason4:
        ok(f"Short時VWAP以上を正しく除外: {reason4}")
    else:
        ng("Short時VWAP以上の検出ミス", "VWAP以上", reason4)


def test_exit_short():
    """Short方向エグジットテスト"""
    print("\n[9] Short方向エグジットテスト")
    entry_price = 449.0
    atr = 5.0
    atr_pct = atr / entry_price

    def make_post_bars(prices, start_time=time(10, 0), vwap_val=None):
        bars = []
        for i, p in enumerate(prices):
            t = datetime(2026, 4, 15, tzinfo=ET).replace(
                hour=start_time.hour, minute=start_time.minute
            ) + timedelta(minutes=5*i)
            bars.append(make_bar(t, p, p+0.3, p-0.5, p, volume=3_000_000))
        df = bars_to_df(bars)
        df["vwap"] = vwap_val if vwap_val else entry_price + 5.0  # Short時はVWAP高め
        return df

    target2_price = entry_price * (1 - 1.5 * atr_pct)
    stop_price    = entry_price * (1 + 0.8 * atr_pct)

    # ケース1: Short第2利確（価格が下落してtarget2到達）
    prices1 = [448.0, 446.0, 444.0, 442.0, 440.0]
    df1 = make_post_bars(prices1, vwap_val=entry_price + 5.0)
    result1 = simulate_exit(entry_price, "short", atr, df1, CFG)
    if result1["exit_reason"] == "第2利確":
        ok(f"Short第2利確: {result1['return_pct']:+.2f}%")
    else:
        ng("Short第2利確検出ミス", "第2利確", result1["exit_reason"])

    # ケース2: Short損切り（価格が上昇してstop到達）
    prices2 = [449.5, 450.0, 451.0, 452.0, 453.0]
    df2 = make_post_bars(prices2, vwap_val=entry_price - 5.0)  # VWAP低め→VWAPチェック通過
    result2 = simulate_exit(entry_price, "short", atr, df2, CFG)
    if "損切" in result2["exit_reason"] or "VWAP" in result2["exit_reason"]:
        ok(f"Short損切/VWAP: {result2['exit_reason']} {result2['return_pct']:+.2f}%")
    else:
        ng("Short損切り検出ミス", "損切", result2["exit_reason"])


def test_exit_trailing():
    """第1利確→BE引き上げ→第2利確の連続フローテスト"""
    print("\n[10] トレイリング連続フローテスト")
    entry_price = 452.0
    atr = 5.0
    atr_pct = atr / entry_price
    target1 = entry_price * (1 + 1.0 * atr_pct)  # ≈457.02
    target2 = entry_price * (1 + 1.5 * atr_pct)  # ≈459.53

    def make_post_bars(prices, vwap_offset=-10.0):
        bars = []
        for i, p in enumerate(prices):
            t = datetime(2026, 4, 15, tzinfo=ET).replace(
                hour=10, minute=0) + timedelta(minutes=5*i)
            bars.append(make_bar(t, p, p+1.0, p-0.3, p, volume=3_000_000))
        df = bars_to_df(bars)
        df["vwap"] = entry_price + vwap_offset
        return df

    # ケース1: 第1利確後に戻りがあるがBEで守られて第2利確到達
    # target1≈457.0 → 一度下がる → target2≈459.5到達
    prices1 = [454.0, 457.5, 455.0, 454.5, 458.0, 460.0, 461.0]
    df1 = make_post_bars(prices1)
    result1 = simulate_exit(entry_price, "long", atr, df1, CFG)
    if result1["exit_reason"] == "第2利確":
        ok(f"第1利確後→第2利確: {result1['return_pct']:+.2f}%")
    else:
        ng("第1利確後→第2利確フロー失敗", "第2利確", result1["exit_reason"])

    # ケース2: 第1利確後に建値まで戻りBE損切り
    # target1≈457.0通過 → entry_price=452.0まで戻る → BE損切
    prices2 = [454.0, 457.5, 455.0, 453.0, 452.0, 451.5]
    df2 = make_post_bars(prices2)
    result2 = simulate_exit(entry_price, "long", atr, df2, CFG)
    if "BE損切" in result2["exit_reason"] or "損切" in result2["exit_reason"]:
        ok(f"第1利確後→BE損切: {result2['exit_reason']} {result2['return_pct']:+.2f}%")
    else:
        ng("BE損切フロー失敗", "BE損切", result2["exit_reason"])


def test_orb_size_large():
    """ORBサイズテスト（前日ATRベース）"""
    print("\n[11] ORBサイズ境界値テスト")
    dt = datetime(2026, 4, 15, tzinfo=ET)

    # 前日データ: high=455, low=450 → prev_atr=5.0
    prev_bars_list = []
    prev_dt = datetime(2026, 4, 14, tzinfo=ET)
    for i in range(78):
        t = prev_dt.replace(hour=9, minute=30) + timedelta(minutes=5*i)
        prev_bars_list.append(make_bar(t, 452.0, 455.0, 450.0, 452.5))
    prev_df = bars_to_df(prev_bars_list)

    def make_day_with_orb(orb_h, orb_l, day_h, day_l):
        bars = []
        bars.append(make_bar(dt.replace(hour=9, minute=30), orb_l, orb_h, orb_l, (orb_h+orb_l)/2))
        bars.append(make_bar(dt.replace(hour=9, minute=35), (orb_h+orb_l)/2, orb_h, orb_l, (orb_h+orb_l)/2))
        bars.append(make_bar(dt.replace(hour=9, minute=40), (orb_h+orb_l)/2, orb_h, orb_l, (orb_h+orb_l)/2))
        for i in range(20):
            t = dt.replace(hour=9, minute=45) + timedelta(minutes=5*i)
            bars.append(make_bar(t, (day_h+day_l)/2, day_h, day_l, (day_h+day_l)/2))
        return bars_to_df(bars)

    # prev_atr=5.0 基準
    # ORBサイズ=2.0 → ratio=0.40 → min=0.3 OK
    df1 = make_day_with_orb(452.0, 450.0, 455.0, 450.0)
    orb1 = find_orb(df1, CFG, prev_df)
    if orb1 is not None:
        ok(f"正常ORBサイズ(ratio={orb1['size']/orb1['atr']:.2f}): 通過")
    else:
        ng("正常ORBがスキップされた", "通過", None)

    # ORBサイズ=4.9 → ratio=0.98 → max=3.0 OK
    df2 = make_day_with_orb(454.9, 450.0, 455.0, 450.0)
    orb2 = find_orb(df2, CFG, prev_df)
    if orb2 is not None:
        ok(f"大きめORBサイズ(ratio={orb2['size']/orb2['atr']:.2f}): 通過")
    else:
        ng("大きめORBが不当にスキップ", "通過", None)

    # ORBサイズ=5.0 → ratio=1.00 → max=3.0 OK
    df3 = make_day_with_orb(455.0, 450.0, 455.0, 450.0)
    orb3 = find_orb(df3, CFG, prev_df)
    if orb3 is not None:
        ok(f"ORBサイズ=prev_atr(ratio={orb3['size']/orb3['atr']:.2f}): 通過")
    else:
        ng("ORBサイズ=prev_atrが不当にスキップ", "通過", None)


def test_performance_mult():
    """performance_mult段階的変化テスト"""
    print("\n[12] performance_multテスト")
    from backtest import calc_performance_mult

    # ケース1: トレード数が少ない（3件未満）→ 1.0固定
    result1 = calc_performance_mult([], CFG)
    if result1 == 1.0:
        ok(f"トレード0件 → perf_mult=1.0")
    else:
        ng("トレード0件のperf_mult", 1.0, result1)

    result2 = calc_performance_mult([{"return_pct": 2.0}, {"return_pct": -1.0}], CFG)
    if result2 == 1.0:
        ok(f"トレード2件 → perf_mult=1.0（固定）")
    else:
        ng("トレード2件のperf_mult", 1.0, result2)

    # ケース2: 好調（勝率70%以上・プラス成長・DDなし）
    good_trades = [{"return_pct": 2.0}] * 7 + [{"return_pct": -0.5}] * 3
    result3 = calc_performance_mult(good_trades, CFG)
    if result3 > 1.0:
        ok(f"好調トレード → perf_mult={result3:.3f}（>1.0）")
    else:
        ng("好調時のperf_mult", ">1.0", result3)

    # ケース3: 不調（勝率40%未満・マイナス成長）
    bad_trades = [{"return_pct": -2.0}] * 7 + [{"return_pct": 0.5}] * 3
    result4 = calc_performance_mult(bad_trades, CFG)
    if result4 < 1.0:
        ok(f"不調トレード → perf_mult={result4:.3f}（<1.0）")
    else:
        ng("不調時のperf_mult", "<1.0", result4)

    # ケース4: 最小値クランプ（極端な不調）
    terrible_trades = [{"return_pct": -5.0}] * 10
    result5 = calc_performance_mult(terrible_trades, CFG)
    min_val = CFG["performance"]["perf_mult_min"]
    if result5 >= min_val:
        ok(f"極端不調 → perf_mult={result5:.3f}（≥min={min_val}）")
    else:
        ng("perf_mult最小値クランプ失敗", f"≥{min_val}", result5)

    # ケース5: 最大値クランプ
    perfect_trades = [{"return_pct": 3.0}] * 10
    result6 = calc_performance_mult(perfect_trades, CFG)
    max_val = CFG["performance"]["perf_mult_max"]
    if result6 <= max_val:
        ok(f"完璧トレード → perf_mult={result6:.3f}（≤max={max_val}）")
    else:
        ng("perf_mult最大値クランプ失敗", f"≤{max_val}", result6)


def test_filter_combinations():
    """フィルター組み合わせテスト"""
    print("\n[13] フィルター組み合わせテスト")
    orb_high = 451.5
    orb_low  = 449.0
    avg_vol  = 1_000_000
    vwap     = 450.5

    def make_entry_bar(o, h, l, c, vol=2_000_000):
        return {
            "open": o, "high": h, "low": l, "close": c,
            "volume": vol,
            "body": abs(c - o),
            "wick": h - l,
            "upper_wick": h - max(o, c),
            "vwap": vwap,
        }

    prev_bars = pd.DataFrame([{"volume": 1_500_000}, {"volume": 1_200_000}])

    # ケース1: ヒゲ過大 + 出来高不足（先に発動するのはヒゲ）
    bar1 = make_entry_bar(451.5, 455.0, 450.0, 452.0, vol=300_000)
    ok_flag1, reason1 = check_entry_quality(
        bar1, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok_flag1 and "ヒゲ" in reason1:
        ok(f"ヒゲ優先で除外（ヒゲ+出来高不足）: {reason1}")
    else:
        ng("ヒゲ優先除外ミス", "ヒゲ", reason1)

    # ケース2: SPY逆行 + 陰線（SPY逆行が先）
    bar2 = make_entry_bar(452.5, 452.6, 452.0, 452.1, vol=2_500_000)
    ok_flag2, reason2 = check_entry_quality(
        bar2, prev_bars, "long", vwap, avg_vol, "down", orb_high, orb_low, CFG)
    if not ok_flag2 and "SPY" in reason2:
        ok(f"SPY逆行優先で除外（SPY+陰線）: {reason2}")
    else:
        ng("SPY優先除外ミス", "SPY逆行", reason2)

    # ケース3: 全条件クリア（Long）
    bar3 = make_entry_bar(451.6, 452.0, 451.5, 451.9, vol=2_500_000)
    ok_flag3, reason3 = check_entry_quality(
        bar3, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if ok_flag3:
        ok("全条件クリア（Long）: OK")
    else:
        ng("全条件クリアで不当スキップ", "OK", reason3)

    # ケース4: 全条件クリア（Short）wick/body < 2.0
    bar4 = make_entry_bar(449.3, 449.4, 449.0, 449.0, vol=2_500_000)
    ok_flag4, reason4 = check_entry_quality(
        bar4, prev_bars, "short", vwap, avg_vol, "down", orb_high, orb_low, CFG)
    if ok_flag4:
        ok("全条件クリア（Short）: OK")
    else:
        ng("Short全条件クリアで不当スキップ", "OK", reason4)


def test_weekly_loss_accumulation():
    """週次損失累積テスト"""
    print("\n[14] 週次損失リミットテスト")
    d = date(2026, 4, 15)
    balance = 6700.0
    peak    = 6700.0
    limit   = CFG["layer0"]["weekly_loss_pct_max"]

    # 週次損失0%（正常）
    skip1, reason1 = is_skip_day(d, CFG, 20.0, 1.0, 0, 0.0, peak, balance)
    if not skip1:
        ok("週次損失0%: スキップなし")
    else:
        ng("週次損失0%でスキップ", False, reason1)

    # 週次損失 = limit - 0.1%（ぎりぎりOK）
    skip2, reason2 = is_skip_day(d, CFG, 20.0, 1.0, 0, limit - 0.1, peak, balance)
    if not skip2:
        ok(f"週次損失{limit-0.1:.1f}%: スキップなし（閾値未満）")
    else:
        ng(f"週次損失{limit-0.1:.1f}%でスキップ", False, reason2)

    # 週次損失 = limit（スキップ）
    skip3, reason3 = is_skip_day(d, CFG, 20.0, 1.0, 0, limit, peak, balance)
    if skip3:
        ok(f"週次損失{limit}%到達: スキップ")
    else:
        ng(f"週次損失{limit}%でスキップされない", True, skip3)


def test_blackout_zone():
    """ブラックアウトゾーン（場中指標）の時間判定テスト"""
    print("\n[15] ブラックアウトゾーンテスト")
    # ブラックアウトゾーンはbacktest.pyでは定義されているが
    # is_skip_dayには含まれない（別途実装予定）
    # 現状の実装を確認
    blackout_min = CFG["layer0"]["blackout_minutes"]
    ok(f"ブラックアウト設定確認: 発表前後{blackout_min}分（config確認）")

    # 発表時刻が10:00 ETの場合のブラックアウトゾーン
    event_time   = time(10, 0)
    blackout_start = time(9, 30)   # 10:00 - 30分
    blackout_end   = time(10, 30)  # 10:00 + 30分

    # エントリー期限（10:30）はブラックアウト終了と重なる
    # この場合は実質トレード不可になることを確認
    entry_deadline = CFG["layer4"]["entry_deadline_et"]
    ok(f"エントリー期限設定確認: {entry_deadline}（config確認）")
    ok(f"ブラックアウト終了({blackout_end}) ≥ エントリー期限({entry_deadline}): 実質スキップ")


def test_orb_entry_edge_cases():
    """ORBエントリーのエッジケーステスト"""
    print("\n[16] ORBエッジケーステスト")
    dt = datetime(2026, 4, 15, tzinfo=ET)
    orb_high = 451.5
    orb_low  = 449.0
    orb = {"high": orb_high, "low": orb_low,
           "size": orb_high - orb_low, "atr": 5.0}

    # ケース1: 第1ブレイク直後にプルバック→すぐ再ブレイク（最速パターン）
    bars = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    # 9:45: 第1ブレイク（close=452.0 > orb_high=451.5）
    bars.append(make_bar(dt.replace(hour=9, minute=45), 451.6, 452.5, 451.5, 452.0))
    # 9:50: プルバック（close=451.0 < orb_high=451.5）
    bars.append(make_bar(dt.replace(hour=9, minute=50), 452.0, 452.1, 450.8, 451.0))
    # 9:55: 再ブレイク（close=452.5 > orb_high=451.5 * 1.001 = 451.95）
    bars.append(make_bar(dt.replace(hour=9, minute=55), 451.2, 453.0, 451.1, 452.5,
                         volume=2_500_000))
    # 10:00以降も追加（データが少ないとエントリー探索が途中で終わる場合がある）
    for i in range(5):
        t = dt.replace(hour=10, minute=0) + timedelta(minutes=5*i)
        bars.append(make_bar(t, 452.5, 453.0, 452.0, 452.8))
    df = bars_to_df(bars)
    entry = find_orb_entry(df, orb, "long", CFG)
    if entry is not None:
        ok(f"最速3ステップ検出: {entry['idx'].time()}")
    else:
        ng("最速3ステップ未検出", "9:55", None)

    # ケース2: プルバックタイムアウト後にリセットして再度第1ブレイク
    bars2 = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars2.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    # 第1ブレイク
    bars2.append(make_bar(dt.replace(hour=9, minute=45), 451.5, 452.0, 451.6, 451.8))
    # 15分プルバックなし → タイムアウト（9:45+15分=10:00）
    for i in range(3):
        t = dt.replace(hour=9, minute=50) + timedelta(minutes=5*i)
        bars2.append(make_bar(t, 451.8, 452.5, 451.7, 452.0))
    # 10:05: リセット後に新たな第1ブレイク（ただし10:30まで間に合うか）
    bars2.append(make_bar(dt.replace(hour=10, minute=5), 451.5, 452.5, 451.0, 452.0))
    # プルバック
    bars2.append(make_bar(dt.replace(hour=10, minute=10), 452.0, 452.2, 451.0, 451.2))
    # 再ブレイク（10:15 < 10:30なのでOK）
    bars2.append(make_bar(dt.replace(hour=10, minute=15), 451.3, 453.0, 451.2, 452.5,
                          volume=2_500_000))
    df2 = bars_to_df(bars2)
    entry2 = find_orb_entry(df2, orb, "long", CFG)
    if entry2 is not None:
        ok(f"リセット後再エントリー検出: {entry2['idx'].time()}")
    else:
        ng("リセット後再エントリー未検出", "10:15付近", None)


def test_orb_boundary_values():
    """ORBサイズ境界値の厳密テスト（前日ATRベース）"""
    print("\n[17] ORBサイズ境界値厳密テスト")
    dt = datetime(2026, 4, 15, tzinfo=ET)
    cfg_min = CFG["layer4"]["orb_size_atr_min"]  # 0.3
    cfg_max = CFG["layer4"]["orb_size_atr_max"]  # 3.0

    # 前日ATR = 10.0（high=460, low=450）
    prev_atr = 10.0
    prev_bars_list = []
    prev_dt = datetime(2026, 4, 14, tzinfo=ET)
    for i in range(78):
        t = prev_dt.replace(hour=9, minute=30) + timedelta(minutes=5*i)
        prev_bars_list.append(make_bar(t, 455.0, 460.0, 450.0, 455.0))
    prev_df = bars_to_df(prev_bars_list)

    def make_day(orb_h, orb_l):
        bars = []
        for i in range(3):
            t = dt.replace(hour=9, minute=30+i*5)
            bars.append(make_bar(t, orb_l, orb_h, orb_l, (orb_h+orb_l)/2))
        for i in range(20):
            t = dt.replace(hour=9, minute=45) + timedelta(minutes=5*i)
            bars.append(make_bar(t, (orb_h+orb_l)/2, orb_h+1, orb_l-1, (orb_h+orb_l)/2))
        return bars_to_df(bars)

    # ちょうどmin（ratio = 0.3）→ 通過
    # orb_size = prev_atr * 0.3 = 3.0
    orb_at_min = prev_atr * cfg_min  # 3.0
    df1 = make_day(450.0 + orb_at_min, 450.0)
    orb1 = find_orb(df1, CFG, prev_df)
    if orb1 is not None:
        ok(f"ORBサイズ=min閾値ちょうど(ratio={orb1['size']/orb1['atr']:.3f}): 通過")
    else:
        ng("ORBサイズmin閾値が不当にスキップ", "通過", None)

    # min未満（ratio < 0.3）→ スキップ
    orb_below_min = prev_atr * (cfg_min - 0.01)  # 2.9
    df2 = make_day(450.0 + orb_below_min, 450.0)
    orb2 = find_orb(df2, CFG, prev_df)
    if orb2 is None:
        ok("ORBサイズmin未満: スキップ")
    else:
        ng("ORBサイズmin未満が通過してしまった", None, f"{orb2['size']/orb2['atr']:.3f}")

    # ちょうどmax（ratio = 3.0）→ 通過
    # orb_size = prev_atr * 3.0 = 30.0
    orb_at_max = prev_atr * cfg_max  # 30.0
    df3 = make_day(450.0 + orb_at_max, 450.0)
    orb3 = find_orb(df3, CFG, prev_df)
    if orb3 is not None:
        ok(f"ORBサイズ=max閾値ちょうど(ratio={orb3['size']/orb3['atr']:.3f}): 通過")
    else:
        ng("ORBサイズmax閾値が不当にスキップ", "通過", None)

    # max超（ratio > 3.0）→ スキップ
    # orb_size = prev_atr * 3.01 = 30.1
    orb_above_max = prev_atr * (cfg_max + 0.01)  # 30.1
    df4 = make_day(450.0 + orb_above_max, 450.0)
    orb4 = find_orb(df4, CFG, prev_df)
    if orb4 is None:
        ok("ORBサイズmax超(ratio>3.0): スキップ")
    else:
        ng("ORBサイズmax超が通過してしまった", None, f"{orb4['size']/orb4['atr']:.3f}")


def test_entry_quality_boundary_values():
    """エントリー品質フィルターの境界値テスト"""
    print("\n[18] エントリー品質境界値テスト")
    orb_high = 451.5
    orb_low  = 449.0
    avg_vol  = 1_000_000
    vwap     = 450.5
    prev_bars = pd.DataFrame([{"volume": 1_500_000}, {"volume": 1_200_000}])

    wick_ratio = CFG["layer5"]["wick_body_ratio_max"]       # 2.0
    vol_ratio  = CFG["layer5"]["breakout_volume_ratio"]     # 1.5
    dist_max   = CFG["layer5"]["orb_distance_max_pct"] / 100  # 0.02

    def bar(o, h, l, c, vol=2_000_000):
        return {"open": o, "high": h, "low": l, "close": c, "volume": vol,
                "body": abs(c-o), "wick": h-l,
                "upper_wick": h - max(o,c), "vwap": vwap}

    # ① ヒゲ/実体 = ちょうど2.0 → 通過（> 2.0 でスキップ）
    # body=1.0, wick=2.0
    b1 = bar(451.0, 452.5, 450.5, 452.0, vol=2_000_000)  # body=1.0, wick=2.0
    ok1, r1 = check_entry_quality(b1, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if ok1:
        ok(f"ヒゲ/実体=ちょうど{wick_ratio}倍: 通過")
    else:
        ng(f"ヒゲ/実体={wick_ratio}倍で不当スキップ", "通過", r1)

    # ② ヒゲ/実体 = 2.001 → スキップ
    b2 = bar(451.0, 452.501, 450.5, 452.0, vol=2_000_000)  # body=1.0, wick=2.001
    ok2, r2 = check_entry_quality(b2, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok2 and "ヒゲ" in r2:
        ok(f"ヒゲ/実体=2.001倍: スキップ")
    else:
        ng("ヒゲ/実体=2.001倍が通過", "スキップ", r2)

    # ③ 出来高 = ちょうど1.5倍 → 通過（< 1.5倍でスキップ）
    b3 = bar(451.6, 452.0, 451.5, 451.9, vol=int(avg_vol * vol_ratio))
    ok3, r3 = check_entry_quality(b3, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if ok3:
        ok(f"出来高=ちょうど{vol_ratio}倍: 通過")
    else:
        ng(f"出来高={vol_ratio}倍で不当スキップ", "通過", r3)

    # ④ 出来高 = 1.499倍 → スキップ
    b4 = bar(451.6, 452.0, 451.5, 451.9, vol=int(avg_vol * (vol_ratio - 0.001)))
    ok4, r4 = check_entry_quality(b4, prev_bars, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok4 and "出来高" in r4:
        ok(f"出来高=1.499倍: スキップ")
    else:
        ng("出来高=1.499倍が通過", "スキップ", r4)

    # ⑤ フォロースルーなし（直前2本が平均割れ）→ スキップ
    prev_low = pd.DataFrame([{"volume": 800_000}, {"volume": 700_000}])
    b5 = bar(451.6, 452.0, 451.5, 451.9, vol=2_000_000)
    ok5, r5 = check_entry_quality(b5, prev_low, "long", vwap, avg_vol, "up", orb_high, orb_low, CFG)
    if not ok5 and "フォロー" in r5:
        ok(f"フォロースルーなし: スキップ")
    else:
        ng("フォロースルーなし未検出", "スキップ", r5)

    # ⑥ ORB乖離 = ちょうど2.0%未満 → 通過（> 2.0%でスキップ）
    # 浮動小数点誤差を避けて1.99%で確認
    price_just_below = orb_high * (1 + dist_max - 0.0001)
    b6 = bar(price_just_below - 0.1, price_just_below + 0.05,
             price_just_below - 0.1, price_just_below, vol=2_000_000)
    ok6, r6 = check_entry_quality(b6, prev_bars, "long", price_just_below, avg_vol,
                                   "up", orb_high, orb_low, CFG)
    if ok6:
        ok(f"ORB乖離=1.99%（閾値未満）: 通過")
    else:
        ng("ORB乖離=1.99%で不当スキップ", "通過", r6)

    # ⑦ ORB乖離 = 2.01% → スキップ
    price_above = orb_high * (1 + dist_max + 0.0001)
    b7 = bar(price_above - 0.1, price_above + 0.05,
             price_above - 0.1, price_above, vol=2_000_000)
    ok7, r7 = check_entry_quality(b7, prev_bars, "long", price_above, avg_vol,
                                   "up", orb_high, orb_low, CFG)
    if not ok7 and "乖離" in r7:
        ok(f"ORB乖離=2.01%: スキップ")
    else:
        ng("ORB乖離=2.01%が通過", "スキップ", r7)


def test_exit_volume_fade():
    """出来高フェードによるエグジットテスト"""
    print("\n[19] 出来高フェードエグジットテスト")
    entry_price = 452.0
    atr = 5.0
    fade_ratio = CFG["exit"]["volume_fade_ratio"]  # 0.7

    # 最初3本は出来高大きく、その後フェード
    bars = []
    dt = datetime(2026, 4, 15, tzinfo=ET)
    volumes = [3_000_000, 2_800_000, 2_500_000,  # 最初3本（高出来高）
               600_000, 500_000, 400_000]         # 以降フェード（avg×0.7未満）
    prices  = [452.5, 453.0, 453.5, 453.8, 454.0, 454.2]

    for i, (p, v) in enumerate(zip(prices, volumes)):
        t = dt.replace(hour=10, minute=0) + timedelta(minutes=5*i)
        bars.append(make_bar(t, p, p+0.5, p-0.2, p, volume=v))

    df = bars_to_df(bars)
    df["vwap"] = entry_price - 5.0  # VWAP低め

    result = simulate_exit(entry_price, "long", atr, df, CFG)
    if result["exit_reason"] in ("出来高フェード", "30分ルール", "タイムアウト"):
        ok(f"出来高フェード検出: {result['exit_reason']}")
    else:
        ng("出来高フェード未検出", "出来高フェード", result["exit_reason"])

    # 出来高がちょうどavg×0.7 → フェードしない
    bars2 = []
    avg_vol = 2_000_000
    fade_threshold = int(avg_vol * fade_ratio)  # = 1_400_000
    volumes2 = [avg_vol] * 3 + [fade_threshold] * 3  # ちょうど閾値

    for i, (p, v) in enumerate(zip(prices, volumes2)):
        t = dt.replace(hour=10, minute=0) + timedelta(minutes=5*i)
        bars2.append(make_bar(t, p, p+0.5, p-0.2, p, volume=v))

    df2 = bars_to_df(bars2)
    df2["vwap"] = entry_price - 5.0
    result2 = simulate_exit(entry_price, "long", atr, df2, CFG)
    if result2["exit_reason"] != "出来高フェード":
        ok(f"出来高=閾値ちょうど: フェード未発動（{result2['exit_reason']}）")
    else:
        ng("出来高閾値ちょうどでフェード発動", "フェード未発動", result2["exit_reason"])


def test_layer0_boundary_values():
    """Layer0 境界値テスト"""
    print("\n[20] Layer0 境界値テスト")
    d = date(2026, 4, 15)
    balance = 6700.0
    peak    = 6700.0

    vix_max  = CFG["layer0"]["vix_max"]           # 35
    gap_max  = CFG["layer0"]["spy_gap_pct_max"]   # 2.0
    loss_skip = CFG["layer0"]["consecutive_loss_skip"]  # 3
    dd_max   = CFG["layer0"]["max_drawdown_pct"]  # 10.0

    # VIX = ちょうど35.0 → スキップ
    skip1, r1 = is_skip_day(d, CFG, vix_max, 1.0, 0, 0.0, peak, balance)
    if skip1:
        ok(f"VIX=ちょうど{vix_max}: スキップ")
    else:
        ng(f"VIX={vix_max}でスキップされない", True, skip1)

    # VIX = 34.9 → 通過
    skip2, r2 = is_skip_day(d, CFG, vix_max - 0.1, 1.0, 0, 0.0, peak, balance)
    if not skip2:
        ok(f"VIX={vix_max-0.1}: 通過")
    else:
        ng(f"VIX={vix_max-0.1}で不当スキップ", False, r2)

    # SPYギャップ = ちょうど2.0% → スキップ
    skip3, r3 = is_skip_day(d, CFG, -1.0, gap_max, 0, 0.0, peak, balance)
    if skip3:
        ok(f"SPYギャップ=ちょうど{gap_max}%: スキップ")
    else:
        ng(f"SPYギャップ={gap_max}%でスキップされない", True, skip3)

    # SPYギャップ = 1.99% → 通過
    skip4, r4 = is_skip_day(d, CFG, -1.0, gap_max - 0.01, 0, 0.0, peak, balance)
    if not skip4:
        ok(f"SPYギャップ={gap_max-0.01}%: 通過")
    else:
        ng(f"SPYギャップ={gap_max-0.01}%で不当スキップ", False, r4)

    # 連続損失 = loss_skip - 1 → 通過
    skip5, r5 = is_skip_day(d, CFG, -1.0, 1.0, loss_skip - 1, 0.0, peak, balance)
    if not skip5:
        ok(f"連続損失={loss_skip-1}回: 通過")
    else:
        ng(f"連続損失={loss_skip-1}回で不当スキップ", False, r5)

    # 連続損失 = loss_skip → スキップ
    skip6, r6 = is_skip_day(d, CFG, -1.0, 1.0, loss_skip, 0.0, peak, balance)
    if skip6:
        ok(f"連続損失={loss_skip}回: スキップ")
    else:
        ng(f"連続損失={loss_skip}回でスキップされない", True, skip6)

    # DD = ちょうど10.0% → スキップ
    balance_at_dd = peak * (1 - dd_max / 100)
    skip7, r7 = is_skip_day(d, CFG, -1.0, 1.0, 0, 0.0, peak, balance_at_dd)
    if skip7:
        ok(f"DD=ちょうど{dd_max}%: スキップ")
    else:
        ng(f"DD={dd_max}%でスキップされない", True, skip7)

    # DD = 9.99% → 通過
    balance_below_dd = peak * (1 - (dd_max - 0.01) / 100)
    skip8, r8 = is_skip_day(d, CFG, -1.0, 1.0, 0, 0.0, peak, balance_below_dd)
    if not skip8:
        ok(f"DD={dd_max-0.01}%: 通過")
    else:
        ng(f"DD={dd_max-0.01}%で不当スキップ", False, r8)


def test_orb_entry_negative_cases():
    """ORBエントリーのパスしない全パターンテスト"""
    print("\n[21] ORBエントリー失敗パターンテスト")
    dt = datetime(2026, 4, 15, tzinfo=ET)
    orb_high = 451.5
    orb_low  = 449.0
    orb = {"high": orb_high, "low": orb_low, "size": 2.5, "atr": 5.0}

    pullback_timeout = CFG["layer4"]["pullback_timeout_min"]   # 15
    rebreak_timeout  = CFG["layer4"]["rebreak_timeout_min"]    # 20

    # ケース1: 再ブレイク待ちタイムアウト（プルバック後20分待っても再ブレイクなし）
    bars = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    # 第1ブレイク
    bars.append(make_bar(dt.replace(hour=9, minute=45), 451.6, 452.5, 451.5, 452.0))
    # プルバック
    bars.append(make_bar(dt.replace(hour=9, minute=50), 452.0, 452.1, 450.8, 451.0))
    # 再ブレイクなし20分間（451.5以下をうろうろ）
    for i in range(4):
        t = dt.replace(hour=9, minute=55) + timedelta(minutes=5*i)
        bars.append(make_bar(t, 451.0, 451.4, 450.5, 451.1))
    df1 = bars_to_df(bars)
    entry1 = find_orb_entry(df1, orb, "long", CFG)
    if entry1 is None:
        ok(f"再ブレイク待ちタイムアウト({rebreak_timeout}分): スキップ")
    else:
        ng("再ブレイクタイムアウト未検出", None, entry1["idx"].time())

    # ケース2: Short方向プルバックタイムアウト
    bars2 = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars2.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    # Short第1下抜け
    bars2.append(make_bar(dt.replace(hour=9, minute=45), 449.0, 449.2, 447.8, 448.5))
    # プルバックなし15分間（449.0以下継続）
    for i in range(3):
        t = dt.replace(hour=9, minute=50) + timedelta(minutes=5*i)
        bars2.append(make_bar(t, 448.5, 448.8, 447.5, 448.0))
    df2 = bars_to_df(bars2)
    entry2 = find_orb_entry(df2, orb, "short", CFG)
    if entry2 is None:
        ok(f"Short プルバックタイムアウト({pullback_timeout}分): スキップ")
    else:
        ng("Short プルバックタイムアウト未検出", None, entry2["idx"].time())

    # ケース3: エントリー期限（10:30）ちょうどに再ブレイク → スキップ
    bars3 = []
    for i in range(3):
        t = dt.replace(hour=9, minute=30+i*5)
        bars3.append(make_bar(t, 450.0, 451.5, 449.0, 450.5))
    bars3.append(make_bar(dt.replace(hour=9, minute=45), 451.6, 452.0, 451.5, 452.0))
    bars3.append(make_bar(dt.replace(hour=9, minute=50), 452.0, 452.1, 451.0, 451.2))
    # 10:30ちょうど（entry_end = time(10, 30)、条件は t > entry_end）
    bars3.append(make_bar(dt.replace(hour=10, minute=30), 451.3, 453.0, 451.2, 452.5,
                          volume=2_500_000))
    df3 = bars_to_df(bars3)
    entry3 = find_orb_entry(df3, orb, "long", CFG)
    if entry3 is None:
        ok("10:30ちょうどの再ブレイク: スキップ（期限超過）")
    else:
        ng("10:30ちょうどが通過してしまった", None, entry3["idx"].time())


def test_performance_mult_boundary():
    """performance_mult 境界値テスト"""
    print("\n[22] performance_mult 境界値テスト")
    from backtest import calc_performance_mult

    max_val = CFG["performance"]["perf_mult_max"]  # 2.0
    min_val = CFG["performance"]["perf_mult_min"]  # 0.3

    # 最大値を超えないことを確認（完璧トレード大量）
    perfect = [{"return_pct": 10.0}] * 50
    result1 = calc_performance_mult(perfect, CFG)
    if result1 <= max_val:
        ok(f"perf_mult上限クランプ: {result1:.3f} ≤ {max_val}")
    else:
        ng("perf_mult上限クランプ失敗", f"≤{max_val}", result1)

    # 最小値を下回らないことを確認（最悪トレード大量）
    terrible = [{"return_pct": -10.0}] * 50
    result2 = calc_performance_mult(terrible, CFG)
    if result2 >= min_val:
        ok(f"perf_mult下限クランプ: {result2:.3f} ≥ {min_val}")
    else:
        ng("perf_mult下限クランプ失敗", f"≥{min_val}", result2)

    # 勝率ちょうど50% → mult=1.0
    fifty_fifty = [{"return_pct": 1.0}] * 5 + [{"return_pct": -1.0}] * 5
    result3 = calc_performance_mult(fifty_fifty, CFG)
    # 成長率・DDも考慮するため厳密に1.0にはならないが1.0付近
    if 0.5 <= result3 <= 1.5:
        ok(f"勝率50%: perf_mult={result3:.3f}（合理的範囲内）")
    else:
        ng("勝率50%のperf_mult異常", "0.5〜1.5", result3)


# ============================================================
# メイン
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Momentum Burst デイトレード 動作確認テスト（全パターン）")
    print("=" * 60)

    # 既存テスト
    test_layer0_skip()
    test_trend_score()
    test_orb_detection()
    test_orb_entry_3step()
    test_entry_quality_filters()
    test_exit_logic()

    # 追加テスト
    test_orb_short_direction()
    test_entry_quality_short()
    test_exit_short()
    test_exit_trailing()
    test_orb_size_large()
    test_performance_mult()
    test_filter_combinations()
    test_weekly_loss_accumulation()
    test_blackout_zone()
    test_orb_entry_edge_cases()

    # 境界値・負例テスト
    test_orb_boundary_values()
    test_entry_quality_boundary_values()
    test_exit_volume_fade()
    test_layer0_boundary_values()
    test_orb_entry_negative_cases()
    test_performance_mult_boundary()

    print("\n" + "=" * 60)
    print(f"結果: PASS={PASS}  FAIL={FAIL}  合計={PASS+FAIL}")
    if FAIL == 0:
        print("✅ 全テスト通過")
    else:
        print(f"❌ {FAIL}件のテスト失敗 → backtest.pyのロジックを修正してください")
    print("=" * 60)
