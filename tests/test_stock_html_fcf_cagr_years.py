"""
tests/test_stock_html_fcf_cagr_years.py

[[FCF-CAGR-YEARS-MISMATCH-1]]の回帰テスト。

docs/value-monitor/tanuki_valuation/stock.htmlのFCF CAGR表示は
`valid = hist.filter(fcf!=null && fcf>0)`というフィルタ後配列を使うため、
`valid[-4]`〜`valid[-1]`の間にゼロ/マイナスFCF年（フィルタで除外される年）
が挟まっていた場合、実際の経過年数は3年より多くなる。修正前は指数を
`1/3`に固定していたため、実経過年数を無視した誤った複利換算になり、
ラベルも常に「CAGR(3yr)」で実態と食い違っていた。

このJSロジックはNode.js等JS実行環境がないと直接実行できないため
（本リポジトリにはJS用のテストランナーが存在しない）、本テストは
以下の2段階で検証する:
1. stock.html本体から該当コードブロックを実際に読み取り、修正前の
   バグパターン（固定`1/3`指数）が存在しないこと・修正後の年数差分
   パターンが存在することをソース上で確認する（実装からの乖離を防ぐ）
2. 同じ算術式をPythonへ忠実に移植し、除外年ありのシナリオで実際に
   正しい経過年数・CAGR・ラベルが算出されることを数値的に検証する
   （src/value/tanuki_valuation/pipeline.py側の既存の同種修正
   `span = yr_new - yr_old`と同じ考え方であることも確認する）

実行方法:
    python -m pytest tests/test_stock_html_fcf_cagr_years.py -v
"""

import os
import re

_STOCK_HTML = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..",
    "docs", "value-monitor", "tanuki_valuation", "stock.html",
))


def _read_cagr_block() -> str:
    with open(_STOCK_HTML, encoding="utf-8") as f:
        content = f.read()
    start = content.index("// FCF CAGR")
    end = content.index("cagrStr = `FCF CAGR", start)
    end = content.index("\n", end) + 1
    return content[start:end]


class TestSourcePattern:
    def test_old_hardcoded_one_third_exponent_is_gone(self):
        """修正前のバグパターン `**(1/3)` 固定指数の実コードが残っていない
        こと（コメント中の`1/3`という説明文言自体は許容する）"""
        block = _read_cagr_block()
        assert "(1/3)" not in block

    def test_years_derived_from_year_field_difference(self):
        """修正後: 経過年数を .year フィールドの差分から実測していること"""
        block = _read_cagr_block()
        assert re.search(r"nwEntry\.year\s*-\s*oldEntry\.year", block), (
            "years を .year の差分で算出するコードが見つからない"
        )

    def test_label_uses_computed_years_not_literal_3(self):
        """ラベルが固定文字列 'CAGR(3yr)' ではなく動的な ${years} を使っていること"""
        block = _read_cagr_block()
        assert "CAGR(3yr)" not in block
        assert "CAGR(${years}yr)" in block

    def test_zero_years_guard_present(self):
        """years<=0（理論上のエッジケース）でゼロ除算/NaNにならないガードがあること"""
        block = _read_cagr_block()
        assert "years > 0" in block


class TestCorrectedFormula:
    """修正後の算術式をPythonへ忠実に移植した数値検証。
    src/value/tanuki_valuation/pipeline.py の既存修正
    （`span = yr_new - yr_old`、FCF_CAGR_{span}yr）と同じ考え方。"""

    @staticmethod
    def _compute(valid_entries):
        """valid_entries: [(year, fcf), ...] 少なくとも4件、直近が末尾"""
        if len(valid_entries) < 4:
            return None
        old_year, old_fcf = valid_entries[-4]
        nw_year, nw_fcf = valid_entries[-1]
        years = nw_year - old_year
        if years <= 0:
            return None
        cagr = ((nw_fcf / old_fcf) ** (1 / years) - 1) * 100
        return years, cagr, f"FCF CAGR({years}yr): {'+' if cagr >= 0 else ''}{cagr:.1f}%"

    def test_gap_year_produces_more_than_3_years_span_not_3(self):
        """2020年がマイナスFCFで除外された結果、validな4件が
        2018,2019,2021,2022年になるケース: 実経過年数は4年（2022-2018）で
        あるべきで、修正前バグのように3年固定になってはいけない"""
        # (year, fcf) — validは正のFCFのみのフィルタ後配列という前提
        valid = [(2018, 100.0), (2019, 110.0), (2021, 130.0), (2022, 150.0)]
        years, cagr, label = self._compute(valid)
        assert years == 4  # 修正前バグなら常に3扱いされていた
        expected_cagr = ((150.0 / 100.0) ** (1 / 4) - 1) * 100
        assert abs(cagr - expected_cagr) < 1e-9
        assert label == f"FCF CAGR(4yr): +{expected_cagr:.1f}%"

    def test_no_gap_year_produces_exactly_3_years(self):
        """除外年がない連続4年（例: 2019〜2022）では実経過年数はちょうど
        3年になり、この場合は修正前の固定値と結果が一致する（回帰なし）"""
        valid = [(2019, 100.0), (2020, 110.0), (2021, 120.0), (2022, 130.0)]
        years, cagr, label = self._compute(valid)
        assert years == 3
        expected_cagr = ((130.0 / 100.0) ** (1 / 3) - 1) * 100
        assert abs(cagr - expected_cagr) < 1e-9

    def test_declining_fcf_gives_negative_cagr_with_correct_span(self):
        valid = [(2017, 200.0), (2018, 180.0), (2020, 150.0), (2021, 120.0)]
        years, cagr, label = self._compute(valid)
        assert years == 4  # 2021-2017、2019年が除外年
        assert cagr < 0
        assert label.startswith("FCF CAGR(4yr): -")

    def test_fewer_than_four_valid_entries_yields_no_cagr(self):
        assert self._compute([(2020, 100.0), (2021, 110.0)]) is None
