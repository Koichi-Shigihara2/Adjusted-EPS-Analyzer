"""
tests/test_reader_fcf_list_with_dates.py

common/sec_data/reader.py::get_fcf_list_with_dates() のユニットテスト
（[[GATE2-READER-FCFLIST-1]] / [[GROWTH-FCFSERIES-ACCESSOR-ADOPT-1]]）。

get_fcf_list()は年次データの"period"（会計年度）を抽出時に切り捨てて
いたため、呼び出し元でFCFSeriesによる順序検証を後付けできなかった。
get_fcf_list_with_dates()はperiodを値と対で返す新規メソッド。

実行方法:
    python -m pytest tests/test_reader_fcf_list_with_dates.py -v
"""

from common.sec_data.reader import SECReader


def test_get_fcf_list_with_dates_returns_paired_periods():
    """実データ（AAPL）で、fcf_listとperiodsが同じ長さ・
    fcf_listと対応する降順のperiodsを返すこと。"""
    reader = SECReader()
    fcf_list, periods = reader.get_fcf_list_with_dates("AAPL", years=5)

    assert len(fcf_list) > 0
    assert periods is not None
    assert len(fcf_list) == len(periods)
    # periodsは新しい順（降順）であること
    assert periods == sorted(periods, reverse=True)


def test_get_fcf_list_unchanged_behavior_after_refactor():
    """既存get_fcf_list()（後方互換の薄いラッパーに変更後）が、
    get_fcf_list_with_dates()の値部分と完全一致すること（リグレッション
    確認）。"""
    reader = SECReader()
    legacy_result = reader.get_fcf_list("AAPL", years=5)
    fcf_list, _periods = reader.get_fcf_list_with_dates("AAPL", years=5)

    assert legacy_result == fcf_list


def test_get_fcf_list_with_dates_unknown_ticker_returns_empty():
    reader = SECReader()
    fcf_list, periods = reader.get_fcf_list_with_dates("__NOT_A_REAL_TICKER__", years=5)
    assert fcf_list == []
    assert periods == []
