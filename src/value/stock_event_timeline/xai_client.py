from typing import Dict, Any
import requests

from .config import XAI_API_KEY, XAI_BASE_URL, XAI_MODEL
from .models import EventModel


def generate_event_summary(payload: Dict[str, Any]) -> EventModel:
    """
    payload 縺ｫ縺ｯ莉･荳九ｒ蜷ｫ繧√ｋ諠ｳ螳夲ｼ・
    - ticker, event_date, window_start, window_end
    - price/volume summary
    - sp500 summary
    - news_context
    """
    if not XAI_API_KEY:
        # 髢狗匱譎ゅ・繝繝溘・繧定ｿ斐☆
        return EventModel(
            code=payload.get("code", "E1"),
            title="Dummy Event",
            comment="髢狗匱逕ｨ縺ｮ繝繝溘・繧､繝吶Φ繝医〒縺吶・,
            categories=["other"],
            causality_confidence="Low",
            alternative_factors=[],
            is_main_cause=False,
            window_start=payload.get("window_start", payload.get("event_date", "")),
            window_end=payload.get("window_end", payload.get("event_date", "")),
        )

    prompt = payload["prompt"]
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": XAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an equity event analyst. Respond ONLY in JSON.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(f"{XAI_BASE_URL}/chat/completions", json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    # content 縺ｯ JSON 譁・ｭ怜・諠ｳ螳・
    import json
    obj = json.loads(content)
    return EventModel(**obj)
