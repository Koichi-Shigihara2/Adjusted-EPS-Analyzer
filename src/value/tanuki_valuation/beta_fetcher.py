"""
src/value/tanuki_valuation/beta_fetcher.py
β自動取得・beta_config.json 更新スクリプト

用途:
  - 新規銘柄登録時の β 初期設定
  - 既存銘柄の β 定期リフレッシュ
  - β 乖離の検出

使用方法:
    # 全銘柄リフレッシュ
    python beta_fetcher.py

    # 特定銘柄のみ
    python beta_fetcher.py NVDA AAPL META

    # ドライラン（config を書き換えずに差分だけ表示）
    python beta_fetcher.py --dry-run

ルール:
    - yfinance 5年βをベース
    - 上限 2.5 / 下限 0.3
    - source が "damodaran_*" の銘柄は上書きしない（手動設定を保護）
    - DISCORD_WEB_HOOK が設定されていれば大きな変化を通知
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT   = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "config" / "beta_config.json"
DATA_DIR    = REPO_ROOT / "docs" / "value-monitor" / "tanuki_valuation" / "data"

# common/ を import できるように repo root を sys.path に追加
_repo_str = str(REPO_ROOT)
if _repo_str not in sys.path:
    sys.path.insert(0, _repo_str)

try:
    from common.yfinance_utils import safe_yf_ticker as _safe_yf_ticker
    _USE_SAFE_YF = True
except ImportError:
    _USE_SAFE_YF = False

BETA_CAP    = 2.5
BETA_FLOOR  = 0.3
DRIFT_WARN  = 0.5   # この差分以上で「大きな乖離」と判定


# Damodaran業種別β（手動設定が必要な特例銘柄向け）
DAMODARAN_OVERRIDES: dict[str, tuple[float, str]] = {
    "LMT": (0.74, "damodaran_2025_aerospace_defense"),
    # 必要に応じて追加
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"overrides": {}}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    cfg["_updated_at"] = datetime.now().strftime("%Y-%m-%d")
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_registered_tickers() -> list[str]:
    path = DATA_DIR / "tickers.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("tickers", [])


def fetch_yfinance_beta(ticker: str) -> Optional[float]:
    """yfinance から5年βを取得する。失敗時は None を返す。リトライあり。"""
    if _USE_SAFE_YF:
        t = _safe_yf_ticker(ticker)
        if t is None:
            return None
        try:
            return t.info.get("beta")
        except Exception as e:
            print(f"  [{ticker}] yfinance info取得エラー: {e}", file=sys.stderr)
            return None
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        return info.get("beta")
    except Exception as e:
        print(f"  [{ticker}] yfinance 取得エラー: {e}", file=sys.stderr)
        return None


def calc_capped_beta(raw_beta: float, ticker: str) -> tuple[float, str]:
    """上限・下限を適用し (capped_beta, source_string) を返す。"""
    capped = max(BETA_FLOOR, min(BETA_CAP, raw_beta))
    src = "yfinance_5yr"
    if capped != round(raw_beta, 3):
        src += f"_capped_from_{round(raw_beta, 2)}"
    return round(capped, 3), src


def refresh_tickers(
    tickers: list[str],
    dry_run: bool = False,
) -> tuple[list[dict], list[dict]]:
    """
    指定銘柄のβを yfinance から取得して beta_config.json を更新する。

    Returns:
        (updated_list, skipped_list)
        updated_list: 変化した銘柄のログ
        skipped_list: スキップされた銘柄のログ
    """
    cfg      = load_config()
    overrides = cfg.setdefault("overrides", {})

    updated  = []
    skipped  = []

    for ticker in tickers:
        # Damodaran手動設定は上書きしない
        if ticker in DAMODARAN_OVERRIDES:
            b, src = DAMODARAN_OVERRIDES[ticker]
            cur = overrides.get(ticker, {})
            if cur.get("source", "").startswith("damodaran"):
                skipped.append({"ticker": ticker, "reason": "Damodaran手動設定を保護"})
                continue
            # 初回登録のみ Damodaran 値を適用
            if not dry_run:
                overrides[ticker] = {"beta": b, "source": src}
            updated.append({"ticker": ticker, "old": cur.get("beta"), "new": b, "source": src})
            continue

        yf_beta = fetch_yfinance_beta(ticker)
        if yf_beta is None:
            skipped.append({"ticker": ticker, "reason": "yfinance 取得失敗"})
            time.sleep(0.1)
            continue

        new_beta, src = calc_capped_beta(yf_beta, ticker)
        cur = overrides.get(ticker, {})
        old_beta = cur.get("beta")

        if old_beta is not None and abs(new_beta - old_beta) < 0.01:
            # 変化なし
            time.sleep(0.1)
            continue

        drift = f"{new_beta - old_beta:+.2f}" if old_beta is not None else "(新規)"
        updated.append({
            "ticker":  ticker,
            "old":     old_beta,
            "new":     new_beta,
            "drift":   drift,
            "source":  src,
            "warn":    old_beta is not None and abs(new_beta - old_beta) >= DRIFT_WARN,
        })

        if not dry_run:
            overrides[ticker] = {"beta": new_beta, "source": src}

        time.sleep(0.15)  # API rate limit

    if not dry_run and updated:
        save_config(cfg)

    return updated, skipped


def build_discord_message(
    updated: list[dict],
    skipped: list[dict],
    run_date: str,
    dry_run: bool,
) -> str:
    warn_items = [u for u in updated if u.get("warn")]
    if not updated and not warn_items:
        return (
            f"✅ **β設定リフレッシュ** `{run_date}`\n"
            f"変化なし（全銘柄βが安定）"
        )

    mode = "【DRY RUN】" if dry_run else ""
    lines = [
        f"⚡ **β設定リフレッシュ{mode}** `{run_date}` — {len(updated)}銘柄更新",
        "",
    ]
    if warn_items:
        lines.append("**⚠️ 大きな乖離あり（要確認）**")
        for u in warn_items:
            lines.append(f"　`{u['ticker']}`: {u['old']} → {u['new']} ({u['drift']})")
        lines.append("")
    if updated:
        lines.append("**更新一覧**")
        for u in updated:
            lines.append(f"　`{u['ticker']}`: {u.get('old','N/A')} → {u['new']} ({u.get('drift','新規')})")
    if skipped:
        lines.append(f"\nスキップ: {', '.join(s['ticker'] for s in skipped)}")

    return "\n".join(lines)


def post_discord(message: str) -> bool:
    webhook = os.environ.get("DISCORD_WEB_HOOK", "")
    if not webhook or not message:
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
    dry_run = "--dry-run" in sys.argv
    targets = [a for a in sys.argv[1:] if not a.startswith("--")]

    tickers = targets if targets else get_registered_tickers()
    if not tickers:
        print("対象銘柄が見つかりません")
        sys.exit(1)

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode_str = "【DRY RUN】" if dry_run else ""
    print(f"=== β設定リフレッシュ {mode_str}{run_date} ({len(tickers)}銘柄) ===")

    updated, skipped = refresh_tickers(tickers, dry_run=dry_run)

    warn_items = [u for u in updated if u.get("warn")]
    for u in updated:
        marker = "⚠️" if u.get("warn") else "  "
        print(f"  {marker} {u['ticker']:6s}: {str(u.get('old','N/A')):6s} → {u['new']:<6}  {u.get('drift','新規')}")
    for s in skipped:
        print(f"  スキップ {s['ticker']}: {s['reason']}")

    if not updated and not skipped:
        print("  変化なし")

    # Discord通知（大きな乖離があるか、新規登録の場合のみ）
    if warn_items or any(u.get("drift") == "(新規)" for u in updated):
        message = build_discord_message(updated, skipped, run_date, dry_run)
        if post_discord(message):
            print("Discord通知: 送信完了")

    # GitHub Actions サマリー
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path and updated:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("## β設定リフレッシュ\n\n")
            f.write(f"更新: {len(updated)}銘柄  スキップ: {len(skipped)}銘柄\n\n")
            if warn_items:
                f.write("### ⚠️ 大きな乖離\n")
                for u in warn_items:
                    f.write(f"- `{u['ticker']}`: {u.get('old')} → {u['new']} ({u.get('drift')})\n")


if __name__ == "__main__":
    main()
