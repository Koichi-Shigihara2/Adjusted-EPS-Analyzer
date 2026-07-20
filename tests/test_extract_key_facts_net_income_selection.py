"""
tests/test_extract_key_facts_net_income_selection.py

EPS-ANALYZER-NORMALIZE-SCOPE-1: net_income候補タグの共通化に伴う回帰テスト。

extract_key_facts.pyは以前、共有NET_INCOME_QUARTERLY_TAGS（freshness基準の
best_tag選定）で一度net_incomeを決定した後、内部の別リスト`net_income_priority`
（4タグ、上記と異なる優先順位）で無条件に上書きしていた。この上書きロジックは
「'us-gaap:NetIncomeLoss'」を探すが、その特定のキーは同ループの直前で
"特別扱い済み"として除外されており`data`辞書には決して現れないため、
NetIncomeLossAvailableToCommonStockholders・NetIncomeLossAttributableToParent
が存在しない銘柄（ABBV/XOM/WMT/VZ等、NetIncomeLossとProfitLossの両方を
申告する大型・成熟企業に多い）では常にProfitLoss（非支配持分込みの連結利益）に
フォールバックしてしまうバグがあった。

NetIncomeLossはUS-GAAP XBRLタクソノミ上「親会社に帰属する利益」を表す概念で
あり、EPS Analyzerの目的（1株当たり利益の分析）にはProfitLoss（非支配持分込み）
より適切。本テスト群は、NetIncomeLossとProfitLossが同一期間で両方申告されている
場合にNetIncomeLossが正しく採用されることを確認する（修正前はProfitLossが
誤って採用されていた）。

実行方法:
    python -m pytest tests/test_extract_key_facts_net_income_selection.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import src.value.adjusted_eps_analyzer.extract_key_facts as ekf  # noqa: E402
from common.sec_data.tag_definitions import TAG_CANDIDATES  # noqa: E402


def _units(*items, unit="USD"):
    return {unit: list(items)}


def _fact(start, end, val, filed, form="10-Q", fp=None):
    d = {"start": start, "end": end, "val": val, "filed": filed, "form": form}
    if fp is not None:
        d["fp"] = fp
    return d


def _patch_common(monkeypatch, facts):
    monkeypatch.setattr(ekf, "get_cik", lambda ticker: "0000000001")
    monkeypatch.setattr(ekf, "fetch_company_facts", lambda cik: facts)


class TestNetIncomeCandidatesSharedWithParserQuarterly:
    def test_tag_candidates_net_income_order(self):
        """TAG_CANDIDATES["NET_INCOME"]は既存3タグ（順序維持）+ EPS Analyzer
        固有だった3タグ（末尾）の計6タグであること"""
        assert TAG_CANDIDATES["NET_INCOME"] == (
            "NetIncomeLoss",
            "ProfitLoss",
            "NetIncomeLossAvailableToCommonStockholdersBasic",
            "NetIncomeLossAvailableToCommonStockholders",
            "NetIncomeLossAttributableToParent",
            "IncomeLossFromContinuingOperations",
        )


class TestNetIncomeLossPreferredOverProfitLoss:
    """NetIncomeLossとProfitLossが同一期間で両方申告されている場合、
    （ABBV/XOM/WMT/VZ等の実例パターン）NetIncomeLoss（親会社帰属）が
    採用されること。修正前は内部の矛盾したnet_income_priorityリストにより
    ProfitLoss（非支配持分込み）へ誤って上書きされていた"""

    def test_annual_prefers_net_income_loss(self, monkeypatch):
        facts = {
            "facts": {
                "us-gaap": {
                    "NetIncomeLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", 1000000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", 1100000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", 1200000, "2023-10-15"),
                            _fact("2023-01-01", "2023-12-31", 3179000000, "2024-02-15",
                                  form="10-K", fp="FY"),
                        )
                    },
                    "ProfitLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-12-31", 3180000000, "2024-02-15",
                                  form="10-K", fp="FY"),
                        )
                    },
                    "WeightedAverageNumberOfDilutedSharesOutstanding": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", 100_000_000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", 100_000_000, "2023-10-15"),
                            _fact("2023-01-01", "2023-12-31", 100_000_000, "2024-02-15",
                                  form="10-K", fp="FY"),
                            unit="shares",
                        )
                    },
                }
            }
        }
        _patch_common(monkeypatch, facts)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q4 = next(q for q in quarters if q["end"] == "2023-12-31" and q.get("quarter") == 4)
        # Q4は年次(annual_net)からQ1-Q3合計を差し引いた残差で計算される。
        # annual_netの採用元がNetIncomeLoss(3,179,000,000)であることを確認する
        # （ProfitLoss=3,180,000,000が採用されていれば残差がずれる）
        expected_q1q3_sum = 1000000 + 1100000 + 1200000
        expected_q4 = 3179000000 - expected_q1q3_sum
        assert q4["net_income"]["value"] == expected_q4, (
            "annual側もNetIncomeLoss（親会社帰属）が採用されるべき。ProfitLoss"
            "（非支配持分込み）への誤ったフォールバックが発生している"
        )

    def test_quarterly_prefers_net_income_loss(self, monkeypatch):
        facts = {
            "facts": {
                "us-gaap": {
                    "NetIncomeLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", 1000000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", 1100000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", 1200000, "2023-10-15"),
                            _fact("2023-01-01", "2023-12-31", 4600000, "2024-02-15",
                                  form="10-K", fp="FY"),
                        )
                    },
                    "ProfitLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", 1005000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", 1105000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", 1205000, "2023-10-15"),
                            _fact("2023-01-01", "2023-12-31", 4620000, "2024-02-15",
                                  form="10-K", fp="FY"),
                        )
                    },
                    "WeightedAverageNumberOfDilutedSharesOutstanding": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", 100_000_000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", 100_000_000, "2023-10-15"),
                            unit="shares",
                        )
                    },
                }
            }
        }
        _patch_common(monkeypatch, facts)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q1 = next(q for q in quarters if q["end"] == "2023-03-31")
        assert q1["net_income"]["value"] == 1000000, (
            "四半期net_incomeもNetIncomeLossが採用されるべき（ProfitLossではない）"
        )
