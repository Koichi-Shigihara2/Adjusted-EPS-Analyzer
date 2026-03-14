"""
external_data.py - 外部 API からの補完データ取得
Alpha Vantage: 株価
FRED: 米10年債利回り
FMP: 決算プレスリリース
"""
import os
import requests
from typing import Optional


def get_current_price(ticker: str) -> float:
    """Alpha Vantage から最新株価を取得"""
    key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not key:
        return 0.0
    try:
        url  = (f"https://www.alphavantage.co/query"
                f"?function=GLOBAL_QUOTE&symbol={ticker}&apikey={key}")
        resp = requests.get(url, timeout=10).json()
        price_str = resp.get("Global Quote", {}).get("05. price", "0")
        return float(price_str)
    except Exception as e:
        print(f"[WARN] get_current_price({ticker}): {e}")
        return 0.0


def get_market_context(ticker: str) -> dict:
    """株価 + 米10年債利回りを返す"""
    av_key   = os.environ.get("ALPHA_VANTAGE_API_KEY")
    fred_key = os.environ.get("FRED_API_KEY")

    price    = 0.0
    yield_10y = 0.0

    # 株価 (Alpha Vantage)
    if av_key:
        try:
            url  = (f"https://www.alphavantage.co/query"
                    f"?function=GLOBAL_QUOTE&symbol={ticker}&apikey={av_key}")
            resp = requests.get(url, timeout=10).json()
            price = float(resp.get("Global Quote", {}).get("05. price", 0))
        except Exception as e:
            print(f"[WARN] Alpha Vantage: {e}")

    # 米10年債利回り (FRED)
    if fred_key:
        try:
            url  = (f"https://api.stlouisfed.org/fred/series/observations"
                    f"?series_id=DGS10&api_key={fred_key}"
                    f"&file_type=json&sort_order=desc&limit=1")
            resp = requests.get(url, timeout=10).json()
            obs  = resp.get("observations", [{}])
            yield_10y = float(obs[0].get("value", 0))
        except Exception as e:
            print(f"[WARN] FRED: {e}")

    return {"price": price, "yield_10y": yield_10y}


def get_press_release(ticker: str) -> Optional[dict]:
    """FMP から最新の決算プレスリリースを取得"""
    key = os.environ.get("FMP_API_KEY")
    if not key:
        return None
    try:
        url  = (f"https://financialmodelingprep.com/api/v3"
                f"/press-releases/{ticker}?limit=1&apikey={key}")
        resp = requests.get(url, timeout=10).json()
        return resp[0] if resp else None
    except Exception as e:
        print(f"[WARN] get_press_release({ticker}): {e}")
        return None
