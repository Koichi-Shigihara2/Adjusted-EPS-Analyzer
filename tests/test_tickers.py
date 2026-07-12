"""
tests/test_tickers.py

common/sec_data/tickers.py のユニットテスト。
get_active_tickers()がフラグ='true'かつstatusが'retired'でない銘柄のみを
返すこと（ZS-TICKERS-LEAK-1・銘柄リスト統一アクセサ導入）を検証する。

実行方法:
    python -m pytest tests/test_tickers.py -v
"""

import csv
import sys
import os

_SEC_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "common", "sec_data")
)
sys.path.insert(0, _SEC_DATA_DIR)

import tickers as tk  # noqa: E402


def _write_csv(tmp_path, rows: list[dict]) -> str:
    path = tmp_path / "cik_lookup.csv"
    fieldnames = ["ticker", "cik", "name", "eps_sector", "stonks_silo",
                  "tanuki", "eps", "hypecore", "status", "registered_date",
                  "registration_source", "registration_note"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            full = {k: "" for k in fieldnames}
            full.update(row)
            writer.writerow(full)
    return str(path)


def _row(ticker, tanuki="false", stonks_silo="false", eps="false",
         hypecore="false", status="active"):
    return {
        "ticker": ticker, "cik": "0000000000", "name": ticker,
        "tanuki": tanuki, "stonks_silo": stonks_silo, "eps": eps,
        "hypecore": hypecore, "status": status,
    }


class TestGetActiveTickers:
    def test_returns_only_flagged_tickers(self, tmp_path):
        csv_path = _write_csv(tmp_path, [
            _row("AAA", tanuki="true"),
            _row("BBB", tanuki="false"),
            _row("CCC", tanuki="true"),
        ])
        assert tk.get_active_tickers("tanuki", csv_path) == ["AAA", "CCC"]

    def test_excludes_retired_status_even_if_flag_true(self, tmp_path):
        """ZS-TICKERS-LEAK-1型の再発防止: statusがretiredなら
        フラグがtrueでも対象外とする"""
        csv_path = _write_csv(tmp_path, [
            _row("AAA", tanuki="true", status="active"),
            _row("BBB", tanuki="true", status="retired"),
        ])
        assert tk.get_active_tickers("tanuki", csv_path) == ["AAA"]

    def test_candidate_status_is_still_included(self, tmp_path):
        """status=candidateは既存の運用（WST/CON等）を壊さないため対象に含める"""
        csv_path = _write_csv(tmp_path, [
            _row("AAA", tanuki="true", status="active"),
            _row("BBB", tanuki="true", status="candidate"),
        ])
        assert tk.get_active_tickers("tanuki", csv_path) == ["AAA", "BBB"]

    def test_empty_flag_value_excluded(self, tmp_path):
        csv_path = _write_csv(tmp_path, [_row("AAA", tanuki="")])
        assert tk.get_active_tickers("tanuki", csv_path) == []

    def test_case_and_whitespace_insensitive(self, tmp_path):
        csv_path = _write_csv(tmp_path, [
            {"ticker": "AAA", "cik": "0", "name": "AAA", "tanuki": " TRUE ",
             "status": " Active "},
        ])
        assert tk.get_active_tickers("tanuki", csv_path) == ["AAA"]


class TestConvenienceWrappersUseActiveTickers:
    """get_tanuki_tickers等の既存便利関数がget_active_tickers経由になったこと
    （statusフィルタが一貫して適用されること）を確認する"""

    def test_get_tanuki_tickers_excludes_retired(self, tmp_path):
        csv_path = _write_csv(tmp_path, [
            _row("AAA", tanuki="true", status="active"),
            _row("BBB", tanuki="true", status="retired"),
        ])
        assert tk.get_tanuki_tickers(csv_path) == ["AAA"]

    def test_get_stonks_silo_tickers_excludes_retired(self, tmp_path):
        csv_path = _write_csv(tmp_path, [
            _row("AAA", stonks_silo="true", status="active"),
            _row("BBB", stonks_silo="true", status="retired"),
        ])
        assert tk.get_stonks_silo_tickers(csv_path) == ["AAA"]

    def test_get_eps_tickers_excludes_retired(self, tmp_path):
        csv_path = _write_csv(tmp_path, [
            _row("AAA", eps="true", status="active"),
            _row("BBB", eps="true", status="retired"),
        ])
        assert tk.get_eps_tickers(csv_path) == ["AAA"]

    def test_get_hypecore_tickers_excludes_retired(self, tmp_path):
        csv_path = _write_csv(tmp_path, [
            _row("AAA", hypecore="true", status="active"),
            _row("BBB", hypecore="true", status="retired"),
        ])
        assert tk.get_hypecore_tickers(csv_path) == ["AAA"]


class TestProductionCikLookup:
    """本番cik_lookup.csvに対する回帰テスト（ZS-TICKERS-LEAK-1の実害確認）"""

    def test_zs_excluded_from_tanuki_tickers(self):
        """ZSはtanuki=falseのため対象外であること"""
        assert "ZS" not in tk.get_tanuki_tickers()

    def test_zs_included_in_stonks_silo_tickers(self):
        """ZSはstonks_silo=trueのためSTONKS SILO側では引き続き対象"""
        assert "ZS" in tk.get_stonks_silo_tickers()

    def test_rklb_excluded_from_tanuki_tickers(self):
        assert "RKLB" not in tk.get_tanuki_tickers()
