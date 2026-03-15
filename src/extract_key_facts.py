"""
SEC EDGARから四半期財務データを抽出するモジュール
edgartools ラッパー
"""
from edgar import Company, set_identity
from datetime import datetime, timedelta
import pandas as pd

# ユーザーエージェント設定（必須）
set_identity("Your Name your.email@example.com")

def extract_quarterly_data(cik, ticker, max_quarters=20):
    """
    CIKとティッカーから四半期データを取得
    戻り値: リスト of dict (各四半期の主要数値)
    """
    company = Company(cik, ticker)
    filings = company.get_filings(form="10-Q", limit=max_quarters)
    
    quarters = []
    for filing in filings:
        try:
            # ファクトテーブルから必要な項目を抽出
            facts = filing.obj().facts  # 実際のメソッドはedgartoolsに依存
            # 簡略化のため、ここではサンプル的な実装にしています
            # 実際には facts から us-gaap:NetIncomeLoss などを取得
            # デモ用にダミーデータを返す（実際のコードでは適切に実装）
            # 注意：本番ではfactsから正しく抽出する必要あり
            
            # ダミー（実際のコードに置き換え）
            period_data = {
                "filing_date": filing.filing_date,
                "form": "10-Q",
                "net_income": 0.0,
                "weighted_average_shares_diluted": 0.0,
                "effective_tax_rate": 0.21,
                # 他の項目（SBCなど）はadjustment_detectorでfactsから取得する想定
            }
            # 実際の取得処理...
            
            quarters.append(period_data)
        except Exception as e:
            print(f"Error processing filing {filing.filing_date}: {e}")
            continue
    
    return quarters
