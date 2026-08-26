"""
tests/test_collect_and_send_market_data_switch.py

[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序4-6（collect_and_send.py切替）
の回帰テスト。fetch_hist()（yfinance直接呼び出し）のcommon.market_data.
reader経由への置き換え（fetch_recent_records()新設・format_line()の入力
形式変更・_get_sp500_ma_deviation()/fetch_qqq_tech_data()の再実装）を
検証する。

src/market/market_pulse/collect_and_send.pyは他の切替済みファイル
（beta_fetcher.py等）と同じくトップレベルパッケージに属さない独立
ディレクトリのスクリプトのため、sys.path追加による直接importで読む
（pipeline.py用テストと同型のパターン）。

実行方法:
    python -m pytest tests/test_collect_and_send_market_data_switch.py -v
"""

import os
import sys

import pytest

_MARKET_PULSE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "market", "market_pulse")
)
if _MARKET_PULSE_DIR not in sys.path:
    sys.path.insert(0, _MARKET_PULSE_DIR)

import collect_and_send as cs  # noqa: E402


def _patch_price_series(monkeypatch, series_map, has_market_data=True):
    """ticker→レコードリストのdictを渡し、_md_get_price_series()をmockする"""
    monkeypatch.setattr(cs, "HAS_MARKET_DATA", has_market_data)
    monkeypatch.setattr(cs, "_md_get_price_series", lambda ticker, days: series_map.get(ticker, []))


def _patch_ma_deviation(monkeypatch, dev_map):
    monkeypatch.setattr(cs, "_md_get_ma_deviation", lambda ticker, window: dev_map.get((ticker, window)))


class TestFetchRecentRecords:
    def test_returns_last_two_real_closes(self, monkeypatch):
        _patch_price_series(monkeypatch, {"XYZ": [
            {"date": "2026-08-06", "close": 100.0, "volume": 1000, "_gap": False},
            {"date": "2026-08-07", "close": 105.0, "volume": 1100, "_gap": False},
        ]})
        result = cs.fetch_recent_records("XYZ")
        assert len(result) == 2
        assert result[-1]["close"] == 105.0

    def test_ignores_gap_placeholders(self, monkeypatch):
        """単発の営業日欠損（_gap: True）を除外し、実データの末尾count件を使う"""
        _patch_price_series(monkeypatch, {"XYZ": [
            {"date": "2026-08-04", "close": 100.0, "volume": 1000, "_gap": False},
            {"date": "2026-08-05", "close": 999.0, "_gap": True},
            {"date": "2026-08-06", "close": 110.0, "volume": 1200, "_gap": False},
            {"date": "2026-08-07", "close": 121.0, "volume": 1300, "_gap": False},
        ]})
        result = cs.fetch_recent_records("XYZ")
        assert [r["close"] for r in result] == [110.0, 121.0]

    def test_insufficient_real_data_returns_none(self, monkeypatch):
        _patch_price_series(monkeypatch, {"XYZ": [
            {"date": "2026-08-07", "close": 100.0, "volume": 1000, "_gap": False},
        ]})
        assert cs.fetch_recent_records("XYZ") is None

    def test_empty_series_returns_none(self, monkeypatch):
        _patch_price_series(monkeypatch, {"XYZ": []})
        assert cs.fetch_recent_records("XYZ") is None

    def test_market_data_unavailable_returns_none(self, monkeypatch):
        _patch_price_series(monkeypatch, {}, has_market_data=False)
        assert cs.fetch_recent_records("XYZ") is None

    def test_unexpected_exception_returns_none(self, monkeypatch):
        def _raise(ticker, days):
            raise RuntimeError("simulated failure")
        monkeypatch.setattr(cs, "HAS_MARKET_DATA", True)
        monkeypatch.setattr(cs, "_md_get_price_series", _raise)
        assert cs.fetch_recent_records("XYZ") is None

    def test_custom_count_requests_more_records(self, monkeypatch):
        _patch_price_series(monkeypatch, {"XYZ": [
            {"date": f"2026-08-{d:02d}", "close": float(d), "volume": 100, "_gap": False}
            for d in range(1, 6)
        ]})
        result = cs.fetch_recent_records("XYZ", count=3, days=10)
        assert [r["close"] for r in result] == [3.0, 4.0, 5.0]


class TestFormatLine:
    def test_none_records_shows_restricted_message(self):
        assert "取得制限あり" in cs.format_line("テスト", None)

    def test_normal_case_shows_value_and_change(self):
        records = [
            {"date": "2026-08-06", "close": 100.0, "volume": 1000},
            {"date": "2026-08-07", "close": 105.0, "volume": 1100},
        ]
        line = cs.format_line("テスト", records)
        assert "105.00" in line
        assert "+5.00" in line
        assert "+5.00%" in line
        assert "08/07" in line

    def test_volume_ratio_included_when_both_positive(self):
        records = [
            {"date": "2026-08-06", "close": 100.0, "volume": 1000},
            {"date": "2026-08-07", "close": 105.0, "volume": 2000},
        ]
        line = cs.format_line("テスト", records)
        assert "前日比出来高比:2.00" in line

    def test_single_record_shows_no_diff(self):
        records = [{"date": "2026-08-07", "close": 100.0, "volume": 1000}]
        line = cs.format_line("テスト", records)
        assert "100.00" in line
        assert "+0.00 (+0.00%)" in line


class TestGetSp500MaDeviation:
    def test_normal_case_computed_correctly(self, monkeypatch):
        _patch_ma_deviation(monkeypatch, {("^GSPC", 50): 3.4, ("^GSPC", 200): 2.0})
        _patch_price_series(monkeypatch, {"^GSPC": [
            {"date": f"day{i}", "close": 100.0 + i * 0.1, "_gap": False} for i in range(220)
        ]})
        result = cs._get_sp500_ma_deviation()
        assert result["deviation_50"] == 3.4
        assert result["above_ma200"] is True

    def test_above_ma200_false_when_deviation_negative(self, monkeypatch):
        _patch_ma_deviation(monkeypatch, {("^GSPC", 50): -1.0, ("^GSPC", 200): -2.0})
        _patch_price_series(monkeypatch, {"^GSPC": [
            {"date": f"day{i}", "close": 100.0, "_gap": False} for i in range(220)
        ]})
        result = cs._get_sp500_ma_deviation()
        assert result["above_ma200"] is False

    def test_ma200_slope_true_when_recent_ma_higher(self, monkeypatch):
        """直近200日平均 > 10日前時点の200日平均 → slope=True"""
        _patch_ma_deviation(monkeypatch, {("^GSPC", 50): 1.0, ("^GSPC", 200): 1.0})
        # 単調増加系列: 直近window(-200:)の平均は必ず10日前window(-210:-10)の平均を上回る
        closes = [{"date": f"day{i}", "close": float(i), "_gap": False} for i in range(220)]
        _patch_price_series(monkeypatch, {"^GSPC": closes})
        result = cs._get_sp500_ma_deviation()
        assert result["ma200_slope"] is True

    def test_insufficient_history_returns_none_deviation(self, monkeypatch):
        _patch_ma_deviation(monkeypatch, {("^GSPC", 50): None, ("^GSPC", 200): None})
        _patch_price_series(monkeypatch, {"^GSPC": []})
        assert cs._get_sp500_ma_deviation() is None

    def test_market_data_unavailable_returns_none(self, monkeypatch):
        monkeypatch.setattr(cs, "HAS_MARKET_DATA", False)
        assert cs._get_sp500_ma_deviation() is None

    def test_short_series_yields_none_slope(self, monkeypatch):
        """window=220未満（210件未満）ではma200_slopeがNoneになる"""
        _patch_ma_deviation(monkeypatch, {("^GSPC", 50): 3.4, ("^GSPC", 200): 2.0})
        _patch_price_series(monkeypatch, {"^GSPC": [
            {"date": f"day{i}", "close": 100.0, "_gap": False} for i in range(100)
        ]})
        result = cs._get_sp500_ma_deviation()
        assert result["ma200_slope"] is None


class TestFetchQqqTechData:
    def test_normal_case_computed_correctly(self, monkeypatch):
        _patch_ma_deviation(monkeypatch, {("QQQ", 125): 8.11})
        qqq_series = [{"date": f"day{i}", "close": 100.0 + i, "_gap": False} for i in range(25)]
        spy_series = [{"date": f"day{i}", "close": 200.0 + i * 0.5, "_gap": False} for i in range(25)]
        _patch_price_series(monkeypatch, {"QQQ": qqq_series, "SPY": spy_series})
        qqq_vs_ma125, qqq_vs_spy_20d = cs.fetch_qqq_tech_data()
        assert qqq_vs_ma125 == 8.11
        assert qqq_vs_spy_20d is not None

    def test_missing_ma125_returns_none_tuple(self, monkeypatch):
        _patch_ma_deviation(monkeypatch, {("QQQ", 125): None})
        _patch_price_series(monkeypatch, {"QQQ": [], "SPY": []})
        assert cs.fetch_qqq_tech_data() == (None, None)

    def test_market_data_unavailable_returns_none_tuple(self, monkeypatch):
        monkeypatch.setattr(cs, "HAS_MARKET_DATA", False)
        assert cs.fetch_qqq_tech_data() == (None, None)

    def test_insufficient_20d_series_leaves_spy_diff_none(self, monkeypatch):
        _patch_ma_deviation(monkeypatch, {("QQQ", 125): 5.0})
        _patch_price_series(monkeypatch, {
            "QQQ": [{"date": "d1", "close": 100.0, "_gap": False}],
            "SPY": [{"date": "d1", "close": 200.0, "_gap": False}],
        })
        qqq_vs_ma125, qqq_vs_spy_20d = cs.fetch_qqq_tech_data()
        assert qqq_vs_ma125 == 5.0
        assert qqq_vs_spy_20d is None


class TestLoadDivHistory:
    """[[MARKETPULSE-MINOR-INCONSISTENCIES-1]]⑤対応: _load_div_history()の
    フォールバックがCNN由来（fear_greed.score）を使い、feargreedchart.com由来
    （tech_pulse.components.fg_score）を使わないことを検証する回帰テスト。
    """

    def _write_json(self, tmp_path, entries):
        import json
        path = tmp_path / "market_data.json"
        path.write_text(json.dumps(entries), encoding="utf-8")
        return str(path)

    def _recent_date(self, days_ago=1):
        from datetime import datetime, timedelta, timezone
        return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

    def test_uses_stored_divergence_value_when_present(self, tmp_path):
        entries = [{
            "date": self._recent_date(1),
            "tech_pulse": {"score": 70, "divergence": {"value": 12.3}},
        }]
        path = self._write_json(tmp_path, entries)
        assert cs._load_div_history(path, window=90) == [12.3]

    def test_fallback_uses_cnn_score_not_feargreedchart_score(self, tmp_path):
        """divergence.value欠損時、fear_greed.score（CNN）を使い、
        tech_pulse.components.fg_score（feargreedchart.com）は使わないこと。
        CNN=30・feargreedchart.com=57のように大きく異なる値を与え、
        混入していれば誤った期待値になるよう設計する。
        """
        entries = [{
            "date": self._recent_date(2),
            "tech_pulse": {
                "score": 72,
                "components": {"fg_score": 57},  # feargreedchart.com（使われてはいけない）
                # divergence未記録（旧エントリを再現）
            },
            "fear_greed": {"score": 30},  # CNN（使われるべき）
        }]
        path = self._write_json(tmp_path, entries)
        result = cs._load_div_history(path, window=90)
        assert result == [72 - 30]  # = 42.0
        assert result != [72 - 57]  # feargreedchart.com由来(15.0)ではない

    def test_entry_missing_both_scores_is_skipped(self, tmp_path):
        """tech_pulseブロック自体が丸ごとnull（旧スキーマ）のエントリは、
        フォールバック条件を満たさず完全にスキップされる
        （2026-08-26②で確認した実データの挙動と同じ）。"""
        entries = [
            {"date": self._recent_date(3), "tech_pulse": None, "fear_greed": None},
            {"date": self._recent_date(1), "tech_pulse": {"score": 60, "divergence": {"value": 5.0}}},
        ]
        path = self._write_json(tmp_path, entries)
        assert cs._load_div_history(path, window=90) == [5.0]

    def test_entry_outside_window_excluded(self, tmp_path):
        entries = [
            {"date": self._recent_date(200), "tech_pulse": {"score": 70, "divergence": {"value": 99.0}}},
            {"date": self._recent_date(1), "tech_pulse": {"score": 70, "divergence": {"value": 1.0}}},
        ]
        path = self._write_json(tmp_path, entries)
        assert cs._load_div_history(path, window=90) == [1.0]
