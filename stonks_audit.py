import json

d = json.load(open('docs/value-monitor/stonks-silo/data/results.json', encoding='utf-8'))
for ticker, t in sorted(d['tickers'].items()):
    dq = t['deficit_quality']
    ra = t['runway']
    pp = t['profitability_path']
    rec = t.get('records', {})

    years = t['years']
    rev = {yr: rec.get(str(yr), {}).get('revenue') for yr in years}
    ni  = {yr: rec.get(str(yr), {}).get('net_income') for yr in years}
    ocf = pp['ocf_annual']

    def fmt(v):
        if v is None: return 'N/A'
        if abs(v) >= 1e9: return f'${v/1e9:.2f}B'
        if abs(v) >= 1e6: return f'${v/1e6:.0f}M'
        return f'${v:,.0f}'

    print(f'=== {ticker} ===')
    print(f'  総合: {t["overall_verdict"]}({t["overall_score"]})')
    print(f'  売上:   ' + '  '.join(f'{yr}:{fmt(v)}' for yr, v in rev.items()))
    print(f'  純利益: ' + '  '.join(f'{yr}:{fmt(v)}' for yr, v in ni.items()))
    print(f'  OCF:    ' + '  '.join(f'{yr}:{fmt(v)}' for yr, v in ocf.items()))
    gm = dq['gross_margin']
    gm_str = f'{gm:.1f}%' if gm is not None else 'N/A'
    derived = dq.get('gross_margin_derived', False)
    print(f'  粗利率: {gm_str}{"(逆算)" if derived else ""}  CAGR: {dq["cagr_3yr"]}%  R&D: {dq["rnd_ratio"]}  S&M: {dq["sm_ratio"]}')
    print(f'  現金: {fmt(ra["cash"])}  月次バーン: {fmt(ra["monthly_burn"])}  Runway: {ra["runway_months"]}ヶ月  判定: {ra["verdict"]}')
    print(f'  OCFトレンド: {pp["ocf_trend"]}  OCF_BE: {pp["ocf_breakeven_reason"]}  GAAP_BE: {pp["gaap_breakeven_reason"]}')
    print()
