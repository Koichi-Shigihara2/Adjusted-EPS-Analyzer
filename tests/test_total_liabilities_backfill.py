"""
tests/test_total_liabilities_backfill.py

[[TOTAL-LIABILITIES-FALLBACK-TAG-DESIGN-FLAW-1]]の回帰テスト。

SECParser._backfill_total_liabilities_via_identity()が、XBRL_MAPPING
["total_liabilities"]の2番目の候補LiabilitiesAndStockholdersEquityが
誤採用された年度（total_liabilities==total_assetsという数学的シグネチャ
で検知）についてのみ、貸借対照表恒等式（total_assets-stockholders_equity）
で逆算した値に置き換えることを確認する。

実行方法:
    python -m pytest tests/test_total_liabilities_backfill.py -v
"""

from common.sec_data.parser import SECParser


def _extracted(fields: dict, provenance: dict = None) -> dict:
    """{field_name: {year: val}} からextracted構造を組み立てる"""
    provenance = provenance or {}
    extracted = {}
    for field, year_map in fields.items():
        extracted[field] = {
            "annual": dict(year_map), "quarterly": {},
            "_annual_provenance": dict(provenance.get(field, {})),
        }
    return extracted


def test_backfill_replaces_wrong_value_when_tl_equals_ta():
    """total_liabilities == total_assets（かつequity!=0）の年度は恒等式逆算値に置換される
    （KULR(2019)実データ相当: Assets=236766, Equity=-796965, 誤値=236766 → 逆算1033731）"""
    extracted = _extracted({
        "total_liabilities": {2019: 236766},
        "total_assets": {2019: 236766},
        "stockholders_equity": {2019: -796965},
    })
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    assert extracted["total_liabilities"]["annual"][2019] == 1033731
    prov = extracted["total_liabilities"]["_annual_provenance"][2019]
    assert prov["derived"] is True
    assert prov["is_own_data"] is False


def test_backfill_does_not_touch_correct_value():
    """total_liabilities != total_assetsの正常な年度は一切変更しない"""
    extracted = _extracted({
        "total_liabilities": {2020: 500},
        "total_assets": {2020: 1000},
        "stockholders_equity": {2020: 500},
    })
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    assert extracted["total_liabilities"]["annual"][2020] == 500
    assert 2020 not in extracted["total_liabilities"]["_annual_provenance"]


def test_backfill_skips_when_stockholders_equity_is_zero():
    """stockholders_equity==0の場合はtotal_liabilities==total_assetsが正当な値の
    可能性があるため対象外（誤検知回避）"""
    extracted = _extracted({
        "total_liabilities": {2021: 1000},
        "total_assets": {2021: 1000},
        "stockholders_equity": {2021: 0},
    })
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    assert extracted["total_liabilities"]["annual"][2021] == 1000
    assert 2021 not in extracted["total_liabilities"]["_annual_provenance"]


def test_backfill_skips_year_with_missing_fields():
    """3項目のいずれかがNoneの年度は対象外（例外を送出しない）"""
    extracted = _extracted({
        "total_liabilities": {2022: 1000},
        "total_assets": {},
        "stockholders_equity": {2022: 500},
    })
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    assert extracted["total_liabilities"]["annual"][2022] == 1000
    assert 2022 not in extracted["total_liabilities"]["_annual_provenance"]


def test_backfill_noop_when_fields_absent():
    """total_assets/stockholders_equity/total_liabilitiesのいずれかのフィールド
    自体が存在しない場合は何もしない（例外を送出しない）"""
    parser = SECParser()
    extracted = {"total_assets": {"annual": {2020: 100}, "_annual_provenance": {}}}
    parser._backfill_total_liabilities_via_identity(extracted)  # no KeyError


def test_backfill_records_source_is_own_data_true_when_both_sources_are_own_data():
    """逆算元のtotal_assets/stockholders_equityが両方本人データの場合、
    source_is_own_data=Trueが記録される"""
    extracted = _extracted(
        {
            "total_liabilities": {2019: 236766},
            "total_assets": {2019: 236766},
            "stockholders_equity": {2019: -796965},
        },
        provenance={
            "total_assets": {2019: {"is_own_data": True}},
            "stockholders_equity": {2019: {"is_own_data": True}},
        },
    )
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    prov = extracted["total_liabilities"]["_annual_provenance"][2019]
    assert prov["source_is_own_data"] is True


def test_backfill_records_source_is_own_data_false_when_either_source_is_not_own_data():
    """逆算元のtotal_assets/stockholders_equityのいずれかが本人データでない場合、
    source_is_own_data=Falseが記録される（AMZN(2008)等、各銘柄の最古記録年度で
    total_assets/stockholders_equity自体が後続filingの比較列由来のケース）"""
    extracted = _extracted(
        {
            "total_liabilities": {2008: 1000},
            "total_assets": {2008: 1000},
            "stockholders_equity": {2008: 400},
        },
        provenance={
            "total_assets": {2008: {"is_own_data": False}},
            "stockholders_equity": {2008: {"is_own_data": True}},
        },
    )
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    prov = extracted["total_liabilities"]["_annual_provenance"][2008]
    assert prov["source_is_own_data"] is False


def test_backfill_handles_multiple_years_independently():
    """複数年度が混在する場合、バグのシグネチャに該当する年度のみ個別に置換される"""
    extracted = _extracted({
        "total_liabilities": {2019: 500, 2020: 1000},
        "total_assets": {2019: 1000, 2020: 1000},
        "stockholders_equity": {2019: 500, 2020: 300},
    })
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    assert extracted["total_liabilities"]["annual"][2019] == 500  # 既存の正しい値を維持
    assert extracted["total_liabilities"]["annual"][2020] == 700  # 逆算値に置換(1000-300)
    assert 2019 not in extracted["total_liabilities"]["_annual_provenance"]
    assert extracted["total_liabilities"]["_annual_provenance"][2020]["derived"] is True


def test_backfill_handles_negative_derived_liabilities_correctly():
    """負の自己資本（債務超過）でも恒等式は符号に依存せず正しく機能する
    （ABBV/ADSK/AMD等の実データパターン相当）"""
    extracted = _extracted({
        "total_liabilities": {2018: 2000},
        "total_assets": {2018: 2000},
        "stockholders_equity": {2018: -8446},
    })
    parser = SECParser()
    parser._backfill_total_liabilities_via_identity(extracted)
    assert extracted["total_liabilities"]["annual"][2018] == 2000 - (-8446)
