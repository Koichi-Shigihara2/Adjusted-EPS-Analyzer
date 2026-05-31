"""
common/sec_data/audit.py
SECデータ品質監査スクリプト

使用方法:
    python common/sec_data/audit.py              # 全銘柄監査
    python common/sec_data/audit.py AVGO BKNG   # 特定銘柄のみ

終了コード:
    0 = 問題なし または 軽微な問題のみ
    1 = 重大問題あり（NI/OCF 全件 None）

Discord通知:
    環境変数 DISCORD_WEB_HOOK が設定されている場合に自動送信
"""

import json
import os
import sys
import glob
from datetime import datetime


TTM_DIR  = os.path.join(os.path.dirname(__file__), "ttm")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs",
                        "value-monitor", "tanuki_valuation", "data")


def get_registered_tickers() -> list[str]:
    path = os.path.join(DATA_DIR, "tickers.json")
    if not os.path.exists(path):
        return []
    return json.load(open(path, encoding="utf-8")).get("tickers", [])


def audit_ticker(ticker: str) -> dict:
    """1銘柄の監査。返り値: {ticker, critical: [], warning: []}"""
    result = {"ticker": ticker, "critical": [], "warning": []}

    ttm_path = os.path.join(TTM_DIR, f"{ticker}_ttm_series.json")
    if not os.path.exists(ttm_path):
        result["critical"].append("TTMファイルなし")
        return result

    series = json.load(open(ttm_path, encoding="utf-8"))
    if isinstance(series, dict):
        series = series.get("series", series.get("ttm_series", []))

    if not series:
        result["critical"].append("TTMエントリ0件")
        return result

    n = len(series)
    ni_none  = sum(1 for s in series if s.get("flow", {}).get("NetIncome", {}).get("val") is None)
    ocf_none = sum(1 for s in series if s.get("flow", {}).get("OCF",       {}).get("val") is None)
    rev_none = sum(1 for s in series if s.get("flow", {}).get("Revenue",   {}).get("val") is None)

    # 重大: 計算の根幹となるフィールドが全件 None
    if ni_none == n:
        result["critical"].append(f"NI全件None({n}件) → Q計算不可・RICE誤分類リスク")
    elif ni_none > 0:
        result["warning"].append(f"NI一部None({ni_none}/{n}件)")

    if ocf_none == n:
        result["critical"].append(f"OCF全件None({n}件) → Q計算不可")
    elif ocf_none > 0:
        result["warning"].append(f"OCF一部None({ocf_none}/{n}件)")

    # 警告: Revenue 欠損（1件程度は許容、全件は重大）
    if rev_none == n:
        result["critical"].append(f"Revenue全件None({n}件)")
    elif rev_none > 0:
        result["warning"].append(f"Revenue一部None({rev_none}/{n}件)")

    # TTMエントリ数が少ない
    if n < 3:
        result["warning"].append(f"TTMエントリ{n}件（3件未満・上場間もない可能性）")

    return result


def run_audit(tickers: list[str]) -> tuple[list[dict], list[dict]]:
    """監査実行。(critical_list, warning_list) を返す"""
    critical_tickers = []
    warning_tickers  = []

    for ticker in tickers:
        r = audit_ticker(ticker)
        if r["critical"]:
            critical_tickers.append(r)
        elif r["warning"]:
            warning_tickers.append(r)

    return critical_tickers, warning_tickers


def build_discord_message(
    tickers: list[str],
    critical: list[dict],
    warning: list[dict],
    run_date: str,
) -> str:
    total = len(tickers)
    ok    = total - len(critical) - len(warning)

    if not critical and not warning:
        return (
            f"✅ **SECデータ品質監査 完了** `{run_date}`\n"
            f"全{total}銘柄: 問題なし"
        )

    lines = [f"{'🔴' if critical else '🟡'} **SECデータ品質監査** `{run_date}`"]
    lines.append(f"対象: {total}銘柄  🟢正常: {ok}  🟡警告: {len(warning)}  🔴重大: {len(critical)}")
    lines.append("")

    if critical:
        lines.append("**🔴 重大問題（要対処）**")
        for r in critical:
            for msg in r["critical"]:
                lines.append(f"　`{r['ticker']}`: {msg}")
        lines.append("")
        tickers_str = " ".join(r["ticker"] for r in critical)
        lines.append(f"```")
        lines.append(f"python common/sec_data/update.py {tickers_str}")
        lines.append(f"python src/value/tanuki_valuation/pipeline.py {tickers_str}")
        lines.append(f"```")

    if warning:
        lines.append("**🟡 警告（軽微・要確認）**")
        for r in warning:
            for msg in r["warning"]:
                lines.append(f"　`{r['ticker']}`: {msg}")

    return "\n".join(lines)


def post_discord(message: str) -> bool:
    webhook = os.environ.get("DISCORD_WEB_HOOK", "")
    if not webhook:
        return False
    try:
        import urllib.request
        payload = json.dumps({"content": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"Discord送信エラー: {e}", file=sys.stderr)
        return False


def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else get_registered_tickers()
    if not tickers:
        print("監査対象銘柄が見つかりません。tickers.json を確認してください。")
        sys.exit(1)

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"=== SECデータ品質監査 {run_date} ===")
    print(f"対象: {len(tickers)}銘柄")
    print()

    critical, warning = run_audit(tickers)
    ok_count = len(tickers) - len(critical) - len(warning)

    print(f"🟢 正常: {ok_count}銘柄")
    if warning:
        print(f"🟡 警告: {len(warning)}銘柄")
        for r in warning:
            for msg in r["warning"]:
                print(f"   {r['ticker']:6s}: {msg}")
    if critical:
        print(f"🔴 重大: {len(critical)}銘柄")
        for r in critical:
            for msg in r["critical"]:
                print(f"   {r['ticker']:6s}: {msg}")

    # Discord通知
    message = build_discord_message(tickers, critical, warning, run_date)
    if post_discord(message):
        print("\nDiscord通知: 送信完了")

    # GitHub Actions サマリー出力
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("## SECデータ品質監査\n\n")
            status = "🔴 重大問題あり" if critical else ("🟡 警告あり" if warning else "🟢 問題なし")
            f.write(f"**{status}** — 対象: {len(tickers)}銘柄  正常: {ok_count}  警告: {len(warning)}  重大: {len(critical)}\n\n")
            if critical:
                f.write("### 🔴 重大問題\n")
                for r in critical:
                    f.write(f"- `{r['ticker']}`: {', '.join(r['critical'])}\n")
                f.write("\n")
            if warning:
                f.write("### 🟡 警告\n")
                for r in warning:
                    f.write(f"- `{r['ticker']}`: {', '.join(r['warning'])}\n")

    # 重大問題があれば exit 1
    if critical:
        print("\n重大問題あり → exit 1")
        sys.exit(1)


if __name__ == "__main__":
    main()
