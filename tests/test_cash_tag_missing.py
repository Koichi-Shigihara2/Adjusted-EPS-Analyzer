"""
tests/test_cash_tag_missing.py

[[CASH-TAG-MISSING-1]]の回帰テスト。

tag_definitions.py::TAG_CANDIDATES["CASH_AND_EQUIVALENTS"]へASU 2016-18
対応タグ（CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents）
を追加し、GEV/SITM等（従来3タグのいずれも報告していない銘柄）の
cash_and_equivalents欠落を解消した。一方、CPRT/HEIは従来タグ
（CashAndCashEquivalentsAtCarryingValue）が引き続き機能しているにも
かかわらず新タグの方が新しい年度まで報告されているため、無対応だと
_extract_values_best_candidate()の「最新annual年が新しい候補が全期間の
勝者になる」設計により機能していた期間まで過大計上（制限付き現金混入）
に置き換わってしまう。quarterly.py::TICKER_RESTRICTIONSのcash_concept
上書きで両銘柄を既存タグへ固定し、この回帰を防いでいる。

実行方法:
    python -m pytest tests/test_cash_tag_missing.py -v
"""

from common.sec_data.parser import SECParser
from common.sec_data.tag_definitions import TAG_CANDIDATES
from common.sec_data.quarterly import TICKER_RESTRICTIONS


def _entry(start, end, val, fy, accn="0000000000-00-000001", fp="FY", form="10-K", filed=None):
    return {
        "start": start, "end": end, "val": val, "accn": accn,
        "fp": fp, "fy": fy, "form": form, "filed": filed or (end + "T00:00:00"),
    }


class TestNewTagRegisteredAsCandidate:
    def test_new_asu_tag_present_in_candidates(self):
        assert (
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
            in TAG_CANDIDATES["CASH_AND_EQUIVALENTS"]
        )


class TestGapFillingForTickersWithNoOtherCandidate:
    """GEV/SITM型: 従来3タグのいずれも報告しない銘柄では、新タグが唯一の
    候補として採用され、欠落が解消される"""

    def test_ticker_with_only_new_tag_gets_value(self):
        us_gaap = {
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": {"units": {"USD": [
                _entry("2024-01-01", "2024-12-31", 8205000000, fy=2024),
            ]}},
        }
        parser = SECParser()
        result = parser._extract_values_best_candidate(
            us_gaap, list(TAG_CANDIDATES["CASH_AND_EQUIVALENTS"]), fiscal_end_month=12,
            anchor_month=12, anchor_day=31, field_name="cash_and_equivalents",
        )
        assert result["annual"][2024] == 8205000000


class TestCprtHeiPinnedToOriginalTag:
    """CPRT/HEI型: 新タグの方が新しい年度まで報告されているケースの
    シミュレーション。オーバーライド無しではより新しい候補が全期間の
    勝者になってしまうが、cash_concept上書きで既存タグに固定される"""

    def _make_us_gaap(self):
        return {
            "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
                _entry("2019-01-01", "2019-12-31", 500_000_000, fy=2019),
            ]}},
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": {"units": {"USD": [
                _entry("2019-01-01", "2019-12-31", 520_000_000, fy=2019),
                _entry("2025-01-01", "2025-12-31", 900_000_000, fy=2025),
            ]}},
        }

    def test_without_override_fresher_tag_wins_and_changes_old_year(self):
        """オーバーライド無しでは新タグ（より新しい年度を持つ）が全期間の
        勝者になり、2019年の値も制限付き現金混入版に置き換わってしまう
        （これがCPRT/HEIで発生していた回帰リスクそのもの）"""
        us_gaap = self._make_us_gaap()
        parser = SECParser()
        result = parser._extract_values_best_candidate(
            us_gaap,
            [
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            ],
            fiscal_end_month=12, anchor_month=12, anchor_day=31,
            field_name="cash_and_equivalents",
        )
        assert result["annual"][2019] == 520_000_000  # 過大計上版に置き換わる

    def test_cprt_and_hei_have_cash_concept_override(self):
        assert TICKER_RESTRICTIONS["CPRT"]["cash_concept"] == "CashAndCashEquivalentsAtCarryingValue"
        assert TICKER_RESTRICTIONS["HEI"]["cash_concept"] == "CashAndCashEquivalentsAtCarryingValue"

    def test_with_override_pinned_tag_preserves_old_value(self):
        """cash_concept上書き適用後（xbrl_keysを単一タグに絞る、parser.py
        本体の配線と同じ操作）は2019年の値が元のまま保たれる"""
        us_gaap = self._make_us_gaap()
        parser = SECParser()
        result = parser._extract_values_best_candidate(
            us_gaap,
            ["CashAndCashEquivalentsAtCarryingValue"],  # cash_concept適用後の状態
            fiscal_end_month=12, anchor_month=12, anchor_day=31,
            field_name="cash_and_equivalents",
        )
        assert result["annual"][2019] == 500_000_000
        assert 2025 not in result["annual"]  # 新タグは参照しないため2025は増えない
