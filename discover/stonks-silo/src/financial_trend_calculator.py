# discover/stonks-silo/src/signal_detector.py
"""
財務ベクトル計算モジュール

quarterly_normalized.json の四半期データから各指標のYoY・QoQベクトルを計算し、
全銘柄のパーセンタイルで正規化してベクトル（角度・長さ）に変換する。

ベクトル定義:
  角度: 半円180度。真上(90°)=最大改善, 水平(0°)=変化なし, 真下(-90°)=最大悪化
  長さ: 全銘柄×全期間の変化率分布のパーセンタイル(0-1)
  原価(原価率): 下がる方が改善のため符号を反転

出力フィールド（results.jsonのticker配下に追加）:
  "financial_vectors": {
    "updated_at": "...",
    "fields": {
      "OCF":        { "yoy": {"angle":45, "length":0.7, "pct":75, "val_latest":-26M, "val_prev":-35M},
                      "qoq": {"angle":20, "length":0.4, "pct":60, ...} },
      "RD":         { ... },
      "NetIncome":  { ... },
      "CapEx":      { ... },
      "Revenue":    { ... },   # 取得できない銘柄はNone
      "GrossProfit":{ ... },   # 取得できない銘柄はNone（逆算含む）
    },
    "composite": {
      "yoy": {"angle":35, "length":0.6},
      "qoq": {"angle":50, "length":0.8},
    },
    "data_quality": {
      "fields_available": ["OCF","RD","NetIncome","CapEx"],
      "fields_missing":   ["Revenue","GrossProfit"],
    }
  }
"""

from __future__ import annotations

import json
import logging
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).resolve().parent
# discover/stonks-silo/src/ → repo root は3階層上
# テスト環境ではフォールバックとして現在ディレクトリから探す
try:
    _REPO_ROOT = _THIS_DIR.parents[2]
except IndexError:
    _REPO_ROOT = Path.cwd()
_NORM_DIR = _REPO_ROOT / "common" / "sec_data" / "normalized"

# 計算対象フィールド
# invert=True: 値が下がる方が改善（原価率）
VECTOR_FIELDS = [
    {"name": "Revenue",     "invert": False, "weight": 1.5},
    {"name": "GrossProfit", "invert": False, "weight": 1.5},  # 原価率の合成
    {"name": "RD",          "invert": False, "weight": 1.0},  # 投資継続性（増加=良い）
    {"name": "NetIncome",   "invert": False, "weight": 2.0},  # 損益改善
    {"name": "OCF",         "invert": False, "weight": 2.0},  # 現金創出力
    {"name": "CapEx",       "invert": False, "weight": 0.5},  # 投資強度（参考）
]

# ヒートマップ対象フィールド（安定取得できるもののみ）
# Revenue・GrossProfitはQ2/Q4未申告銘柄が多いため除外
HEATMAP_FIELDS = {"RD", "NetIncome", "OCF"}

# サブパネル用（別折りたたみ）
SUB_FIELDS = ["SM", "SBC"]

# 合成ベクトルに使うフィールド（RD/CapExは方向性が複雑なため除外）
COMPOSITE_FIELDS = {"Revenue", "GrossProfit", "NetIncome", "OCF"}


_TODAY = date.today().isoformat()


def _build_q4_implied(annual_entries: list, quarterly_entries: list) -> list:
    """
    ttm_calculator._build_q4_quarterly_entriesと同等のQ4逆算ロジック。
    FY年次値 - (Q1+Q2+Q3) = Q4 implied
    """
    result = []
    for annual in annual_entries:
        fy_end   = annual.get("end", "")
        fy_start = annual.get("start", "")
        fy_val   = annual.get("val")
        if not fy_end or fy_val is None:
            continue
        if fy_end > _TODAY:
            continue
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
        try:
            period_days = (date.fromisoformat(fy_end) - date.fromisoformat(q3_end)).days
        except (ValueError, TypeError):
            period_days = 90
        result.append({
            "end":         fy_end,
            "start":       q3_end,
            "val":         q4_val,
            "fp":          "Q4",
            "fy":          annual.get("fy"),
            "form":        "10-K",
            "filed":       annual.get("filed", ""),
            "accn":        annual.get("accn", ""),
            "period_days": period_days,
            "is_ytd":      False,
            "is_annual":   False,
            "is_implied":  True,
        })
    return result


def _get_quarterly_entries(normalized: dict, field_name: str) -> list:
    """standalone Q エントリ + Q4 implied を返す（年次・YTD除外）"""
    entries = normalized.get("fields", {}).get(field_name, [])
    quarterly = [
        e for e in entries
        if not e.get("is_annual") and not e.get("is_ytd")
    ]
    annual = [e for e in entries if e.get("is_annual")]

    # Q4 impliedを追加
    q4_implied = _build_q4_implied(annual, quarterly)

    # 既存Q4エントリと重複しないよう end_date で管理
    existing_ends = {e["end"] for e in quarterly}
    for q4 in q4_implied:
        if q4["end"] not in existing_ends:
            quarterly.append(q4)
            existing_ends.add(q4["end"])

    return sorted(quarterly, key=lambda x: x["end"])


def _calc_yoy_change(entries: list) -> Optional[dict]:
    """
    直近四半期と1年前同期のYoY変化率を計算。
    同じfp（Q1/Q2/Q3/Q4）同士で比較。
    """
    if len(entries) < 5:
        return None

    # fpでグルーピング
    by_fp: dict[str, list] = {}
    for e in entries:
        fp = e.get("fp", "")
        if fp.startswith("Q"):
            by_fp.setdefault(fp, []).append(e)

    # 最新エントリのfpを取得
    latest = entries[-1]
    latest_fp = latest.get("fp", "")
    if not latest_fp.startswith("Q"):
        return None

    same_fp = sorted(by_fp.get(latest_fp, []), key=lambda x: x["end"])
    if len(same_fp) < 2:
        return None

    val_latest = same_fp[-1]["val"]
    val_prev   = same_fp[-2]["val"]

    if val_prev == 0:
        return None

    change_pct = (val_latest - val_prev) / abs(val_prev) * 100
    return {
        "change_pct": change_pct,
        "val_latest": val_latest,
        "val_prev":   val_prev,
        "end_latest": same_fp[-1]["end"],
        "end_prev":   same_fp[-2]["end"],
        "fp":         latest_fp,
    }


def _calc_qoq_change(entries: list) -> Optional[dict]:
    """直近四半期と前四半期のQoQ変化率を計算。"""
    if len(entries) < 2:
        return None

    val_latest = entries[-1]["val"]
    val_prev   = entries[-2]["val"]

    if val_prev == 0:
        return None

    change_pct = (val_latest - val_prev) / abs(val_prev) * 100
    return {
        "change_pct": change_pct,
        "val_latest": val_latest,
        "val_prev":   val_prev,
        "end_latest": entries[-1]["end"],
        "end_prev":   entries[-2]["end"],
    }


def _pct_to_angle(pct: float) -> float:
    """
    パーセンタイル(0-100) → 角度(-90°〜+90°)
    50パーセンタイル = 0°（水平、変化なし）
    100パーセンタイル = +90°（真上、最大改善）
    0パーセンタイル = -90°（真下、最大悪化）
    """
    normalized = (pct - 50) / 50  # -1 〜 +1
    return round(normalized * 90, 1)


def _pct_to_length(pct: float) -> float:
    """パーセンタイル(0-100) → 長さ(0-1)。50パーセンタイルを0.5とする。"""
    return round(abs(pct - 50) / 50, 3)


def compute_vectors(all_normalized: dict[str, dict]) -> dict[str, dict]:
    """
    全銘柄のnormalizedデータからベクトルを計算する。

    Parameters
    ----------
    all_normalized: {ticker: normalized_dict}

    Returns
    -------
    {ticker: financial_vectors_dict}
    """
    # Step1: 全銘柄×全フィールドのchange_pctを収集してパーセンタイル基準を作る
    all_changes: dict[str, dict[str, list[float]]] = {
        "yoy": {f["name"]: [] for f in VECTOR_FIELDS},
        "qoq": {f["name"]: [] for f in VECTOR_FIELDS},
    }

    raw_changes: dict[str, dict] = {}  # {ticker: {field: {yoy/qoq: change_info}}}

    for ticker, normalized in all_normalized.items():
        raw_changes[ticker] = {}
        for field_cfg in VECTOR_FIELDS:
            fname = field_cfg["name"]
            entries = _get_quarterly_entries(normalized, fname)
            yoy = _calc_yoy_change(entries)
            qoq = _calc_qoq_change(entries)
            raw_changes[ticker][fname] = {"yoy": yoy, "qoq": qoq}

            if yoy is not None:
                pct = yoy["change_pct"]
                if field_cfg["invert"]:
                    pct = -pct
                all_changes["yoy"][fname].append(pct)
            if qoq is not None:
                pct = qoq["change_pct"]
                if field_cfg["invert"]:
                    pct = -pct
                all_changes["qoq"][fname].append(pct)

    # Step2: 各フィールドのパーセンタイル計算用ソート済みリスト
    sorted_changes: dict[str, dict[str, list[float]]] = {
        "yoy": {fname: sorted(vals) for fname, vals in all_changes["yoy"].items()},
        "qoq": {fname: sorted(vals) for fname, vals in all_changes["qoq"].items()},
    }

    def _calc_percentile(val: float, sorted_vals: list[float]) -> float:
        """変化率をパーセンタイル(0-100)に変換"""
        if not sorted_vals:
            return 50.0
        n = len(sorted_vals)
        # 二分探索で位置を求める
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if sorted_vals[mid] < val:
                lo = mid + 1
            else:
                hi = mid
        return round(lo / n * 100, 1)

    # Step3: 各銘柄のベクトルを計算
    results: dict[str, dict] = {}

    for ticker, field_data in raw_changes.items():
        normalized = all_normalized[ticker]
        fields_out: dict = {}
        available: list[str] = []
        missing: list[str] = []
        composite_angles_yoy: list[tuple[float, float]] = []  # (angle, weight)
        composite_angles_qoq: list[tuple[float, float]] = []

        # 全フィールドの最新endを取得して基準日を決定
        all_entries_by_field = {
            field_cfg["name"]: _get_quarterly_entries(normalized, field_cfg["name"])
            for field_cfg in VECTOR_FIELDS
        }
        latest_ends = [
            entries[-1]["end"]
            for entries in all_entries_by_field.values()
            if entries
        ]
        # 基準日 = 全フィールドの最新endの最大値
        base_end = max(latest_ends) if latest_ends else None

        for field_cfg in VECTOR_FIELDS:
            fname = field_cfg["name"]
            invert = field_cfg["invert"]
            weight = field_cfg["weight"]
            info = field_data.get(fname, {})

            field_out: dict = {}

            # 時系列データ: base_endより古い（または等しい）エントリの末尾8件
            entries = all_entries_by_field[fname]
            if base_end:
                filtered = [e for e in entries if e["end"] <= base_end]
            else:
                filtered = entries
            recent = filtered[-8:]
            field_out["series_q"] = [
                {"end": e["end"], "fp": e.get("fp", ""), "val": e["val"]}
                for e in recent
            ]

            for period in ("yoy", "qoq"):
                change = info.get(period)
                if change is None:
                    field_out[period] = None
                    continue

                pct_val = change["change_pct"]
                if invert:
                    pct_val = -pct_val

                sv = sorted_changes[period].get(fname, [])
                pct_rank = _calc_percentile(pct_val, sv)
                angle = _pct_to_angle(pct_rank)
                length = _pct_to_length(pct_rank)

                field_out[period] = {
                    "angle":      angle,
                    "length":     length,
                    "percentile": pct_rank,
                    "change_pct": round(change["change_pct"], 1),
                    "val_latest": change["val_latest"],
                    "val_prev":   change["val_prev"],
                    "end_latest": change["end_latest"],
                    "end_prev":   change["end_prev"],
                }
                if "fp" in change:
                    field_out[period]["fp"] = change["fp"]

                # 合成ベクトル用に収集（対象フィールドのみ）
                if fname in COMPOSITE_FIELDS:
                    if period == "yoy":
                        composite_angles_yoy.append((angle, weight))
                    else:
                        composite_angles_qoq.append((angle, weight))

            fields_out[fname] = field_out
            if any(field_out.get(p) is not None for p in ("yoy", "qoq")):
                available.append(fname)
            else:
                missing.append(fname)

        # 合成ベクトル（加重平均角度）
        def _weighted_angle(angle_weights: list[tuple[float, float]]) -> Optional[dict]:
            if not angle_weights:
                return None
            total_w = sum(w for _, w in angle_weights)
            if total_w == 0:
                return None
            avg_angle = sum(a * w for a, w in angle_weights) / total_w
            # 角度の絶対値を長さとして使用（-90〜+90 → 0〜1）
            length = round(abs(avg_angle) / 90, 3)
            return {
                "angle":  round(avg_angle, 1),
                "length": length,
            }

        results[ticker] = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "fields": fields_out,
            "composite": {
                "yoy": _weighted_angle(composite_angles_yoy),
                "qoq": _weighted_angle(composite_angles_qoq),
            },
            "data_quality": {
                "fields_available": available,
                "fields_missing":   missing,
                "heatmap_fields":   sorted(HEATMAP_FIELDS),
            },
        }

    return results


def load_all_normalized(tickers: list[str]) -> dict[str, dict]:
    """対象ティッカーのquarterly_normalizedを一括読み込み"""
    result = {}
    for ticker in tickers:
        path = _NORM_DIR / f"{ticker}_quarterly_normalized.json"
        if not path.exists():
            logger.warning("[%s] normalized not found: %s", ticker, path)
            continue
        try:
            with open(path, encoding="utf-8") as f:
                result[ticker] = json.load(f)
        except Exception as e:
            logger.error("[%s] failed to load normalized: %s", ticker, e)
    return result
