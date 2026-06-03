"""
common/system_health.py
全システム健全性チェック + 毎朝Discord通知

使用方法:
    python common/system_health.py         # 全チェック実行
    python common/system_health.py --quiet # Discord通知のみ（コンソール省略）

終了コード:
    0 = HEALTHY（問題なし）
    1 = WARNING（軽微な問題あり）
    2 = CRITICAL（重大問題あり）
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from typing import Optional

# repo root を sys.path に追加（common/ から見て1段上）
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from common.sec_data.audit import (
    audit_beta_drift,
    get_registered_tickers,
    post_discord,
    run_audit,
)

_TANUKI_DATA = os.path.join(_REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "data")
_DOCS_ROOT   = os.path.join(_REPO_ROOT, "docs")
_SS_RESULTS  = os.path.join(_DOCS_ROOT, "value-monitor", "stonks-silo", "data", "results.json")

_STALE_DAYS  = 7   # この日数以上古いデータを「stale」と判定


# ── git log でファイルの最終コミット日時を取得 ──────────────────────
def _git_last_commit_date(rel_path: str) -> Optional[date]:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci", "--", rel_path],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=10,
        )
        line = result.stdout.strip()
        if not line:
            return None
        return datetime.fromisoformat(line[:19]).date()
    except Exception:
        return None


# ── A. SEC データ健全性 ──────────────────────────────────────────────
def check_a_sec(tickers: list[str]) -> tuple[str, bool, str]:
    critical, warning = run_audit(tickers)
    n_crit   = len(critical)
    n_warn   = len(warning)
    ok       = n_crit == 0
    icon     = "✅" if ok else "⚠️ " if n_warn and not n_crit else "🔴"
    detail   = f"警告{n_warn}件 / 重大{n_crit}件"
    label    = f"{icon} {detail}"
    return label, ok, detail


# ── B. score_history.json 整合性 ─────────────────────────────────────
def check_b_score_history(tickers: list[str]) -> tuple[str, bool, str]:
    missing, stale = [], []
    today = date.today()
    for t in tickers:
        sh_path = os.path.join(_TANUKI_DATA, t, "score_history.json")
        if not os.path.exists(sh_path):
            missing.append(t)
            continue
        try:
            entries = json.load(open(sh_path, encoding="utf-8"))
        except Exception:
            missing.append(t)
            continue
        if not entries:
            stale.append(t)
            continue
        latest = max(e.get("date", "2000-01-01") for e in entries)
        if (today - date.fromisoformat(latest)).days > _STALE_DAYS:
            stale.append(t)

    total  = len(tickers)
    n_miss = len(missing)
    n_stale= len(stale)
    ok     = n_miss == 0 and n_stale == 0
    icon   = "✅" if ok else "⚠️ "
    detail = f"{total - n_miss}/{total}件存在 / 古いデータ{n_stale}件"
    if missing:
        detail += f" (未作成: {', '.join(missing[:5])}{'…' if len(missing) > 5 else ''})"
    return f"{icon} {detail}", ok, detail


# ── C. latest.json 必須フィールド欠損 ───────────────────────────────
def check_c_latest(tickers: list[str]) -> tuple[str, bool, str]:
    broken = []
    for t in tickers:
        lp = os.path.join(_TANUKI_DATA, t, "latest.json")
        if not os.path.exists(lp):
            broken.append(t)
            continue
        try:
            d = json.load(open(lp, encoding="utf-8"))
        except Exception:
            broken.append(t)
            continue
        price = (d.get("components") or {}).get("current_price")
        if (d.get("tanuki_score") is None
                or d.get("upside_percent") is None
                or price is None):
            broken.append(t)

    n   = len(broken)
    ok  = n == 0
    icon = "✅" if ok else "⚠️ "
    detail = f"欠損{n}件" + (f"（{', '.join(broken[:5])}{'…' if n > 5 else ''}）" if broken else "")
    return f"{icon} {detail}", ok, detail


# ── D. ワークフロー出力データの鮮度チェック ─────────────────────────
def check_d_actions() -> tuple[str, bool, str]:
    # ワークフロー別にチェックするデータ出力ファイル（repo_root基準の相対パス）
    checks = [
        ("MarketPulse", "docs/market-monitor/market-pulse/data/market_data.json"),
        ("TANUKI",      "docs/value-monitor/tanuki_valuation/data/tickers.json"),
        ("StonksSilo",  "docs/value-monitor/stonks-silo/data/results.json"),
        ("MacroPulse",  "docs/market-monitor/macro-pulse/data/fed_context.csv"),
    ]
    stale = []
    today = date.today()
    for name, rel_path in checks:
        last = _git_last_commit_date(rel_path)
        if last is None:
            continue
        if (today - last).days > _STALE_DAYS:
            stale.append(f"{name}({(today - last).days}日)")

    ok     = len(stale) == 0
    icon   = "✅" if ok else "⚠️ "
    detail = "全ワークフロー正常" if ok else f"7日超 {len(stale)}件: {', '.join(stale)}"
    return f"{icon} {detail}", ok, detail


# ── E. Stonks Silo 健全性 ────────────────────────────────────────────
def check_e_silo() -> tuple[str, bool, str]:
    if not os.path.exists(_SS_RESULTS):
        return "⚠️  results.json未作成", False, "results.json未作成"
    try:
        data = json.load(open(_SS_RESULTS, encoding="utf-8"))
    except Exception as e:
        return f"🔴 読み込みエラー: {e}", False, str(e)

    ss_date  = (data.get("generated_at") or "")[:10]
    tickers  = data.get("tickers") or {}
    null_ue  = sum(
        1 for td in tickers.values()
        if (td.get("deficit_quality") or {}).get("unit_economics_score") is None
    )
    ok      = True
    icon    = "✅"
    detail  = f"更新{ss_date or '不明'} / UEスコアnull {null_ue}件"
    return f"{icon} {detail}", ok, detail


# ── Discord 1行サマリー ───────────────────────────────────────────────
def build_one_line(run_date: str, results: dict) -> str:
    overall_ok = all(r["ok"] for r in results.values())
    globe      = "🟢" if overall_ok else "🔴"
    status     = "HEALTHY" if overall_ok else "WARNING"
    parts = []
    labels = {"A": "SEC", "B": "Score", "C": "Latest", "D": "Actions", "E": "Silo"}
    for key, label in labels.items():
        r = results.get(key, {})
        icon = "✅" if r.get("ok") else "⚠️"
        extra = f"{r.get('short','')}" if not r.get("ok") else ""
        parts.append(f"{label}{icon}{extra}")

    return f"{globe} System Health {run_date}: {status} | {' '.join(parts)}"


# ── メイン ───────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="全システム健全性チェック")
    parser.add_argument("--quiet", action="store_true", help="コンソール出力を省略")
    args = parser.parse_args()

    today    = date.today().isoformat()
    tickers  = get_registered_tickers()

    if not args.quiet:
        print(f"\n=== System Health Check {today} ===")

    # 各チェック実行
    label_a, ok_a, det_a = check_a_sec(tickers)
    label_b, ok_b, det_b = check_b_score_history(tickers)
    label_c, ok_c, det_c = check_c_latest(tickers)
    label_d, ok_d, det_d = check_d_actions()
    label_e, ok_e, det_e = check_e_silo()

    results = {
        "A": {"ok": ok_a, "short": det_a.split("件")[0] + "件" if "件" in det_a else det_a[:10]},
        "B": {"ok": ok_b, "short": det_b.split("件")[0] + "件" if "件" in det_b else det_b[:10]},
        "C": {"ok": ok_c, "short": det_c.split("）")[0] + "）" if "）" in det_c else det_c[:10]},
        "D": {"ok": ok_d, "short": det_d[:20]},
        "E": {"ok": ok_e, "short": det_e[:20]},
    }

    overall_ok = all(r["ok"] for r in results.values())
    n_warn     = sum(1 for r in results.values() if not r["ok"])

    if not args.quiet:
        print(f"[A] SEC Data:      {label_a}")
        print(f"[B] ScoreHistory:  {label_b}")
        print(f"[C] Latest JSON:   {label_c}")
        print(f"[D] Actions:       {label_d}")
        print(f"[E] StonksSilo:    {label_e}")
        status_str = "✅ HEALTHY" if overall_ok else f"⚠️  WARNING（問題{n_warn}件）"
        print(f"Overall: {status_str}\n")

    # Discord 通知
    one_line = build_one_line(today, results)
    sent = post_discord(one_line)
    if not args.quiet:
        if sent:
            print("Discord通知: 送信完了")
        else:
            print("Discord通知: DISCORD_WEB_HOOK 未設定またはスキップ")

    if not overall_ok:
        return 2 if not ok_a else 1  # SEC critical → 2、それ以外 → 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
