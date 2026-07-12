"""
tests/test_stonks_silo_pipeline.py

discover/stonks-silo/src/pipeline.py::_filter_stonks_silo_tickers() の
ユニットテスト。FLAG-CONSUMER-AUDIT-2（CLI引数でticker明示指定時に
stonks_silo=trueフラグの検証を一切行わず無条件実行していた問題）の
回帰テスト。

実行方法:
    python -m pytest tests/test_stonks_silo_pipeline.py -v
"""

import importlib.util
import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_STONKS_SRC = os.path.join(_REPO_ROOT, "discover", "stonks-silo", "src")
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if _STONKS_SRC not in sys.path:
    sys.path.insert(0, _STONKS_SRC)

# src/value/tanuki_valuation/pipeline.py も "pipeline" という同名モジュールで
# sys.modulesにキャッシュされうるため（test_pipeline_logic.py等）、
# importlibで一意な名前を付けて明示的にロードする
_spec = importlib.util.spec_from_file_location(
    "stonks_silo_pipeline", os.path.join(_STONKS_SRC, "pipeline.py")
)
sp = importlib.util.module_from_spec(_spec)
sys.modules["stonks_silo_pipeline"] = sp
_spec.loader.exec_module(sp)


class TestFilterStonksSiloTickers:
    """_filter_stonks_silo_tickers()がstonks_silo=falseの銘柄を除外し、
    stonks_silo=trueの銘柄はそのまま通すことを確認する"""

    def test_stonks_silo_false_ticker_excluded(self, monkeypatch, capsys):
        monkeypatch.setattr(sp, "stonks_tickers", lambda: ["ASTS", "BBAI"])
        result = sp._filter_stonks_silo_tickers(["ASTS", "AAPL"])
        assert result == ["ASTS"]
        captured = capsys.readouterr()
        assert "AAPL" in captured.out
        assert "警告" in captured.out

    def test_all_stonks_silo_true_tickers_no_warning(self, monkeypatch, capsys):
        monkeypatch.setattr(sp, "stonks_tickers", lambda: ["ASTS", "BBAI"])
        result = sp._filter_stonks_silo_tickers(["ASTS", "BBAI"])
        assert result == ["ASTS", "BBAI"]
        captured = capsys.readouterr()
        assert "警告" not in captured.out

    def test_all_excluded_returns_empty_list(self, monkeypatch, capsys):
        monkeypatch.setattr(sp, "stonks_tickers", lambda: ["ASTS"])
        result = sp._filter_stonks_silo_tickers(["AAPL", "MSFT"])
        assert result == []
        captured = capsys.readouterr()
        assert "AAPL" in captured.out and "MSFT" in captured.out

    def test_production_stonks_silo_false_ticker_excluded(self):
        """本番cik_lookup.csvのstonks_silo=false銘柄（AAPL）が
        実際に除外されることを確認する"""
        result = sp._filter_stonks_silo_tickers(["AAPL"])
        assert "AAPL" not in result
