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
from common.sec_data.fetcher import SECFetcher, load_company_facts
from common.sec_data.parser import SECParser
from common.sec_data.quarterly import build_raw_table, save_raw_table
from common.sec_data.normalizer import normalize, save_normalized
from common.sec_data.ttm_calculator import calc_ttm, save_ttm_series


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

        # 1. company_facts 取得
        raw = fetcher.fetch_company_facts(ticker)
        if not raw:
            failed.append(ticker)
            continue

        # 2. 従来パース＆保存（annual等）
        parsed = parser.parse_and_save(ticker)
        if parsed:
            annual_years = list(parsed.get("annual", {}).keys())[:3]
            print(f"   年次: {annual_years}")
        else:
            failed.append(ticker)
            continue

        # 3. 四半期Raw Table生成
        try:
            company_facts = load_company_facts(ticker, data_dir=data_dir)
            if company_facts is None:
                print(f"   [WARN] company_facts 読み込み失敗 → TTMスキップ")
                success += 1
                continue

            raw_table = build_raw_table(ticker, company_facts)
            save_raw_table(ticker, raw_table)
            print(f"   Raw Table: {len(raw_table.get('fields', {}))} fields")
        except Exception as e:
            print(f"   [WARN] Raw Table生成エラー: {e} → TTMスキップ")
            success += 1
            continue

        # 4. 正規化（YTD→Q差分変換）
        try:
            normalized = normalize(ticker, raw_table)
            save_normalized(ticker, normalized)
            print(f"   Normalized: OK")
        except Exception as e:
            print(f"   [WARN] Normalize エラー: {e} → TTMスキップ")
            success += 1
            continue

        # 5. TTMシリーズ生成
        try:
            ttm_result = calc_ttm(ticker, normalized)
            save_ttm_series(ticker, ttm_result)
            ttm_fields = list(ttm_result.get("ttm", {}).keys())
            print(f"   TTM: {len(ttm_fields)} fields → {ttm_fields[:5]}...")
        except Exception as e:
            print(f"   [WARN] TTM計算エラー: {e}")

        success += 1

    # サマリー
    print("\n" + "=" * 60)
    print(f"完了: {success}/{len(tickers)}")
    if failed:
        print(f"失敗: {', '.join(failed)}")
    print("=" * 60)

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
