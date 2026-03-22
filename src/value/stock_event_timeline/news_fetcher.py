from datetime import timedelta
from typing import List
import requests
import pandas as pd

from .config import NEWS_API_KEY


def fetch_news_around_date(ticker: str, event_date: pd.Timestamp, days: int = 3) -> List[dict]:
    if not NEWS_API_KEY:
        return []

    from_date = (event_date - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = (event_date + timedelta(days=days)).strftime("%Y-%m-%d")
    url = (
        "https://newsapi.org/v2/everything"
        f"?q={ticker}&from={from_date}&to={to_date}&sortBy=popularity&apiKey={NEWS_API_KEY}"
    )
    resp = requests.get(url, timeout=10)
    data = resp.json()
    return data.get("articles", [])[:5]


def build_news_context(articles: List[dict]) -> str:
    lines = []
    for a in articles:
        lines.append(f"{a.get('publishedAt','')}: {a.get('title','')}\n{a.get('description','')}")
    return "\n\n".join(lines)
