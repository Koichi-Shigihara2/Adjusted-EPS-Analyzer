"""
tests/test_iv_formula.py

IV per share 計算式の整合性を自動検証するテスト。

検証式:
    iv_pt = v0_rm × (1 + alpha) + rpo_pv + growth_option_pv
    IV_per_share = iv_pt / diluted_shares + net_cash_per_share
    → stored intrinsic_value_per_share との誤差 < $0.01

実行:
    python -m pytest tests/test_iv_formula.py -v
"""

import json
import os
import pytest

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR  = os.path.join(REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "data")

TICKERS = ["MSFT", "NVDA", "CELH", "PLTR", "TSLA"]
TOLERANCE_USD = 0.01


def _load(ticker: str):
    p = os.path.join(DATA_DIR, ticker, "latest.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("ticker", TICKERS)
def test_iv_formula_adds_up(ticker):
    """IV per share = (v0_rm × (1+α) + RPO_PV + Growth_Option_PV) / shares + net_cash_per_share"""
    d = _load(ticker)
    if d is None:
        pytest.skip(f"{ticker}: latest.json not found")

    dcf    = d.get("dcf_components", {})
    comps  = d.get("components", {})
    bs_adj = d.get("bs_adjustment", {})

    v0_rm         = dcf.get("v0_rm")
    alpha         = d.get("alpha")
    rpo_pv        = comps.get("rpo_pv") or 0.0
    go_pv         = comps.get("growth_option_pv") or 0.0
    diluted_shares = comps.get("diluted_shares")
    net_cash_ps   = (bs_adj.get("net_cash_per_share") or 0.0)
    iv_stored     = d.get("intrinsic_value_per_share")

    if v0_rm is None:
        pytest.skip(f"{ticker}: v0_rm not in dcf_components (old data — regenerate)")
    if alpha is None:
        pytest.skip(f"{ticker}: alpha missing")
    if not diluted_shares or diluted_shares <= 0:
        pytest.skip(f"{ticker}: diluted_shares missing or zero")
    if iv_stored is None:
        pytest.skip(f"{ticker}: intrinsic_value_per_share missing")

    iv_pt    = v0_rm * (1.0 + alpha) + rpo_pv + go_pv
    iv_recalc = iv_pt / diluted_shares + net_cash_ps

    diff = abs(iv_recalc - iv_stored)
    assert diff < TOLERANCE_USD, (
        f"{ticker}: IV formula mismatch.\n"
        f"  recalculated = ${iv_recalc:.4f}\n"
        f"  stored       = ${iv_stored:.4f}\n"
        f"  diff         = ${diff:.4f} (tolerance = ${TOLERANCE_USD})\n"
        f"  v0_rm={v0_rm/1e9:.3f}B  alpha={alpha:.4f}  rpo_pv={rpo_pv/1e9:.3f}B  "
        f"go_pv={go_pv/1e9:.3f}B  shares={diluted_shares/1e9:.4f}B  nc_ps={net_cash_ps:.4f}"
    )
