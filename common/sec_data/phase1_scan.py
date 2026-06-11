#!/usr/bin/env python3
"""Phase 1 全銘柄スキャン: バグ・不整合・欠損の洗い出し"""
import json, os, re
from datetime import date

DATA  = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../docs/value-monitor/tanuki_valuation/data"))
TODAY = date(2026, 6, 11)

tickers = sorted([
    d for d in os.listdir(DATA)
    if os.path.isdir(os.path.join(DATA, d))
    and os.path.exists(os.path.join(DATA, d, "report.txt"))
])

issues = {k: [] for k in [
    "A1_NetDebt", "A2_Deviation", "A3_CAGR", "A4_ScenarioIV",
    "A5_SWG", "A6_ScenarioGrowth",
    "B1_FCFStale", "B2_EarningsExpired",
    "C1_MatrixQuadrant", "C2_Matrix2ROEDef",
]}

def parse_b(s):
    """'$1.23B' or '$-0.45B' -> float(B) or None"""
    if s is None:
        return None
    s = s.strip().lstrip("$")
    try:
        return float(s.rstrip("B").replace(",", ""))
    except ValueError:
        return None

for t in tickers:
    txt  = open(os.path.join(DATA, t, "report.txt"), encoding="utf-8").read()
    lines = txt.splitlines()
    lj   = json.load(open(os.path.join(DATA, t, "latest.json"), encoding="utf-8"))

    comp = lj.get("components", {}) or {}
    segs = lj.get("segments", []) or []
    fcfh = lj.get("fcf_history", []) or []

    # generated date
    gen_year = 2026
    for l in lines:
        m = re.search(r"^Generated:\s+(\d{4})", l)
        if m:
            gen_year = int(m.group(1))
            break

    # ──────────────── A-1: Net_Debt consistency ────────────────
    nd_b = td_b = ca_b = st_b = None
    for l in lines:
        m = re.match(r"^\s{2}Net_Debt:\s+\$([+-]?\d+\.?\d*)B", l)
        if m:
            nd_b = float(m.group(1))
        m = re.match(
            r"^\s{2}Total_Debt:\s+\$(\d+\.?\d*)B\s+Cash:\s+\$(\d+\.?\d*)B"
            r"(?:\s+ST_Invest:\s+\$(\d+\.?\d*)B)?",
            l
        )
        if m:
            td_b = float(m.group(1))
            ca_b = float(m.group(2))
            st_b = float(m.group(3)) if m.group(3) else 0.0

    if nd_b is not None and td_b is not None:
        computed = td_b - ca_b - (st_b or 0.0)
        diff = abs(nd_b - computed)
        if diff > 0.02:
            issues["A1_NetDebt"].append(
                f"{t}: report={nd_b:+.2f}B computed={computed:+.2f}B diff={diff:.3f}B"
            )

    # ──────────────── A-2: Deviation_BASE consistency ────────────
    price_rep = iv_rep = dev_rep = None
    for l in lines:
        m = re.match(r"^Current_Price:\s+\$([0-9,.]+)", l)
        if m:
            price_rep = float(m.group(1).replace(",", ""))
        m = re.match(r"^Intrinsic_Value_BASE:\s+\$([0-9,.]+)", l)
        if m:
            iv_rep = float(m.group(1).replace(",", ""))
        m = re.match(r"^Deviation_BASE:\s+([+-]?\d+\.?\d*)%", l)
        if m:
            dev_rep = float(m.group(1))

    if price_rep and iv_rep and dev_rep is not None and price_rep > 0:
        computed_dev = (iv_rep - price_rep) / price_rep * 100
        diff = abs(dev_rep - computed_dev)
        if diff > 0.2:
            issues["A2_Deviation"].append(
                f"{t}: report={dev_rep:+.1f}% computed={computed_dev:+.1f}% diff={diff:.2f}pt"
            )

    # ──────────────── A-3: FCF_CAGR consistency ─────────────────
    # latest.json の実値(unrounded)から計算してreportと照合する
    cagr_n_rep = cagr_pct_rep = None
    for l in lines:
        m = re.match(r"^\s+FCF_CAGR_(\d+)yr:\s+([+-]?\d+\.?\d*)%", l)
        if m:
            cagr_n_rep = int(m.group(1))
            cagr_pct_rep = float(m.group(2))
            break

    valid_fcf_j = [(e["year"], e["fcf"]) for e in fcfh if e.get("fcf") is not None]
    if cagr_n_rep and cagr_pct_rep is not None and len(valid_fcf_j) >= 4:
        old_yr, old_v = valid_fcf_j[-4]
        new_yr, new_v = valid_fcf_j[-1]
        span = new_yr - old_yr
        if span != cagr_n_rep:
            issues["A3_CAGR"].append(f"{t}: span mismatch report={cagr_n_rep}yr actual={span}yr")
        elif old_v > 0 and new_v > 0 and span > 0:
            computed_cagr = ((new_v / old_v) ** (1 / span) - 1) * 100
            diff = abs(cagr_pct_rep - computed_cagr)
            if diff > 0.2:  # 0.2pt 以上の差はバグ（丸め誤差は 0.05pt 以内）
                issues["A3_CAGR"].append(
                    f"{t}: report={cagr_pct_rep:.1f}% computed={computed_cagr:.1f}% diff={diff:.2f}pt"
                )

    # ──────────────── A-4: Scenario IV monotonicity ──────────────
    # カンマ含む数値（$1,234.56）に対応した regex
    sc_ivs = []
    sc_gs  = []
    for l in lines:
        m = re.match(r"^(BEAR|BASE|BULL): Growth=([\d.]+)%, IV=\$([\d,]+\.?\d*)", l)
        if m and len(sc_ivs) < 3:
            sc_gs.append(float(m.group(2)))
            sc_ivs.append(float(m.group(3).replace(",", "")))

    if len(sc_ivs) == 3:
        bear_iv, base_iv, bull_iv = sc_ivs
        if not (bear_iv <= base_iv + 0.01 and base_iv <= bull_iv + 0.01):
            issues["A4_ScenarioIV"].append(
                f"{t}: BEAR={bear_iv} BASE={base_iv} BULL={bull_iv} (non-monotone)"
            )

    # ──────────────── A-5: Segment_Weighted_Growth ───────────────
    swg_rep = None
    for l in lines:
        m = re.match(r"^\s+Segment_Weighted_Growth:\s+([+-]?\d+\.?\d*)%", l)
        if m:
            swg_rep = float(m.group(1))
            break

    if swg_rep is not None and segs:
        total_w = sum(s.get("weight", 0) for s in segs)
        if total_w > 0:
            computed_swg = sum(s.get("weight", 0) * s.get("growth", 0) for s in segs) / total_w * 100
            diff = abs(swg_rep - computed_swg)
            if diff > 0.15:
                issues["A5_SWG"].append(
                    f"{t}: report={swg_rep:.1f}% computed={computed_swg:.1f}% diff={diff:.3f}pt"
                )

    # ──────────────── A-6: Scenario growth monotonicity ──────────
    if len(sc_gs) == 3:
        bear_g, base_g, bull_g = sc_gs
        if not (bear_g <= base_g + 0.01 and base_g <= bull_g + 0.01):
            issues["A6_ScenarioGrowth"].append(
                f"{t}: BEAR_g={bear_g} BASE_g={base_g} BULL_g={bull_g}"
            )

    # ──────────────── B-1: FCF_History staleness ─────────────────
    if fcfh:
        max_yr = max(e.get("year", 0) for e in fcfh)
        if gen_year - max_yr >= 2:
            issues["B1_FCFStale"].append(f"{t}: max_year={max_yr} gen_year={gen_year} lag={gen_year-max_yr}yr")

    # ──────────────── B-2: Next_Earnings_Date expired ────────────
    ned = lj.get("next_earnings_date") or ""
    if ned and ned not in ("N/A", ""):
        try:
            ned_d = date.fromisoformat(ned[:10])
            if ned_d < TODAY:
                issues["B2_EarningsExpired"].append(f"{t}: {ned}")
        except Exception:
            pass

    # ──────────────── C-1: Matrix quadrant consistency ───────────
    matrix_type = quadrant_rep = key_metric_y = matrix_dev = None
    for l in lines:
        if matrix_type is None:
            m = re.match(r"^Matrix:\s+(.+)", l)
            if m: matrix_type = m.group(1)
        if quadrant_rep is None:
            m = re.match(r"^Quadrant:\s+(.+)", l)
            if m: quadrant_rep = m.group(1).strip()
        if key_metric_y is None:
            m = re.match(r"^Key_Metric_Y:\s+(.+)", l)
            if m: key_metric_y = m.group(1).strip()
        if matrix_dev is None:
            # 非インデントの Deviation_Rate (MATRIX POSITION セクション)
            m = re.match(r"^Deviation_Rate:\s+([+-]?\d+\.?\d*)%", l)
            if m: matrix_dev = float(m.group(1))

    if matrix_type and quadrant_rep and key_metric_y and matrix_dev is not None:
        qx = matrix_dev > 0
        qy = None
        metric_desc = ""

        if "①" in matrix_type:
            m = re.search(r"RICE\s*=\s*([+-]?\d+\.?\d*)", key_metric_y)
            if m:
                v = float(m.group(1))
                qy = v >= 1.0
                metric_desc = f"RICE={v:.3f}"
        elif "②" in matrix_type:
            m = re.search(r"=\s*([+-]?\d+\.?\d*)%", key_metric_y)
            if m:
                v = float(m.group(1))
                qy = v >= 15.0
                metric_desc = f"ROE={v:.1f}%"
        elif "③" in matrix_type:
            m = re.search(r"=\s*([+-]?\d+\.?\d*)%", key_metric_y)
            if m:
                v = float(m.group(1))
                qy = v > 0
                metric_desc = f"RevGrowth={v:.1f}%"
        elif "④" in matrix_type:
            m = re.search(r"FCF_Margin\s*=\s*([+-]?\d+\.?\d*)%", key_metric_y)
            if m:
                v = float(m.group(1))
                qy = v >= 15.0
                metric_desc = f"FCFMargin={v:.1f}%"

        if qy is not None:
            exp_q = ("右上" if qy else "右下") if qx else ("左上" if qy else "左下")
            if exp_q != quadrant_rep:
                issues["C1_MatrixQuadrant"].append(
                    f"{t}: [{matrix_type.strip()}] report={quadrant_rep} expected={exp_q}"
                    f" ({metric_desc} dev={matrix_dev:+.1f}%)"
                )

    # ──────────────── C-2: Matrix② ROE定義文年数 ────────────────
    if matrix_type and "②" in matrix_type:
        roe_years = comp.get("roe_years_used") or 10
        for l in lines:
            if "ROE_10yr_avg" in l and "Matrix②" in l:
                if roe_years != 10:
                    issues["C2_Matrix2ROEDef"].append(
                        f"{t}: roe_years_used={roe_years} but definition says ROE_10yr_avg"
                    )
                break


# ── 結果表示 ──────────────────────────────────────────────────
total_ng = 0
total_warn = 0

labels = {
    "A1_NetDebt":        ("NG",   "A-1: Net_Debt計算不整合"),
    "A2_Deviation":      ("NG",   "A-2: Deviation計算不整合"),
    "A3_CAGR":           ("NG",   "A-3: FCF_CAGR計算不整合"),
    "A4_ScenarioIV":     ("WARN", "A-4: シナリオIV単調性違反"),
    "A5_SWG":            ("NG",   "A-5: Segment_Weighted_Growth不整合"),
    "A6_ScenarioGrowth": ("NG",   "A-6: シナリオ成長率単調性違反"),
    "B1_FCFStale":       ("WARN", "B-1: FCF_History陳腐化(lag>=2yr)"),
    "B2_EarningsExpired":("WARN", "B-2: Next_Earnings_Date過去日付"),
    "C1_MatrixQuadrant": ("NG",   "C-1: Matrix象限不整合"),
    "C2_Matrix2ROEDef":  ("WARN", "C-2: Matrix②ROE定義文年数固定"),
}

print(f"=== Phase 1 全銘柄スキャン ({len(tickers)} 銘柄) ===\n")
for key, lst in issues.items():
    sev, desc = labels[key]
    if sev == "NG":
        total_ng += len(lst)
    else:
        total_warn += len(lst)
    if lst:
        icon = "❌" if sev == "NG" else "⚠️"
        print(f"{icon} [{sev}] {desc} ({len(lst)}件)")
        for item in lst:
            print(f"   {item}")
        print()

print("─" * 60)
print(f"合計: NG={total_ng} / WARN={total_warn}  (既存チェック除く)")
