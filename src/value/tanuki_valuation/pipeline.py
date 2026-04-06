import json
import os
from datetime import datetime
from .data_fetcher import TanukiDataFetcher
from .core_calculator import KoichiValuationCalculator

class TanukiValuationPipeline:
    def __init__(self):
        self.fetcher = TanukiDataFetcher()
        self.calculator = KoichiValuationCalculator()
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, tickers: list = None):
        print("=== TANUKI VALUATION Phase 4 実行開始（成長率減衰カーブ＋RPO補正＋1〜3年後予測）===")
        
        if tickers is None:
            tickers = ["TSLA", "PLTR", "SOFI", "CELH", "NVDA", "AMD", "APP", "SOUN", "RKLB", "ONDS"]

        results = {}
        for ticker in tickers:
            print(f"\n🔄 Updating {ticker}...")
            financials = self.fetcher.get_financials(ticker)
            
            if "error" in financials or financials.get("diluted_shares", 0) <= 100_000:
                print(f"❌ {ticker} skipped")
                continue

            valuation = self.calculator.calculate_pt(financials)
            results[ticker] = valuation
            print(f"✅ {ticker} 更新完了")

        # 保存（将来価値も含めて）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"tanuki_valuation_phase4_{timestamp}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n🎉 TANUKI VALUATION Phase 4 更新完了！")
        print(f"   結果保存先: {output_path}")
        return results

if __name__ == "__main__":
    pipeline = TanukiValuationPipeline()
    pipeline.run()