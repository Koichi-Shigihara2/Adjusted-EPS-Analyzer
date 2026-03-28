import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)  # 1時間キャッシュ
def load_price_history(ticker: str, years: int = 5) -> pd.DataFrame:
    """yfinanceから株価を取得し、DataFrameで返す（キャッシュ付き）"""
    end = datetime.utcnow()
    start = end - timedelta(days=years*365)
    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)

    if df.empty:
        return pd.DataFrame()

    # MultiIndex対策
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    return df
