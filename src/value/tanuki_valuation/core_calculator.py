import numpy as np
from typing import Dict, Any

class KoichiValuationCalculator:
    def __init__(self):
        self.wacc_default = 0.085   # 8.5%
        self.k = 0.10               # モメンタム係数

    def calculate_pt(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        fcf_avg = financials.get("fcf_5yr_avg", 0.0)
        diluted_shares = financials.get("diluted_shares", 0)
        roe_avg = financials.get("roe_10yr_avg", 0.0)
        current_price = financials.get("current_price", 0.0)
        fcf_method = financials.get("fcf_calc_method", "N/A")

        if diluted_shares <= 0:
            return {"error": "diluted_shares missing or zero"}

        # FCFが負または極端に小さい場合は最低値フロアを設ける（成長株対策）
        if fcf_avg <= 0:
            fcf_avg = 100_000  # 最低100kドルフロア（後で調整可）

        # V_固定的（10年DCF + 永続0成長）
        wacc = self.wacc_default
        v_fixed = sum(fcf_avg / (1 + wacc) ** t for t in range(1, 11))
        terminal = fcf_avg / wacc / (1 + wacc) ** 10
        v0 = v_fixed + terminal

        # α個別成長期待（簡易ROEベース）
        g_individual = max(0.0, roe_avg * 0.6)
        alpha = max(0.0, (g_individual / wacc) * 0.7)
        beta = 0.0

        m_total = 0.0

        intrinsic_value_pt = v0 * (1 + alpha + beta) + self.k * m_total * v0 * (alpha + beta)

        intrinsic_value_per_share = intrinsic_value_pt / diluted_shares if diluted_shares > 0 else 0.0

        approx_value = intrinsic_value_pt * (1 + self.k * m_total)

        return {
            "intrinsic_value_pt": float(intrinsic_value_pt),
            "intrinsic_value_per_share": float(intrinsic_value_per_share),
            "approx_value": float(approx_value),
            "v0": float(v0),
            "alpha": float(alpha),
            "beta": float(beta),
            "m_total": float(m_total),
            "implied_irr": float((intrinsic_value_per_share / current_price - 1) * 100) if current_price > 0 else 0.0,
            "calculation_date": "2026-03-30",
            "formula": "Koichi式 v5.1 exact (FCF floor applied)",
            "components": {
                **financials,
                "fcf_avg_used": float(fcf_avg),
                "fcf_method": fcf_method
            }
        }
