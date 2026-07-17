"""
tests/test_extract_key_facts_split.py

src/value/adjusted_eps_analyzer/extract_key_facts.py::extract_quarterly_facts() の
希薄化後株式数(diluted_shares)選定ロジックのユニットテスト。

SPLIT-AUTO-CHECK-1: 同一期間に複数のfactが競合する場合（株式分割による比較年度
再掲等、SEC-TAG-FICO-CPRT-1と同型のfact競合パターン）に、Q1〜Q3用ループ
（以前は無条件上書き＝リスト末尾勝ち）とQ4専用ロジック（以前は先頭一致でbreak
＝リスト先頭勝ち）で異なる選定規則を使っていたため、どちらが採用されるかが
不整合だった。両方とも「filed日が最新のfactを優先」に統一したことの回帰テスト。

実行方法:
    python -m pytest tests/test_extract_key_facts_split.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import src.value.adjusted_eps_analyzer.extract_key_facts as ekf  # noqa: E402


def _units(*items, unit="shares"):
    """company_facts.json形式のunitsブロックを組み立てるヘルパー

    実際のSEC company_facts.jsonではNetIncomeLossは"USD"単位、
    WeightedAverageNumberOfDilutedSharesOutstandingは"shares"単位で
    格納されている（ARCH-DATA-1ステージ2: detect_fiscal_end_monthは
    parser.py::_detect_fiscal_end_month由来で"USD"単位のみを走査するため、
    NetIncomeLoss側はunit="USD"を明示する必要がある）
    """
    return {unit: list(items)}


def _fact(start, end, val, filed, form="10-Q"):
    return {"start": start, "end": end, "val": val, "filed": filed, "form": form}


def _build_facts(diluted_items, net_income_q, net_income_annual):
    """
    最小のcompany_facts.json形式フィクスチャを組み立てる。
    net_income_q: [(start, end, val, filed), ...] 3件（Q1〜Q3）
    net_income_annual: (start, end, val, filed) 1件（10-K、Q4計算用）
    """
    ni_items = [
        {"start": s, "end": e, "val": v, "filed": f, "form": "10-Q"}
        for s, e, v, f in net_income_q
    ]
    s, e, v, f = net_income_annual
    # fp="FY"は実際のSEC company_facts.jsonでは10-K annualエントリに常に付与されている
    # フィールド（ARCH-DATA-1ステージ2: common/sec_data/utils.py::detect_fiscal_end_month/
    # detect_fiscal_anchor_dateがform=="10-K"完全一致・fp=="FY"で判定するため必須）
    ni_items.append({"start": s, "end": e, "val": v, "filed": f, "form": "10-K", "fp": "FY"})

    return {
        "facts": {
            "us-gaap": {
                "NetIncomeLoss": {"units": _units(*ni_items, unit="USD")},
                "WeightedAverageNumberOfDilutedSharesOutstanding": {
                    "units": _units(*diluted_items)
                },
            }
        }
    }


def _patch_common(monkeypatch, facts):
    monkeypatch.setattr(ekf, "get_cik", lambda ticker: "0000000001")
    monkeypatch.setattr(ekf, "fetch_company_facts", lambda cik: facts)


class TestDilutedSharesLatestFiledWins:
    """Q1〜Q3・Q4いずれも、同一期間に競合するfactがある場合に
    filed日が最新のものを採用すること（先頭/末尾の位置に依存しない）"""

    def test_q1_prefers_latest_filed_even_when_listed_first(self, monkeypatch):
        """分割前値(古いfiled)がリスト先頭、分割後値(新しいfiled)がリスト末尾
        → 末尾（新しいfiled）が採用される"""
        diluted_items = [
            _fact("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),    # 古いfiled・先頭
            _fact("2023-01-01", "2023-03-31", 1_000_000_000, "2024-04-20"),  # 新しいfiled・末尾
            _fact("2023-04-01", "2023-06-30", 1_010_000_000, "2023-07-15"),
            _fact("2023-07-01", "2023-09-30", 1_020_000_000, "2023-10-15"),
        ]
        facts = _build_facts(
            diluted_items,
            net_income_q=[
                ("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),
                ("2023-04-01", "2023-06-30", 110_000_000, "2023-07-15"),
                ("2023-07-01", "2023-09-30", 120_000_000, "2023-10-15"),
            ],
            net_income_annual=("2023-01-01", "2023-12-31", 460_000_000, "2024-02-15"),
        )
        _patch_common(monkeypatch, facts)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q1 = next(q for q in quarters if q["end"] == "2023-03-31")
        assert q1["diluted_shares"]["value"] == 1_000_000_000

    def test_q1_prefers_latest_filed_even_when_listed_last(self, monkeypatch):
        """分割後値(新しいfiled)がリスト先頭、分割前値(古いfiled)がリスト末尾でも
        → 新しいfiledの方が採用される（リスト順ではなくfiled日で決まることの確認）"""
        diluted_items = [
            _fact("2023-01-01", "2023-03-31", 1_000_000_000, "2024-04-20"),  # 新しいfiled・先頭
            _fact("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),    # 古いfiled・末尾
            _fact("2023-04-01", "2023-06-30", 1_010_000_000, "2023-07-15"),
            _fact("2023-07-01", "2023-09-30", 1_020_000_000, "2023-10-15"),
        ]
        facts = _build_facts(
            diluted_items,
            net_income_q=[
                ("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),
                ("2023-04-01", "2023-06-30", 110_000_000, "2023-07-15"),
                ("2023-07-01", "2023-09-30", 120_000_000, "2023-10-15"),
            ],
            net_income_annual=("2023-01-01", "2023-12-31", 460_000_000, "2024-02-15"),
        )
        _patch_common(monkeypatch, facts)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q1 = next(q for q in quarters if q["end"] == "2023-03-31")
        assert q1["diluted_shares"]["value"] == 1_000_000_000

    def test_q4_prefers_latest_filed_annual_fact_not_first_in_list(self, monkeypatch):
        """Q4（10-K由来）でも、リスト先頭ではなくfiled日が最新のfactが採用される
        （NVDA 2024-01-28四半期で確認された実害パターンの回帰テスト）"""
        diluted_items = [
            _fact("2023-01-01", "2023-12-31", 103_000_000, "2024-02-15", form="10-K"),   # 先頭・古いfiled
            _fact("2023-01-01", "2023-12-31", 1_030_000_000, "2025-02-20", form="10-K"),  # 末尾・新しいfiled
            _fact("2023-01-01", "2023-03-31", 1_000_000_000, "2023-04-15"),
            _fact("2023-04-01", "2023-06-30", 1_010_000_000, "2023-07-15"),
            _fact("2023-07-01", "2023-09-30", 1_020_000_000, "2023-10-15"),
        ]
        facts = _build_facts(
            diluted_items,
            net_income_q=[
                ("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),
                ("2023-04-01", "2023-06-30", 110_000_000, "2023-07-15"),
                ("2023-07-01", "2023-09-30", 120_000_000, "2023-10-15"),
            ],
            net_income_annual=("2023-01-01", "2023-12-31", 460_000_000, "2024-02-15"),
        )
        _patch_common(monkeypatch, facts)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q4 = next(q for q in quarters if q["end"] == "2023-12-31" and q.get("quarter") == 4)
        assert q4["diluted_shares"]["value"] == 1_030_000_000

    def test_production_nvda_2024_q4_no_longer_pre_split(self, monkeypatch):
        """本番相当のケース: NVDA 2024-01-28四半期がsplit前株数（約2.49B）ではなく
        分割後株数（約24.94B）になっていること（実データではなくextract_quarterly_facts
        のロジックのみを、実際に確認済みのSEC生ファクト値で検証する）"""
        diluted_items = [
            _fact("2023-01-30", "2024-01-28", 2494000000, "2024-02-21", form="10-K"),
            _fact("2023-01-30", "2024-01-28", 24940000000, "2025-02-26", form="10-K"),
            _fact("2023-01-30", "2024-01-28", 24940000000, "2026-02-25", form="10-K"),
            _fact("2023-04-29", "2023-07-30", 24994000000, "2023-08-23"),
            _fact("2023-07-31", "2023-10-29", 24940000000, "2023-11-21"),
            _fact("2023-01-30", "2023-04-30", 2490000000, "2023-05-26"),
        ]
        facts = _build_facts(
            diluted_items,
            net_income_q=[
                ("2023-01-30", "2023-04-30", 2043000000, "2023-05-26"),
                ("2023-05-01", "2023-07-30", 6188000000, "2023-08-23"),
                ("2023-07-31", "2023-10-29", 9243000000, "2023-11-21"),
            ],
            net_income_annual=("2023-01-30", "2024-01-28", 29760000000, "2024-02-21"),
        )
        _patch_common(monkeypatch, facts)

        quarters = ekf.extract_quarterly_facts("NVDA", years=5)
        q4 = next(q for q in quarters if q["end"] == "2024-01-28" and q.get("quarter") == 4)
        assert q4["diluted_shares"]["value"] == 24940000000
