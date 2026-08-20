"""
tests/test_iv_formula.py

IV per share 計算式の整合性を自動検証するテスト。

検証式（`validator.py::recalc_ivps_from_components()`をそのまま使う。
[[TEST-STALE-IV-1]]対応・2026-08-20: 以前はこのファイル内に独立した
式を実装しており、ALPHA-REDESIGN-1（P_t算出にalphaを乗算しなくなった
設計変更）に追従せず「alpha乗算あり」の旧式のまま残存していた
〈pytest既知failed2件・MSFT/NVDAの原因〉。同一概念の計算を2箇所以上
独立実装しないという[[QUALITY-GATES-EPIC-1]]ゲート3の原則に従い、
validator.py側の関数をimportして使う形に変更した）:
    IV_per_share = (v0_rm + rpo_pv + growth_option_pv) / diluted_shares
                   + net_cash_per_share
    → stored intrinsic_value_per_share との誤差 < $0.01

実行:
    python -m pytest tests/test_iv_formula.py -v
"""

import json
import os
import sys
import pytest

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR  = os.path.join(REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "data")

_TANUKI_DIR = os.path.join(REPO_ROOT, "src", "value", "tanuki_valuation")
if _TANUKI_DIR not in sys.path:
    sys.path.insert(0, _TANUKI_DIR)

from validator import recalc_ivps_from_components  # type: ignore[import]  # noqa: E402

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from common.sec_data.tickers import get_tanuki_tickers  # noqa: E402

# 2026-08-20: 5銘柄ハードコードから本番の一覧取得関数（事例5の原則）へ
# 拡大。全銘柄で新規失敗がないことを事前に実測確認済み
# （[[TEST-STALE-IV-1]]対応の一環）。
TICKERS = get_tanuki_tickers()
TOLERANCE_USD = 0.01


def _load(ticker: str):
    p = os.path.join(DATA_DIR, ticker, "latest.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("ticker", TICKERS)
def test_iv_formula_adds_up(ticker):
    """IV per share = (v0_rm + RPO_PV + Growth_Option_PV) / shares + net_cash_per_share"""
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

    iv_recalc = recalc_ivps_from_components(v0_rm, rpo_pv, go_pv, diluted_shares, net_cash_ps)

    diff = abs(iv_recalc - iv_stored)
    assert diff < TOLERANCE_USD, (
        f"{ticker}: IV formula mismatch.\n"
        f"  recalculated = ${iv_recalc:.4f}\n"
        f"  stored       = ${iv_stored:.4f}\n"
        f"  diff         = ${diff:.4f} (tolerance = ${TOLERANCE_USD})\n"
        f"  v0_rm={v0_rm/1e9:.3f}B  alpha={alpha:.4f}（参考値・式には未使用）  "
        f"rpo_pv={rpo_pv/1e9:.3f}B  "
        f"go_pv={go_pv/1e9:.3f}B  shares={diluted_shares/1e9:.4f}B  nc_ps={net_cash_ps:.4f}"
    )
