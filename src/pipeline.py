import yaml, json, os
from edgar_fetcher import fetch_filings
from xbrl_parser import parse_xbrl
from adjustment_detector import detect_adjustments
from tax_adjuster import apply_tax
from eps_calculator import calculate_eps
from ai_analyzer import analyze_with_gemini_v3

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
        for i, filing in enumerate(filings):
            try:
                data = parse_xbrl(filing)
                if not data: continue
                
                adjustments_raw = detect_adjustments(data)
                net_adjustment, detailed_adjustments = apply_tax_adjustments(adjustments_raw, data)
                result = calculate_eps(data, net_adjustment, detailed_adjustments)

                # AI分析（最新四半期のみ）
                if i == 0:
                    ai_result = analyze_adjustments(ticker, result, detailed_adjustments)
                    try:
                        result["ai_analysis"] = json.loads(ai_result)
                    except:
                        result["ai_analysis"] = {"health": "Error", "comment": ai_result}
                
                result["date"] = str(filing.period_end_date)
                result["form"] = filing.form
                
                save_result(ticker, filing.accession_no, result)
                results_history.append(result)
            except Exception as e:
                print(f"Skipping filing {filing.accession_no} due to error: {e}")

        if results_history:
            with open(f"data/{ticker}/latest.json", "w") as f:
                json.dump(results_history[0], f, indent=2)
            
            with open(f"data/{ticker}/history.json", "w") as f:
                json.dump(results_history, f, indent=2)

if __name__ == "__main__":
    run()
