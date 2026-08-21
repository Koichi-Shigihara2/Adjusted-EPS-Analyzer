"""
tests/test_text_kpi_extractor.py

src/tail/text_kpi_extractor.py のキーワードアンカー抽出
（[[TAIL-XBRL-SEGMENT-FETCHER-NONDIMENSIONED-GAP-1]] Step5、
2026-08-21⑨新設）のユニットテスト。

固定サンプルは2026-08-21調査セッションでSOFI直近10-Q（accession
0001818874-26-000054、2026Q2）・同時期8-K EX-99.1から実際に取得した
テキスト断片（周辺コンテキスト込み）。ネットワークアクセスは行わない。

実行方法:
    python -m pytest tests/test_text_kpi_extractor.py -v
"""

import os
import sys
from unittest.mock import patch

import pytest

_TAIL_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "tail")
)
if _TAIL_DIR not in sys.path:
    sys.path.insert(0, _TAIL_DIR)

import text_kpi_extractor as tke  # noqa: E402


# ─────────────────────────────────────────────
# 固定サンプル（2026Q2 SOFI、実データ）
# ─────────────────────────────────────────────

# 10-Q MD&A: Net interest marginの正式開示（約35,772文字目付近）
SAMPLE_10Q_NIM = (
    'me\n$\n156,592\n$\n97,263\n$\n59,329\n61\n%\n$\n323,323\n$\n168,379\n$\n154,944\n92\n%\n'
    'Earnings per share\ndiluted\n$\n0.12\n$\n0.08\n$\n0.04\n50\n%\n$\n0.24\n$\n0.14\n$\n0.10\n71\n%\n'
    'Net interest margin\n5.98\n%\n5.86\n%\n5.94\n%\n5.94\n%\n($ in thousands)\n'
    'June 30, 2026\nDecember 31, 2025\n$ Change\n% Change\nLoans held for sale\n$\n29,737,289\n$\n'
)

# 10-Q MD&A: 正式なNCO比率表（約102,602文字目付近、Personal loans=2.62%）
SAMPLE_10Q_NCO = (
    'net charge-offs and the annualized ratio of net charge-offs to average loans outstanding:\n'
    'Three Months Ended June 30, 2026\nThree Months Ended June 30, 2025\n($ in thousands)\n'
    'Average Loans  (1)\nNet Charge-offs  (2)(3)(4)\nRatio  (4)(5)\nAverage Loans  (1)\n'
    'Net Charge-offs  (2)(3)(4)\nRatio  (4)(5)\nPersonal loans\n$\n26,183,468\n$\n171,015\n2.62\n%\n'
    '$\n18,414,581\n$\n129,970\n2.83\n%\nStudent loans\n15,971,158'
)

# 8-K EX-99.1: NCOの一過性除外後の調整値（"would have been"仮定法、
# 10-Qの正式値2.62%とは異なる約3.7%）。誤って拾ってはならないサンプル
SAMPLE_8K_NCO_ADJUSTED_TRAP = (
    ' with expectations. Excluding the impact of late stage delinquent loan sales, it is estimated '
    'that, including recoveries, the all-in annualized net charge-off rate for personal loans would '
    'have been approximately 3.7%, a 70 basis point improvement from the prior quarter and an 80 '
    'basis point improvement from the prior year period, driven by an improvement in the underlying '
    'performance as well as s'
)

# 8-K EX-99.1: NIM開示（10-Qと同一値5.98%）
SAMPLE_8K_NIM = (
    'point decrease in cost of funds, partially offset by a 32 basis point decrease in average asset '
    'yields year-over-year. For the second quarter, net interest margin of 5.98% increased\n4\n'
    'basis points from the prior quarter.\nDuring the quarter, average total deposits comprised over '
    '90% of average total liabilities. The average rate paid on deposits in the\nsecond\n'
    'quarter was 156 basis points lower than'
)


# ─────────────────────────────────────────────
# fetch_10q_mda_full(): Part I/Part II同名"Item 2"の誤選択バグの回帰確認
# ─────────────────────────────────────────────

class TestFetch10qMdaFullSectionBoundary:
    """fetch_10q_mda_full()が、10-Q Part II内の同名"Item 2"
    （"Unregistered Sales of Equity Securities..."、短い）ではなく、
    Part Iの本来のMD&A（長い）を正しく選ぶことを確認する。

    2026-08-21⑨の実機検証で発見したバグの回帰防止テスト:
    当初extract_mda_section()をmax_chars=10,000,000で呼び出して全文を
    得ようとしたが、同関数はmax_charsを「Item3が見つからない場合の
    フォールバック長」の算出（`end = s + max_chars * 2`）にも使って
    おり、巨大なmax_charsを渡すとPart IIの短いセクションのフォール
    バック長が異常に肥大化し、本来187,179文字あるはずのMD&Aが
    3,421文字のPart II断片にすり替わっていた（SOFI 2026Q2で実測）。
    """

    @staticmethod
    def _mock_response(text: str):
        resp = type("MockResp", (), {})()
        resp.text = text
        return resp

    def test_selects_long_part1_mda_over_short_part2_item2(self):
        real_mda_body = "REAL MDA CONTENT " * 200  # 十分に長い本文
        synthetic_html = (
            "<html><body>"
            "Item 1. Financial Statements\n...\n"
            "Item 2. Management s Discussion and Analysis of Financial Condition\n"
            + real_mda_body +
            "\nItem 3. Quantitative and Qualitative Disclosures About Market Risk\n...\n"
            "Item 2. Unregistered Sales of Equity Securities and Use of Proceeds\nNone.\n"
            "Item 3. Defaults Upon Senior Securities\nNone.\n"
            "</body></html>"
        )
        with patch.object(tke, "get_recent_filings", return_value=[{
                "accession": "0000000000-26-000001",
                "primary_document": "dummy-20260630.htm",
                "report_date": "2026-06-30",
            }]), \
             patch.object(tke, "edgar_get", return_value=self._mock_response(synthetic_html)):
            mda_full, quarter = tke.fetch_10q_mda_full("0000000000")

        assert mda_full is not None
        assert "REAL MDA CONTENT" in mda_full
        assert "Unregistered Sales" not in mda_full
        assert quarter == "2026Q2"


# ─────────────────────────────────────────────
# extract_by_keyword_anchor(): 実データでの抽出確認
# ─────────────────────────────────────────────

class TestExtractByKeywordAnchor:
    def test_finds_nim_in_10q_sample(self):
        snippet = tke.extract_by_keyword_anchor(
            SAMPLE_10Q_NIM, ["net interest margin"], window=50
        )
        assert snippet is not None
        assert "5.98" in snippet

    def test_finds_nco_ratio_in_10q_sample(self):
        snippet = tke.extract_by_keyword_anchor(
            SAMPLE_10Q_NCO,
            ["annualized ratio of net charge-offs to average loans outstanding"],
            window=300,
        )
        assert snippet is not None
        assert "2.62" in snippet
        assert "Personal loans" in snippet

    def test_no_match_returns_none(self):
        snippet = tke.extract_by_keyword_anchor(
            SAMPLE_10Q_NIM, ["totally unrelated phrase"], window=100
        )
        assert snippet is None

    def test_priority_order_picks_first_candidate_in_list_not_first_position_in_text(self):
        """候補リストの先頭から順に試すのであって、テキスト中で先に
        出現する語を採用するのではないことを、2つの異なるフレーズが
        別々の位置にある合成テキストで確認する（候補[1]がテキスト中で
        先に出現し、候補[0]は後方に出現するケース）。"""
        text = (
            "irrelevant filler " * 5
            + "SECOND_PHRASE appears here first "
            + "irrelevant filler " * 20
            + "FIRST_PHRASE appears here later"
        )
        snippet = tke.extract_by_keyword_anchor(
            text, ["FIRST_PHRASE", "SECOND_PHRASE"], window=20
        )
        assert snippet is not None
        assert "FIRST_PHRASE" in snippet
        assert "SECOND_PHRASE" not in snippet

    def test_nco_formal_phrase_does_not_match_8k_adjusted_trap_text(self):
        """10-Q正式表現のフレーズは、8-Kの一過性除外後の仮定値
        （"would have been approximately 3.7%"）テキスト単体には
        一切マッチしないこと（フレーズ自体がその文言を含まないため）。
        """
        snippet = tke.extract_by_keyword_anchor(
            SAMPLE_8K_NCO_ADJUSTED_TRAP,
            ["annualized ratio of net charge-offs to average loans outstanding"],
            window=300,
        )
        assert snippet is None


# ─────────────────────────────────────────────
# KEYWORD_ANCHOR_CANDIDATES: NCOの調整値混入防止ガードの回帰確認
# ─────────────────────────────────────────────

class TestKeywordAnchorCandidatesConfig:
    def test_nco_sources_excludes_8k(self):
        """NCOの検索対象ドキュメントに8-Kが含まれないこと
        （8-Kの一過性除外後の仮定値"would have been"を誤って
        採用するリスクを構造的に排除するための設計）。"""
        spec = tke.KEYWORD_ANCHOR_CANDIDATES["正味貸倒率（NCO）"]
        assert spec["sources"] == ["10-Q"]

    def test_nco_phrases_do_not_reference_would_have_been(self):
        spec = tke.KEYWORD_ANCHOR_CANDIDATES["正味貸倒率（NCO）"]
        for phrase in spec["phrases"]:
            assert "would have been" not in phrase.lower()

    def test_nim_sources_include_both_documents(self):
        """NIMは両ドキュメントで値が一致するため制限不要。"""
        spec = tke.KEYWORD_ANCHOR_CANDIDATES["純金利マージン（NIM）"]
        assert set(spec["sources"]) == {"10-Q", "8-K"}


# ─────────────────────────────────────────────
# _try_keyword_anchor_fallback(): 未登録KPI・ティッカーへの無影響確認
# ─────────────────────────────────────────────

class TestKeywordAnchorFallbackNoSideEffect:
    def test_nco_only_never_fetches_8k(self):
        """NCO単独のフォールバック時、8-K（一過性除外後の調整値
        "would have been約3.7%"の混入源）を一切フェッチしないこと。
        これがNCOの定義問題（10-Q正式値2.62% vs 8-K調整値3.7%）に
        対する構造的な防護そのもの（KEYWORD_ANCHOR_CANDIDATESの
        sources設定がドキュメントレベルで8-Kを除外している）。"""
        not_found_kpis = [
            {"name": "正味貸倒率（NCO）", "extraction_hint": "net charge-off rate"},
        ]
        with patch.object(tke, "fetch_10q_mda_full", return_value=(SAMPLE_10Q_NCO, "2026Q2")), \
             patch.object(tke, "fetch_8k_exhibit99_full") as m_8k, \
             patch.object(tke, "call_grok", return_value='{"extracted_kpis": [], "not_found": []}'):
            tke._try_keyword_anchor_fallback(
                "SOFI", "0001818874", "2026Q2", not_found_kpis
            )
        m_8k.assert_not_called()

    def test_returns_empty_dict_when_no_registered_kpi(self):
        """KEYWORD_ANCHOR_CANDIDATESに登録の無いKPIのみの場合、
        ネットワーク・Grok呼び出しを一切行わずに空dictを返すこと
        （他ティッカー・他KPIへの無影響の保証）。"""
        not_found_kpis = [
            {"name": "NDR（ネット・ダラー・リテンション）", "extraction_hint": "net dollar retention"}
        ]
        with patch.object(tke, "fetch_10q_mda_full") as m_10q, \
             patch.object(tke, "fetch_8k_exhibit99_full") as m_8k, \
             patch.object(tke, "call_grok") as m_grok:
            result = tke._try_keyword_anchor_fallback(
                "DUMMY", "0000000000", "2026Q2", not_found_kpis
            )
        assert result == {}
        m_10q.assert_not_called()
        m_8k.assert_not_called()
        m_grok.assert_not_called()

    def test_calls_grok_only_when_snippet_found(self):
        """登録済みKPIでも、全文取得結果にキーワードが無ければ
        Grokを呼ばないこと（空スニペットを渡さない設計）。"""
        not_found_kpis = [
            {"name": "純金利マージン（NIM）", "extraction_hint": None},
        ]
        with patch.object(tke, "fetch_10q_mda_full", return_value=("no relevant content here", "2026Q2")), \
             patch.object(tke, "fetch_8k_exhibit99_full", return_value="also nothing relevant"), \
             patch.object(tke, "call_grok") as m_grok:
            result = tke._try_keyword_anchor_fallback(
                "DUMMY", "0000000000", "2026Q2", not_found_kpis
            )
        assert result == {}
        m_grok.assert_not_called()

    def test_end_to_end_with_mocked_grok_extracts_correct_values(self):
        """登録済み2KPI（NCO・NIM）について、実データ由来の固定
        サンプルからスニペットを構築しGrokへ渡すところまでを検証する
        （Grok呼び出し自体はモック、実際の抽出値5.98%/2.62%を返す
        レスポンスを模して最終結果に正しく反映されることを確認）。"""
        not_found_kpis = [
            {"name": "正味貸倒率（NCO）", "extraction_hint": "net charge-off rate"},
            {"name": "純金利マージン（NIM）", "extraction_hint": "net interest margin"},
        ]
        mock_grok_response = '''{
          "extracted_kpis": [
            {"name": "正味貸倒率（NCO）", "value": "2.62%", "value_numeric": 2.62,
             "unit": "%", "source_text": "Personal loans ... 2.62 %", "confidence": "high", "quarter": "2026Q2"},
            {"name": "純金利マージン（NIM）", "value": "5.98%", "value_numeric": 5.98,
             "unit": "%", "source_text": "Net interest margin 5.98 %", "confidence": "high", "quarter": "2026Q2"}
          ],
          "not_found": []
        }'''

        with patch.object(tke, "fetch_10q_mda_full", return_value=(SAMPLE_10Q_NCO + SAMPLE_10Q_NIM, "2026Q2")), \
             patch.object(tke, "fetch_8k_exhibit99_full", return_value=SAMPLE_8K_NIM), \
             patch.object(tke, "call_grok", return_value=mock_grok_response) as m_grok:
            result = tke._try_keyword_anchor_fallback(
                "SOFI", "0001818874", "2026Q2", not_found_kpis
            )

        assert m_grok.called
        extracted = {e["name"]: e for e in result["extracted_kpis"]}
        assert extracted["正味貸倒率（NCO）"]["value_numeric"] == 2.62
        assert extracted["純金利マージン（NIM）"]["value_numeric"] == 5.98

        # Grokに渡されたプロンプトに、10-Qの正式NCO値のスニペットが
        # 含まれ、8-Kの調整値("would have been"/"3.7")が含まれないこと
        prompt_sent = m_grok.call_args.kwargs.get("user_prompt") or m_grok.call_args.args[0]
        assert "2.62" in prompt_sent
        assert "would have been" not in prompt_sent
        assert "3.7" not in prompt_sent
