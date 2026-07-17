"""
tests/test_fy_tag_provenance.py

ARCH-DATA-1ステージ3（fyタグ裏取り）の回帰テスト。

common/sec_data/parser.py の {bs,pl,cf,shares,other}_provenance サイドカーに
追加した fy_tag フィールド（採用エントリの生XBRL fyタグ）が正しく記録されること、
および年度バケツキー（determine_fiscal_year()の計算結果）とfy_tagが食い違う
場合に fy_mismatches_out へ正しく記録されること（is_own_dataによる
severity分岐: True→要確認、False→info）を検証する。

実行方法:
    python -m pytest tests/test_fy_tag_provenance.py -v
"""

from common.sec_data.parser import SECParser


def _entry(start, end, val, fy, accn="0000000000-00-000001", fp="FY", form="10-K", filed=None):
    return {
        "start": start, "end": end, "val": val, "accn": accn,
        "fp": fp, "fy": fy, "form": form, "filed": filed or (end + "T00:00:00"),
    }


class TestFyTagSidecarBestCandidate:
    """_extract_values_best_candidate()（非merge_all_tagsフィールド）でfy_tagが
    provenanceサイドカーに正しく記録されること"""

    def test_fy_tag_recorded_when_fy_matches_computed_year(self):
        us_gaap = {
            "NetIncomeLoss": {"units": {"USD": [
                _entry("2020-01-01", "2020-12-31", 100, fy=2020),
            ]}},
        }
        parser = SECParser()
        result = parser._extract_values_best_candidate(
            us_gaap, ["NetIncomeLoss"], fiscal_end_month=12,
            anchor_month=12, anchor_day=31,
        )
        assert result["annual"][2020] == 100
        assert result["_annual_provenance"][2020]["fy_tag"] == 2020

    def test_fy_tag_recorded_even_when_it_mismatches_computed_year(self):
        """fyタグ自体は忠実に記録する（判定・除外は行わない。裏取りロジック側の責務）"""
        us_gaap = {
            "NetIncomeLoss": {"units": {"USD": [
                # CDNS型: end=2015-01-03はアンカー(12,31)に基づけばFY2014だが
                # fyタグは2015（企業側の誤り、またはSECの付番揺れを想定）
                _entry("2014-01-04", "2015-01-03", 200, fy=2015),
            ]}},
        }
        parser = SECParser()
        result = parser._extract_values_best_candidate(
            us_gaap, ["NetIncomeLoss"], fiscal_end_month=12,
            anchor_month=12, anchor_day=31,
        )
        assert result["annual"][2014] == 200
        assert result["_annual_provenance"][2014]["fy_tag"] == 2015


class TestFyTagSidecarMerged:
    """_extract_values_merged()（merge_all_tagsフィールド）でfy_tagが
    provenanceサイドカーに正しく記録されること"""

    def test_fy_tag_recorded_in_merged_path(self):
        us_gaap = {
            "Revenues": {"units": {"USD": [
                _entry("2014-01-04", "2015-01-03", 300, fy=2015),
            ]}},
        }
        parser = SECParser()
        result = parser._extract_values_merged(
            us_gaap, ["Revenues"], use_max=False, fiscal_end_month=12,
            anchor_month=12, anchor_day=31,
        )
        assert result["annual"][2014] == 300
        assert result["_annual_provenance"][2014]["fy_tag"] == 2015


class TestFyMismatchDetection:
    """fy_mismatches_out へのARCH-DATA-1ステージ3裏取り不一致記録の回帰テスト。
    is_own_dataによりseverityが info/要確認 に正しく分岐すること"""

    def test_no_mismatch_when_fy_matches_computed_year(self):
        us_gaap = {
            "NetIncomeLoss": {"units": {"USD": [
                _entry("2020-01-01", "2020-12-31", 100, fy=2020),
            ]}},
        }
        parser = SECParser()
        mismatches = []
        parser._extract_values_best_candidate(
            us_gaap, ["NetIncomeLoss"], fiscal_end_month=12,
            anchor_month=12, anchor_day=31, field_name="net_income",
            fy_mismatches_out=mismatches,
        )
        assert mismatches == []

    def test_no_mismatch_recorded_when_not_own_data(self):
        """accn_reportdate未提供（本人データ判定不可、is_own_data=False）の場合は
        記録されない（2026-07-17設計変更: 比較年度再掲エントリのfyタグは
        「その数値がどの10-Kに載っていたか」というfiling側の属性でしかなく、
        企業の申告ミスとは無関係な正常仕様のため、全105銘柄検証で4,434件・
        105銘柄というノイズになることが判明し対象外とした）"""
        us_gaap = {
            "NetIncomeLoss": {"units": {"USD": [
                _entry("2014-01-04", "2015-01-03", 200, fy=2015),
            ]}},
        }
        parser = SECParser()
        mismatches = []
        parser._extract_values_best_candidate(
            us_gaap, ["NetIncomeLoss"], fiscal_end_month=12,
            anchor_month=12, anchor_day=31, field_name="net_income",
            fy_mismatches_out=mismatches,
        )
        assert mismatches == []

    def test_mismatch_recorded_when_own_data(self):
        """accn_reportdateが一致する（本人データ、is_own_data=True）場合のみ
        記録される（fyタグ由来の値が実際に採用されているケース）。
        スキーマはfield/end_date/fy_tag/computed_yearのみ（is_own_data/severityは
        全件Trueで自明なため2026-07-17に撤去）"""
        us_gaap = {
            "NetIncomeLoss": {"units": {"USD": [
                _entry("2014-01-04", "2015-01-03", 200, fy=2015, accn="ACCN-A"),
            ]}},
        }
        parser = SECParser()
        mismatches = []
        parser._extract_values_best_candidate(
            us_gaap, ["NetIncomeLoss"], fiscal_end_month=12,
            anchor_month=12, anchor_day=31, field_name="net_income",
            accn_reportdate={"ACCN-A": "2015-01-03"},
            fy_mismatches_out=mismatches,
        )
        assert mismatches == [{
            "field": "net_income", "end_date": "2015-01-03",
            "fy_tag": 2015, "computed_year": 2014,
        }]

    def test_no_mismatches_recorded_when_fy_mismatches_out_is_none(self):
        """fy_mismatches_out省略時は記録処理自体が発生しない（既存呼び出し元との
        後方互換。CHECK-22ロジックへの影響がないことの回帰確認）"""
        us_gaap = {
            "NetIncomeLoss": {"units": {"USD": [
                _entry("2014-01-04", "2015-01-03", 200, fy=2015),
            ]}},
        }
        parser = SECParser()
        # fy_mismatches_out未指定でも例外なく動作すること
        result = parser._extract_values_best_candidate(
            us_gaap, ["NetIncomeLoss"], fiscal_end_month=12,
            anchor_month=12, anchor_day=31, field_name="net_income",
        )
        assert result["annual"][2014] == 200


class TestCheck22Unaffected:
    """CHECK-22（fyキー競合検知、collisions_out）がfy_tag/fy_mismatches_out追加の
    影響を受けないことの回帰テスト"""

    def test_fy_collision_still_detected_after_fy_tag_changes(self):
        """CRM/FCX型: 同一fyタグに複数の異なる本人end_dateが競合し、
        フォールバックで自然分離できるケースが引き続き正しく検知されること"""
        us_gaap = {
            "NetIncomeLoss": {"units": {"USD": [
                _entry("2018-01-01", "2018-12-31", 100, fy=2020, accn="ACCN-2018"),
                _entry("2019-01-01", "2019-12-31", 110, fy=2020, accn="ACCN-2019"),
            ]}},
        }
        parser = SECParser()
        collisions = []
        result = parser._extract_values_best_candidate(
            us_gaap, ["NetIncomeLoss"], fiscal_end_month=12,
            anchor_month=12, anchor_day=31, field_name="net_income",
            accn_reportdate={"ACCN-2018": "2018-12-31", "ACCN-2019": "2019-12-31"},
            collisions_out=collisions,
        )
        # フォールバックで自然分離: 2018年度分は2018に、2019年度分は2019に
        assert result["annual"].get(2018) == 100
        assert result["annual"].get(2019) == 110
        assert len(collisions) == 1
        assert collisions[0]["resolution"] == "fyタグ衝突だがフォールバック年度で自然分離"
