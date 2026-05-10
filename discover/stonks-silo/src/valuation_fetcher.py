# discover/stonks-silo/src/valuation_fetcher.py
"""
yfinance を使って各銘柄のバリュエーション指標をリアルタイム取得する。
計算（PSR・EV/Sales・ネットキャッシュ）は pipeline.py 側で行う。
"""

from datetime import datetime, timezone


def fetch_valuation(ticker: str) -> dict:
    """
    yfinance から時価総額・株価・EV・有利子負債を取得する。

    Returns
    -------
    {
        "market_cap": int | None,
        "current_price": float | None,
        "enterprise_value": int | None,
        "total_debt": int | None,
        "fetched_at": str,  # ISO 8601 UTC
        "error": str | None,
    }
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    empty = {
        "market_cap": None,
        "current_price": None,
        "enterprise_value": None,
        "total_debt": None,
        "fetched_at": fetched_at,
        "error": None,
    }

    try:
        import yfinance as yf
        info = yf.Ticker(ticker.upper()).info

        market_cap       = info.get("marketCap")
        current_price    = info.get("currentPrice") or info.get("regularMarketPrice")
        enterprise_value = info.get("enterpriseValue")
        total_debt       = info.get("totalDebt")

        # yfinance が 0 を返す場合は None 扱い（未取得と区別できないため）
        if total_debt == 0:
            total_debt = None

        return {
            "market_cap":       market_cap,
            "current_price":    current_price,
            "enterprise_value": enterprise_value,
            "total_debt":       total_debt,
            "fetched_at":       fetched_at,
            "error":            None,
        }

    except ImportError:
        empty["error"] = "yfinance not installed"
        return empty
    except Exception as e:
        empty["error"] = str(e)
        return empty
