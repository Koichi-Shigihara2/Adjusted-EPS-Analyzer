"""
TANUKI VALUATION - Core Calculator v5.3
Koichi式株価評価モデル

v5.3 変更点:
- 動的WACC（CAPM: Rf + β × (Rm - Rf)）
- 感度分析マトリクス（WACC ±1% × 高成長期間 3/5/7年）

P_t = (V_0 + RPO調整) × (1 + α)
V_0 = 2段階DCF（高成長期 + ターミナル）
α = min(1.0, max(0, (ROE_10yr × retention_rate / WACC) × 0.7))

パラメータ:
- WACC: CAPM計算（Rf=4.3%, Rm=10%, β=企業別）
- terminal_growth: 3%
- retention_rate: 60%
- high_growth_range: 15%〜50%
- FCF floor: revenue × 8%
- α_cap: 1.0
- min_fcf_years: 3
- RPO割引率: 15%
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

# セグメント別成長率（segment_config.pyからインポート試行）
try:
    from segment_config import get_segment_growth, calculate_scenario_growth, SEGMENT_OVERRIDES
    HAS_SEGMENT_CONFIG = True
except ImportError:
    HAS_SEGMENT_CONFIG = False
    SEGMENT_OVERRIDES = {}
    def get_segment_growth(ticker):
        return None
    def calculate_scenario_growth(ticker, scenario):
        return None


class KoichiValuationCalculator:
    """Koichi式 v5.3 バリュエーション計算エンジン"""

    def __init__(self):
        # CAPM パラメータ
        self.risk_free_rate = 0.043   # 10年国債利回り（Rf）
        self.market_return = 0.10     # 市場期待リターン（Rm）
        self.default_beta = 1.0       # デフォルトβ
        
        # 計算パラメータ
        self.high_growth_years = 5    # 高成長期間（年）- 感度分析の基準値
        self.retention_rate = 0.60    # 内部留保率
        self.terminal_growth = 0.03   # 永続成長率
        
        # v5.2 追加パラメータ
        self.alpha_cap = 1.0          # α上限（100%）
        self.min_fcf_years = 3        # 最低FCFデータ年数
        self.rpo_discount_rate = 0.15 # RPO割引率
        
        # 感度分析パラメータ
        self.sensitivity_wacc_delta = 0.01  # ±1%
        self.sensitivity_growth_years = [3, 5, 7]

    def _calculate_wacc(self, beta: float) -> float:
        """
        CAPM によるWACC計算
        WACC = Rf + β × (Rm - Rf)
        """
        market_risk_premium = self.market_return - self.risk_free_rate
        wacc = self.risk_free_rate + beta * market_risk_premium
        return wacc

    def _calculate_dcf(
        self, 
        fcf_avg: float, 
        high_growth_rate: float, 
        wacc: float,
        high_growth_years: int
    ) -> Dict[str, float]:
        """
        2段階DCF計算（内部ヘルパー）
        
        Returns:
            {"pv_high": float, "pv_terminal": float, "v0": float}
        """
        current_fcf = fcf_avg
        pv_high = 0.0
        
        for t in range(high_growth_years):
            current_fcf *= (1 + high_growth_rate)
            discount_factor = (1 + wacc) ** (t + 1)
            pv_high += current_fcf / discount_factor
        
        # ターミナル価値
        terminal_fcf = current_fcf * (1 + self.terminal_growth)
        terminal_value = terminal_fcf / (wacc - self.terminal_growth)
        pv_terminal = terminal_value / (1 + wacc) ** high_growth_years
        
        v0 = pv_high + pv_terminal
        
        return {
            "pv_high": pv_high,
            "pv_terminal": pv_terminal,
            "v0": v0
        }

    def _calculate_sensitivity_matrix(
        self,
        fcf_avg: float,
        high_growth_rate: float,
        base_wacc: float,
        rpo_adjustment: float,
        alpha: float,
        diluted_shares: int
    ) -> Dict[str, Any]:
        """
        感度分析マトリクス生成
        WACC: base-1%, base, base+1%
        高成長期間: 3年, 5年, 7年
        
        Returns:
            {
                "wacc_values": [0.08, 0.09, 0.10],
                "growth_years": [3, 5, 7],
                "matrix": [
                    [price_3y_low, price_5y_low, price_7y_low],
                    [price_3y_mid, price_5y_mid, price_7y_mid],
                    [price_3y_high, price_5y_high, price_7y_high]
                ],
                "base_wacc": 0.09,
                "base_years": 5
            }
        """
        wacc_low = base_wacc - self.sensitivity_wacc_delta
        wacc_mid = base_wacc
        wacc_high = base_wacc + self.sensitivity_wacc_delta
        
        wacc_values = [wacc_low, wacc_mid, wacc_high]
        growth_years = self.sensitivity_growth_years
        
        matrix = []
        
        for wacc in wacc_values:
            row = []
            for years in growth_years:
                dcf = self._calculate_dcf(fcf_avg, high_growth_rate, wacc, years)
                v0_adjusted = dcf["v0"] + rpo_adjustment
                intrinsic_value_pt = v0_adjusted * (1 + alpha)
                price_per_share = intrinsic_value_pt / diluted_shares if diluted_shares > 0 else 0
                row.append(round(price_per_share, 2))
            matrix.append(row)
        
        return {
            "wacc_values": [round(w, 3) for w in wacc_values],
            "growth_years": growth_years,
            "matrix": matrix,
            "base_wacc": round(base_wacc, 3),
            "base_years": self.high_growth_years
        }

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
                "rpo": float (optional),
                "beta": float (optional) - WACC計算用
            }
        """
        # データ抽出
        fcf_avg = financials.get("fcf_5yr_avg", 0.0)
        diluted_shares = financials.get("diluted_shares", 0)
        roe_avg = financials.get("roe_10yr_avg", 0.0)
        latest_revenue = financials.get("latest_revenue", 0.0)
        fcf_list_raw = financials.get("fcf_list_raw", [])
        current_price = financials.get("current_price", 0.0)
        ticker = financials.get("eps_data", {}).get("ticker", "Unknown")
        rpo = financials.get("rpo", 0.0)
        beta = financials.get("beta", self.default_beta)

        # ========================================
        # バリデーション
        # ========================================
        if diluted_shares <= 100_000:
            return {"error": "diluted_shares missing or invalid", "ticker": ticker}
        
        if len(fcf_list_raw) < self.min_fcf_years:
            print(f"   [{ticker}] ⚠️ FCFデータ不足 ({len(fcf_list_raw)}年 < {self.min_fcf_years}年)")
            return {
                "error": f"FCFデータ不足 ({len(fcf_list_raw)}年)",
                "ticker": ticker,
                "fcf_years_available": len(fcf_list_raw),
                "min_required": self.min_fcf_years
            }

        # ========================================
        # STEP 1: 動的WACC計算
        # ========================================
        wacc = self._calculate_wacc(beta)
        print(f"   [{ticker}] 動的WACC: {wacc:.1%} (β={beta:.2f}, Rf={self.risk_free_rate:.1%}, Rm={self.market_return:.0%})")

        # ========================================
        # STEP 2: 高成長率決定（セグメント優先）
        # ========================================
        high_growth_rate = 0.25  # デフォルト
        growth_source = "default"
        segment_info = None
        
        # セグメント加重成長率を優先
        segment_growth = get_segment_growth(ticker)
        if segment_growth is not None:
            high_growth_rate = segment_growth
            growth_source = "segment_weighted"
            print(f"   [{ticker}] セグメント加重成長率: {high_growth_rate:.1%}")
            
            # セグメント詳細取得
            if ticker in SEGMENT_OVERRIDES:
                segment_info = SEGMENT_OVERRIDES[ticker]
        else:
            # FCF CAGR計算
            if len(fcf_list_raw) >= 3:
                recent_fcfs = [f for f in fcf_list_raw[-5:] if f > 0]
                if len(recent_fcfs) >= 2:
                    raw_cagr = (recent_fcfs[-1] / recent_fcfs[0]) ** (1 / (len(recent_fcfs) - 1)) - 1
                    high_growth_rate = max(0.15, min(0.50, raw_cagr))
                    growth_source = "fcf_cagr"
            
            print(f"   [{ticker}] FCF CAGR成長率: {high_growth_rate:.1%}")

        # ========================================
        # STEP 3: FCF補正（マイナス対応）
        # ========================================
        original_fcf = fcf_avg
        fcf_floor_applied = 0.0

        if fcf_avg <= 0 and latest_revenue > 0:
            fcf_floor = latest_revenue * 0.08
            fcf_avg = max(fcf_avg, fcf_floor)
            fcf_floor_applied = fcf_avg - original_fcf
            print(f"   [{ticker}] FCFが{original_fcf:,.0f}のため補正 → ${fcf_avg:,.0f} (売上高×8%)")

        # ========================================
        # STEP 4: 2段階DCF計算
        # ========================================
        dcf_result = self._calculate_dcf(
            fcf_avg, high_growth_rate, wacc, self.high_growth_years
        )
        v0 = dcf_result["v0"]
        pv_high = dcf_result["pv_high"]
        pv_terminal = dcf_result["pv_terminal"]

        # ========================================
        # STEP 5: RPO補正
        # ========================================
        rpo_adjustment = 0.0
        rpo_calculation = {"applied": False}
        
        if rpo > 0:
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

        v0_adjusted = v0 + rpo_adjustment

        # ========================================
        # STEP 6: α（成長期待プレミアム）算出
        # ========================================
        g_individual = max(0.0, roe_avg * self.retention_rate)
        alpha_raw = (g_individual / wacc) * 0.7
        alpha_uncapped = max(0.0, alpha_raw)
        alpha = min(self.alpha_cap, alpha_uncapped)

        if alpha_uncapped > self.alpha_cap:
            print(f"   [{ticker}] ROE_10yr = {roe_avg:.1%} → α = {alpha_uncapped:.3f} → キャップ適用 → {alpha:.3f}")
        else:
            print(f"   [{ticker}] ROE_10yr = {roe_avg:.1%} → α = {alpha:.3f}")

        # ========================================
        # STEP 7: 本質的価値算出
        # ========================================
        intrinsic_value_pt = v0_adjusted * (1 + alpha)
        intrinsic_value_per_share = intrinsic_value_pt / diluted_shares

        # ========================================
        # STEP 8: 感度分析マトリクス
        # ========================================
        sensitivity = self._calculate_sensitivity_matrix(
            fcf_avg=fcf_avg,
            high_growth_rate=high_growth_rate,
            base_wacc=wacc,
            rpo_adjustment=rpo_adjustment,
            alpha=alpha,
            diluted_shares=diluted_shares
        )
        print(f"   [{ticker}] 感度分析マトリクス生成完了")

        # ========================================
        # STEP 9: シナリオ別理論株価（セグメント企業向け）
        # ========================================
        scenario_valuations = None
        if segment_info is not None:
            scenario_valuations = {}
            for scenario in ["bear", "base", "bull"]:
                scenario_rate = calculate_scenario_growth(ticker, scenario)
                if scenario_rate:
                    dcf_scenario = self._calculate_dcf(
                        fcf_avg, scenario_rate, wacc, self.high_growth_years
                    )
                    v0_scenario = dcf_scenario["v0"] + rpo_adjustment
                    pt_scenario = v0_scenario * (1 + alpha)
                    price_scenario = pt_scenario / diluted_shares
                    scenario_valuations[scenario] = {
                        "growth_rate": round(scenario_rate, 3),
                        "intrinsic_value_per_share": round(price_scenario, 2)
                    }

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

        # 乖離率
        upside_percent = ((intrinsic_value_per_share / current_price) - 1) * 100 if current_price > 0 else 0

        # ========================================
        # 結果返却
        # ========================================
        result = {
            "intrinsic_value_pt": float(intrinsic_value_pt),
            "intrinsic_value_per_share": float(intrinsic_value_per_share),
            "v0": float(v0),
            "v0_adjusted": float(v0_adjusted),
            "alpha": float(alpha),
            "alpha_was_capped": alpha_uncapped > self.alpha_cap,
            "future_values": future_values,
            "upside_percent": round(upside_percent, 1),
            "calculation_date": datetime.now().strftime("%Y-%m-%d"),
            "formula": "Koichi式 v5.3（動的WACC＋感度分析）",
            
            # WACC情報
            "wacc": {
                "value": round(wacc, 4),
                "beta": round(beta, 2),
                "risk_free_rate": self.risk_free_rate,
                "market_return": self.market_return,
                "method": "CAPM"
            },
            
            # 感度分析
            "sensitivity": sensitivity,
            
            # 成長率情報
            "growth_scenarios": {
                "primary": {
                    "rate": round(high_growth_rate, 3),
                    "source": growth_source
                },
                "segment": segment_info
            },
            
            # シナリオ別理論株価
            "scenario_valuations": scenario_valuations,
            
            # 計算コンポーネント
            "components": {
                **financials,
                "high_growth_rate_used": float(high_growth_rate),
                "high_growth_years": self.high_growth_years,
                "pv_high": float(pv_high),
                "pv_terminal": float(pv_terminal),
                "roe_used": float(roe_avg),
                "fcf_floor_applied": float(fcf_floor_applied),
                "rpo_adjustment": float(rpo_adjustment),
                "alpha_uncapped": float(alpha_uncapped),
            }
        }
        
        return result


if __name__ == "__main__":
    calculator = KoichiValuationCalculator()
    
    # テスト
    test_data = {
        "fcf_5yr_avg": 4850000000,
        "diluted_shares": 3180000000,
        "roe_10yr_avg": 0.148,
        "current_price": 248.50,
        "fcf_list_raw": [2800000000, 3500000000, 4200000000, 5800000000, 7950000000],
        "latest_revenue": 96773000000,
        "eps_data": {"ticker": "TSLA"},
        "beta": 2.31  # TSLAのβ
    }
    
    result = calculator.calculate_pt(test_data)
    print(f"\nTSLA: ${result.get('intrinsic_value_per_share', 0):.2f}")
    print(f"WACC: {result.get('wacc', {}).get('value', 0):.1%}")
    print(f"感度分析マトリクス:")
    sens = result.get("sensitivity", {})
    print(f"  WACC: {sens.get('wacc_values')}")
    print(f"  Years: {sens.get('growth_years')}")
    for i, row in enumerate(sens.get("matrix", [])):
        print(f"  {row}")
