#!/usr/bin/env python3
"""
TANUKI TAIL DCF Bridge
Grok stage2シナリオ（売上成長率・営業利益率）→ 将来理論価格計算

入力:
  - docs/value-monitor/tanuki_valuation/data/{ticker}/latest.json
  - docs/portfolio/tail/data/reviews/{ticker}_*_review.json (is_latest=true)

出力:
  - docs/portfolio/scenario/{ticker}/bear.json
  - docs/portfolio/scenario/{ticker}/base.json
  - docs/portfolio/scenario/{ticker}/bull.json

使用方法:
  python src/tail/tail_dcf_bridge.py --ticker PLTR SOFI TSLA
  python src/tail/tail_dcf_bridge.py           # VALUATION_DIR配下の全ティッカー
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

# calculate_future_values を tanuki_valuation から直接 import
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))   # src/tail
_SRC_DIR   = os.path.dirname(_THIS_DIR)                    # src
_REPO_ROOT = os.path.dirname(_SRC_DIR)                     # repo root
_CALC_DIR  = os.path.join(_SRC_DIR, "value", "tanuki_valuation", "calculator")
if _CALC_DIR not in sys.path:
    sys.path.insert(0, _CALC_DIR)

from future_values import calculate_future_values          # noqa: E402

# ── パス定数 ──────────────────────────────────────────────────────
REVIEWS_DIR   = os.path.join(_REPO_ROOT, "docs", "portfolio", "tail", "data", "reviews")
VALUATION_DIR = os.path.join(_REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "data")
SCENARIO_DIR  = os.path.join(_REPO_ROOT, "docs", "portfolio", "scenario")
POSITIONS_DIR = os.path.join(_REPO_ROOT, "docs", "portfolio", "tail", "data", "positions")
KPI_DIR       = os.path.join(_REPO_ROOT, "docs", "portfolio", "tail", "data", "kpi")

JST = timezone(timedelta(hours=9))


def _load_latest_valuation(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(VALUATION_DIR, ticker, "latest.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_latest_review(ticker: str) -> Optional[Dict[str, Any]]:
    """is_latest=True のレビュー、なければファイル名で最新を返す"""
    if not os.path.exists(REVIEWS_DIR):
        return None
    files = sorted(
        [f for f in os.listdir(REVIEWS_DIR)
         if f.startswith(f"{ticker}_") and f.endswith("_review.json")],
        reverse=True,
    )
    if not files:
        return None
    for fname in files:
        with open(os.path.join(REVIEWS_DIR, fname), encoding="utf-8") as f:
            rv = json.load(f)
        if rv.get("is_latest"):
            return rv
    with open(os.path.join(REVIEWS_DIR, files[0]), encoding="utf-8") as f:
        return json.load(f)


def _load_thesis(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(POSITIONS_DIR, f"{ticker}_thesis.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_layer2_kpi(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(KPI_DIR, f"{ticker}_layer2.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _build_current_kpi_values(
    thesis: Optional[Dict[str, Any]],
    layer2: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """thesis.kpis の name → 最新 layer2 値のマッピングを返す"""
    if not thesis or not layer2:
        return {}
    kpis_layer2 = layer2.get("kpis", {})
    result: Dict[str, Any] = {}
    for kpi in (thesis.get("kpis") or []):
        name = kpi.get("name", "")
        l2_name = kpi.get("layer2_name", "")
        if not name:
            continue
        # layer2_name があればその最新値を取得
        lookup = l2_name or name
        entry = kpis_layer2.get(lookup)
        if entry:
            data = entry.get("data", [])
            if data:
                result[name] = data[0].get("value")  # data[0] = 最新四半期
    return result


def _fcf_margin(valuation: Dict[str, Any]) -> float:
    """直近実績FCFマージン率（比率）。マイナス or 未取得の場合は 0.05 で代替"""
    history = valuation.get("fcf_history", [])
    if not history:
        return 0.05
    margin = history[-1].get("fcf_margin", 0.0)
    if margin <= 0:
        return 0.05
    return margin / 100.0


def _weighted_growth(y1: float, y2: float, y3: float) -> float:
    """Y1×3 + Y2×2 + Y3×1 の加重平均（近い将来を重く見る）"""
    return (y1 * 3 + y2 * 2 + y3 * 1) / 6


def generate_scenario_files(ticker: str) -> bool:
    """
    ticker の将来理論価格シナリオファイルを生成する。

    Returns:
        True  = 全シナリオ生成成功
        False = スキップ（データ欠損など）
    """
    valuation = _load_latest_valuation(ticker)
    if not valuation:
        print(f"  [WARN] {ticker}: latest.json 未発見 → スキップ")
        return False

    review = _load_latest_review(ticker)
    if not review:
        print(f"  [WARN] {ticker}: レビュー未発見 → スキップ")
        return False

    thesis  = _load_thesis(ticker)
    layer2  = _load_layer2_kpi(ticker)
    current_kpi_values = _build_current_kpi_values(thesis, layer2)

    scenarios = review.get("stage2", {}).get("scenarios", {})
    if not scenarios:
        print(f"  [WARN] {ticker}: stage2.scenarios 未発見 → スキップ")
        return False

    quarter         = review.get("quarter", "unknown")
    current_iv      = float(valuation.get("intrinsic_value_per_share") or 0)
    current_price   = float((valuation.get("components") or {}).get("current_price") or 0)
    latest_revenue  = float((valuation.get("components") or {}).get("latest_revenue") or 0)
    fcf_adj         = _fcf_margin(valuation)
    now_jst         = datetime.now(JST)

    out_dir = os.path.join(SCENARIO_DIR, ticker)
    os.makedirs(out_dir, exist_ok=True)

    success = True
    for sc_name in ("bear", "base", "bull"):
        sc = scenarios.get(sc_name)
        if not sc:
            print(f"  [WARN] {ticker}: {sc_name} シナリオなし → スキップ")
            success = False
            continue

        y1       = float(sc.get("revenue_growth_y1", 0))
        y2       = float(sc.get("revenue_growth_y2", 0))
        y3       = float(sc.get("revenue_growth_y3", 0))
        terminal = float(sc.get("terminal_growth", 0.03))
        op_margin = float(sc.get("operating_margin_terminal", 0))
        wg       = _weighted_growth(y1, y2, y3)
        raw_kpi_forecasts = sc.get("kpi_forecasts") or {}
        kpi_forecasts: Dict[str, Any] = {}
        for kpi_name, fc in raw_kpi_forecasts.items():
            cur = current_kpi_values.get(kpi_name)
            entry: Dict[str, Any] = {}
            if cur is not None:
                entry["current"] = cur
            if isinstance(fc, dict):
                entry.update({k: v for k, v in fc.items() if k != "current"})
            else:
                entry["value"] = fc
            kpi_forecasts[kpi_name] = entry

        future_vals = calculate_future_values(
            current_value     = current_iv,
            high_growth_rate  = wg,
            high_growth_years = 3,      # Y1-Y3をPhase1として扱う
            terminal_growth   = terminal,
            projection_years  = 5,
        )

        output = {
            "ticker":  ticker,
            "quarter": quarter,
            "scenario": sc_name,
            "assumptions": {
                "Y1_growth":        round(y1, 4),
                "Y2_growth":        round(y2, 4),
                "Y3_growth":        round(y3, 4),
                "terminal_growth":  terminal,
                "operating_margin": op_margin,
                "weighted_growth":  round(wg, 4),
                "fcf_adjustment":   round(fcf_adj, 4),
                "base_revenue":     latest_revenue,
            },
            "base_intrinsic_value": round(current_iv, 2),
            "current_price":        round(current_price, 2),
            "future_values":        future_vals,
            "kpi_forecasts":        kpi_forecasts,
            "generated_at":         now_jst.isoformat(),
        }

        out_path = os.path.join(out_dir, f"{sc_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    if success:
        print(f"  ✓ {ticker}: シナリオファイル生成 → {out_dir}")
    return success


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TANUKI TAIL DCF Bridge — Grokシナリオ → 将来理論価格"
    )
    parser.add_argument("--ticker", nargs="+", help="対象ティッカー（複数可）")
    args = parser.parse_args()

    now_jst = datetime.now(JST)
    print(f"TANUKI TAIL DCF Bridge — {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 60)

    if args.ticker:
        tickers = args.ticker
    else:
        # VALUATION_DIR 配下のディレクトリをすべて対象とする
        if os.path.exists(VALUATION_DIR):
            tickers = sorted(
                d for d in os.listdir(VALUATION_DIR)
                if os.path.isdir(os.path.join(VALUATION_DIR, d))
            )
        else:
            print(f"[WARN] VALUATION_DIR 未発見: {VALUATION_DIR}")
            tickers = []

    ok, ng = [], []
    for ticker in tickers:
        result = generate_scenario_files(ticker)
        (ok if result else ng).append(ticker)

    print(f"\n{'━' * 60}")
    print(f"完了: 生成 {len(ok)} 件 / スキップ {len(ng)} 件")
    for t in ok:
        print(f"  OK: {t}")
    for t in ng:
        print(f"  --: {t}")


if __name__ == "__main__":
    main()
