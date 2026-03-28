# src/value/tanuki_valuation/pipeline.py
import os
import json
from datetime import datetime
from .core_calculator import KoichiValuationCalculator      # ← 相対インポートに修正
from .data_fetcher import TanukiDataFetcher                # ← 相対インポートに修正
from .segment_kpi_ai import SegmentKPIAI                   # ← 相対インポートに修正

def run_update():
    fetcher = TanukiDataFetcher()
    ai = SegmentKPIAI()
    calc = KoichiValuationCalculator()
    
    # テスト銘柄＋全保有銘柄
    tickers = ["MSFT", "AMZN"] + ["SOFI","TSLA","PLTR","CELH","NVDA","AMD","APP","SOUN","RKLB","ONDS","FIG"]
    
    for ticker in tickers:
        print(f"🔄 Updating {ticker}...")
        data = fetcher.get_financials(ticker)
        
        # AIセグメントKPI（ブル/中立/ベア）
        sec_text = "SECデータ取得中（FMP連携）"   # 後続Phaseで本実装
        scenarios = ai.generate_scenarios(ticker, sec_text)
        
        # Koichi式v5.1計算
        result = calc.calculate_pt(data)
        
        # 履歴保存（手戻り4対応）
        history_dir = f"docs/value-monitor/tanuki_valuation/data/{ticker}/history"
        os.makedirs(history_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"{history_dir}/{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 最新結果保存（画面で使用）
        latest_path = f"docs/value-monitor/tanuki_valuation/data/{ticker}/latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {ticker} 更新完了")
    
    print("🎉 TANUKI VALUATION 全銘柄更新完了！")

if __name__ == "__main__":
    run_update()
