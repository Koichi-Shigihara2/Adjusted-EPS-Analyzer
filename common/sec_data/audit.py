"""
common/sec_data/audit.py
SECデータ品質監査スクリプト

使用方法:
    python common/sec_data/audit.py              # 全銘柄監査（SECデータのみ）
    python common/sec_data/audit.py AVGO BKNG   # 特定銘柄のみ
    python common/sec_data/audit.py --check-beta # β乖離チェックも実施

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
EPS_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "docs",
                        "value-monitor", "adjusted_eps_analyzer", "data")


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

    # 株数乖離チェック: EPS quarterly.json の希薄化株数 vs latest.json の希薄化株数
    # 5倍超の乖離はデータソース不一致の疑い
    _q_path = os.path.join(EPS_DIR, ticker, "quarterly.json")
    _l_path  = os.path.join(DATA_DIR, ticker, "latest.json")
    if os.path.exists(_q_path) and os.path.exists(_l_path):
        try:
            _qdata = json.load(open(_q_path, encoding="utf-8"))
            _qs = _qdata if isinstance(_qdata, list) else _qdata.get("quarters", [])
            _recent_q = sorted(
                [q for q in _qs if (q.get("filing_date") or "") >= "2022-01-01"],
                key=lambda q: q.get("filing_date", ""),
            )
            if _recent_q:
                _eps_shares = _recent_q[-1].get("diluted_shares") or 0
                _ld = json.load(open(_l_path, encoding="utf-8"))
                _val_shares = (_ld.get("components") or {}).get("diluted_shares") or 0
                if _eps_shares > 1e6 and _val_shares > 1e6:
                    _ratio = max(_eps_shares, _val_shares) / min(_eps_shares, _val_shares)
                    if _ratio >= 5.0:
                        result["warning"].append(
                            f"株数乖離{_ratio:.1f}x: EPS={_eps_shares/1e6:.1f}M"
                            f" vs DCF={_val_shares/1e6:.1f}M → データソース不一致疑い"
                        )
        except Exception:
            pass

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


def audit_beta_drift(tickers: list[str]) -> list[dict]:
    """
    beta_config.json と yfinance の実測β値を比較し、
    乖離が大きい銘柄をリストアップする。

    yfinance が利用できない場合は空リストを返す（graceful skip）。
    """
    try:
        import yfinance as yf
        import time as _time
    except ImportError:
        print("  [beta] yfinance 未インストール → βチェックをスキップ")
        return []

    repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
    cfg_path  = os.path.join(repo_root, "config", "beta_config.json")
    if not os.path.exists(cfg_path):
        return []

    cfg       = json.load(open(cfg_path, encoding="utf-8"))
    overrides = cfg.get("overrides", {})
    DRIFT_THRESHOLD = 0.5  # この差分以上を「大きな乖離」と判定

    drift_list = []
    for ticker in tickers:
        try:
            info   = yf.Ticker(ticker).info
            yf_b   = info.get("beta")
            cfg_b  = overrides.get(ticker, {}).get("beta")
            src    = overrides.get(ticker, {}).get("source", "")

            if yf_b is None:
                continue
            if cfg_b is None:
                drift_list.append({
                    "ticker": ticker,
                    "cfg": None,
                    "yf":  round(yf_b, 3),
                    "diff": None,
                    "level": "critical",
                    "msg": f"beta_config未設定（yfinance={yf_b:.2f}）",
                })
                continue

            diff = abs(yf_b - cfg_b)
            if diff >= DRIFT_THRESHOLD:
                level = "critical" if diff >= 1.0 else "warning"
                drift_list.append({
                    "ticker": ticker,
                    "cfg":  cfg_b,
                    "yf":   round(yf_b, 3),
                    "diff": round(yf_b - cfg_b, 2),
                    "level": level,
                    "src":  src,
                    "msg":  f"β乖離 config={cfg_b} / yfinance={yf_b:.2f} (差{yf_b-cfg_b:+.2f})",
                })
            _time.sleep(0.12)
        except Exception:
            pass

    return drift_list


def main():
    check_beta = "--check-beta" in sys.argv
    args       = [a for a in sys.argv[1:] if not a.startswith("--")]
    tickers    = args if args else get_registered_tickers()
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

    # ── β乖離チェック（--check-beta 指定時）──
    beta_drift = []
    if check_beta:
        print("\n=== β乖離チェック ===")
        beta_drift = audit_beta_drift(tickers)
        beta_critical = [d for d in beta_drift if d["level"] == "critical"]
        beta_warning  = [d for d in beta_drift if d["level"] == "warning"]
        if not beta_drift:
            print("🟢 β乖離: 問題なし")
        else:
            if beta_critical:
                print(f"🔴 重大β乖離: {len(beta_critical)}銘柄")
                for d in beta_critical:
                    print(f"   {d['ticker']:6s}: {d['msg']}")
            if beta_warning:
                print(f"🟡 β警告: {len(beta_warning)}銘柄")
                for d in beta_warning:
                    print(f"   {d['ticker']:6s}: {d['msg']}")
        if beta_drift:
            print("\n対処方法:")
            print("  python src/value/tanuki_valuation/beta_fetcher.py --dry-run")
            print("  python src/value/tanuki_valuation/beta_fetcher.py")

    # Discord通知
    message = build_discord_message(tickers, critical, warning, run_date)

    # β乖離情報を Discord メッセージに追記
    if check_beta and beta_drift:
        beta_lines = ["\n**⚡ β乖離検知**"]
        for d in beta_drift[:8]:  # 最大8件
            icon = "🔴" if d["level"] == "critical" else "🟡"
            beta_lines.append(f"　{icon} `{d['ticker']}`: {d['msg']}")
        if len(beta_drift) > 8:
            beta_lines.append(f"　... 他{len(beta_drift)-8}銘柄")
        beta_lines.append("\n```\npython src/value/tanuki_valuation/beta_fetcher.py\n```")
        message = message + "\n" + "\n".join(beta_lines) if message else "\n".join(beta_lines)

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
            if check_beta and beta_drift:
                f.write("\n### ⚡ β乖離\n")
                for d in beta_drift:
                    icon = "🔴" if d["level"] == "critical" else "🟡"
                    f.write(f"- {icon} `{d['ticker']}`: {d['msg']}\n")

    # 重大問題があれば exit 1
    if critical:
        print("\n重大問題あり → exit 1")
        sys.exit(1)


if __name__ == "__main__":
    main()
