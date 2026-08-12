"""
tests/test_macro_pulse_logic.py

MACRO PULSE (src/market/macro_pulse/05_main.py, 05_audit.py) のユニットテスト。
MACRO-NFP-1:
  ① NFP「水準」→「前月比」変換ロジック
  ② 同一FRED観測値の重複書き込み防止ロジック
  ③ 軽量整合性チェックスクリプト
を検証する。

実行方法:
    python -m pytest tests/test_macro_pulse_logic.py -v
"""

import importlib.util
import os
import pathlib
from datetime import date

import pandas as pd
import pytest

_MACRO_DIR = pathlib.Path(__file__).resolve().parent.parent / "src" / "market" / "macro_pulse"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _MACRO_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


main05 = _load_module("main05_test", "05_main.py")
audit05 = _load_module("audit05_test", "05_audit.py")


# ─────────────────────────────────────────────────────────────────
#  ① fred_latest_with_prev / fred_latest
#  MACRODATA-LAYER-CONSTRUCTION-1本番消費者切替（2026-08-12）:
#  common.macro_data.reader経由に切替たため、fredapiの偽クライアントでは
#  なくmain05._md_reader.get_series()/get_latest()をmonkeypatchする。
# ─────────────────────────────────────────────────────────────────
def _records(pairs):
    """[(date_str, value), ...] からcommon.macro_data.reader.get_series()
    が返すレコード形式（観測日昇順のdictリスト）を作る。"""
    return [
        {"value": v, "as_of": d, "fetched_at": "2026-01-01T00:00:00+09:00",
         "source": "FRED", "source_detail": "series=TEST"}
        for d, v in pairs
    ]


class TestFredLatestWithPrev:
    def test_returns_latest_and_prev(self, monkeypatch):
        records = _records([("2026-04-01", 158736.0), ("2026-05-01", 159001.0)])
        monkeypatch.setattr(main05._md_reader, "get_series", lambda series_id, **kw: records)
        val_now, d_now, val_prev, d_prev = main05.fred_latest_with_prev("PAYEMS")
        assert val_now == 159001.0
        assert val_prev == 158736.0
        assert d_now == date(2026, 5, 1)
        assert d_prev == date(2026, 4, 1)

    def test_single_observation_returns_none_prev(self, monkeypatch):
        records = _records([("2026-05-01", 159001.0)])
        monkeypatch.setattr(main05._md_reader, "get_series", lambda series_id, **kw: records)
        val_now, d_now, val_prev, d_prev = main05.fred_latest_with_prev("PAYEMS")
        assert val_now == 159001.0
        assert val_prev is None
        assert d_prev is None

    def test_empty_series_returns_all_none(self, monkeypatch):
        monkeypatch.setattr(main05._md_reader, "get_series", lambda series_id, **kw: [])
        result = main05.fred_latest_with_prev("PAYEMS")
        assert result == (None, None, None, None)


# ─────────────────────────────────────────────────────────────────
#  ① fetch_event_row: NFPは前月比(人)に変換して格納する
# ─────────────────────────────────────────────────────────────────
class TestFetchEventRowNFPDiff:
    def test_nfp_actual_is_diff_times_1000(self, monkeypatch):
        records = _records([("2026-04-01", 158736.0), ("2026-05-01", 159001.0)])
        monkeypatch.setattr(main05._md_reader, "get_series", lambda series_id, **kw: records)
        row = main05.fetch_event_row(
            "NFP", date(2026, 5, 20),
            fin_ctx={}, schedule=pd.DataFrame(columns=main05.SCHEDULE_COLUMNS),
            events=pd.DataFrame(columns=main05.EVENTS_COLUMNS),
        )
        # (159001.0 - 158736.0) * 1000 = 265000
        assert row["actual"] == "265000"
        assert row["release_date"] == "2026-05-01"

    def test_nfp_actual_can_be_negative(self, monkeypatch):
        records = _records([("2026-04-01", 159001.0), ("2026-05-01", 158984.0)])
        monkeypatch.setattr(main05._md_reader, "get_series", lambda series_id, **kw: records)
        row = main05.fetch_event_row(
            "NFP", date(2026, 5, 20),
            fin_ctx={}, schedule=pd.DataFrame(columns=main05.SCHEDULE_COLUMNS),
            events=pd.DataFrame(columns=main05.EVENTS_COLUMNS),
        )
        assert row["actual"] == "-17000"

    def test_nfp_no_prev_leaves_actual_empty(self, monkeypatch):
        records = _records([("2026-05-01", 159001.0)])
        monkeypatch.setattr(main05._md_reader, "get_series", lambda series_id, **kw: records)
        row = main05.fetch_event_row(
            "NFP", date(2026, 5, 20),
            fin_ctx={}, schedule=pd.DataFrame(columns=main05.SCHEDULE_COLUMNS),
            events=pd.DataFrame(columns=main05.EVENTS_COLUMNS),
        )
        assert row["actual"] == ""

    def test_non_nfp_indicator_still_uses_raw_level(self, monkeypatch):
        # 非NFPはfred_latest()＝reader.get_latest()経由（末尾の1件のみ使用）
        monkeypatch.setattr(
            main05._md_reader, "get_latest",
            lambda series_id, **kw: {"value": 1420.0, "as_of": "2026-05-01"},
        )
        row = main05.fetch_event_row(
            "Building Permits", date(2026, 5, 20),
            fin_ctx={}, schedule=pd.DataFrame(columns=main05.SCHEDULE_COLUMNS),
            events=pd.DataFrame(columns=main05.EVENTS_COLUMNS),
        )
        assert row["actual"] == "1420.0"


# ─────────────────────────────────────────────────────────────────
#  ② dedupe_new_rows: 同一FRED観測値の重複書き込み防止
# ─────────────────────────────────────────────────────────────────
class TestDedupeNewRows:
    def _row(self, indicator, release_date, actual, event_id=None):
        r = {c: "" for c in main05.EVENTS_COLUMNS}
        r.update({
            "indicator": indicator,
            "release_date": release_date,
            "actual": actual,
            "event_id": event_id or f"{indicator}_{release_date}",
        })
        return r

    def test_duplicate_within_lag_window_is_dropped(self):
        rows = [
            self._row("NFP", "2026-06-01", "158984.0"),
            self._row("NFP", "2026-07-02", "158984.0"),  # 同一観測値・lag(35日)以内
        ]
        kept = main05.dedupe_new_rows(rows, pd.DataFrame(columns=main05.EVENTS_COLUMNS))
        assert len(kept) == 1
        assert kept[0]["event_id"] == "NFP_2026-06-01"

    def test_different_values_are_both_kept(self):
        rows = [
            self._row("NFP", "2026-06-01", "158984.0"),
            self._row("NFP", "2026-07-02", "159200.0"),
        ]
        kept = main05.dedupe_new_rows(rows, pd.DataFrame(columns=main05.EVENTS_COLUMNS))
        assert len(kept) == 2

    def test_dedup_against_existing_events(self):
        existing = pd.DataFrame([{
            **{c: "" for c in main05.EVENTS_COLUMNS},
            "indicator": "NFP", "release_date": "2026-06-01",
            "actual": "158984.0", "event_id": "nfp_2026-06-01",
        }])
        rows = [self._row("NFP", "2026-07-02", "158984.0")]
        kept = main05.dedupe_new_rows(rows, existing)
        assert kept == []

    def test_outside_lag_window_not_treated_as_duplicate(self):
        rows = [
            self._row("Initial Claims 4W MA", "2026-01-01", "210000.0"),
            self._row("Initial Claims 4W MA", "2026-06-01", "210000.0"),  # lag=7日を大きく超える
        ]
        kept = main05.dedupe_new_rows(rows, pd.DataFrame(columns=main05.EVENTS_COLUMNS))
        assert len(kept) == 2

    def test_regression_building_permits_duplicate_across_runs(self):
        """
        実際に発生した重複(permit_2026-03-01 と permit_2026-03-17、
        共に1363.0、lag=47日以内)を再現し、2回目の書き込みが弾かれることを確認する。
        """
        existing = pd.DataFrame([{
            **{c: "" for c in main05.EVENTS_COLUMNS},
            "indicator": "Building Permits", "release_date": "2026-03-01",
            "actual": "1363.0", "event_id": "permit_2026-03-01",
        }])
        new_row = self._row("Building Permits", "2026-03-17", "1363.0", event_id="permit_2026-03-17")
        kept = main05.dedupe_new_rows([new_row], existing)
        assert kept == []

    def test_regression_michigan_sentiment_duplicate_across_runs(self):
        """
        実際に発生した重複(mich_sent_2026-03-01 と mich_sent_2026-03-13、
        共に53.3、lag=10日以内)を再現し、2回目の書き込みが弾かれることを確認する。
        """
        existing = pd.DataFrame([{
            **{c: "" for c in main05.EVENTS_COLUMNS},
            "indicator": "Michigan Consumer Sentiment", "release_date": "2026-03-01",
            "actual": "53.3", "event_id": "mich_sent_2026-03-01",
        }])
        new_row = self._row("Michigan Consumer Sentiment", "2026-03-13", "53.3", event_id="mich_sent_2026-03-13")
        kept = main05.dedupe_new_rows([new_row], existing)
        assert kept == []


# ─────────────────────────────────────────────────────────────────
#  ③ 05_audit.py: 軽量整合性チェック
# ─────────────────────────────────────────────────────────────────
class TestAuditNFPLevelResidue:
    def _events_df(self, nfp_vals_by_date):
        rows = []
        for d, v in nfp_vals_by_date:
            row = {c: "" for c in main05.EVENTS_COLUMNS}
            row.update({"indicator": "NFP", "release_date": d, "actual": str(v),
                        "event_id": f"nfp_{d}"})
            rows.append(row)
        return pd.DataFrame(rows)

    def test_flags_narrow_band_level_residue(self):
        events = self._events_df([
            ("2026-02-01", 158637.0), ("2026-03-01", 158736.0),
            ("2026-04-01", 159001.0), ("2026-05-01", 159001.0),
            ("2026-06-01", 158984.0), ("2026-07-01", 158984.0),
        ])
        ng, warn = audit05.check_nfp_level_residue(events)
        assert len(ng) == 1

    def test_does_not_flag_genuine_month_over_month_diffs(self):
        # 前月比なら大きく振れる（数万〜十数万・符号も反転しうる）のが正常
        events = self._events_df([
            ("2026-02-01", 180000.0), ("2026-03-01", 210000.0),
            ("2026-04-01", -20000.0), ("2026-05-01", 265000.0),
            ("2026-06-01", 150000.0), ("2026-07-01", 300000.0),
        ])
        ng, warn = audit05.check_nfp_level_residue(events)
        assert ng == []

    def test_insufficient_history_no_flag(self):
        events = self._events_df([("2026-06-01", 158984.0), ("2026-07-01", 158984.0)])
        ng, warn = audit05.check_nfp_level_residue(events)
        assert ng == []


class TestAuditDuplicateEvents:
    def test_flags_duplicate_within_risk_indicators_only(self):
        events = pd.DataFrame([
            {**{c: "" for c in main05.EVENTS_COLUMNS},
             "indicator": "NFP", "release_date": "2026-06-01", "actual": "158984.0",
             "event_id": "nfp_2026-06-01"},
            {**{c: "" for c in main05.EVENTS_COLUMNS},
             "indicator": "NFP", "release_date": "2026-07-02", "actual": "158984.0",
             "event_id": "nfp_2026-07-02"},
        ])
        schedule = pd.DataFrame([{"indicator": "NFP", "release_date": "2026-07-02"}])
        ng, warn = audit05.check_duplicate_events(events, schedule)
        assert ng == []
        assert len(warn) == 1

    def test_non_risk_indicator_not_flagged(self):
        # Sahm Ruleはscheduleに登録されていないため対象外（正常な横ばいをNG化しない）
        events = pd.DataFrame([
            {**{c: "" for c in main05.EVENTS_COLUMNS},
             "indicator": "Sahm Rule Recession Indicator", "release_date": "2026-01-01",
             "actual": "-0.1", "event_id": "sahm_rule_2026-01-01"},
            {**{c: "" for c in main05.EVENTS_COLUMNS},
             "indicator": "Sahm Rule Recession Indicator", "release_date": "2026-02-01",
             "actual": "-0.1", "event_id": "sahm_rule_2026-02-01"},
        ])
        schedule = pd.DataFrame(columns=["indicator", "release_date"])
        ng, warn = audit05.check_duplicate_events(events, schedule)
        assert ng == [] and warn == []


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
