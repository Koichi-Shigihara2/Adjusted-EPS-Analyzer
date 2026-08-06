"""
tests/test_layer3_accessor_wrappers.py

移行実装計画（SEC_EDGAR_LAYER_DESIGN.md 8章）フェーズD Step1対応。

layer3_builder.py::get_quarterly_series() / get_latest_quarterly() の
単体テスト。reader.py側（normalized/経由）の対応するテストクラス
（tests/test_gate2_phase3b1_reader_integration.py::TestGetQuarterlySeries /
TestGetLatestQuarterly）とフィルタ条件・ソート順の挙動が同一であることを
確認する（第一引数の形だけがnormalized dictからLayer3 store dictに
変わる）。

この段階では新規追加のみで、既存normalized/経由の消費者（5系統）は
一切変更しない。
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from common.sec_data.layer3_builder import (  # noqa: E402
    get_field_entries,
    get_quarterly_series,
    get_latest_quarterly,
)


def _make_store(field_name: str, entries: list) -> dict:
    """build_ticker_store()の戻り値と同じshapeの合成storeを作る。"""
    return {
        "ticker": "TEST",
        "fields": {
            field_name: {
                "source_tag": "TestConcept",
                "category": "flow",
                "entries": entries,
            }
        },
    }


class TestGetFieldEntries:
    def test_returns_entries_list(self):
        store = _make_store("revenue", [{"end": "2024-03-31", "val": 100}])
        assert get_field_entries(store, "revenue") == [{"end": "2024-03-31", "val": 100}]

    def test_missing_field_returns_empty_list(self):
        assert get_field_entries({"fields": {}}, "revenue") == []
        assert get_field_entries({}, "revenue") == []


class TestGetQuarterlySeries:
    def test_excludes_annual_and_ytd(self):
        store = _make_store("revenue", [
            {"end": "2024-03-31", "val": 100, "is_annual": False, "is_ytd": False},
            {"end": "2024-12-31", "val": 400, "is_annual": True,  "is_ytd": False},
            {"end": "2024-06-30", "val": 999, "is_annual": False, "is_ytd": True},
            {"end": "2024-06-30", "val": 110, "is_annual": False, "is_ytd": False},
        ])
        result = get_quarterly_series(store, "revenue")
        assert [e["val"] for e in result] == [100, 110]

    def test_sorts_by_end_ascending(self):
        store = _make_store("revenue", [
            {"end": "2024-09-30", "val": 3, "is_annual": False, "is_ytd": False},
            {"end": "2024-03-31", "val": 1, "is_annual": False, "is_ytd": False},
            {"end": "2024-06-30", "val": 2, "is_annual": False, "is_ytd": False},
        ])
        result = get_quarterly_series(store, "revenue")
        assert [e["end"] for e in result] == ["2024-03-31", "2024-06-30", "2024-09-30"]

    def test_missing_field_returns_empty_list(self):
        assert get_quarterly_series({"fields": {}}, "revenue") == []
        assert get_quarterly_series({}, "revenue") == []

    def test_source_tag_field_ignored_by_filter(self):
        """Layer3 entriesにのみ存在するsource_tag等の追加キーがあっても
        フィルタ・ソートに影響しないことを確認（normalized/にはない
        キーだが、entries自体の互換性を壊さないことの回帰確認）。"""
        store = _make_store("revenue", [
            {"end": "2024-03-31", "val": 100, "is_annual": False, "is_ytd": False,
             "source_tag": "RevenueFromContractWithCustomerExcludingAssessedTax"},
        ])
        result = get_quarterly_series(store, "revenue")
        assert [e["val"] for e in result] == [100]


class TestGetLatestQuarterly:
    def test_returns_last_entry_by_end(self):
        store = _make_store("net_income", [
            {"end": "2024-03-31", "val": 1, "is_annual": False, "is_ytd": False},
            {"end": "2024-09-30", "val": 3, "is_annual": False, "is_ytd": False},
            {"end": "2024-06-30", "val": 2, "is_annual": False, "is_ytd": False},
        ])
        latest = get_latest_quarterly(store, "net_income")
        assert latest["val"] == 3
        assert latest["end"] == "2024-09-30"

    def test_empty_series_returns_none(self):
        assert get_latest_quarterly({"fields": {}}, "net_income") is None
        assert get_latest_quarterly({}, "net_income") is None
