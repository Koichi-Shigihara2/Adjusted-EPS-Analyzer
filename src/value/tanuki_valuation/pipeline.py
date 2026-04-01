from .data_fetcher import TanukiDataFetcher
from .core_calculator import KoichiValuationCalculator
import json, os
from datetime import datetime

def run_update():
    fetcher = TanukiDataFetcher()
    calculator = KoichiValuationCalculator()
    tickers = ["MSFT", "AMZN"]   # ← テスト用に2銘柄だけ

    print("=== TANUKI VALUATION テスト実行開始 (MSFT & AMZN) ===\n")
    results = {}
    for ticker in tickers:
        print(f"🔄 Updating {ticker}...")
        financials = fetcher.get_financials(ticker)
        
        if "error" in financials:
            print(f"❌ {ticker} skipped - {financials.get('error')}")
            continue
            
        calc = calculator.calculate_pt(financials)
        results[ticker] = calc
        
        print(f"   → FCF 5yr Avg     : ${financials.get('fcf_5yr_avg', 0):,.0f}")
        print(f"   → Diluted Shares  : {financials.get('diluted_shares', 0):,.0f}")
        print(f"   → Intrinsic Value (Per Share): ${calc.get('intrinsic_value_per_share', 0):.2f}")
        print(f"✅ {ticker} 更新完了\n")

    data_dir = "docs/value-monitor/tanuki_valuation/data"
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(f"{data_dir}/history", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"{data_dir}/history/{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    with open(f"{data_dir}/latest.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("🎉 テスト完了！ MSFTとAMZNの結果を確認してください。")

if __name__ == "__main__":
    run_update()