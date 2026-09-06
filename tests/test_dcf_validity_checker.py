"""
tests/test_dcf_validity_checker.py

common/screening/dcf_validity_checker.py::check_c_data_jump() の
section/fieldパラメータ化（[[DATA-JUMP-CHECK-GENERALIZE-1]]）のユニットテスト。
Revenue専用のハードコードから汎用化した際、Revenue呼び出し元の挙動が
一切変わらないこと・新規フィールド（売上総利益・CapEx）向けの非対称な
閾値（down_ratio明示指定）が正しく機能することを検証する。

実行方法:
    python -m pytest tests/test_dcf_validity_checker.py -v
"""

import json
import os

from common.screening.dcf_validity_checker import check_c_data_jump


def _write_annual(sec_data_dir, ticker: str, year: int, section: str, field: str, value) -> None:
    ticker_dir = os.path.join(sec_data_dir, ticker)
    os.makedirs(ticker_dir, exist_ok=True)
    with open(os.path.join(ticker_dir, f"annual_{year}.json"), "w", encoding="utf-8") as f:
        json.dump({"period": year, section: {field: value}}, f)


class TestCheckCDataJumpRevenueBackwardCompat:
    """デフォルト引数（section="pl", field="revenue"）がパラメータ化前と
    完全に同一の挙動をすることを確認する（後方互換の回帰テスト）"""

    def test_default_args_still_check_revenue_with_2x_threshold(self, tmp_path):
        repo_root = str(tmp_path)
        for year, val in [(2020, 100_000_000), (2021, 400_000_000)]:
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "pl", "revenue", val)
        flag, jumps, vals = check_c_data_jump(repo_root, "TESTCO")
        assert flag is True
        assert len(jumps) == 1
        assert "4.00x" in jumps[0]

    def test_default_args_no_flag_within_2x_band(self, tmp_path):
        repo_root = str(tmp_path)
        for year, val in [(2020, 100_000_000), (2021, 150_000_000)]:
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "pl", "revenue", val)
        flag, jumps, vals = check_c_data_jump(repo_root, "TESTCO")
        assert flag is False
        assert jumps == []

    def test_default_down_ratio_is_symmetric_half(self, tmp_path):
        """down_ratio省略時は1/jump_ratio（デフォルト2.0倍→0.5倍）で対称に判定されること"""
        repo_root = str(tmp_path)
        for year, val in [(2020, 100_000_000), (2021, 49_000_000)]:
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "pl", "revenue", val)
        flag, jumps, vals = check_c_data_jump(repo_root, "TESTCO")
        assert flag is True  # 0.49 <= 0.5


class TestCheckCDataJumpFieldParameterization:
    """section/field引数でRevenue以外のフィールド（売上総利益・CapEx）を
    チェックできることを確認する"""

    def test_gross_profit_field_with_custom_thresholds(self, tmp_path):
        repo_root = str(tmp_path)
        for year, val in [(2023, 10_000_000), (2024, 60_000_000)]:
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "pl", "gross_profit", val)
        flag, jumps, vals = check_c_data_jump(
            repo_root, "TESTCO", section="pl", field="gross_profit", jump_ratio=5.0, down_ratio=0.2,
        )
        assert flag is True
        assert "6.00x" in jumps[0]

    def test_gross_profit_not_flagged_by_revenue_default_args(self, tmp_path):
        """フィールド未指定（デフォルトrevenue）で呼ぶとgross_profitの変化は無視されること"""
        repo_root = str(tmp_path)
        for year, val in [(2023, 10_000_000), (2024, 60_000_000)]:
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "pl", "gross_profit", val)
        flag, jumps, vals = check_c_data_jump(repo_root, "TESTCO")
        assert flag is False

    def test_capex_field_asymmetric_down_ratio_not_reciprocal_of_up_ratio(self, tmp_path):
        """CapExの下振れ閾値0.15は上振れ8.0の逆数0.125とは異なる非対称な値であり、
        down_ratio引数で明示指定しないと正しく判定できないことを確認する"""
        repo_root = str(tmp_path)
        for year, val in [(2023, 100_000_000), (2024, 13_000_000)]:  # ratio=0.13 (< 0.15, > 0.125)
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "cf",
                           "capital_expenditure", val)
        flag_explicit, jumps_explicit, _ = check_c_data_jump(
            repo_root, "TESTCO", section="cf", field="capital_expenditure", jump_ratio=8.0, down_ratio=0.15,
        )
        assert flag_explicit is True  # 0.13 <= 0.15

        flag_reciprocal, jumps_reciprocal, _ = check_c_data_jump(
            repo_root, "TESTCO", section="cf", field="capital_expenditure", jump_ratio=8.0,
        )
        assert flag_reciprocal is False  # 0.13 > 0.125（down_ratio省略時の対称値では発火しない）

    def test_capex_upside_jump_detected(self, tmp_path):
        repo_root = str(tmp_path)
        for year, val in [(2023, 2_761_000), (2024, 34_245_000)]:  # ALAB実データ相当、比率約12.4x
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "cf",
                           "capital_expenditure", val)
        flag, jumps, _ = check_c_data_jump(
            repo_root, "TESTCO", section="cf", field="capital_expenditure", jump_ratio=8.0, down_ratio=0.15,
        )
        assert flag is True
        assert "12.4" in jumps[0]

    def test_negative_value_transition_is_flagged(self, tmp_path):
        """売上総利益がマイナスに転じるケース（RCAT実例相当）も比率が
        down_ratio以下になり検知されることを確認する"""
        repo_root = str(tmp_path)
        for year, val in [(2022, 925_515), (2023, -336_795)]:
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "pl", "gross_profit", val)
        flag, jumps, _ = check_c_data_jump(
            repo_root, "TESTCO", section="pl", field="gross_profit", jump_ratio=5.0, down_ratio=0.2,
        )
        assert flag is True

    def test_zero_denominator_skipped(self, tmp_path):
        repo_root = str(tmp_path)
        for year, val in [(2022, 0), (2023, 5_000_000)]:
            _write_annual(str(tmp_path / "common" / "sec_data" / "data"), "TESTCO", year, "cf",
                           "capital_expenditure", val)
        flag, jumps, _ = check_c_data_jump(
            repo_root, "TESTCO", section="cf", field="capital_expenditure", jump_ratio=8.0, down_ratio=0.15,
        )
        assert flag is False
        assert jumps == []
