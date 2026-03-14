import yaml, json, os
from edgar_fetcher import fetch_filings
from xbrl_parser import parse_xbrl
from adjustment_detector import detect_adjustments
from tax_adjuster import apply_tax
from eps_calculator import calculate_eps

def save_result(ticker, accession_no, result):
    os.makedirs(f"data/{ticker}", exist_ok=True)
    # 個別の決算データ保存
    with open(f"data/{ticker}/{accession_no}.json", "w") as f:
        json.dump(result, f, indent=2)

def run():
    with open("config/monitor_tickers.yaml") as f:
        tickers = yaml.safe_load(f)["tickers"]

    for ticker in tickers:
        print(f"Processing {ticker}...")
        filings = fetch_filings(ticker)
        
        results_history = []
        for filing in filings:
            try:
                data = parse_xbrl(filing)
                if not data: continue
                
                adjustments = detect_adjustments(data)
                net_adjustments = apply_tax(adjustments, data)
                result = calculate_eps(data, net_adjustments)
                
                # 期間情報などを付与
                result["date"] = str(filing.period_end_date)
                result["form"] = filing.form
                
                save_result(ticker, filing.accession_no, result)
                results_history.append(result)
            except Exception as e:
                print(f"Skipping filing {filing.accession_no} due to error: {e}")

        # 最後に最新版をlatest.jsonとして保存（サイト表示用）
        if results_history:
            with open(f"data/{ticker}/latest.json", "w") as f:
                json.dump(results_history[0], f, indent=2)
            
            # 10年分の推移用まとめファイル（後で一覧画面で使用）
            with open(f"data/{ticker}/history.json", "w") as f:
                json.dump(results_history, f, indent=2)

if __name__ == "__main__":
    run()
