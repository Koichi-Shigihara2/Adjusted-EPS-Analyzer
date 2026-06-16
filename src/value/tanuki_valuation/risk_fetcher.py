"""
TANUKI VALUATION - Risk Event Fetcher
Grok web search で直近3ヶ月の既知リスクイベントを取得する。
"""

import json
import os
import time
from typing import Any, Dict, List

import requests

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
GROK_URL    = "https://api.x.ai/v1/chat/completions"
GROK_MODELS = ["grok-3", "grok-3-mini", "grok-2-1212"]


def fetch_risk_events(ticker: str, company_name: str = "") -> List[Dict[str, Any]]:
    """
    Grok web search で直近3ヶ月の既知リスクイベントを最大3件取得。
    失敗時は [] を返す（パイプライン停止させない）。
    """
    if not XAI_API_KEY:
        print(f"   [{ticker}] XAI_API_KEY 未設定 → risk_events スキップ")
        return []

    name_part = company_name or ticker
    system_prompt = (
        "You are a financial risk analyst. "
        "List up to 3 known or ongoing risk events for the given company. "
        "Include active litigation, regulatory investigations, competitive threats, or earnings risks. "
        "Return JSON array only, no explanation: "
        "[{\"type\":\"regulatory\",\"summary\":\"one line description\",\"impact\":\"high\"}] "
        "Use impact: high / mid / low. Return [] if no significant risks known."
    )
    user_prompt = (
        f"{ticker} {name_part} "
        "known risks: antitrust lawsuit regulatory SEC investigation earnings warning competition 2025 2026. "
        "List current or ongoing risk events as JSON."
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}",
    }
    base_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    for model in GROK_MODELS:
        payload: Dict[str, Any] = {
            "model":       model,
            "messages":    base_messages,
            "max_tokens":  600,
            "temperature": 0.1,
        }
        try:
            resp = requests.post(GROK_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()

            start = text.find("[")
            end   = text.rfind("]") + 1
            if start >= 0 and end > start:
                events = json.loads(text[start:end])
                if isinstance(events, list):
                    print(f"   [{ticker}] risk_events: {len(events)}件 ({model})")
                    return events

            print(f"   [{ticker}] Grok risk parse failed: {text[:120]}")
            return []

        except Exception as e:
            print(f"   [{ticker}] Grok risk failed ({model}): {e}")

        time.sleep(0.1)

    print(f"   [{ticker}] risk_events: 全モデル失敗 → []")
    return []
