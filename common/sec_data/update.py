"""
SEC データ一括更新スクリプト
GitHub Actions から実行される

使用方法:
    python common/sec_data/update.py              # 全ティッカー
    python common/sec_data/update.py TSLA PLTR    # 特定ティッカーのみ
"""

import sys
import os

# common/sec_data/ から実行される前提でパス設定
script_dir = os.path.dirname(os.path.abspath(__file__))
common_dir = os.path.dirname(script_dir)
repo_root = os.path.dirname(common_dir)
sys.path.insert(0, repo_root)

from common.sec_data.config import get_all
from common.sec_data.fetcher import SECFetcher
from common.sec_data.parser import SECParser


def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else get_all()
    
    # データ保存先をcommon/sec_data/data/に設定
    data_dir = os.path.join(script_dir, "data")
    
    fetcher = SECFetcher(data_dir=data_dir)
    parser = SECParser(data_dir=data_dir)
    
    print("=" * 60)
    print("SEC EDGAR データ更新")
    print(f"対象: {len(tickers)} 銘柄")
    print(f"保存先: {data_dir}")
    print("=" * 60)
    
    success = 0
    failed = []
    
    for ticker in tickers:
        print(f"\n--- {ticker} ---")
        
        # 1. データ取得
        raw = fetcher.fetch_company_facts(ticker)
        if not raw:
            failed.append(ticker)
            continue
        
        # 2. パース＆保存
        parsed = parser.parse_and_save(ticker)
        if parsed:
            success += 1
            annual_years = list(parsed.get("annual", {}).keys())[:3]
            print(f"   年次: {annual_years}")
        else:
            failed.append(ticker)
    
    # サマリー
    print("\n" + "=" * 60)
    print(f"完了: {success}/{len(tickers)}")
    if failed:
        print(f"失敗: {', '.join(failed)}")
    print("=" * 60)
    
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
