"""
ショートレポート逆張り戦略 スクリーナー
========================================
実行: python screener.py --ticker ACME --report-url https://...
     python screener.py --ticker ACME --report-text "report body here"
     python screener.py --dry-run   # テスト実行（通知なし）
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yfinance as yf

# ============================================================
# 設定読み込み
# ============================================================
CONFIG_PATH = Path(__file__).parent / "config.json"
TRADES_PATH = Path(__file__).parent / "trades.csv"
STATE_PATH  = Path(__file__).parent / "state.json"   # 保有中・禁止銘柄の状態


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {
        "open_position": None,        # {"ticker": str, "entry_date": str, "entry_price": float}
        "banned_tickers": {},         # {"ACME": "2026-05-01"} (禁止解除日)
        "consecutive_losses": 0,
        "skip_next": False,
    }


def save_state(state: dict):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ============================================================
# Step 1: 株価データ取得
# ============================================================

def get_price_data(ticker: str) -> dict | None:
    """株価・20日高値・200日MA・アナリスト数・機関保有比率を取得"""
    try:
        stock = yf.Ticker(ticker)
        hist  = stock.history(period="1y")
        if hist.empty:
            return None

        current_price    = float(hist["Close"].iloc[-1])
        high_20d         = float(hist["Close"].iloc[-20:].max())
        drop_from_high   = (current_price - high_20d) / high_20d * 100  # 負の値

        ma200 = float(hist["Close"].rolling(200).mean().iloc[-1]) if len(hist) >= 200 else None

        # S&P500 vs 200日MA（市場環境判定）
        sp500      = yf.Ticker("^GSPC").history(period="1y")
        sp_current = float(sp500["Close"].iloc[-1])
        sp_ma200   = float(sp500["Close"].rolling(200).mean().iloc[-1]) if len(sp500) >= 200 else None
        bull_market = (sp_ma200 is not None) and (sp_current > sp_ma200)

        # アナリスト情報
        info             = stock.info
        analysts         = info.get("numberOfAnalystOpinions", 0) or 0
        inst_ownership   = (info.get("heldPercentInstitutions", 0) or 0) * 100

        # 決算日
        earnings_dates = None
        try:
            cal = stock.calendar
            if cal is not None and "Earnings Date" in cal:
                ed = cal["Earnings Date"]
                if isinstance(ed, list) and len(ed) > 0:
                    earnings_dates = ed[0]
                elif hasattr(ed, 'date'):
                    earnings_dates = ed
        except Exception:
            pass

        return {
            "ticker":          ticker,
            "current_price":   round(current_price, 2),
            "high_20d":        round(high_20d, 2),
            "drop_from_high":  round(drop_from_high, 2),   # 例: -15.3
            "ma200":           round(ma200, 2) if ma200 else None,
            "bull_market":     bull_market,
            "analysts":        int(analysts),
            "inst_ownership":  round(float(inst_ownership), 1),
            "earnings_date":   str(earnings_dates) if earnings_dates else None,
        }

    except Exception as e:
        print(f"[価格取得エラー] {ticker}: {e}")
        return None


# ============================================================
# Step 2: インパクトスコア算出（Grok API）
# ============================================================

SCORE_PROMPT = """\
以下のショートセラーレポートを読み、インパクトスコア（0〜100）を算出してください。

採点基準：
- 財務不正・会計操作の告発：30点
- 経営陣の詐欺・横領告発：25点
- ビジネスモデル自体の否定：20点
- 製品・サービスの誇大広告指摘：15点
- 競合比較による割高批判のみ：5点
- 過去に類似告発で株価が回復した前例あり：-10点（減点）

出力形式（JSONのみ、前後に説明文・コードブロック記号不要）：
{{"score": <0-100の整数>, "reason": "<50字以内の採点理由>", "highest_risk_item": "<最もリスクの高い告発内容を一言で>"}}

レポート本文（または要約）：
{report_text}
"""


def score_report(report_text: str) -> dict:
    """Grok APIでインパクトスコアを算出"""
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        print("[警告] XAI_API_KEY が未設定。スコアを手動で入力してください。")
        score = int(input("インパクトスコア (0-100): ").strip())
        return {"score": score, "reason": "手動入力", "highest_risk_item": "不明"}

    prompt = SCORE_PROMPT.format(report_text=report_text[:4000])  # 最大4000字
    payload = {
        "model": "grok-3-mini",
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        # JSONブロック除去
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result
    except Exception as e:
        print(f"[Grok APIエラー] {e}")
        score = int(input("インパクトスコアを手動入力 (0-100): ").strip())
        return {"score": score, "reason": "手動入力（API失敗）", "highest_risk_item": "不明"}


def fetch_report_text(url: str) -> str:
    """URLからレポートテキストを取得"""
    try:
        resp = requests.get(url, timeout=30,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        # 簡易テキスト抽出（HTMLタグ除去）
        import re
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:4000]
    except Exception as e:
        print(f"[URLフェッチエラー] {e}")
        return ""


# ============================================================
# Step 3: スクリーニング判定
# ============================================================

def check_exclusions(report_text: str, score_result: dict) -> list[str]:
    """除外条件チェック（該当する除外理由のリスト）"""
    exclusions = []
    score = score_result.get("score", 100)
    risk  = score_result.get("highest_risk_item", "").lower()

    keywords_fraud = ["sec investigation", "sec subpoena", "doj", "department of justice",
                      "securities fraud", "accounting fraud", "financial fraud"]
    for kw in keywords_fraud:
        if kw in report_text.lower():
            exclusions.append(f"除外: 調査機関関与の可能性（'{kw}'）")
            break

    if "詐欺" in risk or "fraud" in risk or "forgery" in risk:
        exclusions.append("除外: 経営陣詐欺告発（highest_risk_itemより）")

    return exclusions


def run_screening(ticker: str, report_text: str, cfg: dict, state: dict,
                  dry_run: bool = False) -> dict:
    """メインスクリーニングロジック。判定結果dictを返す"""

    result = {
        "ticker":      ticker,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "action":      None,   # "ENTRY" / "SKIP" / "WAIT"
        "skip_reasons": [],
        "price_data":  None,
        "score_result": None,
    }

    # --- 状態チェック ---
    if state.get("open_position"):
        result["action"] = "WAIT"
        result["skip_reasons"].append(f"保有中のポジションあり: {state['open_position']['ticker']}")
        return result

    banned = state.get("banned_tickers", {})
    if ticker in banned:
        ban_until = datetime.fromisoformat(banned[ticker])
        if datetime.now(timezone.utc) < ban_until:
            result["action"] = "SKIP"
            result["skip_reasons"].append(f"再エントリー禁止期間中（{banned[ticker]}まで）")
            return result

    if state.get("skip_next"):
        result["action"] = "SKIP"
        result["skip_reasons"].append("連続損失後のクールダウン（1回スキップ）")
        return result

    # --- 株価データ取得 ---
    price_data = get_price_data(ticker)
    if not price_data:
        result["action"] = "SKIP"
        result["skip_reasons"].append("株価データ取得失敗")
        return result
    result["price_data"] = price_data

    # --- インパクトスコア算出 ---
    score_result = score_report(report_text)
    result["score_result"] = score_result
    score = score_result.get("score", 100)

    # --- 除外条件チェック ---
    exclusions = check_exclusions(report_text, score_result)
    if exclusions:
        result["action"] = "SKIP"
        result["skip_reasons"].extend(exclusions)
        return result

    # --- 決算前チェック ---
    no_entry_days = cfg["position"]["no_entry_before_earnings_days"]
    if price_data.get("earnings_date"):
        try:
            ed = datetime.fromisoformat(str(price_data["earnings_date"]).split("+")[0])
            days_to_earnings = (ed - datetime.now()).days
            if 0 <= days_to_earnings <= no_entry_days:
                result["action"] = "SKIP"
                result["skip_reasons"].append(
                    f"決算{days_to_earnings}日前（{no_entry_days}日以内は禁止）")
                return result
        except Exception:
            pass

    # --- エントリー5条件チェック ---
    fails = []
    e = cfg["entry"]

    if score >= e["impact_score_threshold"]:
        fails.append(f"インパクトスコア {score} ≥ {e['impact_score_threshold']}（告発が深刻）")

    if price_data["analysts"] < e["min_analysts"]:
        fails.append(f"アナリスト数 {price_data['analysts']} < {e['min_analysts']}")

    if price_data["inst_ownership"] < e["min_inst_ownership_pct"]:
        fails.append(f"機関保有 {price_data['inst_ownership']}% < {e['min_inst_ownership_pct']}%")

    if price_data["drop_from_high"] > -e["min_drop_from_20d_high_pct"]:
        fails.append(
            f"20日高値からの下落 {price_data['drop_from_high']}% が不足（>{-e['min_drop_from_20d_high_pct']}%必要）")

    if not price_data["bull_market"]:
        fails.append("S&P500が200日MAを下回っている（弱気相場）")

    if fails:
        result["action"] = "SKIP"
        result["skip_reasons"].extend(fails)
    else:
        result["action"] = "ENTRY"

    return result


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="ショートレポート逆張りスクリーナー")
    parser.add_argument("--ticker",       required=True, help="対象ティッカー（例: ACME）")
    parser.add_argument("--report-url",   default="",   help="レポートのURL")
    parser.add_argument("--report-text",  default="",   help="レポート本文（直接入力）")
    parser.add_argument("--score",        type=int,     help="インパクトスコアを手動指定（0-100）")
    parser.add_argument("--dry-run",      action="store_true", help="テスト実行（通知・状態更新なし）")
    args = parser.parse_args()

    cfg   = load_config()
    state = load_state()

    ticker = args.ticker.upper()

    # レポートテキスト準備
    report_text = args.report_text
    if not report_text and args.report_url:
        print(f"[URL取得] {args.report_url}")
        report_text = fetch_report_text(args.report_url)
    if not report_text:
        print("[入力待ち] レポートの要約または本文を入力してください（空行2回で確定）:")
        lines = []
        blank = 0
        while blank < 2:
            line = input()
            if line == "":
                blank += 1
            else:
                blank = 0
                lines.append(line)
        report_text = "\n".join(lines)

    # スコア手動指定
    if args.score is not None:
        original_score_report = score_report
        def mock_score(text):
            return {"score": args.score, "reason": "手動指定", "highest_risk_item": "手動指定"}
        import builtins
        globals()["score_report"] = mock_score

    # スクリーニング実行
    result = run_screening(ticker, report_text, cfg, state, dry_run=args.dry_run)

    # 結果表示
    print("\n" + "="*60)
    print(f"スクリーニング結果: {ticker}")
    print("="*60)

    pd = result.get("price_data")
    sr = result.get("score_result")

    if pd:
        print(f"  現在値         : ${pd['current_price']}")
        print(f"  20日高値比     : {pd['drop_from_high']}%")
        print(f"  アナリスト数   : {pd['analysts']}人")
        print(f"  機関保有比率   : {pd['inst_ownership']}%")
        print(f"  市場環境       : {'強気 (Bull)' if pd['bull_market'] else '弱気 (Bear)'}")
        print(f"  決算日         : {pd.get('earnings_date', '不明')}")

    if sr:
        print(f"  インパクトスコア: {sr['score']}")
        print(f"  採点理由       : {sr['reason']}")
        print(f"  最大リスク     : {sr['highest_risk_item']}")

    print(f"\n  判定: {result['action']}")
    if result["skip_reasons"]:
        for r in result["skip_reasons"]:
            print(f"    - {r}")

    # 通知
    if not args.dry_run:
        from notify import send_signal
        send_signal(result, cfg)

        # 状態更新（ENTRYの場合のみ）
        if result["action"] == "ENTRY":
            state["open_position"] = {
                "ticker":      ticker,
                "entry_date":  datetime.now(timezone.utc).date().isoformat(),
                "entry_price": pd["current_price"] if pd else None,
            }
            save_state(state)
            print("\n✅ エントリー候補をDiscordに通知しました。Moomooで手動発注してください。")
        else:
            print(f"\n⏭ スキップ。Discordに通知しました。")
    else:
        print("\n[DRY RUN] 通知・状態更新はスキップされました。")


if __name__ == "__main__":
    main()
