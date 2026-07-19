"""
tests/test_split_history_adjustments.py

src/value/adjusted_eps_analyzer/pipeline.py::load_split_history()/
apply_split_adjustments() の回帰テスト（SPLIT-REALTIME-GAP-1）。

config/split_history.yaml へのNVDA/AVGO/CPRT/WMT/LRCX/CELH/KLAC登録が、
恒久固着していた分割前四半期を正しく遡及補正すること、KLACのように
post-split四半期データがまだ存在しない銘柄は安全にno-opとなること、
未登録銘柄・除外銘柄（RCAT）には一切影響しないことを確認する。

実行方法:
    python -m pytest tests/test_split_history_adjustments.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import src.value.adjusted_eps_analyzer.pipeline as pl  # noqa: E402


def _q(period_end, diluted_shares_used, form="10-Q"):
    return {
        "period_end": period_end,
        "filing_date": period_end,
        "form": form,
        "diluted_shares_used": diluted_shares_used,
        "diluted_shares": diluted_shares_used,
        "gaap_eps": 1.0,
        "adjusted_eps": 1.0,
    }


class TestLoadSplitHistory:
    def test_yaml_contains_all_registered_tickers(self):
        """config/split_history.yaml に本タスクで登録した8銘柄が存在すること"""
        history = pl.load_split_history()
        for ticker in ("NVDA", "AVGO", "CPRT", "WMT", "LRCX", "CELH", "KLAC", "TSLA"):
            assert ticker in history, f"{ticker} not registered in split_history.yaml"


class TestApplySplitAdjustmentsRealData:
    """本番のconfig/split_history.yamlを実際に読み込み、各銘柄の恒久固着
    四半期が正しく遡及補正されることを確認する（合成データではなく
    実登録内容そのものへの回帰テスト）"""

    def setup_method(self):
        self.history = pl.load_split_history()

    def test_nvda_stuck_quarters_corrected(self):
        quarters = [
            _q("2021-10-31", 2_538_000_000),
            _q("2022-05-01", 2_537_000_000),
            _q("2022-07-31", 2_516_000_000),
            _q("2022-10-30", 2_499_000_000),
            _q("2023-01-29", 25_070_000_000, form="10-K"),
            _q("2023-04-30", 2_490_000_000),  # NVDA-STI型の孤立ギャップ
            _q("2023-07-30", 24_994_000_000),
            _q("2023-10-29", 24_940_000_000),
            _q("2024-07-28", 24_848_000_000),  # real split date(2024-06-10)以降
        ]
        result = pl.apply_split_adjustments("NVDA", quarters, self.history)
        by_end = {r["period_end"]: r for r in result}
        assert by_end["2023-04-30"]["diluted_shares_used"] == 24_900_000_000
        assert by_end["2021-10-31"]["diluted_shares_used"] == 25_380_000_000
        # 既に分割調整済みの四半期は変更されない
        assert by_end["2023-07-30"]["diluted_shares_used"] == 24_994_000_000

    def test_avgo_stuck_quarters_corrected(self):
        quarters = [
            _q("2022-07-31", 430_000_000),
            _q("2023-01-29", 429_000_000),
            _q("2023-04-30", 427_000_000),
            _q("2023-07-30", 4_269_000_000),
            _q("2023-10-29", 4_272_000_000, form="10-K"),
            _q("2024-08-04", 4_663_000_000),  # real split date(2024-07-15)以降
        ]
        result = pl.apply_split_adjustments("AVGO", quarters, self.history)
        by_end = {r["period_end"]: r for r in result}
        assert by_end["2023-04-30"]["diluted_shares_used"] == 4_270_000_000
        assert by_end["2023-07-30"]["diluted_shares_used"] == 4_269_000_000  # unchanged

    def test_cprt_single_split_corrected(self):
        """CPRTは2023-08-22の単一分割のみ登録（2022-11-04は分割ではなく
        授権株式数増加の株主総会承認だったため対象外、一次情報で確認済み）"""
        quarters = [
            _q("2021-10-31", 482_442_000),
            _q("2022-04-30", 481_448_000),
            _q("2022-07-31", 964_604_000, form="10-K"),
            _q("2024-07-31", 974_798_000, form="10-K"),  # real split date(2023-08-22)以降
        ]
        result = pl.apply_split_adjustments("CPRT", quarters, self.history)
        by_end = {r["period_end"]: r for r in result}
        assert by_end["2021-10-31"]["diluted_shares_used"] == 964_884_000
        assert by_end["2022-07-31"]["diluted_shares_used"] == 964_604_000  # unchanged

    def test_wmt_stuck_quarters_corrected(self):
        quarters = [
            _q("2022-04-30", 2_765_000_000),
            _q("2022-10-31", 2_711_000_000),
            _q("2023-01-31", 8_202_000_000, form="10-K"),
            _q("2024-04-30", 8_084_000_000),  # real split date(2024-02-26)以降
        ]
        result = pl.apply_split_adjustments("WMT", quarters, self.history)
        by_end = {r["period_end"]: r for r in result}
        assert by_end["2022-04-30"]["diluted_shares_used"] == 8_295_000_000

    def test_lrcx_eight_stuck_quarters_corrected(self):
        quarters = [
            _q("2021-03-28", 144_609_000),
            _q("2022-09-25", 137_208_000),
            _q("2023-03-26", 135_395_000),
            _q("2023-06-25", 1_358_336_000, form="10-K"),
            _q("2024-12-29", 1_291_469_000),  # real split date(2024-10-03)以降
        ]
        result = pl.apply_split_adjustments("LRCX", quarters, self.history)
        by_end = {r["period_end"]: r for r in result}
        assert by_end["2021-03-28"]["diluted_shares_used"] == 1_446_090_000
        assert by_end["2023-03-26"]["diluted_shares_used"] == 1_353_950_000
        # 2023-06-25はチェック対象外(>= split_date)だが、既に分割調整済みの値のため
        # 変更されない（閾値判定でスキップされる）
        assert by_end["2023-06-25"]["diluted_shares_used"] == 1_358_336_000

    def test_celh_stuck_quarters_corrected(self):
        quarters = [
            _q("2022-03-31", 78_289_000),
            _q("2022-09-30", 75_796_000),
            _q("2022-12-31", 226_947_000, form="10-K"),
            _q("2023-12-31", 236_964_000, form="10-K"),  # real split date(2023-11-15)以降
        ]
        result = pl.apply_split_adjustments("CELH", quarters, self.history)
        by_end = {r["period_end"]: r for r in result}
        assert by_end["2022-03-31"]["diluted_shares_used"] == 234_867_000

    def test_tsla_single_stuck_quarter_corrected(self):
        """TSLAは2021-06-30の1四半期のみが恒久固着（追加登録、Koichiさん
        承認済みの対象6銘柄の1つだが当初の登録依頼で記載漏れだったため
        追加登録した）"""
        quarters = [
            _q("2021-06-30", 1_119_000_000),
            _q("2021-09-30", 3_369_000_000),
            _q("2022-03-31", 3_472_000_000),
            _q("2022-06-30", 3_464_000_000),
            _q("2022-09-30", 3_468_000_000, form="10-K"),
        ]
        result = pl.apply_split_adjustments("TSLA", quarters, self.history)
        by_end = {r["period_end"]: r for r in result}
        assert by_end["2021-06-30"]["diluted_shares_used"] == 3_357_000_000
        assert by_end["2021-09-30"]["diluted_shares_used"] == 3_369_000_000  # unchanged

    def test_klac_no_post_split_data_is_safe_noop(self):
        """KLACは事前登録（2026-06-12）だが、post-split四半期データが
        まだ存在しない状態。post_split_sharesが空リストとなりスキップされ、
        エラーにならず全四半期が無変更のままであること"""
        quarters = [
            _q("2025-12-31", 132_009_000),
            _q("2026-03-31", 131_750_000),
        ]
        result = pl.apply_split_adjustments("KLAC", quarters, self.history)
        assert result[0]["diluted_shares_used"] == 132_009_000
        assert result[1]["diluted_shares_used"] == 131_750_000

    def test_rcat_not_registered_no_change(self):
        """RCATは分割と無関係と判明したため未登録。split_history.get()が
        空リストを返しapply_split_adjustments()が早期returnすること"""
        quarters = [
            _q("2022-07-31", 53_860_199),
            _q("2024-03-31", 74_204_622),
        ]
        result = pl.apply_split_adjustments("RCAT", quarters, self.history)
        assert result[0]["diluted_shares_used"] == 53_860_199
        assert result[1]["diluted_shares_used"] == 74_204_622

    def test_unregistered_ticker_no_change(self):
        """split_history.yamlに存在しない銘柄は完全に無変更で返る"""
        quarters = [_q("2023-01-01", 1_000_000)]
        result = pl.apply_split_adjustments("UNKNOWNTICKER", quarters, self.history)
        assert result[0]["diluted_shares_used"] == 1_000_000
