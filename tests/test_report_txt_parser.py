"""
tests/test_report_txt_parser.py

common/screening/report_txt_parser.py::_all_tickers_with_report() の
ユニットテスト。ZS-TICKERS-LEAK-1（tanuki=falseの銘柄でもreport.txtが
存在すればスクリーニング対象に混入していた問題）の回帰テスト。

実行方法:
    python -m pytest tests/test_report_txt_parser.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from common.screening.report_txt_parser import _all_tickers_with_report  # noqa: E402


def _make_report(tmp_path, ticker: str) -> None:
    d = tmp_path / "docs" / "value-monitor" / "tanuki_valuation" / "data" / ticker
    d.mkdir(parents=True, exist_ok=True)
    (d / "report.txt").write_text(f"{ticker} INTEGRATED INVESTMENT REPORT\n", encoding="utf-8")


class TestAllTickersWithReport:
    """本番cik_lookup.csvのtanuki=false銘柄(ZS)を使い、report.txtが
    存在してもスクリーニング対象から除外されることを確認する"""

    def test_tanuki_false_ticker_excluded_even_with_report_txt(self, tmp_path):
        """ZS-TICKERS-LEAK-1: tanuki=falseのZSにreport.txtが残存していても
        対象銘柄リストに含まれないこと"""
        _make_report(tmp_path, "ZS")
        _make_report(tmp_path, "AAPL")
        result = _all_tickers_with_report(str(tmp_path))
        assert "ZS" not in result
        assert "AAPL" in result

    def test_tanuki_true_ticker_without_report_txt_excluded(self, tmp_path):
        """report.txtが存在しないtanuki=true銘柄は含まれない（両条件必須）"""
        result = _all_tickers_with_report(str(tmp_path))
        assert "AAPL" not in result

    def test_rklb_excluded_even_with_stale_report_txt(self, tmp_path):
        """RKLB（tanuki=false・report.txt残存）も同様に除外される
        （STALE-REPORT-CLEANUP-1対象銘柄との重複防止確認）"""
        _make_report(tmp_path, "RKLB")
        result = _all_tickers_with_report(str(tmp_path))
        assert "RKLB" not in result
