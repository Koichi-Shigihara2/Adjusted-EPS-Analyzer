# src/value/tanuki_valuation/data_fetcher.py
import os
import json
from typing import Dict, Any
import requests
from datetime import datetime

class TanukiDataFetcher:
    """データ取得層（FMP/FRED/Alpha Vantage + EPSアナライザー緩やか連携）"""
    
    def __init__(self):
        self.fmp_key = os.getenv("FMP_API_KEY")
        self.fred_key = os.getenv("FRED_API_KEY")
        self.alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    def get_financials(self, ticker: str) -> Dict[str, Any]:
        """FMPから財務データ取得（FCF、ROE、CapExなど）"""
        base = f"https://financialmodelingprep.com/api/v3"
        
        # キャッシュフロー（過去10年）
        cf_url = f"{base}/cash-flow-statement/{ticker}?period=annual&limit=10&apikey={self.fmp_key}"
        cf_data = requests.get(cf_url).json()
        
        fcf_list = [item["freeCashFlow"] for item in cf_data if "freeCashFlow" in item]
        
        # キー指標（ROEなど）
        metrics_url = f"{base}/key-metrics/{ticker}?limit=10&apikey={self.fmp_key}"
        metrics = requests.get(metrics_url).json()
        
        # EPSアナライザー連携（緩やか連携レベル2）
        eps_path = f"docs/value-monitor/adjusted_eps_analyzer/data/{ticker}/annual.json"
        eps_data = {}
        if os.path.exists(eps_path):
            with open(eps_path, "r", encoding="utf-8") as f:
                eps_data = json.load(f)
        
        return {
            "fcf_5yr_avg": self._normalize_fcf(fcf_list[-5:]),
            "roe_10yr_avg": np.mean([m.get("roe", 0) for m in metrics]),
            "current_price": self._get_current_price(ticker),
            "fcf_list_raw": fcf_list,
            "eps_data": eps_data  # 再利用
        }
    
    def _normalize_fcf(self, fcf_list: list) -> float:
        """ノーマライズ（core_calculatorと共通ロジック）"""
        import numpy as np
        return float(np.mean(np.clip(fcf_list, np.mean(fcf_list)-2*np.std(fcf_list), np.mean(fcf_list)+2*np.std(fcf_list)))) if fcf_list else 0.0
    
    def _get_current_price(self, ticker: str) -> float:
        """Alpha Vantageで最新株価"""
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={self.alpha_key}"
        data = requests.get(url).json()
        return float(data.get("Global Quote", {}).get("05. price", 0))
    
    def get_fred_risk_free(self) -> float:
        """FREDから10年国債利回り（WACC用）"""
        # 簡易実装（実際はfredライブラリ推奨）
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={self.fred_key}&file_type=json&limit=1"
        data = requests.get(url).json()
        return float(data["observations"][0]["value"]) / 100 if data["observations"] else 0.08
