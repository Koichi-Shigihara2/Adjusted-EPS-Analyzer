"""
tests/test_registration_validator.py

common/sec_data/registration_validator.py の --promote 機能
（[[REGISTER-FLOW-REDESIGN-1]]方針2、2026-09-03新設）のユニットテスト。
ticker_ng_items()・promote_ticker_status()を検証する。

実行方法:
    python -m pytest tests/test_registration_validator.py -v
"""

import csv
import sys
import os

_SEC_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "common", "sec_data")
)
sys.path.insert(0, _SEC_DATA_DIR)

import registration_validator as rv  # noqa: E402


class TestTickerNgItems:
    """ticker_ng_items()がメッセージ先頭の"{ticker}: "プレフィックスで
    自ティッカー分のNGのみに絞り込むこと（P3等の全体チェックが無関係な
    既存銘柄のNGを含んでも、それらで昇格をブロックしない設計）"""

    def test_filters_to_target_ticker_only(self):
        issues = rv.Issues()
        issues.ng("P1-Step3-Valuation", "AAA: latest.json 未生成")
        issues.ng("P3-SegWeight", "BBB: weight合計=0.900 (≠1.0)")
        issues.warn("P1-Step2-Beta", "AAA: beta_config.json に override なし")

        result = rv.ticker_ng_items(issues, "AAA")
        assert result == [("P1-Step3-Valuation", "AAA: latest.json 未生成")]

    def test_returns_empty_when_no_ng_for_ticker(self):
        issues = rv.Issues()
        issues.ng("P3-SegWeight", "BBB: weight合計=0.900 (≠1.0)")

        assert rv.ticker_ng_items(issues, "AAA") == []

    def test_does_not_match_ticker_as_substring(self):
        """"AA"に対し"AAA: ..."のようなプレフィックス誤マッチをしないこと
        （"{ticker}: "の完全一致プレフィックスで判定するため部分文字列
        一致は起きないはずだが、明示的に回帰テストする）"""
        issues = rv.Issues()
        issues.ng("P1-Step3-Valuation", "AAA: latest.json 未生成")

        assert rv.ticker_ng_items(issues, "AA") == []


class TestPromoteTickerStatus:
    """promote_ticker_status()がstatus列のみを書き換え、他の列・他の行は
    一切変更しないこと（テキストベース部分編集、他行はバイト単位で保持）"""

    _HEADER = (
        "ticker,cik,name,eps_sector,stonks_silo,tanuki,eps,hypecore,"
        "status,registered_date,registration_source,registration_note,"
        "exclusion_reason\n"
    )

    def _write_csv(self, tmp_path, rows: list[str]) -> str:
        path = tmp_path / "cik_lookup.csv"
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(self._HEADER)
            f.writelines(rows)
        return str(path)

    def test_updates_only_target_status(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(tmp_path, [
            "AAA,0000000001,Company A,,false,false,false,false,provisioning,"
            "2026-09-03,manual,test registration,\n",
            "BBB,0000000002,Company B,,false,true,true,true,active,,unknown,"
            "existing,\n",
        ])
        monkeypatch.setattr(rv, "CIK_CSV", csv_path)

        old_status = rv.promote_ticker_status("AAA", "active")
        assert old_status == "provisioning"

        with open(csv_path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["ticker"] == "AAA"
        assert rows[0]["status"] == "active"
        # 他の列は変更されていないこと
        assert rows[0]["registration_note"] == "test registration"
        # 他の行はまったく変更されていないこと
        assert rows[1]["status"] == "active"
        assert rows[1]["name"] == "Company B"

    def test_preserves_quoted_name_field_with_comma(self, tmp_path, monkeypatch):
        """name列にカンマを含む銘柄（"Astera Labs, Inc."型）の行を
        書き換えても、csv.writerが正しく再引用符化すること"""
        csv_path = self._write_csv(tmp_path, [
            'AAA,0000000001,"Astera Labs, Inc.",,false,true,true,true,'
            'provisioning,2026-09-03,manual,test,\n',
        ])
        monkeypatch.setattr(rv, "CIK_CSV", csv_path)

        rv.promote_ticker_status("AAA", "candidate")

        with open(csv_path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["name"] == "Astera Labs, Inc."
        assert rows[0]["status"] == "candidate"

    def test_raises_when_ticker_not_found(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(tmp_path, [
            "AAA,0000000001,Company A,,false,true,true,true,active,,unknown,x,\n",
        ])
        monkeypatch.setattr(rv, "CIK_CSV", csv_path)

        try:
            rv.promote_ticker_status("ZZZ", "active")
            assert False, "ValueErrorが発生するはず"
        except ValueError:
            pass
