"""
四半期データパイプライン動作確認スクリプト（NVDA）

実行方法:
    cd ~/Documents/On-a-journey-git
    python test_quarterly_pipeline.py
"""

import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# リポジトリルートをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from common.sec_data.fetcher import load_company_facts, needs_quarterly_update, _get_latest_accn
from common.sec_data.quarterly import build_raw_table, save_raw_table
from common.sec_data.normalizer import normalize, save_normalized
from common.sec_data.ttm_calculator import calc_ttm, save_ttm
from common.sec_data.quality_checker import run_checks

ticker = "NVDA"

print(f"\n{'='*60}")
print(f"四半期パイプライン テスト: {ticker}")
print(f"{'='*60}")

# 1. company_facts.json ロード
print("\n[1] company_facts ロード...")
cf = load_company_facts(ticker)
if cf is None:
    print(f"ERROR: {ticker}/company_facts.json が見つかりません")
    print("  先に SECFetcher.fetch_company_facts() を実行してください")
    sys.exit(1)
print(f"  OK: entityName={cf.get('entityName', 'N/A')}")

# 2. Raw Table 生成
print("\n[2] Raw Table 生成...")
raw = build_raw_table(ticker, cf)
ocf_entries = raw["fields"].get("OCF", [])
rev_entries = raw["fields"].get("Revenue", [])
print(f"  OCF エントリ数: {len(ocf_entries)}")
print(f"  Revenue エントリ数: {len(rev_entries)}")
if ocf_entries:
    latest_ocf = max(ocf_entries, key=lambda x: x["end"])
    print(f"  最新OCF: end={latest_ocf['end']} val={latest_ocf['val']:,.0f} is_ytd={latest_ocf['is_ytd']}")
save_raw_table(ticker, raw)
print(f"  保存完了")

# 3. 正規化
print("\n[3] YTD→SA 正規化...")
norm = normalize(ticker, raw)
ocf_norm = norm["fields"].get("OCF", [])
q_entries = [e for e in ocf_norm if not e.get("is_annual")]
print(f"  OCF 四半期エントリ数（正規化後）: {len(q_entries)}")
if q_entries:
    recent = sorted(q_entries, key=lambda x: x["end"], reverse=True)[:4]
    print("  直近4Qの OCF（SA）:")
    for e in recent:
        ytd_flag = " [YTD残]" if e.get("is_ytd") else ""
        anomaly = " [ANOMALY]" if e.get("anomaly") else ""
        print(f"    end={e['end']} fp={e.get('fp','?')} val={e['val']/1e9:.2f}B{ytd_flag}{anomaly}")
save_normalized(ticker, norm)
print(f"  保存完了")

# 4. TTM 計算
print("\n[4] TTM 計算...")
ttm = calc_ttm(ticker, norm)
ocf_ttm = ttm["flow"].get("OCF")
rev_ttm = ttm["flow"].get("Revenue")
ni_ttm = ttm["flow"].get("NetIncome")
cash_stock = ttm["stock"].get("Cash")

print(f"  TTM end: {ttm['ttm_end']}")
if ocf_ttm:
    print(f"  TTM OCF:     {ocf_ttm['val']/1e9:.1f}B  (Q数={ocf_ttm['quarters_used']}, 欠損={ocf_ttm['missing']})")
if rev_ttm:
    print(f"  TTM Revenue: {rev_ttm['val']/1e9:.1f}B")
if ni_ttm:
    print(f"  TTM NI:      {ni_ttm['val']/1e9:.1f}B")
if cash_stock:
    print(f"  Cash:        {cash_stock['val']/1e9:.1f}B (as_of={cash_stock['as_of']})")
if ttm.get("burn_rate"):
    print(f"  Burn Rate:   {ttm['burn_rate']}")
if ttm.get("q4_implied"):
    q4_ocf = ttm["q4_implied"].get("OCF")
    if q4_ocf:
        print(f"  Q4 implied OCF: {q4_ocf['val']/1e9:.2f}B (FY{q4_ocf['fy']})")
save_ttm(ticker, ttm)
print(f"  保存完了")

# 5. Quality Check
print("\n[5] Quality Check...")
qc = run_checks(ticker, norm, raw)
print(f"  結果: {qc['passed']}/{qc['passed']+qc['failed']} PASS")
for check_id, result in qc["results"].items():
    status = result["status"]
    mark = "OK" if status == "PASS" else "NG"
    print(f"  [{mark}] {check_id}: {result['detail']}")

print(f"\n{'='*60}")
print(f"完了")

# 期待値チェック
ocf_val = ttm["flow"].get("OCF", {}).get("val", 0)
passed = qc["passed"]
total = qc["passed"] + qc["failed"]

print(f"\n期待値チェック:")
ocf_ok = 27e9 <= ocf_val <= 120e9  # 広めに設定（FY状況による）
qc_ok = passed >= 10
print(f"  TTM OCF: {ocf_val/1e9:.1f}B  {'OK' if ocf_ok else 'NG (期待: 27-120B)'}")
print(f"  QC:      {passed}/{total} PASS  {'OK' if qc_ok else 'NG (期待: 10+/13)'}")
