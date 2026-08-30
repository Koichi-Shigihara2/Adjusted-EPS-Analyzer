"""
tests/test_system_health_workflow_monitor.py

[[DATA-FRESHNESS-MONITORING-FUTURE-IDEA-1]]対応（2026-08-30）の回帰テスト。
common/system_health.py に追加したcheck J（cron定義ワークフローの実行状況
チェック）が、以下を正しく検知できることを検証する:

- 直近実行が失敗（conclusion != success）しているワークフローがある場合に
  異常として検知する（この検知ロジックが存在しなければ、SEC_Data_Update
  障害調査で見つかったような「週次実行が2回連続失敗し3週間誰も気づかない」
  事態が今後も再発しうる）
- cronの想定間隔（頻度から推定した許容日数）を大きく超えて未実行の
  ワークフローがある場合に異常として検知する
- 正常系（全ワークフローが直近・成功）では異常なしと判定する
- cron式からの頻度推定（毎日/週数回/週次/月次）が想定通り動く

実行方法:
    python -m pytest tests/test_system_health_workflow_monitor.py -v
"""

import os
import sys
from datetime import date, timedelta

import pytest

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from common import system_health as sh  # noqa: E402


# ── cron頻度推定 ──────────────────────────────────────────────────────
def test_parse_cron_threshold_daily():
    label, days = sh._parse_cron_threshold_days("15 22 * * *")
    assert label == "毎日"
    assert days == 3


def test_parse_cron_threshold_weekdays():
    label, days = sh._parse_cron_threshold_days("25 21 * * 1-5")
    assert label == "週数回"
    assert days == 4


def test_parse_cron_threshold_weekly_single_day():
    # SEC_Data_Update.yml実物のcron式（日曜のみ）
    label, days = sh._parse_cron_threshold_days("0 12 * * 0")
    assert label == "週次"
    assert days == 10


def test_parse_cron_threshold_monthly_dom_restricted():
    # Beta_Config_Update.yml実物のcron式（月初第1日曜）
    label, days = sh._parse_cron_threshold_days("0 23 1-7 * 0")
    assert label == "月次"
    assert days == 40


# ── ワークフロー発見 ──────────────────────────────────────────────────
def test_discover_cron_workflows_finds_sec_data_update():
    found = dict(sh._discover_cron_workflows())
    assert "SEC_Data_Update.yml" in found
    assert found["SEC_Data_Update.yml"] == "0 12 * * 0"


# ── check_j_workflow_runs: 異常検知（本回帰テストの本体） ─────────────
def _fake_run(conclusion: str, days_ago: int) -> dict:
    created = (date.today() - timedelta(days=days_ago)).isoformat()
    return {"conclusion": conclusion, "created_at": f"{created}T12:00:00Z"}


def test_check_j_detects_failed_run(monkeypatch):
    """直近実行が failure のワークフローが1件でもあれば ok=False になること。
    修正前（check_j導入前）はこの検知ロジック自体が存在せず、
    SEC_Data_Updateの2週連続失敗のような事態を誰も検知できなかった。"""
    monkeypatch.setattr(sh, "_get_repo_slug", lambda: "Koichi-Shigihara2/On-a-journey")
    monkeypatch.setattr(
        sh, "_discover_cron_workflows",
        lambda: [("SEC_Data_Update.yml", "0 12 * * 0"), ("Score_Verifier.yml", "0 0 * * *")],
    )

    def fake_fetch(repo_slug, workflow_file):
        if workflow_file == "SEC_Data_Update.yml":
            return _fake_run("failure", days_ago=1)
        return _fake_run("success", days_ago=0)

    monkeypatch.setattr(sh, "_fetch_latest_run", fake_fetch)

    label, ok, detail = sh.check_j_workflow_runs()
    assert ok is False
    assert "失敗" in detail
    assert "SEC_Data_Update.yml" in detail


def test_check_j_detects_stale_run(monkeypatch):
    """週次ワークフロー（許容10日）の直近成功実行が21日前しかない場合に
    ok=False になること（SEC_Data_Update障害の実測値=約3週間放置を模擬）。"""
    monkeypatch.setattr(sh, "_get_repo_slug", lambda: "Koichi-Shigihara2/On-a-journey")
    monkeypatch.setattr(
        sh, "_discover_cron_workflows",
        lambda: [("SEC_Data_Update.yml", "0 12 * * 0")],
    )
    monkeypatch.setattr(
        sh, "_fetch_latest_run",
        lambda repo_slug, workflow_file: _fake_run("success", days_ago=21),
    )

    label, ok, detail = sh.check_j_workflow_runs()
    assert ok is False
    assert "未実行超過" in detail


def test_check_j_healthy_when_all_recent_and_successful(monkeypatch):
    monkeypatch.setattr(sh, "_get_repo_slug", lambda: "Koichi-Shigihara2/On-a-journey")
    monkeypatch.setattr(
        sh, "_discover_cron_workflows",
        lambda: [
            ("SEC_Data_Update.yml", "0 12 * * 0"),
            ("Score_Verifier.yml", "0 0 * * *"),
        ],
    )

    def fake_fetch(repo_slug, workflow_file):
        days_ago = 1 if workflow_file == "SEC_Data_Update.yml" else 0
        return _fake_run("success", days_ago=days_ago)

    monkeypatch.setattr(sh, "_fetch_latest_run", fake_fetch)

    label, ok, detail = sh.check_j_workflow_runs()
    assert ok is True
    assert "すべて正常" in detail


def test_check_j_api_unreachable_is_not_treated_as_failure(monkeypatch):
    """API到達不可（レート制限・ネットワーク不調等）は異常扱いしない設計
    （一過性の外部要因で毎日REDになるのを避けるための意図的な仕様）。"""
    monkeypatch.setattr(sh, "_get_repo_slug", lambda: "Koichi-Shigihara2/On-a-journey")
    monkeypatch.setattr(
        sh, "_discover_cron_workflows",
        lambda: [("SEC_Data_Update.yml", "0 12 * * 0")],
    )

    def raise_error(repo_slug, workflow_file):
        raise OSError("network unreachable")

    monkeypatch.setattr(sh, "_fetch_latest_run", raise_error)

    label, ok, detail = sh.check_j_workflow_runs()
    assert ok is True
    assert "確認不可" in detail


def test_check_j_no_repo_slug_skips_gracefully(monkeypatch):
    monkeypatch.setattr(sh, "_get_repo_slug", lambda: None)
    label, ok, detail = sh.check_j_workflow_runs()
    assert ok is True
