"""
growth_sanity.py
æé·çãµããã£ãã§ãã¯ã¢ã¸ã¥ã¼ã«

è¨­å®ããã Phase1 æé·çãæ¥­çãã³ããã¼ã¯ã»éå»å®ç¸¾ã¨æ¯ã¹ã¦
æããã«éç¾å®çã§ãªãããæ¤è¨¼ããæ ¹æ ãµããªã¼ãçæããã
"""

import os
import json
import logging
import xlrd

logger = logging.getLogger(__name__)

# âââââââââââââââââââââââââââââââââââââââââââââ
# Damodaran ã­ã£ãã·ã¥ã®ãã¹
# ãã®ã¹ã¯ãªããã¯ src/value/tanuki_valuation/ ã«ãããã
# ãªãã¸ããªã«ã¼ããåºæºã«ããçµ¶å¯¾ãã¹ã§åç§ãã
# âââââââââââââââââââââââââââââââââââââââââââââ
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
_CACHE_DIR = os.path.join(_REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "common", "damodaran_cache")
_FUNDGR_PATH = os.path.join(_CACHE_DIR, "fundgrEB.xls")
_INDNAME_PATH = os.path.join(_CACHE_DIR, "indname.xls")
_META_PATH = os.path.join(_CACHE_DIR, "cache_meta.json")


# âââââââââââââââââââââââââââââââââââââââââââââ
# TANUKI sector â Damodaran Industry Name ãããã³ã°
#
# ãéè¦ãDamodaran ã®åé¡ã¯ SIC ã³ã¼ããã¼ã¹ã®ãã
# å®æã¨ä¹é¢ããéæãããï¼ä¾: MSFTâTrucking, ZSâSteelï¼ã
# ticker_overrides ã§åå¥ä¸æ¸ããåªåããã
# âââââââââââââââââââââââââââââââââââââââââââââ
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

# éæåå¥ã® Damodaran åé¡ä¸æ¸ã
# indname.xls ã§å®éã«ç¢ºèªãããããã³ã°ï¼SICãã¼ã¹åé¡ãå®æã¨ä¹é¢ããå ´åï¼
TICKER_INDUSTRY_OVERRIDES = {
    # æ­£ããåé¡ããã¦ããéæï¼ç¢ºèªæ¸ã¿ï¼
    "NVDA":  "Semiconductor",
    "AAPL":  "Computers/Peripherals",
    "CRWD":  "Software (System & Application)",
    "DDOG":  "Software (System & Application)",
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
    # SICãã¼ã¹åé¡ãå®æã¨ä¹é¢ â å®æã«è¿ãæ¥­ç¨®ã«ä¸æ¸ã
    "MSFT":  "Software (System & Application)",   # SICâTrucking ãä¸æ¸ã
    "NET":   "Software (System & Application)",   # SICâTelecom ãä¸æ¸ã
    "ZS":    "Software (System & Application)",   # SICâSteel ãä¸æ¸ã
    "SNOW":  "Software (System & Application)",   # SICâTransportation ãä¸æ¸ã
    "ANET":  "Telecom. Equipment",                # SICâTelecom.Services ãä¸æ¸ã
    "ARM":   "Semiconductor",                     # SICâTransportation ãä¸æ¸ã
    "CELH":  "Beverage (Soft)",                   # SICâSteel ãä¸æ¸ã
    "LUNR":  "Aerospace/Defense",                 # SICâMetals&Mining ãä¸æ¸ã
    "S":     "Software (System & Application)",   # SICâUtility(Water) ãä¸æ¸ã
    "DIS":   "Entertainment",                     # SICâReal Estate ãä¸æ¸ã
    "CEG":   "Power",                             # Constellation Energy
    "CIX":   "Machinery",                         # CompX International
    "LMT":   "Aerospace/Defense",                 # Lockheed Martin
}


# âââââââââââââââââââââââââââââââââââââââââââââ
# Damodaran ãã¼ã¿èª­ã¿è¾¼ã¿ï¼èµ·åæ1åã ãå®è¡ï¼
# âââââââââââââââââââââââââââââââââââââââââââââ
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
        # row7 ããããã¼: Industry Name / Number of Firms / ROC / Reinvestment Rate / Expected Growth in EBIT
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

        # ã­ã£ãã·ã¥å¹´ãç¢ºèªãã¦å¤ããã°è­¦å
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
    ticker ã¨ sector ãã Damodaran ã®æ¥­ç¨®ãã³ããã¼ã¯ãè¿ãã
    æ»ãå¤: {"industry": str, "g_ebit": float, "roc": float, "rr": float} or None
    """
    _load_damodaran()
    if not _damodaran_data:
        return None

    # åªåé ä½: tickeråå¥ä¸æ¸ã > sector ãããã³ã°
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


# âââââââââââââââââââââââââââââââââââââââââââââ
# Revenue CAGR è¨ç®
# âââââââââââââââââââââââââââââââââââââââââââââ
def calc_revenue_cagr(annual_revenues: list[float]) -> dict:
    """
    annual_revenues: å¤ãé ã®ãªã¹ã [rev_oldest, ..., rev_latest]
    æ»ãå¤: {"cagr_3yr": float|None, "cagr_5yr": float|None}
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


# âââââââââââââââââââââââââââââââââââââââââââââ
# ãã¡ã³ãã¡ã³ã¿ã«æé·çï¼RR Ã ROICï¼
# âââââââââââââââââââââââââââââââââââââââââââââ
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
    g = Reinvestment Rate Ã ROIC
    è¨ç®ä¸è½ï¼è² ã®ROICç­ï¼ã®å ´åã¯ None ãè¿ãã
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
        # ç°å¸¸å¤ãé¤å¤ï¼-100%ã+200%ã®ç¯å²å¤ï¼
        if not (-1.0 <= g <= 2.0):
            return None
        return g
    except Exception:
        return None


# âââââââââââââââââââââââââââââââââââââââââââââ
# ã¡ã¤ã³å¤å®é¢æ°
# âââââââââââââââââââââââââââââââââââââââââââââ
def check_growth_sanity(
    ticker: str,
    phase1_growth: float,
    sector: str | None = None,
    annual_revenues: list[float] | None = None,
    g_fundamental: float | None = None,
) -> dict:
    """
    æé·çãµããã£ãã§ãã¯ãå®è¡ããçµæ dict ãè¿ãã

    æ»ãå¤ä¾:
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

    # --- Damodaran ãã³ããã¼ã¯åå¾ ---
    benchmark = get_industry_benchmark(ticker, sector)
    industry_g = benchmark["g_ebit"] if benchmark else None

    # --- Revenue CAGR è¨ç® ---
    cagr = calc_revenue_cagr(annual_revenues or [])

    # --- ãã§ãã¯1: æ¥­çãã³ããã¼ã¯æ¯è¼ ---
    if industry_g is not None and industry_g > 0:
        ratio = phase1_growth / industry_g
        ind_label = f"{benchmark['industry']}({industry_g:.1%})"
        if ratio <= 1.5:
            signals.append(f"æ¥­çå¹³å{ind_label}ã®{ratio:.1f}åä»¥å â")
        elif ratio <= 2.5:
            signals.append(f"æ¥­çå¹³å{ind_label}ã®{ratio:.1f}å â¹ï¸")
        else:
            warnings.append(f"æ¥­çå¹³å{ind_label}ã®{ratio:.1f}åè¶ â ï¸")
    elif industry_g is not None and industry_g <= 0:
        # æ¥­çå¹³åããã¤ãã¹ã®å ´åï¼åç´æ¯è¼ä¸å¯ï¼
        signals.append(f"æ¥­çå¹³å({benchmark['industry']})ã¯ãã¤ãã¹æé·ãåå¥éæã®ç¬èªè©ä¾¡ãå¿è¦ â¹ï¸")

    # --- ãã§ãã¯2: éå»å®ç¸¾ CAGR æ¯è¼ ---
    historical_cagrs = [v for v in [cagr.get("cagr_3yr"), cagr.get("cagr_5yr")] if v and v > 0]
    if historical_cagrs:
        best = max(historical_cagrs)
        ratio_hist = phase1_growth / best
        label_3yr = f"{cagr['cagr_3yr']:.1%}" if cagr.get("cagr_3yr") else "N/A"
        label_5yr = f"{cagr['cagr_5yr']:.1%}" if cagr.get("cagr_5yr") else "N/A"
        hist_label = f"éå»å®ç¸¾(3yr:{label_3yr} / 5yr:{label_5yr})"
        if ratio_hist <= 1.3:
            signals.append(f"{hist_label}ã¨æ´å â")
        elif ratio_hist <= 2.0:
            signals.append(f"{hist_label}ããé«ãï¼æ¸éæ³å®ããï¼ â¹ï¸")
        else:
            warnings.append(f"{hist_label}ã®{ratio_hist:.1f}åè¶ â ï¸")

    # --- ãã§ãã¯3: ãã¡ã³ãã¡ã³ã¿ã«æé·çï¼RRÃROICï¼ä¸é ---
    if g_fundamental is not None and g_fundamental > 0:
        if phase1_growth <= g_fundamental * 1.2:
            signals.append(f"RRÃROICä¸é({g_fundamental:.1%})ä»¥å â")
        else:
            signals.append(f"RRÃROICä¸é({g_fundamental:.1%})è¶ï¼æå¾å¤åè¡åï¼ â¹ï¸")

    # --- ãã¼ã¿ä¸è¶³ã®å ´å ---
    if not signals and not warnings:
        signals.append("ãã³ããã¼ã¯ãã¼ã¿ä¸è¶³ã®ããèªåæ¤è¨¼ã¹ã­ãã â¹ï¸")

    # --- ç·åå¤å® ---
    if len(warnings) == 0:
        verdict = "PLAUSIBLE"
    elif len(warnings) == 1:
        verdict = "REVIEW"
    else:
        verdict = "AGGRESSIVE"

    # Damodaran ã­ã£ãã·ã¥å¹´ãåå¾
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
