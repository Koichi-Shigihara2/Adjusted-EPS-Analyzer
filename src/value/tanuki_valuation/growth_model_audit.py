#!/usr/bin/env python3
"""
GROWTH-3 クランプ影響スキャン
全銘柄の成長率モデルを横断監査し、CAGR_max > 100% でクランプ発動している銘柄を特定。

実行方法:
    python src/value/tanuki_valuation/growth_model_audit.py
"""

import json
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent.parent.parent
DATA_DIR   = REPO_ROOT / "docs" / "value-monitor" / "tanuki_valuation" / "data"


def _fmt(v, pct=False, decimals=1):
    if v is None:
        return "N/A"
    if pct:
        return f"{v * 100:.{decimals}f}%"
    return f"{v:.{decimals}f}"


def audit_growth_models():
    ticker_dirs = sorted(
        d for d in DATA_DIR.iterdir()
        if d.is_dir() and (d / "latest.json").exists()
    )

    clamped      = []  # growth_model=decay AND cagr_max > 100%
    decay_all    = []  # growth_model=decay (全逓減銘柄)
    high_cagr    = []  # cagr_3yr > 50% or cagr_5yr > 50%

    for ticker_dir in ticker_dirs:
        ticker = ticker_dir.name
        if ticker == "tickers.json":
            continue
        try:
            with open(ticker_dir / "latest.json", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue

        gs          = d.get("growth_sanity") or {}
        rice        = d.get("rice") or {}
        comps       = d.get("components") or {}
        model       = gs.get("growth_model")
        p1g         = gs.get("phase1_growth")
        rec_g       = gs.get("recommended_g")
        cagr3       = gs.get("rev_cagr_3yr")
        cagr5       = gs.get("rev_cagr_5yr")
        ind_bench   = gs.get("industry_benchmark")
        upside      = d.get("upside_percent")
        score       = d.get("tanuki_score", "N/A")
        rev         = comps.get("latest_revenue") or 0
        rice_val    = (rice.get("base") or {}).get("rice")

        # CAGR_max（逓減モデルの入力値）
        cagr_max = max(
            cagr3 if cagr3 is not None else 0,
            cagr5 if cagr5 is not None else 0,
        )
        # start_g: cagr_max を 100% でクランプした値（growth_sanity の内部ロジックと同様）
        start_g = min(cagr_max, 1.0)

        row = {
            "ticker":     ticker,
            "model":      model or "N/A",
            "cagr3":      cagr3,
            "cagr5":      cagr5,
            "cagr_max":   cagr_max if (cagr3 or cagr5) else None,
            "start_g":    start_g if model == "decay" else None,
            "rec_g":      rec_g,
            "ind_bench":  ind_bench,
            "upside":     upside,
            "score":      score,
            "rev_b":      rev / 1e9 if rev else None,
            "rice":       rice_val,
        }

        if model == "decay":
            decay_all.append(row)
            # クランプ発動 = cagr_max > 100%
            if cagr_max > 1.0:
                clamped.append(row)

        if (cagr3 is not None and cagr3 > 0.5) or (cagr5 is not None and cagr5 > 0.5):
            high_cagr.append(row)

    # ────────────────────────────────────────────────────────────────
    print("=" * 90)
    print("GROWTH-3 クランプ影響スキャン結果")
    print("=" * 90)

    print(f"\n【逓減モデル適用銘柄】growth_model=decay: {len(decay_all)}件")
    print("-" * 90)
    print(f"  {'Ticker':6} {'CAGR3':>8} {'CAGR5':>8} {'start_g':>8} {'rec_g':>7} {'bench':>7} {'Upside':>8} {'Rev($B)':>8} {'Score'}")
    print("-" * 90)
    for r in decay_all:
        clamped_mark = " ⚠️ CLAMP" if (r["cagr_max"] or 0) > 1.0 else ""
        rev_str = f"{r['rev_b']:.2f}B" if r['rev_b'] else 'N/A'
        up_str2 = _fmt(r['upside'], decimals=1) + ('%' if r['upside'] is not None else '')
        print(
            f"  {r['ticker']:6} {_fmt(r['cagr3'], pct=True):>8} {_fmt(r['cagr5'], pct=True):>8}"
            f" {_fmt(r['start_g'], pct=True):>8} {_fmt(r['rec_g'], pct=True):>7}"
            f" {_fmt(r['ind_bench'], pct=True):>7}"
            f" {up_str2:>8} {rev_str:>8}  {r['score']}{clamped_mark}"
        )

    print(f"\n【クランプ発動銘柄】start_g=100% (CAGR_max>100%): {len(clamped)}件")
    print("-" * 90)
    if clamped:
        for r in clamped:
            rec_str = _fmt(r['rec_g'], pct=True)
            ind_str = _fmt(r['ind_bench'], pct=True)
            up_str  = f"{r['upside']:+.1f}%" if r['upside'] is not None else "N/A"
            rev_str = f"{r['rev_b']:.2f}B" if r['rev_b'] else 'N/A'
            print(
                f"  {r['ticker']:6}: CAGR_max={_fmt(r['cagr_max'], pct=True, decimals=1)}"
                f"  start_g=100%(クランプ) → rec_g={rec_str}=(100%+{ind_str})/2"
                f"  Upside={up_str}  Score={r['score']}  Rev={rev_str}"
            )
    else:
        print("  (なし)")

    print(f"\n【高成長銘柄】CAGR_3yr>50% or CAGR_5yr>50%: {len(high_cagr)}件")
    print("-" * 90)
    for r in high_cagr:
        up_str3 = f"{r['upside']:+.1f}%" if r['upside'] is not None else "N/A"
        print(
            f"  {r['ticker']:6}: CAGR3={_fmt(r['cagr3'], pct=True):>8}"
            f" CAGR5={_fmt(r['cagr5'], pct=True):>8}"
            f" model={r['model']:6}  rec_g={_fmt(r['rec_g'], pct=True):>7}"
            f"  Upside={up_str3:>8}  Score={r['score']}"
        )

    print("\n【チェック項目】")
    print("  • クランプ発動銘柄: CAGR_max>100% → start_g=100% → rec_g=(100%+bench)/2 で過大化の可能性")
    print("  • Upside が大きく負値（割高）なのに GROWTH_PREMIUM 判定の銘柄は IV 過大評価リスクあり")
    print("  • 小規模売上（<$100M）からの高CAGRは拡大誤差。売上規模フィルタの必要性を判断")
    print("  • 対処案: 1) クランプ上限を 80% or 70% に引き下げ")
    print("           2) 売上規模フィルタ（Rev < $Xm 時に start_g を割引）")
    print("           3) 上場年数フィルタ（上場 N 年未満は CAGR 信頼度係数で割引）")
    print("           4) 現状維持（TRIM/GROWTH_PREMIUM ラベルで運用）")
    print("=" * 90)


if __name__ == "__main__":
    audit_growth_models()
