"""
ショートレポート逆張りバックテスト v2
起点：レポート公開翌日の終値（急落後）
v2変更点：CSVパス修正・急落幅フィルター・ショートセラー別集計追加
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings, os
warnings.filterwarnings('ignore')

REPORTS = [
    {"date":"2020-09-10","ticker":"NKLA",       "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"bull",   "note":"Nikola・詐欺"},
    {"date":"2020-10-08","ticker":"WKHS",       "short_seller":"Hindenburg", "report_type":"valuation","market_env":"bull",   "note":"Workhorse・過大評価"},
    {"date":"2021-02-04","ticker":"CLVS",       "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"bull",   "note":"Clover Health・DOJ隠蔽"},
    {"date":"2021-03-11","ticker":"RIDE",       "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"bull",   "note":"Lordstown・詐欺"},
    {"date":"2021-06-14","ticker":"SI",         "short_seller":"Hindenburg", "report_type":"valuation","market_env":"bull",   "note":"Silvergate・過大評価"},
    {"date":"2021-10-06","ticker":"IRNT",       "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"bull",   "note":"IronNet・詐欺"},
    {"date":"2022-05-02","ticker":"IEP",        "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"bear",   "note":"Icahn Enterprises・詐欺"},
    {"date":"2022-08-08","ticker":"MULN",       "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"bear",   "note":"Mullen Automotive・詐欺"},
    {"date":"2023-01-24","ticker":"ADANIENT.NS","short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"neutral","note":"Adani・会計不正"},
    {"date":"2023-05-02","ticker":"IEP",        "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"neutral","note":"Icahn 第2弾"},
    {"date":"2023-09-07","ticker":"SMCI",       "short_seller":"Hindenburg", "report_type":"fraud",    "market_env":"bull",   "note":"Super Micro・会計不正"},
    {"date":"2024-01-02","ticker":"CVNA",       "short_seller":"Hindenburg", "report_type":"valuation","market_env":"bull",   "note":"Carvana・会計"},
    {"date":"2021-09-13","ticker":"GCMG",       "short_seller":"MuddyWaters","report_type":"fraud",    "market_env":"bull",   "note":"GCM Grosvenor・詐欺"},
    {"date":"2022-06-01","ticker":"RUN",        "short_seller":"MuddyWaters","report_type":"valuation","market_env":"bear",   "note":"Sunrun・過大評価"},
    {"date":"2023-03-27","ticker":"NUVB",       "short_seller":"MuddyWaters","report_type":"fraud",    "market_env":"neutral","note":"Nuvation Bio・詐欺"},
    {"date":"2024-02-13","ticker":"FTAI",       "short_seller":"MuddyWaters","report_type":"fraud",    "market_env":"bull",   "note":"FTAI Aviation・会計不正"},
    {"date":"2024-03-27","ticker":"APP",        "short_seller":"MuddyWaters","report_type":"valuation","market_env":"bull",   "note":"AppLovin・過大評価"},
    {"date":"2025-03-05","ticker":"SOFI",       "short_seller":"MuddyWaters","report_type":"fraud",    "market_env":"neutral","note":"SoFi・会計操作"},
    {"date":"2021-12-06","ticker":"PRTA",       "short_seller":"Kerrisdale", "report_type":"valuation","market_env":"bull",   "note":"Prothena・過大評価"},
    {"date":"2023-08-10","ticker":"IONQ",       "short_seller":"Kerrisdale", "report_type":"valuation","market_env":"bull",   "note":"IonQ・量子過大評価"},
    {"date":"2023-10-17","ticker":"QBTS",       "short_seller":"Kerrisdale", "report_type":"valuation","market_env":"bull",   "note":"D-Wave・量子過大評価"},
    {"date":"2024-04-03","ticker":"OKLO",       "short_seller":"Kerrisdale", "report_type":"valuation","market_env":"bull",   "note":"Oklo・原子力過大評価"},
    {"date":"2022-01-14","ticker":"SGML",       "short_seller":"Grizzly",    "report_type":"fraud",    "market_env":"bear",   "note":"Sigma Lithium・詐欺"},
    {"date":"2022-09-19","ticker":"MASI",       "short_seller":"Grizzly",    "report_type":"fraud",    "market_env":"bear",   "note":"Masimo・ガバナンス"},
    {"date":"2023-05-22","ticker":"TPVG",       "short_seller":"Grizzly",    "report_type":"valuation","market_env":"neutral","note":"TriplePoint・過大評価"},
    {"date":"2024-01-18","ticker":"LAC",        "short_seller":"Bleecker",   "report_type":"valuation","market_env":"bull",   "note":"Lithium Americas・過大評価"},
]
HOLD_DAYS = [3, 7, 14, 30, 60]

def get_vix(date_str):
    try:
        rd = datetime.strptime(date_str, "%Y-%m-%d")
        v = yf.download("^VIX", start=(rd-timedelta(5)).strftime("%Y-%m-%d"),
                        end=(rd+timedelta(3)).strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
        return round(float(v['Close'].iloc[-1]),2) if len(v)>0 else None
    except: return None

def backtest_one(r):
    try:
        rd = datetime.strptime(r['date'], "%Y-%m-%d")
        df = yf.download(r['ticker'], start=(rd-timedelta(10)).strftime("%Y-%m-%d"),
                         end=(rd+timedelta(100)).strftime("%Y-%m-%d"),
                         progress=False, auto_adjust=True)
        if len(df) < 5: return None
        cl = df['Close']
        cl.index = pd.to_datetime(cl.index)
        after = cl[cl.index >= rd]
        if len(after) < 2: return None
        p0 = float(after.iloc[0])
        p1 = float(after.iloc[1])
        ed = after.index[1]
        drop = (p1 - p0) / p0 * 100
        res = {**r, 'day0_price':round(p0,2), 'entry_price':round(p1,2),
               'day1_drop_pct':round(drop,2), 'vix': get_vix(r['date'])}
        for d in HOLD_DAYS:
            fut = cl[cl.index >= ed+timedelta(d)]
            if len(fut)>0:
                ret = (float(fut.iloc[0])-p1)/p1*100
                res[f'ret_{d}d'] = round(ret,2)
                res[f'win_{d}d'] = 1 if ret>0 else 0
            else:
                res[f'ret_{d}d'] = res[f'win_{d}d'] = None
        return res
    except Exception as e:
        print(f"  ERR {r['ticker']}: {e}"); return None

def show(df_sub, label, rc='ret_30d', wc='win_30d'):
    s = df_sub[df_sub[rc].notna()]
    if len(s)==0: return
    print(f"  {label:<30} n={len(s):2d}  勝率={s[wc].mean()*100:.0f}%  "
          f"平均={s[rc].mean():+.1f}%  中央値={s[rc].median():+.1f}%  "
          f"最良={s[rc].max():+.1f}%  最悪={s[rc].min():+.1f}%")

def main():
    print("="*70)
    print(f"ショートレポート逆張りバックテスト v2  対象:{len(REPORTS)}件")
    print("="*70)
    results = []
    for i,r in enumerate(REPORTS):
        print(f"[{i+1:02d}/{len(REPORTS)}] {r['ticker']:<14} ({r['date']})  {r['note']}")
        res = backtest_one(r)
        if res: results.append(res)
        else:   print("       → 取得失敗")

    df = pd.DataFrame(results)
    if df.empty: return
    print(f"\n取得成功: {len(df)}/{len(REPORTS)}件")

    print("\n【A】全体集計")
    for d in HOLD_DAYS: show(df, f"{d}日後", f'ret_{d}d', f'win_{d}d')

    print("\n【B】レポートタイプ別（30日後）")
    show(df[df.report_type=='fraud'],    "詐欺・不正系")
    show(df[df.report_type=='valuation'],"過大評価系")

    print("\n【C】相場環境別（30日後）")
    for env,lbl in [("bull","強気"),("neutral","中立"),("bear","弱気")]:
        show(df[df.market_env==env], lbl)

    print("\n【D】4象限分析 ←核心仮説（30日後）")
    for env,el in [("bull","強気"),("neutral","中立"),("bear","弱気")]:
        for rt,rl in [("valuation","過大評価系"),("fraud","詐欺・不正系")]:
            show(df[(df.market_env==env)&(df.report_type==rt)], f"[{el}×{rl}]")

    print("\n【E】急落幅フィルター別（30日後）←追加分析")
    print("  ※day1_drop_pctがマイナス=翌日もさらに下落してからエントリー")
    for lbl,sub in [
        ("全件",                         df),
        ("翌日-3%以上下落",              df[df.day1_drop_pct<=-3]),
        ("翌日-5%以上下落",              df[df.day1_drop_pct<=-5]),
        ("翌日-10%以上下落",             df[df.day1_drop_pct<=-10]),
        ("翌日プラス（初日に戻した）",    df[df.day1_drop_pct>0]),
    ]: show(sub, lbl)

    print("\n【F】急落幅×相場環境（30日後）←実用フィルター設計用")
    for env,el in [("bull","強気"),("neutral","中立"),("bear","弱気")]:
        for thr,tl in [(-3,"翌日-3%超"),(-5,"翌日-5%超"),(-10,"翌日-10%超")]:
            sub = df[(df.market_env==env)&(df.day1_drop_pct<=thr)]
            if len(sub)>=2: show(sub, f"[{el}×{tl}]")

    print("\n【G】ショートセラー別（30日後）")
    for ss in sorted(df.short_seller.unique()): show(df[df.short_seller==ss], ss)

    print("\n【H】VIX水準別（30日後）")
    dv = df[df.vix.notna()&df.ret_30d.notna()].copy()
    dv['vb'] = pd.cut(dv.vix,[0,20,30,100],labels=["低VIX<20","中VIX20-30","高VIX>30"])
    for b,s in dv.groupby('vb',observed=True): show(s, str(b))

    print("\n【I】個別案件（30日後順）")
    cols=['ticker','short_seller','report_type','market_env','day1_drop_pct','ret_7d','ret_30d','ret_60d','vix','note']
    pd.set_option('display.width',150); pd.set_option('display.max_rows',50)
    print(df[cols].sort_values('ret_30d',ascending=False).to_string(index=False))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'short_report_backtest_result.csv')
    df.to_csv(out, index=False, encoding='utf-8-sig')
    print(f"\n✓ CSV: {out}")

if __name__=='__main__': main()
