import os
import json
import re
import smtplib
import subprocess
import time
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.utils import formatdate
from openai import OpenAI

# 環境変数・設定
XAI_API_KEY   = os.getenv("XAI_API_KEY")
GMAIL_USER     = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
MAIL_TO        = os.getenv("GMAIL_USER")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
DB_FILE   = "src/subport/short_report/processed_content.json"

JST = timezone(timedelta(hours=9))

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

WAIT_BETWEEN_ACCOUNTS = 10  # 秒

# ショートレポート判定キーワード（日英）
SHORT_REPORT_KEYWORDS = [
    "short", "fraud", "不正", "詐欺", "overvalued", "sell",
    "we are short", "target price", "ショート", "レポート公開",
    "report", "investigation", "manipulate", "inflate", "fabricat",
    "警告", "疑惑", "会計操作", "水増し",
]


# ============================================================
# 既存関数（変更なし）
# ============================================================

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_db(db):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


def is_none_response(text: str) -> bool:
    cleaned = text.strip().upper()
    if cleaned == "NONE":
        return True
    if re.match(r"^SUMMARY\s*:\s*NONE\.?$", cleaned):
        return True
    return False


def extract_tweet_url(citations, username: str) -> str:
    if citations:
        for citation in citations:
            url = citation if isinstance(citation, str) else getattr(citation, "url", "")
            if url and ("x.com/" in url or "twitter.com/" in url) and "/status/" in url:
                return url
    return f"https://x.com/{username}"


def clean_summary(text: str) -> str:
    return re.sub(r'[\s　]*（\d+字）\s*$', '', text).strip()


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


def check_account(account: str, seen_summaries: list):
    now_jst       = datetime.now(JST)
    since_dt      = now_jst - timedelta(hours=13)
    since_time_str = since_dt.strftime('%Y-%m-%d %H:%M:%S')
    from_date_str  = since_dt.strftime('%Y-%m-%d')
    username       = account[1:]

    prompt = f"""
@{username} のX（旧Twitter）の投稿を確認してください。

【必須条件】
1. 日本時間 {since_time_str} 以降に投稿された投稿の中から、投資・経済・市場・政治に関して重要度が高いものを最大3件選んでください。
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

        posts = parse_posts(res_text)
        new_posts = [p for p in posts if p["summary"] not in seen_summaries]

        citations  = getattr(response, "citations", None)
        tweet_url  = extract_tweet_url(citations, username)

        for p in new_posts:
            p["url"] = tweet_url
            print(f"  ✅ 新規: {p['summary'][:60]}...")

        return new_posts

    except Exception as e:
        print(f"xAI APIエラー [{account}]: {str(e)}")
        return []


def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From']    = GMAIL_USER
    msg['To']      = MAIL_TO
    msg['Date']    = formatdate(localtime=True)
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("メール送信成功")
    except Exception as e:
        print(f"メール送信エラー: {str(e)}")


# ============================================================
# ★追加: ショートレポート検知 → スクリーナー自動起動
# ============================================================

def is_short_report(summary: str) -> bool:
    """投稿要約がショートレポート本体である可能性を判定"""
    summary_lower = summary.lower()
    return any(kw in summary_lower for kw in SHORT_REPORT_KEYWORDS)


def extract_ticker(summary: str) -> str | None:
    """
    要約から $TICKER 形式のティッカーを抽出。
    なければGrokに抽出させる。
    """
    # $TICKER 形式を優先
    match = re.search(r'\$([A-Z]{1,5})\b', summary)
    if match:
        return match.group(1)

    # Grokに抽出させる
    try:
        response = client.chat.completions.create(
            model="grok-3-mini",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    f"以下の文章から米国株のティッカーシンボルを1つだけ抽出してください。"
                    f"ティッカーのみを返してください。見つからない場合は「NONE」とだけ返してください。\n\n{summary}"
                )
            }],
        )
        ticker = response.choices[0].message.content.strip().upper()
        return None if ticker == "NONE" or len(ticker) > 5 else ticker
    except Exception:
        return None


def trigger_screener(ticker: str, summary: str, account: str, url: str):
    """screener.py をサブプロセスで起動"""
    screener_path = os.path.join(
        os.path.dirname(__file__), "src", "subport", "short_report", "screener.py"
    )
    if not os.path.exists(screener_path):
        print(f"  [screener] スクリプトが見つかりません: {screener_path}")
        return

    report_text = f"[{account}] {summary} {url}"
    print(f"  [screener] {ticker} をスクリーニング中...")

    result = subprocess.run(
        ["python", screener_path,
         "--ticker", ticker,
         "--report-text", report_text],
        capture_output=True, text=True, timeout=120,
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print(f"  [screener エラー] {result.stderr[:200]}")


def process_short_report_candidates(new_posts_by_account: list):
    """
    新規投稿の中からショートレポート候補を検出し、
    screener.py を自動起動する。
    new_posts_by_account: [(account, post), ...]
    """
    candidates = []
    for account, post in new_posts_by_account:
        summary = post["summary"]
        if not is_short_report(summary):
            continue

        ticker = extract_ticker(summary)
        if not ticker:
            print(f"  [screener] ティッカー抽出失敗 → スキップ: {summary[:50]}")
            continue

        print(f"\n  [ショートレポート候補] {account} → {ticker}")
        candidates.append((account, post, ticker))

    for account, post, ticker in candidates:
        trigger_screener(ticker, post["summary"], account, post.get("url", ""))
        time.sleep(3)  # API連続呼び出し回避

    return candidates


# ============================================================
# メイン
# ============================================================

def main():
    db          = load_db()
    new_updates = []
    all_new_posts = []   # ★ (account, post) のリスト
    total = len(TARGET_ACCOUNTS)
    print(f"{total} アカウントをチェック開始...")

    for i, account in enumerate(TARGET_ACCOUNTS):
        print(f"[{i+1}/{total}] {account} チェック中...")

        stored = db.get(account, [])
        if isinstance(stored, str):
            seen_summaries = [stored]
        else:
            seen_summaries = stored

        posts = check_account(account, seen_summaries)

        if posts:
            updated = seen_summaries + [p["summary"] for p in posts]
            db[account] = updated[-10:]

            for p in posts:
                time_label = f"🕐 {p['posted_at']}\n" if p['posted_at'] else ""
                new_updates.append(
                    f"🔔 {account}\n{time_label}{p['summary']}\n🔗 {p['url']}"
                )
                all_new_posts.append((account, p))   # ★
        else:
            print(f"  ⏭ 新規投稿なし")

        if i < total - 1:
            print(f"  {WAIT_BETWEEN_ACCOUNTS} 秒待機...")
            time.sleep(WAIT_BETWEEN_ACCOUNTS)

    save_db(db)
    print("DB保存完了")

    # ★ ショートレポート候補を自動スクリーニング
    if all_new_posts:
        print("\n[ショートレポート検知フェーズ]")
        candidates = process_short_report_candidates(all_new_posts)
        if candidates:
            print(f"  スクリーナー起動: {len(candidates)} 件")
        else:
            print("  ショートレポート候補なし")

    # メール通知（既存）
    if new_updates:
        message_body = "\n\n---\n\n".join(new_updates)
        now_jst = datetime.now(JST)
        subject = f"🦝01_【ショートセラーニュース】 {now_jst.strftime('%m/%d %H:%M')} JST"
        send_email(subject, message_body)
        print(f"処理完了。{len(new_updates)} 件の更新あり。")
    else:
        print("新しい更新（13時間以内）はありませんでした。")


if __name__ == "__main__":
    main()
