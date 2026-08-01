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


# ============================================
# [[SPAC-SHELL-BS-ENTITY-MIXING-1]]段階2: former_names区間一致による
# 矛盾未顕在化ケース（SPIR型）の事前検知
# ============================================

def test_report_date_in_former_name_window_inclusive_boundaries():
    """区間は両端含む（inclusive）。BBAI実データでreportDate="from"完全一致を確認済み"""
    fn = {"name": "Shell Co", "from": "2020-12-31T05:00:00.000Z", "to": "2021-12-07T05:00:00.000Z"}
    assert SECParser._report_date_in_former_name_window("2020-12-31", fn) is True  # from境界
    assert SECParser._report_date_in_former_name_window("2021-12-07", fn) is True  # to境界
    assert SECParser._report_date_in_former_name_window("2021-06-15", fn) is True  # 区間内
    assert SECParser._report_date_in_former_name_window("2020-12-30", fn) is False  # 区間外(前)
    assert SECParser._report_date_in_former_name_window("2021-12-08", fn) is False  # 区間外(後)


def test_report_date_in_former_name_window_tolerant_of_malformed_input():
    assert SECParser._report_date_in_former_name_window("", {"from": "2020-01-01", "to": "2020-12-31"}) is False
    assert SECParser._report_date_in_former_name_window("2020-06-01", {}) is False


def test_resolve_bs_entity_mixing_spir_type_detected_without_violation():
    """SPIR(2020)型: 数学的矛盾は存在しないが、アンカー候補accnのreportDateが
    former_names区間内にあるため、段階2条件③'で検知・None化される"""
    extracted = _extracted({
        "total_assets":        {2020: (231610511, "SHELL-ACCN", True)},
        "total_liabilities":   {2020: (32442098, "SHELL-ACCN", True)},
        "current_assets":      {2020: (1603187, "SHELL-ACCN", True)},
        "long_term_debt":      {2020: (26645000, "SUCCESSOR-ACCN", False)},  # 矛盾なし(<total_liabilities)
    })
    accn_reportdate = {"SHELL-ACCN": "2020-12-31"}
    former_names = [{"name": "NavSight Holdings, Inc.",
                      "from": "2020-06-26T04:00:00.000Z", "to": "2021-08-13T04:00:00.000Z"}]
    detections: list = []
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted, accn_reportdate=accn_reportdate,
                                      former_names=former_names, spac_detections_out=detections)

    assert extracted["long_term_debt"]["annual"].get(2020) is None
    assert extracted["total_assets"]["annual"][2020] == 231610511
    assert len(detections) == 1
    assert detections[0]["triggered_by"] == "former_names_window"
    assert detections[0]["nulled_fields"] == ["long_term_debt"]


def test_resolve_bs_entity_mixing_no_detection_without_former_names_data():
    """former_names未指定（省略時のデフォルト）では段階2は一切発火せず、
    矛盾のないケースは段階1と同様に無変更のまま（後方互換）"""
    extracted = _extracted({
        "total_assets":      {2020: (231610511, "SHELL-ACCN", True)},
        "total_liabilities": {2020: (32442098, "SHELL-ACCN", True)},
        "long_term_debt":    {2020: (26645000, "SUCCESSOR-ACCN", False)},
    })
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted)  # accn_reportdate/former_names省略
    assert extracted["long_term_debt"]["annual"][2020] == 26645000


def test_resolve_bs_entity_mixing_former_names_match_alone_insufficient_without_multi_accn():
    """former_names区間一致があっても、複数accn混在（条件①）が成立しなければ
    誤検知しない（単純な改名で全フィールドが単一accnのまま継続報告される
    RKLB型ケースを想定した安全側の確認）"""
    extracted = _extracted({
        "total_assets":      {2020: (1000, "SAME-ACCN", True)},
        "total_liabilities": {2020: (500, "SAME-ACCN", True)},
    })
    accn_reportdate = {"SAME-ACCN": "2020-12-31"}
    former_names = [{"name": "Old Co Name", "from": "2020-01-01", "to": "2021-01-01"}]
    detections: list = []
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted, accn_reportdate=accn_reportdate,
                                      former_names=former_names, spac_detections_out=detections)
    assert extracted["total_assets"]["annual"][2020] == 1000
    assert detections == []


def test_resolve_bs_entity_mixing_idempotent_when_violation_and_former_names_both_match():
    """BBAI型: 数学的矛盾（条件③）とformer_names一致（条件③'）が両方成立する
    場合でも、結果（None化されるフィールド）は条件③単独の場合と変わらない
    （冪等性）。detections には記録される（triggered_by="math_violation"）"""
    extracted = _extracted({
        "total_assets":        {2020: (380653, "SHELL-ACCN", True)},
        "total_liabilities":   {2020: (389749, "SHELL-ACCN", True)},
        "current_assets":      {2020: (34346000, "SUCCESSOR-ACCN", False)},  # 矛盾あり(>total_assets)
    })
    accn_reportdate = {"SHELL-ACCN": "2020-12-31"}
    former_names = [{"name": "GigCapital4, Inc.",
                      "from": "2020-12-31T05:00:00.000Z", "to": "2021-12-07T05:00:00.000Z"}]
    detections: list = []
    parser = SECParser()
    parser._resolve_bs_entity_mixing(extracted, accn_reportdate=accn_reportdate,
                                      former_names=former_names, spac_detections_out=detections)
    assert extracted["current_assets"]["annual"].get(2020) is None
    assert len(detections) == 1
    assert detections[0]["triggered_by"] == "math_violation"
