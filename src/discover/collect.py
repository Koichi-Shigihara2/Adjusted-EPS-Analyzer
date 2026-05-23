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


def get_company_name(ticker: str) -> str:
    try:
        path = Path("docs/value-monitor/tanuki_valuation/data/tickers.json")
        with open(path) as f:
            tickers = json.load(f)
        for t in tickers:
            if t.get("ticker") == ticker:
                return t.get("name", ticker)
    except Exception:
        pass
    return ticker


def fetch_news(ticker: str) -> list:
    if not NEWS_API_KEY:
        return []
    company = get_company_name(ticker)
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f'"{company}" OR "{ticker} stock"',
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "from": (datetime.now(JST) - timedelta(days=1)).strftime("%Y-%m-%d"),
        "excludeDomains": "seekingalpha.com,fool.com,benzinga.com,nypost.com,dailymail.co.uk,thesun.co.uk,tmz.com",
        "apiKey": NEWS_API_KEY,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        articles = res.json().get("articles", [])
        print(f"    NEWS_API: {len(articles)}件取得 ({ticker})")
        return articles
    except Exception as e:
        print(f"NEWS_API error ({ticker}): {e}")
        return []


GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_HEADERS = {"Content-Type": "application/json"}
GROK_MODELS = ["grok-3-mini", "grok-3", "grok-2-1212"]


def call_grok(prompt: str, max_tokens: int = 800, temperature: float = 0.3, model_override: str = None) -> str:
    headers = {**GROK_HEADERS, "Authorization": f"Bearer {XAI_API_KEY}"}
    models = [model_override] if model_override else GROK_MODELS
    last_error = None
    for model in models:
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


def classify_news(ticker: str, articles: list, company: str = "") -> dict:
    if not articles or not XAI_API_KEY:
        return {"items": [], "summary": "データなし"}

    if not company:
        company = ticker

    headlines = "\n".join([
        f"- {a.get('title', '')} ({a.get('publishedAt', '')[:10]})"
        for a in articles[:5]
    ])

    prompt = f"""
以下は{ticker}（{company}）に関する直近24時間のニュースヘッドラインです。
各ニュースを以下のカテゴリに分類し、投資家として重要度（高/中/低/なし）を判定してください。

カテゴリ：
- カタリスト（決算・FDA承認・大型契約・提携・新製品）
- リスク（規制・訴訟・競合参入・業績悪化）
- ブレイクスルー（技術革新・市場拡大・業界変革）
- 一般（その他）

【除外条件】以下のニュースは重要度「なし」として除外してください：
- {ticker}（{company}）が主役ではなく、複数銘柄の中の1つとして言及されている記事
  （例：「注目10銘柄」「AI株ランキング」「ETFの組入れ上位」等）
- マクロ経済・金利・市場全体に関する記事（個別銘柄の言及なし）
- AI業界全体・半導体セクター全体の話題で個別企業の具体的情報がない記事
- ETF・投資信託の組入銘柄として言及されているだけの記事
- 複数企業を並べたランキング・比較記事

【主役判定の基準】
記事のタイトルまたは本文の冒頭で{ticker}または{company}が
主要な話題として取り上げられている場合のみ対象とする

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
            data = json.loads(m.group())
            data["items"] = [i for i in data.get("items", []) if i.get("importance") != "なし"]
            return data
    except Exception as e:
        print(f"Grok分類エラー ({ticker}): {e}")
    return {"items": [], "summary": "分類失敗"}


def classify_news_with_grok_search(ticker: str, company: str) -> dict:
    """NEWS_APIで記事が取れない場合のGrokによる代替検索"""
    prompt = f"""{company}（{ticker}）に関する直近24時間の重要ニュースを
web検索で調べてください。

投資家として重要なニュース（決算・契約・製品・規制・人事等）が
あれば以下のJSON形式で回答してください。
重要なニュースがない場合は items を空にしてください。

{{
  "items": [
    {{"title": "...", "category": "カタリスト/リスク/ブレイクスルー/一般",
      "importance": "高/中/低", "summary": "30字以内の日本語要約"}}
  ],
  "top_importance": "高/中/低",
  "summary": "全体を50字以内で要約"
}}"""
    result = call_grok(prompt, max_tokens=800, model_override="grok-3")
    if not result:
        return {"items": [], "summary": "データなし", "top_importance": "低"}
    try:
        m = re.search(r'\{.*\}', result, re.DOTALL)
        if m:
            data = json.loads(m.group())
            data["items"] = [i for i in data.get("items", []) if i.get("importance") != "なし"]
            return data
    except Exception:
        pass
    return {"items": [], "summary": "データなし", "top_importance": "低"}


def explore_candidates(existing_tickers: list) -> list:
    if not XAI_API_KEY:
        return []

    existing_str = ", ".join(existing_tickers)
    prompt = f"""
以下の条件を満たす米国株の新規投資候補を3〜5銘柄探してください：
- AI・宇宙・医療・エネルギー転換等の成長分野
- 機関投資家の保有比率が増加傾向
- 売上成長率20%以上
- まだ一般的に広く知られていない（時価総額100億〜1000億ドル程度）

以下の銘柄は既に監視リストに登録済みのため除外してください：
{existing_str}

各銘柄について以下のJSON形式で回答してください（コードブロック不要）：
{{"candidates": [{{"ticker": "XXXX", "company": "会社名", "sector": "セクター", "reason": "注目理由（100字以内）", "risk": "主なリスク（50字以内）"}}]}}
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
        company  = get_company_name(ticker)
        articles = fetch_news(ticker)
        if articles:
            classified = classify_news(ticker, articles, company)
        elif info.get("category") in ["保有中", "監視中"]:
            print(f"    NEWS_API 0件 → Grok web検索で代替")
            classified = classify_news_with_grok_search(ticker, company)
        else:
            classified = {"items": [], "summary": "データなし", "top_importance": "低"}
        results[ticker] = {
            "category":      info["category"],
            "memo":          info.get("memo", ""),
            "classified":    classified,
            "top_importance": classified.get("top_importance", "低"),
        }

    print("新規候補探索中...")
    existing = list(config.get("tickers", {}).keys())
    candidates = explore_candidates(existing)

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
