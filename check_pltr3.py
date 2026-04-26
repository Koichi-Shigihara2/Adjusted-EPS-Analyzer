import json
with open("docs/value-monitor/tanuki_valuation/data/PLTR/latest.json", encoding="utf-8") as f:
    d = json.load(f)
print("top keys:", list(d.keys()))
comp = d.get("components", {})
print("components keys:", list(comp.keys())[:20])
print("fcf_5yr_avg:", comp.get("fcf_5yr_avg"))
print("fcf_2yr_avg:", comp.get("fcf_2yr_avg"))
print("fcf_list:", comp.get("fcf_list"))
print("fiscal_year_latest:", comp.get("fiscal_year_latest"))
