import json
with open("docs/value-monitor/tanuki_valuation/data/CELH/latest.json", encoding="utf-8") as f:
    d = json.load(f)
comp = d.get("components", {})
print("fcf_list_raw:", comp.get("fcf_list_raw"))
print("fcf_2yr_avg:", comp.get("fcf_2yr_avg"))
print("fcf_5yr_avg:", d.get("fcf_5yr_avg") or comp.get("fcf_5yr_avg"))
