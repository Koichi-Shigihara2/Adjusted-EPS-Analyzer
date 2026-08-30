"""
tests/test_quarterly_classify_period.py

[[QUARTERLY-CLASSIFY-PERIOD-NO-UPPER-BOUND-1]]の回帰テスト。

quarterly.py::_classify_period()のis_annual判定に、130日という下限
のみでは、10-K内に埋め込まれた中間的な期間長の比較開示（6〜9ヶ月累計等）
やタグの多年度累計開示が誤ってis_annual=Trueに分類される問題があった。
2026-08-30、105銘柄・company_facts.json全概念の実データ分布（真の年次
エントリは349〜372日に集中し336〜362日は1件も存在しない空白がある）を
根拠に、340〜400日の範囲に限定する上限を追加した。

修正前は`DELL`のNetIncome/ProfitLoss 2023-08-04期（181日、fp='FY'、
form='10-K'）がis_annual=Trueに誤分類されていた。本テストはその
再現ケースを含む。

実行方法:
    python -m pytest tests/test_quarterly_classify_period.py -v
"""

from common.sec_data.quarterly import _classify_period


class TestTrueAnnualStillClassified:
    """真の年次期間（349〜372日）は引き続きis_annual=Trueと判定される"""

    def test_standard_365_day_fy_form_10k(self):
        result = _classify_period("2023-01-01", "2023-12-31", "FY", "10-K")
        assert result["is_annual"] is True
        assert result["period_days"] == 364

    def test_53_week_fiscal_year_370_days(self):
        result = _classify_period("2023-01-01", "2024-01-05", "FY", "10-K")
        assert result["is_annual"] is True

    def test_10k_a_form_also_annual(self):
        result = _classify_period("2023-01-01", "2023-12-31", "FY", "10-K/A")
        assert result["is_annual"] is True

    def test_q4_tagged_true_annual_via_days_only_branch(self):
        """DELLのように一部タグでfp='Q4'のまま真の年次（363日）が
        報告されるケース（旧days>300分岐に相当する経路）"""
        result = _classify_period("2023-02-04", "2024-02-02", "Q4", "10-K")
        assert result["is_annual"] is True
        assert result["period_days"] == 363


class TestMidLengthComparativeDisclosureExcluded:
    """中間的な期間長のfp='FY'比較開示は、130日を超えていても
    is_annual=Falseに正しく判定される（本項目の核心的なバグ修正）"""

    def test_dell_2023_08_04_181day_regression(self):
        """DELL実データ再現: 2023-02-04始点、2023-08-04終点、181日、
        fp='FY'・form='10-K'（修正前はis_annual=Trueに誤分類）"""
        result = _classify_period("2023-02-04", "2023-08-04", "FY", "10-K")
        assert result["is_annual"] is False
        assert result["period_days"] == 181
        # is_annual=Falseかつ130日超のためYTD候補として扱われる
        assert result["is_ytd"] is True

    def test_9month_ytd_273days_excluded(self):
        result = _classify_period("2020-01-01", "2020-09-30", "FY", "10-K/A")
        assert result["is_annual"] is False
        assert result["period_days"] == 273

    def test_6month_ytd_180days_excluded(self):
        result = _classify_period("2023-01-01", "2023-06-30", "FY", "10-K/A")
        assert result["is_annual"] is False


class TestExtremeMultiYearDisclosureExcluded:
    """数年〜十年規模の累計開示（上限が無い場合に誤って年次扱いされて
    いた極端な外れ値）も正しく除外される"""

    def test_multi_year_cumulative_disclosure_excluded(self):
        result = _classify_period("2015-01-01", "2024-12-31", "FY", "10-K")
        assert result["is_annual"] is False
        assert result["period_days"] > 400


class TestKlacQuarterStillExcludedByLowerBound:
    """XBRL-TAG-KLAC-1の教訓（下限130日）は引き続き有効。四半期程度
    （89〜91日）はfp='FY'でもis_annual=Trueにならない"""

    def test_klac_quarter_length_89days_not_annual(self):
        result = _classify_period("2021-04-01", "2021-06-29", "FY", "10-K")
        assert result["is_annual"] is False
        assert result["period_days"] == 89


class TestFormRestrictionUnchanged:
    """form=10-K/10-K-A以外（PARSER-ENTG-COMPYEAR-1の教訓）は、
    period_daysが真の年次範囲内であってもis_annual=Falseのまま"""

    def test_10q_form_with_annual_length_days_not_annual(self):
        result = _classify_period("2023-01-01", "2023-12-31", "FY", "10-Q")
        assert result["is_annual"] is False
