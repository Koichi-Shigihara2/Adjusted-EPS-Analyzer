"""
common/sec_data/ttm_calculator.py
責務: 直近4四半期を合算してTTM値を計算する
出力: ttm/{ticker}_ttm.json
"""

import json
import logging
import os
from datetime import date, datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
TTM_DIR = os.path.join(BASE_DIR, "ttm")

# フロー系フィールド（4Q合算）
FLOW_FIELDS = frozenset([
    "OCF", "ICF", "CFF", "CapEx", "FinanceLeasePmts", "SBC", "DA",
    "Revenue", "GrossProfit", "OperatingIncome", "NetIncome",
])

# ストック系フィールド（最新Q末の値）
STOCK_FIELDS = frozenset([
    "Cash", "STDebt", "LTDebt", "DeferredRevenue", "Equity",
])

# 株式数フィールド（最新Q末の値）
SHARES_FIELDS = frozenset([
    "SharesBasic", "SharesDiluted",
])

# TTMに含める当日以前の implied Q4 のみ
_TODAY = date.today().isoformat()


def calc_ttm(ticker: str, normalized: dict) -> dict:
    """
    直近4四半期の合算値を計算する。

    - フロー系（OCF/Revenue/NetIncome等）: Q合算
    - ストック系（Cash/Debt/Equity等）: 最新Q末の値
    - 株数（Shares）: 最新Q末の値
    - Q4は 10-K に単独データがないため implied Q4 を合算に含める
    """
    ticker = ticker.upper()
    fields = normalized.get("fields", {})

    # 各フィールドを四半期・年次に分離
    quarterly_by_field: dict[str, list] = {}
    annual_by_field: dict[str, list] = {}

    for field_name, entries in fields.items():
        quarterly_by_field[field_name] = sorted(
            [e for e in entries if not e.get("is_annual")],
            key=lambda x: x["end"],
            reverse=True,
        )
        annual_by_field[field_name] = sorted(
            [e for e in entries if e.get("is_annual")],
            key=lambda x: x["end"],
            reverse=True,
        )

    # Q4 implied 合成エントリを計算し、quarterly に追加
    q4_synthetic: dict[str, list] = {}  # field_name → [synthetic entry, ...]
    for field_name in FLOW_FIELDS:
        q4_list = _build_q4_quarterly_entries(
            annual_by_field.get(field_name, []),
            quarterly_by_field.get(field_name, []),
        )
        if q4_list:
            q4_synthetic[field_name] = q4_list
            merged = sorted(
                quarterly_by_field.get(field_name, []) + q4_list,
                key=lambda x: x["end"],
                reverse=True,
            )
            quarterly_by_field[field_name] = merged

    # TTM end date = 最新四半期 end_date
    ttm_end = _latest_end(quarterly_by_field)

    flow_result: dict = {}
    stock_result: dict = {}
    shares_result: dict = {}

    for field_name in FLOW_FIELDS:
        q_entries = quarterly_by_field.get(field_name, [])
        last4 = q_entries[:4]
        if not last4:
            continue
        total = sum(e["val"] for e in last4)
        flow_result[field_name] = {
            "val": total,
            "quarters_used": len(last4),
            "missing": max(0, 4 - len(last4)),
        }

    for field_name in STOCK_FIELDS:
        q_entries = quarterly_by_field.get(field_name, [])
        if not q_entries:
            continue
        latest = q_entries[0]
        stock_result[field_name] = {
            "val": latest["val"],
            "as_of": latest["end"],
        }

    for field_name in SHARES_FIELDS:
        q_entries = quarterly_by_field.get(field_name, [])
        if not q_entries:
            continue
        latest = q_entries[0]
        shares_result[field_name.replace("Shares", "")] = {
            "val": latest["val"],
            "as_of": latest["end"],
        }

    burn_rate = _calc_burn_rate(flow_result, stock_result)

    # q4_implied 出力: TTM に使われた Q4 implied エントリを表示
    q4_implied_output = _make_q4_implied_output(
        q4_synthetic, quarterly_by_field
    )

    logger.info("[%s] TTM calculated (end=%s)", ticker, ttm_end)
    return {
        "ticker": ticker,
        "ttm_end": ttm_end,
        "generated_at": datetime.now().isoformat(),
        "flow": flow_result,
        "stock": stock_result,
        "shares": shares_result,
        "burn_rate": burn_rate,
        "q4_implied": q4_implied_output,
    }


def _build_q4_quarterly_entries(
    annual_entries: list,
    quarterly_entries: list,
) -> list:
    """
    各FY年次エントリについて Q4 implied 合成エントリを生成する。

    Q4 = FY年次値 - (Q1+Q2+Q3)
    10-K は Q4 単独を報告しないため必要。
    """
    result: list = []
    for annual in annual_entries:
        fy_end = annual.get("end", "")
        fy_start = annual.get("start", "")
        fy_val = annual.get("val")

        if not fy_end or fy_val is None:
            continue
        # 未来のQ4は含めない（アナリスト予想にならないよう）
        if fy_end > _TODAY:
            continue

        # 同FY内の Q1/Q2/Q3
        fy_qs = [
            e for e in quarterly_entries
            if e.get("end", "") < fy_end
            and e.get("start", "") >= fy_start
            and not e.get("is_annual")
        ]
        top3 = sorted(fy_qs, key=lambda x: x["end"], reverse=True)[:3]
        if len(top3) < 3:
            continue

        q3_end = sorted(top3, key=lambda x: x["end"], reverse=True)[0]["end"]
        q4_val = fy_val - sum(e["val"] for e in top3)

        # period_days: FY_end - Q3_end
        try:
            period_days = (
                date.fromisoformat(fy_end) - date.fromisoformat(q3_end)
            ).days
        except (ValueError, TypeError):
            period_days = 90

        result.append({
            "end": fy_end,
            "start": q3_end,
            "val": q4_val,
            "fp": "Q4",
            "fy": annual.get("fy"),
            "form": "10-K",
            "filed": annual.get("filed", ""),
            "accn": annual.get("accn", ""),
            "period_days": period_days,
            "is_ytd": False,
            "is_annual": False,
            "is_implied": True,
        })

    return result


def _make_q4_implied_output(
    q4_synthetic: dict[str, list],
    quarterly_by_field: dict[str, list],
) -> dict:
    """TTM の直近4Q に含まれる implied Q4 エントリを q4_implied 出力形式に変換"""
    output: dict = {}
    for field_name, q4_list in q4_synthetic.items():
        last4_ends = {
            e["end"]
            for e in quarterly_by_field.get(field_name, [])[:4]
        }
        used = [e for e in q4_list if e["end"] in last4_ends]
        if not used:
            continue
        latest = max(used, key=lambda x: x["end"])
        output[field_name] = {
            "val": latest["val"],
            "fy": str(latest.get("fy") or latest["end"][:4]),
            "is_implied": True,
        }
    return output


def _latest_end(quarterly_by_field: dict[str, list]) -> str | None:
    """全フィールド中で最新の四半期 end_date を返す"""
    latest = None
    for entries in quarterly_by_field.values():
        if entries and (latest is None or entries[0]["end"] > latest):
            latest = entries[0]["end"]
    return latest


def _calc_burn_rate(flow: dict, stock: dict) -> dict | None:
    """
    バーンレート計算（赤字企業向け）。

    burn_rate_quarterly = -OCF_TTM / 4
    cash_runway_quarters = Cash / burn_rate_quarterly
    OCF_TTM >= 0 の場合は None を返す
    """
    ocf_info = flow.get("OCF")
    cash_info = stock.get("Cash")

    if ocf_info is None:
        return None

    ocf_ttm = ocf_info["val"]
    if ocf_ttm >= 0:
        return None

    burn_rate_quarterly = -ocf_ttm / 4
    result: dict = {"burn_rate_quarterly": burn_rate_quarterly}

    if cash_info and burn_rate_quarterly > 0:
        result["cash_runway_quarters"] = cash_info["val"] / burn_rate_quarterly

    return result


def _calc_q4_implied(
    ticker: str,
    annual: dict,
    normalized: dict,
) -> dict:
    """
    Q4逆算: FY年次値 - (Q1+Q2+Q3合計) でQ4を推定。
    SEC 10-K はQ4単独を報告しないため必要。
    戻り値に "is_implied": True フラグを付ける。
    """
    fields = normalized.get("fields", {})
    implied: dict = {}

    for field_name in FLOW_FIELDS:
        a_entries = sorted(
            [e for e in fields.get(field_name, []) if e.get("is_annual")],
            key=lambda x: x["end"],
            reverse=True,
        )
        q_entries = sorted(
            [e for e in fields.get(field_name, []) if not e.get("is_annual")],
            key=lambda x: x["end"],
            reverse=True,
        )
        if not a_entries or not q_entries:
            continue

        annual_entry = a_entries[0]
        fy_end = annual_entry["end"]
        fy_start = annual_entry.get("start", "")
        fy_val = annual_entry["val"]

        fy_qs = [
            e for e in q_entries
            if e["end"] < fy_end and e.get("start", "") >= fy_start
        ]
        top3 = sorted(fy_qs, key=lambda x: x["end"], reverse=True)[:3]
        if len(top3) < 3:
            continue

        q4_val = fy_val - sum(e["val"] for e in top3)
        fy_year = annual_entry.get("fy") or fy_end[:4]

        implied[field_name] = {
            "val": q4_val,
            "fy": str(fy_year),
            "is_implied": True,
        }

    return implied


def save_ttm(ticker: str, ttm: dict) -> str:
    """TTMデータをJSONファイルに保存し、パスを返す"""
    os.makedirs(TTM_DIR, exist_ok=True)
    path = os.path.join(TTM_DIR, f"{ticker.upper()}_ttm.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ttm, f, ensure_ascii=False, indent=2)
    logger.info("[%s] TTM saved -> %s", ticker, path)
    return path
