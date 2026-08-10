"""
tests/test_market_data_fetcher.py

BACKLOG [[MARKETDATA-LAYER-CONSTRUCTION-1]] common/market_data/fetcher.py の
単体テスト。保存前検証ロジック（validate_price_record・validate_attributes_record）
とアトミック書き込み・重複排除ロジックを検証する。ネットワークアクセス
（yfinance呼び出し）は行わない。

実行方法:
    python -m pytest tests/test_market_data_fetcher.py -v
"""

import json
import os

from common.market_data import fetcher


class TestValidatePriceRecord:
    def test_normal_record_has_no_warnings(self):
        record = {"open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0, "volume": 1000}
        assert fetcher.validate_price_record(record) == []

    def test_close_not_positive_is_flagged(self):
        record = {"open": 10.0, "high": 12.0, "low": 9.0, "close": -1.0, "volume": 1000}
        warnings = fetcher.validate_price_record(record)
        assert any("close" in w for w in warnings)

    def test_volume_zero_is_flagged(self):
        record = {"open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0, "volume": 0}
        warnings = fetcher.validate_price_record(record)
        assert any("volume" in w for w in warnings)

    def test_volume_missing_key_is_not_checked(self):
        """フィールド自体が存在しない場合は検証をスキップする
        （fetch_daily_prices()は.history()由来のためvolume自体は常に含まれるが、
        将来別経路のレコードで一部フィールドが欠けるケースに備えた仕様）"""
        record = {"open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0}
        assert fetcher.validate_price_record(record) == []

    def test_high_less_than_close_is_flagged(self):
        record = {"open": 10.0, "high": 10.5, "low": 9.0, "close": 11.0, "volume": 1000}
        warnings = fetcher.validate_price_record(record)
        assert any("high >= close >= low" in w for w in warnings)

    def test_close_less_than_low_is_flagged(self):
        record = {"open": 10.0, "high": 12.0, "low": 9.0, "close": 8.0, "volume": 1000}
        warnings = fetcher.validate_price_record(record)
        assert any("high >= close >= low" in w for w in warnings)

    def test_fifty_two_week_inverted_is_flagged(self):
        record = {
            "close": 11.0, "volume": 1000,
            "fifty_two_week_high": 5.0, "fifty_two_week_low": 20.0,
        }
        warnings = fetcher.validate_price_record(record)
        assert any("fifty_two_week" in w for w in warnings)

    def test_fifty_two_week_absent_is_not_checked(self):
        """yfinance側の52週高安値が存在しない場合（.history()のみの通常経路）は
        検証自体をスキップする"""
        record = {"open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0, "volume": 1000}
        assert fetcher.validate_price_record(record) == []

    def test_multiple_violations_all_reported(self):
        record = {"open": -1.0, "high": 1.0, "low": 9.0, "close": -1.0, "volume": 0}
        warnings = fetcher.validate_price_record(record)
        assert len(warnings) >= 3


class TestValidateAttributesRecord:
    def test_matching_market_cap_has_no_warnings(self):
        record = {"current_price": 100.0, "shares_outstanding": 1000, "market_cap": 100000}
        assert fetcher.validate_attributes_record(record) == []

    def test_missing_fields_skips_check(self):
        """指数等でshares_outstanding/market_capが存在しない場合は検証をスキップする"""
        record = {"current_price": 7748.78}
        assert fetcher.validate_attributes_record(record) == []

    def test_large_cap_relative_tolerance_exceeded_is_flagged(self):
        record = {
            "current_price": 300.0, "shares_outstanding": 15_000_000_000,
            "market_cap": 5_000_000_000_000,
        }
        warnings = fetcher.validate_attributes_record(record)
        assert len(warnings) == 1
        assert "market_cap mismatch" in warnings[0]

    def test_large_cap_within_relative_tolerance_is_not_flagged(self):
        # computed = 300 * 15e9 = 4.5e12, reported差1%以内
        record = {
            "current_price": 300.0, "shares_outstanding": 15_000_000_000,
            "market_cap": 4_540_000_000_000,
        }
        assert fetcher.validate_attributes_record(record) == []

    def test_small_cap_absolute_floor_protects_against_false_positive(self):
        """小型株では相対2%が小さすぎるため、絶対$1,000,000フロアが優先される"""
        record = {"current_price": 1.0, "shares_outstanding": 1_000_000, "market_cap": 1_950_000}
        assert fetcher.validate_attributes_record(record) == []

    def test_small_cap_exceeding_absolute_floor_is_flagged(self):
        record = {"current_price": 1.0, "shares_outstanding": 1_000_000, "market_cap": 2_500_000}
        warnings = fetcher.validate_attributes_record(record)
        assert len(warnings) == 1


class TestAtomicWriteJson:
    def test_write_and_read_roundtrip(self, tmp_path):
        path = os.path.join(str(tmp_path), "sub", "out.json")
        fetcher._atomic_write_json(path, {"a": 1})
        assert json.load(open(path, encoding="utf-8")) == {"a": 1}

    def test_no_leftover_tempfile_after_success(self, tmp_path):
        path = os.path.join(str(tmp_path), "out.json")
        fetcher._atomic_write_json(path, {"a": 1})
        leftovers = [f for f in os.listdir(str(tmp_path)) if f.startswith(".tmp_")]
        assert leftovers == []

    def test_existing_file_untouched_when_write_fails(self, tmp_path):
        """書き込み中に例外が発生しても、既存ファイルは元の内容のまま残る
        （tempfile→os.replace()方式のアトミック性の確認）"""
        path = os.path.join(str(tmp_path), "out.json")
        fetcher._atomic_write_json(path, {"version": 1})

        class Unserializable:
            def __iter__(self):
                raise RuntimeError("simulated crash during write")

        try:
            fetcher._atomic_write_json(path, {"version": 2, "data": Unserializable()})
        except TypeError:
            pass

        assert json.load(open(path, encoding="utf-8")) == {"version": 1}
        leftovers = [f for f in os.listdir(str(tmp_path)) if f.startswith(".tmp_")]
        assert leftovers == []


class TestViolationsLogSections:
    def test_empty_warnings_still_written(self, tmp_path):
        base = str(tmp_path)
        fetcher._write_violations_section(
            "AAPL", "daily_price_validation",
            {"checked_at": "2026-08-10T00:00:00+00:00", "date": "2026-08-10", "warnings": []},
            base_dir=base,
        )
        path = fetcher._violations_log_path("AAPL", base)
        saved = json.load(open(path, encoding="utf-8"))
        assert saved["daily_price_validation"]["warnings"] == []

    def test_daily_and_attributes_sections_do_not_clobber_each_other(self, tmp_path):
        base = str(tmp_path)
        fetcher._write_violations_section(
            "AAPL", "daily_price_validation",
            {"checked_at": "t1", "date": "2026-08-10", "warnings": ["daily warn"]},
            base_dir=base,
        )
        fetcher._write_violations_section(
            "AAPL", "attributes_validation",
            {"checked_at": "t2", "warnings": ["attr warn"]},
            base_dir=base,
        )
        path = fetcher._violations_log_path("AAPL", base)
        saved = json.load(open(path, encoding="utf-8"))
        assert saved["daily_price_validation"]["warnings"] == ["daily warn"]
        assert saved["attributes_validation"]["warnings"] == ["attr warn"]


class TestAppendDailyRecordDedup:
    def test_same_date_refetch_replaces_not_duplicates(self, tmp_path):
        base = str(tmp_path)
        record_v1 = {"date": "2026-08-10", "close": 100.0, "volume": 1000, "_validation_warnings": []}
        record_v2 = {"date": "2026-08-10", "close": 101.0, "volume": 1100, "_validation_warnings": []}
        fetcher._append_daily_record("AAPL", record_v1, base_dir=base)
        fetcher._append_daily_record("AAPL", record_v2, base_dir=base)
        path = os.path.join(base, "daily", "AAPL.json")
        saved = json.load(open(path, encoding="utf-8"))
        assert len(saved["records"]) == 1
        assert saved["records"][0]["close"] == 101.0

    def test_different_dates_both_kept_sorted(self, tmp_path):
        base = str(tmp_path)
        fetcher._append_daily_record(
            "AAPL", {"date": "2026-08-11", "close": 102.0, "volume": 900, "_validation_warnings": []},
            base_dir=base,
        )
        fetcher._append_daily_record(
            "AAPL", {"date": "2026-08-10", "close": 100.0, "volume": 1000, "_validation_warnings": []},
            base_dir=base,
        )
        path = os.path.join(base, "daily", "AAPL.json")
        saved = json.load(open(path, encoding="utf-8"))
        dates = [r["date"] for r in saved["records"]]
        assert dates == ["2026-08-10", "2026-08-11"]


class TestNyseCalendar:
    def test_known_fixed_holiday_is_not_trading_day(self):
        # 感謝祭2026-11-26
        assert fetcher.is_trading_day("2026-11-26") is False

    def test_regular_weekday_is_trading_day(self):
        assert fetcher.is_trading_day("2026-08-10") is True

    def test_observed_july_fourth_holiday_is_not_trading_day(self):
        # 2026-07-04は土曜のため2026-07-03（金）が振替休場になる
        assert fetcher.is_trading_day("2026-07-03") is False

    def test_regular_weekend_is_not_trading_day(self):
        assert fetcher.is_trading_day("2026-08-08") is False
