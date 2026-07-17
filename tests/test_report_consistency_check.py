"""
tests/test_report_consistency_check.py

common/sec_data/report_consistency_check.py のWARN台帳機能（QUALITY-GATES-EPIC-1
Phase 1）のユニットテスト。台帳未登録WARNが強調表示され、台帳登録済みWARNが
通常表示されることを検証する。

実行方法:
    python -m pytest tests/test_report_consistency_check.py -v
"""

import sys
import os
import json

_SEC_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "common", "sec_data")
)
sys.path.insert(0, _SEC_DATA_DIR)

import report_consistency_check as rcc  # noqa: E402
from report_consistency_check import annotate_warn, load_warn_ledger  # noqa: E402

from common.sec_data.contracts import Classification  # noqa: E402


class TestAnnotateWarn:
    """annotate_warn()が台帳照合結果に応じてWARNメッセージを正しく分岐すること"""

    def test_acknowledged_warn_unchanged(self):
        ledger = {("WARN-10", "ELF")}
        msg, is_new = annotate_warn(
            "ELF", "  [WARN-10 PS異常値] yfinance PS=16.9x vs 自社計算=2.8x", ledger
        )
        assert is_new is False
        assert msg == "  [WARN-10 PS異常値] yfinance PS=16.9x vs 自社計算=2.8x"
        assert "未確認" not in msg

    def test_unacknowledged_warn_marked_new(self):
        ledger = {("WARN-10", "ELF")}
        msg, is_new = annotate_warn(
            "AAPL", "  [WARN-10 PS異常値] yfinance PS=16.9x vs 自社計算=2.8x", ledger
        )
        assert is_new is True
        assert "未確認" in msg
        assert "WARN-10" in msg

    def test_same_check_different_ticker_not_acknowledged(self):
        """同一CHECK番号でも台帳に登録されていないtickerは未確認扱いになる"""
        ledger = {("WARN-20", "MO")}
        msg, is_new = annotate_warn(
            "XOM", "  [WARN-20 fcf_cagr floor張り付き] growth.rate=15.0%", ledger
        )
        assert is_new is True
        assert "未確認" in msg

    def test_different_check_same_ticker_not_acknowledged(self):
        """同一tickerでも台帳に登録されていないCHECK番号は未確認扱いになる"""
        ledger = {("WARN-10", "ELF")}
        msg, is_new = annotate_warn(
            "ELF", "  [WARN-20 fcf_cagr floor張り付き] growth.rate=15.0%", ledger
        )
        assert is_new is True
        assert "未確認" in msg

    def test_empty_ledger_marks_all_new(self):
        msg, is_new = annotate_warn("ELF", "  [WARN-10 PS異常値] test", set())
        assert is_new is True
        assert "未確認" in msg

    def test_message_without_check_number_passthrough(self):
        """CHECK番号を含まないメッセージはis_new=Trueだが本文は変更しない"""
        msg, is_new = annotate_warn("ELF", "  no check tag here", set())
        assert is_new is True
        assert msg == "  no check tag here"


class TestLoadWarnLedger:
    """load_warn_ledger()が台帳ファイルを正しく(check, ticker)集合に変換すること"""

    def test_loads_existing_ledger_entries(self, tmp_path):
        ledger_path = tmp_path / "warn_acknowledged.json"
        ledger_path.write_text(
            json.dumps({
                "acknowledged": [
                    {"check": "WARN-10", "ticker": "ELF", "acknowledged_date": "2026-07-12", "comment": "test"},
                    {"check": "WARN-20", "ticker": "MO", "acknowledged_date": "2026-07-12", "comment": "test"},
                ]
            }),
            encoding="utf-8",
        )
        result = load_warn_ledger(str(ledger_path))
        assert result == {("WARN-10", "ELF"), ("WARN-20", "MO")}

    def test_missing_file_returns_empty_set(self, tmp_path):
        result = load_warn_ledger(str(tmp_path / "does_not_exist.json"))
        assert result == set()

    def test_malformed_json_returns_empty_set(self, tmp_path):
        ledger_path = tmp_path / "warn_acknowledged.json"
        ledger_path.write_text("{not valid json", encoding="utf-8")
        result = load_warn_ledger(str(ledger_path))
        assert result == set()

    def test_production_ledger_contains_known_three_warns(self):
        """本番のconfig/warn_acknowledged.jsonに既知3件（ELF/MO/XOM）が
        登録されていること（QUALITY-GATES-EPIC-1 Phase 1 Step4の登録確認）"""
        result = load_warn_ledger()
        assert ("WARN-10", "ELF") in result
        assert ("WARN-20", "MO") in result
        assert ("WARN-20", "XOM") in result


class TestCheckCDataJumpIntegration:
    """CHECK-21（check_c_data_jump()統合、QUALITY-GATES-EPIC-1 Phase 2b-2）が
    WARN-21としてwarnリストに追加され、ngリストには追加されないことを検証する
    （NGではなくWARNとした判断・NG-11との役割分担の回帰テスト）"""

    def _make_ticker_dir(self, tmp_path, ticker: str) -> None:
        """check_ticker()がreport.txtの存在で早期returnしないよう最小のfixtureを作る"""
        ticker_dir = tmp_path / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        (ticker_dir / "report.txt").write_text("Classification: WATCH\n", encoding="utf-8")
        (ticker_dir / "latest.json").write_text("{}", encoding="utf-8")

    def test_warn_21_added_when_check_c_data_jump_flags(self, tmp_path, monkeypatch):
        self._make_ticker_dir(tmp_path, "TESTCO")
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(
            rcc, "check_c_data_jump",
            lambda repo_root, ticker: (True, ["2020(100M)→2021(400M) 倍率4.00x"], []),
        )
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert any("WARN-21" in w and "4.00x" in w for w in warn)
        assert not any("WARN-21" in n for n in ng)

    def test_no_warn_21_when_check_c_data_jump_does_not_flag(self, tmp_path, monkeypatch):
        self._make_ticker_dir(tmp_path, "TESTCO")
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(
            rcc, "check_c_data_jump",
            lambda repo_root, ticker: (False, [], []),
        )
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert not any("WARN-21" in w for w in warn)

    def test_multiple_jumps_produce_multiple_warn_21_entries(self, tmp_path, monkeypatch):
        """FICO/CPRT型のように複数年で段差が続く場合、jumpの件数分WARN-21が出ること"""
        self._make_ticker_dir(tmp_path, "TESTCO")
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(
            rcc, "check_c_data_jump",
            lambda repo_root, ticker: (
                True,
                ["2019(300M)→2020(1160M) 倍率3.87x", "2020(1160M)→2021(1295M) 倍率1.12x が除外"],
                [],
            ),
        )
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        warn_21_entries = [w for w in warn if "WARN-21" in w]
        assert len(warn_21_entries) == 2


class TestCheck23FyTagMismatch:
    """CHECK-23（fyタグ裏取り不一致、ARCH-DATA-1ステージ3で新設）が
    fy_tag_mismatch_log.jsonを読んでWARN-23を正しく追加すること。
    CHECK-22（fy_collision_log.json）とは独立した別軸のチェックであることの
    回帰も併せて確認する"""

    def _make_ticker_dir(self, tmp_path, ticker: str) -> None:
        """check_ticker()がreport.txtの存在で早期returnしないよう最小のfixtureを作る"""
        ticker_dir = tmp_path / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        (ticker_dir / "report.txt").write_text("Classification: WATCH\n", encoding="utf-8")
        (ticker_dir / "latest.json").write_text("{}", encoding="utf-8")

    def _make_sec_data_dir(self, sec_data_path, ticker: str) -> "Path":
        ticker_dir = sec_data_path / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        return ticker_dir

    def test_no_warn_23_when_no_mismatch_log(self, tmp_path, monkeypatch):
        self._make_ticker_dir(tmp_path, "TESTCO")
        sec_data_path = tmp_path / "sec_data"
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(rcc, "SEC_DATA_DIR", str(sec_data_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert not any("WARN-23" in w for w in warn)

    def test_warn_23_added_when_mismatch_log_present(self, tmp_path, monkeypatch):
        self._make_ticker_dir(tmp_path, "TESTCO")
        sec_data_path = tmp_path / "sec_data"
        ticker_dir = self._make_sec_data_dir(sec_data_path, "TESTCO")
        (ticker_dir / "fy_tag_mismatch_log.json").write_text(
            json.dumps({"ticker": "TESTCO", "mismatches": [
                {"field": "revenue", "end_date": "2015-01-03", "fy_tag": 2015,
                 "computed_year": 2014},
            ]}),
            encoding="utf-8",
        )
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(rcc, "SEC_DATA_DIR", str(sec_data_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert any("WARN-23" in w for w in warn)
        assert not any("WARN-23" in n for n in ng)  # 非ブロッキング（NGにはならない）

    def test_warn_23_reports_count_and_fields_for_multiple_mismatches(self, tmp_path, monkeypatch):
        """複数フィールドにまたがる不一致の件数・対象フィールドがメッセージに
        反映されること（2026-07-17設計変更: is_own_data=Falseは検知対象外と
        なったため、fy_tag_mismatch_log.jsonにはis_own_data=Trueの不一致のみが
        記録される前提。スキーマもfield/end_date/fy_tag/computed_yearのみに簡素化）"""
        self._make_ticker_dir(tmp_path, "TESTCO")
        sec_data_path = tmp_path / "sec_data"
        ticker_dir = self._make_sec_data_dir(sec_data_path, "TESTCO")
        (ticker_dir / "fy_tag_mismatch_log.json").write_text(
            json.dumps({"ticker": "TESTCO", "mismatches": [
                {"field": "total_assets", "end_date": "2015-01-03", "fy_tag": 2015,
                 "computed_year": 2014},
                {"field": "revenue", "end_date": "2015-01-03", "fy_tag": 2015,
                 "computed_year": 2014},
            ]}),
            encoding="utf-8",
        )
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(rcc, "SEC_DATA_DIR", str(sec_data_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        warn_23 = next(w for w in warn if "WARN-23" in w)
        assert "2件" in warn_23
        assert "revenue" in warn_23 and "total_assets" in warn_23

    def test_check_22_and_23_are_independent(self, tmp_path, monkeypatch):
        """fy_collision_log.json（CHECK-22）とfy_tag_mismatch_log.json（CHECK-23）は
        独立して検知され、片方のみ存在する場合にもう片方が誤検知されないこと"""
        self._make_ticker_dir(tmp_path, "TESTCO")
        sec_data_path = tmp_path / "sec_data"
        ticker_dir = self._make_sec_data_dir(sec_data_path, "TESTCO")
        (ticker_dir / "fy_collision_log.json").write_text(
            json.dumps({"ticker": "TESTCO", "collisions": [
                {"field": "revenue", "fy": 2020, "end_dates": ["2019-12-31", "2020-12-31"],
                 "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
            ]}),
            encoding="utf-8",
        )
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(rcc, "SEC_DATA_DIR", str(sec_data_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert any("WARN-22" in w for w in warn)
        assert not any("WARN-23" in w for w in warn)


class TestRunChecksTickerScan:
    """FLAG-CONSUMER-AUDIT-2: run_checks()のスキャン対象決定が
    os.listdir(DATA_DIR)からtickers.get_tanuki_tickers()との積集合に
    変わったことの回帰テスト。tanuki=false銘柄はreport.txtが残存していても
    スキャン対象から除外されること"""

    def _make_ticker_dir(self, tmp_path, ticker: str) -> None:
        ticker_dir = tmp_path / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        (ticker_dir / "report.txt").write_text("Classification: WATCH\n", encoding="utf-8")
        (ticker_dir / "latest.json").write_text("{}", encoding="utf-8")

    def test_tanuki_false_ticker_excluded_from_scan(self, tmp_path, monkeypatch):
        """ZS相当（report.txt残存だがtanuki=false）はスキャン対象に含まれない"""
        self._make_ticker_dir(tmp_path, "AAPL")
        self._make_ticker_dir(tmp_path, "ZS")
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(rcc._tickers_mod, "get_tanuki_tickers", lambda csv_path=None: ["AAPL"])
        monkeypatch.setattr(rcc, "_load_rpo_whitelist", lambda: set())
        monkeypatch.setattr(rcc, "load_warn_ledger", lambda: set())

        checked = []

        def _fake_check_ticker(ticker, whitelist):
            checked.append(ticker)
            return [], []

        monkeypatch.setattr(rcc, "check_ticker", _fake_check_ticker)

        class Args:
            ticker = None
            quiet = True

        rcc.run_checks(Args())

        assert "AAPL" in checked
        assert "ZS" not in checked

    def test_report_txt_missing_excludes_tanuki_true_ticker(self, tmp_path, monkeypatch):
        """tanuki=trueでもreport.txtが存在しない銘柄はスキャン対象に含まれない
        （両条件必須。report_txt_parser.pyと同型のパターン）"""
        self._make_ticker_dir(tmp_path, "AAPL")
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(rcc._tickers_mod, "get_tanuki_tickers", lambda csv_path=None: ["AAPL", "MSFT"])
        monkeypatch.setattr(rcc, "_load_rpo_whitelist", lambda: set())
        monkeypatch.setattr(rcc, "load_warn_ledger", lambda: set())

        checked = []

        def _fake_check_ticker(ticker, whitelist):
            checked.append(ticker)
            return [], []

        monkeypatch.setattr(rcc, "check_ticker", _fake_check_ticker)

        class Args:
            ticker = None
            quiet = True

        rcc.run_checks(Args())

        assert checked == ["AAPL"]


class TestClassificationStrOverride:
    """GATE2-PHASE3B-1③-b: Classification(str, Enum)のf-string補間が
    ③-a（GrowthVerdict）と同様に__str__override後、常に素の値
    （"Classification.WATCH"ではなく"WATCH"）になることを確認する。
    NG-3（DCF_Reliability=LOW & Classification が WATCH/SELL/PASS 以外）は
    report.txtをregexで再パースした文字列と比較するため、この挙動が
    崩れるとNG-3が全銘柄で誤発火する（事前調査で発見した最重要リスク）"""

    def test_fstring_interpolation_matches_plain_string(self):
        for member in Classification:
            assert f"{member}" == member.value
            assert str(member) == member.value
            assert f"Classification: {member}" == f"Classification: {member.value}"

    def test_all_members_equal_their_plain_string_value(self):
        assert Classification.BUY == "BUY"
        assert Classification.WATCH == "WATCH"
        assert Classification.HOLD == "HOLD"
        assert Classification.TRIM == "TRIM"
        assert Classification.GROWTH_PREMIUM == "GROWTH_PREMIUM"
        assert Classification.SELL == "SELL"
        assert Classification.PASS == "PASS"


class TestCheck3LowRoundingWithEnumClassification:
    """CHECK-3（NG-3 LOW丸め未発動）が、pipeline.py側でClassification
    Enum化された後もreport.txt生成・regexパース・比較の一連の流れで
    正しく動作することを確認する回帰テスト（事前調査で発見した
    テスト空白地帯を埋める。従来この観点の専用テストは存在しなかった）"""

    def _make_ticker_dir(self, tmp_path, ticker: str, classification: str, dcf_reliability: str = "LOW") -> None:
        ticker_dir = tmp_path / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        report_text = (
            f"Classification: {classification}\n"
            f"DCF_Reliability: {dcf_reliability} ⚠️\n"
            "FCF_Base: $100,000,000\n"
        )
        (ticker_dir / "report.txt").write_text(report_text, encoding="utf-8")
        (ticker_dir / "latest.json").write_text("{}", encoding="utf-8")

    def test_ng3_does_not_fire_when_classification_is_watch(self, tmp_path, monkeypatch):
        """DCF_Reliability=LOW & Classification=WATCH（正しく丸められた状態）→ NG-3は発火しない"""
        # Classification.WATCHのf-string表現（__str__override後の実際の出力）を使う
        classification_text = f"{Classification.WATCH}"
        assert classification_text == "WATCH"
        self._make_ticker_dir(tmp_path, "TESTCO", classification_text)
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert not any("NG-3" in n for n in ng)

    def test_ng3_does_not_fire_when_classification_is_sell(self, tmp_path, monkeypatch):
        classification_text = f"{Classification.SELL}"
        self._make_ticker_dir(tmp_path, "TESTCO", classification_text)
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert not any("NG-3" in n for n in ng)

    def test_ng3_does_not_fire_when_classification_is_pass(self, tmp_path, monkeypatch):
        classification_text = f"{Classification.PASS}"
        self._make_ticker_dir(tmp_path, "TESTCO", classification_text)
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert not any("NG-3" in n for n in ng)

    def test_ng3_fires_when_classification_is_buy_and_reliability_low(self, tmp_path, monkeypatch):
        """DCF_Reliability=LOWなのにClassification=BUY（丸め未発動）→ NG-3が正しく発火することのサニティ確認"""
        classification_text = f"{Classification.BUY}"
        self._make_ticker_dir(tmp_path, "TESTCO", classification_text)
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert any("NG-3" in n and "Classification=BUY" in n for n in ng)

    def test_ng3_would_falsely_fire_if_str_override_were_missing(self, tmp_path, monkeypatch):
        """__str__override欠落時にNG-3が誤発火することを再現し、overrideの必要性を裏付ける回帰テスト
        （Classification.WATCHのクラス名付き表記"Classification.WATCH"を直接report.txtに
        書き込むことで、override漏れが起きた場合と同じ状態をシミュレートする）"""
        broken_classification_text = "Classification.WATCH"  # __str__override漏れ時の実際の出力
        self._make_ticker_dir(tmp_path, "TESTCO", broken_classification_text)
        monkeypatch.setattr(rcc, "DATA_DIR", str(tmp_path))
        ng, warn = rcc.check_ticker("TESTCO", whitelist=set())
        assert any("NG-3" in n for n in ng), (
            "__str__override漏れ時の表記だとNG-3が誤発火することを確認 "
            "（= 現在のClassificationは__str__overrideがあるため実際には発生しない）"
        )
