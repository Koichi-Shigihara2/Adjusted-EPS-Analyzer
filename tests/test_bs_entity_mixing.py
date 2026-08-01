"""
tests/test_bs_entity_mixing.py

[[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階1の回帰テスト。

SPAC合併等で同一年度のBS(instant fact)フィールドが異なる法的実体（accn）
から混在採用され、current_assets>total_assets等の数学的矛盾を起こす
ケースを、SECParser._resolve_bs_entity_mixing()が安全側にNone化することを
確認する（実例: BBAI/RDW/RKLB/SOFI/VRT/ONDS/KULR(2016)）。

条件（4つすべて必須）:
  ①複数accnが混在
  ②本人データ(is_own_data=True)を提供するaccnが単一に定まる
  ③現に数学的矛盾が確認できる
  ④アンカーへの統一により実際に矛盾が解消する（KULR(2019)型の除外条件）

実行方法:
    python -m pytest tests/test_bs_entity_mixing.py -v
"""

from common.sec_data.parser import SECParser


def _extracted(fields: dict) -> dict:
    """{field_name: {year: (val, accn, is_own_data)}} からextracted構造を組み立てる"""
    extracted = {}
    for field, year_map in fields.items():
        annual = {}
        prov = {}
        for year, (val, accn, is_own_data) in year_map.items():
            annual[year] = val
            prov[year] = {"accn": accn, "filed": "2021-01-01", "is_own_data": is_own_data, "fy_tag": year}
        extracted[field] = {"annual": annual, "quarterly": {}, "_annual_provenance": prov}
    return extracted


# ============================================
# _bs_math_violations()
# ============================================

def test_bs_math_violations_detects_current_assets_over_total_assets():
    assert SECParser._bs_math_violations({"total_assets": 100, "current_assets": 200}) is True


def test_bs_math_violations_false_when_consistent():
    bs = {"total_assets": 1000, "current_assets": 200, "total_liabilities": 500,
          "current_liabilities": 100, "long_term_debt": 300, "short_term_debt": 50,
          "cash_and_equivalents": 80}
    assert SECParser._bs_math_violations(bs) is False


def test_bs_math_violations_tolerant_of_missing_values():
    """片方がNoneの組は比較不能として無視する（欠損データを誤検知しない）"""
    assert SECParser._bs_math_violations({"total_assets": None, "current_assets": 200}) is False
    assert SECParser._bs_math_violations({}) is False


# ============================================
# _resolve_bs_entity_mixing(): BBAI型（SPACシェル+Successor混在）
# ============================================

def test_resolve_bs_entity_mixing_bbai_type_nulls_non_anchor_fields():
    """BBAI(2020)型: SPACシェル由来の本人データ(total_assets等)をアンカーとし、
    Successor由来（本人データではない）のcurrent_assets等をNone化して
    current_assets>total_assetsの矛盾を解消する"""
    extracted = _extracted({
        "total_assets":         {2020: (380653, "SHELL-ACCN", True)},
        "stockholders_equity":  {2020: (-9096, "SHELL-ACCN", True)},
        "total_liabilities":    {2020: (389749, "SHELL-ACCN", True)},
        "cash_and_equivalents": {2020: (150000, "SHELL-ACCN", True)},
        "long_term_debt":       {2020: (105894000, "SUCCESSOR-ACCN", False)},
        "short_term_debt":      {2020: (1100000, "SUCCESSOR-ACCN", False)},
        "current_assets":       {2020: (34346000, "SUCCESSOR-ACCN", False)},
        "current_liabilities":  {2020: (12055000, "SUCCESSOR-ACCN", False)},
    })
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted)

    assert extracted["total_assets"]["annual"][2020] == 380653
    assert extracted["cash_and_equivalents"]["annual"][2020] == 150000
    assert extracted["current_assets"]["annual"].get(2020) is None
    assert extracted["current_liabilities"]["annual"].get(2020) is None
    assert extracted["long_term_debt"]["annual"].get(2020) is None
    assert extracted["short_term_debt"]["annual"].get(2020) is None
    # provenanceも合わせて除去される
    assert 2020 not in extracted["current_assets"]["_annual_provenance"]


def test_resolve_bs_entity_mixing_no_change_when_no_violation():
    """複数accn混在があっても数学的矛盾がなければ一切変更しない
    （105銘柄シミュレーションで確認した56件の正常系に相当）"""
    extracted = _extracted({
        "total_assets":      {2020: (1000, "ACCN-A", True)},
        "current_assets":    {2020: (200, "ACCN-A", True)},
        "short_term_debt":   {2020: (0, "ACCN-B", False)},
    })
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted)
    assert extracted["short_term_debt"]["annual"][2020] == 0
    assert extracted["total_assets"]["annual"][2020] == 1000


def test_resolve_bs_entity_mixing_no_change_when_single_accn():
    """単一accnのみ（複数accn混在なし）の場合は一切触れない"""
    extracted = _extracted({
        "total_assets":   {2020: (1000, "ACCN-A", True)},
        "current_assets": {2020: (2000, "ACCN-A", True)},  # 矛盾があってもaccnは単一
    })
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted)
    assert extracted["current_assets"]["annual"][2020] == 2000


def test_resolve_bs_entity_mixing_no_change_when_anchor_ambiguous():
    """本人データaccnが2個以上（一意に定まらない）場合は一切変更しない"""
    extracted = _extracted({
        "total_assets":   {2020: (100, "ACCN-A", True)},
        "current_assets": {2020: (200, "ACCN-B", True)},  # 別accnもis_own_data=True
    })
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted)
    assert extracted["total_assets"]["annual"][2020] == 100
    assert extracted["current_assets"]["annual"][2020] == 200


def test_resolve_bs_entity_mixing_kulr2019_type_untouched_when_null_does_not_resolve():
    """KULR(2019)型の回帰テスト: 矛盾の原因となる2フィールド(current_liabilities/
    total_liabilities)が既に同一accnから採用されており、accn混在（別フィールド
    のshort_term_debt）とは無関係な矛盾のケース。アンカーへの統一（短期負債の
    None化）では矛盾が解消しないため、一切変更しない（無関係フィールドの
    巻き添えNone化を防ぐ）"""
    extracted = _extracted({
        "total_assets":        {2019: (236766, "OWN-ACCN", True)},
        "total_liabilities":   {2019: (236766, "OWN-ACCN", True)},
        "current_liabilities": {2019: (1033731, "OWN-ACCN", True)},  # 同一accn内で既に矛盾
        "short_term_debt":     {2019: (0, "OTHER-ACCN", False)},
    })
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted)
    # short_term_debtが巻き添えでNone化されていないことを確認（KULR(2019)実データで
    # 確認された回帰: 条件④追加前はここがNoneになっていた）
    assert extracted["short_term_debt"]["annual"][2019] == 0
    assert extracted["current_liabilities"]["annual"][2019] == 1033731
