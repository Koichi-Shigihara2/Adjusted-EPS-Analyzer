import numpy as np
from typing import Dict, Any

class KoichiValuationCalculator:
    def __init__(self):
        self.wacc = 0.085          # 割引率
        self.k = 0.10              # モメンタム係数
        self.high_growth_years = 3 # あなたのKPI監視期間

    def calculate_pt(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        fcf_avg = financials.get("fcf_5yr_avg", 0.0)
        diluted_shares = financials.get("diluted_shares", 0)
        roe_avg = financials.get("roe_10yr_avg", 0.0)
        current_price = financials.get("current_price", 0.0)
        fcf_list_raw = financials.get("fcf_list_raw", [])
        ticker = financials.get("eps_data", {}).get("ticker", "Unknown")

        if diluted_shares <= 0:
            return {"error": "diluted_shares missing"}

        # === 企業別高成長率の自動計算 ===
        high_growth_rate = 0.25  # デフォルト25%
        if len(fcf_list_raw) >= 3:
            # 過去FCFのCAGR（複合年間成長率）を計算
            recent_fcfs = [f for f in fcf_list_raw[-5:] if f > 0]  # 正の値のみ
            if len(recent_fcfs) >= 2:
                cagr = (recent_fcfs[-1] / recent_fcfs[0]) ** (1 / (len(recent_fcfs) - 1)) - 1
                high_growth_rate = max(0.15, min(0.50, cagr))  # 15%〜50%にキャップ

        print(f"   [{ticker}] 企業別高成長率（CAGRベース）: {high_growth_rate:.1%}")

        # FCFフロア
        original_fcf = fcf_avg
        if fcf_avg < 100_000:
            fcf_avg = max(100_000, abs(fcf_avg) * 0.1)
            print(f"   [{ticker}] FCF floor applied: {original_fcf:,.0f} → {fcf_avg:,.0f}")

        # === 2段階DCF ===
        high_growth_fcf = fcf_avg * (1 + high_growth_rate)
        pv_high = sum(high_growth_fcf * ((1 + high_growth_rate) ** t) / (1 + self.wacc) ** (t + 1) for t in range(self.high_growth_years))

        terminal_fcf = high_growth_fcf * ((1 + high_growth_rate) ** self.high_growth_years) * 1.03
        terminal_value = terminal_fcf / (self.wacc - 0.03)
        pv_terminal = terminal_value / (1 + self.wacc) ** self.high_growth_years

        v0 = pv_high + pv_terminal

        # α個別成長期待
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
            "calculation_date": "2026-04-01",
            "formula": "Koichi式 v5.1 企業別成長率自動計算",
            "components": {
                **financials,
                "fcf_avg_used": float(fcf_avg),
                "high_growth_rate_used": float(high_growth_rate),
                "high_growth_years": self.high_growth_years,
                "pv_high_growth": float(pv_high),
                "pv_terminal": float(pv_terminal)
            }
        }