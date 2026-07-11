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

from report_consistency_check import annotate_warn, load_warn_ledger  # noqa: E402


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
