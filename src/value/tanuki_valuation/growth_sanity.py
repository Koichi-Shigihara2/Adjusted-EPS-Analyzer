"""
growth_sanity.py
成長率サニティチェックモジュール

設定された Phase1 成長率が業界ベンチマーク・過去実績と比べて
明らかに非現実的でないかを検証し、根拠サマリーを生成する。
"""

import os
import json
import logging
import xlrd

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Damodaran キャッシュのパス
# このスクリプトは src/value/tanuki_valuation/ にあるため
# リポジトリルートを基準にした絶対パスで参照する
# ─────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
_CACHE_DIR = os.path.join(_REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "common", "damodaran_cache")
_FUNDGR_PATH = os.path.join(_CACHE_DIR, "fundgrEB.xls")
_INDNAME_PATH = os.path.join(_CACHE_DIR, "indname.xls")
_META_PATH = os.path.join(_CACHE_DIR, "cache_meta.json")


# ─────────────────────────────────────────────
# TANUKI sector → Damodaran Industry Name マッピング
#
# 【重要】Damodaran の分類は SIC コードベースのため
# 実態と乖離する銘柄がある（例: MSFT→Trucking, ZS→Steel）。
# ticker_overrides で個別上書きを優先する。
# ─────────────────────────────────────────────
SECTOR_TO_DAMODARAN = {
    "semiconductor":     "Semiconductor",
    "semiconductor_eq":  "Semiconductor Equip",
    "software":          "Software (System & Application)",
    "cloud":             "Software (System & Application)",
    "cybersecurity":     "Software (System & Application)",
    "internet":          "Software (Internet)",
    "ecommerce":         "Retail (General)",
    "fintech":           "Financial Svcs. (Non-bank & Insurance)",
    "biotech":           "Drugs (Biotechnology)",
    "pharma":            "Drugs (Pharmaceutical)",
    "healthcare":        "Healthcare Products",
    "healthcare_it":     "Heathcare Information and Technology",
    "ev":                "Auto & Truck",
    "defense":           "Aerospace/Defense",
    "general_tech":      "Computers/Peripherals",
    "advertising":       "Advertising",
    "entertainment":     "Entertainment",
    "telecom":           "Telecom. Services",
    "restaurant":        "Restaurant/Dining",
    "education":         "Education",
    "retail_auto":       "Retail (Automotive)",
}

# 銘柄個別の Damodaran 分類上書き
# indname.xls で実際に確認したマッピング（SICベース分類が実態と乖離する場合）
TICKER_INDUSTRY_OVERRIDES = {
    # 正しく分類されている銘柄（確認済み）
    "NVDA":  "Semiconductor",
    "AAPL":  "Computers/Peripherals",
    "CRWD":  "Software (System & Application)",
    "DDOG":  "Software (System & Application)",
    "PLTR":  "Software (System & Application)",
    "APP":   "Software (System & Application)",
    "MSTR":  "Software (System & Application)",
    "ADBE":  "Software (System & Application)",
    "CRM":   "Software (System & Application)",
    "NOW":   "Software (System & Application)",
    "WDAY":  "Software (System & Application)",
    "HUBS":  "Software (System & Application)",
    "GTLB":  "Software (System & Application)",
    "BILL":  "Software (System & Application)",
    "PANW":  "Software (System & Application)",
    "FTNT":  "Software (System & Application)",
    "SPOT":  "Software (System & Application)",
    "MDB":   "Software (Internet)",
    "OKTA":  "Software (Internet)",
    "SHOP":  "Software (Internet)",
    "CRWV":  "Software (Internet)",
    "TTD":   "Advertising",
    "NFLX":  "Entertainment",
    "CAVA":  "Restaurant/Dining",
    "ONON":  "Shoe",
    "DUOL":  "Education",
    "HIMS":  "Healthcare Support Services",
    "VEEV":  "Heathcare Information and Technology",
    "AXON":  "Aerospace/Defense",
    "RKLB":  "Aerospace/Defense",
    "COIN":  "Financial Svcs. (Non-bank & Insurance)",
    "TSLA":  "Auto & Truck",
    "CVNA":  "Retail (Automotive)",
    "SQ":    "Retail (Automotive)",
    "SMCI":  "Computers/Peripherals",
    "UBER":  "Transportation",
    "LYFT":  "Transportation",
    "GOOGL": "Software (Entertainment)",
    "META":  "Software (Entertainment)",
    # SICベース分類が実態と乖離 → 実態に近い業種に上書き
    "MSFT":  "Software (System & Application)",   # SIC→Trucking を上書き
    "AMZN":  "Software (System & Application)",   # SIC→Retail(General)、クラウド主軸
    "NET":   "Software (System & Application)",   # SIC→Telecom を上書き
    "ZS":    "Software (System & Application)",   # SIC→Steel を上書き
    "SNOW":  "Software (System & Application)",   # SIC→Transportation を上書き
    "ANET":  "Telecom. Equipment",                # SIC→Telecom.Services を上書き
    "ARM":   "Semiconductor",                     # SIC→Transportation を上書き
    "CELH":  "Beverage (Soft)",                   # SIC→Steel を上書き
    "LUNR":  "Aerospace/Defense",                 # SIC→Metals&Mining を上書き
    "S":     "Software (System & Application)",   # SIC→Utility(Water) を上書き
    "DIS":   "Entertainment",                     # SIC→Real Estate を上書き
}


# ─────────────────────────────────────────────
# Damodaran データ読み込み（起動時1回だけ実行）
# ─────────────────────────────────────────────
_damodaran_data: dict = {}   # {industry_name: {roc, rr, g_ebit}}
_damodaran_loaded = False


def _load_damodaran():
    global _damodaran_data, _damodaran_loaded
    if _damodaran_loaded:
        return

    if not os.path.exists(_FUNDGR_PATH):
        logger.warning(f"Damodaran cache not found: {_FUNDGR_PATH}")
        _damodaran_loaded = True
        return

    try:
        wb = xlrd.open_workbook(_FUNDGR_PATH)
        sh = wb.sheet_by_name("Industry Averages")
        # row7 がヘッダー: Industry Name / Number of Firms / ROC / Reinvestment Rate / Expected Growth in EBIT
        for i in range(8, sh.nrows):
            row = sh.row_values(i)
            name = str(row[0]).strip()
            if not name or name.startswith("Total"):
                continue
            roc = row[2] if isinstance(row[2], float) else None
            rr  = row[3] if isinstance(row[3], float) else None
            g   = row[4] if isinstance(row[4], float) else None
            _damodaran_data[name] = {"roc": roc, "rr": rr, "g_ebit": g}

        logger.info(f"Damodaran data loaded: {len(_damodaran_data)} industries")

        # キャッシュ年を確認して古ければ警告
        if os.path.exists(_META_PATH):
            with open(_META_PATH, encoding="utf-8") as f:
                meta = json.load(f)
            cache_year = meta.get("year", 0)
            import datetime
            current_year = datetime.date.today().year
            if current_year - cache_year >= 2:
                logger.warning(
                    f"Damodaran cache is from {cache_year}. "
                    "Consider updating: https://pages.stern.nyu.edu/~adamodar/pc/datasets/fundgrEB.xls"
                )
    except Exception as e:
        logger.warning(f"Failed to load Damodaran data: {e}")
    finally:
        _damodaran_loaded = True


def get_industry_benchmark(ticker: str, sector: str | None) -> dict | None:
    """
    ticker と sector から Damodaran の業種ベンチマークを返す。
    戻り値: {"industry": str, "g_ebit": float, "roc": float, "rr": float} or None
    """
    _load_damodaran()
    if not _damodaran_data:
        return None

    # 優先順位: ticker個別上書き > sector マッピング
    industry_name = TICKER_INDUSTRY_OVERRIDES.get(ticker)
    if industry_name is None and sector:
        industry_name = SECTOR_TO_DAMODARAN.get(sector)
    if industry_name is None:
        return None

    data = _damodaran_data.get(industry_name)
    if data is None:
        return None

    return {
        "industry": industry_name,
        "g_ebit": data["g_ebit"],
        "roc": data["roc"],
        "rr": data["rr"],
    }


# ─────────────────────────────────────────────
# Revenue CAGR 計算
# ─────────────────────────────────────────────
def calc_revenue_cagr(annual_revenues: list[float]) -> dict:
    """
    annual_revenues: 古い順のリスト [rev_oldest, ..., rev_latest]
    戻り値: {"cagr_3yr": float|None, "cagr_5yr": float|None}
    """
    result = {"cagr_3yr": None, "cagr_5yr": None}
    if not annual_revenues or len(annual_revenues) < 2:
        return result

    latest = annual_revenues[-1]
    if latest <= 0:
        return result

    if len(annual_revenues) >= 4:
        base = annual_revenues[-4]
        if base > 0:
            result["cagr_3yr"] = (latest / base) ** (1 / 3) - 1

    if len(annual_revenues) >= 6:
        base = annual_revenues[-6]
        if base > 0:
            result["cagr_5yr"] = (latest / base) ** (1 / 5) - 1

    return result


# ─────────────────────────────────────────────
# ファンダメンタル成長率（RR × ROIC）
# ─────────────────────────────────────────────
def calc_fundamental_growth(
    operating_income: float,
    tax_rate: float,
    total_equity: float,
    total_debt: float,
    cash: float,
    capex: float,
    depreciation: float,
    delta_working_capital: float,
) -> float | None:
    """
    g = Reinvestment Rate × ROIC
    計算不能（負のROIC等）の場合は None を返す。
    """
    try:
        nopat = operating_income * (1 - tax_rate)
        if nopat <= 0:
            return None

        invested_capital = total_equity + total_debt - cash
        if invested_capital <= 0:
            return None

        roic = nopat / invested_capital

        reinvestment = capex - depreciation + delta_working_capital
        reinvestment_rate = reinvestment / nopat

        g = reinvestment_rate * roic
        # 異常値を除外（-100%〜+200%の範囲外）
        if not (-1.0 <= g <= 2.0):
            return None
        return g
    except Exception:
        return None


# ─────────────────────────────────────────────
# メイン判定関数
# ─────────────────────────────────────────────
def check_growth_sanity(
    ticker: str,
    phase1_growth: float,
    sector: str | None = None,
    annual_revenues: list[float] | None = None,
    g_fundamental: float | None = None,
) -> dict:
    """
    成長率サニティチェックを実行し、結果 dict を返す。

    戻り値例:
    {
        "verdict": "PLAUSIBLE",          # PLAUSIBLE / REVIEW / AGGRESSIVE
        "phase1_growth": 0.20,
        "industry_benchmark": 0.096,
        "damodaran_industry": "Semiconductor",
        "damodaran_year": 2025,
        "rev_cagr_3yr": 0.221,
        "rev_cagr_5yr": 0.198,
        "g_fundamental": 0.312,
        "signals": [...],
        "warnings": [...],
    }
    """
    signals = []
    warnings = []

    # --- Damodaran ベンチマーク取得 ---
    benchmark = get_industry_benchmark(ticker, sector)
    industry_g = benchmark["g_ebit"] if benchmark else None

    # --- Revenue CAGR 計算 ---
    cagr = calc_revenue_cagr(annual_revenues or [])

    # --- チェック1: 業界ベンチマーク比較 ---
    if industry_g is not None and industry_g > 0:
        ratio = phase1_growth / industry_g
        ind_label = f"{benchmark['industry']}({industry_g:.1%})"
        if ratio <= 1.5:
            signals.append(f"業界平均{ind_label}の{ratio:.1f}倍以内 ✅")
        elif ratio <= 2.5:
            signals.append(f"業界平均{ind_label}の{ratio:.1f}倍 ℹ️")
        else:
            warnings.append(f"業界平均{ind_label}の{ratio:.1f}倍超 ⚠️")
    elif industry_g is not None and industry_g <= 0:
        # 業界平均がマイナスの場合（単純比較不可）
        signals.append(f"業界平均({benchmark['industry']})はマイナス成長。個別銘柄の独自評価が必要 ℹ️")

    # --- チェック2: 過去実績 CAGR 比較 ---
    historical_cagrs = [v for v in [cagr.get("cagr_3yr"), cagr.get("cagr_5yr")] if v and v > 0]
    if historical_cagrs:
        best = max(historical_cagrs)
        ratio_hist = phase1_growth / best
        label_3yr = f"{cagr['cagr_3yr']:.1%}" if cagr.get("cagr_3yr") else "N/A"
        label_5yr = f"{cagr['cagr_5yr']:.1%}" if cagr.get("cagr_5yr") else "N/A"
        hist_label = f"過去実績(3yr:{label_3yr} / 5yr:{label_5yr})"
        if ratio_hist <= 1.3:
            signals.append(f"{hist_label}と整合 ✅")
        elif ratio_hist <= 2.0:
            signals.append(f"{hist_label}より高め（減速想定あり） ℹ️")
        else:
            warnings.append(f"{hist_label}の{ratio_hist:.1f}倍超 ⚠️")

    # --- チェック3: ファンダメンタル成長率（RR×ROIC）上限 ---
    if g_fundamental is not None and g_fundamental > 0:
        if phase1_growth <= g_fundamental * 1.2:
            signals.append(f"RR×ROIC上限({g_fundamental:.1%})以内 ✅")
        else:
            signals.append(f"RR×ROIC上限({g_fundamental:.1%})超（期待値先行型） ℹ️")

    # --- データ不足の場合 ---
    if not signals and not warnings:
        signals.append("ベンチマークデータ不足のため自動検証スキップ ℹ️")

    # --- 総合判定 ---
    if len(warnings) == 0:
        verdict = "PLAUSIBLE"
    elif len(warnings) == 1:
        verdict = "REVIEW"
    else:
        verdict = "AGGRESSIVE"

    # Damodaran キャッシュ年を取得
    damodaran_year = None
    if os.path.exists(_META_PATH):
        try:
            with open(_META_PATH, encoding="utf-8") as f:
                damodaran_year = json.load(f).get("year")
        except Exception:
            pass

    return {
        "verdict": verdict,
        "phase1_growth": phase1_growth,
        "industry_benchmark": industry_g,
        "damodaran_industry": benchmark["industry"] if benchmark else None,
        "damodaran_year": damodaran_year,
        "rev_cagr_3yr": cagr.get("cagr_3yr"),
        "rev_cagr_5yr": cagr.get("cagr_5yr"),
        "g_fundamental": g_fundamental,
        "signals": signals,
        "warnings": warnings,
    }
