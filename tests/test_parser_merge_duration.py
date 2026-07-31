"""
tests/test_parser_merge_duration.py

SEC-TAG-FICO-CPRT-1の回帰テスト。
parser.py::_extract_values_merged()（MERGE_ALL_TAGS_FIELDS対象:
revenue/selling_and_marketing/depreciation_and_amortization）が、
同一end_dateに複数タグが競合した場合「先に処理されたタグが勝つ」
早い者勝ちだった問題を検証する。91日間の四半期比較開示が
form='10-K'・fp='FY'で年次候補に混入しても、365日間の正規の年次値を
優先して採用することを確認する（FICO/CPRT/LITEで実際に確認された
パターンを再現）。

実行方法:
    python -m pytest tests/test_parser_merge_duration.py -v
"""

from common.sec_data.parser import SECParser


def _entry(start, end, val, fy, fp="FY", form="10-K", filed=None):
    return {
        "start": start, "end": end, "val": val, "accn": "0000000000-00-000000",
        "fp": fp, "fy": fy, "form": form, "filed": filed or (end + "T00:00:00"),
    }


def test_merge_prefers_365day_duration_over_91day_when_end_date_tied():
    """FICO型: 同一end_dateで91日間(誤)と365日間(正)が競合 → 365日間を採用"""
    us_gaap = {
        # 先に列挙される(=XBRL_MAPPING上optimisticに先勝ちしていた)タグ: 91日間の誤エントリ
        "Revenues": {"units": {"USD": [
            _entry("2020-07-01", "2020-09-30", 374356000, fy=2019),
        ]}},
        # 後に列挙されるタグ: 365日間の正規エントリ
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
            _entry("2019-10-01", "2020-09-30", 1294562000, fy=2019),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_values_merged(
        us_gaap,
        ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
         "RevenueFromContractWithCustomerIncludingAssessedTax", "RevenueFromContractWithCustomer",
         "SalesRevenueNet", "TotalRevenue", "RevenuesNetOfInterestExpense"],
        use_max=False, fiscal_end_month=9,
    )
    assert result["annual"].get(2020) == 1294562000


def test_merge_prefers_365day_duration_regardless_of_tag_order():
    """タグの列挙順を逆にしても365日間が勝つこと（順序非依存であることの確認）"""
    us_gaap = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
            _entry("2019-10-01", "2020-09-30", 1294562000, fy=2019),
        ]}},
        "Revenues": {"units": {"USD": [
            _entry("2020-07-01", "2020-09-30", 374356000, fy=2019),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_values_merged(
        us_gaap,
        ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
        use_max=False, fiscal_end_month=9,
    )
    assert result["annual"].get(2020) == 1294562000


def test_merge_keeps_later_end_date_unconditionally():
    """end_dateが異なる場合は従来通り最新end_dateを優先する（durationは同一end_date時のみのtie-break）"""
    us_gaap = {
        "TagA": {"units": {"USD": [
            _entry("2019-01-01", "2019-12-31", 100, fy=2019),
        ]}},
        "TagB": {"units": {"USD": [
            _entry("2019-01-01", "2019-12-30", 200, fy=2019),  # 1日短いend_date・fy一致
        ]}},
    }
    parser = SECParser()
    result = parser._extract_values_merged(
        us_gaap, ["TagA", "TagB"], use_max=False, fiscal_end_month=12,
    )
    # TagAのend_date(12-31)がTagBより新しいため、durationに関わらずTagAが勝つ
    assert result["annual"].get(2019) == 100


def test_merge_no_regression_when_single_candidate():
    """候補が1つしかない場合は従来通り採用される（回帰なし）"""
    us_gaap = {
        "Revenues": {"units": {"USD": [
            _entry("2024-01-01", "2024-12-31", 5000000000, fy=2024),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_values_merged(
        us_gaap, ["Revenues", "SalesRevenueNet"], use_max=False, fiscal_end_month=12,
    )
    assert result["annual"].get(2024) == 5000000000


def test_merge_exact_match_does_not_bypass_duration_filter():
    """[[PERIOD-LENGTH-VALIDATION-GAP-1]]対応後: fy==end_yearの完全一致（exact
    match）であっても、期間長(340-380日)フィルタは無条件で優先適用され、
    候補が1つのみでも範囲外なら採用されない（None）。
    対応前は「候補が1つのみのためdurationに関わらず採用される」仕様だったが、
    これはTDY/AVGO/CPRT等で四半期値が年次値として誤採用される直接の原因
    だったため、意図的に仕様変更した。
    """
    us_gaap = {
        # exact=True（fy=2020, end_year=2020）だが91日間の四半期エントリ
        "TagShortExact": {"units": {"USD": [
            _entry("2020-01-01", "2020-03-31", 50, fy=2020),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_values_merged(
        us_gaap, ["TagShortExact"], use_max=False, fiscal_end_month=12,
    )
    assert result["annual"].get(2020) is None
