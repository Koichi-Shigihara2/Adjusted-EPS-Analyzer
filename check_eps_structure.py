import json
with open('docs/value-monitor/adjusted_eps_analyzer/data/MSFT/annual.json', encoding='utf-8') as f:
    d = json.load(f)
years = d.get('years', [])
if years:
    first = years[0]
    print('year:', first.get('year'))
    print('all keys:', list(first.keys()))
    print()
    # 調整項目の全item_idを表示
    for adj in first.get('adjustments', []):
        print(f"  item_id: {adj.get('item_id')}, name: {adj.get('item_name')}, extracted_from: {adj.get('extracted_from')}")
