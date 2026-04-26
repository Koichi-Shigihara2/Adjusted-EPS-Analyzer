import os

path = os.path.join("src", "value", "tanuki_valuation", "growth.py")
with open(path, encoding="utf-8") as f:
    content = f.read()

idx = content.find("recent_2yr")
print(repr(content[idx-100:idx+300]))