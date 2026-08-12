"""
tests/test_macro_data_reader.py

BACKLOG [[MACRODATA-LAYER-CONSTRUCTION-1]] common/macro_data/reader.py の
単体テスト。fetcher.pyが書き込むseries/{SERIES_ID}.jsonを読み取るAPI群
（get_latest・get_series・get_value_as_of）の正常系・欠損系・
ルックバック境界を検証する。ネットワークアクセス（fredapi呼び出し）は
行わない。

実行方法:
    python -m pytest tests/test_macro_data_reader.py -v
"""

import os

from common.macro_data import fetcher, reader


def _seed_series(base_dir: str, series_id: str, pairs):
    """[(as_of, value), ...] からseries/{series_id}.jsonを直接書き込む
    （fetcher経由ではなく、reader単体のテストのため直接シードする）。"""
    records = [
        {
            "value": val,
            "as_of": as_of,
            "fetched_at": "2026-08-12T00:00:00+09:00",
            "source": "FRED",
            "source_detail": f"series={series_id}",
        }
        for as_of, val in pairs
    ]
    payload = {"series_id": series_id, "records": records}
    fetcher._atomic_write_json(
        os.path.join(base_dir, "series", f"{series_id}.json"), payload
    )


class TestGetLatest:
    def test_missing_series_returns_none(self, tmp_path):
        assert reader.get_latest("NOPE", base_dir=str(tmp_path)) is None

    def test_single_record_returned(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-01-01", 0.5)])
        latest = reader.get_latest("T10Y2Y", base_dir=base)
        assert latest["as_of"] == "2026-01-01"
        assert latest["value"] == 0.5

    def test_picks_most_recent_of_multiple_records(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-01-01", 0.5), ("2026-03-01", 0.7), ("2026-02-01", 0.6)])
        latest = reader.get_latest("T10Y2Y", base_dir=base)
        assert latest["as_of"] == "2026-03-01"
        assert latest["value"] == 0.7


class TestGetSeries:
    def test_missing_series_returns_empty_list(self, tmp_path):
        assert reader.get_series("NOPE", base_dir=str(tmp_path)) == []

    def test_no_range_returns_all_ascending(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-03-01", 0.7), ("2026-01-01", 0.5), ("2026-02-01", 0.6)])
        series = reader.get_series("T10Y2Y", base_dir=base)
        assert [r["as_of"] for r in series] == ["2026-01-01", "2026-02-01", "2026-03-01"]

    def test_start_only_filters_lower_bound_inclusive(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-01-01", 0.5), ("2026-02-01", 0.6), ("2026-03-01", 0.7)])
        series = reader.get_series("T10Y2Y", start="2026-02-01", base_dir=base)
        assert [r["as_of"] for r in series] == ["2026-02-01", "2026-03-01"]

    def test_end_only_filters_upper_bound_inclusive(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-01-01", 0.5), ("2026-02-01", 0.6), ("2026-03-01", 0.7)])
        series = reader.get_series("T10Y2Y", end="2026-02-01", base_dir=base)
        assert [r["as_of"] for r in series] == ["2026-01-01", "2026-02-01"]

    def test_start_and_end_both_inclusive(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-01-01", 0.5), ("2026-02-01", 0.6), ("2026-03-01", 0.7)])
        series = reader.get_series("T10Y2Y", start="2026-01-01", end="2026-02-01", base_dir=base)
        assert [r["as_of"] for r in series] == ["2026-01-01", "2026-02-01"]

    def test_date_object_accepted_for_start_end(self, tmp_path):
        import datetime as _dt
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-01-01", 0.5), ("2026-02-01", 0.6)])
        series = reader.get_series(
            "T10Y2Y", start=_dt.date(2026, 2, 1), base_dir=base
        )
        assert [r["as_of"] for r in series] == ["2026-02-01"]

    def test_out_of_range_returns_empty(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "T10Y2Y", [("2026-01-01", 0.5)])
        series = reader.get_series("T10Y2Y", start="2027-01-01", base_dir=base)
        assert series == []


class TestGetValueAsOf:
    def test_missing_series_returns_none(self, tmp_path):
        assert reader.get_value_as_of("NOPE", "2026-06-03", base_dir=str(tmp_path)) is None

    def test_exact_date_match_returned(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "PAYEMS", [("2026-06-01", 150000.0)])
        record = reader.get_value_as_of("PAYEMS", "2026-06-01", base_dir=base)
        assert record["as_of"] == "2026-06-01"
        assert record["value"] == 150000.0

    def test_most_recent_before_target_within_window_returned(self, tmp_path):
        """monthly系列: target日そのものにレコードがなくても、
        window内の直近過去日を返すこと"""
        base = str(tmp_path)
        _seed_series(base, "PAYEMS", [("2026-06-01", 150000.0)])
        record = reader.get_value_as_of("PAYEMS", "2026-06-20", base_dir=base)
        assert record["as_of"] == "2026-06-01"

    def test_picks_latest_among_multiple_candidates_within_window(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "PAYEMS", [("2026-05-01", 149000.0), ("2026-06-01", 150000.0)])
        record = reader.get_value_as_of("PAYEMS", "2026-06-15", base_dir=base)
        assert record["as_of"] == "2026-06-01"
        assert record["value"] == 150000.0

    def test_data_exactly_at_default_45day_window_boundary_returned(self, tmp_path):
        """target - 45日ちょうどのレコードは境界内として採用されること"""
        base = str(tmp_path)
        _seed_series(base, "PAYEMS", [("2026-05-01", 149000.0)])
        # 2026-05-01 + 45日 = 2026-06-15
        record = reader.get_value_as_of("PAYEMS", "2026-06-15", base_dir=base)
        assert record["as_of"] == "2026-05-01"

    def test_data_one_day_past_default_window_returns_none(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "PAYEMS", [("2026-05-01", 149000.0)])
        # 2026-05-01 + 46日 = 2026-06-16 → 窓外
        record = reader.get_value_as_of("PAYEMS", "2026-06-16", base_dir=base)
        assert record is None

    def test_future_data_after_target_is_not_used(self, tmp_path):
        """target日より後のレコードは使わない（as-of検索の方向性確認）"""
        base = str(tmp_path)
        _seed_series(base, "PAYEMS", [("2026-07-01", 151000.0)])
        record = reader.get_value_as_of("PAYEMS", "2026-06-01", base_dir=base)
        assert record is None

    def test_custom_lookback_days_narrower_window(self, tmp_path):
        base = str(tmp_path)
        _seed_series(base, "BAMLH0A0HYM2", [("2026-06-01", 3.2)])
        # 10日ルックバックでは6/1→6/15 (14日差) は窓外
        record = reader.get_value_as_of(
            "BAMLH0A0HYM2", "2026-06-15", lookback_days=10, base_dir=base
        )
        assert record is None

    def test_date_object_accepted(self, tmp_path):
        import datetime as _dt
        base = str(tmp_path)
        _seed_series(base, "PAYEMS", [("2026-06-01", 150000.0)])
        record = reader.get_value_as_of("PAYEMS", _dt.date(2026, 6, 1), base_dir=base)
        assert record["as_of"] == "2026-06-01"


class TestErrorResilienceForNeverFetchedSeries:
    def test_all_apis_return_empty_values_not_raise(self, tmp_path):
        base = str(tmp_path)
        assert reader.get_latest("NEVERFETCHED", base_dir=base) is None
        assert reader.get_series("NEVERFETCHED", base_dir=base) == []
        assert reader.get_value_as_of("NEVERFETCHED", "2026-06-01", base_dir=base) is None
