import re
with open("src/value/tanuki_valuation/growth.py", encoding="utf-8") as f:
    content = f.read()
idx = content.find("recent_2yr")
print(repr(content[idx-100:idx+300]))
