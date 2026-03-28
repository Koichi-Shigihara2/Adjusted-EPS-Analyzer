import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

from .config import XAI_API_KEY, XAI_BASE_URL, XAI_MODEL
from .news_fetcher import fetch_news_around_date, build_news_context
from .models import EventModel

load_dotenv()

def generate_event_summary(event_data: Dict[str, Any]) -> EventModel:
    if not XAI_API_KEY:
        return EventModel(
            code=f"event_{event_data.get('start_date', '')}",
            title="Dummy Event",
            comment="xAI API key not configured. Please set XAI_API_KEY.",
            categories=["other"],
            causality_confidence="Low",
            alternative_factors=[],
            is_main_cause=False,
            window_start=event_data.get("start_date", ""),
            window_end=event_data.get("end_date", ""),
        )

    prompt = build_prompt(event_data)

    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": XAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a senior equity analyst. Respond ONLY in JSON with the exact structure: {\"code\": \"E1\", \"title\": \"short title in English\", \"comment\": \"brief summary in Japanese within 200 characters\", \"categories\": [\"earnings\"], \"causality_confidence\": \"High\", \"alternative_factors\": [], \"is_main_cause\": true, \"window_start\": \"YYYY-MM-DD\", \"window_end\": \"YYYY-MM-DD\"}",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(f"{XAI_BASE_URL}/chat/completions", json=body, headers=headers, timeout=30)
        if resp.status_code != 200:
            # エラー詳細を表示
            error_detail = resp.text
            print(f"API Error {resp.status_code}: {error_detail}")
            return EventModel(
                code=f"error_{event_data.get('start_date', '')}",
                title="API Error",
                comment=f"HTTP {resp.status_code}: {error_detail[:200]}",
                categories=["error"],
                causality_confidence="Low",
                alternative_factors=[],
                is_main_cause=False,
                window_start=event_data.get("start_date", ""),
                window_end=event_data.get("end_date", ""),
            )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        obj = json.loads(content)
        return EventModel(**obj)
    except Exception as e:
        return EventModel(
            code=f"error_{event_data.get('start_date', '')}",
            title="API Error",
            comment=f"Failed to analyze: {str(e)}",
            categories=["error"],
            causality_confidence="Low",
            alternative_factors=[],
            is_main_cause=False,
            window_start=event_data.get("start_date", ""),
            window_end=event_data.get("end_date", ""),
        )

def build_prompt(event_data: Dict[str, Any]) -> str:
    ticker = event_data.get("ticker", "Unknown")
    start = event_data.get("start_date")
    end = event_data.get("end_date")
    spike_dates = event_data.get("spike_dates", [])
    price_summary = event_data.get("price_summary", {})

    max_return = price_summary.get('max_return', 0)
    min_return = price_summary.get('min_return', 0)
    max_vol_ratio = price_summary.get('max_vol_ratio', 0)

    prompt = f"""
Ticker: {ticker}
Event period: {start} to {end}
Spike days: {', '.join(spike_dates)}
Price change summary: max return {max_return:.2%}, min return {min_return:.2%}
Volume ratio: {max_vol_ratio:.2f}x average

You are a financial analyst. Using your knowledge of market events, recall the actual news, events, analyst reports, or social media posts that occurred around {start} that could explain this price/volume spike. Provide a concise analysis in Japanese (300-500 characters). Follow this structure:
- First sentence: state the price movement fact (date, return, volume ratio).
- Then list 2-4 key factors with bullet points. For each factor, include the date, specific details (product names, analyst names, numbers), and source (e.g., "Tesla's announcement on Sep 8", "Morgan Stanley report on Sep 11", "Elon Musk's X post on Sep 10").
- End with one sentence on broader market context or technical factors if applicable.
- Base your answer on factual knowledge. If you are uncertain about a specific detail, indicate that it is based on your recollection but try to be precise.
"""
    return prompt







