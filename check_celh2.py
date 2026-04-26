import json
with open("common/sec_data/data/CELH/annual_2021.json") as f:
    d = json.load(f)
print("FCF:", d.get("cf", {}).get("free_cash_flow"))
print("OCF:", d.get("cf", {}).get("operating_cash_flow"))
print("Capex:", d.get("cf", {}).get("capital_expenditure"))
