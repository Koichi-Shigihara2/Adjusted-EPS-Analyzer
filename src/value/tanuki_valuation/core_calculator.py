"""
TANUKI VALUATION - Core Calculator v5.2
Koichi式株価評価モデル

P_t = (V_0 + RPO調整) × (1 + α)
V_0 = 2段階DCF（高成長期3年 + ターミナル）
α = min(1.0, max(0, (ROE_10yr × retention_rate / WACC) × 0.7))

パラメータ:
- WACC: 8.5%（成長期待を含まない固定値）
- terminal_growth: 3%
- retention_rate: 60%
- high_growth_range: 15%〜50%
- FCF floor: revenue × 8%（FCFがマイナスの場合）
- α_cap: 1.0（100%上限）
- min_fcf_years: 3（最低FCFデータ年数）
- RPO割引率: 15%（バックログの現在価値化）
"""

from typing import Dict, Any, List
from datetime import datetime


class KoichiValuationCalculator:
    """Koichi式 v5.2 バリュエーション計算エンジン"""

    def __init__(self):
        # 固定パラメータ
        self.wacc = 0.085           # 割引率（成長期待を含まない）
        self.high_growth_years = 3   # 高成長期間（年）
        self.retention_rate = 0.60   # 内部留保率
        self.terminal_growth = 0.03  # 永続成長率
        
        # v5.2 追加パラメータ
        self.alpha_cap = 1.0         # α上限（100%）
        self.min_fcf_years = 3       # 最低FCFデータ年数
        self.rpo_discount_rate = 0.15  # RPO割引率

    def calculate_pt(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """
        メイン計算関数
        
        Args:
            financials: {
                "fcf_5yr_avg": float,
                "diluted_shares": int,
                "roe_10yr_avg": float,
                "current_price": float,
                "fcf_list_raw": list,
                "latest_revenue": float,
                "eps_data": {"ticker": str},
                "rpo": float (optional) - 残存履行義務
            }
        
        Returns:
            完全なバリュエーション結果
        """
        # データ抽出
        fcf_avg = financials.get("fcf_5yr_avg", 0.0)
        diluted_shares = financials.get("diluted_shares", 0)
        roe_avg = financials.get("roe_10yr_avg", 0.0)
        latest_revenue = financials.get("latest_revenue", 0.0)
        fcf_list_raw = financials.get("fcf_list_raw", [])
        current_price = financials.get("current_price", 0.0)
        ticker = financials.get("eps_data", {}).get("ticker", "Unknown")
        rpo = financials.get("rpo", 0.0)  # 残存履行義務

        # ========================================
        # バリデーション
        # ========================================
        if diluted_shares <= 100_000:
            return {"error": "diluted_shares missing or invalid", "ticker": ticker}
        
        # データ不足ガード
        if len(fcf_list_raw) < self.min_fcf_years:
            print(f"   [{ticker}] ⚠️ FCFデータ不足 ({len(fcf_list_raw)}年 < {self.min_fcf_years}年)")
            return {
                "error": f"FCFデータ不足 ({len(fcf_list_raw)}年)",
                "ticker": ticker,
                "fcf_years_available": len(fcf_list_raw),
                "min_required": self.min_fcf_years
            }

        # ========================================
        # STEP 1: FCF 5年平均算出
        # ========================================
        fcf_calculation = {
            "input": fcf_list_raw,
            "sum": sum(fcf_list_raw) if fcf_list_raw else 0,
            "count": len(fcf_list_raw),
            "result": fcf_avg
        }

        # ========================================
        # STEP 2: 企業別高成長率（CAGR）算出
        # ========================================
        high_growth_rate = 0.25  # デフォルト
        cagr_calculation = {"method": "default", "result": high_growth_rate}

        if len(fcf_list_raw) >= 3:
            recent_fcfs = [f for f in fcf_list_raw[-5:] if f > 0]
            if len(recent_fcfs) >= 2:
                raw_cagr = (recent_fcfs[-1] / recent_fcfs[0]) ** (1 / (len(recent_fcfs) - 1)) - 1
                high_growth_rate = max(0.15, min(0.50, raw_cagr))
                cagr_calculation = {
                    "method": "cagr",
                    "start_value": recent_fcfs[0],
                    "end_value": recent_fcfs[-1],
                    "periods": len(recent_fcfs) - 1,
                    "raw_cagr": raw_cagr,
                    "clipped_result": high_growth_rate
                }

        print(f"   [{ticker}] 企業別高成長率（CAGR）: {high_growth_rate:.1%}")

        # ========================================
        # FCF現実的補正（マイナスFCF対応）
        # ========================================
        original_fcf = fcf_avg
        fcf_floor_applied = 0.0

        if fcf_avg <= 0 and latest_revenue > 0:
            fcf_floor = latest_revenue * 0.08
            fcf_avg = max(fcf_avg, fcf_floor)
            fcf_floor_applied = fcf_avg - original_fcf
            print(f"   [{ticker}] FCFが{original_fcf:,.0f}のため補正 → ${fcf_avg:,.0f} (売上高×8%)")

        # ========================================
        # STEP 3: 2段階DCF計算
        # ========================================
        current_fcf = fcf_avg
        pv_high = 0.0
        high_growth_detail = []

        for t in range(self.high_growth_years):
            current_fcf *= (1 + high_growth_rate)
            discount_factor = (1 + self.wacc) ** (t + 1)
            pv_year = current_fcf / discount_factor
            pv_high += pv_year
            high_growth_detail.append({
                "year": t + 1,
                "fcf": current_fcf,
                "discount_factor": discount_factor,
                "pv": pv_year
            })

        # ターミナル価値計算
        terminal_fcf = current_fcf * (1 + self.terminal_growth)
        terminal_value = terminal_fcf / (self.wacc - self.terminal_growth)
        pv_terminal = terminal_value / (1 + self.wacc) ** self.high_growth_years

        # V_0（本質的価値ベース）
        v0 = pv_high + pv_terminal

        # ========================================
        # STEP 4: RPO補正（SaaS企業向け）
        # ========================================
        rpo_adjustment = 0.0
        rpo_calculation = {"applied": False}
        
        if rpo > 0:
            # RPOを割引現在価値化（平均1.5年で実現と仮定）
            rpo_pv = rpo / (1 + self.rpo_discount_rate) ** 1.5
            rpo_adjustment = rpo_pv
            rpo_calculation = {
                "applied": True,
                "rpo_raw": rpo,
                "discount_rate": self.rpo_discount_rate,
                "assumed_realization_years": 1.5,
                "rpo_pv": rpo_pv
            }
            print(f"   [{ticker}] RPO補正: ${rpo:,.0f} → PV ${rpo_pv:,.0f}")

        # V_0 + RPO調整
        v0_adjusted = v0 + rpo_adjustment

        # ========================================
        # STEP 5: α（成長期待プレミアム）算出 ★キャップ追加
        # ========================================
        g_individual = max(0.0, roe_avg * self.retention_rate)
        alpha_raw = (g_individual / self.wacc) * 0.7
        alpha_uncapped = max(0.0, alpha_raw)
        alpha = min(self.alpha_cap, alpha_uncapped)  # ★キャップ適用

        alpha_calculation = {
            "roe_10yr_avg": roe_avg,
            "retention_rate": self.retention_rate,
            "g_individual": g_individual,
            "wacc": self.wacc,
            "alpha_raw": alpha_raw,
            "alpha_uncapped": alpha_uncapped,
            "alpha_cap": self.alpha_cap,
            "alpha_final": alpha,
            "was_capped": alpha_uncapped > self.alpha_cap
        }

        if alpha_uncapped > self.alpha_cap:
            print(f"   [{ticker}] ROE_10yr = {roe_avg:.1%} → α = {alpha_uncapped:.3f} → キャップ適用 → {alpha:.3f}")
        else:
            print(f"   [{ticker}] ROE_10yr = {roe_avg:.1%} → α = {alpha:.3f}")

        # ========================================
        # STEP 6: 本質的価値（P_t）算出
        # ========================================
        intrinsic_value_pt = v0_adjusted * (1 + alpha)
        intrinsic_value_per_share = intrinsic_value_pt / diluted_shares if diluted_shares > 0 else 0.0

        # ========================================
        # 1〜3年後価値予測
        # ========================================
        future_values = {}
        current_value = intrinsic_value_per_share

        for year in range(1, 4):
            if year <= self.high_growth_years:
                growth_rate = high_growth_rate
            else:
                growth_rate = self.terminal_growth
            
            future_value = current_value * (1 + growth_rate)
            future_values[f"{year}年後"] = round(future_value, 2)
            current_value = future_value

        print(f"   [{ticker}] 1〜3年後理論株価: {future_values}")

        # 乖離率計算
        upside_percent = ((intrinsic_value_per_share / current_price) - 1) * 100 if current_price > 0 else 0

        # ========================================
        # 結果返却
        # ========================================
        return {
            "intrinsic_value_pt": float(intrinsic_value_pt),
            "intrinsic_value_per_share": float(intrinsic_value_per_share),
            "v0": float(v0),
            "v0_adjusted": float(v0_adjusted),
            "alpha": float(alpha),
            "alpha_was_capped": alpha_uncapped > self.alpha_cap,
            "future_values": future_values,
            "upside_percent": round(upside_percent, 1),
            "calculation_date": datetime.now().strftime("%Y-%m-%d"),
            "formula": "Koichi式 v5.2（αキャップ＋RPO補正＋データガード）",
            
            # 計算コンポーネント
            "components": {
                **financials,
                "high_growth_rate_used": float(high_growth_rate),
                "pv_high": float(pv_high),
                "pv_terminal": float(pv_terminal),
                "roe_used": float(roe_avg),
                "fcf_floor_applied": float(fcf_floor_applied),
                "rpo_adjustment": float(rpo_adjustment),
                "rpo_pv": float(rpo_adjustment),  # RPO現在価値（フロントエンド表示用）
                "alpha_uncapped": float(alpha_uncapped),
            }
        }


if __name__ == "__main__":
    calculator = KoichiValuationCalculator()
    
    # テスト: 通常ケース
    test_data = {
        "fcf_5yr_avg": 4850000000,
        "diluted_shares": 3180000000,
        "roe_10yr_avg": 0.148,
        "current_price": 248.50,
        "fcf_list_raw": [2800000000, 3500000000, 4200000000, 5800000000, 7950000000],
        "latest_revenue": 96773000000,
        "eps_data": {"ticker": "TSLA"}
    }
    
    result = calculator.calculate_pt(test_data)
    print(f"\nTSLA: ${result.get('intrinsic_value_per_share', 0):.2f}")
    
    # テスト: 異常ROE（FIGケース）
    test_high_roe = {
        "fcf_5yr_avg": 1000000000,
        "diluted_shares": 187000000,
        "roe_10yr_avg": 2.579,  # 257.9%
        "current_price": 20.0,
        "fcf_list_raw": [800000000, 900000000, 1000000000],
        "latest_revenue": 500000000,
        "eps_data": {"ticker": "TEST_HIGH_ROE"}
    }
    
    result2 = calculator.calculate_pt(test_high_roe)
    print(f"\nTEST_HIGH_ROE: ${result2.get('intrinsic_value_per_share', 0):.2f} (α capped: {result2.get('alpha_was_capped')})")
    
    # テスト: データ不足
    test_insufficient = {
        "fcf_5yr_avg": 500000000,
        "diluted_shares": 100000000,
        "roe_10yr_avg": 0.15,
        "current_price": 50.0,
        "fcf_list_raw": [400000000, 500000000],  # 2年分のみ
        "latest_revenue": 2000000000,
        "eps_data": {"ticker": "TEST_INSUFFICIENT"}
    }
    
    result3 = calculator.calculate_pt(test_insufficient)
    print(f"\nTEST_INSUFFICIENT: {result3.get('error', 'OK')}")
