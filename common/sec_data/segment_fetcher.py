"""
SEC セグメント別売上取得スクリプト（ローカル専用）

10-K の iXBRL から セグメント別売上・営業利益を抽出し、
annual_{year}.json の "segments" フィールドに追記する。

使用方法（PowerShell）:
    python common/sec_data/segment_fetcher.py              # 全銘柄
    python common/sec_data/segment_fetcher.py NVDA         # 特定銘柄のみ
    python common/sec_data/segment_fetcher.py NVDA --years 3  # 直近3年

GitHub Actions では実行しない。ローカルで実行してpushする運用。

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
    from bs4 import BeautifulSoup
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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
SEC_BASE = "https://www.sec.gov"
RATE_LIMIT_DELAY = 0.15   # SEC: 10req/秒上限

# ── セグメント別売上の iXBRL タグ候補 ────────────────────────
SEGMENT_REVENUE_TAGS = [
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:Revenues",
    "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
    "us-gaap:SalesRevenueNet",
]

SEGMENT_OPINCOME_TAGS = [
    "us-gaap:OperatingIncomeLoss",
    "us-gaap:GrossProfit",
]

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
        url = "https://www.sec.gov/files/company_tickers.json"
        r = requests.get(url, headers=SEC_HEADERS, timeout=15)
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
    SEC submissions API から 10-K ファイリング一覧を取得

    Returns:
        [{"accn": "0001045810-25-000011", "date": "2025-02-26", "fy": 2025}, ...]
    """
    url = f"{SEC_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=&owner=include&count=10&search_text=&output=atom"
    # submissions endpoint の方が安定
    url2 = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(url2, headers=SEC_HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"   submissions API エラー: {r.status_code}")
            return []
        data = r.json()
        filings = data.get("filings", {}).get("recent", {})
        forms   = filings.get("form", [])
        accns   = filings.get("accessionNumber", [])
        dates   = filings.get("filingDate", [])
        fys     = filings.get("reportDate", [])

        results = []
        for i, f in enumerate(forms):
            if f == "10-K":
                fy_str = fys[i] if i < len(fys) else ""
                fy = int(fy_str[:4]) if fy_str else 0
                results.append({
                    "accn": accns[i],
                    "date": dates[i],
                    "fy":   fy,
                })
                if len(results) >= max_years:
                    break
        return results
    except Exception as e:
        print(f"   submissions API 例外: {e}")
        return []


def get_10k_htm_url(cik: str, accn: str) -> Optional[str]:
    """
    accessionNumber から 10-K の HTM ファイル URL を取得

    Returns:
        "https://www.sec.gov/Archives/edgar/data/.../xxx-20250126.htm"
    """
    accn_nodash = accn.replace("-", "")
    index_url = f"{SEC_BASE}/Archives/edgar/data/{int(cik)}/{accn_nodash}/{accn}-index.json"
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(index_url, headers=SEC_HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        index = r.json()
        # 10-K 本文 HTM を探す
        for item in index.get("directory", {}).get("item", []):
            name = item.get("name", "")
            # メインの10-K HTMLを特定（通常は最大のHTMファイル）
            if name.endswith(".htm") and not name.startswith("R") and "ex" not in name.lower():
                return f"{SEC_BASE}/Archives/edgar/data/{int(cik)}/{accn_nodash}/{name}"
        # フォールバック: 全HTMから最大ファイルを選択
        htm_files = [
            item for item in index.get("directory", {}).get("item", [])
            if item.get("name", "").endswith(".htm")
        ]
        if htm_files:
            largest = max(htm_files, key=lambda x: int(x.get("size", 0) or 0))
            name = largest["name"]
            return f"{SEC_BASE}/Archives/edgar/data/{int(cik)}/{accn_nodash}/{name}"
    except Exception as e:
        print(f"   index取得エラー: {e}")
    return None


def download_10k_html(url: str) -> Optional[str]:
    """10-K HTML をダウンロード（メモリのみ、保存しない）"""
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(url, headers=SEC_HEADERS, timeout=60, stream=True)
        if r.status_code != 200:
            print(f"   HTMダウンロードエラー: {r.status_code}")
            return None
        # 最大50MBまで
        content = b""
        for chunk in r.iter_content(chunk_size=65536):
            content += chunk
            if len(content) > 50 * 1024 * 1024:
                print("   警告: ファイルサイズが50MBを超えました。打ち切ります。")
                break
        print(f"   ダウンロード完了: {len(content)/1024/1024:.1f} MB")
        return content.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"   ダウンロード例外: {e}")
        return None


def parse_ixbrl_segments(
    html: str,
    ticker: str,
    segment_names: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    iXBRL HTML からセグメント別売上・営業利益を抽出

    Args:
        html:          10-K HTML テキスト
        ticker:        銘柄コード（ログ用）
        segment_names: kpi_config.py で定義されたセグメント名リスト

    Returns:
        {
          "Data Center": {"revenue": 115200000000, "operating_income": 81200000000},
          "Gaming":      {"revenue": 3100000000,   "operating_income": None},
          ...
        }
    """
    if not HAS_BS4:
        print("   エラー: beautifulsoup4 が必要です。pip install beautifulsoup4 lxml")
        return {}

    soup = BeautifulSoup(html, "lxml")
    results: Dict[str, Dict[str, Any]] = {seg: {"revenue": None, "operating_income": None} for seg in segment_names}

    # iXBRL タグ（ix:nonFraction / ix:nonNumeric）を収集
    # contextRef にセグメント名が含まれるものを抽出
    ix_tags = soup.find_all(re.compile(r"ix:nonFraction", re.IGNORECASE))
    print(f"   iXBRL タグ数: {len(ix_tags)}")

    # セグメント名を正規化してマッチングキーを作成
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    seg_norm = {normalize(seg): seg for seg in segment_names}

    found_count = 0
    for tag in ix_tags:
        name_attr    = (tag.get("name") or "").lower()
        context_ref  = tag.get("contextref") or tag.get("contextRef") or ""
        context_norm = normalize(context_ref)
        val_str      = tag.get_text(strip=True).replace(",", "").replace("$", "").replace("(", "-").replace(")", "")

        # 数値変換
        try:
            scale_attr = tag.get("scale") or tag.get("data-scale") or "0"
            scale = 10 ** int(scale_attr)
            val = float(val_str) * scale
        except (ValueError, TypeError):
            continue

        # セグメント名マッチング
        matched_seg = None
        for seg_key, seg_orig in seg_norm.items():
            if seg_key in context_norm:
                matched_seg = seg_orig
                break
        if not matched_seg:
            continue

        # 売上タグ
        is_rev = any(t.split(":")[-1].lower() in name_attr for t in SEGMENT_REVENUE_TAGS)
        # 営業利益タグ
        is_oi  = any(t.split(":")[-1].lower() in name_attr for t in SEGMENT_OPINCOME_TAGS)

        if is_rev and results[matched_seg]["revenue"] is None:
            results[matched_seg]["revenue"] = val
            found_count += 1
        elif is_oi and results[matched_seg]["operating_income"] is None:
            results[matched_seg]["operating_income"] = val
            found_count += 1

    print(f"   セグメントデータ取得: {found_count}件")
    return results


def update_annual_json(
    data_dir: str,
    ticker: str,
    fy: int,
    segments_raw: Dict[str, Dict[str, Any]],
    filing_date: str,
) -> bool:
    """
    annual_{fy}.json の "segments" フィールドを更新

    既存データを上書きせずに segments キーのみ追記/更新する。
    """
    ticker = ticker.upper()
    path = os.path.join(data_dir, ticker, f"annual_{fy}.json")

    if not os.path.exists(path):
        print(f"   [{ticker}] annual_{fy}.json が見つかりません")
        return False

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # 既存の segments を保持しつつ更新
    existing_segs = data.get("segments", {})
    for seg_name, seg_vals in segments_raw.items():
        if seg_vals["revenue"] is not None or seg_vals["operating_income"] is not None:
            existing_segs[seg_name] = {
                "revenue":          seg_vals.get("revenue"),
                "operating_income": seg_vals.get("operating_income"),
            }
            # 営業利益率を自動計算
            if seg_vals.get("revenue") and seg_vals.get("operating_income"):
                existing_segs[seg_name]["operating_margin"] = round(
                    seg_vals["operating_income"] / seg_vals["revenue"], 4
                )

    data["segments"] = existing_segs
    data["segments_fetched_at"]   = datetime.now().strftime("%Y-%m-%d")
    data["segments_filing_date"]  = filing_date
    data["segments_source"]       = "SEC 10-K iXBRL (local parse)"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    non_null = sum(1 for v in existing_segs.values() if v.get("revenue") is not None)
    print(f"   [{ticker}] annual_{fy}.json 更新完了 (セグメント{non_null}件)")
    return True


def fetch_segments_for_ticker(
    ticker: str,
    data_dir: str,
    segment_names: List[str],
    max_years: int = 3,
) -> bool:
    """1銘柄のセグメントデータを取得してannual_*.jsonに書き込む"""
    ticker = ticker.upper()
    print(f"\n{'─'*50}")
    print(f"🔄 {ticker}")
    print(f"{'─'*50}")

    if not segment_names:
        print(f"   [{ticker}] kpi_config.py にセグメント定義なし → スキップ")
        return False

    # CIK 取得
    cik = get_cik(ticker, data_dir)
    if not cik:
        print(f"   [{ticker}] CIK取得失敗")
        return False
    print(f"   CIK: {cik}")

    # 10-K ファイリング一覧
    filings = get_10k_filings(cik, max_years=max_years)
    if not filings:
        print(f"   [{ticker}] 10-Kファイリング取得失敗")
        return False
    print(f"   10-K ファイリング: {[f['fy'] for f in filings]}")

    success_count = 0
    for filing in filings:
        fy   = filing["fy"]
        accn = filing["accn"]
        date = filing["date"]
        print(f"\n   FY{fy} ({accn}):")

        # annual_{fy}.json が存在し既にsegmentsがある場合はスキップ
        ann_path = os.path.join(data_dir, ticker, f"annual_{fy}.json")
        if os.path.exists(ann_path):
            with open(ann_path, encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("segments"):
                non_null = sum(1 for v in existing["segments"].values()
                               if v.get("revenue") is not None)
                print(f"   既存データあり（{non_null}セグメント）→ スキップ（--force で強制更新）")
                success_count += 1
                continue

        # HTM URL 取得
        htm_url = get_10k_htm_url(cik, accn)
        if not htm_url:
            print(f"   HTM URL取得失敗")
            continue
        print(f"   URL: {htm_url}")

        # HTML ダウンロード（メモリのみ）
        html = download_10k_html(htm_url)
        if not html:
            continue

        # iXBRL パース
        segments_raw = parse_ixbrl_segments(html, ticker, segment_names)
        del html  # メモリ解放

        # annual_*.json に書き込み
        ok = update_annual_json(data_dir, ticker, fy, segments_raw, date)
        if ok:
            success_count += 1

    return success_count > 0


def main():
    parser = argparse.ArgumentParser(description="SEC 10-K セグメント別売上取得（ローカル専用）")
    parser.add_argument("tickers", nargs="*", help="対象ティッカー（省略時は全銘柄）")
    parser.add_argument("--years",  type=int, default=3, help="取得年数（デフォルト: 3）")
    parser.add_argument("--force",  action="store_true", help="既存データがある場合も再取得")
    args = parser.parse_args()

    if not HAS_BS4:
        print("エラー: beautifulsoup4 が必要です。")
        print("  pip install beautifulsoup4 lxml")
        sys.exit(1)

    # kpi_config.py からセグメント定義を読み込む
    try:
        kpi_config_path = os.path.join(
            repo_root, "src", "value", "tanuki_valuation", "kpi_config.py"
        )
        import importlib.util
        spec = importlib.util.spec_from_file_location("kpi_config", kpi_config_path)
        kpi_config = importlib.util.load_module_from_spec(spec)
        spec.loader.exec_module(kpi_config)
        KPI_DEFINITIONS = kpi_config.KPI_DEFINITIONS
    except Exception as e:
        print(f"kpi_config.py 読み込みエラー: {e}")
        KPI_DEFINITIONS = {}

    tickers = [t.upper() for t in args.tickers] if args.tickers else get_all()
    data_dir = os.path.join(script_dir, "data")

    # CIK キャッシュをロード
    global _cik_cache
    _cik_cache = _load_cik_cache(data_dir)

    print("=" * 60)
    print("SEC 10-K セグメント別売上取得（ローカル専用）")
    print(f"対象: {tickers}")
    print(f"取得年数: {args.years}年")
    print(f"データ保存先: {data_dir}")
    print("=" * 60)

    results = {}
    for ticker in tickers:
        defn = KPI_DEFINITIONS.get(ticker, {})
        seg_names = defn.get("segments", [])
        ok = fetch_segments_for_ticker(
            ticker=ticker,
            data_dir=data_dir,
            segment_names=seg_names,
            max_years=args.years,
        )
        results[ticker] = ok

    # サマリー
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
