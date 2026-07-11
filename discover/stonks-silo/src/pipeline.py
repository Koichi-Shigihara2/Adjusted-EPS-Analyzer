# discover/stonks-silo/src/pipeline.py
"""
Stonks Silo Pipeline
config/cik_lookup.csv の stonks_silo=true 銘柄を一括処理して results.json に保存する。

出力先: docs/value-monitor/stonks-silo/data/results.json  (GitHub Pages 公開パス)

使い方:
  python discover/stonks-silo/src/pipeline.py          # stonks_silo=true 全件
  python discover/stonks-silo/src/pipeline.py SOUN BBAI  # 指定ティッカーのみ
"""

import dataclasses
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parents[2]
sys.path.insert(0, str(_SRC_DIR))
sys.path.insert(0, str(_REPO_ROOT))

from fetcher import load_annual_data
from analyzer import StonksAnalyzer
from valuation_fetcher import fetch_valuation
from financial_trend_calculator import compute_vectors, load_all_normalized
from common.sec_data import tickers


_OUTPUT_DIR = _REPO_ROOT / "docs" / "value-monitor" / "stonks-silo" / "data"
_OUTPUT_FILE = _OUTPUT_DIR / "results.json"
_YEARS = 5


# ---------------------------------------------------------------------------
# ティッカー取得
# ---------------------------------------------------------------------------

def stonks_tickers() -> list[str]:
    """cik_lookup.csv から stonks_silo=true の銘柄を返す"""
    return tickers.get_stonks_silo_tickers()


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

            val = fetch_valuation(ticker)
            latest_rev = None
            for yr in reversed(data["years"]):
                r = data["records"][yr]["pl"].get("revenue_sanitized")
                if r:
                    latest_rev = r
                    break

            psr = val["market_cap"] / latest_rev if val["market_cap"] and latest_rev else None
            ev_sales = val["enterprise_value"] / latest_rev if val["enterprise_value"] and latest_rev else None

            latest_bs = data["records"][data["years"][-1]]["bs"]
            cash = (latest_bs.get("cash_and_equivalents") or 0) + (latest_bs.get("short_term_investments") or 0)
            total_debt = val["total_debt"] or 0
            net_cash = cash - total_debt if (latest_bs.get("cash_and_equivalents") is not None) else None

            result["valuation"] = {
                "market_cap":       val["market_cap"],
                "current_price":    val["current_price"],
                "enterprise_value": val["enterprise_value"],
                "total_debt":       val["total_debt"],
                "psr":              round(psr, 1) if psr else None,
                "ev_sales":         round(ev_sales, 1) if ev_sales else None,
                "net_cash":         net_cash,
                "fetched_at":       val["fetched_at"],
                "error":            val["error"],
            }

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

    # 財務ベクトル計算（全銘柄のパーセンタイルを一括計算）
    try:
        all_normalized = load_all_normalized(list(results.keys()))
        vectors = compute_vectors(all_normalized)
        for ticker, vec in vectors.items():
            if ticker in results:
                results[ticker]["financial_vectors"] = vec
        print(f"財務ベクトル計算完了: {len(vectors)} 銘柄")
    except Exception as e:
        print(f"財務ベクトル計算エラー: {e}")
        import traceback
        traceback.print_exc()

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
