"""
common/sec_data/revenue_tag_conflict_check.py
責務: MERGE_ALL_TAGS_FIELDS対象（revenue/selling_and_marketing/
depreciation_and_amortization）の候補XBRLタグ間で、同一会計年度に
値が大きく食い違う「タグ競合」を検知する（読み取り専用・自動修正なし）。

ARCH-DATA-1残課題③: SEC-REV-FINTECH-1（SOFI）・BUG-REV-SPAC-1（IONQ）は
いずれも parser.py::_extract_values_merged() が複数候補タグを
tie-breakで静かに1つに一本化してしまい、「競合が発生した事実」自体が
失われることが発見を遅らせた根本原因だった
（BACKLOG_DONE.md参照: SOFI=RevenueFromContractWithCustomer($0.62B) vs
RevenuesNetOfInterestExpense($3.61B)、IONQ=Revenues($1,235M) vs
RevenueFromContractWithCustomerExcludingAssessedTax($11.1M)）。

本モジュールは parser.py 本体を一切変更せず、company_facts.json
（update.py Step1で既に取得済み・ネットワーク再取得なし）を再読込し、
SECParser の既存メソッド（_detect_fiscal_end_month/_extract_single_key/
_extract_values_merged）をそのまま呼び出して候補タグ一覧・年度判定
ロジックを再利用する（候補タグ一覧を新規に作り直さない）。

正誤判定（どの候補タグが正しいか）は行わない。SOFI/IONQの実例が示す
通り判断には業種知識（銀行の収益表示・SPAC上場企業の資金調達）が
必要なため、人間が TICKER_RESTRICTIONS への登録可否を判断する
既存フローに委ねる。
"""

import sys

from .fetcher import load_company_facts
from .parser import SECParser
from .tickers import get_tanuki_tickers

# タグ競合とみなす閾値: 同一end_yearで最大値/最小値の比が2.0倍以上。
# CHECK-21 Revenue段差型急変（common/screening/dcf_validity_checker.py::
# check_c_data_jump()）が採用する2.0倍/0.5倍の閾値を踏襲し、既存の
# 異常検知基準との一貫性を保つ。実例のSOFI(5.8倍)・IONQ(111倍)双方に
# 対して十分な余裕を持って検知できる水準。
CONFLICT_RATIO_THRESHOLD = 2.0

# 微小値のノイズを除外する下限（$1M未満の候補は比較対象外）
MIN_VALUE_FOR_COMPARISON = 1_000_000


def _candidate_values_by_year(parser: SECParser, us_gaap: dict, xbrl_keys: list,
                                fiscal_end_month: int) -> dict:
    """
    1フィールド分の全候補タグについて、{end_year: {tag_name: val}} 形式で
    年次(10-K/FY)値を独立に抽出する。

    各タグ単体の抽出には SECParser._extract_single_key() をそのまま使う
    （同一タグ内の複数エントリのtie-break——exact match優先・最新end_date
    優先——を再実装せず再利用するため）。tie-breakで1つに絞り込む前の
    「タグごとの代表値」を候補として横に並べる点が _extract_values_merged()
    と異なる。
    """
    by_year: dict = {}
    for key in xbrl_keys:
        if key not in us_gaap:
            continue
        key_result = parser._extract_single_key(us_gaap, key, fiscal_end_month)
        for yr, val in key_result.get("annual", {}).items():
            if val is None:
                continue
            by_year.setdefault(yr, {})[key] = val
    return by_year


def check_revenue_tag_conflict(ticker: str, data_dir: str | None = None) -> dict:
    """
    company_facts.jsonを再読込し、MERGE_ALL_TAGS_FIELDS対象フィールドの
    候補タグ間で同一年度の値が閾値以上乖離していないか検査する。

    Returns:
    {
      "ticker": str,
      "status": "OK" | "WARN",
      "conflicts": [
        {
          "field": str,                  # "revenue" 等
          "fiscal_year": int,
          "candidates": {tag_name: val, ...},  # 競合した全候補タグと値
          "adopted_tag": str | None,     # _extract_values_merged()が実際に採用したタグ名
          "adopted_value": float | None,
          "max_ratio": float,            # 最大値/最小値
        },
        ...
      ],
    }
    """
    ticker = ticker.upper()
    raw_data = load_company_facts(ticker, data_dir=data_dir)
    if raw_data is None:
        return {"ticker": ticker, "status": "OK", "conflicts": [], "note": "company_facts.json not found"}

    us_gaap = raw_data.get("facts", {}).get("us-gaap", {})
    if not us_gaap:
        return {"ticker": ticker, "status": "OK", "conflicts": []}

    parser = SECParser(data_dir=data_dir)
    fiscal_end_month = parser._detect_fiscal_end_month(us_gaap)

    conflicts = []
    for field_name in sorted(SECParser.MERGE_ALL_TAGS_FIELDS):
        xbrl_keys = SECParser.XBRL_MAPPING.get(field_name, [])
        if not xbrl_keys:
            continue

        by_year = _candidate_values_by_year(parser, us_gaap, xbrl_keys, fiscal_end_month)

        # _extract_values_merged()が実際に採用する値（比較の基準として提示するため）
        merged_annual = parser._extract_values_merged(
            us_gaap, xbrl_keys, use_max=False, fiscal_end_month=fiscal_end_month
        ).get("annual", {})

        for yr, tag_values in by_year.items():
            if len(tag_values) < 2:
                continue  # 候補が1つしかなければ競合しようがない
            comparable = {t: v for t, v in tag_values.items() if abs(v) >= MIN_VALUE_FOR_COMPARISON}
            if len(comparable) < 2:
                continue
            abs_vals = [abs(v) for v in comparable.values()]
            max_v, min_v = max(abs_vals), min(abs_vals)
            if min_v <= 0:
                continue
            ratio = max_v / min_v
            if ratio < CONFLICT_RATIO_THRESHOLD:
                continue

            adopted_value = merged_annual.get(yr)
            adopted_tag = None
            if adopted_value is not None:
                for tag, v in comparable.items():
                    if v == adopted_value:
                        adopted_tag = tag
                        break

            conflicts.append({
                "field": field_name,
                "fiscal_year": yr,
                "candidates": comparable,
                "adopted_tag": adopted_tag,
                "adopted_value": adopted_value,
                "max_ratio": round(ratio, 2),
            })

    status = "WARN" if conflicts else "OK"
    return {"ticker": ticker, "status": status, "conflicts": conflicts}


def _format_conflict(c: dict) -> str:
    cand_str = ", ".join(f"{tag}=${v/1e6:,.1f}M" for tag, v in c["candidates"].items())
    adopted_str = (
        f"{c['adopted_tag']}=${c['adopted_value']/1e6:,.1f}M"
        if c["adopted_tag"] is not None
        else "不明（_extract_values_mergedの採用値と一致する候補なし）"
    )
    return (
        f"  [WARN {c['field']} FY{c['fiscal_year']}] 候補タグ競合 (乖離{c['max_ratio']:.1f}倍): "
        f"{cand_str} → 採用値: {adopted_str}"
    )


def main():
    args = sys.argv[1:]
    tickers = args if args else get_tanuki_tickers()
    if not tickers:
        print("対象銘柄が見つかりません。config/cik_lookup.csv を確認してください。")
        sys.exit(1)

    print(f"=== Revenue系タグ競合チェック ===")
    print(f"対象: {len(tickers)}銘柄 / 閾値: {CONFLICT_RATIO_THRESHOLD}倍")
    print()

    warn_count = 0
    for ticker in tickers:
        result = check_revenue_tag_conflict(ticker)
        if result["status"] == "WARN":
            warn_count += 1
            print(f"⚠️  {ticker}")
            for c in result["conflicts"]:
                print(_format_conflict(c))

    print()
    print(f"合計: {warn_count}/{len(tickers)}銘柄でタグ競合の疑いを検知")


if __name__ == "__main__":
    main()
