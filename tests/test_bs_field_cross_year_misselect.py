"""
tests/test_bs_field_cross_year_misselect.py

[[PARSER-STOCKHOLDERS-EQUITY-CROSS-YEAR-MISSELECT-1]]の回帰テスト。

stockholders_equity（等のBS instant factフィールド）が、正しいaccn
（total_assets/total_liabilitiesと同一のfiling）ではなく、別年度・別
filingの無関係な値を誤って採用してしまう2つの独立したパターンを検証する:

- CRM型（2アンカー競合）: `_own_override_is_safe()`の既存accnベース短絡
  判定が、既存エントリの生fyタグと年度バケツの食い違い（fyタグ裏取り、
  CHECK-23と同種）を考慮せず、真に正しい本人データ候補からの上書きを
  誤ってブロックしていた。existing_fy_tag/own_fy_tagパラメータ追加で
  対応。
- VRT型（0アンカー）: stockholders_equityの本人データが皆無の年度で、
  フォールバック（_extract_single_key()の10-K/Aタイブレーク）が無関係な
  比較列の再表示値を誤って採用していた。新設
  _align_stockholders_equity_to_sibling_accn()で、total_assets/
  total_liabilitiesが共通採用したaccnの値を優先する形で対応。

WMT/DELL/CDNS/IOT/VZ向けの既存安全装置（tests/test_bs_entity_mixing.py・
tests/test_fy_tag_provenance.py等）が本修正で壊れていないことは、該当
テストファイルを個別に実行して別途確認する（本ファイルはCRM/VRT型自体の
fail-before/pass-after確認に特化する）。

実行方法:
    python -m pytest tests/test_bs_field_cross_year_misselect.py -v
"""

import os

from common.sec_data.parser import SECParser

_DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common", "sec_data", "data"))


def _entry(start, end, val, fy, accn, fp="FY", form="10-K", filed=None):
    e = {"end": end, "val": val, "accn": accn, "fp": fp, "fy": fy, "form": form,
         "filed": filed or (end + "T00:00:00")}
    if start is not None:
        e["start"] = start
    return e


def _extracted(fields: dict) -> dict:
    """{field_name: {year: (val, accn, is_own_data)}} からextracted構造を組み立てる
    （tests/test_bs_entity_mixing.pyと同じヘルパー）"""
    extracted = {}
    for field, year_map in fields.items():
        annual = {}
        prov = {}
        for year, (val, accn, is_own_data) in year_map.items():
            annual[year] = val
            prov[year] = {"accn": accn, "filed": "2021-01-01", "is_own_data": is_own_data, "fy_tag": year}
        extracted[field] = {"annual": annual, "quarterly": {}, "_annual_provenance": prov}
    return extracted


# ============================================================
# CRM型（2アンカー競合）: 合成データでの単体検証
# ============================================================

class TestCrmTypeFyTagMismatchOverride:
    """_own_override_is_safe()のexisting_fy_tag/own_fy_tag対応。
    CRM(2011)の実構造を最小化して再現する: プレーンタグ（生fy=2010、
    end=2011-01-31、is_own_data=True、determine_fiscal_year()が偶然
    year=2011へ計算）が、NCIタグ側の真の本人データ（生fy=2011、
    end=2012-01-31、is_own_data=True）による上書きをブロックしていた。"""

    def _build_us_gaap(self):
        return {
            # プレーンタグ: CRM実データと同じく2026年まで申告が続き
            # フォールバック選定（_freshness、最新annual年で決まる）で
            # NCIタグより「新しい」候補として勝つ（実際のバグ再現に必須。
            # 1年分のみだとNCIタグ側〈2012年〉の方が新しく見え、
            # 別のフォールバック経路を通ってしまい再現しない）
            "StockholdersEquity": {"units": {"USD": [
                # 2010年10-K: 自身の本人データ（reportDate=2011-01-31と一致）
                # だが生fyタグは2010。determine_fiscal_year()はend=2011-01-31を
                # year=2011と計算する（アンカー日ちょうどのため）
                _entry(None, "2011-01-31", 1_276_491_000, fy=2010, accn="ACCN-2010-10K"),
                # 後年の申告継続（CRM実データの2012年以降相当を最小限で模した
                # ダミー、プレーンタグをNCIタグより新しく見せるためだけの1件）
                _entry(None, "2013-01-31", 2_000_000_000, fy=2012, accn="ACCN-2012-10K"),
            ]}},
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": {"units": {"USD": [
                # 2011年10-K: 自身の本人データ（reportDate=2012-01-31と一致）、
                # 生fyタグ2011でyear=2011バケツと一致（真の本人データ）
                _entry(None, "2012-01-31", 1_587_360_000, fy=2011, accn="ACCN-2011-10K"),
            ]}},
        }

    def _accn_reportdate(self):
        return {"ACCN-2010-10K": "2011-01-31", "ACCN-2011-10K": "2012-01-31",
                "ACCN-2012-10K": "2013-01-31"}

    def test_fail_before_reproduces_misselection_against_pre_fix_parser(self):
        """このテスト自体はfail-before証跡の記録用。2026-08-30の修正前の
        parser.py（`_own_override_is_safe()`がexisting_fy_tag/own_fy_tagを
        受け取らない版）に対して本テストを実行すると、CRM実データと同じ
        誤り（year=2011に生fy=2010の値1,276,491,000が採用される）が
        再現することを`git stash`で確認済み（コミットメッセージ・
        セッション記録参照）。現在のコードでは下のtest_pass_afterと
        同じ結果（正しい値）になる。"""
        parser = SECParser()
        result = parser._extract_values_best_candidate(
            self._build_us_gaap(),
            ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
            fiscal_end_month=1, accn_reportdate=self._accn_reportdate(),
            field_name="stockholders_equity", anchor_month=1, anchor_day=31,
        )
        assert result["annual"][2011] == 1_587_360_000

    def test_pass_after_correct_value_selected(self):
        """修正後: year=2011バケツには真に生fy=2011の本人データ
        （$1,587,360,000）が採用されること"""
        parser = SECParser()
        result = parser._extract_values_best_candidate(
            self._build_us_gaap(),
            ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
            fiscal_end_month=1, accn_reportdate=self._accn_reportdate(),
            field_name="stockholders_equity", anchor_month=1, anchor_day=31,
        )
        assert result["annual"][2011] == 1_587_360_000
        prov = result["_annual_provenance"][2011]
        assert prov["accn"] == "ACCN-2011-10K"
        assert prov["is_own_data"] is True
        assert prov["fy_tag"] == 2011

    def test_own_override_is_safe_directly_permits_when_fy_tags_disagree_correctly(self):
        """_own_override_is_safe()を直接呼び、existing_fy_tag!=year かつ
        own_fy_tag==year のときにTrue（上書き許可）を返すことを確認"""
        parser = SECParser()
        ok = parser._own_override_is_safe(
            year=2011, own_end_date="2012-01-31", fiscal_end_month=1,
            annual_end_dates={2011: "2011-01-31"},
            annual_durations={2011: None},
            annual_accn={2011: "ACCN-2010-10K"},
            accn_reportdate=self._accn_reportdate(),
            anchor_month=1, anchor_day=31, is_instant=True,
            existing_fy_tag=2010, own_fy_tag=2011,
        )
        assert ok is True

    def test_own_override_is_safe_without_fy_tags_still_blocks(self):
        """existing_fy_tag/own_fy_tag省略時（デフォルトNone）は従来通り
        Falseのまま（後方互換の確認）"""
        parser = SECParser()
        ok = parser._own_override_is_safe(
            year=2011, own_end_date="2012-01-31", fiscal_end_month=1,
            annual_end_dates={2011: "2011-01-31"},
            annual_durations={2011: None},
            annual_accn={2011: "ACCN-2010-10K"},
            accn_reportdate=self._accn_reportdate(),
            anchor_month=1, anchor_day=31, is_instant=True,
        )
        assert ok is False


class TestWmtTypeProtectionStillHolds:
    """WMT型の安全装置がCRM型対応後も壊れていないことの直接確認。
    既存エントリのexisting_fy_tagが年度バケツ自体と一致する（自己整合な
    真のFYデータ）場合は、accnベース短絡判定は従来通りFalseを返す
    （新しいエスケープハッチはexisting_fy_tag!=yearのときのみ発火する）。"""

    def test_own_override_is_safe_blocks_when_existing_fy_tag_matches_year(self):
        parser = SECParser()
        accn_reportdate = {"WMT-FY2009-ACCN": "2009-01-31"}
        ok = parser._own_override_is_safe(
            year=2009, own_end_date="2010-01-31", fiscal_end_month=1,
            annual_end_dates={2009: "2009-01-31"},
            annual_durations={2009: 365},
            annual_accn={2009: "WMT-FY2009-ACCN"},
            accn_reportdate=accn_reportdate,
            anchor_month=1, anchor_day=31, is_instant=False,
            existing_fy_tag=2009,  # 既存エントリの生fyタグはバケツ(2009)と一致
            own_fy_tag=2009,       # 本人データ候補側の生fyタグも2009（同一バケツを競合）
        )
        assert ok is False  # WMT型は引き続き保護される


# ============================================================
# VRT型（0アンカー）: 合成データでの単体検証
# ============================================================

class TestVrtTypeAlignToSiblingAccn:
    def test_pass_after_aligns_to_ta_tl_shared_accn(self):
        """stockholders_equityの本人データが皆無の年度で、total_assets/
        total_liabilitiesが共通採用したaccnに一致するstockholders_equity
        候補タグのエントリがあれば、そちらへ差し替えること"""
        extracted = _extracted({
            "total_assets":         {2017: (25000, "SHARED-ACCN", False)},
            "total_liabilities":    {2017: (1276, "SHARED-ACCN", False)},
            "stockholders_equity":  {2017: (-129_600_000, "OTHER-ACCN", False)},
        })
        us_gaap = {
            "StockholdersEquity": {"units": {"USD": [
                _entry("2017-01-01", "2017-12-31", 23724, fy=2018, accn="SHARED-ACCN"),
            ]}},
        }
        parser = SECParser()
        parser._align_stockholders_equity_to_sibling_accn(
            extracted, us_gaap, fiscal_end_month=12, anchor_month=12, anchor_day=31,
        )
        assert extracted["stockholders_equity"]["annual"][2017] == 23724
        prov = extracted["stockholders_equity"]["_annual_provenance"][2017]
        assert prov["accn"] == "SHARED-ACCN"
        assert prov["aligned_to_sibling_accn"] is True

    def test_no_op_when_existing_accn_already_matches_anchor_accn(self):
        """AVGO(2017)型: 現在の採用値が既にanchor_accnと同一accn由来の場合
        （NCI込みタグを採用済み）は対象外（同一accn内のタグ選択問題であり
        VRT型〈別filingへの誤誘導〉ではないため）。105銘柄シミュレーション
        で、この場合に機械的にプレーンタグへ差し替えるとTA=TL+SEの恒等式が
        NCI込み値でのみ完全一致する銘柄（AVGO）で逆に恒等式を壊すことが
        判明し、この保護を追加した。"""
        extracted = _extracted({
            "total_assets":         {2017: (54_418, "SHARED-ACCN", False)},
            "total_liabilities":    {2017: (31_232, "SHARED-ACCN", False)},
            # 現在の採用値は既にSHARED-ACCN由来（NCI込みタグ、$23,186）
            # → TL+SE=54,418=TA と恒等式が完全一致している
            "stockholders_equity":  {2017: (23_186, "SHARED-ACCN", False)},
        })
        us_gaap = {
            "StockholdersEquity": {"units": {"USD": [
                # 同一accn内にプレーンタグ（NCI抜き）の候補も存在するが、
                # 既にSHARED-ACCN採用済みのため対象外のまま
                _entry("2017-01-01", "2017-12-31", 20_285, fy=2018, accn="SHARED-ACCN"),
            ]}},
        }
        parser = SECParser()
        parser._align_stockholders_equity_to_sibling_accn(
            extracted, us_gaap, fiscal_end_month=12, anchor_month=12, anchor_day=31,
        )
        assert extracted["stockholders_equity"]["annual"][2017] == 23_186  # 変化なし

    def test_no_op_when_own_data_already_present(self):
        """stockholders_equityに既に本人データ(is_own_data=True)がある年度は
        対象外（CRM型は別ロジックで対応済みのため、二重処理を避ける）"""
        extracted = _extracted({
            "total_assets":         {2011: (100, "TA-ACCN", True)},
            "total_liabilities":    {2011: (40, "TA-ACCN", True)},
            "stockholders_equity":  {2011: (60, "SE-OWN-ACCN", True)},
        })
        us_gaap = {
            "StockholdersEquity": {"units": {"USD": [
                _entry("2011-01-01", "2011-12-31", 999, fy=2011, accn="TA-ACCN"),
            ]}},
        }
        parser = SECParser()
        parser._align_stockholders_equity_to_sibling_accn(
            extracted, us_gaap, fiscal_end_month=12, anchor_month=12, anchor_day=31,
        )
        assert extracted["stockholders_equity"]["annual"][2011] == 60  # 変化なし

    def test_no_op_when_no_matching_entry_at_anchor_accn(self):
        """CWAN(2023)型: アンカーaccnにstockholders_equity候補タグの
        エントリが一切存在しない場合は何もしない（安全側、既存の値を保持）"""
        extracted = _extracted({
            "total_assets":         {2023: (100, "ANCHOR-ACCN", False)},
            "total_liabilities":    {2023: (40, "ANCHOR-ACCN", False)},
            "stockholders_equity":  {2023: (55, "FALLBACK-ACCN", False)},
        })
        us_gaap = {
            "StockholdersEquity": {"units": {"USD": []}},  # ANCHOR-ACCNに該当なし
        }
        parser = SECParser()
        parser._align_stockholders_equity_to_sibling_accn(
            extracted, us_gaap, fiscal_end_month=12, anchor_month=12, anchor_day=31,
        )
        assert extracted["stockholders_equity"]["annual"][2023] == 55  # 変化なし

    def test_no_op_when_ta_tl_accn_disagree(self):
        """total_assets/total_liabilitiesが異なるaccnを採用している年度は
        対象外（『共通アンカー』が存在しないため判断材料がない）"""
        extracted = _extracted({
            "total_assets":         {2020: (100, "ACCN-A", False)},
            "total_liabilities":    {2020: (40, "ACCN-B", False)},
            "stockholders_equity":  {2020: (55, "ACCN-C", False)},
        })
        us_gaap = {
            "StockholdersEquity": {"units": {"USD": [
                _entry("2020-01-01", "2020-12-31", 60, fy=2020, accn="ACCN-A"),
            ]}},
        }
        parser = SECParser()
        parser._align_stockholders_equity_to_sibling_accn(
            extracted, us_gaap, fiscal_end_month=12, anchor_month=12, anchor_day=31,
        )
        assert extracted["stockholders_equity"]["annual"][2020] == 55  # 変化なし


# ============================================================
# 実データでのfail-before/pass-after確認（CRM/VRT実銘柄）
# ============================================================

class TestRealDataCrmVrt:
    """common/sec_data/data/配下の実データ（company_facts.json・
    submissions.json）を使った統合テスト。BACKLOG診断・2026-08-30の
    STEP1再現結果と完全一致することを確認する。"""

    def test_crm_2011_stockholders_equity_uses_own_fy2011_10k_value(self):
        parser = SECParser(data_dir=_DATA_DIR)
        parsed = parser.parse_company_facts("CRM")
        annual_2011 = parsed["annual"].get(2011, {})
        assert annual_2011.get("bs", {}).get("stockholders_equity") == 1_587_360_000
        prov = annual_2011.get("bs_provenance", {}).get("stockholders_equity")
        assert prov["accn"] == "0001193125-12-107281"
        assert prov["is_own_data"] is True
        assert prov["fy_tag"] == 2011

    def test_vrt_2017_stockholders_equity_matches_ta_tl_shared_accn(self):
        parser = SECParser(data_dir=_DATA_DIR)
        parsed = parser.parse_company_facts("VRT")
        annual_2017 = parsed["annual"].get(2017, {})
        bs = annual_2017.get("bs", {})
        assert bs.get("stockholders_equity") == 23724
        ta, tl = bs.get("total_assets"), bs.get("total_liabilities")
        assert ta == 25000 and tl == 1276
        assert tl + bs["stockholders_equity"] == ta  # TA=TL+SE恒等式が完全一致
        prov = annual_2017.get("bs_provenance", {}).get("stockholders_equity")
        assert prov.get("aligned_to_sibling_accn") is True

    def test_avgo_2017_accounting_identity_not_broken_by_fix(self):
        """AVGO(2017): 105銘柄シミュレーションで発見した副作用の直接確認。
        stockholders_equityは既にtotal_assets/total_liabilitiesと同一accn
        （NCI込みタグ、$23,186M）を採用しており、TL+SE=TAの恒等式が完全
        一致している。VRT型の新規ステップがこれをプレーンタグ（NCI抜き、
        $20,285M）へ差し替えて恒等式を壊すことがないよう確認する。"""
        parser = SECParser(data_dir=_DATA_DIR)
        parsed = parser.parse_company_facts("AVGO")
        annual_2017 = parsed["annual"].get(2017, {})
        bs = annual_2017.get("bs", {})
        assert bs.get("stockholders_equity") == 23_186_000_000
        assert bs["total_liabilities"] + bs["stockholders_equity"] == bs["total_assets"]

    def test_cwan_2023_unaffected_by_vrt_type_fix(self):
        """CWAN(2023)は『正しいaccnにタグ自体が存在しない』構造的必然
        パターン（BACKLOG記載: 後続3つの異なるfilingで一貫して報告される
        $354,329,000、MinorityInterest加算で恒等式が一致する既に正しい値）
        であり、VRT型の新規ステップの対象外（アンカーaccnに該当タグが
        ないためno-op）のまま値が変化していないことを実データで確認する。"""
        parser = SECParser(data_dir=_DATA_DIR)
        parsed = parser.parse_company_facts("CWAN")
        annual_2023 = parsed["annual"].get(2023, {})
        assert annual_2023.get("bs", {}).get("stockholders_equity") == 354_329_000
        prov = annual_2023.get("bs_provenance", {}).get("stockholders_equity")
        assert not prov.get("aligned_to_sibling_accn")  # 新規ステップは発火していない
