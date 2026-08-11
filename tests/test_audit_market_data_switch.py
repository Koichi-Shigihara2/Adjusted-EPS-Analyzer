"""
tests/test_audit_market_data_switch.py

[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序5（診断ツール2ファイル切替の
1件目、common/sec_data/audit.py）の回帰テスト。

- audit_ticker()のカナダ企業判定を yfinance直接呼び出しから
  common.market_data.reader.get_attributes()経由に切替たこと
- audit_beta_drift()のβ実測値取得元を同様に切替たこと
- 両者ともattributes/未生成銘柄（reader.get_attributes()がNoneを返す）に
  対して例外を出さず中立デフォルト（判定スキップ）で継続すること

を検証する。

実行方法:
    python -m pytest tests/test_audit_market_data_switch.py -v
"""

import json
import os

import pytest

from common.sec_data import audit
from common.market_data import reader as md_reader


def _write_attributes(market_data_dir, ticker: str, record: dict) -> None:
    attr_dir = os.path.join(str(market_data_dir), "attributes")
    os.makedirs(attr_dir, exist_ok=True)
    with open(os.path.join(attr_dir, f"{ticker}.json"), "w", encoding="utf-8") as f:
        json.dump(record, f)


@pytest.fixture
def market_data_source(tmp_path, monkeypatch):
    """audit.py::_md_get_attributes()の参照先をtmp_path配下の一時
    market_dataディレクトリに差し替える（test_beta_fetcher.pyと同型）。"""
    md_dir = tmp_path / "market_data"
    monkeypatch.setattr(
        audit, "_md_get_attributes",
        lambda t: md_reader.get_attributes(t, base_dir=str(md_dir)),
    )
    return md_dir


@pytest.fixture
def isolated_beta_config(tmp_path, monkeypatch):
    """audit.BETA_CONFIG_PATHを一時ファイルに差し替え、本番
    config/beta_config.jsonへの依存を断つ（test_beta_fetcher.pyの
    isolated_configフィクスチャと同型）。"""
    cfg_path = tmp_path / "beta_config.json"
    cfg_path.write_text(json.dumps({
        "overrides": {
            "BBAI": {"beta": 2.5, "source": "yfinance_5yr"},
            "AAPL": {"beta": 1.086, "source": "yfinance_5yr"},
        }
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(audit, "BETA_CONFIG_PATH", str(cfg_path))
    return cfg_path


class TestAuditTickerCanadaCheck:
    def test_canada_country_triggers_warning(self, market_data_source):
        _write_attributes(market_data_source, "SHOP", {"symbol": "SHOP", "country": "Canada"})
        result = audit.audit_ticker("SHOP")
        assert any("カナダ企業" in w for w in result["warning"])

    def test_non_canada_country_no_warning(self, market_data_source):
        _write_attributes(market_data_source, "AAPL", {"symbol": "AAPL", "country": "United States"})
        result = audit.audit_ticker("AAPL")
        assert not any("カナダ企業" in w for w in result["warning"])

    def test_missing_attributes_skips_check_without_error(self, market_data_source):
        """attributes/未生成銘柄（fetcher.py未実行）はreader.get_attributes()が
        Noneを返す。旧yfinance直接呼び出し失敗時と同じ「判定スキップ」の
        中立デフォルト挙動になり、例外を送出しないことを確認する。"""
        result = audit.audit_ticker("NEVERFETCHED")
        assert not any("カナダ企業" in w for w in result["warning"])
        # 早期returnせず後続のTTMチェック（critical）まで到達している
        assert "TTMファイルなし" in result["critical"]


class TestAuditBetaDrift:
    def test_large_drift_detected(self, isolated_beta_config, market_data_source):
        _write_attributes(market_data_source, "BBAI", {"symbol": "BBAI", "beta": 3.181})
        drift = audit.audit_beta_drift(["BBAI"])
        assert len(drift) == 1
        assert drift[0]["ticker"] == "BBAI"
        assert drift[0]["level"] in ("warning", "critical")
        assert drift[0]["diff"] == pytest.approx(0.681, abs=0.01)

    def test_small_drift_not_reported(self, isolated_beta_config, market_data_source):
        _write_attributes(market_data_source, "AAPL", {"symbol": "AAPL", "beta": 1.086})
        drift = audit.audit_beta_drift(["AAPL"])
        assert drift == []

    def test_missing_attributes_skipped_without_error(self, isolated_beta_config, market_data_source):
        drift = audit.audit_beta_drift(["NEVERFETCHED"])
        assert drift == []

    def test_missing_config_entry_flagged_critical(self, isolated_beta_config, market_data_source):
        _write_attributes(market_data_source, "NEWTICKER", {"symbol": "NEWTICKER", "beta": 1.2})
        drift = audit.audit_beta_drift(["NEWTICKER"])
        assert len(drift) == 1
        assert drift[0]["level"] == "critical"
        assert drift[0]["cfg"] is None

    def test_returns_empty_when_market_data_unavailable(self, isolated_beta_config, monkeypatch):
        monkeypatch.setattr(audit, "HAS_MARKET_DATA", False)
        drift = audit.audit_beta_drift(["AAPL"])
        assert drift == []
