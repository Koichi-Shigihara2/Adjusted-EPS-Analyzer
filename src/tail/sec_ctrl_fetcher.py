#!/usr/bin/env python3
"""
TANUKI TAIL — sec_ctrl_fetcher.py  (SEC-CTRL-1)

10-Q の Part I Item 4「Controls and Procedures」を取得し、
内部統制の有効性・マテリアル・ウィークネス有無を評価して保存する。

出力: docs/portfolio/tail/data/ctrl/{ticker}_ctrl.json
使用方法:
    python src/tail/sec_ctrl_fetcher.py           # tail ポジション全銘柄
    python src/tail/sec_ctrl_fetcher.py SOUN PLTR  # 個別指定
"""

import os
import csv
import json
import re
import time
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, List, Tuple, Dict, Any

import requests

# ── パス設定 ──────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root  = os.path.abspath(os.path.join(script_dir, "..", ".."))

DATA_DIR     = os.path.join(repo_root, "docs", "portfolio", "tail", "data")
CTRL_DIR     = os.path.join(DATA_DIR, "ctrl")
CIK_LOOKUP   = os.path.join(repo_root, "config", "cik_lookup.csv")
POS_IDX_PATH = os.path.join(DATA_DIR, "positions_index.json")

JST = ZoneInfo("Asia/Tokyo")

EDGAR_BASE = "https://www.sec.gov"
EDGAR_DATA = "https://data.sec.gov"
EDGAR_HDR  = {
    "User-Agent": "TANUKI-TAIL-Bot contact@example.com",
    "Accept-Encoding": "gzip, deflate",
}

# ── シグナル検出パターン ──────────────────────────────────────
_RE_NOT_EFFECTIVE = re.compile(
    r"(were\s+not\s+effective|was\s+not\s+effective|"
    r"not\s+effective\s+as\s+of|concluded\s+.{0,60}not\s+effective)",
    re.IGNORECASE,
)
_RE_MATERIAL_WEAKNESS = re.compile(
    r"material\s+weakness(?:es)?",
    re.IGNORECASE,
)
_RE_SIG_DEFICIENCY = re.compile(
    r"significant\s+deficienc(?:y|ies)",
    re.IGNORECASE,
)
_RE_EFFECTIVE = re.compile(
    r"(were\s+effective|was\s+effective|are\s+effective|"
    r"concluded\s+.{0,80}effective\s+as\s+of)",
    re.IGNORECASE,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGAR ユーティリティ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _edgar_get(url: str, timeout: int = 60) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, headers=EDGAR_HDR, timeout=timeout)
        resp.raise_for_status()
        time.sleep(0.15)
        return resp
    except Exception as e:
        print(f"  [EDGAR] 取得失敗 {url}: {e}")
        return None


def _get_recent_10q(cik: str, count: int = 1) -> List[Dict[str, Any]]:
    cik_int = int(cik.lstrip("0") or "0")
    url  = f"{EDGAR_DATA}/submissions/CIK{cik_int:010d}.json"
    resp = _edgar_get(url)
    if not resp:
        return []

    data   = resp.json()
    recent = data.get("filings", {}).get("recent", {})
    forms  = recent.get("form", [])
    accns  = recent.get("accessionNumber", [])
    dates  = recent.get("filingDate", [])
    reports = recent.get("reportDate", [])
    pdocs  = recent.get("primaryDocument", [])

    result: List[Dict[str, Any]] = []
    for i, form in enumerate(forms):
        if form.strip().upper() == "10-Q":
            result.append({
                "accession":      accns[i]  if i < len(accns)  else "",
                "filing_date":    dates[i]  if i < len(dates)  else "",
                "report_date":    reports[i] if i < len(reports) else "",
                "primary_document": pdocs[i] if i < len(pdocs) else "",
            })
            if len(result) >= count:
                break
    return result


def _strip_html(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;",  " ", text)
    text = re.sub(r"&amp;",   "&", text)
    text = re.sub(r"&lt;",    "<", text)
    text = re.sub(r"&gt;",    ">", text)
    text = re.sub(r"&#\d+;",  " ", text)
    text = re.sub(r"\s{3,}",  "\n", text)
    return text.strip()


def _extract_item4_ctrl(text: str, max_chars: int = 6000) -> str:
    """
    Part I Item 4 「Controls and Procedures」セクションを抽出する。
    10-Q には Part II Item 4 (Mine Safety) も存在するため、
    「Controls and Procedures」を含むもっとも長い Item 4 区間を選ぶ。
    """
    # Item 4 全出現箇所を取得
    item4_re   = re.compile(r"(?i)item\s+4[\.\s]")
    item5_re   = re.compile(r"(?i)item\s+5[\.\s]")
    ctrl_re    = re.compile(r"(?i)controls?\s+and\s+procedures?")

    starts = [m.start() for m in item4_re.finditer(text)]
    if not starts:
        return text[:max_chars]

    best_text  = ""
    best_len   = 0
    for s in starts:
        m_end = item5_re.search(text, s + 200)
        end   = m_end.start() if m_end else s + max_chars * 3
        segment = text[s:end]
        if ctrl_re.search(segment) and len(segment) > best_len:
            best_len  = len(segment)
            best_text = segment

    if not best_text:
        best_text = text[starts[0]:starts[0] + max_chars * 2]

    return best_text[:max_chars]


def _report_date_to_quarter(report_date: str) -> str:
    try:
        dt = datetime.strptime(report_date, "%Y-%m-%d")
        q  = (dt.month - 1) // 3 + 1
        return f"{dt.year}Q{q}"
    except Exception:
        return report_date


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 解析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _extract_sentences(text: str, pattern: re.Pattern, context: int = 200) -> List[str]:
    """パターンに一致する文の前後 context 文字を返す（重複除去）"""
    seen   = set()
    result = []
    for m in pattern.finditer(text):
        start = max(0, m.start() - context)
        end   = min(len(text), m.end() + context)
        snippet = text[start:end].strip()
        key = snippet[:80]
        if key not in seen:
            seen.add(key)
            result.append(snippet)
    return result


def _analyze_ctrl_text(item4_text: str) -> Dict[str, Any]:
    """
    Item4 テキストから有効性・弱点を判定する。
    effective = True  → 開示統制は有効
    effective = False → 開示統制は無効（または判定不能）
    """
    # 「not effective」が先に一致するか確認
    not_eff    = bool(_RE_NOT_EFFECTIVE.search(item4_text))
    eff        = bool(_RE_EFFECTIVE.search(item4_text))
    has_mw     = bool(_RE_MATERIAL_WEAKNESS.search(item4_text))
    has_sd     = bool(_RE_SIG_DEFICIENCY.search(item4_text))

    if not_eff:
        effective = False
    elif eff and not has_mw:
        effective = True
    else:
        effective = None  # 判定不能

    mw_snippets = _extract_sentences(item4_text, _RE_MATERIAL_WEAKNESS)
    sd_snippets = _extract_sentences(item4_text, _RE_SIG_DEFICIENCY)

    return {
        "effective":               effective,
        "material_weaknesses":     mw_snippets,
        "significant_deficiencies": sd_snippets,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_ctrl(ticker: str, cik: str) -> Optional[Dict[str, Any]]:
    print(f"\n[{ticker}] CIK={cik}")
    filings = _get_recent_10q(cik, count=1)
    if not filings:
        print(f"  [{ticker}] 10-Q 未発見")
        return None

    filing  = filings[0]
    accn    = filing["accession"]
    pdoc    = filing["primary_document"]
    report  = filing["report_date"]
    filed   = filing["filing_date"]
    cik_int = int(cik.lstrip("0") or "0")
    accn_nd = accn.replace("-", "")

    if not pdoc:
        print(f"  [{ticker}] primaryDocument なし ({accn})")
        return None

    url  = f"{EDGAR_BASE}/Archives/edgar/data/{cik_int}/{accn_nd}/{pdoc}"
    print(f"  [{ticker}] 10-Q 取得: {url}")
    resp = _edgar_get(url, timeout=120)
    if not resp:
        return None

    html = resp.text
    # ファイルサイズが大きい場合、Controls and Procedures は後半にある
    if len(html) > 600_000:
        # 後半60%を対象にする
        html = html[int(len(html) * 0.35):]

    raw_text   = _strip_html(html)
    item4_text = _extract_item4_ctrl(raw_text)
    print(f"  [{ticker}] Item4 抽出: {len(item4_text)}文字")

    analysis   = _analyze_ctrl_text(item4_text)
    quarter    = _report_date_to_quarter(report)

    eff_label = {True: "effective", False: "not_effective", None: "unknown"}
    print(f"  [{ticker}] 有効性: {eff_label[analysis['effective']]}, "
          f"MW={len(analysis['material_weaknesses'])}, "
          f"SD={len(analysis['significant_deficiencies'])}")

    return {
        "ticker":                 ticker.upper(),
        "quarter":                quarter,
        "filing_date":            filed,
        "report_date":            report,
        "effective":              analysis["effective"],
        "material_weaknesses":    analysis["material_weaknesses"],
        "significant_deficiencies": analysis["significant_deficiencies"],
        "item4_excerpt":          item4_text[:2000],
        "fetched_at":             datetime.now(JST).isoformat(),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CIK ロード / ポジション取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_cik_map() -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not os.path.exists(CIK_LOOKUP):
        return result
    with open(CIK_LOOKUP, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = row.get("ticker", "").upper().strip()
            c = row.get("cik", "").strip()
            if t and c:
                result[t] = c
    return result


def load_tail_tickers() -> List[str]:
    """positions_index.json から全ティッカーを取得"""
    if not os.path.exists(POS_IDX_PATH):
        return []
    with open(POS_IDX_PATH, encoding="utf-8") as f:
        data = json.load(f)
    tickers = []
    for entry in data:
        if isinstance(entry, dict):
            t = entry.get("ticker", "").upper().strip()
        else:
            t = str(entry).upper().strip()
        if t:
            tickers.append(t)
    return tickers


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エントリポイント
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    args = sys.argv[1:]
    if args:
        tickers = [t.upper() for t in args]
    else:
        tickers = load_tail_tickers()
        if not tickers:
            print("positions_index.json が見つからないか空です")
            sys.exit(1)

    cik_map = load_cik_map()
    os.makedirs(CTRL_DIR, exist_ok=True)

    ok, ng = 0, 0
    for ticker in tickers:
        cik = cik_map.get(ticker)
        if not cik:
            print(f"[{ticker}] CIK 未登録 — スキップ")
            ng += 1
            continue

        try:
            result = fetch_ctrl(ticker, cik)
            if result is None:
                ng += 1
                continue
            path = os.path.join(CTRL_DIR, f"{ticker}_ctrl.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  [{ticker}] 保存: {path}")
            ok += 1
        except Exception as e:
            print(f"  [{ticker}] エラー: {e}")
            ng += 1

        time.sleep(0.5)

    print(f"\n完了: {ok} 成功 / {ng} 失敗")


if __name__ == "__main__":
    main()
