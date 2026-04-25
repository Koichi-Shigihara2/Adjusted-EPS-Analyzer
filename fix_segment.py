import re

path = 'common/sec_data/segment_fetcher.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

# primaryDocument フィールドを追加
old2 = "        fys     = filings.get(\"reportDate\", [])\n\n        results = []"
new2 = "        fys      = filings.get(\"reportDate\", [])\n        pri_docs = filings.get(\"primaryDocument\", [])\n\n        results = []"
content = content.replace(old2, new2, 1)

# 結果dictにhtm_fileを追加
old3 = "                results.append({\n                    \"accn\": accns[i],\n                    \"date\": dates[i],\n                    \"fy\":   fy,\n                })"
new3 = "                htm_file = pri_docs[i] if i < len(pri_docs) else \"\"\n                if not (htm_file.endswith(\".htm\") or htm_file.endswith(\".html\")):\n                    htm_file = \"\"\n                results.append({\n                    \"accn\":     accns[i],\n                    \"date\":     dates[i],\n                    \"fy\":       fy,\n                    \"htm_file\": htm_file,\n                })"
content = content.replace(old3, new3, 1)

# htm_url 取得を修正
old4 = "        htm_url = get_10k_htm_url(cik, accn)"
new4 = "        _htm = filing.get(\"htm_file\", \"\")\n        print(f\"   htm_file: {repr(_htm)}\")\n        if _htm:\n            htm_url = f\"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn.replace('-','')}/{_htm}\"\n        else:\n            htm_url = get_10k_htm_url(cik, accn)"
content = content.replace(old4, new4, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done, htm_file count:', content.count('htm_file'))
