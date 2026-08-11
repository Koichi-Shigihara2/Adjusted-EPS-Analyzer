"""
tests/test_extract_key_facts_share_fallback.py

ASTS-SHARES-OSCILLATION-1: extract_key_facts.py の株式数フォールバック回帰テスト。

株式数フォールバック④（現在株数の無条件代入）が、Q1〜Q3の一部四半期
だけXBRLタグが欠落している銘柄（ASTS/AVAV/RCAT）にも適用され、現在時点の
株数が過去の四半期に逆行伝播していた問題への対応。新設したフォールバック③
（隣接する実四半期からの引き継ぎ）が、フォールバック④より優先されることを確認する。

MARKETDATA-LAYER-CONSTRUCTION-1着手順序6: フォールバック④のデータソースを
yfinance直接呼び出しからcommon.market_data.reader.get_attributes()経由に
切替（2026-08-12）。本ファイルのpoison注入も`ekf._get_market_data_attributes`
のmonkeypatchに合わせて更新済み。

実行方法:
    python -m pytest tests/test_extract_key_facts_share_fallback.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


import src.value.adjusted_eps_analyzer.extract_key_facts as ekf  # noqa: E402


def _units(*items):
    return {"shares": list(items)}


def _fact(start, end, val, filed, form="10-Q"):
    return {"start": start, "end": end, "val": val, "filed": filed, "form": form}


def _patch_common(monkeypatch, facts):
    monkeypatch.setattr(ekf, "get_cik", lambda ticker: "0000000001")
    monkeypatch.setattr(ekf, "fetch_company_facts", lambda cik: facts)


def _patch_market_data_poison(monkeypatch, poison_shares):
    """フォールバック④（market_data属性の現在株数代入）が呼ばれた場合に検知できるよう、
    明確に分かる値（poison値）を返す偽attributesをekf._get_market_data_attributesの
    差し替えで注入する（ディスクI/O・ネットワーク呼び出しを回避）。"""
    fake_attrs = {"shares_outstanding": poison_shares}
    monkeypatch.setattr(ekf, "_get_market_data_attributes", lambda ticker: fake_attrs)
    return fake_attrs


_POISON_SHARES = 999_000_000  # market_data「現在株数」が誤って過去に伝播した場合に検知しやすい値


class TestNeighborCarryOverPrefersRealDataOverMarketData:
    """Q1〜Q3の一部だけdiluted sharesタグが欠落している場合、
    market_data代入(フォールバック④)ではなく隣接する実四半期(フォールバック③)が
    優先されること"""

    def test_missing_q1_inherits_from_q2_not_market_data(self, monkeypatch):
        """Q1のdiluted sharesタグが欠落 → 直後のQ2の実株数を引き継ぐ
        （market_dataのpoison値は使われない）"""
        diluted_items = [
            # Q1 (2023-03-31) は欠落（意図的に含めない）
            _fact("2023-04-01", "2023-06-30", 110_000_000, "2023-07-15"),
            _fact("2023-07-01", "2023-09-30", 120_000_000, "2023-10-15"),
        ]
        facts = {
            "facts": {
                "us-gaap": {
                    "NetIncomeLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", -5_000_000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", -4_000_000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", -3_000_000, "2023-10-15"),
                        )
                    },
                    "WeightedAverageNumberOfDilutedSharesOutstanding": {
                        "units": _units(*diluted_items)
                    },
                }
            }
        }
        _patch_common(monkeypatch, facts)
        _patch_market_data_poison(monkeypatch, _POISON_SHARES)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q1 = next(q for q in quarters if q["end"] == "2023-03-31")
        assert q1["diluted_shares"]["value"] == 110_000_000, (
            "Q1はQ2(直後)の実株数を引き継ぐべき（market_dataのpoison値が使われている）"
        )
        assert q1["diluted_shares"]["value"] != _POISON_SHARES

    def test_missing_q2_prefers_prior_quarter_over_next(self, monkeypatch):
        """中間のQ2が欠落 → 直前のQ1・直後のQ3どちらも実データがある場合は
        直前(Q1)を優先する"""
        diluted_items = [
            _fact("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),
            # Q2 (2023-06-30) は欠落
            _fact("2023-07-01", "2023-09-30", 120_000_000, "2023-10-15"),
        ]
        facts = {
            "facts": {
                "us-gaap": {
                    "NetIncomeLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", -5_000_000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", -4_000_000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", -3_000_000, "2023-10-15"),
                        )
                    },
                    "WeightedAverageNumberOfDilutedSharesOutstanding": {
                        "units": _units(*diluted_items)
                    },
                }
            }
        }
        _patch_common(monkeypatch, facts)
        _patch_market_data_poison(monkeypatch, _POISON_SHARES)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q2 = next(q for q in quarters if q["end"] == "2023-06-30")
        assert q2["diluted_shares"]["value"] == 100_000_000, "直前(Q1)の実株数を優先すべき"


class TestMarketDataFallbackStillAppliesWhenNoNeighborExists:
    """全期間でdiluted sharesタグが欠落している銘柄（Visa等、フォールバック④
    本来の対象）は、引き続きmarket_data代入にフォールバックすること（既存動作を維持）"""

    def test_all_quarters_missing_falls_back_to_market_data(self, monkeypatch):
        facts = {
            "facts": {
                "us-gaap": {
                    "NetIncomeLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", 5_000_000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", 4_000_000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", 3_000_000, "2023-10-15"),
                        )
                    },
                    # WeightedAverageNumberOfDilutedSharesOutstandingタグ自体が存在しない
                }
            }
        }
        _patch_common(monkeypatch, facts)
        _patch_market_data_poison(monkeypatch, _POISON_SHARES)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        assert quarters, "quartersが空であってはならない"
        for q in quarters:
            assert q["diluted_shares"]["value"] == _POISON_SHARES, (
                "隣接する実データが皆無の場合はmarket_data代入に落ちるべき（既存動作維持）"
            )


class TestQ4BlockGeneralizedNeighborLookup:
    """Q4ブロックの「Q3の実株数を引き継ぐ」既存パターンが、Q3も欠落している場合に
    より遠い四半期（Q2等）まで探索するよう一般化されたことの回帰テスト"""

    def test_q4_falls_back_to_q2_when_q3_diluted_shares_missing(self, monkeypatch):
        """Q1にのみ実株数があり、Q2・Q3は欠落。10-Kの年次株式数も取得できない
        ケースで、Q4計算時にQ3ではなくQ1(最も近い実データ)を引き継ぐこと"""
        diluted_items = [
            _fact("2023-01-01", "2023-03-31", 100_000_000, "2023-04-15"),
            # Q2, Q3 は欠落
        ]
        facts = {
            "facts": {
                "us-gaap": {
                    "NetIncomeLoss": {
                        "units": _units(
                            _fact("2023-01-01", "2023-03-31", 5_000_000, "2023-04-15"),
                            _fact("2023-04-01", "2023-06-30", 4_000_000, "2023-07-15"),
                            _fact("2023-07-01", "2023-09-30", 3_000_000, "2023-10-15"),
                            _fact("2023-01-01", "2023-12-31", 20_000_000, "2024-02-15", form="10-K"),
                        )
                    },
                    "WeightedAverageNumberOfDilutedSharesOutstanding": {
                        "units": _units(*diluted_items)
                        # 10-K分の年次エントリなし → diluted_val=0のままQ4ブロックの
                        # 引き継ぎロジックに到達する
                    },
                }
            }
        }
        _patch_common(monkeypatch, facts)
        _patch_market_data_poison(monkeypatch, _POISON_SHARES)

        quarters = ekf.extract_quarterly_facts("TESTCO", years=5)
        q4 = next(q for q in quarters if q["quarter"] == 4 and q["fiscal_year"] == 2023)
        assert q4["diluted_shares"]["value"] == 100_000_000, (
            "Q3が欠落している場合、Q4はより遠いQ1の実株数を引き継ぐべき"
        )
