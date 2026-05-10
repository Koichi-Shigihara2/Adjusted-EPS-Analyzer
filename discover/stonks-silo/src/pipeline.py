# discover/stonks-silo/src/pipeline.py
"""
Stonks Silo Pipeline
config/cik_lookup.csv の stonks_silo=true 銘柄を一括処理して results.json に保存する。

出力先: docs/value-monitor/stonks-silo/data/results.json  (GitHub Pages 公開パス)

使い方:
  python discover/stonks-silo/src/pipeline.py          # stonks_silo=true 全件
  python discover/stonks-silo/src/pipeline.py SOUN BBAI  # 指定ティッカーのみ
"""

import csv
import dataclasses
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parents[2]
sys.path.insert(0, str(_SRC_DIR))

from fetcher import load_annual_data
from analyzer import StonksAnalyzer
from valuation_fetcher import fetch_valuation


_CIK_LOOKUP = _REPO_ROOT / "config" / "cik_lookup.csv"
_OUTPUT_DIR = _REPO_ROOT / "docs" / "value-monitor" / "stonks-silo" / "data"
_OUTPUT_FILE = _OUTPUT_DIR / "results.json"
_YEARS = 5


# ---------------------------------------------------------------------------
# ティッカー取得
# ---------------------------------------------------------------------------

def stonks_tickers() -> list[str]:
    """cik_lookup.csv から stonks_silo=true の銘柄を返す"""
    if not _CIK_LOOKUP.exists():
        raise FileNotFoundError(f"cik_lookup.csv not found: {_CIK_LOOKUP}")

    tickers = []
    with open(_CIK_LOOKUP, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("stonks_silo", "").strip().lower() == "true":
                tickers.append(row["ticker"].strip().upper())
    return sorted(tickers)


# ---------------------------------------------------------------------------
# シリアライズ
# ---------------------------------------------------------------------------

def _to_dict(obj) -> object:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_dict(v) for v in obj]
    if isinstance(obj, float):
        if obj == float("inf") or obj != obj:
            return None
        return obj
    return obj


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def run(tickers: list[str] | None = None) -> dict:
    """
    tickers=None のとき stonks_tickers() で stonks_silo=true 全件処理。
    特定ティッカー指定時は既存 results.json とマージする。
    """
    partial = tickers is not None
    target = [t.upper() for t in tickers] if partial else stonks_tickers()

    if not target:
        print("対象ティッカーが見つかりません。cik_lookup.csv の stonks_silo 列を確認してください。")
        return {}

    print(f"対象: {len(target)} 銘柄  {target}")

    analyzer = StonksAnalyzer()
    results = {}
    errors = {}

    for ticker in target:
        try:
            data = load_annual_data(ticker, years=_YEARS)
            analysis = analyzer.analyze(data)
            result = _to_dict(analysis)
            result["records"] = {
                str(yr): {
                    "revenue":    _to_dict(rec["pl"].get("revenue")),
                    "net_income": _to_dict(rec["pl"].get("net_income")),
                }
                for yr, rec in data["records"].items()
            }

            # バリュエーション取得・計算
            val = fetch_valuation(ticker)
            latest_yr = data["years"][-1]
            latest_rev_san = data["records"][latest_yr]["pl"].get("revenue_sanitized")
            latest_cash    = data["records"][latest_yr]["bs"].get("cash_and_equivalents")
            latest_sti     = data["records"][latest_yr]["bs"].get("short_term_investments")
            cash_total     = (latest_cash or 0) + (latest_sti or 0) or None

            psr      = None
            ev_sales = None
            net_cash = None

            if latest_rev_san and latest_rev_san > 0:
                if val["market_cap"] is not None:
                    psr = round(val["market_cap"] / latest_rev_san, 2)
                if val["enterprise_value"] is not None:
                    ev_sales = round(val["enterprise_value"] / latest_rev_san, 2)

            if cash_total is not None and val["total_debt"] is not None:
                net_cash = cash_total - val["total_debt"]
            elif cash_total is not None:
                net_cash = cash_total  # 無借金

            val["psr"]      = psr
            val["ev_sales"] = ev_sales
            val["net_cash"] = net_cash
            result["valuation"] = val

            results[ticker] = result
            print(f"  [{ticker}] {analysis.overall_verdict} (score={analysis.overall_score})")
        except FileNotFoundError:
            errors[ticker] = "annual_*.json not found"
            print(f"  [{ticker}] SKIP — データなし")
        except Exception as e:
            errors[ticker] = str(e)
            print(f"  [{ticker}] ERROR — {e}")

    # 特定ティッカー指定時は既存データとマージ（全件消去を防ぐ）
    if partial and _OUTPUT_FILE.exists():
        try:
            with open(_OUTPUT_FILE, encoding="utf-8") as f:
                existing = json.load(f)
            merged = existing.get("tickers", {})
            merged_errors = existing.get("errors", {})
            merged.update(results)
            merged_errors.update(errors)
            results = merged
            errors = merged_errors
        except Exception:
            pass

    # stonks_silo=true の銘柄のみ残す（削除・false変更に追従）
    valid = set(stonks_tickers())
    results = {k: v for k, v in results.items() if k in valid}
    errors  = {k: v for k, v in errors.items()  if k in valid}

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ticker_count": len(results),
        "tickers": results,
        "errors": errors,
    }

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n保存完了: {_OUTPUT_FILE}")
    print(f"成功={len(results)}  スキップ/エラー={len(errors)}")
    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tickers = sys.argv[1:] if len(sys.argv) > 1 else None
    run(tickers)
