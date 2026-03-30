import os
import numpy as np
from typing import Dict, Any
from ..adjusted_eps_analyzer.extract_key_facts import extract_quarterly_facts

class TanukiDataFetcher:
    def __init__(self):
        self.alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    def get_financials(self, ticker: str) -> Dict[str, Any]:
        print(f"   [DEBUG {ticker}] extract_quarterly_facts 開始")
        quarterly_data = extract_quarterly_facts(ticker, years=5)
        
        if not quarterly_data:
            print(f"   [DEBUG {ticker}] quarterly_data が空です")
            return {"error": "No quarterly data"}

        print(f"   [DEBUG {ticker}] quarterly_data 取得件数: {len(quarterly_data)}")

        fcf_list = []
        method = "未計算"
        for q in quarterly_data:
            ocf = q.get('us-gaap:NetCashProvidedByUsedInOperatingActivities', {}).get('value', 0)
            capex = q.get('us-gaap:PaymentsForPropertyPlantAndEquipment', {}).get('value', 0)
            if ocf != 0:
                fcf = ocf - abs(capex)
                method = "OCF - CapEx（最正確）"
            else:
                net = q.get('net_income', {}).get('value', 0)
                sbc = q.get('us-gaap:ShareBasedCompensation', {}).get('value', 0) or 0
                amort = q.get('us-gaap:AmortizationOfIntangibleAssets', {}).get('value', 0) or 0
                fcf = net + sbc + amort - abs(capex)
                method = "簡易計算 (フォールバック)"
            fcf_list.append(fcf)

        fcf_5yr_avg = self._normalize_fcf(fcf_list[-5:]) if fcf_list else 0.0

        # diluted_shares の取得を強化
        diluted_shares = 0
        if quarterly_data:
            ds = quarterly_data[0].get('diluted_shares', {})
            if isinstance(ds, dict):
                diluted_shares = ds.get('value', 0)
            else:
                diluted_shares = ds

        print(f"   [DEBUG {ticker}] diluted_shares = {diluted_shares:,}")

        if diluted_shares <= 0:
            print(f"   [DEBUG {ticker}] diluted_shares が0です！ スキップの可能性あり")

        return {
            "fcf_5yr_avg": fcf_5yr_avg,
            "diluted_shares": diluted_shares,
            "roe_10yr_avg": 0.0,
            "current_price": 0.0,
            "fcf_list_raw": fcf_list,
            "eps_data": {"ticker": ticker, "quarters": quarterly_data},
            "fcf_calc_method": method
        }

    def _normalize_fcf(self, fcf_list: list) -> float:
        if not fcf_list:
            return 0.0
        mean = np.mean(fcf_list)
        std = np.std(fcf_list) if len(fcf_list) > 1 else 0
        clipped = np.clip(fcf_list, mean - 2 * std, mean + 2 * std)
        return float(np.mean(clipped))
