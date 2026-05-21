#!/usr/bin/env python3
"""
backfill_tech_pulse.py
market_data.json の tech_pulse が欠落しているエントリを補完する。

データソース:
  - QQQ/SPY: yfinance（過去データ）
  - VXN: FRED API VXNCLS（環境変数 FRED_API_KEY が必要）
  - F&G: market_data.json の fear_greed.score を再利用
         （feargreedchart.com は過去データを提供しないため）

スコア計算:
  固定範囲方式（±15%/±30%/±10%）でバックフィル。
  Z スコアは全エントリ補完後に 90 日ローリングで計算して付与する。

使い方:
  python src/market/market_pulse/backfill_tech_pulse.py
  python src/market/market_pulse/backfill_tech_pulse.py --dry-run
"""
import json
import os
import sys
import argparse
import statistics as _stats
from datetime import datetime, date, timezone, timedelta

import pandas as pd
import yfinance as yf

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
JSON_PATH = os.path.join(
    REPO_ROOT, "docs", "market-monitor", "market-pulse", "data", "market_data.json"
)

FRED_API_KEY = os.getenv("FRED_API_KEY")


# ── helpers ────────────────────────────────────────────────────────────────

def _tp_label(score):
    if score <= 20: return "EXTREME FEAR"
    if score <= 35: return "FEAR"
    if score <= 50: return "CAUTION"
    if score <= 65: return "NEUTRAL"
    if score <= 80: return "GREED"
    return "EXTREME GREED"


def _calc_score(qqq_vs_ma125, vxn_vs_ma50, qqq_vs_spy_20d):
    """固定範囲方式 Tech Pulse スコア（バックフィル専用）"""
    score = 50.0
    if qqq_vs_ma125 is not None:
        score += max(-25, min(25, qqq_vs_ma125 / 15 * 25))
    if vxn_vs_ma50 is not None:
        score += max(-20, min(20, -vxn_vs_ma50 / 30 * 20))
    if qqq_vs_spy_20d is not None:
        score += max(-15, min(15, qqq_vs_spy_20d / 10 * 15))
    return max(0, min(100, round(score)))


def _qqq_components(target: date, qqq_hist: pd.DataFrame, spy_hist: pd.DataFrame):
    """指定日時点の qqq_vs_ma125 / qqq_vs_spy_20d を返す"""
    try:
        qqq_sub = qqq_hist[qqq_hist.index <= target]
        spy_sub = spy_hist[spy_hist.index <= target]
        if len(qqq_sub) < 125:
            return None, None
        qqq_latest = float(qqq_sub["Close"].iloc[-1])
        ma125 = float(qqq_sub["Close"].iloc[-125:].mean())
        qqq_vs_ma125 = round((qqq_latest / ma125 - 1) * 100, 2)

        qqq_vs_spy_20d = None
        if len(qqq_sub) >= 21 and len(spy_sub) >= 21:
            qqq_ret = (float(qqq_sub["Close"].iloc[-1]) / float(qqq_sub["Close"].iloc[-21]) - 1) * 100
            spy_ret = (float(spy_sub["Close"].iloc[-1]) / float(spy_sub["Close"].iloc[-21]) - 1) * 100
            # 単純差分（%pt）: collect_and_send.py の新式と統一
            qqq_vs_spy_20d = round(qqq_ret - spy_ret, 2)
        return qqq_vs_ma125, qqq_vs_spy_20d
    except Exception as e:
        print(f"  [WARN] QQQ計算失敗: {e}")
        return None, None


def _vxn_components(target: date, vxn_series: pd.Series):
    """指定日時点の vxn_latest / vxn_vs_ma50 を返す"""
    try:
        vxn_sub = vxn_series[vxn_series.index <= target]
        if len(vxn_sub) < 50:
            return None, None
        vxn_latest = round(float(vxn_sub.iloc[-1]), 2)
        ma50 = float(vxn_sub.iloc[-50:].mean())
        vxn_vs_ma50 = round((vxn_latest / ma50 - 1) * 100, 2)
        return vxn_latest, vxn_vs_ma50
    except Exception as e:
        print(f"  [WARN] VXN計算失敗: {e}")
        return None, None


def _zscore_pass(all_data, window=90):
    """全エントリの乖離値を計算し 90 日ローリング Z スコアを付与する（インプレース更新）"""
    for i, entry in enumerate(all_data):
        tp = entry.get("tech_pulse")
        if not tp:
            continue
        tps = tp.get("score")
        fgs = (entry.get("fear_greed") or {}).get("score")
        if tps is None or fgs is None:
            continue
        div_val = round(float(tps) - float(fgs), 1)

        # 過去 window 日以内の乖離値を収集
        try:
            cur_dt = datetime.fromisoformat(entry.get("date", ""))
            if cur_dt.tzinfo is None:
                cur_dt = cur_dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        cutoff = cur_dt - timedelta(days=window)

        hist_divs = []
        for j in range(i):
            prev = all_data[j]
            prev_tp = prev.get("tech_pulse")
            if not prev_tp:
                continue
            prev_tps = prev_tp.get("score")
            prev_fgs = (prev.get("fear_greed") or {}).get("score")
            if prev_tps is None or prev_fgs is None:
                continue
            try:
                prev_dt = datetime.fromisoformat(prev.get("date", ""))
                if prev_dt.tzinfo is None:
                    prev_dt = prev_dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
            if prev_dt >= cutoff:
                hist_divs.append(float(prev_tps) - float(prev_fgs))

        hist_divs.append(div_val)
        zscore = None
        if len(hist_divs) >= 5:
            mean = _stats.mean(hist_divs)
            stdev = _stats.stdev(hist_divs)
            zscore = round((div_val - mean) / stdev, 2) if stdev else 0.0

        if "divergence" not in tp or tp["divergence"] is None:
            tp["divergence"] = {}
        tp["divergence"]["value"] = div_val
        tp["divergence"]["zscore"] = zscore

        # シグナル判定
        fg_score = (entry.get("fear_greed") or {}).get("score")
        signal = ""
        if zscore is not None and fg_score is not None:
            if fg_score < 30 and div_val > 10 and zscore > 1.0:
                signal = "ハイテク先行反発シグナル"
            elif div_val < -10 and zscore < -1.0:
                signal = "ハイテク先行下落注意"
        tp["divergence"]["signal"] = signal


# ── main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Tech Pulseバックフィルスクリプト")
    parser.add_argument("--dry-run", action="store_true", help="JSON を保存しない（確認用）")
    args = parser.parse_args()

    if not os.path.exists(JSON_PATH):
        print(f"[ERROR] {JSON_PATH} が見つかりません")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    missing_idx = [i for i, d in enumerate(all_data) if not d.get("tech_pulse")]
    if not missing_idx:
        print("[INFO] 全エントリに tech_pulse が存在します。Z スコアの再計算のみ行います。")
        _zscore_pass(all_data)
        if not args.dry_run:
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Z スコア更新完了: {JSON_PATH}")
        return

    print(f"[INFO] tech_pulse 欠落エントリ: {len(missing_idx)} 件 / 全 {len(all_data)} 件")

    # ── yfinance データ取得 ─────────────────────────────────────────
    print("[INFO] QQQ/SPY 履歴取得中...")
    qqq_hist = yf.Ticker("QQQ").history(period="1y")
    spy_hist = yf.Ticker("SPY").history(period="1y")

    if qqq_hist is None or len(qqq_hist) < 5:
        print("[ERROR] QQQ データ取得失敗")
        sys.exit(1)

    # DatetimeIndex → date オブジェクトへ正規化
    qqq_hist.index = pd.to_datetime(qqq_hist.index).normalize().date
    spy_hist.index = pd.to_datetime(spy_hist.index).normalize().date

    # ── FRED VXN 取得 ───────────────────────────────────────────────
    vxn_series = None
    if FRED_API_KEY:
        try:
            from fredapi import Fred
            start = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
            vxn_raw = Fred(api_key=FRED_API_KEY).get_series("VXNCLS", observation_start=start).dropna()
            vxn_series = vxn_raw.copy()
            vxn_series.index = pd.to_datetime(vxn_series.index).normalize().date
            print(f"[INFO] VXN データ取得完了: {len(vxn_series)} 件")
        except Exception as e:
            print(f"[WARN] VXN 取得失敗: {e}")
    else:
        print("[WARN] FRED_API_KEY 未設定。VXN はスキップします。")

    # ── 各エントリを補完 ────────────────────────────────────────────
    filled = 0
    for idx in missing_idx:
        entry = all_data[idx]
        d_str = entry.get("date", "")
        try:
            target = date.fromisoformat(d_str[:10])
        except Exception:
            print(f"[WARN] 日付パース失敗: {d_str!r}")
            continue

        qqq_vs_ma125, qqq_vs_spy_20d = _qqq_components(target, qqq_hist, spy_hist)
        vxn_latest, vxn_vs_ma50 = (
            _vxn_components(target, vxn_series) if vxn_series is not None else (None, None)
        )
        fg_score = (entry.get("fear_greed") or {}).get("score")

        tp_score = _calc_score(qqq_vs_ma125, vxn_vs_ma50, qqq_vs_spy_20d)
        tp_label = _tp_label(tp_score)
        div_val = round(float(tp_score) - float(fg_score), 1) if fg_score is not None else None

        entry["tech_pulse"] = {
            "score": tp_score,
            "label": tp_label,
            "components": {
                "qqq_vs_ma125": qqq_vs_ma125,
                "vxn_latest": vxn_latest,
                "vxn_vs_ma50": vxn_vs_ma50,
                "qqq_vs_spy_20d": qqq_vs_spy_20d,
                "fg_score": fg_score,
            },
            "divergence": {
                "value": div_val,
                "zscore": None,
                "signal": "",
            },
        }
        print(f"  {target}: score={tp_score:>3} ({tp_label:<14}) QvMA125={qqq_vs_ma125!s:>7}, QvSPY20={qqq_vs_spy_20d!s:>6}, VXNdev={vxn_vs_ma50!s:>6}, F&G={fg_score!s:>4}")
        filled += 1

    print(f"\n[INFO] 補完完了: {filled} 件")

    # ── Z スコアを全エントリに付与 ──────────────────────────────────
    print("[INFO] 乖離 Z スコアを再計算中...")
    _zscore_pass(all_data)

    if args.dry_run:
        print("[INFO] --dry-run モード: JSON は保存されません")
        return

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] JSON 保存完了: {JSON_PATH} (全 {len(all_data)} 件)")


if __name__ == "__main__":
    main()
