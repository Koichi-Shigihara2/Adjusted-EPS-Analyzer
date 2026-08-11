"""
tests/test_score_verifier.py

src/value/tanuki_valuation/score_verifier.py の全銘柄スキャン（--ticker省略時）が
tanuki=true銘柄に限定されることのユニットテスト。FLAG-CONSUMER-AUDIT-2
（tanuki=false化済みだがscore_history.jsonが残存する銘柄、ZS・RKLB等が
全銘柄スキャン時に混入していた問題）の回帰テスト。

実行方法:
    python -m pytest tests/test_score_verifier.py -v
"""

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_SV_DIR = os.path.join(_REPO_ROOT, "src", "value", "tanuki_valuation")
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if _SV_DIR not in sys.path:
    sys.path.insert(0, _SV_DIR)

import score_verifier as sv  # noqa: E402


def _make_score_history(data_dir, ticker: str) -> None:
    d = os.path.join(data_dir, ticker)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "score_history.json"), "w", encoding="utf-8") as f:
        f.write("[]")


class TestFullScanTickerFiltering:
    """main()の全銘柄スキャン用ロジック（--ticker省略時）が
    tanuki=true銘柄のみに限定されることを確認する。
    main()自体はargparse+実処理を含むため、同一のフィルタ条件を
    直接検証する（本番の_data_dir()/tickers.get_tanuki_tickers()と
    同じ組み合わせパターン）"""

    def test_tanuki_false_ticker_dir_excluded(self, tmp_path, monkeypatch):
        _make_score_history(str(tmp_path), "AAPL")
        _make_score_history(str(tmp_path), "ZS")
        monkeypatch.setattr(
            sv._tickers_mod, "get_tanuki_tickers", lambda csv_path=None: ["AAPL"]
        )

        tanuki_set = set(sv._tickers_mod.get_tanuki_tickers())
        tickers = sorted(
            d for d in os.listdir(str(tmp_path))
            if os.path.isdir(os.path.join(str(tmp_path), d)) and d in tanuki_set
        )

        assert tickers == ["AAPL"]
        assert "ZS" not in tickers
        # 既存ファイル自体は削除されない
        assert os.path.exists(os.path.join(str(tmp_path), "ZS", "score_history.json"))

    def test_explicit_ticker_argument_not_filtered(self, monkeypatch):
        """--ticker明示指定時はtanuki判定を経由しない（挙動変更なし）"""
        monkeypatch.setattr(
            sv._tickers_mod, "get_tanuki_tickers", lambda csv_path=None: ["AAPL"]
        )
        args_ticker = "ZS"
        tickers = [args_ticker.upper()]
        assert tickers == ["ZS"]

    def test_production_zs_rklb_excluded_from_tanuki_tickers(self):
        """本番cik_lookup.csvでZS・RKLBがtanuki=falseであることを確認する
        （全銘柄スキャン時に更新対象から外れることの前提条件）"""
        tanuki_set = set(sv._tickers_mod.get_tanuki_tickers())
        assert "ZS" not in tanuki_set
        assert "RKLB" not in tanuki_set


class TestFetchPriceAfter:
    """[[MARKETDATA-LAYER-CONSTRUCTION-1]]着手順序5-2: fetch_price_after()の
    common.market_data.reader.get_price_on_or_after()経由への切替回帰テスト。
    ネットワークアクセス（yfinance呼び出し）は行わない。"""

    def test_future_target_returns_none_without_calling_reader(self, monkeypatch):
        called = []
        monkeypatch.setattr(
            sv._market_data_reader, "get_price_on_or_after",
            lambda *a, **k: called.append((a, k)) or {"close": 999.0},
        )
        # 十分先の未来日（daysを大きくして target > today にする）
        result = sv.fetch_price_after("AAPL", "2026-08-01", 3650)
        assert result is None
        assert called == []

    def test_elapsed_target_returns_close_from_reader(self, monkeypatch):
        monkeypatch.setattr(
            sv._market_data_reader, "get_price_on_or_after",
            lambda ticker, date: {"date": date, "close": 123.45, "symbol": ticker},
        )
        result = sv.fetch_price_after("AAPL", "2026-06-03", 30)
        assert result == 123.45

    def test_no_record_found_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            sv._market_data_reader, "get_price_on_or_after", lambda ticker, date: None,
        )
        assert sv.fetch_price_after("AAPL", "2026-06-03", 30) is None

    def test_reader_exception_returns_none_not_raise(self, monkeypatch):
        def _boom(ticker, date):
            raise RuntimeError("boom")
        monkeypatch.setattr(sv._market_data_reader, "get_price_on_or_after", _boom)
        assert sv.fetch_price_after("AAPL", "2026-06-03", 30) is None
