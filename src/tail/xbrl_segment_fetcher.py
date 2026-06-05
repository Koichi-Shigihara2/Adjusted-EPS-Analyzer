#!/usr/bin/env python3
"""
TANUKI TAIL — xbrl_segment_fetcher.py

四半期レビュー用セグメント別KPI取得スクリプト（ローカル & GHA）

処理フロー:
  1. EDGAR submissions API で直近 N 件の 10-Q ファイリングを取得
  2. 各 10-Q の XBRL Instance Document (_htm.xml) をダウンロード
  3. tail_kpi_map.json の tag_history に従い explicitMember でセグメント別数値を抽出
  4. docs/portfolio/tail/data/kpi/{ticker}_layer2.json に保存

使用方法:
    python src/tail/xbrl_segment_fetcher.py --ticker PLTR
    python src/tail/xbrl_segment_fetcher.py --ticker SOFI TSLA
    python src/tail/xbrl_segment_fetcher.py --ticker PLTR --quarters 4

必要パッケージ: requests
"""

import os
import sys
import json
import time
import re
import argparse
from datetime import datetime, date
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("requests が必要です: pip install requests")
    sys.exit(1)

# ── パス設定 ──────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root  = os.path.abspath(os.path.join(script_dir, "..", ".."))

KPI_MAP_PATH = os.path.join(
    repo_root, "docs", "portfolio", "tail", "data", "tail_kpi_map.json"
)
OUTPUT_DIR = os.path.join(
    repo_root, "docs", "portfolio", "tail", "data", "kpi"
)

# ── SEC API 設定 ──────────────────────────────────────────────
SEC_HEADERS = {
    "User-Agent": "Koichi Personal Investment Tools koichi@example.com",
    "Accept": "application/json,application/xml,*/*",
}
SEC_BASE = "https://www.sec.gov"
THROTTLE  = 0.2   # SEC リクエスト間隔（秒）


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CIK 取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_cik(ticker: str) -> Optional[str]:
    """EDGAR company_tickers.json からティッカー → CIK（10桁）"""
    ticker = ticker.upper()
    try:
        time.sleep(THROTTLE)
        r = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=SEC_HEADERS, timeout=15,
        )
        r.raise_for_status()
        for entry in r.json().values():
            if entry.get("ticker", "").upper() == ticker:
                return str(entry["cik_str"]).zfill(10)
    except Exception as e:
        print(f"  CIK 取得エラー: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10-Q ファイリング一覧取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_10q_filings(cik: str, n: int = 8) -> List[Dict[str, Any]]:
    """
    EDGAR submissions API から最新 n 件の 10-Q を取得。
    Returns list of {accn, filed, period, xml}
    """
    results: List[Dict[str, Any]] = []

    def _extract(fil: Dict[str, Any]) -> None:
        forms   = fil.get("form", [])
        accns   = fil.get("accessionNumber", [])
        filed   = fil.get("filingDate", [])
        reports = fil.get("reportDate", [])
        prims   = fil.get("primaryDocument", [])
        for i, f in enumerate(forms):
            if f != "10-Q" or len(results) >= n:
                continue
            prim = prims[i] if i < len(prims) else ""
            if prim.endswith(".htm"):
                xml_file = prim[:-4] + "_htm.xml"
            elif prim.endswith(".html"):
                xml_file = prim[:-5] + "_htm.xml"
            else:
                xml_file = ""
            results.append({
                "accn":   accns[i] if i < len(accns) else "",
                "filed":  filed[i] if i < len(filed) else "",
                "period": reports[i] if i < len(reports) else "",
                "xml":    xml_file,
            })

    try:
        time.sleep(THROTTLE)
        r = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=SEC_HEADERS, timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        _extract(data.get("filings", {}).get("recent", {}))

        # 古いファイリングが別ページに分割されている場合
        if len(results) < n:
            for sub in data.get("filings", {}).get("files", []):
                if len(results) >= n:
                    break
                nm = sub.get("name", "")
                if not nm.endswith(".json"):
                    continue
                try:
                    time.sleep(THROTTLE)
                    sr = requests.get(
                        f"https://data.sec.gov/submissions/{nm}",
                        headers=SEC_HEADERS, timeout=20,
                    )
                    sr.raise_for_status()
                    _extract(sr.json())
                except Exception:
                    continue

    except Exception as e:
        print(f"  submissions API エラー: {e}")

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# XBRL Instance Document ダウンロード
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def download_xbrl(cik: str, accn: str, xml_file: str) -> Optional[str]:
    url = (
        f"{SEC_BASE}/Archives/edgar/data/{int(cik)}/"
        f"{accn.replace('-', '')}/{xml_file}"
    )
    try:
        time.sleep(THROTTLE)
        r = requests.get(url, headers=SEC_HEADERS, timeout=90)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}: {xml_file}")
            return None
        print(f"  取得: {xml_file} ({len(r.content) // 1024} KB)")
        return r.text
    except Exception as e:
        print(f"  ダウンロード例外: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# タグ選択・ユーティリティ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def select_tag(tag_history: List[Dict[str, Any]], period_end: str) -> Optional[str]:
    """valid_from / valid_to に基づいてタグを選択。"""
    try:
        pe = date.fromisoformat(period_end[:10])
    except Exception:
        pe = date.today()
    for entry in sorted(tag_history, key=lambda x: x.get("valid_from", ""), reverse=True):
        vf = entry.get("valid_from")
        vt = entry.get("valid_to")
        if vf and date.fromisoformat(vf) > pe:
            continue
        if vt and pe > date.fromisoformat(vt):
            continue
        return entry["tag"]
    return None


def quarter_label(period_end: str) -> str:
    """'2025-03-31' → '2025Q1'"""
    try:
        d = date.fromisoformat(period_end[:10])
        return f"{d.year}Q{(d.month - 1) // 3 + 1}"
    except Exception:
        return period_end


def _is_quarterly(start: Optional[str], end: Optional[str]) -> bool:
    """期間が 60〜100 日（≒3ヶ月）かどうかを判定。"""
    if not start or not end:
        return True
    try:
        diff = (date.fromisoformat(end) - date.fromisoformat(start)).days
        return 60 <= diff <= 100
    except Exception:
        return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# XBRL コンテキスト解析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# コンテキストブロックを抽出する正規表現
_CTX_RE = re.compile(
    r'<(?:\w+:)?context\b[^>]*?id=["\']([^"\']+)["\'][^>]*?>(.*?)</(?:\w+:)?context>',
    re.DOTALL | re.IGNORECASE,
)
_START_RE = re.compile(r'<(?:\w+:)?startDate[^>]*>([\d\-]+)<', re.IGNORECASE)
_END_RE   = re.compile(r'<(?:\w+:)?endDate[^>]*>([\d\-]+)<',   re.IGNORECASE)


def parse_contexts(xml_text: str, dim_local: str) -> Dict[str, Dict[str, Any]]:
    """
    指定ディメンション軸（ローカル名）の explicitMember を持つ
    コンテキスト情報を返す。
    Returns: {ctx_id: {"member": "pltr:CommercialOperatingSegmentMember",
                        "start": "2025-01-01", "end": "2025-03-31"}}
    """
    # ディメンション属性にローカル名が含まれる explicitMember を抽出
    mem_re = re.compile(
        r'<[^>]*?explicitMember[^>]*?dimension=["\'][^"\']*'
        + re.escape(dim_local)
        + r'[^"\']*["\'][^>]*?>\s*(.+?)\s*</[^>]*?explicitMember>',
        re.DOTALL | re.IGNORECASE,
    )

    result: Dict[str, Dict[str, Any]] = {}
    for m in _CTX_RE.finditer(xml_text):
        ctx_id   = m.group(1)
        ctx_body = m.group(2)
        mm = mem_re.search(ctx_body)
        if not mm:
            continue
        sm = _START_RE.search(ctx_body)
        em = _END_RE.search(ctx_body)
        result[ctx_id] = {
            "member": mm.group(1).strip(),
            "start":  sm.group(1) if sm else None,
            "end":    em.group(1) if em else None,
        }
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# XBRL ファクト値の抽出
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_fact(
    xml_text: str,
    ctx_ids: set,
    concept_local: str,
    period_end: str,
    contexts: Dict[str, Dict[str, Any]],
) -> Optional[float]:
    """
    指定コンテキストIDセットから concept_local の数値を取得。
    period_end に合致する四半期値を優先して返す。
    [\\w-]+ で us-gaap: のようなハイフン含む namespace prefix に対応。
    """
    fact_re = re.compile(
        r'<(?:[\w-]+:)?' + re.escape(concept_local)
        + r'\b[^>]*?contextRef=["\']([^"\']+)["\'][^>]*?>\s*(-?[\d.]+)\s*<',
        re.IGNORECASE,
    )
    pe_ym = period_end[:7]  # "2025-03"

    candidates: List[tuple] = []
    for fm in fact_re.finditer(xml_text):
        cref = fm.group(1)
        if cref not in ctx_ids:
            continue
        try:
            val = float(fm.group(2))
        except ValueError:
            continue
        ctx   = contexts.get(cref, {})
        end   = ctx.get("end", "")
        start = ctx.get("start")
        # 優先度: ① period_end 年月一致  ② quarterly 期間  ③ その他
        pm = end.startswith(pe_ym)
        iq = _is_quarterly(start, end)
        candidates.append((val, pm, iq))

    if not candidates:
        return None
    candidates.sort(key=lambda c: (not c[1], not c[2]))
    return candidates[0][0]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# XBRL 全KPI抽出
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_and_extract(
    xml_text: str,
    kpi_list: List[Dict[str, Any]],
    period_end: str,
) -> Dict[str, Optional[float]]:
    """
    XBRL Instance Document から kpi_list の全 KPI 値を抽出。
    Returns: {kpi_name: float_or_None}
    """
    # ディメンション軸ごとにコンテキストを一度だけ解析
    dims: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for kpi in kpi_list:
        dim_full  = kpi.get("dimension", "us-gaap:StatementBusinessSegmentsAxis")
        dim_local = dim_full.split(":")[-1]
        if dim_local not in dims:
            dims[dim_local] = parse_contexts(xml_text, dim_local)

    results: Dict[str, Optional[float]] = {}

    for kpi in kpi_list:
        name      = kpi["kpi_name"]
        dim_local = kpi.get("dimension", "us-gaap:StatementBusinessSegmentsAxis").split(":")[-1]
        ctx_map   = dims.get(dim_local, {})
        concept   = kpi.get("revenue_tag", "us-gaap:Revenues").split(":")[-1]
        fallbacks = kpi.get("fallback_tags", [])

        seg_tag = select_tag(kpi["tag_history"], period_end)
        if not seg_tag:
            results[name] = None
            continue

        def _try(t: str) -> Optional[float]:
            t_local = t.split(":")[-1]
            ctx_ids = {
                cid for cid, info in ctx_map.items()
                if info["member"] == t or info["member"].split(":")[-1] == t_local
            }
            if not ctx_ids:
                return None
            return extract_fact(xml_text, ctx_ids, concept, period_end, ctx_map)

        val = _try(seg_tag)
        if val is None:
            for fb in fallbacks:
                val = _try(fb)
                if val is not None:
                    print(f"    {name}: fallback '{fb}' 使用")
                    break

        results[name] = val
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1銘柄処理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_ticker(ticker: str, kpi_map: Dict[str, Any], out_dir: str, n_quarters: int = 8) -> bool:
    ticker   = ticker.upper()
    kpi_list = kpi_map.get(ticker)
    if not kpi_list:
        print(f"[{ticker}] tail_kpi_map.json に定義なし → スキップ")
        return False

    print(f"\n{'─' * 52}")
    print(f"  {ticker}")
    print(f"{'─' * 52}")

    cik = get_cik(ticker)
    if not cik:
        print("  CIK 取得失敗")
        return False
    print(f"  CIK: {cik}")

    filings = get_10q_filings(cik, n=n_quarters)
    if not filings:
        print("  10-Q ファイリング取得失敗")
        return False
    print(f"  10-Q: {[f['period'] for f in filings]}")

    # KPIごとに四半期データを蓄積
    kpi_data: Dict[str, List[Dict[str, Any]]] = {
        kpi["kpi_name"]: [] for kpi in kpi_list
    }

    for filing in filings:
        period = filing["period"]   # "2025-03-31"
        filed  = filing["filed"]    # "2025-05-05"
        accn   = filing["accn"]
        xml_f  = filing["xml"]
        qlabel = quarter_label(period)

        if not xml_f:
            print(f"\n  [{qlabel}] XML ファイル名不明 → スキップ")
            continue

        print(f"\n  [{qlabel}] period={period}  filed={filed}")

        xml_text = download_xbrl(cik, accn, xml_f)
        if not xml_text:
            continue

        extracted = parse_and_extract(xml_text, kpi_list, period)
        del xml_text  # メモリ解放

        for kpi_name, val in extracted.items():
            if val is not None:
                # 整数に近い値（USD金額）はint、小数値（比率）はfloatのまま保持
                out_val = int(round(val)) if val % 1 < 0.001 else round(val, 4)
                print(f"    {kpi_name}: {out_val:,}")
                kpi_data[kpi_name].append({
                    "quarter": qlabel,
                    "value":   out_val,
                    "filed":   filed,
                })
            else:
                print(f"    {kpi_name}: 取得失敗")

    # 出力 JSON 構築
    missing_kpis = [n for n, d in kpi_data.items() if not d]
    layer2_complete = len(missing_kpis) == 0

    output = {
        "ticker":          ticker,
        "fetched_at":      datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "layer2_complete": layer2_complete,
        "missing_kpis":    missing_kpis,
        "kpis": {
            n: {"unit": "USD", "data": d}
            for n, d in kpi_data.items()
        },
    }

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{ticker}_layer2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    status = "✓" if layer2_complete else "△"
    print(f"\n  {status} 保存: {out_path}")
    if missing_kpis:
        print(f"  missing_kpis: {missing_kpis}")
    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エントリーポイント
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TANUKI TAIL — XBRL Segment KPI Fetcher (10-Q)"
    )
    parser.add_argument(
        "--ticker", required=True, nargs="+",
        help="対象ティッカー（複数可）: --ticker PLTR SOFI TSLA",
    )
    parser.add_argument(
        "--quarters", type=int, default=8,
        help="取得四半期数（デフォルト: 8）",
    )
    args = parser.parse_args()

    with open(KPI_MAP_PATH, encoding="utf-8") as f:
        kpi_map = json.load(f)

    summary: Dict[str, bool] = {}
    for tkr in args.ticker:
        ok = fetch_ticker(tkr.upper(), kpi_map, OUTPUT_DIR, n_quarters=args.quarters)
        summary[tkr.upper()] = ok

    print(f"\n{'━' * 52}")
    print("完了:")
    for tkr, ok in summary.items():
        print(f"  {'✓' if ok else '✗'} {tkr}")


if __name__ == "__main__":
    main()
