"""
ショートレポート逆張りバックテスト v4
インパクトスコア付き：「このレポートで株価は永続的に下落するか一時的か」を判定

インパクトスコア（0〜100）：低いほど逆張り好機
  - 空売り残比率（低い＝市場が信じていない＝インパクト小）
  - 機関投資家保有比率（高い＝支持厚い＝インパクト小）
  - アナリスト推奨（Buy多い＝インパクト小）
  - アナリスト数（多い＝カバレッジ厚い＝インパクト小）
  - レポートタイプ（valuation＝インパクト小）
  - レポート前の財務実績（売上成長・EPS beat＝インパクト小）
"""
import yfinance as yf
import pandas as pd
import numpy as np
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
HOLD_DAYS = [7, 30, 60]

def get_vix(date_str):
    try:
        rd = datetime.strptime(date_str, "%Y-%m-%d")
        v = yf.download("^VIX", start=(rd-timedelta(5)).strftime("%Y-%m-%d"),
                        end=(rd+timedelta(3)).strftime("%Y-%m-%d"),
                        progress=False, auto_adjust=True)
        return round(float(v['Close'].iloc[-1]), 2) if len(v) > 0 else None
    except: return None

def get_impact_data(ticker):
    """
    インパクト判定に使う基礎データを取得
    ※ レポート時点のデータが理想だが、yfinanceは現在値のみ提供
      →「レポート当時の近似値」として使用（限界あり・注記）
    """
    res = {}
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # 空売り残比率（Float の何%が空売りされているか）
        res['short_pct_float'] = info.get('shortPercentOfFloat')
        if res['short_pct_float']:
            res['short_pct_float'] = round(res['short_pct_float'] * 100, 1)

        # 機関投資家保有比率
        res['inst_own_pct'] = info.get('heldPercentInstitutions')
        if res['inst_own_pct']:
            res['inst_own_pct'] = round(res['inst_own_pct'] * 100, 1)

        # アナリスト数・推奨
        res['analyst_count']    = info.get('numberOfAnalystOpinions')
        res['rec_mean']         = info.get('recommendationMean')  # 1=Strong Buy 5=Strong Sell
        res['rec_key']          = info.get('recommendationKey')   # buy/hold/sell

        # 財務指標
        res['revenue_growth']   = info.get('revenueGrowth')
        if res['revenue_growth']:
            res['revenue_growth'] = round(res['revenue_growth'] * 100, 1)
        res['earnings_growth']  = info.get('earningsGrowth')
        if res['earnings_growth']:
            res['earnings_growth'] = round(res['earnings_growth'] * 100, 1)
        res['roe']              = info.get('returnOnEquity')
        if res['roe']:
            res['roe'] = round(res['roe'] * 100, 1)
        res['debt_to_equity']   = info.get('debtToEquity')
        res['beta']             = info.get('beta')

        # アナリスト目標株価 vs 現在株価（上昇余地）
        target = info.get('targetMeanPrice')
        current = info.get('currentPrice')
        if target and current and current > 0:
            res['analyst_upside_pct'] = round((target - current) / current * 100, 1)
        else:
            res['analyst_upside_pct'] = None

    except Exception as e:
        print(f"    infoエラー {ticker}: {e}")

    return res

def calc_impact_score(r, impact_data):
    """
    インパクトスコアを計算（0〜100、低いほど逆張り好機）
    各要素は逆張り安全性への寄与度で重み付け
    """
    score = 50  # ベーススコア

    # ① レポートタイプ（最重要・±20点）
    if r['report_type'] == 'valuation':
        score -= 20  # 過大評価系＝インパクト小
    else:
        score += 20  # 詐欺・不正系＝インパクト大

    # ② 空売り残比率（±15点）
    si = impact_data.get('short_pct_float')
    if si is not None:
        if si < 3:    score -= 15  # 空売り少ない＝市場が信じていない
        elif si < 8:  score -= 5
        elif si < 15: score += 5
        else:         score += 15  # 空売り多い＝市場も疑っている

    # ③ 機関投資家保有比率（±10点）
    inst = impact_data.get('inst_own_pct')
    if inst is not None:
        if inst > 80:   score -= 10  # 機関が厚く支持
        elif inst > 60: score -= 5
        elif inst > 40: score += 0
        elif inst > 20: score += 5
        else:           score += 10  # 機関がほとんどいない

    # ④ アナリスト推奨（±10点）
    rec = impact_data.get('rec_mean')
    if rec is not None:
        if rec <= 2.0:   score -= 10  # Strong Buy寄り
        elif rec <= 2.5: score -= 5
        elif rec <= 3.0: score += 0
        elif rec <= 3.5: score += 5
        else:            score += 10  # Sell寄り

    # ⑤ アナリスト数（±5点）
    n_analyst = impact_data.get('analyst_count')
    if n_analyst is not None:
        if n_analyst >= 20:  score -= 5   # カバレッジ厚い
        elif n_analyst >= 10: score -= 2
        elif n_analyst < 5:  score += 5   # カバレッジ薄い

    # ⑥ 売上成長率（±5点）
    rev_g = impact_data.get('revenue_growth')
    if rev_g is not None:
        if rev_g > 30:   score -= 5  # 高成長＝実態が強い
        elif rev_g > 10: score -= 2
        elif rev_g < 0:  score += 5  # 減収＝弱い

    # ⑦ 相場環境（±5点）
    if r['market_env'] == 'bull':    score -= 5
    elif r['market_env'] == 'bear':  score += 5

    return max(0, min(100, score))

def backtest_one(r):
    try:
        rd    = datetime.strptime(r['date'], "%Y-%m-%d")
        start = (rd - timedelta(280)).strftime("%Y-%m-%d")
        end   = (rd + timedelta(100)).strftime("%Y-%m-%d")

        df = yf.download(r['ticker'], start=start, end=end, progress=False, auto_adjust=True)
        if len(df) < 20: return None

        cl = df['Close']
        hi = df['High']
        cl.index = pd.to_datetime(cl.index)
        hi.index = pd.to_datetime(hi.index)

        before    = cl[cl.index < rd]
        hi_before = hi[hi.index < rd]
        after     = cl[cl.index >= rd]
        if len(after) < 2 or len(before) < 20: return None

        p0 = float(after.iloc[0])
        p1 = float(after.iloc[1])
        ed = after.index[1]

        hi20 = float(hi_before.iloc[-20:].max()) if len(hi_before) >= 20 else None
        hi52 = float(hi_before.max())            if len(hi_before) >= 50 else None
        pre20_price = float(before.iloc[-20])    if len(before) >= 20 else None

        drop_20d   = (p1 - hi20)        / hi20        * 100 if hi20        else None
        drop_52w   = (p1 - hi52)        / hi52        * 100 if hi52        else None
        pre20d_ret = (p1 - pre20_price) / pre20_price * 100 if pre20_price else None
        day1_drop  = (p1 - p0)          / p0          * 100

        # インパクトデータ取得
        impact_data  = get_impact_data(r['ticker'])
        impact_score = calc_impact_score(r, impact_data)

        res = {**r,
               'day0_price':          round(p0, 2),
               'entry_price':         round(p1, 2),
               'day1_drop_pct':       round(day1_drop, 2),
               'drop_from_20d_high':  round(drop_20d, 2) if drop_20d  else None,
               'drop_from_52w_high':  round(drop_52w, 2) if drop_52w  else None,
               'pre20d_return':       round(pre20d_ret, 2) if pre20d_ret else None,
               'vix':                 get_vix(r['date']),
               'impact_score':        impact_score,
               **{k: impact_data.get(k) for k in [
                   'short_pct_float','inst_own_pct','analyst_count',
                   'rec_mean','rec_key','revenue_growth','earnings_growth',
                   'beta','analyst_upside_pct'
               ]}}

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

def show(sub, label, rc='ret_60d', wc='win_60d'):
    s = sub[sub[rc].notna()]
    if len(s) == 0: return
    print(f"  {label:<40} n={len(s):2d}  勝率={s[wc].mean()*100:.0f}%  "
          f"平均={s[rc].mean():+.1f}%  中央値={s[rc].median():+.1f}%  "
          f"最良={s[rc].max():+.1f}%  最悪={s[rc].min():+.1f}%")

def main():
    print("="*75)
    print(f"ショートレポート逆張りバックテスト v4  対象:{len(REPORTS)}件")
    print("インパクトスコア付き（低いほど逆張り好機）")
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

    print("\n【A】全体集計（60日後）")
    for d in HOLD_DAYS: show(df, f"{d}日後", f'ret_{d}d', f'win_{d}d')

    print("\n【B】インパクトスコア別（60日後）← 核心分析")
    print("  スコア低=逆張り好機、スコア高=危険")
    for lbl, sub in [
        ("スコア<40（低インパクト・逆張り好機）",  df[df.impact_score < 40]),
        ("スコア40-59（中程度）",                  df[(df.impact_score >= 40) & (df.impact_score < 60)]),
        ("スコア60-74（高インパクト）",             df[(df.impact_score >= 60) & (df.impact_score < 75)]),
        ("スコア≥75（非常に高インパクト・危険）",   df[df.impact_score >= 75]),
    ]: show(sub, lbl)

    print("\n【C】インパクトスコア×相場環境（60日後）")
    for env, el in [("bull","強気"), ("neutral","中立"), ("bear","弱気")]:
        for thr, tl in [(40,"スコア<40"), (60,"スコア<60")]:
            sub = df[(df.market_env == env) & (df.impact_score < thr)]
            if len(sub) >= 2: show(sub, f"[{el}×{tl}]")

    print("\n【D】空売り残比率別（60日後）← 市場がどれだけ信じているか")
    df_si = df[df.short_pct_float.notna()]
    for lbl, sub in [
        ("空売り残<3%（市場が信じていない）",  df_si[df_si.short_pct_float < 3]),
        ("空売り残3-8%（中程度）",             df_si[(df_si.short_pct_float >= 3) & (df_si.short_pct_float < 8)]),
        ("空売り残8-15%（高め）",              df_si[(df_si.short_pct_float >= 8) & (df_si.short_pct_float < 15)]),
        ("空売り残≥15%（非常に高い）",         df_si[df_si.short_pct_float >= 15]),
    ]: show(sub, lbl)

    print("\n【E】アナリスト推奨別（60日後）")
    df_rec = df[df.rec_mean.notna()]
    for lbl, sub in [
        ("推奨mean≤2.0（Strong Buy寄り）", df_rec[df_rec.rec_mean <= 2.0]),
        ("推奨mean2.0-2.5（Buy寄り）",     df_rec[(df_rec.rec_mean > 2.0) & (df_rec.rec_mean <= 2.5)]),
        ("推奨mean2.5-3.0（中立寄り）",    df_rec[(df_rec.rec_mean > 2.5) & (df_rec.rec_mean <= 3.0)]),
        ("推奨mean>3.0（Sell寄り）",       df_rec[df_rec.rec_mean > 3.0]),
    ]: show(sub, lbl)

    print("\n【F】機関投資家保有比率別（60日後）")
    df_inst = df[df.inst_own_pct.notna()]
    for lbl, sub in [
        ("機関保有>80%（強いサポート）",    df_inst[df_inst.inst_own_pct > 80]),
        ("機関保有60-80%",                  df_inst[(df_inst.inst_own_pct > 60) & (df_inst.inst_own_pct <= 80)]),
        ("機関保有<60%（サポート薄い）",    df_inst[df_inst.inst_own_pct <= 60]),
    ]: show(sub, lbl)

    print("\n【G】インパクトスコア×drop_from_20d_high（60日後）← 実用複合フィルター")
    for score_thr, sl in [(40,"スコア<40"), (60,"スコア<60")]:
        for drop_thr, dl in [(-10,"20d高値-10%超"), (-20,"20d高値-20%超")]:
            sub = df[(df.impact_score < score_thr) & (df.drop_from_20d_high <= drop_thr)]
            if len(sub) >= 2: show(sub, f"[{sl}×{dl}]")

    print("\n【H】個別案件（インパクトスコア順）60日後リターン付き")
    cols = ['ticker','short_seller','report_type','market_env','impact_score',
            'short_pct_float','inst_own_pct','analyst_count','rec_mean',
            'drop_from_20d_high','ret_30d','ret_60d','note']
    pd.set_option('display.width', 180)
    pd.set_option('display.max_columns', None)
    print(df[cols].sort_values('impact_score').to_string(index=False))

    print("\n【I】相関分析（インパクトスコアと60日後リターン）")
    corr_cols = ['impact_score','short_pct_float','inst_own_pct',
                 'analyst_count','rec_mean','revenue_growth','drop_from_20d_high',
                 'pre20d_return','ret_60d']
    corr = df[corr_cols].corr()['ret_60d'].drop('ret_60d')
    print("  60日後リターンとの相関係数：")
    for col, val in corr.sort_values().items():
        bar = "█" * int(abs(val) * 20)
        direction = "←負" if val < 0 else "正→"
        print(f"    {col:<25}: {val:+.3f}  {direction} {bar}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'short_report_backtest_v4_result.csv')
    df.to_csv(out, index=False, encoding='utf-8-sig')
    print(f"\n✓ CSV: {out}")
    print("\n⚠ 注意：インパクト指標（空売り残・機関保有・アナリスト推奨）は")
    print("  yfinanceの現在値を使用。レポート当時の値ではありません。")
    print("  相関分析の参考値として使ってください。")

if __name__ == '__main__': main()
