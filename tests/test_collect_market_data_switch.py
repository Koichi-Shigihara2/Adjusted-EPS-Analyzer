"""
tests/test_collect_market_data_switch.py

[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序4-5（collect.py切替）の回帰
テスト。get_price_change()のyfinance直接呼び出し（.history(period="2d")）
がcommon.market_data.reader経由に置き換わったこと・reader側がデータ
不足を返す場合の中立デフォルト（None、旧コードのlen(hist)<2時と同じ）を
検証する。

src/discover/collect.pyはパッケージ経由でimportできない構成のため、
importlib.util経由でファイルパス指定してモジュール単体を読む
（valuation_fetcher.py切替時と同じパターン）。

実行方法:
    python -m pytest tests/test_collect_market_data_switch.py -v
"""

import importlib.util
import os

import pytest

_MODULE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "discover", "collect.py")
)


def _load_module():
    spec = importlib.util.spec_from_file_location("collect", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cl():
    return _load_module()


def _patch_market_data(monkeypatch, module, series=None, has_market_data=True):
    monkeypatch.setattr(module, "HAS_MARKET_DATA", has_market_data)
    monkeypatch.setattr(module, "_md_get_price_series", lambda ticker, days: series)


class TestGetPriceChangeNormalCase:
    def test_positive_change_computed_correctly(self, cl, monkeypatch):
        _patch_market_data(monkeypatch, cl, series=[
            {"date": "2026-08-06", "close": 100.0, "_gap": False},
            {"date": "2026-08-07", "close": 105.0, "_gap": False},
        ])
        assert cl.get_price_change("XYZ") == 5.0

    def test_negative_change_computed_correctly(self, cl, monkeypatch):
        _patch_market_data(monkeypatch, cl, series=[
            {"date": "2026-08-06", "close": 100.0, "_gap": False},
            {"date": "2026-08-07", "close": 90.0, "_gap": False},
        ])
        assert cl.get_price_change("XYZ") == -10.0

    def test_uses_last_two_real_closes_ignoring_gap_placeholders(self, cl, monkeypatch):
        """単発の営業日欠損（_gap: True）を除外し、実データの末尾2件を比較する
        （防御的設計、data_fetcher.py切替時と同様のパターン）"""
        _patch_market_data(monkeypatch, cl, series=[
            {"date": "2026-08-04", "close": 100.0, "_gap": False},
            {"date": "2026-08-05", "close": 200.0, "_gap": True},  # 欠損プレースホルダー
            {"date": "2026-08-06", "close": 110.0, "_gap": False},
            {"date": "2026-08-07", "close": 121.0, "_gap": False},
        ])
        # 末尾2件の実データ（110.0→121.0）のみを使用、gapの200.0は無視される
        assert cl.get_price_change("XYZ") == 10.0


class TestGetPriceChangeNeutralDefaults:
    def test_insufficient_real_closes_returns_none(self, cl, monkeypatch):
        """実データが1件以下の場合、旧コードのlen(hist)<2と同じくNoneを返す"""
        _patch_market_data(monkeypatch, cl, series=[
            {"date": "2026-08-07", "close": 100.0, "_gap": False},
        ])
        assert cl.get_price_change("XYZ") is None

    def test_empty_series_returns_none(self, cl, monkeypatch):
        """daily/未取得銘柄（reader.get_price_series()が空リスト）でも
        例外にならずNoneを返す"""
        _patch_market_data(monkeypatch, cl, series=[])
        assert cl.get_price_change("XYZ") is None

    def test_zero_previous_close_returns_none(self, cl, monkeypatch):
        """0除算を避け、prev<=0の場合はNoneを返す（旧コードのif prev > 0と同じ）"""
        _patch_market_data(monkeypatch, cl, series=[
            {"date": "2026-08-06", "close": 0.0, "_gap": False},
            {"date": "2026-08-07", "close": 10.0, "_gap": False},
        ])
        assert cl.get_price_change("XYZ") is None

    def test_market_data_module_unavailable_returns_none(self, cl, monkeypatch):
        """common.market_data.readerがimport不可の場合（HAS_MARKET_DATA=
        False）、旧来の完全失敗時と同様にNoneを返す"""
        _patch_market_data(monkeypatch, cl, has_market_data=False)
        assert cl.get_price_change("XYZ") is None

    def test_unexpected_exception_returns_none(self, cl, monkeypatch):
        def _raise(ticker, days):
            raise RuntimeError("simulated failure")
        monkeypatch.setattr(cl, "HAS_MARKET_DATA", True)
        monkeypatch.setattr(cl, "_md_get_price_series", _raise)
        assert cl.get_price_change("XYZ") is None
