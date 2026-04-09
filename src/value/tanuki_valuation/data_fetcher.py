"""
TANUKI VALUATION - Data Fetcher v3.0
共通SECデータモジュール + yfinance を使用

データソース:
- SEC EDGAR (common/sec_data) → FCF, 株式数, ROE, 売上高
- yfinance → 現在株価
"""

import sys
import os

# パス設定（src/value/tanuki_valuation/ から common/ へ）
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
sys.path.insert(0, repo_root)

from typing import Dict, Any

# yfinance（現在株価取得用）
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("[WARNING] yfinance not installed. Current price will be 0.")

# 共通SECデータモジュール
try:
    from common.sec_data.reader import SECReader
    HAS_SEC_DATA = True
except ImportError:
    HAS_SEC_DATA = False
    print("[WARNING] common.sec_data not found.")


class TanukiDataFetcher:
    """財務データ取得クラス - SEC + yfinance"""

    def __init__(self):
        # SECデータリーダー
        if HAS_SEC_DATA:
            sec_data_dir = os.path.join(repo_root, "common", "sec_data", "data")
            self.sec_reader = SECReader(data_dir=sec_data_dir)
        else:
            self.sec_reader = None

    def get_financials(self, ticker: str) -> Dict[str, Any]:
        """
        財務データ取得
        
        Returns:
            dict: {
                "fcf_5yr_avg": float,
                "diluted_shares": int,
                "roe_10yr_avg": float,
                "current_price": float,
                "fcf_list_raw": list,
                "latest_revenue": float,
                "eps_data": {"ticker": str}
            }
        """
        ticker = ticker.upper()
        print(f"\n   [{ticker}] データ取得開始")
        
        result = {
            "fcf_5yr_avg": 0.0,
            "diluted_shares": 0,
            "roe_10yr_avg": 0.0,
            "current_price": 0.0,
            "fcf_list_raw": [],
            "latest_revenue": 0.0,
            "rpo": 0.0,  # 残存履行義務（SaaS企業向け）
            "eps_data": {"ticker": ticker}
        }

        # 1. SECデータから取得
        if self.sec_reader:
            result = self._fetch_from_sec(ticker, result)
        else:
            print(f"   [{ticker}] SEC データモジュールが利用不可")

        # 2. 現在株価（yfinance）
        result["current_price"] = self._fetch_current_price(ticker)

        # ログ出力
        print(f"   [{ticker}] 最終結果:")
        print(f"       FCF 5yr Avg: ${result['fcf_5yr_avg']:,.0f}")
        print(f"       Diluted Shares: {result['diluted_shares']:,.0f}")
        print(f"       ROE avg: {result['roe_10yr_avg']:.1%}")
        print(f"       Current Price: ${result['current_price']:.2f}")
        print(f"       Revenue: ${result['latest_revenue']:,.0f}")
        if result['rpo'] > 0:
            print(f"       RPO: ${result['rpo']:,.0f}")

        return result

    def _fetch_from_sec(self, ticker: str, result: dict) -> dict:
        """SECデータから財務情報を取得"""
        
        # FCF 5年平均
        fcf_avg = self.sec_reader.get_fcf_5yr_avg(ticker)
        if fcf_avg != 0:
            result["fcf_5yr_avg"] = fcf_avg
            print(f"   [{ticker}] SEC FCF 5yr avg: ${fcf_avg:,.0f}")
        
        # FCFリスト
        fcf_list = self.sec_reader.get_fcf_list(ticker, 5)
        if fcf_list:
            result["fcf_list_raw"] = fcf_list
            print(f"   [{ticker}] SEC FCF list: {len(fcf_list)}年分")
        
        # 希薄化後株式数
        shares = self.sec_reader.get_diluted_shares(ticker)
        if shares > 0:
            result["diluted_shares"] = shares
            print(f"   [{ticker}] SEC shares: {shares:,.0f}")
        
        # ROE平均
        roe = self.sec_reader.get_roe_avg(ticker, 10)
        if roe != 0:
            result["roe_10yr_avg"] = roe
            print(f"   [{ticker}] SEC ROE avg: {roe:.1%}")
        
        # 売上高
        revenue = self.sec_reader.get_latest_revenue(ticker)
        if revenue > 0:
            result["latest_revenue"] = revenue
            print(f"   [{ticker}] SEC revenue: ${revenue:,.0f}")
        
        # RPO（残存履行義務）
        rpo = self.sec_reader.get_rpo(ticker)
        if rpo > 0:
            result["rpo"] = rpo
            print(f"   [{ticker}] SEC RPO: ${rpo:,.0f}")
        
        return result

    def _fetch_current_price(self, ticker: str) -> float:
        """yfinanceから現在株価を取得"""
        if not HAS_YFINANCE:
            return 0.0
        
        try:
            stock = yf.Ticker(ticker)
            
            # currentPrice または regularMarketPrice
            info = stock.info
            price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
            
            if price > 0:
                print(f"   [{ticker}] yfinance price: ${price:.2f}")
                return float(price)
            
            # フォールバック: history から最新終値
            hist = stock.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                print(f"   [{ticker}] yfinance history price: ${price:.2f}")
                return price
                
        except Exception as e:
            print(f"   [{ticker}] yfinance error: {e}")
        
        return 0.0


if __name__ == "__main__":
    fetcher = TanukiDataFetcher()
    
    # テスト
    for ticker in ["TSLA", "PLTR", "SOFI"]:
        data = fetcher.get_financials(ticker)
        print(f"\n{ticker}: FCF=${data['fcf_5yr_avg']:,.0f}, Shares={data['diluted_shares']:,.0f}, Price=${data['current_price']:.2f}")
