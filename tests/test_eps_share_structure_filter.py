"""
tests/test_eps_share_structure_filter.py

[[EPS-LOAR-1]]の回帰テスト。

LOARのIPO前4半期（diluted_shares=204,000、IPO後の約9,500万株とは
根本的に別物の株式構造）でadjusted_eps=11.29/106.37/-21.34/3.32/-36.50
という無意味な異常値が表示され続けていた問題への対応。

|EPS|>50等の絶対値閾値では一部（11.29・3.32等）を見逃すため、根本原因
（株式数がIPO後と別物）に直結する株式数基準（直近四半期のdiluted_shares
の1%未満）を採用した。

- apply_share_structure_filter(): 該当四半期にspecial_flags=
  ["SHARE_STRUCTURE_MISMATCH"]を付与する（削除はしない、監査可能性維持）
- calculate_ttm(): フラグ付き四半期を1件でも含む窓はNoneを返す
- aggregate_annual(): フラグ付き四半期を年度集計の対象から除外する
  （除外後4四半期未満の年度は既存ロジックで自然にスキップされる）

実行方法:
    python -m pytest tests/test_eps_share_structure_filter.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import src.value.adjusted_eps_analyzer.pipeline as aea_pipeline  # noqa: E402


def _make_quarter(filing_date, diluted_shares, adjusted_eps=0.1, gaap_net_income=1_000_000,
                   net_adjustment_total=0.0, fiscal_year=None):
    return {
        "filing_date": filing_date,
        "diluted_shares": diluted_shares,
        "diluted_shares_used": diluted_shares,
        "adjusted_eps": adjusted_eps,
        "gaap_net_income": gaap_net_income,
        "net_adjustment_total": net_adjustment_total,
        "fiscal_year": fiscal_year or int(filing_date[:4]),
        "special_flags": [],
        "special_notes": {},
        "adjustments": [],
    }


class TestApplyShareStructureFilter:
    def test_loar_like_pattern_flags_pre_ipo_quarters_only(self):
        """LOAR実データ相当（post-IPO 9四半期・pre-IPO 5四半期）で、
        pre-IPOの5件のみがフラグされ、post-IPOの9件は無傷であること"""
        quarters = (
            [_make_quarter(f"2023-{m:02d}-30", 204_000, adjusted_eps=v)
             for m, v in [(3, -36.5), (6, 3.32), (9, -21.34), (12, 106.37)]]
            + [_make_quarter("2024-03-31", 204_000, adjusted_eps=11.29)]
            + [_make_quarter(f"2024-{m:02d}-30", 89_000_000 + i * 1_000_000)
               for i, m in enumerate([6, 9, 12])]
            + [_make_quarter(f"2025-{m:02d}-30", 95_000_000 + i * 100_000)
               for i, m in enumerate([3, 6, 9, 12])]
            + [_make_quarter(f"2026-{m:02d}-30", 95_500_000 + i * 100_000)
               for i, m in enumerate([3, 6])]
        )
        result = aea_pipeline.apply_share_structure_filter("LOAR", quarters)

        flagged = [q for q in result if "SHARE_STRUCTURE_MISMATCH" in q["special_flags"]]
        unflagged = [q for q in result if "SHARE_STRUCTURE_MISMATCH" not in q["special_flags"]]
        assert len(flagged) == 5
        assert len(unflagged) == 9
        assert all(q["diluted_shares"] == 204_000 for q in flagged)
        assert all(q["diluted_shares"] > 80_000_000 for q in unflagged)

    def test_flagged_quarter_carries_explanatory_note(self):
        quarters = [
            _make_quarter("2023-03-31", 204_000, adjusted_eps=-36.5),
            _make_quarter("2026-06-30", 95_000_000),
        ]
        result = aea_pipeline.apply_share_structure_filter("LOAR", quarters)
        flagged = next(q for q in result if q["diluted_shares"] == 204_000)
        assert "share_structure_mismatch" in flagged["special_notes"]
        assert "204,000" in flagged["special_notes"]["share_structure_mismatch"]

    def test_no_mismatch_leaves_all_quarters_unflagged(self):
        """全四半期の株式数が近い場合（通常の非IPOティッカー）は
        一件も除外されないこと（既存挙動の非回帰確認）"""
        quarters = [_make_quarter(f"2025-{m:02d}-30", 10_000_000 + i * 50_000)
                    for i, m in enumerate([3, 6, 9, 12])]
        result = aea_pipeline.apply_share_structure_filter("TEST", quarters)
        assert all(q["special_flags"] == [] for q in result)

    def test_gradual_buyback_within_ratio_is_not_flagged(self):
        """大型自社株買いで株数が漸減するケース（LOAR型のような桁違いの
        別物ではない）は閾値1%を下回らない限り除外されないこと"""
        quarters = [
            _make_quarter("2024-03-31", 50_000_000),
            _make_quarter("2024-06-30", 45_000_000),
            _make_quarter("2024-09-30", 40_000_000),
            _make_quarter("2024-12-31", 36_000_000),  # 直近の72%、1%は下回らない
        ]
        result = aea_pipeline.apply_share_structure_filter("TEST", quarters)
        assert all(q["special_flags"] == [] for q in result)

    def test_empty_or_all_zero_shares_is_noop(self):
        assert aea_pipeline.apply_share_structure_filter("TEST", []) == []
        quarters = [_make_quarter("2024-01-01", 0)]
        result = aea_pipeline.apply_share_structure_filter("TEST", quarters)
        assert result[0]["special_flags"] == []


class TestCalculateTtmSkipsFlaggedWindows:
    def test_window_containing_flagged_quarter_returns_none(self):
        quarters = [
            _make_quarter("2023-12-31", 204_000),
            _make_quarter("2024-03-31", 204_000),
            _make_quarter("2024-06-30", 89_000_000),
            _make_quarter("2024-09-30", 91_000_000),
        ]
        quarters[0]["special_flags"] = ["SHARE_STRUCTURE_MISMATCH"]
        quarters[1]["special_flags"] = ["SHARE_STRUCTURE_MISMATCH"]
        assert aea_pipeline.calculate_ttm(quarters, 3) is None

    def test_window_without_flagged_quarter_computes_normally(self):
        quarters = [
            _make_quarter("2025-03-31", 95_000_000),
            _make_quarter("2025-06-30", 95_100_000),
            _make_quarter("2025-09-30", 95_200_000),
            _make_quarter("2025-12-31", 95_300_000),
        ]
        ttm = aea_pipeline.calculate_ttm(quarters, 3)
        assert ttm is not None
        assert ttm["diluted_shares"] == sum(q["diluted_shares_used"] for q in quarters) / 4


class TestAggregateAnnualExcludesFlaggedQuarters:
    def test_year_with_flagged_quarter_short_of_four_is_skipped(self):
        """LOAR FY2024相当: 1四半期がフラグ済みのため実質3四半期しか
        残らず、年度集計自体がスキップされること"""
        quarters = [
            _make_quarter("2024-03-31", 204_000, fiscal_year=2024),
            _make_quarter("2024-06-30", 89_000_000, fiscal_year=2024),
            _make_quarter("2024-09-30", 91_000_000, fiscal_year=2024),
            _make_quarter("2024-12-31", 91_500_000, fiscal_year=2024),
        ]
        quarters[0]["special_flags"] = ["SHARE_STRUCTURE_MISMATCH"]
        result = aea_pipeline.aggregate_annual(quarters)
        assert result == []

    def test_year_fully_flagged_is_skipped(self):
        """LOAR FY2023相当: 全4四半期がフラグ済みのため年度自体が
        annual.jsonに出力されないこと"""
        quarters = [_make_quarter(f"2023-{m:02d}-30", 204_000, fiscal_year=2023)
                    for m in [3, 6, 9, 12]]
        for q in quarters:
            q["special_flags"] = ["SHARE_STRUCTURE_MISMATCH"]
        result = aea_pipeline.aggregate_annual(quarters)
        assert result == []

    def test_clean_year_is_unaffected(self):
        quarters = [_make_quarter(f"2025-{m:02d}-30", 95_000_000, fiscal_year=2025)
                    for m in [3, 6, 9, 12]]
        result = aea_pipeline.aggregate_annual(quarters)
        assert len(result) == 1
        assert result[0]["year"] == "2025"
