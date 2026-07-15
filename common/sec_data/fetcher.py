"""
SEC EDGAR データ取得モジュール
Company Facts API を使用してBS/PL/CFデータを取得・保存
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any

from .config import get_all, get_ticker_info


class SECFetcher:
    """SEC EDGAR Company Facts API クライアント"""
    
    BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts"
    CIK_LOOKUP_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    
    # SEC APIは10リクエスト/秒制限
    RATE_LIMIT_DELAY = 0.15
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # CIKキャッシュ
        self.cik_cache_path = os.path.join(self.data_dir, "_cik_cache.json")
        self.cik_cache = self._load_cik_cache()
        
        # User-Agent必須（SEC要件）
        self.headers = {
            "User-Agent": "Koichi Personal Investment Tools koichi@example.com",
            "Accept": "application/json"
        }
    
    def _load_cik_cache(self) -> dict:
        """CIKキャッシュ読み込み"""
        if os.path.exists(self.cik_cache_path):
            try:
                with open(self.cik_cache_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cik_cache(self):
        """CIKキャッシュ保存"""
        with open(self.cik_cache_path, "w") as f:
            json.dump(self.cik_cache, f, indent=2)
    
    def get_cik(self, ticker: str) -> Optional[str]:
        """ティッカーからCIKを取得（10桁ゼロパディング）"""
        ticker = ticker.upper()
        
        # キャッシュ確認
        if ticker in self.cik_cache:
            return self.cik_cache[ticker]
        
        # SEC ticker.json から取得
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for entry in data.values():
                    if entry.get("ticker", "").upper() == ticker:
                        cik = str(entry["cik_str"]).zfill(10)
                        self.cik_cache[ticker] = cik
                        self._save_cik_cache()
                        return cik
        except Exception as e:
            print(f"   [CIK ERROR] {ticker}: {e}")
        
        return None
    
    def fetch_company_facts(self, ticker: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Company Facts API から全データ取得
        
        Returns:
            dict: SEC Company Facts 生データ
        """
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.data_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        
        raw_path = os.path.join(ticker_dir, "company_facts.json")
        
        # キャッシュ確認（24時間有効）
        if not force_refresh and os.path.exists(raw_path):
            age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(raw_path))).total_seconds()
            if age < 86400:
                try:
                    with open(raw_path, "r", encoding="utf-8") as f:
                        print(f"   [{ticker}] キャッシュから読み込み")
                        return json.load(f)
                except:
                    pass
        
        # CIK取得
        cik = self.get_cik(ticker)
        if not cik:
            print(f"   [{ticker}] CIK取得失敗")
            return None
        
        # Company Facts API呼び出し
        url = f"{self.BASE_URL}/CIK{cik}.json"
        print(f"   [{ticker}] SEC API取得中... (CIK: {cik})")
        
        try:
            time.sleep(self.RATE_LIMIT_DELAY)
            resp = requests.get(url, headers=self.headers, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # 保存
                with open(raw_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"   [{ticker}] SEC API取得完了")
                return data
            else:
                print(f"   [{ticker}] SEC API エラー: {resp.status_code}")
                return None
                
        except Exception as e:
            print(f"   [{ticker}] SEC API 例外: {e}")
            return None
    
    def fetch_submissions(self, ticker: str, force_refresh: bool = False) -> Optional[Dict[str, str]]:
        """
        submissions API（recent + 必要な過去分アーカイブ）から
        10-K/10-K/A/10-Q/10-Q/A の accession Number -> reportDate マッピングを取得・保存する。

        FY52WEEK-BUCKET-MISPLACE-1調査で判明した「fyタグはfiling単位の粗いラベルで
        比較年度再掲時に書き換わる」問題への対応。reportDate==end_dateが成立する
        factのみが「本人の当期データ」であることが全106銘柄・年次830件超・四半期859件で
        例外なく確認できている（parser.pyの本人データ判定ロジックが参照する）。

        Returns:
            dict: {accn: reportDate} のマッピング（取得失敗時はNone）
        """
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.data_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)

        out_path = os.path.join(ticker_dir, "submissions.json")

        # キャッシュ確認（24時間有効。10-K/10-Q提出時のみ更新されれば十分なため
        # company_facts.jsonと同じ頻度でよい）
        if not force_refresh and os.path.exists(out_path):
            age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(out_path))).total_seconds()
            if age < 86400:
                try:
                    with open(out_path, "r", encoding="utf-8") as f:
                        return json.load(f).get("accn_to_reportdate", {})
                except Exception:
                    pass

        cik = self.get_cik(ticker)
        if not cik:
            print(f"   [{ticker}] submissions: CIK取得失敗")
            return None

        relevant_forms = {"10-K", "10-K/A", "10-Q", "10-Q/A"}
        accn_to_reportdate: Dict[str, str] = {}

        def _extract(recent_or_archive: dict) -> None:
            forms = recent_or_archive.get("form", [])
            accns = recent_or_archive.get("accessionNumber", [])
            report_dates = recent_or_archive.get("reportDate", [])
            for form, accn, rd in zip(forms, accns, report_dates):
                if form in relevant_forms and rd:
                    accn_to_reportdate[accn] = rd

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            time.sleep(self.RATE_LIMIT_DELAY)
            resp = requests.get(url, headers=self.headers, timeout=30)
        except Exception as e:
            print(f"   [{ticker}] submissions API 例外: {e}")
            return None

        if resp.status_code != 200:
            print(f"   [{ticker}] submissions API エラー: {resp.status_code}")
            return None

        data = resp.json()
        _extract(data.get("filings", {}).get("recent", {}))

        # 過去分アーカイブ（filings.recentは直近分のみのため、古いfilingは別JSONに分割）
        for finfo in data.get("filings", {}).get("files", []):
            fname = finfo.get("name")
            if not fname:
                continue
            archive_url = f"https://data.sec.gov/submissions/{fname}"
            try:
                time.sleep(self.RATE_LIMIT_DELAY)
                aresp = requests.get(archive_url, headers=self.headers, timeout=30)
            except Exception as e:
                print(f"   [{ticker}] submissions archive({fname}) 例外: {e}")
                continue
            if aresp.status_code != 200:
                print(f"   [{ticker}] submissions archive({fname}) エラー: {aresp.status_code}")
                continue
            _extract(aresp.json())

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {"ticker": ticker, "cik": cik, "accn_to_reportdate": accn_to_reportdate},
                f, ensure_ascii=False, indent=2,
            )

        print(f"   [{ticker}] submissions取得完了 ({len(accn_to_reportdate)}件)")
        return accn_to_reportdate

    def fetch_all(self, tickers: list = None, force_refresh: bool = False) -> Dict[str, bool]:
        """
        複数ティッカーの一括取得
        
        Returns:
            dict: {ticker: success_flag}
        """
        if tickers is None:
            tickers = get_all()
        
        results = {}
        total = len(tickers)
        
        print(f"\n{'='*60}")
        print(f"SEC EDGAR データ一括取得開始（{total}銘柄）")
        print(f"{'='*60}")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{total}] {ticker}")
            info = get_ticker_info(ticker)
            print(f"   {info['name']} ({info['status']})")
            
            data = self.fetch_company_facts(ticker, force_refresh)
            results[ticker] = data is not None
        
        # サマリー
        success = sum(1 for v in results.values() if v)
        print(f"\n{'='*60}")
        print(f"取得完了: {success}/{total}")
        print(f"{'='*60}")
        
        return results


def load_company_facts(ticker: str, data_dir: str = None) -> Optional[Dict[str, Any]]:
    """
    {data_dir}/{ticker}/company_facts.json を読み込んで返す。

    ファイルが存在しない場合は None を返す（ネットワーク取得は行わない）。
    取得が必要な場合は SECFetcher.fetch_company_facts() を使うこと。
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
    path = os.path.join(data_dir, ticker.upper(), "company_facts.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"   [{ticker}] company_facts.json 読み込みエラー: {e}")
        return None


def load_submissions(ticker: str, data_dir: str = None) -> Dict[str, str]:
    """
    {data_dir}/{ticker}/submissions.json を読み込んで accn_to_reportdate を返す。

    ファイルが存在しない場合は空dictを返す（ネットワーク取得は行わない）。
    取得が必要な場合は SECFetcher.fetch_submissions() を使うこと。
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
    path = os.path.join(data_dir, ticker.upper(), "submissions.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("accn_to_reportdate", {})
    except Exception as e:
        print(f"   [{ticker}] submissions.json 読み込みエラー: {e}")
        return {}


def _get_latest_accn(company_facts: dict) -> Optional[str]:
    """company_facts 内で最も最近の accn（filingアクセッション番号）を返す"""
    latest_filed = ""
    latest_accn = None
    try:
        for concept_data in company_facts.get("facts", {}).get("us-gaap", {}).values():
            for unit_data in concept_data.get("units", {}).values():
                for entry in unit_data:
                    filed = entry.get("filed", "")
                    if filed > latest_filed:
                        latest_filed = filed
                        latest_accn = entry.get("accn")
    except Exception:
        pass
    return latest_accn


def needs_quarterly_update(ticker: str, company_facts: dict, run_state: dict) -> bool:
    """
    company_facts の最新 filing の accn を run_state と比較。
    差分がある（または未記録）場合のみ True を返す。
    """
    latest_accn = _get_latest_accn(company_facts)
    if latest_accn is None:
        return False
    saved_accn = run_state.get(ticker.upper(), {}).get("quarterly", {}).get("last_accn")
    return latest_accn != saved_accn


def update_quarterly_run_state(ticker: str, latest_accn: str, run_state: dict) -> dict:
    """run_state の quarterly セクションを更新して返す"""
    ticker = ticker.upper()
    updated = dict(run_state)
    updated.setdefault(ticker, {})["quarterly"] = {
        "last_fetched": datetime.now().strftime("%Y-%m-%d"),
        "last_accn": latest_accn,
    }
    return updated


if __name__ == "__main__":
    fetcher = SECFetcher()

    # テスト: 単一ティッカー
    data = fetcher.fetch_company_facts("TSLA")
    if data:
        print(f"\nTSLA facts keys: {list(data.get('facts', {}).keys())}")
