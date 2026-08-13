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


def _make_analysis(overall_score, overall_verdict):
    """StonksAnalysis最小スタブ（dq/ra/ppは_to_dict()のdataclass判定を
    通すためだけの最小構成、値そのものは本テストの検証対象外）"""
    dq = analyzer_mod.DeficitQuality(latest_year=2025, revenue=100.0, net_income=-10.0)
    ra = analyzer_mod.RunwayAnalysis(
        latest_year=2025, cash=50.0, monthly_burn=-5.0, runway_months=10.0,
        ocf_annual=-60.0, capex_annual=-5.0,
    )
    pp = analyzer_mod.ProfitabilityPath()
    return analyzer_mod.StonksAnalysis(
        ticker="XYZ", years=[2025], deficit_quality=dq, runway=ra, profitability_path=pp,
        overall_score=overall_score, overall_verdict=overall_verdict,
    )


_spec_analyzer = importlib.util.spec_from_file_location(
    "stonks_silo_analyzer", os.path.join(_STONKS_SRC, "analyzer.py")
)
analyzer_mod = importlib.util.module_from_spec(_spec_analyzer)
sys.modules["stonks_silo_analyzer"] = analyzer_mod
_spec_analyzer.loader.exec_module(analyzer_mod)


class TestRunNetCashSwitch:
    """[[NETCASH-DUAL-CALC-1]]: run()のnet_cash計算がSECReader.get_net_cash()
    経由に切り替わったこと（cash+STI-total_debtの独自計算を廃止）、
    overall_score/overall_verdictがnet_cashと無関係に不変であることの回帰テスト。
    """

    def _patch_common(self, monkeypatch, tmp_path, overall_score=50.0, overall_verdict="WATCH",
                       net_cash_available=True, net_cash_value=123.0):
        data = {
            "years": [2025],
            "records": {
                2025: {
                    "pl": {"revenue": 100.0, "net_income": -10.0, "revenue_sanitized": 100.0},
                },
            },
        }
        monkeypatch.setattr(sp, "stonks_tickers", lambda: ["XYZ"])
        monkeypatch.setattr(sp, "load_annual_data", lambda ticker, years=5: data)
        monkeypatch.setattr(
            sp.StonksAnalyzer, "analyze",
            lambda self, d: _make_analysis(overall_score, overall_verdict),
        )
        monkeypatch.setattr(
            sp, "fetch_valuation",
            lambda ticker: {
                "market_cap": 1000.0, "current_price": 10.0, "enterprise_value": 900.0,
                "total_debt": 200.0, "sector": "Technology", "industry": "Software",
                "fetched_at": "2026-08-13T00:00:00+00:00", "error": None,
            },
        )
        monkeypatch.setattr(
            sp.SECReader, "get_net_cash",
            lambda self, ticker, sector=None, industry=None: {
                "net_cash": net_cash_value, "available": net_cash_available,
            },
        )
        monkeypatch.setattr(sp, "load_all_normalized", lambda tickers: {})
        monkeypatch.setattr(sp, "compute_vectors", lambda normalized: {})
        monkeypatch.setattr(sp, "_OUTPUT_DIR", tmp_path)
        monkeypatch.setattr(sp, "_OUTPUT_FILE", tmp_path / "results.json")

    def test_net_cash_uses_sec_reader_value_directly(self, monkeypatch, tmp_path):
        """available=Trueの場合、net_cashはSECReader.get_net_cash()の
        戻り値がそのまま反映される（独自のcash+STI-total_debt計算はしない）"""
        self._patch_common(monkeypatch, tmp_path, net_cash_available=True, net_cash_value=999.5)
        result = sp.run(["XYZ"])
        assert result["tickers"]["XYZ"]["valuation"]["net_cash"] == 999.5
        # total_debtはfetch_valuation()の値がそのまま独立表示される（削除しない）
        assert result["tickers"]["XYZ"]["valuation"]["total_debt"] == 200.0

    def test_net_cash_none_when_sec_reader_unavailable(self, monkeypatch, tmp_path):
        """SECReader.get_net_cash()がavailable=Falseを返す場合
        （BS欠損等、SITM型）、net_cashはNoneになる"""
        self._patch_common(monkeypatch, tmp_path, net_cash_available=False, net_cash_value=0.0)
        result = sp.run(["XYZ"])
        assert result["tickers"]["XYZ"]["valuation"]["net_cash"] is None

    def test_overall_score_and_verdict_unaffected_by_net_cash(self, monkeypatch, tmp_path):
        """net_cashの値・availableに関わらずoverall_score/overall_verdictは
        StonksAnalyzer.analyze()の結果のみで決まる（net_cash無関係の確認）"""
        self._patch_common(
            monkeypatch, tmp_path, overall_score=77.0, overall_verdict="PROMISING",
            net_cash_available=False, net_cash_value=0.0,
        )
        result = sp.run(["XYZ"])
        assert result["tickers"]["XYZ"]["overall_score"] == 77.0
        assert result["tickers"]["XYZ"]["overall_verdict"] == "PROMISING"

    def test_sec_reader_called_with_sector_and_industry_from_valuation_fetcher(self, monkeypatch, tmp_path):
        """get_net_cash()にfetch_valuation()由来のsector/industryが
        渡されること（セクターガード適用に必須）"""
        self._patch_common(monkeypatch, tmp_path)
        captured = {}

        def _capture(self, ticker, sector=None, industry=None):
            captured["sector"] = sector
            captured["industry"] = industry
            return {"net_cash": 1.0, "available": True}

        monkeypatch.setattr(sp.SECReader, "get_net_cash", _capture)
        sp.run(["XYZ"])
        assert captured["sector"] == "Technology"
        assert captured["industry"] == "Software"
