#!/usr/bin/env python3
"""
登録パイプライン健全性チェッカー
-----------------------------------------------------------------------
Usage:
    python common/sec_data/registration_validator.py          # 全銘柄
    python common/sec_data/registration_validator.py AAPL     # 単体
    python common/sec_data/registration_validator.py --summary # サマリーのみ

チェック項目:
    P1. 7ステップ登録完全性 (SEC/Beta/Valuation/HypeCore/Discover/Monitor)
    P2. データ品質・鮮度 (latest_revenue TTM乖離、旧XBRL形式、TTM陳腐化)
    P3. segment_config 整合性 (fiscal_year鮮度、weight合計、growth率)
    P4. Config 孤立エントリ (discover_config/cik_lookup の非監視残存)
    P5. 自動更新ワークフロー カバレッジ
"""
import json
import os
import re
import sys
from datetime import date, datetime
from typing import Optional

# ── パス解決 ──────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT   = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", ".."))

SEC_DATA_DIR = os.path.join(_REPO_ROOT, "common", "sec_data", "data")
TTM_DIR      = os.path.join(_REPO_ROOT, "common", "sec_data", "ttm")
TANUKI_DIR   = os.path.join(_REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "data")
HYPECORE_DIR = os.path.join(_REPO_ROOT, "docs", "value-monitor", "hypecore", "data")
EPS_DIR      = os.path.join(_REPO_ROOT, "docs", "value-monitor", "adjusted_eps_analyzer", "data")
BETA_CFG     = os.path.join(_REPO_ROOT, "config", "beta_config.json")
SEG_CFG      = os.path.join(_REPO_ROOT, "config", "segment_config.json")
DISCOVER_CFG = os.path.join(_REPO_ROOT, "config", "discover_config.json")
CIK_CSV      = os.path.join(_REPO_ROOT, "config", "cik_lookup.csv")
MONITOR_YAML = os.path.join(_REPO_ROOT, "config", "monitor_tickers.yaml")

TODAY = date.today()

# ── ヘルパー ──────────────────────────────────────────────────────────

def _load_monitor_tickers() -> list[str]:
    with open(MONITOR_YAML, encoding="utf-8") as f:
        return sorted([l.strip().lstrip("- ") for l in f if l.strip().startswith("- ")])


def _load_json(path: str) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _annual_files(ticker: str) -> list[str]:
    d = os.path.join(SEC_DATA_DIR, ticker)
    if not os.path.isdir(d):
        return []
    return sorted([f for f in os.listdir(d) if re.match(r"annual_\d{4}\.json$", f)])


def _max_annual_year(ticker: str) -> Optional[int]:
    files = _annual_files(ticker)
    if not files:
        return None
    return max(int(f[7:11]) for f in files)


def _ttm_end(ticker: str) -> Optional[str]:
    path = os.path.join(TTM_DIR, f"{ticker}_ttm_series.json")
    d = _load_json(path)
    if d and d.get("series"):
        return d["series"][0].get("ttm_end")
    return None


def _ttm_revenue(ticker: str) -> Optional[float]:
    path = os.path.join(TTM_DIR, f"{ticker}_ttm_series.json")
    d = _load_json(path)
    if not d or not d.get("series"):
        return None
    rv = d["series"][0].get("flow", {}).get("Revenue")
    if isinstance(rv, dict):
        return rv.get("val")
    return rv


def _latest_json(ticker: str) -> Optional[dict]:
    return _load_json(os.path.join(TANUKI_DIR, ticker, "latest.json"))


def _fy_year(fy_str: str) -> Optional[int]:
    """'FY2025' or '2025' -> 2025"""
    if not fy_str:
        return None
    m = re.search(r"(20\d{2})", str(fy_str))
    return int(m.group(1)) if m else None


# ── Issue コレクター ───────────────────────────────────────────────────

class Issues:
    def __init__(self) -> None:
        self._items: list[tuple[str, str, str]] = []  # (sev, category, msg)

    def ng(self, cat: str, msg: str) -> None:
        self._items.append(("NG", cat, msg))

    def warn(self, cat: str, msg: str) -> None:
        self._items.append(("WARN", cat, msg))

    def info(self, cat: str, msg: str) -> None:
        self._items.append(("INFO", cat, msg))

    def count_ng(self) -> int:
        return sum(1 for s, _, _ in self._items if s == "NG")

    def count_warn(self) -> int:
        return sum(1 for s, _, _ in self._items if s == "WARN")

    def all(self) -> list[tuple[str, str, str]]:
        return list(self._items)


# ═══════════════════════════════════════════════════════════════════════
# P1: 7ステップ登録完全性チェック
# ═══════════════════════════════════════════════════════════════════════

def check_p1_registration_completeness(ticker: str, issues: Issues,
                                        beta_overrides: dict,
                                        discover_tickers: set,
                                        monitor_set: set) -> None:
    """7ステップ各段のデータ存在確認"""

    # Step 1: SEC annual data
    annual = _annual_files(ticker)
    if not annual:
        issues.ng("P1-Step1-SEC", f"{ticker}: SEC annual data なし (common/sec_data/data/{ticker}/)")
    elif len(annual) < 3:
        issues.warn("P1-Step1-SEC", f"{ticker}: SEC annual data が {len(annual)} 件のみ (<3件、上場直後?)")

    # Step 2: Beta config
    if ticker not in beta_overrides:
        issues.warn("P1-Step2-Beta", f"{ticker}: beta_config.json に override なし (raw yfinance 値使用中)")

    # Step 3: Valuation (latest.json)
    lj_path = os.path.join(TANUKI_DIR, ticker, "latest.json")
    if not os.path.exists(lj_path):
        issues.ng("P1-Step3-Valuation", f"{ticker}: latest.json 未生成 (pipeline 未実行?)")

    # Step 4: Audit – runtime チェックのため skip（別途 audit.py で実行）

    # Step 5: HypeCore poc.json
    poc_path = os.path.join(HYPECORE_DIR, f"{ticker}_poc.json")
    if not os.path.exists(poc_path):
        issues.warn("P1-Step5-HypeCore", f"{ticker}: _poc.json 未生成 (hypecore 未実行?)")

    # Step 5.5: EPS analyzer
    eps_path = os.path.join(EPS_DIR, ticker)
    if not os.path.exists(eps_path):
        issues.warn("P1-Step5b-EPS", f"{ticker}: EPS analyzer データなし")

    # Step 6: discover_config
    if ticker not in discover_tickers:
        issues.ng("P1-Step6-Discover", f"{ticker}: discover_config.json に未登録")

    # Step 7: monitor_tickers.yaml
    if ticker not in monitor_set:
        issues.ng("P1-Step7-Monitor", f"{ticker}: monitor_tickers.yaml に未登録 (自動更新対象外)")


# ═══════════════════════════════════════════════════════════════════════
# P2: データ品質・鮮度チェック
# ═══════════════════════════════════════════════════════════════════════

def check_p2_data_quality(ticker: str, issues: Issues) -> None:

    lj = _latest_json(ticker)
    comps = (lj or {}).get("components", {})

    # ── A: latest_revenue TTM 乖離 ───────────────────────────────────
    annual_rev = comps.get("latest_revenue") or 0
    ttm_rev = _ttm_revenue(ticker)
    sector = comps.get("sector", "")

    if annual_rev and ttm_rev:
        ratio = ttm_rev / annual_rev
        # 金融セクターは revenue 定義が異なるため特別扱い
        fin_sectors = {"Financial Services", "Financial", "Banks", "Insurance"}
        is_financial = any(fs.lower() in (sector or "").lower() for fs in fin_sectors)

        if ratio >= 3.0:
            sev = "WARN" if is_financial else "NG"
            issues.ng("P2-A-RevTTM", f"{ticker}: latest_revenue=${annual_rev/1e9:.2f}B <<"
                      f" TTM=${ttm_rev/1e9:.2f}B (ratio={ratio:.1f}x) "
                      f"{'[金融セクター: revenue定義差の可能性]' if is_financial else '[SEC parserバグ疑い]'}")
        elif ratio >= 1.5:
            issues.warn("P2-A-RevTTM", f"{ticker}: latest_revenue(annual)=${annual_rev/1e9:.2f}B"
                        f" < TTM=${ttm_rev/1e9:.2f}B (ratio={ratio:.1f}x) "
                        f"[高成長: TTM反映推奨]")

    # ── B: 旧XBRL形式 (net_income=None in recent years 2022+) ────────
    annual_files = _annual_files(ticker)
    recent_none_years = []
    for fn in annual_files:
        yr = int(fn[7:11])
        if yr < 2022:
            continue  # 旧データは許容
        d = _load_json(os.path.join(SEC_DATA_DIR, ticker, fn))
        if d and d.get("pl", {}).get("net_income") is None and d.get("pl", {}).get("revenue"):
            recent_none_years.append(yr)
    if recent_none_years:
        issues.warn("P2-B-XBRL", f"{ticker}: net_income=None in recent years={recent_none_years}"
                    " (旧XBRL形式 → ROE計算でEPSフォールバック使用中)")

    # ── C: 年次データ陳腐化 ──────────────────────────────────────────
    max_yr = _max_annual_year(ticker)
    if max_yr is not None:
        lag = TODAY.year - max_yr
        if lag >= 3:
            issues.ng("P2-C-AnnualStale", f"{ticker}: 最新年次={max_yr} ({lag}年前) SEC取得が止まっている")
        elif lag == 2:
            issues.warn("P2-C-AnnualStale", f"{ticker}: 最新年次={max_yr} ({lag}年前) 要確認")

    # ── D: TTM 陳腐化 ─────────────────────────────────────────────────
    ttm_end_str = _ttm_end(ticker)
    if ttm_end_str:
        try:
            ttm_end_d = date.fromisoformat(ttm_end_str[:10])
            days_old = (TODAY - ttm_end_d).days
            if days_old > 200:
                issues.warn("P2-D-TTMStale", f"{ticker}: ttm_end={ttm_end_str} ({days_old}日前)"
                            " TTM更新が6ヶ月以上停止")
        except Exception:
            pass

    # ── E: Valuation calculation_date 陳腐化 ──────────────────────────
    if lj:
        calc_date_str = (lj.get("calculation_date") or "")[:10]
        if calc_date_str:
            try:
                calc_d = date.fromisoformat(calc_date_str)
                days_old = (TODAY - calc_d).days
                if days_old > 30:
                    issues.warn("P2-E-ValStale", f"{ticker}: calculation_date={calc_date_str}"
                                f" ({days_old}日前) 再生成推奨")
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════
# P3: segment_config 整合性チェック
# ═══════════════════════════════════════════════════════════════════════

def check_p3_segment_config(issues: Issues) -> None:
    seg = _load_json(SEG_CFG) or {}
    for ticker, conf in seg.items():
        if ticker.startswith("_"):
            continue
        segs = conf.get("segments", {})
        fy_str = str(conf.get("fiscal_year", ""))
        fy_year = _fy_year(fy_str)

        # fiscal_year 鮮度
        if fy_year:
            lag = TODAY.year - fy_year
            if lag >= 2:
                issues.ng("P3-SegFY", f"{ticker}: segment_config fiscal_year={fy_str}"
                          f" ({lag}年前) 要更新 [成長率ウェイトが古い]")
            # lag==1 は現在 FY2025 が正常 → WARN なし
        elif segs and not all(s == "General" for s in segs):
            issues.warn("P3-SegFY", f"{ticker}: fiscal_year 未設定 (セグメントあり)")

        # weight 合計検証
        if segs:
            total_w = sum(float(v.get("weight", 0)) for v in segs.values())
            if abs(total_w - 1.0) > 0.05:
                issues.ng("P3-SegWeight", f"{ticker}: weight合計={total_w:.3f} (≠1.0)"
                          " [Segment_Weighted_Growth が不正になる]")

        # growth 率異常値
        for seg_name, sv in segs.items():
            g = sv.get("growth")
            if g is not None:
                if g < -0.5 or g > 3.0:
                    issues.warn("P3-SegGrowth", f"{ticker}/{seg_name}: growth={g:.1%}"
                                " (範囲外: -50%~+300%)")


# ═══════════════════════════════════════════════════════════════════════
# P4: Config 孤立エントリチェック
# ═══════════════════════════════════════════════════════════════════════

def check_p4_orphan_configs(issues: Issues, monitor_set: set) -> None:

    # discover_config の非監視残存
    disc = _load_json(DISCOVER_CFG) or {}
    disc_tickers = set(disc.get("tickers", {}).keys())
    for t in sorted(disc_tickers - monitor_set):
        issues.warn("P4-DiscoverOrphan", f"{t}: discover_config.json に残存するが monitor_tickers 未登録"
                    " [削除漏れ?]")

    # cik_lookup の非監視残存 (annual data あり)
    try:
        with open(CIK_CSV, encoding="utf-8") as f:
            import csv
            cik_tickers = {row["ticker"].strip() for row in csv.DictReader(f)
                           if row.get("ticker", "").strip()}
    except Exception:
        cik_tickers = set()

    for t in sorted(cik_tickers - monitor_set - {"ticker", "TICKER"}):
        if t.startswith("_"):
            continue
        sec_dir = os.path.join(SEC_DATA_DIR, t)
        has_annual = os.path.isdir(sec_dir) and any(
            re.match(r"annual_\d{4}\.json$", f) for f in os.listdir(sec_dir)
        ) if os.path.isdir(sec_dir) else False
        if has_annual:
            issues.warn("P4-CIKOrphan", f"{t}: cik_lookup に登録済み+SEC data あり だが"
                        " monitor_tickers 未登録 [inactive?]")
        else:
            # SEC data なし = 登録途中の可能性
            company_facts = os.path.exists(os.path.join(sec_dir, "company_facts.json"))
            if company_facts or os.path.isdir(sec_dir):
                issues.warn("P4-CIKIncomplete", f"{t}: cik_lookup 登録済みだが annual data 未取得"
                            " (登録途中 or SEC fetch 失敗?)")

    # SEC data dir があるが monitor 未登録 かつ cik_lookup にも未登録の銘柄のみ報告
    # (cik_lookup 登録済みは P4-C / P4-CI で既に報告されるため除外)
    if os.path.isdir(SEC_DATA_DIR):
        for t in sorted(os.listdir(SEC_DATA_DIR)):
            if not os.path.isdir(os.path.join(SEC_DATA_DIR, t)):
                continue
            if t in monitor_set or t.startswith("--") or t.startswith("_"):
                continue
            if t in cik_tickers:
                continue  # P4-C or P4-CI で報告済み
            issues.warn("P4-SecDataOrphan", f"{t}: SEC data dir あり だが monitor・cik_lookup 未登録")


# ═══════════════════════════════════════════════════════════════════════
# P5: 自動更新ワークフロー カバレッジ
# ═══════════════════════════════════════════════════════════════════════

def check_p5_workflow_coverage(issues: Issues, monitor_set: set) -> None:
    """
    SEC_Data_Update は cik_lookup.csv から get_all() で ticker を取得する。
    monitor_tickers.yaml 未登録銘柄は TANUKI_VALUATION_Update の対象外になる。
    （pipeline.py は引数なしで tanuki data dir を走査するため実質カバー済みだが念のため確認）
    """
    # tanuki data に latest.json がある銘柄 vs monitor_tickers
    tanuki_tickers = set()
    if os.path.isdir(TANUKI_DIR):
        for t in os.listdir(TANUKI_DIR):
            if os.path.exists(os.path.join(TANUKI_DIR, t, "latest.json")):
                tanuki_tickers.add(t)

    uncovered = sorted(tanuki_tickers - monitor_set)
    if uncovered:
        issues.warn("P5-WorkflowGap", f"tanuki latest.json があるが monitor 未登録: {uncovered}"
                    " [自動更新ワークフローの対象外]")

    # TANUKI_VALUATION_Update が weekdays 実行か確認
    wf_path = os.path.join(_REPO_ROOT, ".github", "workflows", "TANUKI_VALUATION_Update.yml")
    if os.path.exists(wf_path):
        with open(wf_path, encoding="utf-8") as f:
            wf_content = f.read()
        if "weekday" not in wf_content and "1-5" not in wf_content and "schedule" not in wf_content:
            issues.warn("P5-WorkflowSchedule", "TANUKI_VALUATION_Update.yml に schedule 設定が見つからない")


# ═══════════════════════════════════════════════════════════════════════
# メイン
# ═══════════════════════════════════════════════════════════════════════

def run(target_tickers: Optional[list] = None, summary_only: bool = False) -> Issues:
    monitor_tickers = _load_monitor_tickers()
    monitor_set = set(monitor_tickers)

    beta = _load_json(BETA_CFG) or {}
    beta_overrides = beta.get("overrides", {})

    disc = _load_json(DISCOVER_CFG) or {}
    discover_tickers = set(disc.get("tickers", {}).keys())

    tickers_to_check = target_tickers if target_tickers else monitor_tickers

    all_issues = Issues()

    # ── P1 / P2: 銘柄ごとチェック ────────────────────────────────────
    for t in tickers_to_check:
        check_p1_registration_completeness(t, all_issues, beta_overrides,
                                           discover_tickers, monitor_set)
        check_p2_data_quality(t, all_issues)

    # ── P3: segment_config（全銘柄対象）──────────────────────────────
    check_p3_segment_config(all_issues)

    # ── P4: Config孤立（全体チェック）────────────────────────────────
    check_p4_orphan_configs(all_issues, monitor_set)

    # ── P5: ワークフローカバレッジ ────────────────────────────────────
    check_p5_workflow_coverage(all_issues, monitor_set)

    # ── レポート出力 ──────────────────────────────────────────────────
    _print_report(all_issues, len(tickers_to_check), summary_only)

    return all_issues


def _print_report(issues: Issues, n_tickers: int, summary_only: bool) -> None:
    items = issues.all()
    ng_items   = [(c, m) for s, c, m in items if s == "NG"]
    warn_items = [(c, m) for s, c, m in items if s == "WARN"]

    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║  登録パイプライン健全性チェック ({n_tickers} 銘柄)  {TODAY}  ║")
    print(f"╚══════════════════════════════════════════════════════════╝")
    print()

    # カテゴリ別グルーピング
    cats_ng: dict[str, list[str]] = {}
    cats_warn: dict[str, list[str]] = {}
    for cat, msg in ng_items:
        cats_ng.setdefault(cat, []).append(msg)
    for cat, msg in warn_items:
        cats_warn.setdefault(cat, []).append(msg)

    _CAT_LABELS = {
        "P1-Step1-SEC":      "P1-Step1  SEC data 未取得",
        "P1-Step2-Beta":     "P1-Step2  Beta 未設定",
        "P1-Step3-Valuation":"P1-Step3  Valuation 未生成",
        "P1-Step5-HypeCore": "P1-Step5  HypeCore 未実行",
        "P1-Step5b-EPS":     "P1-Step5b EPS Analyzer なし",
        "P1-Step6-Discover": "P1-Step6  Discover 未登録",
        "P1-Step7-Monitor":  "P1-Step7  monitor_tickers 未登録",
        "P2-A-RevTTM":       "P2-A  latest_revenue TTM乖離",
        "P2-B-XBRL":         "P2-B  旧XBRL (net_income=None)",
        "P2-C-AnnualStale":  "P2-C  年次データ陳腐化",
        "P2-D-TTMStale":     "P2-D  TTM陳腐化(>6ヶ月)",
        "P2-E-ValStale":     "P2-E  Valuation陳腐化(>30日)",
        "P3-SegFY":          "P3-FY segment fiscal_year鮮度",
        "P3-SegWeight":      "P3-W  segment weight合計不正",
        "P3-SegGrowth":      "P3-G  segment growth率異常",
        "P4-DiscoverOrphan": "P4-D  discover_config孤立エントリ",
        "P4-CIKOrphan":      "P4-C  cik_lookup孤立エントリ",
        "P4-CIKIncomplete":  "P4-CI cik_lookup登録途中",
        "P4-SecDataOrphan":  "P4-S  SEC data孤立ディレクトリ",
        "P5-WorkflowGap":    "P5    ワークフローカバレッジ外",
        "P5-WorkflowSchedule":"P5   ワークフロースケジュール",
    }

    def _print_section(label: str, cats: dict[str, list[str]], icon: str) -> None:
        if not cats:
            return
        for cat, msgs in sorted(cats.items()):
            cat_label = _CAT_LABELS.get(cat, cat)
            print(f"{icon} [{cat_label}]  ({len(msgs)}件)")
            if not summary_only:
                for m in msgs:
                    print(f"     {m}")
            print()

    if ng_items:
        print(f"━━━━━ ❌ NG ({len(ng_items)}件) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _print_section("", cats_ng, "❌")
    else:
        print("━━━━━ ❌ NG: 0件 ✅ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

    if warn_items:
        print(f"━━━━━ ⚠️  WARN ({len(warn_items)}件) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _print_section("", cats_warn, "⚠️ ")
    else:
        print("━━━━━ ⚠️  WARN: 0件 ✅ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

    print("─" * 60)
    print(f"合計: NG={len(ng_items)} / WARN={len(warn_items)}  "
          f"(対象={n_tickers}銘柄  日付={TODAY})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    summary_only = "--summary" in sys.argv

    if args:
        run(target_tickers=args, summary_only=summary_only)
    else:
        result = run(summary_only=summary_only)
        sys.exit(1 if result.count_ng() > 0 else 0)
