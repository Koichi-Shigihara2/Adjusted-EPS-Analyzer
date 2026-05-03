"""
F&G第2水準戦略 拡張分析スクリプト
====================================
Step A: TQQQバックテスト（利確20%の到達率検証）
Step B: 年別パフォーマンス分解（QQQ / TQQQ）
Step C: 個別株バックテスト（NVDA / PLTR / QQQ比較）
Step D: サマリーレポート出力

使い方:
  python fg_level2_extended.py --fetch          # TQQQ・個別株データ取得
  python fg_level2_extended.py                  # 全分析実行
  python fg_level2_extended.py --step A         # 個別ステップ実行
  python fg_level2_extended.py --step B
  python fg_level2_extended.py --step C
"""

import argparse
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

warnings.filterwarnings("ignore")

# ============================================================
# 設定
# ============================================================
BASE_DIR    = Path(__file__).parent
FG_CSV      = BASE_DIR / "fg_historical.csv"
OUTPUT_DIR  = BASE_DIR / "backtest_results" / "extended"

TICKERS_EXTRA = ["TQQQ", "NVDA", "PLTR"]
PRIMARY_FG_ZONE = (11, 20)   # Level2 本戦略

COOLDOWN_DAYS = 5

# 条件マトリクス
TARGET_GAINS   = [0.10, 0.15, 0.20]
HOLD_DAYS_LIST = [30, 60]

FG_ZONES = {
    "Extreme Fear (1-10)":  (1, 10),
    "Level2 Fear (11-20)":  (11, 20),
}

# ============================================================
# データ取得
# ============================================================

def fetch_prices(tickers: list, fg_path: Path) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    fg = pd.read_csv(fg_path, parse_dates=["date"])
    start = str(fg["date"].min().date())
    end   = datetime.today().strftime("%Y-%m-%d")

    prices = {}
    for t in tickers:
        csv_path = BASE_DIR / f"{t.lower()}_prices.csv"
        if csv_path.exists():
            print(f"  {t}: 既存CSV使用 ({csv_path.name})")
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            prices[t] = df
            continue

        print(f"  {t}: yfinance取得中...")
        df = yf.download(t, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            print(f"  ❌ {t} 取得失敗")
            continue
        df = df[["Close"]].rename(columns={"Close": t})
        df.index = pd.to_datetime(df.index)
        df.to_csv(csv_path, encoding="utf-8")
        print(f"  {t}: {len(df)}行 保存 → {csv_path.name}")
        prices[t] = df

    return prices


# ============================================================
# バックテスト共通ロジック
# ============================================================

def load_fg(fg_path: Path) -> pd.Series:
    fg = pd.read_csv(fg_path, parse_dates=["date"])
    fg.columns = [c.lower().strip() for c in fg.columns]
    score_col = next((c for c in fg.columns if "score" in c or "fg" in c), None)
    if score_col != "fg_score":
        fg = fg.rename(columns={score_col: "fg_score"})
    fg["fg_score"] = pd.to_numeric(fg["fg_score"], errors="coerce")
    fg = fg.dropna(subset=["date","fg_score"]).sort_values("date").reset_index(drop=True)
    return fg.set_index("date")["fg_score"]


def run_backtest(fg_series: pd.Series, price_series: pd.Series,
                 zone: tuple, target_gain: float, hold_days: int) -> list:
    # インデックスをDatetimeIndexに統一
    if not isinstance(price_series.index, pd.DatetimeIndex):
        price_series = price_series.copy()
        price_series.index = pd.to_datetime(price_series.index, errors="coerce")
        price_series = price_series[price_series.index.notna()]
    if not isinstance(fg_series.index, pd.DatetimeIndex):
        fg_series = fg_series.copy()
        fg_series.index = pd.to_datetime(fg_series.index, errors="coerce")
        fg_series = fg_series[fg_series.index.notna()]

    trading_days   = price_series.dropna().index.tolist()
    cooldown_until = pd.Timestamp("2000-01-01")
    trades = []

    for i, entry_date in enumerate(trading_days):
        if entry_date <= cooldown_until:
            continue
        if i + 1 >= len(trading_days):
            break

        # F&G確認
        candidates = fg_series.index[fg_series.index <= entry_date]
        if len(candidates) == 0:
            continue
        fg_date = candidates[-1]
        if (entry_date - fg_date).days > 3:
            continue
        fg_val = fg_series[fg_date]
        if not (zone[0] <= fg_val <= zone[1]):
            continue

        entry_price  = price_series[entry_date]
        target_price = entry_price * (1 + target_gain)
        stop_idx     = min(i + hold_days, len(trading_days) - 1)
        stop_date    = trading_days[stop_idx]
        future       = price_series.iloc[i:stop_idx + 1]
        hit_mask     = future >= target_price

        if hit_mask.any():
            exit_date  = hit_mask[hit_mask].index[0]
            exit_price = price_series[exit_date]
            hit_target = True
        else:
            exit_date  = stop_date
            exit_price = price_series[stop_date]
            hit_target = False

        trades.append({
            "entry_date":  entry_date,
            "exit_date":   exit_date,
            "year":        entry_date.year,
            "fg_score":    int(fg_val),
            "entry_price": round(float(entry_price), 4),
            "exit_price":  round(float(exit_price), 4),
            "return_pct":  round((float(exit_price) - float(entry_price)) / float(entry_price) * 100, 2),
            "hold_days":   (exit_date - entry_date).days,
            "hit_target":  hit_target,
        })
        cooldown_until = exit_date + timedelta(days=COOLDOWN_DAYS)

    return trades


def summarize(trades: list) -> dict:
    if not trades:
        return {"n": 0}
    df  = pd.DataFrame(trades)
    n   = len(df)
    pos = (df["return_pct"] > 0).sum()
    hit = df["hit_target"].sum()
    return {
        "n":               n,
        "win_rate":        round(pos / n * 100, 1),
        "target_hit_rate": round(hit / n * 100, 1),
        "avg_return":      round(df["return_pct"].mean(), 2),
        "median_return":   round(df["return_pct"].median(), 2),
        "max_return":      round(df["return_pct"].max(), 2),
        "min_return":      round(df["return_pct"].min(), 2),
        "avg_hold_days":   round(df["hold_days"].mean(), 1),
    }


# ============================================================
# Step A: TQQQバックテスト
# ============================================================

def step_a(fg_series: pd.Series, prices: dict):
    print("\n" + "="*70)
    print("Step A: TQQQバックテスト（利確10/15/20% × 30/60日）")
    print("="*70)

    if "TQQQ" not in prices:
        print("❌ TQQQデータなし。--fetch を実行してください。")
        return []

    p = prices["TQQQ"].iloc[:, 0]

    results = []
    for target in TARGET_GAINS:
        for hold in HOLD_DAYS_LIST:
            for zone_name, zone in FG_ZONES.items():
                trades = run_backtest(fg_series, p, zone, target, hold)
                s = summarize(trades)
                s.update({"ticker":"TQQQ","zone":zone_name,"target_pct":target*100,"hold_days":hold})
                results.append((s, trades))

    print(f"{'ゾーン':<24} {'利確':>5} {'保有':>4} {'N':>4} {'勝率':>7} {'達成率':>7} {'平均R':>7} {'最大':>7} {'最小':>7}")
    print("-"*70)
    for s, _ in results:
        if s["n"] == 0:
            continue
        print(f"{s['zone']:<24} {s['target_pct']:>4.0f}% {s['hold_days']:>3}日 {s['n']:>4}"
              f" {s['win_rate']:>6.1f}% {s['target_hit_rate']:>6.1f}%"
              f" {s['avg_return']:>6.1f}% {s['max_return']:>6.1f}% {s['min_return']:>6.1f}%")
    return results


# ============================================================
# Step B: 年別パフォーマンス分解
# ============================================================

def step_b(fg_series: pd.Series, prices: dict):
    print("\n" + "="*70)
    print("Step B: 年別パフォーマンス分解（Level2ゾーン / 利確10% / 60日）")
    print("="*70)

    tickers_avail = [t for t in ["QQQ", "TQQQ"] if t in prices]
    yearly_rows = []

    for ticker in tickers_avail:
        df_p = prices[ticker]
        p = df_p.iloc[:, 0]

        trades = run_backtest(fg_series, p, PRIMARY_FG_ZONE, 0.10, 60)
        df_t = pd.DataFrame(trades)
        if df_t.empty:
            continue

        print(f"\n--- {ticker} ---")
        print(f"{'年':<6} {'N':>4} {'勝率':>7} {'平均R':>7} {'中央値':>7} {'最大':>7} {'最小':>7}")
        print("-"*50)

        for year, grp in df_t.groupby("year"):
            n   = len(grp)
            wr  = round((grp["return_pct"] > 0).mean() * 100, 1)
            avg = round(grp["return_pct"].mean(), 1)
            med = round(grp["return_pct"].median(), 1)
            mx  = round(grp["return_pct"].max(), 1)
            mn  = round(grp["return_pct"].min(), 1)
            print(f"{year:<6} {n:>4} {wr:>6.1f}% {avg:>6.1f}% {med:>6.1f}% {mx:>6.1f}% {mn:>6.1f}%")
            yearly_rows.append({"ticker":ticker,"year":year,"n":n,"win_rate":wr,
                                 "avg_return":avg,"median":med,"max":mx,"min":mn})

    return yearly_rows


# ============================================================
# Step C: 個別株バックテスト
# ============================================================

def step_c(fg_series: pd.Series, prices: dict):
    print("\n" + "="*70)
    print("Step C: 個別株バックテスト（Level2ゾーン / 利確20% / 60日）")
    print("="*70)

    tickers = ["QQQ", "TQQQ", "NVDA", "PLTR"]
    avail   = [t for t in tickers if t in prices]

    results = []
    print(f"{'銘柄':<8} {'利確':>5} {'保有':>4} {'N':>4} {'勝率':>7} {'達成率':>7} {'平均R':>7} {'最大':>7} {'最小':>7}")
    print("-"*65)

    for ticker in avail:
        df_p = prices[ticker]
        col  = df_p.columns[0]
        p    = df_p[col]

        for target in [0.10, 0.20]:
            trades = run_backtest(fg_series, p, PRIMARY_FG_ZONE, target, 60)
            s = summarize(trades)
            s.update({"ticker": ticker, "target_pct": target * 100, "hold_days": 60})
            results.append(s)
            if s["n"] == 0:
                print(f"{ticker:<8} {target*100:>4.0f}%  60日    0  (シグナルなし)")
                continue
            print(f"{ticker:<8} {target*100:>4.0f}%  60日 {s['n']:>4}"
                  f" {s['win_rate']:>6.1f}% {s['target_hit_rate']:>6.1f}%"
                  f" {s['avg_return']:>6.1f}% {s['max_return']:>6.1f}% {s['min_return']:>6.1f}%")

    return results


# ============================================================
# Step D: サマリーレポート CSV 出力
# ============================================================

def step_d(step_a_results, step_b_rows, step_c_results):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if step_a_results:
        rows = [s for s, _ in step_a_results if s.get("n", 0) > 0]
        pd.DataFrame(rows).to_csv(OUTPUT_DIR / "tqqq_summary.csv", index=False, encoding="utf-8-sig")

    if step_b_rows:
        pd.DataFrame(step_b_rows).to_csv(OUTPUT_DIR / "yearly_breakdown.csv", index=False, encoding="utf-8-sig")

    if step_c_results:
        valid = [r for r in step_c_results if r.get("n", 0) > 0]
        pd.DataFrame(valid).to_csv(OUTPUT_DIR / "ticker_comparison.csv", index=False, encoding="utf-8-sig")

    print(f"\n[保存] {OUTPUT_DIR}/")
    print("  tqqq_summary.csv      — Step A TQQQ全条件")
    print("  yearly_breakdown.csv  — Step B 年別分解")
    print("  ticker_comparison.csv — Step C 銘柄比較")

    # コンソールサマリー
    print("\n" + "="*70)
    print("総合サマリー — Level2 (11-20) ゾーン / 60日保有")
    print("="*70)
    if step_c_results:
        print(f"{'銘柄':<8} {'利確':>5}  {'N':>4}  {'勝率':>7}  {'達成率':>7}  {'平均R':>7}")
        print("-"*50)
        for r in step_c_results:
            if r.get("n", 0) == 0:
                continue
            print(f"{r['ticker']:<8} {r['target_pct']:>4.0f}%  {r['n']:>4}  "
                  f"{r['win_rate']:>6.1f}%  {r['target_hit_rate']:>6.1f}%  {r['avg_return']:>6.1f}%")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="F&G Level2 拡張分析")
    parser.add_argument("--fetch", action="store_true", help="TQQQ・個別株データ取得")
    parser.add_argument("--step",  default="ALL", choices=["A","B","C","ALL"])
    parser.add_argument("--fg-csv", default=str(FG_CSV))
    args = parser.parse_args()

    fg_path = Path(args.fg_csv)

    if not fg_path.exists():
        print(f"❌ F&G CSVなし: {fg_path}")
        print("   fg_level2_backtest.py --fetch を先に実行してください")
        sys.exit(1)

    if args.fetch:
        print("[データ取得]")
        fetch_prices(TICKERS_EXTRA, fg_path)
        print("✅ 取得完了")
        return

    # CSVロード
    print("[読み込み中...]")
    fg_series = load_fg(fg_path)

    prices = {}
    for ticker in ["QQQ", "TQQQ", "NVDA", "PLTR"]:
        csv_path = BASE_DIR / f"{ticker.lower()}_prices.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path, index_col=0, header=0)
            # yfinance マルチヘッダー由来の "Ticker" 行を除去
            df = df[~df.index.astype(str).str.match(r'^(Ticker|Price|Date)$', na=False)]
            df.index = pd.to_datetime(df.index, errors="coerce")
            df = df[df.index.notna()]
            df = df.apply(pd.to_numeric, errors="coerce")
            prices[ticker] = df
            print(f"  {ticker}: {len(df)}行")
        else:
            print(f"  {ticker}: CSVなし（スキップ）")

    step_a_results, step_b_rows, step_c_results = [], [], []

    if args.step in ("A", "ALL"):
        step_a_results = step_a(fg_series, prices)

    if args.step in ("B", "ALL"):
        step_b_rows = step_b(fg_series, prices)

    if args.step in ("C", "ALL"):
        step_c_results = step_c(fg_series, prices)

    if args.step == "ALL":
        step_d(step_a_results, step_b_rows, step_c_results)

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()
