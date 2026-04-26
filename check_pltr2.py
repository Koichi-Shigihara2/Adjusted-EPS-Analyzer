import json
with open("docs/value-monitor/tanuki_valuation/data/PLTR/latest.json", encoding="utf-8") as f:
    d = json.load(f)
cf = d.get("components", {})
print("fcf_list:", d.get("fcf_list"))
print("fcf_5yr_avg:", d.get("fcf_5yr_avg"))
print("fcf_2yr_avg:", d.get("fcf_2yr_avg"))
print("fiscal_year_latest:", d.get("fiscal_year_latest"))
