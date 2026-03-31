import numpy as np
from typing import Dict, Any

class KoichiValuationCalculator:
    def __init__(self):
        self.wacc = 0.085          # 割引率（成長期待を一切含まない固定値）
        self.k = 0.10              # モメンタム係数
        self.high_growth_years = 3 # あなたのスタイルに合わせた高成長期

    def calculate_pt(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        fcf_avg = financials.get("fcf_5yr_avg", 0.0)
        diluted_shares = financials.get("diluted_shares", 0)
        roe_avg = financials.get("roe_10yr_avg", 0.0)
        current_price = financials.get("current_price", 0.0)
        ticker = financials.get("eps_data", {}).get("ticker", "Unknown")

        if diluted_shares <= 0:
            return {"error": "diluted_shares missing"}

        # FCFが負の場合の安全フロア
        original_fcf = fcf_avg
        if fcf_avg < 100_000:
            fcf_avg = max(100_000, abs(fcf_avg) * 0.1)
            print(f"   [{ticker}] FCF floor applied: {original_fcf:,.0f} → {fcf_avg:,.0f}")

        # === 2段階DCF ===
        # 1. 高成長期（3年）
        high_growth_fcf = fcf_avg * 1.25  # 25%成長（あなたのハイパー成長株スタイルに合わせ調整可）
        pv_high = sum(high_growth_fcf * (1.25 ** t) / (1 + self.wacc) ** (t + 1) for t in range(self.high_growth_years))

        # 2. 永続成長期（3年後から）
        terminal_fcf = high_growth_fcf * (1.25 ** self.high_growth_years) * 1.03  # 永続3%成長
        terminal_value = terminal_fcf / (self.wacc - 0.03)
        pv_terminal = terminal_value / (1 + self.wacc) ** self.high_growth_years

        v0 = pv_high + pv_terminal

        # α個別成長期待（ROEベース）
        g_individual = max(0.0, roe_avg * 0.6)
        alpha = max(0.0, (g_individual / self.wacc) * 0.7)
        beta = 0.0
        m_total = 0.0

        intrinsic_value_pt = v0 * (1 + alpha + beta) + self.k * m_total * v0 * (alpha + beta)
        intrinsic_value_per_share = intrinsic_value_pt / diluted_shares if diluted_shares > 0 else 0.0

        return {
            "intrinsic_value_pt": float(intrinsic_value_pt),
            "intrinsic_value_per_share": float(intrinsic_value_per_share),
            "v0": float(v0),
            "alpha": float(alpha),
            "beta": float(beta),
            "m_total": float(m_total),
            "implied_irr": float((intrinsic_value_per_share / current_price - 1) * 100) if current_price > 0 else 0.0,
            "calculation_date": "2026-03-30",
            "formula": "Koichi式 v5.1 2段階DCF (3年高成長)",
            "components": {
                **financials,
                "fcf_avg_used": float(fcf_avg),
                "high_growth_fcf": float(high_growth_fcf)
            }
        }
