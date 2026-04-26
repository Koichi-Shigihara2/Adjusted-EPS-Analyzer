import json, os
data_dir = "common/sec_data/data/PLTR"
for fname in sorted(os.listdir(data_dir)):
    if fname.startswith("annual_"):
        with open(os.path.join(data_dir, fname)) as f:
            d = json.load(f)
        fy = fname.replace("annual_","").replace(".json","")
        cf = d.get("cf", {})
        pl = d.get("pl", {})
        print(f"FY{fy}: FCF={cf.get('free_cash_flow')} OCF={cf.get('operating_cash_flow')} Capex={cf.get('capital_expenditure')} Revenue={pl.get('revenue')} NetIncome={pl.get('net_income')}")
