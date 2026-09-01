"""
tests/test_flag_consumer_audit_3.py

FLAG-CONSUMER-AUDIT-3: hypecore.py --batch/単体指定・
adjusted_eps_analyzer/pipeline.py --ticker が、CLI引数でticker明示指定時に
対応フラグ（hypecore=true / eps=true）を検証していなかった
問題（tanuki_valuation/pipeline.pyのCLI引数パスと同型のギャップ）の回帰テスト。

実行方法:
    python -m pytest tests/test_flag_consumer_audit_3.py -v
"""

import importlib.util
import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestHypecoreFilterTickers:
    """hypecore.py::_filter_hypecore_tickers()がhypecore=false銘柄を除外し、
    hypecore=trueの銘柄はそのまま通すことを確認する"""

    def _mod(self):
        return _load_module(
            "hypecore_flag_audit3",
            os.path.join(_REPO_ROOT, "src", "value", "hypecore", "hypecore.py"),
        )

    def test_excludes_ticker_not_in_hypecore_set(self, capsys):
        mod = self._mod()
        result = mod._filter_hypecore_tickers(["ENB", "PLTR"], ["PLTR", "NVDA"])
        assert result == ["PLTR"]
        captured = capsys.readouterr()
        assert "ENB" in captured.out
        assert "警告" in captured.out

    def test_all_included_no_warning(self, capsys):
        mod = self._mod()
        result = mod._filter_hypecore_tickers(["PLTR", "NVDA"], ["PLTR", "NVDA"])
        assert result == ["PLTR", "NVDA"]
        captured = capsys.readouterr()
        assert "警告" not in captured.out

    def test_production_enb_excluded(self):
        """本番cik_lookup.csvのhypecore=false銘柄（ENB）が実際に除外されること"""
        mod = self._mod()
        from common.sec_data.tickers import get_hypecore_tickers
        result = mod._filter_hypecore_tickers(["ENB"], get_hypecore_tickers())
        assert "ENB" not in result


class TestEpsAnalyzerFilterEpsTickers:
    """adjusted_eps_analyzer/pipeline.py::_filter_eps_tickers()の回帰テスト

    pipeline.pyは`from .extract_key_facts import ...`という相対importを
    使うため、importlib.util.spec_from_file_locationでは単独ロードできない
    （パッケージの一部として読み込む必要がある）。標準のパッケージimportを使う。
    """

    def _mod(self):
        import src.value.adjusted_eps_analyzer.pipeline as eps_pipeline
        return eps_pipeline

    def test_excludes_ticker_not_in_eps_set(self, capsys):
        mod = self._mod()
        result = mod._filter_eps_tickers(["ZS", "NVDA"], ["NVDA", "AAPL"])
        assert result == ["NVDA"]
        captured = capsys.readouterr()
        assert "ZS" in captured.out
        assert "警告" in captured.out

    def test_production_eps_false_ticker_excluded(self):
        """本番cik_lookup.csvのeps=false銘柄（ZS）が実際に除外されること"""
        mod = self._mod()
        from common.sec_data.tickers import get_eps_tickers
        result = mod._filter_eps_tickers(["ZS"], get_eps_tickers())
        assert "ZS" not in result
