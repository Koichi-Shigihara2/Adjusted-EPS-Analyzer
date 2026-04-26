import json
with open("docs/value-monitor/tanuki_valuation/data/PLTR/latest.json", encoding="utf-8") as f:
    d = json.load(f)
comp = d.get("components", {})
print("fcf_list_raw:", comp.get("fcf_list_raw"))
print("fcf_base_method:", comp.get("fcf_base_method"))
print("fcf_base_used:", comp.get("fcf_base_used"))
