import json
with open('common/sec_data/data/MSFT/company_facts.json', encoding='utf-8') as f:
    d = json.load(f)
rd = d['facts']['us-gaap']['ResearchAndDevelopmentExpense']
units = rd.get('units', {}).get('USD', [])
annual = [x for x in units if x.get('form') == '10-K']
for x in sorted(annual, key=lambda x: x.get('end',''))[-5:]:
    print(x.get('end'), f"${x.get('val'):,.0f}")
