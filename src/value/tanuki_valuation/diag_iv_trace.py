"""
Phase 1 診断スクリプト: IV per share 計算経路の追跡

report.txt の表示値 と latest.json の実際の中間値を左右対照表で出力する。

実行: python src/value/tanuki_valuation/diag_iv_trace.py
"""
import json, os, sys

TICKERS = ["MSFT", "NVDA", "CELH", "PLTR", "TSLA"]
_script_dir = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
DATA_DIR = os.path.join(REPO, "docs", "value-monitor", "tanuki_valuation", "data")
REPORT_DIR = DATA_DIR   # report.txt は <DATA_DIR>/<TICKER>/report.txt


def load(ticker: str):
    p = os.path.join(DATA_DIR, ticker, "latest.json")
    if not os.path.exists(p):
        return None, []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    rp = os.path.join(REPORT_DIR, ticker, "report.txt")
    report_lines = []
    if os.path.exists(rp):
        with open(rp, encoding="utf-8") as f:
            report_lines = f.readlines()
    return data, report_lines


def grep_report(lines, keyword):
    """report.txt から keyword を含む行を返す（最初にヒットした行）"""
    for ln in lines:
        if keyword in ln:
            return ln.strip()
    return "(not found)"


def fmt_b(v):
    if v is None:
        return "N/A"
    return f"${v/1e9:.3f}B"


def fmt_ps(v):
    if v is None:
        return "N/A"
    return f"${v:.2f}"


def run():
    for ticker in TICKERS:
        data, report_lines = load(ticker)
        if data is None:
            print(f"[{ticker}] latest.json not found, skipping.\n")
            continue

        comps   = data.get("components", {})
        dcf_c   = data.get("dcf_components", {})
        bs_adj  = data.get("bs_adjustment", {})
        rpo_adj = data.get("rpo_adjustment", {})
        go_data = data.get("growth_options", {})

        # ── 実際に使われた中間値 ──
        v0_rm         = dcf_c.get("v0_rm")            # V₀ (Rm=10%)
        pv_fcf_main   = dcf_c.get("pv_high_growth")   # FCF_PV (CAPM WACC) ← 表示用
        pv_tv_main    = dcf_c.get("pv_terminal")       # TV_PV  (CAPM WACC) ← 表示用
        # 3段階の場合 pv_high_growth = pv_phase1 + pv_phase2 として格納済み
        pv_phase1     = dcf_c.get("pv_phase1")
        pv_phase2     = dcf_c.get("pv_phase2")
        dcf_type      = data.get("dcf_type", "two_stage")

        alpha         = data.get("alpha")
        rpo_pv        = comps.get("rpo_pv", 0) or 0
        growth_opt_pv = comps.get("growth_option_pv", 0) or 0
        net_cash      = bs_adj.get("net_cash")
        net_cash_ps   = bs_adj.get("net_cash_per_share", 0) or 0
        bs_applied    = bs_adj.get("applied", False)
        diluted_shares = comps.get("diluted_shares")
        shares_source = comps.get("_shares_source", "unknown")

        iv_ps_displayed = data.get("intrinsic_value_per_share")  # 表示値
        iv_pt_stored    = data.get("intrinsic_value_pt")          # 格納値(CAPM WACC使用)

        # ── 再現計算（v0_rm ベース）──
        if v0_rm is not None and alpha is not None:
            v0_x_alpha     = v0_rm * (1 + alpha)
            iv_pt_recalc   = v0_x_alpha + rpo_pv + growth_opt_pv
            eq_value       = iv_pt_recalc + (net_cash or 0)
            if diluted_shares and diluted_shares > 0:
                iv_recalc_ps = iv_pt_recalc / diluted_shares + net_cash_ps
            else:
                iv_recalc_ps = None
        else:
            v0_x_alpha = iv_pt_recalc = eq_value = iv_recalc_ps = None

        # ── report.txt 現在の表示値 ──
        r_fcf_pv    = grep_report(report_lines, "DCF_FCF_PV:")
        r_tv_pv     = grep_report(report_lines, "DCF_TV_PV:")
        r_rpo_pv    = grep_report(report_lines, "RPO_PV:")
        r_net_debt  = grep_report(report_lines, "Net_Debt:")
        r_iv        = grep_report(report_lines, "Intrinsic_Value_BASE:")
        r_dev       = grep_report(report_lines, "Deviation_BASE:")

        # ── 表示 ──
        SEP = "─" * 68
        print(SEP)
        print(f"  {ticker}  (DCF type: {dcf_type})")
        print(SEP)
        print(f"{'項目':<28} {'実際に使われた値':>18}  {'report.txt現在の表示':>30}")
        print("─" * 68)

        # 株数
        sh_str = f"{diluted_shares/1e6:.1f}M ({shares_source})" if diluted_shares else "N/A"
        print(f"{'Shares_Used':<28} {sh_str:>18}  {'(not explicitly shown)':>30}")

        # V₀ (Rm=10%)
        print(f"{'DCF_v0 (Rm=10%)':<28} {fmt_b(v0_rm):>18}  {'(not shown in report)':>30}")

        # FCF_PV (CAPM WACC - 表示用)
        if pv_phase1 is not None:
            pv_fcf_str = f"{fmt_b(pv_phase1)} + {fmt_b(pv_phase2)} (P1+P2)"
        else:
            pv_fcf_str = fmt_b(pv_fcf_main)
        print(f"{'DCF_FCF_PV (CAPM WACC)':<28} {pv_fcf_str:>18}  {r_fcf_pv[:40]:>30}")
        print(f"{'DCF_TV_PV  (CAPM WACC)':<28} {fmt_b(pv_tv_main):>18}  {r_tv_pv[:40]:>30}")

        # CAPM V₀ の合計
        if pv_fcf_main is not None and pv_tv_main is not None:
            v0_capm = pv_fcf_main + pv_tv_main
            print(f"{'  → sum (CAPM WACC)':<28} {fmt_b(v0_capm):>18}  {'(displayed sum)':>30}")

        # Rm V₀ と CAPM V₀ の差
        if v0_rm is not None and pv_fcf_main is not None:
            diff = v0_rm - (pv_fcf_main + pv_tv_main)
            print(f"{'  [v0_rm - CAPM sum]':<28} {fmt_b(diff):>18}  {'⚠ nonzero if WACC≠Rm':>30}")

        # Alpha
        alpha_str = f"{alpha:.4f}" if alpha is not None else "N/A"
        print(f"{'Alpha (HypeCore)':<28} {alpha_str:>18}  {'(shown in [HYPECORE])':>30}")

        # v0 × (1+alpha) — KEY MISSING
        print(f"{'DCF_v0 × (1+α)':<28} {fmt_b(v0_x_alpha):>18}  {'<-- NOT SHOWN in [3]':>30}")

        # RPO_PV
        rpo_str = fmt_b(rpo_pv)
        print(f"{'RPO_PV':<28} {rpo_str:>18}  {r_rpo_pv[:40]:>30}")

        # Growth Option PV
        go_str = fmt_b(growth_opt_pv)
        print(f"{'Growth_Option_PV':<28} {go_str:>18}  {'(not shown in [3])':>30}")

        # P_t = v0×(1+α) + RPO_PV + GO_PV
        print(f"{'P_t (= Enterprise Value)':<28} {fmt_b(iv_pt_recalc):>18}  {'(not shown in [3])':>30}")
        if iv_pt_stored is not None:
            print(f"{'  stored intrinsic_value_pt':<28} {fmt_b(iv_pt_stored):>18}  {'⚠ uses CAPM WACC':>30}")

        # Net_Cash equity bridge
        nc_str = fmt_b(net_cash) if bs_applied else f"{fmt_b(net_cash)} (not applied)"
        print(f"{'Net_Cash (equity bridge)':<28} {nc_str:>18}  {r_net_debt[:40]:>30}")

        # Equity Value = P_t + Net_Cash
        print(f"{'Equity_Value (= P_t + NC)':<28} {fmt_b(eq_value):>18}  {'(not shown in [3])':>30}")

        # Final IV per share
        print(f"{'IV per share (recalculated)':<28} {fmt_ps(iv_recalc_ps):>18}  {r_iv[:40]:>30}")
        print(f"{'IV per share (stored)':<28} {fmt_ps(iv_ps_displayed):>18}  {r_dev[:40]:>30}")

        # Consistency check
        if iv_recalc_ps is not None and iv_ps_displayed is not None:
            diff_ps = abs(iv_recalc_ps - iv_ps_displayed)
            status = "✅ OK (< $0.01)" if diff_ps < 0.01 else f"❌ DIFF ${diff_ps:.4f}"
            print(f"{'  [formula consistency]':<28} {status:>18}")

        print()


if __name__ == "__main__":
    run()
