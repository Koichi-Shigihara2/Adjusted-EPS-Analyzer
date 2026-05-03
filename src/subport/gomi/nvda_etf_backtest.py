"""
NVDAサプライズ→半導体ETF追随ギャップ戦略 バックテスト
トリガー：NVDA決算EPSサプライズ（上方）
対象：SMH・SOXX
エントリー：決算翌日寄り付き（Open）
保有期間：3・5・7日
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings, os
warnings.filterwarnings('ignore')

# -----------------------------------------------------------------------
# NVDAの決算データ（実績EPS・予想EPS・決算発表日）
# 出所：Macrotrends / Earnings Whispers より手動収集
# surprise_pct = (実績 - 予想) / |予想| × 100
# -----------------------------------------------------------------------
NVDA_EARNINGS = [
    # 2020
    {"date":"2020-02-27","actual_eps":1.89,"est_eps":1.67,"fiscal_q":"FY2020Q4"},
    {"date":"2020-05-21","actual_eps":1.80,"est_eps":1.66,"fiscal_q":"FY2021Q1"},
    {"date":"2020-08-19","actual_eps":2.18,"est_eps":1.97,"fiscal_q":"FY2021Q2"},
    {"date":"2020-11-18","actual_eps":2.91,"est_eps":2.57,"fiscal_q":"FY2021Q3"},
    # 2021
    {"date":"2021-02-24","actual_eps":3.10,"est_eps":2.81,"fiscal_q":"FY2021Q4"},
    {"date":"2021-05-26","actual_eps":3.66,"est_eps":3.28,"fiscal_q":"FY2022Q1"},
    {"date":"2021-08-18","actual_eps":4.04,"est_eps":3.38,"fiscal_q":"FY2022Q2"},
    {"date":"2021-11-17","actual_eps":5.16,"est_eps":4.42,"fiscal_q":"FY2022Q3"},
    # 2022
    {"date":"2022-02-16","actual_eps":4.43,"est_eps":3.65,"fiscal_q":"FY2022Q4"},
    {"date":"2022-05-25","actual_eps":1.36,"est_eps":1.29,"fiscal_q":"FY2023Q1"},  # ガイダンス下方修正ショック
    {"date":"2022-08-24","actual_eps":0.51,"est_eps":0.50,"fiscal_q":"FY2023Q2"},  # ほぼ予想通り
    {"date":"2022-11-16","actual_eps":0.58,"est_eps":0.70,"fiscal_q":"FY2023Q3"},  # 下方サプライズ
    # 2023
    {"date":"2023-02-22","actual_eps":0.88,"est_eps":0.81,"fiscal_q":"FY2023Q4"},
    {"date":"2023-05-24","actual_eps":1.09,"est_eps":0.92,"fiscal_q":"FY2024Q1"},  # 大幅上方サプライズ・AIブーム開始
    {"date":"2023-08-23","actual_eps":2.70,"est_eps":2.09,"fiscal_q":"FY2024Q2"},  # 超大幅サプライズ
    {"date":"2023-11-21","actual_eps":4.02,"est_eps":3.37,"fiscal_q":"FY2024Q3"},
    # 2024
    {"date":"2024-02-21","actual_eps":5.16,"est_eps":4.59,"fiscal_q":"FY2024Q4"},
    {"date":"2024-05-22","actual_eps":6.12,"est_eps":5.59,"fiscal_q":"FY2025Q1"},
    {"date":"2024-08-28","actual_eps":0.68,"est_eps":0.64,"fiscal_q":"FY2025Q2"},  # 株式分割後
    {"date":"2024-11-20","actual_eps":0.81,"est_eps":0.75,"fiscal_q":"FY2025Q3"},
    # 2025
    {"date":"2025-02-26","actual_eps":0.89,"est_eps":0.84,"fiscal_q":"FY2025Q4"},
    {"date":"2025-05-28","actual_eps":0.96,"est_eps":0.89,"fiscal_q":"FY2026Q1"},
]

HOLD_DAYS  = [3, 5, 7]
ETFS       = ["SMH", "SOXX"]

def get_vix(date_str):
    try:
        rd = datetime.strptime(date_str, "%Y-%m-%d")
        v  = yf.download("^VIX",
                         start=(rd - timedelta(5)).strftime("%Y-%m-%d"),
                         end=(rd + timedelta(3)).strftime("%Y-%m-%d"),
                         progress=False, auto_adjust=True)
        return round(float(v['Close'].iloc[-1]), 2) if len(v) > 0 else None
    except: return None

def get_nvda_gap(date_str):
    """NVDA決算翌日のギャップ率（Open/前日Close - 1）"""
    try:
        rd    = datetime.strptime(date_str, "%Y-%m-%d")
        start = (rd - timedelta(5)).strftime("%Y-%m-%d")
        end   = (rd + timedelta(5)).strftime("%Y-%m-%d")
        df    = yf.download("NVDA", start=start, end=end,
                            progress=False, auto_adjust=True)
        df.index = pd.to_datetime(df.index)
        after = df[df.index > rd]
        if len(after) < 1: return None
        prev_close = float(df[df.index <= rd]['Close'].iloc[-1])
        next_open  = float(after['Open'].iloc[0])
        return round((next_open - prev_close) / prev_close * 100, 2)
    except: return None

def backtest_etf(earnings, etf):
    """1決算×1ETFのバックテスト"""
    date_str = earnings['date']
    try:
        rd    = datetime.strptime(date_str, "%Y-%m-%d")
        start = (rd - timedelta(10)).strftime("%Y-%m-%d")
        end   = (rd + timedelta(30)).strftime("%Y-%m-%d")

        df = yf.download(etf, start=start, end=end,
                         progress=False, auto_adjust=True)
        if len(df) < 5: return None
        df.index = pd.to_datetime(df.index)

        after = df[df.index > rd]
        if len(after) < 2: return None

        # エントリー：翌営業日の寄り付き（Open）
        entry_open  = float(after['Open'].iloc[0])
        entry_date  = after.index[0]
        # 前日終値（決算日終値）
        prev_close  = float(df[df.index <= rd]['Close'].iloc[-1])
        # 翌日終値
        next_close  = float(after['Close'].iloc[0])

        # ETFギャップ（前日Close→翌日Open）
        etf_gap = (entry_open - prev_close) / prev_close * 100
        # ETF翌日の動き（Open→Close）
        intraday = (next_close - entry_open) / entry_open * 100

        res = {
            'date':       date_str,
            'etf':        etf,
            'fiscal_q':   earnings['fiscal_q'],
            'actual_eps': earnings['actual_eps'],
            'est_eps':    earnings['est_eps'],
            'surprise_pct': round((earnings['actual_eps'] - earnings['est_eps'])
                                   / abs(earnings['est_eps']) * 100, 2),
            'entry_open': round(entry_open, 2),
            'prev_close': round(prev_close, 2),
            'etf_gap_pct':   round(etf_gap, 2),
            'intraday_pct':  round(intraday, 2),
        }

        # 保有期間別リターン（Open→N日後Close）
        for d in HOLD_DAYS:
            target = entry_date + timedelta(d)
            fut = df[df.index >= target]
            if len(fut) > 0:
                exit_p = float(fut['Close'].iloc[0])
                ret    = (exit_p - entry_open) / entry_open * 100
                res[f'ret_{d}d']  = round(ret, 2)
                res[f'win_{d}d']  = 1 if ret > 0 else 0
            else:
                res[f'ret_{d}d']  = res[f'win_{d}d'] = None

        res['vix']       = get_vix(date_str)
        res['nvda_gap']  = get_nvda_gap(date_str)
        return res

    except Exception as e:
        print(f"  ERR {etf} {date_str}: {e}"); return None

def show(sub, label, rc='ret_5d', wc='win_5d'):
    s = sub[sub[rc].notna()]
    if len(s) == 0: return
    print(f"  {label:<42} n={len(s):2d}  勝率={s[wc].mean()*100:.0f}%  "
          f"平均={s[rc].mean():+.2f}%  中央値={s[rc].median():+.2f}%  "
          f"最良={s[rc].max():+.2f}%  最悪={s[rc].min():+.2f}%")

def main():
    print("="*75)
    print("NVDAサプライズ→半導体ETF追随ギャップ戦略 バックテスト")
    print(f"対象決算: {len(NVDA_EARNINGS)}件 / ETF: {ETFS} / 保有: {HOLD_DAYS}日")
    print("="*75)

    results = []
    for i, e in enumerate(NVDA_EARNINGS):
        sp = (e['actual_eps'] - e['est_eps']) / abs(e['est_eps']) * 100
        print(f"[{i+1:02d}/{len(NVDA_EARNINGS)}] {e['date']}  "
              f"EPS実績:{e['actual_eps']:.2f} 予想:{e['est_eps']:.2f} "
              f"サプライズ:{sp:+.1f}%")
        for etf in ETFS:
            res = backtest_etf(e, etf)
            if res: results.append(res)

    df = pd.DataFrame(results)
    if df.empty: return
    print(f"\n取得成功: {len(df)}件")

    # サプライズ方向で分類
    df['direction'] = df['surprise_pct'].apply(
        lambda x: 'beat' if x > 0 else ('miss' if x < 0 else 'inline'))

    print("\n【A】全体集計（保有期間別）")
    for d in HOLD_DAYS: show(df, f"全件 {d}日後", f'ret_{d}d', f'win_{d}d')

    print("\n【B】上方サプライズのみ（主戦場）/ 5日後")
    beats = df[df.direction == 'beat']
    for etf in ETFS:
        show(beats[beats.etf==etf], f"上方サプライズ × {etf}")

    print("\n【C】サプライズ幅別（5日後）")
    for etf in ETFS:
        sub = beats[beats.etf==etf]
        for lbl, cond in [
            ("サプライズ+5%未満",      sub[sub.surprise_pct < 5]),
            ("サプライズ+5〜15%",      sub[(sub.surprise_pct>=5)&(sub.surprise_pct<15)]),
            ("サプライズ+15%以上",     sub[sub.surprise_pct >= 15]),
        ]:
            show(cond, f"{etf} × {lbl}")

    print("\n【D】ETFギャップ幅別（5日後）← 出遅れの測定")
    print("  ※ ETFギャップ小＝出遅れが大きい＝追随余地あり")
    for etf in ETFS:
        sub = beats[beats.etf==etf]
        med_gap = sub['etf_gap_pct'].median()
        print(f"\n  {etf} ETFギャップ中央値: {med_gap:+.2f}%")
        for lbl, cond in [
            ("ギャップ+2%未満（小・出遅れ大）", sub[sub.etf_gap_pct < 2]),
            ("ギャップ+2〜4%（中）",           sub[(sub.etf_gap_pct>=2)&(sub.etf_gap_pct<4)]),
            ("ギャップ+4%以上（大・既に追随）", sub[sub.etf_gap_pct >= 4]),
        ]:
            show(cond, f"{etf} × {lbl}")

    print("\n【E】NVDAギャップ vs ETFギャップ差（出遅れ分析）")
    df_gap = df[df.nvda_gap.notna() & df.etf_gap_pct.notna()].copy()
    df_gap['gap_diff'] = df_gap['nvda_gap'] - df_gap['etf_gap_pct']
    beats_gap = df_gap[df_gap.direction=='beat']
    for etf in ETFS:
        sub = beats_gap[beats_gap.etf==etf]
        if len(sub) > 0:
            print(f"\n  {etf}:  NVDAギャップ平均={sub.nvda_gap.mean():+.2f}%  "
                  f"ETFギャップ平均={sub.etf_gap_pct.mean():+.2f}%  "
                  f"出遅れ平均={sub.gap_diff.mean():+.2f}%")
            for lbl, cond in [
                ("出遅れ+2%以上（大きな追随余地）", sub[sub.gap_diff >= 2]),
                ("出遅れ+1〜2%",                   sub[(sub.gap_diff>=1)&(sub.gap_diff<2)]),
                ("出遅れ小（すでに追随）",           sub[sub.gap_diff < 1]),
            ]:
                show(cond, f"{etf} × {lbl}")

    print("\n【F】VIX水準別（5日後）")
    df_vix = beats[beats.vix.notna()].copy()
    df_vix['vb'] = pd.cut(df_vix.vix, [0,15,20,30,100],
                           labels=["低VIX<15","中低VIX15-20","中高VIX20-30","高VIX>30"])
    for etf in ETFS:
        sub = df_vix[df_vix.etf==etf]
        for b, s in sub.groupby('vb', observed=True):
            show(s, f"{etf} × {b}")

    print("\n【G】SMH vs SOXX 直接比較（上方サプライズ×5日後）")
    pivot = beats.pivot_table(
        values=['ret_3d','ret_5d','ret_7d','win_5d'],
        index='date', columns='etf').round(2)
    print(pivot.to_string())

    print("\n【H】個別案件リスト（サプライズ大きい順）")
    cols = ['date','etf','fiscal_q','surprise_pct','nvda_gap','etf_gap_pct',
            'intraday_pct','ret_3d','ret_5d','ret_7d','vix']
    pd.set_option('display.width', 160)
    print(beats[cols].sort_values('surprise_pct', ascending=False).to_string(index=False))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'nvda_etf_backtest_result.csv')
    df.to_csv(out, index=False, encoding='utf-8-sig')
    print(f"\n✓ CSV: {out}")

if __name__ == '__main__': main()
