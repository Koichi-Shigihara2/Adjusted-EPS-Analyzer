"""
tests/test_contracts.py

common/sec_data/contracts.py のユニットテスト。
QUALITY-GATES-EPIC-1 Phase 3a（Gate2第一段階: 正規化契約の型導入）。

実行方法:
    python -m pytest tests/test_contracts.py -v
"""

import pytest

from common.sec_data.contracts import (
    ContractViolation,
    EntryProvenance,
    FCFSeries,
    FinancialEntry,
    validate_entries,
    validate_fields,
)


def _entry(**overrides):
    base = {
        "end": "2025-12-31", "start": "2025-10-01", "val": 100.0,
        "accn": "0000000000-00-000000", "fp": "Q4", "fy": 2025,
        "form": "10-Q", "filed": "2026-02-01", "period_days": 91,
        "is_ytd": False, "is_annual": False,
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────
# 規約B: FinancialEntry（quarterly.py標準エントリ形状）
# ─────────────────────────────────────────────

class TestFinancialEntry:
    def test_valid_entry_round_trips(self):
        d = _entry()
        entry = FinancialEntry.from_dict(d)
        assert entry.end == "2025-12-31"
        assert entry.val == 100.0
        assert entry.is_implied is False
        assert entry.anomaly is False
        assert entry.backfilled is False
        assert entry.provenance.is_empty()

    def test_optional_keys_default_false_when_absent(self):
        entry = FinancialEntry.from_dict(_entry())
        assert entry.is_implied is False

    def test_optional_keys_respected_when_present(self):
        entry = FinancialEntry.from_dict(_entry(is_implied=True, anomaly=True, backfilled=True))
        assert entry.is_implied is True
        assert entry.anomaly is True
        assert entry.backfilled is True

    @pytest.mark.parametrize("missing_key", [
        "end", "start", "val", "accn", "fp", "fy", "form", "filed",
        "period_days", "is_ytd", "is_annual",
    ])
    def test_missing_required_key_raises(self, missing_key):
        d = _entry()
        del d[missing_key]
        with pytest.raises(ContractViolation):
            FinancialEntry.from_dict(d)

    def test_non_dict_raises(self):
        with pytest.raises(ContractViolation):
            FinancialEntry.from_dict(["not", "a", "dict"])  # type: ignore[arg-type]

    def test_to_dict_omits_falsy_optional_keys(self):
        entry = FinancialEntry.from_dict(_entry())
        d = entry.to_dict()
        assert "is_implied" not in d
        assert "anomaly" not in d
        assert "backfilled" not in d
        assert "_provenance" not in d

    def test_to_dict_includes_provenance_when_present(self):
        d = _entry(_provenance={"source_tag": "DebtLongtermAndShorttermCombinedAmount"})
        entry = FinancialEntry.from_dict(d)
        out = entry.to_dict()
        assert out["_provenance"] == {"source_tag": "DebtLongtermAndShorttermCombinedAmount"}

    def test_provenance_non_dict_raises(self):
        with pytest.raises(ContractViolation):
            FinancialEntry.from_dict(_entry(_provenance="not-a-dict"))


class TestValidateEntries:
    def test_valid_list_passes(self):
        entries = validate_entries("Revenue", [_entry(), _entry(end="2026-03-31")])
        assert len(entries) == 2

    def test_invalid_entry_error_includes_field_name(self):
        bad = _entry()
        del bad["val"]
        with pytest.raises(ContractViolation, match=r"\[Revenue\]"):
            validate_entries("Revenue", [bad])

    def test_validate_fields_checks_every_field(self):
        fields = {
            "Revenue": [_entry()],
            "LTDebt": [_entry(end="2026-03-31")],
        }
        # 例外が出なければOK
        validate_fields(fields)

    def test_validate_fields_raises_on_any_bad_field(self):
        bad = _entry()
        del bad["fy"]
        fields = {"Revenue": [_entry()], "LTDebt": [bad]}
        with pytest.raises(ContractViolation, match=r"\[LTDebt\]"):
            validate_fields(fields)


# ─────────────────────────────────────────────
# 規約③: EntryProvenance
# ─────────────────────────────────────────────

class TestEntryProvenance:
    def test_empty_by_default(self):
        assert EntryProvenance().is_empty()

    def test_from_dict_none_is_empty(self):
        assert EntryProvenance.from_dict(None).is_empty()

    def test_from_dict_round_trip(self):
        p = EntryProvenance.from_dict({"source_tag": "X", "duration_days": 365})
        assert p.source_tag == "X"
        assert p.duration_days == 365
        assert p.to_dict() == {"source_tag": "X", "duration_days": 365}

    def test_to_dict_partial(self):
        p = EntryProvenance(source_tag="X")
        assert p.to_dict() == {"source_tag": "X"}


# ─────────────────────────────────────────────
# 規約A: FCFSeries（fcf_listの順序規約）
# ─────────────────────────────────────────────

class TestFCFSeries:
    def test_descending_dates_pass(self):
        series = FCFSeries([300.0, 200.0, 100.0],
                            ["2026-03-31", "2025-03-31", "2024-03-31"])
        assert list(series) == [300.0, 200.0, 100.0]

    def test_ascending_dates_raise(self):
        """GROWTH-CAGR-SIGN-1相当の規約違反（順序取り違え）を検知できること"""
        with pytest.raises(ContractViolation, match="新しい順"):
            FCFSeries([100.0, 200.0, 300.0],
                      ["2024-03-31", "2025-03-31", "2026-03-31"])

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ContractViolation):
            FCFSeries([100.0, 200.0], ["2025-03-31"])

    def test_no_dates_skips_validation(self):
        # reader.py::get_fcf_list() のように日付情報が失われている経路向け。
        # 誤った順序を渡しても例外にならない（検証不能なため素通り）。
        series = FCFSeries([100.0, 200.0, 300.0])
        assert list(series) == [100.0, 200.0, 300.0]

    def test_newest_and_oldest(self):
        series = FCFSeries([300.0, 200.0, 100.0],
                            ["2026-03-31", "2025-03-31", "2024-03-31"])
        assert series.newest == 300.0
        assert series.oldest == 100.0

    def test_newest_oldest_empty_series(self):
        series = FCFSeries([])
        assert series.newest is None
        assert series.oldest is None

    def test_newest_n(self):
        series = FCFSeries([500.0, 400.0, 300.0, 200.0, 100.0],
                            ["2026-03-31", "2025-03-31", "2024-03-31",
                             "2023-03-31", "2022-03-31"])
        top3 = series.newest_n(3)
        assert list(top3) == [500.0, 400.0, 300.0]
        assert isinstance(top3, FCFSeries)

    def test_list_like_indexing_and_slicing(self):
        series = FCFSeries([300.0, 200.0, 100.0],
                            ["2026-03-31", "2025-03-31", "2024-03-31"])
        assert series[0] == 300.0
        assert series[-1] == 100.0
        assert series[:2] == [300.0, 200.0]
        assert len(series) == 3
        assert sum(series) == 600.0

    def test_as_list_returns_plain_list(self):
        series = FCFSeries([300.0, 200.0], ["2026-03-31", "2025-03-31"])
        out = series.as_list()
        assert type(out) is list
        assert out == [300.0, 200.0]

    def test_equality_with_plain_list(self):
        series = FCFSeries([300.0, 200.0], ["2026-03-31", "2025-03-31"])
        assert series == [300.0, 200.0]
