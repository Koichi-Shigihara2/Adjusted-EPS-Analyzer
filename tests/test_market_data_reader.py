"""
tests/test_market_data_reader.py

BACKLOG [[MARKETDATA-LAYER-CONSTRUCTION-1]] common/market_data/reader.py の
単体テスト。fetcher.pyが書き込むdaily/・attributes/・analyst_history/を
読み取るAPI群（get_latest_price・get_price_series・get_ma_deviation・
get_attributes・get_analyst_events・get_calendar・get_index_series・
get_sp500_constituents_prices）の正常系・欠損系・エラー耐性を検証する。
ネットワークアクセス（yfinance呼び出し）は行わない。

実行方法:
    python -m pytest tests/test_market_data_reader.py -v
"""

import os

from common.market_data import fetcher, reader

# 合成データの基準日（NYSE通常営業日、月曜）。「今日」の日付に依存させず
# テストを決定的にするため固定日を使う。
_ANCHOR = "2026-08-10"


def _make_price_record(date: str, close: float, warnings=None) -> dict:
    return {
        "date": date, "open": close - 0.5, "high": close + 1.0, "low": close - 1.0,
        "close": close, "volume": 1000, "_validation_warnings": warnings or [],
    }


def _seed_no_gap_series(base_dir: str, symbol: str, window: int, anchor: str = _ANCHOR):
    """anchorを最終日とするwindow営業日分の連続データ（欠損なし）を書き込み、
    実際に書き込んだ日付リスト（昇順）を返す。"""
    dates = reader._expected_trading_days(anchor, window)
    for i, d in enumerate(dates):
        fetcher._append_daily_record(symbol, _make_price_record(d, 100.0 + i), base_dir=base_dir)
    return dates


class TestGetLatestPrice:
    def test_missing_symbol_returns_none(self, tmp_path):
        assert reader.get_latest_price("NOPE", base_dir=str(tmp_path)) is None

    def test_single_record_returned(self, tmp_path):
        base = str(tmp_path)
        fetcher._append_daily_record("AAPL", _make_price_record(_ANCHOR, 200.0), base_dir=base)
        latest = reader.get_latest_price("AAPL", base_dir=base)
        assert latest["date"] == _ANCHOR
        assert latest["close"] == 200.0
        assert latest["symbol"] == "AAPL"

    def test_picks_most_recent_of_multiple_records(self, tmp_path):
        base = str(tmp_path)
        fetcher._append_daily_record("AAPL", _make_price_record("2026-08-07", 190.0), base_dir=base)
        fetcher._append_daily_record("AAPL", _make_price_record(_ANCHOR, 200.0), base_dir=base)
        latest = reader.get_latest_price("AAPL", base_dir=base)
        assert latest["date"] == _ANCHOR
        assert latest["close"] == 200.0

    def test_lowercase_symbol_is_normalized(self, tmp_path):
        base = str(tmp_path)
        fetcher._append_daily_record("AAPL", _make_price_record(_ANCHOR, 200.0), base_dir=base)
        assert reader.get_latest_price("aapl", base_dir=base) is not None


class TestGetPriceSeries:
    def test_missing_symbol_returns_empty_list(self, tmp_path):
        assert reader.get_price_series("NOPE", days=10, base_dir=str(tmp_path)) == []

    def test_zero_or_negative_days_returns_empty_list(self, tmp_path):
        base = str(tmp_path)
        fetcher._append_daily_record("AAPL", _make_price_record(_ANCHOR, 200.0), base_dir=base)
        assert reader.get_price_series("AAPL", days=0, base_dir=base) == []
        assert reader.get_price_series("AAPL", days=-5, base_dir=base) == []

    def test_no_gap_series_matches_expected_trading_days(self, tmp_path):
        base = str(tmp_path)
        expected_dates = _seed_no_gap_series(base, "AAPL", 30)
        series = reader.get_price_series("AAPL", days=30, base_dir=base)
        assert len(series) == 30
        assert [r["date"] for r in series] == expected_dates
        assert all(r["_gap"] is False for r in series)

    def test_missing_trading_day_is_flagged_as_gap(self, tmp_path):
        base = str(tmp_path)
        expected_dates = _seed_no_gap_series(base, "AAPL", 30)
        removed_date = expected_dates[15]

        # 該当日のレコードを削除して欠損を意図的に作る
        path = os.path.join(base, "daily", "AAPL.json")
        payload = fetcher._load_json(path, default={"records": []})
        payload["records"] = [r for r in payload["records"] if r["date"] != removed_date]
        fetcher._atomic_write_json(path, payload)

        series = reader.get_price_series("AAPL", days=30, base_dir=base)
        assert len(series) == 30
        gap_dates = [r["date"] for r in series if r["_gap"]]
        assert gap_dates == [removed_date]
        gap_row = [r for r in series if r["date"] == removed_date][0]
        assert gap_row.get("close") is None

    def test_only_latest_available_date_used_as_anchor(self, tmp_path):
        """複数日の記録があっても、直近保存日を末尾とする窓で切り出すこと"""
        base = str(tmp_path)
        fetcher._append_daily_record("AAPL", _make_price_record("2026-07-01", 100.0), base_dir=base)
        fetcher._append_daily_record("AAPL", _make_price_record(_ANCHOR, 200.0), base_dir=base)
        series = reader.get_price_series("AAPL", days=5, base_dir=base)
        assert series[-1]["date"] == _ANCHOR
        assert series[-1]["close"] == 200.0


class TestGetMaDeviation:
    def test_missing_symbol_returns_none(self, tmp_path):
        assert reader.get_ma_deviation("NOPE", window=50, base_dir=str(tmp_path)) is None

    def test_insufficient_history_returns_none(self, tmp_path):
        base = str(tmp_path)
        _seed_no_gap_series(base, "AAPL", 10)
        assert reader.get_ma_deviation("AAPL", window=50, base_dir=base) is None

    def test_correct_value_when_window_fully_satisfied(self, tmp_path):
        base = str(tmp_path)
        _seed_no_gap_series(base, "AAPL", 30)
        deviation = reader.get_ma_deviation("AAPL", window=30, base_dir=base)
        closes = [100.0 + i for i in range(30)]
        expected_ma = sum(closes) / 30
        expected_deviation = (closes[-1] - expected_ma) / expected_ma * 100.0
        assert deviation == expected_deviation

    def test_gap_within_window_returns_none(self, tmp_path):
        base = str(tmp_path)
        expected_dates = _seed_no_gap_series(base, "AAPL", 30)
        removed_date = expected_dates[10]
        path = os.path.join(base, "daily", "AAPL.json")
        payload = fetcher._load_json(path, default={"records": []})
        payload["records"] = [r for r in payload["records"] if r["date"] != removed_date]
        fetcher._atomic_write_json(path, payload)
        assert reader.get_ma_deviation("AAPL", window=30, base_dir=base) is None


class TestGetAttributes:
    def test_missing_symbol_returns_none(self, tmp_path):
        assert reader.get_attributes("NOPE", base_dir=str(tmp_path)) is None

    def test_present_record_returned_with_symbol(self, tmp_path):
        base = str(tmp_path)
        path = os.path.join(base, "attributes", "AAPL.json")
        fetcher._atomic_write_json(path, {
            "fetched_at": "2026-08-10T00:00:00+00:00", "trailing_pe": 30.0, "beta": 1.1,
        })
        attrs = reader.get_attributes("AAPL", base_dir=base)
        assert attrs["symbol"] == "AAPL"
        assert attrs["trailing_pe"] == 30.0


class TestGetCalendar:
    def test_missing_symbol_returns_empty_dict(self, tmp_path):
        assert reader.get_calendar("NOPE", base_dir=str(tmp_path)) == {}

    def test_attributes_without_calendar_key_returns_empty_dict(self, tmp_path):
        """fetcher.pyは現時点でcalendarを取得しないため常に空dict
        （BACKLOG設計:「fetcher.py側で取得済みの場合、なければ空dict」）"""
        base = str(tmp_path)
        path = os.path.join(base, "attributes", "AAPL.json")
        fetcher._atomic_write_json(path, {"fetched_at": "2026-08-10T00:00:00+00:00"})
        assert reader.get_calendar("AAPL", base_dir=base) == {}

    def test_future_calendar_key_is_surfaced_when_present(self, tmp_path):
        base = str(tmp_path)
        path = os.path.join(base, "attributes", "AAPL.json")
        fetcher._atomic_write_json(path, {
            "fetched_at": "2026-08-10T00:00:00+00:00",
            "calendar": {"next_earnings_date": "2026-10-30"},
        })
        assert reader.get_calendar("AAPL", base_dir=base) == {"next_earnings_date": "2026-10-30"}


class TestGetAnalystEvents:
    def test_missing_symbol_returns_empty_list(self, tmp_path):
        assert reader.get_analyst_events("NOPE", base_dir=str(tmp_path)) == []

    def test_all_events_returned_without_since(self, tmp_path):
        base = str(tmp_path)
        path = os.path.join(base, "analyst_history", "AAPL.json")
        fetcher._atomic_write_json(path, {"events": [
            {"date": "2026-08-01", "firm": "A"}, {"date": "2026-07-01", "firm": "B"},
        ]})
        events = reader.get_analyst_events("AAPL", base_dir=base)
        assert len(events) == 2

    def test_since_filters_older_events(self, tmp_path):
        base = str(tmp_path)
        path = os.path.join(base, "analyst_history", "AAPL.json")
        fetcher._atomic_write_json(path, {"events": [
            {"date": "2026-08-01", "firm": "A"}, {"date": "2026-07-01", "firm": "B"},
        ]})
        events = reader.get_analyst_events("AAPL", since="2026-07-15", base_dir=base)
        assert len(events) == 1
        assert events[0]["firm"] == "A"

    def test_since_accepts_date_object(self, tmp_path):
        import datetime
        base = str(tmp_path)
        path = os.path.join(base, "analyst_history", "AAPL.json")
        fetcher._atomic_write_json(path, {"events": [
            {"date": "2026-08-01", "firm": "A"}, {"date": "2026-07-01", "firm": "B"},
        ]})
        events = reader.get_analyst_events("AAPL", since=datetime.date(2026, 7, 15), base_dir=base)
        assert len(events) == 1


class TestGetIndexSeries:
    def test_aliases_get_price_series(self, tmp_path):
        base = str(tmp_path)
        _seed_no_gap_series(base, "^GSPC", 10)
        assert reader.get_index_series("^GSPC", days=10, base_dir=base) == \
            reader.get_price_series("^GSPC", days=10, base_dir=base)

    def test_missing_symbol_returns_empty_list(self, tmp_path):
        assert reader.get_index_series("^NOPE", days=10, base_dir=str(tmp_path)) == []


class TestGetSp500ConstituentsPrices:
    def test_only_symbols_with_data_are_included(self, tmp_path):
        base = str(tmp_path)
        fetcher._append_daily_record("AAPL", _make_price_record(_ANCHOR, 200.0), base_dir=base)
        result = reader.get_sp500_constituents_prices(symbols=["AAPL", "MSFT"], base_dir=base)
        assert list(result.keys()) == ["AAPL"]
        assert result["AAPL"]["close"] == 200.0

    def test_empty_symbol_list_returns_empty_dict(self, tmp_path):
        assert reader.get_sp500_constituents_prices(symbols=[], base_dir=str(tmp_path)) == {}


class TestErrorResilienceForNeverFetchedSymbol:
    """fetcher.py未実行の銘柄に対する全API呼び出しが例外を投げないことを確認"""

    def test_all_apis_return_empty_values_not_raise(self, tmp_path):
        base = str(tmp_path)
        assert reader.get_latest_price("GHOST", base_dir=base) is None
        assert reader.get_price_series("GHOST", days=30, base_dir=base) == []
        assert reader.get_ma_deviation("GHOST", window=50, base_dir=base) is None
        assert reader.get_attributes("GHOST", base_dir=base) is None
        assert reader.get_analyst_events("GHOST", base_dir=base) == []
        assert reader.get_calendar("GHOST", base_dir=base) == {}
        assert reader.get_index_series("GHOST", days=30, base_dir=base) == []
        assert reader.get_sp500_constituents_prices(symbols=["GHOST"], base_dir=base) == {}
