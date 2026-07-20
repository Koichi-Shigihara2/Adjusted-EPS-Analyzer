"""
tests/test_estimate_fcf_ma_addback.py

CWAN-SNPS-MA-DISTORTION-1: estimate_fcf_from_eps()が「買収・統合関連」カテゴリ
の加算分を控除してからconversion_rateを掛けることの回帰テスト。

CWAN/SNPS実例で判明した通り、adjusted_net_incomeに買収由来の無形資産償却費等
（非現金・一過性）の加算が含まれたままconversion_rateを掛けると、実際の
キャッシュフロー創出力を超える推定FCFになる。この加算分をFCF換算専用に
控除することで、乖離が是正されることを確認する。

実行方法:
    python -m pytest tests/test_estimate_fcf_ma_addback.py -v
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


def _write_eps_annual(tmp_path, ticker, adjusted_net_income, adjustments):
    ticker_dir = tmp_path / ticker
    ticker_dir.mkdir()
    (ticker_dir / "annual.json").write_text(
        json.dumps({
            "years": [{
                "year": "2025",
                "adjusted_net_income": adjusted_net_income,
                "adjustments": adjustments,
            }]
        }),
        encoding="utf-8",
    )
    return str(tmp_path)


def _config_path(tmp_path, sector_rate=1.0):
    path = tmp_path / "fcf_conversion_config.json"
    path.write_text(
        json.dumps({
            "ticker_overrides": {},
            "sector_conversion_rates": {"TestSector": sector_rate, "default": 0.70},
        }),
        encoding="utf-8",
    )
    return str(path)


class TestMaAddbackDeduction:
    def test_ma_addback_deducted_from_estimate(self, tmp_path):
        """買収・統合関連の加算がある場合、その分を控除した値で推定FCFを計算する
        （CWAN実例に近い比率: 加算が調整済み純利益の大半を占めるケース）"""
        eps_dir = _write_eps_annual(
            tmp_path, "TESTCO",
            adjusted_net_income=126_000_000,
            adjustments=[
                {"category": "買収・統合関連", "item_name": "無形資産償却費", "amount": 75_700_000},
                {"category": "株式報酬関連", "item_name": "株式報酬費用", "amount": 33_000_000},
            ],
        )
        cfg = _config_path(tmp_path, sector_rate=1.61)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=92_293_750, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )
        assert result.applied is True
        assert result.ma_addback_excluded == 75_700_000
        # 控除後: 126,000,000 - 75,700,000 = 50,300,000
        assert result.adj_net_income == 50_300_000
        assert result.estimated_fcf == 50_300_000 * 1.61
        # 控除前(126M×1.61=202.9M/92.3M=2.2x)より乖離が大幅改善していること
        assert result.divergence_ratio < 1.2

    def test_no_ma_category_means_zero_deduction(self, tmp_path):
        """買収・統合関連カテゴリが存在しない銘柄では控除額0円、
        従来と完全に同じ結果になること（非対象銘柄への無影響を保証）"""
        eps_dir = _write_eps_annual(
            tmp_path, "TESTCO",
            adjusted_net_income=100_000_000,
            adjustments=[
                {"category": "株式報酬関連", "item_name": "株式報酬費用", "amount": 20_000_000},
            ],
        )
        cfg = _config_path(tmp_path, sector_rate=0.70)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=80_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )
        assert result.ma_addback_excluded == 0
        assert result.adj_net_income == 100_000_000
        assert result.estimated_fcf == 100_000_000 * 0.70

    def test_ma_addback_can_flip_to_raw_fcf_fallback(self, tmp_path):
        """控除後の調整済み純利益がマイナスに転じる場合は、生FCFへフォールバック
        する（控除前drが1超のため方向性ガードは控除を許可するが、控除後に
        マイナス転落するケース）"""
        eps_dir = _write_eps_annual(
            tmp_path, "TESTCO",
            adjusted_net_income=200_000_000,
            adjustments=[
                {"category": "買収・統合関連", "item_name": "無形資産償却費", "amount": 250_000_000},
            ],
        )
        cfg = _config_path(tmp_path, sector_rate=0.70)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=50_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )
        # 控除前dr = (200M×0.7)/50M = 2.8 > 1.0 のためガードは控除を許可
        assert result.applied is False
        assert result.method == "raw_fcf"
        assert result.estimated_fcf == 50_000_000
        assert result.ma_addback_excluded == 250_000_000
        assert result.ma_addback_detected_but_not_applied == 0
        assert result.adj_net_income < 0

    def test_direction_guard_blocks_deduction_when_pre_dr_le_1(self, tmp_path):
        """FCF-EST-DIRECTION-GUARD-1: 控除前Adj_NIベースのdrが1以下
        （控除しなくても既に生FCFを下回っている＝過小推定側）の場合、
        控除を適用せず元のAdj_NIをそのまま使う（LITE実例に近い比率:
        控除前dr=0.435）"""
        eps_dir = _write_eps_annual(
            tmp_path, "TESTCO",
            adjusted_net_income=31_100_000,
            adjustments=[
                {"category": "買収・統合関連", "item_name": "無形資産償却費", "amount": 149_700_000},
            ],
        )
        cfg = _config_path(tmp_path, sector_rate=0.70)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=50_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )
        # 控除前dr = (31.1M×0.7)/50M = 0.435 <= 1.0 のためガードが控除を阻止
        assert result.applied is True
        assert result.adj_net_income == 31_100_000
        assert result.estimated_fcf == 31_100_000 * 0.70
        assert result.ma_addback_excluded == 0
        assert result.ma_addback_detected_but_not_applied == 149_700_000
        assert result.divergence_ratio < 1.0

    def test_negative_ma_adjustment_amounts_not_subtracted(self, tmp_path):
        """買収・統合関連カテゴリの金額がマイナス（公正価値評価益等）の場合は
        控除対象に含めない（加算〈add_back〉の趣旨に反するため）"""
        eps_dir = _write_eps_annual(
            tmp_path, "TESTCO",
            adjusted_net_income=100_000_000,
            adjustments=[
                {"category": "買収・統合関連", "item_name": "条件付対価公正価値変動益", "amount": -30_000_000},
            ],
        )
        cfg = _config_path(tmp_path, sector_rate=0.70)

        result = estimate_fcf_from_eps(
            ticker="TESTCO", raw_fcf=80_000_000, diluted_shares=100_000_000,
            sector="TestSector", eps_data_dir=eps_dir, config_path=cfg,
            fcf_cv=0.9, outlier_detected=True,
        )
        assert result.ma_addback_excluded == 0
        assert result.adj_net_income == 100_000_000
