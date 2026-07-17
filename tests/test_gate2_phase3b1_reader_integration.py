"""
tests/test_gate2_phase3b1_reader_integration.py

GATE2-PHASE3B-1① 4ファイル統合のテスト。

- reader.py::get_quarterly_series / get_latest_quarterly の単体テスト
- reader.py::get_rpo_context の移行後挙動確認（is_ytd除外の意図的な挙動変化）
- financial_trend_calculator.py / tail_dcf_bridge.py /
  quarterly_review_generator.py / hypecore.py の移行前後の回帰確認
  （移行前の独自実装と等価なフィルタ条件・最新値選択になっているかを
  実データ相当の合成フィクスチャで検証する）
"""

import os
import sys
import json

import pytest

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from common.sec_data.reader import SECReader, get_quarterly_series, get_latest_quarterly  # noqa: E402


# ─────────────────────────────────────────────
# 1. get_quarterly_series / get_latest_quarterly 単体テスト
# ─────────────────────────────────────────────

class TestGetQuarterlySeries:
    def test_excludes_annual_and_ytd(self):
        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2024-03-31", "val": 100, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 400, "is_annual": True,  "is_ytd": False},
                    {"end": "2024-06-30", "val": 999, "is_annual": False, "is_ytd": True},
                    {"end": "2024-06-30", "val": 110, "is_annual": False, "is_ytd": False},
                ]
            }
        }
        result = get_quarterly_series(normalized, "Revenue")
        assert [e["val"] for e in result] == [100, 110]

    def test_sorts_by_end_ascending(self):
        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2024-09-30", "val": 3, "is_annual": False, "is_ytd": False},
                    {"end": "2024-03-31", "val": 1, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 2, "is_annual": False, "is_ytd": False},
                ]
            }
        }
        result = get_quarterly_series(normalized, "Revenue")
        assert [e["end"] for e in result] == ["2024-03-31", "2024-06-30", "2024-09-30"]

    def test_missing_field_returns_empty_list(self):
        assert get_quarterly_series({"fields": {}}, "Revenue") == []
        assert get_quarterly_series({}, "Revenue") == []


class TestGetLatestQuarterly:
    def test_returns_last_entry_by_end(self):
        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2024-03-31", "val": 1, "is_annual": False, "is_ytd": False},
                    {"end": "2024-09-30", "val": 3, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 2, "is_annual": False, "is_ytd": False},
                ]
            }
        }
        latest = get_latest_quarterly(normalized, "Revenue")
        assert latest["end"] == "2024-09-30"
        assert latest["val"] == 3

    def test_empty_series_returns_none(self):
        assert get_latest_quarterly({"fields": {}}, "Revenue") is None
        normalized = {
            "fields": {
                "Revenue": [{"end": "2024-12-31", "val": 400, "is_annual": True, "is_ytd": False}]
            }
        }
        assert get_latest_quarterly(normalized, "Revenue") is None


# ─────────────────────────────────────────────
# 2. get_rpo_context 移行後の挙動確認
#    （②既存_q_sortedはis_annualのみ除外・is_ytd除外なし → get_quarterly_seriesは
#      is_ytdも除外する意図的な挙動変化。現状データでの無害性を確認する）
# ─────────────────────────────────────────────

class TestGetRpoContextAfterMigration:
    def test_ttm_and_yoy_unaffected_by_ytd_exclusion(self, monkeypatch):
        reader = SECReader()
        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2023-03-31", "val": 90,  "is_annual": False, "is_ytd": False},
                    {"end": "2023-06-30", "val": 95,  "is_annual": False, "is_ytd": False},
                    {"end": "2023-09-30", "val": 100, "is_annual": False, "is_ytd": False},
                    {"end": "2023-12-31", "val": 105, "is_annual": False, "is_ytd": False},
                    {"end": "2024-03-31", "val": 100, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 999, "is_annual": False, "is_ytd": True},
                    {"end": "2024-06-30", "val": 110, "is_annual": False, "is_ytd": False},
                    {"end": "2024-09-30", "val": 120, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 130, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 465, "is_annual": True,  "is_ytd": False},
                ],
                "OperatingIncome": [
                    {"end": "2024-03-31", "val": 10, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 11, "is_annual": False, "is_ytd": False},
                    {"end": "2024-09-30", "val": 12, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 13, "is_annual": False, "is_ytd": False},
                ],
                "RPO": [{"end": "2024-12-31", "val": 500, "is_annual": False}],
            }
        }
        monkeypatch.setattr(reader, "_load_json", lambda path: normalized)
        ctx = reader.get_rpo_context("TEST")

        assert ctx["rev_ttm"] == 100 + 110 + 120 + 130
        prior_ttm = 90 + 95 + 100 + 105
        assert ctx["rev_yoy"] == pytest.approx((460 - prior_ttm) / prior_ttm)
        assert ctx["op_margin"] == pytest.approx((10 + 11 + 12 + 13) / 460)

    def test_no_normalized_file_returns_none_defaults(self, monkeypatch):
        reader = SECReader()
        monkeypatch.setattr(reader, "_load_json", lambda path: None)
        ctx = reader.get_rpo_context("NOPE")
        assert ctx == {"rev_yoy": None, "rev_ttm": None, "op_margin": None, "rpo_series": []}


# ─────────────────────────────────────────────
# 3. financial_trend_calculator.py 回帰テスト
# ─────────────────────────────────────────────

_STONKS_SILO_SRC = os.path.join(_REPO_ROOT, "discover", "stonks-silo", "src")
if _STONKS_SILO_SRC not in sys.path:
    sys.path.insert(0, _STONKS_SILO_SRC)
import financial_trend_calculator as ftc  # noqa: E402


class TestFinancialTrendCalculatorRegression:
    def test_get_quarterly_entries_excludes_ytd_and_builds_q4_implied(self):
        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2024-03-31", "start": "2024-01-01", "val": 90,
                     "is_annual": False, "is_ytd": False, "fy": 2024, "filed": "2024-04-01", "accn": "Q1"},
                    {"end": "2024-06-30", "start": "2024-04-01", "val": 95,
                     "is_annual": False, "is_ytd": False, "fy": 2024, "filed": "2024-07-01", "accn": "Q2"},
                    {"end": "2024-09-30", "start": "2024-07-01", "val": 100,
                     "is_annual": False, "is_ytd": False, "fy": 2024, "filed": "2024-10-01", "accn": "Q3"},
                    {"end": "2024-12-31", "start": "2024-01-01", "val": 400,
                     "is_annual": True, "is_ytd": False, "fy": 2024, "filed": "2025-02-01", "accn": "FY"},
                    {"end": "2024-06-30", "start": "2024-01-01", "val": 999,
                     "is_annual": False, "is_ytd": True, "fy": 2024, "filed": "2024-07-01", "accn": "YTD"},
                ]
            }
        }
        entries = ftc._get_quarterly_entries(normalized, "Revenue")
        assert [(e["end"], e["val"]) for e in entries] == [
            ("2024-03-31", 90),
            ("2024-06-30", 95),
            ("2024-09-30", 100),
            ("2024-12-31", 115),  # Q4 implied = 400 - (90+95+100)
        ]
        assert entries[-1]["is_implied"] is True

    def test_get_quarterly_entries_missing_field_returns_empty(self):
        assert ftc._get_quarterly_entries({"fields": {}}, "Revenue") == []


# ─────────────────────────────────────────────
# 4. tail_dcf_bridge.py 回帰テスト
# ─────────────────────────────────────────────

_TAIL_SRC = os.path.join(_REPO_ROOT, "src", "tail")
if _TAIL_SRC not in sys.path:
    sys.path.insert(0, _TAIL_SRC)
import tail_dcf_bridge as tdb  # noqa: E402


class TestTailDcfBridgeRegression:
    def test_load_layer1_financials_uses_latest_quarter_excludes_ytd(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tdb, "COMMON_NORMALIZED_DIR", str(tmp_path))
        monkeypatch.setattr(tdb, "VALUATION_DIR", str(tmp_path))

        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2024-09-30", "val": 160, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 170, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 999, "is_annual": False, "is_ytd": True},
                ],
                "OperatingIncome": [
                    {"end": "2024-09-30", "val": 16, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 17, "is_annual": False, "is_ytd": False},
                ],
                "SBC": [{"end": "2024-12-31", "val": 5, "is_annual": False, "is_ytd": False}],
                "NetIncome": [
                    {"end": "2024-09-30", "val": 14, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 15, "is_annual": False, "is_ytd": False},
                ],
                "SharesDiluted": [{"end": "2024-12-31", "val": 1000, "is_annual": False, "is_ytd": False}],
            }
        }
        (tmp_path / "TEST_quarterly_normalized.json").write_text(
            json.dumps(normalized), encoding="utf-8"
        )

        result = tdb._load_layer1_financials("TEST")
        assert result["operating_margin"] == pytest.approx(0.1)
        assert result["sbc_quarterly"] == 5
        assert result["eps_diluted"] == pytest.approx(0.015)

    def test_load_layer1_financials_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tdb, "COMMON_NORMALIZED_DIR", str(tmp_path))
        monkeypatch.setattr(tdb, "VALUATION_DIR", str(tmp_path))
        assert tdb._load_layer1_financials("NOPE") == {}


# ─────────────────────────────────────────────
# 5. quarterly_review_generator.py 回帰テスト
# ─────────────────────────────────────────────

import quarterly_review_generator as qrg  # noqa: E402


class TestQuarterlyReviewGeneratorRegression:
    def test_load_layer1_financials_matches_pre_migration_values(self, tmp_path, monkeypatch):
        monkeypatch.setattr(qrg, "COMMON_NORMALIZED_DIR", str(tmp_path))
        monkeypatch.setattr(qrg, "TANUKI_DATA_DIR", str(tmp_path))

        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2024-03-31", "val": 140, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 150, "is_annual": False, "is_ytd": False},
                    {"end": "2024-09-30", "val": 160, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 170, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 999, "is_annual": False, "is_ytd": True},
                ],
                "OperatingIncome": [
                    {"end": "2024-03-31", "val": 14, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 15, "is_annual": False, "is_ytd": False},
                    {"end": "2024-09-30", "val": 16, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 17, "is_annual": False, "is_ytd": False},
                ],
                "SBC": [{"end": "2024-12-31", "val": 5, "is_annual": False, "is_ytd": False}],
                "NetIncome": [{"end": "2024-12-31", "val": 15, "is_annual": False, "is_ytd": False}],
                "SharesDiluted": [{"end": "2024-12-31", "val": 1000, "is_annual": False, "is_ytd": False}],
            }
        }
        (tmp_path / "TEST_quarterly_normalized.json").write_text(
            json.dumps(normalized), encoding="utf-8"
        )
        ticker_dir = tmp_path / "TEST"
        ticker_dir.mkdir()
        (ticker_dir / "latest.json").write_text(
            json.dumps({"financial_health": {"sbc_ttm": 20},
                        "components": {"forward_eps": 1.23}}),
            encoding="utf-8",
        )

        result = qrg.load_layer1_financials("TEST")
        assert result["operating_margin"] == pytest.approx(0.1)
        assert result["sbc_quarterly"] == 5
        assert result["eps_diluted"] == pytest.approx(0.015)
        assert result["operating_margin_history"] == [
            {"quarter": "2024Q1", "operating_margin": 0.1},
            {"quarter": "2024Q2", "operating_margin": 0.1},
            {"quarter": "2024Q3", "operating_margin": 0.1},
            {"quarter": "2024Q4", "operating_margin": 0.1},
        ]
        assert result["sbc_ttm"] == 20
        assert result["eps_forward"] == 1.23


# ─────────────────────────────────────────────
# 6. hypecore.py 回帰テスト
# ─────────────────────────────────────────────

_HYPECORE_SRC = os.path.join(_REPO_ROOT, "src", "value", "hypecore")
if _HYPECORE_SRC not in sys.path:
    sys.path.insert(0, _HYPECORE_SRC)
import hypecore  # noqa: E402


class TestHypecoreRegression:
    def test_fetch_quarterly_fundamentals_excludes_ytd_and_annual(self, tmp_path, monkeypatch):
        monkeypatch.setattr(hypecore, "_NORM_DIR", tmp_path)

        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2023-03-31", "val": 100, "is_annual": False, "is_ytd": False},
                    {"end": "2023-06-30", "val": 110, "is_annual": False, "is_ytd": False},
                    {"end": "2023-09-30", "val": 120, "is_annual": False, "is_ytd": False},
                    {"end": "2023-12-31", "val": 130, "is_annual": False, "is_ytd": False},
                    {"end": "2024-03-31", "val": 140, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 150, "is_annual": False, "is_ytd": False},
                    {"end": "2024-09-30", "val": 160, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 170, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 999, "is_annual": False, "is_ytd": True},
                    {"end": "2024-12-31", "val": 500, "is_annual": True,  "is_ytd": False},
                ],
                "NetIncome": [
                    {"end": "2023-03-31", "val": 8,  "is_annual": False, "is_ytd": False},
                    {"end": "2023-06-30", "val": 9,  "is_annual": False, "is_ytd": False},
                    {"end": "2023-09-30", "val": 10, "is_annual": False, "is_ytd": False},
                    {"end": "2023-12-31", "val": 11, "is_annual": False, "is_ytd": False},
                    {"end": "2024-03-31", "val": 12, "is_annual": False, "is_ytd": False},
                    {"end": "2024-06-30", "val": 13, "is_annual": False, "is_ytd": False},
                    {"end": "2024-09-30", "val": 14, "is_annual": False, "is_ytd": False},
                    {"end": "2024-12-31", "val": 15, "is_annual": False, "is_ytd": False},
                ],
                "OCF": [{"end": "2024-12-31", "val": 20, "is_annual": False, "is_ytd": False}],
            }
        }
        (tmp_path / "TEST_quarterly_normalized.json").write_text(
            json.dumps(normalized), encoding="utf-8"
        )

        df = hypecore.fetch_quarterly_fundamentals("TEST")
        last = df.iloc[-1]
        assert last["revenue"] == 170
        assert last["rev_yoy"] == pytest.approx((620 / 460 - 1) * 100)
        assert last["ni_yoy"] == pytest.approx((15 - 11) / 11 * 100)
        assert last["ocf"] == 20

    def test_fetch_quarterly_fundamentals_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(hypecore, "_NORM_DIR", tmp_path)
        df = hypecore.fetch_quarterly_fundamentals("NOPE")
        assert df.empty
