# discover/stonks-silo/src/fetcher.py
"""
Stonks Silo Fetcher
annual_*.json から複数年データを読み込む専用フェッチャー。
TANUKIパイプラインとは独立して動作する。

データパス: common/sec_data/data/{TICKER}/annual_*.json
"""

import json
import re
from pathlib import Path
from typing import Optional


# リポジトリルートからの相対パス
# このファイルは discover/stonks-silo/src/ に置かれる想定
_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parents[2]  # discover/stonks-silo/src/ → 3階層上
_SEC_DATA_DIR = _REPO_ROOT / "common" / "sec_data" / "data"


def _parse_year(filename: str) -> Optional[int]:
    """annual_2022.json → 2022"""
    m = re.search(r"annual_(\d{4})\.json$", filename)
    return int(m.group(1)) if m else None


def load_annual_data(ticker: str, years: int = 5) -> dict:
    """
    指定ティッカーの annual_*.json を最新N年分読み込む。

    Returns
    -------
    {
        "ticker": "PLTR",
        "years": [2020, 2021, 2022, 2023, 2024],
        "records": {
            2020: { "pl": {...}, "cf": {...}, "bs": {...} },
            ...
        },
        "errors": []   # 読み込めなかった年・フィールドの記録
    }
    """
    ticker = ticker.upper()
    ticker_dir = _SEC_DATA_DIR / ticker

    if not ticker_dir.exists():
        raise FileNotFoundError(
            f"Ticker directory not found: {ticker_dir}\n"
            f"Available tickers: {_list_available_tickers()}"
        )

    # annual_*.json を列挙してソート
    annual_files = sorted(
        [(f, _parse_year(f.name)) for f in ticker_dir.glob("annual_*.json")
         if _parse_year(f.name) is not None],
        key=lambda x: x[1],
        reverse=True,
    )

    if not annual_files:
        raise FileNotFoundError(f"No annual_*.json found in {ticker_dir}")

    # 最新 N 年分を取得（古い順に並べ直す）
    selected = annual_files[:years][::-1]

    records = {}
    errors = []

    for path, year in selected:
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            records[year] = _normalize_record(raw, year, ticker, errors)
        except json.JSONDecodeError as e:
            errors.append({"year": year, "error": f"JSON parse error: {e}"})
        except Exception as e:
            errors.append({"year": year, "error": str(e)})

    return {
        "ticker": ticker,
        "years": sorted(records.keys()),
        "records": records,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# 内部ヘルパー
# ---------------------------------------------------------------------------

_PL_FIELDS = [
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "research_and_development",
    "selling_and_marketing",
    "selling_general_and_administrative",
]

_CF_FIELDS = [
    "operating_cash_flow",
    "capital_expenditure",
    "free_cash_flow",
    "stock_based_compensation",
    "depreciation_and_amortization",
]

_BS_FIELDS = [
    "cash_and_equivalents",
    "short_term_investments",
    "total_debt",
    "stockholders_equity",
    "shares_outstanding",
    "shares_diluted",
]


def _normalize_record(raw: dict, year: int, ticker: str, errors: list) -> dict:
    """
    annual_*.json の生データを Stonks Silo 標準形式に変換する。
    フィールドが存在しない場合は None を入れ、errors に記録する。
    """
    def _extract(section: str, fields: list) -> dict:
        section_data = raw.get(section, {})
        result = {}
        for f in fields:
            val = section_data.get(f)
            if val is None:
                errors.append({
                    "year": year,
                    "section": section,
                    "field": f,
                    "warning": "missing",
                })
            result[f] = val
        return result

    pl = _extract("pl", _PL_FIELDS)
    cf = _extract("cf", _CF_FIELDS)
    bs = _extract("bs", _BS_FIELDS)

    # free_cash_flow が欠損でも OCF + CapEx から補完
    if cf["free_cash_flow"] is None:
        ocf = cf["operating_cash_flow"]
        capex = cf["capital_expenditure"]
        if ocf is not None and capex is not None:
            # CapEx は通常マイナス値で格納されているが、符号が揃っていない場合も考慮
            cf["free_cash_flow"] = ocf - abs(capex)
            errors.append({
                "year": year,
                "section": "cf",
                "field": "free_cash_flow",
                "warning": "derived_from_ocf_capex",
            })

    # gross_profit が欠損の場合、revenue - cost 系タグから補完
    if pl["gross_profit"] is None:
        rev = pl.get("revenue")
        pl_raw = raw.get("pl", {})
        cost = (
            pl_raw.get("cost_of_revenue")
            or pl_raw.get("cost_of_goods_sold")
            or pl_raw.get("cost_of_goods_and_services_sold")
        )
        if rev is not None and cost is not None:
            pl["gross_profit"] = rev - cost
            pl["gross_profit_derived"] = True
            errors.append({
                "year": year,
                "section": "pl",
                "field": "gross_profit",
                "warning": "derived_from_revenue_minus_cost",
            })

    return {"pl": pl, "cf": cf, "bs": bs, "raw_year": year}


def _list_available_tickers() -> list[str]:
    if not _SEC_DATA_DIR.exists():
        return []
    return sorted(d.name for d in _SEC_DATA_DIR.iterdir() if d.is_dir())


def available_tickers() -> list[str]:
    """利用可能なティッカー一覧を返す"""
    return _list_available_tickers()


def _fmt(v) -> str:
    if v is None:
        return "N/A"
    if abs(v) >= 1e9:
        return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


# ---------------------------------------------------------------------------
# CLI 簡易テスト
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    ticker = sys.argv[1] if len(sys.argv) > 1 else "PLTR"
    try:
        data = load_annual_data(ticker, years=5)
        print(f"\n=== {data['ticker']} ({len(data['years'])} years) ===")
        print(f"Years: {data['years']}")
        for yr, rec in data["records"].items():
            rev = rec["pl"].get("revenue")
            ocf = rec["cf"].get("operating_cash_flow")
            cash = rec["bs"].get("cash_and_equivalents")
            print(
                f"  {yr}: Revenue={_fmt(rev)}  OCF={_fmt(ocf)}  Cash={_fmt(cash)}"
            )
        if data["errors"]:
            print(f"\nWarnings ({len(data['errors'])}):")
            for e in data["errors"][:10]:
                print(f"  {e}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
