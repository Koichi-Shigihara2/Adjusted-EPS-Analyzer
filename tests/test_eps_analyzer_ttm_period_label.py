"""
tests/test_eps_analyzer_ttm_period_label.py

[[NETINCOME-DUAL-PIPELINE-1]]: EPS Analyzer::calculate_ttm()のperiod文字列に
"TTM "を明示的に前置したことの回帰テスト。STONKS SILOの単年度net_income_fy
との混同を防ぐ目的（NAMING_CONVENTIONS.md規則2）。

net_incomeキー自体は改名しない方針（stock.htmlのupdateChart()にttm[].
net_incomeへの直接参照が存在しないことを事前確認済みだが、より安全な
選択肢としてキー名を維持）。

実行方法:
    python -m pytest tests/test_eps_analyzer_ttm_period_label.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import src.value.adjusted_eps_analyzer.pipeline as aea_pipeline  # noqa: E402


def _make_quarter(filing_date, gaap_net_income, net_adjustment_total=0.0, diluted_shares_used=1_000_000):
    return {
        "filing_date": filing_date,
        "gaap_net_income": gaap_net_income,
        "net_adjustment_total": net_adjustment_total,
        "diluted_shares_used": diluted_shares_used,
    }


class TestCalculateTtmPeriodLabel:
    def test_period_string_starts_with_ttm_prefix(self):
        """periodが"TTM "で始まり、既存の"{start} to {end}"形式は維持される"""
        quarters = [
            _make_quarter("2025-03-31", 10_000_000),
            _make_quarter("2025-06-30", 12_000_000),
            _make_quarter("2025-09-30", 11_000_000),
            _make_quarter("2025-12-31", 15_000_000),
        ]
        result = aea_pipeline.calculate_ttm(quarters, end_idx=3)
        assert result is not None
        assert result["period"] == "TTM 2025-03-31 to 2025-12-31"
        assert result["period"].startswith("TTM ")

    def test_frontend_end_date_parsing_unaffected_by_prefix(self):
        """stock.htmlのitem.period.split(' to ')[1]相当のパース
        （末尾日付抽出）がプレフィックス追加後も正しく機能する"""
        quarters = [
            _make_quarter("2024-01-01", 1.0),
            _make_quarter("2024-04-01", 1.0),
            _make_quarter("2024-07-01", 1.0),
            _make_quarter("2024-10-01", 1.0),
        ]
        result = aea_pipeline.calculate_ttm(quarters, end_idx=3)
        end_date = result["period"].split(" to ")[1]
        assert end_date == "2024-10-01"

    def test_net_income_key_unchanged(self):
        """net_incomeキー自体は改名していない（stock.html未参照のため
        安全側の選択肢として維持、2026-08-13確認済み）"""
        quarters = [
            _make_quarter("2025-01-01", 100.0),
            _make_quarter("2025-04-01", 200.0),
            _make_quarter("2025-07-01", 300.0),
            _make_quarter("2025-10-01", 400.0),
        ]
        result = aea_pipeline.calculate_ttm(quarters, end_idx=3)
        assert "net_income" in result
        assert "net_income_ttm" not in result
        assert result["net_income"] == 1000.0

    def test_insufficient_quarters_returns_none(self):
        """既存の欠損ガード（4四半期未満）はプレフィックス追加後も不変"""
        quarters = [_make_quarter("2025-01-01", 100.0)]
        assert aea_pipeline.calculate_ttm(quarters, end_idx=0) is None
