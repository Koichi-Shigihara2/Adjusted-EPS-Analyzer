"""
ショートレポート逆張りバックテスト v3
v3変更点：急落の総量指標を追加
  - drop_from_5d_high  : 直近5日高値からの下落率
  - drop_from_20d_high : 直近20日高値からの下落率
  - drop_from_52w_high : 52週高値からの下落率
  - pre5d_return       : レポート5日前からの累積変化率
  - pre20d_return      : レポート20日前からの累積変化率
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
        # 52週前からデータ取得
        start = (rd - timedelta(days=280)).strftime("%Y-%m-%d")
        end   = (rd + timedelta(days=100)).strftime("%Y-%m-%d")
        df = yf.download(r['ticker'], start=start, end=end, progress=False, auto_adjust=True)
        if len(df) < 20: return None

        cl = df['Close']
        hi = df['High']
        cl.index = pd.to_datetime(cl.index)
        hi.index = pd.to_datetime(hi.index)

        # レポート日以前のデータ
        before = cl[cl.index < rd]
        hi_before = hi[hi.index < rd]
        after  = cl[cl.index >= rd]
        if len(after) < 2 or len(before) < 20: return None

        p0 = float(after.iloc[0])   # レポート日終値
        p1 = float(after.iloc[1])   # 翌日終値＝エントリー
        ed = after.index[1]
        day1_drop = (p1 - p0) / p0 * 100

        # --- 急落総量指標（v3追加） ---
        # 直近5日・20日の高値からの下落率（エントリー価格基準）
        hi5  = float(hi_before.iloc[-5:].max())  if len(hi_before) >= 5  else None
        hi20 = float(hi_before.iloc[-20:].max()) if len(hi_before) >= 20 else None
        hi52 = float(hi_before.max())            if len(hi_before) >= 50 else None

        drop_5d  = (p1 - hi5)  / hi5  * 100 if hi5  else None
        drop_20d = (p1 - hi20) / hi20 * 100 if hi20 else None
        drop_52w = (p1 - hi52) / hi52 * 100 if hi52 else None

        # レポート5日前・20日前からの株価変化率
        pre5_price  = float(before.iloc[-5])  if len(before) >= 5  else None
        pre20_price = float(before.iloc[-20]) if len(before) >= 20 else None
        pre5d_ret   = (p1 - pre5_price)  / pre5_price  * 100 if pre5_price  else None
        pre20d_ret  = (p1 - pre20_price) / pre20_price * 100 if pre20_price else None

        res = {**r,
               'day0_price':    round(p0, 2),
               'entry_price':   round(p1, 2),
               'day1_drop_pct': round(day1_drop, 2),
               'drop_from_5d_high':  round(drop_5d,  2) if drop_5d  is not None else None,
               'drop_from_20d_high': round(drop_20d, 2) if drop_20d is not None else None,
               'drop_from_52w_high': round(drop_52w, 2) if drop_52w is not None else None,
               'pre5d_return':       round(pre5d_ret,  2) if pre5d_ret  is not None else None,
               'pre20d_return':      round(pre20d_ret, 2) if pre20d_ret is not None else None,
               'vix': get_vix(r['date'])}

        for d in HOLD_DAYS:
            fut = cl[cl.index >= ed + timedelta(d)]
            if len(fut) > 0:
                ret = (float(fut.iloc[0]) - p1) / p1 * 100
                res[f'ret_{d}d'] = round(ret, 2)
                res[f'win_{d}d'] = 1 if ret > 0 else 0
            else:
                res[f'ret_{d}d'] = res[f'win_{d}d'] = None
        return res

    except Exception as e:
        print(f"  ERR {r['ticker']}: {e}"); return None

def show(df_sub, label, rc='ret_60d', wc='win_60d'):
    s = df_sub[df_sub[rc].notna()]
    if len(s) == 0: return
    print(f"  {label:<35} n={len(s):2d}  勝率={s[wc].mean()*100:.0f}%  "
          f"平均={s[rc].mean():+.1f}%  中央値={s[rc].median():+.1f}%  "
          f"最良={s[rc].max():+.1f}%  最悪={s[rc].min():+.1f}%")

def main():
    print("="*75)
    print(f"ショートレポート逆張りバックテスト v3  対象:{len(REPORTS)}件")
    print("="*75)
    results = []
    for i, r in enumerate(REPORTS):
        print(f"[{i+1:02d}/{len(REPORTS)}] {r['ticker']:<14} ({r['date']})  {r['note']}")
        res = backtest_one(r)
        if res: results.append(res)
        else:   print("       → 取得失敗")

    df = pd.DataFrame(results)
    if df.empty: return
    print(f"\n取得成功: {len(df)}/{len(REPORTS)}件")

    # メインは60日後で分析（v2の知見）
    print("\n【A】全体集計（60日後基準）")
    for d in HOLD_DAYS: show(df, f"{d}日後", f'ret_{d}d', f'win_{d}d')

    print("\n【B】4象限分析（60日後）")
    for env,el in [("bull","強気"),("neutral","中立"),("bear","弱気")]:
        for rt,rl in [("valuation","過大評価系"),("fraud","詐欺・不正系")]:
            show(df[(df.market_env==env)&(df.report_type==rt)], f"[{el}×{rl}]")

    print("\n【C】急落総量フィルター別（60日後）← v3追加分析")
    print("  基準：drop_from_20d_high（直近20日高値からの下落率）")
    for lbl, sub in [
        ("全件",                          df),
        ("20日高値から-10%以上下落",      df[df.drop_from_20d_high <= -10]),
        ("20日高値から-20%以上下落",      df[df.drop_from_20d_high <= -20]),
        ("20日高値から-30%以上下落",      df[df.drop_from_20d_high <= -30]),
        ("20日高値から-5%未満（軽微）",   df[df.drop_from_20d_high > -5]),
    ]: show(sub, lbl)

    print("\n【D】52週高値からの下落率別（60日後）← v3追加分析")
    for lbl, sub in [
        ("全件",                          df),
        ("52週高値から-20%以上下落",      df[df.drop_from_52w_high <= -20]),
        ("52週高値から-40%以上下落",      df[df.drop_from_52w_high <= -40]),
        ("52週高値から-60%以上下落",      df[df.drop_from_52w_high <= -60]),
        ("52週高値から-10%未満（高値圏）",df[df.drop_from_52w_high > -10]),
    ]: show(sub, lbl)

    print("\n【E】レポート前20日間の騰落別（60日後）← 過熱感の測定")
    print("  基準：pre20d_return（20日前比変化率）")
    for lbl, sub in [
        ("全件",                       df),
        ("20日前比+30%以上上昇",       df[df.pre20d_return >= 30]),
        ("20日前比+10〜30%上昇",       df[(df.pre20d_return >= 10) & (df.pre20d_return < 30)]),
        ("20日前比±10%以内（横ばい）", df[df.pre20d_return.abs() < 10]),
        ("20日前比マイナス（下落中）",  df[df.pre20d_return < 0]),
    ]: show(sub, lbl)

    print("\n【F】急落総量×相場環境（60日後）← 実用フィルター設計")
    for env,el in [("bull","強気"),("neutral","中立"),("bear","弱気")]:
        for thr,tl in [(-10,"20日高値-10%超"),(-20,"20日高値-20%超"),(-30,"20日高値-30%超")]:
            sub = df[(df.market_env==env)&(df.drop_from_20d_high<=thr)]
            if len(sub) >= 2: show(sub, f"[{el}×{tl}]")

    print("\n【G】個別案件（60日後順）急落指標付き")
    cols = ['ticker','short_seller','report_type','market_env',
            'day1_drop_pct','drop_from_20d_high','drop_from_52w_high',
            'pre20d_return','ret_30d','ret_60d','vix','note']
    pd.set_option('display.width', 160)
    print(df[cols].sort_values('ret_60d', ascending=False).to_string(index=False))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'short_report_backtest_v3_result.csv')
    df.to_csv(out, index=False, encoding='utf-8-sig')
    print(f"\n✓ CSV: {out}")

if __name__ == '__main__': main()
