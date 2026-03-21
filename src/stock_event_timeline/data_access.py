import sqlite3
from typing import Optional
from datetime import datetime
import pandas as pd
import yfinance as yf

from src.stock_event_timeline.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS price_history (
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, date)
        )
        """
    )
    conn.commit()
    conn.close()

def fetch_and_store_price_history(ticker: str, period_years: int = 5) -> pd.DataFrame:
    init_db()
    # 1. データベース接続をここで作成
    conn = get_connection()
    
    end = datetime.utcnow()
    start = datetime(end.year - period_years, end.month, end.day)
    df = yf.download(ticker, start=start, end=end, auto_adjust=False)
    
    # --- 以下の部分をこの通りに書き換えてください ---
    # 1. カラムの階層を強制的にフラット化（TSLAなどの銘柄名を消す）
    if isinstance(df.columns, pd.MultiIndex):
        # 0番目の階層（Open, High...）だけを残し、1番目の階層（TSLA）を捨てる
        df.columns = df.columns.get_level_values(0)

    # 2. インデックス（Date）をカラムに移動
    df = df.reset_index()

    # 3. カラム名を小文字 & アンダーバーに統一
    # ここで 'Date' -> 'date', 'Open' -> 'open' に変換されます
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    # ----------------------------------------------

    # 4. tickerカラムを追加
    df["ticker"] = ticker.upper()

    # 5. SQLiteへ保存
    # 注意: dfのカラム名とto_sqlのリストが一致している必要があります
    df[["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]].to_sql(
        "price_history", conn, if_exists="append", index=False
    )
    
    conn.close()
    return df

def load_price_history(ticker: str, years: int = 5) -> pd.DataFrame:
    init_db()

    conn = get_connection()
    # SQLでtickerは大文字で比較するのが安全です
    cur = conn.cursor()
    cur.execute(
        "SELECT date, open, high, low, close, adj_close, volume "
        "FROM price_history WHERE ticker = ? ORDER BY date",
        (ticker.upper(),),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return fetch_and_store_price_history(ticker, years)

    df = pd.DataFrame(
        rows,
        columns=["date", "open", "high", "low", "close", "adj_close", "volume"],
    )
    df["date"] = pd.to_datetime(df["date"])
    return df