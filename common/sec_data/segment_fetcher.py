"""
SEC セグメント別売上取得スクリプト（ローカル専用）v2.0

XBRL Instance Document（_htm.xml）からセグメント別売上・営業利益を抽出し、
annual_{year}.json の "segments" フィールドに追記する。

【発見した事実】
- iXBRL（10-K HTML本体）: セグメント別Revenueタグなし（NVDAの方針）
- XBRL Instance Document（_htm.xml）: セグメント別Revenueが正しく存在
  例: nvda-20250126_htm.xml
      c-201 = ComputeAndNetworkingSegmentMember → $116,193M
      c-202 = GraphicsSegmentMember             → $14,304M

【ファイル名の法則】
  primaryDocument: "nvda-20250126.htm"
  Instance Doc:    "nvda-20250126_htm.xml"  （.htm → _htm.xml）

使用方法（PowerShell）:
    python common/sec_data/segment_fetcher.py NVDA --years 3
    python common/sec_data/segment_fetcher.py       # 全銘柄

GitHub Actions では実行しない。ローカル実行 → push の運用。

必要パッケージ（初回のみ）:
    pip install beautifulsoup4 lxml requests
"""

import os
import sys
import json
import time
import re
import requests
import argparse
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

try:
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
    import warnings
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# パス設定
script_dir = os.path.dirname(os.path.abspath(__file__))
common_dir = os.path.dirname(script_dir)
repo_root  = os.path.dirname(common_dir)
sys.path.insert(0, repo_root)

from common.sec_data.config import get_all, get_ticker_info

# ── SEC API 設定 ──────────────────────────────────────────────
SEC_HEADERS = {
    "User-Agent": "Koichi Personal Investment Tools koichi@example.com",
    "Accept": "application/xml,text/xml,*/*",
}
SEC_BASE      = "https://www.sec.gov"
RATE_LIMIT_DELAY = 0.15

# ── Revenue / 営業利益 の XBRL タグ名 ────────────────────────
REVENUE_TAGS = {
    "revenues",
    "revenuefromcontractwithcustomerexcludingassessedtax",
    "revenuefromcontractwithcustomerincludingassessedtax",
    "salesrevenuenet",
    "totalrevenues",
}
OPINCOME_TAGS = {
    "operatingincomeloss",
    "grossprofit",
}

# ── CIK キャッシュ ────────────────────────────────────────────
_cik_cache: Dict[str, str] = {}

def _load_cik_cache(data_dir: str) -> Dict[str, str]:
    path = os.path.join(data_dir, "_cik_cache.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_cik_cache(data_dir: str, cache: Dict[str, str]) -> None:
    path = os.path.join(data_dir, "_cik_cache.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def get_cik(ticker: str, data_dir: str) -> Optional[str]:
    """ティッカー → CIK（10桁）"""
    ticker = ticker.upper()
    global _cik_cache
    if ticker in _cik_cache:
        return _cik_cache[ticker]
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=SEC_HEADERS, timeout=15
        )
        if r.status_code == 200:
            for entry in r.json().values():
                if entry.get("ticker", "").upper() == ticker:
                    cik = str(entry["cik_str"]).zfill(10)
                    _cik_cache[ticker] = cik
                    _save_cik_cache(data_dir, _cik_cache)
                    return cik
    except Exception as e:
        print(f"   [{ticker}] CIK取得エラー: {e}")
    return None


def get_10k_filings(cik: str, max_years: int = 5) -> List[Dict[str, Any]]:
    """
    submissions API から 10-K ファイリング一覧を取得
    primaryDocument フィールドから HTM ファイル名を取得し
    _htm.xml ファイル名を導出する
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(url, headers=SEC_HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"   submissions API エラー: {r.status_code}")
            return []
        data     = r.json()
        filings  = data.get("filings", {}).get("recent", {})
        forms    = filings.get("form", [])
        accns    = filings.get("accessionNumber", [])
        dates    = filings.get("filingDate", [])
        fys      = filings.get("reportDate", [])
        pri_docs = filings.get("primaryDocument", [])

        results = []
        for i, f in enumerate(forms):
            if f != "10-K":
                continue
            fy_str   = fys[i] if i < len(fys) else ""
            fy       = int(fy_str[:4]) if fy_str else 0
            htm_file = pri_docs[i] if i < len(pri_docs) else ""

            # _htm.xml ファイル名を導出
            # 例: nvda-20250126.htm → nvda-20250126_htm.xml
            if htm_file.endswith(".htm"):
                xml_file = htm_file[:-4] + "_htm.xml"
            elif htm_file.endswith(".html"):
                xml_file = htm_file[:-5] + "_htm.xml"
            else:
                xml_file = ""

            results.append({
                "accn":     accns[i],
                "date":     dates[i],
                "fy":       fy,
                "htm_file": htm_file,
                "xml_file": xml_file,
            })
            if len(results) >= max_years:
                break
        return results
    except Exception as e:
        print(f"   submissions API 例外: {e}")
        return []


def download_xbrl_instance(cik: str, accn: str, xml_file: str) -> Optional[str]:
    """
    XBRL Instance Document（_htm.xml）をダウンロードして返す
    メモリのみ・保存しない
    """
    accn_nodash = accn.replace("-", "")
    cik_int     = int(cik)
    url = f"{SEC_BASE}/Archives/edgar/data/{cik_int}/{accn_nodash}/{xml_file}"
    print(f"   XML URL: {url}")
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(url, headers=SEC_HEADERS, timeout=60)
        if r.status_code != 200:
            print(f"   XML取得エラー: {r.status_code}")
            return None
        print(f"   ダウンロード完了: {len(r.content)/1024:.0f} KB")
        return r.text
    except Exception as e:
        print(f"   XML取得例外: {e}")
        return None


def parse_xbrl_segments(
    xml_text: str,
    member_map: Dict[str, str],
) -> Dict[str, Dict[str, Any]]:
    """
    XBRL Instance Document からセグメント別売上・営業利益を抽出

    Args:
        xml_text:   _htm.xml のテキスト
        member_map: {"nvda:ComputeAndNetworkingSegmentMember": "Compute and Networking", ...}

    Returns:
        {"Compute and Networking": {"revenue": 116193000000, "operating_income": ...}, ...}

    処理フロー:
        1. context タグを解析してコンテキストIDとセグメントMemberのマッピングを構築
           （StatementBusinessSegmentsAxis ディメンションを使用）
        2. Revenue/OperatingIncome タグのcontextRefでマッピングを引いて値を取得
    """
    soup = BeautifulSoup(xml_text, "xml")

    # ── Step 1: コンテキストID → セグメントMember のマッピング ──
    # context タグを直接検索（名前空間あり・なし両方）
    ctx_to_member: Dict[str, str] = {}

    # 文字列検索でコンテキストを抽出（名前空間の問題を回避）
    # pattern: id="c-NNN" ... StatementBusinessSegmentsAxis ... Member
    ctx_pattern = re.compile(
        r'id="(c-\d+)".*?</.*?context>',
        re.DOTALL
    )
    member_pattern = re.compile(
        r'StatementBusinessSegmentsAxis[^>]*>([^<]+)</xbrldi:explicitMember>'
    )

    for ctx_match in ctx_pattern.finditer(xml_text):
        ctx_id  = ctx_match.group(1)
        ctx_txt = ctx_match.group(0)
        m = member_pattern.search(ctx_txt)
        if m:
            member_val = m.group(1).strip()
            if member_val in member_map:
                ctx_to_member[ctx_id] = member_map[member_val]

    print(f"   セグメントコンテキスト: {ctx_to_member}")

    if not ctx_to_member:
        return {}

    # ── Step 2: Fact タグからセグメント別数値を収集 ──
    results: Dict[str, Dict[str, Any]] = {
        seg: {"revenue": None, "operating_income": None}
        for seg in set(ctx_to_member.values())
    }

    # BeautifulSoup で全タグを走査
    all_tags = soup.find_all(True)
    for tag in all_tags:
        ctx_ref = tag.get("contextRef", "")
        if ctx_ref not in ctx_to_member:
            continue

        seg_name = ctx_to_member[ctx_ref]
        tag_local = tag.name.split(":")[-1].lower() if tag.name else ""

        # 数値取得
        try:
            val_str = tag.get_text(strip=True).replace(",", "")
            val     = float(val_str)
        except (ValueError, TypeError):
            continue

        if tag_local in REVENUE_TAGS and results[seg_name]["revenue"] is None:
            results[seg_name]["revenue"] = val
        elif tag_local in OPINCOME_TAGS and results[seg_name]["operating_income"] is None:
            results[seg_name]["operating_income"] = val

    return results


def update_annual_json(
    data_dir: str,
    ticker: str,
    fy: int,
    seg_results: Dict[str, Dict[str, Any]],
    filing_date: str,
) -> bool:
    """annual_{fy}.json の segments フィールドを更新"""
    ticker = ticker.upper()
    path = os.path.join(data_dir, ticker, f"annual_{fy}.json")
    if not os.path.exists(path):
        print(f"   [{ticker}] annual_{fy}.json が見つかりません")
        return False

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    existing = data.get("segments", {})
    updated = 0
    for seg_name, vals in seg_results.items():
        if vals["revenue"] is not None or vals["operating_income"] is not None:
            entry = {
                "revenue":          vals.get("revenue"),
                "operating_income": vals.get("operating_income"),
            }
            if vals.get("revenue") and vals.get("operating_income"):
                entry["operating_margin"] = round(
                    vals["operating_income"] / vals["revenue"], 4
                )
            existing[seg_name] = entry
            updated += 1

    data["segments"]              = existing
    data["segments_fetched_at"]   = datetime.now().strftime("%Y-%m-%d")
    data["segments_filing_date"]  = filing_date
    data["segments_source"]       = "SEC 10-K XBRL Instance Document (_htm.xml)"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"   [{ticker}] annual_{fy}.json 更新 ({updated}セグメント)")
    return updated > 0


def fetch_segments_for_ticker(
    ticker: str,
    data_dir: str,
    kpi_def: Dict[str, Any],
    max_years: int = 3,
    force: bool = False,
) -> bool:
    """1銘柄のセグメントデータを取得して annual_*.json に書き込む"""
    ticker = ticker.upper()
    print(f"\n{'─'*50}")
    print(f"🔄 {ticker}")
    print(f"{'─'*50}")

    # member_map: XBRLのMember名 → 表示用セグメント名
    member_map: Dict[str, str] = kpi_def.get("xbrl_members", {})
    if not member_map:
        print(f"   [{ticker}] kpi_config.py に xbrl_members 未定義 → スキップ")
        return False

    cik = get_cik(ticker, data_dir)
    if not cik:
        print(f"   [{ticker}] CIK取得失敗")
        return False
    print(f"   CIK: {cik}")

    filings = get_10k_filings(cik, max_years=max_years)
    if not filings:
        print(f"   [{ticker}] 10-Kファイリング取得失敗")
        return False
    print(f"   10-K ファイリング: {[f['fy'] for f in filings]}")

    success = 0
    for filing in filings:
        fy       = filing["fy"]
        accn     = filing["accn"]
        date     = filing["date"]
        xml_file = filing.get("xml_file", "")

        print(f"\n   FY{fy} ({accn}):")

        # 既存データのスキップ判定
        if not force:
            ann_path = os.path.join(data_dir, ticker, f"annual_{fy}.json")
            if os.path.exists(ann_path):
                with open(ann_path, encoding="utf-8") as f:
                    existing = json.load(f)
                segs = existing.get("segments", {})
                if segs and any(v.get("revenue") for v in segs.values()):
                    print(f"   既存データあり → スキップ（--force で再取得）")
                    success += 1
                    continue

        if not xml_file:
            print(f"   xml_file が不明 → スキップ")
            continue

        # XBRL Instance Document ダウンロード
        xml_text = download_xbrl_instance(cik, accn, xml_file)
        if not xml_text:
            continue

        # パース
        seg_results = parse_xbrl_segments(xml_text, member_map)
        del xml_text  # メモリ解放

        # 結果確認
        found = {k: v for k, v in seg_results.items() if v.get("revenue") is not None}
        if not found:
            print(f"   セグメント売上が取得できませんでした")
            continue

        for seg, vals in found.items():
            rev = vals.get("revenue", 0) or 0
            oi  = vals.get("operating_income")
            print(f"   {seg}: ${rev/1e9:.2f}B" + (f"  OI=${oi/1e9:.2f}B" if oi else ""))

        # annual_*.json に書き込み
        ok = update_annual_json(data_dir, ticker, fy, seg_results, date)
        if ok:
            success += 1

    return success > 0


def main():
    parser = argparse.ArgumentParser(
        description="SEC 10-K XBRL Instance Document からセグメント別売上取得（ローカル専用）"
    )
    parser.add_argument("tickers", nargs="*", help="対象ティッカー（省略時は全銘柄）")
    parser.add_argument("--years",  type=int, default=3, help="取得年数（デフォルト: 3）")
    parser.add_argument("--force",  action="store_true", help="既存データがある場合も再取得")
    args = parser.parse_args()

    if not HAS_BS4:
        print("エラー: beautifulsoup4 が必要です。pip install beautifulsoup4 lxml")
        sys.exit(1)

    # kpi_config.py を読み込む
    try:
        import importlib.util
        kpi_path = os.path.join(repo_root, "src", "value", "tanuki_valuation", "kpi_config.py")
        spec     = importlib.util.spec_from_file_location("kpi_config", kpi_path)
        kpi_mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(kpi_mod)
        KPI_DEFINITIONS = kpi_mod.KPI_DEFINITIONS
        print(f"kpi_config.py 読み込み完了: {len(KPI_DEFINITIONS)}銘柄")
    except Exception as e:
        print(f"kpi_config.py 読み込みエラー: {e}")
        KPI_DEFINITIONS = {}

    tickers  = [t.upper() for t in args.tickers] if args.tickers else get_all()
    data_dir = os.path.join(script_dir, "data")

    global _cik_cache
    _cik_cache = _load_cik_cache(data_dir)

    print("=" * 60)
    print("SEC XBRL Instance Document セグメント別売上取得")
    print(f"対象: {tickers}  取得年数: {args.years}年")
    print(f"データ保存先: {data_dir}")
    print("=" * 60)

    results = {}
    for ticker in tickers:
        defn = KPI_DEFINITIONS.get(ticker, {})
        ok   = fetch_segments_for_ticker(
            ticker   = ticker,
            data_dir = data_dir,
            kpi_def  = defn,
            max_years= args.years,
            force    = args.force,
        )
        results[ticker] = ok

    success = [t for t, ok in results.items() if ok]
    failed  = [t for t, ok in results.items() if not ok]
    print("\n" + "=" * 60)
    print(f"完了: {len(success)}/{len(tickers)}")
    if failed:
        print(f"失敗: {', '.join(failed)}")
    print("=" * 60)
    print("\n次のステップ:")
    print("  git add common/sec_data/data/")
    print("  git commit -m 'chore: update segment data'")
    print("  git push")


if __name__ == "__main__":
    main()
