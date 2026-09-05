"""
tests/test_system_health_ticker_audit.py

[[QUALITY-GATES-EPIC-1]]ゲート4（旧TICKER-AUDIT-1の想定機能①②⑤⑥）対応
（2026-09-05）の回帰テスト。common/system_health.py に追加した
check_k_ticker_audit()（銘柄棚卸しレポート）が以下を正しく検知できる
ことを検証する:

- ①status=candidateかつ登録から一定日数超の銘柄を「見直し候補」として
  検知する（statusがactive等の場合や、閾値未満の場合は検知しない）
- ②registration_source=technical_screening（検証由来）かつ
  portfolio.jsonに保有記載のない銘柄を検知する
- ⑤registration_validator.pyのP4-CIKOrphanチェック結果を集約・表示する
- ⑥monitor_tickers.yamlとcik_lookup.csvの銘柄差分を検知する
- いずれも該当なしの場合は「該当なし」と明示的に表示し、ok=Trueとなる
- 判断を自動化せず、レポート出力のみであること（本テストはstatus変更等の
  副作用がないことも暗黙に検証する: fakeデータはメモリ上のみで
  ファイルへの書き込みは一切発生しない）

実行方法:
    python -m pytest tests/test_system_health_ticker_audit.py -v
"""

import os
import sys
from datetime import date, timedelta

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from common import system_health as sh  # noqa: E402


def _row(ticker, status="active", registered_date="", registration_source="unknown"):
    return {
        "ticker": ticker,
        "status": status,
        "registered_date": registered_date,
        "registration_source": registration_source,
    }


def _patch_clean_defaults(monkeypatch, rows=None, held=None, monitor=None, orphan_msgs=None):
    """全サブチェックを「該当なし」の状態にpatchした上で、指定した
    引数だけ上書きするヘルパー（各テストは検証したい観点だけをfakeし、
    他の観点による誤検知を混入させない）。"""
    rows = rows if rows is not None else []
    held = held if held is not None else set()
    monitor = monitor if monitor is not None else {r["ticker"] for r in rows}
    orphan_msgs = orphan_msgs or []

    monkeypatch.setattr(sh._tickers_mod, "get_all_rows", lambda *a, **k: rows)
    monkeypatch.setattr(sh, "_portfolio_tickers", lambda: held)
    monkeypatch.setattr(sh, "_load_monitor_tickers", lambda: sorted(monitor))

    def fake_p4(issues, monitor_set):
        for msg in orphan_msgs:
            issues.warn("P4-CIKOrphan", msg)

    monkeypatch.setattr(sh, "_check_p4_orphan_configs", fake_p4)


class TestStaleCandidates:
    """①status=candidateかつ登録から_STALE_CANDIDATE_DAYS超の銘柄検知"""

    def test_detects_stale_candidate(self, monkeypatch):
        old_date = (date.today() - timedelta(days=sh._STALE_CANDIDATE_DAYS + 1)).isoformat()
        rows = [_row("AAA", status="candidate", registered_date=old_date)]
        _patch_clean_defaults(monkeypatch, rows=rows)
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is False
        assert "AAA" in detail
        assert "①見直し候補" in detail

    def test_candidate_within_threshold_not_flagged(self, monkeypatch):
        recent_date = (date.today() - timedelta(days=sh._STALE_CANDIDATE_DAYS - 1)).isoformat()
        rows = [_row("AAA", status="candidate", registered_date=recent_date)]
        _patch_clean_defaults(monkeypatch, rows=rows)
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True
        assert detail == "該当なし（棚卸し正常）"

    def test_active_status_not_flagged_even_if_old(self, monkeypatch):
        old_date = (date.today() - timedelta(days=365)).isoformat()
        rows = [_row("AAA", status="active", registered_date=old_date)]
        _patch_clean_defaults(monkeypatch, rows=rows)
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True

    def test_candidate_without_registered_date_not_flagged(self, monkeypatch):
        """registered_date欠落（既存active銘柄のバックフィル分等）は
        判定不能のためスキップする（誤検知防止）"""
        rows = [_row("AAA", status="candidate", registered_date="")]
        _patch_clean_defaults(monkeypatch, rows=rows)
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True


class TestScreeningSourceNoPosition:
    """②registration_source=technical_screeningかつポジションなしの銘柄検知"""

    def test_detects_screening_source_without_position(self, monkeypatch):
        rows = [_row("AAA", registration_source="technical_screening")]
        _patch_clean_defaults(monkeypatch, rows=rows, held=set())
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is False
        assert "AAA" in detail
        assert "②検証由来・無保有" in detail

    def test_screening_source_with_position_not_flagged(self, monkeypatch):
        rows = [_row("AAA", registration_source="technical_screening")]
        _patch_clean_defaults(monkeypatch, rows=rows, held={"AAA"})
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True

    def test_non_screening_source_not_flagged_even_without_position(self, monkeypatch):
        rows = [_row("AAA", registration_source="unknown")]
        _patch_clean_defaults(monkeypatch, rows=rows, held=set())
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True


class TestP4CikOrphanAggregation:
    """⑤registration_validator.pyのP4-CIKOrphanチェック結果の集約表示"""

    def test_surfaces_p4_cikorphan_warning(self, monkeypatch):
        rows = [_row("AAA")]
        _patch_clean_defaults(
            monkeypatch, rows=rows,
            orphan_msgs=["AAA: cik_lookup に登録済み+SEC data あり だが monitor_tickers 未登録 [inactive?]"],
        )
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is False
        assert "⑤P4-CIKOrphan" in detail
        assert "AAA" in detail

    def test_no_p4_warnings_when_clean(self, monkeypatch):
        rows = [_row("AAA")]
        _patch_clean_defaults(monkeypatch, rows=rows, orphan_msgs=[])
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True

    def test_other_p4_categories_are_not_surfaced(self, monkeypatch):
        """P4-CIKIncomplete等、P4-CIKOrphan以外のカテゴリは
        本関数のスコープ外のため混入しない"""
        rows = [_row("AAA")]

        def fake_p4(issues, monitor_set):
            issues.warn("P4-CIKIncomplete", "AAA: 別カテゴリの警告")

        _patch_clean_defaults(monkeypatch, rows=rows)
        monkeypatch.setattr(sh, "_check_p4_orphan_configs", fake_p4)
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True
        assert "別カテゴリ" not in detail


class TestMonitorTickersSyncGap:
    """⑥monitor_tickers.yamlとcik_lookup.csvの件数差・銘柄差分の検知"""

    def test_detects_ticker_only_in_cik_lookup(self, monkeypatch):
        rows = [_row("AAA"), _row("BBB")]
        _patch_clean_defaults(monkeypatch, rows=rows, monitor={"BBB"})
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is False
        assert "⑥同期漏れ" in detail
        assert "cik_lookupのみ" in detail
        assert "AAA" in detail

    def test_detects_ticker_only_in_monitor_yaml(self, monkeypatch):
        rows = [_row("BBB")]
        _patch_clean_defaults(monkeypatch, rows=rows, monitor={"BBB", "CCC"})
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is False
        assert "⑥同期漏れ" in detail
        assert "monitor_tickersのみ" in detail
        assert "CCC" in detail

    def test_no_sync_gap_when_sets_match(self, monkeypatch):
        rows = [_row("AAA"), _row("BBB")]
        _patch_clean_defaults(monkeypatch, rows=rows, monitor={"AAA", "BBB"})
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True


class TestOverallBehavior:
    def test_all_clear_returns_explicit_message(self, monkeypatch):
        rows = [_row("AAA", status="active", registration_source="unknown")]
        _patch_clean_defaults(monkeypatch, rows=rows, held=set(), monitor={"AAA"})
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is True
        assert detail == "該当なし（棚卸し正常）"
        assert "✅" in label

    def test_multiple_findings_combined_in_single_report(self, monkeypatch):
        old_date = (date.today() - timedelta(days=sh._STALE_CANDIDATE_DAYS + 1)).isoformat()
        rows = [
            _row("AAA", status="candidate", registered_date=old_date),
            _row("BBB", registration_source="technical_screening"),
        ]
        _patch_clean_defaults(
            monkeypatch, rows=rows, held=set(), monitor={"AAA", "BBB"},
            orphan_msgs=["CCC: 孤立エントリ"],
        )
        label, ok, detail = sh.check_k_ticker_audit()
        assert ok is False
        assert "①見直し候補" in detail
        assert "②検証由来・無保有" in detail
        assert "⑤P4-CIKOrphan" in detail
        assert "⚠️" in label

    def test_does_not_mutate_input_rows_or_files(self, monkeypatch):
        """判断の自動化を行わないこと（想定機能④）の間接的な確認:
        呼び出し前後でfakeデータが変更されない（レポート専用の
        読み取り処理であること）"""
        rows = [_row("AAA", status="candidate",
                      registered_date=(date.today() - timedelta(days=100)).isoformat())]
        rows_copy = [dict(r) for r in rows]
        _patch_clean_defaults(monkeypatch, rows=rows, held=set(), monitor=set())
        sh.check_k_ticker_audit()
        assert rows == rows_copy
