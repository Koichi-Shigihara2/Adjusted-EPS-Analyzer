"""
tests/test_pl_field_cross_accn_alignment.py

[[PL-FIELD-CROSS-ACCN-PERIOD-MISMATCH-1]]案bの回帰テスト。

SECParser._align_cost_of_revenue_to_revenue_period()が、revenueと
cost_of_revenueが異なるaccnから独立採用されている年度についてのみ、
revenueと同一accn・同一期間のcost_of_revenue候補が存在する場合に限り
置換することを確認する（欠損穴埋め型のゲート条件、既存の正しい値は
上書きしない）。

実行方法:
    python -m pytest tests/test_pl_field_cross_accn_alignment.py -v
"""

from common.sec_data.parser import SECParser


def _extracted(revenue: dict, cost_of_revenue: dict) -> dict:
    """{year: {"val":..., "accn":...}} からextracted構造を組み立てる"""
    def _build(field_map):
        annual = {y: v["val"] for y, v in field_map.items()}
        prov = {y: {"accn": v["accn"], "filed": v.get("filed", ""),
                     "is_own_data": v.get("is_own_data", True), "fy_tag": y}
                for y, v in field_map.items()}
        return {"annual": annual, "quarterly": {}, "_annual_provenance": prov}

    return {
        "revenue": _build(revenue),
        "cost_of_revenue": _build(cost_of_revenue),
    }


def _us_gaap_entry(accn, start, end, val, tag="Revenues"):
    return {tag: {"units": {"USD": [
        {"accn": accn, "start": start, "end": end, "val": val, "filed": "2020-01-01"}
    ]}}}


def _merge_us_gaap(*dicts):
    merged = {}
    for d in dicts:
        for tag, tagdata in d.items():
            merged.setdefault(tag, {"units": {"USD": []}})
            merged[tag]["units"]["USD"].extend(tagdata["units"]["USD"])
    return merged


def test_aligns_cost_of_revenue_when_revenue_accn_has_matching_candidate():
    """revenue/cost_of_revenueが別accnで、revenueと同一accn・同一期間に
    正しいCostOfRevenue候補が存在する場合、そちらへ置換される
    （CRM実データ相当の簡略版: 別accnの誤った値から正しい値へ）"""
    extracted = _extracted(
        revenue={2013: {"val": 3050195000, "accn": "accn_rev_2013"}},
        cost_of_revenue={2013: {"val": 968428000, "accn": "accn_cogs_wrong"}},
    )
    us_gaap = _merge_us_gaap(
        _us_gaap_entry("accn_rev_2013", "2012-02-01", "2013-01-31", 3050195000, tag="Revenues"),
        _us_gaap_entry("accn_rev_2013", "2012-02-01", "2013-01-31", 683579000, tag="CostOfRevenue"),
    )
    parser = SECParser()
    parser._align_cost_of_revenue_to_revenue_period(extracted, us_gaap)

    assert extracted["cost_of_revenue"]["annual"][2013] == 683579000
    prov = extracted["cost_of_revenue"]["_annual_provenance"][2013]
    assert prov["accn"] == "accn_rev_2013"
    assert prov["accn_aligned"] is True


def test_does_not_touch_already_aligned_years():
    """revenue/cost_of_revenueが既に同一accnの場合は何もしない（ゲート条件）"""
    extracted = _extracted(
        revenue={2020: {"val": 1000, "accn": "accn_a"}},
        cost_of_revenue={2020: {"val": 400, "accn": "accn_a"}},
    )
    us_gaap = _merge_us_gaap(
        _us_gaap_entry("accn_a", "2019-01-01", "2020-01-01", 1000, tag="Revenues"),
        _us_gaap_entry("accn_a", "2019-01-01", "2020-01-01", 999, tag="CostOfRevenue"),
    )
    parser = SECParser()
    parser._align_cost_of_revenue_to_revenue_period(extracted, us_gaap)

    # 既にrevenueと同一accnのため、us_gaap内に別の値(999)があっても変更しない
    assert extracted["cost_of_revenue"]["annual"][2020] == 400
    assert 2020 not in extracted["cost_of_revenue"]["_annual_provenance"] or \
        "accn_aligned" not in extracted["cost_of_revenue"]["_annual_provenance"][2020]


def test_keeps_current_value_when_no_candidate_in_revenue_accn():
    """revenueのaccn内に一致するcost_of_revenue候補が存在しない場合は現状維持"""
    extracted = _extracted(
        revenue={2019: {"val": 5000, "accn": "accn_rev"}},
        cost_of_revenue={2019: {"val": 2000, "accn": "accn_other"}},
    )
    us_gaap = _merge_us_gaap(
        _us_gaap_entry("accn_rev", "2018-01-01", "2019-01-01", 5000, tag="Revenues"),
        # accn_rev内にCostOfRevenue等のタグが一切存在しない
    )
    parser = SECParser()
    parser._align_cost_of_revenue_to_revenue_period(extracted, us_gaap)

    assert extracted["cost_of_revenue"]["annual"][2019] == 2000
    prov = extracted["cost_of_revenue"]["_annual_provenance"][2019]
    assert prov["accn"] == "accn_other"


def test_skips_when_aligned_value_equals_current_value():
    """置換後の値が現状と同じ場合は無用な書き換えをしない（provenanceのaccn_aligned付与も行わない）"""
    extracted = _extracted(
        revenue={2021: {"val": 100, "accn": "accn_rev"}},
        cost_of_revenue={2021: {"val": 40, "accn": "accn_other"}},
    )
    us_gaap = _merge_us_gaap(
        _us_gaap_entry("accn_rev", "2020-01-01", "2021-01-01", 100, tag="Revenues"),
        _us_gaap_entry("accn_rev", "2020-01-01", "2021-01-01", 40, tag="CostOfRevenue"),
    )
    parser = SECParser()
    parser._align_cost_of_revenue_to_revenue_period(extracted, us_gaap)

    assert extracted["cost_of_revenue"]["annual"][2021] == 40
    prov = extracted["cost_of_revenue"]["_annual_provenance"][2021]
    assert prov.get("accn") == "accn_other"  # 元のprovenanceのまま（上書きしていない）


def test_handles_multiple_years_independently():
    """複数年度が混在する場合、対象年度のみ個別に置換される"""
    extracted = _extracted(
        revenue={
            2019: {"val": 5000, "accn": "accn_rev_2019"},
            2020: {"val": 6000, "accn": "accn_rev_2020"},
        },
        cost_of_revenue={
            2019: {"val": 2000, "accn": "accn_rev_2019"},  # 既に一致（対象外）
            2020: {"val": 2500, "accn": "accn_other_2020"},  # 不一致（対象）
        },
    )
    us_gaap = _merge_us_gaap(
        _us_gaap_entry("accn_rev_2019", "2018-01-01", "2019-01-01", 5000, tag="Revenues"),
        _us_gaap_entry("accn_rev_2020", "2019-01-01", "2020-01-01", 6000, tag="Revenues"),
        _us_gaap_entry("accn_rev_2020", "2019-01-01", "2020-01-01", 2300, tag="CostOfRevenue"),
    )
    parser = SECParser()
    parser._align_cost_of_revenue_to_revenue_period(extracted, us_gaap)

    assert extracted["cost_of_revenue"]["annual"][2019] == 2000  # 変化なし
    assert extracted["cost_of_revenue"]["annual"][2020] == 2300  # 置換された
    assert extracted["cost_of_revenue"]["_annual_provenance"][2020]["accn_aligned"] is True


def test_noop_when_fields_absent():
    """revenue/cost_of_revenueのいずれかのフィールド自体が存在しない場合は
    何もしない（例外を送出しない）"""
    parser = SECParser()
    extracted = {"revenue": {"annual": {2020: 100}, "_annual_provenance": {}}}
    parser._align_cost_of_revenue_to_revenue_period(extracted, {})  # no KeyError


def test_ignores_non_annual_duration_candidates():
    """revenueのaccn内に候補タグはあるが期間長が340-380日でない
    （四半期等）場合は対象外として現状維持する"""
    extracted = _extracted(
        revenue={2022: {"val": 900, "accn": "accn_rev"}},
        cost_of_revenue={2022: {"val": 300, "accn": "accn_other"}},
    )
    us_gaap = _merge_us_gaap(
        _us_gaap_entry("accn_rev", "2021-01-01", "2022-01-01", 900, tag="Revenues"),
        _us_gaap_entry("accn_rev", "2021-10-01", "2022-01-01", 250, tag="CostOfRevenue"),  # 92日、四半期相当
    )
    parser = SECParser()
    parser._align_cost_of_revenue_to_revenue_period(extracted, us_gaap)

    assert extracted["cost_of_revenue"]["annual"][2022] == 300
