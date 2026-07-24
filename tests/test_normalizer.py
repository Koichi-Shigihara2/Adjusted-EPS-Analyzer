"""
tests/test_normalizer.py

common/sec_data/normalizer.py のユニットテスト。
BUG-CON-YTD-3: AMZN等で発生した2つの回帰バグの再発防止テスト。

- バグA: _calc_gross_profit が end日付のみでRevenue/COGSを引き当てる際、
  未解決の累積値（is_ytd=True）が単独四半期値を上書きしてしまう問題。
- バグB: _build_missing_quarter_implied_entries が算出する欠落四半期の
  end/start日付が実際の暦四半期境界と1日ずれ、build_q4_implied_entries が
  算出する同一四半期のend日付と一致せず二重計上される問題。

Q4逆算本体はcommon/sec_data/q4_implied.py::build_q4_implied_entries()に
集約済み（[[Q4-IMPLIED-CALC-TRIPLICATION-1]]対応、移行実装計画フェーズB）。

実行方法:
    python -m pytest tests/test_normalizer.py -v
"""

# QUALITY-GATES-EPIC-1 Phase 3a: normalizer.pyがcontracts.pyを相対importする
# ようになったため、sys.pathハックによる単独モジュールimportは使えなくなった
# （相対importはパッケージ経由でロードされた場合のみ機能する）。
# パッケージ経由のimportに変更。
from common.sec_data.normalizer import (
    _calc_gross_profit,
    _build_missing_quarter_implied_entries,
    normalize,
)
from common.sec_data.q4_implied import build_q4_implied_entries


class TestGrossProfitPreferStandaloneOverUnresolvedYTD:
    """BUG-CON-YTD-3 バグA: 同一end日付で単独四半期値を優先する"""

    def test_prefers_standalone_quarter_value(self):
        # AMZN Q3 2021相当: 5年ロールウィンドウ境界で9ヶ月YTDが未解決のまま
        # 残存し、後発フィリングの比較値（単独四半期）と同じendで共存する
        fields = {
            "Revenue": [
                {"start": "2021-01-01", "end": "2021-09-30", "val": 900,
                 "is_ytd": True, "is_annual": False, "filed": "2021-10-29"},
                {"start": "2021-07-01", "end": "2021-09-30", "val": 300,
                 "is_ytd": False, "is_annual": False, "filed": "2022-10-28",
                 "fp": "Q3", "fy": 2022, "form": "10-Q", "period_days": 91,
                 "accn": "z"},
            ],
            "_COGS": [
                {"start": "2021-01-01", "end": "2021-09-30", "val": 630,
                 "is_ytd": True, "is_annual": False, "filed": "2021-10-29"},
                {"start": "2021-07-01", "end": "2021-09-30", "val": 180,
                 "is_ytd": False, "is_annual": False, "filed": "2022-10-28"},
            ],
            "GrossProfit": [],
        }
        result = _calc_gross_profit(fields)
        gp = result["GrossProfit"]
        assert len(gp) == 1
        # 300-180=120（単独四半期）であるべき。900-630=270（9ヶ月累計混入）は誤り
        assert gp[0]["val"] == 120
        assert gp[0]["end"] == "2021-09-30"

    def test_falls_back_to_cumulative_when_no_standalone_exists(self):
        # 単独四半期値が存在しない場合は従来通り累積値にフォールバックする
        fields = {
            "Revenue": [
                {"start": "2021-01-01", "end": "2021-09-30", "val": 900,
                 "is_ytd": True, "is_annual": False, "filed": "2021-10-29"},
            ],
            "_COGS": [
                {"start": "2021-01-01", "end": "2021-09-30", "val": 630,
                 "is_ytd": True, "is_annual": False, "filed": "2021-10-29"},
            ],
            "GrossProfit": [],
        }
        result = _calc_gross_profit(fields)
        gp = result["GrossProfit"]
        assert len(gp) == 1
        assert gp[0]["val"] == 270


class TestMissingQuarterImpliedDateAlignment:
    """BUG-CON-YTD-3 バグB: 欠落四半期の日付が暦四半期境界と一致する"""

    def test_leading_gap_end_date_matches_calendar_quarter_boundary(self):
        # AMZN型: 12ヶ月移動累計比較値（is_annual誤タグ）から
        # 欠落四半期(FY2022 Q4相当)を逆算するケース
        entries = [
            {"start": "2022-10-01", "end": "2023-09-30", "val": 1030,
             "is_annual": True, "fp": "Q3", "fy": 2023, "form": "10-Q",
             "filed": "x", "accn": "y"},
            {"start": "2023-01-01", "end": "2023-03-31", "val": 110,
             "is_annual": False, "is_ytd": False},
            {"start": "2023-04-01", "end": "2023-06-30", "val": 210,
             "is_annual": False, "is_ytd": False},
            {"start": "2023-07-01", "end": "2023-09-30", "val": 310,
             "is_annual": False, "is_ytd": False},
        ]
        result = _build_missing_quarter_implied_entries(entries)
        assert len(result) == 1
        # 修正前は "2023-01-01"（Q1 2023のstartそのもの）を誤って採用していた
        assert result[0]["end"] == "2022-12-31"
        assert result[0]["start"] == "2022-10-01"
        assert result[0]["val"] == 1030 - (110 + 210 + 310)

    def test_trailing_gap_start_date_matches_calendar_quarter_boundary(self):
        # 9ヶ月YTD - 既知2四半期 = 欠落Q3（末尾側の欠落）
        entries = [
            {"start": "2022-01-01", "end": "2022-09-30", "val": 600,
             "is_ytd": True, "is_annual": False, "fp": "Q3", "fy": 2022,
             "form": "10-Q", "filed": "x", "accn": "y"},
            {"start": "2022-01-01", "end": "2022-03-31", "val": 100,
             "is_annual": False, "is_ytd": False},
            {"start": "2022-04-01", "end": "2022-06-30", "val": 200,
             "is_annual": False, "is_ytd": False},
        ]
        result = _build_missing_quarter_implied_entries(entries)
        assert len(result) == 1
        # 修正前は "2022-06-30"（直前既知四半期のendそのもの）を誤って採用していた
        assert result[0]["start"] == "2022-07-01"
        assert result[0]["end"] == "2022-09-30"
        assert result[0]["val"] == 600 - (100 + 200)

    def test_no_duplicate_with_standard_q4_implied_after_date_fix(self):
        # 統合テスト: missing_quarter_implied が算出したend日付が
        # build_q4_implied_entries のend日付と一致し、
        # normalize()側の既存end重複排除で二重計上されなくなることを確認する
        annual_end_aligned_q4 = build_q4_implied_entries(
            [
                {"start": "2022-01-01", "end": "2022-12-31", "val": 1030,
                 "is_annual": True, "fp": "FY", "fy": 2022, "form": "10-K",
                 "filed": "z", "accn": "a"},
            ],
            [
                {"start": "2022-01-01", "end": "2022-03-31", "val": 110,
                 "is_annual": False, "is_ytd": False},
                {"start": "2022-04-01", "end": "2022-06-30", "val": 210,
                 "is_annual": False, "is_ytd": False},
                {"start": "2022-07-01", "end": "2022-09-30", "val": 310,
                 "is_annual": False, "is_ytd": False},
            ],
            "NetIncome",
        )
        missing_quarter_result = _build_missing_quarter_implied_entries([
            {"start": "2022-10-01", "end": "2023-09-30", "val": 1030 + 100,
             "is_annual": True, "fp": "Q3", "fy": 2023, "form": "10-Q",
             "filed": "x", "accn": "y"},
            {"start": "2023-01-01", "end": "2023-03-31", "val": 110,
             "is_annual": False, "is_ytd": False},
            {"start": "2023-04-01", "end": "2023-06-30", "val": 210,
             "is_annual": False, "is_ytd": False},
            {"start": "2023-07-01", "end": "2023-09-30", "val": 310,
             "is_annual": False, "is_ytd": False},
        ])
        # 両関数が同じ四半期(FY2022 Q4)を別々に算出しても、end日付は一致する
        assert annual_end_aligned_q4[0]["end"] == missing_quarter_result[0]["end"] == "2022-12-31"


class TestNormalizeIntegrationNoOffByOneDuplicate:
    """normalize() 全体を通しても年末/年始で1日ずれの重複が生じないこと"""

    def test_no_duplicate_year_boundary_entries_for_net_income(self):
        raw = {
            "fields": {
                "NetIncome": [
                    # FY2022 annual
                    {"start": "2022-01-01", "end": "2022-12-31", "val": 400,
                     "is_annual": True, "fp": "FY", "fy": 2022, "form": "10-K",
                     "filed": "2023-02-01", "accn": "fy2022"},
                    # Q1-Q3 2022 SA
                    {"start": "2022-01-01", "end": "2022-03-31", "val": 100,
                     "is_annual": False, "is_ytd": False, "fp": "Q1", "fy": 2022,
                     "form": "10-Q", "filed": "2022-04-28", "accn": "q1-2022",
                     "period_days": 90},
                    {"start": "2022-04-01", "end": "2022-06-30", "val": 200,
                     "is_annual": False, "is_ytd": False, "fp": "Q2", "fy": 2022,
                     "form": "10-Q", "filed": "2022-07-28", "accn": "q2-2022",
                     "period_days": 90},
                    {"start": "2022-07-01", "end": "2022-09-30", "val": 300,
                     "is_annual": False, "is_ytd": False, "fp": "Q3", "fy": 2022,
                     "form": "10-Q", "filed": "2022-10-28", "accn": "q3-2022",
                     "period_days": 91},
                    # Q1-Q3 2023 SA（FY2022 Q4=400-100-200-300=-200 を
                    # 誤って12ヶ月移動累計から再算出させる元ネタ）
                    {"start": "2023-01-01", "end": "2023-03-31", "val": 110,
                     "is_annual": False, "is_ytd": False, "fp": "Q1", "fy": 2023,
                     "form": "10-Q", "filed": "2023-04-28", "accn": "q1-2023",
                     "period_days": 89},
                    {"start": "2023-04-01", "end": "2023-06-30", "val": 210,
                     "is_annual": False, "is_ytd": False, "fp": "Q2", "fy": 2023,
                     "form": "10-Q", "filed": "2023-07-28", "accn": "q2-2023",
                     "period_days": 90},
                    {"start": "2023-07-01", "end": "2023-09-30", "val": 310,
                     "is_annual": False, "is_ytd": False, "fp": "Q3", "fy": 2023,
                     "form": "10-Q", "filed": "2023-10-28", "accn": "q3-2023",
                     "period_days": 91},
                    # 12ヶ月移動累計比較値（is_annual誤タグ、AMZN型）
                    # FY2022 Q4(-200) + Q1-Q3 2023(110+210+310=630) = 430
                    {"start": "2022-10-01", "end": "2023-09-30", "val": 430,
                     "is_annual": True, "fp": "Q3", "fy": 2023, "form": "10-Q",
                     "filed": "2023-10-28", "accn": "q3-2023"},
                ],
            }
        }
        result = normalize("TEST", raw)
        ni_entries = [
            e for e in result["fields"]["NetIncome"] if not e.get("is_annual")
        ]
        ends = [e["end"] for e in ni_entries]
        # end日付は重複してはならない（1日ずれの別表現を含む）
        assert len(ends) == len(set(ends)), f"duplicate ends found: {ends}"
        # FY2022 Q4は正しい暦四半期境界(end=2022-12-31)で1件のみ存在する
        q4_2022 = [e for e in ni_entries if e["end"] == "2022-12-31"]
        assert len(q4_2022) == 1
        assert q4_2022[0]["val"] == 400 - (100 + 200 + 300)
        # 誤った1日ずれend（2023-01-01）は存在しない
        assert "2023-01-01" not in ends
