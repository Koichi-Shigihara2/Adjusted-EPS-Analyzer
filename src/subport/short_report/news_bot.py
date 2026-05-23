import os
import json
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone

import requests
from openai import OpenAI

# ─── 環境変数 ─────────────────────────────────────────────────
XAI_API_KEY = os.getenv("XAI_API_KEY")

DB_FILE = "src/subport/short_report/processed_content.json"
JST     = timezone(timedelta(hours=9))

client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

TARGET_ACCOUNTS = [
    "@HindenburgRes",
    "@muddystaters",
    "@CitronResearch",
    "@KerrisdaleCap",
    "@CullyResearch",
    "@ResearchGrizzly",
    "@IcebergRes",
    "@WolfpackRes",
    "@ViceroyResearch",
    "@PresciencePoint",
    "@GMTResearch",
    "@BlueOrcaResearch",
    "@SafkhetCapital",
    "@WhiteDiamondRes",
    "@BleeckerStRes",
]

WAIT_BETWEEN_ACCOUNTS = 10

# Step1 高確度キーワード（無料・高速フィルター）
HIGH_CONFIDENCE_KEYWORDS = [
    "we are short",
    "we're short",
    "new report",
    "new short report",
    "initiating short",
    "target price",
    "price target",
    "forensic analysis",
    "accounting irregularities",
    "we have published",
    "our report",
    "read our report",
    "released our report",
    "ショートレポート発行",
    "空売りレポート",
]


# ─── DB ─────────────────────────────────────────────────────
def load_db() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_db(db: dict):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


# ─── テキスト処理 ─────────────────────────────────────────────
def is_none_response(text: str) -> bool:
    cleaned = text.strip().upper()
    if cleaned == "NONE":
        return True
    if re.match(r"^SUMMARY\s*:\s*NONE\.?$", cleaned):
        return True
    return False


def clean_summary(text: str) -> str:
    return re.sub(r'[\s　]*（\d+字）\s*$', '', text).strip()


def extract_tweet_url(citations, username: str) -> str:
    if citations:
        for citation in citations:
            url = citation if isinstance(citation, str) else getattr(citation, "url", "")
            if url and ("x.com/" in url or "twitter.com/" in url) and "/status/" in url:
                return url
    return f"https://x.com/{username}"


def parse_posts(res_text: str) -> list:
    posts = []
    blocks = re.split(r'\bPOST\s*\d*\s*:', res_text, flags=re.IGNORECASE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        posted_match  = re.search(r"PostedAt\s*:\s*(.+)", block, re.IGNORECASE)
        summary_match = re.search(r"Summary\s*:\s*([\s\S]+?)(?=PostedAt\s*:|$)", block, re.IGNORECASE)
        if summary_match:
            summary = clean_summary(summary_match.group(1).strip())
            if summary and not is_none_response(summary):
                posts.append({
                    "posted_at": posted_match.group(1).strip() if posted_match else "",
                    "summary":   summary,
                })
    return posts


# ─── Discord送信 ─────────────────────────────────────────────
def send_discord(message: str, urgent: bool = False):
    webhook_url = os.getenv("DISCORD_WEB_HOOK")
    if not webhook_url:
        return
    content = f"@here {message}" if urgent else message
    try:
        requests.post(webhook_url, json={"content": content}, timeout=10)
    except Exception as e:
        print(f"Discord送信エラー: {e}")


# ─── 機能A: ニュースメッセージ整形 ────────────────────────────
def format_news_message(account: str, post: dict) -> str:
    posted_at = post.get("posted_at", "")
    time_part = f" | {posted_at}" if posted_at else ""
    return (
        f"📰 ショートセラーニュース\n"
        f"{account}{time_part}\n"
        f"{post['summary']}\n"
        f"🔗 {post['url']}"
    )


# ─── Grok: アカウント投稿チェック ─────────────────────────────
def check_account(account: str, seen_summaries: list) -> list:
    now_jst        = datetime.now(JST)
    since_dt       = now_jst - timedelta(hours=13)
    since_time_str = since_dt.strftime('%Y-%m-%d %H:%M:%S')
    from_date_str  = since_dt.strftime('%Y-%m-%d')
    username       = account[1:]

    prompt = f"""
@{username} のX（旧Twitter）の投稿を確認してください。

【対象条件】
以下のいずれかに該当する投稿のみを対象にしてください：
1. 新しいショートレポートの発行・公開・ティーザー
2. 特定銘柄への空売り開始宣言
3. 不正会計・詐欺・過大評価に関する調査報告
上記に該当しない一般的な市場コメント・ニュース共有は除外してください。

【必須条件】
1. 日本時間 {since_time_str} 以降に投稿された投稿の中から、最大3件選んでください。
2. 条件に合う投稿が1件もない場合は、必ず「None」とだけ回答してください。
3. 投稿が見つかった場合は、重要度が高い順に以下の【回答形式】で列挙してください。

【回答形式】
POST 1:
PostedAt: (投稿日時をJST表記で。例: 2026/03/10 14:32 JST)
Summary: (100〜150字の日本語要約。以下を守ること)
  - 投稿に書かれていることだけを要約し、憶測や補足で膨らませない
  - 銘柄名・企業名・経済指標など固有名詞は省略しない
  - 強気/弱気/中立などスタンスを明示
  - 具体的な数字があれば記載
  - 投稿にグラフや画像が添付されている場合、その内容・データの意味・投稿者の意図を文脈から読み取って説明すること
  - 末尾に文字数を記載しない

POST 2: (あれば)
PostedAt: ...
Summary: ...

POST 3: (あれば)
PostedAt: ...
Summary: ...
"""

    try:
        response = client.responses.create(
            model="grok-4-fast-non-reasoning",
            input=[{"role": "user", "content": prompt}],
            tools=[{
                "type": "x_search",
                "allowed_x_handles": [username],
                "from_date": from_date_str,
            }],
            max_output_tokens=1200,
            temperature=0.0,
        )

        res_text = ""
        for item in response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        res_text += block.text

        res_text = res_text.strip() if res_text else "None"
        print(f"Debug [{account}]: {res_text[:200]}...")

        if is_none_response(res_text):
            return []

        posts     = parse_posts(res_text)
        new_posts = [p for p in posts if p["summary"] not in seen_summaries]
        citations = getattr(response, "citations", None)
        tweet_url = extract_tweet_url(citations, username)

        for p in new_posts:
            p["url"] = tweet_url
            print(f"  ✅ 新規: {p['summary'][:60]}...")

        return new_posts

    except Exception as e:
        print(f"xAI APIエラー [{account}]: {str(e)}")
        return []


# ─── 機能B: ショートレポート2段階判定 ─────────────────────────
def passes_keyword_filter(summary: str) -> bool:
    """Step1: 高確度キーワードフィルター（無料・高速）"""
    lower = summary.lower()
    return any(kw in lower for kw in HIGH_CONFIDENCE_KEYWORDS)


def confirm_short_report_by_grok(summary: str) -> bool:
    """Step2: Grokによる確認（Yes/Noのみ）"""
    prompt = (
        "以下の投稿要約は、ショートセラーが新しいショートレポートを発行・公開した"
        "投稿ですか？（銘柄への言及・価格目標・不正疑惑等を含む）"
        "Yes または No のみで答えてください。\n\n"
        f"要約：{summary}"
    )
    try:
        response = client.chat.completions.create(
            model="grok-3-mini",
            max_tokens=10,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception as e:
        print(f"  [Grok確認] APIエラー: {e}")
        return False


def is_short_report(summary: str) -> bool:
    """2段階判定: Step1キーワード → Step2 Grok確認"""
    if not passes_keyword_filter(summary):
        return False
    print("  [Step1] キーワード一致 → Grok確認中...")
    result = confirm_short_report_by_grok(summary)
    print(f"  [Step2] Grok判定: {'Yes ✅' if result else 'No ❌'}")
    return result


def format_short_report_message(account: str, post: dict, ticker: str) -> str:
    posted_at = post.get("posted_at", "")
    time_part = f" | {posted_at}" if posted_at else ""
    return (
        f"⚠️ ショートレポート検知\n"
        f"{account}{time_part} → ${ticker}\n"
        f"{post['summary']}\n"
        f"🔗 {post['url']}\n"
        f"→ スクリーナー起動中..."
    )


# ─── ティッカー抽出 ───────────────────────────────────────────
def extract_ticker(summary: str) -> str | None:
    match = re.search(r'\$([A-Z]{1,5})\b', summary)
    if match:
        return match.group(1)

    try:
        response = client.chat.completions.create(
            model="grok-3-mini",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    "以下の文章から米国株のティッカーシンボルを1つだけ抽出してください。"
                    "ティッカーのみを返してください。見つからない場合は「NONE」とだけ返してください。"
                    f"\n\n{summary}"
                ),
            }],
        )
        ticker = response.choices[0].message.content.strip().upper()
        return None if ticker == "NONE" or len(ticker) > 5 else ticker
    except Exception:
        return None


# ─── screener.py 起動・ENTRY_SIGNAL解析 ─────────────────────
def parse_entry_signal(line: str) -> dict:
    """ENTRY_SIGNAL: ticker=XX impact=XX analysts=XX inst_pct=XX drop=XX を解析"""
    params = {}
    for part in line.split(":", 1)[1].strip().split():
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    return params


def trigger_screener(ticker: str, summary: str, account: str, url: str) -> dict | None:
    """screener.py をサブプロセスで起動し、ENTRY_SIGNALがあれば解析して返す"""
    screener_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screener.py")
    if not os.path.exists(screener_path):
        print(f"  [screener] スクリプトが見つかりません: {screener_path}")
        return None

    report_text = f"[{account}] {summary} {url}"
    print(f"  [screener] ${ticker} をスクリーニング中...")

    result = subprocess.run(
        ["python", screener_path, "--ticker", ticker, "--report-text", report_text],
        capture_output=True, text=True, timeout=120,
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print(f"  [screener エラー] {result.stderr[:200]}")

    for line in result.stdout.splitlines():
        if line.startswith("ENTRY_SIGNAL:"):
            return parse_entry_signal(line)
    return None


# ─── 機能C: エントリーシグナルメッセージ整形 ─────────────────
def format_entry_signal_message(signal: dict) -> str:
    ticker   = signal.get("ticker", "?")
    score    = signal.get("impact", "?")
    analysts = signal.get("analysts", "?")
    inst_pct = signal.get("inst_pct", "?")
    drop     = signal.get("drop", "?")
    return (
        f"🚨 逆張りエントリーシグナル\n"
        f"${ticker} — 全条件クリア\n"
        f"impact: {score} / analysts: {analysts} / 機関保有: {inst_pct}%\n"
        f"20日高値から: {drop}% 下落\n"
        f"→ エントリー検討"
    )


# ─── メイン ──────────────────────────────────────────────────
def main():
    db            = load_db()
    all_new_posts = []
    total         = len(TARGET_ACCOUNTS)
    print(f"{total} アカウントをチェック開始...")

    # 1. 15アカウントを順番にチェック / 2. 新規投稿があればA通知
    for i, account in enumerate(TARGET_ACCOUNTS):
        print(f"[{i+1}/{total}] {account} チェック中...")

        stored         = db.get(account, [])
        seen_summaries = [stored] if isinstance(stored, str) else stored

        posts = check_account(account, seen_summaries)

        if posts:
            db[account] = (seen_summaries + [p["summary"] for p in posts])[-10:]
            for p in posts:
                send_discord(format_news_message(account, p))  # 機能A
                all_new_posts.append((account, p))
                time.sleep(1)  # Discord rate limit 対策
        else:
            print("  ⏭ 新規投稿なし")

        if i < total - 1:
            print(f"  {WAIT_BETWEEN_ACCOUNTS} 秒待機...")
            time.sleep(WAIT_BETWEEN_ACCOUNTS)

    save_db(db)
    print("DB保存完了")

    if not all_new_posts:
        print("新しい更新（13時間以内）はありませんでした。")
        return

    # 3. Step1キーワード → Step2 Grok判定
    # 4. ショートレポート確定 → B通知
    # 5. screener.py起動
    # 6. エントリーシグナルならC通知（@here）
    print("\n[ショートレポート検知フェーズ]")
    confirmed = 0

    for account, post in all_new_posts:
        if not is_short_report(post["summary"]):
            continue

        ticker = extract_ticker(post["summary"])
        if not ticker:
            print(f"  [screener] ティッカー抽出失敗 → スキップ: {post['summary'][:50]}")
            continue

        print(f"\n  ⚠️ ショートレポート確認 [{account}] → ${ticker}")

        # 4. B通知
        send_discord(format_short_report_message(account, post, ticker), urgent=False)

        # 5. screener起動
        signal = trigger_screener(ticker, post["summary"], account, post.get("url", ""))

        # 6. エントリーシグナルならC通知
        if signal:
            send_discord(format_entry_signal_message(signal), urgent=True)

        confirmed += 1
        time.sleep(3)

    print(f"  ショートレポート確認数: {confirmed} 件")


if __name__ == "__main__":
    main()
