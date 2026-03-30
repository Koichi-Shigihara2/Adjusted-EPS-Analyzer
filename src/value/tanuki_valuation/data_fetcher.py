# src/value/tanuki_valuation/data_fetcher.py
import os
import numpy as np
from typing import Dict, Any
from edgartools import Company
import requests

class TanukiDataFetcher:
    """edgartools + Alpha Vantage で財務データ取得"""
    
    def __init__(self):
        self.alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    def get_financials(self, ticker: str) -> Dict[str, Any]:
        print(f"🔍 edgartoolsで {ticker} の財務データを取得中...")
        
        try:
            company = Company(ticker)
            financials = company.get_financials()
            
            # キャッシュフロー計算書からFCF取得
            cf = financials.cash_flow_statement(period="annual", limit=5)
            fcf_list = cf.get("Free Cash Flow", []).tolist() if hasattr(cf, 'get') else []
            
            # ROE
            income = financials.income_statement(period="annual", limit=10)
            roe_values = income.get("Return on Equity", []).tolist() if hasattr(income, 'get') else []
            
            current_price = self._get_current_price(ticker)
            
            return {
                "fcf_5yr_avg": self._normalize_fcf(fcf_list),
                "roe_10yr_avg": float(np.mean(roe_values)) if roe_values else 0.0,
                "current_price": current_price,
                "fcf_list_raw": fcf_list,
                "eps_data": {"ticker": ticker}
            }
        except Exception as e:
            print(f"⚠️ {ticker} edgartools取得失敗: {e} → フォールバック")
            return {
                "fcf_5yr_avg": 0.0,
                "roe_10yr_avg": 0.0,
                "current_price": self._get_current_price(ticker),
                "fcf_list_raw": [],
                "eps_data": {"ticker": ticker}
            }
    
    def _normalize_fcf(self, fcf_list: list) -> float:
        if not fcf_list:
            return 0.0
        mean = np.mean(fcf_list)
        std = np.std(fcf_list) if len(fcf_list) > 1 else 0
        clipped = np.clip(fcf_list, mean - 2*std, mean + 2*std)
        return float(np.mean(clipped))
    
    def _get_current_price(self, ticker: str) -> float:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={self.alpha_key}"
        try:
            data = requests.get(url, timeout=10).json()
            price = data.get("Global Quote", {}).get("05. price", 0)
            return float(price) if price else 0.0
        except:
            return 0.0
