"""
common/sec_data/ttm_calculator.py
責務: 直近4四半期を合算してTTM値を計算する
出力: ttm/{ticker}_ttm.json
"""

import json
import logging
import os
from datetime import date, datetime

from .contracts import validate_field_classification
from .quarterly import FIELD_CONCEPTS

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
TTM_DIR = os.path.join(BASE_DIR, "ttm")

# フロー系フィールド（4Q合算）
FLOW_FIELDS = frozenset([
    "OCF", "ICF", "CFF", "CapEx", "FinanceLeasePmts", "SBC", "DA",
    "Revenue", "GrossProfit", "OperatingIncome", "NetIncome",
    "RD", "SM", "Buyback",
])

# ストック系フィールド（最新Q末の値）
# CurrentAssets/CurrentLiabilities: GATE2-PHASE3B-1②で追加（貸借対照表項目の
# ためフロー〈4Q合算〉ではなくストック〈最新Q末の値〉分類が妥当。抽出はされて
# いたがFLOW/STOCK/SHARESいずれにも属さず消費者ゼロのままTTM出力から漏れて
# いた既知バグの是正）
STOCK_FIELDS = frozenset([
    "Cash", "STDebt", "LTDebt", "DeferredRevenue", "Equity", "Assets",
    "CurrentAssets", "CurrentLiabilities",
])

# 株式数フィールド（最新Q末の値）
SHARES_FIELDS = frozenset([
    "SharesBasic", "SharesDiluted",
])

# 意図的にTTM出力対象外とするフィールド（GATE2-PHASE3B-1②で新設）。
# FLOW_FIELDS/STOCK_FIELDS/SHARES_FIELDSのいずれにも入れず、かつ
# 「分類漏れ」として検知されないようにするための明示的な除外リスト。
EXCLUDED_FIELDS = frozenset([
    # GrossProfit逆算用の内部計算専用フィールド（quarterly.py::FIELD_CONCEPTS
    # コメント参照）。単独でTTM出力する意味がないため対象外は意図的。
    "_COGS",
    # reader.py::get_rpo_series()/get_rpo_context()がnormalized JSONを
    # 直接読む別経路で消費されるため、TTM層での分類は不要（GATE2-PHASE3B-1
    # 事前調査で確認済み。ttm.jsonを経由しないだけで実際には正常に消費されている）。
    "RPO",
])

# GATE2-PHASE3B-1②規約C: FIELD_CONCEPTSの全キーが上記4分類のいずれかに
# 属することをモジュールロード時に検証する。新フィールド追加時に分類を
# 忘れると黙って出力から消える問題（CurrentAssets/CurrentLiabilitiesの
# 実例）を、import時点で即座に検知するため。
validate_field_classification(FIELD_CONCEPTS, FLOW_FIELDS, STOCK_FIELDS, SHARES_FIELDS, EXCLUDED_FIELDS)

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
        total = sum(e["val"] or 0 for e in last4)
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

    BUG-TTM-Q4DUP-1: normalizer.py が既に同じ end日付のimplied Q4を
    quarterly_entries に永続化済みの場合は再生成しない（financial_trend_calculator.py
    _build_q4_implied と同じ重複排除パターン）。重複生成すると呼び出し元のマージ処理で
    同一end日付のエントリが2件になり、TTM合算（直近4Q）が実態と乖離する。
    """
    result: list = []
    existing_ends = {e["end"] for e in quarterly_entries if not e.get("is_annual")}
    for annual in annual_entries:
        fy_end = annual.get("end", "")
        fy_start = annual.get("start", "")
        fy_val = annual.get("val")

        if not fy_end or fy_val is None:
            continue
        # 未来のQ4は含めない（アナリスト予想にならないよう）
        if fy_end > _TODAY:
            continue
        # BUG-TTM-Q4DUP-1: 既に同一end日付の四半期データ（実データ or 永続化済みimplied）が
        # 存在する場合はスキップ（二重計上防止）
        if fy_end in existing_ends:
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
        q4_val = fy_val - sum(e["val"] or 0 for e in top3)

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

        q4_val = fy_val - sum(e["val"] or 0 for e in top3)
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


# ---------------------------------------------------------------------------
# Rolling TTM系列
# ---------------------------------------------------------------------------

def _calc_fcf(
    ocf: float | None,
    capex: float | None,
    fl: float | None,
    da: float | None = None,
) -> float | None:
    """
    FCF計算（parser.pyと同じ計算式）。

    FCF = OCF - (|CapEx| - |FinanceLeasePmts|)
    ファイナンスリースはCapExから除外（AMZN等対応）。

    OCF または CapEx が None の場合は None を返す。
    FinanceLeasePmts が None の場合は 0 として扱う。
    """
    if ocf is None or capex is None:
        return None
    pure_capex = abs(capex) - abs(fl or 0)
    return ocf - max(0, pure_capex)


def _select_anchors(all_end_dates: list[str], n_periods: int) -> list[str]:
    """
    anchor[0] = all_end_dates[0]（最新Q）
    anchor[i] = anchor[i-1] から約365日前に最も近い end_date

    許容差分: 305〜425日（365±60日）
    範囲外の場合はそのanchorをスキップ（n_periodsに満たなくても継続）。
    """
    if not all_end_dates:
        return []

    anchors: list[str] = [all_end_dates[0]]

    for _ in range(n_periods - 1):
        prev = anchors[-1]
        prev_date = date.fromisoformat(prev)

        best: str | None = None
        best_diff: int | None = None

        for d in all_end_dates:
            if d >= prev:
                continue
            gap = (prev_date - date.fromisoformat(d)).days
            if 305 <= gap <= 425:
                diff = abs(gap - 365)
                if best_diff is None or diff < best_diff:
                    best = d
                    best_diff = diff

        if best is None:
            break

        gap_actual = (prev_date - date.fromisoformat(best)).days
        if gap_actual < 305:
            logger.warning(
                "anchor gap too small: %s → %s (%d days)", prev, best, gap_actual
            )

        anchors.append(best)

    return anchors


def calc_ttm_series(
    ticker: str,
    normalized: dict,
    n_periods: int = 6,
) -> list[dict]:
    """
    Rolling TTM系列を生成する。
    直近Qをanchor[0]とし、約1年(4Q)ずつ遡ってn_periods点を計算。

    n_periods=6 の理由: rice.pyのCF計算が3年分必要（4点）+ FCF用5点 → 安全マージン6点

    戻り値: ttm_end降順のリスト
    [
      {
        "ttm_end": "2026-01-25",
        "flow": {
          "OCF":              {"val": ..., "quarters_used": 4, "missing": 0},
          "CapEx":            {"val": ..., "quarters_used": 4, "missing": 0},
          "FinanceLeasePmts": {"val": ..., "quarters_used": 4, "missing": 0},
          "FCF":              {"val": ...},
          "Revenue":          {"val": ..., "quarters_used": 4, "missing": 0},
          "NetIncome":        {"val": ..., "quarters_used": 4, "missing": 0},
          "RD":               {"val": ..., "quarters_used": 4, "missing": 0},
          "SM":               {"val": ..., "quarters_used": 4, "missing": 2},
        }
      },
      ...
    ]
    """
    ticker = ticker.upper()
    fields = normalized.get("fields", {})

    # calc_ttm() と同じパターンで quarterly / annual に分離
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

    # calc_ttm() と同じパターンで implied Q4 を合成・マージ
    for field_name in FLOW_FIELDS:
        q4_list = _build_q4_quarterly_entries(
            annual_by_field.get(field_name, []),
            quarterly_by_field.get(field_name, []),
        )
        if q4_list:
            merged = sorted(
                quarterly_by_field.get(field_name, []) + q4_list,
                key=lambda x: x["end"],
                reverse=True,
            )
            quarterly_by_field[field_name] = merged

    # anchor選択: FLOW_FIELDS の全 end_date の union を使用
    all_end_dates: list[str] = sorted(
        {
            e["end"]
            for field_name in FLOW_FIELDS
            for e in quarterly_by_field.get(field_name, [])
        },
        reverse=True,
    )

    anchors = _select_anchors(all_end_dates, n_periods)

    series: list[dict] = []
    for anchor in anchors:
        flow: dict = {}

        for field_name in FLOW_FIELDS:
            q_entries = [
                e for e in quarterly_by_field.get(field_name, [])
                if e["end"] <= anchor
            ]
            last4 = q_entries[:4]
            if not last4:
                continue
            total = sum(e["val"] or 0 for e in last4)
            flow[field_name] = {
                "val": total,
                "quarters_used": len(last4),
                "missing": max(0, 4 - len(last4)),
            }

        # FCF計算（派生値・quarters_used/missingなし）
        ocf_val   = flow.get("OCF", {}).get("val")
        capex_val = flow.get("CapEx", {}).get("val")
        fl_val    = flow.get("FinanceLeasePmts", {}).get("val")
        da_val    = flow.get("DA", {}).get("val")  # v8.2: 維持CapEx分離用
        fcf_val = _calc_fcf(ocf_val, capex_val, fl_val, da_val)
        if fcf_val is not None:
            flow["FCF"] = {"val": fcf_val}

        series.append({
            "ttm_end": anchor,
            "flow": flow,
        })

    logger.info("[%s] TTM series calculated: %d periods", ticker, len(series))
    return series


def save_ttm_series(ticker: str, series: list[dict], n_periods: int = 6) -> str:
    """TTM系列をJSONファイルに保存し、パスを返す"""
    os.makedirs(TTM_DIR, exist_ok=True)
    path = os.path.join(TTM_DIR, f"{ticker.upper()}_ttm_series.json")
    data = {
        "ticker": ticker.upper(),
        "generated_at": datetime.now().isoformat(),
        "n_periods": n_periods,
        "series": series,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("[%s] TTM series saved -> %s", ticker, path)
    return path
