# SEC財務データ取得デバッグ標準

## 作成背景

2026-05-17のGrossProfit取得デバッグセッションにおいて、以下の問題が発生した：

- **SECに明確に申告されているGrossProfit**が取得できていないにもかかわらず、複数回にわたり「申告スタイルの問題」「構造的限界」として打ち切りを提案した
- 他フィールド（OCF・RD・NetIncome等）は同期間で正常取得できているにもかかわらず、論理矛盾を見逃した
- Q4 impliedの実装知見（ttm_calculator.py）が既に存在していたにもかかわらず活用されなかった
- 根本原因特定まで多大なトークンと時間を要した

本ドキュメントはその再発防止のための開発標準である。

---

## 1. データ取得の5層構造

SECデータ取得は以下の5層で構成される。問題発生時は**必ず上位層から順に**確認する。

```
Layer 1: SEC EDGAR (company_facts.json)
    ↓ quarterly.py / _get_field_units()
Layer 2: Raw entries (per tag, USD単位)
    ↓ quarterly.py / _process_entries()
Layer 3: Processed entries (YTD変換・accn重複排除・期間フィルタ)
    ↓ quarterly.py / build_raw_table()
Layer 4: Raw table ({ticker}_quarterly_raw.json)
    ↓ normalizer.py / normalize()
Layer 5: Normalized ({ticker}_quarterly_normalized.json)
    ↓ financial_trend_calculator.py
Layer 6: series_q in results.json
```

**鉄則: 上位層で存在するデータが下位層で消えている場合、必ずその境界で何が起きているかを確認する。「申告されていない」と結論づける前に全層を確認すること。**

---

## 2. データ欠落調査の標準手順

### Step 0: 前提確認（最初に必ず実施）

```python
# 比較基準を明確にする
# 「他フィールドは取得できているか？」を確認
# 同期間に他フィールドが取得できているなら、データ欠落は構造的問題ではなくコード問題

for fname in ["Revenue", "GrossProfit", "OCF", "RD", "NetIncome"]:
    entries = normalized["fields"].get(fname, [])
    q = [e for e in entries if not e.get("is_annual")]
    print(fname, len(q), [e["end"] for e in q][-3:])
```

**論理チェック:** 同期間に他フィールドが取れているのにGrossProfitだけ取れない → コード問題

### Step 1: Layer 1確認（SEC生データ）

```python
# 対象フィールドに関連する全XBRLタグを網羅的に検索
gaap = company_facts["facts"]["us-gaap"]
for tag in sorted(gaap.keys()):
    if "gross" in tag.lower() or "profit" in tag.lower() or "cost" in tag.lower():
        entries = gaap[tag].get("units", {}).get("USD", [])
        q = [e for e in entries if e.get("fp","").startswith("Q") and e["end"] >= "2023-01-01"]
        if q:
            print(tag, len(q), q[-1])
```

**チェックポイント:** タグが存在するか？存在するなら何件か？

### Step 2: Layer 2確認（_get_field_units後）

```python
from common.sec_data.quarterly import _get_field_units, _process_entries
entries = _get_field_units(gaap, "TARGET_TAG", "USD")
print("raw:", len(entries))
for e in sorted(entries, key=lambda x: x.get("end",""))[-6:]:
    print(e["end"], e.get("fp"), e.get("val"), e.get("accn","")[:20])
```

### Step 3: Layer 3確認（_process_entries後）

```python
processed = _process_entries(entries)
for e in sorted(processed, key=lambda x: x["end"])[-6:]:
    print(e["end"], e.get("fp"), e.get("is_ytd"), e.get("is_annual"), e["val"])
```

**チェックポイント:** accn重複排除でエントリが消えていないか？YTD変換が正しいか？

### Step 4: Layer 4確認（build_raw_table後）

```python
from common.sec_data.quarterly import build_raw_table
raw = build_raw_table(ticker, company_facts)
field = raw["fields"].get("TARGET_FIELD", [])
print("raw table:", len(field))
```

### Step 5: Layer 5確認（normalize後）

```python
from common.sec_data.normalizer import normalize
result = normalize(ticker, raw)
field = result["fields"].get("TARGET_FIELD", [])
q = [e for e in field if not e.get("is_annual")]
print("normalized:", len(q))
for e in sorted(q, key=lambda x: x["end"])[-6:]:
    print(e["end"], e.get("fp"), e.get("is_implied"), e.get("backfilled"), e["val"])
```

### Step 6: 比較確認

Layer 4で存在 → Layer 5で消えた → normalize()のどの処理で消えたかを特定  
Layer 3で存在 → Layer 4で消えた → build_raw_table()のマージ処理を確認  
Layer 2で存在 → Layer 3で消えた → _process_entries()の重複排除・フィルタを確認  
Layer 1で存在 → Layer 2で消えた → _get_field_units()のタグ名・単位を確認

---

## 3. Q4データ欠落の標準対処

Q4は10-Kにまとめて申告される場合が多く、10-Qとして独立申告されない。

### 判定フロー

```
Q4のstandalone entryが存在しない
    ↓
FY年次データ（is_annual=True）が存在するか？
    YES → Q4 implied = FY - (Q1+Q2+Q3) で逆算可能
    NO  → 構造的限界（許容）
```

### 実装済みの解決策

`common/sec_data/normalizer.py` の `_build_q4_implied_entries()` が全フロー系フィールドに適用済み：

```python
Q4_IMPLIED_FIELDS = (
    "Revenue", "_COGS",
    "OCF", "ICF", "CFF", "CapEx",
    "RD", "SM", "SBC", "DA",
    "NetIncome", "OperatingIncome",
    "GrossProfit",
)
```

**確認方法:**

```python
annual = [e for e in normalized["fields"]["TARGET"], [] if e.get("is_annual")]
print("年次データ:", len(annual))  # 0件 → Q4 implied不可
```

---

## 4. accn重複排除の落とし穴

### 問題

同一accn（同一提出ファイル）内にYTD値とstandalone値の両方が存在する場合、accnで重複排除するとstandaloneが消える。

### 確認方法

```python
# 同一end_dateに複数valが存在するか？
from collections import defaultdict
by_end = defaultdict(list)
for e in entries:
    if e.get("form","") in ("10-Q","10-K"):
        by_end[e["end"]].append(e)
for end, es in by_end.items():
    if len(es) > 1:
        print(end, [(e["val"], e.get("accn","")[:15]) for e in es])
```

### 修正済み対処

Revenue・_COGSは `(end, start, val)` の組み合わせで重複排除（quarterly.py）。

---

## 5. GrossProfit逆算（backfill）の落とし穴

### 問題

`_calc_gross_profit()` でRevenue entryを `next(e for e in rev_entries if e["end"] == end_date)` で取得すると、同一end_dateに年次エントリ（`is_annual=True`, `fp="FY"`）が存在する場合それが先にマッチし、backfilledエントリのfpが"FY"になる。

### 確認方法

```python
# backfilledエントリのfpを確認
gp = [e for e in normalized["fields"]["GrossProfit"] if e.get("backfilled")]
for e in gp:
    print(e["end"], e.get("fp"), e["val"])
# fp="FY"になっていたら問題
```

### 修正済み対処

```python
# annual除外を追加
rev_entry = next(
    (e for e in rev_entries if e["end"] == end_date and not e.get("is_annual")),
    None
)
```

---

## 6. タグ漏れ調査の標準チェックリスト

新しい銘柄をonboardする際、または「データが取れない」と判断する前に以下を実施：

### 6.1 Revenue系

```python
revenue_tags = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
    "TotalRevenue",
    "RevenueFromContractWithCustomerNetOfReturnAndAllowances",
]
```

### 6.2 COGS/GrossProfit系

```python
cogs_tags = [
    "CostOfRevenue",
    "CostOfGoodsAndServicesSold",
    "CostOfGoodsSold",
    "CostOfServices",
    "CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization",
    "CostOfRevenueExcludingDepreciationDepletionAndAmortization",
]
gp_tags = [
    "GrossProfit",
    "GrossProfitLoss",
    "GrossIncome",
]
```

### 6.3 汎用タグ探索

```python
# キーワードで関連タグを全探索
keywords = ["gross", "profit", "cost", "revenue"]
for tag in sorted(gaap.keys()):
    if any(k in tag.lower() for k in keywords):
        entries = gaap.get(tag, {}).get("units", {}).get("USD", [])
        q = [e for e in entries if e.get("fp","").startswith("Q")]
        if q:
            print(tag, len(q))
```

---

## 7. 「構造的限界」と判断するための必要条件

以下を**全て**満たした場合のみ「構造的限界（許容）」と判断する：

1. **Layer 1確認済み**: 全関連XBRLタグを検索し、該当データが存在しない
2. **論理一貫性確認済み**: 他フィールドが同期間で取れているなら、それと整合する説明ができる
3. **Q4 implied確認済み**: 年次データからの逆算を試みた
4. **accn重複確認済み**: 同一accn内に複数値が存在しないか確認した
5. **10-Q/10-K原文確認済み**: 実際の開示書類にその項目が存在するか確認した（または確認できない旨を明記）

**上記を確認せずに「構造的限界」と判断・提案することは禁止する。**

---

## 8. 網羅性チェックスクリプト

```python
# check_all_fields.py の標準版
# 新銘柄追加時・修正後に必ず実行

import json, pathlib

FIELDS = ["Revenue","GrossProfit","OCF","RD","SM","CapEx","NetIncome","Cash","SBC"]
TICKERS = [...]  # cik_lookup.csvから取得

for ticker in TICKERS:
    path = pathlib.Path(f"common/sec_data/normalized/{ticker}_quarterly_normalized.json")
    if not path.exists():
        continue
    d = json.load(open(path))
    row = [ticker.ljust(6)]
    for fname in FIELDS:
        q = [e for e in d["fields"].get(fname, [])
             if not e.get("is_annual") and not e.get("is_ytd")]
        row.append(str(len(q)).ljust(10))
    print("  ".join(row))
```

---

## 9. 既知の構造的限界（許容済み）

| 銘柄 | フィールド | 理由 |
|------|-----------|------|
| IONQ | GrossProfit | 研究段階企業・損益計算書にGP行なし |
| JOBY | GrossProfit | 研究段階企業・損益計算書にGP行なし |
| OSCR | GrossProfit | 保険会社・業種別FCF定義で対応済み |
| AVAV | NetIncome | 非暦年決算・申告タグ未確認 |
| RLMD | Revenue | 上場直後・データ蓄積不足 |

---

## 10. 教訓サマリー

1. **「他フィールドが取れているのにXだけ取れない」は必ずコード問題**
2. **SEC申告書に記載がある項目は必ず取得できるはず**（XBRLタグの問題か実装の問題かのいずれか）
3. **Q4データは10-K年次からの逆算で補完できる**（実装済み）
4. **accn重複排除は(end,start,val)方式を使う**（accnだけでは不十分）
5. **next()で複数候補から1件取得する際は必ずis_annual等でフィルタする**
6. **過去の実装知見（ttm_calculator.py等）を先に確認する**

---

*最終更新: 2026-05-17*  
*作成経緯: GrossProfit Q4欠落デバッグセッション（約2時間・多大なトークン消費）*
