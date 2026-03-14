import yaml, json, os
from edgar_fetcher import fetch_filings
from xbrl_parser import parse_xbrl
from adjustment_detector import detect_adjustments
from tax_adjuster import apply_tax
from eps_calculator import calculate_eps
from ai_analyzer import analyze_with_gemini_v3 # 追加

def save_result(ticker, accession_no, result):
    os.makedirs(f"data/{ticker}", exist_ok=True)
    with open(f"data/{ticker}/{accession_no}.json", "w") as f:
        json.dump(result, f, indent=2)

def run():
    with open("config/monitor_tickers.yaml") as f:
        tickers = yaml.safe_load(f)["tickers"]

    for ticker in tickers:
        print(f"Processing {ticker}...")
        filings = fetch_filings(ticker)
        
        results_history = []
        # enumerateを使用してインデックス i を取得
        for i, filing in enumerate(filings):
            try:
                data = parse_xbrl(filing)
                if not data: continue
                
                adjustments = detect_adjustments(data)
                net_adjustments = apply_tax(adjustments, data)
                result = calculate_eps(data, net_adjustments)

                # 最新の決算（最初の1件）のみAI分析を実行
                if i == 0:
                    print(f"Generating AI analysis for {ticker}...")
                    # 最新モデルのGemini 3 Flashで解析
                    ai_comment = analyze_with_gemini_v3(ticker, result, adjustments)
                    result["ai_comment"] = ai_comment
                
                # 期間情報などを付与
                result["date"] = str(filing.period_end_date)
                result["form"] = filing.form
                
                save_result(ticker, filing.accession_no, result)
                results_history.append(result)
            except Exception as e:
                print(f"Skipping filing {filing.accession_no} due to error: {e}")

        if results_history:
            # 最新版
            with open(f"data/{ticker}/latest.json", "w") as f:
                json.dump(results_history[0], f, indent=2)
            
            # 10年分の推移用（グラフ描画に使用可能）
            with open(f"data/{ticker}/history.json", "w") as f:
                json.dump(results_history, f, indent=2)

if __name__ == "__main__":
    run()
