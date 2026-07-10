"""
report.txt(統合レポート・AI用)パーサー

docs/value-monitor/tanuki_valuation/data/{TICKER}/report.txt をパースし、
TANUKI SCORE / MATRIX POSITION / TANUKI VALUATION / 成長率根拠 / HYPECORE /
STONKS SILO / RISK EVENTS(高重要度のみ) をJSON構造化する。読み取り専用
(report.txt自体は既存パイプラインが生成する静的ファイルであり、本スクリプトは
それを変更しない)。

2026-07-10のサテライト投資候補スクリーニングで使用したアドホックスクリプトを
再利用可能な形に整理したもの。パース時に判明した3件のフォーマット差異に対応済み：
  - Growth_Rate_Rec(乖離⚠️付き)はセクション[3]内にあり、セクション[4]の
    「推奨成長率」「元成長率」「最終推奨値」とは別の場所に存在する
  - Intrinsic_Value_BASE・シナリオIVはマイナス値(例: $-1.34)を取り得る
  - シナリオ行 "IV=$X, Deviation=Y%" のIV捕捉を貪欲マッチにすると末尾の
    カンマを飲み込みDeviationが取得できなくなる(非貪欲マッチが必要)
また、growth_source=fcf_cagrやrecommended_g自動注入の銘柄では、セクション[4]に
推奨値行そのものが存在しないケースがある(パース失敗ではなく仕様)。

実行例:
    # 単一銘柄
    python common/screening/report_txt_parser.py AAPL

    # 複数銘柄を指定してJSON出力
    python common/screening/report_txt_parser.py AAPL MSFT NVDA --output out.json

    # 引数なし = config/cik_lookup.csv の全銘柄(report.txtが存在するもののみ)
    python common/screening/report_txt_parser.py --output all_reports.json

他スクリプトからの利用:
    from common.screening.report_txt_parser import parse_ticker_report
    result = parse_ticker_report(repo_root, "AAPL")
"""
import argparse
import csv
import json
import os
import re
from datetime import datetime

SECTION_HEADER_RE = re.compile(r"^\[(\d+)\.\s*(.+?)\]\s*$", re.MULTILINE)


def _find(pattern, text, group=1, flags=0):
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else None


def split_sections(text):
    """[N. HEADER] を境界に本文をセクション分割する"""
    matches = list(SECTION_HEADER_RE.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[num] = text[start:end]
    return sections


def _parse_tanuki_score(sec1):
    if sec1 is None:
        return None, ["セクション[1]が存在しない"]
    errs = []
    out = {
        "Classification": _find(r"^Classification:\s*(.+)$", sec1, flags=re.MULTILINE),
        "Funda_Score": _find(r"^Funda_Score:\s*(\d+)/100", sec1, flags=re.MULTILINE),
        "Deviation_Rate": _find(r"^\s*Deviation_Rate:\s*([+-]?[\d.]+%)", sec1, flags=re.MULTILINE),
        "MA200_Deviation": _find(r"^\s*MA200_Deviation:\s*([+-]?[\d.]+%)", sec1, flags=re.MULTILINE),
        "HypeCore_Phase": _find(r"^\s*HypeCore_Phase:\s*(.+)$", sec1, flags=re.MULTILINE),
        "Analyst_Consensus": _find(r"^\s*Analyst_Consensus:\s*(.+)$", sec1, flags=re.MULTILINE),
    }
    if out["Classification"] is None:
        errs.append("Classification行が見つからない")
    if out["Funda_Score"] is None:
        errs.append("Funda_Score行が見つからない")
    return out, errs


def _parse_matrix(sec2):
    if sec2 is None:
        return None, ["セクション[2]が存在しない"]
    errs = []
    out = {
        "Matrix": _find(r"^Matrix:\s*(.+)$", sec2, flags=re.MULTILINE),
        "Quadrant": _find(r"^Quadrant:\s*(.+)$", sec2, flags=re.MULTILINE),
        "Key_Metric_Y": _find(r"^Key_Metric_Y:\s*(.+)$", sec2, flags=re.MULTILINE),
    }
    if out["Matrix"] is None or out["Key_Metric_Y"] is None:
        errs.append("Matrix種別 or Key_Metric_Y行が見つからない")
    return out, errs


def _parse_valuation(sec3):
    if sec3 is None:
        return None, ["セクション[3]が存在しない"]
    errs = []
    out = {
        "Current_Price": _find(r"^Current_Price:\s*\$(-?[\d,\.]+)", sec3, flags=re.MULTILINE),
        "Intrinsic_Value_BASE": _find(r"^Intrinsic_Value_BASE:\s*\$(-?[\d,\.]+)", sec3, flags=re.MULTILINE),
        "Deviation_BASE": _find(r"^Deviation_BASE:\s*([+-]?[\d.]+%)", sec3, flags=re.MULTILINE),
    }
    if out["Current_Price"] is None or out["Intrinsic_Value_BASE"] is None:
        errs.append("Current_Price or Intrinsic_Value_BASE行が見つからない")

    # 通常形式: "BEAR: Growth=X%, IV=$Y, Deviation=Z%"
    # 代替形式(推奨値ベース・recommended_g自動調整銘柄): "BEAR: Growth=X%, IV=$Y （推奨値ベース）"(Deviation省略)
    scenarios = {}
    for label in ("BEAR", "BASE", "BULL"):
        m = re.search(
            rf"^{label}:\s*Growth=([+-]?[\d.]+%),\s*IV=\$(-?[\d,\.]+?)(?:,\s*Deviation=([+-]?[\d.]+%))?\s*(（推奨値ベース）)?$",
            sec3, re.MULTILINE)
        if m:
            scenarios[label] = {
                "Growth": m.group(1), "IV": m.group(2), "Deviation": m.group(3),
                "note": "推奨値ベース(Deviation非表示)" if m.group(4) else None,
            }
        else:
            scenarios[label] = None
            errs.append(f"{label}シナリオ行が見つからない")
    out["Scenarios"] = scenarios

    dcf_rel = _find(r"^DCF_Reliability:\s*(\S+)", sec3, flags=re.MULTILINE)
    out["DCF_Reliability"] = dcf_rel
    if dcf_rel is None:
        errs.append("DCF_Reliability行が見つからない")
    out["DCF_Reliability_Note"] = _find(r"^DCF_Reliability:\s*\S+\s*⚠️?\s*\((.+)\)", sec3, flags=re.MULTILINE)
    return out, errs


def _parse_growth(sec3, sec4):
    """Growth_Rate_Rec(乖離⚠️付き)はセクション[3]、Phase1/判定はセクション[4]に格納されている"""
    if sec4 is None:
        return None, ["セクション[4]が存在しない"]
    errs = []
    phase1 = _find(r"^Phase1成長率\s*:\s*([+-]?[\d.]+%)", sec4, flags=re.MULTILINE)
    if phase1 is None:
        errs.append("Phase1成長率行が見つからない")

    rec_rate = None
    rec_warning = None
    if sec3 is not None:
        m = re.search(r"^Growth_Rate_Rec:\s*([+-]?[\d.]+%)\s*\((.+)\)", sec3, re.MULTILINE)
        if m:
            rec_rate = m.group(1)
            paren = m.group(2)
            if "⚠️" in paren:
                wm = re.search(r"([+-]?[\d.]+)pt\s*(above|below)\s*recommended", paren)
                if wm:
                    rec_warning = f"{wm.group(1)}pt {wm.group(2)} recommended"

    if rec_rate is None:
        rec_rate = _find(r"^推奨成長率\s*:\s*([+-]?[\d.]+%)", sec4, flags=re.MULTILINE)
    if rec_rate is None:
        final_rec = _find(r"^\s*最終推奨値:\s*([+-]?[\d.]+%)", sec4, flags=re.MULTILINE)
        orig = _find(r"^元成長率\s*:\s*([+-]?[\d.]+%)", sec4, flags=re.MULTILINE)
        rec_rate = final_rec if final_rec is not None else orig

    gap_pt = None
    if phase1 is not None and rec_rate is not None:
        try:
            gap_pt = round(float(phase1.rstrip("%")) - float(rec_rate.rstrip("%")), 1)
        except ValueError:
            pass

    verdict = _find(r"^判定\s*:\s*(\S+)", sec4, flags=re.MULTILINE)
    if verdict is None:
        errs.append("判定行が見つからない")
    if rec_rate is None:
        errs.append("推奨値行が存在しない(Phase1採用値と推奨値が同一、"
                     "またはgrowth_source=fcf_cagr等でrecommended_g比較行自体が"
                     "出力されないケース。パース不備ではなくレポート仕様)")

    return {
        "Phase1_Growth_Rate": phase1,
        "Growth_Rate_Rec": rec_rate,
        "Rec_Warning": rec_warning,
        "Gap_Pt": gap_pt,
        "Verdict": verdict,
    }, errs


def _parse_hypecore(sec7):
    if sec7 is None:
        return None, ["セクション[7]が存在しない"]
    errs = []
    current_phase = _find(r"^Current_Phase:\s*(.+)$", sec7, flags=re.MULTILINE)
    if current_phase is None:
        errs.append("Current_Phase行が見つからない")

    hist_match = re.search(r"Phase_History \(recent 6 months\):\n((?:\d{4}-\d{2}:.+\n?)+)", sec7)
    phase_history = None
    if hist_match:
        phase_history = [l.strip() for l in hist_match.group(1).strip().split("\n") if l.strip()]
    else:
        errs.append("Phase_History(直近6ヶ月)ブロックが見つからない")

    return {"Current_Phase": current_phase, "Phase_History": phase_history}, errs


def _parse_stonks(sec8):
    if sec8 is None:
        return None, ["セクション[8]が存在しない"]
    errs = []
    out = {}
    for field in ["Short_Interest", "Institutional_Ownership", "Analyst_Consensus",
                  "Insider_Activity", "Runway_Months", "Revenue_Growth_YoY", "Breakeven_Estimate"]:
        val = _find(rf"^{field}:\s*(.+)$", sec8, flags=re.MULTILINE)
        out[field] = val
        if val is None:
            errs.append(f"{field}行が見つからない")

    core_fields = ["Short_Interest", "Runway_Months", "Revenue_Growth_YoY", "Breakeven_Estimate"]
    out["has_meaningful_data"] = any(out.get(f) is not None and not out[f].startswith("N/A") for f in core_fields)
    return out, errs


def _parse_risk_events(sec9):
    if sec9 is None:
        return None, ["セクション[9]が存在しない"]
    events = [
        {"type": m.group(1), "title": m.group(2).strip()}
        for m in re.finditer(r"^\s*\[high\]\s*(\w+):\s*(.+)$", sec9, re.MULTILINE)
    ]
    return events, []


def parse_report_text(ticker, text):
    """report.txtの生テキストをパースしてdictを返す"""
    sections = split_sections(text)
    result = {
        "ticker": ticker,
        "report_price": _find(r"^Price:\s*\$([\d,\.]+)", text, flags=re.MULTILINE),
        "generated_at": _find(r"^Generated:\s*(.+)$", text, flags=re.MULTILINE),
        "parse_errors": {},
    }
    parsers = [
        ("tanuki_score", _parse_tanuki_score, (1,)),
        ("matrix", _parse_matrix, (2,)),
        ("valuation", _parse_valuation, (3,)),
        ("growth_rationale", _parse_growth, (3, 4)),
        ("hypecore", _parse_hypecore, (7,)),
        ("stonks_silo", _parse_stonks, (8,)),
        ("risk_events_high", _parse_risk_events, (9,)),
    ]
    for key, fn, sec_nums in parsers:
        data, errs = fn(*[sections.get(n) for n in sec_nums])
        result[key] = data
        if errs:
            result["parse_errors"][key] = errs
    return result


def parse_ticker_report(repo_root, ticker):
    """{ticker}のreport.txtを読み込みパースする。存在しない場合はNoneを返す"""
    path = os.path.join(repo_root, "docs", "value-monitor", "tanuki_valuation", "data", ticker, "report.txt")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return parse_report_text(ticker, text)


def _all_tickers_with_report(repo_root):
    cik_path = os.path.join(repo_root, "config", "cik_lookup.csv")
    with open(cik_path, encoding="utf-8") as f:
        tickers = [r["ticker"] for r in csv.DictReader(f)]
    return [t for t in tickers
            if os.path.exists(os.path.join(repo_root, "docs", "value-monitor", "tanuki_valuation", "data", t, "report.txt"))]


def main():
    parser = argparse.ArgumentParser(description="report.txt(統合レポート)を構造化パースする")
    parser.add_argument("tickers", nargs="*", help="対象ティッカー(省略時はcik_lookup.csv全銘柄のうちreport.txt存在分)")
    parser.add_argument("--output", default=None, help="出力JSONパス(省略時は標準出力に件数のみ表示)")
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tickers = args.tickers or _all_tickers_with_report(repo_root)

    results = []
    missing = []
    for t in tickers:
        r = parse_ticker_report(repo_root, t)
        if r is None:
            missing.append(t)
        else:
            results.append(r)

    output = {
        "generated_at": datetime.now().isoformat(),
        "requested_count": len(tickers),
        "parsed_count": len(results),
        "missing_report_txt": missing,
        "reports": results,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"出力完了: {args.output} ({len(results)}件)")
    else:
        print(f"パース対象: {len(tickers)}件 / 成功: {len(results)}件 / report.txt不在: {len(missing)}件")
        if missing:
            print("  不在:", missing)


if __name__ == "__main__":
    main()
