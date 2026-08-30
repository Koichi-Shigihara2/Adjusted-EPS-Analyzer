"""
tests/test_eps_discrepancy_flag_overload.py

[[EPS-DISCREPANCY-FLAG-OVERLOAD-1]]の回帰テスト。

check_eps_discrepancy()（XBRL vs Alpha Vantage公式値の20%超乖離＝データ
品質上の疑義）とapply_fair_value_detection()（公正価値変動の自動検出・
調整が適用されたことの記録）は意味的に全く異なる状況を示すにもかかわらず、
修正前は同一の`special_flags: ["EPS_DISCREPANCY"]`を共有していた。
修正後は前者が"EPS_DISCREPANCY"、後者が"FAIR_VALUE_ADJUSTED"という別々の
フラグ名を使うことを検証する。

実行方法:
    python -m pytest tests/test_eps_discrepancy_flag_overload.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_PKG_DIR = os.path.join(_REPO_ROOT, "src", "value", "adjusted_eps_analyzer")
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

import fair_value_detector as fvd  # noqa: E402


def _make_quarter(fiscal_year, quarter, net_income, revenue=5_000_000, diluted_shares=1_000_000):
    return {
        "fiscal_year": fiscal_year,
        "quarter": quarter,
        "filing_date": f"{fiscal_year}-{quarter:02d}-01",
        "gaap_net_income": net_income,
        "gaap_eps": net_income / diluted_shares,
        "revenue": revenue,
        "diluted_shares_used": diluted_shares,
        "net_adjustment_total": 0.0,
        "adjustments": [],
        "special_flags": [],
        "special_notes": {},
    }


class TestFairValueDetectionFlagIsDistinct:
    def test_fair_value_detection_sets_fair_value_adjusted_flag(self):
        """条件1+2+3を満たす四半期はFAIR_VALUE_ADJUSTEDフラグを持つこと
        （修正前はEPS_DISCREPANCYが設定されていた）"""
        q = _make_quarter(2024, 1, net_income=-1_000_000)
        quarterly_raw = [{
            "fiscal_year": 2024, "quarter": 1,
            "us-gaap:FairValueAdjustmentOfWarrants": {"value": 500_000, "unit": "USD"},
        }]
        result = fvd.apply_fair_value_detection(quarterly_raw, [q])
        assert len(result) == 1
        flags = result[0]["special_flags"]
        assert "FAIR_VALUE_ADJUSTED" in flags
        assert "EPS_DISCREPANCY" not in flags

    def test_fair_value_auto_detect_note_flag_field_matches(self):
        """special_notes.fair_value_auto_detect.flag も同じ新フラグ名であること"""
        q = _make_quarter(2024, 1, net_income=-1_000_000)
        quarterly_raw = [{
            "fiscal_year": 2024, "quarter": 1,
            "us-gaap:FairValueAdjustmentOfWarrants": {"value": 500_000, "unit": "USD"},
        }]
        result = fvd.apply_fair_value_detection(quarterly_raw, [q])
        note = result[0]["special_notes"]["fair_value_auto_detect"]
        assert note["flag"] == "FAIR_VALUE_ADJUSTED"

    def test_no_fv_tags_leaves_quarter_unmodified(self):
        """FVタグがない四半期は一切フラグが立たないこと（既存挙動の非回帰確認）"""
        q = _make_quarter(2024, 1, net_income=-1_000_000)
        quarterly_raw = [{"fiscal_year": 2024, "quarter": 1}]
        result = fvd.apply_fair_value_detection(quarterly_raw, [q])
        assert result[0]["special_flags"] == []


class TestEpsDiscrepancySourceUnchanged:
    """check_eps_discrepancy()側（意味が異なる別処理）は
    引き続き'EPS_DISCREPANCY'を使うこと（今回のリネーム対象外）を
    ソースレベルで確認する。"""

    def test_pipeline_check_eps_discrepancy_still_uses_eps_discrepancy_flag(self):
        pipeline_path = os.path.join(_PKG_DIR, "pipeline.py")
        with open(pipeline_path, encoding="utf-8") as f:
            content = f.read()
        start = content.index("def check_eps_discrepancy")
        end = content.index("\ndef ", start + 1)
        block = content[start:end]
        assert "'flag': 'EPS_DISCREPANCY'" in block

    def test_fair_value_detector_no_longer_uses_bare_eps_discrepancy_flag(self):
        fvd_path = os.path.join(_PKG_DIR, "fair_value_detector.py")
        with open(fvd_path, encoding="utf-8") as f:
            content = f.read()
        assert '"EPS_DISCREPANCY"' not in content
        assert '"FAIR_VALUE_ADJUSTED"' in content
