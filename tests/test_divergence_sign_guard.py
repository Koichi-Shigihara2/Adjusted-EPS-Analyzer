"""
tests/test_divergence_sign_guard.py

FCF-DIVERGENCE-SIGN-GUARD-1: divergence_ratio（estimated_fcf/raw_fcf）は
raw_fcf>0の場合のみ符号付きで計算されるため、conversion_rateが負値等の
理由でestimated_fcfの符号がraw_fcfと反転すると、divergence_ratioの絶対値が
小さく（例: -0.45）閾値（>=2.0/>=5.0）を満たさず、divergence_warningが
生成されないまま素通りする問題があった。

raw_fcf>0かつestimated_fcf<0の符号反転を、閾値判定とは独立に無条件で
高乖離警告扱いとするガードの回帰テスト。

実行方法:
    python -m pytest tests/test_divergence_sign_guard.py -v
"""
import json
import os
import sys

_CALC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "value", "tanuki_valuation", "calculator")
)
if _CALC_DIR not in sys.path:
    sys.path.insert(0, _CALC_DIR)

from adjustments import estimate_fcf_from_eps  # type: ignore[import]  # noqa: E402


def _write_eps_annual(tmp_path, ticker, adjusted_net_income, adjustments=None):
    ticker_dir = tmp_path / ticker
    ticker_dir.mkdir()
    (ticker_dir / "annual.json").write_text(
        json.dumps({
            "years": [{
                "year": "2025",
                "adjusted_net_income": adjusted_net_income,
                "adjustments": adjustments or [],
            }]
        }),
        encoding="utf-8",
    )
    return str(tmp_path)


def _config_path(tmp_path, sector_rate=0.70):
    path = tmp_path / "fcf_conversion_config.json"
    path.write_text(
        json.dumps({
            "ticker_overrides": {},
            "sector_conversion_rates": {"TestSector": sector_rate, "default": 0.70},
        }),
        encoding="utf-8",
    )
    return str(path)


class TestDivergenceSignGuard:
    def test_sign_flip_warns_despite_small_ratio_magnitude(self, tmp_path):
        """raw_fcf>0・estimated_fcf<0（負のconversion_rateによる符号反転）の場合、
        divergence_ratioの絶対値(-0.9)が閾値2.0未満であっても
        divergence_warningが生成されること（VSTシミュレーションで発見された
        見逃しパターンの再現）"""
        eps_dir = _write_eps_annual(tmp_path, "TESTCO", adjusted_net_income=100_000_000)
        cfg = _config_path(tmp_path, sector_rate=-0.45)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=50_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )

        assert result.applied is True
        assert result.estimated_fcf < 0
        assert result.raw_fcf > 0
        assert abs(result.divergence_ratio) < 2.0, (
            "この乖離率の絶対値が閾値未満であることが、旧ロジックの見逃し条件"
        )
        assert result.divergence_warning != ""
        assert "符号反転" in result.divergence_warning

    def test_positive_ratio_below_threshold_still_no_warning(self, tmp_path):
        """符号反転がなく、乖離率が2.0未満の通常ケースでは、
        従来通りdivergence_warningが空のままであること（回帰確認）"""
        eps_dir = _write_eps_annual(tmp_path, "TESTCO", adjusted_net_income=100_000_000)
        cfg = _config_path(tmp_path, sector_rate=0.70)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=100_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )

        assert result.applied is True
        assert result.estimated_fcf > 0
        assert result.divergence_ratio < 2.0
        assert result.divergence_warning == ""

    def test_positive_mid_divergence_still_warns_without_sign_flip_text(self, tmp_path):
        """符号反転を伴わない従来型の中乖離（>=2.0倍）は、
        従来通り警告が出て、かつ「符号反転」の文言は含まないこと（回帰確認）"""
        eps_dir = _write_eps_annual(tmp_path, "TESTCO", adjusted_net_income=100_000_000)
        cfg = _config_path(tmp_path, sector_rate=2.5)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=100_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )

        assert result.applied is True
        assert result.divergence_ratio == 2.5
        assert result.divergence_warning != ""
        assert "符号反転" not in result.divergence_warning

    def test_positive_high_divergence_still_warns_without_sign_flip_text(self, tmp_path):
        """符号反転を伴わない従来型の高乖離（>=5.0倍）は、
        従来通り警告が出て、かつ「符号反転」の文言は含まないこと（回帰確認）"""
        eps_dir = _write_eps_annual(tmp_path, "TESTCO", adjusted_net_income=100_000_000)
        cfg = _config_path(tmp_path, sector_rate=6.0)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=100_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )

        assert result.applied is True
        assert result.divergence_ratio == 6.0
        assert result.divergence_warning != ""
        assert "符号反転" not in result.divergence_warning
