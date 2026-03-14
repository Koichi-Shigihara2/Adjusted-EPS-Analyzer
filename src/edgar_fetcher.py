"""
edgar_fetcher.py - SEC EDGAR から filing を取得するユーティリティ
pipeline.py からは直接使用しない（extract_key_facts が内部で使用）が、
単体テストや個別取得のために公開している。
"""
from edgar import Company, set_identity


def fetch_filings(ticker: str, count: int = 45):
    """
    ticker の最新 count 件の 10-Q / 10-K filings を返す。
    count=45 は四半期ベースで約 10 年分（4×10 + 年次 5 = 45）。
    """
    set_identity("jamablue01@gmail.com")
    company  = Company(ticker)
    filings  = company.get_filings(form=["10-Q", "10-K"])
    return filings[:count]
