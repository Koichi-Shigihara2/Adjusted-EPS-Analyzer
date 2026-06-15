#!/usr/bin/env python3
"""
report_consistency_check.py
全銘柄 report.txt の整合性一括チェック

検出項目:
  NG  1. FCF符号矛盾          FCF_History最新年マイナス & Matrix④ Key_Metric_Y 正値
  NG  2. DCF_Reliability欠落   FCF_Base行あり & DCF_Reliability行なし
  NG  3. LOW丸め未発動         DCF_Reliability=LOW & Classification が WATCH/SELL/PASS 以外
  NG  4. 割引率1段             Discount_Rate_Primary 行なし（旧WACC単独形式）
  NG  7. RPO条件違反           RPO_PV>0 & whitelist外 & RPO/Revenue<0.3
  NG  8. Matrix④高FCFラベル赤字 Matrix④ Label="高FCF" & 最新FCF実績マイナス
  NG  11. Revenue桁違い        annual_JSONの隣接年Revenue比が10倍超（誤XBRLタグ検出）
  WARN 5. NetDebt旧表示        Net_Debt行あり & ST_Invest 非ゼロ（latest.json）& 報告なし
  WARN 6. 負PER数値表示        Market_PER_GAAP が負数（N/M 未変換）
  WARN 9. セグメント設定陳腐化  segment_config fiscal_yearが2年以上前
  WARN 10. PS異常値            yfinance PSが自社計算値(price×shares/rev)の2.5倍超 or 0.4倍未満
  WARN 12. Cash-STI期ズレ      latest.jsonのCashが最新四半期値なのにST_Investが年次値のまま
  NG  13. RICE負値ラベルなし   rice.available=true かつ RICE<0 なのに Matrix Label に N/A/OCF赤字 なし
  NG  14. EPS>株価50%          EPS Analyzer直近Q adj_eps が株価の50%超（単位バグ検出）
  NG  15. EPS>株価             EPS Analyzer直近Q adj_eps が株価を上回る（単位バグ確実）
  WARN 16. TTM四半期不足       EPS Analyzer TTM計算に使用した四半期数が4未満
  NG  17. EPS全値$0.0          quarterly.json の全四半期 adj_eps=0.0（BUG-EPS-ZERO-1 回帰検知）
  WARN 18. G=15%デフォルト未調整 recommended_g あり & phase1_growth_auto_adjusted=False（DCF-DEFAULT-G-1 回帰）
  NG  19. SEC株数=0            quarterly.json に diluted_shares=0 の四半期（株数取得失敗）
"""

import os
import re
import json
import glob
import sys

# ─── パス設定 ────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.normpath(os.path.join(SCRIPT_DIR, "../.."))
DATA_DIR     = os.path.join(REPO_ROOT, "docs/value-monitor/tanuki_valuation/data")
SEC_DATA_DIR = os.path.join(REPO_ROOT, "common/sec_data/data")
EPS_DATA_DIR = os.path.join(REPO_ROOT, "docs/value-monitor/adjusted_eps_analyzer/data")
RPO_CONFIG   = os.path.join(REPO_ROOT, "config/rpo_config.json")
SEG_CONFIG   = os.path.join(REPO_ROOT, "config/segment_config.json")

_SEG_CFG_CACHE: dict = {}

def _load_seg_config() -> dict:
    global _SEG_CFG_CACHE
    if not _SEG_CFG_CACHE:
        try:
            with open(SEG_CONFIG, encoding="utf-8") as f:
                _SEG_CFG_CACHE = json.load(f)
        except Exception:
            pass
    return _SEG_CFG_CACHE


# ─── ユーティリティ ──────────────────────────────────────────

def _load_rpo_whitelist() -> set:
    try:
        with open(RPO_CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
        return set(cfg.get("whitelist", {}).keys())
    except Exception:
        return set()


def _read_report(ticker: str):
    path = os.path.join(DATA_DIR, ticker, "report.txt")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_latest(ticker: str) -> dict:
    path = os.path.join(DATA_DIR, ticker, "latest.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_eps_quarterly(ticker: str) -> list:
    path = os.path.join(EPS_DATA_DIR, ticker, "quarterly.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else d.get("quarters", [])
    except Exception:
        return []


# ─── パーサ ──────────────────────────────────────────────────

def _parse_report(text: str) -> dict:
    """report.txt から必要フィールドを抽出して dict で返す。"""
    lines = text.splitlines()

    result = {
        "classification": None,
        "dcf_reliability": None,
        "matrix_type": None,
        "key_metric_y": None,
        "label": None,
        "has_fcf_base": False,
        "discount_rate_primary_data": None,  # data行のみ（定義行は除外）
        "has_wacc_old": False,               # 旧 WACC: 単独行
        "has_net_debt_report": False,
        "has_st_invest_report": False,
        "per_gaap_value": None,
        "rpo_pv_value": None,
        "rpo_pv_line": None,
        "fcf_history": [],                   # [(year, neg_fcf, margin_or_None)]
        "_raw_lines": lines,                 # CHECK-9 用
    }

    in_fcf_section = False

    for line in lines:
        # FCF_History セクション
        if line.strip() == "FCF_History:":
            in_fcf_section = True
            continue
        if in_fcf_section:
            # 年次 FCF 行: "  2025: $-7.19B (FCF_Margin: -140.2%)"
            # または:      "  2023: $-0.27B"
            m = re.match(
                r'^\s{2}(\d{4}): \$([^\s(]+)'
                r'(?:\s+\(FCF_Margin:\s*([+-]?\d+\.?\d*)%\))?',
                line,
            )
            if m:
                year = int(m.group(1))
                fcf_str = m.group(2)   # e.g. "-7.19B" or "9.11B"
                neg_fcf = fcf_str.startswith("-")
                margin  = float(m.group(3)) if m.group(3) is not None else None
                result["fcf_history"].append((year, neg_fcf, margin))
                continue
            # 空行や次セクション開始でリセット
            if line.strip() == "" or (line and not line.startswith(" ")):
                in_fcf_section = False

        # Classification（最初のマッチのみ）
        if result["classification"] is None:
            m = re.match(r'^Classification:\s+(\S+)', line)
            if m:
                result["classification"] = m.group(1)

        # DCF_Reliability（データ行: "DCF_Reliability: LOW ⚠️..." or "...HIGH"）
        if result["dcf_reliability"] is None:
            m = re.match(r'^DCF_Reliability:\s+(\w+)', line)
            if m:
                result["dcf_reliability"] = m.group(1)  # "LOW" or "HIGH"

        # Matrix: （最初のマッチ）
        if result["matrix_type"] is None:
            m = re.match(r'^Matrix:\s+(.+)', line)
            if m:
                result["matrix_type"] = m.group(1).strip()

        # Key_Metric_Y: （最初のマッチ）
        if result["key_metric_y"] is None:
            m = re.match(r'^Key_Metric_Y:\s+(.+)', line)
            if m:
                result["key_metric_y"] = m.group(1).strip()

        # Label: （最初のマッチ）
        if result["label"] is None:
            m = re.match(r'^Label:\s+(.+)', line)
            if m:
                result["label"] = m.group(1).strip()

        # FCF_Base: 行の存在
        if not result["has_fcf_base"]:
            if re.match(r'^FCF_Base:', line):
                result["has_fcf_base"] = True

        # Discount_Rate_Primary データ行（"10.00% (DCF discount rate used)"）
        # 定義行は "Discount_Rate_Primary: Actual discount rate..." → 除外
        if result["discount_rate_primary_data"] is None:
            m = re.match(r'^Discount_Rate_Primary:\s+([\d.]+)%', line)
            if m:
                result["discount_rate_primary_data"] = m.group(1)

        # 旧 WACC: 単独行（"WACC: 12.0%"）
        if not result["has_wacc_old"]:
            if re.match(r'^WACC:\s+[\d.]+%', line):
                result["has_wacc_old"] = True

        # Net_Debt 行（Financial_Health セクション内 "  Net_Debt: ..."）
        if not result["has_net_debt_report"]:
            if re.match(r'^\s+Net_Debt:\s+\$', line):
                result["has_net_debt_report"] = True

        # ST_Invest 表記（"ST_Invest:" を含む行）
        if not result["has_st_invest_report"]:
            if "ST_Invest:" in line:
                result["has_st_invest_report"] = True

        # Market_PER_GAAP（Financial_Health セクション内）
        if result["per_gaap_value"] is None:
            m = re.match(r'^\s+Market_PER_GAAP:\s+(.+)', line)
            if m:
                result["per_gaap_value"] = m.group(1).strip()

        # RPO_PV データ行（"RPO_PV: $NNN ..."）
        if result["rpo_pv_value"] is None:
            m = re.match(r'^RPO_PV:\s+\$([0-9,]+)', line)
            if m:
                try:
                    result["rpo_pv_value"] = float(m.group(1).replace(",", ""))
                    result["rpo_pv_line"]  = line.strip()
                except ValueError:
                    pass

    return result


# ─── チェック本体 ─────────────────────────────────────────────

def check_ticker(ticker: str, whitelist: set) -> tuple[list, list]:
    """
    Returns (issues_ng, issues_warn)
    各要素は表示用文字列。
    """
    text = _read_report(ticker)
    if text is None:
        return [], []

    latest  = _read_latest(ticker)
    parsed  = _parse_report(text)
    ng: list[str]   = []
    warn: list[str] = []

    fcf_hist = parsed["fcf_history"]
    latest_entry = max(fcf_hist, key=lambda x: x[0]) if fcf_hist else None

    # ── CHECK 1: FCF符号矛盾 ─────────────────────────────────
    mt = parsed["matrix_type"] or ""
    kmy = parsed["key_metric_y"] or ""
    if "④" in mt and "FCF_Margin" in kmy and latest_entry:
        m = re.search(r'FCF_Margin\s*=\s*([+-]?\d+\.?\d*)%', kmy)
        if m:
            key_margin = float(m.group(1))
            _, latest_neg, latest_margin = latest_entry
            # 最新FCFがマイナスなのに Key_Metric_Y が正値
            if latest_neg and key_margin > 0:
                ng.append(
                    f"  [NG-1 FCF符号矛盾] 最新FCH({latest_entry[0]})マイナス"
                    f" & Key_Metric_Y FCF_Margin={key_margin:+.1f}%"
                )
                ng.append(f"    → {kmy}")

    # ── CHECK 2: DCF_Reliability欠落 ─────────────────────────
    if parsed["has_fcf_base"] and parsed["dcf_reliability"] is None:
        ng.append("  [NG-2 DCF_Reliability欠落] FCF_Base行あり & DCF_Reliability行なし")

    # ── CHECK 3: LOW丸め未発動 ───────────────────────────────
    rel = parsed["dcf_reliability"]
    cls = parsed["classification"]
    if rel == "LOW" and cls not in ("WATCH", "SELL", "PASS", None):
        ng.append(
            f"  [NG-3 LOW丸め未発動] DCF_Reliability=LOW & Classification={cls}"
        )

    # ── CHECK 4: 割引率1段 ───────────────────────────────────
    if parsed["discount_rate_primary_data"] is None:
        if parsed["has_wacc_old"]:
            ng.append("  [NG-4 割引率1段] Discount_Rate_Primary行なし・旧WACC単独形式")
        else:
            ng.append("  [NG-4 割引率1段] Discount_Rate_Primary行が存在しない")

    # ── CHECK 5: NetDebt旧表示 (警告) ────────────────────────
    if parsed["has_net_debt_report"] and not parsed["has_st_invest_report"]:
        fh = latest.get("financial_health", {}) or {}
        st_inv = fh.get("short_term_investments") or 0
        if st_inv and st_inv != 0.0:
            warn.append(
                f"  [WARN-5 NetDebt旧表示] Net_Debt行あり & ST_Invest非ゼロ({st_inv:,.0f})"
                " だが報告行なし"
            )

    # ── CHECK 6: 負PER数値表示 (警告) ───────────────────────
    pv = parsed["per_gaap_value"] or ""
    if re.match(r'^-[\d.]+', pv):
        warn.append(f"  [WARN-6 負PER数値表示] Market_PER_GAAP: {pv}  (N/M 未変換)")

    # ── CHECK 7: RPO条件違反 ─────────────────────────────────
    rpo_pv = parsed["rpo_pv_value"]
    if rpo_pv is not None and rpo_pv > 0 and ticker not in whitelist:
        comp    = latest.get("components", {}) or {}
        rpo_raw = comp.get("rpo") or 0
        rev_ttm = comp.get("latest_revenue") or 0
        if rev_ttm > 0 and rpo_raw > 0:
            ratio = rpo_raw / rev_ttm
            if ratio < 0.30:
                ng.append(
                    f"  [NG-7 RPO条件違反] RPO_PV={rpo_pv:,.0f} >0"
                    f" & whitelist外 & RPO/Rev={ratio:.2f}<0.30"
                )
                ng.append(f"    → {parsed['rpo_pv_line']}")

    # ── CHECK 8: Matrix④高FCFラベルだが実績赤字 ─────────────
    lbl = parsed["label"] or ""
    if "④" in mt and "高FCF" in lbl and latest_entry:
        _, latest_neg, _ = latest_entry
        if latest_neg:
            ng.append(
                f"  [NG-8 Matrix④高FCFラベル赤字]"
                f" Label={lbl!r} & 最新FCF({latest_entry[0]})実績マイナス"
            )

    # ── CHECK 9: セグメント設定鮮度 (警告) ──────────────────
    # segment_configのfiscal_yearが2年以上前の場合、陳腐化の可能性を警告
    seg_cfg = _load_seg_config().get(ticker, {})
    if seg_cfg.get("enabled") and seg_cfg.get("fiscal_year"):
        fy_str = seg_cfg["fiscal_year"]  # e.g. "FY2025"
        m_fy = re.match(r"FY(\d{4})", fy_str)
        if m_fy:
            fy_yr = int(m_fy.group(1))
            # report内のGenerated行から生成年を取得
            gen_yr = None
            for line in (parsed.get("_raw_lines") or []):
                mm = re.search(r"Generated: (\d{4})-", line)
                if mm:
                    gen_yr = int(mm.group(1))
                    break
            if gen_yr and (gen_yr - fy_yr) >= 2:
                warn.append(
                    f"  [WARN-9 セグメント設定陳腐化] segment_config fiscal_year={fy_str}"
                    f" (現在{gen_yr}年、{gen_yr - fy_yr}年前のデータ)"
                )

    # ── CHECK 10: PS異常値 (警告) ────────────────────────────
    # yfinance PSが自社計算値(price×shares/revenue)と大きく乖離する場合にWARN
    comp = latest.get("components", {}) or {}
    ps_yf   = comp.get("ps")
    price   = comp.get("current_price") or 0
    shares  = comp.get("diluted_shares") or 0
    rev     = comp.get("latest_revenue") or 0
    sector  = (comp.get("sector") or "").lower()
    is_fin  = "financial" in sector or "bank" in sector
    if ps_yf is not None and price and shares and rev and not is_fin:
        ps_calc = (price * shares) / rev
        if ps_calc > 0:
            ratio = ps_yf / ps_calc
            if ratio > 2.5 or ratio < 0.4:
                warn.append(
                    f"  [WARN-10 PS異常値] yfinance PS={ps_yf:.1f}x vs 自社計算={ps_calc:.1f}x"
                    f" (乖離{ratio:.1f}倍) → ステール値の可能性"
                )

    # ── CHECK 11: Revenue桁違い (NG) ──────────────────────────
    # BUG-REV-SPAC-1型の誤XBRLタグ検出。
    # 隣接年Revenue比が10倍超かつベース年 > $1M (スタートアップ微少値を除外) の場合はNG。
    # IONQ 2022: Revenuesタグが$1,235M(SPAC調達)を誤タグ → 正常年$11M との比 112倍
    sec_ticker_dir = os.path.join(SEC_DATA_DIR, ticker)
    if os.path.isdir(sec_ticker_dir):
        _annual_revs: dict[int, float] = {}
        for _fn in sorted(os.listdir(sec_ticker_dir)):
            if _fn.startswith("annual_") and _fn.endswith(".json") and _fn[7:11].isdigit():
                _yr = int(_fn[7:11])
                try:
                    with open(os.path.join(sec_ticker_dir, _fn), encoding="utf-8") as _f:
                        _d = json.load(_f)
                    _r = _d.get("pl", {}).get("revenue")
                    if _r is not None:
                        _annual_revs[_yr] = _r
                except Exception:
                    pass
        _yrs = sorted(_annual_revs.keys())
        for _i, _yr in enumerate(_yrs):
            _r = _annual_revs[_yr]
            if _r <= 1_000_000:
                continue  # スタートアップ微少値はスキップ
            # 孤立年チェック: 前後両年が存在し、どちらも当該年の5%未満 → 誤XBRLタグ疑い
            # (IONQ 2022: 前=$2.1M/後=$22M vs $1,235M → どちらも1.8%以下 → 異常)
            # (ASTS 2025: 後年データなし → 正常な高成長トレンドとして除外)
            _prev = _annual_revs.get(_yrs[_i - 1]) if _i > 0 else None
            _next = _annual_revs.get(_yrs[_i + 1]) if _i < len(_yrs) - 1 else None
            if _prev is None or _next is None:
                continue  # 両端年はスキップ（孤立か判定不能）
            if _prev <= 0 or _next <= 0:
                continue
            _threshold = _r * 0.05  # 前後が当該年の5%未満なら異常
            if _prev < _threshold and _next < _threshold:
                _ratio_prev = _r / _prev
                _ratio_next = _r / _next
                ng.append(
                    f"  [NG-11 Revenue孤立年] {_yr}=${_r/1e6:.1f}M"
                    f" (前年{_yrs[_i-1]}=${_prev/1e6:.1f}M: {_ratio_prev:.0f}x,"
                    f" 翌年{_yrs[_i+1]}=${_next/1e6:.1f}M: {_ratio_next:.0f}x)"
                    f" → XBRLタグ誤り疑い(TICKER_RESTRICTIONSで修正)"
                )

    # CHECK-12: Cash-ST_Invest 期整合チェック（BUG-NETDEBT-5回帰検知）
    # Cashが最新四半期値に更新されているのにST_Investが年次のままなら期ズレ
    _ann_files_c12 = sorted(glob.glob(os.path.join(SEC_DATA_DIR, ticker, "annual_*.json")))
    _q_files_c12   = sorted(glob.glob(os.path.join(SEC_DATA_DIR, ticker, "quarterly_*.json")))
    if _ann_files_c12 and _q_files_c12:
        try:
            with open(_ann_files_c12[-1], encoding="utf-8") as _f12:
                _ann12 = json.load(_f12)
            with open(_q_files_c12[-1], encoding="utf-8") as _f12q:
                _q12   = json.load(_f12q)
            _ann_period12 = _ann12.get("period", "")
            _q_period12   = _q12.get("period", "")
            if _ann_period12 != _q_period12:
                _ann_bs12  = _ann12.get("bs", {})
                _q_bs12    = _q12.get("bs", {})
                _ann_cash12 = _ann_bs12.get("cash_and_equivalents") or 0
                _q_cash12   = _q_bs12.get("cash_and_equivalents") or 0
                _ann_sti12  = _ann_bs12.get("short_term_investments") or 0
                _q_sti12    = _q_bs12.get("short_term_investments") or 0
                # Cashが四半期値に更新済み かつ ST_Investが存在し値が変化する場合のみチェック
                if _q_cash12 != _ann_cash12 and _q_sti12 > 0 and _q_sti12 != _ann_sti12:
                    _fh12     = latest.get("financial_health", {})
                    _rep_cash = _fh12.get("cash_and_equivalents") or 0
                    _rep_sti  = _fh12.get("short_term_investments") or 0
                    # レポートCash≈四半期値 かつ レポートSTI≈年次値 かつ STI≠四半期値 → 期ズレ未修正
                    # （quarterly STI ≈ annual STI の偽陽性を除外: PLTR/QBTS など）
                    _cash_ok = abs(_rep_cash - _q_cash12) < max(1_000_000, _q_cash12 * 0.01)
                    _sti_stale = abs(_rep_sti - _ann_sti12) < max(1_000_000, _ann_sti12 * 0.01)
                    _sti_already_qtr = abs(_rep_sti - _q_sti12) < max(1_000_000, _q_sti12 * 0.01)
                    if _cash_ok and _sti_stale and not _sti_already_qtr:
                        warn.append(
                            f"  [WARN-12 Cash-STI期ズレ] Cash={_rep_cash/1e6:.0f}M({_q_period12})"
                            f" だがST_Invest={_rep_sti/1e6:.0f}M(年次{_ann_period12})のまま"
                            f" → 正={_q_sti12/1e6:.0f}M"
                        )
        except Exception:
            pass

    # CHECK-13: RICE負値ラベル確認（RICE-3 回帰検知）
    # rice.available=true かつ BASE RICE < 0 なら Matrix Label が "N/A" か "OCF赤字" を含むこと
    _rice_ld = latest.get("rice", {})
    if _rice_ld.get("available", False):
        _rice_base_val = (_rice_ld.get("base") or {}).get("rice")
        if _rice_base_val is not None and _rice_base_val < 0:
            _label_c13 = parsed.get("label", "") or ""
            if "N/A" not in _label_c13 and "OCF赤字" not in _label_c13:
                ng.append(
                    f"  [NG-13 RICE負値ラベルなし] BASE RICE={_rice_base_val:.3f} "
                    f"だが Label='{_label_c13}' に 'N/A (OCF赤字)' なし"
                )

    # CHECK-14/15: EPS異常値チェック（単位バグ・大型一時利益検出）
    # EPS Analyzer quarterly.json の直近Q adj_eps / gaap_eps を株価と比較する
    _price_c14 = None
    for _pline in parsed.get("_raw_lines", []):
        _pm = re.match(r'^Price:\s*\$([0-9,.]+)', _pline.strip())
        if _pm:
            try:
                _price_c14 = float(_pm.group(1).replace(",", ""))
            except Exception:
                pass
            break

    if _price_c14 and _price_c14 > 0:
        _eps_qs = _read_eps_quarterly(ticker)
        if _eps_qs:
            _latest_q = sorted(_eps_qs, key=lambda x: x.get("filing_date", ""))[-1]
            _latest_adj = abs(_latest_q.get("adjusted_eps", 0) or 0)
            _latest_gaap = abs(_latest_q.get("gaap_eps", 0) or 0)
            _max_eps = max(_latest_adj, _latest_gaap)
            if _max_eps > _price_c14:
                ng.append(
                    f"  [NG-15 EPS>株価] 直近Q adj_eps={_latest_adj:.2f} gaap_eps={_latest_gaap:.2f}"
                    f" > Price=${_price_c14:.2f}"
                    f" (filing:{_latest_q.get('filing_date','?')})"
                )
            elif _max_eps > _price_c14 * 0.5:
                ng.append(
                    f"  [NG-14 EPS>株価50%] 直近Q adj_eps={_latest_adj:.2f} gaap_eps={_latest_gaap:.2f}"
                    f" > Price*0.5=${_price_c14 * 0.5:.2f}"
                    f" (filing:{_latest_q.get('filing_date','?')})"
                )

            # CHECK-16: TTM計算に使われる四半期数チェック（4件未満は不完全なTTM）
            _recent = sorted(
                [q for q in _eps_qs if q.get("filing_date", "") >= "2023-01-01"],
                key=lambda x: x.get("filing_date", ""),
                reverse=True
            )
            if 0 < len(_recent) < 4:
                warn.append(
                    f"  [WARN-16 TTM四半期不足] EPS Analyzer TTM計算に{len(_recent)}四半期しかない（4必要）"
                )

    # CHECK-17: EPS全値$0.0（BUG-EPS-ZERO-1 回帰検知）
    # 直近3年の四半期で全てadj_eps=gaap_eps=0.0の場合、株式数取得失敗の可能性
    _eps_qs_c17 = _read_eps_quarterly(ticker)
    _recent_c17 = [q for q in _eps_qs_c17 if (q.get("filing_date") or "") >= "2022-01-01"]
    if len(_recent_c17) >= 2:
        _all_adj_zero = all(abs(q.get("adjusted_eps") or 0) < 1e-9 for q in _recent_c17)
        _all_gaap_zero = all(abs(q.get("gaap_eps") or 0) < 1e-9 for q in _recent_c17)
        if _all_adj_zero and _all_gaap_zero:
            ng.append(
                f"  [NG-17 EPS全値$0.0] 直近{len(_recent_c17)}四半期すべてadj_eps=gaap_eps=0.0"
                f" → 株式数取得失敗疑い(BUG-EPS-ZERO-1 回帰)"
            )

    # CHECK-18: G=15%デフォルト未調整（DCF-DEFAULT-G-1 回帰検知）
    # recommended_gがあるのにphase1_growth_auto_adjusted=Falseかつ成長率が15%のままならWARN
    _g_c18 = latest.get("growth") or {}
    _rate_c18 = _g_c18.get("rate")
    _source_c18 = _g_c18.get("source", "")
    _rec_g_c18 = latest.get("recommended_g")
    _auto_adj_c18 = latest.get("phase1_growth_auto_adjusted", False)
    if (
        _rate_c18 is not None
        and _rec_g_c18 is not None
        and not _auto_adj_c18
        and _source_c18 != "segment_weighted"  # segment_configによる意図的設定は除外
        and abs(_rate_c18 - 0.15) < 0.002      # 15%デフォルトのまま
        and abs(_rate_c18 - _rec_g_c18) > 0.05 # recommended_gと5%以上乖離
    ):
        warn.append(
            f"  [WARN-18 G=15%デフォルト未調整] growth.rate={_rate_c18:.1%}"
            f" & recommended_g={_rec_g_c18:.1%} だがauto_adjusted=False"
            f" → DCF-DEFAULT-G-1 回帰の可能性"
        )

    # CHECK-19: SEC株数=0（BUG-EPS-ZERO-1 回帰検知）
    # 直近3年の四半期でdiluted_shares=0かつnet_income非ゼロの場合はNG
    _eps_qs_c19 = _read_eps_quarterly(ticker)
    _recent_c19 = [q for q in _eps_qs_c19 if (q.get("filing_date") or "") >= "2022-01-01"]
    _zero_shares_c19 = [
        q for q in _recent_c19
        if (q.get("gaap_net_income") or 0) != 0 and (q.get("diluted_shares") or 0) == 0
    ]
    if _zero_shares_c19:
        _dates_c19 = [q.get("filing_date", "?") for q in _zero_shares_c19[:3]]
        ng.append(
            f"  [NG-19 SEC株数=0] {len(_zero_shares_c19)}四半期でdiluted_shares=0"
            f" (例: {', '.join(_dates_c19)})"
            f" → 株式数取得失敗(BUG-EPS-ZERO-1 回帰)"
        )

    return ng, warn


# ─── メイン ──────────────────────────────────────────────────

def main():
    whitelist = _load_rpo_whitelist()

    tickers = sorted([
        d for d in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, d))
        and os.path.exists(os.path.join(DATA_DIR, d, "report.txt"))
    ])

    print(f"=== TANUKI VALUATION report.txt 整合性チェック ({len(tickers)} 銘柄) ===\n")

    total_ng   = 0
    total_warn = 0
    flagged: list[tuple[str, list, list]] = []

    for ticker in tickers:
        ng, warn = check_ticker(ticker, whitelist)
        if ng or warn:
            flagged.append((ticker, ng, warn))
            total_ng   += len(ng)
            total_warn += len(warn)

    if not flagged:
        print("✅ 全銘柄整合 — NG=0 / 警告=0\n")
    else:
        for ticker, ng, warn in flagged:
            icon = "❌" if ng else "⚠️"
            print(f"{icon} {ticker}")
            for item in ng:
                print(item)
            for item in warn:
                print(item)
            print()

    print("─" * 50)
    print(f"合計: NG={total_ng} 件 / 警告={total_warn} 件  (対象 {len(tickers)} 銘柄)")
    if total_ng == 0:
        print("✅ NG=0 全銘柄整合")
    return total_ng


if __name__ == "__main__":
    rc = main()
    sys.exit(0 if rc == 0 else 1)
