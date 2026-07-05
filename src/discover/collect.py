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
from datetime import date, datetime, timezone, timedelta
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
        "from": (datetime.now(JST) - timedelta(days=2)).strftime("%Y-%m-%d"),
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


def _dedupe_items(items: list) -> list:
    """DISCOVER-BUG-1: タイトル正規化での完全一致を除外し、importance='なし'も除外する。
    同一の出来事を異なる配信元から複数記事として取得した際、Grokが
    別アイテムとして分類してしまうケースの最終防波堤。"""
    seen_titles = set()
    deduped = []
    for i in items:
        key = i.get("title", "").strip().lower()
        if key and key not in seen_titles:
            seen_titles.add(key)
            deduped.append(i)
    return [i for i in deduped if i.get("importance") != "なし"]


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

【重複統合】
同一の出来事を報じる複数の見出し（異なる配信元による再掲・転載等）は
1件にまとめてください。重複を除いた結果のみをitemsに含めること。

ヘッドライン：
{headlines}

以下のJSON形式で回答してください（他のテキスト不要）：
{{"items": [{{"title": "...", "category": "カタリスト", "importance": "高", "summary": "30字以内の日本語要約", "url": "元記事のURLまたはnull", "source": "出典メディア名またはnull", "published_at": "YYYY-MM-DDまたはnull"}}], "top_importance": "高/中/低", "summary": "全体を50字以内で要約", "conditions_met": ["ニュースから読み取れる銘柄の通過条件（最大3件、なければ空配列）"], "risk_flags": ["ニュースから読み取れるリスク要因（最大3件、なければ空配列）"]}}
"""
    try:
        text = call_grok(prompt, max_tokens=1000)
        text = text.replace("```json", "").replace("```", "").strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            data["items"] = _dedupe_items(data.get("items", []))
            return data
    except Exception as e:
        print(f"Grok分類エラー ({ticker}): {e}")
    return {"items": [], "summary": "分類失敗"}


def classify_news_with_grok_search(ticker: str, company: str) -> dict:
    """NEWS_APIで記事が取れない場合のGrokによる代替検索"""
    prompt = f"""{company}（{ticker}）に関する直近48時間（週末含む）のニュースを
web検索で調べてください。

以下のカテゴリに該当するニュースがあれば（軽微なものも含む）JSON形式で回答してください：
- 決算・業績・ガイダンス
- 大型契約・提携・買収
- 製品発表・承認・規制
- 株価に影響しうる経営陣コメント

なければ items を空にしてください。
同一の出来事を報じる複数の見出し（異なる配信元による再掲・転載等）は
1件にまとめてください。重複を除いた結果のみをitemsに含めること。

{{
  "items": [
    {{"title": "...", "category": "カタリスト/リスク/ブレイクスルー/一般",
      "importance": "高/中/低", "summary": "30字以内の日本語要約",
      "url": "元記事のURLまたはnull", "source": "出典メディア名またはnull",
      "published_at": "YYYY-MM-DDまたはnull"}}
  ],
  "top_importance": "高/中/低",
  "summary": "全体を50字以内で要約",
  "conditions_met": ["ニュースから読み取れる銘柄の通過条件（最大3件、なければ空配列）"],
  "risk_flags": ["ニュースから読み取れるリスク要因（最大3件、なければ空配列）"]
}}"""
    result = call_grok(prompt, max_tokens=1000, model_override="grok-3")
    if not result:
        return {"items": [], "summary": "データなし", "top_importance": "低"}
    try:
        m = re.search(r'\{.*\}', result, re.DOTALL)
        if m:
            data = json.loads(m.group())
            data["items"] = _dedupe_items(data.get("items", []))
            return data
    except Exception:
        pass
    return {"items": [], "summary": "データなし", "top_importance": "低"}


def explore_candidates(existing_tickers: list) -> list:
    if not XAI_API_KEY:
        return []

    existing_str = ", ".join(existing_tickers)
    prompt = f"""
あなたはプロの株式アナリストです。
「市場がまだ気づいていない」米国株の新規投資候補を3〜5銘柄探してください。

【必須条件】以下をすべて満たす銘柄のみ推薦してください：
- 時価総額 $5億〜$100億（小〜中型株。大型・メガキャップは除外）
- 機関投資家保有率 40%未満（まだ大口資金に発掘されていない）
- 直近12ヶ月の売上成長率 30%以上（急成長中）
- S&P500・Russell1000・Nasdaq100等の主要指数に未採用
- 実際に売上が立っているビジネス（純コンセプト株は除外）

【推薦の視点】
- 有名・大型銘柄（NVDA, AAPL, MSFT, META等）は絶対に推薦しない
- 既存監視リストにある銘柄も除外する
- 「なぜ今まで見落とされていたか」の理由も説明すること

以下の銘柄は既に監視リストに登録済みのため除外してください：
{existing_str}

各銘柄について以下のJSON形式で回答してください（コードブロック不要）：
{{"candidates": [{{"ticker": "XXXX", "company": "会社名", "sector": "セクター", "market_cap_b": 時価総額（十億ドル）, "revenue_growth_pct": 売上成長率（%）, "institutional_ownership_pct": 機関投資家保有率（%）, "reason": "注目理由と見落とされていた背景（100字以内）", "risk": "主なリスク（50字以内）", "screening_pass": ["通過条件1", ...（実際に満たすものを最大5件）], "catalyst_type": "決算サプライズ|製品発表|規制変化|市場拡大|その他", "conviction": "高|中|低"}}]}}
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


def explore_macro_themes(existing_tickers: list) -> list:
    if not XAI_API_KEY:
        return []

    existing_str = ", ".join(existing_tickers)
    today = date.today().isoformat()
    prompt = f"""あなたは機関投資家向けのテーマ分析アナリストです。
web検索を使い、今後6〜18ヶ月で市場を動かす可能性がある
「特大テーマ候補」を3件分析してください。

以下の登録銘柄リストを参考に、テーマに関連する銘柄があれば
related_tickersに含めてください（リスト外の銘柄は含めない）：
{existing_str}

以下のJSON形式のみで回答してください。前置き・後置き不要：
{{
  "themes": [
    {{
      "theme": "テーマ名（20字以内）",
      "horizon": "投資時間軸（例: 6〜12ヶ月）",
      "conviction": "高|中|低",
      "background": "根拠・背景（100字以内）",
      "related_tickers": [
        {{"ticker": "登録銘柄のticker", "role": "主要|ボトルネック|注目", "note": "役割説明（30字以内）"}}
      ],
      "catalyst": "具体的なトリガーイベント（50字以内）",
      "sources": [{{"title": "情報源名または記事タイトル", "url": "https://...またはnull"}}]
    }}
  ]
}}
related_tickersのroleは「主要」「ボトルネック」「注目」の3種類のみ使用してください。
- 主要: テーマの恩恵を直接受ける中核銘柄
- ボトルネック: テーマ実現の制約要因となる銘柄（供給・インフラ・規制等）
- 注目: 特定の触媒やユニークなポジションで注目される銘柄
sourcesは根拠となったニュース・レポート・データを1〜3件記載してください。
URLが不明な場合はurlをnullにして情報源名のみ記載してください。"""
    try:
        text = call_grok(prompt, max_tokens=1200, model_override="grok-3")
        text = text.replace("```json", "").replace("```", "").strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            themes = data.get("themes", [])
            for theme in themes:
                theme["generated_at"] = today
            return themes
    except Exception as e:
        print(f"テーマ探索エラー: {e}")
    return []


def get_price_change(ticker: str) -> "float | None":
    """直近2営業日の終値比騰落率（%）を返す"""
    try:
        import yfinance as yf
        hist = yf.Ticker(ticker).history(period="2d", interval="1d")
        if len(hist) >= 2:
            prev = float(hist["Close"].iloc[-2])
            curr = float(hist["Close"].iloc[-1])
            if prev > 0:
                return round((curr - prev) / prev * 100, 2)
    except Exception as e:
        print(f"  price_change取得失敗 ({ticker}): {e}")
    return None


def add_price_changes_to_yesterday(now_jst: datetime) -> None:
    """前日分の月別履歴JSONに翌日騰落率（当日分データ）を追記する"""
    yesterday = (now_jst - timedelta(days=1)).strftime("%Y-%m-%d")
    ym = yesterday[:7].replace("-", "_")
    hist_path = Path(f"docs/discover/data/news_history_{ym}.json")
    if not hist_path.exists():
        return
    try:
        history = json.loads(hist_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"月別履歴JSON読み込みエラー ({hist_path}): {e}")
        return
    if yesterday not in history:
        return
    yesterday_data = history[yesterday]
    tickers_to_update = list(yesterday_data.keys())
    print(f"前日({yesterday}) {len(tickers_to_update)}銘柄の騰落率を付加中...")
    for ticker in tickers_to_update:
        change = get_price_change(ticker)
        for item in yesterday_data[ticker].get("items", []):
            item["price_change_next_day"] = change
        print(f"  {ticker}: {change}")
    hist_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"騰落率追記完了: {hist_path}")


def append_to_monthly_history(results: dict, now_jst: datetime) -> None:
    """当日分のニュース分類結果を月別履歴JSONに追記（同日キーは上書き）する"""
    today = now_jst.strftime("%Y-%m-%d")
    ym = today[:7].replace("-", "_")
    hist_path = Path(f"docs/discover/data/news_history_{ym}.json")
    history: dict = {}
    if hist_path.exists():
        try:
            history = json.loads(hist_path.read_text(encoding="utf-8"))
        except Exception:
            history = {}
    today_data: dict = {}
    for ticker, data in results.items():
        cl = data.get("classified", {})
        today_data[ticker] = {
            "items": [
                {"id": str(idx + 1), **{k: v for k, v in item.items() if k != "price_change_next_day"}}
                for idx, item in enumerate(cl.get("items", []))
            ],
            "top_importance": cl.get("top_importance", "低"),
            "summary":        cl.get("summary", ""),
            "conditions_met": cl.get("conditions_met", []),
            "risk_flags":     cl.get("risk_flags", []),
        }
    history[today] = today_data
    hist_path.parent.mkdir(parents=True, exist_ok=True)
    hist_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"月別履歴追記完了: {hist_path} ({len(history)}日分)")


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

    out = Path("docs/discover/data/daily_report.json")
    if now_jst.weekday() == 6:
        print("特大テーマ探索中（日曜日）...")
        macro_themes = explore_macro_themes(existing)
        if macro_themes:
            hist_path = Path("docs/discover/data/macro_themes_history.json")
            hist = []
            if hist_path.exists():
                try:
                    hist = json.loads(hist_path.read_text(encoding="utf-8"))
                except Exception:
                    hist = []
            hist.insert(0, {"generated_at": now_jst.strftime("%Y-%m-%d"), "themes": macro_themes})
            hist = hist[:26]
            hist_path.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"テーマ履歴追記: {hist_path} ({len(hist)}件)")
    else:
        try:
            with open(out, encoding="utf-8") as f:
                prev = json.load(f)
            macro_themes = prev.get("macro_themes", [])
            print(f"特大テーマ引継ぎ: {len(macro_themes)}件")
        except Exception:
            macro_themes = []

    # 前日分に翌日騰落率を追記し、当日分を月別履歴に保存
    add_price_changes_to_yesterday(now_jst)
    append_to_monthly_history(results, now_jst)

    report = {
        "generated_at": now_jst.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "tickers":      results,
        "candidates":   candidates,
        "macro_themes": macro_themes,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"完了: {len(results)}銘柄 + 候補{len(candidates)}件 + テーマ{len(macro_themes)}件")


if __name__ == "__main__":
    main()
