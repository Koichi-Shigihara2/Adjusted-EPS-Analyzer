import yfinance as yf
from datetime import datetime, timezone

def fetch_valuation(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        return {
            "market_cap": info.get("marketCap"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "enterprise_value": info.get("enterpriseValue"),
            "total_debt": info.get("totalDebt"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": None
        }
    except Exception as e:
        return {
            "market_cap": None,
            "current_price": None,
            "enterprise_value": None,
            "total_debt": None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
