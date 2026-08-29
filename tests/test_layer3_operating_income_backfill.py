"""
tests/test_layer3_operating_income_backfill.py

[[LAYER3-OI-RECONSTRUCTION-FALLBACK-GAP-1]]の回帰テスト。

layer3_builder.py::_backfill_operating_income()が、GP法
（gross_profit - research_and_development - selling_general_and_
administrative、または...selling_and_marketing）で四半期operating_income
の欠損を逆算し、build_ticker_store()の既存フィールドを直接変更する
ことを確認する。common/sec_data/parser.py::_backfill_operating_income()
のGP法部分と同一アルゴリズムだが四半期粒度が対象（詳細は本体docstring
参照）。

実行方法:
    python -m pytest tests/test_layer3_operating_income_backfill.py -v
"""

from common.sec_data.layer3_builder import _backfill_operating_income


def _entry(end, val, fp="Q1", fy=2024, is_annual=False, **overrides):
    e = {
        "end": end, "start": "2023-01-01", "fp": fp, "fy": fy, "form": "10-Q",
        "filed": "2024-01-15", "period_days": 91, "is_ytd": False,
        "is_annual": is_annual, "val": val, "accn": "0001-24-000001",
    }
    e.update(overrides)
    return e


def _field(entries):
    return {"source_tag": "X", "category": "income_statement", "entries": list(entries)}


def _fields_out(**fields):
    return {name: _field(entries) for name, entries in fields.items()}


class TestBackfillOperatingIncome:
    def test_fills_missing_quarter_via_gp_method_with_sga(self):
        """gross_profit - R&D - SGAで欠損四半期を逆算する"""
        fields_out = _fields_out(
            operating_income=[],
            gross_profit=[_entry("2024-03-31", 1000.0)],
            research_and_development=[_entry("2024-03-31", 200.0)],
            selling_general_and_administrative=[_entry("2024-03-31", 300.0)],
            revenue=[_entry("2024-03-31", 1800.0)],
        )
        _backfill_operating_income(fields_out)
        entries = fields_out["operating_income"]["entries"]
        assert len(entries) == 1
        assert entries[0]["val"] == 500.0  # 1000 - 200 - 300
        assert entries[0]["backfilled"] is True
        assert entries[0]["backfill_source"] == "reconstructed_gp"
        assert entries[0]["end"] == "2024-03-31"

    def test_falls_back_to_selling_and_marketing_when_sga_missing(self):
        """統合SGAを報告しない企業はselling_and_marketingで代替する（SOFI等）"""
        fields_out = _fields_out(
            operating_income=[],
            gross_profit=[_entry("2024-03-31", 1000.0)],
            research_and_development=[_entry("2024-03-31", 200.0)],
            selling_general_and_administrative=[],
            selling_and_marketing=[_entry("2024-03-31", 150.0)],
            revenue=[_entry("2024-03-31", 1800.0)],
        )
        _backfill_operating_income(fields_out)
        entries = fields_out["operating_income"]["entries"]
        assert len(entries) == 1
        assert entries[0]["val"] == 650.0  # 1000 - 200 - 150

    def test_does_not_overwrite_existing_operating_income(self):
        """標準タグから既に取得できているoperating_income（同一end日）は上書きしない"""
        fields_out = _fields_out(
            operating_income=[_entry("2024-03-31", 999.0, is_annual=False)],
            gross_profit=[_entry("2024-03-31", 1000.0)],
            research_and_development=[_entry("2024-03-31", 200.0)],
            selling_general_and_administrative=[_entry("2024-03-31", 300.0)],
            revenue=[_entry("2024-03-31", 1800.0)],
        )
        _backfill_operating_income(fields_out)
        entries = fields_out["operating_income"]["entries"]
        assert len(entries) == 1
        assert entries[0]["val"] == 999.0
        assert "backfilled" not in entries[0]

    def test_skips_quarter_when_rd_missing(self):
        """R&Dが欠損している四半期は逆算対象外"""
        fields_out = _fields_out(
            operating_income=[],
            gross_profit=[_entry("2024-03-31", 1000.0)],
            research_and_development=[],
            selling_general_and_administrative=[_entry("2024-03-31", 300.0)],
            revenue=[_entry("2024-03-31", 1800.0)],
        )
        _backfill_operating_income(fields_out)
        assert fields_out["operating_income"]["entries"] == []

    def test_skips_quarter_when_both_sga_and_sm_missing(self):
        """SGA・S&Mともに欠損している四半期は逆算対象外"""
        fields_out = _fields_out(
            operating_income=[],
            gross_profit=[_entry("2024-03-31", 1000.0)],
            research_and_development=[_entry("2024-03-31", 200.0)],
            selling_general_and_administrative=[],
            selling_and_marketing=[],
            revenue=[_entry("2024-03-31", 1800.0)],
        )
        _backfill_operating_income(fields_out)
        assert fields_out["operating_income"]["entries"] == []

    def test_integrity_guard_rejects_gross_profit_exceeding_revenue(self):
        """|gross_profit| > |revenue|は定義上矛盾するため逆算対象外
        （parser.py::_backfill_operating_income()の案Dガードと同型）"""
        fields_out = _fields_out(
            operating_income=[],
            gross_profit=[_entry("2024-03-31", 2000.0)],  # revenueを超過
            research_and_development=[_entry("2024-03-31", 200.0)],
            selling_general_and_administrative=[_entry("2024-03-31", 300.0)],
            revenue=[_entry("2024-03-31", 1800.0)],
        )
        _backfill_operating_income(fields_out)
        assert fields_out["operating_income"]["entries"] == []

    def test_scale_mismatch_guard_skips_fy_tagged_gross_profit_entry(self):
        """[[LAYER3-FY-SCALE-ANNUAL-MISFLAG-1]]対応: gross_profitがfp="FY"
        （52/53週決算企業のend日でis_annual=Falseのまま年次スケールの値が
        紛れ込むケース、JNJ実測で発見）の場合は逆算対象から除外する"""
        fields_out = _fields_out(
            operating_income=[],
            gross_profit=[_entry("2023-01-01", 13855.0, fp="FY", form="10-K")],
            research_and_development=[_entry("2023-01-01", 3485.0, fp="Q4")],
            selling_general_and_administrative=[_entry("2023-01-01", 3107.0, fp="Q4")],
            revenue=[_entry("2023-01-01", 20000.0, fp="FY")],
        )
        _backfill_operating_income(fields_out)
        assert fields_out["operating_income"]["entries"] == []

    def test_does_not_backfill_annual_entries(self):
        """is_annual=Trueのgross_profitエントリは対象外（四半期粒度のみが対象）"""
        fields_out = _fields_out(
            operating_income=[],
            gross_profit=[_entry("2024-12-31", 5000.0, fp="FY", is_annual=True)],
            research_and_development=[_entry("2024-12-31", 500.0, fp="FY", is_annual=True)],
            selling_general_and_administrative=[_entry("2024-12-31", 700.0, fp="FY", is_annual=True)],
            revenue=[_entry("2024-12-31", 9000.0, fp="FY", is_annual=True)],
        )
        _backfill_operating_income(fields_out)
        assert fields_out["operating_income"]["entries"] == []

    def test_noop_when_operating_income_field_absent(self):
        """operating_incomeフィールド自体が存在しない場合は何もしない（例外を送出しない）"""
        fields_out = _fields_out(
            gross_profit=[_entry("2024-03-31", 1000.0)],
        )
        _backfill_operating_income(fields_out)  # no KeyError

    def test_noop_when_gross_profit_field_absent(self):
        """gross_profitフィールド自体が存在しない場合は何もしない（例外を送出しない）"""
        fields_out = _fields_out(
            operating_income=[],
        )
        _backfill_operating_income(fields_out)  # no KeyError
        assert fields_out["operating_income"]["entries"] == []

    def test_handles_multiple_quarters_independently(self):
        """複数四半期が混在する場合、欠損四半期のみ個別に逆算される"""
        fields_out = _fields_out(
            operating_income=[_entry("2024-03-31", 111.0)],  # 標準タグ既存
            gross_profit=[
                _entry("2024-03-31", 1000.0),
                _entry("2024-06-30", 1100.0),
            ],
            research_and_development=[
                _entry("2024-03-31", 200.0),
                _entry("2024-06-30", 220.0),
            ],
            selling_general_and_administrative=[
                _entry("2024-03-31", 300.0),
                _entry("2024-06-30", 330.0),
            ],
            revenue=[
                _entry("2024-03-31", 1800.0),
                _entry("2024-06-30", 1900.0),
            ],
        )
        _backfill_operating_income(fields_out)
        entries = {e["end"]: e for e in fields_out["operating_income"]["entries"]}
        assert entries["2024-03-31"]["val"] == 111.0
        assert "backfilled" not in entries["2024-03-31"]
        assert entries["2024-06-30"]["val"] == 550.0  # 1100 - 220 - 330
        assert entries["2024-06-30"]["backfilled"] is True
