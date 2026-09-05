"""
tests/test_preflight_check.py

[[QUALITY-GATES-EPIC-1]]ゲート0（[[PREFLIGHT-CHECK-1]]想定機能①〜④）対応
（2026-09-05）の回帰テスト。common/registration/preflight_check.py が
以下を正しく検知できることを、SEC EDGARの実レスポンス形状を模した
合成データで検証する（ネットワークアクセスなし、決定的に再現可能）。

- ①上場後3年未満（初回10-K/10-Q提出日から算出）を検知する
- ②直近の年次/四半期報告書が10-K/10-Q以外（20-F等）の場合を検知する
  （8-K・SCHEDULE 13D等の無関係な提出書類に惑わされないこと）
- ③収益系XBRLタグが1つも存在しない場合を検知する
- 正常系（上場3年超・10-K提出・収益タグあり）ではフラグが立たない
- CIK未登録・API到達失敗はエラーとして記録され、判断不能である旨が
  区別して表示される（フラグとは別カテゴリ）
- フラグ・エラーの有無に関わらず自動停止しない設計であること
  （run_preflight_check()自体は例外を送出せず結果を返すのみ）

実データでの確認（本テストとは別に、着手時に実施・記録済み）:
    - APGE（売上ゼロの臨床段階バイオ）: ③が実際に発火
    - CON（2024年IPO直後）: ①が実際に発火
    - SN（2023年当時20-F提出企業）: 登録時点(2026-07-02)以降に10-K/10-Q
      提出企業へ移行済みのため、2026-09-05時点のライブ判定では②ではなく
      ①（10-K/10-Q提出履歴が浅い）が発火する。過去に20-F提出企業だった
      という同一の根本リスク（四半期系列不足）を、②ではなく①が捉えて
      いる形。②のロジック自体はBABA（現役の20-F/6-K提出企業）で実際に
      発火することを別途確認済み。
    - AAPL（上場3年超・10-K提出・収益タグあり）: フラグなし

実行方法:
    python -m pytest tests/test_preflight_check.py -v
"""

import os
import sys
from datetime import date, timedelta

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from common.registration import preflight_check as pc  # noqa: E402


def _submissions(forms_and_dates: list[tuple[str, str]]) -> dict:
    """SEC submissions APIの`filings.recent`形状を模す
    （配列は最新提出が先頭という実際のAPI仕様に合わせる）"""
    forms = [f for f, _ in forms_and_dates]
    dates = [d for _, d in forms_and_dates]
    return {"filings": {"recent": {"form": forms, "filingDate": dates}}}


def _company_facts(us_gaap_tags: list[str]) -> dict:
    return {"facts": {"us-gaap": {tag: {} for tag in us_gaap_tags}}}


class TestListingAgeFlag:
    """①上場後3年未満の検知"""

    def test_flags_recent_listing(self):
        recent_date = (date.today() - timedelta(days=365)).isoformat()  # 1年前
        submissions = _submissions([("10-Q", recent_date)])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert any("①" in f for f in result.flags)

    def test_no_flag_when_listed_long_enough(self):
        old_date = (date.today() - timedelta(days=365 * 5)).isoformat()  # 5年前
        submissions = _submissions([("10-Q", old_date), ("10-K", old_date)])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert not any("①" in f for f in result.flags)

    def test_flags_when_no_quarterly_filings_found_at_all(self):
        submissions = _submissions([("8-K", "2026-01-01"), ("S-8", "2025-06-01")])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert any("①" in f for f in result.flags)

    def test_uses_oldest_quarterly_filing_not_newest(self):
        """複数の10-K/10-Qがある場合、最古のものを基準に年数計算する
        （直近だけを見ると常に「最近」判定になってしまうため）"""
        oldest = (date.today() - timedelta(days=365 * 4)).isoformat()  # 4年前
        newest = (date.today() - timedelta(days=30)).isoformat()       # 1ヶ月前
        submissions = _submissions([("10-Q", newest), ("10-K", oldest)])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert not any("①" in f for f in result.flags)


class TestFormTypeFlag:
    """②直近の年次/四半期報告書が10-K/10-Q以外の検知"""

    def test_flags_20f_as_latest_annual_report(self):
        old_date = (date.today() - timedelta(days=365 * 5)).isoformat()
        submissions = _submissions([
            ("20-F", "2026-03-01"),
            ("6-K", old_date),
        ])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert any("②" in f and "20-F" in f for f in result.flags)

    def test_flags_6k_as_latest_annual_report(self):
        """20-F/40-Fに限らず、6-K（外国民間発行体の中間報告）が最新の
        場合も同様に②が発火すること"""
        old_date = (date.today() - timedelta(days=365 * 5)).isoformat()
        submissions = _submissions([
            ("6-K", "2026-08-01"),
            ("20-F", "2026-03-01"),
            ("6-K", old_date),
        ])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert any("②" in f and "6-K" in f for f in result.flags)

    def test_no_flag_when_latest_annual_report_is_10q(self):
        old_date = (date.today() - timedelta(days=365 * 5)).isoformat()
        submissions = _submissions([
            ("8-K", "2026-08-15"),
            ("10-Q", "2026-08-01"),
            ("10-K", old_date),
        ])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert not any("②" in f for f in result.flags)

    def test_ignores_unrelated_filing_types_between_quarterly_reports(self):
        """APGEの実例（直近提出がSCHEDULE 13D/Aだったが、これは
        10-K/10-Qの欠如を意味しない）を模したケース: 8-K・13D等の
        無関係な提出が最新であっても②は誤検知しない"""
        old_date = (date.today() - timedelta(days=365 * 5)).isoformat()
        submissions = _submissions([
            ("SCHEDULE 13D/A", "2026-09-03"),
            ("8-K", "2026-08-20"),
            ("10-Q", "2026-08-10"),
            ("10-K", old_date),
        ])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_listing_age_and_form_type(result, submissions)
        assert not any("②" in f for f in result.flags)


class TestRevenueTagFlag:
    """③収益系XBRLタグ不在の検知"""

    def test_flags_when_no_revenue_tags_present(self):
        company_facts = _company_facts(["Assets", "NetIncomeLoss"])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_revenue_tags(result, company_facts)
        assert any("③" in f for f in result.flags)

    def test_no_flag_when_revenue_tag_present(self):
        company_facts = _company_facts(["Revenues", "Assets"])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_revenue_tags(result, company_facts)
        assert not any("③" in f for f in result.flags)

    def test_any_candidate_tag_is_sufficient(self):
        """候補タグのうちいずれか1つでも存在すればフラグは立たない
        （SalesRevenueNet等、Revenues以外の候補でも可）"""
        company_facts = _company_facts(["SalesRevenueNet"])
        result = pc.PreflightResult(ticker="AAA")
        pc._check_revenue_tags(result, company_facts)
        assert not any("③" in f for f in result.flags)

    def test_uses_same_candidate_list_as_parser(self):
        """独自の重複リストではなくparser.pyのXBRL_MAPPING["revenue"]を
        そのまま流用していること"""
        from common.sec_data.parser import SECParser
        assert pc.REVENUE_TAG_CANDIDATES == tuple(SECParser.XBRL_MAPPING["revenue"])


class TestRunPreflightCheck:
    """run_preflight_check()の統合的な挙動（CIK未登録・API失敗時の扱い）"""

    def test_error_when_cik_not_registered(self, monkeypatch):
        monkeypatch.setattr(pc._tickers_mod, "get_cik", lambda t: None)
        result = pc.run_preflight_check("ZZZZ")
        assert result.errors
        assert not result.flags

    def test_error_when_submissions_fetch_fails(self, monkeypatch):
        monkeypatch.setattr(pc._tickers_mod, "get_cik", lambda t: "0000000001")

        def fake_fetch(url, timeout=30):
            if "submissions" in url:
                return None
            return _company_facts(["Revenues"])

        monkeypatch.setattr(pc, "_fetch_json", fake_fetch)
        result = pc.run_preflight_check("AAA")
        assert any("submissions" in e for e in result.errors)

    def test_error_when_company_facts_fetch_fails(self, monkeypatch):
        monkeypatch.setattr(pc._tickers_mod, "get_cik", lambda t: "0000000001")
        old_date = (date.today() - timedelta(days=365 * 5)).isoformat()

        def fake_fetch(url, timeout=30):
            if "submissions" in url:
                return _submissions([("10-K", old_date)])
            return None

        monkeypatch.setattr(pc, "_fetch_json", fake_fetch)
        result = pc.run_preflight_check("AAA")
        assert any("company facts" in e for e in result.errors)

    def test_clean_ticker_produces_no_flags_or_errors(self, monkeypatch):
        monkeypatch.setattr(pc._tickers_mod, "get_cik", lambda t: "0000000001")
        old_date = (date.today() - timedelta(days=365 * 5)).isoformat()

        def fake_fetch(url, timeout=30):
            if "submissions" in url:
                return _submissions([("10-Q", "2026-08-01"), ("10-K", old_date)])
            return _company_facts(["Revenues"])

        monkeypatch.setattr(pc, "_fetch_json", fake_fetch)
        result = pc.run_preflight_check("AAA")
        assert result.ok is True
        assert not result.flags
        assert not result.errors

    def test_does_not_raise_and_does_not_write_files(self, monkeypatch, tmp_path):
        """想定機能④（自動停止しない）の間接確認: フラグ・エラーが
        あってもrun_preflight_check()自体は例外を送出せず、また
        ファイルシステムへの書き込みも行わない"""
        monkeypatch.setattr(pc._tickers_mod, "get_cik", lambda t: None)
        before = set(os.listdir(tmp_path))
        result = pc.run_preflight_check("ZZZZ")
        after = set(os.listdir(tmp_path))
        assert before == after
        assert isinstance(result, pc.PreflightResult)


class TestPreflightResultOkProperty:
    def test_ok_true_when_empty(self):
        assert pc.PreflightResult(ticker="AAA").ok is True

    def test_ok_false_when_flags_present(self):
        r = pc.PreflightResult(ticker="AAA")
        r.flags.append("①テスト")
        assert r.ok is False

    def test_ok_false_when_errors_present(self):
        r = pc.PreflightResult(ticker="AAA")
        r.errors.append("テストエラー")
        assert r.ok is False
