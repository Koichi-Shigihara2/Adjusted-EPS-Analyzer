"""
tests/test_gross_profit_backfill.py

[[LAYER3-GROSSPROFIT-BACKFILL-PROD-UNREACHED-1]]①の回帰テスト。

SECParser._backfill_gross_profit_from_revenue_cogs()が、標準タグから
gross_profitを取得できない年度についてのみrevenue-cost_of_revenueで
逆算した値を採用し、本番annual_YYYY.jsonへ書き戻すことを確認する。

実行方法:
    python -m pytest tests/test_gross_profit_backfill.py -v
"""

from common.sec_data.parser import SECParser


def _extracted(fields: dict) -> dict:
    """{field_name: {year: val}} からextracted構造を組み立てる（provenanceは空）"""
    extracted = {}
    for field, year_map in fields.items():
        extracted[field] = {
            "annual": dict(year_map), "quarterly": {}, "_annual_provenance": {},
        }
    return extracted


def test_backfill_fills_missing_gross_profit_from_revenue_minus_cogs():
    """gross_profitが欠損している年度は、revenue-cost_of_revenueの逆算値で埋められる"""
    extracted = _extracted({
        "gross_profit": {},
        "revenue": {2010: 1644200000},
        "cost_of_revenue": {2010: 1148100000},
    })
    parser = SECParser()
    parser._backfill_gross_profit_from_revenue_cogs(extracted)
    assert extracted["gross_profit"]["annual"][2010] == 496100000
    prov = extracted["gross_profit"]["_annual_provenance"][2010]
    assert prov["derived"] is True
    assert prov["is_own_data"] is False


def test_backfill_does_not_overwrite_existing_gross_profit():
    """標準タグから既に取得できているgross_profitは上書きしない（欠損の穴埋めのみ）"""
    extracted = _extracted({
        "gross_profit": {2020: 13023000000},
        "revenue": {2020: 26153000000},
        "cost_of_revenue": {2020: 7818000000},
    })
    parser = SECParser()
    parser._backfill_gross_profit_from_revenue_cogs(extracted)
    assert extracted["gross_profit"]["annual"][2020] == 13023000000
    # 標準タグ値を維持したままなのでderived provenanceは付与されない
    assert 2020 not in extracted["gross_profit"]["_annual_provenance"]


def test_backfill_skips_year_when_revenue_missing():
    """revenue・cost_of_revenueのいずれかが欠損している年度は対象外
    （Predecessor/Successor型で両方Noneになる年度が自動的に除外されることの確認）"""
    extracted = _extracted({
        "gross_profit": {},
        "revenue": {},
        "cost_of_revenue": {2019: 100},
    })
    parser = SECParser()
    parser._backfill_gross_profit_from_revenue_cogs(extracted)
    assert extracted["gross_profit"]["annual"] == {}


def test_backfill_skips_year_when_cost_of_revenue_missing():
    extracted = _extracted({
        "gross_profit": {},
        "revenue": {2019: 100},
        "cost_of_revenue": {},
    })
    parser = SECParser()
    parser._backfill_gross_profit_from_revenue_cogs(extracted)
    assert extracted["gross_profit"]["annual"] == {}


def test_backfill_noop_when_fields_absent():
    """revenue/cost_of_revenue/gross_profitのいずれかのフィールド自体が
    存在しない場合は何もしない（例外を送出しない）"""
    parser = SECParser()
    extracted = {"revenue": {"annual": {2020: 100}, "_annual_provenance": {}}}
    parser._backfill_gross_profit_from_revenue_cogs(extracted)  # no KeyError


def test_backfill_handles_multiple_years_independently():
    """複数年度が混在する場合、欠損年度のみ個別に埋められる"""
    extracted = _extracted({
        "gross_profit": {2019: 500},
        "revenue": {2019: 1000, 2020: 2000},
        "cost_of_revenue": {2019: 400, 2020: 1200},
    })
    parser = SECParser()
    parser._backfill_gross_profit_from_revenue_cogs(extracted)
    assert extracted["gross_profit"]["annual"][2019] == 500  # 既存値を維持
    assert extracted["gross_profit"]["annual"][2020] == 800  # 逆算で新規追加
    assert 2019 not in extracted["gross_profit"]["_annual_provenance"]
    assert extracted["gross_profit"]["_annual_provenance"][2020]["derived"] is True
