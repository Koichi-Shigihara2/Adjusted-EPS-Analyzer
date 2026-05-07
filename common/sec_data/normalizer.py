"""
common/sec_data/normalizer.py
責務: Raw TableのYTD値を単一四半期値に差分変換する
出力: normalized/{ticker}_quarterly_normalized.json
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
NORMALIZED_DIR = os.path.join(BASE_DIR, "normalized")


def normalize(ticker: str, raw: dict) -> dict:
    """
    YTD値 → Q単独値への差分変換。

    - is_ytd=True のエントリを対象に、前四半期YTD値との差分を計算。
    - is_ytd=False（SA）はそのまま通す。
    - is_annual=True のエントリも変換せずそのまま保持。
    GrossProfit が欠損している場合、Revenue - _COGS で逆算を試みる。
    """
    ticker = ticker.upper()
    fields_raw = raw.get("fields", {})
    fields_norm: dict[str, list] = {}

    for field_name, entries in fields_raw.items():
        if field_name == "_COGS":
            fields_norm[field_name] = entries
            continue
        fields_norm[field_name] = _normalize_field(entries)

    # GrossProfit逆算（欠損補完）
    fields_norm = _calc_gross_profit(fields_norm)

    # 内部フィールドは出力から除外
    fields_norm.pop("_COGS", None)

    logger.info("[%s] normalization done", ticker)
    return {
        "ticker": ticker,
        "generated_at": datetime.now().isoformat(),
        "fields": fields_norm,
    }


def _normalize_field(entries: list) -> list:
    """1フィールドのエントリを正規化する"""
    if not entries:
        return []

    annual = [e for e in entries if e.get("is_annual")]
    quarterly = [e for e in entries if not e.get("is_annual")]

    sa_entries = [e for e in quarterly if not e.get("is_ytd")]
    ytd_entries = [e for e in quarterly if e.get("is_ytd")]

    if not ytd_entries:
        return sorted(annual + sa_entries, key=lambda x: x["end"])

    # YTDチェーンの起点となるstart（FY開始日）を特定
    ytd_starts = {e["start"] for e in ytd_entries}

    # Q1 SA など start=FY_start のエントリもYTDチェーンに含める
    chain_entries = [e for e in quarterly if e["start"] in ytd_starts]
    passthrough_entries = [e for e in quarterly if e["start"] not in ytd_starts]

    # FY開始日でグルーピング
    by_fy_start: dict[str, list] = defaultdict(list)
    for e in chain_entries:
        by_fy_start[e["start"]].append(e)

    converted: list = []
    for fy_start, fy_entries in by_fy_start.items():
        sorted_entries = sorted(fy_entries, key=lambda x: x["end"])
        converted.extend(_ytd_to_quarterly(sorted_entries))

    all_quarterly = sorted(passthrough_entries + converted, key=lambda x: x["end"])
    return sorted(annual + all_quarterly, key=lambda x: x["end"])


def _ytd_to_quarterly(fy_entries: list) -> list:
    """
    YTDエントリのリストを受け取り、差分変換した単一四半期エントリを返す。

    fy_entries: 同一FY内のエントリ（SA Q1 + YTD Q2/Q3）をend_date昇順でソート済み。
    Q1（年度最初・SA）は差分なしでそのまま使用。
    """
    result: list = []
    prev_ytd: float = 0

    for entry in fy_entries:
        new_entry = dict(entry)

        if not entry.get("is_ytd"):
            # SA entry（Q1など）: そのまま使用し、累積YTDに加算
            standalone = entry["val"]
            prev_ytd += standalone
        else:
            # YTD entry: 前回YTDとの差分
            standalone = entry["val"] - prev_ytd
            # 異常フラグ: 前QのYTDが正値だったのに累積が減少した場合（決算期変更等）
            # prev_ytd=0（Q1未発見）や負値累積（ICF/CFF）では判定しない。
            if prev_ytd > 0 and entry["val"] < prev_ytd:
                new_entry["anomaly"] = True
                logger.warning(
                    "YTD reversal for end=%s fp=%s val=%s prev_ytd=%s",
                    entry.get("end"), entry.get("fp"), entry["val"], prev_ytd,
                )
            prev_ytd = entry["val"]  # YTDは全Q累積なのでprevを上書き
            new_entry["is_ytd"] = False

        new_entry["val"] = standalone
        result.append(new_entry)

    return result


def _calc_gross_profit(fields: dict) -> dict:
    """
    GrossProfit が欠損している四半期を Revenue - _COGS で逆算する。

    _COGS XBRL概念: CostOfRevenue（quarterly.pyで取得済み）
    """
    gp_entries = fields.get("GrossProfit", [])
    rev_entries = fields.get("Revenue", [])
    cogs_entries = fields.get("_COGS", [])

    if not cogs_entries or not rev_entries:
        return fields

    # 既存GrossProfit の end_date セット
    gp_ends = {e["end"] for e in gp_entries if not e.get("is_annual")}

    # Revenue と COGS を end_date でインデックス化
    rev_by_end = {e["end"]: e["val"] for e in rev_entries if not e.get("is_annual")}
    cogs_by_end = {e["end"]: e["val"] for e in cogs_entries if not e.get("is_annual")}

    backfilled: list = []
    for end_date, rev_val in rev_by_end.items():
        if end_date in gp_ends:
            continue
        cogs_val = cogs_by_end.get(end_date)
        if cogs_val is None or rev_val is None:
            continue
        # Revenue と COGS は符号が正なので単純差分
        gp_val = rev_val - abs(cogs_val)
        # 逆算エントリを対応するRevenueエントリから構築
        rev_entry = next((e for e in rev_entries if e["end"] == end_date), None)
        if rev_entry is None:
            continue
        backfilled.append({
            **{k: rev_entry[k] for k in ("end", "start", "fp", "fy", "form", "filed",
                                          "period_days", "is_ytd", "is_annual")
               if k in rev_entry},
            "val": gp_val,
            "accn": rev_entry.get("accn", ""),
            "backfilled": True,
        })
        logger.debug("GrossProfit backfilled for end=%s: %s", end_date, gp_val)

    if backfilled:
        merged = sorted(
            gp_entries + backfilled,
            key=lambda x: x["end"],
        )
        fields = dict(fields)
        fields["GrossProfit"] = merged

    return fields


def save_normalized(ticker: str, normalized: dict) -> str:
    """normalized dataをJSONファイルに保存し、パスを返す"""
    os.makedirs(NORMALIZED_DIR, exist_ok=True)
    path = os.path.join(NORMALIZED_DIR, f"{ticker.upper()}_quarterly_normalized.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    logger.info("[%s] normalized saved → %s", ticker, path)
    return path
