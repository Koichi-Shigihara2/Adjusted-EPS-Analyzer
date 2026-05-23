#!/usr/bin/env python3
"""
Discover - 情報収集レーダー
毎日JST 7:00実行
- 登録銘柄のニュース収集・分類
- 新規候補探索
"""

import json
import os
import re
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

XAI_API_KEY = os.getenv("XAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
JST = timezone(timedelta(hours=9))


def load_config() -> dict:
    path = Path("config/discover_config.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fetch_news(ticker: str, company_name: str) -> list:
    if not NEWS_API_KEY:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f"{ticker} OR {company_name}",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "from": (datetime.now(JST) - timedelta(days=1)).strftime("%Y-%m-%d"),
        "apiKey": NEWS_API_KEY,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        return res.json().get("articles", [])
    except Exception as e:
        print(f"NEWS_API error ({ticker}): {e}")
        return []


GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_HEADERS = {"Content-Type": "application/json"}
GROK_MODELS = ["grok-3-mini", "grok-3", "grok-2-1212"]


def call_grok(prompt: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
    headers = {**GROK_HEADERS, "Authorization": f"Bearer {XAI_API_KEY}"}
    last_error = None
    for model in GROK_MODELS:
        try:
            print(f"[INFO] Grokモデル試行中: {model}")
            resp = requests.post(GROK_URL, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }, timeout=120)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            print(f"[OK] Grokモデル成功: {model}")
            return text
        except Exception as e:
            print(f"[WARN] Grokモデル失敗 ({model}): {e}")
            last_error = e
    print("[ERROR] すべてのGrokモデルで失敗しました")
    raise last_error


def classify_news(ticker: str, articles: list) -> dict:
    if not articles or not XAI_API_KEY:
        return {"items": [], "summary": "データなし"}

    headlines = "\n".join([
        f"- {a.get('title', '')} ({a.get('publishedAt', '')[:10]})"
        for a in articles[:5]
    ])

    prompt = f"""
以下は{ticker}に関する直近24時間のニュースヘッドラインです。
各ニュースを以下のカテゴリに分類し、投資家として重要度（高/中/低）を判定してください。

カテゴリ：
- カタリスト（決算・FDA承認・大型契約・提携・新製品）
- リスク（規制・訴訟・競合参入・業績悪化）
- ブレイクスルー（技術革新・市場拡大・業界変革）
- 一般（その他）

ヘッドライン：
{headlines}

以下のJSON形式で回答してください（他のテキスト不要）：
{{"items": [{{"title": "...", "category": "カタリスト", "importance": "高", "summary": "30字以内の日本語要約"}}], "top_importance": "高/中/低", "summary": "全体を50字以内で要約"}}
"""
    try:
        text = call_grok(prompt, max_tokens=800)
        text = text.replace("```json", "").replace("```", "").strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        print(f"Grok分類エラー ({ticker}): {e}")
    return {"items": [], "summary": "分類失敗"}


def explore_candidates() -> list:
    if not XAI_API_KEY:
        return []

    prompt = """
以下の条件を満たす米国株の新規投資候補を3〜5銘柄探してください：
- AI・宇宙・医療・エネルギー転換等の成長分野
- 機関投資家の保有比率が増加傾向
- 売上成長率20%以上
- まだ一般的に広く知られていない（時価総額100億〜1000億ドル程度）

各銘柄について以下のJSON形式で回答してください（コードブロック不要）：
{"candidates": [{"ticker": "XXXX", "company": "会社名", "sector": "セクター", "reason": "注目理由（100字以内）", "risk": "主なリスク（50字以内）"}]}
"""
    try:
        text = call_grok(prompt, max_tokens=1000)
        text = text.replace("```json", "").replace("```", "").strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            return data.get("candidates", [])
    except Exception as e:
        print(f"候補探索エラー: {e}")
    return []


def main():
    now_jst = datetime.now(JST)
    config  = load_config()
    tickers = config.get("tickers", {})

    active = {t: v for t, v in tickers.items()
              if v.get("category") in ["保有中", "監視中", "様子見"]}

    print(f"対象銘柄: {len(active)}件")

    results = {}
    for ticker, info in active.items():
        print(f"  {ticker} ({info['category']}) 収集中...")
        articles  = fetch_news(ticker, ticker)
        classified = classify_news(ticker, articles)
        results[ticker] = {
            "category":      info["category"],
            "memo":          info.get("memo", ""),
            "classified":    classified,
            "top_importance": classified.get("top_importance", "低"),
        }

    print("新規候補探索中...")
    candidates = explore_candidates()

    report = {
        "generated_at": now_jst.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "tickers":      results,
        "candidates":   candidates,
    }

    out = Path("docs/discover/data/daily_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"完了: {len(results)}銘柄 + 候補{len(candidates)}件")


if __name__ == "__main__":
    main()
