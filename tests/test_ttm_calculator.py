"""
tests/test_ttm_calculator.py

common/sec_data/ttm_calculator.py のユニットテスト。
BUG-TTM-Q4DUP-1: implied Q4 の二重計上防止ロジックを検証する。

実行方法:
    venv/Scripts/python.exe -m pytest tests/test_ttm_calculator.py -v
"""

from common.sec_data.ttm_calculator import (
    _build_q4_quarterly_entries,
    calc_ttm,
    calc_ttm_series,
    STOCK_FIELDS,
    EXCLUDED_FIELDS,
)


def _annual(end, start, val):
    return {"end": end, "start": start, "val": val, "fy": int(end[:4]), "filed": "", "accn": "", "is_annual": True}


def _q(end, start, val, is_implied=False, is_annual=False):
    e = {"end": end, "start": start, "val": val, "is_annual": is_annual}
    if is_implied:
        e["is_implied"] = True
    return e


class TestBuildQ4QuarterlyEntriesDedup:
    """BUG-TTM-Q4DUP-1: 既存Q4があれば再生成しない"""

    def test_skips_when_implied_q4_already_persisted(self):
        # normalizer.py が既に2024-12-31のimplied Q4を永続化済み
        annual = [_annual("2024-12-31", "2024-01-01", 1000)]
        quarterly = [
            _q("2024-03-31", "2024-01-01", 100),
            _q("2024-06-30", "2024-04-01", 200),
            _q("2024-09-30", "2024-07-01", 300),
            _q("2024-12-31", "2024-09-30", 400, is_implied=True),  # 既存Q4
        ]
        result = _build_q4_quarterly_entries(annual, quarterly)
        assert result == []

    def test_skips_when_real_q4_already_reported(self):
        # 実際にQ4単独データが報告されている銘柄（稀だが存在しうる）も二重生成しない
        annual = [_annual("2024-12-31", "2024-01-01", 1000)]
        quarterly = [
            _q("2024-03-31", "2024-01-01", 100),
            _q("2024-06-30", "2024-04-01", 200),
            _q("2024-09-30", "2024-07-01", 300),
            _q("2024-12-31", "2024-09-30", 400),  # 実データのQ4
        ]
        result = _build_q4_quarterly_entries(annual, quarterly)
        assert result == []

    def test_generates_q4_when_not_already_present(self):
        # 既存Q4が無い場合は従来通り Q4 = FY - (Q1+Q2+Q3) を生成する
        annual = [_annual("2024-12-31", "2024-01-01", 1000)]
        quarterly = [
            _q("2024-03-31", "2024-01-01", 100),
            _q("2024-06-30", "2024-04-01", 200),
            _q("2024-09-30", "2024-07-01", 300),
        ]
        result = _build_q4_quarterly_entries(annual, quarterly)
        assert len(result) == 1
        assert result[0]["end"] == "2024-12-31"
        assert result[0]["val"] == 1000 - (100 + 200 + 300)
        assert result[0]["is_implied"] is True

    def test_calc_ttm_series_no_duplicate_end_dates_in_window(self):
        # 統合テスト: calc_ttm_series が直近4Qに同一end日付を重複させないこと
        # (BUG-TTM-Q4DUP-1 再発防止の回帰テスト)
        normalized = {
            "fields": {
                "NetIncome": [
                    _q("2024-03-31", "2024-01-01", 10),
                    _q("2024-06-30", "2024-04-01", 20),
                    _q("2024-09-30", "2024-07-01", 30),
                    _q("2024-12-31", "2024-09-30", 940, is_implied=True),  # 永続化済みimplied Q4
                    _q("2025-03-31", "2025-01-01", 50),
                    _annual("2024-12-31", "2024-01-01", 1000),
                ],
            }
        }
        series = calc_ttm_series("TEST", normalized, n_periods=1)
        assert len(series) == 1
        ni_entries_end_dates = ["2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30"]
        # 重複排除後の正しい4Q合計: 50 + 940 + 30 + 20 = 1040
        assert series[0]["flow"]["NetIncome"]["val"] == 50 + 940 + 30 + 20
        assert series[0]["flow"]["NetIncome"]["quarters_used"] == 4


class TestCalcTtmSeriesNullValGuard:
    """TTM-NULL-1: calc_ttm_series() の4Q合算で val=None がTypeErrorを起こさないことを保証する"""

    def test_none_val_in_series_window_treated_as_zero(self):
        normalized = {
            "fields": {
                "OCF": [
                    _q("2025-03-31", "2025-01-01", None),
                    _q("2024-12-31", "2024-10-01", 100.0),
                    _q("2024-09-30", "2024-07-01", 200.0),
                    _q("2024-06-30", "2024-04-01", 150.0),
                ],
            }
        }
        series = calc_ttm_series("TESTCO3", normalized, n_periods=1)
        assert len(series) == 1
        assert series[0]["flow"]["OCF"]["val"] == 450.0


class TestCurrentAssetsLiabilitiesStockFieldsClassification:
    """GATE2-PHASE3B-1②: CurrentAssets/CurrentLiabilitiesがSTOCK_FIELDSに
    追加され、calc_ttm()の出力（stock辞書）に含まれるようになったことの回帰テスト。
    追加前は抽出されていてもFLOW/STOCK/SHARESいずれにも属さず、TTM出力から
    消えていた（消費者ゼロのまま放置されていた既知バグ）"""

    def test_current_assets_and_liabilities_are_in_stock_fields(self):
        assert "CurrentAssets" in STOCK_FIELDS
        assert "CurrentLiabilities" in STOCK_FIELDS

    def test_current_assets_and_liabilities_not_in_excluded_fields(self):
        """STOCK_FIELDSとEXCLUDED_FIELDSは排他的であるべき
        （両方に入っていると分類は通るが二重計上・意味の混乱を招く）"""
        assert "CurrentAssets" not in EXCLUDED_FIELDS
        assert "CurrentLiabilities" not in EXCLUDED_FIELDS

    def test_calc_ttm_outputs_current_assets_and_liabilities_as_latest_quarter_value(self):
        """calc_ttm()がCurrentAssets/CurrentLiabilitiesをストック系
        （最新Q末の値）として正しくstock辞書に出力すること"""
        normalized = {
            "fields": {
                "CurrentAssets": [
                    _q("2025-03-31", "2025-01-01", 500.0),
                    _q("2024-12-31", "2024-10-01", 480.0),
                ],
                "CurrentLiabilities": [
                    _q("2025-03-31", "2025-01-01", 300.0),
                    _q("2024-12-31", "2024-10-01", 290.0),
                ],
            }
        }
        result = calc_ttm("TESTCO4", normalized)
        assert result["stock"]["CurrentAssets"]["val"] == 500.0
        assert result["stock"]["CurrentAssets"]["as_of"] == "2025-03-31"
        assert result["stock"]["CurrentLiabilities"]["val"] == 300.0
        assert result["stock"]["CurrentLiabilities"]["as_of"] == "2025-03-31"
