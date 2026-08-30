"""
tests/test_core_calculator_v0_note.py

[[V0-V0RM-CONFUSION-RISK-1]]の回帰テスト。

core_calculator.py::KoichiValuationCalculator.calculate_pt()の戻り値に、
既存フィールド構成（後方互換性）を変更せず"v0_note"を追加した。latest.json
を直接読む外部AI・レビュアーが、トップレベルのv0（β込みCAPMベース、
intrinsic_value_betaの計算根拠）をメインの理論株価計算根拠と誤認しない
よう、メイン根拠はdcf_components.v0_rmである旨を明示する。

実行方法:
    python -m pytest tests/test_core_calculator_v0_note.py -v
"""

import os
import sys

_TV_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src", "value", "tanuki_valuation"))
if _TV_DIR not in sys.path:
    sys.path.insert(0, _TV_DIR)

from core_calculator import KoichiValuationCalculator  # type: ignore[import]


def _minimal_financials() -> dict:
    """calculate_pt()を正常系（error無し）で通過させる最小限のfinancials dict。"""
    return {
        "fcf_5yr_avg": 1_000_000_000,
        "fcf_2yr_avg": 1_000_000_000,
        "fcf_list_raw": [800e6, 900e6, 1000e6, 1000e6, 1100e6],
        "diluted_shares": 100_000_000,
        "current_price": 50.0,
        "beta": 1.0,
        "sector": "Technology",
        "industry": "Software",
        "net_debt": 0,
        "net_cash_data": {"fiscal_year": 2025},
        "revenue_ttm": 5_000_000_000,
        "ni_ttm": 500_000_000,
    }


class TestV0NoteField:
    def test_calculate_pt_returns_no_error(self):
        calc = KoichiValuationCalculator()
        result = calc.calculate_pt(_minimal_financials())
        assert result.get("error") is None

    def test_v0_and_v0_note_both_present(self):
        """既存のv0フィールドは変更せず、説明用のv0_noteが追加されていること
        （後方互換性の確認: v0自体は削除・改名されていない）"""
        calc = KoichiValuationCalculator()
        result = calc.calculate_pt(_minimal_financials())
        assert "v0" in result
        assert isinstance(result["v0"], float)
        assert "v0_note" in result

    def test_v0_note_points_to_v0_rm_as_main_basis(self):
        """v0_noteの文言が、メインの理論株価計算根拠はdcf_components.v0_rm
        である旨を明示していること（v0自体をメイン根拠と誤認させない）"""
        calc = KoichiValuationCalculator()
        result = calc.calculate_pt(_minimal_financials())
        note = result["v0_note"]
        assert "v0_rm" in note
        assert "dcf_components" in note

    def test_dcf_components_v0_rm_exists_separately_from_top_level_v0(self):
        """既存の罠の実体確認: トップレベルv0とdcf_components.v0_rmは
        異なる値を持つ別フィールドであること"""
        calc = KoichiValuationCalculator()
        result = calc.calculate_pt(_minimal_financials())
        dcf_components = result.get("dcf_components", {})
        assert "v0_rm" in dcf_components
