"""
tests/test_parser_period_length_validated_fields.py

[[PERIOD-LENGTH-VALIDATION-GAP-1]]の回帰テスト。
parser.py::_extract_single_key()（_extract_values_best_candidate()経由、
MERGE_ALL_TAGS_FIELDS以外の全FLOW型フィールドが通る候補選定）が、
PERIOD_LENGTH_VALIDATED_FIELDS対象フィールドでは年次候補として
受理する際に期間長(340-380日)を必須条件とすることを確認する。
GrossProfitタグが主要財務諸表になく「四半期実績（未監査）」注記にのみ
存在する企業（TDY/AVGO/CPRT/ABBV/CAT/FICO/HEI/HON/KLAC等）で、91日程度の
四半期値が年次値として誤採用される問題への対応。

実行方法:
    python -m pytest tests/test_parser_period_length_validated_fields.py -v
"""

from common.sec_data.parser import SECParser


def _entry(start, end, val, fy, fp="FY", form="10-K", filed=None):
    return {
        "start": start, "end": end, "val": val, "accn": "0000000000-00-000000",
        "fp": fp, "fy": fy, "form": form, "filed": filed or (end + "T00:00:00"),
    }


def test_single_key_rejects_quarterly_entry_for_validated_field():
    """対象フィールド(gross_profit)で91日間の単独候補は受理されない（None）"""
    us_gaap = {
        "GrossProfit": {"units": {"USD": [
            _entry("2013-09-30", "2013-12-29", 214600000, fy=2013),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_single_key(
        us_gaap, "GrossProfit", fiscal_end_month=12, field_name="gross_profit",
    )
    assert result["annual"].get(2013) is None


def test_single_key_accepts_annual_entry_for_validated_field():
    """対象フィールド(gross_profit)で365日間の単独候補は従来通り受理される"""
    us_gaap = {
        "GrossProfit": {"units": {"USD": [
            _entry("2012-12-31", "2013-12-29", 838600000, fy=2013),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_single_key(
        us_gaap, "GrossProfit", fiscal_end_month=12, field_name="gross_profit",
    )
    assert result["annual"].get(2013) == 838600000


def test_single_key_does_not_affect_unvalidated_fields():
    """PERIOD_LENGTH_VALIDATED_FIELDS対象外のフィールド（例: eps_diluted）は
    従来通りduration不問で受理される（対象範囲を9フィールドに限定した設計の確認）"""
    us_gaap = {
        "EarningsPerShareDiluted": {"units": {"USD/shares": [
            _entry("2013-09-30", "2013-12-29", 4.87, fy=2013),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_single_key(
        us_gaap, "EarningsPerShareDiluted", fiscal_end_month=12, field_name="eps_diluted",
    )
    assert result["annual"].get(2013) == 4.87


def test_single_key_field_name_default_empty_does_not_filter():
    """field_name省略時（デフォルト""）は従来通りフィルタが適用されない
    （既存呼び出し元との後方互換性の確認）"""
    us_gaap = {
        "GrossProfit": {"units": {"USD": [
            _entry("2013-09-30", "2013-12-29", 214600000, fy=2013),
        ]}},
    }
    parser = SECParser()
    result = parser._extract_single_key(
        us_gaap, "GrossProfit", fiscal_end_month=12,
    )
    assert result["annual"].get(2013) == 214600000
