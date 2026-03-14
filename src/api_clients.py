"""
api_clients.py - 各外部APIクライアントのシングルトン管理
xAI (Grok) / OpenAI / Alpha Vantage / FRED / FMP
"""
import os
from openai import OpenAI


def get_xai_client() -> OpenAI:
    """xAI (Grok) API クライアント"""
    return OpenAI(
        api_key=os.environ.get("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )


def get_openai_client() -> OpenAI:
    """OpenAI API クライアント（フォールバック用）"""
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def get_av_key() -> str:
    """Alpha Vantage API キー"""
    return os.environ.get("ALPHA_VANTAGE_API_KEY", "")


def get_fred_key() -> str:
    """FRED API キー"""
    return os.environ.get("FRED_API_KEY", "")


def get_fmp_key() -> str:
    """Financial Modeling Prep API キー"""
    return os.environ.get("FMP_API_KEY", "")
