"""
TANUKI VALUATION - KPI Fetcher
annual_{year}.json の segments フィールドから kpi_data を生成する

呼び出し元: core_calculator.py（pipeline.py 経由）
データソース: common/sec_data/data/{TICKER}/annual_{year}.json

責務:
  - annual_{year}.json の segments を読む
  - kpi_config.py の定義（weight, config_growth, note）と突合
  - 全社売上（annual_{year}.json の pl.revenue）を合わせて「その他」を計算
  - 予測値（FY+1〜+3）を config_growth から自動計算
  - kpi_data 構造を返す → pipeline が latest.json に追記
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# パス設定
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# kpi_config.py は同じディレクトリ（tanuki_valuation/）にある
try:
    from kpi_config import KPI_DEFINITIONS, get_kpi_definition
    HAS_KPI_CONFIG = True
except ImportError:
    HAS_KPI_CONFIG = False
    KPI_DEFINITIONS = {}


def _load_annual(data_dir: str, ticker: str, fy: int) -> Optional[Dict[str, Any]]:
    """annual_{fy}.json を読み込む"""
    path = os.path.join(data_dir, ticker.upper(), f"annual_{fy}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _fy_label(fy: int, is_est: bool = False) -> str:
    """FY年度ラベルを生成"""
    return f"FY{fy}_est" if is_est else f"FY{fy}"


def build_kpi_data(
    ticker: str,
    sec_data_dir: str,
    fiscal_year_latest: int,
    history_years: int = 3,
    forecast_years: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    kpi_data を構築して返す

    Args:
        ticker:             銘柄コード
        sec_data_dir:       common/sec_data/data/ のパス
        fiscal_year_latest: 最新会計年度（例: 2025）
        history_years:      過去何年分を表示するか（デフォルト3）
        forecast_years:     将来何年分を予測するか（デフォルト3）

    Returns:
        kpi_data dict（latest.json に格納される形式）
        セグメントデータがない場合は None
    """
    ticker = ticker.upper()

    if not HAS_KPI_CONFIG:
        return None

    defn = get_kpi_definition(ticker)
    if not defn:
        return None

    seg_names     = defn.get("segments", [])
    fiscal_ye_end = defn.get("fiscal_year_end", 12)
    unit          = defn.get("revenue_unit", "B USD")

    if not seg_names:
        return None

    # segment_config.py の設定を読み込む（weight, config_growth, note）
    seg_config = _load_segment_config(ticker)

    # ── 実績データ収集 ──────────────────────────────────────────
    # history_years 分の annual_*.json を読む
    actual_years = list(range(fiscal_year_latest - history_years + 1, fiscal_year_latest + 1))

    # セグメント別データ（年度 → セグメント名 → {revenue, operating_income}）
    annual_data: Dict[int, Dict[str, Any]] = {}
    for fy in actual_years:
        ann = _load_annual(sec_data_dir, ticker, fy)
        if ann:
            annual_data[fy] = ann

    # セグメント別売上が1件も取れていない場合でも segment_config があれば継続
    has_any_segment = any(
        ann.get("segments")
        for ann in annual_data.values()
    )
    # segment_config の定義もない場合のみ None を返す
    if not has_any_segment and not seg_config:
        return None

    # ── セグメント構造を構築 ────────────────────────────────────
    segments: Dict[str, Dict[str, Any]] = {}

    for seg_name in seg_names:
        cfg = seg_config.get(seg_name, {})

        seg_entry: Dict[str, Any] = {
            "weight":        cfg.get("weight"),
            "config_growth": cfg.get("growth"),
            "note":          cfg.get("note", ""),
            "revenue":       {},
            "operating_income": {},
            "operating_margin": {},
            "yoy_growth":    {},
        }

        # 実績値を埋める
        for fy in actual_years:
            ann = annual_data.get(fy, {})
            seg_raw = ann.get("segments", {}).get(seg_name, {})
            label = _fy_label(fy)

            rev = seg_raw.get("revenue")
            oi  = seg_raw.get("operating_income")
            om  = seg_raw.get("operating_margin")

            seg_entry["revenue"][label]           = rev
            seg_entry["operating_income"][label]  = oi
            seg_entry["operating_margin"][label]  = om

        # YoY成長率（実績）を計算
        for i, fy in enumerate(actual_years):
            if i == 0:
                seg_entry["yoy_growth"][_fy_label(fy)] = None
                continue
            prev_fy  = actual_years[i - 1]
            rev_curr = seg_entry["revenue"].get(_fy_label(fy))
            rev_prev = seg_entry["revenue"].get(_fy_label(prev_fy))
            if rev_curr is not None and rev_prev and rev_prev != 0:
                seg_entry["yoy_growth"][_fy_label(fy)] = round(
                    (rev_curr - rev_prev) / abs(rev_prev), 4
                )
            else:
                seg_entry["yoy_growth"][_fy_label(fy)] = None

        # 予測値を埋める（config_growth を適用）
        g = cfg.get("growth")
        if g is not None:
            last_rev = seg_entry["revenue"].get(_fy_label(fiscal_year_latest))
            for j in range(1, forecast_years + 1):
                est_fy    = fiscal_year_latest + j
                est_label = _fy_label(est_fy, is_est=True)
                if last_rev is not None:
                    last_rev  = round(last_rev * (1 + g))
                    seg_entry["revenue"][est_label]          = last_rev
                    seg_entry["operating_income"][est_label] = None  # 予測利益は未設定
                    seg_entry["operating_margin"][est_label] = None
                    seg_entry["yoy_growth"][est_label]       = round(g, 4)
                else:
                    seg_entry["revenue"][est_label]          = None
                    seg_entry["operating_income"][est_label] = None
                    seg_entry["operating_margin"][est_label] = None
                    seg_entry["yoy_growth"][est_label]       = round(g, 4) if g else None

        segments[seg_name] = seg_entry

    # ── 全社売上（total_revenue）を年度別に収集 ─────────────────
    # SEC annual_*.json の pl.revenue（全社売上）を優先使用
    total_revenue: Dict[str, Optional[float]] = {}
    for fy in actual_years:
        ann = annual_data.get(fy, {})
        # pl.revenue が全社売上（最も正確）
        rev = ann.get("pl", {}).get("revenue")
        if rev is None:
            # フォールバック: セグメント合計
            rev = sum(
                (ann.get("segments", {}).get(s, {}).get("revenue") or 0)
                for s in seg_names
            ) or None
        total_revenue[_fy_label(fy)] = rev

    # 予測全社売上（セグメント合計から計算）
    for j in range(1, forecast_years + 1):
        est_fy    = fiscal_year_latest + j
        est_label = _fy_label(est_fy, is_est=True)
        seg_sum   = sum(
            seg["revenue"].get(est_label) or 0
            for seg in segments.values()
        )
        total_revenue[est_label] = seg_sum if seg_sum > 0 else None

    # ── segments_fetched_at を annual から取得 ───────────────────
    latest_ann   = annual_data.get(fiscal_year_latest, {})
    fetched_at   = latest_ann.get("segments_fetched_at", "—")
    filing_date  = latest_ann.get("segments_filing_date", "—")

    return {
        "fetched_at":    fetched_at,
        "filing_date":   filing_date,
        "source":        "SEC 10-K iXBRL (local parse)",
        "unit":          unit,
        "fiscal_year_end": fiscal_ye_end,
        "total_revenue": total_revenue,
        "segments":      segments,
        "errors":        [],
    }


def _load_segment_config(ticker: str) -> Dict[str, Dict[str, Any]]:
    """
    segment_config.py から銘柄のセグメント設定を読み込む

    Returns:
        {"Data Center": {"weight": 0.88, "growth": 0.40, "note": "..."}, ...}
    """
    try:
        import importlib.util
        # tanuki_valuation/ 直下の segment_config.py
        seg_cfg_path = os.path.join(_current_dir, "segment_config.py")
        if not os.path.exists(seg_cfg_path):
            return {}
        spec = importlib.util.spec_from_file_location("segment_config", seg_cfg_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        config = getattr(mod, "SEGMENT_OVERRIDES", {}).get(ticker, {})
        if not config or not config.get("enabled"):
            return {}

        result = {}
        for seg_name, seg_data in config.get("segments", {}).items():
            result[seg_name] = {
                "weight": seg_data.get("weight"),
                "growth": seg_data.get("growth"),
                "note":   seg_data.get("note", ""),
            }
        return result
    except Exception as e:
        print(f"   [kpi_fetcher] segment_config.py 読み込みエラー: {e}")
        return {}


def get_fiscal_year_latest(ticker: str, sec_data_dir: str) -> int:
    """
    利用可能な最新の会計年度を取得

    annual_{year}.json の最大年度を返す
    """
    ticker = ticker.upper()
    ticker_dir = os.path.join(sec_data_dir, ticker)
    if not os.path.exists(ticker_dir):
        return datetime.now().year

    years = []
    for fn in os.listdir(ticker_dir):
        if fn.startswith("annual_") and fn.endswith(".json"):
            try:
                y = int(fn.replace("annual_", "").replace(".json", ""))
                years.append(y)
            except ValueError:
                pass
    return max(years) if years else datetime.now().year


if __name__ == "__main__":
    # テスト実行
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", default="NVDA", nargs="?")
    args = parser.parse_args()

    # パス解決
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    repo_root    = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    sec_data_dir = os.path.join(repo_root, "common", "sec_data", "data")

    ticker    = args.ticker.upper()
    latest_fy = get_fiscal_year_latest(ticker, sec_data_dir)
    print(f"最新FY: {latest_fy}")

    kpi = build_kpi_data(
        ticker=ticker,
        sec_data_dir=sec_data_dir,
        fiscal_year_latest=latest_fy,
    )
    if kpi:
        print(json.dumps(kpi, ensure_ascii=False, indent=2))
    else:
        print("kpi_data 取得失敗（セグメントデータなし）")
