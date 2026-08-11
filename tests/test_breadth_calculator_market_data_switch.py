"""
tests/test_breadth_calculator_market_data_switch.py

[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序4-7（breadth_calculator.py
切替）の回帰テスト。compute_breadth()・fetch_rsp_spy_divergence()の
yfinance一括ダウンロード（yf.download()）がcommon.market_data.reader
経由に置き換わったことを検証する。get_sp500_tickers()は意図的独立実装
のため対象外（本テストでは扱わない）。

src/market/market_pulse/breadth_calculator.pyは他の切替済みファイルと
同じくトップレベルパッケージに属さない独立ディレクトリのスクリプトの
ため、sys.path追加による直接importで読む。

実行方法:
    python -m pytest tests/test_breadth_calculator_market_data_switch.py -v
"""

import os
import sys

import pytest

_MARKET_PULSE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "market", "market_pulse")
)
if _MARKET_PULSE_DIR not in sys.path:
    sys.path.insert(0, _MARKET_PULSE_DIR)

import breadth_calculator as bc  # noqa: E402


def _make_series(closes, gap_at=None):
    """dateはd0, d1, ...の連番、closeは引数のリストからそのまま生成する。
    gap_atで指定したインデックスは_gap: Trueのプレースホルダーにする。"""
    series = []
    for i, c in enumerate(closes):
        if gap_at is not None and i in gap_at:
            series.append({"date": f"d{i:04d}", "_gap": True})
        else:
            series.append({"date": f"d{i:04d}", "close": c, "_gap": False})
    return series


def _patch_price_series(monkeypatch, series_map, has_market_data=True):
    monkeypatch.setattr(bc, "HAS_MARKET_DATA", has_market_data)
    monkeypatch.setattr(bc, "_md_get_price_series", lambda ticker, days: series_map.get(ticker, []))


class TestComputeBreadthBasics:
    def test_market_data_unavailable_returns_none(self, monkeypatch):
        monkeypatch.setattr(bc, "HAS_MARKET_DATA", False)
        assert bc.compute_breadth(["AAPL"]) is None

    def test_insufficient_valid_tickers_returns_none(self, monkeypatch):
        """有効銘柄が100未満の場合はNoneを返す（データ品質ガード）"""
        # 50銘柄のみ、いずれも十分なデータを持つ
        series_map = {
            f"T{i}": _make_series([100.0 + j for j in range(60)]) for i in range(50)
        }
        _patch_price_series(monkeypatch, series_map)
        assert bc.compute_breadth(list(series_map.keys())) is None

    def test_ticker_with_recent_gaps_is_excluded(self, monkeypatch):
        """直近5営業日で実データが3日未満の銘柄は除外される
        （旧ロジックのrecent_nan<3条件と同義）"""
        good = {f"G{i}": _make_series([100.0 + j for j in range(260)]) for i in range(150)}
        # 直近5日中4日がgap（実データ1日のみ）→ 除外対象
        sparse = {"SPARSE": _make_series([100.0 + j for j in range(260)], gap_at={256, 257, 258, 259})}
        series_map = {**good, **sparse}
        _patch_price_series(monkeypatch, series_map)
        result = bc.compute_breadth(list(series_map.keys()))
        assert result is not None
        assert result["total_stocks"] == 150

    def test_missing_ticker_data_skips_gracefully(self, monkeypatch):
        """個別銘柄取得失敗（空リスト）でも例外にならず他銘柄の集計は継続する"""
        good = {f"G{i}": _make_series([100.0 + j for j in range(260)]) for i in range(150)}
        series_map = {**good, "MISSING": []}
        _patch_price_series(monkeypatch, series_map)
        result = bc.compute_breadth(list(series_map.keys()))
        assert result is not None
        assert result["total_stocks"] == 150


class TestComputeBreadthCalculations:
    def _base_series_map(self, n=150):
        """n銘柄、260日分の単調増加系列（全銘柄が上昇トレンド=新高値・
        50/200MA超過の判定を検証しやすくする）"""
        return {f"T{i}": _make_series([100.0 + j * 0.1 for j in range(260)]) for i in range(n)}

    def test_advances_declines_counted_correctly(self, monkeypatch):
        series_map = self._base_series_map(100)
        # 追加で下落銘柄を50件作る
        down = {f"D{i}": _make_series([200.0 - j * 0.1 for j in range(260)]) for i in range(50)}
        series_map.update(down)
        _patch_price_series(monkeypatch, series_map)
        result = bc.compute_breadth(list(series_map.keys()))
        assert result["advances"] == 100  # 単調増加系列は最終日も上昇
        assert result["declines"] == 50   # 単調減少系列は最終日も下落

    def test_new_highs_52w_detected_for_monotonic_increase(self, monkeypatch):
        """単調増加系列は最終日が52週内の最高値 → 新高値としてカウントされる"""
        series_map = self._base_series_map(150)
        _patch_price_series(monkeypatch, series_map)
        result = bc.compute_breadth(list(series_map.keys()))
        assert result["new_highs_52w"] == 150

    def test_pct_above_50ma_and_200ma_for_uptrend(self, monkeypatch):
        """単調増加系列は直近終値が50日/200日移動平均を上回る"""
        series_map = self._base_series_map(150)
        _patch_price_series(monkeypatch, series_map)
        result = bc.compute_breadth(list(series_map.keys()))
        assert result["pct_above_50ma"] == 100.0
        assert result["pct_above_200ma"] == 100.0

    def test_date_reflects_latest_real_date(self, monkeypatch):
        series_map = self._base_series_map(150)
        _patch_price_series(monkeypatch, series_map)
        result = bc.compute_breadth(list(series_map.keys()))
        assert result["date"] == "d0259"


class TestFetchRspSpyDivergence:
    def test_normal_case_computed_correctly(self, monkeypatch):
        rsp = _make_series([100.0 + i * 0.1 for i in range(25)])
        spy = _make_series([200.0 + i * 0.05 for i in range(25)])
        _patch_price_series(monkeypatch, {"RSP": rsp, "SPY": spy})
        result = bc.fetch_rsp_spy_divergence()
        assert result is not None
        assert "rsp_return_1d" in result
        assert "rsp_spy_divergence_1d" in result
        assert "rsp_spy_divergence_20d_avg" in result

    def test_rsp_outperforms_spy_yields_positive_divergence(self, monkeypatch):
        """RSPの騰落率がSPYを上回る場合、divergence_1dは正になる
        （プラス=RSP優勢=広範な上昇、docstring記載の符号と一致）"""
        rsp = _make_series([100.0, 100.0, 105.0])  # +5%
        spy = _make_series([200.0, 200.0, 202.0])  # +1%
        _patch_price_series(monkeypatch, {"RSP": rsp, "SPY": spy})
        result = bc.fetch_rsp_spy_divergence()
        assert result["rsp_spy_divergence_1d"] > 0

    def test_market_data_unavailable_returns_none(self, monkeypatch):
        _patch_price_series(monkeypatch, {}, has_market_data=False)
        assert bc.fetch_rsp_spy_divergence() is None

    def test_insufficient_data_returns_none(self, monkeypatch):
        _patch_price_series(monkeypatch, {"RSP": _make_series([100.0]), "SPY": _make_series([200.0])})
        assert bc.fetch_rsp_spy_divergence() is None

    def test_unequal_length_series_truncated_to_common_tail(self, monkeypatch):
        """RSP/SPYの実データ件数が異なる場合、末尾の共通件数に揃える"""
        rsp = _make_series([100.0 + i * 0.1 for i in range(25)])
        spy = _make_series([200.0 + i * 0.05 for i in range(20)])
        _patch_price_series(monkeypatch, {"RSP": rsp, "SPY": spy})
        result = bc.fetch_rsp_spy_divergence()
        assert result is not None

    def test_unexpected_exception_returns_none(self, monkeypatch):
        def _raise(ticker, days):
            raise RuntimeError("simulated failure")
        monkeypatch.setattr(bc, "HAS_MARKET_DATA", True)
        monkeypatch.setattr(bc, "_md_get_price_series", _raise)
        assert bc.fetch_rsp_spy_divergence() is None
